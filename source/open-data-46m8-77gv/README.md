# NYC Open Data: Capital Budget (`46m8-77gv`)

Publisher: Mayor's Office of Management & Budget (OMB). <https://data.cityofnewyork.us/d/46m8-77gv>. Pulled whole on 2026-10-14 for
GitHub #89 (A6–A8): 16,491 rows, last updated by the publisher 2026-07-13 (rowsUpdatedAt 1783965522). Shape: whole dollars; release × budget line × funding source, four years from yr1_fy; releases 2018-02-01 to 2026-07-13.
Used by `data/capital/` (`code/build_capital_council.py`); see `data/capital/README.md`.

## Provenance

- **Schema:** read once from the dataset's live metadata through the `socrata` MCP on
  2026-10-14; the column list is fixed in `code/fetch_open_data_capital.py`, which stops on
  any field outside it.
- **Rows:** SODA, `https://data.cityofnewyork.us/resource/46m8-77gv.json?$select=:*,*&$order=:id&$limit=5000&$offset=N`,
  4 page(s), one request at a time 2.5 s apart, with an app token (never recorded). Row
  count checked against `$select=count(*)`, and `:id` checked unique across pages. Every
  response was HTTP 200.
- **Committed:** `46m8-77gv.csv.gz`, every row, system fields plus every column, values exactly
  as served (gzip with mtime 0). Its sha256 and the uncompressed CSV's are in
  [`MANIFEST.csv`](MANIFEST.csv), with every page's URL, retrieval time, bytes and sha256.
  The pages themselves stay in the local cache.
- **Data dictionary:** `Capital_Budget_Data_Dictionary.xlsx`, the dataset's attachment (committed).
- **Code:** `code/fetch_open_data_capital.py`, `code/polite_http.py`.

## Terms of use

NYC Open Data Terms of Use (<https://opendata.cityofnewyork.us/overview/#termsofuse>). Use and
redistribution in this repository confirmed by Noel Hidalgo, 2026-10-14. The metadata carries
no dataset-specific license.
