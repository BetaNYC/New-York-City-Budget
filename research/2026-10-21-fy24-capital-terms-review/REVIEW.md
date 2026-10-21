# FY2024 capital and T&C: rows for Noel to review

**Generated:** 2026-10-21 19:20 EDT, from `data/fy24_capital_sd_review.csv` and
`data/fy24_terms_review.csv`. Prepared by BetaNYC with AI assistance.

Sorted by dollars. Page = PDF page (1-based). Nothing here was "fixed": every value is kept as
printed. `review_id` is the id in the review CSV.

**Short version.** Every printed total ties (32 / 32, the p.61 summary, Part III). NYC Open Data
`t474-a92g` matches all 1,241 Part I amounts, none left over. One critical capital row (a negative
Part II-only row). The T&C prints no condition numbers; this parse numbers them in book order and finds
61, where the retired CSV had 59.

## A. Capital: decide or confirm (by dollars)

| # | $ (FY2024) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 189,969,000 | 61 | `72e493cebf2b` | p.61 "Less: Rescindments from Prior Capital Budgets ($189,969,000)" | One printed number, no list in this book; only the subtraction ties ($839,969,000 − $189,969,000 = $650,000,000) | Accept; "unverifiable here" |
| 2 | 61,737,000 | 63–65 | `60857d925b9b` | 29 `PV MA…` rows on `PV 0N…` lines | Part II and Part III only; not in Part I, the p.61 additions or t474. No sponsor. Same kind as FY2025–FY2027 | Accept as printed; ask Council Finance (needs_info) |
| 3 | **−40,000** | 65 | `a8274d6e2660` | `HL TA001` SEC249 ADJUSTMENT FOR THE SIUH NORTHWELL HEALTH CARDIAC IMAGING PROJ, line `HL RN404` | **Critical.** Part II only, a negative amount, a `TA` ID on an `RN` line (the only `RN` line in the book). Not in Part I or t474. In the Part II total and Part III. "SEC249" suggests a Charter §249 adjustment | Accept as printed (a reduction); include in the Council Finance question. Viewers must allow negative amounts |
| 4 | 16,291,000 | 4–60 | `C9.workbook_sponsor` (12) | 12 rows with sponsor `TECHNICAL ADJUSTMENT` (10 of them `TA` IDs) | The PDF prints the singular; t474 has "Technical Adjustments". Amounts and lines match | Accept as printed |
| 5 | 9,500,000 | 58 | `C9.workbook_sponsor` | `PV NC041` | PDF `SPEAKER, POWERS, MANHATTAN DELEGATION`; t474 `Speaker, Manhattan Delegation, Speaker` (Speaker twice, no Powers) | Keep the PDF; a note for `data/capital/` |
| 6 | 7,000,000 | 40 | `C9.workbook_sponsor` | `ED CN019` | t474 misspells `Salamanca` as `Salamance` | Keep the PDF |
| 7 | — | — | `e217c47e116b` | t474's FY2024 text | 78 rows print accents as mojibake: UTF-8 read as cp437 (`Avil├⌐s` = Avilés, `Vel├ízquez` = Velázquez). Decoded for comparing only | Accept; a note for `data/capital/README.md` |

## B. Capital: checked, no action needed (FYI)

- **The PDF is encrypted** with an empty user password; copying is not permitted by its owner flags, but
  text extraction is not blocked (see README). Ink coverage is 0, so the text read is the whole page.
- **3 rows** needed the "nearest row" rule (`60f77b1fc2e3`, `07afe6fa682d`, `42e4b7f4238f`: pp.47, 48,
  65). Values match the other Part and t474.
- **Part III hairlines** (`971a1f35a243`): 95 rules of 0.10–0.17 pt, too thin for 300 dpi.
- **`ED NC003`** has $6,000,000 in FY2025 and $0 in FY2024 (Part I, II, III); t474 has it.
- **The retired `data/fy24/capital/` CSV** dropped the printed comma after `SPEAKER` on 190 rows and
  moved a wrapped sponsor line into the title on 9. Every amount agrees.

## C. Terms & Conditions

No dollars. All 67 items are warnings.

| # | Page | review_id | What | Suggested decision |
|---|---|---|---|---|
| 1 | 2–24 | — | **The PDF prints no condition numbers.** `item_number` here is the order in the book (1..61), as the retired CSV numbered them. T1 checks it: 61 headings, 61 "As a condition" paragraphs | Accept; say so wherever `item_number` is shown for FY2024 |
| 2 | 16–22 | the 54 `T7.*` rows | **The retired CSV is wrong from #44 on.** It lost 4 conditions (#44 DOT/DCAS/Parks, #47 DYCD, #54 Mayoralty, #56 Office of Criminal Justice), split #61 into 3 rows, put headings and the FSR table into texts, and dropped hyphens (`low-barrier`, `self-placement`) | Use the new file. Note it in DATA-ANOMALIES |
| 3 | 16, 18, 20 | `0854a8a154a6` `8aac1c9377f9` `99c338f1bd52` `69d9c623064d` `0d866d6b93f5` | 5 agency lines print **no agency code** (`Department of Transportation`, `Department of Citywide Administrative Services`, `Department of Parks and Recreation`, `Department of Youth and Community Development`, `Mayoralty`). `agency_code` is blank. The units are printed | Accept as printed (source_error); do not fill codes from elsewhere |
| 4 | 21 | `21abfd518d7e` | #56 `Office of Criminal Justice ( 128)`: the name is regular type, only the code bold; units `[ 003]`, `[ 004]` print a space | Accept as printed |
| 5 | 14, 18, 21 | `eb2f5ae3ddde` `35b4e4c39597` `7215f7ce374a` | #34: the budget line wraps across a line end (`HD-` / `0009`) and T3 reads it with a space (a limit of the check; the text is right). #46 "units of appropriations", #56 "003 and004": the PDF's typos | Accept |
| 6 | 13–19 | `f91b9bd711c9` `88e7d9669319` `ea3b794ec2d8` `1d7347d142b1` | A line ends in a hyphen and joins with none (`low-` / `barrier`, `self-` / `placement`) | Accept |

## D. Policy questions (not decided here)

1. Retire or keep the old `data/fy24/capital|terms` CSVs? The terms one has lost 4 conditions.
2. FY2024 T&C numbers are ours, not the PDF's. Should the explorer show "#44" for FY2024 at all?
