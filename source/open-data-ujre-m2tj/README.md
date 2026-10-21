# NYC Open Data: Discretionary Award Tracker (`ujre-m2tj`)

Publisher: Mayor's Office of Contract Services (MOCS). <https://data.cityofnewyork.us/d/ujre-m2tj>. Pulled on 2026-10-21 for the Open
Data tracking plan ([`research/2026-10-21-open-data-tracking/PLAN.md`](../../research/2026-10-21-open-data-tracking/PLAN.md)),
approved by Noel Hidalgo 2026-10-21. Last updated by the publisher 2021-06-30 (rowsUpdatedAt 1625084549).

53,418 rows, every row. One row per (award, posting): two postings, 2021-05-05 (26,698 rows) and 2021-06-09 (26,720), so most awards appear twice. 26,723 distinct MOCS award numbers, FY19 / FY20 / FY21. `statussummary` is the clearance status at the posting date (51,743 rows `Cleared - Contact Contracting Agency`).

Used by: Expense crosswalk (`data/open_data/crosswalk_expense.csv`): the MOCS award number bridges to the Council rows that carry one from `4d7f-74pe`, and its status is shown beside the Council workbook's, each dated (PLAN Q6).

## Snapshots

| Date | Folder | Rows | rowsUpdatedAt |
|---|---|---:|---|
| 2026-10-21 | this folder | 53,418 | 2021-06-30 |

Policy: every changed snapshot is kept (later ones in `<date>/` folders) (code/open_data_registry.py). `code/open_data_watch.py` says when rowsUpdatedAt moves.

## Provenance

- **Metadata:** `/api/views/ujre-m2tj.json`, read first; its columns must equal the schema in
  `code/open_data_registry.py` (verified 2026-10-21), else the pull stops.
- **Rows:** SODA, `https://data.cityofnewyork.us/resource/ujre-m2tj.json?$select=:*,*&$order=:id&$limit=5000&$offset=N`,
  11 page(s), one request at a time 2.5 s apart, with the repo's standard User-Agent and **no app
  token** (none was configured; the MANIFEST says so). Row count checked against `$select=count(*)`, and
  `:id` checked unique across pages. Every response was HTTP 200.
- **Committed:** `ujre-m2tj.csv.gz`, every pulled row, system fields plus every column, values exactly as served
  (gzip with mtime 0). Its sha256 and the uncompressed CSV's are in [`MANIFEST.csv`](MANIFEST.csv), with
  every page's URL, retrieval time, bytes and sha256. The pages stay in the local cache.
- **Data dictionary:** `DICTIONARY Discretionary Award Tracker.xlsx`, the dataset attachment (committed).
- **Code:** `code/fetch_open_data_snapshots.py`, `code/polite_http.py`.

## Terms of use

NYC Open Data Terms of Use (<https://opendata.cityofnewyork.us/overview/#termsofuse>). The metadata
carries no dataset-specific license.
