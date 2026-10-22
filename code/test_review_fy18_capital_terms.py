#!/usr/bin/env python3
"""
Tests for code/review_capital_sd.py and code/review_terms.py on FY2018 (GitHub #111), run from
config/capital_sd/fy2018.toml and config/terms/fy2018.toml. FY2019-FY2027 stay covered by their
own test files.

Re-reads the committed PDFs under source/FY18/ (the capital book is encrypted with an empty user
password and named "ResoA", but holds the supporting detail). Golden rows are read off the
rendered pages by a person (capital pp.4, 8, 43, 70; T&C pp.3, 15, 18).

Run: pytest code/test_review_fy18_capital_terms.py
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import review_capital_sd as cap  # noqa: E402
import review_terms as terms     # noqa: E402


@pytest.fixture(scope="module")
def capital(tmp_path_factory):
    out = cap.run(str(tmp_path_factory.mktemp("cap18")), do_ink=False, fy=2018)
    yield out
    cap.configure(2027)


@pytest.fixture(scope="module")
def tc(tmp_path_factory):
    out = terms.run(str(tmp_path_factory.mktemp("tc18")), do_ink=False, fy=2018)
    yield out
    terms.configure(2027)


def row(rows, part, sub_id):
    hits = [r for r in rows if r["part"] == part and r["sub_id"] == sub_id]
    assert len(hits) == 1, (sub_id, len(hits))
    return hits[0]


def test_capital_counts_and_totals(capital):
    rows, totals, review = capital
    assert sum(r["part"] == "I" for r in rows) == 1485 and sum(r["part"] == "II" for r in rows) == 233
    assert len(totals) == 35 and all(t["status"] == "OK" for t in totals)
    p1 = next(t for t in totals if t["part"] == "I" and t["name"] == "ALL")       # p.70
    assert (p1["printed_count"], p1["printed_fy2018"], p1["printed_fy2019"], p1["printed_fy2020"],
            p1["printed_fy2021"]) == (1485, 575000000, 28000000, 12000000, 0)
    # No summary page and no comparison source: C2 and C9 say so, nothing is flagged for them.
    assert not [x for x in review.rows if x["check_id"].startswith(("C1", "C2", "C4", "C5", "C9"))]


def test_capital_rows(capital):
    rows, _, review = capital
    r = row(rows, "I", "AG CN001")                                                # p.4
    assert (r["budget_line"], r["boro"], r["title"], r["fy2018"], r["sponsor"]) == \
        ("AG D001", "M", "COVELLO SENIOR CENTER", 6000000, "CITYWIDE, MARK-VIVERITO")
    r = row(rows, "I", "PV NC005")                                                # p.8, 3 lines
    assert r["sponsor"] == ("CITYWIDE, DEUTSCH, ESPINAL, EUGENE, LANDER, GENTILE, LEVIN, MAISEL, "
                            "WILLIAMS, GREENFIELD, CUMBO, VAN BRAMER")
    seat = sorted(x["sub_id"] for x in review.rows if x["check_id"] == "C6.sponsor_seat")
    assert len(seat) == 15 and seat[0] == "E CN765" and row(rows, "I", "E CN765")["sponsor"] == "DISTRICT 28"
    assert not [x for x in review.rows if x["check_id"] == "C6.sponsor_digit"]
    assert sorted(x["sub_id"] for x in review.rows if x["check_id"] == "C3.part2_only") == \
        ["AG TA001", "HH TA001", "HH TA003"]                                      # TA in Part II
    cap.configure(2020)
    try:
        assert "no_comparison_source" not in cap.CFG and "sponsor_digit_ok" not in cap.CFG
    finally:
        cap.configure(2027)


def test_terms_count_and_openings(tc):
    rows, review = tc
    assert [r["item_number"] for r in rows] == list(range(1, 34))
    assert not [x for x in review.rows if x["severity"] == "critical"]   # T1 counts 33 openings
    terms.configure(2022)
    try:
        assert "opening_phrases" not in terms.CFG and "all_lines_headings" not in terms.CFG
    finally:
        terms.configure(2027)


def test_terms_capital_and_two_agencies(tc):
    rows, _ = tc
    by = {r["item_number"]: r for r in rows}
    assert (by[2]["agency_name"], by[2]["budget_lines"], by[2]["kind"]) == \
        ("Capital Budget", "All Project Lines – All Projects", "capital")         # p.3
    assert by[4]["budget_lines"] == "HA-0001 – All Projects"                       # p.5
    assert by[17]["agency_name"] == "Department of Education; School Construction Authority"
    assert (by[17]["agency_code"], by[17]["budget_lines"]) == ("040; 040", "E2360 – All Projects")
    assert by[14]["condition_text"].endswith("for the following dates:")        # FSR table, p.15
    assert by[14]["units_of_appropriation"] == "040:All"
