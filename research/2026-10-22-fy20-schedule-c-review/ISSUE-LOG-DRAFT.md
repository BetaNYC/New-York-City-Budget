# Draft #109 issue-log comments: FY2020 Schedule C (NOT posted)

**Written:** 2026-10-22 02:30 EDT. One block per problem, in the order found, in the shape #109
asks for. Each is meant to be its own comment on #109 once Noel approves. "PR" means the PR
that adds this folder; "promotion PR" the one that writes `data/fy20/pdf/schedule_c/`.

---

**Problem:** FY2020 had no config.
**Where:** `Fiscal-2020-Schedule-C-Final-Merge.pdf`, whole document (405 pages: 157 portrait,
248 landscape; pp.166–177 have a MediaBox origin of (−18, −18))
**Found by:** review (starting point for #109)
**Tried:** FY2021's config with FY2020 names and pages: 6,796 rows, 564 critical flags (327
h-rule notes on the appendix pages, 76 unknown headers, 9 unknown statements).
**Fix:** `config/schedule_c/fy2020.toml`. 27 categories from the 20 pt banners (pp.12–185;
"Children's Services", "Government Officials"); sections pp.1–11 front, 12–188 body, 189–217 /
218–358 / 359–405 appendices A / B / C; header labels "Legal Name - School", "Legal Name -
Program", "Councilmember". PR.
**Status:** fixed

---

**Problem:** Amounts printed with no "$" made the h-rule reader take member and appendix tables
apart, and would have put 5,025 rows in the review file.
**Where:** every member table (pp.13–25 Anti-Poverty, 27–32 Boroughwide Needs, 166–177 Speaker's)
and appendix page (pp.189–405): "5,500"
**Found by:** H7.hrule_splits (327 notes); H5; the review file count
**Tried:** a bare-amount word of any size: "151" in "Public School 151Q" and "108" in "P.S. 108"
then read as amounts (p.142's columns cut wrong, 38 characters across a split); comma-formatted
only: the $500 and $541 appendix rows (pp.254–258, 311, 315) were lost.
**Fix:** `bare_amounts` (config switch; `code/schedc/vector.py`, `structure.py`): in h-rule tables
an amount word may be bare, but only right of the EIN column and with the right-aligned amounts;
a bare amount in a table with a Council Member, Borough or Sponsor column is a routine flag
(`W.amount_bare`), anywhere else a review row. PR.
**Status:** fixed, flagged in data (5,025 rows, routine)

---

**Problem:** H-rule tables the reader could not cut: a Council Member column, rows two or three to
a band, a header in the first row's band, an 8-digit EIN as the first row.
**Where:** pp.38–41 (Digital Inclusion and Literacy, "Councilmember Legal Name of Organization |
EIN | Amount"); pp.84, 102, 187 (no rule between rows); pp.84, 187 (header and first row in one
band); p.134 (Amudim, "47-984801")
**Found by:** anchor census (H5: p.38 32 EIN words, 0 rows); H4 ("Councilmember Legal Name of
Organization")
**Fix:** `hrule_lead_column`, `hrule_split_lines`, `hrule_short_ein` (new); FY2023's
`hrule_header_split`. PR.
**Status:** fixed; the 6 cut rows are critical review rows (the image sees no rule there)

---

**Problem:** Designation statements worded 19 ways, one with its text beside the label.
**Where:** p.38 "will designate $640,000 post-adoption. The Council has designated"; p.118 "and has
designated $3 million directly to CUNY."; p.119 "post–adoption" (en dash); p.146 "The Borough
Presidents will designate the providers post-adoption."; p.114 "The City Council designated";
p.161 "Designation Method:" in bold, the statement a separate loose line beside it
**Found by:** structure (unknown statement: 9 boxes)
**Fix:** patterns in config; `statement_beside_label` (p.161). PR.
**Status:** fixed

---

**Problem:** Four summary tables went to the wrong category and one TOTAL failed.
**Where:** p.97 "Health Services" banner printed twice over itself; p.111 "Housing" banner in a
table with empty bands; p.145 "$3,383,670$3,383,670" (the page shows it once)
**Found by:** H10 ("Government Officials: 2 TOTAL lines"; "Housing has no summary table"; Senior
Services short $3,383,670)
**Fix:** `banner_variants`, `summary_amount_doubled` (config switches; flagged). PR.
**Status:** fixed, flagged in data

---

**Problem:** Smaller layout problems.
**Where:** p.42 Trans Equity Programs' box inside the LGBT table (FY2023's
`split_boxes_award_tables`); p.186 a name-column-only table, EINs and amounts beside it (FY2023's
`hrule_beside`); pp.162–164 the header drawn as one cell (`header_one_cell`); p.113 41
characters of a statement counted as orphans of the award table above (`orphans_in_gaps`); p.306
an EIN glued to the name before it in the text layer (a named `H5.page_words` exception, new in
`code/schedc/checks.py`)
**Found by:** H11, H5, H4, H7
**Fix:** as named. PR.
**Status:** fixed

---

**Problem:** The PDF's own numbers disagree eight times; three EINs are printed one row off;
three have the wrong length.
**Where:** p.46 Innovative Criminal Justice Programs rows −$200,000 (Carnegie Hall's NeON Arts
named in the scope, no row); p.45 +$2,000; rounded statements pp.47, 78, 86, 89, 94; p.79 a
box for the whole SAVE initiative over its parts' boxes; roll-up −$219,300. EINs one row off:
p.46 (Foundling, North Brooklyn Coalition, Safe Horizon). Wrong length: p.134 ×2, p.162
**Found by:** totals (H12, H13); comparison with `main` and the disclosure; anchor census
**Tried:** looking for a parse loss: none. p.46 as read matches the page character for
character.
**Fix:** none. Named exceptions and a critical known issue in config; in the review file.
**Status:** flagged in data

---

**Problem:** DATA-ANOMALIES §20's FY2020 merged row.
**Where:** p.162, "Urban Health Plan, Inc. 15-24042810 $88,855 NYC MWBE Alliance, Inc."
**Found by:** §20 list; `code/validate_data.py` `org_merged` on the first PDF parse
**Fix:** read from the table's cells: two awards, Urban Health Plan $88,855 (10-digit EIN, a review
row) and NYC MWBE Alliance, Inc. 82-1902677 $20,000. Test `test_golden20_header_in_one_cell_p162_p163`.
**Status:** fixed

---

## Proposed DATA-ANOMALIES text

In the README, "Proposed DATA-ANOMALIES entry" (not added to `DATA-ANOMALIES.md`; the integrator
numbers it).
