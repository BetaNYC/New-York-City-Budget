# FY2026 PDF review: capital §254 supporting detail and Terms & Conditions

**Report generated:** 2026-10-21 00:32 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** the PDFs in `source/FY26/` (sha256 below) and `data/capital/council_capital_awards.csv`
at `d1f960c` (the FY2026 rows come from the Council's own workbook, captured by the Internet Archive
on 2025-12-03; `data/capital/README.md`).
**Status:** review build for GitHub #103 (epic #101). Not served: DATA-ANOMALIES §27 keeps PDF data out of
the MCP and the site. Nothing in `data/` was changed by this folder.

This is the FY2026 twin of [`../2026-10-20-fy27-capital-terms-review/`](../2026-10-20-fy27-capital-terms-review/README.md),
made with the **same two scripts**, now driven by a per-year config. Every number here was printed by
those scripts on 2026-10-21. Schedule C and the transparency resolutions are separate reviews.

## What is here

| File | What it is |
|---|---|
| [`REVIEW.md`](REVIEW.md) | **For Noel.** The flagged rows, sorted by dollars, with page numbers and what to decide |
| [`ISSUE-LOG-DRAFT.md`](ISSUE-LOG-DRAFT.md) | Draft #103 issue-log comments, one per problem. Not posted |
| `data/fy26_capital_sd_projects.csv` | Parts I and II: 1,456 rows (1,259 + 197), raw and clean side by side, page and bbox |
| `data/fy26_capital_sd_totals.csv` | All 33 printed `TOTALS FOR` lines, with the computed sums and `OK` / `FAIL` |
| `data/fy26_capital_sd_part3.csv`, `…_part3_orgs.csv` | Part III: 125 organizations, 151 budget-line rows |
| `data/fy26_capital_sd_pages.csv` | Triage, every page: kind, rotation, size, chars, rules |
| `data/fy26_capital_sd_checks.txt`, `…_review.csv`, `…_ink.json` | Check output and the machine review queue (50 entries) |
| `data/fy26_terms_conditions.csv` | 68 conditions: agencies, units, budget lines, dates, verbatim text, page range |
| `data/fy26_terms_units.csv` | One row per (condition, agency, unit or budget line): 239 units, 6 budget lines |
| `data/fy26_terms_fsr_table.csv` | The one ruled table (DOE Financial Status Reports, #15, p.8) |
| `data/fy26_terms_pages.csv`, `…_checks.txt`, `…_review.csv` | Triage, checks, review queue (60 entries, all `warn`) |

## The code: one parser, a config per year

| File | Change |
|---|---|
| [`code/review_capital_sd.py`](../../code/review_capital_sd.py) | Reads `config/capital_sd/fy<FY>.toml`; `--fy` (default 2027). Negative amounts (`-183,000`, `$(183,000)`); the workbook's FY2026 IDs keep an agency prefix (`E CN0001`); an unmapped tab glyph `(cid:9)` is read as a space in `title` (kept in `title_raw`) |
| [`code/review_terms.py`](../../code/review_terms.py) | Reads `config/terms/fy<FY>.toml`; `--fy`. Page furniture from config (FY2026 prints `Page N of 29` at the head); `Units of Appropriation`; `units of appropriation 401, …` without "numbers"; U+2010 budget lines; superscript ordinals in table cells |
| `config/capital_sd/fy2027.toml`, `fy2026.toml` | PDF, sha256, page map, /Rotate per part, FY columns, export fonts, the Part II-only series, the ink self-test row |
| `config/terms/fy2027.toml`, `fy2026.toml` | PDF, sha256, the retired CSV, page furniture, the FSR table's condition |
| [`code/test_review_fy26_capital_terms.py`](../../code/test_review_fy26_capital_terms.py) | 11 FY2026 tests, golden rows read off the pages |

**FY2027 output is byte-identical.** Both scripts were run on FY2027 before and after the change
(same venv, `--out /tmp/...`), and all 14 files compared with `cmp`: identical, including
`checks.txt`, `review.csv` (so every `review_id` is unchanged) and the ink JSON. The FY2027 ink
self-test still gives 59 regions on p.40. `code/build_pdf_promoted.py --check` and the full suite
(`pytest code/`, 552 passed, 3 skipped) pass. Two FY2026 runs give byte-identical output.

## Results

### Capital supporting detail (86 pp., sha256 `8535ee99…5b2f`)

**Page map** (all 86 pages agree with it). Unlike FY2027, Parts I and II are upright and Part III
is rotated: p.1 cover · p.2 contents · p.3 divider · **pp.4–64 Part I** ("Page 1 of 61") ·
**p.65 summary** · p.66 divider · **pp.67–76 Part II** (a second export, other fonts) · p.77 divider ·
**pp.78–86 Part III** (rotated 90°).

| Check | Result |
|---|---|
| Rows | Part I 1,259; Part II 197; Part III 125 organizations / 151 budget-line rows |
| C1 every `TOTALS FOR` line (count and all four FYs) | **33 / 33 tie**, including both `ALL` lines: Part I 1,259 projects, $779,320,000 FY2026 / $25,250,000 FY2027 / $3,000,000 / $3,000,000; Part II 197, $203,243,000 / $21,250,000 |
| C2 p.65 summary | Additions $779,320,000 = Part I. Additions − rescindments $26,920,000 = net $752,400,000. The rescindments are one printed number with no list behind it |
| C3 Part II vs Part I | 150 rows equal in every field; 5 differ only in an accent (`GUTIÉRREZ` / `GUTIERREZ` ×4, `FARÍAS` / `FARIAS` ×1); 42 are in Part II only (39 `MM` rows on `0N` lines, $62,073,000, plus 3 `MA` rows, $2,817,000 net); all 155 Part I rows on `DN` lines are in Part II |
| C4 Part III | 125 / 125 organization lines equal their rows; grand total $203,243,000 / $21,250,000 = Part II; 151 / 151 budget lines equal Part II |
| C5 two reads of each word | 24,020 agree. 155 words on 4 edited pages (pp.56, 59, 61, 74) were written out of row order. 8 near disagreements: all kept the geometry read; 4 are a `0` both rows print, 4 are sponsors the Council workbook confirms |
| C6 every word in exactly one field | 0 orphans, 0 unplaced words, every row has one value per FY |
| C7 rules in pixels vs vector rules | 86 pages, 233 / 233 matched, none one-sided |
| C8 ink coverage at 300 dpi | **0 uncovered regions.** Self-test: hiding `AG NC1273` (p.4) gives 81 regions; hiding one `0` gives 1 |
| C9 Council workbook, FY2026 | **1,253 / 1,261** non-zero amounts match on (ID, budget line, FY, amount). The 8 others: 7 `ADMIN` rows with FY2027 money only ($2,950,000; the workbook has no row for them) and `HN CN0092` $125,000, which the workbook files under `HN CN1451` (its row 61). Borough 1,251 / 1,251. Title 1,239 / 1,251. Sponsor list 1,247 / 1,251 |
| vs the retired `data/fy26/capital` CSV | Same 1,456 rows and (ID, budget line) keys; every amount, borough and sponsor equal. It differs on 41 titles and 81 code cells, where it pulled non-standard codes (`B:07X277`, `S:437`) out of the title; here they stay in the title as printed (FY2027 has 18 such rows). It also names the ID column `budget_line` and the budget line `sub_id`, as FY2027's did |

A third source agrees too: `P CN1606` QUEENS COUNTY FARM EDUCATIONAL CENTER, $2,000,000 (p.56), the
row `data/capital/RECONCILIATION.md` §4 found missing from Open Data `t474-a92g`, is printed in the PDF.

### Terms & Conditions (29 pp., sha256 `53159ea1…c22c`)

p.1 cover; pp.2–29 conditions; `Page N of 29` at the head of every page. One ruled table (p.8).

| Check | Result |
|---|---|
| T1 numbering | 68 conditions, 1..68, no gap or repeat |
| T2 unit and budget-line lines | 245 / 245 heading lines placed (239 units, 6 budget lines) |
| T3 body names the heading's units | 67 / 68. #67 says "units of appropriations 311 and 312" (the PDF's typo), which the check does not read; the heading has 311, 312 and NYPD 001 |
| T4 characters | 0 characters outside a condition, the table or page furniture |
| T5 FSR table | vector and image lattices agree on every separator (5 × 8); 28 / 28 cells identical |
| T6 ink | 0 uncovered regions |
| T7 vs the retired `data/fy26/terms` CSV | Same 68 numbers and first agencies. 21 texts equal; 29 differ only because the old CSV turned the PDF's U+2010 hyphens into `-`; 18 are old-CSV errors: headings in the text (#5, #25, #29, #39, #53–#55, #59–#68) and the FSR table in #15's text. The old CSV lost units in 12 conditions (#5, #25 entirely; the second and later agencies of #59–#68) |

## What FY2026 does that FY2027 does not

- **Rotation is the other way round.** Parts I and II are upright, Part III rotated. `bbox_pt` is in
  pdfplumber's display coordinates, as for FY2027; promotion unrotates Part III.
- **Two exports in one book.** Part I is unsubsetted Arial; Part II uses subsets `AAAAAA+` /
  `AAAAAB+`. Text typed in later is `KGLUJE+ArialMT` (pp.56, 59, 61, 74).
- **Negative amounts.** `PV MA0005` MANHATTAN COMMUNITY ACCESS CORPORATION prints `-183,000` in Part II
  and `$(183,000)` / `(183,000)` in Part III.
- **A `TECHNICAL ADJUSTMENTS` sponsor** (18 Part I rows, $25,919,000 FY2026; all in the workbook) and an
  `ADMIN` sponsor (7 rows, FY2027 money only, not in the workbook).
- **T&C typography:** U+2010 hyphens (91 in condition text), no-break spaces and superscript ordinals
  in the FSR dates ("October 2nd"). All kept as printed.

## How to redo it

```
python3 -m venv .venv
.venv/bin/pip install -r code/requirements.txt -r code/requirements-cv.txt pytest
.venv/bin/python code/review_capital_sd.py --fy 2026          # ~6 s; --no-ink skips C7/C8
.venv/bin/python code/review_capital_sd.py --fy 2026 --selftest-ink --out /tmp/x   # C8 must fire on p.4
.venv/bin/python code/review_terms.py --fy 2026
.venv/bin/python -m pytest code/test_review_fy26_capital_terms.py code/test_review_capital_sd.py
```

Run on pdfplumber 0.11.9, pypdfium2 5.14.0, numpy 2.5.4, opencv-python-headless 4.14.0.94,
pillow 11.3.0, Python 3.14.8.

## Shared code

`code/ocr/grid.py` is **not changed**. No Schedule C or transparency code was touched.

## Not done

- **OCR audit (PLAN stage 10).** Not run, as for FY2027: both PDFs are born-digital with 0 uncovered ink.
- **DATA-ANOMALIES** is not edited (parallel FY2026 sessions may edit it). Proposed text is in
  `ISSUE-LOG-DRAFT.md` § "Proposed DATA-ANOMALIES entry".
- **`data/capital/`** is not edited. The workbook's duplicate `HN CN1451` (REVIEW A5) is a note for
  its RECONCILIATION, if Noel agrees.
