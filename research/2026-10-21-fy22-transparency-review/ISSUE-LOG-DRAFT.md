# Draft #107 issue-log comments: FY2022 transparency resolutions (NOT posted)

**Written:** 2026-10-21 23:09 EDT. One block per problem, in the order found, in the shape #107
asks for. Each is meant to be its own comment on #107 once Noel approves. "PR" means the PR that
adds this folder; "promotion PR" the one that writes `data/fy22/pdf/transparency/`.

---

**Problem:** Starting point. The committed FY2022 CSVs come from the old text-order parser.
**Where:** 14 PDFs, 709 pages (565 chart pages)
**Found by:** review (starting point)
**Tried:** the FY2023 reader with a new config (`config/transparency/fy2022.toml`).
**Fix:** first run: 6 hard checks failed (T3, T4, T5, T6, T11, T15) and 478 rows had no amount.
Each cause is below.
**Status:** fixed

---

**Problem:** 387 amounts printed in cents could not be read.
**Where:** Reso 03 chart #48, Pandemic Support for Human Service Providers ("$20,290.00")
**Found by:** T5 (rows without a readable amount)
**Tried:** checked every one: all end in ".00".
**Fix:** ".00" is accepted and read as whole dollars; any other cents stay unreadable. PR.
**Status:** fixed

---

**Problem:** "Beating Hearts" charts have no Agency or Amount column.
**Where:** Reso 03 p.94, 04 p.39, 06 p.38, 08 p.40, 10 p.43, 11 p.31, 12 p.25 (91 rows)
**Found by:** T4 (header not recognised), T5 (no amount), T6 and T15 (the note under the table,
"Staten Island Heart Society, Inc. has received $350,000 …")
**Tried:** —
**Fix:** a header with organization and EIN but no agency, amount or purpose is a list: rows kept
with a blank amount, `action` = `listed`, the note read as the chart's note. Allowed only as a
named exception (`T4.no_amount`). The image side reads the same header. PR.
**Status:** fixed; flagged in data (7 review rows)

---

**Problem:** Captions that do not say "(continued)" where they should, or say it wrongly.
**Where:** repeated without "(continued)": Reso 01 pp.51–54, Reso 02 p.35. Wrong number: Reso 07
p.34 ("CHART #21" under #22). "(continued)" on a first page: Reso 02 pp.80, 124
**Found by:** T3 (chart starts twice; "(continued)" does not continue)
**Tried:** —
**Fix:** each read as what the page plainly is, and each allowed only as a named exception
(`T3.continued_missing`, `T3.continued_number`, `T3.continued_start`). PR.
**Status:** fixed; flagged in data (8 review rows)

---

**Problem:** Page labels did not count up on 12 resolutions.
**Where:** 25 chart pages print no "Page n"; Reso 02 p.106 has no table, only a spilled footnote
and "Page 84"
**Found by:** T3 (page labels)
**Tried:** looked at Reso 12 p.20 and Reso 02 p.106 rendered.
**Fix:** named exceptions (`T3.page_label`; `T3.label_page` for p.106, whose label joins the count). PR.
**Status:** flagged in data (26 review rows)

---

**Problem:** The image grid disagreed on 2,151 rows and 13% of the ink looked uncovered, all on
Reso 02.
**Where:** Reso 02, 116 of 138 pages
**Found by:** image lattice (H8) and ink coverage (H9)
**Tried:** looked at the rendered page (clean) and the page boxes: the media box starts at
(−8.39, −8.39). pdfplumber counts from there, pdfium renders from the corner.
**Fix:** the reader records each page's origin; the image checks shift the picture to match;
`bbox_pt` is written on the page as rendered. Now 7,917 / 7,918 agree. PR.
**Status:** fixed

---

**Problem:** After the shift, the ink check still fired once per Reso 02 page (77 px).
**Where:** the "EIN" header on every Reso 02 chart page
**Found by:** ink coverage (H9)
**Tried:** measured at 8x zoom: the bold capitals rise 0.45 pt above the box the text layer gives
them (box top 54.15 pt, glyph top about 53.7 pt).
**Fix:** `header_char_top_pt = 0.6` in the FY2022 config raises header boxes (0 elsewhere). PR.
**Status:** fixed

---

**Problem:** An EIN read as "F1u3n-4d1in7g0 3to8 9g".
**Where:** Reso 09 p.38 rows 3–4 (Family Life Academy Charter School, ($5,000) / $5,000)
**Found by:** T5 (odd EIN)
**Tried:** the page shows "13-4170389". The text layer also holds a long line "Funding to go
support the creation of educational home kits …" drawn over the EIN and off the page. A rule
that hides any run starting on top of earlier text also fired in FY2023–FY2026 (clipped
continuations, "(cid:9)" tabs), so it was narrowed: only letters an earlier run shows in its own
cell count, "(cid:" glyphs are ignored, and it runs only on pages the config names.
**Fix:** `T7.overlaid` names Reso 09 p.38; EIN read; the line kept in `hidden_text`; both rows
are critical review items. "anc" of that line shows in the empty `*` column (H9, 2 spots). PR.
**Status:** fixed; flagged in data (5 review rows). FY2026 Reso 02 p.114 has the same pattern
and was left unchanged (decision for Noel).

---

**Problem:** Odd values the PDF prints.
**Where:** Reso 03 p.32 (a row with only DYCD and ($1,613,026)); Reso 07 p.21 ("FY22 05075" as an
EIN); Reso 03 p.29 ("#" in the `*` column); `***` with no footnote on Reso 03 p.16, Reso 08 p.16,
Reso 09 p.38
**Found by:** T5 (anchors), T11 (markers)
**Tried:** checked each on the rendered page
**Fix:** none; kept as printed. Named exceptions where a check needs one.
**Status:** flagged in data (9 critical review rows)

---

**Problem:** The retired CSV missed 150 rows.
**Where:** `data/fy22/transparency-resolutions/fy22_transparency_all.csv`
**Found by:** comparison with the retired file (multiset of resolution, EIN, amount)
**Tried:** —
**Fix:** all 7,768 of its rows are here. The 150 it lacks: 91 "Beating Hearts" rows, 45 EINs
printed without a hyphen, 12 ordinary rows, the blank-EIN row and the "FY22 05075" row. List:
`data/fy22_tr_retired_csv_compare.csv`. The retired files are left as they are.
**Status:** fixed (in the new tables)
