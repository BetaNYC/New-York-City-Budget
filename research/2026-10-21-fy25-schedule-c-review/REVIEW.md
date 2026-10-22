# FY2025 Schedule C: what a person needs to check

**Report generated:** 2026-10-21 19:20 EDT. Source: `data/fy25_sc_review.csv` (39 rows),
sorted by how much money each could touch. Write each decision into
`data/fy25_sc_review_decisions.csv` by `review_id` (`source_error`, `parser_bug`,
`accepted_as_printed` or `needs_info`), with the columns of the FY2026 file
(`review_id,decision,note,decided_by,decided_at`). Nothing here changes a total.
"Suggest" is the conservative call; the decision is Noel's.

## The two critical rows

| # | review_id | Page | $ | What | What we did / suggest |
|---:|---|---:|---:|---|---|
| 1 | `905ac4e21fd6` | 407 | 20,000 | **The two grids disagree on one cell edge.** Victory Music and Dance Company, Mealy, $20,000: the name line "…Oldtimers Week -" ends in a hyphen that pokes past the border into the EIN box. The vector grid keeps it with the name (right, on the page); the image grid puts it with the EIN. The same row was FY2026 #10. | EIN `472167056` (both grids agree on the digits). Crop `data/overlays/p407-0.png`. Suggest `accepted_as_printed`. |
| 2 | `aeba2de31691` | 334 | 10,000 | Same as #1: Parks – "Archie Spigner Park -" / "Spring EggHunt", Williams, $10,000 (FY2026 #13). | EIN `136400434`. Crop `p334-0.png`. Suggest `accepted_as_printed`. |

## The PDF disagrees with itself (9)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 3 | `216731fd545f` | 222 | 2,749,000 | **Pride at Work.** The statement says "will designate $50,000 post-adoption and has designated **$3.2 million**". The box is **$501,000**; its 5 rows add to $451,000, and $50,000 + $451,000 = $501,000. The "$3.2 million" belongs to no part of this initiative. Read off the page. | `source_error`. Rows and box are right; the statement is wrong. |
| 4 | `95efc19212e4` | 222 | 2,749,000 | The same statement's check that reserve + designated = box ($50,000 + $3,200,000 ≠ $501,000). | `source_error`, follows from #3. |
| 5 | `b461712d068d` | 64 | 594,000 | **Cultural After-School Adventure (CASA).** "will designate $2,066,000 post-adoption and has designated $14,680,000" = $16,746,000; the box and its summary line (p.63) say **$17,340,000**. The rows add to $14,680,000, as the statement says. | `source_error`. The $594,000 is in no row and no stated reserve. |
| 6 | `2a7b9021166b` | — | 571,000 | The roll-up: category TOTALs $540,282,182 vs rows + reserves + direct pots $539,711,182. Exactly #5, #8 and #9 (−$594,000 − $27,000 + $50,000). | `source_error`, follows from #5, #8, #9. |
| 7 | `1ae5bdec45d3` | 115 | 50,000 | **Education TOTAL.** Printed $39,924,300; its 12 lines add to **$39,974,300** (added by hand from the page image, 2026-10-21). | `source_error`. |
| 8 | `42591594f78a` | 167 | 27,000 | **Immigrant Opportunities Initiative.** "will designate $38,000 post-adoption and has designated $2,562,000" (= the $2,600,000 box); the 31 rows printed under it (pp.167–168) add to **$2,535,000**. Both pages have as many rows as EIN words, and the image grid agrees with every row. | `source_error`. Not fixed; named exception. |
| 9 | `542f8982f47a` | 60 | 9,000 | **Initiative to Combat Sexual Assault.** "has designated **$4.1 million**"; the 16 rows add to $4,091,000, and $69,000 + $4,091,000 = the $4,160,000 box. The statement rounds. | `accepted_as_printed` (a rounded figure, not an error). |
| 10 | `e6438d55595b` | 60 | 9,000 | The same rounding seen by the reserve + designated check. | Same as #9. |
| 11 | `4688526d8c78` | 202 | 0 | **Parks and Recreation Services prints no summary table and no TOTAL.** Its one box, Parks Equity Initiative $5,368,500, stands in for the TOTAL in the roll-up. Known going in (PLAN §10). | `accepted_as_printed`. |

## Rows where we read an odd print (8)

| # | review_id | Page | $ | What | What we did / suggest |
|---:|---|---:|---:|---|---|
| 12 | `059e90065dc6` | 157 | 500,000 | **Box amount in three cells**: CUNY Social Work Fellows, "$" \| "5" \| "00,000" (phantom column rules). The page shows $500,000; the summary line (p.155) says $500,000. | Read as $500,000. Suggest `accepted_as_printed`. |
| 13 | `afeeb831053e` | 260 | 250,000 | **Box amount's last digit past the table edge**: HRA Teen RAPP "$250,00" + "0". The page shows $250,000; summary (p.260) says $250,000; its one row says $250,000. | Read as $250,000. Suggest `accepted_as_printed`. |
| 14 | `db0f3555cba2` | 222 | 200,000 | **Amount's last digit in a phantom column**: Destination Tomorrow, Inc., "$200,00" \| "0". The page shows $200,000 (crop looked at). | Read as $200,000. Suggest `accepted_as_printed`. |
| 15 | `f3abe7c98bb6` | 222 | 100,000 | Same: Non-Traditional Employment for Women, $100,000. | Same. |
| 16 | `42975706d090` | 222 | 61,000 | Same: Pathways To Apprenticeship, $61,000. | Same. |
| 17 | `0b8b3b5578d8` | 222 | 50,000 | Same: Pathways To Apprenticeship, $50,000. | Same. |
| 18 | `cc0902d7384c` | 222 | 40,000 | Same: Leap, Inc., $40,000. | Same. |
| 19 | `ea10460875ca` | 168 | 77,000 | **Amount with cents**: Haitian Americans United for Progress, Inc., "$77,000.00". | Read as $77,000. Suggest `accepted_as_printed`. |
| 20 | `1ee14a219ab4` | 170 | 50,000 | **Amount with a trailing period**: Northern Manhattan Improvement Corporation, "$50,000.". | Read as $50,000. Suggest `accepted_as_printed`. |

## EIN and names (3)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 21 | `20b22fe61d13` | 181 | 150,000 | **Malformed EIN**: Safe Horizon, Inc., printed "13-294-6970" (two hyphens; the digits are Safe Horizon's EIN 13-2946970 elsewhere in the PDF and the disclosure). | Clean EIN left blank; printed value kept; named exception. Suggest `source_error`. |
| 22 | `88e958b70648` | 71 | 20,000 | **Line-end hyphen**: CUNY – Queens College "Foundation-" / "Kupferberg Center for the Arts". | Kept as printed: `Foundation-Kupferberg`. Suggest `accepted_as_printed` (as FY2026). |
| 23 | `ca560847e521` | 71 | 20,000 | Same as #22, next row. | Same. |

## Names that differ between a box and its summary line (16, no money)

The amounts agree. Rows carry the **box** title. These matter for comparing initiatives across
years by name. Suggest `accepted_as_printed` for all sixteen.

| review_id | Page | Summary line says | Box says |
|---|---:|---|---|
| `d2185d52eee6` | 42 | Diversity, Inclusion and Equity in Tech **Initiative** | drops "Initiative" |
| `e7afc0c2b7d6` | 59 | Alternatives to Incarceration **(ATI)** | **(ATIs)** |
| `2de1356a794c` | 114 | Supportive Alternatives to Violent Encounters (SAVE) $2,450,000 | **two** SAVE boxes: $1,850,000 + $600,000 |
| `270e78291f32` | 153 | Reproductive **&** Sexual Health Services | …**and**… |
| `f883f940964d` | 155 | Creative Arts Team **(CUNY CAT)** | Creative Arts Team |
| `96b68da612de` | 156 | CUNY Research **Institute** | …**Institutes** |
| `6f5e9285ae0c` | 156 | CUNY School of Labor and Urban Studies | adds "(SLU)" |
| `ec230d5d032b` | 163 | Financial Empowerment for NYC Renters | …NYC**'s** Renters |
| `6434f450c0f6` | 174 | Fiscal 2025 Subsidy (agency BPL) | Fiscal 2025 Subsidy: Brooklyn Public Library |
| `7d105b3b097c` | 174 | Fiscal 2025 Subsidy (agency NYPL) | …: New York Public Library |
| `6e5edb75ba1d` | 174 | Fiscal 2025 Subsidy (agency QBPL) | …: Queens Borough Public Library |
| `a36b7775ac88` | 174 | Fiscal 2025 Subsidy (agency (NYPL-R) Research) | …: Research Library |
| `97fe354d628a` | 178 | Developmental, Psychological **&** Behavioral Health Services | …**and**… |
| `d80ef1d7535b` | 179 | LGBTQIA+ Youth Mental Health | adds "(formerly LGBTQ Youth Mental Health)" |
| `d93963e854bc` | 181 | Older Adults Mental Health (formerly Geriatric **Older Adults**) | (formerly Geriatric **Mental Health**) |
| `ef26066f88e0` | 212 | Hate Crimes Prevention **Initiative** | drops "Initiative" |

## Not in the review file, on purpose

- **67 line-end hyphens** in names and purposes. Each was read by hand from `fy25_sc_flags.csv`:
  65 are compound words (`low-⏎income`, `Anti-⏎Violence`, `(Bedford-⏎Stuyvesant)`,
  `Woodhaven-⏎Richmond`) and keep the hyphen; the other 2 are #22 and #23. Flag `W5.wrap_hyphen`.
- **16 two-band names** (`W.continuation_row`, e.g. p.117 "…Washington Heights and" / "Inwood",
  p.211 "…Madiba Prep School" / "(MS681)"). The image grid read all 16 the same way, on its own.
- **2 names left of their header's centre** (p.183, `W.header_span_cell`: Astor Services for
  Children & Families $673,888, Rising Ground, Inc. $800,000). The image grid read both the
  same way, on its own.
- **6 unmapped glyphs** (`(cid:9)`, 6 rows, e.g. p.312 "Council District 30") drawn as an empty
  box. Raw keeps them; the clean value drops them (`W.cid_glyph`).
- **Box titles whose first letter is drawn apart** (pp.36, 149, 258 ×2). Put back; each title
  then equals its summary line, which is the check.
- **Money with no rows, by design.** 16 initiatives say "will designate awards post-adoption"
  ($50,455,000). 7 CUNY/DOE initiatives are "designated directly" and print no rows (pp.155–157,
  $20,011,869; Vallone's statement splits its $16,411,869 as $15,753,469 CUNY + $658,400 DOE, which adds up).
  The four library subsidies (p.174, $15,700,000) are "directly allocated" to each library.
  These amounts are in the initiatives table, not in any award row.
- **Disclosure gaps.** The disclosure is a later snapshot (it includes transparency-resolution
  changes), so gaps are coverage, not errors. 211 PDF rows ($7,348,995) have no disclosure row:
  55 key already used, 51 amount differs, 43 EIN not in the disclosure, 33 EIN used up, 28
  City-EIN name mismatch, 1 unreadable EIN (#21). 1,908 disclosure rows have no PDF row: 1,813
  amount or count differs ($123,219,047), 84 EIN not in the PDF, 11 City-EIN Pending. Every row
  and reason: `data/fy25_sc_disclosure_match.csv`.
