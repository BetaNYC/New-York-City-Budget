# Draft #106 issue-log comments: FY2023 transparency resolutions (NOT posted)

**Written:** 2026-10-21 22:20 EDT. One block per problem, in the order found, in the shape #106
asks for. Each is meant to be its own comment on #106 once Noel approves. "PR" means the PR that
adds this folder; "promotion PR" the one that writes `data/fy23/pdf/transparency/`. The reader
already handled FY2024–FY2026, so this year needed five small code changes. (#106's "Local
category lost two $5,000 rows" note is about Schedule C, not this family.)

---

**Problem:** Starting point. The committed FY2023 CSVs come from the old text-order parser.
**Where:** 14 PDFs, 697 pages (656 chart pages)
**Found by:** review (starting point)
**Tried:** the FY2024 reader with a new config (`config/transparency/fy2023.toml`).
**Fix:** first run: 4 hard checks failed (T3, T5, T6, T11) and the crop step crashed on a
page-0 item. Each cause is below.
**Status:** fixed

---

**Problem:** A caption with no "#" dropped a whole chart.
**Where:** Reso 01 p.81, "CHART 41: Neighborhood Development Grant Initiative - Fiscal 2022"
**Found by:** T3 (caption missing; chart numbers not 1..55) and T5 (4 EIN-shaped words, 0 rows)
**Tried:** —
**Fix:** the caption reader takes "CHART n" without "#"; flagged `W.caption_format`. 4 rows back. PR.
**Status:** fixed; flagged in data (1 review row)

---

**Problem:** A chart's first page prints "(continued)", so its rows were dropped.
**Where:** Reso 08 p.32, chart #25 Prisoners' Rights Project (Legal Aid Society, $1,000,000 MOCJ →
DYCD); p.31 is chart #24
**Found by:** T3 ("(continued)" does not continue the previous chart; numbers not 1..40) and T5
**Tried:** —
**Fix:** a "(continued)" caption whose chart has not started, right after the chart before it,
starts the chart; allowed only as a named exception (`T3.continued_start`). PR.
**Status:** fixed; flagged in data (1 review row)

---

**Problem:** Caption spellings: "- FY 2023" for "- Fiscal 2023", and "(cpntinued)".
**Where:** "FY 2023": Reso 01 p.66, Reso 09 pp.21, 22, 25. "(cpntinued)": Reso 03 p.20
**Found by:** T12 (4 charts with no fiscal year) and T3 (chart #8 starts twice)
**Tried:** —
**Fix:** the caption reader takes both; each is flagged `W.caption_format`. 11 rows get their
budget year; chart #8's second page joins it. PR.
**Status:** fixed; flagged in data (5 review rows)

---

**Problem:** Empty drawn rows read as rows with no EIN and no amount.
**Where:** Reso 01 p.67 row 22, Reso 03 p.83 row 4, Reso 06 p.53 rows 11–12
**Found by:** T5 (rows without a readable amount)
**Tried:** looked at the rendered page: the grid draws a blank row under the last one.
**Fix:** a drawn row with no text, visible or hidden, is not a row; counted in T5. PR.
**Status:** fixed

---

**Problem:** A second wording of the `***` footnote was read as unexpected text.
**Where:** Reso 02 p.8, "*** Correction and/or Reversal of a change made in a previous
Transparency Resolution."
**Found by:** T6 (unexpected text under the table) and T11 (2 `***` rows with no footnote)
**Tried:** —
**Fix:** both wordings are accepted. PR.
**Status:** fixed

---

**Problem:** 18 rows marked `***` on pages that print no `***` footnote.
**Where:** Reso 03 p.11; Reso 04 p.15; Reso 06 pp.34, 35, 40; Reso 07 p.29; Reso 08 p.6
**Found by:** T11 (markers)
**Tried:** checked the footer lines of each page
**Fix:** none; kept as printed (`correction` = 1). Named exceptions, as in FY2024.
**Status:** flagged in data (18 critical review rows)

---

**Problem:** 4 chart pages print no "Page n" label.
**Where:** Reso 08 p.44 (chart #37); Reso 09 pp.29–31 (charts #27–#29), all Fiscal 2022
**Found by:** T3 (page labels)
**Tried:** looked at Reso 09 p.29 rendered: no label.
**Fix:** none; the labels after them count them. Named exceptions.
**Status:** flagged in data (4 review rows)

---

**Problem:** Odd values the PDF prints.
**Where:** Reso 11 p.19 (Fort Greene Council, Inc. printed with the City's EIN 13-6400434);
Reso 07 p.27 (two $0 rows)
**Found by:** W.unpaired_purpose and W.amount_zero
**Tried:** checked each on the rendered page
**Fix:** none; kept as printed.
**Status:** flagged in data (4 review rows)

---

**Problem:** The retired CSV missed 70 rows.
**Where:** `data/fy23/transparency-resolutions/fy23_transparency_all.csv`
**Found by:** comparison with the retired file (multiset of resolution, EIN, amount)
**Tried:** —
**Fix:** all 8,354 of its rows are here. The 70 it lacks: 61 EINs printed without a hyphen and 9
ordinary rows. List: `data/fy23_tr_retired_csv_compare.csv`. The retired files are left as they are.
**Status:** fixed (in the new tables)
