# FY2018 capital and Terms & Conditions: items for Noel to review

**Generated:** 2026-10-22 02:25 EDT, from `data/fy18_capital_sd_review.csv` and
`data/fy18_terms_review.csv`. Prepared by BetaNYC with AI assistance.

Critical first, then by dollars. Page = PDF page (1-based). Nothing here was "fixed": every value is
kept as printed. `review_id` is the id in the review CSV.

**Short version.** Capital: 1,718 rows (Part I 1,485, Part II 233). **All 35 printed totals tie**
($575,000,000 FY2018 in Part I), and Parts II and III tie to Part I. **There is nothing else to check the
amounts against**: no Council workbook and no Open Data for FY2018. **3 critical items**: three `TA` rows
in Part II only. T&C: 33 conditions, 0 critical.

## A. Critical

| # | $ (FY2018) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 1,093,000 | 72, 80 | `42492ceceb7d` `187ddcc76d8e` `9bf6c42e89cf` | Part II **`AG TA001`** `AG DN865` CONSELYA BLOCK ASSOCIATION/211 AINSLIE $500,000; **`HH TA001`** `HH DN106` COALITION OF THE HOMLESS 2ND FLOOR RENOVATION $693,000; **`HH TA003`** `HH MN336` PROJECT RENEWAL **−$100,000** | In Part II (and its totals) but not in Part I, and not in the `MA` / `0N` series. No sponsor. `TA` = Technical Adjustment in the Council's t474 dictionary (for later years). Net $1,093,000 | Accept as printed; ask Council Finance what the three are (needs_info). Note the negative amount and the typo `HOMLESS` |

## B. Decide or confirm (by dollars)

| # | $ (FY2018) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 575,000,000 | 4–70 | — | All of Part I | **No outside source.** Every amount stands on the book's own totals (35 / 35), Part II (178 rows re-printed, every field equal) and Part III (170 / 170 lines). Nothing contradicts it; nothing independent confirms it | Accept as the record of FY2018 (`data/capital/README.md` and §26 call FY2018 "in no source found"). Whether it enters `data/capital/` is D1 |
| 2 | 32,189,000 | 72–83 | `3c7ffca64663` | 52 Part II `MA` rows on `0N` lines | Not in Part I, no sponsor, in Part II's totals; the FY2027 pattern | Accept as printed; meaning of `MA` / `0N` unconfirmed (as FY2027) |
| 3 | 5,000,000 | 43–44 | 15 `C6.sponsor_seat` (`0bff42c8a1f9` … `6026be0cb2ef`) | `E CN765`–`E CN779`, Queens schools | Sponsor printed **`DISTRICT 28`**, a seat, not a member | Accept as printed; the explorer can show it as is |
| 4 | — | 15 (T&C) | `bac83e7e0d7c` | FSR table, last row | "Summary" is printed 1.7 pt **below the table's bottom rule**; read into the last row ("FY18 FSR update; FY19 Executive Budget Summary"). Columns 3 and 4 are printed **"Anticipated Meeting Date", "Issue Date"** (other years: Issue Date first); read as printed. All dates "TBD" | Accept |
| 5 | — | 18 (T&C) | `e85955a5930b` | #17 DOE (040) + **School Construction Authority (040)**, `E2360 – All Projects` | SCA printed with DOE's code; T3 cannot read "budget line E2360" (no hyphen) | Accept as printed |

## C. Checked, no action needed (FYI)

- **Capital, 30 row flags** (26 "nearest row", 4 sponsor wrapped below the row; pp.5–82). Two reads
  agree on every word. Spot-checked `PV NC005` (p.8, a three-line sponsor) on the page image.
- **Capital, `HN CN014`** CUNY-WIDE COMMUNITY COLLEGES is on borough `A` (p.5).
- **Capital, 138 Part III hairlines** below pixel size (`ed0bba0e4270`).
- **T&C, 3 line-end hyphens joined** (#12 `2017-2018`, #15 `non-Department`, #32 `direct-managed`): the
  retired CSV dropped the last two.
- **T&C, 8 T7 warnings:** the retired CSV folded the FSR table into #14, and filed budget-line
  headings as units (#2–#5, #17).

## D. Policy questions (not decided here)

1. **FY2018 into `data/capital/`?** The PDF is the only source for FY2018 Council capital. Promote it
   only as `data/fy18/pdf/capital_sd/` (this stack), or also add it to `council_capital_awards.csv` with
   `source_kind = pdf`?
2. Retire the old `data/fy18/terms` CSV once this is closed?
3. Is FY2018's Resolution A book (not in `source/`) worth finding (`families/capital.md` Q4)?
