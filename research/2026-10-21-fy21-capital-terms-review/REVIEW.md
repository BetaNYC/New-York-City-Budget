# FY2021 T&C: items for Noel to review

**Generated:** 2026-10-21 23:50 EDT, from `data/fy21_terms_review.csv`. Prepared by BetaNYC with AI
assistance.

Page = PDF page (1-based). Nothing here was "fixed": every value is kept as printed. `review_id` is the
id in the review CSV.

**Short version.** FY2021 has Terms & Conditions only (no capital supporting detail in `source/`).
46 conditions, every check passes; **no critical items**. All 11 review entries are warnings, and
most of them describe the retired CSV, not the PDF. No dollars: the T&C prints no amounts.

## A. Critical

None.

## B. Decide or confirm

| # | Page | review_id | What | Suggested decision |
|---|---|---|---|---|
| 1 | 2–16 | — | **No condition numbers and no page numbers.** `item_number` is the order in the book (1..46). T1 checks it: 46 headings, 46 "As a condition" paragraphs | Accept; say so wherever `item_number` is shown for FY2021 |
| 2 | 5 | — | **#12 prints School Construction Authority with DOE's code, `(040)`**, as its second agency. Kept as printed (`agency_code` = `040; 040`) | Accept as printed. A loader must not treat the two as one agency by code |
| 3 | 2, 5, 11, 13 | — | **The retired CSV keeps only the first agency of the four two-agency conditions**: #1 lists DOC's units 001–004 under ACS's code 068; #12 loses SCA, #28 "Capital Budget", #37 DCAS. T7 compares the first agency only, so these have no review row | Use the new file. Note it in DATA-ANOMALIES |
| 4 | 2, 3, 5, 11 | `5d05f4678df0` `fe962e80c270` `247734947bdf` `a37e610f8e5f` | The retired CSV put capital budget lines into `units` (#2, #3 `HA-0001`; #12 `E2364 and E2365`; #28 `HD-0009`) | Use the new file |
| 5 | 8, 9 | `ef031011506a` `85c40ad36427` | The retired CSV folded the FSR table into #19's text and dropped the printed hyphen in #23 ("average meals per day - for breakfast") | Use the new file |

## C. Checked, no action needed (FYI)

| # | Page | review_id | What | Suggested decision |
|---|---|---|---|---|
| 1 | 5, 11 | `70be57701f90` `c11fccdc03bd` | T3: #12 names "E2364 and E2365" with no hyphen; #28 wraps `HD-` / `0009`. The check's limits; the texts are right | Accept |
| 2 | 5, 7, 11 | `36fcd3345fe1` `e66767c4964a` `45902b80e8c2` | A line ends in a hyphen and joins with none: #12 `non-functioning`, #18 `semi-annual`, #28 `HD-0009`. All three are right | Accept |
| 3 | 5 | — | #12: "2021" in "July 15, 2021" is set in Calibri, a later edit; the words read the same | Accept |
| 4 | 8 | — | The FSR table's months run SEPTEMBER 2020 to MAY 2021, in order (FY2022's copy of the table does not) | Accept |
| 5 | 16 | — | #45 prints "004,006" with no space | Accept as printed |

## D. Policy questions (not decided here)

1. Retire or keep the old `data/fy21/terms` CSV? It loses the second agency of four conditions.
2. The FY2021 capital supporting detail is being added to `source/` separately. When it lands, it gets
   its own config (`config/capital_sd/fy2021.toml`) and review, and FY2021's `capital_sd` row in
   `data/pdf_years.csv`.
