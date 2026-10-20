# Data Dictionary

Every column in every CSV this repository produces, what it means, and how the files join to each other. For *how each fiscal year is parsed* and its reconciliation status, see [`code/PARSING.md`](code/PARSING.md). For known data limitations, see [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md).

**Generated:** 2026-07-08. Covers FY2009–FY2027.

> **2.0 (2026-10-14): PDF-derived files are retired.** The Schedule C (awards, initiatives,
> appendices), Terms & Conditions, per-year §254 capital, transparency-resolution,
> `data/combined/` and `data/recovered/` files below were extracted from the adopted-budget PDFs.
> Their definitions stay here because the files stay in the repository as a historical record;
> they are not served by `@betanyc/nyc-budget-mcp` 2.0 or shown on the Pages site, and should not
> be cited as current. The MCP serves only `data/{year}/expense_disclosure/`,
> `data/disclosure_years.csv` and `data/capital/` (`council_capital_awards.csv`,
> `council_vs_omb_by_budget_line.csv`).

---

## Coverage at a glance

Not every document type exists (or is machine-readable) for every year. This matters: the discretionary **award** files — the ones with per-organization EINs — only exist **FY2015 onward** (FY2015 is the earliest Schedule C year with an award file). For FY2009–FY2014 the repo has initiatives-level Schedule C files only. The PDFs for those years do print per-organization award rows with EINs, and FY2008 prints 1,674 member-item rows without EINs; no parser here extracts them. **Corrected 2026-10-20:** earlier text said FY2009–FY2014 have no organization/EIN detail because designations were made after adoption. See [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) §2 for the evidence.

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

**Separately, the Council's expense funding disclosure workbooks give an EIN-level award list for FY2009 and every year FY2011–FY2027** (`data/{year}/expense_disclosure/`, below). It is a parallel dataset from a different source and a later moment, not a fill for the Schedule C gaps in this table.

"awards" = the `_awards.csv` file with per-organization EINs. **EIN-keyed analysis of the Schedule C files is valid FY2015–FY2027.** The FY2009–FY2014 files are initiatives-only; the PDFs print award rows with EINs that were never extracted (corrected 2026-10-20, DATA-ANOMALIES §2). (The budget MCP's 1.x award tools served these files; 2.0 removed them and serves the disclosure instead.) See [`DATA-ANOMALIES.md`](DATA-ANOMALIES.md) for the full gap list.

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
designation; exact copies are kept and flagged, see `duplicate_group`), **FY2009 and FY2011–FY2027**
(FY2013–FY2027 from the RnD site; FY2009, FY2011, FY2012 from the Council's own workbooks as
archived by the Internet Archive; FY2010 deliberately not loaded, see `data/disclosure_years.csv`
below). A **parallel
award-level dataset**: it is not derived from the adopted-budget PDFs, it does not feed the
Schedule C files above, and its totals are not the adopted Schedule C totals. Built by
`code/parse_expense_disclosure.py --write`; per-year counts, totals and printed-total
reconciliation are in `code/PARSING.md` and each year's `{year}_expense_reconciliation.txt`.

Status values beyond Cleared/Pending, all `status_norm = other`, raw value kept: `Government` (FY2011 136 rows, $2.6M; FY2012 49 rows, $235.2M: a City agency is the recipient), `Pending FC Clearance` (FY2011, 3), `CBO Defunded` (FY2012, 155 rows, all $0). None is defined by the Council; report `Government` as its own line, never as cleared (#89 B3, B4).

Column names follow the disclosure's own fields, not the Schedule C vocabulary (`legal_name`, not
`organization`; `council_member`, not `member`).

| Column | Type | Meaning |
|--------|------|---------|
| `fiscal_year` | int | From the workbook's **file name**. FY2013, FY2014 and FY2016 have no Fiscal Year column; where one exists it agrees in every row. |
| `mocs_id` | text | Mayor's Office of Contract Services ID (`FY25 00001`). **FY2024+ only**, blank before. Identifies a row within one snapshot; not stable across snapshots (DATA-ANOMALIES §22). Its join to registered contracts / Checkbook is unverified. |
| `od_mocs_id` | text | **Cross-reference, not a source** (#89 A4): the MOCS ID NYC Open Data `4d7f-74pe` gives the same designation (`FY09 5052`), FY2009–FY2021 only, the only MOCS IDs that exist for those years. Set only on an **unambiguous pair**: within the fiscal year, this is the only Council row and the Open Data row the only Open Data row in their (EIN, amount rounded half-up to whole dollars) bucket, and the amounts agree per `od_match`. Blank otherwise (a shared bucket, a blank EIN, no Open Data row, or FY2022+): 54,970 of the 89,923 FY2009–FY2021 rows carry one. Open Data's 8-digit EINs (a lost leading zero) are padded before matching. Read from the committed extract `source/open-data-4d7f-74pe/4d7f-74pe-keys.csv.gz`. Two FY2009 values repeat because Open Data repeats them (`FY09 Not an Award` ×2, `FY09 2039` ×2). Open Data's statuses, names and addresses are never copied in. |
| `od_match` | text | How the amounts of an `od_mocs_id` pair agree: `exact`, `rounded_cents` (Open Data rounded FY2009–FY2011 amounts to cents: our `7481.296758`, theirs `7481.30`) or `rounded_dollars` (FY2012 on: `6333.33` vs `6333`). Blank exactly when `od_mocs_id` is. |
| `source` | text | Funding stream as the Council names it: `Local`, `Youth`, `Aging`, `Speaker's Initiative`, or a named citywide initiative. |
| `council_member` | text | Sponsor as printed. **The roster at the time the workbook was exported, not at adoption** — never a join key (see DATA-ANOMALIES §21). A substring of it blends people: `Levin` is in `Levine`, `Won` in `Wong`. |
| `council_member_id` | text | **Derived** (GitHub #72): the Legistar person ID the printed name resolves to **for that fiscal year**, from `data/disclosure_council_member_crosswalk.csv`; blank unless `council_member_type` is `member` or `member_outside_fy`. `Levin` is 7567 (Stephen T. Levin), `Levine` 7634 (Mark Levine). Filter on this, not on the name, to mean one person. |
| `council_member_type` | text | **Derived** (GitHub #72). `member` — exactly one Legistar person has the printed surname (and initial, if printed) and a recorded vote in that fiscal year. `member_outside_fy` — exactly one person has the name, but no vote that year: the export-time roster naming someone not yet or no longer in office (FY2025 `Wong`, FY2021 `Aviles`, FY2020 `D. Diaz`); the ID is given, the type says it is not that year's member. `ambiguous` — two people of that name voted that year (FY2014 and FY2022 `Barron`, FY2014 `Vallone`); no ID, never guessed. One such value is typed `member` by a recorded **file convention** instead: FY2021 bare `Diaz` is Ruben Diaz, Sr. (7744), because the same workbook prints Darma V. Diaz as `D. Diaz` (crosswalk `method` begins `file_convention`; see below). `unresolved` — no Legistar member has the name: FY2014 `NA` and three multi-member values (`Barron & Eugene`, `Lappin, Koppell/Citywide`, a nine-member FY2011 list); 4 values, 56 rows. **Printed abbreviations** (`LABEL_CONVENTIONS`, 2026-10-16, decided by Marvin on the evidence,
delegated by Noel Hidalgo). FY2009–FY2013 print `CC` where FY2014–FY2027 print `Speaker`, and no
year prints both. The evidence is NYC Open Data `4d7f-74pe` (the full copy), joined to these rows
on `od_mocs_id` = `mocs_id` and re-verified 2026-10-17: every `CC` row that pairs with an Open
Data row is `Speaker` there, 895 of 895 (FY2009 224, FY2011 245, FY2012 219, FY2013 207; the
other `CC` rows have no Open Data pair). The FY2010 Internet Archive workbook, which is not
loaded, also prints `CC` (50 rows, never `Speaker`), consistent with FY2009–FY2013. So `CC` is
typed `speaker`. FY2009 also prints the borough codes `BK`, `BX`, `MN`, `QN` beside `SI`
(already read as Staten Island). Paired with Open Data they are `… Delegation` every time: `QN`
37/37, `MN` 35/35, `SI` 23/23, `BK` 18/18, `BX` 13/13, with no paired row disagreeing. They are
typed `delegation`. FY2009 prints both a code and the bare borough name in the same year (`BK`
18 and `Brooklyn` 50), as it already did for `SI` / `Staten Island`; both are typed
`delegation`. The printed value stays in `council_member`; `method` is
`file_convention:CC=Speaker`, `file_convention:QN=Queens_Delegation`, and so on, and `evidence`
carries the counts. The rule applies to the value in any year. The build stops if a year ever
prints both `CC` and `Speaker`, or a code and that borough's spelled-out `… Delegation` (no year
does; the bare name does not trip it). Multi-member values stay `unresolved`.

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

**Outcome, all loaded years FY2009 and FY2011–FY2027 (conventions as of 2026-10-16), as
(year, value) pairs / rows:** `member` 912 / 113,547 (one by file convention, 123 rows);
`member_outside_fy` 3 / 341; `ambiguous` 3 / 189; `unresolved` 4 / 56 (was 12 / 1,196 before
the printed-abbreviation rule); `speaker` 18 / 7,193; `delegation` 97 / 7,870; `citywide` 8 / 434;
`district_label` 5 / 384; `blank` 18 / 26,530. 156,544 rows in all, the disclosure table's count.
`python3 code/build_member_crosswalk.py` prints these.

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

## `data/disclosure_years.csv`

One row per fiscal year of the expense disclosure, loaded or not. Written by
`code/parse_expense_disclosure.py --write` (checked by `--check`). Sums are this repo's arithmetic
on the rows, never a Council figure.

| Column | Meaning |
|--------|---------|
| `fiscal_year` | The year. |
| `loaded` | `yes`, or `no` for a year whose workbook exists but is deliberately not in the dataset (FY2010). |
| `source_kind` | `council_rnd` (rnd.council.nyc.gov, `source/expense-funding-disclosure/`) or `internet_archive` (a Wayback capture in `source/wayback-council/files/`). |
| `source_path`, `url`, `wayback_timestamp`, `retrieved`, `sha256` | Where the workbook is in the repo, its original URL, the capture timestamp (Internet Archive only), the date we downloaded it, and its sha256 (equal to the folder's `MANIFEST.csv`; the build stops if the file differs). |
| `sheet`, `award_rows` | The sheet read, and the rows kept. |
| `cleared_rows` … `other_amount`, `total_amount` | Rows and dollars by `status_norm`, and the total. |
| `row_flagged` | Rows with a `row_flag`. |
| `early_snapshot` | `yes` for a workbook frozen while much of it was Pending and never revised (FY2009, FY2013): do not headline its Cleared total. |
| `note` | Why a year is an early snapshot or not loaded, with its counts. |

## `data/capital/` (Council capital, structured sources only)

Built by `code/build_capital_council.py`; overview, sources per year and code meanings in
[`data/capital/README.md`](data/capital/README.md). A separate dataset from the PDF-derived
`data/{year}/capital/` files above.

### `council_capital_awards.csv`

| Column | Meaning |
|--------|---------|
| `report_year` | The Council's capital list the row comes from (the workbook's year, or t474's `Reported`). |
| `amount_fy` | The fiscal year the amount is for: the report year, or an out-year. Blank only on a `split_record_amount_unknown` row. |
| `project_id` | The Council's ID as printed (`E  CN459`, `E CN0001`, `CC0001`): unique within a year only, internal to budget negotiations, **not** an FMS project ID. Blank in FY2015 (none printed). |
| `borough` | As printed: `K M Q R X`, `C` citywide; `A` and lower-case values are kept, meaning unconfirmed. |
| `budget_line` | As printed (`P  D018`, `PW-DN846`). Blank in FY2016 (none printed). FY2015's comes from its "Project" column, which holds budget lines. |
| `budget_line_norm` | **Derived:** agency code, one space, line (`P D018`); blank when `budget_line` has no budget-line shape. The join key to OMB. |
| `council_district` | As printed: a comma list of district numbers and codes (00 Speaker, 88–99; `data/capital/README.md`). **Unusable for t474 years**: Open Data collapsed the lists into one number. |
| `sponsor` | As printed: member surnames, delegations, caucuses, "Technical Adjustments", "Admin". |
| `title`, `description` | As printed. t474's FY2019 `title` often names the organization. |
| `amount` | Dollars, as printed; negative on some technical adjustments; blank only on a flagged split record. |
| `source_kind` | `council_workbook` or `open_data_t474`. |
| `source_file`, `source_row` | The workbook and its 1-based sheet row, or the t474 file and the row's SODA `:id`. |
| `row_flag` | `split_record_amount_unknown`: a t474 record broken across rows whose amount the Council's own files cannot prove (data/capital/RECONCILIATION.md §2). Blank otherwise. |

### `omb_capital_budget_council_lines.csv` and `omb_commitment_plan_council_lines.csv`

OMB's rows on Council-series budget lines (the line part starts with `D`), every release, values
as served. Capital Budget (`46m8-77gv`): `pub_date`, `release` (`adopted` for the last release of
each first fiscal year, published in July every year 2018–2026), `proj_type`, `budget_line`,
`budget_line_norm`, `budget_line_title`, `funding` (C City non-exempt, E City exempt, F federal,
S state, P private), `yr1_fy`, `year1_amt`…`year4_amt` (**dollars**; year N is `yr1_fy` + N − 1,
per OMB's data dictionary), `source_row` (`:id`). Commitment Plan (`2cmn-uidm`): the same idea
with `funding` CITY / NON CITY, `num_yrs_prsnt`, and `year1_amt_k`…`year5_amt_k` in
**thousands of dollars**.

### `council_vs_omb_by_budget_line.csv`

`report_year`, `budget_line_norm`, `omb_pub_date` (the adopted release used), `council_rows`,
`council_y1` / `omb_y1` (the report year), `council_y2` / `omb_y2` (the next year), `verdict`:
`match` (both years equal to the dollar), `differ`, `council_only`, `omb_only`. OMB amounts are
summed over funding sources. This repo's arithmetic, not a Council or OMB figure.
