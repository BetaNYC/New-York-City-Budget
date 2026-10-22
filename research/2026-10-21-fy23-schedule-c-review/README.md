# FY2023 Schedule C, checked from the PDF (#106)

**Report generated:** 2026-10-21 22:45 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** `source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf` (sha256
`05437d32…23969`, 334 pages); expense disclosure as committed in `data/fy23/expense_disclosure/`;
code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #106 (epic #101). This folder is the review record. The tables are promoted to
`data/fy23/pdf/schedule_c/` by a separate PR. Same toolkit and method as FY2024
(`research/2026-10-21-fy24-schedule-c-review/`, #105), which this branch stacks on.

FY2023 has no MediaBox offset and no landscape inserts. Its trouble is in the initiative
pages: boxes printed in odd ways (an amount with a space after "$", one with no "$"), a box drawn
inside the award table above it, white-filled boxes that look like a table of names only, and a
header with no rule under it. Six new switches handle them in shared code, each switched on only by
FY2023's config. FY2024, FY2025 and FY2027's outputs are byte-identical with them in place
(checked: every file in their review folders has the same sha256). FY2026's are too, except that a
re-run fills 4 `decision` cells of `fy26_sc_review.csv` from `fy26_sc_review_decisions.csv`, which
was committed after that review file (428ec86). That is not from this branch; the committed file
is left as it was.

## Results

| What | Result |
|---|---|
| Award rows | **5,925**, **$323,063,807** (body 1,867 / $273,264,807; Appendix A 489 / $5,610,000; B 2,728 / $36,539,000; C 841 / $7,650,000) |
| Printed totals | **26 / 26** category TOTALs tie; 26 / 26 categories' boxes equal their summary lines (12 of them through 17 named aliases); 96 of 105 initiatives' rows equal what their statement designates, 30 reserve-only boxes print no rows, 6 of 9 stated sums add up |
| What didn't tie | **Twelve places the PDF disagrees with itself or rounds** (named exceptions, none corrected): six boxes whose rows or reserve don't make the box, AAPI −$120,000 (p.34), Innovative Criminal Justice Programs +$325,000 (p.43), Educational Programs for Students −$50,000 (p.53), Social and Emotional Supports −$500 (p.54), Legal Services for Low-Income New Yorkers +$1,100,000 (p.82), Young Women's Leadership Development −$416,000 (p.136); **two boxes that print a different amount from their summary line**, Low Wage Worker Support $120,000 vs $2,000,000 (p.83) and Autism Awareness $3,166,846 vs $3,316,846 (p.86); four statements that round ("$14.5 million", "$4.4 million", "$3.5 million", "$6.6 million", pp.42, 44, 43, 59). The roll-up gap (+$646,350) is exactly these |
| Appendices | No printed total; each equals its fixed pot (DATA-ANOMALIES §19) to the dollar: **$5,610,000 / $36,539,000 / $7,650,000** |
| The two lost Local rows | Both are here: **Elite Community Foundation, Inc.** $5,000 (p.213, EIN printed `84 -2079676`) and **Laundromat Project, Inc., The** $5,000 (p.235, the page shows `87-0753479`, the text layer has a space for the hyphen). With them Appendix B is $36,539,000, so §19's $36,529,000 was the parser's loss, as §19 (corrected 2026-10-20) says |
| Not in any row | $178,301,269 held post-adoption ($60,672,916 stated reserves in 39 boxes; 25 boxes held whole, "will designate post-adoption"); $35,526,369 designated straight to CUNY (5 initiatives), DOE (p.136) or the four library systems (pp.84–85), with no rows |
| Image grid (independent) | **4,884** rows agree on every field. **1,040** rows sit in tables with no drawn vertical rules; for **1,028** the pixels' own horizontal rules confirm the row's top and bottom and that no rule runs through it. The other **12** are review rows: 11 last rows with an empty spacer band under them before a black box bar (e.g. p.55), 1 first row with no rule above it (p.35). **1** more differs on fields (p.185: an org's trailing "-" over the EIN rule) |
| Ink coverage | 0 uncovered regions on the award pages (896 loose px of 172,012,911 ink px). Self-test passes on Laundromat Project, Inc. $5,000 (p.235), one of the two lost rows: hiding the row, or its letter "i", makes the check fire |
| Anchor census | 5,923 EIN-shaped words = 5,923 rows with an EIN, page by page; the 2 lost Local rows print EINs that are not EIN-shaped in the text layer (named) |
| Characters | 0 characters inside an award table left out of a cell; 0 characters cross a column split in the 46 tables built from horizontal rules |
| The old parse | Nothing the first PDF parse had (`f710a09`, 5,880 rows) is missing; this build has 45 more rows ($13,210,433: 43 body, the 2 Local). Against `data/fy23/schedule_c/` on `main` (5,904 rows, later repaired from the disclosure), 1 differs, where `main` took the EIN from the disclosure (Asiyah Women's Center, p.13; see below); 21 rows ($10,855,593) are new to it |
| DATA-ANOMALIES §20 | No FY2023 row is listed there |
| Disclosure (report only) | 5,713 rows match on (EIN, amount); 5,729 without the City-EIN name rule. 212 PDF rows ($18,563,055) have no disclosure row. No prototype floor for this year |
| Review file | **53 rows**, 17 critical; largest $3,000,000 (a spacer band, p.53) and $1,880,000 (Low Wage Worker Support's box) |

## What FY2023 does that FY2024 doesn't

Each is a switch or list in `config/schedule_c/fy2023.toml` with the pages it came from; the code
is shared. Each switch changes FY2023's output when turned off (checked one by one).

1. **A box amount printed "$ 5,000,000"** (p.34, AAPI) (`box_amount_dollar_space`), and **one
   printed with no "$"**, "Trauma Recovery Centers 2,400,000" in the black bar (p.92)
   (`box_amount_without_dollar`, flagged `W.box_amount_no_dollar`). Without them the boxes were
   not boxes, and their rows went to the box before.
2. **A box inside the award table above it** (p.53: Community Schools' last rows, an empty band,
   then "Educational Programs for Students | $7,143,133" and its Agency and U/A rows, all one
   ruled table; its statement is in the next table) (`split_boxes_award_tables`).
3. **White-filled boxes that make a table of the name column only**, the EINs and amounts printed
   beside it (p.68 CUNY Research Institutes; p.139 under COMPASS's last rows; p.140 STARS)
   (`hrule_beside`). The table is read from the horizontal rules instead, as FY2024's h-rule
   tables.
4. **A header in the same row band as the first award row**, no rule between (p.35)
   (`hrule_header_split`). The band is cut halfway between the header words and the row's.
5. **A letter in a phantom column**: the "I" of "Inc." centred 0.07 pt left of a white box's
   edge (p.98) (`sliver_chars`). It goes to the cell its glyph runs into; flagged
   `W.sliver_char`.
6. **A last row with no left rule** (p.93, City Parks Foundation $778,500): one vertical line
   added at the table's edge for that page (`[[vector_pages]]`).
7. **First letters of box titles in their own cells** (p.60 "E" | "nding the Epidemic", p.63)
   (`box_title_letters`, FY2025's switch). FY2024's `open_top_rows` and `header_two_bands` are off:
   they changed nothing, except that `open_top_rows` pulled p.92's last row into the box under it.
8. **62 statement wordings** (142 statements), including a reserve after the providers ("has designated the
   following providers for Fiscal 2023 and $186,947 will be designated post-adoption", pp.71–75,
   131–132), "The Council Members will designate $100,000 per Council District, for a total of
   $5,100,000 post adoption" (p.41), and "Fiscal 2022" typos (pp.49, 50).
9. **A purpose that ends "in conjunction with Council Member"** (p.176) matched H6's furniture
   pattern; it is a named exception (`checks.py` now takes H6 exceptions by award and field).
10. **The ink region floor is 32 px**, not 48: the self-test row's "i" is under 40 px.
11. **Two initiatives on one page failing the same check** (p.43) got one review id; the
    initiative is now their `field`, as for box aliases (no other year has such a pair).

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars |
| `ISSUE-LOG-DRAFT.md` | #106 issue-log comments, drafted, **not posted** |
| `data/fy23_sc_awards.csv` | Every award row, same columns as FY2024 |
| `data/fy23_sc_initiatives.csv` | 145 initiatives: box amount, designation statement and its kind, reserve, rows and their sum |
| `data/fy23_sc_categories.csv` | The 26 category summary tables, line by line, with TOTALs |
| `data/fy23_sc_review.csv` | The review file (same columns as `fy24_sc_review.csv`) |
| `data/fy23_sc_checks.txt` | Every check and its numbers |
| `data/fy23_sc_flags.csv` | Every flag, including routine warns |
| `data/fy23_sc_pages.csv` | Per page: tables, award rows, EIN words, image lattice and ink numbers |
| `data/fy23_sc_disclosure_match.csv` | Each PDF row's disclosure partner or the reason it has none |
| `data/fy23_sc_manifest.json` | Input hashes and tool versions |
| `data/overlays/` | Page crops for the 13 image-side review rows |

There is no `fy23_sc_review_decisions.csv` yet: Noel writes it (the pipeline never does).

## How to redo it

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r code/requirements.txt -r code/requirements-cv.txt pytest
.venv/bin/python code/parse_schedule_c_v2.py --fy 2023      # under 1 min on a laptop CPU
for y in 2024 2025 2026 2027; do .venv/bin/python code/parse_schedule_c_v2.py --fy $y; done   # must not change
.venv/bin/python -m pytest code/test_schedc.py
```

Same tool versions as FY2024 (Python 3.12.13, pdfplumber 0.11.10, pypdfium2 5.14.0, OpenCV
4.14.0, numpy 2.5.4). The run is byte-identical on re-run (checked, overlays included).

## What these checks cannot prove

- For the 1,028 rows checked only by pixel rules, the **text** of each field is read once, from
  the text layer, with columns split at the EIN and amount words. The pixels confirm the rows,
  the EIN census and the "nothing crosses a split" check confirm the columns; no second reader
  read those fields.
- Which side is right where the PDF disagrees with itself (pp.34, 43, 53, 54, 82, 83, 86, 136),
  or what a rounded statement meant to the dollar (pp.42, 43, 44, 59).
- That Asiyah Women's Center's EIN is wrong in the PDF: it prints Muslims Giving Back's
  822712941 twice (pp.13, 175). The disclosure says 832104070.
- That an award exists which the PDF never printed; text both grids read the same wrong way.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` here (parallel sessions); for the integrator to number.

> **§NN. FY2023 Schedule C rebuilt from the PDF, checked (#106) — REVIEW NOT STARTED**
>
> **Scope.** A new, checked parse of `source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf`
> with the §29 toolkit (`config/schedule_c/fy2023.toml`). Review record:
> `research/2026-10-21-fy23-schedule-c-review/`. The old `data/fy23/schedule_c/*.csv` files are
> unchanged and stay the historical record (§27). Not served by the MCP.
>
> **Result.** 5,925 award rows, $323,063,807 (body 1,867 / $273,264,807; appendices A, B, C
> 489 / $5,610,000, 2,728 / $36,539,000, 841 / $7,650,000). Nothing the first PDF parse had is
> missing; 45 rows are new, including the two $5,000 Local rows §19 describes, so Appendix B is
> the $36,539,000 pot. All 26 category TOTALs tie. The image grid agrees on 4,884 rows; 1,040
> rows sit in tables with no vertical rules, and the pixels' horizontal rules confirm 1,028.
>
> **What the PDF itself gets wrong (flagged, never fixed).**
> - **Two boxes print a different amount from their summary line:** Low Wage Worker Support
>   $120,000 vs $2,000,000 (p.83, p.81); Autism Awareness $3,166,846 vs $3,316,846 (p.86).
> - **Six boxes whose rows (and reserve) don't make the box:** pp.34, 43, 53, 54, 82, 136
>   (−$416,000 to +$1,100,000). Four statements round ("$14.5 million" etc., pp.42, 43, 44, 59).
>   With the two above they are the whole roll-up gap (+$646,350).
> - **pp.13, 175.** Asiyah Women's Center is printed with Muslims Giving Back's EIN 822712941.
> - **p.213** EIN "84 -2079676"; **p.235** "87-0753479" whose hyphen the text layer reads as a
>   space. Clean EIN left blank.
> - **17 box/summary name differences**; "Fiscal 2022" in two statements (pp.49, 50).
>
> **Things a re-parse must know.** A box amount printed "$ 5,000,000" (p.34) and one with no "$"
> (p.92). A box drawn inside the award table above it (p.53). White-filled boxes that make a
> table of names only (pp.68, 139, 140). 46 award tables have horizontal rules only. Statements
> put the reserve after the providers ("... and $N will be designated post-adoption").

## Not done here

- OCR audit (PLAN stage 10): docTR is not installed.
- Nothing added to the MCP or the public site.
