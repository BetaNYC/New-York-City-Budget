# NYC Open Data: City Council Discretionary Funding (`4d7f-74pe`)

Pulled whole on 2026-10-14 for GitHub #85: 97,002 rows, FY2009–FY2021, last updated by the
publisher 2021-04-20 (`rowsUpdatedAt` 1618932382). Analysis:
[`research/2026-10-14-open-data-vs-disclosure-diff.md`](../../research/2026-10-14-open-data-vs-disclosure-diff.md).

**Rows are designations, not applications.** The portal describes the dataset as
"applications for discretionary funding". Its rows are the same designations (awards) as the
Council's disclosure workbooks, row for row in most years. The Council's real application files
(every request, funded or not) are a different data class, found in the Internet Archive
(`source/wayback-council/README.md`). Count these rows as designations.

**Terms of use.** Covered by the NYC Open Data Terms of Use
(<https://opendata.cityofnewyork.us/overview/#termsofuse>). Use and redistribution in this
repository confirmed by Noel Hidalgo, 2026-10-14. The metadata carries no dataset-specific
license.

**BBL `0`.** 15 rows carry BBL `0` (FY2019 14, FY2010 1). That names no tax lot; wherever this
repository carries or profiles Open Data's BBL it is read as blank
(`code/diff_open_data_disclosure.py`, `od_geo`). We do not adopt Open Data's geocodes (#89 B7).

## Provenance

- **Rows:** SODA, `https://data.cityofnewyork.us/resource/4d7f-74pe.json?$select=:*,*&$order=:id&$limit=5000&$offset=N`,
  20 pages, one request at a time 2.5 s apart, with an app token (never recorded). Row count
  checked against `$select=count(*)`, and `:id` checked unique across pages.
- **Metadata:** read once through the `socrata` MCP (`get_data type=metadata`):
  `metadata-via-mcp-2026-10-14.json` (committed).
- **Data dictionary:** the dataset's attachment, `City_Council_Discretionary_Funding_Data_Dictionary.xlsx`
  (committed). It defines EIN, Amount, FC EIN and every geocoding column as `integer`, and
  defines no status values and no geocoding method.
- **Manifest:** [`MANIFEST.csv`](MANIFEST.csv): every page (URL, retrieval time, bytes, sha256,
  rows), the count, the dictionary, and the assembled CSV's sha256. Times for `count.json` and
  the metadata are the files' modification times.
- **Code:** `code/fetch_open_data_4d7f74pe.py`, `code/polite_http.py`.

## Not committed

The rows themselves (20 JSON pages, 76 MB; assembled `4d7f-74pe.csv`, 47 MB, 13 MB gzipped)
stay in the local cache. The sha256 in the manifest pins exactly what was compared. Whether to
commit a copy is an open question (the dataset could change or disappear; the publisher has
not touched it since 2021).
