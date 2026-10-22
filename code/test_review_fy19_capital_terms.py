#!/usr/bin/env python3
"""
Tests for code/review_capital_sd.py on FY2019 (GitHub #110), run from
config/capital_sd/fy2019.toml (layout = "grid": the book is an Excel print with drawn cell
borders). FY2019 has no Terms & Conditions in source/. FY2020-FY2027 stay covered by their own
test files.

Re-reads the committed PDF under source/FY19/. Golden rows are read off the rendered pages by a
person (pp.1, 12, 40, 54, 55).

Run: pytest code/test_review_fy19_capital_terms.py
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import review_capital_sd as cap  # noqa: E402


@pytest.fixture(scope="module")
def capital(tmp_path_factory):
    out = cap.run(str(tmp_path_factory.mktemp("cap19")), do_ink=False, fy=2019)
    yield out
    cap.configure(2027)


def row(rows, sub_id, budget_line=None):
    hits = [r for r in rows if r["sub_id"] == sub_id and budget_line in (None, r["budget_line"])]
    assert len(hits) == 1, (sub_id, len(hits))
    return hits[0]


def test_counts_and_the_one_total(capital):
    rows, totals, review = capital
    assert len(rows) == 1625 and {r["part"] for r in rows} == {"I"}
    assert len(totals) == 1                                                       # p.54, no label
    t = totals[0]
    assert (t["printed_count"], t["status"]) == (None, "OK")
    assert (t["printed_fy2019"], t["printed_fy2020"], t["printed_fy2021"], t["printed_fy2022"]) == \
        (614910000, 15900000, 0, 0)                                               # `6` + `14,910,000`
    assert not [x for x in review.rows if x["check_id"].startswith(("C1", "C2", "C5", "C3.dn", "C4"))]
    assert not [x for x in review.rows if x["check_id"] in ("C6.orphan", "C6.unconsumed", "H3.page_map",
                                                            "H4.header", "C6.cd_unknown")]


def test_grid_row_fields(capital):
    rows, _, _ = capital
    r = row(rows, "AG CN002")                                                     # p.1, first row
    assert (r["pdf_page"], r["boro"], r["budget_line"], r["council_district"], r["sponsor"]) == \
        (1, "X", "HD D024", "16", "Gibson")
    assert (r["title"], r["description"], r["description_raw"]) == \
        ("VOLUNTEERS OF AMERICA", "CLARKE PLACE SENIOR RESIDENCE PROJECT",
         "--CLARKE PLACE SENIOR RESIDENCE PROJECT")
    assert (r["fy2019"], r["fy2020"], r["fy2020_printed"]) == (250000, 0, "-")
    r = row(rows, "CS NC001")                                                     # p.1, two codes
    assert (r["sponsor_raw"], r["sponsor"], r["fy2019"]) == ("00, 37", "Speaker, Espinal", 3640000)
    r = row(rows, "E CN001")                                                      # p.1, two title lines
    assert r["title_raw"] == "[SCA] [02M077/02M198] LOWER\nLAB/ISADOR E. IDA STRAUS"
    assert row(rows, "HL NC57")["fy2019"] == 546000                               # p.36, extra_sub_ids


def test_key_to_cd(capital):
    rows, _, review = capital
    # p.55: "Caucus Black, Latino and Asian97" -- the name runs into the district's digits.
    assert [x["pdf_page"] for x in review.rows if x["check_id"] == "C6.key_overrun"] == [55]
    r = row(rows, "PV NC071")                                                     # p.49
    assert "Caucus Black, Latino and Asian" in r["sponsor"] and "Brooklyn Delegation" in r["sponsor"]


def test_flags_as_printed(capital):
    rows, _, review = capital
    assert sorted(x["sub_id"] for x in review.rows if x["check_id"] == "C6.boro") == \
        ["E CN161", "E CN227", "E CN403"]                                         # `k`, as printed
    r = row(rows, "HW CN030")                                                     # p.40
    assert (r["council_district"], r["title"]) == ("49, 00", "DOT REPAVING IN DISTRICT 31")
    assert [x["sub_id"] for x in review.rows if x["check_id"] == "C9.workbook_cd"] == ["HW CN030"]
    assert not [x for x in review.rows if x["check_id"] == "C9.workbook"]         # 1,628 / 1,628
    cap.configure(2020)
    try:
        assert "layout" not in cap.CFG                                            # off elsewhere
    finally:
        cap.configure(2027)
