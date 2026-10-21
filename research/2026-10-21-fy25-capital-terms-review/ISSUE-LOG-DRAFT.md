# Draft #104 issue-log comments (NOT posted)

**Written:** 2026-10-21 19:40 EDT. One block per problem, in the order found, in the shape #104 asks
for. Each is meant to be its own comment on #104 once Noel approves. "PR" below means the PR that
adds this folder. Capital supporting detail and Terms & Conditions only; Schedule C and the
transparency resolutions log their own.

---

**Problem:** FY2025 had no config; the scripts knew FY2026 and FY2027 only.
**Where:** `config/capital_sd/`, `config/terms/`
**Found by:** starting point for #104
**Tried:** —
**Fix:** `config/capital_sd/fy2025.toml`, `config/terms/fy2025.toml`. Every new rule in
`code/review_capital_sd.py` is a config switch that is off by default. FY2026 and FY2027 were run
before the first change and after the last, and all 28 files compared with `cmp`: byte-identical
(so every `review_id` too). The before-run equals the committed research files. PR.
**Status:** fixed

---

**Problem:** No detail page was read: 0 rows, 72 "no header" errors.
**Where:** `Supporting-Detail-…-Council-Version-24.07.17.pdf`, pp.4–66 and 69–77
**Found by:** H4 (header not found)
**Tried:** —
**Fix:** FY2025 heads the ID column `PROJECT ID`, not `SUB ID`, so `PROJECT` names both the ID and the
title column; the header finder now accepts either. Parts I and II then give 1,327 and 181 rows and
32 / 32 `TOTALS FOR` lines tie. PR.
**Status:** fixed

---

**Problem:** The summary page's rescindments were not read.
**Where:** p.67, "Less Rescindments from Prior Capital Budgets ($ 75,000,000)"
**Found by:** C2 (a crash on a missing value)
**Fix:** a space may follow the `$`. Then additions $775,000,000 = Part I, and
$775,000,000 − $75,000,000 = $700,000,000 net. The rescindments have no list in this book. PR.
**Status:** fixed; the rescindments are flagged as unverifiable here (REVIEW A1)

---

**Problem:** Part III gave 0 organizations; 235 lines "not understood".
**Where:** pp.79–87
**Found by:** C4, C6
**Tried:** a wider amount tolerance alone (no change: the tolerance key had landed inside the TOML's
`[ink_selftest]` table, so it was never read).
**Fix:** Part III is a third export with anonymous fonts. `CIDFont+F1` is the bold face (organization
lines; checked on a 288 dpi render), so config `bold_fonts` names it. Its amounts sit 2.8–4.7 pt left
of the FY header's right edge, so `part3_amount_x1_tol = 6.0` (columns are ~65 pt apart). Then
106 / 106 organizations tie, the grand total equals Part II, and 129 / 129 budget lines agree. PR.
**Status:** fixed

---

**Problem:** Two sponsor words were in no row.
**Where:** p.50, `HN CN017` DOMINICAN AMERICAN CULTURAL CENTER: `ASIAN CAUCUS`
**Found by:** C5 (geometry says no row, the stream says `HN CN017`)
**Fix:** the sponsor cell wraps to three lines; the third falls below the row's band. A sponsor line in
no band now joins the row of the sponsor line just above it when the gap is a within-cell gap
(< 12 pt), as wrapped title lines do; the row is flagged `sponsor_wrapped_below`. No FY2026 / FY2027
word was ever in no band, so their output cannot change. The retired CSV had lost this line on 5 rows.
Test `test_sponsor_cell_wrapping_past_the_row_band`. PR.
**Status:** fixed

---

**Problem:** Part II rows looked different from Part I (5 warnings on one row).
**Where:** p.69 `ED NC128` (AG DN06Y, VISION URBANA, $62,000) vs p.44 `ED NC128` (ED DN06L, FORDHAM
UNIVERSITY COMMUNITY CENTER, $600,000)
**Found by:** C3
**Fix:** the PDF prints the same ID on two Part I rows (p.4 and p.44). Part II is now compared with the
Part I row on its own budget line. A new warn check, `C3.id_reused`, lists every such ID: 6 in FY2025
(`E CN810`, `ED NC128`, `HN CN018`, `HN CN020`, `HN CN021`, `HO CN019`), 3 of them on the same budget
line. t474 holds the same pairs. None in FY2026 or FY2027. PR.
**Status:** flagged in data (warn), REVIEW A5

---

**Problem:** 53 sponsor and 6 title warnings against the comparison source.
**Where:** `data/capital/council_capital_awards.csv`, report year 2025 (from NYC Open Data `t474-a92g`)
**Found by:** C9
**Tried:** —
**Fix:** two causes. (1) t474's accents are mojibake: cp1252 bytes read as cp437 (`OssΘ`, `Cabßn`,
`AvilΘs`, `CAF╔`), 50 rows. Config `workbook_mojibake = "cp1252"` decodes them for comparing only.
(2) For the 6 reused IDs, the check compared with the first t474 row with that ID; config
`wb_pick_by_amount` picks the one with the row's amount. Then borough, title and sponsor are equal on
1,325 / 1,325. Both are switches because (2) would also change FY2026 (`HN CN1451` would lose 2 false
warnings). PR.
**Status:** fixed; the mojibake is flagged once (`C9.workbook_text`, REVIEW A8), a note for `data/capital/`

---

**Problem:** A post-export edit read `S C HULMAN`.
**Where:** p.51, `HO CN025` ELMHURST HOSPITAL ENTRYWAY RENOVATIONS; fonts `MIZCVF+ArialMT`, `BXDXCW+ArialMT`
**Found by:** reading the edited rows (`W.edited_after_export`)
**Fix:** the edit's `C` is in a second font subset, and the word reader splits at a font change. With
config `join_touching_words`, words that touch (gap < 0.5 pt) join with no space. It is a switch
because FY2026 / FY2027 `sponsor_raw` would lose the space in `GENNARO ,` (4 rows). PR.
**Status:** fixed; the edit is flagged (REVIEW A6)

---

**Problem:** 106 vector rules not seen in pixels.
**Where:** pp.79–87, the rules between Part III organizations
**Found by:** C7
**Fix:** they are 0.12 pt, 50% grey: under half a pixel at 300 dpi. Config `c7_hairline_pt = 0.25`
counts rules thinner than that in one warning instead of 106. Ink coverage (C8) is 0 on those pages,
so nothing hides under them. PR.
**Status:** flagged in data (warn)

---

**Problem:** Part II has 40 rows that are not in Part I.
**Where:** pp.71–72: 39 `PV MA…` rows on `0N` lines ($57,657,000 FY2025, no sponsor); p.74
`PV CT001` 126 PV207APLO APOLLO THEATER on `PV DN027` ($2,500,000)
**Found by:** C3
**Fix:** none. The `MA` / `0N` series is configured as expected (as FY2027); `PV CT001` falls outside it,
so it is the one critical item. All 40 are in the Part II total and Part III; none is in Part I, the
p.67 additions or t474.
**Status:** open: question for Council Finance (REVIEW A2, A7)

---

**Problem:** 2 Part I amounts are not in t474.
**Where:** p.58 `P CN175` ($10,000,000 FY2026), p.44 `ED NC091` ($6,000,000 FY2026)
**Found by:** C9
**Fix:** none; t474 holds FY2025 amounts only. `families/capital.md` §"FY2025 out-years" predicted them.
**Status:** flagged in data (warn), REVIEW A3, A4

---

**Problem:** FY2025 T&C needed no code change, but differs from FY2026's.
**Where:** `FY25-Terms-and-Conditions-1.pdf`
**Found by:** T1–T7 on the first run
**Fix:** config only: a bare page number at the foot of every page (top 733 pt) is the furniture; the
FSR table (p.6) is under #16, not #15. 65 conditions, 234 / 234 heading lines placed, 0 characters
lost, 0 uncovered ink, 28 / 28 table cells agree. PR.
**Status:** fixed

---

**Problem:** The PDF's own wording trips T3 in 3 conditions.
**Where:** p.19 #57 (`109, 011, and 112` for DOHMH; the heading has `111`); pp.24–25 #64, #65 ("units of
appropriations")
**Found by:** T3
**Fix:** none; the heading is kept as printed.
**Status:** flagged in data (warn), REVIEW C2, C3

---

**Problem:** Retired FY2025 T&C CSV puts headings into text, drops hyphens and units.
**Where:** `data/fy25/terms/fy25_terms_and_conditions.csv`, 19 conditions
**Found by:** T7
**Fix:** headings parsed into agency groups, each with its units and budget lines: 234 / 234 heading
lines placed. The FSR table is its own file. Printed hyphens kept (`education - for`, #15). PR.
**Status:** fixed here; the retired CSV is not edited

## Proposed DATA-ANOMALIES entry (not applied)

> **§NN. FY2025 capital and T&C, re-read from the PDFs (GitHub #104).** `research/2026-10-21-fy25-capital-terms-review/`.
> Capital: 32 / 32 printed totals tie; Part I equals NYC Open Data `t474-a92g` on all 1,325 of its
> FY2025 rows (2 FY2026-only amounts are not in t474). t474's FY2025 accents are cp437 mojibake
> (50 rows). The PDF prints 6 project IDs on two rows each, so `sub_id` is not a key. Part II carries
> 39 `MA` / `0N` rows ($57,657,000) and `PV CT001` ($2,500,000) that are not Council additions
> (meaning unconfirmed). The PDF was edited after export on p.51. T&C: 65 conditions; the retired CSV
> put headings into the text of 14, the FSR table into #16, dropped hyphens in 4, and lost units in 9.
