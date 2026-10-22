# Draft #111 issue-log comments (NOT posted)

**Written:** 2026-10-22 02:25 EDT. One block per problem, in the order found, in the shape #111 asks
for. Each is meant to be its own comment on #111 once Noel approves. "PR" below means the PR that adds
this folder.

## Capital supporting detail

**Problem:** The capital book is filed as "ResoA" but holds the supporting detail.
**Where:** `source/FY18/FY18-Sec254-Capital-ResoA-M499-Res1534-Res1535.pdf`, 96 pp.
**Found by:** triage (p.1 title, contents p.2, `PROJECT ID … SPONSOR` header on pp.4–83)
**Fix:** read with the supporting-detail script (`config/capital_sd/fy2018.toml`). Encrypted with an
empty password; opens as is. PR.
**Status:** fixed

---

**Problem:** Part III amounts sit left of their column header.
**Where:** pp.85–96: amounts end up to 4.6 pt left of the `FY 2018` header's right edge
**Found by:** the first run (the grand total line had no FY2018 amount)
**Fix:** config `part3_amount_x1_tol = 6.0` (as FY2022, FY2025). Then C4: 138 / 138 organizations, the
grand total and 170 / 170 budget lines tie. PR.
**Status:** fixed

---

**Problem:** No summary page and no comparison source.
**Where:** the whole book; `data/capital/` has no FY2018 rows (no workbook; t474 starts at FY2019)
**Found by:** triage; C9 would list every row as missing from an empty source
**Fix:** C2 says "no summary page" (the FY2019 path); config `no_comparison_source` makes C9 say so. The
35 printed totals (35 / 35 tie) and Parts II/III are the only checks. PR.
**Status:** fixed (no outside check exists; REVIEW B1)

---

**Problem:** A seat printed as the sponsor.
**Where:** pp.43–44, `E CN765`–`E CN779`: `DISTRICT 28` ($5,000,000)
**Found by:** C6 (a number in the sponsor cell; critical)
**Fix:** config `sponsor_digit_ok = ["DISTRICT 28"]`: listed as warnings, kept as printed. PR.
**Status:** flagged in data (REVIEW B3)

---

**Problem:** Three `TA` rows in Part II only.
**Where:** p.72 `AG TA001` $500,000; p.80 `HH TA001` $693,000, `HH TA003` −$100,000
**Found by:** C3 (critical)
**Fix:** none; kept as printed, and in Part II's totals.
**Status:** open: needs_info (REVIEW A1)

---

**Problem:** Part III hairlines are below pixel size.
**Where:** pp.85–96, 138 rules of 0.04–0.1 pt
**Found by:** C7
**Fix:** config `c7_hairline_pt = 0.25` (as FY2022, FY2023): counted, not listed. PR.
**Status:** fixed

## Terms & Conditions

**Problem:** Six conditions do not open "As a condition".
**Where:** #2 p.3 "Where the Commissioner", #3 p.4 "The appropriations", #4–#5 pp.5–6 "In relation to",
#21 p.22 and #29 p.30 "No later than"; and #14 (p.15) opens at 114 pt
**Found by:** T1 (33 headings, 26 openings; critical)
**Fix:** config `opening_phrases` lists the five openings and `body_x0_max = 120`; T1 counts 33. PR.
**Status:** fixed

---

**Problem:** "All Project Lines – All Projects" read as a second agency.
**Where:** #2 p.3, #3 p.4, under "Capital Budget"
**Found by:** T2 (two agencies with no code), the "kind" column (capital+expense)
**Fix:** config `all_lines_headings`: kept as printed in `budget_lines`. PR.
**Status:** fixed

---

**Problem:** A word of the FSR table printed below the table, and two columns swapped.
**Where:** p.15: "Summary" 1.7 pt below the bottom rule (it had joined #14's text); the header prints
"Anticipated Meeting Date" before "Issue Date"; header in mixed case
**Found by:** a test (#14's text should end "for the following dates:")
**Fix:** config `fsr_table.overflow_below_pt`, `columns_3_4`, `header_starts`. "Summary" goes to the last
row, with a warning. PR.
**Status:** fixed (REVIEW B4)
