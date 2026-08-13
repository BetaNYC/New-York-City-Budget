---
title: "FY2024 source comparability — Council expense disclosure vs. parsed Schedule C"
created: 2026-08-12
type: research-note
status: complete
tags: [nyc-budget, schedule-c, source-comparability, fy2024]
---

# FY2024: disclosure workbook vs. parsed Schedule C

**Report generated:** 2026-08-12 00:18 EDT
**Data current as of:** files on disk at that time. No network calls were made.

**Inputs**

| | path | fingerprint |
|---|---|---|
| disclosure | `source/expense-funding-disclosure/funded_disclosure_FY2024.xlsx` | sha256 `a128abad…4dd47d`, sheet `FY24 (06-08-26)` |
| Schedule C | `data/fy24/schedule_c/fy24_schedule_c_awards.csv` | 5,368 rows |
| | `data/fy24/schedule_c/fy24_appendix_{a_aging,b_local,c_youth}.csv` | 477 / 2,616 / 818 rows |
| | `data/fy24/schedule_c/fy24_schedule_c_initiatives.csv` | 146 rows |
| reader | `code/parse_expense_disclosure.py` (commit `7cd320b`) | stdlib only |
| this analysis | `research/phase1-source-comparability/compare_2024.py` | read-only, prints only |

Nothing under `data/`, `source/`, `viz/`, or `code/` was modified.

**Live-state correction.** The brief for this run stated that the 28,575 appendix rows
"reach no consumer" and that `grep -c appendix mcp/scripts/build-index.mjs` returns 0. That
was true when the brief was written and is **no longer true**. A parallel session committed
`4c822a3 mcp: load the 28,575 Schedule C appendix rows into the index (1.4.0)` to this same
branch during this run:

```
$ git log --oneline -2
4c822a3 mcp: load the 28,575 Schedule C appendix rows into the index (1.4.0)
7cd320b Add stdlib-only parser for Council expense disclosure workbooks
$ grep -c -i appendix mcp/scripts/build-index.mjs          # working tree
20
$ git show HEAD:mcp/scripts/build-index.mjs | grep -c -i appendix
20
$ sqlite3 read-only: select source_table, appendix_stream, count(*), sum(amount)
                     from awards where fiscal_year=2024 group by 1,2
  ('appendix','aging',  477,  5610000)
  ('appendix','local', 2616, 36539000)
  ('appendix','youth',  818,  7650000)
  ('schedule_c','',    5368,400663574)
```

`mcp/data/budget.db` was rebuilt at `2026-08-12T04:13:41Z` and now holds all 9,279 FY2024
Schedule C rows, $450,462,574. Every FY2024 figure below is stated against the CSVs, which
are unchanged, so the analysis stands either way — but any downstream claim about what the
MCP exposes must be re-read, not carried forward.

---

## Verdict

**FY2024 disclosure and FY2024 Schedule C describe the same universe of designations. They
are not interchangeable, and neither is a superset of the other.**

Three findings carry that verdict, in descending order of consequence:

1. **The two sources are on different Council time bases.** Schedule C carries the members
   seated when the budget was adopted; the disclosure carries the members seated when the
   workbook was last refreshed. Joining the two on surname silently mis-assigns money —
   most sharply for `Brannan`, a single surname that means **district 43 in Schedule C and
   district 47 in the disclosure**.
2. **The three appendix streams agree to the exact dollar** ($5,610,000 / $36,539,000 /
   $7,650,000) while carrying different row counts. Every dollar of the discrepancy is
   accounted for. This is the strongest evidence available that the two sources are the
   same universe.
3. **The `_schedule_c_awards.csv` extraction is short $71,264,926 against the Schedule C
   document's own printed category totals** — a defect visible without the disclosure at
   all. Against the document's printed totals the disclosure is within **1.2%**; against
   the extracted award rows it is off by **17.2%**.
4. **Pending rows must be included, not filtered out.** The exact stream agreement in (2)
   only holds with them. Filtering to Cleared breaks all three streams and doubles the
   Schedule C-only EIN count. The adopted Schedule C contains designations the disclosure
   still marks Pending.

The claim "disclosure is a superset of Schedule C" is **false**. 40 EINs and 65 rows worth
$1,768,000 exist in Schedule C and not in the disclosure, and only 2 of the 40 are
explainable as key errors.

---

## 1. Headline counts and dollars

```
$ python3 research/phase1-source-comparability/compare_2024.py totals

disclosure rows              10811   $527,971,414
  Cleared                    10731   $526,907,681
  Pending                       80     $1,063,733

schedule C awards             5368   $400,663,574
schedule C a_aging             477     $5,610,000
schedule C b_local            2616    $36,539,000
schedule C c_youth             818     $7,650,000
schedule C TOTAL              9279   $450,462,574

row delta   disclosure - scheduleC = +1532
$   delta   disclosure - scheduleC = +77,508,840
```

That $77.5M gap is mostly **not** a disclosure-vs-Schedule-C difference. It decomposes:

```
initiatives.csv (category totals)   $   471,928,500   (146 rows)
awards.csv (award level)            $   400,663,574   (5368 rows)
appendices A+B+C                    $    49,799,000

initiatives + appendices            $   521,727,500
awards      + appendices            $   450,462,574
disclosure workbook                 $   527,971,414

disclosure - (initiatives+appx)     $    +6,243,914      <- 1.2%
disclosure - (awards+appx)          $   +77,508,840      <- 17.2%
initiatives - awards (unexploded)   $   +71,264,926      <- internal to Schedule C
```

**VERIFIED.** $71,264,926 of the $77.5M is money the Schedule C document itself accounts
for at the category level but whose award-level rows were never extracted. Measured against
Schedule C's own printed totals plus the appendices, the disclosure is $6,243,914 higher —
1.2%.

Where the unexploded money sits, by category (`initiatives.csv` minus `awards.csv`):

```
SMALL BUSINESS SERVICES AND WORKFORCE DEVELOPMENT   47,822,020   24,433,495   +23,388,525
PUBLIC SAFETY                                       26,961,475    4,026,600   +22,934,875
HIGHER EDUCATION INITIATIVES                        24,011,869    6,670,000   +17,341,869
LIBRARIES                                           15,700,000      812,054   +14,887,946
CRIMINAL JUSTICE SERVICES                           28,711,645   15,330,719   +13,380,926
YOUNG WOMEN'S INITIATIVE                            16,027,048    5,046,393   +10,980,655
CULTURAL ORGANIZATIONS                              34,350,000   26,271,923    +8,078,077
...
SPEAKER'S INITIATIVE TO ADDRESS CITYWIDE NEEDS       2,830,000   48,262,020   -45,432,020
YOUTH SERVICES                                               0   13,472,048   -13,472,048
COMMUNITY SAFETY AND VICTIM SERVICES                 5,100,000   16,108,726   -11,008,726
TOTAL                                              471,928,500  400,663,574   +71,264,926
```

The two large negative rows are a **category-assignment inconsistency inside the Schedule C
extraction**, not extra money. `initiatives.csv` files the Speaker's money under Small
Business:

```
$ grep -n "Speaker" data/fy24/schedule_c/fy24_schedule_c_initiatives.csv
127:SMALL BUSINESS SERVICES AND WORKFORCE DEVELOPMENT,,Multiple Speaker's Initiative to Address Citywide Needs,47822020
```

`awards.csv` files the same money under `SPEAKER'S INITIATIVE TO ADDRESS CITYWIDE NEEDS`
($48,262,020, 505 rows). The disclosure's own `Speaker's Initiative` Source is $48,277,020
across 523 rows — within $15,000 of the awards figure, and it corroborates the
`awards.csv` categorization over the `initiatives.csv` one.

**Cleared vs Pending — and the Pending rows are load-bearing.** FY2024 is 99.3% Cleared
(10,731 rows). The 80 Pending rows carry $1,063,733 and are concentrated in `Local` (37),
`Youth` (7), `Anti-Poverty` (5), `Aging` (5). **70 of the 80 have their `(EIN, amount)`
present in Schedule C**, so Pending status does not predict absence from Schedule C.

I recomputed every headline figure on the Cleared-only subset. It does **not** leave the
findings intact — dropping Pending rows destroys the exact stream agreement:

```
ALL            disc rows  10811  $  527,971,414
               SC-only EINs   40  rows   65  $ 1,768,000
               (EIN,amount) matched  9028  (97.3% of SC rows)
               (EIN,amt,member)      7697  (83.0% of SC rows)
               Local  disc $ 36,539,000 | appx $ 36,539,000  delta        +0
               Youth  disc $  7,650,000 | appx $  7,650,000  delta        +0
               Aging  disc $  5,610,000 | appx $  5,610,000  delta        +0

CLEARED-ONLY   disc rows  10731  $  526,907,681
               SC-only EINs   88  rows  126  $ 2,362,800
               (EIN,amount) matched  8967  (96.6% of SC rows)
               (EIN,amt,member)      7651  (82.5% of SC rows)
               Local  disc $ 36,269,500 | appx $ 36,539,000  delta  -269,500
               Youth  disc $  7,597,000 | appx $  7,650,000  delta   -53,000
               Aging  disc $  5,565,000 | appx $  5,610,000  delta   -45,000
```

**VERIFIED, and it corrects an assumption worth naming.** The adopted Schedule C contains
designations the disclosure still carries as **Pending**. Pending does not mean "not in the
budget" — it means the clearance step has not completed. Filtering to Cleared drops
$367,500 across the three appendix streams and more than doubles the Schedule C-only EIN
count (40 → 88). **Any reconciliation against Schedule C must include Pending rows.** This
will matter far more for FY2027, which is 49.8% Pending.

---

## 2. The three appendix streams: exact dollar agreement

```
$ python3 research/phase1-source-comparability/compare_2024.py appendix

stream      disclosure n  appendix n          disc $          appx $     $ delta
Aging                488         477       5,610,000       5,610,000           0
Local               2658        2616      36,539,000      36,539,000           0
Youth                833         818       7,650,000       7,650,000           0
```

**VERIFIED, and this is the single most important result in the report.** Three independent
streams, extracted from a 453-page PDF, land on the Council's own published totals to the
dollar while differing in row count. Coincidence is not available as an explanation.

The disclosure side has a clean generating rule:

```
Disclosure Local 'Speaker': 180 rows $16,139,000
Other Local members: 51, each exactly $400,000 = $20,400,000; +Speaker = $36,539,000
```

Every non-Speaker member gets exactly **$400,000 Local, $150,000 Youth, $110,000 Aging**.
The per-member allocation is a hard constant, which makes per-member totals a precise test.

---

## 3. Council member: the two sources are on different time bases

### The member column is a bare surname on both sides

```
$ python3 research/phase1-source-comparability/compare_2024.py members

  surname-collision check -- does either side carry a first name/district?
    Williams   disclosure values=['Williams'] n=154 | scheduleC values=['Williams'] n=148
    Sanchez    disclosure values=['Sanchez']  n=149 | scheduleC values=['Sanchez']  n=137
    Rivera     disclosure values=['Rivera']   n=177 | scheduleC values=['Rivera']   n=115
    Barron     disclosure values=[]           n=0   | scheduleC values=['Barron']   n=88
    Vallone    disclosure values=[]           n=0   | scheduleC values=[]           n=0
```

**VERIFIED — evidence for issue #51.** The disclosure publishes a bare surname, exactly like
Schedule C. It carries **no first name and no district**. It does **not** disambiguate
Williams / Sanchez / Rivera / Barron / Vallone. Adopting the disclosure as a member source
buys nothing on this axis directly.

### But within FY2024 there is no surname collision at all

Program-name and purpose text carry literal `Council District NN` strings. Grouping those by
surname gives an independent district attribution that needs no external roster:

```
  Williams     disc {27: 73}    | sc {27: 52}
  Sanchez      disc {14: 74}    | sc {14: 41, 15: 1}
  Rivera       disc {2: 46}     | sc {2: 15}
  Barron       disc {}          | sc {42: 41}
  Vallone      disc {}          | sc {}
```

**VERIFIED.** Every FY2024 surname on both sides resolves to exactly one district. No
FY2024 surname denotes two people. The only multi-district labels are the four aggregate
ones — `Bronx Delegation`, `Brooklyn Delegation`, `Queens Delegation`, `Speaker` — which are
aggregates by design.

### The collision that actually bites is across sources, not within one

```
  Banks        disc {42: 64}    | sc {}
  Marmorato    disc {13: 65}    | sc {}
  Salaam       disc {9: 54}     | sc {}
  Zhuang       disc {43: 97}    | sc {}
  Brannan      disc {47: 110}   | sc {43: 57}      <-- SAME NAME, DIFFERENT DISTRICT
  Kagan        disc {}          | sc {47: 83}
  Jordan       disc {}          | sc {9: 24}
  Velazquez    disc {}          | sc {13: 29}
```

The member sets differ in a way that is not noise:

```
  in SCHEDULE C but not in disclosure:        in DISCLOSURE but not in Schedule C:
       88 rows  'Barron'                          95 rows  'Banks'
      117 rows  'Jordan'                         121 rows  'Salaam'
      152 rows  'Kagan'                          151 rows  'Zhuang'
      127 rows  'Velazquez'                      130 rows  'Marmorato'
```

Restricting to rows whose `(EIN, amount)` matches across sources and whose member differs
produces a dominant substitution map:

```
    69   scheduleC 'Brannan'    -> disclosure 'Zhuang'
    65   scheduleC 'Kagan'      -> disclosure 'Brannan'
    62   scheduleC 'Jordan'     -> disclosure 'Salaam'
    48   scheduleC 'Barron'     -> disclosure 'Banks'
    44   scheduleC 'Brooklyn'   -> disclosure 'Brooklyn Delegation'
    41   scheduleC 'Velazquez'  -> disclosure 'Marmorato'
    23   scheduleC 'Queens'     -> disclosure 'Queens Delegation'
    17   scheduleC 'Manhattan'  -> disclosure 'Manhattan Delegation'
```

**VERIFIED:** the substitutions exist, at those counts, and the district attributions above
confirm each pair shares a district (Jordan/Salaam → 9, Barron/Banks → 42,
Velazquez/Marmorato → 13, Kagan→47 = Brannan-in-disclosure→47, Brannan-in-ScheduleC→43 =
Zhuang→43).

**INFERRED:** that the cause is the Council term turning over between the FY2024 adopted
budget (Schedule C, adopted June 2023) and the disclosure's `06-08-26` refresh, with
`Brannan` additionally changing districts. The mechanism is consistent with every count and
every district attribution above, but I did not verify it against a roster — that would
require a network call, which was out of scope tonight.

**Practical consequence, independent of the cause.** A naive surname join across these two
sources mis-assigns at least 134 rows: 69 Schedule C `Brannan` rows join to the wrong person
(the disclosure's `Brannan` is a different district), and 65 Schedule C `Kagan` rows find no
partner at all while the disclosure's `Brannan` rows sit unclaimed. The member column is not
a stable key across sources and should not be treated as one.

Also present in Schedule C and not in the disclosure, and **not** roster changes:

```
       38 rows  'Center'      <- PDF extraction garbage
       12 rows  'Program'     <- PDF extraction garbage
        5 rows  'Brooks-'     <- 'Brooks-Powers' broken at the hyphen
```

---

## 4. The appendix member defect, fully closed

Per-member stream totals, with the successor substitution applied to the **Schedule C side
only**:

```
### Local  disc $36,539,000 / sc $36,539,000
    members either side: 56;  per-member totals agree EXACTLY: 44
      center                 disc    0r $        0 | sc    2r $   34,500  delta   -34,500
      lee                    disc   36r $  400,000 | sc   35r $  370,500  delta   +29,500
      program                disc    0r $        0 | sc    3r $   21,000  delta   -21,000
      manhattan delegation   disc    0r $        0 | sc    3r $   13,000  delta   -13,000
      aviles                 disc   23r $  400,000 | sc   22r $  390,000  delta   +10,000
      brooklyn delegation    disc    0r $        0 | sc    2r $   10,000  delta   -10,000
      hanif                  disc   55r $  400,000 | sc   53r $  390,000  delta   +10,000
      powers                 disc   72r $  400,000 | sc   70r $  390,000  delta   +10,000
      gennaro                disc   50r $  400,000 | sc   49r $  394,000  delta    +6,000
      brannan                disc   66r $  400,000 | sc   56r $  395,000  delta    +5,000
      hanks                  disc   95r $  400,000 | sc   94r $  395,000  delta    +5,000
      adams                  disc   41r $  400,000 | sc   39r $  397,000  delta    +3,000

### Youth  agree EXACTLY: 49/52     ### Aging  agree EXACTLY: 46/53
      program   -15,000                  center   -63,500   riley  +27,500
      williams  +10,000                  program   -7,000   louis  +21,000
      brooks-powers +5,000                                  salamanca +10,000
                                                            banks  +7,000  zhuang +5,000
```

The shortfalls are not missing money. They are money filed under a garbage member string:

```
Local   shortfall on real members $   78,500   dollars on garbage member strings $   78,500   equal=True
Youth   shortfall on real members $   15,000   dollars on garbage member strings $   15,000   equal=True
Aging   shortfall on real members $   70,500   dollars on garbage member strings $   70,500   equal=True
ALL                               $  164,000                                     $  164,000   equal=True
```

**VERIFIED.** 17 appendix rows carrying exactly $164,000 have a non-roster string in the
`member` column, and that $164,000 is exactly the amount by which the real members fall
short. Nothing is lost; 17 rows are mis-attributed.

### The mechanism, read row by row

Every one of the 17 is the same defect: a PDF page-wrap put the **previous** row's trailing
purpose text into the `organization` field, which shifted the true member name into the
middle of the org string and left the `member` field holding the last word of the previous
line. All 17 are quoted in full below with their disclosure counterparts.

```
SC  a_aging:34    member='Center'       $  21,000 EIN=113199040
       org='in the 42nd Council District. Louis Bergen Basin Community Development Corporation d/b/a Millennium Development'
       program='Philip Howard Houses'
  ->DISC xlsx-row 912    member='Louis'  $21,000 Cleared
       name='Bergen Basin Community Development Corporation d/b/a Millennium Development'
       program='Philip Howard Houses'
```

Purpose tail `in the 42nd Council District.`, then the true member `Louis`, then the org.
`Center` came off the previous row. The disclosure confirms member, amount, org, and program
exactly.

```
SC  b_local:2250  member='Center'       $  29,500 EIN=112591783
       org='in Harlem. Lee Services Now for Adult Persons (SNAP), Inc.'
  ->DISC xlsx-row 9199   member='Lee'    $29,500 Cleared
       name='Services Now for Adult Persons (SNAP), Inc.'
```

This one alone is the entire `lee` Local shortfall of $29,500.

```
SC  a_aging:350   member='Center'       $  27,500 EIN=136213586
       org='in addition to programming for health and social activities. Riley Regional Aid for Interim Needs, Inc.'
       program='Boston East Neighborhood Senior Center'
  ->DISC xlsx-row 8638   member='Riley'  $27,500 Cleared
       name='Regional Aid for Interim Needs, Inc.'  program='Boston East Neighborhood Senior Center'

SC  a_aging:333   member='Center'       $  10,000 EIN=131981482
       org='including congregate meals, classes/workshops, and related supplies and materials in Council District 16. Salamanca Presbyterian Senior Services, Inc.'
       program='Jackson & Davidson Senior Centers - Council District 17'
  ->DISC xlsx-row 8224   member='Salamanca'  $10,000 Cleared
       name='Presbyterian Senior Services, Inc.'
       program='Jackson & Davidson Senior Centers - Council District 17'

SC  a_aging:395   member='Center'       $   5,000 EIN=131624178
       org='as well as transportation services for medical appointments. Brannan Selfhelp Community Services, Inc.'
       program='Social Services & Benefits Assistance'
  ->DISC xlsx-row 9132   member='Zhuang'  $5,000 Cleared
       name='Selfhelp Community Services, Inc.'  program='Social Services & Benefits Assistance'
```

Note the last one: the org string names `Brannan`, and the disclosure says `Zhuang` — the
district-43 substitution again, this time embedded inside a corrupted cell.

```
SC  b_local:568   member='Center'       $   5,000 EIN=133893536
       org='at CCNY. It will support public events focuses on LGBTQ+ themes and support the core programming of LGBTQ+ CUNY students, including the Mixner Fellowship. Hanks City University of New York'
       program='College of Staten Island - Liberty Partnership Student Success Program'
  ->DISC xlsx-row 2437   member='Hanks'  $5,000 Cleared  name='City University of New York'
       program='College of Staten Island - Liberty Partnership Student Success Program'

SC  b_local:2132  member='Program'      $  10,000 EIN=112734261
       org='funding will be used to address the social challenges faced by youth as a result of COVID-19. Aviles Regina Opera Company, Inc.'
  ->DISC xlsx-row 8636   member='Aviles' $10,000 Cleared  name='Regina Opera Company, Inc.'

SC  b_local:595   member='Program'      $   6,000 EIN=475518278
       org='(BCTA). Gennaro Climate Museum'
  ->DISC xlsx-row 2518   member='Gennaro' $6,000 Cleared  name='Climate Museum'

SC  b_local:2276  member='Program'      $   5,000 EIN=463003829
       org='in Council District 7. Hanif Smith Street Stage, Inc.'
       program='Shakespeare in Carroll Park'
  ->DISC xlsx-row 9320   member='Hanif'  $5,000 Cleared  name='Smith Street Stage, Inc.'
       program='Shakespeare in Carroll Park'

SC  c_youth:228   member='Program'      $  10,000 EIN=770695007
       org='in Council District 7. Williams Community Youth Care Services, Inc.'
  ->DISC xlsx-row 2693   member='Williams' $10,000 Cleared  name='Community Youth Care Services, Inc.'

SC  c_youth:141   member='Program'      $   5,000 EIN=452796896
       org='(CACNY-YAMTSP), CACNY Year round programming including TESA (Technology, Education, Skills, & Arts Development) and academic support. Brooks-Powers Caribbean American Society of New York, Inc.'
       program='Council District'
  ->DISC xlsx-row 1779   member='Brooks-Powers' $5,000 Cleared
       name='Caribbean American Society of New York, Inc.'  program='Council District 31'

SC  b_local:602   member='Manhattan'    $   5,000 EIN=133072967
       org='(two vans with 17 feeding sites) and the Bronx (one van with eight feeding sites). Powers Coalition for the Homeless, Inc.'
       program='Grand Central Van Food Program - Council District 4'
  ->DISC xlsx-row 2543   member='Powers' $5,000 Cleared  name='Coalition for the Homeless, Inc.'
       program='Grand Central Van Food Program - Council District 4'

SC  b_local:1479  member='Manhattan'    $   5,000 EIN=132613958
       org='residents. Powers Manhattan Legal Services'   program='Council District 4'
  ->DISC xlsx-row 6307   member='Powers' $5,000 Cleared  name='Manhattan Legal Services'
       program='Council District 4'

SC  b_local:2213  member='Manhattan'    $   3,000 EIN=133164464
       org='public schools. Adams Samaritans of New York, Inc.'
       program='Suicide Prevention - Council District 28'
  ->DISC xlsx-row 9007   member='Adams'  $3,000 Cleared  name='Samaritans of New York, Inc.'
       program='Suicide Prevention - Council District 28'

SC  b_local:170   member='Brooklyn'     $   5,000 EIN=113395358
       org='Holocaust Park. Kagan Association of Holocaust Survivors from the Former Soviet Union, Inc.'
       program='Holocaust Survivors Programs'
  ->DISC xlsx-row 706    member='Brannan' $5,000 Cleared
       name='Association of Holocaust Survivors from the Former Soviet Union, Inc.'
       program='Holocaust Survivors Programs'

SC  b_local:1829  member='Brooklyn'     $   5,000 EIN=133471084
       org='Collaborative Studies. Hanif New York City Outward Bound Center, Inc.'
       program='Middle School 839K (15K839)'
  ->DISC xlsx-row 7405   member='Hanif'  $5,000 Cleared  name='New York City Outward Bound Center, Inc.'
       program='Middle School 839K (15K839)'
```

**16 of 17 are confirmed against a disclosure row matching on stream, EIN, amount, and
usually program name.** The seventeenth is a full page-header bleed and has no counterpart:

```
SC  a_aging:35    member='Program'      $   7,000 EIN=113199040
       org='will support a NORC program at the Philip Howard Houses. It will allow the seniors of the
            building to come down and have a place to socialize and attend health/wellness classes.
            Appendix A: Aging Discretionary Page 3 Council Member Legal Name of Organization'
       program='Program Name Tax ID Amount Purpose of Funds Barron Bergen Basin Community Development
                Corporation d/b/a Millennium Development - Spring Creek Senior Partners Senior Center'
  ->DISC  no (source, EIN, amount) match
```

The row has swallowed the page header (`Appendix A: Aging Discretionary Page 3`) and the
column headers (`Council Member Legal Name of Organization` / `Program Name Tax ID Amount
Purpose of Funds`). **Ambiguity, stated not resolved:** the buried text names `Barron` and a
Spring Creek program, which would make the true member `Banks` — but I could not confirm the
$7,000 against any disclosure row, and I am not going to assert a member for it. The
`program` cell is not a program name; it is header text.

This is a mechanical, fixable defect with a clear signature: an appendix row whose `member`
value is not on the roster, whose `organization` begins mid-sentence in lowercase, and whose
true member appears as a token inside the org string. **Out of scope for tonight** (the
corpus is read-only), but it is a concrete parser fix worth its own task.

---

## 5. EIN coverage, both directions

```
$ python3 research/phase1-source-comparability/compare_2024.py ein

distinct EIN in disclosure  2164
distinct EIN in schedule C  2142
intersection                2102
disclosure-only               62
SCHEDULE C-ONLY               40   <-- falsifies 'disclosure is a superset'

Schedule C-only EINs cover 65 rows, $1,768,000
  by file: {'awards': 32, 'b_local': 22, 'a_aging': 5, 'c_youth': 6}
```

### The direction that matters: Schedule C EINs absent from the disclosure

**VERIFIED: 40 EINs, 65 rows, $1,768,000.** Cross-checking each by normalized organization
name against every disclosure `legal_name` resolves only **2** as key errors:

```
  MATCH-BY-NAME  scEIN=126186140  discEIN=136186140  'Bible Church of Christ, Inc., The'
                 sc awards:22 $10,000 member='Stevens'
                 disc row947  $10,000 Cleared src='Anti-Poverty' member='Stevens'
  MATCH-BY-NAME  scEIN=112631746  discEIN=111631746  'Brookdale Hospital Medical Center, The'
                 sc awards:849 $15,000 member='Osse'
                 disc row1394 $15,000 Cleared src='Community Safety and Victim Services' member='Osse'

  org name found in disclosure under a different EIN: 2
  org name NOT found in disclosure at all:           39
```

Both are single-digit transcription errors in the **Schedule C** EIN (`12`→`13`, `112`→`111`)
with the amount, member, and org name all matching. Those are extraction defects, not
disclosure omissions.

A fuzzy pass (Jaccard ≥ 0.5 on tokenized names) plus targeted substring searches resolved
one more as a legal-name change and one as a fiscal-conduit representational difference:

```
  'City Island Rocks, LLC'      sc b_local:556  EIN=920731021 $5,000 member='Velazquez'
  'City Island Rocks, Limited'  disc row2347    EIN=932974940 $5,000 member='Marmorato'
```
Same $5,000, same organization under a renamed entity with a new EIN — **and the member
substitution again** (Velazquez → Marmorato, district 13).

```
  'Players Philanthropy Fund DBA Welcome to Chinatown'  sc b_local:1978 EIN=276601178 $22,000 Marte
  'Welcome to Chinatown, Inc.'                          disc row10426  EIN=881524156 $22,000 Marte
```
Schedule C names the **fiscal sponsor**; the disclosure names the **grantee project**. Same
designation, same member, same $22,000, two different legal entities and EINs. The
disclosure workbook does have `Fiscal Conduit` / `FC EIN` columns in the header map, but they
are not what carries this — the conduit is simply absent from the disclosure's view.

Categorizing all 40 exhaustively, so the residue is stated rather than implied:

```
ein_typo                     EINs   2  rows   3  $    75,000
renamed_entity               EINs   1  rows   1  $     5,000
fiscal_sponsor_vs_grantee    EINs   1  rows   1  $    22,000
org_cell_corrupted           EINs   1  rows   1  $    35,000
name_match_other_ein         EINs   0  rows   0  $         0
no_trace_in_disclosure       EINs  35  rows  59  $ 1,631,000
TOTAL                        EINs  40  rows  65  $ 1,768,000
```

**VERIFIED: 35 of the 40 EINs — 59 rows, $1,631,000 — have no trace in the disclosure under
any name.** Substring searches of all 10,811 disclosure `legal_name` values return zero:

```
$ substring search of all 10,811 disclosure legal_name values
'Wildcat': 0        'Brothers Care': 0     'East Elmhurst': 0    'Seeking Asylum': 0
'Specialized Schools': 0  'Bombazo': 0     'Common Justice': 0   'Macaulay': 0
'Road Runners': 0   'Exodus Transitional': 0   'Queensborough': 0  'Cardinal McCloskey': 0
'Elmhurst United': 0  'Kyoung': 0          'Olinville': 0        'Small Property Owners': 0
'Upper Manhattan Mental': 0  'Beyond Boxing': 0  'Wildlife Federation': 0  'Skyriders': 0
'Renaissance Charter': 0  'Rockaway Artists': 0  'Virgilius': 0   'DeSales': 0
'Russian Disabled': 0  'Manhattan Community College': 0  'Community Bridge': 0
```

The largest is **Wildcat Service Corporation, EIN 132725423 — 18 Schedule C rows,
$1,255,000, absent from the disclosure entirely**:

```
    awards:2933    $185,000  member='Gennaro'      bucket='ENVIRONMENTAL INITIATIVES'
    awards:2934     $39,000  member='Ariola'       bucket='ENVIRONMENTAL INITIATIVES'
    awards:2935    $120,000  member='Riley'        bucket='ENVIRONMENTAL INITIATIVES'
    awards:2936    $145,000  member='Sanchez'      bucket='ENVIRONMENTAL INITIATIVES'
    awards:2937     $15,000  member='Stevens'      bucket='ENVIRONMENTAL INITIATIVES'
    awards:2938    $100,000  member='Salamanca'    bucket='ENVIRONMENTAL INITIATIVES'
    awards:2939     $65,000  member='Brooks-Powers' bucket='ENVIRONMENTAL INITIATIVES'
    awards:2940    $130,000  member='Louis'        bucket='ENVIRONMENTAL INITIATIVES'
    awards:2941     $40,000  member='Holden'       bucket='ENVIRONMENTAL INITIATIVES'
    awards:2942     $30,000  member='Farias'       bucket='ENVIRONMENTAL INITIATIVES'
    awards:2943     $60,000  member='Lee'          bucket='ENVIRONMENTAL INITIATIVES'
    awards:2944     $86,000  member='Joseph'       bucket='ENVIRONMENTAL INITIATIVES'
    awards:2945     $40,000  member='Hudson'       bucket='ENVIRONMENTAL INITIATIVES'
    awards:2946    $100,000  member='Kagan'        bucket='ENVIRONMENTAL INITIATIVES'
    awards:4231     $40,000  member='Ariola'       bucket='Support Our Older Adults (…)'
    awards:5200     $50,000  member=''             org='Ariola, Holden Wildcat Service Corporation'
    a_aging:468      $5,000  member='Holden'       bucket='Aging'
    b_local:2554     $5,000  member='Menin'        bucket='Local'
```

**Ambiguity, stated not resolved.** I cannot tell from the files on disk whether Wildcat is
genuinely absent from the disclosure, appears there under an unrecognizable name, or was
removed from the workbook between adoption and the `06-08-26` refresh. Resolving it needs a
source the brief did not permit tonight. It is the single largest unexplained item in the
comparison and should be the first thing checked in any follow-up.

Two of the 65 Schedule C-only rows are **not designations at all** — they are extraction
defects where purpose text or member names bled into the `organization` column:

```
    awards:4885  EIN=311731465 $35,000  member=''
      org='Funds will support the I WILL GRADUATE NYC youth empowerment program to educate and
           inspire youth of NYC educational excellence in STEM. Exodus Transitional Community, Inc.'
    awards:5200  EIN=132725423 $50,000  member=''
      org='Ariola, Holden Wildcat Service Corporation'
```

### The other direction

```
  disclosure-only EINs: 62
    covering 78 rows, $3,587,618
    status: Counter({'cleared': 75, 'pending': 3})
    top Sources: [('Food Pantries', 20), ('SU-CASA', 12), ('Local', 12),
                  ('Developmental, Psychological and Behavioral Health Services', 3),
                  ('Cultural Immigrant Initiative', 3), ('Support Our Older Adults', 3), …]
```

`Food Pantries` and `SU-CASA` dominate, and both are initiatives the awards extraction barely
touched (see §7) — so most of this direction is a symptom of the extraction shortfall rather
than a source difference.

---

## 6. Exact award matching, both directions

```
$ python3 research/phase1-source-comparability/compare_2024.py exact

  key (EIN, amount)
    disclosure rows matched     9028 / 10811  (83.5%)
    schedule C rows matched     9028 / 9279   (97.3%)
    unmatched disclosure        1783
    unmatched schedule C         251

  key (EIN, amount, member)
    disclosure rows matched     7697 / 10811  (71.2%)
    schedule C rows matched     7697 / 9279   (83.0%)
    unmatched disclosure        3114
    unmatched schedule C        1582

  restricted to the Local/Youth/Aging streams only:
    (EIN, amount)                    disc unmatched   198/3979   sc unmatched   130/3911
    (EIN, amount, member)            disc unmatched   506/3979   sc unmatched   438/3911
    (stream, EIN, amount, member)    disc unmatched   516/3979   sc unmatched   448/3911
```

**VERIFIED.** Reading these:

- **97.3% of Schedule C rows have an exact `(EIN, amount)` partner in the disclosure.** That
  is the practical measure of "same universe."
- Adding `member` drops matching by 12.3 points (9,028 → 7,697). That drop is almost entirely
  the time-base problem from §3, not real disagreement — the member field is the single
  worst-behaved key in the comparison.
- Within the appendix streams, adding `stream` to the key costs only 10 more unmatched rows
  (506 → 516), so stream assignment is essentially consistent across sources.
- The 1,783 unmatched disclosure rows carry **$87,665,981**, of which 233 rows with a blank
  Council Member carry **$61,743,917**. Those are initiative-level awards, and they are the
  §1 extraction shortfall seen from the other side.

Top unmatched disclosure rows by Source:

```
        2 rows  $16,411,869  'Peter F. Vallone Academic Scholarship'
        1 rows  $ 5,840,400  'Fiscal 2024 Subsidy: New York Public Library'
      458 rows  $ 5,573,712  'Food Pantries'
        1 rows  $ 4,380,300  'Fiscal 2024 Subsidy: Brooklyn Public Library'
        1 rows  $ 4,380,300  'Fiscal 2024 Subsidy: Queens Borough Public Library'
      151 rows  $ 3,825,000  'SU-CASA'
       71 rows  $ 3,591,500  'NYC Cleanup'
      229 rows  $ 2,304,250  'Local'
```

`Peter F. Vallone Academic Scholarship` ($16.4M) and the three library subsidies ($14.6M) are
lump-sum entries the awards extraction never exploded — `initiatives.csv` carries them at
exactly the same figures, confirming the money is in the Schedule C document.

---

## 7. Source vocabulary vs. initiative vocabulary

```
$ python3 research/phase1-source-comparability/compare_2024.py source

disclosure distinct Source      150
schedule C distinct initiative  118  (+ 26 categories)

exact string matches Source <-> initiative: 96
Source values with NO exact initiative match: 54
initiative values with NO exact Source match: 22
```

**VERIFIED: the vocabularies map, but not by string equality.** 96 of 150 Source values have
a byte-identical initiative counterpart. The 54 that do not fall into four kinds:

**(a) Structural — the four streams the disclosure models as `Source` and Schedule C models
as a separate artifact.** These are not vocabulary gaps:

```
     2658 rows     $36,539,000  'Local'                  -> appendix B
      833 rows      $7,650,000  'Youth'                  -> appendix C
      488 rows      $5,610,000  'Aging'                  -> appendix A
      523 rows     $48,277,020  "Speaker's Initiative"   -> category SPEAKER'S INITIATIVE…
```

**(b) Renames the same year publishes both ways.** Schedule C keeps the parenthetical, the
disclosure drops it, or vice versa:

```
  sc 'Support Our Older Adults (formerly Support Our Seniors)'  329 rows
  disc 'Support Our Older Adults'                               416 rows  $7,650,000
  sc 'HIV/AIDS Faith Based'                    29    disc 'HIV/AIDS Faith Based Initiative'   37
  sc 'Alternatives to Incarceration (ATIs)'    17    disc "Alternatives to Incarceration (ATI's)" 24
  sc 'Young Women's Leadership Development'    23    disc "Young Women's Leadership Development" 28
  sc "City's First Readers"                    10    disc "City's First Readers"               18
  sc 'Pride at Work'                           11    disc 'Pride At Work'                       6
  sc 'Domestic Worker and Employer Empowerment' 4    disc 'Domestic Worker and Employer Empowerment Initiative' 4
  sc 'Managed Care Consumer Assistance Program' 12   disc 'MCCAP Initiative'                   13
```

Note `Pride at Work` / `Pride At Work` — the two sources differ only in the capitalization of
`at`. Any join on the initiative name must be case-folded and punctuation-normalized.

**(c) Schedule C initiative values that are PDF fragments, not initiative names.** These are
extraction defects and would poison a naive vocabulary crosswalk:

```
        1 rows  '(formerly Access to Critical Services for Seniors)'
        9 rows  '(formerly Senior Centers for Immigrant Populations)'
       11 rows  'LGBTQ Inclusive Curriculum)'
       26 rows  'Senior Centers, Programs, and Enhancements)'
        2 rows  'Services in Every Borough)'
        1 rows  'Big Brothers Big Sisters of New York City'          <- an org, not an initiative
        6 rows  'Safe Horizon, Inc. 13-294-6970'                     <- an org + EIN
        1 rows  'Ghetto Film School (GFS) Accelerator Program Model' <- a program
        1 rows  'Prisoners' Rights Project'                          <- a program
        1 rows  'Cure Hate'
        1 rows  'for the continuation of the Justice Innovation, Inc. Project Reset program in the Bronx, and'
```

The last is raw purpose text. Five of these are unbalanced-parenthesis fragments produced by
splitting a wrapped `X (formerly Y)` name across lines.

**(d) Genuinely disclosure-only.** Named subsidies and scholarships the disclosure itemizes
and the awards extraction never exploded (`Fiscal 2024 Subsidy: …`, `Peter F. Vallone
Academic Scholarship`).

### Dollars per bucket, where the names do match

```
$ python3 research/phase1-source-comparability/compare_2024.py bucket

buckets whose dollars agree EXACTLY on both sides: 57 of 99
```

**VERIFIED.** For 57 named buckets, including `Local`, `Youth`, and `Aging`, the two sources
agree to the dollar. Largest disagreements, all in the same direction (disclosure higher):

```
bucket                                                     disc n   sc n     disc $       sc $        delta
Domestic Violence and Empowerment (DoVE) Initiative           428     14  12,030,000    816,923  +11,213,077
Afterschool Enrichment Initiative                              46     16   8,235,000    715,300   +7,519,700
Food Pantries                                                 532      3   7,260,712  1,059,000   +6,201,712
Parks Equity Initiative                                       245     17   5,368,500    290,500   +5,078,000
Coalition Theaters of Color                                    68     21   5,715,000  1,510,000   +4,205,000
AAPI Community Support                                         54     14   5,060,000  1,550,000   +3,510,000
Community Housing Preservation Strategies                      66     11   3,651,000    643,310   +3,007,690
Cultural After-School Adventure (CASA)                        866    742  17,340,000 14,860,000   +2,480,000
Autism Awareness                                               38     11   3,261,846    812,054   +2,449,792
```

The row-count ratios (532 vs 3, 428 vs 14, 245 vs 17) are the signature of an initiative
whose award table the PDF extraction largely failed to reach, not of a source disagreement.
Two buckets run the other way and are small: `Financial Empowerment for NYC's Renters`
(-$195,000) and `Neighborhood Development Grant Initiative` (-$111,000).

---

## 8. Where the appendix rows genuinely differ: reallocation, not loss

Beyond the 17 mis-attributed rows, the two sources describe **different line items inside the
same per-member cap**. Comparing amount multisets per member, after the successor
substitution:

```
Local   members whose AMOUNT MULTISET is byte-identical:  24/56
        | rows only in disclosure 109 ($1,197,500)  only in appendix  67 ($1,197,500)
Youth   members whose AMOUNT MULTISET is byte-identical:  42/52
        | rows only in disclosure  27 ($  235,750)  only in appendix  12 ($  235,750)
Aging   members whose AMOUNT MULTISET is byte-identical:  42/53
        | rows only in disclosure  24 ($  187,500)  only in appendix  13 ($  187,500)
```

**VERIFIED, and the equality is the whole point.** In every stream the one-sided rows sum to
**exactly the same dollars in both directions**. Not approximately — exactly. Roughly 3.3% of
Local, 3.1% of Youth, and 3.3% of Aging dollars sit on different line items between the two
sources while every member's total stays pinned to the cap.

A clean 1:1 member (Restler, 70 rows / $400,000 on both sides, identical amount multiset) and
a member that differs (Holden, 31 vs 27 rows, $400,000 on both sides):

```
##### Holden  Local: disclosure 31 rows $400,000  |  appendix B 27 rows $400,000
   amount multiset only-in-disclosure: {3000.0: 3, 600.0: 1, 20000.0: 1, 193000.0: 1, 8900.0: 1}
   amount multiset only-in-appendixB : {16000.0: 1, 207500.0: 1, 8000.0: 1}

   -- EIN 133788986: disc 4 rows / appx 1 rows
        DISC r376    $7,000 'Animal Care and Control of New York City' | prog='Animal Care'
        DISC r377    $3,000 'Animal Care and Control of New York City' | prog='Cat & Dog Food Assistance - Council District 30'
        DISC r379    $3,000 'Animal Care and Control of New York City' | prog='Pet Food Assistance - Council District 30'
        DISC r380    $2,000 'Animal Care and Control of New York City' | prog='Spay/Neuter Event - Council District 30'
        APPX 93      $7,000 'Animal Care and Control of New York City' | prog='Animal Care'
   -- EIN 131624041: disc 0 rows / appx 1 rows
        APPX 1262    $8,000 'Humane Society of New York' | prog=''
   -- EIN 113444285: disc 0 rows / appx 1 rows
        APPX 266     $5,000 'Bobbi and the Strays, Inc.' | prog='Animal Care'
   -- EIN 112106191: disc 1 rows / appx 0 rows
        DISC r8545   $3,000 'Queens Symphony Orchestra, Inc.' | prog='Movie Night Event'
```

**VERIFIED:** the line items differ; the $400,000 does not.
**INFERRED:** that members reallocated within their cap between the June 2023 adopted budget
and the disclosure's 2026 refresh, so the disclosure holds the later state. The alternative —
that the extraction invented `Humane Society of New York` and `Bobbi and the Strays` while
deleting `Queens Symphony Orchestra` in a way that preserved the total to the dollar — is not
credible, but I did not confirm the reallocation against a source document.

A pure key difference on one row of Restler's otherwise-identical set:

```
   DISC r7987  $5,000 'Outstanding Renewal Enterprises, Inc.'  EIN=133320984
   APPX 904    $5,000 'Department of Youth and Community Development' EIN=136400434
```

Same $5,000, same member, same stream; the disclosure names the grantee and Schedule C names
the pass-through agency under the City's own EIN.

**Caution on EIN 136400434.** That is the City of New York's EIN and it appears across NYCHA,
DOE, Sanitation, Police, Parks, Transportation, community boards, and the public libraries.
Any analysis that treats `(EIN, member)` as an award identity will produce nonsense on this
EIN — my first cut at §8 did exactly that before I caught it. Exclude or special-case it.

---

## 9. Canonical case: Bard College, EIN 141713034

```
$ python3 research/phase1-source-comparability/compare_2024.py bard

  DISC xlsx-row 811   $ 10,000 Cleared  src='Community Safety and Victim Services'  member='Powers'
  DISC xlsx-row 812   $350,000 Cleared  src='Discharge Planning'                    member=''
  DISC xlsx-row 813   $  9,500 Cleared  src='Local'                                 member='Abreu'
  DISC xlsx-row 814   $ 10,000 Cleared  src='Local'                                 member='Brooks-Powers'

  SC   awards:841     $ 10,000  member='Powers'         bucket='COMMUNITY SAFETY AND VICTIM SERVICES'
  SC   b_local:189    $  9,500  member='Abreu'          bucket='Local'
  SC   b_local:190    $ 10,000  member='Brooks-Powers'  bucket='Local'
```

**VERIFIED.** For FY2024 the disclosure shows **4 designations, $379,500**; Schedule C shows
**3, $29,500**. The three that exist match exactly on member and amount. The missing one is
the **$350,000 `Discharge Planning` initiative award with a blank member** — an
initiative-level row, exactly the class of row the awards extraction under-covers.

Querying `mcp/data/budget.db` read-only for the full series shows the same initiative row is
present for FY2025, FY2026, and FY2027 but not FY2024:

```
 (2024, 'Powers', 'Bard College', 10000, '')
 (2024, 'Abreu',  'Bard College',  9500, '')
 (2024, 'Brooks-Powers', 'Bard College', 10000, '')
 (2025, '', 'Bard College', 350000, 'Discharge Planning')
 (2026, '', 'Bard College', 700000, '(Formerly Alternatives to Incarceration, Discharge Planning, and Diversion Programs)')
 (2027, '', 'Bard College', 800000, 'Alternatives to Incarceration and Reentry Programs')
```

So the FY2024 omission is year-specific, not a systematic failure to carry Bard's initiative
money — which makes it a tractable bug rather than a design gap.

---

## Answers to the questions asked

**By EIN, both directions.** Disclosure 2,164 distinct EINs; Schedule C 2,142; intersection
2,102. Disclosure-only 62 EINs / 78 rows / $3,587,618. **Schedule C-only 40 EINs / 65 rows /
$1,768,000**, of which 2 are Schedule C digit errors, 1 is a renamed entity, 1 is a
fiscal-sponsor-vs-grantee difference, 1 is a corrupted org cell, and **35 EINs / 59 rows /
$1,631,000 have no trace in the disclosure under any name**. The superset claim is falsified.
On the Cleared-only subset the Schedule C-only count rises to 88 EINs / 126 rows / $2,362,800.

**By Source/initiative.** The vocabularies map but not by string equality: 96 of 150 exact,
plus renames, parenthetical variants, and a case-only difference (`Pride at Work` /
`Pride At Work`). 22 Schedule C "initiative" values are PDF fragments, orgs, or raw purpose
text rather than initiative names. Of 99 buckets matching by name on both sides, **57 agree
to the dollar**.

**By council member.** Both sources publish a **bare surname**. The disclosure adds no first
name and no district and **does not disambiguate** Williams / Sanchez / Rivera / Barron /
Vallone. Within FY2024 there is no surname collision on either side — every surname resolves
to one district. The real hazard is across sources: **`Brannan` means district 43 in
Schedule C and district 47 in the disclosure**, and four surnames present in one source are
absent from the other in matched successor pairs (Kagan/Brannan, Jordan/Salaam, Barron/Banks,
Velazquez/Marmorato).

**By exact award.** `(EIN, amount)`: 9,028 matched — **97.3% of Schedule C rows**, 83.5% of
disclosure rows. `(EIN, amount, member)`: 7,697 — 83.0% / 71.2%. Adding `member` costs 1,331
matches, nearly all of it the time-base problem.

**Dollar totals.** Per year: disclosure $527,971,414 vs Schedule C parsed $450,462,574, but
vs the Schedule C document's own printed totals plus appendices ($521,727,500) the gap is
**$6,243,914 / 1.2%**. Per initiative: 57 of 99 named buckets agree exactly; the three
appendix streams agree exactly.

**Cleared vs Pending.** Reported at every level above. FY2024 is 99.3% Cleared; the 80
Pending rows carry $1,063,733 and 70 of them have an exact `(EIN, amount)` partner in
Schedule C. **The Pending rows are required for the reconciliation to close**: filtering to
Cleared breaks the exact appendix agreement by $269,500 / $53,000 / $45,000 and raises the
Schedule C-only EIN count from 40 to 88. The adopted Schedule C contains designations the
disclosure still marks Pending, so Pending must be included, not excluded.

**Does close agreement here support "same universe"?** Yes, strongly. Three independently
extracted appendix streams landing on the Council's published totals to the dollar, 97.3% of
Schedule C rows finding an exact `(EIN, amount)` partner, 57 buckets agreeing exactly, and
one-sided rows summing to identical dollars in both directions — that is not what two
different universes look like.

---

## Open items, stated as ambiguity rather than resolved

1. **Wildcat Service Corporation (EIN 132725423), 18 rows, $1,255,000, no trace in the
   disclosure.** The largest unexplained item in the comparison. Needs a source not available
   tonight.
2. **`a_aging:35`, $7,000, EIN 113199040** — a row that swallowed a page header and column
   headers. Its buried text names `Barron`, implying `Banks`, but no disclosure row confirms
   the $7,000. Not assigned.
3. **The successor substitution map is derived from this data, not from a roster.** The
   counts and district attributions are internally consistent, but the map itself should be
   confirmed against an authoritative Council roster before being encoded anywhere.
4. **FY2024 is one year.** The appendix streams agreeing to the dollar is powerful evidence
   for FY2024. FY2021–FY2023 and FY2025–FY2027 need the same test before the finding
   generalizes, and FY2016–FY2020 is known-broken extraction where it should be expected to
   fail.

## Concrete follow-ups this run identified but did not do

- **Appendix member-attribution fix.** 17 FY2024 rows, $164,000, one mechanical signature
  (non-roster `member` value + `organization` starting mid-sentence in lowercase + the true
  member appearing as a token inside the org string). Worth running across every year.
- **Initiative-name cleanup.** 22 FY2024 `initiative` values are fragments, orgs, or purpose
  text. Five are unbalanced-parenthesis splits of `X (formerly Y)` names.
- **The $71.26M unexploded award tables.** `Food Pantries` (532 disclosure rows vs 3),
  `DoVE` (428 vs 14), `Parks Equity` (245 vs 17), `SU-CASA` (151 vs 0), the library subsidies,
  and the Vallone scholarship. This is the largest single quality gap in FY2024 Schedule C and
  it is measurable without the disclosure at all.
- **Never join these two sources on surname.** If a crosswalk is built, key it on
  `(EIN, amount)` and treat member as an attribute to be reconciled, not a join key.
