#!/usr/bin/env python3
"""
build_community_boards.py — the 59 community boards' budgets, one table (#269).

Reads viz/agencies/data/nyc_budget.csv (built from NYC Open Data mwzb-yiwb by
code/agency_budget_cleanup.py) and writes viz/agencies/data/community_boards.csv: one row per
board, fiscal year and unit of appropriation, with the adopted and modified amounts and the Open
Data release each one comes from. viz/agencies/boards.html shows it, and anyone can download it.

Nothing is computed but sums of the City's own figures: each amount is copied from
nyc_budget.csv as it is, and `total` rows add a board's units for the year.

Each community board is its own agency in the budget: Manhattan 341-352, Bronx 381-392,
Brooklyn 471-488, Queens 431-444, Staten Island 491-493. nyc_budget.csv has agency names, not
numbers, so the number is the borough's base plus the board's number ("BROOKLYN COMMUNITY BOARD
#6" -> 470 + 6 = 476). code/test_build_community_boards.py checks every one against the codes
NYC Open Data gives.

  python3 code/build_community_boards.py           # write the CSV
  python3 code/build_community_boards.py --check   # exit 1 if the committed CSV is not current

Stdlib only.
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "viz", "agencies", "data", "nyc_budget.csv")
OUT = os.path.join(ROOT, "viz", "agencies", "data", "community_boards.csv")

BOROUGHS = {  # name in the data -> (short name, code base, number of boards)
    "MANHATTAN": ("Manhattan", 340, 12),
    "BRONX": ("Bronx", 380, 12),
    "BROOKLYN": ("Brooklyn", 470, 18),
    "QUEENS": ("Queens", 430, 14),
    "STATEN ISLAND": ("Staten Island", 490, 3),
}

# The June release each fiscal year's figures come from (NYC Open Data mwzb-yiwb, read
# 2026-11-09): Adopted Y is from the release tagged Y, Modified Y from the release tagged Y+1.
JUNE_RELEASES = {2017: "2016-06-15", 2018: "2017-06-06", 2019: "2018-06-14", 2020: "2019-06-19",
                 2021: "2020-06-30", 2022: "2021-06-30", 2023: "2022-06-14", 2024: "2023-06-30",
                 2025: "2024-06-30", 2026: "2025-06-30", 2027: "2026-06-30"}

FIELDS = ["borough", "board", "agency_code", "agency_name", "fiscal_year", "unit_code", "unit_name",
          "adopted", "modified", "adopted_source", "modified_source"]

NAME = re.compile(r"^(MANHATTAN|BRONX|BROOKLYN|QUEENS|STATEN ISLAND) COMMUNITY BOARD #(\d{1,2})$")


def years(header: list[str]) -> list[int]:
    return sorted(int(c.split(" ")[1]) for c in header if re.fullmatch(r"Adopted \d{4}", c))


def source(kind: str, fy: int) -> str:
    if kind == "adopted":
        return f"NYC Open Data mwzb-yiwb, release {JUNE_RELEASES[fy]} (fiscal_year {fy}), financial_plan_amount"
    if fy + 1 not in JUNE_RELEASES:
        return "not yet published"
    return (f"NYC Open Data mwzb-yiwb, release {JUNE_RELEASES[fy + 1]} (fiscal_year {fy + 1}), "
            "current_modified_budget_amount")


def build(src: str = SRC) -> str:
    with open(src, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fys = years(reader.fieldnames)
        rows = [r for r in reader if NAME.match(r["Fund"].strip())]
    out = []
    for r in rows:
        boro, n = NAME.match(r["Fund"].strip()).groups()
        short, base, count = BOROUGHS[boro]
        n = int(n)
        if not 1 <= n <= count:
            raise SystemExit(f"build_community_boards: unexpected board {r['Fund']!r}")
        for fy in fys:
            out.append({
                "borough": short, "board": n, "agency_code": str(base + n), "agency_name": r["Fund"].strip(),
                "fiscal_year": fy, "unit_code": r["Department ID"], "unit_name": r["Department"].strip(),
                "adopted": r[f"Adopted {fy}"], "modified": r[f"Modified {fy}"],
                "adopted_source": source("adopted", fy), "modified_source": source("modified", fy),
            })
    # A total row per board and year: the sum of its units, blank where nothing is published.
    totals = {}
    for o in out:
        k = (o["borough"], o["board"], o["agency_code"], o["agency_name"], o["fiscal_year"])
        t = totals.setdefault(k, {"adopted": Decimal(0), "modified": Decimal(0), "mod_blank": False})
        t["adopted"] += Decimal(o["adopted"] or 0)
        if o["modified"] == "":
            t["mod_blank"] = True
        else:
            t["modified"] += Decimal(o["modified"])
    for (b, n, code, name, fy), t in totals.items():
        out.append({"borough": b, "board": n, "agency_code": code, "agency_name": name, "fiscal_year": fy,
                    "unit_code": "total", "unit_name": "TOTAL, ALL UNITS",
                    "adopted": _fmt(t["adopted"]), "modified": "" if t["mod_blank"] else _fmt(t["modified"]),
                    "adopted_source": source("adopted", fy), "modified_source": source("modified", fy)})
    order = {name: i for i, name in enumerate(BOROUGHS[k][0] for k in BOROUGHS)}
    out.sort(key=lambda o: (order[o["borough"]], o["board"], o["fiscal_year"],
                            o["unit_code"] == "total", o["unit_code"]))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(out)
    return buf.getvalue()


def _fmt(d: Decimal) -> str:
    return str(int(d)) if d == d.to_integral_value() else f"{d:.2f}"


def main(argv: list[str]) -> int:
    text = build()
    if "--check" in argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != text:
            print("viz/agencies/data/community_boards.csv is not current: run python3 code/build_community_boards.py")
            return 1
        return 0
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(f"wrote {os.path.relpath(OUT, ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
