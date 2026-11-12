# FY2027 transparency resolutions: what a person needs to check

**Report generated:** 2026-11-12. Source: `data/fy27_tr_review.csv` (10 rows), sorted the same
way: the critical item first, then by how much money each could touch. Decide each in the
explorer's Review tab, or write it into `data/fy27_tr_review_decisions.csv` by `review_id`
(decisions `accepted_as_printed`, `source_error`, `parser_bug`, `needs_info`,
`read_from_page_image`). The pipeline never writes that file. Nothing here changes a dollar
amount. Each item has a crop in `data/overlays/` (`r<reso>-p<page>-<review_id>.png`).

## Critical (1)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 1 | `c983e4543f60` | 04, p.13 | 20,000 | **An EIN where the organization's name belongs.** Chart #8 CASA - Fiscal 2027, Restler: "113271472 - Urban Assembly Institute of Math and Science for Young Women (13K527) **", EIN 11-3271472, DCLA, $20,000. 11-3271472 is the EIN Reso 01 p.21 prints for Noel Pointer Foundation, Inc. (four CASA rows for Ossé). The page shows the same. | `org` kept as printed. Named exception `T5.ein_in_text`, so the EIN census passes for this one word only. | `needs_info`: the organization is likely Noel Pointer Foundation, Inc., but the PDF does not say so. Ask Council Finance, or check the disclosure workbook once it has the row |

## Warn (9)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 2 | `dd6186017c15` | 01, p.28 | 17,500 | **Line-end hyphen.** NYC Cleanup, Stevens, Association of Community Employment Programs for the Homeless, Inc. - "Special Projects-⏎Council District 16". Probably "Special Projects - Council District 16" with the spaces lost. | Kept joined: "Special Projects-Council District 16". The other 6 line-end hyphens are compound words (one-on-one, School-Community ×2, YM-YWHA, back-to-school ×2), read by hand, not listed. | `accepted_as_printed` |
| 3 | `843b700617c6` | 01, p.37 | 0 | **A chart prints no fiscal year.** Chart #22 "Educational Programs for Students". Charts #21 and #23 are Fiscal 2027. | `budget_fiscal_year` blank, as printed. | `accepted_as_printed` |
| 4 | `8a66539867c8` | 01, p.40 | 0 | Same: chart #25 "Nontraditional Worker Organizing and Education" (between #24 and #26, both Fiscal 2027). | Same. | `accepted_as_printed` |
| 5 | `f5fe42087cd0` | 02, p.29 | 0 | Same: chart #24 "Nontraditional Worker Organizing and Education" (between #23 and #25, both Fiscal 2027). | Same. | `accepted_as_printed` |
| 6 | `32a603505c39` | 03, p.9 | — | **Caption repeated without "(continued)".** Chart #6 Speaker's Initiative to Address Citywide Needs - Fiscal 2027 starts p.8; p.9 prints the same caption again. | Read as its continuation (named exception, as FY2022). | `accepted_as_printed` |
| 7 | `2dd5104fe949` | 04, p.9 | — | Same, Reso 04 chart #6. | Same. | `accepted_as_printed` |
| 8 | `35992519dff3` | 04, p.12 | — | **"(Continued)" with a capital C.** Chart #8 CASA. | Read as chart #8 (continued). | `accepted_as_printed` |
| 9 | `4e37d0bb4fc2` | 04, p.13 | — | Same. | Same. | `accepted_as_printed` |
| 10 | `c54044418234` | 04, p.14 | — | Same. | Same. | `accepted_as_printed` |

## Not in the review file, on purpose

- **31 EINs printed without a hyphen.** 9 digits in `ein`, as printed in `ein_printed`; flag
  `W.ein_no_hyphen`.
- **118 rows with no border between two cells** (purpose-of-funds charts). Split by the header's
  columns; both grids agree on every one. Flag `W.spanning_cell`.
- **31 rows with no drawn `*` cell**, all empty. Flag `W.made_cell_empty`.
- **6 line-end hyphens** that are compound words (in `fy27_tr_flags.csv`).
- **13 zero-width characters** (e.g. after "Maritime, Ferry, and Waterfront Careers Readiness
  Initiative"), dropped and counted.
- **Disclosure gaps**, report only (`data/fy27_tr_disclosure_match.csv`). Fiscal 2027: 1,010 of
  1,962 organization designations are not in the disclosure on (EIN, amount): 796 the EIN is there
  at another amount, 89 key already used, 70 EIN not in it, 41 taken back by a later resolution,
  14 City-EIN name mismatch.
- **Rescission origins**, report only: of 520 rescissions from organizations, 243 match a
  Schedule C award, 205 take back an earlier resolution's designation, 49 are part of a larger
  earlier amount, 23 not found.

## Decisions for Noel

1. **Reso 04 p.13** (#1): ask Council Finance which organization this is? Suggested `needs_info`.
2. **The 3 charts with no year** (#3-#5): leave blank (current), as FY2026 did for Operation
   Backpack?
