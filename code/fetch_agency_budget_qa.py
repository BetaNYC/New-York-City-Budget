#!/usr/bin/env python3
"""
fetch_agency_budget_qa.py — pull the snapshot the agency budget accuracy test checks against (#268).

The City agency budgets half (viz/agencies/, built by code/agency_budget_cleanup.py) shows, for
every agency and unit of appropriation, an Adopted and a Modified figure per fiscal year, from
NYC Open Data "Expense Budget" (mwzb-yiwb). code/qa_agency_budget.py recomputes every one of
those figures from this snapshot, with its own code, and compares.

Two files, written to source/agency-budget-qa/ (or --out):

  releases.csv   every (fiscal_year, publication_date) release the dataset has, with its row
                 count: so the test can see which release is each year's June release
  by_unit.csv    for each June release candidate (the latest release of each fiscal_year tag),
                 the server-side sums of the three amounts by agency x unit of appropriation,
                 exactly as served (numbers as text, codes as served: unpadded before 2023)

Plus MANIFEST.csv: each request's URL, time, HTTP status, bytes and sha256.

Field names are from the dataset's metadata (/api/views/mwzb-yiwb.json): publication_date,
fiscal_year, agency_number, agency_name, unit_appropriation_number, unit_appropriation_name,
adopted_budget_amount, current_modified_budget_amount, financial_plan_amount.

Read-only. Public, no app token. One request at a time, 2 s apart, with the repo's User-Agent.
Stdlib only.

  python3 code/fetch_agency_budget_qa.py [--out DIR]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from polite_http import USER_AGENT  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_OUT = os.path.join(ROOT, "source", "agency-budget-qa")
RESOURCE = "https://data.cityofnewyork.us/resource/mwzb-yiwb.json"
FIRST_TAG = 2017      # the explorer shows FY2017 onward
PAGE = 50_000
GAP = 2.0

UNIT_FIELDS = ["fiscal_year", "publication_date", "agency_number", "agency_name",
               "unit_appropriation_number", "unit_appropriation_name",
               "adopted_budget_amount", "current_modified_budget_amount", "financial_plan_amount",
               "rows"]


class Client:
    def __init__(self):
        self.last = 0.0
        self.log: list[dict] = []

    def get(self, params: dict) -> list[dict]:
        wait = GAP - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        url = f"{RESOURCE}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read()
            status = resp.status
        self.last = time.monotonic()
        self.log.append({"url": url, "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "http_status": status, "bytes": len(body),
                         "sha256": hashlib.sha256(body).hexdigest()})
        return json.loads(body)

    def get_all(self, params: dict) -> list[dict]:
        out, offset = [], 0
        while True:
            page = self.get({**params, "$limit": str(PAGE), "$offset": str(offset)})
            out.extend(page)
            if len(page) < PAGE:
                return out
            offset += PAGE


def fetch(out_dir: str) -> None:
    c = Client()
    releases = c.get_all({
        "$select": "fiscal_year,publication_date,count(*) as rows",
        "$group": "fiscal_year,publication_date",
        "$order": "fiscal_year,publication_date",
    })
    latest: dict[int, str] = {}
    for r in releases:
        tag = int(r["fiscal_year"])
        if tag >= FIRST_TAG and r["publication_date"] > latest.get(tag, ""):
            latest[tag] = r["publication_date"]
    where = " OR ".join(f"(fiscal_year={t} AND publication_date='{d}')" for t, d in sorted(latest.items()))
    group = ("fiscal_year,publication_date,agency_number,agency_name,"
             "unit_appropriation_number,unit_appropriation_name")
    units = c.get_all({
        "$select": group + ",sum(adopted_budget_amount) as adopted_budget_amount,"
                   "sum(current_modified_budget_amount) as current_modified_budget_amount,"
                   "sum(financial_plan_amount) as financial_plan_amount,count(*) as rows",
        "$where": where,
        "$group": group,
        "$order": group,
    })
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "releases.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fiscal_year", "publication_date", "rows"], lineterminator="\n")
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in ("fiscal_year", "publication_date", "rows")} for r in releases)
    with open(os.path.join(out_dir, "by_unit.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=UNIT_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in UNIT_FIELDS} for r in units)
    with open(os.path.join(out_dir, "MANIFEST.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["url", "retrieved_at", "http_status", "bytes", "sha256"], lineterminator="\n")
        w.writeheader()
        w.writerows(c.log)
    print(f"releases: {len(releases)}, by_unit rows: {len(units)}, tags: {sorted(latest)}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=DEFAULT_OUT)
    fetch(os.path.abspath(ap.parse_args().out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
