---
title: "Audit of ba90fce — what is salvageable and what must be rebuilt"
created: 2026-08-13
type: audit
status: open
tags: [nyc-budget, data-quality, audit, schedule-c]
---

# Audit of `ba90fce` — read this before touching either audit script

**Report generated:** 2026-08-13
**Verdict: do not merge `ba90fce`.** Its conclusions about the appendices are right; its evidence is
not. Two of the four tests it rests on cannot fail, and one headline figure is wrong in the
flattering direction.

Retraction posted to [#57](https://github.com/BetaNYC/New-York-City-Budget/issues/57#issuecomment-5282646717).
Raw findings, all 124 with evidence: [`findings-raw.md`](findings-raw.md).

## The one thing to carry forward

**The Council's disclosure workbooks answer the appendix question directly, and were never opened.**
`source/expense-funding-disclosure/funded_disclosure_FY*.xlsx` carries a per-award `source` column
naming the funding stream. `code/parse_expense_disclosure.py` already reads it.

Verified by hand, FY2027:

```
disclosure TOTAL                     $705,564,000   10,040 rows
  streams (Aging / Local / Youth)     $49,799,000    3,860 rows
  body (excluding streams)           $655,765,000
parser category total                $655,764,999
DELTA                                          $1

repo FY2027 appendix CSVs            $49,799,000    3,860 rows   == the disclosure streams exactly
```

The streams sit **outside** the categories, to one dollar. That settles additive-vs-subset on the
Council's own record, on a field built for the question. `ba90fce` instead ran four regex tests over
`pdftotext` output and got the right answer for reasons that do not hold.

## Salvageable

| Piece | State |
|---|---|
| `code/verify_amounts_against_pdf.py` | **Method sound, implementation not trustworthy.** Reading the adopted PDF with a second engine is the right idea. See the fix list below. |
| The conclusion that appendices are **additive** | **Correct.** Re-establish it from the disclosure, not from the four regex tests. |
| The withdrawal of the 3 `neighbour_bleed` findings | **Holds.** The PDF prints those three rows intact; they were false positives of a proximity heuristic. |
| `data/AMOUNT-PDF-VERIFICATION.csv` | Regenerate after fixing `pdf_line`; the verdicts themselves need the stricter pin first. |

## Must be rebuilt or deleted

| Claim in `ba90fce` | Why it fails |
|---|---|
| "68.3% of the Council's own printed GRAND TOTALs" | **The PDFs print no grand total.** `grep -ic "grand total"` → 0 in every year; `655,764,999` appears nowhere in the FY2027 PDF. The figure is our own parser summing category subtotals, and it under-counts (categories with no summary block contribute $0, in 11 of 13 years). The ratio is also not apples-to-apples — numerator includes the streams, denominator excludes them. Both consistent pairings give ~61%. |
| FY2027 "appendices supply 98% of the shortfall" | **Coincidence between two unrelated ~$50M quantities.** `research/phase1-source-comparability/comparison-2027.md` already attributes that exact gap to "62 post-adoption rows plus two $1 extraction errors." The FY2027 body prints post-adoption language 44 times, ~$50.5M. |
| Test 3, "never overshoots" | **Cannot fail.** Award rows under-capture their own categories every year, so no overshoot is possible whatever the truth. 6 of its 13 rows had zero parsed appendix data. |
| Test 1, "own page numbering from FY2019" | Regex artifact — it required the literal token `PAGE`. FY2016/17/18 restart at 1 but print `……….1-25`. |
| Test 2, "stream names appear zero times" | FY2024-era naming applied to all 13 years. FY2016–20 Appendix C is *Youth Initiatives*; FY2021–22 Appendix B is *Local Discretionary*. The needle could not match — a test that cannot fail. Output also printed 1, not 0, for FY2026. |
| "$447,500 upper bound on double-counting" | Not a bound. It is the odd-amount *subset*; all twins is **$46,034,500**, 103× larger. Key was also narrower than the standing `(EIN, amount)`. |
| "All 18 rounding rows" | `fy17:163` confirms against a **one-row EIN-column offset printed in the FY2017 PDF itself** (visible in pdfplumber at coordinate level). Cross-engine agreement cannot detect an error in the printed document — which voids the "two engines, same bytes" argument for this class. |
| "None is an amount defect" | 11 of the 440 are `org_merged`/`org_prose` per this repo's own `validate_data.py`, whose comment says the amount "may belong to a DIFFERENT organization." 4 got full `pdf_confirms` and were excluded from "needs a human." |
| The controls (11.0%, 5.0%, 14.1%) | **Implemented nowhere.** No seed, no control path. Not re-derivable by anyone. An independent rotation control over 3,088 real rows put the false-confirm rate at **13.9%** — against the 14.1% that got the first version rejected. |

## Fix list for `verify_amounts_against_pdf.py`

1. `pdf_lines()` → `fh.read().split("\n")`, not `.splitlines()`. Form feeds are counted as lines, so
   all 440 `pdf_line` values are 10–468 too high against the cache the script itself writes.
2. Commit the controls as a `--control` path with a fixed seed. A measurement nobody can re-run is
   not a measurement.
3. Require a stricter pin before the word "confirms": exactly one printed line carrying our EIN,
   our amount **and** our name. Re-measure the rotation control against it.
4. Never emit `pdf_confirms` for a row `validate_data.py` flags `org_merged`/`org_prose`. Give it
   its own verdict and count it in "needs a human."
5. Add a printed-column-integrity check: the disclosure's name for that EIN must match the name on
   the confirming line. A mismatch is a source-print defect (`fy17:163`), not a confirmation.
6. Fix `test_leading_wrapped_column` — it passes with `names_us()` replaced by `return False`.

## Fix list for `audit_appendix_overlap.py`

Rewrite around the disclosure workbooks. Assert per year: (a) appendix CSV totals == disclosure
stream totals, (b) category total + stream total == disclosure total. Demote the four regex tests to
corroboration, or drop them. Delete `pairs()` — its four outputs are computed over all 13 PDFs and
never printed, and its `MONEY` regex requires a literal `$` that FY2016–FY2020 appendix pages do not
print, so those years silently scan to zero.

`test_round_thousand_split` asserts literal arithmetic and never calls `twins()`; six mutations of
`twins()` — including making every row a twin and collapsing the bound to $0 — all passed. `twins()`
has no coverage at all.

## The lesson, stated once

The repo's own rule is *a regex may nominate; only the Council's data may decide.* `ba90fce` broke
it while quoting it. The deciding evidence was one import away, in a file the repo already parses,
and four pattern-matching tests were built instead. Three of those four could not have failed.
