# Draft #109 issue-log comments: FY2020 transparency resolutions (NOT posted)

**Written:** 2026-10-22 00:38 EDT. One block per problem, in the order found, in the shape #109
asks for. Each is meant to be its own comment on #109 once Noel approves. "PR" means the PR that
adds this folder; "promotion PR" the one that writes `data/fy20/pdf/transparency/`.

---

**Problem:** Starting point. The committed FY2020 CSVs come from the old text-order parser.
**Where:** 8 PDFs, 508 pages (413 chart pages)
**Found by:** review (starting point)
**Tried:** the FY2021 reader with a new config (`config/transparency/fy2020.toml`).
**Fix:** first run: 4 hard checks failed (T3, T4, T5, T11); 272 EIN-shaped words on 30 pages had
no row, the image grid found 272 rows the vector side did not, and the ink check found 360
uncovered regions. Each cause is below.
**Status:** fixed

---

**Problem:** Purpose-of-funds charts were dropped: their captions did not match.
**Where:** "Chart #35:" (Reso 01 pp.70–80, Reso 02 pp.85–86), "Chart # 44:" (Reso 03 pp.73–87)
**Found by:** T3 (no chart caption above the table), T5 (EIN-shaped words but 0 rows), H8 (image
rows with no vector row), H9 (uncovered ink)
**Tried:** —
**Fix:** captions are rewritten before matching ("Chart" → "CHART", "# 44" → "#44"); each page is
a `W.caption_format` review item. All 272 rows come back; the image grid then agrees on 5,396 of
5,396 and the ink check finds 0 regions. PR.
**Status:** fixed; flagged in data (28 review rows)

---

**Problem:** "(continued)" printed before the fiscal year, so SU-CASA "started twice".
**Where:** "CHART #16: SU-CASA (continued) - Fiscal 2020" (Reso 05 pp.32–33); chart #10 on Reso
06 pp.17–18
**Found by:** T3 (chart starts twice)
**Tried:** —
**Fix:** the same rewrite moves "(continued)" to the end; `W.caption_format`. PR.
**Status:** fixed; flagged in data (4 review rows)

---

**Problem:** A "(continued)" caption with no chart number.
**Where:** Reso 06 pp.25–26: "CHART #: Purpose of Funds Changes - Fiscal 2020 (continued)",
after chart #16 of that title (p.24)
**Found by:** T3 (no chart caption above the table)
**Tried:** —
**Fix:** the caption pattern allows an empty number. Such a caption is read as continuing the
chart before it only through the FY2022 `T3.continued_number` rule (same title and year, named
exception); otherwise T3 fails ("caption prints no chart number"). PR.
**Status:** fixed; flagged in data (2 review rows)

---

**Problem:** "Organization - School" was not a known header label.
**Where:** 7 pages (Reso 03 pp.58, 72; Reso 04 pp.50, 74; Reso 05 p.50; Reso 07 p.41; Reso 08 p.25)
**Found by:** T4 (header not recognised)
**Tried:** —
**Fix:** added as an organization label. PR.
**Status:** fixed

---

**Problem:** Other caption and header cases earlier years already handle.
**Where:** "Beating Hearts Initiative" with no Agency or Amount (Reso 03 p.88, 04 p.84, 05 p.73;
73 rows, no note under the table); a first page printing "(continued)" (Reso 02 p.34); a caption
repeated without "(continued)" (Reso 05 p.47)
**Found by:** T3, T4
**Tried:** looked at Reso 05 p.73 rendered: no note.
**Fix:** named exceptions (`T4.no_amount`, `T3.continued_start`, `T3.continued_missing`). PR.
**Status:** flagged in data (5 review rows)

---

**Problem:** `***` rows on pages with no `***` footnote.
**Where:** Reso 02 pp.16, 23; Reso 04 p.20; Reso 05 p.22 (11 rows)
**Found by:** T11 (marker without its footnote)
**Tried:** looked at Reso 04 p.20 rendered: footnotes `*` and `**` only.
**Fix:** kept as printed; named exceptions per row. PR.
**Status:** flagged in data (11 critical review rows; suggested `source_error`)

---

**Problem:** A separator printed without spaces at a line end.
**Where:** Reso 05 p.67 row 4: "Millennium Development-" / "Millennium Youth Services"
**Found by:** W5.wrap_hyphen (all 144 line-end hyphens read by hand; the other 143 are compound
words)
**Tried:** —
**Fix:** kept as printed; named in `wrap_hyphen_review`, so it goes to review. PR.
**Status:** flagged in data (1 review row)

---

**Problem:** Two charts are $1 off inside themselves.
**Where:** Reso 01 chart #10 DoVE (pp.32–34): +$3,264,794 / −$3,264,793. Reso 04 chart #11 DoVE
(p.30): MOCJ $110,814 against $110,815 taken back
**Found by:** chart nets (reported, not a check: the charts print no totals)
**Tried:** both grids read the same digits; the old parse's notes show the same +$1 on Reso 01.
**Fix:** none (the PDF's own arithmetic). Listed in `REVIEW.md` for Noel.
**Status:** open (decision for Noel)

---

**Problem:** Is anything else different? Re-run of every finished year.
**Where:** FY2021–FY2026 review folders
**Found by:** byte comparison after the caption and header changes
**Tried:** —
**Fix:** every tracked file in FY2021–FY2025 is byte-identical; FY2026 differs only by the two
committed review decisions it picks up (known, not committed). Re-running FY2020 is
byte-identical. PR.
**Status:** fixed
