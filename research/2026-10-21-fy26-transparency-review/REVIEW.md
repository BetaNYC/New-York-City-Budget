# FY2026 transparency resolutions: what a person needs to check

**Report generated:** 2026-10-21 00:55 EDT. Source: `data/fy26_tr_review.csv` (24 rows), sorted
the same way: the 2 critical items first, then by how much money each could touch. Write each
decision into `data/fy26_tr_review_decisions.csv` by `review_id` (columns `review_id, decision,
note`; decisions `source_error`, `parser_bug`, `accepted_as_printed` or `needs_info`). The pipeline
never writes that file. Nothing here changes a dollar amount. Each row has a crop in
`data/overlays/` (named `r<reso>-p<page>-<review_id>.png`).

**Updated 2026-10-23 (#196):** two items added for Reso 02 p.114, now 26 rows (3 critical, 23
warn). They are #25 and #26 at the end, so the numbers above stay as they were.

## Critical (2)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 1 | `487d846b5a5b` | 06, p.2 | 5,000 | **A row prints no EIN.** Local Initiatives, Department of Health and Mental Hygiene **, DHMH, ($5,000), 816/120. The EIN cell is empty on the page. The row just above, the same agency and amount, prints 13-6400434. | `ein` left blank, as printed. | `source_error` |
| 2 | `01cb3c5559d1` | 06, p.5 | — | **A chart is captioned "Fiscal 2023".** Chart #2 "Aging Discretionary - Fiscal 2023" (4 rows). The resolution's own text names Fiscal 2024, 2025 and 2026 only; the chart sits between two Fiscal 2026 charts; and its rows name Council Member Zhuang, who took office in January 2024, after FY2023 ended. Almost surely a typo for 2026. | `budget_fiscal_year` kept as printed (2023). Named exception in `config/transparency/fy2026.toml`, so the check passes for this one case only. | `source_error`; Noel to decide whether the explorer should show it as 2026 (see "Decisions for Noel") |

## Warn (22)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 3 | `a47ff8c5407b` | 01, p.85 | 500,000 | **Purpose change with no matching partner.** Speaker's Initiative, YMCA of Greater New York – Bronx YMCAs ($500,000) becomes Northeast Bronx YMCA $350,000 (#8) and La Central YMCA $150,000 (#9). Same EIN, split in two. | Kept as printed. | `accepted_as_printed` |
| 4 | `58100791ada4` | 03, p.93 | 500,000 | **Purpose change across two organizations.** School-Based Immigrant Rapid Response Legal Access: Project Rousseau ($500,000) (#5) to Safe Passage Project $500,000. A different EIN on each side. | Kept as printed. | `accepted_as_printed` |
| 5 | `71b3b170be30` | 03, p.93 | 500,000 | The other half of #4. | Same. | `accepted_as_printed` |
| 6 | `3524a4050de3` | 04, p.33 | 500,000 | **The same move, reversed a month later.** Safe Passage ($500,000) (#7) back to Project Rousseau $500,000. | Same. | `accepted_as_printed` |
| 7 | `4b38509307b7` | 04, p.33 | 500,000 | The other half of #6. | Same. | `accepted_as_printed` |
| 8 | `e00249abeff9` | 01, p.85 | 350,000 | Part of #3. | Same. | `accepted_as_printed` |
| 9 | `030dc2c1c5fc` | 01, p.85 | 150,000 | Part of #3. | Same. | `accepted_as_printed` |
| 10 | `ae93444880d9` | 02, p.110 | 100,000 | **Text cut off by the next cell.** Source prints "Speaker's Initiat"; "ive" is in the PDF but hidden under the Member cell. Fortune Society, $100,000. | `source` = "Speaker's Initiat" (what shows). `hidden_text` = "source: ive". Both grids agree. | `accepted_as_printed` |
| 11 | `b37d94a2bf90` | 02, p.110 | 100,000 | Same, Fortune Society – Fordham Plaza ($100,000). | Same. | `accepted_as_printed` |
| 12 | `5446d05f734c` | 02, p.110 | 75,000 | Same, Center for Alternative Sentencing – Job Readiness Training ($75,000). The purpose is also cut: "…at risk of inc" / hidden "arceration in Coney Island." | Same. | `accepted_as_printed` |
| 13 | `ea9ee205da67` | 02, p.110 | 75,000 | Same, Center for Alternative Sentencing – ROAR, $75,000. | Same. | `accepted_as_printed` |
| 14 | `fd74d258bf10` | 03, p.81 | 18,000 | **No drawn border around one purpose cell.** 2020 Vision for Schools – Park East High School, $18,000: the last row's purpose cell has no border of its own in the PDF. | Read from the header's column width; the text is the whole sentence on the page. Image grid agrees. | `accepted_as_printed` |
| 15 | `d9a313796d9a` | 06, p.3 | 15,500 | **Line-end hyphen.** HeartShare – "Heart Paws-⏎Canine Therapy Program". Could be "Heart Paws - Canine" with the spaces lost. | Kept joined: "Heart Paws-Canine Therapy Program". The other 96 line-end hyphens are real compound words (faith-based ×66, non-profits ×22, …) and are not listed. | `accepted_as_printed` |
| 16 | `7866664b23b6` | 02, p.109 | 10,000 | Purpose cut off: Nourishing Wells, hidden "l and household resources." | As #10. | `accepted_as_printed` |
| 17 | `d9074007ab74` | 01, p.86 | 7,500 | Purpose cut off: Make: STEAM – Williamsburg HS, hidden "nd Technology." | As #10. | `accepted_as_printed` |
| 18 | `ff0c9432d996` | 01, p.86 | 7,500 | Purpose cut off: Make: STEAM – MS 582K, hidden "582)." | As #10. | `accepted_as_printed` |
| 19 | `977106b18980` | 01, p.85 | 5,000 | Purpose cut off: South Asian Youth Action, hidden "st Center Program in Council District 23." | As #10. | `accepted_as_printed` |
| 20 | `1216bfc3e536` | 02, p.109 | 5,000 | Purpose cut off: Police Department – 45th & 49th Precinct Explorers, hidden "ecinct." | As #10. | `accepted_as_printed` |
| 21 | `66242e01ad39` | 03, p.2 | 5,000 | **"\*" printed in the name, not in the `*` column.** CAIPA Foundation – Mental Health Seminars & Workshops – Council District 20 *. The `*` column is empty on every FY2026 row; this is the only asterisk. | `prequal_pending` = 1, `org_marker` = "*". | `accepted_as_printed` |
| 22 | `bf7f09c1f8e1` | 08, p.19 | 5,000 | **Organization name cut off.** "Jozef Piłsudski Institute … Modern History of Polan"; hidden "d, Inc. - Stories of Greenpoint". The old parser read this row's EIN as `of2 G3-r7e1e6n4p7o7in6t` and dropped it. | As #10. EIN 23-7164776 read cleanly. | `accepted_as_printed` |
| 23 | `ebdf1f207c90` | 08, p.19 | 5,000 | Same organization, the rescinded side, hidden " of Greenpoint". | Same. | `accepted_as_printed` |
| 24 | `b58a6462dcf7` | 01, p.67 | 0 | **A chart prints no fiscal year.** Chart #49 "Operation Backpack" (no "- Fiscal YYYY"). Reso 01's report (pp.1-2) lists Operation Backpack among the Fiscal 2026 initiatives, and the chart sits among charts #1-#60, all Fiscal 2026. | `budget_fiscal_year` blank, as printed. | `accepted_as_printed`, or Noel sets 2026 (see below) |

## Added 2026-10-23: text drawn over text on Reso 02 p.114 (#196)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 25 | `34ac4848782b` | 02, p.114 | 63,165 | **Critical: a line drawn on top of the purpose's last line.** Chart #64 "Purpose of Funds Changes", Diaspora Community Services, Inc., 11-3122295, $63,165. The page shows the purpose ending "… aiming to promote healthy development from pregnancy through early childhood." The text layer also holds "Funding supports health and wellness services for children and caregivers," (the first line of the next row's purpose, which that row's cell clips away) drawn on the same spot. Read together they came out interleaved: "pFurengdninagn csyu pthproorutsg hh …". | Named page (`T7.overlaid`, as FY2022 Reso 09 p.38): the drawn-over line is hidden and kept in `hidden_text`; `purpose` is what the page shows. Both grids agree. The next row's purpose ("focusing on …") is unchanged. | `accepted_as_printed` |
| 26 | `3466f1432813` | 02, p.114 | 63,165 | The same row, listed again as hidden text (`W.clipped_text`). | Same. | `accepted_as_printed` |

## Not in the review file, on purpose

- **173 EINs printed without a hyphen** (`131641068`). Read as printed (`ein_printed`), 9 digits in
  `ein`; flag `W.ein_no_hyphen` on the row. These are the rows the old parser dropped.
- **448 rows with no border between Source and Member** (purpose-of-funds charts). Split by the
  header's columns; both grids agree on every one. Flag `W.spanning_cell`.
- **90 rows with no drawn `*` cell**, all empty. Flag `W.made_cell_empty`.
- **96 line-end hyphens** that are compound words (listed in `fy26_tr_flags.csv`, read by hand).
- **1 zero-width character**, dropped and counted.
- **Disclosure gaps.** Report only. The FY2026 disclosure is a 2026-07-15 snapshot, after the
  last resolution. 213 FY2026 designations are not in it on (EIN, amount): 157 were taken back
  by a later resolution, 44 the EIN is there at another amount, 6 City-EIN name mismatch, 4 key
  already used, 2 EIN not in the disclosure. Every row and reason:
  `data/fy26_tr_disclosure_match.csv`.
- **Rescission origins**, report only: of 974 rescissions from organizations, 346 take back an
  earlier resolution's designation, 435 match a Schedule C award, 116 are part of a larger earlier
  amount, 77 not found (checked Schedule C, `data/fy26/pdf/schedule_c/`, since #204 on 2026-10-23;
  unchanged from the retired CSV).

## Decisions for Noel

1. **Reso 06 chart #2 "Fiscal 2023"** (#2). Keep `budget_fiscal_year` = 2023 as printed (current), or
   add a `budget_fiscal_year_corrected` = 2026 column? I'd keep as printed and let the explorer
   show the flag; a correction column can come later.
2. **Operation Backpack** (#24). Leave blank (current), or fill 2026 from the report text? I'd leave it
   blank: the chart itself does not say.
3. **`fiscal_year` on the rows** is the document year (2026, the folder and the
   `data/pdf_years.csv` row). The year whose budget a row changes is `budget_fiscal_year` (2023–2026).
   The explorer should use `budget_fiscal_year` for money and `resolution_date` for "when". OK?
