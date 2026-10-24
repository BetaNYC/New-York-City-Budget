# FY2024 Schedule C: what a person needs to check

**Report generated:** 2026-10-21 20:25 EDT. Source: `data/fy24_sc_review.csv` (39 rows),
sorted by how much money each could touch. Write each decision into
`data/fy24_sc_review_decisions.csv` by `review_id` (`source_error`, `parser_bug`,
`accepted_as_printed` or `needs_info`), columns `review_id,decision,note,decided_by,decided_at`.
"Suggest" is the conservative call; the decision is Noel's.

## The 11 critical rows

| # | review_id | Page | $ | What | What we did / suggest |
|---:|---|---:|---:|---|---|
| 1 | `bedc460d57d2` | 130–137 | 12,028,500 | **Eight landscape pages merged out of order.** pp.130–137 (1148×887, no printed page number) sit between printed pp.89 and 90, right after A Greener NYC's statement. Their 191 rows are cleaning, litter and BID sanitation awards ("Funds to be used for cleanups…"). They add to **exactly $12,028,500**, which is NYC Cleanup's box ($14,280,000, p.145) less its $2,251,500 post-adoption. A Greener NYC's own rows follow on printed pp.90–97 (pp.138–145). | Rows attached to **NYC Cleanup**, each flagged `H12.initiative_pages`. Left in page order they would give A Greener NYC $17,013,500 against a $5,100,000 box. Suggest `accepted_as_printed` (the amounts are as printed; only the initiative is inferred). |
| 2 | `9a8689307af6` | 152 | 374,219 | **First row with no rule above it.** Planned Parenthood of Greater New York, 13-2621497, $374,219 (Ending the Epidemic, continued from p.151). Nothing is drawn above it but the page-header rule, so no rule confirms its top. | Read from its band, with p.151's header. Crop `data/overlays/p152-0.png`. Suggest `accepted_as_printed`. |
| 3 | `8ba353215e9e` | 261 | 107,627 | **EIN copied from the row above.** Drama Club, Inc. is printed with 47-2288307, Digital Girl, Inc.'s EIN (the row above it; also pp.41, 46). The disclosure, and the data on `main`, give Drama Club 30-0836513. | Kept as printed. Suggest `source_error`. |
| 4 | `c09c40f2bac6` | 153 | 102,354 | Same as #2: Muslim Women's Institute for Research and Development, 80-0010627. | Crop `p153-0.png`. Suggest `accepted_as_printed`. |
| 5 | `b7a5b9ebd5f4` | 41 | 45,000 | Same shape as #2, on a fully ruled table: the column rules start 13 pt above the first rule, and no rule closes the top. Salamanca, Bronx Community Foundation, Inc., The – Council District 17, 81-4237999, $45,000, DYCD (read off the page). | Crop `p041-0.png`. Suggest `accepted_as_printed`. |
| 6 | `be89f5eeeee5` | 45 | 40,000 | Same: Ariola, Salvadori Center, Ltd., 11-2883503. | Suggest `accepted_as_printed`. |
| 7 | `c33057717b39` | 46 | 25,000 | Same: Restler, United Jewish Organizations of Williamsburg, Inc., 11-2728233. | Suggest `accepted_as_printed`. |
| 8 | `0cdb5c23177a` | 42 | 20,000 | Same: Farias, Educational Video Center, Inc., 13-3378456. | Suggest `accepted_as_printed`. |
| 9 | `34b925e70f86` | 43 | 20,000 | Same: Lee, Mouse, Inc., 13-3973196. | Suggest `accepted_as_printed`. |
| 10 | `2623e541756f` | 44 | 20,000 | Same: Velazquez, Older Adults Technology Services (OATS), Inc., 55-0882599. | Suggest `accepted_as_printed`. |
| 11 | `00ae54e5a85a` | 122 | 600,000 | **An empty band joined to a row.** Connect, Inc., 02-0694269, $600,000 (SAVE): the empty spacer band under it is part of its row, so a rule runs through the row. | Crop `p122-0.png` (looked at). Suggest `accepted_as_printed`. |

## The PDF disagrees with itself (9)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 12 | `5974719139ed` | 129 | 635,000 | **A Greener NYC.** Box $5,100,000; "will designate $750,000 post-adoption" leaves $4,350,000; its rows (pp.138–145) add to **$4,985,000**. ("Each Council District receives an allocation of $100,000.") | `source_error`. |
| 13 | `74d683068660` | 181 | 450,000 | **Mental Health Services for Vulnerable Populations.** Box $3,663,000 less $575,000 = $3,088,000; rows add to $2,638,000. | `source_error`. |
| 14 | `3d70b97c0a81` | — | 430,904 | The roll-up: exactly #12, #13, #15, #16, #17, #18 and #19 (+$635,000 − $450,000 + $175,000 + $78,969 − $60,000 + $52,935 − $1,000). | `source_error`, follows. |
| 15 | `1a68732ea61c` | 176 | 175,000 | **Autism Awareness.** Box $3,261,846 less $418,442 = $2,843,404; rows add to $3,018,404 (page image looked at). | `source_error`. |
| 16 | `8dcfa6d2ac82` | 148 | 78,969 | **Access Health.** Box $3,620,210 less $239,286 = $3,380,924; rows add to $3,459,893. | `source_error`. |
| 17 | `b9acf34dd211` | 109 | 60,000 | **DoVE.** Box $12,010,000 less $1,608,500 = $10,401,500; rows add to $10,341,500. | `source_error`. |
| 18 | `74a4b6fa4c75` | 63 | 52,935 | **Criminal Justice Services TOTAL.** Printed $28,658,710; its 7 lines add to $28,711,645 (page image looked at). The table is also titled "Fiscal 2023". | `source_error`. |
| 19 | `85503e5c22b6` | 147 | 1,000 | **Food Pantries.** "will designate $6.2 million": $1,000,000 + $59,000 + $6,200,000 = $7,259,000 vs the $7,260,000 box. Rounding. | `accepted_as_printed`. |
| 20 | `3bc1fb50f35f` | 201 | 0 | **Parks prints no summary table and no TOTAL** (as FY2025). Its box stands in for the TOTAL. | `accepted_as_printed`. |

## EINs and names (4)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 21 | `37a6bd2df12a` | 182 | 150,000 | Safe Horizon, Inc. printed "13-294-6970" (as FY2025). Clean EIN blank. | `source_error`. |
| 22 | `ce412af86fce` | 135 | 10,000 | Knickerbocker Avenue Merchants Partnership printed with Tax ID **"TF4876222"**. Clean EIN blank; `main` has 84-3309358 from the disclosure. | `source_error`. |
| 23 | `9e4d8ef2d88a` | 341 | 8,000 | Line-end hyphen: "…All Grades-" / "Public School/Intermediate School 187M". Kept as `Grades-Public`. | `accepted_as_printed`. |
| 24 | `ef89bb21758f` | 332 | 1,000 | Line-end hyphen before "Council District": Parks – "…Summer Programming -" / "Council District 36". | `accepted_as_printed`. |

## Names that differ between a box and its summary line (15, no money)

Rows carry the **box** title. Suggest `accepted_as_printed` for all.

| review_id | Page | Summary line says | Box says |
|---|---:|---|---|
| `bdd6a1aa5a9a` | 46 | Diversity, Inclusion and Equity in Tech **Initiative** | drops "Initiative" |
| `6e11c2c9376a` | 63 | Alternatives to Incarceration **(ATI)** | **(ATIs)** |
| `1672aeb9d0f6` | 122 | SAVE $2,450,000 | **two** SAVE boxes: $600,000 + $1,850,000 |
| `66700ef9d761` | 126 | LGBTQIA+ Inclusive Curriculum (Formerly **Known** as …) | (Formerly **known** as …) |
| `792826d73c8d` | 154 | Reproductive **&** Sexual Health Services | …**and**… |
| `de8e1513cdef` | 156 | Care Workers **for** Our Future | Care Workers **For** Our Future |
| `1e489e17df77` | 156 | Creative Arts Team **(CUNY CAT)** | Creative Arts Team |
| `e134d831a2af` | 163 | Financial Empowerment for NYC Renters | …NYC**'s** Renters |
| `d71790a696cd` | 174 | Fiscal 2024 Subsidy (BPL) | …: Brooklyn Public Library |
| `9be268ef6a38` | 174 | Fiscal 2024 Subsidy (NYPL) | …: New York Public Library |
| `5921290ddb90` | 174 | Fiscal 2024 Subsidy (QBPL) | …: Queens Public Library |
| `19c65298e907` | 175 | Fiscal 2024 Subsidy ((NYPL-R) Research) | …: Research Library |
| `48b8fbf048ad` | 179 | Developmental, Psychological **&** Behavioral Health Services | …**and**… |
| `52e9f86d86bc` | 180 | **LGBTQIA** Youth All-Borough Mental Health | **LGBTQIA+** … |
| `97038c7c5dc0` | 212 | Hate Crimes Prevention **Initiative** | drops "Initiative" |

## Not in the review file, on purpose

- **1,438 rows checked by pixel rules only** (`lattice` = `vector+bands`): tables with no drawn
  vertical rules. Their row bands are confirmed by the pixels; their fields are read once. See
  README, "What these checks cannot prove".
  *Update 2026-10-24 (#193):* All 1,438 now have `lattice` = `vector+columns` (`image_check`
  `columns_agree`): the image side finds their columns from the header's labels and the blank
  strips between them, and the text layer, clipped a second time through those cells, gives the
  same value in every field. It is the same text layer, so a text-layer error still passes.
- **645 rows read with a header carried from the page before** (`W.headerless_table`, 38 pages),
  **81 with a loose header** (`W.loose_header`), **927 in tables built from horizontal rules**
  (`W.hrule_table`). Routine flags; the image grid or the pixel rules checked each row.
- **81 line-end hyphens**, read by hand: 79 are compound words or names (Brooks-Powers,
  Woodhaven-Richmond Hill, Bed-Stuy, K-12) and keep the hyphen; the other 2 are #23, #24.
- **16 two-band names** (`W.continuation_row`), **1 unmapped glyph** (`(cid:9)`, p.135).
- **Money with no rows, by design.** $38,403,539 held post-adoption; $19,511,869 designated
  straight to CUNY (6 initiatives, pp.156–158; Vallone's statement splits $16,411,869 as $15,753,469 to
  CUNY + $658,400 to DOE, which adds up); the four library subsidies ($15,700,000, p.174).
- **Disclosure gaps.** 268 PDF rows ($10,565,141) have no disclosure row: 94 amount differs, 65
  EIN not in the disclosure, 56 key already used, 34 EIN used up, 17 City-EIN name mismatch, 2
  unreadable EIN (#21, #22). 1,788 disclosure rows have no PDF row: 1,703 amount or count
  differs ($80,922,376), 76 EIN not in the PDF, 9 City-EIN Pending. Every row and reason:
  `data/fy24_sc_disclosure_match.csv`.
