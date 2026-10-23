# `data/retired/` — the old PDF-parser CSVs, for years already redone

**What these are.** The CSVs the first PDF parsers (`code/parse_schedule_c*.py`, `parse_terms*.py`,
`parse_capital*.py`, `parse_transparency_reso.py`) wrote for each fiscal year, from the Council's
adopted-budget PDFs. Each file keeps its old path under this folder:
`data/fy26/schedule_c/fy26_schedule_c_awards.csv` is now
`data/retired/fy26/schedule_c/fy26_schedule_c_awards.csv`. Nothing was edited or deleted; the
move is a pure rename (#218), so `git log --follow` shows each file's history.

**Why they are retired.** Version 2.0 stopped serving and shipping all PDF-derived data
([DATA-ANOMALIES.md §27](../../DATA-ANOMALIES.md)): these parsers read the text layer with regular
expressions, and the checks found real errors in them (lost row boundaries, amounts on the wrong
organization, dropped rows and conditions; §20, §21 and §29–§55). Decided in #209: move each
family-year here once the new, checked process has redone it.

**Where the checked tables are.** `data/fyNN/pdf/<family>/`, one folder per family-year, listed with
its status, row count and review in [`data/pdf_years.csv`](../pdf_years.csv). Each was rebuilt from the
PDF and checked against everything the PDF prints ([`PDF-RECIPE.md`](../../PDF-RECIPE.md)); a person
reviews every flagged row before a year is `closed` and served.

## What is here

| Old folder | Fiscal years moved | Checked tables |
|---|---|---|
| `schedule_c/` | FY2018–FY2027 | `data/fyNN/pdf/schedule_c/` |
| `transparency-resolutions/` | FY2018–FY2024, FY2026 (the old parser never did FY2025) | `data/fyNN/pdf/transparency/` |
| `capital/` (§254) | FY2020, FY2022–FY2027 (no old parse of FY2018, FY2019 or FY2021) | `data/fyNN/pdf/capital_sd/` |
| `terms/` | FY2018, FY2021–FY2027 (no old parse of FY2019 or FY2020) | `data/fyNN/pdf/terms/` |

Not yet redone, so still in their old place: FY2009–FY2017 under `data/fyNN/`. They move here
year by year as each is redone.

## What still reads them

None of this is served by the MCP or the explorer (`mcp/test/no-pdf-data.test.js`). Some scripts
still read the old files, and find them here or in the old place through `code/retired_paths.py`:

- The new reviews compare against the old parse: Terms & Conditions check T7 (`config/terms/*.toml`,
  `old_csv`), the transparency "retired CSV" comparison and its **rescission-origin check**, which
  looks up the year's old Schedule C award files (`code/transreso/disclosure.py`; its open question
  is #204).
- The historical reports and roll-ups: `code/validate_data.py` (`data/QA-REPORT.md`),
  `code/audit_amounts.py`, `code/reconcile_disclosure_schedule_c.py`
  (`data/DISCLOSURE-COVERAGE.md`), `code/build_combined.py` (`data/combined/`), and the
  open-data T&C crosswalk for a year with no checked T&C table.
- The one-off repair passes of 2026-08 (`code/fix_*.py`, `code/recover_*.py`).

Older records name these files by their old path, `data/fyNN/<family>/...`: the `file` column of
`data/combined/org_name_recovery_crosswalk.csv`, `absorbed_from_file` in
`data/recovered/schedule_c_absorbed_awards.csv`, and the dated `research/` folders. For a year
listed above, the file is now under `data/retired/` at the same path.
