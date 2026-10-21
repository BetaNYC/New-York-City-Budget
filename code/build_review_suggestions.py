"""
The suggested decision for every review row of the promoted PDF families, as a machine-readable
file: data/pdf_review_suggestions.csv. The explorer's review screen shows it beside each item and
its "accept suggestion" button copies it into the reviewer's decision.

A suggestion is only ever the review file's own words turned into the decision vocabulary
(PLAN.md §5.3: source_error | parser_bug | accepted_as_printed | needs_info). Each rule below
cites the REVIEW.md item it comes from. Where a REVIEW.md makes no suggestion, the suggestion is
left blank: the reviewer decides with no default.

  FY2027 capital §254 and T&C: research/2026-10-20-fy27-capital-terms-review/REVIEW.md
  FY2027 Schedule C:           research/2026-10-20-fy27-schedule-c-review/REVIEW.md

Every review_id in the families' review CSVs (data/fyNN/pdf/<family>/*_review.csv) gets exactly
one row; a review_id the rules do not cover is a stop.

Run:   .venv/bin/python code/build_review_suggestions.py --write
Check: .venv/bin/python code/build_review_suggestions.py --check
"""
import argparse
import csv
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "data", "pdf_review_suggestions.csv")
COLUMNS = ["fiscal_year", "family", "review_id", "check_id", "suggested_decision", "suggested_note", "source"]
DECISIONS = ("source_error", "parser_bug", "accepted_as_printed", "needs_info")

CAP_REVIEW = "research/2026-10-20-fy27-capital-terms-review/REVIEW.md"
SC_REVIEW = "research/2026-10-20-fy27-schedule-c-review/REVIEW.md"

REVIEW_FILES = {
    ("2027", "capital_sd"): "data/fy27/pdf/capital_sd/fy27_capital_sd_review.csv",
    ("2027", "terms"): "data/fy27/pdf/terms/fy27_terms_review.csv",
    ("2027", "schedule_c"): "data/fy27/pdf/schedule_c/fy27_sc_review.csv",
}

# Capital: rows whose suggestion depends on the row, not only the check (REVIEW.md table A).
CAPITAL_BY_SUB = {
    ("C9.workbook_title", "E CC0598"): ("needs_info", "Real difference from the workbook's title: ask Council Finance which project it is.", "A13"),
    ("C9.workbook_title", "E CC1245"): ("needs_info", "Different school (P.S. 370 vs P.S. 199): ask Council Finance.", "A15"),
    ("C9.workbook_title", "HD CC1041"): ("accepted_as_printed", "Title edited in the PDF after export; keep the PDF's.", "A14"),
}
CAPITAL_BY_CHECK = {
    # REVIEW.md A1 says "Accept as printed"; the Council Finance question stays in the note.
    "C3.ma_series": ("accepted_as_printed", "Accept as printed; ask Council Finance what MA / 0N mean.", "A1"),
    "C2.rescindments": ("accepted_as_printed", "One printed number with no list behind it; only the subtraction ties.", "A2"),
    "C9.workbook_sponsor": ("accepted_as_printed", "Keep the PDF's sponsor; the workbook differs (delegations, or one 'Sanchez' for two members).", "A3, A5, A7, A11, A17"),
    "W.edited_after_export": ("accepted_as_printed", "Text typed into the PDF after export; keep as printed.", "A4, A7, A9, A14, A16"),
    "C3.part2_vs_part1": ("source_error", "The PDF disagrees with itself: Part I carries the later edit, Part II the old sponsor.", "A6, A8, A12"),
    "C6.amount_cells": ("accepted_as_printed", "Misprint on p.56: FY2030 not printed on this row; kept blank. No dollar effect.", "A10"),
    "C6.sponsor_digit": ("accepted_as_printed", "Misprint on p.56: the stray 0 belongs to the row below; kept as printed.", "A11"),
    "C5.geom_vs_stream": ("accepted_as_printed", "Checked: the page-position read stands, confirmed by the workbook or a 0 both rows print.", "B"),
    "W.fy2030_wrapped_below": ("accepted_as_printed", "Checked: FY2030 0 sits just below the row line.", "B"),
    "W.geom_near": ("accepted_as_printed", "Checked: joined to the nearest row; sponsors match the workbook.", "B"),
}
TERMS_BY_CHECK = {
    "T7.old_csv_text": ("accepted_as_printed", "The retired CSV is wrong here; the new text is as printed.", "C1"),
    "T7.old_csv_units": ("accepted_as_printed", "The retired CSV dropped these units; the new list is as printed.", "C1"),
    "W.midword_wrap": ("accepted_as_printed", "The PDF splits the word inside the cell; kept as printed.", "C3"),
    "W.wrap_hyphen": ("accepted_as_printed", "Line-end hyphen joined with no space, hyphen kept.", "C4"),
}
# Schedule C: only where its REVIEW.md says "Suggest ..." (items 1, 4, 5).
SC_BY_ID = {
    "01375b88b4c3": ("accepted_as_printed", "EIN read as 134113613 (both grids agree); name kept without the cut-off ' -'.", "item 1"),
    "d68b985e6c58": ("source_error", "The PDF disagrees with itself by $1 (statement $7,229,999, rows $7,229,998).", "item 4"),
    "7253bd6cce3a": ("source_error", "The same $1 in the roll-up (item 4).", "item 5"),
}


def suggest(fy, family, r):
    if family == "capital_sd":
        hit = CAPITAL_BY_SUB.get((r["check_id"], r["sub_id"])) or CAPITAL_BY_CHECK.get(r["check_id"])
        src = CAP_REVIEW
    elif family == "terms":
        hit = TERMS_BY_CHECK.get(r["check_id"])
        src = CAP_REVIEW
    elif family == "schedule_c":
        hit = SC_BY_ID.get(r["review_id"])
        src = SC_REVIEW
        if hit is None:
            return ("", "No suggestion in the Schedule C REVIEW.md.", src)
    else:
        raise SystemExit(f"unknown family {family}")
    if hit is None:
        raise SystemExit(f"{family} {r['review_id']}: no rule for check {r['check_id']}")
    decision, note, item = hit
    assert decision in DECISIONS, decision
    return decision, note, f"{src} {item}"


def build():
    rows = []
    for (fy, family), rel in REVIEW_FILES.items():
        with open(os.path.join(REPO, rel), newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d, note, src = suggest(fy, family, r)
                rows.append({"fiscal_year": fy, "family": family, "review_id": r["review_id"], "check_id": r["check_id"],
                             "suggested_decision": d, "suggested_note": note, "source": src})
    ids = [(r["family"], r["review_id"]) for r in rows]
    assert len(ids) == len(set(ids)), "duplicate review_id within a family"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue(), rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text, rows = build()
    if a.write:
        with open(OUT, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(OUT, REPO)} ({len(rows)} rows)")
        return
    cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
    if cur != text:
        print(f"DRIFT {os.path.relpath(OUT, REPO)}: run --write")
        sys.exit(1)
    print(f"ok    {os.path.relpath(OUT, REPO)} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
