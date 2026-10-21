# Changelog

All notable changes to `@betanyc/nyc-budget-mcp` are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

Nothing yet.

## 2.0.1 — unreleased (built 2026-10-20; not tagged, not published)

A patch: the index gains empty tables; no tool, argument or answer changes.

### Added (index, 2026-10-21)
- **Is each record on NYC Open Data?** `scripts/open-data.mjs` loads `data/open_data/`
  (`code/build_open_data_crosswalk.py`, plan `research/2026-10-21-open-data-tracking/PLAN.md`) into
  `open_data_crosswalk`, `open_data_coverage`, `open_data_datasets` and `open_data_rules`. Every row
  must name a record the index holds, or the build stops. Rows about PDF-derived records (T&C
  units, §254 rows) follow the PDF gate, so this index carries none of them. The index grows
  about 11 MB (41 MB → 52 MB). **No tool reads these tables yet** (`test/open-data.test.js`); the
  explorer shows them. Version stays 2.0.1: it is not published, so the version guard passes.

### Changed (index)
- **The index build reads `data/pdf_years.csv` and serves closed rows only (GitHub #102).**
  `scripts/build-index.mjs` creates the reviewed-PDF tables (`pdf_years`, `pdf_capital_sd`,
  `pdf_capital_sd_orgs`, `pdf_capital_sd_totals`, `pdf_terms`, `pdf_terms_units`,
  `pdf_terms_fsr`, `pdf_schedule_c`, `pdf_schedule_c_categories`,
  `pdf_schedule_c_initiatives`, the derived `pdf_sc_disclosure`, and `pdf_review`), configured
  in `scripts/pdf-families.mjs`. A family loads only when its status in `data/pdf_years.csv` is
  `closed`. None is yet (FY2027 capital §254, Terms & Conditions and Schedule C are `reviewed`), so
  the shipped `data/budget.db` has these tables empty.
- **No tool reads them.** `test/pdf-families.test.js` builds an index with the reviewed rows and
  requires every tool's answer to be identical to the default index's; it also checks that no
  `src/` file names a `pdf_` table. `test/no-pdf-data.test.js` allows the `pdf_*` tables only
  with zero non-closed rows.
- **`--include-reviewed --out <file>`** builds a separate index with the `reviewed` families, for
  the explorer's local or demo build. It refuses to write `data/budget.db`.
- `pdf_sc_disclosure` pairs Schedule C rows with the disclosure by a line-for-line port of
  `code/schedc/disclosure.py` (PR #125); the build stops if the port disagrees with the promoted
  file on any row.

### Related, not in the package
- **Budget explorer (2026-10-20).** `viz/explorer/` is an in-browser explorer (DuckDB-WASM over
  Parquet) for exactly this server's data, published at
  `betanyc.github.io/New-York-City-Budget/explorer/` and linked from the Pages notice. Its data
  build runs `scripts/build-index.mjs` and exports `data/budget.db` to Parquet; it never parses a
  CSV. A new CI job runs a parity test: per fiscal year, row counts and dollar totals (by status
  for the disclosure, by year for capital), every row and column, and the explorer's queries
  against `searchDisclosure`, `searchCapital` and `compareCapitalToOmb` must all agree with this
  index. `deploy-viz.yml` now builds the site (index, data, tests, app) instead of publishing
  `viz/` as-is, and also runs on `data/**`, `mcp/scripts/**` and `mcp/src/fold.ts` changes.
  Nothing in the package changes.
- **Explorer, reviewed PDF data (2026-10-20, GitHub #102).** `npm run data -- --include-reviewed`
  (local or demo builds only; the public deploy never passes it) adds the FY2027 Schedule C, capital
  §254 and Terms & Conditions tables, labeled "checked, review in progress", with a PDF viewer that
  highlights each row. Nothing in the package changes.

## 2.0.0 — unreleased (built 2026-10-14; not tagged, not published)

2.0 rebuilds the server on **structured sources only**: the NYC Council's expense funding
disclosure spreadsheets and its capital designations (the Council's capital workbooks and NYC
Open Data), with a by-budget-line comparison to OMB's adopted capital budget. Everything
extracted from the adopted-budget PDFs, and every tool built on it, is retired. The retired data
stays in the repository for history; none of it is in the package.

**What upgrading means.** The last published version is 1.3.1. 1.4.0 and 1.5.0 were never tagged
or published, so 2.0.0 follows 1.3.1 directly and supersedes both: 1.4.0's appendix rows are
retired with the rest of Schedule C, and 1.5.0's `search_disclosure_awards` ships here (its
notes are folded in below and kept, as written, in the 1.5.0 entry).

### Breaking changes
- **Node 22 or newer is required** (`engines` was `>=18`). Node 18 and Node 20 are past end of life. CI now tests Node 22 and 24.
- **Six tools removed.** Calling one returns an error that names its replacement, or, for the
  three with none, says so and points to where to look instead.

  | 1.x tool | In 2.0.0 |
  |---|---|
  | `search_awards` | `search_disclosure_awards` |
  | `get_awards_by_ein` | `search_disclosure_awards` with `ein` |
  | `search_capital_projects` | `search_council_capital` |
  | `search_transparency_resolutions` | No replacement tool yet; the error points to `nyc-council-mcp` (Finance `modification` items), the disclosure rows and the PDFs |
  | `get_terms_conditions` | No replacement tool yet; the error points to the Terms and Conditions PDFs in `source/FYNN/` |
  | `get_legistar_link` | Removed; use `nyc-council-mcp` for Legistar records |
  | `list_available_fiscal_years` | Kept, rebuilt on the structured datasets |

- **`get_legistar_link` is removed, not rewired**, because it depends on the PDF documents: its
  crosswalk (`data/combined/legistar_crosswalk.csv`) is keyed on the adopted-budget PDFs
  (`document_type` schedule_c / capital_a / capital_b / terms_conditions / transparency_reso,
  `local_file` a PDF path), which 2.0 no longer serves, and 10 of its 255 rows are researchers'
  `candidate` anchors (FY2009–FY2014 Schedule C, FY2015–FY2018 Terms & Conditions) rather than
  verified links. A Legistar index keyed on structured data could return later.
- **Figures from 1.x do not reproduce.** 1.x served the adopted Schedule C and §254 capital as
  extracted from PDFs; 2.0 serves the Council's disclosure (a later snapshot that includes
  post-adoption designations) and its capital lists. They are different sources.
- **The package no longer ships** Schedule C awards, initiatives or appendix rows, recovered
  sidecars, Terms & Conditions, §254 capital, transparency resolutions or the Legistar crosswalk.
  `test/no-pdf-data.test.js` fails if any of them, or any file the index build reads from a
  PDF-derived path, comes back.

### Added
- **`search_council_capital`** — the Council's capital designations, FY2015–FY2017 and
  FY2019–FY2027 (16,916 rows; FY2018 is in no source found). Filters: `fiscal_year` (the
  Council list's year), `amount_fy`, `budget_line` (exact, normalized to `AGENCY LINE`;
  `PD018` refused), `project_id` (exact, case and spacing ignored), `sponsor` (literal
  substring, lists every value matched) or `sponsor_exact`, `borough` (exact, case-sensitive),
  `council_district` (a district inside the workbook's printed list; never a t474 row, whose
  lists Open Data collapsed into one number), `title` and `description` (literal substrings),
  `min_amount`, `max_amount`, `limit`. True match count; the list's own-year amounts and
  out-year amounts totaled separately over every match; rows with no amount (split t474
  records) counted and kept out of totals; highest amount first, ordered before the limit; each
  year's source file, URL or Internet Archive capture, retrieval date and sha256 (computed at
  build from the committed file and checked against its manifest); a caveat on every answer
  (FY2018 missing; codes A, 80, CC, PN unconfirmed; links below the budget line would be by line
  and title only and are not made; no contract-level data).
- **`compare_capital_to_omb`** — `data/capital/council_vs_omb_by_budget_line.csv` (1,425 line-year
  comparisons over 515 distinct budget lines, FY2019–FY2027): per report year and Council-series budget line, the Council total vs OMB's
  adopted release for that year and the next, with a verdict. Labeled as this repo's arithmetic,
  not a Council or OMB reconciliation; an absent side shows `—`, never `$0`; lines that disagree
  first.
- **`search_disclosure_awards` now covers FY2009, FY2011 and FY2012** from the Council's archived
  workbooks (Internet Archive captures, retrieved 2026-10-14): 156,544 rows in all. New on each
  row where present: `od_mocs_id` and `od_match` (the MOCS ID NYC Open Data `4d7f-74pe` gives the
  same designation, FY2009–FY2021, only on an unambiguous pair; a cross-reference, not a source)
  and `row_flag`. New exact filters `mocs_id` and `od_mocs_id`.
- **Every disclosure answer states the coverage**: FY2009, FY2011–FY2027; FY2010 not included;
  FY2009 and FY2013 early snapshots. `fiscal_year: 2010` returns the recorded reason instead of an
  empty search. When every matched year is an early snapshot, the Cleared line reads "early
  snapshot, not a headline"; a total that mixes early and ordinary years says so and marks them
  in the per-year split.
- Disclosure notes for rows with a `row_flag` (`not_an_award`: two FY2009 lump allocations on the
  City's EIN, kept and counted as published) and for rows that print no grantee EIN (53 rows,
  $159,951,020.83, most of it FY2009 initiative-level rows such as "School Budget Restoration",
  $120,000,000). Both stay in the totals; the note says how much. Those 53 rows carry
  `row_flag` `no_grantee_ein` (a rule: blank or `NA` EIN), and each row says "No grantee EIN
  printed by the Council. Often a city program rather than a nonprofit." `row_flag` can join
  flags with `;`.
- FY2009–FY2013 `CC` is typed `council_member_type = speaker` and the FY2009 borough codes
  `BK`/`BX`/`MN`/`QN` `delegation` (they were `unresolved`); `council_member` still shows the
  printed value. `unresolved` drops from 1,196 rows to 56.
- Per-year disclosure provenance now comes from `data/disclosure_years.csv` (Council RnD URL or
  Internet Archive capture, retrieval date, sha256, early-snapshot flag, note) into a
  `disclosure_years` table; the build stops if a year's row count disagrees with it.
- `meta.inputs` in the index: every repo file the build read.
- Tests: `test/no-pdf-data.test.js` (tables allowlisted; every build input on a structured
  allowlist; the `npm pack` file list is exactly eight files), `test/tools.test.js`,
  `test/disclosure-v2.test.js`, `test/capital.test.js`. Mutation-checked: folding out-years into
  the own-year total, a year-first sort, prefix or substring matches on `budget_line`,
  `project_id`, `council_district`, `sponsor_exact` and `od_mocs_id`, case-folding `borough`,
  live LIKE wildcards in `title`, tokenizing t474 districts, an invented `0` for a split record or
  an absent OMB side, a capital sha256 that is not the file's, an `awards` table or a crosswalk
  read coming back, shipping `retired-1.x/`, dropping the early-snapshot label, the coverage
  line, FY2010's reason, the mixed-years warning, the `row_flag` or EIN-less note, the per-year
  capital sources or the removed-tool notes each fail at least one test. One mutant survives as
  equivalent: SQLite already sorts NULL amounts last in a descending sort.

### Changed
- `list_available_fiscal_years` reports, per fiscal year, the disclosure (rows, Council RnD or
  Internet Archive, retrieval date, early-snapshot flag, or NOT LOADED), the capital list (rows,
  Council workbook or NYC Open Data t474-a92g, or MISSING) and whether the year is in the OMB
  comparison, then states the gaps.
- The disclosure caveat no longer points to `search_awards`; it says the disclosure is not the
  adopted budget's Schedule C. The disclosure footer names the Internet Archive source of
  FY2009, FY2011 and FY2012.
- Strict-schema alias hints rebuilt for the 2.0 tools (`council_member` on capital → `sponsor`,
  `district` on capital → `council_district`, `query` → the tool's text filters, `organization`
  → `legal_name` or, on capital, `title`).
- Shown disclosure amounts are rounded to cents; FY2009–FY2012 carry fractional amounts such as
  `7481.296758`. Totals are computed on the exact values.
- **Red-team fixes (2026-10-16).** FY2012's Cleared total is no longer labeled "(headline)":
  any matched year that is an early snapshot or prints statuses other than Cleared/Pending
  (FY2011, FY2012) drops the label, multi-year totals that include one say they mix years, and a
  note explains each such status (`Government`: City agencies as recipient; Open Data calls the
  FY2012 rows Cleared). Text filters match on folded text (NFKD, accents, curly quotes, dashes,
  case), so `Women's` finds `Women’s`. A blank text filter is an error, not "no filter"; filters
  are capped at 500 characters. `compare_capital_to_omb` says "line-year comparisons" (1,425 over
  515 distinct lines) and lists Council rows on lines outside the Council series that it does not
  compare (FY2021 `PW MN02A`, $304,000). An EIN error points to `legal_name` for the three odd
  published EINs. The package now ships `LICENSE` and `dist/fold.js`.
- **Review fixes (2026-10-17).** The "(headline)" label is decided per fiscal year, whatever the
  filter: any FY2011 or FY2012 match drops it, and the note gives the year's whole-year other
  statuses. A printed value pasted back exactly always finds its rows, including the garbled
  t474 sponsors (`OssΘ`, `AvilΘs`, `Avil├⌐s`): the folded twin is now skipped only where folding
  changes nothing but ASCII case. Folding also handles `ẞ`, dotless `ı`, zero-width characters,
  the okina and guillemets. The removed tools without a replacement now say where to look
  instead. The no-EIN note no longer repeats itself.
- **One license.** The README's licensing section now says BetaNYC's code, derived data and
  documentation are all MIT. It previously pointed the data at a separate CC BY-SA 4.0 file,
  which contradicted the repository's `LICENSE`; that second license is withdrawn. The Council's
  source documents remain public records, not covered by BetaNYC's license.
- Package size: 14.9 MB packed / 67.7 MB unpacked (1.5.0 build) → 8.9 MB / 41.3 MB (8 files: the index, `dist/`, README, LICENSE, package.json).
- `package.json`: version 2.0.0, description and keywords; the `enrich-crosswalk` script is
  gone. The 1.x tests and `scripts/enrich-crosswalk.mjs` are parked in `retired-1.x/` (not run,
  not shipped).
- **The index build fails loud and installs atomically.** `build-index.mjs` builds into a temp
  file, checks it with `scripts/verify-index.mjs` (a dataset with 0 rows, a loaded
  `data/disclosure_years.csv` year missing or short, or a published capital report year missing,
  is a stop), and only then renames it over `data/budget.db`. A failed build leaves the previous
  index in place. Found on Node 20 CI: npm 10 runs `prepare` even on `npm pack --ignore-scripts`,
  so the tarball test rebuilt the index (delete, then refill in place) while other test files
  read it, and they answered "The Council capital list covers (none)". `prepare` is now
  `scripts/prepare.mjs`, which honors `--ignore-scripts`.

### Data sources
- NYC Council expense funding disclosure workbooks, FY2013–FY2027, from
  `rnd.council.nyc.gov`, downloaded 2026-10-12 (`source/expense-funding-disclosure/`).
- FY2009, FY2011, FY2012: the Council's own workbooks, Internet Archive captures of 2025-02-12,
  retrieved 2026-10-14 (`source/wayback-council/`). FY2010's archived workbook is kept there but
  not loaded.
- Council capital workbooks: FY2015, FY2016, FY2017 and FY2026 from Internet Archive captures,
  FY2027 from `rnd.council.nyc.gov` (2026-10-12). NYC Open Data `t474-a92g` (Council capital,
  FY2019–FY2025), `46m8-77gv` (OMB Capital Budget), pulled 2026-10-14.
- Unchanged from 1.5.0: the Council-member crosswalk to Legistar person IDs, and the Census 2020
  ZCTA file behind `zip` / `zip_status`.

### What the data means (read before citing a figure)
- The **disclosure** notes in the 1.5.0 entry below all still hold: `council_member` is the
  export-time roster; addresses are mailing addresses; `duplicate_group`, soft hyphens, `#N/A`,
  `zip` / `zip_status`, FY2021 bare `Diaz` = Legistar 7744.
- **Early snapshots.** FY2009 (1,389 of 5,745 rows Pending) and FY2013 (2,644 of 4,987) were
  frozen and never revised by the Council; FY2013 also prints 18 citywide initiatives as one row
  each. Do not headline their Cleared totals.
- **`od_mocs_id` is a cross-reference, not a source.** Open Data's statuses, names and amounts
  are never copied in; blank where the pairing is ambiguous.
- **Capital `report_year` vs `amount_fy`.** A list's designations are its rows with `amount_fy`
  equal to the list's year; out-year rows are plans for later years.
- **Capital sums are this repo's arithmetic.** Only FY2015 and FY2016 print totals, and the rows
  equal them. t474's `council_district` is unusable (lists collapsed); its FY2019 `title` often
  names the organization.

## 1.5.0 — 2026-10-12 (never released; folded into 2.0.0)

> Kept as written. Its references to `search_awards`, `get_awards_by_ein` and
> `source/expense-funding-disclosure/MANIFEST.csv` as the provenance table describe 1.5.0; in
> 2.0.0 those tools are removed and provenance comes from `data/disclosure_years.csv`.

A new tool over a new source. **No existing tool's parameters, output or figures changed**;
`search_awards` and `get_awards_by_ein` still serve the adopted Schedule C exactly as in 1.4.0.

**1.4.0 was never tagged** (there is no `mcp-v1.4.0` tag; the last is `mcp-v1.3.1`), so it was
never released. Anyone upgrading from the published package gets 1.4.0's change, award totals
that **rise** because appendix rows are returned, together with this one. Read the 1.4.0 entry
below before comparing a figure with one published from 1.3.x.

### What the disclosure data means (read before citing a figure)
- **One snapshot.** Every disclosure row comes from the Council workbooks retrieved on
  2026-10-12. No row from an earlier pull is mixed in. Each answer names the file, sheet,
  retrieval date and sha256 prefix it used.
- **Addresses are grantee mailing addresses**, as the Council printed them. They are not where
  services were delivered. `zip`, `city` and `zip_status` describe the mailing address only.
- **`council_member` is the roster when the workbook was exported**, not necessarily the member
  who made the designation. `council_member_id` is the Legistar person that printed name
  resolves to for that fiscal year; `council_member_type` says why a row has no ID (`ambiguous`,
  `unresolved`, a delegation, a district label) or that the person had no recorded vote that
  year (`member_outside_fy`). A name two members carried in the same year is never guessed.
- **FY2021 bare `Diaz` is Ruben Diaz, Sr. (Legistar 7744)**, by a recorded file convention
  (decision 2026-10-13), not by the general rule. Both Diazes voted in FY2021, but the same
  workbook prints Darma V. Diaz as `D. Diaz`, so bare `Diaz` (123 rows) is read as the other one.
  The grantee addresses point the same way (of `Diaz`'s 46 Local rows, 18 have city Bronx; of
  `D. Diaz`'s 24, 14 are Brooklyn and none Bronx). Those are mailing addresses, so they support
  the reading; they do not prove it. The index build stops if that evidence changes.
- **`duplicate_group`** marks rows that are exact copies of another row in every published field
  (662 rows in 321 groups, FY2013 to FY2023). All copies are kept and counted in totals; the
  answer says how many matched rows are copies and how much lies beyond the first of each group.
- **A soft hyphen is published as `-`.** 211 cells held an invisible soft hyphen that had lost
  its glyph. It now reads as a hyphen, so Queens house numbers such as `12-11 40th Avenue` keep
  it (earlier builds printed `1211 40th Avenue`).
- **`#N/A` is kept as text.** 37 cells hold the Excel error `#N/A`. They are shown as printed,
  never blanked and never read as a ZIP or a number.
- **`zip` and `zip_status`.** `postal_code` is the cell as printed and is never changed. `zip` is
  a 5-digit ZIP read from it and checked against the Census Bureau's 2020 ZIP Code Tabulation
  Areas (ZCTAs), from the 2020 ZCTA-to-County relationship file (URL, date and sha256 in
  `source/census-zcta/MANIFEST.csv`). `zip_status` says how: `valid` (a ZCTA, in the row's
  state when one is named); `padded` (4 digits that lost a leading zero, padded only into an
  in-state ZCTA); `trimmed` (a ragged ZIP+4 such as `11203-`, `11231=1020` or
  `11413 ZipCode2: 3929`, cut to its first five digits only when they are an in-state ZCTA);
  `repaired_extra_digit` (6 digits where exactly one one-digit deletion is an in-state ZCTA,
  such as `111691` to 11691); `ambiguous_extra_digit` (6 digits where two or more are, such as
  `114345` to 11434 or 11435; no zip, the candidates shown, none picked); `not_a_zcta` (a
  well-formed ZIP with no ZCTA, such as a PO-box ZIP: not verified, not fake); `state_mismatch`
  (a ZCTA in another state than the row's); `invalid` (nothing readable); `blank` (nothing
  printed).

### Added
- **`search_disclosure_awards`** — the NYC Council's expense funding disclosure, FY2013–FY2027:
  the Council's own award-level workbooks (`source/expense-funding-disclosure/`), parsed by
  `code/parse_expense_disclosure.py` into `data/fyNN/expense_disclosure/` — 139,556
  designations, Cleared and Pending, with MOCS ID from FY2024. Filters: `fiscal_year`, `ein`,
  `legal_name`, `council_member`, `source` (funding stream), `agency`, `program_name`,
  `status` (`cleared` / `pending` / `other`; default all), `min_amount`, `max_amount`,
  `limit`. A separate tool, not a new `source_table` on the award tools, because the disclosure
  is a later snapshot than the adopted budget: it includes post-adoption designations and its
  `council_member` is the roster when the workbook was exported.
- Every response states the **true match count** and computes the **totals over every match**
  in SQL, never over the rows shown; a short page says "Showing N of M" (issues #42, #49). Rows
  come highest amount first, ordered before the limit (as in #41). **Cleared** (the headline) and
  **Pending** totals are separate, with an all-statuses line labeled as not a headline figure,
  plus a per-year split for multi-year answers.
- Every response names the **snapshot** of each fiscal year it draws on — file, sheet (which
  carries the Council's own "last updated" date), retrieval date, sha256 prefix — read from
  `source/expense-funding-disclosure/MANIFEST.csv` into a `disclosure_snapshots` table. The
  index build fails if a year's row count disagrees with the manifest, so the index cannot claim
  one snapshot while serving another.
- A one-line caveat and the tool's own source footer on every response (the shared footer
  describes the adopted-budget documents and would misattribute this source).
- Strict schema as for every tool (#40): unknown parameters raise. New per-tool alias hints:
  `organization` → `legal_name`, `program` → `program_name`, `status_norm` → `status`, and
  a disclosure-specific reason for `council_district` / `district`. Hints stay per-tool, so the
  existing tools' messages are unchanged.
- `test/disclosure.test.js` (13 tests). Expected values are computed from the committed CSVs
  and `MANIFEST.csv`, never from the index under test. Mutation-checked: computing totals from
  the page, hiding truncation, stripping unknown parameters, folding Pending into Cleared and
  limiting before ordering each fail at least one test.
- `test/disclosure-audit.test.js` (14 tests): the Schedule C audit questions asked of this tool
  (M1–M12 in `data/DISCLOSURE-AUDIT.md`). Totals are checked against the CSVs summed **exactly**
  (BigInt) for every fiscal year × status, so a one-cent float residue would fail. Mutation-
  checked: OR-ing the fiscal-conduit EIN into the `ein` filter, unescaping LIKE, a
  fiscal-year-first sort, removing the limit, EIN and multi-value guards, and truncating amounts
  in the SQL sum each fail at least one test.

- **Grantee addresses, and filters on them** (2026-10-13). Each `search_disclosure_awards` row
  now shows the grantee's mailing address as printed (`address1`, `address2`, `city`, `state`,
  `postal_code`) with the derived 5-digit `zip` and its `zip_status` (`valid`, `padded`,
  `trimmed`, `repaired_extra_digit`, `ambiguous_extra_digit`, `not_a_zcta`, `state_mismatch`,
  `invalid`, `blank`; rules in DATA-DICTIONARY), plus the candidate ZIPs on an
  `ambiguous_extra_digit` row. New
  filters: `zip` (exactly 5 digits, on the derived zip; a ZIP+4 or 4-digit value is an error
  that names the five digits to use, never trimmed or padded by the tool), `zip_status` (one of
  the nine), and `city` (exact, case- and surrounding-whitespace-insensitive; not a substring,
  so `Brooklyn,` and `Brooklyn NY` as printed are different values). Alias hints:
  `postal_code` and `zip_code` → `zip`. The caveat line now says the address is a mailing
  address, not where services were delivered. The index build stops on a `zip_status` outside
  the nine, a `zip` that does not fit its status, or `zip_candidates` on any status but
  `ambiguous_extra_digit` (or missing from it).
- `test/disclosure.test.js` +6 tests (every row's address, zip, zip_status and zip_candidates indexed exactly as
  the CSV has them; zip / zip_status / city filters; the row's address line). Audit question M13
  in `test/disclosure-audit.test.js` (zip totals exact to the cent; every zip_status count).
  Mutation-checked: filtering `postal_code` instead of `zip`, a substring or case-sensitive
  `city`, dropping the `zip_status` filter or the 5-digit guard, dropping the address line,
  rewriting `postal_code` in the index, blanking trimmed zips, giving an ambiguous row one of
  its candidates as its zip, and dropping the candidates from the row each fail at least one
  test.

### Fixed (found by the disclosure audit before release)
- **`ein` must be 9 digits.** `ein: "N/A"` normalized to `""` and matched the 6 rows with a blank
  EIN; an 8-digit EIN (a leading zero lost in a spreadsheet) silently matched nothing while its
  9-digit form has rows. Both are now an error; the 8-digit case names the zero-padded form to
  try. Nothing is padded or guessed.
- **`limit` below 1 is an error.** `0` and negatives silently returned one row.
- **LIKE wildcards are literal.** `legal_name: "_"` matched all 139,556 rows; `%`, `_` and `\`
  in a text filter are now escaped. (This tool only; the older tools' shared `likeClause` is
  unchanged in this release.)
- **A substring filter that matches several values says so.** `council_member: "Levin"` summed
  Levin and Levine; `source: "Youth"` summed the Youth stream and initiatives such as Summer
  Youth Employment Program. The answer now lists every distinct `council_member`, `source` or
  `agency` value the filter matched, with rows and dollars, when there is more than one.
- **An EIN that pools many names says how many.** `ein: "136400434"` (the City of New York) covers
  hundreds of City bodies; the answer now counts the distinct legal names in the match.
- **Council members are people, not substrings (#72).** New exact filter `council_member_id`
  (a Legistar person ID, digits only; a string or a number) and new `source_exact` (one funding
  stream, case- and surrounding-whitespace-insensitive equality: `Youth` no longer means
  `Summer Youth Employment Program` too). Each row shows the person its printed name resolves to
  for that fiscal year (`Levin [Legistar person 7567]`), or why it does not (ambiguous,
  unresolved, a district label), and flags a name from the export-time roster whose person had no
  recorded vote that year. A substring `council_member` filter lists each name/person pair it
  blended and points to `council_member_id`. IDs come from the repo's committed member crosswalk
  (`data/disclosure_council_member_crosswalk.csv`); the index build stops on a row whose ID and
  type disagree. `council_member` and `source` keep their substring behavior.
- **Exact copies are flagged (#69).** 662 disclosure rows in 321 groups (FY2013–FY2023) are
  identical in every published field but their workbook row. All are kept, as published. Each
  such row is now marked in the answer ("exact copy of workbook row N", or the group's first), and
  every answer with flagged rows says how many of its matched rows are copies and how many rows
  and dollars lie beyond the first copy of each group. The tool description no longer says "one
  row per designation".
- **Excel error values stay text (#71).** 37 disclosure cells hold `#N/A` (ZIPs, addresses,
  cities); their 25 rows are indexed and served like any other. The index build now stops if an
  EIN column ever holds an Excel error value, which `normEin` would otherwise have turned into a
  silent blank.

### Changed
- `npm pack`: **9.3 MB → 14.9 MB** packed, 36.1 MB → 67.6 MB unpacked (`data/budget.db`).
  `purpose` (26 MB of the CSVs' 52 MB) and `source_file` are **not indexed**; each row gives its
  workbook row number in the repo CSV instead. Grantee addresses were left out at first (15.7 MB
  packed, 61.2 MB unpacked); adding them cost 1.4 MB packed (17.1 MB), and the index build now
  ends with `VACUUM`, which removes the free and part-filled pages that row-by-row inserts
  leave, for 14.9 MB packed with the addresses. Same rows, same answers.
- `package-lock.json` synced to 1.5.0 (it was missed on 1.3.0 and 1.3.1).



The award tools now return the Schedule C **appendix** designations — 28,575 rows that were
parsed, committed, and reaching no consumer. Minor rather than patch: award counts and dollar
totals returned by `search_awards` and `get_awards_by_ein` **increase** for FY2018 and
FY2021–FY2027, so figures published from v1.3.x and earlier will not reproduce against this
version unless the new `source_table` filter is used. No parameter was renamed or removed, and no
main-body row changed.

### Fixed
- **1,271 award rows had lost their grantee name.** Extraction put purpose prose where the
  organization belonged (1,060 rows), or absorbed a neighbouring award's text into the field
  (211 rows), so a query returned a sentence — or another organization's name — where a grantee
  should be. `get_awards_by_ein("13-4051235")` showed *"For a Community Education Summit to focus
  on the opioid crisis…"* instead of **Film Fleadh Foundation, Inc.**

  Names were restored deterministically from the Council's own published expense disclosure files
  (`source/expense-funding-disclosure/`, FY2013–FY2027), joined on **(EIN, amount)**. EIN alone is
  not a usable key: fiscal sponsors pass funds through for many grantees, and EIN 13-2612524 (Fund
  for the City of New York) carries 229 distinct names in this corpus — joining on it would have
  stamped the sponsor's name onto awards that went elsewhere. `(EIN, amount)` identifies the
  individual award and resolves uniquely for 96% of affected rows.

  Nothing was inferred and no model read a value. Every substitution is recorded in
  `data/combined/org_name_recovery_crosswalk.csv` with the original text, the replacement, the EIN
  and the amount, so each edit is auditable and reversible. **473 rows the method could not resolve
  to a single candidate were left untouched** and remain flagged by `code/validate_data.py` rather
  than filled in with a guess.

- **28,575 appendix rows were invisible to every tool.** `scripts/build-index.mjs` read exactly
  one file per fiscal year, `{fy}_schedule_c_awards.csv`, and nothing else — `grep -c appendix
  scripts/build-index.mjs` returned 0. The three per-year appendix CSVs (Appendix A aging,
  B local, C youth) were parsed, QA'd, committed, and documented in the repo README, and no query
  path could see them.

  The canonical case is **Bard College, EIN 14-1713034**. Three FY2023 designations — Abreu
  $5,000, Brooks-Powers $10,000, Powers $5,000, $20,000 across three members — sat in
  `data/fy23/schedule_c/fy23_appendix_b_local.csv` while `get_awards_by_ein("14-1713034",
  fiscal_year: 2023)` returned *No Schedule C awards for EIN 14-1713034*. Not an incomplete
  answer: a confident, well-formatted, footnoted zero for an organization the Council had in fact
  funded. FY2024–FY2027 were the quieter version of the same bug — main-body rows present,
  appendix designations missing, so the answer looked right and was short.

  The rows are real, and this was checked against a source outside this repo before any of them
  was loaded. The Council's own published disclosure spreadsheet
  (`source/expense-funding-disclosure/funded_disclosure_FY2023.xlsx`) carries all three Bard
  designations with `Source` = "Local", matching member, amount, and purpose text. At the
  aggregate level FY2027 agrees exactly: the disclosure's `Source` counts are Aging 467, Local
  2558, Youth 835, which are the FY2027 appendix files' row counts, file for file.

### Added
- **`source_table` on every award row**, `'schedule_c'` (main-body award tables) or `'appendix'`.
  Both are returned by default. `search_awards` and `get_awards_by_ein` accept it as an optional
  filter; **`source_table: "schedule_c"` reproduces the pre-1.4.0 result set exactly**, which is
  the intended escape hatch for reconciling against an already-published number, and the intended
  cheap reversal if returning both by default proves to be the wrong call.
- **`appendix_stream`** — `aging` / `local` / `youth`, read off the source filename. It is the
  only thing distinguishing the three appendix files once they are merged into one table, so
  dropping it would have destroyed information that exists on disk.
- Appendix rows are **tagged in tool output** (`· [appendix: local]`), and any result set mixing
  the two sources prints a `By source:` split naming both totals and the `source_table` escape
  hatch. A caller reconciling against a v1.3.x figure has to be able to see why the number moved;
  silently returning a larger total is how a reconciliation becomes a phantom discrepancy.
- `list_available_fiscal_years` reports appendix coverage as an explicit **subset** of the award
  years (FY2018 + FY2021–FY2027 — no new fiscal year is introduced) and states the totals change.
- `test/appendix-ingest.test.js` pins the Bard FY2023 case in both directions: the three
  designations are now returned, **and** `source_table: "schedule_c"` still returns nothing for
  FY2023 — which is what proves these are new rows rather than a main-body figure that shifted.
  `test/coverage.test.js` keeps its per-year main-body counts and totals unchanged (now scoped to
  `source_table = 'schedule_c'`) and adds a parallel per-year appendix table.

### Known limits — stated, not papered over
- **Four fields do not exist in the appendix CSVs and are stored EMPTY, not inferred:**
  `category`, `initiative`, `award_type` (absent from all three files) and `agency` (absent from
  aging and youth; present in local). Reading A/B/C as the missing `initiative`, or filling agency
  with DFTA-for-aging and DYCD-for-youth, is plausible and unverified — and demonstrably not a
  constant per stream, since Bard's FY2023 *local* rows record `MOCJ`. Consequence for callers:
  filtering `search_awards` on `category` or `initiative` excludes appendix rows entirely, because
  they have no such value to match.
- **FY2015–FY2017 and FY2019–FY2020 appendix CSVs are header-only upstream**, so those years gain
  nothing here. FY2018 has an aging appendix only. That is a parser gap in `data/`, out of scope
  for this release; the loader indexes what exists and invents nothing.
- **The repo README describes these files as "subsets of the main body ... do not add them to the
  Schedule C total."** That warning is correct about the printed *category* totals and does not
  hold for the awards table: matching FY2015–FY2027 appendix rows against their own year's awards
  CSV on (member, EIN, amount) leaves **27,874 of 28,575 unmatched**, and against the Council
  disclosure only 14 rows across FY2023 + FY2027 exceed the disclosure's own multiplicity. The
  overlap is real but marginal; treating it as a full duplicate set would have kept the Bard rows
  invisible. Reconciling that README sentence with this finding is Phase 1 work, not this release.

## 1.3.1 — 2026-07-22

`search_awards` now applies limits after ordering each fiscal year's matches by award amount,
so organization-filtered searches no longer hide the largest awards behind sponsor-name order.
Patch release: no tool arguments, schemas, or data coverage changed.

### Fixed
- **Filtered award limits could return a lower-value sponsor-ordered slice (issue #39).**
  `search_awards(organization="Association of Community Employment", fiscal_year=2026, limit=4)`
  returned `$67,000`, `$15,000`, `$40,000`, and `$250,000`, omitting awards of `$280,000`,
  `$280,000`, and `$260,000`. Award searches now order by fiscal year, amount descending,
  then sponsor before applying the limit.
- `test/award-ordering.test.js` pins the real FY2026 reproduction and verifies the limited
  result equals the four highest-value rows from the full filtered set.

## 1.3.0 — 2026-07-21

Unknown tool parameters are now rejected instead of silently dropped (issue #37). Minor rather
than patch: tool-call behavior visibly changes for callers who were passing undeclared
parameters, and `TOOLS` becomes a public export. No declared parameter was renamed or removed.

### Fixed
- **Unknown tool parameters were silently dropped instead of rejected (issue #37).** Every tool
  accepted parameters that were not in its schema, stripped them (zod's default), and returned
  UNFILTERED results with no error and no warning. `search_awards(council_district=10,
  fiscal_year=2026, limit=15)` returned $47,500,647 of **citywide** awards — real, correctly
  formatted, correctly sourced data answering a different question. There is no district filter
  because Schedule C keys on the sponsoring member's surname (`council_member`), so that guess is
  the natural one and its failure was invisible to the caller.

  Two layers now close it: every tool's advertised `inputSchema` sets `additionalProperties: false`
  (so a calling model knows the parameter is invalid before it calls), and every handler parses
  arguments through a `.strict()` zod schema (so anything slipping through raises). The error names
  the unknown key *and* that tool's accepted parameters, with per-tool alias hints for the guesses
  actually seen in the wild — `council_district`/`district` point at `council_member` or `sponsor`,
  `query` points at `organization`/`program`. Hints are filtered against each tool's own schema, so
  `search_capital_projects` is never told about `council_member` and `search_awards` is never told
  about `sponsor`.

  No parameter was renamed or removed, and valid calls are unaffected.

### Added
- `TOOLS` is now exported from `src/server.ts`, and `test/strict-schema.test.js` loops over it to
  assert `additionalProperties: false` on every tool — a check that covers tools added later.

## 1.2.0 — 2026-07-16

`get_legistar_link` now returns a **working** Legistar link. It points at the City Council
**meeting where the matter was adopted**, replacing the previously-emitted `LegislationDetail.aspx`
bill link that resolved to "Invalid parameters!". New feature (adopting-session output + four new
crosswalk columns), so a minor bump. See issue #31.

### Fixed
- **The bill-detail link was broken for every crosswalk row.** NYC runs two independent Legistar
  backends with different ids: the OData WebAPI exposes `MatterId`/`MatterGuid`, but the public
  `LegislationDetail.aspx` page keys on a *separate* ID/GUID that appears nowhere in the OData
  record, so `LegislationDetail.aspx?ID={MatterId}&GUID={MatterGuid}` returns "Invalid parameters!"
  — there is no formula between the two. The stored `legistar_url` column (that broken scheme) is
  **no longer surfaced** as a citation.
- **Stale "PROTOTYPE — local snapshot, not a published package" footer.** The disclaimer appended
  to every tool response predated the npm release and contradicted reality (published since
  v1.0.0). It now identifies the package and self-reports its version.

### Added
- **Adopting-session link (works).** The public *meeting* URL scheme accepts the OData `EventId`:
  `https://legistar.council.nyc.gov/MeetingDetail.aspx?LEGID={EventId}&GID=61` (`GID=61` is a
  verified term-stable constant, resolves meetings 2007–2026). `get_legistar_link` builds this at
  query time for confirmed rows and surfaces the adopting body, action, and datetime. A row with no
  confirmed City Council adoption event gets **no link** (never a wrong one); its matter number +
  adoption date remain the citation.
- **Four crosswalk columns** — `adopting_event_id`, `adopting_body`, `adopting_action`,
  `adopting_datetime` — precomputed per confirmed row.

### Data / tooling
- **`scripts/enrich-crosswalk.mjs`** (new) resolves each confirmed crosswalk row's adopting `EventId`
  from Legistar OData (matter file → `MatterId` → histories → the `Approved, by Council` / City
  Council / passed history row's `MatterHistoryEventId`). Idempotent and resumable (skips
  already-enriched rows; rewrites the CSV after each row), throttled ~1 req/sec with 429 backoff.
  Endpoints/fields reuse the production `nyc-council-mcp` Legistar client.
- **Enrichment coverage (2026-07-16):** 231 of 232 confirmed rows enriched. The one exception,
  Res 0849-2025 (FY2025 transparency_reso_11), has no full-Council adoption in its Legistar history
  (introduced → referred to Committee on Finance → P-C item approved by committee only) → null link,
  correctly. `candidate` (10) and `not_located` (13) rows are not enriched by design.
- `build-index.mjs` loads the four new columns into the `crosswalk` table.

## 1.1.0 — 2026-07-15

FY2025 §254 capital is now reconciled and directly comparable to the other years. No tool,
argument, or table-schema changes — this is a data-coverage/quality improvement plus the
user-facing description corrections it requires. Minor bump (mirrors the 0.2.0 coverage-expansion
precedent), not a patch.

### Changed
- **FY2025 capital reparsed to the Supporting Detail Book.** Upstream PRs #20/#21 replaced the old
  non-reconcilable FY2025 "Appropriation Changes" data with the FY2025 "Supporting Detail Book"
  (Council-additions Capital Project Detail), parsed into the **same 13-column schema as
  FY2026/FY2027** (`part, agency, budget_line, sub_id, boro, fy1..fy4, sponsor, title,
  building_code, school_code`) and reconciled exactly: 30/30 agency subtotals; Part I
  $775,000,000 / 1327 projects; Part II non-city $158,992,000 / 181. `search_capital_projects`
  with `fiscal_year: 2025` now returns rows with `boro` and `sponsor` populated, directly
  comparable to the other years.
- **Description corrections.** `search_capital_projects` and `list_available_fiscal_years` no
  longer describe FY2025 capital as the non-reconcilable "Appropriation Changes" type / different
  schema. The README data-scope table and the `build-index.mjs` capital comment were updated to
  match.

### Loader
- No loader change was required: `build-index.mjs` already loads capital by the explicit per-year
  filename `${key}_capital_projects.csv`, so FY2025 picks up the new canonical reconciled file and
  **not** the renamed provenance file (`fy25_capital_changes_appropriation.csv`) or the Part III
  sidecar (`fy25_capital_noncity_by_entity.csv`). Verified by the new regression test. The legacy
  `action` column is retained in the schema for back-compat but is empty for every loaded row.

### Tests
- `test/coverage.test.js`: added an FY2025-capital regression test asserting the new schema is
  what's served — 1508 rows (Part I 1327 + Part II 181), `boro` populated on every row, `sponsor`
  populated on all Part I rows, and that `search_capital_projects(fiscal_year: 2025)` returns rows
  carrying `boro:` and `sponsor:`. This would fail if the loader ever indexed the old
  appropriation file (empty boro/sponsor) instead of the canonical detail.

## 1.0.1 — 2026-07-08

Bug fix. No tool, schema, or data-coverage changes — a stale organization name in
user-facing description text only.

### Fixed
- `search_awards` tool description (and the matching README caveat) referred to EIN
  13-2612524 as **"Delegation Fund for the City of New York, Inc."** — a name that no
  longer exists in the data. The "Delegation" prefix was a Transparency-Resolution
  header-bleed parsing artifact corrected in the data by PR #10; the description string
  was left stale (flagged but deliberately out-of-scope in PR #11's test-only fix). The
  correct organization name for that EIN is **"Fund for the City of New York, Inc."**,
  verified against the built index (EIN 132612524: 205 award rows across 78 distinct
  programs — the fiscal-sponsor caveat the description illustrates still holds).

## 1.0.0 — 2026-07-08

First public release. Published to npm as `@betanyc/nyc-budget-mcp`; consumable via
`npx -y @betanyc/nyc-budget-mcp`. No tool or data-coverage changes from 0.2.0 — this
release retires the local-only prototype framing and ships the package to the registry.

### Changed
- Package renamed `nyc-budget-mcp` → **`@betanyc/nyc-budget-mcp`** (scoped, public) and
  un-marked `private` for npm publication.
- Prototype framing removed from the package description and README now that the server ships.
- `files` allowlist now ships the prebuilt SQLite index (`data/budget.db`) inside the npm
  tarball. The index is a build artifact (git-ignored) generated by `prepare`/`pretest` at
  pack time from the repo's `../data/` CSVs; shipping it is required because registry installs
  do not run `prepare` and the tarball has no access to `../data/`. Mirrors the local-corpus
  packaging model of `@betanyc/nyc-charter-laws-rules`.
- Added `repository` (with `directory: "mcp"` for this monorepo subdirectory package),
  `homepage`, and `bugs` metadata; `repository.url` is required for npm provenance publishing.

### Release
- Tag-triggered publish via `.github/workflows/release.yml` at the repo root, scoped to the
  `mcp/` subdirectory. Release tags are **`mcp-v*`** (e.g. `mcp-v1.0.0`), not the bare `v*`
  used by the single-package fleet repos, because this MCP is one component of a larger
  monorepo (budget data pipeline + docs) — a repo-global `v*` tag would misrepresent an
  MCP-only release.

## 0.2.0 — 2026-07-08

Coverage expansion to every EIN-bearing / parsed year (gated on the FY08–24 data QA pass).

- **Schedule C awards: FY2025–FY2027 → FY2015–FY2027.** FY2015 is the earliest EIN-level year;
  FY2009–FY2014 are initiatives-only (no EIN) and are deliberately **excluded** from the award tools.
- **Terms & Conditions:** widened to FY2015–FY2018 + FY2021–FY2027 (no FY2019/FY2020 document).
- **Capital (§254):** widened to FY2020 + FY2022–FY2027 (no FY2021 detail book).
- **Transparency Resolutions:** FY2026 → FY2010–FY2024 + FY2026. Added a `source_fy` (resolution
  document year) axis — `search_transparency_resolutions.fiscal_year` now filters it. FY2010–FY2013
  rows are flagged `low_text_confidence` and the org/program-text caveat is surfaced in results and
  the tool description (financial columns reliable; join on EIN).
- **`list_available_fiscal_years`** rewritten to report exact per-dataset coverage plus the honesty
  guard (award tools = FY2015–FY2027; FY2009–FY2014 initiatives-only excluded; unparsed years named).
- **build-index** driven by per-dataset year lists; idempotent rebuild now also clears the WAL/SHM
  sidecars (fixes SQLITE_IOERR_SHORT_READ on re-run over network volumes).
- **`test/coverage.test.js`** added: a real per-fiscal-year gate for every award year FY2015–FY2027
  (queryable + exact count/total + 100% valid 9-digit EIN) plus honesty-boundary and coverage
  assertions. Full suite now 27 tests, all passing.

## 0.1.0 — 2026-07-07

Initial prototype (local-only; not published to npm, not pushed to GitHub).

- SQLite-backed MCP server wrapping BetaNYC's New-York-City-Budget data.
- 7 tools: `search_awards`, `get_awards_by_ein`, `search_transparency_resolutions`,
  `get_legistar_link`, `search_capital_projects`, `get_terms_conditions`,
  `list_available_fiscal_years`.
- `scripts/build-index.mjs` builds `data/budget.db` from a committed CSV snapshot
  (awards/terms/capital FY2025–FY2027, FY2026 transparency resolutions,
  FY2008–FY2027 Legistar crosswalk).
- `test/journeys.test.js` re-runs all 8 validated user journeys through the MCP
  protocol (10 tests, all passing).
