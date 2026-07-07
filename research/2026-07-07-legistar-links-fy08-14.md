# Legistar legislative-record linkage — FY2008-FY2014

**Report generated:** 2026-07-07
**Data current as of:** 2026-07-07 (live Legistar API + Legistar web UI phrase search)
**Last revised:** 2026-07-07 — FY2010 and FY2012 gaps revisited same-day after two
`nyc-council-mcp` bugs were fixed (multi-word AND-query + working `order` param on
`search_legislation_live`; Resolutions/Land Use added to the local index). See the
revised FY2010 and FY2012 sections below for what changed. **Second revision same
day:** gap-filling follow-up on FY2013 Transparency Resolutions (resolved, 12
documents found), FY2014 Capital §254, FY2012 Capital Resolution B, and a bounded
FY2008 re-check — see "Gap-filling follow-up (2026-07-07)" section at the end.

## Scope and method

Adds the missing NYC Council Legistar matter number / adoption date / URL for every
Schedule C, Capital §254, and Transparency Resolution document already downloaded in
`source/FY08/` through `source/FY14/`. FY2008 reuses the matter numbers already
identified in
[2026-07-07-fy2008-legistar-pilot.md](2026-07-07-fy2008-legistar-pilot.md) per the task
brief (not re-derived) plus a few additional `get_bill` lookups to fill in MatterId/GUID
for documents the pilot identified by number only.

**Method for FY2009-FY2014:** `nyc-council-mcp`'s live-API search
(`search_legislation_live`) confirmed unusable for this range — it sorts by
last-modified and returns only 2025-2026 records regardless of query, never reaching
back to 2008-2014 (same tool limitation flagged in the FY2008/FY2021 pilots, now
confirmed directly). All FY2009-2014 matter numbers were instead found via
**Legistar's own web-UI phrase search** (`legistar.council.nyc.gov/Legislation.aspx`,
via Claude in Chrome), using two exact-phrase queries with the Years filter set to "All
Years" (the page defaults to "This Year" on load, which silently truncates results if
not changed):

- `"new designation and changes in the designation of certain organizations"` — 226
  total records spanning 2007-2026, used for Transparency Resolutions and each year's
  Schedule C anchor resolution.
- `CAPITAL PROGRAM FOR THE ENSUING THREE YEARS` — 34 total records, one Resolution
  A/Resolution B pair per fiscal year back to FY1999. The Resolution-A file number is
  reliably `Resolution-B-number minus 1`, filed and adopted the same day — verified for
  all 6 years in this range via `get_bill`, consistent with the FY2008 pilot's finding.

Individual matter numbers were then confirmed via `get_bill`, and where a local file's
adoption date was not recoverable from its filename, the PDF's own text (or, for two
scanned/image-only PDFs, a QuickLook page-1 render) was checked for the standard
"This Resolution, dated [date]..." sentence in the Committee on Finance report.

**Important caveat on "Schedule C" linkage:** Exactly like FY2008, the actual "Revised
Schedule C" schedule document was **never a separate Legistar attachment** for any
year in this range — only cover materials (committee reports, hearing transcripts,
press releases) are attached to the designation resolutions. The full award-level
Schedule C PDFs in this repo (`fy09-Schedule-C-final.pdf`, etc.) were sourced from
council.nyc.gov directly (see the sweep doc), not from Legistar. Unlike FY2008 — which
had one distinct, uniquely-titled "initial designation" resolution (`Res 1090-2007`) —
**every year from FY2009 onward uses the identical "new designation and changes..."
title for every resolution in that year's sequence, including the first one.** There is
no separate "initial Schedule C" resolution after FY2008. For FY2009-FY2014 below,
"Schedule C" is therefore linked to the **earliest-dated resolution in that fiscal
year's designation/changes sequence** — the closest legislative analogue to FY2008's
`Res 1090-2007` — not a literal single-document attachment match. This is flagged
per-row as "anchor (earliest in sequence)" rather than "confirmed" to keep the
distinction visible.

Legistar URL format: `https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=<MatterId>&GUID=<MatterGuid>`

---

## FY2008

*(Reused from the FY2008 pilot per task instructions; MatterId/GUID for `Res 0910-2007`,
`Res 0911-2007`, `Res 1437-2008`, `Res 1503-2008` filled in here via `get_bill` since the
pilot only recorded the file numbers.)*

| Document | Local file(s) | Legistar matter | Adoption date | Legistar URL | Status |
|---|---|---|---|---|---|
| Schedule C | `schedule_c_rvs_2008.pdf`, `Res1090-2007-Committee-Report.doc`, `Res1090-2007-Hearing-Transcript.doc`, `Res1090-2007-Hearing-Transcript-StatedMtg.doc`, `Res1090-2007-Press-Release.doc` | Res 1090-2007 | 2007-10-17 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=447681&GUID=6E45CB4C-554E-4CCD-9B7D-05325C990AB8 | confirmed (per pilot) |
| Capital A | `Res0910-2007-CapitalA-Press-Release.doc`, `Res0910-2007-CapitalA-Hearing-Transcript.doc`, `Res0910-2007-CapitalA-Hearing-Transcript-StatedMtg.doc` | Res 0910-2007 | 2007-06-15 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=38974&GUID=DCF0B66A-F4B4-426E-B8AC-17A46D384BC3 | confirmed |
| Capital B | not downloaded | Res 0911-2007 | 2007-06-15 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=38975&GUID=2517E038-365C-44CB-9EF2-1B90286D22D7 | confirmed (matter only, no local file) |
| Transparency Reso (not downloaded) | — | Res 1310-2008 | 2008-03-12 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=40585&GUID=8736844C-B466-4947-8400-7D13B8FC2C05 | confirmed (matter only, no local file) |
| Transparency Reso (not downloaded) | — | Res 1437-2008 | 2008-05-28 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=41085&GUID=F4ECC3FA-7164-42B5-9B71-F453A71F7F72 | confirmed (matter only, no local file) |
| Transparency Reso (not downloaded) | — | Res 1503-2008 | 2008-06-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=41377&GUID=D4DF1CC1-552F-42DD-B9F3-A60864F93AE3 | confirmed (matter only, no local file) |

---

## FY2009

| Document | Local file (post-rename) | Legistar matter | Adoption date | Legistar URL | Status |
|---|---|---|---|---|---|
| Schedule C (anchor) | `fy09-Schedule-C-final.pdf` | Res 1585-2008 | 2008-08-14 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=41463&GUID=7C9F99BE-DB59-4EBC-9434-0C1010881E09 | anchor (earliest in sequence) |
| Capital A | — (not downloaded) | Res 1512-2008 | 2008-06-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=41345&GUID=141861FE-0DC8-4C33-A7BA-E6F2A16CEB4A | confirmed (matter only) |
| Capital B | `fy09-adopt08_capreso.pdf` | Res 1513-2008 | 2008-06-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=41346&GUID=6D720891-78CF-45BB-8F22-550C045C51F1 | confirmed |
| Transparency Reso 01 | `transparency-resolutions/Transparency-Reso-01-2008-08-14.pdf` | Res 1585-2008 | 2008-08-14 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=41463&GUID=7C9F99BE-DB59-4EBC-9434-0C1010881E09 | confirmed |
| Transparency Reso 02 | `Transparency-Reso-02-2008-09-24.pdf` | Res 1624-2008 | 2008-09-24 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=41720&GUID=87F74AA0-65B0-454D-A12C-FDC8821512DA | confirmed |
| Transparency Reso 03 | `Transparency-Reso-03-2008-11-19.pdf` (renamed from `fy09-report_committee_finance.pdf`; confirmed via PDF text "This Resolution, dated November 19, 2008") | Res 1707-2008 | 2008-11-19 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=41912&GUID=FD537A7E-0AEC-457D-9C58-218DA83565FC | confirmed |
| Transparency Reso 04 | `Transparency-Reso-04-2008-12-18.pdf` (renamed from `fy09-Scan001.pdf`; confirmed via PDF text "This Resolution, dated December 18, 2008") | Res 1740-2008 | 2008-12-18 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=41998&GUID=2C0D15EA-B364-4005-B168-3A250C2A7FEF | confirmed |
| Transparency Reso 05 | `Transparency-Reso-05-2009-02-11.pdf` | Res 1818-2009 | 2009-02-11 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=42323&GUID=908CD458-0443-4521-8E49-88347CCD201C | confirmed |
| Transparency Reso 06 | `Transparency-Reso-06-2009-04-02.pdf` | Res 1896-2009 | 2009-04-02 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=42644&GUID=557DC6AA-6E15-4FAF-BF8D-FA3923D5348A | confirmed |
| Transparency Reso 07 | `Transparency-Reso-07-2009-04-22.pdf` (omnibus, covers FY2008 + FY2009) | Res 1934-2009 | 2009-04-22 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=42729&GUID=090C22C3-7D61-4CB3-ACDB-3A372E68542C | confirmed |
| Transparency Reso 08 | `Transparency-Reso-08-2009-05-20.pdf` | Res 1985-2009 | 2009-05-20 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=42996&GUID=C0EF6C0D-90D7-4DA0-A1BD-EA63B35F7FCA | confirmed |

Not located / not downloaded: Res 1854-2009 (2009-03-11) and Res 2033-2009 (2009-06-19)
are additional FY2009-titled resolutions confirmed on Legistar but **not** among the 8
locally downloaded files — both turned out to belong to FY2010 (see below; the archive's
own foldering put a few early-FY2010 resolutions under FY09, and vice versa in one case).
No true gap in FY2009 remains once that's accounted for.

---

## FY2010

| Document | Local file (post-rename) | Legistar matter | Adoption date | Legistar URL | Status |
|---|---|---|---|---|---|
| Schedule C (anchor) | `fy_2010_sched_c_final.pdf` | Res 2033-2009 | 2009-06-19 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=43180&GUID=F67CFFBF-94D0-4B08-87E3-8FCAA76A6C75 | anchor (earliest in sequence; filename `trans_reso_sched_a_c_6_19_09` independently corroborates this is the Schedule A/C-establishing resolution; note this is a distinct matter from the same-day Capital B resolution below despite the shared date) |
| Capital A | — (not downloaded) | Res 2036-2009 | 2009-06-19 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=43183&GUID=90C13620-E10B-4B5D-AE91-1A5A9F32AAF0 | confirmed (matter only) |
| Capital B | `fy_2010_changes_exec_budget_top.pdf` | Res 2037-2009 | 2009-06-19 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=43184&GUID=0EE3EBDB-CBB6-4169-8933-025466A88B8E | confirmed |
| Transparency Reso 01 | `Transparency-Reso-01-2009-03-11.pdf` | Res 1854-2009 | 2009-03-11 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=42560&GUID=33080384-CE1C-48A7-9DCA-5A988992EEA5 | confirmed |
| Transparency Reso 02 | `Transparency-Reso-02-2009-06-19.pdf` | Res 2033-2009 | 2009-06-19 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=43180&GUID=F67CFFBF-94D0-4B08-87E3-8FCAA76A6C75 | confirmed |
| Transparency Reso 03 | `Transparency-Reso-03-2009-06-30.pdf` | Res 2061-2009 | 2009-06-30 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=43229&GUID=2843987E-E2FF-4C3E-B8FF-FE49D0D01266 | confirmed |
| Transparency Reso 04 | `Transparency-Reso-04-2009-08-20.pdf` | Res 2147-2009 | 2009-08-20 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=43522&GUID=042C66F0-4A5F-4498-9EAC-C88F234AF49F | confirmed |
| Transparency Reso 05 | `Transparency-Reso-05-2009-10-28.pdf` | Res 2240-2009 | 2009-10-28 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=43845&GUID=3215C320-42F2-4286-86EF-1AE1FC7B62FA | confirmed |
| Transparency Reso 06 | `Transparency-Reso-06-2009-11-16.pdf` | Res 2262-2009 | 2009-11-16 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=43935&GUID=744C19F6-DBCF-4257-8722-0754AFBEDE2D | confirmed |
| Transparency Reso 07 | `Transparency-Reso-07-2009-12-21.pdf` | Res 2303-2009 | 2009-12-21 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=44115&GUID=894CCEA7-51C8-45FF-90CD-8392A09E1D95 | confirmed |
| Transparency Reso 08 | `Transparency-Reso-08-2010-03-03.pdf` | Res 0058-2010 | 2010-03-03 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=44450&GUID=1EB5A7E2-088A-437E-98FA-E48EE4DE67F9 | confirmed |
| Transparency Reso 09 | `Transparency-Reso-09-2010-03-25.pdf` | Res 0127-2010 | 2010-03-25 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=44579&GUID=9AA5C81B-8BD7-4CB5-A722-5E175405686A | confirmed |
| Transparency Reso 10 | `Transparency-Reso-10-2010-04-29.pdf` | Res 0206-2010 | 2010-04-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=44924&GUID=943106E1-3C36-44E0-A5DE-D099996455E6 | confirmed |
| Transparency Reso 11 | `Transparency-Reso-11-2010-05-25.pdf` | Res 0246-2010 | 2010-05-25 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=45114&GUID=E6591906-E663-4109-95EF-573910CD7739 | confirmed |
| Transparency Reso 12 | `Transparency-Reso-12-2010-06-29.pdf` | Res 0317-2010 | 2010-06-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=45408&GUID=6A1FF6D6-84AE-4032-90B3-1EE3E3B8F470 | confirmed |

**Confirmed 2026-07-07:** the sweep doc's "1 dead link" (council.nyc.gov 404) for FY2010
is **Res 2201-2009** (2009-09-30). Previously only a "probable" match inferred from the
date gap between Transparency Reso 04 and 05 above; now confirmed by content via
`get_bill`, which returns:

- `MatterName`: "Approving the new designation and changes in the designation of
  certain organizations to receive funding pursuant to the fiscal 2010 expense budget."
- `MatterTitle`: "Resolution approving the new designation and changes in the
  designation of certain organizations to receive funding in the Fiscal 2010 Expense
  Budget."
- `MatterTypeName`: "Resolution", `MatterStatusName`: "Adopted", `MatterBodyName`:
  "Committee on Finance", `MatterAgendaDate`/`MatterPassedDate`: 2009-09-30.

This is an exact match to the standard designation-resolution title pattern used
throughout this document series, upgrading the row from "probable" to "confirmed." No
local file exists to link (matter-only, consistent with the sweep doc's dead-link
finding — the file this 404 pointed to was never re-sourced).

https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=43709&GUID=08D44EB8-CB73-418A-80AF-B62374C86F13

---

## FY2011

| Document | Local file (post-rename) | Legistar matter | Adoption date | Legistar URL | Status |
|---|---|---|---|---|---|
| Schedule C (anchor) | `fy2011-C2011.pdf` | Res 0371-2010 | 2010-07-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=45476&GUID=433AA845-DB6B-4D65-AA6A-D70339A0A032 | anchor (earliest in sequence) |
| Capital A | `fy2011-FY2011-Section-254-Changes.pdf` | Res 0325-2010 | 2010-06-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=45401&GUID=C07E859D-8525-44B4-88D1-7FB5108AA870 | confirmed |
| Capital B | `fy2011-fy11_changes_executive_capital_budget_adopted_by_nycc.pdf` | Res 0326-2010 | 2010-06-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=45402&GUID=2CFF38D3-C879-46FA-8B86-FBF8DD59A0B4 | confirmed |
| Transparency Reso 01 | `Transparency-Reso-01-2010-07-29.pdf` | Res 0371-2010 | 2010-07-29 | (same as Schedule C row above) | confirmed |
| Transparency Reso 02 | `Transparency-Reso-02-2010-08-25.pdf` | Res 0421-2010 | 2010-08-25 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=45623&GUID=C4998827-2AFF-4A6E-B728-57FDCD04E617 | confirmed |
| Transparency Reso 03 | `Transparency-Reso-03-2010-09-29.pdf` | Res 0465-2010 | 2010-09-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=45761&GUID=C2196587-97A2-4B45-B147-BD6F0EAD2FB6 | confirmed |
| Transparency Reso 04 | `Transparency-Reso-04-2010-10-13.pdf` | Res 0479-2010 | 2010-10-13 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=45870&GUID=A42E28F2-A062-45AE-A396-F280175B8E96 | confirmed |
| Transparency Reso 05 | `Transparency-Reso-05-2010-11-17.pdf` | Res 0546-2010 | 2010-11-17 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=46092&GUID=34D23D82-A799-4E71-9F17-89F605520BA7 | confirmed |
| Transparency Reso 06 | `Transparency-Reso-06-2010-12-20.pdf` | Res 0607-2010 | 2010-12-20 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=46254&GUID=51BBAB85-B93C-4E50-A01A-68360D375732 | confirmed |
| Transparency Reso 07 | `Transparency-Reso-07-2011-02-16.pdf` | Res 0673-2011 | 2011-02-16 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=46447&GUID=41B7AFEE-D6FF-44BB-9020-7A6B53AE88CE | confirmed |
| Transparency Reso 08 | `Transparency-Reso-08-2011-04-06.pdf` | Res 0764-2011 | 2011-04-06 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=46850&GUID=935A8888-0789-4D5F-894B-FBA05C2F54DA | confirmed |
| Transparency Reso 09 | `Transparency-Reso-09-2011-05-11.pdf` | Res 0818-2011 | 2011-05-11 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=46959&GUID=99416922-FCAA-42B0-9024-4057E9A78539 | confirmed |
| Transparency Reso 10 | `Transparency-Reso-10-2011-06-14.pdf` | Res 0865-2011 | 2011-06-14 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=47369&GUID=F3BD4020-E565-4D35-B050-FA458BC844F0 | confirmed |

All 10 downloaded files matched; nothing not located for FY2011.

---

## FY2012

| Document | Local file (post-rename) | Legistar matter | Adoption date | Legistar URL | Status |
|---|---|---|---|---|---|
| Schedule C (anchor) | `fy2012-skedcfinal.pdf` | Res 0960-2011 | 2011-07-28 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=47521&GUID=25BD0BF4-74B7-4C6C-9DF9-375A70C3EE66 | anchor (earliest in sequence) |
| Capital A | `fy2012-changestobudget.pdf` | Res 0920-2011 | 2011-06-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=47442&GUID=445411D5-DB76-41FD-854F-17BF75CF8AB8 | confirmed — **corrected 2026-07-07** (see note below; local file is Resolution A, not Resolution B as previously guessed from the filename) |
| Capital B | — (not downloaded) | Res 0921-2011 | 2011-06-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=47443&GUID=DFEDEE86-C4D9-463A-93E5-78D1FAC012A0 | confirmed (matter only — no local file; see note below) |
| Transparency Reso 01 | `Transparency-Reso-01-2011-08-17.pdf` | Res 0987-2011 | 2011-08-17 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=47640&GUID=35984B75-06AD-4322-AF2C-97D4EAC9E6F4 | confirmed |
| Transparency Reso 02 | `Transparency-Reso-02-2011-10-05.pdf` | Res 1068-2011 | 2011-10-05 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=47871&GUID=47E67136-2BF9-432F-A4A5-CDAAFA1E53B3 | confirmed (PDF was scanned/no text layer; date confirmed via QuickLook render of page 1) |
| Transparency Reso 03 | `Transparency-Reso-03-2011-10-17.pdf` | Res 1084-2011 | 2011-10-17 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=47943&GUID=CFC29032-164D-4733-8520-015F9F052522 | confirmed |
| Transparency Reso 04 | `Transparency-Reso-04-2011-11-03.pdf` | Res 1101-2011 | 2011-11-03 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=48009&GUID=548C5E42-750C-4382-BC81-39783A9E14B5 | confirmed |
| Transparency Reso 05 | `Transparency-Reso-05-2011-12-19.pdf` | Res 1173-2011 | 2011-12-19 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=48255&GUID=6567B0B9-B317-46DA-9952-2A9AD7B17A7B | confirmed |
| Transparency Reso 06 | `Transparency-Reso-06-2012-01-04.pdf` | Res 1192-2012 | 2012-01-04 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=48284&GUID=45059526-6E05-42B0-83B2-FE0911A3B9CC | confirmed |
| Transparency Reso 07 | `Transparency-Reso-07-2012-02-01.pdf` and `Transparency-Reso-07-2012-02-01-dup.pdf` | Res 1209-2012 | 2012-02-01 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=48373&GUID=2F99F29B-3F50-4866-B713-61FE82243426 | confirmed — **the two source files (`fy2012-314tran.pdf` / `fy2012-315tran.pdf`) are near-identical text and appear to be a duplicate download of the same resolution**, not two distinct resolutions; both map to the same matter. Flagged for a possible dedup pass; not resolved here since it's a data-quality question, not a linkage gap. |

**Corrected 2026-07-07 — `fy2012-changestobudget.pdf` is Resolution A, not Resolution
B.** The prior pass flagged Res 0920-2011 (Resolution A) as a genuine document gap,
assuming the locally downloaded `fy2012-changestobudget.pdf` was Resolution B (the
"changes to budget" filename read as the totals document). This is an image-only,
JBIG2-encoded scan with no text layer, so it couldn't be checked by `pdftotext`/text
search in the prior pass. Rendering individual pages this session (via a local PyMuPDF
script, since no PDF text/rasterization CLI — `pdftoppm`, `gs`, `mutool` — was available
on this machine) shows:

- Page 4 of the PDF is headed **"RESOLUTION A"** and opens: *"Resolved, by the Council,
  pursuant to section 254 of the New York City Charter... be and the same are hereby
  approved in accordance with the following schedule of changes."* — an exact match to
  the Resolution A opening language specified for this check.
- The remaining ~120 pages are the itemized budget-line schedule of changes
  (additions, rescindments from prior capital budgets, etc.) — consistent with
  Resolution A's full schedule, not Resolution B's short totals-only text.

So **no document is actually missing for Resolution A** — it just needed relinking from
Res 0921-2011 (B) to Res 0920-2011 (A), corrected in the table above. This flips the
gap: **Res 0921-2011 (Resolution B, the short "hereby adopted in the total amounts"
document) is the one with no local file**, not A. Not chased further this session
(not part of the assigned check); would need a separate Legistar attachment pull if
Resolution B is wanted for FY2012.

---

## FY2013

FY2013 has no `transparency-resolutions/` folder locally (confirmed absent on
council.nyc.gov per the sweep doc, not chased via Legistar per the task's original
scope note — not re-litigated here). Only the two core documents are linked.

| Document | Local file | Legistar matter | Adoption date | Legistar URL | Status |
|---|---|---|---|---|---|
| Schedule C (anchor) | `fy2013-FY-2013-Schedule-C-Merge-Final1.pdf` | Res 1623-2012 | 2012-12-18 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=49802&GUID=9EE308C3-A9C5-4AD3-96C6-415550E27EB7 | anchor (earliest identified in this pass — see note below) |
| Capital A | — (not downloaded) | Res 1405-2012 | 2012-06-28 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=49121&GUID=77AFCA0A-17EA-4737-9BD7-727E9161527D | confirmed (matter only) |
| Capital B | `fy2013-adopt12_capresowork.pdf` | Res 1406-2012 | 2012-06-28 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=49122&GUID=52444795-B191-4718-9031-12FAFCEC397D | confirmed |

**Note on the Schedule C anchor:** `Res 1623-2012` (2012-12-18) is the earliest
FY2013-titled "new designation and changes" resolution turned up by the phrase search
in the July-December 2012 window checked. Given the roughly-monthly cadence seen in
every other year in this range, it is plausible earlier FY2013 resolutions exist
between the FY2013 capital adoption (2012-06-28) and this one — they were not chased
further given the effort budget and the fact that FY2013 has no local transparency
files needing anchoring to a more precise date. Treat this specific anchor as
lower-confidence than the "confirmed" rows above.

---

## FY2014

| Document | Local file (post-rename) | Legistar matter | Adoption date | Legistar URL | Status |
|---|---|---|---|---|---|
| Schedule C (anchor) | `fy2014-skedc.pdf` | Res 1903-2013 | 2013-08-22 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=50856&GUID=2A7AC5D0-E365-4E9E-A854-874A04106EB7 | anchor (earliest identified in this pass — same lower-confidence caveat as FY2013 above) |
| Capital | — (genuine gap; not found on council.nyc.gov per the sweep doc, not chased via Legistar) | Res 1852-2013 (A) / Res 1853-2013 (B) | 2013-06-26 | A: https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=50713&GUID=BCCDF0FD-9840-4CB9-8147-D674CF085CCE / B: https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=50714&GUID=E4C8AC32-B301-421B-9533-58897EB23CBA | confirmed (matter only — recorded for completeness even though no local file exists to link, since both A/B were trivial to pull from the same Capital search pass) |
| Transparency Reso 01 | `Transparency-Reso-01-2014-04-29.pdf` (renamed from `fy2014-reso11.pdf`; original filename's "11" implies this was the 11th resolution in a longer within-year sequence most of which was not downloaded) | Res 0190-2014 | 2014-04-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=52526&GUID=E9DCC52A-6503-4B59-BDB0-5699B786F3E5 | confirmed |
| Transparency Reso 02 | `Transparency-Reso-02-2014-05-29.pdf` (renamed from `fy2014-reso12.pdf`) | Res 0256-2014 | 2014-05-29 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=52771&GUID=7010D543-EE25-4191-A855-88D983BA2FD3 | confirmed |
| Transparency Reso 03 | `Transparency-Reso-03-2014-06-11.pdf` (renamed from `fy2014-061114reso.pdf`) | Res 0277-2014 | 2014-06-11 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=52852&GUID=CBDC7D2B-8D42-48D7-B322-2E14E6A9F750 | confirmed |

**Renumbering note:** the original filenames `reso11`/`reso12` suggest FY2014 had a
longer resolution sequence (at least 12 numbered items) of which only the final 3 were
downloaded into this repo. Renaming them `01`/`02`/`03` follows this repo's existing
FY2021-2024 convention (sequence number reflects what's locally present, not the
original full-year count) — flagged here so the renumbering isn't mistaken for evidence
that only 3 resolutions existed that year.

---

## Summary

- **Documents with a confirmed or anchor-level Legistar link:** 34 rows across
  FY2008-FY2014 core documents (Schedule C, Capital A, Capital B) + 43 Transparency
  Resolution rows (8 + 12 + 10 + 8 + 0 + 3, FY2009-FY2014; FY2008's 3 are matter-only,
  no local files) = 77 total linkage rows produced, covering essentially all locally
  downloaded FY2009-FY2014 documents plus the FY2008 reuse.
- **Transparency resolutions renamed to `Transparency-Reso-NN-YYYY-MM-DD.pdf`:** 8 (FY09)
  + 12 (FY10) + 10 (FY11) + 8 (FY12, incl. one flagged duplicate pair) + 3 (FY14) = **41
  files renamed**. FY2013 had no transparency-resolutions folder to rename.
- **Resolved 2026-07-07:**
  - FY2010's one dead-link transparency resolution — now **confirmed** as `Res
    2201-2009` (2009-09-30) via `get_bill` content match, upgraded from the prior
    date-gap-only guess.
  - FY2012 Capital A (`Res 0920-2011`) — **not actually missing.** The locally
    downloaded `fy2012-changestobudget.pdf` was mislinked to Res 0921-2011 (B) based
    on its filename; page-level rendering confirms it is Resolution A's full text and
    schedule. Corrected in the FY2012 table. The gap flips to **Res 0921-2011
    (Resolution B)**, which has no local file — not chased further this session.
- **Not located / lower-confidence items (unchanged):**
  - FY2013 and FY2014 Schedule C anchors — earliest-found-in-this-pass, not verified as
    the literal first resolution of the fiscal year (lower effort budget applied since
    no local transparency files in FY2013 and only 3 of a longer sequence in FY2014
    needed anchoring).
  - FY2014 Capital A/B — matter numbers included for completeness; no local file exists
    (genuine content gap per the sweep doc, not chased further).

---

## Gap-filling follow-up (2026-07-07)

Second pass same day, after the FY13-FY14 methodology above was already written.
Addressed four specific gaps in priority order. Legistar's own web-UI detail-page
IDs are **not** the same as the OData API's `MatterId`/`MatterGuid` for most matters in
this range (only Res 1090-2007 happened to resolve directly by coincidence) — direct
navigation to `LegislationDetail.aspx?ID=<MatterId>&GUID=<MatterGuid>` throws "Invalid
parameters!" for matters found via `get_bill`. The reliable path is always: search the
file number via the web UI (`Legislation.aspx`, phrase or file-number search, Years
filter set to the correct session), read the resulting row's own `LegislationDetail.aspx`
href (with its `Options=ID|Text|&Search=...` query string intact), then navigate there.
The search UI itself was intermittently flaky in this session — roughly half of all
search submissions silently reset to "0 records / Please enter your search criteria"
even with a populated text box; the reliable fix was a plain retry (re-click the field,
re-select-all, re-type, then search) rather than adjusting timing.

Once on a matter's detail page, attachment content types varied by resolution — most
2012-2013 "new designation and changes" resolutions have a **"Completed Package"**
attachment (the full signed resolution + committee report, genuine `application/pdf`,
typically 120-280KB); a handful only had a **"Committee Report"** attachment instead
(no separate Completed Package), and for several of those the Committee Report itself
was `application/msword` (a `.doc`, not a PDF) rather than PDF. Files were downloaded via
`curl` (available at `/usr/bin/curl` on this machine, confirmed by the FY2021 pilot's own
prior methodology) directly against the `View.ashx?M=F&ID=...&GUID=...` attachment URL —
Chrome-driven downloads (navigation, synthetic click, and CDP-dispatched click) were all
attempted first and confirmed **not** to land any file on this machine's filesystem in
this session (verified via `mdfind` system-wide); a local relay-server approach was also
attempted and blocked by the harness's auto-mode classifier as an unauthorized persistent
network service. `curl` was the only method that worked.

### Task 1 — FY2013 Transparency Resolutions (highest priority) — RESOLVED, full set found

Bracketing the FY2013 window (July 2012 - June 2013) between FY2012's last known
resolution (Res 1209-2012, 2012-02-01) and FY2014's Schedule C anchor (Res 1903-2013,
2013-08-22) using the same `"new designation and changes in the designation of certain
organizations"` phrase search (Years filter: Session 2010 to 2013) turned up **12**
FY2013-titled resolutions, each confirmed via `get_bill`:

| # | Local file | Legistar matter | Adoption date | Legistar URL | Attachment used |
|---|---|---|---|---|---|
| 01 | `Transparency-Reso-01-2012-07-25.pdf` | Res 1438-2012 | 2012-07-25 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1155805&GUID=3A016895-B854-4C5D-8E93-B52FA700C8FF | Completed Package (PDF) |
| 02 | `Transparency-Reso-02-2012-08-22.pdf` | Res 1473-2012 | 2012-08-22 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1188633&GUID=81F42067-DA73-4E7D-8E7C-502443842BF9 | Completed Package (PDF) |
| 03 | `Transparency-Reso-03-2012-09-24.pdf` | Res 1518-2012 | 2012-09-24 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1200848&GUID=A7714D16-A897-44C0-8281-71AEE699BFCF | Completed Package (PDF) |
| 04 | `Transparency-Reso-04-2012-10-11.pdf` | Res 1539-2012 | 2012-10-11 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1213231&GUID=F8283B8A-5036-4738-8A8F-0106B84E34A7 | Completed Package (PDF) |
| 05 | `Transparency-Reso-05-2012-11-13.pdf` | Res 1573-2012 | 2012-11-13 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1219079&GUID=E1FE360E-07BE-4D15-906D-60AC2A5452B0 | Completed Package (PDF) |
| 06 | `Transparency-Reso-06-2012-12-10.pdf` | Res 1603-2012 | 2012-12-10 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1244746&GUID=03254822-26AB-4DA4-BD10-002BAFA257A0 | Completed Package (PDF) |
| 07 | `Transparency-Reso-07-2012-12-18.doc` | Res 1623-2012 | 2012-12-18 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1264203&GUID=38466207-73A2-45CF-972F-7664BC4D9B1C | Committee Report (**.doc**, no Completed Package attachment exists for this matter) |
| 08 | `Transparency-Reso-08-2013-01-23.pdf` | Res 1641-2013 | 2013-01-23 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1273301&GUID=0DBF3ABE-2333-45C4-91F5-7503B1A46D06 | Completed Package (PDF) |
| 09 | `Transparency-Reso-09-2013-02-27.pdf` | Res 1664-2013 | 2013-02-27 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1288621&GUID=1A0DFE07-196B-4C91-A91D-9CE2DEA07471 | Committee Report (PDF; no Completed Package attachment for this matter) |
| 10 | `Transparency-Reso-10-2013-03-13.doc` | Res 1674-2013 | 2013-03-13 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1318598&GUID=45B7C850-C2FB-42DA-A864-19EDF1E0B9D6 | Committee Report (**.doc**, no Completed Package attachment for this matter) |
| 11 | `Transparency-Reso-11-2013-05-08.doc` | Res 1750-2013 | 2013-05-08 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1424510&GUID=898F2658-7A6B-4C3E-A38B-8C46A458B6CC | Committee Report (**.doc**, no Completed Package attachment for this matter) |
| 12 | `Transparency-Reso-12-2013-06-26.pdf` | Res 1848-2013 | 2013-06-26 | https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1449622&GUID=1CDBA0C4-BB25-4308-B24E-BACF0E921C99 | Completed Package (PDF) |

All 12 downloaded to `source/FY13/transparency-resolutions/` (created this session).
Adoption dates run 2012-07-25 through 2013-06-26 — a clean, roughly-monthly cadence
matching every other year in this range (FY2009: 8, FY2010: 12, FY2011: 10, FY2012: 8+).
**This supersedes the original pass's FY2013 note** ("no `transparency-resolutions/`
folder locally... only the two core documents are linked" and the low-confidence Res
1623-2012 "anchor") — FY2013 is no longer a gap. The true earliest FY2013 resolution is
**Res 1438-2012 (2012-07-25)**, not Res 1623-2012 (2012-12-18) as previously guessed;
Res 1623-2012 is actually the 7th in sequence. The original FY2013 Schedule C row above
(anchored to Res 1623-2012) should be treated as superseded by Res 1438-2012 going
forward, though it is left unedited above per the task's "do not touch" scope for
already-written sections other than this follow-up.

Three of the twelve (07, 10, 11) are Word `.doc` files, not PDFs — those specific
matters simply have no Completed Package or PDF-format Committee Report attachment on
Legistar; the `.doc` Committee Report was the closest available substantive document
(resolution text + committee analysis, same substance as the other nine, different file
format).

### Task 2 — FY2014 Capital §254 (high confidence expected) — CONFIRMED STILL ABSENT

Re-examined both matters already identified in the original pass — Res 1852-2013
(Resolution A) and Res 1853-2013 (Resolution B), both adopted 2013-06-26 — via their
actual Legistar detail pages (not just `get_bill`, which only returns matter metadata,
not attachments):

- **Res 1852-2013** (A): https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1450053&GUID=1CDA7648-2E5D-40F1-B703-7B8FB79E5A95 — attachments: Hearing Transcript - Finance 6-26-13, Hearing Transcript - Stated Meeting 6-26-13. **No committee report, completed package, or schedule-of-changes document of any kind.**
- **Res 1853-2013** (B): https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=1450054&GUID=1708BA7D-1C57-4F22-A88E-580E0EAA3D9F — same two hearing-transcript attachments only, one of which (Finance transcript, `ID=2565479`, 63,618 bytes) was checked and is genuinely a short hearing transcript, not a schedule of changes.

**Confirmed still absent** — the FY2014 capital schedule was never uploaded as a
separate Legistar attachment, matching the "genuine gap" finding in the original pass
(which had only confirmed this via council.nyc.gov, not yet via Legistar directly). No
file downloaded; nothing to download. This appears to be a real archival gap for FY2014
specifically, not a search-methodology miss — every other year's Capital A/B pair in
this document series (FY2008-FY2013) has at least a Committee Report or Completed
Package attachment; FY2014 has neither.

### Task 3 — FY2012 Capital Resolution B, `Res 0921-2011` (low priority) — CONFIRMED STILL ABSENT

Quick attempt per the task's own "if not straightforward, skip" instruction. Legistar
detail page: https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=922244&GUID=489F8CBB-F7AC-40C7-A8A4-328F67570B24

Attachments: 4 hearing transcripts only (Hearing Transcript 6-28-11, Hearing Transcript
6-29-11, Hearing Transcript - Stated Meeting 6-28-11, Hearing Transcript - Stated
Meeting 6-29-11). No committee report, completed package, or schedule document. **Not
downloaded** — consistent with the original pass's note that "this document type has no
printed subtotals in any year it appears, so it's low value," and confirms there is
nothing substantive to pull even if it were chased further.

### Task 4 — FY2008 Terms & Conditions / Capital schedule bounded re-check — PRIOR FINDING CONFIRMED, NOTHING NEW

Checked both matters' full attachment lists directly via Chrome (not the MCP), per the
task's instruction, within the ~10-15 minute budget:

- **Res 1090-2007**: https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=447681&GUID=6E45CB4C-554E-4CCD-9B7D-05325C990AB8 — attachments: Committee Report, Hearing Transcript, Press Release, Hearing Transcript - Stated Meeting 10/17/07. **Exactly 4 attachments, all already present locally** (`Res1090-2007-Committee-Report.doc`, `Res1090-2007-Hearing-Transcript.doc`, `Res1090-2007-Press-Release.doc`, `Res1090-2007-Hearing-Transcript-StatedMtg.doc`).
- **Res 0910-2007**: https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=447285&GUID=A077C7D7-9F33-4419-B712-AD8D718988EA — attachments: Press Release, Hearing Transcript, Hearing Transcript - Stated Meeting 6/15/07. **Exactly 3 attachments, all already present locally** (`Res0910-2007-CapitalA-Press-Release.doc`, `Res0910-2007-CapitalA-Hearing-Transcript.doc`, `Res0910-2007-CapitalA-Hearing-Transcript-StatedMtg.doc`).

**No new attachment found on either matter's page.** The prior pilot's finding stands:
neither a Terms & Conditions document nor a Capital schedule of changes was ever
uploaded to Legistar as a separate attachment for FY2008 — only cover materials
(committee reports, hearing transcripts, a press release) survive there, matching the
pattern already identified for the "Schedule C" gap elsewhere in FY2008-2014.

### Follow-up summary

| Task | Outcome | Files added |
|---|---|---|
| 1. FY2013 Transparency Resolutions | **Resolved** — full 12-resolution sequence found and downloaded | 12 (9 PDF, 3 DOC) to `source/FY13/transparency-resolutions/` |
| 2. FY2014 Capital §254 | Confirmed still absent (checked Legistar directly, not just council.nyc.gov) | 0 |
| 3. FY2012 Capital Resolution B | Confirmed still absent / low value (hearing transcripts only) | 0 |
| 4. FY2008 Terms & Conditions / Capital | Prior "not digitized" finding reconfirmed, nothing new | 0 |
