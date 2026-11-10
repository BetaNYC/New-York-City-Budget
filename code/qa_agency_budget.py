#!/usr/bin/env python3
"""
qa_agency_budget.py — check every figure the City agency budgets explorer shows (#268).

The explorer (viz/agencies/) loads viz/agencies/data/nyc_budget.csv: one row per agency x unit
of appropriation, with "Adopted YYYY" and "Modified YYYY" for FY2017 onward. This checker
recomputes every one of those cells from a snapshot of NYC Open Data mwzb-yiwb
(source/agency-budget-qa/, pulled by code/fetch_agency_budget_qa.py), with its own code (it
imports nothing from code/agency_budget_cleanup.py), and compares them to the dollar.

THE YEAR RULE it applies (the 2026-11-09 correction, nyc-budget-viz#3/#4):

  The June release of fiscal_year tag Y is the tag's latest publication_date, and it must be
  dated in June of calendar year Y-1 (NYC adopts FY Y in June, before July 1).
  Adopted Y  = sum(financial_plan_amount)          in the June release tagged Y
  Modified Y = sum(current_modified_budget_amount) in the June release tagged Y+1
  The newest year's Modified is blank ("Not yet published") until tag Y+1's June release exists.

It also checks the rule against the data itself: for every Y, citywide financial_plan_amount in
release Y equals adopted_budget_amount in release Y+1, to the dollar. And it pins the FY2026
adopted total, $117,791,473,676, which is OMB's printed FY2026 Adopted Budget (net
$115,907,309,727 plus intra-city $1,884,163,949; adopt25/erc6-25.pdf, p. 1E).

  python3 code/qa_agency_budget.py                    # check the CSV against the committed snapshot
  python3 code/qa_agency_budget.py --snapshot DIR     # against another snapshot (e.g. a fresh pull)
  python3 code/qa_agency_budget.py --live             # pull a fresh snapshot to a temp dir first

Exit 0 when every cell matches, 1 otherwise. Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile
from collections import defaultdict
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SNAPSHOT = os.path.join(ROOT, "source", "agency-budget-qa")
CSV_PATH = os.path.join(ROOT, "viz", "agencies", "data", "nyc_budget.csv")

FIRST_YEAR = 2017
FY2026_ADOPTED = 115_907_309_727 + 1_884_163_949  # = 117,791,473,676

# The 59 community boards, by agency number (each board is its own agency in the budget).
COMMUNITY_BOARDS = ([str(n) for n in range(341, 353)] + [str(n) for n in range(381, 393)]
                    + [str(n) for n in range(471, 489)] + [str(n) for n in range(431, 445)]
                    + [str(n) for n in range(491, 494)])


def pad(code: str) -> str:
    """Releases before 2023 write '40' and '1'; later ones '040' and '001'."""
    c = (code or "").strip()
    return c.zfill(3) if c.isdigit() else c


def money(s: str) -> Decimal:
    return Decimal(s) if s not in ("", None) else Decimal(0)


def read(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def june_releases(releases: list[dict]) -> dict[int, str]:
    """{tag: publication_date} of each tag's June release. A tag whose latest release is not
    dated in June of tag-1 is left out (still in progress, or something new to look at)."""
    latest: dict[int, str] = {}
    for r in releases:
        t = int(r["fiscal_year"])
        if r["publication_date"] > latest.get(t, ""):
            latest[t] = r["publication_date"]
    return {t: d for t, d in latest.items() if d[:6] == f"{t - 1}06"}


def expected(snapshot_dir: str) -> dict:
    """Recompute the explorer's figures from the snapshot.

    Returns {"cells": {(agency_no, unit_no): {"Adopted Y": Decimal|None, "Modified Y": ...}},
             "names": {(agency_no, unit_no): (agency_name, unit_name)}, "june": {...},
             "years": [...], "routes": {Y: (finplan Y, adopted Y+1)}}"""
    june = june_releases(read(os.path.join(snapshot_dir, "releases.csv")))
    years = [y for y in sorted(june) if y >= FIRST_YEAR]
    if not years or years != list(range(years[0], years[-1] + 1)):
        raise SystemExit(f"qa: June releases are not a run of years: {sorted(june)}")
    fp: dict = defaultdict(Decimal)
    cm: dict = defaultdict(Decimal)
    ad_city: dict = defaultdict(Decimal)
    fp_city: dict = defaultdict(Decimal)
    names: dict = {}
    keys = set()
    for r in read(os.path.join(snapshot_dir, "by_unit.csv")):
        t, d = int(r["fiscal_year"]), r["publication_date"]
        if june.get(t) != d:
            continue
        k = (pad(r["agency_number"]), pad(r["unit_appropriation_number"]))
        keys.add(k)
        fp[(k, t)] += money(r["financial_plan_amount"])
        cm[(k, t)] += money(r["current_modified_budget_amount"])
        fp_city[t] += money(r["financial_plan_amount"])
        ad_city[t] += money(r["adopted_budget_amount"])
        if k not in names or t >= names[k][0]:
            names[k] = (t, r["agency_name"].strip(), r["unit_appropriation_name"].strip())
    # Every tag with a June release is a year the explorer should show. When the FY2028 budget
    # is adopted (June 2027), a fresh pull adds 2028 here, and the check fails until the explorer
    # shows it too: that is the signal to extend it.
    shown = years
    cells = {}
    for k in keys:
        row = {}
        for y in shown:
            row[f"Adopted {y}"] = fp[(k, y)]
            row[f"Modified {y}"] = cm[(k, y + 1)] if (y + 1) in june else None
        cells[k] = row
    routes = {y: (fp_city[y], ad_city[y + 1]) for y in shown if (y + 1) in june}
    return {"cells": cells, "names": {k: v[1:] for k, v in names.items()}, "june": june,
            "years": shown, "routes": routes}


def compare(exp: dict, csv_rows: list[dict]) -> dict:
    """Compare every cell. Returns counts and the first problems found."""
    by_name: dict = defaultdict(list)
    for k, (agency, _unit) in exp["names"].items():
        by_name[(agency, k[1])].append(k)
    ambiguous = {nk: ks for nk, ks in by_name.items() if len(ks) > 1}
    problems: list[str] = []
    compared = 0
    seen = set()
    for row in csv_rows:
        nk = (row["Fund"].strip(), row["Department ID"].strip())
        ks = by_name.get(nk, [])
        if len(ks) != 1:
            problems.append(f"CSV row {nk}: {'no' if not ks else len(ks)} matching unit(s) in the snapshot")
            continue
        k = ks[0]
        seen.add(k)
        if exp["names"][k][1] != row["Department"].strip():
            problems.append(f"{k}: unit name {row['Department']!r}, snapshot {exp['names'][k][1]!r}")
        for col, want in exp["cells"][k].items():
            got = row.get(col)
            compared += 1
            if got is None:
                problems.append(f"{k}: CSV has no column {col!r}")
            elif want is None:
                if got != "":
                    problems.append(f"{k} {col}: {got!r}, but it is not published yet (want blank)")
            elif got == "" or Decimal(got) != want:
                problems.append(f"{k} {col}: CSV {got!r}, Open Data {want}")
    for k in sorted(set(exp["cells"]) - seen):
        problems.append(f"{k} {exp['names'][k]}: in the snapshot, not in the CSV")
    return {"compared": compared, "problems": problems, "ambiguous": ambiguous,
            "rows": len(csv_rows), "units": len(exp["cells"])}


def check(snapshot_dir: str = SNAPSHOT, csv_path: str = CSV_PATH) -> dict:
    exp = expected(snapshot_dir)
    rows = read(csv_path)
    res = compare(exp, rows)
    p = res["problems"]
    for y, (a, b) in sorted(exp["routes"].items()):
        if a != b:
            p.append(f"year rule: citywide financial_plan_amount tag {y} = {a}, adopted_budget_amount tag {y + 1} = {b}")
    total = sum((c["Adopted 2026"] for c in exp["cells"].values()), Decimal(0))
    if total != FY2026_ADOPTED:
        p.append(f"FY2026 adopted from the snapshot = {total}, OMB says {FY2026_ADOPTED}")
    csv_total = sum((money(r.get("Adopted 2026", "")) for r in rows), Decimal(0))
    if csv_total != FY2026_ADOPTED:
        p.append(f"FY2026 adopted in the CSV = {csv_total}, OMB says {FY2026_ADOPTED}")
    boards = {k[0] for k in exp["cells"] if k[0] in {b.zfill(3) for b in COMMUNITY_BOARDS}}
    if len(boards) != 59:
        p.append(f"community boards in the snapshot: {len(boards)}, want 59")
    res["boards"] = len(boards)
    res["years"] = exp["years"]
    res["june"] = exp["june"]
    return res


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", default=SNAPSHOT)
    ap.add_argument("--csv", default=CSV_PATH)
    ap.add_argument("--live", action="store_true", help="pull a fresh snapshot to a temp dir first")
    a = ap.parse_args(argv)
    snap = a.snapshot
    if a.live:
        sys.path.insert(0, HERE)
        from fetch_agency_budget_qa import fetch
        snap = tempfile.mkdtemp(prefix="agency-budget-qa-")
        fetch(snap)
    res = check(snap, a.csv)
    print(f"years FY{res['years'][0]}-FY{res['years'][-1]}; June releases {res['june']}")
    print(f"{res['rows']} CSV rows, {res['units']} units in Open Data, {res['boards']} community boards; "
          f"{res['compared']} cells compared; {len(res['problems'])} problems")
    for line in res["problems"][:50]:
        print("  " + line)
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
