# Draft #103 issue-log comments: FY2026 Schedule C (NOT posted)

**Written:** 2026-10-21 00:50 EDT. One block per problem, in the order found, in the shape #103
asks for. Each is meant to be its own comment on #103 once Noel approves. "PR" means the PR
that adds this folder; "promotion PR" the one that writes `data/fy26/pdf/schedule_c/`.

---

**Problem:** FY2026 had no config; the toolkit was built on FY2027 only.
**Where:** `Fiscal-2026-Schedule-C-4.pdf`, whole document (469 pages; portrait 612×792 and
landscape 792×612, no /Rotate)
**Found by:** review (starting point for #103)
**Tried:** the FY2027 config with FY2026 names and pages: 9,061 rows, 704 EIN words with no row,
6 unknown headers, 6 unknown statements.
**Fix:** `config/schedule_c/fy2026.toml`. Categories from the 20 pt banners (not the ToC, which
says "DOMESTIC VIOLENCE" and "HIGHER EDUCATION INITIATIVES" in capitals); sections pp.1–10 front,
11–279 body, 280–305 / 306–426 / 427–469 appendices A / B / C. PR.
**Status:** fixed

---

**Problem:** On portrait pages the initiative box, its description, its statement and its award
table are one ruled table, so the award header is row 12, not row 0, and the rows were lost.
**Where:** 80 tables, e.g. p.36 (AAPI Community Support: 32 row bands in one table)
**Found by:** anchor census (H5): 61 pages with fewer rows than EIN words
**Tried:** —
**Fix:** `split_merged_tables` (config switch): split at the award header; the statement rows
become text lines, as FY2027 prints them. Row indices kept as printed. PR.
**Status:** fixed

---

**Problem:** A rule is drawn between the two lines of a long name, so the second line is its own
row band with no EIN and no amount.
**Where:** 8 rows, e.g. p.130 Young Men's and Young Women's Hebrew Association of Washington
Heights / "and Inwood"; p.48 an empty band under a two-line amount
**Found by:** anchor census (more rows than EIN words on pp.48, 130, 183)
**Tried:** joining any band with no EIN and no amount: it also took text that a band only sees
through the taller EIN cell above it.
**Fix:** `continuation_rows` (config switch): a band whose own cells (not cells spanning down from
above) hold no EIN and no amount joins the row above, line break kept, flagged
`W.continuation_row`. The image grid read all 8 joined names the same way on its own. PR.
**Status:** fixed, flagged in data

---

**Problem:** Award tables continue onto the next page without repeating their header, so they
were not read; a one-row carry-over even looked like an initiative box ("… | $98,469").
**Where:** p.48 (1 row), p.157 (1 row), p.195 (4 rows)
**Found by:** anchor census; then box vs summary (3 fake boxes)
**Tried:** —
**Fix:** `headerless_continuation` (config switch): a table continues the last award table when
nothing came between and the previous header's EIN and amount columns land on an EIN and an
amount. The image side does the same with its own last header (`carry_header`). Flagged
`W.headerless_table`. PR.
**Status:** fixed, flagged in data

---

**Problem:** The image grid cannot see a table one row tall.
**Where:** p.48 Pursuit Transformation Company $417,203; p.157 Tell Every Amazing Lady About
Ovarian Cancer Foundation $98,469
**Found by:** grid compare (H8: `no_image_row`)
**Tried:** carrying the image header over (fixed p.195's 4 rows, not these). The table's vertical
rules are ~53 px at 300 dpi, shorter than the 60 px kernel, so no region is found.
**Fix:** none: a smaller kernel would also start to read glyph stems as rules (11 pt stem ~33 px).
Both rows in the review file; the EIN census and ink coverage cover them.
**Status:** flagged in data

---

**Problem:** Designation statements are worded 60 ways, and three mean something FY2027 never
says.
**Where:** "will designate awards post-adoption" (14, e.g. p.111 SU-CASA); "has designated $N to
the following providers" (p.189); "designated directly to the City University of New York"
(pp.162–164); text-layer splits "h as" (p.170), "designate d" (p.166), "Fiscal 2026 :" (p.170)
**Found by:** structure (unknown statement wording is a hard flag)
**Tried:** —
**Fix:** six statement patterns in config, each citing its page; new kinds `reserve_all`,
`designated`, `direct` in `code/schedc/reconcile.py`. 155 / 155 statements match a pattern (the other
4 initiatives are member items and print none). PR.
**Status:** fixed

---

**Problem:** A box's first letters sit in a 5 pt sliver cell, so "Designation Method:" read as
"esignation Method:" and the statement was missed.
**Where:** p.162 (Care Workers for Our Future and two more)
**Found by:** structure (3 CUNY initiatives with no statement, so their $0 rows failed H12)
**Tried:** —
**Fix:** a sliver's letters are put back in front of their own row band (by the letter's
vertical centre) when reading box and statement rows. Never used for award cells. PR.
**Status:** fixed

---

**Problem:** Box titles that wrap put the amount on the second line; two boxes print title and
amount in one cell.
**Where:** p.157 Healthy Beginnings, HIV/AIDS Pathways to Care; pp.218, 220 (BID
Containerization $5,000,000 and three more)
**Found by:** box vs summary (H11), and rows attached to the wrong initiative (H12 on p.156,
Cancer Services)
**Tried:** —
**Fix:** `box_amount_on_second_row` (config switch); one-cell boxes split at the trailing "$N".
PR.
**Status:** fixed

---

**Problem:** Two categories title their summary table differently.
**Where:** p.153 "Fiscal 2026 Food Initiatives", p.162 "Fiscal 2026 Higher Education Initiatives"
**Found by:** totals (H10: category with no summary table)
**Fix:** `summary_titles` list in config. 25 / 25 categories found. PR.
**Status:** fixed

---

**Problem:** Box and summary names differ in 11 places; one summary line stands for three boxes.
**Where:** pp.47, 126 (SAVE: $2,450,000 = $1,275,000 + $600,000 + $575,000), 129, 160, 163, 170,
178, 183, 184, 187, 217
**Found by:** box vs summary (H11)
**Tried:** —
**Fix:** none to the data. Named `box_aliases` in config, each matched exactly; each use is a warn
in the review file. Rows carry the box title.
**Status:** flagged in data

---

**Problem:** Two EINs are printed with 8 digits.
**Where:** p.158 Brooklyn Center for Quality Life "26-265183" ($27,348); p.379 Morris Heights
Health Center "61081232" ($5,000)
**Found by:** anchor census (H5); known going in (#103)
**Fix:** clean EIN left blank, printed value kept; named exceptions. In the review file.
**Status:** flagged in data

---

**Problem:** An amount is printed without its "$".
**Where:** p.111 Ghetto Film School, Inc., "75,000"
**Found by:** anchor census (H5), and its initiative's rows summing to $0 (H12)
**Fix:** `amount_without_dollar` (config switch): digits-and-commas only, flagged
`W.amount_no_dollar`. In the review file. PR.
**Status:** fixed, flagged in data

---

**Problem:** An unmapped glyph: pdfplumber writes "(cid:9)", the page shows an empty box.
**Where:** 6 glyphs in 5 rows, e.g. p.344 "District 36.(cid:9)(cid:9)"
**Found by:** review (a crop of p.344)
**Fix:** raw keeps it; the clean value drops it (a fourth clean rule), flagged `W.cid_glyph`. PR.
**Status:** fixed, flagged in data

---

**Problem:** A name's trailing hyphen runs over the border into the EIN box, so the grids
disagree on that cell (the FY2027 p.463 shape, other way round).
**Where:** p.344 Parks – Archie Spigner Park, $10,000; p.421 Victory Music and Dance Company,
$20,000
**Found by:** grid compare (H8)
**Fix:** none needed: the vector grid keeps the hyphen with the name, as on the page; the EIN
digits agree. In the review file.
**Status:** flagged in data

---

**Problem:** The PDF's own numbers disagree, twice.
**Where:** p.173 Immigrant Services: TOTAL $86,091,341, lines add to $86,092,141 (+$800). p.98
Cultural Immigrant Initiative: "has designated $6,798,000", 383 rows add to $6,783,000 (−$15,000).
**Found by:** totals (H10, H12), and the same −$14,200 in the roll-up (H13)
**Tried:** looking for a parse loss: none. Every page has as many rows as EIN words, ink coverage
finds 0 regions, the image grid agrees on every row of that initiative; p.173 read off the page.
**Fix:** none. Named exceptions in config, matched on page and both amounts. In the review file.
**Status:** flagged in data

---

**Problem:** The ink self-test failed on the chosen row: withholding its smallest character (a
comma) fired nothing.
**Where:** p.176 Bronx Defenders, The, $5,533,333 (one of the 13 rows the old parser lost)
**Found by:** ink coverage acceptance
**Tried:** p.12's first row: the same result.
**Fix:** the test now withholds the smallest letter or digit ('f': fires), and `checks.txt` also
reports the comma result: a lone comma or period is under the 64 px region floor. H7 (every
character lands in a cell) is the check that covers it. PR.
**Status:** fixed (limit written down)

---

**Problem:** 255 PDF rows ($21,432,686) have no disclosure row, and 2,254 disclosure rows have no
PDF row.
**Where:** `data/fy26_sc_disclosure_match.csv`
**Found by:** disclosure
**Fix:** none needed: the FY2026 disclosure is a later snapshot (sheet "FY26 (09-14-26)") with
post-adoption and transparency-resolution changes. Every row has one reason. Without the City-EIN
name rule 9,529 rows match: the 2026-10-19 prototype's number.
**Status:** report only

---

## Proposed DATA-ANOMALIES text

Added in the PR as §30 (FY2026 Schedule C rebuilt from the PDF).
