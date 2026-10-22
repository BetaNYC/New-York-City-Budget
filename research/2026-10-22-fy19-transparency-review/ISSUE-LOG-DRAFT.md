# Draft #110 issue-log comments: FY2019 transparency resolutions (NOT posted)

**Written:** 2026-10-22 01:45 EDT. One block per problem, in the order found, in the shape #110
asks for. Each is meant to be its own comment on #110 once Noel approves. "PR" means the PR that
adds this folder; "promotion PR" the one that writes `data/fy19/pdf/transparency/`.

---

**Problem:** Starting point. The committed FY2019 CSVs come from the old text-order parser.
**Where:** 11 PDFs, 733 pages (592 chart pages)
**Found by:** review (starting point)
**Tried:** the FY2020 reader with a new config (`config/transparency/fy2019.toml`).
**Fix:** first run: the image grid agreed on all 7,207 rows, but 4 hard checks failed (T3, T4,
T11, T13), the run crashed drawing a crop for a resolution-level flag, the ink check found 91
uncovered regions, and 484 captions were review items. Each cause is below.
**Status:** fixed

---

**Problem:** The run crashed on a review crop for "page 0".
**Where:** `review_crops` in `code/parse_transparency_v2.py`; a T3 numbering problem is flagged
on the resolution (page 0)
**Found by:** the run itself (pypdfium2 "Failed to load page")
**Tried:** —
**Fix:** items with no page get no crop. No other year has such an item, so nothing else
changes. PR.
**Status:** fixed

---

**Problem:** Wrapped names land in the wrong row, or fall off the table (overfull cells).
**Where:** 21 pages: Reso 03 pp.43, 46, 83; Reso 04 pp.23, 26, 40, 49, 51, 52, 56, 64, 65; Reso
07 pp.25–31, 37, 38
**Found by:** H9 ink coverage (Reso 04 pp.49, 51; Reso 07 p.27: glyph parts outside every cell),
then a scan for letters drawn across a row rule
**Tried:** the image grid agreed with the wrong reading, because it reads the same text layer
by letter centre. A first block rule (lines drawn one after another at the same left edge)
merged whole rows on Reso 04 p.40 and Reso 07 p.27, because those rows are drawn column by
column. A line now joins a block across a rule only if it and the block both cross a rule.
**Fix:** on pages the config names (`T7.overfull`), each cell's lines are one block and go to
the row holding the block's middle, on both grids. 43 rows change, all compared by hand: e.g.
Reso 07 p.27 row 17 "IGnrce.enwich House" → "Greenwich House", row 22 gains "Aged", Reso 04 p.49
row 6 gains "67K". T7 now fails if text crosses a rule on a page the config does not name.
FY2018 has 3 such pages; FY2020–FY2026 none. PR.
**Status:** fixed; flagged in data (33 review rows)

---

**Problem:** 484 caption review items for "CHART 1:" (no "#").
**Where:** every chart page of Reso 01–07 and 11; Reso 08–10 print "CHART #1:"
**Found by:** W.caption_format
**Tried:** —
**Fix:** `caption_no_hash = true` on those resolutions in the config: their house style is not a
review item. The 3 captions odd inside their own resolution (Reso 02 p.32, Reso 09 p.23, Reso 10
p.15) still are. PR.
**Status:** fixed; flagged in data (3 review rows)

---

**Problem:** A caption printing the wrong chart number.
**Where:** Reso 01 p.108: "CHART 55: Purpose of Funds Changes - Fiscal 2018"; #55 is Fiscal 2019
(pp.104–107), and pp.109–111 print "CHART 56: … Fiscal 2018 (continued)"
**Found by:** T3 (chart #55 starts twice; chart #56's first page prints "(continued)")
**Tried:** the FY2022 `T3.continued_number` rule does not fit (different fiscal years).
**Fix:** new named exception `T3.chart_number` (page, printed number, number read); read as #56. PR.
**Status:** fixed; flagged in data (1 review row)

---

**Problem:** A "Page n" label printed on top of a footnote.
**Where:** Reso 03 p.55 ("…Transparency ResolutPioange 41")
**Found by:** T3 (labels not 1..69)
**Tried:** —
**Fix:** named exception `T3.page_label`: the labels around it count the page. PR.
**Status:** fixed; flagged in data (1 review row)

---

**Problem:** Reso 01 is dated a day before its Legistar adoption.
**Where:** Reso 01 p.1, "This Resolution, dated July 17, 2018"; Res 0457-2018 adopted 2018-07-18
(noted already in the 2026-07-07 Legistar pass)
**Found by:** T13 (printed date ≠ config date)
**Tried:** —
**Fix:** new named exception `T13.printed_date`; `resolution_date` stays Legistar's, and the
row's `resolution_date_source` no longer claims the printed date. PR.
**Status:** fixed; flagged in data (1 review row)

---

**Problem:** Bold header capitals outside their text boxes.
**Where:** Reso 09 pp.11–44 (88 ink slivers along the header's top)
**Found by:** H9 ink coverage
**Tried:** looked at p.11: "E" box top 42.73 pt, ink from 41.5 pt.
**Fix:** `header_char_top_pt = 1.3` in the config (the FY2022 knob). Ink: 0 regions. PR.
**Status:** fixed

---

**Problem:** Other cases earlier years already handle.
**Where:** "Beating Hearts Initiative" with no Agency or Amount (Reso 02 p.103, 03 p.83, 04 p.68,
05 p.138, 07 p.41; 112 rows, no note); `**` rows on a page with only the `*` footnote (Reso 04
p.19, 4 rows)
**Found by:** T4, T11
**Tried:** —
**Fix:** named exceptions (`T4.no_amount`, `T11.markers`). PR.
**Status:** flagged in data (5 + 4 review rows; the 4 critical, suggested `source_error`)

---

**Problem:** Rows with no readable EIN.
**Where:** Reso 01 p.111, "All Allocations", EIN "Various" (±$4,090,000); Reso 03 p.46, Himalayan
Elders Project, "472383238" plus a hidden tab glyph ($12,000)
**Found by:** T5 (rows that print no EIN)
**Tried:** —
**Fix:** kept as printed. PR.
**Status:** flagged in data (3 critical review rows)

---

**Problem:** A separator printed without spaces at a line end.
**Where:** Reso 07 p.30 row 22: "Neighborhood SC-" / "Catholic Charities Neighborhood Services"
**Found by:** W5.wrap_hyphen (all 25 line-end hyphens read by hand)
**Tried:** —
**Fix:** kept as printed; named in `wrap_hyphen_review`. PR.
**Status:** flagged in data (1 review row)

---

**Problem:** One chart is $1 off inside itself; Reso 02 is −$144,999 overall.
**Where:** Reso 02 chart #8 DoVE (pp.33–37): +$4,546,229 / −$4,546,228. Charts #5 A Greener NYC
(−$70,000) and #12 Parks Equity Initiative (−$75,000) have no matching designation.
**Found by:** chart nets (reported, not a check: the charts print no totals)
**Tried:** both grids read the same digits.
**Fix:** none (the PDF's own arithmetic). Listed in `REVIEW.md` for Noel.
**Status:** open (decision for Noel)

---

**Problem:** Is anything else different? Re-run of every finished year.
**Where:** FY2020–FY2026 review folders
**Found by:** byte comparison after the reader, check and config changes
**Tried:** —
**Fix:** every tracked file in FY2020–FY2025 is byte-identical; FY2026 differs only by the two
committed review decisions it picks up (known, not committed). Re-running FY2019 is
byte-identical. PR.
**Status:** fixed
