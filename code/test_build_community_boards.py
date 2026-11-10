#!/usr/bin/env python3
"""
The community board table (#269) is the agency data, unchanged, for all 59 boards.

FAILS if viz/agencies/data/community_boards.csv is not what code/build_community_boards.py makes
from viz/agencies/data/nyc_budget.csv, if a board or year is missing, if a board's code is wrong,
if any amount differs from nyc_budget.csv, or if a total is not the sum of its units.

Run: python -m pytest code/test_build_community_boards.py
"""
import csv
import os
import sys
from collections import defaultdict
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_community_boards as b  # noqa: E402

YEARS = list(range(2017, 2028))

# Agency number -> name for the 59 boards, as NYC Open Data mwzb-yiwb gives them in the release of
# 2026-06-30 (read 2026-11-09).
OPEN_DATA_BOARDS = {
    **{str(340 + n): f"MANHATTAN COMMUNITY BOARD #{n}" for n in range(1, 13)},
    **{str(380 + n): f"BRONX COMMUNITY BOARD #{n}" for n in range(1, 13)},
    **{str(430 + n): f"QUEENS COMMUNITY BOARD #{n}" for n in range(1, 15)},
    **{str(470 + n): f"BROOKLYN COMMUNITY BOARD #{n}" for n in range(1, 19)},
    **{str(490 + n): f"STATEN ISLAND COMMUNITY BOARD #{n}" for n in range(1, 4)},
}


def _read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_committed_csv_is_current():
    assert b.main(["--check"]) == 0


def test_59_boards_every_year_with_the_right_codes():
    rows = _read(b.OUT)
    totals = [r for r in rows if r["unit_code"] == "total"]
    assert len(OPEN_DATA_BOARDS) == 59
    assert {(r["agency_code"], r["agency_name"]) for r in totals} == set(OPEN_DATA_BOARDS.items())
    assert len(totals) == 59 * len(YEARS)
    for code in OPEN_DATA_BOARDS:
        assert sorted(int(r["fiscal_year"]) for r in totals if r["agency_code"] == code) == YEARS, code


def test_every_amount_is_copied_unchanged():
    src = {(r["Fund"], r["Department ID"]): r for r in _read(b.SRC)}
    n = 0
    for r in _read(b.OUT):
        if r["unit_code"] == "total":
            continue
        s = src[(r["agency_name"], r["unit_code"])]
        assert r["unit_name"] == s["Department"]
        assert r["adopted"] == s[f"Adopted {r['fiscal_year']}"]
        assert r["modified"] == s[f"Modified {r['fiscal_year']}"]
        n += 1
    assert n == 173 * len(YEARS)


def test_totals_are_the_sum_of_units():
    sums = defaultdict(lambda: [Decimal(0), Decimal(0), False])
    totals = {}
    for r in _read(b.OUT):
        k = (r["agency_code"], r["fiscal_year"])
        if r["unit_code"] == "total":
            totals[k] = r
            continue
        sums[k][0] += Decimal(r["adopted"] or 0)
        if r["modified"] == "":
            sums[k][2] = True
        else:
            sums[k][1] += Decimal(r["modified"])
    for k, t in totals.items():
        a, m, blank = sums[k]
        assert Decimal(t["adopted"]) == a, k
        assert (t["modified"] == "") if blank else (Decimal(t["modified"]) == m), k


def test_sources_follow_the_year_rule_and_fy2027_modified_is_not_published():
    for r in _read(b.OUT):
        fy = int(r["fiscal_year"])
        assert f"(fiscal_year {fy}), financial_plan_amount" in r["adopted_source"]
        if fy == 2027:
            assert r["modified"] == "" and r["modified_source"] == "not yet published"
        else:
            assert f"(fiscal_year {fy + 1}), current_modified_budget_amount" in r["modified_source"]


def test_manhattan_cb1_matches_omb_page_182e():
    # OMB FY2026 Adopted Budget, Expense/Revenue/Contract volume, p. 182E.
    got = {(r["fiscal_year"], r["unit_code"]): r for r in _read(b.OUT) if r["agency_code"] == "341"}
    assert got[("2025", "001")]["adopted"] == "267484"
    assert got[("2025", "001")]["modified"] == "249484"
    assert got[("2025", "002")]["modified"] == "190939"
    assert got[("2026", "001")]["adopted"] == "275060"
    assert got[("2026", "002")]["adopted"] == "27245"
