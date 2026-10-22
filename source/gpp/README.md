# Budget PDFs from the City's Government Publications Portal

Copies of budget PDFs that City agencies filed with the DORIS Government Publications Portal
(GPP, `a860-gpp.nyc.gov`), downloaded on 2026-10-22. They are mostly the Office of Management and
Budget's (OMB) copies of the Council's capital "supporting detail" books, one for every year from
FY2009 to FY2027. Several of those years are missing from `source/FY*/`, or are there only in a
different version.

**Status:** not reviewed. Nothing in `data/` or the MCP reads these files yet. The review is
tracked in a GitHub issue.

## What is here

[`MANIFEST.csv`](MANIFEST.csv) lists every file downloaded, one row each, with its `status`:

| status | Count | Meaning |
|---|---:|---|
| `committed` | 21 | In `files/<gpp_id>/<label>`, byte for byte as downloaded |
| `same_as_existing` | 3 | Identical (same sha256) to a PDF already in `source/`; `same_as` names it |
| `not_committed` | 26 | OMB's other adopted-budget books for FY2026 and FY2027 (101 MB, up to 4,700 pages each). Listed so they can be fetched again from `url` |

By `kind`:

| kind | Years | Notes |
|---|---|---|
| `capital_supporting_detail` | FY2009–FY2027 (19) | "Supporting Detail for Fiscal Year NNNN Changes to the Executive Capital Budget Adopted by the City Council Pursuant to Section 254 of the City Charter". Filed by OMB; FY2016 and FY2013 match `source/` exactly |
| `capital_resolution_a` | FY2026, FY2027 | "Changes to the Executive Capital Budget Adopted by the City Council" |
| `expense_contract_resolutions` | FY2026, FY2027 | "City Council Changes As Adopted, Schedules A and B" to the expense and contract budget resolutions |
| `schedule_c` | FY2010 | The Council's own filing; identical to `source/FY10/fy_2010_sched_c_final.pdf` |
| `omb_adopted_budget_other` | FY2026, FY2027 | The rest of OMB's adopted-budget set (Budget Function Analysis, Supporting Schedules, Financial Plan and others) |

Not found on the portal: the Council's Terms and Conditions documents (only agencies' compliance
reports about them), transparency resolutions, and any Schedule C after FY2010.

## Provenance

- **Search:** the portal's catalog API, run from a real browser session (the portal blocks
  scripts outside one). Queries: `"supporting detail" "section 254"` (OMB items with a fiscal year
  in the title), plus item `sj139284d`. Item metadata: `/catalog/<gpp_id>.json`; file names:
  `/concern/file_sets/<file_set_id>.json`.
- **Download:** `/downloads/<file_set_id>`, one request about every 2.4 seconds. 50 files, all
  HTTP 200. Each file's sha256 was computed on download and checked again on disk.
- **Columns:** `gpp_id` and `item_url` identify the portal item; `file_set_id` and `url` the file;
  `label` is the file name the agency uploaded; `agency`, `date_published` and `uploaded` are the
  portal's own fields.
- **Rights:** official City publications, reproduced as public records, same terms as the rest
  of `source/`.

## Before using any of these

- The supporting-detail books here are OMB's filings. For years where `source/FY*/` has a book
  with a different sha256, compare the two before choosing one; they may be different versions.
- The FY2010 book (`2j62s602t`) has no text on its first page; check whether it is a scan.
- The process for turning a book into checked tables is in `PDF-RECIPE.md` (PR #151).
