# FY2018 transparency resolutions: what a person needs to check

**Report generated:** 2026-10-22 02:10 EDT. Source: `data/fy18_tr_review.csv` (72 rows), sorted
the same way: the 8 critical items first, then by how much money each could touch. Write each
decision into `data/fy18_tr_review_decisions.csv` by `review_id` (columns `review_id, decision,
note, decided_by, decided_at`; decisions `source_error`, `parser_bug`, `accepted_as_printed` or
`needs_info`), or use the explorer's review screen and `code/validate_review_decisions.py --add`.
The pipeline never writes that file. Nothing here changes a dollar amount. Each item has a crop
in `data/overlays/` (named `r<reso>-p<page>-<review_id>.png`).

## Critical (8)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 1–2 | `c23dd9634d2f` `e91a0aaaa584` | 10, p.20 | 7,805,000 | **"All Allocations", EIN "Various"**: Source "Domestic Violence and Empowerment (DoVE) Initiative", ($7,805,000.00) and $7,805,000.00, a new purpose for the whole initiative. | Kept as printed: `ein` blank, `ein_printed` "Various". The old CSV missed both rows. | `accepted_as_printed` |
| 3–8 | `f82dd14b7559` `892eb2d0637a` `cee66042cf61` `5d5d048fe0e0` `ac5f4f3b2246` `dd3371e7d09f` | 05, p.23 | 12,500–22,500 | **`**` on a page that prints no footnotes at all** (the last page of its chart): Torres, New York Botanical Garden ±$20,000 DYCD; Mendez, Fund for the City of New York - Cafeteria Culture Program, $12,500 and $22,500 DYCD → DOE. | Kept as printed: `budget_modification` = 1. Named exceptions. | `source_error` |

## Warn (64)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 9–10 | `891ae2c18138` `0c636406fa73` | 04, p.56 | 100,000 | **One organization under two EINs in a purpose-of-funds pair**: Cumbo, NYC Cleanup, Association of Community Employment Programs for the Homeless, ($100,000) at 13-3846431 and $100,000 at 13-3846432. | Kept as printed; each row has no partner (`W.unpaired_purpose`). | `source_error` |
| 11–14 | `f5ced6badb09` `3c0cccfb6524` `e34d7856b945` `50fc3ed732af` | 05, p.61 | 100,000 | **Amounts printed without "$"**: "(100,000.00)" / "100,000.00", Asian American Federation of New York (Communities of Color Nonprofit Stabilization Fund) and Edwin Gould Services for Children and Famlies (Speaker's Initiative). Red and black as usual. | Read as ±$100,000 (`W.amount_format`). | `accepted_as_printed` |
| 15–28 | 14 items (`W.clipped_text`) | 03 pp.17, 71, 72; 04 pp.52, 56 | 5,000–100,000 | **Text hidden under the next cell**: the page shows "…Programs f", "…Queens Chapt", "…Together, I"; the rest ("or the Homeless, Inc.", "er #32", "nc.(COMET)") is in the text layer only. Reso 03 p.71: Source "…Initiat" + "ive". | The value keeps what shows; the hidden part is in `hidden_text`. Reso 04 p.52 row 2 (`f65b3e471906`): on this named page the EIN that follows the hidden "ork" is read as the EIN (`T7.clip_restart`); the old CSV missed the row. | `accepted_as_printed` |
| 29–30 | `a45d2c58e270` `e72fa2e63d66` | 05, p.60 | 20,000 | **Two +$20,000 purpose rows and no negative**: Cabrera, Police Athletic League, Inc. (PAL Teen Center; Teen 12-week Basketball clinic). Both black, both "$20,000.00". The resolution's purpose rows are +$40,000 out of balance. | Kept as printed (`W.unpaired_purpose`). | `source_error` |
| 31–34 | `35a637fffb8f` `4cdf76f91af6` `2559afe221ef` `64f13a65f966` | 04 p.56; 11 pp.17, 19 | 5,000–15,000 | **Overfull cell** (FY2019's rule): the purpose wraps past its row. On Reso 11 p.19 the old reading was "aFnudn daifntegr t-os cshuopopl.ort …" (two rows' lines on top of each other). | Read as one block per cell; each compared by hand with the page. | `accepted_as_printed` |
| 35–38 | `84a993ad87e4` `8a065aeb7f44` `03edcbd7ff6d` `ceebd039e948` | 06 pp.14, 16 | 2,000–5,000 | **Fiscal conduit EIN not readable**: "#########" (Excel's mark for a number too wide for its cell) on three rows (Drag Queen Story Hour NYC, Staten Island Cricket Club, Little Essentials); "13-281380" (8 digits) for City as Living Laboratory. | `fiscal_conduit_ein` blank, printed text kept. | `source_error` |
| 39 | `eb698a904c6b` | 01, p.1 | — | **Adopted before the fiscal year**: Reso 01 dated June 21, 2017; Fiscal 2018 began July 1, 2017. It changes the Fiscal 2018 budget (adopted June 6, 2017; charts 1–29, 38) and the Fiscal 2017 and 2016 budgets (charts 30–37, 39). | Kept in FY2018, as the 2026-07-07 notes and the crosswalk file it; `budget_fiscal_year` from each chart (`K.adopted_before_fy`). | `accepted_as_printed` |
| 40–43 | `d9a3167efc56` `d29aff00bfeb` `7c5237cd294e` `5facef00cd09` | 03 pp.24, 25, 30; 04 p.58 | — | **A footnote that explains the chart**: Reso 03: "these funds were shown to be reallocated from one agency to another … the funds will no longer be reallocated and will remain within the agency as designated in Schedule C." Reso 04 p.58: "In Schedule C $5,154,200 was designated to Consortium for Worker Education - Jobs to Build On (CWE), $4.46m of which CWE subcontracted …; this chart reflects that change." | Read as footnote text (`T6.footnote`), not furniture and not a printed total. | `accepted_as_printed` |
| 44–55 | 12 items (`W.caption_format`) | 03 pp.37–40, 43–44; 04 pp.16, 31, 58; 06 pp.51–53 | — | **"(Continued)" with a capital C** (11 pages), and "CHART 42: Job Training and Placement Initiative - Fiscal 2018 ***" (Reso 04 p.58, the footnote marker for item 43). | Read as the printed number and year. | `accepted_as_printed` |
| 56–64 | 9 items (`T4.no_amount`) | 02 p.68; 03 p.78; 04 p.59; 05 p.63; 06 p.55; 07 p.38; 08 p.47; 09 p.36; 11 p.20 | — | **"Beating Hearts Initiative": no Agency or Amount column** (136 rows). Each note: "Staten Island Heart Society, Inc. has received $350,000 that will go towards providing automated external defibrillators (AEDs) to non-profit organizations…" (the text layer has no spaces in it). | Rows kept, amount blank, `action` = `listed`. Named exceptions. | `accepted_as_printed` |
| 65–68 | `241f9d46f4af` `16f492248504` `f3fc2485680a` `65cbbfbabc94` | 01 pp.55, 56; 03 p.48; 04 p.32 | — | **Header row with no labels**: a grey band with nothing printed in it. | Read with the labels of the chart page before it (pp.54, 47, 31), whose column edges are the same (`T4.blank_header`). Rows checked on the page. | `accepted_as_printed` |
| 69–71 | `b987e6b57bb7` `c5019261f33b` `a8b55f8e61d7` | 01 p.36; 02 p.33; 03 p.27 | — | **Caption repeated without "(continued)"**: chart #12 Support Our Seniors, #13 Cultural Immigrant Initiative, #9 DoVE. | Read as continuations. Named exceptions. | `source_error` |
| 72 | `cb788599b9ed` | 09, p.30 | — | **Chart prints no fiscal year**: "CHART 20: Senior Centers, Programs, and Enhancements" (one row, −$40,000). | `budget_fiscal_year` blank, as printed. Its neighbours are Fiscal 2018. | `accepted_as_printed` |

## Not in the review file, on purpose

- **Reso 11 p.17 prints the agency "DSS/H" / "RA"** on two lines (a narrow column); the clean value
  is "DSS/H RA" (2 rows, ±$5,000). See Decisions.
- **Old CSV**: its 2 rows not here are its own misreading of Reso 04 p.56's EIN (see README).
- **27 line-end hyphens on 27 rows**, all read by hand: compound words (Ferreras-Copeland x12,
  enrollment-based x8, low-income x3, Anti-Violence x2, self-peer, free-of-charge). None goes to
  review.
- **50 EINs printed without a hyphen** (`W.ein_no_hyphen`), read as printed.
- **56 rows with a cell spanning two columns** (`W.spanning_cell`), as FY2019.
- **Resolution nets** (README): Reso 03 +$75,000, 04 −$75,000, 05 −$500,000, 08 +$1,000,000,
  10 +$400,000. No chart is $1 off.
- **Disclosure gaps** (report only): 291 FY2018 designations not found on (EIN, amount): 232
  taken back later, 40 at another amount, 9 key already used, 8 City-EIN name mismatch, 2 EIN not
  in the disclosure. `data/fy18_tr_disclosure_match.csv`.
- **Rescission origins** (report only): of 931, 411 take back an earlier resolution's row, 47
  match a Schedule C award (retired CSV), 178 part of a larger amount, 295 not found.

## Decisions for Noel

1. **Reso 01 in FY2018** (item 39): kept, as the Legistar notes file it. If the Council's own
   series puts it in FY2017, it moves with its config entry; nothing else changes.
2. **Fiscal conduit columns**: four new columns at the end of FY2018's row table only. Fine for
   the explorer, or should they live in a side table?
3. **"DSS/H RA"** (Reso 11 p.17): keep as printed, or a review row and a note "DSS/HRA"?
4. **"Beating Hearts Initiative"** rows (136): kept as `listed`, as FY2019–FY2022; the note gives
   the $350,000 total only.
5. **Police Athletic League's two +$20,000 rows** (items 29–30): `source_error`, or ask Council
   Finance (`needs_info`)?
