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
