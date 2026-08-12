---
title: "FY2016 source comparability — Council disclosure vs parsed Schedule C"
created: 2026-08-12
type: research-report
status: draft
tags: [nyc-budget, schedule-c, data-quality, source-comparability]
---

# FY2016 — disclosure spreadsheet vs parsed Schedule C

**Report generated:** 2026-08-12
**Data current as of:** 2026-08-12 (all inputs on disk; no network calls)
**Branch:** `research/phase1-source-comparability`

Inputs, all read-only:

| Role | Path |
|---|---|
| Disclosure | `source/expense-funding-disclosure/funded_disclosure_FY2016.xlsx` |
| Parsed awards | `data/fy16/schedule_c/fy16_schedule_c_awards.csv` |
| Parsed initiative totals | `data/fy16/schedule_c/fy16_schedule_c_initiatives.csv` |
| Parsed appendices | `data/fy16/schedule_c/fy16_appendix_{a_aging,b_local,c_youth}.csv` |
| **Primary source (adjudicator)** | `source/FY16/fy2016-skedcf.pdf` |

Reproduce: `python3 research/phase1-source-comparability/compare_2016.py`
Self-check: `python3 research/phase1-source-comparability/compare_2016.py --demo` → `demo: ok`

The FY2016 Schedule C PDF is on disk, so this run did **not** have to treat the disclosure
spreadsheet as ground truth. Where the two disagreed, the PDF was read directly and settled it.
That distinction changed three conclusions this report would otherwise have gotten wrong.

---

## Verdict

**The two sources are the same universe. The FY2016 extraction is broken, and the disclosure
spreadsheet is not a superset.** Both halves of that are load-bearing.

1. **Same universe — strong evidence.** At the initiative-total level the two sources agree to
   **0.48%**, and 113 of 124 identically-named initiatives agree **to the dollar**. A throwaway
   15-line regex over the PDF recovers 3,651 member-item rows of which **87.2% match a disclosure
   row exactly on (EIN, amount)**. These are two renderings of one dataset.
2. **Extraction is broken — root cause found.** The awards extractor drops **every** provider row
   carrying the Schedule C asterisk: **0 of 26 asterisked rows survive vs 161 of 163 unasterisked
   (98.8%)**. Their text is swallowed into the neighbouring row's `organization` string, hiding
   **$11,059,565** in a free-text field. Separately, all three FY2016 appendices are empty while
   the PDF plainly contains ~$45.9M of member items.
3. **"Disclosure is a superset" is FALSE.** One award — Pamela C Torres Day Care Center,
   EIN 131740021, $622,088 — is printed in the FY2016 Schedule C PDF and **absent from the FY2016
   disclosure spreadsheet entirely**. Verified in the primary source, not inferred.

FY2016 is a known-broken extraction year, and it is broken. But it is broken in **specific,
named, mechanical ways**, each with a verified root cause — not diffusely unreliable.

---

## 1. Headline counts

```
$ python3 research/phase1-source-comparability/compare_2016.py --section totals
disclosure   rows_present=7797 awards=7797 blank=0 stripped=0
disclosure   total $381,376,626   by_status {'cleared': 7668, 'pending': 129}
  cleared  n= 7668  $380,361,130
  pending  n=  129  $1,015,496

schedule C   rows=335   total $89,917,012
  fy16_appendix_a_aging.csv          rows=0
  fy16_appendix_b_local.csv          rows=0
  fy16_appendix_c_youth.csv          rows=0
  award_type  {'initiative_provider': 335}
  member non-blank: 0
  agency non-blank: 0
  purpose non-blank: 0

DELTA rows        7,462  (disclosure 7797 - schedule C 335)
DELTA $      $291,459,614  ($381,376,626 - $89,917,012)
schedule C captures 23.6% of disclosure $, 4.3% of rows
```

FY2016 disclosure carries **no** summary rows and **no** blanks — the FY2024/FY2026 trap does not
appear here (`stripped=0`). Every one of the 7,797 rows is a designation.

**Cleared vs Pending, disclosure side, used throughout this report:**

| Status | Rows | Dollars | Share of $ |
|---|---:|---:|---:|
| Cleared | 7,668 | $380,361,130 | 99.73% |
| Pending | 129 | $1,015,496 | 0.27% |

The parsed Schedule C carries **no status field at all**, so no Cleared/Pending split can be
computed on that side. Where this report reports status it is necessarily the disclosure's.
§6 shows why the PDF's asterisk is *not* a usable substitute.

---

## 2. The gap decomposes cleanly into two independent failures

| Bucket | Disclosure rows | Disclosure $ | Extracted | Status |
|---|---:|---:|---:|---|
| Member items (`Local`/`Youth`/`Aging` → appendices A/B/C) | 4,467 | $49,799,000 | **0 rows** | total failure |
| Initiative providers (body) | 3,330 | $331,577,626 | 335 rows / $89,917,012 | partial |
| **All** | **7,797** | **$381,376,626** | **335 / $89,917,012** | |

Member items are **57.3% of rows but only 13.1% of dollars**; initiative providers are the
reverse. Cleared/Pending within the member-item bucket:

```
Local   (appendix B)  3008 rows $   36,539,000   cleared 2988/$36,409,500  pending 20/$129,500
Youth   (appendix C)   919 rows $    7,650,000   cleared  909/$7,592,000   pending 10/$58,000
Aging   (appendix A)   540 rows $    5,610,000   cleared  539/$5,607,000   pending  1/$3,000
```

### 2a. The initiative *totals* file is nearly perfect — the failure is in the *awards* file

This is the single most important structural fact about FY2016, and it is easy to miss because
`fy16_schedule_c_awards.csv` looks catastrophic on its own.

```
initiatives CSV: 193 rows  $333,186,574
disclosure non-Local/Youth/Aging: 3330 rows  $331,577,626
delta $1,608,948  (0.48%)
```

`fy16_schedule_c_initiatives.csv` captures the initiative layer **essentially completely**. Both
sides independently arrive at **exactly 193 distinct initiative names**. Of the 124 that match by
exact string, **113 agree on dollars to the penny**; normalizing dashes and quotes lifts that to
126 of 138.

So the FY2016 corpus knows what the initiatives are and what they are worth. What it lost is the
**provider-level breakdown underneath them** — 335 of ~3,330 rows.

---

## 3. By EIN, both directions

```
$ python3 research/phase1-source-comparability/compare_2016.py --section ein
disclosure distinct EINs :   2274   (rows with no EIN: 0)
schedule C distinct EINs :    233   (rows with no EIN: 0)
in BOTH                  :    225
disclosure ONLY          :   2049
schedule C ONLY          :      8   <-- falsifies 'disclosure is a superset'
  disclosure-only EINs with >=1 Cleared row : 1937
  disclosure-only EINs that are all Pending : 112
```

The 2,049 disclosure-only EINs are the expected direction — they are overwhelmingly the member
items and the dropped asterisk rows. **1,937 of them include at least one Cleared row**, so they
are not explainable as unvetted noise.

### 3a. The eight schedule-C-only EINs, each one adjudicated

This is the direction that matters. **Seven of eight are entity/EIN discrepancies, not absences.**
Each was checked by name against the disclosure.

| # | Schedule C EIN | Org (Schedule C) | Amount | Disclosure counterpart | Verdict |
|---|---|---|---:|---|---|
| 1 | 111839567 | Lutheran Family Health Center's Family Support Center | $95,000 | EIN **202508411**, `Sunset Park Health Council, Inc. d.b.a. NYU Lutheran Family Health Centers`, same initiative, **same $95,000** | parent-entity EIN |
| 2 | 131740021 | Pamela C Torres Day Care Center, Inc. | $622,088 | **NONE — no name match, no amount match** | **genuine absence** |
| 3 | 133092676 | Harlem Hospital Center | $300,000 | EIN **132655001**, same name, same initiative, **same $300,000** | different EIN, same org |
| 4 | 133165187 | Bailey House, Inc. | $125,000 | EIN **133165181** — *last digit differs* — same name, same initiative, **same $125,000** | one-digit discrepancy |
| 5 | 133573842 | Hispanic Federation | $1,000,000 | EIN **133573852** — *one digit differs* — `Hispanic Federation, Inc.`, same initiative, **$983,333** | one-digit discrepancy + $16,667 amount diff |
| 6 | 133780848 | New Yorkers Against Gun Violence | $30,000 | EIN **133808186**, `New Yorkers Against Gun Violence Education Fund`, same initiative, **same $30,000** | affiliated entity |
| 7 | 135564940 | Sheltering Arms Children and Family Services, Inc. | $240,800 | EIN **133709095**, identical name, same initiative, **same $240,800** | different EIN, same org |
| 8 | 471912944 | Fund for New York City Voter Assistance Corporation | $343,840 | EIN **136400434**, `Campaign Finance Board`, same initiative `Student Voter Registration Day`, **same $343,840** | affiliated entity |

Six of the seven carry an **identical dollar amount** on both sides, which is what makes the
identification safe rather than a guess.

**Case 2 is the real one, and it is verified against the primary source.** The FY2016 Schedule C
PDF, page 31:

```
Legal Name of Organization                                        EIN             *        Amount
Pamela C Torres Day Care Center, Inc.                         13-1740021                  $622,088
```

(`source/FY16/fy2016-skedcf.pdf`, line 1858 of `pdftotext -layout` output.)

The extractor got this **right**. The FY2016 disclosure spreadsheet omits the organization
altogether — no name match on `pamela`, `torres`, or `day care center`; no row anywhere in the
workbook for $622,088. Searching every disclosure year FY2014–FY2027 for that EIN returns exactly
one hit:

```
FY2014  $   622,088 EIN=131740021 'Pamela C. Torres Day Care Center, Inc.' src='Discretionary Child Care'
```

Same EIN, same amount, same initiative — in **FY2014**. Two readings fit and this run cannot
separate them: either FY2016 disclosure dropped a real award, or the FY2016 PDF reprinted a stale
FY2014 line. **Recorded as an ambiguity, not resolved.** Either way the superset claim fails,
because the row exists in one source and not the other.

### 3b. EIN is not a unique organization key — 35.5% of disclosure dollars sit under one EIN

```
EIN 136400434: 525 rows, $135,441,355, 136 distinct legal names
    148  'New York City Housing Authority'
     57  'Department of Parks and Recreation'
     52  'Department of Sanitation'
     19  'Department of Transportation'
     13  'Queens Borough Public Library'
     11  'Department of Education'
     11  'Department for the Aging'
```

`136400434` is the City of New York's EIN, used for every city-agency recipient. It alone carries
**$135.4M — 35.5% of all FY2016 disclosure dollars**. Across the workbook, **84 of 2,274 EINs map
to more than one distinct legal name** (CUNY colleges, HHC hospitals, YMCA branches,
Neighborhood Housing Services affiliates).

**Consequence for any downstream join:** EIN is reliable for identifying independent nonprofits and
useless for city agencies and multi-affiliate systems. `get_awards_by_ein` on 136400434 would
return 525 unrelated awards across 136 organizations. Any future reconciliation must join on
(EIN, initiative, amount) — never EIN alone.

---

## 4. Source vocabulary vs initiative vocabulary

```
disclosure distinct Source values    : 197
schedule C distinct initiative values: 80     (awards CSV)
exact-string overlap (casefolded)    : 54
```

The two vocabularies **overlap but are not the same controlled list**, and neither is a superset.

**Present in disclosure, structurally absent from Schedule C's initiative field** — these are the
member-item channels, and they are appendix-bound by design:

| Disclosure `Source` | Rows | Where it belongs in Schedule C |
|---|---:|---|
| `Local` | 3,008 | Appendix B (empty) |
| `Youth` | 919 | Appendix C (empty) |
| `Aging` | 540 | Appendix A (empty) |

Their absence from `initiative` is **correct behavior**, not a vocabulary mismatch. Their absence
from the appendix CSVs is the bug (§5).

**Genuine wording differences** — the PDF and the spreadsheet use different names for the same
initiative. These need a crosswalk; they are not defects:

| Initiatives CSV (from PDF) | Disclosure `Source` |
|---|---|
| `MsExtra` | `MS Extra` |
| `End the Epidemic` | `HIV/AIDS - End the Epidemic` |
| `Mental Hygiene Services – MH Providers` | `MHy Services - Mental Health Providers` |
| `NYC Youth Build` | `NYC YouthBuild Project Initiative` |
| `City’s First Readers` | `City's First Readers (Formerly Known as Early Childhood Literacy)` |
| `Holocaust Survivors Initiative` | `Holocaust Survivors` |
| `Human Trafficking` | `Support for Victims of Human Trafficking` |

Typography differs systematically too: Schedule C uses en-dash `–` and curly `’`, disclosure uses
hyphen `-` and straight `'`, and disclosure pads with multiple spaces
(`'Anti-Gun Violence   - Community-Based Programs'`). Normalizing punctuation lifted the name
overlap from 124 to 138 and the exact-dollar agreement from 113 to 126.

### 4a. Two `initiative` values in the awards CSV are PDF line-wrap fragments

| Fragment in `awards.csv` | Rows | Dollars | True initiative |
|---|---:|---:|---|
| `mediation and youth development)` | 12 | $920,000 | `Anti-Gun Violence - School Based Conflict Mediation` |
| `Services Enhancement` | 11 | $1,684,000 | `Naturally Occurring Retirement Communities (NORC) Supportive Services Enhancement` |

The extractor captured only the **tail of a wrapped heading**. 23 rows and $2,604,000 are filed
under initiative names that do not exist.

### 4b. Category bleed in the initiatives CSV

```
--- initiatives CSV containing 'Mediation':
    [PARKS AND RECREATION] $  1,240,000  'Anti-Gun Violence - School Based Conflict Mediation'
--- initiatives CSV containing 'NORC':
    [PUBLIC SAFETY INITIATIVE] $  1,950,000  'Naturally Occurring Retirement Communities (NORC) Supportive Services Enhancement'
    [PUBLIC SAFETY INITIATIVE] $  1,900,000  'Neighborhood Naturally Occurring Retirement Communities(NNORCs)'
```

An anti-gun-violence initiative filed under `PARKS AND RECREATION`, and two senior-services NORC
initiatives under `PUBLIC SAFETY INITIATIVE`. **INFERRED** (not verified against the PDF's section
structure): the category assignment carries across a PDF section boundary. Consistent with the
`fy16_schedule_c_reconciliation.txt` note `categories from ToC: 26 | summary blocks found: 25 <-- MISMATCH`.

### 4c. Per-initiative dollars where names match exactly

113 of 124 agree to the dollar. The 11 that do not:

| Initiative | Disclosure $ | Schedule C $ | Delta |
|---|---:|---:|---:|
| Jobs to Build On | $5,636,000 | $281,800 | **$5,354,200** |
| COMPASS Slot Restoration | $8,804,200 | $9,783,200 | −$979,000 |
| Worker Cooperative Business Development Initiative | $2,100,000 | $1,095,000 | $1,005,000 |
| Discretionary Child Care | $11,331,878 | $12,082,540 | −$750,662 |
| Senior Centers, Programs, and Enhancements | $3,578,000 | $2,969,000 | $609,000 |
| New York Immigrant Family Unity Project | $5,230,000 | $4,900,000 | $330,000 |
| Initiative to Address Sexual Assault | $600,000 | $300,000 | $300,000 |
| Child Advocacy Centers | $748,000 | $500,000 | $248,000 |
| Legal Services for Domestic Violence Victims | $350,000 | $125,000 | $225,000 |
| Legal Services for the Working Poor | $1,725,000 | $1,525,000 | $200,000 |
| Citywide Civil Legal Services | $3,825,000 | $3,750,000 | $75,000 |

Every positive delta in this table is explained by §6 (dropped asterisk rows). The two negative
deltas are explained by §7 (the sources genuinely disagree).

---

## 5. The appendices: data is in the PDF and reaches nothing

All three FY2016 appendix CSVs are header-only. The PDF's table of contents:

```
APPENDIX A: AGING DISCRETIONARY……….1-25
APPENDIX B: LOCAL INITIATIVES……….26-162
APPENDIX C: YOUTH INITIATIVES……….163-212
```

212 pages of member items. A deliberately crude 15-line regex over the `pdftotext -layout` output
recovers:

```
appendix-style rows detectable in PDF text: 3651
sum $45,876,207
distinct leading tokens (members): 100
```

against **0 rows** in the appendix CSVs. Matched against the disclosure's 4,467 member items:

```
PDF appendix rows recovered : 3651  $  45,876,207
disclosure member items     : 4467  $  49,799,000

(EIN, amount) pairs matched (multiset): 3183 of 3651 PDF rows = 87.2%
(member, EIN, amount) matched         : 3020 of 3651 = 82.7%
```

**87.2% agreement from a throwaway regex.** This is the strongest same-universe evidence in the
report, and it also sets the floor for what a real appendix parser should achieve: a purpose-built
extractor should beat 87%, and the disclosure spreadsheet supplies row-level ground truth to
validate it against.

Note this also means the **council member** field is recoverable for FY2016 member items — the PDF
prints it (`Eugene`, `Ferreras`, `Arroyo`, `Ulrich`, `Torres`, `Lander` …) and 82.7% of
(member, EIN, amount) triples already match the disclosure.

---

## 6. Root cause of the awards-file loss: the asterisk

Matching PDF body provider rows to the awards CSV on (EIN, amount):

```
PDF body provider rows detected : 189   $66,144,060
  with * flag   :   26  $   14,898,635
  without *     :  163  $   51,245,425

PDF rows WITHOUT * present in awards CSV: 161/163 = 98.8%
PDF rows WITH    * present in awards CSV: 0/26 = 0.0%
```

**Zero percent versus 98.8 percent.** The extractor fails on exactly the rows carrying the
asterisk. (The 189 rows are what one regex shape catches, not the full body; the *ratio* is the
finding, not the denominator.)

What the asterisk means, from the PDF's own legend:

> For those organizations identified in Schedule C with an asterisk either MOCS or the Council's
> review process has not yet been completed; the New York State Attorney General's Office has not
> yet provided the Council with final verification of the organization's charitable filing status;
> or the organization is required to attend MOCS corporate governance, fiscal management and
> compliance training.

### 6a. The asterisk is NOT a Pending proxy — and that makes the loss worse

```
PDF body rows matched to a disclosure row by (EIN, amount):
   no-star  -> disclosure cleared   147
   star     -> disclosure cleared    23

  no-star rows matched: 147, of which Pending in disclosure: 0
  star    rows matched: 23, of which Pending in disclosure: 0
```

**All 23 matched asterisked rows are `Cleared` in the disclosure.** The asterisk is an
*adoption-time* review flag that had resolved by the time the disclosure snapshot was taken.

So the dropped rows are **not** provisional or unvetted money that could be dismissed — they are
real, subsequently-cleared awards. Anyone treating the FY2016 corpus as complete is missing
awards that are systematically biased toward organizations that were mid-review at adoption:
smaller and newer nonprofits, and those using fiscal conduits.

### 6b. The failure mode: rows collapse into the `organization` string

The dropped row's text is not discarded — it is concatenated into a neighbouring row's
`organization` field. **21 of 335 awards rows (6.3%)** contain an embedded EIN, hiding
**$11,059,565**.

Verified against the PDF. The awards CSV has:

```
$   125,000  [Legal Services for Domestic Violence V]
    org: Her Justice 13-3688519 * $100,000 Safe Horizon
```

The PDF prints three cleanly aligned rows:

```
Legal Name of Organization                                             EIN          *       Amount
Her Justice                                                       13-3688519        *      $100,000
Safe Horizon                                                      13-2946970               $125,000
Sanctuary for Families                                            13-3193119        *      $125,000
```

`Her Justice` ($100,000, asterisked) was folded into the `organization` field of the `Safe Horizon`
row; `Sanctuary for Families` ($125,000, asterisked) vanished entirely. One unasterisked row
survived out of three.

The worst instances chain several rows together:

```
$   293,850  [Alternatives to Incarceration (ATI) Pr]
    org: Center for Community Alternatives' Crossroads Program 16-1395992 * $408,978
         Center for Employment Opportunities (CEO) 13-3843322 * $440,957
         Educational Assistance Corporation (EAC) 23-7175609 * $1,021,340 Fortune Society

$    94,000  [Worker Cooperative Business Developmen]
    org: Green Worker Cooperatives 20-1828936 * $234,000 ICA Group** 04-2628399 * $234,000
         Working World, The (TWW)** 20-2264584 * $234,000 Make the Road New York

$   281,800  [Jobs to Build On]
    org: Consortium for Worker Education (CWE) 13-3564313 * $5,354,200
         Department of Small Business Services
```

The last one is the $5,354,200 `Jobs to Build On` delta from §4c, sitting verbatim in a text field.
Note `**` (double asterisk) also appears and fails the same way.

---

## 7. Where the two sources genuinely disagree — Discretionary Child Care, fully reconciled

This initiative was worked end-to-end because it is the one case where the extraction is
**perfect** and the sources still disagree. It is the reason this report does not treat the
disclosure as ground truth.

The PDF prints the initiative total and 16 provider rows:

```
    Discretionary Child Care                                                                 $12,082,540
    Legal Name of Organization                                           EIN          *          Amount
    A&G Early Child Care Community Network Inc.                      47-2375867               $2,150,000
    Afro American Parents Education Day Care Center, Inc.            13-2727406                $162,000
    Afro American Parents Education Day Care Center, Inc.            13-2727406                $585,662
    Beth Jacob Day Care Center, Inc.                                 11-2290419                $960,000
    Bethany Day Nursery, Inc.                                        13-2732818                $709,605
    Brooklyn Bureau of Community Services                            11-1630780                $300,000
    Catholic Charities Neighborhood Services Inc.                    11-2047151                  $94,197
    Conselyea St. Block Association, Inc.                            11-2347180               $1,448,669
    Fort Greene Council Inc.                                         11-2300840                $587,058
    Gan Day Care                                                     11-2302049               $1,136,000
    Leake and Watts Services, Inc.                                   13-1860451                $570,377
    Nasry Michelen Day Care Center, Inc.                             20-3108162                $933,098
    Pamela C Torres Day Care Center, Inc.                         13-1740021                  $622,088
    Staten Island Mental Health Society Inc. Head Start
    Program                                                       13-5623279                 $390,000
    West Side Montessori School                                   13-1992185                 $275,000
    Williamsbridge NAACP Early Childhood Education Center         13-2686694                $1,158,786
```

`fy16_schedule_c_awards.csv` reproduces **all 16 rows and the exact $12,082,540 total**, matching
`fy16_schedule_c_initiatives.csv`. No asterisks in this block — consistent with §6.

The disclosure has 18 rows totaling **$11,331,878**. Row by row:

| Organization | Schedule C | Disclosure | Delta |
|---|---:|---:|---:|
| A&G Early Child Care Community Network Inc. | 2,150,000 | 2,150,000 | 0 |
| Conselyea St. Block Association, Inc. | 1,448,669 | 1,448,669 | 0 |
| Williamsbridge NAACP Early Childhood Education | 1,158,786 | 1,158,786 | 0 |
| Gan Day Care | 1,136,000 | 1,136,000 | 0 |
| Beth Jacob Day Care Center, Inc. | 960,000 | 960,000 | 0 |
| **Nasry Michelen Day Care Center, Inc.** | 933,098 | 296,628 | **636,470** |
| Bethany Day Nursery, Inc. | 709,605 | 709,605 | 0 |
| **Pamela C Torres Day Care Center, Inc.** | 622,088 | 0 | **622,088** |
| Fort Greene Council Inc. | 587,058 | 587,058 | 0 |
| **Afro American Parents (2nd row)** | 585,662 | 162,000 | **423,662** |
| Leake and Watts Services, Inc. | 570,377 | 570,377 | 0 |
| **Staten Island Mental Health Society** | 390,000 | 325,000 | **65,000** |
| Brooklyn Bureau of Community Services | 300,000 | 300,000 | 0 |
| West Side Montessori School | 275,000 | 275,000 | 0 |
| Afro American Parents (1st row) | 162,000 | 162,000 | 0 |
| Catholic Charities Neighborhood Services Inc. | 94,197 | 94,197 | 0 |
| **TOTAL** | **12,082,540** | **11,331,878** | **750,662** |

The disclosure's 18 rows include four the PDF does not itemize, all under the City EIN:

```
row  7631  $     65,000  EIN=136400434  Cleared  "Administration for Children's Services"
row  7632  $    157,088  EIN=136400434  Cleared  "Administration for Children's Services"
row  7699  $    636,470  EIN=136400434  Cleared  "Administration for Children's Services"
row  7767  $    300,000  EIN=136400434  Cleared  "Administration for Children's Services"
```

Two reconcile arithmetically against named providers:

```
Nasry Michelen 933,098 == 296,628 + 636,470 ? True
SI Mental Health 390,000 == 325,000 + 65,000 ? True
```

The PDF folds ACS-administered amounts **into the named provider's line**; the disclosure lists
them **separately under the City's EIN**. Different presentation of the same money.

The residual closes exactly:

```
schedC-only:  Pamela 622,088 + Afro dup 585,662 = 1207750
disc-only:    ACS 157,088 + ACS 300,000        =  457088
net                                            =  750662
observed schedC - disclosure                   =  750662
MATCH: True
```

**Every dollar of the $750,662 discrepancy is accounted for.** The extraction introduced none of
it. This is the FY2016 corpus's best-behaved initiative, and it still disagrees with the disclosure
by 6.6% — because the two documents are different renderings with different aggregation rules.

**CAUTION, and the reason the PDF was consulted:** before reading the PDF, the exact arithmetic
above looked like proof that the extractor had merged adjacent rows. It had not. The Council
itself publishes $933,098 and $390,000. An analysis that stopped at the two spreadsheets would
have filed a confident, wrong bug report.

---

## 8. By exact award

```
(EIN, amount)
  disclosure distinct pairs : 5867
  schedule C distinct pairs : 334
  matched pairs             : 287
  schedule C pairs UNMATCHED: 47
  disclosure pairs unmatched: 5580
  schedule C ROWS covered by a matched pair: 288 / 335
```

**86.0% of Schedule C rows (288/335) match a disclosure row exactly on (EIN, amount).** For a
year whose extraction is nominally broken, the rows that *were* extracted are largely faithful.

**(EIN, amount, member) is not computable for FY2016.** The `member` column in
`fy16_schedule_c_awards.csv` is empty in all 335 rows, because all 335 are `initiative_provider`
and member attribution lives in the appendices, which are empty. This is a structural consequence
of §5, not a separate defect.

The 47 unmatched pairs break down as: the 8 EIN cases in §3a, the collapsed-row victims in §6b
(where the surviving row's amount belongs to a different organization), and the aggregation
differences in §7.

---

## 9. By council member — evidence for issue #51

```
schedule C rows with a non-empty member: 0 / 335
disclosure distinct Council Member values: 59
```

**The Schedule C side contributes nothing for FY2016.** The comparison the issue asks for cannot
be run against this year's extracted data at all. What follows is about the *disclosure* side.

### 9a. The disclosure does not disambiguate surnames in FY2016

```
  Williams   1 distinct value(s): ['Williams']
  Sanchez    0 distinct value(s): []
  Rivera     0 distinct value(s): []
  Barron     1 distinct value(s): ['Barron']
  Vallone    1 distinct value(s): ['Vallone']
```

Bare surnames, no first name, no district. FY2016 happens not to *have* a live collision among
these (Sanchez and Rivera were not serving), so the format does not break in FY2016 — but it
carries no information that would prevent breaking.

Checking the format across years:

```
FY2016: 59 distinct member values   Williams -> ['Williams']  Barron -> ['Barron']  Vallone -> ['Vallone']
FY2022: 58 distinct member values   Williams -> ['Williams']  Sanchez -> ['Sanchez']  Rivera -> ['Rivera']  Barron -> ['Barron']
FY2024: 58 distinct member values   Williams -> ['Williams']  Sanchez -> ['Sanchez']  Rivera -> ['Rivera']
FY2026: 59 distinct member values   Williams -> ['Williams']  Sanchez -> ['Sanchez, J', 'Sanchez, P']
```

**FY2026 is the only year in the entire FY2014–FY2027 disclosure series that disambiguates
anything**, and it does so for `Sanchez` only (`Sanchez, J` / `Sanchez, P`). `Williams` stays bare
in FY2026 even though the format demonstrably supports an initial.

**Conclusion for #51: the disclosure spreadsheet cannot resolve colliding surnames and must not be
used as the authority for member attribution.** It is a second source with the same defect, except
in FY2026 for one surname.

### 9b. Other member-field hazards in the disclosure

| Value | Rows | Dollars | Note |
|---|---:|---:|---|
| *(empty)* | 1,142 | $282,171,525 | **74.0% of dollars** — initiative awards carry no member |
| `Speaker` | 296 | $19,695,000 | role, not a person |
| `Brooklyn Delegation` | 196 | $3,109,124 | body, not a person |
| `Manhattan Delegation` | 135 | $3,409,303 | body |
| `Bronx Delegation` | 82 | $2,012,978 | body |
| `Queens Delegation` | 75 | $1,864,101 | body |
| `SI Delegation` | 40 | $405,494 | body |
| `Citywide` | 9 | $2,806,000 | not a member |
| **`CD28`** | 76 | $1,293,794 | **district code where every other row uses a surname** |

`CD28` is a genuine inconsistency inside one workbook column — a district number in a field that is
otherwise surnames, roles, or bodies. Any member-attribution schema needs an explicit
`attribution_kind` (member / delegation / speaker / citywide / district-code / none); a plain
`member` string cannot represent this column without lying.

---

## 10. VERIFIED vs INFERRED

**VERIFIED** — each backed by a command in this document:

- Disclosure FY2016: 7,797 rows, $381,376,626, 7,668 Cleared / 129 Pending, 0 stripped, 0 blank.
- Schedule C awards: 335 rows, $89,917,012, 100% `initiative_provider`, `member`/`agency`/`purpose` entirely empty.
- All three FY2016 appendix CSVs are header-only (0 rows).
- Initiative-total agreement: $333,186,574 vs $331,577,626 → 0.48%. 193 names both sides; 113 of 124 exact-name initiatives agree to the dollar.
- EIN: 2,274 disclosure / 233 Schedule C / 225 shared / 2,049 disclosure-only / 8 Schedule-C-only.
- 7 of the 8 Schedule-C-only EINs resolve to entity or EIN discrepancies, 6 with identical dollar amounts.
- Pamela C Torres (131740021, $622,088) is printed in the FY2016 PDF and absent from FY2016 disclosure; the same EIN and amount appear in FY2014 disclosure.
- EIN 136400434 carries 525 rows, $135,441,355, 136 distinct legal names; 84 of 2,274 EINs map to >1 name.
- Asterisk rows: 0/26 extracted vs 161/163 (98.8%) unasterisked.
- All 23 matched asterisked rows are `Cleared` in the disclosure.
- 21 of 335 awards rows contain an embedded EIN in `organization`, hiding $11,059,565.
- Her Justice / Safe Horizon / Sanctuary for Families are three separate aligned rows in the PDF.
- Discretionary Child Care residual closes exactly: (622,088 + 585,662) − (157,088 + 300,000) = 750,662.
- The PDF prints $12,082,540 for Discretionary Child Care, matching both Schedule C files.
- PDF appendix regex: 3,651 rows / $45,876,207; 87.2% (EIN, amount) and 82.7% (member, EIN, amount) match rate.
- Member-value inventory including the empty 1,142 rows / $282,171,525 and `CD28`.
- FY2026 is the only disclosure year that disambiguates a surname.

**INFERRED** — plausible, not confirmed:

- That the collapsed-row bug is *caused by* the asterisk column rather than merely correlated with it. The correlation is absolute (0% vs 98.8%) and the mechanism is visible in the `organization` strings, but the extractor code was not read this run (out of scope — `code/` is read-only tonight).
- That §4b category bleed comes from a PDF section boundary. Consistent with the reconciliation file's `25 summary blocks found` vs `26 categories from ToC`, but not traced through the PDF.
- That the 87.2% appendix match rate is a *floor* rather than a ceiling. It comes from a deliberately crude regex; a real parser should do better, but that is an expectation, not a measurement.
- That FY2017–FY2020 share this root cause. **Not tested. FY2016 only.**

**AMBIGUITIES LEFT STANDING:**

- **Pamela C Torres.** Cannot determine whether the FY2016 disclosure dropped a real award or the FY2016 PDF reprinted a stale FY2014 line. Both fit every observation available on disk.
- **The second Afro American row ($585,662).** The PDF genuinely prints the organization twice at two amounts. Whether that is two distinct awards or a Council duplication is not determinable from these sources; the disclosure has only the $162,000.
- **Hispanic Federation** differs on *both* EIN (…842 vs …852) and amount ($1,000,000 vs $983,333). Which source is right is not determinable here.
- **Which document is authoritative** when the PDF and the disclosure disagree on aggregation (§7). This is a policy judgment about the corpus, not a data question, and this run did not make it.

---

## 11. What this implies for the corpus

Ordered by dollars recovered per unit of work. **Recommendations, not changes** — nothing in
`data/`, `source/`, or `code/` was modified.

1. **Parse the FY2016 appendices.** Largest single gap: 4,467 rows / $49,799,000 and the only
   route to member attribution for the year. The PDF has the data, and the disclosure gives
   row-level ground truth to validate against — a crude regex already hits 87.2%.
2. **Fix the asterisk handling in the awards extractor.** Recovers ~26 body rows and ~$14.9M
   in FY2016 alone, and un-hides the $11,059,565 currently inside `organization` strings. Highest
   value per line of code, and the bug is systematically biased toward smaller and newer
   organizations, which makes it an equity problem as well as a completeness one.
3. **Add a validation check that no `organization` value contains an EIN pattern.** A three-line
   assertion that would have caught this bug at extraction time, and will catch it in every other
   year.
4. **Do not adopt the disclosure spreadsheet as ground truth.** It is a genuine second source with
   its own omissions (Pamela C Torres), its own aggregation rules (ACS rows), and the same
   member-disambiguation defect as Schedule C. Use it to *validate*, and record disagreements
   rather than silently preferring one.
5. **Never join these sources on EIN alone.** 35.5% of disclosure dollars sit under the City's
   single EIN across 136 organizations. Join on (EIN, initiative, amount).
6. **Build the initiative-name crosswalk** (§4). Both vocabularies are stable and about 193 terms;
   a one-time mapping table makes cross-source reconciliation mechanical for every year.
7. **Check whether the asterisk bug affects FY2017–FY2020.** Untested. If the same extractor path
   produced those years, the same 0%-survival signature should be measurable the same way, and the
   test is cheap.
