# Draft #110 issue-log comments: FY2019 Schedule C (NOT posted)

**Written:** 2026-10-22 04:45 EDT. One block per problem, in the order found, in the shape #110
asks for. Each is meant to be its own comment on #110 once Noel approves. "PR" means the PR
that adds this folder; "promotion PR" the one that writes `data/fy19/pdf/schedule_c/`.

---

**Problem:** FY2019 had no config.
**Where:** `Fiscal-2019-Schedule-C-Final-Report.pdf`, whole document (357 pages: 99 portrait,
258 landscape; every MediaBox starts at (0, 0))
**Found by:** review (starting point for #110)
**Tried:** FY2020's config with FY2019 names and pages: 5,971 rows; 9 of 27 categories found (18
"has no summary table"); 54 unknown statements; 5 unknown headers.
**Fix:** `config/schedule_c/fy2019.toml`. The same 27 categories as FY2020, from the 20 pt
banners (pp.12–128); sections pp.1–11 front, 12–131 body, 132–162 / 163–307 / 308–357 appendices
A / B / C; summary tables titled "Fiscal 2019 Council … Initiatives" except two (pp.41, 102);
header "CM Purpose of Funds". PR.
**Status:** fixed

---

**Problem:** A "*" column FY2020 does not have.
**Where:** most award tables, e.g. p.13 "EIN | * | Amount", "462971279 | * | 5,000"; p.10 says
what it means ("organizations identified in Schedule C with an asterisk": review not complete)
**Found by:** H4 (unknown header label "*"); H7 (26 unmapped cells, p.94)
**Tried:** a new output column: rejected, it would change the review and award columns the
explorer reads.
**Fix:** header label `star`: a "*" becomes the routine row flag `W.asterisk` (304 rows); any
other text there a critical `H7.star`; a row whose cell runs under the "*" keeps it for the
amount (p.45). In the h-rule table on p.94 (no "*" column) three rows print the "*" in the
Program cell: kept as printed, `W.star_in_cell`, warn review rows. 304 "*" in the text layer's
award tables, 304 rows flagged. PR.
**Status:** fixed, flagged in data (304 rows, routine; 3 review rows)

---

**Problem:** Designation statements worded 14 ways, three laid out beside their label.
**Where:** p.35 the statement as two loose lines beside a "Designation Method:" cell; pp.43, 105
the label loose and centred between the statement's two lines; p.94 "post adoption. The Council
has designated"; p.122 "and the Council has designated"; p.84 "Funding is allocated directly to
the Brooklyn Public Library."; p.59 "… Community Boards and each is designated $42,500."; p.95
"… District Attorneys."; p.107 "will designate to service providers post-budget adoption."; p.129
COMPASS "has distributed its allocations between the Department of Youth and Community
Development and providers, as outlined below:"
**Found by:** structure (unknown statement: 54 boxes)
**Fix:** patterns in config; FY2020's `statement_beside_label`; new `statement_beside_label_span`
(pp.43, 105). PR.
**Status:** fixed

---

**Problem:** Award headers printed outside the drawn grid, or cut by white columns.
**Where:** pp.42, 125 "Legal Name of Organization" / "EIN * Amount" loose above an h-rule table
(the first row then read as an initiative box: "Center for Alternative Sentencing and Employment
Services $828,775", "Legal Momentum $125,000"); p.39 "Amoun" | "t" and "$372,20" | "3" (the
last character in the 8 pt white column at the table's right edge); p.54 an empty band above
Support for Homeless Students' title bar; p.74 "Foreclosure Buyback Initiativ" | "e"
**Found by:** H5 (p.42: 19 EIN-shaped words, 2 rows); H11 (box vs summary)
**Fix:** FY2024's `loose_header`, FY2021's `header_band_words`, `edge_slivers`,
`skip_empty_first_row`, FY2023's `sliver_chars`; header labels "EIN *", "Program *", "Amoun" /
"t"; new `box_title_tail` (p.74). PR.
**Status:** fixed; the 3 p.39 amounts are warn review rows

---

**Problem:** A table of 28 organizations with EINs and amounts under one award that are not awards.
**Where:** pp.105–106, "**Below is a list of the Jobs to Build On service providers partners:"
under Consortium for Worker Education (CWE) – Jobs to Build On** (13-3564313, $5,154,200)
**Found by:** H4 (unknown header "Organization | EIN | Amount | Service Type"); H5 (28 EIN-shaped
words with no row)
**Tried:** reading them as awards (what the old parse did, 27 of 28): they would count CWE's money
twice, and they add to $4,463,500, not $5,154,200.
**Fix:** `side_lists` in config (page and header as printed): read, not counted; one critical
review row per page with the count and sum; its EINs are named `H5.page_words` exceptions. PR.
**Status:** flagged in data (decision for Noel)

---

**Problem:** Six boxes print their post-adoption reserve again as an award row for a City agency.
**Where:** p.37 Adult Literacy (DYCD $185,000, p.38); p.43 Human Trafficking (MOCJ $200,000);
p.72 Community Housing Preservation Strategies (four HPD rows, $179,919, p.73); p.78 Immigrant
Health (DOHMH $50,000); p.82 Legal Services for the Working Poor (DSS $50,000); p.125 Prevent
Sexual Assault (MOCJ $100,000). Each agency row prints the City's EIN 13-6400434.
**Found by:** H12 (rows equal the box, not the box less the reserve)
**Tried:** looking for a parse error: none; each agency row is on the page, and its amount equals
the stated reserve to the dollar.
**Fix:** none. Named exceptions in config; warn review rows.
**Status:** flagged in data

---

**Problem:** The PDF's own numbers disagree in three more places.
**Where:** p.62 Ending the Epidemic rows $150,000 over the box less its reserve, no agency row;
p.49 a box for the whole SAVE initiative over its three parts' boxes; p.59 Community Boards,
"each is designated $42,500" (59 × $42,500 = the box). Roll-up +$914,919 = the six reserves
above + p.62
**Found by:** totals (H12, H13)
**Fix:** none. Named exceptions in config; in the review file.
**Status:** flagged in data

---

**Problem:** Box titles printed differently from their summary lines (15).
**Where:** pp.45, 49, 64, 65, 67, 74, 84 (×3), 88, 89, 95, 97, 100, 127
**Found by:** H11
**Fix:** `box_aliases` in config, each a warn review row. PR.
**Status:** flagged in data

---

**Problem:** DATA-ANOMALIES §20's 39 FY2019 merged rows.
**Where:** the old parse (`data/fy19/schedule_c/fy19_schedule_c_awards.csv` at `26a5ab8`), e.g.
"Haitian Americans United for Progress, Inc. 11-2423857 * $70,000 Indochina Sino-American Senior
Citizen Center, Inc." (p.38). 38 of the 39 lost the row boundary at a "*" between the EIN and
the amount; one (p.94) at a school name in the Program column.
**Found by:** §20 list; `code/validate_data.py` `org_merged` on the first PDF parse
**Fix:** read from the table's cells: the 39 rows are **82 separate awards**, each found in this
parse on (EIN, amount). Row by row: `data/fy19_sc_s20_check.csv`, made by `s20_check.py`. Test
`test_golden19_star_column_p13`.
**Status:** fixed

---

**Problem:** #59: the old parser read no appendix row in FY2019.
**Where:** pp.132–357, amounts with no "$" ("15,000")
**Found by:** #59
**Fix:** FY2020's `bare_amounts`: 4,444 rows, $49,799,000, each appendix equal to its pot. PR.
**Status:** fixed

---

## Proposed DATA-ANOMALIES text

In the README, "Proposed DATA-ANOMALIES entry" (not added to `DATA-ANOMALIES.md`; the integrator
numbers it).
