# Changelog

All notable changes to `@betanyc/nyc-budget-mcp` are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

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
