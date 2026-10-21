---
title: "Plan: track whether each record is on NYC Open Data"
created: 2026-10-21
type: plan
status: draft, for Noel's approval before any bulk pull
tags: [open-data, explorer, mcp, crosswalk, provenance]
---

# Plan: track whether each record is on NYC Open Data

**Report generated:** 2026-10-21 00:48 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** NYC Open Data catalog and dataset metadata read 2026-10-21 00:35–00:45 EDT
(read-only; no rows pulled). Builds on the #84 inventory,
[`../2026-10-14-structured-data-inventory.md`](../2026-10-14-structured-data-inventory.md).
**Implements:** item 2 of `viz/explorer/DESIGN-NOTES.md` (branch `feature/budget-explorer`).
**Status:** a plan only. Per that note and the workspace research-planning rule, **no dataset is
pulled until Noel approves this plan.**

## 1. Goal

For every record the explorer and the MCP serve, say one of:

- **"Also on NYC Open Data: dataset X, row Y, as of D"** (same values), or
- **"On NYC Open Data with differences: …, as of D"** (which fields differ), or
- **"Not on NYC Open Data as of D"** (a dataset covers that year and kind, and the record is not in it), or
- **"No NYC Open Data dataset covers this"** (no dataset covers that year and kind; different from absent).

And keep history: when a record first appeared on the portal, and when it changed or left.

## 2. Scope

**In:** the record families the repo already serves or is about to serve:

| Family | Repo source | Record key |
|---|---|---|
| Expense designations | `data/fyNN/expense_disclosure/` (Council workbooks), Schedule C PDFs (`data/fyNN/pdf/schedule_c/`) | (fiscal year, MOCS ID) where the workbook has one (FY2024+); else the #85 match key below |
| Council capital awards | `data/capital/council_capital_awards.csv`, capital §254 PDFs (`data/fyNN/pdf/capital_sd/`) | (report year, project ID without agency prefix, budget line, amount FY) |
| Capital budget lines | `data/capital/omb_*_council_lines.csv` | (release, budget line, FY) |
| Terms & Conditions | `data/fyNN/pdf/terms/` | (fiscal year, agency code, unit of appropriation): a **context** link, not the same record (no dataset publishes the conditions) |

**Out (for now):** transparency-resolution-only changes (no portal dataset carries them),
participatory budgeting ballots, geography, and any live portal call from the explorer or the MCP.

## 3. Datasets

Found by catalog search (12 queries: council discretionary, city council capital, city council,
discretionary funding, schedule C, capital budget, expense budget, participatory budgeting, council
initiatives, terms and conditions, budget modification, capital commitment plan) and each
candidate's metadata (`/api/views/<id>.json`). "Rows" is the metadata's cached count. "Updated" is
`rowsUpdatedAt`.

### Tier 1: record-level matches (build)

| ID | Name, publisher | Covers | Rows | Updated | In repo | Use |
|---|---|---|---:|---|---|---|
| `4d7f-74pe` | City Council Discretionary Funding (blank attribution; Council data) | FY2009–FY2021 | 97,002 | 2021-04-20 (frozen) | `source/open-data-4d7f-74pe/` (2026-10-14; unchanged since) | Expense designations, row for row (#85) |
| `ujre-m2tj` | Discretionary Award Tracker, MOCS | FY2019–FY2021 (one 2021 snapshot) | 53,418 | 2021-06-30 (frozen) | no | Bridge MOCS award number → clearance status; second witness for FY2019–FY2021 |
| `t474-a92g` | City Council Capital Budget, NYCC | report years FY2019–FY2026 | 11,503 | 2025-12-17 | `source/open-data-t474-a92g/` (2026-10-14; unchanged since) | Council capital awards, row for row (`data/capital/RECONCILIATION.md` §4) |

### Tier 2: line-level or project-level context (build where a key exists)

| ID | Name, publisher | Rows | Updated | In repo | Use |
|---|---|---:|---|---|---|
| `46m8-77gv` | Capital Budget, OMB | 16,491 | 2026-07-13 | yes (2026-10-14; unchanged) | Council budget line appears in OMB's adopted budget (amount by line, not by award) |
| `2cmn-uidm` | Capital Commitment Plan, OMB | 60,739 | 2026-09-28 | yes (2026-10-14; unchanged) | Line in the commitment plan, by release |
| `djxg-kcfi` | CPDB – Commitments, DCP | 41,277 | 2026-08-24 | no | The only bridge from a budget line (`AG-DN04L`) to an FMS project |
| `mwzb-yiwb` | Expense Budget, OMB | 1,137,678 | 2026-07-08 | no | T&C context: the unit of appropriation exists in OMB's budget, with its adopted amount |
| `uvw5-9znb` | City Council Members (1999 to Present), NYCC | 558 | 2026-04-10 | no | Member terms; input to the Speakers table (DESIGN-NOTES item 3), sourced from a record |

### Tier 3: hold (no clean key, or frozen and narrow)

`7hgn-sgmk` DCLA Cultural Organizations Capital Funding (707 rows, 2026-04-28; FY15-named columns,
organization only), `qm5f-frjb` / `wwhr-5ven` Participatory Budgeting (frozen 2018 / 2017; no budget
line), `fi59-268w` CPDB Projects (no budget line), `fb86-vt7u` Capital Projects Dashboard (key needs
normalizing; #84). Each stays as in the #84 inventory.

**Already-held snapshots are current.** `4d7f-74pe`, `t474-a92g`, `46m8-77gv` and `2cmn-uidm` show
the same `rowsUpdatedAt` today as in their 2026-10-14 pulls, so the first crosswalk needs **no new
pull** for them.

## 4. Snapshot cadence and storage

**Watch metadata, pull on change.** A small script reads each dataset's metadata only
(`/api/views/<id>.json`: `rowsUpdatedAt`, column list, cached row count) and writes one line per
dataset to `source/open-data-watch.csv`. A whole pull happens only when `rowsUpdatedAt` moved.

| Dataset kind | Metadata check | Expected change |
|---|---|---|
| Frozen (`4d7f-74pe`, `ujre-m2tj`, PB) | quarterly | none |
| Council capital `t474-a92g` | monthly | about once a year (December) |
| OMB releases (`46m8-77gv`, `2cmn-uidm`, `mwzb-yiwb`) | monthly | 3 times a year (January, April/May, June/July; plus September for the commitment plan) |
| DCP CPDB, Council members | monthly | every few months |

Run by hand at first. A scheduled job (GitHub Action or the app scheduler) only after Noel says so.

**Storage: the existing pattern, extended for history.**

- Keep `source/open-data-<id>/` as is: `README.md` (publisher, terms, row counts, method),
  `MANIFEST.csv` (every page: URL, time, bytes, sha256), the gzip'd CSV (values as served, gzip
  mtime 0), the data dictionary.
- The current files become the **first snapshot**. Later snapshots go to
  `source/open-data-<id>/<YYYY-MM-DD>/` with their own `MANIFEST.csv`; the top-level README lists them.
- Same fetch rules as `code/fetch_open_data_capital.py` / `code/polite_http.py`: SODA paged on `:id`,
  one request at a time 2.5 s apart, app token never recorded, `count(*)` and `:id` uniqueness checked.
- **`mwzb-yiwb` is large** (1.1 M rows). Store a Council-relevant extract (the agencies and units of
  appropriation the T&C files name, every publication date), as `data/capital/` does for
  `2cmn-uidm`, with the SoQL filter in the MANIFEST. Open question Q2.

## 5. Crosswalk design

One table per family, built by the same loader as everything else (`mcp/scripts/build-index.mjs`
reads them; nothing reads `research/` or the portal at build time):

`data/open_data/crosswalk_<family>.csv`

| Column | Meaning |
|---|---|
| `family` | `expense`, `capital_award`, `capital_line`, `terms_unit` |
| `record_key` | the repo record's key, as one string (§2) |
| `fiscal_year` | the record's year |
| `dataset_id` | e.g. `t474-a92g` |
| `snapshot_date` | which snapshot this row compares against |
| `portal_row_id` | the portal's `:id`; blank when absent |
| `match_status` | `same`, `differs`, `absent`, `not_covered`, `ambiguous`, `context` |
| `match_rule` | which rule matched (below) |
| `differing_fields` | `;`-joined, with both values, when `differs` |

**History:** `data/open_data/crosswalk_history_<family>.csv` keeps every snapshot's rows (append
only). The explorer shows the latest; "first seen / last seen" come from history.

**Match rules** (in order; the first that gives one portal row wins; two or more → `ambiguous`,
never a guess):

- **Expense (`4d7f-74pe`):** reuse `code/diff_open_data_disclosure.py`, which already matches
  FY2009–FY2021 row for row: EIN padded to 9 digits (the portal lost leading zeros on 1,600),
  amount within Open Data's rounding (whole dollars FY2012+, cents before), then member, source,
  agency, organization. MOCS ID is not usable before FY2024 (the workbooks have none).
- **Expense (`ujre-m2tj`):** MOCS award number when the record has one; else (fiscal year,
  vendor name normalized, amount, agency).
- **Capital award (`t474-a92g`):** (report year, project ID with whitespace collapsed and the agency
  prefix dropped, budget line, amount FY, amount), as `data/capital/` does. Broken portal records
  (#89 RECONCILIATION §2) are `differs` with the repair named.
- **Capital line (`46m8-77gv`, `2cmn-uidm`, `djxg-kcfi`):** budget line normalized (`PV DN132`,
  `PVDN132`, `PV-DN132` are one line), release, FY. Status `context`: the line is on the portal, not
  the award.
- **T&C unit (`mwzb-yiwb`):** (fiscal year, agency number, unit of appropriation), latest
  publication on or before the T&C adoption. Status `context`.

**`not_covered`** is decided per dataset from its coverage (e.g. `4d7f-74pe` stops at FY2021), so
"not on Open Data" is never claimed for a year no dataset covers.

**Explorer:** a badge per row ("On Open Data", "Differs", "Not on Open Data as of D", "No Open
Data dataset"), a link to the portal row, and a per-year coverage strip. The MCP gets the same
fields. Parity test covers the crosswalk tables.

## 6. Effort

| Step | Days |
|---|---:|
| Metadata watch script + `source/open-data-watch.csv` + tests | 0.5 |
| New snapshots: `ujre-m2tj`, `djxg-kcfi`, `uvw5-9znb`, `mwzb-yiwb` extract (after approval) | 1 |
| Expense crosswalk (reuses #85 code) + history | 1–1.5 |
| Capital award and line crosswalks | 1 |
| T&C context links | 0.5 |
| Loader, parity test, explorer badge and coverage strip | 1.5–2 |
| **Total** | **5.5–6.5** |

## 7. Open questions for Noel

1. **Approve the dataset list?** Tier 1 and 2 build; tier 3 held. Suggested: yes.
2. **`mwzb-yiwb` (1.1 M rows): whole, or a Council-relevant extract?** DESIGN-NOTES says "pull each
   dataset whole". Suggested: extract, with the filter recorded (size; the rest is not Council data).
3. **Keep every changed snapshot in git, or only the latest plus manifests and crosswalk history?**
   Suggested: keep every changed snapshot for the small datasets; latest only for the two big OMB ones.
4. **Scheduled watch, or by hand?** Suggested: by hand until the crosswalk is in use.
5. **Wording when a dataset is frozen.** For FY2010, the portal has rows the Council's workbook
   lacks (#89 A3). Should the explorer show portal-only records too, or only flag ours? Suggested:
   flag ours only in v1; list portal-only counts per year on the coverage strip.
6. **`ujre-m2tj`'s status values** (clearance) are newer than `4d7f-74pe`'s for FY2019–FY2021. Show
   both? Suggested: show both, dated.
