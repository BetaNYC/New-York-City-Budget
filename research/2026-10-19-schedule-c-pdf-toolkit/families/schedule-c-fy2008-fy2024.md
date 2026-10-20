# Schedule C, FY2008–FY2024: condition of each PDF and the QA path to clean data

**Report generated:** 2026-10-19 23:52 EDT. Prepared by BetaNYC (Noel Hidalgo), with AI
assistance.
**Last revised:** 2026-10-20 00:18 EDT — factual QA pass (10 fixes)
**Data current as of:** source PDFs at `main` @ `f5740c3` (this branch adds docs only); disclosure
CSVs as committed (workbooks retrieved 2026-10-12, FY2009/FY2011/FY2012 from the Internet
Archive per §25); Christian Moscardi's `code/ocr/grid.py` from PR #43 (local branch `pr43`).
**Status:** draft. Nothing was built and no repo file changed except this one. Every number below
came from a scratch command run on 2026-10-19 (pdfplumber 0.11.9, pypdfium2 4.30.0, OpenCV 4.14.0,
Python 3.12.13); the scripts are scratch and not committed.

Companion to [`../PLAN.md`](../PLAN.md) (stages 0–11, checks H1–H17) and
[`../CONDITION.md`](../CONDITION.md) (triage: every Schedule C PDF is tier A, born-digital).
FY2025–FY2027 are assessed separately and are not repeated here.

---

## Bottom line

1. **Every year from FY2009 to FY2024 prints award rows with EINs, and FY2008 prints award rows
   without EINs.** FY2009–FY2014 print ~3,950–4,730 award rows a year in "Council
   Discretionary / Aging / Youth" (later "Local / Aging / Youth") tables, plus initiative
   designation tables. DATA-ANOMALIES §2 ("initiatives-level only … no EINs") and
   `code/PARSING.md` ("that data isn't in these documents") are wrong for all six years.
   FY2008 prints 1,674 member-item rows (Appendix E,
   $36,399,802) with no EIN column.
2. **Award EINs and conduit EINs separate cleanly by column.** In FY2009 and FY2011–FY2014 the count
   of EIN-shaped words in the award-EIN column equals, exactly, the number of vector-table rows that
   carry an EIN (FY09 3,859; FY11 4,139; FY12 4,331; FY13 4,553; FY14 4,193 on ruled pages, plus 533
   on the unruled Aging pages, which have no vector rows to compare). Conduit (FC EIN) words sit in
   their own column: 525, 163, 54, 29, 29. FY2010 has 3,994 award-column EINs and at least 286
   conduit EINs (57 on one line, 229 wrapped over three lines).
3. **Where the PDF prints an Aging or Youth total, the prototype hits it to the dollar;
   elsewhere it comes close or matches an expected amount.** FY2009 and FY2011 Appendix 1 print
   the aging and youth discretionary lines, and the vector sums match ($5,546,250 aging both
   years; youth $7,723,700 and $7,737,414). Their "Local Initiatives" lines come in $6,500 and
   $5,500 below the Council section (open question 1). FY2014 prints an Excel pivot of its
   Local section: Grand Total $36,424,244.5 against a vector sum of $36,424,247. For
   FY2015–FY2024 no appendix total is printed; the computed appendix sums equal the fixed pots
   in DATA-ANOMALIES §19 ($5,610,000 / $36,539,000 / $7,650,000) in every year except
   FY2016–FY2017 Local ($36,538,000; $36,538,500).
4. **The ruled-table years (FY2009, FY2011–FY2024) pass the two-lattice test on award pages.** On 75
   sample pages (FY2009–FY2024) plus 3 for FY2008, every award table where both lattices ran agreed
   on rows and columns, except at known blind spots: dark or gray header bars, white-fill phantom
   columns, a table edge at the page border. Three structures defeat both lattices and need their
   own path: **FY2010's banded rows** (vertical rules only, alternating gray fills), **FY2014's
   unruled Aging section** (pp.78–112), and **h-rule-only initiative tables** in FY2015–FY2024 (no
   vertical rules: 0 to 27 pages a year).
5. **New PDF self-errors to flag:** FY2017 Appendix C (Youth) prints 897 of 922 EINs in Excel
   scientific notation (`8.61E+08`), so they cannot be recovered from the PDF. Short EINs,
   `EX…` exemption codes, `Pending`, `N/A` and blank EIN cells sit on real award rows (125 such
   rows across the FY2009–FY2012 award sections alone).
6. **The old parse lost most of the award stream before FY2021.** For FY2009–FY2014 it emitted
   none. For FY2015–FY2020 it emitted no appendix rows except FY2018 Aging, although the PDFs
   print 4,391–4,598 appendix rows a year. In FY2023 it dropped two Local rows ($10,000): one
   EIN prints with an internal space, the other with a hyphen the text layer encodes as a soft
   hyphen (U+00AD). That also falsifies the "seat vacancy / rounding"
   explanation DATA-ANOMALIES §19 gives for FY2023's $36,529,000.

---

## How this was measured

- **Census (every page, all 17 PDFs):** pdfplumber `find_tables()` (lines strategy) per page;
  EIN-shaped words (`NN-NNNNNNN` or 9 digits after trimming `*`/`-`); EIN-shaped substrings of
  the page text; `$` amounts; cell text per table. Rule counts come from
  `data/pdf_condition_pages.csv`.
- **Column roles:** histograms of EIN-word x-centers per section (award EIN column vs FC EIN
  column), and content-majority column roles per table (leftmost EIN-majority column = award
  EIN, amount-majority column = amount).
- **Section sums:** every row of every vector table in a section's page range with an amount;
  rows whose EIN cell is not EIN-shaped are counted and listed, not dropped. Per-year
  `x_tolerance` as measured below.
- **Lattice prototype (sample pages, 3–7 per year: 75 pages over FY2009–FY2024, plus 3 for
  FY2008):**
  the vector lattice from pdfplumber, against Christian's `grid.detect_grid` run per table region
  (connected components of a 60 px rule mask, padded 8 px, integer kernel divisor giving a
  ~60 px kernel on the shorter axis, as in the FY2027 run), rendered at 300 dpi with pypdfium2.
  Row separators were matched at 1 pt and column separators at 2 pt.
- **Pages looked at:** FY08 p.36; FY09 pp.8, 100; FY10 pp.62, 300; FY14 pp.80, 200; FY15
  p.28; FY17 pp.50, 320; FY20 p.38; FY24 p.41. They were rendered to PNG and read, not inferred.
- **Disclosure match (sample pages only):** (EIN, amount) multiset against
  `data/fyNN/expense_disclosure/fyNN_expense_awards.csv`, never EIN alone, never the member.

**One coordinate trap found on 2026-10-19:** FY2020 (12 pages) and FY2024 (216 pages) have a
non-zero MediaBox origin. The PDF stores `[-18.03, 17.97, 773.97, 629.97]` (FY2024 p.227), a
lower-left corner of (−18, 18) in PDF space; pdfplumber's top-down frame reports the same box as
(−18.03, −17.97, …). pdfplumber reports coordinates in that frame and the render does not, so
every separator missed by ~18 pt until both were normalized to the page origin. The FY2024
landscape pages went from "every separator differs" to "exact". This is a stage-3 requirement
(normalize to the MediaBox origin), not a per-year config value.

---

## Eras

| Era | Years | Producer | What defines it |
|---|---|---|---|
| **A. Adjustments Summary + Appendix E** | FY2008 | Mac OS X Quartz, combined in Acrobat 8.1 | Agency-by-agency narrative (pp.4–30), cultural lists App. A–D (pp.31–34, unruled), one fully ruled 5-column member-item table (App. E, pp.36–123): Legal Name, Purpose, Agency, Amount, Council Member. **No EIN column.** |
| **B. Two sections + Appendix 1** | FY2009–FY2011 | Distiller 8.1 (FY09); ScanSoft PDF Create! 5 (FY10, FY11) | §1 initiatives: summary table + `Program:` blocks + designation tables `Organization │ * │ Amount │ Tax ID#`. §2 Discretionary Allocations: Council (10 cols: Council Member, Sponsor, Legal Name, EIN, *, Amount, Agency, Purpose, Fiscal Conduit Name, FC EIN), Aging and Youth (8 cols, no Sponsor/Agency). Appendix 1 totals by agency and U/A (FY09, FY11). **FY2010 is a sub-variant with banded rows.** |
| **C. Budget Disclosures with a Source column** | FY2012–FY2014 | ScanSoft (FY12); Word 2010 (FY13, FY14) | One 11-column table: Source (`Local`/`Aging`/`Youth`/`Boro`), Sponsor, Council Member, Legal Name, EIN, *, Amount ($), Agency, Purpose, FC Name, FC EIN. A4 landscape (FY12, FY14). Header printed once per section in FY12–FY13. FY14 adds an unruled Aging section, an 8-column Youth table, child-care and OST appendices and an Excel pivot of Local. |
| **D. Appendix template, asterisk column** | FY2015–FY2019 | Acrobat Pro 11 (FY15–FY17); Word 2016 (FY18–FY19) | Initiative body (Anti-Poverty, Boroughwide Needs, per-initiative org tables, Speaker's Initiative "Sponsor" table from FY17) then Appendices Aging / Local / Youth. `*` column. Appendix amounts printed bare (`10,556`). FC columns through FY2018; gone in FY2019 Local. FY2018–FY2019 add "– Program Name" and "CM Purpose of Funds". |
| **E. No asterisk, "Tax ID"** | FY2020–FY2023 | Word 2016; Adobe PDF Library 20/22 | `*` column gone (FY20). Header says `Tax ID` from FY2021. `$` amounts in appendices from FY2021. Otherwise Era D. |
| **F. FY2025–27 layout** | FY2024 | Adobe PDF Library 23.3 | Excel-inserted landscape pages (1148×887), per-member initiative tables (`Council │ Legal Name – Program Name │ Tax ID │ Amount │ Agency`), headers repeated at the *bottom* of some tables, non-zero MediaBox origins. Same shape as FY2025–FY2027. |

---

## Summary table

"Appendix rows" are the vector-table rows in the year's Local/Aging/Youth (or Council/Aging/Youth)
sections, with an amount, counted by the prototype. "Init EIN tokens" are EIN-shaped words on
the initiative-section pages. They are an upper bound (they include conduit EINs and prose
designations). "Old" means the committed `data/fyNN/schedule_c/` rows.

| FY | Era | Pages | Appendix rows (L/A/Y) | Appendix $ (L/A/Y) | Init EIN tokens | Lattice result | Old parse rows (body; appendices) | Tier | Days (est.) |
|---|---|---:|---|---|---:|---|---|---|---|
| 08 | A | 123 | 1,674 (App. E, no EIN) | $36,399,802 | 0 | data rows agree; header bar differs | none | A, no-EIN schema | 1.5–2 |
| 09 | B | 246 | 2,265 / 652 / 1,038 | 35,390,983 / 5,546,250 / 7,723,700 | 151 | exact on award pages | 0; 0 (initiatives only) | A | 2–3 |
| 10 | B (banded) | 408 | not countable by lattice; 3,994 award EINs | — | 293 | rows fail both lattices | 0; 0 | A cols / B rows | 4–6 |
| 11 | B | 291 | 2,552 / 607 / 988 | 36,643,833 / 5,546,250 / 7,737,414 | 214 | exact | 0; 0 | A | 2–3 |
| 12 | C | 393 | 2,810 / 573 / 953 | 36,393,631 / 5,546,250 / 7,737,414 | 162 | exact | 0; 0 | A | 2–3 |
| 13 | C | 258 | 3,046 / 575 / 933 | 36,418,231 / 5,546,250 / 7,737,414 | 512 | exact (phantom cols in init) | 0; 0 | A | 2.5–3 |
| 14 | C | 439 | 3,198 / 533 EINs unruled / 1,003 | 36,424,247 / — / 7,722,414 | 718 | exact rows; header fill | 0; 0 | A + B (Aging) | 3–4 |
| 15 | D | 292 | 3,107 / 552 / 939 | 36,539,000 / 5,610,000 / 7,650,000 | 657 | exact; h-only init | 652; 0 | A | 2–3 |
| 16 | D | 352 | 2,955 / 526 / 910 | 36,538,000 / 5,610,000 / 7,650,000 | 1,130 | exact; h-only init | 335; 0 | A | 2.5–3 |
| 17 | D | 355 | 3,043 / 549 / 922 | 36,538,500 / 5,610,000 / 7,650,000 | 1,597 | exact; h-only init | 364; 0 | A, EINs lost in Youth | 3–4 |
| 18 | D | 357 | 3,054 / 537 / 895 | 36,539,000 / 5,610,000 / 7,650,000 | 1,449 | exact | 480; 422 Aging only | A | 2.5–3 |
| 19 | D | 357 | 3,016 / 523 / 905 | 36,539,000 / 5,610,000 / 7,650,000 | 1,579 | exact; h-only init | 846; 0 | A | 2.5–3 |
| 20 | E | 405 | 2,986 / 510 / 897 | 36,539,000 / 5,610,000 / 7,650,000 | 3,525 | exact; h-only init | 2,841; 0 | A | 2.5–3 |
| 21 | E | 343 | 2,902 / 514 / 894 | 36,539,000 / 5,610,000 / 7,650,000 | 1,863 | exact | 1,810; 4,310 | A | 2 |
| 22 | E | 326 | 2,790 / 510 / 882 | 36,539,000 / 5,610,000 / 7,650,000 | 1,545 | exact | 1,492; 4,182 | A | 2 |
| 23 | E | 334 | 2,728 / 489 / 841 | 36,539,000 / 5,610,000 / 7,650,000 | 1,867 | exact; h-only init | 1,848; 4,056 | A | 2–2.5 |
| 24 | F | 453 | 2,616 / 477 / 818 | 36,539,000 / 5,610,000 / 7,650,000 | 5,378 | exact after origin fix | 5,368; 3,911 | A | 2.5–3 |

Day estimates are year-specific work on top of the shared pipeline in PLAN.md (PRs 1–9). They
are estimates, not measurements.

---

## Cross-year findings that shape every plan

### Rows that carry no EIN are still award rows

The section sums count rows that have an amount but no EIN-shaped value in the award-EIN cell:

| FY | Local / Council | Aging | Youth | What the cell holds |
|---|---:|---:|---:|---|
| 09 | 44 | 23 | 29 | blank 75, `EX` + 6 digits 15, 8-digit `NN-NNNNNN` 4, `NN-NNNNNNA` 1, spaced `NN NNN NNNN` 1 |
| 10 | 10 | 3 | 3 | blank 6, `EX…` 5, `O`+8 digits 1, `NNN-NNNNNN` 1, `N/A` 1, 2 not itemized (counts on fragmented tables) |
| 11 | 7 | 1 | 0 | blank 5, `NA` 1, 8-digit 1, `Ex NNNNNN` 1 |
| 12 | 4 | 0 | 1 | blank 4, `NNNNNN (Scho…` 1 |
| 13 | 1 | 0 | 0 | blank 1 (plus 13 8-digit EINs in initiative tables) |
| 14 | 8 | — | 0 | blank 8 |
| 16 | 2 | 0 | 0 | 8-digit 2 |
| 23 | 2 | 0 | 0 | `84 -2079676` (printed space); `87-0753479` (prints a hyphen; text layer has U+00AD soft hyphen) |

So H5's anchor census cannot be "one EIN per row". It must be "one amount per row; EIN cell
either EIN-shaped or a named exception." Each of these is a review row, not a fix. FY2009's
initiative tables also print `Pending` in the Tax ID# column on 36 rows.

### Ruling, by structure

| Structure | Years | Vector lattice | Christian's image lattice | Path |
|---|---|---|---|---|
| Fully ruled award tables | FY08 App. E, FY09, FY11–FY24 appendices and member tables | rows and columns | agrees on data rows | PLAN stages 3–5 unchanged |
| Dark/gray header bar | FY08 (dark fill), FY14 (0.75-gray fill, no stroke), FY24 headers | two edges | one separator mid-bar, or none | known blind spot; H8 skips header band |
| White-fill phantom columns | FY09 p.8, FY13 pp.16, 64, FY14 p.26, FY22 p.53, FY24 pp.41, 100, 203 | extra separators | none | drop rule from PLAN stage 3 |
| Banded rows (vertical rules + alternating gray fills) | FY10 award section pp.60–407 | fragments into 1,772 tables (census) | columns only; rows missed (fills lighter than the 128 threshold) | rows from fill rects + text baselines; new code |
| Unruled table | FY14 Aging pp.78–112 (0 h, 0 v rules on pp.79–80) | none | none | tier-B column inference from header-word x |
| h-rule-only tables (no verticals) | initiative org tables, FY15–FY24 | no table, or a degenerate one built from white fills | `None` (needs ≥2 columns) | rows from h-rules, columns from header words |
| First row above the first drawn rule | FY10 continuation pages (139 pages miss exactly one EIN); FY24 pp.41–45 | row missed | row missed | caught only by the H5 anchor census |

**Pages with EINs but no usable vector table (h-rule-only, `v_rules` ≤ 2):** FY15 1 page (19
EIN words), FY16 9 (254), FY17 18 (493), FY18 5 (72), FY19 15 (250), FY20 24 (456), FY21 0,
FY22 1 (26), FY23 14 (190), FY24 27 (558). More pages have a few stray verticals and are
partly missed: FY20 10 pages (218), FY23 13 (222), FY24 17 (224). FY2009, FY2013 and FY2014
also have initiative pages (14, 11 and 10 before p.66) where single-provider EINs print in
prose (`Tax ID#: 02-0694269`, FY09 p.8). Those are designation statements, not table rows.

### Text extraction, by year

Share of words with an internal case or comma junction (`AmericanPlaceTheatre,Inc.`), on the
sample pages, at pdfplumber `x_tolerance` 3 / 1.5 / 1:

| FY | tol 3 | tol 1.5 | tol 1 | Setting |
|---|---|---|---|---|
| 08, 09, 15–24 | 0.0–0.6% | same | same | default 3; residuals are real names (`CityParks`, `McNair`) |
| 10 | 25.8% | 0.0% | 0.0% | 1.5 |
| 11 | 30.6% | 0.0% | 0.0% | 1.5 |
| 12 | 36.2% | 19.2% | 0.0% | 1.0 (word count 3,399 at 1.0, 3,404 at 0.5) |
| 13 | 4.6% | 4.6% | 0.2% | 1.0 |
| 14 | 14.6% | 1.3% | 0.4% | 1.0 (residual `BronxWorks` is a real name) |

Other print formats, from census cells: EINs are hyphenated through FY2012 and mostly bare
9-digit from FY2013 (FY13 4,812 bare vs 235 hyphenated). Amounts print as `$6,000.00` in
FY2010 (3,871 cells) and in FY2018 Aging (537), and bare (`10,556`) in FY2015–FY2020
appendices (4,482–5,062 cells a year). FY2011 Youth prints bare amounts too (988). 8-digit
EINs: FY09 4, FY11 2, FY13 13, FY14 5, FY15 1, FY16 2, FY18 1, FY20 2, FY21 6, FY22 4.

### Independent checks available

| Source | Years | What it checks |
|---|---|---|
| Appendix 1 "Totals by Agency and U/A" | FY2009 (pp.235–245), FY2011 (pp.284–291) | DFTA "Council Member Discretionary Funds" = Aging section; DYCD U/A 312 "Council Member Discretionary Funds" = Youth section; "Local Initiatives" lines by agency ≈ Council section; citywide total ($412,044,737; $394,999,169) |
| Excel pivot, Local by Source and member | FY2014 p.388 | Boro 987,674.5; Local 35,436,570; per member; Grand Total 36,424,244.5 |
| Category summary `TOTAL` lines | every year FY2009–FY2024 (20–40 lines) | H10/H11, as the old legacy parser already did |
| "Designation Method" statements | 112–191 per year, FY2009–FY2024 | H12 (initiative rows sum to designated amount) |
| Fixed appendix pots | FY2015–FY2024 (and FY2011–FY2013 Aging/Youth) | W1 |
| Council disclosure workbook | FY2009 (early snapshot), FY2011–FY2024 | W2, report-only |
| None | FY2008 (no workbook, no App. E total); FY2010 (workbook not loaded, incomplete) | ink coverage + H5 only |

---

## Per-year assessments

### FY2008 — `source/FY08/schedule_c_rvs_2008.pdf`

1. **File.** 123 pp; Mac OS X 10.4.9 Quartz PDFContext, combined in Acrobat 8.1; 88 landscape
   792×612, 35 portrait. Era A.
2. **Sections.** Cover p.1; ToC pp.2–3 (by agency code, `(010) Borough President –
   Manhattan … (945)`); agency narratives pp.4–30 (each action with a `$` amount, e.g. p.30
   "PS Enhancement $53,160"); Appendix A–D pp.31–34 (cultural lists, unruled, each with a
   `TOTAL`); Appendix E "Discretionary Allocations" divider p.35; App. E table pp.36–123.
   Header `Legal Name │ Purpose of Funds │ Agency │ Amount │ Council Member`, repeated on
   every page (88 pages). No EIN, no initiative, no sponsor column.
3. **Ruling.** App. E is fully ruled with alternating gray row fills (p.36 viewed). h-rules
   median 21.5 per page, 1 page with fewer h-rules than amount tokens.
4. **Prototype (pp.36, 80, 123).** 5 columns agree exactly. Data rows agree. The only
   disagreement is the dark header bar: vector edges 36.4/48.4 pt, image one separator at
   42.2 pt. Text clean at the default tolerance (0.3% junctions, all real names like
   `McMahon`). Multi-member cells print as `Felder, Gentile` and `Manhattan Delegation`.
5. **Totals.** 1,674 rows, $36,399,802 (DYCD 864 rows, $17,781,636; DFTA 144, $4,230,594 …).
   App. E prints no total. The narrative prints DFTA "Council Member Discretionary Funds
   $5,546,250" (p.15) and DYCD $7,737,414 (p.18), but App. E's DFTA rows sum to $4,230,594,
   so the aging and youth pots are *not* itemized in this PDF. 0 EIN tokens.
6. **Disclosure.** None exists for FY2008.
7. **Old parse.** None ("Untouched", DATA-ANOMALIES §5; "deferred", `code/PARSING.md`). The PDF does
   hold 1,674 award rows.
8. **QA path.** Tier A, but with a no-EIN schema: the award key is (legal name, amount, member,
   agency), and PLAN's (EIN, amount) checks do not apply. Stages 0–8 and 11 apply; stage 9
   does not; H5 becomes "one amount cell per row". App. A–D need tier-B handling and reconcile
   to their own `TOTAL`s. Review load is small: the header-bar class, about 13 `$` tokens
   inside purpose text, multi-member cells. **1.5–2 days.**

### FY2009 — `source/FY09/fy09-Schedule-C-final.pdf`

1. **File.** 246 pp; Acrobat Distiller 8.1.0 / PDFMaker 8.1 for Word; 188 pages carry
   `/Rotate` 90 (57–167, 169–193, 195–246) and render upright. One Type0 font without ToUnicode
   (decodes cleanly). Era B.
2. **Sections.** §1 initiatives pp.4–53, with a summary table per category (21 summary
   tables, 22 `TOTAL` lines, pp.4–51) and 11 designation tables `Organization │ * │ Amount │
   Tax ID#` (pp.8–50). §2 divider p.55. Council Discretionary pp.57–167 (10 cols); Aging
   pp.169–193 (8 cols); Youth pp.195–234 (8 cols, header row merged into one cell). Appendix 1
   pp.235–245; Budget Disclosures p.246.
3. **Ruling.** Fully ruled (p.100 viewed: 10-column grid, purpose wraps, bottom-aligned
   cells). pp.169–234 have the table's top rule at the page edge.
4. **Prototype (pp.8, 100, 180, 210).** pp.100 and 180 exact (25×10 and 38×8). p.210: 24 of 25
   row separators match; the vector-only one is the top edge at y=0.4 pt, on the page border.
   p.8: the designation table is exact (4×4), and the summary table differs by its title bar
   and two white-fill slivers. Text clean at tolerance 3.
5. **Totals and anchors.** Award-column EIN words 3,859 (x≈260–310 pt) and conduit 525 (x≈730),
   on pp.57–234. Vector rows with an EIN = 3,859, exactly. 96 more rows have an amount and a
   non-EIN cell (table above). Section sums: Council 2,265 rows $35,390,983; Aging 652 rows
   **$5,546,250 = App. 1 DFTA line**; Youth 1,038 rows **$7,723,700 = App. 1 DYCD U/A 312
   line**. App. 1's 52 "Local Initiatives" lines sum to $35,384,483, $6,500 below the Council
   section. Unresolved: a line this regex missed, or a PDF self-difference.
6. **Disclosure.** FY2009 loaded (Internet Archive; early snapshot, 1,389 of 5,745 Pending).
   Sample pp.100, 180, 210: 77 of 85 rows match on (EIN, amount).
7. **Old parse.** Initiatives only (123 rows, 21/22 categories reconciled). It emitted no award
   rows, although the PDF prints 3,955.
8. **QA path.** Tier A. Stages 0–11 apply unchanged, with the rotation-applied page geometry.
   Config: section page ranges, three header variants (one merged), conduit column, the 36
   `Pending` and 96 non-EIN rows as named exceptions. App. 1 adds a printed check for Aging and
   Youth (H13-like), and Local within a few thousand dollars. Review load: about 100 exception
   rows plus the $6,500. **2–3 days.**

### FY2010 — `source/FY10/fy_2010_sched_c_final.pdf`

1. **File.** 408 pp; ScanSoft PDF Create! 5 from Word; 348 landscape. Era B, banded variant.
2. **Sections.** §1 initiatives pp.3–57 (17 designation tables `Organization │ * │ Amount │
   TaxID#`, 21 summary tables). §2 divider p.59. Council pp.60–283 (column header printed once,
   p.61, 16 vector columns incl. phantoms), Aging pp.284–331, Youth pp.332–407. No Appendix 1.
   p.408 is a closing page (81 characters).
3. **Ruling.** **Vertical rules only; rows are separated by alternating gray fills and no
   horizontal rules** (pp.62 and 300 viewed). A row continues across the page break (p.300
   opens with the tail `Association, Inc.` of a conduit-name cell). On 139 pages exactly one EIN
   falls outside every vector table, because the first row sits above the first fill band.
4. **Prototype (pp.15, 62, 300, 350).** p.15 (initiative table) exact. Award pages: the
   vector lattice fragments into 4–7 tables per page (1,772 tables in the year), and the image
   finds 6–9 rows where the vector finds 10–25. **Neither lattice can delimit rows here.** Text
   is glued at tolerance 3 (25.8%) and clean at 1.5.
5. **Anchors.** Award-column EIN words 3,994 (x≈290–320 pt). Conduit 57 on one line, plus **229
   FC EINs wrapped over three lines** (`13-⏎34020⏎57`, p.62). Amounts print with cents
   (3,871 cells). The section sums are not reliable on fragmented tables (Aging gives 572 rows
   against 701 EIN words), so none is reported as a result.
6. **Disclosure.** Not loaded: the archived workbook is incomplete (2,592 rows vs NYC Open Data
   5,981; `data/disclosure_years.csv`). No sample match was run.
7. **Old parse.** Initiatives only (124 rows, 21/21). No award rows.
8. **QA path.** Tier A for columns, tier B for rows. New code is needed for row bands: gray fill
   rects from the vector stream as the row skeleton, white gaps between bands as rows, and
   cross-page continuation. H8 runs on columns only. H5 (one award EIN or named exception per
   row) and H9 (ink) carry the completeness load. Wrapped FC EINs join under a digits-only rule
   that is logged. There is no printed appendix total and no disclosure. **4–6 days; do it last
   among FY09–FY14.**

### FY2011 — `source/FY11/fy2011-C2011.pdf`

1. **File.** 291 pp; ScanSoft PDF Create! 5; 239 landscape; pp.2–52 draw the header rule as a
   4224×4 px image (PLAN §2.1). Era B.
2. **Sections.** Initiatives pp.3–52 (18 designation tables `Organization │ TaxID# │ * │
   Amount`, 20 `TOTAL` lines). Council pp.53–194 (10 cols, header on all 142 pages); Aging
   pp.195–223 and Youth pp.224–283 (8 cols, 89 pages); Appendix 1 pp.284–291.
3. **Ruling.** Fully ruled. Rule-to-EIN ratio 1.15.
4. **Prototype (pp.9, 100, 250).** All three exact (43, 23 and 17 rows). Text glued at
   tolerance 3 (30.6%) and clean at 1.5.
5. **Totals and anchors.** Award-column EINs 4,139; conduit 163. Vector rows with EIN = 4,139,
   exactly. Sections: Council 2,552 rows $36,643,833; **Aging 607 rows $5,546,250 = App. 1 DFTA
   line; Youth 988 rows $7,737,414 = App. 1 DYCD U/A 312 line.** App. 1 "Local Initiatives"
   (53 lines) $36,638,333, $5,500 below the Council section (same open question as FY2009).
   App. 1 citywide $394,999,169.
6. **Disclosure.** Loaded (Internet Archive). Sample pp.9, 100, 250: 78 of 80 match.
7. **Old parse.** Initiatives only (110 rows, 18/19 with "Education +$250k in-source"). No award
   rows.
8. **QA path.** Tier A, the cleanest early year. Stages unchanged; config `x_tolerance`=1.5,
   two header variants. Review: 8 non-EIN rows, the $5,500. **2–3 days. Pilot year for eras B
   and C.**

### FY2012 — `source/FY12/fy2012-skedcfinal.pdf`

1. **File.** 393 pp; ScanSoft from Word (.docx); 335 pages A4 landscape (842×595). Era C.
2. **Sections.** Introduction and 18 categories pp.3–57 (14 designation tables `Organization
   │ Amount │ TaxID#`); "FY 2012 Budget Disclosures" p.58; one 11-column Source table, Aging
   pp.59–93, Local pp.94–316, Youth pp.317–393. The column header prints only 3 times (start of
   each section), so the column identity on other pages comes from geometry.
3. **Ruling.** Fully ruled (h median 14, v 12 per page); 10 pages with fewer h-rules than EINs.
4. **Prototype (pp.34, 100, 200, 350).** All four exact. Text: tolerance 1.0 needed (36.2% glued
   at 3, 19.2% at 1.5, 0.0% at 1.0).
5. **Totals and anchors.** Award EINs 4,331; conduit 54; vector rows with EIN 4,331. Sections:
   Aging 573 rows $5,546,250 and Youth 953 rows $7,737,414, the same pots App. 1 prints for
   FY2009/FY2011. Local 2,810 rows $36,393,631. No App. 1 and no pivot, so Local has no printed
   total.
6. **Disclosure.** Loaded. Sample: 65 of 67.
7. **Old parse.** Initiatives only (97 rows, 16/16). No award rows.
8. **QA path.** Tier A. Config: `x_tolerance`=1.0, section ranges from the Source column, header
   carried by column geometry across pages. Review: 5 non-EIN rows. **2–3 days.**

### FY2013 — `source/FY13/fy2013-FY-2013-Schedule-C-Merge-Final1.pdf`

1. **File.** 258 pp; Word 2010; 194 landscape letter. Era C.
2. **Sections.** Categories pp.3–62 (designation tables in four header orders, e.g. `Organization
   │ Amount │ Tax ID#` and `Organization │ Tax ID # │ Amount`). "Out of School Time (OST)
   Restoration Chart" pp.64–69 (`MOCS * │ PROVIDER NAME │ EIN │ SITE NAME │ Award`, 238 EINs).
   "FY 2013 Budget Disclosures" p.70. Source table: Aging pp.71–90, Youth pp.91–122, Local
   pp.123–258 (header 3 times).
3. **Ruling.** Fully ruled; designation and OST tables carry white-fill phantom columns.
4. **Prototype (pp.16, 64, 100, 200).** pp.100, 200 exact. pp.16 and 64: rows agree (42, 40), with
   6 and 10 vector-only column separators (phantoms). Text needs tolerance 1.0 (4.6% → 0.2%).
5. **Totals and anchors.** Award EINs 4,553 (counted at tolerance 1); conduit 29; vector rows with
   EIN 4,553. Aging 575 rows $5,546,250; Youth 933 rows $7,737,414; Local 3,046 rows
   $36,418,231. 13 8-digit EINs in initiative tables. Census tokens on initiative pages: 512.
6. **Disclosure.** Loaded, but an early snapshot with 18 citywide initiatives as lump rows.
   Sample: 86 of 131. Of the 45 unmatched, 39 are OST site rows on p.64 and 6 are p.16
   designations with split amounts ($81,333, $41,667).
7. **Old parse.** Initiatives only (121 rows, 17/17).
8. **QA path.** Tier A. Config `x_tolerance`=1.0, four designation-header variants, OST chart as
   its own table type (scope decision: open question 4). **2.5–3 days.**

### FY2014 — `source/FY14/fy2014-skedc.pdf`

1. **File.** 439 pp; Word 2010; 361 A4 landscape, 65 letter portrait, 12 letter landscape, 1 A4
   portrait (p.388). Excel-inserted runs number their own pages ("Page 3 of 35", "p. 88 of 276").
   Era C.
2. **Sections.** Categories pp.5–60 (30+ designation tables `Organization │ EIN# │ Amount`);
   Appendix A "Discretionary Child Care Allocations" pp.66–67 (with Tax ID); Appendix B "OST
   Restorations" pp.68–77 (no EIN); **Aging pp.78–112, unruled**; Local pp.113–387 (11-col
   Source table, header on all 275 pages, Source `Local` and `Boro`); pivot p.388; Youth
   pp.389–439 (8 cols, `Council Member │ Organization │ EIN │ * │ Amount │ Purpose │ Fiscal
   Conduit │ Fiscal EIN`).
3. **Ruling.** Local and Youth fully ruled (p.200 viewed). **Aging has no rules at all** (p.80
   viewed: 0 rects, 0 lines; columns aligned by position; amounts sit at the row's baseline while
   purpose text runs above it). The header is a 0.75-gray fill with no stroke.
4. **Prototype (pp.26, 80, 200, 420).** pp.200, 420: all data rows and columns agree. The one
   vector-only separator is the top of the gray header fill, which the image threshold does not
   see. p.26: rows agree, 6 phantom columns. p.80: no lattice either way. Text needs tolerance 1.0.
5. **Totals and anchors.** Award EINs 4,726 (Local and Youth rows with EIN 4,193, plus 533 on
   unruled Aging pages); conduit 29. Local 3,198 rows $36,424,247 against the **pivot Grand
   Total $36,424,244.5 (difference $2.50)**. The pivot has half-dollar subtotals (Boro
   987,674.5), so the printed whole-dollar amounts are probably rounded from fractional values.
   That reading is unverified; DATA-ANOMALIES §22 records 30 fractional-cent FY2014 amounts in
   the disclosure. Youth 1,003 rows $7,722,414.
6. **Disclosure.** Loaded. Sample: 48 of 52.
7. **Old parse.** Initiatives only (123 rows, 17/17).
8. **QA path.** Tier A for Local and Youth. **Tier B for Aging**: columns from header-word x
   positions (the header prints in text on p.78), rows from the EIN/amount baseline, and H9 ink
   coverage as the backstop. The pivot gives a per-member and per-Source check on Local. Scope
   calls on child care and OST. **3–4 days.**

### FY2015 — `source/FY15/fy2015-FY15-Schedule-C-Template-Final.pdf`

1. **File.** 292 pp; Acrobat Pro 11.0.0; 204 landscape. Era D (first year).
2. **Sections.** Intro, "Units of Appropriation and Terms and Conditions" p.6; Anti-Gun Violence
   p.9; Anti-Poverty p.12 (table p.13 `Council Member │ Legal Name │ EIN │ Amount`);
   Boroughwide Needs p.20 (table p.21 `Borough │ …`); initiatives to p.82 (19 summary tables,
   28 `TOTAL` lines); App. A "List of Baselined Initiatives" p.87; App. B Aging pp.89–111; App. C
   Youth pp.112–144; App. D Local pp.145–292 (`Sponsor │ Council Member │ Legal Name │ EIN │ * │
   Amount ($) │ Purpose │ FC Name │ FC EIN`, no Agency column).
3. **Ruling.** Appendices fully ruled. Initiative org tables are **h-rule-only** with 0.5 pt
   rules (p.28 viewed: 52 white fill boxes, no verticals).
4. **Prototype (pp.28, 100, 150, 250).** Appendix pages exact. p.28: the vector "table" is
   built from white fills and the image finds no region, so neither reads columns.
5. **Totals and anchors.** App. B 552 rows **$5,610,000**, C 939 **$7,650,000**, D 3,107
   **$36,539,000**: the fixed pots. Initiative-page EIN tokens 657.
6. **Disclosure.** Loaded. Sample: 65 of 75 (misses: p.250 4, p.28 3, p.150 3). The 3 on
   p.28 are the prototype's own blank-EIN misreads of the h-only table.
7. **Old parse.** Dedicated parser: 652 body rows, appendices **empty** (0 of 4,598 printed
   rows). Category reconciliation 24/24.
8. **QA path.** Tier A appendices unchanged. The h-only initiative tables need the
   h-rule + header-word column path (1 page fully, 2 partly). **2–3 days.**

### FY2016 — `source/FY16/fy2016-skedcf.pdf`

1. **File.** 352 pp; Acrobat Pro 11.0.0; p.4 blank. Era D.
2. **Sections.** p.11 states what the `*` means. Anti-Poverty pp.12–25 (`Council Member │ … │
   Fiscal Conduit │ FC EIN`); Boroughwide pp.26–33 (`Borough │ …`); initiatives to p.140 (24
   summary tables); a 6-col table pp.127–130; App. A Aging pp.141–165; App. B Local pp.166–302
   (10 cols with Sponsor and Agency); App. C Youth pp.303–352 (8 cols).
3. **Ruling.** Appendices fully ruled. 9 h-only initiative pages (pp.41–49, 254 EIN words).
4. **Prototype (pp.15, 44, 150, 200, 320).** Four exact; p.44 has no table in either lattice.
5. **Totals and anchors.** A 526 rows $5,610,000; B 2,955 rows **$36,538,000** (2 rows with
   8-digit EINs); C 910 rows $7,650,000. Initiative tokens 1,130.
6. **Disclosure.** Loaded. Sample: 75 of 77.
7. **Old parse.** 335 body rows; appendices **empty** (bare amounts, #59); §20 `org_merged` 21.
   The PDF prints 4,391 appendix rows.
8. **QA path.** Tier A; h-only path for 9 pages. **2.5–3 days.**

### FY2017 — `source/FY17/FY17-Schedule-C.pdf`

1. **File.** 355 pp; Acrobat Pro 11.0.7. Era D.
2. **Sections.** Anti-Poverty pp.13–26; Boroughwide pp.27–35; initiatives (school-site tables
   with a `Program` column, e.g. p.50); Speaker's Initiative p.115 with `Sponsor` table
   pp.116–120; App. A Aging pp.133–165; App. B Local pp.166–303; App. C Youth pp.304–355
   (header typo "Youth Dicretionary").
3. **Ruling.** Appendices fully ruled. 18 h-only initiative pages (from p.39, 493 EIN words;
   p.50 viewed: horizontal rules between rows, no verticals).
4. **Prototype (pp.15, 50, 140, 200, 320).** Four exact, p.50 no lattice either way.
5. **Totals and anchors.** A 549 rows $5,610,000; B 3,043 rows **$36,538,500**; C 922 rows
   $7,650,000. **App. C prints 897 of its 922 EINs in scientific notation** (`8.61E+08`,
   `5.1E+08`, p.320). The 9-digit value cannot be recovered from the PDF. Only 25 Youth EINs and
   6 FC EINs are intact.
6. **Disclosure.** Loaded. Sample (five pages; p.50 has no vector table, p.320's EINs are not
   EIN-shaped): 50 of 51. The Youth appendix cannot be
   matched on (EIN, amount) at all.
7. **Old parse.** 364 body rows (§20: 118 `org_merged`, the worst year); appendices **empty**.
8. **QA path.** Tier A, with a printed-data defect. Keep `ein_printed` = `8.61E+08`, `ein`
   empty, flag `ein_scientific_notation` (897 named exceptions or one range exception). Any
   later recovery from the disclosure is a derived column with its source stated, never a PDF
   value. **3–4 days.**

### FY2018 — `source/FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf`

1. **File.** 357 pp; Word 2016; pp.115–119 blank. Era D.
2. **Sections.** Anti-Poverty pp.12–25 (`Legal Name of Organization - Program Name`, `CM Purpose
   of Funds`); Boroughwide pp.27–35; cultural school tables pp.46–50 (`Cultural Organization -
   School`); Speaker's `Sponsor` table pp.110–114; App. A Aging pp.130–162 (FC cols); App. B
   Local pp.163–307; App. C Youth pp.308–357.
3. **Ruling.** Fully ruled except 5 h-only pages (72 EIN words) and 3 partly ruled pages.
4. **Prototype (pp.15, 47, 140, 200, 330).** All five exact.
5. **Totals and anchors.** A 537 rows $5,610,000 (amounts printed with cents, 537 cells); B 3,054
   $36,539,000; C 895 $7,650,000. Initiative tokens 1,449.
6. **Disclosure.** Loaded. Sample: 114 of 116.
7. **Old parse.** 480 body rows (§20: 94 `org_merged`); App. A 422 rows (the PDF prints 537) with
   the `fy18_aging_shift` defect (§21, 422 cells); Local and Youth **empty**.
8. **QA path.** Tier A. **2.5–3 days.**

### FY2019 — `source/FY19/Fiscal-2019-Schedule-C-Final-Report.pdf`

1. **File.** 357 pp; Word 2016. Era D (last).
2. **Sections.** Anti-Poverty pp.13–26; Boroughwide pp.27–34; initiatives (cultural tables
   pp.45–84); Speaker's `Sponsor` table pp.110–120; App. A pp.132–162 and App. C pp.308–357 (6
   cols, no FC); App. B pp.163–307 (8 cols, no FC).
3. **Ruling.** 15 h-only pages (250 EIN words), 2 partly ruled.
4. **Prototype (pp.15, 38, 140, 200, 330).** Four exact; p.38 h-only.
5. **Totals.** A 523 $5,610,000; B 3,016 $36,539,000; C 905 $7,650,000. Rows equal EIN words in
   every appendix.
6. **Disclosure.** Loaded. Sample: 81 of 82.
7. **Old parse.** 846 body rows (§20: 39); appendices **empty**.
8. **QA path.** Tier A + h-only path. **2.5–3 days.**

### FY2020 — `source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf`

1. **File.** 405 pp; Word 2016; **12 pages with MediaBox origin (−18, 18)** in PDF space
   (pdfplumber: −18, −18). Era E.
2. **Sections.** Anti-Poverty pp.13–25; Boroughwide pp.26–32; initiatives to p.185 (school,
   program and member tables, many header variants pp.51–164); Speaker's p.165, `Sponsor` table
   pp.166–177; App. A pp.189–217; App. B pp.218–358; App. C pp.359–405. No `*` column.
3. **Ruling.** 24 h-only pages (456 EIN words) and 10 partly ruled (218): the most of any year
   before FY2024. p.38 viewed (Digital Inclusion: thin horizontal rules only).
4. **Prototype (pp.15, 38, 58, 200, 250, 380).** Five exact; p.38 h-only.
5. **Totals.** A 510 $5,610,000; B 2,986 $36,539,000; C 897 $7,650,000. Appendix amounts bare.
   Initiative tokens 3,525.
6. **Disclosure.** Loaded. Sample: 106 of 109.
7. **Old parse.** 2,841 body rows (§20: 1); appendices **empty**.
8. **QA path.** Tier A + h-only path + origin normalization. **2.5–3 days.**

### FY2021 — `source/FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf`

1. **File.** 343 pp; Adobe PDF Library 20.9.95 / PDFMaker 20. Era E.
2. **Sections.** Anti-Poverty pp.12–25; Boroughwide pp.26–32; initiatives to p.126; Speaker's
   `Sponsor` pp.111–118; App. A pp.129–157; App. B pp.158–295; App. C pp.296–343. Headers say
   `Tax ID`.
3. **Ruling.** **No page has EINs outside a vector table**, the only year so.
4. **Prototype (pp.15, 42, 140, 200, 320).** All award tables exact; p.42 has two small tables
   with no image region.
5. **Totals.** A 514, B 2,902, C 894 rows, the pots exact; rows equal EIN words.
6. **Disclosure.** Loaded. Sample: 88 of 90.
7. **Old parse.** Appendices match the PDF's row counts exactly (514/2,902/894). Body 1,810 rows,
   after §13 recovered 10 dropped header-adjacent rows.
8. **QA path.** Tier A, stages unchanged. **2 days. The best first year after FY2024.**

### FY2022 — `source/FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf`

1. **File.** 326 pp; Word 2016. Era E.
2. **Sections.** Anti-Poverty pp.10–23; Boroughwide pp.24–31; initiatives to p.121; Speaker's
   `Sponsor` pp.98–111; App. A pp.122–150; App. B pp.151–280; App. C pp.281–326.
3. **Ruling.** 1 h-only page (p.85, 26 words), 2 partly ruled.
4. **Prototype (pp.15, 53, 130, 200, 300).** Exact except p.53 (two one-row tables with no image
   lattice, one table with 5 phantom columns).
5. **Totals.** A 510, B 2,790, C 882 rows, the pots exact.
6. **Disclosure.** Loaded. Sample: 96 of 108; 11 of the 12 misses are p.53 initiative rows.
7. **Old parse.** Appendices equal; body 1,492 (§13 +13).
8. **QA path.** Tier A. **2 days.**

### FY2023 — `source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf`

1. **File.** 334 pp; Adobe PDF Library 22.1.149. Era E.
2. **Sections.** Anti-Poverty pp.13–26; Boroughwide pp.27–33; Speaker's `Sponsor` pp.109–130;
   App. A pp.141–167; App. B pp.168–293; App. C pp.294–334.
3. **Ruling.** 14 h-only pages (190 words), 13 partly ruled (222).
4. **Prototype (pp.15, 62, 120, 200, 300).** Exact except p.62 (h-only, region without lattice).
5. **Totals.** A 489 $5,610,000; **B 2,728 rows $36,539,000**; C 841 $7,650,000.
6. **Disclosure.** Loaded. Sample: 82 of 83.
7. **Old parse.** B has 2,726 rows totaling $36,529,000. It lost **Elite Community Foundation,
   Inc. $5,000 (p.213, EIN printed `84 -2079676`) and Laundromat Project, Inc., The $5,000
   (p.235, printed `87-0753479`, text layer `87`U+00AD`0753479`)**. Both were absorbed into
   neighbors' `program`/`purpose` text. DATA-ANOMALIES §19 explains the $10,000 as a seat
   vacancy or rounding.
8. **QA path.** Tier A + h-only path; the space and the soft hyphen are named exceptions: a
   printed oddity and a text-layer character. **2–2.5 days.**

### FY2024 — `source/FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf`

1. **File.** 453 pp; Adobe PDF Library 23.3.45; 192 portrait, 253 landscape, 8 at 1148×887;
   **216 pages with MediaBox origin (−18, 18)** in PDF space (pdfplumber: −18, −18). Era F.
2. **Sections.** Anti-Poverty landscape inserts pp.10–25; Boroughwide p.26; initiatives
   pp.27–225 with per-member tables (`Council │ Legal Name – Program Name │ Tax ID │ Amount │
   Agency`, 78 pages; a 15-column variant pp.201–208); Speaker's pp.226–~254 (`Sponsor` table,
   28 pages); Youth Services pp.262–265; App. A pp.266–291; App. B pp.292–411; App. C
   pp.412–453.
3. **Ruling.** 27 h-only pages (558 words), 17 partly ruled (224). On pp.41–45 the first row has
   no top rule (p.41 viewed) and the column header prints at the **bottom** of the table.
4. **Prototype (pp.20, 41, 100, 203, 240, 300, 420).** After origin normalization: four exact.
   pp.41 and 100 differ by the header bar and 2 phantom columns; p.203 by 10 phantom columns.
   The first row on pp.41–45 is missed by **both** lattices (1 EIN per page outside the table).
5. **Totals.** A 477, B 2,616, C 818 rows, the pots exact. Initiative tokens 5,378.
6. **Disclosure.** Loaded. Sample: 172 of 175.
7. **Old parse.** Appendices equal (477/2,616/818); body 5,368 (§13 +69; §20: 1).
8. **QA path.** Tier A; reuse the FY2025–FY2027 config shape directly. Add origin normalization
   (shared), the first-row-above-rule check (H5), and the h-only path. **2.5–3 days.**

---

## Recommended build order

| # | Year | Why here |
|---|---|---|
| 1 | FY2024 | Same layout as FY2025–FY2027; reuses their config. Forces the shared origin fix. |
| 2 | FY2021 | Cleanest year: every EIN sits in a vector table; appendices already match the old parse, so the diff isolates body-stream differences. |
| 3 | FY2022, FY2023 | Era E with few h-only pages; FY2023 brings the two named EIN exceptions (a printed space, a soft hyphen) and the §19 correction. |
| 4 | FY2020 | Era E, but builds the h-only path (24 + 10 pages) that eras D–F all need. |
| 5 | FY2019, FY2018, FY2016, FY2015 | Era D on the h-only path; bare amounts; recovers 4,400–4,600 appendix rows a year that were never published. |
| 6 | FY2017 | Era D plus the scientific-notation Youth appendix, which needs a schema decision first. |
| 7 | FY2011 | Pilot for eras B and C: glued text fixed by tolerance, fully ruled, and App. 1 prints Aging and Youth totals that reconcile to the dollar. |
| 8 | FY2009, FY2012, FY2013 | Same machinery as FY2011 (rotation for FY09, Source column for FY12–FY13). |
| 9 | FY2014 | Adds the unruled Aging path and the pivot check. |
| 10 | FY2010 | Banded rows need new row code; no App. 1 and no disclosure to lean on. |
| 11 | FY2008 | Different schema (no EIN); no independent source. |

This differs from PLAN §7 in one way: FY2009–FY2014 do not need a separate scoping PR before
work starts. Five of the six are as clean as FY2021, and two of them have better printed checks
than any later year. FY2011 can start as soon as the h-only path is not on its critical path,
because era B has no h-only tables.

**Effort, all 17 years (estimate):** about 40–53 year-specific days on top of PLAN's shared
work, plus three new shared pieces this survey found: MediaBox origin normalization (<0.5 day),
the h-rule + header-word column path (2–3 days), and banded-row detection (in FY2010's estimate).
Human review of critical rows: 1–2 hours a year, more in FY2017 (897 EIN rows) and FY2010.

---

## Corrections the published record needs

1. **DATA-ANOMALIES §2** and **`code/PARSING.md`** ("Schedule C — early era", the full status
   table): FY2009–FY2014 Schedule C prints organization award rows with EINs. Award-column
   EINs: 3,859 / 3,994 / 4,139 / 4,331 / 4,553 / 4,726. The stated reason, "designations were
   largely made after adoption", does not hold for these PDFs, and "FY2016 is the first year
   the adopted Schedule C carries award/EIN tables" is wrong. **`DATA-DICTIONARY.md`** states
   the same claim ("FY2009–FY2014 are initiatives-only (no EIN)"; "EIN-keyed analysis … is
   valid FY2015–FY2027") and needs the same correction.
2. **DATA-ANOMALIES §5 FY2008 row ("Untouched … Earliest-era format") and `code/PARSING.md`
   ("Distinct pre-FY09 format; deferred"):** FY2008 prints 1,674 member-item award rows
   ($36,399,802) in Appendix E, without EINs.
3. **DATA-ANOMALIES §19:** the FY2023 Local figure of $36,529,000 comes from the old parse. The
   PDF's 2,728 Local rows sum to $36,539,000 (the same pot as every other year; no printed Local
   total was found in its text); the parse dropped two $5,000 rows whose EIN text does not match
   `NN-NNNNNNN` (a printed space, and a soft hyphen in the text layer). The "seat vacancy /
   rounding" explanation is wrong for FY2023. (FY2026's $36,534,000 was not checked here.) The same
   fixed pots appear in FY2015–FY2020, which §19's table omits, and in FY2009–FY2013 Aging/Youth at
   $5,546,250 / $7,737,414 (FY2009 Youth $7,723,700).
4. **DATA-ANOMALIES §23 table:** "FY2013 / FY2014: no Schedule C award files" describes the
   repo's files, not the PDFs. Both PDFs print award tables (and FY2015–FY2017, FY2019–FY2020
   "appendix CSVs empty" hides 4,391–4,598 printed appendix rows a year). The coverage table
   should say so, so the 0% rows are not read as a property of the source.
5. **New entry (proposed):** FY2017 Appendix C prints 897 EINs in Excel scientific notation.
   It is a source defect, flagged and never repaired from another source in place.
6. **New entry (proposed):** award rows without an EIN-shaped value (blank, `EX…`, `NA`, `Pending`,
   8-digit, spaced or soft-hyphen), counted per year above. An EIN-keyed completeness measure
   undercounts by exactly these rows.
7. **DATA-ANOMALIES §3** (glued text, transparency resolutions) could note that, for Schedule C,
   the spaces are recoverable from geometry: `x_tolerance` 1.5 (FY2010–FY2011) and 1.0
   (FY2012–FY2014) bring glued words to 0.0–0.4% on sample pages. Whether the same holds for
   the transparency PDFs was not tested.

---

## Open questions

1. **FY2009/FY2011 Local vs Appendix 1:** the Council sections exceed the summed "Local
   Initiatives" lines by $6,500 and $5,500. Is there an App. 1 line the regex missed (wrapped
   or glued), or is this a self-difference to name? Needs a line-by-line agency join.
2. **FY2014 pivot vs printed amounts ($2.50):** are the printed whole-dollar amounts rounded
   from fractional values? If so, which value is the record: the printed cell (PLAN's rule) or
   the pivot's? Recommendation: the printed cell, with the pivot difference named.
3. **FY2017 Youth EINs:** leave `ein` empty and key those rows on (name, amount, member) for
   report-only matching? Recommendation: yes, and say so in the year's README.
4. **Scope of site-level tables:** FY2013 OST chart (pp.64–69, 238 EINs), FY2014 child-care
   App. A (69 EINs) and OST App. B (no EIN). Are they award rows for this dataset, or a
   separate table type?
5. **Prose designations** ("Designation Method: … has designated X … Tax ID#: …") in
   FY2009–FY2014: emit as award rows tied to the initiative (needed for H12), or keep them as
   initiative attributes?
6. **FY2008 schema:** a no-EIN award table in the same output family, or a separate
   `fy08_sc_member_items` table?
7. **FY2010:** is the incomplete archived workbook (2,592 rows) worth loading as a report-only
   partial check, given that `data/disclosure_years.csv` deliberately leaves it out (#89 A3)?
8. **Wrapped conduit EINs (FY2010, 229):** confirm that a digits-only join across line breaks
   inside one cell is an allowed clean rule (it changes no digit), recorded in
   `clean_rules_applied`.
9. **Section page ranges** for FY2015–FY2024 initiative bodies were taken from header and divider
   text in this survey, not by reading every page. Each year's onboarding confirms them (PLAN §7
   step 1).
