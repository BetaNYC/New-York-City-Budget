# NYC Budget — Data QA Report

**Report generated:** 2026-07-15  
**Data current as of:** 2026-07-15 (files under `data/`)  
**Tool:** `code/validate_data.py`

**Verdict:** FAIL — 272 files, 2 hard failure(s), 412 soft advisory(ies).

Severity: HARD (exit 1) = schema drift, malformed row, non-numeric amount, or malformed EIN. SOFT (exit 0) = zeros, sign anomalies, outliers, duplicates, column-bleed residuals, coverage notes. See the module docstring for the full check list and rationale.

## Hard failures

- **[schema]** `combined/all_years_awards.csv` — unexpected columns: ['category_canonical', 'initiative_canonical']
- **[schema]** `combined/all_years_initiatives.csv` — unexpected columns: ['category_canonical', 'initiative_canonical']

## EIN coverage (feeds the MCP award-tool decision)

Valid 9-digit EINs / total rows, per year and EIN-bearing doctype. Initiatives, terms, and capital carry no EIN by design and are omitted. Transparency uses the `*_transparency_all.csv` file (per-reso components excluded to avoid double count).

| FY | doctype | valid EIN / rows | coverage |
|---|---|---|---|
| FY2010 | transparency | 1788/1788 | 100.0% |
| FY2011 | transparency | 1545/1545 | 100.0% |
| FY2012 | transparency | 932/932 | 100.0% |
| FY2013 | transparency | 1857/1857 | 100.0% |
| FY2014 | transparency | 166/166 | 100.0% |
| FY2015 | appendix | 0/0 | 0.0% |
| FY2015 | awards | 652/652 | 100.0% |
| FY2015 | transparency | 3047/3047 | 100.0% |
| FY2016 | appendix | 0/0 | 0.0% |
| FY2016 | awards | 335/335 | 100.0% |
| FY2016 | transparency | 4156/4156 | 100.0% |
| FY2017 | appendix | 0/0 | 0.0% |
| FY2017 | awards | 364/364 | 100.0% |
| FY2017 | transparency | 4656/4656 | 100.0% |
| FY2018 | appendix | 422/422 | 100.0% |
| FY2018 | awards | 480/480 | 100.0% |
| FY2018 | transparency | 5366/5366 | 100.0% |
| FY2019 | appendix | 0/0 | 0.0% |
| FY2019 | awards | 846/846 | 100.0% |
| FY2019 | transparency | 7090/7090 | 100.0% |
| FY2020 | appendix | 0/0 | 0.0% |
| FY2020 | awards | 2841/2841 | 100.0% |
| FY2020 | transparency | 5319/5319 | 100.0% |
| FY2021 | appendix | 4310/4310 | 100.0% |
| FY2021 | awards | 1810/1810 | 100.0% |
| FY2021 | transparency | 4463/4463 | 100.0% |
| FY2022 | appendix | 4182/4182 | 100.0% |
| FY2022 | awards | 1492/1492 | 100.0% |
| FY2022 | transparency | 7768/7768 | 100.0% |
| FY2023 | appendix | 4056/4056 | 100.0% |
| FY2023 | awards | 1848/1848 | 100.0% |
| FY2023 | transparency | 8354/8354 | 100.0% |
| FY2024 | appendix | 3911/3911 | 100.0% |
| FY2024 | awards | 5368/5368 | 100.0% |
| FY2024 | transparency | 3294/3294 | 100.0% |
| FY2025 | appendix | 3920/3920 | 100.0% |
| FY2025 | awards | 5646/5646 | 100.0% |
| FY2026 | appendix | 3914/3914 | 100.0% |
| FY2026 | awards | 5838/5838 | 100.0% |
| FY2026 | transparency | 4755/4755 | 100.0% |
| FY2027 | appendix | 3860/3860 | 100.0% |
| FY2027 | awards | 6118/6118 | 100.0% |

## Reconciliation roll-up

Parsed from every `*_reconciliation.txt`. Transparency prints no totals → N/A by nature. PARTIAL = documented in-source arithmetic diffs, not extraction errors.

| FY | doctype | ratio | status |
|---|---|---|---|
| FY2009 | schedule_c | 21/22 | PARTIAL (1 in-source diff) |
| FY2010 | schedule_c | 21/21 | PASS |
| FY2010 | transparency | — | N/A (no printed totals) |
| FY2011 | schedule_c | 18/19 | PARTIAL (1 in-source diff) |
| FY2011 | transparency | — | N/A (no printed totals) |
| FY2012 | schedule_c | 16/16 | PASS |
| FY2012 | transparency | — | N/A (no printed totals) |
| FY2013 | schedule_c | 17/17 | PASS |
| FY2013 | transparency | — | N/A (no printed totals) |
| FY2014 | schedule_c | 17/17 | PASS |
| FY2014 | transparency | — | N/A (no printed totals) |
| FY2015 | schedule_c | 24/24 | PASS |
| FY2015 | transparency | — | N/A (no printed totals) |
| FY2016 | schedule_c | 24/26 | PARTIAL (2 in-source diff) |
| FY2016 | transparency | — | N/A (no printed totals) |
| FY2017 | schedule_c | 24/27 | PARTIAL (3 in-source diff) |
| FY2017 | transparency | — | N/A (no printed totals) |
| FY2018 | schedule_c | 24/27 | PARTIAL (3 in-source diff) |
| FY2018 | transparency | — | N/A (no printed totals) |
| FY2019 | schedule_c | 27/28 | PARTIAL (1 in-source diff) |
| FY2019 | transparency | — | N/A (no printed totals) |
| FY2020 | capital | 23/23 | PASS |
| FY2020 | schedule_c | 27/28 | PARTIAL (1 in-source diff) |
| FY2020 | transparency | — | N/A (no printed totals) |
| FY2021 | schedule_c | 25/26 | PARTIAL (1 in-source diff) |
| FY2021 | transparency | — | N/A (no printed totals) |
| FY2022 | capital | 32/32 | PASS |
| FY2022 | schedule_c | 24/26 | PARTIAL (2 in-source diff) |
| FY2022 | transparency | — | N/A (no printed totals) |
| FY2023 | capital | 30/30 | PASS |
| FY2023 | schedule_c | 26/26 | PASS |
| FY2023 | transparency | — | N/A (no printed totals) |
| FY2024 | capital | 30/30 | PASS |
| FY2024 | schedule_c | 24/26 | PARTIAL (2 in-source diff) |
| FY2024 | transparency | — | N/A (no printed totals) |
| FY2025 | capital | — | N/A (no printed totals) |
| FY2025 | capital | 30/30 | PASS |
| FY2025 | schedule_c | 24/26 | PARTIAL (2 in-source diff) |
| FY2026 | capital | 31/31 | PASS |
| FY2026 | schedule_c | 24/25 | PARTIAL (1 in-source diff) |
| FY2026 | transparency | — | N/A (no printed totals) |
| FY2027 | capital | 24/26 | PARTIAL (2 in-source diff) |
| FY2027 | schedule_c | 25/25 | PASS |

## Per-file findings

| file | rows | EIN cov | hard | soft findings |
|---|---|---|---|---|
| `combined/all_years_awards.csv` | 33638 | 100% | 1 | duplicate: 143 duplicate row instance(s); e.g. x2: ['FY17', 'HOUSING', 'Housing', 'Community Housing Preservation Strategies']...; column_bleed: 106 suspected surname-in-organization residual(s); e.g. line 489: 'Hudson Guild' |
| `combined/all_years_initiatives.csv` | 2598 | — | 1 | — |
| `fy09/schedule_c/fy09_schedule_c_initiatives.csv` | 123 | — | 0 | — |
| `fy10/schedule_c/fy10_schedule_c_initiatives.csv` | 124 | — | 0 | — |
| `fy10/transparency-resolutions/fy10_transparency_all.csv` | 1788 | 100% | 0 | fiscal_year: 58 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1730 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['10', '2010-04-29', 'LocalInitiatives', '']... |
| `fy10/transparency-resolutions/reso01_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy10/transparency-resolutions/reso02_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy10/transparency-resolutions/reso03_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy10/transparency-resolutions/reso04_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy10/transparency-resolutions/reso05_transparency_designations.csv` | 86 | 100% | 0 | fiscal_year: 86 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso06_transparency_designations.csv` | 214 | 100% | 0 | fiscal_year: 214 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso07_transparency_designations.csv` | 195 | 100% | 0 | fiscal_year: 195 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso08_transparency_designations.csv` | 501 | 100% | 0 | fiscal_year: 501 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso09_transparency_designations.csv` | 317 | 100% | 0 | fiscal_year: 317 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso10_transparency_designations.csv` | 309 | 100% | 0 | fiscal_year: 58 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 251 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['10', '2010-04-29', 'LocalInitiatives', '']... |
| `fy10/transparency-resolutions/reso11_transparency_designations.csv` | 95 | 100% | 0 | fiscal_year: 95 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso12_transparency_designations.csv` | 71 | 100% | 0 | fiscal_year: 71 row(s) with empty fiscal_year |
| `fy11/schedule_c/fy11_schedule_c_initiatives.csv` | 110 | — | 0 | — |
| `fy11/transparency-resolutions/fy11_transparency_all.csv` | 1545 | 100% | 0 | fiscal_year: 26 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1519 row(s) with empty fiscal_year; duplicate: 2 duplicate row instance(s); e.g. x2: ['3', '2010-09-29', 'Food Pantries', '']... |
| `fy11/transparency-resolutions/reso01_transparency_designations.csv` | 262 | 100% | 0 | fiscal_year: 262 row(s) with empty fiscal_year |
| `fy11/transparency-resolutions/reso02_transparency_designations.csv` | 226 | 100% | 0 | fiscal_year: 226 row(s) with empty fiscal_year |
| `fy11/transparency-resolutions/reso03_transparency_designations.csv` | 435 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 427 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['3', '2010-09-29', 'Food Pantries', '']... |
| `fy11/transparency-resolutions/reso04_transparency_designations.csv` | 96 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 88 row(s) with empty fiscal_year |
| `fy11/transparency-resolutions/reso05_transparency_designations.csv` | 211 | 100% | 0 | fiscal_year: 211 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['5', '2010-11-17', 'HIV/AIDS-FaithBasedInitiative', '']... |
| `fy11/transparency-resolutions/reso06_transparency_designations.csv` | 190 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 184 row(s) with empty fiscal_year |
| `fy11/transparency-resolutions/reso07_transparency_designations.csv` | 125 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 121 row(s) with empty fiscal_year |
| `fy11/transparency-resolutions/reso08_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy11/transparency-resolutions/reso09_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy11/transparency-resolutions/reso10_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy12/schedule_c/fy12_schedule_c_initiatives.csv` | 97 | — | 0 | — |
| `fy12/transparency-resolutions/fy12_transparency_all.csv` | 932 | 100% | 0 | fiscal_year: 40 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 549 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2011-11-03', 'HIV/AIDS Faith Based Initiative (cont.)', '']...; column_bleed: 4 suspected surname-in-organization residual(s); e.g. line 118: 'Hudson Guild' |
| `fy12/transparency-resolutions/reso01_transparency_designations.csv` | 134 | 100% | 0 | fiscal_year: 134 row(s) with empty fiscal_year; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 118: 'Hudson Guild' |
| `fy12/transparency-resolutions/reso02_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy12/transparency-resolutions/reso03_transparency_designations.csv` | 168 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 162 row(s) with empty fiscal_year |
| `fy12/transparency-resolutions/reso04_transparency_designations.csv` | 258 | 100% | 0 | fiscal_year: 7 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 251 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2011-11-03', 'HIV/AIDS Faith Based Initiative (cont.)', '']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 49: 'Brewer WellnessintheSchools,Inc.' |
| `fy12/transparency-resolutions/reso05_transparency_designations.csv` | 42 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 2 row(s) with empty fiscal_year |
| `fy12/transparency-resolutions/reso06_transparency_designations.csv` | 200 | 100% | 0 | column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 156: 'Gennaro 11-2267876 Young Israel of Queens Valley' |
| `fy12/transparency-resolutions/reso07_transparency_designations.csv` | 130 | 100% | 0 | fiscal_year: 9 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy13/schedule_c/fy13_schedule_c_initiatives.csv` | 121 | — | 0 | — |
| `fy13/transparency-resolutions/fy13_transparency_all.csv` | 1857 | 100% | 0 | fiscal_year: 70 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 426 row(s) with empty fiscal_year; duplicate: 10 duplicate row instance(s); e.g. x2: ['2', '2012-08-22', 'YouthDiscretionary-Fiscal2013', '2013']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 547: 'Gennaro CatholicCharitiesNeighborhoodServices -Colin-NewellE' |
| `fy13/transparency-resolutions/reso01_transparency_designations.csv` | 587 | 100% | 0 | fiscal_year: 3 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 244 row(s) with empty fiscal_year; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 547: 'Gennaro CatholicCharitiesNeighborhoodServices -Colin-NewellE' |
| `fy13/transparency-resolutions/reso02_transparency_designations.csv` | 227 | 100% | 0 | fiscal_year: 3 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 128 row(s) with empty fiscal_year; duplicate: 2 duplicate row instance(s); e.g. x2: ['2', '2012-08-22', 'YouthDiscretionary-Fiscal2013', '2013']... |
| `fy13/transparency-resolutions/reso03_transparency_designations.csv` | 374 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 49 row(s) with empty fiscal_year; duplicate: 3 duplicate row instance(s); e.g. x2: ['3', '2012-09-24', 'Anti-GunViolenceInitiative-ConflictPreventionRemediation-FY2013', '']... |
| `fy13/transparency-resolutions/reso04_transparency_designations.csv` | 130 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['4', '2012-10-11', 'LocalInitiatives-Fiscal2013', '2013']... |
| `fy13/transparency-resolutions/reso05_transparency_designations.csv` | 215 | 100% | 0 | duplicate: 2 duplicate row instance(s); e.g. x2: ['5', '2012-11-13', 'HIV/AIDSFaithBasedInitiative-Fiscal2013', '2013']... |
| `fy13/transparency-resolutions/reso06_transparency_designations.csv` | 103 | 100% | 0 | — |
| `fy13/transparency-resolutions/reso08_transparency_designations.csv` | 55 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['8', '2013-01-23', 'LocalInitiatives-Fiscal2013', '2013']... |
| `fy13/transparency-resolutions/reso09_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy13/transparency-resolutions/reso12_transparency_designations.csv` | 166 | 100% | 0 | fiscal_year: 48 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 5 row(s) with empty fiscal_year |
| `fy14/schedule_c/fy14_schedule_c_initiatives.csv` | 123 | — | 0 | — |
| `fy14/transparency-resolutions/fy14_transparency_all.csv` | 166 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['1', '2014-04-29', 'CulturalAfterSchoolAdventure-Fiscal2014', '2014']... |
| `fy14/transparency-resolutions/reso01_transparency_designations.csv` | 36 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['1', '2014-04-29', 'CulturalAfterSchoolAdventure-Fiscal2014', '2014']... |
| `fy14/transparency-resolutions/reso02_transparency_designations.csv` | 80 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy14/transparency-resolutions/reso03_transparency_designations.csv` | 50 | 100% | 0 | — |
| `fy15/schedule_c/fy15_appendix_a_aging.csv` | 0 | 0% | 0 | — |
| `fy15/schedule_c/fy15_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy15/schedule_c/fy15_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy15/schedule_c/fy15_schedule_c_awards.csv` | 652 | 100% | 0 | column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 489: 'Hudson Guild' |
| `fy15/schedule_c/fy15_schedule_c_initiatives.csv` | 140 | — | 0 | — |
| `fy15/terms/fy15_terms_and_conditions.csv` | 17 | — | 0 | — |
| `fy15/transparency-resolutions/fy15_transparency_all.csv` | 3047 | 100% | 0 | fiscal_year: 160 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 23 duplicate row instance(s); e.g. x2: ['1', '2014-07-24', 'Local Initiatives - Fiscal 2015', '2015']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 1523: 'Hudson Guild' |
| `fy15/transparency-resolutions/reso01_transparency_designations.csv` | 291 | 100% | 0 | fiscal_year: 5 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['1', '2014-07-24', 'Local Initiatives - Fiscal 2015', '2015']... |
| `fy15/transparency-resolutions/reso02_transparency_designations.csv` | 548 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy15/transparency-resolutions/reso03_transparency_designations.csv` | 875 | 100% | 0 | fiscal_year: 42 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 5 duplicate row instance(s); e.g. x2: ['3', '2014-09-23', 'Local Initiatives - Fiscal 2015', '2015']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 684: 'Hudson Guild' |
| `fy15/transparency-resolutions/reso04_transparency_designations.csv` | 275 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2014-10-07', 'Local Initiatives - Fiscal 2015', '2015']... |
| `fy15/transparency-resolutions/reso05_transparency_designations.csv` | 121 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['5', '2014-10-22', 'Local Initiatives - Fiscal 2015', '2015']... |
| `fy15/transparency-resolutions/reso06_transparency_designations.csv` | 170 | 100% | 0 | fiscal_year: 11 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['6', '2014-11-25', 'FoodPantriesInitiative-Fiscal2015', '2015']... |
| `fy15/transparency-resolutions/reso07_transparency_designations.csv` | 284 | 100% | 0 | duplicate: 6 duplicate row instance(s); e.g. x2: ['7', '2014-12-17', 'Local Initiatives - Fiscal 2015', '2015']... |
| `fy15/transparency-resolutions/reso08_transparency_designations.csv` | 40 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy15/transparency-resolutions/reso09_transparency_designations.csv` | 117 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy15/transparency-resolutions/reso10_transparency_designations.csv` | 68 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy15/transparency-resolutions/reso11_transparency_designations.csv` | 178 | 100% | 0 | fiscal_year: 26 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['11', '2015-02-26', 'LocalInitiatives-Fiscal2014', '2014']... |
| `fy15/transparency-resolutions/reso12_transparency_designations.csv` | 80 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['12', '2015-03-31', 'Local Initiatives - Fiscal 2015', '2015']... |
| `fy16/schedule_c/fy16_appendix_a_aging.csv` | 0 | 0% | 0 | — |
| `fy16/schedule_c/fy16_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy16/schedule_c/fy16_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy16/schedule_c/fy16_schedule_c_awards.csv` | 335 | 100% | 0 | column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 80: 'Hudson Guild 13-5562989 * $29,730 Lenox Hill Neighborhood Ho' |
| `fy16/schedule_c/fy16_schedule_c_initiatives.csv` | 193 | — | 0 | — |
| `fy16/terms/fy16_terms_and_conditions.csv` | 30 | — | 0 | — |
| `fy16/transparency-resolutions/fy16_transparency_all.csv` | 4156 | 100% | 0 | fiscal_year: 92 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 9 row(s) with empty fiscal_year; duplicate: 28 duplicate row instance(s); e.g. x2: ['2', '2015-08-13', 'Local Initiatives - Fiscal 2016', '2016']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 729: 'Hudson Guild' |
| `fy16/transparency-resolutions/reso01_transparency_designations.csv` | 432 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy16/transparency-resolutions/reso02_transparency_designations.csv` | 431 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['2', '2015-08-13', 'Local Initiatives - Fiscal 2016', '2016']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 297: 'Hudson Guild' |
| `fy16/transparency-resolutions/reso03_transparency_designations.csv` | 883 | 100% | 0 | fiscal_year: 22 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 7 row(s) with empty fiscal_year; duplicate: 7 duplicate row instance(s); e.g. x2: ['3', '2015-09-17', 'Local Initiatives - Fiscal 2016', '2016']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 760: 'Joseph P. Addabbo Family Health Center, Inc.' |
| `fy16/transparency-resolutions/reso04_transparency_designations.csv` | 516 | 100% | 0 | — |
| `fy16/transparency-resolutions/reso05_transparency_designations.csv` | 315 | 100% | 0 | fiscal_year: 2 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 11 duplicate row instance(s); e.g. x3: ['5', '2015-10-15', 'Cultural After School Adventure (CASA) - Fiscal 2016', '2016']... |
| `fy16/transparency-resolutions/reso06_transparency_designations.csv` | 161 | 100% | 0 | column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 17: 'Williams Top Development Corporation** 11-3409359 Top Develo' |
| `fy16/transparency-resolutions/reso07_transparency_designations.csv` | 471 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['7', '2015-11-24', 'YouthDiscretionary-Fiscal2016', '2016']... |
| `fy16/transparency-resolutions/reso08_transparency_designations.csv` | 208 | 100% | 0 | fiscal_year: 14 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['8', '2015-12-16', 'Healthy Aging Initiative - Fiscal 2016', '2016']... |
| `fy16/transparency-resolutions/reso09_transparency_designations.csv` | 190 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy16/transparency-resolutions/reso10_transparency_designations.csv` | 186 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 2 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['10', '2016-02-24', 'Anti-Gun Violence - Art a Catalyst for Change Initiative - Fiscal 2016', '2016']... |
| `fy16/transparency-resolutions/reso11_transparency_designations.csv` | 88 | 100% | 0 | duplicate: 2 duplicate row instance(s); e.g. x2: ['11', '2016-03-22', 'NYC Digital Inclusion and Literacy Initiative - Fiscal 2016', '2016']... |
| `fy16/transparency-resolutions/reso12_transparency_designations.csv` | 115 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy16/transparency-resolutions/reso13_transparency_designations.csv` | 160 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy17/schedule_c/fy17_appendix_a_aging.csv` | 0 | 0% | 0 | — |
| `fy17/schedule_c/fy17_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy17/schedule_c/fy17_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy17/schedule_c/fy17_schedule_c_awards.csv` | 364 | 100% | 0 | duplicate: 2 duplicate row instance(s); e.g. x2: ['HOUSING', 'Community Housing Preservation Strategies', 'initiative_provider', '']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 42: 'Williams East Flatbush Village, Inc.' |
| `fy17/schedule_c/fy17_schedule_c_initiatives.csv` | 133 | — | 0 | — |
| `fy17/terms/fy17_terms_and_conditions.csv` | 30 | — | 0 | — |
| `fy17/transparency-resolutions/fy17_transparency_all.csv` | 4656 | 100% | 0 | fiscal_year: 213 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 2 row(s) with empty fiscal_year; duplicate: 50 duplicate row instance(s); e.g. x2: ['1', '2016-07-14', 'Cultural After-School Adventure (CASA) - Fiscal 2017', '2017']...; column_bleed: 4 suspected surname-in-organization residual(s); e.g. line 876: 'Mealy Reel Works Teen Film Making, Inc.' |
| `fy17/transparency-resolutions/reso01_transparency_designations.csv` | 684 | 100% | 0 | fiscal_year: 26 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 8 duplicate row instance(s); e.g. x2: ['1', '2016-07-14', 'Cultural After-School Adventure (CASA) - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso02_transparency_designations.csv` | 1019 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 9 duplicate row instance(s); e.g. x2: ['2', '2016-08-16', 'Local Initiatives - Fiscal 2017', '2017']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 192: 'Mealy Reel Works Teen Film Making, Inc.' |
| `fy17/transparency-resolutions/reso03_transparency_designations.csv` | 421 | 100% | 0 | fiscal_year: 41 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['3', '2016-09-14', 'NYC Cleanup - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso04_transparency_designations.csv` | 550 | 100% | 0 | fiscal_year: 2 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2016-09-28', 'Parks Equity Initiative - Fiscal 2017', '2017']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 472: 'Hudson Guild' |
| `fy17/transparency-resolutions/reso05_transparency_designations.csv` | 458 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 9 duplicate row instance(s); e.g. x2: ['5', '2016-10-27', 'Cultural After-School Adventure (CASA) - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso06_transparency_designations.csv` | 166 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy17/transparency-resolutions/reso07_transparency_designations.csv` | 332 | 100% | 0 | fiscal_year: 7 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 7 duplicate row instance(s); e.g. x2: ['7', '2016-12-15', 'Anti-Poverty Initiative - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso08_transparency_designations.csv` | 303 | 100% | 0 | fiscal_year: 7 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 2 row(s) with empty fiscal_year; duplicate: 2 duplicate row instance(s); e.g. x2: ['8', '2017-01-18', 'Parks Equity Initiative - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso09_transparency_designations.csv` | 161 | 100% | 0 | fiscal_year: 9 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy17/transparency-resolutions/reso10_transparency_designations.csv` | 122 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy17/transparency-resolutions/reso11_transparency_designations.csv` | 129 | 100% | 0 | fiscal_year: 2 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['11', '2017-03-16', 'Parks Equity Initiative - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso12_transparency_designations.csv` | 130 | 100% | 0 | fiscal_year: 41 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy17/transparency-resolutions/reso13_transparency_designations.csv` | 181 | 100% | 0 | fiscal_year: 34 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['13', '2017-06-06', 'Youth Discretionary - Fiscal 2017', '2017']... |
| `fy18/schedule_c/fy18_appendix_a_aging.csv` | 422 | 100% | 0 | — |
| `fy18/schedule_c/fy18_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy18/schedule_c/fy18_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy18/schedule_c/fy18_schedule_c_awards.csv` | 480 | 100% | 0 | duplicate: 5 duplicate row instance(s); e.g. x2: ['Housing', 'Community Housing Preservation Strategies', 'initiative_provider', '']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 123: 'Joseph P. Addabbo Family Health Center, Inc., The 06-1181226' |
| `fy18/schedule_c/fy18_schedule_c_initiatives.csv` | 128 | — | 0 | — |
| `fy18/terms/fy18_terms_and_conditions.csv` | 33 | — | 0 | — |
| `fy18/transparency-resolutions/fy18_transparency_all.csv` | 5366 | 100% | 0 | fiscal_year: 345 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1 row(s) with empty fiscal_year; duplicate: 51 duplicate row instance(s); e.g. x2: ['1', '2017-06-21', 'Local Initiatives - Fiscal 2018', '2018']...; column_bleed: 4 suspected surname-in-organization residual(s); e.g. line 3262: 'Hudson Guild' |
| `fy18/transparency-resolutions/reso01_transparency_designations.csv` | 885 | 100% | 0 | fiscal_year: 25 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 9 duplicate row instance(s); e.g. x2: ['1', '2017-06-21', 'Local Initiatives - Fiscal 2018', '2018']... |
| `fy18/transparency-resolutions/reso02_transparency_designations.csv` | 808 | 100% | 0 | fiscal_year: 31 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['2', '2017-07-20', 'Parks Equity Initiative - Fiscal 2018', '2018']... |
| `fy18/transparency-resolutions/reso03_transparency_designations.csv` | 1176 | 100% | 0 | fiscal_year: 34 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 19 duplicate row instance(s); e.g. x2: ['3', '2017-08-24', 'Cultural After-School Adventure (CASA) - Fiscal 2018', '2018']... |
| `fy18/transparency-resolutions/reso04_transparency_designations.csv` | 462 | 100% | 0 | fiscal_year: 34 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 7 duplicate row instance(s); e.g. x2: ['4', '2017-09-27', 'Local Initiatives - Fiscal 2018', '2018']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 393: 'Hudson Guild' |
| `fy18/transparency-resolutions/reso05_transparency_designations.csv` | 503 | 100% | 0 | fiscal_year: 60 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['5', '2017-10-31', 'Local Initiatives - Fiscal 2018', '2018']... |
| `fy18/transparency-resolutions/reso06_transparency_designations.csv` | 299 | 100% | 0 | fiscal_year: 47 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['6', '2017-11-30', 'Purpose of Funds Changes - Fiscal 2018', '2018']... |
| `fy18/transparency-resolutions/reso07_transparency_designations.csv` | 231 | 100% | 0 | fiscal_year: 30 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 78: 'Louis Armstrong House Museum' |
| `fy18/transparency-resolutions/reso08_transparency_designations.csv` | 402 | 100% | 0 | fiscal_year: 48 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['8', '2018-02-15', 'Aging Discretionary - Fiscal 2018', '2018']...; column_bleed: 2 suspected surname-in-program residual(s); e.g. line 105: 'Hudson High School Of Learning Technologies (M437)' |
| `fy18/transparency-resolutions/reso09_transparency_designations.csv` | 181 | 100% | 0 | fiscal_year: 2 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1 row(s) with empty fiscal_year |
| `fy18/transparency-resolutions/reso10_transparency_designations.csv` | 88 | 100% | 0 | — |
| `fy18/transparency-resolutions/reso11_transparency_designations.csv` | 83 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy18/transparency-resolutions/reso12_transparency_designations.csv` | 248 | 100% | 0 | fiscal_year: 16 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['12', '2018-06-14', 'Local Initiatives - Fiscal 2018', '2018']... |
| `fy19/schedule_c/fy19_appendix_a_aging.csv` | 0 | 0% | 0 | — |
| `fy19/schedule_c/fy19_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy19/schedule_c/fy19_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy19/schedule_c/fy19_schedule_c_awards.csv` | 846 | 100% | 0 | duplicate: 2 duplicate row instance(s); e.g. x2: ['HOUSING', 'Community Housing Preservation Strategies', 'initiative_provider', '']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 318: 'Joseph P. Addabbo Family Health Center, Inc., The' |
| `fy19/schedule_c/fy19_schedule_c_initiatives.csv` | 133 | — | 0 | — |
| `fy19/transparency-resolutions/fy19_transparency_all.csv` | 7090 | 100% | 0 | fiscal_year: 713 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 74 duplicate row instance(s); e.g. x3: ['1', '2018-07-18', 'Local Initiatives - Fiscal 2019', '2019']...; column_bleed: 18 suspected surname-in-organization residual(s); e.g. line 1419: 'Hudson Guild' |
| `fy19/transparency-resolutions/reso01_transparency_designations.csv` | 1702 | 100% | 0 | fiscal_year: 78 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 21 duplicate row instance(s); e.g. x3: ['1', '2018-07-18', 'Local Initiatives - Fiscal 2019', '2019']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 1419: 'Hudson Guild' |
| `fy19/transparency-resolutions/reso02_transparency_designations.csv` | 1562 | 100% | 0 | fiscal_year: 26 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 13 duplicate row instance(s); e.g. x2: ['2', '2018-08-08', 'Local Initiatives - Fiscal 2019', '2019']...; column_bleed: 7 suspected surname-in-organization residual(s); e.g. line 204: 'Ayala Young Audiences New York, Inc.' |
| `fy19/transparency-resolutions/reso03_transparency_designations.csv` | 1064 | 100% | 0 | fiscal_year: 35 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 9 duplicate row instance(s); e.g. x2: ['3', '2018-09-26', 'Cultural Immigrant Initiative - Fiscal 2019', '2019']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 746: 'Ayala New York City Housing Authority' |
| `fy19/transparency-resolutions/reso04_transparency_designations.csv` | 591 | 100% | 0 | fiscal_year: 94 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 11 duplicate row instance(s); e.g. x2: ['4', '2018-10-31', 'Aging Discretionary - Fiscal 2019', '2019']...; column_bleed: 3 suspected surname-in-program residual(s); e.g. line 212: 'Hudson High School Of Learning Technologies' |
| `fy19/transparency-resolutions/reso05_transparency_designations.csv` | 913 | 100% | 0 | fiscal_year: 346 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 11 duplicate row instance(s); e.g. x2: ['5', '2018-12-11', 'Anti-Poverty Initiative - Fiscal 2019', '2019']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 203: 'Rivera Educational Alliance, Inc.' |
| `fy19/transparency-resolutions/reso06_transparency_designations.csv` | 89 | 100% | 0 | fiscal_year: 22 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['6', '2018-12-20', 'Local Initiatives - Fiscal 2017', '2017']... |
| `fy19/transparency-resolutions/reso07_transparency_designations.csv` | 337 | 100% | 0 | fiscal_year: 20 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 80: 'Powers Midtown Management Group, Inc.' |
| `fy19/transparency-resolutions/reso08_transparency_designations.csv` | 349 | 100% | 0 | fiscal_year: 68 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 3 duplicate row instance(s); e.g. x2: ['8', '2019-02-28', 'Boroughwide Needs Initiative - Fiscal 2018', '2018']... |
| `fy19/transparency-resolutions/reso09_transparency_designations.csv` | 285 | 100% | 0 | duplicate: 3 duplicate row instance(s); e.g. x2: ['9', '2019-03-28', 'Local Initiatives - Fiscal 2019', '2019']...; column_bleed: 3 suspected surname-in-program residual(s); e.g. line 18: 'Louis Armstrong World Festival' |
| `fy19/transparency-resolutions/reso10_transparency_designations.csv` | 131 | 100% | 0 | fiscal_year: 20 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['10', '2019-04-18', 'Local Initiatives - Fiscal 2019', '2019']... |
| `fy19/transparency-resolutions/reso11_transparency_designations.csv` | 67 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy20/capital/fy20_capital_projects.csv` | 1663 | — | 0 | — |
| `fy20/schedule_c/fy20_appendix_a_aging.csv` | 0 | 0% | 0 | — |
| `fy20/schedule_c/fy20_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy20/schedule_c/fy20_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy20/schedule_c/fy20_schedule_c_awards.csv` | 2841 | 100% | 0 | duplicate: 29 duplicate row instance(s); e.g. x2: ['Community Development', 'Digital Inclusion and Literacy Initiative', 'member_item', 'Ayala']...; column_bleed: 12 suspected surname-in-organization residual(s); e.g. line 107: 'Hudson Guild' |
| `fy20/schedule_c/fy20_schedule_c_initiatives.csv` | 137 | — | 0 | — |
| `fy20/transparency-resolutions/fy20_transparency_all.csv` | 5319 | 100% | 0 | fiscal_year: 207 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 41 duplicate row instance(s); e.g. x2: ['1', '2019-07-23', 'Local Initiatives - Fiscal 2020', '2020']...; column_bleed: 11 suspected surname-in-program residual(s); e.g. line 57: 'Louis Armstrong Tenant Association' |
| `fy20/transparency-resolutions/reso01_transparency_designations.csv` | 1361 | 100% | 0 | fiscal_year: 28 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 8 duplicate row instance(s); e.g. x2: ['1', '2019-07-23', 'Local Initiatives - Fiscal 2020', '2020']...; column_bleed: 1 suspected surname-in-program residual(s); e.g. line 57: 'Louis Armstrong Tenant Association' |
| `fy20/transparency-resolutions/reso02_transparency_designations.csv` | 1268 | 100% | 0 | fiscal_year: 13 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 13 duplicate row instance(s); e.g. x2: ['2', '2019-08-14', 'Cultural After-School Adventure (CASA) - Fiscal 2020', '2020']...; column_bleed: 4 suspected surname-in-program residual(s); e.g. line 34: 'Hudson River Park Estuary Lab Levine (Environmental Educatio' |
| `fy20/transparency-resolutions/reso03_transparency_designations.csv` | 1062 | 100% | 0 | fiscal_year: 28 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 7 duplicate row instance(s); e.g. x2: ['3', '2019-09-25', 'Local Initiatives - Fiscal 2020', '2020']... |
| `fy20/transparency-resolutions/reso04_transparency_designations.csv` | 539 | 100% | 0 | fiscal_year: 76 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['4', '2019-11-14', 'Anti-Poverty Initiative - Fiscal 2020', '2020']...; column_bleed: 2 suspected surname-in-program residual(s); e.g. line 78: 'Louis Armstrong Tenant Association' |
| `fy20/transparency-resolutions/reso05_transparency_designations.csv` | 557 | 100% | 0 | fiscal_year: 46 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 5 duplicate row instance(s); e.g. x2: ['5', '2019-12-19', 'Cultural After-School Adventure (CASA) - Fiscal 2020', '2020']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 115: 'Louis Armstrong House Museum' |
| `fy20/transparency-resolutions/reso06_transparency_designations.csv` | 176 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-program residual(s); e.g. line 10: 'Williams Plaza Tenant Association' |
| `fy20/transparency-resolutions/reso07_transparency_designations.csv` | 233 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['7', '2020-02-27', 'Digital Inclusion and Literacy Initiative - Fiscal 2020', '2020']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 16: 'Hudson River Park Trust' |
| `fy20/transparency-resolutions/reso08_transparency_designations.csv` | 123 | 100% | 0 | — |
| `fy21/schedule_c/fy21_appendix_a_aging.csv` | 514 | 100% | 0 | — |
| `fy21/schedule_c/fy21_appendix_b_local.csv` | 2902 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Richards', 'Queens Borough Public Library', 'Arverne Library', '136400434']...; column_bleed: 46 suspected surname-in-organization residual(s); e.g. line 24: 'Adams Street Foundation, Inc.' |
| `fy21/schedule_c/fy21_appendix_c_youth.csv` | 894 | 100% | 0 | column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 416: 'Hudson Guild' |
| `fy21/schedule_c/fy21_schedule_c_awards.csv` | 1810 | 100% | 0 | duplicate: 4 duplicate row instance(s); e.g. x2: ['Boroughwide Needs', '', 'member_item', 'Brooklyn']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 1031: 'Hudson Guild' |
| `fy21/schedule_c/fy21_schedule_c_initiatives.csv` | 124 | — | 0 | — |
| `fy21/terms/fy21_terms_and_conditions.csv` | 46 | — | 0 | — |
| `fy21/transparency-resolutions/fy21_transparency_all.csv` | 4463 | 100% | 0 | fiscal_year: 126 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 18 duplicate row instance(s); e.g. x2: ['1', '2020-08-27', 'Local Initiatives - Fiscal 2021', '2021']...; column_bleed: 9 suspected surname-in-organization residual(s); e.g. line 628: 'Louis Armstrong House Museum' |
| `fy21/transparency-resolutions/reso01_transparency_designations.csv` | 2414 | 100% | 0 | fiscal_year: 58 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['1', '2020-08-27', 'Local Initiatives - Fiscal 2021', '2021']...; column_bleed: 5 suspected surname-in-organization residual(s); e.g. line 628: 'Louis Armstrong House Museum' |
| `fy21/transparency-resolutions/reso02_transparency_designations.csv` | 705 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['2', '2020-09-23', 'Cultural After-School Adventure (CASA) - Fiscal 2021', '2021']... |
| `fy21/transparency-resolutions/reso03_transparency_designations.csv` | 249 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['3', '2020-10-29', 'Cultural After-School Adventure (CASA) - Fiscal 2021', '2021']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 76: 'Louis Midtown Management Group, Inc.' |
| `fy21/transparency-resolutions/reso04_transparency_designations.csv` | 184 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy21/transparency-resolutions/reso05_transparency_designations.csv` | 226 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x3: ['5', '2020-12-17', 'Local Initiatives - Fiscal 2021', '2021']... |
| `fy21/transparency-resolutions/reso06_transparency_designations.csv` | 218 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['6', '2021-02-25', 'Youth Discretionary - Fiscal 2021', '2021']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 113: 'Holden Colonial Farmhouse Restoration Society of Bellerose, ' |
| `fy21/transparency-resolutions/reso07_transparency_designations.csv` | 312 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['7', '2021-04-22', 'Aging Discretionary - Fiscal 2021', '2021']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 114: 'Gennaro Department of Parks and Recreation' |
| `fy21/transparency-resolutions/reso08_transparency_designations.csv` | 155 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['8', '2021-06-30', 'Local Initiatives - Fiscal 2021', '2021']... |
| `fy22/capital/fy22_capital_projects.csv` | 1641 | — | 0 | amount: line 1635: fy1 negative -72,000 (capital expected >= 0) |
| `fy22/schedule_c/fy22_appendix_a_aging.csv` | 510 | 100% | 0 | — |
| `fy22/schedule_c/fy22_appendix_b_local.csv` | 2790 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Eugene', 'Prospect Lefferts Gardens Neighborhood Association, Inc.', '', '237064386']...; column_bleed: 55 suspected surname-in-organization residual(s); e.g. line 12: 'Ayala 2020 Vision for Schools, Inc.' |
| `fy22/schedule_c/fy22_appendix_c_youth.csv` | 882 | 100% | 0 | column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 411: 'Hudson Guild' |
| `fy22/schedule_c/fy22_schedule_c_awards.csv` | 1492 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Speaker’s Initiative to Address Citywide Needs', 'Speaker’s Initiative to Address Citywide Needs', 'initiative_provider', '']...; column_bleed: 5 suspected surname-in-organization residual(s); e.g. line 409: 'Dinowitz, Riley New York Botanical Garden' |
| `fy22/schedule_c/fy22_schedule_c_initiatives.csv` | 138 | — | 0 | — |
| `fy22/terms/fy22_terms_and_conditions.csv` | 50 | — | 0 | — |
| `fy22/transparency-resolutions/fy22_transparency_all.csv` | 7768 | 100% | 0 | fiscal_year: 134 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 40 duplicate row instance(s); e.g. x3: ['1', '2021-07-29', 'Local Initiatives - Fiscal 2022', '2022']...; column_bleed: 18 suspected surname-in-organization residual(s); e.g. line 168: 'Holden Outstanding Renewal Enterprises, Inc.' |
| `fy22/transparency-resolutions/reso01_transparency_designations.csv` | 1432 | 100% | 0 | fiscal_year: 33 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 9 duplicate row instance(s); e.g. x3: ['1', '2021-07-29', 'Local Initiatives - Fiscal 2022', '2022']...; column_bleed: 8 suspected surname-in-organization residual(s); e.g. line 168: 'Holden Outstanding Renewal Enterprises, Inc.' |
| `fy22/transparency-resolutions/reso02_transparency_designations.csv` | 2147 | 100% | 0 | fiscal_year: 24 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 14 duplicate row instance(s); e.g. x2: ['2', '2021-08-26', 'Local Initiatives - Fiscal 2022', '2022']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 746: 'Louis Armstrong House Museum' |
| `fy22/transparency-resolutions/reso03_transparency_designations.csv` | 1464 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['3', '2021-09-23', 'Viral Hepatitis Prevention- Fiscal 2022', '2022']...; column_bleed: 4 suspected surname-in-organization residual(s); e.g. line 649: 'Hudson River Community Sailing, Inc.' |
| `fy22/transparency-resolutions/reso04_transparency_designations.csv` | 512 | 100% | 0 | fiscal_year: 5 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2021-10-07', 'Cultural After-School Adventure (CASA) - Fiscal 2022', '2022']... |
| `fy22/transparency-resolutions/reso05_transparency_designations.csv` | 335 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['5', '2021-10-21', 'Local Initiatives - Fiscal 2022', '2022']... |
| `fy22/transparency-resolutions/reso06_transparency_designations.csv` | 280 | 100% | 0 | — |
| `fy22/transparency-resolutions/reso07_transparency_designations.csv` | 264 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy22/transparency-resolutions/reso08_transparency_designations.csv` | 268 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['8', '2021-12-09', 'Aging Discretionary - Fiscal 2022', '2022']... |
| `fy22/transparency-resolutions/reso09_transparency_designations.csv` | 301 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['9', '2021-12-15', 'Art a Catalyst for Change - Fiscal 2022', '2022']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 144: 'Joseph P. Addabbo Family Health Center, Inc.' |
| `fy22/transparency-resolutions/reso10_transparency_designations.csv` | 383 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 7 duplicate row instance(s); e.g. x2: ['10', '2022-03-10', 'A Greener NYC - Fiscal 2022', '2022']... |
| `fy22/transparency-resolutions/reso11_transparency_designations.csv` | 156 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 71: 'Louis Armstrong House Museum' |
| `fy22/transparency-resolutions/reso12_transparency_designations.csv` | 126 | 100% | 0 | fiscal_year: 14 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy22/transparency-resolutions/reso13_transparency_designations.csv` | 66 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy22/transparency-resolutions/reso14_transparency_designations.csv` | 34 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['14', '2022-06-13', 'SU-CASA - Fiscal 2022', '2022']... |
| `fy23/capital/fy23_capital_projects.csv` | 1547 | — | 0 | — |
| `fy23/schedule_c/fy23_appendix_a_aging.csv` | 489 | 100% | 0 | — |
| `fy23/schedule_c/fy23_appendix_b_local.csv` | 2726 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Brooks-Powers', 'Queens Borough Public Library', 'Laurelton Library', '136400434']...; column_bleed: 118 suspected surname-in-organization residual(s); e.g. line 29: 'Krishnan, Won Adhikaar for Human Rights and Social Justice' |
| `fy23/schedule_c/fy23_appendix_c_youth.csv` | 841 | 100% | 0 | column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 410: 'Hudson Guild' |
| `fy23/schedule_c/fy23_schedule_c_awards.csv` | 1848 | 100% | 0 | duplicate: 6 duplicate row instance(s); e.g. x3: ['BOROUGHWIDE NEEDS', '', 'member_item', 'Manhattan']...; column_bleed: 7 suspected surname-in-organization residual(s); e.g. line 1394: 'Marte, Schulman Association of Community Employment Programs' |
| `fy23/schedule_c/fy23_schedule_c_initiatives.csv` | 143 | — | 0 | — |
| `fy23/terms/fy23_terms_and_conditions.csv` | 60 | — | 0 | — |
| `fy23/transparency-resolutions/fy23_transparency_all.csv` | 8354 | 100% | 0 | amount: line 6896: designate amount 0 (expected > 0); amount: line 6897: designate amount 0 (expected > 0); fiscal_year: 544 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 11 row(s) with empty fiscal_year; duplicate: 43 duplicate row instance(s); e.g. x2: ['1', '2022-07-14', 'Youth Discretionary - Fiscal 2023', '2023']...; column_bleed: 12 suspected surname-in-program residual(s); e.g. line 407: 'Hudson River Park Project' |
| `fy23/transparency-resolutions/reso01_transparency_designations.csv` | 1759 | 100% | 0 | fiscal_year: 130 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 2 row(s) with empty fiscal_year; duplicate: 7 duplicate row instance(s); e.g. x2: ['1', '2022-07-14', 'Youth Discretionary - Fiscal 2023', '2023']...; column_bleed: 2 suspected surname-in-program residual(s); e.g. line 407: 'Hudson River Park Project' |
| `fy23/transparency-resolutions/reso02_transparency_designations.csv` | 1736 | 100% | 0 | fiscal_year: 35 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['2', '2022-08-11', 'Youth Discretionary - Fiscal 2023', '2023']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 963: 'Hudson Guild' |
| `fy23/transparency-resolutions/reso03_transparency_designations.csv` | 1562 | 100% | 0 | fiscal_year: 51 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 15 duplicate row instance(s); e.g. x2: ['3', '2022-09-29', 'Local Initiatives - Fiscal 2023', '2023']...; column_bleed: 4 suspected surname-in-organization residual(s); e.g. line 177: 'Hudson River Community Sailing, Inc.' |
| `fy23/transparency-resolutions/reso04_transparency_designations.csv` | 807 | 100% | 0 | fiscal_year: 83 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2022-10-27', 'Anti-Poverty Initiative - Fiscal 2023', '2023']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 182: 'Louis Armstrong House Museum' |
| `fy23/transparency-resolutions/reso05_transparency_designations.csv` | 423 | 100% | 0 | fiscal_year: 78 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['5', '2022-11-22', 'Art a Catalyst for Change - Fiscal 2023', '2023']... |
| `fy23/transparency-resolutions/reso06_transparency_designations.csv` | 432 | 100% | 0 | fiscal_year: 56 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['6', '2022-12-21', 'Community Safety and Victim Services Initiative - Fiscal 2023', '2023']... |
| `fy23/transparency-resolutions/reso07_transparency_designations.csv` | 201 | 100% | 0 | amount: line 177: designate amount 0 (expected > 0); amount: line 178: designate amount 0 (expected > 0); fiscal_year: 24 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy23/transparency-resolutions/reso08_transparency_designations.csv` | 556 | 100% | 0 | fiscal_year: 20 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['8', '2023-02-02', 'Local Initiatives - Fiscal 2023', '2023']... |
| `fy23/transparency-resolutions/reso09_transparency_designations.csv` | 144 | 100% | 0 | fiscal_year: 16 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 9 row(s) with empty fiscal_year |
| `fy23/transparency-resolutions/reso10_transparency_designations.csv` | 254 | 100% | 0 | fiscal_year: 16 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['10', '2023-03-02', 'Local Initiatives - Fiscal 2023', '2023']... |
| `fy23/transparency-resolutions/reso11_transparency_designations.csv` | 137 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy23/transparency-resolutions/reso12_transparency_designations.csv` | 208 | 100% | 0 | fiscal_year: 21 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 54: 'Hudson Guild' |
| `fy23/transparency-resolutions/reso13_transparency_designations.csv` | 25 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy23/transparency-resolutions/reso14_transparency_designations.csv` | 110 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy24/capital/fy24_capital_projects.csv` | 1364 | — | 0 | amount: line 1287: fy1 negative -40,000 (capital expected >= 0) |
| `fy24/schedule_c/fy24_appendix_a_aging.csv` | 477 | 100% | 0 | — |
| `fy24/schedule_c/fy24_appendix_b_local.csv` | 2616 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Restler', 'Department of Education', 'Urban Assembly Institute of Math and Science for Young Women (K527)', '136400434']...; column_bleed: 89 suspected surname-in-organization residual(s); e.g. line 101: 'Brewer Aperture Foundation, Inc.' |
| `fy24/schedule_c/fy24_appendix_c_youth.csv` | 818 | 100% | 0 | column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 408: 'Hudson Guild' |
| `fy24/schedule_c/fy24_schedule_c_awards.csv` | 5368 | 100% | 0 | duplicate: 28 duplicate row instance(s); e.g. x2: ['CULTURAL ORGANIZATIONS', 'Cultural After-School Adventure (CASA)', 'member_item', 'Williams']...; column_bleed: 22 suspected surname-in-organization residual(s); e.g. line 394: 'Hudson Guild' |
| `fy24/schedule_c/fy24_schedule_c_initiatives.csv` | 146 | — | 0 | — |
| `fy24/terms/fy24_terms_and_conditions.csv` | 59 | — | 0 | — |
| `fy24/transparency-resolutions/fy24_transparency_all.csv` | 3294 | 100% | 0 | fiscal_year: 215 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 28 duplicate row instance(s); e.g. x2: ['1', '2023-08-03', 'Community Safety and Victim Services Initiative - Fiscal 2024', '2024']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 212: 'Rivera Outstanding Renewal Enterprises, Inc.' |
| `fy24/transparency-resolutions/reso01_transparency_designations.csv` | 790 | 100% | 0 | fiscal_year: 16 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 5 duplicate row instance(s); e.g. x2: ['1', '2023-08-03', 'Community Safety and Victim Services Initiative - Fiscal 2024', '2024']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 212: 'Rivera Outstanding Renewal Enterprises, Inc.' |
| `fy24/transparency-resolutions/reso02_transparency_designations.csv` | 953 | 100% | 0 | fiscal_year: 53 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['2', '2023-09-14', 'Food Pantries - Fiscal 2024', '2024']... |
| `fy24/transparency-resolutions/reso03_transparency_designations.csv` | 327 | 100% | 0 | fiscal_year: 30 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy24/transparency-resolutions/reso04_transparency_designations.csv` | 280 | 100% | 0 | fiscal_year: 13 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 11 duplicate row instance(s); e.g. x2: ['4', '2023-11-02', 'Cultural After-School Adventure (CASA) - Fiscal 2024', '2024']... |
| `fy24/transparency-resolutions/reso05_transparency_designations.csv` | 212 | 100% | 0 | fiscal_year: 20 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 97: 'Hanks Waterfront Alliance, Inc.' |
| `fy24/transparency-resolutions/reso06_transparency_designations.csv` | 126 | 100% | 0 | fiscal_year: 15 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['6', '2024-02-08', 'Local Initiatives - Fiscal 2024', '2024']... |
| `fy24/transparency-resolutions/reso07_transparency_designations.csv` | 369 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['7', '2024-04-11', 'Local Initiatives - Fiscal 2024', '2024']... |
| `fy24/transparency-resolutions/reso08_transparency_designations.csv` | 161 | 100% | 0 | fiscal_year: 42 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['8', '2024-05-23', 'Domestic Violence and Empowerment (DoVE) Initiative - Fiscal 2023', '2023']... |
| `fy24/transparency-resolutions/reso09_transparency_designations.csv` | 76 | 100% | 0 | fiscal_year: 14 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy25/capital/fy25_capital_projects.csv` | 1508 | — | 0 | — |
| `fy25/schedule_c/fy25_appendix_a_aging.csv` | 470 | 100% | 0 | — |
| `fy25/schedule_c/fy25_appendix_b_local.csv` | 2616 | 100% | 0 | column_bleed: 85 suspected surname-in-organization residual(s); e.g. line 163: 'Holden Association of Community Employment Programs for the ' |
| `fy25/schedule_c/fy25_appendix_c_youth.csv` | 834 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Salaam', 'Figure Skating in Harlem, Inc.', '', '133945168']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 407: 'Hudson Guild' |
| `fy25/schedule_c/fy25_schedule_c_awards.csv` | 5646 | 100% | 0 | duplicate: 18 duplicate row instance(s); e.g. x3: ['CULTURAL ORGANIZATION', 'Cultural After-School Adventure (CASA)', 'member_item', 'Williams']...; column_bleed: 14 suspected surname-in-program residual(s); e.g. line 212: 'Louis Pink Houses TA Programming' |
| `fy25/schedule_c/fy25_schedule_c_initiatives.csv` | 158 | — | 0 | — |
| `fy25/terms/fy25_terms_and_conditions.csv` | 65 | — | 0 | — |
| `fy26/capital/fy26_capital_projects.csv` | 1456 | — | 0 | amount: line 1336: fy1 negative -183,000 (capital expected >= 0) |
| `fy26/schedule_c/fy26_appendix_a_aging.csv` | 473 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Salaam', 'Catholic Managed Long Term Care, Inc.', '', '208180809']... |
| `fy26/schedule_c/fy26_appendix_b_local.csv` | 2618 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Salaam', 'New York Interfaith Commission for Housing Equality, Inc.', '', '993367298']...; column_bleed: 139 suspected surname-in-organization residual(s); e.g. line 26: 'Rivera Ackerman Institute for the Family' |
| `fy26/schedule_c/fy26_appendix_c_youth.csv` | 823 | 100% | 0 | column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 415: 'Hudson Guild' |
| `fy26/schedule_c/fy26_schedule_c_awards.csv` | 5838 | 100% | 0 | duplicate: 15 duplicate row instance(s); e.g. x2: ['CULTURAL ORGANIZATIONS', 'Cultural After-School Adventure (CASA)', 'member_item', 'Williams']...; column_bleed: 16 suspected surname-in-program residual(s); e.g. line 200: 'Louis Armstrong Houses TA Association' |
| `fy26/schedule_c/fy26_schedule_c_initiatives.csv` | 157 | — | 0 | — |
| `fy26/terms/fy26_terms_and_conditions.csv` | 68 | — | 0 | — |
| `fy26/transparency-resolutions/fy26_transparency_all.csv` | 4755 | 100% | 0 | fiscal_year: 326 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1 row(s) with empty fiscal_year; duplicate: 36 duplicate row instance(s); e.g. x2: ['1', '2025-08-14', 'Local Initiatives - Fiscal 2026', '2026']...; column_bleed: 9 suspected surname-in-organization residual(s); e.g. line 533: 'Brannan Edith and Carl Marks Jewish Community House of Benso' |
| `fy26/transparency-resolutions/reso01_transparency_designations.csv` | 985 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1 row(s) with empty fiscal_year; duplicate: 10 duplicate row instance(s); e.g. x2: ['1', '2025-08-14', 'Local Initiatives - Fiscal 2026', '2026']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 533: 'Brannan Edith and Carl Marks Jewish Community House of Benso' |
| `fy26/transparency-resolutions/reso02_transparency_designations.csv` | 1638 | 100% | 0 | fiscal_year: 31 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 18 duplicate row instance(s); e.g. x2: ['2', '2025-09-25', 'Local Initiatives - Fiscal 2026', '2026']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 453: 'Mealy Department of Parks and Recreation' |
| `fy26/transparency-resolutions/reso03_transparency_designations.csv` | 832 | 100% | 0 | fiscal_year: 168 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['3', '2025-10-29', 'Local Initiatives - Fiscal 2025', '2025']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 461: 'Hudson Square District Management Association, Inc.' |
| `fy26/transparency-resolutions/reso04_transparency_designations.csv` | 487 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 3 duplicate row instance(s); e.g. x2: ['4', '2025-11-25', 'Support Our Older Adults - Fiscal 2026', '2026']... |
| `fy26/transparency-resolutions/reso05_transparency_designations.csv` | 162 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 133: 'Hudson Square District Management Association, Inc.' |
| `fy26/transparency-resolutions/reso06_transparency_designations.csv` | 190 | 100% | 0 | fiscal_year: 14 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['6', '2026-02-12', 'Local Initiatives - Fiscal 2026', '2026']... |
| `fy26/transparency-resolutions/reso07_transparency_designations.csv` | 78 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy26/transparency-resolutions/reso08_transparency_designations.csv` | 91 | 100% | 0 | fiscal_year: 16 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy26/transparency-resolutions/reso09_transparency_designations.csv` | 141 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy26/transparency-resolutions/reso10_transparency_designations.csv` | 151 | 100% | 0 | fiscal_year: 27 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['10', '2026-06-30', 'Local Initiatives - Fiscal 2023', '2023']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 87: "Hudson Yards Hell's Kitchen Business Improvement District, I" |
| `fy27/capital/fy27_capital_projects.csv` | 1388 | — | 0 | — |
| `fy27/schedule_c/fy27_appendix_a_aging.csv` | 467 | 100% | 0 | — |
| `fy27/schedule_c/fy27_appendix_b_local.csv` | 2558 | 100% | 0 | duplicate: 2 duplicate row instance(s); e.g. x2: ['Hanks', 'Grace Foundation of New York', 'Council District 49', '134131863']...; column_bleed: 85 suspected surname-in-organization residual(s); e.g. line 22: 'Salaam Abyssinian Baptist Church' |
| `fy27/schedule_c/fy27_appendix_c_youth.csv` | 835 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Paladino', 'New York Sun Works, Inc.', 'Hydroponic Classrooms - Public School 094Q David D. Porter (26Q094)', '200670312']...; column_bleed: 3 suspected surname-in-program residual(s); e.g. line 361: 'Joseph Miccio Community Center Cornerstone Programs - Counci' |
| `fy27/schedule_c/fy27_schedule_c_awards.csv` | 6118 | 100% | 0 | duplicate: 33 duplicate row instance(s); e.g. x2: ['Cultural Organizations', 'Cultural After-School Adventure (CASA)', 'member_item', 'Abreu']...; column_bleed: 16 suspected surname-in-program residual(s); e.g. line 203: 'Louis Armstrong Houses TA Association' |
| `fy27/schedule_c/fy27_schedule_c_initiatives.csv` | 170 | — | 0 | — |
| `fy27/terms/fy27_terms_and_conditions.csv` | 75 | — | 0 | — |

### Notes on the soft heuristics

- **Column-bleed** is a *suspected*-residual heuristic: it flags an organization/program field whose leading token is one of 47 surnames drawn from the transparency `council_member` column (boroughs/agencies excluded). Because that source column itself carries some bleed, the set is imperfect and the check has known FALSE POSITIVES — organizations whose real name simply begins with such a token (e.g. `Hudson Guild`, `Joseph P. Addabbo Family Health Center`). Genuine residuals look like `Brewer ParentsofPublicSchool9,Inc.` (a member surname prepended to a glued-word org). Treat this column as a review queue, not a defect list; the repo has no authoritative council-member roster to validate against.
- **Capital negative amounts**: the §254 books are *Changes to the Capital Budget*, so a negative FY amount (a de-appropriation/reduction) can be legitimate. Flagged for review, not treated as an error.
- **Transparency prior-year rows**: a resolution routinely amends *earlier* years' designations, so `fiscal_year` values below the folder year are expected and counted, not flagged.

