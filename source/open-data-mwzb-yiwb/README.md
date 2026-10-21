# NYC Open Data: Expense Budget (`mwzb-yiwb`)

Publisher: Mayor's Office of Management & Budget (OMB). <https://data.cityofnewyork.us/d/mwzb-yiwb>. Pulled on 2026-10-21 for the Open
Data tracking plan ([`research/2026-10-21-open-data-tracking/PLAN.md`](../../research/2026-10-21-open-data-tracking/PLAN.md)),
approved by Noel Hidalgo 2026-10-21. Last updated by the publisher 2026-07-08 (rowsUpdatedAt 1783519030).

**An extract, not the whole dataset** (PLAN Q2, approved 2026-10-21): 180,885 of 1,137,678 rows. Kept: the adopted release of each fiscal year that has Terms & Conditions in the repo (FY2017, FY2018, FY2021–FY2027; the last `publication_date` before July 1 of the year before), and only the (agency, unit of appropriation) pairs those T&C files name. A multi-agency condition contributes every agency × every unit it lists, so the extract over-covers rather than misses. Releases before 2023 write agency and unit numbers without leading zeros (`40`, `1`), later ones padded (`040`, `001`); the filter asks for both. The exact `$where` is in `MANIFEST.csv`. FY2015–FY2016 are before the dataset starts (FY2017). Latest-only snapshot (PLAN Q3). It replaced a same-day first pull (105,717 rows) whose filter asked for padded numbers only and so missed FY2017–FY2023 for most agencies.

Used by: T&C crosswalk (`data/open_data/crosswalk_terms_unit.csv`): whether each unit of appropriation a condition names is in OMB's adopted expense budget, with its adopted amount. Context, not the condition.

## Snapshots

| Date | Folder | Rows | rowsUpdatedAt |
|---|---|---:|---|
| 2026-10-21 | this folder | 180,885 | 2026-07-08 |

Policy: latest only: a newer snapshot replaces this one (code/open_data_registry.py). `code/open_data_watch.py` says when rowsUpdatedAt moves.

## Provenance

- **Metadata:** `/api/views/mwzb-yiwb.json`, read first; its columns must equal the schema in
  `code/open_data_registry.py` (verified 2026-10-21), else the pull stops.
- **Rows:** SODA, `https://data.cityofnewyork.us/resource/mwzb-yiwb.json?$select=:*,*&$order=:id&$limit=5000&$offset=N`&$where=…,
  37 page(s), one request at a time 2.5 s apart, with the repo's standard User-Agent and **no app
  token** (none was configured; the MANIFEST says so). Row count checked against `$select=count(*)`, and
  `:id` checked unique across pages. Every response was HTTP 200.
- **Committed:** `mwzb-yiwb.csv.gz`, every pulled row, system fields plus every column, values exactly as served
  (gzip with mtime 0). Its sha256 and the uncompressed CSV's are in [`MANIFEST.csv`](MANIFEST.csv), with
  every page's URL, retrieval time, bytes and sha256. The pages stay in the local cache.
- **Data dictionary:** `Expense_Budget_Data_Dictionary.xlsx`, the dataset attachment (committed).
- **Code:** `code/fetch_open_data_snapshots.py`, `code/polite_http.py`.

## Terms of use

NYC Open Data Terms of Use (<https://opendata.cityofnewyork.us/overview/#termsofuse>). The metadata
carries no dataset-specific license.
