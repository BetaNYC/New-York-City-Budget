# Draft #102 / #246 issue-log comments: FY2027 transparency resolutions (NOT posted)

**Written:** 2026-11-12. One block per problem, in the order found.

---

**Problem:** No FY2027 transparency resolutions in the repo, and no known way to download them.
**Where:** `source/FY27/`; #246
**Found by:** #246 (2026-08-14: Legistar detail URLs said "Invalid parameters!", the Web API 403)
**Tried:** the Web API's matter ids in website URLs (fails: the two number matters differently).
**Fix:** search the website, open the matter with the website's own ID/GUID, download the
attachments (`View.ashx?M=F&ID=..&GUID=..`) with plain curl. Recorded in `source/FY27/README.md`
with the URLs and sha256. Noel's four uploads equal fresh downloads byte for byte.
**Status:** fixed

---

**Problem:** The charts PDFs print no resolution text, so the fiscal-year check (T12) failed on
152 charts and "Charts 1 through N" could not be tied.
**Where:** all 4 PDFs, p.1
**Found by:** T12.fiscal_year, first run
**Tried:** —
**Fix:** each matter's "Res. No." Word file is the resolution text. Kept beside the PDF; the
config names it with its sha256 and the reader reads its paragraphs (stdlib zip + XML). It names
Fiscal 2025-2027 (Reso 02: 2026-2027) and Charts 1 through 38 / 40 / 49 / 28, which tie.
**Status:** fixed

---

**Problem:** The PDF condition survey had no rows for the new PDFs (T2 failed).
**Where:** `data/pdf_condition.csv`, `data/pdf_condition_pages.csv`
**Found by:** T2.triage
**Fix:** re-ran `code/pdf_condition.py`, kept only the 4 new PDFs' rows (227 pages, all pass the
text-layer gate). The re-run also lists GPP files added since the last survey; those are left for
their own PR.
**Status:** fixed

---

**Problem:** A caption repeated on the next page without "(continued)".
**Where:** Reso 03 p.9, Reso 04 p.9 (chart #6)
**Found by:** T3.charts
**Fix:** named exceptions `T3.continued_missing`, as FY2022. Review items #6-7.
**Status:** flagged in data

---

**Problem:** One more EIN-shaped word on a page than rows with an EIN.
**Where:** Reso 04 p.13, chart #8 CASA, Restler, $20,000
**Found by:** T5.anchors
**Tried:** looked at the page: the Organization cell prints "113271472 - Urban Assembly Institute
…", an EIN for a name. Its EIN cell, 11-3271472, is Noel Pointer Foundation's in Reso 01 p.21.
**Fix:** new named exception `T5.ein_in_text` (page and word; passes only if a row there prints
the word in its organization). Row kept as printed; critical review item #1.
**Status:** flagged in data (needs_info suggested)

---

**Problem:** Three charts print no "- Fiscal YYYY".
**Where:** Reso 01 pp.37, 40; Reso 02 p.29
**Found by:** T12.fiscal_year (warn)
**Fix:** none; `budget_fiscal_year` blank, as printed. Known issues with context, review #3-5.
**Status:** flagged in data
