# Draft #107 issue-log comments: FY2022 Schedule C (NOT posted)

**Written:** 2026-10-21 23:58 EDT. One block per problem, in the order found, in the shape #107
asks for. Each is meant to be its own comment on #107 once Noel approves. "PR" means the PR
that adds this folder; "promotion PR" the one that writes `data/fy22/pdf/schedule_c/`.

---

**Problem:** FY2022 had no config.
**Where:** `Fiscal-2022-Schedule-C-Merge-6.30.21.pdf`, whole document (326 pages: 86 portrait,
240 landscape; every MediaBox starts at (0, 0))
**Found by:** review (starting point for #107)
**Tried:** FY2023's config with FY2022 names and pages: 5,671 rows; appendices already equal to
their pots; 3 categories with no summary table found, 20 unknown statements, 6 unknown headers.
**Fix:** `config/schedule_c/fy2022.toml`. 25 categories from the banners (pp.9–119; no
Community Safety and Victim Services; "Senior Services Initiatives"); sections pp.1–8 front,
9–121 body, 122–150 / 151–280 / 281–326 appendices A / B / C; Housing's summary title and
Environmental Initiatives' untitled table (p.49). PR.
**Status:** fixed

---

**Problem:** A summary TOTAL printed "TOTAL:" was not a TOTAL, so Community Development had none.
**Where:** p.32
**Found by:** H10 (0 TOTAL lines)
**Fix:** `total_colon` (config switch; `code/schedc/structure.py`). PR.
**Status:** fixed

---

**Problem:** Designation statements worded 74 ways, several new.
**Where:** p.37 "will designate $3,462,000 million post-adoption"; p.65 "has allocated $195,000
directly to the NYC Department of Housing Preservation and Development, $25,000 directly to the
Department of Consumer Affairs, and has designated the following provider"; p.112 "$100,000 will
be allocated to DYCD and will be designated post-budget adoption"; p.113 "The has designated";
pp.92–96 no final "."
**Found by:** structure (unknown statement: 20 boxes)
**Fix:** 12 patterns in config; `reserve...` groups now add up (`structure.statement_kind`), as
`designated...` groups did (no other year's pattern has two). "$3,462,000 million" is read as
$3,462,000 and is a review row. PR.
**Status:** fixed, flagged in data

---

**Problem:** A four-column award table ("Legal Name of Organization | EIN | Program | Amount",
no vertical rules) was lost: its rows read as initiative boxes ("Groove with Me, Inc.").
**Where:** pp.84–85, Art as a Catalyst for Change (40 rows, $720,000; also lost by the old parse)
**Found by:** anchor census (H5: p.84 14 EIN words, 0 rows; p.85 26 and 0); H11; H12
**Tried:** the h-rule path alone: it splits org | EIN | amount, so "13-3919147 P.S. 108K" sat in
the EIN cell.
**Fix:** `hrule_extra_column` (config switch; `vector.hrule_tables`): words between the EIN and
amount columns make a fourth column. The header, printed over two bands in the box table above,
is read with FY2025's `header_two_bands`; p.85 continues p.84. "Program" is read into `purpose`.
PR.
**Status:** fixed, flagged in data (`W.hrule_table`); where "Program" goes is a decision for Noel

---

**Problem:** Award rows drawn as one wide cell each (rules and an outer border, no column rules),
so name, EIN and amount were one text.
**Where:** pp.117–118, Young Women's Leadership Development (24 rows; p.117's last three and all
of p.118)
**Found by:** anchor census (H5: p.117 10 EIN words, 3 rows; p.118 21 and 0)
**Tried:** treating the table as a white-box table (`hrule_beside`-style "suspect"): it threw
away p.117's ruled Wrap-Around rows above.
**Fix:** `split_one_cell_rows` (config switch; `vector.split_one_cell_rows`): only the one-cell
rows holding an EIN and an amount, and the one-cell header, are cut at the EIN and amount words.
PR.
**Status:** fixed

---

**Problem:** A box printed "$ 250,000", a box inside the award table above it, and a box title
whose first letter is its own cell.
**Where:** p.37 (Discharge Planning), p.81 (Mental Health Services for Vulnerable Populations
under Hetrick-Martin's row), p.54 ("E" | "nding the Epidemic")
**Found by:** H11, H12
**Fix:** FY2023's `box_amount_dollar_space` and `split_boxes_award_tables`, FY2025's
`box_title_letters`. PR.
**Status:** fixed

---

**Problem:** The ink self-test did not fire when its row was withheld.
**Where:** p.84, Groove with Me, Inc. (the first row of a table with no header row of its own)
**Found by:** ink coverage acceptance
**Tried:** a lower region floor: no change, the row was never measured.
**Fix:** none in code. `run_cv` treats a table's first row as its header and counts its ink as
covered; for a headerless or loose-header table that is an award row (1 here, 42 in FY2023, 45
in FY2024). The self-test uses the table's second row (SEA, $18,000) and passes. Listed in the
README; a fix would change other years' outputs, so it is a decision for Noel.
**Status:** open (decision)

---

**Problem:** The PDF's own numbers disagree, eleven times, and five EINs have the wrong length.
**Where:** box vs summary: p.57 Public Health Funding Backfill ($4,467,933 vs $4,667,933);
reserves while rows make the whole box: pp.34 (×2), 39, 44, 85, 119; reserve and rows make
neither: pp.54, 58, 115; rounding: p.36; roll-up +$6,545,340. EINs: pp.48 (10 digits), 52, 79,
80, 82 (8 digits)
**Found by:** totals (H11, H12, H13); anchor census (H5)
**Tried:** looking for a parse loss: none. EIN census exact, ink coverage clean.
**Fix:** none. Named exceptions and box aliases in config; p.57 is a critical known issue. In the
review file.
**Status:** flagged in data

---

## Proposed DATA-ANOMALIES text

In the README, "Proposed DATA-ANOMALIES entry" (not added to `DATA-ANOMALIES.md`; the integrator
numbers it).
