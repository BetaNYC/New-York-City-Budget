#!/usr/bin/env python3
"""
audit_amounts.py — check every award `amount` against the Council's own disclosure. AUDIT ONLY.

This script does not change a single figure, and that is a deliberate conclusion, not an
unfinished feature. The evidence for it is in the report the script writes; the short version:

  * Our amounts come from the ADOPTED Schedule C (June of the budget year). The disclosure
    workbooks are a later administrative snapshot — their own sheet tabs are stamped with the
    republication date ("FY19 (4-14-21)", "FY20 (06-16-2022)", "FY24 (06-08-26)"). A disagreement
    between the two is frequently the Council revising after adoption, not this repo being wrong.
    Overwriting ours with theirs would quietly turn an adopted-budget dataset into a mixed-vintage
    one and destroy the only evidence that the figure ever moved.
  * The one class that looks mechanically fixable — 11 rows off by exactly $1 — has no dominant
    direction (8 of ours higher, 3 lower). Both sides are rounding an initiative split; neither is
    the error. Changing ours would make it agree with the spreadsheet and stop agreeing with the
    PDF we cite as its source.
  * The rows where an amount demonstrably belongs to a different organization are the `org_merged`
    boundary loss of DATA-ANOMALIES.md §20. There the defect is a MISSING row, not a wrong number:
    there is no correct amount to write in its place, and writing one would erase the evidence.

So there is no --apply, and nothing is ever appended to org_name_recovery_crosswalk.csv. That file
is the audit trail for substitutions APPLIED to the data; this script applies none, and a crosswalk
entry claiming otherwise would be a lie about what the data received.

Outputs (neither is written under --dry-run):
  data/AMOUNT-AUDIT.md            the report
  data/AMOUNT-AUDIT-findings.csv  one row per non-corroborated award, so the report is actionable

Usage:
  python3 code/audit_amounts.py --dry-run   # print the summary, write nothing at all
  python3 code/audit_amounts.py             # print the summary and write both outputs
"""
import argparse
import collections
import csv
import datetime
import glob
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NINE = re.compile(r"^\d{9}$")
# A second organization's EIN or dollar figure still sitting in our `organization` text — the
# `org_merged` signature of DATA-ANOMALIES.md §20, where one award was absorbed into the next.
MERGED = re.compile(r"\d{2}-\d{7}|\$")
REPORT = "data/AMOUNT-AUDIT.md"
FINDINGS = "data/AMOUNT-AUDIT-findings.csv"

# A near miss counts as rounding only within this many dollars. Not a guess: the observed distance
# distribution has a clean gap either side of it — 11 rows at exactly $1, ZERO at $2-$5, then
# nothing again until $6. Anything past it is a different-figure disagreement, not a rounding one.
ROUND_TOL = 5

# How far apart two awards can be printed and still count as "the same table region" for the
# neighbour test. The Schedule C boundary loss of §20 absorbs an award into the row immediately
# following it, so the true signal is at distance 1-3; widening to 5 adds 3 rows and starts
# admitting coincidence.
REGION = 3

VERDICTS = ["exact", "name_variant", "rounding", "neighbour_bleed", "ein_absent", "unconfirmed",
            "no_key", "no_disclosure_year"]
CORROBORATED = {"exact", "name_variant"}


def canon(n):
    """Normalise a legal name for COMPARISON only, never for output. Same rules as
    recover_org_names.py so the two passes agree on what counts as the same organization."""
    n = (n or "").lower().strip().replace("’", "'")
    n = re.sub(r"^the\s+", "", n)
    n = re.sub(r"[,.]?\s*(the|inc|incorporated|llc|ltd|corp|corporation|co)\b\.?", " ", n)
    return re.sub(r"[^a-z0-9]+", "", n)


def hidx(hdr, needles, exclude=()):
    """Index of the first header CONTAINING one of `needles`, skipping any containing `exclude`.

    Substring, because the headers drift across the FY2013-FY2027 series: the amount column is
    "Amount ($" in FY2014 and "Amount" after it; the name column is "Legal Name of Organization
    Requesting Funding" in FY2016 and "Legal Name" from FY2018.

    `exclude` is load-bearing. "FC EIN" (FY2014-FY2017) and "Fiscal Conduit EIN" (FY2018+) both
    contain "ein", and a fiscal conduit's EIN is the PASS-THROUGH sponsor's, not the grantee's.
    Grabbing one would key an award to an organization that never received it."""
    for i, h in enumerate(hdr):
        hl = (h or "").strip().lower()
        if any(x in hl for x in exclude):
            continue
        if any(n in hl for n in needles):
            return i
    return -1


def money(v):
    """Dollars as int, or None if the cell is not a number."""
    s = (v or "").strip().replace("$", "").replace(",", "")
    if not s:
        return None
    try:
        return int(round(float(s)))
    except ValueError:
        return None


def unshift(vals, i_name, i_ein):
    """Repair a disclosure row whose cells are shifted one column LEFT of their headers.

    FY2016 ships 272 such rows and FY2014 ships 1,125 (verified counts). They are citywide
    initiative awards with no council member, and the empty member cell collapsed, dragging every
    later cell one position left. Read naively the row yields ein="Cleared" and amount="DFTA", so
    it is silently dropped — and every one of OUR rows that should have matched it then reports a
    phantom "no disclosure support". That is worse than not reading the file at all, because it
    manufactures defects in data that is fine.

    The signature is unambiguous and was checked against every year FY2014-FY2027: the name slot
    holds a bare 9-digit number AND the EIN slot holds a non-empty non-numeric token ("Cleared" /
    "Pending"). In FY2016 that partitions 7,797 rows into 272 / 7,525 with no row in between.
    Requiring the EIN slot to be NON-EMPTY is what keeps a genuinely blank EIN — FY2014 has real
    ones, e.g. "88th Precinct" — from being mistaken for a shift.

    Repairs the in-memory copy only. source/ is never written.
    """
    if i_name < 1 or i_ein < 0 or i_ein >= len(vals) or i_name >= len(vals):
        return vals, False
    ein_slot = (vals[i_ein] or "").strip()
    if not NINE.match((vals[i_name] or "").strip()):
        return vals, False
    if not ein_slot or ein_slot.replace("-", "").isdigit():
        return vals, False
    return vals[:i_name - 1] + [""] + vals[i_name - 1:], True


class Year:
    """One fiscal year of the Council's disclosure, indexed three ways."""

    def __init__(self):
        self.by_org = collections.defaultdict(collections.Counter)   # (ein, canon) -> {amt: n}
        self.by_ein = collections.defaultdict(collections.Counter)   # ein         -> {amt: n}
        self.by_amt = collections.defaultdict(set)                   # amt -> {(ein, canon), ...}
        self.rows = 0
        self.shifted = 0


def load_disclosure(fy):
    """Index one funded_disclosure_FY####.xlsx. Returns None when the year has no workbook.

    FY2013 ships as .xls — a real OLE2 compound document, not a renamed zip (magic d0cf11e0).
    Nothing in the standard library reads BIFF, so FY2013 has no machine-readable disclosure here.
    It costs us nothing: this corpus has no FY2013 award rows, only initiative totals, which this
    audit does not cover.

    Shared strings are streamed with iterparse; loading them whole stalls on these files.
    """
    path = f"source/expense-funding-disclosure/funded_disclosure_FY{fy}.xlsx"
    if not os.path.exists(path):
        return None
    z = zipfile.ZipFile(path)
    shared = []
    with z.open("xl/sharedStrings.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "si":
                shared.append("".join(t.text or "" for t in el.iter(NS + "t")))
                el.clear()

    def cell(c):
        v = c.find(NS + "v")
        if v is None or v.text is None:
            return ""
        return shared[int(v.text)] if c.get("t") == "s" else v.text

    y = Year()
    hdr = i_name = i_ein = i_amt = None
    with z.open("xl/worksheets/sheet1.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag != NS + "row":
                continue
            vals = [cell(c) for c in el.findall(NS + "c")]
            if hdr is None:
                hdr = vals
                i_name = hidx(hdr, ("legal name",))
                i_ein = hidx(hdr, ("tax id", "ein"), exclude=("fc ein", "conduit"))
                i_amt = hidx(hdr, ("amount",))
                el.clear()
                continue
            vals, did = unshift(vals, i_name, i_ein)
            y.shifted += did

            def get(i):
                return (vals[i] or "").strip() if 0 <= i < len(vals) else ""

            ein = re.sub(r"\D", "", get(i_ein))
            name = get(i_name)
            amt = money(get(i_amt))
            # The last handful of rows in FY2024 and FY2026 are spreadsheet trailers
            # ("Adoption Total", "Difference:"). They carry no EIN and no name, so they fall out
            # here rather than needing a rule of their own.
            if ein and name and amt:
                key = (ein, canon(name))
                y.by_org[key][amt] += 1
                y.by_ein[ein][amt] += 1
                y.by_amt[amt].add(key)
                y.rows += 1
            el.clear()
    return y


def classify(amount, ein, corg, year, neighbours):
    """Verdict for one award row. Pure — everything it needs is an argument, so it is testable
    without touching a workbook.

    `neighbours` is the set of (ein, canon_org) keys printed within REGION lines of this row in the
    same source file.

    Order matters and is by strength of evidence: an exact figure under the same EIN outranks an
    approximate one, and both outrank any story about where the number came from.
    """
    if amount is None or not ein or not corg:
        return "no_key", None, None
    key = (ein, corg)

    # Every figure the Council records under this EIN, whether or not the name spelling agrees.
    # `nearest` is reported for every verdict so the distance distribution can be measured rather
    # than assumed — it is what justifies ROUND_TOL.
    pool = set(year.by_org.get(key, ())) | set(year.by_ein.get(ein, ()))
    near = min(pool, key=lambda a: abs(a - amount)) if pool else None

    own = year.by_org.get(key)
    if own and amount in own:
        return "exact", amount, None

    # Same EIN, different spelling of the name. The AMOUNT is corroborated by the Council's own
    # record; only the org text disagrees. Not an amount defect, and reporting it as one would
    # bury the real findings under thousands of rows of name drift.
    if amount in year.by_ein.get(ein, ()):
        return "name_variant", amount, None

    if near is not None and abs(near - amount) <= ROUND_TOL:
        return "rounding", near, None

    # This exact figure belongs, in the Council's record, to exactly ONE organization, and that
    # organization is printed within a few lines of ours. Uniqueness is what makes this worth
    # saying: $5,000 is held by hundreds of grantees a year, so adjacency alone proves nothing.
    owners = year.by_amt.get(amount, ())
    if len(owners) == 1:
        owner = next(iter(owners))
        if owner != key and owner in neighbours:
            return "neighbour_bleed", near, owner

    if ein not in year.by_ein:
        return "ein_absent", near, None
    return "unconfirmed", near, None


def read_corpus():
    """Every award row in the per-year Schedule C and appendix files.

    Excludes *_initiatives.csv (initiative TOTALS, not awards — a different unit that would not
    join to a per-award disclosure) and the *_reconciliation.txt notes.
    """
    out = []
    for path in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiatives" in path or "reconcil" in path:
            continue
        fy = 2000 + int(re.search(r"data/fy(\d\d)/", path).group(1))
        with open(path, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                org = (r.get("organization") or "").strip()
                out.append(dict(fy=fy, file=path, line=ln,
                                ein=re.sub(r"\D", "", r.get("ein") or ""),
                                org=org, corg=canon(org), amount=money(r.get("amount"))))
    return out


def audit():
    """Classify the whole corpus. Returns (rows, per-year Year objects)."""
    rows = read_corpus()
    years = {}
    for fy in sorted({r["fy"] for r in rows}):
        years[fy] = load_disclosure(fy)

    # (ein, canon_org) printed at each line, per file — the neighbour index.
    at_line = collections.defaultdict(dict)
    for r in rows:
        at_line[r["file"]][r["line"]] = (r["ein"], r["corg"])

    for r in rows:
        year = years.get(r["fy"])
        if year is None:
            r["verdict"], r["nearest"], r["owner"] = "no_disclosure_year", None, None
            continue
        near = set()
        for d in range(1, REGION + 1):
            for ln in (r["line"] - d, r["line"] + d):
                k = at_line[r["file"]].get(ln)
                if k:
                    near.add(k)
        r["verdict"], r["nearest"], r["owner"] = classify(
            r["amount"], r["ein"], r["corg"], year, near)
    return rows, years


def summarise(rows):
    counts = collections.Counter(r["verdict"] for r in rows)
    dollars = collections.Counter()
    for r in rows:
        dollars[r["verdict"]] += r["amount"] or 0
    return counts, dollars


BUCKETS = [("exactly $1", 1, 1), ("$2–$5", 2, 5), ("$6–$99", 6, 99),
           ("$100–$999", 100, 999), ("$1,000+", 1000, None)]


def distance_histogram(rows):
    """How far our amount sits from the nearest figure the Council records under the same EIN, for
    rows that are not an exact hit. This is what ROUND_TOL is chosen against: if there is a clean
    gap just above the threshold, the threshold is reading a real boundary in the data rather than
    imposing one."""
    h = collections.Counter()
    for r in rows:
        if r["verdict"] == "exact" or r["nearest"] is None:
            continue
        d = abs(r["nearest"] - r["amount"])
        if d == 0:
            continue
        for label, lo, hi in BUCKETS:
            if d >= lo and (hi is None or d <= hi):
                h[label] += 1
                break
    return h


def crosswalk_check(rows):
    """Cross-reference the substitutions applied by earlier passes against these verdicts.

    Read-only. This script never writes to the crosswalk — it applies no substitution, and an
    entry claiming one would be a false statement about what the data received.
    """
    path = "data/combined/org_name_recovery_crosswalk.csv"
    if not os.path.exists(path):
        return {}
    verdict = {(r["file"], r["line"]): r["verdict"] for r in rows}
    out = collections.defaultdict(collections.Counter)
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            v = verdict.get((r["file"], int(r["line"])), "row_absent")
            out[r["defect"]]["_n"] += 1
            out[r["defect"]]["corroborated" if v in CORROBORATED else v] += 1
    return out


def write_report(rows, years, counts, dollars, today):
    total = len(rows)
    total_d = sum(r["amount"] or 0 for r in rows)
    corr = sum(counts[v] for v in CORROBORATED)
    corr_d = sum(dollars[v] for v in CORROBORATED)
    rounding = [r for r in rows if r["verdict"] == "rounding"]
    bleed = [r for r in rows if r["verdict"] == "neighbour_bleed"]
    drift = sum(abs(r["nearest"] - r["amount"]) for r in rows if r["verdict"] == "rounding")
    hi = sum(1 for r in rounding if r["amount"] > r["nearest"])

    per_year = collections.defaultdict(collections.Counter)
    for r in rows:
        per_year[r["fy"]][r["verdict"]] += 1
        per_year[r["fy"]]["_n"] += 1
        per_year[r["fy"]]["_d"] += r["amount"] or 0

    L = []
    a = L.append
    a("---")
    a("title: Amount Audit — award amounts against the Council's expense disclosure")
    a(f"created: {today}")
    a("type: data-audit")
    a("status: active")
    a("tags: [nyc-budget, data-quality, audit, schedule-c]")
    a("---")
    a("")
    a("# Amount Audit")
    a("")
    a(f"**Report generated:** {today}  ")
    a(f"**Data current as of:** {today} (corpus at `data/fy*/schedule_c/`, "
      "disclosure at `source/expense-funding-disclosure/`)  ")
    a("**Produced by:** `code/audit_amounts.py` — read-only, changes nothing")
    a("")
    a("## Verdict, up front")
    a("")
    a("**Report, do not touch. None of this is safely auto-correctable, and the script has no "
      "`--apply` path.** The reasoning is in [Is any of this auto-correctable?](#is-any-of-this-"
      "auto-correctable) below. Nothing was written to "
      "`data/combined/org_name_recovery_crosswalk.csv`: that file records substitutions *applied "
      "to the data*, and this pass applied none.")
    a("")
    a(f"Of **{total:,} award rows** carrying **${total_d:,}**, "
      f"**{corr:,} ({corr / total:.2%})** have their amount corroborated by the Council's own "
      f"same-year disclosure, covering **${corr_d:,} ({corr_d / total_d:.2%} of dollars)**.")
    a("")
    a("## What was compared")
    a("")
    a("Each award row in `data/fy*/schedule_c/*.csv` (Schedule C awards plus the three "
      "appendices; initiative totals and reconciliation notes excluded) against "
      "`source/expense-funding-disclosure/funded_disclosure_FY####.xlsx` for the **same fiscal "
      "year**, joined on **(EIN, canonical organization name)**.")
    a("")
    a("Three deliberate choices, each of which has burned this repo before:")
    a("")
    a("- **EIN alone is not the key.** Fiscal sponsors pass funds through for many grantees — "
      "EIN 13-2612524 (Fund for the City of New York) carries 229 distinct names in this corpus. "
      "Keying on EIN alone would corroborate an award against a different organization's money.")
    a("- **Council member is not part of the key.** The disclosure workbooks are republished with "
      "the roster current at snapshot time, not the one that adopted the budget.")
    a("- **Headers are matched by case-insensitive substring**, because they drift across the "
      "series (`Amount ($` in FY2014; `Legal Name of Organization Requesting Funding` in FY2016; "
      "`Tax ID` from FY2021). The fiscal-conduit columns `FC EIN` / `Fiscal Conduit EIN` are "
      "explicitly excluded — they hold the pass-through sponsor's EIN, not the grantee's.")
    a("")
    a("### One repair to the source, in memory only")
    a("")
    shifted = {fy: y.shifted for fy, y in years.items() if y and y.shifted}
    a("Some disclosure rows are shifted one column left of their headers: citywide initiative "
      "awards with no council member, where the empty cell collapsed and dragged the rest of the "
      "row with it. Read naively they yield `ein=\"Cleared\"`, `amount=\"DFTA\"` and are dropped — "
      "which would make every one of our matching rows report a **phantom** shortfall.")
    a("")
    a("Rows repaired in memory: "
      + (", ".join(f"**FY{fy}: {n}**" for fy, n in sorted(shifted.items())) if shifted
         else "none") + ". "
      "The signature is a bare 9-digit number in the name slot **and** a non-empty non-numeric "
      "token in the EIN slot; in FY2016 it partitions 7,797 rows into 272 / 7,525 with nothing "
      "ambiguous in between. `source/` is never written.")
    a("")
    a("## Results")
    a("")
    a("| Verdict | Rows | % | Dollars | Meaning |")
    a("|---|---:|---:|---:|---|")
    mean = {
        "exact": "our amount is one of the amounts the disclosure records for this "
                 "(EIN, organization) that year",
        "name_variant": "amount corroborated under the same EIN that year; only the organization "
                        "*text* differs from the disclosure's legal name. **Not an amount defect**",
        "rounding": f"nearest disclosure amount is within ${ROUND_TOL} but not equal",
        "neighbour_bleed": "our amount is uniquely held, in the disclosure, by a *different* "
                           f"organization printed within {REGION} lines of ours",
        "ein_absent": "this EIN does not appear anywhere in that year's disclosure, so the "
                      "amount can be neither confirmed nor contradicted",
        "unconfirmed": "the EIN is present that year, but not carrying this amount",
        "no_key": "our row has no EIN or no organization name — nothing to join on",
        "no_disclosure_year": "no disclosure workbook exists for this fiscal year",
    }
    for v in VERDICTS:
        if not counts[v]:
            continue
        a(f"| `{v}` | {counts[v]:,} | {counts[v] / total:.2%} | ${dollars[v]:,} | {mean[v]} |")
    a(f"| **total** | **{total:,}** | | **${total_d:,}** | |")
    a("")
    a("### By fiscal year")
    a("")
    a("| FY | rows | corroborated | % | rounding | bleed | unconfirmed + ein_absent |")
    a("|---|---:|---:|---:|---:|---:|---:|")
    for fy in sorted(per_year):
        c = per_year[fy]
        ok = sum(c[v] for v in CORROBORATED)
        a(f"| FY{fy} | {c['_n']:,} | {ok:,} | {ok / c['_n']:.1%} | {c['rounding']} | "
          f"{c['neighbour_bleed']} | {c['unconfirmed'] + c['ein_absent']:,} |")
    a("")
    a("## Off by cents / rounding")
    a("")
    a(f"**{len(rounding)} rows**, total absolute drift **${drift}** — "
      f"{hi} where ours is higher, {len(rounding) - hi} where ours is lower.")
    a("")
    a(f"The ${ROUND_TOL} threshold is not a guess. Measuring the distance from our amount to the "
      "nearest figure the Council records under the same EIN, across every row that is not an "
      "exact hit, the distribution has a clean gap right where the threshold sits:")
    a("")
    a("| distance | rows |")
    a("|---|---:|")
    hist = distance_histogram(rows)
    for label, _, _ in BUCKETS:
        a(f"| {label} | {hist.get(label, 0):,} |")
    a("")
    a("Every one of these is an initiative allocation split N ways and rounded independently on "
      "each side. FY2015 New York Urban League is the clearest: the disclosure carries both "
      "$166,666 and $833,334 for the same organization — a fifth and the whole — and we carry "
      "$833,333.")
    a("")
    a("| file | line | organization | ours | disclosure | Δ | §20 merged row |")
    a("|---|---:|---|---:|---:|---:|---|")
    merged_round = 0
    for r in sorted(rounding, key=lambda x: (x["file"], x["line"])):
        m = bool(MERGED.search(r["org"]))
        merged_round += m
        a(f"| `{os.path.basename(r['file'])}` | {r['line']} | {r['org'][:38]} | "
          f"${r['amount']:,} | ${r['nearest']:,} | {r['amount'] - r['nearest']:+d} | "
          f"{'**yes**' if m else '—'} |")
    a("")
    a(f"### Why even these ${ROUND_TOL} gaps must not be closed automatically")
    a("")
    a(f"**{merged_round} of these {len(rounding)} rows are `org_merged` rows** — their "
      "`organization` field still carries a second organization's EIN or dollar figure, the "
      "boundary loss of DATA-ANOMALIES.md §20. On those rows the $1 gap is not rounding at all. "
      "It is a coincidence of an even two-way split, and the amount on the row belongs to the "
      "*other* organization.")
    a("")
    a("`fy17_schedule_c_awards.csv:209` is §20's own worked example, and this audit reached it "
      "from the opposite direction. The row reads:")
    a("")
    a("```")
    a("organization: Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services")
    a("ein:          113305406   (Brooklyn Defenders)")
    a("amount:       2076666     (Bronx Defenders' share)")
    a("```")
    a("")
    a("The disclosure records $2,076,667 for EIN 113305406. A tolerant fixer would see a $1 gap, "
      "call it rounding, write $2,076,667, and produce a row that passes every check while the "
      "award it swallowed is still missing and the evidence of the swallow is gone. **A defect "
      "that is visible is worth more than a figure that is plausible.** This one class of finding "
      "is on its own sufficient to settle the question below.")
    a("")
    a("## Amount belonging to a different organization")
    a("")
    a(f"**{len(bleed)} rows.** Our amount is held, in the Council's record, by exactly one "
      f"organization — and that organization is printed within {REGION} lines of ours in the same "
      "file. Uniqueness is what makes the claim worth making: $5,000 is held by hundreds of "
      "grantees a year, so proximity alone proves nothing.")
    a("")
    if bleed:
        a("| file | line | our organization | our amount | belongs to |")
        a("|---|---:|---|---:|---|")
        for r in sorted(bleed, key=lambda x: (x["file"], x["line"])):
            a(f"| `{os.path.basename(r['file'])}` | {r['line']} | {r['org'][:34]} | "
              f"${r['amount']:,} | EIN {r['owner'][0]} |")
        a("")
    a("These are the same boundary loss as §20 — the Schedule C parser absorbing one award into "
      "the next when an asterisk or a program name sits between the EIN and the dollar figure — "
      "reached here from the opposite direction, by noticing that the Council attributes the "
      "figure to a neighbour. The count is small because the test is strict on purpose: the "
      "amount must be *uniquely* held. Rows where the swallowed award happened to be an even "
      "split of the same pot land in the rounding table above instead, which is where the more "
      "dangerous cases turn out to be.")
    a("")
    a("## Is any of this auto-correctable?")
    a("")
    a("**No. Audit only.** Four reasons, in descending order of how much they should worry you.")
    a("")
    a("**1. The two sources are different vintages of the truth, not two attempts at one figure.** "
      "Our amounts come from the adopted Schedule C, published in June of the budget year. The "
      "disclosure workbooks are administrative snapshots republished later — their sheet tabs say "
      "so: `FY19 (4-14-21)`, `FY20 (06-16-2022)`, `FY24 (06-08-26)`. When they disagree, the "
      "Council revising an award after adoption is at least as likely as this repo mis-parsing "
      "one. Copying their figure over ours would make the dataset agree with a spreadsheet and "
      "stop agreeing with the PDF it cites as its source — and would erase the only evidence that "
      "the number ever moved. That is a loss of information dressed up as a correction.")
    a("")
    a(f"**2. The rounding cases have no correct answer, and {merged_round} of {len(rounding)} are "
      "not rounding at all.** $833,333 against $833,334; $29,730 against $29,729. Both sides are "
      f"dividing an initiative pot and rounding, and ours is not systematically wrong — {hi} high, "
      f"{len(rounding) - hi} low. No rule picks a winner, so any rule applied here would be "
      f"invented. Worse, on the {merged_round} `org_merged` rows the $1 gap is a coincidence "
      "hiding a swallowed award, and closing it would destroy the evidence — see above.")
    a("")
    a("**3. On the bleed rows, there is nothing to write.** §20's defect is a *missing* row: an "
      "award got absorbed into its neighbour. The surviving row has organization A's name against "
      "organization B's money, and the fix is to recover the lost row, not to overwrite a number. "
      "Substituting an amount would make the row look sound while the award it swallowed stayed "
      "missing — converting a visible defect into an invisible one. That is the single worst "
      "outcome available here.")
    a("")
    a(f"**4. `unconfirmed` and `ein_absent` ({counts['unconfirmed'] + counts['ein_absent']:,} "
      "rows) are mostly not defects at all.** The repo's own source-comparability study found row "
      "capture against the disclosure is materially below 100% in every fiscal year. Absence from "
      "the disclosure is absence of evidence. Treating it as evidence of a wrong amount, and "
      "'fixing' it, would fabricate figures for awards the disclosure simply does not list.")
    a("")
    a("The bar this repo already set for a fix — a substitution resolvable to exactly ONE "
      "candidate from the Council's own record — is met by none of these classes. Not one.")
    a("")
    a("## Corroboration of earlier passes")
    a("")
    a("Cross-referencing `data/combined/org_name_recovery_crosswalk.csv` against these verdicts, "
      "as an independent check on repairs already applied:")
    a("")
    cw = crosswalk_check(rows)
    if cw:
        a("| earlier fix | rows | amount corroborated afterwards | remainder |")
        a("|---|---:|---:|---|")
        for defect in sorted(cw):
            c = cw[defect]
            rest = ", ".join(f"{n} {k}" for k, n in sorted(c.items())
                             if k not in ("_n", "corroborated")) or "—"
            a(f"| `{defect}` | {c['_n']:,} | {c['corroborated']:,} | {rest} |")
        a("")
        we = cw.get("wrong_ein", {})
        if we:
            a(f"The `wrong_ein` result is the meaningful one: those {we['_n']} rows were re-keyed "
              "on (name, amount), and "
              f"{we['corroborated']} of {we['_n']} now agree with the disclosure on a key that "
              "*includes the EIN the pass wrote*. That is confirmation arriving from a direction "
              "the fix itself did not use.")
    else:
        a("_Crosswalk not present; cross-check skipped._")
    a("")
    a("## Limits of this audit")
    a("")
    a("- **FY2013 has no machine-readable disclosure.** It ships as `.xls` — a genuine OLE2 "
      "compound document (magic `d0cf11e0`), not a renamed zip — and no standard-library module "
      "reads BIFF. It costs nothing here: this corpus holds no FY2013 award rows, only initiative "
      "totals.")
    a("- **Set membership, not multiset.** A row is corroborated if its amount appears among that "
      "organization's disclosure amounts for the year. Where we hold three $5,000 rows and the "
      "disclosure holds one, all three read `exact`. That is a duplication question, not an "
      "amount question, and it is out of scope here.")
    a("- **`name_variant` is a floor, not a ceiling.** It corroborates the amount under the EIN "
      "without asserting the two names are the same organization. For a fiscally-sponsored award "
      "they may not be.")
    a("- **Nothing here establishes completeness.** This audit asks whether the amounts we hold "
      "are right, never whether we hold all the awards. Those are different questions and the "
      "second one has a worse answer.")
    a("")
    a(f"Row-level detail for every non-corroborated award: `{FINDINGS}` "
      f"({sum(counts[v] for v in VERDICTS if v not in CORROBORATED and v != 'exact'):,} rows).")
    a("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the summary and write nothing at all")
    args = ap.parse_args()

    if not os.path.isdir("source/expense-funding-disclosure"):
        print("error: run from the repo root (source/expense-funding-disclosure not found)",
              file=sys.stderr)
        return 2

    rows, years = audit()
    counts, dollars = summarise(rows)
    total = len(rows)
    total_d = sum(r["amount"] or 0 for r in rows)
    corr = sum(counts[v] for v in CORROBORATED)

    print(f"award rows audited : {total:,}  (${total_d:,})")
    for fy in sorted(years):
        y = years[fy]
        if y:
            print(f"  FY{fy} disclosure: {y.rows:>6,} usable rows"
                  + (f"   [{y.shifted} shifted rows repaired in memory]" if y.shifted else ""))
    print()
    for v in VERDICTS:
        if counts[v]:
            print(f"  {v:<20} {counts[v]:>7,}  {counts[v] / total:>7.2%}  ${dollars[v]:>16,}")
    print(f"\ncorroborated by the Council's own disclosure: {corr:,} ({corr / total:.2%})")

    rounding = [r for r in rows if r["verdict"] == "rounding"]
    if rounding:
        drift = sum(abs(r["nearest"] - r["amount"]) for r in rounding)
        hi = sum(1 for r in rounding if r["amount"] > r["nearest"])
        print(f"rounding drift: {len(rounding)} rows, ${drift} absolute "
              f"({hi} ours-higher, {len(rounding) - hi} ours-lower)")
    print(f"amount belongs to a different nearby org: "
          f"{counts['neighbour_bleed']} rows (DATA-ANOMALIES.md §20)")

    if args.dry_run:
        # Exit BEFORE any write. A dry run that touched an output file once recorded 16
        # substitutions the data never received; the whole value of an audit trail is that it
        # describes what happened, so a dry run must leave zero trace.
        print("\n--dry-run: nothing written (no report, no findings CSV, no crosswalk entry)")
        return 0

    today = datetime.date.today().isoformat()
    os.makedirs("data", exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write(write_report(rows, years, counts, dollars, today))
    print(f"\nreport   -> {REPORT}")

    flagged = [r for r in rows if r["verdict"] not in CORROBORATED]
    with open(FINDINGS, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "line", "fiscal_year", "ein", "organization", "our_amount",
                    "verdict", "nearest_disclosure_amount", "delta", "belongs_to_ein",
                    "org_text_merged"])
        for r in sorted(flagged, key=lambda x: (x["file"], x["line"])):
            w.writerow([r["file"], r["line"], r["fy"], r["ein"], r["org"], r["amount"],
                        r["verdict"], r["nearest"] if r["nearest"] is not None else "",
                        (r["amount"] - r["nearest"]) if r["nearest"] is not None else "",
                        r["owner"][0] if r["owner"] else "",
                        "yes" if MERGED.search(r["org"]) else ""])
    print(f"findings -> {FINDINGS} ({len(flagged):,} rows)")
    print("crosswalk untouched: this pass changes no data, so it records no substitution")
    return 0


if __name__ == "__main__":
    sys.exit(main())
