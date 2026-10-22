# FY2020 transparency resolutions: what a person needs to check

**Report generated:** 2026-10-22 00:35 EDT. Source: `data/fy20_tr_review.csv` (52 rows), sorted
the same way: the 11 critical items first, then by how much money each could touch. Write each
decision into `data/fy20_tr_review_decisions.csv` by `review_id` (columns `review_id, decision,
note, decided_by, decided_at`; decisions `source_error`, `parser_bug`, `accepted_as_printed` or
`needs_info`), or use the explorer's review screen and `code/validate_review_decisions.py --add`.
The pipeline never writes that file. Nothing here changes a dollar amount. Each item has a crop
in `data/overlays/` (named `r<reso>-p<page>-<review_id>.png`).

## Critical (11)

All 11 are the same thing: **`***` printed after the organization on a page whose footnotes
stop at `**`** ("* Indicates pending completion …", "** Requires a budget modification …"; no
`***` line). Checked on the rendered page (Reso 04 p.20). Kept as printed: `correction` = 1.
Named exceptions. Suggest `source_error` for all 11.

| # | review_id | Reso, page | $ | Row |
|---:|---|---|---:|---|
| 1–2 | `9411c421c481` `b11e3943ff48` | 02, p.23 | 20,000 | Koslowitz, City University of New York - Public School 99Q ($20,000) CUNY → Research Foundation of CUNY $20,000 DCLA, CASA |
| 3–4 | `5e1954e2cdf7` `cb9d34a1ebc5` | 05, p.22 | 20,000 | Louis, Museum of Contemporary African Diasporian Arts ($20,000) DYCD → $20,000 DCLA, CASA |
| 5–8, 11 | `ca48b7dd6301` `3b4dcd5e1bf4` `3ba31591bc74` `ff25ba018683` `93c41680864b` | 04, p.20 | 2,500–7,500 | Cornegy, Local Initiatives: Museum of Contemporary African Diasporian Arts ($5,000) DFTA and ($2,500) DCLA, Jewish Community Council of Greater Coney Island $5,000 DFTA, NYCHA - Louis Armstrong Tenant Association ($5,000) HPD, Universal Baptist Church $7,500 DYCD |
| 9–10 | `155eed8b8492` `d2ca501023b2` | 02, p.16 | 3,500 | Cohen, Department of Parks and Recreation ($3,500) DPR → New York Junior Tennis League $3,500 DYCD, Local Initiatives |

## Warn (41)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 12 | `6e4fd2221c4c` | 05, p.67 | 20,250 | **A separator printed without spaces at a line end**: Maisel, "Bergen Basin Community Development Corporation d/b/a Millennium Development-" / "Millennium Youth Services", $20,250 DYCD. The row above (the same organization, ($20,250)) prints "Millennium Development - Millennium Youth Services". | Kept as printed: "…Millennium Development-Millennium Youth Services". Named in `wrap_hyphen_review`. | `accepted_as_printed` |
| 13 | `7d297ebc5ead` | 01, p.55 | 10,000 | **`*` at the end of the organization**, not in the `*` column: "Queens Borough Public Library *" (City EIN 13-6400434, QBPL, $10,000, no member). | Read as pending pre-qualification (`prequal_pending` = 1), as FY2025–FY2026. | `accepted_as_printed` |
| 14–24, 26–42 | 28 items (`W.caption_format`) | 01 pp.70–80; 02 pp.85–86; 03 pp.73–87 | — | **"Chart" for "CHART"** (and on Reso 03 **"Chart # 44"** with a space after "#"), on every purpose-of-funds page of those three resolutions. | Read as the printed number. | `accepted_as_printed` |
| 45–46, 49–50 | `7a051541c9d5` `d1ee041dbda3` `ab16b2d9c357` `e75ee0530211` | 05 pp.32–33; 06 pp.17–18 | — | **"(continued)" before the fiscal year**: "CHART #16: SU-CASA (continued) - Fiscal 2020" (Reso 06: chart #10). | Read as continuations. | `accepted_as_printed` |
| 51–52 | `1e665593adec` `24ca023a8fe8` | 06, pp.25–26 | — | **"(continued)" caption with no chart number**: "CHART #: Purpose of Funds Changes - Fiscal 2020 (continued)", after chart #16 of that title on p.24. | Read as chart #16. Named exceptions (`T3.continued_number`). | `source_error` |
| 25 | `3814d11c8583` | 02, p.34 | — | **First page of a chart prints "(continued)"**: chart #12 Healthy Aging Initiative (p.33 is #11; labels "Page 18", "Page 19" run on). | Read as the chart's start. Named exception. | `source_error` |
| 47 | `65d2c665a71e` | 05, p.47 | — | **Caption repeated without "(continued)"**: chart #28 Public Health Funding Backfill (starts p.46). | Read as its continuation. Named exception. | `source_error` |
| 43, 44, 48 | `e9dbe8d9d0cb` `482acf9ead89` `23682e47634e` | 03 p.88; 04 p.84; 05 p.73 | — | **"Beating Hearts Initiative": no Agency or Amount column** (73 rows: 28, 33, 12). Unlike FY2021 and FY2022, **no note** under the table: the PDF does not say what the organizations get or from whom. | Rows kept, amount blank, `action` = `listed`. Named exceptions (`T4.no_amount`). | `accepted_as_printed` |

## Not in the review file, on purpose

- **Two charts $1 off inside themselves** (no printed total, so no check fails): Reso 01 chart
  #10 DoVE (pp.32–34, +$3,264,794 against −$3,264,793) and Reso 04 chart #11 DoVE (p.30, MOCJ
  $110,814 against $110,815 taken back). Both grids read the same digits. See Decisions.
- **4 EINs printed without a hyphen**, read as printed (`W.ein_no_hyphen`); all 4 are rows the
  old CSV missed.
- **144 line-end hyphens on 96 rows**, all read by hand (`config/transparency/fy2020.toml`);
  only item 12 is not a compound word.
- **210 rows with a cell spanning two columns** (`W.spanning_cell`): initiative names printed
  across Source and Member on purpose-of-funds charts ("Viral Hepatitis Prevention"), member
  blank, as FY2026.
- **33 `*` cells with no border of their own** (`W.made_cell_empty`, Reso 03 pp.31–43), all empty.
- **1 drawn row that prints nothing** (Reso 04 p.84, under a "Beating Hearts" chart). Counted, not
  a row.
- **Disclosure gaps** (report only): 293 FY2020 designations not found on (EIN, amount): 228
  taken back later, 48 at another amount, 9 EIN not in the disclosure, 5 City-EIN name mismatch,
  3 key already used. `data/fy20_tr_disclosure_match.csv`.
- **Rescission origins** (report only): of 1,053, 498 take back an earlier resolution's row, 196
  match a Schedule C award (retired CSV), 218 part of a larger amount, 141 not found.

## Decisions for Noel

1. **The two $1 slips** (DoVE, Reso 01 chart #10 and Reso 04 chart #11). Kept as printed. Should
   they become review rows (`source_error`)? I'd add them only if the explorer shows chart nets.
2. **"Beating Hearts Initiative" rows** (73) with no amount and, this year, no note at all. Kept
   as `listed`, as FY2021–FY2022. Decide the three years together.
3. **Item 12**, "Millennium Development-Millennium Youth Services": kept as printed, not
   respaced. `accepted_as_printed`.
