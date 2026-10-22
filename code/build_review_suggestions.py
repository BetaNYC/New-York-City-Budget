"""
The suggested decision for every review row of the promoted PDF families, as a machine-readable
file: data/pdf_review_suggestions.csv. The explorer's review screen shows it beside each item and
its "accept suggestion" button copies it into the reviewer's decision.

A suggestion is only ever the review file's own words turned into the decision vocabulary
(PLAN.md §5.3: source_error | parser_bug | accepted_as_printed | needs_info; and, since #209,
read_from_page_image, whose note carries what the page shows: code/page_image.py). Each rule below
cites the REVIEW.md item it comes from. Where a REVIEW.md makes no suggestion, the suggestion is
left blank: the reviewer decides with no default.

  FY2027 capital §254 and T&C: research/2026-10-20-fy27-capital-terms-review/REVIEW.md
  FY2027 Schedule C:           research/2026-10-20-fy27-schedule-c-review/REVIEW.md
  FY2026 capital §254 and T&C: research/2026-10-21-fy26-capital-terms-review/REVIEW.md
  FY2026 Schedule C and transparency: research/2026-10-21-fy26-{schedule-c,transparency}-review/REVIEW.md
  FY2025-FY2018, every family: code/review_suggestion_rules.py, one rule list per family-year, each
    citing that year's own research/<date>-fyNN-<family>-review/REVIEW.md
Items that say "ask Council Finance" become needs_info (they stay open until answered), as for FY2027.

Every review_id in the families' review CSVs (data/fyNN/pdf/<family>/*_review.csv) gets exactly
one row; a review_id the rules do not cover is a stop. So is a family-year in data/pdf_years.csv
with no entry in REVIEW_FILES, or with no rules of its own (a year never falls through to
another year's rules).

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
sys.path.insert(0, HERE)

import page_image  # noqa: E402
import review_suggestion_rules as rules  # noqa: E402

OUT = os.path.join(REPO, "data", "pdf_review_suggestions.csv")
COLUMNS = ["fiscal_year", "family", "review_id", "check_id", "suggested_decision", "suggested_note", "source"]
DECISIONS = ("source_error", "parser_bug", "accepted_as_printed", "needs_info", "read_from_page_image")

CAP_REVIEW = "research/2026-10-20-fy27-capital-terms-review/REVIEW.md"
SC_REVIEW = "research/2026-10-20-fy27-schedule-c-review/REVIEW.md"
CAP26_REVIEW = "research/2026-10-21-fy26-capital-terms-review/REVIEW.md"

REVIEW_FILES = {
    ("2027", "capital_sd"): "data/fy27/pdf/capital_sd/fy27_capital_sd_review.csv",
    ("2027", "terms"): "data/fy27/pdf/terms/fy27_terms_review.csv",
    ("2027", "schedule_c"): "data/fy27/pdf/schedule_c/fy27_sc_review.csv",
    ("2026", "capital_sd"): "data/fy26/pdf/capital_sd/fy26_capital_sd_review.csv",
    ("2026", "terms"): "data/fy26/pdf/terms/fy26_terms_review.csv",
    ("2026", "transparency"): "data/fy26/pdf/transparency/fy26_tr_review.csv",
    ("2026", "schedule_c"): "data/fy26/pdf/schedule_c/fy26_sc_review.csv",
    ("2025", "capital_sd"): "data/fy25/pdf/capital_sd/fy25_capital_sd_review.csv",
    ("2025", "schedule_c"): "data/fy25/pdf/schedule_c/fy25_sc_review.csv",
    ("2025", "terms"): "data/fy25/pdf/terms/fy25_terms_review.csv",
    ("2025", "transparency"): "data/fy25/pdf/transparency/fy25_tr_review.csv",
    ("2024", "capital_sd"): "data/fy24/pdf/capital_sd/fy24_capital_sd_review.csv",
    ("2024", "schedule_c"): "data/fy24/pdf/schedule_c/fy24_sc_review.csv",
    ("2024", "terms"): "data/fy24/pdf/terms/fy24_terms_review.csv",
    ("2024", "transparency"): "data/fy24/pdf/transparency/fy24_tr_review.csv",
    ("2023", "capital_sd"): "data/fy23/pdf/capital_sd/fy23_capital_sd_review.csv",
    ("2023", "schedule_c"): "data/fy23/pdf/schedule_c/fy23_sc_review.csv",
    ("2023", "terms"): "data/fy23/pdf/terms/fy23_terms_review.csv",
    ("2023", "transparency"): "data/fy23/pdf/transparency/fy23_tr_review.csv",
    ("2022", "capital_sd"): "data/fy22/pdf/capital_sd/fy22_capital_sd_review.csv",
    ("2022", "schedule_c"): "data/fy22/pdf/schedule_c/fy22_sc_review.csv",
    ("2022", "terms"): "data/fy22/pdf/terms/fy22_terms_review.csv",
    ("2022", "transparency"): "data/fy22/pdf/transparency/fy22_tr_review.csv",
    ("2021", "schedule_c"): "data/fy21/pdf/schedule_c/fy21_sc_review.csv",
    ("2021", "terms"): "data/fy21/pdf/terms/fy21_terms_review.csv",
    ("2021", "transparency"): "data/fy21/pdf/transparency/fy21_tr_review.csv",
    ("2020", "capital_sd"): "data/fy20/pdf/capital_sd/fy20_capital_sd_review.csv",
    ("2020", "schedule_c"): "data/fy20/pdf/schedule_c/fy20_sc_review.csv",
    ("2020", "transparency"): "data/fy20/pdf/transparency/fy20_tr_review.csv",
    ("2019", "capital_sd"): "data/fy19/pdf/capital_sd/fy19_capital_sd_review.csv",
    ("2019", "schedule_c"): "data/fy19/pdf/schedule_c/fy19_sc_review.csv",
    ("2019", "transparency"): "data/fy19/pdf/transparency/fy19_tr_review.csv",
    ("2018", "capital_sd"): "data/fy18/pdf/capital_sd/fy18_capital_sd_review.csv",
    ("2018", "schedule_c"): "data/fy18/pdf/schedule_c/fy18_sc_review.csv",
    ("2018", "terms"): "data/fy18/pdf/terms/fy18_terms_review.csv",
    ("2018", "transparency"): "data/fy18/pdf/transparency/fy18_tr_review.csv",
}

# FY2026 Schedule C (research/2026-10-21-fy26-schedule-c-review/REVIEW.md): every review_id, from
# its tables (items 15-17 state source_error without the word "Suggest"; item 8 is "Same" as 7).
SC26_REVIEW = "research/2026-10-21-fy26-schedule-c-review/REVIEW.md"
SC26_BY_ID = {
    "3c76fd1e62f3": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 1"),
    "072b76ac2954": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 2"),
    "5c57e0993df3": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 10"),
    "239a56d3a7b0": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 13"),
    "6664767f0cae": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 3"),
    "c0ca776b10e9": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 4"),
    "94ae97242c0b": ("source_error", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 5"),
    "9937d66ba686": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 6"),
    "1ba072f0ec08": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 7"),
    "27f7098256d9": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 8 (same as item 7)"),
    "a4f483f8851e": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 9"),
    "3c166360f764": ("source_error", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 15"),
    "818c8efb9455": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 11"),
    "b584161694fe": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 12"),
    "b3a44442119b": ("source_error", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 17"),
    "205216c81be1": ("source_error", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 14"),
    "d46489c09362": ("source_error", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "item 16"),
    "6a638deac498": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
    "7e804857cd66": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
    "725050558d24": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
    "1627668768c9": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
    "1fdc4cfb83e2": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
    "d7e15277029d": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
    "44ce15605701": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
    "90633378be3d": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
    "cc1ddc891f8b": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
    "fce75be02b84": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
    "fc84c7565f29": ("accepted_as_printed", "As the FY2026 Schedule C REVIEW.md suggests; see its item.", "section: Names that differ between a box and its summary line"),
}

# FY2026 transparency (research/2026-10-21-fy26-transparency-review/REVIEW.md): its "Suggest"
# column, by review_id; the two rows it gives none stay blank.
TR26_REVIEW = "research/2026-10-21-fy26-transparency-review/REVIEW.md"
TR26_BY_ID = {
    "487d846b5a5b": ("source_error", "As the transparency REVIEW.md suggests; see its item.", "Critical #1"),
    "01cb3c5559d1": ("source_error", "As the transparency REVIEW.md suggests; see its item.", "Critical #2"),
    "a47ff8c5407b": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #3"),
    "58100791ada4": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #4"),
    "71b3b170be30": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #5"),
    "3524a4050de3": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #6"),
    "4b38509307b7": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #7"),
    "e00249abeff9": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #8"),
    "030dc2c1c5fc": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #9"),
    "ae93444880d9": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #10"),
    "b37d94a2bf90": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #11"),
    "5446d05f734c": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #12"),
    "ea9ee205da67": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #13"),
    "fd74d258bf10": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #14"),
    "d9a313796d9a": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #15"),
    "7866664b23b6": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #16"),
    "d9074007ab74": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #17"),
    "ff0c9432d996": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #18"),
    "977106b18980": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #19"),
    "1216bfc3e536": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #20"),
    "66242e01ad39": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #21"),
    "bf7f09c1f8e1": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #22"),
    "ebdf1f207c90": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #23"),
    "b58a6462dcf7": ("accepted_as_printed", "As the transparency REVIEW.md suggests; see its item.", "Warn #24"),
}

# FY2026 (research/2026-10-21-fy26-capital-terms-review/REVIEW.md, tables A, B, C).
CAPITAL26_BY_SUB = {
    ("C3.part2_only", "PV MA0022"): ("accepted_as_printed", "Part II only (MA ID on a 0N line); accept as printed and include in the Council Finance question.", "A3"),
    ("C3.part2_only", "PV MA0007"): ("accepted_as_printed", "Part II only, on a DN line; accept as printed and include in the Council Finance question.", "A7"),
    ("C3.part2_only", "PV MA0005"): ("accepted_as_printed", "A negative row (-183,000), Part II only; a reduction, accept as printed.", "A8"),
}
CAPITAL26_BY_CHECK = {
    "C3.ma_series": ("accepted_as_printed", "Accept as printed; ask Council Finance what MM / MA / 0N mean.", "A1"),
    "C2.rescindments": ("accepted_as_printed", "One printed number; only the subtraction can be checked here.", "A2"),
    "W.edited_after_export": ("accepted_as_printed", "Typed into the PDF after export; accept the later edit as printed.", "A4"),
    "C9.workbook_sponsor": ("accepted_as_printed", "Keep the PDF's sponsor (later edits, or the workbook's merged HN CN1451).", "A4, A5"),
    "C3.part2_vs_part1": ("accepted_as_printed", "Part II prints the name without its accent; accept both as printed.", "A9"),
    "C9.workbook": ("accepted_as_printed", "Keep the PDF: ADMIN out-year rows not in the workbook, and the workbook's two projects under HN CN1451.", "A5, A6"),
    "C9.workbook_title": ("accepted_as_printed", "Keep the PDF's title (the workbook's differ or carry stray characters).", "A10-A15"),
    "C5.geom_vs_stream": ("accepted_as_printed", "Checked: the page-position read stands.", "B"),
    "W.geom_near": ("accepted_as_printed", "Checked: joined to the nearest row; values match the other Part and the workbook.", "B"),
}
TERMS26_BY_CHECK = {
    "T7.old_csv_text": ("accepted_as_printed", "The retired CSV is wrong here; use the new text, as printed.", "C1, C2"),
    "T7.old_csv_units": ("accepted_as_printed", "The retired CSV lost these units; the new list is as printed.", "C1"),
    "T3.body_vs_heading": ("accepted_as_printed", "#67's body says 'appropriations 311 and 312'; the heading is right, the typo is the PDF's.", "C3"),
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
    if (fy, family) in rules.RULES:
        return rules.suggest(fy, family, r)
    if family == "transparency" and fy == "2026":
        hit = TR26_BY_ID.get(r["review_id"])
        if hit is None:
            return ("", "No suggestion in the transparency REVIEW.md.", TR26_REVIEW)
        decision, note, item = hit
        return decision, note, f"{TR26_REVIEW} {item}"
    if family == "capital_sd" and fy == "2026":
        hit = CAPITAL26_BY_SUB.get((r["check_id"], r["sub_id"])) or CAPITAL26_BY_CHECK.get(r["check_id"])
        src = CAP26_REVIEW
    elif family == "terms" and fy == "2026":
        hit = TERMS26_BY_CHECK.get(r["check_id"])
        src = CAP26_REVIEW
    elif family == "capital_sd" and fy == "2027":
        hit = CAPITAL_BY_SUB.get((r["check_id"], r["sub_id"])) or CAPITAL_BY_CHECK.get(r["check_id"])
        src = CAP_REVIEW
    elif family == "terms" and fy == "2027":
        hit = TERMS_BY_CHECK.get(r["check_id"])
        src = CAP_REVIEW
    elif family == "schedule_c" and fy == "2026":
        decision, note, item = SC26_BY_ID[r["review_id"]]
        return decision, note, f"{SC26_REVIEW} {item}"
    elif family == "schedule_c" and fy == "2027":
        hit = SC_BY_ID.get(r["review_id"])
        src = SC_REVIEW
        if hit is None:
            return ("", "No suggestion in the Schedule C REVIEW.md.", src)
    else:
        raise SystemExit(f"FY{fy} {family}: no suggestion rules for this family-year")
    if hit is None:
        raise SystemExit(f"{family} {r['review_id']}: no rule for check {r['check_id']}")
    decision, note, item = hit
    assert decision in DECISIONS, decision
    return decision, note, f"{src} {item}"


def build():
    with open(os.path.join(REPO, "data", "pdf_years.csv"), newline="", encoding="utf-8") as f:
        missing = [(y["fiscal_year"], y["family"]) for y in csv.DictReader(f)
                   if (y["fiscal_year"], y["family"]) not in REVIEW_FILES]
    if missing:
        raise SystemExit(f"in data/pdf_years.csv but not in REVIEW_FILES: {missing}")
    rows = []
    for (fy, family), rel in REVIEW_FILES.items():
        with open(os.path.join(REPO, rel), newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d, note, src = suggest(fy, family, r)
                if d == page_image.DECISION:
                    # Accepting it must record a decision the readers can apply.
                    page_image.parse(note)
                    assert r.get("award_id") or r.get("row_id"), (fy, family, r["review_id"])
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
