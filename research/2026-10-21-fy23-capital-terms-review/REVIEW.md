# FY2023 capital and T&C: rows for Noel to review

**Generated:** 2026-10-21 22:18 EDT, from `data/fy23_capital_sd_review.csv` and
`data/fy23_terms_review.csv`. Prepared by BetaNYC with AI assistance.

Sorted by dollars. Page = PDF page (1-based). Nothing here was "fixed": every value is kept as
printed. `review_id` is the id in the review CSV.

**Short version.** Every printed total ties (32 / 32, the p.71 summary, Part III). NYC Open Data
`t474-a92g` matches all 1,411 of its FY2023 amounts; the PDF adds the one t474 lost to a broken record
(`E CN136`, $150,000). **No critical items** in either queue (40 capital and 15 T&C warnings). The two
things most worth a person's eye are the 15 `RR` rows (A3) and the `E D001` gap against OMB (A5).

## A. Capital: decide or confirm (by dollars)

| # | $ (FY2023) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 179,676,000 | 71 | `8ae1e4bce8aa` | p.71 "Less: Rescindments from Prior Capital Budgets ($179,676,000)" | One printed number, no list in this book; only the subtraction ties ($879,676,000 − $179,676,000 = $700,000,000) | Accept; "unverifiable here" (the Resolution A book holds the list) |
| 2 | 78,861,000 | 73–80 | `1d8e17ac8eac` | 39 `MA` rows on `0N` lines | Part II and Part III only; not in Part I, the p.71 additions or t474. No sponsor. Same kind as FY2024–FY2027 | Accept as printed; ask Council Finance (needs_info) |
| 3 | 22,633,000 | 46–69 | `2943b904ff07` | 15 Part I rows with `RR` IDs | Printed with **no sponsor**; 4 on borough **`A`** (`HA RR001`, `HA RR002`, `HD RR001`, `PO RR001`), a code the Council's dictionary does not define. They are in every total and in t474 (sponsor `NA`). The dictionary calls `RR` "analogous to TA". **Two look like near-twins** of a sponsored row on the same budget line: `HD RR001` "CYPRESS HILLS CHILD CARE ASSOC." $4,280,000 (p.51) beside `HD NC040` "CYPRESS HILLS CHILD CARE CORPORATION" $4,279,000 (p.50, `SPEAKER, NURSE`), both on `HD D020`; and `HA RR002` "SMITH HOUSES" $2,681,000 beside `HA CN001` "SMITH HOUSES FOB PROJECT COMPLETION" $810,000 (p.48, `MARTE`), both on `HA D001`. OMB's adopted `HD D020` and `HA D001` equal the PDF's sums, so both rows of each pair are in the City's budget | Accept as printed; ask Council Finance what `RR` and borough `A` mean, and whether the Cypress Hills pair is one project or two (needs_info). Viewers should not treat a blank sponsor as an error |
| 4 | 21,550,000 (sum) | 54–69 | 6 `C9.workbook_sponsor` | `P CN122`, `HR NC066`, `HO CN017`, `HR NC060`, `PV NC075`, `HR NC059` | t474 shortens "BLACK, LATINO AND ASIAN CAUCUS" to `BLAC`. Amounts and lines match | Keep the PDF |
| 5 | 5,400,000 | 11–46 | — (report only) | budget line `E D001` | PDF Part I sums to $224,446,000; OMB's July 2022 adopted release has $229,846,000; t474 $224,296,000. The PDF closes t474's $150,000 gap (A7); the other $5,400,000 is on OMB's side. The other 129 lines match OMB in FY2023 and FY2024 | No change; a note for `data/capital/RECONCILIATION.md` (FY2023 "1 differ" is now $5,400,000, not $5,550,000) |
| 6 | 315,000 | 49 | `77cb70d1662c` | `HD NC011` 334 EAST 92ND HOUSING DEVELOPMENT FUND | t474 adds "CORP."; the PDF does not print it (ink coverage 0) | Keep the PDF |
| 7 | 150,000 | 11 | `ce2bc7db78b0` `2e3681ee24d2` `22af775af265` | `E CN136` P.S. 28 - AUDITORIUM LIGHTING UPGRADE, `E D001`, ABREU | t474's row is a broken record with no amount (`split_record_amount_unknown`); its fragment `row-fpup_sjfd_kina` carries "B:M028 S:M028", "FY23", 150000. The PDF prints $150,000 and the codes. With it, t474 $879,526,000 + $150,000 = p.71 $879,676,000 | Accept as printed. The PDF settles the broken record; a note for `data/capital/` (not edited here) |
| 8 | — | — | `105afded4e87` | t474's FY2023 text | 74 rows print accents as mojibake: UTF-8 read as cp437 (`Avil├⌐s` = Avilés, `Cab├ín` = Cabán). Decoded for comparing only | Accept; a note for `data/capital/README.md` |

## B. Capital: checked, no action needed (FYI)

- **Reused ID numbers.** `HD NC040` and `HR NC040` share `HD D020`; `HA CN001` and `P CN001` share
  `HA D001` (pp.48, 50, 51). The full IDs differ; each matches its own t474 row by amount. Any join that
  drops the agency prefix must also use the amount (the crosswalk's unique keys do).
- **The cover's City seal** (two images, p.1) was the only uncovered ink; config counts it as covered.
- **8 rows** needed the "nearest row" rule and **2** a sponsor wrapped below the row (`ff6b24c37e8d`,
  `a35af639a950`, `ec62e89c3526`, `71895c143104`, `e2e09ca11ccc`, `ce031ef32afc`, `18a59469b4fb`,
  `a81025a1db8d`, `19c4ba7f3fb5`, `ed18e361dfd3`: pp.54–80). Values match the other Part and t474
  (except `HR NC066`'s `BLAC`, A4).
- **Part III hairlines** (`969bfd99c859`): 89 rules of 0.12 pt, too thin for 300 dpi.
- **15 RR sponsors** (`C9.workbook_sponsor`, PDF blank vs t474 `NA`): covered by A3.
- **Codes kept in titles.** Codes that are not a letter and three digits stay in `title` as printed
  (`S:03M075`, `/M063`, `B:N/A`, `B: S:`); `title_raw` always has the whole cell.
- **The retired `data/fy23/capital/` CSV** dropped the printed comma after `SPEAKER` on 265 rows and
  moved a wrapped sponsor line into the title on 10. Every amount and borough agrees.

## C. Terms & Conditions

No dollars. All 15 items are warnings.

| # | Page | review_id | What | Suggested decision |
|---|---|---|---|---|
| 1 | 2–19 | — | **The PDF prints no condition numbers.** `item_number` here is the order in the book (1..60), as the retired CSV numbered them. T1 checks it: 60 headings, 60 "As a condition" paragraphs | Accept; say so wherever `item_number` is shown for FY2023 |
| 2 | 2, 3, 9, 10, 12, 14 | `3e41521cbb15` `d96bec3a28ea` `8f7b0fa9c92d` `61d2a4bef758` `ce533845f48a` `d93b0cdb6112` `adefd52eca53` `d9b3b76eb960` `6d26ae390012` | **The retired CSV vs the new file.** Same 60 conditions and agencies. The old file put the capital budget lines into `units` (#3, #4, #5, #35), the FSR table into #24's text, and dropped printed hyphens and dashes (#28 "per day - for", #34 `low-barrier`, #35 `HD-0009`, #43 `self-placement`) | Use the new file |
| 3 | 12, 16 | `17b10c274754` `96eaff94146b` | #35: the budget line wraps across a line end (`HD-` / `0009`) and T3 reads it with a space (a limit of the check; the text is right). #49: "units of appropriations 311 and 312" (plural), which T3 does not read | Accept |
| 4 | 12–17 | `298e5afd2811` `f5bbc61b56ec` `b80e0d5bbe8b` `a6126bef1caa` | A line ends in a hyphen and joins with none (`low-` / `barrier`, `HD-` / `0009`, `self-` / `placement`) | Accept |

## D. Policy questions (not decided here)

1. Retire or keep the old `data/fy23/capital|terms` CSVs? Their amounts and conditions agree; the
   capital one has lost 265 commas.
2. FY2023 T&C numbers are ours, not the PDF's, as for FY2024. Should the explorer show "#24" for FY2023?
3. Should the RR series (A3) be labelled in the explorer ("technical adjustment, no sponsor printed")?
