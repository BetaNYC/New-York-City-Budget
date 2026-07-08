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
| `parse_schedule_c_legacy.py` | Schedule C **initiatives** (early era, FY09-FY14) | pypdf text layer |
| `parse_terms.py` | Terms & Conditions, **numbered-item** format (FY25–FY27) | pypdf text layer |
| `parse_terms_legacy.py` | Terms & Conditions, **unnumbered-header** format (FY15–FY24) | pypdf text layer |
| `parse_capital.py` | §254 Capital Project Detail — **FY27** clean-pypdf | pypdf text layer |
| `parse_capital_fy26.py` | §254 Capital Project Detail — **FY26** (pypdf-scrambled) | pdfplumber word coordinates |
| `parse_capital_detail.py` | §254 Capital Project Detail — **FY20/FY22/FY23/FY24** ("Supporting Detail Book") | pdfplumber `extract_text()` (clean reading order) |
| `parse_capital_fy25.py` | §254 Resolution-A / Appropriation-Changes (FY25 + FY17/FY21/FY23/FY24) | pdfplumber word coordinates |
| `parse_transparency_reso.py` | Post-adoption Transparency Resolutions | pdfplumber word coordinates |

**Why three Capital-Project-Detail parsers exist:** the same logical document is emitted with
different PDF text layers across years. `parse_capital.py` (pypdf) works only where pypdf
happens to preserve column order; on FY20/FY22/FY23/FY24 pypdf *scrambles* the columns
(amount/budget-line/sponsor interleave), so those years use `parse_capital_detail.py`, which
reads pdfplumber's clean `extract_text()` output. FY26 scrambles under both and needs the
coordinate-clustering `parse_capital_fy26.py`. All three emit the identical FY27 schema and
reconcile against the printed `TOTALS FOR <agency> (N PROJECTS)` subtotal lines.

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
| FY15 | `fy2015-FY15-Schedule-C-Template-Final.pdf` | PARTIAL 21/28 | 3 categories undercount (real); best-effort, see below. |

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
- **Schedule C FY2015** — 21/28; three categories (Children's −500k, Food −100k, Senior −2.1M)
  genuinely undercount (dropped line items), beyond in-source arithmetic. Best-effort.
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
| FY09 | — | — | **BLOCKED**: all 8 PDFs are scanned images with no text layer |

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

**B. Resolution A / Appropriation Changes** — NOT RECONCILABLE (no printed subtotals; same as
FY25). Use `parse_capital_fy25.py`. Applies to FY17/FY21/FY23/FY24 (each of those years also has
a type-A book except FY17/FY21, which have only this type). Status recorded in the table below.

**FY19** is a third, older Capital-Project-Detail sub-format (extra community-district column, no
SPONSOR column, `-` for zero, and **no `TOTALS FOR` subtotals**) — deferred / NOT RECONCILABLE.

---

## Full status table (kept current)

Legend: RECONCILED (ratio) · EXTRACTED (parsed, not reconcilable by nature) · PARTIAL ·
NOT_RECONCILED · BLOCKED · N/A (no such document that year).

| FY | Schedule C | Terms & Conditions | Capital | Transparency Resolutions |
|---|---|---|---|---|
| FY08 | NOT_RECONCILED (older era) | N/A | BLOCKED (.doc only) | N/A (via Legistar only) |
| FY09 | RECONCILED 21/22 (init)| N/A | pending | BLOCKED (scanned, no text) |
| FY10 | RECONCILED 21/21 (init)| N/A | pending | EXTRACTED 12 (org-text LOW) |
| FY11 | RECONCILED 18/19 (init)| N/A | pending | EXTRACTED 10 (org-text LOW) |
| FY12 | RECONCILED 16/16 (init)| N/A | BLOCKED (JBIG2 scan) | EXTRACTED 7 (org-text LOW) |
| FY13 | RECONCILED 17/17 (init)| N/A | pending | EXTRACTED 9 (3 .doc BLOCKED) |
| FY14 | RECONCILED 17/17 (init)| N/A | N/A (not published) | EXTRACTED 3 |
| FY15 | PARTIAL (21/28) | EXTRACTED (17) | pending | EXTRACTED 12 |
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
