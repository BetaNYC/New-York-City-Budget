# FY2024 transparency resolutions, checked from the PDFs (#105)

**Report generated:** 2026-10-21 19:18 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** the 9 PDFs in `source/FY24/transparency-resolutions/` (388 pages; hashes
in `config/transparency/fy2024.toml`); expense disclosure as committed in
`data/fyNN/expense_disclosure/` (FY2024 workbook sheet "FY24 (06-08-26)", FY2023 "FY23 (07-11-2023)",
FY2022 "FY22 (07-11-2023)"); resolution numbers and adoption dates from
`research/2026-07-07-legistar-links-fy21-27.md` (read from Legistar on 2026-07-07, not
re-queried); code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #105 (epic #101). This folder is the review record. The tables are promoted to
`data/fy24/pdf/transparency/` by a separate PR. FY2024 Schedule C and capital/terms are other
sessions' work. The method is FY2026's (`research/2026-10-21-fy26-transparency-review/`) with the
FY2025 additions (`research/2026-10-21-fy25-transparency-review/`); this README says what differs.

## What these PDFs are

Same layout as FY2025 and FY2026. All 9 open with the Committee on Finance report, which prints
the date ("This Resolution, dated August 3, 2023"); none prints "Charts 1 through N". **Reso 01's
chart pages (pp.3–61) are landscape pages stored portrait with /Rotate 90.** Both readers
(pdfplumber and pdfium) read them as displayed, so the parse needs nothing special; `bbox_pt` here
is in display coordinates and the promotion turns it back into unrotated page coordinates, as the
row contract asks.

## Results

| What | Result |
|---|---|
| Rows | **3,303** (2,185 designations, 978 rescissions, 140 purpose-of-funds rows) from 329 charts on 370 chart pages. Budget years: 2024 3,085 · 2023 169 · 2022 49 |
| Printed totals | **None to tie.** 0 money amounts outside the tables (T15), and no resolution prints a chart count. The "Page n" labels count every chart page (1..n on all 9; 11 pages print none, below) |
| Image grid (independent) | **3,303 / 3,303** rows agree on every field, Reso 01's rotated pages included |
| Ink coverage | 2 small regions (160 px of 118 million), both on Reso 02 p.11: the left edge of a clipped "n" that shows before the cell border (review item). Self-test on a rotated page (Reso 01 p.3) passes |
| Anchor census | 3,302 EIN-shaped words = 3,302 rows with an EIN; 1 row prints "TF4876222" in the EIN column |
| Sign vs colour | 1,048 / 1,048 amounts in parentheses are red |
| Characters | 397,833 non-space; 0 in a table but in no cell; 2 hidden |
| Dates | All 9 print their date and it matches Legistar and the filename |
| Numbers | All 9 from Legistar (Res 0726-2023 .. Res 0484-2024) |
| Disclosure (report only) | FY2024: 1,957 of 2,072 organization designations ($50.6M) are in the disclosure on (EIN, amount); 74 of the rest were taken back later |
| Old CSV (`data/fy24/transparency-resolutions/`) | Every one of its 3,294 rows is here. It missed 9: 7 EINs printed without a hyphen (6 of them start with 0), "Bronx Community Board #7", and the "TF4876222" row |
| Review file | **19 rows** (5 critical, 14 warn), largest $20,000 (`REVIEW.md`) |

### Per resolution

| # | Res. | Adopted | Rows | Charts | Orgs + (n, $) | Orgs − (n, $) | Agency side net | Purpose rows | "Speaker" rows |
|---:|---|---|---:|---:|---|---|---:|---:|---:|
| 1 | 0726-2023 | 2023-08-03 | 790 | 45 | 515, $14,945,183 | 178, −$3,633,013 | −$11,312,170 | 36 | 18 |
| 2 | 0744-2023 | 2023-09-14 | 955 | 55 | 763, $12,764,430 | 121, −$2,262,159 | −$10,502,271 | 16 | 28 |
| 3 | 0806-2023 | 2023-10-05 | 327 | 57 | 200, $8,786,840 | 57, −$1,567,750 | −$7,219,090 | 14 | 8 |
| 4 | 0834-2023 | 2023-11-02 | 283 | 32 | 160, $6,199,562 | 90, −$2,089,024 | −$4,110,538 | 6 | 10 |
| 5 | 0864-2023 | 2023-12-20 | 214 | 33 | 108, $3,162,809 | 70, −$1,872,390 | −$1,290,419 | 8 | 8 |
| 6 | 0006-2024 | 2024-02-08 | 127 | 25 | 54, $1,322,411 | 42, −$1,192,545 | −$129,866 | 18 | 12 |
| 7 | 0305-2024 | 2024-04-11 | 370 | 32 | 250, $5,158,480 | 101, −$2,613,480 | −$2,545,000 | 16 | 15 |
| 8 | 0436-2024 | 2024-05-23 | 161 | 33 | 71, $3,073,004 | 69, −$2,247,590 | +$50,000 | 20 | 9 |
| 9 | 0484-2024 | 2024-06-30 | 76 | 17 | 35, $1,204,486 | 34, −$1,009,486 | −$195,000 | 6 | 7 |

Every resolution's designation rows net to $0 except Reso 08 (+$875,414): one-row charts
LGBTQIA+ Community Services ($794,375, p.21) and MCCAP Initiative ($60,327, p.22), plus DoVE
(+$20,000) and Food Pantries (+$712). New money, not moves. The retired file's own notes show the
same +$875,414. Reported, not flagged.

## What is new in FY2024 (and how the code handles it)

1. **"Page\xa0n"**: Reso 01 prints its page labels with a no-break space. The label reader now
   takes any space.
2. **A clipped letter that overlaps the next cell's text.** Reso 02 p.11: "Staten Island
   Delegation" is clipped at the Borough cell's border, and its "n" ends 0.95 pt *after* the
   organization ("South Shore District …") begins. The run rule joined them, so the organization
   came out empty and the whole name went to hidden text. A run now also breaks where a letter
   starts more than 0.5 pt before the last one ends (real clipped text continues within ±0.07 pt).
   Now: member "Staten Island Delegatio", hidden "n", organization read. The image grid agrees.
3. **11 chart pages with no "Page n" label** (Reso 02 pp.66–73, Reso 03 pp.55–57), all
   prior-year charts (Fiscal 2022 and 2023) sitting between the current-year charts and the
   purpose-of-funds charts; the next label counts them. As in FY2025, they look added late.
   Named exceptions.

FY2025 and FY2026 outputs are byte-identical with these changes (all data files and crops,
compared on 2026-10-21).

## Files

As in FY2025 (`fy24_` prefix): `REVIEW.md`, `ISSUE-LOG-DRAFT.md` (for #105, **not posted**),
`data/fy24_tr_rows.csv` (3,303), `fy24_tr_charts.csv` (329), `fy24_tr_resolutions.csv` (9),
`fy24_tr_review.csv` (19, same columns as `fy26_tr_review.csv`), `fy24_tr_checks.txt`,
`fy24_tr_flags.csv`, `fy24_tr_pages.csv` (has each page's `rotation`),
`fy24_tr_disclosure_match.csv`, `fy24_tr_retired_csv_compare.csv` (the 9 rows above),
`fy24_tr_manifest.json`, `data/overlays/` (19 review crops and the 2 ink spots).

## How to redo it

```
.venv/bin/python code/parse_transparency_v2.py --fy 2024      # ~1 min on a laptop CPU
.venv/bin/python -m pytest code/test_transreso.py
```

Byte-identical on re-run (checked). Every year-specific fact is in
`config/transparency/fy2024.toml`.

## What these checks cannot prove

- That a change exists which no PDF printed (no totals, and no chart counts this year).
- Text where both grids read the same wrong text layer (no OCR sample).

## Not done here

- OCR audit; rescission origins use the *retired* FY2024 Schedule C CSVs (report only).
- Nothing added to the MCP or the public site; the retired `data/fy24/transparency-resolutions/`
  files are unchanged.
