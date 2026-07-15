# @betanyc/nyc-budget-mcp — NYC Budget MCP server

A Model Context Protocol (MCP) server that wraps this repository's data — NYC Council discretionary funding (Schedule C), Terms & Conditions, Section 254 capital changes, the Transparency Resolutions, and the FY2008–FY2027 Legistar crosswalk — and exposes it to MCP-capable AI clients as structured query tools.

Published on npm as [`@betanyc/nyc-budget-mcp`](https://www.npmjs.com/package/@betanyc/nyc-budget-mcp) and run via `npx` (see [Quick start](#quick-start-npx)). The published package ships a prebuilt SQLite index, so no local clone, build, or data checkout is needed to run it.

At build time it reads the parent repo's own `../data/` tree directly — there is no copied CSV snapshot to keep in sync. Data and query layer live in one repo and move together.

## Quick start (npx)

Add this to your MCP client config (Claude Desktop, Claude Code, etc.):

```json
"mcpServers": {
  "nyc-budget": {
    "command": "npx",
    "args": ["-y", "@betanyc/nyc-budget-mcp"]
  }
}
```

Restart the client — the 7 `nyc-budget` tools become available. `npx -y` resolves the
package from npm per machine (no clone, build, or absolute path required — the BetaNYC-fleet
portability convention), and the prebuilt budget index ships inside the package, so the
server has its data on first run.

## Data scope (read this first)

| Dataset | Coverage | Notes |
|---|---|---|
| Schedule C awards | **FY2015–FY2027** | FY2015 is the earliest EIN-level year. FY2009–FY2014 are initiatives-only (no EIN) and are **excluded** from the award tools; FY2008 is unparsed |
| Terms & Conditions | **FY2015–FY2018 + FY2021–FY2027** | No standalone T&C document exists for FY2019/FY2020 |
| Capital (§254) | **FY2020 + FY2022–FY2027** | No FY2021 detail book. Every parsed year is the "Supporting Detail Book" (Council-additions Capital Project Detail), shares the full schema (borough/sub-id/sponsor), and reconciles against printed subtotals + grand totals (FY2027 partially). FY2025 was reparsed from its Supporting Detail Book in [PR #21](https://github.com/BetaNYC/New-York-City-Budget/pull/21) and is now directly comparable to the other years |
| Transparency Resolutions | **FY2010–FY2024 + FY2026** | Filtered by resolution document year (`source_fy`). **FY2010–FY2013 org/program TEXT is low-confidence** — financial columns reliable, join on EIN. FY2009 + FY2025/FY2027 not parsed |
| Legistar crosswalk | **FY2008–FY2027** | Provenance index; covers years not parsed to CSV |

The tools do **not** pretend data exists where it doesn't: FY2009–FY2014 award data (there is none — initiatives-only) and the unparsed years are reported honestly by `list_available_fiscal_years`, which states exact per-dataset coverage and the FY2009–FY2014 no-EIN boundary.

## Tools

| Tool | Purpose |
|---|---|
| `search_awards` | Schedule C awards by EIN / organization / program / council member / fiscal year / category / initiative |
| `get_awards_by_ein` | Every award for an EIN across FY2015–FY2027, with per-year totals |
| `search_transparency_resolutions` | FY2010–FY2024 + FY2026 post-adoption designations / rescissions / purpose changes (FY2010–FY2013 text low-confidence) |
| `get_legistar_link` | Legistar matter/URL/adoption date for a source document (surfaces `status`) |
| `search_capital_projects` | §254 capital by agency / fiscal year / sponsor / title |
| `get_terms_conditions` | Reporting mandates by fiscal year / agency |
| `list_available_fiscal_years` | What each dataset actually covers (the parse-gap guard) |

### The fiscal-sponsor caveat (important for correct EIN use)

EIN is the only reliable cross-system join key, **but a single EIN can be a fiscal sponsor** covering dozens of programs. EIN `13-2612524` ("Fund for the City of New York, Inc.") is a passthrough — to isolate one grantee (e.g. BetaNYC) filter by `program` as well as `ein`. `get_awards_by_ein` honestly returns the whole pool; `search_awards(ein, program)` narrows it. (A maintained fiscal-sponsor alias table is future work — see the user-journeys doc.)

## Architecture

Modeled on [`@betanyc/nyc-charter-laws-rules`](https://github.com/BetaNYC/nyc-charter-laws-rules) — a local/offline corpus with no live upstream API. TypeScript + the MCP SDK + zod, served over stdio.

- **`../data/`** — the parent repo's real CSVs (the single source of truth). This server reads them directly; there is no vendored snapshot inside `mcp/`.
- **`scripts/build-index.mjs`** — reads those CSVs and builds a local **SQLite** index (`mcp/data/budget.db`, git-ignored) via `better-sqlite3`. Idempotent: the `.db` is dropped and rebuilt each run. SQLite (not DuckDB) was chosen to match `nyc-council-mcp`'s established BetaNYC pattern and its synchronous query style.
- **`src/db.ts`** — opens the `.db` read-only and exposes one query function per tool.
- **`src/server.ts` / `src/index.ts`** — MCP tool definitions, zod-validated routing, stdio transport.

CSV parsing uses `csv-parse` because organization names contain quoted commas (`"El Puente de Williamsburg, Inc."`) that a naive split corrupts.

## Build & run

From inside `mcp/`:

```bash
npm install          # runs prepare → build + build-index
npm start            # launch the MCP server over stdio
npm run build-index  # rebuild mcp/data/budget.db from ../data/
npm test             # build + build-index + run the journey tests
```

`mcp/data/budget.db` is a build artifact (git-ignored); `npm install` regenerates it from `../data/`. It is **not** committed to git — the npm `files` allowlist ships it into the published tarball, freshly built by `prepare` at publish time (see [Releases](#releases)).

## Run from source (development)

To run a local, in-development build instead of the published package — e.g. after editing `src/` or the underlying `../data/` CSVs — point your client at the built entry with an **absolute path**:

1. Build + index once: `npm install` (or `npm run build && npm run build-index`) inside `mcp/`.
2. Add a project-scoped entry to `~/.claude.json` (Claude Desktop: its equivalent config):
   ```json
   "mcpServers": {
     "nyc-budget": {
       "command": "node",
       "args": ["/ABSOLUTE/PATH/TO/New-York-City-Budget/mcp/dist/index.js"]
     }
   }
   ```
   The server resolves `budget.db` from its own `__dirname`, so it works regardless of the launch cwd — no `cwd` key needed.
3. **Restart the client.** MCP servers load at startup; a running session will not hot-load a newly-added server.

**After any data or code change, re-run `npm run build && npm run build-index`** — the server serves the built `dist/` + `budget.db`, not the TypeScript source or the CSVs directly. For everyday use prefer the [npx quick start](#quick-start-npx) above.

## Tests

`test/journeys.test.js` re-runs all 8 user journeys from `people/noel/work/2026-07-07-mcp-budget-user-journeys.md` (in the BetaNYC workspace) against the real MCP tools, driven in-process through the MCP protocol via `InMemoryTransport`, asserting the same real answers found by hand: BetaNYC EIN `13-2612524` (FY25 $115k / FY26 $115k / FY27 $95k), Council District 33 / Restler capital ($18,750,000 across 12 FY2026 projects), and the FY2026 Transparency Resolution 1 Noel Pointer → El Puente CASA transfer. Journey 8 asserts the MCP honestly reports its coverage and the FY2009–FY2014 no-EIN boundary.

`test/coverage.test.js` is the per-fiscal-year gate: for **every award year FY2015–FY2027** it asserts the year is queryable through the tools, its award count and dollar total match the QA-cleared committed data exactly, and every award row carries a valid 9-digit EIN. It also asserts the honesty boundary (FY2009–FY2014 have no award rows), the exact per-dataset year coverage, and that the FY2010–FY2013 transparency low-confidence caveat is flagged and surfaced. Full suite: **27 tests, all passing** (13 per-year award checks + 4 coverage/honesty checks + 10 journeys).

## Releases

This package is published to npm by CI, never from a laptop. The release pipeline mirrors
the BetaNYC MCP fleet, adapted for this monorepo (the package lives in `mcp/`, not the repo root):

- **Version bump lands in a PR** — a semver bump in `mcp/package.json` (fix = patch, feature =
  minor, breaking = major) plus a `CHANGELOG.md` entry, reviewed and merged to `main`.
- **Publishing is tag-triggered.** `.github/workflows/release.yml` (repo root) fires on a pushed
  **`mcp-v*`** tag whose version matches `mcp/package.json`. It installs, tests, and runs
  `npm publish --provenance --access public` from `mcp/`, then cuts a GitHub Release. The
  `mcp-v` prefix (not the fleet's bare `v*`) scopes releases to this MCP so a tag can't be
  confused with a release of the repo's budget-data pipeline.
- **To release** after the version-bump PR merges:
  ```bash
  git tag mcp-v<version>          # e.g. mcp-v1.0.0 — must match mcp/package.json
  git push origin mcp-v<version>
  ```
  Watch the Release workflow in the Actions tab; it publishes on green.
- **CI** — `.github/workflows/ci.yml` builds and tests `mcp/` on a Node 20/22 matrix for every
  PR that touches the `mcp/` tree.

## About BetaNYC

This project is built and maintained by [BetaNYC](https://beta.nyc), New York's
civic technology and open-data community. We work to improve lives in New York
through civic design, technology, data, and public-interest technology.

**Come do civic tech with us.** We run public events, meetups, and hands-on
data classes throughout the year — including [NYC School of Data](https://www.schoolofdata.nyc/)
and [CityCamp NYC](https://citycamp.nyc), and we host frequent civic-tech gatherings. See what's coming up on our
[events calendar](https://www.beta.nyc/events/).

**Sustain this work.** These MCP servers are free and open source. To help keep this work going and find BetaNYC's
tools, please consider [donating and becoming a Beta
Builder](https://beta.nyc/donate).

## Building on this? Tell us!

If you build something with this project, we'd love to hear about it. We can help other New Yorkers find it. BetaNYC publishes a weekly newsletter,
*This Week in NYC's Civic Technology and Open Data*.

- **[Subscribe to the newsletter](https://beta.nyc/newsletter)** to keep up with
  NYC civic tech, open data, and public-interest technology.
- **Built something, or found a story worth sharing?** [Submit a link for the
  newsletter](https://www.beta.nyc/newsletter-inbox/) and we'll consider it for
  an upcoming issue.

## Related BetaNYC MCP servers

BetaNYC maintains a suite of open-source MCP servers for NYC and NYS civic data.
See the full directory, with install details for each, at
**[beta.nyc/ai-tools](https://beta.nyc/ai-tools)**.

This server pairs directly with:

- **[nyc-checkbook-mcp](https://github.com/BetaNYC/nyc-checkbook-mcp)**: follow a Council discretionary award from the budget's Schedule C through to the agency's actual contracts, payments, and spending in Checkbook.
- **[nyc-council-mcp](https://github.com/BetaNYC/nyc-council-mcp)**: connect Transparency Resolutions and the Legistar crosswalk back to the underlying Council legislation, sponsors, and votes.

> **Working with the wider NYC Open Data portal?** NYC Open Data hosts a related
> (now-frozen) Council Discretionary Funding dataset this repo supersedes. To search
> the full catalog or run ad-hoc SoQL queries across other datasets, pair it with
> [socrata-mcp-server](https://github.com/npstorey/socrata-mcp-server)
> (`socrata-mcp-server` on npm), a third-party MCP by [Nathan Storey](https://github.com/npstorey).

## Provenance & licensing

This server reads the repo's own derived data. Provenance, reconciliation status, and licensing are covered by the [repository README](../README.md) and [`LICENSE`](../LICENSE): derived data and code are MIT; the underlying budget documents are © The City of New York.
