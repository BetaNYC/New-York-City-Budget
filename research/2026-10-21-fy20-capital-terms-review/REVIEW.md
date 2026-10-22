# FY2020 capital: rows for Noel to review

**Generated:** 2026-10-22 00:25 EDT, from `data/fy20_capital_sd_review.csv`. Prepared by BetaNYC with AI
assistance.

Critical first, then by dollars. Page = PDF page (1-based). Nothing here was "fixed": every value is
kept as printed. `review_id` is the id in the review CSV.

**Short version.** FY2020 has capital supporting detail only (no T&C in `source/`), and the book is
Part I only. Every printed total ties (24 / 24, the p.80 summary). NYC Open Data `t474-a92g` matches all
1,660 of its amounts; the PDF adds the two t474 lost (`E CN817` $170,000, `E CN832` $300,000). OMB's
adopted release carries $7,353,000 more on 11 lines (report only). **3 critical items**, all the PDF's
own content: three lower-case boroughs.

## A. Critical

| # | $ (FY2020) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 693,000 | 48, 60, 73 | `ca13252e83c6` `78e592d4982c` `e35efec7c1fe` | `F CN003` FDNY 8TH DIVISION VAN $60,000; `HW CN006` ARTHUR KILL ROAD WIDENING $300,000; `PV NC037` CLOVE ENTRANCE DISCOVERY ZONE $333,000 (all BORELLI) | Borough printed in lower case, `r` (t474 and the retired CSV: `R`, Staten Island) | Accept as printed (source_error); a loader may upper-case it for display, never in the file |

## B. Decide or confirm (by dollars)

| # | $ (FY2020) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 46,210,000 | 80 | `e0af50180695` | p.80 "Less: Rescindments from Prior Capital Budgets ($46,210,000)" | One printed number, no list in this book | Accept; "unverifiable here" |
| 2 | 7,353,000 | 2–79 | — | OMB adopted release (2019-07-09) by budget line | 184 / 191 PDF lines equal OMB. OMB is higher on 7 (`E D001` +$2,500,000, `HD D020` +$2,000,000, `HW D102` +$500,000, `P D020` +$450,000, `HW D104` +$250,000, `PV DN031` +$150,000, `PV D467` +$38,000) and has 4 lines with no PDF row (`HL DN843` $1,000,000, `ED DN973` $300,000, `RE D024` $136,000, `PV DN176` $29,000). t474 has no amount the PDF lacks | No change; a note for `data/capital/RECONCILIATION.md` later. Ask Council Finance only if the gap matters for a use |
| 3 | — | 2–79 | 53 `C9.workbook_sponsor` | sponsor wording vs t474 | **29 `AMPREY-SAMUEL`** (the PDF's spelling on 31 rows; t474 and the Council: Ampry-Samuel); 10 where t474 misspells `Ayalya`; 9 caucus written out vs `BLAC`, 3 `STATEN ISLAND DELEGATION` vs `SI Delegation`, 1 t474 `Delgation`, 1 `WOMEN'S CAUCUS` vs t474 `Women's Delegation`. Real differences: **`P CN925`** (p.67, $800,000: PDF Koo, BLAC caucus, Van Bramer; t474 Koo, Van Bramer, Women's Caucus) and **`HN CN034`** (p.57, $250,000: PDF Speaker, Powers, Queens Delegation; t474 Speaker only). `TF CN90` (B5) | Keep the PDF. `AMPREY-SAMUEL` is a source_error: keep as printed, note the correct spelling. `P CN925`, `HN CN034`: ask Council Finance only if sponsor lists matter |
| 4 | 2,500,000 | 68, 71 | `cc0b0b54cb41` | **`P CN967` printed twice**: p.68 `P D019` DPR FOREST PARK ASPHALT PATHWAYS $500,000 (SPEAKER, HOLDEN) and p.71 `PV DN01L` UNIVERSAL HIP HOP MUSEUM $2,000,000 (SPEAKER) | One ID, two lines, two projects. t474 has both, the same way | Accept as printed; a join must use (ID, line) |
| 5 | 400,000 | 79 | `f87b1473381e` | **`TF CN90` printed twice on `TF D005`, $200,000 each**: REAL TIME PASSENGER INFORMATION FOR COUNCIL DISTRICT 11 (SPEAKER, COHEN, borough M) and … SIGNS DOT (SPEAKER, MOYA, Q). Also a two-digit ID number | ID, line and amount are all equal, so C9 compares both PDF rows with one t474 row (one title and one sponsor warning are that artefact). t474 has both rows | Accept as printed; ask Council Finance whether these were meant to be two IDs (needs_info) |
| 6 | 300,000 | 39 | `5185801f4cfe` `76f209026e6e` | `E CN832` P.S. 3 BEDFORD VILLAGE (K003) (K003)GYMNASIUM UPGRADE | t474's row is a broken record with no amount (`row-t24a_8n7r_msc3`). A space typed later in another font sits on top of the letters, so the page shows `(K003)GYMNASIUM` | Accept as printed; a note for `data/capital/` |
| 7 | 170,000 | 39 | `d0eebbc94db5` `75768494492f` `68e67d3cee5f` | `E CN817` MORE ACCESSIBLEBATHROOMS ATPARK WEST HIGH SCHOOL (M535/M542) | t474's row is a broken record with no amount and the title cut at "MORE ACCESSIBLE". The PDF's title cell holds an empty line and two overprinted spaces (the same p.39 edit); config `title_blank_line` joins its two title lines. With both p.39 rows, t474 $700,740,000 + $470,000 = p.80 $701,210,000 | Accept as printed; a note for `data/capital/` |
| 8 | 0 | 71 | — | `PV NC013` BALLET HISPANICO (`PV DN042`, ROSENTHAL) | All four amounts are 0, and it counts in `TOTALS FOR CULTURAL AFFAIRS (126 PROJECTS)`. Not in t474 (t474 lists non-zero amounts) | Accept as printed |
| 9 | — | — | `80b785ba2af7` | t474's FY2020 text | 1 row of mojibake (`FA├çADE`, UTF-8 read as cp437). Decoded for comparing only | Accept; a note for `data/capital/README.md` |

## C. Checked, no action needed (FYI)

- **ID numbers outside the usual shape** (`E CNA02`–`CNA09` p.46, `HL NC02` p.54, `TF CN90` p.79) are rows,
  listed in config; all are in t474 the same way.
- **`HD NC926`** CONCOURSE VILLAGE prints borough `C` (p.53, $3,000,000); t474 has `C` too.
- **17 row flags** (16 "nearest row", 1 sponsor wrapped below the row) (`W.geom_near`,
  `W.sponsor_wrapped_below`, pp.55–78). Values match t474.
- **Typos kept as printed:** `ACQUISTION` (`AG NC902`), `BROOKYN` (`PV NC912`), `EXPANSIO` (`HL NC902`), and
  titles that end in a comma where the export cut them (`E CN063` "(BLDG ID= Q451,").
- **The retired `data/fy20/capital/` CSV** has every amount right but dropped the comma after `SPEAKER`
  on 219 rows, moved wrapped sponsors into titles on 26, and upper-cased the three `r`.

## D. Policy questions (not decided here)

1. Retire or keep the old `data/fy20/capital` CSV? Its amounts are right; 26 sponsors are cut short.
2. How should the explorer show `AMPREY-SAMUEL`, and the lower-case `r`?
3. FY2020 has no T&C in `source/`. Is there one to find?
