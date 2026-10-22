# FY2025 PDF review: capital §254 supporting detail and Terms & Conditions

**Report generated:** 2026-10-21 19:05 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** the PDFs in `source/FY25/` (sha256 below) and `data/capital/council_capital_awards.csv`
at `2aecf90` (its FY2025 rows come from NYC Open Data `t474-a92g`, published by the Council; no Council
workbook was found for FY2025, `data/capital/README.md`).
**Status:** review build for GitHub #104 (epic #101). Nothing in `data/` was changed by this folder; the
stacked promotion PR writes `data/fy25/pdf/`.

This is the FY2025 twin of [`../2026-10-21-fy26-capital-terms-review/`](../2026-10-21-fy26-capital-terms-review/README.md),
made with the **same two scripts**, driven by a new per-year config. Every number here was printed by those
scripts on 2026-10-21. Schedule C and the transparency resolutions are separate reviews.

## What is here

| File | What it is |
|---|---|
| [`REVIEW.md`](REVIEW.md) | **For Noel.** The flagged rows, sorted by dollars, with page numbers and what to decide |
| [`ISSUE-LOG-DRAFT.md`](ISSUE-LOG-DRAFT.md) | Draft #104 issue-log comments, one per problem. Not posted |
| `data/fy25_capital_sd_projects.csv` | Parts I and II: 1,508 rows (1,327 + 181), raw and clean side by side, page and bbox |
| `data/fy25_capital_sd_totals.csv` | All 32 printed `TOTALS FOR` lines, with the computed sums and `OK` / `FAIL` |
| `data/fy25_capital_sd_part3.csv`, `…_part3_orgs.csv` | Part III: 106 organizations, 129 budget-line rows |
| `data/fy25_capital_sd_pages.csv` | Triage, every page: kind, rotation, size, chars, rules |
| `data/fy25_capital_sd_checks.txt`, `…_review.csv`, `…_ink.json` | Check output and the machine review queue (25 entries) |
| `data/fy25_terms_conditions.csv` | 65 conditions: agencies, units, budget lines, dates, verbatim text, page range |
| `data/fy25_terms_units.csv` | One row per (condition, agency, unit or budget line): 228 units, 6 budget lines |
| `data/fy25_terms_fsr_table.csv` | The one ruled table (DOE Financial Status Reports, #16, p.6) |
| `data/fy25_terms_pages.csv`, `…_checks.txt`, `…_review.csv` | Triage, checks, review queue (35 entries, all `warn`) |
| `data/fy25_*_review_decisions.csv` | Empty decisions files (header only), for the explorer's review screen to fill |

## The code: same parser, one more config

| File | Change |
|---|---|
| [`code/review_capital_sd.py`](../../code/review_capital_sd.py) | Header `PROJECT ID` (FY2025) as well as `SUB ID`; summary page `($ 75,000,000)` (a space after `$`); a sponsor cell that wraps past its row's band joins the row of the sponsor line above it; Part II rows are compared with the Part I row on their own budget line when an ID is printed twice; new warn checks `C3.id_reused`, `C7.hairlines`, `C9.workbook_text`. Six config switches, all off by default: `bold_fonts`, `part3_amount_x1_tol`, `join_touching_words`, `workbook_mojibake`, `wb_pick_by_amount`, `c7_hairline_pt` |
| [`code/review_terms.py`](../../code/review_terms.py) | Docstring only. FY2025 needed only a config |
| `config/capital_sd/fy2025.toml` | PDF, sha256, page map, FY columns (FY2025–FY2028), export fonts, Part III's bold face, the switches above, the ink self-test row |
| `config/terms/fy2025.toml` | PDF, sha256, the retired CSV, page furniture (a bare page number at the foot), the FSR table's condition (#16) |
| [`code/test_review_fy25_capital_terms.py`](../../code/test_review_fy25_capital_terms.py) | 14 FY2025 tests, golden rows read off the rendered pages |

**FY2026 and FY2027 output is byte-identical.** Both scripts were run on both years before any change
(same venv, `--out /tmp/cap_base/...`) and again after the last change, and all 28 files were compared
with `cmp`: identical, including `checks.txt`, `review.csv` (so every `review_id` is unchanged) and the
ink JSON. The before-run itself equals the committed research files byte for byte. Two of the new
rules would have changed FY2026/FY2027 had they been on for every year, which is why they are switches:

- `wb_pick_by_amount`: FY2026 `HN CN1451` would be compared with its own workbook row (the one with its
  $250,000), and lose 2 false warnings (title, sponsor).
- `join_touching_words`: FY2026/FY2027 `sponsor_raw` would lose the space in `GENNARO ,` (4 rows).
  The clean `sponsor` is already the same.

`pytest code/` passes: 616 passed, 3 skipped.

## Results

### Capital supporting detail (87 pp., sha256 `e34acb15…8f3d`)

`Supporting-Detail-for-FY2025-Changes-To-the-Executive-Capital-Budget-Pursuant-to-Section-254-Council-Version-24.07.17.pdf`.

**Page map** (all 87 pages agree with it). p.1 cover · p.2 contents · p.3 divider · **pp.4–66 Part I**
("Page 1 of 63") · **p.67 summary** · p.68 divider · **pp.69–77 Part II** · p.78 divider ·
**pp.79–87 Part III**. All three Parts are upright; the contents, the dividers and the summary carry
/Rotate 90 (the triage's "rotated pages 2–3, 67–68, 78").

| Check | Result |
|---|---|
| Rows | Part I 1,327; Part II 181; Part III 106 organizations / 129 budget-line rows |
| C1 every `TOTALS FOR` line (count and all four FYs) | **32 / 32 tie**, including both `ALL` lines: Part I 1,327 projects, $775,000,000 FY2025; Part II 181, $158,992,000 FY2025 / $11,000,000 FY2026 |
| C2 p.67 summary | Additions $775,000,000 = Part I. Additions − rescindments $75,000,000 = net $700,000,000. The rescindments are one printed number with no list behind it |
| C3 Part II vs Part I | 141 rows equal a Part I row in every field; 40 are in Part II only (39 `MA` rows on `0N` lines, $57,657,000, and `PV CT001` $2,500,000); all 141 Part I rows on `DN` lines are in Part II. **6 IDs are printed on two Part I rows each** (`C3.id_reused`) |
| C4 Part III | 106 / 106 organization lines equal their rows; grand total $158,992,000 / $11,000,000 = Part II; 129 / 129 budget lines equal Part II |
| C5 two reads of each word | 24,789 agree. 20 words on p.51 (edited after export) were written out of row order. 2 near disagreements, both settled: a `0` both rows print, and a sponsor the Open Data row confirms |
| C6 every word in exactly one field | 0 orphans, 0 unplaced words, every row has one value per FY |
| C7 rules in pixels vs vector rules | 87 pages, 113 / 113 matched, none one-sided. Plus 106 hairlines (0.12 pt, 50% grey) between Part III organizations, under a pixel at 300 dpi, so not visible to the image side (one `C7.hairlines` warning) |
| C8 ink coverage at 300 dpi | **0 uncovered regions.** Self-test: hiding `ED NC056` (p.4) gives 39 regions |
| C9 Open Data `t474-a92g`, FY2025 | **1,325 / 1,325** of its rows match a PDF amount on (ID, budget line, FY, amount); the PDF's 2 others are FY2026 money t474 does not carry (`P CN175` $10,000,000, `ED NC091` $6,000,000; `families/capital.md` predicted them). Borough, title and sponsor equal on 1,325 / 1,325 once t474's mojibake is decoded |
| vs the retired `data/fy25/capital` CSV | Same 1,508 rows and (ID, budget line) keys; every amount and borough equal. It **lost the last sponsor line on 5 rows** (`BLACK, LATINO AND ASIAN CAUCUS` on `HN CN017`, `HO CN019`, `LB CN005`, `LQ CN003`, `P CN096`); t474 has it on all 5. It differs on 51 titles and 54 code cells, where it pulled non-standard codes (`S:02M411`, `B:KBNU`) out of the title or lost a space (`NORTHSIDECENTER`); here they stay as printed, as for FY2026. It names the ID column `budget_line` and the budget line `sub_id` |

### Terms & Conditions (25 pp., sha256 `1e7b8be1…8e57`)

`FY25-Terms-and-Conditions-1.pdf`. p.1 cover; pp.2–25 conditions; a bare page number at the foot of every
page. One ruled table (p.6).

| Check | Result |
|---|---|
| T1 numbering | 65 conditions, 1..65, no gap or repeat |
| T2 unit and budget-line lines | 234 / 234 heading lines placed (228 units, 6 budget lines) |
| T3 body names the heading's units | 62 / 65. #57 says `011` where the heading has DOHMH `111`; #64 and #65 say "units of appropriations" (plural), which the check does not read. All three are the PDF's own wording |
| T4 characters | 0 characters outside a condition, the table or page furniture |
| T5 FSR table | vector and image lattices agree on every separator (5 × 8); 28 / 28 cells identical |
| T6 ink | 0 uncovered regions |
| T7 vs the retired `data/fy25/terms` CSV | Same 65 numbers and first agencies. 46 texts equal; 19 differ: 14 are headings put into the text (#30, #39, #51–#53, #57–#65), 1 is the FSR table in #16's text, 4 are hyphens the old CSV dropped (#15 and #20 print `education - for`, `per day - for`; #22 `non-special`, #23 `Pre-Kindergarten` across a line end). It lost the units of every agency after the first in #57–#65 (9 conditions) |

## What FY2025 does that FY2026 does not

- **`PROJECT ID`, not `SUB ID`,** in the column header, and `($ 75,000,000)` on the summary page.
- **Three exports.** Parts I and II are unsubsetted Arial; Part III is `CIDFont+F1`/`F3`, whose bold face
  does not say "Bold" (checked on a render). Text typed in later is `BXDXCW+ArialMT` / `MIZCVF+ArialMT`
  (p.51 only: `, SCHULMAN` on `HO CN025`, with its `C` in the other subset).
- **IDs printed twice.** `ED NC128` (pp.4 and 44, different budget lines), `E CN810`, `HN CN018`,
  `HO CN019` (same ID **and** budget line, two projects), `HN CN020`, `HN CN021`. t474 holds the same
  pairs, so this is the source, not the parser. A loader must not treat `sub_id` as a key.
- **`ED` IDs on other agencies' lines** (`ED NC128` on `AG DN06Y`, Aging). As printed.
- **A `CT` row in Part II** (`PV CT001`, 126 PV207APLO APOLLO THEATER) beside the expected `MA` series.
- **The comparison source is mojibake.** t474's FY2025 accents are cp1252 bytes read as cp437 (`OssΘ`,
  `Cabßn`, `CAF╔`): 50 rows. Decoded for comparing only.
- **T&C:** no `Page N of M` header (a bare number at the foot), plain `-` hyphens (FY2026 used U+2010), the
  FSR table under #16 (FY2026: #15).

## How to redo it

```
python3 -m venv .venv
.venv/bin/pip install -r code/requirements.txt -r code/requirements-cv.txt pytest
.venv/bin/python code/review_capital_sd.py --fy 2025          # ~3 min with C7/C8; --no-ink skips them
.venv/bin/python code/review_capital_sd.py --fy 2025 --selftest-ink --out /tmp/x   # C8 must fire on p.4
.venv/bin/python code/review_terms.py --fy 2025
.venv/bin/python -m pytest code/test_review_fy25_capital_terms.py code/test_review_fy26_capital_terms.py code/test_review_capital_sd.py
```

Run on pdfplumber 0.11.10, pypdfium2 5.14.0, numpy 2.5.4, opencv-python-headless 4.14.0.94,
pillow 13.0.0, Python 3.14.8 (FY2026 was run on pdfplumber 0.11.9 and pillow 11.3.0; its outputs
reproduce byte for byte on these versions).

## Not in scope: the Resolution A book

`source/FY25/Fiscal-2025-Capital-Changes.pdf` (88 pp., sha256 `e35b1699…c501`) is a different family
("Changes to the Executive Capital Budget", Resolution A grammar, `families/capital.md` R2). It is
AES-256 encrypted with an empty user password (V5 R6, `/P -1324`): it opens and its text extracts, and
its permissions allow copying. It is landscape (70 pp.) with 18 portrait pages (71–88) and no
`TOTALS FOR` lines; the retired `data/fy25/capital/fy25_capital_changes_appropriation.csv` (149 rows)
says so itself. **Recommendation:** leave it for its own family pass, as the epic rates it low priority.
It is worth doing once, because it is the only book that lists the **rescindments** this book prints
as one number ($75,000,000, p.67), and it holds the capital Terms and Conditions; check it against OMB
(`data/capital/RECONCILIATION.md` §3), not against this book.

## Shared code

`code/ocr/grid.py`, `code/build_pdf_promoted.py` and `data/pdf_years.csv` are
not changed here (the promotion PR adds two families). No Schedule C or transparency code was touched.

## Not done

- **OCR audit (PLAN stage 10).** Not run, as for FY2026: both PDFs are born-digital with 0 uncovered ink.
- **DATA-ANOMALIES** is not edited (parallel FY2025 sessions may edit it). Proposed text is in
  `ISSUE-LOG-DRAFT.md`.
- **`data/capital/`** is not edited. t474's mojibake and the PDF's reused IDs are notes for its README /
  RECONCILIATION, if Noel agrees.
- **Suggested decisions** (`code/build_review_suggestions.py`) and the explorer's decisions-file list
  (`mcp/scripts/pdf-families.mjs`, out of bounds for this session) do not list FY2025 yet.
