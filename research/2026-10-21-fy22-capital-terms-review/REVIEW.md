# FY2022 capital and T&C: rows for Noel to review

**Generated:** 2026-10-21 22:50 EDT, from `data/fy22_capital_sd_review.csv` and
`data/fy22_terms_review.csv`. Prepared by BetaNYC with AI assistance.

Critical first, then by dollars. Page = PDF page (1-based). Nothing here was "fixed": every value is
kept as printed. `review_id` is the id in the review CSV.

**Short version.** Every printed total ties (34 / 34, the p.72 summary, Part III). NYC Open Data
`t474-a92g` matches all 1,490 of its FY2022 amounts; the PDF adds the one t474 lost (`E CN673`,
$55,000), and all 149 PDF budget lines equal OMB's adopted release. **33 critical capital items**, all
the PDF's own content: 4 Borough President rows in Part II only, 28 sponsor cells naming a vacant
district, 1 lower-case borough. The T&C has no critical items; the retired T&C CSV is misaligned at
conditions 26–28.

## A. Capital: critical

| # | $ (FY2022) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 3,479,000 (net) | 75, 82 | `da1ad2bc0307` `bc340f5d743d` `e41187db0bd7` `351ce4515a42` | `PW KBP01` SAINT FRANCIS COLLEGE $1,551,000 (`PW KN497`); `HL KBP01` BROOKLYN PLAZA MEDICAL CENTER $1,000,000 (`HL KN04A`); `PW KBP02` CAMPAIGN AGAINST HUNGER $1,000,000 (`PW KN03G`); **`PW MBP01` EARTH MATTER NY −$72,000** (`PW MN03W`) | Part II only, no sponsor, on `KN` / `MN` lines (Brooklyn and Manhattan, by the letters; likely Borough President money, unconfirmed). Not in Part I or t474; in the Part II total and Part III (p.86 prints EARTH MATTER's total as `($72,000)`). `MBP01` is negative | Accept as printed; ask Council Finance what `KBP` / `MBP` and `KN` / `MN` are, with the `MA` question (needs_info). Viewers must allow negative amounts |
| 2 | — | 17–82 | the 28 `C6.sponsor_digit` rows | `CD 22` on 10 rows (e.g. `E CN270`–`E CN272` p.17, `HN CN030` p.54), `CD 48` on 18 (e.g. `E CN884`–`E CN895` p.43, `PW NC078`, `PW NC079` p.70) | The sponsor cell names a council district, not a member. t474 writes `Vacant 22` and `Vacant 48` (and `Vacant 23` for `E CN271`, a t474 typo: the PDF prints `CD 22`). Amounts match | Accept as printed (accepted_as_printed); do not fill a member's name. A note for the explorer: "district seat, no member" |
| 3 | 1,000,000 | 60 | `5bcbe970615b` `bde48836df34` | `P CN039` on `P D021` | Borough printed in lower case, `x` (t474: `X`, the Bronx) | Accept as printed (source_error); a loader may upper-case it for display, never in the file |

## B. Capital: decide or confirm (by dollars)

| # | $ (FY2022) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 44,442,000 | 74–82 | `27d98cd2c1f9` | 25 `MA` rows on `0N` lines | Part II and Part III only; not in Part I, the p.72 additions or t474. No sponsor. Same kind as FY2023–FY2027 | Accept as printed; ask Council Finance (needs_info) |
| 2 | 29,495,000 | 72 | `492c5a1caa88` | p.72 "Less: Rescindments from Prior Capital Budgets ($29,495,000)" | One printed number, no list in this book | Accept; "unverifiable here" |
| 3 | — | 4–70 | 97 `C9.workbook_sponsor` | sponsor wording vs t474 | After decoding t474's mojibake: **25 `AMPREY-SAMUEL`** (the PDF's spelling; t474 and the Council spell it Ampry-Samuel); 22 `CD nn` vs `Vacant nn` (A2); 19 `DIAZ` vs t474 `Diaz (D)`; 13 `TA` rows with no sponsor vs `Technical Adjustments`; 2 `TECHNICAL ADJUSTMENTS` vs singular; 5 caucus written out vs `BLAC`; 8 where only one side lists the Speaker (5 PDF, 3 t474); `PV NC090` (t474 drops a comma); `PW CN072` (the PDF lists Grodenchik and Koslowitz, t474 Vacant 22 and the Manhattan Delegation); `E CN884` (B6) | Keep the PDF. `AMPREY-SAMUEL` is a source_error: keep as printed, note the correct spelling. `PW CN072` and the Speaker differences: ask Council Finance only if sponsor lists matter for a use |
| 4 | 13,394,000 | 4–70 | `038c3dd9f65a` | 15 Part I `TA` rows (`AG TANC1`, `E TA001`–`TA003`, `L TA001`, `P TA001`–`TA005`, `P TANC1`, `PO TA001`, `PW TANC1`–`TANC3`) | All borough `A`; 13 print no sponsor, 2 print a member plus `TECHNICAL ADJUSTMENTS`. In every total and in t474. The Council's dictionary: TA = Technical Adjustment | Accept as printed |
| 5 | 2,600,000 | 58 | `62919a1021c7` | `E CN274` DPR WOODTREE PLAYGROUND BASKETBALL (`P D019`, `CD 22`) | t474 adds "COURTS" | Keep the PDF |
| 6 | 1,550,000 | 43, 68–69 | `59e2eb49f84a` `4364e45c23ae` `6e210c7c1743` | **`E CN884` printed twice on `E D001`, $500,000 each**: "811K TECHNOLOGY" (`CD 48`) and "NYC PUBLIC SCHOOL 97 BRONX - SCHOOLYARD" (`SPEAKER, GJONAJ`); `PV NC101` on `PV D235` (Brooklyn Museum, $1,250,000) and `PW DN725` (BronxWorks, $300,000) | Two projects share one ID. For `E CN884` the ID, line and amount are all equal, so C9 compares both PDF rows with one t474 row (one title and one sponsor warning are that artefact). Every amount is matched | Accept as printed; any join on (ID, line, amount) must allow two rows. Ask Council Finance whether `E CN884` should have been two IDs (needs_info) |
| 7 | 350,000 | 49 | `1476c315c5b3` | `HD NC032` FIFTH AVENUE CCOMMITTEE | The PDF's typo; t474 spells it right | Accept as printed (source_error) |
| 8 | 55,000 | 34 | `4545e1886ad8` `c08473c0402f` `ee64abe785c1` | `E CN673` BRONX THEATRE HIGH SCHOOL, `E D001` | t474's row is a broken record with no amount; its fragment `row-y68w-ar36-igcc` carries 55000, "FY22" and the codes the PDF prints. With it, t474 $704,440,000 + $55,000 = p.72 $704,495,000 | Accept as printed; a note for `data/capital/` |
| 9 | — | — | `e96770906545` | t474's FY2022 text | 32 rows of accents and no-break spaces as mojibake (UTF-8 read as cp437, `┬á`). Decoded for comparing only | Accept; a note for `data/capital/README.md` |

## C. Capital: checked, no action needed (FYI)

- **OMB:** all 149 PDF budget lines equal OMB's adopted release (2021-07-16) in FY2022 and FY2023. OMB
  also has `LB D109` ($2,214,000) with no Council row anywhere; not a PDF question.
- **17 row flags** (13 "nearest row", 4 sponsor wrapped below the row) (`W.geom_near`,
  `W.sponsor_wrapped_below`: pp.33–82). Values match the other Part and t474.
- **Part III hairlines** (`38a5739f5d65`): 99 rules too thin for 300 dpi.
- **The cover's City seal** is counted as covered ink by config, as FY2023.
- **The retired `data/fy22/capital/` CSV** has every amount right but dropped the comma after `SPEAKER`
  on 236 rows, moved wrapped sponsors into titles on 21, and upper-cased `P CN039`'s `x`.

## D. Terms & Conditions

No dollars. All 26 items are warnings.

| # | Page | review_id | What | Suggested decision |
|---|---|---|---|---|
| 1 | 2–18 | — | **No condition numbers and no page numbers.** `item_number` is the order in the book (1..50). T1 checks it: 50 headings, 50 "As a condition" paragraphs | Accept; say so wherever `item_number` is shown for FY2022 |
| 2 | 10 | `819622aa4546` | **#26 `Department of Education (40)`**: a two-digit code. Kept in the name; `agency_code` blank; units read as `:401`, `:402` | Accept as printed (source_error). Do not pad to 040 in the file; a loader may treat it as DOE |
| 3 | 11 | `924353311887` | #28 names ten agencies; **HPD prints no code** (unit 012) | Accept as printed |
| 4 | 10–11 | `6fff6baee87b` `73210662cb57` `32342163824d` `e92f4da931aa` `091f83e3ce8d` `d7e66c14cbf4` `2ce23841b1e5` `1e4cffe2b96f` | **The retired CSV is misaligned at #26–#28**: it lost #26 (folded into #25) and split #28 into two rows, so the counts still read 50 | Use the new file. Note it in DATA-ANOMALIES |
| 5 | 2, 3, 5, 8, 10, 13, 14 | `ee81410cc36f` `5d39069d9b31` `1c6bc612978d` `0b37aebfdbcd` `56161b411c13` `fa4ae69a2216` `e531b1cfd0e0` `fa856ab5fb36` `ccf737ab4b71` `24716725f905` | The retired CSV also put capital budget lines into `units` (#3, #4, #5, #14, #33), the FSR table into #21's text, and dropped printed hyphens and dashes (#14 `non-functioning`, #25 "per day - for", #33 `HD-0009`, #38 `self-placement`) | Use the new file |
| 6 | 5, 13 | `8ab721c74138` `b652b09c6bda` | T3: #14 names "E2364 and E2365" with no hyphen; #33 wraps `HD-` / `0009`. The check's limits; the texts are right | Accept |
| 7 | 5–16 | `bb792c09e95d` `44f5a24c108d` `41bd338dc406` `d25e844cbc47` | A line ends in a hyphen and joins with none | Accept |
| 8 | 8–9 | — | **The FSR table's months are out of order as printed**: SEPTEMBER 2022, OCTOBER 2022, DECEMBER 2022, FEBRUARY 2022, MARCH 2021, MAY 2022 (the FY2022 schedule should run September 2021 to May 2022). Kept as printed | Accept as printed (source_error); do not correct the years |

## E. Policy questions (not decided here)

1. Retire or keep the old `data/fy22/capital|terms` CSVs? The terms one is misaligned at #26–#28.
2. How should the explorer show a sponsor of `CD 22` / `CD 48`, and the misspelled `AMPREY-SAMUEL`?
3. Are the `KBP` / `MBP` rows Council money at all? If not, should they be labelled apart from the
   Council's additions, as the `MA` series is?
