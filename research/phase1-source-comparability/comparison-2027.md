# FY2027: Council expense disclosure workbook vs. parsed Schedule C

**Report generated:** 2026-08-12
**Data current as of:** 2026-08-12 (all inputs read from disk; no network calls)
**Branch:** `research/phase1-source-comparability` (worktree `/Users/noneck/Code/NYCB-phase1`)
**Status:** Read-only comparison. No file under `data/`, `source/`, `viz/`, or `code/` was modified.

**Inputs**

| Role | Path | sha256 (first 16) |
|---|---|---|
| Disclosure workbook | `source/expense-funding-disclosure/funded_disclosure_FY2027.xlsx` | `d15f058a38ea2416` |
| Schedule C PDF (consulted directly to adjudicate 3 findings) | `source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf` | `63c03739d3ac5e4f` |
| Parsed Schedule C | `data/fy27/schedule_c/fy27_schedule_c_awards.csv` + `fy27_appendix_{a_aging,b_local,c_youth}.csv` | — |
| Reader | `code/parse_expense_disclosure.py` (commit `7cd320b`) | — |

---

## Verdict

**For FY2027 the two sources are the same universe, and the disclosure workbook is a strict superset of the extracted Schedule C.**

Every one of the 9,978 extracted Schedule C rows has a disclosure counterpart. Not one row exists on the Schedule C side that the disclosure lacks — the direction that would have falsified the superset claim. The 62-row / $50.65M gap runs entirely the other way and is fully explained: those are **post-adoption designations**, which the Schedule C PDF states only in an initiative's header bar and prose, never as a provider table row.

The agreement is not approximate. **168 of 170 initiatives reconcile to the exact dollar** against the PDF's own printed initiative totals. 27 of 28 spending categories match exactly; the 28th is off by $2 from two single-dollar extraction errors.

This is strong evidence that FY2027 Schedule C extraction is sound, and it makes the disclosure workbook usable as an independent check on the other years.

**Three real extraction defects surfaced, all in fields other than money.** Money is right; labels are not. Details in §5–§7.

---

## 1. Headline counts

Command: `python3 code/parse_expense_disclosure.py` for the disclosure side; direct `csv` reads for Schedule C.

```
  disclosure FY2027             10040 rows  $   705,564,000
  Schedule C extracted (4 CSV)   9978 rows  $   654,910,412
  delta                            62 rows  $    50,653,588

  matched pairs                  9978 rows
  Schedule C rows with NO disclosure counterpart: 0
  disclosure rows with NO Schedule C counterpart: 62  $50,653,586
  matched pairs whose AMOUNT differs: 2  (net $+2)
  sum check: $50,653,586 + $2 = $50,653,588  == delta? True
```

The gap decomposes with nothing left over: 62 post-adoption rows plus two $1 extraction errors.

The extracted awards file also reproduces `fy27_schedule_c_reconciliation.txt` exactly — `awards 6118 rows $605,111,412` against a computed `$605,111,412 / 6118 rows`.

### Cleared vs. Pending

FY2027 is roughly half Pending, as expected for the upcoming year. Status lives only in the disclosure workbook; Schedule C carries no status field, so every status figure below is the disclosure's, reported for the Schedule C rows it matched.

```
disclosure, all 10,040 rows:
   Cleared      5037  $   143,034,722
   Pending      5003  $   562,529,278

disclosure rows that MATCHED into Schedule C (9,978):
   Cleared      5030  $   141,714,722
   Pending      4948  $   513,195,692

disclosure rows with NO Schedule C counterpart (62):
   Pending        55  $    49,333,586
   Cleared         7  $     1,320,000

by Schedule C file:
   awards   Cleared=1953 ($100,523,172)  Pending=4165 ($504,588,242)
   Aging    Cleared=392 ($4,695,000)     Pending=75 ($915,000)
   Local    Cleared=2044 ($30,487,300)   Pending=514 ($6,051,700)
   Youth    Cleared=641 ($6,009,250)     Pending=194 ($1,640,750)
```

Note the asymmetry: the appendices are overwhelmingly **Cleared** (Local 80%, Aging 84%, Youth 77% by row) while the main awards file is 68% Pending. Member-designated local awards clear early; large initiative-provider contracts do not.

---

## 2. Method, and one correction I had to make to it

Matching is a greedy multi-pass over `(EIN, amount, member, organization, program, initiative)`, finest key first, relaxing one field at a time. Both directions are multiset comparisons, so duplicate awards to the same organization are counted, not collapsed.

**A first version of this matcher produced 831 initiative disagreements and an appendix cross-tab showing `Local → appendix Youth 10` and `Youth → appendix Local 10`.** Those symmetric counts were the tell: the matcher was swapping two otherwise-identical rows across initiative boundaries, because initiative was not in the finest key. Adding it dropped the appendix cross-talk to **zero**:

```
   disclosure Source='Local'  -> Local     2558
   disclosure Source='Youth'  -> Youth      835
   disclosure Source='Aging'  -> Aging      467
```

Those three counts are also an independent confirmation of the appendix mapping — appendix A is Aging, B is Local, C is Youth — since they match the disclosure's `Source` counts exactly with no residue.

I am flagging this because the artifact was indistinguishable from a real finding at first glance. Any number in this report that came from a coarse-key pairing is labeled as such.

---

## 3. By EIN — both directions

```
disclosure distinct EIN: 2232   scheduleC distinct EIN: 2232
intersection: 2232
in Schedule C NOT in disclosure: 0    <-- falsifies superset if >0
in disclosure NOT in Schedule C: 0
```

**The EIN sets are identical.** All 10,040 disclosure EINs and all 9,978 Schedule C EINs are 9 digits; neither side has a blank.

At the multiset level only three EINs differ in row count, and they account for all 62 rows:

```
  136400434  disc=832 sc=772  delta=+60  'Bronx Community Board #1'
  133893536  disc= 56 sc= 55  delta= +1  'City University of New York'
  133505372  disc= 11 sc= 10  delta= +1  'Medicare Rights Center, Inc.'
```

**EIN 136400434 is not an organization key.** It is the City of New York's own EIN, shared across 72 distinct legal names in the disclosure and 81 in Schedule C — NYCHA (198 rows), Department of Education (145), Parks (120), Sanitation (58), CUNY, NYPD, the borough libraries, the District Attorneys, the Borough Presidents. Any analysis that treats EIN as an organization identifier will fuse every city agency into one entity. The first name attached to it in the file, "Bronx Community Board #1", is arbitrary.

---

## 4. The 62 disclosure-only rows — post-adoption designations

Split: **54 rows / $48,833,586 carry a blank Council Member**; 8 rows / $1,820,000 name one. 55 of 62 are Pending.

I read the Schedule C PDF to determine what these are. Page 171 shows the mechanism directly — an initiative whose header bar carries a dollar figure but whose body has no provider table:

> **Older Adults Across the Boroughs — $1,129,774**
> Agency: DFTA (125) · U/A: 003 - Out-Of-Home Services - OTPS · First Year Funded: Fiscal 2026
> **Designation Method:** The Council will designate $1,129,774 post-adoption for Fiscal 2027.

That is exactly disclosure row 8902 — `EIN 136400434 | '' | 'Department for the Aging' | $1,129,774 | 'Older Adults Across the Boroughs' | Pending`. There is no provider to extract, so the Schedule C parser correctly emits no row. The disclosure workbook records the allocation against the administering agency.

Page 172 shows the partial case:

> **Support Our Older Adults — $7,649,999**
> **Designation Method:** The Council will designate $420,000 post-adoption and has designated $7,229,999 to the following providers for Fiscal 2027:

Two disclosure rows are unmatched for this initiative — row 9033 (`Department for the Aging`, $410,000) and row 9034 (`Department of Cultural Affairs`, $10,000). They sum to **$420,000**, the stated post-adoption amount.

### The test that settles it

If the 62 rows are post-adoption designations, then for every initiative the **disclosure total** should equal the **PDF's printed initiative total**, even where the extracted provider rows fall short. Comparing every disclosure `Source` against `fy27_schedule_c_initiatives.csv` (stripping the `Multiple ` prefix the initiatives file uses for four entries):

```
  EXACT match : 168
  differ      : 1  [('Support Our Older Adults', '7,650,000', '7,649,999')]
  no counterpart: 1  ["Speaker's Initiative"]
```

168 of 170 initiatives reconcile to the dollar. Forty of them have a nonzero post-adoption residual, and in every one of those the disclosure total still lands exactly on the printed figure:

| Initiative | PDF printed | disclosure total | matched to providers | post-adoption residual |
|---|---:|---:|---:|---:|
| Afterschool Enrichment Initiative | $9,805,048 | $9,805,048 | $150,000 | $9,655,048 |
| Food Pantries | $10,467,000 | $10,467,000 | $1,266,000 | $9,201,000 |
| Homeowner Stabilization Services | $5,150,000 | $5,150,000 | $0 | $5,150,000 |
| Older Adult Center Improvements | $5,000,000 | $5,000,000 | $0 | $5,000,000 |
| SU-CASA | $3,825,000 | $3,825,000 | $0 | $3,825,000 |
| Nontraditional Worker Organizing and Education | $2,100,000 | $2,100,000 | $0 | $2,100,000 |
| Cultural After-School Adventure (CASA) | $17,340,000 | $17,340,000 | $15,620,000 | $1,720,000 |
| YouthBuild Project Initiative | $1,490,000 | $1,490,000 | $0 | $1,490,000 |
| Older Adults Across the Boroughs | $1,129,774 | $1,129,774 | $0 | $1,129,774 |
| Educational Programs for Students | $8,943,133 | $8,943,133 | $7,943,133 | $1,000,000 |
| Empowering Black Communities | $1,000,000 | $1,000,000 | $0 | $1,000,000 |
| NYC Cleanup | $14,280,000 | $14,280,000 | $13,401,000 | $879,000 |
| Domestic Violence and Empowerment (DoVE) | $12,010,000 | $12,010,000 | $11,160,000 | $850,000 |
| Gender-Affirming Care for TGNCNBI Youth | $3,500,000 | $3,500,000 | $2,833,333 | $666,667 |
| Healthy Beginnings | $4,593,244 | $4,593,244 | $4,118,003 | $475,241 |
| HIV/AIDS Pathways to Care | $11,339,653 | $11,339,653 | $10,911,934 | $427,719 |
| Support Our Older Adults | $7,649,999 | $7,650,000 | $7,230,000 | $420,000 |

(…24 more, all exact. Full list reproducible from the commands in §10.)

**This is the strongest single result in the report.** The disclosure workbook and the Schedule C PDF are two independently produced documents, and their per-initiative totals agree on 168 of 170 without any reconciliation step.

### Ten unmatched rows, quoted in full

Every one has `council_member=''` and `program_name=''` except where noted, and every one is Pending. Format: disclosure xlsx row number, EIN, member, legal name, amount, Source, status, agency.

1. `row 7993 | 136400434 | '' | 'Department of Youth and Community Development' | $9,201,000 | 'Food Pantries' | Pending | DYCD`
   purpose: *"This funding supports food and hygiene product purchases and operational expenses for food pantries and soup kitchens, and supplies school-based pantries with f…"*
   **Why it differs:** post-adoption. Initiative prints $10,467,000; only $1,266,000 reached named providers at adoption.

2. `row 10000 | 136400434 | '' | 'Department of Youth and Community Development' | $7,690,000 | 'Afterschool Enrichment Initiative' | Pending | DYCD`
   **Why:** post-adoption. This initiative has four such rows totaling $9,655,048 of a $9,805,048 allocation — almost entirely undesignated at adoption.

3. `row 8289 | 136400434 | '' | 'Housing Preservation and Development' | $5,150,000 | 'Homeowner Stabilization Services (Formerly Estate Planning and Resolution Initiative and Foreclosure Prevention Programs)' | Pending | HPD`
   **Why:** post-adoption, 100% of the initiative. No provider table exists in the PDF.

4. `row 8855 | 136400434 | '' | 'Department for the Aging' | $5,000,000 | 'Older Adult Center Improvements' | Pending | DFTA`
   **Why:** post-adoption, 100%.

5. `row 6996 | 136400434 | '' | 'Department of Cultural Affairs' | $3,825,000 | 'SU-CASA' | Pending | DCLA`
   purpose: *"To support senior centers in each Council District with arts programming."*
   **Why:** post-adoption, 100%. Allocation is per-district but districts are not yet assigned.

6. `row 8902 | 136400434 | '' | 'Department for the Aging' | $1,129,774 | 'Older Adults Across the Boroughs' | Pending | DFTA`
   **Why:** post-adoption, 100%. Verified against PDF p.171 — quoted above.

7. `row 9033 | 136400434 | '' | 'Department for the Aging' | $410,000 | 'Support Our Older Adults' | Pending | DFTA`
   **Why:** post-adoption. With row 9034 ($10,000, DCLA) sums to the $420,000 the PDF states on p.172.

8. `row 9961 | 136400434 | '' | "Administration for Children's Services" | $225,080 | 'Wrap-Around Support for Transitional-Aged Foster Youth' | Pending | ACS`
   **Why:** post-adoption residual of a $1,096,788 initiative.

9. `row 1699 | 136400434 | 'Speaker' | 'Department of Youth and Community Development' | $750,000 | "Speaker's Initiative" | Cleared | DYCD`
   **Why:** one of 8 unmatched rows that *do* name a member, and one of only 7 Cleared. The Speaker's Initiative is the single initiative with no printed total to check against, so this one is **INFERRED** to be an undesignated Speaker allocation, not verified.

10. `row 3085 | 133505372 | 'Speaker' | 'Medicare Rights Center, Inc.' | $135,000 | "Speaker's Initiative" | Cleared | DFTA`
    **Why:** the only unmatched row against a **non-City EIN with a real named organization**. This is the least explained of the 62 — see §8.

11. `row 9864 | 136400434 | '' | 'Department of Consumer and Worker Protection' | $2,100,000 | 'Nontraditional Worker Organizing and Education' | Pending | DCWP`
    **Why:** post-adoption, 100%. Also note `Department of Consumer and Worker Protection` never appears in Schedule C at all, since it has no provider rows.

---

## 5. Two amount mismatches — off by exactly $1 each

These are the only matched pairs whose amounts disagree, and both are **extraction** errors.

```
  DISC row 9188: EIN 135563028 'Osborne Association, Inc., The' 'Nurse' $15,000.00 [Pending] prog='Elder and Older Adult Reentry Initiatives'
  SC fy27_schedule_c_awards.csv:4682: 'Osborne Association, Inc., The' 'Nurse' $14,999.00 prog='Elder and Older Adult Reentry Initiatives'
  DELTA $+1.00

  DISC row 9227: EIN 131624178 'Selfhelp Community Services, Inc.' 'Lee' $45,000.00 [Pending] prog='Fresh Meadows NORC'
  SC fy27_schedule_c_awards.csv:4724: 'Selfhelp Community Services, Inc.' 'Lee' $44,999.00 prog='Fresh Meadows NORC'
  DELTA $+1.00
```

Organization, member, program, EIN, and initiative all match exactly; only the last digit of the amount is wrong. Both land in `Support Our Older Adults`, which is also the one initiative that fails the exact-total test. Three numbers exist for that initiative's designated providers and no two agree:

```
  disclosure providers $7,230,000 vs PDF prose $7,229,999 = $+1
  extracted providers  $7,229,998 vs PDF prose $7,229,999 = $-1
```

**The $1 between the disclosure and the PDF is a source-side discrepancy in the Council's own two documents, not an extraction error.** The extraction has its own separate $2 error. Do not conflate them: fixing lines 4682 and 4724 will make the extraction agree with the disclosure at $7,230,000 and leave it $1 above the PDF's printed $7,229,999.

**AMBIGUITY, left standing:** which figure is authoritative for `Support Our Older Adults` is a judgment I did not make.

---

## 6. By Source / initiative

The disclosure's `Source` and Schedule C's `initiative` are the same vocabulary. Distinct values: 173 disclosure (including `Local`/`Youth`/`Aging`), 158 Schedule C awards-side. After normalizing case, whitespace, curly apostrophes, and a trailing `Initiative`, only **3** Schedule C values have no disclosure counterpart:

```
  in Schedule C initiative, NOT in disclosure Source (3):
     'Initiative and Adult Literacy Forward)'  (64 rows, $14,500,000)
     'Neuter, and Release for Stray Animals)'  (1 rows, $500,000)
     'Speaker’s Initiative to Address Citywide Needs'  (608 rows, $86,387,049)
```

Two are **PDF line-wrap truncations** — the extractor captured the tail of a wrapped initiative header instead of the whole string:

| Schedule C captured | Disclosure's full name |
|---|---|
| `Initiative and Adult Literacy Forward)` | `NYC RISE with Adult Literacy Forward (Formerly Adult Literacy Initiative and Adult Literacy Forward)` |
| `Neuter, and Release for Stray Animals)` | `Spay/Neuter and Veterinary Care for Cats and Dogs (Formerly Trap, Neuter, and Release for Stray Animals)` |

The third is a genuine naming difference, not an error: the PDF uses the formal `Speaker's Initiative to Address Citywide Needs`, the workbook the short `Speaker's Initiative`. Note the PDF's curly apostrophe (U+2019).

On matched pairs the two vocabularies agree on **9,250 of 9,978 (92.7%)**. Of the 728 disagreements, 663 are the three naming variants above. The rest are §7.

### Dollars by category — 27 of 28 exact

```
  category                                               rows    disclosure $     extracted $    delta
  Speaker’s Initiative to Address Citywide Needs          608 $    86,387,049 $    86,387,049    exact
  Immigrant Services                                      201 $    86,357,141 $    86,357,141    exact
  Community Development                                   412 $    44,830,000 $    44,830,000    exact
  Education                                                78 $    42,131,186 $    42,131,186    exact
  Mental Health Services                                  227 $    40,267,110 $    40,267,110    exact
  (appendix Local)                                       2558 $    36,539,000 $    36,539,000    exact
  Criminal Justice Services                                80 $    33,342,153 $    33,342,153    exact
  Small Business Services and Workforce Development       239 $    30,215,853 $    30,215,853    exact
  Higher Education                                         17 $    29,561,869 $    29,561,869    exact
  Cultural Organizations                                 1242 $    28,181,000 $    28,181,000    exact
  Health Services                                         178 $    25,660,046 $    25,660,046    exact
  Older Adult Services                                    520 $    25,211,906 $    25,211,904      $+2
  Environmental Initiatives                               456 $    24,191,000 $    24,191,000    exact
  Food Initiatives                                         37 $    17,817,750 $    17,817,750    exact
  Legal Services                                           36 $    15,913,000 $    15,913,000    exact
  Domestic Violence Services                              419 $    14,943,334 $    14,943,334    exact
  Housing                                                 108 $    13,952,750 $    13,952,750    exact
  Young Women's Initiative                                 73 $    10,807,167 $    10,807,167    exact
  Youth Services                                           38 $     9,272,000 $     9,272,000    exact
  (appendix Youth)                                        835 $     7,650,000 $     7,650,000    exact
  Public Safety                                           107 $     5,647,600 $     5,647,600    exact
  (appendix Aging)                                        467 $     5,610,000 $     5,610,000    exact
  Parks and Recreation Services                           228 $     5,108,500 $     5,108,500    exact
  Community Safety and Victim Services                    324 $     5,100,000 $     5,100,000    exact
  Veteran Services                                         25 $     3,243,000 $     3,243,000    exact
  Anti-Poverty                                            294 $     2,800,000 $     2,800,000    exact
  Homeless Services                                         8 $     2,170,000 $     2,170,000    exact
  Boroughwide Needs                                       163 $     2,000,000 $     2,000,000    exact
```

The lone `$+2` is the two $1 rows from §5.

---

## 7. DEFECT — initiative labels shift across block boundaries

After the three naming variants are set aside, **65 rows / $16,135,000 carry a materially wrong initiative label in the extracted Schedule C.** Fifty-two of them fall in four contiguous runs; the remaining 13 are scattered singles, 11 of which sit on the boundary of the Speaker's Initiative block. The disclosure gives the correct assignment.

```
  lines 4248-4276  n=  29  $   4,025,000
     SC says       : 'Opioid Prevention and Treatment'
     disclosure says: 'Peer Specialists Support'
  lines 4229-4242  n=  14  $   2,275,000
     SC says       : 'Older Adults Mental Health'
     disclosure says: 'Opioid Prevention and Treatment'
  lines 3691-3697  n=   7  $   5,650,000
     SC says       : 'Creative Arts Team'
     disclosure says: 'CUNY Research Institutes'
  lines 4244-4245  n=   2  $     700,000
     SC says       : 'Older Adults Mental Health'
     disclosure says: 'Opioid Prevention and Treatment'
```

The alphabetical ordering inside `fy27_schedule_c_awards.csv` is the visible tell. Lines 4194–4228 run Bridge → BronxWorks → … → Young Adult Institute, a complete A-to-Y block. Line 4229 restarts at Amudim → Bailey House → … → Young Men's Christian Association — a **new** initiative block that inherited the previous label.

The arithmetic confirms it independently. Reassigning by the matched disclosure partner reproduces the disclosure's own subtotals to the dollar:

```
  Older Adults Mental Health           disc  35 $  3,474,520 | SC-matched  35 $  3,474,520 | unmatched 0
  Opioid Prevention and Treatment      disc  17 $  3,075,000 | SC-matched  17 $  3,075,000 | unmatched 0
  Peer Specialists Support             disc  32 $  4,500,000 | SC-matched  31 $  4,225,000 | unmatched 1
  CUNY Research Institutes             disc   7 $  5,650,000 | SC-matched   7 $  5,650,000 | unmatched 0
  Creative Arts Team                   disc   1 $    400,000 | SC-matched   1 $    400,000 | unmatched 0
```

Compare against what the extracted labels currently produce: `Older Adults Mental Health` is credited **52 rows / $6,549,520** instead of 35 / $3,474,520, and `CUNY Research Institutes` is credited **0 rows / $0** instead of 7 / $5,650,000 — its entire $5.65M sits under `Creative Arts Team`.

**VERIFIED.** The amounts are right; only the initiative attribution is wrong. Any per-initiative aggregate built from `fy27_schedule_c_awards.csv` today misstates these five initiatives.

---

## 8. By council member — evidence for issue #51

### The rosters are identical, and neither disambiguates

Both sources carry **57 distinct member values**. They are the same 57 apart from a suffix on the four borough delegations (`Brooklyn Delegation` vs `Brooklyn`).

```
disclosure (57): ['Abreu', 'Aldebol', 'Ariola', 'Aviles', 'Banks', 'Brewer', 'Bronx Delegation',
 'Brooklyn Delegation', 'Brooks-Powers', 'Caban', 'Carr', 'De La Rosa', 'Dinowitz', 'Encarnacion',
 'Epstein', 'Farias', 'Felder', 'Feliz', 'Gennaro', 'Gutierrez', 'Hanif', 'Hankerson', 'Hanks',
 'Hudson', 'J. Sanchez', 'Joseph', 'Krishnan', 'Lee', 'Louis', 'Maloney', 'Manhattan Delegation',
 'Marte', 'Mealy', 'Menin', 'Morano', 'Narcisse', 'Nurse', 'Osse', 'P. Sanchez', 'Paladino',
 'Queens Delegation', 'Restler', 'Riley', 'Salaam', 'Santosuosso', 'Schulman', 'Speaker',
 'Staten Island Delegation', 'Stevens', 'Thomas-Henry', 'Ung', 'Vernikov', 'Williams', 'Wilson',
 'Won', 'Wong', 'Zhuang']
```

**Answer to the issue #51 question: for FY2027, the disclosure adds no disambiguation power.**

```
  Williams  disclosure=['Williams']            scheduleC=['Williams']
  Sanchez   disclosure=['J. Sanchez', 'P. Sanchez']  scheduleC=['J. Sanchez', 'P. Sanchez']
  Rivera    disclosure=[]                      scheduleC=[]
  Barron    disclosure=[]                      scheduleC=[]
  Vallone   disclosure=[]                      scheduleC=[]

  disclosure values containing a digit: []
  scheduleC  values containing a digit: []
```

Neither source carries a first name or a district number. `Sanchez` is already split by initial in **both**, identically. `Rivera`, `Barron`, and `Vallone` are not in the FY2027 Council. FY2027 is simply not a year where the collision bites — the disclosure would have to be checked against FY2014–FY2022 to test whether it helps there. Its `Council Member` column uses the same bare-surname convention, so **INFERRED: it probably will not help in those years either**, but that is not verified here.

### DEFECT — the `member` column is contaminated by text bleed

Member values agree on 9,158 of 9,978 matched pairs (91.8%). The 820 disagreements break into four groups. All 820 come from pairings made on a key that excluded member, so each rests on EIN + amount + organization + program evidence.

**(a) 497 rows: disclosure `Speaker` → Schedule C blank.** Structural, not an error — see (d).

**(b) 129 rows: delegation suffix.** `Brooklyn Delegation` → `Brooklyn`, etc. A pure naming convention difference. Six of these 129 also fall in group (c) — the categories overlap, and the disjoint restatement is below.

**(c) 91 rows / $20,011,231: a borough word split out of the organization name into `member`.** This is a real defect.

```
  fy27_schedule_c_awards.csv:3963
     SC   member='Brooklyn'       organization='Defender Services'
     DISC member=''               legal_name  ='Brooklyn Defender Services'   ($8,300,000, Pending)
  fy27_schedule_c_awards.csv:765
     SC   member='Brooklyn'       organization='Community Pride Center, Inc.'
     DISC member=''               legal_name  ='Brooklyn Community Pride Center, Inc.'   ($544,375, Pending)
  fy27_schedule_c_awards.csv:3271
     SC   member='Queens'         organization='Botanical Garden Society, Inc.'
     DISC member=''               legal_name  ='Queens Botanical Garden Society, Inc.'   ($450,000, Pending)
  fy27_schedule_c_awards.csv:41
     SC   member='Brooklyn'       organization='Museum'
     DISC member='Hudson'         legal_name  ='Brooklyn Museum'   ($10,000, Cleared)
  fy27_schedule_c_awards.csv:5042
     SC   member='Manhattan'      organization='College'
     DISC member=''               legal_name  ='Manhattan College'   ($100,000, Pending)
```

Distribution: Brooklyn 45, Queens 22, Staten Island 17, Manhattan 7.

**The consequence is that the Schedule C value `Brooklyn` is overloaded and cannot be read as a member**, and nothing in the file distinguishes the two meanings. Six rows are simultaneously both — a Brooklyn-delegation designation to an organization whose name also begins "Brooklyn" — so the categories are not disjoint. Restated disjointly:

| SC `member` value | total rows | org-name leak | (of those, also delegation-designated) | delegation only | neither |
|---|---:|---:|---:|---:|---:|
| `Brooklyn` | 106 | 45 | 5 | 57 | 4 |
| `Queens` | 68 | 22 | 1 | 39 | 7 |
| `Manhattan` | 29 | 7 | 0 | 16 | 6 |
| `Staten Island` | 29 | 17 | 0 | 11 | 1 |

**A `GROUP BY member` over FY2027 Schedule C attributes $20,011,231 of awards to phantom borough "members."**

The mechanism is visible where the bleed is longer. In `fy27_appendix_b_local.csv`:

```
line 372: member='Restler' | org='Brooklyn Public Library'
          purpose='Funding to support educational programming at the Center for Brooklyn History in'
line 373: member='Brooklyn' | org='Heights. Aviles Brooklyn Public Library'
          purpose='Funds to support Older Adults Wellness and Arts Programs at New Utrecht Public Library.'
```

Line 372's purpose is truncated mid-sentence at "in". The wrapped continuation "Brooklyn Heights." was split across line 373's `member` and `organization`, and line 373's real member — `Aviles` — was swallowed into the organization string. **The true line 373 is `member='Aviles', organization='Brooklyn Public Library'`.**

The same bleed corrupts organization names outright:

```
line 5389: org='Funds will support small business support, public events, cultural programming, and
                community beautification in Council District 47. Alliance of Resident Theatres/New York, Inc.'
line 5390: org="Funding to support programming expenses with an emphasis on space, training and education,
                strategic support and building connections amongst New York's theater community. American
                Composers Orchestra"
```

**(d) 80 rows: disclosure `Speaker` → Schedule C names a member.** Here **Schedule C is genuinely richer, and the extraction throws most of it away.** PDF pages 268–271 show the Speaker's Initiative section uses a **`Sponsor`** column, not `Council Member`, and it holds values the extractor cannot represent:

| PDF `Sponsor` cell | What the CSV captured |
|---|---|
| `Krishnan, Lee` (2 members) | line 5530 `member='Manhattan'` (bled from prior purpose), `org='(two vans with 15 feeding sites) and the Bronx (one van with seven feeding sites). Krishnan, Lee Commonpoint NY, Inc.'` |
| `Lee, Queens` (member + delegation) | line 5533 `member=''`, `org='Lee, Queens Commonpoint NY, Inc.'` |
| `Lee, Queens, Restler` (3 sponsors) | line 5535 `member=''`, `org='Lee, Queens, Restler Communities Resist Inc.'` |
| `Dinowitz, Osse` | line 5547 `member=''`, `org='Dinowitz, Osse Council on the Environment, Inc.'` |
| `Progressive` (a **caucus**) | line 5536 `member=''` — lost entirely |
| `LGBTQIA+` (a **caucus**) | lost entirely |
| `Vernikov` (single) | line 5546 `member=''` — lost |
| `Mealy` (single) | line 5590 `member=''` — lost |
| `Hudson` (single) | line 5537 `member='Hudson'` — correct |

Confirmation that no multi-sponsor cell survived anywhere in the file:

```
rows with a comma in member: 0
```

Schedule C attributes 103 of 608 Speaker's-Initiative awards to a named sponsor where the disclosure records all 608 as `Speaker`. Those 103 break down as:

- **80** carry a real member surname — genuine sponsor data the disclosure does not have.
- **13** are borough-word bleed from group (c) (Staten Island 5, Brooklyn 4, Manhattan 2, Queens 2) — e.g. line 5445 `member='Brooklyn'`, `org='Academy of Music'` against disclosure `'Brooklyn Academy of Music'`, $2,500,000.
- **10** hold a bare borough name that is not org-name bleed, and are therefore **AMBIGUOUS**: the PDF's `Sponsor` column does use borough delegations (`Lee, Queens`), so these may be genuine delegation sponsorships or may be bleed I could not distinguish.

An unknown further number of genuine multi-sponsor and caucus cells were dropped entirely. The sponsor data is real and worth having; the current extraction of it is not usable.

**AMBIGUITY:** I did not count how many Sponsor cells the extractor lost in total. That needs a full page-by-page read of the Speaker's Initiative section (PDF pp. ~262–290), which this run did not do.

---

## 9. Exact-award matching — headline numbers

Multiset match, both directions.

**On `(EIN, amount)`:**
```
disclosure rows 10040, scheduleC rows 9978
matched pairs (multiset intersection): 9976
disclosure-only rows: 64
scheduleC-only rows : 2
```

**On `(EIN, amount, member)`:**
```
matched: 9158   disc-only: 882   sc-only: 820
```

The drop from 9,976 to 9,158 is **entirely** the member-field differences catalogued in §8 — the `Speaker`/blank convention, the delegation suffix, and the borough-word bleed. It is not a data disagreement.

**On the full hierarchical key (§2):**
```
matched 9978  D-unmatched 62 ($50,653,586)  S-unmatched 0
```

The two `scheduleC-only` rows under the coarse key are the $14,999 and $44,999 rows from §5; they bind at `ein+org+prog` once amount is relaxed.

---

## 10. Reproducing this

Scripts were written to a scratch directory and are not committed — they are throwaway. The load is three lines:

```python
import sys; sys.path.insert(0, "code")
from parse_expense_disclosure import parse_year
disc, rep = parse_year("source/expense-funding-disclosure/funded_disclosure_FY2027.xlsx")
```

Schedule C is four `csv.DictReader` passes over `data/fy27/schedule_c/`. Normalization used throughout: EIN to 9 digits zero-padded; amounts via `float` after stripping `,` and `$`; text lowercased with curly quotes and dashes folded and non-alphanumerics collapsed to single spaces; initiative additionally stripped of a trailing `initiative` and a leading `multiple `.

If this is worth re-running per year, it belongs in a committed script. It is not one yet.

---

## 11. What this does and does not establish

**VERIFIED for FY2027:**
- Zero Schedule C rows absent from the disclosure. The superset claim holds in the direction that could have falsified it.
- EIN sets identical (2,232 each way).
- 168 of 170 initiative totals reconcile exactly against the PDF's own printed figures; the 170th is off by $1 between the Council's two documents.
- 27 of 28 category totals exact; the 28th off by $2.
- The 62-row / $50.65M gap is post-adoption designations, confirmed against PDF pp. 171–172 and against 40 independent initiative-total reconciliations.
- Three extraction defects: 65 rows with wrong initiative labels (§7), 91 rows with a borough word split out of the organization into `member` (§8c), and near-total loss of the Speaker's Initiative `Sponsor` column (§8d).
- Two $1 amount errors (§5).

**INFERRED, not verified:**
- That the disclosure will not disambiguate `Williams`/`Rivera`/`Barron`/`Vallone` in earlier years. FY2027 has no collision to test.
- That disclosure row 1699 (`Speaker`, DYCD, $750,000) is an undesignated Speaker allocation. The Speaker's Initiative has no printed total to check against.

**AMBIGUITY, left standing:**
- Which figure is authoritative for `Support Our Older Adults` — the disclosure's $7,650,000 or the PDF's $7,649,999.
- Disclosure row 3085 (`Speaker`, `Medicare Rights Center, Inc.`, EIN 133505372, $135,000, Cleared) is the only unmatched row naming a real non-City organization. The other 61 are City-EIN agency allocations or Speaker allocations. I do not know why this one has no Schedule C provider row.
- The total number of `Sponsor` cells the extractor dropped from the Speaker's Initiative section.

**Explicitly out of scope tonight:** FY2016–FY2020, where extraction is known broken; the empty appendix CSVs for FY2015–FY2017 and FY2019–FY2020; and any fix to a parser.

**Caution for the other years.** FY2027 is a *good* case — 49.8% Pending, heavy post-adoption residual, and a modern workbook layout. Close agreement here does not transfer. It does establish that the comparison method works and that the disclosure workbook is a legitimate independent check, which is what the FY2016–FY2020 investigation needs.
