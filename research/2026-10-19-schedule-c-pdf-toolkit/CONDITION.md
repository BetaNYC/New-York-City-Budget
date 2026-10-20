# PDF condition survey: every PDF in `source/`

**Report generated:** 2026-10-19. Prepared by BetaNYC with AI assistance.
**Last revised:** 2026-10-20 00:52 EDT — factual QA pass (5 fixes)
**Data current as of:** 2026-10-19 (the 243 PDFs in `source/` at `origin/main` f5740c3)
**Status:** draft. Stage 0 (triage) of the PDF-to-structured-data plan.

Survey data: `data/pdf_condition.csv` (one row per PDF) and `data/pdf_condition_pages.csv`
(one row per page). Code: `code/pdf_condition.py`, tests `code/test_pdf_condition.py`.
Reproduce: `python code/pdf_condition.py` (from the repo root, deps in `code/requirements.txt`).
It reads 243 PDFs / 17,852 pages in 11.4 s wall time on 10 cores (88 s CPU). Two runs give
byte-identical CSVs.

## Bottom line

- **Every PDF opened. None is a git-LFS pointer, none failed to parse, and none has an OCR
  text layer.** That means there is no tier C anywhere in the corpus: the invisible-glyph share
  is 0.0 for all 243 files.
- **19 PDFs (1,189 pages) are image-only scans (tier D)**, all from FY2009 to FY2012: four
  capital "changes" books and fifteen transparency resolutions.
- **Schedule C is tier A in every year, FY2008 to FY2027.** It is born-digital with vector
  ruled tables on 75% to 99% of its pages.
- **The capital books are the hard born-digital case (tier B).** The §254 changes and
  supporting-detail listings are column-aligned text with no cell rules, so their columns
  have to be inferred.

## Method

1. **Text-layer gate: a port of Christian Moscardi's probe.** His `textlayer.py` lives in
   `BetaNYC/nyc-executive-orders` (MIT). It uses two probes. The first is mean extracted
   characters per page: at or below 100 there is no text layer, and the document is `scanned`.
   The second is the share of glyphs drawn in PDF render mode 3 (invisible): above 0.5 the text
   is an OCR overlay on a scan (`scanned-ocr-layer`), otherwise it is born-digital (`text`). It
   keeps per-page counts so that one image-only page inside a good document still shows up. His
   code runs on PyMuPDF (AGPL), so the shipped port runs on pypdfium2 (Apache-2.0/BSD-3)
   instead.
2. **Validation of the port.** We ran his original module unmodified, through
   `uv run --with 'pymupdf>=1.24,<2'` (PyMuPDF 1.28.2), on all 243 PDFs and compared the
   results with `research/2026-10-19-schedule-c-pdf-toolkit/validate_textlayer_port.py`.
   - **Classifications match on 243 of 243** (224 `text`, 19 `scanned`), and the
     invisible-share values are identical (largest gap 0.0000).
   - **Low-text page lists differ in 8 PDFs** (`compared=243 ... differences=8`). In every
     case the port flags one extra page that the original does not: FY2011 Transparency Reso 07
     p.13, FY2018 Terms & Conditions p.1, and p.3 of the FY2018 ResoA book and of the FY2022,
     FY2023, FY2024, FY2026 and FY2027 supporting-detail books. Each of those pages is a short divider or cover
     with real text (34 to 99 characters).
   - **The cause is whitespace counting.** PyMuPDF counts the empty lines Word emits (" \n" ×
     N) and pdfium does not. For example, FY2022 supporting detail p.3 is 155 characters in
     PyMuPDF and 99 in pdfium. None of these pages is a scan.
   - **What the survey does about it.** It splits low-text pages by measured ink, so all eight
     land in `short_text_pages`, not `image_only_pages`.
3. **Ink check (new here).** Every low-text page (100 characters or fewer) is rendered at
   36 dpi, and a page counts as inked when at least 0.2% of its pixels are darker than 200/255.
   - **`image_only_pages`** are inked pages whose ink is not explained by their own text: an
     image covers at least 30% of the page, or there is ink and no text at all.
   - **`short_text_pages`** are inked pages that do have a short text layer (covers and
     dividers).
   - **`blank_pages`** are pages with no ink.
4. **Vector rules (new here).** Each visible path is walked segment by segment in page
   coordinates.
   - **Rules and rects.** An axis-aligned segment at least 4 pt long and at most 2.5 pt thick
     is a horizontal or vertical rule, and so is a thin closed four-point box. A non-thin box is
     a rect.
   - **Ruled pages.** A page counts as ruled with at least 2 horizontal and 3 vertical rules,
     or at least 15 rects.
   - **Document tier.** A document is A if at least 50% of its pages are ruled, B if under 10%
     are, and "A+B" (composite) in between. The per-page tier in the pages CSV is the finer view.
5. **Garbled-text signal.** The share of non-whitespace characters that are U+FFFD, C0
   controls, or private-use code points. A pypdf census also counts fonts without a
   `/ToUnicode` map, Type0 fonts without one, and Type3 fonts.
6. **Family.** Two independent rule sets, one on the filename and one on the first page's
   text. Agreement, or a single signal, decides the family. A conflict or no signal at all gives
   `unknown`. Every row records `family_by_filename`, `family_by_title` and `family_basis`.
7. **Spot checks.** We rendered 24 pages with pypdfium2 (not committed) and looked at every
   one; see "Spot checks" below.

Where the heuristics are unsure is stated in "Where the heuristic is unsure" at the end.

## Tier counts

Document tier is the `qa_tier` column. Page tier is the `page_tier` column in the pages CSV:
D for image-only pages in any document, C for OCR-layer pages, and A/B for text pages by
whether that page is ruled.

| Tier | Meaning | PDFs | Pages (in those PDFs) | Pages by page tier |
|---|---|---:|---:|---:|
| A | born-digital, ruled tables | 189 | 14,670 | 12,962 |
| A+B | born-digital, composite (10–50% of pages ruled) | 11 | 611 | — |
| B | born-digital, unruled | 24 | 1,382 | 3,532 |
| C | scan with OCR text layer | 0 | 0 | 0 |
| D | image-only scan | 19 | 1,189 | 1,289 |
| — | blank (no ink) | — | — | 51 |
| — | short text (cover/divider with real text) | — | — | 18 |
| **Total** | | **243** | **17,852** | **17,852** |

Page tier D (1,289) is larger than the D-document page count because the 13 "mixed" documents
add 150 image-only pages inside tier A documents (FY2010 and FY2011 transparency resolutions).
Page tier D is also smaller than all pages of D documents, because 50 pages in those documents
are not image-only: 34 are blank and 16 carry real text (the born-digital ends of the FY2009
capital book).

**Special cases** (`special_flags`):

- **Encrypted: 11.** All are capital books (FY2009 to FY2025). All open with an empty user
  password, so this is an owner-permissions flag and blocks nothing here. A pipeline must still
  open them with a library that honors an empty password.
- **Mixed: 13.**
  - **FY2009 capital changes** (`fy09-adopt08_capreso.pdf`): pages 3–279 are full-page images
    and pages 1–2 and 280–293 are text.
  - **FY2010 and FY2011 transparency resolutions (12 files,** ScanSoft PDF Create! 5): 150
    pages with no text and no image. These are vector-drawn "EXHIBIT X" divider pages.
- **Rotated pages: 26 documents.** See "Surprises", item 3.
- **Garbled text: none above 1%.** The largest is 0.55% (FY2017 DOHMH oral-health insert): the
  private-use bullet glyphs Word emits from the Symbol font. The others are FY2012 Schedule C
  (0.02%) and FY2013 Transparency Reso 09 (0.07%).
- **Fonts.** One Type0 font has no ToUnicode map (FY2009 Schedule C); its garbled share is 0.0
  anyway. There are no Type3 fonts.
- **Unknown family: 1.** `FY18/FY18-Sec254-Capital-ResoA-M499-Res1534-Res1535.pdf` is named as
  the ResoA book, but its title page says "Supporting Detail For Fiscal Year 2018", and its
  pages are supporting-detail listings (sponsor column). Left as `unknown` on purpose.
- **Parse errors: 0. LFS pointers: 0.** All 243 files start with `%PDF-`.

## Condition by family × fiscal year

Each cell is tier (text class, pages). `*` = mixed (holds image-only pages). Transparency
resolutions are summarized per year as tier × count.

| FY | schedule_c | transparency_resolution | capital_changes | capital_supporting_detail | terms_conditions | unknown |
|---|---|---|---|---|---|---|
| 2008 | A (txt, 123 pp) | — | — | — | — | — |
| 2009 | A (txt, 246 pp) | 8 PDFs / 332 pp: D×8 | D* (mixed, 293 pp) | — | — | — |
| 2010 | A (txt, 408 pp) | 12 PDFs / 430 pp: A*×8, B×1, D×3 | D (scan, 98 pp) | — | — | — |
| 2011 | A (txt, 291 pp) | 10 PDFs / 307 pp: A×1, A*×4, A+B×2, D×3 | B (txt, 74 pp); D (scan, 108 pp) | — | — | — |
| 2012 | A (txt, 393 pp) | 8 PDFs / 226 pp: A×6, A+B×1, D×1 | D (scan, 124 pp) | — | — | — |
| 2013 | A (txt, 258 pp) | 9 PDFs / 238 pp: A×8, A+B×1 | — | A+B (txt, 88 pp) | — | — |
| 2014 | A (txt, 439 pp) | 3 PDFs / 48 pp: A×3 | — | — | — | — |
| 2015 | A (txt, 292 pp) | 12 PDFs / 378 pp: A×12 | — | A+B (txt, 84 pp) | B (txt, 17 pp) | — |
| 2016 | A (txt, 352 pp) | 13 PDFs / 557 pp: A×13 | B (txt, 83 pp) | A+B (txt, 86 pp) | B (txt, 30 pp) | — |
| 2017 | A (txt, 355 pp) | 13 PDFs / 630 pp: A×13 | B (txt, 94 pp) | — | A (txt, 1 pp); B (txt, 30 pp) | — |
| 2018 | A (txt, 357 pp) | 12 PDFs / 598 pp: A×12 | — | — | B (txt, 34 pp) | B (txt, 96 pp) |
| 2019 | A (txt, 357 pp) | 11 PDFs / 733 pp: A×11 | — | A (txt, 55 pp) | — | — |
| 2020 | A (txt, 405 pp) | 8 PDFs / 508 pp: A×8 | — | A+B (txt, 80 pp) | — | — |
| 2021 | A (txt, 343 pp) | 8 PDFs / 404 pp: A×8 | B (txt, 73 pp) | — | B (txt, 16 pp) | — |
| 2022 | A (txt, 326 pp) | 14 PDFs / 709 pp: A×14 | B (txt, 78 pp) | B (txt, 92 pp) | A+B (txt, 18 pp) | — |
| 2023 | A (txt, 334 pp) | 14 PDFs / 697 pp: A×14 | B (txt, 101 pp) | B (txt, 89 pp) | B (txt, 19 pp) | — |
| 2024 | A (txt, 453 pp) | 9 PDFs / 388 pp: A×9 | B (txt, 86 pp) | A+B (txt, 78 pp) | B (txt, 24 pp) | — |
| 2025 | A (txt, 455 pp) | 13 PDFs / 395 pp: A×13 | B (txt, 88 pp) | A+B (txt, 87 pp) | B (txt, 25 pp) | — |
| 2026 | A (txt, 469 pp) | 10 PDFs / 544 pp: A×10 | — | B (txt, 86 pp) | B (txt, 29 pp) | — |
| 2027 | A (txt, 498 pp) | — | — | B (txt, 80 pp) | B (txt, 32 pp) | — |

Totals by family: schedule_c 20 PDFs / 7,154 pp; transparency_resolution 187 / 8,122;
capital_changes 12 / 1,300; capital_supporting_detail 11 / 905; terms_conditions 12 / 275;
unknown 1 / 96. Families are absent in some years (no capital_changes for FY2013–FY2015 or
FY2018–FY2020, no transparency resolutions for FY2008 or FY2027). This survey only records
what is in `source/`; it does not say whether those documents exist.

## QA path to structured data, per family

The tiers, as defined for this plan:

- **A (born-digital, ruled):** a vector cell-grid parse, cross-checked against the image grid
  (Christian's PR #43 `grid.py`, with the absolute-kernel patch).
- **B (born-digital, unruled):** layout and column inference from character x-positions, with
  heavier review.
- **C (scan with an OCR layer):** treat the text layer as untrusted and re-OCR it (Christian's
  PR #43 OCR path).
- **D (image-only):** the full OCR pipeline plus a human QA sample.

### schedule_c: tier A, FY2008–FY2027 (20 PDFs, 7,154 pages)

- **Condition.** Every year is born-digital. Pages by page tier are A 6,771 and B 376 (unruled
  pages, such as the narrative FY2008 p.30 below); 6 are blank and 1 is short text. Looking at the
  pages agrees: FY2027 p.100 is a fully ruled grid (Council Member / Organization / EIN /
  Amount / Agency), FY2009 p.60 is a fully ruled grid, and FY2008 p.30 is narrative ("PS
  Enhancement $53,160"), correctly B.
- **Path.** Vector cell grid as the primary read, with the image grid as a hard check. This is
  the approach the FY2025–FY2027 prototypes already validated (99.7% row agreement on FY2027,
  per the image-grid check summarized in `PLAN.md` §2.3). The
  unruled narrative pages, which hold initiative descriptions and amounts, need the tier B
  treatment.
- **Watch out.**
  - **FY2009** has 188 rotated pages (57–167, 169–193, 195–246). They render upright, but a
    grid reader must use the rotation-applied page.
  - **Page sizes vary within a year** (FY2027 has five: 612×792, 1056×816, 932×720,
    1003×775, 990×765), which marks inserted Excel pages. Any
    fixed-coordinate column scheme will break.

### transparency_resolution: mostly tier A (187 PDFs, 8,122 pages)

- **Condition.** Page tiers are A 6,004, B 1,389, D 694, blank 33 and short text 2.
  - **FY2013 onward** is uniformly born-digital, with ruled "CHART n" tables (Excel output
    with cell rules) after a few pages of resolution text.
  - **FY2009** is entirely image-only scans (8 files, PDFlib+PDI wrappers). FY2010 has 3 more
    scans, FY2011 has 3 (Xerox WorkCentre 5675) and FY2012 has 1.
  - **FY2010–FY2011 ScanSoft files (12 of them)** are "mixed", but their image-only pages are
    vector-drawn "EXHIBIT A…M" dividers. We looked at FY2010 Reso 05 p.10 and FY2011 Reso 03
    p.47. All 150 such pages have 0 characters and no image. They carry no data and can be
    skipped, but only after an OCR or human look confirms each is a divider.
- **Path.**
  - **Tier A files:** vector grid on the CHART pages. Many charts have row rules only at the
    header and the bottom (for example, FY2013 Reso 04 p.13 has 3 horizontal and 11 vertical
    rules), so columns come from the rules but rows come from text lines. Cross-check against
    the image grid.
  - **The 15 tier D files (566 pages; see errata 1):** full OCR, with a human QA sample per chart.
- **Watch out.**
  - **Near-duplicate.** `FY12/.../Transparency-Reso-07-2012-02-01-dup.pdf` is not
    byte-identical to `...-01.pdf`: 99,455 vs 99,456 bytes, differing from byte 48 on, with the
    same 29 pages and producer. Which copy is canonical is open.
  - **The FY2025–FY2026 layout changed.** The three sampled first pages open "Page 1 of 1 Preconsidered
    Res. No." rather than the Committee report header, though the files run 4 to 127 pages.
    The resolution page is numbered on its own, separately from the charts after it.

### capital_changes (§254 "Changes to the Executive Capital Budget", ResoA books): B or D

- **Condition.**
  - **FY2016, FY2017 and FY2021–FY2025 are born-digital tier B (7 books):** a mainframe-style
    report (Budget Line / Title / FY columns, "ELIMINATE/SUBSTITUTE" stacked values). 443 of
    the family's 687 tier B pages have no vertical rule; FY2016 and FY2021 are the exceptions,
    with column rules on most pages. FY2025 p.20 (labeled "PAGE: 17") is typical.
  - **FY2009–FY2012 are tier D scans:** FY2009 pages 3–279, FY2010 (98 pp), FY2011
    `fy11_changes_...` (108 pp) and FY2012 (124 pp).
  - **FY2011 `Section-254-Changes.pdf`** is a different, born-digital B listing ("AS400 ID /
    Budget Line / Boro / Project Title").
- **Path.**
  - **Tier B:** fixed-width column inference. The header row gives the column x-ranges, and
    the "(CN)" fund suffix and the ELIMINATE/SUBSTITUTE pairs need explicit rules. Reconcile to
    the totals printed in each agency section.
  - **Tier D:** OCR. The FY2009 images are crisp renders of a monospace mainframe report (p.100
    looked near-digital), which is the best case for OCR. FY2010–FY2012 are real Xerox scans.
- **Watch out.** FY2012 renders sideways even with the page rotation applied; see Surprises.

### capital_supporting_detail: B in practice (11 PDFs, 905 pages)

- **Condition.** The tool says A+B for 6 files (FY2013, 2015, 2016, 2020, 2024, 2025), B for
  4, and A for FY2019. Looking says B, except FY2019.
  - **The "ruled" pages are not cell grids.** In FY2020 the 16 ruled pages are where
    section-header boxes ("HOMELESS SERVICES", "HEALTH") and TOTALS rules happen to meet the
    rule thresholds (p.54 viewed). The project rows themselves are unruled (FY2027 p.20,
    labeled "Page 17 of 57").
  - **FY2019** (`Capital-Final-Upload.pdf`, Excel 2016) really is a fully ruled grid (p.10
    viewed). Its family came from the title alone, since the filename matches no rule.
- **Path.** Tier B column inference, with the header row (Project ID / Budget Line / Boro /
  Title / FY×4 / Sponsor) defining the columns. Reconcile to "TOTALS FOR …" lines. FY2019 is
  vector grid plus image check.
- **Watch out.** Most books have rotated page runs (for example FY2027 pp.4–60 and 63–71). They
  render upright.

### terms_conditions: tier B (12 PDFs, 275 pages)

- **Condition.** Word-produced prose: numbered agency / unit-of-appropriation sections with
  conditions (FY2027 p.5 viewed). Page tiers are B 252, A 15 and short text 8.
- **Path.** This is not tabular data. Section segmentation (agency code, U/A list, condition
  text) by heading pattern, then human review of the segment boundaries.
- **Watch out.**
  - **`FY17/2016-DOHMH-Terms-and-Conditions-Oral-Health.pdf`** (1 page) is not a T&C
    document. It is a DOHMH program update with a small table, filed under T&C (family from
    filename only).
  - **`FY15/fy2015-tc.pdf`** is the *capital* budget T&C, with no title match. Its family also
    comes from the filename only.

### unknown: 1 PDF

- **`FY18/FY18-Sec254-Capital-ResoA-M499-Res1534-Res1535.pdf`:** the filename says ResoA
  (capital_changes), but the title page (viewed) and the body (p.10 viewed: Project ID /
  Budget Line / … / Sponsor) say supporting detail. The content argues for supporting detail.
  Whether FY2018 is missing its ResoA book, or the file is misnamed upstream, is for a human to
  settle. Treat it as tier B either way.

## Worst offenders (most tier D pages)

| D pages | PDF | Note |
|---:|---|---|
| 277 | `FY09/fy09-adopt08_capreso.pdf` | pp.3–279 full-page images; 1–2 and 280–293 text |
| 121 | `FY12/fy2012-changestobudget.pdf` | pp.1–3, 5, 7–105, 107–124; renders sideways; blank 4, 6, 106 |
| 102 | `FY11/fy2011-fy11_changes_executive_capital_budget_adopted_by_nycc.pdf` | blank 2, 4, 6, 94, 96, 108 |
| 95 | `FY10/fy_2010_changes_exec_budget_top.pdf` | blank 4, 6, 92 |
| 71 | `FY10/transparency-resolutions/Transparency-Reso-04-2009-08-20.pdf` | pp.1–71 |
| 67 | `FY09/transparency-resolutions/Transparency-Reso-07-2009-04-22.pdf` | blank p.11 |
| 52 | `FY09/transparency-resolutions/Transparency-Reso-05-2009-02-11.pdf` | pp.1–52 |
| 46 | `FY09/transparency-resolutions/Transparency-Reso-03-2008-11-19.pdf` | pp.1–46 |
| 46 | `FY12/transparency-resolutions/Transparency-Reso-02-2011-10-05.pdf` | pp.1–46 |
| 45 | `FY09/transparency-resolutions/Transparency-Reso-06-2009-04-02.pdf` | pp.1–45 |

Exact page lists for every file are in the `image_only_pages` column.

## Spot checks (rendered with pypdfium2, viewed)

| Render (label) | Survey said | What we saw |
|---|---|---|
| `sc27_p100` FY2027 Schedule C p.100 | A | Fully ruled 5-column grid. Agrees. |
| `sc09_p60` FY2009 Schedule C p.60 (rotated page) | A | Upright, fully ruled 10-column grid with wrapped purpose text. Agrees. |
| `sc08_p30` FY2008 Schedule C p.30 | B | Narrative agency headings + amounts, no table. Agrees. |
| `tr13_04_p12`, `tr13_04_p13` FY2013 Reso 04 | A, A | Excel CHART tables with full grids (2-row chart on p.13). p.13 was B before the threshold was lowered from 5 to 2 horizontal rules; fixed. |
| `tr10_05_p11` FY2010 Reso 05 p.11 | A | Ruled CHART 1 table. Agrees. |
| `tr10_05_p10` FY2010 Reso 05 p.10 | D (image-only) | "EXHIBIT A" divider in outlined vector type. No data. |
| `tr11_03_p47` FY2011 Reso 03 p.47 | D (image-only) | "EXHIBIT M" divider. Same. |
| `tr09_01_p5` FY2009 Reso 01 p.5 | D | Photocopied resolution text with skew and speckle. Agrees. |
| `tr10_02_p2` FY2010 Reso 02 p.2 | blank | Blank back of a duplex scan (two specks). Agrees. |
| `capreso09_p100` FY2009 capital changes p.100 | D | Clean mainframe-report raster, no text layer. Agrees; easy OCR. |
| `capreso09_p285` same, p.285 | B | Born-digital "Rescindments" table with column rules only. Agrees. |
| `chg10_p10` FY2010 changes p.10 | D | Xerox scan, upright, readable. Agrees. |
| `chg10_p4` same, p.4 | blank | Blank. Agrees. |
| `chg12_p10` FY2012 changes p.10 | D | Xerox scan, **sideways after /Rotate is applied**. |
| `chg11_p5` FY2011 Section-254-Changes p.5 | B | Unruled column listing. Agrees. |
| `chg25_p20` FY2025 capital changes p.20 | B | Mainframe-style report, horizontal separators only. Agrees. |
| `sd27_p20` FY2027 supporting detail p.20 | B | Unruled listing. Agrees. |
| `sd20_p54` FY2020 supporting detail p.54 | A (ruled) | Section-header boxes + TOTALS rules; rows unruled. **Heuristic false positive.** |
| `sd19_p10` FY2019 supporting detail p.10 | A | Excel full grid. Agrees. |
| `tc27_p5` FY2027 T&C p.5 | B | Prose sections. Agrees. |
| `tc17_dohmh_p1` FY2017 DOHMH insert | A | Bulleted program update + one small ruled table. Not a T&C. |
| `fy18unk_p1`, `fy18unk_p10` FY2018 "ResoA" | unknown / B | Supporting-detail title page; unruled supporting-detail listing. |

## Surprises

1. **There is no OCR text layer anywhere.** In Christian's executive-orders corpus, 665 of the
   1,205 records with a text layer were OCR layers (his docstring). Here the invisible-glyph share is 0.0 in all 243 files, so tier C is empty, and the
   whole "untrusted second-hand OCR" problem does not arise.
2. **The FY2009 capital changes book is mostly raster.** It is a Distiller-made PDF whose
   pages 3–279 are full-page images of a mainframe report, with born-digital pages at both
   ends. Filename and title both say born-digital capital document; only page-level probing
   catches it.
3. **Rotation metadata cannot be trusted for the scans.** FY2012 `changestobudget.pdf` has
   /Rotate set on all 124 pages and still renders sideways. The FY2010 book, also rotated on
   every page, renders upright. An OCR step needs orientation detection per page, not
   /Rotate.
4. **Capital supporting detail is not ruled, even when the tool says it is.** Six books score
   as composite (A+B) only because section-header boxes and TOTALS rules cross the rule
   threshold. Looking at the pages, the project rows are unruled throughout (except FY2019,
   which is an Excel grid). In practice the most important capital data is tier B.
5. **The FY2018 "ResoA" file is the supporting detail.** Its title page and body are
   supporting detail, so FY2018's ResoA book may not be in `source/`. In the same vein,
   `FY17/2016-DOHMH-Terms-and-Conditions-Oral-Health.pdf` is a DOHMH program update, not
   terms and conditions.

Also notable: 150 "image-only" pages in the FY2010–FY2011 transparency resolutions are
vector-outlined "EXHIBIT" dividers, not scans. The `-dup` transparency file is not a byte
duplicate. 11 capital books carry owner-password encryption.

## Where the heuristic is unsure

- **Rule thresholds sit in no empty valley.** Unlike Christian's two gates, both of which are
  bimodal, the ruled-page share is spread out: transparency resolutions run from 0% to 99%.
  The thresholds (2 horizontal and 3 vertical rules, or 15 rects, per page; 10%/50% per
  document) are judgment calls. Section boxes trip them, which is the FY2020 supporting-detail
  false positive. A table ruled only by column lines with 0–1 horizontal rules is missed, as on
  FY2009 capital changes p.285. Use the page CSV's `h_rules`, `v_rules` and `rects`, not the
  boolean, when choosing a parser.
- **Outlined text inflates the rule counts.** Vector-outlined glyphs ("EXHIBIT A") produce
  straight segments that count as rules: FY2010 Reso 05 p.10 shows 29 horizontal and 22
  vertical rules with no table on the page.
- **Image-only vs short text.** The 30%-image-area / zero-text rule is new and was validated
  only by the pages viewed above. A scanned page carrying a digital stamp of more than 0
  characters, with an image under 30% of the page, would be filed as short text. There are 18
  short-text pages in total, few enough to review by hand.
- **Paths inside Form XObjects** are measured in the form's own coordinate space. pdfium does
  not compose the form matrix, so a rotated form could swap h and v. Total rule counts are
  unaffected.
- **Family rules are filename and title regexes.** Two files rest on a single signal that is
  plausibly wrong in meaning, though not in category: the DOHMH insert and FY2015 `tc`. One
  file is `unknown` by design.
- **Garbled share only sees what pdfium decodes.** A font that maps glyphs to the wrong but
  valid Unicode (a shifted encoding) would not register. The one Type0 font without ToUnicode
  (FY2009 Schedule C) decoded without U+FFFD, but its text has not been checked against the
  page image.

## Couldn't classify

- **Family:** 1 PDF (`FY18/FY18-Sec254-Capital-ResoA-M499-Res1534-Res1535.pdf`, a
  filename/title conflict). Every other PDF has a family, though 22 rest on the filename alone
  (15 of them scans whose first page has no text) and 1 on the title alone.
- **Text class:** none. Every PDF opened and got a class.

## Errata from the family assessments (added 2026-10-19)

The per-family assessments stacked on this survey read the documents themselves and correct
four things above. The survey's CSVs are unchanged; read them with these in mind.

1. **Transparency resolution scans are 566 pages, not 694.** The 694 is every page tiered D in
   the family: 544 image-only pages in the 15 scanned files, plus the 150 vector-drawn
   "EXHIBIT" divider pages in 12 born-digital FY2010–FY2011 files, which carry no text. The 15
   scanned files hold 566 pages (544 image-only, 22 blank): FY2009 332, FY2010 131, FY2011 57,
   FY2012 46.
2. **FY2015 Terms and Conditions is mixed expense and capital,** not capital-only.
3. **`FY18/FY18-Sec254-Capital-ResoA-M499-Res1534-Res1535.pdf` is the FY2018 capital
   supporting detail book** (title page: "Supporting Detail For Fiscal Year 2018"; p.70 "TOTALS
   FOR ALL (1485 PROJECTS) 575,000,000"). The survey's `unknown` family stands as a correct
   refusal to guess from a conflicting filename.
4. **`FY11/…Section-254-Changes.pdf` is project-level supporting detail,** not a changes book.
