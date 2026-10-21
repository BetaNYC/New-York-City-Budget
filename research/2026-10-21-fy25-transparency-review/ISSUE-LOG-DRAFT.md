# Draft #104 issue-log comments: FY2025 transparency resolutions (NOT posted)

**Written:** 2026-10-21 19:20 EDT. One block per problem, in the order found, in the shape #104
asks for. Each is meant to be its own comment on #104 once Noel approves. "PR" means the PR that
adds this folder; "promotion PR" the one that writes `data/fy25/pdf/transparency/`.

---

**Problem:** No FY2025 config; the FY2026 reader had FY2026 written into a few places (row ids
`fy26-tr…`, the Schedule C and retired-CSV paths, one check message).
**Where:** `code/transreso/structure.py`, `disclosure.py`, `checks.py`, `code/parse_transparency_v2.py`
**Found by:** reading the code before the run
**Tried:** —
**Fix:** the year comes from `--fy`; `config/transparency/fy2025.toml` holds every FY2025 fact.
A year with no retired CSV (FY2025 has none) is reported as such. FY2026 re-run byte-identical
(10 data files and 24 crops). PR.
**Status:** fixed

---

**Problem:** Chart counts and labels did not tie on the first run: Reso 11 printed "Charts 1
through 18" and 17 were found; three chart pages had no "Page n".
**Where:** Reso 11 p.6; Reso 02 pp.74-75; Reso 03 p.28
**Found by:** T3 (chart numbering, printed chart count, page labels)
**Tried:** —
**Fix:** Reso 11 p.6 prints "CHART #4 Anti-Poverty" with no colon; the caption reader now takes
the colon as optional and lists the page (`W.caption_format`). 18 / 18. The three pages really
print no label, and the next label counts them (p.76 is "Page 74"); named exceptions in the
config (`T3.page_label`), in the review file. PR.
**Status:** fixed; flagged in data (4 review rows)

---

**Problem:** A header the reader did not know: "Member/Borough".
**Where:** Reso 08 p.12
**Found by:** T4 (headers)
**Tried:** —
**Fix:** added to the label list as the member column. PR.
**Status:** fixed

---

**Problem:** Staff notes printed in a column past the `*` column, past the table's right rule and
off the page. Only "01/" shows, in the `*` column. The reader did not count the rest.
**Where:** Reso 07 pp.29-30, 4 purpose-of-funds rows ("01/22; placeholder - program name & Purpose
fo funds change"; "01/22; DCLA: We checked Midori’s final CDF report and they did do activity at
PS536X so that change is ok. ; proram name & POF change as per CBO's request")
**Found by:** T11 (the `*` column held "01/"), then a scan of every FY2024-2026 page for letters
off the page
**Tried:** (1) cut at the page edge: "01/22; D" counted as visible, but a 6× render shows the page
cuts the text at the table's right rule (771.9 pt), after "01/". The image grid disagreed.
(2) Cut at the table's edge. FY2026 has off-page letters too (Reso 01 pp.85-86, Reso 02
pp.109-110), but they start in a drawn cell and were already caught as clipped.
**Fix:** a run that starts in an undrawn cell is cut at the table's edge; the rest is hidden and
kept in `hidden_text`. `prequal_printed` = "01/", `prequal_pending` = 0. Named exceptions for T11.
383 hidden letters in 11 runs now (was 45 in 7). PR.
**Status:** fixed; flagged in data (4 critical + 8 warn review rows)

---

**Problem:** The image grid lost the `*` column on one page, so 2 rows disagreed.
**Where:** Reso 07 p.30
**Found by:** grid compare (H8)
**Tried:** looking right of the grid's last rule on every page: also found the `*` column's rule
on 24 FY2026 pages, where the column is empty. Rows did not change, but FY2026's pages file did.
**Fix:** look there only where a data row has a letter on the page right of the grid (pixels
decide where the rule is; text only says whether to look). 3,555 / 3,555 rows agree; FY2026
byte-identical. PR.
**Status:** fixed

---

**Problem:** Two rows print no EIN.
**Where:** Reso 07 p.18 (SU-CASA, Afro-Latin Jazz Alliance – East Side House Melrose, $15,000);
Reso 08 p.13 (the same row taken back)
**Found by:** anchor census (T5)
**Tried:** —
**Fix:** none; EIN blank, as printed. Reso 08 takes the row back and gives it again with EIN
45-3665976, so the Council fixed it itself.
**Status:** flagged in data (2 critical review rows)

---

**Problem:** A `***` marker with no `***` footnote on the page.
**Where:** Reso 06 p.6, Speaker's Initiative, Brooklyn Kindergarten Society \*\*\*, $50,000
**Found by:** T11 (markers)
**Tried:** —
**Fix:** none; kept as printed. 44 of the chart's 49 rows carry `**`; likely a typo. Named
exception in the config.
**Status:** flagged in data (1 critical review row)

---

**Problem:** Reso 04 has no resolution number.
**Where:** Reso 04 (2024-10-23), p.1
**Found by:** dates and numbers (T13), and the 2026-07-07 Legistar pass
(`data/combined/legistar_crosswalk.csv`: `not_located`)
**Tried:** the repo's Legistar notes and crosswalk; the PDF prints none. Legistar not queried
(out of scope for this run).
**Fix:** `resolution_number` blank on its 27 rows; `resolution_date` from its own p.1. In the
review file as `K.no_resolution_number`.
**Status:** open (needs a Legistar lookup)

---

**Problem:** The same two rows printed under three fiscal years.
**Where:** Reso 02, "Art a Catalyst for Change" charts #17 (Fiscal 2025, p.47), #43 (2024, p.74),
#44 (2023, p.75): Black Spectrum Theatre ($18,000) to $18,000, two schools
**Found by:** reading the unlabelled pages (above)
**Tried:** —
**Fix:** none; kept as printed (6 rows). In the review file as `K.repeated_chart`.
**Status:** flagged in data; open

---

**Problem:** No old CSV to compare with.
**Where:** `data/fy25/` (no `transparency-resolutions/` folder)
**Found by:** comparison with the retired file
**Tried:** —
**Fix:** none needed; the checks report it. The new tables are the first FY2025 transparency data
in the repo (3,555 rows; the 2026-10-19 prototype found 3,555 too).
**Status:** n/a
