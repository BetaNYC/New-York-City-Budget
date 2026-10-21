# FY2025 capital and T&C: rows for Noel to review

**Generated:** 2026-10-21 19:40 EDT, from `data/fy25_capital_sd_review.csv` and
`data/fy25_terms_review.csv`. Prepared by BetaNYC with AI assistance.

Sorted by dollars. Page = PDF page (1-based), not the printed "Page N of 63". Nothing here was
"fixed": every value is kept as printed, and the flag says why to look. The `review_id` column is the
id in the review CSV, so a decision can be recorded against it.

**Short version.** Every printed total ties (32 / 32, plus the p.67 summary and Part III). No dollar
amount in the PDF is in doubt. NYC Open Data `t474-a92g` (the comparison source for FY2025) matches all
1,325 of its rows; the PDF's 2 extra amounts are FY2026 money t474 does not carry. What is left: one
critical Part II row, the `MA` series, six IDs the PDF prints twice, and notes on the comparison source.

## A. Capital: decide or confirm (by dollars)

| # | $ (FY2025) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 75,000,000 | 67 | `5d3c4a40fa87` | p.67 "Less Rescindments from Prior Capital Budgets ($ 75,000,000)" | One printed number. No list in this book, so only the subtraction ties ($775,000,000 − $75,000,000 = $700,000,000). The Resolution A book (`Fiscal-2025-Capital-Changes.pdf`, out of scope here) lists rescindments | Accept; note "unverifiable here" |
| 2 | 57,657,000 | 71–72 | `507dc9fd67ed` | 39 `PV MA…` rows on `PV 0N…` lines | In Part II and Part III only. Not in Part I, not in the p.67 "City Council Additions", not in t474. No sponsor. The Part II total ($158,992,000) includes them. FY2027's `MA` / `0N` and FY2026's `MM` / `0N` rows are the same kind. One of them, `PV MA064`, has $5,000,000 in FY2026 and $0 in FY2025 | Accept as printed. Ask Council Finance what `MA` / `0N` mean (needs_info, as FY2027) |
| 3 | 10,000,000 (FY2026) | 58 | `940ddffa55f1` | `P CN175` BROOKVILLE PARK REC CENTER, line `P D019`, TECHNICAL ADJUSTMENTS | $0 in FY2025, $10,000,000 in FY2026. t474 holds FY2025 amounts only, so it has no row for it | Accept as printed |
| 4 | 6,000,000 (FY2026) | 44, 69 | `77932689b8e3` | `ED NC091` BAY RIDGE COMMUNITY DEVELOPMENT CENTER CONSTRUCTION, line `ED DN05P` | Same as #3: FY2026 money only. In Part I, Part II and Part III (p.79) | Accept as printed |
| 5 | 5,100,000 … 400,000 | 4–52 | `b97b9d69ea26` `77cd9e43ac40` `35fd6f14b9fd` `f9c753ab818c` `6fe051c46a51` `a8de47729cc7` | **The PDF prints 6 IDs on two rows each:** `HN CN021` (p.50 $5,000,000 QUEENSBOROUGH CC / p.51 $100,000 HUNTER WELCOME CENTER), `HN CN018` (p.51, same budget line: $100,000 HUNTER CAMPUS SCHOOL ROOF / $2,000,000 LEHMAN FINE ARTS), `HN CN020`, `HO CN019` (same line), `ED NC128` (p.4 AG DN06Y / p.44 ED DN06L), `E CN810` (same line) | t474 has the same pairs, so it is the source's numbering, not a parse error. Every row is in its total. A table keyed on `sub_id` alone would merge them | Accept as printed. Tell loaders: `sub_id` is not unique in FY2025 (key on page + row) |
| 6 | 4,000,000 | 51 | `dae1e9abc36f` | `HO CN025` ELMHURST HOSPITAL ENTRYWAY RENOVATIONS | `, SCHULMAN` typed into the PDF after export (fonts `MIZCVF+` / `BXDXCW+ArialMT`); its `C` is in a second subset, so the reader split the word at the font change; the parser joins touching words again. Sponsor reads `SPEAKER, LEE, KRISHNAN, SCHULMAN`, as t474 has it | Accept as printed (the later edit) |
| 7 | **2,500,000** | 74 | `7b83487a1305` | `PV CT001` 126 PV207APLO APOLLO THEATER, line `PV DN027` | **Critical.** Part II only, with a `CT` ID (not the `MA` series), on a `DN` line (the lines Part I rows use). Not in Part I, not in t474. No sponsor. In Part III (p.79, APOLLO THEATER FOUNDATION) and every Part II total. Its title has the same shape as FY2026's `PV MA0007` (`126 PV467GUG8`), which Noel accepted | Accept as printed; include in the Council Finance question |
| 8 | — | — | `e9eba9e60b6b` | t474's FY2025 text | 50 rows of `data/capital/council_capital_awards.csv` (FY2025) print accents as mojibake: cp1252 bytes read as cp437 (`OssΘ` = Ossé, `Cabßn` = Cabán, `AvilΘs` = Avilés, `CAF╔` = CAFÉ). The parser decodes them for comparing only; nothing is written back | Accept. A note for `data/capital/README.md` (not edited here) |

## B. Capital: checked, no action needed (FYI)

- **Wrapped sponsor cells.** `HN CN017` (p.50) prints its sponsors on three lines; the third
  (`ASIAN CAUCUS`) sits below the row's band. It now joins the row the sponsor line above it belongs to
  (`f18f2cb14557`, `021bc6efdf47`). The retired `data/fy25/capital` CSV lost that last line on 5 rows
  (`HN CN017`, `HO CN019`, `LB CN005`, `LQ CN003`, `P CN096`); t474 has it on all 5.
- **2 two-read disagreements** on p.51 (`20e687731a8f`, `5088871bb15a`), the page edited after export:
  one is a `0` both rows print, one a sponsor (`NURSE`) t474 confirms. Both kept the page-position read.
- **8 rows** needed the "nearest row" rule (`W.geom_near`: pp.50, 52, 54, 62, 65, 74, 76). Values match
  the other Part and t474.
- **Part III hairlines** (`66a7270ffdea`): 106 rules of 0.12 pt between organizations are too thin
  for a 300 dpi render. Nothing hides under them: ink coverage is 0 there.
- **`TECHNICAL ADJUSTMENTS`** is a printed sponsor on 32 Part I rows ($44,194,000). All are in t474 (as
  "Technical Adjustments"). Kept as printed.
- **The retired `data/fy25/capital/` CSV** agrees on every row, amount and borough. Besides the 5
  sponsors above, it differs in how it split odd codes out of 51 titles (`S:02M411`, `B:KBNU`,
  `NORTHSIDECENTER`); here they stay in the title as printed.

## C. Terms & Conditions

Nothing has dollars. All checks pass except three wording quirks.

| # | Page | review_id | What | Suggested decision |
|---|---|---|---|---|
| 1 | 6–25 | the 28 `T7.*` rows | **The retired CSV is wrong for 19 conditions.** It put headings into the text (#30, #39, #51–#53, #57–#65), put the FSR table into #16's text, dropped printed hyphens in 4 (#15, #20, #22, #23), and lost the units of every agency after the first in #57–#65 | Use the new file. Note it in DATA-ANOMALIES |
| 2 | 19 | `91bdc255aaed` | #57 lists DOHMH units `… 109, 011, and 112`; its heading has `111`. The PDF disagrees with itself | Accept as printed (source_error) |
| 3 | 24, 25 | `da3e74b07554` `aab45d05a5af` | "units of appropriations" (plural): the check does not read it, so it flags the body as naming fewer units than the heading. The heading is right. FY2026 #67 has the same typo | Accept |
| 4 | 5–25 | `a560c1790b58` `920b6c961e52` `98451b48b2b4` `9bb44f4a427b` | `community-` / `based`, `non-` / `special`, `Pre-` / `Kindergarten`, `Person-` / `related`: a line ends in a hyphen and is joined with none | Accept |

## D. Policy questions (not decided here)

1. Should the retired `data/fy25/capital/` and `data/fy25/terms/` CSVs be replaced by these, or left as
   history with a pointer? (Same question as FY2026 D2.)
2. `sub_id` is not unique in FY2025 (A5). Should the explorer's capital view say so?
