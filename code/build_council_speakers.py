#!/usr/bin/env python3
"""build_council_speakers.py -- data/reference/council_speakers.csv: who was Speaker, with each
person's Council member id and terms from NYC Open Data uvw5-9znb (viz/explorer/DESIGN-NOTES.md
item 3). Groundwork only: no attribution logic reads it yet.

    python3 code/build_council_speakers.py --write | --check

Sourced from records, not memory. uvw5-9znb has no role column, so who was Speaker comes from the
printed record below: each fiscal year's adopted Schedule C, which names the Speaker on its cover
(or in its introduction). Each claim is checked against the PDF's text at build time; a page that
no longer says it is a stop. The person's Council member id and terms come from uvw5-9znb: the
member terms that overlap the fiscal years the record covers (a fiscal year runs July to June).

`member_term_start` / `member_term_end` are those **Council member terms** (the span of the
member's terms that overlap the fiscal years named), NOT the Speaker's tenure: no record in this
repository gives the dates of election as Speaker (`term_basis` says so). No row is written for a Speaker
no committed record names (FY2027 onward: see `NOT_RECORDED`).
"""
import argparse
import csv
import gzip
import io
import os
import re
import sys

import pdfplumber

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = "data/reference/council_speakers.csv"
UVW5 = "source/open-data-uvw5-9znb/uvw5-9znb.csv.gz"

# (fiscal year, PDF, 1-based page, the printed name as it appears, uvw5-9znb name)
RECORDS = [
    (2008, "source/FY08/schedule_c_rvs_2008.pdf", 1, "Christine Quinn", "Christine C. Quinn"),
    (2009, "source/FY09/fy09-Schedule-C-final.pdf", 1, "Christine Quinn", "Christine C. Quinn"),
    (2011, "source/FY11/fy2011-C2011.pdf", 1, "ChristineC.Quinn,Speaker", "Christine C. Quinn"),
    (2012, "source/FY12/fy2012-skedcfinal.pdf", 1, "ChristineC.Quinn,Speaker", "Christine C. Quinn"),
    (2013, "source/FY13/fy2013-FY-2013-Schedule-C-Merge-Final1.pdf", 1, "Christine C. Quinn", "Christine C. Quinn"),
    (2014, "source/FY14/fy2014-skedc.pdf", 1, "Christine C. Quinn", "Christine C. Quinn"),
    (2015, "source/FY15/fy2015-FY15-Schedule-C-Template-Final.pdf", 1, "Melissa Mark-Viverito", "Melissa Mark-Viverito"),
    (2017, "source/FY17/FY17-Schedule-C.pdf", 4, "Speaker Melissa Mark-Viverito", "Melissa Mark-Viverito"),
    (2018, "source/FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf", 4, "Speaker Melissa Mark-Viverito", "Melissa Mark-Viverito"),
    (2019, "source/FY19/Fiscal-2019-Schedule-C-Final-Report.pdf", 1, "Corey Johnson", "Corey D. Johnson"),
    (2020, "source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf", 1, "Corey Johnson", "Corey D. Johnson"),
    (2021, "source/FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf", 1, "Corey Johnson", "Corey D. Johnson"),
    (2022, "source/FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf", 1, "Corey Johnson", "Corey D. Johnson"),
    (2023, "source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf", 1, "Adrienne E. Adams", "Adrienne E. Adams"),
    (2024, "source/FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf", 1, "Adrienne E. Adams", "Adrienne E. Adams"),
    (2025, "source/FY25/Fiscal-2025-Schedule-C-MERGE-FINAL-2.pdf", 4, "Speaker Adrienne E. Adams", "Adrienne E. Adams"),
    (2026, "source/FY26/Fiscal-2026-Schedule-C-4.pdf", 4, "Speaker Adrienne E. Adams", "Adrienne E. Adams"),
]
# Years with no committed record naming the Speaker. FY2010, FY2016: the Schedule C cover does not
# print the name. FY2027: no FY2027 PDF in source/ names a Speaker; DESIGN-NOTES says the Speaker
# changed in January 2026, which needs a record (e.g. Legistar) before it is written here.
NOT_RECORDED = [2010, 2016, 2027]

FIELDS = ["person", "council_member_id", "member_term_start", "member_term_end", "fiscal_years_named",
          "term_basis", "source"]


def squash(s):
    return re.sub(r"\s+", "", s)


def check_record(fy, pdf, page, printed):
    with pdfplumber.open(os.path.join(ROOT, pdf)) as p:
        text = p.pages[page - 1].extract_text() or ""
    if squash(printed) not in squash(text) or "Speaker" not in text:
        raise SystemExit(f"FY{fy}: {pdf} p.{page} no longer prints {printed!r} with 'Speaker'")


def build():
    with gzip.open(os.path.join(ROOT, UVW5), "rt", encoding="utf-8", newline="") as f:
        members = list(csv.DictReader(f))
    people = {}
    for fy, pdf, page, printed, name in RECORDS:
        check_record(fy, pdf, page, printed)
        people.setdefault(name, []).append((fy, pdf, page))
    rows = []
    for name, recs in people.items():
        fys = sorted(r[0] for r in recs)
        start, end = f"{fys[0] - 1}-07-01", f"{fys[-1]}-06-30"
        terms = [m for m in members if m["name"] == name
                 and m["term_start"][:10] <= end and m["term_end"][:10] >= start]
        ids = {m["council_member_id"] for m in terms}
        if len(ids) != 1:
            raise SystemExit(f"{name}: member ids {ids} in uvw5-9znb for FY{fys[0]}-FY{fys[-1]}")
        rows.append({
            "person": name, "council_member_id": ids.pop(),
            "member_term_start": min(m["term_start"][:10] for m in terms),
            "member_term_end": max(m["term_end"][:10] for m in terms),
            "fiscal_years_named": ";".join(str(y) for y in fys),
            "term_basis": "Council member terms overlapping those fiscal years (uvw5-9znb), not "
                          "Speaker tenure; the Speaker election date is not recorded",
            "source": "; ".join(f"{pdf} p.{page}" for _, pdf, page in recs) + f"; {UVW5}"})
    rows.sort(key=lambda r: r["member_term_start"])
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text = build()
    path = os.path.join(ROOT, OUT)
    if a.write:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        print(f"wrote {OUT}")
        return 0
    same = os.path.exists(path) and open(path, encoding="utf-8").read() == text
    print("ok" if same else f"DRIFT {OUT}")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
