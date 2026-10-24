# FY2021 transparency resolutions, checked from the PDFs (#108)

**Report generated:** 2026-10-21 23:55 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** the 8 PDFs in `source/FY21/transparency-resolutions/` (404 pages; hashes
in `config/transparency/fy2021.toml`); expense disclosure as committed in
`data/fyNN/expense_disclosure/` (FY2021 workbook sheet "FY21 (06-23-2023)", FY2020 "FY20 (06-16-2022)",
FY2019 "FY19 (4-14-21)"); resolution numbers and adoption dates from
`research/2026-07-07-legistar-links-fy21-27.md` and `data/combined/legistar_crosswalk.csv` (read
from Legistar on 2026-07-07, not re-queried); code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #108 (epic #101). This folder is the review record. The tables are promoted to
`data/fy21/pdf/transparency/` by a separate PR. FY2021 Schedule C and capital/terms are other
sessions' work. The method is FY2026's, with the FY2025–FY2022 additions
(`research/2026-10-21-fy22-transparency-review/` is the closest model); this README says what
differs.

## What these PDFs are

The same Excel charts as FY2022–FY2026, one table per landscape page. Each resolution opens with
the Committee on Finance report (it prints the date) and the resolution text, so the front runs
6–15 pages. No page carries /Rotate and every media box starts at (0, 0); none prints "Charts 1
through N". The last chart of four resolutions is a portrait "Beating Hearts" page.

FY2021 is the most regular year so far: one new footnote wording, and nothing else the FY2022
reader did not already handle.

## Results

| What | Result |
|---|---|
| Rows | **4,500** (3,397 designations, 759 rescissions, 316 purpose-of-funds rows, **28 "Beating Hearts" rows with no amount**) from 237 charts on 324 chart pages. Budget years: 2021 4,374 · 2020 110 · 2019 16 |
| Printed totals | **None to tie.** 0 money amounts outside the tables, except the 4 "Beating Hearts" notes ("$175,000", below). No chart counts. The "Page n" labels count every chart page (1..n on all 8; 15 pages print none) |
| Image grid (independent) | **4,500 / 4,500** rows agree on every field |
| Ink coverage | **0 regions.** 12 loose px in all, under the region size. Self-test on Reso 01 p.16 passes |
| Anchor census | 4,499 EIN-shaped words = 4,499 rows with an EIN, page by page; 1 row prints no EIN (review item) |
| Sign vs colour | 917 amounts in parentheses, all red |
| Characters | 610,926 non-space; 0 in a table but in no cell; 0 hidden |
| Dates | All 8 print their date and it matches Legistar and the filename |
| Numbers | All 8 from Legistar (Res 1394-2020 .. Res 1693-2021) |
| Disclosure (report only) | FY2021: 3,094 of 3,335 organization designations ($103.6M) are in the disclosure on (EIN, amount); 158 of the rest were taken back later |
| Old CSV (`data/fy21/transparency-resolutions/`) | Every one of its 4,463 rows is here. It missed 37: the 28 "Beating Hearts" rows, 8 EINs printed without a hyphen, and the blank-EIN row |
| Review file | **21 rows** (1 critical, 20 warn), largest $10,000 (`REVIEW.md`) |

### Per resolution

| # | Res. | Adopted | Rows | Charts | Orgs + (n, $) | Orgs − (n, $) | Agency side net | Purpose rows | "Speaker" rows |
|---:|---|---|---:|---:|---|---|---:|---:|---:|
| 1 | 1394-2020 | 2020-08-27 | 2,432 | 54 | 2,197, $53,731,596 | 108, −$2,351,450 | −$51,380,146 | 62 | 8 |
| 2 | 1433-2020 | 2020-09-23 | 709 | 42 | 541, $22,436,584 | 89, −$3,974,362 | −$18,462,222 | 30 | 6 |
| 3 | 1470-2020 | 2020-10-29 | 255 | 34 | 156, $6,026,406 | 59, −$1,549,886 | −$4,476,520 | 18 | 0 |
| 4 | 1480-2020 | 2020-11-19 | 184 | 15 | 90, $1,384,930 | 54, −$554,930 | −$830,000 | 26 | 2 |
| 5 | 1509-2020 | 2020-12-17 | 232 | 27 | 107, $3,114,256 | 86, −$2,743,256 | −$371,000 | 24 | 10 |
| 6 | 1544-2021 | 2021-02-25 | 218 | 27 | 99, $2,660,765 | 60, −$1,631,325 | −$529,440 | 40 | 9 |
| 7 | 1603-2021 | 2021-04-22 | 315 | 23 | 134, $20,000,244 | 101, −$2,290,244 | −$710,000 | 68 | 10 |
| 8 | 1693-2021 | 2021-06-30 | 155 | 15 | 54, $644,800 | 53, −$644,800 | $0 | 48 | 6 |

**6 of 8 resolutions net to $0** (organizations plus the agency side). Two add new money:
**Reso 06 +$500,000** (chart #22 Lien Sale Outreach and Assistance Initiative, one-sided) and
**Reso 07 +$17,000,000** (chart #11 Food Pantries Initiative, $16,000,000 over 17 rows with no
agency side, and chart #19 Educational Programs for Students, $1,000,000). Purpose-of-funds rows
balance in every resolution. The old parse's notes
(`data/fy21/transparency-resolutions/fy21_transparency_reconciliation.txt`) show +$17,480,000 in
all, with small nets in Reso 02 (+$10,000), 03 (−$60,000), 05 (−$10,000) and 07 (+$17,040,000);
this parse nets those to $0 and $17,000,000, and its rows contain every old row, so the old
nets came from how it classed rows, not from missing ones. Reported, not flagged.

## What is new in FY2021 (and how the code handles it)

1. **A third wording of the `***` footnote**: "*** Technical adjustment to designation made in a
   previous Transparency Resolution." (Reso 02–07, 14 pages, 34 rows). Added to
   `transreso.structure.FOOTNOTES`; before that, T6 reported 14 lines of unexpected text and T11
   34 `***` rows without their footnote.
2. Nothing else. The FY2022 additions cover the rest: "Beating Hearts" no-amount charts (4,
   `T4.no_amount`), a first page printing "(continued)" (Reso 02 p.20, `T3.continued_start`),
   and chart pages with no "Page n" label (15, `T3.page_label`). Each is a named exception.

FY2022, FY2023, FY2024, FY2025 and FY2026 outputs are byte-identical with this change (every
tracked file in their review folders, crops included; re-run on 2026-10-21 with Python 3.12.13),
apart from the known FY2026 decisions drift described in the FY2023 README.

## Files

As in FY2022 (`fy21_` prefix): `REVIEW.md`, `ISSUE-LOG-DRAFT.md` (for #108, **not posted**),
`data/fy21_tr_rows.csv` (4,500), `fy21_tr_charts.csv` (237), `fy21_tr_resolutions.csv` (8),
`fy21_tr_review.csv` (21, same columns as `fy22_tr_review.csv`), `fy21_tr_checks.txt`,
`fy21_tr_flags.csv`, `fy21_tr_pages.csv`, `fy21_tr_disclosure_match.csv`,
`fy21_tr_retired_csv_compare.csv` (the 37 rows above), `fy21_tr_manifest.json`,
`data/overlays/` (21 review crops).

## How to redo it

```
.venv/bin/python code/parse_transparency_v2.py --fy 2021      # ~1 min on a laptop CPU
.venv/bin/python -m pytest code/test_transreso.py
```

Byte-identical on re-run (checked). Every year-specific fact is in
`config/transparency/fy2021.toml`.

## What these checks cannot prove

- That a change exists which no PDF printed (no totals, and no chart counts this year).
- Text where both grids read the same wrong text layer (no OCR sample).
- What the "Beating Hearts" organizations each receive (the PDF names none per row).

## Since this review

- Rescission origins (report only) now use the checked FY2021 Schedule C,
  `data/fy21/pdf/schedule_c/fy21_sc_awards.csv` (#204, re-run 2026-10-23): 251 → 256 match a
  Schedule C award, 52 → 48 part of a larger amount, 39 → 38 not found. The retired old-parser CSVs
  had missed or misread those awards' (EIN, amount).

## Not done here

- OCR audit.
- The "Beating Hearts" note is bold italic, and the text layer gives it no spaces between words
  ("***StatenIslandHeartSociety,Inc.hasreceived$175,000…"), so the review file quotes it that
  way. It is not a table cell and no row value depends on it.
- Nothing added to the MCP or the public site; the retired `data/fy21/transparency-resolutions/`
  files are unchanged.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` (the integrator numbers sections). Proposed text:

> ## NN. FY2021 transparency resolutions rebuilt from the PDFs, checked (#108) — REVIEW NOT STARTED
>
> > **Scope.** A new, checked parse of the 8 PDFs in `source/FY21/transparency-resolutions/`
> > (`code/parse_transparency_v2.py --fy 2021`, `config/transparency/fy2021.toml`). Its review
> > record is [`research/2026-10-21-fy21-transparency-review/`](research/2026-10-21-fy21-transparency-review/README.md).
> > The old `data/fy21/transparency-resolutions/*.csv` files are unchanged and stay the historical
> > record (§27). Not served by the MCP.
>
> **Result.** 4,500 rows from 237 charts (the old parse had 4,463, all of which are here), each
> with its resolution's number and adoption date. An independent image grid agrees on all 4,500.
> No totals and no chart counts are printed. 6 of 8 resolutions net to $0; Reso 06 adds $500,000
> and Reso 07 $17,000,000 (mostly the Food Pantries Initiative).
>
> **What the old parse missed.** The 28 "Beating Hearts" rows (no amount column), 8 EINs printed
> without a hyphen, and one row with no EIN.
>
> **Things a re-parse must know.** The `***` footnote has a third wording ("Technical adjustment
> to designation made in a previous Transparency Resolution"). "Beating Hearts" charts have no
> amount. Reso 02 p.20 prints "(continued)" on a chart's first page. 15 chart pages print no
> "Page n" label.
>
> **What the PDF itself gets wrong (flagged, never fixed).** A row with no member and no EIN,
> "Department of Cultural Affairs **" ($10,000) DCLA (Reso 02 p.29).
