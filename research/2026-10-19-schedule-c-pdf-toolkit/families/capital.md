# Capital §254 PDFs: condition, prototype parses, and whether to parse them at all

**Report generated:** 2026-10-19 23:50 EDT. Prepared by BetaNYC (Noel Hidalgo), with AI
assistance.
**Last revised:** 2026-10-20 00:18 EDT — factual QA pass (8 fixes)
**Data current as of:** the PDFs in `source/` at branch head `30fc9f3`; `data/capital/` as
committed there (Council workbooks, NYC Open Data `t474-a92g`, `46m8-77gv`, `2cmn-uidm`, pulled
2026-10-14); Christian Moscardi's OCR pipeline at PR #43 head `2191833`.
**Status:** draft. Assessment only. Nothing in this repo was changed except this file. The
prototypes are scratch scripts (about 250 lines in all), not committed.

Every number below comes from a command run on 2026-10-19 on the committed files. Effort figures are
estimates and say so. Nothing was fetched from the network except Python packages and docTR
model weights.

---

## Bottom line

- **There are 24 capital PDFs, not 23.** The survey's 12 `capital_changes` and 11
  `capital_supporting_detail` add up to 23. The 24th, `FY18/...ResoA...`, is filed as `unknown`.
  Two of the 24 are in the wrong family (see "Corrections").
- **Two document types, both easy to parse from the born-digital text.**
  - **Supporting detail** (project level: project ID, budget line, borough, title, four FY
    amounts, sponsor). A 68-line column-inference prototype was run over all 12 born-digital
    books of this type. It reconciled **all 382 printed `TOTALS FOR …` lines** (count and four
    FY sums), 17,911 rows.
  - **Resolution A, "appropriation changes"** (budget-line level: ELIMINATE / SUBSTITUTE / NEW
    values by fund code, four FY columns). The 41-line prototype checked 729 Council-series
    lines (FY2021–FY2025) against OMB's adopted budget. 724 matched to the dollar. Its own
    column-distance flag caught the 2 that failed.
- **For FY2017 and FY2019–FY2027 the PDFs add almost nothing** to 2.0's structured capital
  data. The prototype rows match `data/capital/council_capital_awards.csv` exactly for FY2016,
  FY2019, FY2024 and FY2027, and in every other year except for a handful of named rows. Those
  named rows are worth having: in four places the PDF settles something the structured data
  leaves open.
- **PDF-only years for Council capital: FY2009, FY2010, FY2011, FY2012, FY2013 and FY2018.**
  FY2014 is in no source at all. Of these:
  - **FY2011, FY2013 and FY2018 are born-digital and reconcile 99/99 printed totals.** They are
    cheap.
  - **FY2018 is the big one.** `data/capital/README.md` and DATA-ANOMALIES §26 call the year
    "missing … in no source found". But `source/` holds its supporting-detail book: Part I,
    1,485 projects, $575,000,000.
  - **FY2009, FY2010 and FY2012 exist only as image scans** of the Resolution A book (budget
    lines, not projects). FY2011 is also scanned, but it has a born-digital twin.
- **Tier D OCR works on these pages, but not through the grid path.**
  - **Recognition.** Christian's render → orient → recognize read 26 of 26 non-zero amounts
    with the right digits on 6 checked pages. It read 20 of 22 budget-line IDs right.
  - **Orientation.** It turned the sideways FY2012 scan upright on both pages (`rotate90=1`).
  - **What it gets wrong.** It reads zero cells as the letter `O` or `U`. On one page it dropped
    5 of 24 `0` cells.
  - **No lattice.** `detect_grid` finds no grid on any of the 8 pages: the separators are
    dashed lines, not rules. So column assignment has to come from word geometry, not from
    `grid.py`.

---

## 1. Inventory, as it really is

The tier, page count and image-only pages come from `data/pdf_condition.csv`. "Type" is what the
pages say: the header and row grammar, read with pdfplumber and looked at as rendered PNGs.

| FY | File (`source/`) | Pages | Tier | Type (from the pages) |
|---|---|---:|---|---|
| 09 | `FY09/fy09-adopt08_capreso.pdf` | 293 | D | Resolution A book: pp.3–279 image-only; p.2 Reso A, p.280 T&C, pp.281–293 rescindments, all text |
| 10 | `FY10/fy_2010_changes_exec_budget_top.pdf` | 98 | D | Resolution A changes, Xerox scan; blank 4, 6, 92 |
| 11 | `FY11/fy2011-FY2011-Section-254-Changes.pdf` | 74 | B | **Supporting detail** ("AS400 ID / BUDGET LINE / BORO / PROJECT TITLE / FY×4"), not a changes book |
| 11 | `FY11/fy2011-fy11_changes_executive_capital_budget_adopted_by_nycc.pdf` | 108 | D | Resolution A changes, Xerox scan |
| 12 | `FY12/fy2012-changestobudget.pdf` | 124 | D | Resolution A changes, Xerox scan, sideways |
| 13 | `FY13/fy2013-adopt12_capresowork.pdf` | 88 | A+B | Supporting detail, Parts I and III |
| 15 | `FY15/fy2015-adopt14_capresowork.pdf` | 84 | A+B | Supporting detail, Parts I–III |
| 16 | `FY16/fy2016-adopt15_capreso.pdf` | 83 | B | Resolution A book |
| 16 | `FY16/fy2016-adopt15_capresowork.pdf` | 86 | A+B | Supporting detail |
| 17 | `FY17/FY17-Sec254-Capital-ResoA-M398-Res1122-Res1123.pdf` | 94 | B | Resolution A book |
| 18 | `FY18/FY18-Sec254-Capital-ResoA-M499-Res1534-Res1535.pdf` | 96 | B | **Supporting detail**, Parts I–III (filename says ResoA) |
| 19 | `FY19/Capital-Final-Upload.pdf` | 55 | A | Council database printed from Excel (ruled grid) |
| 20 | `FY20/Supporting-Detail-for-the-FY-2020-Changes-…-Section-254-2.pdf` | 80 | A+B | Supporting detail, Part I only |
| 21 | `FY21/FY21-Sec254-Capital-ResoA-M231-Res1362-Res1363.pdf` | 73 | B | Resolution A book |
| 22 | `FY22/FY22-Sec254-Capital-ResoA-Book.pdf` | 78 | B | Resolution A book |
| 22 | `FY22/FY22-Sec254-Capital-Supporting-Detail-Book.pdf` | 92 | B | Supporting detail |
| 23 | `FY23/FY23-Sec254-Capital-ResoA-Book.pdf` | 101 | B | Resolution A book |
| 23 | `FY23/FY23-Sec254-Capital-Supporting-Detail-Book.pdf` | 89 | B | Supporting detail |
| 24 | `FY24/FY2024-Sec254-Supporting-Detail-Book_7.10.2023pwp-2.pdf` | 78 | A+B | Supporting detail |
| 24 | `FY24/Fiscal-Year-2024-Changes-To-The-Executive-Capital-Budget-…-Council.pdf` | 86 | B | Resolution A book |
| 25 | `FY25/Fiscal-2025-Capital-Changes.pdf` | 88 | B | Resolution A book |
| 25 | `FY25/Supporting-Detail-for-FY2025-Changes-…-Council-Version-24.07.17.pdf` | 87 | A+B | Supporting detail, Parts I–III |
| 26 | `FY26/Fiscal-2026-Capital-Budget-Supporting-Details-1.pdf` | 86 | B | Supporting detail |
| 27 | `FY27/Supporting-Detail-for-FY2027-Changes-…-Section-254.V4.pdf` | 80 | B | Supporting detail |

By type:

- **Resolution A books: 11.** Seven are born-digital (FY16, 17, 21–25). Four are image scans
  (FY09–12), 595 image-only pages in all (277 + 95 + 102 + 121).
- **Supporting-detail books: 13.** Twelve are unruled text. FY19 is an Excel grid.
- **No capital PDF for FY2008 or FY2014.** No Resolution A book for FY2013, FY2015, FY2018–FY2020,
  FY2026 or FY2027. No supporting detail for FY2009, FY2010, FY2012, FY2017 or FY2021.

---

## 2. Layout eras

| Era | Years | What it looks like (rendered pages viewed) | Ruled? |
|---|---|---|---|
| R1: Resolution A, mainframe report, scanned or rasterized | FY2009 (clean raster), FY2010–FY2012 (Xerox scans) | Monospace "FY 20NN APPROPRIATION CHANGES / CHANGES TO PART I" report. Budget line and title on the left; four FY columns; values stacked under ELIMINATE / SUBSTITUTE labels or "(NEW PROJECT)"; fund code after each value, `1,252,000(CN)` | No: dashed separators between blocks (FY09 p.100, FY10 pp.10 and 50, FY11 pp.10 and 50, FY12 pp.10 and 50 viewed) |
| R2: Resolution A, same report, born-digital | FY2016, FY2017, FY2021–FY2025 | Same grammar in Helvetica (FY25 p.20 viewed). Also holds Reso A (p.2), Reso B fund totals (p.3), the capital Terms and Conditions, and "Rescindments from prior capital budgets" | Horizontal block rules only |
| S1: Supporting detail, AS400 | FY2011 | `AS400 ID, BUDGET LINE, BORO, PROJECT TITLE, FY×4`, no sponsor column; title holds "ORG -- PURPOSE (SHAREPOINT ID …)" (p.10 viewed) | No |
| S2: Supporting detail, Parts I–III | FY2013, FY2015, FY2016, FY2018, FY2020, FY2022–FY2027 | `PROJECT ID` (FY26–27: `SUB ID`), `BUDGET LINE, BORO, PROJECT TITLE, FY×4, SPONSOR`; agency headings; `TOTALS FOR <AGENCY> (N PROJECTS)` and `TOTALS FOR ALL`; Part II re-lists non-city projects; Part III is a by-organization cross-tab (FY18 p.10, FY13 p.70 viewed) | No: the A+B scores come from section boxes, as the survey found |
| X: Excel export of the Council database | FY2019 | `PROJECT, POLBORO, NEWPROJECT, CD, TITLE, DESC, FY19–FY22` (p.10 viewed). Same columns as `t474-a92g` | Yes, full cell grid |

**What the rows are.**

- **Supporting detail:** one Council capital designation. Project ID (`CN`/`NC`/`CC`/`TA`/`RR`
  series), budget line (`D` / `DN` Council series), borough, title, four FY amounts (report year
  plus three), and sponsor(s).
- **Resolution A:** one budget line of the whole capital budget as the Council changed it. For
  each FY column: an ELIMINATE row, then SUBSTITUTE rows, one per fund. A line created at
  adoption carries "(NEW PROJECT)" and one row of values.
  - **Fund codes seen:** `(CN)`, `(F)`, `(S)`, `(P)`, plus `(CX)` in FY2022 and in the FY2009
    rescindment totals.
  - **Most lines are the Council series** (`D`, `DN`), 130 to 194 per year. Between 26 and 111
    per year are other lines: agency lines such as `HA-1` and `CS-2`, and borough-president lines
    such as `E-K001` and `ED-KN776`. Those have no counterpart anywhere in this repo.
    `data/capital/` keeps Council-series lines only.

---

## 3. Prototype results

### 3.1 Supporting detail (born-digital), all 12 books

**Method.** pdfplumber words (`x_tolerance=1.5`).

- **Columns** come from the header words on each page: the `BORO` and `PROJECT` x0 values, the
  x1 of each FY header, and the `SPONSOR` x0.
- **A row** starts where an agency code plus a project ID sits at the ID column and the line
  carries an amount right-aligned to an FY column. Lines without that are continuation lines
  (title or sponsor wraps).
- **Each `TOTALS FOR` line** is checked on count and on all four sums against the rows since the
  previous total. `ALL` is checked against the whole Part.

Two bugs in the first draft were the instructive part:

- **Negative amounts.** The books print technical adjustments as `-11,600,000` (FY11 `P TA002`),
  `-40,000` (FY24 `HL TA001`) and so on. The first regex dropped them, and 6 totals failed by
  exactly those amounts.
- **The FY27 Part I grand total** prints its count with a comma, `(1,213 PROJECTS)`.

With both fixed:

| Book | Rows | `TOTALS FOR` lines | Reconciled | Part I grand total as printed |
|---|---:|---:|---:|---|
| FY11 Section-254 (S1) | 1,096 | 27 | 27 | none printed (agency totals only) |
| FY13 | 1,490 | 37 | 37 | 1,252 projects, $489,312,000 |
| FY15 | 1,487 | 33 | 33 | 1,279 projects, $465,143,000 |
| FY16 | 1,550 | 35 | 35 | 1,384 projects, $500,000,000 |
| FY18 | 1,718 | 35 | 35 | 1,485 projects, $575,000,000 |
| FY20 | 1,663 | 24 | 24 | 1,663 projects, $701,210,000 |
| FY22 | 1,641 | 34 | 34 | 1,462 projects, $704,495,000 |
| FY23 | 1,547 | 32 | 32 | 1,393 projects, $879,676,000 |
| FY24 | 1,364 | 32 | 32 | 1,241 projects, $839,969,000 |
| FY25 | 1,508 | 32 | 32 | 1,327 projects, $775,000,000 |
| FY26 | 1,456 | 33 | 33 | 1,259 projects, $779,320,000 |
| FY27 | 1,391 | 28 | 28 | 1,213 projects, $853,688,000 |

**What this does not prove.**

- **Totals check counts and amounts, not text.** A wrong borough, budget line, title or sponsor
  passes them.
- **The prototype leaves known loose ends.**
  - **Page footers.** On a few pages `Page N of M` lands in the last sponsor.
  - **Totals amounts misattributed.** On FY13 the totals amounts sit 1.8 pt above their label,
    and 24 rows pick them up as "stray amounts".
  - **Wrapped FY columns.** On 20 FY27 rows the FY2028–FY2030 zeros wrap onto the next line.
  - **Part III is not parsed.** It is the by-entity cross-tab, with its own schema.

**FY19 (era X)** was parsed separately. `pdfplumber.extract_tables` (lines strategy) found one
header variant on all 55 pages and 1,625 rows of 10 cells. Every amount parsed.

### 3.2 Resolution A, born-digital (7 books)

**Method.** The header `FY nnnn` centers give the columns. A budget line (`XX-…` at x0 < 60)
opens each block. A value is an amount word, optionally followed by a `(fund)` word. Its action
is SUBSTITUTE if it sits at or below the SUBSTITUTE label, ELIMINATE otherwise, and NEW where
"(NEW" appears and there is no SUBSTITUTE.

| Book | Blocks | Values | eliminate / substitute / new | Flags raised by the prototype |
|---|---:|---:|---|---|
| FY16 | 260 | 1,964 | 892 / 892 / 180 | 8 blocks with a value missing its fund code |
| FY17 | 305 | 2,364 | 1,076 / 1,076 / 212 | 13 |
| FY21 | 187 | 1,505 | 725 / 724 / 56 | 6; 1 value far from its column |
| FY22 | 229 | 1,816 | 864 / 864 / 88 | 10 |
| FY23 | 207 | 1,692 | 804 / 804 / 84 | 9 |
| FY24 | 214 | 1,677 | 784 / 784 / 109 | 6; 1 far from column |
| FY25 | 240 | 1,937 | 920 / 921 / 96 | 11; 1 substitute count not a multiple of 4; 1 far from column |

**Against OMB's adopted capital budget** (`data/capital/omb_capital_budget_council_lines.csv`,
`release = adopted`, year 1 and year 2 summed over funding sources), using SUBSTITUTE or NEW
values for the report year and the next:

| FY | Council-series lines | = OMB | differ | not in OMB file | = Council table |
|---|---:|---:|---:|---:|---|
| 2021 | 161 | 161 | 0 | 0 | 161 of 161 |
| 2022 | 151 | 150 | 0 | 1 | 148 of 149 (the `E D001` t474 split, §5) |
| 2023 | 130 | 130 | 0 | 0 | 129 of 130 |
| 2024 | 138 | 136 | 1 | 1 | 136 of 137 |
| 2025 | 149 | 147 | 1 | 1 | 139 of 145 |

- **The two "differ" rows are prototype errors, both caught by its own flag.** In both cases
  `PV-DN05C` picked up a stray `11` from its title text (value 59.6 pt from the column center),
  giving 286,011 for a printed 286,000 (FY24 p.41) and 210,011 for 210,000 in FY25.
- **Against the Council table**, the FY2017 Resolution A matches the FY2017 Council workbook on
  192 of 192 Council-series lines.
- **Against the same year's supporting-detail Part I**, Resolution A matches on 149/149 lines
  (FY22), 129/130 (FY23), 137/137 (FY24), 142/146 (FY25) and 183/190 (FY16). Where FY23 and FY25
  differ (FY23 `E D001` $229,846,000 against $224,446,000; FY25 `ED D075` and `HA D001`, each
  $500,000 higher), OMB agrees with Resolution A. Why the two Council books differ is not settled
  here.

**Other printed anchors in these books.**

- **Resolution B fund totals.** p.3 of every R2 book prints CITY NON-EXEMPT, CITY EXEMPT,
  FEDERAL, STATE, PRIVATE and TOTAL FUNDS for four years. Example: FY25 TOTAL FUNDS
  $15,284,195,162. That is the whole adopted capital budget. It checks itself (the funds sum to
  the total) but not the changes.
- **Rescindment totals.** Only FY2009 prints them. Its born-digital pp.281–293 hold 119 rows
  summing to CN $609,615,000 and CX $90,000,000, which equal the three printed totals (TOTAL
  RESCINDMENTS $699,615,000).
- **No subtotals on the change pages.** The ELIMINATE / SUBSTITUTE grammar is the structural
  check: four values per fund row, one block per budget line.

### 3.3 Resolution A, tier D (FY2009–FY2012): Christian's OCR, two pages per book

**Run.** `render_pdf` at 300 dpi, `orient_page(gray, Engine())`, `Engine.words(upright)`,
`detect_grid(upright)`, using PR #43 code unchanged. docTR 0.12.0 and torch 2.14.1, CPU. The
dependency bounds come from `code/requirements-ocr.txt`. Each page took 6.8 to 12.4 s.

| Page | Orientation (`orient_page`) | Grid | Words | Mean conf |
|---|---|---|---:|---:|
| FY09 p.100, p.150 | 0, `projection+ocr` | none | 174, 180 | 0.953, 0.950 |
| FY10 p.10, p.50 | 0, `projection+ocr` | none | 136, 209 | 0.944, 0.952 |
| FY11 p.10 | 0, `projection+ocr` | none | 163 | 0.965 |
| FY11 p.50 | 0, `ocr-4way` | none | 238 | 0.962 |
| FY12 p.10, p.50 | **1** (quarter turn), `ocr-4way` | none | 214, 241 | 0.960, 0.962 |

I checked six pages against the rendered image, field by field: FY09 p.100 and p.150, FY10 p.10
and p.50, FY11 p.50, FY12 p.50.

- **Non-zero amounts: 26 of 26 have the right digits.** Formatting slips: `250, 000 (CN)` once,
  and `750,000( (CN)` / `0( (CN)` twice.
- **Budget-line IDs: 20 of 22 right.** Both misses put the letter O for a zero: `CS-DNO12`
  (FY10 p.10) and `PV-DNO76` (FY12 p.50).
- **Zero cells come back as letters.** Of the zero-value tokens found, 17 of 33 (FY10 p.50),
  13 of 24 (FY11 p.50), 11 of 27 (FY12 p.50) and 9 of 9 (FY09 p.150) are the letter `O` or `U`,
  not a digit.
- **Dropped cells.** On FY10 p.50, 19 of 24 ELIMINATE zeros were found and 5 were missing. FY11
  p.50 (12 of 12) and FY12 p.50 (16 of 16) lost none.
- **Labels.** `SUBSTITUTE` was read once as `SUBSTITOTE`.
- **Layout.** docTR's line grouping merges the title and value columns, so values must be
  placed by box geometry against the header word boxes. That is the born-digital prototype's
  method, run on OCR boxes.

**An independent check exists for FY2011 only.** The OCR'd FY11 Resolution A values on p.10 and
p.50 can be compared, budget line by budget line, with the born-digital FY11 supporting detail:
`CS DN012` 709,000, `CS DN312` 276,000, `PV DN072` 350,000, `PV DN088` 750,000 (FY2012),
`PV DN122` 2,000,000 (FY2012), `PV DN131` 300,000. All six equal the sums of the prototype's
FY11 supporting-detail rows.

For FY2009, FY2010 and FY2012 the only checks are internal:

- **The block grammar:** four values per fund row, ELIMINATE paired with SUBSTITUTE.
- **A second, independent read:** a second DPI, or dots.ocr per PLAN §4.
- **A human sample.**

FY2009's Resolution B page (p.3) is an image as well. It prints the adopted budget's fund
totals, not a total of the changes.

---

## 4. Year by year: is the PDF worth parsing?

"Structured" means `data/capital/council_capital_awards.csv` (Council designations, project
level). OMB means `omb_capital_budget_council_lines.csv` (FY2019 on) and
`omb_commitment_plan_council_lines.csv` (releases from 2016-04-26, in thousands).

| FY | PDF in hand | Structured source in repo | What the PDF adds | Verdict |
|---|---|---|---|---|
| 2009 | Reso A, D | none | Council-series budget lines and the non-city grantee named in each `DN` title; rescindments | PDF-only. Worth it only if pre-2013 Council capital is wanted; OCR plus a second read |
| 2010 | Reso A, D | none | same | PDF-only; same cost |
| 2011 | S1 supporting detail, B; Reso A, D | none | 1,096 project rows, 27/27 totals | **PDF-only, cheap: do it.** The Reso A scan is then optional, with a built-in check |
| 2012 | Reso A, D (sideways) | none | budget lines | PDF-only; OCR |
| 2013 | S2 supporting detail | none | 1,490 rows, 37/37 totals | **PDF-only, cheap: do it** |
| 2014 | nothing | none | — | a gap in every source here |
| 2015 | S2 supporting detail | Council workbook, captured 2014-10-25 | the adopted state | Worth it as a check. Totals are equal ($465,143,000), but 49 of 211 budget lines differ in their FY2015 sum, and the workbook has 1,347 non-zero amounts to the PDF's 1,285. The workbook looks like a later state with offsetting adjustments (one `P D056` row of −$1,647,000); not established |
| 2016 | Reso A + S2 | Council workbook (no budget line) | the budget line for every project | Low cost. All 1,385 non-zero (ID, FY, amount) entries match the workbook. The PDF supplies the budget line the workbook lacks |
| 2017 | Reso A | Council workbook | budget-line view plus non-Council lines | Redundant for Council lines (192/192) |
| 2018 | S2 supporting detail (filed `unknown`) | **none** (no workbook; t474 starts FY2019; 46m8 starts FY2019) | 1,718 rows, 35/35 totals; Part I $575,000,000 / 1,485 projects | **PDF-only, cheap, highest value: do it first.** The only outside check is existence: all 191 Part I budget lines appear in OMB's 2017-11-06 commitment plan release, but only 42 match on year-1 amount (thousands), because a plan is not a budget |
| 2019 | X (Excel grid) | t474 | nothing | **Don't.** 1,628 of 1,628 non-zero amounts match; FY2019 sum $614,910,000 equal |
| 2020 | S2 | t474 | settles 2 split records | Don't parse as data; record the 2 values (§5) |
| 2021 | Reso A | t474, OMB | non-Council lines only | Don't, for Council data (161/161 OMB, 161/161 Council) |
| 2022 | Reso A + S2 | t474, OMB | settles 1 split record | Don't; record it |
| 2023 | Reso A + S2 | t474, OMB | settles 1 split record | Don't; record it |
| 2024 | Reso A + S2 | t474, OMB | nothing | **Don't.** 1,241/1,241 exact |
| 2025 | Reso A + S2 | t474, OMB | 2 out-year amounts t474 lacks | Don't; record them |
| 2026 | S2 | Council workbook, OMB | 7 out-year rows and 1 ID the workbook lacks | Don't; record them |
| 2027 | S2 | Council workbook, OMB | nothing | **Don't.** 1,215/1,215 exact |

For FY2020–FY2027 the comparison is on (project ID number, budget line, FY, amount) for every
non-zero amount in Part I. The Council workbook's FY2027 IDs drop the agency prefix, so the IDs
were compared on series and number.

| FY | PDF non-zero | Structured non-zero | Matched | PDF only | Structured only |
|---|---:|---:|---:|---:|---:|
| 2020 | 1,662 | 1,660 | 1,660 | 2 | 0 |
| 2022 | 1,491 | 1,490 | 1,490 | 1 | 0 |
| 2023 | 1,412 | 1,411 | 1,411 | 1 | 0 |
| 2024 | 1,241 | 1,241 | 1,241 | 0 | 0 |
| 2025 | 1,327 | 1,325 | 1,325 | 2 | 0 |
| 2026 | 1,261 | 1,254 | 1,253 | 8 | 1 |
| 2027 | 1,215 | 1,215 | 1,215 | 0 | 0 |

**Resolution A in the structured era.** These books cover agency and borough-president budget
lines that this repo has no structured copy of. OMB publishes them in the full `46m8-77gv`, but
this repo keeps Council-series lines only and nothing was fetched. Parsing Resolution A for
those lines is a scope decision, not a data gap that only the PDF can fill (FY2019 on).

---

## 5. What the PDFs settle that the structured data leaves open

Each item was read in the PDF text. Each is for a review file, not a silent fix.

1. **The four of t474's five split records that the Council's own files could not settle**
   (RECONCILIATION §2: "cannot be shown from the Council's own files"; DATA-ANOMALIES §26 counts
   five, the fifth, FY2026, proven by the Council's workbook). The supporting-detail books print
   each one in full. With them, `E D001` equals the PDF in all three years.

   | Year | Project | Where | Title | Amount | Sponsor |
   |---|---|---|---|---:|---|
   | FY2020 | `E CN817` | p.39 | MORE ACCESSIBLE BATHROOMS … PARK WEST | $170,000 | JOHNSON |
   | FY2020 | `E CN832` | p.39 | P.S. 3 BEDFORD VILLAGE … GYMNASIUM | $300,000 | CORNEGY |
   | FY2022 | `E CN673` | p.34 | BRONX THEATRE HIGH SCHOOL | $55,000 | RODRIGUEZ |
   | FY2023 | `E CN136` | p.11 | P.S. 28 - AUDITORIUM LIGHTING UPGRADE | $150,000 | ABREU |

2. **FY2025 out-years.**
   - **What the PDF prints.** Part I prints two FY2026 amounts that t474 does not have: `P CN175`
     `P D019` $10,000,000 (sponsor "TECHNICAL ADJUSTMENTS", p.58) and `ED NC091` `ED DN05P`
     $6,000,000 (p.44).
   - **The total agrees with the PDF.** The printed Part I FY2026 total is $16,000,000, the sum of
     the two.
3. **FY2026 workbook.**
   - **The duplicate ID.** The workbook's duplicate `HN CN1451` is two projects in the PDF (p.50):
     `HN CN1451` $250,000 (SPEAKER) and `HN CN0092` $125,000 (POWERS).
   - **Missing out-year rows.** The PDF also prints seven FY2027 out-year rows, `NC1560`–`NC1566`,
     sponsor "ADMIN", $2,950,000 in all, that the workbook lacks. The printed Part I FY2027 total
     is $25,250,000.
4. **FY2018 exists** (above).

---

## 6. What carries over from PLAN.md (written for Schedule C)

| PLAN item | Capital |
|---|---|
| Stage 0 triage gate | Carries over as is. It already put the four scans in tier D |
| Stage 1 render, Stage 2 page map from config | Carry over. The page map is per book: Reso A, Reso B, change pages, T&C, rescindments; supporting detail Parts I, II, III |
| Stage 3 vector lattice / Stage 4 image lattice (`grid.py`) | **Do not carry over**, except FY19. Neither type is ruled. `detect_grid` returned no grid on 8 of 8 scanned pages. Columns come from header word geometry |
| Stage 5 centroid assignment rule | Carries over, applied to word boxes against header-derived column bands |
| Stage 6 ink coverage | Carries over and matters more here: it is the check for the dropped OCR zeros (FY10 p.50) |
| Stage 7 structure | New grammars: the supporting-detail row and wrap rules; the Reso A block (ELIMINATE / SUBSTITUTE / NEW, stacked funds, "CHANGE TITLE TO READ") |
| Stage 8 reconcile, H10–H13 | Supporting detail: every `TOTALS FOR` line (count and four sums), the `ALL` lines, Part II ⊆ Part I, Part III = Part II by entity, and FY27's "TOTAL NON-CITY PROJECT ALLOCATIONS" $210,677,000. Reso A: block grammar, Reso B self-sum, FY09 rescindment totals |
| Stage 9 disclosure alignment | Becomes an **alignment with `data/capital/`**, report-only: by (ID, budget line, FY, amount), and by budget line with OMB 46m8 (FY2019 on). Never used to fill a value |
| Stage 10 OCR audit, `reread_cell` banned | Carries over. For tier D it is the primary read, and PLAN §4's "second agreeing read or critical" rule applies |
| §5 provenance, raw vs clean, review file | Carry over unchanged. Add `fund` and `action` for Reso A, and `part` for supporting detail |
| Join rule (EIN, amount) | Does not apply. There is no EIN. The key is (project ID, budget line, amount) within a year, and by budget line across sources |

---

## 7. QA path and effort per type (estimates, not measured)

- **Born-digital supporting detail, FY2011, FY2013, FY2018** (PDF-only), plus FY2015/FY2016
  as checks.
  - **Build.** Write the shared parser with per-year config: header variant, Part page ranges,
    footer and wrap rules, negatives, and Part III as its own table.
  - **Checks.** All totals; the hand-written golden rows from 8–12 pages per year; and for
    FY2015 and FY2016, the alignment with the workbook.
  - **Review.** A person reads the text fields (sponsor, title, borough) on a sample, because
    totals cannot see them.
  - **Estimate:** about 1 week for all five years, mostly config and golden rows. The
    reconciliation already works.
- **FY2009–FY2012 Resolution A scans (595 image pages).**
  - **First read.** Christian's render and orient unchanged, `Engine.words`, then geometry-based
    column assignment and the Reso A block grammar.
  - **Second read.** A second pass (another DPI or dots.ocr). Ink coverage catches dropped zeros.
  - **Normalization.** One listed rule for the letter O in numeric positions, counted and flagged,
    never silent.
  - **Checks.** FY2011 against its born-digital supporting detail; FY2009 rescindments against
    their printed totals (born-digital already). FY2010 and FY2012 have nothing outside the
    document, so a human samples every page with a non-zero value.
  - **Runtime:** about 1.1 to 2 CPU-hours per pass at the measured 6.8–12.4 s per page.
  - **Estimate:** 2 to 3 weeks including review.
- **Born-digital Resolution A, FY2016–FY2025.** About 1 week, if wanted. The checks are OMB
  (FY2021–FY2025) and the Council tables (FY2017, FY2021–FY2025). Non-Council lines would have
  internal checks only.
- **FY2019 grid and the FY2020–FY2027 supporting detail.** Not as datasets. A half-day script
  that writes §5's items into the capital review file is enough.

---

## 8. Recommended order

1. **FY2018 supporting detail.** The only structured-era year with no structured source, it is
   born-digital, and the prototype already reconciles 35/35.
2. **FY2013, then FY2011 supporting detail.** Both are PDF-only, born-digital and fully
   reconciled.
3. **The §5 review items**, as a small report against `data/capital/` (no new dataset).
4. **FY2015 and FY2016 supporting detail**, as adopted-state checks and the source of FY2016's
   budget lines.
5. **Only if pre-FY2013 budget-line history is wanted:** OCR of the FY2011 scan first (it has a
   check), then FY2009, FY2010 and FY2012.
6. **Don't:** FY2017 and FY2019–FY2027 as data products, or Resolution A for Council lines in any
   year that OMB or a Council table covers.

All of this is subject to open question 1: 2.0 serves structured sources only.

---

## 9. Corrections the published record needs (flagged, not made)

1. **`data/pdf_condition.csv` and `CONDITION.md`: FY2018.** `FY18/FY18-Sec254-Capital-ResoA-…pdf`
   is `capital_supporting_detail`, not `unknown`. It has Parts I–III, 35 `TOTALS FOR` lines and
   the supporting-detail header on 79 pages. FY2018's Resolution A book is not in `source/`.
   (Recorded in `../CONDITION.md` errata, 2026-10-19. `data/pdf_condition.csv` is unchanged by
   design; the errata say to read it with this in mind.)
2. **`data/pdf_condition.csv` and `CONDITION.md`: FY2011.**
   `FY11/fy2011-FY2011-Section-254-Changes.pdf` is filed as `capital_changes` but is project-level
   supporting detail (AS400 ID, 27 agency totals). The FY2011 changes book is the scan. "FY2011 … a
   different, born-digital B listing" is right about the condition and wrong about the family.
   (Recorded in `../CONDITION.md` errata, 2026-10-19; the CSV is unchanged by design, as above.)
3. **`CONDITION.md` "capital_changes … Tier D" and DATA-ANOMALIES §1.** The four scans are the
   same Resolution A format as FY2016–FY2025, and their separators are dashed, not ruled.
   CONDITION.md says FY2009 p.100 "looked near-digital"; the OCR agrees (mean confidence
   0.950–0.953). DATA-ANOMALIES §1 lists only the FY2012 capital scan as blocked; the FY2009,
   FY2010 and FY2011 Resolution A books are image-only too.
4. **`data/capital/README.md`, `RECONCILIATION.md` §1, DATA-ANOMALIES §26: "FY2018 is in no
   source found".** It is in `source/` as a PDF. Whether a PDF-derived year may enter
   `data/capital/` is a policy question; the statement needs a qualifier either way.
5. **`data/capital/RECONCILIATION.md` §2, README "Known problems", DATA-ANOMALIES §26: four of
   the five split t474 records "cannot be shown from the Council's own files".** The Council's
   §254 supporting-detail PDFs print all four (§5).
6. **DATA-ANOMALIES §5: "Capital ResoA, FY2017 & FY2021 … no printed subtotals to verify
   against — unverifiable".** They are verifiable by budget line: FY2017 192/192 against the
   Council workbook; FY2021 161/161 against OMB and 161/161 against t474. The same section says
   FY2019 has "no subtotals to reconcile". It matches t474 on 1,628/1,628 non-zero amounts.
7. **`code/PARSING.md` (FY27 capital).** It says the two open FY27 DIFFs (`HOUSING &
   DEVELOPMENT` 63/65, `HUMAN RESOURCES` 18/19) "are in-source line-item vs. printed-subtotal
   gaps, not parser errors". They are parser errors. (`fy27_capital_reconciliation.txt` and
   DATA-ANOMALIES §12 report the 24/26 without a cause; both should name it once this is
   fixed.)
   - **Housing & Development.** The PDF prints `HD CC0707` (THE DOE FUND INC. - 2031 EASTERN
     PARKWAY, $300,000) and `HD CC0863` (EARL W.JIMERSON BALCONY RAILINGS, $300,000) on p.40.
   - **Human Resources.** It prints `HR CC0168` (ALI FORNEY CENTER, $250,000) on p.47. The old
     CSV merged that row into `HR CC1253`'s title, and `HR CC0995`'s title holds sponsor
     fragments.
   - **Both sections reconcile.** The prototype reconciles them exactly (65 projects,
     $54,135,000; 19 projects, $19,483,000). The retired `fy27_capital_projects.csv` has 1,388
     rows; the PDF has 1,391.
8. **`data/capital/README.md`, FY2015 "The Council's own file".** True. But the 2014-10-25
   capture differs from the adopted PDF in the FY2015 sum of 49 of 211 budget lines while the
   totals agree. It needs a caveat that it is not the adopted state.
9. **An earlier count of 23 files.** There are 24 capital PDFs: 12 + 11 + the `unknown` FY2018.
   After corrections 1 and 2: 11 Resolution A books and 13 supporting-detail books.

---

## 10. Open questions

1. **May PDF-derived capital enter 2.0** (`data/capital/` or a sibling), given DATA-ANOMALIES
   §27? If not, FY2009–FY2013 and FY2018 stay historical-record only, and §5 stays a review note.
2. **FY2015: the adopted PDF or the October 2014 workbook?** Which one is "the year's capital
   list" for the dataset?
3. **Why do Resolution A and supporting detail differ** on FY2016 (7 lines), FY2023 `E D001` and
   FY2025 (4 lines)? OMB sides with Resolution A where it has data. Is the difference
   non-Council money on a Council line? This needs Council Finance; nothing here settles it.
4. **Does FY2018's Resolution A book exist upstream?** And is FY2014 published at all? Neither is
   in `source/`. This assessment did not look (no Council-site calls).
5. **Is Part III (the by-entity cross-tab) a dataset, or only a check?** FY2025's earlier parse
   treated it as a sidecar.
6. **Should the capital Terms and Conditions be parsed with the T&C family?** They are bound
   inside the Resolution A books: FY09 p.280, FY16 pp.77–78, FY17 pp.88–91, FY21 pp.59–61,
   FY22 pp.72–74, FY23 pp.65–67, FY24 pp.66–68, FY25 pp.71–74. The survey's T&C family counts
   only the separate files.
7. **Tier D normalization.** Is a counted, listed "letter O → 0 in a numeric field" rule
   acceptable, or must every such cell go to review? On the pages checked that is 9 to 17 cells
   per page.
