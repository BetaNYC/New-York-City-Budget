# FY2021 PDF review: Terms & Conditions (no capital supporting detail in `source/`)

**Report generated:** 2026-10-21 23:50 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** the PDF in `source/FY21/` (sha256 below) and the retired
`data/fy21/terms/fy21_terms_and_conditions.csv` at `735556c`.
**Status:** review build for GitHub #108 (epic #101). Nothing in `data/` was changed by this folder; the
stacked promotion PR writes `data/fy21/pdf/terms/`.

The FY2021 twin of the Terms & Conditions half of
[`../2026-10-21-fy22-capital-terms-review/`](../2026-10-21-fy22-capital-terms-review/README.md), made with
the **same script** and a new per-year config. Every number here was printed by that script on
2026-10-21. Schedule C and the transparency resolutions are separate reviews.

**Only one of the two families exists for FY2021.** There is no FY2021 capital supporting detail in
`source/FY21/` (#108: "No capital supporting detail in `source/`"). A copy is on the City's
publications portal and is being added separately; it is out of scope here, so this folder has no
`fy21_capital_sd_*` files and `data/pdf_years.csv` gets no FY2021 `capital_sd` row.

## What is here

| File | What it is |
|---|---|
| [`REVIEW.md`](REVIEW.md) | **For Noel.** The flagged items with page numbers and what to decide |
| [`ISSUE-LOG-DRAFT.md`](ISSUE-LOG-DRAFT.md) | Draft #108 issue-log comments, one per problem. Not posted |
| `data/fy21_terms_conditions.csv` | 46 conditions: agencies, units, budget lines, dates, verbatim text, page range |
| `data/fy21_terms_units.csv` | One row per (condition, agency, unit or budget line): 107 units, 4 budget lines |
| `data/fy21_terms_fsr_table.csv` | The one ruled table (DOE Financial Status Reports, condition 19, p.8): 6 rows |
| `data/fy21_terms_pages.csv`, `…_checks.txt`, `…_review.csv` | Triage, checks, review queue (11 entries, all `warn`) |
| `data/fy21_terms_review_decisions.csv` | Empty decisions file (header only) |

Review CSV columns are the FY2022 ones.

## The code

| File | Change |
|---|---|
| [`code/review_terms.py`](../../code/review_terms.py) | One addition. **Config `body_x0_max`:** T1 counts the paragraphs that open "As a condition" at the left margin, and the margin was hard-coded as x0 < 80 pt. FY2021 sets its body at 90 pt, so T1 counted 0 openings for 46 headings. Default 80, so every other year is unchanged |
| `config/terms/fy2021.toml` | New |
| [`code/test_review_fy21_capital_terms.py`](../../code/test_review_fy21_capital_terms.py) | 4 FY2021 tests, golden rows read off the rendered pages |

**FY2022–FY2027 output is byte-identical.** All six years' research files were rebuilt with this code
(`review_terms.py`) and `git status` shows no change to any of them. A second
FY2021 run gives the same files.

## Results

### Terms & Conditions (16 pp., sha256 `0b469b3e…7e4f`)

`Fiscal-2021-Terms-and-Conditions.pdf`. Acrobat PDFMaker 20 for Word; not encrypted; no /Rotate; all
612 × 792. p.1 cover; pp.2–16 conditions. **No page numbers or other furniture**, like FY2022. One
ruled table, on p.8. Prints **no condition numbers**, like FY2022–FY2024.

| Check | Result |
|---|---|
| T1 conditions | 46, numbered here in book order; 46 paragraphs open "As a condition" at the left margin |
| T2 unit and budget-line lines | 111 / 111 placed (107 units, 4 budget lines). Every agency line prints a three-digit code |
| T3 body names the heading's units | 44 / 46. #12 names "budget lines E2364 and E2365" (no hyphen; T3 reads `XX-nnnn`); #28 wraps `HD-` / `0009` across a line end. Both are the check's limits; the texts are right (as FY2022 #14, #33) |
| T4 characters | 0 outside a condition or the table |
| T5 FSR table | both lattices agree on every separator (5 x, 8 y); 28 / 28 cells identical. Months in order, SEPTEMBER 2020 to MAY 2021 (FY2022's copy of this table prints them out of order) |
| T6 ink | 0 uncovered regions |
| T7 vs the retired `data/fy21/terms` CSV | Same 46 conditions in the same order; first agency equal on all 46; 44 texts equal. The old file put the FSR table into #19's text, dropped the printed hyphen in #23 ("meals per day - for"), and put capital budget lines into `units` (#2, #3, #12, #28). It also kept **only the first agency of the four multi-agency conditions**: #1 lists DOC's units 001–004 under ACS's code 068, and #12 (SCA), #28 (Capital Budget) and #37 (DCAS) lose their second agency. T7 compares the first agency only, so these are listed here, not in the review file. 22 mid-word splits in the old text, 0 in the new |

**Four conditions name two agencies:** #1 ACS (068) and DOC (072), p.2; #12 DOE (040) and **School
Construction Authority (040)**, p.5 (SCA printed with DOE's code, kept as printed); #28 HPD (806) and
"Capital Budget" (`HD-0009`), p.11; #37 DYCD (260) and DCAS (856), p.13 (the body is about the Office of
the Census). Two conditions are capital only: #2 and #3, both `HA-0001` (NYCHA roofs; Mayor's Action
Plan), pp.2–3.

## What FY2021 does that FY2022 does not

- **Body text at 90 pt**, not 72 pt (the one code change).
- **Every agency line prints a three-digit code** (FY2022 had `(40)` and an HPD line with none).
- **The FSR table is on one page** and its months are in order.
- **A year typed in another font:** p.5, #12, "2021" in "no later than July 15, 2021" is set in Calibri
  (the rest of the page is Times New Roman), a later edit. The text reads the same; T6 sees no stray ink.
- p.16 #45 prints "004,006" with no space; kept as printed.

## How to redo it

```
.venv/bin/python code/review_terms.py --fy 2021          # --no-ink skips T6
.venv/bin/python -m pytest code/test_review_fy21_capital_terms.py
```

Same environment as FY2022 (pdfplumber 0.11.10, pypdfium2 5.14.0, opencv-python-headless 4.14.0.94,
numpy 2.5.4, Python 3.14.8).

## Not in scope: the Resolution A book

`source/FY21/FY21-Sec254-Capital-ResoA-M231-Res1362-Res1363.pdf` (73 pp., sha256 `ead9f9bc…1bf9`) is
the Resolution A family ("Capital Changes"). Adobe InDesign 14.0; not encrypted; tier B, text layer
present; per `data/pdf_condition.csv`, pp.3–73 carry a /Rotate and two pages are landscape. No retired
parse of it exists in `data/fy21/`. It is **not** the supporting detail: it does not list Council
projects by ID. **Recommendation:** leave it for one Resolution A pass across FY2016–FY2025
(`families/capital.md` R2), checked against OMB.

## Not done

- **Capital supporting detail:** none in `source/FY21/` (above).
- **OCR audit (PLAN stage 10).** Not run: the PDF is born-digital with 0 uncovered ink.
- **DATA-ANOMALIES** is not edited. The proposed entry is below.
- Suggested decisions (`code/build_review_suggestions.py`) and `mcp/scripts/pdf-families.mjs` do not
  list FY2021 yet (recipe Step 6, the integrator's).

## Proposed DATA-ANOMALIES entry

Not applied (parallel sessions edit that file; the integrator numbers it):

> **§NN. FY2021 Terms & Conditions, re-read from the PDF (GitHub #108).**
> `research/2026-10-21-fy21-capital-terms-review/`. 46 conditions, unnumbered and with no page
> furniture, numbered here in book order; all 111 unit and budget-line heading lines placed; the
> FSR table (p.8) agrees under both lattices. The retired `data/fy21/terms` CSV has the same 46
> conditions in order but keeps only the first agency of the four two-agency conditions (#1 ACS/DOC,
> #12 DOE/SCA, #28 HPD/Capital Budget, #37 DYCD/DCAS), files DOC's units under ACS's code, puts
> capital budget lines in `units`, folds the FSR table into #19's text and drops a printed hyphen
> (#23). The PDF prints SCA with DOE's code (040). FY2021 has no capital supporting detail in
> `source/`.
