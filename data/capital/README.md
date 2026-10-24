# Council capital (structured sources only)

**Report generated:** 2026-10-14 · **Data current as of:** Council workbooks as captured or
downloaded (FY2015 2014-10-25, FY2016 2015-09-10, FY2017 2017-07-04, FY2026 2025-12-03,
FY2027 2026-10-12); NYC Open Data pulled 2026-10-14 (t474-a92g rows last updated 2025-12-17;
46m8-77gv 2026-07-13; 2cmn-uidm 2026-09-28). GitHub #89 A6, A7.

Built by `code/build_capital_council.py` (`--write`, `--check`); audited by
`code/audit_capital.py` ([`CAPITAL-AUDIT.md`](CAPITAL-AUDIT.md)). No PDF-derived data: the
older `data/fyNN/capital/` files (under `data/retired/` for the years redone) come from the Section 254 PDFs, are a separate dataset, and are retired in 2.0 (kept for history, not served). This dataset is served by `@betanyc/nyc-budget-mcp` 2.0 (`search_council_capital`, `compare_capital_to_omb`).
Column definitions: [`DATA-DICTIONARY.md`](../../DATA-DICTIONARY.md) § `data/capital/`.

## Files

| File | What it is |
|---|---|
| `council_capital_awards.csv` | The Council's capital designations: one row per (record, fiscal-year column) with a non-zero amount, except that a record whose amounts are all zero is kept as one $0 row (FY2016 rows 573, `E CN679`, and 715, `E CN845`; CAPITAL-AUDIT K1). FY2015–FY2017, FY2019–FY2027. |
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
- **Accented names are garbled in t474, as published** (#199). Open Data shows `OssΘ` or
  `Oss├⌐` for Ossé, `Avil├⌐s` for Avilés, `Cab├ín` for Cabán, `FA├çADE` for FAÇADE: text
  decoded with the wrong character set before it was posted. FY2025 is Windows-1252 read as
  code page 437 (`OssΘ`, `Cabßn`, `CAF╔`); FY2019–FY2024 and FY2026 are UTF-8 read as code
  page 437 (`Oss├⌐`; `┬á` is a non-breaking space). Accented sponsors appear from FY2023 (rows here:
  FY2023 71, FY2024 78, FY2025 49); FY2019–FY2022 have it in titles and descriptions only. A few
  words (`FA╬ñADE`) do not come back in one step. This table keeps t474's text as published;
  the capital PDF reviews decode it only to compare (`workbook_mojibake` in
  `config/capital_sd/`) and write nothing back. Compare names after decoding:
  `s.encode("cp437").decode("cp1252")` for FY2025, `.decode("utf-8")` for the others. The FY2026
  and FY2027 workbooks print the accents correctly (t474's FY2026 rows are garbled; see
  `data/open_data/README.md`). A few FY2015–FY2017 workbook titles show the reverse, code page
  437 read as Windows-1252 (`CAF‚` for CAFé, `FA‡ADE` for FAçADE).
- **`project_id` is not a key, even with its agency code** (#208). Within one report year the
  same full ID names two different projects, and the §254 PDFs print them the same way:
  FY2019 6 (`LB CN001`–`LB CN006`, each once on `LN D008`, the New York Public Library, and once
  on `LB D104` or `HN D300`), FY2020 2 (`P CN967` on `P D019` and `PV DN01L`; `TF CN90` twice on
  `TF D005` at $200,000, two projects), FY2022 2 (`E CN884` twice on `E D001` at $500,000, two
  schools; `PV NC101` on `PV D235` and `PW DN725`), FY2025 6 (`E CN810`, `ED NC128`,
  `HN CN018`, `HN CN020`, `HN CN021`, `HO CN019`). The workbooks do it too: FY2017 32 IDs
  (17 of them `E CN755`–`E CN776`), FY2026 `HN CN1451` (its $125,000 row is `HN CN0092` in the
  FY2026 PDF). And one ID number is used by different agencies, so never match on the number
  alone: FY2023 `HD NC040` / `HR NC040` on `HD D020`, `HA CN001` / `P CN001` on `HA D001`. Key a
  record on (report year, project ID, budget line, `amount_fy`), and on `source_row` where that
  repeats.
- **The PDFs and OMB still differ** after the PDF adds the records t474 broke across rows (#208,
  report only): FY2020 OMB $7,353,000 higher on 11 lines, FY2023 `E D001` $5,400,000 higher.
  Details in RECONCILIATION §3.

## Terms of use

NYC Open Data rows are covered by the NYC Open Data Terms of Use
(<https://opendata.cityofnewyork.us/overview/#termsofuse>); use and redistribution here
confirmed by Noel Hidalgo, 2026-10-14. Council workbooks: © The City of New York, official
publications reproduced as public records, as in the rest of `source/`.
