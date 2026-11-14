---
title: "#270 — City agency budgets in the modern explorer and the MCP: review and plan"
created: 2026-11-12
type: plan
status: draft
tags: [agencies, explorer, mcp, open-data, mwzb-yiwb, accessibility, parity, consolidation]
---

# #270 — City agency budgets in the modern explorer and the MCP

Part of epic #272. Review and plan only: nothing here builds the feature. The tests that define it
are on this branch (`tests/270-agency-budgets`), skipped until each part exists. A build session
starts from this branch.

**Workstream issues:** #284 data loader and year rule · #285 MCP tools · #286 explorer view ·
#287 accessibility and phones · #288 parity and retiring the old app · #289 docs.

## 1. Where things stand (2026-11-12, `main` at `919a9b5`)

### The old app, `viz/agencies/`

- Backbone 1.0.0 (2013), jQuery 1.9.1 (2013), Underscore, DataTables, Highcharts **4.0.4 (2014,
  not open source: "License: www.highcharts.com/license")**, Bootstrap, Fuse, spin.js. A fork of
  DataMade's Look at Cook. No build step.
- Loads one file, `data/nyc_budget.csv` (764 rows, one per agency × unit of appropriation, with
  `Adopted YYYY` and `Modified YYYY` for FY2017–FY2027). Sums it in the browser.
- **The CSV has no agency number.** It has `Fund` (agency name), `Department` (unit name) and
  `Department ID` (unit number). Agencies are grouped by name.
- Routes (`js/app.js`): `#(?year=Y)`, `#fund-detail/<agency-slug>(/<unit-slug>)?year=Y`, and
  `#control-officer-detail/...`, which #266 forwards to `fund-detail`. Slugs come from names
  (`BudgetHelpers.convertToSlug`).
- Facts found in this review:
  - **Agency 866 shows under two names** (DEPARTMENT OF CONSUMER AFFAIRS and DEPT OF CONSUMER &
    WORKER PROTECTION). The CSV names each unit by the newest release it is in, and some 866 units
    ended before the rename. So the old app lists 146 "agencies" for 145 agency numbers.
  - **39 unit slugs are shared by two unit numbers** inside one agency (City Council committees
    600/800, City Planning 003/004 "Geographic Systems", and others). An old unit link can't say
    which one.
  - **Old unit links are broken today.** `#fund-detail/police-department/operations` throws
    `TypeError: Cannot read properties of undefined (reading 'get')` and shows an empty table: a
    third route level asks for an `Expense Line` column that this data never had. Agency links work.
  - **$0 hides "not in the budget".** 936 adopted cells are `0` in the CSV because the unit is not
    in that year's release at all (229 more are a real $0). The old app can't tell them apart.
  - **Accessibility baseline** (axe-core 4.14, WCAG 2.2 A/AA tags, run on this branch): the agency
    list has 146 `image-alt` (critical) and 146 `link-name` (serious) violations: the expand
    icons. Tables have no caption and no `th` scope. The Highcharts chart has no role or text
    alternative. `boards.html` (#269) scrolls 15 px sideways at 320 px and has a scrollable region
    a keyboard can't reach (`scrollable-region-focusable`).

### The modern explorer, `viz/explorer/`

- React 19, Vite 7, DuckDB-WASM 1.32 over Parquet, no router: URL-hash state as pure functions
  (`src/state/hash.js`), every view a shareable link. Queries are pure `{ sql, params }` builders
  (`src/query/*.js`), run by DuckDB-WASM in the browser and by `@duckdb/node-api` in tests.
- **One loader by construction:** `scripts/build-data.mjs` runs the MCP's `build-index.mjs`, then
  copies the index's tables into Parquet. It never parses a CSV.
- **No chart library.** Every view is tables and text. Lazy loading per view (`src/duckdb/needs.js`),
  so a first visit downloads only the landing page's tables.
- Tests: Vitest unit tests (pure functions, Node environment), `node --test` parity
  (`test/parity.test.mjs`: Parquet = `budget.db`, and the explorer's queries = the MCP's), and
  lazy-load tests. No browser tests yet.

### The MCP, `mcp/` (`@betanyc/nyc-budget-mcp` 2.0.6)

- TypeScript, `@modelcontextprotocol/sdk`, better-sqlite3. Index built by
  `scripts/build-index.mjs` from structured sources only; every input recorded in `meta.inputs`
  and checked against an allowlist (`test/shipped-data.test.js`). Eight tools; no agency budgets.
- The T&C crosswalk (`data/open_data/crosswalk_terms_unit.csv`) already reads `mwzb-yiwb`, from a
  **different snapshot** (`source/open-data-mwzb-yiwb/`, 2026-10-21) with the year rule fixed in
  #274 / 2.0.6.

### The data, NYC Open Data `mwzb-yiwb`

Two committed snapshots, plus a live pipeline:

| What | Where | Used by |
|---|---|---|
| Live pull | `code/agency_budget_cleanup.py` | writes `viz/agencies/data/nyc_budget.csv` |
| June-release sums by agency × unit, all 11 tags, with agency numbers (2026-11-09) | `source/agency-budget-qa/` | `code/qa_agency_budget.py` (checks every CSV cell) |
| Raw rows for T&C units only (2026-10-21) | `source/open-data-mwzb-yiwb/` | `code/build_open_data_crosswalk.py` |

So the year rule is coded three times today (pipeline, checker, crosswalk). Checked on this branch:
the 2026-11-09 snapshot, under the year rule, gives every one of the 1,373 T&C crosswalk amounts to
the dollar, and every one of the CSV's 16,808 cells.

### CI and the site

- `ci.yml`: MCP build and tests; explorer data, unit and parity tests and build (Node 22 and 24);
  the version guard (a PR touching `mcp/src`, `mcp/scripts` or shipped data needs a version bump).
- `python-checks.yml`: `pytest code` on macOS (includes the agency pipeline and accuracy tests).
- `deploy-viz.yml`: runs `viz/test_pages_site.py`, the agency tests, `qa_agency_budget.py` and the
  explorer tests, then builds and publishes. **This plan never runs it.**
- Workflows start only for PRs whose base is `main`. Stacked PRs need a hand-started run
  (`workflow_dispatch` of `ci.yml` / `python-checks.yml`) on the top branch, as in Phase 1.
- `viz/site_shell.py` writes the shared top bar and footer; `viz/test_pages_site.py` checks every
  page (its tests 7 and 8 describe the Backbone app and change at retirement).

## 2. Decisions, with reasons

### Keep and drop

| Area | Keep | Drop | Why |
|---|---|---|---|
| Framework | React 19 + Vite 7 (the explorer's) | Backbone 1.0, jQuery 1.9, Underscore, Bootstrap 3 JS | One app, one build. jQuery 1.9 has known XSS advisories fixed only in 3.5+. |
| Charts | A small hand-written SVG line chart (two series, 11 points), with a table of the same numbers | Highcharts 4.0.4 | The explorer has no chart library and needs none for two lines. Highcharts 4 is not open source and is 12 years old. The table is the text alternative. |
| Tables | Plain semantic `<table>` with `caption` and `th scope`, sorted by a header button, as the explorer's other views do | DataTables | No dependency; screen readers read real tables. |
| State and URLs | `src/state/hash.js` keys: `view=agencies`, `abfy`, `abag`, `abunit`, `legacy` | Backbone.Router | Same as every explorer view: pure functions, fixed key order, shareable. |
| Old links | `/agencies/` becomes a tiny page that forwards `#fund-detail/...`, `#control-officer-detail/...` and `#?year=` to `../explorer/#view=agencies&legacy=<path>&abfy=Y`; the explorer resolves `legacy` by slug, then replaces it | — | GitHub Pages can't redirect on a `#fragment`; only script in the page can read it. The explorer resolves slugs against every name ever published, so 866's old name still works. |
| Data loading | One `agency_budget` table in the MCP index → Parquet → DuckDB-WASM | The browser summing a CSV | One loader and one query engine (#270's goal). |
| Source for the loader | `source/agency-budget-qa/` (committed, hashed, has agency numbers) | Reading `nyc_budget.csv` | The CSV has no agency number, and its 0s hide absences. The snapshot is structured Open Data with a manifest, which fits `build-index.mjs`'s rules. |
| CSV download | Same address, `agencies/data/nyc_budget.csv`, same columns; after #288 written from the index, and checked equal to today's file | — | People and scripts fetch it by URL. |
| Build | Vite (`npm run build`), `assemble-site.mjs` | — | Already deployed. |
| Test runners | `node:test` (MCP, parity), Vitest (unit), **Playwright + `@axe-core/playwright`** (new, browser), Python `unittest` (site pages) | — | Each is already the runner for that layer, except the browser layer, which did not exist. |

Docs checked for the new libraries (2026-11-12): Playwright
[accessibility testing](https://playwright.dev/docs/accessibility-testing),
[configuration](https://playwright.dev/docs/test-configuration),
[web server](https://playwright.dev/docs/test-webserver),
[emulation](https://playwright.dev/docs/emulation),
[test API](https://playwright.dev/docs/api/class-test); Node
[test runner](https://nodejs.org/api/test.html); Vitest [API](https://vitest.dev/api/). The
`wcag22aa` axe tag was confirmed in the installed axe-core 4.14.0 (`axe.getRules(["wcag22aa"])`
→ `target-size`). Versions added: `@playwright/test` ^1.65.0, `@axe-core/playwright` ^4.14.0.

### The year rule (one place in code)

In a release tagged Y (the June release: the tag's latest `publication_date`, dated June of Y−1):

| Figure | Comes from |
|---|---|
| Adopted FY Y | `financial_plan_amount`, June release tagged **Y** |
| Modified FY Y | `current_modified_budget_amount`, June release tagged **Y+1** |
| Newest year's modified | NULL, "Not yet published", until tag Y+1's June release exists |

`adopted_budget_amount` in release Y is FY **Y−1** (the #274 bug). After #284,
`mcp/scripts/agency-budget.mjs` is the only code that applies the rule for the site and the MCP.
`code/qa_agency_budget.py` stays as the independent check (it imports nothing from the loader), and
the MCP test re-derives every cell with its own code.

### The `agency_budget` table (#284)

```
fiscal_year INTEGER, agency_number TEXT, agency_name TEXT, unit_number TEXT, unit_name TEXT,
adopted REAL, modified REAL, adopted_release TEXT, modified_release TEXT
```

- One row per fiscal year × agency × unit where the unit is in that year's adopted release or the
  next year's (7,611 rows with today's snapshot).
- Numbers are 3-character text. Names are as published in that year's adopted release (or the
  modified release, if the unit is only there).
- `adopted` is NULL when the unit is not in that year's adopted release; `modified` is NULL when it
  is not in the next one, or the next one is not out yet. Never 0 for "absent".
- Releases are `publication_date` (`YYYYMMDD`), so every figure can say where it came from.
- Gross: Open Data rows include intra-city transfers. OMB's headline is net.

### MCP tools (#285)

- `search_agency_budget { agency?, unit?, fiscal_year?, limit? }`: units with adopted and modified,
  the agency total, each figure's release.
- `compare_adopted_modified { agency?, unit?, fiscal_year }`: adopted, modified, change in dollars
  and percent. Agency or unit required.
- `agency` takes a number (`056`, `56`) or words from the name (`police`); `unit` the same.
- Every answer says "gross (includes intra-city transfers)", names `mwzb-yiwb` and the release,
  says "not yet published" or "not in that year's budget" instead of $0.
- **Boundary with `@betanyc/nyc-checkbook-mcp`:** this server answers budgets (adopted, modified).
  Checkbook answers spending, payments and contracts. Both tool descriptions and a README section
  say so; a spending question gets a pointer, not an answer.

### Explorer view (#286)

- Three screens, one view: all agencies for a year → one agency's units → one unit across
  FY2017–FY2027. Adopted and modified side by side, change from the year before.
- The page's `h1` names the half ("City agency budgets"); the Council tabs are not shown on it.
- Labels: "Not yet published" (newest modified), "Not in this year's budget" (absent unit). Never $0.
- A CSV download of what is on screen.
- The test contract: root `[data-view="agencies"]` with `data-ready="true"` once numbers are on
  screen; year picker labeled "Fiscal year"; a polite live region; focus to the new heading.
- Queries in `src/query/agency.js`: `agencyListQuery({ abfy })`, `agencyUnitsQuery({ abfy, abag })`,
  `agencyYearsQuery({ abag, abunit })` (blank = all). Old links in `src/agency/legacy.js`:
  `agencySlug`, `legacyToExplorerHash`, `resolveLegacy`.
- `agency_budget.parquet` loads when the view opens (`needs.js`), not on a first Council visit.

### Accessibility and phones (#287)

WCAG 2.2 AA, checked by machine on every PR:

- **Landmarks and headings:** one `main`, one `h1`, every `nav` named, no skipped heading level.
- **Tables:** `caption`, `th scope="col"` and `scope="row"` (the agency or unit name is the row
  header). Amounts as text, not only as bar widths.
- **Chart:** `svg role="img"` with a name that sums it up ("Adopted and modified, FY2017–FY2027 …"),
  and the "by fiscal year" table right after it. Colors pass 3:1 against the background, and the two
  lines also differ by marker shape and dash, not only by color.
- **Keyboard:** skip link; every control reachable with Tab; links, not click handlers on rows;
  after moving to an agency or unit, focus goes to its heading (`tabindex="-1"`); focus is visible.
- **Announcements:** one polite live region says what is shown after a change ("Showing FY2024,
  Police Department, 18 units"). Loading uses the existing `role="status"`.
- **Phones:** no sideways scrolling at 320 and 375 CSS px (WCAG 1.4.10). Below 600 px, tables become
  stacked rows (each cell labeled with its header), or show one year with a year picker, not a wide
  grid. Touch targets ≥ 24×24 (WCAG 2.5.8), the view's buttons and selects ≥ 44×44 (the shell's rule).
  Text at 200% still fits.
- **First load on a phone:** the explorer downloads the query engine (about 33 MB, cached) before
  the first number. The old page loaded a 150 KB CSV. Show the CSV download and the loading size
  at once; measure on a mid-range phone before retiring the old app (risk 3).

## 3. Tests on this branch

Each test skips, naming its issue, until what it reads exists; then it runs with no edit. Each was
checked against a throwaway prototype (not committed): right implementation passes, a one-year-late
one fails.

| File | Runner | Checks | Runs when |
|---|---|---|---|
| `mcp/test/agency-budget.test.js` | `node --test` | Table and column types; 3-digit text numbers; one row per key; every cell = snapshot under the year rule (re-derived independently); FY2017→newest; NULL not 0 for unpublished and absent; June releases only; OMB's printed FY2025/FY2026 totals and Manhattan CB 1 figures; DOE 040/401 FY2017 = $6,164,926,031 (not the FY2016 figure); 59 boards; every T&C crosswalk amount = `agency_budget` | `agency_budget` is in `budget.db` (#284) |
| `mcp/test/agency-budget-tools.test.js` | `node --test` | Both tools' schemas; OMB figures with releases; `56` = `056`; name search; unit filter; gross and intra-city stated; "not yet published"; "not in that year's budget"; bad years and arguments refused; README boundary section; `list_available_fiscal_years`; no spending figures | the tools are listed (#285) |
| `viz/explorer/test/agency-parity.test.mjs` | `node --test` (`npm run test:agency`, part of `npm test`) | 1. Parquet = `budget.db`, every row and column. 2. Parquet = `nyc_budget.csv`, all 16,808 cells; 936 absent cells counted; names equal; 866's split adds up. 3. The explorer's queries = the old app's citywide, agency and unit totals, every year | Parquet exported (#284); queries module (#286) |
| `viz/explorer/test/unit/agency-hash.test.js` | Vitest | URL keys, zeros kept, round trip, lazy loading | `VIEWS` has `agencies` (#286) |
| `viz/explorer/test/unit/agency-legacy.test.js` | Vitest | Slug rule = the old app's own function (run from its file); every old agency link; 866's old name; 39 shared unit slugs ask, never guess | `src/agency/legacy.js` exists (#286) |
| `viz/explorer/e2e/agencies.a11y.spec.js` | Playwright + axe | axe WCAG 2.2 A/AA on three screens; landmarks; headings; captions and scopes; chart name and table; keyboard path and focus; live region; words not $0; `legacy` resolved | view + data in the built site |
| `viz/explorer/e2e/agencies.mobile.spec.js` | Playwright | No sideways scroll at the phone project's width, 320 and 375; tables on screen; axe `target-size`; 44 px controls; 200% text | same |
| `viz/explorer/e2e/agencies.retired.spec.js` | Playwright | Every old route lands on the same agency and year; shared unit slug asks; no-JavaScript link; CSV address | `/agencies/` no longer loads Backbone (#288) |
| `viz/test_agencies_retired.py` | `unittest` / pytest | Forwarding page loads no old library, forwards all three routes, has a plain link, relative links, keeps the shell; CSV kept; FAQ and boards load no old library; no page says the MCP lacks agency budgets | same |

Run them: `cd mcp && node --test test/agency-budget*.test.js` · `cd viz/explorer && npx vitest run
test/unit/agency-*.test.js && npm run test:agency` · `npm run e2e:site && npx playwright install
chromium && npm run test:e2e` · `python3 -m unittest viz/test_agencies_retired.py`.

Today: MCP 1 pass, 3 suites skipped; Vitest 19 skipped (143 existing pass); parity 3 suites
skipped; Playwright 72 skipped; Python 8 skipped. No existing test changed.

## 4. Stacked PRs

Small, each shippable on its own, each naming its issue. Base `main` unless stated.

| # | Branch | Issue | What | Ships alone because |
|---|---|---|---|---|
| A | `feat/284-agency-loader` | #284 | `mcp/scripts/agency-budget.mjs`; `agency_budget` in `build-index.mjs`; allowlist and `ALLOWED_TABLES` in `shipped-data.test.js`; Parquet export in `build-data.mjs`; add to `parity.test.mjs` TABLES; MCP 2.1.0 bump and CHANGELOG ("Unreleased") | Data only; no screen or tool changes. Unskips `agency-budget.test.js` and parity 1–2 |
| B | `feat/285-agency-tools` (on A) | #285 | The two tools; `list_available_fiscal_years`; `tools.test.js` tool list; `mcp/README.md` boundary section | Unskips `agency-budget-tools.test.js` |
| C | `feat/286-agency-state` (on A) | #286 | `hash.js` keys; `src/agency/legacy.js`; `src/query/agency.js`; `needs.js` entry. No screen yet | Pure functions; unskips both Vitest files and parity 3 |
| D | `feat/286-agency-view` (on C) | #286 | The view: three screens, SVG chart, tables, labels, CSV download, `legacy` resolution | New page beside the old one; nothing removed |
| E | `feat/287-a11y-ci` (on D) | #287 | `e2e` job in `ci.yml` (Chromium only: `npm run e2e:site`, `npx playwright install --with-deps chromium`, `npm run test:e2e`); fixes found | Unskips the a11y and mobile specs |
| F | `feat/288-retire-agencies` (on D + B) | #288 | `/agencies/` forwarding page; old libs moved out of the tree; CSV written from the index (check: equal to today's file); `site_shell.py` menu to the new view; `test_pages_site.py` tests 7–8 updated; `deploy-viz.yml` test step runs `test_agencies_retired.py` (edit only; never run by hand) | Unskips the retirement specs; old links keep working |
| G | `docs/289-agency-docs` (on F) | #289 | README, WHICH-TOOL, `mcp/README.md`, DATA-DICTIONARY, SCHEMA.md, DATA-ANOMALIES §57, `mcp.html`, `about.html`, "last revised" dates | Docs only |
| H (later) | `feat/286-boards-view` | #286 | Community boards as a filter of the view, if Noel agrees (question 2) | Optional |

Merge order: A → B and C (either order) → D → E → F → G. Tag `mcp-v2.1.0` only after B, and only
Noel tags.

### Where #270 links the "What's changed" log

Another session is designing a cross-repo "What's changed" standard. #270 builds no change log page.
When the standard lands, link it from: the Agency budgets view's footer note ("How these figures are
made · What's changed"), the forwarding page at `/agencies/`, `mcp/README.md` next to the
CHANGELOG link, and the 2.1.0 CHANGELOG entry. PR G leaves a marked place for those links.

## 5. Risks

1. **Two snapshots of `mwzb-yiwb` drift.** After a refresh, the agency snapshot and the T&C extract
   can disagree if the City restates a release. The MCP test cross-checks every T&C amount, so a
   drift fails CI; disclose it in DATA-ANOMALIES, never smooth it.
2. **Absent vs $0 is a visible change.** 936 cells move from "$0" to "Not in this year's budget".
   That is more accurate, but readers comparing screenshots will see it. The parity test counts it;
   the forwarding page and FAQ say so.
3. **First load on a phone.** DuckDB-WASM is about 33 MB before the first number, against a 150 KB
   CSV today. Community board staff use phones. Measure before F; if it is too slow, ship a small
   static first screen (the newest year's agency totals, prerendered) and keep the CSV link visible.
4. **Old unit links.** They are broken today; after F they work, except 39 that are ambiguous by
   name. Those ask the reader to pick, never guess.
5. **Year rollover.** In June 2027 the FY2028 release adds a year. The checker and the pinned June
   releases fail on purpose until a person updates them (#268). The loader must pick the year range
   from the data, not hard-code 2027.
6. **Stacked PRs and CI.** Workflows run only on PRs to `main`; start `ci.yml` and
   `python-checks.yml` by hand on the top branch. Never start `deploy-viz.yml`,
   `pdf-tables-release.yml` or `publish-mcp.yml`.
7. **Version guard.** A touches `mcp/scripts`, so it carries the 2.1.0 bump. B to G stay on 2.1.0
   until Noel tags.
8. **Playwright in CI.** Browsers download (`npx playwright install --with-deps chromium`) on each
   run; cache them, and keep the job to Chromium so the phone project needs no WebKit.

## 6. Open questions for Noel

1. **Absent units:** show "Not in this year's budget" (recommended) instead of $0, in the view, the
   MCP and the CSV? (The CSV keeps 0 unless you say otherwise, so downloads don't change shape.)
2. **Community boards (#269):** keep `agencies/boards.html` as is after retirement, or make it a
   filter of the new view (PR H)?
3. **CSV column names:** keep `Fund` / `Department` in the download (recommended until a major
   release), or rename to `Agency` / `Unit of appropriation`? (Morning report question 4.)
4. **Pipeline:** after F, retire `code/agency_budget_cleanup.py`'s own year logic, so the refresh is
   `fetch_agency_budget_qa.py` → index → CSV? Recommended: yes, keep `qa_agency_budget.py` as the
   independent check.
5. **URL:** the view lives at `explorer/#view=agencies`. Is that acceptable until the `/council/`
   rename (#264), or do you want a separate entry page?
6. **Release:** OK to ship the table and tools as MCP 2.1.0 (minor), tagged by you after PR B?

## 7. Done when

- [ ] `agency_budget` is in the MCP index and the Parquet, built by one module (#284)
- [ ] `search_agency_budget` and `compare_adopted_modified` answer with releases, gross, and no $0 for missing (#285)
- [ ] `mcp/README.md` states the boundary with `@betanyc/nyc-checkbook-mcp` (#285)
- [ ] The Agency budgets view shows all agencies, an agency, and a unit, FY2017–FY2027 (#286)
- [ ] axe finds no WCAG 2.2 A/AA violation; no sideways scroll at 320 px; checks run in CI (#287)
- [ ] Parity: all 16,808 cells equal `/agencies/`, with the counted differences only (#288)
- [ ] `/agencies/` forwards every old link; the CSV keeps its address; the old libraries are gone (#288)
- [ ] Docs updated; nothing says agency budgets are missing from the MCP (#289)
- [ ] `grep -rn "PENDING #28[4-9]" mcp/test viz` finds only skip reasons that no longer trigger: every #270 test runs, none skipped
- [ ] Noel has tagged the MCP release
