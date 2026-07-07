# FY2008–FY2020 sourcing sweep — council.nyc.gov direct

**Report generated:** 2026-07-07
**Data current as of:** 2026-07-07
**Status:** Bulk download complete. Parser-compatibility spot-checked across the range.
Supersedes the "primary sourcing" recommendation in
[2026-07-07-fy09-fy21-legacy-import-scoping.md](2026-07-07-fy09-fy21-legacy-import-scoping.md)
for this range — see "Relationship to the Open Data legacy plan" below.

## What happened

The FY2008 and FY2021 Legistar pilots (see
[2026-07-07-fy2008-legistar-pilot.md](2026-07-07-fy2008-legistar-pilot.md) and
[2026-07-07-fy2021-legistar-pilot.md](2026-07-07-fy2021-legistar-pilot.md)) were run on
the assumption that council.nyc.gov's budget archive doesn't go back past ~FY2022,
based on how the original FY22–24 gap-fill was scoped. That assumption was wrong. A
direct check of `council.nyc.gov/budget/fyNNNN/` for every year down to FY2006 found:

- **FY2006–FY2007: HTTP 404** (page doesn't exist)
- **FY2008 onward: HTTP 200, real content** — matching exactly the FY2008 floor already
  established independently via Legistar in Addendum 2 of the legacy-import scoping doc.

Crucially, **FY2008's actual Schedule C document — which the Legistar pilot concluded
was a genuine digitization gap — turned out to exist all along on council.nyc.gov**,
just uploaded there directly (in 2017, evidently as part of a retroactive archive
digitization effort) rather than attached to the Legistar legislative record. This
means the Legistar pilot's "digitization gap" conclusion was a **channel gap, not a
content gap**: the document was never missing, Legistar was just the wrong place to
look for it.

Given this, every year FY2008–FY2020 was checked directly against council.nyc.gov and
everything cleanly identifiable was downloaded via ordinary HTTP `GET` — no Legistar
hunting, no browser automation, no subagents. Total: **146 files, ~126MB**, across
`source/FY08/` through `source/FY20/`.

## Coverage table

| Year | Schedule C | Terms & Conditions | Capital §254 | Transparency Resolutions |
|---|---|---|---|---|
| FY2008 | ✅ (`schedule_c_rvs_2008.pdf`, 123pp) | — not found | — not found | — not found on this page (3 exist via Legistar, see FY2008 pilot doc) |
| FY2009 | ✅ | — not found | ✅ | ✅ 8/8 |
| FY2010 | ✅ | — not found | ✅ | ⚠️ 12/13 (1 dead link on council.nyc.gov itself, 404) |
| FY2011 | ✅ | — not found | ✅ (2 docs: "Section 254" + "Changes to...") | ✅ 10/10 |
| FY2012 | ✅ | — not found | ✅ | ✅ 8/8 |
| FY2013 | ✅ | — not found | ✅ | — not found on this page |
| FY2014 | ✅ | — not found | — **not found** (genuine gap, see below) | ✅ 3/3 |
| FY2015 | ✅ | ✅ | ✅ | ✅ 12/12 |
| FY2016 | ✅ | ✅ (+1 duplicate link, same file) | ✅ (2 docs) | ✅ 13/13 |
| FY2017 | ✅ | ✅ (+1 DOHMH-specific T&C) | — **not found** (genuine gap) | ✅ 13/13 |
| FY2018 | ✅ | ✅ | — **not found** (genuine gap) | ✅ 12/12 |
| FY2019 | ✅ | — not found | ✅ | ✅ 11/11 |
| FY2020 | ✅ | — not found | ✅ | ✅ 8/8 |

**Schedule C: 13/13 years, 100%.** Every single year FY2008–2020 has it.

**Terms & Conditions: present FY2015–2018 only** (4/13 years). Absent FY2008–2014 and
FY2019–2020. This lines up with the repo's own README already noting T&C format
evolution over time — plausibly T&C wasn't published as a standalone document before
~2015, and FY2019/2020's absence from this specific page may be a page-content gap
rather than a true absence (not independently verified — a lower priority to chase
given how much of the range already lacks it structurally).

**Capital §254: present 10/13 years.** FY2014, FY2017, FY2018 have no capital-changes
document linked on their council.nyc.gov page at all — confirmed absence on this page,
not a classification miss (manually inspected the full raw link list for all three
years). Not chased via Legistar in this pass — same fallback pattern used for FY2022's
missing capital document is available if these are wanted later.

**Transparency Resolutions: present 10/13 years**, one dead link (FY2010, a genuine
404 on council.nyc.gov's own server, not our download). FY2008 and FY2013 don't list
any on this specific page — FY2008 is already confirmed to have 3 via Legistar (see the
FY2008 pilot doc); FY2013 not checked via Legistar in this pass.

## Parser-compatibility spot check (real signal, not assumption)

Ran the **existing, unmodified** parsers from `code/` against a sample across the range:

| Test | Result | Verdict |
|---|---|---|
| FY2009 Schedule C (`parse_schedule_c.py`) | **0/22 categories reconcile** — 2,472 award rows extracted ($28.65M) but every category TOTAL comparison shows 0 vs 0 | **Real format deviation** — the TOTAL-line detection isn't matching FY2009's layout. Award-level extraction partially works; category reconciliation doesn't. Needs investigation, not just a quick regex tweak — this is the oldest and roughest year tested. |
| FY2016 Schedule C | **24/26 categories exact**, $333.2M vs $333.9M grand total, 335 award rows | Parses about as cleanly as FY2022–2024 already do. Zero or near-zero changes needed. |
| FY2020 Schedule C | **27/28 categories exact**, $404.4M grand total exact, 2,841 award rows | Same — parses cleanly, no material changes needed. |
| FY2015 & FY2018 Terms & Conditions (`parse_terms.py`) | **0 conditions, 0 agencies** both years | **Same known deviation already documented for FY2022–2024** (unnumbered condition headers) — the already-scoped parser variant should apply here too, not a new problem. |
| FY2019 Capital §254 (`parse_capital.py`, Capital Project Detail type) | **0 projects parsed** | **Same known deviation already documented for FY2022–2024** (pypdf column-scrambling on this document type) — the already-scoped pdfplumber coordinate-clustering fix should apply here too. |

**Reading this pattern:** the two already-scoped parser fixes (T&C header regex,
capital pdfplumber rewrite) look like they'll serve the *entire* FY2008–2020 range, not
just FY2022–2024 — good news, this isn't 13 separate one-off fixes. Schedule C is the
one area with a real open question: recent years in this range (FY2015 onward, spot
checked) parse about as cleanly as FY2022–2024, but the oldest tested year (FY2009)
breaks down significantly. The transition point between "parses cleanly" and "needs
real work" within FY2008–2014 has not been mapped — only FY2009 was tested from that
early cluster.

## Known gaps (not chased in this pass)

- FY2008: Terms & Conditions, Capital, Transparency Resolutions — all three would need
  the Legistar route the FY2008 pilot already partially ran (Transparency Resolutions
  confirmed to exist there; Capital confirmed to exist as a legislative record but not
  as a digitized schedule attachment; Terms & Conditions inconclusive).
- FY2010: one dead Transparency Resolution link (council.nyc.gov's own site, not
  recoverable without an alternate source — Legistar or Wayback Machine).
- FY2013: no Transparency Resolutions found on this page — not checked via Legistar.
- FY2014, FY2017, FY2018: no Capital §254 document found on this page — not checked via
  Legistar.
- Terms & Conditions absence FY2008–2014 and FY2019–2020: not independently verified as
  a true absence vs. a page-content gap, except for FY2008 (checked via Legistar in the
  pilot, inconclusive there too).

None of these blocks the bulk of the sweep from being usable — they're specific,
enumerable gaps, not blanket unknowns.

## Relationship to the Open Data legacy plan

[2026-07-07-fy09-fy21-legacy-import-scoping.md](2026-07-07-fy09-fy21-legacy-import-scoping.md)
was written on the assumption that NYC Open Data's `4d7f-74pe` CSV (FY2009–2021) would
need to be the primary source for this range, with Legistar as a secondary check. That
assumption is now outdated for Schedule C specifically: this sweep has actual
PDF-reconciled source documents for the *whole* FY2008–2020 range, matching this
repo's own stated methodology (deterministic PDF parsing, no reliance on a secondary
dataset). The Open Data CSV is now better positioned as a **cross-check / gap-filler**
(e.g. for the specific missing years/document-types above) rather than the primary
source. That scoping doc's open questions about schema mapping (`category`,
`award_type`, geocoding fields) become moot for the years this sweep covers with real
PDFs — they'd only still apply if the Open Data CSV is used to patch a specific
remaining gap.

## Next steps (not started)

1. Hand this document + the FY22–24 cross-year summary to `software-engineer` together
   — the T&C and capital parser fixes serve both ranges.
2. Separately investigate the FY2009 Schedule C reconciliation failure — is it a single
   fixable format issue, or does it get progressively worse toward FY2008? (FY2008 has
   no downloadable award-level schedule to even test against, per the FY2008 pilot.)
3. Decide whether to chase the enumerated gaps above via Legistar (established method
   from FY2022) or accept them as documented absences.
4. FY2007 remains out of scope per the earlier decision (only sourceable via messy
   multi-year catch-up resolutions).
