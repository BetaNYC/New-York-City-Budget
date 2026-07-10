# NYC Budget Explorer

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
- Two series per year: **Adopted** (the budget as adopted) and **Modified** (the current
  modified budget at the adopted snapshot).
- All data downloadable as a single CSV.

## Data

- **Source:** [NYC Open Data — Expense Budget](https://data.cityofnewyork.us/City-Government/Expense-Budget/mwzb-yiwb),
  dataset id `mwzb-yiwb`. Public, no API token.
- **Coverage:** Fiscal Years 2017–2027.
- **Validation:** FY2026 adopted total = **$114,384,991,832** (~$114.385B), matching the City's
  published adopted expense budget.

### The adopted-snapshot methodology (important)

Each fiscal year is published up to three times — Preliminary (Jan), Executive (Apr/May), and
Adopted (June) — and **each publication restates the whole budget**. Naively summing every row
would count the same money up to three times (~$343B for FY2026 instead of ~$114B). The pipeline
keeps only the **Adopted (latest) snapshot per fiscal year** and sums within it. A validation
gate aborts the run if the FY2026 total ever falls outside `[110B, 118B]`.

Full column definitions and methodology: [`data/SCHEMA.md`](data/SCHEMA.md).

## Regenerating the data

The cleaned CSV the site loads (`data/nyc_budget.csv`) is produced by
[`data/nyc_budget_cleanup.py`](data/nyc_budget_cleanup.py):

```bash
python3 data/nyc_budget_cleanup.py
```

Stdlib only (`urllib`, `csv`, `json`) — no third-party dependencies. Requires Python
`>=3.11,<3.15`. Idempotent and read-only against the API.

Tests:

```bash
cd data && python3 -m unittest test_nyc_budget_cleanup
```

## Running the site locally

The front-end is fully static. From the repo root:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>. `js/app.js` loads `/data/nyc_budget.csv` — serving from the
repo root is what makes that absolute path resolve.

## Layout

```
index.html, faq.html      front-end pages (masthead adapted for NYC)
js/, css/, lib/, fonts/    Look at Cook front-end (Backbone + Highcharts)
images/                    front-end assets
data/
  nyc_budget_cleanup.py    pipeline: SODA pull -> adopted-snapshot filter -> pivot -> CSV
  test_nyc_budget_cleanup.py  hermetic regression tests (no live API)
  nyc_budget.csv           the cleaned data the site loads
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
| `dataSource` | `/data/nyc_budget.csv` | the cleaned CSV |

## Status and known TODOs

This is a working v1. Outstanding items:

- **`Control Officer` is a placeholder** (duplicates the agency view). A real second dimension
  (e.g. object class) would make the second top-level view meaningful.
- **BetaNYC brand pass is light.** The Look at Cook visual theme is largely intact; a full pass
  against BetaNYC's brand (color `#2359a8`, Poppins/Roboto, logo) remains.
- **GitHub Pages / hosting** is intentionally not configured — left for a maintainer to enable.
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

Where this repo shows the **citywide expense budget** (~$114B, every agency), the Schedule C visualization shows **Council discretionary funding** (~$656M) — different datasets, same toolkit.

## Attribution

Adapted from **[Look at Cook](https://github.com/datamade/look-at-cook)** by DataMade, Derek
Eder, Nick Rougeux, and Open City. The original front-end is © 2019 DataMade and released under
the MIT License, preserved here in [`LICENSE.md`](LICENSE.md). BetaNYC's adaptation — the NYC
data pipeline, the cleaned dataset, and the NYC-specific copy — is likewise available under the
same terms. If you reuse this, keep the DataMade copyright and license intact.
