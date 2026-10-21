# FY2027 Schedule C: what a person needs to check

**Report generated:** 2026-10-20 22:40 EDT. Source: `data/fy27_sc_review.csv` (6 rows),
sorted by how much money each could touch. Write each decision into
`data/fy27_sc_review_decisions.csv` by `review_id` (`source_error`, `parser_bug`,
`accepted_as_printed` or `needs_info`). Nothing here changes a total.

| # | review_id | Page | $ | What | What we did |
|---:|---|---:|---:|---|---|
| 1 | `01375b88b4c3` | 463 | 5,000 | **The two grids disagree on one cell edge.** Center for Educational Innovation, Thomas-Henry, $5,000. The name ends "& Porgrams -", and that last hyphen pokes past the border into the EIN box. The vector grid puts the hyphen with the EIN; the image grid puts it with the name. On the page it belongs to the name. | EIN read as `134113613` (both grids agree on the digits). Name kept without the cut-off " -". Crop: `data/overlays/p463-0.png`. Suggest `accepted_as_printed`. |
| 2 | `efad3687c709` | 13 | 9,000 | **Line-end hyphen.** God's Love We Deliver, "…Thanksgiving and Easter Meals-" then "Council District 32" on the next line. Could be "Meals - Council District 32" with the space lost. | Kept as printed: `…Easter Meals-Council District 32`. Raw text keeps the line break. |
| 3 | `2a9b49ebcf3e` | 315 | 5,625 | Same as #2 (Appendix A, same organization, $5,625). | Same. |
| 4 | `d68b985e6c58` | 214 | 1 | **The PDF disagrees with itself by $1.** Support Our Older Adults: "has designated $7,229,999"; its 394 rows add to $7,229,998. | Not fixed. Named exception in `config/schedule_c/fy2027.toml`. Suggest `source_error`. |
| 5 | `7253bd6cce3a` | — | 1 | The same $1 in the roll-up: category TOTALs $655,764,999 vs rows + reserves $655,764,998. | Same as #4. |
| 6 | `173122c5ffd8` | 486 | 0 | **Text layer vs pixels.** New York WEB Center, purpose: the text layer says "multi media", the page shows "multi-media". Both grids read the text layer, so they agree with each other. Found by the 2026-10-19 prototype's OCR sample. | Text layer kept as the record (PLAN open decision 4). |

## Not in the review file, on purpose

- **80 line-end hyphens** in names and purposes (`low-⏎income`, `after-⏎school`,
  `Home-⏎Delivered`). Each was read by hand from the list in `fy27_sc_flags.csv`: all but #2 and
  #3 are real compound words, so the clean value keeps the hyphen. Flag `W5.wrap_hyphen` on the row.
- **2 zero-width characters**, dropped and counted (`fy27_sc_checks.txt`).
- **Disclosure gaps.** The disclosure is a later snapshot, so gaps are coverage, not errors.
  129 PDF rows ($9,375,459) have no disclosure row: 42 amount differs, 50 key already used by
  another PDF row, 17 EIN not in the disclosure, 11 EIN used up, 9 City-EIN name mismatch.
  557 disclosure rows have no PDF row: 456 amount or count differs, 71 City-EIN Pending
  ($11,338,761), 30 EIN not in the PDF. Every row and reason: `data/fy27_sc_disclosure_match.csv`.
