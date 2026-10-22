# Draft #105 issue-log comments (NOT posted)

**Written:** 2026-10-21 19:20 EDT. One block per problem, in the order found, in the shape #105 asks
for. Each is meant to be its own comment on #105 once Noel approves. "PR" below means the PR that adds
this folder. Capital supporting detail and Terms & Conditions only.

---

**Problem:** The capital book is encrypted.
**Where:** `FY2024-Sec254-Supporting-Detail-Book_7.10.2023pwp-2.pdf`
**Found by:** `data/pdf_condition.csv` flag `encrypted`; checked with pypdf
**Tried:** opening with no password
**Fix:** none needed. AES-256 (V5 R6) with an empty user password: pdfplumber, pypdfium2 and pypdf open
it and every character extracts; ink coverage is 0. The owner flags (`/P -1052`) allow printing and
extraction for accessibility, not copying.
**Status:** flagged for Noel (PR body)

---

**Problem:** The summary page's rescindments were not read.
**Where:** p.61, "Less: Rescindments from Prior Capital Budgets ($189,969,000)"
**Found by:** C2 (a crash on a missing value)
**Fix:** the label may carry a colon. Then $839,969,000 − $189,969,000 = $650,000,000, and the additions
equal Part I. FY2025–FY2027 output unchanged. PR.
**Status:** fixed; the rescindments are unverifiable here (REVIEW A1)

---

**Problem:** Part III gave no grand total (a crash).
**Where:** pp.71–78
**Found by:** C4
**Fix:** config only: Part III amounts sit 3.6–5.2 pt left of the FY header's right edge, as FY2025's
do (`part3_amount_x1_tol = 6.0`). Then 95 / 95 organizations, grand total = Part II, 113 / 113 lines.
**Status:** fixed

---

**Problem:** 92 sponsor warnings against the comparison source.
**Where:** `data/capital/council_capital_awards.csv`, report year 2024 (from t474-a92g)
**Found by:** C9
**Fix:** t474's FY2024 accents are UTF-8 bytes read as cp437 (`Avil├⌐s`, `Vel├ízquez`), 78 rows;
config `workbook_mojibake = "utf-8"`. Then 1,227 / 1,241 sponsors agree; the other 14 are real
(12 `TECHNICAL ADJUSTMENT` vs "Technical Adjustments", one t474 typo, one t474 row missing Powers).
**Status:** flagged in data (warn), REVIEW A4–A7

---

**Problem:** 95 vector rules not seen in pixels.
**Where:** pp.71–78, between Part III organizations (0.10–0.17 pt, 50% grey)
**Found by:** C7
**Fix:** config `c7_hairline_pt = 0.25`, as FY2025: counted in one warning. Ink coverage is 0 there.
**Status:** flagged in data (warn)

---

**Problem:** A negative Part II-only row.
**Where:** p.65 `HL TA001` SEC249 ADJUSTMENT FOR THE SIUH NORTHWELL HEALTH CARDIAC IMAGING PROJ, line
`HL RN404`, −$40,000
**Found by:** C3 (critical: not in the `MA` / `0N` series)
**Fix:** none; kept as printed. It is in the Part II total and Part III.
**Status:** open: question for Council Finance (REVIEW A3)

---

**Problem:** The T&C prints no condition numbers, and the parser finds conditions by their numbers.
**Where:** `FY24-Terms-and-Conditions.pdf`, every heading ("Administration for Children's Services (068)")
**Found by:** triage (reading the bold lines on pp.2-3 before the first run)
**Fix:** config `numbered = false`: a bold agency line after body text starts the next condition,
numbered in book order. T1 then checks the count independently: 61 headings, 61 paragraphs opening
"As a condition" at the left margin. FY2025–FY2027 unchanged (they keep `N.` headings). PR.
**Status:** fixed; the numbers are ours, not the PDF's (REVIEW C1)

---

**Problem:** Heading lines the FY2025 grammar does not know (3 critical T2 items, 10 lines missed).
**Where:** p.14 `Capital Budget` after HPD's units; p.16 `Department of Transportation`,
`… Citywide Administrative Services`, `… Parks and Recreation` (no codes); p.18 DYCD (no code); p.20
`Mayoralty`, `[ 020 ]`; p.21 `Office of Criminal Justice ( 128)` in regular type, `[ 003]`; p.22
`Unit of appropriation [101]`; p.23 an agency name wrapped onto `Services (858)`
**Found by:** T2, T4.bold_in_body
**Fix:** in unnumbered mode a codeless bold line is an agency group (code blank, flagged
`T2.no_agency_code`); a centred line that is exactly "Name (code)" starts a condition even when not bold
(flagged `T2.heading_not_bold`); a codeless agency line followed by "Name (code)" before any unit is one
wrapped name; the unit regex allows `[ 003]`, `[ 020 ]` and a lower-case `appropriation`. Then
187 / 187 heading lines are placed. PR.
**Status:** fixed; 6 headings flagged (REVIEW C3, C4)

---

**Problem:** Text missing from conditions on pp.11, 16, 18, 21.
**Where:** white rectangles drawn behind heading lines
**Found by:** reading T2 output (pdfplumber's `find_tables` turned them into 4 "tables", whose text was
then left out, and T5 found no image lattice for them)
**Fix:** config `table_pages = [8, 9]`: only the FSR table's pages are searched for tables. PR.
**Status:** fixed

---

**Problem:** The retired FY2024 CSVs.
**Where:** `data/fy24/capital/fy24_capital_projects.csv`, `data/fy24/terms/fy24_terms_and_conditions.csv`
**Found by:** C9 / T7
**Fix:** none to them. Capital: the comma after `SPEAKER` dropped on 190 rows, a wrapped sponsor line
moved into the title on 9; amounts all equal. Terms: 59 rows for 61 conditions (the 4 with codeless or
non-bold headings lost, #61 split in 3), headings and the FSR table in texts, hyphens dropped.
**Status:** fixed here; the retired CSVs are not edited

## Proposed DATA-ANOMALIES entry (not applied)

> **§NN. FY2024 capital and T&C, re-read from the PDFs (GitHub #105).** `research/2026-10-21-fy24-capital-terms-review/`.
> Capital (an encrypted PDF with an empty user password): 32 / 32 printed totals tie; Part I equals NYC
> Open Data `t474-a92g` on all 1,241 amounts. t474's FY2024 accents are UTF-8 read as cp437 (78 rows).
> Part II carries 29 `MA` / `0N` rows ($61,737,000) and `HL TA001` (−$40,000 on `HL RN404`), not
> Council additions. The retired capital CSV drops the comma after `SPEAKER` (190 rows). T&C: the PDF
> prints no condition numbers; 61 conditions in book order. The retired CSV has 59 and is misnumbered
> from #44 on; 5 agency headings print no code.
