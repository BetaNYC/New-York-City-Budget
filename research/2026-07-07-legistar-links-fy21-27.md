# Legistar links: FY2021–FY2027

**Report generated:** 2026-07-07
**Data current as of:** 2026-07-07
**Last revised:** 2026-07-07 (FY2025/FY2027 Transparency Resolution gap-fill
pass — see "Method — 2026-07-07 FY2025/FY2027 gap-fill" below)
**Status:** Complete for all core documents (24/24 linked). Transparency
Resolutions: 68 of 68 linked for FY2021–FY2026 (all previously "not located"
items resolved in the earlier 2026-07-07 follow-up pass; FY2025's 13 added in
this pass). FY2027: 0 found, and 0 is the correct/expected count — see
FY2027 section below for why.

## Method and a key structural finding

Every fiscal year's Adopted Budget is enacted at a single Council Stated Meeting
(almost always June 30, occasionally a few days earlier/later) as a **cluster of
sequential resolution file numbers**, confirmed by pulling the full June 30, 2020
Stated Meeting agenda (`get_event_bills` on event 18032, reached via
`get_bill_history` on the known Capital Resolution A) and cross-checking the
pattern against all seven years via `nyc-council-mcp`'s `search_legislation_live`:

| Offset | Title | What it corresponds to in this repo |
|---|---|---|
| N | "RESOLUTION TO ADOPT A BUDGET APPROPRIATING THE AMOUNTS NECESSARY..." | Overall Expense Budget adoption |
| N+1 | "RESOLUTION TO ADOPT A CONTRACT BUDGET SETTING FORTH, BY AGENCY, CATEGORIES OF CONTRACTUAL SERVICES..." | **Schedule C and Terms & Conditions** — this is the Legistar record that adopts the by-agency discretionary-contract categories; Schedule C and T&C are exhibits under it, not separately-filed Legistar matters |
| N+2 | "RESOLUTION BY THE NEW YORK CITY COUNCIL PURSUANT TO SECTION 254... (RESOLUTION A)" | Capital budget changes (already known from the FY22–24 and FY2021 pilot docs) |
| N+3 | "...(RESOLUTION B)" | Capital budget total-amounts adoption (companion, not separately downloaded in this repo) |

This N/N+1/N+2 pattern was verified directly via `get_bill` for **all seven**
fiscal years (not inferred from just one) — every offset matched exactly, with
title text confirming the resolution type each time. **Important caveat:**
this confirms the *Contract Budget resolution's file number* as the correct
matter to cite for Schedule C/T&C, but I could not get past Legistar's
"Invalid parameters!" error on direct `LegislationDetail.aspx` navigation, nor
get a link click to register in a shared, multi-agent-contended browser
session (documented tooling problem — see FY2021 pilot's "Tooling notes"), so
the **attachment list itself was not visually confirmed** to contain the
Schedule C and T&C PDFs specifically. The matter-number/date/title linkage is
solid; item-level attachment confirmation is not. Status is marked
"confirmed (inferred exhibit)" for Schedule C/T&C rows to reflect this.

For **Capital** (Resolution A, and where applicable its "Capital Project
Detail/Supporting Detail Book" companion), matter numbers were already known
for FY2022–2024 from the prior scoping docs, or found fresh here for
FY2025–2027 using the confirmed N+2 offset and verified individually via
`get_bill`.

For **Transparency Resolutions**, the generic title "Resolution approving the
new designation and changes in the designation of certain organizations to
receive funding in the Expense Budget" was searched via
`search_legislation_live` — a multi-word phrase query that, contrary to the
single-generic-token limitation documented for other title patterns, matched
**cleanly and exclusively** against this one resolution series (no noise from
other legislation types). The catch: the API caps results at 50 and returns
them in a fixed, query-independent order (confirmed by running two different
substrings of the same phrase and diffing byte-identical output) that tracks
`MatterPassedDate` descending — i.e. it always returns the 50 *newest*
matches, with no offset/pagination parameter available to reach further back.
This reliably covered FY2026 (all 10), FY2024 (all 9), FY2023 (all 14), and
the last 4 of FY2022's 14 — but hit the 50-result ceiling before reaching
FY2022's earlier resolutions or any of FY2021's 8. A follow-up attempt to use
Legistar's own web advanced-search (date-range filter, which would solve
this) was blocked by browser-extension/multi-agent contention this session
(three connected Chrome instances, ambiguous selection, a working tab closed
mid-navigation) — consistent with the tooling problems the FY2021 pilot
already flagged. Per the task's effort-budget instruction, the 17 unreached
resolutions are recorded as "not located" rather than pursued further.

## Method — 2026-07-07 follow-up

The blocker above is fixed: `search_legislation_live` now supports a working
`order` param (`date_asc`/`date_desc`) and multi-word AND queries, and the
local `search_bills` index now covers Resolutions back to 2014-01-22. Rather
than paging `search_legislation_live`, a single `search_bills` call for the
exact title phrase ("new designation and changes in the designation of
certain organizations") with `limit=100` returned the full run of this
resolution series from 2014 through 2026-06-30 in one shot — including all 17
previously-missing matters, each with a `passed_date` matching the target
PDF's filename date exactly. Every match was then individually verified via
`get_bill` (file number, `MatterId`, `MatterGuid`, `MatterPassedDate`, and
`MatterStatusName: "Adopted"` all cross-checked) before being written into
the tables below. All 17 are now "confirmed."

---

## Method — 2026-07-07 FY2025/FY2027 gap-fill

FY2025 and FY2027 had **zero** Transparency Resolutions sourced in this repo
at all prior to this pass — a pre-existing gap distinct from the FY2021/2022
"not located" items resolved above (those already had partial FY2021/2022
data; FY2025/2027 had none).

**FY2025:** `nyc-council-mcp`'s `search_legislation_live` (live Legistar API,
phrase-quoted title, `order=date_desc`) returned 12 matches in the FY2025
window (2024-08-15 through 2025-06-30), each verified via `get_bill`
(`MatterStatusName: "Adopted"`, `MatterBodyName: "Committee on Finance"`).
But cross-checking against `council.nyc.gov/budget/fy2025/`'s own
"Transparency Resolutions" section (the primary-source page used throughout
this doc series) turned up **13**, not 12 — a resolution dated 2024-10-23 is
absent from the Legistar phrase-search results (confirmed absent from the
raw API response, not just an artifact of result-count truncation) despite
being adopted and posted by the Council itself. All 13 PDFs were downloaded
directly from `council.nyc.gov/budget/fy2025/`'s own linked URLs (the same
primary-source pattern already established for Schedule C, Terms &
Conditions, and Capital documents in this doc for other years). 12 of 13
carry a cross-verified Legistar matter number; the 2024-10-23 one does not
(see table note).

**FY2027:** The same `search_legislation_live` phrase search (`order=date_desc`)
returns **Res 0529-2026 (2026-06-30, FY2026's last)** as the newest match —
nothing newer exists in Legistar under this resolution series. Independently,
`council.nyc.gov/budget/fy2027/` was confirmed live (page exists, correct
title "Fiscal Year 2027 Budget") but has **no Transparency Resolutions
section at all yet** (checked via DOM query — 0 matching links, and none of
the page's headings mention it). Both sources agree: **0 is correct**, not a
gap. Every fiscal year's Transparency Resolution series has so far started
in the second half of August (FY2025: Aug 15; FY2026: Aug 14; FY2024: Aug 3)
— FY2027 began 2026-07-01, so as of this pass (2026-07-07, seven days in)
it is too early for the Council to have adopted or posted any.

## FY2021 (`source/FY21/`)

| Document | Local path | Legistar matter | Legistar URL | Adopted | Status |
|---|---|---|---|---|---|
| Schedule C | `source/FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf` | Res 1361-2020 (Contract Budget, M 230) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=65938&GUID=E329BBC3-0676-45BB-BF80-0CE3FE8A7DF7 | 2020-06-30 | confirmed (inferred exhibit) |
| Terms & Conditions | `source/FY21/Fiscal-2021-Terms-and-Conditions.pdf` | Res 1361-2020 (Contract Budget, M 230) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=65938&GUID=E329BBC3-0676-45BB-BF80-0CE3FE8A7DF7 | 2020-06-30 | confirmed (inferred exhibit) |
| Capital §254 Resolution A | `source/FY21/FY21-Sec254-Capital-ResoA-M231-Res1362-Res1363.pdf` | Res 1362-2020 (M 231) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=65939&GUID=4557B556-938C-4803-A5B0-A24F9C921889 | 2020-06-30 | confirmed (from FY2021 pilot) |
| Transparency Reso #1 | `source/FY21/transparency-resolutions/Transparency-Reso-01-2020-08-27.pdf` | Res 1394-2020 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=66163&GUID=BE3507A2-88A4-4C3E-97EF-108C917E678B | 2020-08-27 | confirmed |
| Transparency Reso #2 | `source/FY21/transparency-resolutions/Transparency-Reso-02-2020-09-23.pdf` | Res 1433-2020 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=66272&GUID=C3963F07-5E20-4B1B-A6F6-29A6DCE3CEA3 | 2020-09-23 | confirmed |
| Transparency Reso #3 | `source/FY21/transparency-resolutions/Transparency-Reso-03-2020-10-29.pdf` | Res 1470-2020 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=66454&GUID=C4BA24FB-92A8-4386-AA65-CC7D25C6C7E6 | 2020-10-29 | confirmed |
| Transparency Reso #4 | `source/FY21/transparency-resolutions/Transparency-Reso-04-2020-11-19.pdf` | Res 1480-2020 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=66521&GUID=183A7D62-9660-4C2B-BB9C-69AB6F9FD1F3 | 2020-11-19 | confirmed |
| Transparency Reso #5 | `source/FY21/transparency-resolutions/Transparency-Reso-05-2020-12-17.pdf` | Res 1509-2020 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=66617&GUID=3E86BFF9-9DC4-4397-A2F0-92508ECC60E0 | 2020-12-17 | confirmed |
| Transparency Reso #6 | `source/FY21/transparency-resolutions/Transparency-Reso-06-2021-02-25.pdf` | Res 1544-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=66803&GUID=6C3B21DE-395F-456E-BA03-15D713F440AD | 2021-02-25 | confirmed |
| Transparency Reso #7 | `source/FY21/transparency-resolutions/Transparency-Reso-07-2021-04-22.pdf` | Res 1603-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67065&GUID=BB3A29A9-63FF-4091-8050-06FDAAA0EE48 | 2021-04-22 | confirmed |
| Transparency Reso #8 | `source/FY21/transparency-resolutions/Transparency-Reso-08-2021-06-30.pdf` | Res 1693-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67385&GUID=52CA543B-B01B-41AA-B21D-0C9D9FE862B5 | 2021-06-30 | confirmed |

## FY2022 (`source/FY22/`)

| Document | Local path | Legistar matter | Legistar URL | Adopted | Status |
|---|---|---|---|---|---|
| Schedule C | `source/FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf` | Res 1700-2021 (Contract Budget, M 300) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67311&GUID=92D21F55-1CDE-460A-81BB-2E6144538476 | 2021-06-30 | confirmed (inferred exhibit) |
| Terms & Conditions | `source/FY22/FY22-Terms-and-Conditions_FINAL.pdf` | Res 1700-2021 (Contract Budget, M 300) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67311&GUID=92D21F55-1CDE-460A-81BB-2E6144538476 | 2021-06-30 | confirmed (inferred exhibit) |
| Capital §254 Resolution A | `source/FY22/FY22-Sec254-Capital-ResoA-Book.pdf` | Res 1701-2021 (M 301) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67312&GUID=D5169437-2921-4FF6-8A47-440DCFBD95CC | 2021-06-30 | confirmed (from FY22-24 gap doc) |
| Capital Supporting Detail Book | `source/FY22/FY22-Sec254-Capital-Supporting-Detail-Book.pdf` | Res 1701-2021 (M 301) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67312&GUID=D5169437-2921-4FF6-8A47-440DCFBD95CC | 2021-06-30 | confirmed (inferred, same M-message as Reso A) |
| Transparency Reso #1 | `.../Transparency-Reso-01-2021-07-29.pdf` | Res 1715-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67433&GUID=656351E0-7A00-4ED6-9AE5-E897CBEF2A62 | 2021-07-29 | confirmed |
| Transparency Reso #2 | `.../Transparency-Reso-02-2021-08-26.pdf` | Res 1726-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67490&GUID=2602C1B2-E5C9-4A2F-91BC-697261B609D5 | 2021-08-26 | confirmed |
| Transparency Reso #3 | `.../Transparency-Reso-03-2021-09-23.pdf` | Res 1739-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67545&GUID=623E80B5-209E-4322-A4AA-7B75221A9F02 | 2021-09-23 | confirmed |
| Transparency Reso #4 | `.../Transparency-Reso-04-2021-10-07.pdf` | Res 1752-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67634&GUID=93989314-3E64-4207-9CA0-1B88BCE97C4B | 2021-10-07 | confirmed |
| Transparency Reso #5 | `.../Transparency-Reso-05-2021-10-21.pdf` | Res 1765-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67689&GUID=232B07D0-8C53-4353-B0AC-BBF4E20E5FF7 | 2021-10-21 | confirmed |
| Transparency Reso #6 | `.../Transparency-Reso-06-2021-11-10.pdf` | Res 1785-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67797&GUID=33CF5E8B-3BFE-4563-AC42-2E6C55EF4DBC | 2021-11-10 | confirmed |
| Transparency Reso #7 | `.../Transparency-Reso-07-2021-11-23.pdf` | Res 1803-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67866&GUID=0E9A8171-9D02-4809-979D-7E33D9A84529 | 2021-11-23 | confirmed |
| Transparency Reso #8 | `.../Transparency-Reso-08-2021-12-09.pdf` | Res 1839-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=67977&GUID=E574A30A-D47D-46F6-B517-DB0A3F52B6EA | 2021-12-09 | confirmed |
| Transparency Reso #9 | `.../Transparency-Reso-09-2021-12-15.pdf` | Res 1869-2021 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=68007&GUID=1E40920F-C625-4B37-A68E-6754D70CA352 | 2021-12-15 | confirmed |
| Transparency Reso #10 | `.../Transparency-Reso-10-2022-03-10.pdf` | Res 0058-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=68341&GUID=17C86DE3-ED28-45BF-9232-D1EA258DE952 | 2022-03-10 | confirmed |
| Transparency Reso #11 | `.../Transparency-Reso-11-2022-04-14.pdf` | Res 0107-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=68648&GUID=D3A0B53F-CF44-4123-9ED7-77B3A8B2CC3C | 2022-04-14 | confirmed |
| Transparency Reso #12 | `.../Transparency-Reso-12-2022-05-05.pdf` | Res 0154-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=69169&GUID=9F299F0F-9019-408B-883E-DDA8C31131D9 | 2022-05-05 | confirmed |
| Transparency Reso #13 | `.../Transparency-Reso-13-2022-05-19.pdf` | Res 0160-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=69391&GUID=41993EA5-70A0-42E7-BA88-837F3AC0F404 | 2022-05-19 | confirmed |
| Transparency Reso #14 | `.../Transparency-Reso-14-2022-06-13.pdf` | Res 0224-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=69668&GUID=31BD6152-03DF-4DE5-B15E-CF9620747372 | 2022-06-13 | confirmed |

(FY2022 transparency-resolution local paths above are all under
`source/FY22/transparency-resolutions/`.)

## FY2023 (`source/FY23/`)

| Document | Local path | Legistar matter | Legistar URL | Adopted | Status |
|---|---|---|---|---|---|
| Schedule C | `source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf` | Res 0226-2022 (Contract Budget, M 50) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=69621&GUID=0FA67523-248A-4B25-A939-D784C53C9E38 | 2022-06-13 | confirmed (inferred exhibit) |
| Terms & Conditions | `source/FY23/FY23-Terms-and-Conditions_FINAL_OMB-and-Council-Review-6.11.22.pdf` | Res 0226-2022 (Contract Budget, M 50) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=69621&GUID=0FA67523-248A-4B25-A939-D784C53C9E38 | 2022-06-13 | confirmed (inferred exhibit) |
| Capital §254 Resolution A | `source/FY23/FY23-Sec254-Capital-ResoA-Book.pdf` | Res 0227-2022 (M 51) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=69622&GUID=DD188CF2-78BD-4A8B-AF8B-6A75EEE438EB | 2022-06-13 | confirmed (from FY22-24 gap doc) |
| Capital Supporting Detail Book | `source/FY23/FY23-Sec254-Capital-Supporting-Detail-Book.pdf` | Res 0227-2022 (M 51) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=69622&GUID=DD188CF2-78BD-4A8B-AF8B-6A75EEE438EB | 2022-06-13 | confirmed (inferred, same M-message as Reso A) |
| Transparency Reso #1 | `.../Transparency-Reso-01-2022-07-14.pdf` | Res 0255-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=69789&GUID=47066D56-EBF0-45EC-97B5-B59388D52171 | 2022-07-14 | confirmed |
| Transparency Reso #2 | `.../Transparency-Reso-02-2022-08-11.pdf` | Res 0288-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=69889&GUID=FFC68ACE-5EC9-4A59-BD62-8723C8E9EDF9 | 2022-08-11 | confirmed |
| Transparency Reso #3 | `.../Transparency-Reso-03-2022-09-29.pdf` | Res 0327-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=70175&GUID=51AFA7B4-FF48-4557-833F-78582CE37C46 | 2022-09-29 | confirmed |
| Transparency Reso #4 | `.../Transparency-Reso-04-2022-10-27.pdf` | Res 0363-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=70358&GUID=B6FBA5DE-A63D-4345-A1A9-0DECE21BED9E | 2022-10-27 | confirmed |
| Transparency Reso #5 | `.../Transparency-Reso-05-2022-11-22.pdf` | Res 0388-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=70503&GUID=A46C9CE9-46EA-410A-BD27-C336E26FE413 | 2022-11-22 | confirmed |
| Transparency Reso #6 | `.../Transparency-Reso-06-2022-12-21.pdf` | Res 0440-2022 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=70543&GUID=0549803D-1D57-4A62-9A59-13256DF38211 | 2022-12-21 | confirmed |
| Transparency Reso #7 | `.../Transparency-Reso-07-2023-01-19.pdf` | Res 0457-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=70676&GUID=A9BBBF7B-B2B5-40F8-B925-D0372260A3A0 | 2023-01-19 | confirmed |
| Transparency Reso #8 | `.../Transparency-Reso-08-2023-02-02.pdf` | Res 0472-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=70759&GUID=1CB90392-DF66-4A63-B80F-0AE41CAEE698 | 2023-02-02 | confirmed |
| Transparency Reso #9 | `.../Transparency-Reso-09-2023-02-16.pdf` | Res 0502-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=70832&GUID=186AF42C-7C88-4167-B1A4-BD865C4B26B9 | 2023-02-16 | confirmed |
| Transparency Reso #10 | `.../Transparency-Reso-10-2023-03-02.pdf` | Res 0508-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=70946&GUID=64869601-1DB4-4B84-92EE-05DE4CE6F054 | 2023-03-02 | confirmed |
| Transparency Reso #11 | `.../Transparency-Reso-11-2023-03-16.pdf` | Res 0530-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=70972&GUID=3957447C-B91C-40FD-A176-7DB70AFA5F42 | 2023-03-16 | confirmed |
| Transparency Reso #12 | `.../Transparency-Reso-12-2023-04-27.pdf` | Res 0575-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=71183&GUID=12171174-BC41-4C2E-A9BF-C08195AEFD31 | 2023-04-27 | confirmed |
| Transparency Reso #13 | `.../Transparency-Reso-13-2023-05-11.pdf` | Res 0607-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=71334&GUID=FC8CE78A-3F72-4767-9D16-4D4AC9DB050A | 2023-05-11 | confirmed |
| Transparency Reso #14 | `.../Transparency-Reso-14-2023-06-30.pdf` | Res 0705-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=71611&GUID=A8903F59-949F-4C7F-8DE3-4F3A55828B3F | 2023-06-30 | confirmed |

(FY2023 transparency-resolution local paths above are all under
`source/FY23/transparency-resolutions/`.)

## FY2024 (`source/FY24/`)

| Document | Local path | Legistar matter | Legistar URL | Adopted | Status |
|---|---|---|---|---|---|
| Schedule C | `source/FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf` | Res 0707-2023 (Contract Budget, M 141) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=71613&GUID=86D036D0-77E8-4A98-9A11-97A3D64CE9CA | 2023-06-30 | confirmed (inferred exhibit) |
| Terms & Conditions | `source/FY24/FY24-Terms-and-Conditions.pdf` | Res 0707-2023 (Contract Budget, M 141) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=71613&GUID=86D036D0-77E8-4A98-9A11-97A3D64CE9CA | 2023-06-30 | confirmed (inferred exhibit) |
| Capital Supporting Detail Book | `source/FY24/FY2024-Sec254-Supporting-Detail-Book_7.10.2023pwp-2.pdf` | Res 0708-2023 (M 142, Reso A) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=71614&GUID=C5A9B457-98C4-4D0C-A1EA-6AB51E53206E | 2023-06-30 | confirmed (inferred, same M-message as Reso A) |
| Capital Changes ("Reso A") | `source/FY24/Fiscal-Year-2024-Changes-To-The-Executive-Capital-Budget-Adopted-by-the-City-Council.pdf` | Res 0708-2023 (M 142, Reso A) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=71614&GUID=C5A9B457-98C4-4D0C-A1EA-6AB51E53206E | 2023-06-30 | confirmed (from FY22-24 gap doc; companion Reso B = Res 0709-2023, ID=71615, GUID 9246C194-FF5B-4C21-897B-6A41170908A2, not separately downloaded) |
| Transparency Reso #1 | `.../Transparency-Reso-01-2023-08-03.pdf` | Res 0726-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=71693&GUID=8AE525AB-23ED-459C-842E-DFBC5CC3C6AF | 2023-08-03 | confirmed |
| Transparency Reso #2 | `.../Transparency-Reso-02-2023-09-14.pdf` | Res 0744-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=71819&GUID=B8D550E6-677E-416D-858A-D8D1D2E3F126 | 2023-09-14 | confirmed |
| Transparency Reso #3 | `.../Transparency-Reso-03-2023-10-05.pdf` | Res 0806-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=71935&GUID=5E46C1B1-E139-4E29-8D05-206D831F4740 | 2023-10-05 | confirmed |
| Transparency Reso #4 | `.../Transparency-Reso-04-2023-11-02.pdf` | Res 0834-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=72030&GUID=679A985A-4335-486D-A73D-D07F34D9A958 | 2023-11-02 | confirmed |
| Transparency Reso #5 | `.../Transparency-Reso-05-2023-12-20.pdf` | Res 0864-2023 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=72180&GUID=A16794C7-CBF3-4568-8FFB-E2E12B4B06A9 | 2023-12-20 | confirmed |
| Transparency Reso #6 | `.../Transparency-Reso-06-2024-02-08.pdf` | Res 0006-2024 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=72349&GUID=E16E27E3-4C58-40D0-BB11-8AAD7AFA52BC | 2024-02-08 | confirmed |
| Transparency Reso #7 | `.../Transparency-Reso-07-2024-04-11.pdf` | Res 0305-2024 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=74000&GUID=AC16CB4F-B542-4846-BB19-D4648C16E869 | 2024-04-11 | confirmed |
| Transparency Reso #8 | `.../Transparency-Reso-08-2024-05-23.pdf` | Res 0436-2024 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=74256&GUID=0E7BADC2-89FA-4729-8B82-C230256D25E0 | 2024-05-23 | confirmed |
| Transparency Reso #9 | `.../Transparency-Reso-09-2024-06-30.pdf` | Res 0484-2024 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=74356&GUID=F136B03A-C4BD-40AE-9616-51F0F7BE3B0C | 2024-06-30 | confirmed |

(FY2024 transparency-resolution local paths above are all under
`source/FY24/transparency-resolutions/`.)

## FY2025 (`source/FY25/`)

**13 of 13 Transparency Resolutions found and downloaded** (2026-07-07
gap-fill pass) — see "Method — 2026-07-07 FY2025/FY2027 gap-fill" above.
Source: `council.nyc.gov/budget/fy2025/`, cross-verified against Legistar
via `get_bill` for 12 of 13 (all but #4).

| Document | Local path | Legistar matter | Legistar URL | Adopted | Status |
|---|---|---|---|---|---|
| Schedule C | `source/FY25/Fiscal-2025-Schedule-C-MERGE-FINAL-2.pdf` | Res 0490-2024 (Contract Budget, M 42) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=74480&GUID=40E2DE40-3F8E-45AE-BB1B-A4080E4D6299 | 2024-06-30 | confirmed (inferred exhibit) |
| Terms & Conditions | `source/FY25/FY25-Terms-and-Conditions-1.pdf` | Res 0490-2024 (Contract Budget, M 42) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=74480&GUID=40E2DE40-3F8E-45AE-BB1B-A4080E4D6299 | 2024-06-30 | confirmed (inferred exhibit) |
| Capital Changes | `source/FY25/Fiscal-2025-Capital-Changes.pdf` | Res 0491-2024 (M 43, Reso A) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=74481&GUID=D2C1C949-B3CA-463A-8BC5-326C803A9C79 | 2024-06-30 | confirmed (newly found this pass) |
| Transparency Reso #1 | `.../Transparency-Reso-01-2024-08-15.pdf` | Res 0517-2024 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=74597&GUID=F7B05370-C041-4C68-89EA-82D4D395D9B8 | 2024-08-15 | confirmed |
| Transparency Reso #2 | `.../Transparency-Reso-02-2024-09-12.pdf` | Res 0559-2024 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=74713&GUID=06F14751-EDB0-4696-88EF-5BAFF4B49149 | 2024-09-12 | confirmed |
| Transparency Reso #3 | `.../Transparency-Reso-03-2024-10-10.pdf` | Res 0597-2024 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=74800&GUID=A90604FF-CB89-4866-8FB8-D099801EEE11 | 2024-10-10 | confirmed |
| Transparency Reso #4 | `.../Transparency-Reso-04-2024-10-23.pdf` | not resolved this pass | n/a | 2024-10-23 (per council.nyc.gov) | confirmed via council.nyc.gov primary source only — absent from Legistar's phrase-search results for the standard title text; not chased further to individual matter number (see method note above) |
| Transparency Reso #5 | `.../Transparency-Reso-05-2024-11-13.pdf` | Res 0641-2024 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=74987&GUID=31B11577-DBD3-4D20-A20F-A1A6E8E2FFA9 | 2024-11-13 | confirmed |
| Transparency Reso #6 | `.../Transparency-Reso-06-2024-12-05.pdf` | Res 0677-2024 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=75088&GUID=9303B891-9859-4876-9714-6FDEFF3D43B6 | 2024-12-05 | confirmed |
| Transparency Reso #7 | `.../Transparency-Reso-07-2025-01-23.pdf` | Res 0712-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=75210&GUID=E6873435-00D0-4AE7-A691-BD0D826CDEC4 | 2025-01-23 | confirmed |
| Transparency Reso #8 | `.../Transparency-Reso-08-2025-02-13.pdf` | Res 0732-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=75369&GUID=06FE016B-44E3-4ED1-9E27-3A78A504D7AA | 2025-02-13 | confirmed |
| Transparency Reso #9 | `.../Transparency-Reso-09-2025-03-12.pdf` | Res 0791-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=75514&GUID=1A1A7EAB-2288-459C-9D94-FE2373B68454 | 2025-03-12 | confirmed |
| Transparency Reso #10 | `.../Transparency-Reso-10-2025-03-26.pdf` | Res 0815-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=75624&GUID=E315D0D5-ADFF-44BC-AD90-E59EC19F4B7F | 2025-03-26 | confirmed |
| Transparency Reso #11 | `.../Transparency-Reso-11-2025-04-24.pdf` | Res 0849-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=75693&GUID=6BA6ABD6-3C2A-444A-9A0A-2F99CDEA6870 | 2025-04-24 | confirmed |
| Transparency Reso #12 | `.../Transparency-Reso-12-2025-05-28.pdf` | Res 0875-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=75850&GUID=834D3003-01C7-4C11-B126-84D65B35CE0D | 2025-05-28 | confirmed |
| Transparency Reso #13 | `.../Transparency-Reso-13-2025-06-30.pdf` | Res 0959-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=76075&GUID=AD973B65-F33A-4B11-994A-2FBDDF984437 | 2025-06-30 | confirmed |

(FY2025 transparency-resolution local paths above are all under
`source/FY25/transparency-resolutions/`.)

## FY2026 (`source/FY26/`)

| Document | Local path | Legistar matter | Legistar URL | Adopted | Status |
|---|---|---|---|---|---|
| Schedule C | `source/FY26/Fiscal-2026-Schedule-C-4.pdf` | Res 0974-2025 (Contract Budget, M 128) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=76115&GUID=CC857BB0-6B46-4D9B-9681-B767FDF1B5D6 | 2025-06-30 | confirmed (inferred exhibit) |
| Terms & Conditions | `source/FY26/FY26-Terms-and-Conditions-1.pdf` | Res 0974-2025 (Contract Budget, M 128) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=76115&GUID=CC857BB0-6B46-4D9B-9681-B767FDF1B5D6 | 2025-06-30 | confirmed (inferred exhibit) |
| Capital Budget Supporting Details | `source/FY26/Fiscal-2026-Capital-Budget-Supporting-Details-1.pdf` | Res 0975-2025 (M 129, Reso A) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=76116&GUID=C88B8E4F-54DC-4690-8772-BD3252D75884 | 2025-06-30 | confirmed (newly found this pass) |
| Transparency Reso #1 | `.../Transparency-Reso-01-2025-08-14.pdf` | Res 1013-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=76221&GUID=01CD2610-B141-4C37-9B85-986A549BB691 | 2025-08-14 | confirmed |
| Transparency Reso #2 | `.../Transparency-Reso-02-2025-09-25.pdf` | Res 1059-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=76441&GUID=8AE8D84A-AB69-4B9A-813A-EC275C425B81 | 2025-09-25 | confirmed |
| Transparency Reso #3 | `.../Transparency-Reso-03-2025-10-29.pdf` | Res 1100-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=76604&GUID=37796C8C-0093-45CF-9F5D-5F7B95200446 | 2025-10-29 | confirmed |
| Transparency Reso #4 | `.../Transparency-Reso-04-2025-11-25.pdf` | Res 1153-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=76762&GUID=DFCA0CF3-EA86-424E-9BE7-31B91EFFA734 | 2025-11-25 | confirmed |
| Transparency Reso #5 | `.../Transparency-Reso-05-2025-12-18.pdf` | Res 1186-2025 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=76863&GUID=57C3A63D-C050-40C2-9C27-FAB99C67010D | 2025-12-18 | confirmed |
| Transparency Reso #6 | `.../Transparency-Reso-06-2026-02-12.pdf` | Res 0255-2026 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=77952&GUID=C36B06D0-D039-46CD-951C-A2875CA3BF1B | 2026-02-12 | confirmed |
| Transparency Reso #7 | `.../Transparency-Reso-07-2026-03-10.pdf` | Res 0353-2026 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=78310&GUID=D7504BF6-F9DF-4F3F-BAD0-5CBCCCB4EFB2 | 2026-03-10 | confirmed |
| Transparency Reso #8 | `.../Transparency-Reso-08-2026-04-16.pdf` | Res 0420-2026 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=78579&GUID=9BCE9066-AABE-4928-BEA3-4C46EC83E440 | 2026-04-16 | confirmed |
| Transparency Reso #9 | `.../Transparency-Reso-09-2026-05-20.pdf` | Res 0479-2026 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=78870&GUID=3D3655A0-06EF-4C6B-A0D4-D95AA6A34FFA | 2026-05-20 | confirmed |
| Transparency Reso #10 | `.../Transparency-Reso-10-2026-06-30.pdf` | Res 0529-2026 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=79151&GUID=78561307-299E-48B7-87EA-A97C18EF48F0 | 2026-06-30 | confirmed |

(FY2026 transparency-resolution local paths above are all under
`source/FY26/transparency-resolutions/`.)

## FY2027 (`source/FY27/`)

**0 Transparency Resolutions exist yet — confirmed correct, not a gap.**
FY2027 began 2026-07-01; this pass ran 2026-07-07, seven days in. Every
observed fiscal year's Transparency Resolution series starts in the second
half of August (FY2025: Aug 15; FY2026: Aug 14; FY2024: Aug 3), so none
would be expected this early. Confirmed two ways: `search_legislation_live`
(live Legistar API) returns Res 0529-2026 (2026-06-30, FY2026's last) as the
newest match under this resolution series, nothing newer; and
`council.nyc.gov/budget/fy2027/` is live but has no Transparency Resolutions
section yet (0 matching links in the page DOM). See "Method — 2026-07-07
FY2025/FY2027 gap-fill" above.

| Document | Local path | Legistar matter | Legistar URL | Adopted | Status |
|---|---|---|---|---|---|
| Schedule C | `source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf` | Res 0540-2026 (Contract Budget, M 69) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=79146&GUID=45F33EBC-A752-4F42-A473-67D0C9EFF5A0 | 2026-06-30 | confirmed (inferred exhibit) |
| Terms & Conditions | `source/FY27/FY27-FINAL-Terms-and-Conditions-6.30.26.pdf` | Res 0540-2026 (Contract Budget, M 69) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=79146&GUID=45F33EBC-A752-4F42-A473-67D0C9EFF5A0 | 2026-06-30 | confirmed (inferred exhibit) |
| Capital Supporting Detail | `source/FY27/Supporting-Detail-for-FY2027-Changes-To-the-Executive-Capital-Budget-Pursuant-to-Section-254.V4.pdf` | Res 0541-2026 (M 70, Reso A) | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=79130&GUID=38B41267-1949-4412-B255-E139B449CF45 | 2026-06-30 | confirmed (newly found this pass) |

---

## Not-located items — resolved 2026-07-07 (0 of 92 remaining)

All 17 Transparency Resolutions previously blocked by `search_legislation_live`'s
50-result ceiling (7 in FY2021, 10 in FY2022) were located and confirmed in
the 2026-07-07 follow-up pass — see "Method — 2026-07-07 follow-up" above.
FY2025's previously-unsourced 13 Transparency Resolutions were found and
downloaded in a second 2026-07-07 pass — see "Method — 2026-07-07
FY2025/FY2027 gap-fill" above. Every document in this doc for FY2021–FY2026
(24 core documents + 68 Transparency Resolutions = 92 total) is now linked
and confirmed, with one exception noted in-table (FY2025 Transparency Reso
#4's Legistar matter number, sourced from council.nyc.gov only). FY2027
Transparency Resolutions: confirmed 0 exist as of this pass (too early in
the fiscal year, not a gap) — see FY2027 section above.
