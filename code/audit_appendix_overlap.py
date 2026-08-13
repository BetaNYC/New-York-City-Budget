#!/usr/bin/env python3
"""
audit_appendix_overlap.py -- are the Schedule C appendices a subset of the award body, or additive?

DATA-DICTIONARY.md says: "These are subsets of the award body -- do not add them to the Schedule C
total." The published headline (62,213 rows / $3,741,615,569) adds them anyway. Only one can be
right, and the difference is roughly $49.8M a year, so it decides the top-line number in the README,
the viz and every MCP response footer. Issue #57 calls it a release blocker and says it is not
resolvable from the CSVs.

It is resolvable -- from the PDFs, which is where both the body and the appendices are printed.

FOUR INDEPENDENT TESTS, because the CSV-level one is genuinely ambiguous (84-96% of appendix rows
have no (ein, amount) twin among the awards, pointing additive; but a few hundred match on all of
(ein, amount, member, organization), pointing subset):

  1. PAGE NUMBERING. The table of contents numbers the body continuously, then restarts for the
     appendices ("APPENDIX A: AGING DISCRETIONARY....PAGE 1 - 26"). A re-sorted view of the same
     awards would not get its own pagination; a separate section would.
  2. STREAM NAMES IN THE BODY. If the appendices detail a body line item, that line item has to
     exist. Search the body pages for "Aging Discretionary", "Local Initiatives", "Youth
     Discretionary".
  3. SHORTFALL ARITHMETIC. The document prints a GRAND TOTAL and the parser reconciles it. If the
     appendices were already inside the award body, the awards alone would reach that total and
     adding the appendices would OVERSHOOT it. Does that ever happen?
  4. TWIN DISTINCTIVENESS. Appendix rows with an exact twin among the awards, split by whether the
     amount is a round thousand. $5,000 is designated hundreds of times a year, so a round-number
     twin is nearly free; a twin on an odd figure is what a genuine duplicate looks like.

No test alone settles it. Test 3 speaks to dollars, 1 and 2 to what the document intends, 4 bounds
how much could possibly be double-counted even if the others were misread.

Read-only. Writes no data file.

Usage:  python3 code/audit_appendix_overlap.py [--year 2024]
"""
import argparse
import csv
import glob
import os
import re
import subprocess
import sys

CACHE = "build/pdftext"
STREAMS = ("Aging Discretionary", "Local Initiative", "Youth Discretionary")
TOC_APPENDIX = re.compile(r"(?i)appendix\s+([abc])\s*:\s*(.+?)\s*[.…]+\s*page\s*(\d+)\s*[-–]\s*(\d+)")
MONEY = re.compile(r"\$\s?([\d,]+)")
EIN = re.compile(r"\b(\d{2})-?(\d{7})\b")

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


def pdf_pages(fy):
    src = PDFS.get(fy)
    if not src or not os.path.exists(src):
        return None
    os.makedirs(CACHE, exist_ok=True)
    txt = os.path.join(CACHE, f"fy{fy}.pages.txt")
    if not os.path.exists(txt):
        subprocess.run(["pdftotext", "-layout", src, txt], check=True)
    # pdftotext separates pages with a form feed, so page N is index N-1.
    return open(txt, encoding="utf-8", errors="replace").read().split("\f")


def sections(fy):
    """Where the body ends and each appendix begins, from the parser's own reconciliation file.

    Parsed from that file rather than re-derived, so this audit and the parser cannot disagree
    about which pages are the body.
    """
    key = f"fy{str(fy)[2:]}"
    path = f"data/{key}/schedule_c/{key}_schedule_c_reconciliation.txt"
    if not os.path.exists(path):
        return None
    head = open(path, encoding="utf-8").read()
    m = re.search(r"sections:\s*body\s*(\d+)\.\.(\d+)(.*)", head)
    if not m:
        return None
    apx = {a.lower(): int(p) for a, p in re.findall(r"([ABC])\s+(\d+)", m.group(3))}
    return int(m.group(1)), int(m.group(2)), apx


def pairs(pages, rng):
    out = set()
    for p in rng:
        if not 1 <= p <= len(pages):
            continue
        for line in pages[p - 1].splitlines():
            eins = [a + b for a, b in EIN.findall(line)]
            amts = [int(a.replace(",", "")) for a in MONEY.findall(line)]
            for e in eins:
                for a in amts:
                    out.add((e, a))
    return out


def csv_total(pattern):
    tot, n = 0, 0
    for f in glob.glob(pattern):
        if "initiatives" in f or "reconcil" in f:
            continue
        for r in csv.DictReader(open(f, newline="", encoding="utf-8")):
            try:
                tot += int(float(r.get("amount") or 0))
                n += 1
            except (TypeError, ValueError):
                pass
    return n, tot


def grand_total(fy):
    """The GRAND TOTAL the document itself prints, and how cleanly the parser reconciled to it.

    Taken from the parser's reconciliation file rather than re-summed here, so the two cannot drift.
    """
    key = f"fy{str(fy)[2:]}"
    path = f"data/{key}/schedule_c/{key}_schedule_c_reconciliation.txt"
    if not os.path.exists(path):
        return None, ""
    t = open(path, encoding="utf-8").read()
    m = re.search(r"GRAND TOTAL\s+([\d,]+)\s+([\d,]+)\s+(.*)", t)
    return (int(m.group(2).replace(",", "")), m.group(3).strip()) if m else (None, "")


def twins(key):
    """Appendix rows with an exact (EIN, amount, organization) twin among the award rows."""
    def load(pat):
        out = []
        for f in glob.glob(pat):
            if "initiatives" in f or "reconcil" in f:
                continue
            out += list(csv.DictReader(open(f, newline="", encoding="utf-8")))
        return out

    def k(r):
        try:
            amt = int(float(r.get("amount") or 0))
        except (TypeError, ValueError):
            amt = 0
        return (re.sub(r"\D", "", r.get("ein") or ""), amt,
                re.sub(r"[^a-z0-9]", "", (r.get("organization") or "").lower()))

    aw = {k(r) for r in load(f"data/{key}/schedule_c/*_schedule_c_awards.csv")}
    ap = load(f"data/{key}/schedule_c/*_appendix_*.csv")
    t = [r for r in ap if k(r) in aw]
    odd = [r for r in t if k(r)[1] % 1000]
    return len(ap), len(t), sum(k(r)[1] for r in t), len(odd), sum(k(r)[1] for r in odd)


def audit(fy):
    pages = pdf_pages(fy)
    sec = sections(fy)
    if not pages or not sec:
        return None
    body_lo, body_hi, apx = sec
    key = f"fy{str(fy)[2:]}"

    toc = "\n".join(pages[:6])
    toc_hits = TOC_APPENDIX.findall(toc)
    restarts = sum(1 for _, _, lo, _ in toc_hits if int(lo) == 1)

    body_txt = "\n".join(pages[body_lo - 1:body_hi]).lower()
    stream_hits = {s: body_txt.count(s.lower()) for s in STREAMS}

    apx_lo = min(apx.values()) if apx else body_hi + 1
    b = pairs(pages, range(body_lo, body_hi + 1))
    a = pairs(pages, range(apx_lo, len(pages) + 1))
    both = a & b
    # $5,000 is designated hundreds of times a year, so an overlap on a round number is cheap.
    # An overlap on an odd figure is the kind that would actually indicate the same award twice.
    odd = {p for p in both if p[1] % 1000}

    n_aw, d_aw = csv_total(f"data/{key}/schedule_c/*_schedule_c_awards.csv")
    n_ap, d_ap = csv_total(f"data/{key}/schedule_c/*_appendix_*.csv")
    gt, recon = grand_total(fy)
    ap_rows, tw, tw_d, tw_odd, tw_odd_d = twins(key)

    return dict(fy=fy, toc_appendices=len(toc_hits), toc_restarts_at_1=restarts,
                stream_hits=stream_hits, apx_pairs=len(a), body_pairs=len(b),
                overlap=len(both), overlap_odd=len(odd),
                awards_rows=n_aw, awards_dollars=d_aw, apx_rows=n_ap, apx_dollars=d_ap,
                grand_total=gt, reconciliation=recon, ap_rows=ap_rows,
                twins=tw, twins_dollars=tw_d, twins_odd=tw_odd, twins_odd_dollars=tw_odd_d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, help="one fiscal year; default all")
    args = ap.parse_args()

    years = [args.year] if args.year else sorted(PDFS)
    res = [r for r in (audit(y) for y in years) if r]
    if not res:
        print("no year could be audited", file=sys.stderr)
        return 1

    print("TEST 1 — does the ToC give the appendices their own page numbering?")
    print("TEST 2 — do the appendix stream names appear anywhere in the body?\n")
    print(f"{'FY':<6}{'apx in ToC':>11}{'restart at p1':>15}{'stream names in body':>22}")
    for r in res:
        print(f"{r['fy']:<6}{r['toc_appendices']:>11}{r['toc_restarts_at_1']:>15}"
              f"{sum(r['stream_hits'].values()):>22}")

    print("\nTEST 3 — if the appendices were already inside the awards, awards alone would reach")
    print("         the printed GRAND TOTAL and adding them would overshoot it.\n")
    print(f"{'FY':<6}{'GRAND TOTAL':>15}{'awards':>15}{'shortfall':>14}"
          f"{'appendices':>13}{'covers':>8}{'over?':>7}")
    over = 0
    for r in res:
        if not r["grand_total"]:
            continue
        short = r["grand_total"] - r["awards_dollars"]
        cov = f"{r['apx_dollars'] / short * 100:.0f}%" if short > 0 else "n/a"
        o = "YES" if r["awards_dollars"] + r["apx_dollars"] > r["grand_total"] else "no"
        over += o == "YES"
        print(f"{r['fy']:<6}{r['grand_total']:>15,}{r['awards_dollars']:>15,}{short:>14,}"
              f"{r['apx_dollars']:>13,}{cov:>8}{o:>7}")
    print(f"\n  years where awards + appendices exceed the Council's own total: {over} of {len(res)}")

    print("\nTEST 4 — appendix rows with an exact twin among the awards\n")
    print(f"{'FY':<6}{'apx rows':>10}{'no twin':>10}{'%':>7}{'twins':>8}"
          f"{'twin $':>14}{'distinctive':>13}{'distinctive $':>15}")
    for r in res:
        if not r["ap_rows"]:
            continue
        nt = r["ap_rows"] - r["twins"]
        print(f"{r['fy']:<6}{r['ap_rows']:>10,}{nt:>10,}{nt / r['ap_rows'] * 100:>6.0f}%"
              f"{r['twins']:>8,}{r['twins_dollars']:>14,}{r['twins_odd']:>13,}"
              f"{r['twins_odd_dollars']:>15,}")

    tot_ap = sum(r["apx_dollars"] for r in res)
    tot_aw = sum(r["awards_dollars"] for r in res)
    tot_gt = sum(r["grand_total"] or 0 for r in res)
    odd_d = sum(r["twins_odd_dollars"] for r in res)
    print(f"\nacross {len(res)} years:")
    print(f"  award rows                        ${tot_aw:,}")
    print(f"  appendix rows                     ${tot_ap:,}")
    print(f"  published headline                ${tot_aw + tot_ap:,}")
    print(f"  Council's own printed GRAND TOTALs ${tot_gt:,}"
          f"   <- the headline is {(tot_aw + tot_ap) / tot_gt * 100:.1f}% of it")
    print(f"  upper bound on double-counting, by distinctive-amount twins: ${odd_d:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
