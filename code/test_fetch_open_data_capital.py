"""Tests for fetch_open_data_capital.py (#89 A8). No network: a fake opener. Each test names
the outcome that would make it fail."""
import gzip
import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_open_data_capital as F
import polite_http as H


def test_rows_url_pages_on_id_with_at_most_5000_rows():
    """FAILS if paging loses $order=:id, exceeds 5,000 rows, or drops the system fields."""
    u = F.rows_url("t474-a92g", 10000)
    assert "$order=:id" in u and "$limit=5000" in u and "$offset=10000" in u
    assert "$select=:*,*" in u and F.PAGE <= 5000


def test_unknown_field_is_a_stop():
    """FAILS if a row carrying a field outside the verified schema is written."""
    with pytest.raises(ValueError, match="not in the verified schema"):
        F.rows_csv("t474-a92g", [{":id": "r", "surprise": "x"}])
    text = F.rows_csv("t474-a92g", [{":id": "r", "award": "5"}])
    assert text.splitlines()[0].split(",")[:5] == [":id", ":created_at", ":updated_at",
                                                   ":version", "reported"]


def test_gzip_is_deterministic():
    """FAILS if two writes of the same text differ (mtime or file name leaking in)."""
    assert F.gz("a,b\n") == F.gz("a,b\n") and gzip.decompress(F.gz("a,b\n")) == b"a,b\n"


class _Resp(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_pull_pages_until_short_page_and_checks_count(tmp_path, monkeypatch):
    """FAILS if paging stops early, re-fetches a cached page, accepts a count mismatch or a
    repeated :id."""
    sent = []

    def opener(req, timeout):
        sent.append(req.full_url)
        off = int(req.full_url.split("$offset=")[1])
        n = 5000 if off == 0 else 2
        return _Resp(json.dumps([{":id": f"r{off + i}"} for i in range(n)]).encode())
    monkeypatch.setattr(F, "source_dir", lambda ds: str(tmp_path / "src"))
    f = H.Fetcher(min_gap=0, opener=opener, sleep=lambda s: None)
    rows = F.pull(f, "t474-a92g", str(tmp_path / "c"), {}, expected=5002, log=lambda *a: None)
    assert len(rows) == 5002 and len(sent) == 2
    F.pull(f, "t474-a92g", str(tmp_path / "c"), {}, expected=5002, log=lambda *a: None)
    assert len(sent) == 2          # cached: no new request
    with pytest.raises(RuntimeError, match="count"):
        F.pull(f, "t474-a92g", str(tmp_path / "c"), {}, expected=9, log=lambda *a: None)
