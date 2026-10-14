# The Council's own budget files in the Internet Archive

**Report generated:** 2026-10-14 (office) · **Data current as of:** Internet Archive CDX and
downloads 2026-10-14 06:56–07:05 ET; captures range from 2011-10-27 to 2025-12-03 · Issue: #86
(epic #89); capital profiles feed #87.

Code: `code/fetch_wayback_council_files.py` (CDX listing, `id_` downloads, manifest row counts),
`code/polite_http.py`, `code/diff_disclosure_snapshots.py` (unchanged, reused), and three narrow
extensions to `code/parse_expense_disclosure.py` (below). Raw files and manifests:
[`source/wayback-council/`](../source/wayback-council/). Snapshot diffs:
[`2026-10-14-wayback-snapshot-diffs/`](2026-10-14-wayback-snapshot-diffs/). The Open Data
comparison of FY2009–FY2012 is in
[`2026-10-14-open-data-vs-disclosure-diff.md`](2026-10-14-open-data-vs-disclosure-diff.md).
Follow-up questions: [`2026-10-14-follow-up-questions-85-86.md`](2026-10-14-follow-up-questions-85-86.md).

## Requests made

| Host | Requests | Statuses |
|---|---:|---|
| web.archive.org (CDX) | 9 | 9 × 200 |
| web.archive.org (downloads, `id_`) | 27 | 27 × 200 |

Paced at ≥ 6 s, one at a time. No 429 or 403. (Three CDX queries made earlier on 2026-10-14
for the first look are not counted here.) No file was fetched twice. Before any download, the
CDX digest, which is the SHA-1 of the content, was checked against our repo files. That is how
the 2025 capture of `funded_disclosure_FY2014.xlsx` was skipped: it is byte-identical to ours.

## Where the files were

Three locations, not one:

1. **`council.nyc.gov/downloads/excel/`**, the Council's pre-2016 site, captured 2011–2016:
   `funded_disclosure_FY2009.xls` … `FY2012.xls`, `FY2014.xls` (an **.xls** version of FY2014),
   `FY2015.xlsx` (six distinct versions, 2014-10 to 2016-12), `FY2016.xlsx`, `FY2017.xlsx`,
   `Capital-Database-FY15.xlsx`, `Capital-Database-FY16.xlsx`, and three **application** files:
   `unfunded_disclosure_FY2012.xls`, `applied_disclosure_FY2014.xls`,
   `FY2013_CM_Applications_REFORMAT.xlsx`. There is no FY2013 disclosure here. A FY2016 capture
   from 2015-06 is a 404.
2. **`council.nyc.gov/budget/wp-content/uploads/sites/54/2016/`**, the WordPress budget site:
   `2016/06/` has `funded_disclosure_FY2017.xlsx` (2017-06), `Capital-Database-FY17.xlsx`
   (2017-07), `FY17-Terms-and-Conditions.csv` and PDFs. `2016/08/` has FY2009–FY2016 workbooks,
   all captured 2025-02-12.
3. **`rnd.council.nyc.gov/src/assets/Capital-Database.xlsx`**: one capture (2025-12-03).

The old site also served the disclosure as JavaScript (`includes/scripts/funded_disclosure_2014.js`
… `2017.js`, ~0.5 MB each, one capture each). Not downloaded.

## FY2009–FY2012: the Council's own workbooks

Every pair of captures is **content-identical**: the same rows, statuses and amounts in the
2014–2016 copy and the 2025 copy (`2026-10-14-wayback-snapshot-diffs/fy2009…fy2012`), though the
bytes differ (an .xls re-save). The 2025 copy of FY2013 is likewise content-identical to our
2026-10-12 FY2013 file. **The Council never revised FY2009–FY2013 after first publishing them.**

| FY | Sheet | Award rows | Cleared | Pending | Other (raw) | Total $ |
|---|---|---:|---:|---:|---|---:|
| 2009 | MASTER | 5,745 | 4,356 | 1,389 | — | 414,226,176.88 |
| 2010 | MASTER | 2,592 | 1,048 | 1,544 | — | 111,558,052.58 |
| 2011 | MASTER | 5,420 | 4,894 | 387 | Government 136, Pending FC Clearance 3 | 395,907,487.50 |
| 2012 | MASTER | 5,823 | 5,482 | 137 | Government 49 ($235.2M), CBO Defunded 155 ($0) | 386,832,781.80 |

**The existing parser reads all four with no new header synonyms.** Their headers ("Legal Name",
"Amount", "Amount ($)", "Street Address 1/2", "Address 2 (optional)", "Zip Code", "Fiscal
Conduit Name", "FC EIN") are already in `HEADER_MAP`. All four lack a MOCS ID and a Fiscal Year
column, as FY2013 does. FY2011 and FY2012 add status values the later years do not use
(`Government`, `Pending FC Clearance`, `CBO Defunded`). Each workbook has 0 stripped rows and 0 footer totals, so there is
no printed total to reconcile against.

Against Open Data (#85), FY2009, FY2011 and FY2012 agree row for row after rounding. **FY2010
does not:** the Council's workbook has 2,592 rows to Open Data's 5,981. Open Data has 1,864 Local, 817
Youth and 561 Aging rows the workbook does not, and on 180 matched rows the workbook's address is
blank. Both archived copies agree, so this is what the Council published, not a broken
capture.

## Older snapshots of FY2013–FY2017 vs our 2026-10-12 files

| FY | Old → new | Rows old → new | $ old → new | What moved |
|---|---|---|---|---|
| 2013 | 2025-02-12 → ours | 4,987 → 4,987 | equal | nothing |
| 2014 | 2016-05-23 `.xls` → ours `.xlsx` | 6,084 → 6,611 | 393.18M → 393.73M | 952 pending→cleared; +986 / −459 rows; 69 candidate amount changes; 92 likely re-issued |
| 2015 | 2014-10-16 → 2014-11-16 | 6,291 → 6,291 | equal | nothing (status blank or `*` in both) |
| 2015 | 2014-11-16 → 2014-12-17 | 6,291 → 6,453 | 290.43M → 286.52M | first statuses appear; 5,059 "likely re-issued" (the key fields were re-keyed) |
| 2015 | 2014-12-17 → 2015-03-23 | 6,453 → 6,537 | +0.21M | 93 pending→cleared |
| 2015 | 2015-03-23 → 2015-10-29 | 6,537 → 6,643 | −0.02M | 203 pending→cleared |
| 2015 | 2015-10-29 → 2016-12-21 | 6,643 → 6,650 | +0.02M | 64 pending→cleared |
| 2015 | 2016-12-21 → ours | 6,650 → 6,650 | equal | 34 pending→cleared; 28 rows swapped |
| 2016 | 2016-12-22 → ours | 7,791 → 7,797 | +360 | 22 pending→cleared |
| 2017 | 2016-12-22 → 2017-06-13 | 8,252 → 6,688 | 353.53M → 352.17M | −1,874 / +310 rows; 160 cleared→**pending** |
| 2017 | 2017-06-13 → ours | 6,688 → 8,671 | 352.17M → 353.50M | +2,522 / −539 rows; 362 pending→cleared |

What this shows:
- **Clearance is a process you can watch.** FY2015 started as an all-blank status column
  (October 2014, five months into the fiscal year) and drained Pending over two years.
- **The June 2017 FY2017 file is a different cut, not a later state.** It has 1,564 fewer rows
  and almost the same total, with whole initiatives thinned out (Food Pantries −240, Cultural
  Immigrant −170, DoVE −164, NYC Cleanup −150, Parks Equity −147). **Checked: these are lump
  rows,** the same treatment as FY2013. Food Pantries goes from 241 rows ($4.0M) to one $4,000,000
  row, NYC Cleanup from 151 to one $7.8M row, and Cultural Immigrant from 171 rows ($5.10M) to one
  $5.01M row. Our current FY2017 file restores the itemized rows.
- **The 2014-12 FY2015 jump** pairs only 1,091 of 6,291 rows by the composite key, and
  diff_disclosure_snapshots nominates 5,059 as "likely re-issued". Probably a re-keying of
  `program_name` or `agency` across the file. Not investigated.

Each full report (added/removed rows, transitions, nominations) is in
`2026-10-14-wayback-snapshot-diffs/`.

## The application files: a data class we do not have

| File | Rows | Status | Sum of Amount |
|---|---:|---|---:|
| `unfunded_disclosure_FY2012.xls` (2011-10) | 12,695 | all `Not Funded` | $2.63B |
| `FY2013_CM_Applications_REFORMAT.xlsx` (2016-12) | 19,236 | all `Applied` | $5.11B |
| `applied_disclosure_FY2014.xls` (2016-12) | 22,096 | all `Applied` | $4.86B |

These are discretionary funding **applications**, every request with amounts requested, not
awards. They have the same 16 columns as the disclosure files, with Source blank. They are kept
in the cache only (36 MB).

## Capital databases (for #87)

| Version | Capture | Sheet | Data rows | Columns | Money columns (sum) |
|---|---|---|---:|---|---|
| FY15 | 2014-10-25 | `DoITT` | 1,342 (1,341 + a **totals row**) | Project, Borough, District(s), Sponsors, Fiscal Year Funded, Title, Description, FY15–FY18 | FY15 465.1M · FY16 9.8M · FY17 5.0M (half of a naive column sum) |
| FY16 | 2015-09-10 | `6.25_5PM_FINAL_AMT_YES` | 1,385 (1,384 + a **totals row**) | same 7 + FY16–FY19 | FY16 500.0M · FY17 23.5M |
| FY17 | 2017-07-04 | `FINAL 06-13-16 6PM` | 1,469 | PROJECT, POLBORO, Budget Line, DISTRICTS, SPONSORS, TITLE, DESC, FY17–FY20 | FY17 514.8M · FY18 22.6M |
| FY26 | 2025-12-03 | `FY26` | 1,252 | PROJECT, BORO, BUDLINE, CD, SPONSOR, TITLE, DESC, FY26–FY29 | FY26 779.3M · FY27 22.3M · FY28 3.0M · FY29 3.0M |
| FY26 (ours, git `98f1086`) | 2026-07-15 | `FY26` | 1,252 | same | same values: content-identical to the 2025-12 capture |
| FY27 (ours) | 2026-10-12 | `FY27 CAPITAL` | 1,213 | PROJECT ID, BORO, BUDGET LINE, CD, SPONSOR, TITLE, PROJECT DESCRIPTION, FY27, FY28 | FY27 853.7M · FY28 44.0M |

Notes for #87:
- **Grain differs by era.** FY15 has about 250 distinct project IDs over 1,341 rows, one row per
  sponsor per project. FY16, FY26 and FY27 have one row per project ID (FY17: 1,437 IDs over
  1,469 rows).
- **FY15 and FY16 end in a totals row.** Its amounts equal the column totals, so naive sums
  double-count it.
- The budget-line column (`Budget Line`/`BUDLINE`/`BUDGET LINE`, e.g. `E D001`) appears from
  FY17. FY15/FY16 have `Fiscal Year Funded` instead.
- The project ID format changes: `AG D001` (FY15), `AG CN001` (FY16), `E  CN052` (FY17, a double
  space), `E CN0001` (FY26), `CC0001` (FY27).
- **Not found:** any capital database for FY18–FY25 under these names or folders.

## Parser changes (all backward compatible; `--check` reports 0 stale)

1. **A workbook with empty extra sheets.** The 2014–2015 FY2015 copies have the data sheet plus
   empty `Sheet2`/`Sheet3`. Empty sheets (no cells) are now ignored, and the name comes from
   `workbook.xml.rels`. Two sheets with data still stop the parse.
2. **Contact columns dropped by name.** `Contact Person`, `Contact Phone #` and `Contact Email`
   (only in the 2014-10-16 FY2015 copy) are skipped and noted in `header_note`. Any other unknown
   header still stops.
3. **Space as a thousands separator.** One cell, `30 000`, in the 2016-05-23 FY2014 `.xls`. Only
   strict 3-digit groups qualify (`30 00` stays not-a-number).

Tests for each: `code/test_parse_expense_disclosure.py` (last section). Each was checked to fail
with its rule removed.

## Not done (left as questions)

- The `.js` disclosure files, the `html/budget/docs/` workbooks (DOE financial reports, charter
  school data, crossing guards), the terms-and-conditions PDFs, and the agency reports under
  `2021/`–`2026/` uploads (NYPD overtime, DoITT/OTI capital, BQE plan, and others): listed by CDX,
  not downloaded.
- No CDX query outside `council.nyc.gov/budget/`, `/html/budget/`, `/downloads/excel/` and the
  host-wide name filters `funded_disclosure` and `Capital Database`. There may be other names
  (e.g. `Schedule-C`, `expense_funding`).
