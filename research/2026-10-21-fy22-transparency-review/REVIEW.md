# FY2022 transparency resolutions: what a person needs to check

**Report generated:** 2026-10-21 23:09 EDT. Source: `data/fy22_tr_review.csv` (125 rows), sorted
the same way: the 13 critical items first, then by how much money each could touch. Write each
decision into `data/fy22_tr_review_decisions.csv` by `review_id` (columns `review_id, decision,
note, decided_by, decided_at`; decisions `source_error`, `parser_bug`, `accepted_as_printed` or
`needs_info`), or use the explorer's review screen and `code/validate_review_decisions.py --add`.
The pipeline never writes that file. Nothing here changes a dollar amount. Each item has a crop
in `data/overlays/` (named `r<reso>-p<page>-<review_id>.png`).

## Critical (13)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 1 | `c78abec43002` | 03, p.32 | 1,613,026 | **A row with only an agency and an amount.** Food Pantries Initiative (chart #12): no borough, no organization, no EIN; DYCD ($1,613,026), 260 005. Checked on the rendered page: the cells are blank. Likely the agency side of the chart, printed without "Department of Youth and Community Development" and the City EIN. | Kept as printed: `org` and `ein` blank, `agency_side` 0 (no City EIN). | `source_error` |
| 2 | `ea2da519c983` | 07, p.21 | 52,906 | **EIN printed as "FY22 05075".** Food Pantries Initiative (chart #11), Department of Youth and Community Development, ($52,906). Checked on the rendered page. | `ein` blank, `ein_printed` as printed. | `source_error` |
| 3 | `62ece7acb42f` | 03, p.29 | 40,000 | **"#" in the `*` column.** Holden, Queens Symphony Orchestra - Queensborough Community College, ($40,000), Cultural Immigrant Initiative. Same as FY2024 Reso 02 p.18. | `prequal_printed` = "#", `prequal_pending` = 0. Named exception. | `source_error` |
| 4 | `37436d8be9c4` | 02, p.47 | 30,000 | **The image grid reads one character differently.** D.Diaz, Department of Parks and Recreation - Tree Guards - Knickerboker Avenue's Commercial Strip **-** Council District 37. The "-" sits on the organization cell's right border; the text layer puts it in the cell, the image grid just past it. | Kept the text layer's reading (it matches the page). | `accepted_as_printed` |
| 5–6 | `239c16196a56` `e77512553e4c` | 08, p.16 | 20,000 | **`***` with no `***` footnote.** Louis, Kan Cobra Tiger Alliance - Public School 326K, ($20,000) DCLA → $20,000 DYCD, CASA. | Kept as printed: `correction` = 1. Named exceptions. | `source_error` |
| 7–8 | `4034dfce09c3` `b9b076640c06` | 03, p.16 | 10,000 | Same: Miller, Bartlett Foundation, ($10,000) DYCD → $10,000 DFTA, Local Initiatives. | Same. | `source_error` |
| 9, 11 | `4d8585917f15` `88872c74d8dc` | 09, p.38 | 5,000 | **Text drawn over the EIN.** Gibson, Family Life Academy Charter School, ($5,000) and $5,000. The text layer holds a long line "Funding to go support the creation of educational home kits …" drawn on top of the EIN "13-4170389" and running off the page; the page shows only the EIN. | Named page (`T7.overlaid`): the line is hidden and kept in `hidden_text`; `ein` = 134170389. Both grids agree. | `accepted_as_printed` |
| 10, 12 | `607486956bbd` `942d87172f90` | 09, p.38 | 5,000 | `***` with no `***` footnote: Gibson, Chess-in-the-Schools, $5,000 and ($5,000), purpose-of-funds. | Kept as printed. Named exceptions. | `source_error` |
| 13 | `9ecd6516e762` | 09, p.38 | — | **Ink outside every kept letter** (2 spots, 352 and 347 px): "anc", the only visible part of the hidden line in item 9, shows in the empty `*` column of rows 3 and 4. | The check is right. `prequal_printed` stays blank. | `accepted_as_printed` |

## Warn (112)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 14–15 | 2 items | 08, p.39 | 700,000 | **Purpose-of-funds pair with two EINs**: Department of Youth and Community Development ($700,000) → New York Immigration Coalition $700,000. | Kept as printed. | `accepted_as_printed` |
| 16–82 (63 items) | `W.unpaired_purpose` | 09, pp.39–60 | up to 218,946 | **Chart #27, MCCAP Initiative purpose changes**: the money is re-split into different amounts (Community Service Society ($185,000) and ($45,469) on p.39 …), so rows do not pair one to one. 37 rows out, 26 in; they balance in dollars. | Kept as printed. | `accepted_as_printed` (all 63) |
| 44–45 | 2 items | 06, p.37 | 30,000 | Purpose-of-funds pair with two EINs: Department of Health and Mental Hygiene ($30,000) → United Cerebral Palsy $30,000. | Kept as printed. | `accepted_as_printed` |
| 69–70 | `8771cf1f01ff` `a26ceccddd55` | 09, p.38 | 5,000 | Hidden text on the same two rows as items 9 and 11 (`W.clipped_text`). | Same. | `accepted_as_printed` |
| 83–86, 89 | `1261c00d1659` `da278350c2cb` `e827f7761d15` `82ce780558d7` `1edc82efe7e4` | 01, pp.51–54; 02, p.35 | — | **Caption repeated without "(continued)"**: chart #13 Support Our Seniors (starts p.50), chart #8 CASA (starts p.34). | Read as continuations. Named exceptions. | `source_error` |
| 90, 92 | `19d15e76756d` `bb00cc89d0e2` | 02, pp.76, 104 | — | Caption with no ":" after the chart number (#23, #49). | Read as printed number. | `accepted_as_printed` |
| 91, 94 | `ba4ecf0d1945` `39a4244febd3` | 02, pp.80, 124 | — | **First page of a chart prints "(continued)"** (#27 Coalition Theaters of Color, #67 Access Health). | Read as the chart's start. Named exceptions. | `source_error` |
| 93 | `40e63629ae75` | 02, p.106 | — | **A page with no table**: only "** Requires a budget modification …" and "Page 84" (chart #50's footnote spilled over). | Counted in the labels. Named exception. | `accepted_as_printed` |
| 104 | `90f2e470d4e8` | 07, p.34 | — | **"(continued)" with the wrong number**: prints "CHART #21: Purpose of Funds Changes" under chart #22 of that title (p.33); #21 is Local Initiatives - Fiscal 2020. | Read as chart #22. Named exception. | `source_error` |
| 96, 100, 101, 105, 111, 116, 122 | `8ace3e37e684` `bbf9ce77cf46` `8bf18e681885` `28f3b3abeb91` `2435a8a49b95` `fbe8c9c0f20f` `53b6424a8b5a` | 03 p.94; 04 p.39; 06 p.38; 08 p.40; 10 p.43; 11 p.31; 12 p.25 | — | **"Beating Hearts": no Agency or Amount column** (91 rows). Note under each: "Staten Island Heart Society, Inc. has received $350,000 that will go towards providing automated external defibrillators (AEDs) to non-profit organizations … listed above." | Rows kept, amount blank, `action` = `listed`. Named exceptions. | `accepted_as_printed` |
| 25 items between 87 and 125 | `T3.page_label` | 12 resolutions | — | **No "Page n" label** on 25 chart pages, mostly the last charts (list in the config). Checked on Reso 12 p.20. | Named exceptions; the labels around them count them. | `accepted_as_printed` |

## Not in the review file, on purpose

- **53 EINs printed without a hyphen**, read as printed (`W.ein_no_hyphen`); 45 of them are rows
  the old CSV missed.
- **128 line-end hyphens on 75 rows**, all read by hand (`config/transparency/fy2022.toml`).
- **111 rows with a cell spanning two columns** (`W.spanning_cell`), as in FY2026.
- **387 amounts printed in cents** (Reso 03 chart #48, all ".00").
- **Disclosure gaps** (report only): 611 FY2022 designations not found on (EIN, amount): 498 taken
  back later, 72 at another amount, 22 EIN not in the disclosure, 14 key already used, 5 City-EIN
  name mismatch. `data/fy22_tr_disclosure_match.csv`.
- **Rescission origins** (report only): of 872, 604 take back an earlier resolution's row, 156
  match a Schedule C award (retired CSV), 56 part of a larger amount, 56 not found.

## Decisions for Noel

1. **Item 1, the $1,613,026 row with no organization or EIN** (Reso 03 p.32). Kept blank. It is
   probably DYCD's own side of the Food Pantries chart; I would not fill it in. `source_error`.
2. **"Beating Hearts" rows** (91): kept as rows with no amount, `action` = `listed`. The
   alternative is to leave them out of the transparency tables. I'd keep them: they are printed
   as a chart, and the explorer can filter on `action`.
3. **Overlaid text** (Reso 09 p.38): hidden on that page only. The same thing happens in
   **FY2026 Reso 02 p.114** (a hidden first line read into the purpose of the row above); FY2026
   was not changed. Decide whether to name that page in `config/transparency/fy2026.toml` too.
