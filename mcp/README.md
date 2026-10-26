# @betanyc/nyc-budget-mcp — NYC Budget MCP server

A Model Context Protocol (MCP) server for NYC Council budget data. The package itself is
**built only from structured sources**: the Council's own expense funding disclosure spreadsheets
and its capital designations (the Council's capital workbooks and NYC Open Data), plus a
by-budget-line comparison with OMB's adopted capital budget.

Four more tools answer from the **checked tables BetaNYC reads from the Council's budget PDFs**
(Schedule C, transparency resolutions, the capital book, Terms and Conditions; FY2018 on). Those
tables are an **optional download** (about 17 MB; 115 MB on disk), not part of the package: see
[The checked PDF tables](#the-checked-pdf-tables-optional-download).

> **Version 2.0.4** (2026-10-25). 2.0.2 (2026-10-23) added the four PDF tools and the optional
> download; nothing was removed. 2.0.3 matched capital IDs in full, and 2.0.4 makes short
> text-filter terms match whole words (`whole_word`). The downloader always takes the newest data release
> ([releases page](https://github.com/BetaNYC/New-York-City-Budget/releases)). As of 2026-10-24 that is
> [`pdf-tables-2026-10-24-260d16e`](https://github.com/BetaNYC/New-York-City-Budget/releases/tag/pdf-tables-2026-10-24-260d16e): 36 checked family-years, FY2018–FY2027 (17.4 MB of tables), and, with `--pdfs`, the
> 126 PDFs they cite (148 MB). The first was `pdf-tables-2026-10-23-5bab77c`.
>
> **2.0.0 was a breaking release.** It removed the five tools built on the old PDF parser's
> output (Schedule C, Terms & Conditions, §254 capital, transparency resolutions) and
> `get_legistar_link`. The four PDF tools in 2.0.2 read the new, checked tables, not that output.
> See [Migrating from 1.x](#migrating-from-1x) and [`CHANGELOG.md`](CHANGELOG.md).

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

Restart the client; the eight `nyc-budget` tools become available. The four PDF tools answer
with how to add their tables until you download them:

```json
"mcpServers": {
  "nyc-budget": {
    "command": "npx",
    "args": ["-y", "@betanyc/nyc-budget-mcp@2"],
    "env": { "NYC_BUDGET_PDF_DATA": "on" }
  }
}
```

or, once, in a terminal: `npx @betanyc/nyc-budget-mcp download --pdf-tables` (add `--pdfs` for
the PDF files too). `@2` keeps you on 2.x. A
config that names no version follows npm's `latest` tag; one pinned to `@1` stays on the retired
PDF-derived data.

## Data scope (read this first)

| Dataset | Years | Source | Notes |
|---|---|---|---|
| Expense funding **disclosure** | **FY2009, FY2011–FY2027** (156,544 rows) | The Council's own award-level workbooks: FY2013–FY2027 downloaded from the Council RnD site on 2026-10-12, FY2009, FY2011 and FY2012 from the Council's archived workbooks via the Internet Archive (retrieved 2026-10-14) | **FY2010 is not included**: the Council's workbook (2,592 rows) is incomplete against NYC Open Data's (5,981 rows), and the two are never mixed. **FY2009 and FY2013 are early snapshots**, frozen while much was Pending and never revised: their Cleared totals are not headline figures. Per-year provenance: [`../data/disclosure_years.csv`](../data/disclosure_years.csv) |
| Council **capital** designations | **FY2015–FY2017, FY2019–FY2027** (16,916 rows) | The Council's capital workbooks (FY2015–FY2017 and FY2026 via the Internet Archive, FY2027 from the RnD site) and NYC Open Data `t474-a92g`, which the Council publishes (FY2019–FY2025) | **FY2018 is missing** from every source found. Exact by budget line only: Council project IDs do not link to OMB, FMS or Checkbook, and there is no contract-level data. Overview: [`../data/capital/README.md`](../data/capital/README.md) |
| **Checked PDF tables** (optional download) | Schedule C FY2018–FY2027 · transparency resolutions FY2018–FY2026 · capital book FY2018–FY2020, FY2022–FY2027 · Terms and Conditions FY2018, FY2021–FY2027 | Read by BetaNYC from the Council's PDFs (`../source/FYNN/`) and checked (`../PDF-RECIPE.md`); statuses in [`../data/pdf_years.csv`](../data/pdf_years.csv) | As of 2026-10-24 every family-year is `reviewed` ("checked, review in progress"); none is `closed` ("checked and reviewed") yet. FY2008–FY2017 were read only by the old parser and are not served |
| Council vs **OMB** adopted capital budget | **FY2019–FY2027** (1,425 line-year comparisons, 515 distinct budget lines) | This repo's arithmetic on the capital table and OMB's `46m8-77gv` adopted release | Not a Council or OMB reconciliation. [`../data/capital/RECONCILIATION.md`](../data/capital/RECONCILIATION.md) §3 |

`list_available_fiscal_years` reports this per year, with every gap stated.

**In a browser:** the [budget explorer](https://betanyc.github.io/New-York-City-Budget/explorer/)
([`../viz/explorer/`](../viz/explorer/README.md)) is built from this server's own index
(`scripts/build-index.mjs` → `data/budget.db` → Parquet), and a parity test in CI checks that the
two agree year by year. A change to the index build reaches the explorer on its next deploy.

## Tools

| Tool | Purpose |
|---|---|
| `search_disclosure_awards` | The Council's expense funding disclosure by fiscal year / EIN / legal name / council member (substring) or **`council_member_id`** (exact Legistar person ID: `Levin` 7567 and `Levine` 7634 never blend) / source (substring) or **`source_exact`** / agency / program / grantee **`zip`** (exact 5-digit) / **`zip_status`** / **`city`** (exact) / status / **`mocs_id`** / **`od_mocs_id`** / amount range. Each row shows the grantee's mailing address as printed, its derived zip and zip_status, and, FY2009–FY2021, the MOCS ID NYC Open Data gives the same designation where the pairing is unambiguous. Reports the true match count, Cleared and Pending totals over **all** matches, the source and retrieval date of each year, the early-snapshot years and FY2010's exclusion |
| `search_council_capital` | The Council's capital designations by fiscal year (the list's year) / `amount_fy` / **`budget_line`** (exact, `P D018`) / **`project_id`** (exact) / sponsor (substring) or `sponsor_exact` / `borough` (exact code) / `council_district` (workbook years only) / title / description / amount range. Totals the list's own year separately from out-year amounts; names the file, retrieval date and sha256 of every year it draws on |
| `compare_capital_to_omb` | For each report year and Council-series budget line, the Council table's total vs OMB's adopted release, this year and next, with a verdict (`match`, `differ`, `council_only`, `omb_only`). Lines that disagree first |
| `search_schedule_c_awards` | The adopted budget's Schedule C as printed, by fiscal year / organization / EIN (the organization's or its fiscal conduit's) / member, sponsor or delegation / category / initiative / agency / purpose / `disclosure_status` / amount range. Each row says whether the same EIN and amount is in the disclosure spreadsheet (cleared, pending or unmatched, with the reason). Sub-awards listed under their award, never counted. PDF tables |
| `search_transparency_changes` | The transparency resolutions: designations, rescissions and purpose-of-funds changes after adoption, by fiscal year / budget year / organization / EIN / member / `resolution_number` / `resolution_date` or a `date_from`–`date_to` range / action, newest first. Totals per kind of change; "no dollar amount" rows counted, never summed. PDF tables |
| `search_capital_book` | The §254 supporting detail (Parts I and II) by fiscal year / `project_id` / `budget_line` / sponsor / borough / agency / title / part / amount range, in book order. The total is Part I's (it ties to the book's printed total); "of which … went to non-city groups" is the Part I rows the book lists again in Part II (the same year, SUB ID and budget line, as the explorer); rows printed only in Part II are listed apart and never added, and only the year's Part II series among them ("MA" IDs on "0N" lines; FY2026 "MM"; from `config/capital_sd/fyYYYY.toml`) is labeled with its question to Council Finance and that question's status (`data/council_questions.csv`). Reductions counted on their own; "CD nn" sponsors labeled as districts with no member; borough "A" and "C" shown as printed, "not a borough, meaning unclear" (question to the Council: #227, with its status), and matched as printed by a borough filter. PDF tables |
| `search_terms_conditions` | Terms and Conditions by fiscal year / agency / unit of appropriation / text, the same filters as the explorer's Terms view. PDF tables |
| `list_available_fiscal_years` | What each fiscal year holds in each dataset and where it came from; FY2010 (disclosure) and FY2018 (capital) stated as gaps; each PDF family-year's status, and whether the PDF tables are installed |

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
  **`row_flag`**: `not_an_award` (two FY2009 lump allocations on the City's own EIN, kept and
  counted as published) or `no_grantee_ein` (the 53 rows that print no grantee EIN, each shown
  with "No grantee EIN printed by the Council. Often a city program rather than a nonprofit.",
  plus a note with their matched count and dollars);
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
one side shows `—` there, never `$0`. Counts are line-year comparisons (1,425 over 515 distinct
budget lines, FY2019–FY2027). A Council row on a line outside the Council series is not compared
and the answer lists it (one today: FY2021 `PW MN02A`, $304,000).

### Behavior common to the searches

- **Text filters fold before they match**, on the query and on the data: case, accents, curly
  quotes and dashes do not matter (`Women's` finds `Women’s`; `Jewish Emigre` and `Jewish
  Émigré` find the same 6 rows). `%` and `_` are literal.
- **Short terms match whole words** (#259). A term of 3 or fewer letters and digits, after
  trimming, matches only where it is not inside a longer word: the characters just before and
  just after it (once folded) are not letters or digits. `AI` finds "AI Training Program",
  "(AI)", "AI-powered" and "BetaNYC's AI", but not "Jamaica" or "AIDS"; `DOE` finds "DOE's".
  A longer term stays a substring, so `Fellow` still finds "Fellowship" and `BetaNYC` still
  finds "BetaNYC's". A term with no letter or digit (`%`, `_`) stays a substring. Every tool with
  a text filter takes **`whole_word`**, which overrides the default for all its name and prose
  filters in that call: `false` to find a short term inside words (`AI` inside `AIDS`), `true` to keep a
  longer word from matching longer ones (`Fellow` but not `Fellowship`). When any filter matched
  as whole words, the answer's second line names it and says how to get a substring instead.
  Folding is the same either way, the matching runs in SQL so the totals cover exactly the rows
  matched, and exact filters (EIN, IDs, budget line, codes, city, zip) are not affected.
  Identifier filters that match substrings, the capital book's `project_id` and the transparency
  `resolution_number`, always stay substrings: an ID fragment such as `CC1` or `101` finds every
  ID containing it, whatever its length and whatever `whole_word` says. The
  explorer's search is still a substring.
- **A blank text filter is an error**, never "no filter": `legal_name: ""` is refused with a
  message instead of returning all 156,544 rows. Filters are capped at 500 characters.
- **"(headline)" is earned per year, whatever the filter.** A Cleared total is labeled a headline
  only when every matched year is ordinary: not an early snapshot (FY2009, FY2013) and not a
  year that prints statuses other than Cleared/Pending anywhere in it (FY2011, and FY2012, whose
  `Government` rows hold $235,206,318). A narrow FY2011 search with no such rows is still not a
  headline. Otherwise the label says why, and a note gives the year's other statuses.

## The checked PDF tables (optional download)

The four PDF tools follow the rules settled for epic #190
([`research/2026-10-22-mcp-pdf-tables/PLAN.md`](../research/2026-10-22-mcp-pdf-tables/PLAN.md)):

- **Checked data only.** Only family-years `data/pdf_years.csv` lists as `reviewed` or `closed`
  are served, and only rows at that status. At run time the server trusts the downloaded
  release's own `pdf_years` table for that list; what guarantees no old-parser year is ever in it
  is the build and its tests (`test/pdf-families.test.js`), not the server. Every row says which: "checked, review in progress"
  or "checked and reviewed". The old parser's output is never served; FY2008–FY2017 answer "not
  available yet".
- **Values as printed**, never corrected. Each row lists its review entries as the public
  explorer shows them: "N things to check on this row (about how the PDF was read, not about the
  organization)", each entry's note and its decision in plain words, or "not yet decided". The
  note is one plain sentence for its check, from `src/checkwords.ts` (shared with the explorer),
  never the check's code or the reviewers' shorthand; the row's other flags follow as "how this
  row was read: ...". No check id or severity is shown ("critical" next to an organization's
  name would read as a charge against it), and the reviewers' suggested decisions are not served
  (the download withholds `pdf_review_suggestions`, as the public explorer does).
- **Questions to Council Finance** (`data/council_questions.csv`, worded by `src/questions.ts`,
  shared with the explorer): an entry a question covers says "Open question (not yet sent)" (a
  draft), "Question sent to Council Finance on <date>" (under 30 days), the same with ", no
  answer yet" (30 days or more), or "Council Finance answered on <date>: <answer>". A
  `needs_info` decision no question covers says "Still being checked".
- **Hidden text** (text in the PDF a reader cannot see on the page) is served in its own line,
  always labeled "hidden text, not visible on the printed page".
- **The #209 fields**: `fiscal_conduit`, the `*` mark (`review_not_completed`, with the PDF's
  footnote), `program_or_subheading`, `amount_kind` ("no dollar amount" rows counted, never
  summed) and the Jobs to Build On sub-awards, listed under their parent award.
- **Three links per row**, from `src/rowlinks.ts` (shared with the explorer): the explorer's
  source view with the row highlighted (this one opens the live explorer, which serves the
  current files, not a fixed commit); the PDF on GitHub **at the commit the tables were built
  from** (recorded at build time only when that commit is on `origin/main`, `data/` and `source/`
  are clean, and every cited PDF has the same bytes there; otherwise no GitHub link; never
  `main`); the publisher's copy where a manifest records the same
  file. With `--pdfs`, the row also names the PDF's copy on your machine.
- Totals cover every match, however many rows are shown, as in the other tools.
- **The same search rules as the explorer** (`viz/explorer/src/query/pdf.js`, PR #224): the same
  columns per filter (an EIN also matches the fiscal conduit's; an organization never matches a
  sub-award's partner), the same row order and the same totals. `test/pdf-tools.test.js` checks
  counts, totals and the first page against the explorer's own queries.

### Getting it

Either way, files go to a per-user folder, never `node_modules`: `NYC_BUDGET_DATA_DIR` if set,
else `~/Library/Application Support/nyc-budget-mcp` (macOS), `$XDG_DATA_HOME/nyc-budget-mcp` or
`~/.local/share/nyc-budget-mcp` (Linux), `%LOCALAPPDATA%\nyc-budget-mcp` (Windows).

- `npx @betanyc/nyc-budget-mcp download --pdf-tables [--pdfs] [--from <manifest URL or path>]`
- or `NYC_BUDGET_PDF_DATA=on` (tables) or `=pdfs` (tables and PDFs) in the server's `env`: the
  server downloads in the background on its next start; the other tools answer meanwhile, and the
  PDF tools say the download is under way.

| Setting | What it does |
|---|---|
| `download --pdf-tables` | Download the checked tables (about 17 MB) |
| `download --pdf-tables --pdfs` | The tables and the PDFs the rows cite (148 MB more), so each row can name the PDF's copy on your machine |
| `download ... --from <manifest>` | Use another release's manifest (URL or local path) |
| `NYC_BUDGET_PDF_DATA=on` | Download the tables in the background when the server starts, if none are installed |
| `NYC_BUDGET_PDF_DATA=pdfs` | The same, with the PDFs (also fetches PDFs missing from an install) |
| `NYC_BUDGET_PDF_DATA_URL` | Use another release's manifest, like `--from` |
| `NYC_BUDGET_DATA_DIR` | Where the files go (default: the per-user folder above) |

The setting does not update an install. To get a newer release, run `download --pdf-tables`
again.

By default the downloader asks GitHub for this repo's newest published release whose tag starts
with `pdf-tables-` and that carries `pdf-tables.manifest.json`. `NYC_BUDGET_PDF_DATA_URL` (or
`--from`) points at another manifest, over `https://`, `file:` or a local path. Every file is
downloaded to a temporary name, checked against the manifest's size and sha256 (the tables also
after unpacking; a file larger than its manifest says is stopped as it arrives), opened and
checked for the tables and format the tools read, and only then renamed into place. A failed
download leaves the previous install untouched and no temporary file; temporary files a killed
download left are removed by the next one. One download runs at a time per folder (a lock file,
`pdf-tables/download.lock`). Plain `http:` is refused except on this machine. A running server
picks up tables `download` installs, without a restart.

**Releases.** The releases are listed on
[GitHub](https://github.com/BetaNYC/New-York-City-Budget/releases); the data releases' tags start
with `pdf-tables-`, and the downloader takes the newest. As of 2026-10-24 that is
`pdf-tables-2026-10-24-260d16e` (a hand run from commit `260d16e`): 36 family-years, all
`reviewed` (17.4 MB of tables), and 126 PDFs (148 MB). The first was
`pdf-tables-2026-10-23-5bab77c`, published on 2026-10-23 from commit `5bab77c`.

**To try tables you built yourself**, build a release locally:
`npm run build-pdf-release -- --out <dir> [--pdfs] [--allow-local-commit]`
(`--allow-local-commit` is for local trials only: it warns, the manifest says
`"source_commit_scope": "local"`, and a server builds no GitHub link from such tables), and install it
with `download --pdf-tables --from <dir>/pdf-tables.manifest.json`.

### Publishing a release (W7)

**Today releases are hand runs.** The repository variable `PDF_TABLES_AUTO_PUBLISH` is not set,
so a push to `main` builds and checks a release but does not publish it. Both releases so far
(2026-10-23 and 2026-10-24) were hand runs.


`.github/workflows/pdf-tables-release.yml` runs on a push to `main` that changes the PDF tables:
`data/fy*/pdf/**`, `data/pdf_years.csv`, `research/*/data/*_review_decisions.csv`, or the
scripts that build them (`mcp/scripts/build-index.mjs`, `build-pdf-release.mjs`,
`verify-pdf-release.mjs`, `pdf-families.mjs`, `source-commit.mjs`), the PDFs a release carries
(`source/FY*/**`), or the format the downloader reads (`mcp/src/pdfdata.ts`). Never on a pull request or a
fork. **A push publishes only once the repository variable `PDF_TABLES_AUTO_PUBLISH` is `true`**
(Settings → Secrets and variables → Actions → Variables); until then a push builds and checks
only, so the first release is a maintainer's hand run. Two jobs:

1. **Build and check** (read-only): `build-pdf-release.mjs --pdfs` (never
   `--allow-local-commit`), then `verify-pdf-release.mjs --commit <pushed commit>`, which fails
   unless every file has its manifest's size and sha256 (the tables also unpacked), the manifest
   parses as the downloader reads it, the tables were built from the pushed commit with
   `source_commit_check: "pdfs_match"` and `source_commit_scope: "origin/main"`, `data/` and
   `source/` are clean, and the commit is on `origin/main`. Then the downloader installs the
   tables from the folder into a throwaway data folder. The checked files go to the next job.
2. **Publish** (the only job with `contents: write`; it runs no repository code): checks every
   file's sha256 against the manifest again, and stops unless the commit is `main`'s tip right
   now. The downloader installs the newest published release, so publishing an older commit
   (a "Re-run jobs" keeps its run's old commit but would get today's date) would roll users back;
   for the same reason a re-run of a push run is refused (start a hand run instead). Then it
   creates a **draft** release tagged
   `pdf-tables-YYYY-MM-DD-<7-digit commit>` (UTC date) at the pushed commit, uploads the files
   `verify-pdf-release.mjs` listed (the tables, every cited PDF by sha256, the manifest last), and
   only then publishes it. The downloader skips drafts, so it never sees a half-uploaded release.
   The release is not marked "latest", so the npm releases (`mcp-v*`) keep that badge. If an
   upload fails, the step deletes its own draft, so the next run starts clean. A second run for
   the same commit on the same day stops: the release exists (a draft left behind, say if the
   runner died, is named as such: delete it on the Releases page and run again).

The actions it uses are pinned by commit id, their version in a comment.

Run by hand: Actions → "PDF tables release" → Run workflow, on `main`. `dry_run` (default: on)
builds and checks without publishing; uncheck it to publish.

**A hand run** (a maintainer's decision):

1. Actions → "PDF tables release" → Run workflow on `main`, `dry_run` checked. Read the run's
   summary: the tag, file count and size (the first was about 165 MB: 17 MB of tables, 148 MB
   of PDFs).
2. Run it again with `dry_run` unchecked to publish.
3. Check it from any machine: `NYC_BUDGET_DATA_DIR=$(mktemp -d) npx @betanyc/nyc-budget-mcp download --pdf-tables`,
   then a PDF tool with the same `NYC_BUDGET_DATA_DIR`.

To publish on every merge instead, set the repository variable `PDF_TABLES_AUTO_PUBLISH` to
`true`. Delete it to go back to hand runs.

To withdraw a release, delete it (and its tag) on GitHub; the downloader then picks the newest
remaining one.

### The release format (`nyc-budget-pdf-tables/1`)

A release carries, as flat assets:

| Asset | What it is |
|---|---|
| `pdf-tables.manifest.json` | The manifest (below) |
| `pdf-tables.db.gz` | gzip of `pdf-tables.db`: every `pdf_*` table of a `build-index.mjs --include-reviewed` build (reviewed and closed family-years; no spreadsheet table), with `pdf_review_suggestions` left empty (withheld, as in the public explorer), plus `meta` (`pdf_tables_format`, `built_at`, `source_commit`, `source_commit_check`, `source_commit_scope`, `pdf_gate`, `withheld`, `inputs`, `counts`) |
| `<sha256>.pdf` | Optional (`--pdfs` builds): each PDF the rows cite, named by its sha256 |

```json
{
  "format": "nyc-budget-pdf-tables/1",
  "built_at": "2026-10-23T01:00:50.411Z",
  "source_commit": "<40-digit commit the tables were built from>",
  "source_commit_check": "pdfs_match",
  "source_commit_scope": "origin/main",
  "families": [{ "fiscal_year": 2027, "family": "schedule_c", "status": "reviewed", "rows": 9979 }],
  "pdfs_included": false,
  "files": [
    { "name": "pdf-tables.db.gz", "kind": "pdf_tables", "bytes": 16803670, "sha256": "…",
      "unpacked": { "name": "pdf-tables.db", "bytes": 116428800, "sha256": "…" } },
    { "name": "<sha256>.pdf", "kind": "pdf", "path": "source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf", "bytes": 0, "sha256": "…" }
  ]
}
```

File names are plain names resolved next to the manifest; a `pdf` file's `path` must be a
`source/….pdf` repo path. A server refuses a manifest or tables of another `format`, so a later
format change needs a new value and a server that reads it.

## Migrating from 1.x

| 1.x tool | In 2.0.0 |
|---|---|
| `search_awards` | `search_disclosure_awards` (`legal_name`, `program_name`, `council_member` / `council_member_id`, `fiscal_year`, `ein`), or `search_schedule_c_awards` for Schedule C as printed (PDF tables download) |
| `get_awards_by_ein` | `search_disclosure_awards` with `ein`; its totals and per-year split cover every match |
| `search_capital_projects` | `search_capital_book` (the §254 tables, checked; PDF tables download) or `search_council_capital` (the Council's own lists) |
| `search_transparency_resolutions` | `search_transparency_changes` (PDF tables download). For a resolution's Legistar record, [`nyc-council-mcp`](https://github.com/BetaNYC/nyc-council-mcp) |
| `get_terms_conditions` | `search_terms_conditions` (PDF tables download) |
| `get_legistar_link` | Removed. Its crosswalk indexed the PDF documents 2.0 no longer serves, and several rows were researchers' candidates rather than verified links. For a resolution's Legistar record, use [`nyc-council-mcp`](https://github.com/BetaNYC/nyc-council-mcp) |
| `list_available_fiscal_years` | Kept, rebuilt: per year, which structured datasets exist and where they came from |

Calling a removed tool returns an error that names its replacement. Figures published from 1.x
(the old parser's Schedule C and §254) will not reproduce: the checked tables were read again
from the PDFs, and the old parser lost and merged rows.

## Architecture

TypeScript + the MCP SDK + zod over stdio, on a local SQLite index (no live upstream API).

- **The parent repo's structured datasets** are the single source of truth: `../data/disclosure_years.csv`, `../data/fyNN/expense_disclosure/`, `../data/capital/`, `../data/open_data/` (whether each record is also on NYC Open Data, which the explorer shows), and the `MANIFEST.csv` of each source folder whose files they cite.
- **`scripts/build-index.mjs`** reads only those files and builds `mcp/data/budget.db` (git-ignored) with `better-sqlite3`. It records every file it read in the index's `meta.inputs`, stops on any value outside a documented vocabulary (a status, a flag, a row count that disagrees with `disclosure_years.csv`, a capital source whose sha256 differs from its manifest), and is idempotent: the `.db` is dropped and rebuilt each run.
- **The PDF tables, kept out of the package.** The index also has empty `pdf_*` tables (`scripts/pdf-families.mjs`). The package's build (`npm run build-index` = `build-index.mjs --spreadsheet-only`) loads no PDF family, whatever its status; with no flag, `closed` families load (the explorer's default build); `--include-reviewed --out <file>` adds `reviewed` ones and refuses to write `data/budget.db`. Every build records the commit it was built from (`meta.source_commit`, `NYC_BUDGET_SOURCE_COMMIT` overrides `git rev-parse HEAD`) and whether every cited PDF has the same bytes at that commit.
- **`scripts/build-pdf-release.mjs`** builds the optional download from an `--include-reviewed` build (see [the release format](#the-release-format-nyc-budget-pdf-tables1)).
- **`src/pdfdata.ts`** finds, checks and opens the downloaded tables (read-only) and downloads them; **`src/pdfquery.ts`** runs the four PDF tools' queries, with the serving gate on every query.
- **`src/db.ts`** opens the index read-only and runs one query per tool; totals come from SQL over every match, never from the page.
- **`src/server.ts`** holds the tool definitions, strict zod validation, the migration notes for removed tools, and the response text.

## Build & run

From inside `mcp/`:

```bash
npm install          # runs prepare → build + build-index
npm start            # launch the MCP server over stdio
npm run build-index  # rebuild mcp/data/budget.db from the repo's datasets (spreadsheet only)
npm run build-pdf-release -- --out <dir> [--pdfs]   # build the optional PDF tables download
npm test             # build + build-index + a PDF tables release in .pdf-test/ + the tests
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
| `test/shipped-data.test.js` | The package's index has only the expected tables, every `pdf_*` table empty, the commit recorded; every file its build read is on a structured allowlist and none is PDF-derived; `npm pack` would ship exactly the `dist/` code, README, LICENSE, package.json and the index (replaces 2.0.0's `no-pdf-data.test.js`) |
| `test/pdf-families.test.js` | The PDF families' gate: `--include-reviewed` never writes `data/budget.db`; a reviewed build loads exactly what `pdf_years.csv` lists, from no old-parser file; the download holds the `pdf_*` tables only, every row of a listed reviewed or closed family-year; the spreadsheet tools answer the same with or without it |
| `test/pdf-tools.test.js` | The four PDF tools: without the download, how to add it; every served row labeled, with its page and links at the build's commit (never a branch; none when the PDFs were not checked against it); planted rows of an unlisted year or another status never served; hidden text always labeled; decisions shown; "no dollar amount" rows and Part II never summed; totals equal the CSVs; **parity** with the explorer's queries (`viz/explorer/src/query/pdf.js`: Terms, Schedule C only rows, capital Part I) |
| `test/pdf-download.test.js` | The download, against a local HTTP server and folder only: install, `--pdfs`, a tampered, oversized or missing file (or PDF) installs nothing and leaves no temp file, a killed download's temp files are swept, one download at a time, plain http refused, `NYC_BUDGET_PDF_DATA=on` in the background and `=pdfs` not re-downloading a release without PDFs, release picking |
| `test/pdf-release.test.js` | The automatic release (W7): `verify-pdf-release.mjs` accepts pretest's release and lists exactly its files, manifest last; refuses a local build, another commit, a tampered or missing file, another format; the workflow's tag is one the downloader picks, and the CLI installs from exactly the uploaded files on a local HTTP server; the workflow never runs on a PR, has write access only in its publish job, never builds with `--allow-local-commit` |
| `test/source-commit.test.js` | The commit recorded for the GitHub links, on a throwaway repo: only a clean commit on `origin/main` whose PDFs match |
| `test/tools.test.js` | Exactly eight tools listed; every removed 1.x tool answers with its migration note; `list_available_fiscal_years` matches the datasets year by year |
| `test/disclosure.test.js` | Every row of every year indexed with its provenance; FY2010 not loaded; true counts and Cleared / Pending totals under any `limit`; ordering; status, amount, address and member filters; caveat and footer; strict-schema hints |
| `test/disclosure-audit.test.js` | The audit questions (`../data/DISCLOSURE-AUDIT.md`, M1–M13): exact-to-the-cent totals for every year × status, truncation, sort before limit, limit edges, EIN rules, literal wildcards, multi-value notices, address filters, and the EIN-less note |
| `test/disclosure-v2.test.js` | FY2009, FY2011, FY2012 with `od_mocs_id`, `od_match`, `row_flag`; early-snapshot labeling; the coverage line; FY2010's reason; exact `mocs_id` / `od_mocs_id`; the `row_flag` note |
| `test/capital.test.js` | Every capital row and its provenance (sha256 recomputed from the committed file); own-year vs out-year totals; ordering; split records; every filter's exactness; FY2018; caveats; and `compare_capital_to_omb` verdict counts, figures and ordering |
| `test/license.test.js` | One license: the license statements name no second license; `LICENSE` names code, data and docs and excludes `source/`; `mcp/LICENSE` equals the repository's. |
| `test/cleared-label.mjs` | Helper, not a test: the Cleared-line label expected for a set of CSV rows. |
| `test/strict-schema.test.js` | Issue #37: every tool advertises and enforces `additionalProperties: false`, with per-tool hints |
| `test/build-guard.test.js` | The index build fails loudly on a dataset with no rows or a missing year, and installs the new index in one step (#95) |
| `test/checkwords.test.js` | Every check code in the promoted files has a plain sentence (`src/checkwords.ts`); questions to Council Finance are worded by status (`src/questions.ts`) |
| `test/whole-word.test.js` | #259: short terms match whole words (`AI` not in `Jamaica` or `AIDS`; punctuation and either end of the text are word edges; accents folded), the 3-character default and `whole_word` overriding it both ways on every text-filter tool, totals equal to the rows matched, the answer's note |
| `test/fold-roundtrip.test.js` | A printed value pasted back exactly finds its own rows, including accented and garbled text as published |
| `test/open-data.test.js` | Whether each record is on NYC Open Data (`data/open_data/`), as the explorer shows it |
| `test/pdf-align.test.js` | How a Schedule C row is matched to the disclosure spreadsheet (`disclosure_status`) |
| `test/rowlinks.test.js` | The row-link builder (`src/rowlinks.ts`), shared with the explorer: the explorer link, the GitHub links, the publisher's copy |

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
- **The PDF tables** are not in the npm package: `.github/workflows/pdf-tables-release.yml`
  publishes them as `pdf-tables-*` GitHub Releases, by hand for now (see "Publishing a release").
  The latest npm release is 2.0.4 (tag `mcp-v2.0.4`).
- **CI**: `.github/workflows/ci.yml` builds and tests `mcp/` on Node 22 and 24 for every PR into
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
the [repository README](../README.md#license): BetaNYC's code, derived data and documentation
are all MIT ([`LICENSE`](../LICENSE)). The Council's workbooks are © The City of New York,
reproduced as public records and not covered by BetaNYC's license; NYC Open Data rows are
covered by the [NYC Open Data Terms of Use](https://opendata.cityofnewyork.us/overview/#termsofuse).
