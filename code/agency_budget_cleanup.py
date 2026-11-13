#!/usr/bin/env python3
"""
agency_budget_cleanup.py — rebuild viz/agencies/data/nyc_budget.csv, the City agency budgets
download, from the MCP index (#270, #288).

Until #288 this script pulled NYC Open Data's Expense Budget (mwzb-yiwb) itself and applied the
year rule with its own code. That made three copies of the rule (this script, the MCP loader and
the accuracy check). Now it does no year math and reads no Open Data: the one loader,
mcp/scripts/agency-budget.mjs, builds the agency_budget table from the committed snapshot, and
viz/explorer/scripts/agency-csv.mjs lays that table out as this file, with the same address,
columns and 0s as before. code/qa_agency_budget.py stays the independent check, with its own code.

Refresh, after the City publishes a new June release:

  python3 code/fetch_agency_budget_qa.py     # new snapshot in source/agency-budget-qa/
  python3 code/agency_budget_cleanup.py      # index -> nyc_budget.csv (this script)
  python3 code/qa_agency_budget.py           # independent check, every cell

  python3 code/agency_budget_cleanup.py --check   # exit 1 if the committed CSV differs

Needs Node 22+ and `npm ci` in mcp/ and viz/explorer/ (the index build and the writer).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO / "viz" / "agencies" / "data"
WRITER = REPO / "viz" / "explorer" / "scripts" / "agency-csv.mjs"
INDEX_BUILD = REPO / "mcp" / "scripts" / "build-index.mjs"

# The download's shape (kept since #265/#266): these columns, then "Adopted Y", "Modified Y".
STATIC_COLUMNS = ["Fund", "Department", "Department ID"]
# Look at Cook columns the file no longer has (#266). Kept so a test can make sure none comes back.
REMOVED_COLUMNS = ["Control Officer", "Short Title", "Link to Website", "Department Description"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 if the committed CSV differs from the index")
    ap.add_argument("--skip-index", action="store_true", help="use mcp/data/budget.db as it is")
    args = ap.parse_args(argv)
    if not args.skip_index:
        subprocess.run(["node", str(INDEX_BUILD), "--spreadsheet-only"], cwd=REPO / "mcp", check=True)
    cmd = ["node", str(WRITER)] + (["--check"] if args.check else [])
    return subprocess.run(cmd, cwd=REPO / "viz" / "explorer").returncode


if __name__ == "__main__":
    sys.exit(main())
