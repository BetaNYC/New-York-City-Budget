# Draft #109 issue-log comments (NOT posted)

**Written:** 2026-10-22 00:25 EDT. One block per problem, in the order found, in the shape #109 asks
for. Each is meant to be its own comment on #109 once Noel approves. "PR" below means the PR that adds
this folder. Capital supporting detail only: FY2020 has no Terms & Conditions in `source/`.

---

**Problem:** The book has Part I only.
**Where:** pp.2–79 Part I, p.80 summary; no contents, dividers, Part II or Part III
**Found by:** triage (page furniture, every page)
**Tried:** the FY2022 shape of config; C3 would flag all 179 `DN` rows as missing from Part II, and C4
crashed on the missing Part III total
**Fix:** when the page map has no Part II (III) pages, C3 (C4) says "this book prints no Part II (III);
nothing to compare". No other year is affected. PR.
**Status:** fixed

---

**Problem:** IDs that are not two letters and three to five digits.
**Where:** p.46 `E CNA02`–`CNA09`; p.54 `HL NC02`; p.79 `TF CN90` (twice)
**Found by:** triage (a regex over each line's first two words)
**Fix:** config `extra_sub_ids` (added for FY2022) lists the ten. Then 24 / 24 `TOTALS FOR` lines tie on
count. PR.
**Status:** fixed

---

**Problem:** One title split into two blocks.
**Where:** p.39, `E CN817` (C5: 21 title blocks for 20 rows; three words in no row)
**Found by:** C5 (critical)
**Tried:** the render: its second title line sits 16.2 pt below the first, past the 12 pt block gap and
more than the smallest gap between rows (15.84 pt), so no spacing rule can tell. The cause is a
MicrosoftSansSerif space on a line of its own, typed after export; two more such spaces sit on top of
letters (`ACCESSIBLEBATHROOMS ATPARK`), and one in `E CN832` (`(K003)GYMNASIUM`)
**Fix:** config `title_blank_line = [[39, "E CN817"]]` joins the row's next title block, with a warning.
C5: 27,501 words agree, 0 disagree. PR.
**Status:** fixed (flagged in data, REVIEW B7)

---

**Problem:** Title and sponsor warnings that were the comparison's fault.
**Where:** pp.61, 78–79: `MT CN001` / `TF CN001` / `T CN001`, `HW CN905` / `P CN905`
**Found by:** C9 (9 title and several sponsor warnings, every amount matched)
**Tried:** checking t474: the rows are identical once the agency prefix is kept. C9 drops the prefix
(FY2027's workbook prints none), and FY2020 uses one number with several prefixes on one line at one
amount
**Fix:** config `wb_full_id = true` compares the full ID; default off. Title warnings 9 → 3. PR.
**Status:** fixed

---

**Problem:** Three lower-case boroughs.
**Where:** `F CN003` p.48, `HW CN006` p.60, `PV NC037` p.73: `r`
**Found by:** C6 (critical), C9
**Fix:** none; kept as printed (t474 and the retired CSV have `R`).
**Status:** flagged in data (REVIEW A1)

---

**Problem:** The Open Data comparison: two broken records.
**Where:** report year 2020 of `data/capital/council_capital_awards.csv` (t474-a92g): `E CN817`, `E CN832`
**Found by:** C9
**Fix:** the blank-amount rule (added for FY2023) lists both; the PDF prints $170,000 and $300,000, which
close t474's $700,740,000 to the PDF's $701,210,000. Config `workbook_mojibake = "utf-8"` (1 row).
**Status:** flagged in data (REVIEW B6, B7)

---

**Problem:** OMB's adopted budget is $7,353,000 higher on 11 Council-series lines.
**Where:** OMB `46m8-77gv`, release 2019-07-09, against Part I by budget line
**Found by:** ad hoc comparison (report only)
**Fix:** none; t474 has no amount the PDF lacks, so this is between OMB and the Council's book.
**Status:** open: note for `data/capital/RECONCILIATION.md` (REVIEW B2)
