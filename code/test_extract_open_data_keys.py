"""Tests for extract_open_data_keys.py (#89 A4). Synthetic CSVs; no cache, no network. Each test
names the outcome that would make it fail."""
import csv
import gzip
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_open_data_keys as X

HDR = ":id,:created_at,fiscal_year,mocs_id,ein,amount,bbl\n"


def test_keys_are_five_columns_as_served_and_deterministic(tmp_path):
    """FAILS if a column other than the five is kept, if a value is normalized (the 8-digit EIN
    is padded later, by the reader, never here), if row order changes, or if two runs give
    different bytes (gzip mtime/name leaking in)."""
    p = tmp_path / "od.csv"
    p.write_text(HDR + "row-b,t,2009,FY09 2,61629188,7481.3,0\nrow-a,t,2009,FY09 1,1,5,\n")
    data, n = X.keys_bytes(str(p))
    assert n == 2 and data == X.keys_bytes(str(p))[0]
    rows = list(csv.reader(io.StringIO(gzip.decompress(data).decode())))
    assert rows == [X.COLUMNS, ["row-b", "2009", "FY09 2", "61629188", "7481.3"],
                    ["row-a", "2009", "FY09 1", "1", "5"]]


def test_missing_column_is_a_stop(tmp_path):
    """FAILS if a CSV without one of the five columns produces a keys file."""
    p = tmp_path / "od.csv"
    p.write_text(":id,fiscal_year,ein,amount\nr,2009,1,5\n")
    with pytest.raises(SystemExit, match="missing columns"):
        X.keys_bytes(str(p))


def test_committed_keys_match_their_manifest_row():
    """FAILS if the committed .csv.gz is not the file its MANIFEST.csv row pins, or does not
    hold every Open Data row (97,002)."""
    with open(X.OUT, "rb") as f:
        raw = f.read()
    import hashlib
    assert hashlib.sha256(raw).hexdigest() == X.manifest_sha(os.path.basename(X.OUT))
    assert gzip.decompress(raw).decode().count("\n") == 97_003
