# FY2022 PDF review: capital §254 supporting detail and Terms & Conditions

**Report generated:** 2026-10-21 22:50 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** the PDFs in `source/FY22/` (sha256 below) and `data/capital/council_capital_awards.csv`
at `ced4a68` (its FY2022 rows come from NYC Open Data `t474-a92g`, published by the Council; no Council
workbook was found for FY2022, `data/capital/README.md`).
**Status:** review build for GitHub #107 (epic #101). Nothing in `data/` was changed by this folder; the
stacked promotion PR writes `data/fy22/pdf/`.

The FY2022 twin of [`../2026-10-21-fy23-capital-terms-review/`](../2026-10-21-fy23-capital-terms-review/README.md),
made with the **same two scripts** and a new per-year config. Every number here was printed by those
scripts on 2026-10-21. Schedule C and the transparency resolutions are separate reviews.

## What is here

| File | What it is |
|---|---|
| [`REVIEW.md`](REVIEW.md) | **For Noel.** The flagged rows, critical first, then by dollars, with page numbers and what to decide |
| [`ISSUE-LOG-DRAFT.md`](ISSUE-LOG-DRAFT.md) | Draft #107 issue-log comments, one per problem, and the proposed DATA-ANOMALIES entry. Not posted |
| `data/fy22_capital_sd_projects.csv` | Parts I and II: 1,641 rows (1,462 + 179), raw and clean side by side, page and bbox |
| `data/fy22_capital_sd_totals.csv` | All 34 printed `TOTALS FOR` lines, with the computed sums and `OK` / `FAIL` |
| `data/fy22_capital_sd_part3.csv`, `…_part3_orgs.csv` | Part III: 99 organizations, 122 budget-line rows |
| `data/fy22_capital_sd_pages.csv` | Triage, every page |
| `data/fy22_capital_sd_checks.txt`, `…_review.csv`, `…_ink.json` | Check output and the machine review queue (161 entries: 33 `critical`, 128 `warn`) |
| `data/fy22_terms_conditions.csv` | 50 conditions: agencies, units, budget lines, dates, verbatim text, page range |
| `data/fy22_terms_units.csv` | One row per (condition, agency, unit or budget line): 128 units, 6 budget lines |
| `data/fy22_terms_fsr_table.csv` | The one ruled table (DOE Financial Status Reports, condition 21, pp.8–9): 6 rows |
| `data/fy22_terms_pages.csv`, `…_checks.txt`, `…_review.csv` | Triage, checks, review queue (26 entries, all `warn`) |
| `data/fy22_*_review_decisions.csv` | Empty decisions files (header only) |

Review CSV columns are the FY2024 ones (the FY columns are named for this year, as every year's are).

## The code

| File | Change |
|---|---|
| [`code/review_capital_sd.py`](../../code/review_capital_sd.py) | Two additions. **Config `extra_sub_ids`:** FY2022 prints ID numbers that are not two letters and digits (`AG TANC1`, `PW KBP01`, `PW MBP01`); each is listed in full in the config, and nothing else changes (default: matches nothing). Before this, those lines were read as part of the row above and C1 caught it. **Amounts like `($72,000)`:** Part III p.86 prints a negative organization total with the `$` inside the brackets; `AMOUNT_RE` now reads it (`money()` already did). Everything else is config, reusing the FY2023 switches (`bold_fonts`, `part3_amount_x1_tol`, `workbook_mojibake = "utf-8"`, `wb_pick_by_amount`, `c7_hairline_pt`, `ink_cover_image_pages`, `flag_id_series`) |
| [`code/review_terms.py`](../../code/review_terms.py) | No change. FY2022 is unnumbered like FY2023 and FY2024; it prints no page furniture at all (config: a pattern that matches nothing) |
| `config/capital_sd/fy2022.toml`, `config/terms/fy2022.toml` | New |
| [`code/test_review_fy22_capital_terms.py`](../../code/test_review_fy22_capital_terms.py) | 9 FY2022 tests, golden rows read off the rendered pages |

**FY2023–FY2027 output is byte-identical.** All five years' research files were rebuilt with this code
(both scripts) and `git status` shows no change to any of them. A second FY2022 run gives the same files.

## Results

### Capital supporting detail (92 pp., sha256 `040dfc52…611e`)

`FY22-Sec254-Capital-Supporting-Detail-Book.pdf`. Not encrypted; no page has a /Rotate; all 792 × 612.

**Page map** (all 92 pages agree). p.1 cover (the City seal, two images) · p.2 contents · p.3 divider ·
**pp.4–71 Part I** ("Page 1 of 68") · **p.72 summary** · p.73 divider · **pp.74–82 Part II** · p.83
divider · **pp.84–92 Part III** (unnamed `CIDFont+F1/F3` fonts, as FY2023). Header `PROJECT ID`.

| Check | Result |
|---|---|
| Rows | Part I 1,462; Part II 179; Part III 99 organizations / 122 budget-line rows |
| C1 every `TOTALS FOR` line | **34 / 34 tie** on count and all four FYs, including both `ALL` lines: Part I 1,462 projects, $704,495,000 FY2022; Part II 179, $173,172,000 FY2022 and $19,730,000 FY2023. 34 Part I rows also carry FY2023 money |
| C2 p.72 summary | Additions $704,495,000 = Part I. Additions − rescindments $29,495,000 = net $675,000,000. No list of the rescindments in this book |
| C3 Part II vs Part I | 150 rows equal a Part I row in every field; all 150 Part I rows on `DN` lines are in Part II. 29 are in Part II only: 25 `MA` / `0N` rows ($44,442,000) and **4 Borough President rows** (`HL KBP01`, `PW KBP01`, `PW KBP02` on `KN` lines, `PW MBP01` on `MN03W` at **−$72,000**): critical. Two ID numbers printed twice in Part I (`E CN884` twice on `E D001`, $500,000 each; `PV NC101` on two lines). **15 Part I `TA` rows** ($13,394,000, all borough `A`, 13 with no sponsor): one warning |
| C4 Part III | 99 / 99 organization lines equal their rows (once `($72,000)` is read, p.86); grand total = Part II in both years; 122 / 122 budget lines agree |
| C5 two reads of each word | 26,650 agree; no page edited after export; 0 disagreements |
| C6 every word in one field | 0 orphans. **28 sponsor cells print a district, not a person:** `CD 22` (10 rows) and `CD 48` (18 rows) across Parts I and II (23 Part I rows); t474 writes `Vacant 22` and `Vacant 48`, so these are seats with no member. **`P CN039` prints its borough in lower case** (`x`, p.60). All kept as printed, all critical |
| C7 rules | 119 / 119 matched; plus 99 hairlines between Part III organizations |
| C8 ink coverage | **0 uncovered regions** (the cover's seal counted as covered by config, as FY2023). Self-test: hiding `AG CN002` (p.4) gives 49 regions |
| C9 Open Data `t474-a92g`, FY2022 | **1,490 / 1,490** t474 amounts match a Part I amount, none left over. The PDF adds **`E CN673` $55,000** (p.34), the record t474 lost to a broken row; its fragment `row-y68w-ar36-igcc` carries "B:X546 S:X546", "FY22" and 55000, as the PDF prints. **t474's FY2022 total $704,440,000 + $55,000 = the PDF's $704,495,000.** Borough 1,461 / 1,462 (`P CN039`: `x` vs `X`). Sponsor 1,365 / 1,462 after decoding t474's mojibake (UTF-8 read as cp437, 32 rows); the 97 others are wording (REVIEW B3). Title 1,458 / 1,462 |
| PDF vs OMB adopted capital budget (report only) | Part I by budget line against OMB `46m8-77gv`, release 2021-07-16, FY2022 and FY2023: **149 / 149 PDF lines match** both years. OMB has one more Council-series line, `LB D109` ($2,214,000), with no Council row in the PDF or t474. The PDF closes the one line t474 missed (`E D001`, by `E CN673`) |
| vs the retired `data/fy22/capital` CSV | Same 1,641 rows and (ID, budget line) keys; **every amount equal**; borough equal except `P CN039` (it upper-cased `x`). It **dropped the printed comma after `SPEAKER` on 236 rows**, **moved a wrapped sponsor line into the title on 21 rows** and cut it from the sponsor on 18 (`PW CN072`: "… GJONAJ, GIBSON, MOYA, KOSLOWITZ" lost from the sponsor), and joined two sponsor names on 6 (`SPEAKER, BRONX DELEGATION AYALA`). 21 other title / code cells differ in how unusual codes are split. Same swapped column names as FY2023 |

### Terms & Conditions (18 pp., sha256 `39336f56…24b9`)

`FY22-Terms-and-Conditions_FINAL.pdf`. p.1 cover; pp.2–18 conditions. **No page numbers or other
furniture.** One ruled table, split over pp.8–9. Prints **no condition numbers**, like FY2023.

| Check | Result |
|---|---|
| T1 conditions | 50, numbered here in book order; 50 paragraphs open "As a condition" at the left margin |
| T2 unit and budget-line lines | 134 / 134 placed (128 units, 6 budget lines). Two agency lines print no proper code: **#26 `Department of Education (40)`** (two digits; kept in the name, code blank) and #28's `Department of Housing Preservation and Development` (no code). #28 names ten agencies |
| T3 body names the heading's units | 48 / 50. #14 names "budget lines E2364 and E2365" (no hyphen; T3 reads `XX-nnnn`); #33 wraps `HD-` / `0009` across a line end. Both are the check's limits; the texts are right |
| T4 characters | 0 outside a condition or the table |
| T5 FSR table | both lattices agree on every separator on p.8 (5 x, 7 y) and p.9 (5 x, 2 y); 28 / 28 cells identical. **The month column is out of order as printed:** SEPTEMBER 2022, OCTOBER 2022, DECEMBER 2022, FEBRUARY 2022, MARCH 2021, MAY 2022 (`families/transparency-and-terms.md` noted it) |
| T6 ink | 0 uncovered regions |
| T7 vs the retired `data/fy22/terms` CSV | Both have 50 rows, but not the same 50: the old file **lost #26** (`Department of Education (40)`, folding it into #25) and **split #28** (its ten agencies) into two rows, so its #26–#28 do not line up; from #29 on they agree again. 43 texts equal. It also put capital budget lines into `units`, the FSR table into #21's text, and dropped printed hyphens and dashes (`non-functioning`, `self-placement`, `HD-0009`, "meals per day - for") |

## What FY2022 does that FY2023 does not

- **ID numbers outside the usual shape:** `TANC1`–`TANC3`, `KBP01`, `KBP02`, `MBP01`.
- **Borough President rows** in Part II only (`KN` / `MN` lines), one of them negative (−$72,000), and a
  Part III organization total printed `($72,000)`.
- **Printed vacancies as sponsors** (`CD 22`, `CD 48`) and one lower-case borough.
- **`TA` IDs** (15, all borough `A`) where FY2023 had `RR`.
- **An ID printed twice on one line with one amount** (`E CN884`, $500,000 each, two different schools):
  no join on (ID, line, amount) can tell them apart.
- **The PDF misspells a member** on 25 Part I rows: `AMPREY-SAMUEL` (t474 and the Council: Ampry-Samuel).
- T&C: no page furniture at all; a table over two pages; a two-digit agency code.

## How to redo it

```
.venv/bin/python code/review_capital_sd.py --fy 2022          # --no-ink skips C7/C8
.venv/bin/python code/review_capital_sd.py --fy 2022 --selftest-ink --out /tmp/x   # C8 must fire on p.4
.venv/bin/python code/review_terms.py --fy 2022
.venv/bin/python -m pytest code/test_review_fy22_capital_terms.py
```

Same environment as FY2023 (pdfplumber 0.11.10, pypdfium2 5.14.0, Python 3.14.8). The comparisons with
the retired capital CSV and with OMB by budget line were run ad hoc; their numbers are above.

## Not in scope: the Resolution A book

`source/FY22/FY22-Sec254-Capital-ResoA-Book.pdf` (78 pp., sha256 `0add1c70…9f27`) is the Resolution A
family. Not encrypted; 4 pages carry a /Rotate (pp.75–78, per `data/pdf_condition.csv`), 74 are
landscape; tier B, text layer present. No retired parse of it exists in `data/fy22/capital/`.
**Recommendation:** leave it for one Resolution A pass across FY2016–FY2025 (`families/capital.md` R2),
checked against OMB; its value here is the list behind the $29,495,000 of rescindments (p.72).

## Not done

- **OCR audit (PLAN stage 10).** Not run: both PDFs are born-digital with 0 uncovered ink.
- **DATA-ANOMALIES** and **`data/capital/`** are not edited. The proposed entry is below.
- Suggested decisions (`code/build_review_suggestions.py`) and `mcp/scripts/pdf-families.mjs` do not
  list FY2022 yet (recipe Step 6, the integrator's).

## Proposed DATA-ANOMALIES entry

Not applied (parallel sessions edit that file; the integrator numbers it):

> **§NN. FY2022 capital and T&C, re-read from the PDFs (GitHub #107).** `research/2026-10-21-fy22-capital-terms-review/`.
> Capital: 34 / 34 printed totals tie; Part I equals NYC Open Data `t474-a92g` on all 1,490 of its
> FY2022 amounts and adds the one t474 lost to a broken record (`E CN673`, $55,000), so t474's
> $704,440,000 becomes the PDF's $704,495,000; all 149 PDF budget lines equal OMB's July 2021 adopted
> release. The PDF prints IDs outside the usual shape (`TANC1`, `KBP01`, `MBP01`), 4 Borough President
> rows in Part II only (one −$72,000), 28 sponsor cells that name a vacant district (`CD 22`, `CD 48`),
> a lower-case borough (`P CN039`), and `AMPREY-SAMUEL` for Ampry-Samuel (25 rows). The retired capital
> CSV drops the comma after `SPEAKER` (236 rows) and moves wrapped sponsors into titles (21). T&C: no
> printed numbers or page furniture; 50 conditions in book order; the retired CSV lost condition 26
> (`Department of Education (40)`) and split 28, so its 26–28 are misaligned; the FSR table's months are
> out of order as printed.
