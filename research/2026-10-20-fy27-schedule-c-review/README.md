# FY2027 Schedule C, checked from the PDF (#102)

**Report generated:** 2026-10-20 22:35 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** `source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf` (sha256 `63c03739…d955`,
498 pages); expense disclosure as committed in `data/fy27/expense_disclosure/` (retrieved
2026-10-12); code at this branch's commit.
**Status:** checked, review in progress. Every check passes or is a named, listed exception.
Noel has not signed off the review file yet.

Part of #102 (epic #101). This folder is the review record. The tables are promoted to
`data/fy27/pdf/schedule_c/` by a separate PR. The capital and Terms & Conditions PDFs are in
`research/2026-10-20-fy27-capital-terms-review/` (PR #122).

## Results

| What | Result |
|---|---|
| Award rows | **9,979**, **$655,045,412** (body 6,119 / $605,246,412; Appendix A 467 / $5,610,000; B 2,558 / $36,539,000; C 835 / $7,650,000) |
| Printed totals | 25 / 25 category TOTALs tie; 25 / 25 categories' boxes equal their summary lines; 169 / 170 initiatives' rows equal what their statement says they designated |
| What didn't tie | **$1**: Support Our Older Adults (p.214) says "has designated $7,229,999"; its 394 rows add to $7,229,998. It is the only gap in the roll-up (category TOTALs $655,764,999 = body rows $605,246,412 + post-adoption reserves $50,518,586 + $1). Flagged, not fixed |
| Image grid (independent) | 9,978 / 9,979 rows agree on every field. The one that doesn't is p.463 (below) |
| Ink coverage | 0 uncovered regions on the 486 pages with award rows. Self-test passes: hiding the Medicare Rights row, or one letter of it, makes the check fire |
| Anchor census | 9,979 EIN-shaped words on the pages = 9,979 rows, page by page |
| Characters | 0 characters inside an award table left out of a cell |
| Medicare Rights Center $135,000 (p.279) | In the data (`fy27-p279-t00-r012`). The old parser dropped it |
| Disclosure (report only) | 9,850 rows match on (EIN, amount) with the City-EIN name rule; 9,859 without it (the prototype's number) |
| Review file | **6 rows**, largest $9,000 |

The 2026-10-19 prototype (scratch, BetaNYC working notes) got the same 9,979 rows and
$655,045,412. This build reproduces it from committed code.

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars |
| `ISSUE-LOG-DRAFT.md` | #102 issue-log comments, drafted, **not posted** |
| `data/fy27_sc_awards.csv` | Every award row. Contract columns (`fiscal_year`, `source_pdf`, `pdf_sha256`, `pdf_page`, `bbox_pt`, `review_id`, `flags`), clean values, the printed text (`*_raw`, `*_printed`), image-check result, disclosure match |
| `data/fy27_sc_initiatives.csv` | 170 initiatives: box amount, designation statement and its kind, reserve, rows and their sum |
| `data/fy27_sc_categories.csv` | The 25 category summary tables, line by line, with TOTALs |
| `data/fy27_sc_review.csv` | The review file (schema: PLAN §5.3, plus `dollar_impact`) |
| `data/fy27_sc_review_decisions.csv` | Noel's decisions, by `review_id`. The pipeline never writes it |
| `data/fy27_sc_checks.txt` | Every check and its numbers |
| `data/fy27_sc_flags.csv` | Every flag, including routine warns (80 line-end hyphens kept as printed) |
| `data/fy27_sc_pages.csv` | Per page: tables, award rows, EIN words, image lattice and ink numbers |
| `data/fy27_sc_disclosure_match.csv` | Each PDF row's disclosure partner or the reason it has none; each disclosure-only row with a reason |
| `data/fy27_sc_manifest.json` | Input hashes and tool versions |
| `data/overlays/` | Page crops for flagged rows |

## How to redo it

```
python3 -m venv .venv
.venv/bin/pip install -r code/requirements.txt -r code/requirements-cv.txt
.venv/bin/python code/parse_schedule_c_v2.py --fy 2027      # ~2 min on a laptop CPU
.venv/bin/python -m pytest code/test_schedc.py
```

The run is byte-identical on re-run (checked). Every year-specific fact is in
`config/schedule_c/fy2027.toml`; the code in `code/schedc/` and `code/schedc_cv/` is shared and
meant for the next years (PLAN §7).

## How it works (PLAN §3)

1. **Vector grid.** pdfplumber finds each table from the PDF's own drawn borders. Each
   character goes to the one cell holding its centre (Christian Moscardi's `assign_words`
   rule, applied to PDF characters).
2. **Structure** by page position, never text order: category banner → summary table →
   initiative box → designation statement → rows. Rows attach to the last box above them.
3. **Image grid.** The page is rendered at 300 dpi; Christian's `code/ocr/grid.py` finds each
   table's rules from the pixels (`kernel_px=60`, from PR #99), one table region at a time.
   Rows are rebuilt from that grid alone and compared field by field.
4. **Ink coverage.** Every dark pixel inside an award table must be under a character we
   emitted, a header label, or a drawn rule. Ported from Christian's
   `nyc_executive_orders/vlm_ocr.py` (`find_uncovered_regions`, `_tight_bbox`).
5. **Printed totals**: category TOTALs, box vs summary lines, each initiative's rows vs its
   statement (full / partial / post-adoption only), and the roll-up.
6. **Disclosure**, report only: (EIN, amount) multiset, City EIN needs a name match.

## What these checks cannot prove

- That an award exists which the PDF never printed.
- Text where both grids read the same wrong text layer (p.486). Only pixels or a person can.
- Which side is right where the PDF disagrees with itself (p.214's $1).
- Which disclosure row is "the" match when several share a key (994 disclosure rows).

## Not done here

- OCR audit (PLAN stage 10): docTR is not installed; the PDF is born-digital and ink coverage
  is clean. The p.486 note comes from the 2026-10-19 prototype's OCR sample.
- Review UI (stage 11). The review file links rows by `pdf_page` and `bbox_pt`.
- Nothing added to the MCP or the public site.
