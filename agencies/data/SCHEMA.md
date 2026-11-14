# `nyc_budget.csv` — schema and methodology

Stable documentation of the City agency budgets CSV, `agencies/data/nyc_budget.csv`. Since
#288 (2026-11-12) it is written from the MCP index's `agency_budget` table by
[`viz/explorer/scripts/agency-csv.mjs`](../../explorer/scripts/agency-csv.mjs); the table is built
by [`mcp/scripts/agency-budget.mjs`](../../../mcp/scripts/agency-budget.mjs), the one place the
year rule below is coded. (Until #288 [`code/agency_budget_cleanup.py`](../../../code/agency_budget_cleanup.py)
pulled Open Data and applied the rule itself; before #265 it was `data/nyc_budget_cleanup.py` in
BetaNYC/nyc-budget-viz.) This file is the contract a downstream consumer can build against without
re-reading the code. The explorer's view and the MCP read the table, not this file.

## Source

- **Dataset:** NYC Open Data "Expense Budget", id `mwzb-yiwb`.
- **API:** Socrata SODA 2.1. Resource `https://data.cityofnewyork.us/resource/mwzb-yiwb.json`,
  metadata `https://data.cityofnewyork.us/api/views/mwzb-yiwb.json`.
- **Auth:** none. Public, read-only. No app token required.
- **Coverage:** Fiscal Years 2017–2027 (inclusive).
- **SODA query reference:** https://dev.socrata.com/docs/queries/

Source field names (confirmed from the metadata endpoint, not guessed):
`publication_date` (text, `YYYYMMDD`), `fiscal_year` (number), `agency_number` (text),
`agency_name` (text), `unit_appropriation_number` (text), `unit_appropriation_name` (text),
`adopted_budget_amount` (number), `current_modified_budget_amount` (number),
`financial_plan_amount` (number).

## Which fiscal year each amount describes

> **Correction, 2026-11-09.** Before this date the pipeline labeled every amount one fiscal
> year too late (for example, the FY2025 adopted budget was shown as "Adopted 2026"). The
> mapping below is the corrected one.

A release's `fiscal_year` names the budget being proposed or adopted in that release. It is
not the year of every amount in the row. The dataset's data dictionary defines the three
amounts but does not say which year each covers. OMB's printed Adopted Budget does: the
FY2026 Adopted Budget, Expense/Revenue/Contract volume
(<https://www.nyc.gov/assets/omb/downloads/pdf/adopt25/erc6-25.pdf>) is the same publication as
the Open Data release dated `20250630` with `fiscal_year = 2026`, and its columns are headed
"Adopted Budget for FY 2025", "Current Modified Budget for FY 2025" and "Adopted Budget for
FY 2026". So, in a release tagged `fiscal_year = Y`:

| Field | Describes |
|---|---|
| `adopted_budget_amount` | FY **Y−1** adopted budget |
| `current_modified_budget_amount` | FY **Y−1** budget as modified, as of the release date |
| `financial_plan_amount` | FY **Y** plan (in the June release, the FY Y adopted budget) |

## One release per budget cycle (the anti-triple-count rule)

Each `fiscal_year` tag is published up to three times — Preliminary (January), Executive
(April/May), and Adopted (June) — and **each release restates the entire budget**. Summing
across releases counts the same money up to three times.

The pipeline keeps only the **June (adoption) release** of each tag: the latest
`publication_date` for the tag, which must fall in or after June of the prior calendar year.
Because `publication_date` is zero-padded `YYYYMMDD` text, its lexical maximum equals its
chronological maximum. Release dates are discovered from the data, not hard-coded.

## Validation gate

`mcp/test/agency-budget.test.js` (the table) and `code/test_agency_budget_cleanup.py` (this CSV)
fail unless the figures reproduce OMB's printed FY2026 Adopted Budget (link above) exactly:

| Check | Value | Where in the PDF |
|---|---:|---|
| Citywide FY2026 adopted, gross | $117,791,473,676 | p. 1E: net $115,907,309,727 + intra-city $1,884,163,949 |
| Citywide FY2025 adopted, gross | $114,384,991,832 | p. 1E: net $112,431,582,240 + intra-city $1,953,409,592 |
| Citywide FY2025 modified (June 2025), gross | $123,844,584,236 | p. 1E: net $121,598,357,432 + intra-city $2,246,226,804 |
| Manhattan CB 1 (341) unit 001 FY2025 adopted | $267,484 | p. 182E |
| Manhattan CB 1 unit 001 / 002 FY2025 modified | $249,484 / $190,939 | p. 182E |
| Manhattan CB 1 unit 001 / 002 FY2026 adopted | $275,060 / $27,245 | p. 182E |

Totals here are **gross**: Open Data rows include intra-city transfers, which OMB subtracts to
get its headline "net total budget" ($115.9 billion for FY2026). The two routes to "FY Y
adopted" (the citywide `financial_plan_amount` in the June release tagged Y, and
`adopted_budget_amount` in the release tagged Y+1) agree to the dollar for FY2017–FY2026.

## Grain

One row per `(agency_number, unit_appropriation_number)` pair — an agency's unit of
appropriation. As of the last regeneration (2026-11-09): **764 rows, 145 agency numbers**.
Releases before 2023 write both numbers without leading zeros (`40`, `1`); later releases pad
them (`040`, `001`). The pipeline pads both to three digits so a unit is one row across all
years. (Before 2026-11-09 they were not padded, so most units appeared as two rows.) Amounts
within a `(agency, unit, fiscal_year)` group are summed. Display names resolve to the newest
release the unit appears in.

## Columns

Header names are **case-sensitive** and kept as they were, so files and scripts that read them
keep working (Noel's default for #270: keep `Fund` / `Department` until a major release).

### Static columns

| Column | Meaning | Source |
|---|---|---|
| `Fund` | The **agency** (the site shows it as "Agency") | `agency_name` |
| `Department` | The agency's **unit of appropriation** (shown as "Unit of appropriation") | `unit_appropriation_name` |
| `Department ID` | The unit of appropriation's number | `unit_appropriation_number`, zero-padded to 3 digits (keep as text) |

The names `Fund` and `Department` are Look at Cook's (it was built for Cook County). They are kept
because `js/app.js` reads them and existing downloads use them.

**Removed in #266 (2026-11-09):** `Control Officer`, which equaled `Fund` on all 764 rows (it
fed Look at Cook's "Who controls it?" view, also removed), and `Short Title`, `Link to Website`
and `Department Description`, which were empty on all 764 rows. No descriptions or websites were
added: none came from an official City source, and none is invented.

### Per-fiscal-year columns

For each fiscal year `YYYY` in 2017–2027, two columns:

| Column | Meaning | Source |
|---|---|---|
| `Adopted YYYY` | Adopted budget for fiscal year `YYYY` | `sum(financial_plan_amount)`, June release tagged `YYYY` (equals `adopted_budget_amount` in the release tagged `YYYY+1`) |
| `Modified YYYY` | FY `YYYY` budget as modified through June of FY `YYYY` (near year end) | `sum(current_modified_budget_amount)`, June release tagged `YYYY+1` |

**The newest year's `Modified` is empty.** The City publishes FY `YYYY`'s modified figure in
the release that adopts FY `YYYY+1`. Until then (today: `Modified 2027`, until the FY2028
budget is adopted in June 2027) the cell is an empty string, not `0`. The site shows it as
"Not yet published". Consumers must treat empty as "no data", not zero.

**`0` can mean "not in this year's budget".** A unit that is not in a year's release at all is
written as `0` here, as the old app did (936 adopted cells as of 2026-11-09; 229 more are a real
$0). The explorer and the MCP say "Not in this year's budget" there; the `agency_budget` table
(DATA-DICTIONARY.md) has NULL. This file keeps the 0s so its shape does not change.

**"Modified" here is as of June.** It is the modified budget recorded in the June release,
shortly before the fiscal year closes on June 30. Checkbook NYC's year-end modified figure can
differ slightly.

**FY2016 is not shown.** The release tagged 2017 also carries the FY2016 adopted and modified
budgets, but the site's range starts at FY2017, so those amounts are not used.

Values are written plain — no `$`, no thousands separators. Whole-dollar amounts render as
integers; cents are preserved only when actually present. Consumers should parse them as floats.

## Regenerating

```bash
# from the repo root, after `npm ci` in mcp/ and viz/explorer/
python3 code/agency_budget_cleanup.py            # index build, then writes viz/agencies/data/nyc_budget.csv
python3 code/agency_budget_cleanup.py --check    # exit 1 if the committed file differs from the index
```

The same as `node viz/explorer/scripts/agency-csv.mjs` after the index build. Deterministic:
`viz/explorer/test/agency-csv.test.mjs` checks the committed file equals the index byte for byte
(CRLF line ends, minimal quoting, as Python's `csv` module wrote it before). To take in a new
June release, refresh the snapshot first (`python3 code/fetch_agency_budget_qa.py`), then run
`python3 code/qa_agency_budget.py`, the independent check.

## The MCP and the explorer

- Since 2.1.0 the budget MCP serves these figures (`search_agency_budget`,
  `compare_adopted_modified`) from the `agency_budget` table, and the explorer's City agency
  budgets view reads the same table as Parquet. Both use the `(agency, unit)` grain, the
  one-June-release rule and the year mapping above, never the raw multi-publication rows.
- Keep `agency_number` / `unit_appropriation_number` as **strings**; they are zero-padded and
  casting to int drops leading zeros (`040` → `40`).
- There is one dimension, agency then unit of appropriation. A second one (e.g. object class)
  would need a real field from the source, not a copy of the agency.
