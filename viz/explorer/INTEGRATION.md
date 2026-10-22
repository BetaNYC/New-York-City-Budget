---
title: How reviewed PDF data reaches the explorer and the MCP
created: 2026-10-20
type: plan
status: draft
tags: [viz, explorer, mcp, pdf-review, fy2027]
---

# How reviewed PDF data reaches the explorer and the MCP

**Report generated:** 2026-10-20 22:30 · **Data current as of:** PR #122 (`feature/fy27-capital-terms-review`),
`feature/fy27-schedule-c-review` in progress, explorer `07e276a`.

The explorer's rule from `PLAN.md` stands: **one loader.** PDF-derived tables enter
`mcp/scripts/build-index.mjs`, so the MCP and the explorer get them together, and the parity test
covers them. Nothing reads `research/` at build time.

## 1. The row contract (every PDF-derived table)

Each review session already emits most of this (PR #122 does). These columns are required, with
these names, so one viewer and one loader serve every year and every PDF family:

| Column | Meaning |
|---|---|
| `fiscal_year` | Integer, e.g. 2027 |
| `source_pdf` | Repo path, e.g. `source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf` |
| `pdf_sha256` | Hash of that file (ties the row to the exact bytes) |
| `pdf_page` | 1-based PDF page, not the printed page label |
| `bbox_pt` | Row box in PDF points, `x0,top,x1,bottom` on the unrotated page, for highlighting |
| `review_id` | Blank, or the id of the row's entry in the review CSV |
| `flags` | `;`-joined check ids, blank when clean |

Values stay **as printed** (`*_raw` columns optional, kept beside any normalized column).

## 2. Where reviewed data lives

`research/<date>-fy27-.../data/` is a working area. A year's tables are **promoted** to
`data/fyNN/pdf/<family>/` (e.g. `data/fy27/pdf/capital_sd/`, `data/fy27/pdf/terms/`,
`data/fy27/pdf/schedule_c/`) by a separate small PR, with:

- the build script that regenerates them, in `code/`, with tests;
- a row in **`data/pdf_years.csv`** (new; same idea as `data/disclosure_years.csv`):
  `fiscal_year, family, source_pdf, pdf_sha256, issue, status, rows, flagged, printed_totals_tied, note`.
  `status` is `reviewed` (checks pass, flags listed, Noel has not signed off) or `closed`
  (the year's issue is closed).

The old PDF-derived files in `data/fyNN/schedule_c/`, `terms/`, `capital/` (moved unchanged to
`data/retired/fyNN/` once a year is redone: `data/retired/README.md`) stay out of the MCP, as since 2.0.

## 3. What the loader does

`build-index.mjs` reads `data/pdf_years.csv` and loads each listed family into its own table
(`pdf_schedule_c`, `pdf_capital_sd`, `pdf_capital_sd_orgs`, `pdf_terms`, `pdf_terms_units`),
carrying `status`. Then:

- **MCP:** serves only `status = closed` rows. A `reviewed` year is invisible to MCP tools.
- **Explorer:** an env flag at build time. The public deploy (`deploy-viz.yml`) builds with
  `closed` only. A local or demo build (`npm run data -- --include-reviewed`) adds `reviewed`
  rows, and every such row, page, and chart shows a **"checked, review in progress"** label.
- **Parity test:** extends to every `pdf_*` table, per status.

## 4. What the explorer shows

- **Source viewer.** Every PDF-derived row opens its page in pdf.js with `bbox_pt` highlighted
  (nyc-eo-explorer's `PdfViewer`). PDFs are read from GitHub pinned to the build commit, like the
  spreadsheets (FY27: 8.5 + 0.7 + 0.2 MB; all PDFs 242 MB, so never copied into Pages).
- **Schedule C (FY27):** joins the Awards view as a second source beside the disclosure
  spreadsheet, matched on (EIN, amount). The view shows match / PDF-only / spreadsheet-only.
- **Capital §254:** Part I enriches the existing Capital view, matched on `sub_id` +
  `budget_line` (1,215 of 1,215 amounts already match the Council workbook): adds per-member
  sponsors (`SANCHEZ J.` / `SANCHEZ P.`), FY2028–FY2030 columns, and the p.61 summary. Part III
  becomes an **Organizations** view (109 organizations, 127 lines).
- **Terms & Conditions:** a new view: 75 conditions by agency and unit of appropriation, with
  report deadlines. Text only, no dollars.
- **Review flags** render as a badge on the row with the note from the review CSV.

## 5. Order of work

1. Explorer PR from `feature/budget-explorer` (v1, structured data only). Open now.
2. PR #122 stays as the review record (research/ + `code/review_*.py`).
3. **Promotion PR** per family: `data/fy27/pdf/<family>/` + `data/pdf_years.csv` row, status
   `reviewed`. Capital + Terms first (PR #122 work is done); Schedule C when its session lands.
4. **Loader PR:** `build-index.mjs` + parity tests + explorer views for `pdf_*`, built on 1 and 3.
5. **Friday demo:** local build with `--include-reviewed`. Public site unchanged.
6. When #102 closes: flip FY27 rows to `closed` in `pdf_years.csv`; they reach the MCP and the
   public site through the normal deploy.

## Open for Noel

- Sign-off on `REVIEW.md` items (PR #122) moves Capital + Terms from `reviewed` to `closed`.
- The three Council Finance questions (MA lines, `E CC0598`, `E CC1245`, rescindments) do not
  block `reviewed`; they are flags.
