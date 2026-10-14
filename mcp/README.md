# @betanyc/nyc-budget-mcp — NYC Budget MCP server

A Model Context Protocol (MCP) server for NYC Council budget data, **built only from structured
sources**: the Council's own expense funding disclosure spreadsheets and its capital
designations (the Council's capital workbooks and NYC Open Data), plus a by-budget-line
comparison with OMB's adopted capital budget. Nothing in it was extracted from a PDF.

> **2.0.0 is a breaking release.** The five tools built on data extracted from the
> adopted-budget PDFs (Schedule C, Terms & Conditions, §254 capital, transparency resolutions)
> and `get_legistar_link` are removed. See [Migrating from 1.x](#migrating-from-1x) and
> [`CHANGELOG.md`](CHANGELOG.md). The retired data stays in the repository for history; it is
> not in the package.

Published on npm as [`@betanyc/nyc-budget-mcp`](https://www.npmjs.com/package/@betanyc/nyc-budget-mcp) and run via `npx`. The package ships a prebuilt SQLite index, so no clone, build or data checkout is needed to run it.

## Quick start (npx)

Add this to your MCP client config (Claude Desktop, Claude Code, etc.):

```json
"mcpServers": {
  "nyc-budget": {
    "command": "npx",
    "args": ["-y", "@betanyc/nyc-budget-mcp@2"]
  }
}
```

Restart the client; the four `nyc-budget` tools become available. `@2` keeps you on 2.x. A
config that names no version follows npm's `latest` tag; one pinned to `@1` stays on the retired
PDF-derived data.

## Data scope (read this first)

| Dataset | Years | Source | Notes |
|---|---|---|---|
| Expense funding **disclosure** | **FY2009, FY2011–FY2027** (156,544 rows) | The Council's own award-level workbooks: FY2013–FY2027 downloaded from the Council RnD site on 2026-10-12, FY2009, FY2011 and FY2012 from the Council's archived workbooks via the Internet Archive (retrieved 2026-10-14) | **FY2010 is not included**: the Council's workbook (2,592 rows) is incomplete against NYC Open Data's (5,981 rows), and the two are never mixed. **FY2009 and FY2013 are early snapshots**, frozen while much was Pending and never revised: their Cleared totals are not headline figures. Per-year provenance: [`../data/disclosure_years.csv`](../data/disclosure_years.csv) |
| Council **capital** designations | **FY2015–FY2017, FY2019–FY2027** (16,916 rows) | The Council's capital workbooks (FY2015–FY2017 and FY2026 via the Internet Archive, FY2027 from the RnD site) and NYC Open Data `t474-a92g`, which the Council publishes (FY2019–FY2025) | **FY2018 is missing** from every source found. Exact by budget line only: Council project IDs do not link to OMB, FMS or Checkbook, and there is no contract-level data. Overview: [`../data/capital/README.md`](../data/capital/README.md) |
| Council vs **OMB** adopted capital budget | **FY2019–FY2027** (1,425 budget lines) | This repo's arithmetic on the capital table and OMB's `46m8-77gv` adopted release | Not a Council or OMB reconciliation. [`../data/capital/RECONCILIATION.md`](../data/capital/RECONCILIATION.md) §3 |

`list_available_fiscal_years` reports this per year, with every gap stated.

## Tools

| Tool | Purpose |
|---|---|
| `search_disclosure_awards` | The Council's expense funding disclosure by fiscal year / EIN / legal name / council member (substring) or **`council_member_id`** (exact Legistar person ID: `Levin` 7567 and `Levine` 7634 never blend) / source (substring) or **`source_exact`** / agency / program / grantee **`zip`** (exact 5-digit) / **`zip_status`** / **`city`** (exact) / status / **`mocs_id`** / **`od_mocs_id`** / amount range. Each row shows the grantee's mailing address as printed, its derived zip and zip_status, and, FY2009–FY2021, the MOCS ID NYC Open Data gives the same designation where the pairing is unambiguous. Reports the true match count, Cleared and Pending totals over **all** matches, the source and retrieval date of each year, the early-snapshot years and FY2010's exclusion |
| `search_council_capital` | The Council's capital designations by fiscal year (the list's year) / `amount_fy` / **`budget_line`** (exact, `P D018`) / **`project_id`** (exact) / sponsor (substring) or `sponsor_exact` / `borough` (exact code) / `council_district` (workbook years only) / title / description / amount range. Totals the list's own year separately from out-year amounts; names the file, retrieval date and sha256 of every year it draws on |
| `compare_capital_to_omb` | For each report year and Council-series budget line, the Council table's total vs OMB's adopted release, this year and next, with a verdict (`match`, `differ`, `council_only`, `omb_only`). Lines that disagree first |
| `list_available_fiscal_years` | What each fiscal year holds in each dataset and where it came from; FY2010 (disclosure) and FY2018 (capital) stated as gaps |

### Unknown parameters are rejected, not ignored

Every tool declares `additionalProperties: false` and validates its arguments against a strict
schema. A parameter that is not in the tool's schema raises an error naming the accepted
parameters, with a hint where the guess is a common one (`council_district` on the disclosure
points at `council_member` / `council_member_id`; `council_member` on capital points at
`sponsor`). Silently dropping an unknown filter returns real data answering a different
question (issue #37).

### `search_disclosure_awards`

The disclosure is the Council's own, later, award-level list: it includes designations made
after adoption, and `council_member` is the roster when the workbook was exported. Every
response carries:

- the **true number of matching rows** and the totals over all of them, whatever `limit` shows
  (default 50, max 500, highest amount first); a short page says "Showing N of M";
- **Cleared** and **Pending** totals separately, plus an all-statuses line labeled as not a
  headline figure. Cleared is the headline, except when every matched year is an **early
  snapshot** (FY2009, FY2013): then it is labeled "early snapshot, not a headline", and a total
  that mixes early and ordinary years says so and marks them in the per-year split;
- the **source of each fiscal year** it draws on: file, sheet (the Council stamps its own
  "last updated" date there), retrieval date, sha256 prefix, and the Council RnD URL or the
  Internet Archive capture it came from;
- a **coverage line**: the years served, that FY2010 is not included, and which years are early
  snapshots. Asking for `fiscal_year: 2010` returns the recorded reason, not an empty search;
- notes when the match includes **exact copies** (`duplicate_group`), rows with a recorded
  **`row_flag`** (`not_an_award`: two FY2009 lump allocations on the City's own EIN, kept and
  counted as published), or rows that **print no grantee EIN** (FY2009's largest is "School
  Budget Restoration", $120,000,000);
- each row's grantee **mailing address** as printed, with the 5-digit `zip` derived from it and
  its `zip_status` (rules in [`../DATA-DICTIONARY.md`](../DATA-DICTIONARY.md)). It is where the
  grantee gets mail, **not where services were delivered**.

**Address filters.** `zip` is exact and 5 digits only: it matches the derived zip, so the
`11203-` rows (zip `11203`, `trimmed`) and a Brookline `2446` (zip `02446`, `padded`) are found
under their ZIP; a ZIP+4 or a 4-digit value is an error, never trimmed or padded by the tool.
Rows whose `zip_status` is `ambiguous_extra_digit`, `invalid` or `blank` have no zip and never
match. `city` is exact, ignoring case and surrounding whitespace; it is not a borough filter.

**The fiscal-sponsor caveat.** One EIN can pool many bodies: `13-2612524` (Fund for the City of
New York) is a fiscal sponsor for dozens of programs, and `136400434` (the City of New York)
covers hundreds of City agencies, schools and programs. The answer counts the distinct legal
names an EIN matched; narrow with `legal_name` or `program_name`.

Example — `search_disclosure_awards({ ein: "13-3179546", fiscal_year: 2026, limit: 1 })` (Food Bank For New York City), abridged:

```text
254 matching designation(s) in the Council's expense funding disclosure. Showing 1 of 254, highest amount first — the totals below cover all 254. …

Totals over all 254 match(es):
  Cleared (headline): 254 row(s), $5,298,821
  Pending:            0 row(s), $0
  All statuses (not a headline figure): 254 row(s), $5,298,821

Snapshot (which download each year comes from):
  FY2026: funded_disclosure_FY2026.xlsx, sheet "FY26 (09-14-26)", retrieved 2026-10-12 (sha256 81651e599ad6), from the Council RnD site, https://rnd.council.nyc.gov/src/assets/excelFund/funded_disclosure_FY2026.xlsx

Coverage: FY2009, FY2011–FY2027. FY2010 is NOT included (…). Early snapshots, whose Cleared totals are not headline figures: FY2009, FY2013.

Rows:
FY2026 · FY26 08060 · $1,000,000 · Cleared · (no member) → Food Bank For New York City (EIN 133179546) · source: Food Pantries · agency: DYCD
    program: School Pantries
    grantee mailing address: 39 Broadway, 10th Flr, New York, NY 10006 · zip 10006 (valid: a 2020 Census ZCTA)
    workbook row 7688
…
```

### `search_council_capital`

One row per (record, fiscal-year amount): a workbook lists the report year and out-years in
columns and t474 lists out-years as rows; both become one row per amount, with the year it is
for in `amount_fy`. `fiscal_year` selects the Council's list for that year; totals report the
list's own year (`amount_fy` = the list's year) and **out-year amounts separately**, never
added together. Rows with no amount (five t474 records broken across rows, four of them in the
served years, `split_record_amount_unknown`) are counted and kept out of every total.

- **`budget_line`** is exact, in the form agency code, space or `-`, line (`P D018`,
  `PW-DN846`); `PD018` is refused because where the agency code ends cannot be told. It is the
  only key shared with OMB.
- **`project_id`** is the Council's own ID, unique within one year only, and not an FMS or
  Checkbook project ID. FY2015 prints none; FY2016 prints no budget lines.
- **`sponsor`** is the surname or body as printed, with no Legistar ID attached; one surname
  can be different members in different years. A substring filter lists every value it matched
  (co-sponsored rows such as `Speaker, Rivera` included); `sponsor_exact` takes one value.
- **`council_district`** matches a district inside the Council workbook's printed list
  (FY2015–FY2017, FY2026, FY2027). It never matches a t474 row: NYC Open Data stored that column
  as a number, collapsing lists such as "22, 25, 29" into one integer.
- **`borough`** is the printed code, case-sensitive: FY2016's lower-case `k` and `x` are not
  folded into `K` and `X`, and `A` is kept. Their meaning is unconfirmed.
- Every answer names each year's source file, its retrieval date and sha256 (hashed at index
  build and checked against the source folder's manifest), and states the caveats: FY2018
  missing, codes `A`, `80`, `CC` and `PN` unconfirmed, no project- or contract-level links.

### `compare_capital_to_omb`

BetaNYC's arithmetic, not a Council or OMB reconciliation: for each report year it sums the
Council table by budget line for that year and the next, and compares OMB's adopted release for
that first fiscal year (the last release of the year, published in July), summed over funding
sources, Council-series lines only. `match` means the line's totals are equal to the dollar in
both years; it does not show that the projects under the line are the same. A line absent from
one side shows `—` there, never `$0`.

## Migrating from 1.x

| 1.x tool | In 2.0.0 |
|---|---|
| `search_awards` | `search_disclosure_awards` (`legal_name`, `program_name`, `council_member` / `council_member_id`, `fiscal_year`, `ein`) |
| `get_awards_by_ein` | `search_disclosure_awards` with `ein`; its totals and per-year split cover every match |
| `search_capital_projects` | `search_council_capital` |
| `search_transparency_resolutions` | Removed, no replacement yet. Post-adoption designations appear in the disclosure as rows, without a resolution number |
| `get_terms_conditions` | Removed, no replacement yet |
| `get_legistar_link` | Removed. Its crosswalk indexed the PDF documents 2.0 no longer serves, and several rows were researchers' candidates rather than verified links. For a resolution's Legistar record, use [`nyc-council-mcp`](https://github.com/BetaNYC/nyc-council-mcp) |
| `list_available_fiscal_years` | Kept, rebuilt: per year, which structured datasets exist and where they came from |

Calling a removed tool returns an error naming its replacement. Figures published from 1.x
(adopted Schedule C, §254) are a different source and will not reproduce against 2.0.

## Architecture

TypeScript + the MCP SDK + zod over stdio, on a local SQLite index (no live upstream API).

- **The parent repo's structured datasets** are the single source of truth: `../data/disclosure_years.csv`, `../data/fyNN/expense_disclosure/`, `../data/capital/`, and the `MANIFEST.csv` of each source folder whose files they cite.
- **`scripts/build-index.mjs`** reads only those files and builds `mcp/data/budget.db` (git-ignored) with `better-sqlite3`. It records every file it read in the index's `meta.inputs`, stops on any value outside a documented vocabulary (a status, a flag, a row count that disagrees with `disclosure_years.csv`, a capital source whose sha256 differs from its manifest), and is idempotent: the `.db` is dropped and rebuilt each run.
- **`src/db.ts`** opens the index read-only and runs one query per tool; totals come from SQL over every match, never from the page.
- **`src/server.ts`** holds the tool definitions, strict zod validation, the migration notes for removed tools, and the response text.

## Build & run

From inside `mcp/`:

```bash
npm install          # runs prepare → build + build-index
npm start            # launch the MCP server over stdio
npm run build-index  # rebuild mcp/data/budget.db from the repo's datasets
npm test             # build + build-index + run the tests
```

`mcp/data/budget.db` is a build artifact (git-ignored); the npm `files` allowlist ships it,
freshly built by `prepare` at publish time.

## Run from source (development)

1. Build and index once: `npm install` (or `npm run build && npm run build-index`) inside `mcp/`.
2. Point your client at the built entry with an absolute path:
   ```json
   "mcpServers": {
     "nyc-budget": {
       "command": "node",
       "args": ["/ABSOLUTE/PATH/TO/New-York-City-Budget/mcp/dist/index.js"]
     }
   }
   ```
   The server finds `budget.db` from its own location, so no `cwd` is needed.
3. Restart the client. After any data or code change, re-run `npm run build && npm run build-index`.

## Tests

Every expected value is computed from the committed CSVs, manifests and source files, never
from the index under test, and each test states what result would make it fail. The 2.0.0
tests were mutation-checked (see `CHANGELOG.md`).

| File | What it holds the server to |
|---|---|
| `test/no-pdf-data.test.js` | The index has only the structured tables; every file the build read is on a structured allowlist and none is PDF-derived; `npm pack` would ship exactly six files (code, README, package.json, the index) |
| `test/tools.test.js` | Exactly four tools listed; every removed 1.x tool answers with its migration note; `list_available_fiscal_years` matches the datasets year by year |
| `test/disclosure.test.js` | Every row of every year indexed with its provenance; FY2010 not loaded; true counts and Cleared / Pending totals under any `limit`; ordering; status, amount, address and member filters; caveat and footer; strict-schema hints |
| `test/disclosure-audit.test.js` | The audit questions (`../data/DISCLOSURE-AUDIT.md`, M1–M13): exact-to-the-cent totals for every year × status, truncation, sort before limit, limit edges, EIN rules, literal wildcards, multi-value notices, address filters, and the EIN-less note |
| `test/disclosure-v2.test.js` | FY2009, FY2011, FY2012 with `od_mocs_id`, `od_match`, `row_flag`; early-snapshot labeling; the coverage line; FY2010's reason; exact `mocs_id` / `od_mocs_id`; the `row_flag` note |
| `test/capital.test.js` | Every capital row and its provenance (sha256 recomputed from the committed file); own-year vs out-year totals; ordering; split records; every filter's exactness; FY2018; caveats; and `compare_capital_to_omb` verdict counts, figures and ordering |
| `test/strict-schema.test.js` | Issue #37: every tool advertises and enforces `additionalProperties: false`, with per-tool hints |

The 1.x tests and the Legistar enrichment script are parked in `retired-1.x/` (not run, not
shipped) until a maintainer deletes them.

## Releases

Published to npm by CI, never from a laptop:

- **Version bump lands in a PR**: a semver bump in `mcp/package.json` plus a `CHANGELOG.md`
  entry, reviewed and merged to `main`. The CI `version-guard` job fails a PR that changes
  shipped code or shipped data without a version that is new to npm.
- **Publishing is tag-triggered.** `.github/workflows/release.yml` fires on a pushed
  **`mcp-v*`** tag whose version matches `mcp/package.json`; it installs, tests, and runs
  `npm publish --provenance --access public` from `mcp/`, then cuts a GitHub Release.
- **To release** after the version-bump PR merges: `git tag mcp-v<version>` and
  `git push origin mcp-v<version>`.
- **CI**: `.github/workflows/ci.yml` builds and tests `mcp/` on Node 20 and 22 for every PR into
  `main` that touches `mcp/` or the data the index is built from.

## About BetaNYC

This project is built and maintained by [BetaNYC](https://beta.nyc), New York's
civic technology and open-data community. We work to improve lives in New York
through civic design, technology, data, and public-interest technology.

**Come do civic tech with us.** We run public events, meetups, and hands-on
data classes throughout the year — including [NYC School of Data](https://www.schoolofdata.nyc/)
and [CityCamp NYC](https://citycamp.nyc), and we host frequent civic-tech gatherings. See what's coming up on our
[events calendar](https://www.beta.nyc/events/).

**Sustain this work.** These MCP servers are free and open source. To help keep this work going and find BetaNYC's
tools, please consider [donating and becoming a Beta
Builder](https://beta.nyc/donate).

## Building on this? Tell us!

If you build something with this project, we'd love to hear about it. We can help other New Yorkers find it. BetaNYC publishes a weekly newsletter,
*This Week in NYC's Civic Technology and Open Data*.

- **[Subscribe to the newsletter](https://beta.nyc/newsletter)** to keep up with
  NYC civic tech, open data, and public-interest technology.
- **Built something, or found a story worth sharing?** [Submit a link for the
  newsletter](https://www.beta.nyc/newsletter-inbox/) and we'll consider it for
  an upcoming issue.

## Related BetaNYC MCP servers

BetaNYC maintains a suite of open-source MCP servers for NYC and NYS civic data.
See the full directory, with install details for each, at
**[beta.nyc/ai-tools](https://beta.nyc/ai-tools)**.

This server pairs directly with:

- **[nyc-checkbook-mcp](https://github.com/BetaNYC/nyc-checkbook-mcp)**: look up an organization's contracts, payments and spending in Checkbook by EIN or name, alongside its Council designations here.
- **[nyc-council-mcp](https://github.com/BetaNYC/nyc-council-mcp)**: the Council's legislation, sponsors and votes from Legistar, including the resolutions that adopt and modify the budget. (This server's 1.x `get_legistar_link` is retired; see the migration table.)

> **Working with the wider NYC Open Data portal?** NYC Open Data hosts a related
> (now-frozen) Council Discretionary Funding dataset this repo supersedes. To search
> the full catalog or run ad-hoc SoQL queries across other datasets, pair it with
> [socrata-mcp-server](https://github.com/npstorey/socrata-mcp-server)
> (`socrata-mcp-server` on npm), a third-party MCP by [Nathan Storey](https://github.com/npstorey).

## Cross-MCP example journeys

Join keys, ordered by reliability: **EIN** (org-level, exact, but pools fiscal-sponsor
programs) › **MOCS ID** (FY2024+ in the Council's workbook; FY2009–FY2021 from NYC Open Data as
`od_mocs_id`; *unverified as a contract key and not stable across disclosure snapshots*) ›
**budget line** (capital, shared with OMB) › **organization name** (display only; never join on it).

### 1. Follow an organization's money — EIN → `nyc-checkbook-mcp` + IRS 990
- **Chain:** `search_disclosure_awards({ ein })` → `nyc-checkbook-mcp` `search_spending` / `search_contracts` → IRS Form 990 by EIN ([ProPublica Nonprofit Explorer](https://projects.propublica.org/nonprofits/)).
- **Caveat:** narrow fiscal-sponsor EINs by `legal_name` or `program_name`; in Checkbook, search the registered payee name, which may be the sponsor's.

### 2. Did this designation become a registered contract? — MOCS ID → `nyc-checkbook-mcp`
- **Chain:** `search_disclosure_awards({ mocs_id })` → `nyc-checkbook-mcp` `search_contracts` / `get_contract`.
- **Caveat to verify first:** the disclosure's MOCS ID is a MOCS registration identifier; Checkbook keys contracts by its own FMS `contract_id`. Confirm the mapping on a known example before treating them as one key. A MOCS ID is not fixed across snapshots: the 2026-10-12 FY2026 workbook carries 131 designations as `FY26GP NNNNN` that read `FY26 NNNNN` in July.

### 3. From a capital budget line to OMB and Checkbook
- **Chain:** `search_council_capital({ budget_line })` → `compare_capital_to_omb({ budget_line })` → `nyc-checkbook-mcp` by budget line or agency.
- **Caveat:** a Council project ID links to nothing outside the Council's list. Only the budget line is shared, so anything below the line is a match by line and title, not a join.

### 4. The resolution behind a designation — `nyc-council-mcp`
- Initiatives adopt and change through the Committee on Finance's periodic omnibus resolutions ("MODIFICATION (MN-N)…"). Search `nyc-council-mcp` by `committee=Finance` and `modification`, not by an initiative's name.

## Provenance & licensing

This server reads the repo's own structured datasets. Provenance and licensing are covered by
the [repository README](../README.md#license): the code is MIT ([`LICENSE`](../LICENSE)); the
data is under the terms that section and [`LICENSE-DATA`](../LICENSE-DATA) give. The Council's
workbooks are © The City of New York, reproduced as public records; NYC Open Data rows are
covered by the [NYC Open Data Terms of Use](https://opendata.cityofnewyork.us/overview/#termsofuse).
