# FY2025 Schedule C, checked from the PDF (#104)

**Report generated:** 2026-10-21 19:15 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** `source/FY25/Fiscal-2025-Schedule-C-MERGE-FINAL-2.pdf` (sha256
`71b7dfc2…c196`, 455 pages); expense disclosure as committed in `data/fy25/expense_disclosure/`
(workbook sheet `FY25 (09-14-26)`); code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #104 (epic #101). This folder is the review record. The tables are promoted to
`data/fy25/pdf/schedule_c/` by a separate PR. Same toolkit and method as FY2027
(`research/2026-10-20-fy27-schedule-c-review/`, #102) and FY2026
(`research/2026-10-21-fy26-schedule-c-review/`, #103). FY2025 needed nine new switches and two
new config lists, all off for FY2026 and FY2027; both years' outputs are byte-identical with them
in place (checked: every file in both review folders, overlays included, has the same sha256).

## Results

| What | Result |
|---|---|
| Award rows | **9,579**, **$471,876,698** (body 5,659 / $422,077,698; Appendix A 470 / $5,610,000; B 2,616 / $36,539,000; C 834 / $7,650,000) |
| Printed totals | 24 / 25 category TOTALs tie; 25 / 25 categories' boxes equal their summary lines (9 of them through 16 named aliases); the 26th category, Parks (p.202), prints no summary table; 130 / 133 initiative row sums equal what the statement says they designated |
| What didn't tie | **$50,000**: Education (p.115) prints TOTAL $39,924,300; its 12 lines add to $39,974,300. **$594,000**: CASA (p.64) "will designate $2,066,000 … and has designated $14,680,000" adds to $16,746,000, not its $17,340,000 box. **$27,000**: Immigrant Opportunities (p.167) says "has designated $2,562,000"; its 31 rows add to $2,535,000. The roll-up gap is exactly these three (−$571,000). Two statements are wrong but net to zero: Pride at Work (p.222) says "$3.2 million" for a $501,000 box; Combat Sexual Assault (p.60) rounds $4,091,000 to "$4.1 million". Flagged, not fixed |
| Not in any row | $81,921,615 held "post-adoption" (16 initiatives "will designate awards post-adoption", $50,455,000, and $31,466,615 in partial reserves); **$35,711,869** designated straight to CUNY/DOE (7 initiatives, pp.155–157) or to the four library systems (p.174), with no rows printed |
| Image grid (independent) | **9,577 / 9,579** rows agree on every field. 2 differ (a name's hyphen over the EIN border, pp.334, 407: the vector side is right, as in FY2026) |
| Ink coverage | 0 uncovered regions on the award pages (30 loose px of 276,778,130 ink px). Self-test passes on Bronx Defenders $5,533,333 (p.169): hiding the row, or its letter "f", makes the check fire. A lone comma is below the check's floor (written in `checks.txt`) |
| Anchor census | 9,578 EIN-shaped words = 9,578 rows with an EIN, page by page; 1 more row prints a malformed EIN (named) |
| Characters | 0 characters inside an award table left out of a cell |
| The 13 rows the old parser lost ($9,092,588) | All in the data, e.g. Bronx Defenders $5,533,333 (`fy25-p169-t01-r001`, under New York Immigrant Family Unity Project, the box above it on p.169). Nothing the old parse had is missing (multiset of EIN and amount, against `data/fy25/schedule_c/` on `main`) |
| DATA-ANOMALIES §20 | The old parse's one merged FY2025 row comes back as two awards: Corbin Hill Food Project $50,000 (its "farm shares" purpose) and Council For Unity, Inc. $50,000, p.233 |
| Disclosure (report only) | 9,385 rows match on (EIN, amount); the 2026-10-19 prototype matched 9,386. The one less is Safe Horizon $150,000 (p.181), whose EIN is printed "13-294-6970" and is left blank here. 9,368 with the City-EIN name rule |
| Review file | **39 rows**, 2 critical; largest $2,749,000 (a statement, not a row) |

The 2026-10-19 prototype (scratch, BetaNYC working notes) got 9,579 rows and $471,876,698. This
build gets the same from committed code.

## What FY2025 does that FY2026 doesn't

Each is a switch or list in `config/schedule_c/fy2025.toml` with the page it came from; the code
is in `code/schedc/` and `code/schedc_cv/`, shared. Turning any switch off changes FY2025's
output (checked one by one). Two FY2026 switches are not needed and are off.

1. **A header in two row bands**, "Council" over "Member" (pp.131–144, 14 tables)
   (`header_two_bands`). The joined labels must all be known, or it stays a flag.
2. **A box title's first letter drawn apart**: in its own narrow cell (p.149 "E" | "nding the
   Epidemic", p.258 "V" | "eteran…"), or just left of the table's rule (p.36 "D" + "igital
   Inclusion…") (`box_title_letters`). The box-vs-summary check confirms each title.
3. **An amount's last digit past its rule**: into a white-filled phantom column (p.222, 5 rows,
   "$200,00" | "0") or past the table edge (p.260 box "$250,00" + "0")
   (`amount_sliver_join`). Each is a review row.
4. **Amounts with cents or a trailing period** (p.168 "$77,000.00", p.170 "$50,000.")
   (`amount_odd_format`). Each is a review row.
5. **A row cut into more cells than its header** (p.183, 2 rows): the name sits left of the
   header's centre (`header_span_cells`).
6. **A second box inside the first box's table** (p.35 "Adult Literacy Pilot Project")
   (`split_boxes`), and **a box amount cut into three cells** (p.157 "$" | "5" | "00,000")
   (`box_amount_cells`, a review row).
7. **A statement inside a description cell** (p.168, after "Scope of Service")
   (`statement_in_cell`).
8. **A page whose name column the default table finder loses** (p.167: the left rule sits 3 pt
   from the box above it and is snapped onto it). Read with a 1 pt snap on that page only
   (`[[vector_pages]]`).
9. **Statements in millions**, "$4.1 million" (9 initiatives), read at face value, so a rounded
   one fails and is a review row; two typos kept as printed ("The City Council for Fiscal 2025
   and will designate", p.60; "has designated and has designated", p.129); Libraries say "This
   funding is directly allocated to the … Library" (p.174).
10. **17 summary-table titles**, one table with no title (p.59), and **one category with no
    summary table at all** (Parks, p.202; `[[no_summary]]`, a review row). Its box stands in
    for the TOTAL in the roll-up.
11. **"Institute" as the name column's header** (p.156), on both sides (`extra_roles` for the
    image grid).
12. **26 categories**, two FY2026 does not have (Libraries; Mental Health, not "Mental Health
    Services"), and "Cultural Organization", singular.

Shared code changes, all inert on FY2026 and FY2027: per-page pdfplumber table settings
(`vector.read_page`); a `None`-safe money format in messages (a box amount the parse cannot
read no longer crashes the run); a skipped empty band under a statement; review ids for two
box aliases on one page (the box title becomes the `field`).

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars |
| `ISSUE-LOG-DRAFT.md` | #104 issue-log comments, drafted, **not posted** |
| `data/fy25_sc_awards.csv` | Every award row. Contract columns (`fiscal_year`, `source_pdf`, `pdf_sha256`, `pdf_page`, `bbox_pt`, `review_id`, `flags`), clean values, the printed text (`*_raw`, `*_printed`), image-check result, disclosure match |
| `data/fy25_sc_initiatives.csv` | 160 initiatives: box amount, designation statement and its kind, reserve, rows and their sum |
| `data/fy25_sc_categories.csv` | The 25 category summary tables, line by line, with TOTALs |
| `data/fy25_sc_review.csv` | The review file (same columns as `fy26_sc_review.csv`) |
| `data/fy25_sc_checks.txt` | Every check and its numbers |
| `data/fy25_sc_flags.csv` | Every flag, including routine warns (67 line-end hyphens kept as printed) |
| `data/fy25_sc_pages.csv` | Per page: tables, award rows, EIN words, image lattice and ink numbers |
| `data/fy25_sc_disclosure_match.csv` | Each PDF row's disclosure partner or the reason it has none; each disclosure-only row with a reason |
| `data/fy25_sc_manifest.json` | Input hashes and tool versions |
| `data/overlays/` | Page crops for the 2 image-grid rows |

There is no `fy25_sc_review_decisions.csv` yet: Noel writes it (the pipeline never does).

## How to redo it

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r code/requirements.txt -r code/requirements-cv.txt pytest
.venv/bin/python code/parse_schedule_c_v2.py --fy 2025      # ~1 min on a laptop CPU
.venv/bin/python code/parse_schedule_c_v2.py --fy 2026      # must leave FY2026's files unchanged
.venv/bin/python code/parse_schedule_c_v2.py --fy 2027      # must leave FY2027's files unchanged
.venv/bin/python -m pytest code/test_schedc.py
```

Run with Python 3.12.13, pdfplumber 0.11.10, pypdfium2 5.14.0, OpenCV 4.14.0, numpy 2.5.4 (the
FY2026 run's versions). The run is byte-identical on re-run (checked). Running FY2026 on
`main` today also rewrites `fy26_sc_review.csv`, filling its `decision` column from the decisions
file Noel committed after it; that is not a change from this branch.

## What these checks cannot prove

- That an award exists which the PDF never printed.
- Text where both grids read the same wrong text layer.
- Which side is right where the PDF disagrees with itself (pp.60, 64, 115, 167, 222).
- That "$4.1 million" (p.60) meant $4,091,000. The rows and the box say so; the statement does not.
- Which disclosure row is "the" match when several share a key (1,592 disclosure rows).

PLAN open decision 4 mentions FY2025 purpose text clipped on screen but whole in the text layer.
No award cell here has text running past its cell's edge (scanned), so none is in the review file.

## Not done here

- OCR audit (PLAN stage 10): docTR is not installed; the PDF is born-digital and ink coverage
  is clean.
- Nothing added to the MCP or the public site.
