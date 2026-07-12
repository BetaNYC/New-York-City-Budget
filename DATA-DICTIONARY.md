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

Detail breakouts re-sorted by funding stream: `_a_aging` (Aging Discretionary), `_b_local` (Local Initiatives — adds an `agency` column), `_c_youth` (Youth Discretionary). **These are subsets of the award body — do not add them to the Schedule C total.**

| Column | Type | Meaning |
|--------|------|---------|
| `member` | text | Sponsoring Council Member surname. |
| `organization` | text | Recipient organization. |
| `program` | text | Program/site. |
| `ein` | text | Recipient tax ID (9 digits). |
| `amount` | number | Dollars. |
| `agency` | text | Implementing agency (`_b_local` only). |
| `purpose` | text | Free-text use description. |

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

**Document-type variance:** FY2026/FY2027 (and the backfilled FY2020/FY2022/FY2023/FY2024) use the "Capital Project Detail" schedule and reconcile against printed `TOTALS FOR <agency> (N PROJECTS)` subtotals. FY2025 is the "Appropriation Changes" resolution — a different schema (no borough/sub_id/sponsor, adds an `action` column) with no subtotals; labeled `NOT RECONCILABLE`.

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

Cross-year roll-ups built by [`code/build_combined.py`](code/build_combined.py). Same columns as the per-year files with a leading `year` column, plus a derived `initiative_canonical` column (see below).

- `all_years_awards.csv` — `year, category, initiative, initiative_canonical, award_type, member, organization, program, ein, amount, agency, purpose` (FY2015–FY2027; `purpose` is carried through so source-distinct rows are not collapsed into false duplicates — see DATA-ANOMALIES #10)
- `all_years_initiatives.csv` — `year, category, agencies, initiative, initiative_canonical, amount`

**`initiative_canonical`** is a **derived** field, not from source: it is the stable longitudinal key for an initiative across years. `initiative` still preserves the exact source spelling; `initiative_canonical` unifies the spellings the City used for the *same* program (e.g. `&`/`and`, curly vs. straight apostrophe, a leading `*` marker). Join on `initiative_canonical` for year-over-year analysis; cite `initiative` when quoting a specific document. Derivation: `initiative_canonical = initiative_name_crosswalk[initiative]` if the raw spelling is mapped, else a deterministic house-style normalization of `initiative`. See DATA-ANOMALIES #17.

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
- **`initiative_canonical`** — the stable key for tracking one initiative across years in the combined roll-ups. Join on this, not the raw `initiative`, for longitudinal analysis (the City's spelling of an initiative drifts year to year — see DATA-ANOMALIES #17).
- **`member` / `council_member` / `sponsor`** — surname only; join to a Council roster for district/full name.
- **`fiscal_year` / folder year** — align on the *column*, not the filename, for transparency files.
- **`legistar_matter_number`** — the crosswalk is the bridge from a document to its legislative record; no budget CSV carries the matter number inline.
