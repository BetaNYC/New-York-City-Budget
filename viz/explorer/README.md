# `viz/explorer/` — the NYC Council budget explorer

A static, in-browser explorer for the Council's expense funding disclosure and Council capital
data, published at
[betanyc.github.io/New-York-City-Budget/explorer/](https://betanyc.github.io/New-York-City-Budget/explorer/).
Parquet files served as static assets, queried with DuckDB-WASM in the browser. No server, no API.
Design and scope: [`PLAN.md`](PLAN.md). Site-level overview: [`../README.md`](../README.md).

**Same data as the MCP, by construction and by test.** `scripts/build-data.mjs` runs the MCP's own
index build (`mcp/scripts/build-index.mjs`) and copies `mcp/data/budget.db`'s tables, column for
column, into Parquet. It never parses a CSV. `test/parity.test.mjs` then checks, for every fiscal
year, that row counts and dollar totals equal `budget.db`, that every row and column is identical,
and that the explorer's queries (`src/query/sql.js`) answer exactly what the MCP's
(`mcp/src/db.ts`) answer for the same filters. Text search uses the MCP's own fold rule, imported
from `mcp/dist/fold.js`.

**Nothing PDF-derived.** Only the tables the MCP 2.0 index holds: `disclosure`,
`disclosure_years`, `capital_council`, `capital_sources`, `capital_vs_omb`, `meta`.

## Run it

Node 22.12 or newer. From a fresh clone:

```bash
(cd mcp && npm ci)            # the MCP's dependencies, dist/ and its index
cd viz/explorer
npm ci
npm run data                  # rebuild budget.db, export Parquet to public/data/
npm test                      # unit tests + parity with budget.db and the MCP
npm run dev                   # http://localhost:5276/
npm run build                 # dist/
node scripts/assemble-site.mjs --out /tmp/site   # the whole Pages site, as deployed
```

`public/data/`, `dist/` and `site/` are build output and gitignored.

## Views

| View | What it shows |
|---|---|
| Expense awards | Search and filter by year, status, organization, EIN, Council member, agency, program, funding source, amount. Totals by status over every match; early-snapshot and other-status notes; one page of rows, highest amount first. |
| Award detail | Every column, flags explained, and the source: workbook, sheet, row, retrieval date, sha256, the Council's URL, and a link to the committed spreadsheet. |
| Years | Totals per fiscal year for both datasets. A year with no data says "no data for this year" with the recorded reason (FY2010 expense: `data/disclosure_years.csv`; FY2018 capital and nothing before FY2015: `data/capital/README.md`). Early snapshots are labeled and get no bar. |
| Capital | Council capital rows by report year, sponsor, borough, district, budget line, title, amount; report-year vs out-year amounts; detail with source link. |
| Capital vs OMB | The Council-vs-OMB comparison by budget line, disagreements first. |
| About the data | Coverage, gaps, provenance, credits. Readable before the data loads. |

All state is in the URL hash, so any filtered view is a link.

## Source links

Each row links to its source spreadsheet in `source/` on GitHub, **pinned to the commit the site
was built from** (`manifest.json` `source_commit`): `raw.githubusercontent.com` to download it,
and github.com for its page. The spreadsheets are not copied into the site. They are 30 MB
together, small enough to serve from Pages, but a pinned GitHub link already names the exact file
that produced the row, keeps its history one click away, and keeps the deployed site to the app
and about 4 MB of data. Nothing in `source/` is in git LFS, so the raw link serves the file
itself. The app never fetches these files, so cross-origin rules do not apply.

## Files

| Path | What |
|---|---|
| `scripts/build-data.mjs` | Runs `mcp/scripts/build-index.mjs`, exports `budget.db` to `public/data/*.parquet` with `@duckdb/node-api`, writes `manifest.json` (commit, counts, sha256s, capital gap reasons). `--skip-index` exports the existing `budget.db`. |
| `scripts/lib/capital-gaps.mjs` | Reads the capital gap years and their reasons from `data/capital/README.md`; a gap it cannot explain stops the build. |
| `scripts/assemble-site.mjs` | Lays out the Pages site: `viz/` (minus this folder) plus `dist/` as `explorer/`. Refuses a non-empty output directory; never deletes. |
| `src/query/sql.js` | Query building (pure functions, `?` parameters), shared by the app and the parity test. |
| `src/state/hash.js` | URL-hash state. |
| `src/data/years.js` | The year overview's model: data or a gap with its reason, never a zero. |
| `src/duckdb/` | The DuckDB-WASM engine singleton and React hooks. |
| `src/views/`, `src/components/` | The views and shared UI. |
| `test/unit/` | Vitest unit tests (`npm run test:unit`). |
| `test/parity.test.mjs` | The parity test (`npm run test:parity`; needs `npm run data`). |
| `PLAN.md` | The plan this was built from. |
| `LICENSE-nyc-eo-explorer` | MIT license of the code adapted from nyc-eo-explorer. |

## Credits and licenses

Built by [BetaNYC](https://beta.nyc). The structure and several modules are adapted from BetaNYC's
[nyc-eo-explorer](https://github.com/BetaNYC/nyc-eo-explorer) (commit `45e47a8`), MIT License,
Copyright (c) 2026 BetaNYC: the DuckDB store and hook (`src/duckdb/`), URL-hash state
(`src/state/hash.js`), asset URLs (`src/paths.js`) and the Vite configuration. Its license is
reproduced in [`LICENSE-nyc-eo-explorer`](LICENSE-nyc-eo-explorer). The rest of this folder is
BetaNYC's, MIT, under the repository's [`LICENSE`](../../LICENSE).

Bundled into the built site, each under its own license: DuckDB-WASM (MIT), React and React DOM
(MIT), Apache Arrow (Apache-2.0). The source documents are © the City of New York.
