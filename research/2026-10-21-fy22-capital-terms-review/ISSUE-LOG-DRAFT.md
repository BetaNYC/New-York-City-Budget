# Draft #107 issue-log comments (NOT posted)

**Written:** 2026-10-21 22:50 EDT. One block per problem, in the order found, in the shape #107 asks
for. Each is meant to be its own comment on #107 once Noel approves. "PR" below means the PR that adds
this folder. Capital supporting detail and Terms & Conditions only.

---

**Problem:** IDs that are not two letters and digits.
**Where:** capital book p.4 `AG TANC1`; p.63 `P TANC1`; p.70 `PW TANC1`–`TANC3`; Part II p.75 `HL KBP01`,
p.82 `PW KBP01`, `PW KBP02`, `PW MBP01`
**Found by:** triage, before the first run (a regex over each line's first two words)
**Fix:** config `extra_sub_ids` lists the six ID numbers in full; an anchor may be one of them. Default:
none, so FY2023–FY2027 are unchanged. Then 34 / 34 `TOTALS FOR` lines tie on count. PR.
**Status:** fixed

---

**Problem:** A Part III organization total did not equal its rows.
**Where:** p.86, EARTH MATTER NY, INC. prints `($72,000)` (the `$` inside the brackets); DOWNTOWN
ART/ALPHA OMEGA YOUTH CENTER appeared $72,000 short
**Found by:** C4 (critical: an organization line with 3 amounts, and one whose rows did not add up)
**Tried:** looking at the render: the page is right; the reader did not know the `($…)` form
**Fix:** `AMOUNT_RE` reads `($72,000)` as −72,000 (`money()` already did). 99 / 99 organization lines
tie. FY2023–FY2027 unchanged. PR.
**Status:** fixed

---

**Problem:** Four Part II rows outside the `MA` / `0N` series.
**Where:** `HL KBP01` (p.75), `PW KBP01`, `PW KBP02`, `PW MBP01` (p.82), on `KN` / `MN` lines; $3,479,000
net, `PW MBP01` at −$72,000
**Found by:** C3 (critical)
**Fix:** none; kept as printed. They are in the Part II total and in Part III.
**Status:** open: question for Council Finance (REVIEW A1)

---

**Problem:** 28 sponsor cells hold a number.
**Where:** `CD 22` (10 rows) and `CD 48` (18 rows), pp.17–82
**Found by:** C6 (critical)
**Fix:** none; the PDF names the district where a seat has no member (t474: `Vacant 22`, `Vacant 48`).
**Status:** flagged in data (REVIEW A2)

---

**Problem:** A lower-case borough.
**Where:** p.60, `P CN039`, `x`
**Found by:** C6 (critical), C9
**Fix:** none; kept as printed (t474 and the retired CSV have `X`).
**Status:** flagged in data (REVIEW A3)

---

**Problem:** The Open Data comparison: a broken record, mojibake and a reused ID.
**Where:** report year 2022 of `data/capital/council_capital_awards.csv` (t474-a92g)
**Found by:** C9
**Fix:** the blank-amount rule added for FY2023 lists `E CN673` (the PDF prints $55,000, which closes
t474's total to the PDF's); config `workbook_mojibake = "utf-8"` (32 rows, `┬á` no-break spaces);
`wb_pick_by_amount = true` for `PV NC101`. `E CN884` is printed twice on one line with one amount, so no
key tells its rows apart (REVIEW B6). Then 1,490 / 1,490 amounts, 1,365 sponsors and 1,458 titles agree.
**Status:** flagged in data (warn), REVIEW B3, B6, B8, B9

---

**Problem:** 15 Part I `TA` rows, all borough `A`, 13 with no sponsor.
**Where:** pp.4–70, $13,394,000
**Fix:** config `flag_id_series = ["TA"]`: one warning naming every row.
**Status:** flagged in data (REVIEW B4)

---

**Problem:** The T&C prints no page numbers or other furniture.
**Where:** `FY22-Terms-and-Conditions_FINAL.pdf`, every page
**Found by:** triage (no character above 70 pt or below 705 pt that is not body text)
**Fix:** config furniture pattern `(?!)`, which matches nothing. Unnumbered conditions as FY2023
(`numbered = false`); `table_pages = [8, 9]`. T4 then finds 0 characters outside a condition or the table.
**Status:** fixed

---

**Problem:** Two agency headings with no proper code.
**Where:** p.10 #26 `Department of Education (40)`; p.11 #28 `Department of Housing Preservation and
Development`
**Found by:** T2 (`T2.no_agency_code`)
**Fix:** none; kept as printed, code blank.
**Status:** flagged in data (REVIEW D2, D3)

---

**Problem:** The FSR table's months are out of order.
**Where:** pp.8–9: SEPTEMBER 2022, OCTOBER 2022, DECEMBER 2022, FEBRUARY 2022, MARCH 2021, MAY 2022
**Found by:** reading T5's cells (already noted in `families/transparency-and-terms.md`)
**Fix:** none; kept as printed.
**Status:** flagged (REVIEW D8)

---

**Problem:** The retired FY2022 CSVs.
**Where:** `data/fy22/capital/fy22_capital_projects.csv`, `data/fy22/terms/fy22_terms_and_conditions.csv`
**Found by:** an ad hoc comparison (capital) / T7 (terms)
**Fix:** none to them. Capital: same 1,641 rows, every amount equal; the comma after `SPEAKER` dropped on
236 rows, wrapped sponsors moved into titles on 21, `x` upper-cased. Terms: 50 rows, but #26 lost and #28
split in two, so #26–#28 are misaligned; capital lines in `units`, the FSR table in #21's text,
hyphens dropped.
**Status:** fixed here; the retired CSVs are not edited

## Proposed DATA-ANOMALIES entry (not applied)

The same text as the README's "Proposed DATA-ANOMALIES entry".
