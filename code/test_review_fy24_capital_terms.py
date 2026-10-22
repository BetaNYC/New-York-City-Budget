#!/usr/bin/env python3
"""
Tests for code/review_capital_sd.py and code/review_terms.py on FY2024 (GitHub #105), run from
config/capital_sd/fy2024.toml and config/terms/fy2024.toml. FY2025-FY2027 stay covered by their
own test files.

Both re-read the committed PDFs under source/FY24/. The capital book is AES-256 encrypted with an
empty user password; pdfplumber opens it as is. Golden rows are read off the rendered pages by a
person (pp.4, 5, 65 of the capital book; pp.2, 16, 21, 23 of the T&C).

Run: pytest code/test_review_fy24_capital_terms.py
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
    out = cap.run(str(tmp_path_factory.mktemp("cap24")), do_ink=False, fy=2024)
    yield out
    cap.configure(2027)


def row(rows, part, sub_id):
    hits = [r for r in rows if r["part"] == part and r["sub_id"] == sub_id]
    assert len(hits) == 1, (part, sub_id, len(hits))
    return hits[0]


def test_counts_and_totals(capital):
    rows, totals, review = capital
    assert sum(r["part"] == "I" for r in rows) == 1241
    assert sum(r["part"] == "II" for r in rows) == 123
    assert len(totals) == 32 and all(t["status"] == "OK" for t in totals)
    assert next(t for t in totals if t["part"] == "I" and t["name"] == "ALL")["printed_fy2024"] == 839969000
    assert not [x for x in review.rows if x["check_id"].startswith(("C1", "C2.summary", "C4", "C6"))]


def test_summary_page_prints_less_with_a_colon():
    cap.configure(2024)
    try:
        with pdfplumber.open(cap.PDF) as pdf:
            s = cap.summary_page(pdf, None)          # p.61: "Less: Rescindments ..."
    finally:
        cap.configure(2027)
    assert s == {"additions": 839969000, "rescindments": 189969000, "net": 650000000}


def test_golden_rows(capital):
    rows, _, _ = capital
    r = row(rows, "I", "AG CN001")                   # p.4
    assert (r["budget_line"], r["boro"], r["title"], r["fy2024"], r["sponsor"]) == \
        ("AG D001", "M", "SIROVICH CENTER ROOF REHAB", 236000, "RIVERA")
    assert row(rows, "I", "E CN019")["sponsor"] == "SPEAKER, HUDSON"   # p.5: the comma is printed


def test_negative_part2_only_row(capital):
    rows, _, review = capital
    r = row(rows, "II", "HL TA001")                  # p.65, -40,000 on HL RN404
    assert r["fy2024"] == -40000
    assert r["title"] == "SEC249 ADJUSTMENT FOR THE SIUH NORTHWELL HEALTH CARDIAC IMAGING PROJ"
    assert [x["sub_id"] for x in review.rows if x["check_id"] == "C3.part2_only"] == ["HL TA001"]


def test_open_data_utf8_mojibake_decoded(capital):
    _, _, review = capital
    cap.configure(2024)                               # other tests reset the module to FY2027
    assert cap.wb_text("Avil├⌐s") == "Avilés" and cap.wb_text("Vel├ízquez") == "Velázquez"
    sp = [x for x in review.rows if x["check_id"] == "C9.workbook_sponsor"]
    assert len(sp) == 14                              # 12 of them print TECHNICAL ADJUSTMENT
    assert sum("'TECHNICAL ADJUSTMENT'" in x["note"] for x in sp) == 12


@pytest.fixture(scope="module")
def tc(tmp_path_factory):
    out = terms.run(str(tmp_path_factory.mktemp("tc24")), do_ink=False, fy=2024)
    yield out
    terms.configure(2027)


def test_terms_unnumbered_conditions(tc):
    rows, review = tc
    assert [r["item_number"] for r in rows] == list(range(1, 62))
    assert not [x for x in review.rows if x["severity"] == "critical"]
    assert rows[0]["units_of_appropriation"] == "068:001; 068:002; 068:007; 068:008"   # p.2


def test_terms_codeless_and_wrapped_headings(tc):
    rows, review = tc
    by = {r["item_number"]: r for r in rows}
    assert by[44]["agency_name"] == ("Department of Transportation; Department of Citywide "
                                     "Administrative Services; Department of Parks and Recreation")
    assert by[44]["agency_code"] == "; ; "                       # p.16: no codes printed
    assert by[56]["agency_name"] == "Office of Criminal Justice"  # p.21: regular type
    assert "heading_not_bold" in by[56]["flags"]
    assert by[56]["units_of_appropriation"] == "128:003; 128:004"  # printed "[ 003]"
    first = by[61]["agency_name"].split("; ")
    assert "Office of Technological Innovation/Department of Information Telecommunication " \
           "Services" in first                                   # p.23, wrapped over two lines
    assert sum(x["check_id"] == "T2.no_agency_code" for x in review.rows) == 5


def test_terms_white_boxes_are_not_tables(tc):
    rows, _ = tc
    by = {r["item_number"]: r for r in rows}
    assert by[21]["condition_text"].endswith("for the following dates:")
    assert "Unit of Appropriation [890]" in by[44]["heading_raw"]
