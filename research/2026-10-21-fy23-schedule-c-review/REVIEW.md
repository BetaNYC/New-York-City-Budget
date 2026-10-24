# FY2023 Schedule C: what a person needs to check

**Report generated:** 2026-10-21 22:55 EDT. Source: `data/fy23_sc_review.csv` (53 rows),
sorted by how much money each could touch. Write each decision into
`data/fy23_sc_review_decisions.csv` by `review_id` (`source_error`, `parser_bug`,
`accepted_as_printed` or `needs_info`), columns `review_id,decision,note,decided_by,decided_at`.
"Suggest" is the conservative call; the decision is Noel's.

## The 17 critical rows

| # | review_id | Page | $ | What | What we did / suggest |
|---:|---|---:|---:|---|---|
| 1 | `5c1ea3c592f5` | 83 | 1,880,000 | **Low Wage Worker Support: box and summary disagree.** The box prints $120,000, which is what its two rows add to (NICE $40,000, NYCOSH $80,000). The summary line (p.81) prints $2,000,000, and the Legal Services TOTAL uses it. The statement holds "$1.8 million" post-adoption; $120,000 + $1,880,000 = $2,000,000. | Rows kept as printed; the box is the printed $120,000. Suggest `source_error` (the box should say $2,000,000; ask Council Finance if it matters). |
| 2 | `addf327a197a` | 86 | 150,000 | **Autism Awareness: box and summary disagree.** The box prints $3,166,846; the summary line prints $3,316,846. The 38 rows ($3,261,846) plus the $55,000 held after adoption make $3,316,846. | Suggest `source_error` (the box looks mistyped: 16 for 31). |
| 3 | `f842b0aeae4d` | 175 | 75,000 | **EIN of another organization.** Asiyah Women's Center (Speaker; Brannan, Brooklyn, Hanif) is printed with 822712941, the EIN of Muslims Giving Back, Inc. (pp.21, 245). The disclosure, and the data on `main`, give Asiyah 832104070. | Kept as printed. Suggest `source_error`. |
| 4 | `186283d4be9b` | 13 | 10,000 | Same as #3: Asiyah Women's Center (Brannan, Anti-Poverty), $10,000. | Suggest `source_error`. |
| 5 | `163f240bb2b0` | 53 | 3,000,000 | **An empty band joined to a row.** New York City United Community Schools, 46-1227433, $3,000,000 (Community Schools): the empty spacer band under it, before the next box's black bar, is part of its row, so a rule runs through the row. | Crop `data/overlays/p053-0.png`. Suggest `accepted_as_printed`. |
| 6 | `bf52ac293034` | 55 | 3,000,000 | Same: Department of Education – Arts Instruction, 13-6400434, $3,000,000 (Support for Arts Instruction). | Crop `p055-1.png`. Suggest `accepted_as_printed`. |
| 7 | `70d3a0797e63` | 55 | 2,000,000 | Same: Department of Education – SAPIS, 13-6400434, $2,000,000 (looked at). | Crop `p055-0.png`. Suggest `accepted_as_printed`. |
| 8 | `084364a08c51` | 49 | 600,000 | Same: Connect, Inc., 02-0694269, $600,000 (the first SAVE box; looked at). | Crop `p049-0.png`. Suggest `accepted_as_printed`. |
| 9 | `2a6bb02def4e` | 53 | 600,000 | Same: United Way of New York City, 13-2617681, $600,000 (Educational Programs for Students). | Crop `p053-1.png`. Suggest `accepted_as_printed`. |
| 10 | `e91ef8c9d66e` | 92 | 350,000 | Same: Young Men's Christian Association of Greater New York, 13-1624228, $350,000 (Opioid Prevention and Treatment; looked at), over the "Trauma Recovery Centers 2,400,000" bar. | Crop `p092-0.png`. Suggest `accepted_as_printed`. |
| 11 | `c0ef11620d71` | 70 | 320,334 | Same: Women In Need, Inc., 13-3164477, $320,334. | Crop `p070-0.png`. Suggest `accepted_as_printed`. |
| 12 | `5171353e74bf` | 54 | 250,000 | Same: New York Road Runners, Inc., 13-2949483, $250,000. | Crop `p054-0.png`. Suggest `accepted_as_printed`. |
| 13 | `d1e231a74f09` | 103 | 95,000 | Same: Third Sector New England, 04-2261109, $95,000 (looked at). | Crop `p103-0.png`. Suggest `accepted_as_printed`. |
| 14 | `8e697cd61a68` | 59 | 50,000 | Same: East River Development Alliance, Inc. (Urban Upbound), 86-1096987, $50,000. | Crop `p059-0.png`. Suggest `accepted_as_printed`. |
| 15 | `20fd93c23915` | 52 | 30,000 | Same: St. Nick's Alliance Corporation, 51-0192170, $30,000. | Crop `p052-0.png`. Suggest `accepted_as_printed`. |
| 16 | `4b1dfdfb2be3` | 35 | 30,000 | **First row with no rule above it.** Chinese-American Family Alliance for Mental Health, Inc., 26-4048050, $30,000 (AAPI): the header and this row share one band with no rule between (looked at); the band was cut between them. | Crop `p035-0.png`. Suggest `accepted_as_printed`. |
| 17 | `7203f36323e6` | 185 | 2,500 | **The image grid reads one row differently.** Brooklyn Defender Services - Legal & Social Work Services - Council District 33, 113305406, $2,500 (Restler): the name's trailing "-" runs over the EIN column's rule, so the image puts it in the EIN cell (looked at). The text layer has it at the end of the name. | Suggest `accepted_as_printed`. |

## The PDF disagrees with itself or rounds (13)

All named exceptions in the config; none corrected.

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 18 | `60d30e197381` | 83 | 1,800,000 | Low Wage Worker Support: box $120,000 less "$1.8 million" is negative; the rows make the box. Follows #1. | `source_error` |
| 19 | `5e23c23b81d0` | 82 | 1,100,000 | **Legal Services for Low-Income New Yorkers.** Box $5,800,000 less "$1.1 million" post-adoption = $4,700,000; the 7 rows add to the whole $5,800,000. | `source_error` |
| 20 | `4d66285c3481` | — | 646,350 | The roll-up: exactly #18–#30 (−$120,000 + $13,000 − $60,250 + $325,000 − $34,697 − $50,000 − $500 − $30,203 + $1,100,000 − $80,000 − $416,000; Autism nets to $0 against the summary). | `source_error`, follows |
| 21 | `c86863bceb1b` | 136 | 416,000 | **Young Women's Leadership Development.** Box $1,805,500; its 24 rows (p.137, page read) add to $1,389,500. | `source_error` |
| 22 | `7343a78c371a` | 43 | 325,000 | **Innovative Criminal Justice Programs.** Box $2,637,948 less $325,000 post-adoption = $2,312,948; the 10 rows add to the whole box. | `source_error` |
| 23 | `170bd2acf96b` | 86 | 150,000 | Autism Awareness: box less $55,000 = $3,111,846; rows $3,261,846. Follows #2. | `source_error` |
| 24 | `770dd36fc602` | 34 | 120,000 | **AAPI.** Box $5,000,000 less $1,020,000 = $3,980,000; the 44 rows (pp.34–35) add to $3,860,000. | `source_error` |
| 25 | `22ccfb411398` | 43 | 60,250 | **Initiative to Combat Sexual Assault.** Box $4,210,000 less "$3.5 million" = $710,000; the 4 rows add to $649,750, so the reserve is really $3,560,250. Rounding. | `accepted_as_printed` |
| 26 | `90d63ce2c958` | 53 | 50,000 | **Educational Programs for Students.** Box $7,143,133; the 10 rows add to $7,093,133. | `source_error` |
| 27 | `fec82b45a0b0` | 44 | 34,697 | Supports for Persons Involved in the Sex Trade: "$4.4 million" post-adoption for a $4,434,697 box. Rounding. | `accepted_as_printed` |
| 28 | `9c0cdbb4aa58` | 59 | 30,203 | Food Pantries: "$6.6 million" post-adoption + "$1 million" designated vs a $7,630,203 box. The one row is the $1,000,000 stated. Rounding. | `accepted_as_printed` |
| 29 | `18a488723d4c` | 42 | 13,000 | Alternatives to Incarceration (ATIs): "$14.5 million" post-adoption for a $14,487,000 box. Rounding. | `accepted_as_printed` |
| 30 | `30182d965dcb` | 54 | 500 | **Social and Emotional Supports for Students.** Box $1,916,500; the 5 rows add to $1,916,000. | `source_error` |

## Values read in an unusual way (6)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 31 | `d83b9f331a32` | 92 | 2,400,000 | Box "Trauma Recovery Centers" printed **2,400,000 with no "$"** (looked at). Read as $2,400,000; the summary line (p.86) says $2,400,000. Its statement: "will designate post adoption." | `accepted_as_printed` |
| 32 | `fc13598169fe` | 98 | 247,765 | The "I" of "Inc." sits in a 5 pt phantom column; read into the name: "Metropolitan New York Coordinating Council on Jewish Poverty, Inc." (looked at). | `accepted_as_printed` |
| 33 | `c8a0d834a577` | 176 | 15,000 | BAFA - Bangladesh Academy of Fine Arts, Inc.: the purpose's printed text ends "… in conjunction with Council Member", which H6 takes for page furniture. It is the PDF's text, cut short. | `accepted_as_printed` |
| 34 | `c231b2927c37` | 213 | 5,000 | **One of the two lost Local rows.** Elite Community Foundation, Inc. - Council District 47 (Kagan), EIN printed "84 -2079676" (a space before the hyphen; looked at). Clean EIN blank. | `source_error` |
| 35 | `42eba5fef74a` | 235 | 5,000 | **The other.** Laundromat Project, Inc., The (Ossé): the page shows 87-0753479 (looked at); the text layer has a space for the hyphen. Clean EIN blank. | `accepted_as_printed` (the EIN is 870753479 on the page; note it) |
| 36 | `3bae83a8c666` | 199 | 5,000 | Line-end hyphen before "Council District": Connect, Inc. - Community Empowerment Program-Council District 35. | `accepted_as_printed` |

## Names that differ between a box and its summary line (17, no money except two)

Rows carry the **box** title. Suggest `accepted_as_printed` for all but the two money ones,
which are #1 and #2 above.

| review_id | Page | Summary line says | Box says |
|---|---:|---|---|
| `75e7a5e5be51` | 34 | AAPI Community Support | AAPI |
| `aa458d9c7ee4` | 38 | Diversity, Inclusion and Equity in Tech **Initiative** | drops "Initiative" |
| `dc7e02ebee2c` | 42 | Alternatives to Incarceration **(ATI)** | **(ATIs)** |
| `c2920e4be06c` | 49 | SAVE $2,450,000 | **three** SAVE boxes: $600,000 + $850,000 (p.49) + $1,000,000 (p.50) |
| `b3a0f412d9b6` | 63 | HIV/AIDS Faith Based | HIV/AIDS Faith**-**Based |
| `5f3858a67456` | 64 | Reproductive **&** Sexual Health Services | …**and**… |
| `e602d8113a98` | 68 | Creative Arts Team **(CUNY CAT)** | Creative Arts Team |
| `880123f31f54` | 74 | Financial Empowerment for NYC Renters | …NYC**'s** Renters |
| `80c47e8ba89f` | 83 | Low Wage Worker Support **$2,000,000** | **$120,000** (see #1) |
| `019971983c80` | 84 | Fiscal 2023 Subsidy ((NYPL-R) Research) | …: Research Library |
| `1d3195d45268` | 84 | Fiscal 2023 Subsidy (BPL) | …: Brooklyn Public Library |
| `ca7f2069303c` | 84 | Fiscal 2023 Subsidy (NYPL) | …: New York Public Library |
| `e03d4fae5809` | 85 | Fiscal 2023 Subsidy (QBPL) | …: Queens Borough Public Library |
| `c14d4414ba1d` | 86 | Autism Awareness **$3,316,846** | **$3,166,846** (see #2) |
| `7130a9da7163` | 89 | Developmental, Psychological **&** Behavioral Health Services | …**and**… |
| `0f0bd3d3bdfa` | 94 | Art a Catalyst for Change | Art **as** a Catalyst for Change |
| `d2de48f8a72c` | 136 | Young Women**'**s Leadership Development | Young Women**’**s … (curly apostrophe) |

## Not in the review file, on purpose

- **1,028 rows checked by pixel rules only** (`lattice` = `vector+bands`): tables with no drawn
  vertical rules. Their row bands are confirmed by the pixels; their fields are read once. See
  README, "What these checks cannot prove".
  *Update 2026-10-24 (#193):* All 1,028 now have `lattice` = `vector+columns` (`image_check`
  `columns_agree`): the image side finds their columns from the header's labels and the blank
  strips between them, and the text layer, clipped a second time through those cells, gives the
  same value in every field. It is the same text layer, so a text-layer error still passes.
- **828 rows read with a header carried from the page before** (`W.headerless_table`, 41 pages:
  p.51 and pp.295–334), **3 with a loose header** (`W.loose_header`, p.80), **594 in tables
  built from horizontal rules** (`W.hrule_table`). Routine flags; the image grid or the pixel
  rules checked each row.
- **66 line-end hyphens**, read by hand: 65 are compound words or names (low-income,
  after-school, Bed-Stuy, Brooks-Powers, Woodhaven-Richmond Hill) and keep the hyphen; the other
  is #36.
- **19 two-band names** (`W.continuation_row`), **1 unmapped glyph** (`(cid:N)`, p.275, SCORE).
- **Money with no rows, by design.** $178,301,269 held post-adoption; $35,526,369 designated
  straight to CUNY (Vallone Scholarship $16,411,869, split in its statement as $15,753,469 to
  CUNY + $658,400 to DOE, which adds up; SLU, Childcare Expansion, Creative Arts Team, Diversity
  Incubator), to DOE (Work-Based Learning Internships, p.136) and the four library subsidies
  ($15,700,000, pp.84–85).
- **"Fiscal 2022" in two statements** (pp.49, 50, Domestic Violence Services): typos, read as
  the statements they are.
- **Disclosure gaps.** 212 PDF rows ($18,563,055) have no disclosure row: 112 amount differs, 48
  EIN not in the disclosure, 30 key already used, 17 City-EIN name mismatch, 3 EIN used up, 2
  unreadable EIN (#34, #35). 5,314 disclosure rows have no PDF row: 4,827 amount or count
  differs ($217,641,815), 476 EIN not in the PDF, 11 City-EIN Pending. The FY2023 workbook
  (11,027 rows) also holds designations made after adoption. Every row and reason:
  `data/fy23_sc_disclosure_match.csv`.
