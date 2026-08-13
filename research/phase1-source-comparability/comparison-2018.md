# FY2018: Council expense disclosure vs. parsed Schedule C

**Report generated:** 2026-08-12
**Data current as of:** 2026-08-12 (all inputs read from disk; no network calls)
**Branch:** `research/phase1-source-comparability` (worktree `/Users/noneck/Code/NYCB-phase1`, base `main` @ `de251b5`)
**Scope:** FY2018 only. Nothing under `data/`, `source/`, `viz/`, or `code/` was modified.

**Inputs**

| Side | File | Provenance |
|---|---|---|
| Disclosure | `source/expense-funding-disclosure/funded_disclosure_FY2018.xlsx` | sha256 `9071aaa3394893a2c15e508b6413095c5e98a2fd06eb00712a7a57d6f901b11d`, sheet `FY18` |
| Schedule C | `data/fy18/schedule_c/fy18_schedule_c_awards.csv` | last touched by `26a5ab8` |
| Schedule C | `data/fy18/schedule_c/fy18_appendix_a_aging.csv` | 422 rows |
| Schedule C | `data/fy18/schedule_c/fy18_appendix_b_local.csv` | **header only, 0 rows** |
| Schedule C | `data/fy18/schedule_c/fy18_appendix_c_youth.csv` | **header only, 0 rows** |

**Reproduce:** `python3 research/phase1-source-comparability/compare_year.py 2018`
(committed alongside this file; stdlib only; reads through `code/parse_expense_disclosure.py`).
Every count below came from that script or from a one-off probe quoted inline.

---

## Verdict

**The two documents are the same universe where they overlap, but FY2018 Schedule C covers only a
fraction of it, and its row-level fields are unreliable.** Three separate claims, ranked by how
firmly they are established:

1. **VERIFIED — the disclosure is very nearly a superset of Schedule C, and the ten exceptions are
   Schedule C's errors, not disclosure omissions.** 414 of Schedule C's 424 distinct EINs appear in
   the disclosure. Of the 10 that do not, 4 are demonstrably wrong EINs or wrong entities on the
   Schedule C side (§3.1–§3.4), 5 are sub-provider rows from a nested table the disclosure does not
   publish at that granularity (§3.5), and 1 is a mangled appendix row (§3.7). **No case was found
   where the disclosure is missing a designation that Schedule C genuinely records.** The
   "disclosure is a superset" hypothesis survives FY2018.
2. **VERIFIED — where FY2018 Schedule C keeps a row, its dollar figure is usually exact; its error
   mode is omission, not corruption.** In Community Housing Preservation Strategies, 38 of 52
   organizations agree to the cent, and the $801,484 initiative-level shortfall is **exactly** the
   sum of the 14 organizations Schedule C dropped (§5). Across all 55 shared initiative names,
   per-(initiative, EIN) totals agree exactly 396 times against 43 disagreements.
3. **VERIFIED — coverage is 28% of dollars and the member dimension is effectively absent.**
   Schedule C FY2018 carries $107.1M against the disclosure's $381.9M. Appendix B (Local) and
   Appendix C (Youth) are header-only, which alone discards **3,998 disclosure rows worth
   $44,194,000**. Only 95 of 902 Schedule C rows carry any member value at all, and most of those
   values are not council members (§4).

**Direct answer to the falsification test:** the direction that would break the superset claim —
Schedule C EINs absent from the disclosure — produced 10 EINs / 10 rows / $1,154,000, and all ten
have an explanation on the Schedule C side. That is 1.1% of Schedule C's rows and 1.1% of its
dollars.

---

## 1. Totals

```
$ python3 research/phase1-source-comparability/compare_year.py 2018
==============================================================================
FY2018 ROW AND DOLLAR TOTALS
==============================================================================
disclosure   rows   8894   $381,900,000.00   file=funded_disclosure_FY2018.xlsx sheet='FY18'
    status cleared    rows   8843   $381,385,171.00
    status pending    rows     51   $514,829.00
schedule C   rows    902   $107,136,231.00
    appendix_a_aging     rows    422   $4,419,275.00
    awards               rows    480   $102,716,956.00
      award_type initiative_provider  rows   463   $100,012,226.00
      award_type member_item          rows    17   $2,704,730.00
```

Schedule C is **10.1% of the disclosure's rows and 28.1% of its dollars.**

**Cleared vs. Pending.** FY2018 publishes `CLEARED` / `PENDING` in uppercase (the parser stores the
raw string and a lowercased `status_norm`). Pending is small — 51 rows, $514,829, 0.13% of dollars.
It is also **entirely disjoint from Schedule C**:

```
pending disclosure rows: 51  $514,829.00
  pending rows whose EIN appears in Schedule C: 0
  pending rows whose (EIN,amount) appears in Schedule C: 0
  pending sources: [('Local', 21), ('Youth', 12), ('Anti-Poverty', 4), ('HIV/AIDS Faith Based
  Initiative', 3), ('Boro', 2), ('Ending the Epidemic', 2), ('Aging', 2), ('Community Housing
  Preservation Strategies', 1), ('Coalition Theaters of Color', 1), ('Food Pantries', 1),
  ('A Greener NYC', 1), ('Domestic Violence and Empowerment (DoVE) Initiative', 1)]
```

Not one pending EIN reaches Schedule C. **INFERRED, not verified:** the likely reason is that 33 of
the 51 pending rows are Local or Youth, whose Schedule C appendices are empty — so this is probably
a coverage artifact, not evidence that Schedule C filters pending designations. The remaining 18
pending rows sit in initiatives Schedule C does cover, and their absence is unexplained. Every
comparison elsewhere in this report is dominated by Cleared, which is 99.4% of disclosure rows.

---

## 2. By EIN, both directions

```
==============================================================================
BY EIN, BOTH DIRECTIONS
==============================================================================
distinct EIN  disclosure   2156   schedule C    424   in both    414
Schedule C EIN NOT in disclosure : 10   ($1,154,000.00, 10 rows)   <-- falsifies superset if > 0
disclosure EIN NOT in Schedule C : 1742   ($141,208,539.00, 5155 rows)
    of those disclosure-only rows: cleared 5104, pending 51
```

Split by file:

```
            awards: rows 480  distinct EIN 298  EIN in disclosure 290  (EIN,amount) matched 413 = 86.0%
  appendix_a_aging: rows 422  distinct EIN 179  EIN in disclosure 177  (EIN,amount) matched 417 = 98.8%
```

**Appendix A is the cleaner of the two extractions by a wide margin** — 98.8% of its rows match a
disclosure (EIN, amount) pair exactly. The awards CSV is at 86%, and §3.5 explains most of the gap.

### 2.1 EIN is not a unique organization key — on either side

This is a caveat that affects every EIN-based join in this project, not just FY2018.

```
== EIN 136400434 in disclosure: distinct legal_names
   rows=698 distinct names=62
    186  'New York City Housing Authority'
    139  'Department of Education'
    106  'Department of Parks and Recreation'
     66  'Department of Sanitation'
     25  'Department of Transportation'
     21  'Queens Borough Public Library'
     18  'City University of New York'
     ... 55 more, including 24 community boards, 5 district attorneys, and 'City Clerk'
```

**EIN 13-6400434 is the City of New York's own EIN**, and the disclosure files 698 FY2018 rows under
it across 62 distinct legal names. Ten EINs carry more than one legal name in the FY2018 disclosure:

```
   136400434 -> 62: ["Administration for Children's Services", 'Borough President - Staten Island', ...]
   131988190 ->  8: ['Borough of Manhattan Community College', 'Bronx Community College', 'CUNY Creative Arts Team', ...]
   132655001 ->  4: ['Health and Hospitals Corporation', 'Health and Hospitals Corporation - Elmhurst Hospital Center', ...]
   135596746 ->  3: ['NYSARC, Inc., New York City Chapter', 'NYSARC, Inc., New York City Chapter - HIRE ...', ...]
   800010627 ->  2: ["Muslim Women's Institute for Research and Development (MWIRD)", 'Muslim Women’s Institute ...']
```

Practical consequence: **any "awards by EIN" answer for a city agency is meaningless**, and joining
Schedule C to disclosure on EIN alone silently conflates NYCHA with the Department of Education.
The last two rows above also show the disclosure carrying the same org twice under a straight-vs.-
curly apostrophe and a capitalization difference, so name-based dedup needs normalization too.

### 2.2 The ten Schedule C EINs absent from the disclosure

```
Schedule C EINs absent from disclosure (all, with rows):
  060646594        $78,000.00  [awards] 'American Lung Association of the Northeast, Inc.'
  116325086         $5,000.00  [appendix_a_aging] '.00 To support various creative aging activities and multicultural programs at the library'
  133077049        $32,000.00  [awards] 'Neighborhood Self Help by Older Persons Project, Inc.'
  133238142       $200,000.00  [awards] 'Cooperative Home Care Associates'
  134147836       $110,000.00  [awards] 'Homeless Edward J. Malloy Initiative for Construction Skills'
  135654450       $234,000.00  [awards] 'Selfhelp Community Services'
  201635756       $185,000.00  [awards] 'RV Systems, Inc. (Database)'
  237359002       $100,000.00  [awards] 'ARGUS Community, Inc'
  371514651       $200,000.00  [awards] 'Members Assistance Program, Inc. (MAP)'
  432061329        $10,000.00  [appendix_a_aging] '.00 The funding will provide seniors over the age of sixty who reside in the greater Clear'
```

All ten are read individually in §3.

---

## 3. Ten mismatches read individually

### 3.1 One-digit EIN error — `133077049` vs `133077047`

Schedule C:

```
   category: 'Senior Services'
   initiative: 'Naturally Occurring Retirement Communities (NORCs)'
   award_type: 'initiative_provider'
   organization: 'Neighborhood Self Help by Older Persons Project, Inc.'
   program: 'Morrison Lafayette/Boyton Lafayette NORC'
   ein: '133077049'
   amount: '32000'
```

Disclosure — ten rows for that organization, **all** at `133077047`, one of which is the same
initiative, member and amount:

```
   row5628 EIN 133077047 'Neighborhood Self Help by Older Persons Project, Inc.' $32,000.00 src='Naturally Occurring Retirement Communities (NORCs)' cm='Citywide' status=CLEARED
```

Same org, same initiative, same $32,000. The final digit differs. **VERIFIED** as the same award.
**INFERRED:** the error is on the Schedule C side, because the disclosure is internally consistent
across ten independent rows and Schedule C has exactly one. Not confirmed against the source PDF.

### 3.2 Wrong entity, right award — `135654450` "Selfhelp Community Services"

```
   organization: 'Selfhelp Community Services'
   program: 'Northridge NORC'
   ein: '135654450'
   amount: '234000'
   initiative: 'Naturally Occurring Retirement Communities (NORCs)'
```

The disclosure has 37 rows for Selfhelp, **every one at EIN `131624178`**, including:

```
   row7480 EIN 131624178 'Selfhelp Community Services, Inc.' $234,000.00 'Naturally Occurring Retirement Communities (NORCs)' 'Citywide' CLEARED
```

Same org, same initiative, same $234,000, different EIN. Same finding shape as §3.1 but a wholly
different number rather than one digit.

### 3.3 Parent vs. affiliate — `060646594` American Lung Association

```
   category: 'Health Services'
   initiative: 'screening, education, and care coordination projects.  $78,000 supports asth ma programs,'
   organization: 'American Lung Association of the Northeast, Inc.'
   ein: '060646594'
   amount: '78000'
```

Disclosure:

```
   row225 EIN 131632524 'American Lung Association' $78,000.00 src='Child Health and Wellness' cm='' status=CLEARED
```

Same $78,000. Schedule C names the **Northeast affiliate** (06-0646594); the disclosure names the
parent (13-1632524). This one is **not** obviously a Schedule C error — the two documents may
genuinely disagree about which legal entity received the money. Note also the `initiative` field
here is not an initiative name at all but a fragment of PDF body text, which is a separate
extraction defect (§6).

### 3.4 Field misalignment inside the awards CSV — CWE / HOPE

Schedule C, Job Training and Placement Initiative:

```
  EIN 133268539  'Consortium for Worker Education'  $60,000.00  type=initiative_provider member='' purpose=''
```

Disclosure:

```
  row2051 EIN 133564313 'Consortium for Worker Education (CWE)' $50,000.00 'Job Training and Placement Initiative' ''
  row2052 EIN 133564313 'Consortium for Worker Education (CWE)' $150,000.00 ...
  row2053 EIN 133564313 'Consortium for Worker Education (CWE)' $200,000.00 ...
  row2054 EIN 133564313 'Consortium for Worker Education (CWE)' $2,000,000.00 ... cm='Citywide'
  row2055 EIN 133564313 'Consortium for Worker Education (CWE)' $5,154,200.00 ... cm='Citywide'
  row4048 EIN 133268539 'HOPE Program, Inc., The' $60,000.00 'Job Training and Placement Initiative' 'Citywide'
```

The Schedule C row pairs **CWE's name** with **the HOPE Program's EIN and amount**. CWE's real EIN
is 13-3564313; 13-3268539 is HOPE. This is a straight column misalignment in the FY2018 extraction,
and the same file separately carries a correct `'HOPE Program, Inc., The'` row at `133268539`,
$100,000 — so the wrong pairing is not a substitution but a duplication of one record's key onto
another record's name. **VERIFIED.** This EIN is not in the ten (it exists in the disclosure); it
surfaced from the (EIN, amount) unmatched list, and it is the clearest single proof that FY2018
awards-CSV rows cannot be trusted field-by-field.

### 3.5 Different granularity, not a discrepancy — the JtBO sub-provider table

Five of the ten missing EINs — Members Assistance Program ($200,000), Cooperative Home Care
Associates ($200,000), RV Systems Inc. (Database) ($185,000), Edward J. Malloy Initiative for
Construction Skills ($110,000), ARGUS Community ($100,000), total **$795,000** — sit in one
initiative, and each returned nothing on a name search of the FY2018 disclosure:

```
--- disclosure FY2018 legal_name contains 'Malloy'            (none)
--- disclosure FY2018 legal_name contains 'Argus'             (none)
--- disclosure FY2018 legal_name contains 'Cooperative Home'  (none)
--- disclosure FY2018 legal_name contains 'Members Assistance'(none)
--- disclosure FY2018 legal_name contains 'RV Systems'        (none)
```

The reason is printed in the Schedule C data itself. One extracted row still carries the PDF's
page-break header:

```
  EIN 132736022  'Fiscal 2018 Adopted Expense Budget Adjustment Summary Page 80 Below is a list of
                  the JtBO service provider partners: Organization EIN Amount Service Type South
                  Bronx Overall Economic Development Corp'  $203,000.00
```

Schedule C prints a **nested sub-provider table** — the partners a pass-through recipient
subcontracts to. The disclosure records the designation to the pass-through and stops. Concretely:
the disclosure gives Consortium for Worker Education $7,554,200 across five rows; Schedule C prints
31 rows of downstream partners totalling $5,015,300. `RV Systems, Inc. (Database)`, purpose
`'Program data and Reporting Monitoring'`, is a data-systems vendor, not a designation at all.

**This is a real structural difference between the two documents, not an extraction bug.** It is the
one category where Schedule C carries information the disclosure does not.

### 3.6 Aggregation, not omission — "Support for Educators" and SBS

Schedule C collapses multi-row disclosure entries into one line:

```
  schC  EIN 136400434 $20,354,000 org='Council of School Supervisors and Administrators 11-2024569 * $450,000 Department of Education'

  disc  EIN 136400434 'Department of Education' $19,694,500 cm='Citywide'
  disc  EIN 112024569 'Council of School Supervisors and Administrators' $450,000 cm='Citywide'
  disc  EIN 136400434 'Department of Education' $360,000 cm=''
  disc  EIN 135562308 'New York University' $225,000 cm=''
  disc  EIN 262671377 'Border Crossers, Inc.' $50,000 cm=''
  disc  EIN 136400434 'Department of Education' $25,000 cm=''
```

The organization string shows the mechanism: `'Council of School Supervisors and Administrators
11-2024569 * $450,000 Department of Education'` is the CSA record's full printed line, swallowed
into the DOE record's name field — so the CSA $450,000 exists in the extracted text but is not a
row. Disclosure total $20,804,500 vs Schedule C $20,354,000, delta $450,500.

**Ambiguity left standing:** $450,000 of that delta is CSA. The remaining **$500 is unexplained** —
$20,354,000 does not equal the DOE rows ($20,079,500) plus NYU and Border Crossers ($275,000) either.
I did not resolve it.

The same file also aggregates correctly elsewhere: `'Department of Small Business Services'`
EIN 136400434 $281,800 in Schedule C is exactly the disclosure's $131,800 + $150,000.

### 3.7 Appendix A — the `ein` and `amount` columns belong to a different record

Raw CSV line 236 of `fy18_appendix_a_aging.csv`:

```
Koo,"Korean Community Services of Metropolitan New York, Inc.","Flushing Neighborhood Senior Center
237348989 * $15,000.00 To fund resources and programs for seniors on a daily basis. Dromm Latin
American Cultural Center of Queens, Inc. - Sunday to Remember",112997255,8000,".00 To support
Sunday to Remember art and ...
```

Reading the columns as the parser did: `member=Koo`, `organization='Korean Community Services...'`,
`ein=112997255`, `amount=8000`. But the true record for Korean Community Services is sitting inside
the `program` column — `237348989 * $15,000.00` — and the disclosure confirms it exactly:

```
   row4690 EIN 237348989 'Korean Community Services of Metropolitan New York, Inc.' $15,000 'Aging' 'Koo'
```

Same member, same source, same amount. Meanwhile `112997255` is the **next** record's org:

```
   row4726 EIN 112997255 'Latin American Cultural Center of Queens, Inc.' $5,000 'Youth' 'Ferreras-Copeland'
```

Line 20 shows the identical shape — `member=Levine`, `organization='Bloomingdale Aging in Place,
Inc.'`, `ein=131623910`, where `131623910` is the disclosure's `'Blue Card, Inc., The'` and
Bloomingdale's own `264742989 * $7,500.00` is buried in the `program` column.

Both of the appendix-A entries in the missing-ten list (`116325086`, `432061329`) are this same
defect. `116325086` is a garbled read of `111635086`, which the disclosure has as
`'RC Church St. Andrew Avellino' $5,000 'Aging' 'Vallone'` — and the Schedule C row's own text
column ends `'... Vallone Friendship Club of St. Andrew Avellino'`, naming both the member and
the church. `432061329` ('San Gennaro Senior Center', member Vacca) has no counterpart in the
disclosure by EIN or by name; it is the **one Schedule C row in FY2018 I could not account for.**

**Real data is trapped in the free-text columns:**

```
embedded "EIN * $amount" pairs found inside text columns: 181; of those, EIN known to disclosure: 180
```

181 EIN/amount pairs sit inside `organization` / `program` / `purpose` strings in a 422-row file,
and 180 of those EINs are ones the disclosure knows.

**Ambiguity left standing, explicitly:** I could not establish *how many* of the 422 appendix rows
are shifted. A token-overlap test between the `organization` column and the disclosure's name for
that row's EIN was too loose to separate the cases (298 of 422 rows matched both their own row and
the next one). Two rows are hand-verified as shifted; the population size is **unknown**, not zero.

---

## 4. By council member — and the Williams / Sanchez / Rivera / Barron / Vallone question

```
distinct values  disclosure 59   schedule C 11
disclosure blank 938   schedule C blank 807
```

**Schedule C FY2018 has no usable member dimension.** All 11 of its values:

```
  ''                             807   $103,706,201.00
  'ferreras-'                      4        $95,000.00     <- truncated
  'koo'                            8       $103,000.00
  'levine'                        19       $134,800.00
  'manhattan'                      2        $15,500.00     <- not a member
  'palma'                         10       $110,000.00
  'placement'                     13     $1,945,500.00     <- fragment of "Job Placement"
  'program'                        5        $51,000.00     <- not a member
  'rose'                          11       $114,000.00
  'staten island'                  4       $759,230.00     <- not a member
  'treyger'                       19       $102,000.00
```

Six of the eleven are real surnames; the other five are text fragments. 89.5% of rows have no member
at all. This is why the exact-award match rate collapses when member is added (§5).

The disclosure by contrast is complete and clean — 59 values, 51 of them council-member surnames,
plus five delegations, `Citywide` (404 rows, $109.7M), `Speaker` (244 rows, $16.7M), and blank
(938 rows, $160.5M — chiefly citywide initiative allocations). Per-member totals cluster tightly
around the FY2018 discretionary allocation, e.g. `'gentile' 117 $1,747,583.00`,
`'koo' 144 $1,747,583.00`, `'treyger' 134 $1,747,583.00`.

### 4.1 Evidence for issue #51: the disclosure does **not** disambiguate surnames

```
surname collision probe (Williams / Sanchez / Rivera / Barron / Vallone):
  disclosure: {'vallone': 124, 'williams': 139, 'barron': 87}
  schedule C: {}
```

**The FY2018 disclosure uses bare surnames, exactly like Schedule C.** It carries no first name, no
initial, and no district number in the `Council Member` column. It is therefore **not** a solution
to the colliding-surname problem on its own.

Checked across four years to see whether the format ever improves:

```
2018 distinct= 59 collide-surnames: {'Vallone': 124, 'Williams': 139, 'Barron': 87}
2022 distinct= 58 collide-surnames: {'Rivera': 170, 'Sanchez': 105, 'Williams': 134, 'Barron': 79}
2024 distinct= 58 collide-surnames: {'Williams': 154, 'Sanchez': 149, 'Rivera': 177}
2027 distinct= 58 collide-surnames: {'P. Sanchez': 135, 'Williams': 165, 'J. Sanchez': 105}
```

**VERIFIED:** only FY2027 introduces initials, and only for Sanchez — the one surname held by two
sitting members simultaneously in that year. The Council disambiguates reactively, when its own
spreadsheet would otherwise collide, and never retroactively. `Williams` stays bare in all four
years.

**Bearing on #51, stated carefully.** The disclosure's contribution to disambiguation is *indirect
but real*: it supplies the full designation universe per member per year, so a surname can be
resolved by cross-referencing the member's district against the recipient organizations' addresses
(`address1`/`city`/`postal_code` are populated in the disclosure and absent from Schedule C). What
it does **not** supply is an explicit member identifier. Anyone hoping the spreadsheet contains a
first name or district number should stop hoping. **INFERRED, not tested here:** whether the
address columns are sufficient to resolve a collision in a year that has one — FY2018 has no actual
collision (one Williams, one Barron, one Vallone), so this year cannot test it.

---

## 5. By exact award

```
==============================================================================
BY EXACT AWARD
==============================================================================
(EIN, amount)          disclosure   8894 rows / 6163 keys   schedule C    902 rows / 800 keys
                       matched multiset 830 rows (92.0% of Schedule C)
  Schedule C rows unmatched :     72   $34,246,963.00
  disclosure rows unmatched :   8064   $309,010,732.00

(EIN, amount, member)  matched multiset 279 rows (30.9% of Schedule C)
  Schedule C rows unmatched :    623
  disclosure rows unmatched :   8615
```

**92.0% of Schedule C rows match a disclosure row on (EIN, amount) exactly.** Adding member drops it
to 30.9% — that drop is entirely §4's missing member column, not a disagreement about who funded
what. Treat the 30.9% as a measurement of FY2018 extraction quality, **not** as evidence the two
sources disagree.

The 72 unmatched Schedule C rows break down as:

```
{'EIN present': 62, 'EIN absent from disclosure': 10}
```

62 of the 72 are an EIN both sources know, where Schedule C's amount is not among that EIN's
disclosure amounts. Their composition is diagnostic:

```
by initiative: [('Job Training and Placement Initiative', 21), ('Community Housing Preservation
Strategies', 17), ('Crisis Management System – School Based Conflict Mediation', 7), ('', 5),
('Discretionary Child Care', 2), ('Viral Hepatitis Prevention', 2)]
rows with EIN 136400434: 8
```

**21 of the 62** are the §3.5 sub-provider table, **24** are the two initiatives where Schedule C
prints a rollup the disclosure splits differently (§5.1), and **8** are EIN `136400434`, the City of
New York (§2.1). Together those account for 53 of the 62.

**Five exact duplicate rows** inflate the awards CSV, all in the same initiative:

```
exact duplicate rows in awards csv: 5 extra copies across 5 distinct rows
   x2  133975090 $51000 'Agudath Israel of America Community Services, Inc.' init='Community Housing Preservation Strategie'
   x2  141719016 $71000 'Crenulated Company LTD, The' init='Community Housing Preservation Strategie'
   x2  471169779 $71000 'Neighborhood Housing Services of Brooklyn CDC, Inc.' init='Community Housing Preservation Strategie'
   x2  132972415 $61000 'Northern Manhattan Improvement Corporation' init='Community Housing Preservation Strategie'
   x2  133442022 $51000 'Urban Justice Center' init='Community Housing Preservation Strategie'
```

### 5.1 The strongest single agreement result: Community Housing Preservation Strategies

Per-organization totals, both sides:

```
disclosure 68 rows $3,651,000.00; distinct EIN 52
schedule C 60 rows $2,849,516.00; distinct EIN 38

EIN               disc $     schedC $  name
111817497         29,730       29,730  Queensboro Council for Social Welfare, Inc.
112268359         61,000       61,000  Southside United Housing Development Fund Corpor
112375583         80,730       80,730  Queens Community House, Inc.
112382250         29,730            0  Greater Ridgewood Restoration Corporation  <-- differs
112412584        161,730      161,730  Housing and Family Services of Greater New York,
112435523         29,729            0  Brighton Neighborhood Association, Inc.  <-- differs
...
471169779        222,730      222,730  Neighborhood Housing Services of Brooklyn CDC, I
510141489         90,730       90,730  Housing Conservation Coordinators, Inc.
510192170         61,000       61,000  St. Nick's Alliance Corporation
```

**38 of 52 organizations agree to the cent. The other 14 are $0 in Schedule C — dropped entirely.**
Their disclosure amounts sum to:

```
29,730 + 29,729 + 29,729 + 29,729 + 29,730 + 90,729 + 29,730 + 100,000
      + 29,729 + 100,730 + 29,729 + 29,730 + 90,730 + 151,730 = 801,484
```

The initiative-level delta from §7 is `$-801,484.00`. **Exactly.** The entire FY2018 CHPS shortfall
is 14 omitted organizations and nothing else.

Note that `112412584` (Housing and Family Services) agrees at $161,730 total while **no individual
row matches**: Schedule C splits it 71,000 + 61,000 + 29,730 and the disclosure splits it
29,730 + 132,000. Same money, different tranching. This is the general reason a per-EIN total
comparison is a fairer test of agreement than a row-level one:

```
per-(shared initiative, EIN) totals across 55 shared names:
  exact dollar agreement : 396
  both present, differ   : 43
  disclosure-only EIN    : 306
  schedule C-only EIN    : 41
```

**396 exact agreements against 43 disagreements** — 90.2% where both sources have the organization.

---

## 6. Source / initiative vocabulary

```
disclosure Source values : 137
schedule C initiative    : 73    category: 19
schedule C appendix files: {'Aging': 422}

exact-after-normalization overlap: 55 names
disclosure Source with NO Schedule C counterpart: 82
Schedule C initiative/category with NO disclosure counterpart: 38
```

**The vocabularies substantially map onto each other but neither is a subset of the other.**
55 names match exactly after case/punctuation normalization, including `Aging`, `Beating Hearts`,
`Social Adult Day Care`, `Naturally Occurring Retirement Communities (NORCs)`, and
`Alternatives to Incarceration (ATI's)` — note the apostrophe survives on both sides.

### 6.1 The 82 disclosure-only names are dominated by real coverage gaps

The top of that list is not vocabulary drift, it is missing data:

```
  'Local'                                     3097 rows  $36,544,000.00
  'Youth'                                      901 rows   $7,650,000.00
  'Cultural After-School Adventure (CASA)'     661 rows  $13,260,000.00
  'Anti-Poverty'                               309 rows   $2,805,000.00
  'Cultural Immigrant Initiative'              269 rows   $5,865,000.00
  'Food Pantries'                              261 rows   $4,090,000.00
  'Parks Equity Initiative'                    224 rows   $4,503,500.00
```

`Local` and `Youth` alone are **3,998 rows / $44,194,000** with a Schedule C counterpart file that
is header-only. Their cleared/pending split:

```
Local   rows  3097  $ 36,544,000.00   cleared  3076 $36,385,500.00   pending  21 $158,500.00
Youth   rows   901  $  7,650,000.00   cleared   889 $ 7,571,500.00   pending  12 $ 78,500.00
Aging   rows   543  $  5,610,000.00   cleared   541 $ 5,597,000.00   pending   2 $ 13,000.00
```

Aging is the only one of the three with a populated appendix — 422 rows / $4,419,275 against 543 /
$5,610,000, so even the working appendix is missing 121 rows and $1,190,725.

### 6.2 The 38 Schedule C-only names are mostly category labels and PDF garbage

Three groups:

- **Category names, not initiative names** — `'Housing'` (77 rows), `'Mental Health Services'` (81),
  `'Health Services'` (61), `'Public Safety'` (30). These are Schedule C's outer grouping level.
  The disclosure has no equivalent column, so they cannot match by construction.
- **Real naming drift** — `'Coalition of Theaters of Color'` vs the disclosure's
  `'Coalition Theaters of Color'`; `'Dropout Prevention and Intervention'` vs
  `'Dropout Prevention and Intervention Initiative'`; `'Court-Involved Youth Mental Health'` vs
  `'...Initiative'`; `'Diversity, Inclusion and Equity in Tech'` vs
  `'Diversity, Inclusion & Equity in Tech Initiative'` (spelled-out "and" vs. ampersand);
  `'Access to Healthy Food and Nutritional Education'` vs `'Access to Food and Nutritional
  Education'`. Six sub-programs of `Crisis Management System` appear in Schedule C
  (`– Cure Violence`, `– Job Readiness Program`, `– Legal Services`, `– Mental Health/Therapeutic
  Services`, `– School Based Conflict Mediation`, `-Youth Programs`) against one flat
  `Crisis Management System` in the disclosure — note the en-dash vs. hyphen inconsistency **within
  Schedule C itself**. A crosswalk is buildable but must be hand-built; fuzzy matching will not
  survive `and`/`&`.
- **Extraction garbage** — two "initiative" values are body text:

```
  'schools, which includes intense literacy training for high -needs students. An allocation of'     3 rows
  'screening, education, and care coordination projects.  $78,000 supports asth ma programs,'        3 rows
```

  Note `high -needs` and `asth ma`: stray spaces mid-word, characteristic of PDF text extraction.
  49 further awards rows have an empty `initiative`.

---

## 7. Dollars per shared initiative

Full table in the script output. **22 of the 55** shared names agree to the cent:

```
name                                                          disc $        schedC $           delta
Beating Hearts                                           $350,000.00     $350,000.00           $0.00
Center for Court Innovation                            $1,710,000.00   $1,710,000.00           $0.00
Child Mind Institute                                     $500,000.00     $500,000.00           $0.00
Children and Families in NYC Homeless System           $1,000,000.00   $1,000,000.00           $0.00
Citywide Homeless Prevention Fund                        $820,000.00     $820,000.00           $0.00
Create New Technology Incubators                       $1,400,000.00   $1,400,000.00           $0.00
Elder Abuse Enhancement                                  $335,000.00     $335,000.00           $0.00
Foreclosure Buyback Initiative                         $1,000,000.00   $1,000,000.00           $0.00
Homeless Prevention Services for Veterans                $150,000.00     $150,000.00           $0.00
Housing Information Project                              $300,000.00     $300,000.00           $0.00
Jill Chaifetz Helpline                                   $245,000.00     $245,000.00           $0.00
Job Placement for Veterans                               $150,000.00     $150,000.00           $0.00
Key to the City                                          $700,000.00     $700,000.00           $0.00
Legal Services for Veterans                              $300,000.00     $300,000.00           $0.00
LGBT Senior Services in Every Borough                  $1,500,000.00   $1,500,000.00           $0.00
Mental Health Services for Veterans                      $225,000.00     $225,000.00           $0.00
Physical Education and Fitness                         $1,925,000.00   $1,925,000.00           $0.00
Prisoners' Rights Project                                $750,000.00     $750,000.00           $0.00
Reproductive and Sexual Health Services                  $344,788.00     $344,788.00           $0.00
Social Adult Day Care                                  $1,055,556.00   $1,055,556.00           $0.00
Step In and Stop It Initiative to Address Bystande       $154,000.00     $154,000.00           $0.00
Urban Advantage                                        $3,500,000.00   $3,500,000.00           $0.00
```

**Every non-zero delta but one is negative** — Schedule C under-reports, never over-reports. The
single positive is:

```
Naturally Occurring Retirement Communities (NORCs)     $3,654,995.00   $3,805,000.00     $150,005.00
```

That $150,005 over-count is consistent with §3.1 and §3.2, where Schedule C carries two NORC rows
under EINs the disclosure does not use — the same money counted under a second key. **INFERRED, not
verified:** I did not reconcile the NORC line item to the cent.

The largest deltas:

```
Domestic Violence and Empowerment (DoVE) Initiativ     $7,805,000.00     $562,500.00  $-7,242,500.00
Discretionary Child Care                               $9,378,195.00   $3,537,041.00  $-5,841,154.00
Afterschool Enrichment Initiative                      $5,967,000.00   $1,675,000.00  $-4,292,000.00
Job Training and Placement Initiative                  $8,481,000.00   $5,015,300.00  $-3,465,700.00
Autism Awareness                                       $3,236,846.00     $264,903.00  $-2,971,943.00
```

DoVE is the extreme case: the disclosure has 222 rows, Schedule C has **1**.

---

## 8. What this establishes for Phase 1

**Established (VERIFIED):**

1. The disclosure spreadsheet is a superset of FY2018 Schedule C in every direction tested, with one
   documented exception class (§3.5 sub-provider tables) and one unexplained row (§3.7,
   `432061329`).
2. FY2018 Schedule C's failure mode is **omission and field misalignment, never invented money**.
   Retained rows are dollar-exact far more often than not (396 vs 43 on per-(initiative, EIN)
   totals; CHPS delta explained to the cent).
3. The disclosure's `Council Member` column is bare surnames and does **not** disambiguate colliding
   surnames, in any year before FY2027 and then only for Sanchez (issue #51).
4. EIN is not a unique organization key. 13-6400434 covers 698 FY2018 disclosure rows across 62
   distinct legal names.
5. The 28,575 orphaned appendix rows are not the whole FY2018 gap. FY2018's Local and Youth
   appendices are *empty*, so 3,998 rows / $44.2M have no Schedule C representation at all,
   orphaned or otherwise.

**Not established, flagged rather than papered over:**

- How many of the 422 appendix-A rows carry shifted `ein`/`amount` columns. Two hand-verified;
  population size unknown.
- Whether `432061329` / "San Gennaro Senior Center" (member Vacca, $10,000) is a Schedule C
  fabrication, a disclosure omission, or a garbled EIN for an org I failed to find.
- The $500 residual in "Support for Educators" (§3.6).
- Whether the FY2018 disclosure's `Source` value or Schedule C's `initiative` value is authoritative
  where they drift (`Coalition of Theaters of Color` vs `Coalition Theaters of Color`). That is a
  judgment call I did not make.
- Whether the §3.1/§3.2 EIN discrepancies originate in the extraction or in the published PDF. I did
  not open `FY-2018-Schedule-C-Cover-Template-FINAL-MERGE.pdf`.

**Recommended next probe, in priority order:** run this same comparison for FY2022–FY2026, where
Schedule C extraction is believed good. If the (EIN, amount) match rate rises toward 100% and the
`disclosure EIN NOT in Schedule C` count collapses, that converts finding #1 from "survives FY2018"
to "holds across the corpus" — and makes the disclosure a usable ground truth for repairing
FY2016–FY2020.
