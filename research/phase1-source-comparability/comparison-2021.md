---
title: "FY2021 — Council expense disclosure vs parsed Schedule C, source comparability"
created: 2026-08-12
type: research
status: complete
tags: [nyc-budget, schedule-c, expense-disclosure, data-integrity, fy2021]
---

# FY2021 — disclosure spreadsheet vs parsed Schedule C

**Report generated:** 2026-08-12
**Data current as of:** 2026-08-12 — committed `data/` tree at `de251b5`, `source/expense-funding-disclosure/funded_disclosure_FY2021.xlsx` as verified byte-identical to the Council's published copy on 2026-08-11. No network calls, no re-extraction.

**Sources compared**

| Side | Files |
|---|---|
| Disclosure | `source/expense-funding-disclosure/funded_disclosure_FY2021.xlsx`, read via `code/parse_expense_disclosure.py` |
| Schedule C | `data/fy21/schedule_c/fy21_schedule_c_awards.csv` + `fy21_appendix_a_aging.csv` + `fy21_appendix_b_local.csv` + `fy21_appendix_c_youth.csv` |

**Reproduce:** `python3 research/phase1-source-comparability/compare_year.py 2021` for the counts, `python3 research/phase1-source-comparability/diagnose_2021.py` for the diagnosis. The second carries a `demo()` asserting the headline claims below; it fails loudly if either source is re-parsed into different numbers.

Every count in this report was produced twice, by two independently written comparison scripts (`compare_year.py`, from a parallel session, and my own scratch implementation). They agree on every headline figure. Where they could not both check something, it is marked INFERRED.

---

## Verdict

**The two sources describe the same universe. The disclosure spreadsheet is NOT a superset of Schedule C.**

Both halves matter and they are usually stated as if only one could be true.

The *same universe* half is strongly supported. All three Schedule C appendices reproduce their disclosure counterpart **to the dollar**, and 50 of the 85 initiatives whose names map across the two vocabularies agree to the dollar as well. That is not the signature of two different datasets.

The *not a superset* half is what falsifies the convenient assumption. **74 Schedule C EINs, 101 rows, $1,539,674 have no FY2021 disclosure row at any amount.** Of those 74 EINs, **66 are disclosed by the Council in at least one other fiscal year** — so they are real organizations with real EINs that the FY2021 workbook simply does not carry. Only 8 appear in no disclosure year at all and are plausible Schedule C transcription errors.

$1.54M against Schedule C's $251.9M is 0.6% of dollars and 1.7% of rows. Small, but it is not zero, and "0.6%" is the answer to a question nobody asked. The operative fact is that **the disclosure workbook cannot be used as a completeness check on Schedule C**, because for 66 organizations it is the less complete of the two.

---

## 1. Row and dollar totals

```
python3 research/phase1-source-comparability/compare_year.py 2021
```

```
disclosure   rows   9054   $393,250,506.00   sheet='FY21 (06-23-2023)'
    status cleared    rows   8934   $391,770,561.00
    status pending    rows    120   $1,479,945.00
schedule C   rows   6120   $251,869,188.00
    appendix_a_aging     rows    514   $5,610,000.00
    appendix_b_local     rows   2902   $36,539,000.00
    appendix_c_youth     rows    894   $7,650,000.00
    awards               rows   1810   $202,070,188.00
      award_type initiative_provider  rows  1320   $186,751,269.00
      award_type member_item          rows   490    $15,318,919.00
```

VERIFIED. The Schedule C row and dollar figures match `fy21_schedule_c_reconciliation.txt` exactly (`awards: 1810 rows $202,070,188`, `appendix A 514 / $5,610,000`, `appendix B 2902 / $36,539,000`, `appendix C 894 / $7,650,000`).

**Cleared vs Pending exists only on the disclosure side.** No Schedule C CSV carries a status column — `awards.csv` is `category,initiative,award_type,member,organization,program,ein,amount,agency,purpose`, and the appendices are narrower still. Every Cleared/Pending split below is therefore a property of the disclosure workbook alone, and no Schedule C row can be assigned a clearance state.

**Pending does not mean "absent from Schedule C."** Of the 120 pending disclosure rows, **103 (85.8%)** have an `(EIN, amount)` match in Schedule C — a *higher* hit rate than the cleared rows (6,456 of 8,934, 72.3%). Pending is a MOCS clearance state, not a funding decision, and it does not predict Schedule C membership.

### The $141M gap is structural, not a discrepancy

Disclosure carries $393.3M against Schedule C's $251.9M. Nearly all of that sits in one bucket:

| Bucket | Disclosure | Schedule C | Δ rows | Δ $ |
|---|---|---|---|---|
| Aging | 514 rows, $5,610,000 | 514 rows, $5,610,000 | 0 | **$0** |
| Local | 2,936 rows, $36,539,000 | 2,902 rows, $36,539,000 | +34 | **$0** |
| Youth | 901 rows, $7,650,000 | 894 rows, $7,650,000 | +7 | **$0** |
| everything else | 4,703 rows, $343,451,506 | 1,810 rows, $202,070,188 | +2,893 | +$141,381,318 |

The three appendices agree **to the dollar** with their disclosure Source buckets while carrying slightly fewer rows. The entire divergence lives in the main `awards.csv`, which is the file extracted from the printed Schedule C body — and which is visibly incomplete for FY2021 (see §5).

---

## 2. By EIN, both directions

EINs normalized to 9 digits, leading zeros preserved, non-digits stripped.

```
distinct EIN  disclosure   2033   schedule C   1899   in both   1825
Schedule C EIN NOT in disclosure : 74   ($1,539,674.00, 101 rows)
disclosure EIN NOT in Schedule C : 208  ($23,562,931.00, 352 rows)
    of those disclosure-only rows: cleared 343, pending 9
```

Neither side has a row with an unusable EIN. VERIFIED.

### The direction that matters: Schedule C → disclosure

The 74 Schedule-C-only EINs split cleanly when tested against every other disclosure year FY2014–FY2027:

| | EINs |
|---|---|
| Disclosed in at least one **other** fiscal year, absent from FY2021 | **66** |
| Disclosed in **no** fiscal year at all | 8 |

VERIFIED, by re-parsing all 14 workbooks and testing EIN membership per year (`diagnose_2021.py` §1).

The 66 are real FY2021 disclosure gaps. A representative one, traced in full:

**Sustainable South Bronx, EIN 02-0535999**

```
FY2020 disclosure row 9619: 'Sustainable South Bronx' member='Speaker' $25,000 source='Local'
FY2021 disclosure        : no row for EIN 020535999; no org named 'Sustainable South Bronx' at any EIN
FY2022 disclosure        : no org named 'Sustainable South Bronx'
FY2021 SCHEDULE C [appendix_b_local]: member='Speaker' $25,000 org='Salamanca Sustainable South Bronx' ein=020535999 agency='SBS'
FY2021 SCHEDULE C [appendix_b_local]: member='Gibson'  $5,000  org='Sustainable South Bronx'          ein=020535999 agency='DYCD'
```

The FY2020 disclosure carries the identical `Speaker` / $25,000 / Local designation. FY2021 Schedule C carries it too. The FY2021 disclosure workbook carries neither it nor the org under any spelling. The organization did not stop existing between the two rows; the workbook stopped listing it.

(Note the Schedule C org string `'Salamanca Sustainable South Bronx'` — a sponsor surname concatenated onto the legal name by the PDF extraction. FY2020 disclosure shows Salamanca sponsoring this org repeatedly, so the bleed is real and identifiable. This is a Schedule C defect sitting on top of a disclosure gap.)

The 8 EINs in no disclosure year, quoted in full — these are the plausible Schedule C EIN transcription errors:

```
112023047  'Our Lady of Hope Roman Catholic Church'                  Holden      $5,000
113044143  'Federazione Italo-Americana of Brooklyn & Queens, Inc.'  Holden      $5,000
133202305  'Dyckman Resident Association'                            Rodriguez   $5,000
133776486  'White Plains Road District Management Association'       Gjonaj     $11,000
202474691  'Quilts of Valor: Quilters by the Sea'                    Gjonaj      $5,000
265551998  'Association for Neighborhood & Housing Development'      (blank)    $85,000
464636329  'Do You Enlightenment and Cultural Empowerment Services'  Ampry-Samuel $5,000
834167441  'Amayas Bookreads, Inc.'                                  Rodriguez   $5,000
```

Only one of the 8 resolves cleanly: ANHD (see M1 below) is in FY2021 disclosure under EIN **132775999** with all three matching amounts. The Schedule C EIN 265551998 is wrong. For the other 7 no same-named disclosure org exists at token-overlap ≥ 0.6, so **which side is wrong is undetermined** — the org may be absent from disclosure, or the Schedule C EIN may be misread. Do not assume either without an external check against IRS BMF or Charities Bureau.

### disclosure → Schedule C

208 EINs / 352 rows / $23,562,931 appear only in disclosure. This is the expected direction given `awards.csv` is materially incomplete for FY2021, and it does not falsify anything.

---

## 3. By Source / initiative

**136** distinct disclosure `Source` values against **119** distinct Schedule C `initiative`/`category` values. After case- and punctuation-insensitive slugging, **85 map exactly.**

Of those 85:

| | count | dollars |
|---|---|---|
| Dollar totals identical | **50** | $115,421,313 |
| Dollar totals differ | 35 | — |

Within the 50 dollar-identical initiatives: 40 also have identical row counts, **10 have more rows on the disclosure side, and 0 have more rows on the Schedule C side.** VERIFIED. Where the money agrees, disclosure is never the coarser record — it splits designations that Schedule C aggregates, never the reverse.

### Vocabulary present in one and not the other

The naming is genuinely different, not merely differently punctuated. Representative pairs that a slug-match misses and a human would not:

| Schedule C | Disclosure |
|---|---|
| `Anti-Poverty Initiative` (317) | `Anti-Poverty` (318) |
| `Boroughwide Needs` (128) | `Boroughwide Needs Initiative` (128) |
| `Speaker's Initiative to Address Citywide Needs` (133) | `Speaker's Initiative` (144) |
| `HIV/AIDS Faith-Based` (24) | `HIV/AIDS Faith Based Initiative` (25) |
| `Access Health` (10) | `Access Health Initiative` (48) |
| `Court-Involved Youth Mental Health` (10) | `Court-Involved Youth Mental Health Initiative` (22) |
| `Diversity, Inclusion and Equity in Tech` (3) | `Diversity, Inclusion & Equity in Tech Initiative` (3) |
| `LGBT Senior Services in Every Borough` (2) | `LGBTQ Senior Services in Every Borough` (2) |
| `Elder Abuse Prevention Programs` (5) | `Elder Abuse Enhancement` (5) |
| `DOHMH Viral Hepatitis Prevention` (32) | *(no counterpart; disclosure has `Viral Hepatitis Prevention`, which Schedule C ALSO has separately at 30)* |

Ten Schedule C "initiative" values are budget **categories** leaking into the initiative column (`Housing` 59, `Community Development` 31, `Cultural Organizations` 29, `Mental Health Services` 24, `Immigrant Services` 19, `Young Women's Initiative` 6, `Domestic Violence Services` 4, `Public Safety` 4, `Small Business Services and Workforce Development` 4, `Youth Services` 1) — an artifact of `awards.csv` falling back to `category` when `initiative` is blank, which it is for **442 of 1,810 rows**. Two of the twelve fallback values (`Speaker's Initiative to Address Citywide Needs` 133, `Boroughwide Needs` 128) are genuine initiative names and are not miscategorized.

**51 disclosure Source values have no Schedule C counterpart at all**, and several are large: `Cultural After-School Adventure (CASA)` 714 rows / $14,280,000, `Cultural Immigrant Initiative` 334 / $6,375,000, `NYC Cleanup` 149 / $8,160,000, `A Greener NYC` 152 / $2,040,000, `Digital Inclusion and Literacy Initiative` 96 / $1,530,000, `Neighborhood Development Grant Initiative` 75 / $1,020,000, `Community Housing Preservation Strategies` 68 / $3,103,350. `Food Pantries` is present in Schedule C but with **1 row / $1,000,000** against disclosure's **410 rows / $21,659,000**.

INFERRED: these are the initiatives whose provider lists the FY2021 Schedule C extraction did not capture from the printed body, rather than initiatives the Council funded outside Schedule C. Consistent with the $141M `awards.csv` shortfall and with the 442 blank-initiative rows, but not independently confirmed against the source PDF in this run.

---

## 4. By council member — and issue #51

```
distinct values  disclosure 58   schedule C 57
blank member     disclosure 1663 ($286,699,506)   schedule C 1350
```

### The disclosure workbook does NOT disambiguate colliding surnames

Direct answer to the question issue #51 asks. Taking each name in turn, as the two sources actually publish them:

| Surname | Disclosure | Schedule C | Disambiguated? |
|---|---|---|---|
| Williams | *(absent from FY2021)* | *(absent)* | untestable this year |
| Sanchez | *(absent from FY2021)* | *(absent)* | untestable this year |
| Rivera | `Rivera` (153) | `Rivera` (111) | **no** — bare surname both sides |
| Barron | `Barron` (81) | `Barron` (50) | **no** |
| Vallone | `Vallone` (115) | `Vallone` (84) | **no** |
| Diaz | `Diaz` (123), `D. Diaz` (88) | `Diaz` (73) | **partially** — one initial, on one of the two |

**The disclosure workbook offers no district number, no first name, and no member ID.** It publishes the same bare surname Schedule C does. The single exception is `D. Diaz` alongside `Diaz`, which distinguishes two simultaneous Díaz members by one initial and nothing more.

So: **the disclosure spreadsheet is not a solution to the surname-collision problem.** It cannot resolve Williams or Sanchez, which are the two names issue #51 names first, and for FY2021 it does not even contain them. Any fix has to come from a member roster keyed to district and term, not from this file.

### What the disclosure workbook does carry: seat succession

This is the larger member-side finding and it was not anticipated.

Restricting to `(EIN, amount)` keys that are **unique on both sides** — necessary, because a $5,000 key otherwise joins every member who gave $5,000 to that org and manufactures hundreds of spurious pairs:

```
unique-key matches: 2485   member identical: 2215 (89.1%)   member differs: 270
```

Of the 270 that differ, five pairs dominate and every one is a mid-FY2021 seat change:

```
   43  schedule C 'Lancman'   -> disclosure 'Gennaro'
   40  schedule C 'Richards'  -> disclosure 'Brooks-Powers'
   35  schedule C 'Menchaca'  -> disclosure 'Aviles'
   19  schedule C 'Torres'    -> disclosure 'Feliz'
   14  schedule C 'King'      -> disclosure 'Riley'
```

Confirmed per-member across the full row sets, not just unique keys:

```
schedule C King        n=  31  unmatched=  0  [('Riley', 26), ('Levin', 4), ('Johnson', 1)]
schedule C Lancman     n=  90  unmatched=  1  [('Gennaro', 70), ('Brooks-Powers', 5), ('Diaz', 3)]
schedule C Menchaca    n=  51  unmatched=  0  [('Aviles', 42), ('Brannan', 2), ('D. Diaz', 1)]
schedule C Richards    n=  99  unmatched=  3  [('Brooks-Powers', 62), ('Gennaro', 6), ('Kallos', 6)]
schedule C Torres      n=  44  unmatched=  1  [('Feliz', 19), ('Diaz', 2), ('Gibson', 2)]
```

**The two sources disagree about who sponsored a designation, for five seats, on the same money.** Schedule C names the member who held the seat when the budget was adopted; the disclosure workbook names the successor.

The mechanism is VERIFIED from the file itself, not assumed: **the FY2021 worksheet is named `FY21 (06-23-2023)`.** The workbook is a snapshot taken 2023-06-23 — three fiscal years after FY2021 was adopted — and it has been maintained since. The adjacent years carry the same pattern (`FY20 (06-16-2022)`, `FY22 (07-11-2023)`, `FY23 (07-11-2023)`). Schedule C is frozen at adoption; the disclosure workbook is a living document that rewrites the sponsor field as seats turn over.

INFERRED, not verified here: that each named pair is in fact the same council district changing hands. The pairing is verified from the data; the district identity is not, because neither source carries a district number.

`D. Diaz` is a **different** phenomenon and should not be filed with the five. 40 of her 88 disclosure rows have no `(EIN, amount)` match anywhere in Schedule C, and 28 of the rest land on blank-member Schedule C rows — not on a predecessor. She is not a relabel of anyone. INFERRED: these are designations made after adoption for a seat with no adopted Schedule C designations. Not confirmed.

Four further name differences are purely cosmetic: Schedule C `Brooklyn` / `Manhattan` / `Queens` / `Staten Island` are disclosure's `Brooklyn Delegation` / `Manhattan Delegation` / `Queens Delegation` / `Staten Island Delegation`.

---

## 5. Exact award match, both directions

Multiset match, so repeated identical designations are counted rather than collapsed.

| Key | matched pairs | Schedule C unmatched | disclosure unmatched |
|---|---|---|---|
| `(EIN, amount)` | 5,840 | 280 | 3,214 |
| `(EIN, amount, member)` | 5,308 | 812 | 3,746 |

Adding `member` to the key costs **532 matches**. That is the seat-succession effect priced: about two-thirds of the loss is the five relabeled seats, and it is the single strongest argument against joining these two sources on member name.

### Repeated rows are mostly real, not extraction noise

100 appendix keys repeat within a Schedule C file, 268 surplus rows. I checked these against disclosure rather than assuming they were duplicates, and **they are overwhelmingly genuine multiple designations that disclosure repeats identically**:

```
x5  scheduleC[appendix_b_local] 'Matteo' $25,000 ein=133706442 'Staten Island Economic Development Corporation'
      disclosure has 5 matching rows: [8056, 8057, 8059, 8060, 8061]
x16 scheduleC[appendix_b_local] 'Rose'      $542 ein=136400434 'Department of Education'
      disclosure has 16 matching rows: [2395, 2400, 2402, 2403, 2434, ...]
x3  scheduleC[appendix_b_local] 'Cornegy' $5,000 ein=113250772 'Bridge Street Development Corporation'
      disclosure has 3 matching rows: [868, 870, 871]
```

Counts match exactly. The exceptions have a known cause — `x5 'Richards' $1,000 NYCHA` and `x4 'King' $2,000 NYCHA` return zero disclosure matches because those members were relabeled.

EIN **136400434** is a city-agency placeholder used for pass-through designations to agencies, community boards, borough presidents, and DAs. **It is present on both sides** — 684 disclosure rows / $26,840,960, and 520 Schedule C rows. I initially recorded it as disclosure-only; that was wrong and is corrected here. It carries 61 distinct `legal_name` values under one EIN, so any EIN-keyed join will over-collapse it.

---

## 6. Ten-plus mismatches read individually

All quoted verbatim from the two sources via `diagnose_2021.py` §3.

**M1 — ANHD: same org, two different EINs. Schedule C is wrong.**
```
DISCLOSURE row 445: source='Community Housing Preservation Strategies' member='' legal_name='Association for Neighborhood & Housing Development, Inc.' ein=132775999 amount=50,540 status='cleared' agency='HPD'
DISCLOSURE row 446: ... ein=132775999 amount=25,270 status='cleared'
DISCLOSURE row 447: ... ein=132775999 amount=85,000 status='cleared'
SCHEDULE C [awards]: initiative='the capacity and technical skills of the providers within this initiative. This initiative provides' organization='Association for Neighborhood & Housing Development, Inc.' ein=265551998 amount=85,000
SCHEDULE C [awards]: ... ein=265551998 amount=50,540
```
Why: all three amounts match; only the EIN differs, and 265551998 appears in **no** disclosure year while 132775999 appears in FY2021. The Schedule C EIN is a misread. Note also that this row's `initiative` field is a fragment of prose from the PDF body — a second, independent defect in the same row.

**M2 — Asiyah Women's Center: same org, two different EINs, side undetermined.**
```
DISCLOSURE row 436: source='Local' member='Brannan' legal_name="Asiyah Women's Center, Inc." ein=832104070 amount=5,000 status='cleared' agency='DYCD'
DISCLOSURE row 437: source='Local' member='Perkins' legal_name="Asiyah Women's Center, Inc." ein=832104070 amount=7,500 status='cleared' agency='MOCJ'
SCHEDULE C [appendix_b_local]: member='Perkins' organization="Asiyah Women's Center" ein=822712941 amount=7,500 agency='MOCJ'
```
Why: member, amount and agency all match; only the EIN differs. Unlike M1 this one does **not** resolve — 822712941 is disclosed in FY2023–FY2025, and 832104070 in FY2021. Both EINs are real in some year. AMBIGUOUS: which is correct for FY2021 cannot be settled from these files.

**M3 — BAFA: disclosure splits one Schedule C row into three.**
```
DISCLOSURE row 512: source='Anti-Poverty' member='Diaz' legal_name='BAFA - Bangladesh Academy of Fine Arts, Inc.' ein=454788710 amount=7,500 status='cleared'
DISCLOSURE row 513: source='Local'        member='Diaz' ... amount=10,000 status='cleared'
DISCLOSURE row 514: source='Local'        member='Diaz' ... amount=4,300  status='cleared'
SCHEDULE C [appendix_b_local]: member='Diaz' organization='BAFA' ein=454788710 amount=10,000
```
Why: the $10,000 Local row matches exactly. The $4,300 second Local designation has no Schedule C counterpart. Also note the org name truncated to the acronym in Schedule C.

**M4 — Sustainable South Bronx: absent from FY2021 disclosure entirely.** Quoted in §2 above. The single clearest falsification of the superset claim.

**M5 — Schedule C organization field is a purpose string plus a PDF page header.**
```
SCHEDULE C [appendix_b_local]: member='' organization='Funding to support operational expenses related to providing immigration services to local residents in Council District 16. Page 89 Appendix B: Local Initiatives Council Member Sponsor Legal Name of Organization' ein=113462888 amount=25,000 agency='DYCD'
```
Why: a page break inside the printed appendix. The purpose text, the page number, and the repeated column headers were all absorbed into the org field, and the member field was left empty. EIN 113462888 is disclosed FY2015–FY2020 but not FY2021. Pure Schedule C extraction damage, in the file the appendix ingest treats as clean.

**M6 — Bard College, EIN 141713034, the canonical test case.**
```
DISCLOSURE row 564: source='Discharge Planning' member=''              amount=250,000 status='cleared' agency='MOCJ'
DISCLOSURE row 565: source='Local'  member='Gennaro'       amount=8,000  status='cleared'
DISCLOSURE row 566: source='Local'  member='Levine'        amount=3,500  status='cleared'
DISCLOSURE row 567: source='Local'  member='Brooks-Powers' amount=5,000  status='cleared'
DISCLOSURE row 568: source='Local'  member='Powers'        amount=5,000  status='cleared'
SCHEDULE C [appendix_b_local]: member='Lancman'  amount=8,000  agency='MOCJ'
SCHEDULE C [appendix_b_local]: member='Levine'   amount=3,500  agency='MOCJ'
SCHEDULE C [appendix_b_local]: member='Richards' amount=5,000  agency='MOCJ'
SCHEDULE C [appendix_b_local]: member='Powers'   amount=5,000  agency='MOCJ'
```
Why: four Local designations, all four amounts identical across both sources. Two of the four member names differ, and both differences are the succession pattern (Lancman→Gennaro, Richards→Brooks-Powers). Disclosure additionally carries a $250,000 `Discharge Planning` award absent from Schedule C. **For FY2021, Bard is present in both sources** — the FY2023 gap that makes this EIN the canonical test case is not reproduced here.

**M7 — Chin $7,700: same member, same amount, different organization.**
```
DISCLOSURE row 2815: source='Local' member='Chin' legal_name='Earth Matter NY' ein=270625845 amount=7,700 status='cleared' agency='DYCD'
DISCLOSURE row 2816: source='Youth' member='Chin' legal_name='Earth Matter NY' ein=270625845 amount=5,000 status='cleared' agency='DYCD'
SCHEDULE C [appendix_b_local]: member='Chin' organization='Remember the Triangle Fire Coalition, Inc.' ein=455137219 amount=7,700 agency='DYCD'
SCHEDULE C [appendix_c_youth]: member='Chin' organization='Earth Matter NY -Heritage Farm Beds'      ein=270625845 amount=5,000
```
Why: the Youth row agrees perfectly. The Local row assigns the same member and same $7,700 to a *different named organization with a different EIN* on each side. Triangle Fire Coalition (455137219) is disclosed in FY2022–FY2023 but not FY2021. AMBIGUOUS: either the Council funded both and disclosure dropped one, or a Schedule C row is shifted. Cannot be resolved from these files.

**M8 — Bay Ridge Community Council: in Schedule C, disclosed in three other years, absent from FY2021.**
```
SCHEDULE C [appendix_b_local]: member='Brannan' organization='Bay Ridge Community Council' ein=112602994 amount=5,000 agency='DYCD'
DISCLOSURE FY2021: (no rows)
```
EIN 112602994 disclosed in FY2014, FY2015 and FY2020. A second instance of the M4 pattern.

**M9 — White Plains Road DMA: EIN in no disclosure year.**
```
SCHEDULE C [appendix_b_local]: member='Gjonaj' organization='White Plains Road District Management Association' ein=133776486 amount=11,000 agency='DYCD'
DISCLOSURE any year: (no rows for 133776486; no org at token-overlap >= 0.6 in FY2021)
```
Why: one of the 8. Undetermined whether the EIN is misread or the org is genuinely undisclosed.

**M10 — AIMHigh: King → Riley.**
```
DISCLOSURE row 151: source='Local' member='Riley' legal_name='AIMHigh Empowerment Institute, Inc.' ein=813143733 amount=22,000 status='cleared' agency='DYCD'
SCHEDULE C [appendix_b_local]: member='King' organization='AIMHigh Empowerment Institute, Inc.' ein=813143733 amount=22,000 agency='DYCD'
```
Why: identical EIN, amount, org, agency. Member alone differs. Textbook succession relabel.

**M11 — Arab American Association: Menchaca → Aviles, across three files.**
```
DISCLOSURE row 313: source='DoVE Initiative' member='Aviles' ein=113604756 amount=25,000 status='cleared' agency='MOCJ'
DISCLOSURE row 316: source='Local'           member='Aviles' ein=113604756 amount=25,000 status='cleared' agency='MOCJ'
DISCLOSURE row 318: source='Youth'           member='Aviles' ein=113604756 amount=15,000 status='cleared' agency='DYCD'
SCHEDULE C [appendix_b_local]: member='Menchaca' amount=25,000 agency='MOCJ'
SCHEDULE C [appendix_c_youth]: member='Menchaca' organization='Arab American Association of New York, Inc. -Youth Program' amount=15,000
```
Why: the same relabel, holding across both the Local and Youth appendices. Note the disclosure carries 12 rows for this EIN against Schedule C's 7 — four initiative-level awards (`Communities of Color Nonprofit Stabilization Fund` $22,500, `Cultural Immigrant Initiative` $40,000 and $10,000, `Initiative to Combat Sexual Assault` $60,000) are absent from `awards.csv`, which is the §3 incompleteness showing up on a single org.

**M12 — Belmont DMA: Torres → Feliz.**
```
DISCLOSURE row 631: source='Local' member='Feliz' legal_name='Belmont District Management Association, Inc.' ein=270834463 amount=50,000 status='cleared' agency='SBS'
SCHEDULE C [appendix_b_local]: member='Torres' organization='Belmont District Management Association, Inc.' ein=270834463 amount=50,000 agency='SBS'
```
Why: identical but for the member. Fifth succession pair.

### Why the mismatches differ — summary

| Cause | Direction | Roughly |
|---|---|---|
| `awards.csv` missing initiative provider lists | disclosure only | ~2,893 rows, $141.4M |
| Seat succession relabeling | member field disagrees | 5 seats, ~532 exact-match losses |
| Genuine FY2021 disclosure omissions | Schedule C only | 66 EINs |
| Schedule C EIN misreads | Schedule C only | ≤ 8 EINs, 1 confirmed (M1) |
| Schedule C PDF damage (org = prose, page headers, sponsor bleed) | Schedule C only | M1, M4, M5 + 8 artifact initiative labels |
| Disclosure splitting one designation into several rows | disclosure only | +41 appendix rows, $0 |
| Initiative naming drift | vocabulary | 51 disclosure / 34 Schedule C values unmatched |

---

## 7. What this means for FY2021 being "believed good"

FY2021 Schedule C extraction is good **in the appendices** and materially incomplete **in the body**.

The appendices are excellent: all three reconcile to the dollar against an independently published source, and their row counts are within 41 of disclosure's. That is the strongest external validation the Schedule C corpus has received.

`awards.csv` is not. Beyond the $141M and 2,893-row shortfall, the file carries visible extraction damage in a year presumed clean:

- **442 of 1,810 rows have a blank `initiative`** and fall back to the budget category.
- **Eight `initiative` values are not initiatives.** Six are an organization name with a mangled EIN appended (`'La Casa de Salud, Inc. 20-693325'` 41 rows/$1,349,375; `'Transgender Legal Defense and Education Fund, Inc. 43-762842'` 12/$278,787; `'Amudim Community Resources, Inc. 47-984801'` 11/$1,530,000; `'Getting Out and Staying Out 61-711370'` 10/$1,435,650; `'SAFE Foundation, Inc. 26-102131'` 6/$1,317,500; `'Sunnyside Community Services, Inc. 51-189327'` 1/$137,700). One is a sentence fragment (`'the capacity and technical skills of the providers within this initiative. This initiative provides'`, 6 rows/$236,620). One is an agency list prepended to a real initiative name.
- **At least one `organization` value is a purpose string plus a page header** (M5).

None of this is caused by the appendix ingest and none of it is fixed by it. It is stated here because "FY2021 extraction is believed good" is true of the appendices and should not be extended to `awards.csv` without qualification.

---

## 8. Ambiguity left standing

Not resolved, and deliberately not papered over:

1. **7 of the 8 no-disclosure-year EINs.** Whether the EIN is misread or the organization is genuinely undisclosed is undetermined. Settling it needs IRS BMF or Charities Bureau, which is outside this run.
2. **M2, Asiyah Women's Center.** Two real EINs, each disclosed in different years, same org, same $7,500 Perkins designation. Neither source is self-evidently right.
3. **M7, Chin $7,700.** Same member and amount attached to two different organizations. Could be a dropped disclosure row or a shifted Schedule C row.
4. **Which source is authoritative for the sponsoring member.** Schedule C reflects adoption; disclosure reflects 2023-06-23. Both are correct about different moments. Downstream consumers need to choose deliberately, and neither file says which is intended. This is a judgment call I did not make.
5. **The 51 unmatched disclosure Source values.** Inferred to be Schedule C body extraction gaps; not confirmed against the source PDF.
6. **`D. Diaz`.** 40 of 88 rows match nothing in Schedule C. Inferred to be post-adoption designations for a seat with none at adoption. Not confirmed.

---

## 9. Bearing on issue #51

Two findings, one of which contradicts the premise.

**The disclosure workbook does not disambiguate colliding surnames.** It publishes bare surnames exactly as Schedule C does. Williams and Sanchez — the two names the issue leads with — do not appear in FY2021 at all, so this year cannot even test them. The only disambiguation anywhere in the FY2021 file is a single initial in `D. Diaz`. If the plan was to resolve member identity by joining to disclosure, that plan does not work.

**And the member field is actively unsafe to join on.** The two sources disagree about the sponsor for five seats — 315 Schedule C rows across King, Lancman, Menchaca, Richards and Torres — because Schedule C is frozen at adoption and the disclosure workbook is a 2023-06-23 snapshot that rewrites sponsors as seats turn over. Adding `member` to an exact-match key costs 532 matches. A member-name join across these two sources will silently mis-attribute money, and it will do so most for the districts that changed hands, which are disproportionately the districts where attribution matters.

What FY2021 does support: **EIN plus amount is a workable join key** (5,840 matched pairs), provided the city-agency placeholder EIN 136400434 is excluded, since it carries 61 distinct organization names under one number.
