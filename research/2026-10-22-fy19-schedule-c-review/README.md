# FY2019 Schedule C, checked from the PDF (#110)

**Report generated:** 2026-10-22 04:30 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** `source/FY19/Fiscal-2019-Schedule-C-Final-Report.pdf` (sha256
`dd6e75fa…10`, 357 pages); expense disclosure as committed in `data/fy19/expense_disclosure/`;
code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #110 (epic #101). This folder is the review record. The tables are promoted to
`data/fy19/pdf/schedule_c/` by a separate PR. Same toolkit and method as FY2020
(`research/2026-10-22-fy20-schedule-c-review/`, #109), which this branch stacks on.

FY2019 prints amounts with no "$" in the member tables and the appendices, as FY2020 does (#59);
all of them are read and each appendix equals its pot. Two things are new this year:

- **A "*" column.** Most award tables print a column headed "*" between the EIN and the amount.
  p.10 says what it means: "For those organizations identified in Schedule C with an asterisk,
  either MOCS or the Council's review process has not yet been completed …". 304 rows carry
  one. No output column holds it (the columns stay the same as FY2020's); each such row has the
  routine flag `W.asterisk` in `flags` and `asterisk` in `row_flags`. Every "*" printed in the
  award tables is on a row (304 in the text layer, 304 rows).
- **A post-adoption reserve printed again as a row.** In six boxes the statement says "will
  designate $N post-adoption" and the rows include one for the City agency that holds the $N,
  with the City's EIN 13-6400434 (e.g. p.38, Adult Literacy: Department of Youth and Community
  Development, $185,000). The rows add to the whole box. Kept as printed; named exceptions.

## Results

| What | Result |
|---|---|
| Award rows | **5,995**, **$248,436,176** (body 1,551 / $198,637,176; Appendix A 523 / $5,610,000; B 3,016 / $36,539,000; C 905 / $7,650,000) |
| Printed totals | **27 / 27** category TOTALs tie; 27 / 27 categories' boxes equal their summary lines (10 of them through 15 named aliases); every initiative's rows equal what its statement designates except the 8 named below; 16 boxes held whole post-adoption print no rows |
| What didn't tie | **Eight places, named exceptions, none corrected.** Six boxes print the post-adoption reserve again as an agency row, so their rows add to the box, not the box less the reserve: Adult Literacy (p.37, DYCD $185,000), Support for Victims of Human Trafficking (p.43, MOCJ $200,000), Community Housing Preservation Strategies (p.72, four HPD rows, $179,919), Immigrant Health (p.78, DOHMH $50,000), Legal Services for the Working Poor (p.82, DSS $50,000), Prevent Sexual Assault (p.125, MOCJ $100,000). **Ending the Epidemic** (p.62): box $6,945,000 less $1,270,000 = $5,675,000; its 52 rows add to $5,825,000, $150,000 more, with no agency row: the PDF disagrees with itself. A box for the whole SAVE initiative over its three parts' boxes (p.49). The roll-up gap (+$914,919) is exactly the first seven |
| Community Boards | p.59 "allocated directly to the Community Boards and each is designated $42,500": 59 × $42,500 = $2,507,500, the box (a named exception, since the check reads $42,500 as the stated total) |
| A list that is not awards | **pp.105–106**: under CWE's "Jobs to Build On**" row ($5,154,200), "**Below is a list of the Jobs to Build On service providers partners": 28 rows with an EIN, $4,463,500 as printed ($2,643,500 + $1,820,000). Read as **no award** (`side_lists` in the config): they break down one award, and counting them would count that money twice. They add to $690,700 less than the row they explain. Two critical review rows. The old parse had 27 of the 28 as awards |
| Appendices | No printed total; each equals its fixed pot (DATA-ANOMALIES §19) to the dollar: **$5,610,000 / $36,539,000 / $7,650,000** |
| Not in any row | $102,483,574 held post-adoption ($35,688,075 stated reserves in 46 boxes; 16 boxes held whole, $66,795,499); $38,095,169 designated straight to an agency (DOE, CUNY, the Community Boards, the three library systems, three District Attorneys), with no rows |
| Image grid (independent) | **5,090** rows agree on every field. **903** rows (all in the body) sit in tables the image lattice cannot read (ruled with horizontal lines only, or with no drawn vertical rules); for **902** the pixels' horizontal rules confirm the row's top and bottom. **3** review rows: p.87, a two-line name with a rule between its lines, joined (looked at: one award); pp.144, 206, a name's trailing "-" that runs into the EIN column, which the image reads into the EIN (the vector cell is right) |
| Ink coverage | 0 uncovered regions on the award pages (18 loose px of 180,736,020 ink px). Self-test passes on Deutsch \| Association of Holocaust Survivors from the Former Soviet Union, Inc. \| 6,500 (p.133, Appendix A), an amount with no "$" |
| Anchor census | 6,023 EIN-shaped words, 5,995 rows with an EIN: page by page equal except pp.105–106, the 28 EINs of the partner list (named exceptions) |
| Characters | 0 characters inside an award table left out of a cell; 0 characters cross a column split in the 30 tables built from horizontal rules |
| The old parse | The first PDF parse (`f710a09`, 846 rows, $181,026,931, no appendix row) is all here on (EIN, amount) except the **27 partner-list rows** above. This build has 5,176 rows ($71,772,745) the old parse did not: 4,444 in the appendices ($49,799,000, #59) and 732 in the body. Against `data/fy19/schedule_c/` on `main` (846 rows, later repaired from the disclosure), the same 27 plus 3 rows where `main` took the disclosure's EIN: Health + Hospitals' Bellevue, Coney Island and Kings County rows in Viral Hepatitis Prevention (p.66), which the PDF prints with the City's EIN 13-6400434, not H+H's 13-2655001 |
| DATA-ANOMALIES §20 | **All 39 merged rows come back as separate awards: 82 awards, each found on (EIN, amount)** in this parse. Row by row: `data/fy19_sc_s20_check.csv` (made by `s20_check.py` from the old file at `26a5ab8`). In 38 of the 39 the lost boundary was a "*" between an EIN and its amount; in the other (p.94), a school name in the Program column between the EIN and the amount |
| DATA-ANOMALIES #59 | The appendices' rows without "$" are all read: 4,444 rows, $49,799,000, the three pots |
| Disclosure (report only) | 5,714 rows match on (EIN, amount); 5,733 without the City-EIN name rule. 281 PDF rows ($21,209,758) have no disclosure row. No prototype floor for this year |
| Review file | **38 rows**, 5 critical; largest $2,643,500 (the partner list, p.105) |

## What FY2019 does that FY2020 doesn't

Each is in `config/schedule_c/fy2019.toml` with the pages it came from; the code is shared. Each
switch changes FY2019's output when turned off (checked one by one); the FY2020–FY2025 switches
with no effect are off.

1. **The "*" column**: a header label `star`. Read into the routine row flag `W.asterisk`; any
   other text there would be a critical `H7.star`. Where a row's cells do not split under the
   "*" (p.45, the amount cell runs under it), the cell is the amount's. In the h-rule table on
   p.94 there is no "*" column; three rows print "*" at the end of the Program cell
   ("Public School / Middle School 183  *"): kept in the cell as printed, flagged
   `W.star_in_cell`, three warn review rows.
2. **A list under an award that is not awards** (`side_lists`, pp.105–106; matched on page and
   header as printed): read, not counted, one critical review row per page; its EINs are named
   `H5.page_words` exceptions and its image rows are not reported as missing.
3. **The statement label centred between its two lines** (`statement_beside_label_span`, pp.43,
   105): the loose lines beside the label whose height overlaps it.
4. **A box title's last letter in its own cell** (`box_title_tail`, p.74 "Foreclosure Buyback
   Initiativ" | "e").
5. **Earlier years' switches** turned on: FY2024's `loose_header` (pp.42, 125, the header loose
   above an h-rule table), FY2021's `header_band_words`, `edge_slivers` and
   `skip_empty_first_row` (p.54), FY2023's `sliver_chars` (p.39: "$372,20" | "3"; three warn
   review rows), FY2020's `bare_amounts`, `orphans_in_gaps`, `statement_beside_label`.
6. **Headers**: "CM Purpose of Funds", "EIN *" (an h-rule table's loose header, p.42), "Program
   *" (p.94), "Amoun" | "t" (p.39, the last letter in the white column at the table's edge).
   Two summary tables are titled without "Council" (pp.41, 102).
7. **Statements**: 14 patterns. New: "Funding is allocated directly to the … Public Library"
   (p.84), "allocated directly to the Community Boards and each is designated $42,500" (p.59),
   "… directly to the Kings County, Queens County, and Richmond County District Attorneys" (p.95),
   "will designate to service providers post-budget adoption" (p.107), "has distributed its
   allocations between the Department of Youth and Community Development and providers, as
   outlined below" (p.129, COMPASS: DYCD is a row).

## Files

| File | What it is |
|---|---|
| `REVIEW.md` | The review list in plain words, by dollars |
| `ISSUE-LOG-DRAFT.md` | #110 issue-log comments, drafted, **not posted** |
| `data/fy19_sc_awards.csv` | Every award row, same columns as FY2020 |
| `data/fy19_sc_initiatives.csv` | 136 initiatives |
| `data/fy19_sc_categories.csv` | The 27 category summary tables, line by line, with TOTALs |
| `data/fy19_sc_review.csv` | The review file (same columns as `fy20_sc_review.csv`) |
| `data/fy19_sc_checks.txt` | Every check and its numbers |
| `data/fy19_sc_flags.csv` | Every flag, including routine warns |
| `data/fy19_sc_pages.csv` | Per page: tables, award rows, EIN words, image lattice and ink numbers |
| `data/fy19_sc_disclosure_match.csv` | Each PDF row's disclosure partner or the reason it has none |
| `data/fy19_sc_manifest.json` | Input hashes and tool versions |
| `data/fy19_sc_s20_check.csv` | DATA-ANOMALIES §20: each of the 39 old merged rows, split into its awards, and the award ids that hold them now |
| `s20_check.py` | Writes that file (`python3 -I s20_check.py <old awards csv> <new awards csv> <out>`) |
| `data/overlays/` | Page crops for the 3 image-side review rows |

There is no `fy19_sc_review_decisions.csv` yet: Noel writes it (the pipeline never does).

## How to redo it

```
.venv/bin/python code/parse_schedule_c_v2.py --fy 2019      # about 1 min on a laptop CPU
for y in 2020 2021 2022 2023 2024 2025 2026 2027; do .venv/bin/python code/parse_schedule_c_v2.py --fy $y; done   # must not change
.venv/bin/python -m pytest code/test_schedc.py
git show 26a5ab8:data/fy19/schedule_c/fy19_schedule_c_awards.csv > /tmp/old.csv
python3 -I research/2026-10-22-fy19-schedule-c-review/s20_check.py /tmp/old.csv \
    research/2026-10-22-fy19-schedule-c-review/data/fy19_sc_awards.csv \
    research/2026-10-22-fy19-schedule-c-review/data/fy19_sc_s20_check.csv
```

Same tool versions as FY2020. The run is byte-identical on re-run (checked, overlays included).
FY2020–FY2025 and FY2027's outputs are byte-identical with this branch's code; FY2026's too
except the 4 decision cells a re-run fills from its committed decisions file.

## What these checks cannot prove

- **For the 902 rows checked only by pixel rules, the text of each field is read once.** That is
  most of FY2019's body (the h-rule tables and the tables whose header is printed outside the
  grid). The pixels confirm the rows; the EIN census and H7 the columns; no second reader read
  those fields.
- **The partner list on pp.105–106 is not ink-checked or read twice**: the ink check covers award
  tables only. Its sum is read from its amount column.
- **The ink check treats a table's first row as its header** (shared code, not changed).
- That an agency row holding a reserve is a reserve and not an award to the agency; that the
  partner list is not a set of awards; that Ending the Epidemic's extra $150,000 is the PDF's
  error and not a missing reserve figure.
- That an award exists which the PDF never printed; text both grids read the same wrong way.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` here (parallel sessions); for the integrator to number.

> **§NN. FY2019 Schedule C rebuilt from the PDF, checked (#110) — REVIEW NOT STARTED**
>
> **Scope.** A new, checked parse of `source/FY19/Fiscal-2019-Schedule-C-Final-Report.pdf` with
> the §29 toolkit (`config/schedule_c/fy2019.toml`). Review record:
> `research/2026-10-22-fy19-schedule-c-review/`. The old `data/fy19/schedule_c/*.csv` files are
> unchanged and stay the historical record (§27). Not served by the MCP.
>
> **Result.** 5,995 award rows, $248,436,176 (body 1,551 / $198,637,176; appendices A, B, C
> 523 / $5,610,000, 3,016 / $36,539,000, 905 / $7,650,000). Nothing the first PDF parse had is
> missing except 27 rows of a partner list that are not awards (below); 5,176 rows are new
> ($71,772,745), 4,444 of them in the appendices: #59's FY2019 loss, recovered from the PDF. All
> 27 category TOTALs tie. **All 39 of §20's FY2019 merged rows come back as separate awards (82
> awards).** The image grid agrees on 5,090 rows.
>
> **What the PDF itself does (flagged, never fixed).**
> - **A "*" column** (p.10: review not complete at adoption) on 304 rows; kept as a row flag.
> - **Six post-adoption reserves printed again as City-agency rows** (13-6400434; pp.38, 43, 73,
>   78, 82, 125): those boxes' rows add to the box, not the box less the reserve.
> - **Ending the Epidemic** (p.62): rows $150,000 more than the box less its reserve.
> - **A partner list under CWE's Jobs to Build On row** (pp.105–106, 28 rows, $4,463,500 vs the
>   row's $5,154,200): read as no award.
> - **H+H printed with the City's EIN** in Viral Hepatitis Prevention (p.66, 3 rows).
> - **15 box/summary name differences**; a SAVE box for the whole initiative over its parts' boxes
>   (p.49).
>
> **Things a re-parse must know.** Amounts with no "$" in member tables and appendices. A "*"
> column. Headers loose above h-rule tables (pp.42, 125). A statement label centred between its
> two lines (pp.43, 105). A box title's last letter in its own cell (p.74). Two summary tables
> titled without "Council" (pp.41, 102).

## Not done here

- OCR audit (PLAN stage 10): docTR is not installed.
- Nothing added to the MCP or the public site.
