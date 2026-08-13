#!/usr/bin/env python3
"""
prototype_recover_absorbed.py — can the awards ABSORBED into a merged row be recovered?

PROTOTYPE. Read-only: writes one CSV under research/missing-absorbed-awards/ and prints a
report. It does not touch data/, and it is not wired into the build.

The defect: the Schedule C parser finds an award by an EIN followed by an amount. Where the PDF
prints an asterisk, a program name, or a CASA school between them, the pattern misses, and that
award's text is ABSORBED into the `organization` field of the next row that does match:

    ein 113305406  amount 2,076,666
    organization  "Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services"
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ an award with no row of its own

This script pulls those absorbed (name, EIN, amount) triples back out and asks whether the
Council's own expense disclosure workbooks can confirm and complete them.

Method deliberately mirrors code/recover_org_names.py, which recovered 1,060 lost grantee names
the same way, INCLUDING its central key choice: (EIN, amount), never EIN alone. Fiscal sponsors
pass funds through for many grantees -- EIN 13-2612524 carries 229 distinct names in this corpus
-- so EIN alone would stamp the sponsor's name onto an award that went somewhere else.

ONE DELIBERATE DEPARTURE, and it matters. recover_org_names.py reads each xlsx row as
    dict(zip(header, [cv(c) for c in row.findall('c')])),
which assumes every row emits a cell for every column. Excel OMITS empty cells, so any row with a
blank in the middle shifts every later column one to the left. Measured cost: FY2014 loses 210 of
2,245 (EIN, amount) keys and FY2016 loses 248 of 5,867; every other workbook is unaffected. On this
task the fix moves 9 absorbed awards from "no same-year match" to "unambiguous same-year match".
read_workbook() below maps each cell by its `r` attribute (A1, C1, ...) instead. `--naive-reader`
reproduces the old behavior for comparison; it writes to a SEPARATE CSV so a comparison run cannot
be mistaken for the real result.

Usage:
  python3 code/prototype_recover_absorbed.py
  python3 code/prototype_recover_absorbed.py --naive-reader   # show what the sparse-cell bug costs
"""
import argparse
import csv
import glob
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
OUT = "research/missing-absorbed-awards/absorbed_award_candidates.csv"

# The validator's org_merged trigger, reproduced exactly (code/validate_data.py:353) so this
# script operates on the same 303 rows and no others.
EIN_IN_TEXT = re.compile(r"\d{2}-\d{7}")

# An EIN as it survives in absorbed text: hyphenated in the Schedule C body, bare 9 digits in the
# FY18 Appendix A stream. Negative lookarounds keep it off longer digit runs.
ANY_EIN = re.compile(r"(?<![\d-])(\d{2}-\d{7}|\d{9})(?![\d-])")
AMT = re.compile(r"\$\s?([\d,]+(?:\.\d{2})?)")

# Distance from the end of an EIN to the start of the amount that belongs to it. Measured on all
# 303 rows: 442 of 445 pairs sit at 0-9 characters ("* "), and 3 at 20-29 (a CASA school name).
# Beyond that the next dollar sign belongs to a different award, so the pair is not asserted.
# ponytail: a flat character budget, not a grammar. Raise it only against a measured histogram.
MAX_EIN_AMT_GAP = 40

# Disclosure column names drift year to year. Each of our schema fields maps to the first header
# present in a given workbook.
COLMAP = {
    "organization": ["Legal Name", "Legal Name of Organization",
                     "Legal Name of Organization Requesting Funding"],
    "ein":          ["Tax ID", "EIN"],
    "amount":       ["Amount"],
    "member":       ["Council Member", "Council Members"],
    "program":      ["Program Name"],
    "agency":       ["Agency"],
    "purpose":      ["Purpose of Funds", "CM Purpose of Funds",
                     "Purpose to be listed in Schedule C"],
    "source":       ["Source"],
    "status":       ["Status"],
}


def colidx(ref):
    """'AB12' -> 27. Excel column letters are base-26 with no zero."""
    n = 0
    for ch in re.match(r"([A-Z]+)", ref).group(1):
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_workbook(path, naive=False):
    """Yield each data row as {our_field: value}. Shared strings are streamed; loading them whole
    stalls on these files."""
    z = zipfile.ZipFile(path)
    shared = []
    with z.open("xl/sharedStrings.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "si":
                shared.append("".join(t.text or "" for t in el.iter(NS + "t")))
                el.clear()

    def cv(c):
        v = c.find(NS + "v")
        if v is None or v.text is None:
            return ""
        return shared[int(v.text)] if c.get("t") == "s" else v.text

    hdr, pick = None, {}
    with z.open("xl/worksheets/sheet1.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag != NS + "row":
                continue
            cells = el.findall(NS + "c")
            if hdr is None:
                hdr = [cv(c) for c in cells]
                pick = {k: next((h for h in names if h in hdr), None)
                        for k, names in COLMAP.items()}
                el.clear()
                continue
            if naive:
                vals = [cv(c) for c in cells]
            else:
                vals = [""] * len(hdr)
                for c in cells:
                    i = colidx(c.get("r"))
                    if i < len(hdr):
                        vals[i] = cv(c)
            d = dict(zip(hdr, vals))
            el.clear()
            yield {k: (d.get(h) or "").strip() if h else "" for k, h in pick.items()}


def norm_ein(v):
    return re.sub(r"\D", "", v or "")


def to_amt(v):
    try:
        return int(round(float(str(v).replace(",", "").replace("$", "") or 0)))
    except (TypeError, ValueError):
        return None


def load_disclosure(naive=False):
    """(fy, ein, amount) -> [disclosure row], plus the same index ignoring fy."""
    by_year, any_year = defaultdict(list), defaultdict(list)
    for p in sorted(glob.glob("source/expense-funding-disclosure/funded_disclosure_FY*.xlsx")):
        fy = "FY" + re.search(r"FY(\d{4})", p).group(1)[2:]
        for d in read_workbook(p, naive):
            ein, amt = norm_ein(d["ein"]), to_amt(d["amount"])
            if len(ein) != 9 or amt is None:
                continue
            d["fy"] = fy
            by_year[(fy, ein, amt)].append(d)
            any_year[(ein, amt)].append(d)
    return by_year, any_year


def merged_rows():
    """The org_merged population: every award row whose `organization` carries an EIN or a '$'."""
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiatives" in f or "reconcil" in f:
            continue
        fy = "FY" + re.search(r"/fy(\d\d)/", f).group(1)
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                org = r.get("organization") or ""
                if EIN_IN_TEXT.search(org) or "$" in org:
                    yield f, fy, ln, r


def absorbed(org):
    """Pull (name, ein, amount) out of an absorbed organization string.

    The name is whatever text precedes the EIN since the previous award ended. It is only a hint:
    disclosure supplies the authoritative legal name, so a ragged name here costs nothing."""
    out, prev = [], 0
    for m in ANY_EIN.finditer(org):
        nxt = AMT.search(org, m.end())
        if not nxt or nxt.start() - m.end() > MAX_EIN_AMT_GAP:
            continue  # a fiscal-conduit EIN, or a $ belonging to a later award
        # Leading ".00" is the cents tail of the PREVIOUS award's amount, split across the join.
        name = re.sub(r"^\.\d*\s*", "", org[prev:m.start()].strip(" *,"))
        out.append((name, norm_ein(m.group(1)), to_amt(nxt.group(1))))
        prev = nxt.end()
    return out


def corpus_keys():
    """(fy, ein, amount) already carrying a row of its own, so we do not 'recover' a duplicate."""
    keys = set()
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiatives" in f or "reconcil" in f:
            continue
        fy = "FY" + re.search(r"/fy(\d\d)/", f).group(1)
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                ein, amt = norm_ein(r.get("ein")), to_amt(r.get("amount"))
                if len(ein) == 9 and amt is not None:
                    keys.add((fy, ein, amt))
    return keys


FIELDS = ["category", "initiative", "award_type", "member", "organization",
          "program", "ein", "amount", "agency", "purpose"]

# Confidence tiers. The dividing line is not "did we find a row" but "does the row we found
# identify ONE award". B is separated from A because when several disclosure rows share an EIN,
# an amount and a legal name, they are still different awards from different members for
# different purposes -- measured: those candidate sets disagree on purpose 19/32 and on member
# 16/32 -- so only the fields they agree on may be carried over.
TIERS = {
    ("unique", "same_fy"):         ("A", "one same-year disclosure row: every field it carries is unambiguous"),
    ("unique_by_name", "same_fy"): ("B", "several same-year rows, one legal name: name and agency safe, member/program/purpose are not"),
    ("unique", "any_fy"):          ("C", "no same-year row; matched only by pooling all years"),
    ("unique_by_name", "any_fy"):  ("C", "no same-year row; matched only by pooling all years"),
    ("ambiguous", "any_fy"):       ("C", "more than one distinct legal name at this EIN and amount"),
    ("ambiguous", "same_fy"):      ("C", "more than one distinct legal name at this EIN and amount"),
    ("absent", "none"):            ("D", "no disclosure row at this EIN and amount in any year"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--naive-reader", action="store_true",
                    help="read xlsx the way recover_org_names.py does, to price the sparse-cell bug")
    args = ap.parse_args()

    by_year, any_year = load_disclosure(args.naive_reader)
    print(f"disclosure keys: {len(by_year):,} (fy,ein,amount) / {len(any_year):,} (ein,amount)")
    have = corpus_keys()
    print(f"corpus keys    : {len(have):,} (fy,ein,amount) already have a row")

    rows, tally, retained = [], Counter(), Counter()
    no_triple = []
    for f, fy, ln, r in merged_rows():
        tally["merged_rows"] += 1

        # Sanity anchor: is the RETAINED row's own (ein, amount) in disclosure? The established
        # figure is 248 of 303 confirmed, 55 absent and all FY2016.
        rk = (fy, norm_ein(r.get("ein")), to_amt(r.get("amount")))
        retained["confirmed" if rk in by_year else f"absent_{fy}"] += 1

        trips = absorbed(r.get("organization") or "")
        if not trips:
            no_triple.append((f, ln, (r.get("organization") or "")[:100]))
            continue
        for name, ein, amt in trips:
            tally["absorbed_triples"] += 1
            cands = by_year.get((fy, ein, amt), [])
            scope = "same_fy"
            if not cands:
                cands = any_year.get((ein, amt), [])
                scope = "any_fy" if cands else "none"
            if len(cands) == 1:
                verdict = "unique"
            elif len(cands) > 1:
                verdict = "ambiguous" if len({c["organization"] for c in cands}) > 1 \
                          else "unique_by_name"
            else:
                verdict = "absent"
            dup = (fy, ein, amt) in have
            tally[f"{verdict}|{scope}"] += 1
            tally["already_in_corpus" if dup else "genuinely_missing"] += 1

            d = cands[0] if cands else {}
            tier, _ = TIERS[(verdict, scope)]
            # Fields the whole candidate set agrees on may be carried over; the rest must be blank.
            agreed = {k: d.get(k, "") for k in
                      ("organization", "member", "program", "agency", "purpose", "source")
                      if cands and len({c.get(k, "") for c in cands}) == 1}
            rows.append(dict(
                fy=fy, tier=tier, absorbing_file=f, absorbing_line=ln,
                absorbing_ein=r.get("ein"), absorbing_amount=r.get("amount"),
                absorbing_category=r.get("category", ""), absorbing_initiative=r.get("initiative", ""),
                absorbing_award_type=r.get("award_type", ""),
                extracted_name=name, ein=ein, amount=amt,
                verdict=verdict, scope=scope, n_candidates=len(cands),
                already_in_corpus=int(dup),
                d_organization=agreed.get("organization", ""), d_member=agreed.get("member", ""),
                d_program=agreed.get("program", ""), d_agency=agreed.get("agency", ""),
                d_purpose=agreed.get("purpose", ""), d_source=agreed.get("source", ""),
                d_status=d.get("status", ""), d_fy=d.get("fy", ""),
                first_candidate_name=d.get("organization", ""),
            ))

    # --naive-reader writes elsewhere: it is a comparison run, and clobbering the real output with
    # it silently poisons any downstream analysis.
    out = OUT if not args.naive_reader else OUT.replace(".csv", "_NAIVEREADER.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    print(f"\nretained rows (the 303 themselves): {dict(retained)}")
    print(f"merged rows yielding no triple: {len(no_triple)}")
    for f, ln, o in no_triple:
        print(f"    {f}:{ln} {o!r}")
    print(f"\nabsorbed triples extracted: {n}")
    for k in sorted(k for k in tally if "|" in k):
        print(f"  {k:26} {tally[k]:>4}  ({tally[k]/n:6.1%})")
    print(f"  {'already have a row':26} {tally['already_in_corpus']:>4}")
    print(f"  {'genuinely missing':26} {tally['genuinely_missing']:>4}")

    print("\nconfidence tiers:")
    for t in "ABCD":
        sub = [r for r in rows if r["tier"] == t]
        if sub:
            print(f"  {t}  {len(sub):>4}  ({len(sub)/n:5.1%})  ${sum(r['amount'] for r in sub):>13,}"
                  f"   {TIERS[(sub[0]['verdict'], sub[0]['scope'])][1]}")

    supply = {"organization": "d_organization", "member": "d_member", "program": "d_program",
              "agency": "d_agency", "purpose": "d_purpose", "ein": "ein", "amount": "amount"}
    print("\nper-field fill rate, by tier (share of rows where disclosure supplies a value all "
          "candidates agree on):")
    print(f"  {'field':14} " + "".join(f"{'tier '+t:>12}" for t in "ABC"))
    for field in FIELDS + ["[Source]"]:
        src = supply.get(field, "d_source" if field == "[Source]" else None)
        if not src:
            print(f"  {field:14} " + f"{'--- absent from disclosure in any form ---':>36}")
            continue
        cells = ""
        for t in "ABC":
            sub = [r for r in rows if r["tier"] == t]
            f_ = sum(1 for r in sub if str(r[src]).strip())
            cells += f"{f_/len(sub):11.1%} " if sub else f"{'-':>12}"
        print(f"  {field:14} " + cells)
    print(f"\nwrote {out}")
    return 0


def demo():
    """One runnable check: the absorbed-triple parser on the four text shapes actually observed.
    If MAX_EIN_AMT_GAP or the regexes drift, this fails."""
    # asterisk between EIN and amount (FY16-FY20 Schedule C body)
    assert absorbed("Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services") == \
        [("Bronx Defenders", "133931074", 2076667)]
    # several in one string, names carried forward correctly
    assert absorbed("A 11-1111111 * $10 B 22-2222222 * $20 C") == \
        [("A", "111111111", 10), ("B", "222222222", 20)]
    # bare 9-digit EIN and cents (FY18 Appendix A)
    assert absorbed("Menchaca Asian Community United Society Inc. 264164117 * $10,000.00 To cover") == \
        [("Menchaca Asian Community United Society Inc.", "264164117", 10000)]
    # a CASA school name between EIN and amount
    assert absorbed("East Flatbush Village, Inc. 80-0612019 Meyer Levin High School $18,000 Afro") == \
        [("East Flatbush Village, Inc.", "800612019", 18000)]
    # a fiscal-conduit EIN with no amount of its own must NOT become an award
    assert absorbed("Seabreeze Jewish Center 112164803 * $3,000.00 Funds for x. "
                    "JCC of Greater Coney Island 112665181 Search and Care, Inc.") == \
        [("Seabreeze Jewish Center", "112164803", 3000)]
    # purpose prose that merely mentions a dollar figure is not an award
    assert absorbed("The funds requested will subsidize farm shares to $12 per share. Council For Unity") == []
    print("demo ok")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        sys.exit(main())
