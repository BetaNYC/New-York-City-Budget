# NYC Open Data: City Council Capital Budget (`t474-a92g`)

Publisher: City Council (NYCC). <https://data.cityofnewyork.us/d/t474-a92g>. Pulled whole on 2026-10-14 for
GitHub #89 (A6–A8): 11,503 rows, last updated by the publisher 2025-12-17 (rowsUpdatedAt 1766003942). Shape: whole dollars; one row per Council capital award, report years FY2019–FY2026.
Used by `data/capital/` (`code/build_capital_council.py`); see `data/capital/README.md`.

## Provenance

- **Schema:** read once from the dataset's live metadata through the `socrata` MCP on
  2026-10-14; the column list is fixed in `code/fetch_open_data_capital.py`, which stops on
  any field outside it.
- **Rows:** SODA, `https://data.cityofnewyork.us/resource/t474-a92g.json?$select=:*,*&$order=:id&$limit=5000&$offset=N`,
  3 page(s), one request at a time 2.5 s apart, with an app token (never recorded). Row
  count checked against `$select=count(*)`, and `:id` checked unique across pages. Every
  response was HTTP 200.
- **Committed:** `t474-a92g.csv.gz`, every row, system fields plus every column, values exactly
  as served (gzip with mtime 0). Its sha256 and the uncompressed CSV's are in
  [`MANIFEST.csv`](MANIFEST.csv), with every page's URL, retrieval time, bytes and sha256.
  The pages themselves stay in the local cache.
- **Data dictionary:** `City_Council_Capital_Budget_Data_Dictionary.xlsx`, the dataset's attachment (committed).
- **Code:** `code/fetch_open_data_capital.py`, `code/polite_http.py`.

## Terms of use

NYC Open Data Terms of Use (<https://opendata.cityofnewyork.us/overview/#termsofuse>). Use and
redistribution in this repository confirmed by Noel Hidalgo, 2026-10-14. The metadata carries
no dataset-specific license.
