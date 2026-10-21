# FY2025 transparency resolutions: what a person needs to check

**Report generated:** 2026-10-21 19:15 EDT. Source: `data/fy25_tr_review.csv` (40 rows), sorted
the same way: the 7 critical items first, then by how much money each could touch. Write each
decision into `data/fy25_tr_review_decisions.csv` by `review_id` (columns `review_id, decision,
note, decided_by, decided_at`; decisions `source_error`, `parser_bug`, `accepted_as_printed` or
`needs_info`), or use the explorer's review screen and `code/validate_review_decisions.py --add`.
The pipeline never writes that file. Nothing here changes a dollar amount. Each row has a crop in
`data/overlays/` (named `r<reso>-p<page>-<review_id>.png`).

## Critical (7)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 1 | `d10cfd773e5b` | 06, p.6 | 50,000 | **`***` with no `***` footnote.** Speaker's Initiative, Brooklyn Kindergarten Society \*\*\*, $50,000. The page prints only the `*` and `**` footnotes; 44 of the chart's 49 rows carry `**`. Likely a typo for `**`. | Kept as printed: `org_marker` = `***`, `correction` = 1. Named exception in the config. | `source_error` |
| 2 | `6194373b6cad` | 07, p.18 | 15,000 | **A row prints no EIN.** SU-CASA, Salamanca, Afro-Latin Jazz Alliance of New York – East Side House Melrose Older Adult Center, $15,000. The EIN cell is empty on the page; the row above, the same organization, prints 45-3665976. | `ein` blank, as printed. | `source_error` |
| 3 | `8f86e12b062a` | 08, p.13 | 15,000 | **The fix, a month later.** Reso 08 takes back #2 with no EIN, ($15,000), and gives it again on the next row with EIN 45-3665976. | `ein` blank, as printed. | `source_error` (the Council corrected it itself) |
| 4 | `2af64a316933` | 07, p.30 | 5,000 | **A staff note in the `*` column.** Midori Foundation – Blueprint Middle School, ($5,000). The `*` cell shows "01/"; the rest of a note runs past the table and off the page: "22; DCLA: We checked Midori’s final CDF report and they did do activity at PS536X so that change is ok. ; proram name & POF change as per CBO's request". | `prequal_printed` = "01/", `prequal_pending` = 0; the note in `hidden_text`. Both grids agree. Named exception. | `source_error` |
| 5 | `6d600c42f6eb` | 07, p.30 | 5,000 | Same note, the other half of #4 (Midori – PS 536X, $5,000). | Same. | `source_error` |
| 6 | `469d079afabb` | 07, p.29 | 4,000 | Same kind of note: "01/22; placeholder - program name & Purpose fo funds change". Parks – Community Movie Nights, $4,000. | Same. | `source_error` |
| 7 | `800de0e0fe8a` | 07, p.29 | 4,000 | Same note, the other half of #6 (Parks, ($4,000)). | Same. | `source_error` |

## Warn (33)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 8 | `0349423b7d88` | 03, p.30 | 1,500,000 | **Purpose change across two organizations.** Guaranteed Income Pilot Program: Department of Social Services ($1,500,000) to The Bridge Project $1,500,000. A different EIN on each side. | Kept as printed. | `accepted_as_printed` |
| 9 | `ff5773ebb808` | 03, p.30 | 1,500,000 | The other half of #8. | Same. | `accepted_as_printed` |
| 10 | `3effec0d1599` | 02, p.76 | 500,000 | **Purpose change split in three.** Speaker's Initiative, Children's Rescue Fund ($500,000) becomes $250,000 (#13), $200,000 Job Training (#16) and $50,000 Digital Inclusion (#18). Same EIN. | Kept as printed. | `accepted_as_printed` |
| 11 | `4658dfa7a07c` | 01, p.60 | 250,000 | **Text cut off by the next cell.** Source prints "Speaker's Initiat"; "ive" is in the PDF but hidden under the Member cell. New York Abortion Access Fund, $250,000. | `source` = "Speaker's Initiat" (what shows); `hidden_text` = "source: ive". Both grids agree. | `accepted_as_printed` |
| 12 | `6571dd7ba64c` | 01, p.60 | 250,000 | Same, the ($250,000) side. | Same. | `accepted_as_printed` |
| 13 | `47c31940b36d` | 02, p.76 | 250,000 | Part of #10. | Same. | `accepted_as_printed` |
| 14 | `77104373ff82` | 01, p.61 | 200,000 | **Purpose change across two organizations.** Job Training and Placement Initiative: Small Business Services ($200,000) (#15) to Consortium for Worker Education – Make the Road $200,000. | Kept as printed. | `accepted_as_printed` |
| 15 | `98f5a62ade86` | 01, p.61 | 200,000 | The other half of #14. | Same. | `accepted_as_printed` |
| 16 | `21a0c85ceef0` | 02, p.76 | 200,000 | Part of #10. | Same. | `accepted_as_printed` |
| 17 | `95986eea8677` | 01, p.59 | 50,000 | Cut off twice: Source "Community Saf" (hidden "ety and Victim Services"), organization "Justice Innovation – Housing Resource Cente" (hidden "r"). $50,000. | As #11. | `accepted_as_printed` |
| 18 | `431ad8f5aa4e` | 02, p.76 | 50,000 | Part of #10. | Same. | `accepted_as_printed` |
| 19 | `30fbe731573e` | 07, p.29 | 40,000 | **Purpose change split in four.** Local, Riley, Regional Aid for Interim Needs ($40,000) becomes $20,000 + $10,000 + $5,000 + $5,000 (#22, #25, #26, #27). Same EIN. | Kept as printed. | `accepted_as_printed` |
| 20 | `0476bae4c128` | 01, p.61 | 25,000 | "Speaker's Initiat" cut off, as #11. HANAC – Angelo Petromelis Older Adult Center ($25,000). | As #11. | `accepted_as_printed` |
| 21 | `e087cb418031` | 01, p.61 | 25,000 | Same, the $25,000 side. | As #11. | `accepted_as_printed` |
| 22 | `0044ed64f258` | 07, p.29 | 20,000 | Part of #19. | Same. | `accepted_as_printed` |
| 23 | `7718c398efd7` | 02, p.75 | 18,000 | **The same two rows printed under three fiscal years.** Black Spectrum Theatre: Catherine & Count Basie MS ($18,000) to Redwood MS $18,000, as "Art a Catalyst for Change" chart #17 (Fiscal 2025, p.47), #43 (Fiscal 2024, p.74) and #44 (Fiscal 2023, p.75). #43 and #44 are the pages with no "Page n" label (#36, #37). | Kept as printed: 6 rows. | `needs_info`: three changes, or one printed three times? |
| 24 | `663fda14012d` | 01, p.60 | 10,000 | Organization cut off: UA3 – Community Safety Resources – Counc, hidden "il District 43". $10,000. | As #11. | `accepted_as_printed` |
| 25 | `94490377231c` | 07, p.29 | 10,000 | Part of #19. | Same. | `accepted_as_printed` |
| 26 | `3ad768887b3b` | 07, p.29 | 5,000 | Part of #19. | Same. | `accepted_as_printed` |
| 27 | `559e64838ec0` | 07, p.29 | 5,000 | Part of #19. | Same. | `accepted_as_printed` |
| 28 | `0fd7070c93cb` | 07, p.30 | 5,000 | The hidden note of #4, as a hidden-text item. | See #4. | `accepted_as_printed` |
| 29 | `a318f4e49268` | 07, p.30 | 5,000 | The hidden note of #5. | See #4. | `accepted_as_printed` |
| 30 | `fbad21e8a701` | 07, p.30 | 5,000 | **No drawn `*` cell** in the row of #4; read from the header's column. | Image grid agrees. | `accepted_as_printed` |
| 31 | `fcf8559ea5c0` | 07, p.30 | 5,000 | Same, row of #5. | Same. | `accepted_as_printed` |
| 32 | `9731f6eca137` | 07, p.29 | 4,000 | The hidden note of #6. | See #4. | `accepted_as_printed` |
| 33 | `a8a2b11c69ac` | 07, p.29 | 4,000 | The hidden note of #7. | See #4. | `accepted_as_printed` |
| 34 | `b3e7d29f540e` | 07, p.29 | 4,000 | No drawn `*` cell, row of #6. | Same. | `accepted_as_printed` |
| 35 | `d61b2f941102` | 07, p.29 | 4,000 | No drawn `*` cell, row of #7. | Same. | `accepted_as_printed` |
| 36 | `12339e63ded9` | 02, p.74 | — | **No "Page n" label** under chart #43. p.73 is "Page 71", p.76 "Page 74", so the labels count it. | Named exception. | `accepted_as_printed` |
| 37 | `ebc45aab76d0` | 02, p.75 | — | Same, chart #44. | Same. | `accepted_as_printed` |
| 38 | `6dca757565ba` | 03, p.28 | — | Same, chart #23 (p.27 "Page 25", p.29 "Page 27"). | Same. | `accepted_as_printed` |
| 39 | `47b66a00021b` | 04, p.1 | 0 | **Reso 04 has no resolution number.** Adopted 2024-10-23 (its own p.1: "dated October 23, 2024"). The PDF prints no number; the 2026-07-07 Legistar pass did not find the matter. | `resolution_number` blank on its 27 rows; `resolution_date` set. | `needs_info`: look it up in Legistar and add it to the config |
| 40 | `8341a2514d47` | 11, p.6 | — | **Caption without a colon:** "CHART #4 Anti-Poverty - Fiscal 2025". Charts #3 and #5 are around it. | Read as chart #4. | `accepted_as_printed` |

## Not in the review file, on purpose

- **8 EINs printed without a hyphen.** Read as printed (`ein_printed`), 9 digits in `ein`; flag
  `W.ein_no_hyphen`.
- **30 rows with no border between Source and Member** (purpose-of-funds charts). Split by the
  header's columns; both grids agree. Flag `W.spanning_cell`.
- **58 rows with no drawn `*` cell**, all empty. Flag `W.made_cell_empty`.
- **4 line-end hyphens**, all compound words (at-risk, evidence-based, In-School ×2), read by hand.
- **Disclosure gaps.** Report only. 189 FY2025 designations are not in the disclosure on (EIN,
  amount): 149 taken back by a later resolution, 27 the EIN is there at another amount, 8
  City-EIN name mismatch, 5 key already used. FY2024 and FY2023 rows are checked against those
  years' disclosures. Every row and reason: `data/fy25_tr_disclosure_match.csv`.
- **Rescission origins**, report only: of 825 rescissions from organizations, 385 take back an
  earlier resolution's designation, 334 match a Schedule C award (retired CSV), 58 are part of a
  larger earlier amount, 48 not found.

## Decisions for Noel

1. **Staff notes in `hidden_text`** (#4–#7). The notes are in the public PDF's text layer, but
   nobody reading the page can see them. They are kept in `hidden_text` like every other hidden
   letter (the FY2026 rule). Keep them there (current), or blank them in the promoted tables?
   I'd keep them: they are what the PDF holds, and they explain the stray "01/".
2. **Black Spectrum, three fiscal years** (#23). Keep all 6 rows (current), or mark the 2023
   and 2024 copies? I'd keep them and leave the flag; only the Council can say.
3. **Reso 04's number** (#39). Leave blank (current) until someone looks it up in Legistar.
