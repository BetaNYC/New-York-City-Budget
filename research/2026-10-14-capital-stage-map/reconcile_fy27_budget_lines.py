"""Reconcile the Council's FY27 Capital-Database.xlsx against OMB's adopted Capital Budget.

Inputs:
  1. The Council RnD workbook (sheet "FY27 CAPITAL"), e.g.
     ../NYCB-disclosure/source/expense-funding-disclosure/Capital-Database.xlsx (2026-10-12 pull).
  2. omb-46m8-77gv-pub20260713-council-lines.tsv in this folder: NYC Open Data dataset
     46m8-77gv ("Capital Budget", OMB), pub_date 20260713, every budget line matching
     "% D%", summed by line (columns: budline, year1_amt FY2027, year2_amt FY2028).
     Pulled 2026-10-14 with one SoQL query through the socrata MCP:
       select budline, funding, sum(year1_amt), sum(year2_amt), count(*)
       where pub_date = 20260713 and budline like '% D%' group by budline, funding
     All 161 rows were funding = C (city non-exempt).

Usage: python -I reconcile_fy27_budget_lines.py <Capital-Database.xlsx> <omb.tsv>
"""
import collections
import re
import sys

import openpyxl


def norm(s):
    return re.sub(r"\s+", " ", str(s).strip())


def main(xlsx, tsv):
    ws = openpyxl.load_workbook(xlsx, read_only=True, data_only=True).worksheets[0]
    rows = [r for r in list(ws.iter_rows(values_only=True))[1:] if any(v not in (None, "") for v in r)]
    council = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        k = norm(r[2])
        council[k][0] += r[7] or 0
        council[k][1] += r[8] or 0
        council[k][2] += 1
    omb = {}
    for line in open(tsv):
        b, y1, y2 = line.rstrip("\n").split("\t")
        omb[norm(b)] = [int(y1), int(y2)]
    exact = [k for k in council if k in omb and council[k][:2] == omb[k]]
    diff = [(k, council[k][:2], omb[k]) for k in council if k in omb and council[k][:2] != omb[k]]
    only_c = [k for k in council if k not in omb]
    only_o = [(k, omb[k]) for k in omb if k not in council]
    print(f"Council rows: {len(rows)}; Council budget lines: {len(council)}; OMB D lines: {len(omb)}")
    print(f"Exact match (FY27 and FY28): {len(exact)}")
    print("Different amounts (line, council [FY27, FY28], OMB [FY27, FY28]):")
    for d in sorted(diff):
        print("  ", d)
    print("Council lines missing from OMB:", only_c)
    print("OMB D lines with no Council row:")
    for o in sorted(only_o):
        print("  ", o)
    print("Totals FY27/FY28: council", sum(v[0] for v in council.values()), sum(v[1] for v in council.values()),
          "omb", sum(v[0] for v in omb.values()), sum(v[1] for v in omb.values()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
