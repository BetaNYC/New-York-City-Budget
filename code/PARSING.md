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
| FY19 | `Fiscal-2019-Schedule-C-Final-Report.pdf` | 27/28 exact | Only trailing Youth Services (no block). Clean. |
| FY20 | `Fiscal-2020-Schedule-C-Final-Merge.pdf` | 27/28 exact | Only trailing Youth Services. Clean. |
| FY21 | `Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf` | 25/26 exact | Only trailing Youth Services. Clean. |
| FY22 | `Fiscal-2022-Schedule-C-Merge-6.30.21.pdf` | 24/26 exact | Veterans −714,500 in-source; trailing Youth. |
| FY23 | `Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf` | 26/26 exact | Perfectly clean. |
| FY24 | `Fiscal-2024-Schedule-C-Merge-Final.pdf` | 24/26 exact | Criminal Justice +52,935 in-source; trailing Youth. |
| FY08–FY15, FY18 | (older-era / ToC-detection) | see "Bounded / blocked" below | Not yet reconciled by the current parser. |

The single per-category diffs above are arithmetic inconsistencies *inside the official PDFs*
(line items vs. the printed category TOTAL), the same class already documented for FY25–FY27 —
not extraction errors. "Trailing no-block category" = a ToC category (usually Youth Services)
funded only through an appendix, with no main-body Council-Initiatives summary block, so it
correctly maps to no block and shows 0/0.

---

## Bounded / blocked (tracked here, see status table at bottom)

- **Schedule C FY2008–FY2014** — older document era; the parser finds 0 summary blocks (the
  `Agency Initiative Amount` table marker and ToC shape differ). FY2014 additionally crashed
  the reconciliation writer on a `None` page index (guarded). Bounded-effort target.
- **Schedule C FY2015** — 21/28; three categories (Children's −500k, Food −100k, Senior −2.1M)
  genuinely undercount (dropped line items), beyond in-source arithmetic. Best-effort.
- **Schedule C FY2018** — body parses (25 summary blocks) but ToC detection returns 0
  categories, so blocks can't be labeled. A ToC-detection fix should recover it.

_Detailed status table lives at the end of this file and is kept current as work proceeds._
