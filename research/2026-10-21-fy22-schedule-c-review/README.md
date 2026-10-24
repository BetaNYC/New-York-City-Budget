# FY2022 Schedule C, checked from the PDF (#107)

**Report generated:** 2026-10-21 23:50 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** `source/FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf` (sha256
`2c444f83…f1`, 326 pages); expense disclosure as committed in `data/fy22/expense_disclosure/`;
code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #107 (epic #101). This folder is the review record. The tables are promoted to
`data/fy22/pdf/schedule_c/` by a separate PR. Same toolkit and method as FY2023
(`research/2026-10-21-fy23-schedule-c-review/`, #106), which this branch stacks on.

FY2022 is close to FY2023 in layout (no MediaBox offset, Word 2016). Three things are new: a
four-column table with a "Program" column (Art as a Catalyst for Change, pp.84–85, 40 rows the
old parse lost), award rows drawn as one wide cell each (pp.117–118), and a summary TOTAL printed
"TOTAL:" (p.32). Three new switches handle them in shared code, each switched on only by
FY2022's config. FY2023, FY2024, FY2025 and FY2027's outputs are byte-identical with them in
place; FY2026's too, except the 4 decision cells a re-run fills from its committed decisions file
(as in FY2023's README).

## Results

| What | Result |
|---|---|
| Award rows | **5,732**, **$285,155,968** (body 1,550 / $235,356,968; Appendix A 510 / $5,610,000; B 2,790 / $36,539,000; C 882 / $7,650,000) |
| Printed totals | **25 / 25** category TOTALs tie; 25 / 25 categories' boxes equal their summary lines (10 of them through 16 named aliases); 90 of 100 initiatives' rows equal what their statement designates, 31 reserve-only boxes print no rows, 11 / 11 stated sums add up |
| What didn't tie | **Eleven places the PDF disagrees with itself or rounds** (named exceptions, none corrected): six statements that hold a reserve while their rows add to the whole box (LGBT Community Services +$1,100,000 and Trans Equity Programs +$1,000,000, p.34; Sex Trade +$290,000, p.39; City's First Readers +$1,650,000, p.44; Crisis Management System +$1,000,000, p.85; Afterschool Enrichment +$1,421,769, p.119); three whose reserve and rows make neither (Ending the Epidemic +$246,046, p.54; Viral Hepatitis +$53,880, p.58; Dedicated Contraceptive Fund −$3,150, p.115); one rounded statement ("$3 million", p.36); **one box that prints a different amount from its summary line**, Public Health Funding Backfill $4,467,933 vs $4,667,933 (p.57 vs p.52). The roll-up gap (+$6,545,340) is exactly these |
| Appendices | No printed total; each equals its fixed pot (DATA-ANOMALIES §19) to the dollar: **$5,610,000 / $36,539,000 / $7,650,000** |
| Not in any row | $203,090,898 held post-adoption ($91,151,096 stated reserves in 53 boxes, including p.65's $220,000 allocated straight to HPD and DCA; 23 boxes held whole, $111,939,802); $33,826,369 designated straight to CUNY (5 initiatives), DOE (p.117) or the four library systems (pp.75–76), with no rows |
| Image grid (independent) | **5,616** rows agree on every field. **108** rows sit in tables with no drawn vertical rules; for **106** the pixels' own horizontal rules confirm the row's top and bottom. The other **10** rows, and **2** image-only rows (the same rows, read without their extra band), are review rows: a name's second line in its own ruled band, or an empty spacer band before a black box bar, joined to the row (e.g. pp.42, 81, 90, 117) |
| Ink coverage | 0 uncovered regions on the award pages (0 loose px of 173,743,942 ink px). Self-test passes on Society of the Educational Arts, Inc. (SEA) $18,000 (p.84), in the four-column table the old parse lost |
| Anchor census | 5,727 EIN-shaped words = 5,727 rows with an EIN, page by page; 5 more rows print EINs of the wrong length (named: one 10-digit, four 8-digit) |
| Characters | 0 characters inside an award table left out of a cell; 0 characters cross a column split in the 4 tables built from horizontal rules |
| The old parse | Nothing the first PDF parse had (`f710a09`, 5,661 rows) is missing; this build has 71 more rows ($13,595,025), all in the body, including Art as a Catalyst for Change (40 rows, $720,000). Against `data/fy22/schedule_c/` on `main` (5,674 rows), nothing is missing and 58 rows ($12,800,025) are new |
| DATA-ANOMALIES §20 | No FY2022 row is listed there |
| Disclosure (report only) | 5,555 rows match on (EIN, amount); 5,571 without the City-EIN name rule. 177 PDF rows ($22,364,486) have no disclosure row. No prototype floor for this year |
| Review file | **47 rows**, 13 critical; largest $1,200,000 (Hetrick-Martin, p.81) |

## What FY2022 does that FY2023 doesn't

Each is a switch or list in `config/schedule_c/fy2022.toml` with the pages it came from; the code
is shared. Each switch changes FY2022's output when turned off (checked one by one).

1. **A fourth column, "Program", between EIN and Amount** in an h-rule table (pp.84–85, Art as a
   Catalyst for Change: 40 awards of $18,000, each naming the school it serves)
   (`hrule_extra_column`). The column is read into `purpose` (header label "Program"); the
   header is printed over two bands in the box table above (`header_two_bands`, FY2025's), and
   p.85 carries it over (`headerless_continuation`).
2. **Award rows drawn as one wide cell each**, rules and an outer border only (pp.117–118, Young
   Women's Leadership Development, 24 rows) (`split_one_cell_rows`): cut at the EIN and amount
   words, as h-rule tables are.
3. **"TOTAL:" with a colon** (p.32, Community Development) (`total_colon`).
4. **Statements**: 74 wordings (138 statements). New: "$3,462,000 million" (p.37, read as
   $3,462,000; a review row); two amounts "allocated directly" to HPD and DCA beside the providers
   (p.65; `reserve...` groups now add up in `structure.statement_kind`, as `designated...` groups
   already did); statements with no final "." (pp.92–96).
5. From FY2023: `box_amount_dollar_space` (p.37 "Discharge Planning | $ 250,000"),
   `split_boxes_award_tables` (p.81). From FY2025: `box_title_letters` (p.54 "E" | "nding the
   Epidemic"). FY2023's `hrule_beside`, `hrule_header_split`, `sliver_chars`, `loose_header`,
   `statement_loose_text`, `box_amount_without_dollar` are off (no effect).
6. **The ink self-test row** is the table's second row: the ink check takes a table's first row
   as its header (see "cannot prove").

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars |
| `ISSUE-LOG-DRAFT.md` | #107 issue-log comments, drafted, **not posted** |
| `data/fy22_sc_awards.csv` | Every award row, same columns as FY2024 |
| `data/fy22_sc_initiatives.csv` | 141 initiatives: box amount, designation statement and its kind, reserve, rows and their sum |
| `data/fy22_sc_categories.csv` | The 25 category summary tables, line by line, with TOTALs |
| `data/fy22_sc_review.csv` | The review file (same columns as `fy24_sc_review.csv`) |
| `data/fy22_sc_checks.txt` | Every check and its numbers |
| `data/fy22_sc_flags.csv` | Every flag, including routine warns |
| `data/fy22_sc_pages.csv` | Per page: tables, award rows, EIN words, image lattice and ink numbers |
| `data/fy22_sc_disclosure_match.csv` | Each PDF row's disclosure partner or the reason it has none |
| `data/fy22_sc_manifest.json` | Input hashes and tool versions |
| `data/overlays/` | Page crops for the 12 image-side review rows |

There is no `fy22_sc_review_decisions.csv` yet: Noel writes it (the pipeline never does).

## How to redo it

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r code/requirements.txt -r code/requirements-cv.txt pytest
.venv/bin/python code/parse_schedule_c_v2.py --fy 2022      # under 1 min on a laptop CPU
for y in 2023 2024 2025 2026 2027; do .venv/bin/python code/parse_schedule_c_v2.py --fy $y; done   # must not change
.venv/bin/python -m pytest code/test_schedc.py
```

Same tool versions as FY2023. The run is byte-identical on re-run (checked, overlays included).

## What these checks cannot prove

- For the 106 rows checked only by pixel rules, the **text** of each field is read once, from the
  text layer. The pixels confirm the rows, the EIN census and the "nothing crosses a split" check
  confirm the columns; no second reader read those fields.
  *Update 2026-10-23 (#193):* the image side now finds these tables' columns itself (the header's
  labels and the blank strips between them, `imagegrid.pixel_columns`) and reads 100 of them a
  second time: all agree on every field (`image_check` `columns_agree`, `lattice`
  `vector+columns`). The other 6 (pp.60–61) are read by the image lattice itself once the config
  names their "Institute" header, and agree. Like the image lattice it reads the PDF's text layer,
  so a text-layer error still passes both.
- **The ink check treats a table's first row as its header.** For a table with no header row of
  its own (a header carried from the page before, or printed as loose text) that first row is
  an award row, and its ink is not checked: 1 row here (p.84, $18,000), 42 in FY2023
  ($5,979,833), 45 in FY2024. H7 (every character in a cell) and the image grid still cover
  them. This is in shared code (`parse_schedule_c_v2.py` `run_cv`), not changed here, because a
  fix changes the other years' outputs; a decision for Noel.
  *Update 2026-10-23 (#192):* fixed. The first row of the one award table with no header row of
  its own (p.84) is now ink-checked like any other; the re-run found no unread ink in it.
- Which side is right where the PDF disagrees with itself (pp.34, 39, 44, 54, 57, 58, 85, 115,
  119), or what a rounded statement meant to the dollar (pp.36, 37).
- That the "Program" column (pp.84–85) belongs in `purpose`: the PDF gives it no other home.
- That an award exists which the PDF never printed; text both grids read the same wrong way.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` here (parallel sessions); for the integrator to number.

> **§NN. FY2022 Schedule C rebuilt from the PDF, checked (#107) — REVIEW NOT STARTED**
>
> **Scope.** A new, checked parse of `source/FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf` with
> the §29 toolkit (`config/schedule_c/fy2022.toml`). Review record:
> `research/2026-10-21-fy22-schedule-c-review/`. The old `data/fy22/schedule_c/*.csv` files are
> unchanged and stay the historical record (§27). Not served by the MCP.
>
> **Result.** 5,732 award rows, $285,155,968 (body 1,550 / $235,356,968; appendices A, B, C
> 510 / $5,610,000, 2,790 / $36,539,000, 882 / $7,650,000). Nothing the first PDF parse had is
> missing; 71 rows are new, among them Art as a Catalyst for Change (40 rows, $720,000, pp.84–85),
> which the old parse dropped. All 25 category TOTALs tie. The image grid agrees on 5,616 rows.
>
> **What the PDF itself gets wrong (flagged, never fixed).**
> - **p.57.** Public Health Funding Backfill's box prints $4,467,933; its summary line $4,667,933.
> - **Six statements hold a reserve while their rows add to the whole box** (pp.34 ×2, 39, 44,
>   85, 119; $290,000 to $1,650,000); three more whose reserve and rows make neither (pp.54, 58,
>   115); "$3 million" for $3,013,205 (p.36). With p.57 they are the whole roll-up gap
>   (+$6,545,340).
> - **p.37** "$3,462,000 million" (read as $3,462,000). **Five EINs of the wrong length**
>   (pp.48, 52, 79, 80, 82). **16 box/summary name differences.**
>
> **Things a re-parse must know.** A four-column table with a "Program" column (pp.84–85). Rows
> drawn as one wide cell each (pp.117–118). "TOTAL:" (p.32). A box drawn inside an award table
> (p.81). The ink check skipped the first row of a table with no header row of its own, until
> #192.

## Not done here

- OCR audit (PLAN stage 10): docTR is not installed.
- Nothing added to the MCP or the public site.
