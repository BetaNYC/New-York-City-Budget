# Data Dictionary

Every column in every CSV this repository produces, what it means, and how the files join to each other. For *how each fiscal year is parsed* and its reconciliation status, see [`code/PARSING.md`](code/PARSING.md). For known data limitations, see [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md).

**Generated:** 2026-07-08. Covers FY2009–FY2027.

---

## Coverage at a glance

Not every document type exists (or is machine-readable) for every year. This matters: the discretionary **award** files — the ones with per-organization EINs — only exist **FY2015 onward** (FY2015 is the earliest EIN-level Schedule C). Earlier years (FY2009–FY2014) have initiatives-level Schedule C only (no organization/EIN detail), because those designations were largely made *after* budget adoption and live in the Transparency Resolutions instead.

| FY | Schedule C | Terms & Conditions | Capital §254 | Transparency Resolutions |
|----|-----------|--------------------|--------------|--------------------------|
| 2009 | initiatives only | — | — | — (scanned; see anomalies) |
| 2010–2014 | initiatives only | — | — | ✔ |
| 2015 | see PARSING.md | ✔ | — | ✔ |
| 2016–2018 | **awards + initiatives** | ✔ | — | ✔ |
| 2019 | **awards + initiatives** | — | — | ✔ |
| 2020 | **awards + initiatives** | — | ✔ | ✔ |
| 2021 | **awards + initiatives** | ✔ | — | ✔ |
| 2022–2024 | **awards + initiatives** | ✔ | ✔ | ✔ |
| 2025–2027 | **awards + initiatives** | ✔ | ✔ | 2026 only |

**Separately, the Council's expense funding disclosure workbooks give an EIN-level award list for every year FY2013–FY2027** (`data/{year}/expense_disclosure/`, below). It is a parallel dataset from a different source and a later moment, not a fill for the Schedule C gaps in this table.

"awards" = the `_awards.csv` file with per-organization EINs. **EIN-keyed analysis (and the budget MCP's award tools) is valid FY2015–FY2027.** FY2009–FY2014 are initiatives-only (no EIN) and are excluded from EIN-keyed tooling. See [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) for the full gap list.

---

## `data/{year}/schedule_c/{year}_schedule_c_awards.csv`

One row per discretionary designation to a named organization. **The primary who-got-what file. FY2015+ only.**

| Column | Type | Meaning |
|--------|------|---------|
| `category` | text | Schedule C category (e.g. "Aging Discretionary"). Sums to the printed category TOTAL. |
| `initiative` | text | The Council initiative the award falls under (e.g. "Cultural After-School Adventure (CASA)"). |
| `award_type` | text | `member_item` (an individual Council Member's local designation) or `initiative_provider` (a provider named collectively under a citywide initiative). |
| `member` | text | Sponsoring Council Member **surname**, or a borough delegation ("Brooklyn Delegation") or "Speaker". Not a full name — join to a roster for district. |
| `organization` | text | Recipient organization name. **Best-effort text; a minority are imperfect.** The EIN + amount are the reliable fields. |
| `program` | text | Specific program/site the funds support. **This is the field that distinguishes grantees sharing one fiscal-sponsor EIN** (see EIN note below). |
| `ein` | text | Recipient tax ID, **9 digits, no hyphens**. The reliable cross-system join key (to IRS 990 data, and across BetaNYC's other datasets). |
| `amount` | number | Dollars designated. Exact against the source. |
| `agency` | text | The City agency that implements the funds (DYCD, DFTA, DCLA, …). |
| `purpose` | text | Free-text description of the funded use (where the source provides it). |

**EIN caveat (load-bearing):** a single EIN can be a **fiscal sponsor** — a passthrough for many unrelated programs. EIN `13-2612524` ("Delegation Fund for the City of New York, Inc.") covers dozens of grantees. To isolate one grantee (e.g. BetaNYC), filter on `ein` **and** `program`. EIN alone returns the whole pool.

## `data/{year}/schedule_c/{year}_schedule_c_initiatives.csv`

Authoritative category/initiative totals. **One row per initiative; sums exactly to each category's printed TOTAL.** This is the file that reconciles, and the *only* Schedule C file for FY2009–FY2014.

| Column | Type | Meaning |
|--------|------|---------|
| `category` | text | Schedule C category. |
| `agencies` | text | Agency or agencies administering the initiative. |
| `initiative` | text | Initiative name. |
| `amount` | number | Total dollars for the initiative. |

## `data/{year}/schedule_c/{year}_appendix_*.csv`

Detail breakouts by funding stream: `_a_aging` (Aging Discretionary), `_b_local` (Local Initiatives — adds an `agency` column), `_c_youth` (Youth Discretionary). **These are separate designations from the award body, not a subset of it — adding appendix rows to body award rows double-counts nothing.** Evidence for every year, from the Council's disclosure `source` column: [`data/DISCLOSURE-COVERAGE.md`](data/DISCLOSURE-COVERAGE.md) §4 and DATA-ANOMALIES §23. (This is about award rows, not the printed category `TOTAL`s.) Header-only for FY2015–FY2017 and FY2019–FY2020 (an extraction gap, GitHub #59: the PDFs print them); FY2018 has aging only.

| Column | Type | Meaning |
|--------|------|---------|
| `member` | text | Sponsoring Council Member surname. |
| `organization` | text | Recipient organization. |
| `program` | text | Program/site. |
| `ein` | text | Recipient tax ID (9 digits). |
| `amount` | number | Dollars. |
| `agency` | text | Implementing agency (`_b_local` only). |
| `purpose` | text | Free-text use description. |

## `data/{year}/expense_disclosure/{year}_expense_awards.csv`

The NYC Council's own **expense funding disclosure** workbooks
(`source/expense-funding-disclosure/`), one row per row the workbook prints (normally one per
designation; exact copies are kept and flagged, see `duplicate_group`), **FY2013–FY2027**. A **parallel
award-level dataset**: it is not derived from the adopted-budget PDFs, it does not feed the
Schedule C files above, and its totals are not the adopted Schedule C totals. Built by
`code/parse_expense_disclosure.py --write`; per-year counts, totals and printed-total
reconciliation are in `code/PARSING.md` and each year's `{year}_expense_reconciliation.txt`.

Column names follow the disclosure's own fields, not the Schedule C vocabulary (`legal_name`, not
`organization`; `council_member`, not `member`).

| Column | Type | Meaning |
|--------|------|---------|
| `fiscal_year` | int | From the workbook's **file name**. FY2013, FY2014 and FY2016 have no Fiscal Year column; where one exists it agrees in every row. |
| `mocs_id` | text | Mayor's Office of Contract Services ID (`FY25 00001`). **FY2024+ only**, blank before. Identifies a row within one snapshot; not stable across snapshots (DATA-ANOMALIES §22). Its join to registered contracts / Checkbook is unverified. |
| `source` | text | Funding stream as the Council names it: `Local`, `Youth`, `Aging`, `Speaker's Initiative`, or a named citywide initiative. |
| `council_member` | text | Sponsor as printed. **The roster at the time the workbook was exported, not at adoption** — never a join key (see DATA-ANOMALIES §21). A substring of it blends people: `Levin` is in `Levine`, `Won` in `Wong`. |
| `council_member_id` | text | **Derived** (GitHub #72): the Legistar person ID the printed name resolves to **for that fiscal year**, from `data/disclosure_council_member_crosswalk.csv`; blank unless `council_member_type` is `member` or `member_outside_fy`. `Levin` is 7567 (Stephen T. Levin), `Levine` 7634 (Mark Levine). Filter on this, not on the name, to mean one person. |
| `council_member_type` | text | **Derived** (GitHub #72). `member` — exactly one Legistar person has the printed surname (and initial, if printed) and a recorded vote in that fiscal year. `member_outside_fy` — exactly one person has the name, but no vote that year: the export-time roster naming someone not yet or no longer in office (FY2025 `Wong`, FY2021 `Aviles`, FY2020 `D. Diaz`); the ID is given, the type says it is not that year's member. `ambiguous` — two people of that name voted that year (FY2014 and FY2022 `Barron`, FY2014 `Vallone`); no ID, never guessed. One such value is typed `member` by a recorded **file convention** instead: FY2021 bare `Diaz` is Ruben Diaz, Sr. (7744), because the same workbook prints Darma V. Diaz as `D. Diaz` (crosswalk `method` begins `file_convention`; see below). `unresolved` — no Legistar member has the name (`CC`, `NA`). `speaker`, `delegation` (borough delegations, bare borough names, `Brooklyn / Queens`), `citywide`, `district_label` (`CD19`, `CD28`), `blank`: not a person, no ID. |
| `legal_name` | text | Grantee legal name. |
| `ein` | text | Grantee EIN, **9 digits, no hyphen, leading zeros kept**. Blank on 6 rows where the Council left it blank (FY2013 2, FY2014 3, FY2015 1). The FY2013 file prints 175 EINs as `NN-NNNNNNN` (hyphen removed here) and stores some as numbers, three of which lost a leading zero (re-padded; rows listed in the FY2013 report). Fiscal-sponsor caveat as above: filter on `ein` **and** `amount` or `program_name`, never `ein` alone. |
| `status` | text | Clearance status **exactly as published**: `Cleared` / `Pending`, or `CLEARED` / `PENDING` (FY2018). |
| `status_norm` | text | `cleared`, `pending`, or `other` (any status that is neither — none today). **Filter on this.** A year's headline figure is the `cleared` rows; adding `pending` makes a different, larger claim and should be labeled so. |
| `amount` | number | Dollars. Integral amounts print with no decimal point. 281 rows carry fractions as published (e.g. `13881.76`), written as the shortest decimal that is the same stored value. |
| `agency` | text | Implementing agency (DYCD, DFTA, …). |
| `program_name` | text | Program/site, where given. |
| `address1`, `address2`, `city`, `state`, `postal_code` | text | Grantee mailing address **as printed**. `postal_code` is never rewritten: it appears as 5 digits, ZIP+4, 4 digits (an Excel number that lost its leading zero, or a typo), `0`, `#N/A`, or text. Street addresses are not validated. |
| `zip` | text | **Derived** (GitHub #70): the 5-digit ZIP read from `postal_code`, or blank. From `12345`, `12345-6789`, `12345 - 6789` or `123456789`, the first five digits; from a 4-digit value, `0` + it, **only** when `zip_status` is `padded`; from a ragged ZIP+4 (`11203-`, `11217-11217`), the first five digits, **only** when `zip_status` is `trimmed`. Nothing else is guessed. |
| `zip_status` | text | **Derived** (GitHub #70), checked against the Census Bureau's 2020 ZIP Code Tabulation Areas (`data/reference/zcta2020_states.csv`, from the file in `source/census-zcta/`): `valid` — a ZCTA, and in the row's state when the `state` cell names one (a USPS code in any case, a state name, or the `New YorkNY` run-together; boroughs, `N/A` and the like are not read, so 869 `valid` rows are checked for existence only); `state_mismatch` — a ZCTA lying wholly in other states (e.g. FY2013 rows 404–406, `11217` with state `NC`); `not_a_zcta` — a well-formed 5-digit ZIP that is not a 2020 ZCTA. **This means not verified, not fake:** ZCTAs are not every USPS ZIP, and PO-box-only or single-building ZIPs such as `10008` have no ZCTA; `padded` — 4 digits whose `0`-padded form is a ZCTA in the row's own state (Brookline MA `2446` → `02446`); `trimmed` — a ragged ZIP+4 (five digits, a hyphen, then anything but exactly four digits: `11203-`, `10027-000`, `11217-11217`, `11102-20`) whose first five digits are a ZCTA in the row's own state; a row whose state cell names no state is not trimmed; `invalid` — anything else: 4 digits that do not pad into an in-state ZCTA (Bronx `7083`: 07083 is in New Jersey; Hartford `6108` on a row whose state says New York), a ragged ZIP+4 that does not trim into an in-state ZCTA, a five-digit-led value that is not the hyphenated form (`11231=1020`, `11413 ZipCode2: 3929`, six-digit typos such as `111691`), `0`, `#N/A`, `N/A`, a name or URL; `blank` — the cell is empty. `blank` stays its own value, apart from `invalid`: an empty cell is not a malformed ZIP. |
| `purpose` | text | Purpose of funds (the header varies: "Purpose of Funds", "CM Purpose of Funds", "Purpose to be listed in Schedule C"). |
| `fiscal_conduit`, `fiscal_conduit_ein` | text | Fiscal conduit, where named (FY2013–FY2018, plus one row each in FY2022 and FY2023). Kept as printed apart from the same hyphen/leading-zero EIN rules. |
| `source_file` | text | Provenance: the workbook. |
| `source_row` | int | Provenance: the 1-based sheet row, so any record can be found in the workbook. |
| `duplicate_group` | int or blank | **Exact copies (GitHub #69).** Blank for a unique row. When the row is identical to another row of the same workbook in every published field (everything but `source_row`), the `source_row` of the first of them: a group's rows all carry the same number, and the first row carries its own. 662 rows in 321 groups, FY2013–FY2023 (per year in DATA-ANOMALIES §22 and each `{year}_expense_reconciliation.txt`). **Every copy is kept** and counted in every total: the workbooks print them, and whether each is a second designation or a filing error cannot be told from the file. To count each group once, keep rows where `duplicate_group` is blank or equals `source_row`. |

All text cells are trimmed, with internal runs of whitespace (including line breaks and no-break
spaces) collapsed to one space and invisible format characters (Unicode category Cf: zero-width
space, left-to-right mark, BOM) removed, **except the soft hyphen (U+00AD), which becomes `-`**.
In these workbooks a soft hyphen is a hyphen that lost its glyph, not a line-break hint: all 211
cells holding one (185 `address1`, 1 `address2`, 25 `purpose`, no other field) read as a
hyphenated word or range, including the Queens house number `12-11 40th Avenue` (FY2018 rows
2796–2811), `after-school`, `ages 12-19`, `multi-media` (GitHub #68). Where the cell already prints
a `-` or `/` right beside the soft hyphen (`12-<SHY>11`, 169 address cells; `E<SHY>-waste`;
`disposal/<SHY>destruction`) the soft hyphen is dropped instead, so no `--` is invented. One
consequence of reading it literally: FY2018 row 6448 `purpose` reads `(e- waste)`, as the cell
has it. Nothing else is rewritten: `New YorkNY`, 4-digit ZIPs and mojibake are kept as the workbook
holds them (`data/DISCLOSURE-AUDIT.md`).

**Excel error cells are published as text (GitHub #71).** 37 cells hold the spreadsheet error
value `#N/A` (FY2014 `postal_code` 19; FY2017 `address1`, `city` and `postal_code` 6 each, on the
same 6 rows). The CSV carries the four characters `#N/A`, exactly as the workbook displays them:
it is not a blank, not a ZIP and not a number, and nothing reads it as one (the validator counts
such cells as `excel_error`; the MCP index keeps them as text and refuses one in an EIN column).
Distinct from these, some cells hold the typed **text** `N/A`, `NA` or `na` (e.g. FY2013–FY2014
addresses and ZIPs, three FY2014 `council_member` cells): also kept as published.

**Not the same universe as the adopted Schedule C totals.** The workbook is a later snapshot of the
same year, republished with in-year additions; FY2024 prints its own `Adoption Total`
($527,096,000) beside its `New Total` ($527,971,414). Compare like with like.

## `data/disclosure_council_member_crosswalk.csv` (GitHub #72)

One row per (fiscal year, printed `council_member` value) in the expense disclosure: `fiscal_year,
council_member, rows, council_member_type, council_member_id, legistar_full_name, method,
evidence`. Built by `code/build_member_crosswalk.py` from the committed roster extract
`data/reference/council_members_legistar.csv` (every Legistar person, with the fiscal years in
which Legistar records a vote by them; provenance in `council_members_legistar_meta.csv`),
itself extracted by `code/extract_council_roster.py` from the local Legistar index that BetaNYC's
Council MCP (`@betanyc/nyc-council-mcp`) reads. No Legistar web API or Council website call.

**Method.** Accent-, case- and space-insensitive surname match (an exact surname before a
component of a hyphenated one, so `Viverito` reaches Mark-Viverito but `Powers` is not
Brooks-Powers); a printed initial (`D. Diaz`, `Sanchez, J`) must match the first-name initial or
Legistar's own initial prefix (`D. Diaz`); a person counts for a fiscal year only if Legistar
records a vote by them in it. **Service is a set of years, not a span**: Charles Barron voted
FY2004–FY2014 and FY2022–FY2024 and Inez Barron held the seat between.

**Limits.** A fiscal year counts only if a vote was recorded in it, so a member sworn in or out
within days of 1 July with no vote on one side is not counted there. People with no recorded
vote (pre-2001 members, Public Advocates) are never candidates and are named in `evidence` when
excluded. Votes run 2001 to the index's last indexing date; the unfinished part of FY2027 is not
covered. The crosswalk says who a printed name **is**; the printed name is still the export-time
roster, not proof of who made the designation.

**File conventions.** A value the method leaves `ambiguous` may be resolved only by a decision a
person made and recorded in `FILE_CONVENTIONS` (`code/build_member_crosswalk.py`), applied to that
one (fiscal year, value) and no other. One exists. **FY2021 bare `Diaz` → Ruben Diaz, Sr. (7744)**
(Noel Hidalgo, 2026-10-13): Ruben Diaz, Sr. (District 18, Bronx) and Darma V. Diaz (District 37,
Brooklyn) both voted in FY2021, and the workbook prints Darma as `D. Diaz` in the same year, so
bare `Diaz` is read as the other one. Typed `member`; `method` begins `file_convention`. The
evidence is computed from the parsed workbook on every build and written to `evidence`: of
`Diaz`'s 46 Local-stream rows, 18 have city Bronx and 17 a 104xx ZIP (2 Brooklyn, both multi-borough
organizations); of `D. Diaz`'s 24, 14 are Brooklyn / 112xx and none Bronx. **These are grantee
mailing addresses, not where services were delivered**, so they support the reading; they do
not prove it. The build stops if the method stops calling the value ambiguous, if `D. Diaz` is
gone or resolves to someone else, or if the addresses stop pointing that way. (Legistar also
holds a second `Ruben Diaz` record, 5267, with 2002 sponsorships and no recorded vote; it is
never a candidate, and the FY2018-FY2022 record 7744 is the one used for FY2019-FY2021.)

**Outcome (2026-10-12 data, conventions as of 2026-10-13):** 758 (year, name) pairs / 101,069
rows `member` (one by file convention, 123 rows); 3 / 341 `member_outside_fy`; 3 / 189
`ambiguous`; 2 / 243 `unresolved`; non-member labels: `speaker`
6,190 rows, `delegation` 7,098, `citywide` 431, `district_label` 384, `blank` 23,611.

## `data/{year}/terms/{year}_terms_and_conditions.csv`

Reporting mandates the Council attaches to appropriations. **No printed totals to reconcile against** — this is a list of conditions, not dollars.

| Column | Type | Meaning |
|--------|------|---------|
| `item_number` | text | Condition item number (synthetic/sequential for pre-FY2019 docs that don't number their items — see anomalies). |
| `agency_name` | text | Agency the condition binds. |
| `agency_code` | text | Numeric agency code. |
| `units_of_appropriation` | text | Unit(s) of appropriation the condition attaches to. |
| `num_units` | number | Count of units referenced. |
| `report_deadlines` | text | Reporting deadline date(s), where stated. |
| `coverage_period` | text | Period the report must cover, where stated. |
| `condition_text` | text | Full text of the condition. |

## `data/{year}/capital/{year}_capital_projects.csv`

Section 254 changes to the adopted capital budget.

| Column | Type | Meaning |
|--------|------|---------|
| `part` | text | Document part/section. |
| `agency` | text | Agency the project belongs to. |
| `budget_line` | text | Capital budget line ID. |
| `sub_id` | text | Sub-project ID within the budget line. **Not a Checkbook contract key** — there is no clean join from here into spending data (see anomalies). |
| `boro` | text | Borough: M/X/K/Q/R (Manhattan/Bronx/Brooklyn/Queens/Staten Island). |
| `fy1` | number | Allocation in the adoption year. |
| `fy2`–`fy4` | number | Out-year allocations. |
| `sponsor` | text | Sponsoring Council Member surname; co-sponsored rows list several. |
| `title` | text | Project title. |
| `building_code` | text | Building code, where applicable. |
| `school_code` | text | School code (DOE/SCA projects). |

**Document-type variance:** FY2025/FY2026/FY2027 (and the backfilled FY2020/FY2022/FY2023/FY2024) use the "Capital Project Detail" schedule and reconcile against printed `TOTALS FOR <agency> (N PROJECTS)` subtotals. **FY2025's canonical capital detail** is parsed from the Council-version supporting-detail book (`fy25_capital_projects.csv`) and reconciles **30/30** agency subtotals plus both grand totals — Part I $775M / 1,327 projects, Part II $158,992,000 / 181 projects, Part III cross-tab 106/106 entities — making it directly comparable to FY2026/FY2027. A separate FY2025 "Appropriation Changes" resolution book (all executive-capital changes, ~$5.2B) is a *different* document type — a different schema (no borough/sub_id/sponsor, adds an `action` column) with no subtotals — retained for provenance as `fy25_capital_changes_appropriation.csv` and labeled `NOT RECONCILABLE`.

## `data/{year}/transparency-resolutions/` — `resoNN_*.csv` + `{year}_transparency_all.csv`

Post-adoption discretionary designations, rescissions, and purpose changes. **No printed totals** (labeled `NOT RECONCILABLE`); the only internal check is that transfers (rescind + re-designate) net to zero.

| Column | Type | Meaning |
|--------|------|---------|
| `resolution` | text | Which Transparency Resolution (e.g. "Reso 1"). |
| `date` | date | Adoption date of the resolution. |
| `chart` | text | The source chart/initiative the row came from. |
| `fiscal_year` | number | The fiscal year the designation applies to. **May differ from the containing file's year** — a `{year}_transparency_all.csv` embeds prior-year rows (see anomalies). Always filter on this column, not the filename. |
| `action` | text | `designate` / `rescind` / `purpose_change`. **Rescissions carry negative `amount`.** |
| `source` | text | Funding source/initiative. |
| `council_member` | text | Sponsoring Council Member surname. |
| `organization` | text | Recipient. **Low text-confidence FY2010–2013** (see anomalies) — financial columns remain reliable. |
| `program` | text | Program/site. |
| `ein` | text | Recipient tax ID (9 digits) — reliable across all years. |
| `amount` | number | Dollars (negative for rescissions). |
| `agency` | text | Implementing agency. |
| `agy_num` | text | Numeric agency code. |
| `ua` | text | Unit of appropriation. |
| `purpose` | text | Free-text use description. |
| `flags` | text | Parser-emitted quality/notes flags. |

## `data/combined/`

Cross-year roll-ups built by [`code/build_combined.py`](code/build_combined.py). Same columns as the per-year files with a leading `year` column, plus derived `category_canonical` and `initiative_canonical` columns (see below).

- `all_years_awards.csv` — `year, category, category_canonical, initiative, initiative_canonical, award_type, member, organization, program, ein, amount, agency, purpose` (FY2015–FY2027; `purpose` is carried through so source-distinct rows are not collapsed into false duplicates — see DATA-ANOMALIES #10)
- `all_years_initiatives.csv` — `year, category, category_canonical, agencies, initiative, initiative_canonical, amount`

**`initiative_canonical`** is a **derived** field, not from source: it is the stable longitudinal key for an initiative across years. `initiative` still preserves the exact source spelling; `initiative_canonical` unifies the spellings the City used for the *same* program (e.g. `&`/`and`, curly vs. straight apostrophe, a leading `*` marker). Join on `initiative_canonical` for year-over-year analysis; cite `initiative` when quoting a specific document. Derivation: `initiative_canonical = initiative_name_crosswalk[initiative]` if the raw spelling is mapped, else a deterministic house-style normalization of `initiative`. See DATA-ANOMALIES #17.

**`category_canonical`** is likewise a **derived, editorial** field: the stable key for a category (the viz "Fund" axis) across years. `category` preserves the exact source label; `category_canonical` unifies the labels the City used for the *same* program area — an ALL-CAPS era vs Title Case, a `Services`/`Initiative` suffix drift, plurality, and the *Senior Services → Older Adult Services* rename. Derivation: a split override on `(category, initiative)` if present (a few early compound categories are split at the initiative level), else `category_name_crosswalk[category]`, else the raw category verbatim (retired categories are left as-is). Unlike `initiative_canonical`, these merges reflect **human editorial judgment** (confirmed against the organizations funded under each name), not just mechanical normalization. See DATA-ANOMALIES #18.

## `data/combined/category_name_crosswalk.csv`

Maps collision-prone raw category labels to a canonical program-area name. One row per non-identity mapping; categories left as-is are not listed.

| Column | Type | Meaning |
|--------|------|---------|
| `raw_category` | text | A verbatim `category` label as it appears in a source-year CSV. |
| `initiative` | text | Blank = the rule applies to the whole category. A specific initiative = a **split override** (a compound category whose lines route to different modern homes); it takes precedence over any category-level rule. |
| `category_canonical` | text | The canonical program-area name this maps to. |
| `basis` | text | `casing` (ALL-CAPS→Title Case), `editorial` (confirmed name merge / rename), or `split-crossref` (compound category resolved at the initiative level). |

## `data/combined/initiative_name_crosswalk.csv`

Maps each collision-prone raw initiative spelling to one canonical program name. **One row per raw spelling that participates in a collision group** (spellings that never collide are normalized on the fly by `build_combined.py` and are not listed here).

| Column | Type | Meaning |
|--------|------|---------|
| `raw_initiative` | text | A verbatim `initiative` spelling as it appears in a source-year CSV. |
| `initiative_canonical` | text | The unified program name every spelling in this group maps to. |
| `tier` | text | `mechanical` (case / whitespace / `&`-`and` / apostrophe / leading `*` — auto-safe) or `review` (hyphenation / dropped-word — maintainer-gated). |
| `confidence` | text | `high` (mechanical) or `review`. **Do not treat a `review` row as an authoritative merge until a maintainer has accepted it.** |
| `note` | text | Pipe-delimited cause tags (e.g. `curly-apostrophe`, `ampersand-vs-and`, `hyphenation`). |

## `data/combined/legistar_crosswalk.csv`

Links each budget **source document** to its NYC Council **Legistar** legislative record. **One row per document, FY2008–FY2027** (covers years not yet parsed to CSV).

| Column | Type | Meaning |
|--------|------|---------|
| `fiscal_year` | number | FY2008–FY2027. |
| `document_type` | text | `schedule_c`, `terms_conditions`, `capital_a`, `capital_b`, `transparency_reso`, or `transparency_reso_NN`. |
| `local_file` | text | Repo-relative path to the source PDF (`source/FYnn/…`); blank for matter-only rows. |
| `legistar_matter_number` | text | e.g. `Res 0974-2025`. |
| `legistar_url` | text | Legistar detail-page URL. |
| `adoption_date` | date | Date the matter was adopted. |
| `status` | text | `confirmed` (matter verified), `candidate` (anchor/exhibit, not upgraded), or `not_located` (no matter found). **Do not cite a candidate/not_located row as authoritative.** |
| `notes` | text | Provenance qualifier (e.g. "inferred exhibit"). |

---

## How the files join

- **`ein`** — the primary cross-system key (award ↔ transparency ↔ external IRS 990 / Checkbook). 9 digits, no hyphens. Watch the fiscal-sponsor pooling caveat above.
- **`(ein, amount)`** — the join between the expense-disclosure dataset and the Schedule C award files, as a multiset within one fiscal year. Never `ein` alone (fiscal sponsors), never the sponsoring member (the disclosure's roster is export-time).
- **`mocs_id`** — expense disclosure, FY2024+ only: a per-row identifier within one snapshot. Not stable across snapshots; a join to registered contracts / Checkbook is unverified.
- **`initiative_canonical`** — the stable key for tracking one initiative across years in the combined roll-ups. Join on this, not the raw `initiative`, for longitudinal analysis (the City's spelling of an initiative drifts year to year — see DATA-ANOMALIES #17).
- **`category_canonical`** — the stable key for tracking one category (Fund/program area) across years. Join on this, not the raw `category`, for longitudinal Fund-axis analysis (an editorial consolidation — see DATA-ANOMALIES #18).
- **`member` / `council_member` / `sponsor`** — surname only; join to a Council roster for district/full name.
- **`fiscal_year` / folder year** — align on the *column*, not the filename, for transparency files.
- **`legistar_matter_number`** — the crosswalk is the bridge from a document to its legislative record; no budget CSV carries the matter number inline.
