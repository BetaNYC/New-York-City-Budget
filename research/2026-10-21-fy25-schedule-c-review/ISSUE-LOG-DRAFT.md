# Draft #104 issue-log comments: FY2025 Schedule C (NOT posted)

**Written:** 2026-10-21 19:25 EDT. One block per problem, in the order found, in the shape #104
asks for. Each is meant to be its own comment on #104 once Noel approves. "PR" means the PR
that adds this folder; "promotion PR" the one that writes `data/fy25/pdf/schedule_c/`.

---

**Problem:** FY2025 had no config; the toolkit had run on FY2027 and FY2026 only.
**Where:** `Fiscal-2025-Schedule-C-MERGE-FINAL-2.pdf`, whole document (455 pages; 792×612,
612×792, 1056×816 and 990×765; MediaBox origin 0 on every page, so no offset)
**Found by:** review (starting point for #104)
**Tried:** the FY2026 config with FY2025 names and pages: 9,577 rows, 9 of 25 categories found,
17 unknown headers, 19 unknown statements, 217 unmapped cells, and two crashes on a box amount
the parse could not read.
**Fix:** `config/schedule_c/fy2025.toml`. 26 categories from the 20 pt banners (Libraries and
"Mental Health" are new; "Cultural Organization" is singular); sections pp.1–9 front, 10–267
body, 268–293 / 294–412 / 413–455 appendices A / B / C. The crash: a `None`-safe money format in
`code/schedc/reconcile.py` and `code/parse_schedule_c_v2.py`. PR.
**Status:** fixed

---

**Problem:** 17 categories' summary tables were not found.
**Where:** 17 different titles ("Fiscal 2025 Community Development Initiatives" p.34, "… Council
Libraries Initiatives" p.174, "Fiscal 2025 Mental Health Services" p.176, …); Criminal Justice
Services (p.59) prints no title row; Parks and Recreation Services (p.202) prints no summary
table at all
**Found by:** totals (H10: category with no summary table)
**Fix:** `summary_titles` lists all 18 forms (the 17 titles, plus the bare "Agency | Initiative
| Amount" header of p.59). Parks: a new `[[no_summary]]` config list
(`code/schedc/reconcile.py`, `H10.no_summary`): the category passes only when named, is a warn in
the review file, and its box stands in for its TOTAL in the roll-up. Known going in (PLAN §10).
PR.
**Status:** fixed; Parks flagged in data

---

**Problem:** "Council" and "Member" are printed in two row bands with a rule between them, so
"Council" was an unknown header and "Member" a fake award row.
**Where:** pp.131–144 (NYC Cleanup's member tables)
**Found by:** headers (H4), furniture in data cells (H6: 28 cells)
**Fix:** `header_two_bands` (config switch): when row 0 has an unknown label, row 1 holds no EIN
and no amount, and every row-1 text sits under a row-0 cell, the two are read as one header,
but only if every joined label is known. PR.
**Status:** fixed

---

**Problem:** Statements state amounts in millions, and are worded 30 ways.
**Where:** "has designated $4.1 million" (9 initiatives, pp.36–222); "to the following
organizations" (p.146); "in Fiscal 2025" (pp.149–153); two typos ("The City Council for Fiscal
2025 and will designate", p.60; "has designated and has designated", p.129); Libraries "This
funding is directly allocated to the Brooklyn Public Library." (p.174)
**Found by:** structure (unknown statement wording is a hard flag; 19 of them)
**Fix:** `statement_amount` in `code/schedc/structure.py` reads "$4.1 million" at face value
(4,100,000), so a rounded figure fails H12 and becomes a review row rather than passing on a
tolerance. Six statement patterns in config, each citing its pages. 155 / 160 initiatives have a
statement that matches a pattern; the other 5 are member-item initiatives and print none. PR.
**Status:** fixed

---

**Problem:** A box's first letter is drawn apart from its title, so titles read "igital
Inclusion…", "E", "V".
**Where:** p.36 "D" just left of the table's left rule (outside every cell); p.149 "E" | "nding
the Epidemic" and p.258 "V" | "eteran Resource Centers", "V" | "eterans Community Development",
each first letter in its own 6–9 pt cell
**Found by:** box vs summary (H11)
**Tried:** the FY2026 sliver rule (cells under 8 pt): it misses the 8.8 pt cells of p.258, and
it never ran on box titles.
**Fix:** `box_title_letters` (config switch): a 1–2 character first cell that abuts the next is
joined to it; a 1–2 character loose line straddling the table's left rule in row 0 is put in
front. H11 then confirms all four titles against their summary lines. PR.
**Status:** fixed

---

**Problem:** An award table's whole name column was missing: 10 rows read with an EIN and an
amount but no name.
**Where:** p.167, Immigrant Opportunities Initiative (Ansob Center for Refugees … City University
of New York – CUNY School of Law)
**Found by:** headers (H4: header lacks org)
**Tried:** looking at the page: the table is fully ruled. pdfplumber's default 3 pt snap moves the
table's left rule (x 67.2) onto the box border above it (x 64.4); the row rules start at 67.7, so
they no longer meet it, and no cells are formed. `intersection_tolerance` 5 merged the table with
the box above.
**Fix:** per-page pdfplumber settings in config (`[[vector_pages]]`, read by
`code/schedc/vector.py`): p.167 only, `snap_tolerance` 1. Every other page uses the defaults.
The image grid agrees with all 10 rows. PR.
**Status:** fixed

---

**Problem:** An amount's last digit sits past the rule that ends its cell, so "$200,00" was
unreadable and "0" was an unmapped cell.
**Where:** p.222 Pride at Work, 5 rows (a white-filled phantom column inside the drawn border);
p.260 box "HRA Teen RAPP $250,00" + "0" outside the table's right rule
**Found by:** anchor census (H5), unmapped cells (H7), box vs summary (H11: box amount
unreadable)
**Tried:** looking at the page: it shows $200,000 and $250,000 (crops).
**Fix:** `amount_sliver_join` (config switch): only when the amount ends in an incomplete
thousands group and the 1–2 digits sit in a ≤10 pt cell abutting it (or a loose line at the
table edge), and the two read as one amount. Every such row is a review row
(`W.amount_split_digits`). PR.
**Status:** fixed, flagged in data

---

**Problem:** Two amounts are printed with cents or a trailing period.
**Where:** p.168 Haitian Americans United for Progress "$77,000.00"; p.170 Northern Manhattan
Improvement Corporation "$50,000."
**Found by:** anchor census (H5: rows without an amount)
**Fix:** `amount_odd_format` (config switch): ".00" or "." only, read as whole dollars, flagged
`W.amount_odd_format`, in the review file. PR.
**Status:** fixed, flagged in data

---

**Problem:** A second initiative box is drawn inside the first box's ruled table, under its
statement, so its title and amount were read as part of the statement.
**Where:** p.35, "Adult Literacy Pilot Project | $2,500,000" (row 11 of the Adult Literacy
Initiative table)
**Found by:** box vs summary (H11: summary line with no box)
**Tried:** splitting any row ending in "$N": it split every summary table.
**Fix:** `split_boxes` (config switch): only a row met while reading a statement, with no EIN,
ending in "$N", starts a new table. PR.
**Status:** fixed

---

**Problem:** A box amount is cut into three cells by phantom column rules.
**Where:** p.157, CUNY Social Work Fellows: "$" | "5" | "00,000"
**Found by:** box vs summary (H11: summary line with no box)
**Fix:** `box_amount_cells` (config switch): the last 2–4 cells of row 0, joined, must read as
one amount; flagged `W.box_amount_cells`, in the review file. PR.
**Status:** fixed, flagged in data

---

**Problem:** A designation statement is printed inside the "Scope of Service" cell, so the box
looked like it had no statement and no rows.
**Where:** p.168, Legal Services for Low-Income Immigrants ($4,400,000): "… for Fiscal 2025
only." / "Designation Method: The Council will designate awards post-adoption."
**Found by:** totals (H12: a box with no statement and $0 in rows)
**Fix:** `statement_in_cell` (config switch): text from "Designation Method:" inside a
description row is read as the statement. PR.
**Status:** fixed

---

**Problem:** Two rows are cut into more cells than their header, so the name fell in a cell no
column claimed.
**Where:** p.183, Astor Services for Children & Families ($673,888) and Rising Ground, Inc.
($800,000): the name sits in a cell x 77–230; the header's centre is in an empty cell 230–409
**Found by:** unmapped cells (H7)
**Fix:** `header_span_cells` (config switch): an unclaimed text cell goes to the header cell over
its centre, if that column read empty. Flagged `W.header_span_cell`. The image grid read both
rows the same way. PR.
**Status:** fixed, flagged in data

---

**Problem:** The CUNY Research Institutes award table is headed "Institute", which neither side
knew.
**Where:** p.156 (6 rows, $4,500,000)
**Found by:** headers (H4); then grid compare (H8: 6 rows the image grid could not see)
**Fix:** header label "Institute" → org in config; `extra_roles` adds the same word to the image
side's header table (`code/schedc_cv/imagegrid.py`, config-driven, empty for FY2026/FY2027). All 6
rows agree. PR.
**Status:** fixed

---

**Problem:** An EIN is printed with two hyphens.
**Where:** p.181 Safe Horizon, Inc., "13-294-6970" ($150,000)
**Found by:** anchor census (H5)
**Fix:** clean EIN left blank, printed value kept; named exception. In the review file. This is
also the one disclosure match fewer than the prototype (9,385 vs 9,386).
**Status:** flagged in data

---

**Problem:** Box and summary names differ in 16 places; one summary line stands for two boxes;
the four library lines are all called "Fiscal 2025 Subsidy".
**Where:** pp.42, 59, 114 (SAVE: $2,450,000 = $1,850,000 + $600,000), 153, 155, 156 ×2, 163, 174
×4, 178, 179, 181, 212
**Found by:** box vs summary (H11)
**Fix:** none to the data. Named `box_aliases` in config, each matched exactly; each use is a
warn in the review file. Rows carry the box title. Two aliases on one page shared a review id;
they now take the box title as their `field` (only where a page has two;
`code/schedc/reconcile.py`). PR.
**Status:** flagged in data

---

**Problem:** The PDF's own numbers disagree, five times.
**Where:** p.115 Education: TOTAL $39,924,300, lines add to $39,974,300 (+$50,000). p.64 CASA:
reserve $2,066,000 + designated $14,680,000 = $16,746,000, box $17,340,000 (−$594,000). p.167
Immigrant Opportunities: "has designated $2,562,000", 31 rows add to $2,535,000 (−$27,000).
p.222 Pride at Work: "has designated $3.2 million" for a $501,000 box whose rows add to $451,000.
p.60 Combat Sexual Assault: "$4.1 million" for rows adding to $4,091,000.
**Found by:** totals (H10, H12), and the −$571,000 roll-up (H13), which is exactly the first three
**Tried:** looking for a parse loss: none. Every page has as many rows as EIN words, ink coverage
finds 0 regions, the image grid agrees on every row of those initiatives; p.115's lines added by
hand from the page image; pp.64, 222 read off the page.
**Fix:** none. Named exceptions in config, matched on page and both amounts. In the review file.
**Status:** flagged in data

---

**Problem:** 211 PDF rows ($7,348,995) have no disclosure row, and 1,908 disclosure rows have no
PDF row.
**Where:** `data/fy25_sc_disclosure_match.csv`
**Found by:** disclosure
**Fix:** none needed: the FY2025 disclosure is a later snapshot (sheet "FY25 (09-14-26)") with
post-adoption and transparency-resolution changes. Every row has one reason. Without the City-EIN
name rule 9,385 rows match: the prototype's 9,386 less Safe Horizon (above).
**Status:** report only

---

**Problem (checked, none found):** DATA-ANOMALIES §20 lists one FY2025 row where the old parse
put one award's text in another's name.
**Where:** p.233, Speaker's Initiative: Corbin Hill Food Project's purpose ("…farm shares to $12
per share…") had landed in Council For Unity, Inc.'s name
**Found by:** review (§20 list)
**Fix:** none needed: the cell grid reads them as two awards, Corbin Hill Food Project, Inc., The
(46-1206478, $50,000) and Council For Unity, Inc. (11-2880221, $50,000); the image grid agrees.
Golden test `test_golden25_section20_row_comes_back_split_p233`.
**Status:** fixed (by the method)

---

## Proposed DATA-ANOMALIES text

Added in the PR as §32 (FY2025 Schedule C rebuilt from the PDF).
