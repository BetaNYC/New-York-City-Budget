---
title: Budget explorer — plan
created: 2026-10-20
type: plan
status: draft
tags: [viz, explorer, duckdb, mcp]
---

# Budget explorer — plan

**Report generated:** 2026-10-20 · **Data current as of:** `origin/main` @ 893a920

A static, in-browser explorer for the structured Council data this repo already holds, built on
the pattern of [BetaNYC/nyc-eo-explorer](https://github.com/BetaNYC/nyc-eo-explorer): Parquet
files served as static assets, queried with DuckDB-WASM in the browser. No server, no API.

## Goal

Let anyone search, filter, and chart the Council's discretionary awards, and trace every row to
the Council file and row it came from, using **exactly the data the MCP
(`@betanyc/nyc-budget-mcp` 2.x) serves**.

## Scope

**In (v1):**

- Expense awards: `data/fyNN/expense_disclosure/`, years as listed in `data/disclosure_years.csv`
  (`loaded = yes`: FY2009, FY2011–FY2027). Per-year provenance and notes (early snapshot, FY2010
  not loaded) come from the same file.
- Council capital awards: `data/capital/council_capital_awards.csv` (FY2015–FY2017,
  FY2019–FY2027) and the Council-vs-OMB comparison
  (`data/capital/council_vs_omb_by_budget_line.csv`).
- A link from each row to its source spreadsheet in `source/` (`source_file`, `source_row`).
- A link from the existing notice at `viz/index.html` to the explorer.

**Out (v1):**

- Anything extracted from PDFs: Schedule C, Terms & Conditions, transparency resolutions,
  `data/combined/`, `data/recovered/`. A PDF-derived year joins only after its review issue in
  epic #101 closes, and through the same build as the MCP, never a separate path.
- `viz/legacy.html` and `viz/data/schedule_c.csv` stay frozen and untouched.
- No live calls to the Council site or Legistar. Build input is the repo only.

## Same data as the MCP — by construction, then by test

1. **One loader.** The explorer's data build does not re-parse the CSVs. It runs the MCP's own
   `mcp/scripts/build-index.mjs` to produce `budget.db`, then exports the needed tables
   (`disclosure`, `disclosure_years`, `capital_council`, `capital_sources`, `capital_vs_omb`) to
   Parquet with DuckDB. A rule change in the MCP build therefore reaches the explorer
   automatically. (If reading SQLite from DuckDB proves awkward, the fallback is to factor the
   loader into a shared module both builds import. Not two parsers.)
2. **Parity test.** For every fiscal year, row counts and dollar totals (by status for
   disclosure; by year for capital) computed from the Parquet files must equal those computed
   from `budget.db`. Runs in CI on every PR; a mismatch fails the check.

## Gaps shown as gaps

A year with no data renders as "no data for this year" with the reason from
`disclosure_years.csv` or `data/capital/README.md`, never as $0. Known gaps at
893a920: FY2010 expense (not loaded, #89 A3), FY2018 capital (see #100), capital before FY2015.
FY2009 is an early snapshot and is labeled so; its cleared total is never a headline (#89 A5).

## Build and deploy

- `viz/explorer/` is a Vite + React app, structured like nyc-eo-explorer (`scripts/build-data.mjs`,
  `src/duckdb/`, `src/views/`, `test/`). Node ≥ 20, `@duckdb/node-api` for the build.
- **`deploy-viz.yml` must change.** Today it publishes `viz/` as-is with `git subtree split`;
  there is no build step. The new job: check out, build the MCP index, build the explorer data
  and app, assemble the static site (notice + legacy + `explorer/`), publish to `gh-pages`.
  Trigger paths widen to `data/**`, `mcp/scripts/**` and `viz/**`, so a data merge redeploys.
- Built Parquet files are gitignored, as in nyc-eo-explorer.

## Views (v1)

- **Browse/search:** awards by year, Council member, organization, EIN, agency, status, amount.
- **Award detail:** every column, flags explained, link to the source spreadsheet row.
- **Year overview:** totals by year with the gap and early-snapshot notes inline.
- **Capital:** by district/sponsor/budget line, plus the Council-vs-OMB comparison.

## Tests

- Unit tests for query building and URL state (as in nyc-eo-explorer).
- The parity test above.
- Existing `viz/test_pages_site.py` keeps passing; the notice gains one link.

## Documentation

`viz/README.md` (new section + files table), root `README.md`, `mcp/README.md` (pointer to the
explorer), CHANGELOG entry.

## Open questions

- Credit line for nyc-eo-explorer's design (its license allows reuse; confirm wording).
- Whether the source spreadsheets in `source/` are served from Pages or read cross-origin
  (sizes to check).
