# Every PDF in `source/`: condition and the QA path to structured data

**Report generated:** 2026-10-20 00:00 EDT. Prepared by BetaNYC (Noel Hidalgo), with AI
assistance.
**Last revised:** 2026-10-20 00:18 EDT — factual QA pass (10 fixes)
**Data current as of:** `source/` PDFs at `main` @ `f5740c3`; the condition survey
([`../CONDITION.md`](../CONDITION.md), `data/pdf_condition*.csv`); the three family assessments
in this folder, written 2026-10-19 23:46–23:52 EDT.
**Status:** draft. Assessment only. Nothing here changes data, the MCP, or the published docs.

This page joins the condition survey (one row per PDF, measured) with three assessments that read
the documents themselves. It answers two questions per family: what condition the PDFs are in,
and what QA it would take to make them clean structured data. The build plan they feed is
[`../PLAN.md`](../PLAN.md).

| Assessment | Covers |
|---|---|
| [`schedule-c-fy2008-fy2024.md`](schedule-c-fy2008-fy2024.md) | Schedule C, FY2008–FY2024 (FY2025–FY2027 are summarized in `PLAN.md` §2.3) |
| [`capital.md`](capital.md) | 24 capital PDFs: §254 Resolution A and supporting detail books |
| [`transparency-and-terms.md`](transparency-and-terms.md) | 187 transparency resolutions; 12 Terms and Conditions files (11 T&C documents and 1 misfiled DOHMH report) |

## The whole collection at a glance

243 PDFs, 17,852 pages. None carries a hidden OCR text layer. 224 are born-digital; 19 are
image-only scans (survey, ported from Christian Moscardi's `textlayer.py`,
BetaNYC/nyc-executive-orders).

| Family | PDFs | Condition | QA path | Verdict |
|---|---:|---|---|---|
| Schedule C FY2015–FY2027 | 13 | Born-digital, ruled award tables | Vector grid + Christian's image grid; printed totals; disclosure alignment report-only | **Build.** FY2027 first, then FY2024, FY2021 … |
| Schedule C FY2009–FY2014 | 6 | Born-digital, ruled; glued words fixable by `x_tolerance`; FY2010 rows banded by gray fill, not rules; FY2014 Aging unruled | As above, plus per-year text settings and two new structure paths | **Build after FY2015+.** These years do print award rows with EINs |
| Schedule C FY2008 | 1 | Born-digital, ruled member-item table, no EIN column, no printed total | Own no-EIN table; no independent check exists | **Last, as its own table** |
| Transparency resolutions FY2013–FY2026 | 149 | Born-digital, full cell grids | Same machinery as Schedule C; disclosure as a cross-check | **Rebuild.** The committed CSVs drop real rows |
| Transparency resolutions FY2010–FY2012 (digital) | 23 | Born-digital; glued words fixable; charts print totals | Word-gap splitting; reconcile to printed chart totals | **Rebuild** |
| Transparency resolutions FY2009–FY2012 (scans) | 15 | Image-only, 566 pages | Christian's PR #43 OCR pipeline (FY2009 done) and its extension (#44); human review queue | **Extend #43 per #44**, review-heavy |
| Terms and Conditions | 12 | Prose, one row per condition | Re-extract text; check numbering | **Small fix**, not a table build |
| Capital supporting detail | 13 | Born-digital, mostly unruled; printed `TOTALS FOR` lines | Column inference; reconcile all printed totals | **Parse PDF-only years only:** FY2011, FY2013, FY2018 (FY2015, FY2016 as checks) |
| Capital Resolution A | 11 | FY2016, FY2017 and FY2021–FY2025 born-digital (7); FY2009–FY2012 image-only (595 pages, dashed rules) | Born-digital: low priority, matches OMB 724/729. Scans: OCR + word-position columns | **Low priority;** scans only if pre-2013 history is wanted |

## What every family shares

1. **Read the borders, not the text order.** Where tables are ruled, the cell grid from the
   PDF's vector lines is primary, and Christian's `grid.py` image grid is the independent check.
   Where they disagree, a person looks.
2. **Reconcile to what the PDF prints.** Category, initiative, chart and `TOTALS FOR` lines exist
   in more years than the repo's docs say. They are the first check, before any outside source.
3. **Outside sources are cross-checks, never fillers.** Council disclosure workbooks for awards,
   OMB and NYC Open Data for capital. A value missing from a PDF stays missing.
4. **Flag the PDF's own errors; never fix them.** Examples: FY2017 Schedule C Youth prints 897
   EINs in scientific notation (`8.61E+08`); 8-digit EINs; printed values the disclosure
   records differently ($14,999 vs $15,000).
5. **Completeness needs its own check.** "One EIN per row" fails on 125 early rows with blank or
   malformed EINs. The plan's ink-coverage stage (from Christian's `vlm_ocr.py`,
   BetaNYC/nyc-executive-orders) is the general answer.

## Shared machinery the assessments add to the plan

- A page-origin offset correction (FY2020, FY2024 Schedule C).
- A column path for tables ruled horizontally only.
- Row detection from gray fill bands (FY2010 Schedule C).
- Per-year text settings for glued words (`x_tolerance` 1.0–1.5; Schedule C FY2010–FY2014,
  transparency FY2010–FY2012).
- An OCR path for dashed-rule scans, with columns from word positions (capital Resolution A
  FY2009–FY2012), since `grid.py` found no grid on those pages.

## Corrections the published record needs (flagged, none made here)

| Where | What the assessments found |
|---|---|
| `DATA-ANOMALIES.md` §2, `code/PARSING.md`, `DATA-DICTIONARY.md` | FY2009–FY2014 Schedule C do print award rows with EINs |
| `DATA-ANOMALIES.md` §19 | FY2023 Local $36,529,000 is a parser loss of two $5,000 rows, not rounding |
| `DATA-ANOMALIES.md` §23 | FY2027 Medicare Rights Center $135,000 is in the PDF (p.279); the old parser dropped it |
| `code/PARSING.md` (FY27 capital) | The "in-source gaps" are printed on p.40 and p.47; parser misses |
| `DATA-ANOMALIES.md` §26, `data/capital/README.md` | FY2018 capital supporting detail is in `source/` (1,485 projects, $575,000,000) |
| `DATA-ANOMALIES.md` §5 | FY2017, FY2019, FY2021 capital verify against structured data |
| `code/PARSING.md`, §1/§3 | Transparency: zero-row files, dropped and merged rows, truncated cents, printed totals exist |
| Transparency CSVs | FY2026 drops 173 hyphenless EINs (157 match the disclosure) |
| Terms and Conditions CSVs | 393 words split mid-word |

Each assessment lists its corrections with section numbers and evidence; the §23 item is from
`../PLAN.md` §2.3.

## Recommended order

1. **Schedule C FY2027** (prototype done, image check done), then FY2024 → FY2021 → FY2022,
   FY2023 → FY2020 → FY2019, FY2018, FY2016, FY2015 → FY2017 → FY2025, FY2026.
2. **Transparency resolutions FY2013–FY2026** on the same machinery.
3. **Capital FY2018, FY2013, FY2011 supporting detail** (PDF-only, born-digital, reconcile).
4. **Schedule C FY2011** as the pilot for the early eras, then FY2009, FY2012, FY2013, FY2014,
   FY2010, FY2008.
5. **Transparency FY2010–FY2012**, digital then scans (#44, with Christian).
6. **Terms and Conditions** re-extract.
7. **Capital scans FY2009–FY2012**, only if pre-2013 capital history is wanted.

## Effort (estimates from the assessments, not measured)

| Work | Estimate |
|---|---|
| Shared build (plan stages 0–11, review tool) | 13–18 days, including FY2025–FY2027 |
| Schedule C FY2008–FY2024, year-specific | 40–53 days |
| Transparency resolutions, all groups | about 11–16 days including review |
| Capital PDF-only born-digital years | about 1 week |
| Capital scans | 2–3 weeks |
| Terms and Conditions | about 1 day |

## Open decisions

1. Where clean PDF-derived data lives, given 2.0 retired PDF data from the MCP. Recommendation:
   its own research dataset per family, served nowhere until every hard check passes for a year.
2. Whether to correct the published record now (table above) or with each year's build.
   Recommendation: one docs PR now for the factual corrections, since they change what readers
   believe today.
3. Questions for the PR #43 author: land #43 first; ask about #44, chart-title reading and
   wider total detection. These are public, so they wait for a maintainer decision.
