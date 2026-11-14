# What's changed

This page lists the changes to BetaNYC's New York City Budget site and its AI server, nyc-budget-mcp, that a reader would notice: new pages and tools, new data, data fixes, and corrections when we published something wrong. Newest first. Routine updates are not listed.

- **History begins:** 2026-07-06. Older entries summarize launches and releases. Corrections made before this date may be missing.
- **Data refresh:** Not on a schedule, and there is no nightly refresh. Budget documents and City datasets are added when the City or the Council publishes them.

To report a bug in this server or ask for a new feature, open an issue at https://github.com/BetaNYC/New-York-City-Budget/issues.

## Unreleased: Server adds City agency budgets, FY2027 changes and Council Members by person

- **Tags:** MCP, Data
- **What changed:** The server can now answer questions about every City agency's adopted and modified budget from Fiscal Year 2017 on, with the same figures as the site's agency pages, and it says "not in that year's budget" or "not yet published" instead of showing $0. It can also search the Council's four FY2027 transparency resolutions (changes to the budget after it was adopted), and in the tables read from the Council's budget documents it now treats each Council Member as one person, so you can search by person and similar names or relatives no longer blend together. Another new tool shows when the money on a capital budget line is planned to be committed and how that plan has changed, from the City's budget office and City Planning. Two new tools say what changed in the server and who built it.
- **Who it affects:** People who use the server with an AI assistant.
- **MCP version:** [nyc-budget-mcp 2.1.0](mcp/CHANGELOG.md)
- **More detail:** [Developer notes](mcp/CHANGELOG.md) · [Agency budgets plan](https://github.com/BetaNYC/New-York-City-Budget/issues/270) · [Agency budget data](https://github.com/BetaNYC/New-York-City-Budget/issues/284) · [Agency budget tools](https://github.com/BetaNYC/New-York-City-Budget/issues/285) · [FY2027 transparency resolutions](https://github.com/BetaNYC/New-York-City-Budget/pull/298) · [Council Members as people](https://github.com/BetaNYC/New-York-City-Budget/issues/51) · [Capital commitment plan](https://github.com/BetaNYC/New-York-City-Budget/issues/250)

## 2026-11-13: The explorer now shows every City agency's budget, trend first

- **Tags:** Site, Data
- **What changed:** The explorer has a new view of City agency budgets: each agency's adopted and modified budget from Fiscal Year 2017 on, with a citywide chart that shows the trend first and then one year. The old agency pages are retired, and their links forward to the new view. Every page on the site now passes automated accessibility and phone checks.
- **More detail:** [Questions and answers](https://betanyc.github.io/New-York-City-Budget/agencies/faq.html) · [The new view](https://github.com/BetaNYC/New-York-City-Budget/pull/294) · [Trend first](https://github.com/BetaNYC/New-York-City-Budget/pull/307) · [Old pages retired](https://github.com/BetaNYC/New-York-City-Budget/pull/296) · [Accessibility checks](https://github.com/BetaNYC/New-York-City-Budget/pull/305)

## 2026-11-13: Agency pages showed $0 for units that were not in that year's budget

- **Tags:** Site, Correction
- **What changed:** The old agency pages showed $0 both for a real $0 and for a unit of an agency's budget that was not in that year's budget at all. The new view says "Not in this year's budget" for the second case, so the two can't be mixed up.
- **If you used the old numbers:** The old pages were online from July 10, 2026, first at betanyc.github.io/nyc-budget-viz and then on this site from November 10, until they were retired on November 13, 2026. In the last version of the old pages, as the questions and answers page says, "1,737 amounts it showed as $0 (936 adopted and 801 modified) were units that were not in that year's budget." If you copied a $0 for a unit, look the unit up again in the new view. If you copied it before November 9, 2026, move the year back by one first (see the November 9 entry). If the new view says "Not in this year's budget", the unit did not exist that year, which is different from a $0 budget. In the download, a 0 can mean either a real $0 or a unit that was not in that year's budget. Check the unit in the new view before you report it as $0.
- **Who it affects:** Anyone who used a $0 amount from the agency pages or the download.
- **More detail:** [Questions and answers](https://betanyc.github.io/New-York-City-Budget/agencies/faq.html#q7) · [Data notes](DATA-ANOMALIES.md#57-expense-budget-mwzb-yiwb-a-releases-fiscal_year-is-not-the-year-of-all-its-amounts-2026-11-09-268-nyc-budget-viz34) · [The change](https://github.com/BetaNYC/New-York-City-Budget/pull/294)

## 2026-11-13: Changes the Council made to the FY2027 budget are now searchable

- **Tags:** Site, Data
- **What changed:** The explorer adds the four transparency resolutions the Council adopted after the FY2027 budget, from July 16 to October 22, 2026: 2,808 lines, each labeled "checked, review in progress". The server gets them in its next release.
- **More detail:** [How they were read and checked](DATA-ANOMALIES.md#58-fy2027-transparency-resolutions-read-and-checked-from-the-pdfs-246-102--status-reviewed-public-review-in-progress) · [The change](https://github.com/BetaNYC/New-York-City-Budget/pull/298)

## 2026-11-10: Agency amounts in the Terms and Conditions tables were one year late

- **Tags:** Data, Site, Correction
- **What changed:** Where the Council's Terms and Conditions name a unit of an agency's budget, we show that unit's adopted amount from the City's open data. Each amount was the previous year's figure. They now show the right year: 1,344 of 1,376 amounts changed, and whether each unit was found on NYC Open Data did not change.
- **If you used the old numbers:** These amounts were in this repo's data from October 21, 2026, and on the explorer's Terms and Conditions page from October 23, 2026, until November 10, 2026. If you quoted one from the explorer in that time, look it up again; the old figure is the previous year's adopted budget. The AI server never had these amounts: neither its package nor its optional download of PDF tables included them, so its answers were not affected. The developer notes for version 2.0.6 say to check amounts quoted from the server again; that advice does not apply. Example from the developer notes: "DOE unit 401, FY2017, was $5,844,620,680 (the FY2016 figure) and is now $6,164,926,031."
- **Who it affects:** Anyone who used a Terms and Conditions unit amount from the explorer.
- **More detail:** [Developer notes](mcp/CHANGELOG.md#206--2026-11-10) ([corrected in 2.1.0](mcp/CHANGELOG.md)) · [The report](https://github.com/BetaNYC/New-York-City-Budget/issues/274) · [The fix](https://github.com/BetaNYC/New-York-City-Budget/pull/281) · [Why the City's data is easy to misread](DATA-ANOMALIES.md#57-expense-budget-mwzb-yiwb-a-releases-fiscal_year-is-not-the-year-of-all-its-amounts-2026-11-09-268-nyc-budget-viz34) · [The same mistake on the agency pages](#2026-11-09-agency-budget-years-were-shown-one-year-late)

## 2026-11-10: The agency budget explorer joins this site, with all 59 community boards

- **Tags:** Site, Data
- **What changed:** The City agency budget explorer moved from its own address into this site, with one menu and footer for every page. A new table and download cover the budgets of all 59 community boards. New pages explain BetaNYC and the AI server.
- **More detail:** [The move](https://github.com/BetaNYC/New-York-City-Budget/pull/275) · [Community board budgets](https://github.com/BetaNYC/New-York-City-Budget/pull/279) · [Site look and new pages](https://github.com/BetaNYC/New-York-City-Budget/pull/277)

## 2026-11-09: Agency budget years were shown one year late

- **Tags:** Site, Data, Correction
- **What changed:** Every year in the agency budget explorer was labeled one year late, for every agency. The amount shown as "Adopted 2026" was really the Fiscal Year 2025 adopted budget. The dollar amounts came from the City unchanged; only the year they were filed under was wrong, and it is fixed. A community board staff member's spreadsheet showed the problem.
- **If you used the old numbers:** The explorer and its download had this error from their first version on July 10, 2026, at the explorer's old address, until November 9, 2026. As the questions and answers page says: "If you copied numbers from this explorer before November 9, 2026, move each year back by one: what it called 2026 is Fiscal Year 2025." Example from the report: "Adopted 2026" ($114,384,991,832) is really the FY2025 adopted budget. The real FY2026 adopted total is $117,791,473,676. The same fix also merged agencies and units that had shown up as two rows, and left the newest year's modified budget blank instead of showing it as 0. If a unit's row was blank or 0 for some years, look for a second row with the same name; the new view shows them as one.
- **Who it affects:** Anyone who used the agency budget explorer or its download before November 9, 2026.
- **More detail:** [Questions and answers](https://betanyc.github.io/New-York-City-Budget/agencies/faq.html#correction) · [The report](https://github.com/BetaNYC/nyc-budget-viz/issues/3) · [The fix](https://github.com/BetaNYC/nyc-budget-viz/pull/4) · [Why the City's data is easy to misread](DATA-ANOMALIES.md#57-expense-budget-mwzb-yiwb-a-releases-fiscal_year-is-not-the-year-of-all-its-amounts-2026-11-09-268-nyc-budget-viz34)

## 2026-10-25: Short search words matched inside longer words

- **Tags:** MCP, Correction
- **What changed:** A search for a short word, like "AI", also matched it inside longer words, such as "Jamaica" and "AIDS", and the totals counted those rows. Now a word of three or fewer letters and digits matches only as a whole word. Longer words still match anywhere in a name, and searches by tax ID or other ID numbers are unchanged.
- **If you used the old numbers:** If you searched by a short name or word before version 2.0.4 (released October 25, 2026), run the search again; the old answer and its total may include rows you did not want. Every version from 1.0.0 (July 8, 2026) matched this way. Example from the developer notes: a search of Schedule C awards for tax ID 13-2612524 and the name "AI" returned 34 rows; that search now returns the one row, $20,000.
- **Who it affects:** People who searched the server by a short word.
- **MCP version:** [nyc-budget-mcp 2.0.4](mcp/CHANGELOG.md#204--2026-10-25)
- **More detail:** [Developer notes](mcp/CHANGELOG.md#204--2026-10-25) · [The report](https://github.com/BetaNYC/New-York-City-Budget/issues/259) · [The fix](https://github.com/BetaNYC/New-York-City-Budget/pull/260)

## 2026-10-24: Better matching to NYC Open Data, and better checks on the PDF tables

- **Tags:** MCP, Data
- **What changed:** 13 more capital rows now match their record on NYC Open Data, because the match now uses the agency's code as well as the project number. A new edition of the optional download of checked tables confirms about 6,100 more rows with a second check; no amount, tax ID or name changed.
- **MCP version:** [nyc-budget-mcp 2.0.3](mcp/CHANGELOG.md#203--2026-10-24)
- **More detail:** [Developer notes](mcp/CHANGELOG.md#203--2026-10-24) · [Capital matching](https://github.com/BetaNYC/New-York-City-Budget/pull/254) · [Checks](https://github.com/BetaNYC/New-York-City-Budget/pull/252)

## 2026-10-23: Server and explorer serve the tables checked from the Council's PDFs

- **Tags:** MCP, Data, Site
- **What changed:** Four new server tools search the tables read and checked from the Council's budget documents: Schedule C awards, transparency resolutions, the capital book, and Terms and Conditions, for FY2018 to FY2027 depending on the document. Every row says whether its review is still in progress, and the tables are an optional download. The explorer has a searchable page for each.
- **Who it affects:** People who use the server with an AI assistant, and explorer users.
- **MCP version:** [nyc-budget-mcp 2.0.2](mcp/CHANGELOG.md#202--2026-10-23)
- **More detail:** [Developer notes](mcp/CHANGELOG.md#202--2026-10-23) · [What is served, and how it is labeled](DATA-ANOMALIES.md#56-checked-pdf-tables-served-again-labeled-mcp-202-2026-10-23-epic-190) · [Server tools](https://github.com/BetaNYC/New-York-City-Budget/pull/226) · [Explorer pages](https://github.com/BetaNYC/New-York-City-Budget/pull/224)

## 2026-10-21: A new explorer to search the Council's funding data in your browser

- **Tags:** Site
- **What changed:** The site has a new explorer that searches the same Council funding data as the AI server, right in your browser. It also shows whether each record is on NYC Open Data.
- **More detail:** [The explorer](https://github.com/BetaNYC/New-York-City-Budget/pull/123) · [Open Data badges](https://github.com/BetaNYC/New-York-City-Budget/pull/138)

## 2026-10-20: Our notes said some years had no records, but the City printed them

- **Tags:** Data, Correction
- **What changed:** A new read of the Council's budget documents found that our notes described gaps in our own reading as gaps in what the City printed. The notes are corrected, each with a dated line. No data changed.
- **If you used the old numbers:** Our notes said this about FY2009 to FY2014 from July 8, 2026, and about FY2018 capital from October 17, 2026, until October 20, 2026. Versions 1.0.0 to 1.3.1 of the server said the same about FY2009 to FY2014 in their coverage notes, until version 2.0.0 on October 17, 2026. If you wrote, from our notes or the server, that the City printed no award-level records for FY2009 to FY2014, or no FY2018 capital detail, that is wrong. The City printed them; we had not extracted them. Example from the notes: earlier text said FY2009–FY2014 have "no per-organization award rows and no EINs"; the PDFs show award rows with EINs in every one of those years.
- **More detail:** [The correction](https://github.com/BetaNYC/New-York-City-Budget/pull/100) · [FY2018 capital](DATA-ANOMALIES.md#26-council-capital-from-structured-sources-github-89-a6-a7-b8b10)

## 2026-10-17: Server version 2 uses the Council spreadsheets, not text read from PDFs

- **Tags:** MCP, Data, Site
- **What changed:** The server was rebuilt on the Council's own spreadsheets and capital lists, with NYC Open Data and a comparison to the City's adopted capital budget. Everything read from the budget PDFs by the old method was retired, with six tools and the site's first explorer, which was frozen and marked not to be cited. Figures from version 1 will not match version 2, because the sources are different.
- **Who it affects:** Anyone who used version 1 of the server or the site's first explorer.
- **MCP version:** [nyc-budget-mcp 2.0.0](mcp/CHANGELOG.md#200--2026-10-17)
- **More detail:** [Developer notes](mcp/CHANGELOG.md#200--2026-10-17) · [What was retired](DATA-ANOMALIES.md#27-pdf-derived-data-retired-in-20-2026-10-14) · [The change](https://github.com/BetaNYC/New-York-City-Budget/pull/95)

## 2026-08-13: Award answers had wrong grantee names and left out 28,575 appendix awards

- **Tags:** Data, Correction
- **What changed:** In the award tables read from the Council's budget PDFs, 5,450 cells had been read wrong, for example text about what the money was for sitting where the grantee's name belongs. They were repaired from the Council's own spreadsheets. No dollar amount changed. Awards printed in the documents' appendices, 28,575 rows, had been left out of every server answer; the fix to add them was never released, because version 2 retired these tables on October 17, 2026.
- **If you used the old numbers:** From version 1.0.0 on July 8, 2026, until version 2.0.0 on October 17, 2026, the server's award answers left out appendix awards, showed some wrong grantee names, put a borough or a word from the organization's name where the Council Member belongs on 673 awards and gave 20 the wrong tax ID, so a total or a "no awards" answer may be too low. Example from the developer notes: Bard College had three FY2023 designations, "Abreu $5,000, Brooks-Powers $10,000, Powers $5,000, $20,000 across three members", but the server answered "No Schedule C awards for EIN 14-1713034". Check such a figure against the Council's expense funding disclosure, which the server's search_disclosure_awards tool and the explorer's award search serve.
- **More detail:** [Data notes](DATA-ANOMALIES.md#21-schedule-c-awards--the-extraction-defects-repaired-2026-08-1213-and-what-remains--partially-resolved) · [Developer notes for the unreleased versions](mcp/CHANGELOG.md#150--2026-10-12-never-released-folded-into-200) · [Appendix awards](https://github.com/BetaNYC/New-York-City-Budget/pull/55) · [The repair](https://github.com/BetaNYC/New-York-City-Budget/pull/56)

## 2026-08-12: We said award amounts were exact, but 303 rows mixed up two awards

- **Tags:** Data, Correction
- **What changed:** Our notes said that even where an award row's organization name was garbled, its tax ID and amount were exact. For 303 rows (276 in the yearly award tables and 27 in the appendices) that was false. One row named one organization but carried another's amount. The notes are corrected and those rows are now flagged.
- **If you used the old numbers:** Our notes said this from the first release on July 6, 2026, until August 12, 2026. If you used an award amount for a named organization from these files or, for the 276 rows in the yearly tables, from version 1 of the server, FY2016 to FY2020 or FY2024 to FY2026, check the amount against the Council's expense funding disclosure, which version 2 of the server and the explorer serve. FY2018 has the most, 121 rows (94 in the yearly table and 27 in an appendix), and FY2017 has 118. Example from the data notes: a FY2017 row with amount $2,076,666 and organization "Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services". That one row carries two organizations' names, tax IDs and amounts.
- **More detail:** [Data notes](DATA-ANOMALIES.md#20-schedule-c-awards--lost-row-boundaries-put-another-organizations-amount-on-a-named-row--open) · [The correction](https://github.com/BetaNYC/New-York-City-Budget/pull/54)

## 2026-08-11: Award searches with a limit could hide the largest awards

- **Tags:** MCP, Correction
- **What changed:** When an award search matched more awards than it returns (50 unless you asked for fewer), the server cut the list by sponsor name instead of keeping the largest awards. It now orders by amount, largest first, before it shortens the list. A community contributor sent the fix.
- **If you used the old numbers:** From version 1.0.0 on July 8, 2026, until version 1.3.1 on August 11, 2026 (the developer notes date it July 22; it was published August 11). If you used a list of awards from an earlier version, it may have left out the largest ones, and its total covered only the awards it listed. That tool was removed in version 2.0.0, so check the organization's full list in the Council's expense funding disclosure instead. Example from the developer notes: the search for "Association of Community Employment" in fiscal year 2026 with a limit of 4 returned $67,000, $15,000, $40,000, and $250,000, omitting awards of $280,000, $280,000, and $260,000.
- **MCP version:** [nyc-budget-mcp 1.3.1](mcp/CHANGELOG.md#131--2026-07-22)
- **More detail:** [Developer notes](mcp/CHANGELOG.md#131--2026-07-22) · [The report](https://github.com/BetaNYC/New-York-City-Budget/issues/39) · [The fix](https://github.com/BetaNYC/New-York-City-Budget/pull/41)

## 2026-07-21: Unknown search options were dropped, so answers were not filtered

- **Tags:** MCP, Correction
- **What changed:** If you or your AI assistant asked a tool for something it had no option for, such as a Council district, the server ignored that part without saying so and answered for the whole city. Now it refuses, and lists the options the tool accepts.
- **If you used the old numbers:** From version 1.0.0 on July 8, 2026, until version 1.3.0 on July 21, 2026, an answer to a question with an option the tool did not have was not filtered by it. The record does not list which questions were affected. Example from the developer notes: a request for Council District 10's FY2026 awards (limit 15) returned $47,500,647 of awards from across the city. Those tools were removed in version 2.0.0. Check a district's or Council Member's figure against the Council's expense funding disclosure, which version 2 serves.
- **MCP version:** [nyc-budget-mcp 1.3.0](mcp/CHANGELOG.md#130--2026-07-21)
- **More detail:** [Developer notes](mcp/CHANGELOG.md#130--2026-07-21) · [The report](https://github.com/BetaNYC/New-York-City-Budget/issues/37) · [The fix](https://github.com/BetaNYC/New-York-City-Budget/pull/40)

## 2026-07-16: Links to Council records on Legistar did not work

- **Tags:** MCP, Correction
- **What changed:** The server's link to each budget resolution on Legistar, the Council's legislation site, opened a page that said "Invalid parameters!". Version 1.2.0 linked to the Council meeting where the item was adopted, and gave no link where it could not confirm one.
- **If you used the old numbers:** From version 1.0.0 on July 8, 2026, until version 1.2.0 on July 16, 2026, the link was broken for every row. Find the item on Legistar by its number and adoption date instead. Example from the developer notes: the link opened a Legistar page that said "Invalid parameters!". The tool was removed in version 2.0.0. For a resolution's Legistar record now, use the NYC Council MCP.
- **MCP version:** [nyc-budget-mcp 1.2.0](mcp/CHANGELOG.md#120--2026-07-16)
- **More detail:** [Developer notes](mcp/CHANGELOG.md#120--2026-07-16) · [The report](https://github.com/BetaNYC/New-York-City-Budget/issues/31) · [The fix](https://github.com/BetaNYC/New-York-City-Budget/pull/32)

## 2026-07-15: FY2025 capital projects now compare with other years

- **Tags:** MCP, Data
- **What changed:** FY2025 capital projects now come from the Council's supporting detail book, read the same way as FY2026 and FY2027 and checked against its printed totals, so FY2025 can be compared with those years. Each project now shows its borough and sponsor.
- **MCP version:** [nyc-budget-mcp 1.1.0](mcp/CHANGELOG.md#110--2026-07-15)
- **More detail:** [Developer notes](mcp/CHANGELOG.md#110--2026-07-15) · [The change](https://github.com/BetaNYC/New-York-City-Budget/pull/22)

## 2026-07-10: A chart of Council discretionary funding goes online

- **Tags:** Site
- **What changed:** The site's first page charts the Council's discretionary funding (Schedule C) for FY2015 to FY2027, by category and by the agency that runs each program.
- **More detail:** [The chart](https://github.com/BetaNYC/New-York-City-Budget/pull/14) · [Automatic publishing](https://github.com/BetaNYC/New-York-City-Budget/pull/17)

## 2026-07-08: The AI server is published for anyone to use

- **Tags:** MCP
- **What changed:** The server is published so anyone can connect it to an AI assistant and ask about the Council's budget documents: Schedule C awards, transparency resolutions, capital projects and Terms and Conditions, with the years each one covers.
- **MCP version:** [nyc-budget-mcp 1.0.0](mcp/CHANGELOG.md#100--2026-07-08)
- **More detail:** [Developer notes](mcp/CHANGELOG.md#100--2026-07-08) · [The release](https://github.com/BetaNYC/New-York-City-Budget/pull/9)

## 2026-07-08: Dropped award rows and a wrong organization name, fixed on launch day

- **Tags:** Data, MCP, Correction
- **What changed:** Before the server's first release, fixes to how the budget PDFs were read recovered award rows that had been dropped and removed a stray word, "Delegation", from the front of organization names. One tool description still used the wrong name for the Fund for the City of New York, and version 1.0.1 fixed it the same day.
- **If you used the old numbers:** The award files in this repo had these errors from the first release on July 6, 2026, until the fixes on July 8, 2026; the wrong name was in the server's description for a few hours on July 8. Example from the data notes: one dropped row understated the Fund for the City of New York (FCNY)'s FY2027 Schedule C passthrough by exactly $125,000 (36 rows and $3,232,714 instead of the true 37 rows and $3,357,714). These files were later retired; see the entry for October 17, 2026.
- **MCP version:** [nyc-budget-mcp 1.0.1](mcp/CHANGELOG.md#101--2026-07-08)
- **More detail:** [Developer notes](mcp/CHANGELOG.md#101--2026-07-08) · [Dropped rows](https://github.com/BetaNYC/New-York-City-Budget/pull/8) · [Stray word](https://github.com/BetaNYC/New-York-City-Budget/pull/10) · [Description fix](https://github.com/BetaNYC/New-York-City-Budget/pull/12)

## 2026-07-07: The Council's budget documents from FY2008 to FY2027

- **Tags:** Data
- **What changed:** The repo now holds the Council's budget documents from FY2008 to FY2027 and spreadsheets read from them: Schedule C awards, transparency resolutions, capital projects and Terms and Conditions. A list links documents to their records on Legistar.
- **More detail:** [The change](https://github.com/BetaNYC/New-York-City-Budget/pull/2) · [Backfill and checks](https://github.com/BetaNYC/New-York-City-Budget/pull/3)

## 2026-07-06: First release of the Council's budget as spreadsheets

- **Tags:** Data
- **What changed:** The first release of this repo turned the Council's FY2025 to FY2027 budget documents into spreadsheets anyone can use.
- **More detail:** [First commit](https://github.com/BetaNYC/New-York-City-Budget/commit/0dc772c416daf91543a1f3aab353f52e52c74294)
