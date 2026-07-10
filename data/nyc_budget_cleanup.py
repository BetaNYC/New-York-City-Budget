#!/usr/bin/env python3
"""
nyc_budget_cleanup.py — NYC Expense Budget -> DataMade "Look at Cook" nyc_budget.csv

Pipeline for BetaNYC's NYC budget visualization (fork of DataMade's look-at-cook front-end).
Pulls NYC's live Expense Budget from NYC Open Data, filters out the triple-count publication
gotcha, aggregates to agency x unit-of-appropriation x fiscal year, and emits a CSV matching
the look-at-cook cleaned-CSV contract exactly so the front-end renders with zero JS changes.
The output filename (nyc_budget.csv) matches js/app.js `dataSource = '/data/nyc_budget.csv'`.

DATA SOURCE (build-against-docs, never guess — Engineering Standard sec 0)
  NYC Open Data "Expense Budget", dataset id mwzb-yiwb, via the Socrata SODA 2.1 API.
  - Resource endpoint : https://data.cityofnewyork.us/resource/mwzb-yiwb.json
  - Metadata endpoint : https://data.cityofnewyork.us/api/views/mwzb-yiwb.json
  - Public, read-only, NO app token required.
  - SODA query docs   : https://dev.socrata.com/docs/queries/
  Field names below were CONFIRMED from the metadata endpoint on 2026-07-09 (not guessed):
    publication_date (text, YYYYMMDD), fiscal_year (number),
    agency_number (text), agency_name (text),
    unit_appropriation_number (text), unit_appropriation_name (text),
    adopted_budget_amount (number), current_modified_budget_amount (number).

THE TRIPLE-COUNT GOTCHA
  Each fiscal year is published up to three times — Preliminary (Jan), Executive (Apr/May),
  Adopted (June) — and each snapshot restates the ENTIRE budget. Summing across snapshots
  triple-counts. We keep exactly ONE publication_date per fiscal year: the ADOPTED (June)
  snapshot, which is the latest (max) publication_date for that fiscal year. Because
  publication_date is zero-padded YYYYMMDD text, lexical max == chronological max.

OUTPUT SCHEMA (look-at-cook cleaned-CSV contract; header names are case-sensitive)
  Static : Fund, Department, Control Officer, Department ID, Short Title,
           Link to Website, Department Description
  Per FY : "Adopted {year}" and "Modified {year}" for year 2017..2027
           (plain years, e.g. "Adopted 2017", NOT "FY2017").
  Value mapping (v1):
    Fund                  = agency_name
    Department            = unit_appropriation_name
    Control Officer       = agency_name   (v1 PLACEHOLDER — duplicates Fund so the
                            front-end's second top-level view renders. A real second axis,
                            e.g. object class, replaces this later.)
    Department ID         = unit_appropriation_number
    Short Title / Link to Website / Department Description = "" (empty for v1)
    Adopted {year}        = sum(adopted_budget_amount)          over the (agency, unit) group
    Modified {year}       = sum(current_modified_budget_amount) over the same group
  Both series come from the same Adopted snapshot. At that snapshot Modified diverges from
  Adopted (e.g. FY2026: $114.4B adopted vs $123.8B modified), so the two chart lines show a
  real spread. Numbers are written plain (no $, no commas) — the front-end parses floats.

COLUMN/LABEL COUPLING (critical — do not drift)
  js/app.js builds each per-year data key as `<apropTitle> + ' ' + year` and
  `<expendTitle> + ' ' + year` (getTotals / getChartTotals). The config sets
  apropTitle='Adopted' and expendTitle='Modified', so the CSV column PREFIXES here MUST be
  exactly 'Adopted' and 'Modified' (see APROP_LABEL / EXPEND_LABEL below). Rename one side and
  you must rename the other, or the chart reads NaN.

VALIDATION GATE
  After filtering, NYC's FY2026 Adopted total must be ~$114.4B. If it falls outside
  [110B, 118B] the run aborts non-zero rather than emitting a suspect CSV.

RUNTIME
  Stdlib only (urllib, csv, json) — no third-party deps, portable across the team's Python
  spread. Tested range: Python >=3.11,<3.15. Idempotent: re-running overwrites the output
  CSVs deterministically. Read-only against the API; writes only local CSV files.

USAGE
  python3 nyc_budget_cleanup.py                 # full CSV + sample CSV
  python3 nyc_budget_cleanup.py --sample-only   # sample CSV only (fast)
  python3 nyc_budget_cleanup.py --out DIR       # write into DIR (default: script dir)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# --- constants ---------------------------------------------------------------

DATASET_ID = "mwzb-yiwb"
RESOURCE_URL = f"https://data.cityofnewyork.us/resource/{DATASET_ID}.json"
FISCAL_YEARS = list(range(2017, 2028))  # FY2017 .. FY2027 inclusive

# look-at-cook cleaned-CSV contract (case-sensitive header names).
STATIC_COLUMNS = [
    "Fund",
    "Department",
    "Control Officer",
    "Department ID",
    "Short Title",
    "Link to Website",
    "Department Description",
]

# Per-year column PREFIXES. These MUST equal js/app.js apropTitle / expendTitle — the
# front-end reads each year's value via `<label> + ' ' + year` (see module docstring,
# COLUMN/LABEL COUPLING). APROP_LABEL carries adopted_budget_amount; EXPEND_LABEL carries
# current_modified_budget_amount.
APROP_LABEL = "Adopted"
EXPEND_LABEL = "Modified"


def year_columns() -> list[str]:
    cols: list[str] = []
    for y in FISCAL_YEARS:
        cols.append(f"{APROP_LABEL} {y}")
        cols.append(f"{EXPEND_LABEL} {y}")
    return cols


# Recognizable agencies for the hand-checkable sample CSV (agency_number).
SAMPLE_AGENCY_NUMBERS = {
    "040",  # Department of Education
    "056",  # Police Department
    "057",  # Fire Department
    "816",  # Department of Health and Mental Hygiene
    "806",  # Housing Preservation and Development
    "827",  # Department of Sanitation
    "846",  # Department of Parks and Recreation
}

# Validation gate: FY2026 Adopted (Appropriations) total must land near $114.4B.
GATE_FY = 2026
GATE_MIN = 110_000_000_000
GATE_MAX = 118_000_000_000

PAGE_SIZE = 50_000
HTTP_TIMEOUT = 120


# --- logging -----------------------------------------------------------------

def log(event: str, **fields: object) -> None:
    """Structured, timestamped, secret-free log line."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    extra = " ".join(f"{k}={v}" for k, v in fields.items())
    print(f"[nyc_budget_cleanup] {ts} {event} {extra}".rstrip(), file=sys.stderr)


# --- SODA client -------------------------------------------------------------

def soda_get(params: dict[str, str]) -> list[dict]:
    """One SODA GET. Fails loud on any transport/HTTP error (runtime-reliability)."""
    url = f"{RESOURCE_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500]
        raise SystemExit(
            f"FATAL: SODA HTTP {e.code} for {DATASET_ID}. Response: {body}"
        ) from e
    except urllib.error.URLError as e:
        raise SystemExit(
            f"FATAL: cannot reach NYC Open Data ({e.reason}). Check connectivity."
        ) from e


def soda_get_all(select: str, where: str, group: str) -> list[dict]:
    """Paginated grouped SODA pull. Loops on $offset until a short page is returned."""
    rows: list[dict] = []
    offset = 0
    while True:
        page = soda_get(
            {
                "$select": select,
                "$where": where,
                "$group": group,
                "$order": group,  # stable order => deterministic pagination
                "$limit": str(PAGE_SIZE),
                "$offset": str(offset),
            }
        )
        rows.extend(page)
        log("page.fetched", offset=offset, rows=len(page))
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


# --- pipeline steps ----------------------------------------------------------

def discover_adopted_snapshots() -> dict[int, str]:
    """
    Return {fiscal_year: adopted_publication_date} for each target FY.

    The Adopted snapshot is the latest (max) publication_date for a fiscal year. Computed
    dynamically from the data so the pipeline survives future publications rather than
    hard-coding dates.
    """
    rows = soda_get(
        {
            "$select": "fiscal_year,publication_date",
            "$group": "fiscal_year,publication_date",
            "$order": "fiscal_year,publication_date",
            "$limit": "5000",
        }
    )
    latest: dict[int, str] = {}
    for r in rows:
        fy = int(r["fiscal_year"])
        if fy not in FISCAL_YEARS:
            continue
        pd = r["publication_date"]  # YYYYMMDD text; lexical max == chronological max
        if fy not in latest or pd > latest[fy]:
            latest[fy] = pd
    missing = [fy for fy in FISCAL_YEARS if fy not in latest]
    if missing:
        raise SystemExit(f"FATAL: no Adopted snapshot found for FY(s): {missing}")
    for fy in FISCAL_YEARS:
        log("adopted.snapshot", fy=fy, publication_date=latest[fy])
    return latest


def build_where(adopted: dict[int, str]) -> str:
    """OR of (fiscal_year=X AND publication_date='Y') across the target FYs."""
    clauses = [
        f"(fiscal_year={fy} AND publication_date='{adopted[fy]}')" for fy in FISCAL_YEARS
    ]
    return " OR ".join(clauses)


def pull_aggregated(where: str) -> list[dict]:
    """
    Server-side aggregate: sum adopted_budget_amount (Appropriations) and
    current_modified_budget_amount (Expenditures) by agency x unit x fiscal year.
    """
    select = (
        "agency_number,agency_name,"
        "unit_appropriation_number,unit_appropriation_name,fiscal_year,"
        "sum(adopted_budget_amount) as appropriations,"
        "sum(current_modified_budget_amount) as expenditures"
    )
    group = (
        "agency_number,agency_name,"
        "unit_appropriation_number,unit_appropriation_name,fiscal_year"
    )
    return soda_get_all(select, where, group)


def pivot(rows: list[dict]) -> list[dict]:
    """
    Collapse to one record per (agency_number, unit_appropriation_number) with an
    Appropriations and an Expenditures column per fiscal year. Names are taken from the
    most recent fiscal year present, so agency/unit renames resolve to their latest label.
    """
    appro: dict[tuple[str, str], dict[int, float]] = defaultdict(
        lambda: {fy: 0.0 for fy in FISCAL_YEARS}
    )
    expen: dict[tuple[str, str], dict[int, float]] = defaultdict(
        lambda: {fy: 0.0 for fy in FISCAL_YEARS}
    )
    # (agency_no, unit_no) -> (latest_fy_seen, agency_name, unit_name)
    labels: dict[tuple[str, str], tuple[int, str, str]] = {}

    for r in rows:
        agency_no = (r.get("agency_number") or "").strip()
        unit_no = (r.get("unit_appropriation_number") or "").strip()
        fy = int(r["fiscal_year"])
        key = (agency_no, unit_no)
        appro[key][fy] += float(r.get("appropriations") or 0.0)
        expen[key][fy] += float(r.get("expenditures") or 0.0)

        agency_name = (r.get("agency_name") or "").strip()
        unit_name = (r.get("unit_appropriation_name") or "").strip()
        if key not in labels or fy > labels[key][0]:
            labels[key] = (fy, agency_name, unit_name)

    records: list[dict] = []
    for key in sorted(appro, key=lambda k: (k[0], k[1])):
        agency_no, unit_no = key
        _, agency_name, unit_name = labels[key]
        rec = {
            "Fund": agency_name,
            "Department": unit_name,
            "Control Officer": agency_name,  # v1 placeholder (see module docstring)
            "Department ID": unit_no,
            "Short Title": "",
            "Link to Website": "",
            "Department Description": "",
        }
        for fy in FISCAL_YEARS:
            rec[f"{APROP_LABEL} {fy}"] = _fmt_amount(appro[key][fy])
            rec[f"{EXPEND_LABEL} {fy}"] = _fmt_amount(expen[key][fy])
        records.append(rec)
    return records


def _fmt_amount(v: float) -> str:
    """Whole-dollar values render as ints; keep cents only if actually present."""
    return str(int(round(v))) if abs(v - round(v)) < 0.005 else f"{v:.2f}"


def validate_gate(records: list[dict]) -> float:
    """Recompute FY2026 Adopted total from emitted records; abort if out of range."""
    col = f"{APROP_LABEL} {GATE_FY}"
    total = sum(float(rec[col]) for rec in records)
    log("gate.fy2026_appropriations", value=f"{total:.0f}", billions=f"{total / 1e9:.3f}")
    if not (GATE_MIN <= total <= GATE_MAX):
        raise SystemExit(
            f"FATAL: FY{GATE_FY} Appropriations total ${total / 1e9:.2f}B outside expected "
            f"[{GATE_MIN / 1e9:.0f}B, {GATE_MAX / 1e9:.0f}B]. Filtering is wrong — "
            f"not writing CSV."
        )
    return total


def write_csv(records: list[dict], path: Path) -> None:
    columns = STATIC_COLUMNS + year_columns()
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(records)
    log("csv.written", path=str(path), rows=len(records))


# --- main --------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parent),
        help="Output directory (default: this script's directory).",
    )
    ap.add_argument(
        "--sample-only",
        action="store_true",
        help="Write only the sample CSV (recognizable agencies), skip the full CSV.",
    )
    args = ap.parse_args()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    log("run.start", dataset=DATASET_ID, fiscal_years=f"{FISCAL_YEARS[0]}-{FISCAL_YEARS[-1]}")

    adopted = discover_adopted_snapshots()
    where = build_where(adopted)
    raw = pull_aggregated(where)
    log("aggregate.pulled", rows=len(raw))

    records = pivot(raw)
    log("pivot.done", departments=len(records),
        agencies=len({rec["Fund"] for rec in records}))

    validate_gate(records)  # aborts if FY2026 total is wrong

    if not args.sample_only:
        write_csv(records, out_dir / "nyc_budget.csv")

    sample_names = {a for a in SAMPLE_AGENCY_NUMBERS}
    # Sample selection is by agency_number, but records no longer carry it; rebuild the
    # agency_number -> keep decision from the raw rows.
    keep_funds = {
        (r.get("agency_name") or "").strip()
        for r in raw
        if (r.get("agency_number") or "").strip() in sample_names
    }
    sample = [rec for rec in records if rec["Fund"] in keep_funds]
    write_csv(sample, out_dir / "nyc_budget_sample.csv")

    log("run.done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
