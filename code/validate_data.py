#!/usr/bin/env python3
"""
validate_data.py — reusable, row-level data-QA over every parsed year in data/ (FY2009-FY2027).

Complements the per-file *_reconciliation.txt (which checks only category/subtotal TOTALS) with
row-level and cross-file integrity. Stdlib-only (csv, re, glob, os, argparse, datetime,
collections) so it runs unchanged on any Python 3.11-3.14 the team has installed — no third-party
imports, nothing to add to requirements.txt.

Checks
------
1. Schema consistency  — each file's header matches the expected column set for its type.
2. EIN validity        — every non-empty `ein` is 9 digits after stripping hyphens; per-year
                          EIN-coverage % is reported (feeds the downstream MCP-award-tool decision).
3. Amount sanity       — amounts parse as numbers; Schedule C / award amounts > 0; transparency
                          `rescind` < 0 and `designate` > 0 (`purpose_change` is a transfer, mixed
                          signs expected); zeros and > $1B outliers flagged.
4. Fiscal-year         — year columns are in a plausible range. NOTE: transparency files embed
                          PRIOR-year rows by design (a resolution amends earlier designations); a
                          fiscal_year < the file's folder year is EXPECTED and is not flagged.
5. Duplicate rows      — fully-identical rows within a single file (e.g. the FY2012 `-dup` source).
6. Column-bleed        — a council-member surname leaking into an organization/program text field
                          (the transparency-parser bug class); reported with counts + samples.
7. Reconciliation      — every *_reconciliation.txt is parsed into one pass/partial/N-A ratio table.

Severity + exit code
--------------------
HARD failures (exit 1): missing/extra schema column, malformed row (wrong field count),
non-numeric amount, malformed EIN (non-empty, not 9 digits). These mean the data is structurally
wrong. SOFT advisories (exit 0 if nothing hard): zeros, sign anomalies, outliers, duplicates,
column-bleed residuals, low EIN coverage. Advisories are surfaced, not gated — some (e.g. the ~21
legitimate-name FY26 bleed residuals) are known and acceptable.

Usage
-----
  .venv/bin/python code/validate_data.py                 # validate ./data, write data/QA-REPORT.md
  .venv/bin/python code/validate_data.py --data-dir data --report data/QA-REPORT.md
  .venv/bin/python code/validate_data.py --no-report     # stdout only
"""
import argparse
import csv
import datetime
import glob
import os
import re
from collections import Counter, defaultdict

# ------------------------------------------------------------------ type registry
# Each type: required columns (exact order not required, set membership is), any optional columns,
# the EIN column name (or None), the amount columns, the amount sign rule, and the year column.
TYPES = {
    "schedule_c_initiatives": dict(
        cols=["category", "agencies", "initiative", "amount"],
        ein=None, amounts=["amount"], rule="positive", year_col=None),
    "schedule_c_awards": dict(
        cols=["category", "initiative", "award_type", "member", "organization",
              "program", "ein", "amount", "agency", "purpose"],
        ein="ein", amounts=["amount"], rule="positive", year_col=None,
        text_cols=["organization", "program"]),
    "appendix_aging": dict(
        cols=["member", "organization", "program", "ein", "amount", "purpose"],
        ein="ein", amounts=["amount"], rule="positive", year_col=None,
        text_cols=["organization", "program"]),
    "appendix_local": dict(
        cols=["member", "organization", "program", "ein", "amount", "agency", "purpose"],
        ein="ein", amounts=["amount"], rule="positive", year_col=None,
        text_cols=["organization", "program"]),
    "appendix_youth": dict(
        cols=["member", "organization", "program", "ein", "amount", "purpose"],
        ein="ein", amounts=["amount"], rule="positive", year_col=None,
        text_cols=["organization", "program"]),
    "terms": dict(
        cols=["item_number", "agency_name", "agency_code", "units_of_appropriation",
              "num_units", "report_deadlines", "coverage_period", "condition_text"],
        ein=None, amounts=[], rule=None, year_col=None),
    "transparency": dict(
        cols=["resolution", "date", "chart", "fiscal_year", "action", "source",
              "council_member", "organization", "program", "ein", "amount", "agency",
              "agy_num", "ua", "purpose", "flags"],
        ein="ein", amounts=["amount"], rule="transparency", year_col="fiscal_year",
        text_cols=["organization", "program"], member_col="council_member",
        embeds_prior_years=True),
    "transparency_reso": dict(
        cols=["resolution", "date", "chart", "fiscal_year", "action", "source",
              "council_member", "organization", "program", "ein", "amount", "agency",
              "agy_num", "ua", "purpose", "flags"],
        ein="ein", amounts=["amount"], rule="transparency", year_col="fiscal_year",
        text_cols=["organization", "program"], member_col="council_member",
        embeds_prior_years=True),
    "capital": dict(
        cols=["part", "agency", "budget_line", "sub_id", "boro", "fy1", "fy2", "fy3",
              "fy4", "sponsor", "title", "building_code", "school_code"],
        optional=["action"], ein=None, amounts=["fy1", "fy2", "fy3", "fy4"],
        rule="nonneg", year_col=None),
    "combined_initiatives": dict(
        cols=["year", "category", "agencies", "initiative", "amount"],
        ein=None, amounts=["amount"], rule="positive", year_col="year"),
    "combined_awards": dict(
        # `purpose` mirrors the per-year schedule_c_awards schema — build_combined.py carries it
        # through so source-distinct rows are not collapsed into false duplicates (DATA-ANOMALIES #8).
        cols=["year", "category", "initiative", "award_type", "member", "organization",
              "program", "ein", "amount", "agency", "purpose"],
        ein="ein", amounts=["amount"], rule="positive", year_col="year",
        text_cols=["organization", "program"]),
}

# boroughs/agencies that show up in the noisy `member` column but are NOT council surnames —
# excluded from the column-bleed surname set to avoid false positives.
NOT_SURNAMES = {"brooklyn", "bronx", "queens", "manhattan", "staten", "island", "speaker",
                "citywide", "delegation", "various"}

BILLION = 1_000_000_000


def detect_type(path):
    """Map a data file to its schema type by filename. Returns a type key or None (skip)."""
    b = os.path.basename(path)
    if b == "legistar_crosswalk.csv":
        return None  # hand-maintained crosswalk, not parsed budget data
    if b == "all_years_initiatives.csv":
        return "combined_initiatives"
    if b == "all_years_awards.csv":
        return "combined_awards"
    if b.endswith("_schedule_c_initiatives.csv"):
        return "schedule_c_initiatives"
    if b.endswith("_schedule_c_awards.csv"):
        return "schedule_c_awards"
    if b.endswith("_appendix_a_aging.csv"):
        return "appendix_aging"
    if b.endswith("_appendix_b_local.csv"):
        return "appendix_local"
    if b.endswith("_appendix_c_youth.csv"):
        return "appendix_youth"
    if b.endswith("_terms_and_conditions.csv"):
        return "terms"
    if b.endswith("_transparency_all.csv"):
        return "transparency"
    if re.match(r"reso\d+_transparency_designations\.csv$", b):
        return "transparency_reso"
    if b.endswith("_capital_projects.csv"):
        return "capital"
    return None


def year_of(path):
    """Folder fiscal year as an int (2000+NN) from a .../fyNN/... path, else None."""
    m = re.search(r"/fy(\d{2})/", path.replace(os.sep, "/"))
    return 2000 + int(m.group(1)) if m else None


def parse_amount(s):
    """Return (value, ok). ok=False means a non-empty, non-numeric value (malformed)."""
    s = (s or "").strip()
    if s == "":
        return None, True
    t = s.replace("$", "").replace(",", "").replace(" ", "")
    try:
        return float(t), True
    except ValueError:
        return None, False


class FileResult:
    def __init__(self, path, typ, year):
        self.path = path
        self.typ = typ
        self.year = year
        self.nrows = 0
        self.hard = []   # (check, message)
        self.soft = []   # (check, message)
        self.ein_total = 0
        self.ein_present = 0   # non-empty
        self.ein_valid = 0     # non-empty AND 9-digit
        self.dupes = 0
        self.dupe_samples = []
        self.bleed = 0
        self.bleed_samples = []

    def coverage(self):
        return (100.0 * self.ein_valid / self.nrows) if self.nrows else 0.0


def check_file(path, surnames):
    typ = detect_type(path)
    if typ is None:
        return None
    spec = TYPES[typ]
    year = year_of(path)
    res = FileResult(path, typ, year)

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if not rows:
        res.hard.append(("schema", "empty file (no header)"))
        return res
    header = rows[0]
    body = rows[1:]
    res.nrows = len(body)

    # --- 1. schema
    hset = set(header)
    required = set(spec["cols"])
    optional = set(spec.get("optional", []))
    missing = required - hset
    extra = hset - required - optional
    if missing:
        res.hard.append(("schema", f"missing columns: {sorted(missing)}"))
    if extra:
        res.hard.append(("schema", f"unexpected columns: {sorted(extra)}"))
    # malformed rows: field count != header width
    bad_width = [i + 2 for i, r in enumerate(body) if len(r) != len(header)]
    if bad_width:
        res.hard.append(("schema", f"{len(bad_width)} row(s) with wrong field count "
                                   f"(first at line {bad_width[0]})"))

    # if the header is unusable, skip value-level checks (they'd be meaningless)
    idx = {c: i for i, c in enumerate(header)}

    def cell(r, col):
        i = idx.get(col)
        return r[i] if (i is not None and i < len(r)) else ""

    # --- 5. duplicate rows (within file)
    seen = Counter(tuple(r) for r in body if len(r) == len(header))
    for rowtuple, c in seen.items():
        if c > 1:
            res.dupes += (c - 1)
            if len(res.dupe_samples) < 3:
                res.dupe_samples.append((c, list(rowtuple)))

    # --- 2/3/4/6 per-row value checks
    ein_col = spec.get("ein")
    action_col = "action" if typ in ("transparency", "transparency_reso") else None
    bad_eins = []
    zero_amts = 0
    sign_bad = []
    outliers = []
    year_bad = []
    fy_embedded = 0
    fy_empty = 0
    member_col = spec.get("member_col")
    text_cols = spec.get("text_cols", [])

    for ln, r in enumerate(body, start=2):
        if len(r) != len(header):
            continue  # already flagged as malformed
        # EIN
        if ein_col:
            res.ein_total += 1
            raw = cell(r, ein_col).strip()
            if raw:
                res.ein_present += 1
                digits = raw.replace("-", "")
                if digits.isdigit() and len(digits) == 9:
                    res.ein_valid += 1
                else:
                    if len(bad_eins) < 5:
                        bad_eins.append((ln, raw))
        # amounts
        action = cell(r, action_col).strip().lower() if action_col else ""
        for acol in spec["amounts"]:
            val, ok = parse_amount(cell(r, acol))
            if not ok:
                res.hard.append(("amount", f"line {ln} col {acol}: non-numeric "
                                           f"{cell(r, acol)!r}"))
                continue
            if val is None:
                continue
            if abs(val) > BILLION and len(outliers) < 5:
                outliers.append((ln, acol, val))
            rule = spec["rule"]
            if rule == "positive":
                if val == 0:
                    zero_amts += 1
                elif val < 0 and len(sign_bad) < 5:
                    sign_bad.append((ln, f"{acol} negative {val:,.0f} (expected > 0)"))
            elif rule == "nonneg":
                if val < 0 and len(sign_bad) < 5:
                    sign_bad.append((ln, f"{acol} negative {val:,.0f} (capital expected >= 0)"))
            elif rule == "transparency":
                if action == "designate" and val <= 0 and len(sign_bad) < 5:
                    sign_bad.append((ln, f"designate amount {val:,.0f} (expected > 0)"))
                elif action == "rescind" and val >= 0 and len(sign_bad) < 5:
                    sign_bad.append((ln, f"rescind amount {val:,.0f} (expected < 0)"))
                # purpose_change / other: mixed signs expected -> no sign check
        # fiscal year
        ycol = spec.get("year_col")
        if ycol:
            yv = cell(r, ycol).strip()
            if ycol == "year":  # combined 'FYnn'
                m = re.match(r"FY(\d{2})$", yv)
                yr = 2000 + int(m.group(1)) if m else None
            else:
                yr = int(yv) if yv.isdigit() else None
                if yv == "":
                    fy_empty += 1
            if yr is not None:
                if yr < 2005 or yr > 2035:
                    if len(year_bad) < 5:
                        year_bad.append((ln, yv))
                elif spec.get("embeds_prior_years") and res.year and yr < res.year:
                    fy_embedded += 1  # EXPECTED (prior-year designation being amended)
                elif res.year and yr > res.year + 1:
                    if len(year_bad) < 5:
                        year_bad.append((ln, f"{yv} is after folder year FY{res.year}"))
        # column bleed: a surname as the leading token of an org/program field
        for tcol in text_cols:
            v = cell(r, tcol).strip()
            if not v:
                continue
            first = v.split()[0].strip(".,").lower()
            if first in surnames and len(v.split()) > 1:
                res.bleed += 1
                if len(res.bleed_samples) < 5:
                    res.bleed_samples.append((ln, tcol, v[:60]))
                break

    # roll per-row tallies into findings
    if bad_eins:
        res.hard.append(("ein", f"{len(bad_eins)}+ malformed EIN(s), e.g. line {bad_eins[0][0]}: "
                                f"{bad_eins[0][1]!r}"))
    if zero_amts:
        res.soft.append(("amount", f"{zero_amts} row(s) with amount == 0"))
    for ln, msg in sign_bad:
        res.soft.append(("amount", f"line {ln}: {msg}"))
    for ln, acol, val in outliers:
        res.soft.append(("amount", f"line {ln} col {acol}: outlier {val:,.0f} (> $1B)"))
    for ln, yv in year_bad:
        res.soft.append(("fiscal_year", f"line {ln}: implausible/forward year {yv!r}"))
    if fy_embedded:
        res.soft.append(("fiscal_year", f"{fy_embedded} prior-year row(s) embedded "
                                        f"(EXPECTED for transparency; not an error)"))
    if fy_empty:
        res.soft.append(("fiscal_year", f"{fy_empty} row(s) with empty fiscal_year"))
    if res.dupes:
        c, sample = res.dupe_samples[0]
        res.soft.append(("duplicate", f"{res.dupes} duplicate row instance(s); "
                                      f"e.g. x{c}: {sample[:4]}..."))
    if res.bleed:
        ln, tcol, v = res.bleed_samples[0]
        res.soft.append(("column_bleed", f"{res.bleed} suspected surname-in-{tcol} residual(s); "
                                         f"e.g. line {ln}: {v!r}"))
    return res


def build_surname_set(files):
    """Council-member surnames drawn from the (cleaner) transparency `council_member` column,
    used only to spot member-name leakage into org/program fields. Conservative: single alpha
    tokens >= 4 chars, boroughs/agencies excluded."""
    surnames = set()
    for path in files:
        typ = detect_type(path)
        if typ not in ("transparency", "transparency_reso"):
            continue
        with open(path, newline="", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            for r in rd:
                v = (r.get("council_member") or "").strip()
                if not v:
                    continue
                tok = v.split()[-1]  # surname is the last token ("De La Rosa" -> "Rosa")
                low = tok.lower()
                if tok.isalpha() and len(tok) >= 4 and low not in NOT_SURNAMES:
                    surnames.add(low)
    return surnames


# ------------------------------------------------------------------ reconciliation roll-up
RECON_PATTERNS = [
    ("schedule_c", re.compile(r"(\d+)\s*/\s*(\d+)\s+(?:reconcilable\s+)?categories exact")),
    ("capital", re.compile(r"(\d+)\s*/\s*(\d+)\s+agency subtotals reconcile")),
]


def parse_reconciliations(data_dir):
    """Return list of (year:int|None, doctype, ratio_str, status) from every *_reconciliation.txt."""
    out = []
    for path in sorted(glob.glob(os.path.join(data_dir, "fy*", "*", "*reconciliation*.txt"))):
        text = open(path, encoding="utf-8").read()
        year = year_of(path)
        if "schedule_c" in path:
            doctype = "schedule_c"
        elif "capital" in path:
            doctype = "capital"
        elif "transparency" in path:
            doctype = "transparency"
        else:
            doctype = "other"
        if re.search(r"NOT RECONCILABLE", text, re.I):
            out.append((year, doctype, "—", "N/A (no printed totals)"))
            continue
        matched = False
        for _name, pat in RECON_PATTERNS:
            m = pat.search(text)
            if m:
                num, den = int(m.group(1)), int(m.group(2))
                status = "PASS" if num == den else f"PARTIAL ({den - num} in-source diff)"
                out.append((year, doctype, f"{num}/{den}", status))
                matched = True
                break
        if not matched:
            out.append((year, doctype, "?", "unparsed"))
    return out


# ------------------------------------------------------------------ orchestration
def validate_tree(data_dir):
    files = sorted(glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True))
    surnames = build_surname_set(files)
    results = []
    for path in files:
        r = check_file(path, surnames)
        if r is not None:
            results.append(r)
    recon = parse_reconciliations(data_dir)
    return results, recon, surnames


def coverage_by_year(results):
    """(year, doctype) -> (valid_ein, rows). Transparency uses only the *_all file to avoid
    double-counting the per-reso components."""
    agg = defaultdict(lambda: [0, 0])
    for r in results:
        if TYPES[r.typ].get("ein") is None:
            continue
        if r.typ == "transparency_reso":
            continue  # components of transparency_all — would double-count
        if r.typ.startswith("combined_"):
            continue  # roll-ups of already-counted per-year data
        doctype = {"schedule_c_awards": "awards", "appendix_aging": "appendix",
                   "appendix_local": "appendix", "appendix_youth": "appendix",
                   "transparency": "transparency"}.get(r.typ, r.typ)
        key = (r.year, doctype)
        agg[key][0] += r.ein_valid
        agg[key][1] += r.nrows
    return agg


def print_summary(results, recon):
    hard = sum(len(r.hard) for r in results)
    soft = sum(len(r.soft) for r in results)
    print(f"validate_data: {len(results)} files checked | "
          f"{hard} HARD finding(s) | {soft} soft advisory(ies)")
    if hard:
        print("\nHARD FAILURES:")
        for r in results:
            for check, msg in r.hard:
                print(f"  [{check}] {os.path.relpath(r.path)}: {msg}")
    cov = coverage_by_year(results)
    print("\nEIN coverage (valid 9-digit / rows), EIN-bearing doctypes:")
    for (year, doctype), (v, n) in sorted(cov.items(), key=lambda k: (str(k[0][0]), k[0][1])):
        pct = 100.0 * v / n if n else 0.0
        print(f"  FY{year} {doctype:16} {v:6d}/{n:<6d}  {pct:5.1f}%")
    print(f"\nReconciliation roll-up ({len(recon)} files):")
    for year, doctype, ratio, status in recon:
        print(f"  FY{year} {doctype:13} {ratio:>7}  {status}")
    return hard


def write_report(results, recon, surnames, md_path, data_dir):
    today = datetime.date.today().isoformat()
    hard = sum(len(r.hard) for r in results)
    soft = sum(len(r.soft) for r in results)
    cov = coverage_by_year(results)
    L = []
    L.append("# NYC Budget — Data QA Report")
    L.append("")
    L.append(f"**Report generated:** {today}  ")
    L.append(f"**Data current as of:** {today} (files under `{data_dir}/`)  ")
    L.append(f"**Tool:** `code/validate_data.py`")
    L.append("")
    L.append(f"**Verdict:** {'FAIL' if hard else 'PASS'} — "
             f"{len(results)} files, {hard} hard failure(s), {soft} soft advisory(ies).")
    L.append("")
    L.append("Severity: HARD (exit 1) = schema drift, malformed row, non-numeric amount, or "
             "malformed EIN. SOFT (exit 0) = zeros, sign anomalies, outliers, duplicates, "
             "column-bleed residuals, coverage notes. See the module docstring for the full "
             "check list and rationale.")
    L.append("")

    if hard:
        L.append("## Hard failures")
        L.append("")
        for r in results:
            for check, msg in r.hard:
                L.append(f"- **[{check}]** `{os.path.relpath(r.path, data_dir)}` — {msg}")
        L.append("")

    L.append("## EIN coverage (feeds the MCP award-tool decision)")
    L.append("")
    L.append("Valid 9-digit EINs / total rows, per year and EIN-bearing doctype. Initiatives, "
             "terms, and capital carry no EIN by design and are omitted. Transparency uses the "
             "`*_transparency_all.csv` file (per-reso components excluded to avoid double count).")
    L.append("")
    L.append("| FY | doctype | valid EIN / rows | coverage |")
    L.append("|---|---|---|---|")
    for (year, doctype), (v, n) in sorted(cov.items(), key=lambda k: (str(k[0][0]), k[0][1])):
        pct = 100.0 * v / n if n else 0.0
        L.append(f"| FY{year} | {doctype} | {v}/{n} | {pct:.1f}% |")
    L.append("")

    L.append("## Reconciliation roll-up")
    L.append("")
    L.append("Parsed from every `*_reconciliation.txt`. Transparency prints no totals → N/A by "
             "nature. PARTIAL = documented in-source arithmetic diffs, not extraction errors.")
    L.append("")
    L.append("| FY | doctype | ratio | status |")
    L.append("|---|---|---|---|")
    for year, doctype, ratio, status in recon:
        L.append(f"| FY{year} | {doctype} | {ratio} | {status} |")
    L.append("")

    L.append("## Per-file findings")
    L.append("")
    L.append("| file | rows | EIN cov | hard | soft findings |")
    L.append("|---|---|---|---|---|")
    for r in sorted(results, key=lambda x: x.path):
        rel = os.path.relpath(r.path, data_dir)
        covs = f"{r.coverage():.0f}%" if TYPES[r.typ].get("ein") else "—"
        softtxt = "; ".join(f"{c}: {m}" for c, m in r.soft) or "—"
        L.append(f"| `{rel}` | {r.nrows} | {covs} | {len(r.hard)} | {softtxt} |")
    L.append("")
    L.append("### Notes on the soft heuristics")
    L.append("")
    L.append(f"- **Column-bleed** is a *suspected*-residual heuristic: it flags an organization/"
             f"program field whose leading token is one of {len(surnames)} surnames drawn from the "
             f"transparency `council_member` column (boroughs/agencies excluded). Because that "
             f"source column itself carries some bleed, the set is imperfect and the check has "
             f"known FALSE POSITIVES — organizations whose real name simply begins with such a "
             f"token (e.g. `Hudson Guild`, `Joseph P. Addabbo Family Health Center`). Genuine "
             f"residuals look like `Brewer ParentsofPublicSchool9,Inc.` (a member surname prepended "
             f"to a glued-word org). Treat this column as a review queue, not a defect list; the "
             f"repo has no authoritative council-member roster to validate against.")
    L.append("- **Capital negative amounts**: the §254 books are *Changes to the Capital Budget*, "
             "so a negative FY amount (a de-appropriation/reduction) can be legitimate. Flagged for "
             "review, not treated as an error.")
    L.append("- **Transparency prior-year rows**: a resolution routinely amends *earlier* years' "
             "designations, so `fiscal_year` values below the folder year are expected and counted, "
             "not flagged.")
    L.append("")
    os.makedirs(os.path.dirname(md_path) or ".", exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Row-level data QA over parsed NYC budget data.")
    ap.add_argument("--data-dir", default="data", help="root of the parsed data tree (default: data)")
    ap.add_argument("--report", default=None,
                    help="path for the markdown report (default: <data-dir>/QA-REPORT.md)")
    ap.add_argument("--no-report", action="store_true", help="stdout only; do not write the report")
    a = ap.parse_args()
    results, recon, surnames = validate_tree(a.data_dir)
    hard = print_summary(results, recon)
    if not a.no_report:
        md_path = a.report or os.path.join(a.data_dir, "QA-REPORT.md")
        write_report(results, recon, surnames, md_path, a.data_dir)
        print(f"\nWROTE -> {md_path}")
    raise SystemExit(1 if hard else 0)


if __name__ == "__main__":
    main()
