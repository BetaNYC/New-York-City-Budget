#!/usr/bin/env python3
"""
schedulec_cleanup.py — transform this repo's reconciled Schedule C CSVs into the
DataMade "look-at-cook" cleaned-CSV format that viz/js/app.js consumes.

WHY THIS EXISTS
---------------
The look-at-cook toolkit (viz/, MIT — © 2019 DataMade / Derek Eder / Nick Rougeux /
Open City) renders a wide, one-row-per-leaf CSV with per-year measure columns. This
script reads the repo's own authoritative `data/{year}/schedule_c/` files — no live
API, no re-parsing of PDFs — and emits that shape for NYC Council discretionary
(Schedule C) funding.

MAPPING ONTO THE TWO-AXIS MODEL (see viz/PLAN.md for the full rationale)
------------------------------------------------------------------------
look-at-cook has two fixed hierarchy axes that both drill to a shared leaf. The JS
hard-codes the column names `Fund`, `Control Officer`, `Department`, so we KEEP those
column names and repurpose them semantically:

    Fund             (axis 1, top view "Where's it going?")  = Schedule C CATEGORY
    Control Officer  (axis 2, top view "Who administers it?") = administering AGENCY (bucketed)
    Department       (shared leaf)                            = INITIATIVE

Leaf identity is the tuple (category, initiative) — unique within any year (verified).
Each leaf row carries the FULL initiative dollars; grouping by either axis re-sums the
same rows, so BOTH axes reconcile to the same grand total (no dollars are split).

TWO CHART LINES
---------------
Schedule C is a single-measure dataset (award $). We use the toolkit's two series as
two REAL, additive measures rather than collapsing one:

    Adopted <year>    = the initiative's adopted discretionary total  (from *_initiatives.csv)
                        --> the authoritative, reconciled figure. FY2027 grand total
                            reconciles to $655,764,999 exactly (the validation gate).
    Itemized <year>   = the share of that initiative designated to a NAMED recipient
                        (from *_awards.csv, summed per (category, initiative) exact match)
                        --> a genuine measure; NOT gated. The visible gap between the two
                            lines is discretionary money not traceable to a named
                            recipient at the initiative level (lump-sum initiatives such
                            as the Speaker's Initiative, plus a small residue of award
                            rows whose parsed initiative name does not exactly match an
                            initiatives-file name). See viz/PLAN.md § Risks.

Absent leaf-years are written as 0 (not blank): the app sums the per-year columns with
parseFloat, and a blank cell would poison every category/grand total with NaN. This
matches look-at-cook's own convention (0 for a year an entity did not exist).

USAGE
-----
    python3 viz/schedulec_cleanup.py                # writes viz/data/schedule_c.csv
    python3 viz/schedulec_cleanup.py --check        # build + reconcile, do not write
    python3 viz/schedulec_cleanup.py --out PATH --start 2015 --end 2027

Requires only the Python standard library (csv, argparse, os). No third-party deps.
Detects nothing version-specific; runs on Python 3.9+.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# Paths + configuration
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data")

DEFAULT_START = 2015          # first FY with the modern reconciled Schedule C schedule
DEFAULT_END = 2027            # last FY currently in the repo
DEFAULT_OUT = os.path.join(HERE, "data", "schedule_c.csv")

# Initiative-name canonicalization (DATA-ANOMALIES #17). The leaf key is
# (category, initiative); the City spells one initiative differently across years, so the
# raw name splits a single program into multiple short-lived leaves and the funding line
# breaks. We canonicalize the initiative before it becomes a leaf key so those spellings
# merge into one continuous series. Kept deliberately in sync with code/build_combined.py
# (the single source of truth for the house style); stdlib-only to preserve this script's
# standalone, no-deps contract.
CROSSWALK = os.path.join(DATA, "combined", "initiative_name_crosswalk.csv")


def house_style(s: str) -> str:
    """Strip a leading '*' marker, straight-quote curly apostrophes, spell '&' as 'and',
    collapse whitespace. Source casing preserved (acronyms intact)."""
    s = (s or "").strip()
    s = re.sub(r"^\*+\s*", "", s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"\s*&\s*", " and ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_crosswalk(path: str = CROSSWALK) -> dict:
    """raw_initiative -> initiative_canonical. Missing file is not fatal (house_style fallback)."""
    m = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                m[r["raw_initiative"]] = r["initiative_canonical"]
    return m


def canonical_initiative(raw: str, xwalk: dict) -> str:
    """Explicit crosswalk mapping wins; otherwise mechanical house_style normalization."""
    return xwalk.get(raw) or house_style(raw)

# The FY2027 discretionary grand total the repo reconciles to, to the dollar
# (README.md, DATA-DICTIONARY.md). This is the build's validation gate.
FY27_GATE_YEAR = 2027
FY27_GATE_TOTAL = 655_764_999

# The toolkit's fixed leading columns (names are load-bearing — the JS keys on them).
BASE_COLS = [
    "Fund",                    # = Schedule C category
    "Department",              # = initiative (the leaf)
    "Control Officer",         # = administering agency (bucketed)
    "Department ID",           # synthetic stable id
    "Short Title",             # = initiative (display)
    "Link to Website",         # unused for Schedule C (blank)
    "Department Description",  # generated one-line description
]
APROP_LABEL = "Adopted"        # must equal apropTitle in js/app.js
ITEMIZED_LABEL = "Itemized"    # must equal expendTitle in js/app.js


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def agency_bucket(raw: str) -> str:
    """Collapse the initiatives-file `agencies` field to a single axis-2 value.

    Single agency -> that agency. Comma-joined list -> "Multiple agencies".
    Blank -> "Unspecified agency". No dollars are split; this only groups the
    leaf row, so reconciliation is preserved.
    """
    s = (raw or "").strip()
    if not s:
        return "Unspecified agency"
    if "," in s:
        return "Multiple agencies"
    return s


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _initiatives_path(year: int) -> str:
    yy = f"{year % 100:02d}"
    return os.path.join(DATA, f"fy{yy}", "schedule_c", f"fy{yy}_schedule_c_initiatives.csv")


def _awards_path(year: int) -> str:
    yy = f"{year % 100:02d}"
    return os.path.join(DATA, f"fy{yy}", "schedule_c", f"fy{yy}_schedule_c_awards.csv")


def _to_amount(raw) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Core build
# ---------------------------------------------------------------------------
def build_rows(start: int = DEFAULT_START, end: int = DEFAULT_END):
    """Return (fieldnames, rows, diagnostics) for the cleaned CSV.

    Rows are dicts keyed by the output fieldnames. Diagnostics is a dict of
    per-year totals and match stats used by the reconciliation gate and reporting.
    """
    years = list(range(start, end + 1))
    xwalk = load_crosswalk()

    # leaf key = (category, initiative)
    # per leaf: adopted[year], itemized[year], agency bucket (latest year), meta
    adopted: dict[tuple, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    itemized: dict[tuple, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    agency_by_year: dict[tuple, dict[int, str]] = defaultdict(dict)

    diagnostics = {
        "years": years,
        "adopted_year_totals": {},
        "itemized_year_totals": {},
        "awards_matched_pct": {},
        "missing_files": [],
    }

    for year in years:
        ipath = _initiatives_path(year)
        if not os.path.exists(ipath):
            diagnostics["missing_files"].append(ipath)
            continue
        init_rows = _read_csv(ipath)
        year_total = 0.0
        leaf_keys_this_year = set()
        for r in init_rows:
            cat = (r.get("category") or "").strip()
            raw_initiative = (r.get("initiative") or "").strip()
            if not cat or not raw_initiative:
                continue
            # Canonicalize before the name becomes a leaf key, so spellings of one program
            # (e.g. '&' vs 'and' across years) merge into a single continuous series.
            initiative = canonical_initiative(raw_initiative, xwalk)
            key = (cat, initiative)
            amt = _to_amount(r.get("amount"))
            adopted[key][year] += amt
            agency_by_year[key][year] = agency_bucket(r.get("agencies"))
            year_total += amt
            leaf_keys_this_year.add(key)
        diagnostics["adopted_year_totals"][year] = year_total

        # Itemized: sum awards per (category, initiative) exact match to an initiative row.
        apath = _awards_path(year)
        if os.path.exists(apath):
            awd_by_key: dict[tuple, float] = defaultdict(float)
            for a in _read_csv(apath):
                akey = ((a.get("category") or "").strip(),
                        canonical_initiative((a.get("initiative") or "").strip(), xwalk))
                awd_by_key[akey] += _to_amount(a.get("amount"))
            matched_total = 0.0
            all_awards_total = sum(awd_by_key.values())
            for akey, amt in awd_by_key.items():
                if akey in leaf_keys_this_year:
                    itemized[akey][year] += amt
                    matched_total += amt
            diagnostics["itemized_year_totals"][year] = matched_total
            diagnostics["awards_matched_pct"][year] = (
                (matched_total / all_awards_total * 100.0) if all_awards_total else 0.0
            )
        else:
            diagnostics["itemized_year_totals"][year] = 0.0

    # Assemble output rows, one per leaf, sorted for a stable Department ID.
    fieldnames = list(BASE_COLS)
    for year in years:
        fieldnames.append(f"{APROP_LABEL} {year}")
        fieldnames.append(f"{ITEMIZED_LABEL} {year}")

    rows = []
    for dept_id, key in enumerate(sorted(adopted.keys()), start=1):
        cat, initiative = key
        # agency bucket: prefer the most recent year the leaf appears
        present_years = sorted(agency_by_year[key].keys())
        bucket = agency_by_year[key][present_years[-1]] if present_years else "Unspecified agency"
        latest_year = present_years[-1] if present_years else end
        latest_amt = adopted[key].get(latest_year, 0.0)
        desc = (
            f"“{initiative}” — a {cat} discretionary initiative "
            f"administered by {bucket}. FY{latest_year} adopted: "
            f"${latest_amt:,.0f}."
        )
        row = {
            "Fund": cat,
            "Department": initiative,
            "Control Officer": bucket,
            "Department ID": dept_id,
            "Short Title": initiative,
            "Link to Website": "",
            "Department Description": desc,
        }
        for year in years:
            # 0 (not blank) for absent leaf-years: the app sums these columns with
            # parseFloat; a blank would make the whole column total NaN.
            adopted_amt = int(round(adopted[key].get(year, 0.0)))
            itemized_amt = int(round(itemized[key].get(year, 0.0)))
            # Clamp Itemized to Adopted. The awards->initiatives match is by
            # (category, initiative) NAME, which in ~13 leaf-years across the range
            # over-attributes (two source initiatives colliding on one name key),
            # producing itemized > adopted — visibly nonsensical on the chart. We
            # therefore treat Itemized as a LOWER BOUND on dollars designated to a
            # named recipient, capped at the adopted total. See PLAN.md § Risks.
            itemized_amt = min(itemized_amt, adopted_amt)
            row[f"{APROP_LABEL} {year}"] = adopted_amt
            row[f"{ITEMIZED_LABEL} {year}"] = itemized_amt
        rows.append(row)

    # Recompute itemized year totals from the clamped, assembled rows so reported
    # figures match what the viz actually renders.
    for year in years:
        diagnostics["itemized_year_totals"][year] = sum(
            int(r[f"{ITEMIZED_LABEL} {year}"]) for r in rows
        )

    return fieldnames, rows, diagnostics


def reconcile(rows, gate_year=FY27_GATE_YEAR, gate_total=FY27_GATE_TOTAL):
    """Return (ok, computed_total). Sum the Adopted <gate_year> column across all rows."""
    col = f"{APROP_LABEL} {gate_year}"
    computed = sum(int(r[col]) for r in rows)
    return computed == gate_total, computed


def write_csv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=DEFAULT_OUT, help="output CSV path (default: viz/data/schedule_c.csv)")
    ap.add_argument("--start", type=int, default=DEFAULT_START, help="first fiscal year (default 2015)")
    ap.add_argument("--end", type=int, default=DEFAULT_END, help="last fiscal year (default 2027)")
    ap.add_argument("--check", action="store_true", help="build + reconcile, do not write")
    args = ap.parse_args(argv)

    fieldnames, rows, diag = build_rows(args.start, args.end)
    ok, computed = reconcile(rows)

    print(f"Built {len(rows)} leaf rows across FY{args.start}-FY{args.end} "
          f"({len(fieldnames)} columns).")
    if diag["missing_files"]:
        print("  WARNING missing initiatives files:")
        for p in diag["missing_files"]:
            print(f"    {p}")
    print("\nPer-year grand totals (Adopted | Itemized-to-recipient | awards matched %):")
    for y in diag["years"]:
        a = diag["adopted_year_totals"].get(y, 0.0)
        it = diag["itemized_year_totals"].get(y, 0.0)
        pct = diag["awards_matched_pct"].get(y, 0.0)
        print(f"  FY{y}: ${a:>14,.0f} | ${it:>14,.0f} | {pct:5.1f}%")

    print(f"\nReconciliation gate: Adopted {FY27_GATE_YEAR} grand total = ${computed:,} "
          f"(target ${FY27_GATE_TOTAL:,}) -> {'PASS' if ok else 'FAIL'}")

    if not ok:
        print("ERROR: reconciliation gate FAILED — not writing output.", file=sys.stderr)
        return 1

    if args.check:
        print("\n--check: gate passed; no file written.")
        return 0

    write_csv(args.out, fieldnames, rows)
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
