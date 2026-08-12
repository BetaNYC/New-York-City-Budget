# FY2017 — Council expense disclosure vs. parsed Schedule C

**Report generated:** 2026-08-12
**Data current as of:** 2026-08-12 (all inputs read from disk; no network calls)
**Branch:** `research/phase1-source-comparability`

**Sources compared**

| Side | File |
|---|---|
| Disclosure | `source/expense-funding-disclosure/funded_disclosure_FY2017.xlsx`, read via `code/parse_expense_disclosure.py` |
| Schedule C | `data/fy17/schedule_c/fy17_schedule_c_awards.csv` + `fy17_appendix_{a_aging,b_local,c_youth}.csv` |
| Ground truth | `source/FY17/FY17-Schedule-C.pdf` (355 pp.), read with `pdftotext -layout` |

Every number below is followed by the command that produced it. Claims are labeled
**VERIFIED** (I ran the check) or **INFERRED** (reasoning beyond what I ran).

---

## Verdict

**FY2017 Schedule C extraction is broken in a single, precisely identified, mechanical way,
and the disclosure workbook is a strict superset of what Schedule C should contain.**

The extractor drops every designation whose PDF line carries an **asterisk**. Not "most",
not "approximately" — **338 of 338** distinct `(EIN, amount)` keys in the extracted awards
CSV correspond to a *non-asterisked* PDF line, and **zero** correspond to an asterisked-only
line. The asterisk is the FY2017 Schedule C's own Cleared/Pending flag, defined on p. 8 of
the PDF.

The five Schedule C EINs that do not appear in disclosure — the direction that would
falsify "disclosure is a superset" — **do not falsify it.** All five are the same
organizations under a different EIN, and three of the five are explained by the two sources
using genuinely different identifiers for the same entity (see §2.2). No Schedule C
designation was found that disclosure lacks.

---

## 1. Row and dollar totals

```
$ python3 research/phase1-source-comparability/compare_year.py 2017
disclosure   rows   8671   $353,501,886.00   file=funded_disclosure_FY2017.xlsx sheet='FY17'
    status cleared    rows   8621   $352,787,056.00
    status pending    rows     50   $714,830.00
schedule C   rows    364   $89,901,487.00
    awards               rows    364   $89,901,487.00
      award_type initiative_provider  rows   364   $89,901,487.00
```

**VERIFIED.** Reproduced independently by my own script; both agree to the dollar.

| | rows | dollars |
|---|---:|---:|
| Disclosure, cleared | 8,621 | $352,787,056 |
| Disclosure, pending | 50 | $714,830 |
| **Disclosure, total** | **8,671** | **$353,501,886** |
| Schedule C `awards.csv` | 364 | $89,901,487 |
| Schedule C appendix A (aging) | **0** | $0 |
| Schedule C appendix B (local) | **0** | $0 |
| Schedule C appendix C (youth) | **0** | $0 |

```
$ wc -l data/fy17/schedule_c/*.csv
       1 data/fy17/schedule_c/fy17_appendix_a_aging.csv
       1 data/fy17/schedule_c/fy17_appendix_b_local.csv
       1 data/fy17/schedule_c/fy17_appendix_c_youth.csv
     365 data/fy17/schedule_c/fy17_schedule_c_awards.csv
```

All three FY2017 appendix CSVs are header-only. **VERIFIED.**

### 1.1 The appendix hole, sized

The three empty appendices correspond exactly to three disclosure `Source` values:

```
disclosure Source Local  :  3127 rows $    36,538,500  (cleared 3107/$36,404,000, pending 20/$134,500)
disclosure Source Youth  :   925 rows $     7,650,000  (cleared  911/$7,565,000,  pending 14/$85,000)
disclosure Source Aging  :   558 rows $     5,610,000  (cleared  554/$5,590,000,  pending  4/$20,000)
  subtotal: 4610 rows $49,798,500
```

**VERIFIED.** 4,610 disclosure rows / $49,798,500 have no Schedule C counterpart *by
construction*, because the files that would hold them are empty. That is 53% of all
disclosure rows for FY2017.

### 1.2 Disclosure is a later snapshot than the PDF

The PDF's printed grand total is $279,908,500 (`fy17_schedule_c_reconciliation.txt`);
disclosure totals $353,501,886. The gap is not error — disclosure includes post-adoption
designations. Proof, from the City's First Readers block:

> ```
> Designation Method:  The City Council has designated the following providers for Fiscal 2017,
>                      and will designate $1 million post-Adoption:
> ```
> — `FY17-Schedule-C.pdf`, p. 12

```
PDF CFR provider lines listed at adoption: 12, sum $1,792,000
listed + post-adoption = $2,792,000
disclosure CFR: 25 rows, $2,792,000  -> MATCHES headline
```

**VERIFIED.** The twelve providers the PDF lists sum to $1,792,000; the PDF's headline for
the initiative is $2,792,000; disclosure carries 25 rows totaling exactly $2,792,000. The
disclosure workbook contains the post-adoption million that the PDF explicitly defers.

**INFERRED:** this generalizes — disclosure is the *later and more complete* of the two
sources for every initiative with a post-adoption tranche. I confirmed it for one
initiative, not all.

---

## 2. By EIN, both directions

```
distinct EIN  disclosure   2219   schedule C    216   in both    211
Schedule C EIN NOT in disclosure : 5   ($1,490,333.00, 5 rows)   <-- falsifies superset if > 0
disclosure EIN NOT in Schedule C : 2008   ($160,750,921.17, 6053 rows)
    of those disclosure-only rows: cleared 6006, pending 47
```

**VERIFIED**, and reproduced by both scripts.

Of the 2,618 disclosure rows sitting on the 211 shared EINs: **2,615 cleared, 3 pending.**

### 2.1 The direction that matters: Schedule C → disclosure

Only **5** Schedule C EINs are absent from disclosure. Each one, read individually:

```
111904261       $175,000.00  'Broadway Housing Communities, Inc. 13-3212867 * $47,000 Brooklyn Public Library (BPL)'
111904262       $175,000.00  'Queens Public Library (QPL)'
133077049        $32,000.00  'Neighborhood Self Help by Older Persons Project, Inc.'
133165187       $125,000.00  'Bailey House, Inc.'
133573842       $983,333.00  'Hispanic Federation, Inc.'
```

Searching disclosure by *organization name* instead of EIN resolves all five:

| Org | Schedule C EIN | Disclosure EIN | Difference |
|---|---|---|---|
| Brooklyn Public Library | `111904261` | `136400434` | different identifier entirely |
| Queens Public Library | `111904262` | `136400434` | different identifier entirely |
| Hispanic Federation, Inc. | `133573842` | `133573852` | 8th digit: **4** vs **5** |
| Bailey House, Inc. | `133165187` | `133165181` | 9th digit: **7** vs **1** |
| Neighborhood Self Help by Older Persons Project, Inc. | `133077049` | `133077047` | 9th digit: **9** vs **7** |

**VERIFIED** — the org-name search returned matching entities in every case:

```
'Brooklyn Public Library': 11 rows, EINs=['136400434'], tot=$396,000
'Queens Public Library': 3 rows, EINs=['136400434'], tot=$315,000
'Hispanic Federation': 5 rows, EINs=['133573852'], tot=$1,641,833
'Bailey House': 7 rows, EINs=['133165181'], tot=$212,230
'Neighborhood Self Help': 13 rows, EINs=['133077047'], tot=$183,500
```

**The superset claim survives.** No Schedule C designation is missing from disclosure.

For the two libraries, the Schedule C EIN is *not* a parser error — the PDF prints it:

> ```
> Brooklyn Public Library (BPL)         11-1904261        $175,000
> Queens Public Library (QPL)           11-1904262        $175,000
> ```
> — `FY17-Schedule-C.pdf`, p. 12

**The two published sources disagree with each other about these EINs.** Schedule C prints
each library's own number; disclosure assigns them the City's.

**INFERRED** for the three single-digit cases: these are transcription errors, and given
that disclosure is a typed workbook while Schedule C is a typeset PDF, the disclosure value
is more likely correct. I did not verify either against IRS records — that needs a network
call, which was out of scope tonight.

### 2.2 EIN `136400434` is a catch-all, not an organization

```
EIN 136400434 (City of New York): 664 disclosure rows, $88,580,677, 186 DISTINCT legal names
```

**VERIFIED.** Disclosure assigns this one EIN to every governmental recipient — city
agencies, community boards, borough presidents, public hospitals, public libraries, public
schools. Sample:

```
r84  'Youth Health Initiative'  $500,000    "Administration for Children's Services"
r546 'Viral Hepatitis Prevention' $120,000  'Bellevue Hospital'
r708 'Boro'                     $20,000     'Borough President of Staten Island'
r846 'Local'                    $6,000      'Bronx Community Board # 4'
r1144 'Anti-Poverty'            $5,000      'Brooklyn Public Library'
```

**Consequence for any downstream join: EIN is not a unique organization key on the
disclosure side.** 7.7% of FY2017 disclosure rows and 25% of its dollars collapse onto a
single EIN spanning 186 distinct legal names. Any EIN-keyed aggregation will silently merge
the Department of Education with a community board.

---

## 3. By Source / initiative

```
disclosure distinct Source (norm): 144
SC distinct initiative (norm):     70
in both: 56 | disclosure-only: 88 | SC-only: 14
```

**VERIFIED.** Normalization = lowercase, curly-apostrophe folded, non-alphanumerics stripped.

### 3.1 The 14 Schedule C initiative labels with no disclosure counterpart

All but three are **wording variants of a disclosure Source**, not real vocabulary gaps:

| Schedule C label | rows | $ | Closest disclosure `Source` |
|---|---:|---:|---|
| `HPD Home Loan Program – Project Help` | 1 | 1,500,000 | `HPD Home Loan Program` |
| `Big Brothers Big Sisters of New York City` | 1 | 1,200,000 | `Big Brothers and Big Sisters of New York City` |
| `Holocaust Survivors` | 10 | 1,115,000 | `Elie Wiesel Holocaust Survivors` |
| **`Services`** | 8 | 1,111,824 | — **truncation artifact** |
| `LGBTQ Youth All-Borough Mental Health Initiative` | 1 | 1,000,000 | `LGBTQ Youth Mental Health` |
| `Coalition of Theaters of Color` | 16 | 970,900 | `Coalition Theaters of Color` |
| `Sports Training and Rolemodels for Success Initiative (STARS)` | 5 | 850,000 | `Sports Training and Rolemodels for Success (STARS) Initiative` |
| `Access Health` | 10 | 701,156 | `Access Health Initiative` |
| **`Small Business Outreach and Assistance Program`** | 5 | 666,250 | — **no close match** |
| `Mental Health Services for Vulnerable Populations` | 6 | 663,295 | `Mental Health Services for Vulnerbale Populations` *(sic — typo is disclosure's)* |
| `Homeless Prevention Fund` | 2 | 656,000 | `Citywide Homeless Prevention Fund` |
| **`Initiative`** | 6 | 617,000 | — **truncation artifact** |
| `LGBTQ Senior Services in Every Borough` | 1 | 300,000 | `LGBT Senior Services in Every Borough` |
| `Ghetto Film School (GFS) Accelerator Program Model` | 1 | 260,000 | `Ghetto Film School Accelerator Program Model` |

**VERIFIED.** `Services` and `Initiative` are bare fragments — the extractor truncated a
longer initiative name. A further **24 Schedule C rows ($557,840) carry a blank
initiative.** `LGBTQ` vs `LGBT` and the `Vulnerbale` typo are genuine editorial differences
between the two published sources.

**The two vocabularies map onto each other.** They are not independent taxonomies — they
are the same list with inconsistent punctuation, article usage, and acronym placement.
Joining on initiative name requires normalization; joining on the raw string will fail on
roughly 20% of labels.

### 3.2 The 88 disclosure Sources with no Schedule C counterpart

7,896 rows, $222,599,925. **VERIFIED.** The largest are the appendix categories (§1.1) plus
whole initiative blocks the extractor lost:

```
   3127  'Local'                                             (appendix B — empty)
    925  'Youth'                                             (appendix C — empty)
    561  'Cultural After-School Adventure (CASA)'            (present in PDF, 0 rows extracted)
    558  'Aging'                                             (appendix A — empty)
    315  'Anti-Poverty'
    272  'Food Pantries'
    222  'Cultural Immigrant Initiative'
    173  'NYC Cleanup'
    168  'Boro'
    167  'Domestic Violence and Empowerment (DoVE) Initiative'
    154  'Parks Equity Initiative'
    120  'Support Our Seniors'
    115  'Healthy Aging Initiative'
    108  'A Greener NYC'
    107  'SU-CASA'
```

---

## 4. By council member — evidence for issue #51

```
distinct values  disclosure 59   schedule C 1
disclosure blank 1282   schedule C blank 364
```

**VERIFIED. The FY2017 Schedule C awards CSV has zero member attribution — all 364 rows
have an empty `member` field.** There is no member comparison to make on the Schedule C
side. Disclosure would *add* 7,389 member-attributed rows ($108,818,988) where Schedule C
currently has none.

This is not because FY2017 Schedule C lacks member data. The PDF contains a
member-attributed table layout that the extractor did not capture at all:

> ```
> Crowley            Queens Theatre in the Park, Inc.    11-3381629   Public School 153            $20,000
> Cumbo              Brooklyn Music School               11-6000202   Public School 020          * $20,000
> Cumbo              Girl Be Heard Institute             27-1848709   Dr. Susan McKinney Sec Sch   $20,000
> Cumbo              Irondale Productions Inc.           13-3178772   K691 - Fort Greene Prep    * $20,000
> ```
> — `FY17-Schedule-C.pdf`, CASA designations

```
CASA-style member-attributed lines in PDF: 345 (sampled)
extract rows whose initiative mentions CASA/After-School Adventure: 0
extract rows with any member value: 0
```

**VERIFIED.** The entire Cultural After-School Adventure block — 561 designations per
disclosure — is absent from the extraction, and with it the only member-attributed layout
in the FY2017 body.

### 4.1 Does disclosure disambiguate Williams / Sanchez / Rivera / Barron / Vallone?

**No — not in FY2017, and only conditionally in any year.** The `Council Member` column is
**bare surname**, with no first name, no district, no member ID.

```
--- FY2017: 59 distinct Council Member values ---
   Williams   {'Williams': 150}
   Barron     {'Barron': 85}
   Vallone    {'Vallone': 117}
--- FY2022: 58 distinct Council Member values ---
   Williams   {'Williams': 134}   Sanchez {'Sanchez': 105}   Rivera {'Rivera': 170}
   Barron     {'Barron': 79}      Gennaro {'Gennaro': 132}   Louis  {'Louis': 192}
--- FY2025: 58 distinct Council Member values ---
   Williams   {'Williams': 171}   Sanchez {'Sanchez': 141}   Rivera {'Rivera': 169}
--- FY2026: 59 distinct Council Member values ---
   Sanchez    {'Sanchez, P': 157, 'Sanchez, J': 91}
```

**VERIFIED.** `Sanchez`, `Rivera`, and `Diaz` return **zero** FY2017 rows.
Disambiguation appears for the first time in **FY2026**, as `'Sanchez, P'` / `'Sanchez, J'`.

**The honest reading for issue #51:** disclosure's member column disambiguates only when the
Council itself has a live surname collision, and only by appending a first initial. It
carries no stable member identifier. It is *not* a general fix for name resolution — it is a
surname string that happens to be unique in most years. For FY2017 specifically, it adds no
disambiguation power, and the question is moot because Schedule C has no member data at all.

**INFERRED:** the FY2017 surnames are unique because only one Williams, one Barron and one
Vallone were seated. I verified the file contains one value each; I did not verify Council
composition against an external roster.

Two further cautions, **VERIFIED**: the column is not always a person. It carries
`'Speaker'` (317 rows), `'Brooklyn Delegation'` (186), `'Manhattan Delegation'` (100),
`'Bronx Delegation'` (89), `'Queens Delegation'` (59), `'Staten Island Delegation'` (36),
`'Citywide'` (13) — and `'CD28'` (77 rows), a district number where a name should be.

---

## 5. By exact award

```
(EIN, amount)          disclosure   8671 rows / 6084 keys   schedule C    364 rows / 338 keys
                       matched multiset 328 rows (90.1% of Schedule C)
  Schedule C rows unmatched :     36   $16,663,105.00
  disclosure rows unmatched :   8343   $280,263,504.00

(EIN, amount, member)  matched multiset 283 rows (77.7% of Schedule C)
  Schedule C rows unmatched :     81
  disclosure rows unmatched :   8388
```

**VERIFIED.** My set-membership variant gave 329 matched / 35 unmatched; `compare_year.py`
uses a stricter multiset match giving 328 / 36. The multiset figure is the correct one and
is quoted here.

**All 380 disclosure rows on a matched key are `Cleared`; zero are `Pending`.** **VERIFIED**
— and it is exactly what §6 predicts.

The `(EIN, amount, member)` result needs a caveat that the percentage hides: **every one of
those 283 matches is against a disclosure row whose `Council Member` is also blank.** Since
Schedule C's member is blank in all 364 rows, the triple key can only match disclosure's
1,282 initiative-level rows. It matched **zero** rows carrying a named member, and that is
structural, not empirical.

---

## 6. Root cause: the extractor drops every asterisked designation

The FY2017 Schedule C PDF defines the asterisk on p. 8:

> "For those organizations identified in Schedule C without an asterisk, the Council has
> completed its review process and, where applicable, MOCS has preliminarily reviewed or
> prequalified the organization…"
>
> "For those organizations identified in Schedule C with an asterisk either MOCS or the
> Council's review process has not yet been completed…"

**The asterisk is FY2017's Cleared/Pending flag.** It is the same semantic field as
disclosure's `Status`, observed at an earlier point in time.

Scanning the PDF body (pages 6–132) for designation lines, handling both the hyphenated
(`13-3212867`) and bare (`133682471`) EIN formats the document uses:

```
PDF body 6-132 designation lines: 1046  $156,422,932
  asterisked (review NOT complete):  479  $62,451,715
  no asterisk (review complete):     567  $93,971,217

extracted awards.csv: 364 rows  $89,901,487
  extracted keys matching a NO-ASTERISK pdf line: 338 / 338 distinct
  extracted keys matching ONLY an asterisked line: 0
  extracted keys in NEITHER: 0
```

**VERIFIED, and this is the finding.** Every distinct `(EIN, amount)` key in the extracted
awards CSV traces to a non-asterisked PDF line. Not one traces to an asterisked line.
**479 designations worth $62,451,715 are dropped from the body alone.**

### 6.1 The mechanism, quoted in full

City's First Readers, as the PDF prints it (p. 12):

```
 Legal Name of Organization                                    EIN          *          Amount
 Broadway Housing Communities, Inc.                        13-3212867       *          $47,000
 Brooklyn Public Library (BPL)                             11-1904261                 $175,000
 Child Center of New York, Inc., The                       11-1733454                  $47,000
 Committee for Hispanic Children and Families, The         11-2622003                  $66,000
 Jumpstart for Children                                    04-3263046       *         $175,000
 Literacy Inc. (LINC)                                      13-3911331       *         $440,000
 New York Public Library (NPL)                             13-1887440                 $175,000
 New York University                                       13-5562308       *         $236,000
 Parent Child Home Program                                 11-2495601                  $34,000
 Queens Public Library (QPL)                               11-1904262                 $175,000
 Reach Out and Read of Greater New York                    13-4080045                 $175,000
 Sunset Park Health Council, Inc.                          20-2508411                  $47,000
```

Twelve providers. What the extractor produced:

```
  L7  ein=111904261 $  175,000 org='Broadway Housing Communities, Inc. 13-3212867 * $47,000 Brooklyn Public Library (BPL)'
  L8  ein=111733454 $   47,000 org='Child Center of New York, Inc., The'
  L9  ein=112622003 $   66,000 org='Committee for Hispanic Children and Families, The'
  L10 ein=131887440 $  175,000 org='Jumpstart for Children 04-3263046 * $175,000 Literacy Inc. (LINC) 13-3911331 * $440,000 New York Public Library (NPL)'
  L11 ein=112495601 $   34,000 org='New York University 13-5562308 * $236,000 Parent Child Home Program'
  L12 ein=111904262 $  175,000 org='Queens Public Library (QPL)'
  L13 ein=134080045 $  175,000 org='Reach Out and Read of Greater New York'
  L14 ein=202508411 $   47,000 org='Sunset Park Health Council, Inc.'
```

Eight rows. The mechanism is exact:

1. **The asterisk acts as a false row terminator.** Each asterisked provider's name, EIN and
   amount are swallowed into the *next* non-asterisked row's `organization` text.
2. **The asterisked provider's EIN and amount are lost entirely** — they survive only as
   unparsed text inside another row's org field.
3. **The surviving row's `ein` and `amount` are correct and belong to the *trailing* org in
   the run-on string**, not the leading one. L7's `organization` begins with "Broadway
   Housing" but its EIN and amount are Brooklyn Public Library's.

Dropped from this one block: Broadway Housing ($47,000), Jumpstart ($175,000), LINC
($440,000), NYU ($236,000) — **$898,000**.

**The data is misaligned, not destroyed.** The trailing-organization rule means these rows
are mechanically recoverable from the existing CSVs without re-parsing the PDF.

### 6.2 Independent confirmation — Access Health

The Access Health block (p. 46) prints EINs *without* hyphens, a second layout variant:

```
  Asian-American Coalition for Children and Families, Inc.     133682471              $75,000
  Bedford Stuyvesant Family Health Center                      112412205              $52,692
  BOOM! Health                                                 133599121             $105,388
  Care for the Homeless                                        133666994              $70,000
  Centro Altagracia de Fe y Justicia                           161765323      *       $52,692
  Community Health Center of Richmond                          510567466      *       $52,692
  Community Healthcare Network                                 133083068      *       $52,692
  Community Service Society of New York                        135562202              $90,000
  Federation of Protestant Welfare Agencies                    135562220              $75,000
  HANAC                                                        112290832              $52,692
  Make the Road New York                                       113344389      *       $52,692
  New York Immigration Coalition                               133573409              $75,000
  Sunset Park Health Council                                   202508411              $52,692
  United Chinese Association of Brooklyn                       371469112              $52,692
  Urban Health Plan                                            237360305      *       $52,692
  Voces Latinas Corporation                                    202312651      *       $52,692
```

16 providers, 6 asterisked, 10 clean. The extractor produced **exactly the 10 clean ones**,
with the same bleed signature:

```
  ein=135562202 $90,000 org='Centro Altagracia de Fe y Justicia 161765323 * $52,692 Community Health Center o'
  ein=133573409 $75,000 org='Make the Road New York 113344389 * $52,692 New York Immigration Coalition'
```

**VERIFIED.** Prediction and observation agree exactly, in a different block with a
different EIN format.

---

## 7. Ten-plus mismatches, read individually

All **36** unmatched Schedule C rows were read. Every one falls into a named class below.

**Class A — organization-text bleed (§6.1). The `ein`/`amount` belong to the trailing org.**

```
ein=111904261 $175,000  init='City's First Readers'  org='Broadway Housing Communities, Inc. 13-3212867 * $47,000 B…'
      -> disclosure has NO row for EIN 111904261
ein=131887440 $175,000  init='City's First Readers'  org='Jumpstart for Children 04-3263046 * $175,000 Literacy Inc…'
      -> disclosure has EIN 131887440: 1 row $30,000
ein=113305406 $2,076,666 init='New York Immigrant Family Unity Project'
                          org='Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defender…'
      -> disclosure has EIN 113305406: 12 rows $2,184,667; amounts [2500,3500,4500,5000,20000,35000,2076667]
```
Why it differs: the extractor merged two or more PDF lines. Note the third case — Schedule C
says **$2,076,666** where disclosure says **$2,076,667**; the PDF shows the *adjacent*
provider at $2,076,667, so this is a bled value off by one dollar, not a rounding
disagreement.

**Class B — City-agency lump vs. per-designation split (EIN `136400434`).** 8 rows.

```
ein=136400434 $6,206,400 init='COMPASS'                         org='Department of Youth and Community Development'
ein=136400434 $1,125,000 init='Physical Education and Fitness'  org='Department of Education'
ein=136400434 $529,000   init='NORCs'                           org='Catholic Charities Neighborhood Services, Inc.'
ein=136400434 $281,800   init='Job Training and Placement'      org='Department of Small Business Services'
      -> disclosure has EIN 136400434: 664 rows $88,580,677; amounts [500,541,557,1000,1100,1200,1500,1800,…]
```
Why it differs: Schedule C prints one line naming the receiving *agency*; disclosure
decomposes the same money into many small per-recipient designations. These can never match
on `(EIN, amount)` — the grain differs. **This is a real semantic difference between the two
sources, not an extraction bug.**

**Class C — genuine EIN disagreement between the two published sources.** 5 rows (§2.1).

```
ein=111904262 $175,000  org='Queens Public Library (QPL)'          -> disclosure uses 136400434
ein=133573842 $983,333  org='Hispanic Federation, Inc.'            -> disclosure uses 133573852
ein=133165187 $125,000  org='Bailey House, Inc.'                   -> disclosure uses 133165181
ein=133077049 $32,000   org='Neighborhood Self Help by Older…'     -> disclosure uses 133077047
```
Why it differs: the two documents print different identifiers for the same entity.

**Class D — amount off by one dollar from a bled neighbor.**

```
ein=112498292 $29,730  init='Community Housing Preservation Strategies'
              org='Good Old Lower East Side, Inc. 13-3311582 * $29,729 Gowan…'
      -> disclosure has EIN 112498292: 1 row, exactly $29,729
ein=112412584 $29,729  init='Community Housing Preservation Strategies'
              org='Central Astoria Local Development Coalition, Inc.'
      -> disclosure has EIN 112412584: 13 rows $259,730; amounts [2000,3000,3500,5000,7000,7500,10000,15000,…]
```
Why it differs: **$29,730 vs $29,729.** The extractor swapped the two adjacent providers'
amounts. **Anyone joining on `(EIN, amount)` will drop both rows and see no error.**

**Class E — truncated initiative labels carrying real money.**

```
ein=135596746 $194,103 init='Services'    org='Long Island Jewish Medical Center 11-2241326 * $106,103 M…'
ein=135623279 $107,103 init='Services'    org='PSCH (Kingsboro Psychiatric Center) 11-2542430 * $132,103…'
ein=202508411 $273,103 init='Services'    org='Sunset Park Health Council'
ein=136400434 $105,000 init='Initiative'  org='Third Sector New England** 04-2261109 * $66,000 Departmen…'
```
Why it differs: the initiative name was truncated to a bare fragment *and* the org text bled.
`Third Sector New England**` carries a double asterisk — the PDF's fiscal-conduit marker
("Federation of Protestant Welfare Agencies (FPWA) will serve as Fiscal Conduit"), a third
marker convention the extractor does not model.

**Class F — page furniture captured as data.**

```
ein=135564937 $78,540 init='Autism Awareness'
              org="Page 71 Heartshare Human Services of New York 11-1633549 …"
```
Why it differs: the string **"Page 71"** — a PDF page footer — was absorbed into the
organization name. The extractor is not stripping page furniture before parsing rows.

---

## 8. Dollar totals per initiative

Disclosure split cleared/pending; Schedule C has no status field (its equivalent, the
asterisk, was dropped rather than recorded). Top 25 by disclosure dollars:

| Initiative (disclosure `Source`) | clr n | cleared $ | pnd n | pending $ | SC n | SC $ |
|---|---:|---:|---:|---:|---:|---:|
| Local | 3107 | 36,404,000 | 20 | 134,500 | 0 | 0 |
| City Council Merit-Based Scholarships | 2 | 15,375,000 | 0 | 0 | 0 | 0 |
| Support for Educators | 2 | 12,744,500 | 0 | 0 | 1 | 12,294,500 |
| Crisis Management System | 73 | 11,340,534 | 0 | 0 | 0 | 0 |
| Cultural After-School Adventure (CASA) | 561 | 11,220,000 | 0 | 0 | 0 | 0 |
| Year-Round Employment (Work, Learn, Grow) | 2 | 11,035,000 | 0 | 0 | 0 | 0 |
| Discretionary Child Care | 12 | 9,859,449 | 0 | 0 | 5 | 3,148,737 |
| Parks Maintenance | 1 | 9,553,205 | 0 | 0 | 0 | 0 |
| Job Training and Placement Initiative | 6 | 8,096,000 | 0 | 0 | 3 | 551,800 |
| NYC Cleanup | 173 | 7,809,952 | 0 | 0 | 0 | 0 |
| COMPASS | 9 | 7,750,000 | 0 | 0 | 4 | 7,116,400 |
| Youth | 911 | 7,565,000 | 14 | 85,000 | 0 | 0 |
| New York Immigrant Family Unity Project | 7 | 6,582,000 | 0 | 0 | 2 | 4,153,332 |
| Domestic Violence and Empowerment (DoVE) | 166 | 6,266,026 | 1 | 38,964 | 0 | 0 |
| Adult Literacy Initiative | 33 | 6,000,000 | 0 | 0 | 0 | 0 |
| Speaker's Initiative | 79 | 5,719,000 | 0 | 0 | 0 | 0 |
| Afterschool Enrichment Initiative | 5 | 5,675,000 | 0 | 0 | 2 | 4,075,000 |
| Anti-Eviction and Housing Court Resources | 14 | 5,650,000 | 0 | 0 | 12 | 4,744,500 |
| Alternatives to Incarceration (ATI's) | 26 | 5,632,000 | 0 | 0 | 6 | 1,456,100 |
| Aging | 554 | 5,590,000 | 4 | 20,000 | 0 | 0 |
| Ending the Epidemic | 54 | 5,595,000 | 0 | 0 | 0 | 0 |
| Cultural Immigrant Initiative | 222 | 5,100,000 | 0 | 0 | 0 | 0 |
| Legal Services for Low-Income New Yorkers | 4 | 5,000,000 | 0 | 0 | 2 | 4,000,000 |
| Food Pantries | 271 | 3,846,290 | 1 | 5,000 | 0 | 0 |
| NORCs | 51 | 3,781,995 | 0 | 0 | 8 | 1,285,000 |

**VERIFIED.** Schedule C is at or below disclosure in every row. It is never above.
**INFERRED:** that one-sidedness is itself corroboration — a random parsing error would
overshoot sometimes. A filter that only ever removes rows undershoots always.

---

## 9. What this establishes, and what it does not

**VERIFIED**

1. FY2017 Schedule C extraction retains exactly the non-asterisked designations and drops
   every asterisked one: 338/338 keys traced, 479 designations / $62,451,715 lost from the
   body.
2. The asterisk is the PDF's own review-status flag, semantically the same field as
   disclosure's `Status`.
3. All three FY2017 appendix CSVs are empty; 4,610 disclosure rows / $49,798,500 have no
   possible counterpart.
4. The entire CASA block (561 disclosure designations) is missing, and with it FY2017's only
   member-attributed table. All 364 extracted rows have a blank `member`.
5. Disclosure is a superset. The 5 apparent counterexamples all resolve to identifier
   disagreements, not missing designations.
6. Disclosure's `Council Member` is a bare surname with no stable identifier, first
   disambiguated in FY2026. It does not resolve issue #51 in general.
7. Disclosure EIN `136400434` covers 664 rows / $88,580,677 / 186 distinct legal names. EIN
   is not a unique org key on the disclosure side.
8. Disclosure is a later snapshot than the PDF and includes post-adoption designations.
9. Organization text bleed is systematic and directional: the surviving row's `ein`/`amount`
   belong to the **trailing** org in the run-on string.

**INFERRED, not verified**

- That the three single-digit EIN differences are typos rather than legitimate changes, and
  that disclosure's value is the correct one. Not checked against IRS records.
- That Class-B agency-lump rows represent the *same* dollars at different grain rather than
  different money. The totals are consistent with it; I did not reconcile any single agency
  lump against its disclosure decomposition line by line.
- That the asterisk-drop behavior is identical in FY2016 and FY2018–FY2020. I only tested
  FY2017.

**Ambiguity left standing**

- `Small Business Outreach and Assistance Program` (5 Schedule C rows, $666,250) has no close
  disclosure `Source`. Whether it is a rename, a merge into another initiative, or a genuine
  Schedule C-only category is unresolved.
- 24 Schedule C rows ($557,840) have a blank initiative. Which block they belong to is not
  determinable from the CSV alone.
- Disclosure's `Council Member` value `'CD28'` (77 rows) is a district number where every
  other row carries a name. Whether it denotes a vacancy, a caretaker, or a data-entry
  artifact is unknown.
- Schedule C and disclosure disagree on the Brooklyn/Queens Public Library EINs, and **both
  are published City documents.** Neither is obviously authoritative.

---

## 10. Reproducing this

```bash
python3 research/phase1-source-comparability/compare_year.py 2017
pdftotext -layout -f 6 -l 132 source/FY17/FY17-Schedule-C.pdf fy17_body.txt
```

The asterisk test — the load-bearing check — is this, against `fy17_body.txt`:

```python
pat = re.compile(r'^\s*(\S.*?)\s{2,}(\d{2}-\d{7}|\d{9})\s+(.*?)\s*(\*?)\s+\$([\d,]+)\s*$', re.M)
# partition PDF lines on the asterisk; intersect each side with the extracted (ein, amount) keys.
# Expected: 100% of extracted keys land in the no-asterisk set, 0% in the asterisk-only set.
```

Both EIN formats must be handled — the PDF uses hyphenated `13-3212867` in most blocks and
bare `133682471` in the Access Health block. A hyphen-only pattern misses 16 designations and
produces false "missing from extract" findings.
