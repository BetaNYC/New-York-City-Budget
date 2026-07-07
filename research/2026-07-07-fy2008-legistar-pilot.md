# Pilot: FY2008 Legistar sourcing (oldest possible year)

**Report generated:** 2026-07-07
**Data current as of:** 2026-07-07
**Status:** Pilot complete. Part of a two-year test (FY2008 here; a parallel agent ran
FY2021) to establish real per-year cost/feasibility before committing to a full
FY2008–FY2021 historical sourcing pass. This document does not coordinate with or
depend on the FY2021 pilot's findings.

## Why FY2008

`research/2026-07-07-fy09-fy21-legacy-import-scoping.md`'s Addendum 2 established
FY2008 as the confirmed floor year for the Schedule-C-equivalent designation
resolution mechanism (`Res 1090-2007`, adopted 2007-10-17) — a content floor, not a
records/indexing floor. FY2008 also sits right at a documented (if not fully
source-verified) NYC Council discretionary-funding accountability reform following a
2008 "slush fund" scandal, so this pilot doubled as a test of whether that era looks
structurally different from FY2022–FY2024.

## Source status table

| Document | Found? | Local path | Format / notes |
|---|---|---|---|
| Schedule C (Res 1090-2007 core resolution) | Resolution text found; **the "Revised Schedule C" schedule itself was not located as a separate digitized attachment** | `source/FY08/Res1090-2007-Committee-Report.doc`, `Res1090-2007-Hearing-Transcript.doc`, `Res1090-2007-Press-Release.doc`, `Res1090-2007-Hearing-Transcript-StatedMtg.doc` | All four are legacy Word 9.0 Composite Document Format (`.doc`, not true PDF, despite Legistar serving them through the same `View.ashx` endpoint used for later years' PDFs) |
| Capital Section 254, Resolution A (schedule of changes) | Resolution found (`Res 0910-2007`); **no "Changes To..." schedule document attached** | `source/FY08/Res0910-2007-CapitalA-Press-Release.doc`, `Res0910-2007-CapitalA-Hearing-Transcript.doc`, `Res0910-2007-CapitalA-Hearing-Transcript-StatedMtg.doc` | Same legacy `.doc` format as above |
| Capital Section 254, Resolution B (total amounts) | Found (`Res 0911-2007`), not downloaded | — | Per FY23–25 precedent this document type has no printed subtotals to reconcile against (`NOT RECONCILABLE`), so it was deprioritized under the effort budget; matter confirmed to exist |
| Terms & Conditions | **Not found; inconclusive** | — | See "Terms & Conditions" section below |
| Transparency-Resolution-equivalent legislation | **Confirmed to exist for FY2008** — 3 standalone resolutions found | Not downloaded (see note) | `Res 1310-2008` (2008-03-12), `Res 1437-2008` (2008-05-28), `Res 1503-2008` (2008-06-29) |

## Schedule C — Res 1090-2007

**Legistar record:** `MatterId 39743`, adopted 2007-10-17, Committee on Finance,
sponsor David I. Weprin (+3 co-sponsors). Confirmed via `nyc-council-mcp` `get_bill`
and cross-checked on the Legistar web detail page
(`legistar.council.nyc.gov/LegislationDetail.aspx?ID=447681&GUID=6E45CB4C-554E-4CCD-9B7D-05325C990AB8`).

**Resolution text itself confirms the schedule exists and was originally attached:**

> "These designations are set forth on 'Revised Schedule C' which is attached to this
> Resolution..."

The Committee Report (downloaded, 1 page, 260 words) repeats this: "These designations
are set forth on 'Revised Schedule C' attached hereto," and adds a notable line not
present in later years' committee reports — "in an effort to make the budget process
more transparent, the Council is providing a list, separate and apart from 'Revised
Schedule C', setting forth the organizations receiving Council discretionary funds."
This is suggestive of the accountability-reform context flagged in the sibling scoping
doc's Addendum 2, though it is not proof of it.

**The actual "Revised Schedule C" schedule was not found.** The Legistar record's
attachment list is only: Committee Report, Hearing Transcript, Press Release, Hearing
Transcript – Stated Meeting 10/17/07. None of these is the schedule; all four are
1-page-metadata legacy Word documents (transcripts and cover memos), not the
multi-page organization/amount schedule the resolution text describes. Checked two
plausible alternate locations for the schedule:

- **The resolution's own "Text" tab** — full text is only the `RESOLVED` clause and
  sponsor block; no schedule data embedded.
- **`M 0820-2007`** (the related MN-1 budget-modification communication referenced in
  the resolution's preamble) — a *different* mechanism (agency-to-agency unit-of-
  appropriation transfers under Charter §107(b), not organization-level Schedule C
  designations). Its own attachments (Res. No. 1091, Exhibit A, Committee Report,
  Press Release, Hearing Transcript) were not downloaded since this is confirmed to be
  the wrong document by title/purpose, not a plausible lead for Schedule C itself.

**Conclusion: Schedule C for FY2008 is a confirmed content gap on Legistar, not a
search failure.** The schedule existed in 2007 (the resolution and committee report
both describe it) but was not preserved as a separate digitized attachment the way
FY2022–FY2024's Schedule C PDFs were. Whether a paper copy survives in Council
archives outside Legistar is outside this pilot's scope.

## Capital Section 254 — Res 0910-2007 (A) / Res 0911-2007 (B)

Found via the same method the FY22–24 pass established: `nyc-council-mcp`
`search_legislation_live` for "254" and "capital" hit the tool's 50-result last-modified
cap well before reaching 2007, so the Legistar **web UI's** own text search (all years,
phrase `"CAPITAL PROGRAM FOR THE ENSUING THREE YEARS"`) was used instead — 34 total
records, one Resolution-A/B pair per fiscal year, cleanly showing `Res 0911-2007`
(Resolution B, FY2008 capital total) and, by the established "A is filed immediately
below B" convention, `Res 0910-2007` (Resolution A, FY2008 schedule of changes),
confirmed directly via `get_bill`.

- **Res 0910-2007** ("Resolution A"): adopted 2007-06-15, Committee on Finance,
  sponsors Weprin and Felder. Legistar record has no "Changes To the Executive Capital
  Budget"-style schedule attachment — only Press Release, Hearing Transcript, and
  Hearing Transcript – Stated Meeting (all downloaded, all legacy `.doc` format).
- Checked one plausible alternate source: the Mayor's original capital-budget
  submission communication, `M 0652-2007` ("Communication from the Mayor - Executive
  Capital Budget for Fiscal Year 2008, pursuant to Section 249"), cross-referenced via
  `Res 0910-2007`'s `MatterEXText4` field. Attempted to pull its attachment list via
  the Legistar web UI but repeated search-box submission failures (see Tooling notes
  below) meant this lead was not run to completion — flagged as unresolved, not as a
  negative finding, since the FY22 precedent shows Mayor's Message attachments were
  never the sourcing path used previously either.

**Conclusion: same pattern as Schedule C.** The Resolution A/B legislative record
exists and is easy to find; the actual schedule-of-changes document is not present as
a Legistar attachment for FY2008. This mirrors Schedule C's outcome closely enough
that it looks like a real era boundary, not two independent coincidences.

## Terms & Conditions

**Not found; genuinely inconclusive**, per the task's own framing that this is an
acceptable outcome. Two checks were run:

1. Res 1090-2007's own attachment list (Committee Report, Hearing Transcript, Press
   Release, Hearing Transcript–Stated Meeting) has no Terms & Conditions-titled item.
2. A Legistar full-text search for "Terms and Conditions" was attempted but proved
   unusable as a discovery method — unquoted, it returned the search engine's 1,000-
   record cap (the phrase's constituent words are common enough in unrelated
   legislative boilerplate that the search doesn't function as a targeted filter at
   this generality). A narrower, more surgical search (e.g. restricted by committee
   and date range) was not attempted, per the task's explicit instruction not to
   over-search a document type that may not separately exist this far back.

Because council.nyc.gov's own budget-archive pages (the primary channel that surfaced
T&C for FY2022–2024) do not go back this far, and no plausible Legistar record was
identified by inspection of Res 1090-2007's neighborhood, **Terms & Conditions for
FY2008 should be treated as "not sourced in this pass," not as "confirmed absent."** A
future pass with a narrower search strategy (e.g., restrict Legistar's Years filter to
2007 and search shorter, more distinctive phrases) could resolve this either way with
modest additional effort.

## Transparency-Resolution-equivalent legislation — confirmed present for FY2008

This is the pilot's clearest and most consequential finding. The sibling scoping doc
flagged this mechanism's FY2008 existence as an open question, plausibly a later
addition given the accountability-reform timing. **It is not a later addition — it
existed from the very first budget cycle this mechanism covers.**

A Legistar web-UI phrase search for "new designation and changes in the designation of
certain organizations" (226 total records, unrestricted by year) paginated to its
oldest page turned up three **standalone, single-fiscal-year** FY2008 resolutions,
confirmed individually via `nyc-council-mcp` `get_bill`:

| File # | Adopted | Title |
|---|---|---|
| `Res 1310-2008` | 2008-03-12 | "Resolution approving or disclosing the changes in the designation of certain organizations to receive funding in the Fiscal 2008 Expense Budget." |
| `Res 1437-2008` | 2008-05-28 | "Resolution approving or disclosing the new designation and changes in the designation of certain organizations to receive funding in the Fiscal 2008 Expense Budget." |
| `Res 1503-2008` | 2008-06-29 | "Resolution approving or disclosing the new designation and changes in the designation of certain organizations to receive funding in the Fiscal 2008 Expense Budget." |

All three are Committee on Finance resolutions sponsored by David I. Weprin (the same
sponsor as the original Schedule C resolution), spaced roughly every ~2–3 months
across the FY2008 fiscal year (July 2007–June 2008) — a materially similar cadence to
FY2022's 14 Transparency Resolutions (roughly monthly) and FY2024's 9 (roughly
bimonthly), just with a different name ("approving or disclosing..." rather than
"Transparency Resolution #N").

Also found in the same result set: later **omnibus catch-up resolutions**
(`Res 1934-2009`, `Res 2061-2009`, `Res 2147-2009`, `Res 0058-2010`, `Res 0206-2010`)
that retroactively cover FY2008 bundled with FY2009/FY2010 — consistent with
Addendum 1/2's earlier finding about catch-up resolutions, but now clarified: those
omnibus resolutions supplement, rather than substitute for, standalone FY2008-specific
disclosure resolutions that did exist contemporaneously.

**Not done:** downloading/inspecting these three resolutions' own attachments to check
whether *they* carry a designation-change schedule as a digitized attachment (same
question as Schedule C above). Given the pattern established for Schedule C and
Capital A, low probability of a different outcome; deprioritized under the effort
budget rather than treated as unimportant.

## Feasibility verdict and effort notes

**Relative effort per document type** (tool-call count, order of magnitude, this
session):

- **Transparency-Resolution-equivalent legislation: cheap.** One Legistar web-UI
  phrase search plus pagination to the oldest page (~6 tool calls) found and confirmed
  all three FY2008 resolutions. Existence question resolved decisively.
- **Capital Section 254: moderate.** The `nyc-council-mcp` live-API search hit its
  50-result cap before reaching 2007 (same tool quirk documented in the FY22–24 doc),
  requiring a fallback to the Legistar web UI's own phrase search (~10 tool calls
  including the A/B pairing confirmation via `get_bill`). Attachment-hunting for the
  actual schedule added a few more calls and came back empty.
- **Schedule C: moderate, mostly attachment-hunting.** The core resolution was already
  identified going in (per the task brief), so the bulk of the effort here was
  confirming the schedule wasn't attached anywhere plausible (Committee Report, Text
  tab, MN-1 cross-reference) — a negative result that still required checking multiple
  leads (~10 tool calls plus 4 downloads).
- **Terms & Conditions: cheap but inconclusive**, specifically because the task's
  effort-budget instruction was followed and the search was not pushed further once
  the obvious full-text approach proved too broad to be useful.
- **Tooling friction, not document-type friction:** a nontrivial share of total tool
  calls in this session (~15–20) went to Chrome browser-automation flakiness unrelated
  to document difficulty — the Legistar search box repeatedly failed to register typed
  text or register a first click on "Search Legislation" before postback, requiring
  retries via `form_input` and re-clicks. A multi-browser reconnection prompt
  mid-session (the account has 3 connected Chrome extensions; "Office Machine Chrome"
  was reselected via `list_connected_browsers`/`select_browser` to match the task's
  stated pre-connected session) added a few calls but was a one-time cost. This
  overhead would likely repeat for every future year sourced via the Legistar web UI,
  not scale down with practice.

**Total effort estimate for this pilot:** roughly 55–65 tool calls across
`nyc-council-mcp`, Claude in Chrome, and `curl` downloads (browser-automation retries
included). A meaningful share of that was retry overhead rather than irreducible
research effort; a cleaner run (e.g., scripted Legistar queries instead of UI
automation, or a more stable browser session) could plausibly do the same discovery
work in 30–40 calls.

## Does FY2008 look different from FY2022–2024 in ways that matter for scaling?

**Yes, in one specific and important way: attachment digitization.** FY2022–2024's
core documents (Schedule C, Capital A) were found as actual downloadable PDF/document
attachments on Legistar or council.nyc.gov. **FY2008's equivalent legislative records
exist and are easy to find, but the schedule/exhibit documents themselves were not
preserved as separate digitized attachments** — only cover materials (committee
reports, press releases, hearing transcripts) survive on Legistar, all in a legacy
Word 9.0 `.doc` container format rather than true PDF. If this pattern holds across
FY2009–FY2021, **the "document acquisition" phase of this project would need to
pivot for older years** — either accepting that Schedule C/Capital-A source data for
this range comes primarily from NYC Open Data's `4d7f-74pe` dataset (which is exactly
the FY2009–2021 range the sibling legacy-import scoping doc already covers) rather
than from PDF extraction, or investigating a non-Legistar physical/microfiche archive
this pilot did not have scope to check.

**No, in one way that matters for planning:** the Transparency-Resolution-equivalent
mechanism is **not** a later addition — it's present from the first year this project
could theoretically source at all. This simplifies scope for the "does this mechanism
exist yet" question at every year from FY2008 forward: the answer is yes, don't
re-litigate it per year, budget only for locating and downloading each year's specific
resolution set.

**Practical implication for the 14-year historical pass:** Schedule C and Capital-A
document *acquisition* for FY2008 (and plausibly nearby years) is not a parsing
problem to hand to `software-engineer` — it's a **document-does-not-exist-in-digitized-
form problem** that instead argues for leaning on the already-scoped NYC Open Data
FY2009–2021 legacy import (see the sibling doc) as the primary source for that range,
with Legistar reserved for the Transparency-Resolution-equivalent legislation
(confirmed cleanly findable every year) and as a fallback/verification check rather
than a primary PDF-acquisition channel.
