# FY2027 capital and T&C: rows for Noel to review

**Generated:** 2026-10-20 22:16 EDT, from `data/fy27_capital_sd_review.csv` and
`data/fy27_terms_review.csv`. Prepared by BetaNYC with AI assistance.

Sorted by dollars. Page = PDF page (1-based), not the printed "Page N of 57". Nothing here was
"fixed": every value is kept as printed, and the flag says why to look.

**Short version.** Every printed total ties. No dollar amount is in doubt. What's left is
words (sponsor, title, names) and two policy questions.

## A. Capital: decide or confirm (by dollars)

| # | $ (FY2027) | Page | Row | What | Suggested decision |
|---|---:|---|---|---|---|
| 1 | 70,987,000 | 66–67 | 30 `PV MA…` rows on `PV 0N…` lines | In Part II and Part III only. Not in Part I, not in the p.61 "City Council Additions", not in the Council workbook. No sponsor. The Part II total ($210,677,000) includes them. **Evidence (2026-10-20):** in the repo's OMB Capital Budget extract (`source/open-data-46m8-77gv/46m8-77gv.csv.gz`), all 29 `PV 0N…` lines behind these 30 rows appear in the Adopted release (pub_date 20260713) with City funds (`C`) in yr1 FY2027 at exactly the PDF amounts (total $70,987,000); none appears in the Preliminary (20260217) or Executive (20260512) release. So the lines were added at adoption. What `MA` stands for is still unconfirmed | Accept as printed. Ask Council Finance what `MA` / `0N` mean |
| 2 | 23,317,000 | 61 | p.61 "Less Rescindments" | One printed number. No list of rescindments in this book, so only the subtraction ties | Accept; note "unverifiable here" |
| 3 | 10,000,000 | 46 | `HO CC1034` | Sponsor: PDF `SPEAKER, BROOKS-POWERS`; workbook adds `Queens Delegation` | Keep PDF; note the difference |
| 4 | 8,000,000 + 7,000,000 + 3,000,000 | 55, 55, 46 | `PV CC1107`, `PV CC1106`, `HO CC1108` | `, FARIAS` typed into the PDF after export (other font, no accent). Workbook agrees it's Farías | Accept as printed |
| 5 | 5,000,000 | 55 | `PV CC1008` | Sponsor: PDF `SPEAKER, WILLIAMS`; workbook adds `Queens Delegation` | Keep PDF; note |
| 6 | 4,769,000 | 47 / 65 | `HR CC1065` | Part I sponsor `SPEAKER, BANKS, LOUIS, ZHUANG` (`, LOUIS, ZHUANG` added after export). Part II, same row: `SPEAKER, BANKS`. **The PDF disagrees with itself** | Use Part I (the later edit) for sponsor; flag Part II as stale |
| 7 | 4,000,000 | 56 | `PV CC1010` | `, WON` added after export. Workbook also lists `Queens Delegation` | Accept; note |
| 8 | 4,000,000 | 58 / 69 | `PV CC1054` | `, HANIF` added in Part I only; Part II says `SPEAKER, AVILÉS` | As #6 |
| 9 | 3,000,000 | 45 | `HN CC1001` | `, QUEENS DELEGATION` added after export | Accept |
| 10 | 2,500,000 | 56 | `PV CC0989` QUEENS MUSEUM ROOF | **Misprint.** No FY2030 value printed on its line; its sponsor `SPEAKER, THOMAS-HENRY` slid left into the FY2030 column. FY2030 left blank (`None`) | Accept as printed. FY2030 is 0 in every row and total, so no dollar effect |
| 11 | 1,500,000 | 56 | `PV CC1110` NYSF ANSPACHER | Same misprint: a stray `0` printed after its sponsor (`… MANHATTAN DELEGATION 0`). Workbook: `Speaker, Manhattan Delegation` | Accept as printed; it is #10's missing 0 |
| 12 | 1,500,000 | 47 / 65 | `HR CC1059` | `, LOUIS` added in Part I only | As #6 |
| 13 | 1,000,000 | 23 | `E CC0598` | Title: PDF `QUEENS UNITED MIDDLE SCHOOL GYM SUPPLEMENTAL COOLING`; workbook `… SCIENCE LAB UPGRADE`. Same ID, line and amount | **Real difference.** Ask Council Finance which project it is |
| 14 | 1,000,000 | 40 | `HD CC1041` | Title edited after export: PDF `FIFTH AVE COMMITTEE 153 NEVINS STREET`; workbook `FIFTH AVE COMMITTEE - AFFORDABLE HOUSING PROJECT 153 NEVINS STREET` | Accept PDF |
| 15 | 675,000 | 36 | `E CC1245` | Title: PDF `P.S. 370 AUDITORIUM UPGRADE`; workbook `P.S. 199 AUDITORIUM UPGRADE B:K199 S:K199`. **Different school** | **Real difference.** Ask Council Finance |
| 16 | 250,000 | 46 | `HO CC0865` | Sponsor `BANKS` retyped after export (same text) | Accept |
| 17 | — | 13–15, 37, 39, 44, 48, 49, 53 | 34 rows, sponsor `SANCHEZ J.` or `SANCHEZ P.` | Workbook says just `Sanchez`. The PDF tells the two members apart; the workbook does not | Accept PDF; worth a note in `data/capital/` docs |
| 18 | — | 73, 79 | Part III names `ALI FORNAY CENTER, INC.` and `TALLER BORICA/PUERTO RICAN WORKSHOP` | Part I/II titles spell `ALI FORNEY`, `TALLER BORICUA`. Looks like typos in Part III | Accept as printed; note |
| 19 | — | 23 and others | `B:B:Q156 S:S:Q289` | Doubled code prefix, printed so in PDF and workbook. Parser reads the code anyway | None |

## B. Capital: checked, no action needed (FYI)

- **32 two-read disagreements** (pp.34, 40, 45, 46, 47, 55, 56, 58). On these pages someone edited
  the PDF after export, so the text stream is out of order. Every one kept the page-position read,
  and each is confirmed by the Council workbook or is a `0` both rows print.
- **16 rows** where FY2030's `0` sits a little below the row line, and **10 rows** that needed the
  "nearest row" rule (pp.45, 55, 56). All FY2030 values are 0; sponsors match the workbook.
- **Old CSV errors now fixed here** (the retired `data/fy27/capital/` file, not edited): in Part I it missed
  `HD CC0707`, `HD CC0863` (p.40) and merged `HR CC0168` into `HR CC1253`'s title (p.47), which is why
  it showed 24/26; it left
  titles blank where the title sits above the row (p.40); and it named the ID column `budget_line`
  and the budget line `sub_id`.

## C. Terms & Conditions

Nothing has dollars. All checks pass.

| # | Page | What | Suggested decision |
|---|---|---|---|
| 1 | 24–31 | **The retired CSV is wrong for #64–#75** (and, for text only, #30, #33, #39, #57–#59). In 12 multi-agency conditions it kept only the first agency's units, and put the other agencies' headings (and budget-line headings) into the condition text. E.g. #75 lists 16 units; old CSV 5 | Use the new file. Note it in DATA-ANOMALIES |
| 2 | all | Old CSV text has **134 mid-word splits** (`appropriatio n`); new has 0 | Use the new file |
| 3 | 8 | FSR table cells print words split across lines: `Su⏎mmary`, `FY 2⏎028` (3 cells). Kept as printed, joined with a space | Accept as printed |
| 4 | 5, 7, 31 | #13, #14, #75: a line ends in a hyphen (`pre-⏎Kindergarten`), joined with no space, hyphen kept | Accept |

## D. Policy questions (not decided here)

1. Where clean PDF data lives (epic #101, open decision 1). This branch writes to `research/` only.
2. Should the retired `data/fy27/capital/` and `data/fy27/terms/` CSVs be replaced by these, or
   left as history with a pointer?
