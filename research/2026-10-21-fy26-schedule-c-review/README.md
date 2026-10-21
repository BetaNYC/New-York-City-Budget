# FY2026 Schedule C, checked from the PDF (#103)

**Report generated:** 2026-10-21 00:40 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** `source/FY26/Fiscal-2026-Schedule-C-4.pdf` (sha256 `58532138…b074`,
469 pages); expense disclosure as committed in `data/fy26/expense_disclosure/` (workbook sheet
`FY26 (09-14-26)`); code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #103 (epic #101). This folder is the review record. The tables are promoted to
`data/fy26/pdf/schedule_c/` by a separate PR. Same toolkit and method as FY2027
(`research/2026-10-20-fy27-schedule-c-review/`, #102); FY2026 needed eight year-specific
switches (all off for FY2027) and three small rules that never fire on FY2027; FY2027's output
is byte-identical with them in place (checked).

## Results

| What | Result |
|---|---|
| Award rows | **9,765**, **$545,669,395** (body 5,850 / $495,870,395; Appendix A 473 / $5,610,000; B 2,619 / $36,539,000; C 823 / $7,650,000) |
| Printed totals | 24 / 25 category TOTALs tie; 25 / 25 categories' boxes equal their summary lines (10 of them through 11 named aliases); 131 / 132 initiative row sums equal what the statement says they designated |
| What didn't tie | **$800**: Immigrant Services (p.173) prints TOTAL $86,091,341; its 8 lines add to $86,092,141. **$15,000**: Cultural Immigrant Initiative (p.98) says "has designated $6,798,000"; its 383 rows add to $6,783,000. The roll-up gap is exactly these two (−$14,200). Flagged, not fixed |
| Not in any row | $78,512,162 in 14 initiatives "will designate awards post-adoption"; $66,771,395 in other post-adoption reserves; **$23,911,869** designated straight to CUNY/DOE with no rows printed (8 initiatives, pp.162–164) |
| Image grid (independent) | 9,761 / 9,765 rows agree on every field. 2 differ (a name's hyphen over the EIN border, pp.344, 421: the vector side is right); 2 are one-row tables the image grid cannot see (pp.48, 157) |
| Ink coverage | 0 uncovered regions on the award pages. Self-test passes on Bronx Defenders $5,533,333 (p.176): hiding the row, or its letter "f", makes the check fire. A lone comma is below the check's floor (written in `checks.txt`) |
| Anchor census | 9,763 EIN-shaped words = 9,763 rows with an EIN, page by page; 2 more rows print 8-digit EINs (named) |
| Characters | 0 characters inside an award table left out of a cell |
| The 13 rows the old parser lost ($8,588,150) | All in the data, e.g. Bronx Defenders $5,533,333 (`fy26-p176-t00-r003`). Nothing the old parse had is missing |
| Disclosure (report only) | 9,529 rows match on (EIN, amount): the 2026-10-19 prototype's number exactly. 9,510 with the City-EIN name rule |
| Review file | **28 rows**, 4 critical; largest $417,203 |

The 2026-10-19 prototype (scratch, BetaNYC working notes) got 9,765 rows. This build gets the
same count from committed code, and the same disclosure match.

## What FY2026 does that FY2027 doesn't

Each is a switch in `config/schedule_c/fy2026.toml` with the page it came from; the code is in
`code/schedc/` and `code/schedc_cv/`, shared.

1. **One table for box + statement + rows** (portrait pages, e.g. p.36). Split at the award
   header; the statement rows become text (`split_merged_tables`).
2. **A rule between the two lines of a long name** (p.130 "…Washington Heights" / "and
   Inwood"). The second band joins the row above, flagged (`continuation_rows`, 8 rows; and 1
   empty sliver band under a two-line amount, p.48).
3. **Award tables that continue over a page without a header** (pp.48, 157, 195; 6 rows). Read
   with the last header, flagged (`headerless_continuation`); the image side does the same with
   its own last header (`carry_header`).
4. **Box titles that wrap, amount on the second line** (p.157 Healthy Beginnings), and **title
   and amount in one cell** (pp.218, 220).
5. **Two summary tables with other titles** ("Fiscal 2026 Food Initiatives" p.153, "…Higher
   Education Initiatives" p.162).
6. **60 wordings of the designation statement**, three new kinds: "will designate awards
   post-adoption" (no amount), "has designated $N to the following providers", "designated
   directly to the City University of New York". The text layer splits words ("h as",
   "designate d"); the patterns allow exactly those.
7. **First letters in a 5 pt sliver cell** (p.162: "D" | "esignation Method:"), put back.
8. **An amount printed without "$"** (p.111, "75,000"), and **an unmapped glyph** (6 of them, 5 rows)
   (`(cid:9)`, shown as an empty box on p.344), dropped from the clean value, kept in raw.
9. **Box and summary names differ** in 11 places (`&` vs `and`, a dropped ")", one summary line
   for three SAVE boxes). Named aliases; each is a review row.

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars |
| `ISSUE-LOG-DRAFT.md` | #103 issue-log comments, drafted, **not posted** |
| `data/fy26_sc_awards.csv` | Every award row. Contract columns (`fiscal_year`, `source_pdf`, `pdf_sha256`, `pdf_page`, `bbox_pt`, `review_id`, `flags`), clean values, the printed text (`*_raw`, `*_printed`), image-check result, disclosure match |
| `data/fy26_sc_initiatives.csv` | 159 initiatives: box amount, designation statement and its kind, reserve, rows and their sum |
| `data/fy26_sc_categories.csv` | The 25 category summary tables, line by line, with TOTALs |
| `data/fy26_sc_review.csv` | The review file (schema: PLAN §5.3, plus `dollar_impact`) |
| `data/fy26_sc_checks.txt` | Every check and its numbers |
| `data/fy26_sc_flags.csv` | Every flag, including routine warns (85 line-end hyphens kept as printed) |
| `data/fy26_sc_pages.csv` | Per page: tables, award rows, EIN words, image lattice and ink numbers |
| `data/fy26_sc_disclosure_match.csv` | Each PDF row's disclosure partner or the reason it has none; each disclosure-only row with a reason |
| `data/fy26_sc_manifest.json` | Input hashes and tool versions |
| `data/overlays/` | Page crops for the 4 image-grid rows |

There is no `fy26_sc_review_decisions.csv` yet: Noel writes it (the pipeline never does).

## How to redo it

```
python3 -m venv .venv
.venv/bin/pip install -r code/requirements.txt -r code/requirements-cv.txt
.venv/bin/python code/parse_schedule_c_v2.py --fy 2026      # ~1 min on a laptop CPU
.venv/bin/python code/parse_schedule_c_v2.py --fy 2027      # must leave FY2027's files unchanged
.venv/bin/python -m pytest code/test_schedc.py
```

The run is byte-identical on re-run (checked).

## What these checks cannot prove

- That an award exists which the PDF never printed.
- Text where both grids read the same wrong text layer.
- Which side is right where the PDF disagrees with itself (p.98's $15,000, p.173's $800).
- That a one-row table carried over a page break (pp.48, 157) is right: only the vector grid
  sees it. The EIN census and ink coverage do cover those rows.
- Which disclosure row is "the" match when several share a key (1,737 disclosure rows).

## Not done here

- OCR audit (PLAN stage 10): docTR is not installed; the PDF is born-digital and ink coverage
  is clean.
- Review UI (stage 11). The review file links rows by `pdf_page` and `bbox_pt`.
- Nothing added to the MCP or the public site.
