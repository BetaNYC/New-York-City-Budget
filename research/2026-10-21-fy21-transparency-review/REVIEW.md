# FY2021 transparency resolutions: what a person needs to check

**Report generated:** 2026-10-21 23:58 EDT. Source: `data/fy21_tr_review.csv` (21 rows), sorted
the same way: the 1 critical item first, then by how much money each could touch. Write each
decision into `data/fy21_tr_review_decisions.csv` by `review_id` (columns `review_id, decision,
note, decided_by, decided_at`; decisions `source_error`, `parser_bug`, `accepted_as_printed` or
`needs_info`), or use the explorer's review screen and `code/validate_review_decisions.py --add`.
The pipeline never writes that file. Nothing here changes a dollar amount. Each item has a crop
in `data/overlays/` (named `r<reso>-p<page>-<review_id>.png`).

## Critical (1)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 1 | `8374908023d2` | 02, p.29 | 10,000 | **A row with no member and no EIN.** Cultural Immigrant Initiative (chart #9, continued): "Department of Cultural Affairs **", DCLA ($10,000), 126 003, just above Adams, Bartlett Foundation - Council District 28 \*\*, $10,000 DYCD. Checked on the rendered page: the member and EIN cells are blank. Likely DCLA's own side of a move to DYCD, printed without the City EIN. | Kept as printed: `ein` blank, `agency_side` 0 (no City EIN). | `source_error` |

## Warn (20)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 2, 4, 6, 14 | `b101c7bf90cd` `6a63371fb2e6` `2fb7a8bb7da9` `e8e0773ce499` | 01 p.126; 02 p.65; 03 p.47; 05 p.40 | — | **"Beating Hearts": no Agency or Amount column** (28 rows: 18, 3, 3, 4). Note under each: "***Staten Island Heart Society, Inc. has received $175,000 that will go towards providing automated external defibrillators (AEDs) to non-profit organizations that primarily serve the youth and aging populations. The non-profit organizations are listed above." | Rows kept, amount blank, `action` = `listed`. Named exceptions (`T4.no_amount`), as FY2022. | `accepted_as_printed` |
| 3 | `9d313b962d53` | 02, p.20 | — | **First page of a chart prints "(continued)"**: chart #6 Speaker's Initiative to Address Citywide Needs (p.19 is chart #5; the labels "Page 7", "Page 8" run on, so no page is missing). | Read as the chart's start. Named exception. | `source_error` |
| 5, 7–13, 15–21 | 15 items (`T3.page_label`) | 02 p.65; 03 p.47; 05 pp.33–37, 40; 06 pp.34–37; 07 pp.31–32; 08 p.20 | — | **No "Page n" label** on 15 chart pages: the prior-year charts just before "Purpose of Funds Changes" and the "Beating Hearts" pages. The next label counts them (Reso 05 p.38 prints "Page 28" after "Page 22"). Checked on Reso 05 p.35. | Named exceptions; the labels around them count them. | `accepted_as_printed` |

## Not in the review file, on purpose

- **8 EINs printed without a hyphen**, read as printed (`W.ein_no_hyphen`); all 8 are rows the
  old CSV missed.
- **12 line-end hyphens on 12 rows**, all read by hand (`config/transparency/fy2021.toml`).
- **6 rows with a cell spanning two columns** (`W.spanning_cell`, Reso 01 p.124), as in FY2026.
- **15 drawn rows that print nothing** under the "Beating Hearts" chart on Reso 02 p.65 (the
  table is drawn with 18 rows and 3 are filled). Counted, not rows.
- **An EIN starting "00"**: Gjonaj, Life Scout Troop 211, 00-0102159 (Reso 02 p.65, "Beating
  Hearts", no amount). The IRS does not issue that prefix; it is read as printed and is not in
  the disclosure match (no amount). Worth a look if the "Beating Hearts" rows are kept.
- **Disclosure gaps** (report only): 241 FY2021 designations not found on (EIN, amount): 158
  taken back later, 52 at another amount, 24 EIN not in the disclosure, 5 key already used, 2
  City-EIN name mismatch. `data/fy21_tr_disclosure_match.csv`.
- **Rescission origins** (report only): of 610, 268 take back an earlier resolution's row, 251
  match a Schedule C award (retired CSV), 52 part of a larger amount, 39 not found.

## Decisions for Noel

1. **Item 1, the $10,000 row with no member or EIN** (Reso 02 p.29). Kept blank. It is probably
   DCLA's own side of a move to DYCD; I would not fill it in. `source_error`.
2. **"Beating Hearts" rows** (28): kept as rows with no amount, `action` = `listed`, the same
   choice as FY2022 (#158). If FY2022's decision changes, change this year's with it.
