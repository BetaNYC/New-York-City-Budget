# FY2026 transparency resolutions, checked from the PDFs (#103)

**Report generated:** 2026-10-21 00:40 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** the 10 PDFs in `source/FY26/transparency-resolutions/` (544 pages; hashes
in `config/transparency/fy2026.toml`); expense disclosure as committed in
`data/fyNN/expense_disclosure/` (FY2026 workbook snapshot 2026-07-15); resolution numbers and
adoption dates from `research/2026-07-07-legistar-links-fy21-27.md` (read from Legistar on
2026-07-07, not re-queried); code at this branch's commit.
**Status:** checked, review in progress. Every check passes or is a named, listed exception.
Noel has not signed off the review file yet.

Part of #103 (epic #101). This folder is the review record. The tables are promoted to
`data/fy26/pdf/transparency/` by a separate PR. FY2026 Schedule C and FY2026 capital/terms are
other sessions' work and are not touched here.

## What these PDFs are

After the budget is adopted (June 30, 2025), the Council changes who gets the money, a batch at
a time, by resolution. Each of the 10 PDFs is one resolution: a cover page, then charts. Each
chart row is one change: money taken from an organization (amount in red parentheses), money
given to one (black), or the purpose of an award reworded (purpose-of-funds charts print the old
wording in parentheses and the new one without). The **date** of each resolution is what lets the
explorer say *when* a designation was made, and so which Speaker made a "Speaker" designation
(`viz/explorer/DESIGN-NOTES.md` item 3 on `feature/budget-explorer`).

## Results

| What | Result |
|---|---|
| Rows | **4,952** (3,025 designations, 1,308 rescissions, 619 purpose-of-funds rows) from 388 charts on 532 chart pages |
| Per resolution | 994 · 1,655 · 845 · 491 · 303 · 193 · 80 · 94 · 141 · 156 (table below) |
| Printed totals | **None to tie.** The FY2026 charts print no totals: 0 money amounts outside the tables on all 532 chart pages (T15). What *is* printed and ties: "Charts 1 through N" on the 8 resolutions that print it (8 / 8); the "Page n" labels under the charts (1..n, no gap, all 10) |
| Image grid (independent) | **4,952 / 4,952** rows agree on every field, including the 12 clipped cells |
| Ink coverage | 0 uncovered regions on 532 chart pages (18 loose px of 189 million). Self-test passes: hiding one row, or one letter, makes the check fire |
| Anchor census | 4,951 EIN-shaped words on the visible text = 4,951 rows with an EIN, page by page; 1 row prints no EIN (on the page, too) |
| Sign vs colour | 1,617 amounts in parentheses, all red; 0 disagree |
| Characters | 713,428 non-space characters; 0 in a table but in no cell; 222 hidden (13 runs), each in the review file: 157 under a neighbouring cell (12 runs), and since #196 one line drawn on top of a cell's own text on Reso 02 p.114 (65 letters, named `T7.overlaid`) |
| Dates | Reso 01 and 02 print their date ("dated August 14, 2025") and it matches; Reso 03–10 print none, so the date is the Legistar adoption date, equal to the filename date in all 10 |
| Disclosure (report only) | FY2026: 2,440 of 2,653 organization designations ($153.6M) are in the 2026-07-15 disclosure on (EIN, amount); 157 of the rest were taken back by a later resolution |
| Old CSV (`data/fy26/transparency-resolutions/`) | Every one of its 4,755 rows is here. It missed 197: 173 EINs printed without a hyphen, 21 rows on the prior-year purpose-of-funds chart of 7 resolutions (Fiscal 2025 in 6, Fiscal 2024 in 1), the 2 clipped Pilsudski rows, 1 row with no EIN |
| Review file | **26 rows** (3 critical, 23 warn; the two for Reso 02 p.114 added 2026-10-23, #196), largest $500,000 (`REVIEW.md`) |

### Per resolution

"Orgs +" / "Orgs −" are rows to and from organizations; "agency side" is the City-EIN row with no
member that parks money in, or takes it from, an agency pool.

| # | Res. | Adopted | Rows | Charts | Orgs + (n, $) | Orgs − (n, $) | Agency side net | Purpose rows | "Speaker" rows |
|---:|---|---|---:|---:|---|---|---:|---:|---:|
| 1 | 1013-2025 | 2025-08-14 | 994 | 69 | 556, $88,366,514 | 186, −$8,301,500 | −$78,731,680 | 79 | 76 |
| 2 | 1059-2025 | 2025-09-25 | 1,655 | 66 | 1,205, $39,562,766 | 168, −$5,187,904 | −$34,374,862 | 132 | 54 |
| 3 | 1100-2025 | 2025-10-29 | 845 | 72 | 429, $26,091,181 | 175, −$13,859,162 | −$12,232,019 | 166 | 63 |
| 4 | 1153-2025 | 2025-11-25 | 491 | 30 | 177, $8,572,127 | 122, −$5,083,250 | −$3,488,877 | 172 | 28 |
| 5 | 1186-2025 | 2025-12-18 | 303 | 35 | 207, $6,413,702 | 58, −$4,193,554 | −$2,220,148 | 12 | 17 |
| 6 | 0255-2026 | 2026-02-12 | 193 | 30 | 78, $3,829,031 | 58, −$3,319,756 | −$509,275 | 16 | 31 |
| 7 | 0353-2026 | 2026-03-10 | 80 | 24 | 36, $2,118,339 | 26, −$1,837,849 | −$280,490 | 12 | 17 |
| 8 | 0420-2026 | 2026-04-16 | 94 | 21 | 39, $846,219 | 33, −$528,274 | −$317,945 | 8 | 12 |
| 9 | 0479-2026 | 2026-05-20 | 141 | 22 | 65, $1,946,904 | 64, −$1,946,904 | $0 | 10 | 12 |
| 10 | 0529-2026 | 2026-06-30 | 156 | 19 | 54, $3,757,461 | 84, −$6,198,739 | +$2,441,278 | 12 | 38 |

Every resolution's designation rows net to $0 except Reso 01 (+$1,333,334). That is not an error
the PDF can show (it prints no total); it is consistent with money held back at adoption being
designated later. Reported, not flagged.

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars, with a suggested decision for each |
| `ISSUE-LOG-DRAFT.md` | #103 issue-log comments, drafted, **not posted** |
| `data/fy26_tr_rows.csv` | Every row. Contract columns (`fiscal_year`, `source_pdf`, `pdf_sha256`, `pdf_page`, `bbox_pt`, `review_id`, `flags`), `resolution_seq` / `resolution_number` / `resolution_date`, chart, `budget_fiscal_year`, clean values, the printed text (`*_raw`, `*_printed`), `hidden_text`, image check, disclosure result |
| `data/fy26_tr_charts.csv` | 388 charts: number, title, budget year, kind, pages, rows, sums |
| `data/fy26_tr_resolutions.csv` | 10 resolutions: number, date, hash, pages, charts printed / found, sums |
| `data/fy26_tr_review.csv` | The review file (PLAN §5.3 columns, plus `resolution_seq`, `row_id`) |
| `data/fy26_tr_checks.txt` | Every check and its numbers |
| `data/fy26_tr_flags.csv` | Every flag, including the routine ones |
| `data/fy26_tr_pages.csv` | Per page: caption, rows, EIN words, image lattice and ink numbers |
| `data/fy26_tr_disclosure_match.csv` | Each designation's disclosure match or reason; each rescission's origin |
| `data/fy26_tr_retired_csv_compare.csv` | Rows here that the retired CSV lacks (and the reverse, 0) |
| `data/fy26_tr_manifest.json` | Input hashes and tool versions |
| `data/overlays/` | A page crop for each review item |

## How to redo it

```
python3 -m venv .venv
.venv/bin/pip install -r code/requirements.txt -r code/requirements-cv.txt
.venv/bin/python code/parse_transparency_v2.py --fy 2026      # ~1 min on a laptop CPU
.venv/bin/python -m pytest code/test_transreso.py
```

The run is byte-identical on re-run (checked). Every year-specific fact is in
`config/transparency/fy2026.toml`. The code in `code/transreso/` sits on the Schedule C toolkit
(`code/schedc/`, `code/schedc_cv/`) and is meant for the other transparency years.

## How it works

1. **Vector grid.** pdfplumber finds each table from the PDF's own drawn borders.
2. **Text by runs.** The charts are Excel exports. Excel clips text that overflows a cell at the
   next border, but the hidden letters stay in the PDF's text layer. Reading letter by letter
   would paste them into the next cell (the old parser read Reso 08 p.19's EIN as
   `of2 G3-r7e1e6n4p7o7in6t`). So text is read in runs: letters drawn one after another with no
   gap. A run belongs to the cell it starts in; its letters past that cell's border are hidden,
   kept out of the value and recorded in `hidden_text`.
3. **Cells the grid does not draw.** On purpose-of-funds charts the rows draw no border between
   Source and Member (448 rows): the cell is split by the header's columns, each run going where
   it starts. Where a header column has no cell in a row (91 rows, 90 of them an empty `*`), the
   cell is the header column's width.
4. **Structure** by position: caption above (`CHART #n: title - Fiscal YYYY`, "(continued)"),
   header row, rows, footnotes and `Page n` below. Fiscal year and initiative come from the
   caption. A blank member is never filled from the row above.
5. **Image grid.** Each page rendered at 300 dpi; Christian Moscardi's `code/ocr/grid.py` finds the
   rules from pixels, one table region at a time. Two additions, both from pixels only: a rule drawn
   only in the header row is found in the header's pixels, and a column rule counts in a row only
   where that row's pixels show it. Rows are rebuilt from that alone and compared field by field.
6. **Ink coverage.** Every dark pixel in a chart table must be under a letter we kept or a drawn
   rule. Hidden letters are not kept, so if one were in fact visible this check would fire.
7. **Disclosure**, report only: (EIN, amount) multiset; City EIN needs a name match.

## What these checks cannot prove

- That a change exists which no PDF printed (no totals to catch it).
- Whether the Council's numbering has gaps: Reso 03–10 leave "Res. No." blank; the numbers come
  from the 2026-07-07 Legistar pass.
- Which side is right where the PDF disagrees with itself (Reso 06's "Fiscal 2023" chart).
- Text where both grids read the same wrong text layer. No OCR sample was run (ink is clean and
  the PDFs are born-digital).

## Since this review

- Rescission origins (report only) now use the checked FY2026 Schedule C,
  `data/fy26/pdf/schedule_c/fy26_sc_awards.csv` (#204, re-run 2026-10-23): no rescission's origin
  changed.

## Not done here

- OCR audit (PLAN stage 10) and the review UI (stage 11), as for FY2027.
- Nothing added to the MCP or the public site.
