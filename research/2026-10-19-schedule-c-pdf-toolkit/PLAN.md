# Schedule C from the PDFs: a build plan on Christian Moscardi's toolkit

**Report generated:** 2026-10-19 23:19 EDT (software-engineer agent; operator noel; machine office)
**Data current as of:** source PDFs at `main` @ `f5740c3`; disclosure workbooks retrieved
2026-10-12; Christian's code at PR #43 head `2191833` (his commits through `f8afb27`,
2026-07-28) and `BetaNYC/nyc-executive-orders` @ `84df8193`. PDF triage numbers in §2 were
measured tonight (scratch scripts in `/tmp/schedc-toolkit-plan/`, not committed).
**Status:** draft. Nothing here is built. Nothing in this repo was changed except this file.

Every number below either comes from the 2026-10-19 prototype notes (BetaNYC working notes, not in
this repo; their results are summarized in §2.3) or from
a command run for this plan (marked "measured tonight"). Where a number is an estimate or an
extrapolation, it says so.

---

## Built on

This plan reuses Christian Moscardi's work and says where, module by module.

- **PR #43, "OCR 2009 transparency resolutions"** (open; seven commits by Christian, 2026-07-23
  to 07-28): the staged OCR pipeline in `code/ocr/` (`render.py`, `orient.py`, `classify.py`,
  `grid.py`, `headers.py`, `recognize.py`, `assemble.py`, `report.py`), its driver
  `code/parse_transparency_reso_fy09.py`, its test file (35 test functions; 44 passed and 1
  skipped in the FY27 run), `code/ocr/install-and-run.md` and `code/requirements-ocr.txt`. The ruled-lattice detector `grid.py` is the most reused
  piece here.
- **`BetaNYC/nyc-executive-orders`:** Christian wrote `vlm_ocr.py` (dots.ocr runner, the
  `finish_reason`/logprob/`ink_coverage` QA signals), `vlm_pages.py` (page flags) and the
  `qa-ui/` review app. `textlayer.py` (born-digital vs scanned gate) was started by Noel
  (2026-07-13); Christian added the render-mode-3 split and per-page counts (2026-09-09,
  `b10b5a88`). `clean.py` (non-destructive raw vs clean) was started by Noel (2026-07-15) and
  refined by Christian (four commits, 2026-09-09).

His design rules carry over directly: geometry decides column identity, placement by
centroid, per-stage artifacts on disk, overlays as the iteration surface, no quiet repair,
disagreements go to review, and thresholds set in measured "empty valleys" with the
measurement written next to the constant.

---

## 1. Goal, scope, non-goals

**Goal.** Clean, parsable Schedule C data straight from the PDFs. Nothing guessed. Every value
traceable to a page, a table, a row and a box. Every disagreement between independent reads,
and every place the PDF disagrees with itself, lands in a review file. The old parse
(`code/parse_schedule_c*.py`, `data/fyXX/schedule_c/*.csv`) is evidence of failure modes, not
a starting point.

**In scope.**

1. The 20 adopted Schedule C PDFs, FY2008 to FY2027 (inventory in §2).
2. Every structure they print: category summaries and TOTALs, initiative descriptions and
   designation statements, award tables (body and appendices), page furniture classified so
   nothing is unaccounted.
3. Shared machinery only where another PDF family needs the same thing (the triage gate, the
   image lattice, the ink check, the review UI). Terms and Conditions, §254 capital and
   transparency resolutions are out of scope as deliverables.

**Non-goals.**

1. Correcting the PDFs. A total that does not add up, an 8-digit EIN, a $14,999 that the
   disclosure records as $15,000: flagged as a named exception, never fixed.
2. Re-deriving data from the disclosure workbooks. The disclosure is a later snapshot. It is
   used to report coverage, never to fill or overwrite a PDF value.
3. Serving the result through the MCP. §27 retired PDF-derived data from 2.0, and
   `mcp/test/no-pdf-data.test.js` enforces it. Where the output lives is open decision 2.
4. Repairing the old CSVs or the 2026-08-12/13 crosswalk. They stay as the historical record.
5. Splitting org from program on " - ", expanding caucus names, or normalizing member names.
   Derived columns can come later, each with a stated source.
6. Using an LLM or VLM to produce any value. OCR is an audit.

---

## 2. What the PDFs are (measured tonight)

### 2.1 All 20 Schedule C PDFs are born-digital

A pypdfium2 port of `textlayer.classify_pdf` (same rules: >100 chars/page, render-mode-3 share
above 0.5 means "scanned with an OCR layer") ran over all 20 files in 48.6 s
(`triage_pdfium.py`, measured tonight):

| FY | File (`source/`) | Pages | Invisible chars | Pages with ≤100 chars | Page sizes (pt) |
|---|---|---:|---:|---|---|
| 08 | `FY08/schedule_c_rvs_2008.pdf` | 123 | 0 | none | 612×792, 792×612 |
| 09 | `FY09/fy09-Schedule-C-final.pdf` | 246 | 0 | none | 612×792, 792×612 |
| 10 | `FY10/fy_2010_sched_c_final.pdf` | 408 | 0 | p.408 (closing page, 94 chars) | 612×792, 792×612 |
| 11 | `FY11/fy2011-C2011.pdf` | 291 | 0 | none | 612×792, 792×612 |
| 12 | `FY12/fy2012-skedcfinal.pdf` | 393 | 0 | none | 612×792, 842×595 |
| 13 | `FY13/fy2013-FY-2013-Schedule-C-Merge-Final1.pdf` | 258 | 0 | none | 612×792, 792×612 |
| 14 | `FY14/fy2014-skedc.pdf` | 439 | 0 | none | 4 sizes incl. A4 |
| 15 | `FY15/fy2015-FY15-Schedule-C-Template-Final.pdf` | 292 | 0 | none | 612×792, 792×612 |
| 16 | `FY16/fy2016-skedcf.pdf` | 352 | 0 | p.4 (0 objects: blank) | 612×792, 792×612 |
| 17 | `FY17/FY17-Schedule-C.pdf` | 355 | 0 | none | 612×792, 792×612 |
| 18 | `FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf` | 357 | 0 | pp.115–119 (0 objects: blank) | 612×792, 792×612 |
| 19 | `FY19/Fiscal-2019-Schedule-C-Final-Report.pdf` | 357 | 0 | none | 612×792, 792×612 |
| 20 | `FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf` | 405 | 0 | none | 612×792, 792×612 |
| 21 | `FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf` | 343 | 0 | none | 612×792, 792×612 |
| 22 | `FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf` | 326 | 0 | none | 612×792, 792×612 |
| 23 | `FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf` | 334 | 0 | none | 612×792, 792×612 |
| 24 | `FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf` | 453 | 0 | none | 3 sizes incl. 1148×887 |
| 25 | `FY25/Fiscal-2025-Schedule-C-MERGE-FINAL-2.pdf` | 455 | 0 | none | 4 sizes |
| 26 | `FY26/Fiscal-2026-Schedule-C-4.pdf` | 469 | 0 | none | 612×792, 792×612 |
| 27 | `FY27/Fiscal-2027-Schedule-C-Final-3.pdf` | 498 | 0 | none | 5 sizes |

7,154 pages, 0 invisible characters, every file classified `text`. **No Schedule C year needs
OCR as its primary path.** §3 still covers that path, because the gate must catch a future
year that arrives scanned. Two small quirks: FY09 has pages with `/Rotate` 90, and FY11 pp.2–52
draw their header rule as a 4224×4 px image, which the vector path will not see as a line.

**Christian's `textlayer.py` crashes on these files in its own environment.** With PyMuPDF
1.28.0 on Python 3.11.15 (the exec-orders venv), `classify_pdf` aborted the interpreter
(`Fatal Python error: none_dealloc`) on 19 of the 20 Schedule C PDFs. On FY27 it died after 61
pages of `page.get_texttrace()`. Only FY09 completed. That is a second reason, after AGPL
licensing, to port the gate to pypdfium2 rather than import it (§8.3). The prototype notes
report a successful textlayer run on FY25–27 earlier tonight. The environment for that run is
not recorded, and this plan does not try to reconcile the two.

### 2.2 FY2009–FY2014 do print organizations and EINs

DATA-ANOMALIES §2 and `code/PARSING.md` say FY2009–FY2014 Schedule C is "initiatives-level only
… no per-organization award rows and no EINs." The PDFs disagree. Measured tonight
(`ruled.py`, words matching `NN-NNNNNNN` or 9 bare digits, after stripping `*` and `-`):

| FY | EIN-shaped words | inside a pdfplumber lines-strategy table | Example (page, text as extracted) |
|---|---:|---:|---|
| 08 | 0 | 0 | — |
| 09 | 4,535 | 4,497 | p.8 `Church Avenue Merchants Block Association $44,696 11-2480339` |
| 10 | 4,345 | 4,200 | p.6 `BillieHolidayTheatre,Inc. * $82,000 11-2336154` |
| 11 | 4,516 | 4,515 | p.53 header `Member Sponsor LegalNameofOrganization EIN * Amount Agency PurposeofFunds FiscalConduitName FCEIN` |
| 12 | 4,547 | 4,542 | p.100 `Local Quinn AmericanPlaceTheatre,Inc. 13-1997644 * $3,000DCA` |
| 13 | 5,069 | 5,022 | p.8 `Legal Aid Society $750,000 13-5562265` |
| 14 | 5,473 | 4,891 | p.100 `Aging Dickens OneStopSeniorServices 133174492 * $8,000…` |
| 15 | 5,254 | 5,217 | |
| 16 | 5,587 | 5,333 | |
| 17 | 5,221 | 4,716 | |
| 18 | 5,974 | 5,853 | |
| 19 | 6,023 | 5,754 | |
| 20 | 7,917 | 7,243 | |
| 21 | 6,173 | 6,173 | |
| 22 | 5,727 | 5,684 | |
| 23 | 5,923 | 5,510 | |
| 24 | 9,289 | 8,502 | |
| 25 | 9,578 | 9,578 | (vector prototype: 9,579 rows) |
| 26 | 9,763 | 9,763 | (vector prototype: 9,765 rows; the FY26 plan records two 8-digit EINs) |
| 27 | 9,979 | 9,979 | (vector prototype: 9,979 rows) |

These are **EIN-shaped tokens, not award rows.** They include conduit and fiscal-sponsor EINs
("Tax ID# for Conduit/Administrator", FY09 p.4), and the 9-bare-digit pattern can match other
numbers. They are an upper bound and a census anchor, nothing more. But the header on FY10
p.61 and FY11 p.53 is an award table with member, sponsor, EIN, amount, agency, purpose and
fiscal conduit columns. So FY2009–FY2014 are award-bearing years for this plan, and §2 owes a
correction (open decision 3).

Two more facts from this table:

- **FY10–FY14 extract with glued words** (`AmericanPlaceTheatre,Inc.`), the "glued text layer"
  of DATA-ANOMALIES §3. On FY12 p.100 the spaces come back from geometry: pdfplumber
  `extract_text(x_tolerance=1)` gives `Local Quinn American Place Theatre, Inc. 13-1997644 *
  $3,000 DCA`. The default tolerance of 3 does not. That is one line on one page, so
  `x_tolerance` becomes a per-year configured, snapshot-tested value, not an assumption.
- **The years whose EIN tokens all sit in ruled tables** are FY21, FY25, FY26 and FY27. In
  every other year some EIN pages have no table that pdfplumber's lines strategy finds (FY24:
  33 pages; FY14: 50). Those pages need the image lattice, a text-strategy table, or both.
  Finding out which is part of onboarding each year (§6).

### 2.3 What FY2025–FY2027 already proved (from the 2026-10-19 notes)

- Vector parse on drawn borders with char-center cells: FY25 9,579 rows, FY26 9,765, FY27
  9,979. (EIN, amount) multiset matches against the disclosure: 9,386 / 9,529 / 9,859.
- FY27 image lattice (Christian's `grid.py`, per table region, 60 px kernel): 9,952 of 9,979
  rows agree on every field. The 27 others are vector-side artifacts (18 stray-hyphen EINs, 7
  fallback row bands, 2 text differences). None is an image misread.
- docTR full-page OCR: 115/115 EINs and 115/115 amounts on 5 pages. `reread_cell` got 82/115
  digits right, and 8 of its misreads passed the validators (one at confidence 0.933).
- The old parse lost real awards: FY27 Medicare Rights Center $135,000 (p.279); FY25 13 rows,
  $9.1M (Bronx Defenders $5,533,333, p.169); FY26 13 rows, $8.6M.
- The fragile step is attaching rows to initiatives. The guard is "each initiative's rows sum
  to its printed designated amount."

---

## 3. Pipeline

One stage, one artifact on disk, cached by input hash, as in Christian's driver. "Reuse"
means import the named function unchanged. "Configure" means pass different arguments.
"Patch" means a small change offered back upstream. "Port" means rewrite with attribution
because importing is not viable. "New" is our code.

| # | Stage | Christian's module (real function) | Mode | Artifact |
|---|---|---|---|---|
| 0 | Triage gate, per page | `textlayer.classify_pdf` rules (`TEXT_LAYER_CHARS_PER_PAGE_THRESHOLD`=100, `INVISIBLE_CHAR_SHARE_THRESHOLD`=0.5, `image_only_pages`) | **port** to pypdfium2 | `triage.json` |
| 1 | Render | `ocr/render.py` `render_pdf(pdf_path, cache_dir, dpi=300, pages=None, force=False)`, `parse_page_spec(spec)` | **reuse** | `raw/page-NNN.png` |
| 2 | Page map | `ocr/classify.py` `classify_page(gray)` | **not used as a gate** (see below) | `pages.csv` |
| 3 | Vector lattice | — (pdfplumber `page.find_tables()`, lines strategy) | **new** | `vector_grid.json` |
| 4 | Image lattice | `ocr/grid.py` `detect_grid(gray, …, kernel_divisor=…)`, `Grid`, `span_diagnostics`, `draw_overlay` | **reuse + configure**, **patch** (`kernel_px`) | `image_grid.json`, overlays |
| 5 | Cell text | `ocr/recognize.py` `assign_words` rule (centroid containment) | **reuse the rule**, new code over PDF chars | `cells.jsonl` |
| 6 | Ink coverage | exec-orders `vlm_ocr.ink_coverage`, `find_uncovered_regions`, `_tight_bbox` | **port** and re-target | `ink.json`, red overlays |
| 7 | Structure | — | **new**, per-year config | `structure.json` |
| 8 | Reconcile | — | **new** | `checks.txt` |
| 9 | Disclosure alignment | — (rules from DATA-ANOMALIES §23) | **new**, report-only | `disclosure_match.csv` |
| 10 | OCR audit | `ocr/recognize.py` `Engine(det_arch="db_resnet50", reco_arch="crnn_vgg16_bn")`, `Engine.words(gray)`, `assign_words(words, grid)`, `cell_text(words)`, `find_cell_span_conflicts` | **reuse**, report-only; **never** `reread_cell` | `ocr_audit.csv` |
| 11 | Review queue + UI | exec-orders `qa-ui/` (`server/api.js` `createApi`, `src/pdfPage.jsx` `PdfPage`, `src/qa.jsx` `FLAG_SEVERITY`/`worstSeverity`) | **adapt** (copy with attribution) | `review.csv`, local web app |

### Stage 0: triage gate

Port, not import: `textlayer.py` imports `fitz` (PyMuPDF, AGPL) at module top, and it crashed
on 19 of 20 files tonight (§2.1). The port keeps his three classes and thresholds and his
per-page list, using pypdfium2 calls verified tonight on all 20 files: `PdfTextPage.count_chars()`,
`PdfPage.get_objects()`, `raw.FPDFTextObj_GetTextRenderMode` compared against
`raw.FPDF_TEXTRENDERMODE_INVISIBLE`, and `raw.FPDFTextObj_GetText`. Character totals differ by
engine (FY27: pdfium `count_chars` 1,750,113; the notes' PyMuPDF figure 1,682,167), so the
threshold is re-measured once on the pdfium counts and the "empty valley" is written next to
the constant. The gate also records per page: image objects, path objects, `/Rotate`, size.

Routing: `text` pages go down the vector path. `scanned` or `scanned-ocr-layer` pages, or a
`text` page with no characters inside a table region, go down §4's path. A page the year's
config says should hold awards but which classifies otherwise is a **critical** flag.

### Stage 2: page map, without `classify_page` as a gate

On FY27, `classify_page` labeled pages holding 1,095 award rows `narrative`, because
`count_rules` measures spans against one whole-page bounding box and portrait pages stack
several tables (image-grid report). Here the page map comes from the year's config (page
ranges by size and header text, as each FY plan's "PDF map" does) and is checked, not
inferred. `classify_page` output is kept as a recorded second opinion only.

### Stage 3: vector lattice (primary)

pdfplumber `find_tables()` per page, default lines strategy. The FY27 plan measured 9,978
single-EIN rows against 9,979 EIN tokens across 498 pages in 41.5 s. Then:

- **Drop phantom columns:** a vector column separator that only edges a white-filled rect
  (FY27: 2,269 such separators, e.g. p.33's 5.4 pt slivers) is dropped when the image lattice
  has no separator within 2 pt *and* no character lies in the sliver. Both conditions are
  logged.
- **Pages with EINs but no lines-strategy table** (FY24 33 pages, FY14 50, §2.2) fall back to
  the image lattice for geometry. Text still comes from the PDF characters. If neither lattice
  holds the row, it is a critical flag. Never a line-based fallback like the one behind FY27's
  7 row-band flags.

### Stage 4: image lattice (independent check)

Christian's `grid.detect_grid` called once per **table region**, not per page. Whole-page mode
returned no lattice on 91 of 107 FY27 multi-table pages. Regions are connected components of a
rule mask opened with a 60 px kernel, padded 8 px. That region finder was scratch code
(`regions()` in the FY27 `image_grid.py`) and becomes new code here. Kernel: `kernel_px=60`
once the patch lands; until then the integer divisor `max(2, min(crop_h, crop_w) // 60)`, as
in the FY27 run. Christian's defaults on cropped tables produced 121 missing award rows,
because a ~24 px kernel is shorter than an 11 pt glyph stem at 300 dpi (~33 px). Both values
are per-year config, re-checked against each year's body font size.

Known blind spots, recorded and not "fixed": fill-only boxes and title bars have no image
lattice (FY27: 180 vector tables). The 60% span test drops the Agency|Initiative rule under a
merged TOTAL row (4 FY27 summary tables). Summary tables are therefore checked by arithmetic
(H10), not by lattice agreement.

### Stage 5: cell text

Each PDF character goes into the one cell that holds its center, which is Christian's
`assign_words` rule applied to characters instead of OCR words. This removed the 18 FY27
stray-hyphen EINs. Raw cell text keeps line breaks. Text is clipped to **both** lattices, and
H8 requires the strings to be identical. Word gaps come from geometry with a per-year
`x_tolerance` (§2.2). Nothing is dehyphenated: a line-end hyphen is kept in `*_raw`, and the
join rule in the clean column flags its own ambiguous cases (§5.2).

### Stage 6: ink coverage (the dropped-content check)

Christian's `ink_coverage` is, in his docstring's words, "the only QA signal here that can see
*dropped* content." Schedule C prints no award total, so it fills the missing completeness check.
The re-targeted question: **is every inked pixel inside an award table accounted for by
something we emitted or by a drawn rule?**

1. Render at 300 dpi (stage 1). Ink = `grid.binarize(gray)` (Christian's fixed 128 threshold;
   rules render as 2–4 px solid black per the image-grid report).
2. Measure only inside the year's award-table regions (stage 4 regions ∪ stage 3 table
   bboxes), so his ROI margin and scanner-bed trim are not needed on digital renders.
3. Covered = union of (a) the bbox of every character we emitted into an output field,
   pt→px, padded by a margin measured on FY27, and (b) every vector line and rect stroke from
   pdfplumber, drawn at its true width. Born-digital pages give exact rule geometry, so (b)
   replaces his `rule_pixels` heuristic, which was tuned for 200-dpi scans.
4. Uncovered ink is grouped with the ported `find_uncovered_regions(uncovered, cell_px,
   min_region_ink, offset)` and `_tight_bbox`. `cell_px` and `min_region_ink` are re-measured
   on FY27 (his are 24 px and 400 px at 200 dpi).
5. Any region left over is a **critical** flag with a red overlay, as in his overlays.

Acceptance before relying on it: on FY27, (i) the clean run reports zero regions, or each
residual is explained; (ii) deleting the Medicare Rights row (p.279) from the emitted set makes
the check fire on that row; (iii) deleting one emitted character (the p.486 hyphen class) makes
it fire. If (i) cannot reach zero without thresholds that blind (ii) and (iii), it ships as
**warn**, and the plan says so.

### Stage 7: structure

Sections, categories, initiatives and appendices are assigned by **(page, y) geometry, never
by content-stream order**. FY27 p.205 emits a box after rows that sit below it, and the old
parser mislabeled 56 FY27 rows that way. Per-year config gives page ranges, header variants,
box signatures (FY27: bold 12 pt at x≈77 followed by `Agency:`) and the designation-statement
grammar. An unknown header is a hard failure (FY26 plan check 4). Rows attach to the last
initiative box above them; a landscape insert inherits from the preceding portrait page.

### Stage 8: reconcile

Every printed number the document can check against itself (§6, H10–H13). Self-errors are
**named exceptions** in config, keyed by page and both amounts. The check passes only if the
observed difference equals the named one, so a second error on the same initiative still fails.

### Stage 9: disclosure alignment (report-only)

Rules from DATA-ANOMALIES §23 and the FY plans: (EIN, amount) multiset; never EIN alone; never
council member; City EIN 13-6400434 also needs a name-prefix condition (FY27: 130 of 757
City-EIN pairs, $4,236,500, paired different agencies without it). Rows and dollars, Cleared
and Pending, by stream, with one waterfall reason per unmatched row and the count of ambiguous
keys. Pinned to the 2026-10-12 snapshot. The disclosure never changes a PDF value.

### Stage 10: OCR audit (report-only, sampled)

docTR through Christian's `Engine.words` → `assign_words` → `cell_text` on the image lattice.
Compare EIN digits and amount digits only, since OCR is unreliable on org text (290 of 341
FY27 text cells exact; it drops " - " and reads `Italian` as `ltalian`). Sample: every page
with any flag, plus a fixed sample seeded from the PDF's sha256. **`reread_cell` is never
called.** Its validated misreads would silently replace correct values. Use as a tie-break
for text-layer disagreements like p.486 (`multi media` in the text layer, `multi-media` in the
pixels): the review row shows all three reads, and a person decides.

dots.ocr (`vlm_ocr.py`) is optional and only for disputed pages. It runs in the exec-orders
environment as an external tool, because `vlm_ocr` imports `fitz` and the MLX/CUDA stacks.
Its JSON is consumed as one more report-only read. Not in the build.

### Stage 11: review queue and UI

`review.csv` is the product of every stage (schema in §5.3). The UI adapts Christian's
`qa-ui`: the PDF page on the left via pdf.js with live boxes (vector lattice, image lattice,
the row's cells, uncovered ink in red), the row's raw and clean fields and its flags on the
right, his critical/warn severity and "needs review" filter, and his hash deep links
(`#collection=…&unit=…&page=…`) so a review row can link straight to its page. It reads our
per-page JSON through a small `createApi`-style middleware. Local dev tool only, never
deployed.

---

## 4. If a year is scanned or carries an OCR layer

None does today (§2.1). If the gate ever routes a Schedule C year, or some pages of one, away
from `text`:

1. **Primary path becomes PR #43's pipeline:** `render_pdf` → `orient_page(gray, engine,
   override, do_dewarp)` → `detect_grid` → `Engine.words` + `assign_words` + `cell_text` →
   `map_header` (with Schedule C aliases added: "Tax ID", "Legal Name of Organization – Program
   Name", "Sponsor", "Purpose of Funds") → our structure and reconcile stages.
2. **The vector lattice is gone, so the image lattice is primary,** and H8 changes from
   "two lattices agree" to "a second OCR pass agrees": full-page OCR at two DPIs, or docTR
   plus dots.ocr. Every disagreement goes to review.
3. **`reread_cell` stays off as a replacement.** It may run as one more report-only read.
4. **Christian's validators** (`parse_ein`, `parse_amount`) gate shape only. A value that
   validates is not thereby right (8 FY27 counterexamples).
5. **Ink coverage moves closer to his original:** OCR word boxes are the "elements", and his
   `rule_pixels` handles rules, since a scan has no vector geometry.
6. **Severity rises:** on a scanned year, any OCR-sourced EIN or amount without a second
   agreeing read is critical, not warn.

The "scanned-ocr-layer" class gets the same treatment. Somebody else's invisible OCR is a
guess we did not make and cannot audit.

---

## 5. Outputs

### 5.1 Tables (per year, per structure)

Same split as the FY27 plan, generalized: `fyNN_sc_categories`, `fyNN_sc_initiatives`,
`fyNN_sc_body_awards`, `fyNN_sc_appendix_awards`, `fyNN_sc_pages` (every page: family, printed
page label, triage class), `fyNN_sc_review`, `fyNN_sc_disclosure_match` (derived, separate),
`fyNN_sc_checks.txt`, plus `fyNN_sc_manifest.json` (input sha256, config hash, tool versions).

**Provenance on every row:** `pdf_sha256`, `pdf_page`, `table_index`, `row_index`, `bbox_pt`
(`x0,top,x1,bottom`, rounded to 0.01 pt), `lattice` (`vector` | `image` | `both`). `award_id` =
`fyNN-pPPP-tTT-rRRR`. That is stable for a given PDF and config, and the snapshot tests catch
any change.

**Raw and clean side by side** (the `clean.py` principle: clean is derived, raw is never
overwritten). For each text field: `<field>_raw` (cell text as extracted, line breaks kept)
and `<field>` (clean). For numbers: `<field>_printed` (verbatim) and the parsed value. A clean
value may differ from raw only by rules listed in the module docstring: whitespace collapse,
zero-width-space removal (counted), and line-break joins (§5.2). Each row carries
`clean_rules_applied`.

Multi-valued people cells (`J. Sanchez; Riley`, `Brewer, Caban, LGBTQIA+`) stay as printed.

### 5.2 The one join rule

At a line break: join with no space when the line ends in a hyphen not preceded by a space,
otherwise join with a space. When the hyphen could be either a compound hyphen
(`Home-⏎Delivered`) or a split word, the row carries flag `wrap_hyphen` (warn) and the clean
value keeps the hyphen. Never a dictionary lookup.

### 5.3 Review file

One row per (check, location). It is never silently empty: a year with zero rows writes a
header plus an `ok` line naming the checks that ran.

| Column | Meaning |
|---|---|
| `review_id` | sha1 of (fy, check_id, pdf_page, table_index, row_index, field). Stable across re-runs, so decisions survive |
| `fiscal_year`, `pdf_sha256`, `pdf_page`, `table_index`, `row_index`, `bbox_pt` | where |
| `check_id` | e.g. `H8.cell_text`, `H9.ink`, `H12.designated_sum`, `W4.ocr_amount` |
| `severity` | `critical` (content provably missing or wrong: qa-ui's definition) or `warn` (worth a look) |
| `field` | column involved, if any |
| `value_vector`, `value_image`, `value_ocr`, `value_disclosure` | every independent read we have, verbatim; empty where not run |
| `expected`, `observed` | for arithmetic checks |
| `overlay` | path to the page PNG with both lattices and the region drawn |
| `link` | review-UI deep link |

Human decisions live in a separate committed file, `fyNN_sc_review_decisions.csv`:
`review_id`, `decision` (`source_error` | `parser_bug` | `accepted_as_printed` | `needs_info`),
`note`, `decided_by`, `decided_at`. The pipeline never writes it. A decision on a `review_id`
that no longer exists is reported as stale, never dropped silently. Re-running is idempotent.

### 5.4 Severities

- **critical:** fails the build unless the location is a named exception in config, or holds
  a `source_error` / `accepted_as_printed` decision. Examples: uncovered ink, lattice
  disagreement on a cell, a row with ≠1 EIN, an initiative that does not sum.
- **warn:** reported and counted, never fails. Examples: OCR disagreement on a sampled page,
  wrap-hyphen joins, City-EIN name mismatch, multi-valued sponsor cells.

---

## 6. Checks

Hard checks fail the build. Each prints its own numbers into `checks.txt`.

| # | Check |
|---|---|
| H1 | Input identity: PDF sha256 equals config. |
| H2 | Triage: class `text`, 0 invisible chars; no page in an award range has ≤ threshold chars. |
| H3 | Page map: every page has exactly one family; any page outside the config map fails. |
| H4 | Headers: every table header matches a registered variant for the year. |
| H5 | Anchor census: per page, EIN-shaped tokens from `extract_words()` (an independent read) = award rows + tokens classified as non-award (conduit EINs, etc.); each award row has exactly one EIN cell and one amount cell. |
| H6 | No data cell holds header or footer furniture (`Legal Name of Organization`, `Tax ID`, `Page N`, `Appendix X:` …). |
| H7 | Character conservation: every non-whitespace character on an award page is in exactly one cell or a classified furniture region. 0 unclassified. |
| H8 | Lattice agreement on award tables: row separators within 1 pt; each vector column separator that bounds non-empty text has an image separator within 2 pt; cell strings from both lattices identical. |
| H9 | Ink coverage: no uncovered-ink region inside an award table (stage 6; downgraded to warn only if its acceptance test fails, and stated). |
| H10 | Category summary lines sum to the printed TOTAL (named exceptions only). |
| H11 | Initiative box amounts equal summary lines, as a multiset per category. |
| H12 | Each initiative's rows sum to its designated amount by statement kind (full / partial / post-adoption only / direct); named exceptions only. |
| H13 | Roll-up identity where the year's statements allow it (FY27: body rows + post-adoption reserves = GRAND TOTAL − the named $1). |
| H14 | Provenance on every row; `award_id` unique. |
| H15 | Determinism: two runs byte-identical; per-page row and column counts equal the snapshot. |
| H16 | No value altered: every `*_printed`/`*_raw` equals the cell text; clean differs only by listed rules. |
| H17 | Regression floor against the pinned 2026-10-12 disclosure snapshot (FY25 9,386 / FY26 9,529 / FY27 9,859 matched rows). This tests the parser, not the truth. |

Warn checks: W1 appendix pots (§19 equal-per-district amounts, since the PDF prints no
appendix total); W2 disclosure coverage with waterfall reasons and ambiguity counts; W3 OCR
audit disagreements; W4 City-EIN name mismatches; W5 `wrap_hyphen` joins; W6 zero-width or
control characters in cells (counted); W7 multi-valued people cells.

**What these checks cannot prove:**

1. That an award exists which the PDF never printed. The PDF is the universe.
2. Award-stream completeness by arithmetic. No award or appendix total is printed. H5, H7, H9
   and H12 together are the substitute.
3. Text correctness where both lattices read the same wrong text layer (p.486). Only OCR or a
   person sees pixels, and OCR is sampled.
4. Which side is right when the PDF disagrees with itself.
5. Per-row disclosure status where several rows share an (EIN, amount) key (FY27: 2,196
   matches with more than one identical candidate).
6. Member or sponsor attribution, which the disclosure records with the roster at export time.

---

## 7. One plan per fiscal year

Each year gets `config/schedule_c/fy20NN.toml` (read with stdlib `tomllib`, available across
3.11–3.14) holding everything year-specific and nothing else: sha256; page ranges by family;
ToC printed-to-PDF page offsets; header variants; box signature; designation-statement
patterns; `x_tolerance`; image `kernel_px`; named exceptions (page, expected, printed, a
one-line description); expected per-page row and column counts (the snapshot); sample pages
for golden tests. Code is shared. A change to shared code must keep every onboarded year's
snapshot green.

**Onboarding a year** (one PR per year):

1. Run the gate and the census (§2 numbers for that year) and write the page map by reading
   pages, as the FY25–27 plans did.
2. Draft the config. Run. Every unknown header, unmapped page and critical flag is either a
   config fact (cite the page) or a review row.
3. Image-lattice pass with overlays. Re-check the kernel against the year's body font.
4. Golden rows from 8–12 hard pages, written by reading the page, not by copying parser output.
5. Commit the snapshot, `checks.txt` and the review file. A person reviews the critical rows
   before merge.

Order: FY27, FY26, FY25 (planned). Then FY24 back to FY15, where DATA-ANOMALIES §20's 276
merged rows sit (FY16–FY19 mostly). Then FY09–FY14 after a scoping PR (glued text, conduit
columns, A4 pages). FY08 last: 0 EIN-shaped tokens, so likely initiatives only (unverified
beyond the census).

---

## 8. Code layout, dependencies, licensing, runtime

### 8.1 Layout (proposed)

```
code/schedc/                  deterministic core: pdfplumber + pypdfium2 + stdlib only
  triage.py                   stage 0 (pypdfium2 port of textlayer.classify_pdf, credited)
  pagemap.py  vector.py  cells.py  structure.py  reconcile.py  disclosure.py
  review.py   emit.py   config.py
code/schedc_cv/               optional "cv" extra: opencv-python-headless, numpy
  imagegrid.py                stage 4: region finder + calls into code/ocr/grid.py
  ink.py                      stage 6: port of ink_coverage/find_uncovered_regions, credited
code/schedc_audit/ocr.py      optional "ocr" extra: stage 10 via code/ocr/recognize.py
code/parse_schedule_c_v2.py   CLI: --fy, --stage, --pages, --cache-dir (mirrors Christian's driver)
code/test_schedc_*.py         unit + golden-row + snapshot tests (repo convention: tests in code/)
code/testdata/schedc/         small page fixtures (single-page PDFs cut with pypdfium2)
config/schedule_c/fy2027.toml …
tools/schedc-review-ui/       adapted qa-ui (Node; local only)
code/requirements-cv.txt      new; requirements-ocr.txt reused as is
```

Output location is open decision 2.

### 8.2 Dependencies and versions

- Core stays on `code/requirements.txt` as is (`pdfplumber>=0.11,<0.12`, pypdf). pypdfium2
  already arrives with pdfplumber; because the core imports it, declare it explicitly with a
  ceiling (`pypdfium2>=4.30,<5`, the bound PR #43 already uses).
- `requirements-cv.txt`: `opencv-python-headless>=4.9,<5`, `numpy>=1.26,<3` (PR #43's bounds),
  no torch. This is enough for stages 4 and 6.
- `requirements-ocr.txt` from PR #43 unchanged (`python-doctr[torch]>=0.11,<0.13` …).
- **Lock exact versions** with `uv pip compile` per requirements file, and run the snapshot
  tests against the lock. Table detection and rendering are version-sensitive (§15 was a
  toolchain change). The prototypes ran pdfplumber 0.11.9 and 0.11.10; PR 1 settles one.
- **Python range 3.11–3.14**, tested at both ends. This repo has no Python CI job today
  (`.github/workflows/ci.yml` runs Node only), so PR 1 adds one. docTR/torch wheel availability
  on 3.14 is not verified. Detect it in PR 7; if missing, the OCR extra declares a narrower
  range rather than holding back the core.
- No PyMuPDF anywhere in shipped code.

### 8.3 Licensing

This repo is MIT; so is `nyc-executive-orders`. Ports of `textlayer`, `ink_coverage` and
`qa-ui` keep Christian's and Noel's names in the module docstring with the source commit.
PyMuPDF is AGPL-3.0, so it stays out of shipped code; `vlm_ocr` stays an external tool. PR 1
runs a license report over the locked environments (e.g. `pip-licenses`) and records the
result, rather than this plan asserting each package's license from memory. The dots.ocr
weights' license is checked before any optional use.

### 8.4 Determinism

Sorted iteration everywhere; coordinates rounded to 0.01 pt before comparison and output;
seeded OCR sample; no timestamps in data files (the manifest carries them); fixed render DPI
300; fixed binarization threshold 128; pinned pdfium (inside pypdfium2) and OpenCV versions.
H15 runs twice in CI on one year.

### 8.5 Runtime budget (FY27, CPU, from the notes)

pdfplumber vector pass 36.7–41.5 s; render 21.5 s; image grids for all pages 113 s; clipping
and compare 34 s; docTR ~4.4–7.6 s per page after a 10.2 s model load. Full-document OCR would
take about 50 minutes (extrapolated, not measured), hence sampling. Targets per year: core
under 2 minutes, plus cv under 4 minutes, plus OCR sample under 10 minutes. CI runs the core
and cv on fixtures plus one full year, and OCR on fixtures only, behind a manual trigger.

---

## 9. Working with Christian, and PR #43

**Where PR #43 stands (checked tonight):** open, not draft, `mergeable: CONFLICTING`. A
`git merge-tree` of `pr43` onto `origin/main` conflicts only in `DATA-ANOMALIES.md`,
`README.md`, `code/PARSING.md` and `data/QA-REPORT.md`. `code/ocr/` and its tests merge
cleanly. `code/ocr/__init__.py` has no imports, and heavy libraries load lazily inside
functions, so `grid.py` imports with OpenCV and numpy only. One coupling to note:
`assemble.py` imports `parse_transparency_reso` at module top. This plan does not import
`assemble`.

**Options.**

1. *Land #43 first, then import `code/ocr/` unchanged.* One copy of his code; his tests guard
   it; the kernel patch goes upstream as a small follow-up. Cost: waits on the doc-conflict
   resolution, and #43 also brings FY09 transparency CSVs, which under §27 would be kept as
   historical record, not served.
2. *Vendor `grid.py` and `render.py` into `code/schedc_cv/`.* Unblocked today, but two copies
   drift, and his fixes stop reaching us.
3. *Extract a shared package used by both repos.* Right eventually if a third consumer
   appears. Premature now: one module (`grid.py`) is shared, and the exec-orders pieces we use
   are ports.

**Recommendation: option 1.** Resolve #43's four doc conflicts (Christian, or Noel with his
OK), merge it, then open the `kernel_px` patch as its own small PR with his test suite green
(44 passed, 1 skipped with the patch, per the image-grid report). Schedule C PRs that need
`grid.py` (PR 5 below) stack on that. PRs 1–4 do not need #43 and can proceed in parallel. If
#43 is not landing within two weeks, fall back to cherry-picking his `code/ocr/` commits (so
authorship is preserved) as PR 0, not to a copy-paste vendor.

**What to offer him** (public, so Noel's OK first; open decision 1):

1. The `kernel_px` patch ([`patches/grid-kernel-px.patch`](patches/grid-kernel-px.patch), in this
   folder): absolute kernel length, int cast so a float
   divisor no longer raises a cv2 `ksize` TypeError; defaults unchanged.
2. The re-read finding: on tall, vertically centered born-digital cells, `reread_cell` got
   82/115 digits right, and 8 wrong values passed `parse_ein`/`parse_amount`, including EIN
   `131740468` read as `131740458` at confidence 0.933. In his driver, a validated re-read
   replaces the cell.
3. `classify_page`'s single bounding box misclassifies stacked-table pages (1,095 FY27 award
   rows on `narrative` pages), and the 60% span test drops rules under merged cells.
4. To the exec-orders repo: the PyMuPDF crash in `textlayer.classify_pdf` (§2.1) and the
   pypdfium2 port, in case he wants it there too.

**What to ask him:**

1. Is `detect_grid`/`Grid` stable enough to import from other code, or would he rather it move
   behind a small interface first?
2. Would he review the image-lattice and ink-coverage PRs (5 and 6)?
3. Noel recalls another tool of his that may tie this together. Which is it?
4. Does he prefer the `ink_coverage` port as is, or a shared helper both repos import?
5. Has he tried dots.ocr on ruled financial tables?
6. Issue #44 (FY10–FY12 transparency via OCR) shares the glued-text problem with FY10–FY14
   Schedule C (§2.2). Is geometry-based word spacing worth sharing?

---

## 10. PR stack (budget repo; each branch on the previous; FY27 first)

Sizes are estimates of changed lines excluding fixtures.

| PR | Content | Size | Accept when |
|---|---|---|---|
| 0 | #43 lands (Christian's), then the `kernel_px` follow-up | his; ~10 | #43 merged; patch PR green on his suite |
| 1 | Python CI (3.11 + 3.14), lock files, `requirements-cv.txt`, license report | ~150 | CI runs the new tests and Christian's suite at both ends; `uv pip compile` locks committed; license report recorded |
| 2 | Stage 0 gate + `pages` inventory for all 20 PDFs | ~350 | reproduces §2.1 table exactly; unit tests on a synthetic invisible-text PDF and a blank page; credits in docstring |
| 3 | FY27 core: config, page map, vector lattice, cells, structure, emit | ~1,200 | 9,979 award rows; golden rows for FY27 pp.7, 13, 24, 179, 205, 274, 279, 335, 463, 486 match by reading the page; H1–H7, H14–H16 pass |
| 4 | FY27 reconcile + review file + decisions file | ~600 | H10–H13 pass with only the named $1 exception; review file non-empty and every row classified; re-run byte-identical |
| 5 | Image lattice (stage 4) + H8 | ~500 | FY27 9,952 rows agree on every field; the 18 hyphen and 7 band cases resolved by stage 5; remaining disagreements in review with overlays |
| 6 | Ink coverage (stage 6) + H9 | ~400 | the three acceptance tests in §3 pass, or H9 ships as warn and the PR says why |
| 7 | Disclosure alignment report (stage 9) + H17 | ~400 | FY27 9,859 (EIN, amount) matches reproduced; City-EIN rule and waterfall reasons present |
| 8 | OCR audit (stage 10), OCR extra | ~300 | 115/115 EIN and amount agreement reproduced on pp.7, 33, 279, 335, 463; no code path calls `reread_cell` (test asserts it) |
| 9 | Review UI (adapted qa-ui) | ~800 JS | opens FY27, deep link to p.279 works, needs-review filter lists every critical row |
| 10 | FY26 config + snapshot | ~300 + config | 9,765 rows; its 11 checks hold; known exceptions ($800, $15,000, two 8-digit EINs) named |
| 11 | FY25 config + snapshot | ~300 + config | 9,579 rows; Bronx Defenders $5,533,333 (p.169) under the right initiative; Parks has no summary table, recorded |
| 12 | DATA-ANOMALIES corrections | docs | §23 (Medicare Rights is in the PDF), §2 (FY09–14 print EINs), PARSING.md status |
| 13+ | FY24 … FY15, one PR each; then an FY09–FY14 scoping PR | per year | §7 onboarding steps |

---

## 11. Risks, open decisions, effort

### Risks

1. **Agreement is not truth.** Both lattices read the same text layer; p.486 passed both.
   Mitigation: OCR sample, ink coverage, a person on every critical row.
2. **Initiative attribution** relies on per-year formatting cues. H12 catches a shift unless
   shifted amounts happen to be equal. Golden rows on every wrapped-title and out-of-order page.
3. **Ink coverage may be too noisy on some years** (anti-aliasing at glyph edges, fills). It
   ships as warn if it cannot meet its acceptance tests, and the doc says so.
4. **Tool drift.** pdfplumber, pdfium and OpenCV behavior can change between versions. Locks
   plus per-page snapshots.
5. **Scope creep into FY09–FY14,** now that they turn out to carry EINs (§2.2). Kept behind a
   separate scoping PR.
6. **Christian's availability.** Option 1 waits on #43. The fallback is a cherry-pick with
   authorship kept.
7. **Heavy optional stack** (torch, ~165 MB of weights per the image-grid report). Kept out of
   the core.

### Open decisions for Noel

1. **PR #43 relationship.** Recommendation: land #43 first and import `code/ocr/` unchanged;
   offer the `kernel_px` patch and the re-read finding to Christian publicly; cherry-pick with
   authorship if #43 stalls for two weeks.
2. **Where clean output lives.** Recommendation: its own path (e.g. `data/schedule_c_v2/fyNN/`)
   with a README stating "research, not served," outside the MCP until every hard check passes
   for that year. The 2.0 guard test stays as is.
3. **Corrections to the published record.** Recommendation: publish DATA-ANOMALIES entries
   correcting §23 (Medicare Rights $135,000 is in the FY27 PDF; the old parser lost it) and §2
   (FY09–FY14 PDFs print organizations and EINs), with "flag, never fix" as the stated stance
   on PDF self-errors.
4. **Which text is the record when pixels disagree with the text layer** (p.486; FY25's
   Excel-clipped purpose text, which is complete in the text layer but cut on screen).
   Recommendation: the text layer is the record; a pixel disagreement goes to review with both
   values and is never auto-replaced.
5. **Order after FY25–27.** Recommendation: FY24 back to FY15 next, because DATA-ANOMALIES
   §20's merged rows live there, then scope FY09–FY14.

### Effort (estimates)

| Work | Days |
|---|---|
| Shared infrastructure: PRs 1, 2, 5, 6, 7, 8, 9 | 6–8 |
| FY27 year-specific: PRs 3, 4 (the FY27 plan put the whole year at ~4 days, plus 2–2.5 for the image check, part of which is now shared) | 3–4 |
| FY26, FY25 (the plans said 4–4.5 and 5–5.5 standalone; shared code removes about half) | 2–3 each |
| Each of FY24 … FY15 | 2–3 each, unverified until a year is onboarded |
| FY09–FY14 scoping, then per year | 1 for scoping; per-year unknown |
| Human review of each year's critical rows | 1–2 hours per year |

FY25–FY27 end to end, with the UI: about 13–18 working days.
