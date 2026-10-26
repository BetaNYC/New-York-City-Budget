# New York City Budget

Clean, checked data on how the **New York City Council** gives out money: which organizations it
funds, for how much, through which agency, and at which Council member's request. Built by
[BetaNYC](https://beta.nyc) from the Council's own spreadsheets, its budget PDFs and NYC Open
Data. Every row says where it came from.

- **Search it in a browser:** the [budget explorer](https://betanyc.github.io/New-York-City-Budget/explorer/).
- **Ask an AI assistant:** the [`@betanyc/nyc-budget-mcp`](mcp/README.md) server.
- **Download it:** the CSVs in [`data/`](data/), or the [data releases](https://github.com/BetaNYC/New-York-City-Budget/releases).
- **Report a problem:** [GitHub issues](https://github.com/BetaNYC/New-York-City-Budget/issues).

**Last revised:** 2026-10-24.

---

## What this project is

City budgets are among the most important public documents there are, and among the hardest to
use. The Council publishes who gets its discretionary and capital money as spreadsheets and as
long PDF tables. This project turns them into data you can search, join and check, so
journalists, researchers, community boards and New Yorkers can ask questions of their city's
spending.

It is narrow on purpose: **who got what**, at the level of the organization and its tax ID (EIN).
It is not a source for citywide totals, revenue or spending over decades (see
[other sources](#how-this-relates-to-other-nyc-budget-data)).

## The data sources

There are three, and each row says which one it came from.

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
checked process ([`PDF-RECIPE.md`](PDF-RECIPE.md)):

| Family | What it is | Years |
|---|---|---|
| Schedule C | The discretionary awards as adopted, with the initiative and category | FY2018–FY2027 |
| Transparency resolutions | Changes made after adoption: new awards, rescissions, changes of purpose | FY2018–FY2026 |
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

The explorer also says, for each award and capital row, whether it is on NYC Open Data, and the
date of the copy it checked.

## Ask an AI assistant: the MCP server

[`@betanyc/nyc-budget-mcp`](https://www.npmjs.com/package/@betanyc/nyc-budget-mcp) is a
[Model Context Protocol](https://modelcontextprotocol.io) server. It lets an AI assistant (Claude
Desktop, Claude Code and others) search this data and cite each row. Add it to your client's
config:

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

The npm package holds the server's code and its spreadsheet index (`dist` and `data/budget.db`). The checked PDF tables are an **optional
download** (about 17 MB) from this repo's data releases:

```bash
npx @betanyc/nyc-budget-mcp download --pdf-tables          # the tables
npx @betanyc/nyc-budget-mcp download --pdf-tables --pdfs   # the tables and the PDFs (148 MB more)
```

Or set `"env": { "NYC_BUDGET_PDF_DATA": "on" }` in the config, and the server downloads them when
it starts, if none are installed (run `download` again to get a newer release). Until then, the four PDF tools say how to add them. Every file is checked against its
published sha256. Full details: [`mcp/README.md`](mcp/README.md); changes:
[`mcp/CHANGELOG.md`](mcp/CHANGELOG.md).

**How text searches match.** Name and text filters (organization, member, purpose, title and so on)
ignore case and accents. A term of 3 or fewer letters and digits matches whole words only, so `AI`
finds "AI Training Program" but not "Jamaica" or "AIDS". Longer terms match anywhere, so `Fellow`
also finds "Fellowship". Each tool takes `whole_word: true` or `false` to choose either way, and
the answer says when it matched whole words. Exact filters (EIN, budget line) are unchanged.
The capital book's `project_id` and the transparency `resolution_number` always match anywhere,
so fragments like `CC1` work.
A name search finds only the rows whose text matches, so report it as "at least".

## Search in a browser: the explorer

The **[budget explorer](https://betanyc.github.io/New-York-City-Budget/explorer/)** searches the
same data the MCP serves, in your browser. It has pages for expense awards, years, comparing
years, capital, capital vs. OMB, and one for each PDF family (Schedule C, transparency
resolutions, the capital book, organizations in the capital book, Terms and Conditions). Each page
loads its data when you open it. A test checks that the explorer and the MCP give the same rows
and totals.

Every spreadsheet row links to its file. Every PDF row opens its page with the row highlighted.
The "About the data" page explains what each label means. Code:
[`viz/explorer/`](viz/explorer/README.md).

## How a year of PDFs is checked

[`PDF-RECIPE.md`](PDF-RECIPE.md) is the step-by-step. In short:

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

## How to contribute

- **Found something wrong?** Open an [issue](https://github.com/BetaNYC/New-York-City-Budget/issues)
  with the fiscal year, the row (or the explorer link) and what the source shows. Check
  [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) first: many oddities are in the source and already
  listed there.
- **Help review a year.** Build the explorer with its Review tab
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

## What is not done yet

Open work is tracked in two epics: [#101](https://github.com/BetaNYC/New-York-City-Budget/issues/101)
(read every PDF, one year at a time) and [#190](https://github.com/BetaNYC/New-York-City-Budget/issues/190)
(serve the checked tables). The bugs the FY2018–FY2027 reviews found (epic
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

## Repository layout

```
New-York-City-Budget/
├── README.md, PDF-RECIPE.md, DATA-ANOMALIES.md, DATA-DICTIONARY.md
├── source/      the Council's and City's documents (PDFs, workbooks, Open Data pulls), © City of New York
├── data/
│   ├── fyNN/expense_disclosure/   the Council's disclosure, per year
│   ├── fyNN/pdf/                  the checked PDF tables, per year and family
│   ├── capital/                   the Council's capital lists, and the comparison with OMB
│   ├── pdf_years.csv              each PDF family-year's status
│   ├── council_questions.csv      questions to Council Finance, with dates
│   └── retired/                   the old PDF parser's output, kept for history, never served
├── config/      one file per PDF family and year
├── code/        the readers, checks and tests (Python)
├── mcp/         the MCP server (TypeScript)
├── viz/         the GitHub Pages site and the explorer
└── research/    plans, review records and research notes
```

## History, briefly

- **1.x (July–August 2026):** the first MCP served tables an early parser read from the PDFs. We
  later found it lost and merged rows without saying so (DATA-ANOMALIES §20, §21).
- **2.0.0 (2026-10-17):** we stopped serving anything read from a PDF and moved to the Council's
  spreadsheets and NYC Open Data (DATA-ANOMALIES §27). The old Schedule C explorer stays online,
  frozen, at [`legacy.html`](https://betanyc.github.io/New-York-City-Budget/legacy.html), with a
  banner saying not to cite it.
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

More: [`mcp/CHANGELOG.md`](mcp/CHANGELOG.md), [`data/retired/README.md`](data/retired/README.md),
[`code/PARSING.md`](code/PARSING.md) (how each old file was made), and
[this README as it was before 2.0.2](https://github.com/BetaNYC/New-York-City-Budget/blob/15d1f8f/README.md),
which describes the old files in detail.

## How this relates to other NYC budget data

| Source | Best for | Overlap with this repo |
|---|---|---|
| **This repo** | Council awards and capital designations, at the organization and EIN level | — |
| **[NYC Independent Budget Office, Data Center](https://www.ibo.nyc.gov/content/data-center)** | Citywide and agency spending and revenue over decades, debt, headcount | None at the award level. IBO is the context this data sits in |
| **[NYC Open Data: City Council Discretionary Funding](https://data.cityofnewyork.us/dataset/4d7f-74pe)** | Council awards, FY2009–FY2021 | Overlaps the disclosure for FY2009 and FY2011–FY2021; stopped updating in April 2021. Compared row by row in [`research/2026-10-14-open-data-vs-disclosure-diff.md`](research/2026-10-14-open-data-vs-disclosure-diff.md) |
| **[NYC Checkbook](https://www.checkbooknyc.com)** (Comptroller) | Actual spending and registered contracts | Join on EIN to ask whether an award became a contract |
| **[NYC Council budget pages](https://council.nyc.gov/budget/)** | The documents this repo reads | This repo is the structured, checked version |

BetaNYC's [citywide expense-budget explorer](https://github.com/BetaNYC/nyc-budget-viz) covers
the whole adopted budget across agencies. A source-by-source crosswalk:
[`research/2026-07-08-ibo-data-center-crosswalk.md`](research/2026-07-08-ibo-data-center-crosswalk.md).

## AI use

BetaNYC uses AI tools openly and with people accountable for the result. The code here was built
by AI agents (Anthropic's Claude) working under the direction and review of BetaNYC staff.

**The figures are not AI-generated.** Spreadsheet values are read cell by cell. PDF values are
read from the PDF's own text and ruled lines, and checked against an image of the page by
ordinary image processing, not a language model. Where a person confirmed that the page shows
something the text layer doesn't, the row says so. Every row keeps its source.

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
NYC Open Data is under the [NYC Open Data Terms of Use](https://opendata.cityofnewyork.us/overview/#termsofuse).

## Acknowledgments

A member of the NYC Council's Finance Division staff supplied the FY2025 Council-version §254
supporting detail book and pointed us to the expense disclosure spreadsheets. Both made much of
this data possible.
<!-- CREDIT PENDING: attribution requested 2026-07-15; fill in the credit line once they reply on
     how they wish to be acknowledged. -->

## Built by BetaNYC

[BetaNYC](https://beta.nyc) is New York's civic organization for public interest technology, open
data and civic design. We build tools, train the public, and advocate for a more transparent,
accountable and participatory city government.

**Support open civic data:** [beta.nyc](https://beta.nyc) · [donate](https://beta.nyc/donate) ·
[newsletter](https://beta.nyc/newsletter)
