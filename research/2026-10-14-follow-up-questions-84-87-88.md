---
title: "Follow-up questions from #84, #87 and #88"
created: 2026-10-14
type: research-note
status: draft
tags: [nyc-budget, open-data, capital, checkbook, follow-up]
issue: "BetaNYC/New-York-City-Budget#84, #87, #88 (epic #89)"
---

# Follow-up questions from #84, #87 and #88

**Report generated:** 2026-10-14
**Data current as of:** 2026-10-14
**Read with:** [Open Data inventory](2026-10-14-structured-data-inventory.md) and
[capital stage map](2026-10-14-capital-stage-map.md)

Each question says why it matters and, where I have one, a suggested answer. Questions marked
**(needs Noel)** are judgment calls or approvals. The rest can be resolved by research or code.

## Epic-level

**E-1. Checkbook returned `Empty response` on the first call today. Is the Checkbook API blocked
again from this network?** (needs Noel)
Why: stages 4 and 5 depend on it, and the July block (Incapsula) looked the same from the
client. Suggested answer: do not retry from a script. Check `checkbooknyc.com` by hand in a
browser on the same network, and check whether the Comptroller's office answered the July
access letter.

**E-2. Should 2.0 present capital as a budget-line story first and a project story second?**
(needs Noel)
Why: budget line is the only key shared by every stage. Projects link only by text match.
Suggested answer: yes. Make every capital tool answer at line grain with exact figures, and
label any project-level match "matched by budget line and title."

## #84: Open Data inventory

**84-1. Load `t474-a92g` (Council capital, reports FY2019–FY2026) into 2.0?** (needs Noel)
Why: it fills FY2019 and FY2021, which the repo's PDF capital lacks, and gives a second witness
for six other years. Suggested answer: yes. Its FY2025 total ($775,000,000, 1,325 rows) already
sits within two rows of the repo's PDF parse ($775M, 1,327 projects).

**84-2. How should the 7 malformed `t474-a92g` rows be handled?**
Why: they hold shifted fields (`reported = "PARK WEST"`) and Excel `ERROR: #NAME?` values, so
some awards are wrong or split. Suggested answer: pull the full dataset once (11,503 rows), find
the rows, repair them from the RnD workbook or the PDF, list them in `DATA-ANOMALIES.md`, and
tell the Council's Open Data contact.

**84-3. Why does `t474-a92g` report 2026 not equal the July FY26 workbook exactly?**
Why: 1,254 rows and $805,620,000 on Open Data, against 1,252 rows and $807,620,000 across FY26 to
FY29 in the workbook. A $2.0M, two-row gap. Suggested answer: diff the two by `id` once the full
pull is approved. The duplicate `HN CN1451` and the out-year rows are the first places to look.

**84-4. Does the `title` column in `t474-a92g` mean the same thing every year?**
Why: in the FY2019 preview `title` is an organization ("VOLUNTEERS OF AMERICA") and
`description` is the project. In FY2026 `title` is the project ("DUANE PARK UPGRADES"). A tool
that treats `title` as the grantee will be wrong for some years. Suggested answer: profile
`title` by year after the full pull, and read the attached data dictionary.

**84-5. When will the Council add FY2027 to `t474-a92g`?**
Why: until then FY2027 comes only from the RnD workbook, which the Council replaces each year.
Suggested answer: FY2026 appeared on 2025-12-17, about six months after adoption, so expect
about December 2026. Meanwhile keep the RnD workbook as the FY2027 source and archive each pull.

**84-6. Approve full pulls of the build candidates?** (needs Noel)
Why: every analysis beyond the spot checks needs the data local. Sizes: `t474-a92g` 11,503 rows;
`46m8-77gv` 16,491; `2cmn-uidm` 60,739; `fi59-268w` 12,929; `djxg-kcfi` 41,277; `fb86-vt7u`
56,525 (or only rows on Council `D` lines, about 1,400 a period). Each is under the 100,000-row
stop line. Suggested answer: approve `t474-a92g`, `46m8-77gv` and `2cmn-uidm` first (89k rows
together), at 1 request per 2 seconds, after the `4d7f-74pe` pull finishes.

**84-7. Which CPDB release is `fisa_2026`, and does DCP keep earlier versions anywhere?**
Why: Open Data holds one version only, so it cannot show how a project changed. FY2027 Council
items are not in it yet. Suggested answer: read the CPDB data dictionary and DCP's Capital
Planning documentation. If earlier versions exist as downloads, they are the project-level
history source. Do not guess the release from the dates.

**84-8. Can Council discretionary expense money be isolated in OMB's Expense Budget
(`mwzb-yiwb`)?**
Why: if yes, Schedule C has a stage-2 equivalent the way capital does. None of its 26 columns
names a Council initiative, but budget codes or responsibility centers might. Suggested answer:
one small query on a known initiative's agency and budget code, after a decision that it is in
scope.

**84-9. Are Borough President capital datasets in scope for 2.0?** (needs Noel)
Why: Brooklyn (`n6ej-pebd`, 2021), Bronx (`mdgu-ar69`, 2024) and Manhattan (2014–2018) publish
their own capital awards, and the DCLA dataset splits cultural capital into BP, Council and
Mayoral money. Suggested answer: not for 2.0, but record them, because BP money may explain some
of the OMB budget lines that have no Council row (see 87-3).

**84-10. Is the NYC Open Data Terms of Use acceptable for redistributing these datasets inside
the MCP's data store?** (needs Noel)
Why: no dataset I read carries its own license. Suggested answer: the repo already redistributes
Council PDFs and workbooks as public records. Same treatment, with each dataset ID, release date
and pull date recorded in a manifest.

**84-11. Do the Council's participatory budgeting results exist anywhere structured after 2018?**
Why: PB money is Council capital, and both PB datasets stopped in 2017 and 2018. Suggested
answer: check `council.nyc.gov/pb` once, under the Council website's 10-second crawl delay, if
Noel wants PB in scope.

**84-12. Is `4d7f-74pe` really Council-published?**
Why: the catalog's attribution field is blank. Minor, but a citation should name the right
publisher. Suggested answer: read its metadata `Dataset Information` block during the #85 pull.

## #87: capital stage map

**87-1. What accounts for the $25,789,000 between the Council's FY2027 file and OMB's adopted
Capital Budget?**
Why: 7 Council lines differ in amount ($17,152,000) and 8 OMB `D`-series lines have no Council
row ($8,637,000). Until explained, a tool cannot say whether the Council file is complete.
Suggested answer: three hypotheses to test, in order. (a) Changes between adoption (July) and
the October workbook. Check by comparing with the PDF adopted on budget day, which agrees with
the workbook, so this is less likely. (b) Items added on Council lines by the administration or
a Borough President. (c) Items moved between lines; `P D017` −$579,000 and `P D020` +$579,000
suggest one project booked in a different borough. Ask Council Finance if the data cannot settle
it.

**87-2. What do `CD 80` / sponsor "Admin", `CD 99` / "Technical Adjustments", `BORO = A`, and
district codes `91`–`97` mean?**
Why: they are real money on Council lines (the "Admin" row is $371,000 to Ryan Health), and a
tool must attribute it correctly, not to a member. Suggested answer: "Admin" is probably
administration money placed on a Council line, and "99" restores rescinded funding (its
description says so). `91`–`97` are probably delegations and caucuses, since the site names
"Brooklyn Delegation" and "Black, Latino and Asian Caucus". Confirm with the Council RnD team
before publishing any of it.

**87-3. What do the FY2026 `CN` and `NC` prefixes mean, and why did FY2027 switch to `CC`?**
Why: if `NC` marks a non-profit grantee (Part II, non-city), it is a useful filter that FY2027
dropped. Suggested answer: 147 of 148 `DN`-line rows are `NC`, which fits "non-city," but `NC`
also appears on 99 shared-line rows. Check against the FY2026 PDF's Part II list.

**87-4. Is there any official crosswalk from a Council capital project ID to an FMS project ID?**
Why: without one, project-level tracking is a text match. Suggested answer: none on Open Data.
Council Finance or OMB may keep one internally. Worth one question to the Council's data team.
In the meantime, measure how well text matching works (87-5).

**87-5. How well does a budget-line plus title match work across a whole year?**
Why: it worked on all three FY2026 items tried (MBD vans via CPDB, Duane Park via the OPS
dashboard). The dashboard's project name was literally the Council's TITLE and DESC joined with
" - ". Suggested answer: after the CPDB and dashboard pulls, run the match for every FY2026 row.
Report three rates: exact title, fuzzy, and no match, split by `DN` lines and shared lines. This
is a code task for software-engineer.

**87-6. Can the 708 school projects on `E D001` be traced below the line?**
Why: they are $225M of the Council's $854M FY2027 capital, and the budget line cannot separate
them. Suggested answer: the School Construction Authority's datasets (`2xh6-psuq`, `8586-3zfm`)
and the `B:M276 S:M276` building and school codes in the Council's titles may give a key. Not
examined today.

**87-7. Which "spent" figure should a tool report: CPDB `spent_total` or
`spent_total_checkbooknyc`?**
Why: for DCTV's renovation they differ ($1,645,593 vs $1,604,593). Suggested answer: report
both and name the source of each. CPDB's own definitions are in the data dictionary, which I
have not read.

**87-8. Can Checkbook capital spending or contracts be filtered by FMS project ID or budget
code?**
Why: that is what would give check-level payments and contract IDs for a matched project. The
`nyc-checkbook-mcp` `search_spending` tool exposes no such filter. Suggested answer: read the
Checkbook API documentation for capital project fields before any further call (engineering
standards §0), then decide whether the MCP needs a new parameter. This is a software-engineer
task, and it waits on E-1.

**87-9. How should rounding be handled between the commitment plan ($ thousands) and
designations (dollars)?**
Why: a one-row line matches only to $1,000, and several rows on a line can round differently.
Suggested answer: compare in thousands, allow ±$1K per row on the line, and flag anything wider.

**87-10. Should the MCP show slippage, i.e. money moving to later years across commitment plan
releases?**
Why: the data shows it plainly: the MBD vans moved from FY2026 to FY2027, and DCTV's new FY2027
money is planned for FY2030. That is a useful accountability answer. (needs Noel) Suggested
answer: yes, as a 2.0 or 2.1 tool, built on the release history in `2cmn-uidm`.

**87-11. Does the FY2017 Council capital workbook on the Internet Archive (#86) share today's
schema and ID form?**
Why: it is the only lead for capital before FY2019. Suggested answer: open it after #86 caches
it and compare columns with the FY2026 and FY2027 sheets.

**87-12. Is any public dataset the link between a capital project and a registered contract
(Checkbook, PASSPort, the City Record)?**
Why: no Open Data capital dataset carries a contract ID. Suggested answer: check Checkbook's
contract fields (87-8) first, then the City Record MCP for capital procurement notices that name
an FMS project. Do not start before E-1 is settled.

## #88: Council RnD site

**88-1. Does the `Last-Modified` header on the RnD workbooks mean "last changed"?**
Why: the site shows it as the data's "as of" date, but the server sent `Last-Modified` equal to
the request time for the page and bundle. Suggested answer: on the next approved re-pull, record
the header for each workbook and compare it with the hash history in
`NYCB-disclosure/source/expense-funding-disclosure/MANIFEST-HISTORY.csv`.

**88-2. Does the Council keep earlier capital workbooks anywhere?**
Why: the site serves the current year only, and the file is replaced each year. The July FY26
copy exists only because the disclosure repo saved it. Suggested answer: do not guess URLs such
as `Capital-Database-FY26.xlsx`. Ask the Council RnD team, and keep archiving each pull.

**88-3. Should a change to the bundle name (`index-DYh0fcxj.js`) trigger a check?**
Why: the bundle lists every file the site serves. A new hash may mean a new file list.
Suggested answer: yes. A monthly fetch of the page only (one request) compares the bundle name.
Fetch the bundle only when it changes.

**88-4. Should the 2.0 MCP read RnD files directly or only from the repo's archived copies?**
(needs Noel)
Why: the Council overwrites them (FY2025–FY2027 and the capital file changed between July and
October). Suggested answer: archived copies only, with the manifest hash and pull date in every
answer.
