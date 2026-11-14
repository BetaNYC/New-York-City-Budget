# `viz/` — the GitHub Pages site

One site, two halves (epic #272), at https://betanyc.github.io/New-York-City-Budget/:

| Path | What |
|---|---|
| `./` | Front page: two doors and "which tool answers my question?" |
| `agencies/` | Forwards old City agency budgets links to `explorer/#view=agencies` (#288); the CSV download, the FAQ and the community boards table |
| `explorer/` | **Council discretionary funding** and, at `#view=agencies`, **City agency budgets** (NYC Open Data `mwzb-yiwb`), built from `viz/explorer/` |
| `legacy.html` | The first Council explorer, retired: a "this moved" page that forwards old links into `explorer/` (#304) |

Every page carries the same top bar and footer, written by `site_shell.py` (#267).


**History: from 2.0.0 to #267 the site root was a retirement notice.** The interactive Schedule C explorer that
used to be the root is built on figures extracted from the Council's adopted-budget PDFs, and
BetaNYC no longer stands behind that extraction. It stays online, unchanged apart from a
"frozen, do not cite" banner, at `legacy.html`, so existing links still resolve; `index.html` explains the
retirement, states the 2.0 coverage gaps, points to the structured datasets and the MCP, and
offers a link into the retired copy when someone arrives with an old `#…` deep link.

**`legacy.html` is retired (#304, Noel, 2026-11-13).** The look-at-cook app it held, frozen since
2026-10-16, failed the accessibility checks and is not repaired. The page is now a short "this
moved" page in the site shell (`noindex`). Its inline script forwards the old app's links into the
explorer's Schedule C search: `#?year=Y` to `#view=schedc&scfy=Y`, and
`#fund-detail/<category>?year=Y` or `#control-officer-detail/<agency>?year=Y` to the same year with
`sccat` or `scagency`; a link that also names an initiative searches by the initiative alone
(`scinit`), since Schedule C often prints no category or agency on an initiative's rows. The old links carry slugs, so the script
reads the old app's data (`data/schedule_c.csv`, frozen) to turn each one back into its name. A year
outside FY2018–FY2027, or any other link, goes to the explorer's home. The old app's data gets no
further updates and no build step regenerates it. Do not rerun `schedulec_cleanup.py` to refresh it.

**Why retire rather than rebuild.** A rebuild on the structured data (the Council's disclosure
spreadsheets and capital lists) means deciding what the site should show, which totals are
headlines, how to present early-snapshot years and FY2010, and that is an editorial decision
for a separate change. Retiring the PDF-derived view is the smallest change that stops the site
presenting those figures as current.

**The budget explorer (`explorer/`, added 2026-10-20).** An in-browser explorer for the
structured data the MCP serves: the Council's expense funding disclosure (FY2009, FY2011–FY2027)
and Council capital (FY2015–FY2017, FY2019–FY2027), with the Council-vs-OMB comparison. Its data
build runs the MCP's own index build and exports that index to Parquet, and a parity test in CI
checks, year by year, that the two hold the same rows and the same totals. Years with no data
show "no data for this year" and the recorded reason, never $0. Every row links to the source
spreadsheet in `source/`, pinned to the build's commit. Nothing PDF-derived is in it. Source,
build and tests: [`explorer/README.md`](explorer/README.md).

Deployed by `.github/workflows/deploy-viz.yml` on a push to `main` that touches `data/**`,
`mcp/scripts/**`, `mcp/src/fold.ts` or `viz/**`. Since the explorer, the deploy builds the site
rather than publishing `viz/` as-is: it builds the MCP index, the explorer's data and app, runs
the Pages tests and the parity test, assembles everything in `viz/` except `viz/explorer/` plus
the built explorer at `explorer/`, and force-pushes that to `gh-pages`.

## Files

| Path | What |
|---|---|
| `index.html` | The front page: two doors (City agency budgets, Council discretionary funding), "which tool answers my question?", how the PDF tables are checked, and the notice about the frozen first explorer. Self-contained: no stylesheet or script file, one inline script that only fills the deep link. |
| `legacy.html` | Where the first Council explorer (look-at-cook, was `index.html`) lived. Since #304 a short "this moved" page in the site shell, `noindex`: what it was, that it was retired, links to the explorer and the data sources, and a script that forwards old links (above). |
| `site_shell.py` | Writes the shared top bar (skip link, nav to every page) and footer (fiscal year, source, data date, last revised) into every page (#267). `python3 viz/site_shell.py --check` fails if a page's blocks are missing or stale; the Pages test runs it. |
| `test_pages_site.py` | Tests for the pages (stdlib only; `python3 viz/test_pages_site.py` or pytest). |
| `schedulec_cleanup.py` | Builds `data/schedule_c.csv`, the retired explorer's data, from the PDF-derived `data/{year}/schedule_c/*.csv`. Kept so the old app's data stays reproducible; not rerun. `legacy.html` reads that file only to resolve old links. |
| `test_schedulec_cleanup.py` | Its regression tests: kept for the old app's data (the reconciliation gate, axis totals, the column contract the old JS read). |
| `data/schedule_c.csv` | The retired explorer's data (PDF-derived). `legacy.html` reads its names to forward old links. |
| `js/`, `css/`, `lib/`, `fonts/`, `images/` | The look-at-cook toolkit the retired app used. No page loads it since #304; kept for its history and licences. |
| `PLAN.md` | The original design notes for the explorer (historical). |
| `explorer/` | The budget explorer's source (Vite + React + DuckDB-WASM): data build, app, unit and parity tests. Built into `explorer/` on the published site. See [`explorer/README.md`](explorer/README.md). |
| `explorer/PLAN.md` | The explorer's plan. |
| `agencies/` | From [BetaNYC/nyc-budget-viz](https://github.com/BetaNYC/nyc-budget-viz) by `git subtree add` (#265). Since #288 its app is retired: `index.html` forwards old links to the explorer's City agency budgets view; the CSV (`data/nyc_budget.csv`, written from the MCP index), the FAQ and `boards.html` stay. See [`agencies/README.md`](agencies/README.md). |
| `LICENSE.md` | DataMade's MIT license for look-at-cook (retained verbatim). |

## Run it locally

```bash
cd viz && python3 -m http.server 8802
# http://localhost:8802/            the notice
# http://localhost:8802/legacy.html where the retired explorer was (forwards old links)
```

The budget explorer needs a build; see [`explorer/README.md`](explorer/README.md) (`npm run dev`,
or `scripts/assemble-site.mjs` for the whole site as deployed).

## Tests

```bash
python3 viz/test_pages_site.py
python3 viz/test_schedulec_cleanup.py
python3 viz/schedulec_cleanup.py --check
(cd viz/explorer && npm test)    # explorer unit + parity tests (after npm run data)
```

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

See the full suite of BetaNYC's civic-data tools at **[beta.nyc/ai-tools](https://beta.nyc/ai-tools)**.

The retired Schedule C explorer shared its toolkit (DataMade's [Look at Cook](https://github.com/datamade/look-at-cook)) with the first **City agency budgets** explorer (from [nyc-budget-viz](https://github.com/BetaNYC/nyc-budget-viz), #265; retired in #288, now the explorer's `#view=agencies`): NYC's full **expense budget**, every agency, adopted vs. modified, FY2017–FY2027, from NYC Open Data `mwzb-yiwb`. FY2026 adopted: $115.9 billion net (OMB's figure), or $117,791,473,676 as counted in Open Data, which includes $1,884,163,949 of intra-city money. That one covers the citywide total.

## Attribution

The retired explorer (once at `legacy.html`) was built on **[look-at-cook](https://github.com/datamade/look-at-cook)**
by **[DataMade](https://datamade.us)** (Derek Eder, Nick Rougeux) and **Open City**,
released under the MIT License (see `LICENSE.md`, retained verbatim). Adapted for NYC
Council Schedule C funding by **[BetaNYC](https://beta.nyc)**.

Its data is the PDF-derived Schedule C data in this repository, retired in 2.0.0; the
underlying source documents are © the City of New York.
