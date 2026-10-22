#!/usr/bin/env python3
"""
Tests for code/review_terms.py on FY2021 (GitHub #108), run from config/terms/fy2021.toml.
FY2021 has no capital supporting detail in source/ (its Resolution A book is another family).
FY2022-FY2027 stay covered by their own test files.

Re-reads the committed PDF under source/FY21/. Golden rows are read off the rendered pages by a
person (pp.2, 5, 8, 11, 13 of the T&C).

Run: pytest code/test_review_fy21_capital_terms.py
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import review_terms as terms     # noqa: E402


@pytest.fixture(scope="module")
def tc(tmp_path_factory):
    out = terms.run(str(tmp_path_factory.mktemp("tc21")), do_ink=False, fy=2021)
    yield out
    terms.configure(2027)


def test_unnumbered_count_and_no_critical(tc):
    rows, review = tc
    assert [r["item_number"] for r in rows] == list(range(1, 47))
    assert not [x for x in review.rows if x["severity"] == "critical"]   # T1 counts 46 openings


def test_body_margin_is_config():
    terms.configure(2021)
    try:
        assert terms.CFG["body_x0_max"] == 95            # p.2: body text at x0 = 90 pt
    finally:
        terms.configure(2027)
    assert "body_x0_max" not in terms.CFG                # default 80 for every other year


def test_multi_agency_headings(tc):
    rows, _ = tc
    by = {r["item_number"]: r for r in rows}
    assert by[1]["units_of_appropriation"] == \
        "068:001; 068:002; 068:007; 068:008; 072:001; 072:002; 072:003; 072:004"   # p.2
    assert by[12]["agency_name"] == "Department of Education; School Construction Authority"
    assert by[12]["agency_code"] == "040; 040"                                  # p.5, as printed
    assert by[12]["budget_lines"] == "E2364 and E2365 – All Projects"
    assert by[28]["budget_lines"] == "HD-0009 – All Projects"                   # p.11
    assert by[37]["agency_code"] == "260; 856"                                  # p.13: DYCD + DCAS


def test_capital_conditions_and_fsr_table(tc):
    rows, _ = tc
    by = {r["item_number"]: r for r in rows}
    assert by[2]["kind"] == by[3]["kind"] == "capital"                         # pp.2-3, HA-0001
    assert by[19]["condition_text"].endswith("for the following dates:")       # FSR table, p.8
    assert by[19]["units_of_appropriation"] == "040:All"
