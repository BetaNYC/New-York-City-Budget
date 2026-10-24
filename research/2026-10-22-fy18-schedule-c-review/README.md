# FY2018 Schedule C, checked from the PDF (#111)

**Report generated:** 2026-10-22 05:40 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** `source/FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf` (sha256
`d4f1374e…cb`, 357 pages; pp.115–119 blank); expense disclosure as committed in
`data/fy18/expense_disclosure/`; code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #111 (epic #101). This folder is the review record. The tables are promoted to
`data/fy18/pdf/schedule_c/` by a separate PR. Same toolkit and method as FY2019
(`research/2026-10-22-fy19-schedule-c-review/`, #110), which this branch stacks on.

FY2018 looks like FY2019 (amounts with no "$" in the member tables and Appendices B and C, a
"*" column, a post-adoption reserve sometimes printed again as an agency row, the same Jobs to
Build On partner list), plus five things of its own:

- **Appendix A prints every amount with cents** ("$30,000.00", p.131). The old parse ran the
  cents into the purpose (DATA-ANOMALIES §21, `fy18_aging_shift`). Read as whole dollars, a
  routine flag (`W.amount_cents`, 537 rows); Appendix A equals its pot.
- **"Fiscal Conduit" and "FC EIN" columns** (Boroughwide Needs and all three appendices): 50
  rows print a fiscal conduit. No output column holds it; each such row is a warn review row
  that carries the conduit's name and EIN as printed, and the FC EIN counts in the anchor census.
- **TOTAL rows inside award tables** (14 tables, e.g. p.64): not awards; each is checked against
  the rows above it. 13 tie; Autism Awareness's does not (the PDF's own error, below).
- **Box titles printed above their table** (11 boxes: SAVE's three parts, p.53; Crisis
  Management System's eight parts, pp.94–97). Read as the boxes' title bars; warn review rows.
- **A row printed between two ruled tables** (p.107, Urban Health Plan, Inc., "15-24042810",
  $88,855: DATA-ANOMALIES §20's row, as in FY2020). Read as an award row with its EIN as printed.

## Results

| What | Result |
|---|---|
| Award rows | **5,906**, **$203,804,505** (body 1,420 / $154,005,505; Appendix A 537 / $5,610,000; B 3,054 / $36,539,000; C 895 / $7,650,000) |
| Printed totals | **26 / 26** category TOTALs tie but one (Community Development's TOTAL prints $100,000 more than its lines, a named exception); 26 / 26 categories' boxes equal their summary lines (14 of them through 24 named aliases); every initiative's rows equal what its statement designates except the 10 named below; 35 boxes held whole post-adoption print no rows |
| What didn't tie | **Named exceptions, none corrected.** Two reserves printed again as City-agency rows: Discretionary Child Care (p.36, ACS $481,197) and NORCs (p.101, DFTA $2,429,000 = the "$1.9 million" and "$529,000" held). **Six boxes whose rows do not make them:** Support for Educators −$500 (p.57: the DOE row prints $20,354,000, the scope $20,354,500), Immigrant Opportunities −$60,000 (p.80), Autism Awareness +$55,000 (p.85; its own TOTAL row agrees with the box, not the rows), School Based Conflict Mediation +$40,000 (p.95; Street Corner Resources printed twice), COMPASS −$146,000 (p.124: DYCD named in the statement, no row), Immigrant Survivors of Domestic Violence −$20,000 (p.127). **Merit-Based Scholarships** (p.69): box $15,000,000, summary line $14,924,669. **Crisis Management System** (p.93): a box for the whole ($11,340,534) over eight parts' boxes that add to $11,327,800, the summary line. SAVE (p.53): a box for the whole over its three parts. The roll-up gap (+$2,754,028) is exactly these |
| An EIN that is another organization's | **p.55**: Good Shepherd Services, $207,000 (Dropout Prevention), prints 46-1227433, New York City Community Learning Schools' EIN; Good Shepherd prints 13-5598710 elsewhere (p.94). Kept as printed; a critical review row. `main` took 13-5598710 from the disclosure |
| A list that is not awards | **p.106**: "Below is a list of the JtBO service provider partners", 28 rows, $4,463,500, under CWE's Jobs to Build On** row ($5,154,200, p.105; the scope: "$4.46 million … on service provider partners … The remaining $690,700 … oversight"). Read as no award (`side_lists`), one critical review row. The old parse counted 27 of them |
| Appendices | No printed total; each equals its fixed pot (DATA-ANOMALIES §19) to the dollar: **$5,610,000 / $36,539,000 / $7,650,000** |
| Not in any row | $132,416,318 held post-adoption ($23,573,189 stated reserves in 21 boxes; 35 boxes held whole, $108,843,129); $47,133,205 designated straight to an agency (18 boxes: CUNY, DOE, DCAS, the City Clerk, the Brooklyn Borough President, HPD, Parks, DYCD, ACS, H+H, …), with no rows |
| Image grid (independent) | **5,260** rows agree on every field. **646** rows (all in the body) sit in tables the image lattice cannot read (ruled with horizontal lines only, or with no drawn vertical rules); the pixels' horizontal rules confirm the row band of all 646. No image-side review row |
| Ink coverage | 0 uncovered regions on the award pages (30 loose px of 160,718,002 ink px). Self-test passes on Williams \| Bergen Basin Community Development Corporation d/b/a Millennium Development \| $19,000.00 (p.131, Appendix A), an amount printed with cents |
| Anchor census | 5,974 EIN-shaped words, 5,953 rows with an EIN (fiscal conduits' EINs included): page by page equal except pp.16, 177, 300, 301, 331, 332, where the text layer glues an EIN to the name before it ("Ltd.112507910"), and p.106 (the partner list): named exceptions. One row prints an EIN of the wrong length (p.107, named) |
| "*" | 1,504 rows; every "*" in the award tables is on a row (1,504 in the text layer). 9 sit in a cell with no "*" column (pp.92–93 in the School column; p.127 in a cell of its own): warn review rows |
| Characters | 0 characters inside an award table left out of a cell; 0 characters cross a column split in the 14 tables built from horizontal rules |
| The old parse | The first FY2018 PDF parse (`26a5ab8`, 902 rows, $107,136,231: the body and Appendix A, no row from B or C) is all here on (EIN, amount) except the **27 partner-list rows**. This build has 5,031 rows ($101,056,774) the old parse did not: Appendices B and C (#59) and more. Against `data/fy18/schedule_c/` on `main` (repaired from the disclosure), also 3 rows where `main` took the disclosure's value: Good Shepherd's EIN (p.55, above); Bellevue Hospital's (p.68, printed with the City's EIN 13-6400434); Convent Avenue Baptist Church – Hamilton Grange Senior Center (p.136, printed $12,000.00, `main` $15,000) |
| DATA-ANOMALIES §20 | **All 94 FY2018 merged rows come back as separate awards: 224 awards, each found on (EIN, amount)** in this parse (Urban Health Plan by its EIN as printed). Row by row: `data/fy18_sc_s20_check.csv` (made by `s20_check.py` from the old file at `26a5ab8`). 93 of the 94 lost the row boundary at a "*" between an EIN and its amount; the other at Urban Health Plan's 10-digit EIN |
| DATA-ANOMALIES #59 | The appendices' rows are all read: 4,486 rows, $49,799,000, the three pots |
| Disclosure (report only) | 5,707 rows match on (EIN, amount); 5,715 without the City-EIN name rule. 199 PDF rows ($41,175,405) have no disclosure row. No prototype floor for this year |
| Review file | **117 rows**, 2 critical; largest $11,340,534 (the Crisis Management System box over its parts, p.93) |

## What FY2018 does that FY2019 doesn't

Each is in `config/schedule_c/fy2018.toml` with the pages it came from; the code is shared. Each
switch changes FY2018's output when turned off (checked one by one); the FY2019–FY2025
switches with no effect are off, and header labels it does not use were removed.

1. **`amount_cents`** (`vector.hrule_tables`, `structure`): "$30,000.00" is an amount word, so
   Appendix A's ruled tables are not taken apart; read as whole dollars in a member or appendix
   table, a routine flag (`W.amount_cents`). Any other cents stay unreadable.
2. **Fiscal conduit columns** (header labels `conduit`, `conduit_ein`; no switch): a row
   printing one is a warn review row (`W.fiscal_conduit`) with both as printed; the FC EIN
   counts in `checks.py`'s anchor census.
3. **`award_table_totals`**: a "TOTAL" row with no EIN closing an award table is not an award;
   it must equal the rows of its initiative read so far, or it is a critical `H12.table_total`
   (or a named exception: p.86).
4. **`box_title_above`**: a table starting at "Agency:" with a title line and one "$" amount in
   the band right above it is a box; flagged `W.box_title_above`.
5. **`short_ein_rows`**, **`hrule_skip_kept`**, with FY2020's `hrule_short_ein`: a row printing
   an EIN of the wrong length is an award row, not a box; an h-rule stack ends at a ruled table
   (p.107) and skips one at its head (p.93, the header drawn as its own table).
6. **A "*" in a cell of its own** under a header with no "*" column (p.127): the row's asterisk,
   a warn review row, not an unmapped cell.
7. **`side_lists`** (FY2019) now reads a list that runs on into the headerless tables under it
   (p.106: three tables), and takes each row's amount from its text (p.106 prints "Amount" and
   "Service Type" in one header cell). FY2019's result is unchanged.
8. **Statements**: 10 patterns, 5 new: "will designate allocation / this initiative / this
   allocation post-(budget) adoption", "The Borough Presidents will designate the organizations
   and the amount each will receive …", straight to a dozen agencies ("This funding is provided
   directly to the agency", "These funds are allocated directly to agencies for Fiscal 2018:
   Agency City University of New York Department of Education"), NORCs' two reserves, and two
   statements naming the provider in words (pp.98, 124).
9. **Headers**: "Cultural Organization - School" (CASA, pp.45–50), "School" (Art as a Catalyst,
   pp.92–93). Nine summary tables are titled without "Council".

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars |
| `ISSUE-LOG-DRAFT.md` | #111 issue-log comments, drafted, **not posted** |
| `data/fy18_sc_awards.csv` | Every award row, same columns as FY2019 |
| `data/fy18_sc_initiatives.csv` | 145 initiatives |
| `data/fy18_sc_categories.csv` | The 26 category summary tables, line by line, with TOTALs |
| `data/fy18_sc_review.csv` | The review file (same columns as `fy19_sc_review.csv`) |
| `data/fy18_sc_checks.txt` | Every check and its numbers |
| `data/fy18_sc_flags.csv` | Every flag, including routine warns |
| `data/fy18_sc_pages.csv` | Per page: tables, award rows, EIN words, image lattice and ink numbers |
| `data/fy18_sc_disclosure_match.csv` | Each PDF row's disclosure partner or the reason it has none |
| `data/fy18_sc_manifest.json` | Input hashes and tool versions |
| `data/fy18_sc_s20_check.csv` | DATA-ANOMALIES §20: each of the 94 old merged rows, split into its awards, and the award ids that hold them now |
| `s20_check.py` | Writes that file (FY2019's, also matching an EIN printed with the wrong length) |

There is no `fy18_sc_review_decisions.csv` yet: Noel writes it (the pipeline never does). There
are no overlays: no row is an image-side review row.

## How to redo it

```
.venv/bin/python code/parse_schedule_c_v2.py --fy 2018      # about 1 min on a laptop CPU
for y in 2019 2020 2021 2022 2023 2024 2025 2026 2027; do .venv/bin/python code/parse_schedule_c_v2.py --fy $y; done   # must not change
.venv/bin/python -m pytest code/test_schedc.py
git show 26a5ab8:data/fy18/schedule_c/fy18_schedule_c_awards.csv > /tmp/old.csv
python3 -I research/2026-10-22-fy18-schedule-c-review/s20_check.py /tmp/old.csv \
    research/2026-10-22-fy18-schedule-c-review/data/fy18_sc_awards.csv \
    research/2026-10-22-fy18-schedule-c-review/data/fy18_sc_s20_check.csv
```

Same tool versions as FY2019. The run is byte-identical on re-run (checked). FY2019–FY2025 and
FY2027's outputs are byte-identical with this branch's code; FY2026's too except the 4 decision
cells a re-run fills from its committed decisions file.

## What these checks cannot prove

- **For the 646 rows checked only by pixel rules, the text of each field is read once** (the
  h-rule tables and the tables with no drawn vertical rules, all in the body).
  *Update 2026-10-23 (#193):* the image side now finds these tables' columns itself (the header's
  labels and the blank strips between them, `imagegrid.pixel_columns`) and reads 645 of these rows
  a second time: all agree on every field (`image_check` `columns_agree`, `lattice`
  `vector+columns`). The other row (p.107, Urban Health Plan, its EIN printed `15-24042810`) keeps
  its band check only. On the page it sits in the MWBE Leadership Associations table, under that
  table's header; the vector parse splits the table at that row into three (tables 3, 4 and 5, a
  split older than #193), so the image side sees a one-row table with no header. It takes the
  last header for such a table only when its EIN column holds a well-formed EIN, and this one
  does not. Like the image lattice it reads the PDF's text layer, so a
  text-layer error still passes both.
- **The fiscal conduits are kept only in the review file** (and `flags.csv`), not in an awards
  column. The partner list on p.106 is not ink-checked or read twice.
  *Update 2026-10-23 (#193):* its 28 rows are now read a second time through the pixel columns,
  and agree. It is still not ink-checked.
- **The ink check treats a table's first row as its header** (shared code, not changed).
  *Update 2026-10-23 (#192):* fixed. The first row of the 6 award tables with no header row of
  their own is now ink-checked like any other; the re-run found no unread ink in them.
- That an agency row holding a reserve is a reserve and not an award to the agency; that the
  partner list is not a set of awards; which side is right where the PDF disagrees with itself;
  which EIN Good Shepherd's p.55 row should carry.
- That an award exists which the PDF never printed; text both grids read the same wrong way.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` here (parallel sessions); for the integrator to number.

> **§NN. FY2018 Schedule C rebuilt from the PDF, checked (#111) — REVIEW NOT STARTED**
>
> **Scope.** A new, checked parse of
> `source/FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf` with the §29 toolkit
> (`config/schedule_c/fy2018.toml`). Review record: `research/2026-10-22-fy18-schedule-c-review/`.
> The old `data/fy18/schedule_c/*.csv` files are unchanged and stay the historical record
> (§27). Not served by the MCP.
>
> **Result.** 5,906 award rows, $203,804,505 (body 1,420 / $154,005,505; appendices A, B, C
> 537 / $5,610,000, 3,054 / $36,539,000, 895 / $7,650,000). Everything the first parse had is
> here except 27 rows of a partner list that are not awards; 5,031 rows are new ($101,056,774),
> Appendices B and C among them: #59's FY2018 loss. Appendix A's amounts with cents are read
> as whole dollars (§21 `fy18_aging_shift` does not arise). **All 94 of §20's FY2018 merged rows
> come back as separate awards (224 awards).** The image grid agrees on 5,260 rows.
>
> **What the PDF itself does (flagged, never fixed).**
> - **Fiscal conduit columns**: 50 rows print one; kept in the review file.
> - **Good Shepherd Services printed with another organization's EIN** (p.55, 46-1227433).
> - **Two reserves printed again as City-agency rows** (pp.36, 101); **six boxes whose rows do
>   not make them** (pp.57, 80, 85, 95, 124, 127); Community Development's TOTAL $100,000 over
>   its lines (p.38); Merit-Based Scholarships' box $75,331 over its summary line (p.69); Crisis
>   Management System's whole box $12,734 over its parts (p.93).
> - **A partner list under CWE's Jobs to Build On row** (p.106, 28 rows): read as no award.
> - **24 box/summary name differences**; boxes for the whole SAVE and Crisis Management System
>   over their parts' boxes, the parts' titles printed above their tables.
>
> **Things a re-parse must know.** Appendix A's "$N.00" amounts; TOTAL rows inside award tables;
> box titles above their tables (pp.53, 94–97); a row between two ruled tables (p.107); six
> pages where the text layer glues an EIN to the name before it; pp.115–119 blank.

## Not done here

- OCR audit (PLAN stage 10): docTR is not installed.
- Nothing added to the MCP or the public site.
