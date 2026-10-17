# Follow-up questions from #85 (Open Data diff) and #86 (Internet Archive recovery)

**Report generated:** 2026-10-14 (office) · **Data current as of:** Open Data pulled 2026-10-14;
Internet Archive listed and downloaded 2026-10-14; our dataset is the 2026-10-12 re-pull.
Sources: [`2026-10-14-open-data-vs-disclosure-diff.md`](2026-10-14-open-data-vs-disclosure-diff.md),
[`2026-10-14-wayback-council-files.md`](2026-10-14-wayback-council-files.md).

Each item gives the question, why it matters, and a suggested answer where there is one.
**D** = a decision only the maintainer can make; **C** = something to check later; **M** = what
the data means.

## A. Which source is authoritative (decisions for 2.0)

1. **D: Add FY2009, FY2011 and FY2012 to the disclosure dataset from the Council's own archived
   workbooks?** They parse with the existing parser, need no new header synonyms, and agree with
   Open Data row for row after rounding. *Why:* four new years, "spreadsheets first", with no
   PDF. *Suggested:* yes, as `data/fy09…fy12/expense_disclosure/`, with `source_file` pointing at
   `source/wayback-council/` and the Wayback timestamp in the manifest.
2. **D: What to do about FY2010?** The Council's workbook has 2,592 rows ($111.6M); Open Data has
   5,981 ($357.8M). Both archived copies (2016, 2025) agree, so it is what the Council published.
   *Why:* publishing the Council file alone understates FY2010 by about $246M. *Suggested:* hold
   FY2010 out of the disclosure dataset. Offer Open Data's FY2010 as a separately labeled source
   ("NYC Open Data, frozen 2021-04-20") or not at all. Never merge the two into one table.
3. **D: Open Data as a second, parallel source for FY2009–FY2021?** *Why:* it carries later
   statuses, MOCS IDs, expanded member/source names and geocodes, but rounded amounts and some
   damaged EINs. *Suggested:* do not make it the primary for any year where a Council workbook is
   complete. If it is used, use it as an annotation joined by match tier (item 9), not a
   replacement.
4. **D: Which status do we show where the two disagree?** For FY2009–FY2013 Open Data is later
   (FY2009: 1,251 Pending in the workbook are Cleared in Open Data). For FY2017–FY2021 ours is
   later. *Suggested:* keep the workbook's raw `status`. Add `od_status` only if item 3 is
   adopted. Never overwrite.
5. **D: FY2013 lump rows.** Our FY2013 file carries 18 citywide initiatives as one row each
   (OST $50.65M, EarlyLearn $39.3M, …). Open Data itemizes them into 1,168 grantee rows. Lump
   and itemized sums agree for 13 of 18. They differ for EarlyLearn ($39.30M vs $52.09M), OST
   ($50.65M vs $50.84M), Senior Centers ($1.496M vs $1.429M), MWBE ($0.60M vs $0.63M) and IDUHA
   ($1.0M vs $999,998). *Why:* grantee-level questions about FY2013 initiatives are unanswerable
   from our file. *Suggested:* flag lump rows in the dataset (a `lump_row` column, rule: one row
   for a whole initiative where the itemized source has many). Link Open Data's itemization as a
   separate table, and do not replace the lumps.
6. **M: Is our FY2013 file a final record?** 53% of its rows ($380.7M of $398.9M) are Pending,
   and the Council never revised it (the 2025 capture is identical). *Why:* "Cleared $18.2M in
   FY2013" would be a badly misleading headline. *Suggested:* say in DATA-ANOMALIES.md that
   FY2013's statuses are an early snapshot, and do not headline Cleared totals for FY2013.
7. **D: Same question for FY2009 and FY2010** (1,389 and 1,544 Pending). *Suggested:* same
   treatment as item 6.

## B. Matching and normalization (#85)

8. **D: Accept Open Data's rounding as a match tier in any future reconciliation?** It explains
   958 rows. Open Data rounds half-up to whole dollars from FY2012 and to cents before.
   *Suggested:* yes, always as a separate tier that is never folded into "exact". Never copy a
   rounded amount over a published one.
9. **D: Attach Open Data MOCS IDs to our FY2013–FY2021 rows?** They are the only MOCS IDs that
   exist before FY2024 (unique except `FY09 Not an Award` ×2 and `FY09 2039` ×2). *Why:* a
   stable per-row key would make future snapshot diffs exact instead of composite-key guesses.
   *Suggested:* yes, as `od_mocs_id` plus `od_match_tier` (exact / rounded), only on unambiguous
   pairs. Leave blank otherwise.
10. **C: 1,600 Open Data EINs lost a leading zero** (FY2009–FY2018, typed `integer` in the
    dictionary). Padded for matching. *Suggested:* any reuse pads and flags, as here.
11. **M: Open Data's member names are a "member at the time" signal.** FY2021 `Richards` where
    ours says `Brooks-Powers` (60 rows), `Menchaca`/`Aviles` (48), `Torres`/`Feliz` (31).
    *Why:* this is the roster-at-export problem behind #72. *Suggested:* feed it to the member
    crosswalk as evidence (who held the designation in April 2021) and never replace the
    published member.
12. **C: Review a sample of the nominations.** 160 `grantee_differs` (likely re-designations), 66
    `ein_differs` and 199 `amount_differs` across all 13 years (`summary.csv`). *Suggested:* a
    reviewer checks ~20 against the workbooks before anyone cites "re-designated" as fact.
13. **C: FY2021, $17.0M more in ours than Open Data,** including 18 Food Pantries rows worth
    $16.0M that Open Data lacks. *Why:* the largest single difference after FY2010 and FY2013.
    *Suggested:* check against the FY2021 Transparency Resolutions (adoption-time designations
    vs later additions) before saying when they were added.
14. **C: The FY2018 $221 DFTA row** (`funded_disclosure_FY2018.xlsx` row 2289, "Department for
    the Aging", Senior Centers, Programs, and Enhancements) is the net one-row gap with Open Data.
    *Suggested:* look at it in the workbook. It may be a residual adjustment line.
15. **M: The two FY2009 "Not an Award" rows** (Borough President Discretionary Funding $533,000;
    Provider's Choice $1,200,000) are in both sources. *Suggested:* keep, and flag in
    DATA-ANOMALIES.md. They are not grants to an organization.
16. **C: 15 Open Data BBLs are `0`.** *Suggested:* treat as blank if geocodes are ever used.
17. **M: Open Data calls the dataset "applications for discretionary funding".** The rows are
    designations, not applications (the real application files are item 26). *Suggested:* note it
    wherever Open Data is cited, so nobody counts its rows as applications.
18. **C: The 2026-07-07 scoping note says Open Data's member "last-name format already
    matches".** It does not (`CC`/`Speaker`, `QN`/`Queens Delegation`, `Viverito`/`Mark-Viverito`).
    *Suggested:* add a one-line pointer from that note to this diff.

## C. Statuses and geocoding (#85)

19. **M: What do the extra status values mean?** `Government` (City agency recipient: 309 of
    311 FY2013 rows carry the City EIN 136400434), `Revoked` (7, FY2013), `Pending-Council` (2,
    FY2013), `Designated` (1, FY2021), and in the Council workbooks `CBO Defunded` (155, FY2012,
    all $0) and `Pending FC Clearance` (3, FY2011). Nothing defines them; the data dictionary is
    silent. *Suggested:* keep raw, `status_norm = other`, document observed usage. Ask Council
    Finance/RnD for definitions only if a product claim depends on them.
20. **D: FY2012 "Government" is $235.2M (49 rows),** shown as Cleared in Open Data. Count it as
    cleared? *Suggested:* no. Keep `other` and show it as its own line in any total.
21. **D: Adopt Open Data's geocoding columns?** 77.7% of rows geocoded (63–92% by year). Each
    geocode locates the grantee's mailing address; the method is undocumented. *Why:* a
    `council_district` on these rows says where the organization's office is, not where the
    money is spent or whose discretionary money it was. *Suggested:* do not adopt. If geography is
    wanted, geocode our own addresses for all years with one documented method (NYC GeoSearch;
    tracker #75 already lists it). That needs a separate OK.

## D. The Internet Archive files (#86)

22. **D: Which raw files to commit?** Committed: FY2009–FY2012 (2025 captures), four capital
    databases, the FY17 T&C CSV (9.3 MB). Cache only: duplicate older captures, the FY2013–FY2017
    snapshots (~15 MB), three application files (36 MB), the Open Data rows (47 MB CSV / 13 MB
    gzipped). *Suggested:* also commit the FY2013–FY2017 snapshots so the snapshot diffs are
    reproducible from the repo, **except** the 2014-10-16 FY2015 copy (item 23). For Open Data,
    commit a gzipped CSV only if 2.0 uses it (item 3).
23. **D: The 2014-10-16 FY2015 capture holds grantee contact names, phone numbers and emails.**
    The parser drops those columns by name. *Suggested:* never commit that file. Keep it in the
    local cache only, or delete it from the cache (your call: deletions are yours to run).
24. **C: Are the `2016/08/` files still live on council.nyc.gov?** They were captured in February
    2025. I made no direct Council request (not permitted this session). *Suggested:* one HEAD
    request per file, with your OK, would tell us whether the Council still serves them.
25. **D: Download the old site's JavaScript copies** (`funded_disclosure_2014.js` … `2017.js`, 4
    files, ~0.5 MB each)? They may be yet another snapshot of FY2014–FY2017. *Suggested:* skip
    unless snapshot history becomes a product feature (item 31).
26. **D: The application files are a new data class:** `unfunded_disclosure_FY2012.xls` (12,695
    "Not Funded", $2.63B requested), `FY2013_CM_Applications_REFORMAT.xlsx` (19,236 "Applied",
    $5.11B), `applied_disclosure_FY2014.xls` (22,096 "Applied", $4.86B). *Why:* who asked and was
    not funded is a question the award data cannot answer. *Suggested:* open a separate issue.
    Do not mix them into the award dataset. Check for personal contact data before any commit.
27. **C: Capital databases for FY18–FY25 were not found** under `Capital-Database*` or in the
    folders searched. *Suggested:* with your OK, 2–3 more CDX queries (e.g. a `[Cc]apital`
    filter across `uploads/sites/54/` years 2017–2025), and #88's RnD file list.
28. **C: Other Council files listed by CDX but not downloaded:** NYPD overtime T&C reports,
    DoITT/OTI capital spending reports, BQE capital plan, SBS T&C, HA MAP funded projects
    (`uploads/sites/54/2021–2026/`), `html/budget/docs/` (DOE financial reports, charter school
    data, crossing guard locations), T&C PDFs. *Suggested:* add them to the #84/#88 inventory as
    candidate Terms & Conditions sources. Download nothing yet.
29. **C: Wider CDX coverage.** Only `funded_disclosure` and `Capital Database` names were
    searched host-wide. *Suggested:* if FY2008 or other years matter, try `expense`, `schedule`,
    `designation` name filters (2–3 queries).

## E. Capital (#87, from the profiles)

30. **M: The grain differs by era.** FY15 is one row per sponsor per project (about 250 projects
    over 1,341 rows); FY16, FY26 and FY27 are one row per project; FY17 is in between (1,437 IDs
    over 1,469 rows). FY15 and FY16 end with a **totals row** that doubles a naive sum. The
    project ID format changes every era. *Suggested:* the #87 parser strips totals rows by rule
    (no organization/title, amounts equal to the column sums) and keeps a `grain` note per year.

## F. Snapshot history (#86)

31. **D: Is clearance-over-time a 2.0 feature?** FY2015 can be followed through six archived
    versions (October 2014, blank statuses, to 2016, then our 2026 file). *Suggested:* not for 2.0.
    Keep the diffs as research. Revisit if anyone asks "how long does clearance take".
32. **M: The June 2017 FY2017 file is a lump-row cut,** not a later state (Food Pantries 241 rows
    → one $4.0M row). The Council has published both shapes for the same year. *Suggested:* if a
    future re-pull suddenly loses hundreds of initiative rows, check for lumping before calling
    them removals. Worth a line in the snapshot-diff docs.
33. **C: The FY2015 December 2014 change** paired only 1,091 of 6,291 rows by the composite key,
    with 5,059 nominated as "likely re-issued". Probably a file-wide re-keying of `program_name`
    or `agency`. *Suggested:* low priority. Check only if the FY2015 history is used.

## G. Process

34. **D: Branch order.** This work sits on `feature/open-data-diff`, on top of PR #83, and changes
    `parse_expense_disclosure.py` (multi-sheet, contact columns, space thousands, an
    UPPERCASE-note fix). `--check` reports 0 stale; nothing committed changes. *Suggested:*
    open it as the next PR in the stack after #83, when you say so.
35. **C: The UPPERCASE note now uses `isupper()`.** Before, `CBO Defunded` (an acronym in mixed
    case) tripped it. No committed output changes. Mentioned only so it is not a surprise in
    review.
