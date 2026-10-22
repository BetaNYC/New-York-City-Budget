# FY2023 PDF review: capital §254 supporting detail and Terms & Conditions

**Report generated:** 2026-10-21 22:18 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** the PDFs in `source/FY23/` (sha256 below) and `data/capital/council_capital_awards.csv`
at `ced4a68` (its FY2023 rows come from NYC Open Data `t474-a92g`, published by the Council; no Council
workbook was found for FY2023, `data/capital/README.md`).
**Status:** review build for GitHub #106 (epic #101). Nothing in `data/` was changed by this folder; the
stacked promotion PR writes `data/fy23/pdf/`.

The FY2023 twin of [`../2026-10-21-fy24-capital-terms-review/`](../2026-10-21-fy24-capital-terms-review/README.md),
made with the **same two scripts** and a new per-year config. Every number here was printed by those
scripts on 2026-10-21. Schedule C and the transparency resolutions are separate reviews.

## What is here

| File | What it is |
|---|---|
| [`REVIEW.md`](REVIEW.md) | **For Noel.** The flagged rows, sorted by dollars, with page numbers and what to decide |
| [`ISSUE-LOG-DRAFT.md`](ISSUE-LOG-DRAFT.md) | Draft #106 issue-log comments, one per problem, and the proposed DATA-ANOMALIES entry. Not posted |
| `data/fy23_capital_sd_projects.csv` | Parts I and II: 1,547 rows (1,393 + 154), raw and clean side by side, page and bbox |
| `data/fy23_capital_sd_totals.csv` | All 32 printed `TOTALS FOR` lines, with the computed sums and `OK` / `FAIL` |
| `data/fy23_capital_sd_part3.csv`, `…_part3_orgs.csv` | Part III: 89 organizations, 115 budget-line rows |
| `data/fy23_capital_sd_pages.csv` | Triage, every page |
| `data/fy23_capital_sd_checks.txt`, `…_review.csv`, `…_ink.json` | Check output and the machine review queue (40 entries, all `warn`) |
| `data/fy23_terms_conditions.csv` | 60 conditions: agencies, units, budget lines, dates, verbatim text, page range |
| `data/fy23_terms_units.csv` | One row per (condition, agency, unit or budget line): 153 units, 5 budget lines |
| `data/fy23_terms_fsr_table.csv` | The one ruled table (DOE Financial Status Reports, condition 24, p.9): 6 rows |
| `data/fy23_terms_pages.csv`, `…_checks.txt`, `…_review.csv` | Triage, checks, review queue (15 entries, all `warn`) |
| `data/fy23_*_review_decisions.csv` | Empty decisions files (header only) |

Review CSV columns are the FY2024 ones (the FY columns are named for this year, as every year's are).

## The code

| File | Change |
|---|---|
| [`code/review_capital_sd.py`](../../code/review_capital_sd.py) | Three additions, each off unless the year's data or config asks for it. **C9:** an Open Data row with no amount (t474's `split_record_amount_unknown`; FY2023 `E CN136`) is set aside, listed with the PDF row that has its ID and budget line (`C9.workbook_no_amount`), and not joined on amount; it crashed the run before. Only FY2020, FY2022 and FY2023 have such rows. **C8:** config `ink_cover_image_pages` counts a picture's box as covered on the named pages only (FY2023 p.1: the City seal, two images), and says so in `checks.txt`. **C3:** config `flag_id_series` lists every Part I row of an ID series in one warning (`C3.id_series`; FY2023 `RR`). Everything else is config, reusing the FY2025/FY2024 switches (`bold_fonts`, `part3_amount_x1_tol`, `workbook_mojibake = "utf-8"`, `wb_pick_by_amount`, `c7_hairline_pt`) |
| [`code/review_terms.py`](../../code/review_terms.py) | No change. FY2023 is unnumbered like FY2024 (`numbered = false`, `table_pages = [9]`) |
| `config/capital_sd/fy2023.toml`, `config/terms/fy2023.toml` | New |
| [`code/test_review_fy23_capital_terms.py`](../../code/test_review_fy23_capital_terms.py) | 11 FY2023 tests, golden rows read off the rendered pages |

**FY2024, FY2025, FY2026 and FY2027 output is byte-identical.** All four years' research files were
rebuilt with this code (both scripts) and `git status` shows no change to any of them. A second FY2023
run gives the same files byte for byte (`diff -r`).

## Results

### Capital supporting detail (89 pp., sha256 `cd406f89…be42`)

`FY23-Sec254-Capital-Supporting-Detail-Book.pdf`. Not encrypted; no page has a /Rotate; all 792 × 612.

**Page map** (all 89 pages agree). p.1 cover · p.2 contents · p.3 divider · **pp.4–70 Part I**
("Page 1 of 67") · **p.71 summary** · p.72 divider · **pp.73–80 Part II** · p.81 divider ·
**pp.82–89 Part III** (a second export, unnamed `CIDFont+F1/F3` fonts, as FY2025). Header `PROJECT ID`.

| Check | Result |
|---|---|
| Rows | Part I 1,393; Part II 154; Part III 89 organizations / 115 budget-line rows |
| C1 every `TOTALS FOR` line | **32 / 32 tie** on count and all four FYs, including both `ALL` lines: Part I 1,393 projects, $879,676,000 FY2023; Part II 154, $188,160,000. 15 Part I rows also carry FY2024 money (11 Parks, 4 Fire), 4 of them FY2025 |
| C2 p.71 summary | Additions $879,676,000 = Part I. Additions − rescindments $179,676,000 = net $700,000,000. No list of the rescindments in this book |
| C3 Part II vs Part I | 115 rows equal a Part I row in every field; 39 are in Part II only, all `MA` IDs on `0N` lines ($78,861,000, no sponsor). All 115 Part I rows on `DN` lines are in Part II. No ID printed twice. **15 Part I `RR` rows** ($22,633,000, no sponsor, 4 on borough `A`): listed in one warning |
| C4 Part III | 89 / 89 organization lines equal their rows; grand total $188,160,000 = Part II; 115 / 115 budget lines agree |
| C5 two reads of each word | 25,493 agree; no page edited after export (every word in an export font); 0 disagreements |
| C6 every word in one field | 0 orphans, 0 unplaced words |
| C7 rules | 111 / 111 matched; plus 89 hairlines (0.12 pt, 50% grey) between Part III organizations, under a pixel at 300 dpi |
| C8 ink coverage | **0 uncovered regions**, once the City seal on the cover (two images, p.1) is counted as covered by config. Before that, the seal was the only uncovered ink (19 regions, all p.1). Self-test: hiding `AG NC002` (p.4) gives 66 regions |
| C9 Open Data `t474-a92g`, FY2023 | **1,411 / 1,411** t474 amounts match a Part I amount on (ID, budget line, FY, amount), none left over in t474. The PDF has one more, **`E CN136` $150,000** (p.11): t474's row for it is a broken record with no amount (RECONCILIATION §2), and its stray fragment `row-fpup_sjfd_kina` carries "B:M028 S:M028", "FY23" and 150000, which is what the PDF prints. **t474's FY2023 total $879,526,000 + $150,000 = the PDF's $879,676,000.** Borough 1,393 / 1,393. Sponsor 1,372 / 1,393 after decoding t474's mojibake (UTF-8 read as cp437, 74 rows): the 21 others are the 15 `RR` rows (PDF blank, t474 `NA`) and 6 where t474 shortens "BLACK, LATINO AND ASIAN CAUCUS" to `BLAC`. Title 1,391 / 1,393 (`HD NC011`: t474 adds "CORP."; `E CN136`: t474's broken record lacks the codes) |
| Reused ID numbers | Two ID numbers are printed by two agencies on one budget line: `HD NC040` (p.50, Cypress Hills, $4,279,000) and `HR NC040` (p.51, St. Nicks, $1,000,000) on `HD D020`; `HA CN001` ($810,000) and `P CN001` ($2,700,000), both p.48 on `HA D001`. The full IDs differ, so nothing is merged; C9 drops the agency prefix, so it compares each with the t474 row that has its amount (`wb_pick_by_amount`) |
| PDF vs OMB adopted capital budget (report only) | Summing Part I by budget line against `data/capital/council_vs_omb_by_budget_line.csv` (OMB `46m8-77gv`, release 2022-07-15, FY2023 and FY2024): **129 / 130 lines match** both years. `E D001`: PDF $224,446,000, OMB $229,846,000, t474 $224,296,000. The PDF closes t474's $150,000 gap (`E CN136`); the other $5,400,000 is OMB's and is not explained here |
| vs the retired `data/fy23/capital` CSV | Same 1,547 rows and (ID, budget line) keys; **every amount and borough equal**. It **dropped the printed comma after `SPEAKER` on 265 rows** (`SPEAKER MARTE`; p.48 prints `SPEAKER, MARTE`) and **moved a wrapped sponsor line into the title on 10 rows** (`E CN018` "… COMMUNITY SCHOOL WOMEN'S CAUCUS"). 31 other title / code cells differ in how unusual codes are split (`S:03M075`, `M363/M063`, `B: S:`): this parse keeps any code that is not `[A-Z]nnn` in the title, as printed. Same swapped column names as FY2024 |

### Terms & Conditions (19 pp., sha256 `00c491bc…ed55`)

`FY23-Terms-and-Conditions_FINAL_OMB-and-Council-Review-6.11.22.pdf`. p.1 cover; pp.2–19 conditions;
`Page N of 19` at the foot. One ruled table (p.9). Prints **no condition numbers**, like FY2024.

| Check | Result |
|---|---|
| T1 conditions | 60, numbered here in book order (**the PDF prints no numbers**); 60 paragraphs open "As a condition" at the left margin |
| T2 unit and budget-line lines | 158 / 158 placed (153 units, 5 budget lines). Every agency heading prints a code; 4 conditions sit under a bold `Capital Budget` heading (#3, #4, #5; #35 also names HPD) |
| T3 body names the heading's units | 58 / 60. #35 wraps `HD-` / `0009` across a line end, which T3 reads with a space (the check's limit; the text is right); #49 "units of appropriations 311 and 312" (plural) names only DYCD's units in the form T3 reads, NYPD's 001 follows as "unit of appropriation 001" in the next clause |
| T4 characters | 0 outside a condition, the table or page furniture |
| T5 FSR table | both lattices agree on every separator (5 x, 8 y); 28 / 28 cells identical |
| T6 ink | 0 uncovered regions |
| T7 vs the retired `data/fy23/terms` CSV | Same 60 conditions in the same order, same first agency on all 60; 55 texts equal (whitespace ignored). It put the FSR table into #24's text, put the three capital budget lines into `units` (#3, #4, #5, #35), and dropped printed hyphens and dashes (`low-barrier`, `self-placement`, `HD-0009`, "meals per day - for") |

## What FY2023 does that FY2024 does not

- **A City seal image on the cover** of the capital book: the first year whose ink check needed a picture
  counted as covered.
- **`RR` IDs** in Part I (15 rows, $22,633,000): no sponsor, 4 on borough `A`. FY2024 had `TA` IDs with
  sponsor `TECHNICAL ADJUSTMENT`. Two `RR` rows sit next to a near-twin on the same budget line
  (REVIEW A3).
- **Two ID numbers shared by two agencies on one budget line** (`HD`/`HR NC040`, `HA`/`P CN001`).
- **A broken Open Data record the PDF settles** (`E CN136`, $150,000).
- **No negative amounts**, no Part II-only row outside the `MA` / `0N` series, no post-export edits.
- T&C: every agency heading prints a code; a bold `Capital Budget` group heading; no white boxes.

## How to redo it

```
.venv/bin/python code/review_capital_sd.py --fy 2023          # --no-ink skips C7/C8
.venv/bin/python code/review_capital_sd.py --fy 2023 --selftest-ink --out /tmp/x   # C8 must fire on p.4
.venv/bin/python code/review_terms.py --fy 2023
.venv/bin/python -m pytest code/test_review_fy23_capital_terms.py
```

Same environment as FY2024 (pdfplumber 0.11.10, pypdfium2 5.14.0, Python 3.14.8). The comparisons with
the retired capital CSV and with OMB by budget line were run ad hoc (as for FY2024); their numbers are
above.

## Not in scope: the Resolution A book

`source/FY23/FY23-Sec254-Capital-ResoA-Book.pdf` (101 pp., sha256 `aaf08d1c…af3c`) is the Resolution A
family. Not encrypted; 62 pages carry a /Rotate (pp.3–64, per `data/pdf_condition.csv`), 39 are
landscape; tier B, text layer present. No retired parse of it exists in `data/fy23/capital/`.
**Recommendation:** as for FY2024 and FY2025, leave it for one Resolution A pass across FY2016–FY2025
(`families/capital.md` R2: same grammar every year), checked against OMB; its value here is the list
behind the $179,676,000 of rescindments (p.71) and the `E D001` line.

## Not done

- **OCR audit (PLAN stage 10).** Not run: both PDFs are born-digital with 0 uncovered ink.
- **DATA-ANOMALIES** and **`data/capital/`** are not edited. The proposed entry is below and in
  `ISSUE-LOG-DRAFT.md`.
- Suggested decisions (`code/build_review_suggestions.py`) and the explorer's decisions-file list
  (`mcp/scripts/pdf-families.mjs`) do not list FY2023 yet (recipe Step 6, the integrator's).

## Proposed DATA-ANOMALIES entry

Not applied (parallel sessions edit that file; the integrator numbers it):

> **§NN. FY2023 capital and T&C, re-read from the PDFs (GitHub #106).** `research/2026-10-21-fy23-capital-terms-review/`.
> Capital: 32 / 32 printed totals tie; Part I equals NYC Open Data `t474-a92g` on all 1,411 of its
> FY2023 amounts, and adds the one t474 lost to a broken record (`E CN136`, $150,000), so t474's
> $879,526,000 becomes the PDF's $879,676,000. t474's FY2023 accents are UTF-8 read as cp437 (74 rows).
> 15 Part I rows carry `RR` IDs ($22,633,000, no sponsor, 4 on borough `A`). Part II carries 39 `MA` /
> `0N` rows ($78,861,000), not Council additions. Against OMB's July 2022 adopted budget, 129 of 130
> lines match; `E D001` differs by $5,400,000. The retired capital CSV drops the comma after `SPEAKER`
> (265 rows). T&C: the PDF prints no condition numbers; 60 conditions in book order, as the retired CSV
> numbered them; it put the FSR table into condition 24's text.
