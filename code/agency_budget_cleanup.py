#!/usr/bin/env python3
"""
agency_budget_cleanup.py — NYC Expense Budget -> DataMade "Look at Cook" nyc_budget.csv

Moved here from BetaNYC/nyc-budget-viz data/nyc_budget_cleanup.py (#265). It writes
viz/agencies/data/nyc_budget.csv, which the agency explorer at viz/agencies/ loads.

Pipeline for BetaNYC's NYC budget visualization (fork of DataMade's look-at-cook front-end).
Pulls NYC's Expense Budget from NYC Open Data, keeps one release per budget cycle, maps each
money column to the fiscal year it actually describes, aggregates to agency x unit of
appropriation x fiscal year, and emits a CSV matching the look-at-cook cleaned-CSV contract so
the front-end renders it. The output filename (nyc_budget.csv) matches viz/agencies/js/app.js
`dataSource = '/data/nyc_budget.csv'`.

DATA SOURCE (build-against-docs, never guess — Engineering Standard sec 0)
  NYC Open Data "Expense Budget", dataset id mwzb-yiwb, via the Socrata SODA 2.1 API.
  - Resource endpoint : https://data.cityofnewyork.us/resource/mwzb-yiwb.json
  - Metadata endpoint : https://data.cityofnewyork.us/api/views/mwzb-yiwb.json
  - Data dictionary   : Expense_Budget_Data_Dictionary.xlsx, attached to the metadata
  - Public, read-only, NO app token required.
  - SODA query docs   : https://dev.socrata.com/docs/queries/
  Field names CONFIRMED from the metadata endpoint (2026-07-09, re-checked 2026-11-09):
    publication_date (text, YYYYMMDD), fiscal_year (number),
    agency_number (text), agency_name (text),
    unit_appropriation_number (text), unit_appropriation_name (text),
    adopted_budget_amount (number), current_modified_budget_amount (number),
    financial_plan_amount (number).

WHICH YEAR EACH MONEY COLUMN DESCRIBES (the 2026-11-09 fix)
  A release's `fiscal_year` is the budget being PROPOSED or ADOPTED in that release, not the
  year of every column in it. The data dictionary defines the three amounts but does not say
  which year each one covers. OMB's printed Adopted Budget settles it: the FY2026 Adopted
  Budget, Expense/Revenue/Contract volume (adopt25/erc6-25.pdf), is the same publication as the
  Open Data release dated 20250630 with fiscal_year = 2026, and its columns are headed
  "ADOPTED BUDGET FOR FY 2025", "CURRENT MODIFIED BUDGET FOR FY 2025" and "ADOPTED BUDGET FOR
  FY 2026". So in a release tagged fiscal_year = Y:
    adopted_budget_amount          = FY(Y-1) adopted
    current_modified_budget_amount = FY(Y-1) modified, as of that release's date
    financial_plan_amount          = FY Y plan (in the June release: FY Y adopted)
  Before this fix the pipeline labeled the first two as FY Y, so every year shown was one
  year late. This pipeline now uses:
    Adopted Y  = financial_plan_amount from the June release tagged Y
                 (cross-checked: equals adopted_budget_amount in the release tagged Y+1)
    Modified Y = current_modified_budget_amount from the June release tagged Y+1
                 (FY Y's budget as modified through June of FY Y, near year end)
  The newest year has no Modified figure until the City adopts the NEXT year's budget. That
  cell is written EMPTY, not 0, and the site says "not yet published".

ONE RELEASE PER BUDGET CYCLE (avoids triple counting)
  Each fiscal_year tag is published up to three times — Preliminary (Jan), Executive (Apr/May),
  Adopted (June) — and each release restates the entire budget. Summing across releases counts
  the same money up to three times. We keep the June release only: the latest
  publication_date for the tag, and it must fall in June or later of the prior calendar year
  (an adoption-cycle release). A tag whose latest release is earlier than that is still in
  progress and is not used.

ZERO-PADDING
  Releases before 2023 write agency and unit numbers without leading zeros ("40", "1"); later
  releases pad them ("040", "001"). Both are normalized to three digits so one unit is one row.

OUTPUT SCHEMA (look-at-cook cleaned-CSV contract; header names are case-sensitive)
  Static : Fund, Department, Control Officer, Department ID, Short Title,
           Link to Website, Department Description
  Per FY : "Adopted {year}" and "Modified {year}" for year 2017..2027
  Value mapping:
    Fund            = agency_name
    Department      = unit_appropriation_name
    Control Officer = agency_name   (v1 PLACEHOLDER — duplicates Fund)
    Department ID   = unit_appropriation_number (zero-padded to 3)
    Short Title / Link to Website / Department Description = "" (empty for v1)
  Numbers are written plain (no $, no commas) — the front-end parses floats.

COLUMN/LABEL COUPLING (critical — do not drift)
  viz/agencies/js/app.js reads each year's value via `<apropTitle> + ' ' + year` and
  `<expendTitle> + ' ' + year`, with apropTitle='Adopted' and expendTitle='Modified'.
  APROP_LABEL / EXPEND_LABEL below MUST equal those.

VALIDATION GATE (OMB's published numbers)
  The run aborts, writing nothing, unless the emitted CSV reproduces OMB's printed FY2026
  Adopted Budget (adopt25/erc6-25.pdf), exactly:
    - citywide FY2026 adopted, gross of intra-city  = $117,791,473,676
      (page 1E: net total $115,907,309,727 + intra-city $1,884,163,949)
    - citywide FY2025 adopted, gross                 = $114,384,991,832
      (page 1E: net $112,431,582,240 + intra-city $1,953,409,592)
    - citywide FY2025 modified as of June 2025, gross = $123,844,584,236
      (page 1E: net $121,598,357,432 + intra-city $2,246,226,804)
    - Manhattan Community Board 1 (agency 341), page 182E: FY2025 adopted PS $267,484;
      FY2025 modified PS $249,484 and OTPS $190,939; FY2026 adopted PS $275,060, OTPS $27,245.
  It also aborts if, for any year with both releases, the citywide financial_plan_amount of
  the June release tagged Y differs from adopted_budget_amount of the release tagged Y+1.

RUNTIME
  Stdlib only (urllib, csv, json). Tested range: Python >=3.11,<3.15. Idempotent. Read-only
  against the API; writes only local CSV files.

USAGE
  python3 code/agency_budget_cleanup.py                 # full CSV + sample CSV
  python3 code/agency_budget_cleanup.py --sample-only   # sample CSV only
  python3 code/agency_budget_cleanup.py --out DIR       # write into DIR
                                                        # (default: viz/agencies/data/)
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
FISCAL_YEARS = list(range(2017, 2028))  # FY2017 .. FY2027 inclusive (years SHOWN)

STATIC_COLUMNS = [
    "Fund",
    "Department",
    "Control Officer",
    "Department ID",
    "Short Title",
    "Link to Website",
    "Department Description",
]

# Must equal viz/agencies/js/app.js apropTitle / expendTitle (see COLUMN/LABEL COUPLING).
APROP_LABEL = "Adopted"
EXPEND_LABEL = "Modified"

# Internal-only record key (not written to the CSV): the normalized agency number.
AGENCY_KEY = "_agency_number"


def year_columns() -> list[str]:
    cols: list[str] = []
    for y in FISCAL_YEARS:
        cols.append(f"{APROP_LABEL} {y}")
        cols.append(f"{EXPEND_LABEL} {y}")
    return cols


# Recognizable agencies for the hand-checkable sample CSV (agency_number, 3-digit).
SAMPLE_AGENCY_NUMBERS = {
    "040",  # Department of Education
    "056",  # Police Department
    "057",  # Fire Department
    "816",  # Department of Health and Mental Hygiene
    "806",  # Housing Preservation and Development
    "827",  # Department of Sanitation
    "846",  # Department of Parks and Recreation
    "341",  # Manhattan Community Board 1 (OMB gate agency)
}

# Validation gate — OMB FY2026 Adopted Budget, Expense/Revenue/Contract volume,
# https://www.nyc.gov/assets/omb/downloads/pdf/adopt25/erc6-25.pdf
# Citywide totals are GROSS (OMB's "Net Total Budget" plus "Intra-City Expenditures"),
# because the Open Data rows include intra-city amounts.
GATE_CITYWIDE = {
    (APROP_LABEL, 2026): 115_907_309_727 + 1_884_163_949,   # = 117,791,473,676
    (APROP_LABEL, 2025): 112_431_582_240 + 1_953_409_592,   # = 114,384,991,832
    (EXPEND_LABEL, 2025): 121_598_357_432 + 2_246_226_804,  # = 123,844,584,236
}
# (agency_number, unit_number, label, year) -> dollars, page 182E (Manhattan CB 1).
GATE_UNITS = {
    ("341", "001", APROP_LABEL, 2025): 267_484,
    ("341", "001", EXPEND_LABEL, 2025): 249_484,
    ("341", "002", EXPEND_LABEL, 2025): 190_939,
    ("341", "001", APROP_LABEL, 2026): 275_060,
    ("341", "002", APROP_LABEL, 2026): 27_245,
}

# Where the agency explorer loads its CSV from (viz/agencies/js/app.js `dataSource`).
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "viz" / "agencies" / "data"

PAGE_SIZE = 50_000
HTTP_TIMEOUT = 120


# --- logging -----------------------------------------------------------------

def log(event: str, **fields: object) -> None:
    """Structured, timestamped, secret-free log line."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    extra = " ".join(f"{k}={v}" for k, v in fields.items())
    print(f"[agency_budget_cleanup] {ts} {event} {extra}".rstrip(), file=sys.stderr)


# --- SODA client -------------------------------------------------------------

def soda_get(params: dict[str, str]) -> list[dict]:
    """One SODA GET. Fails loud on any transport/HTTP error."""
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

def norm_code(value: str | None) -> str:
    """Zero-pad an agency or unit number to 3 digits ('1' -> '001', '040' stays)."""
    v = (value or "").strip()
    return v.zfill(3) if v.isdigit() else v


def is_adoption_release(tag: int, publication_date: str) -> bool:
    """A release tagged FY `tag` is the June adoption release if published in or after
    June of calendar year tag-1 (NYC adopts FY `tag` in June of tag-1)."""
    return publication_date >= f"{tag - 1}0601"


def discover_june_releases() -> dict[int, str]:
    """
    Return {release_tag: publication_date} of the June (adoption) release for every tag
    needed: FISCAL_YEARS (for Adopted) and FISCAL_YEARS[-1] + 1 (for the newest Modified).

    Tags in FISCAL_YEARS must have a June release or the run aborts. The tag after the last
    shown year is optional: until it is adopted, the newest Modified stays empty.
    """
    rows = soda_get(
        {
            "$select": "fiscal_year,publication_date",
            "$group": "fiscal_year,publication_date",
            "$order": "fiscal_year,publication_date",
            "$limit": "5000",
        }
    )
    wanted = set(FISCAL_YEARS) | {FISCAL_YEARS[-1] + 1}
    latest: dict[int, str] = {}
    for r in rows:
        tag = int(r["fiscal_year"])
        if tag not in wanted:
            continue
        pd = r["publication_date"]  # YYYYMMDD text; lexical max == chronological max
        if tag not in latest or pd > latest[tag]:
            latest[tag] = pd
    june = {t: pd for t, pd in latest.items() if is_adoption_release(t, pd)}
    missing = [fy for fy in FISCAL_YEARS if fy not in june]
    if missing:
        raise SystemExit(
            f"FATAL: no June (adoption) release found for FY(s) {missing}. "
            f"Latest releases seen: { {t: latest.get(t) for t in missing} }"
        )
    for tag in sorted(june):
        log("june.release", tag=tag, publication_date=june[tag])
    nxt = FISCAL_YEARS[-1] + 1
    if nxt not in june:
        log("modified.pending", fy=FISCAL_YEARS[-1],
            reason=f"no June release tagged {nxt} yet; Modified {FISCAL_YEARS[-1]} left empty")
    return june


def build_where(releases: dict[int, str]) -> str:
    """OR of (fiscal_year=T AND publication_date='D') across the chosen releases."""
    return " OR ".join(
        f"(fiscal_year={t} AND publication_date='{releases[t]}')" for t in sorted(releases)
    )


def pull_aggregated(where: str) -> list[dict]:
    """Server-side aggregate of the three amounts by agency x unit x release tag."""
    select = (
        "agency_number,agency_name,"
        "unit_appropriation_number,unit_appropriation_name,fiscal_year,"
        "sum(adopted_budget_amount) as adopted,"
        "sum(current_modified_budget_amount) as modified,"
        "sum(financial_plan_amount) as finplan"
    )
    group = (
        "agency_number,agency_name,"
        "unit_appropriation_number,unit_appropriation_name,fiscal_year"
    )
    return soda_get_all(select, where, group)


def check_release_agreement(rows: list[dict], releases: dict[int, str]) -> dict[int, float]:
    """
    Cross-check the two documented routes to "Adopted Y": financial_plan_amount in the June
    release tagged Y must equal adopted_budget_amount in the release tagged Y+1. Citywide
    totals must match to the dollar or the run aborts. Returns {Y: difference}.
    """
    fin: dict[int, float] = defaultdict(float)
    adp: dict[int, float] = defaultdict(float)
    for r in rows:
        tag = int(r["fiscal_year"])
        fin[tag] += float(r.get("finplan") or 0.0)
        adp[tag] += float(r.get("adopted") or 0.0)
    diffs: dict[int, float] = {}
    for y in FISCAL_YEARS:
        if y in releases and (y + 1) in releases:
            diffs[y] = fin[y] - adp[y + 1]
            log("crosscheck.adopted", fy=y, finplan_tag_y=f"{fin[y]:.0f}",
                adopted_tag_y_plus_1=f"{adp[y + 1]:.0f}", diff=f"{diffs[y]:.0f}")
    bad = {y: d for y, d in diffs.items() if abs(d) >= 1}
    if bad:
        raise SystemExit(
            f"FATAL: financial_plan_amount (release Y) != adopted_budget_amount (release Y+1) "
            f"citywide for FY {sorted(bad)}: {bad}. The year mapping no longer holds."
        )
    return diffs


def pivot(rows: list[dict], releases: dict[int, str]) -> list[dict]:
    """
    One record per (agency_number, unit_number), with "Adopted Y" and "Modified Y" columns.

      Adopted Y  <- finplan  from release tagged Y
      Modified Y <- modified from release tagged Y+1  ("" if that release does not exist)

    Display names come from the newest release in which the unit appears.
    """
    appro: dict[tuple[str, str], dict[int, float]] = defaultdict(
        lambda: {fy: 0.0 for fy in FISCAL_YEARS}
    )
    modif: dict[tuple[str, str], dict[int, float]] = defaultdict(
        lambda: {fy: 0.0 for fy in FISCAL_YEARS}
    )
    labels: dict[tuple[str, str], tuple[int, str, str]] = {}

    for r in rows:
        key = (norm_code(r.get("agency_number")), norm_code(r.get("unit_appropriation_number")))
        tag = int(r["fiscal_year"])
        if tag in FISCAL_YEARS:
            appro[key][tag] += float(r.get("finplan") or 0.0)
        if (tag - 1) in FISCAL_YEARS:
            modif[key][tag - 1] += float(r.get("modified") or 0.0)
        agency_name = (r.get("agency_name") or "").strip()
        unit_name = (r.get("unit_appropriation_name") or "").strip()
        if key not in labels or tag > labels[key][0]:
            labels[key] = (tag, agency_name, unit_name)

    keys = set(appro) | set(modif)
    records: list[dict] = []
    for key in sorted(keys):
        agency_no, unit_no = key
        _, agency_name, unit_name = labels[key]
        rec = {
            "Fund": agency_name,
            "Department": unit_name,
            "Control Officer": agency_name,  # v1 placeholder
            "Department ID": unit_no,
            "Short Title": "",
            "Link to Website": "",
            "Department Description": "",
            AGENCY_KEY: agency_no,
        }
        for fy in FISCAL_YEARS:
            rec[f"{APROP_LABEL} {fy}"] = _fmt_amount(appro[key][fy] if key in appro else 0.0)
            if (fy + 1) in releases:
                rec[f"{EXPEND_LABEL} {fy}"] = _fmt_amount(
                    modif[key][fy] if key in modif else 0.0
                )
            else:
                rec[f"{EXPEND_LABEL} {fy}"] = ""  # not published yet; never invent a value
        records.append(rec)
    return records


def _fmt_amount(v: float) -> str:
    """Whole-dollar values render as ints; keep cents only if actually present."""
    return str(int(round(v))) if abs(v - round(v)) < 0.005 else f"{v:.2f}"


def _num(cell: str) -> float:
    return float(cell) if cell != "" else 0.0


def validate_gate(records: list[dict]) -> dict[str, float]:
    """Recompute OMB's published figures from the emitted records; abort on any mismatch."""
    problems: list[str] = []
    seen: dict[str, float] = {}
    for (label, fy), expected in GATE_CITYWIDE.items():
        col = f"{label} {fy}"
        total = sum(_num(rec[col]) for rec in records)
        seen[col] = total
        log("gate.citywide", column=col, value=f"{total:.0f}", expected=expected)
        if round(total) != expected:
            problems.append(f"citywide {col} = {total:,.0f}, OMB says {expected:,}")
    for (agency, unit, label, fy), expected in GATE_UNITS.items():
        col = f"{label} {fy}"
        match = [r for r in records
                 if r.get(AGENCY_KEY) == agency and r["Department ID"] == unit]
        value = sum(_num(r[col]) for r in match)
        seen[f"{agency}/{unit} {col}"] = value
        log("gate.unit", agency=agency, unit=unit, column=col, value=f"{value:.0f}",
            expected=expected)
        if round(value) != expected:
            problems.append(f"agency {agency} unit {unit} {col} = {value:,.0f}, "
                            f"OMB says {expected:,}")
    if problems:
        raise SystemExit("FATAL: validation gate failed — not writing CSV.\n  "
                         + "\n  ".join(problems))
    return seen


def write_csv(records: list[dict], path: Path) -> None:
    columns = STATIC_COLUMNS + year_columns()
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)
    log("csv.written", path=str(path), rows=len(records))


# --- main --------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="Output directory (default: viz/agencies/data/).",
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

    releases = discover_june_releases()
    raw = pull_aggregated(build_where(releases))
    log("aggregate.pulled", rows=len(raw))

    check_release_agreement(raw, releases)
    records = pivot(raw, releases)
    log("pivot.done", departments=len(records),
        agencies=len({rec[AGENCY_KEY] for rec in records}))

    validate_gate(records)  # aborts on any mismatch with OMB's printed budget

    if not args.sample_only:
        write_csv(records, out_dir / "nyc_budget.csv")
    sample = [rec for rec in records if rec[AGENCY_KEY] in SAMPLE_AGENCY_NUMBERS]
    write_csv(sample, out_dir / "nyc_budget_sample.csv")

    log("run.done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
