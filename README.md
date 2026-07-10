# New York City Budget

Machine-readable, reconciled structured data extracted from the **New York City Council's adopted budget documents** — discretionary funding (Schedule C), reporting mandates (Terms & Conditions), capital changes (Section 254), and post-adoption Transparency Resolutions — for **Fiscal Years 2025, 2026, and 2027**, plus a **historical backfill to FY2009** (see coverage note below).

Every dollar figure here was extracted **deterministically** from the Council's own PDFs and checked line by line against the documents' printed totals. The FY2027 discretionary schedule reconciles to the exact dollar: **$655,764,999**.

**Per-year processing manifest:** [`code/PARSING.md`](code/PARSING.md) records, for every fiscal year and document type, exactly which parser + invocation produces its CSVs and the reconciliation status. It is the authoritative "how do I regenerate FY_N_?" reference.

---

## Built by BetaNYC

[**BetaNYC**](https://beta.nyc) is New York's civic organization dedicated to improving lives through public interest technology, open data, and civic design. We build tools, train the public, and advocate for a more transparent, accountable, and participatory city government.

City budgets are among the most consequential public documents there are, and among the least usable — hundreds of pages of PDF tables that resist analysis. This project turns three years of them into clean, joinable data so journalists, researchers, community boards, and New Yorkers can actually ask questions of their city's spending.

**Support open civic data:** [beta.nyc](https://beta.nyc) · [donate](https://beta.nyc/donate) · [newsletter](https://beta.nyc)

---

## Licensing

This repository has two kinds of content under two different terms:

- **Source documents** (`source/`) are **© The City of New York**. They are official NYC Council adopted-budget publications, reproduced here as public records for transparency and analysis. All rights to those documents remain with the City of New York.
- **Software and derived data** — the parser code in `code/`, the extracted CSVs in `data/`, and the [analysis document](Insights-NYC-Council-Discretionary-FY25-FY27.md) — are released under the **MIT License** (see [`LICENSE`](LICENSE)). This code was **built with [Claude](https://claude.ai)**.

If you use the derived data, please attribute BetaNYC and link back to this repository, and cite the City of New York as the source of the underlying documents.

---

## How this was made

Three Python parsers (in `code/`) read the PDF text layer and emit structured rows using regular expressions, with **no hand transcription and no language-model reading of the numbers**. Each Schedule C category total is reconciled against the document's own printed `TOTAL` line, so the data can be trusted or challenged against the source. The Schedule C parser derives its category list and council-member roster from each document, so it adapts to a new fiscal year automatically.

## Repository layout

```
New-York-City-Budget/
├── README.md                                       ← you are here
├── Insights-NYC-Council-Discretionary-FY25-FY27.md ← narrative analysis
├── LICENSE                                         ← MIT, for the code + derived data
├── source/              ← official NYC Council PDFs, © City of New York
│   ├── FY08/ … FY27/    (Schedule C, Terms, Capital, transparency-resolutions/ per year)
├── data/                ← extracted, reconciled CSVs
│   ├── fy09/ … fy27/    (per year: schedule_c/, terms/, capital/, transparency-resolutions/
│   │   │                 — whichever document types exist and parse for that year)
│   │   ├── schedule_c/  discretionary expense funding
│   │   ├── terms/       Terms & Conditions (reporting mandates)
│   │   └── capital/     Section 254 capital changes
│   └── combined/        all-years roll-ups (built by code/build_combined.py)
├── code/                ← parser scripts + variants + validate_data.py (QA) + tests + PARSING.md + requirements.txt
├── mcp/                 ← prototype MCP server (see below)
└── viz/                 ← Schedule C funding visualization (see viz/README.md)
```

### `mcp/` — prototype MCP server

`mcp/` holds a **prototype** [Model Context Protocol](https://modelcontextprotocol.io) server (TypeScript + SQLite) that exposes this repo's data to MCP-capable AI clients as structured query tools — Schedule C awards (FY2015–FY2027), Terms & Conditions, §254 capital, the Transparency Resolutions (FY2010–FY2024 + FY2026), and the Legistar crosswalk. It reads the repo's own `data/` tree directly (no copied snapshot) and builds a local, git-ignored SQLite index from it, so the query layer and the data always move together. Still a prototype — see [`mcp/README.md`](mcp/README.md) for tools, scope, and how to build and run it.

## The data files

### `data/{year}/schedule_c/{year}_schedule_c_initiatives.csv` — authoritative totals
One row per Council initiative; sums exactly to each category's printed `TOTAL`.
`category, agencies, initiative, amount`

### `data/{year}/schedule_c/{year}_schedule_c_awards.csv` — who got what
One row per designation to a named organization.
`category, initiative, award_type, member, organization, program, ein, amount, agency, purpose`
- `award_type` = `member_item` (an individual Council Member's local designation) or `initiative_provider` (a provider named collectively under a citywide initiative).
- `ein` is the tax ID (digits only) — the reliable join key to IRS 990 / nonprofit data. Organization *names* are best-effort; a minority are imperfect, but the EIN and amount are exact.

### `data/{year}/schedule_c/{year}_appendix_*.csv`
Detail breakouts with a `purpose` field: `_a_aging` (Aging Discretionary), `_b_local` (Local Initiatives, includes an `agency` column), `_c_youth` (Youth Discretionary). These are subsets of the main body re-sorted by funding stream — **do not add them to the Schedule C total.**

### `data/{year}/terms/{year}_terms_and_conditions.csv`
`item_number, agency_name, agency_code, units_of_appropriation, num_units, report_deadlines, coverage_period, condition_text`

### `data/{year}/capital/{year}_capital_projects.csv`
Section 254 capital changes. `part, agency, budget_line, sub_id, boro, fy1, fy2, fy3, fy4, sponsor, title, building_code, school_code` — `fy1` is the adoption year; `fy2..fy4` are out-years; `boro`: M/X/K/Q/R.
- **FY2027 and FY2026** use the "Capital Project Detail" schedule and reconcile against printed agency subtotals.
- **FY2025** is a different document type (the "Appropriation Changes" resolution) — no borough/sub-id/sponsor columns, no subtotals to reconcile; it adds an `action` column (ELIMINATE/SUBSTITUTE/NEW PROJECT) and is labeled `NOT RECONCILABLE`.

### `data/fy26/transparency-resolutions/`
Post-adoption discretionary designations from the 10 FY2026 Transparency Resolutions (per-resolution `resoNN_transparency_designations.csv` files + a combined `fy26_transparency_all.csv`). Columns: `resolution, date, chart, fiscal_year, action, source, council_member, organization, program, ein, amount, agency, agy_num, ua, purpose, flags` — `action` ∈ designate / rescind / purpose_change; rescissions carry negative amounts. These record money the adopted budget left "to be designated post-adoption" (e.g. the FY2026 AI Community Engagement $1M). **No printed totals exist**, so they are labeled `NOT RECONCILABLE`; the only internal check is that transfers (rescind + re-designate) net to zero.

### `data/combined/`
`all_years_initiatives.csv` and `all_years_awards.csv` — the per-year files stacked with a leading `year` column for cross-year analysis.

`legistar_crosswalk.csv` — links each budget source document to its NYC Council **Legistar** legislative record (matter number, adoption date, and detail-page URL), for FY2008–FY2027. One row per document. Columns: `fiscal_year, document_type, local_file, legistar_matter_number, legistar_url, adoption_date, status, notes`.
- `document_type` ∈ `schedule_c`, `terms_conditions`, `capital_a`, `capital_b`, `transparency_reso_NN` (NN = the within-year sequence number).
- `local_file` is the repo-relative path to the source PDF (under `source/FYnn/`); it is blank for matter-only rows where the Legislation exists but no local document was downloaded. Source-relative paths are used (not `data/`) because FY2008–FY2024 are not yet parsed to structured CSVs — that PDF→CSV work is deferred; this crosswalk is the legislative-provenance index that lands first.
- `status` ∈ `confirmed` (matter individually verified, including "positional" bracket-confirmations and "inferred exhibit" Contract-Budget rows — the qualifier is kept in `notes`), `candidate` (an anchor/earliest-in-sequence or an exhibit not confirmed as a standalone matter — deliberately *not* upgraded to confirmed), or `not_located` (no Legistar matter found, or a matter with no local file, or a genuine archival gap).
- `legistar_url` is blank for the FY2015–FY2020 Transparency Resolutions, whose per-item Legistar IDs were not captured in the source research (resolve on demand from the matter number).
- Built from the three `research/2026-07-07-legistar-links-*.md` docs (which carry the per-row Legistar citations and same-day corrections). Where those docs corrected an earlier row (e.g. FY2012 Capital A, FY2013/FY2018 Schedule C), the corrected value is used and the correction is recorded in `notes`.

## Reconciliation status

| Year | Schedule C categories reconciled | Note |
|---|---|---|
| **FY2027** | **25 / 25 exact** | grand total $655,764,999 |
| **FY2026** | 24 / 25 exact | Immigrant Services: the source PDF's own line items exceed its printed total by **$800** |
| **FY2025** | 24 / 26 exact | Education: the source PDF's own line items exceed its printed total by **$50,000** |

The two "misses" are arithmetic inconsistencies **inside the official PDFs**, not extraction errors — the parser faithfully captured both the line items and the printed total, and they disagree in the source.

### Historical coverage (FY2009–FY2024)

Beyond the flagship FY2025–FY2027 set, the repo now backfills earlier years. Full per-year,
per-document-type detail (and the parser/invocation for each) is in [`code/PARSING.md`](code/PARSING.md); the headline:

- **Schedule C** — reconciled for **FY2015–FY2024** (**FY2015** via the dedicated `parse_schedule_c_fy15.py`,
  reconciled **24/24**; **FY2016–FY2024** via `parse_schedule_c.py`) and **FY2009–FY2014**
  (initiatives-only, via `parse_schedule_c_legacy.py` — the early-era documents carry no award-level
  EIN tables; FY2015 and later DO). FY2008 remains open (see PARSING.md).
- **§254 Capital (Capital Project Detail)** — reconciled **23/23–32/32** for **FY2020, FY2022, FY2023, FY2024**
  (via `parse_capital_detail.py`).
- **Terms & Conditions** — extracted for **FY2015–FY2024** (via `parse_terms_legacy.py`; T&C print no totals).
- **Transparency Resolutions** — extracted for **FY2010–FY2024** (no printed totals). Financial columns
  (EIN/amount/agency/date/action) are reliable in every year; organization/member/program *text* is
  low-confidence in the older glued-text-layer years (FY2010–FY2013), flagged per-year in each
  `*_reconciliation.txt`. FY2009 (scanned, no text layer) and FY2013 resolutions 07/10/11 (`.doc`) are blocked.

**Capital (Section 254):** FY2026 reconciles **31/31** agency subtotals (amount + project count); FY2027 reconciles **24/26**; FY2025 is a different document type with no subtotals (`NOT RECONCILABLE`). **Transparency Resolutions:** no printed totals (`NOT RECONCILABLE`); transfers net to zero as expected. See each `*_reconciliation.txt` for details.

**Data QA:** beyond per-file reconciliation, `code/validate_data.py` runs row-level and cross-file
integrity checks (schema, EIN validity + per-year coverage, amount/sign sanity, fiscal-year
integrity, duplicate detection, column-bleed heuristic, and a reconciliation roll-up) over the whole
`data/` tree and writes a dated `data/QA-REPORT.md`. Latest run: 0 hard failures, 100% EIN coverage
on every EIN-bearing file. Details in [`code/PARSING.md`](code/PARSING.md).

## Known limitations

- Some `initiative_provider` award rows have imperfect organization *names* (EIN + amount are correct).
- Borough delegations ("Brooklyn", "Queens", …) appear in the `member` column as collective sponsors.
- **FY2025 capital is not row-comparable to FY2026/FY2027** — it is the "Appropriation Changes" resolution (a different document type), lacking borough/sub-id/sponsor columns and per-agency subtotals. FY2026 and FY2027 capital share a schema and reconcile.
- **Transparency Resolutions have no printed totals** to reconcile against (only the transfer net-out check); ~0.2% of rows have an imperfect organization name (EIN + amount are recoverable).
- Category names differ across years (FY2025 has a standalone "Libraries" that later folds into "Cultural Organizations"). Normalize before comparing.

## Reproduce or extend to a new year

Requires Python 3 with the packages in `code/requirements.txt` (`pypdf`, `cryptography`):

```bash
python code/parse_schedule_c.py <ScheduleC.pdf> --outdir data/fy28/schedule_c --prefix fy28
python code/parse_terms.py       <Terms.pdf>     --outdir data/fy28/terms      --prefix fy28
python code/parse_capital.py     <Capital.pdf>   --outdir data/fy28/capital     --prefix fy28 \
       --roster data/*/schedule_c/*_schedule_c_awards.csv
```

Always read the generated `*_reconciliation.txt` to confirm a parse before trusting a new year.

**Earlier years and other document types use variant parsers** (`parse_schedule_c_legacy.py`,
`parse_terms_legacy.py`, `parse_capital_detail.py`, `parse_transparency_reso.py`) — the exact
parser and invocation for each fiscal year is in [`code/PARSING.md`](code/PARSING.md). After
regenerating any Schedule C year, rebuild the cross-year roll-ups with
`python code/build_combined.py`.

## How this relates to other NYC budget data sources

This repository is one piece of a larger NYC budget-data ecosystem. It is deliberately narrow: **designation-level, who-got-what data from the Council's adopted budget** — the organization, the sponsoring Council member, the amount, the implementing agency, and the recipient's EIN. It is not a source of citywide fiscal totals, revenue, or long-run spending trends. Here is where the neighbors fit.

| Source | What it's best for | Overlap with this repo |
|---|---|---|
| **This repo** | Council discretionary (Schedule C) awards, Terms & Conditions, Section 254 capital changes, Transparency Resolutions, and a Legistar crosswalk, at the organization/EIN level | — |
| **[NYC Independent Budget Office — Data Center](https://www.ibo.nyc.gov/content/data-center)** | The aggregate fiscal picture: citywide and agency-level expenditures and revenue (FY1980+), capital expenditures (since 1985), debt, headcount, education spending, tax data; plus IBO's fiscal analyses and budget-option reports | **None at the award level.** IBO has no discretionary/Schedule C/member-item data. It is the fiscal *context* this repo's who-got-what data sits inside. Most of the Data Center is also on NYC Open Data under agency "NYC Independent Budget Office (IBO)." |
| **[NYC Open Data — City Council Discretionary Funding](https://data.cityofnewyork.us/dataset/4d7f-74pe) (`4d7f-74pe`)** | Award-level Council discretionary funding, FY2009–FY2021, Council-published | **Directly overlaps FY2015–FY2021.** It stopped updating April 2021, so this repo is the machine-readable source for **FY2022–FY2027** and adds source-reconciled totals plus Terms, Capital, Transparency, and Legistar provenance. |
| **[NYC Checkbook](https://www.checkbooknyc.com) (Comptroller)** | Actual spending and registered contracts | Complements this repo: join on EIN to ask whether a designation became a paid contract. |
| **[NYC Council Finance Division](https://council.nyc.gov/budget/) / OMB** | The primary source documents this repo parses | This repo is the structured, reconciled extraction of those documents. |

In short: **IBO tells you what the City spends, raises, and owes in aggregate over decades; this repo tells you which organizations the Council funded, and how much, in the adopted budget.** Neither IBO nor NYC Open Data (after FY2021) publishes the second thing as machine-readable data. That is the gap this repository fills. A detailed source-by-source crosswalk (including how this data can be joined to IBO's agency-level fiscal tables) is in [`research/2026-07-08-ibo-data-center-crosswalk.md`](research/2026-07-08-ibo-data-center-crosswalk.md).

**A companion BetaNYC visualization** turns this repo's Schedule C data into an interactive explorer — see [`viz/`](viz/). It shares its toolkit (DataMade's [Look at Cook](https://github.com/datamade/look-at-cook)) with BetaNYC's **[citywide expense-budget explorer](https://github.com/BetaNYC/nyc-budget-viz)**, which visualizes the full ~$114B adopted/modified budget across all agencies — the aggregate fiscal side this repo deliberately does not cover.

## Future work

- **Schedule C vs. actuals.** Compare discretionary designations here against NYC
  Checkbook spending/contract data — do designations actually convert into paid
  contracts, and at what lag or drop-off rate?
- **Capital project lifecycle.** Trace a Section 254 capital line from budget proposal
  through adoption (this repo) to actual payment and completion (Checkbook capital
  commitments) — an end-to-end view of how capital dollars move from planning to
  money spent.

See `research/` for active and lodged scoping plans, including closing the
FY2022–FY2024 gap between this repo's PDF-extracted years and NYC Open Data's
FY2009–FY2021 historical archive.

---

*Source: NYC Council Finance Division, adopted budget Schedule C, Terms & Conditions, and Section 254 capital changes, FY2025–FY2027, [council.nyc.gov](https://council.nyc.gov/budget/). Structured and analyzed by [BetaNYC](https://beta.nyc).*
