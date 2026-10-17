"""Tests for polite_http.py and the pure parts of fetch_open_data_4d7f74pe.py. No network."""
import io
import os
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_open_data_4d7f74pe as F
import polite_http as H


class Resp(io.BytesIO):
    def __init__(self, body=b"ok", status=200):
        super().__init__(body)
        self.status = status


class Clock:
    def __init__(self):
        self.t = 0.0
        self.slept = []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


def make(responses, gap=2.0):
    """Fetcher whose opener returns `responses` in order (an int = that HTTP error code)."""
    clock = Clock()
    sent = []

    def opener(req, timeout):
        sent.append(req)
        r = responses.pop(0)
        if isinstance(r, int):
            raise urllib.error.HTTPError(req.full_url, r, "x", {}, None)
        return Resp(r)
    f = H.Fetcher(min_gap=gap, opener=opener, sleep=clock.sleep, clock=clock, log=lambda *a: None)
    return f, sent, clock


def test_paces_requests_to_one_host():
    f, _sent, clock = make([b"a", b"b"], gap=2.0)
    f.get("https://x.example/1")
    f.get("https://x.example/2")
    assert clock.slept == [2.0]          # the second request waited the full gap
    assert f.counts == {"x.example": 2}


def test_user_agent_is_descriptive_and_header_passed():
    f, sent, _ = make([b"a"])
    f.get("https://x.example/1", headers={"X-App-Token": "secret"})
    assert sent[0].get_header("User-agent") == H.USER_AGENT
    assert sent[0].get_header("X-app-token") == "secret"


def test_403_blocks_host_and_never_retries():
    f, sent, _ = make([403, b"never"])
    with pytest.raises(H.Blocked):
        f.get("https://x.example/1")
    with pytest.raises(H.Blocked):
        f.get("https://x.example/2")
    assert len(sent) == 1


def test_429_waits_at_least_60s_then_one_retry_succeeds():
    f, sent, clock = make([429, b"fine"])
    status, body = f.get("https://x.example/1")
    assert (status, body) == (200, b"fine")
    assert max(clock.slept) >= 60
    assert len(sent) == 2


def test_second_429_stops_the_host():
    f, sent, _ = make([429, 429, b"never"])
    with pytest.raises(H.Blocked):
        f.get("https://x.example/1")
    with pytest.raises(H.Blocked):
        f.get("https://x.example/2")
    assert len(sent) == 2


def test_wait_429_below_60_refused():
    with pytest.raises(ValueError):
        H.Fetcher(min_gap=1, wait_429=30)


def test_cached_file_is_never_refetched(tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(b"cached")
    f, sent, _ = make([b"net"])
    body, fetched = f.get_cached("https://x.example/a", str(p))
    assert (body, fetched, sent) == (b"cached", False, [])


def test_non_200_writes_nothing(tmp_path):
    f, _sent, _ = make([404])
    with pytest.raises(RuntimeError):
        f.get_cached("https://x.example/a", str(tmp_path / "a.bin"))
    assert not os.listdir(tmp_path)


def test_manifest_upsert_is_idempotent(tmp_path):
    m = str(tmp_path / "M.csv")
    H.upsert_manifest(m, {"file": "b", "bytes": 1})
    H.upsert_manifest(m, {"file": "a", "bytes": 2})
    H.upsert_manifest(m, {"file": "b", "bytes": 3})
    rows = H.read_manifest(m)
    assert [(r["file"], r["bytes"]) for r in rows] == [("a", "2"), ("b", "3")]


def test_rows_url_orders_by_id_and_pages():
    u = F.rows_url(10000)
    assert "$order=:id" in u and "$limit=5000" in u and "$offset=10000" in u
    assert "$select=:*,*" in u


def test_rows_csv_refuses_unknown_field():
    with pytest.raises(ValueError):
        F.rows_csv([{"mocs_id": "1", "surprise": "x"}])


def test_rows_csv_missing_field_is_empty():
    text = F.rows_csv([{"mocs_id": "1"}])
    header, row = text.splitlines()
    i = header.split(",").index("mocs_id")
    assert row.split(",")[i] == "1"
    assert row.count(",") == len(F.SYSTEM + F.COLUMNS) - 1
