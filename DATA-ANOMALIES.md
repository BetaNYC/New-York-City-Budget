# Data Anomalies & Known Limitations

Honest catalog of every known gap, quirk, and caveat in this dataset. Nothing here is a secret failure — each item is either an intrinsic property of the source documents, a documented deferral, or a tracked open task. If you're about to draw a conclusion from this data, read the relevant entry first.

> **2.0 (2026-10-14): PDF-derived data is retired.** Entries about Schedule C, Terms &
> Conditions, §254 capital, transparency resolutions, `data/combined/` and `data/recovered/`
> describe files kept in the repository as a historical record. They are not served by
> `@betanyc/nyc-budget-mcp` 2.0 or shown on the Pages site's front page (`viz/legacy.html` keeps
> the old explorer online, frozen as of 2026-10-16, under a "do not cite" banner). Where an entry says "the MCP" serves or indexes those files, it
> describes 1.x. The structured datasets are covered by §22–§26.

> **Corrections, 2026-10-20.** A re-read of the source PDFs (details: PR #98, open; the §23
> note carries its own evidence) found wrong claims in this file, `code/PARSING.md`,
> `DATA-DICTIONARY.md`, `README.md` and `data/capital/README.md`, most of them reading a
> parser's misses as gaps in what the City printed. The first four are corrected in place, each
> with a dated note. `data/capital/README.md` is left unchanged on purpose, because any edit
> under `data/capital/` triggers the release version guard; its FY2018 line is corrected in §26.
> Corrected entries: §1 (FY2009 and FY2010–FY2012
> transparency), §2 (FY2009–FY2014 Schedule C print award rows with EINs; FY2008 prints member
> items), §3 (transparency rows dropped, merged and cents truncated), §5 (FY2008 Schedule C;
> FY2017, FY2019 and FY2021 capital verify; FY2011 capital file), §19 (FY2023 Local is a parser
> loss), §23 (FY2027 Medicare Rights Center is printed), §26 (an FY2018 capital PDF is in
> `source/`), and in `code/PARSING.md` the FY2027 capital "in-source gaps", the transparency
> totals and the Terms and Conditions text (about 393 mid-word splits). FY2010–FY2012
> transparency charts also print totals, so §28's "FY2009 is the *only* Transparency-Resolution
> year whose charts print totals at all" is too narrow; §28 is left as its author wrote it. No
> data or code changed, so some copies of the old claims remain until the parsers are revised
> (issue #5) or the files are next regenerated: `data/capital/RECONCILIATION.md` ("FY2018 is in
> no source found"); the docstrings and printed messages in `code/parse_schedule_c_legacy.py`
> (no award-level EIN tables), `code/parse_transparency_reso.py` (no printed totals) and
> `code/build_combined.py`; and the generated `data/QA-REPORT.md` and
> `*_transparency_reconciliation.txt` files ("no printed totals" for FY2010–FY2012).

**Generated:** 2026-07-08. See also [`DATA-DICTIONARY.md`](DATA-DICTIONARY.md) (schemas) and [`code/PARSING.md`](code/PARSING.md) (per-year parse status).

---

## 1. Blocked source documents — not machine-readable → tracked in [#4](https://github.com/BetaNYC/New-York-City-Budget/issues/4)

These sources cannot be parsed by the repo's deterministic text-layer extractors and were **left unparsed rather than guessed** (the repo forbids hand transcription / LLM number-reading). They need an OCR/conversion pass — **open GitHub task [#4](https://github.com/BetaNYC/New-York-City-Budget/issues/4)**.

| Fiscal Year | Document | Why blocked |
|---|---|---|
| FY2009 | Transparency Resolutions — 8 PDFs (`source/FY09/transparency-resolutions/`) | Scanned images, no text layer. **No longer blocked:** read by OCR since PR #43 (§28). |
| FY2010–FY2012 | Transparency Resolutions — 7 scanned PDFs, 234 pages: FY2010 Reso 02–04, FY2011 Reso 08–10, FY2012 Reso 02 | Scans, no text layer. The text-layer parser runs on them and emits 0 rows. |
| FY2012 | `source/FY12/fy2012-changestobudget.pdf` (Capital §254) | JBIG2 scan, no text layer |
| FY2013 | Transparency Resolutions 07, 10, 11 (`source/FY13/transparency-resolutions/*.doc`) | Legacy Word `.doc` binary, not a PDF. They hold the Finance Committee report text only, no designation charts (0 EINs), so converting them recovers no rows. |

**Corrected 2026-10-20:** earlier text listed FY2009 as blocked, omitted the seven FY2010–FY2012
scans (counted as "parsed" in `code/PARSING.md` although they produce no rows), and implied the
FY2013 `.doc` files hold designations. Two more files produce no rows for a different reason:
FY2010 Reso 01 is a 6-page Fiscal 2009 resolution whose exhibits are missing, and FY2013 Reso 09
is a Finance Division report on the SoHo Business Improvement District, not a transparency
resolution. Evidence: page text and text-layer character counts of each file (details: PR #98).

## 2. FY2008–FY2014 Schedule C award rows were never extracted (the PDFs print them) → tracked in [#5](https://github.com/BetaNYC/New-York-City-Budget/issues/5)

The repo's Schedule C files for **FY2009–FY2014 are initiatives-level only** (category/initiative totals, from `parse_schedule_c_legacy.py`). The PDFs print more than that. FY2009–FY2014 print per-organization award rows with EINs: the award table header on FY2010 p.61 reads `Member | Sponsor | Legal Name of Organization | EIN | * | Amount | Agency | Purpose of Funds | Fiscal Conduit Name | FC EIN`, and each year prints about 3,900–4,700 award rows with an EIN. A prototype parse (details: PR #98) counts the EIN-shaped words in the award-EIN column, which match the drawn table rows that carry an EIN one for one: 3,859 / 3,994 / 4,139 / 4,331 / 4,553 / 4,726 (FY2009–FY2014; FY2014's figure includes 533 Aging rows on unruled pages, and FY2010's banded tables are counted by column only). These are counts from a prototype, not extracted data: none of these rows is in the repo yet, and rows printed without an EIN are not counted. FY2008 (`source/FY08/schedule_c_rvs_2008.pdf`, Appendix E, pp.36–123) prints 1,674 member-item rows totaling $36,399,802, with no EIN column. The old parsers extracted none of these rows.

**Corrected 2026-10-20:** earlier text said FY2009–FY2014 have "no per-organization award rows and no EINs" because designations were "largely made *after* adoption", and that FY2016 is the first year the adopted Schedule C carries award/EIN tables. The PDFs show award rows with EINs in every one of those years (evidence above; details: PR #98). The old parser's output is unchanged.

**Consequence:** EIN-keyed analysis of the repo's Schedule C files — and the budget MCP's 1.x award tools, removed in 2.0 — covers **FY2015 onward only**, because no award file exists before FY2015. That is a limit of the extraction, not of the source. (**Corrected 2026-10-20:** this line said "FY2016 onward"; FY2015 has an award file, from `parse_schedule_c_fy15.py`.) Extracting the FY2008–FY2014 award rows from the PDFs themselves, or reconstructing those years from Transparency Resolutions + NYC Open Data, is **open GitHub task [#5](https://github.com/BetaNYC/New-York-City-Budget/issues/5)**.

## 3. Low text-confidence for FY2010–FY2013 organization/program names

For FY2010–FY2013 Transparency Resolutions, the **financial columns (EIN, amount, agency, date, action) are reliable**, but the **`organization` / `member` / `program` *text* is low-confidence** — that era's PDFs have a glued text layer that runs adjacent fields together. Each affected `*_reconciliation.txt` self-reports a HIGH / MODERATE / LOW org-text confidence band. Use the EIN, not the name, as the identity key for these years.

**Corrected 2026-10-20:** "reliable" holds for the values on rows the parser emitted, not for completeness. Rows go missing in four ways (details: PR #98):
- **EINs printed without a hyphen are dropped**, because the parser's anchor requires `NN-NNNNNNN`. FY2026 prints 173 such rows, 157 positive and 16 rescissions (e.g. FY2026 Reso 02 p.27, `131641068`, $20,000); all 157 positive designations match the FY2026 Council disclosure on (EIN, amount).
- **Rows with no printed EIN are dropped** (e.g. FY2013 Reso 01 p.17, Friends of Vesuvio Playground, ($3,500.00)).
- **Rows are merged into their neighbor** in FY2013 Reso 01: 77 of its 587 committed rows carry a second EIN inside `organization`, and the absorbed row's own amount is lost (e.g. p.20, Working Today Inc. `13-3858323` $100,000.00, survives only inside the Paraprofessional Healthcare Institute row).
- **Cents are truncated in FY2010–FY2012**: the PDFs print amounts with cents (FY2010 Reso 06 p.28, `$36,369.14`), and every committed amount in those years is a whole number (337 rows lose their cents; `$18,606.94` is committed as `18606`).

Plus the zero-row files in §1. The old parser's output is unchanged.

## 4. Non-exact Schedule C reconciliation is (usually) the *source's* arithmetic

Some Schedule C years reconcile at, e.g., 24/26 or 21/22 categories rather than N/N. In the cases checked, the miss is an **in-source arithmetic inconsistency** — the PDF's own listed line items don't sum to its own printed category TOTAL. The parser faithfully captures both; they disagree in the document. This is the same class already documented for FY2025–FY2027. It is a property of the City's PDFs, not an extraction error — but each such case should be spot-verifiable against the source, and the `*_reconciliation.txt` shows the exact delta.

## 5. Deferred parses — parsed elsewhere-incomplete, not shipped wrong

| Item | Status | Why deferred |
|---|---|---|
| **FY2015 Schedule C** | Being addressed via a dedicated `parse_schedule_c_fy15.py` | Its 28 ToC categories vs 24 summary blocks break the *shared* parser's positional mapping; fixing it in the shared parser risked regressing the good FY2016–FY2027 years. A standalone FY2015 parser avoids that. (Update this entry when it lands.) |
| **Capital ResoA, FY2017 & FY2021** | Parsed but **not committed** | Use FY2025-tuned column coordinates and print **no subtotals**, so withheld rather than shipped unchecked. **Corrected 2026-10-20:** earlier text called them unverifiable. They verify against structured data by budget line: FY2017 192/192 against the Council's workbook; FY2021 161/161 against OMB and 161/161 against `t474-a92g` (details: PR #98). FY2022–2024 ResoA are redundant (their reconcilable Supporting Detail Book is committed instead). |
| **FY2019 Capital** | Not committed | Older capital sub-format (an Excel grid) with no printed subtotals. **Corrected 2026-10-20:** earlier text said there was nothing to reconcile; it matches `t474-a92g` on 1,628 of 1,628 non-zero amounts (details: PR #98). |
| **FY2011 Capital** | Not parsed | `source/FY11/fy2011-FY2011-Section-254-Changes.pdf` is, despite its name, the born-digital **supporting detail** book (74 pages; columns AS400 ID, budget line, borough, project title, four fiscal years). The FY2011 changes book is the scan `fy2011-fy11_changes_executive_capital_budget_adopted_by_nycc.pdf`. (Added 2026-10-20.) |
| **FY2008 Schedule C** | Not attempted | Earliest-era format. (FY2008 is also the confirmed floor — nothing published before it.) **Corrected 2026-10-20:** earlier text said "Untouched … Earliest-era format" with no description; Appendix E (pp.36–123) prints 1,674 member-item award rows, $36,399,802, without an EIN column (§2). |

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
- **Some FY2012–FY2013** charts *do* carry an abbreviated `FY2011` / `FY 2013` token that the current "Fiscal YYYY" regex does not match. Widening the regex to the abbreviated form would populate those deterministically (not fabrication), but it touches all 15 committed transparency years and transparency is not reconciled against printed totals (FY2013 onward print none; FY2010–FY2012 print totals the parser does not check), so it is left as a **bounded, regression-gated future improvement** rather than shipped in this QA pass.

**Consequence:** FY2010–FY2013 transparency data is **not safely filterable by the `fiscal_year` column**. Use the source-document (folder) fiscal year plus EIN. FY2014 onward the column is reliable. FY2010–FY2013 are also LOW org-text-confidence (#3) — join on EIN.

---

*QA methodology and per-check results live in [`data/QA-REPORT.md`](data/QA-REPORT.md). This file is the human-readable index of what to be careful about; the QA report is the machine-generated evidence.*

## 12. FY2027 capital — leaked data in the `agency` field — RESOLVED (fixed in PR #7, 2026-07-08)

**Resolved.** Previously, `data/fy27/capital/fy27_capital_projects.csv` had 52 rows with a malformed `agency` value (a mis-parsed row's text stuffed into the column, e.g. `"PV MA1002 PV 0N957 K 1,500,000 0 0 0 NOEL POINTER FOUNDATION"`). **Actual root cause** (found during the fix): FY2027's Capital Project Detail book uses two code-column layouts, and `parse_capital.py`'s `ROW` regex only accepted the city form (`CC####`/`D####`). The non-city grantee rows (`MA####`/`0N###`, no council sponsor) failed to match, were dropped as projects, and one leaked its text into the `agency` field of the following city rows. (The parser is `parse_capital.py`, not `parse_capital_detail.py` as first assumed.)

**Fix (PR #7):** the `ROW` regex now accepts both code pairs (`(?:CC|MA)` / `(?:D|0N)`) and treats `0N###`-sub-id rows as non-city (no sponsor peeled off the title). Outcome: 52 polluted rows → **0**; 30 previously-dropped non-city grantee projects recovered (1358 → 1388 rows); FY2027 reconciliation improved **23/26 → 24/26**. FY2020/FY2022–FY2026 capital are unchanged. `validate_data.py` gained an `agency_pollution` check so this class is caught going forward. A regression test in `test_parse_capital.py` locks it in.

**Residual (separate, pre-existing schedule_c defect, follow-up task filed):** ~5 FY2027 non-city rows still show a phantom sponsor from bogus `member` tokens ("The"/"Center") in the schedule_c CSVs — affects only the `sponsor` field, not `agency` or reconciliation.

## 13. Schedule C — repeated page-break header dropped whole award rows — RESOLVED (full corpus FY2016–FY2027)

**The bug.** In the wide "with-purpose" Schedule C tables (FY2021 onward), each page repeats a column-header line. On Speaker's Initiative pages it reads `Sponsor Legal Name of Organization - Program Name Tax ID Amount Agency Purpose of Funds`; on Boroughwide Needs pages the leading word is `Delegation` instead of `Sponsor`. Because these variants begin with `Sponsor`/`Delegation` (not `Council Member` or `Legal Name…`), `parse_awards()` did not recognize them as headers, so the line was buffered and bled into the **organization** field of the *next* award. The header-junk filter in `main()` (`HJ = (… "sponsor legal" …)`) then deleted the **entire row** as if it were header noise — silently dropping a real, funded award rather than stripping the bled-in fragment.

**Concrete FY2027 case (the one that surfaced this):** Speaker's Initiative → **"Fund for the City of New York, Inc. – West Side Work Coalition", $125,000, DYCD** (source PDF p.274, EIN 13-2612524) was absent from `data/fy27/schedule_c/fy27_schedule_c_awards.csv`. This understated FCNY's FY2027 Schedule C passthrough by exactly $125,000 (36 rows / \$3,232,714 → the true **37 rows / \$3,357,714**).

**Fix.** `parse_awards()` now recognizes the repeated `Sponsor…`/`Delegation…` column-header line (signature: contains "legal name of organization" + "program name" + "amount" + "tax id"/"ein") and treats it as header noise — it flushes the prior record and clears the buffer, leaving the parse mode unchanged, so the header can no longer glue itself onto the following award. The `main()` header-junk filter is unchanged; it simply no longer sees a corrupted row to delete. Category reconciliation is untouched (the fix is in `parse_awards`, not `parse_initiatives`): FY2027 stays **25/25 exact, GRAND TOTAL \$655,764,999**. A regression test (`test_parse_schedule_c.py::test_fy27_west_side_work_coalition_survives`) locks in that the West Side row survives and that FCNY reconciles to 37 / \$3,357,714.

**Full-corpus outcome (regenerated in this PR).** The fix is in shared parser code, so the same dropped-row class was recovered in every wide-table year. Per-year recovered rows:

| FY | awards before → after | recovered | reconciliation |
|---|---|---|---|
| FY2021 | 1,800 → 1,810 | +10 | 25/26 (unchanged) |
| FY2022 | 1,479 → 1,492 | +13 | 24/26 (unchanged) |
| FY2023 | 1,824 → 1,848 | +24 | 26/26 (unchanged) |
| FY2024 | 5,299 → 5,368 | +69 | 24/26 (unchanged) |
| FY2025 | 5,609 → 5,646 | +37 | 24/26 (unchanged) |
| FY2026 | 5,806 → 5,838 | +32 | 24/25 (unchanged) |
| FY2027 | 6,085 → 6,118 | +33 | 25/25 (unchanged) |

FY2016–FY2020 use the older narrow format and have no repeated wide "with-purpose" header — **0 row change**. Category reconciliation is untouched in every year (the fix is in `parse_awards`, not `parse_initiatives`); each year's `*_schedule_c_initiatives.csv` and the appendix CSVs are byte-identical to before. All recovered rows carry real organization names (100% valid EIN coverage per `validate_data.py`). **FY2026** required a companion `derive_categories` fix to be regenerable at all (§15) — its category reconciliation (24/25, GRAND TOTAL \$665,080,821) is identical to committed; only the awards recovered.

The regression test `test_parse_schedule_c.py::test_fy27_west_side_work_coalition_survives` locks in the FY2027 case (West Side row survives; FCNY reconciles to 37 / \$3,357,714).

## 14. Schedule C — "Delegation Fund for the City of New York" mislabel + org-name truncations — RESOLVED (full corpus FY2016–FY2027)

**The bug (two coupled defects).**
1. **`^funds?` misclassification.** `_poll()` (per-EIN org backfill) and `looks_purpose()` (IP-mode org-buffer filter) both began their purpose-prose regex with `funds?|finds?|funding`, which matches the *bare org word* "Fund". So the real FCNY name **"Fund for the City of New York, Inc."** (EIN 13-2612524) was misread as purpose prose. Two consequences: (a) org names that wrapped across lines were **truncated** to their tail word — ICARE's row became `Assistance` (from "…Coordination and Technical **Assistance**", FY2027 p.192) and NYCETC became `Coalition` (from "New York City Employment and Training **Coalition**", p.250); (b) the per-EIN backfill excluded the correctly-parsed FCNY rows from its "majority org" vote and then **overwrote** them with the wrong surviving string, "Delegation Fund for the City of New York, Inc.".
2. **Bled "Delegation" sponsor token.** On Boroughwide Needs pages the sponsor prints as "<Borough> Delegation"; the borough wraps to its own cell and the bare token **"Delegation"** leads the org line (`Queens` / `Delegation Alley Pond Environmental Center, Inc. …`). `build_roster` deliberately excludes the standalone token "Delegation", so it stayed glued to the org — producing not just "Delegation Fund…" but "Delegation Alley Pond…", "Delegation Apna…", and ~140 more per year.

**The fix.**
- A shared purpose-prefix helper (`_FUNDLEAD`, module level) now treats a leading singular **"Fund"/"Find" as an ORG NAME** unless it is immediately followed by a purpose verb ("Fund will be used to…"). Plural/gerund "Funds"/"Funding" remain always-purpose. This preserves "Fund for the City of New York, Inc." and "Find Aid for the Aged, Inc." while still catching "Funds will be used…", "Funding to support…", etc. Both `_poll()` and `looks_purpose()` use it. Result: truncations gone (ICARE and NYCETC render full names), and the backfill no longer overwrites correct FCNY rows.
- `parse_awards()`'s `emit()` now peels a leading bled **"Delegation"** sponsor token off the org (`^delegation\s+`), fixing the whole "Delegation X" family, not just FCNY.

**Outcome.** The string **"Delegation Fund" no longer appears in any Schedule C CSV** (all years FY2015–FY2027, including FY2026, and the combined roll-up), and no organization leads with the bled "Delegation" token. Per-year org relabelings (all verified as correct, not new mislabels): FY2021–FY2027 each drop ~120–165 "Delegation X" → "X" (FY2026's 30 "Delegation Fund…" rows → "Fund for the City of New York, Inc.", its own "Women's Fund for the City of New York, Inc." correctly preserved); FY2016 corrected 5 FCNY rows that the old backfill had mislabeled "Floating Hospital"/"Man Up"; FY2017/FY2018 cleaned mangled FCNY rows; FY2020 corrected "District 4" → "Find Aid for the Aged, Inc."; FY2019 was org-neutral. Category reconciliation is unchanged in every year. Regression tests: `test_fund_org_name_vs_purpose_prose` (both directions — org preserved, purpose still detected) and the FCNY/ICARE/NYCETC/no-leading-"Delegation" assertions in `test_fy27_west_side_work_coalition_survives`.

**Not covered here:** (a) The **borough delegation** still lands in the `member` field as "<Borough> Delegation" (e.g. "Bronx Delegation") — correct sponsor attribution, not a defect. (b) A *parallel* "Delegation" sponsor bleed exists in the **Transparency Resolutions** output (`parse_transparency_reso.py`, a different parser and much larger — ~4,100 org rows carrying a "<Borough> Delegation" fragment); it is a separate code path handled in its own PR, not here. (c) Two FY2027 rows still show purpose text as the organization (EINs 92-1532576, 93-3219755) — the pre-existing MI-mode multi-designation mangle (§12 residual class), unchanged by this PR.

## 15. Schedule C — FY2026 Table of Contents undetected (`derive_categories` heading gate) — RESOLVED

**The bug.** `derive_categories()` locates the ToC by first finding a standalone `Contents`/`Table of Contents` heading line, then reading the dotted `Name .... page` entries beneath it. FY2026's source PDF (`Fiscal-2026-Schedule-C-4.pdf`) presents its ToC on p.3 with all 25 dotted category rows **but no standalone heading line** in the `pypdf 6.14.2` text layer. The heading probe therefore returned `None`, `derive_categories()` returned an empty list, and the whole year would parse with **no category labels** and a **0/0 reconciliation**. (The committed FY2026 data had been generated by an earlier environment whose text extraction exposed the heading; it was not reproducible with the current toolchain — surfaced during the §13/§14 full-corpus re-parse.)

**The fix.** When — and only when — the heading probe finds nothing, `derive_categories()` now falls back to **dotted-entry density**: it picks the front-matter page (same ≤ 8 window) holding the most `TOC_LINE` `Name .... page` rows (requiring ≥ 5) as the ToC page, then proceeds exactly as before. Because the fallback runs *only* when the heading probe returned `None`, every year that already detects a heading is completely unaffected — verified by regenerating all years and confirming FY2016–FY2025 + FY2027 are **byte-identical** in awards, initiatives, and reconciliation; only FY2026 changed.

**Outcome.** FY2026 now derives its 25 ToC categories (matching the committed reconciliation: 24/25 exact, GRAND TOTAL \$665,080,821), which unblocked its participation in the §13/§14 full-corpus re-parse. Regression test: `test_parse_schedule_c.py::test_fy26_toc_density_fallback` (asserts FY2026 has no heading line yet recovers its categories via the fallback).

## 16. Transparency Resolutions — bled "<Borough> Delegation" sponsor in the organization field — RESOLVED


**The bug.** Boroughwide Transparency-Resolution designations are sponsored by a borough delegation, printed **"<Borough> Delegation"**. In the PDF text layer the borough word and the token "Delegation" land on the **organization** line — leading (`Bronx Delegation Afro-Latino Association…`), split around the org where the line wraps (`Staten Island Grace Foundation of New York Delegation`), or bare (`Delegation Fundacion de Ayuda`). `load_schedule_c_roster()` deliberately excludes the standalone token "Delegation", so `detect_member()` never peels it and it stayed glued to the organization. ~4,100 org values across FY2010–FY2026 carried the bled sponsor.

**The fix.** A `peel_delegation()` helper, applied in `parse()`'s row-finalization loop: it peels a `<Borough> Delegation` sponsor off the front of (or split around) the org and recovers it into `council_member`, and strips a bare leading `Delegation`. It matches **only** an explicit Delegation pattern, so a plain borough-led org name (`Manhattan Chamber of Commerce`) is never touched; the org is always cleaned, but the sponsor is written to `council_member` only when no member was already resolved. The change moves text between `council_member` and `organization` only — **row counts, EINs, amounts, and agencies are unchanged in every year** (EIN coverage stays 100%).

**Outcome.** No organization **leads** with a bled delegation sponsor in any year (verified across FY2010–FY2026). Org-field "Delegation" occurrences fell **4,176 → 175** corpus-wide; per year e.g. FY2023 523 → 1, FY2024 544 → 3, FY2026 637 → 1, FY2020 438 → 2, FY2016 325 → 29. The ~175 remaining are **mid-string** "Delegation" fragments inside heavily-abbreviated/mangled dense-chart rows (e.g. `National Sorority PHI DLTA … Queens Delegation SRV CTR`) — pre-existing layout artifacts, not the leading-sponsor bleed, and not newly introduced. Regression tests: `test_parse_transparency_reso.py::test_peel_delegation_unit` and `::test_no_delegation_bleed_in_org`.

**Note — stale committed data refreshed alongside.** Establishing a reproducibility baseline revealed the committed transparency CSVs did not reproduce from the then-current parser: its `detect_member()` already separated roster-surname members better than the committed data reflected (e.g. committed `organization="Schulman FDNY Foundation"` / empty member → parser yields member `Schulman`, org `FDNY Foundation`). The committed data predated that improvement. Regenerating for this fix therefore also refreshed those pre-existing (already-in-code) member-detection improvements; the Delegation change itself was verified in isolation (fresh unmodified-parser vs fresh fixed-parser output — only delegation-bleed rows differ).

## 17. Initiative names are not canonicalized across years — longitudinal joins fragment — RESOLVED (mechanical tier; review tier maintainer-gated)

**The anomaly.** The `initiative` string is captured verbatim from each year's source PDF, and the City spells the *same* initiative differently across years. A longitudinal join keyed on the raw `initiative` therefore splits one continuous program into multiple short-lived series — it looks funded one year and *gone* the next, when the money in fact continued under a differently-spelled label. Example: **Developmental, Psychological `&` Behavioral Health Services** is funded FY2017–FY2026, then FY2027's Schedule C spells it with the word **`and`** — a naive year-over-year view shows the initiative ending in FY2026 and a brand-new one starting in FY2027.

Scanning `data/combined/all_years_initiatives.csv` (2,598 rows, 846 distinct raw labels, FY2009–FY2027) surfaces **49 collision groups** — sets of raw spellings that denote one initiative. The affected programs represent roughly **\$0.6B in lifetime discretionary funding**. Two tiers:

| Tier | What differs | Groups | Raw labels | Dominant causes |
|---|---|---|---|---|
| **Mechanical** (high confidence, safe to auto-merge) | case, internal whitespace, `&`/`AND`, curly vs. straight apostrophe, a leading `*` footnote marker | **28** | 56 | leading `*` (14), casing (6), curly apostrophe (5), `&`/`AND` (4) |
| **Review** (needs a human eye — may over-merge) | hyphenation, Oxford comma, slash-vs-parens, dropped small words | **21** | 45 | wording / hyphenation / slash |

The largest single collision is review-tier: one hyphen (`After School` vs `After-School`) splits the **\$188M Cultural After-School Adventure (CASA)** program. The largest mechanical fragmenter by dollars is the **curly vs. straight apostrophe** (e.g. *City's First Readers*, \$55.2M), not the `&`/`AND` case that first surfaced this. The same pattern affects the `initiative` column in `all_years_awards.csv` (8 mechanical groups there, including internal double-spaces).

**The fix.** A committed, human-auditable crosswalk plus a **non-destructive** derived column — the raw `initiative` is never altered.

- `data/combined/initiative_name_crosswalk.csv` — `raw_initiative, initiative_canonical, tier, confidence, note`. One row per raw spelling that participates in a collision group (101 rows → 49 canonical programs). `canonical` = the dominant spelling (most dollars, tie-break most years) run through a deterministic house style. Every row is reviewable in the diff; a maintainer accepts or rejects each `confidence=review` row by editing the file and rebuilding.
- [`code/build_combined.py`](code/build_combined.py) now adds an **`initiative_canonical`** column to both `all_years_initiatives.csv` and `all_years_awards.csv`: `canonical = crosswalk[raw]` if the raw spelling is mapped, else `house_style(raw)`. `house_style()` strips a leading `*`, converts curly→straight apostrophes and `&`→`and`, and collapses whitespace — so even unmapped and future names get a consistent key, while source casing (acronyms like CASA, CUNY, HIV/AIDS) is preserved.
- The analysis is reproducible via [`code/analyze_initiative_names.py`](code/analyze_initiative_names.py) (re-run against any refresh of the combined CSV to regenerate the collision inventory the crosswalk is seeded from).

**Outcome.** Downstream consumers (the viz, the budget MCP) can join on `initiative_canonical` for a stable longitudinal key while `initiative` continues to preserve exactly what each source document printed. The **mechanical tier is resolved** — those 56 spellings collapse to 28 canonical programs deterministically. The **review tier is present but maintainer-gated**: its 45 spellings carry `confidence=review` in the crosswalk for accept/reject before they are treated as authoritative merges. Regression tests: `test_build_combined.py::test_initiative_canonical_column` and `::test_canonical_house_style_fallback`.

**Round 2 (2026-07-12) — pattern classes the first pass missed.** Once category consolidation (#18) merged the Fund axis, drilling into a category exposed initiatives that still duplicated for reasons beyond spelling: a trailing **`(Formerly …)` annotation** left in the name, an **Initiative/Program suffix** that drifts on and off, the **`NYC` prefix**, a **parenthetical acronym** on/off (e.g. `Creative Arts Team (CUNY CAT)`), and the **ATI** acronym spelled three ways. These were surfaced from the live viz, reviewed and approved by the operator (48 groups), and added to the crosswalk as `confidence=approved` rows (mapped at the raw level so they compose with the earlier entries). The 2 `Public Library (Branches)` vs `(Research)` pairs were deliberately **left separate** — genuinely different library systems. Result: viz leaves 882 → 832, remaining cross-year duplicate leaves 50 → 2 (the two intentional library pairs); FY2027 gate unchanged. Regression test: `test_build_combined.py::test_round2_pattern_merges_real_crosswalk`.

## 18. Category names are not canonicalized across years — the Fund axis fragments — RESOLVED (editorial)

**The anomaly.** The `category` field (the viz's "Fund" axis) fragments across years the same way initiative names do (#17), for more reasons: an **ALL-CAPS era (≈FY2009–FY2017) vs a Title-Case era (FY2018+)** that duplicates nearly every category; a `Services`/`Initiative(s)` suffix that drifts on and off (`Housing` vs `Housing Initiative`); plurality and possessives (`Veteran`/`Veterans`, `Children`/`Children's`); a literal typo (`ORGANZIATIONS`); an explicit **rename** (`OLDER ADULT SERVICES (FORMERLY SENIOR SERVICES)`); and a few **early compound categories** (`Youth and Community Development`, `Cultural Organizations and Libraries`) that the modern taxonomy has since separated. Scanning `all_years_initiatives.csv` finds **96 raw category labels** that represent roughly **25 modern categories**.

**How merges were decided (method).** Names alone are not enough, so each proposed merge was checked against the **organizations funded under it** — the share of the same nonprofits (by EIN) appearing under the old and new name. Two genuinely unrelated categories share ~17% of orgs; the confirmed merges share 85–100% (the Senior→Older Adult rename: 159 shared orgs). Org detail exists FY2016+ only, so pre-2016 name-only cases were decided by name. The modern **FY2027 names are the anchor**; older names route backward into them. The `%`-of-smaller overlap metric was rejected mid-analysis because it falsely scores tiny categories at 100% — Jaccard (shared ÷ combined) plus name agreement is used instead.

**The fix (non-destructive; editorial).** Raw `category` is **never altered**; a derived `category_canonical` column is added to both roll-ups.

- `data/combined/category_name_crosswalk.csv` — `raw_category, initiative, category_canonical, basis`. A blank `initiative` = a category-level rule (applies to every row of that category); a specific `initiative` = a **split override** (an early compound category whose lines route to different modern homes). `basis` ∈ `casing` (ALL-CAPS→Title Case, applied universally), `editorial` (confirmed name merges + the rename), `split-crossref` (the two compound categories, resolved at the initiative level).
- [`code/build_combined.py`](code/build_combined.py) adds `category_canonical`: a split override on `(category, initiative)` wins, else the category rule, else the raw category verbatim.
- [`viz/schedulec_cleanup.py`](viz/schedulec_cleanup.py) canonicalizes the Fund axis on both the initiatives and awards sides, so the Fund line is continuous. Fund values fall **78 → 36**; **FY2027 reconciliation gate unchanged ($655,764,999)** — canonicalization only relabels/merges the axis, it never moves dollars between programs.

**Editorial decisions recorded (operator, 2026-07-11).** Confirmed merges: Mental Health, Housing, Higher Education, Domestic Violence, Veteran(s), Anti-Poverty, Cultural Organization(s), and **Senior Services → Older Adult Services** (rename). Splits resolved at the initiative level — surviving lines routed to their FY2027 home (e.g. *Digital Inclusion & Literacy → Community Development*, *Immigrant Opportunities Initiative → Immigrant Services*, *CASA → Cultural Organizations*), retired lines left as-is. **Left as-is (not merged):** the ~17 early categories with no clear modern home (MOCS, CUNY, Sanitation, Libraries, etc.), plus a few unconfirmed name-matches (Public Safety Initiative, Government Officials, Parks-without-Services) — flip these in the crosswalk if a later review decides to merge them.

**Outcome.** The viz Fund axis and any longitudinal category rollup can join on `category_canonical`; the raw `category` still shows exactly what each document printed. This is an **editorial** consolidation (disclosed in `README.md` and the viz About panel), not a mechanical one — it reflects human judgment about which differently-named budget codes are the same program area. Regression tests: `test_build_combined.py::test_category_canonical_column`, `::test_category_split_override`, `::test_category_canonical_for_units`.

## 19. Schedule C appendix totals are flat ~$49.8M across FY2021–FY2027 — CONFIRMED real fixed pots, not an extraction artifact

**The concern.** The aging / local / youth Schedule C appendices (`*_appendix_a_aging.csv`, `*_appendix_b_local.csv`, `*_appendix_c_youth.csv`) sum to ~$49.79–49.80M for **seven straight years** (FY2021–FY2027). A flat multi-year total can look like an extraction artifact — the parser carrying a near-identical set forward from a cached or duplicated source rather than re-reading each year. Flagged as outlier **O6** in the 2026-07-15 expense-disclosure-vs-BetaNYC evaluation for the data owner to confirm.

**Verification (2026-07-15).** The totals are a **real, fixed programmatic pot**, confirmed by two independent signals an extraction artifact could not produce:

| FY | appendix total | rows | aging | local | youth |
|---|---|---|---|---|---|
| FY2021 | $49,799,000 | 4,310 | $5,610,000 | $36,539,000 | $7,650,000 |
| FY2022 | $49,799,000 | 4,182 | $5,610,000 | $36,539,000 | $7,650,000 |
| FY2023 | $49,789,000 | 4,056 | $5,610,000 | $36,529,000 | $7,650,000 |
| FY2024 | $49,799,000 | 3,911 | $5,610,000 | $36,539,000 | $7,650,000 |
| FY2025 | $49,799,000 | 3,920 | $5,610,000 | $36,539,000 | $7,650,000 |
| FY2026 | $49,794,000 | 3,914 | $5,610,000 | $36,534,000 | $7,650,000 |
| FY2027 | $49,799,000 | 3,860 | $5,610,000 | $36,539,000 | $7,650,000 |

1. **Row counts vary year to year (4,310 → 3,860)** while the total stays fixed. A duplicated/cached parse would reproduce identical row counts; a churning recipient list under a fixed pot is exactly what real equal-allocation programs look like.
2. **The aging ($5,610,000) and youth ($7,650,000) sub-pots are *exactly* constant every year**, and the local sub-pot varies by ≤ $10,000 in the parsed files. These are the Council's standing **equal-per-district** aging, local, and youth initiatives — a fixed citywide aggregate distributed across a recipient set that changes annually. The flatness is the *point* of these programs, not a parsing defect.

**Corrected 2026-10-20:** earlier text put the FY2023 Local shortfall down to "a seat vacancy / rounding". It is a parser loss. The FY2023 PDF (`source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf`) prints two $5,000 Local rows the parse dropped because their EIN text does not match `NN-NNNNNNN`: Elite Community Foundation, Inc. (p.213, printed `84 -2079676` with a space) and The Laundromat Project, Inc. (p.235, printed `87-0753479`; pypdf, which the parser uses, reads the hyphen as a soft hyphen, U+00AD). With them the PDF's Local rows sum to $36,539,000, the same pot as the other years; `fy23_appendix_b_local.csv` has 2,726 rows, $36,529,000. It holds Laundromat Project only as text in a neighbor's purpose (the Latinas On The Verge row), and it misattributes Elite: the row named Elite Community Foundation, Inc. (sponsor Kagan) carries Elite Learners, Inc.'s EIN and amount (814482839, $27,500), with Elite Community Foundation's own EIN and $5,000 left as text in `program`. The old parser's output is unchanged. FY2026's $36,534,000 has not been checked the same way.

**Conclusion.** O6 resolved — the flat appendix totals are the genuine value of fixed Council allocation pots, not an extraction artifact. No code or data change required; recorded here so future readers don't re-flag the pattern.

---

## 20. Schedule C awards — lost row boundaries put another organization's amount on a named row — OPEN

**Found 2026-08-11** while reviewing community PR #41. Recorded here because it falsifies a claim
this repo published, and because the shape of the error is the dangerous kind: the affected rows
are individually well-formed, carry a valid EIN and a real dollar amount, and pass every existing
check.

**The defect.** The Schedule C parser identifies an award by finding an EIN followed by a dollar
amount. The Council's PDFs do not always print it that way — sometimes an asterisk sits between
them (a compliance marker), sometimes a program or school name. When the pattern does not match,
the parser does not error. It absorbs that award's text into the *next* row it does recognize. The
result is a single row naming one organization while carrying a different organization's amount:

```
FY2017  amount $2,076,666  ein 113305406
organization: "Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services"
```

Two organizations, two EINs, two amounts, one row. A second variant appears in FY2024–FY2026,
where the *purpose* prose lands in the `organization` field instead.

**Scope.** 276 rows corpus-wide, detected by `code/validate_data.py` as the `org_merged` advisory:

| FY | rows | FY | rows |
|---|---:|---|---:|
| FY2016 | 21 | FY2020 | 1 |
| FY2017 | 118 | FY2024 | 1 |
| FY2018 | 94 | FY2025 | 1 |
| FY2019 | 39 | FY2026 | 1 |

**What was published and is now corrected.** `README.md` stated, of award rows with imperfect
organization names, that "EIN + amount are correct" and that "the EIN and amount are exact." For
these 276 rows that is false — the amount can belong to a different organization than the name.
Both lines were corrected on 2026-08-12. This is a documentation correction, not a data
retraction: the dollars present in the dataset are real dollars from the source documents, and no
figure was invented. What was wrong was the caveat telling readers which fields they could trust.

**Why nothing caught it.** Three gaps, each independently sufficient:

1. **The award stream is reconciled against nothing.** Each year's `*_reconciliation.txt` reconciles
   the *category summary* against the document's printed `TOTAL` lines. The award table is reported
   as a bare tally — `awards: 364 rows $89,901,487` — with no printed total beside it and no
   pass/fail. Award-level completeness has never been established by reconciliation in any year.
2. **`validate_data.py` had the detector, gated off.** The "a digit where a digit does not belong"
   idiom already existed for capital `agency` fields and is described there as a zero-false-positive
   signal. It ran only for `typ == "capital"`.
3. **`data/QA-REPORT.md` affirmatively cleared the worst file.** It graded
   `fy17_schedule_c_awards.csv` as `364 rows | 100% EIN coverage | 0 hard failures`, and named two
   of the merged rows in its own notes as *known false positives*. The artifact was inspected,
   misdiagnosed, and passed.

**Fixed in this change (2026-08-12).** The `org_merged` check now runs for every award-bearing
type — `schedule_c_awards`, `combined_awards`, and the three appendices. It is a **soft** advisory,
not a hard failure: the rows are real data that should surface with a warning rather than break the
build. `QA-REPORT.md` is regenerated and no longer grades the affected files as clean.

**Not fixed.** The extraction itself. Re-parsing to recover the absorbed awards is tracked in the
BetaNYC workspace plan `2026-08-11-schedule-c-award-coverage-remediation.md`, alongside a larger
finding: the Council publishes this same data as clean tabular spreadsheets
(`source/expense-funding-disclosure/`, FY2013–FY2027), and a source-comparability study confirmed
they describe the same universe of awards. Recovering the lost rows from that source is likely
cheaper and more reliable than repairing the PDF parser.

**Caution for anyone quoting a completeness figure.** Row-level capture against the Council's own
disclosure files is materially below 100% in **every** fiscal year, not only the years above, and
row capture and dollar capture differ by up to a factor of five because the awards that go missing
are the small ones. Always publish both numbers and name what each measures.

---

## 21. Schedule C awards — the extraction defects repaired 2026-08-12/13, and what remains — PARTIALLY RESOLVED

A community PR review surfaced a family of related extraction defects in the award stream. All
share one cause: the parser identifies an award by an EIN followed by an amount, and where the
source PDF prints anything between them — an asterisk, a program name, a hyphenated sub-name — the
row boundary is lost. This entry records what was repaired, how, and what deliberately was not.

### Repaired — 5,450 cells across 8 classes

| class | rows | column | what was wrong |
|---|---:|---|---|
| `blank_initiative` | 1,514 | `initiative` | an `initiative_provider` row with no initiative |
| `member_bleed` | 1,083 | `organization` | sponsoring member's surname prefixed to the name |
| `org_prose` | 1,076 | `organization` | purpose prose where the grantee name belongs |
| `split_org_name` | 673 | `organization` | a name beginning with a borough/surname split across `member` and `organization` |
| `truncated_org_name` | 423 | `organization` | the name dropped at its first " - " |
| `fy18_aging_shift` | 422 | `purpose` | the amount's decimal tail prefixed to every purpose |
| `org_merged` | 239 | `organization` | a neighbouring award's text absorbed into the field |
| `wrong_ein` | 20 | `ein` | right name and amount, a neighbour's EIN |

**Every change is recorded in `data/combined/org_name_recovery_crosswalk.csv`** with the column it
repaired, the original value, the replacement, the EIN, the amount and the defect class.

### Two guards, both hard-failing

- **`code/verify_crosswalk.py`** asserts the trail is COMPLETE (every entry matches the data),
  GROUNDED (no entry claims a no-op), UNIQUE (no duplicate keys) and **ACCOUNTED** — every cell
  differing from the baseline has an entry, that entry's recorded original matches what the
  baseline actually held, and no amount ever changes. It diffs *every* column, not a fixed list.
- **`code/verify_no_dollars_moved.py`** compares award dollars per fiscal year against a git ref.
  All thirteen years are identical before and after: **$3,741,615,569, delta $0**.

Both caught real errors in the repairs themselves, four times in one session — including a draft
that would have deleted a row carrying a real $20,000 designation hidden under a PDF heading, and a
version of ACCOUNTED whose hardcoded column list did not include `initiative`, so it reported "0
unexplained changes" while 1,514 initiative cells were rewritten.

### Method, and the keys that are NOT safe

- **The join key is (EIN, amount)**, never EIN alone. Fiscal sponsors pass funds through for many
  grantees: EIN 13-2612524 (Fund for the City of New York) carries **229 distinct names** here.
- **Council member is never a key component.** The disclosure workbooks are republished with the
  roster current at snapshot time, not the one that adopted the budget; including `member` drops
  the unique-match rate from 96% to 24%.
- **Disclosure headers are matched by case-insensitive substring.** They drift across the series —
  FY2016 heads the name column `Legal Name of Organization Requesting Funding`, FY2014 the amount
  `Amount ($`, FY2024+ `Legal Name`/`Tax ID`. Exact matching silently skipped two whole years.
- **Nothing is applied on a non-unique match.** A row left flagged is a correct outcome.

### Three published numbers that were wrong

- **"3,893 member-bleed rows"** was a leading-token scan and mostly false positives. Of 4,779 rows
  beginning with a surname or borough, **3,425 are correct as printed** — Brooklyn Book Bodega,
  Queens Borough Public Library, Louis Armstrong House Museum, Hudson Guild.
- **"9,700 blank initiatives, $595M"** counted `member_item` rows as defective. A member item is an
  individual Member's local designation and is *not* under a citywide initiative, so a blank there
  is correct. 5,887 of the 9,700 are member items.
- **"337 truncated fragments"** — a pattern scan for short names returned 1,382 rows, almost all
  legitimate. IlluminArt Productions, FAN4Kids, Mekimi and BOOM!Health are real organizations.
  Only the Council's own data distinguishes a short name from a truncated one.

### Not repaired, deliberately

- **1,993 recoverable initiatives left blank** because the disclosure names funding streams the
  Schedule C initiative axis does not use — `Speaker's Initiative` alone is 1,554 rows. Filling
  them would fragment the initiative axis exactly as §17 describes. A gap is recoverable later; a
  polluted vocabulary is not.
- **~200 rows** could not be resolved to a single candidate and remain flagged rather than guessed.
- **Amounts were audited and not touched.** 60,578 of 62,213 rows (97.37%) are corroborated by the
  Council's same-year disclosure as retrieved 2026-10-12, covering 94.68% of dollars (against the
  2026-07-15 snapshot: 60,667, 97.51%, 94.93%; the difference is all in the three workbooks the
  re-pull replaced: FY2025 −5, FY2026 −16, FY2027 −68). 18 differ by ≤$5 and 3 look like a
  neighbour's amount. `code/audit_amounts.py` reports and has no `--apply` path, deliberately.
- **The parser.** Nothing here stops the defect recurring; FY2027 produced 80 fresh `org_prose`
  rows. That is the open half of GitHub issue #52.

### Recovered data lives in `data/recovered/`, never merged into the per-year extracts

| file | rows | dollars |
|---|---:|---:|
| `schedule_c_appendix_recovered.csv` | 26,127 | $283,588,100 |
| `schedule_c_absorbed_awards.csv` | 442 | $66,472,992 |

Both carry confidence and provenance columns. Nothing already published moved.

---

## 22. Expense disclosure dataset — what the Council's workbooks settle, and what they do not

`data/{year}/expense_disclosure/` (FY2013–FY2027, 139,556 rows as retrieved 2026-10-12; plus FY2009,
FY2011 and FY2012, 16,988 rows from Internet Archive captures, §25) is built from the Council's own
disclosure workbooks by `code/parse_expense_disclosure.py`. It is a **parallel** dataset; nothing
in the Schedule C files moved. What a reader needs to know before using it:

- **Only one year carries a Council total, and it reconciles to the dollar.** FY2024 prints
  `New Total` $527,971,414 (as `SUM(H2:H10818)` and as `Adoption Total` + `Admin New Add`).
  The 2026-07-15 FY2026 workbook printed `Master List Total` = `Updated Total` = $716,213,155;
  the 2026-10-12 one has no footer rows at all, and its rows still sum to $716,213,155 (shown
  in its report as the earlier snapshot's figure, never as a verdict). The other workbooks print
  no total. Their sums are this repo's arithmetic, labeled as such in every report, never the
  Council's.
- **The 2026-07-15 FY2026 workbook also printed `Schedule C Total:` $714,879,821**, $1,333,334 below its Master List.
  The workbook's own `Difference:` row compares Master List with Updated Total (0), not with this
  figure, and the file says nothing about what it measures. It is reported, not reconciled
  against.
- **FY2024 row 10829 holds an unlabeled typed value, $454,755**, below the footer. It matches no
  row, no status, source, agency or member subtotal of FY2024. It is stripped and listed; its
  meaning is unknown.
- **Status is a moment, not a fact about the award.** FY2027 was half Pending on 2026-07-15
  (5,003 of 10,040 rows; $562,529,278 of $705,564,000) and 16% Pending by dollars on 2026-10-12
  (1,537 of 10,407 rows; $115,450,046 of $705,704,000); between the two, 3,608 rows went Pending
  → Cleared and 84 went back (`data/disclosure-snapshots/2026-10-12/FY2027-diff.md`). The FY2013
  file is 95% Pending by dollars. Every row is kept; headline figures are Cleared only and labeled.
- **`council_member` is the roster when the workbook was exported**, not at adoption (§21). Do
  not join on it. Since GitHub #72 each printed name carries the Legistar person it resolves to
  for that year (`council_member_id`, `council_member_type`; DATA-DICTIONARY), and the export-time
  effect is measurable: 341 rows name someone with no recorded vote in that fiscal year (FY2025
  `Wong` 150, FY2021 `Aviles` 84, FY2020 `D. Diaz` 107; audit G8), and 189 rows are `ambiguous`
  because two members of the name served that year (seat hand-overs: FY2014 and FY2022 `Barron`,
  FY2014 `Vallone`). FY2021 bare `Diaz` (123 rows; Ruben Diaz Sr. and Darma Diaz both served) is
  resolved to Ruben Diaz, Sr. by a recorded file convention, not by the evidence alone: the
  workbook prints Darma as `D. Diaz` that year, and the grantee mailing addresses agree (Bronx
  vs Brooklyn; DATA-DICTIONARY, crosswalk `method` = `file_convention`). The 2026-10-12 re-pull shows it moving: 149 FY2025 rows changed from `Holden`
  to `Wong`, and 161 FY2026 rows from `Bottcher` to `Wilson` (159 whose MOCS ID did not change,
  plus 2 that were also re-numbered, below). The snapshot diff never keys on it.
- **A MOCS ID is not a stable key across snapshots, and nothing published says it is one.** In
  the 2026-10-12 FY2026 workbook, 131 rows carry `FY26GP NNNNN` where the 2026-07-15 one had
  `FY26 NNNNN` (same number; on 129 every other field is identical, on 2 -- `FY26 00144`
  Alzheimer's Foundation $5,000 and `FY26 06277` Living Arts Collaborative $20,000 -- the member
  also moved `Bottcher` → `Wilson`); the workbook does not say what `GP` means. One FY2027 row
  was re-issued under a new number (`FY27 06029` → `FY27 10413`), two FY2027 IDs (`FY27 06102`,
  `FY27 06103`, Green Beetz) now carry a different EIN, and 24 FY2027 removed/added pairs share
  EIN, amount and legal name under a new MOCS ID with a different agency, stream or member
  (listed as "Likely re-issued" in `data/disclosure-snapshots/2026-10-12/FY2027-diff.md`; 2 in
  FY2026). IDs ascend with sheet order, which reads as a per-workbook sequence. Whether a MOCS ID
  joins to a registered contract is **unverified**. Key across snapshots on it with care.
- **321 groups of rows (662 rows; 341 beyond the first copy of each group, $8,549,772) are
  identical in every published field except `source_row`**, FY2013–FY2023, verbatim in the
  workbooks (`data/DISCLOSURE-AUDIT.md` F1). A member can designate the same amount to the same
  grantee twice, and from FY2024 the Council numbers look-alike rows as separate designations
  (142 more groups, 147 rows, identical except for a distinct MOCS ID), so the file cannot say
  which earlier repeats are real. **Decision (maintainer, GitHub #69): keep every row as
  published, and flag it.** `duplicate_group` names the first row of each group (blank when
  unique); audit question F3 checks the flag against F1's own grouping; the MCP tool says how many
  flagged rows, and how many dollars beyond each group's first copy, a result's totals include.

  | FY | groups | rows flagged | beyond the first copy | dollars beyond the first copy |
  |---|---:|---:|---:|---:|
  | 2009 | 97 | 373 | 276 | $2,512,897.68 |
  | 2011 | 11 | 23 | 12 | $110,452.38 |
  | 2012 | 11 | 22 | 11 | $89,000 |
  | 2013 | 9 | 20 | 11 | $178,875 |
  | 2014 | 18 | 36 | 18 | $138,000 |
  | 2015 | 17 | 35 | 18 | $1,775,350 |
  | 2016 | 19 | 43 | 24 | $565,382 |
  | 2017 | 27 | 54 | 27 | $758,995 |
  | 2018 | 26 | 53 | 27 | $1,212,646 |
  | 2019 | 28 | 58 | 30 | $724,480 |
  | 2020 | 75 | 154 | 79 | $919,480 |
  | 2021 | 19 | 42 | 23 | $337,186 |
  | 2022 | 40 | 80 | 40 | $1,373,189 |
  | 2023 | 43 | 87 | 44 | $566,189 |
  | **all** | **440** | **1,080** | **640** | **$11,262,122.06** |

  FY2024–FY2027: none. These are this repo's counts of the committed rows (each year's
  reconciliation report states them too), not Council figures.
- **64 amounts carry fractional cents** (FY2013 27, FY2014 30, FY2015 7), e.g. FY2013
  `22320.421`; 7 are binary float residue (e.g. FY2014 row 4255 `16279.539999999994`), of which
  one is still a live formula (FY2014 row 109 `=72743.46-7274.46` → `65469.00000000001`) and six
  are stored values, probably formulas pasted as values. They are published as the workbook stores them, not rounded:
  rounding moves no year's total by more than 1.2 cents, and keeping the stored value is what
  lets every CSV cell be checked against the workbook cell (`DISCLOSURE-AUDIT.md` A6).
- **Spreadsheet artifacts kept as published** (`DISCLOSURE-AUDIT.md`): 37 cells hold the Excel
  error `#N/A` (FY2014 `postal_code` 19; FY2017 `address1`, `city`, `postal_code` 6 each, on 6
  rows), published as the text `#N/A` by decision (GitHub #71; never blanked, never read as a
  value; pinned by `test_committed_na_cells_are_kept_as_published_issue_71`); 27 ZIPs stored as 4-digit numbers, some a
  lost leading zero (MA/VT/NJ), some not (`7083` on a Bronx address), and 72 ZIPs are `0` (all
  kept in `postal_code`; checked in `zip_status`, below); 5,656
  `state` cells read `New YorkNY` (FY2015–FY2017, as typed); one `state` holds a ZIP
  (FY2015 row 1235); fiscal-conduit cells hold `003`, `260`, `005`, a name and a sentence in the
  EIN/name columns. Invisible format characters are deleted (left-to-right marks,
  zero-width spaces, BOMs) except the soft hyphen: 211 cells hold one, and each reads as a hyphen that
  lost its glyph, so it is published as `-` (dropped where a `-` or `/` already sits beside it).
  An earlier version deleted it and published FY2018 rows 2796–2811 as `1211 40th Avenue` for
  the Queens address `12-11 40th Avenue` (GitHub #68; 17 address and 17 purpose cells regained
  their hyphen; audit question D13). Mojibake such as `EspaÃ±ol` is in the source cell and is kept.
- **ZIP codes checked against the Census 2020 ZCTA list (GitHub #70).** `postal_code` stays as
  published; `zip` / `zip_status` are derived (rules in DATA-DICTIONARY; the Census file's URL,
  date and sha256 in `source/census-zcta/MANIFEST.csv`). Of 46 four-digit ZIPs, 13 are padded
  (Brookline and Boston MA, Colchester VT, North Bergen NJ: the padded value is a ZCTA in the
  row's own state) and 33 are not: `1001`/`1002`/`1144` on New York rows pad to Massachusetts
  ZCTAs, `7052`/`7083` to New Jersey ones, `6108` to Connecticut (city Hartford, state cell
  `New York`), and `1004`/`1121`/`1123`/`1126` to no ZCTA at all; each looks like a typo of a NYC
  ZIP, and none is guessed. A ragged ZIP+4 (35 rows: `11203-` 24, `10027-000` 2, `10037-999` 2,
  `11217-11217`, `11204-11204`, `10033-10033`, `11102-20`, and the three printed with another
  separator: `11231=1020` FY2018 row 8527, `11413 ZipCode2: 3929` FY2015 row 1593,
  `11233 ZipCode2: 150` FY2015 row 6003) is `trimmed` to its first five digits, because each is
  a ZCTA in the row's own state; `postal_code` keeps the cell as published. The hyphen, `=` and
  `ZipCode2:` are the only ZIP+4 separators in any year; the other five-digit-led values stay
  `invalid` (`10310\``, `10465ww`, `10448448`, `1030410016`: audit G11 lists them).
  **Six-digit ZIPs** (65 rows, 10 values; decision 2026-10-13) are read by deleting one digit at
  every position, since the extra digit is not always in one place (leading in `111691`,
  trailing in `115300`, inside in `100665`). When exactly one result is a ZCTA in the row's own
  state the row is `repaired_extra_digit` (35 rows: `111691` → 11691 Far Rockaway 30,
  FY2019–FY2027; `100665` → 10065 2; `115300` → 11530; `111234` → 11234; `110027` → 10027).
  When more than one is, the row is `ambiguous_extra_digit` with no `zip` and every candidate in
  `zip_candidates` (30 rows: `104658` → 10458/10465/10468 11; `100037` → 10003/10007/10037 10;
  `900069` → 90006/90069 5; `114345` → 11434/11435 3; `100115` → 10011/10115 1). None is picked,
  by a doubled digit or by knowing the street: that would be a guess. The four ambiguous New
  York values could later be settled from the street address with NYC Planning's GeoSearch
  (tracker #75, a future item that needs the maintainer's approval; no lookup is done now). No
  county narrowing is applied: the committed Census table carries states, not counties (audit
  G12 checks every six-digit row). `blank` (an empty cell) is kept apart from `invalid`.
  `not_a_zcta` is **not verified, not fake**: PO-box and single-building ZIPs have no ZCTA. Counts (this repo's, of the committed rows):

  | FY | valid | padded | trimmed | repaired_extra_digit | ambiguous_extra_digit | not_a_zcta | state_mismatch | invalid | blank |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | 2009 | 4,773 | 0 | 0 | 1 | 0 | 56 | 0 | 0 | 915 |
  | 2011 | 5,221 | 0 | 0 | 0 | 0 | 62 | 0 | 1 | 136 |
  | 2012 | 5,330 | 0 | 6 | 1 | 2 | 58 | 2 | 4 | 420 |
  | 2013 | 4,561 | 0 | 1 | 0 | 0 | 50 | 3 | 5 | 367 |
  | 2014 | 5,557 | 0 | 2 | 0 | 0 | 44 | 1 | 32 | 975 |
  | 2015 | 5,946 | 6 | 2 | 1 | 0 | 63 | 2 | 4 | 626 |
  | 2016 | 6,885 | 2 | 1 | 0 | 1 | 50 | 1 | 11 | 846 |
  | 2017 | 7,688 | 5 | 2 | 0 | 0 | 69 | 7 | 10 | 890 |
  | 2018 | 8,092 | 0 | 1 | 1 | 13 | 80 | 2 | 10 | 695 |
  | 2019 | 8,773 | 0 | 0 | 4 | 0 | 87 | 0 | 4 | 787 |
  | 2020 | 9,658 | 0 | 3 | 2 | 0 | 72 | 0 | 4 | 877 |
  | 2021 | 8,511 | 0 | 3 | 3 | 0 | 80 | 3 | 3 | 451 |
  | 2022 | 10,587 | 0 | 4 | 4 | 11 | 83 | 2 | 4 | 641 |
  | 2023 | 10,120 | 0 | 3 | 3 | 1 | 74 | 5 | 0 | 821 |
  | 2024 | 9,904 | 0 | 3 | 4 | 4 | 71 | 0 | 0 | 825 |
  | 2025 | 10,523 | 0 | 4 | 5 | 0 | 82 | 1 | 0 | 661 |
  | 2026 | 11,006 | 0 | 3 | 4 | 0 | 87 | 1 | 2 | 661 |
  | 2027 | 9,532 | 0 | 3 | 4 | 0 | 81 | 1 | 75 | 711 |
  | **all** | **142,667** | **13** | **41** | **37** | **32** | **1,249** | **31** | **169** | **12,305** |

  The counts in the prose above this table are FY2013–FY2027. The archived FY2009–FY2012 rows
  (§25) add 6 `trimmed` (`10009-10009`, `11205-11205`, `11238-11226`, and more of `11217-11217`
  and `10033-10033`), 2 `repaired_extra_digit`, 2 `ambiguous_extra_digit` (`100215` → 10021 or
  10025) and 2 `state_mismatch`, all under the same rules; audit questions G7, G11 and G12 list
  every one.
  FY2027's 75 `invalid` are mostly the `0` ZIPs (69). The 29 `state_mismatch` rows (FY2013–FY2027) are mostly a
  NYC ZIP on a row whose state cell names another state (`NC`, `NE`, `LA`, `MI`, `New JerseyNJ`
  on Staten Island addresses), plus a few out-of-state ZIPs on rows marked New York
  (`07087`, `08701`, `15050`, `19454`, `94110`). Street addresses are not checked; NYC Planning's GeoSearch would
  be the next step and needs its own approval (about 140,000 lookups).
- **One FY2016 `address2` cell (row 640) is a number formatted as a date** (`42037`, which Excel
  shows as 2015-02-02). The stored value is kept; what was meant is not knowable from the file.

---

## 23. Disclosure vs Schedule C — coverage, and the appendix question (GitHub #57 blocker 2) — SETTLED for blocker 2

`code/reconcile_disclosure_schedule_c.py` joins each year's disclosure rows (§22) to the Schedule
C award files on `(EIN, amount)` as a multiset — never EIN alone, never the member. Full output:
[`data/DISCLOSURE-COVERAGE.md`](data/DISCLOSURE-COVERAGE.md) and
`data/disclosure_schedule_c_coverage.csv` (year × stream × status, rows and dollars). Every number
below is that script's arithmetic on committed files, pinned by
`code/test_reconcile_disclosure_schedule_c.py`. **None is a Council figure.**

**This is coverage, not a capture rate.** The disclosure is a later snapshot than the adopted
Schedule C and includes post-adoption designations, so it is not the adopted-budget universe
(see #58 item 3 on why the earlier 68.3% was retracted). "Published set" = body + the three
appendix CSVs (what the MCP indexed through 1.x). The disclosure-built appendix sidecar is excluded as
circular; the absorbed-awards sidecar is reported separately in the full output.

| FY | disclosure rows | matched | Cleared $ matched (headline) | Pending $ matched | appendix rows matched after the body | appendices vs body |
|---|---:|---:|---:|---:|---:|---|
| FY2013 | 4,987 | 0 | 0 of 18,201,784.75 (0.0%) | 0 of 380,680,617.43 (0.0%) | — | no Schedule C award files |
| FY2014 | 6,611 | 0 | 0 of 392,655,571.85 (0.0%) | 0 of 1,077,905 (0.0%) | — | no Schedule C award files |
| FY2015 | 6,650 | 535 | 61,279,634 of 285,921,454.46 (21.4%) | 450,000 of 810,402 (55.5%) | — | appendix CSVs empty |
| FY2016 | 7,797 | 290 | 76,857,624 of 380,361,130 (20.2%) | 0 of 1,015,496 (0.0%) | — | appendix CSVs empty |
| FY2017 | 8,671 | 329 | 73,268,111 of 352,787,056 (20.8%) | 0 of 714,830 (0.0%) | — | appendix CSVs empty |
| FY2018 | 8,894 | 831 | 73,096,268 of 381,385,171 (19.2%) | 0 of 514,829 (0.0%) | 417 / 422 (aging only) | additive, 1 exception |
| FY2019 | 9,655 | 756 | 161,144,404 of 392,443,522 (41.1%) | 15,000 of 501,478 (3.0%) | — | appendix CSVs empty |
| FY2020 | 10,616 | 2,665 | 236,937,236 of 456,580,952 (51.9%) | 0 of 635,750 (0.0%) | — | appendix CSVs empty |
| FY2021 | 9,054 | 5,841 | 235,798,936 of 391,770,561 (60.2%) | 630,000 of 1,479,945 (42.6%) | 4,148 / 4,310 | additive, with exceptions |
| FY2022 | 11,336 | 5,519 | 252,340,025 of 536,959,144 (47.0%) | 460,124 of 1,590,683 (28.9%) | 4,087 / 4,182 | additive, with exceptions |
| FY2023 | 11,027 | 5,713 | 294,143,159 of 537,910,110 (54.7%) | 1,599,500 of 3,516,885 (45.5%) | 3,930 / 4,056 | additive, with exceptions |
| FY2024 | 10,811 | 9,029 | 439,808,260 of 526,907,681 (83.5%) | 604,800 of 1,063,733 (56.9%) | 3,791 / 3,911 | additive, with exceptions |
| FY2025 | 11,276 | 9,373 | 455,231,615 of 592,800,281 (76.8%) | 677,000 of 2,380,901 (28.4%) | 3,813 / 3,920 | additive, with exceptions |
| FY2026 | 11,764 | 9,519 | 515,964,746 of 708,776,879 (72.8%) | 1,132,375 of 7,436,276 (15.2%) | 3,802 / 3,914 | additive, with exceptions |
| FY2027 | 10,407 | 9,858 | 548,163,294 of 590,253,954 (92.9%) | 98,302,659 of 115,450,046 (85.1%) | 3,796 / 3,860 | additive, with exceptions |

The table is the disclosure as retrieved 2026-10-12. Against the 2026-07-15 snapshot, FY2027 read
10,040 rows, 9,976 matched, 142,899,722 of 143,034,722 Cleared (99.9%), and 3,860 / 3,860
appendix rows, **additive, exactly**; FY2025 and FY2026 moved by under one percentage point.

**Blocker 2 — verdict: the appendices are additive in every year that has appendix rows.** The
test: match the body to the disclosure first, then see whether each appendix row still finds a
designation of its own. A re-sorted subset of the body would find almost none. Instead 96.2% to
98.8% do. In FY2027 the appendix dollars ($49,799,000) equal the disclosure's Local + Aging +
Youth dollars to the dollar in both snapshots; all 3,860 appendix rows found their own
designation against the 2026-07-15 snapshot and 3,796 do against the 2026-10-12 one. The
exceptions are a handful against thousands (0–14 body rows the disclosure files only under
Local/Aging/Youth; 0–33 keys printed in both body and appendix beyond what the disclosure holds), each
listed key by key in `data/DISCLOSURE-COVERAGE.md` §4b as a candidate extraction or filing error.
The five years with empty appendix CSVs (FY2015–2017, 2019–2020) have nothing to add or
double-count; the PDFs do print those appendices, with bare amounts the parser's `$` anchor
misses (#59 — verified for FY2016 and FY2019 by reading the page text). This settles the award
rows only: it says nothing about whether the printed category `TOTAL`s include the appendix pots.

**The FY2027 gap, checked rather than assumed — against the 2026-07-15 snapshot.** 64 disclosure rows had no published Schedule C
counterpart. (The raw row-count difference is 62: 10,040 disclosure rows against 9,978 Schedule
C rows, two of which also lack a disclosure counterpart.) 60 of the 64 carry the City's own EIN `136400434`, all Pending, $50,508,586, each naming a
City agency or office as the grantee (DYCD, Cultural Affairs, Aging, Parks, CUNY, a District
Attorney, a Borough President, …). The other four: two are $1 near-misses —
Schedule C prints Osborne Association $14,999 and Selfhelp Community Services $44,999 where the
disclosure has $15,000 and $45,000 (the two unmatched Schedule C rows) — plus Medicare Rights
Center $135,000 (Speaker's Initiative, Cleared) and CUNY $10,000 (Parks Equity, Pending).

**Corrected 2026-10-20:** the Medicare Rights Center row is not disclosure-only. The FY2027
Schedule C PDF prints it on p.279 (`Felder Medicare Rights Center, Inc. 133505372 $135,000
DFTA`). The old parser dropped it: the row absorbed the previous award's purpose text, which
contains "Council member offices", and the header-junk filter in `parse_schedule_c.py` deletes
any row whose organization contains "council member" (confirmed by re-running the parser with
the filter logged). So it is an extraction loss, not a gap in the published Schedule C. The
old parser's output and the coverage numbers above are unchanged.

**The same gap against the 2026-10-12 snapshot is 549 rows, $59,238,047** (385 Cleared, 164
Pending); 95 of them carry the City EIN ($33,977,899: 68 Pending, 27 Cleared), and 56 Schedule C
body rows now lack a disclosure counterpart (2 in July). Between the snapshots the FY2027
workbook gained 495 rows, lost 128 and changed the amount on 72
(`data/disclosure-snapshots/2026-10-12/FY2027-diff.md`). That widening is the later snapshot
moving away from the adopted Schedule C, which is why this is coverage and not a capture rate;
the full list is in `data/DISCLOSURE-COVERAGE.md` §5.

**Ambiguity, counted.** Where a key's disclosure rows differ in stream or status and Schedule C
has fewer rows than the disclosure, which disclosure rows matched is a deterministic choice, not a
fact; those rows are counted per year in `data/DISCLOSURE-COVERAGE.md` §1 (767 in FY2027, up to
1,228 in FY2026, as retrieved 2026-10-12). A year's matched rows and dollars across all statuses do not depend on the
choice; the Cleared / Pending columns and the stream split do, within those counts.

---

## 24. Disclosure vs NYC Open Data `4d7f-74pe` — small items recorded (GitHub #89 B13) — OPEN where marked

From the Open Data comparison (`research/2026-10-14-open-data-vs-disclosure-diff.md`). Every
number is this repo's arithmetic on committed or manifest-pinned files, not a Council figure.

- **FY2018 row 2289, `$221` to the Department for the Aging.** `funded_disclosure_FY2018.xlsx`
  row 2289: source `Senior Centers, Programs, and Enhancements`, legal name `Department for the
  Aging`, the City's EIN `136400434`, `CLEARED`, $221, agency DFTA, no street address, purpose
  "This allocation provides operational support for non-DFTA and DFTA senior centers." Open Data
  has no row for it, and it is the net one-row difference between the two sources for FY2018
  (8,894 vs 8,893 rows). An amount this small on a City-to-City line reads like a residual
  adjustment, but nothing in the file says so. **Kept as published, not flagged.**
- **FY2021: 18 `Food Pantries` rows, $16,011,884, are in our file and not in Open Data**
  (all Cleared, DYCD; 17 with a blank council member, e.g. Metropolitan New York Coordinating
  Council on Jewish Poverty $4,500,000, United Way of New York City $2,500,000). Our FY2021
  workbook's sheet is dated 2023-06-23; Open Data's copy was last updated 2021-04-20.
  **OPEN: when they were added is not established.** The planned check against the FY2021
  Transparency Resolutions was not made, because this repo's Transparency Resolution files are
  extracted from PDFs (`code/parse_transparency_reso.py`), and the 2.0 rule is structured data
  only. It needs a structured source for post-adoption designations, or the Council's answer.
- **FY2009: two rows that are not grants to an organization.** The Council's FY2009 workbook
  prints `Borough President Discretionary Funding` $533,000 (DFTA) and `Provider's Choice`
  $1,200,000 (ACS), both to the City's EIN with no address; Open Data carries the same two under
  MOCS ID `FY09 Not an Award`, the only rows with that ID. Decision (Noel Hidalgo, 2026-10-14):
  keep both, flag them `row_flag = not_an_award` (DATA-DICTIONARY). The rule is in
  `code/parse_expense_disclosure.py` (`ROW_FLAGS`): FY2009 rows 523 and 4092, $1,733,000 in all,
  still in every total. Audit question I3 checks the flag against Open Data's own rows.
- **Open Data BBL `0`** (15 rows: FY2019 14, FY2010 1) is read as blank wherever this repo
  carries or profiles Open Data geocodes. No other geocode column holds an all-zero value.
- **Open Data calls these rows "applications".** They are designations. The Council's actual
  application files (every request, funded or not) are a separate data class
  (`research/2026-10-14-wayback-council-files.md`), not in this dataset.
- **The 2026-07-07 scoping note said Open Data's member names already match ours.** They do not;
  the note now says so (`research/2026-07-07-fy09-fy21-legacy-import-scoping.md`).

---

## 25. Expense disclosure FY2009, FY2011, FY2012 from the Internet Archive; FY2010 left out (GitHub #86, #89 A2, A3, A5)

The RnD site serves FY2013 onward only. The Council's own workbooks for FY2009–FY2012 survive as
Internet Archive captures (`source/wayback-council/`, `research/2026-10-14-wayback-council-files.md`).
Three of the four are now in the dataset, parsed by the same parser with the same rules; each
year's file, original URL, capture timestamp and sha256 are in `data/disclosure_years.csv`, and
the build stops if a file's sha256 differs from `source/wayback-council/MANIFEST.csv`. Every
number here is this repo's arithmetic on those files.

- **FY2010 is not loaded.** The workbook has 2,592 rows ($111,558,052.58); NYC Open Data
  `4d7f-74pe` has 5,981 rows ($357,820,611) for the year: 1,864 Local, 817 Youth and 561 Aging
  rows the workbook lacks, and 180 matched rows whose address the workbook leaves blank. Both
  archived copies (2016-12 and 2025-02) are content-identical (different files and sha256, same rows), so this is what the Council published.
  Mixing the two would make a year neither source published. **OPEN** until it is known which
  is complete (decision #89 A3). The workbook stays in `source/wayback-council/files/` and its
  counts are in `data/disclosure_years.csv` (`loaded = no`).
- **FY2009 is an early snapshot** (as FY2013 is, §22): 1,389 of 5,745 rows are Pending
  ($7,263,353.01 of $414,226,176.88, 1.8% of dollars), where Open Data, a later state of the same
  rows, shows 24 Pending. The Council never revised the workbook. By dollars the gap is small,
  but its statuses are not the year's outcome; `early_snapshot = yes`, and its Cleared total is
  not a headline. Every FY2009–FY2012 pair of captures (2014–2016 and 2025) is content-identical.
- **Statuses the later years do not use**, all `status_norm = other`, raw value kept: FY2011
  `Government` 136 rows ($2.6M) and `Pending FC Clearance` 3; FY2012 `Government` 49 rows
  ($235,206,318: City agencies as recipients; Open Data calls the same rows Cleared) and
  `CBO Defunded` 155 rows, all $0 (Open Data dropped them). Neither file defines them. FY2012's
  Cleared total ($150.7M) is therefore far below its rows' total ($386.8M); report `Government`
  as its own line (#89 B4).
- **Four EINs are not 9 digits, kept as published:** FY2009 `EX130314` (row 3075, Lynvets
  Football), `EX123557` (4366, Regina Young at Heart), `11-31735A` (4912, St. Albans Presbyterian
  Church); FY2011 `NA` (679, CBO Training). Which digits were meant is not in the file. The
  validator lets exactly these four through (`PUBLISHED_ODD_EINS`). 46 EINs are blank (FY2009 25,
  FY2011 13, FY2012 8); with FY2011 `NA` they carry `row_flag` `no_grantee_ein` (next
  bullet). FY2011 and FY2012 store 150 EINs as numbers that lost a leading zero (3 and 147),
  re-padded as in FY2013.
- **53 disclosure rows print no grantee EIN** (52 blank, plus one FY2011 cell printed `NA`),
  $159,951,020.83 in all, most of it FY2009 rows that name an initiative or program rather than an
  organization ("School Budget Restoration", $120,000,000; "NYCHA Community Services",
  $18,000,000). They are published rows and stay in every total. **Flagged 2026-10-16:** each
  carries `row_flag` `no_grantee_ein`, a rule (a blank or `NA` EIN), not a judgment about the row:
  FY2009 25 ($154.6M), FY2011 14, FY2012 8, FY2013 2, FY2014 3, FY2015 1. No other year prints an
  EIN for these names, so none is inferred, and they are not sorted into City program vs. unknown
  by hand. The MCP says on each row and in its no-EIN note: "No grantee EIN printed by the
  Council. Often a city program rather than a nonprofit." `code/test_parse_expense_disclosure.py`
  locks the count at 53 and the validator requires the flag on exactly the blank/`NA` rows. Two
  other FY2009 rows carry the decided flag `not_an_award` (§24); none carries both.
- **Sub-cent amounts:** FY2009 carries 858 amounts with fractions (e.g. `7481.296758`), FY2011
  205, FY2012 85; 483, 30 and 28 of them past the cent (audit E2). Kept as stored; Open Data
  rounds them (to cents through FY2011, to dollars from FY2012), which is what `od_match` records.
- **Council member values** (`council_member_type`, crosswalk): two rules were extended, both
  generic and tested, never a per-name decision. A printed generational suffix must match
  Legistar's (`Vallone, Jr` is Peter F. Vallone, Jr., 5271, never Paul A. Vallone); a surname
  matches with spaces ignored when no exact surname exists (`DeBlasio` → Legistar's `de Blasio`,
  5286). FY2009 prints Thomas White, Jr. both as `White` and `White, Jr` (both 6273).
  **RESOLVED 2026-10-16: `CC` is the Speaker, and `BK`/`BX`/`MN`/`QN` are borough delegations**
  (decided by Marvin on the evidence; Noel Hidalgo delegated the call). The evidence, from the
  full NYC Open Data `4d7f-74pe` copy joined on `od_mocs_id` = `mocs_id` and re-verified
  2026-10-17: every `CC` row with an Open Data pair is `Speaker` there, 895 of 895 (FY2009 224,
  FY2011 245, FY2012 219, FY2013 207; the rest have no pair), and FY2009 `QN` → Queens
  Delegation 37/37, `MN` → Manhattan 35/35, `SI` → Staten Island 23/23, `BK` → Brooklyn 18/18,
  `BX` → Bronx 13/13. No paired row disagrees. FY2009–FY2013 print `CC` (240 / 271 / 252 / 240
  rows) where FY2014–FY2027 print `Speaker`, and no year prints both; the FY2010 Internet Archive
  workbook (not loaded) also prints `CC` (50 rows, never `Speaker`). The same FY2013 award is
  `CC` in the Council workbook and `Speaker` in Open Data (review-sheet R10, R12). FY2009 prints
  each borough code beside the bare borough name (`BK` 18 and `Brooklyn` 50), as it does `SI` and
  `Staten Island`; both are typed `delegation`. Implemented as a generic rule (`LABEL_CONVENTIONS` in
  `code/build_member_crosswalk.py`), not per-row edits: `council_member` keeps the printed value,
  `council_member_type` becomes `speaker` / `delegation`, and the crosswalk `method` reads
  `file_convention:CC=Speaker` (and so on). The build stops if a year ever prints both `CC` and
  `Speaker`, or a code and that borough's `… Delegation` spelling (no year does). Still
  `unresolved`: three multi-member values (`Barron & Eugene`, `Lappin, Koppell/Citywide`, and a
  nine-member FY2011 list, 51 rows) and FY2014 `NA` (3 rows); 56 rows, down from 1,196.
- **Exact copies** are many more in FY2009 (97 groups, 373 rows; §22 table) than in any later
  year. Kept and flagged as in every year.
- **Duplicate Open Data MOCS IDs.** `od_mocs_id` repeats on two FY2009 pairs because Open Data
  repeats the ID: `FY09 Not an Award` (§24) and `FY09 2039`.

---

## 26. Council capital from structured sources (GitHub #89 A6, A7, B8–B10)

`data/capital/` (README there). Every number is this repo's arithmetic on committed files.

- **FY2018 is missing from this dataset.** No Council workbook was found for it, and `t474-a92g`
  starts at FY2019. **Corrected 2026-10-20:** earlier text (and `data/capital/README.md`) read as
  if FY2018 had no source at all. `source/FY18/FY18-Sec254-Capital-ResoA-M499-Res1534-Res1535.pdf`
  is, despite its name, the FY2018 Section 254 **supporting detail** book (title page "Supporting
  Detail For Fiscal Year 2018"; Part I: 1,485 projects, $575,000,000, p.70 `TOTALS FOR ALL (1485
  PROJECTS) 575,000,000`; the 96-page book also has Parts II and III). It is a PDF,
  so under §27 it is not part of this structured dataset, and it has not been parsed. The FY2018
  Resolution A book is not in `source/`.
- **The Council's list and OMB's adopted budget agree by budget line in most lines, not all**
  (`data/capital/RECONCILIATION.md` §3). FY2027: 146 of 153 Council lines match OMB's July 2026
  release to the dollar in both years; 7 differ (`P D017` $579,000 lower at OMB and `P D020`
  $579,000 higher look like one project booked in another borough: interpretation), and 8 OMB
  `D`-series lines have no Council row; OMB is $25,789,000 higher in total. FY2021 and FY2024
  match on every Council-series (`D`) line. One Council row is on no such line and so is not
  compared: FY2021 `PW MN02A` (Constantinides, BioBus mobile science lab, $304,000); RECONCILIATION
  §3 and the tool's answer list it. 1,425 line-year comparisons in all, over 515 distinct lines.
  **OPEN:** why they differ (#89 C1; Council Finance or OMB).
- **Garbled accented names in `t474-a92g` (FY2019–FY2025), kept as published.** NYC Open Data's
  rows carry accented letters decoded with the wrong character set, and the committed source
  (`source/open-data-t474-a92g/t474-a92g.csv.gz`) has them byte for byte, so this repo did not
  introduce them and does not repair them. Sponsors: FY2023–FY2024 `Oss├⌐` (20 rows),
  `Avil├⌐s` (44), `Cab├ín` (26), `Vel├ízquez` (40), plus co-sponsor lists such as
  `Speaker, Avil├⌐s`; FY2025 `OssΘ` (16), `AvilΘs` (20), `Cabßn` (13). The Council's own
  workbooks spell the same members `Ossé`, `Avilés`, `Cabán` (FY2026, FY2027). Titles and
  descriptions show the same thing (`FA├çADE`, `CAF├ë`, a stray `├ü`), and one FY2017 workbook
  description prints a Greek `Τ` in `FAΤADE`. Consequences: a search for `Ossé` does not find
  `OssΘ` or `Oss├⌐`; search by the printed value, or by `budget_line`. Since 2026-10-17 a
  printed value pasted back exactly always finds its rows (`mcp/test/fold-roundtrip.test.js`).
- **t474-a92g problems.** 5 records broken across 12 rows (§ RECONCILIATION 2): the FY2026 one
  is proven by the Council's workbook; the FY2020 (2), FY2022 and FY2023 ones are kept with a
  blank amount and flagged, and their spilled amounts ($170,000, $300,000, $55,000, $150,000
  on fragments that cannot be tied to a record from the Council's own files) are not counted.
  `council_district` collapsed comma lists into single numbers. FY2019 `title` often names the
  organization. Against the Council's FY2026 workbook, t474's FY2026 differs only by that broken
  record ($2,000,000).
- **Codes:** the Council's t474 dictionary defines CD 00 and 88–99 (99 = Technical
  Adjustments) and ID types CN, NC, TA, RR. Borough `A`, CD `80` ("Admin"), the FY2027 `CC`
  prefix and FY2016 `PN` are **meaning unconfirmed** (#89 B9).
- **Totals rows:** FY2015 and FY2016 end in a totals row; stripped; the kept rows equal it.
- **2cmn-uidm** has one row with no release, line or year and grand-total-sized amounts
  (`row-qxu3-pz44.fhei`); stripped from the reference table.
- **No project-level or contract-level claim** is made: Council project IDs do not appear in any
  OMB dataset (A7, C2, C9).

---

## 27. PDF-derived data retired in 2.0 (2026-10-14)

Noel Hidalgo's decision of 2026-10-14: version 2.0 of `@betanyc/nyc-budget-mcp` and the GitHub
Pages site use structured sources only. Retired and no longer served or shown: Schedule C
(awards, initiatives, appendices), Terms & Conditions, per-year §254 capital, transparency
resolutions, `data/combined/` (including the Legistar crosswalk of those documents) and
`data/recovered/`. The files stay in the repository as a historical record; nothing was deleted.
`mcp/test/no-pdf-data.test.js` fails if the MCP's index build reads one of them or the npm
package ships one. Two things about the structured data that the 2.0 MCP now states on its
answers surfaced when FY2009 entered the served set: the 53 rows with no grantee EIN (now in
§25) and:

- **Fractional amounts.** FY2009–FY2012 carry amounts such as `7481.296758`; the MCP shows them
  rounded to cents and totals the exact values.

---

## 28. FY2009 Transparency Resolutions are OCR-derived — the one year whose numbers are model-read

> **Scope under 2.0.** This is a PDF-derived research dataset (`data/fy09/transparency-resolutions/`),
> kept in the repository like the other transparency-resolution files (§27). It is not served by
> `@betanyc/nyc-budget-mcp` 2.0. The served FY2009 data is the expense disclosure workbook (§25).

**What it is.** All eight FY2009 Transparency Resolution PDFs (`source/FY09/transparency-resolutions/`, 332 pages) are 300-dpi bitonal Xerox scans with **no text layer whatsoever** — `pdftotext` returns nothing. Every other fiscal year in this repo is extracted deterministically from the document's own text layer. FY2009 has no text layer to extract, so it is read by OCR (docTR) via `code/parse_transparency_reso_fy09.py` and the staged pipeline in `code/ocr/`.

**Why this is called out rather than buried.** The repo's standing claim is that its figures are never model-read. That claim holds for FY2010–FY2027 and does **not** hold verbatim for FY2009. Rather than quietly relax the claim, FY2009 is labelled as the exception in `README.md`, `code/PARSING.md`, and in the year's own `fy09_transparency_reconciliation.txt`.

**What is checked instead.** Four things stand in for the missing text layer:

1. **Printed chart totals.** FY2009 is the *only* Transparency-Resolution year whose charts print totals at all (e.g. `$500,000.00` on the Veterans Resource Center chart; `$0.00` on a net-zero transfer chart). Where a total is printed, the OCR'd rows must sum to it **exactly**. Charts with no printed total stay `NOT RECONCILABLE`, as in every other year.
2. **Shape checks** on EIN (`##-#######`), amount (`$#,###.##`; parenthesised = rescission), and the 3-digit `Agy #` / `U/A` codes.
3. **An agency-code dictionary** harvested from the already-parsed FY2010–FY2027 transparency CSVs, so a plausible OCR slip (`DYGD` for `DYCD`) fails where a generic uppercase-letters regex would pass.
4. **No quiet repair.** Only characters that cannot occur in the target grammar and have exactly one reading (bracket variants, whitespace) are normalized. Letter/digit confusions (`O`/`0`, `S`/`$`) are never guessed — the value is left unparsed, flagged with an `ocr:*` code in the `flags` column, and queued in `fy09_transparency_needs_review.csv` with a crop of the original pixels.

**Two structural quirks of the FY2009 documents worth knowing.**

- **Rotation varies page to page within a single file.** The chart pages are landscape tables printed onto portrait sheets, and the direction is not constant — Transparency-Reso-01's Chart 1 page reads top-down on the left edge, Transparency-Reso-07's Chart 3 page reads bottom-up. Orientation is therefore detected per page, and the decision for every page is persisted to `build/ocr/<stem>/orient.json` so a bad call can be corrected by hand and the downstream stages re-run.
- **FY2009 charts carry columns no other year has** — `Fiscal Conduit/Sponsoring Organization`, `Fiscal Conduit EIN`, and `Status (Council, MOC, etc)`. The shared 16-column schema cannot hold them (`validate_data.py` treats an extra column as a hard failure), so they are emitted to the sidecar `fy09_transparency_fiscal_conduits.csv`, joined back on `(resolution, chart, ein)` — the same pattern as `fy25_capital_noncity_by_entity.csv`. The `Status` column has no analogue in any other year; it records the Council's own pre-qualification review state at the time of the resolution.

**One upside.** Because the tables are fully ruled, column identity comes from the printed grid rather than from regex-guessing at a reflowed text line. The FY2010–FY2013 text layers glue adjacent words together and bleed the header into the first data row (see #11 and the `org-text confidence: LOW` bands in those years' reconciliation files). FY2009's organization and member *text* should therefore come out **cleaner than the years that "worked"** — the opposite of what one would expect from a scan.

---

## 29. FY2027 Schedule C rebuilt from the PDF, checked (#102) — ALL 6 ITEMS DECIDED, NOT YET CLOSED

> **Scope.** A new, checked parse of `source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf`
> (`code/parse_schedule_c_v2.py`, `config/schedule_c/fy2027.toml`). Its review record is
> [`research/2026-10-20-fy27-schedule-c-review/`](research/2026-10-20-fy27-schedule-c-review/README.md).
> The old `data/fy27/schedule_c/*.csv` files are unchanged and stay the historical record (§27).
> Not served by the MCP.

**Result.** 9,979 award rows, $655,045,412 (body 6,119 / $605,246,412; appendices A, B, C
467 / $5,610,000, 2,558 / $36,539,000, 835 / $7,650,000, the pots in §19). The old parse had
9,978 rows: the difference is Medicare Rights Center, $135,000, p.279 (§23). All 25 category
TOTALs tie; every initiative's rows equal what its designation statement says it designated,
except one; an independent image grid agrees with the vector grid on 9,978 rows; ink coverage
finds nothing on the page that was not read.

**What the PDF itself gets wrong (flagged, never fixed).**

- **$1, p.214.** Support Our Older Adults says "has designated $7,229,999"; its 394 rows add to
  $7,229,998. It is the only gap in the roll-up: category TOTALs $655,764,999 = body rows
  $605,246,412 + post-adoption reserves $50,518,586 + $1.
- **p.486.** The text layer reads "multi media" where the page shows "multi-media". The text layer
  is kept.

**Things a re-parse must know.** Long initiative titles wrap into a second row of the title bar
(pp.44, 168, 179). Initiative boxes have no right-hand border. On p.463 a name's trailing hyphen
runs over the border into the EIN box. A page's running sub-heading is a category name in small
type (e.g. p.116), not a category banner. Rows on the City's EIN 13-6400434 need a name check
to match the disclosure (9 rows pair different agencies by amount alone).

## 30. FY2026 transparency resolutions rebuilt from the PDFs, checked (#103) — REVIEW IN PROGRESS (2 of 24 decided)

> **Scope.** A new, checked parse of the 10 PDFs in `source/FY26/transparency-resolutions/`
> (`code/parse_transparency_v2.py`, `code/transreso/`, `config/transparency/fy2026.toml`). Its
> review record is [`research/2026-10-21-fy26-transparency-review/`](research/2026-10-21-fy26-transparency-review/README.md).
> The old `data/fy26/transparency-resolutions/*.csv` files are unchanged and stay the historical
> record (§27). Not served by the MCP.

**Result.** 4,952 rows from 388 charts (the old parse had 4,755, all of which are here). Every row
carries its resolution's number and adoption date (`resolution_number`, `resolution_date`), so a
designation can be placed in time. An independent image grid agrees with the vector grid on every
row; ink coverage finds nothing on the page that was not read.

**The FY2026 charts print no totals.** Nothing to tie. What is printed and checked instead: "Charts
1 through N" (Reso 03-10), the "Page n" labels, and red ink on every amount in parentheses.

**What the old parse missed (§9 called FY2026 "fully parsed").** 173 EINs printed without a hyphen; 21 rows on the
prior-year purpose-of-funds chart of 7 resolutions; 2 rows whose clipped text it misread; 1 row
with no EIN.

**Things a re-parse must know.** Excel clips overflowing text at the next border but leaves the
hidden letters in the PDF: read text by runs, not letters (12 cells; "Speaker's Initiat" on Reso 02
p.110 is what the page shows). Purpose-of-funds rows usually draw no border between Source and
Member. Reso 03-10 print no date and leave "Res. No." blank; numbers and dates come from Legistar
(`research/2026-07-07-legistar-links-fy21-27.md`). `fiscal_year` on the new rows is the document
year; the budget year a row changes is `budget_fiscal_year` (2023-2026), from the chart caption.

**What the PDF itself gets wrong (flagged, never fixed).** Reso 06 p.5 captions a chart "Fiscal
2023" that names a Council Member who took office in 2024 (likely 2026). Reso 01 p.67 "Operation
Backpack" prints no fiscal year. Reso 06 p.2 prints one row with no EIN.

---

## 31. FY2026 Schedule C rebuilt from the PDF, checked (#103) — REVIEW IN PROGRESS (4 of 28 decided)

> **Scope.** A new, checked parse of `source/FY26/Fiscal-2026-Schedule-C-4.pdf` with the §29
> toolkit (`code/parse_schedule_c_v2.py`, `config/schedule_c/fy2026.toml`). Its review record is
> [`research/2026-10-21-fy26-schedule-c-review/`](research/2026-10-21-fy26-schedule-c-review/README.md).
> The old `data/fy26/schedule_c/*.csv` files are unchanged and stay the historical record (§27).
> Not served by the MCP.

**Result.** 9,765 award rows, $545,669,395 (body 5,850 / $495,870,395; appendices A, B, C
473 / $5,610,000, 2,619 / $36,539,000, 823 / $7,650,000). The old parse had 9,752 rows: the 13
it lost ($8,588,150, among them Bronx Defenders $5,533,333, p.176) are all here, and nothing the
old parse had is missing. 24 of 25 category TOTALs tie; an independent image grid agrees on
9,761 rows (2 differ on a hyphen at a cell edge; 2 one-row tables it cannot see); ink coverage
finds nothing on the page that was not read.

**What the PDF itself gets wrong (flagged, never fixed).**

- **$800, p.173.** Immigrant Services prints TOTAL $86,091,341; its lines add to $86,092,141.
- **$15,000, p.98.** Cultural Immigrant Initiative says "has designated $6,798,000"; its 383 rows
  (pp.99–111) add to $6,783,000. These two are the whole roll-up gap (−$14,200).
- **Two 8-digit EINs:** p.158 "26-265183", p.379 "61081232". Clean EIN left blank.
- **p.111.** Ghetto Film School's amount is printed "75,000", without "$".
- **11 box/summary name differences** (e.g. "&" vs "and"; one summary line for three SAVE boxes,
  p.112). Rows carry the box title.

**Money in no award row.** 14 initiatives "will designate awards post-adoption" ($78,512,162);
8 CUNY/DOE initiatives are "designated directly" with no rows ($23,911,869, pp.162–164). Both are
in the initiatives table.

**Things a re-parse must know.** On portrait pages the initiative box, statement and award table
are one ruled table (p.36). A rule splits some long names into two row bands (p.130). Award
tables continue over a page without a header (pp.48, 157, 195). Some box titles wrap with the
amount on line two (p.157), or share one cell with it (pp.218, 220). The statement is worded 60
ways; the text layer splits words ("h as", "designate d"). A 5 pt sliver cell holds the first
letter of each box label on p.162. Six glyphs are unmapped (`(cid:9)`, e.g. p.344).

---

## 32. FY2025 Schedule C rebuilt from the PDF, checked (#104) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of `source/FY25/Fiscal-2025-Schedule-C-MERGE-FINAL-2.pdf` with
> the §29 toolkit (`code/parse_schedule_c_v2.py`, `config/schedule_c/fy2025.toml`). Its review
> record is
> [`research/2026-10-21-fy25-schedule-c-review/`](research/2026-10-21-fy25-schedule-c-review/README.md).
> The old `data/fy25/schedule_c/*.csv` files are unchanged and stay the historical record (§27).
> Not served by the MCP.

**Result.** 9,579 award rows, $471,876,698 (body 5,659 / $422,077,698; appendices A, B, C
470 / $5,610,000, 2,616 / $36,539,000, 834 / $7,650,000). The old parse has 9,566 rows: the 13
it lost ($9,092,588, among them Bronx Defenders $5,533,333, p.169) are all here, and nothing the
old parse had is missing. The §20 row (p.233) comes back as two awards (Corbin Hill Food Project
and Council For Unity, $50,000 each). 24 of 25 category TOTALs tie; an independent image grid
agrees on 9,577 rows (2 differ on a hyphen at a cell edge); ink coverage finds nothing on the
page that was not read.

**What the PDF itself gets wrong (flagged, never fixed).**

- **$50,000, p.115.** Education prints TOTAL $39,924,300; its lines add to $39,974,300.
- **$594,000, p.64.** CASA's statement (reserve $2,066,000 + designated $14,680,000) adds to
  $16,746,000, not its $17,340,000 box.
- **$27,000, p.167.** Immigrant Opportunities says "has designated $2,562,000"; its 31 rows add to
  $2,535,000. These three are the whole roll-up gap (−$571,000).
- **p.222.** Pride at Work's statement says "$3.2 million" designated; the box is $501,000 and
  its rows add to $451,000. **p.60.** "$4.1 million" stands for $4,091,000.
- **p.181.** Safe Horizon's EIN is printed "13-294-6970". Clean EIN left blank.
- **pp.168, 170.** Two amounts printed "$77,000.00" and "$50,000.".
- **p.202.** Parks and Recreation Services prints no summary table and no TOTAL.
- **16 box/summary name differences** (e.g. "&" vs "and"; one summary line for two SAVE boxes,
  p.102; four library lines all named "Fiscal 2025 Subsidy", p.174). Rows carry the box title.

**Money in no award row.** 16 initiatives "will designate awards post-adoption" ($50,455,000);
7 CUNY/DOE initiatives are "designated directly" with no rows ($20,011,869, pp.155–157); the
four library subsidies are "directly allocated" ($15,700,000, p.174). All are in the initiatives
table.

**Things a re-parse must know.** "Council" / "Member" are two header row bands (pp.131–144).
Some box titles have their first letter in its own cell or outside the table (pp.36, 149, 258).
Amount digits run past their cell's rule (p.222, p.260) or a box amount is cut into three cells
(p.157). p.167's name column is lost at pdfplumber's default snap (read at 1 pt). Statements
give amounts in millions ("$4.1 million"), and one sits inside a description cell (p.168). A
second box hides inside the first box's table (p.35). 17 summary-table titles; one with no title
(p.59).

---

## 33. FY2025 transparency resolutions parsed from the PDFs, checked (#104) — REVIEW NOT STARTED

> **Scope.** The first parse of the 13 PDFs in `source/FY25/transparency-resolutions/`
> (`code/parse_transparency_v2.py --fy 2025`, `config/transparency/fy2025.toml`). Its review record
> is [`research/2026-10-21-fy25-transparency-review/`](research/2026-10-21-fy25-transparency-review/README.md).
> The old parser never read FY2025, so there is no retired file. Not served by the MCP.

**Result.** 3,555 rows from 309 charts, each with its resolution's adoption date. An independent
image grid agrees on every row; ink coverage finds nothing on the page that was not read. The
charts print no totals; "Charts 1 through N" ties on the 3 resolutions that print it.

**Things a re-parse must know.** Reso 07 pp.29-30 print staff notes in a column past the `*`
column, cut at the table's right rule: only "01/" shows, the rest is in the text layer (kept in
`hidden_text`). Three chart pages print no "Page n" label (Reso 02 pp.74-75, Reso 03 p.28). Reso 11
p.6's caption has no colon. Reso 08 p.12's member header reads "Member/Borough".

**What the PDF itself gets wrong (flagged, never fixed).** Reso 07 p.18 prints a $15,000 row with
no EIN (Reso 08 p.13 takes it back and re-prints it with one). Reso 06 p.6 marks a row `***` with
no `***` footnote. Reso 02 prints the same two Black Spectrum rows under Fiscal 2025, 2024 and
2023. Reso 04 (2024-10-23) prints no resolution number, and none is known.

---

## 34. FY2025 capital and T&C, re-read from the PDFs (GitHub #104) — REVIEW NOT STARTED

> **Scope.** Its review record is [`research/2026-10-21-fy25-capital-terms-review/`](research/2026-10-21-fy25-capital-terms-review/README.md). Not served by the MCP.

Capital: 32 / 32 printed totals tie; Part I equals NYC Open Data `t474-a92g` on all 1,325 of its
FY2025 rows (2 FY2026-only amounts are not in t474). t474's FY2025 accents are cp437 mojibake (50
rows). The PDF prints 6 project IDs on two rows each, so `sub_id` is not a key. Part II carries 39
`MA` / `0N` rows ($57,657,000) and `PV CT001` ($2,500,000) that are not Council additions (meaning
unconfirmed). The PDF was edited after export on p.51. T&C: 65 conditions; the retired CSV put
headings into the text of 14, the FSR table into #16, dropped hyphens in 4, and lost units in 9.

---

## 35. FY2024 Schedule C rebuilt from the PDF, checked (#105) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of `source/FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf` with
> the §29 toolkit (`config/schedule_c/fy2024.toml`). Its review record is
> [`research/2026-10-21-fy24-schedule-c-review/`](research/2026-10-21-fy24-schedule-c-review/README.md).
> The old `data/fy24/schedule_c/*.csv` files are unchanged and stay the historical record (§27).
> Not served by the MCP.

**Result.** 9,291 award rows, $453,858,561 (body 5,380 / $404,059,561; appendices A, B, C
477 / $5,610,000, 2,616 / $36,539,000, 818 / $7,650,000). Nothing the first PDF parse had is
missing; 81 rows are new. The §20 row (p.234) comes back as two awards. 24 of 25 category
TOTALs tie. The image grid agrees on 7,844 rows; 1,447 rows sit in tables with no vertical
rules, and the pixels' horizontal rules confirm the row band of 1,438 of them.

**What the PDF itself gets wrong (flagged, never fixed).**

- **$52,935, p.63.** Criminal Justice Services prints TOTAL $28,658,710; its lines add to
  $28,711,645. The table is titled "Fiscal 2023".
- **Six statements whose reserve and rows do not make the box** (pp.109, 129, 147, 148, 176,
  181; −$60,000 to +$635,000). With p.63 they are the whole roll-up gap (+$430,904).
- **p.261.** Drama Club, Inc. is printed with Digital Girl, Inc.'s EIN 47-2288307.
- **p.135** Tax ID "TF4876222"; **p.182** "13-294-6970". Clean EIN left blank.
- **pp.130–137.** Eight landscape pages are merged out of order: their rows (NYC Cleanup's,
  $12,028,500) follow A Greener NYC's statement. Attached to NYC Cleanup, flagged.
- **p.201.** Parks prints no summary table. **15 box/summary name differences.**

**Things a re-parse must know.** 216 pages have a MediaBox starting at (−18, 18): take every
coordinate from the MediaBox corner. 70 award tables have horizontal rules only. First rows
with no rule above them (pp.41–46, 152–153). Headers printed loose above the table, or at its
bottom (pp.41–45). Statements say "will designate $N post-adoption and has designated the
following providers" with no designated amount (45 boxes). The Speaker's pages use 8.8 pt type.

---

## 36. FY2024 transparency resolutions rebuilt from the PDFs, checked (#105) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of the 9 PDFs in `source/FY24/transparency-resolutions/`
> (`code/parse_transparency_v2.py --fy 2024`, `config/transparency/fy2024.toml`). Its review record
> is [`research/2026-10-21-fy24-transparency-review/`](research/2026-10-21-fy24-transparency-review/README.md).
> The old `data/fy24/transparency-resolutions/*.csv` files are unchanged and stay the historical
> record (§27). Not served by the MCP.

**Result.** 3,303 rows from 329 charts (the old parse had 3,294, all of which are here), each with
its resolution's number and adoption date. An independent image grid agrees on every row,
including Reso 01's /Rotate 90 pages. No totals and no chart counts are printed.

**What the old parse missed.** 7 EINs printed without a hyphen, "Bronx Community Board #7", and a
row whose EIN prints as "TF4876222".

**Things a re-parse must know.** Reso 01's page labels use a no-break space ("Page\xa01"). Reso 02
p.11: a clipped "n" overlaps the next cell's text by 0.95 pt, so runs must break on overlap.
11 chart pages print no "Page n" label (Reso 02 pp.66-73, Reso 03 pp.55-57). `bbox_pt` on Reso 01
is in display coordinates in the review folder and unrotated in `data/fy24/pdf/`.

**What the PDF itself gets wrong (flagged, never fixed).** "TF4876222" as an EIN (Reso 07 p.17;
also in Schedule C; corrected by the same resolution). "#" in the `*` column (Reso 02 p.18). Two
`***` rows with no `***` footnote (Reso 01 p.55).

---

## 37. FY2024 capital and T&C, re-read from the PDFs (GitHub #105) — REVIEW NOT STARTED

> **Scope.** Its review record is [`research/2026-10-21-fy24-capital-terms-review/`](research/2026-10-21-fy24-capital-terms-review/README.md). Not served by the MCP.

Capital (an encrypted PDF with an empty user password): 32 / 32 printed totals tie; Part I equals
NYC Open Data `t474-a92g` on all 1,241 amounts. t474's FY2024 accents are UTF-8 read as cp437 (78
rows). Part II carries 29 `MA` / `0N` rows ($61,737,000) and `HL TA001` (−$40,000 on `HL RN404`),
not Council additions. The retired capital CSV drops the comma after `SPEAKER` (190 rows). T&C: the
PDF prints no condition numbers; 61 conditions in book order. The retired CSV has 59 and is
misnumbered from #44 on; 5 agency headings print no code.

---

## 38. FY2023 Schedule C rebuilt from the PDF, checked (#106) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of `source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf`
> with the §29 toolkit (`config/schedule_c/fy2023.toml`). Its review record is
> [`research/2026-10-21-fy23-schedule-c-review/`](research/2026-10-21-fy23-schedule-c-review/README.md). The old `data/fy23/schedule_c/*.csv` files are
> unchanged and stay the historical record (§27). Not served by the MCP.

**Result.** 5,925 award rows, $323,063,807 (body 1,867 / $273,264,807; appendices A, B, C
489 / $5,610,000, 2,728 / $36,539,000, 841 / $7,650,000). Nothing the first PDF parse had is
missing; 45 rows are new, including the two $5,000 Local rows §19 describes, so Appendix B is
the $36,539,000 pot. All 26 category TOTALs tie. The image grid agrees on 4,884 rows; 1,040
rows sit in tables with no vertical rules, and the pixels' horizontal rules confirm 1,028.

**What the PDF itself gets wrong (flagged, never fixed).**
- **Two boxes print a different amount from their summary line:** Low Wage Worker Support
  $120,000 vs $2,000,000 (p.83, p.81); Autism Awareness $3,166,846 vs $3,316,846 (p.86).
- **Six boxes whose rows (and reserve) don't make the box:** pp.34, 43, 53, 54, 82, 136
  (−$416,000 to +$1,100,000). Four statements round ("$14.5 million" etc., pp.42, 43, 44, 59).
  With the two above they are the whole roll-up gap (+$646,350).
- **pp.13, 175.** Asiyah Women's Center is printed with Muslims Giving Back's EIN 822712941.
- **p.213** EIN "84 -2079676"; **p.235** "87-0753479" whose hyphen the text layer reads as a
  space. Clean EIN left blank.
- **17 box/summary name differences**; "Fiscal 2022" in two statements (pp.49, 50).

**Things a re-parse must know.** A box amount printed "$ 5,000,000" (p.34) and one with no "$"
(p.92). A box drawn inside the award table above it (p.53). White-filled boxes that make a
table of names only (pp.68, 139, 140). 46 award tables have horizontal rules only. Statements
put the reserve after the providers ("... and $N will be designated post-adoption").

---

## 39. FY2023 transparency resolutions rebuilt from the PDFs, checked (#106) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of the 14 PDFs in `source/FY23/transparency-resolutions/`
> (`code/parse_transparency_v2.py --fy 2023`, `config/transparency/fy2023.toml`). Its review
> record is [`research/2026-10-21-fy23-transparency-review/`](research/2026-10-21-fy23-transparency-review/README.md).
> The old `data/fy23/transparency-resolutions/*.csv` files are unchanged and stay the historical
> record (§27). Not served by the MCP.

**Result.** 8,424 rows from 502 charts (the old parse had 8,354, all of which are here), each
with its resolution's number and adoption date. An independent image grid agrees on every row;
the ink check finds nothing outside a parsed cell. No totals and no chart counts are printed.

**What the old parse missed.** 61 EINs printed without a hyphen and 9 ordinary rows.

**Things a re-parse must know.** Captions vary: "CHART 41:" (no "#", Reso 01 p.81), "- FY 2023"
(Reso 01 p.66, Reso 09 pp.21–25), "(cpntinued)" (Reso 03 p.20), and a chart's first page marked
"(continued)" (Reso 08 p.32). Empty drawn rows sit under some tables (Reso 01 p.67, Reso 03 p.83,
Reso 06 p.53). The `***` footnote has a second wording. 4 chart pages print no "Page n" label
(Reso 08 p.44, Reso 09 pp.29–31).

**What the PDF itself gets wrong (flagged, never fixed).** 18 `***` rows with no `***` footnote on
the page (Reso 03–08). The City's EIN 13-6400434 printed for Fort Greene Council, Inc. (Reso 11
p.19). Two $0 rows (Reso 07 p.27).

---

## 40. FY2023 capital and T&C, re-read from the PDFs (GitHub #106) — REVIEW NOT STARTED

> **Scope.** Its review record is [`research/2026-10-21-fy23-capital-terms-review/`](research/2026-10-21-fy23-capital-terms-review/README.md). Not served by the MCP.

Capital: 32 / 32 printed totals tie; Part I equals NYC Open Data `t474-a92g` on all 1,411 of its
FY2023 amounts, and adds the one t474 lost to a broken record (`E CN136`, $150,000), so t474's
$879,526,000 becomes the PDF's $879,676,000. t474's FY2023 accents are UTF-8 read as cp437 (74
rows). 15 Part I rows carry `RR` IDs ($22,633,000, no sponsor, 4 on borough `A`). Part II carries
39 `MA` / `0N` rows ($78,861,000), not Council additions. Against OMB's July 2022 adopted budget,
129 of 130 lines match; `E D001` differs by $5,400,000. The retired capital CSV drops the comma
after `SPEAKER` (265 rows). T&C: the PDF prints no condition numbers; 60 conditions in book order,
as the retired CSV numbered them; it put the FSR table into condition 24's text.

---

## 41. FY2022 Schedule C rebuilt from the PDF, checked (#107) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of `source/FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf` with
> the §29 toolkit (`config/schedule_c/fy2022.toml`). Its review record is
> [`research/2026-10-21-fy22-schedule-c-review/`](research/2026-10-21-fy22-schedule-c-review/README.md). The old `data/fy22/schedule_c/*.csv` files are
> unchanged and stay the historical record (§27). Not served by the MCP.

**Result.** 5,732 award rows, $285,155,968 (body 1,550 / $235,356,968; appendices A, B, C
510 / $5,610,000, 2,790 / $36,539,000, 882 / $7,650,000). Nothing the first PDF parse had is
missing; 71 rows are new, among them Art as a Catalyst for Change (40 rows, $720,000, pp.84–85),
which the old parse dropped. All 25 category TOTALs tie. The image grid agrees on 5,616 rows.

**What the PDF itself gets wrong (flagged, never fixed).**
- **p.57.** Public Health Funding Backfill's box prints $4,467,933; its summary line $4,667,933.
- **Six statements hold a reserve while their rows add to the whole box** (pp.34 ×2, 39, 44,
  85, 119; $290,000 to $1,650,000); three more whose reserve and rows make neither (pp.54, 58,
  115); "$3 million" for $3,013,205 (p.36). With p.57 they are the whole roll-up gap
  (+$6,545,340).
- **p.37** "$3,462,000 million" (read as $3,462,000). **Five EINs of the wrong length**
  (pp.48, 52, 79, 80, 82). **16 box/summary name differences.**

**Things a re-parse must know.** A four-column table with a "Program" column (pp.84–85). Rows
drawn as one wide cell each (pp.117–118). "TOTAL:" (p.32). A box drawn inside an award table
(p.81). The ink check skips the first row of a table with no header row of its own.

---

## 42. FY2022 transparency resolutions rebuilt from the PDFs, checked (#107) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of the 14 PDFs in `source/FY22/transparency-resolutions/`
> (`code/parse_transparency_v2.py --fy 2022`, `config/transparency/fy2022.toml`). Its review
> record is [`research/2026-10-21-fy22-transparency-review/`](research/2026-10-21-fy22-transparency-review/README.md).
> The old `data/fy22/transparency-resolutions/*.csv` files are unchanged and stay the historical
> record (§27). Not served by the MCP.

**Result.** 7,918 rows from 424 charts (the old parse had 7,768, all of which are here), each
with its resolution's number and adoption date. An independent image grid agrees on 7,917.
No totals and no chart counts are printed. 11 of 14 resolutions add new money (+$23.0M in all,
mostly "Pandemic Support for Human Service Providers").

**What the old parse missed.** The 91 "Beating Hearts" rows (no amount column), 45 EINs printed
without a hyphen, 12 ordinary rows, and two rows with no usable EIN.

**Things a re-parse must know.** Most of Reso 02's pages have a media box starting at (−8.39, −8.39): shift the page
image, and write boxes on the rendered page. "Beating Hearts" charts have no amount. Reso 03
chart #48 prints cents. Captions repeat without "(continued)" (Reso 01 pp.51–54, Reso 02 p.35),
print the wrong number (Reso 07 p.34) or "(continued)" on a first page (Reso 02 pp.80, 124).
Reso 09 p.38 draws a hidden line over an EIN. Reso 02 p.106 is only a spilled footnote.
25 chart pages print no "Page n" label.

**What the PDF itself gets wrong (flagged, never fixed).** A row with no member, organization or
EIN, ($1,613,026) DYCD (Reso 03 p.32). "FY22 05075" as an EIN (Reso 07 p.21). "#" in the `*`
column (Reso 03 p.29). Six `***` rows with no `***` footnote (Reso 03 p.16, Reso 08 p.16, Reso 09
p.38).

---

## 43. FY2022 capital and T&C, re-read from the PDFs (GitHub #107) — REVIEW NOT STARTED

> **Scope.** Its review record is [`research/2026-10-21-fy22-capital-terms-review/`](research/2026-10-21-fy22-capital-terms-review/README.md). Not served by the MCP.

Capital: 34 / 34 printed totals tie; Part I equals NYC Open Data `t474-a92g` on all 1,490 of its
FY2022 amounts and adds the one t474 lost to a broken record (`E CN673`, $55,000), so t474's
$704,440,000 becomes the PDF's $704,495,000; all 149 PDF budget lines equal OMB's July 2021 adopted
release. The PDF prints IDs outside the usual shape (`TANC1`, `KBP01`, `MBP01`), 4 Borough
President rows in Part II only (one −$72,000), 28 sponsor cells that name a vacant district (`CD
22`, `CD 48`), a lower-case borough (`P CN039`), and `AMPREY-SAMUEL` for Ampry-Samuel (25 rows).
The retired capital CSV drops the comma after `SPEAKER` (236 rows) and moves wrapped sponsors into
titles (21). T&C: no printed numbers or page furniture; 50 conditions in book order; the retired
CSV lost condition 26 (`Department of Education (40)`) and split 28, so its 26–28 are misaligned;
the FSR table's months are out of order as printed.

---

## 44. FY2021 Schedule C rebuilt from the PDF, checked (#108) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of `source/FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf`
> with the §29 toolkit (`config/schedule_c/fy2021.toml`). Its review record is
> [`research/2026-10-22-fy21-schedule-c-review/`](research/2026-10-22-fy21-schedule-c-review/README.md). The old `data/fy21/schedule_c/*.csv` files are
> unchanged and stay the historical record (§27). Not served by the MCP.

**Result.** 6,179 award rows, $262,477,792 (body 1,869 / $212,678,792; appendices A, B, C
514 / $5,610,000, 2,902 / $36,539,000, 894 / $7,650,000). Nothing the first PDF parse had is
missing; 69 rows are new ($11,149,604), among them 36 of Art as a Catalyst for Change's 40 rows. All 26
category TOTALs tie. The image grid agrees on 5,744 rows.

**What the PDF itself gets wrong (flagged, never fixed).**
- **p.122** prints the box "$477,00" (its summary line $477,000).
- **Three statements hold a reserve while their rows add to the whole box** (pp.44, 93, 107);
  p.39's rows are $1 over; p.55 "$4.6 million" for $4,659,000. They are the whole roll-up gap
  (+$129,070).
- **Six 8-digit EINs** (pp.64, 65, 87, 89, 90, 91; p.60 prints two of them correctly);
  Congregation Beit Simchat Torah printed with two EINs (pp.61, 63). **16 box/summary name
  differences**; p.122's summary title says "Fiscal 2020".

**Things a re-parse must know.** Award headers printed outside the table's rules (pp.35–128).
Sub-headings inside an award table (pp.70–72). 8.9 pt edge columns holding first letters and
last digits (pp.105–106). A box amount outside its box (p.98); an empty band over a box (p.84).

---

## 45. FY2021 transparency resolutions rebuilt from the PDFs, checked (#108) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of the 8 PDFs in `source/FY21/transparency-resolutions/`
> (`code/parse_transparency_v2.py --fy 2021`, `config/transparency/fy2021.toml`). Its review
> record is [`research/2026-10-21-fy21-transparency-review/`](research/2026-10-21-fy21-transparency-review/README.md).
> The old `data/fy21/transparency-resolutions/*.csv` files are unchanged and stay the historical
> record (§27). Not served by the MCP.

**Result.** 4,500 rows from 237 charts (the old parse had 4,463, all of which are here), each
with its resolution's number and adoption date. An independent image grid agrees on all 4,500.
No totals and no chart counts are printed. 6 of 8 resolutions net to $0; Reso 06 adds $500,000
and Reso 07 $17,000,000 (mostly the Food Pantries Initiative).

**What the old parse missed.** The 28 "Beating Hearts" rows (no amount column), 8 EINs printed
without a hyphen, and one row with no EIN.

**Things a re-parse must know.** The `***` footnote has a third wording ("Technical adjustment
to designation made in a previous Transparency Resolution"). "Beating Hearts" charts have no
amount. Reso 02 p.20 prints "(continued)" on a chart's first page. 15 chart pages print no
"Page n" label.

**What the PDF itself gets wrong (flagged, never fixed).** A row with no member and no EIN,
"Department of Cultural Affairs **" ($10,000) DCLA (Reso 02 p.29).

---

## 46. FY2021 Terms & Conditions, re-read from the PDF (GitHub #108) — REVIEW NOT STARTED

> **Scope.** Its review record is [`research/2026-10-21-fy21-capital-terms-review/`](research/2026-10-21-fy21-capital-terms-review/README.md). Not served by the MCP.

46 conditions, unnumbered and with no page furniture, numbered here in book order; all 111 unit and
budget-line heading lines placed; the FSR table (p.8) agrees under both lattices. The retired
`data/fy21/terms` CSV has the same 46 conditions in order but keeps only the first agency of the
four two-agency conditions (#1 ACS/DOC, #12 DOE/SCA, #28 HPD/Capital Budget, #37 DYCD/DCAS), files
DOC's units under ACS's code, puts capital budget lines in `units`, folds the FSR table into #19's
text and drops a printed hyphen (#23). The PDF prints SCA with DOE's code (040). FY2021 has no
capital supporting detail in `source/`.

---

## 47. FY2020 Schedule C rebuilt from the PDF, checked (#109) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of `source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf` with
> the §29 toolkit (`config/schedule_c/fy2020.toml`). Its review record is
> [`research/2026-10-22-fy20-schedule-c-review/`](research/2026-10-22-fy20-schedule-c-review/README.md). The old `data/fy20/schedule_c/*.csv` files are
> unchanged and stay the historical record (§27). Not served by the MCP.

**Result.** 7,921 award rows, $336,750,073 (body 3,528 / $286,951,073; appendices A, B, C
510 / $5,610,000, 2,986 / $36,539,000, 897 / $7,650,000). Nothing the first PDF parse had is
missing; 5,080 rows are new ($77,987,688), 4,180 of them in the appendices: #59's FY2020
loss, recovered from the PDF. All 27 category TOTALs tie. §20's one FY2020 merged row comes
back as two awards. The image grid agrees on 6,380 rows.

**What the PDF itself gets wrong (flagged, never fixed).**
- **p.46**: three EINs printed one row off (Foundling, North Brooklyn Coalition, Safe Horizon).
- **p.46** rows $200,000 short of the box; **p.45** rows $2,000 over; five rounded statements;
  the roll-up gap (−$219,300) is these.
- **Three EINs of the wrong length** (pp.134 ×2, 162). **16 box/summary name differences**;
  a SAVE box for the whole initiative over its parts' boxes (p.79).

**Things a re-parse must know.** Amounts with no "$" in member tables and appendices. Many
tables ruled with horizontal lines only, some with a member column (pp.38–41), two or three rows
to a band (pp.84, 102, 187), a header in one cell (pp.162–164). Banners drawn twice (p.97) or
padded (p.111). A summary amount whose text is doubled (p.145). Page-origin offset pp.166–177.

---

## 48. FY2020 transparency resolutions rebuilt from the PDFs, checked (#109) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of the 8 PDFs in `source/FY20/transparency-resolutions/`
> (`code/parse_transparency_v2.py --fy 2020`, `config/transparency/fy2020.toml`). Its review
> record is [`research/2026-10-21-fy20-transparency-review/`](research/2026-10-21-fy20-transparency-review/README.md).
> The old `data/fy20/transparency-resolutions/*.csv` files are unchanged and stay the historical
> record (§27). Not served by the MCP.

**Result.** 5,396 rows from 300 charts (the old parse had 5,319, all of which are here), each
with its resolution's number and adoption date. An independent image grid agrees on all 5,396.
No totals and no chart counts are printed. Reso 03, 05 and 07 add new money (+$3.0M in all).

**What the old parse missed.** The 73 "Beating Hearts Initiative" rows (no amount column) and 4
EINs printed without a hyphen.

**Things a re-parse must know.** Captions print "Chart" and "Chart # 44", "(continued)" before
the fiscal year (SU-CASA), and "CHART #:" with no number (Reso 06 pp.25–26). Purpose-of-funds
charts have a Source column and initiative names that span Source and Member. "Organization -
School" is a header label. "Beating Hearts Initiative" charts have no amount and no note.

**What the PDF itself gets wrong (flagged, never fixed).** Two DoVE charts are $1 off inside
themselves (Reso 01 chart #10 +$1, Reso 04 chart #11 −$1: MOCJ $110,814 against $110,815
taken back). 11 `***` rows with no `***` footnote (Reso 02 pp.16, 23; Reso 04 p.20; Reso 05
p.22). "Millennium Development-Millennium Youth Services" printed without spaces around the
separator (Reso 05 p.67).

---

## 49. FY2020 capital supporting detail, re-read from the PDF (GitHub #109) — REVIEW NOT STARTED

> **Scope.** Its review record is [`research/2026-10-21-fy20-capital-terms-review/`](research/2026-10-21-fy20-capital-terms-review/README.md). Not served by the MCP.

The book is Part I only (no Part II or III), encrypted with an empty password and rotated. 24 / 24
printed totals tie (1,663 projects, $701,210,000 FY2020, $5,000,000 FY2021). Part I equals NYC Open
Data `t474-a92g` on all 1,660 of its amounts and adds the two t474 lost to broken records (`E
CN817` $170,000, `E CN832` $300,000), so t474's $700,740,000 becomes the PDF's total. Against OMB's
adopted release, 184 / 191 lines match and OMB carries $7,353,000 more on 11 lines. The PDF prints
three lower-case `r` boroughs, IDs outside the usual shape (`CNA02`, `NC02`, `CN90`, the last
twice), an all-zero row, and `AMPREY-SAMUEL` (31 rows). The retired capital CSV drops the comma
after `SPEAKER` (219 rows) and moves wrapped sponsors into titles (26). FY2020 has no Terms &
Conditions in `source/`.

---

## 50. FY2019 Schedule C rebuilt from the PDF, checked (#110) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of `source/FY19/Fiscal-2019-Schedule-C-Final-Report.pdf` with
> the §29 toolkit (`config/schedule_c/fy2019.toml`). Its review record is
> [`research/2026-10-22-fy19-schedule-c-review/`](research/2026-10-22-fy19-schedule-c-review/README.md). The old `data/fy19/schedule_c/*.csv` files are
> unchanged and stay the historical record (§27). Not served by the MCP.

**Result.** 5,995 award rows, $248,436,176 (body 1,551 / $198,637,176; appendices A, B, C
523 / $5,610,000, 3,016 / $36,539,000, 905 / $7,650,000). Nothing the first PDF parse had is
missing except 27 rows of a partner list that are not awards (below); 5,176 rows are new
($71,772,745), 4,444 of them in the appendices: #59's FY2019 loss, recovered from the PDF. All
27 category TOTALs tie. **All 39 of §20's FY2019 merged rows come back as separate awards (82
awards).** The image grid agrees on 5,090 rows.

**What the PDF itself does (flagged, never fixed).**
- **A "*" column** (p.10: review not complete at adoption) on 304 rows; kept as a row flag.
- **Six post-adoption reserves printed again as City-agency rows** (13-6400434; pp.38, 43, 73,
  78, 82, 125): those boxes' rows add to the box, not the box less the reserve.
- **Ending the Epidemic** (p.62): rows $150,000 more than the box less its reserve.
- **A partner list under CWE's Jobs to Build On row** (pp.105–106, 28 rows, $4,463,500 vs the
  row's $5,154,200): read as no award.
- **H+H printed with the City's EIN** in Viral Hepatitis Prevention (p.66, 3 rows).
- **15 box/summary name differences**; a SAVE box for the whole initiative over its parts' boxes
  (p.49).

**Things a re-parse must know.** Amounts with no "$" in member tables and appendices. A "*"
column. Headers loose above h-rule tables (pp.42, 125). A statement label centred between its
two lines (pp.43, 105). A box title's last letter in its own cell (p.74). Two summary tables
titled without "Council" (pp.41, 102).

---

## 51. FY2019 transparency resolutions rebuilt from the PDFs, checked (#110) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of the 11 PDFs in `source/FY19/transparency-resolutions/`
> (`code/parse_transparency_v2.py --fy 2019`, `config/transparency/fy2019.toml`). Its review
> record is [`research/2026-10-22-fy19-transparency-review/`](research/2026-10-22-fy19-transparency-review/README.md).
> The old `data/fy19/transparency-resolutions/*.csv` files are unchanged and stay the historical
> record (§27). Not served by the MCP.

**Result.** 7,207 rows from 445 charts (the old parse had 7,090, all of which are here), each
with its resolution's number and adoption date. An independent image grid agrees on all 7,207.
No totals and no chart counts are printed. Reso 04, 05, 06, 08 and 09 add new money (+$4.7M in
all); Reso 02 takes back $144,999 more than it gives.

**What the old parse missed.** The 112 "Beating Hearts Initiative" rows (no amount column),
Reso 01's two "All Allocations" rows (EIN "Various", $4,090,000 each way), 2 EINs printed
without a hyphen and 1 followed by a hidden tab glyph.

**Things a re-parse must know.** On 21 pages (Reso 03, 04, 07) text wraps to more lines than
its row is tall and is drawn across the row's rules: read it as one block per cell, or wrapped
lines land in the next row ("IGnrce.enwich House") or fall off the table. Some rows are drawn
column by column. Reso 01–07 and 11 print "CHART 1:" with no "#". Reso 01 p.108 prints chart
#56's first page as "CHART 55". Reso 09's bold header capitals rise above their text boxes.

**What the PDF itself gets wrong (flagged, never fixed).** Reso 01 p.1 is dated July 17, 2018;
Legistar says adopted July 18. One DoVE chart is $1 off inside itself (Reso 02 chart #8). 4 `**`
rows with no `**` footnote (Reso 04 p.19). "Neighborhood SC-Catholic Charities" printed without
spaces around the separator (Reso 07 p.30).

---

## 52. FY2019 capital supporting detail, re-read from the PDF (GitHub #110) — REVIEW NOT STARTED

> **Scope.** Its review record is [`research/2026-10-22-fy19-capital-terms-review/`](research/2026-10-22-fy19-capital-terms-review/README.md). Not served by the MCP.

The book is the Council's database printed from Excel (every cell ruled; no agency totals, no Part
II or III, no summary page), read from its vector grid and checked against the image grid. 1,625
rows; its one total row (no label, no count) ties on all four years: $614,910,000 FY2019,
$15,900,000 FY2020. It equals NYC Open Data `t474-a92g` on all 1,628 amounts and all 1,625 titles.
Sponsors are printed as council-district codes with a key on pp.54–55; one row disagrees with t474
(`HW CN030`, p.40: CD 49 Rose in the PDF, 31 Richards in t474, title "DOT REPAVING IN DISTRICT
31"). The PDF prints three lower-case `k` boroughs, a two-digit ID (`HL NC57`) and six IDs used
twice (`LB CN001`–`LB CN006`). Against OMB's adopted release, 165 / 176 lines match and OMB carries
$15,460,000 more on 11 lines. FY2019 has no Terms & Conditions in `source/`.

---

## 53. FY2018 Schedule C rebuilt from the PDF, checked (#111) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of
> `source/FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf` with the §29 toolkit
> (`config/schedule_c/fy2018.toml`). Its review record is
> [`research/2026-10-22-fy18-schedule-c-review/`](research/2026-10-22-fy18-schedule-c-review/README.md).
> The old `data/fy18/schedule_c/*.csv` files are unchanged and stay the historical record
> (§27). Not served by the MCP.

**Result.** 5,906 award rows, $203,804,505 (body 1,420 / $154,005,505; appendices A, B, C
537 / $5,610,000, 3,054 / $36,539,000, 895 / $7,650,000). Everything the first parse had is
here except 27 rows of a partner list that are not awards; 5,031 rows are new ($101,056,774),
Appendices B and C among them: #59's FY2018 loss. Appendix A's amounts with cents are read
as whole dollars (§21 `fy18_aging_shift` does not arise). **All 94 of §20's FY2018 merged rows
come back as separate awards (224 awards).** The image grid agrees on 5,260 rows.

**What the PDF itself does (flagged, never fixed).**
- **Fiscal conduit columns**: 50 rows print one; kept in the review file.
- **Good Shepherd Services printed with another organization's EIN** (p.55, 46-1227433).
- **Two reserves printed again as City-agency rows** (pp.36, 101); **six boxes whose rows do
  not make them** (pp.57, 80, 85, 95, 124, 127); Community Development's TOTAL $100,000 over
  its lines (p.38); Merit-Based Scholarships' box $75,331 over its summary line (p.69); Crisis
  Management System's whole box $12,734 over its parts (p.93).
- **A partner list under CWE's Jobs to Build On row** (p.106, 28 rows): read as no award.
- **24 box/summary name differences**; boxes for the whole SAVE and Crisis Management System
  over their parts' boxes, the parts' titles printed above their tables.

**Things a re-parse must know.** Appendix A's "$N.00" amounts; TOTAL rows inside award tables;
box titles above their tables (pp.53, 94–97); a row between two ruled tables (p.107); six
pages where the text layer glues an EIN to the name before it; pp.115–119 blank.

---

## 54. FY2018 transparency resolutions rebuilt from the PDFs, checked (#111) — REVIEW NOT STARTED

> **Scope.** A new, checked parse of the 12 PDFs in `source/FY18/transparency-resolutions/`
> (`code/parse_transparency_v2.py --fy 2018`, `config/transparency/fy2018.toml`). Its review
> record is [`research/2026-10-22-fy18-transparency-review/`](research/2026-10-22-fy18-transparency-review/README.md).
> The old `data/fy18/transparency-resolutions/*.csv` files are unchanged and stay the historical
> record (§27). Not served by the MCP.

**Result.** 5,558 rows from 400 charts, each with its resolution's number and adoption date, and,
where printed, the fiscal conduit and its EIN (63 rows). An independent image grid agrees on all
5,558. No totals and no chart counts are printed. Reso 08 and 10 add new money (+$1.4M);
Reso 05 takes back $500,000 more than it gives.

**What the old parse got wrong.** It missed 194 rows (136 "Beating Hearts Initiative" rows, 48
more with a hyphenless EIN, 2 "All Allocations", 8 others, most next to hidden text) and misread one EIN (Reso 04
p.56, Vietnam Veterans of America: 21-2629339 for 11-2629339).

**Things a re-parse must know.** Reso 01 is dated June 21, 2017, before Fiscal 2018 began, and
changes the FY2018, 2017 and 2016 budgets. 95 chart pages print fiscal conduit columns. Four
header rows print no labels; eight boxes round resolution text look like tables. Some `***`
footnotes explain one chart over several lines. Amounts print cents, and four print no "$".

**What the PDF itself gets wrong (flagged, never fixed).** Police Athletic League's two +$20,000
purpose rows have no negative (Reso 05 p.60). One organization under two EINs in a pair (Reso 04
p.56). Four conduit EINs print as "#########" or 8 digits. 6 `**` rows on a page with no
footnotes (Reso 05 p.23).

---

## 55. FY2018 capital supporting detail and Terms & Conditions, re-read from the PDFs (GitHub #111) — REVIEW NOT STARTED

> **Scope.** Its review record is [`research/2026-10-22-fy18-capital-terms-review/`](research/2026-10-22-fy18-capital-terms-review/README.md). Not served by the MCP.

The capital book, filed as `FY18-Sec254-Capital-ResoA-…pdf`, is the §254 supporting detail, Parts
I–III (encrypted with an empty password, no summary page). It is the only source for FY2018 Council
capital (§26): 1,485 Part I projects, $575,000,000 FY2018. All 35 printed `TOTALS FOR` lines tie on
count and all four years; Part II and Part III tie to each other and to Part I. There is no outside
source to compare with. 15 rows name the sponsor `DISTRICT 28`; Part II adds 52 `MA` and 3 `TA`
rows not in Part I. The T&C have 33 unnumbered conditions, one a page, all heading lines placed;
the retired `data/fy18/terms` CSV has the same 33 but folds the FSR table into #14's text, drops
two line-end hyphens and files budget-line headings as units.
