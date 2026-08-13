#!/usr/bin/env python3
"""
verify_amounts_against_pdf.py -- settle the amounts the disclosure could not corroborate.

`audit_amounts.py` compares our amounts to the Council's expense-funding *disclosure workbooks*,
and leaves 440 rows unresolved: 419 `ein_absent`, 18 `rounding`, 3 `neighbour_bleed`. Issue #57
calls those a release blocker and proposes inspecting them by hand.

The disclosure is not the only witness, and it is not even the authoritative one. Our amounts come
from the adopted Schedule C PDF, which this repo ships in `source/` and cites as its source. The
disclosure is a later administrative snapshot -- AMOUNT-AUDIT.md's own reasoning for never copying
a figure from it. So a row the disclosure cannot speak to is not unverifiable; it is verifiable
against the document it actually came from.

WHY THIS IS EVIDENCE AND NOT A RE-RUN OF THE PARSER

`parse_schedule_c.py` reads the PDF with **pypdf** (`extract_text()`). This script reads it with
**pdftotext -layout** (poppler) -- a different engine, a different text model, run over the same
bytes. When both put our amount on the same printed line as our EIN, that is two independent
readings agreeing, not one reading checked against itself.

"OUR AMOUNT IS SOMEWHERE UNDER THIS EIN" IS NOT ENOUGH

A first version accepted any line carrying the EIN and the amount, and confirmed all 440 rows. It
was measured against a control that rotates each year's amounts onto neighbouring rows -- so every
wrong amount is a *real* amount printed in that same PDF, which is the neighbour-bleed failure mode
exactly. **14.1% of deliberately-wrong rows still confirmed.** The cause is in the data: one EIN is
printed on 483 separate lines of a single year (a fiscal sponsor -- see AMOUNT-AUDIT.md on EIN
13-2612524 carrying 229 names). Against 483 lines, "the amount appears on one of them" is nearly
free.

So a confirmation must identify ONE line, not a set:

  pdf_confirms       the amount is on a line carrying this EIN, AND either that EIN is printed on
                     exactly one line all year, or that same line also carries our organization
                     name -- so the evidence points at one printed row, not at an EIN's whole block
  pdf_confirms_weak  the amount is under the EIN, but among several lines and none names our
                     organization. Corroborated but not pinned; a person should look
  pdf_contradicts    the EIN is printed, and no line under it carries our amount
  pdf_ein_absent     the EIN appears nowhere in that year's PDF
  pdf_no_source      no Schedule C PDF mapped for that fiscal year

NOTHING IS WRITTEN TO THE DATA. This script has no --apply path and must never get one -- the same
rule `audit_amounts.py` follows, for the same reason: when two vintages of the truth disagree, the
disagreement is the finding.

Usage:  python3 code/verify_amounts_against_pdf.py [--out data/AMOUNT-PDF-VERIFICATION.csv]
"""
import argparse
import csv
import os
import re
import subprocess
import sys

FINDINGS = "data/AMOUNT-AUDIT-findings.csv"
TARGET_VERDICTS = ("ein_absent", "rounding", "neighbour_bleed")
CACHE = "build/pdftext"

# Fiscal year -> adopted Schedule C PDF. Taken from the parser's own test files
# (code/test_parse_schedule_c*.py), which pin each year to its source document, so this mapping is
# not an independent guess about which PDF is authoritative for a year.
PDFS = {
    2015: "source/FY15/fy2015-FY15-Schedule-C-Template-Final.pdf",
    2016: "source/FY16/fy2016-skedcf.pdf",
    2017: "source/FY17/FY17-Schedule-C.pdf",
    2018: "source/FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf",
    2019: "source/FY19/Fiscal-2019-Schedule-C-Final-Report.pdf",
    2020: "source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf",
    2021: "source/FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf",
    2022: "source/FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf",
    2023: "source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf",
    2024: "source/FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf",
    2025: "source/FY25/Fiscal-2025-Schedule-C-MERGE-FINAL-2.pdf",
    2026: "source/FY26/Fiscal-2026-Schedule-C-4.pdf",
    2027: "source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf",
}

MONEY = re.compile(r"\$\s?([\d,]+)")


def pdf_lines(fy):
    """Every line of that year's Schedule C, via poppler. Cached; the PDFs do not change."""
    src = PDFS.get(fy)
    if not src or not os.path.exists(src):
        return None
    os.makedirs(CACHE, exist_ok=True)
    txt = os.path.join(CACHE, f"fy{fy}.layout.txt")
    if not os.path.exists(txt):
        # -layout keeps the printed row intact, which is the whole point: a human "checking against
        # the PDF" is reading the line, not the reading order.
        subprocess.run(["pdftotext", "-layout", src, txt], check=True)
    with open(txt, encoding="utf-8", errors="replace") as fh:
        return fh.read().splitlines()


def ein_index(lines):
    """9-digit EIN -> [(line_no, text)]. The PDF prints `13-3780848`; our CSVs store `133780848`."""
    idx = {}
    for n, line in enumerate(lines, start=1):
        for m in re.finditer(r"\b(\d{2})-?(\d{7})\b", line):
            idx.setdefault(m.group(1) + m.group(2), []).append((n, line))
    return idx


def amounts_on(line):
    return {int(m.group(1).replace(",", "")) for m in MONEY.finditer(line)}


def canon(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def names_us(line, org):
    """Does this printed line carry our organization?

    Substring, because -layout wraps a neighbouring column onto the front of a row: FY2027's
    Selfhelp line reads 'Lee Selfhelp Community Services...'. 18 canonical characters is long
    enough that a collision would have to be a near-identical name.
    """
    c = canon(org)[:18]
    return bool(c) and c in canon(line)


def verify(rows):
    out = []
    by_year = {}
    for r in rows:
        by_year.setdefault(int(r["fiscal_year"]), []).append(r)

    for fy in sorted(by_year):
        lines = pdf_lines(fy)
        if lines is None:
            for r in by_year[fy]:
                out.append(dict(r, pdf_verdict="pdf_no_source", pdf_line="", pdf_amounts="",
                                pdf_ein_lines=0, pdf_text=""))
            continue
        idx = ein_index(lines)
        for r in by_year[fy]:
            ein = re.sub(r"\D", "", r["ein"] or "")
            try:
                ours = int(float(r["our_amount"] or 0))
            except (TypeError, ValueError):
                ours = None
            hits = idx.get(ein, [])
            if not hits:
                out.append(dict(r, pdf_verdict="pdf_ein_absent", pdf_line="", pdf_amounts="",
                                pdf_ein_lines=0, pdf_text=""))
                continue
            carrying = [(n, t) for n, t in hits if ours in amounts_on(t)]
            if carrying:
                # Prefer a line that also names us; that is what pins the match to one printed row.
                named = next(((n, t) for n, t in carrying if names_us(t, r["organization"])), None)
                n, t = named or carrying[0]
                pinned = named is not None or len(hits) == 1
                out.append(dict(r, pdf_verdict="pdf_confirms" if pinned else "pdf_confirms_weak",
                                pdf_line=n, pdf_amounts=ours,
                                pdf_ein_lines=len(hits), pdf_text=" ".join(t.split())[:160]))
            else:
                n, t = hits[0]
                seen = sorted({a for _, tx in hits for a in amounts_on(tx)})
                out.append(dict(r, pdf_verdict="pdf_contradicts", pdf_line=n,
                                pdf_amounts=";".join(str(a) for a in seen),
                                pdf_ein_lines=len(hits), pdf_text=" ".join(t.split())[:160]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/AMOUNT-PDF-VERIFICATION.csv")
    args = ap.parse_args()

    if not os.path.exists(FINDINGS):
        print(f"missing {FINDINGS} -- run code/audit_amounts.py first", file=sys.stderr)
        return 1
    rows = [r for r in csv.DictReader(open(FINDINGS, encoding="utf-8"))
            if r["verdict"] in TARGET_VERDICTS]
    print(f"rows the disclosure could not corroborate: {len(rows)}")

    res = verify(rows)
    tally, dollars = {}, {}
    for r in res:
        v = r["pdf_verdict"]
        tally[v] = tally.get(v, 0) + 1
        dollars[v] = dollars.get(v, 0) + int(float(r["our_amount"] or 0))

    print("\nagainst the adopted Schedule C PDF (poppler; parser uses pypdf):")
    for v in sorted(tally, key=lambda k: -tally[k]):
        print(f"  {v:<18} {tally[v]:>4}   ${dollars[v]:,}")

    need = [r for r in res if r["pdf_verdict"] != "pdf_confirms"]
    print(f"\nstill needing a human: {len(need)} of {len(rows)}")
    for r in need[:12]:
        print(f"  [{r['pdf_verdict']}] {r['file'].split('/')[1]}:{r['line']} "
              f"{r['organization'][:34]!r} ours=${int(float(r['our_amount'])):,}"
              f"{'  pdf=' + str(r['pdf_amounts']) if r['pdf_amounts'] else ''}")
    if len(need) > 12:
        print(f"  ... {len(need) - 12} more in {args.out}")

    cols = (list(rows[0].keys())
            + ["pdf_verdict", "pdf_line", "pdf_amounts", "pdf_ein_lines", "pdf_text"])
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(res)
    print(f"\nwrote {args.out} ({len(res)} rows). No data file was modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
