# Draft #105 issue-log comments: FY2024 transparency resolutions (NOT posted)

**Written:** 2026-10-21 19:18 EDT. One block per problem, in the order found, in the shape #105
asks for. Each is meant to be its own comment on #105 once Noel approves. "PR" means the PR that
adds this folder; "promotion PR" the one that writes `data/fy24/pdf/transparency/`. The reader
already handled FY2025 (#104), so this year needed little new code.

---

**Problem:** Starting point. The committed FY2024 CSVs come from the old text-order parser.
**Where:** 9 PDFs, 388 pages; Reso 01 pp.3-61 carry /Rotate 90
**Found by:** review (starting point)
**Tried:** the FY2025 reader with a new config. The rotated pages read with no change: pdfplumber
and pdfium both give display coordinates, and the image grid agrees on every Reso 01 row.
**Fix:** `config/transparency/fy2024.toml`. Promotion unrotates `bbox_pt` for the row contract.
**Status:** fixed

---

**Problem:** Reso 01's "Page n" labels were not recognised (59 "unexpected text" lines).
**Where:** Reso 01 pp.3-61
**Found by:** T6 (furniture) and T3 (page labels)
**Tried:** —
**Fix:** they print a no-break space ("Page\xa01"); the label reader takes any space. PR.
**Status:** fixed

---

**Problem:** A clipped borough name swallowed the organization next to it.
**Where:** Reso 02 p.11, rows 1-2 ("Staten Island Delegation" / South Shore District Management
Association, Eden II School)
**Found by:** reading the hidden-text list (organization empty, hidden text = "nSouth Shore …")
**Tried:** (1) requiring |gap| ≤ 0.5 pt at a cell-edge crossing: no change, because the clipped "n"
already sits mostly in the next cell. (2) Measured: the "n" ends at 128.53 pt and "South" starts at
127.58 pt, a 0.95 pt overlap; real clipped text continues within ±0.07 pt.
**Fix:** a run also breaks where a letter starts more than 0.5 pt before the last one ends.
Borough "Staten Island Delegatio", hidden "n", organization read. FY2025 and FY2026 unchanged. PR.
**Status:** fixed; flagged in data (2 review rows)

---

**Problem:** Ink check: 2 spots on Reso 02 p.11.
**Where:** Reso 02 p.11, the Borough cell's right edge on rows 1-2
**Found by:** ink coverage (H9)
**Tried:** looked at the crop
**Fix:** none needed: the left edge of the hidden "n" really shows before the border. The check
did its job. In the review file (`H9.ink`).
**Status:** flagged in data

---

**Problem:** 11 chart pages print no "Page n" label.
**Where:** Reso 02 pp.66-73 (charts #46-#53), Reso 03 pp.55-57 (charts #53-#55)
**Found by:** T3 (page labels)
**Tried:** —
**Fix:** none; the labels after them count them (Reso 02 p.74 is "Page 72"). All are prior-year
charts (Fiscal 2022-2023), as in FY2025. Named exceptions in the config.
**Status:** flagged in data (11 review rows)

---

**Problem:** Odd marks the PDF prints.
**Where:** Reso 02 p.18 row 14 ("#" in the `*` column); Reso 01 p.55 rows 1-2 (`***`, no `***`
footnote on the page)
**Found by:** T11 (markers)
**Tried:** checked each on the rendered page
**Fix:** none; kept as printed. Named exceptions.
**Status:** flagged in data (3 critical review rows)

---

**Problem:** An EIN printed as "TF4876222".
**Where:** Reso 07 p.17 row 1, Knickerbocker Avenue Merchants Partnership, ($10,000)
**Found by:** anchor census (T5)
**Tried:** —
**Fix:** none; `ein` blank, printed value kept. Schedule C printed the same placeholder; Reso 07
takes it back and re-gives $10,000 with EIN 84-3309358 (which the disclosure has).
**Status:** flagged in data (1 critical review row)

---

**Problem:** The retired CSV missed 9 rows.
**Where:** `data/fy24/transparency-resolutions/fy24_transparency_all.csv`
**Found by:** comparison with the retired file (multiset of resolution, EIN, amount)
**Tried:** —
**Fix:** all 3,294 of its rows are here. The 9 it lacks: 7 EINs printed without a hyphen, "Bronx
Community Board #7" (Reso 06 p.27), and the "TF4876222" row. List:
`data/fy24_tr_retired_csv_compare.csv`. The retired files are left as they are.
**Status:** fixed (in the new tables)
