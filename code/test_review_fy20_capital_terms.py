#!/usr/bin/env python3
"""
Tests for code/review_capital_sd.py on FY2020 (GitHub #109), run from
config/capital_sd/fy2020.toml. FY2020 has no Terms & Conditions in source/. FY2021-FY2027 stay
covered by their own test files.

Re-reads the committed PDF under source/FY20/ (encrypted, empty user password; pp.2-79 /Rotate
90). Golden rows are read off the rendered pages by a person (pp.2, 39, 46, 79, 80).

Run: pytest code/test_review_fy20_capital_terms.py
"""
import os
import sys

import pdfplumber
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import review_capital_sd as cap  # noqa: E402


@pytest.fixture(scope="module")
def capital(tmp_path_factory):
    out = cap.run(str(tmp_path_factory.mktemp("cap20")), do_ink=False, fy=2020)
    yield out
    cap.configure(2027)


def row(rows, sub_id, budget_line=None):
    hits = [r for r in rows if r["sub_id"] == sub_id and budget_line in (None, r["budget_line"])]
    assert len(hits) == 1, (sub_id, len(hits))
    return hits[0]


def test_part1_only_counts_and_totals(capital):
    rows, totals, review = capital
    assert len(rows) == 1663 and {r["part"] for r in rows} == {"I"}
    assert len(totals) == 24 and all(t["status"] == "OK" for t in totals)
    p1 = next(t for t in totals if t["name"] == "ALL")                            # p.79
    assert (p1["printed_count"], p1["printed_fy2020"], p1["printed_fy2021"]) == (1663, 701210000, 5000000)
    # No Part II or III: C3/C4 say so instead of flagging every DN row or crashing.
    assert not [x for x in review.rows if x["check_id"].startswith(("C1", "C2.summary", "C3.dn", "C4"))]


def test_summary_page_last():
    cap.configure(2020)
    try:
        with pdfplumber.open(cap.PDF) as pdf:
            s = cap.summary_page(pdf, None)          # p.80
    finally:
        cap.configure(2027)
    assert s == {"additions": 701210000, "rescindments": 46210000, "net": 655000000}


def test_extra_sub_ids_and_rotated_page(capital):
    rows, _, _ = capital
    r = row(rows, "AG CN001")                        # p.2, /Rotate 90
    assert (r["pdf_page"], r["budget_line"], r["boro"], r["fy2020"], r["sponsor"]) == \
        (2, "AG D001", "M", 200000, "RODRIGUEZ")
    assert row(rows, "E CNA02")["fy2020"] == 1500000                              # p.46
    assert row(rows, "HL NC02")["fy2020"] == 127000                               # p.54
    assert sorted(r["sponsor"] for r in rows if r["sub_id"] == "TF CN90") == \
        ["SPEAKER, COHEN", "SPEAKER, MOYA"]                                       # p.79, twice


def test_title_blank_line_joins(capital):
    rows, _, review = capital
    r = row(rows, "E CN817")                                                      # p.39
    assert r["title"] == "MORE ACCESSIBLEBATHROOMS ATPARK WEST HIGH SCHOOL (M535/M542)"
    assert not [x for x in review.rows if x["check_id"].startswith("C5.") and x["severity"] == "critical"]
    cap.configure(2022)
    try:
        assert "title_blank_line" not in cap.CFG and "wb_full_id" not in cap.CFG  # off elsewhere
    finally:
        cap.configure(2027)


def test_lowercase_borough_and_open_data(capital):
    rows, _, review = capital
    assert sorted(x["sub_id"] for x in review.rows if x["check_id"] == "C6.boro") == \
        ["F CN003", "HW CN006", "PV NC037"]                                       # `r`, as printed
    na = sorted((x["sub_id"], x["dollars"]) for x in review.rows if x["check_id"] == "C9.workbook_no_amount")
    assert na == [("E CN817", 170000), ("E CN832", 300000)]
    # With the full ID, `MT CN001` and `TF CN001` ($200,000 each on TF D005) are told apart.
    assert not [x for x in review.rows if x["check_id"] == "C9.workbook_title" and x["sub_id"] == "TF CN001"]
