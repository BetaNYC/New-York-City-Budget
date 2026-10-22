# FY2019 capital: rows for Noel to review

**Generated:** 2026-10-22 01:30 EDT, from `data/fy19_capital_sd_review.csv`. Prepared by BetaNYC with AI
assistance.

Critical first, then by dollars. Page = PDF page (1-based). Nothing here was "fixed": every value is
kept as printed. `review_id` is the id in the review CSV.

**Short version.** FY2019 has capital supporting detail only (no T&C in `source/`), and the book is an
Excel print of the Council's database, not the usual Word book. 1,625 rows. Its one total row ties on all
four years ($614,910,000 FY2019, $15,900,000 FY2020). NYC Open Data `t474-a92g` matches all 1,628 of its
amounts and every title. **3 critical items**, all the PDF's own content: three lower-case boroughs. One
row's sponsor disagrees with t474 (B1).

## A. Critical

| # | $ (FY2019) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 800,000 | 6, 8, 12 | `d9a800b45875` `5234b91a1f0c` `c2433bdb9ddd` | `E CN161` I.S. 484 (K484) $250,000; `E CN227` MIDDLE SCHOOL FOR ART & PHILOS (K588) $125,000; `E CN403` P.S. 40 (K040) $425,000 (all CD 41, Ampry-Samuel) | Borough printed in lower case, `k` (t474: `K`, Brooklyn) | Accept as printed (source_error); a loader may upper-case it for display, never in the file |

## B. Decide or confirm (by dollars)

| # | $ (FY2019) | Page | review_id | Row | What | Suggested decision |
|---|---:|---|---|---|---|---|
| 1 | 500,000 | 40 | `adb5da55e034` `b0cdd77f16a9` | **`HW CN030`** `HW D103`, borough Q, DOT REPAVING IN DISTRICT 31 | The PDF prints CD **49, 00** (Rose, Speaker). t474 has council_district 3100 and sponsor **Richards**, Speaker. District 49 is Staten Island; the title and borough say Queens district 31 (Richards). The only row where the PDF and t474 disagree on anything but wording | Keep the PDF value. Likely a source_error in the book (49 for 31); **ask Council Finance (needs_info)** before calling it |
| 2 | 15,460,000 | 1–54 | — | OMB adopted release (2018-07-13) by budget line | 165 / 176 lines equal OMB. OMB is higher on 10 (`HW D101` +$4,000,000, `P D019` +$3,000,000, `P D017` +$2,600,000, `PV D467` +$2,500,000, `HD D021` +$1,500,000, `E D001` +$500,000, `P D018` +$400,000, `PW D007` +$350,000, `T D005` +$250,000, `PO D185` +$60,000) and has 1 line with no PDF row (`LB D107` $300,000). Same as `data/capital/RECONCILIATION.md` §3 | No change; already in RECONCILIATION. Ask Council Finance only if the gap matters for a use |
| 3 | — | 34–53 | 7 `C9.workbook_sponsor` | group names | The Key to CD prints `Caucus Black, Latino and Asian` (code 97; 6 rows) and `Caucus Progressive` (88; 1 row); t474 writes `Black, Latino and Asian Caucus`, `Progressive Caucus`. Same people, other wording | Accept as printed; see D1 |
| 4 | 2,185,000 | 40–41 | `7d3af6c5266a` `ed65bdce0f12` `e2d5d25f539b` `c7fe52caad0e` `a0c8ac801283` `ba540f2c8911` | **`LB CN001`–`LB CN006` printed twice each**: once on `LB D104` (Brooklyn Public Library; `LB CN004` on `HN D300`) and once on `LN D008` (NYPL) | One ID number, two lines, two projects. t474 has all twelve the same way | Accept as printed; a join must use (ID, line) |
| 5 | 6,145,000 | 29, 30, 44, 46 | `cdf76e64474d` `5072f423d6b9` `770f0c233b0e` `270dbcd7c7c6` | `E CN997` $1,000,000; `F CN032` $100,000; `P CN049` $45,000; `P CN589` $5,000,000 | DESC cell empty in the PDF; t474 has `NA` | Accept as printed |
| 6 | — | — | `fd7f8d26b8d4` | t474's FY2019 text | 11 rows of mojibake (`FA├çADE`, and `TRUCK┬á` = a no-break space after TRUCK), UTF-8 read as cp437. Decoded for comparing only | Accept; a note for `data/capital/README.md` |

## C. Checked, no action needed (FYI)

- **The total row has no label and no count** (p.54, bold, under the grid). Its four amounts tie; the
  FY2019 amount is written as two touching pieces, `6` + `14,910,000`, and reads `614,910,000` on the
  page.
- **`HL NC57`** (p.36, HOSPITAL FOR SPECIAL SURGERY, $546,000): a two-digit ID number, listed in config.
  t474 has it the same way.
- **Key to CD, p.55:** `Caucus Black, Latino and Asian97` prints the name and the district as one word
  (`070667af6efe`); split at the digits. Codes 90, 96, 99 are in the key and used by no row.
- **4 dashes run 0.5–0.7 pt over a title cell's right border** (pp.1, 21, 33, 36; `C6.cell_overflow`).
  The dash closes the title (`ABRAHAM LINCOLN HIGH SCHOOL (21K410) -`); it is in the right cell.
- **C7, p.55** (`aad889320595`): the key's top border lies on the header's bottom border; the pixels show
  one rule.
- **Typos kept as printed:** `SUPPMENTAL` (`E CN403`), `CONFGURATION` (`E CN070`), `EASIDE` (`PW NC888`),
  `SURVEILLIANCE`.
- **6 rows carry FY2020 money** (`HD NC042`, `HL NC004`, `LQ CN016`, `PV NC113`, `PV NC121`,
  `PW NC047`), $15,900,000; t474 has the same 6.

## D. Policy questions (not decided here)

1. **How to show FY2019 sponsors.** The PDF prints codes; `sponsor` is the book's key applied, groups named
   as the key prints them (`Caucus Black, Latino and Asian`, with a comma inside). Keep, or name groups as
   t474 does (`Black, Latino and Asian Caucus`)? Either way `sponsor_raw` and `council_district` keep the
   codes.
2. How should the explorer show the lower-case `k`, and the new `description` column (no other year has
   one)?
3. FY2019 has no T&C in `source/`. Is there one to find?
