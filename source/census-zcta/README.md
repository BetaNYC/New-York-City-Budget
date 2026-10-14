---
title: Census 2020 ZCTA-to-County relationship file (reference for ZIP checks)
type: source-readme
status: active
tags: [nyc-budget, expense-disclosure, census, zcta]
---

# Census 2020 ZCTA-to-County relationship file

Used for one thing: checking the ZIP codes in the expense disclosure
(`data/fyNN/expense_disclosure/`, columns `zip`, `zip_status` and `zip_candidates`; GitHub #70).

## What was downloaded, once

| | |
|---|---|
| File | `tab20_zcta520_county20_natl.txt` |
| URL | https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt |
| Retrieved | 2026-10-12, on the maintainer's approval (the only download for #70) |
| Bytes / sha256 / Last-Modified | in [`MANIFEST.csv`](MANIFEST.csv) |
| Record layout | https://www.census.gov/programs-surveys/geography/technical-documentation/records-layout/2020-zcta-record-layout.html |
| Explanation | https://www2.census.gov/geo/pdfs/maps-data/data/rel2020/zcta520/explanation_tab20_zcta520_county20_natl.pdf |
| State FIPS codes | https://www.census.gov/library/reference/code-lists/ansi/ansi-codes-for-states.html |

**The raw file is not committed** (6.8 MB). What is committed is the table derived from it,
[`data/reference/zcta2020_states.csv`](../../data/reference/zcta2020_states.csv) (every 2020
ZCTA and the state or states its counties lie in), and the script that derives it,
[`code/zcta_states.py`](../../code/zcta_states.py). To re-derive: download the file from the
URL above and run `python3 code/zcta_states.py --derive PATH`; the script refuses a file whose
sha256 is not the one in `MANIFEST.csv`.

## What a ZCTA is, and is not

A ZIP Code Tabulation Area is the Census Bureau's area approximation of a USPS ZIP code, built
from census blocks. **Not every USPS ZIP is a ZCTA**: ZIPs that serve only PO boxes or a single
building or organization have no area and so no ZCTA (`10008`, a Manhattan PO-box ZIP, is
not in the 2020 ZCTA list). A disclosure ZIP that is not a ZCTA is therefore marked `not_a_zcta`,
which means **not verified**, never "fake". The relationship file is also a 2020 vintage; a ZIP
created later is not in it.
