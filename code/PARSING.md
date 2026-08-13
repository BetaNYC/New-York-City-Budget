# PARSING.md — per-fiscal-year processing manifest

How to reproduce every `data/fyNN/…` CSV in this repo, fiscal year by fiscal year and
document type by document type: which parser (or parser variant) + exact invocation
produces it, and its reconciliation status.

**This file is authoritative for "how do I regenerate FY_N_?"** The README's "Reproduce or
extend to a new year" section shows the generic pattern for a *clean* modern year; this file
records the real, per-year specifics for the full FY2008–FY2027 range, including the years
that need a variant parser and the ones that are blocked at the source.

All commands assume you are at the repo root with the venv active (`.venv/bin/python`), and
that the packages in `code/requirements.txt` are installed (`pypdf`, `pdfplumber`,
`cryptography`).

## Parsers and which document type each one handles

| Parser | Document type | Text technique |
|---|---|---|
| `parse_schedule_c.py` | Schedule C (discretionary expense) | pypdf text layer, ToC-driven |
| `parse_schedule_c_fy15.py` | Schedule C — **FY2015 only** (adjacent-heading block→category mapping) | pypdf text layer |
| `parse_schedule_c_legacy.py` | Schedule C **initiatives** (early era, FY09-FY14) | pypdf text layer |
| `parse_terms.py` | Terms & Conditions, **numbered-item** format (FY25–FY27) | pypdf text layer |
| `parse_terms_legacy.py` | Terms & Conditions, **unnumbered-header** format (FY15–FY24) | pypdf text layer |
| `parse_capital.py` | §254 Capital Project Detail — **FY27** clean-pypdf (city `CC/DN` **and** non-city `MA/0N` rows) | pypdf text layer |
| `parse_capital_fy26.py` | §254 Capital Project Detail — **FY26** (pypdf-scrambled) | pdfplumber word coordinates |
| `parse_capital_fy25_detail.py` | §254 Capital Project Detail — **FY25 Council-additions detail book** (Parts I+II+III) | pdfplumber word coordinates |
| `parse_capital_detail.py` | §254 Capital Project Detail — **FY20/FY22/FY23/FY24** ("Supporting Detail Book") | pdfplumber `extract_text()` (clean reading order) |
| `parse_capital_fy25.py` | §254 Resolution-A / Appropriation-Changes (FY25 appropriation book + FY17/FY21/FY23/FY24) | pdfplumber word coordinates |
| `parse_transparency_reso.py` | Post-adoption Transparency Resolutions | pdfplumber word coordinates |
| `parse_transparency_reso_fy09.py` | Transparency Resolutions — **FY09 only** (scans, no text layer) | docTR OCR over ruled-grid cells (`code/ocr/`) |

**Why four Capital-Project-Detail parsers exist:** the same logical document is emitted with
different PDF text layers across years. `parse_capital.py` (pypdf) works only where pypdf
happens to preserve column order; on FY20/FY22/FY23/FY24 pypdf *scrambles* the columns
(amount/budget-line/sponsor interleave), so those years use `parse_capital_detail.py`, which
reads pdfplumber's clean `extract_text()` output. FY26 and FY25 scramble under both and need
coordinate clustering (`parse_capital_fy26.py`, `parse_capital_fy25_detail.py`). All four emit
the identical FY27 schema and reconcile against the printed `TOTALS FOR <agency> (N PROJECTS)`
subtotal lines.

**Two different FY2025 §254 books — do not confuse them.** `parse_capital_fy25.py` parses the
broad *Appropriation-Changes* book (`Fiscal-2025-Capital-Changes.pdf`, ~$5.2B of all executive-
capital changes, no printed subtotals → NOT RECONCILABLE), whose output is now
`fy25_capital_changes_appropriation.csv`. `parse_capital_fy25_detail.py` parses the *Council-
additions supporting-detail book* (`Supporting-Detail-for-FY2025-...-Council-Version-24.07.17.pdf`),
the FY26/FY27 counterpart, whose output is the canonical `fy25_capital_projects.csv` and
reconciles **exactly** ($775M / 1327 projects). The Council-additions total for each agency is
≤ that agency's line in the appropriation book; 8 agencies (Aging, ACS, Health, Human Resources,
Sanitation, GSA/Resiliency-Tech, DEP, Children's Services) match to the dollar.

---

## Schedule C — per year

Invocation pattern:
```bash
.venv/bin/python code/parse_schedule_c.py <ScheduleC.pdf> \
    --outdir data/fyNN/schedule_c --prefix fyNN
```

| FY | Source PDF (`source/FYnn/`) | Reconciliation | Notes |
|---|---|---|---|
| FY16 | `fy2016-skedcf.pdf` | 24/26 exact | 1 in-source arithmetic diff (Criminal Justice −700k); 1 trailing no-block category. Awards: member attribution weak (roster=3). |
| FY17 | `FY17-Schedule-C.pdf` | 24/27 exact | Mental Health +$200 in-source; 2 trailing no-block categories. Awards: member attribution weak (roster=3, all rows `initiative_provider`). |
| FY18 | `FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf` | 24/27 exact | Children’s Services −$100k in-source; 2 trailing no-block categories. Contents page headed "Contents" (ToC-detection fix). |
| FY19 | `Fiscal-2019-Schedule-C-Final-Report.pdf` | 27/28 exact | Only trailing Youth Services (no block). Clean. |
| FY20 | `Fiscal-2020-Schedule-C-Final-Merge.pdf` | 27/28 exact | Only trailing Youth Services. Clean. |
| FY21 | `Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf` | 25/26 exact | Only trailing Youth Services. Clean. |
| FY22 | `Fiscal-2022-Schedule-C-Merge-6.30.21.pdf` | 24/26 exact | Veterans −714,500 in-source; trailing Youth. |
| FY23 | `Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf` | 26/26 exact | Perfectly clean. |
| FY24 | `Fiscal-2024-Schedule-C-Merge-Final.pdf` | 24/26 exact | Criminal Justice +52,935 in-source; trailing Youth. |
| FY08 | (earliest era) | see "Bounded / blocked" below | Distinct pre-FY09 format; deferred. |
| FY15 | `fy2015-FY15-Schedule-C-Template-Final.pdf` | **24/24 exact** | Parsed by `parse_schedule_c_fy15.py` (NOT the shared parser). See the FY2015 section below. Award/EIN-level: 652 award rows. |

### Schedule C — FY2015 (dedicated parser)

FY2015 is parsed by **`parse_schedule_c_fy15.py`**, not `parse_schedule_c.py`. The shared parser
maps the Nth summary block to the Nth ToC category (positional). FY2015's ToC leads with two
narrative sections ("FROM BUDGET RESPONSE TO ADOPTION…", "INTRODUCTION"), so positional mapping
shifts every label by two and drops the last four real categories as 0/0. The FY15 variant maps
each block to the category heading that immediately **precedes** it, which labels all 24 blocks
correctly. It reuses the shared parser's award/roster/appendix machinery unchanged (FY2015 IS a
modern award/EIN-level year, unlike FY09–FY14).

It reconciles **24/24 exact** (grand total $233,438,000). Three FY15 line-item formatting artifacts
that the shared segmenter silently drops are handled in the variant — each hand-verified to sum to
the printed category TOTAL, so they are extraction gaps, not in-source arithmetic:
- **CUNY** — an initiative whose *name* contains "Council Initiatives" (`Results Based Accountability for Council Initiatives $500,000`), which the shared parser discards as a heading;
- **HOUSING** — `$ 100,000` with a space between the `$` and the digits;
- **YOUTH AND COMMUNITY DEVELOPMENT** — `…Youth Action Build Initiative 2,100,000`, a bare comma-grouped amount with no `$`.

Four ToC entries carry no summary block: the two narrative sections above plus **BOROUGHWIDE NEEDS**
and **HEALTH SERVICES AND PREVENTION** (real categories funded without a main-body Council-Initiatives
summary). (The same three artifact classes likely explain some of the single-category "in-source"
diffs recorded for FY16–FY24; hardening the shared parser for them is a separate, regression-gated pass.)

```bash
.venv/bin/python code/parse_schedule_c_fy15.py \
    source/FY15/fy2015-FY15-Schedule-C-Template-Final.pdf \
    --outdir data/fy15/schedule_c --prefix fy15
```

The single per-category diffs above are arithmetic inconsistencies *inside the official PDFs*
(line items vs. the printed category TOTAL), the same class already documented for FY25–FY27 —
not extraction errors. "Trailing no-block category" = a ToC category (usually Youth Services)
funded only through an appendix, with no main-body Council-Initiatives summary block, so it
correctly maps to no block and shows 0/0.

---

### Schedule C — early era (FY2009–FY2014)

The FY09–FY14 Schedule C documents have NO award-level EIN tables (discretionary designations
were made post-adoption — see the Transparency Resolutions for org-level detail). They DO carry a
reconcilable per-category *initiatives summary* (`CATEGORY` → `Agency Initiative Funding` table →
`TOTAL $X`). `parse_schedule_c_legacy.py` extracts it and reconciles the row sum against the
printed TOTAL. It emits only `*_schedule_c_initiatives.csv` + `*_schedule_c_reconciliation.txt`
(no awards/appendix files — that data isn't in these documents).

```bash
.venv/bin/python code/parse_schedule_c_legacy.py <ScheduleC.pdf> \
    --outdir data/fyNN/schedule_c --prefix fyNN
```

| FY | Source PDF | Reconciliation |
|---|---|---|
| FY09 | `fy09-Schedule-C-final.pdf` | 21/22 (Health Svcs −$500k in-source) |
| FY10 | `fy_2010_sched_c_final.pdf` | **21/21 exact** |
| FY11 | `fy2011-C2011.pdf` | 18/19 (Education +$250k in-source) |
| FY12 | `fy2012-skedcfinal.pdf` | **16/16 exact** |
| FY13 | `fy2013-FY-2013-Schedule-C-Merge-Final1.pdf` | **17/17 exact** |
| FY14 | `fy2014-skedc.pdf` | **17/17 exact** |

---

## Terms & Conditions — per year

Two formats. **FY25–FY27** number each condition (`N. Agency (Code)`) → `parse_terms.py`.
**FY15–FY24** print no item numbers → `parse_terms_legacy.py` (the current parser returns 0 rows
on them). A condition can span several agency headers; like the FY25–FY27 data, that is emitted
as one row keyed to the first (primary) agency, with every header's UA lines collected. Item
numbers are synthesized in document order. T&C documents print no totals → **NOT RECONCILABLE**;
correctness is checked by counts + regression tests (`test_parse_terms_legacy.py`).

```bash
.venv/bin/python code/parse_terms_legacy.py <TermsAndConditions.pdf> \
    --outdir data/fyNN/terms --prefix fyNN
```

| FY | Source PDF | Conditions | Notes |
|---|---|---|---|
| FY15 | `fy2015-tc.pdf` | 17 | FY15/16 also print a bare sequence number per item; ignored (synthetic numbering) |
| FY16 | `fy2016-tandc.pdf` | 30 | |
| FY17 | `FY17-Terms-and-Conditions.pdf` | 30 | `2016-DOHMH-Terms-and-Conditions-Oral-Health.pdf` is a 1-agency supplement, not merged |
| FY18 | `FY18-Terms-and-Conditions.pdf` | 33 | |
| FY21 | `Fiscal-2021-Terms-and-Conditions.pdf` | 46 | |
| FY22 | `FY22-Terms-and-Conditions_FINAL.pdf` | 50 | 3 Capital Budget items |
| FY23 | `FY23-Terms-and-Conditions_FINAL_OMB-and-Council-Review-6.11.22.pdf` | 60 | |
| FY24 | `FY24-Terms-and-Conditions.pdf` | 59 | |

FY08–FY14, FY19, FY20: no standalone Terms & Conditions document exists (not published, or not
found on council.nyc.gov) → N/A.

---

## Bounded / blocked (tracked here, see status table at bottom)

- ~~Schedule C FY2009–FY2014~~ — **RESOLVED** by `parse_schedule_c_legacy.py` (initiatives-only,
  reconciled; see the early-era table above). **FY2008** remains deferred: a distinct earliest-era
  format with none of the FY09+ markers. NOTE: the main `parse_schedule_c.py` still raises on
  FY2008/FY2014-shaped input (0 categories) — those years route to the legacy parser instead.
- ~~**Schedule C FY2015**~~ — **RESOLVED** by the dedicated `parse_schedule_c_fy15.py` (adjacent-heading
  block→category mapping), which does NOT modify the shared parser. Reconciles 24/24 exact and emits
  652 EIN-anchored award rows. The three per-block "undercounts" turned out to be extraction gaps
  (a 'Council Initiatives' initiative name, a '$ 100,000' space-after-$ amount, and a bare no-$
  '2,100,000' amount), each verified to sum to the printed TOTAL. See the FY2015 section above.
- ~~Schedule C FY2018~~ — **RESOLVED**: its contents page is headed 'Contents' not
  'Table of Contents'; the ToC-detection regex now matches both. Reconciles 24/27.

---

## Transparency Resolutions — per year (FY10–FY24 + FY26)

Post-adoption discretionary designations. **NOT RECONCILABLE** in every year — these documents
print no per-chart or grand totals (the only internal check is the transfer net-out). The
`batch` mode derives each resolution's sequence number and adoption date from the filename
(`Transparency-Reso-NN-YYYY-MM-DD.pdf`), so it works for any year and any count (the old
hardcoded FY26 table and `!= 10` count assertion are gone). `-dup` files are skipped; non-PDF
resolutions (FY2013's three `.doc` files) are skipped and reported as blocked.

Invocation (union all parsed Schedule C rosters for member detection):
```bash
ROSTER=$(ls data/fy*/schedule_c/*_schedule_c_awards.csv)
.venv/bin/python code/parse_transparency_reso.py \
    --batch source/FYnn/transparency-resolutions \
    --outdir data/fyNN/transparency-resolutions --prefix fyNN --roster-csv $ROSTER
```

**Financial columns (EIN, amount, agency, date, action) are deterministic and reliable in every
year** — they come from the EIN+$ anchor. The organization / council_member / program **text**
degrades in the older years, whose PDF text layer glues adjacent words together
("ChristChurchofNewBrighton") and bleeds the column header into the first data row. Each year's
`*_reconciliation.txt` prints an **org-text confidence** band (HIGH / MODERATE / LOW) quantifying
this so the caveat travels with the data.

| FY | resolutions parsed | org-text confidence | Notes |
|---|---|---|---|
| FY10 | 12 | LOW | glued-word + header-bleed artifacts (~22%); join on EIN |
| FY11 | 10 | LOW | ~25% |
| FY12 | 7 (of 8; 1 `-dup` skipped) | LOW | ~19% |
| FY13 | 9 (of 12; **3 `.doc` BLOCKED**: resos 07/10/11) | LOW | ~25% |
| FY14 | 3 | MODERATE | small doc, minor header bleed |
| FY15 | 12 | HIGH | clean |
| FY16 | 13 | MODERATE | ~2–3% artifacts |
| FY17 | 13 | HIGH | clean |
| FY18 | 12 | HIGH | clean |
| FY19 | 11 | HIGH | 3 orphaned org names of 7090 |
| FY20 | 8 | HIGH | clean |
| FY21 | 8 | HIGH | clean |
| FY22 | 14 | HIGH | clean (matches brief's viBe/DCLA spot-check) |
| FY23 | 14 | HIGH | clean |
| FY24 | 9 | HIGH | clean |
| FY09 | 8 | LOW | Scans, no text layer → **OCR pipeline**, `parse_transparency_reso_fy09.py`; 2620 rows, 0/1 printed chart totals exact (reso 07 mismatch) |

---

## OCR pipeline — FY2009 Transparency Resolutions

The eight FY2009 documents (`source/FY09/transparency-resolutions/`, 332 pages) are 300-dpi
bitonal Xerox scans with **no text layer at all**, so `parse_transparency_reso.py` cannot
touch them. They are handled by `parse_transparency_reso_fy09.py`, which drives the staged
OCR pipeline in `code/ocr/`.

**⚠ FY2009 figures are MODEL-READ.** Every other fiscal year in this repo is extracted
deterministically from the document's own text layer; FY2009 has no text layer to extract.
See "Trust model" below for what is checked and how uncertainty is surfaced.

### Why the documents need a pipeline, not a parser

- **Rotation varies page to page.** The chart pages are landscape tables printed onto
  portrait sheets, and the direction is not constant *within a single file* —
  Transparency-Reso-01's Chart 1 page reads top-down on the left edge, Transparency-Reso-07's
  Chart 3 page reads bottom-up. A per-file constant would be wrong.
- **The tables are fully ruled.** Every cell has a printed border, so cell boundaries are
  read off the ink by morphology and column identity comes from *geometry*. This is why the
  FY09 output should be cleaner than FY10–FY13, whose text layer glues words together and
  bleeds the header into the first data row.
- **Column layout varies by chart.** Long form (Charts 1–3): `Member | Organization |
  EIN Number | Agency | Amount | Agy # | U/A | Fiscal Conduit/Sponsoring Organization |
  Fiscal Conduit EIN | * | Status`. Short form (Charts 4+, per-initiative): `Organization |
  EIN Number | Agency | Amount | Agy # | U/A | *`. Columns are resolved by fuzzy-matching
  the header row; **an unmapped required column skips the page for review rather than
  assigning values positionally.**

### Environment (separate from the other parsers)

The OCR stack pulls in torch (~1–2 GB) and is deliberately not in `requirements.txt`:

```bash
python3 -m venv .venv-ocr
.venv-ocr/bin/pip install -r code/requirements.txt -r code/requirements-ocr.txt
```

### Stages

| stage | module | does |
|---|---|---|
| `render` | `ocr/render.py` | PDF page → 300-dpi grayscale PNG (1:1 with the scan) |
| `orient` | `ocr/orient.py` | 90° multiple (projection axis + docTR confidence tiebreak) then deskew off the printed rules |
| `classify` | `ocr/classify.py` | narrative / EXHIBIT divider / chart, plus the `CHART n: Title` caption |
| `grid` | `ocr/grid.py` | ruled lines → cell rectangles (OpenCV morphology, no ML) |
| `ocr` | `ocr/recognize.py` | docTR words → per-cell text + confidence; targeted re-OCR of failing numeric cells |
| `assemble` | `ocr/assemble.py` | cells → the standard 16-column schema, validators, review queue |
| `report` | `ocr/report.py` | printed-total reconciliation + OCR quality band |

Artifacts are cached under `build/ocr/<pdf-stem>/` (gitignored): `raw/`, `upright/`,
`orient.json`, `grid/`, `debug/`, `pages.csv`. Any stage can be re-run in isolation.

### Invocation

```bash
ROSTER=$(ls data/fy*/schedule_c/*_schedule_c_awards.csv)
.venv-ocr/bin/python code/parse_transparency_reso_fy09.py \
    --batch source/FY09/transparency-resolutions \
    --outdir data/fy09/transparency-resolutions --prefix fy09 --roster-csv $ROSTER
```

Iteration flags: `--stage <name>` (run up to and including a stage), `--only
Transparency-Reso-01`, `--pages 9-12`, `--debug` (writes grid-overlay PNGs — the fastest way
to see a grid-detection failure), `--force`, `--min-conf`, `--no-engine` (stages 0–3 with no
docTR at all).

### Trust model

FY2009 is the only year whose numbers are model-read, so it carries extra checks:

1. **Printed chart totals.** Unlike FY10–FY24, several FY09 charts print a total (e.g.
   `$500,000.00` on the Veterans Resource Center chart, `$0.00` on a net-zero transfer
   chart). Those are checked **exactly**, and are the strongest evidence the OCR read the
   dollar figures correctly. Charts with no printed total remain `NOT RECONCILABLE`.
2. **Shape checks** on every EIN (`##-#######`), amount (`$#,###.##`, parenthesised =
   rescission), and `Agy #` / `U/A` (3 digits).
3. **An agency-code dictionary** built from the already-parsed FY10–FY27 transparency CSVs —
   so an OCR'd `DYGD` fails where a regex over uppercase letters would pass.
4. **No quiet repair.** Only characters that cannot occur in the target grammar and have a
   single reading (bracket variants, whitespace) are folded. Letter/digit confusions
   (`O`/`0`, `S`/`$`) are **never** guessed: the cell is left unparsed, flagged in the
   `flags` column with an `ocr:*` code, and queued in
   `fy09_transparency_needs_review.csv` with a crop of the original pixels.
5. **Cross-cell bbox disambiguation.** Full-page word detection occasionally draws one
   bounding box that unambiguously covers ink in two adjacent ruled cells (a value straddling
   a column or row rule), and the naive centroid-based cell assignment would silently hand
   the whole box's text to just one of them. `recognize.find_cell_span_conflicts` catches
   this geometrically (a word with ≥30% of its own area inside each of two-or-more cells,
   checked only against its centroid-cell's neighbours) and, for every cell it implicates,
   re-reads that cell independently from its own cropped rectangle — the same crop-and-
   upscale fallback used for failing numeric cells, just triggered by geometry instead of a
   validator failure. The corrected cell is flagged `ocr:cellspan` so the correction stays
   visible in `flags` and in the review queue rather than silently overwriting the row.

### Outputs

```
data/fy09/transparency-resolutions/
  resoNN_transparency_designations.csv     standard 16-column schema
  fy09_transparency_all.csv                combined
  fy09_transparency_fiscal_conduits.csv    FY09-only Fiscal Conduit / Status columns (sidecar)
  fy09_transparency_needs_review.csv       human-review queue + review-crops/
  fy09_transparency_reconciliation.txt     printed-total checks + OCR quality band
```

The `Fiscal Conduit` and `Status` columns are FY09-only and cannot go in the shared schema
(`validate_data.py` treats an extra column as a hard failure), so they live in the sidecar,
joined back on `(resolution, chart, ein)` — the same pattern as
`fy25_capital_noncity_by_entity.csv`.

### `fy09_transparency_fiscal_conduits.csv` — what it captures

Columns: `resolution, chart, ein, conduit_organization, conduit_ein, status`.

Only the FY09 long-form charts (Charts 1–3) print these two extra fields per row:

- **Fiscal Conduit/Sponsoring Organization** (+ its EIN) — filled in when a designation is paid
  through an intermediary fiscal sponsor rather than directly to the recipient organization (e.g.
  a small or unincorporated group that can't receive funds itself, routed through a 501(c)(3)
  fiscal conduit). Most rows (1746/1907, ~92%) have no conduit — the award went straight to the
  named organization; the remaining ~161 name a conduit.
- **Status** — a per-award PQL (pre-qualification) clearance state as printed on the chart:
  `Cleared`, `Approved`, `Application Pending`, `Missing PQL Application`, `Application Incomplete
  at Deadline`, `Denied`, `Redesignated`, `Government Entity` (city agencies are exempt from PQL),
  `S10K- PQL Not Required` (awards under the $10K PQL threshold), etc. This is the same status
  concept documented for the RnD expense-funding-disclosure spreadsheets in the README, but here
  it's read directly off FY09's printed table rather than sourced from a modern clearance system.

Because `status` is OCR'd off a 300-dpi scan like every other FY09 field, it carries the same
character-level noise as the rest of the pipeline — dozens of near-duplicate spellings of the same
value (`Cleared`/`Cieared`/`Çleared`, `Government Entity`/`Govemment Entity`/`Governmental Entity`,
several `S10K...PQL Not Required` variants). Treat `status` as informational / exploratory text,
not a clean categorical, unless you first normalize it.

Row count: 1907 (one row per FY09 long-form chart line that carries a conduit/status cell; short-
form charts 4+ have neither column and are absent from this file).

**Status: pipeline run (post cross-bbox-disambiguation fix, `c53c71d`).** All 8 resolutions (332
pages: 124 chart, 86 divider, 121 narrative, 1 blank) produced 2620 rows (204/399/534/361/194/
138/231/42 designate and 29/14/19/56/65/182/117/35 rescind across resos 01–08). Of the single
printed chart total in the corpus, reso 07 does **not** reconcile exactly (printed $30,000 vs.
parsed $86,714, diff $116,714) — the only other check available, the FY09-wide net of all
designations/rescissions, is $56,756,635 (informational, not a check against a printed figure).
OCR quality: 19,532 cells recognized, mean confidence 0.927 (p05/p25/median 0.581/0.930/0.996)
against an 0.80 threshold; 2194/2620 rows (83.74%) carry at least one flag and 3858 cells are
queued in `fy09_transparency_needs_review.csv` for human review. Breakdown by flag: `ocr:lowconf`
1903 (72.63%), `ocr:amt` 897 (34.24%), `ocr:ein` 55 (2.10%), `ocr:agency` 29 (1.11%), `ocr:member`
3 (0.11%), `ocr:code` 1 (0.04%), `ocr:cellspan` 7 (0.27%, the cross-cell bbox disambiguation
re-read added in `c53c71d`). Member-cell/roster matching: 257/1339 (19.2%) — informational, since
the FY2015+ rosters used for matching don't cover every member of the 2008–09 Council.
**OCR CONFIDENCE BAND: LOW.** Overall status: NOT RECONCILABLE (no document-wide printed
total), consistent with every other Transparency-Resolution year.

---

## Capital (§254) — per year

Two document types, two schemas (see the README's "The data files" section):

**A. Capital Project Detail ("Supporting Detail Book")** — reconcilable against
`TOTALS FOR <agency> (N PROJECTS)`. Use `parse_capital_detail.py`:
```bash
ROSTER=$(ls data/fy*/schedule_c/*_schedule_c_awards.csv)
.venv/bin/python code/parse_capital_detail.py <SupportingDetailBook.pdf> \
    --outdir data/fyNN/capital --prefix fyNN --roster $ROSTER
```

| FY | Source PDF | Reconciliation |
|---|---|---|
| FY20 | `Supporting-Detail-for-the-FY-2020-Changes-...-Section-254-2.pdf` | **23/23 exact** |
| FY22 | `FY22-Sec254-Capital-Supporting-Detail-Book.pdf` | **32/32 exact** |
| FY23 | `FY23-Sec254-Capital-Supporting-Detail-Book.pdf` | **30/30 exact** |
| FY24 | `FY2024-Sec254-Supporting-Detail-Book_7.10.2023pwp-2.pdf` | **30/30 exact** |

**B. Resolution A / Appropriation Changes** — NOT RECONCILABLE (no printed subtotals). Use
`parse_capital_fy25.py`. Applies to FY17/FY21/FY23/FY24 and the broad FY25 appropriation book
(each of those years also has a type-A book except FY17/FY21, which have only this type). Status
recorded in the table below. **Note:** the FY25 appropriation output is now
`fy25_capital_changes_appropriation.csv` — it is no longer the canonical FY25 capital dataset (see
the FY25 Council-additions detail block below).

**FY19** is a third, older Capital-Project-Detail sub-format (extra community-district column, no
SPONSOR column, `-` for zero, and **no `TOTALS FOR` subtotals**) — deferred / NOT RECONCILABLE.

**FY27** is a Capital Project Detail book whose text layer pypdf preserves in reading order, so it
uses `parse_capital.py` (not `parse_capital_detail.py`). Invocation:
```bash
.venv/bin/python code/parse_capital.py \
    "source/FY27/Supporting-Detail-for-FY2027-Changes-To-the-Executive-Capital-Budget-Pursuant-to-Section-254.V4.pdf" \
    --outdir data/fy27/capital --prefix fy27 --roster data/fy*/schedule_c/*_schedule_c_awards.csv
```
Reconciliation: **24/26** (the two open DIFFs — Part I `HOUSING & DEVELOPMENT` 63/65 and
`HUMAN RESOURCES` 18/19 — are in-source line-item vs. printed-subtotal gaps, not parser errors).

The row grammar has **two code-column layouts**: CITY items carry a `CC####` budget line and a
`D####`/`DN###` sub id, with the SPONSOR glued to the front of the TITLE after the four amounts;
NON-CITY items carry an `MA####` budget line and a `0N###` sub id, and have **no council sponsor**
— the blob after the amounts is the grantee organization name in full. The `ROW` regex accepts
both code pairs. A non-city row is flagged (`_noncity`) so the sponsor-splitter leaves its title
intact rather than peeling a leading roster word (e.g. `BROOKLYN` off `BROOKLYN BALLET`).
Before this fix the `MA/0N` rows failed the `CC/D`-only regex, fell through to the agency-header
branch, were dropped as projects, and leaked a whole row's text into the `agency` field of the
CITY rows that followed (52 polluted rows; the entire Part II `CULTURAL INSTITUTIONS` block was
lost). `validate_data.py` now surfaces this class as an `agency_pollution` advisory (a digit in a
capital `agency` name). See DATA-ANOMALIES.md #12.

**FY25 (Council-additions detail book)** is the FY26/FY27 counterpart — the "Supporting Detail For
Fiscal Year 2025, Changes to the Executive Capital Budget Adopted by the City Council Pursuant to
Section 254" book (Council version). It uses `parse_capital_fy25_detail.py` (coordinate clustering;
the text layer is scrambled like FY26). Invocation:
```bash
.venv/bin/python code/parse_capital_fy25_detail.py \
    "source/FY25/Supporting-Detail-for-FY2025-Changes-To-the-Executive-Capital-Budget-Pursuant-to-Section-254-Council-Version-24.07.17.pdf" \
    --outdir data/fy25/capital --prefix fy25 --roster data/fy*/schedule_c/*_schedule_c_awards.csv
```
Reconciliation: **30/30 agency subtotals exact**, and both `TOTALS FOR ALL` grand totals tie
exactly — Part I **$775,000,000 / 1327 projects**, Part II (non-city) **$158,992,000 / 181
projects**. The book has **three** parts (FY26 had two): I. Capital Project Detail (city), II.
Non-City Capital Project Detail (a non-city subset re-listed), and III. Capital Project Detail by
Non-City Entity — an entity-grouped cross-tab of Part II with a different schema (no boro/sponsor,
per-entity `$` totals). Parts I+II go to the canonical `fy25_capital_projects.csv` (FY26/FY27
schema, directly comparable); Part III goes to the sidecar `fy25_capital_noncity_by_entity.csv`
(`organization, budget_line, fy1..fy4`) and reconciles independently — 106/106 entities to their
printed totals, summing to $158,992,000 = the Part II grand total. Two FY25 header quirks the
parser handles vs. FY26: the left code column header is `PROJECT ID` (not FY26's `SUB ID`), and the
header row therefore carries two `PROJECT` tokens (`PROJECT ID` and `PROJECT TITLE`), disambiguated
by x-position.

---

## Full status table (kept current)

Legend: RECONCILED (ratio) · EXTRACTED (parsed, not reconcilable by nature) · PARTIAL ·
NOT_RECONCILED · BLOCKED · N/A (no such document that year).

| FY | Schedule C | Terms & Conditions | Capital | Transparency Resolutions |
|---|---|---|---|---|
| FY08 | NOT_RECONCILED (older era) | N/A | BLOCKED (.doc only) | N/A (via Legistar only) |
| FY09 | RECONCILED 21/22 (init)| N/A | pending | EXTRACTED 2620 (OCR, LOW confidence, scanned) |
| FY10 | RECONCILED 21/21 (init)| N/A | pending | EXTRACTED 12 (org-text LOW) |
| FY11 | RECONCILED 18/19 (init)| N/A | pending | EXTRACTED 10 (org-text LOW) |
| FY12 | RECONCILED 16/16 (init)| N/A | BLOCKED (JBIG2 scan) | EXTRACTED 7 (org-text LOW) |
| FY13 | RECONCILED 17/17 (init)| N/A | pending | EXTRACTED 9 (3 .doc BLOCKED) |
| FY14 | RECONCILED 17/17 (init)| N/A | N/A (not published) | EXTRACTED 3 |
| FY15 | RECONCILED (24/24, fy15 parser) | EXTRACTED (17) | pending | EXTRACTED 12 |
| FY16 | RECONCILED (24/26) | EXTRACTED (30) | pending | EXTRACTED 13 |
| FY17 | RECONCILED (24/27) | EXTRACTED (30) | EXTRACTED (ResoA) | EXTRACTED 13 |
| FY18 | RECONCILED (24/27) | EXTRACTED (33) | pending (ResoA 0 blocks) | EXTRACTED 12 |
| FY19 | RECONCILED (27/28) | N/A | pending (FY19 sub-format) | EXTRACTED 11 |
| FY20 | RECONCILED (27/28) | N/A | **RECONCILED 23/23** | EXTRACTED 8 |
| FY21 | RECONCILED (25/26) | EXTRACTED (46) | EXTRACTED (ResoA) | EXTRACTED 8 |
| FY22 | RECONCILED (24/26) | EXTRACTED (50) | **RECONCILED 32/32** | EXTRACTED 14 |
| FY23 | RECONCILED (26/26) | EXTRACTED (60) | **RECONCILED 30/30** | EXTRACTED 14 |
| FY24 | RECONCILED (24/26) | EXTRACTED (59) | **RECONCILED 30/30** | EXTRACTED 9 |

_"pending" = not yet processed in this pass; updated as work proceeds._

---

## Data QA — `validate_data.py`

`code/validate_data.py` is a reusable, **stdlib-only** row-level validator over every parsed year
in `data/` (FY2009–FY2027). It complements the per-file `*_reconciliation.txt` (which checks only
category/subtotal TOTALS) with row-level and cross-file integrity: schema consistency, EIN validity +
per-year coverage %, amount sanity (incl. transparency `designate`>0 / `rescind`<0 sign rules),
fiscal-year integrity (allowing transparency's expected prior-year rows), within-file duplicate
detection, a column-bleed heuristic (suspected member-surname leakage into org/program text), and a
reconciliation roll-up parsed from every `*_reconciliation.txt`.

It exits **non-zero only on HARD failures** (schema drift, malformed row, non-numeric amount,
malformed EIN); soft advisories (zeros, sign anomalies, outliers, duplicates, bleed residuals,
coverage notes) do not gate. It writes a dated report to `data/QA-REPORT.md` and prints a summary.

```bash
.venv/bin/python code/validate_data.py                    # validate ./data, write data/QA-REPORT.md
.venv/bin/python code/validate_data.py --data-dir data --report data/QA-REPORT.md
.venv/bin/python code/validate_data.py --no-report        # stdout only
```

Current run (2026-07-28, post OCR re-run `c53c71d`): 281 files, **4 hard failures**, EIN coverage
100% on every EIN-bearing file except FY09 transparency (97.9%, 2565/2620).
Tests: `code/test_validate_data.py`.

**The 4 hard failures are a known, expected FY09-only exception, not parser bugs.** They are all
`[ein]` findings in FY09 transparency-resolutions files — malformed EIN cells (e.g. `EX124290`,
`EX212023`, an 8-digit `95369596`) from the OCR pipeline (see "OCR pipeline — FY2009
Transparency Resolutions" above). Every one of these cells is already flagged `ocr:ein` in its
row's `flags` column and queued in `fy09_transparency_needs_review.csv`; the pipeline is working
as documented (trust-model rule 4: no quiet repair of letter/digit confusions). `validate_data.py`
treats a malformed EIN as HARD unconditionally — the right behavior for every other, deterministic
year, where a malformed EIN would mean a real extraction bug — and deliberately does not
special-case the `ocr:ein` flag, to keep the hard-fail guarantee simple and year-agnostic. So a
`FAIL` verdict from `validate_data.py` is *expected* whenever FY09 transparency data is included
in the run; a hard failure in any other file is not covered by this exception and should be
treated as a real bug.

Current run (2026-07-07): 272 files, **0 hard failures**, EIN coverage **100%** on every
EIN-bearing file. Tests: `code/test_validate_data.py`.

---

## Post-extraction repairs (2026-08-12/13)

**The CSVs under `data/fy*/schedule_c/` are no longer purely the parser's output.** 5,450 cells
were repaired after extraction from the Council's own expense disclosure workbooks
(`source/expense-funding-disclosure/`), joined on `(EIN, amount)`. Regenerating a year from its PDF
will therefore NOT reproduce the committed CSV, and that is expected.

Repairs touch `organization` (3,494), `initiative` (1,514), `purpose` (422) and `ein` (20). **No
amount was ever changed** — `code/verify_no_dollars_moved.py` asserts all thirteen fiscal years are
identical to their pre-repair totals.

To regenerate a year faithfully:

```bash
# 1. re-run the parser for that year, per the per-year table above
# 2. re-apply the repairs, each idempotent and each with a --dry-run:
python3 code/recover_org_names.py          # names lost to prose / absorbed text
python3 code/fix_wrong_eins.py             # a neighbour's EIN on the right row
python3 code/fix_member_bleed.py           # sponsor surname prefixed to a name
python3 code/fix_split_org_names.py        # a name split across member and organization
python3 code/fix_truncated_org_names.py    # a name dropped at its first " - "
python3 code/fill_blank_initiatives.py     # initiative_provider rows with no initiative
python3 code/fix_fy18_aging_shift.py       # FY2018 aging appendix column shift
# 3. verify:
python3 code/verify_crosswalk.py           # audit trail exact — hard fail otherwise
python3 code/verify_no_dollars_moved.py    # no fiscal year's dollars moved
python3 code/validate_data.py              # row-level QA + initiative reconciliation
```

Every repair is recorded in `data/combined/org_name_recovery_crosswalk.csv` with the column it
touched, the original value and the replacement, so any edit can be audited or reversed without
reading a diff. Rationale, method and the keys that are *not* safe: `DATA-ANOMALIES.md` §20 and §21.

**Two sidecars are additive and are NOT produced by any parser** — they hold awards the extraction
lost entirely, recovered from the disclosure workbooks and never merged into the per-year files:
`data/recovered/schedule_c_appendix_recovered.csv` (26,127) and
`data/recovered/schedule_c_absorbed_awards.csv` (442), built by
`code/build_appendix_from_disclosure.py` and `code/build_recovered_awards.py`.
