# Draft #106 issue-log comments: FY2023 Schedule C (NOT posted)

**Written:** 2026-10-21 23:00 EDT. One block per problem, in the order found, in the shape #106
asks for. Each is meant to be its own comment on #106 once Noel approves. "PR" means the PR
that adds this folder; "promotion PR" the one that writes `data/fy23/pdf/schedule_c/`.

---

**Problem:** FY2023 had no config.
**Where:** `Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf`, whole document (334 pages: 98
portrait, 236 landscape; every MediaBox starts at (0, 0))
**Found by:** review (starting point for #106)
**Tried:** FY2024's config with FY2023 names and pages and one statement pattern: 5,884 rows;
appendices already equal to their pots; 75 initiatives off, 8 unknown headers, 133 unmapped
cells, 37 orphan characters.
**Fix:** `config/schedule_c/fy2023.toml`. 26 categories from the banners (pp.12–138; "Senior
Services" and "Veterans Services" this year); sections pp.1–11 front, 12–140 body, 141–167 /
168–293 / 294–334 appendices A / B / C; "Borough" header (Boroughwide Needs, pp.28–33). PR.
**Status:** fixed

---

**Problem:** Designation statements worded 62 ways (142 statements), many putting the reserve after the
providers.
**Where:** e.g. pp.71–75 "has designated the following providers for Fiscal 2023 and $186,947
will be designated post-adoption."; pp.131–132 "post budget adoption", "post-budget adoption";
p.41 "The Council Members will designate $100,000 per Council District, for a total of
$5,100,000 post adoption."; p.102 "This initiative will be designated post-Adoption."; p.132
"The has designated …"; pp.49–50 "for Fiscal 2022"
**Found by:** structure (unknown statement: 78 boxes)
**Fix:** 13 patterns in config, kinds as FY2024 (`reserve_rows`, `partial`, `reserve_only`,
`reserve_all`, `direct`, `full`). PR.
**Status:** fixed

---

**Problem:** Boxes whose amount is printed oddly were not read as boxes, so their rows went to
the box before.
**Where:** p.34 "AAPI | $ 5,000,000" (a space after "$"); p.92 "Trauma Recovery Centers |
2,400,000" (no "$", in the black bar; its statement, "will designate post adoption.", was
taken as Opioid Prevention and Treatment's, so Opioid's 17 rows sat under a box held whole
post-adoption)
**Found by:** totals (H11: summary lines with no box; H12: rows under a reserve-only box)
**Fix:** `box_amount_dollar_space`, `box_amount_without_dollar` (config switches;
`code/schedc/structure.py` `table_kind`). The bare amount is flagged
(`W.box_amount_no_dollar`). PR.
**Status:** fixed, flagged in data

---

**Problem:** A box drawn inside the award table above it was read as award rows.
**Where:** p.53: Community Schools' last two rows, an empty band, "Educational Programs for
Students | $7,143,133" and its Agency and U/A rows, all one ruled table; the box's statement and
award rows are in the next table
**Found by:** totals (H12: Community Schools rows $17,986,266 for a $3,750,000 box; H11: no box
for Educational Programs for Students)
**Tried:** FY2024's `split_boxes_after_rows`: it only looks in tables that hold a statement row.
**Fix:** `split_boxes_award_tables` (config switch; `structure.split_merged_tables`): a table that
starts with an award header is split at a box row (a title and an amount, nothing EIN-like). PR.
**Status:** fixed

---

**Problem:** White-filled boxes make a "table" of the name column only; the EINs and amounts
printed beside it were in no table, and their rows were lost or merged.
**Where:** p.68 (CUNY Research Institutes, 6 rows), p.140 (STARS, 4 rows), p.139 (COMPASS's
last 3 rows read as one)
**Found by:** anchor census (H5: p.68 6 EIN words, 0 rows; p.139 14 and 11; p.140 14 and 10)
**Fix:** `hrule_beside` (config switch; `code/schedc/vector.py` `hrule_tables`): such a table is
"suspect", as FY2024's white-box tables are, and the rows are read from the horizontal rules. PR.
**Status:** fixed, flagged in data (`W.hrule_table`)

---

**Problem:** A column header and the first award row share one row band (no rule between), so
the header was unknown and the table was lost.
**Where:** p.35 ("Legal Name of Organization  EIN  Amount" over "Chinese-American Family Alliance
for Mental Health, Inc. 26-4048050 $30,000"; looked at)
**Found by:** anchor census (H5: 30 EIN words, 0 rows); H4 (unknown header)
**Fix:** `hrule_header_split` (config switch): the band is cut halfway between the header words
and the row's words. The row is a critical review row (no rule confirms its top). PR.
**Status:** fixed, flagged in data

---

**Problem:** An award row pulled into the box drawn under it.
**Where:** p.92: Young Men's Christian Association … $350,000, directly over the "Trauma Recovery
Centers" bar
**Found by:** totals (Opioid Prevention and Treatment, p.91); looking at the page
**Tried:** FY2024's `open_top_rows`, which read the row as the bar table's "first row with no rule
above it".
**Fix:** `open_top_rows` off for FY2023 (it changes nothing else). PR.
**Status:** fixed

---

**Problem:** A table's last row has no left rule, so its name fell in no cell.
**Where:** p.93, Parks Equity Initiative: City Parks Foundation 13-3561657 $778,500
**Found by:** H7 (19 orphan characters)
**Fix:** `[[vector_pages]]` p.93: one vertical line at the table's left edge (x = 90.0). PR.
**Status:** fixed

---

**Problem:** The letter "I" of "Inc." fell in a 5 pt phantom column, so the name read
"…Jewish Poverty, nc." and the "I" was unclaimed.
**Where:** p.98, Metropolitan New York Coordinating Council on Jewish Poverty, Inc. $247,765
(Senior Services)
**Found by:** H7 (unmapped cell); ink coverage (114 px uncovered)
**Fix:** `sliver_chars` (config switch; `vector.read_page`): a glyph centred in a cell under 8 pt
wide whose box runs into one text cell goes to that cell; the row is flagged `W.sliver_char`.
Ink then finds 0 regions. PR.
**Status:** fixed, flagged in data

---

**Problem:** First letters of two box titles in their own cells ("E" | "nding the Epidemic",
"H" | "IV/AIDS Faith-Based").
**Where:** pp.60, 63
**Found by:** H11 (boxes "E", "H")
**Fix:** FY2025's `box_title_letters`. PR.
**Status:** fixed

---

**Problem:** A real purpose text matched the furniture check.
**Where:** p.176, BAFA - Bangladesh Academy of Fine Arts, Inc. $15,000: "… in conjunction with
Council Member" (the PDF's text, cut short)
**Found by:** H6
**Fix:** H6 now takes named exceptions by award and field (`code/schedc/checks.py`); one in
config. A warn in the review file. PR.
**Status:** flagged in data

---

**Problem:** The ink self-test failed: the test row's smallest letter did not fire.
**Where:** p.235, Laundromat Project, Inc. (the "i" is under 40 px at 300 dpi)
**Found by:** ink coverage acceptance
**Fix:** FY2023's region floor is 32 px; the clean run still finds 0 regions. In config. PR.
**Status:** fixed

---

**Problem:** Two initiatives on one page failing the same check got the same review id.
**Where:** p.43 (Initiative to Combat Sexual Assault; Innovative Criminal Justice Programs)
**Found by:** the review file (duplicate `review_id`)
**Fix:** the initiative is the item's `field` when two would collide
(`code/parse_schedule_c_v2.py`); no other year has such a pair, so their ids are unchanged. PR.
**Status:** fixed

---

**Problem:** The PDF's own numbers disagree, fourteen times, and one organization is printed with
another's EIN.
**Where:** boxes vs summary: p.83 Low Wage Worker Support ($120,000 vs $2,000,000), p.86 Autism
Awareness ($3,166,846 vs $3,316,846); rows or reserve vs box: pp.34, 43, 53, 54, 82, 136;
rounded statements: pp.42, 43, 44, 59; roll-up +$646,350; pp.13 and 175 Asiyah Women's Center
printed with Muslims Giving Back's EIN 822712941
**Found by:** totals (H11, H12, H13); an EIN-to-name scan (one EIN, two unrelated names)
**Tried:** looking for a parse loss: none. EIN census exact, ink coverage clean, rows re-added
by hand from the page text (pp.53, 136, 137).
**Fix:** none. Named exceptions and box aliases in config; the two box amounts and the two
Asiyah rows are critical known issues. In the review file.
**Status:** flagged in data

---

**Problem (checked, the epic's known issue):** the old parse lost two $5,000 Local rows.
**Where:** p.213 Elite Community Foundation, Inc. (EIN printed "84 -2079676"); p.235 Laundromat
Project, Inc., The (page shows 87-0753479; text layer "87 0753479")
**Found by:** known going in (epic #101; families/schedule-c-fy2008-fy2024.md; DATA-ANOMALIES §19)
**Fix:** none needed: the vector grid reads both rows; their EINs are H5 named exceptions (clean
EIN blank). Appendix B is $36,539,000, the pot. Golden test. PR.
**Status:** fixed (by the method), flagged in data

---

## Proposed DATA-ANOMALIES text

In the README, "Proposed DATA-ANOMALIES entry" (not added to `DATA-ANOMALIES.md`; the integrator
numbers it). §19's FY2023 row (Local $36,529,000) can then point to it.
