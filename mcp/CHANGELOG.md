# Changelog

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
