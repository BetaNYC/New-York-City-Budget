# `nyc_budget.csv` — schema and methodology

Stable documentation of the cleaned CSV emitted by [`code/agency_budget_cleanup.py`](../../../code/agency_budget_cleanup.py) (until #265, `data/nyc_budget_cleanup.py` in BetaNYC/nyc-budget-viz). This file is the
contract a downstream consumer (the front-end today, an MCP or API tomorrow) can build against
without re-reading the pipeline code.

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

The run aborts, writing nothing, unless the CSV reproduces OMB's printed FY2026 Adopted
Budget (link above) exactly:

| Check | Value | Where in the PDF |
|---|---:|---|
| Citywide FY2026 adopted, gross | $117,791,473,676 | p. 1E: net $115,907,309,727 + intra-city $1,884,163,949 |
| Citywide FY2025 adopted, gross | $114,384,991,832 | p. 1E: net $112,431,582,240 + intra-city $1,953,409,592 |
| Citywide FY2025 modified (June 2025), gross | $123,844,584,236 | p. 1E: net $121,598,357,432 + intra-city $2,246,226,804 |
| Manhattan CB 1 (341) unit 001 FY2025 adopted | $267,484 | p. 182E |
| Manhattan CB 1 unit 001 / 002 FY2025 modified | $249,484 / $190,939 | p. 182E |
| Manhattan CB 1 unit 001 / 002 FY2026 adopted | $275,060 / $27,245 | p. 182E |

Totals here are **gross**: Open Data rows include intra-city transfers, which OMB subtracts to
get its headline "net total budget" ($115.9 billion for FY2026). It also aborts if, for any
year, the citywide `financial_plan_amount` in the June release tagged Y differs from the
`adopted_budget_amount` in the release tagged Y+1 (the two routes to "FY Y adopted"; they
agree to the dollar for FY2017–FY2026).

## Grain

One row per `(agency_number, unit_appropriation_number)` pair — an agency's unit of
appropriation. As of the last regeneration (2026-11-09): **764 rows, 145 agency numbers**.
Releases before 2023 write both numbers without leading zeros (`40`, `1`); later releases pad
them (`040`, `001`). The pipeline pads both to three digits so a unit is one row across all
years. (Before 2026-11-09 they were not padded, so most units appeared as two rows.) Amounts
within a `(agency, unit, fiscal_year)` group are summed. Display names resolve to the newest
release the unit appears in.

## Columns

Header names are **case-sensitive** and must not change without a matching change in
`viz/agencies/js/app.js` (see the coupling note below).

### Static columns

| Column | Meaning | v1 source |
|---|---|---|
| `Fund` | Top-level grouping | `agency_name` |
| `Department` | Sub-grouping under Fund | `unit_appropriation_name` |
| `Control Officer` | Second top-level axis | `agency_name` (**v1 placeholder** — duplicates `Fund` so the front-end's second view renders; a real second axis, e.g. object class, replaces this later) |
| `Department ID` | Stable id for the unit | `unit_appropriation_number`, zero-padded to 3 digits (keep as text) |
| `Short Title` | — | empty in v1 |
| `Link to Website` | — | empty in v1 |
| `Department Description` | — | empty in v1 |

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

**"Modified" here is as of June.** It is the modified budget recorded in the June release,
shortly before the fiscal year closes on June 30. Checkbook NYC's year-end modified figure can
differ slightly.

**FY2016 is not shown.** The release tagged 2017 also carries the FY2016 adopted and modified
budgets, but the site's range starts at FY2017, so those amounts are not used.

Values are written plain — no `$`, no thousands separators. Whole-dollar amounts render as
integers; cents are preserved only when actually present. Consumers should parse them as floats.

### Column/label coupling (do not drift)

`js/app.js` reads each year's value with the key `<label> + ' ' + year`, where `label` is the
config's `apropTitle` (`'Adopted'`) or `expendTitle` (`'Modified'`). The CSV column **prefixes**
here must equal those labels exactly. The pipeline centralizes them in `APROP_LABEL` /
`EXPEND_LABEL`; rename one side and you must rename the other, or the chart reads `NaN`.

## Regenerating

```bash
# from the repo root
python3 code/agency_budget_cleanup.py            # writes viz/agencies/data/nyc_budget.csv (full) + sample
python3 code/agency_budget_cleanup.py --sample-only   # sample only (fast)
python3 code/agency_budget_cleanup.py --out DIR       # write into DIR
```

Stdlib only (`urllib`, `csv`, `json`) — no third-party dependencies. Idempotent: re-running
overwrites the output deterministically. Read-only against the API; writes only local CSVs.

## Notes for a future MCP / API

- The `(agency, unit)` grain, the one-June-release rule and the year mapping above are the
  stable primitives — an MCP should expose totals from the June release with the corrected
  year mapping, never the raw multi-publication rows.
- Keep `agency_number` / `unit_appropriation_number` as **strings**; they are zero-padded and
  casting to int drops leading zeros (`040` → `40`).
- The `Control Officer` placeholder is the one field that is not yet a real second dimension;
  design any second-axis query around a real field (e.g. object class) rather than this column.
