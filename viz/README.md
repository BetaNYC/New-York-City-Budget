# `viz/` — the GitHub Pages site (Schedule C explorer frozen in 2.0; budget explorer added)

**Since 2.0.0 the site root is a retirement notice.** The interactive Schedule C explorer that
used to be the root is built on figures extracted from the Council's adopted-budget PDFs, and
BetaNYC no longer stands behind that extraction. It stays online, unchanged apart from a
"frozen, do not cite" banner, at `legacy.html`, so existing links still resolve; `index.html` explains the
retirement, states the 2.0 coverage gaps, points to the structured datasets and the MCP, and
offers a link into the retired copy when someone arrives with an old `#…` deep link.

**`legacy.html` is frozen as of 2026-10-16.** It stays published, but its data
(`data/schedule_c.csv`) gets no further updates and no build step regenerates it. Do not rerun
`schedulec_cleanup.py` to refresh it.

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
the built explorer at `explorer/`, and force-pushes that to `gh-pages`. The notice and the legacy
page are published exactly as before.

## Files

| Path | What |
|---|---|
| `index.html` | The retirement notice. Self-contained: no stylesheet or script file, one inline script that only fills the deep link. Links to the explorer. |
| `legacy.html` | The retired look-at-cook explorer (was `index.html`), frozen 2026-10-16, with a "frozen, do not cite" banner, `noindex`, and a breadcrumb that points at itself. |
| `test_pages_site.py` | Tests for both pages (stdlib only; `python3 viz/test_pages_site.py` or pytest). |
| `schedulec_cleanup.py` | Builds `data/schedule_c.csv`, the retired explorer's data, from the PDF-derived `data/{year}/schedule_c/*.csv`. Kept so the legacy page's data stays reproducible; not rerun, since the page is frozen. |
| `test_schedulec_cleanup.py` | Its regression tests: still meaningful for the legacy page (the reconciliation gate, axis totals, the column contract the JS reads). |
| `data/schedule_c.csv` | The retired explorer's data (PDF-derived). |
| `js/`, `css/`, `lib/`, `fonts/`, `images/` | The look-at-cook toolkit the legacy page uses. |
| `PLAN.md` | The original design notes for the explorer (historical). |
| `explorer/` | The budget explorer's source (Vite + React + DuckDB-WASM): data build, app, unit and parity tests. Built into `explorer/` on the published site. See [`explorer/README.md`](explorer/README.md). |
| `explorer/PLAN.md` | The explorer's plan. |
| `LICENSE.md` | DataMade's MIT license for look-at-cook (retained verbatim). |

## Run it locally

```bash
cd viz && python3 -m http.server 8802
# http://localhost:8802/            the notice
# http://localhost:8802/legacy.html the retired explorer
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

The retired Schedule C explorer shares its toolkit (DataMade's [Look at Cook](https://github.com/datamade/look-at-cook)) with BetaNYC's citywide budget explorer, **[nyc-budget-viz](https://github.com/BetaNYC/nyc-budget-viz)** — a multi-year visualization of NYC's full **expense budget** (~$114B, every agency, adopted vs. modified), FY2017–FY2027, from NYC Open Data. That one covers the citywide total.

## Attribution

The retired explorer (`legacy.html`) is built on **[look-at-cook](https://github.com/datamade/look-at-cook)**
by **[DataMade](https://datamade.us)** (Derek Eder, Nick Rougeux) and **Open City**,
released under the MIT License (see `LICENSE.md`, retained verbatim). Adapted for NYC
Council Schedule C funding by **[BetaNYC](https://beta.nyc)**.

Its data is the PDF-derived Schedule C data in this repository, retired in 2.0.0; the
underlying source documents are © the City of New York.
