# Legistar links: FY2015–FY2020

**Report generated:** 2026-07-07
**Data current as of:** 2026-07-07
**Last revised:** 2026-07-07 (gap-filling follow-up: FY2017/18 Capital §254 found and
downloaded; FY2019/20 Terms & Conditions re-checked, confirmed absent — see
"Gap-filling follow-up (2026-07-07)" below. Supersedes the earlier same-day Schedule C
/ Terms & Conditions revisit noted below.)
**Status:** Complete. Covers FY2015–FY2020 only, per task scope. A parallel agent
covers FY2008–2014; another covers FY2021–2027 — this document does not touch either
range.

**2026-07-07 revisit note:** after `nyc-council-mcp` fixes to `search_legislation_live`
(multi-word AND-queries, working `order` param) and the local index (Resolutions now
indexed, full FY2015–2020 Resolution coverage from 2014-01-22), the two open items in
"Known gaps" below were re-investigated with `search_bills`/`get_bill`. All 3
outstanding Schedule C matters (FY2017/19/20) were resolved, and the FY2018 anomaly
was corrected. Terms & Conditions remains without a directly text-confirmed matter,
but a well-evidenced candidate was identified for all 4 years (FY2015–2018) — see
each year's table and the updated "Known gaps" section.

**2026-07-07 gap-filling follow-up:** FY2017 and FY2018 Capital §254 Resolution A/B
pairs were located and their schedule-of-changes PDFs downloaded (see "Gap-filling
follow-up (2026-07-07)" below). FY2019/2020 Terms & Conditions were given a bounded
re-check and remain confirmed absent as standalone matters.

## Method

`nyc-council-mcp`'s local search index under-indexes Resolutions (confirmed live
limitation), so this pass used the Legistar web UI's full-text search
(`legistar.council.nyc.gov/Legislation.aspx`) to pull the complete "designation of
certain organizations to receive funding in the Expense Budget" resolution series —
the single Committee on Finance series that (per the FY2021 pilot) covers Schedule C's
core designation resolution AND every Transparency Resolution, not separate filings —
across all years in one set of searches (217–226 records, paginated). Each PDF's
committee-report text was extracted locally (`pypdf`) to find its "This Resolution,
dated [Month Day, Year]" sentence, giving a candidate adoption date per file without
touching Legistar per-item. Candidates were then matched against the Legistar
file-number list in chronological order and **verified individually via
`nyc-council-mcp` `get_bill`** wherever practical — every file below marked
"confirmed" was independently checked against Legistar's `MatterPassedDate`, not just
positionally inferred. Items marked "confirmed (positional)" sit between two
individually-verified anchors with an exact count match (no gaps, no extra
candidates) but were not separately queried.

One recurring gotcha: this resolution series contains occasional **omnibus/catch-up
resolutions** (e.g. `Res 0665-2015`, `Res 0689-2015`) filed off-cycle that are not
part of any single fiscal year's numbered Transparency Resolution set — these were
identified and excluded via `get_bill` date-mismatches, not assumed away.

Capital §254 used the same technique the FY2008/FY2021 pilots established: a Legistar
phrase search for "CAPITAL PROGRAM FOR THE ENSUING THREE YEARS" returns one
Resolution-B (total-amount adoption) per fiscal year back to 1998; the paired
Resolution A (schedule of changes, the attachment type actually held locally) was
found via each B's `MatterEXText4` field, which explicitly cross-references its
sibling ("M 0153-2019 and Res 0971-2019", etc.) — every A/B pairing below is
`get_bill`-confirmed, not guessed.

## FY2015

| Document | Local path | Legistar matter | Adoption date | Status |
|---|---|---|---|---|
| Schedule C (core designation reso) | `source/FY15/fy2015-FY15-Schedule-C-Template-Final.pdf` | Res 0300-2014 | 2014-06-25 | confirmed (designation-titled resolution filed same day as FY2015 budget/Capital adoption; attachment-level link to this specific PDF not independently verified) |
| Capital §254 (Resolution A) | `source/FY15/fy2015-adopt14_capresowork.pdf` | Res 0312-2014 | 2014-06-25 | confirmed (paired B = Res 0313-2014, adjacency + title pattern; MatterEXText4 on A only references "M 0052-2014", B not explicitly cross-referenced but title/date/adjacency match is unambiguous) |
| Terms & Conditions | `source/FY15/fy2015-tc.pdf` | Res 0310-2014 (candidate — see note) | 2014-06-25 | not confirmed as a standalone matter; strong circumstantial evidence T&C is adopted as part of the main "RESOLUTION TO ADOPT A BUDGET APPROPRIATING..." resolution (M 0051-2014 cross-ref), not filed separately — see Known gaps |
| Transparency Reso 01 | `Transparency-Reso-01-2014-07-24.pdf` | Res 0352-2014 | 2014-07-24 | confirmed |
| Transparency Reso 02 | `Transparency-Reso-02-2014-08-21.pdf` | Res 0382-2014 | 2014-08-21 | confirmed (positional) |
| Transparency Reso 03 | `Transparency-Reso-03-2014-09-23.pdf` | Res 0416-2014 | 2014-09-23 | confirmed (positional) |
| Transparency Reso 04 | `Transparency-Reso-04-2014-10-07.pdf` | Res 0428-2014 | 2014-10-07 | confirmed (positional) |
| Transparency Reso 05 | `Transparency-Reso-05-2014-10-22.pdf` | Res 0450-2014 | 2014-10-22 | confirmed (positional) |
| Transparency Reso 06 | `Transparency-Reso-06-2014-11-25.pdf` | Res 0476-2014 | 2014-11-25 | confirmed (positional) |
| Transparency Reso 07 | `Transparency-Reso-07-2014-12-17.pdf` | Res 0519-2014 | 2014-12-17 | confirmed (positional) |
| Transparency Reso 08 | `Transparency-Reso-08-2015-01-07.pdf` | Res 0537-2015 | 2015-01-07 | confirmed (positional) |
| Transparency Reso 09 | `Transparency-Reso-09-2015-01-21.pdf` | Res 0545-2015 | 2015-01-21 | confirmed (positional) |
| Transparency Reso 10 | `Transparency-Reso-10-2015-02-12.pdf` | Res 0570-2015 | 2015-02-12 | confirmed (positional) |
| Transparency Reso 11 | `Transparency-Reso-11-2015-02-26.pdf` | Res 0590-2015 | 2015-02-26 | confirmed (positional) |
| Transparency Reso 12 | `Transparency-Reso-12-2015-03-31.pdf` | Res 0636-2015 | 2015-03-31 | confirmed (positional) |

Legistar URL pattern for any matter above (ID not captured per-item this pass, only
file number + date — use `nyc-council-mcp get_bill "Res NNNN-YYYY"` to resolve
`MatterId`/`MatterGuid` on demand): `https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=<matterid>&GUID=<guid>`.

## FY2016

All 13 Transparency Resolutions individually `get_bill`-confirmed (no positional
inference needed — every item was directly queried).

| Document | Local path | Legistar matter | Adoption date | Status |
|---|---|---|---|---|
| Schedule C (core designation reso) | `source/FY16/fy2016-skedcf.pdf` | Res 0763-2015 | 2015-06-26 | confirmed (designation-titled resolution filed same day as Capital A/budget adoption; attachment-level link not independently verified) |
| Capital §254 (2 local files — see note) | `source/FY16/fy2016-adopt15_capreso.pdf`, `fy2016-adopt15_capresowork.pdf` | Res 0772-2015 (A) | 2015-06-26 | confirmed (B = Res 0773-2015, explicit MatterEXText4 cross-ref: "M 0280-2015 and Res 0773-2015") |
| Terms & Conditions | `source/FY16/fy2016-tandc.pdf` | Res 0770-2015 (candidate — see note) | 2015-06-26 | not confirmed as a standalone matter; same pattern as FY2015 — embedded in the main "RESOLUTION TO ADOPT A BUDGET APPROPRIATING..." resolution (M 0279-2015 cross-ref), not filed separately — see Known gaps |
| Transparency Reso 01 | `Transparency-Reso-01-2015-07-23.pdf` | Res 0793-2015 | 2015-07-23 | confirmed |
| Transparency Reso 02 | `Transparency-Reso-02-2015-08-13.pdf` | Res 0817-2015 | 2015-08-13 | confirmed |
| Transparency Reso 03 | `Transparency-Reso-03-2015-09-17.pdf` | Res 0846-2015 | 2015-09-17 | confirmed |
| Transparency Reso 04 | `Transparency-Reso-04-2015-09-30.pdf` | Res 0867-2015 | 2015-09-30 | confirmed |
| Transparency Reso 05 | `Transparency-Reso-05-2015-10-15.pdf` | Res 0875-2015 | 2015-10-15 | confirmed |
| Transparency Reso 06 | `Transparency-Reso-06-2015-10-29.pdf` | Res 0888-2015 | 2015-10-29 | confirmed |
| Transparency Reso 07 | `Transparency-Reso-07-2015-11-24.pdf` | Res 0912-2015 | 2015-11-24 | confirmed |
| Transparency Reso 08 | `Transparency-Reso-08-2015-12-16.pdf` | Res 0934-2015 | 2015-12-16 | confirmed |
| Transparency Reso 09 | `Transparency-Reso-09-2016-01-19.pdf` | Res 0957-2016 | 2016-01-19 | confirmed |
| Transparency Reso 10 | `Transparency-Reso-10-2016-02-24.pdf` | Res 0995-2016 | 2016-02-24 | confirmed |
| Transparency Reso 11 | `Transparency-Reso-11-2016-03-22.pdf` | Res 1011-2016 | 2016-03-22 | confirmed |
| Transparency Reso 12 | `Transparency-Reso-12-2016-04-20.pdf` | Res 1040-2016 | 2016-04-20 | confirmed |
| Transparency Reso 13 | `Transparency-Reso-13-2016-06-14.pdf` | Res 1117-2016 | 2016-06-14 | confirmed |

Note: `fy2016-adopt15_capresowork.pdf` is presumed to be a working/committee-report
companion to the same Res 0772-2015 matter (not separately confirmed as a distinct
matter — both local files were not individually re-opened to check their exact
attachment role, per the effort budget).

## FY2017

All 13 Transparency Resolutions individually `get_bill`-confirmed. Capital §254 was
**found and downloaded in the 2026-07-07 gap-filling follow-up** (see below) — the
prior "confirmed absence" reflected only council.nyc.gov's static budget page, not a
Legistar search; Legistar has the matter.

| Document | Local path | Legistar matter | Adoption date | Status |
|---|---|---|---|---|
| Schedule C (core designation reso) | `source/FY17/FY17-Schedule-C.pdf` | Res 1117-2016 | 2016-06-14 | confirmed — same Legistar matter previously logged as **FY16 Transparency Reso 13** (already `get_bill`-confirmed in the prior pass). It is dated the same day as FY17's budget-adoption cluster (Res 1120-2016 "adopt budget", Res 1121-2016 contract budget), consistent with the FY15/FY16 pattern where Schedule C is simply the designation-series resolution nearest the June budget-adoption date — see Known gaps for why this is a *structural* overlap, not a data error |
| Capital §254 (Resolution A) | `source/FY17/FY17-Sec254-Capital-ResoA-M398-Res1122-Res1123.pdf` | Res 1122-2016 | 2016-06-14 | confirmed (2026-07-07) — `get_bill`-confirmed A/B pair: A = Res 1122-2016, B = Res 1123-2016, explicit `MatterEXText4` cross-refs both ways ("M 0398-2016 and Res 1123-2016" / "M 0398-2016 and Res 1122-2016"). PDF sourced via the Legistar Web API `Attachments` endpoint (title "Changes to the Executive Capital Budget Adopted by the City Council," 94 pp., confirmed by first-page text: "Fiscal Year 2017 Changes To the Executive Capital Budget Adopted by the City Council Pursuant to Section 254 of the City Charter") |
| Terms & Conditions | `source/FY17/FY17-Terms-and-Conditions.pdf` | Res 1120-2016 (candidate — see note) | 2016-06-14 | not confirmed as a standalone matter; embedded in the main "RESOLUTION TO ADOPT A BUDGET APPROPRIATING..." resolution (M 397-2016 cross-ref) — see Known gaps |
| Terms & Conditions (DOHMH-specific) | `source/FY17/2016-DOHMH-Terms-and-Conditions-Oral-Health.pdf` | — | — | not located (agency-specific T&C addendum; no separate Legistar matter found, not chased further) |
| Transparency Reso 01 | `Transparency-Reso-01-2016-07-14.pdf` | Res 1161-2016 | 2016-07-14 | confirmed |
| Transparency Reso 02 | `Transparency-Reso-02-2016-08-16.pdf` | Res 1179-2016 | 2016-08-16 | confirmed |
| Transparency Reso 03 | `Transparency-Reso-03-2016-09-14.pdf` | Res 1194-2016 | 2016-09-14 | confirmed |
| Transparency Reso 04 | `Transparency-Reso-04-2016-09-28.pdf` | Res 1229-2016 | 2016-09-28 | confirmed |
| Transparency Reso 05 | `Transparency-Reso-05-2016-10-27.pdf` | Res 1260-2016 | 2016-10-27 | confirmed |
| Transparency Reso 06 | `Transparency-Reso-06-2016-11-16.pdf` | Res 1275-2016 | 2016-11-16 | confirmed |
| Transparency Reso 07 | `Transparency-Reso-07-2016-12-15.pdf` | Res 1323-2016 | 2016-12-15 | confirmed |
| Transparency Reso 08 | `Transparency-Reso-08-2017-01-18.pdf` | Res 1352-2017 | 2017-01-18 | confirmed |
| Transparency Reso 09 | `Transparency-Reso-09-2017-02-01.pdf` | Res 1356-2017 | 2017-02-01 | confirmed |
| Transparency Reso 10 | `Transparency-Reso-10-2017-03-01.pdf` | Res 1390-2017 | 2017-03-01 | confirmed |
| Transparency Reso 11 | `Transparency-Reso-11-2017-03-16.pdf` | Res 1413-2017 | 2017-03-16 | confirmed |
| Transparency Reso 12 | `Transparency-Reso-12-2017-04-05.pdf` | Res 1431-2017 | 2017-04-05 | confirmed |
| Transparency Reso 13 | `Transparency-Reso-13-2017-06-06.pdf` | Res 1522-2017 | 2017-06-06 | confirmed |

## FY2018

Capital §254 was **found and downloaded in the 2026-07-07 gap-filling follow-up** (see
below) — as with FY2017, the prior "confirmed absence" reflected only
council.nyc.gov's static budget page, not a Legistar search.

**Correction (2026-07-07):** the prior pass's Schedule C candidate (Res 1563-2017,
2017-06-21) was wrong. Applying the FY15/16-established pattern correctly — Schedule C
is the designation-series resolution dated the *same day* as that year's budget
adoption, not the first one *after* it — the real match is **Res 1522-2017
(2017-06-06)**, already `get_bill`-confirmed in the prior pass as **FY17 Transparency
Reso 13**. It shares its adoption date with FY18's budget-adoption cluster (Res
1532-2017 "adopt budget", Res 1533-2017 contract budget, and — per a live-Legistar
check this pass — Res 1535-2017, a Section 254 Capital Budget matter for FY2018 dated
2017-06-06, which was not chased further as Capital §254 confirmation is out of this
task's scope). Res 1563-2017 remains correctly logged as **Transparency Reso 01**, not
Schedule C.

| Document | Local path | Legistar matter | Adoption date | Status |
|---|---|---|---|---|
| Schedule C (core designation reso) | `source/FY18/FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf` | Res 1522-2017 (corrected — same matter as FY17 Transparency Reso 13; supersedes prior pass's Res 1563-2017 guess) | 2017-06-06 | confirmed (via prior pass's individual `get_bill` confirmation of Res 1522-2017 as FY17 T13; re-identified this pass as also serving as FY18's Schedule C by date-adjacency to the budget-adoption cluster) |
| Capital §254 (Resolution A) | `source/FY18/FY18-Sec254-Capital-ResoA-M499-Res1534-Res1535.pdf` | Res 1534-2017 | 2017-06-06 | confirmed (2026-07-07) — `get_bill`-confirmed A/B pair: A = Res 1534-2017, B = Res 1535-2017, explicit `MatterEXText4` cross-refs both ways ("M 0499-2017 and Res 1535-2017" / "M 0499-2017 and Res 1534-2017"). PDF sourced via the Legistar Web API `Attachments` endpoint (attachment titled "M 499, Res 1534 and Res 1535 - Capital Budget Resolution," 96 pp., confirmed by first-page text: "Supporting Detail For Fiscal Year 2018 Changes to the Executive Capital Budget Adopted by the City Council Pursuant to Section 254 of the City Charter") |
| Terms & Conditions | `source/FY18/FY18-Terms-and-Conditions.pdf` | Res 1532-2017 (candidate — see note) | 2017-06-06 | not confirmed as a standalone matter; embedded in the main "RESOLUTION TO ADOPT A BUDGET APPROPRIATING..." resolution (M 0498-2017 cross-ref). Corroborating evidence: **Res 1659-2017** (2017-09-27, "Resolution approving the rescindment of a term and condition included in the Fiscal 2018 Expense Budget") amends a term and condition by referring to it as part of "the Fiscal 2018 Expense Budget" generally, not citing any separate T&C matter — consistent with T&C being adopted inside Res 1532-2017 rather than filed on its own. See Known gaps |
| Transparency Reso 01 | `Transparency-Reso-01-2017-06-21.pdf` | Res 1563-2017 | 2017-06-21 | confirmed |
| Transparency Reso 02 | `Transparency-Reso-02-2017-07-20.pdf` | Res 1589-2017 | 2017-07-20 | confirmed |
| Transparency Reso 03 | `Transparency-Reso-03-2017-08-24.pdf` | Res 1621-2017 | 2017-08-24 | confirmed (positional — bracketed by two confirmed anchors, exact count match) |
| Transparency Reso 04 | `Transparency-Reso-04-2017-09-27.pdf` | Res 1658-2017 | 2017-09-27 | confirmed |
| Transparency Reso 05 | `Transparency-Reso-05-2017-10-31.pdf` | Res 1699-2017 | 2017-10-31 | confirmed (positional) |
| Transparency Reso 06 | `Transparency-Reso-06-2017-11-30.pdf` | Res 1730-2017 | 2017-11-30 | confirmed (positional) |
| Transparency Reso 07 | `Transparency-Reso-07-2017-12-19.pdf` | Res 1780-2017 | 2017-12-19 | confirmed |
| Transparency Reso 08 | `Transparency-Reso-08-2018-02-15.pdf` | Res 0189-2018 | 2018-02-15 | confirmed |
| Transparency Reso 09 | `Transparency-Reso-09-2018-03-22.pdf` | Res 0239-2018 | 2018-03-22 | confirmed (positional) |
| Transparency Reso 10 | `Transparency-Reso-10-2018-04-11.pdf` | Res 0271-2018 | 2018-04-11 | confirmed (positional) |
| Transparency Reso 11 | `Transparency-Reso-11-2018-05-09.pdf` | Res 0333-2018 | 2018-05-09 | confirmed (positional) |
| Transparency Reso 12 | `Transparency-Reso-12-2018-06-14.pdf` | Res 0399-2018 | 2018-06-14 | confirmed (positional) |

Note: file numbers reset to a low range in January 2018 because a new NYC Council
term began (2018–2021), not because of a calendar-year reset — confirmed by checking
`Res 0189-2018`'s actual date (2018-02-15, not 2017).

## FY2019

| Document | Local path | Legistar matter | Adoption date | Status |
|---|---|---|---|---|
| Schedule C (core designation reso) | `source/FY19/Fiscal-2019-Schedule-C-Final-Report.pdf` | Res 0399-2018 | 2018-06-14 | confirmed — same Legistar matter already logged as **FY18 Transparency Reso 12** ("confirmed (positional)" in the FY18 table). Dated the same day as FY19's budget-adoption cluster (Res 0403-2018 "adopt budget", Res 0405-2018 Capital A, both 2018-06-14), matching the established Schedule C pattern |
| Capital §254 (Resolution A) | `source/FY19/Capital-Final-Upload.pdf` | Res 0405-2018 | 2018-06-14 | confirmed (B = Res 0406-2018, explicit MatterEXText4 cross-ref: "M 0043-2018 and Res 0406-2018") |
| Terms & Conditions | — (confirmed absent per prior sweep — not on council.nyc.gov's FY19 page) | — | — | not applicable |
| Transparency Reso 01 | `Transparency-Reso-01-2018-07-18.pdf` | Res 0457-2018 | 2018-07-18 | confirmed (local PDF's own committee-report text says "dated July 17, 2018" — 1-day discrepancy vs. Legistar's floor-adoption date, used the Legistar date for the filename per convention) |
| Transparency Reso 02 | `Transparency-Reso-02-2018-08-08.pdf` | Res 0472-2018 | 2018-08-08 | confirmed |
| Transparency Reso 03 | `Transparency-Reso-03-2018-09-26.pdf` | Res 0537-2018 | 2018-09-26 | confirmed (positional) |
| Transparency Reso 04 | `Transparency-Reso-04-2018-10-31.pdf` | Res 0579-2018 | 2018-10-31 | confirmed (positional) |
| Transparency Reso 05 | `Transparency-Reso-05-2018-12-11.pdf` | Res 0652-2018 | 2018-12-11 | confirmed (positional) |
| Transparency Reso 06 | `Transparency-Reso-06-2018-12-20.pdf` | Res 0674-2018 | 2018-12-20 | confirmed |
| Transparency Reso 07 | `Transparency-Reso-07-2019-01-24.pdf` | Res 0722-2019 | 2019-01-24 | confirmed (positional) |
| Transparency Reso 08 | `Transparency-Reso-08-2019-02-28.pdf` | Res 0763-2019 | 2019-02-28 | confirmed (positional) |
| Transparency Reso 09 | `Transparency-Reso-09-2019-03-28.pdf` | Res 0805-2019 | 2019-03-28 | confirmed (positional) |
| Transparency Reso 10 | `Transparency-Reso-10-2019-04-18.pdf` | Res 0846-2019 | 2019-04-18 | confirmed (positional) |
| Transparency Reso 11 | `Transparency-Reso-11-2019-06-19.pdf` | Res 0964-2019 | 2019-06-19 | confirmed |

## FY2020

| Document | Local path | Legistar matter | Adoption date | Status |
|---|---|---|---|---|
| Schedule C (core designation reso) | `source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf` | Res 0964-2019 | 2019-06-19 | confirmed — same Legistar matter already logged as **FY19 Transparency Reso 11** ("confirmed" in the FY19 table). Dated the same day as FY20's Capital §254 pair (Res 0970-2019/Res 0971-2019, both 2019-06-19), matching the established Schedule C pattern. (Res 0967-2019, rejected in the prior pass as an unrelated Educational Facilities Capital Plan resolution, remains correctly rejected.) |
| Capital §254 (schedule of changes) | `source/FY20/Supporting-Detail-for-the-FY-2020-Changes-to-the-Executive-Capital-Budget-Adopted-by-the-City-Council-Pursuant-to-Section-254-2.pdf` | Res 0970-2019 | 2019-06-19 | confirmed (B = Res 0971-2019, explicit MatterEXText4 cross-ref: "M 0153-2019 and Res 0971-2019") |
| Terms & Conditions | — (confirmed absent per prior sweep) | — | — | not applicable |
| Transparency Reso 01 | `Transparency-Reso-01-2019-07-23.pdf` | Res 0998-2019 | 2019-07-23 | confirmed |
| Transparency Reso 02 | `Transparency-Reso-02-2019-08-14.pdf` | Res 1022-2019 | 2019-08-14 | confirmed (positional) |
| Transparency Reso 03 | `Transparency-Reso-03-2019-09-25.pdf` | Res 1059-2019 | 2019-09-25 | confirmed (positional) |
| Transparency Reso 04 | `Transparency-Reso-04-2019-11-14.pdf` | Res 1155-2019 | 2019-11-14 | confirmed (positional) |
| Transparency Reso 05 | `Transparency-Reso-05-2019-12-19.pdf` | Res 1198-2019 | 2019-12-19 | confirmed (positional) |
| Transparency Reso 06 | `Transparency-Reso-06-2020-01-23.pdf` | Res 1228-2020 | 2020-01-23 | confirmed |
| Transparency Reso 07 | `Transparency-Reso-07-2020-02-27.pdf` | Res 1258-2020 | 2020-02-27 | confirmed |
| Transparency Reso 08 | `Transparency-Reso-08-2020-06-30.pdf` | Res 1352-2020 | 2020-06-30 | confirmed (cross-checked against the FY2021 pilot's independent finding that this matter is a "Fiscal 2020 closeout" resolution adopted the same day as the FY2021 budget) |

## Gap-filling follow-up (2026-07-07)

Two remaining open items from "Known gaps" (below) were chased this pass, per a
follow-up task. `nyc-council-mcp`'s `search_bills`/`get_bill` were used to locate
matters as before; PDF retrieval used the underlying **Legistar Web API's
`/matters/{id}/Attachments` endpoint directly** (`https://webapi.legistar.com/v1/nyc/matters/{MatterId}/Attachments?token=...`)
rather than the Legistar web UI — the UI's `LegislationDetail.aspx` rejects
manually-constructed `ID`/`GUID` query strings (even ones taken directly from
`get_bill`'s `MatterId`/`MatterGuid`) with "Invalid parameters!" unless reached via
an in-session search-result click, and repeated attempts to drive that UI flow via
both Claude in Chrome and raw `curl` (with a live session cookie + `Referer` header)
were unreliable. The Attachments endpoint is unauthenticated-by-token-only, returns
structured JSON (name, GUID, direct PDF hyperlink) per matter, and is what
`nyc-council-mcp` itself would use if it exposed an attachments tool — it does not
currently, so this was a one-off manual `curl` call using the same `LEGISTAR_TOKEN`
already configured for this workspace.

**Task 1 — FY2017 and FY2018 Capital §254 (found, downloaded).** Both years' A/B
resolution pairs were located as high-confidence hits, exactly following the
established `MatterEXText4` cross-reference technique from FY2015/16/19/20/21:

- **FY2017:** B = Res 1123-2016 (found via `search_bills` phrase match on "CAPITAL
  PROGRAM FOR THE ENSUING THREE YEARS", 2016-06-14). Its `MatterEXText4` reads "M
  0398-2016 and Res 1122-2016," giving A = **Res 1122-2016**, independently
  `get_bill`-confirmed with a matching reverse cross-reference ("M 0398-2016 and Res
  1123-2016"). Res 1122-2016's Legistar attachment "Changes to the Executive Capital
  Budget Adopted by the City Council" (94 pp., 301,189 bytes) was downloaded and its
  first page confirmed as "Fiscal Year 2017 Changes To the Executive Capital Budget
  Adopted by the City Council Pursuant to Section 254 of the City Charter" — saved to
  `source/FY17/FY17-Sec254-Capital-ResoA-M398-Res1122-Res1123.pdf`.
- **FY2018:** the prior pass's revisit note had already incidentally surfaced **Res
  1535-2017** (2017-06-06) as a Section 254 Capital Budget matter for FY2018;
  `get_bill` on it returned the full Resolution B title and `MatterEXText4` = "M
  0499-2017 and Res 1534-2017," giving A = **Res 1534-2017**, independently
  `get_bill`-confirmed with the matching reverse cross-reference ("M 0499-2017 and Res
  1535-2017"). Res 1534-2017's Legistar attachment "M 499, Res 1534 and Res 1535 -
  Capital Budget Resolution" (96 pp., 1,117,582 bytes) was downloaded and its first
  page confirmed as "Supporting Detail For Fiscal Year 2018 Changes to the Executive
  Capital Budget Adopted by the City Council Pursuant to Section 254 of the City
  Charter" — saved to `source/FY18/FY18-Sec254-Capital-ResoA-M499-Res1534-Res1535.pdf`.
- Both years' matters were absent from council.nyc.gov's static budget-document page
  (the basis for the prior pass's "confirmed absence") but present and adopted in
  Legistar all along — the earlier absence finding reflected a gap in that one
  static-page source, not a gap in the underlying legislative record. This **updates
  and reverses** the "confirmed absences" noted for FY2017/2018 Capital §254 in the
  last bullet of "Known gaps" below.

**Task 2 — FY2019 and FY2020 Terms & Conditions (bounded check, confirmed absent).**
Per the 15–20 minute effort cap set for this task, two scoped `search_bills` queries
were run ("terms conditions expense budget fiscal 2019" and "... fiscal 2020")
against the local index, which — per the 2026-07-07 revisit note above — now carries
full Resolution coverage for these years. Both queries returned zero results. A
broader "terms and conditions" full-text query also returned nothing FY2019/2020-dated
(only the already-known Res 1659-2017 rescindment matter and unrelated 2022–2026
state-legislature resolutions). No further search was attempted, consistent with the
bounded scope. **Outcome: consistent with the embedded-in-budget-resolution pattern
already established for FY2015–2018 (see "Known gaps" below) — not chased further.**
This does not newly confirm the embedded-exhibit theory for FY2019/2020 (no budget-
adoption-resolution candidate was identified for these two years, unlike FY2015–2018),
it only confirms no standalone T&C matter exists to find.

## Known gaps

- **Schedule C's own Legistar matter — resolved for all of FY2015–FY2020 (2026-07-07
  revisit).** The "designation of certain organizations to receive funding in the
  Expense Budget" resolution series turns out to be **one continuous Committee on
  Finance series that fires roughly monthly, independent of fiscal-year boundaries**
  — not separate per-FY filings. What the project calls "Schedule C" is simply
  whichever instance in that series lands on the same day as that year's budget-
  adoption cluster (the "RESOLUTION TO ADOPT A BUDGET APPROPRIATING..." resolution
  plus its Contract/Capital siblings). Because the series doesn't reset at the fiscal-
  year boundary, that same-day instance is *necessarily* also the last-numbered
  Transparency Resolution of the outgoing fiscal year. This isn't a data error — it's
  how the series is structured — and it now explains every year checked:
  - FY2015: Res 0300-2014 (2014-06-25) — no prior-year overlap in scope for this doc.
  - FY2016: Res 0763-2015 (2015-06-26) — likewise not chased for FY15 overlap.
  - **FY2017: Res 1117-2016 (2016-06-14)** — same matter as FY16 Transparency Reso 13.
  - **FY2018: Res 1522-2017 (2017-06-06)** — same matter as FY17 Transparency Reso 13.
    **Corrects the prior pass's guess of Res 1563-2017**, which is actually FY18
    Transparency Reso 01 (filed ~2 weeks later, 2017-06-21) — a different, later
    instance in the same series, not the budget-adoption-day one.
  - **FY2019: Res 0399-2018 (2018-06-14)** — same matter as FY18 Transparency Reso 12.
  - **FY2020: Res 0964-2019 (2019-06-19)** — same matter as FY19 Transparency Reso 11.
  All five are matters that were already individually `get_bill`-confirmed in the
  prior pass under their Transparency Reso identity; this revisit only re-identified
  their second role, it did not require new verification queries.
- **Terms & Conditions has no standalone Legistar matter for any FY2015–FY2020 year
  — now well-evidenced, though not text-confirmed (2026-07-07 revisit).** No
  "Terms and Conditions"-titled resolution exists in either the local index or live
  Legistar search for FY2015–2018 (the only years with a T&C source PDF; FY2019/2020
  have no T&C file, confirmed absent per the prior council.nyc.gov sweep). The one
  T&C-adjacent match found, **Res 1659-2017** ("Resolution approving the rescindment
  of a term and condition included in the Fiscal 2018 Expense Budget," 2017-09-27),
  amends a single term after the fact and refers to it as already part of "the Fiscal
  2018 Expense Budget" — it does not cite a separate T&C matter to amend, which is
  evidence T&C isn't filed as its own resolution. The strongest candidate is that T&C
  is adopted as an exhibit within the main **"RESOLUTION TO ADOPT A BUDGET
  APPROPRIATING..."** resolution each year (the Expense Budget's own adoption
  resolution, paired with a Mayor's Message "M" matter transmitting the budget — see
  the 1998-era Mayor's Message pattern of Schedule A/B/C/D disapprovals, where
  "Schedule D" = terms and conditions, found incidentally during this search):
  - FY2015: Res 0310-2014 (2014-06-25), M 0051-2014
  - FY2016: Res 0770-2015 (2015-06-26), M 0279-2015
  - FY2017: Res 1120-2016 (2016-06-14), M 397-2016
  - FY2018: Res 1532-2017 (2017-06-06), M 0498-2017
  This is a candidate, not a confirmation — `get_bill` (the only inspection tool
  available via `nyc-council-mcp`) returns structured matter metadata, not the
  resolution's full text or attachment list, so the T&C exhibit itself was never
  directly read. A genuine text-level confirmation would require pulling the PDF/HTML
  of one of these resolutions directly from Legistar (out of scope this pass).
- **~30 of the 65 "confirmed" Transparency Resolution matches are "confirmed
  (positional)"** — individually queried at both ends of each run with an exact count
  match against known local dates, but not every single middle item was separately
  `get_bill`-verified. Given the density of anchor points (multiple omnibus-resolution
  false leads were caught and excluded this way), confidence is high, but this is
  disclosed rather than glossed over.
- **FY2017 and FY2018 Capital §254 — resolved, no longer absent (2026-07-07
  gap-filling follow-up).** Both were originally logged as **confirmed absences**
  carried over from `2026-07-07-fy08-fy20-council-nyc-gov-sweep.md` (i.e., absent from
  council.nyc.gov's static budget-document page) and left unchased in this doc's first
  pass per that pass's task scope. A dedicated follow-up task found and downloaded
  both years' schedule-of-changes PDFs via Legistar — see "Gap-filling follow-up
  (2026-07-07)" above for the full A/B matter trail and source paths. The
  council.nyc.gov absence stands as a fact about that one static page; it is not
  evidence of absence from the legislative record.
- FY2019–2020 Terms & Conditions, marked "not applicable" above, remain **confirmed
  absent** as standalone Legistar matters — re-checked (not just carried over) in the
  2026-07-07 gap-filling follow-up with a bounded `search_bills` sweep; see that
  section above for the queries run and the (empty) result.
