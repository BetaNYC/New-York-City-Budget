# Review sheet: 20 Open Data / Council near-matches to check by eye (#89 B12)

**Report generated:** 2026-10-14 (office) · **Data current as of:** Open Data `4d7f-74pe` pulled
2026-10-14 (sha256 `3d6d470b…` in `source/open-data-4d7f-74pe/MANIFEST.csv`); Council side =
the archived FY2009–FY2012 workbooks and our 2026-10-12 FY2013–FY2021 files.

File: [`review-sheet.csv`](review-sheet.csv), 20 rows. Built by
`code/build_open_data_review_sheet.py` (tests: `code/test_build_open_data_review_sheet.py`).

## What these rows are

After matching, `code/diff_open_data_disclosure.py` **nominates** pairs that look like one
designation with one thing changed. A nomination is a lead, never a match. Three classes:

| class | what is the same | what differs | all years | sampled |
|---|---|---|---:|---:|
| `grantee_differs` | amount, source, agency, council member | the organization (likely re-designated) | 160 | 7 |
| `ein_differs` | organization, amount | the EIN | 66 | 6 |
| `amount_differs` | organization, EIN | the amount | 199 | 7 |

## How the 20 were picked

Each class's nominations are sorted by (fiscal year, Open Data `:id`, Council file:row), then
drawn with `random.Random(20261014)`: 7, 6 and 7 rows. Same inputs, same 20 rows. The build stops
if the class counts above ever change. The draw is random within a class, not spread by year:
FY2013 and FY2021 have the most nominations, so they appear most.

## How to review a row

1. Read both sides: `open_data_*` and `council_*` columns. `council_side` says which Council
   file: `wayback_workbook` (FY2009–FY2012, `source/wayback-council/files/`) or
   `disclosure_2026_10_12` (our `data/fyNN/expense_disclosure/`).
2. Open the Council row: `council_source_row` is `file:row`. Open Data's row is
   `open_data_row_id` (the SODA `:id`) and `open_data_mocs_id`.
3. Put one value in `reviewer_verdict`:
   - `same` — one designation; the difference is a correction (EIN typo, renamed grantee).
   - `different` — two different designations that happen to line up.
   - `cannot_tell` — the two files do not settle it.
4. Say why in `notes`, in a few words. Name anything outside these two files you used.

Do not edit the other columns. Re-running the script overwrites the file, so copy it before
filling it in.

## What a verdict will and will not do

Verdicts tell us whether the nomination rules are sound (for example, whether `grantee_differs`
is really a re-designation). They do not change any dataset row. If several `ein_differs` rows
come back `same`, that is evidence for a later rule, decided by a person.
