# Draft #108 issue-log comments: FY2021 Schedule C (NOT posted)

**Written:** 2026-10-22 01:55 EDT. One block per problem, in the order found, in the shape #108
asks for. Each is meant to be its own comment on #108 once Noel approves. "PR" means the PR
that adds this folder; "promotion PR" the one that writes `data/fy21/pdf/schedule_c/`.

---

**Problem:** FY2021 had no config.
**Where:** `Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf`, whole document (343 pages: 100
portrait, 243 landscape; every MediaBox starts at (0, 0))
**Found by:** review (starting point for #108)
**Tried:** FY2022's config with FY2021 names and pages: 58 unknown statements, 15 pages with EIN
words but fewer rows, a crash in the roll-up (a TOTAL printed without "$").
**Fix:** `config/schedule_c/fy2021.toml`. 26 categories from the 14 pt banners (pp.11–126;
"Children's Services", "Senior Services", "Veteran Services"); sections pp.1–10 front, 11–128
body, 129–157 / 158–295 / 296–343 appendices A / B / C; 19 summary titles (p.122's says "Fiscal
2020"). PR.
**Status:** fixed

---

**Problem:** Award-table headers printed outside the table's rules, so statements swallowed the
header and 15 pages lost rows.
**Where:** e.g. p.35 ("Legal Name of Organization | EIN" in cells, "Amount" loose beside them),
p.40 (the whole header loose under the statement), p.45 ("EIN" in a cell, the rest loose), p.56,
pp.85, 90
**Found by:** structure (44 unknown statements ending in "Legal Name …"); anchor census (H5)
**Tried:** FY2023's `loose_header` alone: it read the statement's last line as a header word
(p.56, p.85: the statement ends 13 pt above the table).
**Fix:** `header_band_words` (config switch; `code/schedc/structure.py` `_band_header`,
`code/schedc/checks.py` H7): a statement ends at a loose header line; loose words in a table's
first row band complete its header; under the switch `loose_header` reads only the line band
nearest the table and ignores statement lines. The words read are not counted as orphans by H7 or
as uncovered ink. PR.
**Status:** fixed, flagged in data (`W.band_header`, 81 rows)

---

**Problem:** Sub-headings inside an award table read as rows, or glued onto a name.
**Where:** pp.70–72, Community Housing Preservation Strategies: "Technical Assistance",
"Community Consultant Contracts", "Housing Preservation Initiative"
**Found by:** anchor census (H5: p.71 42 EIN words, 0 rows; p.72 19 and 0); "row without a readable
EIN" (p.70)
**Fix:** `award_subheadings` (config list; `structure.build`, `split_merged_tables`): rows
holding only a listed sub-heading are not award rows; the rows under each carry it in `purpose`;
a table that starts with one continues the award table before it. PR.
**Status:** fixed, flagged in data (`W.subheading`, 67 rows); where the sub-heading goes is a
decision for Noel

---

**Problem:** First letters and last digits in an 8.9 pt white column at a table's edges.
**Where:** pp.105–106 (Construction Site Safety Training, Create New Technology Incubators):
"L | egal Name", "E | ast River Development All", "$118,75 | 0"
**Found by:** structure (unknown header label "L"); anchor census
**Tried:** FY2023's `sliver_chars`: it only takes columns under 8 pt.
**Fix:** `edge_slivers` (config switch; `code/schedc/vector.py`): at a table's left and right
edge the sliver limit is 9.5 pt. PR.
**Status:** fixed, flagged in data (9 `W.sliver_char` review rows)

---

**Problem:** Four boxes the parse did not see as boxes.
**Where:** p.84 (Queens Borough Public Library: an empty band drawn above the title bar; its
statement was read onto the NYPL box), p.98 (NORCs: "$5,400,325" printed outside the box's rules),
p.60 (HIV/AIDS Faith-Based: statement inside the description cell), p.73 (Foreclosure Prevention
Programs: header and row cells don't line up)
**Found by:** H11 (box vs summary), H12, H5
**Fix:** `skip_empty_first_row`, `box_amount_loose`, `header_overlap_cells` (new), FY2025's
`statement_in_cell`. PR.
**Status:** fixed

---

**Problem:** A TOTAL printed without "$" and a box printed "$477,00".
**Where:** p.49 (Education, "TOTAL | 21,679,075"); p.122 (Initiative for Immigrant Survivors of
Domestic Violence, "$477,00"; its summary line $477,000)
**Found by:** H10 (summary row unreadable; the roll-up crashed on it); H11
**Fix:** `summary_amount_without_dollar` (read, flagged); `box_amount_read` (config list: page,
title and printed text must match; read as $477,000, printed text kept, a critical review row).
PR.
**Status:** fixed, flagged in data

---

**Problem:** The PDF's own numbers disagree, five times; six EINs have the wrong length; one
organization has two EINs.
**Where:** reserves while rows make the whole box: pp.44, 93, 107; rows $1 over: p.39; rounding:
p.55; roll-up +$129,070. EINs: pp.64, 65, 87, 89, 90, 91 (8 digits; p.60 prints two of them
correctly). Congregation Beit Simchat Torah: 11-2527706 (p.61) vs 23-7406899 (p.63)
**Found by:** totals (H12, H13); anchor census (H5); comparison with `main`
**Tried:** looking for a parse loss: none. EIN census exact, ink coverage clean.
**Fix:** none. Named exceptions in config; in the review file.
**Status:** flagged in data

---

## Proposed DATA-ANOMALIES text

In the README, "Proposed DATA-ANOMALIES entry" (not added to `DATA-ANOMALIES.md`; the integrator
numbers it).
