# Draft #108 issue-log comments (NOT posted)

**Written:** 2026-10-21 23:50 EDT. One block per problem, in the order found, in the shape #108 asks
for. Each is meant to be its own comment on #108 once Noel approves. "PR" below means the PR that adds
this folder. Terms & Conditions only: FY2021 has no capital supporting detail in `source/`.

---

**Problem:** No FY2021 capital supporting detail to review.
**Where:** `source/FY21/` holds the Resolution A book (`FY21-Sec254-Capital-ResoA-M231-Res1362-Res1363.pdf`,
73 pp.), not the supporting detail
**Found by:** triage, before the first run (the issue's "Known going in")
**Tried:** nothing fetched; a copy on the City's publications portal is being added separately
**Fix:** none here. This review covers the T&C only; `data/pdf_years.csv` gets no FY2021 `capital_sd` row.
**Status:** open (out of scope for this PR)

---

**Problem:** T1 counted 0 "As a condition" paragraphs for 46 headings.
**Where:** every condition page, pp.2–16
**Found by:** T1 (critical)
**Tried:** looking at the page: the conditions are all there; FY2021 sets its body text at x0 = 90 pt,
and T1 looked for the opening only left of 80 pt (FY2022–FY2024 are at 72 pt)
**Fix:** config `body_x0_max` (FY2021: 95; default 80, so other years are unchanged). T1: 46 = 46. PR.
**Status:** fixed

---

**Problem:** The body does not name the heading's budget lines in the form T3 reads.
**Where:** #12 p.5 ("budget lines E2364 and E2365", no hyphen); #28 p.11 (`HD-` / `0009` across a
line end)
**Found by:** T3 (warn)
**Fix:** none; the check's limits, as FY2022 #14 and #33. The texts are right.
**Status:** flagged in data (REVIEW C1)

---

**Problem:** The retired T&C CSV keeps only the first agency of two-agency conditions.
**Where:** #1 (ACS / DOC, p.2), #12 (DOE / SCA, p.5), #28 (HPD / Capital Budget, p.11), #37 (DYCD /
DCAS, p.13)
**Found by:** reading the T7 comparison by hand (T7 compares the first agency only)
**Fix:** none needed in the new file, which keeps each agency with its own code and units. The old file
also lists DOC's units under ACS's code (#1), puts budget lines into `units` (#2, #3, #12, #28), folds the
FSR table into #19 and drops a printed hyphen in #23.
**Status:** flagged in data (REVIEW B3–B5)

---

**Problem:** Two agencies share one printed code.
**Where:** p.5, #12: "School Construction Authority (040)" after "Department of Education (040)"
**Found by:** reading the multi-agency conditions
**Fix:** none; kept as printed.
**Status:** flagged in data (REVIEW B2)
