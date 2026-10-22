# FY2022 Schedule C: what a person needs to check

**Report generated:** 2026-10-21 23:55 EDT. Source: `data/fy22_sc_review.csv` (47 rows),
sorted by how much money each could touch. Write each decision into
`data/fy22_sc_review_decisions.csv` by `review_id` (`source_error`, `parser_bug`,
`accepted_as_printed` or `needs_info`), columns `review_id,decision,note,decided_by,decided_at`.
"Suggest" is the conservative call; the decision is Noel's.

## The 13 critical rows

| # | review_id | Page | $ | What | What we did / suggest |
|---:|---|---:|---:|---|---|
| 1 | `138e5d01f8cd` | 57 | 200,000 | **Public Health Funding Backfill: box and summary disagree.** The box prints $4,467,933; the summary line (p.52) prints $4,667,933, and the Health Services TOTAL uses it. The box is held whole post-adoption, so no rows decide it. | Kept both as printed. Suggest `source_error` (ask Council Finance if it matters). |
| 2 | `af73445e7d01` | 81 | 1,200,000 | **An empty band joined to a row.** Hetrick-Martin Institute, Inc., 13-3104537, $1,200,000 (LGBTQ Youth All-Borough Mental Health): the empty spacer band under it, before the next box's black bar, is part of its row (looked at). | Crop `data/overlays/p081-1.png`. Suggest `accepted_as_printed`. |
| 3 | `ac5b40349d76` | 81 | 1,200,000 | **The same row, seen by the image grid alone** (without the spacer band), so it has no vector partner. Not a missing award: #2 is it. | Crop `p081-0.png`. Suggest `accepted_as_printed`. |
| 4 | `0a48be9218b8` | 90 | 1,120,000 | **A name's second line in its own ruled band.** Services And Advocacy For Gay, Lesbian, Bisexual And Transgender Elders, Inc. (SAGE), 13-2947657, $1,120,000: "Inc." sits in the band below, joined to the row; the image reads the row without it (looked at). | Crop `p090-0.png`. Suggest `accepted_as_printed`. |
| 5 | `5a497d555a04` | 42 | 600,000 | Same as #2: Connect, Inc., 02-0694269, $600,000 (the first SAVE box; looked at). | Crop `p042-0.png`. Suggest `accepted_as_printed`. |
| 6 | `af5f6e6a427b` | 46 | 600,000 | Same class (#2/#4): United Way NYC, 13-2617681, $600,000. | Crop `p046-0.png`. Suggest `accepted_as_printed`. |
| 7 | `9251ac077b80` | 72 | 485,000 | Same: Legal Information for Families Today (LIFT), 13-3910567, $485,000. | Crop `p072-0.png`. Suggest `accepted_as_printed`. |
| 8 | `fe84254d8c99` | 62 | 320,334 | Same: Women In Need, Inc., 13-3164477, $320,334. | Crop `p062-0.png`. Suggest `accepted_as_printed`. |
| 9 | `9ea7178a59ce` | 43 | 275,000 | Same: Sanctuary for Families, Inc., 13-3193119, $275,000. | Crop `p043-0.png`. Suggest `accepted_as_printed`. |
| 10 | `724acbc92fc5` | 48 | 207,000 | Same: Good Shepherd Services, 13-5598710, $207,000. | Crop `p048-0.png`. Suggest `accepted_as_printed`. |
| 11 | `dade118979d8` | 117 | 122,425 | Same as #2: Sheltering Arms Children and Family Services, Inc., 13-3709095, $122,425 (Wrap-Around Support; looked at). | Crop `p117-1.png`. Suggest `accepted_as_printed`. |
| 12 | `86bae04c31fe` | 117 | 122,425 | Same as #3: the image grid's own reading of #11. Not a missing award. | Crop `p117-0.png`. Suggest `accepted_as_printed`. |
| 13 | `c92c781a36eb` | 45 | 30,000 | Same class: St. Nick's Alliance Corporation, 51-0192170, $30,000. | Crop `p045-0.png`. Suggest `accepted_as_printed`. |

## The PDF disagrees with itself or rounds (12)

All named exceptions in the config; none corrected.

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 14 | `dd649fd1cda6` | — | 6,545,340 | The roll-up: exactly #1 and #16–#25 (+$1,100,000 + $1,000,000 + $290,000 + $1,650,000 + $1,000,000 + $1,421,769 + $246,046 + $53,880 − $3,150 − $13,205 − $200,000). | `source_error`, follows |
| 15 | `9d59b7591658` | 37 | 3,462,000 | **"$3,462,000 million".** Initiative to Combat Sexual Assault: "will designate $3,462,000 million post-adoption". Read as $3,462,000; with the one row (Safe Horizon, $748,000) it makes the $4,210,000 box. | `accepted_as_printed` |
| 16 | `cef2c45f7ad4` | 44 | 1,650,000 | **City's First Readers.** "will designate $1.65 million post-adoption", but the 17 rows add to the whole $5,564,000 box. | `source_error` |
| 17 | `de4f32c73ead` | 119 | 1,421,769 | **Afterschool Enrichment Initiative.** $1,421,769 post-adoption; the 10 rows add to the whole $8,000,000 box. | `source_error` |
| 18 | `cb94c6da7e6a` | 34 | 1,100,000 | **LGBT Community Services.** "$1.1 million" post-adoption; rows add to the whole $4,725,000 box. | `source_error` |
| 19 | `31b8e20f4550` | 34 | 1,000,000 | **Trans Equity Programs.** "$1 million" post-adoption; rows add to the whole $3,275,000 box. | `source_error` |
| 20 | `59bf41d8b5c7` | 85 | 1,000,000 | **Crisis Management System.** "$1 million" post-adoption; rows add to the whole $3,925,600 box. | `source_error` |
| 21 | `0ca945dfb575` | 39 | 290,000 | **Supports for Persons Involved in the Sex Trade.** $290,000 post-adoption; rows add to the whole $4,434,697 box. | `source_error` |
| 22 | `e3ec713d2c4c` | 54 | 246,046 | **Ending the Epidemic.** Box $7,735,000 less $936,446 = $6,798,554; the 42 rows add to $7,044,600. | `source_error` |
| 23 | `060218d10c59` | 58 | 53,880 | **Viral Hepatitis Prevention.** Box $1,923,658 less $260,091 = $1,663,567; the 30 rows add to $1,717,447. | `source_error` |
| 24 | `26be4bfb4119` | 36 | 13,205 | Alternatives to Incarceration (ATIs): "$3 million" post-adoption; the rows leave $3,013,205. Rounding. | `accepted_as_printed` |
| 25 | `676f68ef6ab5` | 115 | 3,150 | **Dedicated Contraceptive Fund.** Box $781,000; its 4 rows add to $777,850. | `source_error` |

## EINs and line-end hyphens (6)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 26 | `33d5ccf09090` | 48 | 250,000 | Teachers College, Columbia University printed "13-11624202" (10 digits). Clean EIN blank. | `source_error` |
| 27 | `206b3e50d102` | 79 | 212,500 | Getting Out and Staying Out printed "61-711370" (8 digits). | `source_error` |
| 28 | `a32dc02dbe05` | 80 | 86,000 | Sunnyside Community Services, Inc. printed "51-189327". | `source_error` |
| 29 | `d44b9c8f4a36` | 52 | 67,692 | Community Health Center of Richmond, Inc. printed "51-567466". | `source_error` |
| 30 | `843ae354a349` | 82 | 50,000 | Amudim Community Resources, Inc. printed "47-984801". | `source_error` |
| 31 | `2bac9f2b35e0` | 243 | 25,000 | Line-end hyphen: "…McSilver Institute for Poverty Policy-" / "Step Up Program". Kept as `Policy-Step Up`. | `accepted_as_printed` |

## Names that differ between a box and its summary line (16, no money except one)

Rows carry the **box** title. Suggest `accepted_as_printed` for all but Public Health Funding
Backfill, which is #1 above.

| review_id | Page | Summary line says | Box says |
|---|---:|---|---|
| `9f1bc45e32e7` | 33 | Diversity, Inclusion and Equity in Tech **Initiative** | drops "Initiative" |
| `744a51310342` | 36 | Alternatives to Incarceration **(ATI)** | **(ATIs)** |
| `9541121630dd` | 42 | SAVE $2,450,000 | **three** SAVE boxes: $600,000 + $850,000 (p.42) + $1,000,000 (p.43) |
| `dded18d13298` | 56 | HIV/AIDS Faith Based | HIV/AIDS Faith**-**Based |
| `6640edb3c389` | 57 | Reproductive **&** Sexual Health Services | …**and**… |
| `d26c60cf20d3` | 57 | Public Health Funding Backfill **$4,667,933** | **$4,467,933** (see #1) |
| `3d0c6804fb1a` | 61 | CUNY Child Care Expansion | CUNY Childcare Expansion |
| `9f451e699fe5` | 61 | Creative Arts Team **(CUNY CAT)** | Creative Arts Team |
| `f464818673e2` | 65 | Financial Empowerment for NYC Renters | …NYC**'s** Renters |
| `e3676a839b5a` | 75 | Fiscal 2022 Subsidy (NYPL) | …: New York Public Library |
| `e8990c8e4007` | 75 | Fiscal 2022 Subsidy (BPL) | …: Brooklyn Public Library |
| `f9f69b8d6ea3` | 75 | Fiscal 2022 Subsidy ((NYPL-R) Research) | …: Research Library |
| `65d789e57954` | 76 | Fiscal 2022 Subsidy (QBPL) | …: Queens Borough Public Library |
| `a27b3eb5fab4` | 79 | Developmental, Psychological **&** Behavioral Health Services | …**and**… |
| `1148d8994b3c` | 84 | Art a Catalyst for Change | Art **as** a Catalyst for Change |
| `140a32be103d` | 117 | Young Women**'**s Leadership Development | Young Women**’**s … (curly apostrophe) |

## Not in the review file, on purpose

- **106 rows checked by pixel rules only** (`lattice` = `vector+bands`): the h-rule tables of
  pp.84, 85, 116. Their row bands are confirmed by the pixels; their fields are read once.
- **The "Program" column of Art as a Catalyst for Change** (pp.84–85, 40 rows): read into
  `purpose` (e.g. "Heritage High School"). A decision for Noel (PR body), not a review row.
- **p.65 Financial Empowerment for NYC's Renters** ($450,000): "has allocated $195,000 directly
  to HPD, $25,000 directly to DCA, and has designated the following provider" ($230,000 of
  rows). The $220,000 is read as the part with no rows; it adds up.
- **14 rows read with a header carried from the page before** (`W.headerless_table`, p.84's
  table), **52 in tables built from horizontal rules** (`W.hrule_table`). Routine flags.
- **68 line-end hyphens**, read by hand: 67 are compound words or names (after-school,
  low-income, Multi-Social, Social-Emotional, (Bedford-Stuyvesant)) and keep the hyphen; the
  other is #31.
- **6 two-band names** (`W.continuation_row`), **2 unmapped glyphs** (`(cid:N)`, pp.166, 190).
- **Money with no rows, by design.** $203,090,898 held post-adoption; $33,826,369 designated
  straight to CUNY (Vallone Scholarship $16,411,869, split as $15,753,469 + $658,400 to DOE;
  SLU, Childcare Expansion, Creative Arts Team, Diversity Incubator), to DOE (Work-Based Learning
  Internships, p.117) and the four library subsidies ($14,000,000, pp.75–76).
- **Disclosure gaps.** 177 PDF rows ($22,364,486) have no disclosure row: 75 amount differs, 56
  EIN not in the disclosure, 17 City-EIN name mismatch, 15 key already used, 9 EIN used up, 5
  unreadable EIN (#26–#30). 5,781 disclosure rows have no PDF row (the FY2022 workbook, 11,336
  rows, also holds designations made after adoption). Every row and reason:
  `data/fy22_sc_disclosure_match.csv`.
