# City agency budgets: `agencies/` (forwarding page, data and FAQ)

> **This folder is the City agency budgets half of
> [New-York-City-Budget](../../README.md)** (epic #272). It came from
> [BetaNYC/nyc-budget-viz](https://github.com/BetaNYC/nyc-budget-viz) `main` at `b90f922` by
> `git subtree add` (#265), so its history is kept.

**Since #288 (2026-11-12) the City agency budgets are a view of the explorer:**
[`explorer/#view=agencies`](https://betanyc.github.io/New-York-City-Budget/explorer/#view=agencies)
(code: [`viz/explorer/src/views/Agencies.jsx`](../explorer/src/views/Agencies.jsx)). It reads the
same `agency_budget` table as the budget MCP server, built by
[`mcp/scripts/agency-budget.mjs`](../../mcp/scripts/agency-budget.mjs), so the site and the MCP
can't disagree. The old app here (DataMade's Look at Cook front end: Backbone, jQuery,
Highcharts, DataTables) is retired.

## What is in this folder

```
index.html            forwards every old link to the explorer's view (see below), with a
                      plain link for visitors without JavaScript
faq.html              questions and answers about City agency budgets
boards.html           every community board's budget in one table (#269)
data/
  nyc_budget.csv      every agency x unit of appropriation, FY2017 on (same address and columns
                      as before; written from the index, see data/SCHEMA.md)
  community_boards.csv   the community boards table (code/build_community_boards.py)
  SCHEMA.md           the CSV's columns and the year rule
css/, fonts/, images/ the FAQ's stylesheets and the sharing image
js/budget_helpers.js  kept only so the explorer's old-link test runs the old slug rule from it;
                      no page loads it
```

## Old links

GitHub Pages can't redirect on a `#fragment` (browsers never send it to the server), so
`index.html`'s script reads the old link and forwards it:

| Old link | Goes to |
|---|---|
| `agencies/#?year=2019` | `explorer/#view=agencies&abfy=2019` |
| `agencies/#fund-detail/police-department?year=2025` | the Police Department, FY2025 |
| `agencies/#fund-detail/police-department/operations?year=2024` | its unit 001 Operations |
| `agencies/#control-officer-detail/...` | the same as `fund-detail` (#266) |

The explorer matches the old name slug against every name each agency ever had (agency 866's old
name, DEPARTMENT OF CONSUMER AFFAIRS, still works). When two units of one agency share a name
(39 cases, for example City Council's two "Committee on the Aging" units, 600 and 800), it asks
which one instead of guessing. Tests: `viz/explorer/e2e/agencies.retired.spec.js` and
`viz/test_agencies_retired.py`.

## Data

- **Source:** [NYC Open Data, Expense Budget](https://data.cityofnewyork.us/d/mwzb-yiwb)
  (`mwzb-yiwb`), the committed snapshot in [`source/agency-budget-qa/`](../../source/agency-budget-qa/README.md).
- **The year rule:** Adopted Y = `financial_plan_amount` from the June release tagged Y;
  Modified Y = `current_modified_budget_amount` from the June release tagged Y+1. Coded once, in
  the MCP's loader. Full notes: [`data/SCHEMA.md`](data/SCHEMA.md).
- **Checked:** FY2026 adopted total = **$117,791,473,676**, matching OMB's printed FY2026
  Adopted Budget (net $115,907,309,727 + intra-city $1,884,163,949), and every cell is
  recomputed independently by `code/qa_agency_budget.py`.

> **Correction (2026-11-09).** Before this date every year in the old explorer was labeled one
> year late: "Adopted 2026" was really FY2025. Details: [`data/SCHEMA.md`](data/SCHEMA.md).

## Regenerating the CSV

```bash
python3 code/fetch_agency_budget_qa.py     # after the City publishes a new June release
python3 code/agency_budget_cleanup.py      # index build, then data/nyc_budget.csv
python3 code/qa_agency_budget.py           # independent check, every cell
```

Needs Node 22+ and `npm ci` in `mcp/` and `viz/explorer/`.

## About BetaNYC

This project is built and maintained by [BetaNYC](https://beta.nyc), New York's
civic technology and open-data community. We work to improve lives in New York
through civic design, technology, data, and public-interest technology.

**Come do civic tech with us.** We run public events, meetups, and hands-on
data classes throughout the year — including [NYC School of Data](https://www.schoolofdata.nyc/)
and [CityCamp NYC](https://citycamp.nyc), and we host frequent civic-tech gatherings. See what's coming up on our
[events calendar](https://www.beta.nyc/events/).

**Sustain this work.** This project is free and open source. To help keep this work going and find BetaNYC's tools, please consider [donating and becoming a Beta Builder](https://beta.nyc/donate).

## Building on this? Tell us!

If you build something with this project, we'd love to hear about it. We can help other New Yorkers find it. BetaNYC publishes a weekly newsletter, *This Week in NYC's Civic Technology and Open Data*.

- **[Subscribe to the newsletter](https://beta.nyc/newsletter)** to keep up with NYC civic tech, open data, and public-interest technology.
- **Built something, or found a story worth sharing?** [Submit a link for the newsletter](https://www.beta.nyc/newsletter-inbox/) and we'll consider it for an upcoming issue.

## Related BetaNYC projects

BetaNYC maintains a growing suite of open-source tools for NYC and NYS civic data — see the full directory at **[beta.nyc/ai-tools](https://beta.nyc/ai-tools)**.

This folder is part of **[New York City Budget](https://github.com/BetaNYC/New-York-City-Budget)**: the City agency budgets (every agency, about $118B gross for FY2026) beside the Council's discretionary funding (about $656M), with the [`@betanyc/nyc-budget-mcp`](https://github.com/BetaNYC/New-York-City-Budget/tree/main/mcp) server answering both.

## Attribution

The first version of this tool (retired in #288) was adapted from
**[Look at Cook](https://github.com/datamade/look-at-cook)** by DataMade, Derek Eder, Nick
Rougeux, and Open City. The original front-end is © 2019 DataMade and released under the MIT
License, preserved here in [`LICENSE.md`](LICENSE.md) with the files that remain (the FAQ's
stylesheet and `js/budget_helpers.js`). BetaNYC's adaptation — the NYC
data pipeline, the cleaned dataset, and the NYC-specific copy — is likewise available under the
same terms. If you reuse this, keep the DataMade copyright and license intact.
