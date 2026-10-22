# FY2024 transparency resolutions: what a person needs to check

**Report generated:** 2026-10-21 19:18 EDT. Source: `data/fy24_tr_review.csv` (19 rows), sorted
the same way: the 5 critical items first, then by how much money each could touch. Write each
decision into `data/fy24_tr_review_decisions.csv` by `review_id` (columns `review_id, decision,
note, decided_by, decided_at`; decisions `source_error`, `parser_bug`, `accepted_as_printed` or
`needs_info`), or use the explorer's review screen and `code/validate_review_decisions.py --add`.
The pipeline never writes that file. Nothing here changes a dollar amount. Each item has a crop
in `data/overlays/` (named `r<reso>-p<page>-<review_id>.png`).

## Critical (5)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 1 | `19f6be5608b0` | 02, p.18 | 20,000 | **"#" in the `*` column.** NYC Cleanup, Rivera, Fund for the City of New York – Cafeteria Culture Media & Arts – PS 188M The Island School, $20,000. The page prints "#" where only "\*" or nothing belongs. | `prequal_printed` = "#", `prequal_pending` = 0. Named exception. | `source_error` |
| 2 | `ad459e77fe6f` | 07, p.17 | 10,000 | **EIN printed as "TF4876222".** NYC Cleanup, Nurse, Knickerbocker Avenue Merchants Partnership – Knickerbocker Beautification, ($10,000). Schedule C printed the same "TF4876222". The next row gives the $10,000 back with EIN 84-3309358, which the disclosure also has: the Council fixed its own placeholder EIN. | `ein` blank (not 9 digits), `ein_printed` as printed. | `source_error` |
| 3 | `34f46da7ac0f` | 01, p.55 | 5,000 | **`***` with no `***` footnote.** Aging Discretionary – Fiscal 2023, Paladino, Selfhelp – Clearview Senior Center \*\*\*, ($5,000). The page prints only the `*` and `**` footnotes. | Kept as printed: `org_marker` = `***`, `correction` = 1. Named exception. | `source_error` |
| 4 | `5c3c8cd2c7b6` | 01, p.55 | 5,000 | Same, the other half: Department for the Aging \*\*\*, $5,000. | Same. | `source_error` |
| 5 | `325b1e3a5393` | 02, p.11 | — | **Ink outside every kept letter (2 spots, 72 px each).** The left edge of the clipped "n" of "Staten Island Delegation" shows before the Borough cell's border, on both rows (#7, #8). | The check is right: part of a hidden letter is visible. Values keep what shows clearly. | `accepted_as_printed` |

## Warn (14)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 6 | `893fe4e72c68` | 02, p.18 | 17,500 | **Line-end hyphen.** Stevens, Association of Community Employment Programs for the Homeless – "Special Projects-⏎Council District 16". Could be "Special Projects - Council District 16" with the spaces lost. | Kept joined. The other 2 are compound words (Self-Determination, Anti-Hate). | `accepted_as_printed` |
| 7 | `139634d7acf4` | 02, p.11 | 14,000 | **Text cut off by the next cell.** Borough prints "Staten Island Delegatio"; the "n" is hidden under the organization cell. Eden II School for Autistic Children, $14,000. | `member` = "Staten Island Delegatio" (what shows); `hidden_text` = "member: n". Both grids agree. | `accepted_as_printed` |
| 8 | `eeb367e5fe08` | 02, p.11 | 14,000 | Same, South Shore District Management Association, ($14,000). | Same. | `accepted_as_printed` |
| 9–16 | `1abdab01a327` `0bde5b7da493` `8d88c6bf26ea` `6f682c87e2a0` `1e0f9fdc9064` `8dd98e9dbdf2` `682851956538` `f94a25f6d60e` | 02, pp.66–73 | — | **No "Page n" label** under charts #46–#53 (all Fiscal 2022 and 2023). p.65 is "Page 63", p.74 "Page 72", so the labels count them. | Named exceptions. | `accepted_as_printed` |
| 17–19 | `052fa328f235` `b0090fc0b060` `a79e472de558` | 03, pp.55–57 | — | Same, charts #53–#55 (Fiscal 2023). p.54 "Page 52", p.58 "Page 56". | Named exceptions. | `accepted_as_printed` |

## Not in the review file, on purpose

- **7 EINs printed without a hyphen**, read as printed; flag `W.ein_no_hyphen`. These are 7 of the
  9 rows the old CSV missed.
- **37 rows with no drawn `*` cell**, all empty (`W.made_cell_empty`).
- **Disclosure gaps** (report only): 115 FY2024 designations not found on (EIN, amount): 74 taken
  back later, 26 at another amount, 7 City-EIN name mismatch, 4 EIN not in the disclosure, 4 key
  already used. `data/fy24_tr_disclosure_match.csv`.
- **Rescission origins** (report only): of 762, 249 take back an earlier resolution's row, 370
  match a Schedule C award (retired CSV), 73 part of a larger amount, 70 not found.

## Decisions for Noel

1. **"Staten Island Delegatio"** (#7, #8). Values keep what shows (the FY2026 rule), so the
   borough reads "Delegatio". Keep, or add the hidden "n" back for these two? I'd keep: the
   explorer can show `hidden_text`.
2. Nothing else needs a call beyond the suggestions above.
