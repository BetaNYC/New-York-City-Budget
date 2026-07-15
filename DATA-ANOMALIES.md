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
