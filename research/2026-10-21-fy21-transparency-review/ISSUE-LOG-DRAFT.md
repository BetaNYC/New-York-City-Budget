# Draft #108 issue-log comments: FY2021 transparency resolutions (NOT posted)

**Written:** 2026-10-21 23:59 EDT. One block per problem, in the order found, in the shape #108
asks for. Each is meant to be its own comment on #108 once Noel approves. "PR" means the PR that
adds this folder; "promotion PR" the one that writes `data/fy21/pdf/transparency/`.

---

**Problem:** Starting point. The committed FY2021 CSVs come from the old text-order parser.
**Where:** 8 PDFs, 404 pages (324 chart pages)
**Found by:** review (starting point)
**Tried:** the FY2022 reader with a new config (`config/transparency/fy2021.toml`).
**Fix:** first run: 4 hard checks failed (T3, T4, T6, T11); the image grid already agreed on
4,500 of 4,500 rows and the ink check found nothing. Each cause is below.
**Status:** fixed

---

**Problem:** A crash writing the review crops once T3 failed.
**Where:** `code/parse_transparency_v2.py`, `review_crops`
**Found by:** the run itself (pypdfium2 "Failed to load page")
**Tried:** the failing "Page n labels are not 1..n" items carry `pdf_page` 0 (they are about a
whole resolution), and the crop step tried to render page 0.
**Fix:** none needed once T3 passes: no resolution-level item is left. Noted for the code: a
resolution-level item that is not resolved stops the run at the crop step instead of writing
the checks file.
**Status:** open (not changed; only reachable while a hard check fails)

---

**Problem:** A third wording of the `***` footnote was not recognised.
**Where:** Reso 02–07, 14 pages: "*** Technical adjustment to designation made in a previous
Transparency Resolution."
**Found by:** T6 (14 lines of unexpected text under tables) and T11 (34 `***` rows without
their footnote)
**Tried:** —
**Fix:** added to `transreso.structure.FOOTNOTES` next to the FY2023 and FY2026 wordings.
FY2022–FY2026 outputs unchanged. PR.
**Status:** fixed

---

**Problem:** Page labels did not count up on 6 resolutions.
**Where:** 15 chart pages print no "Page n": Reso 05 pp.33–37 and 40, Reso 06 pp.34–37, Reso 07
pp.31–32, Reso 08 p.20 (prior-year charts), Reso 02 p.65 and Reso 03 p.47 ("Beating Hearts")
**Found by:** T3 (page labels)
**Tried:** looked at Reso 05 p.35 rendered: no label; p.38 prints "Page 28" after p.32's "Page 22".
**Fix:** named exceptions (`T3.page_label`), as FY2022. PR.
**Status:** flagged in data (15 review rows)

---

**Problem:** "Beating Hearts" charts have no Agency or Amount column.
**Where:** Reso 01 p.126, 02 p.65, 03 p.47, 05 p.40 (28 rows; portrait pages)
**Found by:** T4 (header not recognised)
**Tried:** —
**Fix:** the FY2022 handling: rows kept with a blank amount, `action` = `listed`, the note
("… has received $175,000 …") read as the chart's note; named exceptions (`T4.no_amount`). PR.
**Status:** flagged in data (4 review rows)

---

**Problem:** A chart's first page prints "(continued)".
**Where:** Reso 02 p.20, chart #6 Speaker's Initiative to Address Citywide Needs
**Found by:** T3 (caption)
**Tried:** checked p.19 (chart #5) and the labels (Page 7, Page 8): no page is missing.
**Fix:** read as the chart's start; named exception (`T3.continued_start`). PR.
**Status:** flagged in data (1 review row)

---

**Problem:** A row prints no member and no EIN.
**Where:** Reso 02 p.29, chart #9 Cultural Immigrant Initiative: "Department of Cultural
Affairs **", DCLA ($10,000)
**Found by:** T5 (anchor census: row without an EIN)
**Tried:** looked at the rendered page: the cells are blank.
**Fix:** kept as printed. PR.
**Status:** flagged in data (critical review row; suggested `source_error`)

---

**Problem:** Is anything else different? Re-run of every finished year.
**Where:** FY2022–FY2026 review folders
**Found by:** byte comparison after the footnote change
**Tried:** the first re-run used Python 3.14, which changes only the `python` line of each
manifest; re-done with Python 3.12.13, the version the committed files were made with.
**Fix:** every tracked file in FY2022–FY2025 is byte-identical; FY2026 differs only by the two
committed review decisions it picks up (known, not committed). Re-running FY2021 is
byte-identical. PR.
**Status:** fixed
