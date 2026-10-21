# NYC Open Data: City Council Members (1999 to Present) (`uvw5-9znb`)

Publisher: City Council (NYCC). <https://data.cityofnewyork.us/d/uvw5-9znb>. Pulled on 2026-10-21 for the Open
Data tracking plan ([`research/2026-10-21-open-data-tracking/PLAN.md`](../../research/2026-10-21-open-data-tracking/PLAN.md)),
approved by Noel Hidalgo 2026-10-21. Last updated by the publisher 2026-04-10 (rowsUpdatedAt 1775844029).

558 rows, every row: one per member term (`council_member_id` is the Legistar person id; `term_start`, `term_end`, `district`, `office_id`). **No role column**: it does not say who was Speaker.

Used by: `data/reference/council_speakers.csv` (member id and terms), DESIGN-NOTES item 3.

## Snapshots

| Date | Folder | Rows | rowsUpdatedAt |
|---|---|---:|---|
| 2026-10-21 | this folder | 558 | 2026-04-10 |

Policy: every changed snapshot is kept (later ones in `<date>/` folders) (code/open_data_registry.py). `code/open_data_watch.py` says when rowsUpdatedAt moves.

## Provenance

- **Metadata:** `/api/views/uvw5-9znb.json`, read first; its columns must equal the schema in
  `code/open_data_registry.py` (verified 2026-10-21), else the pull stops.
- **Rows:** SODA, `https://data.cityofnewyork.us/resource/uvw5-9znb.json?$select=:*,*&$order=:id&$limit=5000&$offset=N`,
  1 page(s), one request at a time 2.5 s apart, with the repo's standard User-Agent and **no app
  token** (none was configured; the MANIFEST says so). Row count checked against `$select=count(*)`, and
  `:id` checked unique across pages. Every response was HTTP 200.
- **Committed:** `uvw5-9znb.csv.gz`, every pulled row, system fields plus every column, values exactly as served
  (gzip with mtime 0). Its sha256 and the uncompressed CSV's are in [`MANIFEST.csv`](MANIFEST.csv), with
  every page's URL, retrieval time, bytes and sha256. The pages stay in the local cache.
- **Data dictionary:** `City_Council_Members_Data_Dictionary.xlsx`, the dataset attachment (committed).
- **Code:** `code/fetch_open_data_snapshots.py`, `code/polite_http.py`.

## Terms of use

NYC Open Data Terms of Use (<https://opendata.cityofnewyork.us/overview/#termsofuse>). The metadata
carries no dataset-specific license.
