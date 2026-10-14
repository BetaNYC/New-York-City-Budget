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
2. **The aging ($5,610,000) and youth ($7,650,000) sub-pots are *exactly* constant every year**, and the local sub-pot varies by ≤ $10,000 (a seat vacancy / rounding). These are the Council's standing **equal-per-district** aging, local, and youth initiatives — a fixed citywide aggregate distributed across a recipient set that changes annually. The flatness is the *point* of these programs, not a parsing defect.

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
appendix CSVs (what the MCP indexes). The disclosure-built appendix sidecar is excluded as
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
  archived copies (2016-12 and 2025-02) are identical, so this is what the Council published.
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
  FY2011 13, FY2012 8). FY2011 and FY2012 store 150 EINs as numbers that lost a leading zero
  (3 and 147), re-padded as in FY2013.
- **Sub-cent amounts:** FY2009 carries 858 amounts with fractions (e.g. `7481.296758`), FY2011
  205, FY2012 85; 483, 30 and 28 of them past the cent (audit E2). Kept as stored; Open Data
  rounds them (to cents through FY2011, to dollars from FY2012), which is what `od_match` records.
- **Council member values** (`council_member_type`, crosswalk): two rules were extended, both
  generic and tested, never a per-name decision. A printed generational suffix must match
  Legistar's (`Vallone, Jr` is Peter F. Vallone, Jr., 5271, never Paul A. Vallone); a surname
  matches with spaces ignored when no exact surname exists (`DeBlasio` → Legistar's `de Blasio`,
  5286). FY2009 prints Thomas White, Jr. both as `White` and `White, Jr` (both 6273). Still
  `unresolved`, deliberately: `CC` (FY2009 240, FY2011 271, FY2012 252 rows; also FY2013 240),
  the two-letter borough codes `BK` 18, `BX` 19, `MN` 54, `QN` 46 (FY2009), and three multi-member
  values (`Barron & Eugene`, `Lappin, Koppell/Citywide`, and a nine-member FY2011 list, 51 rows).
  Open Data spells `CC` as `Speaker` and `QN` as `Queens Delegation`; per #89 B6 that is
  evidence, not the answer, so the reading is a question for the maintainer.
- **Exact copies** are many more in FY2009 (97 groups, 373 rows; §22 table) than in any later
  year. Kept and flagged as in every year.
- **Duplicate Open Data MOCS IDs.** `od_mocs_id` repeats on two FY2009 pairs because Open Data
  repeats the ID: `FY09 Not an Award` (§24) and `FY09 2039`.
