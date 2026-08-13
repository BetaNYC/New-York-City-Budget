# FY2020: Council expense disclosure vs. parsed Schedule C

**Report generated:** 2026-08-12
**Data current as of:** 2026-08-12 (all inputs read from disk; no network calls)
**Branch:** `research/phase1-source-comparability` (worktree `/Users/noneck/Code/NYCB-phase1`)
**Scope:** FY2020 only. Nothing under `data/`, `source/`, `viz/`, `mcp/`, or `code/` was modified.

**Inputs**

| side | file |
|---|---|
| disclosure | `source/expense-funding-disclosure/funded_disclosure_FY2020.xlsx`, read via `code/parse_expense_disclosure.py` |
| Schedule C | `data/fy20/schedule_c/fy20_schedule_c_awards.csv` (2,841 rows) |
| Schedule C | `data/fy20/schedule_c/fy20_appendix_{a_aging,b_local,c_youth}.csv` — **all three are header-only, 0 data rows** |
| Schedule C | `data/fy20/schedule_c/fy20_schedule_c_initiatives.csv` (137 printed initiative rows) |
| ground truth | `source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf` (read, not modified — 4 pages, to settle one claim) |

---

## Verdict

**FY2020 is one universe, badly under-extracted on the Schedule C side. It is not two different universes.**

Three independent lines of evidence, all VERIFIED:

1. **Top-line arithmetic closes to 0.67%.** Disclosure minus its Local/Youth/Aging rows = **$407,417,702**. The Schedule C PDF's own printed grand total, per `fy20_schedule_c_reconciliation.txt`, = **$404,372,774**. Gap **$3,044,928**. Add the appendix buckets back ($49,799,000) and the disclosure total ($457,216,702) sits $3,044,928 above `$404,372,774 + $49,799,000 = $454,171,774` — the *same* gap, so it is one discrepancy, not two.
2. **The vocabularies are the same vocabulary.** 108 of the disclosure's 139 non-appendix `Source` values match a printed Schedule C initiative by name; 90 of those agree **to the dollar**. Of the 31 name-leftovers, 23 pair on an exact dollar amount and are visibly the same initiative with PDF-extraction noise on the Schedule C side (`'1) HPD Community Housing Preservation Strategies'`, `'& DCLA Autism Awareness'`).
3. **The reverse direction barely exists.** Only **10 EINs / 13 rows / $317,620** appear in Schedule C and nowhere in the FY2020 disclosure — 0.12% of extracted Schedule C dollars. Nine of the ten appear in *other* disclosure years, so they are real organizations, not extraction garbage.

**"Disclosure is a superset of Schedule C" survives FY2020**, with the ten exceptions itemized in §3 below. It is not falsified, but it is not clean either — see the two ambiguities left standing at the end.

**The Schedule C side recovers about 56% of the body.** Per council member, body-to-body, recovery ranges from **4% (Koo)** to **68% (Vallone)**. A source universe that differed would not produce a 4%-to-68% spread across members whose disclosure allocations are nearly identical.

Two extraction defects surfaced that are not about disclosure at all and are reported here because this comparison is what exposed them: an **off-by-one category shift** (§6) and a **`Center for …` name-split artifact** (§5).

---

## 1. Row and dollar totals

```
$ python3 research/phase1-source-comparability/compare_disclosure_schedulec.py 2020

disclosure rows               10616       $457,216,702
  cleared                     10549       $456,580,952
  pending                        67           $635,750
  stripped summary rows           0
schedule C body rows           2841       $258,762,385
  member_item                  1512        $53,139,173
  initiative_provider          1329       $205,623,212
schedule C appendix rows          0                 $0
schedule C TOTAL               2841       $258,762,385

row delta   disclosure - scheduleC = +7775
$   delta   disclosure - scheduleC = $198,454,317
```

FY2020 disclosure carries **no** embedded summary rows — the FY2024/FY2026 trap does not apply here.

### Where the 7,775-row gap goes

The Schedule C document splits into a body (citywide initiatives + member designations to them) and three appendices (Aging / Local / Youth). The disclosure's `Source` column names the same split. Bucketing by it:

```
Aging                         517 rows  $     5,610,000
Local                        3021 rows  $    36,546,500
Youth                         902 rows  $     7,642,500
OTHER (body initiatives)     6176 rows  $   407,417,702
appendix buckets combined    4440 rows  $    49,799,000   (Schedule C appendix CSVs hold 0 rows, $0)

   status split inside the appendix buckets: Counter({'cleared': 4388, 'pending': 52})
   status split in the body remainder:       Counter({'cleared': 6161, 'pending': 15})
```

**4,440 of the 7,775 missing rows ($49,799,000) are the empty appendix CSVs** — a known, out-of-scope-tonight gap, now quantified for FY2020. The residual is:

```
   disclosure body-equivalent     6176 rows  $   407,417,702
   schedule C body                2841 rows  $   258,762,385
   residual row gap              +3335
   residual $ gap               $  +148,655,317
```

That $148.7M residual is **not** a universe difference. It is two things: (a) rows the body extractor dropped outright, and (b) aggregation — Schedule C prints one consolidated line per provider-per-initiative where disclosure prints the constituent designations (§7).

---

## 2. By EIN, both directions

```
distinct EIN in disclosure : 2157   (blank EIN rows: 0)
distinct EIN in schedule C : 996    (blank EIN rows: 0)
in BOTH                    : 986
disclosure ONLY            : 1171   $45,339,307 across 2201 rows
schedule C ONLY            : 10     $317,620 across 13 rows
```

Cleared/Pending, by direction:

```
disclosure rows on EINs the Schedule C corpus never mentions:
  Counter({'cleared': 2141, 'pending': 60})   $45,339,307
disclosure rows on EINs that DO appear in Schedule C:
  Counter({'cleared': 8408, 'pending': 7})    $411,877,395
```

**Pending is concentrated in the invisible half.** 60 of the 67 pending rows sit on EINs Schedule C never mentions; only **7 of 67 pending rows** have an EIN anywhere in FY2020 Schedule C. Pending rows are overwhelmingly `Local` (31) and `Youth` (16) — the empty appendices — so anyone reading FY2020 Schedule C is reading an almost entirely Cleared view without being told so.

**986 of Schedule C's 996 EINs (99.0%) are present in the disclosure.**

---

## 3. The falsifying direction: 10 Schedule C EINs absent from disclosure

This is the direction that matters. All ten, in full:

| EIN | rows | $ | organization (as extracted) |
|---|---|---|---|
| 510204121 | 4 | 100,000 | Jamaica Service Program for Older Adults (JSPOA), Inc. |
| 112868878 | 1 | 50,000 | University Hospital |
| 136206256 | 1 | 48,620 | Morningside Retirement and Health Services, Inc. |
| 300037735 | 1 | 39,000 | Flushing Meadows-Corona Park Conservancy |
| 133412540 | 1 | 20,000 | Doe Fund, Inc., The |
| 800361646 | 1 | 20,000 | Van Cortlandt Park Conservancy |
| 112037770 | 1 | 10,000 | Queensborough Community College Auxiliary Enterprise Association, Inc. |
| 113582255 | 1 | 10,000 | Stuyvesant Cove Park Association, Inc. |
| 822659106 | 1 | 10,000 | Friends of Kivlehan Park, Inc. |
| 132561121 | 1 | 10,000 | Turtle Bay Tree Fund, Inc. |

Checked each against every disclosure year FY2014–FY2027:

```
  510204121 JSPOA                      years=[2014, 2015, 2016, 2017, 2018, 2019]
  112868878 University Hospital        years=[2015, 2016, 2017, 2018, 2019, 2021, 2022]   name='Staten Island University Hospital'
  136206256 Morningside Retirement     years=[2014..2018, 2022..2027]
  300037735 Flushing Meadows-Corona    years=[2014, 2015, 2016]
  800361646 Van Cortlandt Pk Consvcy   years=[2015, 2016, 2017, 2018, 2019]
  133412540 Doe Fund                   years=[2014..2017, 2021..2027]
  822659106 Friends of Kivlehan Park   years=[]
  112037770 Queensborough CC Aux       years=[2014, 2015, 2016, 2017, 2018]
  132561121 Turtle Bay Tree Fund       years=[2014..2018, 2024]
  113582255 Stuyvesant Cove Park Assn  years=[2014..2018, 2019]
```

**VERIFIED:** nine of the ten are EINs the Council itself publishes in other years, so the EIN digits in the Schedule C extraction are correct and the FY2020 disclosure genuinely omits them. Notice the shape: seven of the nine last appear in FY2018 or FY2019 and then stop — consistent with organizations whose FY2020 designation was recorded but which fell out of the disclosure workbook, not with OCR noise.

**One is unattested anywhere:** `822659106` Friends of Kivlehan Park, Inc. ($10,000, Matteo, program "Kivlehan Park"). Appears in no disclosure year. Cannot be resolved from files on disk.

**One near-collision, reported as ambiguous, not resolved:**

```
SC : EIN 800361646  Cultural Immigrant Initiative  member=Cohen  $20,000  'Van Cortlandt Park Conservancy'
DIS: EIN 133843182  A Greener NYC                  member=Cohen  $20,000  'Van Cortlandt Park Alliance, Inc.'
```

Same member, same amount, adjacent-sounding organization, different EIN **and** different initiative. Either two real designations or one record crossed during extraction. I did not resolve it and am not going to guess.

---

## 4. Source / initiative vocabulary

```
disclosure Source values      : 142
schedule C initiative values  : 101  (blank on 562 rows)
schedule C category values    : 23
exact-after-normalization overlap: 87
```

That surface comparison understates the agreement, because `fy20_schedule_c_awards.csv`'s `initiative` column is itself damaged — thirteen values have no disclosure counterpart and six of those are **PDF body prose captured as an initiative name**:

```
       6 rows     $2,638,000  'continued reform, and outreach to educate New Yorkers about the criminal justice system.'
       3 rows     $4,300,000  'school leaders.  The allocation to United Federation of Teachers Educational Foundation of'
       2 rows       $650,000  'require legal support to maintain family cohesion and/or obtain public services. Funding of'
      11 rows     $1,800,000  'Amudim Community Resources, Inc. 47-984801'
       6 rows     $1,550,000  'SAFE Foundation, Inc. 26-102131'
```

The last two are an organization name plus a hyphenated EIN promoted into the initiative field.

### The honest comparison: disclosure `Source` vs. the *printed* initiative table

```
disclosure Source (non-appendix) distinct: 139
printed initiative distinct:              135
matched after normalization:              108
  dollar-identical:  90
  dollar-different:  18
matched-set totals: disclosure $323,850,344   printed $323,490,968
```

**90 initiatives agree to the dollar.** The 18 that differ:

```
        1,446,697   disc     $4,434,697 (  12 rows)  printed     $2,988,000   supports for persons involved in sex trade
       -1,332,067   disc     $4,667,933 ( 294 rows)  printed     $6,000,000   public health funding backfill
         -600,000   disc     $4,594,000 (  28 rows)  printed     $5,194,000   city's first readers
          600,000   disc     $9,103,800 (  14 rows)  printed     $8,503,800   educational programs for students
          360,523   disc     $5,765,713 (   8 rows)  printed     $5,405,190   discretionary child care
         -200,000   disc     $1,578,000 (   8 rows)  printed     $1,778,000   college and career readiness
         -181,552   disc     $1,870,048 (   7 rows)  printed     $2,051,600   compass
         -159,500   disc     $4,400,000 (   5 rows)  printed     $4,559,500   support for educators
          155,000   disc     $1,155,000 (  17 rows)  printed     $1,000,000   hate crimes prevention
         -150,000   disc       $444,788 (   3 rows)  printed       $594,788   reproductive and sexual health services
          124,000   disc     $6,903,231 (  12 rows)  printed     $6,779,231   afterschool enrichment
          114,500   disc       $714,500 (   2 rows)  printed       $600,000   work based learning internships
           75,000   disc     $5,400,325 (  40 rows)  printed     $5,325,325   naturally occurring retirement communities
           75,000   disc     $3,113,000 (   9 rows)  printed     $3,038,000   innovative criminal justice
           50,000   disc     $2,925,600 (  30 rows)  printed     $2,875,600   crisis management system
          -41,725   disc     $1,827,275 (   7 rows)  printed     $1,869,000   social and emotional supports for students
           20,000   disc     $2,338,000 (  24 rows)  printed     $2,318,000   mental health services for vulnerable populations
            3,500   disc     $9,808,500 ( 300 rows)  printed     $9,805,000   domestic violence and empowerment (DoVE)
```

Two of these are confirmable against the PDF. Page 75 of the document prints the Health Services initiative table: **Public Health Funding Backfill $6,000,000** and **Reproductive and Sexual Health Services $594,788**, against disclosure's $4,667,933 and $444,788. So on these two the disclosure carries **less** than the adopted Schedule C figure. That is a genuine source-level disagreement, not an extraction artifact, and it means neither document can be treated as strictly dominant.

### The name-leftovers are the same initiatives

Matching the 31 disclosure-only and 27 printed-only names on exact dollar amount pairs 23 of them:

```
      $13,487,000   disclosure 'alternatives to incarceration ati s'          printed 'alternatives to incarceration ati'
       $3,651,000   disclosure 'community housing preservation strategies'    printed '1 hpd community housing preservation strategies'
       $3,246,846   disclosure 'autism awareness'                             printed 'and dcla autism awareness'
       $2,507,500   disclosure 'community boards'                             printed 'community boards community boards enhancement'
       $2,258,750   disclosure 'access to food and nutritional education'     printed 'access to healthy food and nutritional education'
       $1,500,000   disclosure 'lgbtq senior services in every borough'       printed 'lgbt senior services in every borough'
         $600,000   disclosure 'cuny childcare'                               printed 'cuny child care expansion'
         ... 16 more, all exact-dollar
```

The printed side's `1) HPD`, `& DCLA`, `Multiple` prefixes are agency-column text dragged into the initiative name by the PDF extractor. **Caveat, stated because it matters:** this second pass matches on *amount*, so where several initiatives share a value (three at $2,000,000, two at $1,200,000) the specific pairing printed above is arbitrary. The *sets* pair; individual rows in that group should not be quoted.

Four printed / eight disclosure values remain. Three resolve by inspection of the raw initiative rows:

```
{'category': 'Legal Services', 'agencies': 'NYPL', 'initiative': 'Fiscal 2020 Subsidy', 'amount': '5208000'}
{'category': 'Legal Services', 'agencies': 'BPL',  'initiative': 'Fiscal 2020 Subsidy', 'amount': '3906000'}
{'category': 'Legal Services', 'agencies': 'QBPL', 'initiative': 'Fiscal 2020 Subsidy', 'amount': '3906000'}
{'category': 'Legal Services', 'agencies': '',     'initiative': 'Research Fiscal 2020 Subsidy', 'amount': '980000'}
```

5,208,000 + 3,906,000 + 3,906,000 = **13,020,000**, exactly the disclosure's three library `Source` values (`New York Public Library`, `Brooklyn Public Library`, `Queens Borough Public Library`); and `Research Fiscal 2020 Subsidy` = the disclosure's `Research Library` $980,000. Same money, different label. (Their `category: Legal Services` is wrong — see §6.)

**Genuinely unexplained after all that (4 items, disclosure side):**

| disclosure Source | $ | note |
|---|---|---|
| `Speaker's Initiative` | 14,362,052 | nearest printed row is `Multiple Speaker's Initiative to Address Citywide Needs` $12,816,500, Δ $1,545,552 |
| `Senior Centers, Programs, and Enhancements` | 3,376,670 | printed 3,383,670, Δ $7,000 |
| `Sports Training and Rolemodels for Success (STARS)` | 1,472,000 | printed 1,450,000, Δ $22,000 |
| `Bridge Program for Workforce Development` 1,000,000 · `Cure Hate Initiative` 125,000 | | no printed counterpart at any amount |

---

## 5. Council member

```
disclosure distinct : 58  (blank on 2191 rows)
schedule C distinct : 51  (blank on 1329 rows)
```

**Twelve member labels exist in disclosure and nowhere in Schedule C** — 1,522 rows, $35,387,000:

```
      117 rows     $1,276,000  'Bronx Delegation'
      196 rows     $2,411,000  'Brooklyn Delegation'
      107 rows     $2,153,000  'D. Diaz'
      210 rows     $2,060,000  'Levine'
      160 rows     $2,098,000  'Louis'
      107 rows     $2,025,000  'Maisel'
       92 rows     $1,200,000  'Manhattan Delegation'
       84 rows     $1,490,000  'Queens Delegation'
      133 rows     $2,075,000  'Reynoso'
      190 rows    $16,139,000  'Speaker'
       25 rows       $282,000  'Staten Island Delegation'
      101 rows     $2,178,000  'Torres'
```

Six sitting members — **Levine, Louis, Maisel, Reynoso, Torres, and the second Diaz** — plus the Speaker's own designations and every borough delegation are **entirely absent from the FY2020 Schedule C member column**. That is not a vocabulary difference; those are 1,522 designations with a named sponsor that the extraction lost or left blank.

**Five "members" exist in Schedule C and not in disclosure. All five are artifacts:**

```
       17 rows     $7,649,425  'Brooklyn'
       15 rows     $7,318,710  'Center'
        2 rows       $273,000  'Manhattan'
       12 rows     $1,319,608  'Queens'
       10 rows     $1,189,730  'Staten Island'
```

`Brooklyn` / `Manhattan` / `Queens` / `Staten Island` are the borough delegations with `Delegation` shorn off. **`Center` is a name-splitting bug**: every organization whose legal name starts `Center for …` had the word `Center` written into the `member` column and the remainder left as the organization:

```
{'category': 'Criminal Justice Services', 'initiative': 'Alternatives to Incarceration (ATIs)', 'award_type': 'member_item',
 'member': 'Center', 'organization': 'for Alternative Sentencing and Employment Services', 'ein': '132668080', 'amount': '1028775'}
{'category': 'Housing', 'initiative': 'Foreclosure Prevention Programs', 'award_type': 'member_item',
 'member': 'Center', 'organization': 'for New York City Neighborhoods, Inc.', 'ein': '830506416', 'amount': '2000000'}
{'category': 'Cultural Organizations', 'initiative': 'Domestic Violence and Empowerment (DoVE) Initiative', 'award_type': 'member_item',
 'member': 'Center', 'organization': 'for Anti-Violence Education (CAE), Inc., The.', 'ein': '112444676', 'amount': '45000'}
```

**15 rows, $7,318,710**, each with a fabricated council member, a truncated organization name, and `award_type: member_item` on what are initiative-provider rows. The EINs are intact, which is why the disclosure comparison catches them.

### Does the disclosure disambiguate Williams / Sanchez / Rivera / Barron / Vallone? (issue #51)

**Partly, and only when the Council had to.** The disclosure's `Council Member` column is **surname-only**, the same convention Schedule C uses. It adds an initial **only where two members share a surname in that year**:

```
2019  collision surnames -> ['Barron', 'Diaz', 'Rivera', 'Vallone', 'Williams']
2020  collision surnames -> ['Barron', 'D. Diaz', 'Diaz', 'Rivera', 'Vallone']
2021  collision surnames -> ['Barron', 'D. Diaz', 'Diaz', 'Rivera', 'Vallone']
2024  collision surnames -> ['Rivera', 'Sanchez', 'Williams']
2027  collision surnames -> ['J. Sanchez', 'P. Sanchez', 'Williams']
```

In FY2020 the only collision is Diaz, and the disclosure resolves it (`Diaz` vs `D. Diaz`, 148 and 107 rows) while Schedule C has a single undifferentiated `Diaz` (38 rows). FY2027 does the same for Sanchez.

**What this means for #51:** the disclosure carries **no first name, no district number, and no member ID** — it will not resolve a surname on its own. What it does give is a **per-year authoritative roster of 58 labels with the Council's own disambiguation applied**, which is a usable crosswalk key and a per-year test for whether a surname is ambiguous at all. Treat it as the disambiguation *signal*, not the disambiguation *data*. Full names must come from elsewhere.

### Member-level dollars, body to body

Disclosure minus Local/Youth/Aging (so both sides describe the same document section):

```
  member            d.rows   disclosure $ sc.rows    scheduleC $  sc/disc
  Adams                 77      1,390,000      37        866,000      62%
  Chin                  78      1,365,000      22        424,000      31%
  Koo                   59      1,375,000       3         60,000       4%
  Levin                 81      1,390,000      46        886,000      64%
  Miller                61      1,390,000      23        471,000      34%
  Treyger               53      1,375,000      15        300,000      22%
  Vallone               53      1,300,000      31        886,000      68%
  Van Bramer            65      1,365,000      19        516,000      38%
  Yeger                 51      1,400,000       1         70,000       5%
  ...
  TOTAL               3082     62,852,000    1456     35,388,700      56%

  worst 6 recovery: Koo 4%, Yeger 5%, Treyger 22%, Chin 31%, Miller 34%, Van Bramer 38%
  best  6 recovery: Grodenchik 66%, Holden 66%, Borelli 66%, Kallos 66%, Powers 66%, Vallone 68%
```

The disclosure column is flat — every member between $1.30M and $1.52M, which is what a per-district discretionary allocation looks like. The Schedule C column is erratic over the same 45 members. **Koo at 4% and Yeger at 5% are dropped page runs, not policy.** This is the single clearest picture of the FY2020 extraction failure.

---

## 6. VERIFIED extraction defect: the category column is shifted by one

This did not come from the disclosure, but the initiative comparison is what surfaced it, and it changes how every FY2020 category figure should be read.

`fy20_schedule_c_initiatives.csv` opens:

```
category,agencies,initiative,amount
Introduction,,Multiple Anti-Poverty Initiative,2800000
Anti-Poverty,,Multiple Boroughwide Needs Initiative,2000000
Boroughwide Needs,DYCD/NYPL/BPL/QBPL,City's First Readers,5194000
```

The file has **27 category blocks**, and the first initiative under each is the first initiative of the *next* category:

```
   'Introduction'          -> 'Multiple Anti-Poverty Initiative'
   'Anti-Poverty'          -> 'Multiple Boroughwide Needs Initiative'
   'Criminal Justice…'     -> 'Coalition Theaters of Color'
   'Cultural Organizations'-> 'Domestic Violence and Empowerment (DoVE) Initiative'
   'Government Officials'  -> 'Access Health'
   'Legal Services'        -> 'Research Fiscal 2020 Subsidy'
   'Senior Services'       -> 'Chamber on the Go and Small Business Assistance'
   'Small Business…'       -> 'Multiple Speaker's Initiative to Address Citywide Needs'
   ... all 27, no exceptions
```

**Cause, from the PDF's table of contents (page 3 of the file):** 28 entries, the first of which is **`Introduction … 1`** — a narrative section, not a spending category — and the last of which is `Youth Services … 151`. The extractor consumed the 28-entry ToC as its category list and zipped it against 27 summary blocks starting at index 0. `fy20_schedule_c_reconciliation.txt` records the symptom without the diagnosis:

```
categories from ToC: 28 | summary blocks found: 27  <-- MISMATCH
Youth Services                                                    0              0  DIFF +0
GRAND TOTAL                                             404,372,774    404,372,774  27/28 categories exact
```

**"27/28 categories exact" is self-consistent and wrong.** It compares a shifted label to a shifted total, so it agrees with itself. Confirmed against the source:

- PDF document page 74, header **Government Officials** — one initiative, `Community Boards Enhancement $2,507,500`.
- PDF document page 75, header **Health Services** — Access Health, Beating Hearts, Cancer Services, Child Health and Wellness, Ending the Epidemic, HIV/AIDS Faith Based, Maternal and Child Health Services, Public Health Funding Backfill, Reproductive and Sexual Health Services, Viral Hepatitis Prevention, **TOTAL $24,172,764**.

The reconciliation file reports `Government Officials 24,172,764 … OK` and `Food Initiatives 2,507,500 … OK`. Both labels are one behind.

### The awards CSV is mostly right, and wrong on 199 rows

`awards.category` sits exactly one position *ahead* of `initiatives.category`:

```
awards.category index MINUS initiatives.category index, over award rows:
   delta +0 : 199 rows
   delta +1 : 1887 rows
```

Since `initiatives.category` is uniformly one behind truth, the 1,887 rows are **correct** and the 199 rows are **one behind truth**:

```
award rows classifiable against initiatives.csv: 2086  (unclassifiable 755, $88,851,805)
  awards.category == initiatives.category (BOTH one behind truth): 199 rows  $18,494,663
  awards.category == initiatives.category + 1 (awards correct):    1887 rows  $151,415,917

     67 rows  $7,161,200  labeled 'Government Officials'  should be 'Health Services'          init='Ending the Epidemic'
     36 rows  $2,500,000  labeled 'Government Officials'  should be 'Health Services'          init='Access Health'
     40 rows  $1,923,658  labeled 'Government Officials'  should be 'Health Services'          init='Viral Hepatitis Prevention'
     13 rows  $1,631,117  labeled 'Government Officials'  should be 'Health Services'          init='Maternal and Child Health Services'
      6 rows  $1,350,000  labeled 'Higher Education…'     should be 'Homeless Services'        init='Children and Families in NYC Homeless System'
      3 rows    $718,000  labeled 'Veteran Services'      should be 'Young Women's Initiative' init='Dedicated Contraceptive Fund'
      3 rows    $646,000  labeled 'Government Officials'  should be 'Health Services'          init='Child Health and Wellness'
     13 rows    $620,000  labeled 'Cultural Organizations'should be 'Domestic Violence Svcs'   init='Domestic Violence and Empowerment (DoVE) Initiative'
      8 rows    $599,500  labeled 'Government Officials'  should be 'Health Services'          init='Cancer Services'
      6 rows    $350,400  labeled 'Criminal Justice Svcs' should be 'Cultural Organizations'   init='Coalition Theaters of Color'
      1 rows    $350,000  labeled 'Government Officials'  should be 'Health Services'          init='Beating Hearts'
      2 rows    $344,788  labeled 'Government Officials'  should be 'Health Services'          init='Reproductive and Sexual Health Services'
      1 rows    $300,000  labeled 'Speaker's Initiative'  should be 'Veteran Services'         init='Homeless Prevention Services for Veterans'
```

Directly verified against the PDF: DoVE is under **Domestic Violence Services** (document page 56); Ghetto Film School and SU-CASA are under **Cultural Organizations** (document page 55); the ten Health Services initiatives are on document page 75.

**Actionable:** `fy20_schedule_c_initiatives.csv`'s `category` is wrong on **every** row. `fy20_schedule_c_awards.csv`'s `category` is wrong on **199 rows / $18,494,663**, all of them collapsing Health Services into Government Officials or a neighbor. `fy20_schedule_c_reconciliation.txt`'s per-category table should not be cited. 755 award rows could not be classified either way (blank or damaged `initiative`).

**Not verified:** whether the same shift affects other fiscal years. Only FY2020 was examined.

---

## 7. Exact award match

```
  (EIN, amount)
    distinct keys  disclosure   6890   schedule C   2018   shared   1862
    rows matched (multiplicity-aware)        2662
    disclosure rows unmatched                7954
    schedule C rows unmatched                 179
    disclosure status on matched keys      {'cleared': 3552, 'pending': 1}
    disclosure status on unmatched keys    {'cleared': 6997, 'pending': 66}

  (EIN, amount, member)
    distinct keys  disclosure   9149   schedule C   2522   shared   2084
    rows matched (multiplicity-aware)        2328
    disclosure rows unmatched                8288
    schedule C rows unmatched                 513
```

**2,662 of 2,841 Schedule C rows (93.7%) have an exact (EIN, amount) twin in the disclosure.** Adding `member` *lowers* the match to 2,328 and raises Schedule C unmatched from 179 to 513 — the 334-row difference is the §5 member damage (`Center`, bare borough names, blanked sponsors), not a data disagreement. **Match on (EIN, amount); do not add member as a join key for FY2020.**

Only **1 of 3,553** matched-key disclosure rows is Pending, against 66 of 7,063 unmatched. Consistent with §2: Pending lives where Schedule C cannot see.

### Per-EIN dollar agreement

```
EINs where the two sources agree to the dollar : 135
EINs where they do not                         : 851

  largest per-EIN gaps (disclosure - scheduleC):
    136400434     $32,175,806   disc $45,280,715 (832 rows)  sc $13,104,909 (129 rows)  'Borough President-Brooklyn'
    133893536     $20,917,134   disc $22,973,604 (65 rows)   sc  $2,056,470 (10 rows)   'City University of New York'
    133931074      $5,533,333   disc  $5,858,333 (2 rows)    sc    $325,000 (1 rows)    'Bronx Defenders, The'
    132612524      $2,096,105   disc  $5,160,040 (84 rows)   sc  $3,063,935 (19 rows)   'Fund for the City of New York, Inc.'
    133179546      $2,051,853   disc  $3,676,853 (244 rows)  sc  $1,625,000 (2 rows)    'Food Bank For New York City'
```

`136400434` is the City of New York's own EIN, shared by DOE, DOHMH, CUNY, all 59 community boards, and every borough president — 832 disclosure rows under 40+ legal names. **EIN is not a usable entity key for city agencies.** It works for nonprofits and fails for government recipients.

---

## 8. Twelve mismatches read individually

The 179 Schedule C rows with no `(EIN, amount)` twin, largest first, with the disclosure rows for the same EIN alongside.

**1 — UFT Educational Foundation, $3,500,000, EIN 139226721.** Aggregation + a garbled initiative name.
```
SC : {'category': 'Education', 'initiative': 'school leaders.  The allocation to United Federation of Teachers Educational Foundation of',
      'award_type': 'initiative_provider', 'member': '', 'organization': 'United Federation of Teachers Educational Foundation, Inc.',
      'ein': '139226721', 'amount': '3500000'}
DIS: 6 rows, $5,468,800 total —
     row 9837 Cleared    $82,500 src='Educational Programs for Students'
     row 9838 Cleared   $100,000 src='Educational Programs for Students'
     row 9839 Cleared $1,686,300 src='Educational Programs for Students'
     row 9840 Cleared    $32,000 src='Support for Educators'
     row 9841 Cleared   $100,000 src='Support for Educators'
     row 9842 Cleared $3,468,000 src='Support for Educators'
```
**Why:** the Schedule C `initiative` is body prose from the PDF, and $3,500,000 is a consolidated figure. Disclosure's Support for Educators rows sum to $3,600,000 — near, not equal. Grouping rule not recoverable from the CSV.

**2 — UFT Educational Foundation, $1,768,800, Community Schools.** Same EIN, same file.
```
SC : {'category': 'Education', 'initiative': 'Community Schools', 'award_type': 'initiative_provider',
      'organization': 'United Federation of Teachers Educational Foundation, Inc.', 'ein': '139226721', 'amount': '1768800'}
```
**Why:** the disclosure has **no `Community Schools` row for this EIN at all** — its two nearest sums are Educational Programs for Students $1,868,800 and Support for Educators $3,600,000. Either the initiative attribution differs between documents or one figure is an extraction error. Unresolved.

**3 — Department of Education, $1,125,000, Physical Education and Fitness, EIN 136400434.**
```
SC : {'category': 'Small Business…', 'initiative': 'Physical Education and Fitness', 'organization': 'Department of Education',
      'ein': '136400434', 'amount': '1125000'}
DIS: 832 rows for this EIN, $45,280,715 total, spanning Borough President-Brooklyn, Bronx Community Board #1…#12, DOE, CUNY, DOHMH
```
**Why:** the shared city EIN. No per-EIN comparison is meaningful here; only `(EIN, amount, legal_name)` would be, and the legal names differ between documents.

**4 — Safe Horizon, $748,000, Initiative to Combat Sexual Assault, EIN 133540337.**
```
SC : {'initiative': 'Initiative to Combat Sexual Assault', 'organization': 'Safe Horizon, Inc.', 'ein': '133540337', 'amount': '748000'}
DIS: 12 rows, $487,056 total, ALL src='Domestic Violence and Empowerment (DoVE) Initiative', ALL name='Violence Intervention Program'
     (Gjonaj $3,407 / Rivera $15,000 / Gjonaj $20,000 / Gjonaj $21,593 / Salamanca $26,556 / Diaz $27,000 / Gibson $35,000 / Ayala $50,000 …)
```
**Why:** **EIN collision between two different organizations.** Schedule C calls 133540337 "Safe Horizon, Inc."; the disclosure calls it "Violence Intervention Program" in all twelve rows. Separately, Safe Horizon appears in the disclosure under EIN `132946970` ($2,628,423 over 10 rows). One of the two documents has the wrong EIN on Safe Horizon. **Do not join these two records.**

**5 — Food Bank for New York City, $625,000, Food Access and Benefits, EIN 133179546.**
```
SC : {'initiative': 'Food Access and Benefits', 'organization': 'Food Bank for New York City', 'ein': '133179546', 'amount': '625000'}
DIS: 244 rows, $3,676,853 total. Food Access and Benefits alone: $100,000 + $250,000 + $275,000 = $625,000. EXACT.
```
**Why:** pure aggregation, and it reconciles perfectly. Schedule C prints one line per provider-per-initiative; disclosure prints the three constituent designations. **This is the cleanest proof that the two documents describe the same money.** The other 241 rows are that org's Anti-Poverty and Food Pantries designations, which live in the missing appendices.

**6 — United Way of New York City, $550,000, EIN 132617681.**
```
SC : {'category': 'Children's Services', 'initiative': '', 'organization': 'United Way of New York City', 'ein': '132617681', 'amount': '550000'}
DIS: row 9880 Cleared $500,000 src='Census 2020 Outreach'
     row 9881 Cleared $600,000 src='Educational Programs for Students'   (sum $1,100,000)
```
**Why:** Schedule C's `initiative` is **blank** and its category is a §6 shift candidate, so there is nothing to join on. $550,000 matches neither disclosure row and is exactly half the pair's sum — suspicious, unexplained.

**7 — CUNY / College of Staten Island, $500,000, Create New Technology Incubators, EIN 136400434.** Shared city EIN again. Note the disclosure has no `Create New Technology Incubators` Source; it appears only in Schedule C. **Why:** initiative present in one document, absent from the other.

**8 — Urban Justice Center, $463,000, Stabilizing NYC, EIN 133442022.**
```
DIS: 34 rows, $794,569 total, across Access Health / Anti-Poverty ×4 / Chamber on the Go / Community Housing Preservation Strategies / DoVE …
```
**Why:** the disclosure has a `Stabilizing NYC` Source ($3,000,000 over 20 rows) but none of Urban Justice Center's 34 rows carries it. Initiative attribution differs between documents for the same organization.

**9 — CAMBA, Inc., $455,000, Legal Services for the Working Poor, EIN 112480339.**
```
DIS: 14 rows, $620,680 — Anti-Poverty $5,000 ×2, Children and Families in NYC Homeless System $320,333,
     DoVE $25,000, Ending the Epidemic $5,000/$5,000/$135,000, Immigrant Opportunities $20,000 …
```
**Why:** again no `Legal Services for the Working Poor` row for this EIN in the disclosure, though the initiative exists there ($12 rows). Same pattern as #8.

**10 — East New York Restoration LDC, $400,000, EIN 461763706, blank initiative.**
```
SC : {'category': 'Public Safety', 'initiative': '', 'organization': 'East New York Restoration Local Development Corporation',
      'ein': '461763706', 'amount': '400000'}
DIS: 11 rows, $488,750 — A Greener NYC $10,000/$30,000/$40,000 (Barron), Boroughwide Needs $38,750 (Brooklyn Delegation),
     Healthy Aging $40,000 (Barron), Local $5,000/$35,000 (Barron), Neighborhood Development Grant $40,000 (Barron) …
```
**Why:** Schedule C carries a single $400,000 consolidated line with no initiative; disclosure carries eleven itemized designations, all Barron or the Brooklyn Delegation, summing to $488,750. Aggregation plus the missing `Local` appendix.

**11 — Housing Works, $345,094, Ending the Epidemic, EIN 133584089.**
```
SC : {'category': 'Government Officials', 'initiative': 'Ending the Epidemic', 'organization': 'Housing Works, Inc.',
      'ein': '133584089', 'amount': '345094'}
DIS: Ending the Epidemic rows for this EIN: [5000, 83000, 150000, 150000, 195094]  → sum 583,094
     and 150,000 + 195,094 = 345,094  EXACT
```
**Why:** aggregation over a **subset**. Schedule C's line is the sum of exactly two of the five disclosure rows. Also note the Schedule C `category: Government Officials` on an Ending the Epidemic row — one of the 199 shifted rows from §6.

**12 — Shorefront YM-YWHA, $254,595, NORCs, EIN 113070228.**
```
DIS: row 9119 $105,046 Autism Awareness / 9120 $10,000 Healthy Aging (Deutsch) / 9121 $5,000 Local (Deutsch)
     9122 $5,500 Local (Deutsch) / 9123 $229,595 NORCs        (sum $355,141)
```
**Why:** disclosure NORC figure $229,595 vs Schedule C $254,595 — Δ exactly $25,000. Neither document explains the difference. Flagging, not resolving.

**Summary of the twelve:** five are aggregation (two reconcile exactly), two are the shared city EIN, one is an EIN collision between two organizations, three are initiative attribution differing between documents, one is unexplained. **None is a different universe of awards.**

---

## 9. Bard College, EIN 141713034 — the canonical case, in FY2020

```
   disclosure rows: 4
     row 708 Cleared $250,000 src='Discharge Planning' member=''
     row 709 Cleared  $10,000 src='Local' member='Lancman'
     row 710 Cleared   $3,500 src='Local' member='Levine'
     row 711 Cleared   $5,000 src='Local' member='Richards'
   schedule C rows: 0
```

**The FY2023 pattern repeats in FY2020.** Three of the four are `Local` and vanish with the empty Appendix B. The fourth — $250,000 under `Discharge Planning` — belongs in the body and is simply missing from `fy20_schedule_c_awards.csv`. Two different failure modes producing the same user-visible outcome: an EIN lookup returns nothing.

---

## Cleared vs Pending, consolidated

| cut | Cleared | Pending |
|---|---|---|
| all FY2020 disclosure rows | 10,549 · $456,580,952 | 67 · $635,750 |
| in the Local/Youth/Aging buckets (Schedule C appendices, all empty) | 4,388 | 52 |
| in the body remainder | 6,161 | 15 |
| on EINs Schedule C never mentions | 2,141 | 60 |
| on EINs Schedule C does mention | 8,408 | 7 |
| on a matched `(EIN, amount)` key | 3,552 | 1 |
| on an unmatched `(EIN, amount)` key | 6,997 | 66 |

**Pending is 0.14% of disclosure dollars, and 66 of the 67 Pending rows have no exact `(EIN, amount)` match anywhere in FY2020 Schedule C.** Any FY2020 figure derived from the current extraction is effectively Cleared-only, and nothing in the data says so.

---

## VERIFIED vs INFERRED

**VERIFIED — every figure traced to a command in this document**
- All row counts, dollar totals, EIN set arithmetic, member tables, exact-match counts, per-initiative comparisons.
- The 10 Schedule-C-only EINs, and their presence/absence across all 14 disclosure years.
- The category off-by-one in `fy20_schedule_c_initiatives.csv` (all 27 blocks) and in 199 rows of `fy20_schedule_c_awards.csv`, confirmed against PDF document pages 55, 56, 74, 75 and the ToC on page 3.
- The `Center for …` name-split (15 rows).
- Six council members and all borough delegations absent from the Schedule C member column.
- Bard College: 4 disclosure rows, 0 Schedule C rows, FY2020.

**INFERRED — plausible, not confirmed**
- That the $3,044,928 top-line gap is a small number of specific initiative disagreements rather than a systematic definitional difference. The 18 per-initiative deltas in §4 net to roughly this magnitude, but I did not decompose it row by row.
- That the seven Schedule-C-only EINs whose disclosure history stops at FY2018/FY2019 reflect organizations dropping out of the workbook. The pattern is suggestive; the cause is not established.
- That the same category shift affects other fiscal years. Only FY2020 was checked.

**AMBIGUITY LEFT STANDING — not resolved, not papered over**
- `822659106` Friends of Kivlehan Park ($10,000): in Schedule C, in no disclosure year. Unresolvable from disk.
- Van Cortlandt Park **Conservancy** (SC, EIN 800361646) vs **Alliance** (disclosure, EIN 133843182): same member, same $20,000, different EIN and initiative. One record or two — unknown.
- EIN `133540337`: "Safe Horizon, Inc." in Schedule C, "Violence Intervention Program" in all 12 disclosure rows, while Safe Horizon carries `132946970` in the disclosure. One document has it wrong; which is undetermined.
- Public Health Funding Backfill and Reproductive and Sexual Health Services: the PDF prints $6,000,000 and $594,788, the disclosure carries $4,667,933 and $444,788. A real source-level disagreement. **Neither document is strictly authoritative.**
- FY2020 `Speaker's Initiative`: disclosure $14,362,052, nearest printed figure $12,816,500. Unexplained.
- What the `Multiple`, `1) HPD`, `& DCLA` prefixes in `fy20_schedule_c_initiatives.csv` are is clear (agency-column bleed) — but I did not confirm the correct agency attribution for any of them.

---

## Practical guidance for anyone consuming FY2020

1. **Join on `(EIN, amount)`. Do not add `member`** — it costs 334 matches to member-column damage, not to data disagreement.
2. **Never treat EIN `136400434` as an entity.** It is the City of New York: DOE, DOHMH, CUNY, all 59 community boards, all five borough presidents — 832 disclosure rows, $45,280,715.
3. **Do not cite any FY2020 Schedule C `category` value**, and do not cite `fy20_schedule_c_reconciliation.txt`'s per-category table. Initiative names and amounts are sound; category labels are not.
4. **Do not present FY2020 Schedule C figures as complete.** The body recovers ~56% of member designations and the three appendices are empty. An EIN lookup returning nothing means nothing.
5. **Every FY2020 Schedule C figure is Cleared-only** in practice. Say so.

---

## Reproducing this

```bash
cd /Users/noneck/Code/NYCB-phase1
python3 research/phase1-source-comparability/compare_disclosure_schedulec.py 2020
```

Sections 1–7 come from that script. Sections 3 (cross-year EIN check), 5 (`Center`), 6 (category shift), 8, and 9 come from short inline probes reproduced in the code blocks above. PDF pages were read directly from `source/FY20/Fiscal-2020-Schedule-C-Final-Merge.pdf` (read-only).

**Housekeeping note for whoever consolidates this branch:** five other comparison scripts were written into this directory by parallel sessions tonight — `compare_2016.py`, `compare_2019.py`, `compare_2024.py`, `compare_year.py`, `diagnose_2021.py`. `compare_year.py` is the generic form of what `compare_disclosure_schedulec.py` does. **Collapse them into one; do not keep six.** Mine is committed only because every number above traces to it.
