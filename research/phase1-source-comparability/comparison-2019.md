---
title: "FY2019 — Council expense disclosure workbook vs extracted Schedule C"
created: 2026-08-12
type: research
status: complete
tags: [nyc-budget, schedule-c, expense-disclosure, data-integrity, fy2019]
---

# FY2019 — disclosure workbook vs extracted Schedule C

**Report generated:** 2026-08-12
**Data current as of:** 2026-08-12 — `source/expense-funding-disclosure/funded_disclosure_FY2019.xlsx`
and the committed `data/fy19/` tree at `de251b5`. No re-parse of the PDF, no network.
**Branch:** `research/phase1-source-comparability`. Nothing in `data/`, `source/`, `viz/`,
`mcp/` or `code/` was modified.
**Reproduce:** `python3 research/phase1-source-comparability/compare_2019.py`
Every figure below is printed by that script. It ends in seven assertions; it exits non-zero
if any number in this report has drifted.

---

## Verdict

**FY2019 Schedule C extraction is not usable as a record of FY2019 discretionary awards, and
the disclosure workbook is not a superset of it.** Both halves of that sentence are load-bearing
and both are verified.

1. **Coverage is 8.8% of rows and 46.1% of dollars.** 846 extracted rows against 9,655
   disclosed designations; $181,026,931 against $392,945,000.
2. **The three appendix CSVs are empty**, which removes 4,526 disclosed designations
   ($49,724,000) and 837 organizations that appear under no other Source.
3. **Where a row was extracted, the money is usually right and the labels usually are not.**
   753 of 846 rows (89.0%) match a disclosed award exactly on `(EIN, amount)` — but of the rows
   that match, the extracted `initiative` is contradicted by the disclosure's `Source` **251
   times against 439 agreements**, and 70 more rows carry no initiative at all.
4. **The superset claim fails, and not only through OCR noise.** The Schedule C PDF prints
   sub-grantee tables the disclosure workbook does not itemize. Ten sampled "Jobs to Build On"
   partner awards: **0 of 10 exist in the disclosure**, though all ten organizations appear there
   under other designations. Neither source contains the other.
5. **`fy19_schedule_c_awards.csv` cannot answer "which member funded this."** Its `member`
   column holds a borough name or the word `Placement` on 41 rows and is empty on the other 805.
   It is not member attribution, so FY2019 contributes nothing to issue #51 either way.

The comparison is worth running anyway: it produces a **mechanical repair list**, not just a
verdict. See § 9.

---

## 0. Baseline

| | disclosure workbook | extracted Schedule C |
|---|---|---|
| file | `funded_disclosure_FY2019.xlsx`, sheet `FY19 (4-14-21)` | `data/fy19/schedule_c/*.csv` |
| rows | 9,655 | 846 |
| dollars | $392,945,000 | $181,026,931 |
| Cleared | 9,602 · $392,443,522 | *no status column exists* |
| Pending | 53 · $501,478 | *no status column exists* |
| embedded summary rows stripped | 0 | n/a |
| appendix A / B / C rows | n/a | 0 / 0 / 0 |

**Unaccounted for: 8,809 rows and $211,918,069.**

VERIFIED. The disclosure side needs no cleaning for FY2019 — unlike FY2024 and FY2026, the
FY2019 workbook contains **no** embedded summary rows, so its 9,655 rows are 9,655 designations.

The `award_type` split in the extracted file is 805 `initiative_provider` and 41 `member_item`.

---

## 1. By EIN, both directions

| | count |
|---|---|
| distinct EIN, disclosure | 2,152 |
| distinct EIN, Schedule C | 494 |
| in both | 475 |
| **Schedule C only** | **19** (20 rows, $2,980,665) |
| disclosure only | 1,677 |

The Schedule C-only direction is the one that can falsify "the disclosure is a superset," so all
19 were read individually. They are not one thing:

| kind | n EINs | evidence |
|---|---|---|
| digit-mangled copy of a disclosure EIN | 3 | see below |
| same organization, different EIN, same dollar amount | 2 | see below |
| EIN leaked out of a run-together row, belongs to neither named org | 1 | `208427029` |
| organization genuinely absent from the disclosure | 13 | incl. all 7 "Jobs to Build On" partners |

**Digit mangling — VERIFIED by two independent tests** (exact organization-name match in the
disclosure under a different EIN, and a disclosure EIN with the same nine digits reordered):

```
Sloan-Kettering Institute for Cancer Research   Schedule C 131924182   disclosure 131624182
City Parks Foundation                           Schedule C 133561567   disclosure 133561657
Giving Alternative Learners Uplifting Opps.     Schedule C 500615968   disclosure 050615968
```

The third is the ugly one: the leading zero has rotated to the end. A join on EIN silently drops
that organization; a join that strips leading zeros silently merges it with a different one.

**Same organization, different EIN, identical amount:**

```
American Lung Association   Schedule C EIN 060646594 $78,000  |  disclosure EIN 131632524 $78,000
New York Blood Center, Inc. Schedule C EIN 341213000 $150,000 |  disclosure EIN 131949477 $150,000
```

INFERRED: these are one award each, carrying two different EINs. Which EIN is correct cannot be
settled from either file. Not resolved here.

**Disclosure-only EINs: 1,677**, of which 38 appear only on Pending rows. The bulk are the
appendix hole (§ 6): 837 EINs appear in the disclosure **only** under Local, Aging, or Youth,
and those are exactly the three files that came out empty.

---

## 2. Source vocabulary vs initiative vocabulary

| | count |
|---|---|
| distinct `Source` values, disclosure | 136 |
| distinct `initiative` values, Schedule C | 93 (+70 rows with a blank initiative) |
| matched after normalizing case, curly quotes, `&`/`and` | 81 |
| in disclosure only | 55 |
| in Schedule C only | 12 |

Normalization folds typography only. It does not stem, drop stopwords, or fuzzy-match, so
anything that fails to match is a real vocabulary difference.

### 2a. Three Schedule C "initiatives" are PDF prose, not initiative names

VERIFIED — quoted verbatim from `fy19_schedule_c_awards.csv`, `initiative` column:

```
'application, enrollment and recertification and emergency food assistance pantries. Of the'
'courts, and school justice centers and youth programs throughout the City.  An additional'
'will receive $125,000 to improve bail making for bail fund eligible defendants. Additionally,'
```

Five rows carry these, $3,590,000. The extractor took a mid-sentence line break in the PDF's
narrative text as an initiative heading. Two of the three resolve by `(EIN, amount)` match to
`Food Access and Benefits` and `Bail Fund` (VERIFIED). The third does not match any disclosed
award — its EIN belongs to Fund for the City of New York, whose disclosed rows under
`Center for Court Innovation` do not sum to the extracted amount (see mismatch #28).

### 2b. Nine more are wording drift, harmless once mapped

`Access Health` → `Access Health Initiative` · `Coalition of Theaters of Color` → `Coalition
Theaters of Color` · `Construction Site Safety Training` → `Construction Site Safety` ·
`Court-Involved Youth Mental Health` → `… Initiative` · `Dropout Prevention and Intervention`
→ `… Initiative` · `HIV/AIDS Faith-Based` → `HIV/AIDS Faith Based Initiative` ·
`Legal Information for Families Today (LIFT)` → `Legal Information for Families (LIFT)` ·
`LGBT Senior Services in Every Borough` → `LGBTQ …` · `LGBTQ Youth All-Borough Mental Health`
→ `LGBTQ Youth Mental Health`.

**A crosswalk table is needed regardless of extraction quality.** Neither vocabulary is a
subset of the other and the drift is not mechanical.

### 2c. The initiative label bleeds across block boundaries

This is the substantive finding. Taking only the Schedule C rows whose `(EIN, amount)` exists in
the disclosure, and asking whether *any* of the matching disclosure rows carries the same Source:

```
rows with a BLANK initiative                            70
matched rows whose label AGREES                        439
matched rows whose label DISAGREES                     251
rows with no (EIN, amount) match at all                 89
```

Top relabelings, extracted `initiative` → disclosed `Source`:

```
  42  'Child Health and Wellness'                    ->  'Ending the Epidemic'
  34  'Communities of Color Nonprofit Stabilization' ->  'Adult Literacy Initiative'
  22  'Borough Presidents’ Discretionary Funding Re' ->  'Elie Wiesel Holocaust Survivors'
  17  'Child Health and Wellness'                    ->  'HIV/AIDS Faith Based Initiative'
  15  'Discretionary Child Care'                     ->  "City's First Readers"
  13  'HIV/AIDS Faith-Based'                         ->  'Maternal and Child Health Services'
   6  'Children Under Five'                          ->  'Court-Involved Youth Mental Health Initiative'
```

The first row is fully traced. `Child Health and Wellness` carries **67 rows / $6,175,370** in the
extracted file. In the disclosure it is **3 rows / $646,000**:

```
row 247    $78,000  'American Lung Association'
row 4254  $300,000  'Health + Hospitals'
row 6686  $268,000  'New York University'
```

The other 64 belong to `Ending the Epidemic` (45), `HIV/AIDS Faith Based Initiative` (18) and
three others. And in the extracted file, rows 305–310 sit between the mislabeled block and the
next heading with **`initiative` blank entirely** — the heading was neither carried nor reset:

```
305  (blank)  133530740   81,000  'National Black Leadership Commission on AIDS, Inc.'
306  (blank)  132621497   30,000  'Planned Parenthood of New York City, Inc.'
307  (blank)  135669201   50,000  'Public Health Solutions'
308  (blank)  112077266   10,000  'St. Albans Congregational Church'
309  (blank)  237360305   10,000  'Urban Health Plan'
310  (blank)  263178076   20,000  'Vision Urbana, Inc. 13-3848575 * $14,000 Young Women of Colo…'
```

**Consequence:** any FY2019 per-initiative figure taken from `data/fy19/` is unsafe, including
figures that reconcile. The dollars can be right while the initiative attached to them is wrong.

### 2d. `fy19_schedule_c_initiatives.csv` is shifted one category

Cross-checking the category assigned to each initiative in the two extracted files against each
other, for the 94 initiatives that appear in both:

```
agree: 0    disagree: 76    not in the initiatives file: 18
```

**Zero agreements.** The pattern is a uniform one-category lag in `…_initiatives.csv`:

```
initiative                              awards.csv says       initiatives.csv says
Discretionary Child Care                CHILDREN’S SERVICES   BOROUGHWIDE NEEDS
Alternatives to Incarceration (ATI’s)   CRIMINAL JUSTICE      COMMUNITY DEVELOPMENT
Child Mind Institute                    EDUCATION             DOMESTIC VIOLENCE SERVICES
```

The file's first row is category `INTRODUCTION` holding `Multiple Anti-Poverty Initiative`
($2,800,000) — `INTRODUCTION` is the PDF's introduction section, not a funding category.

**This matters for how the reconciliation file reads.** `fy19_schedule_c_reconciliation.txt`
reports 27 of 28 category totals "OK", and its own header already flags `categories from ToC: 28
| summary blocks found: 27  <-- MISMATCH`. INFERRED: the summary block and the initiative rows
were both attached to the same wrong category name, so the check compares a shifted total against
a shifted total and passes. **A green reconciliation here is not evidence that categories are
right.** Not independently confirmed against the PDF, which was not opened for this run.

---

## 3. Council member — evidence for issue #51

**FY2019 provides no evidence either way, because the extracted file has no member attribution.**

`fy19_schedule_c_awards.csv`, `member` column, complete value list:

```
  805  ''
   13  'Placement'
   12  'Brooklyn'
    8  'Queens'
    6  'Staten Island'
    2  'Manhattan'
```

Boroughs and one word sheared off a purpose string (`'Placement'`, from `'Occupational Training
and Job Placement'`). Zero overlap with any disclosed member name — asserted in the script.

The disclosure side carries 58 values across 7,955 rows — the other 1,700 are blank, and none of
those is a `Local`, `Youth`, `Aging` or `Boro` row, so the blanks are citywide initiative
designations rather than missing attribution. But the values are **bare surnames only**:

```
Williams  -> ['Williams']  156 rows       Sanchez -> ABSENT
Rivera    -> ['Rivera']    141 rows       Barron  -> ['Barron']   96 rows
Vallone   -> ['Vallone']   128 rows       Diaz    -> ['Diaz']    143 rows
```

The only multi-token values are `Van Bramer` and the five borough delegations. So **the FY2019
disclosure workbook does not disambiguate the colliding surnames either.** It is a better source
than the extraction — it has member attribution at all — but it is not a solution to #51 for this
year. INFERRED, not verified: each of those surnames appears as exactly one value in FY2019, so
the collision is latent rather than active in this workbook — but "one value" is not "one
member," and the seat-by-seat check against the FY2019 roster was not done here.

---

## 4. Exact award match, both directions

```
key = (EIN, amount)
  Schedule C rows matched into disclosure   753 / 846   (89.0%)
  Schedule C rows unmatched                  93
  disclosure rows unmatched                8,902

key = (EIN, amount, member)
  Schedule C rows matched into disclosure   723 / 846   (85.5%)
  lost by adding member to the key           30
```

Matching is multiset-aware: a `(EIN, amount)` pair occurring twice on one side consumes two on
the other, so repeated identical awards cannot inflate the count.

The 30 rows lost by adding `member` are the member-attribution failure of § 3, not a data
disagreement. Of the 41 `member_item` rows, 28 match on `(EIN, amount)` and **0** can ever match
on member.

The 93 unmatched Schedule C rows are $20,095,287:

```
  69  EIN present in disclosure, amount differs
  20  EIN absent from disclosure
   4  (EIN, amount) exists but was already consumed by another row
```

**89.0% on `(EIN, amount)` is the single most encouraging number in this report.** It says the
FY2019 extraction's failure mode is *omission and mislabeling*, not fabrication: what it did
capture is mostly a real disclosed award. That is what makes § 9 possible.

---

## 5. Dollars per initiative

Restricted to the 81 initiative names present in both vocabularies:

```
                                    disclosure 1,603 rows  $183,498,985
                                   Schedule C    677 rows  $161,029,911
                                                 delta     -$22,469,074
```

**34 of the 81 agree to the dollar.** Full list in the script output; a sample:

```
Legal Services for Low-Income New Yorkers      5 vs 5 rows    $5,300,000
Legal Services for the Working Poor           12 vs 12 rows   $3,205,000
CUNY Research Institutes                       6 vs 6 rows    $3,170,000
Supportive Alternatives to Violent Encounters  5 vs 5 rows    $2,450,000
Social Adult Day Care                          9 vs 9 rows    $1,055,556
Medicaid Redesign Transition                  13 vs 13 rows     $500,000
```

Two of the 34 agree on dollars while disagreeing on row count — `LGBT Community Services`
(6 extracted rows vs 8 disclosed, both $2,000,000) and `Physical Education and Fitness`
(2 extracted vs 3 disclosed, both $1,925,000). The aggregate survives a row split the extraction
got wrong.

Largest disagreements, both signs:

```
initiative                                         dis n     dis $   sc n      sc $        delta
Domestic Violence and Empowerment (DoVE)             281  9,305,000    18  1,582,500   -7,722,500
Child Health and Wellness                              3    646,000    67  6,175,370   +5,529,370
Job Training and Placement Initiative                  5  7,824,200    33 12,287,700   +4,463,500
Parks Equity Initiative                              220  4,603,500     1    600,000   -4,003,500
Communities of Color Nonprofit Stabilization Fund     21  3,700,000    47  7,380,000   +3,680,000
Food Pantries                                        305  4,659,000     1  1,000,000   -3,659,000
```

The negative rows are the appendix hole and per-member designations that were never extracted.
**The positive rows are the more interesting ones** — the extraction reports *more* money under
an initiative than the Council disclosed for it. Two mechanisms, both verified:

- **Label bleed** (§ 2c): `Child Health and Wellness` and `Communities of Color…` absorbed
  neighbouring blocks.
- **Sub-grantee tables** (§ 6b): `Job Training and Placement Initiative` absorbed two embedded
  tables the disclosure does not itemize at all.

---

## 6. Two structural gaps

### 6a. The empty appendices

```
Local  -> appendix B   disclosure 3,090 rows  $36,464,000   extracted CSV: 0 rows
Aging  -> appendix A   disclosure   527 rows   $5,610,000   extracted CSV: 0 rows
Youth  -> appendix C   disclosure   909 rows   $7,650,000   extracted CSV: 0 rows
                              TOTAL 4,526 rows $49,724,000
```

837 distinct EINs appear in the disclosure **only** under those three Sources. Fixing the FY2019
appendix parse recovers 4,526 designations, 837 organizations, and — uniquely for these three
Sources — the member attribution that the main body does not carry at all.

Out of scope tonight, per the run brief. Noted because it sizes the prize.

### 6b. The Schedule C PDF discloses sub-grantees the workbook does not

VERIFIED, and this is what falsifies "the disclosure is a superset."
`fy19_schedule_c_awards.csv` line 725 has this in its `organization` column:

```
'**Below is a list of the Jobs to Build On service providers partners: Organization EIN Am…'
```

The rows that follow it are CWE's sub-grantees. Ten sampled:

```
                                        exact award   organization present
                                        in disclosure  in disclosure
Henry Street Settlement    $273,000         no          yes (15 rows, $635,333)
CAMBA, Inc                 $245,000         no          yes (14 rows, $1,143,117)
East River Development     $300,000         no          yes (17 rows, $611,815)
HANAC, Inc                 $200,000         no          yes (26 rows, $463,172)
LEAP / Brooklyn Workforce  $248,000         no          yes (1 row, $5,000)
Opportunities for a Better
  Tomorrow                 $281,000         no          yes (15 rows, $613,750)
Nontraditional Employment
  for Women                $200,000         no          yes (2 rows, $310,000)
Business Outreach Center   $100,000         no          yes (13 rows, $385,162)
Per Scholas, Inc.          $200,000         no          yes (9 rows, $390,797)
Actor's Fund of America    $18,500          no          yes (2 rows, $8,000)
```

**0 of 10.** The disclosure's whole `Job Training and Placement Initiative` is five rows: three to
Consortium for Worker Education ($7,554,200), plus HOPE Program ($60,000) and WHEDco ($210,000).
The PDF prints where CWE's money went; the workbook does not.

A second embedded table sits in the same block, its header likewise captured as an organization:
`'Fiscal 2019 Adopted Expense Budget Adjustment Summary Organization EIN Amount Service Typ…'`
(line 738).

INFERRED, not verified: the $4,463,500 excess in this initiative is probably these two tables
double-counting against the prime award rather than genuinely additional money. Determining
which requires the PDF. **Do not net these into any total.**

---

## 7. Run-together rows — 38 rows, each hiding at least one award

In the PDF each provider line reads `<Organization> <EIN> <Amount>`. When two lines collapse, the
first line's EIN and amount land **inside the organization string** and only the second line's
EIN and amount reach the columns. **38 rows, 4.5% of the file**, match `NN-NNNNNNN * $A` inside
`organization`.

Testing whether those embedded pairs are real awards:

```
embedded (EIN, amount) pairs recovered from the text:   40
  of those, an EXACT disclosure award:                  37   $3,939,100
  the row's OWN (EIN, amount) is also an exact award:   33 / 38
```

**37 of 40 hidden pairs are real disclosed awards.** The extraction did not lose them — it
stored them as text in the wrong field. They are recoverable with a regex.

---

## 8. Fourteen mismatches, read individually and quoted in full

Selected to cover every failure class. Numbering follows the script's § 6 output.

**#5 — digit substitution in the EIN.**
```
SCHEDULE C  [fy19_schedule_c_awards.csv:466]
    category      'IMMIGRANT SERVICES'
    initiative    'Immigrant Health Initiative'
    organization  'Sloan-Kettering Institute for Cancer Research'
    ein           '131924182'
    amount        '200000'
DISCLOSURE  no row with EIN 131924182; EIN 131624182 carries the identical name
```
WHY: a `6` read as a `9`. The organization is present in both sources; only the key differs.

**#10 — transposed EIN digits.**
```
SCHEDULE C  [fy19_schedule_c_awards.csv:631]
    category      'PARKS AND RECREATION SERVICES'
    initiative    'Parks Equity Initiative'
    organization  'City Parks Foundation'
    ein           '133561567'
    amount        '600000'
DISCLOSURE  no row with EIN 133561567; EIN 133561657 carries the identical name
```
WHY: `…567` vs `…657`. Same failure class as #5.

**#19 — leading zero rotated to the end.**
```
SCHEDULE C  [fy19_schedule_c_awards.csv:534]
    category      'MENTAL HEALTH SERVICES'
    initiative    'Autism Awareness'
    organization  'Giving Alternative Learners Uplifting Opportunities, Inc.'
    ein           '500615968'
    amount        '50000'
DISCLOSURE  no row with EIN 500615968; EIN 050615968 carries the identical name
```
WHY: the worst of the three, because it survives both a naive join and a zero-stripping join.

**#11 — run-together row, correct award buried in the organization field.**
```
SCHEDULE C  [fy19_schedule_c_awards.csv:166]
    category      'DOMESTIC VIOLENCE SERVICES'
    initiative    'Domestic Violence and Empowerment (DoVE) Initiative'
    organization  'Crime Victims Treatment Center, Inc. 81-5080860 * $45,000
                   Edwin Gould Services for Children and Families'
    ein           '135675643'
    amount        '45000'
DISCLOSURE  no row with EIN 135675643. But:
    row 2499  EIN 815080860  DoVE  Cleared  $45,000  'Crime Victims Treatment Center, Inc.'
```
WHY: two PDF lines collapsed. The correct EIN `81-5080860` is *inside the organization string*
and the disclosed award matches it exactly on initiative, amount and name. The `ein` column
instead holds the trailing organization's EIN. Fully recoverable.

**#14 — run-together row where the surviving EIN belongs to neither named org.**
```
SCHEDULE C  [fy19_schedule_c_awards.csv:304]
    category      'HEALTH SERVICES'
    initiative    'Child Health and Wellness'
    organization  'Mount Horeb Baptist Church 11-2074467 * $10,000 Mt. Moriah AME Church'
    ein           '208427029'
    amount        '10000'
DISCLOSURE  no row with EIN 208427029.
    Mount Horeb Baptist Church -> EIN 112074467 (4 rows), incl. $10,000 HIV/AIDS Faith Based
    Mt. Moriah AME Church      -> EIN 112831746 (3 rows), incl. $10,000 HIV/AIDS Faith Based
```
WHY: worse than #11 — `208427029` matches neither named organization, so a third row's EIN also
bled in. The `initiative` is wrong too (`Child Health and Wellness` for what the Council
disclosed as `HIV/AIDS Faith Based Initiative`). Every field except the amount is wrong, and the
amount is ambiguous between the two organizations because both received $10,000.

**#1 — same organization, same amount, different EIN.**
```
SCHEDULE C  [fy19_schedule_c_awards.csv:235]
    category      'HEALTH SERVICES'
    initiative    'Cancer Services'
    organization  'American Lung Association of the Northeast, Inc.'
    ein           '060646594'
    amount        '78000'
DISCLOSURE  row 247  EIN 131632524  'Child Health and Wellness'  $78,000
            'American Lung Association'
```
WHY: unresolved EIN disagreement, *and* the two sources disagree about which initiative funded
it. Amount and organization agree. Neither file can adjudicate. **Left standing.**

**#7, #9, #15, #16 — the "Jobs to Build On" sub-grantees.**
```
[fy19_schedule_c_awards.csv:739]  'Cooperative Home Care Associates'  EIN 133238142  $200,000
                                  member 'Placement'  purpose 'Occupational Training and Job'
[fy19_schedule_c_awards.csv:744]  'STRIVE' / 'East Harlem Employment Services'
                                  EIN 133255679  $100,000
[fy19_schedule_c_awards.csv:743]  'ARGUS Community, Inc'  EIN 237359002  $100,000
[fy19_schedule_c_awards.csv:747]  'Exodus Transitional Community'  EIN 311731465  $75,000
all four: initiative 'Job Training and Placement Initiative'
DISCLOSURE  no row with any of these four EINs
```
WHY: § 6b. These are sub-grantee rows the disclosure workbook does not publish. Note the
`member` value `'Placement'` on #7, #15 and #16 — a fragment of the purpose text `'Occupational
Training and Job Placement'` landing in the member column.

**#13 — a row that is not an award.**
```
SCHEDULE C  [fy19_schedule_c_awards.csv:752]
    initiative    'Job Training and Placement Initiative'
    organization  'RV Systems, Inc. (Database)'
    ein           '201635756'
    amount        '185000'
    purpose       'Program data and Reporting'
DISCLOSURE  no row with EIN 201635756
```
WHY: a database vendor inside a sub-grantee table. Real spending, but not a member designation.
Whatever consumes this data needs to decide whether such rows belong in an "awards" table at all.

**#21 and #23–#25 — one EIN standing in for four different colleges.**
```
[fy19_schedule_c_awards.csv:22]  'Bronx Community College'     EIN 131988190  $100,000
[fy19_schedule_c_awards.csv:40]  'LaGuardia Community College' EIN 131988190  $100,000
[fy19_schedule_c_awards.csv:43]  'Medgar Evers College, CUNY'  EIN 131988190   $75,000
[fy19_schedule_c_awards.csv:49]  'NYC City College of Technology' EIN 131988190 $100,000
all four: initiative 'Communities of Color Nonprofit Stabilization Fund'
DISCLOSURE  EIN 131988190 = 'Research Foundation of the City University of New York',
            36 rows totalling $3,277,000; none at $100,000 or $75,000 under CCNSF
```
WHY: two problems stacked. The EIN is the CUNY Research Foundation's — correct as a fiscal
conduit, useless as an identifier of the four distinct colleges. **A per-organization rollup on
EIN merges four colleges into one grantee here.** These four rows have no `(EIN, amount)` match
at all; the block they sit in is the mislabeled one from § 2c, 34 of whose rows resolve to
`Adult Literacy Initiative` in the disclosure. INFERRED, not verified: these four belong to the
same misassigned block.

**#22 and #29–#32 — EIN `136400434` as a catch-all.**
```
[fy19_schedule_c_awards.csv:12]   'Borough Public Library'  EIN 136400434  $325,000
                                  member 'Queens'  initiative 'Discretionary Child Care'
[fy19_schedule_c_awards.csv:29]   'Department of Youth and Community Development'
                                  EIN 136400434  $185,000  initiative 'CCNSF'
[fy19_schedule_c_awards.csv:359]  'NYC Food Policy Institute at Hunter College'
                                  EIN 136400434  $250,000  initiative 'CUNY Research Institutes'
[fy19_schedule_c_awards.csv:711]  'City University of New York' / 'Queens College'
                                  EIN 136400434  $450,000
DISCLOSURE  EIN 136400434 = 804 rows, $55,785,099 — every City agency, community board,
            borough president and library
```
WHY: `136400434` is the City of New York's own EIN. It is a real value in both sources and it is
not an organization identifier. In the extracted file it is additionally attached to
`'Borough Public Library'` — a name with its borough sheared off, which is why `member` reads
`'Queens'`. **Any dedupe or grantee-count on EIN must exclude `136400434` explicitly.**

**#28 — prose captured as an initiative.**
```
SCHEDULE C  [fy19_schedule_c_awards.csv:99]
    category      'CRIMINAL JUSTICE SERVICES'
    initiative    'courts, and school justice centers and youth programs throughout the
                   City.  An additional'
    organization  'Fund for the City of New York, Inc.'
    ein           '132612524'
    amount        '1710000'
DISCLOSURE  EIN 132612524 = 66 rows, $3,508,359, incl.
    row 3755  Center for Court Innovation  Cleared    $200,000
    row 3756  Center for Court Innovation  Cleared  $1,210,000
```
WHY: § 2a. Also note the disclosure splits this into $200,000 + $1,210,000 = $1,410,000 against
the extraction's single $1,710,000 — a $300,000 gap that neither source explains on its own.
**Left standing.**

**#26 — same initiative, different amount.**
```
SCHEDULE C  [fy19_schedule_c_awards.csv:70]
    initiative    'LGBT Community Services'
    organization  'Destination Tomorrow, Inc.'
    ein           '800259180'
    amount        '200000'
DISCLOSURE  2 rows, $350,000 total:
    row 2969  LGBT Community Services  Cleared  $100,000  'Destination Tomorrow, Inc.'
    row 2970  Trans Equity Programs    Cleared  $250,000  'Destination Tomorrow, Inc.'
```
WHY: the extraction reports $200,000 under an initiative where the Council disclosed $100,000,
and the $250,000 Trans Equity award is absent. Note from § 5 that `LGBT Community Services`
nonetheless *totals* correctly at $2,000,000 across both sources — the initiative total is right
while this organization's share of it is wrong. **A reconciling total does not validate its
rows.**

---

## 9. What this buys: a mechanical repair list

Not a recommendation to act tonight — a statement of what the comparison found that is fixable
without opening the PDF again.

| repair | rows | verified basis |
|---|---|---|
| Recover awards buried in run-together `organization` strings | 37 awards, $3,939,100 | § 7 — each matches a disclosed award exactly |
| Correct the three mangled EINs | 3 orgs, 3 rows | § 1 — name match + digit-permutation match |
| Reassign the 251 mislabeled initiatives from the disclosure's `Source` | 251 | § 2c |
| Fill the 70 blank initiatives the same way | 70 | § 2c |
| Reject the 3 prose strings masquerading as initiatives | 5 | § 2a |
| Reject the 5 non-organization strings in `organization` | 5 | § 7, script § 4b output |
| Flag `136400434` and `131988190` as non-identifying EINs | 35 + 5 rows, $31,185,179 | § 8 |

Every one of these is driven by a `(EIN, amount)` match against the disclosure workbook, which
is the same join that succeeds on 89.0% of rows.

---

## 10. Cleared vs Pending

Reported separately throughout, with one hard limit: **`data/fy19/` has no status column**, so
Cleared/Pending is unrecoverable from the extracted side. It exists only in the disclosure.

```
disclosure Cleared   9,602 rows   $392,443,522
disclosure Pending      53 rows       $501,478   (0.13% of dollars)
```

The 53 Pending rows are small local designations, largest $61,701, spread across 12 Sources —
19 `Local`, 12 `Youth`, 4 `Anti-Poverty`, 3 each `Boro` / `Food Pantries` / `NYC Cleanup`, and
singles elsewhere. They contribute 52 distinct `(EIN, amount)` keys.

**Exactly one of those 52 keys is reachable from the extracted file:**

```
EIN 133597820  $15,000
  disclosure row 3831  Ending the Epidemic  Pending  'Gay Men of African Descent, Inc.'
  schedule C  [fy19_schedule_c_awards.csv:257]  'Child Health and Wellness'
              'Gay Men of African Descent (GMAD)'
```

So the Cleared/Pending distinction is effectively invisible in FY2019 Schedule C — not because
Pending awards were filtered out, but because Pending awards are overwhelmingly Local and Youth
designations, and those are the appendices that came out empty. INFERRED, not verified: a
correct FY2019 appendix parse would surface roughly 31 more Pending designations
(19 `Local` + 12 `Youth`), which downstream consumers would then be presenting as awards without
any status field to qualify them.

---

## 11. Ambiguity left standing

Not papered over. None of these is resolvable from the two files on disk.

1. **American Lung Association and New York Blood Center each carry two EINs** across the
   sources, with identical amounts. Neither file says which is correct.
2. **The $4,463,500 excess under `Job Training and Placement Initiative`** may be genuine
   sub-grantee disclosure or double counting against the prime award. Needs the PDF.
3. **Fund for the City of New York:** extraction $1,710,000 in one row, disclosure $200,000 +
   $1,210,000 = $1,410,000. $300,000 unexplained.
4. **`fy19_schedule_c_initiatives.csv` grand total is $338,301,000.** The disclosure's total for
   every Source *except* Local/Aging/Youth is $343,221,000. **Gap: $4,920,000, unexplained.**
   Do not treat either as validating the other.
5. **The one-category shift in `…_initiatives.csv` (§ 2d)** is verified as an internal
   contradiction between two extracted files; which of the two is right was **not** confirmed
   against the PDF. The `awards.csv` assignment is the plausible-looking one
   (`Discretionary Child Care` under `CHILDREN'S SERVICES`), but plausible is not verified.
6. **Whether FY2019's `Mount Horeb` row should carry $10,000 for Mount Horeb or for Mt. Moriah**
   is undecidable: both organizations received exactly $10,000 under the same initiative.

---

## 12. Bearing on FY2021–FY2027

FY2019 is a known-broken extraction and this report is consistent with that. Two findings do
carry forward, because they are properties of the *sources*, not of this year's parse:

1. **The vocabulary crosswalk is needed in every year.** `Source` and `initiative` are different
   naming systems (§ 2b). A good extraction does not make them align.
2. **"The disclosure is a superset" is false as a general claim** (§ 6b). The PDF publishes
   sub-grantee tables the workbook does not. Whether FY2021+ PDFs also carry them is untested
   here.

Conversely: **close FY2021–FY2027 agreement would not by itself prove the two sources are the
same universe.** § 5 shows two initiatives whose totals reconcile exactly while their rows are
wrong, and § 2d shows a category reconciliation that passes because both sides are shifted
identically. Row-level `(EIN, amount)` agreement is the test that would carry weight, not
totals.

---

## Commands run

```
python3 research/phase1-source-comparability/compare_2019.py
```

Reads `source/expense-funding-disclosure/funded_disclosure_FY2019.xlsx` through
`code/parse_expense_disclosure.py` and the four CSVs in `data/fy19/schedule_c/`. Writes nothing.
Stdlib only — no pandas, no openpyxl, no network. Self-checks assert the 9,655 / $392,945,000
and 846 / $181,026,931 baselines, the three empty appendices, the existence of Schedule C-only
EINs, the zero member-name overlap, the 38 run-together rows with 37 recoverable awards, and
that label disagreement exceeds 200 rows.
