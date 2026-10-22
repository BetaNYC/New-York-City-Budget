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
from `mcp/dist/fold.js`; source-page links and GitHub file links use the MCP's row-link builder,
imported from `mcp/dist/rowlinks.js`.

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

`public/data/`, `dist/`, `site/` and `.cache/` are build output and gitignored.

### With the reviewed PDF data (local or demo builds only)

```bash
npm run data -- --include-reviewed   # index built into .cache/budget-reviewed.db, never mcp/data/budget.db
npm test && npm run build && npx vite preview
```

This adds the PDF families `data/pdf_years.csv` lists with `status = reviewed` (FY2027 capital §254
and Terms & Conditions, GitHub #102). Every row, page and chart from them says **"checked, review
in progress"**, and a banner says the build includes data still in review. The public deploy
(`deploy-viz.yml`) runs `npm run data` with no flag, so it shows only `closed` families (none yet);
the `pdf_*` tables are then empty and their tabs hidden. How the data gets here:
[`INTEGRATION.md`](INTEGRATION.md); the loader: `mcp/scripts/pdf-families.mjs`.

## Views

| View | What it shows |
|---|---|
| Expense awards | Search and filter by year, status, organization, EIN, Council member, agency, program, funding source, amount. Totals by status over every match; early-snapshot and other-status notes; one page of rows, highest amount first. |
| Award detail | Every column, flags explained, and the source: workbook, sheet, row, retrieval date, sha256, the Council's URL, and a link to the committed spreadsheet. |
| Years | Totals per fiscal year for both datasets. A year with no data says "no data for this year" with the recorded reason (FY2010 expense: `data/disclosure_years.csv`; FY2018 capital and nothing before FY2015: `data/capital/README.md`). Early snapshots are labeled and get no bar. |
| Capital | Council capital rows by report year, sponsor, borough, district, budget line, title, amount; report-year vs out-year amounts; detail with source link. |
| Capital vs OMB | The Council-vs-OMB comparison by budget line, disagreements first. |
| About the data | Coverage, gaps, provenance, credits. Readable before the data loads. |
| Capital, with a §254 book loaded | The book's printed totals and summary page above the rows, and per row the book's Part I sponsor as printed (`SANCHEZ J.` / `SANCHEZ P.` where the workbook says `Sanchez`), its FY+1..FY+3 columns, its page and review flags. Matched on report year, Council ID (without the agency code) and budget line. |
| Organizations | §254 Part III: each non-city organization's printed line and its budget-line rows, with whether they add up. Only when a capital book is loaded. |
| Terms & Conditions | The year's conditions by agency, unit of appropriation or budget line, kind, and text; deadlines after "no later than"; condition 15's FSR table. Only when a T&C family is loaded. |
| Review (reviewed builds only) | The review queue: every flagged row of every loaded PDF family, critical first, then by dollars; filters for family, year, check, severity, open/decided. Each item shows the PDF page with the row highlighted, the parsed values, the review fields and the suggested decision (`data/pdf_review_suggestions.csv`, from each REVIEW.md). Buttons: keep as printed (`accepted_as_printed`), accept suggestion, needs more information (`needs_info`), change to… (`parser_bug`, the value in the note). Decisions stay in the browser (localStorage) and export per family as `review_id,decision,note,decided_by,decided_at`, the Schedule C decisions file's header, to the path shown; import resumes a review. Check a file with `code/validate_review_decisions.py`. |
| Source page | Any PDF-derived row opens its PDF page (pdf.js) with the row's `bbox_pt` box highlighted. The PDF is read from GitHub at the build commit, like the spreadsheets; rotated pages (the capital book is `/Rotate 90`) are handled by pdf.js's viewport. The page opens scrolled so the box is in view. |

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
| `src/query/pdf.js` | Queries over the reviewed PDF tables, the §254-to-workbook match, and the box math for the highlight. |
| `src/components/PdfViewer.jsx`, `src/components/pdf.jsx` | The source viewer; the review label, flag badge and page link. |
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
(`src/state/hash.js`), asset URLs (`src/paths.js`), the Vite configuration, and the PDF viewer
(`src/components/PdfViewer.jsx`, from its `PdfViewer.jsx`, and the viewer's CSS). Its license is
reproduced in [`LICENSE-nyc-eo-explorer`](LICENSE-nyc-eo-explorer). The rest of this folder is
BetaNYC's, MIT, under the repository's [`LICENSE`](../../LICENSE).

Bundled into the built site, each under its own license: DuckDB-WASM (MIT), React and React DOM
(MIT), Apache Arrow (Apache-2.0), pdf.js (`pdfjs-dist`, Apache-2.0). The source documents are © the City of New York.
