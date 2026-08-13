---
title: "Reconciliation impact of recovering the absorbed Schedule C awards"
created: 2026-08-12
type: research-finding
status: complete
tags: [nyc-budget, schedule-c, data-quality, reconciliation]
---

# Reconciliation impact of recovering the absorbed Schedule C awards

**Report generated** 2026-08-12
**Data current as of** 2026-08-12 (branch `research/missing-absorbed-awards`, worktree `~/Code/NYCB-missing`, HEAD `2c8168f`)
**Scope** Question 3 of the absorbed-award investigation: what happens to reconciliation if the
absorbed awards are added?

Every figure below is reproduced by
`python3 research/missing-absorbed-awards/measure_reconciliation.py`
(self-check: `--selfcheck`; per-year detail: `--detail fy17`). Read-only; it writes nothing.

---

## Bottom line

**Adding the absorbed awards moves the award sums TOWARD the printed totals, and in 32 cases
lands on them exactly. It does not overshoot.** The three apparent overshoots are all traceable to
a *different* parser defect, and one of them is a $12 rounding residue in the Council's own
document that actually confirms the recovery.

The strongest single result is a null test. Across FY2016–FY2019 there are **87 initiatives that
both (a) join to a printed initiative amount and (b) carry at least one absorbed award. In 32 of
them, adding the absorbed awards closes the gap to exactly $0.** Shuffling the same absorbed
totals across the same 87 initiatives 20,000 times produces a mean of **0.77** exact closures and
never once reaches 32 (`P(null ≥ 32) < 0.00005`). These are not coincidences — the closures include
sums as specific as **$6,206,332** (FY2017 Discretionary Child Care) and **$6,318,149** (FY2018
Discretionary Child Care).

One correction to the question's premise, established below and important: **the printed *category*
total is not a reconciliation target for award rows and cannot be made into one.** The printed
*initiative* amount is. That is where the measurement has to happen.

| Claim | Status |
|---|---|
| A gap exists between award-row sums and printed totals | **VERIFIED** — at both levels |
| The category-level gap is a usable target | **REFUTED** — 27%–64% coverage is by design, and the category labels are shifted |
| The initiative-level gap is a usable target | **VERIFIED** — 24%–77% of joined initiatives already balance to the dollar with no repair |
| Adding absorbed awards closes initiative-level gaps | **VERIFIED** — 32 exact closures, 2 near closures (≤$1,000 residual) |
| Adding absorbed awards overshoots | **REFUTED** — 3 apparent cases, all explained; see §5 |
| A recovered award could already be in the corpus | **VERIFIED as near-zero** — 2 of 442 candidate pairs; see §6 |

---

## 1. Method

**Absorbed award.** An `(EIN, $amount)` pair sitting *inside* an `organization` string — the
`org_merged` advisory. Extracted with `(\d{2}-?\d{7})\s*\*?\s*\$([\d,]+(?:\.\d{2})?)`, which
accepts the asterisk and the hyphen-less appendix EIN form, and rejects the FY2024–FY2026 prose
false positives (`"…farm shares to $12 per share…"` yields no pair).

**Yield.** 303 rows carry the advisory. **297 of them yield 442 embedded pairs.** Six yield none:

| Row | Why no pair |
|---|---|
| `fy18…awards.csv` L442, `fy20…awards.csv` L2665 | `Urban Health Plan, Inc. 15-24042810 $88,855` — a 10-digit EIN run. Mangled, not recoverable by pattern. |
| `fy19…awards.csv` L632 | `East Flatbush Village, Inc. 80-0612019 Meyer Levin High School $18,000 …` — a **program name** sits between the EIN and the amount. **Three** real absorbed awards ($18,000 each, $54,000) sit in this one row and the extractor **misses** all three; the recovery is therefore an under-count, not an over-count. |
| `fy24`, `fy25`, `fy26` (1 row each) | Purpose prose containing a `$`. No absorbed award. False positives of the advisory. |

Pairs by file:

| File | pairs | $ |
|---|---:|---:|
| `fy16_schedule_c_awards.csv` | 26 | 11,059,565 |
| `fy17_schedule_c_awards.csv` | 207 | 27,880,502 |
| `fy18_schedule_c_awards.csv` | 129 | 22,914,829 |
| `fy18_appendix_a_aging.csv` | 40 | 433,625 |
| `fy19_schedule_c_awards.csv` | 40 | 4,203,700 |
| **total** | **442** | **66,492,221** |

**Cross-check against the sibling inventory.** `research/missing-absorbed-awards/absorbed_award_candidates.csv`
(commit `fe485dd`, produced independently by the inventory pass) holds **445** triples totalling
**$66,546,221**. This pass's 442 are a **strict subset** — the only difference is the three
$18,000 awards in `fy19` L632 named above. No triple in this pass is absent from theirs, and no
figure in this report contradicts it. Extending the extractor to catch the L632 shape would add
$54,000 to FY2019 and change none of the conclusions below.

**Repeats are real.** Six triples appear twice or three times *within one organization string*
(FY2017 L27: `Dromm PowerMyLearning $20,000`, `Eugene PowerMyLearning $20,000`,
`Ferreras-Copeland PowerMyLearning $20,000`). Different council members funding the same
organization for the same amount is an ordinary Schedule C pattern, so occurrences are counted, not
deduplicated. This is the same reason `(EIN, amount)` can match an award but cannot prove it unique.

**Attribution.** Each absorbed award is credited to the initiative of the row that swallowed it —
which is the initiative the PDF printed it under, since absorption happens within a single
provider table.

**Join.** Exact, on a normalized initiative name (case, punctuation, and the curly-vs-straight
apostrophe folded out; `Alternatives to Incarceration (ATI’s)` ≡ `(ATI's)`). Prefix or fuzzy
joining was **rejected**: FY2018 alone has six `Crisis Management System – <sub-programme>` award
labels whose parent is one initiative line, and a prefix join would silently pool them into a
fake balance. The exact join covers 52–82 initiatives per year.

---

## 2. Category level — measured, and it is the wrong instrument

Sum of award rows in each category vs the printed category TOTAL in
`*_schedule_c_reconciliation.txt`. Aggregated across all categories (which is immune to the label
problem in §7):

| FY | printed | award rows | gap | absorbed | gap after | coverage now | coverage after |
|---|---:|---:|---:|---:|---:|---:|---:|
| FY2015 | 233,438,000 | 73,199,837 | 160,238,163 | 0 | 160,238,163 | 31.4% | 31.4% |
| FY2016 | 333,886,574 | 89,917,012 | 243,969,562 | 11,059,565 | 232,909,997 | 26.9% | 30.2% |
| FY2017 | 279,908,300 | 89,901,487 | 190,006,813 | 27,880,502 | 162,126,311 | 32.1% | 42.1% |
| FY2018 | 302,086,000 | 102,716,956 | 199,369,044 | 22,914,829 | 176,454,215 | 34.0% | 41.6% |
| FY2019 | 338,301,000 | 181,026,931 | 157,274,069 | 4,203,700 | 153,070,369 | 53.5% | 54.8% |
| FY2020 | 404,372,774 | 258,762,385 | 145,610,389 | 0 | 145,610,389 | 64.0% | 64.0% |
| FY2021 | 304,268,931 | 202,070,188 | 102,198,743 | 0 | 102,198,743 | 66.4% | 66.4% |
| FY2027 | 655,764,999 | 605,111,412 | 50,653,587 | 0 | 50,653,587 | 92.3% | 92.3% |

**There is an enormous gap and the absorbed awards barely dent it** — FY2017 moves 32.1% → 42.1%,
the largest shift in the corpus; FY2019 moves 1.3 points.

**That gap is not a defect.** Most initiatives are lump appropriations to an agency with **no
per-grantee table in the PDF at all** (FY2017 `GOVERNMENT OFFICIALS` $18,265,000, `PARKS AND
RECREATION SERVICES` $21,440,585, `SPEAKER'S INITIATIVE` $30,075,000 — zero award rows each,
because the document prints none). Award rows can never sum to the category total. Coverage rising
monotonically from 27% (FY2016) to 92% (FY2027) tracks the Council itemizing more of the budget
over time, not the parser getting better.

The per-category breakdown makes the point unmistakable. FY2017:

| category (name as printed in the reconciliation) | printed | award rows | gap | absorbed | after |
|---|---:|---:|---:|---:|---:|
| INTRODUCTION | 2,800,000 | 0 | 2,800,000 | 0 | 2,800,000 |
| BOROUGHWIDE NEEDS | 15,147,069 | 0 | 15,147,069 | 0 | 15,147,069 |
| CHILDREN'S SERVICES | 11,140,000 | 4,042,737 | 7,097,263 | 7,104,332 | **−7,069** |
| EDUCATION | 5,655,000 | 17,784,500 | **−12,129,500** | 1,425,000 | −13,554,500 |
| SENIOR SERVICES | 3,392,000 | 9,000,634 | **−5,608,634** | 4,374,517 | −9,983,151 |
| YOUTH SERVICES | **0** | 15,383,600 | −15,383,600 | 1,491,400 | −16,875,000 |
| GOVERNMENT OFFICIALS | 18,265,000 | 0 | 18,265,000 | 0 | 18,265,000 |
| *(all 27 categories)* | 279,908,300 | 89,901,487 | 190,006,813 | 27,880,502 | 162,126,311 |

`YOUTH SERVICES` has a printed total of $0 against $15.4M of award rows. That is not a data error
in the dollars; it is the **category-label shift** documented in §7 — the award rows and the
printed totals are labeled from two different mechanisms that disagree by one position. Per-category
figures are therefore **not interpretable** until that shift is repaired, and even once repaired
they would not be a reconciliation target for the reason above.

**Answer to the question as posed: at the category level the gap is real but structural, adding
the absorbed awards leaves it essentially unchanged, and neither fact bears on the diagnosis.**

---

## 3. Initiative level — this is the real reconciliation target

Where the PDF itemizes an initiative at all, the itemization is **exhaustive**: the provider list
sums to the initiative's printed amount. That claim is testable without touching the absorbed
awards, and it holds.

| FY | joined initiatives | already balance exactly | % | short | over |
|---|---:|---:|---:|---:|---:|
| FY2015 | 54 | 47 | 87% | 7 | 0 |
| FY2016 | 65 | 50 | 77% | 15 | 0 |
| FY2017 | 62 | 15 | **24%** | 46 | 1 |
| FY2018 | 52 | 23 | 44% | 29 | 0 |
| FY2019 | 78 | 33 | 42% | 39 | 6 |
| FY2020 | 82 | 41 | 50% | 39 | 2 |
| FY2021 | 74 | 43 | 58% | 30 | 1 |
| FY2024 | 102 | 61 | 60% | 39 | 2 |
| FY2027 | 152 | 113 | 74% | 34 | 5 |

Hundreds of initiatives across the corpus balance **to the dollar** with no repair at all. That is
the pass/fail signal DATA-ANOMALIES.md §20 says the award stream has never had. It exists; nothing
was reading it.

**FY2017 — the year with 118 absorbed rows — is the worst year in the corpus at 24%.** That is the
first piece of corroboration.

Aggregate gap on joined initiatives, before and after recovery:

| FY | printed | award rows | gap | absorbed (in joined inits) | gap after | newly balanced | newly over |
|---|---:|---:|---:|---:|---:|---:|---:|
| FY2016 | 86,474,645 | 73,550,272 | 12,924,373 | 9,503,585 | 3,420,788 | **5** | 1 |
| FY2017 | 137,820,597 | 84,169,476 | 53,651,121 | 22,996,522 | 30,654,599 | **13** | 0 |
| FY2018 | 109,707,645 | 76,182,556 | 33,525,089 | 16,268,804 | 17,256,285 | **8** | 1 |
| FY2019 | 179,903,641 | 158,781,023 | 21,122,618 | 3,573,279 | 17,549,339 | **6** | 1 |
| FY2020 | 214,474,020 | 174,711,180 | 39,762,840 | 0 | 39,762,840 | 0 | 0 |

Every year moves in the right direction. FY2020, which has one unrecoverable absorbed row, moves
not at all — the control case behaves as a control case should.

Across FY2016–FY2019, initiatives that were **short** carry a combined shortfall of
**$137,047,497**, of which the absorbed awards sitting inside them account for **$51,913,560
(37.9%)**. The recovery is a large partial repair, not a complete one; §8 names what is left.

---

## 4. The 32 exact closures

Gap → exactly $0 after adding the absorbed awards. Column `rows+abs` is the visible award rows plus
the recovered ones.

| FY | initiative | printed | award rows now | absorbed | rows+abs |
|---|---|---:|---:|---:|---:|
| FY2016 | Jobs to Build On | 5,636,000 | 281,800 | 5,354,200 | 1+1 |
| FY2016 | Worker Cooperative Business Development Initiative | 2,100,000 | 1,095,000 | 1,005,000 | 10+5 |
| FY2016 | Obesity Prevention | 1,300,000 | 550,000 | 750,000 | 2+1 |
| FY2016 | Elder Abuse Enhancement | 335,000 | 285,000 | 50,000 | 4+1 |
| FY2016 | Day Laborer Workforce Initiative | 500,000 | 485,000 | 15,000 | 4+1 |
| FY2017 | **Discretionary Child Care** | 9,355,069 | 3,148,737 | **6,206,332** | 5+6 |
| FY2017 | LGBTQ Senior Services in Every Borough | 1,500,000 | 300,000 | 1,200,000 | 1+1 |
| FY2017 | COMPASS | 8,000,000 | 7,116,400 | 883,600 | 4+5 |
| FY2017 | Access to Food and Nutritional Education | 930,000 | 250,000 | 680,000 | 2+4 |
| FY2017 | Educational Programs for Students | 2,975,000 | 2,300,000 | 675,000 | 2+2 |
| FY2017 | Support for Educators | 12,744,500 | 12,294,500 | 450,000 | 1+1 |
| FY2017 | YouthBuild Project Initiative | 2,100,000 | 1,742,200 | 357,800 | 4+2 |
| FY2017 | Child Health and Wellness | 646,000 | 300,000 | 346,000 | 1+2 |
| FY2017 | Cancer Services | 790,500 | 540,500 | 250,000 | 6+4 |
| FY2017 | Day Laborer Workforce Initiative | 570,000 | 350,000 | 220,000 | 4+2 |
| FY2017 | Legal Services for Veterans | 350,000 | 150,000 | 200,000 | 1+1 |
| FY2017 | Information and Referral Services | 407,811 | 351,679 | 56,132 | 2+1 |
| FY2017 | Children and Families in NYC Homeless System | 1,000,000 | 977,000 | 23,000 | 5+1 |
| FY2018 | **Discretionary Child Care** | 9,855,190 | 3,537,041 | **6,318,149** | 5+7 |
| FY2018 | Children Under Five | 1,002,000 | 576,923 | 425,077 | 3+1 |
| FY2018 | Cancer Services | 790,500 | 640,500 | 150,000 | 8+2 |
| FY2018 | Veterans Community Development | 515,000 | 395,000 | 120,000 | 6+2 |
| FY2018 | Supportive Alternatives to Violent Encounters (SAVE) | 1,950,000 | 1,850,000 | 100,000 | 4+1 |
| FY2018 | Access to Healthy Food and Nutritional Education | 930,000 | 835,000 | 95,000 | 5+1 |
| FY2018 | Dedicated Contraceptive Fund | 400,000 | 337,000 | 63,000 | 3+1 |
| FY2018 | Naturally Occurring Retirement Communities (NORCs) | 3,850,000 | 3,805,000 | 45,000 | 12+1 |
| FY2019 | COMPASS | 1,813,600 | 1,319,200 | 494,400 | 5+3 |
| FY2019 | Support for Educators | 20,804,500 | 20,354,500 | 450,000 | 1+1 |
| FY2019 | Immigrant Health Initiative | 2,000,000 | 1,835,000 | 165,000 | 19+2 |
| FY2019 | Construction Site Safety Training | 1,100,000 | 975,000 | 125,000 | 8+1 |
| FY2019 | LGBTQ Inclusive Curriculum | 600,000 | 500,000 | 100,000 | 7+1 |
| FY2019 | Support for Victims of Human Trafficking | 1,200,000 | 1,140,000 | 60,000 | 9+1 |

Worked example — **FY2017 Discretionary Child Care**, printed **$9,355,069**:

```
L2  row ein=112290419 $  960,000 | absorbed 47-2375867 $2,000,000
L3  row ein=131860451 $  273,875 | absorbed 13-2732818 $709,605, 11-2347180 $1,448,669,
                                            11-2300840 $587,058, 11-2302049 $1,136,000
L4  row ein=203108162 $  481,076 | —
L5  row ein=131992185 $  275,000 | absorbed 13-5623279 $325,000
L6  row ein=132686694 $1,158,786 | —
                       5 rows + 6 absorbed = 11 awards = $9,355,069   diff $0
```

Two near closures sit just outside the exact set and are worth naming because they are the same
phenomenon with a rounding tail: **FY2017 New York Immigrant Family Unity Project** (gap
$2,076,668, absorbed $2,076,667, residual **$1**) and **FY2018 Support for Educators**
(residual **$500**). NYIFUP is a rounding residue in the source: the Council split $6,230,000 three
ways at $2,076,666.67 each and printed 2,076,666 (Brooklyn Defender Services) + 2,076,666 (Legal Aid
Society) + 2,076,667 (Bronx Defenders, the absorbed one) = **$6,229,999**. The recovery reproduces
the document exactly; the document is $1 short of its own total.

### The null test

87 joined initiatives carry at least one absorbed award. Shuffling the absorbed totals across those
same 87 initiatives, 20,000 draws, `random.seed(7)`:

```
observed exact closures                     : 32
mean exact closures under the null          : 0.77
maximum in any of 20,000 null draws         : 6
P(null >= 32)                               : < 0.00005
```

The absorbed amounts are matched to their initiatives by the document's own structure, not by
anything the recovery chose. **This independently confirms both the diagnosis and the recovery
method.**

---

## 5. Overshoot audit — all three explained, none a double count

Three initiatives go from a non-negative gap to a negative one. Each was opened.

**FY2016 Community Consultant Contracts (CCC) — residual −$12. Confirms the recovery.**
30 visible rows + 7 absorbed = **37 awards**, all $29,730 except two at $29,731, summing to
$1,100,012 against a printed $1,100,000. `1,100,000 ÷ 37 = 29,729.7297…`. The Council split the
initiative 37 ways evenly and printed rounded per-award figures whose sum exceeds the appropriation
by $12. The recovery produces **exactly the award count an even 37-way split requires**. The $12 is
a rounding residue in the source document, not in the recovery.

**FY2018 Viral Hepatitis Prevention — residual −$396,978. A different parser defect.**
Four award rows (L126–L129, $401,904 — Queens Comprehensive Perinatal Council, SCO Family of
Services, Urban Health Plan, William F. Ryan) carry the `Viral Hepatitis Prevention` label but are
the **Q–W tail of the alphabetical Maternal Health Services list** that runs L118–L123 (B–J). The
parser read the intervening initiative headers mid-list and mis-assigned the tail. Reattaching them:

```
Maternal Health Services   (printed 1,192,818): 769,245 rows + 396,859 absorbed = 1,166,104  short   26,714
Viral Hepatitis Prevention (printed 1,423,658): 1,014,978 rows + 368,270 absorbed = 1,383,248  short  40,410
```

Both short. **No overshoot.** The $40,410 residual is itself exactly one award amount recurring in
that list.

**FY2019 HIV/AIDS Faith Based — residual −$36,019. Same defect, larger.**
The 13-row block L311–L323 labeled `HIV/AIDS Faith-Based` names the *Maternal and Child Health
Services* grantees (BronxWorks, Brooklyn Perinatal Network, Caribbean Women's Health Association,
Community Health Center of Richmond, Joseph P. Addabbo, SCO Family of Services, Urban Health Plan,
William F. Ryan). FY2019 has **zero** award rows labeled `Maternal and Child Health Services`
($1,692,818 printed). Against the correct initiative the block is **$525,799 short**, not $36,019
over.

Four further initiatives were **already** over-counted before any recovery — the same label defect,
caught by the same test:

| FY | label carried | printed under that label | award rows | actual initiative |
|---|---|---:|---:|---|
| FY2017 | Homeless Prevention Services for Veterans | 300,000 | 350,000 | L338 (Project Renewal, $300,000) is the whole initiative; L337 belongs to the previous one |
| FY2019 | **Child Health and Wellness** | 646,000 | 6,175,370 (67 rows) | the block names the **Ending the Epidemic** grantees ($6,945,000 printed, **zero** rows of its own); 6,175,370 + 308,630 absorbed = **6,484,000, short $461,000** |
| FY2019 | Communities of Color Nonprofit Stabilization Fund | 3,700,000 | 7,380,000 | label carryover |
| FY2019 | Borough Presidents' Discretionary Funding Restoration | 1,129,774 | 2,732,000 | label carryover |

**Every overshoot in the corpus is an initiative-label misassignment, not a double count.** This is
a second, independent parser defect that the initiative-level reconciliation surfaces for free —
see §8.

---

## 6. Double-count risk — near zero, and quantified

*Could a recovered award already be present under a slightly different amount or EIN formatting?*
Measured against every award-bearing file in the same fiscal year, with EINs normalized to digits:

| FY | absorbed pairs | exact `(EIN, amount)` already a row | $ at risk | same EIN, different amount |
|---|---:|---:|---:|---:|
| FY2016 | 26 | 0 | 0 | 2 |
| FY2017 | 207 | 0 | 0 | 4 |
| FY2018 | 169 | 2 | 43,500 | 4 |
| FY2019 | 40 | 0 | 0 | 6 |
| **total** | **442** | **2 (0.45%)** | **43,500** | **16** |

The two collisions are `fy18_schedule_c_awards.csv` L364 (EIN 260149521, $40,000) and
`fy18_appendix_a_aging.csv` L402 (EIN 371469320, $3,500). Both need a per-row decision before the
recovery applies — a same-org/same-amount pair can legitimately be two awards from two council
members, which is why `(EIN, amount)` is the right key and `EIN` alone is not.

The 16 same-EIN/different-amount cases are **not** a risk: a different amount is a different award,
and the fiscal-sponsor problem (13-2612524 carrying 229 names) is precisely why the key includes the
amount.

Three structural facts make double counting unlikely by construction:

1. The absorbed text sits **inside** an org string, i.e. in a position no parser ever emitted as a
   row. There is no path by which the same PDF text produced both.
2. Absorption is what *replaces* a row — the defect is the row's absence, so its presence would be
   the anomaly.
3. The initiative-level sums **already balance** for 24%–77% of initiatives. If absorbed awards were
   duplicates, adding them would break balanced initiatives. It breaks none: all 32 movements from
   the short side land on or before zero.

---

## 7. Adjacent finding — the category labels are shifted, corpus-wide

Surfaced while attempting the category-level comparison; **not** part of the absorbed-award defect,
but it invalidates any category-keyed join and is not in DATA-ANOMALIES.md.

`parse_schedule_c.py` labels the summary blocks **positionally** (`cat = cats[bi]`), so any ToC
category with no summary block shifts every label after it. Award rows, by contrast, take their
category from a **heading line matched against the ToC** — a direct text match. The two disagree:

| FY | initiatives whose award-category equals initiatives-category | award-category is exactly one position later | other |
|---|---:|---:|---:|
| FY2016 | 1 | **64** | 0 |
| FY2017 | 0 | 14 | 48 |
| FY2018 | 0 | 8 | 44 |
| FY2019 | 0 | **78** | 0 |
| FY2020 | 14 | 68 | 0 |
| FY2021 | 23 | 47 | 4 |

The parser already knows: every affected year's reconciliation header prints
`categories from ToC: 27 | summary blocks found: 25  <-- MISMATCH`. FY2017 and FY2018 show "other"
rather than a clean +1 because two blocks are missing, so the drift compounds.

**Reconciliation still passes**, because it compares a block's row-sum against that same block's
printed TOTAL; only the *name* is wrong. But the `category` column in every
`*_schedule_c_initiatives.csv` and in the reconciliation report is off by at least one position in
FY2016–FY2021 — which is why FY2017 `YOUTH SERVICES` shows a printed total of $0 against $15.4M of
award rows.

---

## 8. What this does not establish

- **Recovery is partial.** Even after adding every absorbed award, FY2016–FY2019 joined initiatives
  remain **$68.9M short** in aggregate. Three separate causes are now visible and only the first is
  the subject of this investigation: absorbed awards; the initiative-label misassignment of §5/§7;
  and awards the PDF text layer never yielded at all (FY2017 Job Training and Placement Initiative
  shows 3 rows against $8,106,000 printed — a whole provider table is simply missing, and no
  absorbed award is present to recover it).
- **The 55 FY2016 rows whose `(EIN, amount)` has no disclosure counterpart are not adjudicated
  here.** FY2016 nonetheless shows 5 exact closures, which is evidence the absorbed dollars are
  right even where the disclosure workbook does not corroborate them. Whether those 55 should be
  applied is a separate decision.
- **Appendix A recovery has no reconciliation target.** The 40 absorbed pairs ($433,625) in
  `fy18_appendix_a_aging.csv` cannot be tested this way: the reconciliation reports appendices as a
  bare tally (`appendix A (aging): 422 rows $4,419,275`) with no printed total beside them.
  **Unknown**, and it should be labeled that way rather than assumed to behave like the body.
- **The extraction under-counts by three awards.** `fy19` L632 hides three $18,000 awards behind a
  program name sitting between the EIN and the amount — the same pattern failure that caused the
  original defect. The sibling inventory catches them; this pass does not. Any recovery that ships
  should handle that shape.
- **The exact-name initiative join covers 52–82 of 71–101 award labels per year.** Absorbed awards
  under an unjoined label are excluded from §3/§4 entirely (which is why the joined-initiative
  absorbed total is $52.3M against the $66.5M extracted). Those are neither confirmed nor refuted.
- **Two rows need a human decision** before any recovery applies (§6).

---

## 9. Recommendation

The evidence supports the recovery. It also supports something the plan did not ask for:
**reconcile the award stream at the initiative level, and ship that as a permanent check.** It is a
better artifact than the recovery itself — it would have caught this defect in FY2017 (24% balanced
against a 44–77% norm), it caught two more defects in the course of one afternoon, and it costs one
join against data already in the repo.

Sequence:

1. Land the initiative-level reconciliation in `validate_data.py` / the per-year reconciliation
   report, as an advisory with a per-initiative balanced/short/over tally.
2. Fix the category-label shift (§7) — it is a labeling bug in a positional map, and it is
   independent of everything else here.
3. Fix the initiative-label misassignment (§5) — larger, and it must land **before** the recovery,
   or the recovery's own reconciliation check will report false overshoots.
4. Apply the absorbed-award recovery, writing every substitution to an auditable crosswalk in the
   pattern of `code/recover_org_names.py`, keyed on `(EIN, amount)`, with the two collisions in §6
   held out for a human.

---

## Reproduce

```bash
cd ~/Code/NYCB-missing                      # branch research/missing-absorbed-awards
python3 research/missing-absorbed-awards/measure_reconciliation.py --selfcheck
python3 research/missing-absorbed-awards/measure_reconciliation.py
python3 research/missing-absorbed-awards/measure_reconciliation.py --detail fy17
```
