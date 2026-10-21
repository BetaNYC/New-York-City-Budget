# Draft #103 issue-log comments: FY2026 transparency resolutions (NOT posted)

**Written:** 2026-10-21 01:00 EDT. One block per problem, in the order found, in the shape #103
asks for. Each is meant to be its own comment on #103 once Noel approves. "PR" means the PR that
adds this folder; "promotion PR" the one that writes `data/fy26/pdf/transparency/`.

---

**Problem:** No checked reader for transparency resolutions; the committed CSVs come from the old
text-order parser and are not trusted.
**Where:** all 10 PDFs, 544 pages
**Found by:** review (starting point)
**Tried:** running the Schedule C reader (`code/schedc/`) as is. Its table finding works (one table
per chart page, 4,952 rows, the prototype's count), but its cell text pastes hidden letters into
the next cell (below).
**Fix:** `code/transreso/` on top of the Schedule C toolkit, `code/parse_transparency_v2.py`,
`config/transparency/fy2026.toml`, `code/test_transreso.py`. Re-run is byte-identical. PR.
**Status:** fixed

---

**Problem:** Excel clips text that overflows a cell, but the hidden letters stay in the PDF. Read
letter by letter, they land in the next cell.
**Where:** 12 cells: Reso 01 pp.85-86, Reso 02 pp.109-110, Reso 08 p.19 (e.g. the EIN cell read as
`of2 G3-r7e1e6n4p7o7in6t`, the amount as `nt $5,000`)
**Found by:** structure (EIN and amount cells that did not parse)
**Tried:** (1) runs of letters with gaps up to 3 pt, owned by the cell they start in: also caught
an amount touching the purpose text next to it (Reso 01 p.85, Reso 04 pp.34, 52-54), 9 false hits.
(2) Measured the gap where a run crosses a border: clipped text −0.07 to +0.07 pt; a new cell's
text 0.98 pt or more. Also break a run where the colour changes (red amount, black text).
**Fix:** a run crosses a border only with no gap (≤ 0.5 pt). 12 runs, 157 hidden letters, each in
the review file with `hidden_text`; the value keeps what shows ("Speaker's Initiat"). Ink coverage
confirms none of them is visible. PR.
**Status:** fixed; flagged in data (12 review rows)

---

**Problem:** Purpose-of-funds charts draw no border between Source and Member in most rows, so one
cell covers two columns.
**Where:** 448 rows, all purpose-of-funds charts (e.g. Reso 01 p.91)
**Found by:** structure (cells under two header columns)
**Tried:** —
**Fix:** split by the header's columns, each run of text going to the column it starts in. PR.
**Status:** fixed; routine flag `W.spanning_cell`

---

**Problem:** Some rows have no drawn cell under a header column.
**Where:** 90 rows with no `*` cell (all empty); 1 purpose cell, Reso 03 p.81 row 8, $18,000
**Found by:** character conservation (144 letters in a table but in no cell)
**Tried:** —
**Fix:** the cell is the header column's width across the row. 0 letters left outside a cell. PR.
**Status:** fixed; the purpose cell is in the review file

---

**Problem:** The image grid (`grid.py`) keeps only column rules drawn down most of the table, so it
missed Source | Member where only a few rows draw it, and kept it where some rows leave it out.
**Where:** 64 pages; 13 rows disagreed at first (Reso 01 pp.85-86, 88; Reso 02 pp.109-110, 125)
**Found by:** grid compare (H8)
**Tried:** using the lattice as is (13 rows differ, all where a border is drawn in some rows only).
**Fix:** two pixel-only additions on the image side: a rule drawn in the header row alone is found
in the header's pixels; a column rule counts in a row only where that row's pixels show it. Now
4,952 / 4,952 rows agree on every field. PR.
**Status:** fixed

---

**Problem:** The FY2026 charts print no totals, so there is nothing to tie.
**Where:** all 532 chart pages
**Found by:** totals (T15: money printed outside the tables)
**Tried:** looking for a total line, a chart sum or a summary page: 0 found.
**Fix:** check what *is* printed instead: "Charts 1 through N" (8 / 8 resolutions that print it), the
"Page n" labels (1..n with no gap, 10 / 10), parentheses vs red ink (1,617 / 1,617), and ink
coverage for anything dropped. Per-resolution sums are reported, not checked. PR.
**Status:** fixed (no totals exist)

---

**Problem:** Reso 06 chart #2 is captioned "Aging Discretionary - Fiscal 2023".
**Where:** Reso 06 (Res 0255-2026) p.5, 4 rows
**Found by:** fiscal-year check (T12: the resolution's text names 2024-2026 only)
**Tried:** —
**Fix:** none; kept as printed. It sits between two Fiscal 2026 charts and names Council Member
Zhuang, who took office in January 2024, so it looks like a typo for 2026. Named exception in the
config; in the review file.
**Status:** flagged in data; decision for Noel

---

**Problem:** Chart #49 "Operation Backpack" prints no fiscal year.
**Where:** Reso 01 p.67
**Found by:** structure (caption without "- Fiscal YYYY")
**Tried:** —
**Fix:** none; `budget_fiscal_year` blank. The report text (pp.1-2) lists it with the Fiscal 2026
initiatives.
**Status:** flagged in data; decision for Noel

---

**Problem:** One row prints no EIN.
**Where:** Reso 06 p.2, Department of Health and Mental Hygiene **, ($5,000)
**Found by:** anchor census (T5)
**Tried:** —
**Fix:** none; EIN blank, as printed.
**Status:** flagged in data

---

**Problem:** Reso 03-10 print no date and no resolution number ("Preconsidered Res. No." blank).
**Where:** p.1 of Reso 03-10
**Found by:** dates (T13)
**Tried:** —
**Fix:** number and date from the 2026-07-07 Legistar pass
(`research/2026-07-07-legistar-links-fy21-27.md`), in the config with its source;
`resolution_date_source` on every row says where the date came from. Reso 01-02 print their date
and it matches. All 10 filename dates match. PR.
**Status:** fixed

---

**Problem:** The retired CSV missed 197 rows.
**Where:** `data/fy26/transparency-resolutions/fy26_transparency_all.csv`
**Found by:** comparison with the retired file (multiset of resolution, EIN, amount)
**Tried:** —
**Fix:** all 4,755 of its rows are here. The 197 it lacks: 173 EINs printed without a hyphen (its
regex needs one), 21 rows on the prior-year purpose-of-funds chart of 7 resolutions, the 2 clipped
Pilsudski rows, 1 row with no EIN. List: `data/fy26_tr_retired_csv_compare.csv`. Promotion PR adds
the checked rows; the retired files are left as they are.
**Status:** fixed (in the new tables)
