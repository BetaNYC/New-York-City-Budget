# Draft #102 issue-log comments: FY2027 Schedule C (NOT posted)

**Written:** 2026-10-20 22:45 EDT. One block per problem, in the order found, in the shape #102
asks for. Each is meant to be its own comment on #102 once Noel approves. "PR" means the PR
that adds this folder; "promotion PR" the one that writes `data/fy27/pdf/schedule_c/`.

---

**Problem:** The 2026-10-19 prototype (9,979 rows, $655,045,412) was scratch code outside the repo.
**Where:** `Fiscal-2027-Schedule-C-Final-3.pdf`, whole document
**Found by:** review (starting point for #102)
**Tried:** salvaging the scratch scripts. Kept the method (vector grid on drawn borders; image grid
per table region; image rows compared field by field) and rebuilt the rest as tooling.
**Fix:** `code/schedc/`, `code/schedc_cv/`, `code/parse_schedule_c_v2.py`,
`config/schedule_c/fy2027.toml`. Same result: 9,979 rows, $655,045,412. Re-run is byte-identical. PR.
**Status:** fixed

---

**Problem:** The old parser dropped Medicare Rights Center, $135,000.
**Where:** p.279, Speaker's Initiative (sponsor Felder, EIN 133505372, DFTA)
**Found by:** disclosure (earlier, DATA-ANOMALIES §23); now also ink coverage
**Tried:** —
**Fix:** cell-grid parsing reads it (`fy27-p279-t00-r012`; golden test). The ink check is proven on
this row: withholding it, or one letter of it, makes the check fire. PR.
**Status:** fixed

---

**Problem:** Long initiative titles wrap into a second row of the black title bar, so the box
title did not match its summary line.
**Where:** p.44 (NYC RISE with Adult Literacy Forward …), p.168 (Spay/Neuter …), p.179 (Homeowner
Stabilization Services …)
**Found by:** totals (H11, box vs summary line)
**Tried:** title from the first bar cell only (3 mismatches).
**Fix:** cells in the title's column that start above the bottom of the amount cell are part of the
title. 25 / 25 categories match. PR.
**Status:** fixed

---

**Problem:** Two designation statements picked up the next page's running sub-heading.
**Where:** p.115 (SU-CASA, then "Domestic Violence Services"), p.239 (Swim Safety, then "Public
Safety")
**Found by:** structure (unknown statement wording, a hard flag)
**Tried:** "read until the next table": crosses the page break.
**Fix:** a statement continues only on the line directly below it on the same page. 170 / 170
statements now match a known wording (122 full, 34 partial, 10 post-adoption only, 4 none). PR.
**Status:** fixed

---

**Problem:** Initiative boxes have no right-hand border, so the values beside "Agency:", "U/A:" etc.
fall in no cell.
**Where:** every initiative box (e.g. p.205)
**Found by:** character conservation (H7)
**Tried:** —
**Fix:** characters in a table but in no cell are read as loose text for the structure step. H7
counts them only inside award tables: 0 there. PR.
**Status:** fixed

---

**Problem:** A hyphen from the organization name pokes over the border into the EIN box, so the two
grids disagree on that cell.
**Where:** p.463, Center for Educational Innovation – Project BOOST & Porgrams, Thomas-Henry, $5,000
**Found by:** grid compare (H8); the only one of 9,979 rows that differs
**Tried:** —
**Fix:** EIN read as `134113613` (both grids agree on the digits), row flagged
`W.ein_overflow_hyphen` + `H8.lattice`. In the review file. PR.
**Status:** flagged in data

---

**Problem:** The PDF's own numbers are $1 apart.
**Where:** p.214, Support Our Older Adults: "has designated $7,229,999"; its 394 rows add to $7,229,998
**Found by:** totals (H12), and the same $1 in the roll-up (H13)
**Tried:** looking for a parse loss: none. The anchor census (9,979 EIN words = 9,979 rows), ink
coverage (0 regions) and both grids agree on every row of that initiative.
**Fix:** none. Named exception in config, matched on page and both amounts. In the review file.
**Status:** flagged in data

---

**Problem:** Text layer and pixels differ: "multi media" vs "multi-media".
**Where:** p.486, New York WEB Center, purpose
**Found by:** the 2026-10-19 prototype's OCR sample (docTR 0.983); not by this build, because both
grids read the same text layer
**Tried:** —
**Fix:** text layer kept as the record (PLAN open decision 4); listed as a known issue in config so
it reaches the review file.
**Status:** flagged in data

---

**Problem:** Two organization names break at a hyphen before "Council District", so the clean
value may be missing a space ("Meals-Council District 32").
**Where:** p.13 ($9,000) and p.315 ($5,625), God's Love We Deliver
**Found by:** review (line-end hyphen rule, PLAN §5.2)
**Tried:** reading all 80 line-end hyphens by hand: the other 78 are compound words.
**Fix:** kept as printed; raw text keeps the line break. In the review file.
**Status:** flagged in data

---

**Problem:** The City's EIN (13-6400434) pairs different agencies by amount alone.
**Where:** 9 rows, e.g. p.270 Department of Small Business Services $100,000 would pair with a DYCD
disclosure row
**Found by:** disclosure (PLAN H17, W4)
**Tried:** (EIN, amount) only: 9,859 matches, the prototype's number.
**Fix:** City-EIN rows also need the disclosure name to be a prefix of the PDF name: 9,850 matches.
Both numbers are in `fy27_sc_checks.txt`. PR.
**Status:** fixed (report only)

---

**Problem:** 129 PDF rows ($9,375,459) have no disclosure row, and 557 disclosure rows have no PDF row.
**Where:** `data/fy27_sc_disclosure_match.csv`
**Found by:** disclosure
**Tried:** —
**Fix:** none needed: the disclosure is a later snapshot (2026-10-12) with post-adoption
designations. Every row has one reason (amount differs, key used, EIN missing, City-EIN Pending …).
The PDF is never changed by it.
**Status:** report only

---

## Proposed DATA-ANOMALIES text

Added in the PR as §29 (FY2027 Schedule C rebuilt from the PDF).
