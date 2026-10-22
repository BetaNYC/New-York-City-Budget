# Draft #110 issue-log comments (NOT posted)

**Written:** 2026-10-22 01:30 EDT. One block per problem, in the order found, in the shape #110 asks
for. Each is meant to be its own comment on #110 once Noel approves. "PR" below means the PR that adds
this folder. Capital supporting detail only: FY2019 has no Terms & Conditions in `source/`.

---

**Problem:** The book is an Excel print, not the Word table every other year's parser reads.
**Where:** all 55 pages: `PROJECT, POLBORO, NEWPROJECT, CD, TITLE, DESC, FY19–FY22`, every cell ruled; no
agency headings, `TOTALS FOR` lines, Part II, Part III or summary page
**Found by:** triage (producer, page furniture, drawn rects on every page)
**Tried:** the Word-book reader needs a `SUB ID … SPONSOR` header and title blocks spaced by line gaps;
neither exists here
**Fix:** a second reader in `code/review_capital_sd.py`, on only when the config says `layout = "grid"`: a
row is the band between two drawn horizontal rules, a field the column between two drawn vertical rules,
named by its header word. The stream order is the second read (36,308 words agree, 0 disagree). C7 also
compares the column borders with the pixels (599 / 599). FY2020–FY2027 output unchanged. PR.
**Status:** fixed

---

**Problem:** The total row is under the grid, has no label and no count, and splits its first number.
**Where:** p.54, 1.8 pt below the last rule: `6` `14,910,000` `1` `5,900,000` `-` `-`
**Found by:** C1 (0 totals read on the first run; the words came back as not emitted)
**Tried:** looking for it inside a ruled band; it is outside every band
**Fix:** a bold line just under the grid whose words all sit in FY columns is the total; touching pieces
in one cell join with no space (`614,910,000`, `15,900,000`); `-` is 0. C1 checks its amounts alone and
writes the count as `-`. 1 / 1 ties. PR.
**Status:** fixed

---

**Problem:** A two-digit ID.
**Where:** p.36, `HL NC57`
**Found by:** C6 (one ruled row with no ID) and C9 (one t474 amount not in the PDF)
**Fix:** config `extra_sub_ids = ["NC57"]`. Then C9: 1,628 / 1,628 both ways. PR.
**Status:** fixed

---

**Problem:** The sponsor is printed as council-district codes.
**Where:** the CD column, every row (`00, 37`); the Key to CD, p.54 (from y = 167) and p.55
**Found by:** triage
**Tried:** reading the key cell by cell: a group's name runs over the LASTNAME / FIRSTNAME border where the
two cells are merged (`Brooklyn Delegation`), and on p.55 `Caucus Black, Latino and Asian` runs into its
district with no gap, so it prints as `Asian97`
**Fix:** each key word goes to the cell its left edge is in; the district is the digits inside the last
column. `sponsor` = the key applied to the codes (members by LASTNAME, groups by LASTNAME + FIRSTNAME as
printed); `sponsor_raw` and `council_district` keep the codes. C9: codes equal t474's on 1,624 / 1,625,
names on 1,617 / 1,625 (7 are group wording). PR.
**Status:** fixed (how to name groups: REVIEW D1)

---

**Problem:** Three lower-case boroughs.
**Where:** `E CN161` p.6, `E CN227` p.8, `E CN403` p.12: `k` (all CD 41)
**Found by:** C6 (critical), C9
**Fix:** none; kept as printed (t474 has `K`).
**Status:** flagged in data (REVIEW A1)

---

**Problem:** One row's district differs from Open Data.
**Where:** p.40, `HW CN030` DOT REPAVING IN DISTRICT 31, borough Q, $500,000: the PDF prints CD `49, 00`
(Rose, Speaker); t474 has 3100 (Richards, Speaker)
**Found by:** C9 (CD codes and sponsor)
**Fix:** none; kept as printed. The title and borough point to district 31.
**Status:** open: needs_info from Council Finance (REVIEW B1)

---

**Problem:** OMB's adopted budget is $15,460,000 higher on 11 Council-series lines.
**Where:** OMB `46m8-77gv`, release 2018-07-13, against the PDF by budget line
**Found by:** ad hoc comparison (report only)
**Fix:** none; t474 has no amount the PDF lacks, so this is between OMB and the Council's book. The same
numbers are already in `data/capital/RECONCILIATION.md` §3.
**Status:** open: report only (REVIEW B2)
