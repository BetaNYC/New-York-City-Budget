---
title: Adversarial audit of commit ba90fce — raw findings
created: 2026-08-13
type: audit
status: open
tags: [nyc-budget, data-quality, audit, schedule-c]
---

# Adversarial audit of `ba90fce` — raw findings

Produced 2026-08-13 by a 12-dimension workflow, each finding attacked by 3 independent
refuters. **124 findings raised, 71 survived refutation, 16 blockers. 154 claims independently
recomputed as correct.** The final synthesis agent never ran (spend limit), so this is the raw
record rather than a ranked verdict.

## ⚠️ Verification status — this file lists ALL 124 raised, verified or not

The run hit the monthly subagent spend cap. **All 12 audit dimensions completed**, but 69 of ~372
refuters died, and the completeness critic and publication verdict never ran at all.

**Findings below are NOT marked with their verdict.** 305 refuter verdicts did land, and 79 of them
returned `not-a-defect` — so a meaningful share of what is written here was refuted and is reported
anyway. Treat every entry as a lead, not a conclusion.

The failures were concentrated in three dimensions, whose findings are the least trustworthy in
both directions:

| dimension | what it audited | refuter losses |
|---|---|---|
| `script1-logic` | `verify_amounts_against_pdf.py` internals | heavy |
| `refute-440` | the adversarial attack on "440 of 440 confirmed" | heavy |
| `numbers-dictionary-readme` | figures in DATA-DICTIONARY / README / PARSING | 4 |

**The error runs both ways, and not symmetrically.** The workflow scored a finding as surviving only
if at least one refuter returned; a finding whose three refuters *all* died was dropped. So the
71-survivor set **under**-reports — real defects from those three dimensions were silently
discarded — while this raw file **over**-reports, since it includes findings that were refuted or
never tested.

Independently re-verified by hand since (these hold): the absent `GRAND TOTAL`, the
`comparison-2027.md` contradiction, the disclosure stream arithmetic, and the `pdf_line`
`splitlines()` drift (18,023 newlines vs 18,315 `splitlines()` — exactly the 292 form feeds).

Re-run plan: `README.md` in this folder, and the handoff journal in the workspace.

Retraction posted to issue #57: https://github.com/BetaNYC/New-York-City-Budget/issues/57#issuecomment-5282646717

Severity: {'major': 49, 'minor': 36, 'nit': 23, 'blocker': 16}


## BLOCKER

### `DATA-DICTIONARY.md:72 — "The award rows plus appendices come to $3,741,615,569 against the Council's own printed grand totals of $5,476,070,836 — **68.3%**."`

**Problem.** NOT APPLES TO APPLES. The numerator includes the appendix streams ($352,997,275); the denominator excludes them entirely. The printed category totals cover the award body ONLY — Aging / Local / Youth Discretionary are not among the 96 distinct categories in any of the 13 `*_schedule_c_initiatives.csv` files, and the reconciliation file prints appendix A/B/C totals as separate lines BELOW the GRAND TOTAL row. The 68.3% figure therefore divides a body+streams numerator by a body-only denominator. Both consistent pairings give ~61%, not 68.3%, and the shortfall is $2.09B–$2.38B, not $1.73B. The error runs in the flattering direction: it makes capture look 6.5 points better and the under-capture $353M–$648M smaller than it is.

**Evidence.**

```
PROOF THE DENOMINATOR EXCLUDES THE STREAMS (FY2027, the exact-reconciling year):
$ .venv/bin/python -c "...parse_expense_disclosure.parse_year(FY2027)..."
  disclosure FY2027 total       $705,564,000   10040 rows
  streams Aging/Local/Youth     $49,799,000   3860 rows
  disclosure BODY (excl streams)$655,765,000
  parser printed GRAND TOTAL    $655,764,999
  DELTA                         $1
  repo appendix CSV total FY27  $49,799,000  (3860 rows)  == disclosure streams: True
The same relation holds in all 13 years: disclosure-minus-streams tracks the printed total in every year (deltas +$1 to +$39M, all post-adoption residue); if the streams were inside the printed total, disclosure-minus-streams would fall ~$49.8M SHORT of it every year. It never does.

$ grep -ilE "aging discretionary|local initiative|youth discretionary" data/fy*/schedule_c/*_schedule_c_initiatives.csv  ->  exit 1, no hits (96 distinct categories enumerated, none is a stream)

CORRECTED RATIOS (recomputed):
  published (body+apx / body-only):  68.33%   shortfall $1,734,455,267
  body / body:                       61.88%   shortfall $2,087,452,542
  (body+apx) / (body + true streams, $647,537,100 from the workbooks): 61.10%   shortfall $2,381,992,367
```

**Suggested fix.** Delete the 68.3% / $1.73B sentence. If a capture figure must be published, use the disclosure workbooks — the one denominator that covers the same universe as the numerator: $3,741,615,569 / $6,271,829,149 = 59.7% of dollars, and 62,213 / 127,588 = 48.8% of rows, FY2015–FY2027. Publish both, per DATA-ANOMALIES.md §20's own rule.

### `DATA-DICTIONARY.md:72 — "The corpus under-captures award detail; it does not inflate it."`

**Problem.** The shortfall is PARTLY BY CONSTRUCTION, so calling it "under-capture" is misleading. The printed category totals include money that is never designated to a named grantee at adoption: the Schedule C itself states "The Council will designate $X post-adoption" and prints the amount only in the initiative header, never as a provider row. Some of it goes to agencies (Department for the Aging, DCLA, Department of Consumer and Worker Protection), some is per-district money with districts unassigned. This is not extraction loss — no parser could ever capture it, because there is no grantee row to capture. The repo already established this one day earlier and the new claim does not carry it.

**Evidence.**

```
DIRECT PDF MEASUREMENT (regex over `build/pdftext/fy{YYYY}.pages.txt` body pages, sections taken from each reconciliation file):
FY    post-adopt mentions   $ stated post-adoption
2015     1        129,400 | 2016     1        500,000 | 2017     7        257,000
2018    42     20,003,189 | 2019    61     30,118,075 | 2020    55     22,656,658
2021    42     12,502,589 | 2022    64     46,297,614 | 2023    53     17,180,750
2024    49     21,264,253 | 2025    47     20,866,615 | 2026    58     66,771,395
2027    44     50,518,586
  13-year total: $309,066,124  = 5.64% of the $5,476,070,836 denominator, >=17.8% of the claimed $1.73B shortfall.
That is a FLOOR: the regex counts only the explicit "will designate $N post-adoption" phrasing (44 of FY2027's 166 `Designation Method:` blocks), and misses 100%-post-adoption initiatives stated without a dollar figure.

FY2027 is decisive: stated post-adoption $50,518,586 vs the year's ENTIRE printed-total shortfall of $50,653,587 = 99.7%. FY2027 has essentially zero body capture loss (FINDINGS.md: 99.4% row capture, 100% (EIN,amount) match, 2,227/2,232 EINs agree to the dollar).

The repo's own prior work says the same: research/phase1-source-comparability/comparison-2027.md:23 "The 62-row / $50.65M gap ... is fully explained: those are **post-adoption designations**"; :49 "The gap decomposes with nothing left over"; :214 "`Department of Consumer and Worker Protection` never appears in Schedule C at all, since it has no provider rows." FINDINGS.md §3b: FY2027's "7.7% is roughly the **floor** — the share of initiative money that legitimately never becomes a named provider row."
```

**Suggested fix.** If any shortfall figure is published, decompose it and name the by-construction share: "at least $309M of the gap is money the Schedule C itself states will be designated after adoption, plus agency-administered allocations that never become a grantee row." Do not describe the residual as under-capture without that subtraction.

### `DATA-DICTIONARY.md:69 — "In FY2027 ... the awards fall $50,653,587 short and the appendices supply $49,799,000 of it, **98%**, leaving a 0.1% residual."`

**Problem.** This directly contradicts the repo's own FY2027 study, published one commit earlier, and it is the load-bearing discriminating evidence for the whole appendices-are-additive conclusion. Both cannot be true: comparison-2027.md attributes that same $50.65M gap entirely to post-adoption designations ('decomposes with nothing left over') AND separately matches all 3,860 appendix rows to the disclosure exactly with zero residue. The appendices cannot simultaneously be closing the shortfall and be matched money outside it. My own PDF measurement backs comparison-2027.md. The '98%' is a coincidence between two independent ~$50M quantities: the fixed ~$49.8M appendix pot and FY2027's post-adoption residue.

**Evidence.**

```
comparison-2027.md:44 "disclosure rows with NO Schedule C counterpart: 62  $50,653,586"; :46 "sum check: $50,653,586 + $2 = $50,653,588 == delta? True"; :49 "The gap decomposes with nothing left over: 62 post-adoption rows plus two $1 extraction errors."; :276/:290/:292 the three appendices match the disclosure exactly (2558 Local $36,539,000; 835 Youth $7,650,000; 467 Aging $5,610,000), i.e. they are already fully accounted for on the other side of that same reconciliation.

My independent PDF read: FY2027 body prints "will designate $N post-adoption" 44 times summing $50,518,586 = 99.7% of the $50,653,587 'shortfall'.

And the algebra that generates the coincidence: printed GT $655,764,999 == disclosure $705,564,000 minus streams $49,799,000, to $1. So (printed GT − awards) and (disclosure − awards − appendices) are the SAME quantity by construction — which is why FINDINGS.md §3b noticed them 'agree to a dollar'. That agreement is evidence the streams sit OUTSIDE the printed total, not evidence they fill it.
```

**Suggested fix.** Remove the FY2027 sentence. TEST 3 in code/audit_appendix_overlap.py cannot discriminate at all: awards run 30–70% below the printed totals in every year, so 'awards + appendices never overshoots' is guaranteed by the size of the capture gap regardless of which reading is true. Reconcile with comparison-2027.md before republishing any FY2027 claim.

### `code/audit_appendix_overlap.py:126-137 (grand_total) and :254 output label "Council's own printed GRAND TOTALs"`

**Problem.** The PDFs contain no "GRAND TOTAL" line at all. The number the script calls "the printed GRAND TOTAL" / "the Council's own printed GRAND TOTALs" is the PARSER's sum of per-category summary-block subtotals, written by parse_schedule_c.py:365. Worse, it is systematically understated: `p=recon.get(c) or 0` means every ToC category for which the parser found no summary block contributes $0. That happens in 11 of 13 years (FY15: 4 categories, FY17/FY18: 2, FY16/19/20/21/22/24/25: 1). The entire ALSO-CLAIMED headline — "the published headline is 68.3% of the Council's own printed GRAND TOTALs ($5,476,070,836), i.e. the corpus UNDER-captures by $1.73B" — attributes a parser artifact to the Council and divides by a denominator known to be missing categories.

**Evidence.**

```
$ grep -ric "grand total" build/pdftext/fy20*.pages.txt  ->  0 for all 13 files (fy2015..fy2027); also `grep -c "GRAND TOTAL" build/pdftext/fy2027.pages.txt` -> 0.
Source of the number, code/parse_schedule_c.py:363-365:
    for c in cats:
        i=isum.get(c,0); p=recon.get(c) or 0; gi+=i; gp+=p
    L.append(f"{'GRAND TOTAL':52} {gi:>14,} {gp:>14,}  {ok}/{len(cats)} categories exact")
Zero-contributing categories per year (counted from the recon status column):
  fy15 4 ['FROM BUDGET RESPONSE TO ADOPTION:', 'INTRODUCTION', 'BOROUGHWIDE NEEDS', 'HEALTH SERVICES AND PREVENTION']
  fy17 2, fy18 2, fy16/19/20/21/22/24/25 1 each, fy23/26/27 0.
```

**Suggested fix.** Rename the column and the summary line to something true, e.g. "parser-summed category subtotals" with a footnote naming the years where categories contribute $0, or drop the 68.3% / $1.73B framing until a real printed control total is sourced. Do not describe a parser aggregate as "the Council's own printed" figure.

### `code/audit_appendix_overlap.py:219-233 (TEST 3)`

**Problem.** Test 3's stated premise is "If the appendices were already inside the award body, the awards alone would reach that total and adding the appendices would OVERSHOOT it." That premise is already false without any appendix dollars. At the level the totals are actually printed and reconciled — per category — awards ALONE exceed the printed category total in 6 of the 7 years that have appendix data. The aggregate no-overshoot result is produced by netting category overshoots against category under-captures. This is not a year-mapping artifact: FY2023 (26 ToC categories / 26 summary blocks, no MISMATCH) and FY2026 (25/25, no MISMATCH) both overshoot. FY2026 hides $20,057,085 of positive category overshoot inside a $177.8M aggregate shortfall.

**Evidence.**

```
Recomputed per category from the same two files the script reads (printed column of *_schedule_c_reconciliation.txt vs category-summed *_schedule_c_awards.csv):
  fy26 (25/25 blocks, no MISMATCH): 6 of 25 categories over — BOROUGHWIDE NEEDS awards 4,040,000 vs printed 2,000,000 (+2,040,000); COMMUNITY SAFETY AND VICTIM SERVICES 19,822,726 vs 5,100,000 (+14,722,726); DOMESTIC VIOLENCE 17,360,008 vs 15,960,000 (+1,400,008); ENVIRONMENTAL INITIATIVES 26,317,665 vs 25,625,000 (+692,665); HOUSING 18,862,686 vs 18,201,000 (+661,686); SPEAKER'S INITIATIVE 96,620,500 vs 96,080,500 (+540,000). Sum of positive overshoot $20,057,085.
  fy23 (26/26, no MISMATCH): 3 of 26 over, $3,188,040.
  fy21 9 of 26; fy22 7 of 26; fy24 6 of 26; fy25 6 of 26; fy27 0 of 25.
FY2026 Community Safety printed total confirmed directly in the PDF, build/pdftext/fy2026.pages.txt page 50: "Community Safety and Victim Services Initiative  $5,100,000 / TOTAL $5,100,000".
```

**Suggested fix.** Either run the overshoot test per category (which requires a category on appendix rows — the appendix CSVs have none, so it cannot currently be run), or drop Test 3's claim to what it actually supports: FY2027 only. Delete the sentence asserting that subset implies awards alone reach the total.

### `code/audit_appendix_overlap.py:219-244 (TEST 3 and TEST 4 tables) — "years where awards + appendices exceed the Council's own total: 0 of 13"`

**Problem.** The "0 of 13" counts 5 years that carry $0 of appendix dollars (FY2015/16/17/19/20) and one that carries $4.4M against ~$49.8M in every later year (FY2018). Those 6 years cannot overshoot no matter what the truth is — the parser extracted no appendix rows for them. So the real denominator is 7, and of those 7 only FY2027 has award coverage (92%) high enough for the test to discriminate; the other six sit on shortfalls of $71M–$243M against $49.8M of appendices. Test 4's table compounds this by silently `continue`-ing past the 5 empty years (line 240), so a reader sees an 8-row table under a narrative that says 13 years.

**Evidence.**

```
Script output, TEST 3 appendices column: 2015 $0, 2016 $0, 2017 $0, 2018 $4,419,275, 2019 $0, 2020 $0, then 2021-2027 ~$49.8M. Confirmed at source — data/fy19/.../fy19_schedule_c_reconciliation.txt tail: "appendix A (aging): 0 rows $0 / appendix B (local): 0 rows $0 / appendix C (youth): 0 rows $0". FY2020's appendix section is pages 189-405 (217 pages) and yielded 0 rows.
'covers' column: 2018 2%, 2021 49%, 2022 20%, 2023 22%, 2024 70%, 2025 41%, 2026 28%, 2027 98%.
```

**Suggested fix.** Label the years with no parsed appendix data as "n/a", report "0 of 7 testable years" (or "0 of 1 year with the coverage to detect it"), and state the parse gap explicitly rather than printing $0 as if it were a measurement.

### `code/audit_appendix_overlap.py:47 TOC_APPENDIX = re.compile(r"(?i)appendix\s+([abc])\s*:\s*(.+?)\s*[.…]+\s*page\s*(\d+)\s*[-–]\s*(\d+)")`

**Problem.** The published claim "(1) ToC gives appendices their own page numbering from FY2019" is a regex artifact, not a document fact. FY2016, FY2017 and FY2018 all give the appendices their own numbering restarting at 1, but print the range without the token "PAGE" — the regex requires it, so the script reports 0 appendices and 0 restarts for those years. FY2015 prints "…..PAGE 1" with a start page and no range, so the trailing `[-–]\s*(\d+)` fails there too. The Test 1 table is wrong for 4 of 13 rows, and the failure direction is exactly the one the test file's own docstring names as dangerous ("silently reports 0 appendices and reads as evidence for subset — a wrong answer that looks like a measurement") — and the test suite does not cover either form.

**Evidence.**

```
Actual ToC text from build/pdftext/*.pages.txt pages 1-6:
  FY2016: 'APPENDIX A: AGING DISCRETIONARY……….1-25', 'APPENDIX B: LOCAL INITIATIVES……….26-162', 'APPENDIX C: YOUTH INITIATIVES……….163-212'
  FY2017: 'APPENDIX A: AGING DISCRETIONARY……….1-33' ... FY2018: 'Appendix A: Aging Discretionary……….1-33' ...
  FY2015: 'APPENDIX B: AGING DISCRETIONARY…..PAGE 1', 'APPENDIX C: YOUTH DISCRETIONARY…..PAGE 24', 'APPENDIX D: LOCAL INITIATIVE…..PAGE 57'
Script output for those rows: 2015 0/0, 2016 0/0, 2017 0/0, 2018 0/0.
code/test_audit_appendix_overlap.py only exercises the FY2024 form ('….PAGE 1 - 26') and a plain-hyphen variant; `pytest code/test_audit_appendix_overlap.py` -> 7 passed.
```

**Suggested fix.** Make `page` optional and the end-page optional: r"(?i)appendix\s+([abcd])\s*:\s*(.+?)\s*[.…]{2,}\s*(?:page\s*)?(\d+)(?:\s*[-–]\s*(\d+))?". Add the FY2016 and FY2015 literal lines to the test. Then re-derive the "from FY2019" claim — on the corrected regex it is at least FY2016.

### `code/audit_appendix_overlap.py:46 STREAMS = ("Aging Discretionary", "Local Initiative", "Youth Discretionary"); used at :178`

**Problem.** Two defects. (i) The published claim "the stream names appear ZERO times in body pages across 13 years" is contradicted by the script's own output, which prints 1 for FY2026. (ii) The needle set is FY2024-era naming applied to all 13 years, and does not match the actual appendix names in 7 of them: FY2016-FY2020 Appendix C is "Youth Initiatives", not "Youth Discretionary"; FY2021-FY2022 Appendix B is "Local Discretionary", not "Local Initiatives". In those years the needle cannot match by construction, so the zero is guaranteed rather than measured — a test that cannot fail. This is the repo's own "a regex may NOMINATE; only the Council's own data may DECIDE" rule being violated: pattern-matching is being used to decide.

**Evidence.**

```
Script output TEST 2 column: FY2026 = 1. Located it: build/pdftext/fy2026.pages.txt page 52, prose inside a purpose field — "...support community development, event programming, and local initiatives that enhance quality..." (Banks, District 42, EIN 113199040, $10,000).
Per-year appendix names read from each ToC: FY2019 'APPENDIX C: YOUTH INITIATIVES', FY2020 'Appendix C: Youth Initiatives', FY2021 'Appendix B: Local Discretionary', FY2022 'Appendix B: Local Discretionary'.
Re-run with the correct per-year names substituted: total body hits = 2 (FY2016 'Youth Initiatives' x1, FY2026 'Local Initiatives' x1), both prose/org-name noise, not 0.
```

**Suggested fix.** Derive the needles per year from that year's own ToC (the TOC_APPENDIX match already captures the name in group(2)) instead of hardcoding one naming era, and report the actual count with the matched context so a prose hit is visibly distinguished from a line item. Correct the commit claim from ZERO to 2-with-context.

### `DATA-DICTIONARY.md:72 (and code/audit_appendix_overlap.py:23, :127, :220, :254)`

**Problem.** "the Council's own printed grand totals of $5,476,070,836" is false. The Schedule C PDFs print no grand total at all. The figure is this repo's own parser summing 25 per-category printed totals (code/parse_schedule_c.py:365 accumulates `gp` and emits the 'GRAND TOTAL' line into the reconciliation .txt). audit_appendix_overlap.grand_total() then reads that self-produced file while its docstring claims it is 'The GRAND TOTAL the document itself prints'. A derived internal aggregate is published as a Council-printed figure, and the whole of Test 3 is framed on that false premise.

**Evidence.**

```
$ grep -c -i "grand total" build/pdftext/fy2027.pages.txt -> 0 ; same for fy2024 and fy2021 -> 0, 0
$ grep -n "655,764,999" build/pdftext/fy2027.pages.txt -> (no output; the aggregate appears nowhere in the FY2027 PDF)
$ sed -n 365p code/parse_schedule_c.py -> L.append(f"{'GRAND TOTAL':52} {gi:>14,} {gp:>14,}  {ok}/{len(cats)} categories exact")  # gi/gp are running sums over cats
```

**Suggested fix.** Replace every occurrence of "the Council's own printed GRAND TOTAL(s)" with "the sum of the Council's printed per-category totals (derived by code/parse_schedule_c.py; the document prints no grand total)". Fix the grand_total() docstring and the Test 3 header line in the same edit.

### `DATA-DICTIONARY.md:69 — "The arithmetic never overshoots… the awards fall $50,653,587 short and the appendices supply $49,799,000 of it, 98%, leaving a 0.1% residual"; code/audit_appendix_overlap.py:213-231`

**Problem.** Test 3 is non-probative in both directions, and its FY2027 headline is a coincidence presented as causation. (a) The appendix money is not inside the category totals at all — the Council's disclosure proves category total + streams = document total — so the appendices cannot 'supply' any part of a category shortfall. (b) The $50,653,587 shortfall is body extraction loss plus post-adoption/undesignated money, distributed across 20 of 25 categories, not concentrated where the streams would sit. (c) 'Never overshoots' cannot fail: award rows under-capture their own categories in every one of the 13 years, so overshoot is arithmetically impossible regardless of the answer. (d) 6 of the 13 rows (FY2015-FY2020) show $0 appendices only because the parser extracted none, so those rows test nothing.

**Evidence.**

```
Council FY2027 disclosure (code/parse_expense_disclosure.parse_year): total $705,564,000; rows with source in {Aging,Local,Youth} = 467/2,558/835 rows, $5,610,000/$36,539,000/$7,650,000. 655,764,999 + 49,799,000 = 705,563,999 vs 705,564,000 -> delta $1. Streams are therefore OUTSIDE the 25 categories.
Per-category FY2027 printed vs award-row gap (recomputed from fy27_schedule_c_initiatives.csv vs fy27_schedule_c_awards.csv): Youth Services 12,395,048; Food Initiatives 9,201,000; Older Adult Services 6,778,419; Cultural Organizations 6,169,000; Housing 5,248,250; Small Business/Workforce 3,037,049; Environmental 1,434,000; Education 1,153,114; … 20 of 25 categories nonzero; TOTAL 50,653,587. Appendix A is $5,610,000 against a $6,778,419 Older Adult gap and appendix C $7,650,000 against a $12,395,048 Youth gap — and there is no body category that could host $36,539,000 of 'Local'.
FY2027 PDF page 305 shows one direct cause of the gap: "YouthBuild Project Initiative $1,490,000 … The Council will designate $1,490,000 post-adoption for Fiscal 2027."
```

**Suggested fix.** Delete the '98% of the shortfall' argument entirely — it is a coincidence between two unrelated quantities. Replace Test 3 with the disclosure arithmetic: category total + Aging/Local/Youth streams = the workbook total to $1 in FY2027. Separately document the $50,653,587 as an unresolved body-detail capture gap (post-adoption + extraction), which is the opposite of what the current text implies.

### `code/audit_appendix_overlap.py (whole file) vs standing rule 'A regex may NOMINATE; only the Council's own data may DECIDE'`

**Problem.** A published reversal of a documented claim was decided entirely by pattern-matching: a ToC regex, three substring counts, and an EIN/MONEY regex over pdftotext output, plus sums of the repo's own derived CSVs. The Council's own data that settles the question was already in the repo, already had a working stdlib parser, and was never consulted — source/expense-funding-disclosure/funded_disclosure_FY*.xlsx carries a per-award `source` column naming the funding stream. The repo had even already built data/recovered/schedule_c_appendix_recovered.csv from those same workbooks and PARSING.md already calls that sidecar 'additive', so the deciding evidence was one import away.

**Evidence.**

```
code/audit_appendix_overlap.py imports csv, glob, os, re, subprocess only — no reference to source/expense-funding-disclosure or parse_expense_disclosure anywhere in the file or its test.
$ python -c "import parse_expense_disclosure as P; aw,_=P.parse_year('source/expense-funding-disclosure/funded_disclosure_FY2027.xlsx')" -> 10,040 rows, $705,564,000; Counter(a.source) gives Local 2558 $36,539,000 / Youth 835 $7,650,000 / Aging 467 $5,610,000, exactly the three appendix CSVs.
Per-year check FY2021-FY2027: appendix CSV dollar totals equal the disclosure stream dollar totals ($5,610,000 / $36,539,000 / $7,650,000) in essentially every year; FY2027 matches on row count too (467/2,558/835 EXACT).
```

**Suggested fix.** Add a fifth test that reads the disclosure workbooks and asserts (a) appendix CSV totals == disclosure stream totals per year and (b) category grand total + stream total == disclosure total. Make that test the stated basis of the DATA-DICTIONARY correction, and demote the four regex tests to corroboration.

### `code/test_audit_appendix_overlap.py:63-68 test_round_thousand_split_is_what_bounds_the_double_counting`

**Problem.** Wholly tautological. It asserts three literal arithmetic facts (5000 % 1000 == 0, 29730 % 1000 != 0, 833333 % 1000 != 0) and never calls A.twins() or any other program code. The test module's own docstring lists it as coverage item 2 — "twins() round/distinctive split. The upper bound on double-counting rests entirely on it" — so it reads as assurance for the $447,500 / 0.012% upper bound that BLOCKER 2's claimed Test 4 rests on. It certifies nothing. twins() has ZERO test coverage.

**Evidence.**

```
Six independent mutations of twins()/audit() all SURVIVED with 14/14 passing (harness /tmp/nycb-audit/mutate.py, mutate2.py, run against a /tmp copy):
A5  odd = [r for r in t if k(r)[1] % 1000]  ->  odd = list(t)                     : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
A6  split INVERTED (if not k(r)[1] % 1000)                                        : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
A20 t = [r for r in ap if k(r) in aw]  ->  t = list(ap)  (every row a twin)       : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
A21 t = []  (no row ever a twin; bound becomes $0)                                : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
A22 ap = []  (appendix rows never loaded)                                         : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
A23 audit(): odd = {p for p in both if p[1] % 1000}  ->  odd = set(both)          : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
```

**Suggested fix.** Delete the arithmetic asserts and test the function. Build two tiny CSV trees under tmp_path (one awards file, one appendix file), monkeypatch the glob root, and assert twins() returns the expected (ap_rows, twin_count, twin_dollars, odd_count, odd_dollars) — with one $5,000 twin that must land in the round bucket and one $29,730 twin that must land in the distinctive bucket. A21 and A22 (bound silently collapsing to $0) must both fail.

### `code/test_verify_amounts_against_pdf.py:87-91 test_leading_wrapped_column_does_not_break_the_name_match`

**Problem.** The test passes with names_us() fully disabled, so it cannot detect the bug it is written for. Its fixture row uses EIN 20-2765775, which appears on exactly ONE line of the PAGE fixture, so verify()'s `pinned = named is not None or len(hits) == 1` returns pdf_confirms via the single-line disjunct no matter what names_us() does. The docstring claims "A prefix-anchored match would miss every one" — a prefix-anchored match is exactly what it fails to catch.

**Evidence.**

```
Replaced the whole body of names_us() with `return False` in the /tmp copy, then ran only the tests that claim to cover it:
$ pytest code/test_verify_amounts_against_pdf.py -k "wrapped_column or single_line"
=== names_us() disabled entirely; running the test that claims to cover it ===
..                                                                       [100%]
2 passed, 5 deselected in 0.01s
And the targeted mutation of the exact documented bug:
V5  `return bool(c) and c in canon(line)` -> `return bool(c) and canon(line).startswith(c)`  : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
```

**Suggested fix.** Give the wrapped-column fixture a second line under EIN 20-2765775 (a different org, a different amount) so len(hits) == 2 and the single-line disjunct cannot fire. Then pdf_confirms is reachable only through names_us(), and V5 / names_us->False both fail.

### `code/verify_amounts_against_pdf.py:155 — `pinned = named is not None or len(hits) == 1``

**Problem.** `pinned` is not sufficient to justify the word "confirms". I ran the audit's own stated control (rotate a real same-year amount onto each row) over 3,088 real award rows across all 13 years: 8.4% of deliberately-wrong amounts still returned the strong verdict `pdf_confirms`, and 13.9% returned confirms-or-weak. The module docstring (lines 24-30) rejects the FIRST version of this check because it scored 14.1% on that same axis. The shipped version scores 13.9% on that same axis. The tightening that the commit message presents as the reason to believe the result is, on the control the docstring itself names, statistically indistinguishable from the version it replaced. Per-year the strict rate is far worse than the 11.0% AMOUNT-AUDIT.md reports for the 440: FY2025 20.9%, FY2024 19.3%, FY2020 16.1%.

**Evidence.**

```
/tmp/p_control.py (rotate amounts within each fiscal year, 250-row random sample per year, seed 7) → `ALL YEARS CONTROL: {'pdf_contradicts': 2659, 'pdf_confirms': 259, 'pdf_confirms_weak': 169, 'pdf_ein_absent': 1}  n= 3088` / `FALSE-CONFIRM RATE (deliberately wrong amounts that still pdf_confirms): 8.4%` / `FALSE-CONFIRM incl. weak: 13.9%`. Per-year strict pdf_confirms on rotated amounts: 2015 2.9%, 2019 3.3%, 2020 16.1%, 2022 7.0%, 2024 19.3%, 2025 20.9%, 2026 14.9%, 2027 14.5%. Docstring line 27: "**14.1% of deliberately-wrong rows still confirmed.**"
```

**Suggested fix.** Do not publish `pdf_confirms` as a settled verdict on this evidence. Either (a) rename the verdict to something that does not read as settled (`pdf_amount_present_under_ein`), or (b) require the pin to be unique — exactly one printed line in the year carries our EIN, our amount, AND our name — and re-measure the rotation control against that stricter rule before any claim reversal rests on it. Publish the shipped version's control number next to the first version's 14.1%, not only the rejected version's.

### `data/AMOUNT-PDF-VERIFICATION.csv:41 (row data/fy17/schedule_c/fy17_schedule_c_awards.csv:163) and data/AMOUNT-AUDIT.md:163-165 ("### The 18 `rounding` rows: the PDF backs our figure, not the disclosure's" / "All 18.")`

**Problem.** The (EIN, amount) pair on this row is an artifact of a one-row EIN-column offset printed in the FY2017 PDF itself, not a real award. The claim "on all 18 rounding rows the PDF backs OUR figure, not the disclosure's" is false for this row: no Council record — PDF-by-name, FY2016 PDF, FY2016 disclosure, or FY2017 disclosure — asserts that EIN 11-2498292 received $29,730. The script confirms it because a second extraction engine reproduces the same misprint. Cross-engine agreement tests the extraction, not the document; a printing error in the source is invisible to any number of engines, which voids the commit's central 'two engines, two text models, same bytes' argument for this class of row.

**Evidence.**

```
pdfplumber (pdfminer.six, third engine, coordinate-level) on source/FY17/FY17-Schedule-C.pdf page index 81, one baseline per row, all x0=374 for the EIN column:
  top=561.6 Clinton@40 | 11-2652331@374 | $29,729@518
  top=575.6 Community@40 | 13-2851988@374 | $29,729@518
  top=589.5 El Barrio's@40 | 13-2564241@374 | $29,729@518
  top=603.5 Eviction@40 | 13-3248777@374 | $29,729@518
  top=617.4 Good@40 | 13-3311582@374 | $29,729@518
  top=631.3 Gowanus@40 | 13-2915659@374 | $29,729@518
  top=645.2 Greater@40 | 11-2498292@374 | $29,730@518   <-- the line the script confirmed against
  top=659.1 Harlem@40 | 11-2382250@374 | $29,730@518
  top=687.0 Housing Conservation@40 | 51-0141489@374 | $29,730@518  <-- offset self-corrects here

Council's own disclosure (code/audit_amounts.load_disclosure), FY2016 AND FY2017 independently, both give the shifted-back mapping:
  132851988 -> 'clintonhousingdevelopmentcompany'
  132564241 -> 'communityleagueofheights'
  133248777 -> 'elbarriosoperationfightback'
  133311582 -> 'evictioninterventionserviceshomelessnessprevention'
  132915659 -> 'goodoldlowereastside'
  112498292 -> 'gowanuscanalcommunitydevelopment'   {29729: 1}   <-- NOT Greater Ridgewood
  112382250 -> 'greaterridgewoodrestoration'        {29730: 1}

The FY2016 PDF (build /tmp/audit440/fy2016.layout.txt L4034-4041) agrees with the disclosure, not with FY2017:
  4039| Gowanus Canal Community Development Corporation  11-2498292  $29,730
  4040| Greater Ridgewood Restoration Corporation        11-2382250  $29,730

Our published row (data/fy17/schedule_c/fy17_schedule_c_awards.csv:163):
  ein=112498292  amount=29730  organization='Good Old Lower East Side, Inc. 13-3311582 * $29,729 Gowanus Canal Community Development Corporation 13-2915659'
And our corpus has NO row under 112
```

**Suggested fix.** Withdraw "All 18" from data/AMOUNT-AUDIT.md:165 and re-verify each rounding row against the disclosure's EIN->name mapping, not against the printed line alone. Add a printed-column-integrity check: for any confirming line, assert that the disclosure's name for that EIN matches the name printed on the line (canonicalized); a mismatch is a source-print defect, not a confirmation. Downgrade fy17:163 to a new verdict (e.g. pdf_source_conflict) and state in AMOUNT-AUDIT.md that cross-engine agreement cannot detect an error in the printed document.

### `data/AMOUNT-AUDIT.md:169 ("**None is an amount defect.**") and :20 / :149 ("all 440 with their (EIN, amount) pair printed on one line" / "Every one of the 440...")`

**Problem.** 11 of the 440 rows are flagged org_merged or org_prose by the repo's own validator, whose source comment states "the row's own `amount` may belong to a DIFFERENT organization than its `organization` names, so this is an accuracy signal, not a cosmetic one." AMOUNT-AUDIT.md asserts the opposite. Worse, 4 of those 11 got the full-strength `pdf_confirms` verdict, so the script's own "still needing a human" list (41) excludes them: rows the repo elsewhere calls accuracy defects are published as settled.

**Evidence.**

```
Using the repo's own regexes (code/validate_data.py:56 EIN_IN_TEXT, :61 ORG_PROSE) against data/AMOUNT-PDF-VERIFICATION.csv:
  org_merged = 7, org_prose = 4, total defective = 11, dollars = $2,370,587
  merged verdicts: {pdf_confirms_weak: 5, pdf_confirms: 2}
  prose  verdicts: {pdf_confirms_weak: 2, pdf_confirms: 2}
The four reported as pdf_confirms (therefore NOT in the 41 'still needing a human'):
  fy17:163  $29,730  org='Good Old Lower East Side, Inc. 13-3311582 * $29,729 Gowanus Canal Community Development Corporation 13-2915659'
  fy19:304  $10,000  org='Mount Horeb Baptist Church 11-2074467 * $10,000 Mt. Moriah AME Church'
  fy18 appendix_a_aging:331 $10,000 org='.00 The funding will provide seniors over the age of sixty who reside in the greater Clearview, ...'
  fy22 appendix_c_youth:1283 $100,000 org='Funds will ensure children are ready for school and have the support they need to sustain grade-level reading ...'
code/validate_data.py:373-380 comment: "an EIN or a dollar sign inside `organization` means the row boundary was lost ... In both cases the row's own `amount` may belong to a DIFFERENT organization than its `organization` names".
Hand-read of fy22 appendix_c_youth:1283 against /tmp/audit440/fy2022.layout.txt: the row's prose belongs to L4786 (Adams | Literacy (LINC), Inc. - South Jamaica Reads | 133911331 | $100,000) while its EIN/amount come from L4788 (Louis | Little Haiti BK, Inc. | 824710754 | $100,000) — two different awards fused into one published row, reported as pdf_confirms with no flag.
```

**Suggested fix.** Never emit pdf_confirms for a row that validate_data.py flags org_merged or org_prose; give it its own verdict (e.g. pdf_row_identity_lost) and count it in "still needing a human". Replace "None is an amount defect" with the validator's own wording, and reconcile the two documents so the repo does not assert both.


## MAJOR

### `data/AMOUNT-PDF-VERIFICATION.csv:2 (column `pdf_line`, all 440 rows) — generated by code/verify_amounts_against_pdf.py:94 `return fh.read().splitlines()``

**Problem.** `pdf_line` is a Python `str.splitlines()` index, not a line number any standard tool reports. `pdftotext` emits a form feed (\x0c) at every page break; `splitlines()` treats \x0c as a line terminator, `wc -l` / `sed -n Np` / `grep -n` / every text editor do not. All 440 pdf_line values are therefore 10–468 lines too high (median drift 191) against the very cache file the script itself writes. This is the artifact's only positional provenance, and the commit's whole thesis is that a reader can check the row against the document it came from.

**Evidence.**

```
$ .venv/bin/python -c "raw=open('build/pdftext/fy2015.layout.txt','rb').read(); print(raw.count(b'\\n'), raw.count(b'\\x0c'), len(raw.decode().splitlines()))"
18023 292 18315

Row 1 of the CSV: fiscal_year=2015, pdf_line=448, pdf_text="New Yorkers Against Gun Violence 13-3780848 $30,000"
$ sed -n '448p' build/pdftext/fy2015.layout.txt
            <- blank line
$ grep -n "New Yorkers Against Gun Violence" build/pdftext/fy2015.layout.txt | head -1
438:    New Yorkers Against Gun Violence      13-3780848      $30,000

Swept over all 440 rows (matching whitespace-collapsed pdf_text against a \n-split view of the same cache file):
  rows whose pdf_line does NOT match any unix (sed/grep -n) line number: 440 of 440
  drift (splitlines_n - unix_n): min 10  max 468  median 191.0
```

**Suggested fix.** Change `pdf_lines()` to `return fh.read().split("\n")`. Verdicts are unaffected — the form feed just stays glued to the front of each page's first line, and neither the MONEY nor the EIN regex cares — but every pdf_line then resolves with sed/grep/an editor. Regenerate the CSV. If the numbering is kept as-is instead, the column must be renamed or documented as "index into `.splitlines()` of the poppler dump, page breaks counted as lines".

### `data/AMOUNT-PDF-VERIFICATION.csv — 7 rows graded `pdf_confirms_weak` (fy2016:74, fy2016:75, fy2016:94, fy2017:209, fy2018:124, fy2019:166, fy2021:1018); logic at code/verify_amounts_against_pdf.py:121 `c = canon(org)[:18]``

**Problem.** `pdf_confirms_weak` is published as meaning "the amount is printed against this EIN, but among several lines and **none names our organization**" (data/AMOUNT-AUDIT.md:145). For 7 rows the cited line *does* name the organization — it literally begins with it. The cause is that `names_us()` anchors to the FIRST 18 canonical characters of the `organization` field, which is exactly the wrong end for the `org_merged` defect the artifact's own `org_text_merged` column flags: the merge prepends a neighbouring row's text, so our real name sits at the tail. 5 of the 7 rows carrying `org_text_merged='yes'` land in weak for this reason. Worst instance: fy17:209, the row AMOUNT-AUDIT.md singles out as "the one that matters" and quotes as settled ("The PDF prints `Brooklyn Defenders Services 11-3305406 $2,076,666` — our value") while the shipped CSV grades it weak, which the script's docstring glosses as "a person should look." The document and its own artifact disagree about its flagship example.

**Evidence.**

```
Tight test — cited PDF line STARTS with a >=18-char suffix of our org string:
  weak rows matching: 7 of 41
  fy2017:209 org_merged='yes'
    org: 'Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services'
    pdf: 'Brooklyn Defenders Services 11-3305406 $2,076,666'   pdf_ein_lines=10
  fy2016:74  org: 'Clinton Housing Development Company, Inc. 13-2851988 * $29,730 Community League of the Heights, Inc.'
             pdf: 'Community League of the Heights, Inc. 13-2564241 $29,730'
  fy2019:166 org: 'Crime Victims Treatment Center, Inc. 81-5080860 * $45,000 Edwin Gould Services for Children and Families'
             pdf: 'Edwin Gould Services for Children and Families 13-5675643 $45,000'
  (also fy2016:75, fy2016:94, fy2018:124, fy2021:1018)

org_text_merged='yes' rows by verdict: Counter({'pdf_confirms_weak': 5, 'pdf_confirms': 2})

Direction is conservative: correcting these moves rows from weak to confirms (399/41 -> ~406/34), so no published dollar figure is overstated.
```

**Suggested fix.** Two independent fixes. (a) In `names_us()`, test the org string's 18-char suffix as well as its prefix when `org_text_merged` is set — the tail is where the real name lives after a boundary merge. Do NOT use a sliding 18-char window: I tested it and it produces false matches against purpose prose (e.g. fy2022:2145 'richmondhighschool' matching a trailing '...DOE Richmond High S'). (b) Reword the `pdf_confirms_weak` row of the AMOUNT-AUDIT.md table so it matches what the code tests — 'the row's own organization string did not pin the line', not 'none names our organization' — and stop quoting fy17:209 as settled while the artifact grades it weak.

### `DATA-DICTIONARY.md:72 — "the Council's own printed grand totals"; code/audit_appendix_overlap.py:24 "The document prints a GRAND TOTAL"; code/PARSING.md:407 "the printed GRAND TOTAL never being overshot"`

**Problem.** The Council never prints a grand total. In none of the 13 Schedule C PDFs does the string 'GRAND TOTAL' appear. The label is written by this repo's own parser (code/parse_schedule_c.py:365) over `gp`, its running sum of the per-category subtotals it scraped. Attributing a $5.48B figure to 'the Council's own printed grand totals' hands a journalist a number the Council never published and cannot be pointed to on any page.

**Evidence.**

```
$ for y in 2015..2027; do grep -c 'GRAND TOTAL' build/pdftext/fy$y.pages.txt; done
  0 for all thirteen years.
$ grep -n 'GRAND TOTAL' code/parse_schedule_c.py
  365:    L.append(f"{'GRAND TOTAL':52} {gi:>14,} {gp:>14,}  {ok}/{len(cats)} categories exact")
with gp accumulated at line 362 as `p=recon.get(c) or 0; gp+=p`.
```

**Suggested fix.** Say 'the sum of the Council's printed category totals' wherever 'printed GRAND TOTAL' appears, in DATA-DICTIONARY.md, code/PARSING.md and the audit script's docstring and column header.

### `code/audit_appendix_overlap.py:118 (`grand_total()` reads the parser's per-category `printed` column, where unmatched categories score 0)`

**Problem.** The denominator has $0 holes. In 12 category-years the parser scraped no printed total (`printed = 0`, status `DIFF +0` or `no summary block`) while the award CSVs carry $108,101,617 of dollars in those very categories. Those dollars are counted in the numerator and score $0 in the denominator — an apples-to-apples defect independent of the stream problem, and further proof the denominator is a parser artifact rather than a document figure. Correcting it lowers the true capture rate below even the 61.9% body/body figure.

**Evidence.**

```
$ python (parse each *_schedule_c_reconciliation.txt for `^cat  0  0  DIFF +0$` / `no summary block`, sum matching category dollars in the year's awards CSV):
2016 YOUTH AND COMMUNITY DEVELOPMENT 18,976,694 | 2017 YOUTH SERVICES 15,383,600 | 2017 YOUNG WOMEN'S INITIATIVE 675,000 | 2018 Youth Services 5,138,200 | 2018 Young Women's Initiative 1,301,000 | 2019 YOUTH SERVICES 11,493,900 | 2020 Youth Services 12,030,831 | 2021 Youth Services 4,566,248 | 2022 Youth Services 13,042,048 | 2024 YOUTH SERVICES 13,472,048 | 2025 YOUTH SERVICES 9,272,048 | FY2015 BOROUGHWIDE NEEDS 2,000,000 + HEALTH SERVICES AND PREVENTION 750,000
  TOTAL numerator dollars in $0-denominator categories: $108,101,617
```

**Suggested fix.** Either exclude those category-years from both sides, or stop using the parser's summed `printed` column as a public denominator. Do not publish a ratio whose denominator is silently missing categories its numerator counts.

### `DATA-DICTIONARY.md:72 — "Category-level totals are complete: `*_schedule_c_initiatives.csv` sums to $5,474,660,271, within 0.026% of the printed figure."`

**Problem.** 'Complete' is not supported, and 0.026% is a NET figure that cancels offsetting errors. Only 2 of 13 years reconcile all categories cleanly with a full ToC (FY2023 26/26, FY2027 25/25); FY2015 is 24/24 of 24 'reconcilable' but 4 of its 28 ToC categories have no summary block at all; the other 10 years run 24/26, 24/27, 27/28, 25/26, 24/25. The $1,410,565 net delta is the sum of +$200, +$800, +$50,000, +$52,935 against −$100,000, −$700,000, −$714,500. Gross absolute delta is $1,618,435 (0.0296%). The arithmetic rounds fine; the word 'complete' does not survive the reconciliation statuses.

**Evidence.**

```
$ recomputed: SUM initiatives.csv $5,474,660,271 (matches claim); SUM printed $5,476,070,836; net delta $1,410,565 = 0.0258%; gross abs delta $1,618,435 = 0.0296%.
Per-year reconciliation status: 2015 24/24 reconcilable (4 of 28 ToC categories have no summary block) | 2016 24/26 | 2017 24/27 | 2018 24/27 | 2019 27/28 | 2020 27/28 | 2021 25/26 | 2022 24/26 | 2023 26/26 | 2024 24/26 | 2025 24/26 | 2026 24/25 | 2027 25/25.
Per-year deltas driving the net: FY16 −700,000; FY17 +200; FY18 −100,000; FY22 −714,500; FY24 +52,935; FY25 +50,000; FY26 +800.
```

**Suggested fix.** Replace 'Category-level totals are complete' with 'category totals reconcile exactly in 11 of 13 years for most categories; net residual $1,410,565 (0.026%), gross $1,618,435 (0.030%), and 2 of 13 years reconcile every category.' Note that several of the residuals are the PDF's own internal arithmetic inconsistencies (DATA-ANOMALIES.md §1), not extraction error.

### `data/AMOUNT-AUDIT.md:134 — "What the disclosure records is a *different* EIN holding the same amount, which is what a fiscal-conduit arrangement looks like, not what a bled row looks like."`

**Problem.** The stated mechanism is fabricated. In all three disclosure rows named as the competing owner, the `Fiscal Conduit` and `Fiscal Conduit EIN` columns are EMPTY — none is a conduit arrangement. The real mechanisms are three different things, each of them a more interesting finding than the one published: (FY15) a post-adoption reallocation that cut CACF from $833,333 to $500,000; (FY23) a post-adoption redesignation of a printed placeholder; (FY25) an outright omission from the disclosure. The commit reached the correct verdict (withdraw) via a wrong and unverified explanation, and published that explanation as established fact in a human-readable audit report. This is the repo's own standing rule violated in prose form: a plausible pattern was used to DECIDE what the disagreement means, when only the Council's own data may decide.

**Evidence.**

```
Raw disclosure dump (script /tmp/pdfaudit/rawdisc.py, reads source/expense-funding-disclosure/*.xlsx directly). Header ends '... | Purpose of Funds | Fiscal Conduit | FC EIN'. Rows print with two EMPTY trailing cells:

FY2015 | Communities of Color Nonprofit Stabilization | | Hispanic Federation | 133573852 | Cleared | 833333 | DYCD | ... | Funds will support capacity building, streng |  | 
FY2015 | Communities of Color Nonprofit Stabilization | | Coalition for Asian American Children and Fa | 133682471 | Cleared | 500000 | DYCD | ... |  | 
FY2023 | Innovative Criminal Justice Programs | | Fund for the City of New York, Inc. | 132612524 | Cleared | 325000 | DYCD | A More Just NYC | ... |  | 
FY2025 | Citywide Homeless Prevention Fund | | Bridge Fund of New York, Inc., The | 133824852 | Cleared | 164000 | DSS/HRA | ... |  | 

And the true FY23 mechanism, from the same dump — the disclosure replaces the printed MOCJ $325,000 placeholder with two named grantees totalling exactly $325,000:
  Avenues For Justice 100000 / Brooklyn Community Bail Fund 200000 / Department of Probation 200000 / District Attorney-Kings 458000 / Fund for the City of New York 325000 / Justice Innovation 500000 / Liberty Fund 339948 / New York City Criminal Justice Agency 125000 / New York County Defender Services 50000 / Osborne 265000 / Youth Represent 75000  = $2,637,948
The adopted PDF (/tmp/pdfaudit/fy23.txt:1869) says verbatim: "and will designate $325,000 post-adoption:" — Brooklyn Community Bail Fund ($200,000) + NYC Criminal Justice Agency ($125,000) = $325,000 is that post-adoption designation. Not a conduit.
```

**Suggested fix.** Replace the sentence with what the disclosure actually shows, per row: FY15 = post-adoption reallocation (CACF $833,333 adopted vs $500,000 disclosed); FY23 = the printed MOCJ line is an undesignated $325,000 placeholder later split to two named grantees; FY25 = the disclosure has no CSS row for that initiative at all. Cite the Fiscal Conduit columns being empty as the reason the conduit reading is excluded.

### `data/AMOUNT-AUDIT.md:20 and :134 — "0 contradicted, 0 missing" / "All three are false positives" (row fy15_schedule_c_awards.csv:646)`

**Problem.** The withdrawal is correct about the DIAGNOSIS (nothing bled) and wrong to treat the row as closed. The Council's two documents disagree on this award by $333,333: the adopted Schedule C prints $833,333 for CACF, the FY2015 disclosure records $500,000 for the same EIN under the same name. That is a live two-source disagreement, and this audit's own governing sentence is "when two vintages of the truth disagree, the disagreement is the finding" (code/verify_amounts_against_pdf.py docstring). Calling it a "false positive" retires a real, material disagreement under a label that means there was nothing there. Same shape, smaller stakes, at fy25:3465: the FY2025 disclosure has no Community Service Society row under Citywide Homeless Prevention Fund at all, so "$164,000 is corroborated" is true only of the PDF.

**Evidence.**

```
$ .venv/bin/python /tmp/pdfaudit/probe.py  (uses audit_amounts.load_disclosure)
FY2015 ein=133682471 org='Coalition for Asian American Children and Families'
  by_org[(ein,canon)] -> {500000: 1}
FY2025 ein=135562202 org='Community Service Society of New York'
  by_org[(ein,canon)] -> {170469: 1, 5000: 3, 50000: 1, 100000: 1, 230469: 1, 10000: 2}   # no 164000

FY2015 disclosure, full initiative (rawdisc.py): NY Urban League 166666 + 833334 = 1,000,000; Hispanic Federation 166667 + 833333 = 1,000,000; CACF 500000. Sum = $2,500,000 = the printed pot. The adopted PDF (/tmp/pdfaudit/fy15.txt:3523-3525) prints 833,333 / 833,333 / 833,333.

FY2025 disclosure, full initiative: Bridge Fund 41000 + 164000; Coalition for the Homeless 123000 + 492000; no CSS row.
```

**Suggested fix.** Do not label these "false positives." Withdraw only the `neighbour_bleed` verdict (the amount is not another organization's), and re-file fy15:646 as an adopted-vs-disclosure amount disagreement of $333,333, and fy25:3465 as disclosure-omits-the-award. Change the §20 blockquote and the up-front summary at :20 to say "0 contradicted BY THE ADOPTED PDF" rather than settled.

### `code/verify_amounts_against_pdf.py:126 `verify()` — the method as a whole; and data/AMOUNT-AUDIT.md:20 "The 440 rows this audit left unresolved are now settled"`

**Problem.** The check is confirmation-only: it iterates rows that exist in the corpus and asks whether the PDF agrees. It is structurally incapable of finding awards the PDF prints that the corpus never captured, and the report's framing ("settled", "0 contradicted, 0 missing") invites the reader to conclude the award stream is clean in these years. It is not, and the defect is sharper than the generic under-capture DATA-ANOMALIES.md documents: across FY15/FY23/FY25, EVERY provider row present in the PDF but absent from our data is the FIRST row of its provider table — 22 of 22, $17,423,181. One of them sits in the same printed table as the withdrawn row fy23:585 (Avenues For Justice, Inc. 13-3267496 $100,000, Innovative Criminal Justice Programs). So "the PDF prints this row intact" and "the table it sits in is defective" are both true, and the commit reports only the first.

**Evidence.**

```
$ .venv/bin/python /tmp/pdfaudit/firstrow2.py   # parses NAME<gap>EIN<gap>$AMOUNT rows under each "Legal Name … EIN … Amount" header, checks (ein,amount) against every data/fy{YY}/schedule_c/*.csv except *_initiatives.csv
FY15: tables=281 pdf_rows=199 missing=1 ($210,000)  first-of-table=1  non-first=0
FY23: tables=121 pdf_rows=770 missing=12 ($9,495,593)  first-of-table=12  non-first=0
FY25: tables=140 pdf_rows=1252 missing=9 ($7,717,588)  first-of-table=9  non-first=0

The 12 FY23 misses, all first-of-table: Bard College 14-1713034 $250,000 / Justice Innovation, Inc. 85-2810883 $1,595,000 / Community Health Project, Inc. 13-3409680 $100,000 / Avenues For Justice, Inc. 13-3267496 $100,000 / Academy of Medical and Public Health Services 27-2206293 $154,255 / African Services Committee 13-3749744 $60,505 / African Services Committee 13-3749744 $27,000 / Department of Social Services 13-6400434 $77,000 / Bronx Defenders, The 13-3931074 $5,533,333 / Catholic Charities Community Services 13-5562185 $620,000 / City Parks Foundation 13-3561657 $778,500 / Legal Momentum 23-7085442 $200,000

Hand spot-checks (3/3 hold):
$ grep -rn "133267496" data/fy23/schedule_c/*.csv   -> (no output)
$ grep -rn "141713034" data/fy23/schedule_c/*.csv   -> only fy23_appendix_b_local.csv rows at 5000/10000/5000; no $250,000
$ grep -rn "852810883" data/fy23/schedule_c/*.csv   -> awards row 583 at 500000 + appendix rows; no $1,595,000

And the FY23 table containing the withdrawn row reconciles only if the missing row is added: the PDF's 10 printed providers (fy23.txt:1872-1881) sum to $2,637,948 = the printed initiative total; our corpus carries 9 of them = $2,537,948.
```

**Suggested fix.** State plainly in AMOUNT-AUDIT.md that the pass verifies amounts on rows we have and says nothing about rows we lack. Then file the first-row-of-table omission as a new DATA-ANOMALIES entry (it is a distinct, mechanically diagnosable class, not the diffuse under-capture of §13/§21) and check whether `parse_awards()` consumes the first data line after a `Legal Name … EIN … Amount` header as part of the header.

### `code/audit_appendix_overlap.py:140-162 (twins) and :256 "upper bound on double-counting, by distinctive-amount twins: $447,500"`

**Problem.** $447,500 is not an upper bound. It is the odd-amount subset of twins; the actual upper bound on double-counting from this method is ALL twins, $46,034,500 (1.230% of the headline), 103x larger. Separately, twins() keys on (EIN, amount, organization) — narrower than the repo's standing (EIN, amount) join key. Narrowing the key on an upper-bound calculation is the wrong direction: it drops real matches. On the standing key the same odd-amount figure is $1,070,750 and the all-twins figure is $58,010,750 (1.550%). The claim "upper bound on double-counting $447,500 corpus-wide (0.012%)" therefore understates by between 2.4x and 130x depending on which of the two assumptions you relax.

**Evidence.**

```
Recomputed over data/fy{15..27}/schedule_c/ with the script's own normalizers:
  twins on (ein,amt,org): n=4,654  $46,034,500  = 1.230% of $3,741,615,569
  twins on (ein,amt)    : n=6,138  $58,010,750  = 1.550%
  odd subset (ein,amt,org): n=109  $447,500  = 0.0120%   <- what the script prints
  odd subset (ein,amt)    : n=284  $1,070,750 = 0.0286%
Per-year on the standing key, e.g. fy27: twins 1,135 rows $12,168,000 (vs 953 / $10,791,000 on the 3-part key).
Also note `odd` is `amount % 1000`, so $2,500/$7,500/$12,500 count as "distinctive" — among the most common designation amounts.
```

**Suggested fix.** Print both numbers and label them honestly: "$46.0M all twins (upper bound); $447,500 after discarding round-thousand amounts as coincidence (assumption, not a bound)". Switch the join to the standing (EIN, amount) key, or state in the docstring why the org component is added and that it lowers the bound.

### `code/audit_appendix_overlap.py:98-109 (pairs), :181-186, :194-195`

**Problem.** pairs() runs over every page of all 13 PDFs and its four outputs (body_pairs, apx_pairs, overlap, overlap_odd) are never printed — main() uses none of them. It is the bulk of the script's work, silently discarded, and a reader of the file would believe a PDF-level overlap test was performed and reported. It is also broken where it matters: MONEY requires a literal "$", which FY2016-FY2020 appendix pages do not print, so apx_pairs is 0-3 for FY2015/16/17/19/20 — 217 appendix pages in FY2020 yielding exactly zero pairs. Had these numbers been printed as evidence, those years' zeros would have read as "no overlap" when they are "no scan". Seven dict fields in total are computed and never used (body_pairs, apx_pairs, overlap, overlap_odd, awards_rows, apx_rows, reconciliation).

**Evidence.**

```
grep of main() (lines 201-257) for each key returns 0 occurrences for all seven.
Exposing the values by calling A.audit(fy) directly: FY2015 apx_pairs=2, FY2016 apx_pairs=2, FY2017 apx_pairs=3, FY2019 apx_pairs=3, FY2020 apx_pairs=0 (appendix pages 189..405); FY2021-27 apx_pairs 2,606-3,080.
Cause, build/pdftext/fy2020.pages.txt page 190 (Appendix A): "Barron  Bergen Basin ... - Abe Stark Senior Center   113199040   11,500  Funding to support..." — no dollar sign. MONEY = re.compile(r"\$\s?([\d,]+)").
```

**Suggested fix.** Delete pairs() and its call sites (lines 98-109, 181-186, and the four dict entries), or print the results and make MONEY tolerate a bare amount. Do not leave a broken, expensive, unreported test in a script whose output is being cited to reverse a published claim.

### `data/AMOUNT-AUDIT.md — control table, row "amounts rotated within the fiscal year | 11.0% still confirmed"`

**Problem.** Does not reproduce under any within-fiscal-year rotation I could construct, and the claimed figure is lower (i.e. flatters the check) than every variant I measured. 11.0% is also not expressible as n/440 (48/440 = 10.9%, 49/440 = 11.1%), so the denominator is undocumented as well.

**Evidence.**

```
I swept ALL 103 possible rotation offsets within fiscal year over the 440-row pool (/tmp/audit_pdf/controls2.py, using my own reimplementation of the verdict logic, which reproduces the shipped CSV 440/440 on untouched data):
  rotation offsets swept: 103
  min confirms: (offset 16, 79 rows) 18.0%
  max confirms: (offset 57, 156 rows) 35.5%
  median confirms %: 21.6%
  any offset giving 11.0% (48 or 49 rows)? []
Other rotation readings measured: physically adjacent row in the same award CSV -> 63.2% (offset +1), 61.6% (-1), 59.8% (+2). Random real amount drawn from the same-FY corpus (6 seeds) -> 5.9%-7.3%.
```

**Suggested fix.** Either publish the code that produced 11.0% (a `--control rotate` flag on verify_amounts_against_pdf.py, or a test) so the number is reproducible, or restate the control with the definition and denominator spelled out. As written the number I get for the closest reading is 18.0%-32.5% depending on offset; median 21.6%.

### `data/AMOUNT-AUDIT.md — control table, row "a *different* EIN's real amount planted on each row | 5.0% still confirmed"`

**Problem.** Does not reproduce. Every construction of "a different EIN's real amount" I measured lands 2.6x-4.6x higher than 5.0%. The claimed 5.0% is close to a DIFFERENT control I ran (a random real amount from the same-FY corpus, 5.9%-7.3%), and my different-EIN result (13.2%-16.6%) is close to the 11.0% published on the row above it — which suggests the two control rows may be swapped, and both understated.

**Evidence.**

```
/tmp/audit_pdf/controls2.py, 6 seeds each:
  random amount printed under a DIFFERENT EIN in that year's PDF: conf=73/440=16.6%, 69=15.7%, 58=13.2%, 73=16.6%, 66=15.0%, 73=16.6%
  amount taken from another of the 440 rows carrying a different EIN: conf 18.4%, 19.1%, 19.3%, 21.6%, 21.8%, 23.2%
  (for contrast) random real amount from same-FY corpus: 5.9%, 6.6%, 6.6%, 6.8%, 7.3%
Baseline on untouched data reproduces exactly: confirms=399 (90.7%), confirms+weak=440 (100.0%), contradicts=0.
```

**Suggested fix.** Publish the control harness. If the rows are swapped, swap them and correct both figures; my measurements for the two stated definitions are ~6% (random real same-year amount) and ~15% (different-EIN real amount), not 11.0% and 5.0%.

### `code/verify_amounts_against_pdf.py and code/test_verify_amounts_against_pdf.py — the four controls`

**Problem.** Two of the four controls (rotation, different-EIN) are published as measured percentages in a data document but are implemented nowhere in the commit. The test file implements only the mechanism tests; the script has no control path and no seed. Nobody — including the author — can re-derive 11.0%, 5.0%, or the docstring's 14.1%. The commit's own thesis is that a check that confirms everything is worthless unless measured against controls; the controls are therefore load-bearing, and they are unfalsifiable as shipped.

**Evidence.**

```
$ grep -n 'rotat\|control\|11.0\|5.0\|14.1' code/test_verify_amounts_against_pdf.py code/verify_amounts_against_pdf.py
-> only prose in docstrings; no code. `pytest code/test_verify_amounts_against_pdf.py -q` -> 7 passed, none of which is a control. The 7 tests are: amount-absent, ein-absent, single-line, multi-line-weak, multi-line-named, wrapped-column, no-apply-path.
```

**Suggested fix.** Add a `--control {plus7,absent,rotate,other-ein}` flag (seeded) or four tests that assert the published percentages within a tolerance. Two of the four (+$7 and planted-absent) I did reproduce exactly at 440/440 pdf_contradicts, so only the two stochastic ones need pinning.

### `data/AMOUNT-AUDIT.md — "That ambiguity affects **43 of the 440**, and is the whole content of the 41 `pdf_confirms_weak`: their `(EIN, amount)` pair is printed, but the row's `organization` text is separately known-defective (`org_merged`, §20/§21) or the EIN carries the same amount on more than one line."`

**Problem.** Three separate errors in one sentence. (a) 24 of the 41 weak rows satisfy NEITHER stated criterion — they are weak only because the 18-char name prefix matched no line; the stated explanation covers 17 of 41. (b) Under the doc's own two criteria applied to all 440, the count is 50, not 43; 43 is reachable only as weak-union-org_merged (41+2), which is circular because it counts the verdict itself as the ambiguity. (c) The ambiguity is NOT confined to the weak rows: 31 of the 399 `pdf_confirms` have their amount printed on more than one line under their EIN, and on 17 of those the organization-name pin matches MORE THAN ONE carrying line — so "the evidence points at one printed row, not at an EIN's whole block" fails on 17 rows classified as strong confirms.

**Evidence.**

```
Computed from my per-row reproduction (/tmp/audit_pdf/mydetail.json, which matches the shipped CSV 440/440 on verdict, pdf_line and pdf_ein_lines):
  |weak| 41 |org_merged| 7 |amount on >1 line under the EIN| 43
  weak & multi: 12   weak & org_merged: 5
  org_merged | multi (doc's stated criteria, all 440): 50
  weak | org_merged: 43
  weak | org_merged | multi: 74
  weak rows explained by NEITHER stated criterion: 24
  pdf_confirms with >1 carrying line: 31
  pdf_confirms where the name-prefix matches >1 carrying line (pin does not resolve to one row): 17
    e.g. fy20_schedule_c_awards.csv:2306 'Jamaica Service Program for Older Adul' -> PDF lines [7911, 8251]; fy21_appendix_b_local.csv:2538 'Shetu, Inc.' -> [13746, 13748]; fy21_appendix_c_youth.csv:399 'Helen Keller International, Inc.' -> [10512, 15698]
Also: 92 of the 399 confirms have an 18-char name prefix that ALSO matches a same-EIN line carrying a DIFFERENT amount (e.g. 'neighborhoodhousin' matches both 'Neighborhood Housing Services of East Flatbush' and '...of Bedford-Stuyvesant' under EIN 13-3098397 in FY2016) — the amount, not the name, is doing the discriminating.
```

**Suggested fix.** State the ambiguity count under a single non-circular definition. Under the doc's own stated criteria it is 50 of 440; folding in the weak rows it is 74. And drop "is the whole content of the 41 pdf_confirms_weak" — 24 of the 41 are weak for a third reason (name-match failure on a multi-line EIN) that the sentence does not name.

### `DATA-DICTIONARY.md:70 — "the upper bound on double-counting across all 13 years at $447,500, or 0.012% of the headline"; code/audit_appendix_overlap.py:159-160 (twins/odd)`

**Problem.** $447,500 is not an upper bound on anything. It is the subtotal of (EIN, amount, organization) twins whose amount is not a round thousand; every round-thousand twin is excluded by fiat. Excluding the majority of a population by assumption cannot bound that population from above. The quantity the sentence claims to bound is $46,034,500 across the 13 years — 103x larger — and $10,791,000 in FY2027 alone. The commit's own test file (test_round_thousand_split_is_what_bounds_the_double_counting) enshrines the error while asserting nothing but Python's modulo operator.

**Evidence.**

```
Script's own Test 4 output, twin $ column: 2021 1,755,000 | 2022 2,252,500 | 2023 3,071,000 | 2024 9,126,000 | 2025 9,785,500 | 2026 9,253,500 | 2027 10,791,000 = $46,034,500. Published 'upper bound' $447,500 -> 46,034,500/447,500 = 103x.
code/test_audit_appendix_overlap.py: `assert 5000 % 1000 == 0; assert 29730 % 1000 != 0; assert 833333 % 1000 != 0` — no call into twins().
(The conclusion is nonetheless safe: I checked all 953 FY2027 twins against the disclosure — 953/953 have BOTH a stream row and a category row at that (EIN, amount), and 163/163 do so even when member is added. 15 hand-sampled twins are all two distinct designations, e.g. Phipps Neighborhoods / J. Sanchez / $5,000 appears once as source=Local 'Council District 17' and once as source=Anti-Poverty 'Events & Community Food Distributions'.)
```

**Suggested fix.** Drop the words 'upper bound'. State the measured exposure ($46,034,500 of (EIN, amount, organization) twins over 13 years, $2,050,000 for FY2027 once member is also required) and then resolve it with the disclosure check that shows each twin is two distinct designations. Replace the modulo test with one that calls twins() on a fixture.

### `DATA-DICTIONARY.md:68 — "appear **zero** times across the body pages of all 13 years"; code/audit_appendix_overlap.py:37 (STREAMS)`

**Problem.** Two defects. (1) Self-contradiction: the sentence says zero, then the parenthetical concedes one FY2026 hit, and the script's own printed table shows 1 for FY2026 — the published claim is refuted by the output it cites. (2) The null is partly manufactured: STREAMS is fixed at ('Aging Discretionary', 'Local Initiative', 'Youth Discretionary'), but FY2019 prints 'YOUTH INITIATIVES' and FY2021 prints 'Local Discretionary' / 'Youth Discretionary'. Searching for a label the document does not use guarantees zero hits and proves nothing. Searching the labels the documents actually use produces additional body hits.

**Evidence.**

```
Script output TEST 2 column: FY2026 = 1, not 0.
ToC lines pulled from the cached page text: FY2019 'APPENDIX C: YOUTH INITIATIVES……….PAGE 177-226'; FY2021 'Appendix B: Local Discretionary….Page 30-167'.
Re-run of Test 2 over the same body ranges with the documents' own labels: 'youth initiative' body counts = FY2016 2, FY2023 1, FY2024 2, FY2025 3, FY2026 1, FY2027 2 (all incidental prose, but nonzero).
The FY2026 hit, printed in full: body p52 'Millennium Development - Community Development - Council … Funds will be used to support community development, event programming, and local initiatives'.
```

**Suggested fix.** Derive the search terms per year from that year's own ToC appendix titles instead of a fixed tuple, report the actual counts, and change 'zero times' to the true number with the incidental hits enumerated. Note in the prose that absence of a label is weak evidence at best — the deciding evidence is the disclosure `source` column.

### `DATA-DICTIONARY.md:72 — "$3,741,615,569 against … $5,476,070,836 — **68.3%**"`

**Problem.** Scope-inconsistent ratio, and the inconsistency is created by this commit's own thesis. The numerator is body award rows PLUS appendix rows; the denominator is body categories only. If the appendices are additive (the commit's conclusion), the denominator must also include the appendix streams. Publishing 68.3% overstates the corpus's capture rate in the same paragraph that argues the corpus under-captures.

**Evidence.**

```
13-year category grand totals $5,476,070,836; 13-year Aging+Local+Youth stream dollars from the Council disclosure workbooks $647,537,100; scope-consistent denominator $6,123,607,936. 3,741,615,569 / 6,123,607,936 = 61.1%, not 68.3%. (The scope-consistent body-only comparison is 3,388,618,294 / 5,476,070,836 = 61.9%.) Either consistent pairing gives ~61%.
```

**Suggested fix.** Publish 61.1% against the disclosure-derived total, or 61.9% body-vs-body. State which pairing is used. Do not mix scopes.

### `DATA-DICTIONARY.md:67 — "From FY2019 the table of contents gives each appendix its own page numbering, restarting at page 1"`

**Problem.** Both halves are wrong, and the test is non-probative regardless. (a) FY2018's ToC also carries restarting appendix pagination; the script scores FY2018 as 0 solely because TOC_APPENDIX requires the literal word 'page', which the FY2018 line omits. 'From FY2019' describes a regex limitation, not the corpus. (b) Only Appendix A restarts at 1 — B and C continue the appendix block's numbering — as the commit's own test asserts and its own restart counter (1 per year, never 3) confirms. (c) Even if both were right, separate pagination establishes separate printing, not separate money; a re-sorted index would also get its own page numbers.

**Evidence.**

```
FY2018 ToC line from the cached page text: 'Appendix A: Aging Discretionary……….1-33' / 'Appendix B: Local Initiatives……….34-178' / 'Appendix C: Youth Initiatives……….179-228' — restarting, but with no 'PAGE' token, so TOC_APPENDIX.findall returns 0 and the script prints 'apx in ToC 0' for FY2018.
FY2027 ToC: 'Appendix A … Page 1 -26', 'Appendix B … Page 27 - 149', 'Appendix C … Page 150 - 193' — one restart, continuous thereafter. Script column 'restart at p1' = 1 for every year FY2019-FY2027.
code/test_audit_appendix_overlap.py already states it: '# Only Appendix A restarts at 1'.
```

**Suggested fix.** Make the 'page' token optional in TOC_APPENDIX so FY2018 is measured, and reword to 'from FY2018 the ToC gives the appendix block its own page numbering, restarting at 1 at Appendix A and running continuously through C'. Add one sentence conceding that pagination shows separate printing, not separate money.

### `code/audit_appendix_overlap.py:200-207 (audit() returns overlap/overlap_odd) vs main() which never prints them`

**Problem.** The script computes the one PDF-level statistic that speaks directly to duplication — (EIN, amount) pairs appearing on BOTH body pages and appendix pages — stores it in the result dict as `overlap`/`overlap_odd`, and then omits it from every printed table. The dropped number is adverse to the conclusion: it shows 15.8-17.5% of appendix pairs also occur on body pages in FY2024-FY2027. An audit that reverses a published claim must not compute an adverse statistic and silently withhold it.

**Evidence.**

```
Re-running audit() per year and printing the suppressed fields: FY2021 149/3,080 (4.8%) | FY2022 143/2,948 (4.9%) | FY2023 149/2,910 (5.1%) | FY2024 426/2,695 (15.8%) | FY2025 451/2,641 (17.1%) | FY2026 435/2,641 (16.5%) | FY2027 455/2,606 (17.5%). None of these appear in the script's stdout, which prints only toc_appendices, toc_restarts_at_1, stream_hits, the Test 3 dollars and the Test 4 twin columns.
```

**Suggested fix.** Print overlap / overlap_odd as a named test with its own row, and resolve it explicitly against the disclosure (I confirmed the overlapping pairs are distinct designations). Either report it or delete the computation — do not compute and hide.

### `code/audit_appendix_overlap.py:213-231, Test 3 rows for FY2015-FY2020; data/fy19/schedule_c/fy19_appendix_*.csv`

**Problem.** Six of the thirteen Test 3 rows and five of the Test 4 rows show $0 / blank appendices because the parser extracted none, not because the documents have none. The tables give no indication of this, so '0 of 13 years' and the 13-year totals read as thirteen measurements when at most eight are. The reconciliation files for those years locate Appendix A/B/C pages, and the Council disclosure shows ~$49.8M of stream money in each of them.

**Evidence.**

```
$ ls -l data/fy19/schedule_c/ -> fy19_appendix_a_aging.csv 48 bytes, _b_local.csv 55 bytes, _c_youth.csv 48 bytes (header only); same for fy20; fy18 _b_local and _c_youth are header-only.
fy19_schedule_c_reconciliation.txt: 'sections: body 6..131 | A 132 | B 163 | C 308' — the appendices are located and not extracted.
Council disclosure stream totals for those years: FY2018 $49,804,000 | FY2019 $49,724,000 | FY2020 $49,799,000 — of which the CSVs hold $4,419,275 / $0 / $0.
```

**Suggested fix.** Mark those rows 'not extracted' rather than 0, and change '0 of 13 years' to state how many years actually carry appendix data (8, and only 7 with all three streams). Cross-reference data/recovered/schedule_c_appendix_recovered.csv, which already holds FY2015-FY2020 stream awards recovered from these same workbooks.

### `code/test_verify_amounts_against_pdf.py:67-70 test_single_line_ein_confirms`

**Problem.** Does not test the single-line rule it is named for. The fixture org "Brooklyn Book Bodega" canonicalizes to exactly 18 characters and is printed on the matched line, so names_us() returns True and `named is not None` pins the row; the `len(hits) == 1` disjunct is never load-bearing. Combined with the finding above, neither test isolates the single-line disjunct — it can be deleted outright with the suite still green.

**Evidence.**

```
V2  `pinned = named is not None or len(hits) == 1`  ->  `pinned = named is not None`  (single-line rule deleted entirely)
  : {"id":"V2","status":"SURVIVED  <-- test gap","failed":[],"summary":"14 passed in 0.01s"}
Contrast: V3 (drop the name rule) IS caught by test_multi_line_ein_with_our_name_confirms, so only the single-line disjunct is unguarded.
```

**Suggested fix.** Change the fixture org for this test to a name that does NOT appear on the printed line (e.g. row("471234567", 12500, "Bodega Books Brooklyn Ltd")). pdf_confirms then depends solely on len(hits) == 1, and V2 fails.

### `code/verify_amounts_against_pdf.py:121 (`c = canon(org)[:18]`) — no covering test in code/test_verify_amounts_against_pdf.py`

**Problem.** The 18-character anchor length has no test. It is the sole stated defense against a short-name collision promoting a pdf_confirms_weak to a pdf_confirms (docstring: "18 canonical characters is long enough that a collision would have to be a near-identical name"). It can be shortened to 3 characters — turning the name match into a near-free coincidence across a 483-line EIN block — with the suite fully green.

**Evidence.**

```
V4  `c = canon(org)[:18]` -> `c = canon(org)[:4]`   : {"status":"SURVIVED  <-- test gap","failed":[],"summary":"14 passed in 0.01s"}
V18 `c = canon(org)[:3]`                            : {"status":"SURVIVED  <-- test gap","failed":[],"summary":"14 passed in 0.01s"}
```

**Suggested fix.** Add a test with a multi-line EIN where our org shares a short prefix with the printed org but diverges before character 18 (e.g. ours "Brooklyn Book Bodega Inc", printed "Brooklyn Botanic Garden") and assert the verdict is pdf_confirms_weak, not pdf_confirms. V4 and V18 then both fail.

### `code/test_audit_appendix_overlap.py:27-35 test_toc_regex_matches_the_printed_form`

**Problem.** The docstring claims "FY2024's actual line, ellipsis character and en dash included" — but the fixture separator is a plain ASCII hyphen, so neither the `…` member of `[.…]` nor the `–` member of `[-–]` in TOC_APPENDIX is exercised. Both can be deleted with the suite green. The en dash is live code, not defensive padding: FY2023's real printed line uses one.

**Evidence.**

```
A1/A18  TOC_APPENDIX `[.…]+` -> `[.]+` AND `[-–]` -> `[-]`  : {"status":"SURVIVED  <-- test gap","failed":[],"summary":"14 passed in 0.01s"}
(the non-greedy `(.+?)` absorbs the ellipsis character, so removing it from the class changes nothing for this fixture)
Real en dash is in use — scan of the poppler cache in the real repo:
$ grep -i "APPENDIX [ABC]:" build/pdftext/fy2023.pages.txt
  'APPENDIX A: AGING DISCRETIONARY….PAGE 1 – 27'   <- U+2013 en dash
fy2023.pages.txt: endash_in_toc_appendix_line=1   (all other years: 0)
```

**Suggested fix.** Fix the docstring (the fixture is a hyphen, not an en dash) and add two one-line cases: the real FY2023 line `APPENDIX A: AGING DISCRETIONARY….PAGE 1 – 27` (en dash) and a line where the ellipsis is the only dot run, e.g. `APPENDIX A: AGING DISCRETIONARY…PAGE 1 - 26`.

### `code/test_audit_appendix_overlap.py:27-40 (both ToC tests) — no fixture for FY2015–FY2018`

**Problem.** TOC_APPENDIX returns 0 hits for 4 of the 13 years, and no test uses those years' printed form. This is precisely the failure the test module's docstring warns about — "it silently reports 0 appendices and reads as evidence for subset — a wrong answer that looks like a measurement" — and it is uncaught. FY2016/17/18 print no `PAGE` token; FY2015 prints no hi page. Worse, FY2016/17/18 demonstrably DO restart the appendices at page 1 (1-25, 26-162, 163-212), so BLOCKER 2's claim (1) "ToC gives appendices their own page numbering from FY2019" attributes to the documents what is actually a regex limitation.

**Evidence.**

```
Ran the shipped TOC_APPENDIX against the real poppler cache in the read-only repo:
fy2015.pages.txt  regex_hits=0  raw_toc_lines=3   'APPENDIX B: AGING DISCRETIONARY…..PAGE 1'
fy2016.pages.txt  regex_hits=0  raw_toc_lines=3   'APPENDIX A: AGING DISCRETIONARY……….1-25'
fy2017.pages.txt  regex_hits=0  raw_toc_lines=3   'APPENDIX A: AGING DISCRETIONARY……….1-33'
fy2018.pages.txt  regex_hits=0  raw_toc_lines=3   'Appendix A: Aging Discretionary……….1-33'
fy2019..fy2027    regex_hits=3  (all match)
```

**Suggested fix.** Add fixtures for the FY2016 form (`APPENDIX A: AGING DISCRETIONARY……….1-25`, no PAGE token) and the FY2015 form (no hi page). Either extend the regex to make `page` optional and assert 3 hits with lo==1, or — if the intent is to report those years as unmeasurable — assert that explicitly so 0 hits can never be silently read as evidence for subset.

### `code/audit_appendix_overlap.py:46,177-178 (STREAMS / stream_hits) — no test anywhere in code/test_audit_appendix_overlap.py`

**Problem.** BLOCKER 2's claimed Test 2 — the stream names appear ZERO times in body pages across 13 years — is produced by code with no test at all. It is an absence claim, and a broken search returns exactly the zero that is being published as evidence. Both the search terms and the body page slice can be broken with the suite green.

**Evidence.**

```
A13  STREAMS -> ("ZZZ Nonexistent Stream",)  (always 0 hits)          : {"status":"SURVIVED  <-- test gap","summary":"14 passed in 0.01s"}
A15  body_txt = pages[body_lo - 1:body_hi] -> pages[body_lo:body_hi]   : {"status":"SURVIVED  <-- test gap","summary":"14 passed in 0.01s"}
```

**Suggested fix.** Add a positive control: a fake pages list where one body page DOES contain "Local Initiatives" and assert stream_hits picks it up, plus a page-boundary case that fails under the off-by-one slice. A zero result is only evidence once the search is shown to be capable of returning non-zero.

### `code/audit_appendix_overlap.py:126-137,80-95,112-123,180,229 — no test anywhere in code/test_audit_appendix_overlap.py`

**Problem.** BLOCKER 2's claimed Test 3 — the shortfall arithmetic behind "$5,476,070,836 printed GRAND TOTALs", "68.3%", "appendices cover 98% of a $50,653,587 shortfall", "0.13% residual", "0 of 13 years overshoot" — has zero test coverage at every input. grand_total(), sections(), csv_total()'s exclusion list, apx_lo, and the overshoot comparison itself are all unguarded.

**Evidence.**

```
A12  overshoot `awards+apx > grand_total` -> `< grand_total` (inverted)              : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
A10  grand_total(): `int(m.group(2)...)` -> `int(m.group(1)...)` (wrong column)      : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
A11  sections(): regex made unmatchable (every year silently unauditable)            : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
A9   csv_total(): drop the `if "initiatives" in f or "reconcil" in f: continue` skip : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
A14  apx_lo = min(apx.values()) -> max(apx.values())                                 : {"status":"SURVIVED","summary":"14 passed in 0.01s"}
```

**Suggested fix.** Add pure-function tests with literal fixture text: grand_total() against a two-column `GRAND TOTAL 1,234 5,678 clean` line asserting it returns 5678; sections() against a real `sections: body 1..83 A 84 B 110 C 250` line; csv_total() against a tmp_path tree containing an awards file plus an initiatives and a reconciliation file, asserting the latter two are excluded; and a table-row assertion that awards+appendices > grand_total is reported as an overshoot.

### `code/audit_appendix_overlap.py:150-156 (twins() key function `k`) — no test`

**Problem.** The repo's standing rule is "Join on (EIN, amount), NEVER EIN alone. EIN 13-2612524 carries 229 distinct names." twins() keys on (ein, amount, organization), which satisfies it — but nothing enforces that. The key can be collapsed to EIN alone, silently turning the double-counting bound into a fiscal-sponsor artifact, with the suite fully green.

**Evidence.**

```
A17  `return (re.sub(r"\D","",r.get("ein") or ""), amt, <org canon>)`  ->  `return (re.sub(r"\D","",r.get("ein") or ""),)`  (EIN alone)
  : {"id":"A17","status":"SURVIVED  <-- test gap","failed":[],"summary":"14 passed in 0.01s"}
```

**Suggested fix.** Add a regression test built on the known pathological EIN: two rows sharing EIN 13-2612524 with different amounts and different organizations must NOT be twins. That is the standing rule stated as a test, and A17 fails against it.

### `DATA-ANOMALIES.md:362 (§21 "Not repaired, deliberately")`

**Problem.** Still publishes the withdrawn finding as live: "18 differ by ≤$5 and 3 look like a neighbour's amount." The commit withdraws all 3 `neighbour_bleed` rows as false positives, but DATA-ANOMALIES.md is not in the diff at all. DATA-ANOMALIES.md is the repo's canonical "known limitations" catalog and the file README/DATA-DICTIONARY point readers to.

**Evidence.**

```
`git show --stat ba90fce` lists 10 files; DATA-ANOMALIES.md is not among them. `sed -n '294,400p' DATA-ANOMALIES.md` → "Amounts were audited and not touched. ... 18 differ by ≤$5 and 3 look like a neighbour's amount." vs data/AMOUNT-AUDIT.md:134 "Withdrawn, 2026-08-13. All three are false positives."
```

**Suggested fix.** Amend the §21 bullet to "18 differ by ≤$5; 3 previously flagged as a neighbour's amount were withdrawn 2026-08-13 after PDF verification" and link data/AMOUNT-AUDIT.md#settled-against-the-adopted-pdf.

### `research/phase1-source-comparability/PHASE-0.5-IMPACT.md:63-66`

**Problem.** Carries the OLD position in the strongest possible form, and specifically pre-rebuts the exact evidence DATA-DICTIONARY now leads with: "Do not add the AFTER dollar column to a printed Schedule C grand total. FY2027 happens to land within $854,587 of its printed $655,764,999 grand total, and that is a coincidence, not a reconciliation — FY2023's $312,208,214 sits nowhere near its $486,446,095. Anyone tempted by the FY2027 near-miss should look at FY2023 first." The commit's TEST 3 / FY2027 discriminator is precisely that near-miss. Doc is `status: complete`, not marked historical, and was not touched by this commit.

**Evidence.**

```
sed -n '55,70p' research/phase1-source-comparability/PHASE-0.5-IMPACT.md; frontmatter `status: complete`. Script output confirms both figures: FY2027 shortfall 50,653,587 vs appendices 49,799,000 (residual 854,587); FY2023 shortfall 224,026,881 vs appendices 49,789,000 (22%).
```

**Suggested fix.** Add a dated superseded note at PHASE-0.5-IMPACT.md:63 pointing at DATA-DICTIONARY's corrected section, or state why the FY2023 counter-case does not defeat the FY2027 argument.

### `DATA-DICTIONARY.md:69 and commit message ("FY2027 discriminates, being the only year that reconciles 25/25 categories exactly")`

**Problem.** The uniqueness claim that carries the whole FY2027 discriminator is false. FY2027 is not the only fully-reconciling year: FY2023 reconciles 26/26 categories exactly and FY2015 24/24 reconcilable categories exactly, both inside the award range. Under the doc's own logic FY2023 should behave like FY2027 — it does not (appendices cover 22% of a $224M shortfall, not 98%), which is exactly the counter-case PHASE-0.5-IMPACT.md flags. The phrasing survives only on the literal reading "the only year with 25 categories".

**Evidence.**

```
`grep -n "GRAND TOTAL" data/fy23/.../fy23_schedule_c_reconciliation.txt` → "486,446,095  486,446,095  26/26 categories exact"; fy15 → "24/24 reconcilable categories exact"; fy27 → "25/25 categories exact". Per-year sweep: fy10 21/21, fy12 16/16, fy13 17/17, fy14 17/17, fy23 26/26 also exact.
```

**Suggested fix.** Restate as "one of two years in the award range that reconcile every category exactly" and address FY2023 head-on, since a fully-reconciled year whose shortfall is 4.5x its appendix total is the strongest available objection.

### `mcp/CHANGELOG.md:89-96 (1.4.0 — 2026-08-12, "Known limits")`

**Problem.** The unreleased 1.4.0 changelog — the release this commit exists to unblock — still quotes the deleted README sentence as current repo state and defers the decision: "The repo README describes these files as 'subsets of the main body ... do not add them to the Schedule C total.' ... Reconciling that README sentence with this finding is Phase 1 work, not this release." That sentence no longer exists and the reconciliation shipped in this commit. It also asserts the old warning "is correct about the printed *category* totals" — a distinction the corrected README/DATA-DICTIONARY do not make, so the two now disagree about what "the Schedule C total" means.

**Evidence.**

```
sed -n '85,96p' mcp/CHANGELOG.md; mcp/package.json version 1.4.0; commit message "Issue #57 held the mcp-v1.4.0 tag". README.md:95 now reads "additional to the main body".
```

**Suggested fix.** Amend the 1.4.0 entry (it is unreleased) to record the 2026-08-13 resolution and drop the "Phase 1 work, not this release" deferral, or move the note to an Unreleased/1.4.0 addendum.

### `DATA-DICTIONARY.md:68 and commit message ("the stream names appear zero times in the body across 13 years")`

**Problem.** Two defects in one published test. (a) The bolded claim "appear **zero** times across the body pages of all 13 years" is contradicted by the script's own output (FY2026 = 1) and by the doc's own next sentence; the commit message states it flat with no caveat at all. (b) STREAMS is hardcoded to ("Aging Discretionary","Local Initiative","Youth Discretionary") but the documents name the streams differently in 4 of the 13 years: FY2019/FY2020 Appendix C is "YOUTH INITIATIVES", FY2021/FY2022 Appendix B is "Local Discretionary". Those years were never searched under the name the document itself prints, so "zero across 13 years" overstates the coverage of the test.

**Evidence.**

```
`.venv/bin/python code/audit_appendix_overlap.py` TEST 2 column → FY2026 = 1, all others 0. ToC scrape: FY2019 [('A','AGING DISCRETIONARY'),('B','LOCAL INITIATIVES'),('C','YOUTH INITIATIVES')]; FY2021/FY2022 [('B','Local Discretionary')]. code/audit_appendix_overlap.py:41 STREAMS = ("Aging Discretionary", "Local Initiative", "Youth Discretionary").
```

**Suggested fix.** State the result as "zero in 12 of 13 years; one FY2026 prose hit", and derive STREAMS per year from each document's own ToC rather than hardcoding one naming.

### `DATA-DICTIONARY.md:63 and README.md:95`

**Problem.** The correction is unqualified about which total: "Adding them to the Schedule C total is correct." In DATA-DICTIONARY the immediately preceding section defines `{year}_schedule_c_initiatives.csv` as "Authoritative category/initiative totals ... sums exactly to each category's printed TOTAL" — and that file already sums to $5,474,660,271, i.e. essentially the full printed grand total, so the appendix dollars are already inside it. A reader following the corrected sentence one section later double-counts $353M. mcp/CHANGELOG.md:91 already draws exactly this award-vs-category distinction; the correction does not.

**Evidence.**

```
DATA-DICTIONARY.md:47-63 (initiatives section immediately precedes appendix section). Recomputed: sum of data/fy{15..27}/schedule_c/*_schedule_c_initiatives.csv = $5,474,660,271 vs printed GRAND TOTALs $5,476,070,836 (0.0258% below). Appendix dollars $352,997,275 are inside that.
```

**Suggested fix.** Change both to "additional to the **award body**; adding them to the Schedule C **award** total is correct — do NOT add them to the category/initiative totals, which already contain them."

### `DATA-DICTIONARY.md:72 — "against the Council's own printed grand totals of $5,476,070,836"; also DATA-DICTIONARY.md:70 ("the Council's printed GRAND TOTAL"), code/audit_appendix_overlap.py:26 ("The document prints a GRAND TOTAL and the parser reconciles it"), code/audit_appendix_overlap.py:129 (grand_total() docstring: "The GRAND TOTAL the document itself prints"), commit message ("the printed grand totals ($3.74B of $5.48B)")`

**Problem.** The Schedule C PDFs print no grand total. $5,476,070,836 is a parser-derived sum of the per-category printed TOTAL lines, computed inside parse_schedule_c.py and written into the reconciliation .txt as a synthesized 'GRAND TOTAL' row. Describing it as a figure the Council printed makes Test 3 and the 68.3% claim look like a comparison against an authoritative published number when it is a comparison against our own arithmetic on 25-28 extracted subtotals per year.

**Evidence.**

```
$ for n in "655,764,999" "471,875,565" "486,446,095" "665,080,021"; do grep -rl "$n" /tmp/audit57/txt/ || echo "NOT FOUND"; done
  NOT FOUND in any extracted PDF text  (x4; /tmp/audit57/txt holds my own `pdftotext -layout` of all 13 PDFs, byte-identical to build/pdftext)
$ grep -n -B5 'GRAND TOTAL' code/parse_schedule_c.py
  362-        i=isum.get(c,0); p=recon.get(c) or 0; gi+=i; gp+=p
  365:    L.append(f"{'GRAND TOTAL':52} {gi:>14,} {gp:>14,}  {ok}/{len(cats)} categories exact")
  # recon[cat] is set at line 165 from each block's printed "TOTAL $X" line; gp is their running sum
$ grep -n -i 'grand total' /tmp/audit57/txt/fy2027.pages.txt  ->  no match (only per-category 'TOTAL $x' lines)
```

**Suggested fix.** Rename throughout to 'the sum of the Council's printed category TOTALs' (or 'derived grand total'). Fix the two false statements in audit_appendix_overlap.py's module and grand_total() docstrings, which assert the document prints it.

### `DATA-DICTIONARY.md:70 — "In FY2027 — the one year the parser reconciles 25/25 categories exactly"; commit message — "FY2027 discriminates, being the only year that reconciles 25/25 categories exactly"`

**Problem.** FY2027 is not the only fully-reconciled year. FY2023 reconciles 26 of 26 categories exactly and is also an award year with appendix rows — and it does not support the argument: its appendices cover 22.2% of its shortfall, not 98%. The discriminating year was selected from a set of two, and the one that agrees was published while the one that disagrees was not mentioned.

**Evidence.**

```
$ grep -h 'GRAND TOTAL' data/fy23/schedule_c/fy23_schedule_c_reconciliation.txt
  GRAND TOTAL   486,446,095   486,446,095  26/26 categories exact
$ .venv/bin/python /tmp/audit57/recompute.py   (independent re-sum of the CSVs)
  fy23  awards $262,419,214  appendix $49,789,000  printed_GT $486,446,095
  shortfall = 486,446,095 - 262,419,214 = 224,026,881 ; 49,789,000 / 224,026,881 = 22.2%
(also fully exact, non-award years: fy10 21/21, fy12 16/16, fy13 17/17, fy14 17/17)
```

**Suggested fix.** Say 'one of the two years that reconcile every category exactly' and state FY2023's 22% alongside FY2027's 98%, with the reason they differ (FY2023 loses far more award detail), or drop the 'only year' framing entirely.

### `DATA-DICTIONARY.md:67 — "From FY2019 the table of contents gives each appendix its own page numbering, restarting at page 1"; commit message — "the ToC gives each appendix its own page numbering from FY2019"`

**Problem.** Wrong on both halves. (a) The FY2019 boundary is an artifact of the TOC_APPENDIX regex, which requires the literal token 'page' before the range; FY2016, FY2017 and FY2018 print the same restart-at-1 appendix pagination without the word 'PAGE', and FY2015 prints a single start page. All 13 years give the appendices their own numbering. (b) Only Appendix A restarts at 1 — B and C continue the same sequence — so 'each appendix its own page numbering' is false. The commit's own new test asserts exactly this, so the doc contradicts the test shipped beside it.

**Evidence.**

```
$ python - (my own pdftotext -layout, ToC pages 1-6)
  FY2015 'APPENDIX B: AGING DISCRETIONARY…..PAGE 1'
  FY2016 'APPENDIX A: AGING DISCRETIONARY……….1-25'  'APPENDIX B: LOCAL INITIATIVES……….26-162'
  FY2017 'APPENDIX A: AGING DISCRETIONARY……….1-33'
  FY2018 'Appendix A: Aging Discretionary……….1-33'  'Appendix B: Local Initiatives……….34-178'
  FY2024 'APPENDIX A: AGING DISCRETIONARY….PAGE 1 - 26'  'APPENDIX B: LOCAL INITIATIVES….PAGE 27 - 147'  'APPENDIX C: YOUTH DISCRETIONARY….PAGE 148 - 189'
$ .venv/bin/python code/audit_appendix_overlap.py  -> 'restart at p1' column = 1 for every year 2019-2027 (one of three, not three)
code/test_audit_appendix_overlap.py:34 — 'assert sum(1 for _, _, lo, _ in hits if int(lo) == 1) == 1' with comment '# Only Appendix A restarts at 1'
```

**Suggested fix.** Rewrite as: 'In every year FY2015-FY2027 the ToC pages the appendices as their own block, restarting at page 1 (Appendix A), with B and C continuing that sequence.' Loosen TOC_APPENDIX to make 'page' optional so the audit stops reporting 0 for FY2015-FY2018.

### `code/PARSING.md:406 — "apparent duplicates being round-number coincidences worth at most $447,500 corpus-wide"; commit message — "the apparent duplicates are round-number coincidences worth at most $447,500 corpus-wide (0.012%)"`

**Problem.** $447,500 is the upper bound after excluding every round-thousand twin — it is not the upper bound on double-counting. The actual (EIN, amount, organization) twin population across 13 years is 4,654 rows / $46,034,500, which is 1.23% of the headline, 103x the published bound. DATA-DICTIONARY.md carries the hedge ('Restricting to distinctive (non-round-thousand) amounts…'); PARSING.md and the commit message drop it, so the reader of either gets a number that means something different from what it says.

**Evidence.**

```
$ .venv/bin/python /tmp/audit57/twins.py
  FY2021 twins 310 $1,755,000 | FY2022 380 $2,252,500 | FY2023 359 $3,071,000 | FY2024 870 $9,126,000
  FY2025 902 $9,785,500 | FY2026 880 $9,253,500 | FY2027 953 $10,791,000 | FY2018 0 $0
  TOTAL apx rows 28,575  twins3 4,654 ($46,034,500)  distinctive 109 ($447,500)
  twin3 total as % of headline: 1.2303%   (447500/3741615569 = 0.01196% -> the published 0.012% is correct for the distinctive subset)
```

**Suggested fix.** In PARSING.md and any future summary, carry the qualifier: 'at most $447,500 once round-thousand coincidences are excluded; the unfiltered twin population is $46.0M (1.2%).'

### `data/AMOUNT-AUDIT.md — control table rows "amounts rotated within the fiscal year | 11.0% still confirmed" and "a different EIN's real amount planted on each row | 5.0% still confirmed"`

**Problem.** Neither figure is reproducible. The controls exist only as prose — they are in no script and in no test (code/test_verify_amounts_against_pdf.py encodes the mechanism test but not the four table rows), so there is no definition of 'rotated' or 'different EIN's real amount' to re-run. My reconstructions under every reasonable reading land far from 5.0%, and reach 11.0% only under one specific reading out of several. A number published as a measurement should be re-derivable from the repo.

**Evidence.**

```
$ .venv/bin/python /tmp/audit57/controls.py  (calls V.verify() from the shipped module on the same 440 findings rows)
  BASELINE                                    confirms 399 (90.7%)  weak 41 (9.3%)
  CONTROL +$7                                 confirms 0            contradicts 440   <- reproduces
  CONTROL planted-absent 987654321            confirms 0            contradicts 440   <- reproduces
  CONTROL rotate within fiscal year (shift 1) confirms 143 (32.5%)  weak 23 (5.2%)
  CONTROL different-EIN real amount           confirms 116 (26.4%)  weak 18 (4.1%)
$ .venv/bin/python /tmp/audit57/controls2.py  (shuffle within FY, seeds 0-7)  confirms 21.4%-25.5%
  (global shuffle, seeds 0-4)                                                 confirms 14.1%-16.4%
$ .venv/bin/python /tmp/audit57/controls3.py  (neighbour-row bleed simulation)
  NEIGHBOUR-ROW amount                        confirms 133 (30.2%)
  ... restricted to rows whose amount actually changed  confirms 34 (10.5%)  c+w 13.6%   <- nearest match to 11.0% / 14.1%
$ .venv/bin/python /tmp/audit57/controls4.py  (different-EIN real amount, seeds 0-5)  confirms 14.8%-18.4%, never near 5.0%
```

**Suggested fix.** Add the four controls to code/test_verify_amounts_against_pdf.py (or a --controls flag) so the percentages are generated, not asserted. Until then, state the exact rotation/planting rule and denominator next to each number.

### `code/verify_amounts_against_pdf.py:79 — `MONEY = re.compile(r"\$\s?([\d,]+)")``

**Problem.** The money regex requires a literal `$`. FY2015 through FY2020 print award amounts with no `$` at all. Across those six years 28,099 EIN-bearing lines carry a comma-formatted amount that `amounts_on()` cannot see — 87.4% of FY2015's EIN lines, 87.2% FY2016, 79.8% FY2017, 75.5% FY2018, 84.0% FY2019, 63.1% FY2020. Two consequences. (1) `pdf_contradicts` rows in those years publish `pdf_amounts=""` — the artifact tells a human "the EIN is printed and no line under it carries our amount, and the amounts we did see are: none", which is false; the amounts are printed, the reader is blind to them. (2) 63 corpus rows verified where the row's OWN printed line (same council member, same amount) is invisible and the script therefore "confirms" off a different printed line. The check's power is structurally different in 6 of 13 years, so the headline "0 pdf_contradicts" is partly a measurement artifact rather than a result.

**Evidence.**

```
/tmp/p_nodollar2.py → `FY EIN lines / MONEY sees $ / blind (bare amt, no $)`: 2015 5254/655/4590 (87.4%), 2016 5515/646/4809 (87.2%), 2017 5220/1048/4164 (79.8%), 2018 5933/1421/4482 (75.5%), 2019 6023/934/5059 (84.0%), 2020 7918/2893/4995 (63.1%), 2021-2027 all 0.0% blind. Real blind line, FY2015: `Kallos  92nd Street Y ...  131624229 *  14,500 Funds will be us…`. False-contradict reproduced in a 750-row true-row sample: `FY2015 pdf_contradicts org="St. Luke's-Roosevelt Crime Victims Treat" ours=$75000 pdf_saw=` (empty) and `FY2016 pdf_contradicts org='Citizens Care Committee' ours=$40000 pdf_saw=` (empty). /tmp/p_falsepin2.py → 63 rows, e.g. `FY2015 fy15_schedule_c_awards.csv:19 member='Chin' $5,000 / OUR printed row line 5465: Chin Asian Americans for Equality 133187792 * 5,000 readiness. / script confirmed line 496: Chin Asian Americans for Equality 13-3187792 $5,000`.
```

**Suggested fix.** Make the amount pattern `\$?\s{0,2}(\d{1,3}(?:,\d{3})+|\d+)` with a guard that it is not part of an EIN or a longer digit run, and re-run. Until then, no `pdf_contradicts` verdict for FY2015-FY2020 is trustworthy and `pdf_amounts` must not be published as "the amounts printed under this EIN".

### `code/verify_amounts_against_pdf.py:153 — `named = next(((n, t) for n, t in carrying if names_us(t, r["organization"])), None)``

**Problem.** `next()` takes the first line that carries both our name and our amount and never checks whether that match is unique. 17 of the 399 `pdf_confirms` have 2 or 3 distinct printed lines that each name us AND carry our amount; the row is still published as `pdf_confirms` with a single `pdf_line`, i.e. a specific printed row is asserted when the evidence names two or three. This is the repo's standing rule "Nothing applies on a non-unique match" — the script applies no data, but it publishes a pinned line number and a settled verdict off a non-unique match, and that verdict is what reverses two previously published findings.

**Evidence.**

```
/tmp/p_pin2.py → `pdf_confirms pinned by NAME: how many printed lines carry BOTH our name and our amount?  1 line(s): 298 rows / 2 line(s): 11 rows / 3 line(s): 6 rows` → 17 of 399 non-unique. Concrete: `FY2021 fy21:2538 $5000 org='Shetu, Inc.'` matches `line 13746: Dromm Shetu, Inc. 453818185 $5,000 DYCD materials and supplies.` AND `line 13748: Lander Shetu, Inc. 453818185 $5,000 DYCD engagement services…` — two different council members' awards; the script publishes line 13746. Same for `FY2020 fy20:2306` and `fy20:2504`, both $20,000 JSPOA, both pinned to line 7911 while line 8251 is an equally good match.
```

**Suggested fix.** Compute the full list of name+amount matches; if `len(named) > 1`, downgrade to `pdf_confirms_weak` and emit every candidate line number in `pdf_line`. Never publish a single line number for a match that is not unique.

### `code/verify_amounts_against_pdf.py:155 — the `or len(hits) == 1` branch`

**Problem.** The organization name is used only to PROMOTE a row to `pdf_confirms`, never to DEMOTE one. When an EIN has exactly one printed line all year, the row confirms regardless of whether that line names our organization — and a name mismatch on the only candidate line is evidence AGAINST the row, not neutral. 84 of the 399 confirms (21%) sit on a line whose printed organization does not match our `organization` field, and the script discards that signal silently. In several the two organizations are plainly different entities.

**Evidence.**

```
/tmp/p_pin2.py → `pdf_confirms pinned ONLY by 'sole line in the year' (name did NOT match): 84`. Examples: `FY2017 fy17:163 ours=$29730 / our org : 'Good Old Lower East Side, Inc. 13-3311582 * $29,729 Gowanus Canal Community Development ' / pdf line: Greater Ridgewood Restoration Corporation 11-2498292 $29,730`; `FY2015 fy15:572 ours=$32000 / our org: 'Neighborhood Self Help by Older Persons Project, Inc.' / pdf line: Lafayette/Boyton Lafayette NORC 13-3077049 $32,000`; `FY2018 fy18:433 ours=$110000 / our org: 'Homeless Edward J. Malloy Initiative for Construction Skills' / pdf line: Edward J. Malloy Initiative for Construction Skills 13-4147836 $110,000`.
```

**Suggested fix.** Add a fourth verdict, e.g. `pdf_name_mismatch`, for the case where the sole (or chosen) line carries our EIN and our amount but does not name our organization. Those 84 rows are exactly the ones a human should look at, and today they are the ones marked settled.

### `code/verify_amounts_against_pdf.py:121 — `c = canon(org)[:18]` (docstring lines 118-119)`

**Problem.** The justification "18 canonical characters is long enough that a collision would have to be a near-identical name" is false as written. `[:18]` is a prefix of AT MOST 18 characters: 757 distinct organization strings in this corpus canonicalize to fewer than 18 characters, so their key is the whole (short) name. 44 of the 399 confirms are pinned by a key shorter than 18 chars, including `fjc` (3), `drum` (4), `enact` (5), `bkrams`/`strive` (6), `gemsinc`/`helppsi` (7), `shetuinc` (8). `canon()` strips whitespace, so `"enact" in canon(line)` matches any line containing "…to enact…". Separately, 777 distinct 18-char prefixes are shared by more than one organization, and they are not near-identical names. And even at full length the key frequently pins nothing: 138 of the 315 name-pinned confirms use a key that matches more than one line of that year's PDF (26 of them match 11-100 lines).

**Evidence.**

```
/tmp/p_names.py → `distinct organization strings: 6076` / `prefixes shared by >1 distinct org name: 777` / `orgs whose ENTIRE canonical name is <18 chars: 757 across 729 keys`. Shortest keys in use: `'hh'` (H+H), `'fjc'`, `'naf'`, `'wnet'`, `'drum'`, `'park'`, `'enact'`, `'dorot'`, `'hanac'`. Genuine collisions: `'brooklyncommunityb' -> ['Brooklyn Community Bail Fund, Inc.', 'Brooklyn Community Board #10', 'Brooklyn Community Board #12', 'Brooklyn Community Board #13']`; `'manhattancommunity' -> ['Manhattan Community Access Corporation', 'Manhattan Community Board #1', 'Manhattan Community Board #10', ...]`. /tmp/p_pin.py → `Of the 315 pinned by name … 1 (unique) 177 / 2-10 112 / 11-100 26`; worst: `FY2027 key matches 37 lines keylen=18 org='Selfhelp Community Services, Inc.' $44999`, `FY2019 key matches 19 lines keylen=6 org='STRIVE' $100000`; `confirms pinned by a name key SHORTER than the claimed 18 chars: 44`.
```

**Suggested fix.** Require a minimum key length (reject names whose canonical form is under ~12 chars from pinning at all) and require the key to match exactly one line in that year's text before it may promote. Fix the docstring: it describes a fixed-width 18-char key, the code implements a variable-length prefix of up to 18.

### `code/verify_amounts_against_pdf.py:89 — `if not os.path.exists(txt):``

**Problem.** The poppler cache is keyed on the fiscal year alone (`fy{fy}.layout.txt`) and is never validated against the source PDF. If a PDF changes, or the `PDFS` mapping is repointed at a different document for the same year, the stale text is reused silently and the verdicts are produced against a document that is no longer the one the script claims to be reading. Separately, `subprocess.run` writes straight to the final cache path with no temp-file-and-rename, so an interrupted or failed extraction leaves a partial file that every later run trusts as complete. The docstring's justification ("Cached; the PDFs do not change") is a promise about the inputs, not a check on them.

**Evidence.**

```
/tmp/p_cache.py (CACHE redirected to a temp dir, no repo file touched) → `FY2027 first extraction, lines: 26909` … after `V.PDFS[2027]="source/FY26/Fiscal-2026-Schedule-C-4.pdf"` → `after repointing PDFS[2027] to the FY2026 PDF, lines: 26909` / `SAME TEXT RETURNED (stale cache silently used): True`. Truncation: writing `truncated\n` into `fy2026.layout.txt` → `hand-truncated fy2026 cache is used as-is: ['truncated']`.
```

**Suggested fix.** Name the cache after a hash of the source PDF bytes (`fy{fy}.{sha256[:12]}.layout.txt`), or store the source path plus mtime/size alongside and re-extract on mismatch. Write to `txt + '.tmp'` and `os.replace()` on success so a failed run cannot leave a trusted partial.

### `code/test_verify_amounts_against_pdf.py:42 — `V.pdf_lines = lambda fy: page``

**Problem.** Every test monkeypatches `pdf_lines` away and runs `verify()` against a four-line synthetic page (lines 31-36) in which every amount carries a `$` and every line holds exactly one printed row. So `MONEY`, `ein_index`, the poppler cache and the real quirks of `-layout` are entirely untested. The test file's own docstring calls the first case "the mechanism test — if it ever fails, every other result in the file is meaningless", and the commit message calls the controls the reason to believe the result; but the mechanism test is run against a page written to match the author's assumption about the format. That is exactly why the FY2015-FY2020 `$`-less format went unnoticed: a fixture in that format would have made `test_amount_absent_from_the_ein_never_confirms` pass for the wrong reason and `test_single_line_ein_confirms` fail.

**Evidence.**

```
`grep -n "names_us|MONEY|pdf_lines" code/test_verify_amounts_against_pdf.py` returns only lines 41/42/46 — the monkeypatch. `PAGE` (lines 31-36) is four lines, all with `$`. `.venv/bin/pytest code/test_verify_amounts_against_pdf.py -q` → `7 passed in 0.01s` — 0.01s confirms no PDF is read. Meanwhile the real FY2016 text is 87.2% `$`-free on EIN-bearing lines (/tmp/p_nodollar2.py).
```

**Suggested fix.** Add at least one test that runs the real `pdf_lines`/`ein_index`/`amounts_on` against a checked-in 20-line excerpt of the actual FY2016 and FY2021 layout text (both formats), asserting the FY2016 award amount is found. That single test fails today.

### `data/AMOUNT-AUDIT.md "### The 18 `rounding` rows: the PDF backs our figure, not the disclosure's" and commit message "On all 18 `rounding` rows the PDF backs our figure … including fy17:209, the worked example in DATA-ANOMALIES sec.20"`

**Problem.** The flagship rounding example is not confirmed by the script. fy17:209 comes back `pdf_confirms_weak`, which this script's own docstring (line 37-38) defines as "Corroborated but not pinned; a person should look". 5 of the 18 rounding rows are weak, not 0. More importantly the row's `organization` field is itself merged parser garbage (`'Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services'`), i.e. the defect is a ROW-BOUNDARY merge across printed lines 4526/4527. A check that asks "is our amount on the same text line as our EIN" cannot see a row-boundary defect: both pypdf and poppler read the same glyphs off the same line, so their agreement is guaranteed whether or not the parser assigned the row correctly. The "two engines, two text models, same bytes" independence argument (docstring lines 15-20) establishes glyph fidelity, which was never in doubt, not row attribution, which is the documented defect class (§20/§21).

**Evidence.**

```
Script stdout: `[pdf_confirms_weak] fy17:209 'Bronx Defenders 13-3931074 * $2,07' ours=$2,076,666  pdf=2076666`. Verification CSV row: `pdf_confirms_weak | fy17:209 | ein 113305406 | ours 2076666 | disclosure 2076667 | einlines 10 / org= 'Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services'`. `grep -n "2,076,66" build/pdftext/fy2017.layout.txt` → `4526: Bronx Defenders 13-3931074 * $2,076,667` / `4527: Brooklyn Defenders Services 11-3305406 $2,076,666` / `4528: Legal Aid Society 13-5562265 $2,076,666` — three adjacent rows, two carrying the same figure. Rounding-row tally from the artifact: 13 `pdf_confirms`, 5 `pdf_confirms_weak`.
```

**Suggested fix.** State in AMOUNT-AUDIT.md and in the commit narrative that 5 of the 18 rounding rows including fy17:209 are `pdf_confirms_weak`, and that a same-line (EIN, amount) co-occurrence check is structurally incapable of detecting the org_merged row-boundary defect that produced that row. The $1 conclusion may still be right; the evidence offered does not reach it.

### `data/AMOUNT-AUDIT.md:169 ("That ambiguity ... is the whole content of the 41 `pdf_confirms_weak`") — evidence class spans 7 rows of data/AMOUNT-PDF-VERIFICATION.csv`

**Problem.** 7 of the 440 rows carry, verbatim inside their own `organization` text, a second award (EIN + dollar figure) that is absent from the corpus entirely — 8 lost awards totalling $2,280,315. The commit's evidence exposes this and its summary suppresses it: the confirming PDF line proves the boundary loss, yet the row is counted in the 'corroborated' column and the missing sibling is never reported.

**Evidence.**

```
Regex (\d{2}-\d{7})\s*\*?\s*\$([\d,]+) over the `organization` field of the 440 rows, then lookup of (fy, ein, amount) across every data/fy*/schedule_c/*.csv award file:
  FY2016 fy16:74  (pdf_confirms_weak) swallowed 13-2851988 $29,730 -> NOT in corpus (no row at all under that EIN in FY2016)
  FY2016 fy16:75  (pdf_confirms_weak) swallowed 13-3248777 $29,730 -> NOT in corpus
  FY2016 fy16:94  (pdf_confirms_weak) swallowed 13-1943516 $29,730 -> NOT in corpus
  FY2017 fy17:163 (pdf_confirms)      swallowed 13-3311582 $29,729 -> NOT in corpus
  FY2017 fy17:163 (pdf_confirms)      swallowed 13-2915659 $29,729 -> NOT in corpus
  FY2017 fy17:209 (pdf_confirms_weak) swallowed 13-3931074 $2,076,667 -> NOT in corpus
  FY2019 fy19:166 (pdf_confirms_weak) swallowed 81-5080860 $45,000 -> NOT in corpus
  FY2019 fy19:304 (pdf_confirms)      swallowed 11-2074467 $10,000 -> NOT in corpus
Sum = $2,280,315. Each is printed intact in the PDF one line above the confirming line, e.g. /tmp/audit440/fy2017.layout.txt L4615 'Bronx Defenders 13-3931074 * $2,076,667' immediately above the confirmed L4616 'Brooklyn Defenders Services 11-3305406 $2,076,666'.
```

**Suggested fix.** Emit the swallowed (EIN, amount) pairs as their own output column and cross-check them against the corpus; report the count and dollars of provably-lost awards alongside the confirmation tally in AMOUNT-AUDIT.md, so the section does not read as 'settled'.

### `data/AMOUNT-AUDIT.md:173-183 (control table: "every amount corrupted by +$7 | 440/440 pdf_contradicts", "amounts rotated within the fiscal year | 11.0% still confirmed", "a different EIN's real amount planted on each row | 5.0% still confirmed") with "Tests: code/test_verify_amounts_against_pdf.py" at :185`

**Problem.** None of the four published control results is implemented anywhere in the commit. The test file directly cited beneath the table contains seven unit tests over a hard-coded four-line synthetic page and computes no corpus-wide percentage. The 11.0% and 5.0% figures — and the 14.1% in code/verify_amounts_against_pdf.py:26 — are unreproducible published numbers, in a commit whose whole argument is 'the check was measured before it was believed'.

**Evidence.**

```
`git show --stat ba90fce` adds exactly two code files: code/verify_amounts_against_pdf.py, code/audit_appendix_overlap.py (plus their tests). `grep -rn "rotat|planted|11.0%|5.0%|control" code/test_verify_amounts_against_pdf.py code/verify_amounts_against_pdf.py` returns one hit, a prose mention at verify_amounts_against_pdf.py:25. code/test_verify_amounts_against_pdf.py PAGE is a 4-line literal; `.venv/bin/pytest code/test_verify_amounts_against_pdf.py -q` -> "7 passed in 0.01s". No script in the repo produces 11.0% or 5.0%.
```

**Suggested fix.** Ship the control harness (a --control {plus7,planted,rotate,cross-ein} flag or a separate read-only script) so the four numbers can be regenerated, or delete the table and state the controls were run ad hoc and are not reproducible.

### `code/verify_amounts_against_pdf.py:155 (`pinned = named is not None or len(hits) == 1`) and data/AMOUNT-AUDIT.md:146 (pdf_confirms = "...so the evidence points at one printed row, not at an EIN's whole block")`

**Problem.** 17 of the 399 pdf_confirms rows do not meet the published definition: more than one printed line carries the EIN, our amount AND our organization name, so the evidence points at 2-3 printed rows, not one. The script takes the first match without checking uniqueness, so the pdf_confirms / pdf_confirms_weak boundary does not mean what both the script docstring and AMOUNT-AUDIT.md say it means.

**Evidence.**

```
Re-running the script's own predicate over /tmp/audit440/*.layout.txt and counting matches instead of taking the first:
  pdf_confirms rows whose pin matches MORE THAN ONE printed line: 17
  e.g. FY2024 fy24:2941 ein=132725423 $40,000 ein_lines=18 carrying=3 named=3 'Wildcat Service Corporation'
       FY2024 fy24:2945 ein=132725423 $40,000 ein_lines=18 carrying=3 named=3
       FY2024 fy24:4231 ein=132725423 $40,000 ein_lines=18 carrying=3 named=3
       FY2023 fy23:582/583/1964 ein=132949483 $5,000 ein_lines=5 carrying=3 named=3 'New York Road Runners, Inc.'
       FY2021 fy21:399/400/1258 ein=135562162 $5,000 ein_lines=6 carrying=3 named=2 'Helen Keller International, Inc.'
       FY2020 fy20:2306/2504 ein=510204121 $20,000 ein_lines=10 carrying=2 named=2 'Jamaica Service Program for Older Adults (JSPOA), Inc.'
```

**Suggested fix.** Set pinned = (len(named_matches) == 1) or (len(hits) == 1); route the 17 non-unique pins to pdf_confirms_weak, and correct the headline split (which becomes 382 / 58, not 399 / 41).

### `code/verify_amounts_against_pdf.py:5-6 ("leaves 440 rows unresolved") and data/AMOUNT-AUDIT.md:20 ("The 440 rows this audit left unresolved are now settled"), :143 ("The 440 rows the disclosure could not corroborate")`

**Problem.** "The rows the disclosure could not corroborate" is 1,548, not 440. The script filters to three verdicts and silently omits the largest non-corroborated class — 1,102 rows with verdict `unconfirmed`, where the Council's disclosure DOES hold the EIN and records a different amount. That is a stronger disagreement than `ein_absent` (the disclosure is silent), yet only the weaker class is put to the PDF. The framing invites the reader to conclude the residue is settled when 71% of it was never tested.

**Evidence.**

```
collections.Counter over data/AMOUNT-AUDIT-findings.csv 'verdict': {'unconfirmed': 1102, 'ein_absent': 419, 'rounding': 18, 'no_key': 6, 'neighbour_bleed': 3} — 1,548 rows total. code/verify_amounts_against_pdf.py:44 TARGET_VERDICTS = ("ein_absent", "rounding", "neighbour_bleed") = 440. code/audit_amounts.py:classify returns 'unconfirmed' only when `ein in year.by_ein` but the amount is absent from every figure the Council records under that EIN.
```

**Suggested fix.** Reword to "the 440 rows the disclosure has no figure for" and state the 1,102 `unconfirmed` rows explicitly as out of scope with their dollar total, or extend the PDF check to them — they are the rows where a printed-vs-disclosed conflict would actually be informative.


## MINOR

### `data/AMOUNT-PDF-VERIFICATION.csv, column `pdf_amounts`, all 440 rows; written at code/verify_amounts_against_pdf.py:157 `pdf_amounts=ours``

**Problem.** On confirm verdicts the script writes back the row's OWN amount, not what it read out of the PDF. Since the file contains zero `pdf_contradicts` rows (the only verdict where the column holds independent content), `pdf_amounts` equals `our_amount` in 440 of 440 rows. Side by side in a spreadsheet this reads as two witnesses agreeing; it is one value printed twice. The actual PDF evidence is entirely in `pdf_text`.

**Evidence.**

```
$ .venv/bin/python -c "import csv;rows=list(csv.DictReader(open('data/AMOUNT-PDF-VERIFICATION.csv')));print(all(r['pdf_amounts']==str(int(float(r['our_amount']))) for r in rows))"
True
(and pdf_verdict tally: pdf_confirms 399, pdf_confirms_weak 41, pdf_contradicts 0)
```

**Suggested fix.** Either write the full set of amounts found on the cited line (`;`-joined, same shape the contradicts branch already uses), or drop the column from confirm rows and leave it empty. Writing the input back as if it were the output is the shape of a self-confirming check even where, as here, the real evidence is sound.

### `data/AMOUNT-PDF-VERIFICATION.csv — header, no `pdf_page` column`

**Problem.** The artifact's positional pointer resolves only inside `build/pdftext/fy20NN.layout.txt`, which is gitignored (added in this same commit) and must be locally regenerated. There is no page number, so a reader holding the published PDF in `source/` has no way to reach the printed page short of re-deriving the dump. Combined with the pdf_line defect above, the provenance is effectively unfollowable by anyone who does not re-run the script.

**Evidence.**

```
Header: file,line,fiscal_year,ein,organization,our_amount,verdict,nearest_disclosure_amount,delta,belongs_to_ein,org_text_merged,pdf_verdict,pdf_line,pdf_amounts,pdf_ein_lines,pdf_text
.gitignore diff in ba90fce adds: build/pdftext/
form feeds in fy2015 dump = 292, i.e. the page index is already present in the text and is simply not recorded.
```

**Suggested fix.** Emit `pdf_page` alongside `pdf_line` — one running counter over \x0c in `pdf_lines()`. That makes each row checkable against the shipped PDF directly, which is what the commit claims the check delivers.

### `DATA-DICTIONARY.md:72 (one capture percentage published, with no row-capture companion)`

**Problem.** Publishing a single capture figure violates the repo's own published rule, and it reaches for a novel denominator when a same-universe one already exists and is already published per-year. DATA-ANOMALIES.md §20 (unchanged by this commit): 'row capture and dollar capture differ by up to a factor of five ... Always publish both numbers and name what each measures.' The 68.3% is a dollar-capture figure with no row companion and no stated universe.

**Evidence.**

```
DATA-ANOMALIES.md §20 'Caution for anyone quoting a completeness figure': 'Always publish both numbers and name what each measures.'
The same-universe pair already exists in research/phase1-source-comparability/FINDINGS.md §2 (per-year row and dollar capture against the disclosure workbooks). Corpus roll-up, recomputed: rows 62,213 / 127,588 = 48.8%; dollars $3,741,615,569 / $6,271,829,149 = 59.7% (FY2015–FY2027).
```

**Suggested fix.** If the paragraph is rewritten, publish the pair against the disclosure workbooks (48.8% of rows, 59.7% of dollars) and name the by-construction floor. Drop the printed-category-total denominator entirely for public use.

### `data/AMOUNT-PDF-VERIFICATION.csv:19, :292, :395 (`pdf_line` column: 3605, 1920, 8107); produced by code/verify_amounts_against_pdf.py:88 (`fh.read().splitlines()`)`

**Problem.** The `pdf_line` citation in the published evidence artifact does not resolve with any ordinary tool. `pdftotext -layout` emits form feeds (\x0c) at page breaks and Python's `str.splitlines()` splits on them, so `pdf_line` is a splitlines index, offset from the real text line by the number of pages preceding it (82 / 43 / 157 for the three rows). A reader who runs `sed -n '3605p'` lands on a column header; `sed -n '8107p'` lands on an unrelated $41,500 award to a different organization. The entire premise of the artifact is that a human can check the citation.

**Evidence.**

```
$ sed -n '3605p' build/pdftext/fy2015.layout.txt
     Legal Name of Organization                                                EIN                     Amount
$ sed -n '1920p' build/pdftext/fy2023.layout.txt
Agency                 Initiative                                                 Amount
$ sed -n '8107p' build/pdftext/fy2025.layout.txt
Cooper Square Housing Development Fund Company Community Land Trust, Inc.     13-3751729          $41,500

$ .venv/bin/python -c "d=open('build/pdftext/fy2015.layout.txt').read(); print(len(d.splitlines()), d.count(chr(10))+1, d.count(chr(12)))"
18315 18024 292
$ ... print(d[:d.index('Coalition for Asian American Children and Families')].count(chr(12)))
82        # 3523 (real line) + 82 form feeds = 3605 (published pdf_line)

Re-running the script reproduces the committed CSV byte-for-byte, so this is deterministic, not drift:
$ .venv/bin/python code/verify_amounts_against_pdf.py --out /tmp/pdfaudit/RERUN.csv && diff data/AMOUNT-PDF-VERIFICATION.csv /tmp/pdfaudit/RERUN.csv   # no output
```

**Suggested fix.** In `pdf_lines`, split on newlines only — `fh.read().split("\n")` — or strip \x0c before splitting. Regenerate the CSV. Optionally add `pdf_page` as a separate column, which is what the form feeds are actually good for.

### `data/AMOUNT-AUDIT.md:163-165 — "### The 18 `rounding` rows: the PDF backs our figure … All 18."`

**Problem.** "All 18" is asserted at full confidence, but by the script's own taxonomy 5 of the 18 are `pdf_confirms_weak` — defined in the same commit as "Corroborated but not pinned; a person should look." Worse, the one row the section singles out as "the one that matters" (fy17:209) is one of the 5: its EIN is printed on 10 lines that year and no line carrying the amount also names the organization, so the pin is exactly the thing the script says it does not have. The §"What a confirmation does not establish" paragraph attributes all 41 weak rows to the `ein_absent` bucket ("the whole content of the 41 pdf_confirms_weak"), which is arithmetically impossible: 36 of the 41 are ein_absent, 5 are rounding.

**Evidence.**

```
$ python3 (tally over the reproduced /tmp/pdfaudit/RERUN.csv)
('ein_absent', 'pdf_confirms') 383
('ein_absent', 'pdf_confirms_weak') 36
('neighbour_bleed', 'pdf_confirms') 3
('rounding', 'pdf_confirms') 13
('rounding', 'pdf_confirms_weak') 5

rounding rows that are only weak:
  fy16:74 Clinton Housing Development Company 29730 einlines=4
  fy16:75 El Barrio Operation Fight Back 29730 einlines=4
  fy16:94 Strycker's Bay Neighborhood Council 29731 einlines=3
  fy17:209 Bronx Defenders 13-3931074 * $2,076,667 ... 2076666 einlines=10   <- "the one that matters"
  fy27:4682 Osborne Association, Inc., The 14999 einlines=9

(The quoted PDF string itself is accurate — /tmp/pdfaudit/fy17.txt:4527 reads "Brooklyn Defenders Services  11-3305406  $2,076,666". The overstatement is the confidence, not the quote.)
```

**Suggested fix.** Change to "All 18 have their figure printed under their EIN; 13 are pinned to a single named row and 5 — including fy17:209 — are `pdf_confirms_weak`." Fix the 41-weak-rows sentence to say 36 ein_absent + 5 rounding.

### `code/audit_appendix_overlap.py:98-109, 181-186, 194-195`

**Problem.** Dead computation. `pairs()` is called twice per fiscal year (whole-body page range + whole-appendix page range) and its four derived fields — `apx_pairs`, `body_pairs`, `overlap`, `overlap_odd` — are packed into the result dict at lines 194-195 and then never referenced by `main()`. `main()` prints only toc_appendices, toc_restarts_at_1, stream_hits, grand_total, awards_dollars, apx_dollars, ap_rows, twins, twins_dollars, twins_odd, twins_odd_dollars. The docstring's Test-4 narrative is served entirely by `twins()`, which reads the CSVs, not by `pairs()`, which reads the PDF text.

**Evidence.**

```
$ grep -n 'apx_pairs\|body_pairs\|overlap=\|overlap_odd' code/audit_appendix_overlap.py
194:                stream_hits=stream_hits, apx_pairs=len(a), body_pairs=len(b),
195:                overlap=len(both), overlap_odd=len(odd),
(no other occurrence; main() at lines 201-257 references none of the four)
$ time .venv/bin/python code/audit_appendix_overlap.py  -> 0.62s user; the two pairs() scans over ~470 pages x 13 years are the bulk of it
```

**Suggested fix.** Delete `pairs()`, the `b`/`a`/`both`/`odd` locals (lines 181-186) and the four dict keys, plus the now-orphaned `pairs()` tests in code/test_audit_appendix_overlap.py:44-54. If the PDF-level overlap number is wanted as a fifth test, print it; otherwise it is 90% of the runtime for output nobody sees.

### `code/PARSING.md:406 — "stream names absent from the body"`

**Problem.** Absence claim published without the caveat the tool's own output requires. `audit_appendix_overlap.py` prints `stream names in body = 1` for FY2026, not 0. DATA-DICTIONARY.md:70 discloses this in a parenthetical ("One FY2026 hit is the phrase 'local initiatives' inside a purpose sentence, checked by hand"), but PARSING.md states the bare absence, and the same bolded sentence in DATA-DICTIONARY.md reads "appear **zero** times ... of all 13 years" one clause before the parenthetical that contradicts it. This is the failure mode the repo's own standing rule names: a pattern-match result used to DECIDE, published as a count.

**Evidence.**

```
$ .venv/bin/python code/audit_appendix_overlap.py | sed -n '5,18p'
FY     apx in ToC  restart at p1  stream names in body
...
2026            3              1                     1

Hand-check of that hit (confirms the parenthetical is substantively right):
  body pages 6..279, appendices at 280/306/427
  "...support community development, event programming, and local initiatives Banks District 42 113199040 $10,000 DYCD that enhance quality of life for resi..."
```

**Suggested fix.** State the measured number, not zero: "the three stream names appear once in 13 years of body pages, and that one hit is prose inside a purpose sentence (FY2026), not a line item." Same edit in DATA-DICTIONARY.md:70 so the bold claim and its parenthetical agree.

### `DATA-DICTIONARY.md:72 — "`*_schedule_c_initiatives.csv` sums to $5,474,660,271, within 0.026% of the printed figure"`

**Problem.** The figure is FY2015–FY2027 only, but the sentence names the glob with no year qualifier, and the corpus ships six more matching files (FY09–FY14). A reader who runs the stated glob gets $7,363,002,422 — 34.5% higher — and will conclude the number is wrong. The 68.3% headline ratio in the same paragraph is likewise 13-year-scoped (correctly so, since award rows only exist FY15+), which makes the unqualified initiatives sentence the odd one out.

**Evidence.**

```
$ .venv/bin/python -c "import csv,glob; print(sum(int(float(r.get('amount') or 0)) for f in glob.glob('data/fy*/schedule_c/*_schedule_c_initiatives.csv') for r in csv.DictReader(open(f,newline='',encoding='utf-8'))))"
7363002422
Restricted to fy15+: 5474660271  (matches the published figure exactly; delta vs printed 5,476,070,836 = -1,410,565 = 0.0258%)
FY09-FY14 initiative files account for the other $1,888,342,151.
```

**Suggested fix.** Add the scope: "the FY2015–FY2027 `*_schedule_c_initiatives.csv` files sum to $5,474,660,271". FY09–FY14 have initiative totals but no award rows, so they are outside the comparison either way — say so.

### `code/audit_appendix_overlap.py:91-95 (sections)`

**Problem.** The (a) probe: on today's data the tail regex `([ABC])\s+(\d+)` cannot capture a non-appendix marker — group(3) is only the remainder of the `sections:` line, whose entire content is " | A n | B n | C n". But the construction is unguarded: `re.search` is unanchored over the whole file rather than matched at line start, `([ABC])` has no word boundary and is not tied to the `|` delimiter, and if the parser ever writes "A None" (parse_schedule_c.py:311 `apxA=first_heading_page(...)` can return None) the letter is silently skipped while body_hi becomes maxp+1 — apx_lo would then be Appendix B's page and the body and appendix page ranges would overlap, double-scanning pages.

**Evidence.**

```
All 13 sections lines are exactly of the form `sections: body 6..305 | A 306 | B 332 | C 455` (grep -n "^sections:" data/fy*/schedule_c/*_reconciliation.txt). Parser writes it at parse_schedule_c.py:357 with unguarded f-string interpolation of possibly-None values; body_hi at :313 is `apxA or maxp+1`.
```

**Suggested fix.** Anchor the match to the line and the delimiter: re.search(r"(?m)^sections:\s*body\s*(\d+)\.\.(\d+)(.*)$", ...) and re.findall(r"\|\s*([ABC])\s+(\d+)", tail). Return None (not a partial dict) if any of A/B/C is missing.

### `code/audit_appendix_overlap.py:51-52 PDFS[2015] / :180 apx_lo, and data/fy15/schedule_c/fy15_appendix_b_local.csv`

**Problem.** FY2015 has FOUR appendices with a different letter mapping: A = 'LIST OF BASELINED INITIATIVES' (a summary, not award detail), B = AGING DISCRETIONARY, C = YOUTH DISCRETIONARY, D = LOCAL INITIATIVE. The script (following the parser) assumes A=aging / B=local / C=youth, so apx_lo=87 points at the baselined-initiatives summary rather than the first award appendix, and the fy15 appendix CSVs are misnamed relative to their intended contents (fy15_appendix_b_local.csv would hold aging; Appendix D / Local Initiative has no file at all). The dollar impact today is nil because all three fy15 appendix CSVs are empty, but the audit still counts FY2015 as one of the "13 years" in every table.

**Evidence.**

```
build/pdftext/fy2015.pages.txt pages 1-6: ['APPENDIX A: LIST OF BASELINED INITIATIVES ....', 'APPENDIX B: AGING DISCRETIONARY…..PAGE 1', 'APPENDIX C: YOUTH DISCRETIONARY…..PAGE 24', 'APPENDIX D: LOCAL INITIATIVE…..PAGE 57']. data/fy15/schedule_c/ contains fy15_appendix_a_aging.csv, fy15_appendix_b_local.csv, fy15_appendix_c_youth.csv and the recon reports $0 for all three. sections line: 'sections: body 6..86 | A 87 | B 89 | C 112'.
```

**Suggested fix.** Resolve appendix letters to streams from each year's own ToC name rather than by letter position, and exclude FY2015 from the appendix-based tables until its four-appendix layout is handled.

### `code/test_verify_amounts_against_pdf.py:16 — "One EIN in FY2021 is printed on 483 lines"`

**Problem.** Wrong fiscal year. No EIN in FY2021 is printed on 483 lines. FY2021's maximum is 522. The 483 figure belongs to FY2023.

**Evidence.**

```
Counting distinct lines per EIN over my own pdftotext -layout run of each year's Schedule C:
  FY2021 EINs with exactly 483 lines: []
  FY2021 max lines: [('136400434', 522), ('132612524', 50), ('133893536', 37)]
  FY2023 EINs with exactly 483 lines: ['136400434']
Cross-check: the single row in data/AMOUNT-PDF-VERIFICATION.csv with pdf_ein_lines==483 is fiscal_year 2023, ein 136400434 (fy23_schedule_c_awards.csv:585).
```

**Suggested fix.** Change "FY2021" to "FY2023" in the test docstring.

### `code/verify_amounts_against_pdf.py:36-38 — "one EIN is printed on 483 separate lines of a single year (a fiscal sponsor -- see AMOUNT-AUDIT.md on EIN 13-2612524 carrying 229 names)"`

**Problem.** Attributes the 483-line block to the wrong EIN and mischaracterizes it. EIN 13-2612524 (Fund for the City of New York) never exceeds 60 lines in any of the 13 years. The 483-line EIN is 13-6400434, the City of New York's own EIN — an agency/citywide EIN, not a fiscal sponsor. The parenthetical invites the reader to check the wrong thing, and the fiscal-sponsor framing is the premise of the whole tightening argument.

**Evidence.**

```
13-2612524 (FCNY) lines per year: {2015:36, 2016:36, 2017:26, 2018:45, 2019:51, 2020:60, 2021:50, 2022:51, 2023:29, 2024:37, 2025:44, 2026:49, 2027:55} — max 60.
13-6400434: 303, 335, 405, 447, 541, 684, 522, 536, 483, 701, 761, 752, 772 for FY2015..FY2027.
The shipped CSV's own 483-line row is ein=136400434, organization="Mayor's Office of Criminal Justice".
```

**Suggested fix.** Name the actual EIN (13-6400434, FY2023) and drop "a fiscal sponsor". The fiscal-sponsor argument still holds for 13-2612524 at 60 lines / 229 names — it is just a different, smaller example.

### `code/verify_amounts_against_pdf.py:31 — "**14.1% of deliberately-wrong rows still confirmed**" (the first, loose version under the rotation control)`

**Problem.** Unreproducible, and below the floor of the TIGHTENED check under every rotation definition I could build. The loose verdict is by construction a superset of the tightened one, so loose% >= tightened%; my tightened rotation floor across all 103 offsets is 18.0%, and my loose neighbour-rotation measurement is 72.0%. A loose rotation control scoring 14.1% is not reachable from any rotation I can construct.

**Evidence.**

```
/tmp/audit_pdf/controls2.py:
  neighbour offset +1 (full award CSV) LOOSE: conf=317/440=72.0%
  neighbour offset -1 LOOSE: 69.5%;  offset +2 LOOSE: 68.2%
  tightened rotation over the 440 pool, all 103 offsets: min 18.0%, median 21.6%, max 35.5%
  baseline LOOSE on untouched data: 440/440 = 100.0% (this part of the docstring does reproduce)
```

**Suggested fix.** Same fix as the control findings — ship the harness, or restate with the definition. The qualitative point (the loose version confirmed 440/440 on real data) reproduces exactly and stands on its own without the 14.1%.

### `code/audit_appendix_overlap.py:143-163 (twins)`

**Problem.** The twin key is (EIN, amount, organization) with no member component, which inflates the apparent-duplicate count roughly 6x and makes Test 4's job harder than it needs to be. Note the tension with the repo's standing rule that 'member' is never a key component — that rule governs joins to the disclosure workbooks for repair; this is an intra-document duplicate diagnostic against the repo's own two CSVs and no value is copied from anywhere, so reporting the member-qualified figure alongside is a diagnostic, not a join. Flagging rather than prescribing, because the rule is written without that carve-out.

**Evidence.**

```
FY2027 appendix rows matching an award row: (EIN, amount, org) = 953 rows / $10,791,000; adding member = 163 rows / $2,050,000; adding member + purpose prefix = 6 rows / $120,000. The 953 figure is what the published 'apparent duplicates' paragraph is built on.
```

**Suggested fix.** Report both figures in Test 4 (953 unqualified, 163 member-qualified) and state explicitly that member is used here as a within-document diagnostic and never as a join key. If the standing rule is meant to bar even that, say so in the script comment and keep only the 953 figure — but then do not describe it as 'apparent duplicates', because it demonstrably is not.

### `code/test_audit_appendix_overlap.py:71-78 and code/test_verify_amounts_against_pdf.py:94-104 (both test_script_writes_no_data_file)`

**Problem.** Both guards are literal-substring scans of the source text, not behavioural checks. They assert that certain characters do not appear, not that the script writes nothing. Any write that does not spell the banned literals passes — pathlib.Path(...).write_text(), os.path.join()-assembled paths, csv writers, shutil. Presented as enforcement of the repo's "no --apply path / no data file modified" rule, they enforce only the naive spelling of a violation.

**Evidence.**

```
Inserted a REAL data-tree write into audit_appendix_overlap.py in the /tmp copy:
  pathlib.Path(f'data/{key}/schedule_c/CLOBBERED.csv').write_text('x')
$ pytest code/test_audit_appendix_overlap.py -q
.......                                                                  [100%]
7 passed in 0.01s      <- guard did not fire
Inserted a REAL clobber of a data/fy* file into verify_amounts_against_pdf.py:
  open(os.path.join("data", "fy" + "21", "schedule_c", "fy21_schedule_c_awards.csv"), "w").write("clobbered")
$ pytest code/test_verify_amounts_against_pdf.py -q
6 failed, 1 passed          <- the 1 passed IS test_script_writes_no_data_file; the 6 failures are
                               incidental FileNotFoundError from the write itself, not the guard
(They do catch the naive forms: V12 adding a literal "--apply" arg and V14 writing a literal "data/fy21/..." path were both CAUGHT.)
```

**Suggested fix.** Keep the cheap literal scan, but add a behavioural guard: snapshot mtimes+sizes of data/fy*/ (or run under a tmp_path CWD with a seeded data tree), invoke main(), and assert nothing under data/fy* changed. That catches any write regardless of how the path is spelled.

### `code/test_audit_appendix_overlap.py:35`

**Problem.** The assertion reimplements the production expression instead of calling it. `assert sum(1 for _, _, lo, _ in hits if int(lo) == 1) == 1` is a verbatim copy of audit()'s `restarts = sum(1 for _, _, lo, _ in toc_hits if int(lo) == 1)`. The test therefore verifies its own copy of the logic, and the comment above it ("that restart is the evidence, so it must be read correctly") describes coverage that does not exist.

**Evidence.**

```
A16  `restarts = sum(1 for _, _, lo, _ in toc_hits if int(lo) == 1)`  ->  `restarts = len(toc_hits)`
  : {"id":"A16","status":"SURVIVED  <-- test gap","failed":[],"summary":"14 passed in 0.01s"}
```

**Suggested fix.** Factor the restart count out of audit() into a one-line helper (e.g. `def restarts(toc_hits)`) and assert on the helper, so the test exercises the shipped expression rather than a duplicate of it.

### `code/verify_amounts_against_pdf.py:132-137 (the `pdf_no_source` branch) — no test`

**Problem.** One of the five documented verdicts is never exercised. This is the branch that fires when a mapped Schedule C PDF is missing from disk, i.e. exactly the condition under which the script has no evidence at all. It can be changed to emit pdf_confirms with the suite green.

**Evidence.**

```
V11  `pdf_verdict="pdf_no_source"` -> `pdf_verdict="pdf_confirms"` in the `lines is None` branch
  : {"id":"V11","status":"SURVIVED  <-- test gap","failed":[],"summary":"14 passed in 0.01s"}
```

**Suggested fix.** One test: `run([row(...)], page=None)` — the existing run() helper already monkeypatches pdf_lines, so passing page=None gives the branch for free. Assert pdf_verdict == "pdf_no_source".

### `code/verify_amounts_against_pdf.py:168-207 (main) — no test`

**Problem.** main() is wholly untested: the TARGET_VERDICTS filter that defines BLOCKER 1's 440-row denominator, the per-verdict tally and dollar aggregation that produce the published $22,481,361 / $2,834,626 figures, and the CSV column ordering written to data/AMOUNT-PDF-VERIFICATION.csv. The filter can be removed — changing which rows are audited and therefore every headline count — with the suite green.

**Evidence.**

```
V13  `if r["verdict"] in TARGET_VERDICTS]`  ->  `if r["verdict"] or True]`  (audits every row, not the 440)
  : {"id":"V13","status":"SURVIVED  <-- test gap","failed":[],"summary":"14 passed in 0.01s"}
```

**Suggested fix.** Drive main() over a small fixture FINDINGS csv in tmp_path containing one row of each verdict (including one NOT in TARGET_VERDICTS), with --out to tmp_path, and assert the output row count, the header, and the per-verdict dollar tally.

### `research/phase1-source-comparability/FINDINGS.md:564-567 (item 12)`

**Problem.** Still filed as an open blocking action against text that no longer exists: "`README.md:95` still says the appendix files 'are subsets of the main body...' ... **This needs a decision before 1.4.0 ships**, because the repo and the tools now tell different stories." The decision was made in this commit; README.md:95 now says the opposite. Doc is `status: draft` but is the corpus-wide synthesis the other research files defer to.

**Evidence.**

```
sed -n '560,570p' research/phase1-source-comparability/FINDINGS.md vs `grep -n appendix README.md` → line 95 now "additional to the main body".
```

**Suggested fix.** Mark item 12 resolved with the 2026-08-13 date and a pointer to code/audit_appendix_overlap.py.

### `research/phase1-source-comparability/PHASE-0.5-IMPACT.md:91-93`

**Problem.** Quotes the old README line in the present tense as live repo state — "the repo's own `README.md` says of these files: *\"These are subsets of the main body re-sorted by funding stream — do not add them to the Schedule C total.\"*" — with no note that it was corrected.

**Evidence.**

```
sed -n '88,95p' research/phase1-source-comparability/PHASE-0.5-IMPACT.md; README.md:95 no longer contains that sentence.
```

**Suggested fix.** Add "(corrected 2026-08-13; see DATA-DICTIONARY.md)" inline.

### `commit ba90fce message: "150 tests pass (was 143)"`

**Problem.** The two numbers are measured at different scopes, understating the tests added by half. 150 is `pytest code/` today; 143 is `pytest` at repo root on the parent commit. Like-for-like it is 136 → 150 (code/) or 143 → 157 (root): 14 tests added, not 7.

**Evidence.**

```
`.venv/bin/pytest code -q` on ba90fce → "150 passed in 173.61s"; `pytest -q --collect-only` root on ba90fce → 157; `git checkout b7a2f7f && pytest code --collect-only` → 136; `pytest viz --collect-only` → 7 (viz untouched by the commit).
```

**Suggested fix.** State "150 tests in code/ pass (was 136; 157 repo-wide, was 143)".

### `code/audit_appendix_overlap.py:14-15 (module docstring)`

**Problem.** Two claims the committed code does not support. (a) "84-96% of appendix rows have no (ein, amount) twin among the awards" — the script never computes an (ein, amount)-only CSV twin rate; its printed TEST 4 column is 75-100% on (ein, amount, organization), which is what DATA-DICTIONARY publishes. The 84-96% figure is unreproducible from the repo. (b) "a few hundred match on all of (ein, amount, member, organization)" names `member` as a key component, which `twins()` does not use and which contradicts the repo's own standing rule restated in DATA-ANOMALIES.md §21 ("Council member is never a key component").

**Evidence.**

```
code/audit_appendix_overlap.py:14-15 vs `twins()` at line ~138: `return (re.sub(r"\D","",r.get("ein")...), amt, re.sub(r"[^a-z0-9]","",(r.get("organization") or "").lower()))` — no member. Script output TEST 4 "no twin %" column = 100,93,91,91,78,77,78,75.
```

**Suggested fix.** Replace 84-96% with the 75-100% the script actually prints, and drop `member` from the key description.

### `code/audit_appendix_overlap.py:6-8 (module docstring)`

**Problem.** Overstates the blast radius of the additive/subset question: "it decides the top-line number in the README, the viz and every MCP response footer." None of the three is true. README.md carries no award total (its only headline dollar is the FY2027 initiative grand total $655,764,999, which is category-level and unaffected). The viz's "Adopted" series is initiative-level and its "Itemized" series reads only `*_awards.csv` joined on (category, initiative) — appendix rows have neither field, so they cannot enter either series. The MCP FOOTER/SCOPE_NOTE state no dollar total at all.

**Evidence.**

```
`grep -n '\$[0-9]' README.md` → only $655,764,999 and $66,472,992/$283,588,100 sidecar figures. viz/schedulec_cleanup.py:36-44 ("Adopted <year> ... from *_initiatives.csv"; "Itemized <year> ... from *_awards.csv, summed per (category, initiative) exact match"). mcp/src/server.ts:33-37 FOOTER + SCOPE_NOTE contain no total.
```

**Suggested fix.** Narrow to "it decides the award-row headline in DATA-DICTIONARY/AMOUNT-AUDIT and the totals the MCP award tools return".

### `data/AMOUNT-AUDIT.md:167-176 ("The check was measured against controls") and code/verify_amounts_against_pdf.py:25-27`

**Problem.** The four control results (440/440, 440/440, 11.0%, 5.0%) are published as the reason to believe the check, but no committed code reproduces any of them — there is no control harness in the script or its tests, so a reader cannot re-derive them. Separately, the script docstring reports the rotation control at 14.1% while AMOUNT-AUDIT.md's table reports 11.0%, with nothing stating that one is the loose first version and the other the tightened one.

**Evidence.**

```
`grep -rn -i "rotate|control|11.0|14.1" code/verify_amounts_against_pdf.py code/test_verify_amounts_against_pdf.py` → single hit, the docstring prose at line 25-27. Test names in code/test_verify_amounts_against_pdf.py are 7 unit tests on synthetic pages; none runs a control. code/PARSING.md:401 nonetheless says "the controls the check was measured against are in data/AMOUNT-AUDIT.md".
```

**Suggested fix.** Commit the control harness behind a flag (e.g. `--control rotate|plant|corrupt|cross-ein`) so the numbers are reproducible, and label the 14.1% figure as the pre-tightening measurement.

### `DATA-DICTIONARY.md:72 (the 68.3% / $1.73B under-capture record)`

**Problem.** The commit's third headline ("ALSO RECORDED — the risk is the opposite of double-counting, and larger") is recorded in exactly one place: a blockquote inside a schema dictionary's appendix-file section. It appears nowhere in DATA-ANOMALIES.md — which is the repo's stated catalog of limitations and which the sentence itself points at ("See `DATA-ANOMALIES.md` on row capture") — nor in README.md, mcp/README.md, or any MCP output.

**Evidence.**

```
`grep -rn -i "68.3|under-capture" .` → one hit, DATA-DICTIONARY.md:72. DATA-ANOMALIES.md §20 has a "Caution for anyone quoting a completeness figure" paragraph but publishes no figure; §21 publishes no capture-vs-printed number either.
```

**Suggested fix.** Add a DATA-ANOMALIES.md entry carrying $3,741,615,569 / $5,476,070,836 / 68.3% with the category-total contrast, and cross-link it from DATA-DICTIONARY.

### `viz/README.md:5, viz/PLAN.md:35-44, viz/index.html:47`

**Problem.** The viz was not revisited after the reversal. Its "Itemized" series is defined as "the share of that initiative designated to a NAMED recipient" and the gap to "Adopted" as "discretionary money not traceable to a named recipient" — but 28,575 appendix rows worth $352,997,275, now published as additive named designations, are excluded from Itemized by construction (they carry no category/initiative to join on). Nothing in viz/ discloses that.

**Evidence.**

```
viz/schedulec_cleanup.py:36-44 defines Itemized from `*_awards.csv` on exact (category, initiative); DATA-DICTIONARY.md:63 lists category/initiative as absent from appendix files; script output: appendix dollars $352,997,275 across 13 years.
```

**Suggested fix.** One sentence in viz/README.md and viz/PLAN.md § Risks naming the appendix exclusion and its size, so the Adopted-vs-Itemized gap is not read as pure untraceability.

### `code/verify_amounts_against_pdf.py:31 — "one EIN is printed on 483 separate lines of a single year (a fiscal sponsor -- see AMOUNT-AUDIT.md on EIN 13-2612524 carrying 229 names)"; code/test_verify_amounts_against_pdf.py:16 — "One EIN in FY2021 is printed on 483 lines"; data/AMOUNT-AUDIT.md — "an EIN printed on 483 separate lines of one year"`

**Problem.** The 483 figure is attached to the wrong EIN and the wrong year. EIN 13-2612524 (Fund for the City of New York, the fiscal sponsor the parenthetical names) never exceeds 60 printed lines in any year. 483 belongs to EIN 13-6400434 in FY2023. FY2021's maximum is 522, not 483. The corpus maximum is 772 (FY2027), so the argument is also understated.

**Evidence.**

```
$ .venv/bin/python - (using V.ein_index on V.pdf_lines per year)
  2015 13-2612524: 36  13-6400434: 303
  2020 13-2612524: 60  13-6400434: 684
  2021 13-2612524: 50  13-6400434: 522
  2023 13-2612524: 29  13-6400434: 483   <- the 483
  2027 13-2612524: 55  13-6400434: 772   <- corpus max
```

**Suggested fix.** Say '13-6400434 is printed on 483 lines of FY2023 and 772 of FY2027'. Drop or correct the 13-2612524 parenthetical and the 'FY2021' in the test docstring.

### `DATA-DICTIONARY.md:68 — "'Aging Discretionary', 'Local Initiatives' and 'Youth Discretionary' appear **zero** times across the body pages of all 13 years. (One FY2026 hit is the phrase 'local initiatives' inside a purpose sentence, checked by hand.)"`

**Problem.** Two issues. (1) The bolded 'zero' is contradicted by its own parenthetical and by the script's output column, which prints 1 for FY2026 — the honest count is 12 years at 0 and one year at 1. (2) The test is close to circular: parse_schedule_c.py defines body_hi as the first page whose line *starts with* 'Appendix A', so every page carrying the stream names in its running header is excluded from 'the body' by construction, not by measurement.

**Evidence.**

```
$ .venv/bin/python /tmp/audit57/streams.py   (my own pdftotext, body ranges from the reconciliation)
  2015..2025, 2027: aging 0 / local-s 0 / local 0 / youth 0
  2026: aging 0 / 'local initiatives' 1 / 'local initiative' 1 / youth 0
  FY2026 body page 52: 'Funds will be used to support community development, event programming, and local initiatives that enhance quality of life for residents in Council District 42.'  <- prose, as claimed
$ grep -n -A6 'def first_heading_page' code/parse_schedule_c.py
  96-            if ln.strip().lower().startswith(marker.lower()): return pn
$ sed -n '313p' code/parse_schedule_c.py
      body_hi=apxA or maxp+1
```

**Suggested fix.** Write 'zero times in twelve of thirteen years; one FY2026 hit, prose in a purpose field'. Add one sentence noting the body range is defined by the first 'Appendix A' heading, so the test rules out a body *line item*, not stray text.

### `DATA-DICTIONARY.md:70 — "leaving a 0.1% residual" vs commit message — "the appendices supply 98% of its shortfall, residual 0.13%"`

**Problem.** Same quantity, two renderings, and the sentence structure makes the smaller one misread. Following '98%' of the shortfall, '0.1% residual' parses as 0.1% of the shortfall — the residual is 1.69% of the shortfall. Both 0.1% and 0.13% are only correct against the $655,764,999 total, a denominator neither sentence names.

**Evidence.**

```
$ python3 -c "s=655764999-605111412; print(s, 49799000/s*100, (s-49799000), (s-49799000)/s*100, (s-49799000)/655764999*100)"
  50653587  98.31305...  854587  1.68695%  0.13031%
  -> residual is 1.69% of the shortfall, 0.130% of the grand total
```

**Suggested fix.** State it once with its denominator: 'residual $854,587 — 1.7% of the shortfall, 0.13% of the year's total' — and use the identical wording in DATA-DICTIONARY.md and the commit message.

### `code/audit_appendix_overlap.py:20 — "84-96% of appendix rows have no (ein, amount) twin among the awards, pointing additive; but a few hundred match on all of (ein, amount, member, organization)"`

**Problem.** The range is wrong and the key described is not the key used. Measured on the data this commit ships, the (ein, amount) no-twin rate is 70.6%-100.0%, outside the stated 84-96% at both ends. Separately, twins() keys on (ein, amount, organization) — `member` is not in it — and describing the match key as including `member` writes the repo's forbidden key component into the audit's own documentation.

**Evidence.**

```
$ .venv/bin/python - (no-twin % by key definition, per year)
  FY      2-key(ein,amt)   3-key(+org)   4-key(+member)
  2018        100.0%          100.0%        100.0%
  2021         86.1%           92.8%         99.7%
  2024         73.7%           77.8%         96.7%
  2025         71.1%           77.0%         95.6%
  2027         70.6%           75.3%         95.8%
  -> 2-key range 70.6-100.0%, not 84-96%
$ grep -n 'def k(r)' -A5 code/audit_appendix_overlap.py
      return (re.sub(r"\D", "", r.get("ein") or ""), amt,
              re.sub(r"[^a-z0-9]", "", (r.get("organization") or "").lower()))   # no member
```

**Suggested fix.** Update to '70.6-100% have no (ein, amount) twin' and describe the match key as (ein, amount, organization), matching twins().

### `DATA-DICTIONARY.md:63 and README.md:95 — "These are ADDITIONAL to the award body… Adding them to the Schedule C total is correct."`

**Problem.** Correct as a rule, but published without the fact that makes it operationally misleading: 5 of the 13 award years (FY2015, FY2016, FY2017, FY2019, FY2020) have header-only appendix CSVs — 0 rows, $0. A reader told 'adding them is correct' will add nothing for those years and has no way to know the appendix money is simply absent rather than zero. mcp/CHANGELOG.md already records this gap; neither corrected doc mentions it.

**Evidence.**

```
$ .venv/bin/python /tmp/audit57/recompute.py
  fy15 ap_n 0 $0 | fy16 0 $0 | fy17 0 $0 | fy19 0 $0 | fy20 0 $0
  fy18 422 $4,419,275 | fy21 4,310 $49,799,000 | ... | fy27 3,860 $49,799,000
$ grep -n 'header-only' mcp/CHANGELOG.md
  86:- **FY2015-FY2017 and FY2019-FY2020 appendix CSVs are header-only upstream**
(the FY2015 PDF does print them — its ToC lists 'APPENDIX B: AGING DISCRETIONARY…..PAGE 1', but the parser looks for 'Appendix A/B/C' and FY2015's Appendix A is 'List of Baselined Initiatives')
```

**Suggested fix.** Add one sentence to both corrected paragraphs: 'Five of thirteen years (FY2015-17, FY2019-20) currently have empty appendix files — the rows exist in the PDF but were not extracted, so those years' totals are short by the appendix amount.'

### `data/AMOUNT-AUDIT.md — "### The 18 `rounding` rows… `fy17_schedule_c_awards.csv`:209 is the one that matters… The decision not to auto-correct… is confirmed"`

**Problem.** fy17:209 carries verdict `pdf_confirms_weak` in the artifact this section cites, not `pdf_confirms` — its EIN appears on 10 lines and its own `organization` cell is org_merged, which is exactly the condition the same document defines as 'corroborated but not pinned; a person should look'. Presenting the flagship example as settled overstates its own verdict.

**Evidence.**

```
$ .venv/bin/python - (read data/AMOUNT-PDF-VERIFICATION.csv)
  fy17:209 organization field = 'Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services'
  pdf_ein_lines 10  org_text_merged 'yes'  pdf_verdict pdf_confirms_weak
  pdf_text 'Brooklyn Defenders Services 11-3305406 $2,076,666'
(the amount claim itself checks out: all 18 rounding rows carry our figure and not the disclosure's on the printed line — 18 of 18)
```

**Suggested fix.** Say 'confirmed on the printed line, though classed weak because that row's own organization cell is org_merged' — the amount evidence is unaffected.

### `code/verify_amounts_against_pdf.py:27-29 (module docstring)`

**Problem.** "one EIN is printed on 483 separate lines of a single year (a fiscal sponsor -- see AMOUNT-AUDIT.md on EIN 13-2612524 carrying 229 names)" mis-attributes the number. The EIN printed on 483 lines of FY2023 is 13-6400434, the City of New York's own EIN. 13-2612524 (Fund for the City of New York) is printed on 29 lines in FY2023 and peaks at 60 (FY2020) across all 13 years. 483 is also not the corpus maximum — FY2027 has 772. This sentence is the stated reason the whole pinning design exists, and it is reproduced in AMOUNT-AUDIT.md's reasoning.

**Evidence.**

```
/tmp/p_pin2-style scan: `most-printed EIN per year … FY2023: max 136400434 x483   13-2612524 (FCNY) x29`; `FY2020: max 136400434 x684   13-2612524 x60`; `FY2027: max 136400434 x772   13-2612524 x55`. Sample line: `Abreu City University of New York - CUNY Citizenship NOW! 136400434 $5,000 CUNY …`. All 483 are distinct line numbers (verified: `len(hits)=483, DISTINCT line numbers=483`), so `pdf_ein_lines` itself is correct.
```

**Suggested fix.** Replace "a fiscal sponsor … EIN 13-2612524" with "the City's own EIN, 13-6400434, which reaches 772 lines in FY2027". The argument gets stronger, not weaker.

### `code/verify_amounts_against_pdf.py:28-29 ("one EIN is printed on 483 separate lines of a single year (a fiscal sponsor -- see AMOUNT-AUDIT.md on EIN 13-2612524 carrying 229 names)"), data/AMOUNT-AUDIT.md:182, code/test_verify_amounts_against_pdf.py:24 ("One EIN in FY2021 is printed on 483 lines")`

**Problem.** The 483-line EIN is 13-6400434 in FY2023 — the City's own EIN (District Attorney-Kings / Mayor's Office of Criminal Justice), not a fiscal sponsor. EIN 13-2612524 (Fund for the City of New York, the actual fiscal sponsor) is printed on 29 lines in FY2023 and 50 in FY2021. The test docstring attributes 483 to FY2021, where the true figure is 522; FY2024 reaches 701. Three files carry the same misattribution, and it is load-bearing prose — it is the stated justification for the pinning rule.

**Evidence.**

```
Counting \b(\d{2})-?(\d{7})\b occurrences per line over /tmp/audit440/*.layout.txt:
  FY2023 EIN 136400434: 483 lines;  FY2023 EIN 132612524: 29 lines
  FY2021 top EIN line counts: [('136400434', 522), ('132612524', 50), ('133893536', 37)]
  FY2023 top: [('136400434', 483), ('131624228', 38), ('133893536', 33)]
  FY2024 top: [('136400434', 701), ('133192793', 60), ('132620896', 54)]
Also: the FY2023 row that carries pdf_ein_lines=483 in data/AMOUNT-PDF-VERIFICATION.csv is fy23:585, ein=136400434.
```

**Suggested fix.** Change all three to "EIN 13-6400434 is printed on 701 lines of FY2024 (483 in FY2023)" and drop "a fiscal sponsor"; keep the 13-2612524 / 229-names point as a separate, correctly-attributed example.

### `data/AMOUNT-AUDIT.md:169 ("That ambiguity affects **43 of the 440**, and is the whole content of the 41 `pdf_confirms_weak`")`

**Problem.** 43 reconciles to nothing. The sentence says the ambiguity is 'the whole content of the 41 pdf_confirms_weak' (=41) but then defines it as weak-OR-org-defective, whose union is 45. Neither is 43. In a section whose argument is that every number was measured, an unsourced count is a credibility cost.

**Evidence.**

```
pdf_confirms_weak = 41 (reproduced exactly). org_merged+org_prose among the 440 = 11 (7 merged + 4 prose) using code/validate_data.py's own EIN_IN_TEXT / ORG_PROSE. Overlap: 5 merged-weak + 2 prose-weak = 7. Union = 41 + (11 - 7) = 45.
```

**Suggested fix.** State the two counts separately: 41 pdf_confirms_weak, 11 rows with a known-defective organization field, 45 distinct rows affected.

### `code/verify_amounts_against_pdf.py:157 (`pdf_line=n, pdf_amounts=ours`) — affects data/AMOUNT-PDF-VERIFICATION.csv columns pdf_amounts and pdf_line`

**Problem.** Two presentation defects in the published evidence artifact. (a) For all 440 confirming rows the column named `pdf_amounts` contains our own `our_amount` echoed back, not any figure read from the PDF — the artifact's 'what the PDF says' column is circular. (b) `pdf_line` for non-uniquely-matched rows is `carrying[0]`, so when two of our rows correspond to two distinct printed awards, both cite the same printed line and at least one citation points at the wrong award.

**Evidence.**

```
(a) code/verify_amounts_against_pdf.py:157 passes pdf_amounts=ours on the confirming branch; only the pdf_contradicts branch (:162) reports figures actually read from the PDF. Confirmed in the CSV: every confirms/weak row's pdf_amounts equals its our_amount.
(b) fy21:382 and fy21:383 both cite FY2021 line 8316, but /tmp/audit440/fy2021.layout.txt has two distinct printed awards under EIN 261422585:
  L8316: Rose Day Free Street Fair 261422585 $5,000 DYCD running the annual West Brighton Harmony Day event.
  L8318: Rose Free Street Fair & Other Events 261422585 $5,000 DYCD and other ongoing events such as food giveaways.
Same shape: fy22:139/140 both cite L14151 (CASYM has awards at L14151 and L14153); fy24:2114/2116 both cite L20794 ($10,000 awards printed at L20794 and L20800).
```

**Suggested fix.** Rename the column pdf_amount_matched or populate it from amounts_on(t); and when several lines qualify, emit all matching line numbers (semicolon-joined) rather than the first.


## NIT

### `data/AMOUNT-PDF-VERIFICATION.csv — column semantics; data/AMOUNT-AUDIT.md:141-147 verdict table; DATA-DICTIONARY.md`

**Problem.** `pdf_line`, `pdf_amounts`, `pdf_ein_lines` and `pdf_text` are defined in no committed .md — only in the generator's docstring. DATA-DICTIONARY.md has no entry for the file. The published verdict table lists 4 of the 5 values the script can emit; `pdf_no_source` (code/verify_amounts_against_pdf.py:41,135) is absent. Zero rows carry it today because all 13 years map to a PDF, so this is a completeness gap rather than a wrong number.

**Evidence.**

```
$ grep -rn "pdf_line|pdf_ein_lines|pdf_no_source" --include="*.md" .   -> no hits
$ grep -n "## `data/" DATA-DICTIONARY.md   -> entries for data/{year}/... and data/combined/... only; no audit artifacts
Note the sibling data/AMOUNT-AUDIT-findings.csv is equally undocumented, so this matches existing practice and is not a regression introduced here.
```

**Suggested fix.** Add a short column table to the 'Settled against the adopted PDF' section of data/AMOUNT-AUDIT.md, and add `pdf_no_source` to the verdict table with an explicit 'not reachable today, all 13 years map to a PDF'.

### `code/test_verify_amounts_against_pdf.py — no test touches the shipped artifact`

**Problem.** The artifact is derived from data/AMOUNT-AUDIT-findings.csv, which is itself a generated file. Nothing asserts the committed CSV still matches a re-run, so a later change to audit_amounts.py strands data/AMOUNT-PDF-VERIFICATION.csv silently — the published 399/41 tallies keep looking authoritative while describing a prior corpus. The 14 existing tests all run against a 4-line synthetic page.

**Evidence.**

```
$ .venv/bin/pytest code/test_verify_amounts_against_pdf.py code/test_audit_appendix_overlap.py -q
14 passed in 0.01s
$ grep -n "AMOUNT-PDF-VERIFICATION" code/test_verify_amounts_against_pdf.py  -> no hits
All 14 tests substitute V.pdf_lines with a fixed 4-element PAGE list.
```

**Suggested fix.** One test: regenerate to a tmp path and assert byte-equality with data/AMOUNT-PDF-VERIFICATION.csv. It runs in 0.35s warm and is the smallest thing that fails when the artifact goes stale.

### `code/verify_amounts_against_pdf.py:170, 202`

**Problem.** `--out` is an unconstrained path passed straight to `open(args.out, "w")`. `python3 code/verify_amounts_against_pdf.py --out data/fy27/schedule_c/fy27_schedule_c_awards.csv` truncates a data file. The commit does not do this, and the sibling it cites for its read-only discipline (`audit_amounts.py`) deliberately writes to fixed module constants and offers `--dry-run` instead. Precedent for a settable output path does exist (`validate_data.py --report`), so this is a consistency gap, not a new class of risk.

**Evidence.**

```
code/verify_amounts_against_pdf.py:170  ap.add_argument("--out", default="data/AMOUNT-PDF-VERIFICATION.csv")
code/verify_amounts_against_pdf.py:202  with open(args.out, "w", newline="", encoding="utf-8") as fh:
$ grep -n 'add_argument' code/audit_amounts.py
630:    ap.add_argument("--dry-run", action="store_true",
(no --out; REPORT and FINDINGS are module constants)
```

**Suggested fix.** Refuse a destination under `data/fy*`: `if re.match(r"data/fy\\d", args.out): sys.exit("refusing to write into the per-year data tree")`. Two lines, and it makes the docstring's "NOTHING IS WRITTEN TO THE DATA" true of the CLI and not only of the default.

### `code/verify_amounts_against_pdf.py:200`

**Problem.** `cols = list(rows[0].keys()) + [...]` raises IndexError when `data/AMOUNT-AUDIT-findings.csv` contains no row whose verdict is in TARGET_VERDICTS — i.e. exactly the success case where a future `audit_amounts.py` run resolves all 440. The script prints "rows the disclosure could not corroborate: 0" and then crashes with a traceback instead of writing an empty artifact.

**Evidence.**

```
code/verify_amounts_against_pdf.py:176-178 builds `rows` by filtering on verdict, prints len(rows), never guards empty. Line 200 indexes rows[0]. Reproduced by pointing FINDINGS at a header-only CSV:
$ .venv/bin/python -c "rows=[]; rows[0]"
IndexError: list index out of range
```

**Suggested fix.** Return early after the count print when `not rows`, or hoist the column list to a module constant since the findings schema is fixed anyway.

### `code/audit_appendix_overlap.py:15`

**Problem.** Docstring describes a match key the code does not use: "a few hundred match on all of (ein, amount, member, organization), pointing subset". `twins()` at line 150-156 keys on (ein, amount, organization) — `member` is absent. The standing rule ("'member' is never a key component") is honored by the code; the docstring misdescribes it in the direction of claiming a stricter test than was run.

**Evidence.**

```
code/audit_appendix_overlap.py:15   (ein, amount, member, organization), pointing subset):
code/audit_appendix_overlap.py:155-156
        return (re.sub(r"\\D", "", r.get("ein") or ""), amt,
                re.sub(r"[^a-z0-9]", "", (r.get("organization") or "").lower()))
(twins() docstring at line 141 correctly says "(EIN, amount, organization)")
```

**Suggested fix.** Drop `member` from line 15 so the module docstring matches `twins()` and the standing rule reads unambiguously.

### `code/verify_amounts_against_pdf.py:89 and code/audit_appendix_overlap.py:74`

**Problem.** Cache invalidation is `if not os.path.exists(txt)` — no mtime or hash comparison against the source PDF. A replaced or re-downloaded PDF under `source/` is silently never re-extracted, and the audit would then be reporting against a stale reading of a document that has changed. Separately, the two scripts run the identical `pdftotext -layout` command over the same PDF into two different filenames (`fy{Y}.layout.txt`, `fy{Y}.pages.txt`), duplicating ~33MB of identical text.

**Evidence.**

```
$ ls build/pdftext/ | wc -l
26          # 13 years x 2 near-identical files
$ cmp build/pdftext/fy2027.layout.txt build/pdftext/fy2027.pages.txt && echo SAME
SAME
Both call sites: subprocess.run(["pdftotext", "-layout", src, txt], check=True) — same args, different output name.
```

**Suggested fix.** One cache filename shared by both scripts, guarded by `os.path.getmtime(txt) < os.path.getmtime(src)`. Halves the cache and closes the stale-source hole.

### `.github/workflows/ci.yml:26-33`

**Problem.** The 14 new Python tests this commit adds never run in CI. The only CI workflow is path-scoped to `mcp/**` and `.github/workflows/**`, so a PR touching only `code/` and `data/` triggers no job at all. Pre-existing, not caused by this commit, but this commit is the one landing two new guard scripts whose correctness rests entirely on tests that no automation executes.

**Evidence.**

```
ci.yml paths filter: ["mcp/**", ".github/workflows/**"]
$ git diff main..HEAD --name-only | grep -c '^mcp/'
0
version-guard diffs only mcp/src mcp/scripts mcp/package.json data/combined -> also empty -> "version guard not applicable. Passing."
Local run: 150 passed in 177.09s (exit 0); main collects 136.
```

**Suggested fix.** Add a `code/**` path to a Python job (`pytest code/ -q` plus the three guards), or note in code/PARSING.md that these tests are run by hand so a future reader does not assume CI covers them.

### `code/audit_appendix_overlap.py:112-123 (csv_total) and :142-148 (twins.load)`

**Problem.** The (c)/(d) probes come back clean, with one dead line worth removing. `if "initiatives" in f or "reconcil" in f: continue` is unreachable: the two globs are `*_schedule_c_awards.csv` and `*_appendix_*.csv`, neither of which can match `*_schedule_c_initiatives.csv` or `*_schedule_c_reconciliation.txt`. The exclusion is achieved by the glob, not the filter, so the filter reads as a guard that is actually load-bearing when it is not. No double-counting: the two globs are disjoint and match exactly one awards file and three appendix files per year, with no stray files in any of the 13 directories.

**Evidence.**

```
ls of all 13 data/fy{15..27}/schedule_c/ directories: each contains exactly fyNN_appendix_a_aging.csv, fyNN_appendix_b_local.csv, fyNN_appendix_c_youth.csv, fyNN_schedule_c_awards.csv, fyNN_schedule_c_initiatives.csv, fyNN_schedule_c_reconciliation.txt. Row/dollar cross-check: csv_total apx rows and twins() ap_rows agree for every year (fy27 3,860 = 467+2,558+835 per the recon tail).
```

**Suggested fix.** Delete the two `continue` guards, or widen the globs to `*.csv` and let the guards do the work. Pick one.

### `code/parse_schedule_c.py:357 (consumed by audit_appendix_overlap.py:91-95, :177)`

**Problem.** The reconciliation's `sections:` line hardcodes the body start as literal 6 (`f"sections: body 6..{body_hi-1} ..."`) even though the parser computes body_lo = max(6, pn-1) from the first 'Agency Initiative Amount' page and may have used a larger value. The audit therefore scans a body range that is a superset of the parser's actual body. The direction is conservative for Test 2 (more pages searched, more chance of a hit) but it breaks the docstring's own guarantee that "this audit and the parser cannot disagree about which pages are the body."

**Evidence.**

```
code/parse_schedule_c.py:314-317 computes body_lo dynamically; line 357 writes the literal 6. All 13 recon files read 'body 6..'.
```

**Suggested fix.** Write the computed body_lo into the sections line.

### `data/AMOUNT-AUDIT.md — "an EIN printed on **483 separate lines** of one year makes 'the number is in there somewhere' nearly free"`

**Problem.** 483 is only the maximum among the 440 audited rows, not the corpus maximum, and the sentence reads as if it were the worst case. The true worst case is 772 lines (FY2027, same EIN). The error runs against the author's own argument, so it is harmless in direction, but it is still a wrong number presented as a measured fact.

**Evidence.**

```
Per-year max lines for EIN 13-6400434 across my own extraction: FY2023=483, FY2024=701, FY2025=761, FY2026=752, FY2027=772. max across years: (2027, '136400434', 772). max(pdf_ein_lines) in data/AMOUNT-PDF-VERIFICATION.csv = 483 — i.e. 483 is a property of the audited sample, not of the corpus.
```

**Suggested fix.** Say "up to 772 separate lines of one year (483 among the rows audited here)", or scope the sentence to the audited rows explicitly.

### `DATA-DICTIONARY.md:69 — "leaving a 0.1% residual"`

**Problem.** Ambiguous denominator. $50,653,587 - $49,799,000 = $854,587, which is 0.130% of the category grand total but 1.69% of the shortfall the sentence is discussing. The reader's natural referent is the shortfall, where the residual is an order of magnitude larger than stated.

**Evidence.**

```
854,587 / 655,764,999 = 0.130% ; 854,587 / 50,653,587 = 1.69%. The sentence's subject is the shortfall.
```

**Suggested fix.** Moot if the 98% argument is removed per the Test 3 finding. If any version survives, write '$854,587 residual, 1.7% of the shortfall'.

### `code/verify_amounts_against_pdf.py:101 (`re.finditer(r"\b(\d{2})-?(\d{7})\b", line)`) — no test`

**Problem.** The optional dash is untested. Every EIN in the PAGE fixture is printed with a dash, so the `-?` branch that catches a bare 9-digit EIN in the PDF text is never exercised — even though the function's own docstring calls out the two forms. A PDF year printing bare EINs would silently fall to pdf_ein_absent.

**Evidence.**

```
V7  `r"\b(\d{2})-?(\d{7})\b"`  ->  `r"\b(\d{2})-(\d{7})\b"`  (dash required)
  : {"id":"V7","status":"SURVIVED  <-- test gap","failed":[],"summary":"14 passed in 0.01s"}
(The sibling script's identical regex IS covered — A8 on audit_appendix_overlap.EIN was CAUGHT by test_money_and_ein_forms.)
```

**Suggested fix.** Add one fixture line with a bare EIN (`Some Org 471234567 $12,500`) to PAGE, or mirror the sibling suite's direct regex test on ein_index().

### `DATA-DICTIONARY.md:67`

**Problem.** "the table of contents gives **each appendix** its own page numbering, restarting at page 1" overstates the evidence. The ToC restarts once per year, for the appendix block as a whole: Appendix A at page 1, B at 27, C at 150 — continuous within the block. The script's own column agrees: `restart at p1` = 1 per year, not 3.

**Evidence.**

```
FY2027 ToC scrape: "Appendix A: Aging Discretionary….Page 1 -26 / Appendix B: Local Initiatives….Page 27 - 149 / Appendix C: Youth Discretionary….Page 150 - 193". Script TEST 1 column "restart at p1" = 1 for FY2019–FY2027.
```

**Suggested fix.** "the table of contents gives the appendix block its own page numbering, restarting at page 1."

### `data/AMOUNT-AUDIT.md:47`

**Problem.** The main results table still lists `neighbour_bleed | 3 | 0.00% | $1,322,333` with its original meaning column and no withdrawal marker; the withdrawal is ~85 lines further down. A reader scanning the table sees a live finding.

**Evidence.**

```
sed -n '44,52p' data/AMOUNT-AUDIT.md (table row, unmarked) vs line 134 "Withdrawn, 2026-08-13. All three are false positives."
```

**Suggested fix.** Append "— **withdrawn 2026-08-13**" to the table row's meaning cell.

### `code/PARSING.md:401`

**Problem.** "All 440 are confirmed" flattens the two verdicts the artifact itself distinguishes: 399 `pdf_confirms` and 41 `pdf_confirms_weak`, where AMOUNT-AUDIT.md says of the weak rows "Corroborated but not pinned; a person should look." PARSING.md is the per-year processing manifest a reader consults for status.

**Evidence.**

```
code/PARSING.md:401 "All 440 are confirmed"; recomputed from data/AMOUNT-PDF-VERIFICATION.csv: pdf_confirms 399 ($22,481,361), pdf_confirms_weak 41 ($2,834,626).
```

**Suggested fix.** "All 440 are corroborated — 399 pinned to a single printed line, 41 not pinned."

### `DATA-DICTIONARY.md:5`

**Problem.** Header still reads "**Generated:** 2026-07-08" with no "Last revised" line, though the commit rewrote a load-bearing claim in it on 2026-08-13. data/AMOUNT-AUDIT.md in the same commit did add a "Last revised" line, so the two revised docs now follow different conventions.

**Evidence.**

```
head -6 DATA-DICTIONARY.md → "**Generated:** 2026-07-08. Covers FY2009–FY2027."; data/AMOUNT-AUDIT.md:12 → "**Last revised:** 2026-08-13 — ...".
```

**Suggested fix.** Add "**Last revised:** 2026-08-13 — appendix additive/subset correction" to DATA-DICTIONARY.md's header.

### `code/audit_appendix_overlap.py:181-195`

**Problem.** Dead computation in the shipped audit: `pairs()` is run over every body page range and every appendix page range for all 13 years, and `apx_pairs`, `body_pairs`, `overlap`, `overlap_odd` are stuffed into the result dict and never read by `main()`. It is the most expensive part of the run and produces nothing a reader ever sees — and it is plausibly where the unreproducible "84-96%" docstring figure came from.

**Evidence.**

```
`grep -n "overlap|apx_pairs|body_pairs" code/audit_appendix_overlap.py` → only the assignment at 194-195 plus comments at 184-185; `main()` prints only toc_appendices, toc_restarts_at_1, stream_hits, grand_total, awards_dollars, apx_dollars, ap_rows, twins*, so none of the four is ever consumed.
```

**Suggested fix.** Either print the PDF-level overlap as a fifth column (it is the only evidence at the printed-page level) or delete `pairs()` and the four unused fields.

### `code/PARSING.md:397 — "`audit_amounts.py` leaves 440 rows the disclosure has no opinion on"; PARSING.md:401 — "All 440 are confirmed"`

**Problem.** Two flattenings. (a) Only the 419 `ein_absent` rows are no-opinion; on the 18 `rounding` and 3 `neighbour_bleed` rows the disclosure has an opinion and disagrees — which is the whole reason the PDF check is interesting. (b) 'All 440 are confirmed' merges 399 `pdf_confirms` with 41 `pdf_confirms_weak`, a distinction AMOUNT-AUDIT.md is careful to preserve ('a person should look').

**Evidence.**

```
$ .venv/bin/python - (data/AMOUNT-PDF-VERIFICATION.csv)
  verdict(source audit): Counter({'ein_absent': 419, 'rounding': 18, 'neighbour_bleed': 3})
  pdf_confirms 399 $22,481,361 ; pdf_confirms_weak 41 $2,834,626 ; contradicts 0 ; ein_absent 0
```

**Suggested fix.** '440 rows the disclosure could not corroborate (419 no-opinion, 21 disagreements)' and 'all 440 corroborated — 399 pinned to one printed line, 41 not pinned'.

### `DATA-DICTIONARY.md:71 — "$5,000 is designated hundreds of times a year"`

**Problem.** Understated by an order of magnitude — the count is ~1,800-1,950 rows a year. The understatement runs against the doc's own argument (the more common $5,000 is, the cheaper a round-number twin).

**Evidence.**

```
$ .venv/bin/python - (awards + appendix rows with amount == 5000)
  FY2021: 1819
  FY2024: 1853
  FY2027: 1947
```

**Suggested fix.** 'designated roughly 1,900 times a year'.

### `code/PARSING.md:399 — "It caches page text under `build/pdftext/` (gitignored, ~8s to rebuild)"`

**Problem.** Timing is right for one script, but the directory holds two byte-identical copies of every year — fy{Y}.layout.txt (verify_amounts_against_pdf.py) and fy{Y}.pages.txt (audit_appendix_overlap.py) — from the same `pdftotext -layout` invocation. 62MB and two passes where 31MB and one would do.

**Evidence.**

```
$ cmp build/pdftext/fy2024.layout.txt build/pdftext/fy2024.pages.txt  ->  IDENTICAL
$ du -sh build/pdftext  ->  62M
$ time (pdftotext -layout over all 13 PDFs)  ->  8.167s total  (so '~8s' is correct per pass; a cold rebuild of both names is ~16s)
```

**Suggested fix.** Have both scripts share one cache filename (one helper, one path). Then '~8s' is literally true for the whole directory.

### `code/verify_amounts_against_pdf.py:107 — `return {int(m.group(1).replace(",", "")) for m in MONEY.finditer(line)}``

**Problem.** `MONEY`'s capture group is `[\d,]+`, which can match a run of commas with no digits. `int("")` then raises ValueError and aborts the whole run mid-year with a traceback rather than a verdict. Zero occurrences in the current 13 PDFs, so this is latent, but the script is read-only and re-runnable against future adopted PDFs, where a `$` adjacent to a stray comma from `-layout` column collapse is entirely plausible.

**Evidence.**

```
Scan of all 13 cached layout files: `occurrences that would raise: 0`. Synthetic proof: `V.amounts_on("Some Org 13-1234567 $, 500")` → `ValueError invalid literal for int() with base 10: ''`.
```

**Suggested fix.** Tighten the group to `(\d[\d,]*)`, or guard with `if not s: continue`.

### `code/verify_amounts_against_pdf.py:101 — `re.finditer(r"\b(\d{2})-?(\d{7})\b", line)``

**Problem.** The pattern will happily index a 9-digit run that is not an EIN, creating a false index entry: it matches `$123456789`, `page 123456789.`, `ID:987654321,`, `$449331208` and `Contract 20-1234567`. It correctly refuses to match inside a longer digit run (`1234567890` → no match) and refuses comma-formatted money and dashed phone numbers. I could not find a single false entry in this corpus — all 92,420 matches across 13 years, and all 974 index keys absent from the corpus EIN set, look like real EINs of organizations the corpus did not capture. So: latent hazard, not an active defect, and it is not the cause of any published number.

**Evidence.**

```
/tmp/p_einfp.py → `total EIN-regex matches: 92420  dashed: 27765  BARE 9-digit (no dash): 64655`; `index keys NOT present as an EIN anywhere in the corpus: 974 (occurrences: 2467)`; `of those, preceded by '$' or a digit/comma run: 0`. Top unmatched keys are ordinary awards, e.g. `453858268 x33 … Participatory Budgeting Project, Inc. 453858268 * 3,500`. Adversarial strings: `'$123456789 grand total' -> ['123456789']`, `'page 123456789.' -> ['123456789']`, `'tel 212-555-1234' -> []`, `'1234567890' -> []`, `'12,345,678' -> []`.
```

**Suggested fix.** Optional: require the match not be preceded by `$` or followed by a decimal point. Low value given the empirical result — worth a one-line comment recording that this was checked rather than a code change.

### `code/verify_amounts_against_pdf.py:107 and :142 — cents are dropped on both sides`

**Problem.** `amounts_on` captures only `[\d,]+` after `$`, so `$10,000.00` yields 10000; `ours = int(float(r["our_amount"] or 0))` truncates rather than rounds. Two figures that differ only in cents therefore confirm each other. FY2018 does print `.00` tails on award lines, so this is live, not hypothetical — and cents are exactly the granularity of the `rounding` verdict class this script is being used to settle.

**Evidence.**

```
604 `$n,nnn.cc` occurrences across the 13 layout files. A real confirming line from the artifact: `FY2018 fy18:331 ours=$10000 / pdf line: Vacca San Gennaro Senior Center 432061329 $10,000.00`. `int(float("5000.75"))` → 5000.
```

**Suggested fix.** Capture the decimal tail (`\$\s?([\d,]+(?:\.\d{2})?)`) and compare in cents, or state in the docstring that comparison is dollar-truncated — relevant because 18 of the 440 rows are in the `rounding` class.


## Claims independently recomputed as CORRECT

- Row count and shape: exactly 440 data rows + 1 header. Field-count histogram over the raw reader is Counter({16: 441}) — zero ragged rows, no embedded-newline surprises. Header is the 11 columns of AMOUNT-AUDIT-findings.csv plus the 5 new pdf_* columns, in the order the generator declares at code/verify_amounts_against_pdf.py:200.
- Encoding and line endings: valid UTF-8, no BOM, CRLF terminators, trailing newline present. CRLF matches every other CSV in the repo (data/AMOUNT-AUDIT-findings.csv, data/combined/*.csv, data/fy*/schedule_c/*.csv all CRLF), so this is repo convention, not drift. Only 3 distinct non-ASCII characters appear (en-dash x5, e-acute x4, right single quote x1), all inside organization names.
- The headline tally is exactly as claimed. I recomputed it from the file: pdf_confirms 399 rows / $22,481,361; pdf_confirms_weak 41 rows / $2,834,626; pdf_contradicts 0; pdf_ein_absent 0; pdf_no_source 0. Sum $25,315,987 across 440 rows.
- Input composition matches: the 440 rows are 419 ein_absent + 18 rounding + 3 neighbour_bleed, and data/AMOUNT-AUDIT-findings.csv holds 1,548 rows of which exactly those three verdicts total 440. The generator's TARGET_VERDICTS filter is faithful.
- Every pdf_verdict value is one of the five documented in the generator docstring. Set difference against {pdf_confirms, pdf_confirms_weak, pdf_contradicts, pdf_ein_absent, pdf_no_source} is empty. No undocumented or misspelled verdict.
- pdf_text is NOT fabricated provenance — this is the central check and it passes cleanly. For all 440 rows, ' '.join(dump[pdf_line-1].split())[:160] equals the stored pdf_text exactly: 0 mismatches. All 440 pdf_texts contain the row's own EIN (in one of the two printed forms) AND the confirming amount. 0 rows carry a foreign EIN.
- The 160-char truncation hides nothing material, unlike the earlier 120-char defect. 24 rows hit the cap; I diffed each truncated pdf_text against the FULL printed line and found 0 rows where truncation conceals an additional dollar amount and 0 where it conceals an additional EIN. A reader cannot be misled into thinking a line is cleaner than it is.
- pdf_line values are in range for every row: min 381, max 26,171, no zeros, no non-integers, and the per-year maximum is below that year's line count in all 13 years (e.g. fy2026 max cited 26,171 vs 26,192 lines). They are internally consistent — the defect is that they use a different line-numbering convention than standard tools, not that they point outside the document.
- No PII beyond what the source PDFs already publish. Regex sweep over organization, org_text_merged, pdf_text and belongs_to_ein returned 0 email addresses, 0 phone numbers, 0 SSN-shaped strings, 0 street addresses, 0 NY ZIPs, 0 URLs, 0 DOB markers. The only person names present are council-member surnames that poppler's -layout wraps onto the front of a row (Reynoso, Williams, Lander, Dromm, Cornegy...), which are elected officials printed in the adopted PDF.
- Byte-for-byte reproducible, warm AND cold. Warm re-run: `.venv/bin/python code/verify_amounts_against_pdf.py --out /tmp/repro1.csv` produced md5 4dfc5534896a406f20cf262d968a8b03, identical to the committed file (diff empty, 0.35s). Cold run with CACHE redirected to an empty /tmp dir, forcing all 13 pdftotext extractions from scratch: also byte-identical.
- The pdftotext cache is a faithful derivative of the committed PDFs. I re-ran `pdftotext -layout` independently on all 13 source PDFs into /tmp and compared: 13 of 13 byte-identical to build/pdftext/ (poppler 26.07.0). No hand-edited or stale cache content is feeding the artifact.
- This is NOT the issue #57 FOLLOW-UP 3 problem. The generator code/verify_amounts_against_pdf.py is committed in the same commit as the artifact; its input data/AMOUNT-AUDIT-findings.csv is git-tracked; its 13 source PDFs are among the 270 tracked files under source/. Confirmed the contrast: code/absorbed_award_candidates.csv is only READ (code/build_recovered_awards.py:30, `SRC = "code/absorbed_award_candidates.csv"`) and nothing in code/ writes it — that precedent complaint stands, and this file does not repeat it.
- Standing rules hold for this artifact. `git diff --name-only b7a2f7f ba90fce -- 'data/fy*'` returns 0 files. The generator has no --apply path (test_script_writes_no_data_file guards it). No 'member' column exists in the artifact. All 440 (file,line) pointers into the live source CSVs resolve to the same (ein, amount) the artifact records — 440 ok / 0 bad / 0 missing — and none of the 32 referenced source files has any csv-row vs physical-line drift, so the `line` column, unlike `pdf_line`, is safe to follow with sed.
- The 'ambiguity affects 43 of the 440' figure in data/AMOUNT-AUDIT.md:169 reconciles against the file: 41 pdf_confirms_weak + 2 pdf_confirms rows carrying a non-empty org_text_merged = 43. (7 rows total carry org_text_merged; 5 weak + 2 confirms.)
- The three withdrawn neighbour_bleed rows check out. All 3 are pdf_confirms with pdf_ein_lines=1 — the EIN appears on exactly one line all year, so the pin does not rest on a name heuristic — and their pdf_text matches the table printed in AMOUNT-AUDIT.md verbatim: fy15:646 'Coalition for Asian American Children and Families 13-3682471 $833,333', fy23:585 "Mayor's Office of Criminal Justice 13-6400434 $325,000", fy25:3465 'Community Service Society of New York 13-5562202 $164,000'.
- The 18 rounding rows do back OUR figure, and I stress-tested the claim rather than taking it. Composition: 13 pdf_confirms + 5 pdf_confirms_weak. In 17 of 18 the disclosure's competing figure appears nowhere under that EIN anywhere in the year's PDF. The single exception, fy2016:83, survives inspection and actually strengthens the claim: EIN 13-3098397 is shared by three distinct Neighborhood Housing Services affiliates, and the dump shows line 4047 'Neighborhood Housing Services of Bedford-Stuyvesant $29,730', line 4048 'Neighborhood Housing Services of East Flatbush $29,731' (our row, name-pinned), line 4050 'of the North Bronx $29,730' — the disclosure's 29,730 belongs to a sibling organization, not to our row.
- $5,476,070,836 — CORRECT as arithmetic. Summing the `printed` column of the GRAND TOTAL line across the 13 `data/fy*/schedule_c/fy*_schedule_c_reconciliation.txt` files gives exactly $5,476,070,836. (Per-year: 233,438,000 / 333,886,574 / 279,908,300 / 302,086,000 / 338,301,000 / 404,372,774 / 304,268,931 / 465,728,895 / 486,446,095 / 471,875,565 / 534,913,682 / 665,080,021 / 655,764,999.)
- $5,474,660,271 — CORRECT. Summing the `amount` column of all 13 `*_schedule_c_initiatives.csv` files gives exactly $5,474,660,271, and it is identical to the sum of the reconciliation files' `initiatives` column.
- $3,741,615,569 — CORRECT. awards $3,388,618,294 + appendices $352,997,275 = $3,741,615,569 exactly, summing every `*_schedule_c_awards.csv` and `*_appendix_*.csv` across 13 years.
- 68.3% — CORRECT as division. 3,741,615,569 / 5,476,070,836 = 68.3266%, rounds to 68.3%.
- 0.026% — CORRECT as division. |5,476,070,836 − 5,474,660,271| / 5,476,070,836 = 0.0258%, rounds to 0.026%. (Net only; gross absolute delta is 0.0296%.)
- $1.73B — CORRECT as division. 5,476,070,836 − 3,741,615,569 = $1,734,455,267.
- 62,213 rows — CORRECT. The award + appendix row count reproduces at 62,213 across FY2015–FY2027.
- Standing rules on the two new scripts — CLEAN. `git diff --name-only b7a2f7f ba90fce -- 'data/fy*'` returns nothing (no data file under data/fy* modified). Neither script has an `--apply` path; `verify_amounts_against_pdf.py` writes only its own artifact CSV via `--out`, and `audit_appendix_overlap.py` writes nothing at all.
- fy15_schedule_c_awards.csv:646 — the adopted FY2015 Schedule C prints the row intact. /tmp/pdfaudit/fy15.txt:3523 reads `Coalition for Asian American Children and Families    13-3682471    $833,333`, immediately followed by Hispanic Federation 13-3573852 $833,333 and New York Urban League 13-1671035 $833,333 under the header 'Communities of Color Non-Profit Stabilization Fund  $2,500,000'. Our row matches name, EIN and amount. NOT a bled row.
- fy23_schedule_c_awards.csv:585 — /tmp/pdfaudit/fy23.txt:1877 reads `Mayor's Office of Criminal Justice    13-6400434    $325,000`. Our row matches. NOT a bled row.
- fy25_schedule_c_awards.csv:3465 — /tmp/pdfaudit/fy25.txt:7950 reads `Community Service Society of New York    13-5562202    $164,000`. Our row matches. NOT a bled row.
- Independent arithmetic confirmation the commit did not perform — each of the three printed provider tables sums to its own printed initiative total ONLY with our figure included. FY15 Communities of Color: 833,333 x 3 = $2,499,999 vs printed $2,500,000 (the source's own $1 rounding); all three rows present at fy15:646/647/648. FY23 Innovative Criminal Justice Programs: 100,000+200,000+458,000+325,000+500,000+339,948+325,000+50,000+265,000+75,000 = $2,637,948 = printed total exactly, and BOTH $325,000 lines (FCNY–A More Just NYC and MOCJ) are genuine and distinct. FY25 Citywide Homeless Prevention Fund: 164,000+492,000+164,000 = $820,000 = printed total exactly; all three at fy25:3463/3464/3465.
- The `pdf_text` strings quoted in AMOUNT-AUDIT.md's withdrawal table are verbatim-accurate for all three rows (whitespace-collapsed). The FY17 quote at AMOUNT-AUDIT.md:165 is also accurate — /tmp/pdfaudit/fy17.txt:4527 reads `Brooklyn Defenders Services  11-3305406  $2,076,666`.
- The pin for all three rows is genuinely unique, not an artifact of the 18-character `names_us` truncation. Re-running the script's own helpers: FY15 ein_lines=9, exactly 1 line carries the amount, that line names us; FY23 ein_lines=483, exactly 1 carries the amount, names us; FY25 ein_lines=10, exactly 1 carries the amount, names us. All three are correctly classed `pdf_confirms` rather than `pdf_confirms_weak`.
- NO EIN DISAGREEMENT at fy25:3465, and no undetected defect there. The task brief's premise misreads the `belongs_to_ein` column, which audit_amounts.py:243-250 defines as the EIN that UNIQUELY OWNS THE AMOUNT in the disclosure — a neighbour's EIN — not the disclosure's EIN for our organization. 13-5562202 is Community Service Society of New York in BOTH Council sources (adopted PDF line 7950 and 4 other lines; disclosure by_org[(135562202,'communityservicesocietyofnewyork')] carries 170469/230469/100000/50000/5000x3/10000x2). 13-3824852 is a different organization, The Bridge Fund of New York, Inc. — printed on the line above ours in the same table, present in the disclosure under that name, and correctly carried at fy25:3463 in our own data. Two organizations, two correct EINs, same $164,000 award size.
- The commit's headline tallies reproduce exactly. `.venv/bin/python code/verify_amounts_against_pdf.py --out /tmp/pdfaudit/RERUN.csv` prints pdf_confirms 399 $22,481,361 / pdf_confirms_weak 41 $2,834,626 / no pdf_contradicts / no pdf_ein_absent, and `diff data/AMOUNT-PDF-VERIFICATION.csv /tmp/pdfaudit/RERUN.csv` is empty. The `build/pdftext/*.layout.txt` cache is byte-identical to a fresh `pdftotext -layout` run I made into /tmp (diff -q clean, 18023 lines each for FY15).
- No standing-rule violation found in the verify script itself: it joins on (EIN, amount), never fills `member`, has no --apply path, and modified no file under data/fy* (git diff --stat b7a2f7f ba90fce touches only .gitignore, DATA-DICTIONARY.md, README.md, code/PARSING.md, four code files, data/AMOUNT-AUDIT.md and the new data/AMOUNT-PDF-VERIFICATION.csv).
- Scope of the diff: 10 files, 1202 insertions / 4 deletions. `git diff main..HEAD --name-only | grep -E '^data/fy'` returns 0 files. `grep -E '^data/combined'` returns 0 — data/combined/org_name_recovery_crosswalk.csv is NOT modified. `source/`, `mcp/`, and viz/docs paths all return 0. The only data/ changes are data/AMOUNT-AUDIT.md (M) and data/AMOUNT-PDF-VERIFICATION.csv (A).
- code/verify_crosswalk.py: exit 0 on HEAD and exit 0 on a clean /tmp clone of main; stdout byte-identical between the two (`diff` exit 0). Reports 5450 entries, COMPLETE 5450/5450, GROUNDED 5450/5450, UNIQUE 5450/5450, ACCOUNTED 0 unexplained cell changes vs main.
- code/verify_no_dollars_moved.py: exit 0. All 13 fiscal years show delta 0. TOTAL 3,741,615,569 on both main and HEAD — I recomputed this and it equals the published headline exactly, confirming the headline includes appendix rows (the script's glob excludes only *initiatives* and *reconcil*).
- code/validate_data.py: exit 0 on HEAD and exit 0 on main; the 111-line stdout is byte-identical (`diff` exit 0), and data/QA-REPORT.md regenerates byte-identical on both (`cmp` reports IDENTICAL; git status clean after the run).
- pytest: 150 passed, exit 0, 177.09s on HEAD. main collects 136 tests. The delta is exactly the 14 tests in the two new test files — no existing test was removed, renamed, or skipped.
- The .gitignore addition ignores nothing already tracked: `git ls-files -z | xargs -0 git check-ignore` matches 0 files, and `git ls-files build/` returns 0 files (build/ has never been tracked).
- The .gitignore addition does not touch PR #43's OCR pipeline. I enumerated the paths that pipeline writes from pr43:code/ocr/install-and-run.md and pr43:code/parse_transparency_reso_fy09.py (DEFAULT_CACHE = "build/ocr") and ran git check-ignore on each: build/ocr/<stem>/raw/*.png, upright/*.png, orient.json, pages.csv, grid/*.json, cells/*.json, debug/*-grid.png — all report not-ignored. Only build/pdftext/* is ignored. `build/other.txt` also not-ignored, confirming the rule is path-scoped and not a stray build/ wildcard.
- No merge regression against PR #43. `git merge-tree --write-tree HEAD pr43` reports "Auto-merging .gitignore" with no conflict (pr43 adds a broader `build/` rule; the two coexist, redundantly but harmlessly). The three conflicts it does report — DATA-ANOMALIES.md, code/PARSING.md, data/QA-REPORT.md — are byte-for-byte the same conflicts `git merge-tree --write-tree main pr43` produces, and the merge base is identical (8a589a8) for both. Pre-existing, not introduced by this commit.
- Neither new script has an --apply path. `grep -niE 'apply|--force|--clean'` over both files returns exactly one hit: the docstring line forbidding one. The only write modes anywhere in either file are `open(args.out, "w")` in verify_amounts_against_pdf.py:202 and the two `pdftotext` cache writes under build/pdftext/. No os.remove, shutil, unlink, rmtree, rename, or to_csv in either file.
- Running both scripts leaves the tree clean. `git status --porcelain` is empty after verify_amounts_against_pdf.py (exit 0, 0.37s) and after audit_appendix_overlap.py (exit 0, 0.66s). audit_appendix_overlap.py writes no file at all outside the cache. verify_amounts_against_pdf.py's one output is byte-identical to the committed copy (`cmp` IDENTICAL against `git show HEAD:data/AMOUNT-PDF-VERIFICATION.csv`) — the artifact is deterministic and reproducible.
- Blocker-1 tallies reproduce exactly, both from a fresh run and from the committed CSV: 440 input rows (419 ein_absent + 18 rounding + 3 neighbour_bleed), 399 pdf_confirms totalling $22,481,361, 41 pdf_confirms_weak totalling $2,834,626, and zero rows in pdf_contradicts, pdf_ein_absent, or pdf_no_source.
- Blocker-2 arithmetic reproduces: 0 of 13 years where awards + appendices exceed the printed GRAND TOTAL; FY2027 shortfall $50,653,587 against appendices of $49,799,000 = 98% (residual $854,587 = 0.13%); upper bound on double-counting $447,500. Cross-check: FY2018 awards $102,716,956 + appendices $4,419,275 = $107,136,231, which matches verify_no_dollars_moved.py's independent fy18 total exactly.
- The 68.3% ratio: $3,741,615,569 / $5,476,070,836 = 68.33%. I recomputed both sides. And the FY2015–FY2027 initiatives sum is $5,474,660,271, which is $1,410,565 below the printed $5,476,070,836 = 0.0258%, matching the claimed 0.026% (see finding on the missing year qualifier).
- CI is unaffected: ci.yml's path filter (mcp/**) excludes every file in this diff, and the version-guard job's three-dot diff over `mcp/src mcp/scripts mcp/package.json data/combined` is empty, so it takes the "not applicable. Passing" branch. No version bump is owed.
- No standing-rule violation in the new code. verify_amounts_against_pdf.py never accepts an EIN-alone match — `carrying` requires the amount on the same printed line, and a single-line-or-named-org test gates pdf_confirms. audit_appendix_overlap.py's `pairs()` and `twins()` both key on (EIN, amount[, organization]); `member` appears in no key expression in either file.
- Reproduced the script's full output verbatim on commit ba90fce: `.venv/bin/python code/audit_appendix_overlap.py` in 0.66s. Every headline number in the commit claim matches — TEST 3 'years where awards + appendices exceed the Council's own total: 0 of 13'; award rows $3,388,618,294; appendix rows $352,997,275; published headline $3,741,615,569; 'Council's own printed GRAND TOTALs' $5,476,070,836; '68.3% of it'; 'upper bound on double-counting ... $447,500'.
- (b) probe answered NO — group(2) is NOT the parser's computed total, so Test 3 is not inverted. parse_schedule_c.py:360 writes the header as `{'CATEGORY':52} {'initiatives':>14} {'printed':>14}  status` and :363-365 accumulates gi from isum (the parser's sum of the initiative line items it extracted) and gp from recon (the printed `TOTAL $x` line closing each summary block), emitting `{gi:>14,} {gp:>14,}`. So group(1)=gi=parser-computed, group(2)=gp=printed-subtotals. grand_total() taking group(2) is the correct column. The defect is a different one (there is no printed GRAND TOTAL in the PDF at all, and gp drops no-summary-block categories) — see finding 1.
- (e) probe: the body page arithmetic is correct. `pages[body_lo-1:body_hi]` maps 1-indexed inclusive pages body_lo..body_hi correctly given pdftotext's form-feed split, and `pairs()` guards `1 <= p <= len(pages)`. apx_lo = min(apx.values()) = Appendix A's page = body_hi+1 in all 13 years, so the body and appendix ranges are disjoint and jointly cover pages 6..end with no page counted twice. Pages 1-5 (cover, ToC, contents) are correctly excluded from the body scan — they are where the appendix names legitimately appear.
- FY2027 arithmetic recomputed and CORRECT: 655,764,999 - 605,111,412 = 50,653,587 shortfall; 5,610,000 + 36,539,000 + 7,650,000 = 49,799,000 appendices; 49,799,000 / 50,653,587 = 98.31% ('98%'); residual 854,587 / 655,764,999 = 0.1303% ('0.13%'). FY2027 is also the one year with zero per-category overshoot (0 of 25), so it is genuine evidence for additivity — it is the other twelve years that are not.
- Under-capture arithmetic recomputed and CORRECT: 5,476,070,836 - 3,741,615,569 = 1,734,455,267 ('$1.73B'); 3,741,615,569 / 5,476,070,836 = 68.327% ('68.3%'). Correct as arithmetic; the denominator's provenance is the problem, not the division.
- Row-count arithmetic recomputed and CORRECT: 33,638 award rows + 28,575 appendix rows = 62,213, and $3,388,618,294 + $352,997,275 = $3,741,615,569, matching the published headline exactly.
- The *_schedule_c_initiatives.csv claim is CORRECT but year-scoped: FY15-FY27 sums to exactly $5,474,660,271 over 1,900 rows, 0.0258% below $5,476,070,836 ('within 0.026%'). Note that across ALL years present in data/ (FY09-FY27) the same glob sums to $7,363,002,422 over 2,598 rows, so the claim silently excludes FY09-FY14.
- (c) probe answered: csv_total does correctly exclude the initiatives and reconciliation files and does NOT double-count. The two globs are disjoint, match exactly one awards file and three appendix files per year, and there are no stray *_appendix_*.csv or extra *_schedule_c_awards.csv files in any of the 13 directories. csv_total's appendix row count agrees with twins()'s independently loaded ap_rows for every year.
- (d) probe answered: the twins() globs match the intended files and only those — `*_schedule_c_awards.csv` -> 1 file, `*_appendix_*.csv` -> the 3 appendix files, per year, verified by ls across all 13 years. Zero appendix rows have a blank EIN in any year, so there is no spurious ('', amount, '') self-matching. The key-narrowing issue is a separate finding.
- code/test_audit_appendix_overlap.py passes: `.venv/bin/pytest code/test_audit_appendix_overlap.py -q` -> 7 passed in 0.01s. It genuinely verifies that pairs() over-pairs rather than under-pairs, that the round/distinctive split treats 5000 as round and 29730 as distinctive, and that the script opens no file for writing.
- Test 1's underlying document fact is CORRECT where the regex fires: the FY2027 ToC numbers the body continuously (Introduction 1, Anti-Poverty 3, Boroughwide Needs 4, ... Housing ...) and the appendices restart at Page 1. The 'own pagination' observation is real; only its year coverage is wrong.
- The FY2026 and FY2023 per-category overshoots are not explained away by the parser's ToC-order block mapping: both years report 'categories from ToC: N | summary blocks found: N' with no MISMATCH flag, unlike FY2016-2022/2024/2025.
- 440 total rows targeted: data/AMOUNT-AUDIT-findings.csv has exactly 440 rows with verdict in (ein_absent, rounding, neighbour_bleed) — Counter({'ein_absent': 419, 'rounding': 18, 'neighbour_bleed': 3}). I got 440, 419/18/3.
- The 399/41/0/0 split: my independently-written verifier (own regexes, own pinning logic, own fresh pdftotext -layout extraction into /tmp) returns pdf_confirms=399, pdf_confirms_weak=41, pdf_contradicts=0, pdf_ein_absent=0. I got 399/41/0/0.
- $22,481,361 (pdf_confirms) and $2,834,626 (pdf_confirms_weak): I got exactly $22,481,361 and $2,834,626. Their sum $25,315,987 also equals the earlier table's ein_absent $18,308,251 + rounding $5,685,403 + neighbour_bleed $1,322,333 = $25,315,987, so the two sections are internally consistent.
- Row-for-row agreement with the shipped artifact: comparing my 440 results against data/AMOUNT-PDF-VERIFICATION.csv gives 0 verdict mismatches, 0 pdf_line mismatches, 0 pdf_ein_lines mismatches. The CSV is not fabricated and is exactly what the stated method produces.
- 'All 440 have their (EIN, amount) pair printed together on ONE line': confirmed — 0 contradicts and 0 ein_absent means every row had at least one line carrying both. Robustness checks: result is unchanged (399/41) under a broader money regex that also reads amounts printed without a '$'; 0 of the 440 confirming lines print more than one distinct dollar amount; 0 confirming lines carry more than one EIN. So no confirm is an artifact of pdftotext -layout merging two columns onto one row.
- Control 1, every amount corrupted by +$7: I got 440/440 pdf_contradicts, 0 confirms, 0 weak. Reproduces exactly.
- Control 2, an amount planted that appears on no line of that EIN: I got 440/440 pdf_contradicts, 0 confirms, 0 weak. Reproduces exactly. The mechanism test holds.
- The three neighbour_bleed PDF lines, verbatim from my own extraction: FY2015 line 3605 = 'Coalition for Asian American Children and Families    13-3682471    $833,333'; FY2023 line 1920 = "Mayor's Office of Criminal Justice    13-6400434    $325,000"; FY2025 line 8107 = 'Community Service Society of New York    13-5562202    $164,000'. All three match the doc's quoted text after whitespace collapse. The withdrawal is correct — each row's name, EIN and amount are printed together, nothing bled.
- fy17_schedule_c_awards.csv:209 — the PDF does print our figure. FY2017 line 4616 = 'Brooklyn Defenders Services    11-3305406    $2,076,666' and the immediately preceding line 4615 = 'Bronx Defenders    13-3931074    *    $2,076,667', which is §20's merge story exactly. Our $2,076,666 is backed; the disclosure's $2,076,667 belongs to the neighbouring EIN.
- All 18 rounding rows: our figure is printed under our EIN in the PDF in 18/18. In 17 of 18 the disclosure's competing figure appears nowhere under that EIN. The one exception (fy16:83, EIN 13-3098397, ours $29,731 vs disclosure $29,730) resolves in the doc's favour on inspection — line 4048 prints 'Neighborhood Housing Services of East Flatbush 13-3098397 $29,731' (ours), while the $29,730 under that EIN sits on lines 4047 and 4050 belonging to the Bedford-Stuyvesant and North Bronx affiliates. So 'the PDF backs our figure, not the disclosure's — all 18' holds.
- '483 separate lines' exists as a real measurement: max(pdf_ein_lines) in the shipped CSV is 483, and my own count confirms EIN 13-6400434 appears on exactly 483 lines of the FY2023 Schedule C. (The year and EIN are misattributed in two docstrings — filed separately — but the number itself is real.)
- The two named rotation examples check out: FY2021 EIN 13-5562162 (Helen Keller International) carries $24,000 (line 10299), $2,500 (10301) and $25,000 (15382) — plus $5,000, which the doc does not claim to be exhaustive about. FY2020 EIN 51-0204121 (JSPOA) carries both $20,000 (lines 7763, 8097) and $10,000 (line 8098).
- Headline corpus figures in the amended header section: summing every data/fy*/schedule_c/*_awards.csv and *_appendix_*.csv gives 62,213 rows and $3,741,615,569. I got 62,213 and $3,741,615,569 — both exact.
- The 'two engines' claim is true: code/parse_schedule_c.py:50-51 uses pypdf.PdfReader().extract_text(); verify_amounts_against_pdf.py shells out to `pdftotext -layout` (poppler 26.07.0). Independent readers.
- Standing rules held by the commit: `git diff --name-only b7a2f7f ba90fce | grep '^data/fy'` returns nothing (0 data files under data/fy* modified); no --apply path in verify_amounts_against_pdf.py or audit_appendix_overlap.py (the only 'apply' string is the docstring explaining why there isn't one); `pytest code/test_verify_amounts_against_pdf.py -q` -> 7 passed. The shipped build/pdftext cache is byte-identical (sha256) to my own fresh extraction for all 13 years, so nothing was hand-edited into the cache.
- The amended header date: `date` returns 2026-08-13 09:07 EDT, matching the 'Last revised: 2026-08-13' line and the new section's 'Report generated: 2026-08-13'.
- The withdrawn-finding note's substantive claim ('what the disclosure records is a different EIN holding the same amount'): in all three rows belongs_to_ein differs from our ein — 13-3573852 vs 13-3682471, 13-2612524 vs 13-6400434, 13-3824852 vs 13-5562202. For fy15:646 the PDF prints 'Hispanic Federation 13-3573852 $833,333' on the very next line (3606), i.e. two genuinely separate awards of the same size, not a bled row.
- Appendix CSV totals per year: FY2027 aging $5,610,000 / local $36,539,000 / youth $7,650,000, summing to $49,799,000 — I recomputed from data/fy27/schedule_c/*_appendix_*.csv and got the same.
- FY2027 category GRAND TOTAL $655,764,999 — I re-summed the 25 'printed' values in fy27_schedule_c_reconciliation.txt and got 655,764,999.
- FY2027 awards CSV total $605,111,412 across 6,118 rows, shortfall vs category total = $50,653,587 — recomputed, matches.
- 13-year sum of per-year category grand totals = $5,476,070,836 — recomputed by summing grand_total() across the 13 PDFS years, matches the published figure.
- 13-year sum of *_schedule_c_initiatives.csv = $5,474,660,271, i.e. 0.0258% below $5,476,070,836 — recomputed, matches the published 0.026%.
- Published headline $3,741,615,569 = awards $3,388,618,294 + appendices $352,997,275 over the 13 PDF years — recomputed, matches; and 3,741,615,569 / 5,476,070,836 = 68.327%, so the published 68.3% is arithmetically right for that (mis-scoped) denominator.
- '0 of 13 years overshoot' — recomputed; awards+appendices is below the category total in all 13 years, so the stated result is factually true (though it cannot fail; see findings).
- '75-100% of appendix rows have no (EIN, amount, organization) twin' — recomputed: FY2018 100%, FY2027 75%, FY2025 77%, FY2024/FY2026 78%. True as stated.
- code/test_audit_appendix_overlap.py: 7 passed in 0.01s via .venv/bin/pytest.
- No data file under data/fy* was modified by this commit — `git diff --name-only b7a2f7f ba90fce -- 'data/fy*'` returns nothing, and `git status --porcelain` is clean.
- THE CONCLUSION ITSELF: appendices are ADDITIVE. Independently confirmed against the Council's own FY2027 disclosure workbook — disclosure total $705,564,000 vs category grand total $655,764,999 plus streams $49,799,000 = $705,563,999 ($1 delta), and the per-stream row counts and dollars match the appendix CSVs exactly (467/2,558/835 rows).
- Full suite count: CONFIRMED at 150. `/Users/noneck/Code/New-York-City-Budget/.venv/bin/pytest code/ -q` on ba90fce with a clean tree -> "150 passed in 172.76s (0:02:52)". Exit 0, zero failures, zero skips.
- The two new test files contribute exactly 14 tests (7 + 7): `pytest code/test_verify_amounts_against_pdf.py code/test_audit_appendix_overlap.py -q` -> "14 passed in 0.01s". Both run without touching data/ (fixtures are in-memory; pdf_lines is monkeypatched), so they are fast and hermetic.
- code/test_verify_amounts_against_pdf.py DOES have real teeth on the core verdict logic. 11 of 18 mutations I applied to verify_amounts_against_pdf.py were caught, including every one that would launder an unverified number: V1 pinned=True (the documented original bug -> caught by test_multi_line_ein_without_our_name_is_only_weak), V10 accept any line under the EIN regardless of amount (caught), V8 pdf_contradicts->pdf_confirms (caught), V9 pdf_ein_absent->pdf_confirms (caught), V3 drop the name-match rule (caught), V15 ignore the name-bearing line (caught), V16 names_us always False (caught), V17 names_us always True (caught), V6 comma-stripping removed from amounts_on (caught by 5 tests). The mechanism test named in the docstring as "if it ever fails, every other result in the file is meaningless" — test_amount_absent_from_the_ein_never_confirms — is genuine and killed 3 separate mutations.
- code/test_audit_appendix_overlap.py's pairs() and regex-form tests are genuine, not vacuous. A3 (positional zip instead of cross product) was caught by test_pairs_is_deliberately_generous; A4 (drop the page-range bounds check) was caught by test_pairs_ignores_pages_outside_the_range; A7 (MONEY loses comma handling) and A8 (EIN requires the dash) were caught by test_money_and_ein_forms; A2 (ToC regex matches nothing) and A19 (ToC regex loses the (?i) flag) were caught by both ToC tests.
- Overall mutation kill rate, recomputed from 41 applied mutations (all applied to a /tmp copy at /tmp/nycb-audit, never the real repo): 17 caught, 24 survived. Split by file: verify_amounts_against_pdf.py 11 caught / 7 survived = 61% kill; audit_appendix_overlap.py 6 caught / 17 survived = 26% kill. The weaker of the two suites is the one backing the claim that REVERSES published DATA-DICTIONARY.md wording.
- Read-only constraint honored: after all mutation work, `git status --porcelain` in /Users/noneck/Code/New-York-City-Budget is empty and HEAD is still ba90fce; `diff -q` confirms both /tmp copies were restored byte-identical to the repo originals. No script was run with --apply; no file under data/fy* was touched.
- data/AMOUNT-PDF-VERIFICATION.csv holds exactly 440 rows; recomputed verdict split is pdf_confirms 399 = $22,481,361 and pdf_confirms_weak 41 = $2,834,626, with zero pdf_contradicts and zero pdf_ein_absent rows present. Matches the claim exactly.
- Input verdict mix of the 440 rows recomputed from the same CSV: 419 ein_absent + 18 rounding + 3 neighbour_bleed = 440. Matches.
- All three neighbour_bleed rows carry pdf_verdict=pdf_confirms in the artifact, with pdf_text showing name+EIN+amount on one line (e.g. fy15:646 "Coalition for Asian American Children and Families 13-3682471 $833,333"). The withdrawal is supported by the shipped artifact.
- TEST 3 reproduced by running code/audit_appendix_overlap.py: awards + appendices exceed the printed GRAND TOTAL in 0 of 13 years. I got 0.
- Corpus totals reproduced from the script: award rows $3,388,618,294 + appendix rows $352,997,275 = $3,741,615,569 headline; Council printed GRAND TOTALs $5,476,070,836; ratio 68.3%. All three match.
- Independently summed data/fy{15..27}/schedule_c/*_schedule_c_initiatives.csv and got $5,474,660,271 — the published figure to the dollar. Gap to the $5,476,070,836 printed total is $1,410,565 = 0.0258%, so "within 0.026%" is correct.
- FY2027 arithmetic recomputed: GRAND TOTAL $655,764,999, awards $605,111,412, shortfall $50,653,587, appendices $49,799,000 = 98.3% coverage, residual $854,587 = 0.130% of the grand total. Matches.
- TEST 4 upper bound reproduced: distinctive (non-round-thousand) twin dollars sum to $447,500 across 13 years = 0.01196% of $3,741,615,569, i.e. the published 0.012%.
- TEST 4 no-twin share reproduced: 75% (FY2027) to 100% (FY2018), matching DATA-DICTIONARY's "75–100%".
- No file under data/fy* is touched by the commit — `git diff --name-only b7a2f7f ba90fce | grep '^data/fy'` returns nothing. Only data/AMOUNT-AUDIT.md and data/AMOUNT-PDF-VERIFICATION.csv change under data/.
- Neither new script has an --apply path. code/audit_appendix_overlap.py opens no file for writing at all; code/verify_amounts_against_pdf.py writes only its --out CSV (line 202). Both claims hold.
- 150 tests pass on ba90fce: `.venv/bin/pytest code -q` → "150 passed in 173.61s". The 150 is correct (the 143 baseline is not — see findings).
- The .gitignore addition is correctly scoped to build/pdftext/ rather than all of build/, as the comment claims.
- The MCP response footer states NO dollar total — FOOTER (mcp/src/server.ts:35-37) and SCOPE_NOTE (line 33) carry coverage years only. This commit's conclusion does not affect any footer figure. Same for mcp/dist/server.js:13.
- The "SUBSET" wording in mcp/README.md:32, mcp/src/db.ts:306, mcp/src/server.ts:467 and mcp/test/appendix-ingest.test.js:178 refers to the appendix FISCAL YEARS being a subset of the award years, not to rows or dollars. These are correct as written and do NOT carry the reversed claim — no change needed.
- The README.md anchor DATA-DICTIONARY.md#datayearschedule_cyear_appendix_csv resolves correctly against the heading `## \`data/{year}/schedule_c/{year}_appendix_*.csv\``, and #settled-against-the-adopted-pdf resolves against "## Settled against the adopted PDF".
- The FY2026 TEST-2 hit is genuinely a purpose sentence, not a line item: "Millennium Development - Community Development - Council ... Funds will be used to support community development, event programming, and local initiatives". The doc's parenthetical is accurate; only the surrounding "zero times" wording is not.
- Body hits for the alternate names "Aging Initiative"/"Youth Initiative" (1-3 per year in FY2016-FY2020, FY2023-FY2027) are all unrelated — "Healthy Aging Initiative" (a distinct DFTA citywide initiative), "Fresh Youth Initiatives, Inc." (an org name), "Court Involved Youth Initiative" (a program). TEST 2's substantive conclusion survives; only its stated coverage is overstated.
- ToC quote is verbatim in the FY2024 PDF. My own `pdftotext -layout source/FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf` line 82 reads exactly `APPENDIX A: AGING DISCRETIONARY….PAGE 1 - 26` (U+2026 ellipsis, spaced hyphen). Lines 83-84 give B 27-147 and C 148-189.
- Stream names in body pages, recomputed per year from my own extraction (not the repo cache): FY2015-FY2025 and FY2027 = 0 hits for all three names; FY2026 = exactly 1 hit ('local initiatives'). Total across 13 years = 1, matching the script's output column.
- The FY2026 hit is prose, as the doc says. Body page 52: 'Funds will be used to support community development, event programming, and local initiatives that enhance quality of life for residents in Council District 42.' — a purpose field on a $10,000 DYCD row, not a line item.
- Overshoot count = 0 of 13. I re-summed awards and appendix CSVs myself for all 13 years and compared to each year's reconciliation total; awards+appendices is below the total in every year. FY2027 comes closest (654,910,412 vs 655,764,999).
- FY2027 arithmetic, all four numbers: shortfall 655,764,999 - 605,111,412 = $50,653,587; appendices 5,610,000 + 36,539,000 + 7,650,000 = $49,799,000; coverage 98.313% -> 98%; residual $854,587.
- FY2027 '25/25 categories exact' — data/fy27/schedule_c/fy27_schedule_c_reconciliation.txt GRAND TOTAL row reads `655,764,999  655,764,999  25/25 categories exact`, and the initiatives and printed columns agree on every one of the 25 rows.
- '75-100% of appendix rows have no (EIN, amount, organization) twin' — my independent recompute gives 75.3% (FY2027), 77.0% (FY2025), 77.5% (FY2026), 77.8% (FY2024), 90.9% (FY2022), 91.1% (FY2023), 92.8% (FY2021), 100.0% (FY2018). Range 75-100%, correct.
- $447,500 upper bound — 109 appendix rows across 13 years have an exact (EIN, amount, organization) twin among that year's awards AND a non-round-thousand amount, summing to exactly $447,500. As a share of the headline that is 0.01196% -> 0.012%, as published.
- Headline $3,741,615,569 / 62,213 rows — my own sum of every fy15-fy27 awards CSV gives 33,638 rows / $3,388,618,294, and every appendix CSV gives 28,575 rows / $352,997,275. Totals match exactly.
- $5,476,070,836 — sum of the 13 reconciliation 'printed' columns, recomputed independently: matches to the dollar. (See finding 1 for what this figure actually is.)
- 68.3% — 3,741,615,569 / 5,476,070,836 = 68.3266%. Correct. Under-capture 5,476,070,836 - 3,741,615,569 = $1,734,455,267, i.e. the commit's '$1.73B'.
- $5,474,660,271 and 0.026% — summing every fy15-fy27 *_schedule_c_initiatives.csv gives exactly $5,474,660,271 (1,900 rows). Delta to $5,476,070,836 is $1,410,565 = 0.02576% -> 0.026%. (Note the 19-year initiatives sum is $7,363,002,422 against $7,364,662,987, 0.023% — the 13-year framing is the right comparison and is what was published.)
- BLOCKER 1 tallies — data/AMOUNT-PDF-VERIFICATION.csv has 440 rows: 399 pdf_confirms / $22,481,361 and 41 pdf_confirms_weak / $2,834,626, 0 pdf_contradicts, 0 pdf_ein_absent. Source verdicts 419 ein_absent + 18 rounding + 3 neighbour_bleed = 440. All as published.
- '43 of the 440' — the union of the 41 pdf_confirms_weak rows and the 7 rows with org_text_merged='yes' (5 overlap) is exactly 43.
- The three withdrawn neighbour_bleed rows — the quoted PDF lines in AMOUNT-AUDIT.md match the artifact character for character: 'Coalition for Asian American Children and Families 13-3682471 $833,333', "Mayor's Office of Criminal Justice 13-6400434 $325,000", 'Community Service Society of New York 13-5562202 $164,000'. All three verdict pdf_confirms.
- 'On all 18 rounding rows the PDF backs our figure, not the disclosure's' — 18 of 18. On each row's printed line the amount set contains our_amount and does NOT contain nearest_disclosure_amount. Including fy17:209: PDF prints $2,076,666 (ours), disclosure says $2,076,667.
- Two of the four controls reproduce exactly against the shipped module: +$7 on every amount -> 440/440 pdf_contradicts; an amount planted that appears on no line of that EIN -> 440/440 pdf_contradicts. The mechanism test holds.
- Two-engine claim is real: code/parse_schedule_c.py:50-51 uses pypdf.PdfReader().extract_text(); code/verify_amounts_against_pdf.py shells out to poppler `pdftotext -layout`. Different engines over the same bytes, as described.
- My own `pdftotext -layout` output for all 13 PDFs is byte-identical to the repo's build/pdftext cache (cmp clean on all 13) — the cached text is not stale and every count above is reproducible from source/.
- '~8s to rebuild' — one `pdftotext -layout` pass over all 13 PDFs took 8.167s wall on this machine.
- 150 tests collected under code/ (commit claims '150 tests pass (was 143)'), and the two new test files pass: 14 passed in 0.01s.
- README's cross-reference anchor `DATA-DICTIONARY.md#datayearschedule_cyear_appendix_csv` resolves correctly against the heading `## \`data/{year}/schedule_c/{year}_appendix_*.csv\``.
- No data file under data/fy* was modified by the commit (diff touches only .gitignore, three docs, four code files, data/AMOUNT-AUDIT.md and the new data/AMOUNT-PDF-VERIFICATION.csv), and neither new script contains an --apply path or a write to data/fy*. The repo working tree is still clean after my audit — I wrote nothing outside /tmp.
- Reproduced the claimed split exactly: `python code/verify_amounts_against_pdf.py --out /tmp/audit_pdfverify.csv` → `pdf_confirms 399  $22,481,361` / `pdf_confirms_weak 41  $2,834,626` / 0 pdf_contradicts / 0 pdf_ein_absent / 440 rows total. I got 399 and 41, $22,481,361 and $2,834,626.
- The committed artifact is byte-identical to a fresh run: `diff data/AMOUNT-PDF-VERIFICATION.csv /tmp/audit_pdfverify.csv` → IDENTICAL. The result is deterministic and reproducible from the shipped cache.
- Input selection is correct: data/AMOUNT-AUDIT-findings.csv has 1,548 rows; filtering to verdicts (ein_absent, rounding, neighbour_bleed) gives exactly 440, decomposing as 419 ein_absent + 18 rounding + 3 neighbour_bleed, matching the claim.
- The 3 neighbour_bleed rows do each get `pdf_confirms`, and the PDF does print name+EIN+amount on one line for each: fy15:646 line 3605 `Coalition for Asian American Children and Families 13-3682471 $833,333`; fy23:585 line 1920 `Mayor's Office of Criminal Justice 13-6400434 $325,000`; fy25:3465 line 8107 `Community Service Society of New York 13-5562202 $164,000`. (Caveat worth recording rather than a finding: in all three the disclosure's claimed owner EIN is printed on an ADJACENT line carrying the SAME amount — 3605/3606, 1917/1920, 8105/8107 — so the amount is a shared split-the-pot figure and the withdrawal rests on evidence that does not discriminate between the two readings.)
- 68.3% headline ratio: 3,741,615,569 / 5,476,070,836 = 68.33%. I got 68.33%. Shortfall = $1,734,455,267, i.e. the claimed $1.73B.
- *_schedule_c_initiatives.csv sum over FY2015-FY2027 = $5,474,660,271 across 1,900 rows — exactly the claimed figure, delta 0. Against the printed $5,476,070,836 that is 0.0258%, i.e. the claimed 0.026%. (Note: globbing all of data/fy*/ including FY09-FY14 gives $7,363,002,422 over 2,598 rows — the claim is only true when scoped to the 13 Schedule C years, which the commit does not state.)
- No `--apply` path exists and no data file under data/fy* is modified: `git show --stat ba90fce` touches only .gitignore, DATA-DICTIONARY.md, README.md, code/PARSING.md, the two new scripts, two new test files, data/AMOUNT-AUDIT.md and data/AMOUNT-PDF-VERIFICATION.csv.
- The join is on (EIN, amount), never EIN alone — `carrying = [(n, t) for n, t in hits if ours in amounts_on(t)]` at line 150 requires both. `member` appears nowhere in the script and is never used as a key component.
- `pdf_ein_lines` is not inflated by same-line duplicate EINs: for EIN 13-6400434 in FY2023, len(hits)=483 and distinct line numbers=483. Also verified 0 of the 399 confirms landed on one of the 120 corpus-wide text lines that carry two or more distinct EINs, so the specific 'two printed rows collapsed onto one text line' failure did not occur in the published set.
- The 7 tests in code/test_verify_amounts_against_pdf.py pass.
- The headline tally reproduces exactly. I re-implemented verify() independently against my own pdftotext -layout output written to /tmp/audit440/ (not the repo's build/pdftext cache) and got pdf_confirms 399 / $22,481,361 and pdf_confirms_weak 41 / $2,834,626, 0 pdf_contradicts, 0 pdf_ein_absent, 0 pdf_no_source. Row-by-row diff against data/AMOUNT-PDF-VERIFICATION.csv: 0 of 440 rows differ in either verdict or pdf_line.
- The three withdrawn `neighbour_bleed` rows are genuinely printed intact, as claimed. I read all three at coordinate/line level: FY2015 L3605 'Coalition for Asian American Children and Families 13-3682471 $833,333'; FY2023 L1920 "Mayor's Office of Criminal Justice 13-6400434 $325,000"; FY2025 L8107 'Community Service Society of New York 13-5562202 $164,000'. Organization, EIN and amount all agree with the corresponding data rows. The withdrawal is defensible on the amount.
- No corpus over-count against the printed document. For all 417 distinct (fiscal_year, EIN, amount) keys among the 440, I counted our corpus rows against printed lines carrying that (EIN, amount) pair: 0 keys where ours exceeds the PDF. The 'two of our rows confirmed by one printed line' attack fails — e.g. FY2021 EIN 261422585 has two of our rows and two printed awards (L8316, L8318); FY2024 EIN 112037770 $10,000 has two of ours and two printed (L20794, L20800).
- The within-line neighbour-bleed attack fails. Of the 440 confirming lines, 0 carry more than one distinct dollar amount and 0 carry more than one distinct EIN. A -layout line cannot be supplying a neighbouring award's amount in this corpus.
- The 483-line magnitude claim is real, just misattributed: FY2023 EIN 13-6400434 is on exactly 483 lines (I counted 483). The pinning rule it justifies is therefore warranted even though the attribution is wrong.
- 18 of the ~29 rows I hand-read agree exactly on organization, EIN and amount once wrapped printed rows are reconstructed. Verified: fy15:9 (NYAGV 13-3780848 $30,000, L448), fy15:648 (New York Urban League 13-1671035 $833,333, L3607), fy15 NSHOPP 13-3077049 $32,000 (name wraps L3001->3002), fy16:69 (Belmont Arthur Ave 13-3020589 $29,730, L4029), fy20:2175 (Turtle Bay Tree Fund 13-2561121 $10,000, wraps L7420-7422), fy20 Stuyvesant Cove 11-3582255 $10,000 (wraps L7423-7425), fy21:458 (Center for New York City Law at New York Law School 13-5645885 $35,400 — verified at coordinate level on FY21 page index 178: one award whose program name wraps two visual lines), fy21:1018 (Belmont Arthur Ave 13-3020589 $25,270, L3241), fy21:1431 (Penn South 13-3413349 $60,000, wraps L4620-4621), fy23:1931 (New York Harm Reduction Educators 13-3678499 $25,000, wraps L12418-12419), fy23:585 (MOCJ 13-6400434 $325,000, L1920), fy24:2942 (Wildcat 13-2725423 $30,000, wraps L7600-7602), fy25:1224 (Hester Street Collaborative 20-0774906 $200,000, wraps L17822-17823), fy25:3465 (Community Service Society 13-5562202 $164,000, L8107), fy27:4682 (Osborne 13-5563028 $14,999, wraps L12791-12792), fy27:4724 (Selfhelp 13-1624178 $44,999, L12900), fy15:646, fy21:382/383.
- The script has no --apply path and writes no data file: TARGET output is --out only, PDFS/CACHE are read paths plus build/pdftext, and `git diff --stat b7a2f7f ba90fce` shows no file under data/fy* modified. The standing rule holds.
- Header-matching rules are not violated by this commit: code/audit_amounts.py:hidx still excludes 'fc ein'/'conduit', and verify_amounts_against_pdf.py never reads a disclosure workbook at all, so no figure or key is sourced from one. 'member' is never used as a key component in either script.
- code/test_verify_amounts_against_pdf.py: 7 passed in 0.01s under the project venv.
