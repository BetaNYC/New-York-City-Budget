# New York City Budget

Checked, open data on New York City's budget, from [BetaNYC](https://beta.nyc). It has two
halves, and they answer different questions:

| | **City agency budgets** | **Council discretionary funding** |
|---|---|---|
| **What it shows** | How much each City agency was given in the adopted budget, and how that changed during the year | Which organizations the City Council funds, for how much, through which agency, and at which Council member's request |
| **Answers questions like** | "How much does my community board get?" "How did NYPD's budget change since 2017?" | "Which groups did my Council member fund?" "Did this nonprofit get Council money?" |
| **Source** | NYC Open Data, Expense Budget ([`mwzb-yiwb`](https://data.cityofnewyork.us/d/mwzb-yiwb)), published by the Mayor's Office of Management and Budget (OMB) | The Council's spreadsheets, its budget PDFs (Schedule C and others) and NYC Open Data |
| **Years** | FY2017–FY2027 | FY2009, FY2011–FY2027 (by dataset; see below) |
| **Size** | The whole expense budget: $117.8 billion adopted for FY2026, as counted in Open Data | The Council's own share: discretionary awards and capital designations |
| **Look at it** | The [agency budget explorer](https://betanyc.github.io/New-York-City-Budget/agencies/) (moved here from [`nyc-budget-viz`](https://github.com/BetaNYC/nyc-budget-viz) in [#265](https://github.com/BetaNYC/New-York-City-Budget/issues/265)) | The [Council budget explorer](https://betanyc.github.io/New-York-City-Budget/explorer/) |

Not sure which half you need? See [**Which tool answers my question?**](WHICH-TOOL.md) It also
has a [glossary](WHICH-TOOL.md#glossary): fiscal year, adopted vs. modified, unit of
appropriation, intra-city, discretionary funding.

- **Search it in a browser:** the [Council budget explorer](https://betanyc.github.io/New-York-City-Budget/explorer/) and the [City agency budgets view](https://betanyc.github.io/New-York-City-Budget/explorer/#view=agencies) in the same explorer.
- **Ask an AI assistant:** the [`@betanyc/nyc-budget-mcp`](mcp/README.md) server: Council funding, and since 2.1.0 City agency budgets (`search_agency_budget`, `compare_adopted_modified`, [#270](https://github.com/BetaNYC/New-York-City-Budget/issues/270)).
- **Download it:** the CSVs in [`data/`](data/), the [data releases](https://github.com/BetaNYC/New-York-City-Budget/releases), and the agency budgets' [one-file CSV](viz/agencies/data/nyc_budget.csv).
- **What's changed:** [`WHATS-CHANGED.md`](WHATS-CHANGED.md) lists every change a reader would notice, newest first, with each correction and what to re-check.
- **Report a problem:** [GitHub issues](https://github.com/BetaNYC/New-York-City-Budget/issues).

**Last revised:** 2026-11-13.

> **Correction, 2026-11-09.** Before this date the agency budget explorer labeled every year one
> year late: "Adopted 2026" was really the FY2025 adopted budget. A community board staffer's
> spreadsheet showed it. It was fixed the same day
> ([nyc-budget-viz#4](https://github.com/BetaNYC/nyc-budget-viz/pull/4)). If you copied agency
> figures before 2026-11-09, move each one a year earlier, or download them again. The rule now
> used is [below](#which-fiscal-year-each-amount-describes). The Council half was not affected.

---

## Contents

- [What this project is](#what-this-project-is)
- [The fiscal year](#the-fiscal-year)
- [Half 1: City agency budgets](#half-1-city-agency-budgets)
- [Half 2: Council discretionary funding](#half-2-council-discretionary-funding)
- [How the Council PDF tables are checked](#how-the-council-pdf-tables-are-checked)
- [Use it](#use-it): the explorers, the MCP server, downloads
- [What is not done yet](#what-is-not-done-yet)
- [How to contribute](#how-to-contribute)
- [Repository layout](#repository-layout)
- [History, briefly](#history-briefly)
- [How this relates to other NYC budget data](#how-this-relates-to-other-nyc-budget-data)
- [AI use](#ai-use) · [License](#license) · [Acknowledgments](#acknowledgments)

## What this project is

City budgets are among the most important public documents there are, and among the hardest to
use. This project turns NYC's budget data into files you can search, join and check, so
journalists, researchers, community boards and New Yorkers can ask questions of their city's
spending. Every row says where it came from, and no number is changed by hand.

It is one home for two kinds of budget data that people often mix up:

- **City agency budgets** are the whole expense budget, agency by agency: what the City adopted
  in June and what it looked like by the end of the year. This is where a community board, a
  City agency or a reporter looks up how much an agency got.
- **Council discretionary funding** is the money the Council itself directs to organizations, at
  the level of the organization and its tax ID (EIN): **who got what**. It is a small part of the
  budget, and it is where you look up a nonprofit's Council award.

Neither half is a source for revenue, actual spending, or spending over decades. For those, see
[other sources](#how-this-relates-to-other-nyc-budget-data).

**One site, two halves.** The agency budget explorer used to be a separate site
([`nyc-budget-viz`](https://github.com/BetaNYC/nyc-budget-viz)), then a separate app in this repo
at `/agencies/` (#265). Since #270 it is a view of the explorer, `/explorer/#view=agencies`,
built from the same index as the MCP server, so the site and the MCP can't disagree. `/agencies/`
now forwards every old link there (#288). The front page has a door to each half, and every page
shares one top bar and footer (#267). The rest of
the plan is epic [#272](https://github.com/BetaNYC/New-York-City-Budget/issues/272).

## The fiscal year

New York City's fiscal year runs **July 1 to June 30** and is named for the year it **ends**:
FY2026 is July 1, 2025 to June 30, 2026. Both halves use this, and every year in this repo is a
fiscal year unless it says otherwise. The budget for a year is adopted in June, just before it
starts. More words: the [glossary](WHICH-TOOL.md#glossary).

## Half 1: City agency budgets

**What it is.** The City's expense budget for every agency, broken down by **unit of
appropriation** (the lines the budget is adopted by; often split into Personal Services, which
is pay, and Other Than Personal Services, which is everything else). For each fiscal year,
FY2017–FY2027, there are two figures:

- **Adopted:** the budget adopted in June, before the year starts.
- **Modified:** that year's budget as changed during the year, as of June, near the year's end.
  The newest year's Modified figure is **not yet published**: the City publishes it in the release
  that adopts the next year's budget. Until then it is blank, never zero.

**Source.** NYC Open Data, Expense Budget, [`mwzb-yiwb`](https://data.cityofnewyork.us/d/mwzb-yiwb),
published for OMB. Public, read through the Socrata API with no token. The pipeline keeps 764
units of appropriation.

**Totals are gross.** Open Data rows include **intra-city** amounts (money one City agency pays
another), which OMB subtracts to get its headline "net total budget". So for FY2026 the adopted
budget is **$115.9 billion net** (OMB's figure) and **$117,791,473,676 as counted in Open Data**,
which includes $1,884,163,949 of intra-city money.

### Which fiscal year each amount describes

Each fiscal year is published up to three times, Preliminary (January), Executive (April or May)
and Adopted (June), and **each release restates the whole budget**. Adding them up would count
the same money up to three times, so only the **June release** of each year is used.

A release's `fiscal_year` tag names the budget being adopted in it, not the year of every amount
in the row. OMB's printed FY2026 Adopted Budget, which is the same publication as the June 2025
release tagged 2026, heads its columns "Adopted Budget for FY 2025", "Current Modified Budget for
FY 2025" and "Adopted Budget for FY 2026". So, in the release tagged `fiscal_year = Y`:

| Field | Describes |
|---|---|
| `adopted_budget_amount` | FY Y−1, adopted |
| `current_modified_budget_amount` | FY Y−1, as modified to the release date |
| `financial_plan_amount` | FY Y (in the June release, the adopted budget) |

The rule the explorer uses:

- **Adopted Y** = `financial_plan_amount` from the June release tagged Y. (It equals
  `adopted_budget_amount` in the release tagged Y+1, to the dollar.)
- **Modified Y** = `current_modified_budget_amount` from the June release tagged Y+1.
- The newest year's Modified is "Not yet published".

Getting this wrong labels every year one year late. That is the mistake corrected on 2026-11-09
([above](#new-york-city-budget)).

### How the agency figures are checked

The year rule is coded once, in the MCP's loader
([`mcp/scripts/agency-budget.mjs`](mcp/scripts/agency-budget.mjs), #284). It builds the
`agency_budget` table from the committed Open Data snapshot
([`source/agency-budget-qa/`](source/agency-budget-qa/README.md)); the explorer's view, the MCP's
tools and the CSV download ([`viz/explorer/scripts/agency-csv.mjs`](viz/explorer/scripts/agency-csv.mjs))
all read that table. Three checks, each with its own code:

- [`mcp/test/agency-budget.test.js`](mcp/test/agency-budget.test.js) re-derives every cell from
  the snapshot, and checks OMB's printed FY2026 Adopted Budget to the dollar: the citywide FY2026
  and FY2025 adopted totals, the FY2025 modified total, and Manhattan Community Board 1's lines
  (page 182E).
- [`code/qa_agency_budget.py`](code/qa_agency_budget.py) recomputes every cell of the CSV in
  Python ([`code/test_agency_budget_cleanup.py`](code/test_agency_budget_cleanup.py) checks OMB's
  figures in it too).
- [`viz/explorer/test/agency-parity.test.mjs`](viz/explorer/test/agency-parity.test.mjs) checks
  the explorer's data and queries against the old app's 16,808 cells: 0 differences, plus 936
  cells that were $0 and now say "Not in this year's budget".

CI runs them on every PR and before each deploy. Details:
[`viz/agencies/data/SCHEMA.md`](viz/agencies/data/SCHEMA.md).

This is **not** the row-by-row review the Council PDF tables get (below). The agency numbers are
the City's Open Data, as published, checked against OMB's printed totals. A test that checks
every community board and year after the move is planned in
[#268](https://github.com/BetaNYC/New-York-City-Budget/issues/268).

## Half 2: Council discretionary funding

This half is about **who got what**, at the level of the organization and its EIN. The Council
publishes who gets its discretionary and capital money as spreadsheets and as long PDF tables.
This half has three sources, and each row says which one it came from.

### 1. The Council's spreadsheets and capital lists

| Dataset | Years | Rows | Where |
|---|---|---:|---|
| **Expense funding disclosure**: each discretionary award, with grantee, EIN, amount, clearance status and mailing address | FY2009, FY2011–FY2027 | 156,544 | [`data/fyNN/expense_disclosure/`](data/fy27/expense_disclosure/), [`data/disclosure_years.csv`](data/disclosure_years.csv) |
| **Capital designations**: the Council's capital lists, from its workbooks (FY2015–FY2017, FY2026, FY2027) and, for FY2019–FY2025, from NYC Open Data `t474-a92g`, which the Council publishes | FY2015–FY2017, FY2019–FY2027 | 16,916 | [`data/capital/`](data/capital/README.md) |

FY2013–FY2027 disclosure files come from the Council's
[Research & Data site](https://rnd.council.nyc.gov/expense_funding/); FY2009, FY2011 and FY2012
from the Council's own workbooks, saved by the Internet Archive. A script reads each workbook
cell by cell and keeps every value as published. Each file's sha256 is recorded.

Know these before you use them:

- **FY2010 is not included.** The Council's archived workbook is incomplete compared with NYC Open
  Data, and the two are never mixed (DATA-ANOMALIES §25).
- **FY2009 and FY2013 are early snapshots**, frozen while many awards were still Pending. Their
  Cleared totals are not the year's outcome.
- **The disclosure is not the adopted budget.** It is a later list, with awards added during the
  year. Its `council_member` is the roster when the file was exported.
- **Addresses are mailing addresses**, not where services were delivered. ZIP codes are checked
  against the Census list, never silently rewritten.
- **FY2018 Council capital** has no spreadsheet. The checked FY2018 capital book (below) is
  planned to fill it once that year is closed (#202, still open).

Details: [`DATA-DICTIONARY.md`](DATA-DICTIONARY.md),
[`source/expense-funding-disclosure/README.md`](source/expense-funding-disclosure/README.md),
[`data/DISCLOSURE-AUDIT.md`](data/DISCLOSURE-AUDIT.md), [`data/capital/README.md`](data/capital/README.md).

### 2. The checked tables from the Council's budget PDFs

Some things are printed only in the adopted budget's PDFs. We read them again, carefully, with a
checked process ([next section](#how-the-council-pdf-tables-are-checked)):

| Family | What it is | Years |
|---|---|---|
| Schedule C | The discretionary awards as adopted, with the initiative and category | FY2018–FY2027 |
| Transparency resolutions | Changes made after adoption: new awards, rescissions, changes of purpose | FY2018–FY2027 |
| Capital book (§254 supporting detail: the detail behind the capital changes the Council adopts under Section 254 of the City Charter) | The Council's capital additions, project by project | FY2018–FY2020, FY2022–FY2027 |
| Terms and Conditions | The reports the budget requires agencies to make | FY2018, FY2021–FY2027 |

That is 36 family-years (one family in one fiscal year), in `data/fyNN/pdf/`. The gaps in that
table are years with no PDF of that kind in `source/FYNN/` (see [what is not done yet](#what-is-not-done-yet)). Each one's status is
in [`data/pdf_years.csv`](data/pdf_years.csv). Values are kept as printed, never corrected. The
PDFs themselves are in [`source/`](source/).

### 3. NYC Open Data

- **City Council Capital Budget** ([`t474-a92g`](https://data.cityofnewyork.us/d/t474-a92g)),
  which the Council publishes: the capital lists for FY2019–FY2025.
- **OMB's Capital Budget** ([`46m8-77gv`](https://data.cityofnewyork.us/d/46m8-77gv)) and
  **Capital Commitment Plan** ([`2cmn-uidm`](https://data.cityofnewyork.us/d/2cmn-uidm)): to compare
  the Council's capital money with OMB's, by budget line (1,425 comparisons over 515 budget lines,
  FY2019–FY2027).
- **City Council Discretionary Funding** ([`4d7f-74pe`](https://data.cityofnewyork.us/d/4d7f-74pe)),
  which stopped updating in April 2021: a cross-check. It adds NYC Open Data's MOCS ID (the Mayor's Office of Contract Services' ID for an award) to matching
  disclosure rows (FY2009–FY2021).

The Council explorer also says, for each award and capital row, whether it is on NYC Open Data,
and the date of the copy it checked.

## How the Council PDF tables are checked

These claims are about the Council's PDF tables only. [`PDF-RECIPE.md`](PDF-RECIPE.md) is the
step-by-step. In short:

1. Read each table from the borders the PDF draws, not from the order its text comes out in.
2. Check every row: against a second reading of the page image, against every total the PDF
   prints, and for printed marks that were missed.
3. Never fix the PDF. Where it is wrong or unclear, flag the row for a person to decide.

Each family-year then has one of two statuses, and every row shows it:

- **`reviewed`: "checked, review in progress."** The table is checked and public. A person may
  still be deciding some flagged rows.
- **`closed`: "checked and reviewed."** A person has decided every flagged row: critical items
  one by one, warnings by type, and every "needs more information" item answered, or 30 days past
  the date its question went to Council Finance. The questions, with their issues and dates, are in
  [`data/council_questions.csv`](data/council_questions.csv) (explained in
  [`data/COUNCIL-QUESTIONS.md`](data/COUNCIL-QUESTIONS.md)).

As of 2026-10-24 all 36 family-years are `reviewed`, and none is `closed` yet.

**Where the checks stand** (the `pdf-tables-2026-10-24-260d16e` release): 141,456 rows in 36
family-years, FY2018–FY2027. In Schedule C, 76,216 of 76,272 rows read the same from the text
and from the page image; the other 56 are flagged for a person. 515 of 519 printed totals tie
exactly; the other 4 are totals the PDF gets wrong itself (one each in Schedule C FY2018, FY2024,
FY2025 and FY2026), flagged and not fixed. 1,704 review items wait for a person's decision (195
critical, 1,509 warnings); 14 are decided. In short: every row is checked, the review of each
row is not finished, and we never change a number.

Rows show their review notes in plain words, and the status of any question to Council Finance.
Text in the PDF that can't be seen on the printed page is shown apart, labeled "hidden text".

**The checks run in CI** (continuous integration: GitHub runs them automatically). On every pull
request and every push to `main` that touches the readers, configs, PDFs or tables, and when a
maintainer starts it by hand, [`python-checks.yml`](.github/workflows/python-checks.yml) runs
`python -m pytest code` and re-reads every promoted PDF (promoted: its checked tables are
committed to `data/fyNN/pdf/`) to prove the committed tables match (about an hour, on macOS).
[`ci.yml`](.github/workflows/ci.yml) builds and tests the MCP and the explorer, and checks that the
two agree. How to run each check yourself: [`PDF-RECIPE.md`](PDF-RECIPE.md), Steps 2, 5 and 6.

**Data releases.** The checked tables (and the PDFs they cite) are published as GitHub Releases
tagged `pdf-tables-<date>-<commit>`, each with a manifest of sha256s
([all releases](https://github.com/BetaNYC/New-York-City-Budget/releases)). The downloader always
takes the newest. As of 2026-10-24 that is
[`pdf-tables-2026-10-24-260d16e`](https://github.com/BetaNYC/New-York-City-Budget/releases/tag/pdf-tables-2026-10-24-260d16e):
the 36 family-years, FY2018–FY2027 (17.4 MB of tables), and 126 PDFs (148 MB). The first was
[`pdf-tables-2026-10-23-5bab77c`](https://github.com/BetaNYC/New-York-City-Budget/releases/tag/pdf-tables-2026-10-23-5bab77c). The workflow
([`.github/workflows/pdf-tables-release.yml`](.github/workflows/pdf-tables-release.yml)) can
publish on every merge, but that is off for now, so a maintainer runs each release by hand. The
explorer redeploys on every merge that changes the data.

## Use it

### In a browser

- **[Council budget explorer](https://betanyc.github.io/New-York-City-Budget/explorer/)**:
  searches the same data the MCP serves. It has pages for expense awards, years, comparing years,
  capital, capital vs. OMB, and one for each PDF family (Schedule C, transparency resolutions,
  the capital book, organizations in the capital book, Terms and Conditions). Each page loads its
  data when you open it. A test checks that the explorer and the MCP give the same rows and
  totals. Every spreadsheet row links to its file. Every PDF row opens its page with the row
  highlighted. The "About the data" page explains what each label means. Code:
  [`viz/explorer/`](viz/explorer/README.md).
- **[City agency budgets](https://betanyc.github.io/New-York-City-Budget/explorer/#view=agencies)**:
  a view of the same explorer. Every agency for a year, an agency's units of appropriation, and
  one unit across FY2017–FY2027, adopted vs. modified, with a chart and a table of the same
  numbers. A unit that is not in a year's budget says "Not in this year's budget", never $0.
  Downloads: what is on screen, or the whole dataset as one CSV. The old address, `/agencies/`,
  forwards every old link there. Code: [`viz/explorer/src/views/Agencies.jsx`](viz/explorer/src/views/Agencies.jsx).
- **[Community board budgets](https://betanyc.github.io/New-York-City-Budget/agencies/boards.html)**:
  all 59 boards, FY2017–FY2027, adopted and modified by unit (Personal Services, Other Than
  Personal Services, Rent), each figure with the Open Data release it comes from; download all 59
  as [one CSV](viz/agencies/data/community_boards.csv) (built by
  [`code/build_community_boards.py`](code/build_community_boards.py)).
- **The first Council explorer** (July 2026) is retired. Its address,
  [`legacy.html`](https://betanyc.github.io/New-York-City-Budget/legacy.html), says so and forwards
  old links into the explorer (#304; [`viz/README.md`](viz/README.md)).

### Ask an AI assistant: the MCP server

[`@betanyc/nyc-budget-mcp`](https://www.npmjs.com/package/@betanyc/nyc-budget-mcp) is a
[Model Context Protocol](https://modelcontextprotocol.io) server. It lets an AI assistant (Claude
Desktop, Claude Code and others) search the Council data and cite each row. It does not answer
agency budget questions yet ([#270](https://github.com/BetaNYC/New-York-City-Budget/issues/270)).
Add it to your client's config:

```json
"mcpServers": {
  "nyc-budget": {
    "command": "npx",
    "args": ["-y", "@betanyc/nyc-budget-mcp@2"]
  }
}
```

It has eight tools:

| Tool | Answers from |
|---|---|
| `search_disclosure_awards` | The Council's expense funding disclosure |
| `search_council_capital` | The Council's capital lists |
| `compare_capital_to_omb` | The Council's capital vs. OMB's adopted capital budget, by budget line |
| `list_available_fiscal_years` | What each year holds, where it came from, and each PDF family-year's status |
| `search_schedule_c_awards` | Schedule C, from the checked PDF tables |
| `search_transparency_changes` | The transparency resolutions, from the checked PDF tables |
| `search_capital_book` | The capital book, from the checked PDF tables |
| `search_terms_conditions` | Terms and Conditions, from the checked PDF tables |

The npm package holds the server's code and its spreadsheet index (`dist` and `data/budget.db`).
The checked PDF tables are an **optional download** (about 17 MB) from this repo's data
releases: `npx @betanyc/nyc-budget-mcp download --pdf-tables` (add `--pdfs` for the PDFs, 148 MB
more), or set `"env": { "NYC_BUDGET_PDF_DATA": "on" }` and the server downloads them when it
starts, if none are installed (run `download` again to get a newer release). Until then, the four PDF tools say how to add them. Every file is
checked against its published sha256.

**How text searches match.** Name and text filters (organization, member, purpose, title and so on)
ignore case and accents. A term of 3 or fewer letters and digits matches whole words only, so `AI`
finds "AI Training Program" but not "Jamaica" or "AIDS". Longer terms match anywhere, so `Fellow`
also finds "Fellowship". Each tool takes `whole_word: true` or `false` to choose either way, and
the answer says when it matched whole words. Exact filters (EIN, budget line) are unchanged.
The capital book's `project_id` and the transparency `resolution_number` always match anywhere,
so fragments like `CC1` work.
A name search finds only the rows whose text matches, so report it as "at least". The full rules:
[`mcp/README.md`](mcp/README.md#behavior-common-to-the-searches).

Full details: [`mcp/README.md`](mcp/README.md); changes: [`mcp/CHANGELOG.md`](mcp/CHANGELOG.md).

### Download

- **Council data:** the CSVs in [`data/`](data/), described in
  [`DATA-DICTIONARY.md`](DATA-DICTIONARY.md); the checked PDF tables in the
  [data releases](https://github.com/BetaNYC/New-York-City-Budget/releases).
- **Agency data:** one CSV, every agency and unit, FY2017–FY2027:
  [`viz/agencies/data/nyc_budget.csv`](viz/agencies/data/nyc_budget.csv), described in
  [`SCHEMA.md`](viz/agencies/data/SCHEMA.md). Or go
  to the source, [`mwzb-yiwb`](https://data.cityofnewyork.us/d/mwzb-yiwb), and use the
  [year rule](#which-fiscal-year-each-amount-describes).

## What is not done yet

**Bringing the two halves together** is epic
[#272](https://github.com/BetaNYC/New-York-City-Budget/issues/272): names and this README (#264),
moving the agency explorer in (#265), removing what it inherited from Cook County (#266), one
site shell (#267), a standing accuracy test for the agency numbers (#268), a community board
view (#269), then agency budgets in the Council explorer and the MCP (#270) and forwarding the
old address (#271).

For the Council data, open work is tracked in two epics:
[#101](https://github.com/BetaNYC/New-York-City-Budget/issues/101) (read every PDF, one year at
a time) and [#190](https://github.com/BetaNYC/New-York-City-Budget/issues/190) (serve the checked
tables). The bugs the FY2018–FY2027 reviews found (epic
[#244](https://github.com/BetaNYC/New-York-City-Budget/issues/244)) were fixed on 2026-10-24
(#252, #253, #254, #255).

- **No year is `closed` yet.** All 36 family-years are `reviewed`.
- **Questions to Council Finance are drafts, not yet sent.** One issue each:
  [#227](https://github.com/BetaNYC/New-York-City-Budget/issues/227) and
  [#233](https://github.com/BetaNYC/New-York-City-Budget/issues/233)–[#242](https://github.com/BetaNYC/New-York-City-Budget/issues/242).
- **FY2017 back to FY2008 are not re-read yet.** Only the old parser's output exists for them, and
  it is not served (#101).
- **Scanned PDFs wait for an OCR step** in the recipe
  ([#251](https://github.com/BetaNYC/New-York-City-Budget/issues/251)): all FY2009 transparency
  resolutions and some of FY2010–FY2012.
- **Gaps in FY2018–FY2027:** FY2027 transparency resolutions are not in `source/`; two are known
  with no download route ([#246](https://github.com/BetaNYC/New-York-City-Budget/issues/246)).
  There is no FY2021 capital supporting detail in `source/` (OMB's copy is in `source/gpp/`, not
  yet reviewed) and no FY2019 or FY2020 Terms and Conditions.
- **FY2010 disclosure is held.** The Council's archived workbook is incomplete compared with NYC
  Open Data, and we don't mix the two (DATA-ANOMALIES §25).
- **FY2018 Council capital** waits for the FY2018 capital book to be closed
  ([#202](https://github.com/BetaNYC/New-York-City-Budget/issues/202)).
- **Other open issues:** the readers give a few pixels' different counts on Linux, so the Python
  checks run on macOS for now ([#256](https://github.com/BetaNYC/New-York-City-Budget/issues/256));
  4 capital rows still match NYC Open Data two ways
  ([#257](https://github.com/BetaNYC/New-York-City-Budget/issues/257)); checking mailing addresses
  ([#247](https://github.com/BetaNYC/New-York-City-Budget/issues/247)); scheduled re-pulls of the
  Council's workbooks ([#248](https://github.com/BetaNYC/New-York-City-Budget/issues/248)); a
  Checkbook spot check ([#249](https://github.com/BetaNYC/New-York-City-Budget/issues/249)); and
  serving OMB's commitment plan and DCP's capital data in the MCP
  ([#250](https://github.com/BetaNYC/New-York-City-Budget/issues/250)).

## How to contribute

- **Found something wrong?** Open an [issue](https://github.com/BetaNYC/New-York-City-Budget/issues)
  with the half (agency or Council), the fiscal year, the row (or the explorer link) and what the
  source shows. Check [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) first: many oddities are in the
  source and already listed there.
- **Help review a year.** Build the Council explorer with its Review tab
  (`npm run data -- --include-reviewed` in `viz/explorer/`; see [`PDF-RECIPE.md`](PDF-RECIPE.md),
  Step 7) and decide flagged rows. Export your decisions and send them as a pull request.
- **Check an older year.** FY2008–FY2017 are not redone yet. Their issues are under epic
  [#101](https://github.com/BetaNYC/New-York-City-Budget/issues/101); the recipe has every step.
- **Change code.** Open a pull request against `main`. CI builds and tests the MCP and the
  explorer, and a macOS job runs the Python checks (about an hour; run `python -m pytest code`
  yourself first). A change to what the npm package ships needs a version bump and a changelog
  entry.
- **Never fix a value by hand.** Change the reader or record a decision, so every value can be
  traced to its source.

Questions: hello@beta.nyc.

## Repository layout

```
New-York-City-Budget/
├── README.md, WHICH-TOOL.md, PDF-RECIPE.md, DATA-ANOMALIES.md, DATA-DICTIONARY.md
├── source/      the Council's and City's documents (PDFs, workbooks, Open Data pulls), © City of New York
├── data/
│   ├── fyNN/expense_disclosure/   the Council's disclosure, per year
│   ├── fyNN/pdf/                  the checked PDF tables, per year and family
│   ├── capital/                   the Council's capital lists, and the comparison with OMB
│   ├── pdf_years.csv              each PDF family-year's status
│   ├── council_questions.csv      questions to Council Finance, with dates
│   └── retired/                   the old PDF parser's output, kept for history, never served
├── config/      one file per PDF family and year
├── code/        the readers, checks and tests (Python), including the agency pipeline
├── mcp/         the MCP server (TypeScript)
├── viz/         the GitHub Pages site: front page, Council explorer (explorer/), agency
│                explorer (agencies/), legacy.html (retired: forwards old links)
└── research/    plans, review records and research notes
```

## History, briefly

- **1.x (July–August 2026):** the first MCP served tables an early parser read from the PDFs. We
  later found it lost and merged rows without saying so (DATA-ANOMALIES §20, §21).
- **July 2026:** BetaNYC built the agency budget explorer, a separate repo
  ([`nyc-budget-viz`](https://github.com/BetaNYC/nyc-budget-viz)), from DataMade's Look at Cook
  and NYC Open Data `mwzb-yiwb`.
- **2.0.0 (2026-10-17):** we stopped serving anything read from a PDF and moved to the Council's
  spreadsheets and NYC Open Data (DATA-ANOMALIES §27). The old Schedule C explorer stayed online,
  frozen, at [`legacy.html`](https://betanyc.github.io/New-York-City-Budget/legacy.html), with a
  banner saying not to cite it. On 2026-11-13 it was retired: the page now says where it went and
  forwards old links into the explorer (#304).
- **October 2026:** FY2018–FY2027 were read again from the PDFs with the checked process (epic
  [#101](https://github.com/BetaNYC/New-York-City-Budget/issues/101)).
- **2.0.2 (2026-10-23):** the checked tables are served again, labeled, in the MCP and the
  explorer (epic [#190](https://github.com/BetaNYC/New-York-City-Budget/issues/190),
  DATA-ANOMALIES §56). The old parser's output stays retired.
- **2.0.3 (2026-10-24):** fixes for the bugs found in the FY2018–FY2027 reviews (epic
  [#244](https://github.com/BetaNYC/New-York-City-Budget/issues/244)), including the capital
  crosswalk matching on the full project ID.
- **2.0.4 (2026-10-25):** short search terms match whole words
  ([#259](https://github.com/BetaNYC/New-York-City-Budget/issues/259)).
- **2026-11-09:** the agency explorer's year labels corrected
  ([nyc-budget-viz#4](https://github.com/BetaNYC/nyc-budget-viz/pull/4)), and the work to bring
  it into this repo started (epic [#272](https://github.com/BetaNYC/New-York-City-Budget/issues/272)).
- **2.1.0 (2026-11-14, tagged by a maintainer):** City agency budgets in the MCP index and the
  explorer, from one loader and one year rule ([#270](https://github.com/BetaNYC/New-York-City-Budget/issues/270));
  two MCP tools, `search_agency_budget` and `compare_adopted_modified`; the old `/agencies/` app
  retired, its links forwarded.

More: [`mcp/CHANGELOG.md`](mcp/CHANGELOG.md), [`data/retired/README.md`](data/retired/README.md),
[`code/PARSING.md`](code/PARSING.md) (how each old file was made), and
[this README as it was before 2.0.2](https://github.com/BetaNYC/New-York-City-Budget/blob/15d1f8f/README.md),
which describes the old files in detail.

## How this relates to other NYC budget data

| Source | Best for | Overlap with this repo |
|---|---|---|
| **This repo, agency half** | Each agency's adopted and modified budget by unit of appropriation, FY2017–FY2027 | Built from NYC Open Data `mwzb-yiwb`, one June release per year |
| **This repo, Council half** | Council awards and capital designations, at the organization and EIN level | — |
| **[NYC Independent Budget Office, Data Center](https://www.ibo.nyc.gov/content/data-center)** | Citywide and agency spending and revenue over decades, debt, headcount | None at the award level. IBO is the context this data sits in |
| **[NYC OMB budget publications](https://www.nyc.gov/site/omb/publications/publications.page)** | The printed budget the agency figures are checked against | The agency half's check uses OMB's FY2026 Adopted Budget |
| **[NYC Open Data: City Council Discretionary Funding](https://data.cityofnewyork.us/dataset/4d7f-74pe)** | Council awards, FY2009–FY2021 | Overlaps the disclosure for FY2009 and FY2011–FY2021; stopped updating in April 2021. Compared row by row in [`research/2026-10-14-open-data-vs-disclosure-diff.md`](research/2026-10-14-open-data-vs-disclosure-diff.md) |
| **[NYC Checkbook](https://www.checkbooknyc.com)** (Comptroller) | Actual spending and registered contracts | Join on EIN to ask whether an award became a contract; compare an agency's budget with what it spent |
| **[NYC Council budget pages](https://council.nyc.gov/budget/)** | The documents the Council half reads | This repo is the structured, checked version |

A source-by-source crosswalk:
[`research/2026-07-08-ibo-data-center-crosswalk.md`](research/2026-07-08-ibo-data-center-crosswalk.md).

## AI use

BetaNYC uses AI tools openly and with people accountable for the result. The code here was built
by AI agents (Anthropic's Claude) working under the direction and review of BetaNYC staff.

**The figures are not AI-generated.** Agency figures are read from NYC Open Data's API and summed
by a script. Council spreadsheet values are read cell by cell. PDF values are read from the PDF's
own text and ruled lines, and checked against an image of the page by ordinary image processing,
not a language model. Where a person confirmed that the page shows something the text layer
doesn't, the row says so. Every row keeps its source.

One exception, not served: the FY2009 transparency resolutions are scans with no text, so they
were read by OCR (a model). They stay in the repo as a research dataset
([`data/fy09/transparency-resolutions/`](data/fy09/transparency-resolutions/), DATA-ANOMALIES §28).

## License

Everything BetaNYC made here is under the [MIT License](LICENSE) © 2026 BetaNYC: the code
(`code/`, `mcp/`, `viz/`), the derived data (`data/`) and our documentation and research. If you
use the data, please credit BetaNYC, link to this repository and cite the City of New York as the
source.

**Not covered:** the Council and City documents in `source/` are public records, © The City of
New York, reproduced here for transparency. BetaNYC's license does not apply to them.
Third-party libraries in `viz/` keep their own licenses (see [`viz/LICENSE.md`](viz/LICENSE.md)).
The retired legacy explorer, and the first version of the agency explorer (retired in #288), were built on DataMade's
[Look at Cook](https://github.com/datamade/look-at-cook), © 2019 DataMade, Derek Eder, Nick
Rougeux and Open City, MIT License; that copyright notice is kept with the code.
NYC Open Data is under the [NYC Open Data Terms of Use](https://opendata.cityofnewyork.us/overview/#termsofuse).

## Acknowledgments

A member of the NYC Council's Finance Division staff supplied the FY2025 Council-version §254
supporting detail book and pointed us to the expense disclosure spreadsheets. Both made much of
this data possible.
<!-- CREDIT PENDING: attribution requested 2026-07-15; fill in the credit line once they reply on
     how they wish to be acknowledged. -->

A community board staffer's spreadsheet of all 59 boards' budgets found the agency explorer's
year error on 2026-11-09.

DataMade (Derek Eder, Nick Rougeux) and Open City built Look at Cook, the front end the agency
explorer and the legacy explorer are adapted from.

## Built by BetaNYC

[BetaNYC](https://beta.nyc) is New York's civic organization for public interest technology, open
data and civic design. We build tools, train the public, and advocate for a more transparent,
accountable and participatory city government.

**Support open civic data:** [beta.nyc](https://beta.nyc) · [donate](https://beta.nyc/donate) ·
[newsletter](https://beta.nyc/newsletter)
