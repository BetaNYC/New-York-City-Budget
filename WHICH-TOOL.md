# Which tool answers my question?

This repo has two halves of NYC budget data ([README](README.md)). They answer different
questions. Find yours below.

**Last revised:** 2026-11-12.

## City agency budgets

From NYC Open Data, Expense Budget ([`mwzb-yiwb`](https://data.cityofnewyork.us/d/mwzb-yiwb)).
Every agency, by unit of appropriation, adopted and modified, FY2017–FY2027. Look it up in the
explorer's [City agency budgets view](https://betanyc.github.io/New-York-City-Budget/explorer/#view=agencies),
or ask an AI assistant with the [budget MCP server](mcp/README.md) (`search_agency_budget`,
`compare_adopted_modified`). For what the City actually **spent** or paid, use Checkbook NYC or
[`@betanyc/nyc-checkbook-mcp`](https://github.com/BetaNYC/nyc-checkbook-mcp): these are budgets.

| Your question | Where to look |
|---|---|
| How much does my community board get? | Agency budgets: the [community board table](https://betanyc.github.io/New-York-City-Budget/agencies/boards.html), all 59 boards, FY2017–FY2027, with a CSV download ([`viz/agencies/data/community_boards.csv`](viz/agencies/data/community_boards.csv)). Each community board is its own agency in the budget (codes below). |
| How did an agency's budget change from one year to the next? | Agency budgets: compare its Adopted figures year by year. |
| How much did an agency's budget change during the year? | Agency budgets: compare a year's Adopted with its Modified (the MCP's `compare_adopted_modified` does it for you). |
| How big is the City's budget? | Agency budgets: the citywide total. Mind [gross vs. net](#net-and-gross). |
| How much goes to pay vs. everything else? | Agency budgets: units named Personal Services and Other Than Personal Services. |

**Community board agency codes.** Manhattan 341–352, Bronx 381–392, Brooklyn 471–488, Queens
431–444, Staten Island 491–493 (59 boards). Board *n* in a borough is the first code plus *n*−1:
Brooklyn Community Board 6 is 476.

## Council discretionary funding

From the Council's spreadsheets, its budget PDFs and NYC Open Data. Look it up in the
[Council budget explorer](https://betanyc.github.io/New-York-City-Budget/explorer/) or ask an AI
assistant through the [MCP server](mcp/README.md).

| Your question | Where to look |
|---|---|
| Which groups did my Council member fund? | Council: the expense funding disclosure (the explorer's expense awards page; MCP `search_disclosure_awards`). |
| Did this nonprofit get Council money? | Council: search by name or EIN in the disclosure and Schedule C. |
| What did the Council fund in the adopted budget, by initiative? | Council: Schedule C (MCP `search_schedule_c_awards`). |
| What did the Council change after the budget was adopted? | Council: the transparency resolutions (MCP `search_transparency_changes`). |
| Which capital projects did the Council pay for? | Council: capital designations and the capital book (MCP `search_council_capital`, `search_capital_book`). |
| Does the Council's capital money match OMB's? | Council: capital vs. OMB (MCP `compare_capital_to_omb`). |
| What reports must an agency make to the Council? | Council: Terms and Conditions (MCP `search_terms_conditions`). |

## Somewhere else

| Your question | Where to look |
|---|---|
| Was the money actually spent? Did an award become a contract? | [Checkbook NYC](https://www.checkbooknyc.com) (the Comptroller). Use its **Spending** tab for payments and its **Contracts** tab for contracts. This repo has budgets, not spending. |
| City revenue, debt, headcount, or spending over decades | [NYC Independent Budget Office, Data Center](https://www.ibo.nyc.gov/content/data-center). |
| The official printed budget | [OMB's publications](https://www.nyc.gov/site/omb/publications/publications.page) and the [Council's budget pages](https://council.nyc.gov/budget/). |

## Glossary

<a id="fiscal-year"></a>**Fiscal year (FY).** New York City's budget year runs July 1 to June 30
and is named for the year it ends. FY2026 is July 1, 2025 to June 30, 2026. Every year in this
repo is a fiscal year.

<a id="adopted"></a>**Adopted budget.** The budget the Mayor and Council agree in June, before the
fiscal year starts.

<a id="modified"></a>**Modified budget.** The adopted budget as changed during the year. In the
agency half, "Modified" is the figure as of June, near the year's end; Checkbook NYC's year-end
figure can differ slightly. The newest year's Modified is "Not yet published": the City publishes
it in the release that adopts the next year's budget.

<a id="releases"></a>**Preliminary, Executive and Adopted releases.** OMB publishes each year's
budget up to three times: Preliminary (January), Executive (April or May) and Adopted (June).
Each restates the whole budget, so they must never be added together. The agency half uses only
the June release.

<a id="year-rule"></a>**The `mwzb-yiwb` year rule.** In the Open Data release tagged
`fiscal_year = Y`, `financial_plan_amount` is FY Y and the other two amounts are FY Y−1. So
Adopted Y = `financial_plan_amount` from the June release tagged Y, and Modified Y =
`current_modified_budget_amount` from the June release tagged Y+1. Details:
[README](README.md#which-fiscal-year-each-amount-describes).

<a id="unit-of-appropriation"></a>**Unit of appropriation.** The lines the expense budget is
adopted by. An agency has one or more, often split into Personal Services and Other Than
Personal Services. The first agency explorer called these "Department" (a word left from the
Cook County tool it was adapted from), and the CSV download still names the column `Department`.

<a id="ps-otps"></a>**Personal Services (PS) and Other Than Personal Services (OTPS).** PS is pay
for the agency's staff. OTPS is everything else: supplies, contracts, rent and so on.

<a id="intra-city"></a>**Intra-city.** Money one City agency pays another for services it buys from it. The same
dollars appear in both agencies' budgets.

<a id="net-and-gross"></a>**Net and gross.** OMB's headline "net total budget" leaves intra-city
money out, so it is not counted twice. NYC Open Data rows include it, so a total added up from
Open Data is gross. FY2026 adopted: $115.9 billion net, $117,791,473,676 gross as counted in Open
Data, of which $1,884,163,949 is intra-city.

<a id="expense-capital"></a>**Expense and capital budgets.** The expense budget pays for running
the City each year: staff, services, supplies. The capital budget pays for things that last:
buildings, parks, equipment. The agency half is the expense budget. The Council half has both.

<a id="discretionary"></a>**Council discretionary funding.** Money in the budget that the Council,
not the Mayor, directs to particular organizations and programs. It is a small part of the
budget.

<a id="schedule-c"></a>**Schedule C.** The list, printed with the adopted budget, of the Council's
discretionary awards, with each award's initiative and category.

<a id="transparency-resolution"></a>**Transparency resolution.** A Council resolution, after the
budget is adopted, that adds, removes or changes discretionary awards.

<a id="disclosure"></a>**Expense funding disclosure.** The Council's spreadsheet of discretionary
awards, with each grantee's EIN, amount and clearance status. It is a later list than Schedule
C, with awards added during the year.

<a id="ein"></a>**EIN.** An organization's federal tax ID number.

<a id="omb"></a>**OMB.** The Mayor's Office of Management and Budget. It prepares the budget and
publishes the agency data in `mwzb-yiwb`.
