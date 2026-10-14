# NYC Council budget files recovered from the Internet Archive

Files the Council once published at `council.nyc.gov/downloads/excel/` (the old site, captured
2011–2016) and `council.nyc.gov/budget/wp-content/uploads/sites/54/2016/` (the WordPress budget
site, captured 2017–2025), plus one capture of the RnD site's `Capital-Database.xlsx`.
Recovered for GitHub #86 on 2026-10-14. Analysis:
[`research/2026-10-14-wayback-council-files.md`](../../research/2026-10-14-wayback-council-files.md).

## Provenance

- **Listing:** Wayback CDX API, 9 queries, every one recorded in
  [`CDX-QUERIES.csv`](CDX-QUERIES.csv) (query URL, sha256 of the response, rows).
- **Download:** `https://web.archive.org/web/<timestamp>id_/<original-url>` (the `id_` replay
  flag returns the archived bytes unmodified). One request at a time, 6 s apart. 27 downloads,
  all HTTP 200; no 429 or 403.
- **Manifest:** [`MANIFEST.csv`](MANIFEST.csv) has every downloaded file: original URL, Wayback
  timestamp, retrieval time, bytes, sha256, rows (data rows below the header in the one sheet
  that holds data; CSV: records). Each file's SHA-1 equals the digest CDX reported for it.
- **Code:** `code/fetch_wayback_council_files.py` (listing, download, `rows`),
  `code/polite_http.py` (pacing, 429/403 handling, cache, manifest).
- **Rights:** © The City of New York; official Council publications reproduced as public
  records, same terms as the rest of `source/`.

## What is committed here, and what is not

Committed (`files/<timestamp>/<name>`, 9.3 MB):

| File | Capture | Why |
|---|---|---|
| `funded_disclosure_FY2009.xls` … `FY2012.xls` | 2025-02-12 | The Council's own workbooks for four years the dataset does not have. Older captures (2014–2016) are content-identical, row for row. |
| `Capital-Database-FY15.xlsx`, `-FY16.xlsx` | 2014-10-25, 2015-09-10 | Capital designations for years the RnD site no longer serves (#87). |
| `Capital-Database-FY17.xlsx` | 2017-07-04 | Same. |
| `Capital-Database.xlsx` | 2025-12-03 | RnD's FY26 file; content-identical to the July 2026 copy in git history. |
| `FY17-Terms-and-Conditions.csv` | 2021-03-03 | Only CSV of its kind found. |

**Left in the local cache only** (listed in `MANIFEST.csv`, hashes recorded, re-downloadable
from the Internet Archive by the same URL): the 2014–2016 duplicate captures of FY2009–FY2012;
the FY2013–FY2017 historical snapshots; the three application files
(`unfunded_disclosure_FY2012.xls` 16 MB, `applied_disclosure_FY2014.xls` 18 MB,
`FY2013_CM_Applications_REFORMAT.xlsx` 2.5 MB). Whether to commit any of them is an open
question for the maintainer (see the follow-up questions).

**Never to be committed as is:** the 2014-10-16 capture of `funded_disclosure_FY2015.xlsx`
carries three columns of grantee contact data (Contact Person, Contact Phone #, Contact Email).
The parser drops those columns by name and records that they were present.
