# Draft #102 issue-log comments (NOT posted)

**Written:** 2026-10-20 22:16 EDT. One block per problem, in the order found, in the shape #102 asks
for. Each is meant to be its own comment on #102 once Noel approves. "PR" below means the PR that
adds this folder.

---

**Problem:** The capital book has no cell borders, so neither lattice can be read on Parts I and II.
**Where:** `Supporting-Detail-for-FY2027-…-Section-254.V4.pdf`, pp.4–60 and 63–71 (rotated 90°)
**Found by:** triage (`fy27_capital_sd_pages.csv`: 0 vector lines, 1–8 rects per page, all
horizontal); `grid.py` sees only the same horizontal rules (C7: 222 / 222)
**Tried:** families/capital.md §3.1's header-column prototype.
**Fix:** read every word twice, by page geometry (title lines grouped into cells by spacing, ≤ 9.24 pt
within, ≥ 14.94 pt between) and by content-stream order, and require them to agree.
`code/review_capital_sd.py`, PR.
**Status:** fixed. 23,049 words agree; 32 near disagreements all settled (below).

---

**Problem:** Titles printed above their own SUB ID line went to the wrong row (or nowhere) in a
line-by-line read.
**Where:** p.40 (`HD CC1044`, `HD CC1047` FIRST ATLANTIC TERMINAL, `HD CC1050`); the retired
`data/fy27/capital/fy27_capital_projects.csv` has these titles blank
**Found by:** grid compare is not possible here; found by viewing p.40 and by the C9 title check
**Tried:** nearest-line assignment: gives `CHLDC…` to `HD CC1047` (wrong).
**Fix:** pair title blocks with rows in order. Title equals the Council workbook on 1,210 / 1,213 rows;
the 3 misses are real text differences (next items). Golden test
`test_titles_printed_above_their_row_p40`.
**Status:** fixed

---

**Problem:** The retired FY27 capital CSV reconciles 24/26; families/capital.md §9.7 says it's a parser
error, not the PDF.
**Where:** p.40 (`HD CC0707`, `HD CC0863`), p.47 (`HR CC0168` merged into `HR CC1253`'s title)
**Found by:** totals (C1)
**Tried:** —
**Fix:** new parse ties **28 / 28** `TOTALS FOR` lines on count and all four FYs, including Housing &
Development (65, $54,135,000) and Human Resources (19, $19,483,000). PR.
**Status:** fixed here; the retired CSV and `fy27_capital_reconciliation.txt` are not edited

---

**Problem:** The PDF was edited after export. Text in other font subsets was typed in on 7 pages,
and the content stream is out of row order on 8.
**Where:** pp.34, 40, 45, 46, 47, 55, 56, 58; 10 rows (`W.edited_after_export`), e.g. p.47
`HR CC1065` sponsor gained `, LOUIS, ZHUANG`
**Found by:** geometry vs stream (C5); font census
**Tried:** stream order as the second read on those pages: it points 364 words at far rows.
**Fix:** far stream rows count as "no opinion". Near disagreements (32) keep the geometry read and are
downgraded only when the Council workbook agrees, or the word is a `0` both rows print.
**Status:** flagged in data (warn), REVIEW.md A4–A9, A12, A14, A16

---

**Problem:** Part I and Part II disagree on three sponsors.
**Where:** `HR CC1065` (p.47 vs p.65), `HR CC1059` (p.47 vs p.65), `PV CC1054` (p.58 vs p.69)
**Found by:** C3 (Part II ⊆ Part I, every field)
**Tried:** —
**Fix:** none; both kept as printed. The Part I text is the post-export edit.
**Status:** flagged in data (REVIEW.md A6, A8, A12)

---

**Problem:** Misprint: one row has no FY2030 value; its sponsor sits in the FY2030 column; the row
above ends in a stray `0`.
**Where:** p.56, `PV CC0989` (QUEENS MUSEUM ROOF REPLACEMENT, $2,500,000) and `PV CC1110`
**Found by:** C6 (one value per FY cell), first as a title holding `SPEAKER,`
**Tried:** column by word position alone put `SPEAKER,` in the title.
**Fix:** a non-amount word right of the FY 2027 header is sponsor text. FY2030 kept blank (`None`),
the stray `0` kept in `sponsor_raw`. No dollar effect (FY2030 is 0 everywhere).
**Status:** flagged in data (critical, `accepted_as_printed` suggested)

---

**Problem:** Part II has 30 rows that are not in Part I.
**Where:** pp.66–67, `PV MA1001`–`PV MA1053` on `PV 0N…` lines, $70,987,000 FY2027, no sponsor
**Found by:** C3
**Tried:** — (families/DATA-ANOMALIES §12 had called the `0N` lines a code form; they are a series)
**Fix:** none. They are in the Part II total ($210,677,000) and Part III, not in Part I, the p.61
additions, or the Council workbook. Meaning of `MA` / `0N` unconfirmed.
**Status:** open: question for Council Finance

---

**Problem:** Rescindments can't be checked.
**Where:** p.61, "Less Rescindments from Prior Capital Budgets ($23,317,000)"
**Found by:** C2
**Fix:** only the arithmetic ties: $853,688,000 − $23,317,000 = $830,371,000. No list in the book.
**Status:** flagged in data (warn)

---

**Problem:** PDF and Council workbook disagree on two project titles (same ID, line, amount).
**Where:** p.23 `E CC0598` (GYM SUPPLEMENTAL COOLING vs SCIENCE LAB UPGRADE, $1,000,000); p.36
`E CC1245` (P.S. 370 vs P.S. 199, $675,000)
**Found by:** C9 title check
**Fix:** none; kept as printed.
**Status:** open: question for Council Finance

---

**Problem:** 34 workbook rows say `Sanchez` where the PDF says `SANCHEZ J.` or `SANCHEZ P.`
**Where:** pp.13–15, 37, 39, 44, 48, 49, 53
**Found by:** C9 sponsor check
**Fix:** none. The PDF tells the two members apart; the workbook does not.
**Status:** flagged in data (warn); worth a line in `data/capital/README.md`

---

**Problem:** Retired T&C CSV drops units and mixes headings into text for multi-agency conditions.
**Where:** `FY27-FINAL-Terms-and-Conditions-6.30.26.pdf`, #64–#75 (pp.24–31); e.g. #75 prints 16
units across several agencies, old CSV keeps 5
**Found by:** T7 (compare with `data/fy27/terms/fy27_terms_and_conditions.csv`); T2 census
**Fix:** heading parsed into agency groups, each with its units and budget lines.
269 / 269 heading lines placed; the body names exactly the heading's units in 75 / 75.
`code/review_terms.py`, PR.
**Status:** fixed here; the retired CSV is not edited

---

**Problem:** Retired T&C CSV has 134 mid-word splits (`appropriatio n`).
**Where:** throughout
**Found by:** T7 split-word count (join is a word in the new text, halves are not)
**Fix:** pdfplumber text lines (the PDF stores real space characters). New text: 0 splits.
**Status:** fixed here

---

**Problem:** The FSR table splits words across cell lines in the source.
**Where:** p.8, three cells (`Su⏎mmary`, `FY 2⏎028` twice)
**Found by:** T5 cell text (identical under the vector and the image lattice: 28 / 28)
**Fix:** kept as printed, joined with a space, flagged `midword_wrap_in_source`.
**Status:** flagged in data

---

## Proposed DATA-ANOMALIES entry (not applied)

> **§NN. FY2027 capital and T&C, re-read from the PDFs (GitHub #102).** `research/2026-10-20-fy27-capital-terms-review/`.
> Capital: 28 / 28 printed totals tie; Part I equals the Council workbook on 1,215 / 1,215 non-zero
> amounts. The PDF was edited after export (sponsors added on pp.40–58, in Part I only for three rows);
> p.56 misprints one row's FY2030 cell; Part II carries 30 `MA` / `0N` rows ($70,987,000) that are not
> Council additions (meaning unconfirmed). Two titles differ from the workbook (`E CC0598`,
> `E CC1245`). The workbook's `Sanchez` is two members in the PDF. T&C: 75 conditions; the retired
> CSV dropped the second and later agencies' units in #64–#75 and has 134 mid-word splits.
> §12's `0N###` is a separate budget-line series, not a code variant.
