# Council capital (structured sources only)

**Report generated:** 2026-10-14 · **Data current as of:** Council workbooks as captured or
downloaded (FY2015 2014-10-25, FY2016 2015-09-10, FY2017 2017-07-04, FY2026 2025-12-03,
FY2027 2026-10-12); NYC Open Data pulled 2026-10-14 (t474-a92g rows last updated 2025-12-17;
46m8-77gv 2026-07-13; 2cmn-uidm 2026-09-28). GitHub #89 A6, A7.

Built by `code/build_capital_council.py` (`--write`, `--check`); audited by
`code/audit_capital.py` ([`CAPITAL-AUDIT.md`](CAPITAL-AUDIT.md)). No PDF-derived data: the
older `data/fyNN/capital/` files come from the Section 254 PDFs, are a separate dataset, and are retired in 2.0 (kept for history, not served). This dataset is served by `@betanyc/nyc-budget-mcp` 2.0 (`search_council_capital`, `compare_capital_to_omb`).
Column definitions: [`DATA-DICTIONARY.md`](../../DATA-DICTIONARY.md) § `data/capital/`.

## Files

| File | What it is |
|---|---|
| `council_capital_awards.csv` | The Council's capital designations: one row per (record, fiscal-year column) with a non-zero amount. FY2015–FY2017, FY2019–FY2027. |
| `omb_capital_budget_council_lines.csv` | OMB's Capital Budget (`46m8-77gv`), every release FY2019–FY2027, Council-series budget lines only, whole dollars. |
| `omb_commitment_plan_council_lines.csv` | OMB's Capital Commitment Plan (`2cmn-uidm`), every release April 2016–September 2026, Council-series lines only, **thousands of dollars**. |
| `council_vs_omb_by_budget_line.csv` | Per report year and budget line: the Council table vs OMB's adopted release, first and second year. |
| [`RECONCILIATION.md`](RECONCILIATION.md) | Summary, the FY2026 workbook vs t474 diff, every stripped or flagged row. |
| [`CAPITAL-AUDIT.md`](CAPITAL-AUDIT.md) | Independent re-reading of every source. |

## Which source each year comes from

| Report year | Source | Why |
|---|---|---|
| FY2015, FY2016, FY2017 | Council workbook, Internet Archive capture (`source/wayback-council/`) | The Council's own file. |
| FY2018 | **none** | No workbook was found, and t474-a92g starts at FY2019. A gap. |
| FY2019–FY2025 | NYC Open Data `t474-a92g` (published by the Council) | No workbook found for these years. |
| FY2026 | Council workbook (RnD site, captured 2025-12-03) | Preferred over t474; the two are diffed (RECONCILIATION §4). |
| FY2027 | Council workbook (RnD site, 2026-10-12) | t474 has no FY2027 yet. |

## How to read it

- **The budget line is the only key shared with OMB.** Council project IDs (`CC0001`,
  `E CN0001`) appear in no OMB dataset (the Council's own dictionary says the ID "does not link
  to the Financial Management System IDs"). Answers are exact **by budget line**. No row here is
  linked to a contract or an FMS project; any project-level link would be "matched by budget
  line and title" and is not built.
- **`report_year` vs `amount_fy`.** A workbook lists the report year and out-years in columns
  (FY27, FY28); t474 lists out-years as separate rows. Both become one row per amount, with the
  fiscal year in `amount_fy`. A year's designations are the rows with `amount_fy = report_year`.
- **Sums are this repo's arithmetic.** Only FY2015 and FY2016 print totals (their last row),
  and the kept rows equal them exactly (audit K2).
- **The commitment plan is in thousands**, as OMB publishes it; the capital budget in dollars.

## Codes

From the Council's own data dictionary for t474-a92g
(`source/open-data-t474-a92g/City_Council_Capital_Budget_Data_Dictionary.xlsx`). It documents
the Open Data table; that the RnD workbooks use the same codes is **likely but unconfirmed**.

| Code | Meaning per the Council's dictionary | Seen |
|---|---|---|
| ID type `CN` / `NC` | City projects / Non-City projects | FY2016–FY2026 |
| ID type `TA`, `RR` | Technical Adjustment; "analogous to TA" | FY2017, FY2023 |
| CD `00` | Speaker | all years |
| CD `88`–`98` | caucuses and delegations (88 Progressive, 89 Jewish, 90 LGBT, 91 Bronx, 92 Brooklyn, 93 Manhattan, 94 Queens, 95 Staten Island, 96 Citywide, 97 Black, Latino and Asian, 98 Women's) | all years |
| CD `99` | Technical Adjustments | FY2015, FY2025–FY2027 |
| Borough `C, K, M, Q, R, X` | Citywide, Brooklyn, Manhattan, Queens, Staten Island, Bronx | |

**Meaning unconfirmed** (not in the dictionary; to ask Council Finance, #89 B9): borough `A`
(FY2015 1, FY2016 4, FY2017 6, t474 45, FY2027 1 records); CD `80` with sponsor "Admin" (one
FY2027 record, `HL DN164`, $371,000); ID prefix `CC` (every FY2027 record; the printed FY2027
PDF shows agency + `CC`, so the workbook may strip the agency); ID type `PN` (FY2016, 16 records);
lower-case boroughs `k`, `x` (FY2016) and CD `1696` (FY2015, one record), kept as published.

## Known problems, kept visible

- **t474's `council_district` lost its lists.** Open Data typed the column as a number, so a
  comma list such as "22, 25, 29, 30, …" became one integer (`22252930459497004226`). Use
  `sponsor` for t474 years; the workbooks' `council_district` is the published text.
- **5 t474 records are broken across rows** (12 rows): their first rows are kept with a blank
  amount, `row_flag = split_record_amount_unknown`; the spilled fragments are listed in
  RECONCILIATION §2, not used. The FY2026 one (`P CN1606`, $2,000,000) is proven by the
  Council's FY2026 workbook; the FY2020, FY2022 and FY2023 ones cannot be, so those years'
  totals omit them.
- **t474's `title` names the organization in many FY2019 rows** and the project from FY2020
  (e.g. FY2019 `VOLUNTEERS OF AMERICA` / description `CLARKE PLACE SENIOR RESIDENCE`).
  Observed, not measured at scale.
- **FY2015's "Project" column holds budget lines**, and FY2015 has no project ID. FY2016 has
  project IDs and no budget line, so FY2016 cannot be reconciled by line.
- **2cmn-uidm carries one row with no release, line or year** whose amounts are the size of
  grand totals; stripped and listed.

## Terms of use

NYC Open Data rows are covered by the NYC Open Data Terms of Use
(<https://opendata.cityofnewyork.us/overview/#termsofuse>); use and redistribution here
confirmed by Noel Hidalgo, 2026-10-14. Council workbooks: © The City of New York, official
publications reproduced as public records, as in the rest of `source/`.
