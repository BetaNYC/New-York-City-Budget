# Draft #111 issue-log comments: FY2018 Schedule C (NOT posted)

**Written:** 2026-10-22 05:50 EDT. One block per problem, in the order found, in the shape #111
asks for. Each is meant to be its own comment on #111 once Noel approves. "PR" means the PR
that adds this folder; "promotion PR" the one that writes `data/fy18/pdf/schedule_c/`.

---

**Problem:** FY2018 had no config.
**Where:** `FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf`, whole document (357 pages: 96
portrait, 261 landscape; pp.115–119 blank)
**Found by:** review (starting point for #111)
**Tried:** FY2019's config with FY2018 names and pages: 5,486 rows; Appendix A unread (h-rule
reader); 30 unknown statements; box and summary names apart in 13 categories.
**Fix:** `config/schedule_c/fy2018.toml`. 26 categories from the 20 pt banners (pp.11–126; no
Libraries); sections pp.1–10 front, 11–129 body, 130–162 / 163–307 / 308–357 appendices A / B /
C; nine summary tables titled without "Council"; headers "Cultural Organization - School"
(pp.45–50), "School" (pp.92–93). PR.
**Status:** fixed

---

**Problem:** Appendix A prints every amount with cents, and the reader took its ruled tables
apart.
**Where:** pp.130–162, "$30,000.00" (DATA-ANOMALIES §21 `fy18_aging_shift`: the old parse ran
the cents into every purpose)
**Found by:** H4 ("Council Legal Name of Organization Member" as one header cell); the vector
pass marked the tables suspect (an EIN row with no amount word)
**Fix:** `amount_cents` (`code/schedc/vector.py`, `structure.py`): "$N.00" is an amount word;
read as whole dollars in a member or appendix table, a routine flag. 537 rows, $5,610,000, the
pot. PR.
**Status:** fixed, flagged in data (routine)

---

**Problem:** "Fiscal Conduit" and "FC EIN" columns FY2019 does not have.
**Where:** Boroughwide Needs (pp.27–35) and all three appendices
**Found by:** H4 (unknown labels on every appendix page and pp.27–35); H5 (an FC EIN is an EIN-shaped word with no row)
**Tried:** a new output column: rejected, it would change the award and review columns the
explorer reads.
**Fix:** header labels `conduit`, `conduit_ein`; a row printing one is a warn review row
(`W.fiscal_conduit`, 50 rows) carrying both as printed; the FC EIN counts in the anchor census
(`code/schedc/checks.py`). Two of the 50 are odd: p.271 prints "Please indicate the actuals
schools." in the conduit column; p.242 an 8-digit FC EIN. PR.
**Status:** fixed, flagged in data (decision for Noel: a column?)

---

**Problem:** TOTAL rows inside award tables were read as awards with no EIN.
**Where:** 14 tables, e.g. p.64 "TOTAL | $1,187,000" under Access Health NYC
**Found by:** H12 (Health and Mental Health boxes' rows twice the box); H5 (rows without an EIN)
**Fix:** `award_table_totals`: not an award; checked against its rows (`H12.table_total`). 13
tie; p.86 Autism Awareness does not (below). PR.
**Status:** fixed

---

**Problem:** Box titles printed above their table, so the parts of two initiatives went
missing.
**Where:** p.53 (SAVE's three parts); pp.94–97 (Crisis Management System's eight parts):
"Crisis Management System – Cure Violence  $4,775,000" in the band over a table starting at
"Agency:"
**Found by:** H12 (Crisis Management System's rows $1,507,734 short); H11
**Fix:** `box_title_above`; warn review rows. PR.
**Status:** fixed, flagged in data

---

**Problem:** A row printed between two ruled tables was dropped without any check noticing.
**Where:** p.107, "Urban Health Plan, Inc. | 15-24042810 | $88,855" (MWBE Leadership
Associations; DATA-ANOMALIES §20's row, as FY2020 p.162)
**Found by:** H12 (the box's rows $88,855 short). The anchor census missed it (a 10-digit EIN is
not EIN-shaped) and so did the ink check (no table there)
**Tried:** FY2020's `hrule_short_ein` alone: the h-rule stack ran on into the next ruled table
and merged its two rows, and the row was read as an initiative box.
**Fix:** `short_ein_rows` (a row with a wrong-length EIN is not a box) and `hrule_skip_kept` (an
h-rule stack ends at a ruled table, and skips one at its head, as on p.93). PR.
**Status:** fixed; the EIN is a named exception and a review row

---

**Problem:** Statements worded 10 ways, five new.
**Where:** p.36 "will designate allocation post-budget adoption"; p.38 "this initiative"; p.99
"The Borough Presidents will designate the organizations and the amount each will receive …";
straight to an agency (pp.39, 62, 67, 69, 76, 80, 91, 94, 125–127); p.101 NORCs' two reserves;
p.98 and p.124 the provider named in words
**Found by:** structure (unknown statement: 30 boxes)
**Fix:** patterns in config. PR.
**Status:** fixed

---

**Problem:** The PDF's own numbers disagree.
**Where:** p.38 Community Development TOTAL $100,000 over its lines; p.69 Merit-Based
Scholarships box $15,000,000, summary $14,924,669; p.93 Crisis Management System box $12,734 over
its parts; rows vs box: p.57 −$500, p.80 −$60,000, p.85 +$55,000 (and its TOTAL row), p.95
+$40,000 (Street Corner Resources printed twice), p.124 −$146,000 (DYCD named, no row), p.127
−$20,000; reserves printed again as City-agency rows: p.36 ACS $481,197, p.101 DFTA $2,429,000.
Roll-up +$2,754,028 = all of these
**Found by:** totals (H10–H13)
**Tried:** looking for a parse loss in each: none (each page's text layer adds up the same way).
**Fix:** none. Named exceptions in config; in the review file.
**Status:** flagged in data

---

**Problem:** An EIN that is another organization's.
**Where:** p.55, Good Shepherd Services, $207,000, prints 46-1227433 (New York City Community
Learning Schools')
**Found by:** comparison with `main` (repaired from the disclosure) and the disclosure
**Fix:** none; a critical known issue in config.
**Status:** flagged in data

---

**Problem:** The same Jobs to Build On partner list as FY2019, on one page, its header cut
differently.
**Where:** p.106 (28 rows in three ruled tables; "Amount Service Type" in one header cell)
**Found by:** H4, H5
**Fix:** FY2019's `side_lists`, now reading the headerless tables under the list and each row's
"$" amount from its text (FY2019's result unchanged). PR.
**Status:** flagged in data (decision for Noel)

---

**Problem:** DATA-ANOMALIES §20's 94 FY2018 merged rows.
**Where:** the old parse (`data/fy18/schedule_c/fy18_schedule_c_awards.csv` at `26a5ab8`), e.g.
"Street Corner Resources, Inc. 26-0149521 * $40,000 SCAN-New York Volunteer Parent-Aides
Association, Inc." (p.96). 93 of the 94 lost the row boundary at a "*"; one at Urban Health
Plan's 10-digit EIN (p.107).
**Found by:** §20 list; `code/validate_data.py` `org_merged` on the first PDF parse
**Fix:** read from the table's cells: the 94 rows are **224 separate awards**, each found in this
parse on (EIN, amount). Row by row: `data/fy18_sc_s20_check.csv`, made by `s20_check.py`. Test
`test_golden18_short_ein_row_between_tables_p107`.
**Status:** fixed

---

**Problem:** #59: the old parser read no row of Appendices B and C in FY2018.
**Where:** pp.163–357, amounts with no "$"
**Found by:** #59
**Fix:** FY2020's `bare_amounts`: 3,949 rows, $44,189,000, each appendix equal to its pot. PR.
**Status:** fixed

---

## Proposed DATA-ANOMALIES text

In the README, "Proposed DATA-ANOMALIES entry" (not added to `DATA-ANOMALIES.md`; the integrator
numbers it).
