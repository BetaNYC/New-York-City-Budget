#!/usr/bin/env python3
"""
Regression tests for parse_terms_legacy.py — the FY2015-FY2024 (unnumbered-header) Terms &
Conditions parser. Terms & Conditions documents print no totals, so there is no reconciliation;
these tests assert structural correctness and a concrete FY2022 content repro.

Source PDFs are committed under source/ in this repo, so the reparse layer always runs.

Run: pytest code/test_parse_terms_legacy.py
"""
import os, sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

COLS = ["item_number", "agency_name", "agency_code", "units_of_appropriation", "num_units",
        "report_deadlines", "coverage_period", "condition_text"]

# (prefix, source PDF, minimum expected condition count)
YEARS = [
    ("fy15", "source/FY15/fy2015-tc.pdf", 10),
    ("fy16", "source/FY16/fy2016-tandc.pdf", 20),
    ("fy17", "source/FY17/FY17-Terms-and-Conditions.pdf", 20),
    ("fy18", "source/FY18/FY18-Terms-and-Conditions.pdf", 25),
    ("fy21", "source/FY21/Fiscal-2021-Terms-and-Conditions.pdf", 35),
    ("fy22", "source/FY22/FY22-Terms-and-Conditions_FINAL.pdf", 40),
    ("fy23", "source/FY23/FY23-Terms-and-Conditions_FINAL_OMB-and-Council-Review-6.11.22.pdf", 45),
    ("fy24", "source/FY24/FY24-Terms-and-Conditions.pdf", 45),
]


def _parse(src):
    import parse_terms_legacy as P
    return P.parse(P.load_pages(os.path.join(REPO, src)))


@pytest.mark.parametrize("prefix,src,minitems", YEARS)
def test_legacy_structure(prefix, src, minitems):
    if not os.path.exists(os.path.join(REPO, src)):
        pytest.skip(f"source PDF missing: {src}")
    items = _parse(src)
    assert len(items) >= minitems, f"{prefix}: only {len(items)} conditions (< {minitems})"
    for it in items:
        assert set(it.keys()) == set(COLS)
        assert it["condition_text"].strip(), f"{prefix}: blank condition_text in {it}"
        # agency_code is a 3-digit budget code, or empty for a bare 'Capital Budget' item
        assert it["agency_code"] == "" or (len(it["agency_code"]) == 3 and it["agency_code"].isdigit())
        assert it["num_units"] == len(
            [u for u in it["units_of_appropriation"].split("; ") if u]), it


def test_fy22_acs_first_condition():
    """Concrete repro: FY22's first condition is ACS (068), UA 001/002/007/008, with the two
    printed 2022 report deadlines — the exact shape the unnumbered-header variant was built for."""
    items = _parse("source/FY22/FY22-Terms-and-Conditions_FINAL.pdf")
    acs = items[0]
    assert acs["agency_code"] == "068"
    assert "Children" in acs["agency_name"]
    assert {"001", "002", "007", "008"} <= set(acs["units_of_appropriation"].split("; "))
    assert "January 15, 2022" in acs["report_deadlines"]
    assert "July 15, 2022" in acs["report_deadlines"]


def test_capital_budget_items_present():
    """The bare 'Capital Budget' header shape (no agency code) must be captured as its own
    item(s) — a shape the numbered FY25-FY27 parser never sees."""
    items = _parse("source/FY22/FY22-Terms-and-Conditions_FINAL.pdf")
    caps = [it for it in items if it["agency_name"] == "Capital Budget"]
    assert caps, "no Capital Budget items parsed"
    for it in caps:
        assert it["agency_code"] == ""
        assert it["condition_text"].strip()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
