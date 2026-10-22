# Draft #105 issue-log comments: FY2024 Schedule C (NOT posted)

**Written:** 2026-10-21 20:30 EDT. One block per problem, in the order found, in the shape #105
asks for. Each is meant to be its own comment on #105 once Noel approves. "PR" means the PR
that adds this folder; "promotion PR" the one that writes `data/fy24/pdf/schedule_c/`.

---

**Problem:** FY2024 had no config.
**Where:** `Fiscal-2024-Schedule-C-Merge-Final.pdf`, whole document (453 pages: 192 portrait,
253 landscape, 8 at 1148×887)
**Found by:** review (starting point for #105)
**Tried:** the FY2025 config with FY2024 names and pages: 7,691 rows; body 3,780 rows against
5,378 EIN words on the initiative pages; 164 unknown headers.
**Fix:** `config/schedule_c/fy2024.toml`. 26 categories from the banners (pp.9–262); sections
pp.1–8 front, 9–265 body, 266–291 / 292–411 / 412–453 appendices A / B / C. PR.
**Status:** fixed

---

**Problem:** 216 pages have a MediaBox that does not start at (0, 0), so pdfplumber's
coordinates and the rendered pixels are 18 pt apart.
**Where:** pp.227–254 and 266–453 (MediaBox `[-18.03 17.97 773.97 629.97]`); known going in
(families/README.md, "shared machinery")
**Found by:** known going in; confirmed by comparing a character's box in pdfplumber and pdfium
on p.227
**Fix:** every coordinate is taken from the MediaBox corner (`code/schedc/vector.py` `origin`,
`shift`; the image and ink checks shift the same way). A no-op on pages that start at (0, 0):
FY2025–FY2027 outputs are byte-identical. The appendix pages, all offset, agree with the image
grid row for row; a golden test finds p.242's Medicare Rights row inside its `bbox_pt` with
pdfium. PR.
**Status:** fixed

---

**Problem:** Many initiative award tables have a rule under each row and no vertical rules, so
no table was found and their rows were lost.
**Where:** 70 tables on 53 pages, e.g. pp.35–39 (AAPI Community Support), 63–66 (Criminal Justice),
148–155 (Health), 161 (Community Housing Preservation Strategies); families/
schedule-c-fy2008-fy2024.md ("h-rule-only tables", FY2024: 27 pages)
**Found by:** anchor census (H5: 92 pages with fewer rows than EIN words)
**Tried:** (1) every stack of rules as a table: it also swallowed the initiative boxes above
(their description rows are ruled too). (2) Only where no lines-strategy table holds the words:
missed p.161, where white-filled boxes make an empty "table", and p.69, where they make a table of
names and EINs with the amounts outside it. (3) Rules drawn as several abutting thin boxes were
not merged.
**Fix:** `hrule_tables` (config switch; `code/schedc/vector.py`): rules merged across abutting
boxes; a stack becomes a table from the band above its first EIN (or its header band) to its last
EIN band, where an EIN or amount word lies in no cell of a trustworthy table; "suspect" tables (no
word in any cell, or EIN rows without an amount) are replaced or trimmed. Columns split at the
leftmost EIN word and between the EIN and amount words; a new check (H7.hrule_splits) fails if a
character crosses a split: 0 do. PR.
**Status:** fixed, flagged in data (`W.hrule_table`, 927 rows)

---

**Problem:** The image grid cannot read a table with no vertical rules, so 1,600 rows had no
second reading.
**Where:** the tables above, and tables whose only vertical "rules" are white-filled boxes (e.g.
p.178), which pdfplumber reads as ruled and the pixels do not
**Found by:** grid compare (H8: `no_image_row`)
**Tried:** carrying the header on the image side (`carry_header`): fixed 153 rows of tables whose
header is on the page before or at the bottom (pp.41–45).
**Fix:** `band_check` (config switch; `code/schedc_cv/imagegrid.py` `hrule_ys`, `check_bands`):
for rows the image lattice cannot see, the pixels' own horizontal rules must sit at the row's
top and bottom, with none inside. 1,438 of 1,447 rows pass; the 9 others are review rows. The
fields of those rows are read once (README, "cannot prove"). PR.
**Status:** fixed, flagged in data (`lattice` = `vector+bands`)

---

**Problem:** A table's first row has no rule above it, so it was outside every table.
**Where:** pp.41–46 (column rules start 13 pt above the first rule), pp.152–153 (nothing drawn
above but the page-header rule); families doc: "First row above the first drawn rule … FY24
pp.41–45"
**Found by:** anchor census (H5: one EIN word short on each page)
**Fix:** `open_top_rows` (config switch): the band is read as a row only when it holds an EIN and
an amount word; for h-rule tables the same, back to the nearest rule. All 8 are critical review
rows (no rule confirms their top). PR.
**Status:** fixed, flagged in data

---

**Problem:** Award headers printed outside the table: as loose text above it, or only "EIN
Amount" loose with "Legal Name of Organization" inside the box table above, or at the bottom.
**Where:** loose: pp.148, 149, 155, 169, 264, 265; bottom: pp.41–45
**Found by:** anchor census; box vs summary (data rows read as boxes, e.g. "APICHA … | $81,719",
p.149)
**Fix:** `loose_header` (config switch; loose lines now carry their words with x extents, so
"EIN  Amount" splits into two columns); bottom headers are read with the header carried from the
page before (`headerless_continuation`). PR.
**Status:** fixed, flagged in data (`W.loose_header`, `W.headerless_table`)

---

**Problem:** Eight landscape pages are merged out of order, so 191 rows were attached to A
Greener NYC.
**Where:** pp.130–137 (1148×887, no printed page number), between printed pp.89 and 90
**Found by:** totals (H12: A Greener NYC rows $17,013,500 for a $5,100,000 box; NYC Cleanup $0)
**Tried:** summing by page: pp.130–137 add to $12,028,500, exactly NYC Cleanup's box less its
reserve; their purposes are cleaning and sanitation.
**Fix:** `[[initiative_pages]]` in config: rows on those pages go to NYC Cleanup, each flagged; one
critical review row ($12,028,500). PR.
**Status:** flagged in data (decision for Noel)

---

**Problem:** Statements worded 71 ways; 45 give a reserve and "the following providers" with no
designated amount.
**Where:** e.g. p.69 "will designate $2.48 million post-adoption and has designated the
following providers"; pp.176–183 as two sentences; p.147 two designated amounts; pp.156–158
"allocated directly to the City University of New York"; "Fiscal 2023" typos (pp.63, 168, 262)
**Found by:** structure (unknown statement)
**Fix:** new kind `reserve_rows` (rows = box − reserve, `code/schedc/reconcile.py`); several
`designated…` groups add up (`structure.statement_kind`); 10 patterns in config. PR.
**Status:** fixed

---

**Problem:** Two SAVE boxes in one ruled table, the second under the first's award row; a
statement's text outside its cell.
**Where:** p.122; p.217 (Green Jobs Corps Program)
**Found by:** box vs summary; structure (empty statement)
**Fix:** `split_boxes_after_rows`, `statement_loose_text` (config switches). PR.
**Status:** fixed

---

**Problem:** The ink self-test failed: the smallest letter of the test row did not fire.
**Where:** p.242, Medicare Rights Center (Speaker's pages, 8.8 pt type: a letter 'i' is 61 px at
300 dpi, under the 64 px floor)
**Found by:** ink coverage acceptance
**Fix:** FY2024's region floor is 48 px; the clean run still finds 0 regions. In config. PR.
**Status:** fixed

---

**Problem:** The PDF's own numbers disagree, seven times, and one EIN is copied from the row
above.
**Where:** p.63 TOTAL (+$52,935); statements on pp.109, 129, 147, 148, 176, 181; p.261 Drama Club
printed with Digital Girl's EIN; p.135 "TF4876222"; p.182 "13-294-6970"
**Found by:** totals (H10, H12, H13); anchor census (H5); old-vs-new comparison (Drama Club)
**Tried:** looking for a parse loss: none. EIN census exact, ink coverage clean, pages looked at.
**Fix:** none. Named exceptions in config; Drama Club a critical known issue. In the review file.
**Status:** flagged in data

---

**Problem (checked, none found):** DATA-ANOMALIES §20 lists one FY2024 merged row.
**Where:** p.234, Corbin Hill Food Project / Council For Unity, Inc.
**Fix:** none needed: two awards, $50,000 each. Golden test.
**Status:** fixed (by the method)

---

## Proposed DATA-ANOMALIES text

Added in the PR as §33 (FY2024 Schedule C rebuilt from the PDF).
