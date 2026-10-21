# FY2026 Schedule C: what a person needs to check

**Report generated:** 2026-10-21 00:45 EDT. Source: `data/fy26_sc_review.csv` (28 rows),
sorted by how much money each could touch. Write each decision into
`data/fy26_sc_review_decisions.csv` by `review_id` (`source_error`, `parser_bug`,
`accepted_as_printed` or `needs_info`), with the columns of the FY2027 file
(`review_id,decision,note,decided_by,decided_at`). Nothing here changes a total.
"Suggest" is the conservative call; the decision is Noel's.

## Rows that could change a value (17)

| # | review_id | Page | $ | What | What we did / suggest |
|---:|---|---:|---:|---|---|
| 1 | `3c76fd1e62f3` | 48 | 417,203 | **Only one grid sees this row.** Pursuit Transformation Company, 61-1652332, $417,203: one row carried over from p.47's table with no header. Its table is one row tall, shorter than the image grid's 60 px rule detector, so the image side finds no table there. | Read with p.47's header (flag `W.headerless_table`). The EIN census and ink coverage do cover it. Crop: `data/overlays/p048-0.png`. Suggest `accepted_as_printed`. |
| 2 | `072b76ac2954` | 157 | 98,469 | Same as #1: Tell Every Amazing Lady About Ovarian Cancer Foundation, 26-4417161, $98,469, carried over from p.156 (Cancer Services). | Same. Crop `p157-0.png`. Suggest `accepted_as_printed`. |
| 3 | `6664767f0cae` | 242 | 100,000 | **Line-end hyphen.** Department of Education – "Community School District 28-" then "MBK/MSK". | Kept as printed: `…District 28-MBK/MSK`. Is it "28 - MBK/MSK"? Suggest `accepted_as_printed`. |
| 4 | `c0ca776b10e9` | 111 | 75,000 | **Amount printed without "$"**: Ghetto Film School, Inc., 13-4127229, "75,000". It is the initiative's only row and equals its $75,000 box. | Read as 75,000, flagged. Suggest `accepted_as_printed`. |
| 5 | `94ae97242c0b` | 158 | 27,348 | **8-digit EIN**: Brooklyn Center for Quality Life, printed "26-265183". | Clean EIN left blank; printed value kept; named exception. Suggest `source_error`. |
| 6 | `9937d66ba686` | 45 | 25,000 | **Line-end hyphen before "Council District"**: NYC First, Inc. "…STEM Programs-" / "Council District 10". | Kept as printed: `…Programs-Council District 10`. Suggest `accepted_as_printed` (as FY2027 #2). |
| 7 | `1ba072f0ec08` | 77 | 20,000 | **Line-end hyphen**: CUNY – Queens College "Foundation-" / "Kupferberg Center for the Arts" (JHS 210Q). | Kept as printed: `Foundation-Kupferberg`. Suggest `accepted_as_printed`. |
| 8 | `27f7098256d9` | 77 | 20,000 | Same as #7 (Robert H. Goddard HS). | Same. |
| 9 | `a4f483f8851e` | 212 | 20,000 | Line-end hyphen before "Council District": Parks – "Movie Nights-" / "Council District 32". | Kept as printed. Suggest `accepted_as_printed`. |
| 10 | `5c57e0993df3` | 421 | 20,000 | **The two grids disagree on one cell edge.** Victory Music and Dance Company, Mealy, $20,000: the name line "…Oldtimers Week -" ends in a hyphen that pokes past the border into the EIN box. The vector grid keeps it with the name (right, on the page); the image grid puts it with the EIN. | EIN `472167056` (both grids agree on the digits). Crop `p421-0.png`. Suggest `accepted_as_printed`. |
| 11 | `818c8efb9455` | 213 | 15,000 | Line-end hyphen: Parks – "Rockaway Events-" / "Flag Day & Fall Festival". | Kept as printed: `Events-Flag Day`. Suggest `accepted_as_printed`. |
| 12 | `b584161694fe` | 213 | 15,000 | Line-end hyphen: Parks – "Tudor Park Event-" / "council District 32" (lower-case c as printed). | Kept as printed. Suggest `accepted_as_printed`. |
| 13 | `239a56d3a7b0` | 344 | 10,000 | Same as #10: Parks – "Archie Spigner Park -" / "Spring Egg Hunt", Williams, $10,000. | EIN `136400434`. Crop `p344-0.png`. Suggest `accepted_as_printed`. |
| 14 | `205216c81be1` | 379 | 5,000 | **8-digit EIN**: Morris Heights Health Center, Inc., printed "61081232". | As #5. Suggest `source_error`. |

## The PDF disagrees with itself (3)

| # | review_id | Page | $ | What | Suggest |
|---:|---|---:|---:|---|---|
| 15 | `3c166360f764` | 98 | 15,000 | **Cultural Immigrant Initiative.** "will designate $597,000 post-adoption and has designated $6,798,000"; $597,000 + $6,798,000 = the $7,395,000 box. The 383 rows printed under it (pp.99–111) add to **$6,783,000**. Every one of those pages has as many rows as EIN words, and the image grid agrees with every row. | `source_error`. Not fixed; named exception. |
| 16 | `d46489c09362` | 173 | 800 | **Immigrant Services TOTAL.** Printed $86,091,341; its 8 lines add to $86,092,141 (read off the page image, 2026-10-21). | `source_error`. |
| 17 | `b3a44442119b` | — | 14,200 | The roll-up: category TOTALs $665,080,021 vs rows + reserves + direct pots $665,065,821. Exactly #15 and #16 (−$15,000 + $800). | `source_error`, follows from #15 and #16. |

## Names that differ between a box and its summary line (11, no money)

The amounts agree. Rows carry the **box** title. These matter for comparing initiatives across
years by name. Suggest `accepted_as_printed` for all eleven.

| review_id | Page | Summary line says | Box says |
|---|---:|---|---|
| `6a638deac498` | 47 | Diversity, Inclusion **and** Equity in Tech Initiative | …Inclusion **&** Equity… |
| `7e804857cd66` | 126 | Supportive Alternatives to Violent Encounters (SAVE) $2,450,000 | **three** SAVE boxes: $1,275,000 + $600,000 + $575,000 |
| `725050558d24` | 129 | Educational Programs for Students (Formerly – … for Students | the same with the closing **)** |
| `1627668768c9` | 160 | Reproductive **&** Sexual Health Services | …**and**… |
| `1fdc4cfb83e2` | 163 | CUNY Research **Institute** | …**Institutes** |
| `d7e15277029d` | 170 | Financial Empowerment for NYC Renters | …NYC**'s** Renters |
| `44ce15605701` | 178 | Legal Services for Low-Income and Working-Class New Yorkers (**F**ormerly …) | (**f**ormerly …) |
| `90633378be3d` | 183 | Developmental, Psychological **&** Behavioral Health Services | …**and**… |
| `cc1ddc891f8b` | 184 | LGBTQIA+ Youth Mental Health | adds "(Formerly LGBTQ Youth Mental Health)" |
| `fce75be02b84` | 187 | Older Adults Mental Health (Formerly Geriatric **Older Adults**) | (Formerly Geriatric **Mental Health**) |
| `fc84c7565f29` | 217 | Violence Prevention and Intervention for Youth and Young Adults | adds "(Formerly Art a Catalyst for Change and Crisis Management System)" |

## Not in the review file, on purpose

- **85 line-end hyphens** in names and purposes. Each was read by hand from `fy26_sc_flags.csv`:
  78 are compound words (`low-⏎income`, `Anti-⏎Violence`, `(Bedford-⏎Stuyvesant)`) and keep the
  hyphen; the other 7 are #3, #6–#9, #11, #12 above. Flag `W5.wrap_hyphen` on the row.
- **8 two-band names** and 1 empty sliver band (p.48) (`W.continuation_row`, e.g. p.130 "…Washington Heights" / "and Inwood")
  and **6 headerless carry-over rows** (`W.headerless_table`, pp.48, 157, 195). The image grid
  read the 8 joined names and the 4 rows on p.195 the same way, independently.
- **6 unmapped glyphs** (`(cid:9)`, 5 rows, e.g. p.344 "District 36.") drawn as an empty box.
  Raw keeps them; the clean value drops them (`W.cid_glyph`).
- **Money with no rows, by design.** 14 initiatives say "will designate awards post-adoption"
  ($78,512,162). 8 CUNY/DOE initiatives say "designated directly to the City University of New
  York" and print no rows ($23,911,869; pp.162–164; Vallone's statement splits its $16,411,869
  as $15,753,469 CUNY + $658,400 DOE, which adds up). These amounts are in the initiatives table,
  not in any award row.
- **Disclosure gaps.** The disclosure is a later snapshot (it includes transparency-resolution
  changes), so gaps are coverage, not errors. 255 PDF rows ($21,432,686) have no disclosure row:
  110 amount differs, 64 key already used, 45 EIN not in the disclosure, 15 EIN used up, 19
  City-EIN name mismatch, 2 unreadable EIN. 2,254 disclosure rows have no PDF row: 2,101 amount
  or count differs ($167,158,514), 148 EIN not in the PDF, 5 City-EIN Pending. Every row and
  reason: `data/fy26_sc_disclosure_match.csv`.
