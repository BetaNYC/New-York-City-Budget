# Scoping: FY2009–FY2021 Open Data legacy import

**Report generated:** 2026-07-07
**Status:** Lodged for later — not scheduled, not started. Deliberately separate from
the [FY22–FY24 gap scoping](2026-07-07-fy22-fy24-gap-scoping.md), which is the active
task. Do not start this until told to.

## What this is

NYC Open Data hosts ["City Council Discretionary Funding"](https://data.cityofnewyork.us/dataset/4d7f-74pe)
(dataset `4d7f-74pe`) — 97,002 rows covering **FY2009–FY2021**, one row per award. It
stopped being updated in April 2021 (its own `Fiscal Year` column caps out at 2021).
This is a pre-existing, ready-made historical archive — no PDF extraction required —
that could become a `data/legacy/` (or similar) tier in this repo, if brought in.

## Standing clearance

When this task is picked up: **cleared in advance** to use `nyc-council-mcp` and to
check `nyc-checkbook-mcp` for anything related, as live sources. This clearance was
granted 2026-07-07 alongside the FY22–24 gap task; it does not expire, but do not
treat it as a green light to start the import itself without a fresh go-ahead.

## Known findings (carried over from initial exploration, 2026-07-07)

- Dataset `4d7f-74pe`, "City Council Discretionary Funding," created 2018-01-11,
  last data update 2021-04-20. `Status` field (`Cleared` / `Pending` / `Government` /
  `Revoked`) suggests this was a live application-tracking table originally, not a
  purpose-built final archive — worth confirming completeness/accuracy before treating
  it as authoritative the way this repo's PDF-reconciled data is.
- A second dataset, ["Discretionary Award Tracker"](https://data.cityofnewyork.us/dataset/ujre-m2tj)
  (`ujre-m2tj`), is a one-time 2021 snapshot of contract-clearance status — not
  designations. Likely not useful for this import; noted for completeness.
- No dataset was found on the portal that continues past FY2021 or fills FY2022–2024 —
  confirmed via catalog search; that gap is what the sibling FY22–24 task addresses.

### Schema mapping (repo `schedule_c_awards.csv` ↔ Open Data `4d7f-74pe`)

| Repo column | Open Data column | Note |
|---|---|---|
| `member` | `Council Member` | last-name format already matches |
| `organization` | `Legal Name of Organization` | direct |
| `ein` | `EIN` | direct |
| `amount` | `Amount ($)` | direct |
| `agency` | `Agency` | direct |
| `program` | `Program Name` | direct |
| `purpose` | `Purpose of Funds` | direct |
| `initiative` | `Source` | ~690 distinct values, roughly 1:1 |
| `category` | _(missing)_ | Open Data has no two-tier grouping; would need a lookup table built from `Source` values |
| `award_type` | _(missing)_ | `member_item` vs `initiative_provider` isn't explicit; `Fiscal Conduit Name` / `FC EIN` give a partial signal, not a clean derivation |

Open Data also carries geocoding (address, lat/long, BBL, BIN, census tract, Council
District, NTA) that the current repo schema doesn't have at all — a possible schema
extension, or something to drop for cross-year consistency. Open question below.

## Open questions (for whenever this is picked up)

1. How should `category` be reconstructed from the ~690 `Source` values — hand-built
   lookup table, or is a coarser grouping acceptable?
2. Is there a reliable way to derive `award_type` (`member_item` vs
   `initiative_provider`), or does this field simply go unpopulated for legacy years?
3. Should the geocoding fields (address, lat/long, BBL, council district, NTA, etc.)
   be preserved as a schema extension for the legacy tier, or dropped to keep the
   schema consistent across all years?
4. Given this dataset was possibly a live application tracker rather than a final
   archive, should `Status != Cleared` rows be excluded, or kept with the status flag
   preserved?
5. Where does this data live in the repo — a new `data/legacy/` tier, or folded into
   `data/{year}/schedule_c/` per fiscal year alongside the PDF-derived years, with a
   `source: opendata` provenance marker distinguishing it from PDF-reconciled rows?

## Not in scope here

- The FY2022–FY2024 gap — see the sibling scoping doc; kept deliberately separate.
- Parsing/extraction code — once scoped, this routes to `software-engineer` like any
  other extraction work in this repo.

## Addendum: Legistar historical depth (checked 2026-07-07)

**Data current as of:** 2026-07-07. Bounded research note, not an import — written for
whoever picks up this task later. Checked as a side effect of the FY22 gap-fill task
(finding FY2022's missing Resolution-A capital document required browsing Legistar
directly), so the question "how far back does Legistar itself go, independent of
council.nyc.gov's own archive pages and independent of the Open Data FY2009–2021
dataset above" got a cheap answer along the way.

**Method:** `legistar.council.nyc.gov/Legislation.aspx`'s own search UI (not the
`nyc-council-mcp` local index — see caveat below), full-text search restricted to
"All Years," probing for the Schedule-C-equivalent legislative pattern: Committee-on-
Finance resolutions titled "Resolution approving the... designation of certain
organizations to receive funding in the Fiscal `NNNN` Expense Budget."

**Findings — 3 data points:**

1. **Legistar's own year-filter dropdown lists individual years back to 1994** (and
   "Session 1998 to 2001," "Session 2010 to 2013," etc. groupings before that) — this
   is the outer bound of what the system exposes at all, for any matter type.
2. **General capital-budget-resolution matters ("Executive Capital Budget for FY'`NN`")
   are confirmed present back to 1998** (`Res 0327-1998`, "Budget, Capital," introduced
   1998-06-05) via a live full-text search on `nyc-council-mcp`'s
   `search_legislation_live` tool for the phrase "CAPITAL PROGRAM FOR THE ENSUING THREE
   YEARS" — one unbroken run of one-per-year matches, 1998 through 2026 (used directly
   to find FY2022's document; see the sibling FY22–24 scoping doc).
3. **Schedule-C-equivalent "designation of organizations to receive funding" resolutions
   are confirmed back to the FY2008 budget cycle**, filed contemporaneously in 2007:
   `Res 1090-2007`, "Resolution approving the designation of certain organizations to
   receive funding in the Fiscal 2008 Expense Budget" (Committee on Finance, adopted).
   Earlier retroactive/omnibus resolutions (e.g. `Res 0058-2010`, filed 2010, covering
   "Fiscal 2007, Fiscal 2008, Fiscal 2009 and Fiscal 2010 Expense Budgets" in one
   catch-up resolution) reference Fiscal 2007 designations too, but no *standalone*
   Fiscal 2007-cycle designation resolution surfaced in this pass. A probe for the same
   phrasing at "Fiscal 2000 Expense Budget" returned zero hits — inconclusive (could be
   genuinely absent, or the practice existed under different phrasing/committee
   structure that far back and isn't findable by this exact string).

**Headline comparison:** Legistar's Schedule-C-equivalent coverage (confirmed to FY2008,
filed 2007) predates NYC Open Data's `4d7f-74pe` floor (FY2009) by at least one budget
cycle, and likely more if searched harder — this pass did not exhaustively probe FY2001–
FY2007. It also goes meaningfully deeper than council.nyc.gov's own budget-archive pages,
which (per the sibling FY22–24 scoping doc) only reliably expose FY2022 onward.

**Caveat — tool quirk carried over from the FY22–24 pass:** `nyc-council-mcp`'s
*local* full-text index (`search_bills`/`search_legislation`, not `_live`) still
under-indexes Resolutions relative to Introductions (see that doc's global finding on
Transparency Resolutions). All of the above was found via either the *live* Legistar API
search (`search_legislation_live`, which is reliable but returns results sorted by
last-modified rather than relevance/date, capped at the requested `limit`) or by
browsing `legistar.council.nyc.gov`'s own web search UI directly. A future pass wanting
a denser or more exhaustive year-by-year inventory should plan on the web UI, not the
local index, and should budget for the "All Years" dropdown reverting to "This Year"
after each AJAX postback (a recurring UI quirk that silently zeroes out results if not
re-set before every search).

**Not done in this pass (left for whoever picks up the import):** a systematic
year-by-year sweep back through FY2001; confirming whether the pre-2007 practice used
different title phrasing (e.g. no "designation" language) that a differently-worded
search would catch; and cross-checking coverage depth against the Council's own
Legistar "Session" groupings, which imply pre-1998 records may exist but weren't probed
here.
