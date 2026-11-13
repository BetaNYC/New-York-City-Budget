# NYC Open Data Expense Budget (`mwzb-yiwb`): the agency budget accuracy snapshot

Publisher: Mayor's Office of Management and Budget (OMB). <https://data.cityofnewyork.us/d/mwzb-yiwb>.
Pulled 2026-11-09 (read-only, no app token) by [`code/fetch_agency_budget_qa.py`](../../code/fetch_agency_budget_qa.py)
for the agency budget accuracy test (#268).

**What it is for.** [`code/qa_agency_budget.py`](../../code/qa_agency_budget.py) recomputes every
Adopted and Modified figure the City agency budgets explorer shows
(`viz/agencies/data/nyc_budget.csv`, 764 units × FY2017–FY2027) from these files, with its own
code, and compares them to the dollar. [`code/test_qa_agency_budget.py`](../../code/test_qa_agency_budget.py)
runs it in CI. The year rule it applies is in [`DATA-DICTIONARY.md`](../../DATA-DICTIONARY.md)
and [`DATA-ANOMALIES.md`](../../DATA-ANOMALIES.md) §57.

| File | What |
|---|---|
| `releases.csv` | Every release in the dataset: `fiscal_year` tag, `publication_date`, row count (32 releases, tags 2017–2027) |
| `by_unit.csv` | For the latest release of each tag 2017–2027 (each one a June release), the server-side sums of `adopted_budget_amount`, `current_modified_budget_amount` and `financial_plan_amount` by agency × unit of appropriation, with names and row counts (7,468 rows). Values as served: numbers as text, agency and unit numbers unpadded before 2023 (`40`, `1`) and padded after (`040`, `001`) |
| `MANIFEST.csv` | Each request's URL (the exact SODA query), time, HTTP status, bytes and sha256 |

**Not the whole dataset.** The dataset has every release, Preliminary, Executive and Adopted; this
keeps all of their dates but sums only each tag's latest (June) release, the one the explorer uses.
The full rows of a different extract are in [`../open-data-mwzb-yiwb/`](../open-data-mwzb-yiwb/README.md).

**Since #284 it is also the source of the City agency budgets everywhere.**
[`mcp/scripts/agency-budget.mjs`](../../mcp/scripts/agency-budget.mjs) reads `releases.csv`,
`by_unit.csv` and `MANIFEST.csv` into the MCP index's `agency_budget` table, which the explorer's
City agency budgets view, the MCP tools and the CSV download all read.

**Replacing it.** Run `python3 code/fetch_agency_budget_qa.py` after the City publishes a new
June release, then `python3 code/agency_budget_cleanup.py` (index build, then the CSV) and
`python3 code/qa_agency_budget.py`. A new year makes the check fail until the CSV shows it too; `test_the_june_releases_are_pinned`
also fails until a person updates the pinned list. Both are on purpose: a person looks at every
change in the City's numbers before the site does.

Terms of use: [NYC Open Data Terms of Use](https://opendata.cityofnewyork.us/overview/#termsofuse).
