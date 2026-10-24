# FY2020 Schedule C, checked from the PDF (#109)

**Report generated:** 2026-10-22 02:20 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** `source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf` (sha256
`8bab4079…8d`, 405 pages); expense disclosure as committed in `data/fy20/expense_disclosure/`;
code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #109 (epic #101). This folder is the review record. The tables are promoted to
`data/fy20/pdf/schedule_c/` by a separate PR. Same toolkit and method as FY2021
(`research/2026-10-22-fy21-schedule-c-review/`, #108), which this branch stacks on.

FY2020 is the first year back where **the member tables and the appendices print amounts with no
"$"** ("5,500", p.13). That is the layout the old parser could not read (#59): it read no
appendix row and most member rows. The anchor census counts EIN words, never "$", so it covers
these rows; all 5,025 of them are read and each appendix equals its pot. FY2020 also draws many
tables with horizontal rules only (747 rows), some with a Council Member column, two or three
award rows in one band, or a header in one cell. Twelve pages (pp.166–177, Speaker's Initiative)
have a page-origin offset, handled since FY2024. Nine new switches handle FY2020's pages, each
switched on only by its config; FY2021–FY2025 and FY2027's outputs are byte-identical with them in
place, FY2026's too except the 4 decision cells a re-run fills from its committed decisions file.

## Results

| What | Result |
|---|---|
| Award rows | **7,921**, **$336,750,073** (body 3,528 / $286,951,073; Appendix A 510 / $5,610,000; B 2,986 / $36,539,000; C 897 / $7,650,000) |
| Printed totals | **27 / 27** category TOTALs tie; 27 / 27 categories' boxes equal their summary lines (12 of them through 16 named aliases); every initiative's rows equal what its statement designates except the 8 named below; 9 reserve-only boxes print no rows |
| What didn't tie | **Eight places the PDF disagrees with itself or rounds** (named exceptions, none corrected): Innovative Criminal Justice Programs' rows are $200,000 short of the box (p.46; the scope names $200,000 for Carnegie Hall's NeON Arts, which has no row); Initiative to Combat Sexual Assault's rows $2,000 over (p.45); five rounded statements ("$7.8 million" p.78, "$1.4 million" p.86, "$4.8 million" p.89, "$2.9 million" p.47, "$4.66 million" p.94); a box for the whole SAVE initiative over its three parts' boxes (p.79). The roll-up gap (−$219,300) is exactly the first seven |
| A row's EINs shifted | **p.46**: three rows of Initiative to Combat Sexual Assault print EINs that look one row off (New York Foundling Hospital 11-3431280, North Brooklyn Coalition 13-2946970, which is Safe Horizon's on p.78; Safe Horizon 13-3540337, the next row's). Kept as printed; a critical review row ($1,278,000). `main`'s repaired files took the disclosure's EINs |
| Appendices | No printed total; each equals its fixed pot (DATA-ANOMALIES §19) to the dollar: **$5,610,000 / $36,539,000 / $7,650,000** |
| Not in any row | $80,569,432 held post-adoption ($69,374,658 stated reserves in 53 boxes, including p.118's "$3 million directly to CUNY"; 4 boxes held whole, $11,194,774); $36,632,969 designated straight to an agency (CUNY, DOE, the Community Boards, the four library systems), with no rows |
| Image grid (independent) | **6,380** rows agree on every field. **1,541** rows sit in tables the image lattice cannot read (ruled with horizontal lines only, or with their header outside the drawn grid); for **1,532** the pixels' horizontal rules confirm the row's top and bottom. The other **9** are review rows: an empty spacer band joined to a row (pp.42, 82, 113), and 6 rows on pp.84, 102 and 187 that the PDF prints in one band with another row or with the header, no rule between, which the parse cut apart (looked at: they are separate awards) |
| Ink coverage | 0 uncovered regions on the award pages (18 loose px of 210,915,293 ink px). Self-test passes on Bergen Basin … Millennium Development Health & Wellness Program 19,000 (p.190, Appendix A), an amount with no "$" |
| Anchor census | 7,917 EIN-shaped words, 7,918 rows with an EIN: page by page equal except p.306, where the text layer glues one EIN to the name before it ("Students131693134"; a named exception). 3 more rows print EINs of the wrong length (named: two 8-digit, one 10-digit) |
| Characters | 0 characters inside an award table left out of a cell; 0 characters cross a column split in the 46 tables built from horizontal rules |
| The old parse | Nothing the first PDF parse had (`f710a09`, 2,841 rows) is missing; this build has 5,080 more rows ($77,987,688): 4,180 in the appendices and 900 in the body. Against `data/fy20/schedule_c/` on `main` (2,841 rows, later repaired from the disclosure), 4 differ, where `main` took the EIN from the disclosure (the three p.46 rows; Legal Aid Society on p.124, which the PDF prints with the City's EIN 13-6400434); 5,084 rows ($79,315,688) are new to it |
| DATA-ANOMALIES §20 | Its one FY2020 row ("Urban Health Plan, Inc. 15-24042810 $88,855 NYC MWBE Alliance, Inc.", p.162) comes back as two awards: Urban Health Plan $88,855 (EIN printed with 10 digits, a review row) and NYC MWBE Alliance, Inc. 82-1902677 $20,000 |
| DATA-ANOMALIES #59 | The appendices' rows without "$" are all read: 4,393 rows, $49,799,000, the three pots |
| Disclosure (report only) | 7,579 rows match on (EIN, amount); 7,599 without the City-EIN name rule. 342 PDF rows ($27,627,019) have no disclosure row. No prototype floor for this year |
| Review file | **42 rows**, 10 critical; largest $3,000,000 (New York City Community Learning Schools, p.82) |

## What FY2020 does that FY2021 doesn't

Each is a switch in `config/schedule_c/fy2020.toml` with the pages it came from; the code is
shared. Each switch changes FY2020's output when turned off (checked one by one); the FY2021–FY2025
switches with no effect are off.

1. **Amounts with no "$"** in tables with a Council Member, Borough or Sponsor column
   (`bare_amounts`, with FY2026's `amount_without_dollar`; 5,025 rows): read as printed, a routine
   flag (`W.amount_bare`), not a review row. In tables built from horizontal rules an amount word
   may be bare; a bare number left of the EIN column, or left of the right-aligned amounts, is
   part of a name ("Public School 151Q", "P.S. 108").
2. **Horizontal-rule tables with a Council Member column** (`hrule_lead_column`, pp.38–41,
   Digital Inclusion and Literacy): split at the left edge of "Legal".
3. **Two or three award rows in one band** (`hrule_split_lines`, pp.84, 102, 187): cut between
   the lines when each line holds one name, one EIN and one amount. The image check sees no rule
   there, so each is a review row.
4. **A header drawn as one cell** over rows in four (`header_one_cell`, pp.162–164, Neighborhood
   Development Grant Initiative).
5. **An 8-digit EIN starting an h-rule table** (`hrule_short_ein`, p.134, Amudim).
6. **A statement beside its label** as its own loose line (`statement_beside_label`, p.161);
   **orphan characters in a band between segments** belong to no table (`orphans_in_gaps`,
   p.113).
7. **Category banners** drawn with empty bands around them (p.111 "Housing") or printed twice
   over themselves (p.97 "Health Services") (`banner_variants`); **a summary amount the text
   layer holds twice** (`summary_amount_doubled`, p.145 "$3,383,670$3,383,670"; the page shows
   it once).
8. From earlier years: FY2023's `hrule_beside` (p.186), `hrule_header_split` (pp.84, 187) and
   `split_boxes_award_tables` (p.42), FY2022's `hrule_extra_column` (p.142), FY2025's
   `box_title_letters`.
9. **Statements**: 19 patterns. New: "will designate $250,000 post-adoption and has designated $3
   million directly to CUNY" (p.118; both read as the part with no rows), "The Borough Presidents
   will designate the providers post-adoption" (p.146), "post–adoption" with an en dash (p.119),
   "The City Council designated" (p.114).
10. **A named exception for an anchor count** (`H5.page_words` in `code/schedc/checks.py`,
    matched on page, words and rows): p.306.

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars |
| `ISSUE-LOG-DRAFT.md` | #109 issue-log comments, drafted, **not posted** |
| `data/fy20_sc_awards.csv` | Every award row, same columns as FY2022 |
| `data/fy20_sc_initiatives.csv` | 140 initiatives |
| `data/fy20_sc_categories.csv` | The 27 category summary tables, line by line, with TOTALs |
| `data/fy20_sc_review.csv` | The review file (same columns as `fy22_sc_review.csv`) |
| `data/fy20_sc_checks.txt` | Every check and its numbers |
| `data/fy20_sc_flags.csv` | Every flag, including routine warns |
| `data/fy20_sc_pages.csv` | Per page: tables, award rows, EIN words, image lattice and ink numbers |
| `data/fy20_sc_disclosure_match.csv` | Each PDF row's disclosure partner or the reason it has none |
| `data/fy20_sc_manifest.json` | Input hashes and tool versions |
| `data/overlays/` | Page crops for the 9 image-side review rows |

There is no `fy20_sc_review_decisions.csv` yet: Noel writes it (the pipeline never does).

## How to redo it

```
.venv/bin/python code/parse_schedule_c_v2.py --fy 2020      # about 1 min on a laptop CPU
for y in 2021 2022 2023 2024 2025 2026 2027; do .venv/bin/python code/parse_schedule_c_v2.py --fy $y; done   # must not change
.venv/bin/python -m pytest code/test_schedc.py
```

Same tool versions as FY2021. The run is byte-identical on re-run (checked, overlays included).

## What these checks cannot prove

- **For the 1,532 rows checked only by pixel rules, the text of each field is read once.** That
  is a fifth of FY2020's body (all of it in the body): the h-rule tables and the tables whose
  header is printed outside the grid. The pixels confirm the rows; the EIN census and H7 the
  columns; no second reader read those fields.
  *Update 2026-10-23 (#193):* the image side now finds these tables' columns itself (the header's
  labels and the blank strips between them, `imagegrid.pixel_columns`) and reads all 1,532 a
  second time: all agree on every field (`image_check` `columns_agree`, `lattice`
  `vector+columns`). Like the image lattice it reads the PDF's text layer, so a text-layer error
  still passes both.
- **The ink check treats a table's first row as its header** (shared code, not changed): for a
  table with no header row of its own, that first row's ink is not checked.
  *Update 2026-10-23 (#192):* fixed. The first row of the 6 award tables with no header row of
  their own is now ink-checked like any other; the re-run found no unread ink in them.
- That the amounts with no "$" are what the Council meant; that p.46's EINs are shifted rather
  than wrong some other way; which side is right where the PDF disagrees with itself; what a
  rounded statement meant to the dollar.
- That an award exists which the PDF never printed; text both grids read the same wrong way.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` here (parallel sessions); for the integrator to number.

> **§NN. FY2020 Schedule C rebuilt from the PDF, checked (#109) — REVIEW NOT STARTED**
>
> **Scope.** A new, checked parse of `source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf` with
> the §29 toolkit (`config/schedule_c/fy2020.toml`). Review record:
> `research/2026-10-22-fy20-schedule-c-review/`. The old `data/fy20/schedule_c/*.csv` files are
> unchanged and stay the historical record (§27). Not served by the MCP.
>
> **Result.** 7,921 award rows, $336,750,073 (body 3,528 / $286,951,073; appendices A, B, C
> 510 / $5,610,000, 2,986 / $36,539,000, 897 / $7,650,000). Nothing the first PDF parse had is
> missing; 5,080 rows are new ($77,987,688), 4,180 of them in the appendices: #59's FY2020
> loss, recovered from the PDF. All 27 category TOTALs tie. §20's one FY2020 merged row comes
> back as two awards. The image grid agrees on 6,380 rows.
>
> **What the PDF itself gets wrong (flagged, never fixed).**
> - **p.46**: three EINs printed one row off (Foundling, North Brooklyn Coalition, Safe Horizon).
> - **p.46** rows $200,000 short of the box; **p.45** rows $2,000 over; five rounded statements;
>   the roll-up gap (−$219,300) is these.
> - **Three EINs of the wrong length** (pp.134 ×2, 162). **16 box/summary name differences**;
>   a SAVE box for the whole initiative over its parts' boxes (p.79).
>
> **Things a re-parse must know.** Amounts with no "$" in member tables and appendices. Many
> tables ruled with horizontal lines only, some with a member column (pp.38–41), two or three rows
> to a band (pp.84, 102, 187), a header in one cell (pp.162–164). Banners drawn twice (p.97) or
> padded (p.111). A summary amount whose text is doubled (p.145). Page-origin offset pp.166–177.

## Not done here

- OCR audit (PLAN stage 10): docTR is not installed.
- Nothing added to the MCP or the public site.
