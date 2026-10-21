# Is this record on NYC Open Data? (crosswalk)

**Report generated:** 2026-10-21 06:06 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** Open Data snapshots `4d7f-74pe`, `t474-a92g`, `46m8-77gv`, `2cmn-uidm` pulled
2026-10-14 (still current on 2026-10-21, `source/open-data-watch.csv`); `ujre-m2tj`, `djxg-kcfi`,
`mwzb-yiwb` (extract), `uvw5-9znb` pulled 2026-10-21.
**Plan:** [`research/2026-10-21-open-data-tracking/PLAN.md`](../../research/2026-10-21-open-data-tracking/PLAN.md),
approved by Noel Hidalgo 2026-10-21.

Built by `code/build_open_data_crosswalk.py --write` from committed files only (no network);
`--check` regenerates and compares. Rules are in that script's docstring.

## Files

| File | What |
|---|---|
| `crosswalk_expense.csv` | Council expense designations (`data/fyNN/expense_disclosure/`) vs `4d7f-74pe` and `ujre-m2tj` |
| `crosswalk_capital_award.csv` | Council capital awards (`data/capital/council_capital_awards.csv`, and Part I of `data/fyNN/pdf/capital_sd/` where promoted) vs `t474-a92g` |
| `crosswalk_capital_line.csv` | Council budget lines vs `46m8-77gv`, `2cmn-uidm`, `djxg-kcfi` (context) |
| `crosswalk_terms_unit.csv` | Units of appropriation named by Terms & Conditions vs `mwzb-yiwb` (context) |
| `crosswalk_history_<family>.csv.gz` | Every snapshot's rows, append-only |
| `coverage.csv` | Per family, dataset and fiscal year: our records by status, portal rows, portal-only rows |

Columns: `family, record_key, fiscal_year, dataset_id, snapshot_date, portal_row_id, match_status,
match_rule, differing_fields, portal_value, portal_status, portal_as_of`.

`record_key`: expense `FY|source_row`; capital award `report_year|source_row|amount_fy` (or
`pdf|FY|sub_id|amount_fy`); capital line `report_year|budget line`; T&C
`FY|item|agency|unit` (agency `A+B` when a retired CSV does not say whose unit it is).

**Statuses.** `same` · `differs` (fields listed) · `ambiguous` (two or more portal candidates,
listed; never a guess) · `absent` (the dataset covers the year; the record is not in it) · `context`
(the line or unit is on the portal, not the record itself) · `not_covered` (no dataset covers it:
counted in `coverage.csv`, not written as rows).

## What matched (covered years only)

| Family | Dataset | Years | Records | same | differs | ambiguous | absent | context | Portal-only |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| expense | `4d7f-74pe` | FY2009, FY2011–FY2021 | 89,923 | 54,995 | 0 | 34,423 | 505 | — | 1,787 |
| expense | `ujre-m2tj` | FY2019–FY2021 | 29,325 | 16,738 | 2 | 9,868 | 2,717 | — | 9,983 |
| capital award | `t474-a92g` | FY2019–FY2026 | 11,496 | 11,274 | 222 | 0 | 0 | — | 0 |
| capital line | `46m8-77gv` | FY2019–FY2027 | 1,402 | — | — | — | 1 | 1,401 | 24 |
| capital line | `2cmn-uidm` | FY2017–FY2027 | 1,594 | — | — | — | 4 | 1,590 | 3,892 |
| capital line | `djxg-kcfi` | all (one CPDB version) | 1,805 | — | — | — | 123 | 1,682 | 107 |
| T&C unit | `mwzb-yiwb` | FY2017, FY2018, FY2021–FY2027 | 1,263 | — | — | — | 35 | 1,187 | — |

Reading it:

- **Expense, `4d7f-74pe`.** 32,985 of the 34,423 `ambiguous` rows sit in a bucket with the same
  number of rows on each side and the same key values (EIN, amount): they *are* on the portal, but which
  portal row is which cannot be told from the keys. The other 1,438 are real count differences.
  The committed portal extract is keys only (#85), so only EIN and amount are compared here; other
  field differences are in `research/2026-10-14-open-data-diff/field-differences.csv`. FY2013's 1,545
  portal-only rows are the itemized citywide initiatives (#85 finding 4).
- **Expense, `ujre-m2tj`.** The bridge is the MOCS award number each record got from `4d7f-74pe`, so
  records ambiguous there stay ambiguous or absent here (most of the 9,983 portal-only awards are
  their partners). Its clearance status and posting date are in `portal_status` / `portal_as_of`
  (16,113 `Cleared - Contact Contracting Agency`); the Council workbook's own status stays on the
  record (PLAN Q6). The 2 `differs`: $23,296.50 printed by the Council, $23,296 on the portal.
- **Capital awards.** FY2019–FY2025 records *are* `t474-a92g` rows (data/capital loads them), so they
  are `same` except 4 the portal broke across rows. FY2026 (from the Council's workbook): 1,036
  `same`, 218 `differs`: 173 where the workbook lists district `00` (citywide) beside the member's and
  the portal drops it, and 44 where the **portal's text is damaged** (`Avilés` → `Avil├⌐s`, `Cabán`,
  `Ossé`: UTF-8 read as code page 437), plus `P CN1606`, broken on the portal (RECONCILIATION §2).
  FY2015–FY2017 and FY2027: no dataset.
- **Capital lines** are context. `46m8-77gv` uses `data/capital/council_vs_omb_by_budget_line.csv`
  (verdicts other than `match` are in `differing_fields`). `2cmn-uidm` portal-only counts every
  Council-series line in that year's plan that has no award that year (most carry over from earlier
  years), not a missing record. `djxg-kcfi` is one CPDB version: a line from FY2015 with no planned
  commitment now is `absent` there and that is expected.
- **T&C units** are context: the unit is in OMB's adopted expense budget for that year, with its
  adopted amount (`portal_value`) and row count. `not_covered`: `All` units, budget lines, and years
  before FY2017 (the dataset starts there).

## Watch and refresh

`code/open_data_watch.py` (metadata only) appends to `source/open-data-watch.csv`. When a dataset's
verdict is `changed`, pull it with the fetcher named in `code/open_data_registry.py`, then run
`code/build_open_data_crosswalk.py --write`; the new snapshot's rows join the history files.
