# NYC Budget Explorer

> **This folder is the City agency budgets half of
> [New-York-City-Budget](../../README.md)** (epic #272). It came from
> [BetaNYC/nyc-budget-viz](https://github.com/BetaNYC/nyc-budget-viz) `main` at `b90f922` by
> `git subtree add` (#265), so its history is kept. The pipeline and its tests now live in
> [`code/`](../../code/agency_budget_cleanup.py); the site is published at `agencies/`.

A multi-year visualization of **New York City's expense budget**, built by
[BetaNYC](https://beta.nyc). It shows every city agency's budget — broken down by unit of
appropriation — across Fiscal Years 2017 through 2027, and compares each agency's **adopted**
budget against its **modified** budget.

This is an adaptation of DataMade's [Look at Cook](https://github.com/datamade/look-at-cook),
a budget-transparency front-end originally built for Cook County, Illinois. The interactive
front-end is theirs (MIT-licensed); BetaNYC swapped in New York City's budget data and a data
pipeline that produces it. See [Attribution](#attribution).

## What it does

- Interactive chart of the citywide budget over 11 fiscal years, with a per-agency and
  per-unit breakdown table.
- Two series per year: **Adopted** (the budget adopted for that fiscal year) and **Modified**
  (that year's budget as modified through June, near year end). The newest year's Modified
  is "not yet published" until the City adopts the following year's budget.
- All data downloadable as a single CSV.

## Data

- **Source:** [NYC Open Data — Expense Budget](https://data.cityofnewyork.us/City-Government/Expense-Budget/mwzb-yiwb),
  dataset id `mwzb-yiwb`. Public, no API token.
- **Coverage:** Fiscal Years 2017–2027.
- **Validation:** FY2026 adopted total = **$117,791,473,676**, matching OMB's printed FY2026
  Adopted Budget (net $115,907,309,727 + intra-city $1,884,163,949). The run aborts if this,
  the FY2025 totals, or the Manhattan Community Board 1 lines from the same PDF don't match.

> **Correction (2026-11-09).** Before this date every year in the explorer was labeled one
> year late: "Adopted 2026" was really FY2025. In a release tagged `fiscal_year = Y`, the
> dataset's `adopted_budget_amount` and `current_modified_budget_amount` describe FY Y−1, and
> `financial_plan_amount` describes FY Y. Details: [`data/SCHEMA.md`](data/SCHEMA.md).

### Methodology (important)

Each fiscal year is published up to three times — Preliminary (Jan), Executive (Apr/May), and
Adopted (June) — and **each publication restates the whole budget**. Naively summing every row
would count the same money up to three times. The pipeline keeps only the **June release** of
each year, then maps each amount to the year it describes:

- **Adopted Y** = `financial_plan_amount` from the June release tagged Y (cross-checked against
  `adopted_budget_amount` in the release tagged Y+1; they agree to the dollar)
- **Modified Y** = `current_modified_budget_amount` from the June release tagged Y+1

A validation gate aborts the run unless the output reproduces OMB's printed figures.

Full column definitions and methodology: [`data/SCHEMA.md`](data/SCHEMA.md).

## Regenerating the data

The cleaned CSV the site loads (`data/nyc_budget.csv`) is produced by
[`code/agency_budget_cleanup.py`](../../code/agency_budget_cleanup.py) (moved there from this
folder's `data/` in #265). From the repo root:

```bash
python3 code/agency_budget_cleanup.py
```

Stdlib only (`urllib`, `csv`, `json`) — no third-party dependencies. Requires Python
`>=3.11,<3.15`. Idempotent and read-only against the API.

Tests:

```bash
python -m pytest code/test_agency_budget_cleanup.py   # also run in CI by python-checks.yml
```

## Running the site locally

The front-end is fully static. From `viz/` in this repo:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/agencies/>. `js/app.js` loads `data/nyc_budget.csv`, a relative
path, so the page works under `/New-York-City-Budget/agencies/` on GitHub Pages too.

## Layout

```
index.html, faq.html      front-end pages (masthead adapted for NYC)
js/, css/, lib/, fonts/    Look at Cook front-end (Backbone + Highcharts)
images/                    front-end assets
data/
  nyc_budget.csv           the cleaned data the site loads (built by code/agency_budget_cleanup.py)
  SCHEMA.md                column + methodology documentation
```

## Configuration

The build-time constants live at the top of `js/app.js`:

| Constant | Value | Note |
|---|---|---|
| `startYear` / `endYear` | 2017 / 2027 | fiscal-year range |
| `activeYear` | 2026 | default selected year |
| `municipalityName` | `New York City Budget` | masthead / breadcrumb |
| `apropTitle` / `expendTitle` | `Adopted` / `Modified` | chart line labels — **must match the CSV column prefixes** |
| `dataSource` | `data/nyc_budget.csv` | the cleaned CSV |

## Status and known TODOs

This is a working v1. Outstanding items:

- **`Control Officer` is a placeholder** (duplicates the agency view). A real second dimension
  (e.g. object class) would make the second top-level view meaningful.
- **BetaNYC brand pass is light.** The Look at Cook visual theme is largely intact; a full pass
  against BetaNYC's brand (color `#2359a8`, Poppins/Roboto, logo) remains.
- **Hosting:** published with the rest of this repo's GitHub Pages site at `agencies/` by
  `.github/workflows/deploy-viz.yml` (#265).
- `Short Title`, `Link to Website`, and `Department Description` are empty; they could be
  populated from an agency reference table.

## About BetaNYC

This project is built and maintained by [BetaNYC](https://beta.nyc), New York's
civic technology and open-data community. We work to improve lives in New York
through civic design, technology, data, and public-interest technology.

**Come do civic tech with us.** We run public events, meetups, and hands-on
data classes throughout the year — including [NYC School of Data](https://www.schoolofdata.nyc/)
and [CityCamp NYC](https://citycamp.nyc), and we host frequent civic-tech gatherings. See what's coming up on our
[events calendar](https://www.beta.nyc/events/).

**Sustain this work.** This project is free and open source. To help keep this work going and find BetaNYC's tools, please consider [donating and becoming a Beta Builder](https://beta.nyc/donate).

## Building on this? Tell us!

If you build something with this project, we'd love to hear about it. We can help other New Yorkers find it. BetaNYC publishes a weekly newsletter, *This Week in NYC's Civic Technology and Open Data*.

- **[Subscribe to the newsletter](https://beta.nyc/newsletter)** to keep up with NYC civic tech, open data, and public-interest technology.
- **Built something, or found a story worth sharing?** [Submit a link for the newsletter](https://www.beta.nyc/newsletter-inbox/) and we'll consider it for an upcoming issue.

## Related BetaNYC projects

BetaNYC maintains a growing suite of open-source tools for NYC and NYS civic data — see the full directory at **[beta.nyc/ai-tools](https://beta.nyc/ai-tools)**.

This visualization is a companion to **[New York City Budget](https://github.com/BetaNYC/New-York-City-Budget)** — machine-readable, reconciled NYC Council *discretionary* funding (Schedule C), Terms & Conditions, and Section 254 capital data, extracted line-by-line from the Council's adopted-budget PDFs. That repo also ships the [`@betanyc/nyc-budget-mcp`](https://github.com/BetaNYC/New-York-City-Budget/tree/main/mcp) server and a companion **Schedule C funding visualization** (`viz/`) built on this same [Look at Cook](https://github.com/datamade/look-at-cook) toolkit.

Where this repo shows the **citywide expense budget** (~$118B for FY2026, every agency), the Schedule C visualization shows **Council discretionary funding** (~$656M) — different datasets, same toolkit.

## Attribution

Adapted from **[Look at Cook](https://github.com/datamade/look-at-cook)** by DataMade, Derek
Eder, Nick Rougeux, and Open City. The original front-end is © 2019 DataMade and released under
the MIT License, preserved here in [`LICENSE.md`](LICENSE.md). BetaNYC's adaptation — the NYC
data pipeline, the cleaned dataset, and the NYC-specific copy — is likewise available under the
same terms. If you reuse this, keep the DataMade copyright and license intact.
