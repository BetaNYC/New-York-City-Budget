# `viz/explorer/` — the NYC Council budget explorer

A static, in-browser explorer for the Council's expense funding disclosure and Council capital
data, published at
[betanyc.github.io/New-York-City-Budget/explorer/](https://betanyc.github.io/New-York-City-Budget/explorer/).
Parquet files served as static assets, queried with DuckDB-WASM in the browser. No server, no API.
Design and scope: [`PLAN.md`](PLAN.md). Site-level overview: [`../README.md`](../README.md).

**Same data as the MCP, by construction and by test.** `scripts/build-data.mjs` runs the MCP's own
index build (`mcp/scripts/build-index.mjs`) and copies the index's tables, column for column, into
Parquet (the index file depends on the build: see "Which PDF data a build carries"). It never parses a CSV. `test/parity.test.mjs` then checks, for every fiscal
year, that row counts and dollar totals equal `budget.db`, that every row and column is identical,
and that the explorer's queries (`src/query/sql.js`) answer exactly what the MCP's
(`mcp/src/db.ts`) answer for the same filters. Text search uses the MCP's own fold rule, imported
from `mcp/dist/fold.js`; source-page links and GitHub file links use the MCP's row-link builder,
imported from `mcp/dist/rowlinks.js`.

**PDF tables: checked ones only.** Besides the MCP 2.0 index's spreadsheet tables (`disclosure`,
`disclosure_years`, `capital_council`, `capital_sources`, `capital_vs_omb`, `meta`) and the
`open_data_*` tables, the public build carries every PDF family-year `data/pdf_years.csv` lists as
`reviewed` or `closed` (#190, #213), loaded by the MCP's own loader (`mcp/scripts/pdf-families.mjs`).
Every row says **"checked, review in progress"** (`reviewed`) or **"checked and reviewed"**
(`closed`). The old parser's output (`data/fyNN/schedule_c/` and the like, `data/retired/`) is never
loaded.

## Run it

Node 22.12 or newer. From a fresh clone:

```bash
(cd mcp && npm ci)            # the MCP's dependencies, dist/ and its index
cd viz/explorer
npm ci
npm run data                  # rebuild the index (public build), export Parquet to public/data/
npm test                      # unit tests + parity with budget.db and the MCP
npm run dev                   # http://localhost:5276/
npm run build                 # dist/
node scripts/assemble-site.mjs --out /tmp/site   # the whole Pages site, as deployed
```

`public/data/`, `dist/`, `site/` and `.cache/` are build output and gitignored.

### Which PDF data a build carries

| Command | Index it exports | PDF families | Review tab |
|---|---|---|---|
| `npm run data` (the public deploy, `deploy-viz.yml`) | `.cache/budget-public.db` | `reviewed` and `closed` | no |
| `npm run data -- --include-reviewed` (local review) | `.cache/budget-reviewed.db` | `reviewed` and `closed` | yes |
| `npm run data -- --closed-only` (the gate before #213) | `mcp/data/budget.db` | `closed` only | no |

All three use the MCP's loader and its existing flags (`build-index.mjs --include-reviewed --out`),
so `mcp/data/budget.db`, which the MCP serves, is never written with reviewed rows. The manifest
records `build`, `review_screen`, `withheld` and `dropped_columns`: a public build writes no
`pdf_review_suggestions.parquet` (the reviewers' suggested decisions are for the review screen
only), and its `pdf_review.parquet` leaves out the internal review fields (`check_id`, `severity`,
`dollars`, `expected`, `observed`, `detail`); the note and the decision stay. The review screen's
code is a separate chunk, loaded only when the Review tab opens. `test/parity.test.mjs` checks all
of this against the index. Then
`npm test && npm run build && npx vite preview`. How the data gets here:
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
| Schedule C | Every row of each loaded year's Schedule C (not only the rows paired with the disclosure): search by year, organization, EIN (the row's or its fiscal conduit's), sponsor (member, Speaker or delegation), category, initiative, agency, amount, and where the row stands against the disclosure (Cleared, Pending, not paired; a paired row links to its spreadsheet row). Shows the program or sub-heading, the fiscal conduit, the FY2018–FY2019 `*` mark ("review not completed") and "no dollar amount" where present. Sub-awards (the Jobs to Build On partner lists) are listed under their award and never added to a total. |
| Transparency resolutions | The changes the Council votes after adoption, one row per chart line: search by year, the budget year a chart changes, organization, EIN, member, resolution number (with a list of the year's resolutions), adoption date range and kind of change (money added, taken back, purpose changed, listed with no dollar amount). Every row shows its resolution's number and adoption date; totals by kind of change, with a City agency's own lines (a chart's agency side) totaled on their own lines, never mixed with money to or from organizations; hidden text shown in its own labeled field. |
| Capital book | The book's total is **Part I** only, what the book's own grand total prints (Noel, PR #224). Under it: "of which … went to non-city groups" (the Part I rows the book lists again in Part II), Part II's own printed total, and the rows **printed only in Part II**, listed apart and never added to the Part I total (the "MA" series, labeled with its question to Council Finance and its status, from `data/council_questions.csv`). Every row of each loaded §254 supporting-detail book: search by year, project ID (SUB ID), sponsor, borough, agency, title or description, budget line, part and the book's-year amount. The book's four year columns, negative amounts marked as reductions and counted on their own, "CD nn" sponsors explained (a district with no member), FY2019's council district and description. Each row's NYC Open Data match, keyed on the row's own place where the crosswalk records one (#205); where it records none and the book prints the ID on more than one row (often once in Part I and once in Part II), the match is shown as "matched on project ID only, not to this exact row". A printed dash stays "–". |
| Terms & Conditions | The year's conditions by agency, unit of appropriation or budget line, kind, and text; deadlines after "no later than"; condition 15's FSR table. Each condition's number says whether the book prints it or it is the order in the book (FY2018, FY2021–FY2024 print none, #206). Only when a T&C family is loaded. |
| Review (local review builds only) | The review queue: every flagged row of every loaded PDF family, critical first, then by dollars; filters for family, year, check, severity, open/decided. Each item shows the PDF page with the row highlighted, the parsed values, the review fields and the suggested decision (`data/pdf_review_suggestions.csv`, from each REVIEW.md). Buttons: keep as printed (`accepted_as_printed`), accept suggestion, needs more information (`needs_info`), change to… (`parser_bug`, the value in the note). Decisions stay in the browser (localStorage) and export per family as `review_id,decision,note,decided_by,decided_at`, the Schedule C decisions file's header, to the path shown; import resumes a review. Check a file with `code/validate_review_decisions.py`. |
| Every PDF row | Its status label, its review notes and decision where there are any (the flag badge: in the public build, "N things to check on this row" with each note as one plain sentence for its check, from the MCP's `mcp/src/checkwords.ts`, its decision and any question to Council Finance in plain words (`mcp/src/questions.ts`), and the row's other flags as "How this row was read"; no check ids, severities or reviewers' shorthand; in a review build, the full detail), and three links from the MCP's row-link builder (`mcp/src/rowlinks.ts`): its page in the source view, the PDF on GitHub at the build's commit, and the publisher's copy where known. |
| Source page | Any PDF-derived row opens its PDF page (pdf.js) with the row's `bbox_pt` box highlighted. The PDF is read from GitHub at the build commit, like the spreadsheets; rotated pages (the capital book is `/Rotate 90`) are handled by pdf.js's viewport. The page opens scrolled so the box is in view; a row with no box (transparency charts, capital totals, the Terms FSR table) opens at the top of its page. |

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
| `src/query/pdf.js` | Queries over the PDF tables (the family searches, the §254-to-workbook match, the book rows' Open Data lookup), the row labels, and the box math for the highlight. |
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
