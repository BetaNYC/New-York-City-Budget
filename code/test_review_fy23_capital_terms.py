#!/usr/bin/env python3
"""
Tests for code/review_capital_sd.py and code/review_terms.py on FY2023 (GitHub #106), run from
config/capital_sd/fy2023.toml and config/terms/fy2023.toml. FY2024-FY2027 stay covered by their
own test files.

Both re-read the committed PDFs under source/FY23/. Golden rows are read off the rendered pages by
a person (pp.4, 11, 48, 71 of the capital book; pp.2, 9, 16 of the T&C).

Run: pytest code/test_review_fy23_capital_terms.py
"""
import os
import sys

import pdfplumber
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import review_capital_sd as cap  # noqa: E402
import review_terms as terms     # noqa: E402


@pytest.fixture(scope="module")
def capital(tmp_path_factory):
    out = cap.run(str(tmp_path_factory.mktemp("cap23")), do_ink=False, fy=2023)
    yield out
    cap.configure(2027)


def row(rows, part, sub_id):
    hits = [r for r in rows if r["part"] == part and r["sub_id"] == sub_id]
    assert len(hits) == 1, (part, sub_id, len(hits))
    return hits[0]


def test_counts_and_totals(capital):
    rows, totals, review = capital
    assert sum(r["part"] == "I" for r in rows) == 1393
    assert sum(r["part"] == "II" for r in rows) == 154
    assert len(totals) == 32 and all(t["status"] == "OK" for t in totals)
    assert next(t for t in totals if t["part"] == "I" and t["name"] == "ALL")["printed_fy2023"] == 879676000
    assert next(t for t in totals if t["part"] == "II" and t["name"] == "ALL")["printed_fy2023"] == 188160000
    assert not [x for x in review.rows if x["check_id"].startswith(("C1", "C2.summary", "C4", "C6"))]


def test_summary_page():
    cap.configure(2023)
    try:
        with pdfplumber.open(cap.PDF) as pdf:
            s = cap.summary_page(pdf, None)          # p.71
    finally:
        cap.configure(2027)
    assert s == {"additions": 879676000, "rescindments": 179676000, "net": 700000000}


def test_golden_rows(capital):
    rows, _, _ = capital
    r = row(rows, "I", "AG NC002")                   # p.4
    assert (r["budget_line"], r["boro"], r["title"], r["fy2023"], r["sponsor"]) == \
        ("AG DN184", "X", "THE HEBREW HOME FOR THE AGED AT RIVERDALE", 350000, "DINOWITZ")
    r = row(rows, "I", "HA RR002")                   # p.48: an RR row, borough A, no sponsor
    assert (r["budget_line"], r["boro"], r["title"], r["fy2023"], r["sponsor"]) == \
        ("HA D001", "A", "SMITH HOUSES", 2681000, "")
    # p.48: P CN001 sits on HA D001 next to HA CN001 (one ID number, two agencies)
    assert row(rows, "I", "P CN001")["fy2023"] == 2700000
    assert row(rows, "I", "HA CN001")["fy2023"] == 810000
    assert sum(" RR" in r["sub_id"] for r in rows if r["part"] == "I") == 15


def test_rr_series_listed_once(capital):
    _, _, review = capital
    rr = [x for x in review.rows if x["check_id"] == "C3.id_series"]
    assert len(rr) == 1 and rr[0]["dollars"] == 22633000 and rr[0]["note"].count("(no sponsor)") == 15


def test_part2_only_rows_are_the_ma_series(capital):
    rows, _, review = capital
    p1 = {(r["sub_id"], r["budget_line"]) for r in rows if r["part"] == "I"}
    only = [r for r in rows if r["part"] == "II" and (r["sub_id"], r["budget_line"]) not in p1]
    assert len(only) == 39
    assert all(r["sub_id"].split()[-1].startswith("MA") and r["budget_line"].split()[-1].startswith("0N")
               for r in only)
    assert sum(r["fy2023"] for r in only) == 78861000
    assert not [x for x in review.rows if x["check_id"] == "C3.part2_only"]


def test_open_data_blank_amount_row_is_listed_not_joined(capital):
    _, _, review = capital
    na = [x for x in review.rows if x["check_id"] == "C9.workbook_no_amount"]
    assert [(x["sub_id"], x["pdf_page"], x["dollars"]) for x in na] == [("E CN136", 11, 150000)]
    left = [x for x in review.rows if x["check_id"] == "C9.workbook"]
    assert [x["sub_id"] for x in left] == ["E CN136"]   # the PDF's $150,000; t474 has no amount


def test_open_data_mojibake_and_reused_ids(capital):
    _, _, review = capital
    cap.configure(2023)                               # other tests reset the module to FY2027
    assert cap.wb_text("Cab├ín") == "Cabán" and cap.wb_text("Oss├⌐") == "Ossé"
    sp = [x for x in review.rows if x["check_id"] == "C9.workbook_sponsor"]
    # 15 RR rows print no sponsor (t474 "NA"); 6 abbreviate the caucus as "BLAC" in t474
    assert len(sp) == 21
    assert sum("'' vs workbook 'NA'" in x["note"] for x in sp) == 15
    assert sum("BLAC'" in x["note"] or "BLAC," in x["note"] for x in sp) == 6
    # HD NC040 / HR NC040 share HD D020: each is compared with its own t474 row
    assert not [x for x in review.rows if x["sub_id"] in ("HD NC040", "HR NC040", "P CN001")
                and x["check_id"].startswith("C9")]


def test_cover_seal_images_are_covered_only_where_configured():
    cap.configure(2023)
    try:
        assert cap.CFG["ink_cover_image_pages"] == [1]
    finally:
        cap.configure(2027)
    assert "ink_cover_image_pages" not in cap.CFG


@pytest.fixture(scope="module")
def tc(tmp_path_factory):
    out = terms.run(str(tmp_path_factory.mktemp("tc23")), do_ink=False, fy=2023)
    yield out
    terms.configure(2027)


def test_terms_unnumbered_conditions(tc):
    rows, review = tc
    assert [r["item_number"] for r in rows] == list(range(1, 61))
    assert not [x for x in review.rows if x["severity"] == "critical"]
    assert rows[0]["units_of_appropriation"] == "068:001; 068:002; 068:007; 068:008"   # p.2
    assert rows[1]["agency_name"] == ("Administration for Children’s Services; "
                                      "Department of Youth and Community Development")


def test_terms_capital_budget_conditions(tc):
    rows, _ = tc
    by = {r["item_number"]: r for r in rows}
    assert [by[n]["kind"] for n in (3, 4, 5, 35)] == ["capital", "capital", "capital", "capital+expense"]
    assert by[5]["budget_lines"] == "DP-0001– All Projects; DP-0002 – All Projects"   # p.3 as printed


def test_terms_fsr_table(tc):
    rows, _ = tc
    by = {r["item_number"]: r for r in rows}
    assert by[24]["condition_text"].endswith("for the following dates:")             # p.9
