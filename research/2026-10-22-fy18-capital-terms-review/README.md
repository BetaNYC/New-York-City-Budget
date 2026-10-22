# FY2018 PDF review: capital §254 supporting detail and Terms & Conditions

**Report generated:** 2026-10-22 02:20 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** the two PDFs in `source/FY18/` (sha256 below) and the retired
`data/fy18/terms/fy18_terms_and_conditions.csv` at `91c76fe`.
**Status:** review build for GitHub #111 (epic #101). Nothing in `data/` was changed by this folder; the
stacked promotion PR writes `data/fy18/pdf/capital_sd/` and `data/fy18/pdf/terms/`.

The FY2018 twin of [`../2026-10-21-fy22-capital-terms-review/`](../2026-10-21-fy22-capital-terms-review/README.md),
made with the **same two scripts** and two new per-year configs. Every number here was printed by those
scripts on 2026-10-22. Schedule C and the transparency resolutions are separate reviews.

**FY2018 capital has no outside check.** There is no Council workbook for FY2018 and NYC Open Data
`t474-a92g` starts at FY2019 (`data/capital/README.md`; DATA-ANOMALIES §26), and there is no retired
`data/fy18/capital` CSV. **The book's own printed totals are the only check on its amounts**: 35 `TOTALS
FOR` lines, plus Part II against Part I and Part III against Part II, which are three printings of the same
money. All of them tie.

## What is here

| File | What it is |
|---|---|
| [`REVIEW.md`](REVIEW.md) | **For Noel.** The flagged items, critical first, then by dollars, with page numbers and what to decide |
| [`ISSUE-LOG-DRAFT.md`](ISSUE-LOG-DRAFT.md) | Draft #111 issue-log comments, one per problem. Not posted |
| `data/fy18_capital_sd_projects.csv` | Parts I and II: 1,718 rows (1,485 + 233), raw and clean side by side, page and bbox |
| `data/fy18_capital_sd_totals.csv` | All 35 printed `TOTALS FOR` lines, with the computed sums and `OK` / `FAIL` |
| `data/fy18_capital_sd_part3.csv`, `…_part3_orgs.csv` | Part III: 138 organizations, 170 budget-line rows |
| `data/fy18_capital_sd_pages.csv`, `…_checks.txt`, `…_review.csv`, `…_ink.json` | Triage, checks, review queue (50 entries: 3 `critical`, 47 `warn`) |
| `data/fy18_terms_conditions.csv` | 33 conditions: agencies, units, budget lines, dates, verbatim text, page range |
| `data/fy18_terms_units.csv` | One row per (condition, agency, unit or budget line): 71 units, 5 budget-line lines |
| `data/fy18_terms_fsr_table.csv` | The one ruled table (DOE Financial Status Reports, condition 14, p.15): 6 rows |
| `data/fy18_terms_pages.csv`, `…_checks.txt`, `…_review.csv` | Triage, checks, review queue (13 entries, all `warn`) |
| `data/fy18_*_review_decisions.csv` | Empty decisions files (header only) |

Review CSV columns are the FY2020 (capital) and FY2021 (T&C) ones.

## The code

| File | Change |
|---|---|
| [`code/review_capital_sd.py`](../../code/review_capital_sd.py) | Two config switches, off by default. **`no_comparison_source`:** C9 says "no comparison source for FY2018" instead of listing all 1,485 rows as missing from an empty set. **`sponsor_digit_ok`:** a sponsor printed as a seat (`DISTRICT 28`, 15 rows) is a warning, not the critical "number in the sponsor cell" (which is there to catch a misread page number). The "no summary page" path added for FY2019 is reused. Everything else is config (`part3_amount_x1_tol`, `c7_hairline_pt`) |
| [`code/review_terms.py`](../../code/review_terms.py) | Five config switches, off by default. **`opening_phrases`:** T1 counts the paragraphs that open a condition; FY2018 opens 6 of 33 with other words ("Where the Commissioner", "No later than …"). **`all_lines_headings`:** "All Project Lines – All Projects" under "Capital Budget" is a budget-line heading, not a second agency. **`fsr_table.header_starts`, `columns_3_4`:** FY2018's table header is in mixed case and prints "Anticipated Meeting Date" before "Issue Date". **`fsr_table.overflow_below_pt`:** the last cell's word "Summary" is printed 1.7 pt below the table's bottom rule; it is read into that row, with a warning |
| `config/capital_sd/fy2018.toml`, `config/terms/fy2018.toml` | New |
| [`code/test_review_fy18_capital_terms.py`](../../code/test_review_fy18_capital_terms.py) | 4 FY2018 tests, golden rows read off the rendered pages |

**FY2019–FY2027 output is byte-identical.** All research files of every reviewed year (capital FY2019,
FY2020, FY2022–FY2027; T&C FY2021–FY2027) were rebuilt with this code and `git status` shows no change.
A second FY2018 run of each script gives the same files.

## Results

### Capital supporting detail (96 pp., sha256 `22c3bef3…0848`)

`FY18-Sec254-Capital-ResoA-M499-Res1534-Res1535.pdf`. **Despite the name it is the supporting detail,
Parts I–III**, not a Resolution A book. Acrobat Distiller 17.0 from PScript5 (Author "NYC OMB").
**AES-128 encrypted (V4 R4, /P −1324) with an empty user password:** it opens and its text extracts.
Only the cover carries /Rotate 90.

**Page map** (all 96 pages agree). p.1 cover · p.2 contents · p.3 divider · **pp.4–70 Part I** ("Page 1 of
67" …) · p.71 divider · **pp.72–83 Part II** · p.84 divider · **pp.85–96 Part III**. Header `PROJECT ID …
SPONSOR`. **No summary page** (no additions / rescindments / net). Fonts: Helvetica, Helvetica-Bold,
"Times New Roman,Bold" (the "I." mark); none typed in later.

| Check | Result |
|---|---|
| Rows | Part I **1,485**, Part II **233** (1,718; as `families/capital.md` §3.1 counted) |
| C1 every `TOTALS FOR` line | **35 / 35 tie** on count and all four FYs (23 agencies + ALL in Part I, 10 + ALL in Part II). **`TOTALS FOR ALL (1485 PROJECTS)`, p.70: $575,000,000 FY2018, $28,000,000 FY2019, $12,000,000 FY2020, $0 FY2021.** Part II ALL (233): $133,995,000 / $10,500,000 / $7,500,000 / $0 |
| C2 summary | **None printed** |
| C3 Part II vs Part I | 178 Part II rows equal a Part I row in every field; every one of Part I's 178 `DN` (non-city) rows is in Part II. 55 Part II rows are not in Part I ($33,282,000): **52 `MA` IDs on `0N` lines** ($32,189,000, no sponsor; the FY2027 pattern) and **3 `TA` rows** (`AG TA001` $500,000, `HH TA001` $693,000, `HH TA003` −$100,000; critical, below) |
| C4 Part III | 138 / 138 organization lines equal their rows; `TOTAL NON-CITY PROJECT ALLOCATIONS` $133,995,000 / $10,500,000 = its rows = Part II's `TOTALS FOR ALL`; by budget line 170 / 170 equal Part II |
| C5 two reads of each word | 25,746 agree; 0 disagree; 0 out of row order |
| C6 every word in one field | 0 orphans. 15 Queens school rows print the sponsor **`DISTRICT 28`** (a seat, not a member; `E CN765`–`E CN779`, pp.43–44, $5,000,000). One row on borough `A` (`HN CN014` CUNY-WIDE COMMUNITY COLLEGES, p.5) |
| C7 rules | 128 / 128 matched; 138 Part III hairlines (0.04–0.1 pt, grey) are below pixel size and counted, as FY2022 |
| C8 ink coverage | **0 uncovered regions** on 96 pages. Self-test: hiding `AG CN002` (p.4) gives 75 regions |
| C9 | **Not run: no comparison source for FY2018.** The printed totals above are the only check on the amounts |

### Terms & Conditions (34 pp., sha256 `c14da9b3…05c2`)

`FY18-Terms-and-Conditions.pdf`. Microsoft Word 2016; not encrypted; no /Rotate; all 612 × 792. p.1 cover;
pp.2–34 conditions, **one per page**, except that an agency heading can sit at the foot of the page
before its units (pp.24, 25, 30). **No page numbers or other furniture; no condition numbers.** One ruled
table, on p.15.

| Check | Result |
|---|---|
| T1 conditions | **33**, numbered here in book order. 33 paragraphs open a condition at the left margin: 27 "As a condition", and 6 with other words (config `opening_phrases`) |
| T2 unit and budget-line lines | **74 / 74 placed** (71 units, 3 `Budget Line` lines), plus 2 "All Project Lines – All Projects" lines (#2, #3), kept as printed in `budget_lines` |
| T3 body names the heading's units | 32 / 33. #17 names "budget line E2360" (no hyphen; T3 reads `XX-nnnn`); the check's limit, as FY2021 #12 |
| T4 characters | 0 outside a condition or the table |
| T5 FSR table | both lattices agree on every separator (5 x, 8 y); 28 / 28 cells identical. **"Summary", the end of the last row's report content, is printed 1.7 pt below the table's bottom rule**; read into that row (warn). **Columns 3 and 4 are printed "Anticipated Meeting Date", "Issue Date"**, the other way round from FY2021–FY2027; read as printed. Every date is "TBD" |
| T6 ink | 0 uncovered regions |
| T7 vs the retired `data/fy18/terms` CSV | Same 33 conditions in the same order; first agency equal on all 33; 30 texts equal. The old file folded the FSR table into #14's text and dropped two printed hyphens at line ends (#15 "non-Department", #32 "direct-managed"); it put budget-line headings into `units` (#2–#5, #17). 8 mid-word splits in the old text, 0 in the new |

**Capital conditions:** #2 and #3 (all project lines; p.3 the project-location notice, p.4 the Charter and
FMS milestones), #4 and #5 (`HA-0001`, NYCHA: the Mayor's Action Plan, and sidewalk sheds), and #17,
which names **Department of Education (040)** and **School Construction Authority (040)** with
`E2360 – All Projects` (p.18; SCA printed with DOE's code, kept as printed, as FY2021 #12).

## What FY2018 does that later years do not

- **Capital: no summary page, and no structured source at all.** Totals are the only outside check.
- **Capital: `DISTRICT 28`** as a sponsor on 15 rows.
- **T&C: one condition per page**, six conditions that do not open "As a condition", "All Project Lines",
  a table header in mixed case with two columns swapped, and text below the table's last rule.

## How to redo it

```
.venv/bin/python code/review_capital_sd.py --fy 2018          # --no-ink skips C7/C8
.venv/bin/python code/review_capital_sd.py --fy 2018 --selftest-ink --out /tmp/x   # C8 must fire on p.4
.venv/bin/python code/review_terms.py --fy 2018               # --no-ink skips T6
.venv/bin/python -m pytest code/test_review_fy18_capital_terms.py
```

Same environment as FY2020 (pdfplumber 0.11.10, pypdfium2 5.14.0, opencv-python-headless 4.14.0.94,
numpy 2.5.4, Python 3.14.8).

## What the checks cannot prove

- **Capital text fields have no second source.** Totals check counts and amounts. A wrong title, borough,
  budget line or sponsor passes them. C5 (two independent reads, 0 disagreements), C6 and C8 (no word or
  ink left over) are what stand behind the text; Part II re-prints 178 Part I rows and every field agrees.
- **The 52 `MA` and 3 `TA` Part II rows** cannot be checked against anything but Part II's own totals.

## Not done

- **OCR audit (PLAN stage 10).** Not run: both PDFs are born-digital with 0 uncovered ink.
- **Checking FY2018's budget lines against OMB.** `data/capital/omb_capital_budget_council_lines.csv`
  starts at FY2019; `families/capital.md` reports all 191 Part I lines in OMB's 2017-11-06 commitment
  plan, which is not in the repo. Not repeated here.
- **DATA-ANOMALIES** and **`data/capital/`** are not edited. Whether a PDF-derived FY2018 may enter
  `data/capital/` is a policy question (REVIEW D1). The proposed entry is below.
- Suggested decisions (`code/build_review_suggestions.py`) and `mcp/scripts/pdf-families.mjs` do not list
  FY2018 yet (recipe Step 6, the integrator's).

## Proposed DATA-ANOMALIES entry

Not applied (parallel sessions edit that file; the integrator numbers it):

> **§NN. FY2018 capital supporting detail and Terms & Conditions, re-read from the PDFs (GitHub #111).**
> `research/2026-10-22-fy18-capital-terms-review/`. The capital book, filed as
> `FY18-Sec254-Capital-ResoA-…pdf`, is the §254 supporting detail, Parts I–III (encrypted with an empty
> password, no summary page). It is the only source for FY2018 Council capital (§26): 1,485 Part I
> projects, $575,000,000 FY2018. All 35 printed `TOTALS FOR` lines tie on count and all four years; Part
> II and Part III tie to each other and to Part I. There is no outside source to compare with. 15 rows
> name the sponsor `DISTRICT 28`; Part II adds 52 `MA` and 3 `TA` rows not in Part I. The T&C have 33
> unnumbered conditions, one a page, all heading lines placed; the retired `data/fy18/terms` CSV has the
> same 33 but folds the FSR table into #14's text, drops two line-end hyphens and files budget-line
> headings as units.
