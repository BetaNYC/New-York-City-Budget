# FY2023 transparency resolutions: what a person needs to check

**Report generated:** 2026-10-21 22:20 EDT. Source: `data/fy23_tr_review.csv` (45 rows), sorted
the same way: the 18 critical items first, then by how much money each could touch. Write each
decision into `data/fy23_tr_review_decisions.csv` by `review_id` (columns `review_id, decision,
note, decided_by, decided_at`; decisions `source_error`, `parser_bug`, `accepted_as_printed` or
`needs_info`), or use the explorer's review screen and `code/validate_review_decisions.py --add`.
The pipeline never writes that file. Nothing here changes a dollar amount. Each item has a crop
in `data/overlays/` (named `r<reso>-p<page>-<review_id>.png`).

## Critical (18): `***` with no `***` footnote on the page

The row's organization ends in `***` ("correction to a designation"), but the page prints only
the `*` and `**` footnotes. Same as FY2024's two (Reso 01 p.55). For every one: kept as printed,
`org_marker` = `***`, `correction` = 1, named exception in the config. Most are a pair (the money
out and the money back in); Reso 03 p.11 and Reso 04 p.15 mark single rows too.

| # | review_id | Reso, page, row | $ | Chart | Member, organization |
|---:|---|---|---:|---|---|
| 1 | `1a4c3c2f7bb6` | 07, p.29, r1 | (100,000) | #27 LGBTQ Inclusive Curriculum, FY2022 | GLAAD, Inc., DYCD |
| 2 | `bdd1c66e221a` | 07, p.29, r2 | 100,000 | same | GLAAD, Inc., DOE |
| 3 | `21315e4ef0db` | 06, p.35, r1 | (75,000) | #29 Youth Discretionary, FY2022 | Gutierrez, Committee for Hispanic Children and Families |
| 4 | `cf484203e3fa` | 06, p.35, r2 | 75,000 | same | Gutierrez, same, "- Council District …" |
| 5 | `483cec15699e` | 04, p.15, r5 | 35,000 | #9 Cultural Immigrant Initiative, FY2023 | Department of Cultural Affairs (agency side) |
| 6 | `b35fb3edd85e` | 03, p.11, r5 | 30,000 | #2 Youth Discretionary, FY2023 | Sanchez, PowerMyLearning |
| 7 | `9772eb4759f6` | 08, p.6, r2 | (30,000) | #1 Local Initiatives, FY2023 | Holden, Department of Sanitation - Council District 30 |
| 8 | `1fcc565427be` | 08, p.6, r3 | 30,000 | same | same |
| 9 | `5168b453ef72` | 03, p.11, r3 | (25,000) | #2 Youth Discretionary, FY2023 | Sanchez, Davidson Community Center |
| 10 | `a33c100e4b06` | 04, p.15, r1 | (20,000) | #9 Cultural Immigrant Initiative, FY2023 | Narcisse, New York City H2O (DYCD) |
| 11 | `fc16f5ba3747` | 04, p.15, r2 | 20,000 | same | Narcisse, New York City H2O (DCLA) |
| 12 | `f2c48950e024` | 04, p.15, r4 | (20,000) | same | Ariola, CUNY Queensborough CC Auxiliary |
| 13 | `f38433cdc19c` | 06, p.40, r1 | (20,000) | #34 CASA, FY2022 | Ossé, Reel Stories Teen Filmmaking |
| 14 | `99f787b0ab30` | 06, p.40, r2 | 20,000 | same | Ossé, Department of Cultural Affairs |
| 15 | `958da72907d5` | 04, p.15, r3 | (15,000) | #9 Cultural Immigrant Initiative, FY2023 | Adams, CUNY Queensborough CC Auxiliary |
| 16 | `b99b929eed56` | 06, p.34, r3 | (10,000) | #28 Local Initiatives, FY2022 | Brooks-Powers, District 29Q Community Education Council (EIN 13-6400434) |
| 17 | `7cd8a2bbd278` | 06, p.34, r4 | 10,000 | same | same, EIN 69-0210637 (an EIN correction) |
| 18 | `70f32aed1485` | 03, p.11, r4 | (5,000) | #2 Youth Discretionary, FY2023 | Sanchez, Literacy (LINC) |

**Suggest:** `source_error` for all 18 (the marker is real; the page left out its footnote).
Reso 02 p.8 shows what the footnote says that year ("Correction and/or Reversal of a change
made in a previous Transparency Resolution").

## Warn (27)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 19–20 | `5907cbc86aa4` `405fd1cd5d65` | 08, pp.54–55 | 83,000 | **Purpose-of-funds pair with two EINs.** Fund for the City of New York ($83,000, p.54) → Justice Innovation, Inc. $83,000 (p.55), DHMH. The change moves the money to another organization, so the "same EIN" pairing check finds no partner. | Kept as printed. | `accepted_as_printed` |
| 21–22 | `660f4cd228c8` `a06d68da8e0f` | 05, p.43 | 61,000 | Same: Department of Small Business Services ($61,000) → Pathways To Apprenticeship $61,000. | Same. | `accepted_as_printed` |
| 23–24 | `ba79dd7f1663` `03ee7848cf74` | 11, p.19 | 50,000 | **The City's EIN on a nonprofit.** Speaker: Fort Greene Council, Inc. - Mount Ararat Senior Center (11-2300840), ($50,000) → "Fort Greene Council, Inc." $50,000 printed with **13-6400434**, the City's EIN. Checked on the rendered page. | `ein` = 136400434, as printed. The row is not an agency side (it has a member). | `source_error` on `03ee7848cf74`; `accepted_as_printed` on `ba79dd7f1663` |
| 25 | `8d1f42dbadb4` | 02, p.83 | 36,868 | **Text cut off by the next cell.** SAGE - "Senior Housing Navigatio", the "n" hidden under the EIN cell. | `org` keeps what shows; `hidden_text` = "org: n". Both grids agree. | `accepted_as_printed` |
| 26 | `83b3774f3deb` | 01, p.45 | 30,000 | Same: North Flatbush Avenue DMA - "North Flatbush Green & Clean" then a hidden "-", then "Council District 35". | Same. | `accepted_as_printed` |
| 27 | `61be34bd2af0` | 01, p.13 | 15,000 | Same: Chess-in-the-Schools - "… Comprehensive Chess Education", hidden "-", "Council District 29". | Same. | `accepted_as_printed` |
| 28–29 | `f0437acc6ccf` `a39c30bd3383` | 08, p.54 | 10,000 | Purpose-of-funds pair with two EINs: Department of Health and Mental Hygiene ($10,000) → Entertainers for Education Alliance $10,000. | Kept as printed. | `accepted_as_printed` |
| 30 | `64ac34892422` | 01, p.85 | 4,000 | **Text cut off by the next cell.** Hudson, Berean Community and Family Life Center - "Summer Day Camp & Enrichm", "ent Academy" hidden under the EIN cell. | `org` keeps what shows; `hidden_text` = "org: ent Academy". | `accepted_as_printed` |
| 31–32 | `fa1a06056129` `3a6b20f8c756` | 07, p.27 | 0 | **Amount printed as $0.** De La Rosa: Grand Slam foundation, Inc. $0 and Department of Small Business Services $0, chart #25 Neighborhood Development Grant Initiative (FY2022). Checked on the rendered page. | Kept: amount 0, `action` = designate. | `source_error` (a change of $0 changes nothing; maybe a placeholder) |
| 33 | `2222960f81cb` | 01, p.81 | — | **Caption "CHART 41:"** (no "#"). | Read as chart #41; its 4 rows kept. | `accepted_as_printed` |
| 34 | `c0ca3603aa9f` | 01, p.66 | — | Caption "- FY 2023" for "- Fiscal 2023" (chart #26). | Budget year 2023. | `accepted_as_printed` |
| 35–37 | `4d279dd849aa` `e68a283636fa` `a81bbc456a72` | 09, pp.21, 22, 25 | — | Same, charts #19, #20, #23. | Same. | `accepted_as_printed` |
| 38 | `94666477d5c1` | 03, p.20 | — | Caption "(cpntinued)" (chart #8, A Greener NYC). | Read as continued. | `accepted_as_printed` |
| 39 | `77d3e9058811` | 02, p.92 | — | Caption "CHART #45 Food Pantries" (no ":"). | Read as chart #45. | `accepted_as_printed` |
| 40 | `7a418cc6eee6` | 05, p.37 | — | Same, "CHART #31 Crisis Management System". | Read as chart #31. | `accepted_as_printed` |
| 41 | `fabf5c9da0dc` | 08, p.32 | — | **First page of chart #25 prints "(continued)".** p.31 is chart #24; nothing before p.32 prints #25. | Read as the start of chart #25 (Legal Aid Society, $1,000,000 MOCJ → DYCD). Named exception. | `source_error` |
| 42 | `527964f8de17` | 08, p.44 | — | **No "Page n" label** (chart #37, Fiscal 2022). p.43 "Page 41", p.45 "Page 43". | Named exception. | `accepted_as_printed` |
| 43–45 | `ced11a224903` `347104084907` `56ab9fad0d80` | 09, pp.29–31 | — | Same, charts #27–#29 (Fiscal 2022). p.28 "Page 26", p.32 "Page 30". | Named exceptions. | `accepted_as_printed` |

## Not in the review file, on purpose

- **61 EINs printed without a hyphen**, read as printed; flag `W.ein_no_hyphen`. These are 61 of
  the 70 rows the old CSV missed.
- **4 empty drawn rows** (Reso 01 p.67, Reso 03 p.83, Reso 06 p.53 ×2): nothing printed, so no
  value to check. Listed in `fy23_tr_checks.txt` (T5).
- **33 line-end hyphens on 31 rows**, all read by hand: compound words or names (26 are
  "low-income" on Reso 08 pp.55–58). Flag `W5.wrap_hyphen`.
- **226 rows with no drawn `*` cell**, all empty (`W.made_cell_empty`); 144 rows with a cell
  spanning two columns (`W.spanning_cell`), as in FY2026.
- **Disclosure gaps** (report only): 525 FY2023 designations not found on (EIN, amount): 403 taken
  back later, 88 at another amount, 20 key already used, 10 City-EIN name mismatch, 4 EIN not in
  the disclosure. `data/fy23_tr_disclosure_match.csv`.
- **Rescission origins** (report only): of 1,320, 671 take back an earlier resolution's row, 343
  match a Schedule C award (retired CSV), 104 part of a larger amount, 202 not found.

## Decisions for Noel

1. **Fort Greene Council printed with the City's EIN** (#23–24). I'd call it `source_error` and
   keep 13-6400434 as printed. (Purpose-of-funds rows are not matched to the disclosure, so it
   changes no report number.)
2. **Clipped names** (#25–27, #30). Values keep what shows (the FY2026 rule), so "Enrichm" and
   "Navigatio". Keep, or add the hidden text back? I'd keep: the explorer can show `hidden_text`.
3. **$0 rows** (#31–32). Kept as printed. Nothing to decide unless you want them dropped from
   totals (they add $0 either way).
