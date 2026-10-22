# FY2020 Schedule C: what a person needs to check

**Report generated:** 2026-10-22 02:25 EDT. Source: `data/fy20_sc_review.csv` (42 rows),
sorted by how much money each could touch. Write each decision into
`data/fy20_sc_review_decisions.csv` by `review_id` (`source_error`, `parser_bug`,
`accepted_as_printed` or `needs_info`), columns `review_id,decision,note,decided_by,decided_at`.
"Suggest" is the conservative call; the decision is Noel's.

## The 10 critical rows

| # | review_id | Page | $ | What | What we did / suggest |
|---:|---|---:|---:|---|---|
| 1 | `92fbbde31b93` | 82 | 3,000,000 | **An empty band joined to a row.** New York City Community Learning Schools, 46-1227433, $3,000,000: the empty spacer band under it, before Educational Programs for Students' black bar, is part of its row (looked at). | Crop `data/overlays/p082-1.png`. Suggest `accepted_as_printed`. |
| 2 | `34b7b3b66e0e` | 46 | 1,278,000 | **Three EINs printed one row off.** Initiative to Combat Sexual Assault: New York Foundling Hospital $210,000 prints 11-3431280; North Brooklyn Coalition Against Family Violence $320,000 prints 13-2946970 (Safe Horizon's EIN on p.78); Safe Horizon $748,000 prints 13-3540337 (the Violence Intervention Program's, next row). Kept as printed; none of the three matches the disclosure on (EIN, amount); `main` took the disclosure's. | Suggest `source_error` (and `needs_info` if the right EINs matter: ask Council Finance). |
| 3 | `238e95259eb5` | 42 | 155,000 | Same as #1: Queens Community House, Inc., $155,000 (LGBT Community Services), the last row before Trans Equity Programs' box. | Crop `p042-0.png`. Suggest `accepted_as_printed`. |
| 4 | `e6c33610f6fe` | 187 | 128,000 | **A row cut from the band it shares with the header.** STARS: "Legal Name of Organization \| EIN \| Amount" and Armory Foundation, The, 13-3680286, $128,000 are printed in one band with no rule between; the parse cut it between the lines (`hrule_header_split`). The image sees no rule there. | Crop `p187-0.png`. Suggest `accepted_as_printed`. |
| 5 | `959458291e1b` | 84 | 100,000 | **Rows printed with no rule between them, cut apart** (`hrule_split_lines`): History UnErased, Inc., 47-2852025, $100,000, printed in one band with Fund for the City of New York's $25,000 row (looked at: two awards). | Crop `p084-1.png`. Suggest `accepted_as_printed`. |
| 6 | `e57ebd4622c1` | 102 | 45,000 | Same as #4: BOOM!Health $45,000, under BOOM!Health $9,000 in one band (two awards, same EIN). | Crop `p102-1.png`. Suggest `accepted_as_printed`. |
| 7 | `1226a33c1f26` | 82 | 30,000 | Same as #1. | Crop `p082-0.png`. Suggest `accepted_as_printed`. |
| 8 | `f5647df37e55` | 113 | 29,730 | Same as #1: Woodside on the Move, Inc., $29,730, before Community Land Trust's bar. | Crop `p113-0.png`. Suggest `accepted_as_printed`. |
| 9 | `a0caf5c840ff` | 84 | 25,000 | Same as #5: Fund for the City of New York, Inc. - NYC LGBT Historic Sites, 13-2612524, $25,000 (looked at). | Crop `p084-0.png`. Suggest `accepted_as_printed`. |
| 10 | `f2ed1ec88307` | 102 | 9,000 | Same as #6: BOOM!Health $9,000. | Crop `p102-0.png`. Suggest `accepted_as_printed`. |

## The PDF disagrees with itself or rounds (9)

All named exceptions in the config; none corrected.

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 11 | `fc3a84ffde68` | 79 | 2,450,000 | **A box for the whole SAVE initiative**, $2,450,000, printed over its three parts' boxes ($600,000, $850,000, $1,000,000, whose rows are under them). It has no rows of its own; the summary line counts $2,450,000 once. | `accepted_as_printed` |
| 12 | `708260ba1193` | — | 219,300 | The roll-up: exactly #13–#19 (−$200,000 + $2,000 + $17,500 + $30,000 + $18,200 − $88,000 + $1,000). | `source_error`, follows |
| 13 | `0f735cee73ef` | 46 | 200,000 | **Innovative Criminal Justice Programs.** Box $3,038,000; its 7 rows add to $2,838,000. The scope text names "$200,000 will support Carnegie Hall's NeON Arts program", which has no row. | `source_error` (or `needs_info`) |
| 14 | `f07784d053e1` | 47 | 88,000 | Supports for Persons Involved in the Sex Trade: "$2.9 million post-adoption" for a $2,988,000 box, no rows. Rounding. | `accepted_as_printed` |
| 15 | `219baa5b4ca4` | 86 | 30,000 | A Greener NYC: "$1.4 million" post-adoption; the rows leave $1,370,000. Rounding. | `accepted_as_printed` |
| 16 | `fc95b192e3b8` | 89 | 18,200 | NYC Cleanup: "$4.8 million"; the rows leave $4,781,800. Rounding. | `accepted_as_printed` |
| 17 | `01044b295513` | 78 | 17,500 | DoVE: "$7.8 million"; the rows leave $7,782,500. Rounding. | `accepted_as_printed` |
| 18 | `8bc69f4b7bd9` | 45 | 2,000 | **Initiative to Combat Sexual Assault.** Box $3,210,000 less $40,000 = $3,170,000; the 14 rows add to $3,172,000. | `source_error` |
| 19 | `4247765d55cf` | 94 | 1,000 | Food Pantries: "$4.66 million" + "$1 million" = $5,660,000 for a $5,659,000 box. Rounding. | `accepted_as_printed` |

## Values the parse read in a way a person should confirm (3)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 20 | `5a427f5f5b2c` | 145 | 3,383,670 | Senior Centers, Programs, and Enhancements: the text layer holds "$3,383,670$3,383,670"; the page shows it once (looked at). Read once; the Senior Services TOTAL then ties. | `accepted_as_printed` |
| 21 | `44179bb6cd74` | 97 | 0 | The "Health Services" banner is printed twice over itself (text "Health Services\nHealth Services"). Read as the category. | `accepted_as_printed` |
| 22 | `3d574dab5713` | 111 | 0 | The "Housing" banner is a table with empty bands above and below it. Read as the category. | `accepted_as_printed` |

## EINs (4)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 23 | `20e31f29b5c1` | 134 | 100,000 | SAFE Foundation, Inc. printed "26-102131" (8 digits). Clean EIN blank. | `source_error` |
| 24 | `d96a8a1e6abd` | 162 | 88,855 | Urban Health Plan, Inc. printed "15-24042810" (10 digits). This is DATA-ANOMALIES §20's FY2020 row: it now stands alone, NYC MWBE Alliance's $20,000 is its own row. | `source_error` |
| 25 | `8aaef96fc9fe` | 134 | 50,000 | Amudim Community Resources, Inc. printed "47-984801"; p.360 prints 470984801. | `source_error` |
| 26 | `8420de5f633f` | 306 | 0 | p.306 has 18 EIN-shaped words but 19 rows with an EIN: the text layer glues New York Botanical Garden's 131693134 to the name before it ("Students131693134"). The cell reads it apart. | `accepted_as_printed` |

## Names that differ between a box and its summary line (16, no money)

Rows carry the **box** title. Suggest `accepted_as_printed` for all.

| review_id | Page | Summary line says | Box says |
|---|---:|---|---|
| `0790d884345e` | 41 | Diversity, Inclusion and Equity in Tech **Initiative** | drops "Initiative" |
| `1c2540cc450b` | 44 | Alternatives to Incarceration **(ATI)** | **(ATIs)** |
| `aa73b85d05d0` | 79 | SAVE $2,450,000 | a box of the whole and three part boxes (see #11) |
| `de3560c8559b` | 102 | HIV/AIDS Faith Based | HIV/AIDS Faith**-**Based |
| `87d752d177fb` | 106 | CUNY Child Care Expansion | CUNY Childcare Expansion |
| `f19b484af63e` | 106 | Creative Arts Team **(CUNY CAT)** | Creative Arts Team |
| `a22a488ac371` | 113 | Financial Empowerment for NYC Renters | …NYC**'s** Renters |
| `1e575428168d` | 126 | Fiscal 2020 Subsidy (Research) | …: Research Library |
| `5c865c3acb16` | 126 | Fiscal 2020 Subsidy (BPL) | …: Brooklyn Public Library |
| `399970025733` | 127 | Fiscal 2020 Subsidy (NYPL) | …: New York Public Library |
| `ddb57fe39751` | 127 | Fiscal 2020 Subsidy (QBPL) | …: Queens Borough Public Library |
| `8d83d6aaf798` | 131 | Developmental, Psychological **&** Behavioral Health Services | …**and**… |
| `3f354e1f1c6a` | 141 | Art a Catalyst for Change | Art **as** a Catalyst for Change |
| `c7287e9afd4a` | 147 | Elie Wiesel Holocaust Survivors **Initiative** | drops "Initiative" |
| `94067cb11584` | 184 | Young Women**'**s Leadership Development | Young Women**’**s … (curly apostrophe) |
| `22ed91724fcb` | 187 | Sports Training and Rolemodels for Success Initiative | adds **(STARS)** |

## Not in the review file, on purpose

- **1,532 rows checked by pixel rules only** (`lattice` = `vector+bands`), all in the body (747
  of them in h-rule tables). Their bands are confirmed by the pixels; their fields are read once.
- **5,025 amounts printed with no "$"** (`W.amount_bare`): every row of the member tables
  (Anti-Poverty, Boroughwide Needs, Speaker's Initiative) and of the three appendices. The year's
  layout, not a defect; the appendices equal their pots and the EIN census counts them.
- **The "Program" column of Art as a Catalyst for Change** (p.142, 40 rows, $720,000), in
  `purpose`, as FY2021 and FY2022.
- **65 rows with a header read from loose words or one cell**, **71 in tables carried over a page
  without a header**, **37 two-band names**, **71 line-end hyphens** (compound words and names).
  Routine flags.
- **Legal Aid Society, Low Wage Worker Support (p.124), printed with the City's EIN
  13-6400434**: the disclosure's City-EIN name rule flags it (`city_ein_name_mismatch`); `main`
  used 13-5562265.
- **Money with no rows, by design.** $80,569,432 held post-adoption; $36,632,969 designated
  straight to an agency.
- **Disclosure gaps.** 342 PDF rows ($27,627,019) have no disclosure row: 196 amount differs, 49
  key already used, 48 EIN not in the disclosure, 26 City-EIN name mismatch, 20 EIN used up, 3
  unreadable EIN. Every row and reason: `data/fy20_sc_disclosure_match.csv`.
