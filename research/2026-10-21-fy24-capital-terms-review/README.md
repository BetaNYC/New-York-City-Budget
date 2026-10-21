# FY2024 PDF review: capital §254 supporting detail and Terms & Conditions

**Report generated:** 2026-10-21 19:20 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** the PDFs in `source/FY24/` (sha256 below) and `data/capital/council_capital_awards.csv`
at `2aecf90` (its FY2024 rows come from NYC Open Data `t474-a92g`, published by the Council; no Council
workbook was found for FY2024, `data/capital/README.md`).
**Status:** review build for GitHub #105 (epic #101). Nothing in `data/` was changed by this folder; the
stacked promotion PR writes `data/fy24/pdf/`.

The FY2024 twin of [`../2026-10-21-fy25-capital-terms-review/`](../2026-10-21-fy25-capital-terms-review/README.md),
made with the **same two scripts** and a new per-year config. Every number here was printed by those
scripts on 2026-10-21. Schedule C and the transparency resolutions are separate reviews.

## The encrypted capital book

`FY2024-Sec254-Supporting-Detail-Book_7.10.2023pwp-2.pdf` is AES-256 encrypted (V5 R6) with an **empty
user password**: pdfplumber, pypdfium2 and pypdf open it with no password, and every character extracts.
Its owner permissions (`/P -1052`) allow printing and "extract for accessibility", and **do not allow
copying**. Text extraction is not blocked, so the review went ahead; the flag is listed for Noel
(Decisions, PR body). Ink coverage (0 uncovered regions) shows the extracted text is all the page has.

## What is here

| File | What it is |
|---|---|
| [`REVIEW.md`](REVIEW.md) | **For Noel.** The flagged rows, sorted by dollars, with page numbers and what to decide |
| [`ISSUE-LOG-DRAFT.md`](ISSUE-LOG-DRAFT.md) | Draft #105 issue-log comments, one per problem. Not posted |
| `data/fy24_capital_sd_projects.csv` | Parts I and II: 1,364 rows (1,241 + 123), raw and clean side by side, page and bbox |
| `data/fy24_capital_sd_totals.csv` | All 32 printed `TOTALS FOR` lines, with the computed sums and `OK` / `FAIL` |
| `data/fy24_capital_sd_part3.csv`, `…_part3_orgs.csv` | Part III: 95 organizations, 113 budget-line rows |
| `data/fy24_capital_sd_pages.csv` | Triage, every page |
| `data/fy24_capital_sd_checks.txt`, `…_review.csv`, `…_ink.json` | Check output and the machine review queue (22 entries) |
| `data/fy24_terms_conditions.csv` | 61 conditions: agencies, units, budget lines, dates, verbatim text, page range |
| `data/fy24_terms_units.csv` | One row per (condition, agency, unit or budget line): 182 units, 5 budget lines |
| `data/fy24_terms_fsr_table.csv` | The one ruled table (DOE Financial Status Reports, #21, pp.8–9) |
| `data/fy24_terms_pages.csv`, `…_checks.txt`, `…_review.csv` | Triage, checks, review queue (67 entries, all `warn`) |
| `data/fy24_*_review_decisions.csv` | Empty decisions files (header only) |

## The code

| File | Change |
|---|---|
| [`code/review_capital_sd.py`](../../code/review_capital_sd.py) | One change: the summary page prints `Less: Rescindments` (a colon). Everything else is config, using the FY2025 switches (`part3_amount_x1_tol`, `workbook_mojibake = "utf-8"`, `c7_hairline_pt`) |
| [`code/review_terms.py`](../../code/review_terms.py) | FY2024 **prints no condition numbers**. Config `numbered = false`: a bold agency line after body text starts the next condition, numbered in book order, and T1 checks the count against the paragraphs that open "As a condition" (61 = 61). Agency lines with no code (`Department of Transportation`, `Mayoralty`), one in regular type (`Office of Criminal Justice ( 128)`), one wrapped over two lines, `[ 003]` / `[ 020 ]` / `Unit of appropriation`. Config `table_pages`: white boxes behind headings (pp.11, 16, 18, 21) read as tables otherwise. New warn checks `T2.no_agency_code`, `T2.heading_not_bold` |
| `config/capital_sd/fy2024.toml`, `config/terms/fy2024.toml` | New |
| [`code/test_review_fy24_capital_terms.py`](../../code/test_review_fy24_capital_terms.py) | 8 FY2024 tests, golden rows read off the rendered pages |

**FY2025, FY2026 and FY2027 output is byte-identical.** All three years' 42 research files were rebuilt
with this code and compared with `cmp` against the committed ones: identical. Every new terms rule is
behind `numbered = false` or `table_pages`, and the regex changes only add forms those years do not print.

## Results

### Capital supporting detail (78 pp., sha256 `c1397177…1cce4`)

**Page map** (all 78 pages agree; none has a /Rotate). p.1 cover · p.2 contents · p.3 divider ·
**pp.4–60 Part I** ("Page 1 of 57") · **p.61 summary** · p.62 divider · **pp.63–69 Part II** · p.70
divider · **pp.71–78 Part III**. Header `PROJECT ID`, as FY2025.

| Check | Result |
|---|---|
| Rows | Part I 1,241; Part II 123; Part III 95 organizations / 113 budget-line rows |
| C1 every `TOTALS FOR` line | **32 / 32 tie** on count and all four FYs, including both `ALL` lines: Part I 1,241 projects, $839,969,000 FY2024 / $6,000,000 FY2025; Part II 123, $158,842,000 / $6,000,000 |
| C2 p.61 summary | Additions $839,969,000 = Part I. Additions − rescindments $189,969,000 = net $650,000,000. No list of the rescindments in this book |
| C3 Part II vs Part I | 93 rows equal a Part I row in every field; 30 are in Part II only: 29 `MA` rows on `0N` lines ($61,737,000) and **`HL TA001` at −$40,000** (critical); all 93 Part I rows on `DN` lines are in Part II. No ID printed twice |
| C4 Part III | 95 / 95 organization lines equal their rows; grand total = Part II; 113 / 113 budget lines agree |
| C5 two reads of each word | 21,348 agree; no page edited after export; 0 disagreements |
| C6 every word in one field | 0 orphans, 0 unplaced words |
| C7 rules | 111 / 111 matched; plus 95 hairlines (0.10–0.17 pt, 50% grey) between Part III organizations, under a pixel at 300 dpi |
| C8 ink coverage | **0 uncovered regions.** Self-test: hiding `AG CN001` (p.4) gives 52 regions |
| C9 Open Data `t474-a92g`, FY2024 | **1,241 / 1,241** non-zero Part I amounts match on (ID, budget line, FY, amount), none left over either side. Borough and title 1,241 / 1,241. Sponsor 1,227 / 1,241 after decoding t474's mojibake (UTF-8 read as cp437, 78 rows); the 14 others: 12 print `TECHNICAL ADJUSTMENT` (t474: "Technical Adjustments"), `ED CN019` (t474 misspells Salamanca as "Salamance"), `PV NC041` (PDF `SPEAKER, POWERS, MANHATTAN DELEGATION`; t474 `Speaker, Manhattan Delegation, Speaker`) |
| vs the retired `data/fy24/capital` CSV | Same 1,364 rows and (ID, budget line) keys; every amount and borough equal. It **dropped the printed comma after `SPEAKER` on 190 rows** (`SPEAKER HUDSON`; p.5 prints `SPEAKER, HUDSON`) and **moved a wrapped sponsor line into the title on 9 rows** (`… SUBSPECIALTIES SUITE DELEGATION`). 15 titles and 4 code cells differ otherwise (spacing, `S:138`). Same swapped column names as FY2025 |

### Terms & Conditions (24 pp., sha256 `32186dc0…1ca5`)

`FY24-Terms-and-Conditions.pdf`. p.1 cover; pp.2–24 conditions; `Page N of 24` at the foot. One ruled
table (pp.8–9).

| Check | Result |
|---|---|
| T1 conditions | 61, numbered here in book order (**the PDF prints no numbers**); 61 paragraphs open "As a condition" at the left margin |
| T2 unit and budget-line lines | 187 / 187 placed (182 units, 5 budget lines). 5 agency lines print no code (#44 DOT, DCAS, Parks; #47 DYCD; #54 Mayoralty); #56's agency name is in regular type, only `( 128)` bold; #61's "Office of Technological Innovation/Department of Information Telecommunication / Services (858)" wraps |
| T3 body names the heading's units | 58 / 61. #34 wraps `HD-` / `0009` across a line end, which T3 reads with a space (the check's limit; the text is right); #46 "units of appropriations" (plural) and #56 "003 and004" (no space) are the PDF's wording |
| T4 characters | 0 outside a condition, the table or page furniture |
| T5 FSR table | both lattices agree on every separator (pp.8 and 9); 29 / 29 cells identical |
| T6 ink | 0 uncovered regions |
| T7 vs the retired `data/fy24/terms` CSV | It has 59 rows for 61 conditions: it **lost the 4 conditions whose heading has no code or is not bold** (#44, #47, #54, #56), folding their text into the condition before, and split #61 into 3 rows ("Services (858)", a blank). From #44 on its numbers no longer line up. 37 texts equal; it also put headings into texts, the FSR table into #21, and dropped printed hyphens (`low-barrier`, `self-placement`) |

## What FY2024 does that FY2025 does not

- **No condition numbers** in the T&C, codeless and non-bold agency headings, white boxes behind headings.
- **An encrypted capital book** (empty user password; copying not permitted by the owner flags).
- **A negative Part II-only row** on an `RN` line: `HL TA001` "SEC249 ADJUSTMENT FOR THE SIUH NORTHWELL
  HEALTH CARDIAC IMAGING PROJ", −$40,000 (p.65). FY2026's `PV MA0005` was also negative.
- **`TA` IDs** (`P TA001`…, `HD TA001`, `ED TA777`): 10 Part I rows, sponsor `TECHNICAL ADJUSTMENT`
  (singular). t474 describes them as budget-line swaps.
- **No post-export edits**, no reused IDs, no two-read disagreements.
- t474's FY2024 accents are **UTF-8 bytes read as cp437** (`Avil├⌐s`); FY2025's were cp1252 (`AvilΘs`).

## How to redo it

```
.venv/bin/python code/review_capital_sd.py --fy 2024          # --no-ink skips C7/C8
.venv/bin/python code/review_capital_sd.py --fy 2024 --selftest-ink --out /tmp/x   # C8 must fire on p.4
.venv/bin/python code/review_terms.py --fy 2024
.venv/bin/python -m pytest code/test_review_fy24_capital_terms.py
```

Same environment as FY2025 (pdfplumber 0.11.10, pypdfium2 5.14.0, Python 3.14.8).

## Not in scope: the Resolution A book

`source/FY24/Fiscal-Year-2024-Changes-To-The-Executive-Capital-Budget-Adopted-by-the-City-Council.pdf`
(86 pp., all landscape, sha256 `cb1f9a4c…dfb4`) is the Resolution A family. AES-256, empty user password
(V5 R6, `/P -1324`): it opens, its text extracts, and its permissions allow copying. No retired parse of
it exists in `data/fy24/capital/`. **Recommendation:** as for FY2025, leave it for one Resolution A pass
across FY2016–FY2025 (`families/capital.md` R2: same grammar every year), checked against OMB; its value
here is the list behind the $189,969,000 of rescindments (p.61).

## Not done

- **OCR audit (PLAN stage 10).** Not run: both PDFs are born-digital with 0 uncovered ink.
- **DATA-ANOMALIES** and **`data/capital/`** are not edited. Proposed text is in `ISSUE-LOG-DRAFT.md`.
- Suggested decisions (`code/build_review_suggestions.py`) and the explorer's decisions-file list
  (`mcp/scripts/pdf-families.mjs`) do not list FY2024 yet.
