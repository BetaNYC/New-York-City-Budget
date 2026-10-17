# NYC Open Data: Capital Commitment Plan (`2cmn-uidm`)

Publisher: Mayor's Office of Management & Budget (OMB). <https://data.cityofnewyork.us/d/2cmn-uidm>. Pulled whole on 2026-10-14 for
GitHub #89 (A6–A8): 60,739 rows, last updated by the publisher 2026-09-28 (rowsUpdatedAt 1790628315). Shape: THOUSANDS of dollars; release × budget line × City/Non-City, four or five years from yr1_fy; releases 2016-04-26 to 2026-09-28.
Used by `data/capital/` (`code/build_capital_council.py`); see `data/capital/README.md`.

## Provenance

- **Schema:** read once from the dataset's live metadata through the `socrata` MCP on
  2026-10-14; the column list is fixed in `code/fetch_open_data_capital.py`, which stops on
  any field outside it.
- **Rows:** SODA, `https://data.cityofnewyork.us/resource/2cmn-uidm.json?$select=:*,*&$order=:id&$limit=5000&$offset=N`,
  13 page(s), one request at a time 2.5 s apart, with an app token (never recorded). Row
  count checked against `$select=count(*)`, and `:id` checked unique across pages. Every
  response was HTTP 200.
- **Committed:** `2cmn-uidm.csv.gz`, every row, system fields plus every column, values exactly
  as served (gzip with mtime 0). Its sha256 and the uncompressed CSV's are in
  [`MANIFEST.csv`](MANIFEST.csv), with every page's URL, retrieval time, bytes and sha256.
  The pages themselves stay in the local cache.
- **Data dictionary:** `Capital_Commitment_Plan.xlsx`, the dataset's attachment (committed).
- **Code:** `code/fetch_open_data_capital.py`, `code/polite_http.py`.

## Terms of use

NYC Open Data Terms of Use (<https://opendata.cityofnewyork.us/overview/#termsofuse>). Use and
redistribution in this repository confirmed by Noel Hidalgo, 2026-10-14. The metadata carries
no dataset-specific license.
