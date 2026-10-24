# FY2020 transparency resolutions, checked from the PDFs (#109)

**Report generated:** 2026-10-22 00:30 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** the 8 PDFs in `source/FY20/transparency-resolutions/` (508 pages; hashes
in `config/transparency/fy2020.toml`); expense disclosure as committed in
`data/fyNN/expense_disclosure/` (FY2020 workbook sheet "FY20 (06-16-2022)", FY2019 "FY19 (4-14-21)",
FY2018 "FY18"); resolution numbers and adoption dates from
`research/2026-07-07-legistar-links-fy15-20.md` and `data/combined/legistar_crosswalk.csv` (read
from Legistar on 2026-07-07, not re-queried; Reso 02–05 are "confirmed (positional)" there);
code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #109 (epic #101). This folder is the review record. The tables are promoted to
`data/fy20/pdf/transparency/` by a separate PR. FY2020 Schedule C and capital are other
sessions' work. The method is FY2026's, with the FY2025–FY2021 additions
(`research/2026-10-21-fy21-transparency-review/` is the closest model); this README says what
differs. The folder date is the day the FY2021/FY2020 run started.

## What these PDFs are

The same Excel charts as FY2021–FY2026, one table per landscape page. Each resolution opens with
the Committee on Finance report (it prints the date) and the resolution text, so the front runs
6–17 pages. No page carries /Rotate and every media box starts at (0, 0); none prints "Charts 1
through N". The resolution numbers are not in the crosswalk's URL column, so the config has no
`legistar_id`.

FY2020's captions are the least regular so far ("Chart", "Chart # 44", "CHART #:" with no number,
"(continued)" in the middle), and its purpose-of-funds charts carry a Source column.

## Results

| What | Result |
|---|---|
| Rows | **5,396** (3,573 designations, 1,224 rescissions, 526 purpose-of-funds rows, **73 "Beating Hearts Initiative" rows with no amount**) from 300 charts on 413 chart pages. Budget years: 2020 5,189 · 2019 175 · 2018 32 |
| Printed totals | **None to tie.** 0 money amounts outside the tables. No chart counts. The "Page n" labels count every chart page (1..n on all 8; every chart page prints one) |
| Image grid (independent) | **5,396 / 5,396** rows agree on every field |
| Ink coverage | **0 regions.** 133 loose px in all, under the region size. Self-test on Reso 01 p.13 passes |
| Anchor census | 5,396 EIN-shaped words = 5,396 rows with an EIN, page by page |
| Sign vs colour | 1,487 amounts in parentheses, all red |
| Characters | 774,878 non-space; 0 in a table but in no cell; 0 hidden |
| Dates | All 8 print their date and it matches Legistar and the filename |
| Numbers | All 8 from Legistar (Res 0998-2019 .. Res 1352-2020) |
| Disclosure (report only) | FY2020: 3,166 of 3,459 organization designations ($94.3M) are in the disclosure on (EIN, amount); 228 of the rest were taken back later |
| Old CSV (`data/fy20/transparency-resolutions/`) | Every one of its 5,319 rows is here. It missed 77: the 73 "Beating Hearts Initiative" rows and 4 EINs printed without a hyphen |
| Review file | **52 rows** (11 critical, 41 warn), largest $20,250 (`REVIEW.md`) |

### Per resolution

| # | Res. | Adopted | Rows | Charts | Orgs + (n, $) | Orgs − (n, $) | Agency side net | Purpose rows | Net, all rows |
|---:|---|---|---:|---:|---|---|---:|---:|---:|
| 1 | 0998-2019 | 2019-07-23 | 1,361 | 36 | 1,038, $22,202,023 | 152, −$2,419,665 | −$19,782,357 | 130 | +$1 |
| 2 | 1022-2019 | 2019-08-14 | 1,270 | 51 | 1,055, $33,454,356 | 144, −$7,134,675 | −$26,319,681 | 20 | $0 |
| 3 | 1059-2019 | 2019-09-25 | 1,090 | 46 | 641, $22,399,205 | 281, −$8,088,632 | −$13,950,050 | 108 | +$360,523 |
| 4 | 1155-2019 | 2019-11-14 | 573 | 58 | 216, $16,157,897 | 199, −$7,652,635 | −$8,505,263 | 94 | −$1 |
| 5 | 1198-2019 | 2019-12-19 | 570 | 43 | 322, $7,192,488 | 125, −$3,007,514 | −$2,738,277 | 78 | +$1,446,697 |
| 6 | 1228-2020 | 2020-01-23 | 176 | 16 | 115, $1,620,521 | 33, −$473,052 | −$1,147,469 | 26 | $0 |
| 7 | 1258-2020 | 2020-02-27 | 233 | 31 | 116, $3,970,809 | 75, −$2,834,694 | +$98,093 | 34 | +$1,234,208 |
| 8 | 1352-2020 | 2020-06-30 | 123 | 19 | 43, $1,769,000 | 44, −$1,769,000 | $0 | 36 | $0 |

**3 of 8 resolutions net to $0.** Three add new money: Reso 03 +$360,523 (chart #20
Discretionary Child Care), Reso 05 +$1,446,697 (chart #30 Supports for Persons Involved in the
Sex Trade, one-sided) and Reso 07 +$1,234,208 (chart #20 Bridge Program for Workforce
Development, $1,000,000, and others). Purpose-of-funds rows balance in every resolution.

**Two charts are $1 off inside themselves**, and both grids read the same digits:

- Reso 01 chart #10, Domestic Violence and Empowerment (DoVE) Initiative (pp.32–34): +$3,264,794
  against −$3,264,793.
- Reso 04 chart #11, DoVE (p.30): ten rows take back $220,815 and Mayor's Office of Criminal
  Justice gets $110,814 (with $110,000 to others), −$1 in all.

These are the PDF's own arithmetic, not a misreading. The charts print no totals, so no check
fails; they are listed in `REVIEW.md` for Noel. The old parse's notes
(`data/fy20/transparency-resolutions/fy20_transparency_reconciliation.txt`) show the same +$1 on
Reso 01 and +$2,917,358 in all (this parse: +$3,041,428); its other per-resolution nets differ
because of how it classed rows. Every old row is here.

## What is new in FY2020 (and how the code handles it)

1. **Caption variants**, rewritten before the caption is read, each a `W.caption_format` review
   item (32 pages): "Chart #35:" (Reso 01 pp.70–80, Reso 02 pp.85–86), "Chart # 44:" (Reso 03
   pp.73–87), and "SU-CASA (continued) - Fiscal 2020" with "(continued)" before the year (Reso 05
   pp.32–33, Reso 06 pp.17–18). Before this, 272 rows on 30 purpose-of-funds pages were dropped
   (T3, T5) and the image grid and ink check saw them as missing; SU-CASA "started twice".
2. **A "(continued)" caption with no number**: "CHART #: Purpose of Funds Changes - Fiscal 2020
   (continued)" (Reso 06 pp.25–26), under chart #16 of that title. The caption pattern now allows
   an empty number; such a caption is read through the FY2022 `T3.continued_number` rule (named
   exception) and otherwise fails T3.
3. **"Organization - School"** as a header label (Art a Catalyst for Change and similar, 7 pages).
4. Handled by earlier years' rules, as named exceptions: three "Beating Hearts Initiative" charts
   (no note under them this year), one first page printing "(continued)" (Reso 02 p.34), one
   caption repeated without "(continued)" (Reso 05 p.47), and 11 `***` rows on pages whose
   footnotes stop at `**` (Reso 02 pp.16, 23; Reso 04 p.20; Reso 05 p.22).

FY2021, FY2022, FY2023, FY2024, FY2025 and FY2026 outputs are byte-identical with these changes
(every tracked file in their review folders, crops included; re-run on 2026-10-22 with Python
3.12.13), apart from the known FY2026 decisions drift described in the FY2023 README.

## Files

As in FY2021 (`fy20_` prefix): `REVIEW.md`, `ISSUE-LOG-DRAFT.md` (for #109, **not posted**),
`data/fy20_tr_rows.csv` (5,396), `fy20_tr_charts.csv` (300), `fy20_tr_resolutions.csv` (8),
`fy20_tr_review.csv` (52, same columns as `fy21_tr_review.csv`), `fy20_tr_checks.txt`,
`fy20_tr_flags.csv`, `fy20_tr_pages.csv`, `fy20_tr_disclosure_match.csv`,
`fy20_tr_retired_csv_compare.csv` (the 77 rows above), `fy20_tr_manifest.json`,
`data/overlays/` (52 review crops).

## How to redo it

```
.venv/bin/python code/parse_transparency_v2.py --fy 2020      # ~1 min on a laptop CPU
.venv/bin/python -m pytest code/test_transreso.py
```

Byte-identical on re-run (checked). Every year-specific fact is in
`config/transparency/fy2020.toml`.

## What these checks cannot prove

- That a change exists which no PDF printed (no totals, and no chart counts this year).
- Text where both grids read the same wrong text layer (no OCR sample).
- What the "Beating Hearts Initiative" organizations each receive: FY2020's charts print no note
  and no amount at all.
- Resolution numbers for Reso 02–05 rest on Legistar order ("confirmed (positional)" in the
  2026-07-07 notes), not on a number printed in the PDF.

## Since this review

- Rescission origins (report only) now use the checked FY2020 Schedule C,
  `data/fy20/pdf/schedule_c/fy20_sc_awards.csv` (#204, re-run 2026-10-23): 196 → 403 match a
  Schedule C award, 218 → 93 part of a larger amount, 141 → 59 not found. The retired old-parser
  CSVs had missed or misread those awards' (EIN, amount).

## Not done here

- OCR audit.
- Nothing added to the MCP or the public site; the retired `data/fy20/transparency-resolutions/`
  files are unchanged.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` (the integrator numbers sections). Proposed text:

> ## NN. FY2020 transparency resolutions rebuilt from the PDFs, checked (#109) — REVIEW NOT STARTED
>
> > **Scope.** A new, checked parse of the 8 PDFs in `source/FY20/transparency-resolutions/`
> > (`code/parse_transparency_v2.py --fy 2020`, `config/transparency/fy2020.toml`). Its review
> > record is [`research/2026-10-21-fy20-transparency-review/`](research/2026-10-21-fy20-transparency-review/README.md).
> > The old `data/fy20/transparency-resolutions/*.csv` files are unchanged and stay the historical
> > record (§27). Not served by the MCP.
>
> **Result.** 5,396 rows from 300 charts (the old parse had 5,319, all of which are here), each
> with its resolution's number and adoption date. An independent image grid agrees on all 5,396.
> No totals and no chart counts are printed. Reso 03, 05 and 07 add new money (+$3.0M in all).
>
> **What the old parse missed.** The 73 "Beating Hearts Initiative" rows (no amount column) and 4
> EINs printed without a hyphen.
>
> **Things a re-parse must know.** Captions print "Chart" and "Chart # 44", "(continued)" before
> the fiscal year (SU-CASA), and "CHART #:" with no number (Reso 06 pp.25–26). Purpose-of-funds
> charts have a Source column and initiative names that span Source and Member. "Organization -
> School" is a header label. "Beating Hearts Initiative" charts have no amount and no note.
>
> **What the PDF itself gets wrong (flagged, never fixed).** Two DoVE charts are $1 off inside
> themselves (Reso 01 chart #10 +$1, Reso 04 chart #11 −$1: MOCJ $110,814 against $110,815
> taken back). 11 `***` rows with no `***` footnote (Reso 02 pp.16, 23; Reso 04 p.20; Reso 05
> p.22). "Millennium Development-Millennium Youth Services" printed without spaces around the
> separator (Reso 05 p.67).
