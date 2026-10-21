# FY2027 PDF review: capital §254 supporting detail and Terms & Conditions

**Report generated:** 2026-10-20 22:16 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** the PDFs in `source/FY27/` (sha256 below) and `data/capital/council_capital_awards.csv`
at `f334359`.
**Status:** review build for GitHub #102 (epic #101). Not served: DATA-ANOMALIES §27 keeps PDF data out of
the MCP and the site. Nothing in `data/` was changed.

Every number here was printed by the two scripts below on 2026-10-20. Schedule C is a separate review
(branch `feature/fy27-schedule-c-review`).

## What is here

| File | What it is |
|---|---|
| [`REVIEW.md`](REVIEW.md) | **For Noel.** The flagged rows, sorted by dollars, with page numbers and what to decide |
| [`ISSUE-LOG-DRAFT.md`](ISSUE-LOG-DRAFT.md) | Draft #102 issue-log comments, one per problem. Not posted |
| `data/fy27_capital_sd_projects.csv` | Parts I and II: 1,391 rows (1,213 + 178), raw and clean side by side, page and bbox |
| `data/fy27_capital_sd_totals.csv` | All 28 printed `TOTALS FOR` lines, with the computed sums and `OK` / `FAIL` |
| `data/fy27_capital_sd_part3.csv`, `…_part3_orgs.csv` | Part III: 109 organizations, 127 budget-line rows |
| `data/fy27_capital_sd_pages.csv` | Triage, every page: kind, rotation, size, chars, rules |
| `data/fy27_capital_sd_checks.txt`, `…_review.csv`, `…_ink.json` | Check output and the machine review queue |
| `data/fy27_terms_conditions.csv` | 75 conditions: agencies, units, budget lines, dates, verbatim text, page range |
| `data/fy27_terms_units.csv` | One row per (condition, agency, unit or budget line): 262 units, 7 budget lines |
| `data/fy27_terms_fsr_table.csv` | The one ruled table (DOE Financial Status Reports, #15, pp.7–8) |
| `data/fy27_terms_pages.csv`, `…_checks.txt`, `…_review.csv` | Triage, checks, review queue |

Code: [`code/review_capital_sd.py`](../../code/review_capital_sd.py),
[`code/review_terms.py`](../../code/review_terms.py), tests in
[`code/test_review_capital_sd.py`](../../code/test_review_capital_sd.py) (10 tests).

## Results

### Capital supporting detail (80 pp., sha256 `4c48252e…5b90`)

**Page map** (all 80 pages agree with it):
p.1 cover · p.2 contents · p.3 divider · **pp.4–60 Part I** (rotated 90°) · **p.61 summary** ·
p.62 divider · **pp.63–71 Part II** (rotated) · p.72 divider · **pp.73–80 Part III** (upright, ruled).

| Check | Result |
|---|---|
| Rows | Part I 1,213; Part II 178; Part III 109 organizations / 127 budget-line rows |
| C1 every `TOTALS FOR` line (count and all four FYs) | **28 / 28 tie**, including both `ALL` lines: Part I 1,213 projects, $853,688,000 FY2027 / $44,000,000 FY2028; Part II 178, $210,677,000 / $10,000,000 |
| C2 p.61 summary | Additions $853,688,000 = Part I. Additions − rescindments $23,317,000 = net $830,371,000. The rescindments are one printed number with no list behind it |
| C3 Part II vs Part I | 145 rows equal in every field; 3 differ in sponsor only (post-export edits, below); 30 `MA` rows are in Part II only; all 148 Part I rows on `DN` lines are in Part II |
| C4 Part III | 109 / 109 organization lines equal their rows; grand total $210,677,000 = Part II; 127 / 127 budget lines equal Part II |
| C5 two reads of each word (geometry vs content-stream order) | 23,049 agree. 364 words on 8 edited pages were written out of row order, so the stream has no opinion there. 32 near disagreements: all kept the geometry read, which the Council workbook confirms (or which is a `0` both rows print) |
| C6 every word in exactly one field | 0 orphans. 1 row with no FY2030 value and 1 sponsor holding a `0`: a misprint on p.56 |
| C7 rules in pixels (`code/ocr/grid.py`) vs vector rules | 80 pages, 222 / 222 matched, none one-sided |
| C8 ink coverage at 300 dpi | **0 uncovered regions.** Self-test: hiding one row (p.40) gives 59 regions; hiding one `0` gives 1 |
| C9 Council workbook, FY2027 | 1,215 / 1,215 non-zero amounts match on (ID, budget line, FY, amount). Borough 1,213 / 1,213. Title 1,210 / 1,213. Sponsor list 1,175 / 1,213 (34 of the 38 misses are `SANCHEZ J.` / `SANCHEZ P.` vs the workbook's plain `Sanchez`) |

### Terms & Conditions (32 pp., sha256 `54b94c95…1d1b`)

p.1 cover; pp.2–32 conditions. One ruled table (pp.7–8).

| Check | Result |
|---|---|
| T1 numbering | 75 conditions, 1..75, no gap or repeat |
| T2 unit and budget-line lines | 269 / 269 heading lines placed (262 units, 7 budget lines) |
| T3 body names the heading's units | 75 / 75 |
| T4 characters | 0 characters outside a condition, the table or page furniture |
| T5 FSR table | vector and image lattices agree on every separator (5 × 4 and 5 × 5); 28 / 28 cells identical |
| T6 ink | 0 uncovered regions |
| T7 vs the retired `data/fy27/terms` CSV | Same 75 numbers and first agencies. Old text has 134 mid-word splits; new has 0. The old CSV lost the units of every agency after the first in 12 multi-agency conditions (#64–#75), and put those headings into the text |

## How it reads a page with no borders

Parts I and II are a Word table printed without rules, so there is no lattice to read
(families/capital.md §6). Each word is read twice:

1. **Geometry.** A row starts at its SUB ID line. Title lines group into cell blocks by their
   spacing (within a cell ≤ 9.24 pt apart; between cells ≥ 14.94 pt; cut at 12 pt), and blocks pair
   with rows in page order. Every other word joins the row band holding its centre.
2. **Stream.** Word writes a table row by row, so each word follows its own row's SUB ID.

Titles printed *above* their own SUB ID line (p.40 `HD CC1044`, `CC1047`, `CC1050`) are why a
line-by-line reader fails here: the retired CSV left those titles blank.

The ink check is a simplified, re-targeted take on exec-orders `vlm_ocr.ink_coverage` (PLAN §3
stage 6), not a port: ink = `grid.binarize`; covered = emitted characters (padding scales with font
size) plus vector rules at their stroke width. It cannot see a dropped period (too little ink).

## How to redo it

```
python3 -m venv .venv
.venv/bin/pip install "pdfplumber>=0.11,<0.12" "pypdfium2>=5,<6" "numpy>=1.26,<3" \
    "opencv-python-headless>=4.9,<5" "pillow>=10,<12" pytest
.venv/bin/python code/review_capital_sd.py          # ~5 s; --no-ink skips C7/C8
.venv/bin/python code/review_capital_sd.py --selftest-ink --out /tmp/x   # C8 must fire on p.40
.venv/bin/python code/review_terms.py
.venv/bin/python -m pytest code/test_review_capital_sd.py
```

Run on pdfplumber 0.11.9, pypdfium2 5.14.0, numpy 2.5.4, opencv-python-headless 4.14.0.94,
Python 3.14. Two runs give byte-identical output.

## Shared code

`code/ocr/grid.py` is **not changed**. `review_capital_sd.py` calls its `binarize`, `rule_masks`
(`kernel_px=60`) and the private `_rule_components`. No Schedule C code was touched.

## Not done

- **OCR audit (PLAN stage 10).** Not run: docTR is not installed here, and both PDFs are born-digital
  with 0 uncovered ink. A sampled audit can be added later.
- **Review UI (stage 11).** The review is the two CSVs and `REVIEW.md`.
- **DATA-ANOMALIES** is not edited (the Schedule C branch may edit it too). Proposed text is in
  `ISSUE-LOG-DRAFT.md` § "Proposed DATA-ANOMALIES entry".
