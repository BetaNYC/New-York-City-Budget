# `mcp/retired-1.x/` — parked 1.x tests and script (not run, not shipped)

Removed from the active package in 2.0.0, when every PDF-derived dataset and the tools built on
it were retired (see `../CHANGELOG.md`). Parked here rather than deleted, pending a maintainer's
decision to delete them; git history keeps them either way.

- `test/*.test.js`, `test/fixtures/` — the 1.x tests for `search_awards`, `get_awards_by_ein`,
  `search_transparency_resolutions`, `search_capital_projects`, `get_terms_conditions` and
  `get_legistar_link`. They import functions 2.0 no longer has and **will not run**.
  `npm test` runs `test/*.test.js` only, so they are never picked up.
- `scripts/enrich-crosswalk.mjs` — added the adopting-meeting fields to
  `data/combined/legistar_crosswalk.csv` for the retired `get_legistar_link`.

`package.json` `files` lists only `dist` and `data/budget.db`, so nothing here reaches npm;
`test/no-pdf-data.test.js` checks the tarball's file list.
