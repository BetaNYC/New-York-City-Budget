# FY2018 transparency resolutions, checked from the PDFs (#111)

**Report generated:** 2026-10-22 02:05 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** the 12 PDFs in `source/FY18/transparency-resolutions/` (598 pages; hashes
in `config/transparency/fy2018.toml`); expense disclosure as committed in
`data/fyNN/expense_disclosure/`; resolution numbers and adoption dates from
`research/2026-07-07-legistar-links-fy15-20.md` and `data/combined/legistar_crosswalk.csv` (read
from Legistar on 2026-07-07, not re-queried; Reso 03, 05, 06 and 09–12 are "confirmed
(positional)" there); code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #111 (epic #101). This folder is the review record. The tables are promoted to
`data/fy18/pdf/transparency/` by a separate PR. FY2018 Schedule C, Terms and Conditions and
capital are other sessions' work. The method is FY2019's
(`research/2026-10-22-fy19-transparency-review/`); this README says what differs.

## What these PDFs are

The same Excel charts as FY2019, one table per landscape page, with `Agy #` and `U/A` columns,
amounts printed with cents ("$3,500.00"), and every caption "CHART n:" with no "#". Each
resolution opens with the Committee on Finance report (it prints the date). No page carries
/Rotate and every media box starts at (0, 0); none prints "Charts 1 through N".

New this year:

- **Two fiscal conduit columns** on 95 chart pages: "Fiscal Conduit/Sponsoring Organization" and
  "Fiscal Conduit EIN" (on Reso 11 pp.7–8 the second is labelled only "Fiscal Conduit"). 63 rows
  fill them. They are four new columns at the end of the row table, FY2018 only:
  `fiscal_conduit`, `fiscal_conduit_ein`, `fiscal_conduit_raw`, `fiscal_conduit_ein_printed`.
- **Header rows with no labels** (Reso 01 pp.55–56, Reso 03 p.48, Reso 04 p.32): a grey band with
  nothing in it.
- **Boxes round resolution text** on 8 portrait pages, which the table finder takes for a table.
- **`***` footnotes that explain one chart**, over several lines (Reso 03 pp.24–25, 30; Reso 04
  p.58), and a new one-line `***` wording (Reso 05: "Indicates a change that was reflected in the
  Budget Modification (MN-1) approved by the Council on 9/27/2017").
- "(Continued)" with a capital C (11 pages).

### Reso 01 and the fiscal year

Reso 01 (Res 1563-2017) is dated **June 21, 2017**, nine days before Fiscal 2018 began. It came
after the Fiscal 2018 budget was adopted (June 6, 2017), and its p.1 says it changes
designations "in accordance with the Fiscal 2018 Expense Budget" (charts 1–29 and 38; 865 rows)
as well as the Fiscal 2017 and 2016 budgets (charts 30–37 and 39; 28 rows). The 2026-07-07
Legistar notes and the crosswalk file it as FY2018 Transparency Reso 01. **Kept in FY2018**, with
each row's `budget_fiscal_year` from its own chart, and flagged (`K.adopted_before_fy`, a review
item). Not guessed further.

## Results

| What | Result |
|---|---|
| Rows | **5,558** (3,834 designations, 1,100 rescissions, 488 purpose-of-funds rows, **136 "Beating Hearts Initiative" rows with no amount**) from 400 charts on 462 chart pages. Budget years: 2018 5,204 · 2017 326 · 2016 27 · none printed 1 |
| Printed totals | **None to tie.** 0 money amounts outside the tables, except inside notes and footnotes that explain a chart (10, in review). No chart counts. The "Page n" labels count every chart page |
| Image grid (independent) | **5,558 / 5,558** rows agree on every field (the conduit columns included) |
| Ink coverage | **0 regions.** Self-test on Reso 01 p.13 passes |
| Anchor census | 5,615 EIN-shaped words = 5,556 rows with an EIN + 59 fiscal conduit EINs, page by page; 2 rows print "Various" |
| Sign vs colour | 1,343 amounts in parentheses, all red |
| Characters | 812,721 non-space; 0 in a table but in no cell; 181 hidden under the next cell in 14 runs (review) |
| Dates | All 12 print their date and it matches Legistar and the filename |
| Numbers | All 12 from Legistar (Res 1563-2017 .. Res 0399-2018) |
| Disclosure (report only) | FY2018: 3,355 of 3,646 organization designations ($138.1M) are in the disclosure on (EIN, amount); 232 of the rest were taken back later |
| Old CSV (`data/fy18/transparency-resolutions/`) | 5,364 of its 5,366 rows are here. The other 2 are its own misreading: Reso 04 p.56, Vietnam Veterans of America, it read EIN 21-2629339 from the text "#32" + "11-2629339"; the page shows 11-2629339, and so do these rows. It missed 194: the 136 "Beating Hearts Initiative" rows, 48 other rows whose EIN prints without a hyphen, 2 "All Allocations" rows (Reso 10), and 8 others, most next to text hidden under a cell (Reso 03 pp.17, 39; Reso 04 p.56) |
| Review file | **72 rows** (8 critical, 64 warn), largest $7,805,000 (`REVIEW.md`) |

### Per resolution

| # | Res. | Adopted | Rows | Charts | Orgs + (n, $) | Orgs − (n, $) | Agency side net | Purpose rows | Net, designation charts |
|---:|---|---|---:|---:|---|---|---:|---:|---:|
| 1 | 1563-2017 | 2017-06-21 | 893 | 39 | 779, $36,355,580 | 55, −$3,689,346 | −$32,666,234 | 28 | $0 |
| 2 | 1589-2017 | 2017-07-20 | 845 | 46 | 650, $38,650,193 | 79, −$2,491,641 | −$36,158,552 | 46 | $0 |
| 3 | 1621-2017 | 2017-08-24 | 1,229 | 44 | 963, $27,819,373 | 96, −$2,296,183 | −$25,448,190 | 102 | +$75,000 |
| 4 | 1658-2017 | 2017-09-27 | 498 | 43 | 354, $18,367,733 | 80, −$2,130,307 | −$16,312,426 | 18 | −$75,000 |
| 5 | 1699-2017 | 2017-10-31 | 515 | 46 | 304, $8,584,064 | 127, −$3,555,859 | −$5,528,205 | 48 | −$500,000 |
| 6 | 1730-2017 | 2017-11-30 | 315 | 38 | 131, $2,841,090 | 90, −$1,889,812 | −$951,278 | 66 | $0 |
| 7 | 1780-2017 | 2017-12-19 | 241 | 28 | 135, $5,312,225 | 70, −$2,947,800 | −$2,364,425 | 12 | $0 |
| 8 | 0189-2018 | 2018-02-15 | 407 | 31 | 230, $6,132,015 | 120, −$2,747,015 | −$2,385,000 | 44 | +$1,000,000 |
| 9 | 0239-2018 | 2018-03-22 | 190 | 23 | 78, $2,305,288 | 54, −$2,115,288 | −$190,000 | 42 | $0 |
| 10 | 0271-2018 | 2018-04-11 | 90 | 12 | 36, $956,365 | 27, −$521,550 | −$34,815 | 26 | +$400,000 |
| 11 | 0333-2018 | 2018-05-09 | 85 | 13 | 29, $486,801 | 23, −$231,000 | −$255,801 | 28 | $0 |
| 12 | 0399-2018 | 2018-06-14 | 250 | 37 | 111, $3,223,792 | 110, −$3,188,308 | −$35,484 | 28 | $0 |

**7 of 12 resolutions net to $0** on their designation charts. Reso 03 +$75,000 (chart #22
Afterschool Enrichment Initiative) and Reso 04 −$75,000 (one-sided charts, the largest chart #23
Discretionary Child Care −$115,000) cancel out across the two. Reso 05 −$500,000 (several
one-sided charts). Reso 08 +$1,000,000 (charts #24 Job Training and Placement +$375,000 and #25
Day Laborer Workforce +$625,000). Reso 10 +$400,000 (chart #4 Speaker's Initiative). No chart is
off by $1.

**Purpose-of-funds rows do not balance in Reso 05**: +$40,000. On p.60 Police Athletic League
has two +$20,000 rows and no matching negative (both black, both "$20,000.00"). Kept as printed;
the two rows are review items. Reso 04 p.56 pairs Association of Community Employment Programs
for the Homeless ($100,000 each way) under two EINs, 13-3846431 and 13-3846432, also in review.

## What is new in FY2018 (and how the code handles it)

1. **Fiscal conduit columns.** New header labels ("Fiscal Conduit/Sponsoring Organization",
   "Fiscal Conduit EIN", "Fiscal Conduit") and four row columns, written only for a year that
   has them. The EIN census counts conduit EINs; the image grid compares the conduit fields. 4
   conduit EINs are not readable as printed ("#########" three times, Excel's overflow; "13-281380",
   8 digits): `W.conduit_ein` review items.
2. **"Delegation"** as the member column's label (Reso 06 p.42).
3. **A header row with no labels** (`T4.blank_header`, named exception): read with the labels of
   the chart page before it, only when the column edges are the same to the point. The image grid
   borrows the same labels.
4. **A box round resolution text** (`T3.text_box`, named exception, 8 pages): not a chart; its
   table is dropped before the checks.
5. **Long `***` footnotes**: every line under one, down to "Page n", is its text; not furniture,
   not a printed total, and a `T6.footnote` review item with the chart. The MN-1 wording is a new
   `***` footnote.
6. **Captions**: "(Continued)" and "- Fiscal 2018 ***" are rewritten and flagged
   (`W.caption_format`, 12 pages).
7. **Amounts without "$"** but with cents ("(100,000.00)", Reso 05 p.61, 4 rows): read, and
   `W.amount_format` review items. With neither "$" nor cents it is still not an amount.
8. **Text carried into the next cell, then that cell's own text** (`T7.clip_restart`, named
   exception, Reso 04 p.52): "…Velocity Track Club New York" runs into the EIN cell and the EIN
   follows 0.99 pt later in the same run; on this page a gap like that ends the hidden text. Not
   everywhere: Reso 03 p.72 draws hidden text "Inc.(COMET)" with a gap and no space glyph, and the
   general rule broke it (tried and reverted).
9. **Overfull cells** (FY2019's rule), 3 pages: Reso 04 p.56, Reso 11 pp.17, 19. 4 rows change,
   each checked on the page; 4 review items.
10. **Ink self-test**: `ink_acceptance_min_char_pt = 4.0`. The test row's narrowest marks ("i",
    "l" at 1.81 pt; the "*" at 3.17 pt) ink fewer pixels than the smallest region, so withholding
    one could not fire.
11. Handled by earlier years' rules, as named exceptions: 9 "Beating Hearts Initiative" charts
    (each with a note: Staten Island Heart Society received $350,000 for defibrillators; the
    text layer has no spaces in it), 3 captions repeated without "(continued)", and 6 `**` rows on
    Reso 05 p.23, a page that prints no footnotes.

FY2019, FY2020, FY2021, FY2022, FY2023, FY2024, FY2025 and FY2026 outputs are byte-identical with
these changes (every tracked file in their review folders, crops included; re-run on 2026-10-22
with Python 3.12.13), apart from the known FY2026 decisions drift.

## Files

As in FY2019 (`fy18_` prefix): `REVIEW.md`, `ISSUE-LOG-DRAFT.md` (for #111, **not posted**),
`data/fy18_tr_rows.csv` (5,558; the review columns are the same as FY2019's, the row table adds
the four conduit columns at the end), `fy18_tr_charts.csv` (400), `fy18_tr_resolutions.csv` (12),
`fy18_tr_review.csv` (72, same columns as `fy19_tr_review.csv`), `fy18_tr_checks.txt`,
`fy18_tr_flags.csv`, `fy18_tr_pages.csv`, `fy18_tr_disclosure_match.csv`,
`fy18_tr_retired_csv_compare.csv`, `fy18_tr_manifest.json`, `data/overlays/` (72 review crops).

## How to redo it

```
.venv/bin/python code/parse_transparency_v2.py --fy 2018      # ~2 min on a laptop CPU
.venv/bin/python -m pytest code/test_transreso.py
```

Byte-identical on re-run (checked). Every year-specific fact is in
`config/transparency/fy2018.toml`.

## What these checks cannot prove

- That a change exists which no PDF printed (no totals, and no chart counts this year).
- Text where both grids read the same wrong text layer (no OCR sample). On the 4 blank-header
  pages both grids use the same borrowed labels.
- What each "Beating Hearts Initiative" organization receives: the notes give only the total
  ($350,000 to Staten Island Heart Society).
- Whether Reso 01 belongs to FY2018 or FY2017 in the Council's own filing; it is filed here as
  the 2026-07-07 notes file it.
- Resolution numbers for Reso 03, 05, 06 and 09–12 rest on Legistar order.

## Not done here

- OCR audit; rescission origins use the *retired* FY2018 Schedule C CSVs (report only).
- Nothing added to the MCP or the public site; the retired `data/fy18/transparency-resolutions/`
  files are unchanged.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` (the integrator numbers sections). Proposed text:

> ## NN. FY2018 transparency resolutions rebuilt from the PDFs, checked (#111) — REVIEW NOT STARTED
>
> > **Scope.** A new, checked parse of the 12 PDFs in `source/FY18/transparency-resolutions/`
> > (`code/parse_transparency_v2.py --fy 2018`, `config/transparency/fy2018.toml`). Its review
> > record is [`research/2026-10-22-fy18-transparency-review/`](research/2026-10-22-fy18-transparency-review/README.md).
> > The old `data/fy18/transparency-resolutions/*.csv` files are unchanged and stay the historical
> > record (§27). Not served by the MCP.
>
> **Result.** 5,558 rows from 400 charts, each with its resolution's number and adoption date, and,
> where printed, the fiscal conduit and its EIN (63 rows). An independent image grid agrees on all
> 5,558. No totals and no chart counts are printed. Reso 08 and 10 add new money (+$1.4M);
> Reso 05 takes back $500,000 more than it gives.
>
> **What the old parse got wrong.** It missed 194 rows (136 "Beating Hearts Initiative" rows, 48
> more with a hyphenless EIN, 2 "All Allocations", 8 others, most next to hidden text) and misread one EIN (Reso 04
> p.56, Vietnam Veterans of America: 21-2629339 for 11-2629339).
>
> **Things a re-parse must know.** Reso 01 is dated June 21, 2017, before Fiscal 2018 began, and
> changes the FY2018, 2017 and 2016 budgets. 95 chart pages print fiscal conduit columns. Four
> header rows print no labels; eight boxes round resolution text look like tables. Some `***`
> footnotes explain one chart over several lines. Amounts print cents, and four print no "$".
>
> **What the PDF itself gets wrong (flagged, never fixed).** Police Athletic League's two +$20,000
> purpose rows have no negative (Reso 05 p.60). One organization under two EINs in a pair (Reso 04
> p.56). Four conduit EINs print as "#########" or 8 digits. 6 `**` rows on a page with no
> footnotes (Reso 05 p.23).
