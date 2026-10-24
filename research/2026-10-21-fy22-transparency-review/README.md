# FY2022 transparency resolutions, checked from the PDFs (#107)

**Report generated:** 2026-10-21 23:09 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** the 14 PDFs in `source/FY22/transparency-resolutions/` (709 pages; hashes
in `config/transparency/fy2022.toml`); expense disclosure as committed in
`data/fyNN/expense_disclosure/` (FY2022 workbook sheet "FY22 (07-11-2023)", FY2021 "FY21 (06-23-2023)",
FY2020 "FY20 (06-16-2022)"); resolution numbers and adoption dates from
`research/2026-07-07-legistar-links-fy21-27.md` and `data/combined/legistar_crosswalk.csv` (read
from Legistar on 2026-07-07, not re-queried); code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #107 (epic #101). This folder is the review record. The tables are promoted to
`data/fy22/pdf/transparency/` by a separate PR. FY2022 Schedule C and capital/terms are other
sessions' work. The method is FY2026's, with the FY2025–FY2023 additions
(`research/2026-10-21-fy23-transparency-review/` is the closest model); this README says what
differs.

## What these PDFs are

The same Excel charts as FY2023–FY2026, one table per landscape page, but FY2022 is the least
regular year so far. Each resolution opens with the Committee on Finance report (it prints the
date) **and the resolution text** ("Resolved, That the City Council approves …", one paragraph
per chart), so the front runs 5–22 pages. No page carries /Rotate; none prints "Charts 1
through N". 116 of Reso 02's pages have a media box that starts at (−8.39, −8.39) instead of (0, 0).

## Results

| What | Result |
|---|---|
| Rows | **7,918** (6,402 designations, 1,176 rescissions, 249 purpose-of-funds rows, **91 "Beating Hearts" rows with no amount**) from 424 charts on 565 chart pages. Budget years: 2022 7,783 · 2021 115 · 2020 20 |
| Printed totals | **None to tie.** 0 money amounts outside the tables, except the 7 "Beating Hearts" notes ("$350,000", below). No chart counts. The "Page n" labels count every chart page (1..n on all 14; 25 pages print none, and one page holds only a spilled footnote and its label) |
| Image grid (independent) | **7,917 / 7,918** rows agree on every field. The one that differs is a "-" sitting on a cell border (Reso 02 p.47, review item) |
| Ink coverage | **2 regions**, both on Reso 09 p.38 ("anc" showing in the empty `*` column, below). 37,795 loose px under the region size, 37,055 of them on Reso 02: 1-pixel slivers along row rules from rounding its page-origin shift to whole pixels. Self-test on Reso 01 p.16 passes |
| Anchor census | 7,916 EIN-shaped words = 7,916 rows with an EIN, page by page; 2 rows print no EIN (review items) |
| Sign vs colour | 1,306 amounts in parentheses, all red |
| Characters | 1,036,445 non-space; 0 in a table but in no cell; 422 hidden (2 overlaid runs, review items) |
| Dates | All 14 print their date and it matches Legistar and the filename |
| Numbers | All 14 from Legistar (Res 1715-2021 .. Res 0224-2022) |
| Disclosure (report only) | FY2022: 5,699 of 6,310 organization designations ($234.4M) are in the disclosure on (EIN, amount); 498 of the rest were taken back later |
| Old CSV (`data/fy22/transparency-resolutions/`) | Every one of its 7,768 rows is here. It missed 150: the 91 "Beating Hearts" rows, 45 EINs printed without a hyphen, 12 ordinary rows (2 of them Reso 09 p.38's garbled-EIN rows), the blank-EIN row and the "FY22 05075" row |
| Review file | **125 rows** (13 critical, 112 warn), largest $1,613,026 (`REVIEW.md`) |

### Per resolution

| # | Res. | Adopted | Rows | Charts | Orgs + (n, $) | Orgs − (n, $) | Agency side net | Purpose rows | "Speaker" rows |
|---:|---|---|---:|---:|---|---|---:|---:|---:|
| 1 | 1715-2021 | 2021-07-29 | 1,451 | 49 | 1,306, $40,899,068 | 75, −$4,978,100 | −$35,020,968 | 20 | 11 |
| 2 | 1726-2021 | 2021-08-26 | 2,151 | 80 | 1,935, $101,897,856 | 102, −$3,366,819 | −$98,471,037 | 20 | 8 |
| 3 | 1739-2021 | 2021-09-23 | 1,513 | 51 | 1,363, $48,378,531 | 63, −$5,317,326 | −$28,569,927 | 20 | 6 |
| 4 | 1752-2021 | 2021-10-07 | 520 | 25 | 424, $29,878,443 | 47, −$6,501,261 | −$23,243,479 | 14 | 13 |
| 5 | 1765-2021 | 2021-10-21 | 335 | 21 | 238, $6,764,840 | 76, −$2,068,626 | −$4,399,823 | 4 | 0 |
| 6 | 1785-2021 | 2021-11-10 | 293 | 25 | 153, $4,837,082 | 85, −$2,682,086 | −$1,322,459 | 18 | 0 |
| 7 | 1803-2021 | 2021-11-23 | 267 | 22 | 192, $4,521,157 | 29, −$1,068,960 | −$2,373,157 | 28 | 4 |
| 8 | 1839-2021 | 2021-12-09 | 271 | 28 | 172, $5,520,874 | 66, −$2,224,323 | −$1,633,702 | 10 | 2 |
| 9 | 1869-2021 | 2021-12-15 | 303 | 27 | 156, $5,047,907 | 65, −$2,599,218 | −$1,086,500 | 69 | 10 |
| 10 | 0058-2022 | 2022-03-10 | 417 | 29 | 230, $5,790,308 | 127, −$2,638,082 | −$1,055,020 | 14 | 4 |
| 11 | 0107-2022 | 2022-04-14 | 165 | 21 | 80, $1,809,268 | 49, −$1,245,847 | −$456,682 | 20 | 8 |
| 12 | 0154-2022 | 2022-05-05 | 130 | 19 | 63, $910,960 | 54, −$1,966,185 | +$1,055,225 | 4 | 2 |
| 13 | 0160-2022 | 2022-05-19 | 68 | 17 | 37, $4,290,048 | 23, −$1,987,048 | −$2,303,000 | 0 | 17 |
| 14 | 0224-2022 | 2022-06-13 | 34 | 10 | 13, $158,500 | 11, −$151,307 | −$7,193 | 8 | 0 |

Unlike FY2023–FY2026, **11 of 14 resolutions' designation rows do not net to $0** (+$23,021,932 in
all; only Reso 12–14 net to $0). Most of it is one-sided "Pandemic Support for Human Service
Providers" charts: new money to organizations with no agency side (Reso 03 chart #48,
+$14,191,278, 387 rows printed in cents; Reso 10 #24, Reso 08 #20, Reso 07 #18). The old parse's
own notes (`data/fy22/transparency-resolutions/fy22_transparency_reconciliation.txt`) show the
same nets for Reso 04–06 and 08–14. Reported, not flagged.

## What is new in FY2022 (and how the code handles it)

1. **A shifted page origin** (Reso 02, 116 of its 138 pages: media box from −8.39 pt). The text layer
   counts from the box's origin, the renderer from the page's corner, so the image grid and the
   ink check were 8.39 pt off: 2,151 rows disagreed and 13% of the ink looked uncovered. The
   reader now records each page's origin; the image checks shift the picture to match, and
   `bbox_pt` is written on the page as rendered (top-left corner = 0, 0), as the row contract
   asks. Pages with origin (0, 0) (every other year) are untouched.
2. **"Beating Hearts" charts** (7: Reso 03, 04, 06, 08, 10, 11, 12): organizations getting
   defibrillators through Staten Island Heart Society, header Member | Organization | EIN Number
   | `*`, no agency, no amount, and a note under the table ("… has received $350,000 …"). Rows
   kept with a blank amount and `action` = `listed`; allowed only as a named exception
   (`T4.no_amount`), and the note is read as the chart's note, not stray text.
3. **Amounts in cents** ("$20,290.00", Reso 03 chart #48). Read as whole dollars; anything other
   than ".00" stays unreadable.
4. **Captions that do not say "(continued)"**: a repeated caption with no "(continued)" (Reso 01
   pp.51–54, Reso 02 p.35), a "(continued)" caption with the wrong number (Reso 07 p.34 prints
   #21 under #22 "Purpose of Funds Changes"), and two first pages that print "(continued)" (Reso
   02 pp.80, 124). Each is a named exception and a review item.
5. **Text drawn over text** (Reso 09 p.38): a long unwrapped line is drawn on top of the EIN
   "13-4170389" and runs off the page; the page shows the EIN. On pages the config names
   (`T7.overlaid`), a run whose first letter starts on top of a cell's own visible text is
   hidden and listed. Off everywhere else (see "Found in other years").
6. **A page that is only a spilled footnote** (Reso 02 p.106: "** Requires …" and "Page 84").
   Named exception (`T3.label_page`); its label joins the count.
7. **Bold header capitals that rise above their text box** (Reso 02, "EIN"): the ink check fired
   once per page. The config raises header boxes by 0.6 pt (`header_char_top_pt`, FY2022 only).
8. "*Indicates …" (no space) is accepted as the `*` footnote.

FY2023, FY2024, FY2025 and FY2026 outputs are byte-identical with these changes (every tracked
file in their review folders, crops included; re-run on 2026-10-21), apart from the known FY2026
decisions drift described in the FY2023 README.

## Found in other years (not changed)

The overlaid-text rule, tried on every year, also finds **FY2026 Reso 02 p.114**: "Funding
supports health and wellness services for children and caregiv…" is drawn over the visible
"pregnancy through early childhood." (the last line of the row above). The committed FY2026
output reads it into that row's purpose. Left as it is (the FY2026 review is under way); listed
for Noel.

## Files

As in FY2023 (`fy22_` prefix): `REVIEW.md`, `ISSUE-LOG-DRAFT.md` (for #107, **not posted**),
`data/fy22_tr_rows.csv` (7,918), `fy22_tr_charts.csv` (424), `fy22_tr_resolutions.csv` (14),
`fy22_tr_review.csv` (125, same columns as `fy24_tr_review.csv`), `fy22_tr_checks.txt`,
`fy22_tr_flags.csv`, `fy22_tr_pages.csv`, `fy22_tr_disclosure_match.csv`,
`fy22_tr_retired_csv_compare.csv` (the 150 rows above), `fy22_tr_manifest.json`,
`data/overlays/` (125 review crops and 3 check crops).

## How to redo it

```
.venv/bin/python code/parse_transparency_v2.py --fy 2022      # ~2 min on a laptop CPU
.venv/bin/python -m pytest code/test_transreso.py
```

Byte-identical on re-run (checked). Every year-specific fact is in
`config/transparency/fy2022.toml`.

## What these checks cannot prove

- That a change exists which no PDF printed (no totals, and no chart counts this year).
- Text where both grids read the same wrong text layer (no OCR sample). The overlaid run on
  Reso 09 p.38 shows the text layer can hold text the page does not show; the rule that hides it
  runs only where named.
- What the "Beating Hearts" organizations each receive (the PDF names none per row).

## Since this review

- Rescission origins (report only) now use the checked FY2022 Schedule C,
  `data/fy22/pdf/schedule_c/fy22_sc_awards.csv` (#204, re-run 2026-10-23): 156 → 160 match a
  Schedule C award, 56 → 53 part of a larger amount, 56 → 55 not found. The retired old-parser CSVs
  had missed or misread those awards' (EIN, amount).

## Not done here

- OCR audit.
- Nothing added to the MCP or the public site; the retired `data/fy22/transparency-resolutions/`
  files are unchanged.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` (the integrator numbers sections). Proposed text:

> ## NN. FY2022 transparency resolutions rebuilt from the PDFs, checked (#107) — REVIEW NOT STARTED
>
> > **Scope.** A new, checked parse of the 14 PDFs in `source/FY22/transparency-resolutions/`
> > (`code/parse_transparency_v2.py --fy 2022`, `config/transparency/fy2022.toml`). Its review
> > record is [`research/2026-10-21-fy22-transparency-review/`](research/2026-10-21-fy22-transparency-review/README.md).
> > The old `data/fy22/transparency-resolutions/*.csv` files are unchanged and stay the historical
> > record (§27). Not served by the MCP.
>
> **Result.** 7,918 rows from 424 charts (the old parse had 7,768, all of which are here), each
> with its resolution's number and adoption date. An independent image grid agrees on 7,917.
> No totals and no chart counts are printed. 11 of 14 resolutions add new money (+$23.0M in all,
> mostly "Pandemic Support for Human Service Providers").
>
> **What the old parse missed.** The 91 "Beating Hearts" rows (no amount column), 45 EINs printed
> without a hyphen, 12 ordinary rows, and two rows with no usable EIN.
>
> **Things a re-parse must know.** Most of Reso 02's pages have a media box starting at (−8.39, −8.39): shift the page
> image, and write boxes on the rendered page. "Beating Hearts" charts have no amount. Reso 03
> chart #48 prints cents. Captions repeat without "(continued)" (Reso 01 pp.51–54, Reso 02 p.35),
> print the wrong number (Reso 07 p.34) or "(continued)" on a first page (Reso 02 pp.80, 124).
> Reso 09 p.38 draws a hidden line over an EIN. Reso 02 p.106 is only a spilled footnote.
> 25 chart pages print no "Page n" label.
>
> **What the PDF itself gets wrong (flagged, never fixed).** A row with no member, organization or
> EIN, ($1,613,026) DYCD (Reso 03 p.32). "FY22 05075" as an EIN (Reso 07 p.21). "#" in the `*`
> column (Reso 03 p.29). Six `***` rows with no `***` footnote (Reso 03 p.16, Reso 08 p.16, Reso 09
> p.38).
