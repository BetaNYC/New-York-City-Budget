# Draft #111 issue-log comments: FY2018 transparency resolutions (NOT posted)

**Written:** 2026-10-22 02:15 EDT. One block per problem, in the order found, in the shape #111
asks for. Each is meant to be its own comment on #111 once Noel approves. "PR" means the PR that
adds this folder; "promotion PR" the one that writes `data/fy18/pdf/transparency/`.

---

**Problem:** Starting point. The committed FY2018 CSVs come from the old text-order parser.
**Where:** 12 PDFs, 598 pages
**Found by:** review (starting point)
**Tried:** the FY2019 reader with a new config (`config/transparency/fy2018.toml`).
**Fix:** first run stopped: 16 rows had no readable amount. After the first fixes, 6 hard checks
failed (T3, T4, T6, T11, T15, and the ink self-test) and the ink check found 85 regions; the
image grid agreed on every row from the start. Each cause is below.
**Status:** fixed

---

**Problem:** Is Reso 01 FY2018 or FY2017?
**Where:** Reso 01 (Res 1563-2017), dated June 21, 2017
**Found by:** review (the brief asked to check)
**Tried:** read p.1: it changes the Fiscal 2018 Expense Budget (adopted June 6, 2017; charts 1–29,
38) and the Fiscal 2017 and 2016 budgets (charts 30–37, 39). The 2026-07-07 Legistar notes file it
as FY2018 Transparency Reso 01.
**Fix:** kept in FY2018; each row's `budget_fiscal_year` is its chart's. A review item
(`K.adopted_before_fy`). PR.
**Status:** flagged in data (1 review row)

---

**Problem:** Header rows with no labels.
**Where:** Reso 01 pp.55–56, Reso 03 p.48, Reso 04 p.32 (a grey band, nothing printed)
**Found by:** the run (rows with no amount), then T4
**Tried:** —
**Fix:** named exception `T4.blank_header`: the page is read with the labels of the chart page
before it, only when every column edge matches; the image grid borrows the same labels. PR.
**Status:** fixed; flagged in data (4 review rows)

---

**Problem:** Amounts printed without "$".
**Where:** Reso 05 p.61, "(100,000.00)" and "100,000.00" (4 rows)
**Found by:** the run (rows with no amount)
**Tried:** making "$" optional everywhere broke an existing rule ("5,000" alone is not an amount).
**Fix:** an amount without "$" counts only with cents; flagged `W.amount_format`. PR.
**Status:** fixed; flagged in data (4 review rows)

---

**Problem:** New columns: the fiscal conduit and its EIN.
**Where:** 95 chart pages ("Fiscal Conduit/Sponsoring Organization", "Fiscal Conduit EIN"; Reso
11 pp.7–8 "Fiscal Conduit"); "Delegation" for the member (Reso 06 p.42)
**Found by:** T4 (unrecognised headers), T5 (conduit EINs are EIN-shaped words)
**Tried:** —
**Fix:** new labels and four row columns at the end of FY2018's row table only (no other year's
table changes); the census counts conduit EINs; the image grid compares the conduit fields. 63
rows fill them; 4 conduit EINs print "#########" or 8 digits (review). PR.
**Status:** fixed; flagged in data (4 review rows)

---

**Problem:** Boxes round resolution text taken for tables.
**Where:** Reso 03 p.14, 04 p.14, 05 p.14, 06 p.13, 07 p.10, 08 p.11, 09 p.9, 11 p.6
**Found by:** T3 (no chart caption above the table), H9 (84 of the 85 ink regions)
**Tried:** —
**Fix:** named exception `T3.text_box`: the page's table is dropped before the checks. PR.
**Status:** fixed

---

**Problem:** "(Continued)" with a capital C, and a footnote marker after a caption.
**Where:** 11 pages (Reso 03, 04, 06); Reso 04 p.58 "- Fiscal 2018 ***"
**Found by:** T3 (charts starting twice), T12 (no fiscal year)
**Tried:** —
**Fix:** both rewritten before the caption is read, each a `W.caption_format` item. PR.
**Status:** fixed; flagged in data (12 review rows)

---

**Problem:** Footnotes that explain one chart, over several lines.
**Where:** Reso 03 pp.24–25, 30; Reso 04 p.58 (it prints "$5,154,200"); and a one-line MN-1
wording on Reso 05
**Found by:** T6 (unexpected lines under the table), T15 (money outside a table), T11
**Tried:** —
**Fix:** the wordings are `***` footnotes; every line under a long one, down to "Page n", is its
text, kept as a `T6.footnote` review item with the chart. PR.
**Status:** fixed; flagged in data (4 review rows)

---

**Problem:** An EIN read as hidden text.
**Where:** Reso 04 p.52 row 2: "…Velocity Track Club New York" runs into the EIN cell and the
EIN "46-3197831" follows in the same run
**Found by:** H9 ink coverage (the visible EIN was covered by no cell's letters), T5
**Tried:** a general rule (after text crosses into another cell, a gap starts that cell's own
text) fixed it but broke Reso 03 p.72, where hidden text "Inc.(COMET)" has such a gap and no space
glyph (its EIN read "(C1O13M1E9T0)583"). Reverted.
**Fix:** the rule only on pages the config names (`T7.clip_restart`); T7 fails if a named page has
no hidden run. PR.
**Status:** fixed; flagged in data (the row's `W.clipped_text` item)

---

**Problem:** The ink self-test could not fire.
**Where:** Reso 01 p.13 row 1
**Found by:** H9 acceptance ("one char withheld -> 0")
**Tried:** looked at the letter withheld: first an "i"-width letter, then the "*" (3.17 pt); both
ink fewer pixels than the smallest region.
**Fix:** `ink_acceptance_min_char_pt = 4.0` in the config (default 0 elsewhere). PR.
**Status:** fixed

---

**Problem:** Overfull cells (as FY2019).
**Where:** Reso 04 p.56; Reso 11 pp.17, 19 (Reso 11 p.19 read "aFnudn daifntegr t-os cshuopopl.ort")
**Found by:** the FY2019 overfull scan; T7
**Tried:** —
**Fix:** named `T7.overfull` pages; 4 rows change, each compared with the page. PR.
**Status:** fixed; flagged in data (4 review rows)

---

**Problem:** Other cases earlier years already handle.
**Where:** 9 "Beating Hearts Initiative" charts (136 rows, each with a note: $350,000 to Staten
Island Heart Society for defibrillators); 3 captions repeated without "(continued)"; 6 `**` rows
on Reso 05 p.23, which prints no footnotes
**Found by:** T4, T3, T11
**Tried:** —
**Fix:** named exceptions. PR.
**Status:** flagged in data (9 + 3 + 6 review rows; the 6 critical, suggested `source_error`)

---

**Problem:** Things the PDF itself gets wrong.
**Where:** Reso 05 p.60, Police Athletic League: two +$20,000 purpose rows, no negative (purpose
rows +$40,000); Reso 04 p.56, one organization under two EINs (13-3846431 / 13-3846432); Reso 10
p.20 "All Allocations", EIN "Various", ±$7,805,000
**Found by:** W.unpaired_purpose, T5
**Tried:** —
**Fix:** none (kept as printed). Listed in `REVIEW.md`.
**Status:** open (decisions for Noel)

---

**Problem:** The old CSV has 2 rows this parse does not.
**Where:** Reso 04 p.56, Vietnam Veterans of America ±$5,000
**Found by:** the retired-CSV compare
**Tried:** read the page: it shows EIN 11-2629339. The text layer has the hidden "Chapter #32" and
then the EIN; the old parse glued them and read 21-2629339.
**Fix:** none needed; the new rows carry 11-2629339. PR (README).
**Status:** fixed (old CSV wrong)

---

**Problem:** Is anything else different? Re-run of every finished year.
**Where:** FY2019–FY2026 review folders
**Found by:** byte comparison after the reader, check and config changes
**Tried:** —
**Fix:** every tracked file in FY2019–FY2025 is byte-identical; FY2026 differs only by the two
committed review decisions it picks up (known, not committed). Re-running FY2018 is
byte-identical. PR.
**Status:** fixed
