# Plan: serve OMB's capital commitment plan and DCP's CPDB in the MCP (#250)

**Report generated:** 2026-11-13 · **Revised:** 2026-11-14 (scope: all of it ships in 2.1.0; CPDB's unit settled; `fi59-268w` pulled) · **Data current as of:** 2026-11-14 (each dataset's live metadata read from `data.cityofnewyork.us/api/views/<id>.json`, one request each)

Part of the 2.1.0 release epic #312. Issue: #250. This is the plan only; no code yet. It says what to build, what each figure means and where it comes from, how it is tested, and how the work splits into pull requests.

## 1. The three datasets, from their own documentation

| | `2cmn-uidm` Capital Commitment Plan | `djxg-kcfi` CPDB - Commitments | `fi59-268w` CPDB - Projects |
|---|---|---|---|
| Publisher | OMB | DCP | DCP |
| Live `rowsUpdatedAt` | 2026-09-28 | 2026-08-24 | 2026-08-24 |
| In the repo | `source/open-data-2cmn-uidm/` (pulled 2026-10-14, 60,739 rows; same `rowsUpdatedAt` as live) and `data/capital/omb_commitment_plan_council_lines.csv` (Council-series lines, 17,890 rows) | `source/open-data-djxg-kcfi/` (pulled 2026-10-21, 41,277 rows; same `rowsUpdatedAt` as live) | `source/open-data-fi59-268w/` (pulled 2026-11-14 in PR A, 12,929 rows, `ccpversion` `fisa_2026`; every `maprojid` is also in `djxg-kcfi`) |
| Grain | release (`pub_date`) × budget line (`budline`) × `funding` (City / Non City), 4 or 5 years from `yr1_fy` | one planned commitment: `maprojid` × `budgetline` × `plancommdate` × `commitmentcode` | one FMS project (`maprojid` = `magency` + `projectid`) |
| Money | `year1_amt` … `year5_amt`. **Thousands of dollars**: OMB's data dictionary (`source/open-data-2cmn-uidm/Capital_Commitment_Plan.xlsx`, sheet "Field Definition") says "The dollar values are in thousands." | `ccnonexempt`, `ccexempt`, `totalcityplannedcommit`, `nccstate`, `nccfederal`, `nccother`, `totalnoncityplannedcommit`, `totalplannedcommit`. **Unit not stated** in the column descriptions, and the dataset has no data-dictionary attachment | planned (`totalplannedcommit` …), `adopt_*`, `allocate_*`, `commit_*`, `spent_*`, and `spent_total_checkbooknyc` ("Sum of check values from Checkbook NYC"). **Unit not stated**, no attachment |
| Versions | 32 releases, 2016-04-26 → 2026-09-28: history | one version, `ccpversion` (the inventory read `fisa_2026`) | one version, the same |
| Link to the Council | `budline` (no space: `AGD001`), normalized to `AG D001` as `data/capital/` already does | `budgetline` with a hyphen (`AG-DN04L`) | **no budget line at all**: only through `djxg-kcfi`'s `maprojid`, and one project can sit on several budget lines |

Every field name and meaning above is from the metadata read on 2026-11-13. Two facts are **not** in it. Both are now settled (2026-11-14):

1. **CPDB's unit: whole dollars.** Checked against OMB's own figures, which OMB says are in thousands. For every `2cmn-uidm` release from 2025-09-30 to 2026-09-28, CPDB's `totalcityplannedcommit`, summed per budget line and fiscal year (`plancommdate`, July–June), is exactly 1,000 times OMB's City amount at the median. Against the 2026-05-12 release, 1,875 of 2,348 line-years are equal to the dollar after × 1,000; none are equal without it. **DCP never states the unit in writing** (searched 2026-11-14): its data dictionary ([`cpdb_data_dictionary.xlsx`](https://s-media.nyc.gov/agencies/dcp/assets/files/excel/data-tools/bytes/cpdb_data_dictionary.xlsx), linked from the [CPDB page](https://www.nyc.gov/content/planning/pages/resources/datasets/capital-projects-database)) has a column for "the unit of measurement of the data field, e.g. thousands, millions", and fills it for every amount with only "double precision". The [db-cpdb wiki](https://github.com/NYCPlanning/db-cpdb/wiki/Data-Dictionary) labels the fields "$ City Cost (Non-Exempt)" and so on, with no unit. Two pieces of DCP's own code agree with whole dollars: db-cpdb's older build multiplied OMB's commitment-plan amounts by 1000 (`sql/cpdb_build_master.sql`, lines 68, 87 and 98, at commit `2570923`), and DCP's capital-projects map describes a commitment filter as a "USD amount, with cents ... optional" (NYCPlanning/ae-cp-map, `app/gen/zod/findCapitalProjectsSchema.ts:74`). No source says thousands. So every CPDB figure is served with this sentence: "whole dollars: DCP does not state the unit; BetaNYC checked that CPDB's figures equal OMB's (published in thousands) times 1,000." Noel may instead choose to serve CPDB without amounts (§7).
2. **`ccpversion`** is `fisa_2026` on every row of both CPDB datasets. Its figures tie most closely to OMB's 2026-05-12 release (above). An answer names the version and its publication date (2026-08-24), not a plan release, because DCP does not say which release it is.

## 2. The rules every answer keeps

- **The budget line is the only link.** Council project IDs appear in no OMB or DCP dataset (#89's stage map). A tool says, every time, that it links by budget line, never by project, and that one budget line holds many projects.
- **Never blended.** No sum adds Council figures to OMB or DCP figures. Each figure is shown with its source, release or version, and unit.
- **Units in words.** Every answer that shows a `2cmn-uidm` figure says "in thousands of dollars" beside it (or shows the dollar figure computed from it and says so). Never both forms unlabeled.
- **Versions in words.** CPDB is one version: an answer says "as of CPDB `ccpversion` …, published 2026-08-24; it cannot show change over time".
- **Spending is not this server's.** `spent_total_checkbooknyc` is DCP's sum of Checkbook checks per project. A spending question goes to `@betanyc/nyc-checkbook-mcp`; this tool shows DCP's figure as DCP's, labeled, and only per project, never summed to a budget line (a project on several lines cannot be split).
- The provenance footer and caveat pattern of `search_council_capital` and `compare_capital_to_omb`.

## 3. Tool shape (recommended)

A new tool, **`search_capital_plan`**, rather than a section of `compare_capital_to_omb`, because the questions differ ("when is the money planned to be committed?" vs. "does the Council's list match OMB's?") and a section would make that tool's answer much longer.

- Input: `budget_line` (exact, the same normal form as `compare_capital_to_omb`), `pub_date` or `release` (a `2cmn-uidm` release; default the newest), `fiscal_year`, `funding` (City / Non City), `limit`.
- Answer, for a budget line:
  1. the commitment plan, newest release first, each release's four or five years **in thousands**, City and Non City apart; the release history for the line (how the plan moved);
  2. the CPDB planned commitments on that line (`djxg-kcfi`), by project and date, in CPDB's unit once settled;
  3. per project on that line, DCP's project totals (`fi59-268w`: planned, adopted, committed, spent), labeled per project and never summed to the line;
  4. the Council's own rows for the line (`capital_council`), as `compare_capital_to_omb` already finds them, apart.
- `list_available_fiscal_years` adds the plan's releases and CPDB's version.

## 4. Data and index

- **Pull `fi59-268w`** with the existing pattern (`code/fetch_open_data_capital.py`: `$order=:id`, 5,000 a page, ≥2 s apart, app token from `SOCRATA_APP_TOKEN`, stop on 403 or a second 429; `source/open-data-fi59-268w/` with `<id>.csv.gz`, `count.json`, `metadata.json` and `MANIFEST.csv`, the pull date recorded). Read-only pulls are authorized for these three datasets.
- **Index tables** (npm index, built by `mcp/scripts/build-index.mjs`): `capital_plan` from the whole `2cmn-uidm` snapshot (60,739 rows, not only Council lines, so a line's plan is complete), `cpdb_commitments` (41,277), `cpdb_projects` (about 12,929). Each table's row count is checked against its manifest; a missing manifest or a count mismatch stops the build. Amount columns keep the source's unit, with the unit in the column name (`year1_amt_k`).
- **Size:** about 115,000 rows. The npm index grows by an estimated 10–15 MB; measure it, and if it is too large keep `capital_plan` to Council-series lines plus the lines CPDB names.

## 5. Tests first

- Each table equals its committed snapshot, row for row (counts and a column checksum per release or version).
- For three budget lines chosen from the committed files (one Council-heavy, one with Non City funding, one with several releases), the tool's figures equal the source rows to the dollar (or thousand), with the unit stated.
- No answer adds figures across sources; an answer that shows `2cmn-uidm` always says "thousands" (a test scans every answer).
- A project on several budget lines never has its spent total attributed to one line.
- The unit check in §1 runs as a test: CPDB's City total per budget line and fiscal year is 1,000 times OMB's at the median, against the newest `2cmn-uidm` release. If DCP ever changes CPDB to thousands, the build fails before a wrong dollar is served.
- Unknown parameters rejected; tool lists, counts and response-size budgets updated (`tools.test.js`, `pdf-tools.test.js`, `shipped-data.test.js`, `README`).

## 6. Size, and how to split it

This is **bigger than one pull request**: a new pull and its tests, three index tables with build checks, a new tool with about a dozen tests, and docs. One reviewable change per PR, stacked, all three in 2.1.0 (Noel, 2026-11-14: everything ships before the tag; nothing waits for a later release):

| PR | What | Depends on |
|---|---|---|
| **A** | This plan, and the `fi59-268w` pull (registry entry, snapshot, manifest, README, test). Data only; no MCP change. | — |
| **B** | Load `capital_plan`, `cpdb_commitments`, `cpdb_projects` into the index with count and checksum checks; `list_available_fiscal_years` reports them. No new tool. | A |
| **C** | `search_capital_plan`, its tests, README, CHANGELOG, `WHATS-CHANGED.md` (under the Unreleased 2.1.0 entry). | B |

## 7. Decisions

- **Scope** (Noel, 2026-11-14): all three datasets ship in 2.1.0.
- **Split:** A, B, C as above, each its own PR on the 2.1.0 stack.
- **Tool:** a new `search_capital_plan`, as recommended in §3. Noel can still ask for it as a section of `compare_capital_to_omb` instead, in review of PR C.
- **CPDB amounts (for Noel):** served as whole dollars with the sentence in §1, or not served at all because DCP does not state the unit in writing. Recommended: serve them, labeled, with the unit test in §5 guarding them. PR B is built so one switch drops CPDB amounts and keeps CPDB's projects, budget lines and dates.
- **Size:** PR B measures the index with the whole `2cmn-uidm`. If the npm package grows by more than 15 MB, it keeps Council-series lines plus the lines CPDB names, and says so.
