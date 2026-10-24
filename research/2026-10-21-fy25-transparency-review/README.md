# FY2025 transparency resolutions, checked from the PDFs (#104)

**Report generated:** 2026-10-21 19:00 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** the 13 PDFs in `source/FY25/transparency-resolutions/` (395 pages; hashes
in `config/transparency/fy2025.toml`); expense disclosure as committed in
`data/fyNN/expense_disclosure/` (FY2025 workbook sheet "FY25 (09-14-26)", FY2024 "FY24 (06-08-26)",
FY2023 "FY23 (07-11-2023)"); resolution numbers and adoption dates from
`research/2026-07-07-legistar-links-fy21-27.md` and `data/combined/legistar_crosswalk.csv` (read
from Legistar and council.nyc.gov on 2026-07-07, not re-queried); code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #104 (epic #101). This folder is the review record. The tables are promoted to
`data/fy25/pdf/transparency/` by a separate PR. FY2025 Schedule C and FY2025 capital/terms are
other sessions' work and are not touched here. The method is FY2026's
(`research/2026-10-21-fy26-transparency-review/`); this README says what differs.

## What these PDFs are

Same as FY2026: after the budget is adopted (June 30, 2024), the Council changes who gets the
money by resolution. Each of the 13 PDFs is one resolution: one or two front pages, then Excel
charts, one table per page. A row is money taken from an organization (red, in parentheses),
given to one (black), or the purpose of an award reworded (purpose-of-funds charts). Reso 01–10
open with the Committee on Finance report, which prints the date ("This Resolution, dated
August 15, 2024"). Reso 11–13 open with the resolution text instead: no date, "Res. No." left
blank, and "as set forth in Charts 1 through N".

## Results

| What | Result |
|---|---|
| Rows | **3,555** (2,360 designations, 1,004 rescissions, 191 purpose-of-funds rows) from 309 charts on 374 chart pages. Budget years: 2025 3,413 · 2024 108 · 2023 34 |
| Printed totals | **None to tie.** 0 money amounts outside the tables on all 374 chart pages (T15). What *is* printed and ties: "Charts 1 through N" on the 3 resolutions that print it (18, 33, 14: **3 / 3**); the "Page n" labels under the charts (1..n on every resolution; 3 chart pages print none, below) |
| Image grid (independent) | **3,555 / 3,555** rows agree on every field, including the hidden text |
| Ink coverage | 0 uncovered regions on 374 chart pages (42 loose px of 131 million). Self-test on Reso 01 p.60 passes: hiding one row, or one letter, makes the check fire |
| Anchor census | 3,553 EIN-shaped words on the visible text = 3,553 rows with an EIN, page by page; 2 rows print no EIN (on the page, too) |
| Sign vs colour | 1,097 amounts in parentheses, all red; 0 disagree |
| Characters | 442,330 non-space characters; 0 in a table but in no cell; 383 hidden (11 runs), each in the review file |
| Dates | Reso 01–10 print their date and it matches; Reso 11–13 print none, so the date is the Legistar adoption date. All 13 equal the filename date |
| Numbers | 12 of 13 from Legistar. **Reso 04 (2024-10-23) has none**: the PDF prints none and the 2026-07-07 pass could not find it in Legistar. Its rows carry `resolution_date` but a blank `resolution_number` (review item) |
| Disclosure (report only) | FY2025: 2,067 of 2,256 organization designations ($90.6M) are in the disclosure on (EIN, amount); 149 of the rest were taken back by a later resolution |
| Old CSV | **None.** The old parser never read FY2025 (`data/fy25/` has no transparency folder), so there is nothing to compare |
| Review file | **40 rows** (7 critical, 33 warn), largest $1,500,000 (`REVIEW.md`) |

### Per resolution

"Orgs +" / "Orgs −" are rows to and from organizations; "agency side" is the City-EIN row with no
member that parks money in, or takes it from, an agency pool.

| # | Res. | Adopted | Rows | Charts | Orgs + (n, $) | Orgs − (n, $) | Agency side net | Purpose rows | "Speaker" rows |
|---:|---|---|---:|---:|---|---|---:|---:|---:|
| 1 | 0517-2024 | 2024-08-15 | 738 | 44 | 409, $20,386,380 | 241, −$4,388,380 | −$15,998,000 | 56 | 29 |
| 2 | 0559-2024 | 2024-09-12 | 1,108 | 46 | 960, $42,812,684 | 82, −$2,430,674 | −$40,382,010 | 16 | 40 |
| 3 | 0597-2024 | 2024-10-10 | 213 | 25 | 100, $3,314,665 | 71, −$1,066,000 | −$2,248,665 | 26 | 18 |
| 4 | *(none found)* | 2024-10-23 | 27 | 9 | 16, $1,442,735 | 2, −$148,250 | −$1,294,485 | 0 | 0 |
| 5 | 0641-2024 | 2024-11-13 | 260 | 29 | 149, $7,783,961 | 75, −$3,343,961 | −$4,440,000 | 12 | 4 |
| 6 | 0677-2024 | 2024-12-05 | 188 | 22 | 110, $13,006,917 | 42, −$3,076,517 | −$4,880,400 | 14 | 53 |
| 7 | 0712-2025 | 2025-01-23 | 340 | 23 | 276, $5,493,500 | 42, −$1,060,500 | −$4,433,000 | 11 | 22 |
| 8 | 0732-2025 | 2025-02-13 | 165 | 21 | 86, $4,538,837 | 68, −$1,529,503 | −$3,009,334 | 4 | 8 |
| 9 | 0791-2025 | 2025-03-12 | 107 | 22 | 45, $1,305,895 | 45, −$1,436,541 | +$130,646 | 8 | 16 |
| 10 | 0815-2025 | 2025-03-26 | 7 | 3 | 2, $110,000 | 3, −$110,000 | $0 | 2 | 3 |
| 11 | 0849-2025 | 2025-04-24 | 142 | 18 | 46, $820,547 | 48, −$1,063,299 | +$242,752 | 32 | 2 |
| 12 | 0875-2025 | 2025-05-28 | 174 | 33 | 76, $3,067,359 | 75, −$2,439,359 | −$628,000 | 6 | 14 |
| 13 | 0959-2025 | 2025-06-30 | 86 | 14 | 36, $2,107,926 | 31, −$1,116,756 | −$991,170 | 4 | 17 |

Every resolution's designation rows net to $0 except Reso 06 (+$5,050,000). Most of that is chart
#4, Speaker's Initiative to Address Citywide Needs (p.6, +$8,915,400, almost all rows marked `**`,
"requires a budget modification"), i.e. new money rather than money moved. The PDF prints no total,
so this is reported, not flagged.

## What is new in FY2025 (and how the code handles it)

1. **Staff notes printed past the table.** Reso 07 pp.29–30: four purpose-of-funds rows carry a
   note in a column to the right of the `*` column, past the table's right rule and off the page:
   "01/22; placeholder - program name & Purpose fo funds change" and "01/22; DCLA: We checked
   Midori’s final CDF report and they did do activity at PS536X so that change is ok. ; proram
   name & POF change as per CBO's request". Only "01/" shows on the page, in the `*` column.
   The reader did not count these letters at first (they start in a `*` cell the PDF does not
   draw). Now a run that starts in an undrawn cell is cut at the table's edge, like any clipped
   run: `prequal_printed` = "01/" (what shows), the rest in `hidden_text`. On p.30 the `*`
   column's right rule is drawn in the top rows only, so the image grid dropped the column; it
   now also looks for a header rule right of its last column, where a data row has text there.
2. **Three chart pages print no "Page n" label** (Reso 02 pp.74–75, Reso 03 p.28), and the next
   label counts them (p.76 is "Page 74"). Named exceptions in the config.
3. **"CHART #4 Anti-Poverty"** (Reso 11 p.6) prints no colon. Read as chart #4; listed.
4. **"Member/Borough"** header (Reso 08 p.12), a new spelling of the member column.
5. **No Member column** on the "Art a Catalyst for Change" charts (as in FY2026). Reso 02 prints
   the same two Black Spectrum rows under Fiscal 2025, 2024 and 2023 (charts #17, #43, #44).

FY2026's output is byte-identical with these changes (all 10 data files and the 24 crops,
compared on 2026-10-21).

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars, with a suggested decision for each |
| `ISSUE-LOG-DRAFT.md` | #104 issue-log comments, drafted, **not posted** |
| `data/fy25_tr_rows.csv` | Every row (same columns as FY2026: the row contract, `resolution_seq` / `resolution_number` / `resolution_date`, chart, `budget_fiscal_year`, clean and printed values, `hidden_text`, image check, disclosure) |
| `data/fy25_tr_charts.csv` | 309 charts |
| `data/fy25_tr_resolutions.csv` | 13 resolutions |
| `data/fy25_tr_review.csv` | The review file (same columns as `fy26_tr_review.csv`) |
| `data/fy25_tr_checks.txt` | Every check and its numbers |
| `data/fy25_tr_flags.csv` | Every flag, including the routine ones |
| `data/fy25_tr_pages.csv` | Per page: caption, rows, EIN words, image grid and ink numbers |
| `data/fy25_tr_disclosure_match.csv` | Each designation's disclosure match or reason; each rescission's origin |
| `data/fy25_tr_retired_csv_compare.csv` | Empty: no retired file for FY2025 |
| `data/fy25_tr_manifest.json` | Input hashes and tool versions |
| `data/overlays/` | A page crop for each review item |

## How to redo it

```
python3 -m venv .venv
.venv/bin/pip install -r code/requirements.txt -r code/requirements-cv.txt
.venv/bin/python code/parse_transparency_v2.py --fy 2025      # ~1 min on a laptop CPU
.venv/bin/python -m pytest code/test_transreso.py
```

Byte-identical on re-run (checked). Every year-specific fact is in
`config/transparency/fy2025.toml`.

## What these checks cannot prove

- That a change exists which no PDF printed (no totals to catch it).
- Reso 04's resolution number, and whether the Council's numbering has gaps.
- Whether the three identical Black Spectrum charts are three changes or one printed three times.
- Text where both grids read the same wrong text layer (no OCR sample; the PDFs are born-digital
  and ink is clean).

## Since this review

- Rescission origins (report only) now use the checked FY2025 Schedule C,
  `data/fy25/pdf/schedule_c/fy25_sc_awards.csv` (#204, re-run 2026-10-23): no rescission's origin
  changed.

## Not done here

- OCR audit (PLAN stage 10), as for FY2026 and FY2027.
- 8 hyphenless EINs are read as printed (flag `W.ein_no_hyphen`); not in the review file.
- Nothing added to the MCP or the public site.
