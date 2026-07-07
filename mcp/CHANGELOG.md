# Changelog

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
