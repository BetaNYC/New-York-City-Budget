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
8. Initiative recon    — award rows summed per initiative vs that initiative's PRINTED amount in
                          *_schedule_c_initiatives.csv, per fiscal year: balanced / short / over
                          with the residual. The first pass/fail target the award stream has ever
                          had. SOFT advisory. See `initiative_reconciliation()` for why.

Severity + exit code
--------------------
HARD failures (exit 1): missing/extra schema column, malformed row (wrong field count),
non-numeric amount, malformed EIN (non-empty, not 9 digits). These mean the data is structurally
wrong. SOFT advisories (exit 0 if nothing hard): zeros, sign anomalies, outliers, duplicates,
column-bleed residuals, low EIN coverage, initiative-reconciliation residuals. Advisories are
surfaced, not gated — some (e.g. the ~21 legitimate-name FY26 bleed residuals) are known and
acceptable.

Usage
-----
  .venv/bin/python code/validate_data.py                 # validate ./data, write data/QA-REPORT.md
  .venv/bin/python code/validate_data.py --data-dir data --report data/QA-REPORT.md
  .venv/bin/python code/validate_data.py --no-report     # stdout only
  .venv/bin/python code/validate_data.py --dry-run       # stdout only; writes nothing at all
"""
import argparse
import csv
import datetime
import glob
import os
import re
from collections import Counter, defaultdict

# An EIN printed inside a free-text field. `ein` columns are digits-only by the time they are
# validated, so a hyphenated EIN in prose is always a row-boundary artifact, never a real value.
EIN_IN_TEXT = re.compile(r"\d{2}-\d{7}")

# Descriptive prose sitting where a grantee name belongs. Deliberately conservative: matches
# purpose-statement verb phrases, not merely long names, so a genuinely wordy organization name
# does not trip it. Measured 438/33,638 rows corpus-wide, every sampled hit a real defect.
ORG_PROSE = re.compile(
    r"\b(will |funds? (requested|will)|to support|to provide|funding (for|to|will)"
    r"|in order to|program that|services to)\b", re.I)

# Types whose `organization` column must not contain an EIN or a dollar sign. Every award-bearing
# schema, including the appendices and the combined roll-up — the defect predates the appendix
# load and is not confined to one stream.
ORG_INTEGRITY_TYPES = {
    "schedule_c_awards", "combined_awards",
    "appendix_aging", "appendix_local", "appendix_youth",
}

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
    "recovered_awards": dict(
        # Sidecar: awards the Schedule C parser absorbed into a neighbouring row and lost
        # (DATA-ANOMALIES.md §20). Deliberately NOT merged into the per-year CSVs — these carry
        # provenance columns the per-year schema has no place for, and nothing already published
        # should move. Built by code/build_recovered_awards.py.
        cols=["fiscal_year", "category", "initiative", "award_type", "member", "organization",
              "program", "ein", "amount", "agency", "purpose", "confidence", "name_source",
              "absorbed_from_file", "absorbed_from_line", "absorbed_from_ein",
              "disclosure_confirmed"],
        ein="ein", amounts=["amount"], rule="positive", year_col="fiscal_year",
        text_cols=["organization", "program"]),
    "recovered_appendix": dict(
        # Sidecar: appendix designations for FY2015-17, FY2019-20, whose own appendix CSVs are
        # empty (header row only) while FY2021+ hold ~4,000 rows each. Recovered from the
        # Council's disclosure workbooks. Sidecar for the same reason as recovered_awards:
        # nothing already published moves. Built by code/build_appendix_from_disclosure.py.
        cols=["fiscal_year", "stream", "member", "organization", "program", "ein", "amount",
              "agency", "purpose", "status", "confidence", "source_file"],
        ein="ein", amounts=["amount"], rule="positive", year_col="fiscal_year",
        text_cols=["organization", "program"]),
    "capital": dict(
        cols=["part", "agency", "budget_line", "sub_id", "boro", "fy1", "fy2", "fy3",
              "fy4", "sponsor", "title", "building_code", "school_code"],
        optional=["action"], ein=None, amounts=["fy1", "fy2", "fy3", "fy4"],
        rule="nonneg", year_col=None),
    "combined_initiatives": dict(
        # `category_canonical` / `initiative_canonical` are derived columns build_combined.py inserts
        # right after their raw source columns during crosswalk curation (DATA-ANOMALIES #17/#18).
        cols=["year", "category", "category_canonical", "agencies", "initiative",
              "initiative_canonical", "amount"],
        ein=None, amounts=["amount"], rule="positive", year_col="year"),
    "combined_awards": dict(
        # `purpose` mirrors the per-year schedule_c_awards schema — build_combined.py carries it
        # through so source-distinct rows are not collapsed into false duplicates (DATA-ANOMALIES #8).
        # `category_canonical` / `initiative_canonical` are derived, inserted right after their raw
        # source columns during crosswalk curation (DATA-ANOMALIES #17/#18).
        cols=["year", "category", "category_canonical", "initiative", "initiative_canonical",
              "award_type", "member", "organization", "program", "ein", "amount", "agency",
              "purpose"],
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
    if b == "schedule_c_appendix_recovered.csv":
        return "recovered_appendix"
    if b == "schedule_c_absorbed_awards.csv":
        return "recovered_awards"
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
    # capital `agency` is a pure agency name (e.g. 'CULTURAL INSTITUTIONS'); a digit in it means a
    # whole mis-parsed row's worth of text (amounts, codes) leaked into the column — the FY2027
    # non-city column-bleed class. Agency names never contain digits in any parsed year, so this
    # is a zero-false-positive signal.
    agency_polluted = []
    org_merged = []
    org_prose = []

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
        # capital agency-pollution: a digit in the agency name = a leaked mis-parsed row
        if typ == "capital":
            ag = cell(r, "agency")
            if any(ch.isdigit() for ch in ag):
                agency_polluted.append((ln, ag))
        # award org-integrity: an EIN or a dollar sign inside `organization` means the row
        # boundary was lost — either a following award was absorbed into this one's text
        # (FY2016-FY2020: "Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services"),
        # or the purpose prose landed in the org field (FY2024-FY2026). In both cases the row's
        # own `amount` may belong to a DIFFERENT organization than its `organization` names, so
        # this is an accuracy signal, not a cosmetic one. Same zero-false-positive shape as the
        # capital agency check above: verified 276/33,638 rows flagged corpus-wide, every one a
        # real defect on inspection. See DATA-ANOMALIES.md.
        if typ in ORG_INTEGRITY_TYPES:
            org = cell(r, "organization")
            if EIN_IN_TEXT.search(org) or "$" in org:
                org_merged.append((ln, org))
            # Purpose prose in the organization slot: the grantee's NAME was lost and descriptive
            # text took its place. Distinct from org_merged and materially less severe — the `ein`
            # and `amount` on these rows are intact (verified: 438/438 carry a valid 9-digit EIN),
            # so the award is still correctly attributed and correctly valued; only the display
            # name is wrong. Kept as its own advisory precisely so the two are not conflated.
            elif ORG_PROSE.search(org):
                org_prose.append((ln, org))
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
    if agency_polluted:
        ln, v = agency_polluted[0]
        res.soft.append(("agency_pollution", f"{len(agency_polluted)} capital row(s) with a digit "
                                             f"in `agency` (leaked mis-parsed row); "
                                             f"e.g. line {ln}: {v[:60]!r}"))
    if org_prose:
        ln, v = org_prose[0]
        res.soft.append(("org_prose", f"{len(org_prose)} award row(s) whose `organization` holds "
                                      f"purpose prose instead of a grantee name — `ein` and "
                                      f"`amount` are intact, the display name is lost; "
                                      f"e.g. line {ln}: {v[:60]!r}"))
    if org_merged:
        ln, v = org_merged[0]
        res.soft.append(("org_merged", f"{len(org_merged)} award row(s) with an EIN or `$` inside "
                                       f"`organization` — row boundary lost, so `amount` may belong "
                                       f"to a different org than `organization` names; "
                                       f"e.g. line {ln}: {v[:60]!r}"))
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


# --------------------------------------------- initiative-level award reconciliation (check 8)
# The per-year *_reconciliation.txt reconciles the CATEGORY summary against printed category
# TOTALs and reports award rows as a bare tally with NO target ("awards: 335 rows $89,917,012").
# The printed INITIATIVE amount is a target: where the Schedule C itemizes an initiative at all,
# the itemization is exhaustive, so the award rows under an initiative should sum to that
# initiative's own printed amount. 24%-87% of joined initiatives already balance to the dollar
# with no repair, which is what makes a residual on the rest a real signal rather than noise.
#
# The printed CATEGORY total is NOT a usable target for award rows and cannot be made into one:
# most initiatives are lump appropriations with no per-grantee table in the PDF at all, so award
# rows cover 27%-92% of printed category dollars by design. Measured and rejected — do not
# re-derive it. (research/missing-absorbed-awards/RECONCILIATION.md §2-§3, branch
# research/missing-absorbed-awards.)
#
# Deliberately SOFT, never a hard failure. Three known structural gaps live in this residual and
# a gate would only break the build on them: award rows carrying no initiative label at all
# ($172M in FY2026), initiative labels the parser mis-assigns to a neighbouring block, and
# provider tables the PDF text layer never yielded. Surfacing them is the point.


def canon_initiative(s):
    """Fold an initiative name into a join key: lowercase, drop every non-alphanumeric.

    The summary table and the body headers punctuate the same initiative inconsistently — curly
    vs. straight apostrophes, en-dash vs. hyphen ("Alternatives to Incarceration (ATI's)") — so
    punctuation is folded out entirely rather than enumerated.

    EXACT match only. A prefix or fuzzy join was measured and rejected: FY2018 alone has six
    "Crisis Management System - <sub-program>" award labels whose parent is a single initiative
    line, and a prefix join would pool them and manufacture a fake balance.
    """
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _cents(s):
    """Amount as integer cents, so residuals compare exactly. Unparseable/empty -> 0 (the amount
    checks above already flag those as HARD; this pass must not double-report them)."""
    val, ok = parse_amount(s)
    return int(round(val * 100)) if (ok and val is not None) else 0


def load_recovered_awards(data_dir):
    """(year:int -> Counter(join key -> cents), sidecar_present:bool) for the absorbed-award
    sidecar `recovered/schedule_c_absorbed_awards.csv`.

    Optional by design. The sidecar is a separate build artifact (code/build_recovered_awards.py)
    holding awards the parser absorbed into a neighbouring row and lost; it is deliberately NOT
    merged into the per-year CSVs. When it is absent the check still runs and the "after recovery"
    columns simply equal the base ones.
    """
    path = os.path.join(data_dir, "recovered", "schedule_c_absorbed_awards.csv")
    out = defaultdict(Counter)
    if not os.path.exists(path):
        return out, False
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            y = (r.get("fiscal_year") or "").strip()
            if y.isdigit():
                # a blank initiative folds to key "" and is counted as unjoinable below, never
                # silently attributed to some initiative it might belong to
                out[int(y)][canon_initiative(r.get("initiative"))] += _cents(r.get("amount"))
    return out, True


def initiative_reconciliation(data_dir):
    """Per fiscal year, join award rows to their initiative and compare against the printed amount.

    Returns (years, sidecar_present) where `years` is a list of per-year dicts, oldest first. All
    money is integer cents. `rows` holds one record per JOINED initiative:
        initiative, printed, awarded, residual (= printed - awarded), status, n_awards,
        recovered, residual_after (= residual - recovered)
    status is 'balanced' (residual 0) / 'short' (> 0) / 'over' (< 0).

    Everything that could not be joined is carried out as an explicit tally rather than dropped,
    because the unjoined dollars are large and a reader who saw only the joined side would badly
    overestimate coverage.
    """
    recovered, sidecar_present = load_recovered_awards(data_dir)
    years = []
    pattern = os.path.join(data_dir, "fy*", "schedule_c", "*_schedule_c_initiatives.csv")
    for ipath in sorted(glob.glob(pattern)):
        apath = ipath.replace("_initiatives.csv", "_awards.csv")
        if not os.path.exists(apath):
            continue  # FY2009-FY2014 are initiatives-only by nature, not a gap (DATA-ANOMALIES §1)
        year = year_of(ipath)
        if year is None:
            continue  # not under a data/fyNN/ folder — nothing to key the sidecar or the row on

        printed, label = Counter(), {}
        with open(ipath, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                k = canon_initiative(r.get("initiative"))
                if not k:
                    continue
                # one initiative printed on two summary lines (different agencies) sums — the join
                # is by name, so the target for that name is the total printed under it
                printed[k] += _cents(r.get("amount"))
                label.setdefault(k, (r.get("initiative") or "").strip())

        awarded, n_awards = Counter(), Counter()
        unlabeled_rows = unlabeled_amount = 0
        with open(apath, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                k = canon_initiative(r.get("initiative"))
                amt = _cents(r.get("amount"))
                if not k:
                    unlabeled_rows += 1
                    unlabeled_amount += amt
                    continue
                awarded[k] += amt
                n_awards[k] += 1

        rec = recovered.get(year, Counter())
        rows, counts, counts_after = [], Counter(), Counter()
        for k in sorted(awarded, key=lambda k: label.get(k, k).lower()):
            if k not in printed:
                continue
            residual = printed[k] - awarded[k]
            after = residual - rec.get(k, 0)
            status = "balanced" if residual == 0 else ("short" if residual > 0 else "over")
            counts[status] += 1
            counts_after["balanced" if after == 0 else ("short" if after > 0 else "over")] += 1
            rows.append(dict(initiative=label[k], printed=printed[k], awarded=awarded[k],
                             residual=residual, status=status, n_awards=n_awards[k],
                             recovered=rec.get(k, 0), residual_after=after))

        unjoined = [k for k in awarded if k not in printed]
        years.append(dict(
            year=year,
            rows=rows,
            balanced=counts["balanced"], short=counts["short"], over=counts["over"],
            balanced_after=counts_after["balanced"], short_after=counts_after["short"],
            over_after=counts_after["over"],
            printed=sum(r["printed"] for r in rows),
            awarded=sum(r["awarded"] for r in rows),
            recovered=sum(r["recovered"] for r in rows),
            unjoined_labels=len(unjoined),
            unjoined_amount=sum(awarded[k] for k in unjoined),
            unlabeled_rows=unlabeled_rows,
            unlabeled_amount=unlabeled_amount,
            recovered_unjoined=sum(v for k, v in rec.items() if k not in printed),
        ))
    return years, sidecar_present


def _usd(cents):
    """Whole-dollar display; the corpus carries no sub-dollar amounts, but cents are preserved
    internally so a future one cannot silently round into a false balance."""
    return f"{cents / 100:,.0f}" if cents % 100 == 0 else f"{cents / 100:,.2f}"


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


def print_initiative_recon(years, sidecar_present):
    """Per-year roll-up on stdout. The per-initiative residuals go to the markdown report — 455
    unbalanced initiatives corpus-wide is a review queue, not terminal output."""
    print("\nInitiative-level award reconciliation (SOFT — award rows vs printed initiative "
          "amount):")
    if not years:
        print("  (no year has both a *_schedule_c_initiatives.csv and a *_schedule_c_awards.csv)")
        return
    if not sidecar_present:
        print("  note: recovered/schedule_c_absorbed_awards.csv absent — 'after' columns "
              "equal the base columns")
    print(f"  {'FY':<7}{'joined':>7}{'bal':>5}{'short':>6}{'over':>5}"
          f"{'residual':>16}{'recovered':>14}{'resid after':>14}{'bal after':>10}"
          f"{'unjoined $':>16}")
    for y in years:
        resid = y["printed"] - y["awarded"]
        print(f"  FY{y['year']:<5}{len(y['rows']):>7}{y['balanced']:>5}{y['short']:>6}"
              f"{y['over']:>5}{_usd(resid):>16}{_usd(y['recovered']):>14}"
              f"{_usd(resid - y['recovered']):>14}{y['balanced_after']:>10}"
              f"{_usd(y['unjoined_amount'] + y['unlabeled_amount']):>16}")
    unbal = sum(y["short"] + y["over"] for y in years)
    print(f"  {unbal} initiative(s) do not balance; per-initiative residuals are in the report.")


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


def _initiative_recon_section(years, sidecar_present):
    """Markdown for check 8: a per-year roll-up, then every initiative that does not balance."""
    L = ["## Initiative-level award reconciliation (SOFT advisory)", ""]
    L.append("Award rows summed per initiative vs that initiative's own **printed** amount in "
             "`*_schedule_c_initiatives.csv`, joined exactly on a punctuation-folded initiative "
             "name within one fiscal year. `residual = printed - award rows`: positive is "
             "**short**, negative is **over**. This is the award stream's first pass/fail target — "
             "the per-year `*_reconciliation.txt` reconciles only the category summary and reports "
             "award rows as a bare tally with no target at all.")
    L.append("")
    L.append("Advisory, never a gate. Three known structural causes live in this residual: award "
             "rows carrying no initiative label at all, initiative labels the parser mis-assigns "
             "to a neighbouring block, and provider tables the source PDF's text layer never "
             "yielded. `unjoined $` is award dollars under a label with no printed counterpart "
             "plus dollars on rows with no label — counted here so the joined columns are not "
             "mistaken for full coverage.")
    L.append("")
    if not years:
        L.append("_No fiscal year has both an initiatives and an awards CSV._")
        L.append("")
        return L
    L.append("`recovered` is the optional sidecar `recovered/schedule_c_absorbed_awards.csv` "
             "(awards the parser absorbed into a neighbouring row and lost), included so the gap "
             "is legible with and without it. "
             + ("It is present." if sidecar_present else
                "**It is absent, so the `after` columns equal the base columns.**"))
    L.append("")
    L.append("| FY | joined | balanced | short | over | printed | award rows | residual | "
             "recovered | residual after | balanced after | unjoined $ |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for y in years:
        resid = y["printed"] - y["awarded"]
        L.append(f"| FY{y['year']} | {len(y['rows'])} | {y['balanced']} | {y['short']} | "
                 f"{y['over']} | {_usd(y['printed'])} | {_usd(y['awarded'])} | {_usd(resid)} | "
                 f"{_usd(y['recovered'])} | {_usd(resid - y['recovered'])} | "
                 f"{y['balanced_after']} | "
                 f"{_usd(y['unjoined_amount'] + y['unlabeled_amount'])} |")
    L.append("")
    L.append("Unjoined detail — dollars this check cannot test, per year:")
    L.append("")
    L.append("| FY | award labels with no printed counterpart | $ | award rows with no initiative "
             "label | $ | recovered $ not joinable |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for y in years:
        L.append(f"| FY{y['year']} | {y['unjoined_labels']} | {_usd(y['unjoined_amount'])} | "
                 f"{y['unlabeled_rows']} | {_usd(y['unlabeled_amount'])} | "
                 f"{_usd(y['recovered_unjoined'])} |")
    L.append("")
    unbal = [(y["year"], r) for y in years for r in y["rows"] if r["status"] != "balanced"]
    L.append(f"### Initiatives that do not balance ({len(unbal)})")
    L.append("")
    L.append("Balanced initiatives are omitted — their residual is $0 by definition. Sorted by "
             "fiscal year, then by the size of the residual.")
    L.append("")
    L.append("| FY | initiative | status | printed | award rows | rows | residual | recovered | "
             "residual after |")
    L.append("|---|---|---|---:|---:|---:|---:|---:|---:|")
    for year, r in sorted(unbal, key=lambda t: (t[0], -abs(t[1]["residual"]))):
        L.append(f"| FY{year} | {r['initiative']} | {r['status']} | {_usd(r['printed'])} | "
                 f"{_usd(r['awarded'])} | {r['n_awards']} | {_usd(r['residual'])} | "
                 f"{_usd(r['recovered'])} | {_usd(r['residual_after'])} |")
    L.append("")
    return L


def write_report(results, recon, surnames, md_path, data_dir, initrecon=None):
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

    if initrecon is not None:
        L.extend(_initiative_recon_section(*initrecon))

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
    ap.add_argument("--dry-run", action="store_true",
                    help="stdout only; write nothing at all (synonym of --no-report)")
    a = ap.parse_args()
    results, recon, surnames = validate_tree(a.data_dir)
    initrecon = initiative_reconciliation(a.data_dir)
    hard = print_summary(results, recon)
    print_initiative_recon(*initrecon)
    if not (a.no_report or a.dry_run):
        md_path = a.report or os.path.join(a.data_dir, "QA-REPORT.md")
        write_report(results, recon, surnames, md_path, a.data_dir, initrecon)
        print(f"\nWROTE -> {md_path}")
    raise SystemExit(1 if hard else 0)


if __name__ == "__main__":
    main()
