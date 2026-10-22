#!/usr/bin/env python3
"""
Tests for code/review_capital_sd.py and code/review_terms.py on FY2022 (GitHub #107), run from
config/capital_sd/fy2022.toml and config/terms/fy2022.toml. FY2023-FY2027 stay covered by their
own test files.

Both re-read the committed PDFs under source/FY22/. Golden rows are read off the rendered pages by
a person (pp.4, 72, 82, 86 of the capital book; pp.2, 8-11 of the T&C).

Run: pytest code/test_review_fy22_capital_terms.py
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
    out = cap.run(str(tmp_path_factory.mktemp("cap22")), do_ink=False, fy=2022)
    yield out
    cap.configure(2027)


def row(rows, part, sub_id):
    hits = [r for r in rows if r["part"] == part and r["sub_id"] == sub_id]
    assert len(hits) == 1, (part, sub_id, len(hits))
    return hits[0]


def test_counts_and_totals(capital):
    rows, totals, review = capital
    assert sum(r["part"] == "I" for r in rows) == 1462
    assert sum(r["part"] == "II" for r in rows) == 179
    assert len(totals) == 34 and all(t["status"] == "OK" for t in totals)
    assert next(t for t in totals if t["part"] == "I" and t["name"] == "ALL")["printed_fy2022"] == 704495000
    assert next(t for t in totals if t["part"] == "II" and t["name"] == "ALL")["printed_fy2023"] == 19730000
    assert not [x for x in review.rows if x["check_id"].startswith(("C1", "C2.summary", "C4"))]


def test_summary_page():
    cap.configure(2022)
    try:
        with pdfplumber.open(cap.PDF) as pdf:
            s = cap.summary_page(pdf, None)          # p.72
    finally:
        cap.configure(2027)
    assert s == {"additions": 704495000, "rescindments": 29495000, "net": 675000000}


def test_extra_sub_ids_are_rows(capital):
    rows, _, _ = capital
    r = row(rows, "I", "AG TANC1")                   # p.4: an ID that is not two letters + digits
    assert (r["budget_line"], r["boro"], r["fy2022"], r["sponsor"]) == \
        ("AG DN216", "A", 331000, "TREYGER, TECHNICAL ADJUSTMENTS")
    assert row(rows, "II", "PW KBP01")["fy2022"] == 1551000                      # p.82
    cap.configure(2022)
    try:
        assert cap.SUB_ID_EXTRA_RE.match("TANC1") and not cap.SUB_ID_EXTRA_RE.match("TANC9")
    finally:
        cap.configure(2027)
    assert not cap.SUB_ID_EXTRA_RE.match("TANC1")    # off for other years


def test_dollar_inside_brackets_is_negative(capital):
    rows, _, review = capital
    assert cap.AMOUNT_RE.match("($72,000)") and cap.money("($72,000)") == -72000
    assert row(rows, "II", "PW MBP01")["fy2022"] == -72000                       # p.82
    assert not [x for x in review.rows if x["check_id"].startswith("C4")]        # p.86 org line ties


def test_part2_only_borough_president_rows_are_critical(capital):
    _, _, review = capital
    crit = sorted(x["sub_id"] for x in review.rows if x["check_id"] == "C3.part2_only")
    assert crit == ["HL KBP01", "PW KBP01", "PW KBP02", "PW MBP01"]


def test_printed_vacancies_and_lowercase_borough(capital):
    rows, _, review = capital
    assert row(rows, "I", "E CN270")["sponsor"] == "CD 22"                       # p.17, as printed
    assert row(rows, "I", "P CN039")["boro"] == "x"                              # p.60, as printed
    assert sum(x["check_id"] == "C6.sponsor_digit" for x in review.rows) == 28


def test_open_data_blank_amount_and_ta_series(capital):
    _, _, review = capital
    na = [x for x in review.rows if x["check_id"] == "C9.workbook_no_amount"]
    assert [(x["sub_id"], x["pdf_page"], x["dollars"]) for x in na] == [("E CN673", 34, 55000)]
    ta = [x for x in review.rows if x["check_id"] == "C3.id_series"]
    assert len(ta) == 1 and ta[0]["dollars"] == 13394000 and ta[0]["note"].count("(no sponsor)") == 13


@pytest.fixture(scope="module")
def tc(tmp_path_factory):
    out = terms.run(str(tmp_path_factory.mktemp("tc22")), do_ink=False, fy=2022)
    yield out
    terms.configure(2027)


def test_terms_unnumbered_no_furniture(tc):
    rows, review = tc
    assert [r["item_number"] for r in rows] == list(range(1, 51))
    assert not [x for x in review.rows if x["severity"] == "critical"]
    assert rows[0]["units_of_appropriation"] == "068:001; 068:002; 068:007; 068:008"   # p.2


def test_terms_headings_as_printed(tc):
    rows, _ = tc
    by = {r["item_number"]: r for r in rows}
    assert by[26]["agency_name"] == "Department of Education (40)"     # p.10: a two-digit code
    assert by[26]["agency_code"] == ""
    assert len(by[28]["agency_name"].split("; ")) == 10                # p.11: ten agencies
    assert by[28]["agency_code"].split("; ")[2] == ""                  # HPD printed with no code
    assert by[21]["condition_text"].endswith("for the following dates:")   # FSR table, pp.8-9
