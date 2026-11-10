#!/usr/bin/env python3
"""
The City agency budgets explorer shows what NYC Open Data says, in the right year (#268).

Every Adopted and Modified figure in viz/agencies/data/nyc_budget.csv is recomputed from the
committed Open Data snapshot (source/agency-budget-qa/) by code/qa_agency_budget.py, which shares
no code with the pipeline, and compared to the dollar. These tests FAIL if:

  - any cell differs, or a unit is missing on either side;
  - the year rule breaks: Adopted Y must be financial_plan_amount from the June release tagged Y,
    and Modified Y current_modified_budget_amount from the June release tagged Y+1 (a CSV with
    every year moved by one, the 2026-11-09 bug, fails here);
  - the FY2026 adopted total is not $117,791,473,676 (OMB's printed FY2026 Adopted Budget, net
    $115,907,309,727 plus intra-city $1,884,163,949);
  - the newest year's Modified is not blank, or a community board is missing.

Run: python -m pytest code/test_qa_agency_budget.py
"""
import csv
import os
import re
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qa_agency_budget as qa  # noqa: E402

YEARS = list(range(2017, 2028))


def _rows():
    with open(qa.CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_every_cell_matches_open_data():
    res = qa.check()
    assert res["problems"] == [], res["problems"][:20]
    assert res["rows"] == res["units"] == 764
    # 764 units x 11 years x (Adopted, Modified)
    assert res["compared"] == 764 * len(YEARS) * 2


def test_the_june_releases_are_pinned():
    # The release each year's figures come from. A new pull that changes one of these needs a
    # person to look (the snapshot is replaced only on purpose).
    exp = qa.expected(qa.SNAPSHOT)
    assert exp["june"] == {2017: "20160615", 2018: "20170606", 2019: "20180614", 2020: "20190619",
                           2021: "20200630", 2022: "20210630", 2023: "20220614", 2024: "20230630",
                           2025: "20240630", 2026: "20250630", 2027: "20260630"}
    assert exp["years"] == YEARS


def test_year_rule_both_routes_to_adopted_agree():
    # financial_plan_amount in release Y == adopted_budget_amount in release Y+1, citywide, for
    # FY2017-FY2026: the data itself says which year each field describes.
    routes = qa.expected(qa.SNAPSHOT)["routes"]
    assert sorted(routes) == list(range(2017, 2027))
    for y, (fp, ad_next) in routes.items():
        assert fp == ad_next, (y, fp, ad_next)


def test_fy2026_adopted_total_is_omb_printed_total():
    assert qa.FY2026_ADOPTED == 117_791_473_676
    total = sum(Decimal(r["Adopted 2026"]) for r in _rows())
    assert total == Decimal(117_791_473_676)


def test_a_csv_one_year_late_fails():
    # The 2026-11-09 bug: every figure filed one year late. Build that file from the right one and
    # make sure the check catches it in every year.
    exp = qa.expected(qa.SNAPSHOT)
    shifted = []
    for r in _rows():
        s = dict(r)
        for y in YEARS:
            for label in ("Adopted", "Modified"):
                prev = r.get(f"{label} {y - 1}")
                s[f"{label} {y}"] = prev if prev is not None else "0"
        shifted.append(s)
    res = qa.compare(exp, shifted)
    bad_years = {int(m.group(1)) for p in res["problems"] for m in [re.search(r"Adopted (\d{4}): CSV", p)] if m}
    assert bad_years == set(YEARS), sorted(bad_years)


def test_newest_modified_is_not_yet_published():
    rows = _rows()
    assert all(r["Modified 2027"] == "" for r in rows)
    assert all(r["Modified 2026"] != "" for r in rows)


def test_all_59_community_boards_every_year():
    exp = qa.expected(qa.SNAPSHOT)
    boards = {b.zfill(3) for b in qa.COMMUNITY_BOARDS}
    assert len(boards) == 59
    for b in boards:
        units = [k for k in exp["cells"] if k[0] == b]
        assert units, b
        for y in YEARS:
            assert sum(exp["cells"][k][f"Adopted {y}"] for k in units) > 0, (b, y)
    names = {exp["names"][k][0] for k in exp["cells"] if k[0] in boards}
    assert len(names) == 59 and all("COMMUNITY BOARD" in n for n in names), sorted(names)


def test_omb_page_182e_manhattan_cb1():
    # OMB FY2026 Adopted Budget, Expense/Revenue/Contract volume, p. 182E (adopt25/erc6-25.pdf).
    c = qa.expected(qa.SNAPSHOT)["cells"]
    assert c[("341", "001")]["Adopted 2025"] == 267_484
    assert c[("341", "001")]["Modified 2025"] == 249_484
    assert c[("341", "002")]["Modified 2025"] == 190_939
    assert c[("341", "001")]["Adopted 2026"] == 275_060
    assert c[("341", "002")]["Adopted 2026"] == 27_245


def test_only_a_june_release_counts():
    rel = [{"fiscal_year": "2028", "publication_date": "20270115"},
           {"fiscal_year": "2028", "publication_date": "20270501"},
           {"fiscal_year": "2027", "publication_date": "20260630"}]
    assert qa.june_releases(rel) == {2027: "20260630"}, "FY2028 has no June release yet"
    rel.append({"fiscal_year": "2028", "publication_date": "20270626"})
    assert qa.june_releases(rel) == {2027: "20260630", 2028: "20270626"}
    assert qa.pad("40") == "040" and qa.pad("001") == "001"
