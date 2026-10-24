# FY2024 Schedule C, checked from the PDF (#105)

**Report generated:** 2026-10-21 20:20 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** `source/FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf` (sha256
`de122be2…be77a`, 453 pages); expense disclosure as committed in `data/fy24/expense_disclosure/`
(workbook sheet `FY24 (06-08-26)`); code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #105 (epic #101). This folder is the review record. The tables are promoted to
`data/fy24/pdf/schedule_c/` by a separate PR. Same toolkit and method as FY2025
(`research/2026-10-21-fy25-schedule-c-review/`, #104), which this branch stacks on.

FY2024 is the first year the toolkit meets **tables with no vertical rules** and **pages whose
MediaBox does not start at (0, 0)**. Both are handled in shared code, switched on only by
FY2024's config; FY2025, FY2026 and FY2027's outputs are byte-identical with it in place
(checked: every file in their three review folders has the same sha256).

## Results

| What | Result |
|---|---|
| Award rows | **9,291**, **$453,858,561** (body 5,380 / $404,059,561; Appendix A 477 / $5,610,000; B 2,616 / $36,539,000; C 818 / $7,650,000) |
| Printed totals | 24 / 25 category TOTALs tie; 25 / 25 categories' boxes equal their summary lines (10 of them through 15 named aliases); Parks (p.201) prints no summary table; 128 / 133 initiatives' rows equal what their statement designates |
| What didn't tie | **$52,935**: Criminal Justice Services (p.63) prints TOTAL $28,658,710; its 7 lines add to $28,711,645. **Six statements** whose reserve and rows do not make the box: A Greener NYC +$635,000 (p.129), Mental Health Services for Vulnerable Populations −$450,000 (p.181), Autism Awareness +$175,000 (p.176), Access Health +$78,969 (p.148), DoVE −$60,000 (p.109), Food Pantries −$1,000 ("$6.2 million", p.147). The roll-up gap (+$430,904) is exactly these seven. Flagged, not fixed |
| Rows moved by name | **191 rows, $12,028,500** on pp.130–137 (eight landscape pages merged in out of order) belong to NYC Cleanup (box p.145), not to A Greener NYC, whose statement they follow. They add to exactly what NYC Cleanup's statement designates. One critical review row |
| Not in any row | $38,403,539 held "post-adoption" (45 statements of the form "will designate $N post-adoption and has designated the following providers", 4 "will designate post adoption", 1 reserve only, 1 partial); **$35,211,869** designated straight to CUNY (6 initiatives, pp.156–158) or to the four library systems (p.174), with no rows |
| Image grid (independent) | **7,844** rows agree on every field. **1,447** rows sit in tables with no drawn vertical rules, which the image lattice cannot read; for **1,438** of them the pixels' own horizontal rules confirm the row's top and bottom and that no rule runs through it. The other **9** are review rows: 8 first rows with no rule above them (pp.41–46, 152, 153), and 1 row with an empty spacer band (p.122) |
| Ink coverage | 0 uncovered regions on the award pages (1,736 loose px of 274,459,445 ink px). Self-test passes on Medicare Rights Center $100,000 (p.242, a page with a MediaBox offset): hiding the row, or its letter "i", makes the check fire |
| Anchor census | 9,289 EIN-shaped words = 9,289 rows with an EIN, page by page; 2 more rows print EINs that are not EINs ("TF4876222" p.135, "13-294-6970" p.182; named) |
| Characters | 0 characters inside an award table left out of a cell; 0 characters cross a column split in the 70 tables built from horizontal rules |
| The old parse | Nothing the first PDF parse had (`f710a09`, 9,210 rows) is missing; this build has 81 more rows ($6,059,487). Against `data/fy24/schedule_c/` on `main` (9,279 rows, later repaired from the disclosure), 2 differ, both where `main` took the EIN from the disclosure: Drama Club (the PDF prints Digital Girl's EIN, p.261) and Knickerbocker Avenue Merchants Partnership (the PDF prints "TF4876222", p.135). 14 rows ($3,513,614) are new |
| DATA-ANOMALIES §20 | The old parse's one merged FY2024 row comes back as two awards: Corbin Hill Food Project and Council For Unity, Inc., $50,000 each, p.234 |
| Disclosure (report only) | 9,038 rows match on (EIN, amount); 9,023 with the City-EIN name rule. No prototype floor for this year |
| Review file | **39 rows**, 11 critical; largest $12,028,500 (the page move) |

## What FY2024 does that FY2025 doesn't

Each is a switch or list in `config/schedule_c/fy2024.toml` with the pages it came from; the code
is shared. Each switch changes FY2024's output when turned off (checked one by one).

1. **MediaBox offset** (216 pages, pp.227–254 and 266–453: MediaBox `[-18.03 17.97 773.97
   629.97]`). pdfplumber reports coordinates from the PDF's origin; the page renders from the
   MediaBox corner. Every coordinate is now taken from the MediaBox corner
   (`code/schedc/vector.py` `origin`, `shift`), for cells, text, rules and ink. This is always
   on: on a page that starts at (0, 0) it is a no-op, which is why the other years are
   unchanged. `bbox_pt` in the output is from the MediaBox's top-left corner, as a viewer draws
   the page.
2. **Tables ruled with horizontal lines only** (70 tables on 53 pages, e.g. pp.35–39, 63–66,
   149, 161): a rule under each row, none between columns (`hrule_tables`). Rows come from
   the drawn rules; columns are split at the leftmost EIN word and halfway between the EIN and
   amount words. A check fails if any character crosses a split (none does). Lines-strategy
   "tables" that are only white-filled boxes (p.161), or whose EIN rows have no amount cell
   (p.69), are replaced. The image side cannot see these tables; it checks their row bands
   against the pixels' rules instead (`band_check`, `imagegrid.check_bands`).
3. **A first row with no rule above it** (pp.41–46, 152–153): read as a row when its band holds
   an EIN and an amount (`open_top_rows`). Each is a critical review row, because no rule
   confirms its top.
4. **Headers printed as loose text above the table** (pp.148, 149, 155, 169, 264, 265), and
   once only "EIN  Amount" (p.265) (`loose_header`), and **headers printed at the bottom** of
   the table (pp.41–45), read with the header carried from the page before
   (`headerless_continuation`, `carry_header` on the image side, as FY2026).
5. **Two boxes in one table, the second under the first box's award rows** (p.122, SAVE)
   (`split_boxes_after_rows`); **"Designation Method:" alone in a cell**, its text outside the
   cells (p.217) (`statement_loose_text`).
6. **Eight landscape pages merged out of order** (pp.130–137): their rows are NYC Cleanup's
   (`[[initiative_pages]]`). Every moved row is flagged `H12.initiative_pages`.
7. **71 statement wordings**, including a reserve with rows but no designated amount
   ("will designate $N post-adoption and has designated the following providers", 45 boxes; new
   kind `reserve_rows`: rows = box − reserve), two designated amounts in one statement
   (p.147), "allocated directly to the City University of New York", and "Fiscal 2023" typos.
8. **Smaller type** on the Speaker's pages (8.8 pt): the ink check's region floor is 48 px, not
   64, so a dropped letter "i" (61 px) is still seen.

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars |
| `ISSUE-LOG-DRAFT.md` | #105 issue-log comments, drafted, **not posted** |
| `data/fy24_sc_awards.csv` | Every award row, same columns as FY2025 (`lattice` adds `vector+bands` for rows checked by pixel rules) |
| `data/fy24_sc_initiatives.csv` | 148 initiatives: box amount, designation statement and its kind, reserve, rows and their sum |
| `data/fy24_sc_categories.csv` | The 25 category summary tables, line by line, with TOTALs |
| `data/fy24_sc_review.csv` | The review file (same columns as `fy26_sc_review.csv`) |
| `data/fy24_sc_checks.txt` | Every check and its numbers |
| `data/fy24_sc_flags.csv` | Every flag, including routine warns |
| `data/fy24_sc_pages.csv` | Per page: tables, award rows, EIN words, image lattice and ink numbers |
| `data/fy24_sc_disclosure_match.csv` | Each PDF row's disclosure partner or the reason it has none |
| `data/fy24_sc_manifest.json` | Input hashes and tool versions |
| `data/overlays/` | Page crops for the 9 image-side review rows |

There is no `fy24_sc_review_decisions.csv` yet: Noel writes it (the pipeline never does).

## How to redo it

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r code/requirements.txt -r code/requirements-cv.txt pytest
.venv/bin/python code/parse_schedule_c_v2.py --fy 2024      # ~1 min on a laptop CPU
for y in 2025 2026 2027; do .venv/bin/python code/parse_schedule_c_v2.py --fy $y; done   # must not change
.venv/bin/python -m pytest code/test_schedc.py
```

Same tool versions as FY2025 (Python 3.12.13, pdfplumber 0.11.10, pypdfium2 5.14.0, OpenCV
4.14.0, numpy 2.5.4). The run is byte-identical on re-run (checked).

## What these checks cannot prove

- For the 1,438 rows checked only by pixel rules, the **text** of each field is read once, from
  the text layer, with columns split by rule of thumb (the EIN and amount words). The pixels
  confirm the rows, the EIN census and the "nothing crosses a split" check confirm the columns,
  and every row the first PDF parse had is here; but no second reader read those fields.
  *Update 2026-10-23 (#193):* the image side now finds these tables' columns itself (the header's
  labels and the blank strips between them, `imagegrid.pixel_columns`) and reads all 1,438 a
  second time: all agree on every field (`image_check` `columns_agree`, `lattice`
  `vector+columns`). Like the image lattice it reads the PDF's text layer, so a text-layer error
  still passes both.
- That the eight landscape pages belong to NYC Cleanup is an inference from their content and
  their sum, not something the PDF says. It is the largest review row.
- Which side is right where the PDF disagrees with itself (pp.63, 109, 129, 147, 148, 176, 181).
- That an award exists which the PDF never printed; text both grids read the same wrong way.

## Not done here

- OCR audit (PLAN stage 10): docTR is not installed.
- Nothing added to the MCP or the public site.
