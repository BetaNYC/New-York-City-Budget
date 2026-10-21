# NYC Open Data: Capital Projects Database (CPDB) - Commitments (`djxg-kcfi`)

Publisher: Department of City Planning (DCP). <https://data.cityofnewyork.us/d/djxg-kcfi>. Pulled on 2026-10-21 for the Open
Data tracking plan ([`research/2026-10-21-open-data-tracking/PLAN.md`](../../research/2026-10-21-open-data-tracking/PLAN.md)),
approved by Noel Hidalgo 2026-10-21. Last updated by the publisher 2026-08-24 (rowsUpdatedAt 1787586625).

41,277 rows, every row. One CPDB version (`ccpversion` `fisa_2026`): planned commitments 2025-07-01 to 2039-06-01. `budgetline` is written with a hyphen (`AG-DN04L`).

Used by: Capital line crosswalk (`data/open_data/crosswalk_capital_line.csv`): whether a Council budget line has a planned commitment in the current CPDB version. Context, not the award.

## Snapshots

| Date | Folder | Rows | rowsUpdatedAt |
|---|---|---:|---|
| 2026-10-21 | this folder | 41,277 | 2026-08-24 |

Policy: every changed snapshot is kept (later ones in `<date>/` folders) (code/open_data_registry.py). `code/open_data_watch.py` says when rowsUpdatedAt moves.

## Provenance

- **Metadata:** `/api/views/djxg-kcfi.json`, read first; its columns must equal the schema in
  `code/open_data_registry.py` (verified 2026-10-21), else the pull stops.
- **Rows:** SODA, `https://data.cityofnewyork.us/resource/djxg-kcfi.json?$select=:*,*&$order=:id&$limit=5000&$offset=N`,
  9 page(s), one request at a time 2.5 s apart, with the repo's standard User-Agent and **no app
  token** (none was configured; the MANIFEST says so). Row count checked against `$select=count(*)`, and
  `:id` checked unique across pages. Every response was HTTP 200.
- **Committed:** `djxg-kcfi.csv.gz`, every pulled row, system fields plus every column, values exactly as served
  (gzip with mtime 0). Its sha256 and the uncompressed CSV's are in [`MANIFEST.csv`](MANIFEST.csv), with
  every page's URL, retrieval time, bytes and sha256. The pages stay in the local cache.
- **Data dictionary:** none attached to the dataset.
- **Code:** `code/fetch_open_data_snapshots.py`, `code/polite_http.py`.

## Terms of use

NYC Open Data Terms of Use (<https://opendata.cityofnewyork.us/overview/#termsofuse>). The metadata
carries no dataset-specific license.
