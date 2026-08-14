#!/usr/bin/env python3
"""
build_index.py -- build the review index the UI reads.

The extracted CSVs carry no page number, so there is nothing to line a row up against in the PDF.
This reconstructs that link: it re-runs the parser's OWN anchor over each page in isolation, then
matches the (EIN, amount) pairs it finds there against the committed rows. A row is attributed to
the page whose printed text actually carries its EIN and its amount together.

That attribution is evidence, not a guess -- but it is not infallible, and the UI says so: where one
(EIN, amount) pair is printed on more than one page, every candidate page is recorded and the row is
marked `ambiguous`. Silently picking the first would be the same class of error this repo has been
correcting all week.

Emits one JSON per fiscal year to public/data/, plus an index.json manifest. Read-only: it never
writes to data/ or source/.

Usage:  python3 review-ui/build_index.py [--year 2016] [--out review-ui/public/data]
"""
import argparse
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "code"))

import parse_schedule_c as P  # noqa: E402  the anchor and helpers, straight from the parser
import validate_data as V     # noqa: E402  the QA detectors, so the UI cannot disagree with QA

# Year -> adopted Schedule C PDF, taken from the parser's own test files rather than guessed.
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


def key(ein, amount):
    try:
        return re.sub(r"\D", "", str(ein or "")), int(float(amount or 0))
    except (TypeError, ValueError):
        return re.sub(r"\D", "", str(ein or "")), None


def load_rows(fy):
    """Every committed award/appendix row for a year, tagged with its file and 1-based CSV line."""
    k = f"fy{str(fy)[2:]}"
    out = []
    for f in sorted(glob.glob(os.path.join(REPO, f"data/{k}/schedule_c/*.csv"))):
        base = os.path.basename(f)
        if "initiatives" in base or "reconcil" in base:
            continue
        stream = ("appendix_a_aging" if "appendix_a" in base else
                  "appendix_b_local" if "appendix_b" in base else
                  "appendix_c_youth" if "appendix_c" in base else "awards")
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                out.append(dict(r, _file=base, _line=ln, _stream=stream))
    return out


def load_crosswalk():
    """(file, line) -> the repairs applied to that row, so the UI can show what was changed."""
    path = os.path.join(REPO, "data/combined/org_name_recovery_crosswalk.csv")
    cw = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as fh:
            for c in csv.DictReader(fh):
                cw.setdefault((os.path.basename(c["file"]), int(c["line"])), []).append({
                    "column": c.get("column") or "organization",
                    "defect": c.get("defect", ""),
                    "source": c.get("source", ""),
                    "before": c.get("original_organization", ""),
                    "after": c.get("recovered_organization", ""),
                })
    return cw


# A DEFECT is a field that is wrong. An OBSERVATION is a field that is empty for a reason the
# schema allows. Conflating them makes the headline meaningless: every FY2016 row has a blank
# `member`, because FY2016 extracted only citywide initiative rows, which have no sponsoring member.
# Counting that as a defect scored FY2016 at 0% clean when its organization fields are 93.7% sound.
DEFECTS = ("org_merged", "org_prose", "org_blank")


def qa_flags(row):
    org = row.get("organization") or ""
    f = []
    if V.EIN_IN_TEXT.search(org):
        f.append("org_merged")
    if V.ORG_PROSE.search(org):
        f.append("org_prose")
    if not org.strip():
        f.append("org_blank")
    if not (row.get("member") or "").strip():
        f.append("member_blank")
    if not (row.get("initiative") or "").strip() and row.get("award_type") == "initiative_provider":
        f.append("initiative_blank")
    return f


def sections(fy):
    """Body/appendix page boundaries, read from the parser's own reconciliation file."""
    k = f"fy{str(fy)[2:]}"
    path = os.path.join(REPO, f"data/{k}/schedule_c/{k}_schedule_c_reconciliation.txt")
    if not os.path.exists(path):
        return None, ""
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"sections:\s*body\s*(\d+)\.\.(\d+)(.*)", txt)
    if not m:
        return None, txt
    apx = {a: int(p) for a, p in re.findall(r"([ABC])\s+(\d+)", m.group(3))}
    return {"body": [int(m.group(1)), int(m.group(2))], "appendix": apx}, txt


def build(fy, outdir):
    import pypdf
    src = PDFS.get(fy)
    if not src or not os.path.exists(os.path.join(REPO, src)):
        return None
    reader = pypdf.PdfReader(os.path.join(REPO, src))
    rows = load_rows(fy)
    if not rows:
        return None
    cw = load_crosswalk()

    # (ein, amount) -> the pages whose printed text carries both. Built from the parser's own
    # ANCHOR so the UI shows what the parser saw, not a second opinion about the document.
    page_hits = {}
    page_text = []
    for pno, page in enumerate(reader.pages, start=1):
        t = page.extract_text() or ""
        page_text.append(t)
        for m in P.ANCHOR.finditer(t):
            try:
                page_hits.setdefault((P.eind(m.group(1)), P.money(m.group(2))), []).append(pno)
            except (TypeError, ValueError):
                continue

    by_page, unplaced = {}, []
    for r in rows:
        kk = key(r.get("ein"), r.get("amount"))
        pages = sorted(set(page_hits.get(kk, [])))
        flags = qa_flags(r)
        repairs = cw.get((r["_file"], r["_line"]), [])
        rec = {
            "file": r["_file"], "line": r["_line"], "stream": r["_stream"],
            "member": r.get("member", ""), "organization": r.get("organization", ""),
            "program": r.get("program", ""), "ein": r.get("ein", ""),
            "amount": r.get("amount", ""), "agency": r.get("agency", ""),
            "purpose": (r.get("purpose") or "")[:400],
            "category": r.get("category", ""), "initiative": r.get("initiative", ""),
            "award_type": r.get("award_type", ""),
            "flags": flags, "repairs": repairs,
            "pages": pages, "ambiguous": len(pages) > 1,
        }
        if pages:
            by_page.setdefault(pages[0], []).append(rec)
        else:
            unplaced.append(rec)

    sec, recon = sections(fy)
    pages_out = []
    for pno in range(1, len(reader.pages) + 1):
        prs = by_page.get(pno, [])
        anchors = len(list(P.ANCHOR.finditer(page_text[pno - 1])))
        pages_out.append({
            "page": pno,
            "anchors": anchors,          # what the parser's regex found on this page
            "rows": prs,                 # what actually reached the CSVs from it
            "text": page_text[pno - 1][:4000],
            "section": ("body" if sec and sec["body"][0] <= pno <= sec["body"][1]
                        else "appendix" if sec and pno > sec["body"][1] else "front"),
        })

    total_anchors = sum(p["anchors"] for p in pages_out)
    defective = sum(1 for r in rows if any(f in DEFECTS for f in qa_flags(r)))
    flagged = sum(1 for r in rows if qa_flags(r))
    doc = {
        "fiscal_year": fy,
        "pdf": src,
        "page_count": len(reader.pages),
        "sections": sec,
        "reconciliation": recon,
        "summary": {
            "rows": len(rows),
            "dollars": sum(int(float(r.get("amount") or 0)) for r in rows),
            "anchors_in_pdf": total_anchors,
            "rows_placed": len(rows) - len(unplaced),
            "rows_unplaced": len(unplaced),
            "rows_ambiguous": sum(1 for p in pages_out for r in p["rows"] if r["ambiguous"]),
            "rows_flagged": flagged,          # any flag at all, defect or observation
            "rows_defective": defective,      # org_merged / org_prose / org_blank only
            "pct_clean": round((len(rows) - defective) / len(rows) * 100, 1) if rows else 0,
            "repairs": sum(len(cw.get((r["_file"], r["_line"]), [])) for r in rows),
            "by_stream": {s: sum(1 for r in rows if r["_stream"] == s)
                          for s in ("awards", "appendix_a_aging", "appendix_b_local",
                                    "appendix_c_youth")},
            "by_flag": {f: sum(1 for r in rows if f in qa_flags(r))
                        for f in ("org_merged", "org_prose", "org_blank", "member_blank",
                                  "initiative_blank")},
        },
        "unplaced": unplaced[:500],
        "pages": pages_out,
    }
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, f"fy{fy}.json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, separators=(",", ":"))
    return doc["summary"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int)
    ap.add_argument("--out", default=os.path.join(HERE, "public", "data"))
    a = ap.parse_args()

    years = [a.year] if a.year else sorted(PDFS)
    manifest = []
    for fy in years:
        s = build(fy, a.out)
        if not s:
            print(f"FY{fy}: skipped (no PDF or no rows)")
            continue
        manifest.append({"fiscal_year": fy, **s})
        print(f"FY{fy}: {s['rows']:,} rows, {s['rows_placed']:,} placed on a page, "
              f"{s['rows_unplaced']:,} unplaced, {s['pct_clean']}% clean")

    if manifest:
        os.makedirs(a.out, exist_ok=True)
        with open(os.path.join(a.out, "index.json"), "w", encoding="utf-8") as fh:
            json.dump({"years": manifest}, fh, indent=1)
        print(f"\nwrote {len(manifest)} year files + index.json to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
