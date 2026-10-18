---
title: "NYC Open Data inventory: Council budget and capital datasets (#84)"
created: 2026-10-14
type: research-note
status: draft
tags: [nyc-budget, open-data, capital, council, research]
issue: "BetaNYC/New-York-City-Budget#84 (epic #89)"
---

# NYC Open Data inventory: Council budget and capital datasets (#84)

**Report generated:** 2026-10-14
**Data current as of:** 2026-10-14 (NYC Open Data catalog and dataset metadata read live this morning)
**Author:** research-intelligence, for epic #89
**Companion notes:** [capital stage map (#87, #88)](2026-10-14-capital-stage-map.md),
[follow-up questions](2026-10-14-follow-up-questions-84-87-88.md)

## Summary

- **The Council publishes its capital designations on Open Data.** `t474-a92g` "City Council
  Capital Budget" (City Council, NYCC) has 11,503 rows for reports FY2019 through FY2026, one
  row per Council capital award. It was last updated 2025-12-17, so it does not have FY2027 yet.
  Its FY2026 rows carry the same IDs and amounts as the Council's RnD workbook. Its FY2025 total
  is $775,000,000 on 1,325 rows, against the repo's PDF-derived $775M on 1,327 projects. This
  dataset was not in the July crosswalk and fills our FY2019 and FY2021 capital gaps.
- **OMB's adopted Capital Budget (`46m8-77gv`) reconciles to the Council file.** At budget-line
  grain, 146 of the Council's 153 FY2027 budget lines match OMB's July 2026 adopted amounts to
  the dollar, in both FY2027 and FY2028. Details in the stage map.
- **OMB's Capital Commitment Plan (`2cmn-uidm`) is current and has history.** 31 releases,
  April 2016 through 2026-09-28, budget line by City/Non-City, in thousands of dollars.
- **DCP's Capital Projects Database (CPDB) is the only Open Data source at FMS-project grain
  that carries adopted, committed, spent, and a Checkbook-derived spent total.** But Open Data
  holds one snapshot only (`ccpversion = fisa_2026`), with no history.
- **The Mayor's Office of Operations Capital Projects Dashboard (`fb86-vt7u`)** adds phase and
  schedule by FMS ID, ten reporting periods (May 2023 to May 2026), and about 1,400 rows per
  period on Council budget lines.
- **Most other candidates are frozen or aggregate.** OMB's project-level Capital Project Detail
  stopped in October 2023. IBO's 20 datasets are aggregate and mostly frozen in 2021. The
  Council's participatory budgeting datasets stopped in 2017 and 2018.

## Method

- Tool: the `socrata` MCP against `data.cityofnewyork.us`, one request at a time, at least
  2 seconds apart. 25 requests in total: 3 searches, 5 catalog queries, 1 `fetch`, 1 metadata
  read, and 15 small SoQL queries (aggregates or 40 rows or fewer). No bulk pulls. No 403, 429
  or other errors.
- One pair of calls went out in a single batch by mistake. Per the saved results, the two ran
  about 4 seconds apart, so the rate limit held. Every other call ran alone.
- Raw search and catalog responses are cached in `../nycb-cache/` (outside this repo):
  `socrata-search-*.json`, `socrata-catalog-*.json`, `socrata-fetch-t474-a92g.summary.json`,
  `socrata-meta-46m8-77gv.summary.json`.
- "Last updated" below is the catalog's `data_updated_at` (rows), not the metadata date.
  Row counts come from SoQL `count(*)`, the dataset's own `cachedContents`, or the catalog,
  as marked. "Not checked" means I did not spend a request on it.
- **License:** none of the metadata I read carries a dataset-specific license. The standard
  NYC Open Data Terms of Use apply. See follow-up question 84-10.

## Inventory

Fit for nyc-budget-mcp 2.0: **build** (load it), **hold** (useful, but needs a decision or a
test first), **skip** (out of scope or no join).

### A. Council-published

| ID | Title | Publisher | Years | Rows | Cols | Last updated | Update frequency | Grain | Join keys | Fit |
|---|---|---|---|---|---|---|---|---|---|---|
| `t474-a92g` | City Council Capital Budget | City Council (NYCC); attribution link `rnd.council.nyc.gov/capital_funding/` | Reports FY2019–FY2026; out-year rows FY27 (4), FY28 (1), FY29 (1) | 11,503 (cached contents) | 10 | 2025-12-17 | Annually, manual ("Date Made Public" 2/5/2025) | One Council capital award per fiscal year; out-year amounts are separate rows | `id` (unique within a report year only), `budget_line`, `council_district`, `sponsor` | **Build.** Fills FY2019 and FY2021 and gives a second witness for FY2020, FY2022–FY2026. 7 malformed rows to repair (shifted fields, Excel `ERROR: #NAME?`). FY2027 comes from the RnD workbook until the Council updates this. |
| `4d7f-74pe` | City Council Discretionary Funding | Catalog attribution is blank; #89 treats it as Council-published | FY2009–FY2021 | 97,002 (per #89) | 27 | 2021-04-20 | Stopped | One expense award application | `mocs_id`, `ein`, `council_member`, `source`, plus geocodes (BBL, BIN, council district) | **Build FY2009–FY2012; hold the rest** until the #85 diff is done. Another agent is pulling it today. |
| `qm5f-frjb` | Participatory Budgeting Project Tracker | City Council (NYCC) | Vote years from 2012 (preview); end year not checked | Not checked | 23 | 2018-03-15 | Stopped | Winning PB project or subproject | `district`, `agency`, `fiscal_year`, BBL/BIN. No project ID, no budget line | **Hold.** PB money is Council capital, but there is no key to the capital files. |
| `wwhr-5ven` | Participatory Budgeting Projects | Blank attribution; description cites PBNYC | Vote year 2014 in preview; range not checked | Not checked | 20 | 2017-05-12 | Stopped | Ballot item, winners and losers (`winner` 0/1) | `council_district`, `project_number`, BBL/BIN | **Skip** for 2.0. Ballot data, not budget data. |
| `wa6b-r9jh` | Participatory Budgeting Survey Data | City Council (NYCC) | Survey years to 2019 | Not checked | 15 | 2019-07-23 | Stopped | Survey response | none | **Skip.** |
| `uvw5-9znb` | City Council Members (1999 to Present) | City Council (NYCC) | 1999– | Not checked | 6 | 2026-04-10 | Not checked | Member term | Name, district (columns not read) | **Hold** as a lookup to turn `SPONSOR` surnames into districts and people. The repo already resolves members to Legistar person IDs, so this may be redundant. |

### B. MOCS (contract clearance for discretionary awards)

| ID | Title | Publisher | Years | Rows | Cols | Last updated | Update frequency | Grain | Join keys | Fit |
|---|---|---|---|---|---|---|---|---|---|---|
| `ujre-m2tj` | Discretionary Award Tracker | MOCS | FY2019–FY2021 (described as "past three fiscal years", one 2021 snapshot) | Not checked | 7 | 2021-06-30 | One-time | Expense award with clearance status | `mocs_award_number` (e.g. `FY21 09296`), `vendor_name`, `agency` | **Hold.** The only public bridge from a MOCS award number to a clearance status, but frozen. |
| `ubuy-v2nw` | Discretionary Contract Awards 2017-2018 | Not checked | FY2017–FY2018 | Not checked | 3 | Not checked (rows created 2019-10-22) | One-time | Grant name and amount | none | **Skip.** No organization, member or ID. |

### C. OMB capital

| ID | Title | Publisher | Years | Rows | Cols | Last updated | Update frequency | Grain | Join keys | Fit |
|---|---|---|---|---|---|---|---|---|---|---|
| `46m8-77gv` | Capital Budget | OMB | Releases 2018-02-01 → 2026-07-13; first fiscal year FY2019–FY2027 | 16,491 (metadata) | 11 | 2026-07-13 | 3 times a year (Preliminary, Executive, Adopted) | Release × budget line × funding source (C, E, F, S, P), whole dollars, 4 years | `budline` with a space (`PV DN132`; some with two, `P  1018`), `pub_date` | **Build.** Stage 2 (adopted appropriation). Council `D`/`DN` lines reconcile to the Council file. |
| `2cmn-uidm` | Capital Commitment Plan | OMB | Releases 2016-04-26 → 2026-09-28 (31 releases; first year FY2016–FY2027) | 60,739 (query) | 13 | 2026-09-28 | 3 times a year | Release × budget line × City/Non-City, **thousands** of dollars, 4–5 years | `budline` without a space (`PVDN132`), `pub_date` | **Build.** Stage 3 at budget-line grain, with ten years of release history (shows slippage). |
| `wa2y-rh4b` | Capital Project Detail Data - Dollars | OMB | Releases 2019-04-25 → 2023-10-26 (14) | 72,437 (query) | 30 | 2023-10-27 | Stopped | Release × project | `project_id`, `managing_agcy_cd`, `budget_line` (`AG-0001`) | **Skip.** Stale, and a search for two Council `DN` lines returned nothing. |
| `s7yh-frbm` | Capital Project Detail Data - Milestones | OMB | Same as above | Not checked | 12 | 2023-10-27 | Stopped | Project milestone | `project_id` | **Skip.** |
| `8u85-k342` | Capital Commitment Actuals | Catalog attribution blank (OMB data) | From FY2002 | Not checked | 6 | 2025-12-04 | Annual | Agency summary, millions | `agy` name | **Skip** (context only). |
| `c99a-c5ux` | NYC Climate Budgeting Report: Climate Alignment … Capital | OMB | Published 2024–2026 | Not checked | 19 | 2026-08-11 | Annual | Capital project × plan | `project_id` in FMS form (`035 L21FREEZE`), `budget_line` | **Hold.** A project-level enrichment that shares the FMS project ID. |
| `b37a-3faw`, `4utb-pisg`, `4xfc-mzbg`, `exez-mxv4`, `wcpw-9chs`, `vck7-ujai` | Ten-Year Capital Strategy; Capital Plan Funding Source; Capital Cashflow; Cash Source and Use; State of Good Repair (two) | OMB | Various | Not checked | 5–17 | 2025-05 to 2026-09 | Various | Aggregate | none to the Council file | **Skip.** |

### D. DCP Capital Projects Database (CPDB)

| ID | Title | Publisher | Years | Rows | Cols | Last updated | Update frequency | Grain | Join keys | Fit |
|---|---|---|---|---|---|---|---|---|---|---|
| `fi59-268w` | CPDB - Projects | DCP | One version, `fisa_2026`; commitment dates 2018→2039 | 12,929 (query) | 51 | 2026-08-24 | Not stated in what I read | FMS project (`maprojid` = 3-digit managing agency + `projectid`) | `maprojid`, `magency`, `projectid`. **No budget line, no Council ID** | **Build, with a caveat.** Stages 3–5 for a project: planned, adopted, allocated, committed, spent, and `spent_total_checkbooknyc`. One snapshot only. |
| `djxg-kcfi` | CPDB - Commitments | DCP | One version, `fisa_2026`; planned commitment dates 2025-07-01 → 2039-06-01 | 41,277 (query) | 22 | 2026-08-24 | As above | Planned commitment | `maprojid`, `budgetline` with a hyphen (`AG-DN04L`) | **Build.** The only Open Data bridge from a budget line to an FMS project. |
| `h2ic-zdws`, `9jkp-n57r` (+ map views `ws6q-gv6r`, `c48v-p34c`) | CPDB - Projects (Points, Polygons) | DCP | `fisa_2026` | Not checked | 52 | 2026-08-24 | As above | FMS project with geometry | `maprojid` | **Hold.** Geography for a later map tool. |

### E. Mayor's Office of Operations (capital performance)

| ID | Title | Publisher | Years | Rows | Cols | Last updated | Update frequency | Grain | Join keys | Fit |
|---|---|---|---|---|---|---|---|---|---|---|
| `fb86-vt7u` | Capital Projects Dashboard - Citywide Budget and Schedule | OPS | Reporting periods 2023-05 → 2026-05 (10) | 56,525 (query) | 27 | 2026-07-15 | About 3 times a year | Project × reporting period ("only projects in the design phase or later"; it also lists Pre-Design rows) | `fms_id` (`P-301DUAN`), `pid`, `budget_line` (a list, `P -D018 , P -I001`), `community_board` | **Hold, leaning build.** About 1,400 rows a period sit on Council `D` lines. Phase and forecast completion answer "where is it now." The key needs normalizing before a test. |
| `gyhf-rsr3`, `95tx-snak`, `qj5n-h5qp` | Dashboard: Budget and Spend by FY; Schedule History; Budget Spend History | OPS | Same periods | Not checked | 8–10 | 2026-07-15 | As above | Project × period | `fms_id` (assumed, not read) | **Hold.** |
| `n7gv-k5yt` | Capital Projects | OPS | Not checked | Not checked | 16 | 2025-06-04 | Not checked | Not checked | Not checked | **Hold**, not examined. |

### F. IBO (re-verified against the July crosswalk)

The catalog query for IBO returned the same 20 datasets the 2026-07-08 crosswalk named. All are
citywide or agency aggregates, and most stopped updating in 2021. The one capital set is
`hukm-snmq` (Capital Expenditures Since 1985, FY1985–FY2020, 38 columns, last updated
2021-07-12, agency by purpose, wide by year). **Skip all 20 for 2.0**, for the reasons in the
crosswalk: no designation, project, or budget-line grain.

### G. Other capital money that is not the Council's

| ID | Title | Publisher | Last updated | Note | Fit |
|---|---|---|---|---|---|
| `n6ej-pebd` | Capital Awards | Brooklyn Borough President | 2021-06-29 | 5 columns | **Hold** (out of 2.0 scope) |
| `mdgu-ar69` | Bronx Borough President Capital Funding | Bronx BP | 2024-12-09 | 20 columns | **Hold** |
| `9umc-3b2y`, `6wee-b7wf`, `83z6-smyr`, `k84j-firu`, `66yh-nemi` | Capital Grant Awards 2014–2018 | Manhattan BP (some blank attribution) | 2017 | One dataset per year | **Skip** |
| `7hgn-sgmk` | DCLA Cultural Organizations Capital Funding | DCLA | 2026-04-28 | Columns split BP, Council and Mayoral funding by organization. Column names say "FY15" while the preview row says FY2022: check before use | **Hold** (a cross-check for Council cultural capital) |
| `2xh6-psuq`, `8586-3zfm`, `tsak-vtv3`, `6m3u-8rbh` | School Construction Authority capital datasets | SCA | 2026-08/10 | Possible route to the 708 Council school projects on `E D001` | **Hold**, not examined |

### H. OMB expense budget (context for the Schedule C side, not tested)

`mwzb-yiwb` Expense Budget (26 columns, agency × unit of appropriation × budget code × object
code, last updated 2026-07-08), `39g5-gbp3` Expense Budget Funding, `f9xn-fiww` Community Boards
Geographic Report, and `vn4m-mk4t` Register of Community Board Budget Requests (has a council
district column). None of their column lists shows a Council initiative or designation field.
**Hold.** I did not test whether Council discretionary money can be isolated in them.

### I. Not data

`mxwn-eh3b` "Checkbook NYC 2.0" is a 2013 link record (type `href`), not a dataset.

## What this means for nyc-budget-mcp 2.0

- **Build first:** `t474-a92g` (Council capital, FY2019–FY2026), `46m8-77gv` (adopted capital
  budget lines), `2cmn-uidm` (commitment plan lines, with release history), and the CPDB pair
  (`djxg-kcfi` and `fi59-268w`) for project status and Checkbook-derived spending.
- **The honest unit of capital tracking is the budget line, not the project.** The Council's
  project IDs do not appear in any OMB, DCP or OPS dataset I read. See the stage map.
- **Every build candidate is under the 100,000-row stop line, and none has been pulled yet.**
  Full pulls are listed as follow-up question 84-9 for approval.

## Sources

- NYC Open Data catalog: <https://data.cityofnewyork.us/browse>
- `t474-a92g`: <https://data.cityofnewyork.us/dataset/t474-a92g>
- `46m8-77gv`: <https://data.cityofnewyork.us/dataset/46m8-77gv>
- `2cmn-uidm`: <https://data.cityofnewyork.us/dataset/2cmn-uidm>
- `fi59-268w`: <https://data.cityofnewyork.us/dataset/fi59-268w>
- `djxg-kcfi`: <https://data.cityofnewyork.us/dataset/djxg-kcfi>
- `fb86-vt7u`: <https://data.cityofnewyork.us/dataset/fb86-vt7u>
- `wa2y-rh4b`: <https://data.cityofnewyork.us/dataset/wa2y-rh4b>
- `4d7f-74pe`: <https://data.cityofnewyork.us/dataset/4d7f-74pe>
- Prior work: [2026-07-08 IBO crosswalk](2026-07-08-ibo-data-center-crosswalk.md),
  [2026-07-07 FY09–FY21 legacy import scoping](2026-07-07-fy09-fy21-legacy-import-scoping.md)

## Limits

- Searches return the top 10 matches and catalog queries 30 to 60. A Council dataset with an
  unusual title could be missing. The "City Council" catalog query returned 40 results, and
  every Council-attributed budget dataset in it is listed above.
- Row counts marked "not checked" are unknown, not zero.
- I read column lists and previews, not data dictionaries. The attached dictionaries
  (`City_Council_Capital_Budget_Data_Dictionary.xlsx`, `Capital_Budget_Data_Dictionary.xlsx`)
  were not downloaded.
