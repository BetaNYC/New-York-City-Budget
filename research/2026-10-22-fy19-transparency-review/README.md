# FY2019 transparency resolutions, checked from the PDFs (#110)

**Report generated:** 2026-10-22 01:35 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** the 11 PDFs in `source/FY19/transparency-resolutions/` (733 pages; hashes
in `config/transparency/fy2019.toml`); expense disclosure as committed in
`data/fyNN/expense_disclosure/`; resolution numbers and adoption dates from
`research/2026-07-07-legistar-links-fy15-20.md` and `data/combined/legistar_crosswalk.csv` (read
from Legistar on 2026-07-07, not re-queried; Reso 03–05 and 07–10 are "confirmed (positional)"
there); code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #110 (epic #101). This folder is the review record. The tables are promoted to
`data/fy19/pdf/transparency/` by a separate PR. FY2019 Schedule C and capital are other
sessions' work. The method is FY2026's, with the FY2025–FY2020 additions
(`research/2026-10-21-fy20-transparency-review/` is the closest model); this README says what
differs.

## What these PDFs are

The same Excel charts as FY2020–FY2026, one table per landscape page, with `Agy #` and `U/A`
columns on designation charts. Each resolution opens with the Committee on Finance report (it
prints the date) and the resolution text. No page carries /Rotate and every media box starts at
(0, 0); none prints "Charts 1 through N". Reso 03 p.83 ("Beating Hearts") is a legal-size
portrait page. The crosswalk has no Legistar URL for FY2019, so the config has no `legistar_id`.

Three things are new this year:

- **Overfull cells** (21 pages, Reso 03, 04, 07). A name or purpose wraps to more lines than its
  row is tall, and Excel draws the whole block centred on the row, across the rules above and
  below it. On the page the text overlaps the next row or is cut off. The old reading put the
  overflow in the wrong row: "IGnrce.enwich House" (Reso 07 p.27, row 16's "Inc." on top of row
  17's first line), or dropped it ("… Public School" without "67K" under Reso 04 p.49's last row).
  The image grid agreed, because it reads the same text layer the same way.
- **"CHART 1:"** with no "#" is the house style of Reso 01–07 and 11 (484 pages).
- **Reso 01 p.1 prints "dated July 17, 2018"**; Legistar has the adoption on 2018-07-18.

## Results

| What | Result |
|---|---|
| Rows | **7,207** (4,906 designations, 1,553 rescissions, 636 purpose-of-funds rows, **112 "Beating Hearts Initiative" rows with no amount**) from 445 charts on 592 chart pages. Budget years: 2019 6,492 · 2018 411 · 2017 304 |
| Printed totals | **None to tie.** 0 money amounts outside the tables. No chart counts. The "Page n" labels count every chart page (1..n on all 11; one label, Reso 03 p.55, is printed on top of a footnote and counted by the labels around it) |
| Image grid (independent) | **7,207 / 7,207** rows agree on every field |
| Ink coverage | **0 regions.** Self-test on Reso 01 p.18 passes |
| Anchor census | 7,204 EIN-shaped words = 7,204 rows with an EIN, page by page; 3 rows print no readable EIN (review) |
| Sign vs colour | 1,871 amounts in parentheses, all red |
| Characters | 1,013,479 non-space; 0 in a table but in no cell; 0 hidden; 2,475 drawn across a row rule on 21 named pages |
| Dates | All 11 print their date; 10 match Legistar and the filename, Reso 01 is a day earlier (named exception) |
| Numbers | All 11 from Legistar (Res 0457-2018 .. Res 0964-2019) |
| Disclosure (report only) | FY2019: 4,041 of 4,585 organization designations ($140.7M) are in the disclosure on (EIN, amount); 484 of the rest were taken back later |
| Old CSV (`data/fy19/transparency-resolutions/`) | Every one of its 7,090 rows is here. It missed 117: the 112 "Beating Hearts Initiative" rows, Reso 01's two "All Allocations" rows (EIN "Various"), 2 EINs printed without a hyphen and 1 with a hidden tab glyph |
| Review file | **52 rows** (7 critical, 45 warn), largest $4,090,000 (`REVIEW.md`) |

### Per resolution

| # | Res. | Adopted | Rows | Charts | Orgs + (n, $) | Orgs − (n, $) | Agency side net | Purpose rows | Net, all rows |
|---:|---|---|---:|---:|---|---|---:|---:|---:|
| 1 | 0457-2018 | 2018-07-18 | 1,704 | 57 | 1,450, $50,583,906 | 118, −$4,427,558 | −$46,156,348 | 88 | $0 |
| 2 | 0472-2018 | 2018-08-08 | 1,604 | 45 | 1,244, $31,366,276 | 110, −$7,940,557 | −$23,570,718 | 166 | −$144,999 |
| 3 | 0537-2018 | 2018-09-26 | 1,118 | 45 | 848, $24,283,285 | 130, −$5,343,990 | −$18,939,295 | 50 | $0 |
| 4 | 0579-2018 | 2018-10-31 | 596 | 46 | 283, $8,321,012 | 221, −$5,441,187 | −$2,839,825 | 74 | +$40,000 |
| 5 | 0652-2018 | 2018-12-11 | 925 | 100 | 430, $15,158,925 | 398, −$14,920,305 | +$46,380 | 74 | +$285,000 |
| 6 | 0674-2018 | 2018-12-20 | 89 | 21 | 50, $2,845,260 | 25, −$817,500 | −$127,760 | 10 | +$1,900,000 |
| 7 | 0722-2019 | 2019-01-24 | 339 | 23 | 216, $3,058,761 | 73, −$913,761 | −$2,145,000 | 48 | $0 |
| 8 | 0763-2019 | 2019-02-28 | 349 | 46 | 147, $4,631,156 | 122, −$3,509,776 | −$271,380 | 78 | +$850,000 |
| 9 | 0805-2019 | 2019-03-28 | 285 | 29 | 130, $24,517,236 | 118, −$5,703,767 | −$17,213,469 | 18 | +$1,600,000 |
| 10 | 0846-2019 | 2019-04-18 | 131 | 22 | 62, $1,827,733 | 56, −$1,856,673 | +$28,940 | 12 | $0 |
| 11 | 0964-2019 | 2019-06-19 | 67 | 11 | 26, $1,137,440 | 22, −$1,108,500 | −$28,940 | 18 | $0 |

**5 of 11 resolutions net to $0.** Five add new money: Reso 04 +$40,000, Reso 05 +$285,000
(chart #36 Crisis Management System), Reso 06 +$1,900,000 (seven one-sided charts, the largest
chart #7 Educational Programs for Students $600,000), Reso 08 +$850,000 (chart #18 Educational
Programs for Students) and Reso 09 +$1,600,000 (chart #13 New York Immigrant Family Unity
Project). **Reso 02 takes back $144,999 more than it gives**: chart #5 A Greener NYC −$70,000 and
chart #12 Parks Equity Initiative −$75,000 have no matching designation, and chart #8 is $1 off.
Purpose-of-funds rows balance in every resolution.

**One chart is $1 off inside itself**, and both grids read the same digits: Reso 02 chart #8,
Domestic Violence and Empowerment (DoVE) Initiative (pp.33–37), +$4,546,229 against
−$4,546,228. The PDF's own arithmetic, as FY2020's two DoVE slips; listed in `REVIEW.md`.

The old parse's notes (`data/fy19/transparency-resolutions/fy19_transparency_reconciliation.txt`)
give other nets for Reso 02 (+$37,001), 03 (−$12,000) and 07 (−$15,000). Each difference is a
row it missed: Reso 02 the DOHMH row with a hyphenless City EIN (−$182,000), Reso 03 Himalayan
Elders Project (+$12,000), Reso 07 Conscientious Musical Revues (+$15,000).

## What is new in FY2019 (and how the code handles it)

1. **Overfull cells**, read as one block per cell (`transreso.reader`, docstring item 4), only
   on pages the config names (`T7.overfull`, 21 pages). A cell's lines are runs drawn one after
   another, each next line starting at the block's left edge one line lower; the block goes to
   the row holding its vertical middle. Some rows are drawn column by column, so a line joins a
   block across a rule only if it and the block both cross a rule. The image grid does the same
   on its own lattice. On the 21 pages this changes 43 rows (all checked by hand, before and
   after); 33 rows draw text across a rule and are `T7.overfull` review items. A new part of T7
   fails if any page draws text across a rule and is not named, or a named page has none.
   FY2020–FY2026 have no such page.
2. **`caption_no_hash = true`** on a resolution: "CHART n:" is its house style and is not a
   review item. The three odd captions left (Reso 02 p.32 no colon, Reso 09 p.23 "CHART # 7:",
   Reso 10 p.15 "CHART 7:" among "CHART #n:") still are.
3. **A caption printing the wrong chart number** (`T3.chart_number`, named exception with the
   printed and the read number): Reso 01 p.108 prints "CHART 55: Purpose of Funds Changes -
   Fiscal 2018"; #55 is the Fiscal 2019 chart (pp.104–107), and pp.109–111 print "CHART 56: …
   Fiscal 2018 (continued)". Read as the first page of #56.
4. **A printed date one day before Legistar's** (`T13.printed_date`, named exception): Reso 01.
   `resolution_date` is Legistar's 2018-07-18 and its `resolution_date_source` names only the
   Legistar notes.
5. **`header_char_top_pt = 1.3`** (the FY2022 knob): Reso 09's bold header capitals rise 1.23 pt
   above their text-layer boxes. Without it the ink check found 88 slivers on pp.11–44.
6. Handled by earlier years' rules, as named exceptions: five "Beating Hearts Initiative" charts
   (no note, as FY2020), one chart page whose "Page 41" label is printed on top of the `***`
   footnote (Reso 03 p.55, `T3.page_label`), and 4 `**` rows on a page whose footnotes stop at `*`
   (Reso 04 p.19).
7. A crash fix: a review crop for a resolution-level item (page 0) is skipped instead of crashing
   the run.

FY2020, FY2021, FY2022, FY2023, FY2024, FY2025 and FY2026 outputs are byte-identical with these
changes (every tracked file in their review folders, crops included; re-run on 2026-10-22 with
Python 3.12.13), apart from the known FY2026 decisions drift described in the FY2023 README.

## Files

As in FY2020 (`fy19_` prefix): `REVIEW.md`, `ISSUE-LOG-DRAFT.md` (for #110, **not posted**),
`data/fy19_tr_rows.csv` (7,207), `fy19_tr_charts.csv` (445), `fy19_tr_resolutions.csv` (11),
`fy19_tr_review.csv` (52, same columns as `fy20_tr_review.csv`), `fy19_tr_checks.txt`,
`fy19_tr_flags.csv`, `fy19_tr_pages.csv`, `fy19_tr_disclosure_match.csv`,
`fy19_tr_retired_csv_compare.csv` (the 117 rows above), `fy19_tr_manifest.json`,
`data/overlays/` (52 review crops).

## How to redo it

```
.venv/bin/python code/parse_transparency_v2.py --fy 2019      # ~2 min on a laptop CPU
.venv/bin/python -m pytest code/test_transreso.py
```

Byte-identical on re-run (checked). Every year-specific fact is in
`config/transparency/fy2019.toml`.

## What these checks cannot prove

- That a change exists which no PDF printed (no totals, and no chart counts this year).
- Text where both grids read the same wrong text layer (no OCR sample). This matters more this
  year: on the 21 overfull pages both grids use the same block rule, so they cannot disagree
  about which row a wrapped line belongs to. The 43 rows it moves were read by hand against the
  page; the page itself shows those lines overlapped or cut off.
- What the "Beating Hearts Initiative" organizations each receive: the charts print no note and
  no amount.
- Resolution numbers for Reso 03–05 and 07–10 rest on Legistar order ("confirmed (positional)" in
  the 2026-07-07 notes), not on a number printed in the PDF.

## Since this review

- Rescission origins (report only) now use the checked FY2019 Schedule C,
  `data/fy19/pdf/schedule_c/fy19_sc_awards.csv` (#204, re-run 2026-10-23): 49 → 368 match a Schedule
  C award, 298 → 129 part of a larger amount, 333 → 183 not found. The retired old-parser CSVs had
  missed or misread those awards' (EIN, amount).

## Not done here

- OCR audit.
- Nothing added to the MCP or the public site; the retired `data/fy19/transparency-resolutions/`
  files are unchanged.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` (the integrator numbers sections). Proposed text:

> ## NN. FY2019 transparency resolutions rebuilt from the PDFs, checked (#110) — REVIEW NOT STARTED
>
> > **Scope.** A new, checked parse of the 11 PDFs in `source/FY19/transparency-resolutions/`
> > (`code/parse_transparency_v2.py --fy 2019`, `config/transparency/fy2019.toml`). Its review
> > record is [`research/2026-10-22-fy19-transparency-review/`](research/2026-10-22-fy19-transparency-review/README.md).
> > The old `data/fy19/transparency-resolutions/*.csv` files are unchanged and stay the historical
> > record (§27). Not served by the MCP.
>
> **Result.** 7,207 rows from 445 charts (the old parse had 7,090, all of which are here), each
> with its resolution's number and adoption date. An independent image grid agrees on all 7,207.
> No totals and no chart counts are printed. Reso 04, 05, 06, 08 and 09 add new money (+$4.7M in
> all); Reso 02 takes back $144,999 more than it gives.
>
> **What the old parse missed.** The 112 "Beating Hearts Initiative" rows (no amount column),
> Reso 01's two "All Allocations" rows (EIN "Various", $4,090,000 each way), 2 EINs printed
> without a hyphen and 1 followed by a hidden tab glyph.
>
> **Things a re-parse must know.** On 21 pages (Reso 03, 04, 07) text wraps to more lines than
> its row is tall and is drawn across the row's rules: read it as one block per cell, or wrapped
> lines land in the next row ("IGnrce.enwich House") or fall off the table. Some rows are drawn
> column by column. Reso 01–07 and 11 print "CHART 1:" with no "#". Reso 01 p.108 prints chart
> #56's first page as "CHART 55". Reso 09's bold header capitals rise above their text boxes.
>
> **What the PDF itself gets wrong (flagged, never fixed).** Reso 01 p.1 is dated July 17, 2018;
> Legistar says adopted July 18. One DoVE chart is $1 off inside itself (Reso 02 chart #8). 4 `**`
> rows with no `**` footnote (Reso 04 p.19). "Neighborhood SC-Catholic Charities" printed without
> spaces around the separator (Reso 07 p.30).
