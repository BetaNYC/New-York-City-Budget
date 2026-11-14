# NYC Open Data: Capital Projects Database (CPDB) - Projects (`fi59-268w`)

Publisher: Department of City Planning (DCP). <https://data.cityofnewyork.us/d/fi59-268w>. Pulled on 2026-11-14 for #250
(serve OMB's capital commitment plan and DCP's CPDB in the MCP; part of the 2.1.0 epic #312). Last updated by the
publisher 2026-08-24 (rowsUpdatedAt 1787586651).

12,929 rows, every row: one row per FMS project (`maprojid` = `magency` + `projectid`). One CPDB version (`ccpversion`
`fisa_2026`), the same version as [`djxg-kcfi`](../open-data-djxg-kcfi/README.md). Every `maprojid` here is also in
`djxg-kcfi`, and the reverse.

**No budget line.** This dataset has no budget-line column. A project reaches a budget line only through `djxg-kcfi`,
and 3,501 of the 12,929 projects sit on more than one budget line there. So a project's totals here (planned, adopted,
allocated, committed, spent) are never split or summed to one budget line.

**Unit.** The column descriptions do not state one, and the dataset has no data-dictionary attachment.

## Snapshots

| Date | Folder | Rows | rowsUpdatedAt |
|---|---|---:|---|
| 2026-11-14 | this folder | 12,929 | 2026-08-24 |

Policy: every changed snapshot is kept (later ones in `<date>/` folders) (code/open_data_registry.py). `code/open_data_watch.py` says when rowsUpdatedAt moves.

## Provenance

- **Metadata:** `/api/views/fi59-268w.json`, read first; its columns must equal the schema in
  `code/open_data_registry.py` (verified 2026-11-14), else the pull stops.
- **Rows:** SODA, `https://data.cityofnewyork.us/resource/fi59-268w.json?$select=:*,*&$order=:id&$limit=5000&$offset=N`,
  3 page(s), one request at a time 2.5 s apart, with the repo's standard User-Agent and **no app
  token** (the MANIFEST says so). Row count checked against `$select=count(*)`, and
  `:id` checked unique across pages. Every response was HTTP 200 (5 requests in all).
- **Committed:** `fi59-268w.csv.gz`, every pulled row, system fields plus every column, values exactly as served
  (gzip with mtime 0). Its sha256 and the uncompressed CSV's are in [`MANIFEST.csv`](MANIFEST.csv), with
  every page's URL, retrieval time, bytes and sha256. The pages stay in the local cache.
- **Data dictionary:** none attached to the dataset.
- **Code:** `code/fetch_open_data_snapshots.py`, `code/polite_http.py`.

## Terms of use

NYC Open Data Terms of Use (<https://opendata.cityofnewyork.us/overview/#termsofuse>). The metadata
carries no dataset-specific license.
