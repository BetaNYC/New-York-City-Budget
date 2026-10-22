# FY2021 Schedule C: what a person needs to check

**Report generated:** 2026-10-22 01:50 EDT. Source: `data/fy21_sc_review.csv` (48 rows),
sorted by how much money each could touch. Write each decision into
`data/fy21_sc_review_decisions.csv` by `review_id` (`source_error`, `parser_bug`,
`accepted_as_printed` or `needs_info`), columns `review_id,decision,note,decided_by,decided_at`.
"Suggest" is the conservative call; the decision is Noel's.

## The 8 critical rows

| # | review_id | Page | $ | What | What we did / suggest |
|---:|---|---:|---:|---|---|
| 1 | `33e602cf8dba` | 48 | 600,000 | **An empty band joined to a row.** CONNECT, Inc., 02-0694269, $600,000 (the first SAVE box): the empty spacer band under it, before the next SAVE box's black bar, is part of its row (looked at). | Crop `data/overlays/p048-1.png`. Suggest `accepted_as_printed`. |
| 2 | `4ce43827223d` | 48 | 600,000 | **The same row, seen by the image grid alone** (without the spacer band), so it has no vector partner. Not a missing award: #1 is it. | Crop `p048-0.png`. Suggest `accepted_as_printed`. |
| 3 | `c8a4f704fdc5` | 122 | 477,000 | **The box prints "$477,00".** Initiative for Immigrant Survivors of Domestic Violence: the black bar reads "$477,00" (looked at, one zero short); its summary line on the same page prints $477,000, and the $81,000 reserve plus the 9 rows ($396,000) make $477,000. Read as $477,000 (config `box_amount_read`); the printed text is kept in `amount_printed`. | Suggest `source_error`. |
| 4 | `44145080a68e` | 49 | 450,000 | Same as #1: New York City Outward Bound Center, $450,000 (College and Career Readiness). | Crop `p049-0.png`. Suggest `accepted_as_printed`. |
| 5 | `546e6f53c97e` | 69 | 272,284 | Same as #1: Women In Need, Inc., $272,284 (Children and Families in NYC Homeless System). | Crop `p069-1.png`. Suggest `accepted_as_printed`. |
| 6 | `0d1d750eacca` | 69 | 272,284 | Same as #2: the image grid's own reading of #5. | Crop `p069-0.png`. Suggest `accepted_as_printed`. |
| 7 | `ecdc520e676e` | 72 | 51,850 | Same as #1: West Harlem Group Assistance, Inc., 23-7169558, $51,850, before Community Land Trust's bar (looked at). | Crop `p072-1.png`. Suggest `accepted_as_printed`. |
| 8 | `f52f9f5433c8` | 72 | 51,850 | Same as #2: the image grid's own reading of #7. | Crop `p072-0.png`. Suggest `accepted_as_printed`. |

## The PDF disagrees with itself or rounds (6)

All named exceptions in the config; none corrected.

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 9 | `841cdfe7136a` | — | 129,070 | The roll-up: exactly #10–#14 (+$90,000 + $82,769 + $15,300 + $1 − $59,000). | `source_error`, follows |
| 10 | `1aebc9044617` | 44 | 90,000 | **Coalition Theaters of Color.** "will designate $90,000 post-adoption", but the 50 rows add to the whole $3,740,000 box. | `source_error` |
| 11 | `f483739725f1` | 107 | 82,769 | **MWBE Leadership Associations.** $82,769 post-adoption; the 8 rows add to the whole $510,000 box. | `source_error` |
| 12 | `04d4aaf8430a` | 55 | 59,000 | Food Pantries: "$4.6 million post-adoption" and "$1 million" designated; the box is $5,659,000, so the reserve is $4,659,000. Rounding. | `accepted_as_printed` |
| 13 | `dd3aba5da914` | 93 | 15,300 | **Art as a Catalyst for Change.** $15,300 post-adoption; the 40 rows add to the whole $612,000 box. | `source_error` |
| 14 | `151fcd922dc0` | 39 | 1 | Alternatives to Incarceration (ATIs): box $11,878,800 less $256,500 = $11,622,300; the 19 rows add to $11,622,301. | `source_error` |

## Values the parse read in a way a person should confirm (2)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 15 | `afd2a24c928a` | 49 | 21,679,075 | Education's summary TOTAL prints "21,679,075" with no "$". Read as the number; it equals its 8 lines. | `accepted_as_printed` |
| 16 | `26f505650310` | 98 | 5,400,325 | NORCs: the box is drawn narrower than its black bar, "$5,400,325" printed beside it outside the rules (looked at). Read as the box's amount; equals its summary line. | `accepted_as_printed` |

## EINs (7)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 17 | `138ee84f2723` | 87 | 212,500 | Getting Out and Staying Out printed "61-711370" (8 digits). Clean EIN blank. | `source_error` |
| 18 | `11ec0919663e` | 91 | 85,000 | SAFE Foundation, Inc. printed "26-102131". | `source_error` |
| 19 | `60f6f34ae8ad` | 89 | 73,100 | Sunnyside Community Services, Inc. printed "51-189327". | `source_error` |
| 20 | `8182a76d1574` | 61 | 52,700 | **Congregation Beit Simchat Torah prints two EINs**: 11-2527706 here (HIV/AIDS Faith-Based), 23-7406899 on p.63 (Public Health Funding Backfill). Kept as printed; `main` (repaired from the disclosure) uses 23-7406899 for both. | `needs_info` (which EIN is the organization's) |
| 21 | `7964af3acab0` | 90 | 42,500 | Amudim Community Resources, Inc. printed "47-984801". | `source_error` |
| 22 | `96b514e31a42` | 65 | 2,061 | Transgender Legal Defense and Education Fund printed "43-762842"; p.60 prints 04-3762842. | `source_error` |
| 23 | `cc171c3dde22` | 64 | 340 | La Casa de Salud, Inc. printed "20-693325"; p.60 prints 02-0693325. | `source_error` |

## Letters read across an 8.9 pt edge column (9, p.105)

`W.sliver_char` rows `c73a8a136e48`, `bacb4901212e`, `c4cee1a998ed`, `e9acaf3fdb54`,
`897a860fe639`, `25a35d2ae830`, `f227f29ce5f9`, `4d832bf2fe21`, `effe7d96aa01` (Construction Site
Safety Training, $118,750 each but the last, $95,000): each row's first letter sits in the white
column down the table's left edge and its last "0" in the right one. Read joined ("East River
Development All", "$118,750"); the 9 rows add to the $1,045,000 box. Suggest
`accepted_as_printed` for all.

## Names that differ between a box and its summary line (16, no money)

Rows carry the **box** title. Suggest `accepted_as_printed` for all.

| review_id | Page | Summary line says | Box says |
|---|---:|---|---|
| `68e2d659dd59` | 37 | Diversity, Inclusion and Equity in Tech **Initiative** | drops "Initiative" |
| `4d90247ccac0` | 39 | Alternatives to Incarceration **(ATI)** | **(ATIs)** |
| `3d369b9437ff` | 48 | SAVE $2,450,000 | **three** SAVE boxes: $600,000 + $850,000 + $1,000,000 (p.48) |
| `757e663a9c46` | 60 | HIV/AIDS Faith Based | HIV/AIDS Faith**-**Based |
| `101c898dee4d` | 68 | CUNY Child Care Expansion | CUNY Childcare Expansion |
| `4c1cac643d96` | 68 | Creative Arts Team **(CUNY CAT)** | Creative Arts Team |
| `df2ed63b9715` | 72 | Financial Empowerment for NYC Renters | …NYC**'s** Renters |
| `369ac23f5445` | 83 | Fiscal 2021 Subsidy (Research) | …: Research Library |
| `01a9f18eabe9` | 83 | Fiscal 2021 Subsidy (BPL) | …: Brooklyn Public Library |
| `50db07e41b39` | 83 | Fiscal 2021 Subsidy (NYPL) | …: New York Public Library |
| `9c7712192d34` | 84 | Fiscal 2021 Subsidy (QBPL) | …: Queens Borough Public Library |
| `0aa4e34d4f64` | 87 | Developmental, Psychological **&** Behavioral Health Services | …**and**… |
| `3788e6be548e` | 93 | Art a Catalyst for Change | Art **as** a Catalyst for Change |
| `b02b8902cbb0` | 97 | Elie Wiesel Holocaust Survivors **Initiative** | drops "Initiative" |
| `34496e019b96` | 124 | Young Women**'**s Leadership Development | Young Women**’**s … (curly apostrophe) |
| `ae70039849e1` | 128 | Sports Training and Rolemodels for Success Initiative | adds **(STARS)** |

## Not in the review file, on purpose

- **431 rows checked by pixel rules only** (`lattice` = `vector+bands`), all in the body: the
  tables whose header is printed outside the drawn grid. Their row bands are confirmed by the
  pixels; their fields are read once. See README "cannot prove".
- **Sub-headings in `purpose`** (pp.70–72, 67 rows, `W.subheading`): Technical Assistance (2 rows,
  $135,540), Community Consultant Contracts (34, $859,190), Housing Preservation Initiative (31,
  $2,031,500). With the $77,120 reserve they make the $3,103,350 box; the scope text's $884,460
  and $2,083,350 are each one share of the reserve higher. A decision for Noel (PR body).
- **The "Program" column of Art as a Catalyst for Change** (pp.93–94, 40 rows), in `purpose`, as
  FY2022.
- **81 rows with a header read from loose words** (`W.band_header`), **511 with a header printed
  above the table** (`W.loose_header`), **61 in tables carried over a page without a header**,
  **26 in tables built from horizontal rules**, **38 two-band names**. Routine flags.
- **66 line-end hyphens**, all compound words or names (after-school, Bedford-Stuyvesant, …).
- **p.122's summary table is titled "Fiscal 2020 Young Women's Initiatives"** (a typo in the
  PDF; read through `summary_titles`).
- **Money with no rows, by design.** $82,317,815 held post-adoption; $31,080,469 designated
  straight to CUNY (Vallone Scholarship $16,285,469, split as $15,753,469 + $532,000 to DOE;
  SLU, Childcare Expansion, Creative Arts Team, Diversity Incubator), to DOE (Work-Based Learning
  Internships, p.124) and the four library subsidies ($11,900,000, pp.83–84).
- **Disclosure gaps.** 305 PDF rows ($17,987,653) have no disclosure row: 132 amount differs,
  101 EIN not in the disclosure, 33 EIN used up, 19 key already used, 14 City-EIN name mismatch,
  6 unreadable EIN. Every row and reason: `data/fy21_sc_disclosure_match.csv`.
