# FY2018 Schedule C: what a person needs to check

**Report generated:** 2026-10-22 05:45 EDT. Source: `data/fy18_sc_review.csv` (117 rows),
sorted by how much money each could touch. Write each decision into
`data/fy18_sc_review_decisions.csv` by `review_id` (`source_error`, `parser_bug`,
`accepted_as_printed` or `needs_info`), columns `review_id,decision,note,decided_by,decided_at`.
"Suggest" is the conservative call; the decision is Noel's. Most rows (50 fiscal conduits, 24
name aliases) are quick: they record what the PDF prints.

## The 2 critical rows

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 1 | `2b4a8d4794a3` | 106 | 4,463,500 | **A list under an award, read as no award.** "Below is a list of the JtBO service provider partners:" under Consortium for Worker Education – Jobs to Build On** (13-3564313, $5,154,200, p.105): 28 rows (South Bronx Overall Economic Development Corp $203,000, …), $4,463,500. p.105's scope says CWE "will use $4.46 million … on service provider partners … The remaining $690,700 will be used by CWE to provide oversight". Counting them would count CWE's money twice. The old parse had 27 as awards. Same list as FY2019. | `accepted_as_printed` (not awards) |
| 2 | `d6d4b086b31f` | 55 | 207,000 | **An EIN that is another organization's.** Dropout Prevention and Intervention: Good Shepherd Services, $207,000, prints 46-1227433, New York City Community Learning Schools' EIN (the disclosure's Community Schools row); Good Shepherd Services, Inc. prints 13-5598710 elsewhere (e.g. p.94). Kept as printed; `main` took 13-5598710. | `source_error` (`needs_info` if the right EIN matters) |

## The PDF disagrees with itself, or a box stands over its parts (16)

All named exceptions in the config; none corrected.

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 3 | `d992ed9ac544` | 93 | 11,340,534 | **Crisis Management System**: a box for the whole, $11,340,534, over its eight parts' boxes (pp.94–97), which hold the rows and add to $11,327,800, the summary line. The whole box prints $12,734 more than its parts. | `source_error` |
| 4 | `a07c5d547fc2` | — | 2,754,028 | The roll-up: exactly #6, #7, #9–#16, and the two summary differences (Community Development $100,000, Merit-Based Scholarships $75,331). | follows |
| 5 | `e0c7eb890ec1` | 101 | 2,429,000 | **A reserve printed again as a row.** NORCs: "$1.9 million" and "$529,000" held post-adoption; its rows include Department for the Aging, 13-6400434, $2,429,000, so they add to the box ($3,850,000). | `accepted_as_printed` (the agency row is the reserve, printed) |
| 6 | `8838df796532` | 53 | 1,950,000 | **SAVE**: a box for the whole ($1,950,000) over its three parts ($600,000, $350,000, $1,000,000). | `accepted_as_printed` |
| 7 | `dbb4602def0c` | 36 | 481,197 | Same as #5: Discretionary Child Care, Administration for Children's Services, The, 13-6400434, $481,197. | `accepted_as_printed` |
| 8 | `05f146d17855` | 124 | 146,000 | **COMPASS**: "has designated the Department of Youth and Community Development and the providers listed below"; the 7 providers add to $1,667,600; DYCD's $146,000 has no row (FY2019 prints it as a row). | `accepted_as_printed` (or `needs_info`) |
| 9 | `16d351e3fdfc` | 38 | 100,000 | **Community Development's TOTAL** prints $14,460,000; its five lines add to $14,360,000. | `source_error` |
| 10 | `aca387be4c4b` | 80 | 60,000 | **Immigrant Opportunities Initiative**: $2,600,000 less "$132,000" = $2,468,000; the 29 rows (p.81) add to $2,408,000. | `source_error` |
| 11 | `1601e65f92e3` | 85 | 55,000 | **Autism Awareness**: box $3,236,846; the 38 rows add to $3,291,846. | `source_error` |
| 12 | `86e6ca807611` | 86 | 55,000 | Same: the table's own TOTAL row prints $3,236,846 under rows that add to $3,291,846. | `source_error` |
| 13 | `cf5fc90c6f94` | 95 | 40,000 | **School Based Conflict Mediation**: box $1,280,000; the 17 rows (p.96) add to $1,320,000. Street Corner Resources is printed twice, $40,000 each ("Street Corner Resources, Inc." and "Street Corner Resources"). | `source_error` (the duplicate row?) |
| 14 | `e9c3dcdfb617` | 127 | 20,000 | **Initiative for Immigrant Survivors of Domestic Violence**: box $250,000; the 6 rows add to $230,000. | `source_error` |
| 15 | `b6b58e3516cf` | 57 | 500 | **Support for Educators**: box $20,804,500; rows $20,804,000. The scope names $250,000 + $20,104,500 = $20,354,500 for DOE; the DOE row prints $20,354,000. | `source_error` |
| 16 | `14c64dae5d77` | 69 | 0 | **Merit-Based Scholarships**: the summary line prints $14,924,669, the box $15,000,000 (an alias with the amounts named). | `source_error` |
| 17 | `dc693f006c1a` | 93 | 0 | The Crisis Management System alias: one summary line ($11,327,800) for the whole box and its eight parts (see #3). | `accepted_as_printed` |
| 18 | `b1d75b563fe7` | 53 | 0 | The SAVE alias (see #6). | `accepted_as_printed` |

## Values the parse read in a way a person should confirm (28)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 19 | 11 rows `W.box_title_above` | 53, 94–97 | 250,000–4,775,000 | **A box's title bar printed above its table**: SAVE's three parts; Crisis Management System's eight (e.g. "Crisis Management System – Cure Violence" $4,775,000 over a table that starts at "Agency:"). Read as the box. Each part's rows equal its box except School Based Conflict Mediation (#13). | `accepted_as_printed` |
| 20 | `e9c19a33944f` | 107 | 88,855 | **Urban Health Plan, Inc.** prints "15-24042810" (10 digits), $88,855, in MWBE Leadership Associations, a row between two ruled tables (DATA-ANOMALIES §20's row). Clean EIN blank. With it the rows make the box ($600,000). | `source_error` |
| 21 | 9 rows `W.star_in_cell` | 92, 93, 127 | 0 | A "*" printed in a cell with no "*" column: 8 at the end of the School cell in Art as a Catalyst for Change ("Public School 284K *"), kept there as printed; 1 in a cell of its own (p.127, Community Healthcare Network, $63,000). Each row carries `W.asterisk`. | `accepted_as_printed` |
| 22 | `1d1f48236143` and 5 more | 16, 177, 300, 301, 331, 332 | 0 | The text layer glues an EIN to the name before it ("Ltd.112507910"); the vector cell reads it apart. | `accepted_as_printed` |
| 23 | `428ef099881f` | 106 | 0 | The partner list's 28 EINs (see #1). | `accepted_as_printed` |

## Fiscal conduits (50, no money)

`W.fiscal_conduit`: the row prints a "Fiscal Conduit" and "FC EIN" (Boroughwide Needs pp.34–35,
and the appendices). Each review row's `what_to_check` holds both as printed; no awards column
does. Suggest `accepted_as_printed` for all but two:

| review_id | Page | What | Suggest |
|---|---:|---|---|
| `f0d35523ca12` | 271 | The conduit column prints **"Please indicate the actuals schools."**, no FC EIN: a drafting note left in the PDF, not a conduit. | `source_error` |
| `1361ec218029` | 242 | Kingsbridge Heights Community Center, FC EIN printed **"13-281380"** (8 digits). | `source_error` |

The others: Jewish Community Center of Staten Island, Inc. (135562256) ×17, Bergen Basin
Community Development Corporation d/b/a Millennium Development (113199040) ×14, Greater
Ridgewood Youth Council, Inc. (112518141) ×6, United Activities Unlimited, Inc. (132921483) ×4,
Maspeth Town Hall, Inc. ×2, and one each of JCC of Greater Coney Island, Fund for the City of New
York, Flatbush Development Corporation, Citizens Committee for New York City.

## Names that differ between a box and its summary line (21 more, no money)

Rows carry the **box** title. Suggest `accepted_as_printed` for all: "Initiative" dropped or
added (pp.39, 55, 99, 125), "PS" for "Personal Services" (p.62 ×2), "Access Health" / "…NYC"
(p.63), "Faith Based" / "Faith-Based" (p.66), "Maternal Health Services" / "Maternal and Child
Health Services" (p.66), "&" / "and" (pp.67, 88), "Murphy Institute" / "Joseph S. Murphy
Institute" (p.70), "NYC Renters" / "NYC's Renters" (p.76), "(SHIP)" (p.76), "(LIFT)" / "Today"
(p.84), "Coalition Theaters" / "Coalition of Theaters" (p.44), "Support For The Arts" (p.51),
"Services Enhancement" / "Enhancements" (p.102), "Enhancement" (p.102), "Transgender Healthcare"
/ "Transgender Specific Healthcare" (p.127), straight / curly apostrophe (p.129). Each is an
`H11.box_alias` row with both names.

## Not in the review file, on purpose

- **1,504 rows with a "*"** (`W.asterisk`). Every "*" in the award tables is on a row.
- **537 Appendix A amounts printed with cents** (`W.amount_cents`, "$30,000.00") and **4,512
  amounts printed with no "$"** (`W.amount_bare`): the year's layout.
- **646 rows checked by pixel rules only**, all in the body.
  *Update 2026-10-24 (#193):* 645 of these rows now have `lattice` = `vector+columns`
  (`image_check` `columns_agree`): the image side finds their columns from the header's labels and
  the blank strips between them, and the text layer, clipped a second time through those cells,
  gives the same value in every field. The other one, p.107 Urban Health Plan (EIN printed
  `15-24042810`), keeps `vector+bands`; see README. It is the same text layer, so a text-layer
  error still passes.
- **14 TOTAL rows inside award tables**: not awards; 13 equal their rows (the 14th is #12).
- **The "School" column of Art as a Catalyst for Change** (pp.92–93), in `purpose`, as FY2019's
  "Program".
- **Bellevue Hospital printed with the City's EIN 13-6400434** (p.68, $120,000), and
  **Convent Avenue Baptist Church – Hamilton Grange Senior Center printed $12,000.00** (p.136):
  read as printed; `main` took the disclosure's values.
- **Money with no rows, by design.** $132,416,318 held post-adoption; $47,133,205 designated
  straight to an agency.
- **Disclosure gaps.** 199 PDF rows ($41,175,405) have no disclosure row: 99 amount differs, 63
  EIN not in the disclosure, 19 key already used, 9 EIN used up, 8 City-EIN name mismatch, 1
  unreadable EIN. Every row and reason: `data/fy18_sc_disclosure_match.csv`.
