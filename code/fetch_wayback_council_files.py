#!/usr/bin/env python3
"""fetch_wayback_council_files.py -- list and download the Council's archived budget files from
the Internet Archive, slowly and once (GitHub #86).

    python3 code/fetch_wayback_council_files.py cdx --cache DIR URL [--match prefix|exact]
                [--filter REGEX ...] [--collapse digest|urlkey]
    python3 code/fetch_wayback_council_files.py get --cache DIR TIMESTAMP ORIGINAL_URL
    python3 code/fetch_wayback_council_files.py batch --cache DIR PLAN.json
        PLAN is a JSON list of steps, run in order in ONE process so pacing holds across them:
          {"cdx": {"url": ..., "match": "prefix", "filters": [...], "collapse": "digest"}}
          {"get": ["<timestamp>", "<original url>"]}
        CDX and downloads share web.archive.org, so a batch uses one clock at CDX_GAP.

Interface, from the Wayback CDX server documentation
(github.com/internetarchive/wayback/tree/master/wayback-cdx-server):
  GET https://web.archive.org/cdx/search/cdx?url=<url>&matchType=exact|prefix&output=json
      &fl=timestamp,original,mimetype,statuscode,digest,length
      &filter=<field>:<regex>   (repeatable; a leading "!" negates)
      &collapse=digest|urlkey   (drops ADJACENT rows equal on that field; rows are sorted by
                                 urlkey then timestamp, so collapse=digest lists each URL's
                                 distinct contents in time order -- a digest that returns
                                 later after a different one is listed again)
  output=json is an array of arrays whose first row is the field names.
Downloads use the Wayback replay "identity" flag, https://web.archive.org/web/<ts>id_/<url>,
which returns the archived bytes without the replay toolbar or rewriting.

Pacing (2026-10-14 dispatch): CDX calls >= 6 s apart, downloads >= 3 s apart, one at a time.
429 -> wait 65 s, one retry; second 429 or any 403 -> stop every Internet Archive call
(polite_http.Blocked). Results are cached; nothing cached is ever requested again.

Writes:
  <cache>/cdx/<name>.json                     raw CDX response
  <cache>/files/<timestamp>/<basename>        the archived file, as served
  source/wayback-council/MANIFEST.csv         one row per download (committed)
  source/wayback-council/CDX-QUERIES.csv      one row per CDX query (committed)
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import polite_http as H

ROOT = os.path.dirname(HERE)
CDX = "https://web.archive.org/cdx/search/cdx"
FIELDS = "timestamp,original,mimetype,statuscode,digest,length"
MANIFEST = os.path.join(ROOT, "source", "wayback-council", "MANIFEST.csv")
QUERIES = os.path.join(ROOT, "source", "wayback-council", "CDX-QUERIES.csv")
CDX_GAP = 6.0
GET_GAP = 3.0
# Every file this script downloads lands here; the dispatch caps the session at ~40.
DOWNLOAD_CAP = 40


def cdx_url(url, match="exact", filters=(), collapse=None):
    params = [("url", url), ("matchType", match), ("output", "json"), ("fl", FIELDS)]
    params += [("filter", f) for f in filters]
    if collapse:
        params.append(("collapse", collapse))
    return CDX + "?" + urllib.parse.urlencode(params)


def cdx_name(query_url):
    return hashlib.sha1(query_url.encode()).hexdigest()[:16]


def parse_cdx(body):
    """CDX JSON -> list of dicts. An empty body or [] means no captures."""
    text = body.decode("utf-8").strip()
    if not text:
        return []
    data = json.loads(text)
    if not data:
        return []
    head, rows = data[0], data[1:]
    return [dict(zip(head, r)) for r in rows]


def replay_url(timestamp, original):
    if not re.fullmatch(r"\d{14}", timestamp):
        raise ValueError(f"not a 14-digit Wayback timestamp: {timestamp!r}")
    return f"https://web.archive.org/web/{timestamp}id_/{original}"


def file_path(cache, timestamp, original):
    base = os.path.basename(urllib.parse.urlsplit(original).path) or "index"
    return os.path.join(cache, "files", timestamp, base)


def count_downloads(cache):
    root = os.path.join(cache, "files")
    if not os.path.isdir(root):
        return 0
    return sum(len([f for f in fs if not f.endswith(".part")]) for _, _, fs in os.walk(root))


def run_cdx(fetcher, cache, url, match, filters, collapse):
    q = cdx_url(url, match, filters, collapse)
    path = os.path.join(cache, "cdx", cdx_name(q) + ".json")
    body, fetched = fetcher.get_cached(q, path)
    rows = parse_cdx(body)
    rec = {"file": os.path.relpath(path, cache), "url": q, "retrieved_at": H.now_iso(),
           "http_status": 200, "bytes": len(body), "sha256": H.sha256_bytes(body),
           "rows": len(rows), "note": f"{match} {url} filters={list(filters)} collapse={collapse}"}
    if fetched:
        H.upsert_manifest(QUERIES, rec)
    return rows, fetched


def run_get(fetcher, cache, timestamp, original):
    path = file_path(cache, timestamp, original)
    if not os.path.exists(path) and count_downloads(cache) >= DOWNLOAD_CAP:
        raise SystemExit(f"download cap {DOWNLOAD_CAP} reached; list the rest as a question")
    body, fetched = fetcher.get_cached(replay_url(timestamp, original), path)
    if fetched:
        H.upsert_manifest(MANIFEST, {
            "file": os.path.relpath(path, cache), "url": original,
            "wayback_timestamp": timestamp, "retrieved_at": H.now_iso(), "http_status": 200,
            "bytes": len(body), "sha256": H.sha256_bytes(body), "rows": ""})
    return path, body, fetched


def data_rows(path):
    """Rows below the header in the one sheet that holds data (CSV: lines below the header).
    For the manifest's `rows` column; a workbook's award rows are in the research report."""
    if path.lower().endswith(".csv"):
        import csv
        # Records, not lines (a quoted cell may hold a line break). latin-1 decodes any byte,
        # and only the record count is used, so the encoding question does not arise.
        with open(path, newline="", encoding="latin-1") as f:
            return max(0, sum(1 for r in csv.reader(f) if any(c.strip() for c in r)) - 1)
    import zipfile
    if zipfile.is_zipfile(path):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        counts = [sum(1 for r in ws.iter_rows(values_only=True)
                      if any(c not in (None, "") for c in r)) for ws in wb.worksheets]
    else:
        import xlrd
        book = xlrd.open_workbook(path)
        counts = [sum(1 for r in range(sh.nrows)
                      if any(str(v).strip() for v in sh.row_values(r))) for sh in book.sheets()]
    counts = [c for c in counts if c]
    return max(0, counts[0] - 1) if counts else 0


def annotate_rows(cache, manifest=MANIFEST):
    """Fill the manifest's `rows` column from the cached files. Idempotent."""
    for r in H.read_manifest(manifest):
        p = os.path.join(cache, r["file"])
        if os.path.exists(p):
            r["rows"] = data_rows(p)
            H.upsert_manifest(manifest, r)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cdx")
    c.add_argument("--cache", required=True)
    c.add_argument("url")
    c.add_argument("--match", default="exact", choices=["exact", "prefix"])
    c.add_argument("--filter", action="append", default=[])
    c.add_argument("--collapse", choices=["digest", "urlkey"])
    g = sub.add_parser("get")
    g.add_argument("--cache", required=True)
    g.add_argument("timestamp")
    g.add_argument("original")
    n = sub.add_parser("rows", help="fill the manifest's rows column from cached files")
    n.add_argument("--cache", required=True)
    b = sub.add_parser("batch")
    b.add_argument("--cache", required=True)
    b.add_argument("plan")
    a = ap.parse_args(argv)
    if a.cmd == "rows":
        annotate_rows(a.cache)
        return
    if a.cmd == "batch":
        with open(a.plan, encoding="utf-8") as fh:
            steps = json.load(fh)
        f = H.Fetcher(min_gap=CDX_GAP)
        out = []
        for st in steps:
            try:
                if "cdx" in st:
                    q = st["cdx"]
                    rows, fetched = run_cdx(f, a.cache, q["url"], q.get("match", "exact"),
                                            q.get("filters", []), q.get("collapse"))
                    out.append({"step": st, "fetched": fetched, "rows": rows})
                    print(f"cdx {q['url']}: {len(rows)} rows ({'fetched' if fetched else 'cached'})")
                else:
                    ts, orig = st["get"]
                    path, body, fetched = run_get(f, a.cache, ts, orig)
                    out.append({"step": st, "fetched": fetched, "path": path,
                                "bytes": len(body), "sha256": H.sha256_bytes(body)})
                    print(f"get {ts} {orig}: {len(body)} bytes ({'fetched' if fetched else 'cached'})")
            except H.Blocked as e:
                print(f"STOP: {e}")
                break
            except RuntimeError as e:
                out.append({"step": st, "error": str(e)})
                print(f"error: {e}")
        print("requests sent per host:", f.counts, "statuses:",
              dict(Counter(s for _, s in f.statuses)))
        res = os.path.splitext(a.plan)[0] + ".result.json"
        with open(res, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
        return
    if a.cmd == "cdx":
        f = H.Fetcher(min_gap=CDX_GAP)
        rows, fetched = run_cdx(f, a.cache, a.url, a.match, a.filter, a.collapse)
        print(json.dumps({"fetched": fetched, "rows": rows}, indent=1))
    else:
        f = H.Fetcher(min_gap=GET_GAP)
        path, body, fetched = run_get(f, a.cache, a.timestamp, a.original)
        print(f"{path} {len(body)} bytes sha256 {H.sha256_bytes(body)} "
              f"{'fetched' if fetched else 'cached'}")


if __name__ == "__main__":
    main()
