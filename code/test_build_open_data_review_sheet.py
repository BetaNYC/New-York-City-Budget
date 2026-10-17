"""Tests for build_open_data_review_sheet.py (#89 B12). Synthetic rows; no cache, no network.
Each test names the outcome that would make it fail."""
import csv
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_open_data_review_sheet as R
from test_diff_open_data_disclosure import od, ours


def _noms(n=10):
    return {c: [(2015, "x", od(id=f"row-{c}-{i}"), ours(row=str(i)))
                for i in range(n)] for c in R.CLASSES}


def test_sample_is_deterministic_and_sized_per_class():
    """FAILS if the same inputs and seed give a different draw, if a class gets more or fewer
    than its SAMPLE_SIZES rows, or if a different seed gives the same draw (the seed is unused)."""
    a = R.sample(_noms())
    assert a == R.sample(_noms())
    assert [c for c, *_ in a].count("grantee_differs") == R.SAMPLE_SIZES["grantee_differs"]
    assert [c for c, *_ in a].count("ein_differs") == R.SAMPLE_SIZES["ein_differs"]
    assert len(a) == sum(R.SAMPLE_SIZES.values()) == 20
    assert [t[3]["ref"] for t in R.sample(_noms(), seed=1)] != [t[3]["ref"] for t in a]


def test_small_class_is_taken_whole():
    """FAILS if a class smaller than its quota raises or is padded."""
    noms = _noms(3)
    assert len(R.sample(noms)) == 9


def test_sheet_has_both_sides_and_blank_verdicts():
    """FAILS if a row lacks either side's fields or source row, if the verdict/notes columns are
    pre-filled, or if review ids are not sequential."""
    text = R.sheet_csv(R.sample(_noms(2)))
    rows = list(csv.DictReader(io.StringIO(text)))
    assert [r["review_id"] for r in rows] == [f"R{i:02d}" for i in range(1, 7)]
    r = rows[0]
    assert list(r) == R.FIELDS
    assert r["open_data_row_id"].startswith("row-") and r["council_source_row"] == "f.xlsx:0"
    assert r["open_data_amount"] == r["council_amount"] == "5000"
    assert all(x["reviewer_verdict"] == "" and x["notes"] == "" for x in rows)


def test_nominations_are_sorted_and_classed():
    """FAILS if nominations come back in input order (the draw would depend on dict/file order)
    or under the wrong class."""
    a = od(id="row-b", name="A Org", ein="131111111", amount="100")
    b = ours(row="9", name="A Org", ein="131111111", amount="200")
    c = od(id="row-a", name="B Org", ein="132222222", amount="100")
    d = ours(row="8", name="B Org", ein="132222222", amount="300")
    noms = R.nominations([a, c], {2015: ("x", [b, d])})
    assert [t[2]["ref"] for t in noms["amount_differs"]] == ["row-a", "row-b"]
    assert noms["ein_differs"] == [] and noms["grantee_differs"] == []


def test_wrong_open_data_file_is_a_stop(tmp_path):
    """FAILS if a CSV whose sha256 is not the manifest's is used to build the sheet."""
    p = tmp_path / "4d7f-74pe.csv"
    p.write_text("x\n")
    with pytest.raises(SystemExit, match="sha256 differs"):
        R.build(str(p))
