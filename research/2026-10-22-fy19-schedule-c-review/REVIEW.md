# FY2019 Schedule C: what a person needs to check

**Report generated:** 2026-10-22 04:40 EDT. Source: `data/fy19_sc_review.csv` (38 rows),
sorted by how much money each could touch. Write each decision into
`data/fy19_sc_review_decisions.csv` by `review_id` (`source_error`, `parser_bug`,
`accepted_as_printed` or `needs_info`), columns `review_id,decision,note,decided_by,decided_at`.
"Suggest" is the conservative call; the decision is Noel's.

## The 5 critical rows

| # | review_id | Page | $ | What | What we did / suggest |
|---:|---|---:|---:|---|---|
| 1 | `2572ae2f5212` | 105 | 2,643,500 | **A list under an award, read as no award.** Under Consortium for Worker Education (CWE) – Jobs to Build On** (13-3564313, $5,154,200), "**Below is a list of the Jobs to Build On service providers partners:" and a table "Organization \| EIN \| Amount \| Service Type": 13 rows here (South Bronx Overall Economic Development Corp $203,000, Henry Street Settlement $273,000, …). Counting them would count CWE's money twice. The old parse had them as awards. | Suggest `accepted_as_printed` (not awards). If Noel wants them kept, they belong in a separate table, not the award rows. |
| 2 | `b7de66d4e62f` | 106 | 1,820,000 | Same list, continued: 15 rows. With p.105 the list adds to $4,463,500, **$690,700 less than CWE's $5,154,200 row**. | Suggest `accepted_as_printed`; the gap is the PDF's (`needs_info` if it matters: ask Council Finance). |
| 3 | `35418b7e505f` | 87 | 50,000 | **A two-line name joined across a rule.** Young Men's and Young Women's Hebrew Association of Washington / Heights and Inwood, 13-1635308, $50,000: the PDF draws a rule between the name's two lines; the parse joins them (`continuation_rows`). The image sees the rule. Looked at: one award. | Crop `data/overlays/p087-0.png`. Suggest `accepted_as_printed`. |
| 4 | `10cbaf9cd673` | 144 | 5,000 | **The image reads a "-" into the EIN.** Appendix A, Miller, Jamaica Service Program for Older Adults (JSPOA), Inc. - JSPOA - / Transportation Program, 510204121, *, 5,000: the name's line-end "-" runs over the EIN column's rule; the image puts it in the EIN, the vector cell keeps it in the name. Looked at. | Crop `p144-0.png`. Suggest `accepted_as_printed`. |
| 5 | `2d009ca911d2` | 206 | 4,000 | Same as #4: Appendix B, Rosenthal, Department of Transportation - Bike Safety & Helmet Give- / away - CD6, 136400434, 4,000. | Crop `p206-0.png`. Suggest `accepted_as_printed`. |

## The PDF disagrees with itself (11 items, 12 rows)

All named exceptions in the config; none corrected.

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 6 | `dd6c60caebda` | 59 | 2,465,000 | **Community Boards Enhancement**: "allocated directly to the Community Boards and each is designated $42,500". 59 × $42,500 = $2,507,500, the box. The check reads $42,500 as the stated total. | `accepted_as_printed` |
| 7 | `3e86a8a56286` | 49 | 2,450,000 | **A box for the whole SAVE initiative**, $2,450,000, printed over its three parts' boxes ($600,000, $850,000, $1,000,000, whose rows are under them). It has no rows of its own; the summary line counts $2,450,000 once. | `accepted_as_printed` |
| 8 | `ddc25a54a345` | — | 914,919 | The roll-up: exactly #9–#15 ($200,000 + $185,000 + $179,919 + $150,000 + $100,000 + $50,000 + $50,000). | follows #9–#15 |
| 9 | `60afad0b64b6` | 43 | 200,000 | **A reserve printed again as a row.** Support for Victims of Human Trafficking: "will designate $200,000 post-adoption"; its rows include Mayor's Office of Criminal Justice, 13-6400434, $200,000, so they add to the box ($1,200,000), not $1,000,000. | `accepted_as_printed` (the agency row is the reserve, printed) |
| 10 | `ec3b2cf01a32` | 37 | 185,000 | Same: Adult Literacy Initiative, Department of Youth and Community Development, 13-6400434, $185,000 (p.38). | `accepted_as_printed` |
| 11 | `4669485badd0` | 72 | 179,919 | Same: Community Housing Preservation Strategies, four Housing Preservation and Development rows, 13-6400434 ($29,730, $29,730, $61,000, $59,459, p.73), add to the "$179,919" reserve. | `accepted_as_printed` |
| 12 | `93b35e43c47c` | 62 | 150,000 | **Ending the Epidemic.** Box $6,945,000 less "$1,270,000 post-adoption" = $5,675,000; its 52 rows (pp.63–64) add to $5,825,000. No agency row. | `source_error` (or `needs_info`: which number is right?) |
| 13 | `b8aee6987606` | 125 | 100,000 | Same as #9: Prevent Sexual Assault (PSA) Initiative for Young Adults, Mayor's Office of Criminal Justice, 13-6400434, $100,000. | `accepted_as_printed` |
| 14 | `42f406254687` | 78 | 50,000 | Same as #9: Immigrant Health Initiative, Department of Health and Mental Hygiene, 13-6400434, $50,000. | `accepted_as_printed` |
| 15 | `685f229d5a0b` | 82 | 50,000 | Same as #9: Legal Services for the Working Poor, Department of Social Services, 13-6400434, $50,000. | `accepted_as_printed` |
| 16 | `12c6e02b3ba0`, `a3c03050ef92` | 105, 106 | 0 | The partner list's 13 and 15 EINs are EIN-shaped words with no award row (see #1–#2). | `accepted_as_printed` |

## Values the parse read in a way a person should confirm (6)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 17 | `f180288281ff` | 39 | 372,203 | Coalition for Queens, Inc., 61-1652332: the amount's last digit sits in the 8 pt white column at the table's right edge ("$372,20" \| "3"); read as $372,203. The review row says "a letter … read into the cell" (shared wording); here it is the amount's last digit. The three rows add to the box, $700,000. | `accepted_as_printed` |
| 18 | `ceedcc54ed0f` | 39 | 237,797 | Same: Per Scholas, Inc., $237,797. | `accepted_as_printed` |
| 19 | `4d556072e010` | 39 | 90,000 | Same: New York City Housing Authority, $90,000. | `accepted_as_printed` |
| 20 | `ed8a060b3b0e` | 94 | 0 | **A "*" in the Program cell.** Art as a Catalyst for Change, 2020 Vision for Schools, Inc., Program "Public School / Middle School 183  *": this h-rule table has no "*" column. Kept in the cell as printed; the row carries `W.asterisk`. | `accepted_as_printed` |
| 21 | `70f9bb5337a5` | 94 | 0 | Same: "Public School  / Middle School 42 *". | `accepted_as_printed` |
| 22 | `a64980563c5b` | 94 | 0 | Same: 2020 Vision for Schools, $12,000, Program "*" alone. | `accepted_as_printed` |

## Names that differ between a box and its summary line (15, no money)

Rows carry the **box** title. Suggest `accepted_as_printed` for all.

| review_id | Page | Summary line says | Box says |
|---|---:|---|---|
| `cfb068757f9f` | 45 | Coalition Theaters of Color | Coalition **of** Theaters of Color |
| `b6bea8d7dae2` | 49 | SAVE $2,450,000 | a box of the whole and three part boxes (see #7) |
| `f09a5bec8a33` | 64 | HIV/AIDS Faith Based | HIV/AIDS Faith**-**Based |
| `7e94a6a17e37` | 65 | Reproductive **&** Sexual Health Services | …**and**… |
| `8c1603f0064f` | 67 | CUNY Child Care | CUNY Childcare |
| `e0813fbbb70a` | 74 | Financial Empowerment for NYC Renters | …NYC**'s** Renters |
| `2f95d5a8cec4` | 84 | Fiscal 2019 Subsidy ($2,250,000) | …: Brooklyn Public Library |
| `4cf50c4f39c2` | 84 | Fiscal 2019 Subsidy ($3,500,000) | …: New York Public Library |
| `184c44f65bb3` | 84 | Fiscal 2019 Subsidy ($2,250,000) | …: Queens Borough Public Library |
| `696ff7530363` | 88 | Developmental, Psychological **&** Behavioral Health Services | …**and**… |
| `55aaa3515f67` | 89 | LGBTQ Youth Mental Health | LGBTQ Youth **All-Borough** Mental Health |
| `ebfe89b036c3` | 95 | District Attorneys **OTPS Enhancement** | District Attorneys |
| `a668f24821de` | 97 | Elie Wiesel Holocaust Survivors **Initiative** | drops "Initiative" |
| `e5d8de030e4a` | 100 | Social Adult Day Care **Enhancement** | drops "Enhancement" |
| `6a6a7b044ab4` | 127 | Young Women**'**s Leadership Development | Young Women**’**s … (curly apostrophe) |

## Not in the review file, on purpose

- **304 rows with a "*"** (`W.asterisk`): p.10, "either MOCS or the Council's review process has
  not yet been completed …". Every "*" in the award tables is on a row.
- **902 rows checked by pixel rules only** (`lattice` = `vector+bands`), all in the body. Their
  bands are confirmed by the pixels; their fields are read once.
  *Update 2026-10-24 (#193):* All 902 now have `lattice` = `vector+columns` (`image_check`
  `columns_agree`): the image side finds their columns from the header's labels and the blank
  strips between them, and the text layer, clipped a second time through those cells, gives the
  same value in every field. It is the same text layer, so a text-layer error still passes.
- **5,092 amounts printed with no "$"** (`W.amount_bare`): every row of the member tables
  (Anti-Poverty, Boroughwide Needs, Speaker's Initiative) and of the three appendices.
- **The "Program" column of Art as a Catalyst for Change** (pp.93–94, $720,000), in `purpose`, as
  FY2020–FY2022.
- **21 rows under a header printed loose above the table**, **37 in tables carried over a page
  without a header**, **4 two-band names**, **67 line-end hyphens**, **10 cid glyphs**. Routine
  flags.
- **Health + Hospitals printed with the City's EIN 13-6400434** (Viral Hepatitis Prevention,
  p.66: Bellevue $120,000, Coney Island $53,880, Kings County $53,880). Read as printed; `main`
  used H+H's 13-2655001 from the disclosure.
- **Money with no rows, by design.** $102,483,574 held post-adoption; $38,095,169 designated
  straight to an agency.
- **Disclosure gaps.** 281 PDF rows ($21,209,758) have no disclosure row: 117 amount differs, 104
  EIN not in the disclosure, 28 key already used, 19 City-EIN name mismatch, 13 EIN used up. Every
  row and reason: `data/fy19_sc_disclosure_match.csv`.
