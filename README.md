# New York City Budget

> **What changed in 2.0**
>
> BetaNYC's budget MCP ([`@betanyc/nyc-budget-mcp`](mcp/README.md) 2.0.0) and its GitHub Pages site now use **structured sources only**: the NYC Council's own expense funding disclosure spreadsheets (FY2009 and FY2011–FY2027) and its capital designations from the Council's capital workbooks and NYC Open Data (FY2015–FY2017, FY2019–FY2027). Every disclosure (award) answer names, for each year, the Council file and sheet it came from and the date we retrieved it; every capital answer names each year's source (Council workbook or NYC Open Data), its retrieval date and sha256; the OMB comparison cites the comparison file and OMB's release.
>
> - **New tools:** `search_council_capital`, `compare_capital_to_omb`; `search_disclosure_awards` now covers FY2009, FY2011 and FY2012.
> - **Removed:** `search_awards`, `get_awards_by_ein`, `search_transparency_resolutions`, `search_capital_projects`, `get_terms_conditions`, `get_legistar_link`. See the [migration table](mcp/README.md#migrating-from-1x).
> - **Retired, kept for history, not shipped:** everything extracted from the adopted-budget PDFs (Schedule C and its appendices, Terms & Conditions, §254 capital, transparency resolutions, `data/combined/`, `data/recovered/`). The sections below that describe those files describe that historical record.
> - **Not included:** FY2010 disclosure (the Council's archived workbook is incomplete against NYC Open Data) and FY2018 capital (no source found).
> - **On 1.x?** Use `npx -y @betanyc/nyc-budget-mcp@2` and re-check any figure you published from 1.x. Full notes: [`mcp/CHANGELOG.md`](mcp/CHANGELOG.md).

Machine-readable data on how the **New York City Council** designates money, built from the Council's own **spreadsheets** and **NYC Open Data**, not from PDFs:

- **Expense funding disclosure** (`data/fyNN/expense_disclosure/`): every award-level designation the Council publishes, FY2009 and FY2011–FY2027, 156,544 rows, with the grantee, EIN, amount, clearance status and mailing address. FY2013–FY2027 come from the Council's Research & Data site; FY2009, FY2011 and FY2012 from the Council's own workbooks preserved by the Internet Archive.
- **Capital designations** (`data/capital/`): the Council's capital lists, FY2015–FY2017 and FY2019–FY2027, 16,916 rows, from the Council's capital workbooks and NYC Open Data `t474-a92g`, with a by-budget-line comparison to OMB's adopted capital budget (1,425 line-year comparisons over 515 budget lines, FY2019–FY2027).

Each row keeps the workbook, sheet and row it came from, and every file's sha256 is recorded. The parsers read the spreadsheets cell by cell; no number is typed in by hand or read by a language model.

> **GitHub Pages:** [betanyc.github.io/New-York-City-Budget](https://betanyc.github.io/New-York-City-Budget/) now opens on a notice pointing to the structured data. The new **[budget explorer](https://betanyc.github.io/New-York-City-Budget/explorer/)** searches the same data the MCP serves, in the browser, with every row linked to its source spreadsheet ([`viz/explorer/`](viz/explorer/README.md)). The old Schedule C explorer **stays online, frozen** as of 2026-10-16 at `legacy.html`, with a banner saying not to cite it: its figures came from the PDF parser this release retires. See [`viz/README.md`](viz/README.md).

**Retired in 2.0, kept for history:** the earlier versions of this repository parsed the Council's adopted-budget **PDFs** (Schedule C, Terms & Conditions, Section 254 capital, transparency resolutions) for FY2009–FY2027. Those files and their parsers are still here (`data/fyNN/schedule_c/`, `terms/`, `capital/`, `data/combined/`, `data/recovered/`), but we found errors in that extraction, and 2.0 neither serves nor ships them. The sections below that describe them describe that historical record.

**Per-year processing manifest:** [`code/PARSING.md`](code/PARSING.md) records, for every fiscal year and document type (structured and retired), exactly which parser + invocation produces its CSVs and the reconciliation status. It is the authoritative "how do I regenerate FY_N_?" reference.

---

## Built by BetaNYC

[**BetaNYC**](https://beta.nyc) is New York's civic organization dedicated to improving lives through public interest technology, open data, and civic design. We build tools, train the public, and advocate for a more transparent, accountable, and participatory city government.

City budgets are among the most consequential public documents there are, and among the least usable. This project gathers the Council's own discretionary and capital designation spreadsheets, FY2009 onward, into clean, joinable data with provenance on every row, so journalists, researchers, community boards, and New Yorkers can actually ask questions of their city's spending.

**Support open civic data:** [beta.nyc](https://beta.nyc) · [donate](https://beta.nyc/donate) · [newsletter](https://beta.nyc)

---

## Licensing

This repository has two kinds of content under two different terms:

- **Source documents** (`source/`) are **© The City of New York**. They are official NYC Council adopted-budget publications, reproduced here as public records for transparency and analysis. All rights to those documents remain with the City of New York.
- **Everything BetaNYC made** — the code in `code/`, `mcp/` and `viz/`, the extracted data in `data/`, and our documentation and research, including the [analysis document](Insights-NYC-Council-Discretionary-FY25-FY27.md) — is released under the **MIT License** (see [`LICENSE`](LICENSE)). This code was **built with [Claude](https://claude.ai)**.

If you use the derived data, please attribute BetaNYC and link back to this repository, and cite the City of New York as the source of the underlying documents.

---

## How this was made

**2.0 (served):** `code/parse_expense_disclosure.py` reads each disclosure workbook (`.xlsx`, and `.xls` for the archived years) cell by cell, keeps every published value, and writes one record shape for every year; `code/build_capital_council.py` does the same for the capital workbooks and NYC Open Data. Both check each file's sha256 against its manifest and stop rather than publish a partial year. `code/validate_data.py` and the audits (`data/DISCLOSURE-AUDIT.md`, `data/capital/CAPITAL-AUDIT.md`) re-derive the outputs with separate scripts.

**Retired (PDF, kept for history):** three Python parsers (in `code/`) read the PDF text layer and emit structured rows using regular expressions, with **no hand transcription and no language-model reading of the numbers**. (One documented exception: the FY2009 Transparency Resolutions are scans with no text layer, so they are OCR'd — see "AI use" below.) Each Schedule C category total is reconciled against the document's own printed `TOTAL` line, so the data can be trusted or challenged against the source. The Schedule C parser derives its category list and council-member roster from each document, so it adapts to a new fiscal year automatically.

## Repository layout

```
New-York-City-Budget/
├── README.md                                       ← you are here
├── Insights-NYC-Council-Discretionary-FY25-FY27.md ← narrative analysis
├── LICENSE                                         ← MIT, for the code, derived data and docs
├── source/              ← official NYC Council documents, © City of New York
│   ├── FY08/ … FY27/    (Schedule C, Terms, Capital, transparency-resolutions/ per year — PDFs)
│   ├── expense-funding-disclosure/  (Council RnD award-level expense spreadsheets, FY2013–FY2027)
│   ├── gpp/             (budget PDFs from the City's Government Publications Portal: OMB's capital
│   │                     supporting-detail books FY2009–FY2027, not yet reviewed; see its README)
│   ├── wayback-council/ (Council files recovered from the Internet Archive: FY2009–FY2012 disclosure
│   │                     workbooks, FY15–FY17 + FY26 capital databases; manifests for every capture)
│   ├── open-data-4d7f-74pe/  (manifest, metadata and data dictionary of the NYC Open Data pull,
│   │                     and a 5-column key extract used for od_mocs_id; the full rows stay out of git)
│   ├── open-data-t474-a92g/, open-data-46m8-77gv/, open-data-2cmn-uidm/  (Council capital,
│   │                     OMB capital budget and commitment plan: rows as gzip CSV + manifests)
│   └── census-zcta/     (provenance of the Census 2020 ZCTA file used to check disclosure ZIPs)
├── data/                ← extracted, reconciled CSVs
│   ├── fy09/ … fy27/    (per year: schedule_c/, terms/, capital/, transparency-resolutions/
│   │   │                 — whichever document types exist and parse for that year)
│   │   ├── schedule_c/  discretionary expense funding        [PDF-derived: retired in 2.0, not shipped]
│   │   ├── terms/       Terms & Conditions (reporting mandates) [PDF-derived: retired]
│   │   ├── capital/     Section 254 capital changes            [PDF-derived: retired]
│   │   └── expense_disclosure/  the Council's award-level disclosure workbooks, FY2009, FY2011–FY2027 (served by the MCP)
│   ├── capital/         Council capital designations FY2015–FY2017, FY2019–FY2027 from structured sources,
│   │                     OMB reference tables, reconciliation by budget line (no PDF data; served by the MCP)
│   ├── reference/       lookup tables derived from outside sources (Census ZCTA → state; Legistar roster extract)
│   └── combined/        all-years roll-ups (built by code/build_combined.py) [PDF-derived: retired]
├── code/                ← parser scripts + variants + validate_data.py (QA) + tests + PARSING.md + requirements.txt
├── mcp/                 ← MCP server, 2.0: structured sources only (see below)
└── viz/                 ← GitHub Pages site: a notice, the budget explorer (viz/explorer/), and the old Schedule C explorer, online but frozen (viz/README.md)
```

### `source/expense-funding-disclosure/` — Council RnD award-level expense data

Alongside the adopted-budget PDFs, the repo includes the NYC Council Research & Data division's
**expense funding disclosure** spreadsheets — the Council's own machine-readable, award-level
discretionary **expense** files, **FY2013–FY2027**, as published at
[rnd.council.nyc.gov/expense_funding](https://rnd.council.nyc.gov/expense_funding/) (first
retrieved 2026-07-15; all 16 files re-pulled 2026-10-12, when FY2025–FY2027 and the capital
workbook had changed). Because they are already tabular, they need no PDF text extraction.

They were first added beside the parsed Schedule C data, which they complement: they carry fields the PDFs do not expose cleanly — a **MOCS ID#** (the
Mayor's Office of Contract Services identifier, present FY2024+; not stable across snapshots, and
its join to registered contracts and Checkbook spending is unverified), the grantee **EIN** and full **mailing address** (geocodable to council
district), and a **Cleared/Pending** clearance status. In effect they are the live continuation of
NYC Open Data's **City Council Discretionary Funding** dataset (`4d7f-74pe`), which stopped updating
in April 2021. Provenance, per-file manifest, schema (16/17/18-column evolution), and data-quality
notes are documented in
[`source/expense-funding-disclosure/README.md`](source/expense-funding-disclosure/README.md), and
every file's SHA-256 is in its [`MANIFEST.csv`](source/expense-funding-disclosure/MANIFEST.csv).
They are published as data in `data/{year}/expense_disclosure/` (see below).

### `mcp/` — MCP server (2.0: structured sources only)

`mcp/` holds a [Model Context Protocol](https://modelcontextprotocol.io) server (TypeScript + SQLite), published as [`@betanyc/nyc-budget-mcp`](https://www.npmjs.com/package/@betanyc/nyc-budget-mcp). Since 2.0.0 it serves only structured data: `search_disclosure_awards` (the Council's expense funding disclosure, FY2009 and FY2011–FY2027, with each year's source and retrieval date, the early-snapshot years and FY2010's exclusion stated), `search_council_capital` (`data/capital/`, FY2015–FY2017 and FY2019–FY2027), `compare_capital_to_omb` (the by-budget-line comparison with OMB's adopted capital budget) and `list_available_fiscal_years`. The PDF-derived tools were removed; a test fails if any PDF-derived file is read by the index build or shipped in the package. It builds a local, git-ignored SQLite index from this repo's own files, so the query layer and the data move together. See [`mcp/README.md`](mcp/README.md).

## The data files

> **Retired in 2.0 (PDF-derived):** the `schedule_c/`, `terms/`, `capital/` (per-year §254), `transparency-resolutions/`, `data/combined/` and `data/recovered/` files described below were extracted from the adopted-budget PDFs. They stay in the repository as a historical record, are no longer served by the MCP or shown on the Pages site, and should not be cited as current. The structured datasets are `data/{year}/expense_disclosure/`, `data/disclosure_years.csv` and `data/capital/`.

### `data/{year}/schedule_c/{year}_schedule_c_initiatives.csv` — authoritative totals
One row per Council initiative; sums exactly to each category's printed `TOTAL`.
`category, agencies, initiative, amount`

### `data/{year}/schedule_c/{year}_schedule_c_awards.csv` — who got what
One row per designation to a named organization.
`category, initiative, award_type, member, organization, program, ein, amount, agency, purpose`
- `award_type` = `member_item` (an individual Council Member's local designation) or `initiative_provider` (a provider named collectively under a citywide initiative).
- `ein` is the tax ID (digits only) — the reliable join key to IRS 990 / nonprofit data. Organization *names* are best-effort; a minority are imperfect. **For 64 remaining rows the name is not merely imperfect: the row boundary was lost during extraction, so the row's `amount` may belong to a different organization than the one `organization` names.** A further 140 rows carry purpose prose instead of a name. Both are flagged by `code/validate_data.py` (`org_merged` / `org_prose`) and listed per file in [`data/QA-REPORT.md`](data/QA-REPORT.md). 5,450 cells were repaired on 2026-08-12/13 from the Council's own disclosure — see [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) §20 and §21.

### `data/{year}/schedule_c/{year}_appendix_*.csv`
Detail breakouts with a `purpose` field: `_a_aging` (Aging Discretionary), `_b_local` (Local Initiatives, includes an `agency` column), `_c_youth` (Youth Discretionary). **These are separate designations, not a re-sort of the main body: adding appendix rows to the body's award rows double-counts nothing.** Settled for every year from the Council's own disclosure, which files each designation under its stream: matching the body first, at least 96% of appendix rows still find a designation of their own in every year that has appendix rows (FY2027: 3,796 of 3,860 against the 2026-10-12 snapshot; all 3,860 against the 2026-07-15 one); the exceptions are listed key by key in [`data/DISCLOSURE-COVERAGE.md`](data/DISCLOSURE-COVERAGE.md) §4. (This is about award rows. The printed category `TOTAL`s, such as FY2027's $655,764,999, are the category summary and are not a sum of award rows.) FY2015–FY2017 and FY2019–FY2020 appendix CSVs are header-only because the parser missed them (the PDFs do print them, with bare amounts; GitHub #59); `data/recovered/schedule_c_appendix_recovered.csv` holds those years from the disclosure.

### `data/{year}/expense_disclosure/{year}_expense_awards.csv` — the Council's own award list (parallel dataset)
One row per row the workbook prints, **FY2009 and FY2011–FY2027**, from the Council's expense funding disclosure workbooks rather than the adopted-budget PDFs. 156,544 rows: FY2013–FY2027 as retrieved from the RnD site 2026-10-12 (139,556), plus FY2009, FY2011 and FY2012 from the Council's own workbooks as archived by the Internet Archive (16,988; GitHub #86, #89). Usually that is one row per designation, but 1,080 rows in 440 groups (FY2009–FY2023) are exact copies of another row; all are kept and flagged in `duplicate_group` (GitHub #69).
`fiscal_year, mocs_id, od_mocs_id, od_match, source, council_member, council_member_id, council_member_type, legal_name, ein, status, status_norm, amount, agency, program_name, address1, address2, city, state, postal_code, zip, zip_status, zip_candidates, purpose, fiscal_conduit, fiscal_conduit_ein, source_file, source_row, duplicate_group, row_flag`

Per-year coverage (from [`data/disclosure_years.csv`](data/disclosure_years.csv), which also carries each file's URL, Wayback timestamp, retrieval date and sha256; sums are this repo's arithmetic, never a Council figure):

| FY | source | rows | Cleared $ | Pending $ | other $ | note |
|---|---|---:|---:|---:|---:|---|
| 2009 | Internet Archive | 5,745 | 406,962,824 | 7,263,353 | 0 | early snapshot; 2 rows flagged not_an_award |
| 2010 | Internet Archive | 2,592 | 54,432,283 | 57,125,769 | 0 | **not loaded** (workbook incomplete vs Open Data) |
| 2011 | Internet Archive | 5,420 | 383,347,147 | 9,893,296 | 2,667,045 | |
| 2012 | Internet Archive | 5,823 | 150,740,107 | 886,357 | 235,206,318 | `other` is `Government` ($235.2M, City agencies) and 155 `CBO Defunded` $0 rows |
| 2013 | RnD site | 4,987 | 18,201,785 | 380,680,617 | 0 | early snapshot |
| 2014 | RnD site | 6,611 | 392,655,572 | 1,077,905 | 0 | |
| 2015 | RnD site | 6,650 | 285,921,454 | 810,402 | 0 | |
| 2016 | RnD site | 7,797 | 380,361,130 | 1,015,496 | 0 | |
| 2017 | RnD site | 8,671 | 352,787,056 | 714,830 | 0 | |
| 2018 | RnD site | 8,894 | 381,385,171 | 514,829 | 0 | |
| 2019 | RnD site | 9,655 | 392,443,522 | 501,478 | 0 | |
| 2020 | RnD site | 10,616 | 456,580,952 | 635,750 | 0 | |
| 2021 | RnD site | 9,054 | 391,770,561 | 1,479,945 | 0 | |
| 2022 | RnD site | 11,336 | 536,959,144 | 1,590,683 | 0 | |
| 2023 | RnD site | 11,027 | 537,910,110 | 3,516,885 | 0 | |
| 2024 | RnD site | 10,811 | 526,907,681 | 1,063,733 | 0 | |
| 2025 | RnD site | 11,276 | 592,800,281 | 2,380,901 | 0 | |
| 2026 | RnD site | 11,764 | 708,776,879 | 7,436,276 | 0 | |
| 2027 | RnD site | 10,407 | 590,253,954 | 115,450,046 | 0 | |

- **FY2010 is not in the dataset.** The Council's archived FY2010 workbook has 2,592 rows ($111.6M); NYC Open Data has 5,981 ($357.8M) for the same year, and both archived copies of the workbook are content-identical (different files, same rows). The two are never mixed; FY2010 waits until it is known which is complete (DATA-ANOMALIES §25).
- **Early snapshots: FY2009 and FY2013.** The Council froze these workbooks while many rows were still Pending and never revised them, so their Cleared totals are not the year's outcome (DATA-ANOMALIES §25).
- **NYC Open Data's MOCS ID as a cross-reference** (`od_mocs_id`, `od_match`; #89 A4): the Council's workbooks have no MOCS ID before FY2024, and Open Data `4d7f-74pe` has one on every FY2009–FY2021 row. It is attached only where one Council row and one Open Data row share an (EIN, whole-dollar amount) bucket in the year: 54,970 rows. It is Open Data's assertion, never the source of any field.
- **Council members resolve to Legistar person IDs, per year** (GitHub #72): `council_member_id` / `council_member_type`, from [`data/disclosure_council_member_crosswalk.csv`](data/disclosure_council_member_crosswalk.csv) (built by `code/build_member_crosswalk.py` from the committed roster extract `data/reference/council_members_legistar.csv`, itself extracted by `code/extract_council_roster.py` from the Council MCP's local Legistar index). `Levin` (7567) and `Levine` (7634) are two people; names that two members carried in the same year are `ambiguous`, never guessed (one, FY2021 bare `Diaz`, is resolved by a recorded, re-checked file convention: the workbook prints the other Diaz as `D. Diaz`); `Speaker`, delegations and district labels get their own types.
- **ZIP codes are checked, never silently rewritten** (GitHub #70). `postal_code` is the cell as published; `zip`, `zip_status` (`valid` / `padded` / `trimmed` / `repaired_extra_digit` / `ambiguous_extra_digit` / `not_a_zcta` / `state_mismatch` / `invalid` / `blank`) and `zip_candidates` are derived against the Census Bureau's 2020 ZCTA list ([`source/census-zcta/`](source/census-zcta/README.md), table built by `code/zcta_states.py`). A 4-digit ZIP gets its leading zero back only when the result is a real ZCTA in the row's own state (13 rows); a ragged ZIP+4 such as `11203-` or `11231=1020` keeps its first five digits on the same condition (`trimmed`, 41 rows); a 6-digit ZIP is repaired only when exactly one one-digit deletion is an in-state ZCTA (`repaired_extra_digit`, 37 rows, e.g. `111691` → 11691) and otherwise gets no zip, its candidates listed (`ambiguous_extra_digit`, 32 rows). `not_a_zcta` means *not verified* — PO-box ZIPs have no ZCTA — not fake.
- **Every row is kept, Cleared and Pending alike.** `status` is the raw value; filter on `status_norm` (`cleared` / `pending` / `other`). A year's headline figure is the **Cleared** total, labeled as such. On 2026-07-15 about half of FY2027's rows, and about 80% of its dollars, were Pending ($143,034,722 Cleared of $705,564,000). On 2026-10-12 it was $590,253,954 Cleared of $705,704,000.
- **Only FY2024 prints a total of its own, and it reconciles to the dollar** ($527,971,414). FY2026 printed one ($716,213,155) in the 2026-07-15 snapshot; the 2026-10-12 workbook dropped those footer rows, and its rows still sum to $716,213,155, which its reconciliation report shows as an earlier-snapshot figure, not as the workbook's own. No other workbook prints a total, so no other year's sum is a Council figure. Each year's `{year}_expense_reconciliation.txt` lists every footer row that was stripped (5 across 18 years).
- **It is not the adopted Schedule C.** It is a later snapshot of the same year, with in-year additions, and its `council_member` is the roster at export time. Join it to the Schedule C award files on `(ein, amount)` within a year, never on `ein` alone and never on the member.
- **How much of it the Schedule C award files cover**, per year, stream and status, joined on `(ein, amount)`: [`data/DISCLOSURE-COVERAGE.md`](data/DISCLOSURE-COVERAGE.md) and `data/disclosure_schedule_c_coverage.csv` (built by `code/reconcile_disclosure_schedule_c.py`).
- **Audited against the questions the Schedule C audits asked**, plus spreadsheet-specific ones, by an independent second reader of the workbooks (openpyxl, not the parser): [`data/DISCLOSURE-AUDIT.md`](data/DISCLOSURE-AUDIT.md), built by `code/audit_disclosure.py` (`--write` / `--check`), with `code/test_audit_disclosure.py`. Every CSV cell equals its workbook cell; what the Council published oddly (repeated rows, `#N/A` cells, 4-digit ZIPs, truncated stream names) is listed there, not silently fixed.
- **When the Council republishes a workbook**, `code/diff_disclosure_snapshots.py` reports what moved (Pending → Cleared, amount changes, re-numbered MOCS IDs, added/removed rows, totals by status). The reports for each re-pull are committed under `data/disclosure-snapshots/<retrieval date>/`; the first is [`2026-10-12`](data/disclosure-snapshots/2026-10-12/). Re-pulling needs explicit approval each time; the procedure is in [`source/expense-funding-disclosure/README.md`](source/expense-funding-disclosure/README.md).
- **Rows a person decided are not grants to an organization are flagged, not dropped** (`row_flag = not_an_award`; #89 B13): FY2009's `Borough President Discretionary Funding` $533,000 and `Provider's Choice` $1,200,000, both on the City's EIN, which Open Data files under MOCS ID `FY09 Not an Award`. They stay in every total. A rule adds `row_flag = no_grantee_ein` to the 53 rows that print no grantee EIN (blank or `NA`, FY2009–FY2015), often a City program rather than a nonprofit; flags join with `;`.
- `source_file` + `source_row` point at the exact workbook row. Built by `code/parse_expense_disclosure.py --write`; the `.xls` years (FY2009, FY2011–FY2013) need `xlrd`. Details: [`DATA-DICTIONARY.md`](DATA-DICTIONARY.md), [`code/PARSING.md`](code/PARSING.md).

### `data/{year}/terms/{year}_terms_and_conditions.csv`
`item_number, agency_name, agency_code, units_of_appropriation, num_units, report_deadlines, coverage_period, condition_text`

### `data/{year}/capital/{year}_capital_projects.csv`
Section 254 capital changes. `part, agency, budget_line, sub_id, boro, fy1, fy2, fy3, fy4, sponsor, title, building_code, school_code` — `fy1` is the adoption year; `fy2..fy4` are out-years; `boro`: M/X/K/Q/R.
- **FY2025, FY2026, and FY2027** use the "Capital Project Detail" (Council-additions) schedule, share this schema, and reconcile against printed agency subtotals and both `TOTALS FOR ALL` grand totals. FY2025 is now directly comparable to FY2026/FY2027 (parsed from the Council-version supporting-detail book; Part I **$775M / 1327 projects**, Part II non-city **$158,992,000 / 181 projects**). Part III (the non-city-by-entity cross-tab of Part II) is emitted to the sidecar `fy25_capital_noncity_by_entity.csv`.
- The broader FY2025 **"Appropriation Changes"** resolution book (all executive-capital changes, ~$5.2B, `NOT RECONCILABLE`, adds an `action` column) is a *different document type* and is retained for provenance as `fy25_capital_changes_appropriation.csv`.

### `data/fy26/transparency-resolutions/`
Post-adoption discretionary designations from the 10 FY2026 Transparency Resolutions (per-resolution `resoNN_transparency_designations.csv` files + a combined `fy26_transparency_all.csv`). Columns: `resolution, date, chart, fiscal_year, action, source, council_member, organization, program, ein, amount, agency, agy_num, ua, purpose, flags` — `action` ∈ designate / rescind / purpose_change; rescissions carry negative amounts. These record money the adopted budget left "to be designated post-adoption" (e.g. the FY2026 AI Community Engagement $1M). **No printed totals exist**, so they are labeled `NOT RECONCILABLE`; the only internal check is that transfers (rescind + re-designate) net to zero.

**FY2009 only — `fy09_transparency_fiscal_conduits.csv`.** FY09's long-form charts (1–3) print two
columns no other year has: a Fiscal Conduit/Sponsoring Organization (+ its EIN), used when a
designation is paid through an intermediary fiscal sponsor rather than directly to the recipient,
and a per-row PQL clearance `status` (`Cleared`, `Approved`, `Application Pending`, `Denied`,
`Government Entity`, etc.). They can't go in the standard 16-column schema, so they live in this
sidecar (`resolution, chart, ein, conduit_organization, conduit_ein, status`), joined back to
`resoNN_transparency_designations.csv` on `(resolution, chart, ein)`. Most rows have no fiscal
conduit — the money went straight to the named org. Since FY09 is OCR'd off scans (see
[`code/PARSING.md`](code/PARSING.md#ocr-pipeline--fy2009-transparency-resolutions)), `status` has
many spelling variants of the same value and should be treated as informational, not a clean
categorical.

### `data/combined/`
`all_years_initiatives.csv` and `all_years_awards.csv` — the per-year files stacked with a leading `year` column for cross-year analysis. Each also carries two derived `*_canonical` columns (see the editorial note below).

> **⚑ Editorial note — consolidated names.** Schedule C spells the same program differently across fiscal years (`&` vs `and`, an ALL-CAPS era vs Title Case, singular/plural, and outright renames such as *Senior Services → Older Adult Services*). To let a program be tracked over time, we made an **editorial decision to consolidate these into canonical names** — surfaced as the derived `initiative_canonical` and `category_canonical` columns (and used for the viz's Fund axis). **The original source names are preserved verbatim** in the `initiative` and `category` columns; nothing is overwritten. The category merges are human judgment calls, checked against the organizations funded under each name. The full mapping is auditable in `initiative_name_crosswalk.csv` and `category_name_crosswalk.csv`, and the rationale is in [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) #17–#18.

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

### `data/capital/` — Council capital, from structured sources only

The Council's own capital lists, one row per designation and fiscal year: FY2015–FY2017 from the
Council's archived workbooks, FY2019–FY2025 from NYC Open Data `t474-a92g` (which the Council
publishes), FY2026–FY2027 from the RnD site's workbook. FY2018 has no structured source (its
Section 254 supporting detail PDF is in `source/FY18/` but is not parsed; corrected 2026-10-20,
DATA-ANOMALIES §26). Beside it,
OMB's adopted Capital Budget (`46m8-77gv`) and Capital Commitment Plan (`2cmn-uidm`) on the
Council's budget lines, and a reconciliation **by budget line**: in FY2027, 146 of the Council's
153 lines match OMB's adopted budget to the dollar. Project IDs do not link to OMB or to
contracts, so nothing here is claimed below the budget line. Built by
`code/build_capital_council.py`, audited by `code/audit_capital.py`; details, codes and known
problems in [`data/capital/README.md`](data/capital/README.md). These are not the PDF-derived
Section 254 files in `data/{year}/capital/`.

### Historical coverage (FY2009–FY2024)

Beyond the flagship FY2025–FY2027 set, the repo now backfills earlier years. Full per-year,
per-document-type detail (and the parser/invocation for each) is in [`code/PARSING.md`](code/PARSING.md); the headline:

- **Schedule C** — reconciled for **FY2015–FY2024** (**FY2015** via the dedicated `parse_schedule_c_fy15.py`,
  reconciled **24/24**; **FY2016–FY2024** via `parse_schedule_c.py`) and **FY2009–FY2014**
  (initiatives-only, via `parse_schedule_c_legacy.py`). The early-era PDFs do print award rows with
  EINs; the parser does not extract them. FY2008 remains open; it prints 1,674 member-item rows
  without EINs (see PARSING.md). **Corrected 2026-10-20:** this said the early-era documents
  "carry no award-level EIN tables" (DATA-ANOMALIES §2).
- **§254 Capital (Capital Project Detail)** — reconciled **23/23–32/32** for **FY2020, FY2022, FY2023, FY2024**
  (via `parse_capital_detail.py`).
- **Terms & Conditions** — extracted for **FY2015–FY2024** (via `parse_terms_legacy.py`; T&C print no totals).
- **Transparency Resolutions** — extracted for **FY2010–FY2024** (FY2013 onward print no totals;
  FY2010–FY2012 charts do, and the parser does not check them). Financial columns
  (EIN/amount/agency/date/action) are deterministic on the rows emitted, but rows are missing:
  hyphenless EINs, rows with no EIN, merged rows and truncated cents (DATA-ANOMALIES §3).
  Organization/member/program *text* is
  low-confidence in the older glued-text-layer years (FY2010–FY2013), flagged per-year in each
  `*_reconciliation.txt`. **FY2009** has no text layer (all 8 PDFs are scans), so it is handled by a
  separate OCR pipeline — `code/parse_transparency_reso_fy09.py` + `code/ocr/`, documented in
  [`code/PARSING.md`](code/PARSING.md#ocr-pipeline--fy2009-transparency-resolutions); its figures are
  model-read rather than text-layer-extracted, and flagged where uncertain. FY2013 resolutions
  07/10/11 (`.doc`) remain blocked.

**Capital (Section 254):** FY2025 reconciles **30/30** agency subtotals plus both grand totals exactly (Part I $775M / 1327; Part II $158,992,000 / 181; Part III cross-tab 106/106 entities); FY2026 reconciles **31/31**; FY2027 reconciles **24/26** (the two misses are parser losses of three rows the PDF prints; see `code/PARSING.md`). (The separate FY2025 appropriation-changes book remains `NOT RECONCILABLE` by nature.) **Transparency Resolutions:** `NOT RECONCILABLE` as parsed; transfers net to zero as expected. FY2013 onward print no totals; FY2009–FY2012 charts do, and only FY2009 is checked against them. **Corrected 2026-10-20:** this said no year prints totals. See each `*_reconciliation.txt` for details.

**Data QA:** beyond per-file reconciliation, `code/validate_data.py` runs row-level and cross-file
integrity checks (schema, EIN validity + per-year coverage, amount/sign sanity, fiscal-year
integrity, duplicate detection, column-bleed heuristic, and a reconciliation roll-up) over the whole
`data/` tree and writes a dated `data/QA-REPORT.md`. Latest report (2026-10-20): 302 files, 4 hard
failures (all known FY09 OCR artifacts — see below), 598 soft advisories. EIN coverage is below
100% in FY09 transparency (97.9%, 2565/2620) and in the FY2009 and FY2011–FY2015 disclosure files
(lowest FY2009, 99.5%; FY2013–FY2015 are short by 2, 3 and 1 rows and display as 100.0% by
rounding); every other EIN-bearing file with rows is 100%. Coverage counts rows a parser
emitted, and the PDF parsers emit only rows with an EIN, so 100% does not mean every printed row
is present (DATA-ANOMALIES §3). **Corrected 2026-10-20:** this said 100% everywhere except FY09
transparency. Details in [`code/PARSING.md`](code/PARSING.md).

## Known limitations

- Some `initiative_provider` award rows have imperfect organization *names*. **Correction (2026-08-12):** this line previously read "(EIN + amount are correct)". That is not true for all of them. In 64 remaining rows the extraction lost the row boundary, so the `amount` can belong to a different organization than the `organization` field names. 239 such rows were repaired on 2026-08-12/13. See [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) §20 and §21.
- **Award rows are now reconciled against the printed INITIATIVE amount** (`validate_data.py`, soft advisory) — the first pass/fail target the award stream has ever had. The per-year `*_reconciliation.txt` files still check only the *category* summary against printed `TOTAL` lines.
- **Recovered data lives in [`data/recovered/`](data/recovered/), never merged into the per-year extracts**, so nothing already published moves: `schedule_c_absorbed_awards.csv` (442 awards, $66,472,992 the parser absorbed and lost) and `schedule_c_appendix_recovered.csv` (26,127 appendix designations, $283,588,100, for the six years whose appendix streams came out empty). Both carry confidence and provenance columns.
- **5,450 repairs across organization, EIN, initiative and purpose are recorded in [`data/combined/org_name_recovery_crosswalk.csv`](data/combined/org_name_recovery_crosswalk.csv)** with the original value and the replacement, so every automated edit is auditable and reversible. See [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) §21.
- **Award rows are not reconciled against a printed total.** The per-year `*_reconciliation.txt` files reconcile the *category summary* stream against the documents' printed `TOTAL` lines. The award table — the per-organization, per-EIN rows — is reported as a bare tally with no printed total to check it against, in every year. Award-level completeness is therefore **not** established by the reconciliation status shown above.
- Borough delegations ("Brooklyn", "Queens", …) appear in the `member` column as collective sponsors.
- **FY2025 capital is now row-comparable to FY2026/FY2027** — parsed from the FY2025 Council-additions "Capital Project Detail" book (the counterpart to the FY2026/FY2027 books), it shares their schema and reconciles. (Earlier releases used the different "Appropriation Changes" resolution book, now retained separately as `fy25_capital_changes_appropriation.csv`; that book alone is not row-comparable.) Note Part II re-lists the non-city subset, so summing `fy1` across both parts double-counts non-city projects — filter by `part` when aggregating, exactly as for FY2026/FY2027.
- **Transparency Resolutions are not reconciled against printed totals.** FY2013 onward print none; FY2010–FY2012 do, unchecked (only the transfer net-out check runs); ~0.2% of rows have an imperfect organization name (EIN + amount are recoverable).
- Category names differ across years (FY2025 has a standalone "Libraries" that later folds into "Cultural Organizations"). Normalize before comparing.

## Reproduce or extend to a new year

Requires Python 3 with the packages in `code/requirements.txt` (`pypdf`, `cryptography`, `pdfplumber`; `xlrd` only for the `.xls` expense disclosure years, FY2009 and FY2011–FY2013):

```bash
python code/parse_schedule_c.py <ScheduleC.pdf> --outdir data/fy28/schedule_c --prefix fy28
python code/parse_terms.py       <Terms.pdf>     --outdir data/fy28/terms      --prefix fy28
python code/parse_capital.py     <Capital.pdf>   --outdir data/fy28/capital     --prefix fy28 \
       --roster data/*/schedule_c/*_schedule_c_awards.csv
```

Always read the generated `*_reconciliation.txt` to confirm a parse before trusting a new year.

The expense-disclosure dataset is regenerated in one step, for every year at once:
`python3 code/parse_expense_disclosure.py --write` (and `--check` to confirm the committed files
are current).

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
| **[NYC Open Data — City Council Discretionary Funding](https://data.cityofnewyork.us/dataset/4d7f-74pe) (`4d7f-74pe`)** | Award-level Council discretionary funding, FY2009–FY2021, Council-published | **Directly overlaps FY2013–FY2021** with the disclosure dataset: the same Council data at an April 2021 clearance state, with amounts rounded and some EINs missing a leading zero; it itemizes initiatives the Council's FY2013 file lumps, and is the only complete FY2010 source found. Row-by-row diff: [`research/2026-10-14-open-data-vs-disclosure-diff.md`](research/2026-10-14-open-data-vs-disclosure-diff.md). It stopped updating April 2021, so this repo is the machine-readable source for **FY2022–FY2027** and adds source-reconciled totals plus Terms, Capital, Transparency, and Legistar provenance. |
| **[NYC Checkbook](https://www.checkbooknyc.com) (Comptroller)** | Actual spending and registered contracts | Complements this repo: join on EIN to ask whether a designation became a paid contract. |
| **[NYC Council Finance Division](https://council.nyc.gov/budget/) / OMB** | The primary source documents this repo parses | This repo is the structured, reconciled extraction of those documents. |

In short: **IBO tells you what the City spends, raises, and owes in aggregate over decades; this repo tells you which organizations the Council funded, and how much, in the adopted budget.** Neither IBO nor NYC Open Data (after FY2021) publishes the second thing as machine-readable data. That is the gap this repository fills. A detailed source-by-source crosswalk (including how this data can be joined to IBO's agency-level fiscal tables) is in [`research/2026-07-08-ibo-data-center-crosswalk.md`](research/2026-07-08-ibo-data-center-crosswalk.md).

**The companion Schedule C explorer is frozen (2.0):** it was built on this repo's PDF-derived Schedule C data. Its GitHub Pages address now shows a notice pointing to the structured data; the explorer itself stays online at `legacy.html`, frozen as of 2026-10-16 (no further data updates) under a banner saying not to cite it (see [`viz/`](viz/)). It shares its toolkit (DataMade's [Look at Cook](https://github.com/datamade/look-at-cook)) with BetaNYC's **[citywide expense-budget explorer](https://github.com/BetaNYC/nyc-budget-viz)**, which visualizes the full ~$114B adopted/modified budget across all agencies — the aggregate fiscal side this repo deliberately does not cover.

## Future work

- **Schedule C vs. actuals.** Compare discretionary designations here against NYC
  Checkbook spending/contract data — do designations actually convert into paid
  contracts, and at what lag or drop-off rate?
- **Capital project lifecycle.** Trace a Section 254 capital line from budget proposal
  through adoption (this repo) to actual payment and completion (Checkbook capital
  commitments) — an end-to-end view of how capital dollars move from planning to
  money spent.

See `research/` for active and lodged scoping plans. (The FY2022–FY2024 gap between the retired
PDF-extracted years and NYC Open Data's FY2009–FY2021 archive is closed in 2.0 by the Council's
disclosure workbooks, which cover FY2013–FY2027.)

## AI use in this project

BetaNYC uses AI tools openly and with human accountability. The extraction, reconciliation, and analysis tooling in this repository was built by AI agents (Anthropic's Claude) working under the direction and review of BetaNYC staff.

One commitment about the data: **the figures here are not AI-generated.** In 2.0 every dollar amount is read **deterministically**, cell by cell, from the Council's own spreadsheets (the expense funding disclosure workbooks and the capital workbooks) and from NYC Open Data, and every row keeps the file, sheet or Open Data row it came from — never inferred, never estimated by a model. The outputs are re-derived by separate audit scripts (`data/DISCLOSURE-AUDIT.md`, `data/capital/CAPITAL-AUDIT.md`) and checked by `code/validate_data.py`; where the sources disagree or leave a question open, that is recorded in [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) rather than papered over. The earlier PDF extraction, which we found errors in, is retired and kept only as a historical record.

**The one exception, stated plainly: the FY2009 Transparency Resolutions.** Those eight documents are scanned images with no text layer, so there is nothing to extract deterministically — they are read by OCR (docTR), which *is* a model reading numbers. We ship them anyway because the alternative is leaving a year of public designations unreadable, but they are treated differently from every other year: each value is checked against a shape rule and an agency-code dictionary built from the years that *do* have text layers; where a chart prints its own total, the OCR'd rows must sum to it exactly; ambiguous character readings (`O` vs `0`, `S` vs `$`) are **never** guessed but flagged in the `flags` column and queued in `fy09_transparency_needs_review.csv` alongside a crop of the original pixels. Any FY2009 figure you rely on can be traced back to those pixels. See [`code/PARSING.md`](code/PARSING.md#ocr-pipeline--fy2009-transparency-resolutions).

*Scope under 2.0:* the FY2009 OCR files belong to the PDF-derived record. They are published in this repository as a research dataset (`data/fy09/transparency-resolutions/`) and are not served by the 2.0 MCP or the Pages site; see [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) §27–§28.

Questions about our approach: hello@beta.nyc.

## License

Everything BetaNYC made in this repository is under the [MIT License](LICENSE) © 2026 BetaNYC: the code (`code/`, `mcp/`, `viz/`), the derived data (`data/`), and our documentation and research (the top-level `*.md` files and `research/`). Use, adapt and redistribute freely, keeping the copyright and license notice. The `mcp/` package is published to npm as [`@betanyc/nyc-budget-mcp`](https://www.npmjs.com/package/@betanyc/nyc-budget-mcp), also MIT (`mcp/package.json`).

**Not covered:** the Council and City documents in `source/` are public records of the City of New York, © The City of New York, reproduced here for transparency. BetaNYC's license does not apply to them. Third-party libraries bundled in `viz/` keep their own licenses (see `viz/LICENSE.md` and each file's header).

## Acknowledgments

- A member of the **NYC City Council Finance Division staff** supplied the FY2025 Council-version
  §254 Supporting Detail Book and flagged the expense-disclosure spreadsheets, which made the
  reconciled FY2025 capital detail and the award-level expense data in this repo possible.
  <!-- CREDIT PENDING: attribution requested 2026-07-15; fill in the staffer's name/credit line
       here once they reply on how they wish to be acknowledged. -->

---

*Source: NYC Council Finance Division, adopted budget Schedule C, Terms & Conditions, and Section 254 capital changes, FY2025–FY2027, [council.nyc.gov](https://council.nyc.gov/budget/). Structured and analyzed by [BetaNYC](https://beta.nyc).*
