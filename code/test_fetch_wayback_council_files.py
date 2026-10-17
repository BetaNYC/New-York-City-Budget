"""Tests for the pure parts of fetch_wayback_council_files.py (GitHub #86). No network."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_wayback_council_files as W


def test_cdx_url_carries_documented_params():
    u = W.cdx_url("council.nyc.gov/budget/", "prefix", ["statuscode:200"], "digest")
    for part in ("matchType=prefix", "output=json", "collapse=digest", "filter=statuscode%3A200",
                 "fl=timestamp%2Coriginal%2Cmimetype%2Cstatuscode%2Cdigest%2Clength"):
        assert part in u


def test_parse_cdx_header_row_and_empty():
    body = json.dumps([["timestamp", "original"], ["20140810034813", "http://x/a.xls"]]).encode()
    assert W.parse_cdx(body) == [{"timestamp": "20140810034813", "original": "http://x/a.xls"}]
    assert W.parse_cdx(b"") == [] and W.parse_cdx(b"[]") == []


def test_replay_url_uses_identity_flag_and_refuses_bad_timestamp():
    assert W.replay_url("20140810034813", "http://x/a.xls") == \
        "https://web.archive.org/web/20140810034813id_/http://x/a.xls"
    with pytest.raises(ValueError):
        W.replay_url("2014", "http://x/a.xls")


def test_two_captures_of_one_url_do_not_collide(tmp_path):
    a = W.file_path(str(tmp_path), "20140810034813", "http://x/funded_disclosure_FY2009.xls")
    b = W.file_path(str(tmp_path), "20250212200136", "http://x/funded_disclosure_FY2009.xls")
    assert a != b and os.path.basename(a) == "funded_disclosure_FY2009.xls"


def test_download_cap_refuses_new_files_but_serves_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(W, "DOWNLOAD_CAP", 1)
    p = W.file_path(str(tmp_path), "20140810034813", "http://x/a.xls")
    os.makedirs(os.path.dirname(p))
    with open(p, "wb") as fh:
        fh.write(b"cached")

    class NoNet:
        def get_cached(self, url, path):
            if os.path.exists(path):
                return open(path, "rb").read(), False
            raise AssertionError("network used")
    assert W.run_get(NoNet(), str(tmp_path), "20140810034813", "http://x/a.xls")[2] is False
    with pytest.raises(SystemExit):
        W.run_get(NoNet(), str(tmp_path), "20150101000000", "http://x/b.xls")
