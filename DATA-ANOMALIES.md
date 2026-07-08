# Data Anomalies & Known Limitations

Honest catalog of every known gap, quirk, and caveat in this dataset. Nothing here is a secret failure — each item is either an intrinsic property of the source documents, a documented deferral, or a tracked open task. If you're about to draw a conclusion from this data, read the relevant entry first.

**Generated:** 2026-07-08. See also [`DATA-DICTIONARY.md`](DATA-DICTIONARY.md) (schemas) and [`code/PARSING.md`](code/PARSING.md) (per-year parse status).

---

## 1. Blocked source documents — not machine-readable → tracked in [#4](https://github.com/BetaNYC/New-York-City-Budget/issues/4)

These sources cannot be parsed by the repo's deterministic text-layer extractors and were **left unparsed rather than guessed** (the repo forbids hand transcription / LLM number-reading). They need an OCR/conversion pass — **open GitHub task [#4](https://github.com/BetaNYC/New-York-City-Budget/issues/4)**.

| Fiscal Year | Document | Why blocked |
|---|---|---|
| FY2009 | Transparency Resolutions — 8 PDFs (`source/FY09/transparency-resolutions/`) | Scanned images, no text layer |
| FY2012 | `source/FY12/fy2012-changestobudget.pdf` (Capital §254) | JBIG2 scan, no text layer |
| FY2013 | Transparency Resolutions 07, 10, 11 (`source/FY13/transparency-resolutions/*.doc`) | Legacy Word `.doc` binary, not a PDF |

## 2. FY2009–FY2014 have no organization/EIN detail → tracked in [#5](https://github.com/BetaNYC/New-York-City-Budget/issues/5)

Schedule C for **FY2009–FY2014 is initiatives-level only** (category/initiative totals). There are **no per-organization award rows and no EINs**. This is intrinsic: pre-FY2016, designations were largely made *after* adoption, so organization detail lives in the Transparency Resolutions, not the adopted Schedule C. FY2016 is the first year the adopted Schedule C carries award/EIN tables.

**Consequence:** EIN-keyed analysis — and the budget MCP's award tools — are valid **FY2016 onward only**. Reconstructing the earlier years from Transparency Resolutions + NYC Open Data is **open GitHub task [#5](https://github.com/BetaNYC/New-York-City-Budget/issues/5)**.

## 3. Low text-confidence for FY2010–FY2013 organization/program names

For FY2010–FY2013 Transparency Resolutions, the **financial columns (EIN, amount, agency, date, action) are reliable**, but the **`organization` / `member` / `program` *text* is low-confidence** — that era's PDFs have a glued text layer that runs adjacent fields together. Each affected `*_reconciliation.txt` self-reports a HIGH / MODERATE / LOW org-text confidence band. Use the EIN, not the name, as the identity key for these years.

## 4. Non-exact Schedule C reconciliation is (usually) the *source's* arithmetic

Some Schedule C years reconcile at, e.g., 24/26 or 21/22 categories rather than N/N. In the cases checked, the miss is an **in-source arithmetic inconsistency** — the PDF's own listed line items don't sum to its own printed category TOTAL. The parser faithfully captures both; they disagree in the document. This is the same class already documented for FY2025–FY2027. It is a property of the City's PDFs, not an extraction error — but each such case should be spot-verifiable against the source, and the `*_reconciliation.txt` shows the exact delta.

## 5. Deferred parses — parsed elsewhere-incomplete, not shipped wrong

| Item | Status | Why deferred |
|---|---|---|
| **FY2015 Schedule C** | Being addressed via a dedicated `parse_schedule_c_fy15.py` | Its 28 ToC categories vs 24 summary blocks break the *shared* parser's positional mapping; fixing it in the shared parser risked regressing the good FY2016–FY2027 years. A standalone FY2015 parser avoids that. (Update this entry when it lands.) |
| **Capital ResoA, FY2017 & FY2021** | Parsed but **not committed** | Use FY2025-tuned column coordinates and have **no printed subtotals to verify against** — unverifiable, so withheld rather than shipped unchecked. FY2022–2024 ResoA are redundant (their reconcilable Supporting Detail Book is committed instead). |
| **FY2019 Capital** | Not committed | Older capital sub-format with no subtotals to reconcile. |
| **FY2008 Schedule C** | Untouched | Earliest-era format; not yet attempted. (FY2008 is also the confirmed floor — nothing published before it.) |

## 6. Transparency files embed prior-year rows — filter on the column, not the filename

A `{year}_transparency_all.csv` (e.g. `fy26_transparency_all.csv`) contains rows whose `fiscal_year` column spans **several prior years**, not just the filename year — because a given year's resolutions designate money against multiple open fiscal years. **For the modern years (FY2014 onward) filter on the `fiscal_year` column**, never assume the filename bounds the contents. This is expected behavior, not corruption.

**Caveat for FY2010–FY2013 — the `fiscal_year` column is largely EMPTY (see #11).** In those years the column cannot be used as a filter; use the source-document (folder) year plus EIN instead. The MCP surfaces per-year transparency coverage by the resolution *document* year for exactly this reason.

## 7. Capital `sub_id` does not join to spending data

The §254 capital `sub_id` is an internal budget-line sub-project identifier. There is **no clean key** from it into NYC Checkbook's `contract_id` / spending records — a structural gap in the City's own data, not something this repo can bridge. Tracing a capital project from adoption to actual payment requires fuzzy matching (agency + amount + date), which this repo does not attempt.

## 8. FY2012 duplicated Transparency Resolution source — RESOLVED (not double-counted)

FY2012 shipped a duplicated source PDF, `Transparency-Reso-07-2012-02-01-dup.pdf`. **The parser skips any `-dup` file** (`parse_transparency_reso.py`, `if '-dup' in b.lower(): continue`), so only the seven real resolutions (reso01–reso07) were parsed — the duplicate PDF was **not** ingested and did **not** double-count.

The 2 duplicate rows the QA validator flags in `fy12_transparency_all.csv` are unrelated to the `-dup` file: both originate **within resolution 4**, and both are **legitimate in-source repeats** verified against the source PDF (`Transparency-Reso-04-2011-11-03.pdf`):
- Gentile / Society of the Educational Arts, Inc. (EIN 11-3210593), DYCD rescind (−$3,000): the resolution prints this line **twice** (source text lines 651 and 659).
- Muslim Women's Institute for Research and Development (EIN 80-0010627), DOHMH designate ($6,400): printed on **two consecutive lines** (784 and 785).

They were captured faithfully and **left in place (not deduped)** — the source genuinely lists them twice. FY2012 is a LOW org-text-confidence year (see #3); join on EIN, not name.

## 9. Transparency Resolutions not yet parsed for FY2025 / FY2027

FY2025's Transparency Resolution source PDFs are present in `source/FY25/` but not yet parsed into `data/`. FY2027's do not exist yet (the fiscal year is too early in its cycle). FY2026 is fully parsed (and embeds prior-year rows per #6).

## 10. Combined-awards duplicate rows — 142 legitimate in-source designations + a fixed roll-up bug

The QA validator flagged 149 duplicate full-row instances in `data/combined/all_years_awards.csv`. Investigated (2026-07-08):

- **142 are legitimate identical designations** present verbatim as fully-identical rows in the per-year `*_schedule_c_awards.csv` sources — a council member (or the summary) genuinely funding the same organization for the same amount twice under one initiative. Verified against the source Schedule C PDFs, e.g. FY2017 "Northern Manhattan Improvement Corporation" (EIN 13-2972415) $61,000 listed twice, and FY2020 "Ayala → PowerMyLearning, Inc." (EIN 13-3935309) $20,000 listed twice. These are **NOT bugs and are NOT deduped** — removing them would understate real dollars.
- **7 were a `build_combined.py` bug**, now fixed: the roll-up dropped the `purpose` column, collapsing source-distinct rows (identical org/amount, *different* stated purpose) into apparent duplicates. `purpose` is now carried into the roll-up (it always existed in the per-year files), eliminating the 7 spurious instances. Regression-guarded by `code/test_build_combined.py`.

`build_combined.py` does **not** double-stack: the roll-up row count equals the exact sum of the per-year award-file row counts (33,420). After the fix the combined file carries 142 duplicate instances, all legitimate.

## 11. FY2010–FY2013 transparency `fiscal_year` column is largely empty — filter by document year, not this column

The parser populates `fiscal_year` only when a resolution's chart header carries a spelled-out **"Fiscal YYYY"** token (`parse_transparency_reso.py`, `\bFiscal\s*(\d{4})\b`). In the older resolutions that token is usually absent, so the column is mostly blank in the early years:

| FY | empty `fiscal_year` rows | share |
|---|---|---|
| FY2010 | 1730 / 1788 | 97% |
| FY2011 | 1519 / 1545 | 98% |
| FY2012 | 549 / 932 | 59% |
| FY2013 | 426 / 1857 | 23% |
| FY2014 | 0 / 166 | 0% |

This is **genuinely unpopulated in the source, not a parse regression**: 0 empty-`fiscal_year` rows have an extractable "Fiscal YYYY" token in their chart header. Two sub-cases:
- **FY2010–FY2011** chart headers carry **no** fiscal-year designation at all (e.g. `Adult Literacy`, `AgingDiscretionary`). Nothing to extract — filling the column would be fabrication, which the repo forbids.
- **Some FY2012–FY2013** charts *do* carry an abbreviated `FY2011` / `FY 2013` token that the current "Fiscal YYYY" regex does not match. Widening the regex to the abbreviated form would populate those deterministically (not fabrication), but it touches all 15 committed transparency years and transparency has no printed totals to reconcile against, so it is left as a **bounded, regression-gated future improvement** rather than shipped in this QA pass.

**Consequence:** FY2010–FY2013 transparency data is **not safely filterable by the `fiscal_year` column**. Use the source-document (folder) fiscal year plus EIN. FY2014 onward the column is reliable. FY2010–FY2013 are also LOW org-text-confidence (#3) — join on EIN.

---

*QA methodology and per-check results live in [`data/QA-REPORT.md`](data/QA-REPORT.md). This file is the human-readable index of what to be careful about; the QA report is the machine-generated evidence.*

## 12. FY2027 capital — leaked data in the `agency` field — RESOLVED (fixed in PR #7, 2026-07-08)

**Resolved.** Previously, `data/fy27/capital/fy27_capital_projects.csv` had 52 rows with a malformed `agency` value (a mis-parsed row's text stuffed into the column, e.g. `"PV MA1002 PV 0N957 K 1,500,000 0 0 0 NOEL POINTER FOUNDATION"`). **Actual root cause** (found during the fix): FY2027's Capital Project Detail book uses two code-column layouts, and `parse_capital.py`'s `ROW` regex only accepted the city form (`CC####`/`D####`). The non-city grantee rows (`MA####`/`0N###`, no council sponsor) failed to match, were dropped as projects, and one leaked its text into the `agency` field of the following city rows. (The parser is `parse_capital.py`, not `parse_capital_detail.py` as first assumed.)

**Fix (PR #7):** the `ROW` regex now accepts both code pairs (`(?:CC|MA)` / `(?:D|0N)`) and treats `0N###`-sub-id rows as non-city (no sponsor peeled off the title). Outcome: 52 polluted rows → **0**; 30 previously-dropped non-city grantee projects recovered (1358 → 1388 rows); FY2027 reconciliation improved **23/26 → 24/26**. FY2020/FY2022–FY2026 capital are unchanged. `validate_data.py` gained an `agency_pollution` check so this class is caught going forward. A regression test in `test_parse_capital.py` locks it in.

**Residual (separate, pre-existing schedule_c defect, follow-up task filed):** ~5 FY2027 non-city rows still show a phantom sponsor from bogus `member` tokens ("The"/"Center") in the schedule_c CSVs — affects only the `sponsor` field, not `agency` or reconciliation.

## 13. Schedule C — repeated page-break header dropped whole award rows — FY2027 RESOLVED; FY2021–FY2026 data regeneration deferred

**The bug.** In the wide "with-purpose" Schedule C tables (FY2021 onward), each page repeats a column-header line. On Speaker's Initiative pages it reads `Sponsor Legal Name of Organization - Program Name Tax ID Amount Agency Purpose of Funds`; on Boroughwide Needs pages the leading word is `Delegation` instead of `Sponsor`. Because these variants begin with `Sponsor`/`Delegation` (not `Council Member` or `Legal Name…`), `parse_awards()` did not recognize them as headers, so the line was buffered and bled into the **organization** field of the *next* award. The header-junk filter in `main()` (`HJ = (… "sponsor legal" …)`) then deleted the **entire row** as if it were header noise — silently dropping a real, funded award rather than stripping the bled-in fragment.

**Concrete FY2027 case (the one that surfaced this):** Speaker's Initiative → **"Fund for the City of New York, Inc. – West Side Work Coalition", $125,000, DYCD** (source PDF p.274, EIN 13-2612524) was absent from `data/fy27/schedule_c/fy27_schedule_c_awards.csv`. This understated FCNY's FY2027 Schedule C passthrough by exactly $125,000 (36 rows / \$3,232,714 → the true **37 rows / \$3,357,714**).

**Fix.** `parse_awards()` now recognizes the repeated `Sponsor…`/`Delegation…` column-header line (signature: contains "legal name of organization" + "program name" + "amount" + "tax id"/"ein") and treats it as header noise — it flushes the prior record and clears the buffer, leaving the parse mode unchanged, so the header can no longer glue itself onto the following award. The `main()` header-junk filter is unchanged; it simply no longer sees a corrupted row to delete. Category reconciliation is untouched (the fix is in `parse_awards`, not `parse_initiatives`): FY2027 stays **25/25 exact, GRAND TOTAL \$655,764,999**. A regression test (`test_parse_schedule_c.py::test_fy27_west_side_work_coalition_survives`) locks in that the West Side row survives and that FCNY reconciles to 37 / \$3,357,714.

**FY2027 outcome (regenerated in this PR):** `fy27_schedule_c_awards.csv` recovered **33** previously-dropped real awards (6,085 → 6,118 rows; +\$4,183,380), including the FCNY row above. All recovered rows carry real organization names (spot-checked; no residual header text). `fy27_schedule_c_initiatives.csv` and the three appendix CSVs are byte-identical to before.

**Deferred — FY2021–FY2026 data NOT regenerated here.** The fix is in shared parser code, so the same class of dropped rows exists in the other wide-table years. Re-running the fixed parser recovers additional awards in every one of them (FY21 +10, FY22 +13, FY23 +24, FY24 +69, FY25 +37, FY26 +37 rows; FY16–FY20 use the older narrow format and are unaffected — 0 change). Their category reconciliations are unaffected. To keep this PR's data diff scoped to the reported FY2027 award, those years' CSVs are **left as-is pending a full-corpus re-parse + reconciliation review** — filed as a follow-up. Until then, FY2021–FY2026 Schedule C award CSVs still undercount awards by the amounts above; EIN-keyed totals for those years are low by a corresponding margin.

**Also note (unrelated, deferred):** FCNY rows still show the org as "Delegation Fund for the City of New York, Inc." — a *separate* mislabel (a `^funds?` regex in the org-name backfill treats the proper noun "Fund…" as purpose prose). That is **not** fixed here; it touches every fiscal year and is tracked separately in a funding-profiles documentation effort. The West Side row inherits the same "Delegation Fund…" label as its 36 FCNY siblings.
