"""polite_http.py -- one careful HTTP GET at a time, cached, with a download manifest.

Shared by code/fetch_open_data_4d7f74pe.py and code/fetch_wayback_council_files.py
(GitHub #85, #86). The rules come from epic #89 "Access rules: go slow, don't get blocked":

  * one request at a time per host, never concurrent;
  * a minimum gap between requests to the same host (`min_gap` seconds);
  * a descriptive User-Agent;
  * never re-fetch: a cached file is returned as-is, no request made;
  * HTTP 429 -> wait `wait_429` seconds (>= 60), retry ONCE; a second 429 stops every later
    request to that host (Blocked). HTTP 403 stops the host immediately, no retry;
  * every download recorded in a manifest row (url, wayback timestamp, retrieved-at, bytes,
    sha256, rows).

Secrets: an extra request header (the Socrata app token) is passed in by the caller and is never
written to a manifest, a log line or an exception message.

Stdlib only.
"""
import csv
import hashlib
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime

USER_AGENT = "BetaNYC-research/1.0 (+https://github.com/BetaNYC/New-York-City-Budget)"
MANIFEST_FIELDS = ["file", "url", "wayback_timestamp", "retrieved_at", "http_status", "bytes",
                   "sha256", "rows", "note"]


class Blocked(Exception):
    """The host said stop (403, or a second 429). No further request to it is made."""


class Fetcher:
    """GETs with per-host pacing. `opener(request, timeout)` and `sleep`/`clock` are injectable
    so tests run with no network and no real waiting."""

    def __init__(self, min_gap, wait_429=65.0, opener=None, sleep=time.sleep,
                 clock=time.monotonic, log=print):
        if wait_429 < 60:
            raise ValueError("wait_429 must be at least 60 seconds (epic #89)")
        self.min_gap = float(min_gap)
        self.wait_429 = float(wait_429)
        self.opener = opener or (lambda req, timeout: urllib.request.urlopen(req, timeout=timeout))
        self.sleep = sleep
        self.clock = clock
        self.log = log
        self.last = {}          # host -> clock() of the last request
        self.blocked = {}       # host -> reason
        self.counts = {}        # host -> number of requests actually sent
        self.statuses = []      # (host, status) for every request sent

    def _pace(self, host):
        prev = self.last.get(host)
        if prev is not None:
            wait = self.min_gap - (self.clock() - prev)
            if wait > 0:
                self.sleep(wait)

    def _send(self, url, headers, timeout):
        host = urllib.parse.urlsplit(url).hostname
        self._pace(host)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
        self.counts[host] = self.counts.get(host, 0) + 1
        try:
            with self.opener(req, timeout) as resp:
                body = resp.read()
                status = getattr(resp, "status", 200)
        except urllib.error.HTTPError as e:
            status, body = e.code, b""
        finally:
            self.last[host] = self.clock()
        self.statuses.append((host, status))
        return status, body

    def get(self, url, headers=None, timeout=120):
        """Return (status, body bytes). Raises Blocked on 403 or a repeated 429."""
        host = urllib.parse.urlsplit(url).hostname
        if host in self.blocked:
            raise Blocked(f"{host}: {self.blocked[host]}")
        status, body = self._send(url, headers, timeout)
        if status == 403:
            self.blocked[host] = "HTTP 403"
            raise Blocked(f"{host}: HTTP 403 on {url}")
        if status == 429:
            self.log(f"[polite_http] 429 from {host}; waiting {self.wait_429:.0f}s, one retry")
            self.sleep(self.wait_429)
            status, body = self._send(url, headers, timeout)
            if status in (403, 429):
                self.blocked[host] = f"HTTP {status} after a 429"
                raise Blocked(f"{host}: HTTP {status} after a 429 on {url}")
        return status, body

    def get_cached(self, url, path, headers=None, timeout=120):
        """Return (body, fetched). A file already at `path` is read, never re-fetched. A non-200
        response raises RuntimeError and writes nothing to the cache."""
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read(), False
        status, body = self.get(url, headers=headers, timeout=timeout)
        if status != 200:
            raise RuntimeError(f"HTTP {status} for {url}")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".part"
        with open(tmp, "wb") as f:
            f.write(body)
        os.replace(tmp, path)
        return body, True


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def now_iso():
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def read_manifest(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def upsert_manifest(path, row):
    """Add or replace the row for row['file'] (idempotent: re-running writes the same file)."""
    rows = [r for r in read_manifest(path) if r["file"] != row["file"]]
    rows.append({k: row.get(k, "") for k in MANIFEST_FIELDS})
    rows.sort(key=lambda r: r["file"])
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
