# FY2021 Schedule C, checked from the PDF (#108)

**Report generated:** 2026-10-22 01:45 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** `source/FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf` (sha256
`3323ceae…0a`, 343 pages); expense disclosure as committed in `data/fy21/expense_disclosure/`;
code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #108 (epic #101). This folder is the review record. The tables are promoted to
`data/fy21/pdf/schedule_c/` by a separate PR. Same toolkit and method as FY2022
(`research/2026-10-21-fy22-schedule-c-review/`, #107), which this branch stacks on.

FY2021 is FY2022's layout (no MediaBox offset; "Tax ID" in the member tables and appendices,
"EIN" in the initiative tables) with one big difference: **many award-table headers are printed
outside the table's drawn rules**, partly or wholly ("EIN" in a cell, "Legal Name of
Organization" and "Amount" loose beside it; or the whole header loose under the statement).
Before the fix the statement swallowed the header, 44 statements were unreadable and 15 pages lost
their rows. Seven new switches handle FY2021's pages, each switched on only by its config; FY2022,
FY2023, FY2024, FY2025 and FY2027's outputs are byte-identical with them in place, FY2026's too
except the 4 decision cells a re-run fills from its committed decisions file (as before).

## Results

| What | Result |
|---|---|
| Award rows | **6,179**, **$262,477,792** (body 1,869 / $212,678,792; Appendix A 514 / $5,610,000; B 2,902 / $36,539,000; C 894 / $7,650,000) |
| Printed totals | **26 / 26** category TOTALs tie; 26 / 26 categories' boxes equal their summary lines (12 of them through 16 named aliases); every initiative's rows equal what its statement designates except the 5 named below; 16 reserve-only boxes print no rows |
| What didn't tie | **Five places the PDF disagrees with itself or rounds** (named exceptions, none corrected): three statements that hold a reserve while their rows add to the whole box (Coalition Theaters of Color +$90,000, p.44; Art as a Catalyst for Change +$15,300, p.93; MWBE Leadership Associations +$82,769, p.107); Alternatives to Incarceration rows $1 over (p.39); Food Pantries "$4.6 million" for $4,659,000 (p.55). The roll-up gap (+$129,070) is exactly these |
| A box printed wrong | **p.122 "$477,00"**, Initiative for Immigrant Survivors of Domestic Violence: read as $477,000 (its summary line and its rows plus reserve make $477,000). The printed text is kept; a critical review row |
| Appendices | No printed total; each equals its fixed pot (DATA-ANOMALIES §19) to the dollar: **$5,610,000 / $36,539,000 / $7,650,000** |
| Not in any row | $82,317,815 held post-adoption ($17,289,589 stated reserves in 29 boxes; 14 boxes held whole, $65,028,226); $31,080,469 designated straight to CUNY (5), DOE (p.124) or the four library systems (pp.83–84), with no rows |
| Image grid (independent) | **5,744** rows agree on every field. **435** rows sit in tables the image lattice cannot read (their headers are printed outside the drawn grid, so it cannot name their columns); for **431** the pixels' own horizontal rules confirm the row's top and bottom. The other **4**, and **3** image-only rows (the same rows, read without their spacer band), are review rows: an empty band before a black box bar, joined to the row (pp.48, 49, 69, 72) |
| Ink coverage | 0 uncovered regions on the award pages (797 loose px of 182,129,875 ink px, all under the region floor). Self-test passes on Instituto Arte Teatral Internacional, Inc. $50,000 (p.45), in a table whose header is printed outside its cells |
| Anchor census | 6,173 EIN-shaped words = 6,173 rows with an EIN, page by page; 6 more rows print EINs of the wrong length (named, all 8 digits) |
| Characters | 0 characters inside an award table left out of a cell (loose header words read into a header, and sub-headings, are counted as read) |
| The old parse | Nothing the first PDF parse had (`f710a09`, 6,110 rows) is missing; this build has 69 more rows ($11,149,604), all in the body, among them 36 of Art as a Catalyst for Change's 40 rows and the first row of many tables. Against `data/fy21/schedule_c/` on `main` (6,120 rows, later repaired from the disclosure), 1 differs: `main` gives Congregation Beit Simchat Torah's $52,700 row EIN 23-7406899, the PDF prints 11-2527706 (p.61; a review row); 60 rows ($10,661,304) are new to it |
| DATA-ANOMALIES §20 | No FY2021 row is listed there |
| DATA-ANOMALIES #59 | FY2021 prints `$` on its appendix amounts; the census counts EIN words, not `$`, so it would catch a row without one |
| Disclosure (report only) | 5,874 rows match on (EIN, amount); 5,888 without the City-EIN name rule. 305 PDF rows ($17,987,653) have no disclosure row. No prototype floor for this year |
| Review file | **48 rows**, 8 critical; largest $600,000 (CONNECT, Inc., p.48) |

## What FY2021 does that FY2022 doesn't

Each is a switch or list in `config/schedule_c/fy2021.toml` with the pages it came from; the code
is shared. Each switch changes FY2021's output when turned off (checked one by one; eight
FY2022–FY2025 switches with no effect are off).

1. **Award headers printed outside the rules** (`header_band_words`, 81 rows; plus FY2023's
   `loose_header`, 511 rows). p.35: "Legal Name of Organization | EIN" in cells, "Amount" loose
   beside them; p.45: "EIN" in a cell, the other two loose in the same band; p.40: the whole
   header loose, right under the statement. The loose words complete the header, the statement
   ends at it, and H7 counts those words as read.
2. **Sub-headings inside an award table** (`award_subheadings`, pp.70–72, Community Housing
   Preservation Strategies): "Technical Assistance", "Community Consultant Contracts", "Housing
   Preservation Initiative". Not award rows; the 67 rows under them carry the sub-heading in
   `purpose` (flagged `W.subheading`). Without this, the second sub-heading was glued onto
   ANHD's name and p.71–72 lost their rows.
3. **Edge slivers** (`edge_slivers`, pp.105–106): an 8.9 pt white column down a table's left and
   right edge holds each row's first letter and last digit ("E | ast River ...", "$118,75 | 0").
4. **A box amount beside the box** (`box_amount_loose`, p.98, NORCs "$5,400,325"); **an empty
   band above a box** (`skip_empty_first_row`, p.84, Queens Borough Public Library, whose
   statement had been read onto the NYPL box); **header and row cells that don't line up**
   (`header_overlap_cells`, p.73, Foreclosure Prevention Programs); **a TOTAL without "$"**
   (`summary_amount_without_dollar`, p.49 "21,679,075"); **a malformed box amount read as
   named** (`box_amount_read`, p.122 "$477,00").
5. From earlier years: FY2025's `statement_in_cell` (p.60, HIV/AIDS Faith-Based),
   FY2022's `hrule_extra_column` and "Program" label (pp.93–94, Art as a Catalyst for Change),
   FY2023's `statement_loose_text`, `sliver_chars`, FY2025's `box_title_letters`.
6. **Statements**: 11 patterns, new wordings "post-adoptions" (p.61), "This initiative will be
   designated post-adoption" (p.106, no "."), "The Council will designate $85,000 post-adoption.
   The Council has designated $4,845,000 for (the) following providers" (p.81, twice), "...
   allocated directly to the Department for the Aging" (p.96).
7. The category banners are 14 pt (FY2022: 20 pt), and FY2021 has "Children's Services" (p.33).

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars |
| `ISSUE-LOG-DRAFT.md` | #108 issue-log comments, drafted, **not posted** |
| `data/fy21_sc_awards.csv` | Every award row, same columns as FY2022 |
| `data/fy21_sc_initiatives.csv` | 134 initiatives: box amount, designation statement and its kind, reserve, rows and their sum |
| `data/fy21_sc_categories.csv` | The 26 category summary tables, line by line, with TOTALs |
| `data/fy21_sc_review.csv` | The review file (same columns as `fy22_sc_review.csv`) |
| `data/fy21_sc_checks.txt` | Every check and its numbers |
| `data/fy21_sc_flags.csv` | Every flag, including routine warns |
| `data/fy21_sc_pages.csv` | Per page: tables, award rows, EIN words, image lattice and ink numbers |
| `data/fy21_sc_disclosure_match.csv` | Each PDF row's disclosure partner or the reason it has none |
| `data/fy21_sc_manifest.json` | Input hashes and tool versions |
| `data/overlays/` | Page crops for the 7 image-side review rows |

There is no `fy21_sc_review_decisions.csv` yet: Noel writes it (the pipeline never does).

## How to redo it

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r code/requirements.txt -r code/requirements-cv.txt pytest
.venv/bin/python code/parse_schedule_c_v2.py --fy 2021      # under 1 min on a laptop CPU
for y in 2022 2023 2024 2025 2026 2027; do .venv/bin/python code/parse_schedule_c_v2.py --fy $y; done   # must not change
.venv/bin/python -m pytest code/test_schedc.py
```

Same tool versions as FY2022. The run is byte-identical on re-run (checked, overlays included).

## What these checks cannot prove

- **For the 431 rows checked only by pixel rules, the text of each field is read once**, from
  the text layer. FY2021 has four times FY2022's share of these, because its headers are often
  printed outside the drawn grid and the image side finds columns only from a header inside it.
  The pixels confirm the rows, the EIN census and H7 confirm the columns; no second reader read
  those fields. Teaching the image side to use loose header words is shared code and would change
  other years' outputs, so it is a decision for Noel.
  *Update 2026-10-23 (#193):* the image side now finds these tables' columns itself (the header's
  labels and the blank strips between them, `imagegrid.pixel_columns`) and reads all 431, a header
  printed above the grid included a second time: all agree on every field (`image_check`
  `columns_agree`, `lattice` `vector+columns`). Like the image lattice it reads the PDF's text
  layer, so a text-layer error still passes both.
- **The ink check treats a table's first row as its header** (as in FY2022–FY2024): for a table
  whose header is outside its rules that first row is an award row, and its ink is not checked.
  H7 and the image grid still cover those rows. Not changed here (shared code).
  *Update 2026-10-23 (#192):* fixed. The first row of the 36 award tables with no header row of
  their own is now ink-checked like any other; the re-run found no unread ink in them.
- That the sub-headings of pp.70–72 belong in `purpose`, and the "Program" column of pp.93–94:
  the schema has no other home.
- Which side is right where the PDF disagrees with itself (pp.39, 44, 93, 107, 122), or what a
  rounded statement meant to the dollar (p.55).
- That an award exists which the PDF never printed; text both grids read the same wrong way.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` here (parallel sessions); for the integrator to number.

> **§NN. FY2021 Schedule C rebuilt from the PDF, checked (#108) — REVIEW NOT STARTED**
>
> **Scope.** A new, checked parse of `source/FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf`
> with the §29 toolkit (`config/schedule_c/fy2021.toml`). Review record:
> `research/2026-10-22-fy21-schedule-c-review/`. The old `data/fy21/schedule_c/*.csv` files are
> unchanged and stay the historical record (§27). Not served by the MCP.
>
> **Result.** 6,179 award rows, $262,477,792 (body 1,869 / $212,678,792; appendices A, B, C
> 514 / $5,610,000, 2,902 / $36,539,000, 894 / $7,650,000). Nothing the first PDF parse had is
> missing; 69 rows are new ($11,149,604), among them 36 of Art as a Catalyst for Change's 40 rows. All 26
> category TOTALs tie. The image grid agrees on 5,744 rows.
>
> **What the PDF itself gets wrong (flagged, never fixed).**
> - **p.122** prints the box "$477,00" (its summary line $477,000).
> - **Three statements hold a reserve while their rows add to the whole box** (pp.44, 93, 107);
>   p.39's rows are $1 over; p.55 "$4.6 million" for $4,659,000. They are the whole roll-up gap
>   (+$129,070).
> - **Six 8-digit EINs** (pp.64, 65, 87, 89, 90, 91; p.60 prints two of them correctly);
>   Congregation Beit Simchat Torah printed with two EINs (pp.61, 63). **16 box/summary name
>   differences**; p.122's summary title says "Fiscal 2020".
>
> **Things a re-parse must know.** Award headers printed outside the table's rules (pp.35–128).
> Sub-headings inside an award table (pp.70–72). 8.9 pt edge columns holding first letters and
> last digits (pp.105–106). A box amount outside its box (p.98); an empty band over a box (p.84).

## Not done here

- OCR audit (PLAN stage 10): docTR is not installed.
- Nothing added to the MCP or the public site.
