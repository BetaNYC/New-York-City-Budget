# Draft #103 issue-log comments (NOT posted)

**Written:** 2026-10-21 00:32 EDT. One block per problem, in the order found, in the shape #103 asks
for. Each is meant to be its own comment on #103 once Noel approves. "PR" below means the PR that
adds this folder. Capital supporting detail and Terms & Conditions only; Schedule C and the
transparency resolutions log their own.

---

**Problem:** The FY2027 review scripts had FY2027 written into them (PDF, page map, FY columns, file names).
**Where:** `code/review_capital_sd.py`, `code/review_terms.py`
**Found by:** reading them before the FY2026 run
**Tried:** —
**Fix:** every year-specific value moved to `config/capital_sd/fy<FY>.toml` and
`config/terms/fy<FY>.toml`; `--fy` selects one (default 2027). FY2027 output compared before and after
with `cmp`: all 14 files byte-identical (so every `review_id` too). PR.
**Status:** fixed

---

**Problem:** FY2026's capital book is laid out differently from FY2027's.
**Where:** `Fiscal-2026-Capital-Budget-Supporting-Details-1.pdf`, all 86 pages
**Found by:** triage (`fy26_capital_sd_pages.csv`)
**Tried:** the FY2027 page map and rotation rules: they do not fit.
**Fix:** FY2026 config. Parts I (pp.4–64) and II (pp.67–76) are upright, Part III (pp.78–86) is
rotated 90°; summary on p.65; FY columns FY2026–FY2029; Part II is a second export (fonts
`AAAAAA+` / `AAAAAB+`). The H3 check confirms all 86 pages against the map. PR.
**Status:** fixed

---

**Problem:** Negative amounts were not read.
**Where:** p.70 `PV MA0005` (`-183,000`), p.81 MANHATTAN COMMUNITY ACCESS CORPORATION (`$(183,000)`,
`(183,000)`)
**Found by:** C4 (Part III grand total off by $183,000; 6 unplaced words; one org line with 3 amounts)
**Tried:** —
**Fix:** amounts may carry a minus or accounting parentheses. Part III then ties: 125 / 125
organizations, grand total = Part II, 151 / 151 budget lines. PR.
**Status:** fixed; the negative row is flagged for review (REVIEW A8)

---

**Problem:** The workbook comparison matched 0 rows.
**Where:** `data/capital/council_capital_awards.csv`, report year 2026
**Found by:** C9
**Tried:** —
**Fix:** FY2026 workbook IDs keep their agency prefix (`E CN0001`); FY2027's do not (`CC0001`). Both
are compared on the part after the space. Then 1,253 / 1,261 amounts match. PR.
**Status:** fixed

---

**Problem:** The workbook files two projects under one ID.
**Where:** p.50, `HN CN1451` ($250,000, SPEAKER) and `HN CN0092` ($125,000, POWERS); workbook rows 61
and 875 are both `HN CN1451`
**Found by:** C9 (one PDF-only and one workbook-only key, same line and amount)
**Tried:** —
**Fix:** none; the PDF is kept. The workbook's own description for row 61 cites `HN CN0145`.
**Status:** flagged in data (REVIEW A5); a note for `data/capital/RECONCILIATION.md`

---

**Problem:** 7 printed rows are not in the workbook at all.
**Where:** pp.4, 51, 64: sponsor `ADMIN`, $0 FY2026, $2,950,000 FY2027 in total
**Found by:** C9
**Fix:** none; kept as printed. They are in Part I, Part II and every total.
**Status:** flagged in data (warn), REVIEW A6

---

**Problem:** Part II has 42 rows that are not in Part I.
**Where:** pp.70–72: 39 `PV MM…` rows on `0N` lines ($62,073,000, no sponsor), and 3 `PV MA…` rows
(`MA0022` on `0N06Z` $2,500,000; `MA0007` on `DN176` $500,000; `MA0005` on `MN07D` −$183,000)
**Found by:** C3
**Tried:** —
**Fix:** none. The `MM` / `0N` series is configured as expected (FY2027's twin is `MA` / `0N`); the
3 `MA` rows fall outside it, so each is a critical review item. All 42 are in the Part II total and
Part III, not in Part I, the p.65 additions, or the Council workbook.
**Status:** open: question for Council Finance (REVIEW A1, A3, A7, A8)

---

**Problem:** The PDF was edited after export on 4 pages.
**Where:** p.56 `P CN1114` (`, POWERS`), p.59 `PV NC1130` (`, WON`), pp.61 and 74 `PV NC1031`
(`, SALAAM`); font `KGLUJE+ArialMT`
**Found by:** font census; geometry vs stream (C5: 155 words out of row order on those pages)
**Fix:** far stream rows count as "no opinion", as for FY2027. The 8 near disagreements keep the
geometry read: 4 are a `0` both rows print, 4 sponsors equal the Council workbook.
**Status:** flagged in data (warn), REVIEW A4

---

**Problem:** An unmapped tab glyph shows up as `(cid:9)` in 4 titles.
**Where:** pp.35–41, `E CN1588`, `E CN1564`, `E CN1566`, `E CN0450`, between the `B:` and `S:` codes
**Found by:** C9 title check
**Fix:** `title_raw` keeps it; `title` reads it as a space. PR.
**Status:** fixed

---

**Problem:** Rescindments can't be checked.
**Where:** p.65, "Less Rescindments from Prior Capital Budgets ($26,920,000)"
**Found by:** C2
**Fix:** only the arithmetic ties: $779,320,000 − $26,920,000 = $752,400,000. No list in the book.
**Status:** flagged in data (warn)

---

**Problem:** FY2026 T&C differs in small ways from FY2027's.
**Where:** `FY26-Terms-and-Conditions-1.pdf`: `Page N of 29` at the head of every page; #5 and #25 print
`Units of Appropriation`; bodies say "units of appropriation 401, …" without "numbers"; budget lines
use U+2010 (`HB‐0278`)
**Found by:** T2, T3, T4
**Tried:** the FY2027 rules: 29 T3 warnings, the page header inside condition text.
**Fix:** furniture from config; `Units?`; "numbers" optional; U+2010 compared as `-`. FY2027 output
unchanged. T3 then 67 / 68 (#67's own typo "appropriations"). PR.
**Status:** fixed; #67 flagged (REVIEW C3)

---

**Problem:** Superscript ordinals in the FSR table were read out of order (`nd October 2`).
**Where:** p.8, #15, three issue dates
**Found by:** reading the FSR output (T5 could not see it: both lattices share the cell reader)
**Fix:** a character joins a cell line when it overlaps the line's height by half its own height.
FY2027 output unchanged. Test `test_fsr_superscript_ordinals_stay_in_place`. PR.
**Status:** fixed

---

**Problem:** Retired FY2026 T&C CSV puts headings into text and drops units.
**Where:** `data/fy26/terms/fy26_terms_and_conditions.csv`, 18 conditions (#5, #15, #25, #29, #39, #53–#55,
#59–#68)
**Found by:** T7
**Fix:** heading parsed into agency groups, each with its units and budget lines: 245 / 245 heading
lines placed. The FSR table is its own file. `code/review_terms.py`, PR.
**Status:** fixed here; the retired CSV is not edited

---

## Proposed DATA-ANOMALIES entry (not applied)

> **§NN. FY2026 capital and T&C, re-read from the PDFs (GitHub #103).** `research/2026-10-21-fy26-capital-terms-review/`.
> Capital: 33 / 33 printed totals tie; Part I equals the Council workbook on 1,253 / 1,261 non-zero
> amounts (7 `ADMIN` FY2027 rows are not in the workbook; the workbook files `HN CN0092` under
> `HN CN1451`). Part II carries 39 `MM` / `0N` rows ($62,073,000) and 3 `MA` rows (one of them
> −$183,000) that are not Council additions (meaning unconfirmed). The PDF was edited after export
> on pp.56, 59, 61, 74 (sponsors added). Amounts can be negative. T&C: 68 conditions; the retired
> CSV put headings into the text of 18 and dropped units in 12. Hyphens are U+2010 as printed.
