# Draft #106 issue-log comments (NOT posted)

**Written:** 2026-10-21 22:18 EDT. One block per problem, in the order found, in the shape #106 asks
for. Each is meant to be its own comment on #106 once Noel approves. "PR" below means the PR that adds
this folder. Capital supporting detail and Terms & Conditions only.

---

**Problem:** The run crashed comparing with NYC Open Data.
**Where:** `data/capital/council_capital_awards.csv`, report year 2023, `E CN136` on `E D001`
(t474 row `row-s7nq.aj89~8mbm`, `row_flag = split_record_amount_unknown`)
**Found by:** C9 (an empty amount)
**Tried:** nothing else; the row is a known broken t474 record (RECONCILIATION §2)
**Fix:** a comparison row with no amount is set aside, listed with the PDF row that has its ID and budget
line, and not joined on amount (`C9.workbook_no_amount`). The PDF prints $150,000 (p.11), which is what
the record's stray fragment `row-fpup_sjfd_kina` carries; with it, t474's $879,526,000 becomes the
p.71 total, $879,676,000. Only FY2020, FY2022 and FY2023 have such rows; FY2024–FY2027 output unchanged. PR.
**Status:** fixed; flagged in data (REVIEW A7)

---

**Problem:** 19 uncovered ink regions.
**Where:** capital book p.1 (the cover), 609–686 × 428–505 pt
**Found by:** C8
**Tried:** looking at the render: it is the City seal, drawn as two images. No earlier year's cover had one
**Fix:** config `ink_cover_image_pages = [1]`: on the pages named, a picture's box counts as covered, and
`checks.txt` says so. Images on any other page stay uncovered. Then 0 regions; the self-test (hiding
`AG NC002`, p.4) still gives 66. PR.
**Status:** fixed

---

**Problem:** 89 vector rules not seen in pixels.
**Where:** pp.82–89, between Part III organizations (0.12 pt, 50% grey)
**Found by:** C7
**Fix:** config `c7_hairline_pt = 0.25`, as FY2025 and FY2024: counted in one warning. Ink coverage is 0 there.
**Status:** flagged in data (warn)

---

**Problem:** 90 sponsor warnings and 5 title warnings against Open Data.
**Where:** report year 2023 of `data/capital/council_capital_awards.csv` (from t474-a92g)
**Found by:** C9
**Fix:** two config switches. `workbook_mojibake = "utf-8"`: t474's FY2023 accents are UTF-8 read as cp437
(`Avil├⌐s`, `Cab├ín`, 74 rows), as FY2024's. `wb_pick_by_amount = true`: two ID numbers are printed by two
agencies on one budget line (`HD NC040` p.50 / `HR NC040` p.51 on `HD D020`; `HA CN001` / `P CN001` p.48 on
`HA D001`), and C9 drops the agency prefix, so each is compared with the t474 row that has its amount, as
FY2025. Then 1,372 / 1,393 sponsors and 1,391 / 1,393 titles agree. The 21 sponsors left are real: 15 `RR`
rows (PDF blank, t474 `NA`) and 6 `BLAC` abbreviations in t474.
**Status:** flagged in data (warn), REVIEW A4, A6, A8

---

**Problem:** 15 Part I rows with `RR` IDs, no sponsor, 4 on borough `A`.
**Where:** pp.46–69: `E RR001`–`E RR003`, `HA RR001`–`HA RR003`, `HD RR001`, `HD RR002`, `HL RR001`,
`HO RR001`, `P RR001`–`P RR003`, `PO RR001`, `PW RR001`; $22,633,000
**Found by:** C9 (sponsor blank vs t474 `NA`), then reading p.48
**Fix:** none to the data; kept as printed. Config `flag_id_series = ["RR"]` lists them in one warning
(`C3.id_series`). Two sit beside a near-twin on the same line: `HD RR001` $4,280,000 / `HD NC040`
$4,279,000 (Cypress Hills, `HD D020`); `HA RR002` $2,681,000 / `HA CN001` $810,000 (Smith Houses,
`HA D001`). OMB's adopted lines include both rows of each pair.
**Status:** open: question for Council Finance (REVIEW A3)

---

**Problem:** One budget line differs from OMB's adopted capital budget.
**Where:** `E D001`: PDF Part I $224,446,000; OMB `46m8-77gv` release 2022-07-15 $229,846,000
**Found by:** summing Part I by budget line against `data/capital/council_vs_omb_by_budget_line.csv`
(report only, ad hoc)
**Fix:** none. 129 of 130 lines match in FY2023 and FY2024. The PDF closes $150,000 of t474's gap on this
line (`E CN136`); $5,400,000 remains on OMB's side.
**Status:** open (REVIEW A5)

---

**Problem:** The retired FY2023 CSVs.
**Where:** `data/fy23/capital/fy23_capital_projects.csv`, `data/fy23/terms/fy23_terms_and_conditions.csv`
**Found by:** an ad hoc comparison (capital) / T7 (terms)
**Fix:** none to them. Capital: same 1,547 rows, every amount and borough equal; the comma after
`SPEAKER` dropped on 265 rows, a wrapped sponsor line moved into the title on 10. Terms: same 60
conditions; capital budget lines in `units`, the FSR table in #24's text, printed hyphens and dashes
dropped.
**Status:** fixed here; the retired CSVs are not edited

## Proposed DATA-ANOMALIES entry (not applied)

The same text as the README's "Proposed DATA-ANOMALIES entry":

> **§NN. FY2023 capital and T&C, re-read from the PDFs (GitHub #106).** `research/2026-10-21-fy23-capital-terms-review/`.
> Capital: 32 / 32 printed totals tie; Part I equals NYC Open Data `t474-a92g` on all 1,411 of its
> FY2023 amounts, and adds the one t474 lost to a broken record (`E CN136`, $150,000), so t474's
> $879,526,000 becomes the PDF's $879,676,000. t474's FY2023 accents are UTF-8 read as cp437 (74 rows).
> 15 Part I rows carry `RR` IDs ($22,633,000, no sponsor, 4 on borough `A`). Part II carries 39 `MA` /
> `0N` rows ($78,861,000), not Council additions. Against OMB's July 2022 adopted budget, 129 of 130
> lines match; `E D001` differs by $5,400,000. The retired capital CSV drops the comma after `SPEAKER`
> (265 rows). T&C: the PDF prints no condition numbers; 60 conditions in book order, as the retired CSV
> numbered them; it put the FSR table into condition 24's text.
