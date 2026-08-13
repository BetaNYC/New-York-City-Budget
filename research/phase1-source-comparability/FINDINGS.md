---
title: "Phase 1 findings — are the Council's expense disclosure workbooks and this repo's parsed Schedule C the same universe?"
created: 2026-08-12
type: research-finding
status: draft
tags: [type/research, domain/software-engineer, project/nyc-budget]
---

# Phase 1 — source comparability

**Report generated:** 2026-08-12
**Data current as of:** 2026-08-12 (repo `research/phase1-source-comparability` @ `efb20f2`; disclosure
workbooks retrieved 2026-07-15, re-verified byte-identical 2026-08-11)
**Reproducer:** `python3 research/phase1-source-comparability/findings_corpus.py`
(stdlib only, reads only, asserts its own headline claims in `demo()`)

Per-year deep reads live alongside this file as `comparison-2016.md` … `comparison-2027.md`
(FY2016–FY2021, FY2024, FY2027). This document is the corpus-wide synthesis: it puts all
**thirteen** years on the same axes, including the four years no per-year report covered
(FY2022, FY2023, FY2025, FY2026), and it reaches a conclusion none of the per-year reports could.

---

## 1. Verdict

> **(a) Same universe, better captured.**
>
> Qualified twice, and both qualifications matter:
>
> 1. **The disclosure is not a *strict* superset.** In 12 of 13 years a small residue of Schedule C
>    rows has no disclosure counterpart — but it is **0.07%–3.07% of extracted dollars**, and in
>    FY2027 it is exactly **zero**. Option (b) fails, narrowly and measurably.
> 2. **The two sources are snapshots of different moments, on different Council rosters.** Schedule C
>    is frozen at adoption; the workbook is re-published years later with the *current* occupant of
>    each seat. For FY2022 that is a near-total roster swap. Same awards, different sponsor labels.
>
> **Option (c), "different universes," is firmly rejected.** Nothing in thirteen years of testing
> supports it.

The evidence for (a) is not one number. It is four independent measurements that agree, one of
which involves no external document at all.

---

## 2. The capture-rate call: **NEEDS REVISION** — and one specific number must be retracted

The parent plan
(`team/engineering/plans/2026-08-11-schedule-c-award-coverage-remediation.md`, "Evidence" table)
carries this, flagged as unverified:

| FY | disclosure rows | extracted rows | captured | disclosure $ | extracted $ |
|---|---:|---:|---:|---:|---:|
| 2016 | 7,797 | 335 | 4.3% | **$208,529,347** | $89,917,012 |
| 2017 | **8,674** | 364 | 4.2% | $353,501,886 | $89,901,487 |
| 2018 | 8,894 | **480** | **5.4%** | $381,900,000 | $102,716,956 |
| 2019 | 9,655 | 846 | 8.8% | $392,945,000 | $181,026,931 |
| 2020 | 10,616 | 2,841 | 26.8% | $457,216,702 | $258,762,385 |

**The row percentages are arithmetically correct and reproduce.** Three things are wrong with the
rest, in ascending order of consequence.

### 2a. RETRACT: the FY2016 disclosure dollar figure

`$208,529,347` is wrong. The FY2016 workbook totals **$381,376,626** across 7,797 rows.

```
$ python3 code/parse_expense_disclosure.py
2016      7797       381,376,626     7668      129        0  no MOCS ID#; no Fiscal Year column
```

I tried to reproduce `$208,529,347` as a slice — Cleared only ($380,361,130), Pending only
($1,015,496), excluding the per-member streams ($331,577,626), the streams alone ($49,799,000),
and every single `Source` and `Agency` value — and **no slice lands within $1,000 of it**. It is not
a defensible subset; it is a bad number. It never appeared in a per-year report because
`comparison-2016.md` derived its own figure independently and got $381,376,626 too.

Consequence: FY2016 dollar capture is **23.6%**, not the 43.1% the plan's pair implies.

### 2b. REVISE: two counts drifted, and FY2018 moved under Track B

- FY2017 disclosure rows are **8,671**, not 8,674 (the plan's number appears to be the raw sheet
  line count minus a header, without the orphan/summary rows the parser strips).
- FY2018 extracted rows are **902**, not 480, as of MCP 1.4.0 — its aging appendix (422 rows,
  $4,419,275) now loads. FY2018 row capture is **10.1%**, not 5.4%.

### 2c. RETRACT THE SCOPING — this is the consequential one

**"FY2016–FY2020" is not the broken range.** Applying the identical measurement to FY2021–FY2027 —
including the four years nobody had compared before tonight — shows the modern years are also
materially incomplete:

```
$ python3 research/phase1-source-comparability/findings_corpus.py
== CAPTURE, ROWS AND DOLLARS (pre-1.4.0 = awards CSV only; post = awards + appendix) ==
FY    disc rows   awards     +apx   pre %  post %          disc $         sched $  post $%
2015       6650      652      652    9.8%    9.8%    $286,731,856     $73,199,837    25.5%
2016       7797      335      335    4.3%    4.3%    $381,376,626     $89,917,012    23.6%
2017       8671      364      364    4.2%    4.2%    $353,501,886     $89,901,487    25.4%
2018       8894      480      902    5.4%   10.1%    $381,900,000    $107,136,231    28.1%
2019       9655      846      846    8.8%    8.8%    $392,945,000    $181,026,931    46.1%
2020      10616     2841     2841   26.8%   26.8%    $457,216,702    $258,762,385    56.6%
2021       9054     1810     6120   20.0%   67.6%    $393,250,506    $251,869,188    64.0%
2022      11336     1492     5674   13.2%   50.1%    $538,549,827    $272,355,943    50.6%
2023      11027     1848     5904   16.8%   53.5%    $541,426,995    $312,208,214    57.7%
2024      10811     5368     9279   49.7%   85.8%    $527,971,414    $450,462,574    85.3%
2025      11280     5646     9566   50.1%   84.8%    $595,181,182    $462,784,110    77.8%
2026      11757     5838     9752   49.7%   82.9%    $716,213,155    $537,081,245    75.0%
2027      10040     6118     9978   60.9%   99.4%    $705,564,000    $654,910,412    92.8%
```

**FY2022 captures 50.1% of disclosure rows and FY2023 53.5% — after the appendix load.** FY2015,
never in the plan's table at all, captures 9.8%. Publishing "4–27% for FY2016–FY2020" tells a reader
that the rest of the corpus is fine. It is not.

### The revised framing, if a percentage must be published

State two numbers per year, never one, and name what each measures:

- **row capture** — extracted rows ÷ disclosure rows. Low everywhere before FY2024.
- **dollar capture** — extracted dollars ÷ disclosure dollars. Always much higher, because the rows
  Schedule C loses are overwhelmingly the small per-member ones.

And carry the caveat that the denominator is a **later snapshot** which legitimately includes
post-adoption designations. FY2027 quantifies that: its entire 62-row / $50,653,588 gap is
post-adoption money, verified against the PDF's own prose in `comparison-2027.md`. That is 0.6% of
rows — real, bounded, and nowhere near large enough to explain FY2016's 95.7%.

---

## 3. Evidence

### 3a. Where the missing rows actually live — and it is two different failures, not one

```
$ python3 research/phase1-source-comparability/findings_corpus.py
== WHERE THE MISSING ROWS LIVE: per-member streams vs everything else ==
FY     disc Local/Youth/Aging   disc stream $  sched appendix  stream gap  disc body sched awards  body gap
2015                     4773     $50,124,600               0        4773       1877          652      1225
2016                     4467     $49,799,000               0        4467       3330          335      2995
2017                     4610     $49,798,500               0        4610       4061          364      3697
2018                     4541     $49,804,000             422        4119       4353          480      3873
2019                     4526     $49,724,000               0        4526       5129          846      4283
2020                     4440     $49,799,000               0        4440       6176         2841      3335
2021                     4351     $49,799,000            4310          41       4703         1810      2893
2022                     4249     $49,799,000            4182          67       7087         1492      5595
2023                     4145     $49,819,000            4056          89       6882         1848      5034
2024                     3979     $49,799,000            3911          68       6832         5368      1464
2025                     3964     $49,799,000            3920          44       7316         5646      1670
2026                     3966     $49,674,000            3914          52       7791         5838      1953
2027                     3860     $49,799,000            3860           0       6180         6118        62
  FY2015-FY2020 per-member stream shortfall: 26935 rows  $294,629,825
```

Two things fall out of that table, and they need separate fixes.

**Failure 1 — the per-member streams, FY2015–FY2020.** The appendix CSVs are header-only for those
years (`wc -l data/fy1[5-7]/schedule_c/*appendix*` returns `1` for each of the nine files).
**26,935 rows / $294,629,825** are missing, and they are a single, well-understood, *fixed* program.

The strongest corroboration in this report: the disclosure's own Local + Youth + Aging total is
**$49.67M–$50.12M in every one of thirteen years**, including the six where the PDF extraction
produced nothing. `DATA-ANOMALIES.md` §19 independently confirmed that flat ~$49.8M pot for
FY2021–FY2027 from the PDF side, and explicitly worried it might be an extraction artifact. An
outside document now shows the same pot existing in FY2015–FY2020 as well. Two documents,
different production paths, same fixed allocation. **The recovery target for those years is known
in advance to within ~1%** — which makes it about the most testable remediation on the whole plan.

**Failure 2 — the body award stream, nearly every year.** The `body gap` column never closes except
in FY2027. FY2022 is short 5,595 body rows and FY2023 5,034 — **worse in absolute terms than
FY2016's 2,995 or FY2020's 3,335.**

### 3b. The internal check — no disclosure involved, and it says the same thing

This one matters most, because it cannot be dismissed as a disagreement between two documents. It
compares the repo against **itself**: the `initiatives` stream (which reconciles to the PDF's own
printed category totals) against the `awards` stream extracted from the same PDF. Neither the
`initiatives` CSV nor its reconciliation names a Local / Youth / Aging line, so the two are directly
comparable (asserted in `initiatives_total()`).

```
== INTERNAL CHECK, NO DISCLOSURE INVOLVED: the repo's own two Schedule C streams ==
FY        initiatives $          awards $          residual  residual %
2015       $233,438,000       $73,199,837      $160,238,163       68.6%
2016       $333,186,574       $89,917,012      $243,269,562       73.0%
2017       $279,908,500       $89,901,487      $190,007,013       67.9%
2018       $301,986,000      $102,716,956      $199,269,044       66.0%
2019       $338,301,000      $181,026,931      $157,274,069       46.5%
2020       $404,372,774      $258,762,385      $145,610,389       36.0%
2021       $304,268,931      $202,070,188      $102,198,743       33.6%
2022       $465,014,395      $222,556,943      $242,457,452       52.1%
2023       $486,446,095      $262,419,214      $224,026,881       46.1%
2024       $471,928,500      $400,663,574       $71,264,926       15.1%
2025       $534,963,682      $412,985,110      $121,978,572       22.8%
2026       $665,080,821      $487,287,245      $177,793,576       26.7%
2027       $655,764,999      $605,111,412       $50,653,587        7.7%
```

The `initiatives` figures are trustworthy — `tail data/fy23/schedule_c/fy23_schedule_c_reconciliation.txt`
reports `26/26 categories exact`, FY2027 `25/25 categories exact`, FY2022 `24/26`, FY2026 `24/25`.

**FY2027's residual is $50,653,587. The disclosure gap for FY2027 is $50,653,588.** Those agree to a
dollar and were computed from completely different inputs; `comparison-2027.md` traced the gap to
post-adoption designations printed in the PDF's initiative headers but never as provider rows. So
7.7% is roughly the **floor** — the share of initiative money that legitimately never becomes a named
provider row.

Against that floor, a **52.1% residual in FY2022 and 46.1% in FY2023 cannot be post-adoption
activity.** (INFERRED, not verified: I have not read the FY2022 or FY2023 PDFs page by page to
partition their residual. What is VERIFIED is that the residual exists, that it is 6–7× the FY2027
floor, and that the disclosure holds named-provider rows for money of the same order —
$281,442,378 of unmatched FY2022 disclosure body rows.)

### 3c. Same-universe test: the rows Schedule C *did* capture are in the disclosure

```
== SAME-UNIVERSE TEST: do the rows Schedule C DID capture exist in disclosure? ==
FY     sched rows   (EIN,amt) matched    rate  orphan EIN  orphan rows      orphan $  orphan $ %
2015          652                 533   81.7%          17           17    $1,599,181       2.18%
2016          335                 288   86.0%           8            8    $2,756,728       3.07%
2017          364                 328   90.1%           5            5    $1,490,333       1.66%
2018          902                 830   92.0%          10           10    $1,154,000       1.08%
2019          846                 753   89.0%          19           20    $2,980,665       1.65%
2020         2841                2662   93.7%          10           13      $317,620       0.12%
2021         6120                5840   95.4%          74          101    $1,539,674       0.61%
2022         5674                5519   97.3%          42           56    $2,116,822       0.78%
2023         5904                5712   96.7%          39           48    $1,110,059       0.36%
2024         9279                9028   97.3%          40           65    $1,768,000       0.39%
2025         9566                9378   98.0%          35           39    $1,105,669       0.24%
2026         9752                9536   97.8%          37           37      $369,500       0.07%
2027         9978                9976  100.0%           0            0            $0       0.00%
```

`orphan EIN` is the falsifying direction: a Schedule C EIN with no disclosure counterpart. **It is
never large, and in FY2027 it is zero.** The per-year reports read these individually — most resolve
to EIN typos, entity renames, or fiscal-conduit-vs-grantee splits, with a genuinely unexplained
remainder each year (FY2024's largest is Wildcat Service Corporation, EIN 132725423, 18 rows,
$1,255,000, no disclosure trace under any name).

### 3d. The aggregation-invariant test

Row-level matching is confounded when one source splits an award the other prints as a single line
(`comparison-2020.md`: Food Bank NYC's Schedule C $625,000 = the disclosure's three rows of
$100,000 + $250,000 + $275,000). Comparing **total dollars per EIN** removes that confound entirely:

```
$ python3 - <<'EOF'   # per-EIN totals both sides, plus a Cleared-only recomputation
FY     all-status cap%  cleared-only cap%  shared EIN  EIN totals equal    rate  schedC$ > disc$
2015              9.8%               9.9%         408                54   13.2%               38
2016              4.3%               4.4%         225                16    7.1%               10
2017              4.2%               4.2%         211                18    8.5%                9
2018             10.1%              10.2%         414                86   20.8%               10
2019              8.8%               8.8%         475                68   14.3%               13
2020             26.8%              26.9%         986               135   13.7%               13
2021             67.6%              68.5%        1825              1088   59.6%               45
2022             50.1%              50.6%        1747               714   40.9%               18
2023             53.5%              54.1%        1880               835   44.4%               16
2024             85.8%              86.5%        2102              1503   71.5%               73
2025             84.8%              85.2%        2154              1538   71.4%               46
2026             82.9%              84.0%        2183              1459   66.8%               50
2027             99.4%             198.1%        2232              2227   99.8%                0
EOF
```

**FY2027: 2,227 of 2,232 shared EINs agree to the dollar on total award value, and not one EIN has
Schedule C claiming more than the disclosure.** In the one year where extraction is essentially
complete, two separately produced documents agree at 99.8% on a key that is immune to row
splitting. That is the strongest single result in this report.

The `cleared-only` column also settles the plan's open question #2 — see §7 Test 2.

---

## 4. FY2021–FY2027, weighted heavily as instructed

The brief asked me to weight the modern years because "extraction is believed good" there. **That
belief is half right, and the half that is wrong is the more important half.**

| | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 | FY2026 | FY2027 |
|---|---|---|---|---|---|---|---|
| per-member streams | ok | ok | ok | ok | ok | ok | ok |
| body award rows | bad | worst | worst | partial | partial | partial | ok |
| row capture (post-1.4.0) | 67.6% | 50.1% | 53.5% | 85.8% | 84.8% | 82.9% | 99.4% |
| internal residual | 33.6% | 52.1% | 46.1% | 15.1% | 22.8% | 26.7% | 7.7% |
| `(EIN, amount)` match | 95.4% | 97.3% | 96.7% | 97.3% | 98.0% | 97.8% | 100.0% |

Read the columns against each other. The **appendix** streams are genuinely fixed from FY2021 on —
that is the Track B win, and the modern years earn the "believed good" label there. The **body**
stream is not. FY2022 and FY2023 are the two worst years in the entire corpus by internal residual
after FY2015–FY2018, and they are years the project currently presents without a coverage caveat.

The agreement evidence, though, is exactly as strong as hoped: FY2021–FY2027 match at
**95.4%–100.0%** on `(EIN, amount)`, and FY2027 reaches EIN-total agreement of 99.8%. **Where the
extraction works, the two sources agree almost perfectly.** That is what licenses the (a) verdict,
and it is why the FY2015–FY2020 gap reads as extraction failure rather than as two documents
describing different things.

---

## 5. Issue #51 — does the disclosure's `Council Member` column change the approach?

**Yes, but not the way the plan hoped.** It does not solve member identity. It does something more
useful: it proves the problem is worse than #51 states.

### It does not disambiguate

Neither source carries a district number or a member ID in any year (raw headers dumped for FY2014,
FY2016, FY2020, FY2024, FY2027 — `Source, Council Member, Legal Name, EIN/Tax ID, Status, Amount,
Agency, Program Name, address…, Purpose, Fiscal Conduit, FC EIN`, plus `MOCS ID#` FY2024+). The
workbook publishes a bare surname and adds an initial **only reactively**, when two sitting members
share a surname that year — and in three different formats:

```
FY2014-FY2019: []                    FY2020: ['D. Diaz']       FY2021: ['D. Diaz']
FY2022-FY2025: []                    FY2026: ['Sanchez, J', 'Sanchez, P']
FY2027: ['J. Sanchez', 'P. Sanchez']
```

(This corrects a claim in two of the per-year reports that FY2026 or FY2027 is "the only year that
disambiguates anything." FY2020 and FY2021 do too, in a third format.)

### It does two useful things

1. **It supplies attribution where Schedule C has none.** FY2016 and FY2017 Schedule C have a
   **100% empty** `member` column (335/335 and 364/364 rows blank). The workbook attributes 85% of
   FY2016 rows. For those years it is the only member data that exists.
2. **It is a per-year controlled roster** — 58–59 labels, versus Schedule C's 1–61 contaminated with
   borough words and text fragments. Used as a validator, it isolates parse artifacts cheaply:

   | FY | Schedule C member labels not in that year's disclosure roster | rows | $ |
   |---|---|---|---|
   | 2018 | `ferreras-`, `manhattan`, `placement`, `program`, `staten island` | 28 | $2,866,230 |
   | 2019 | `brooklyn`, `manhattan`, `placement`, `queens`, `staten island` | 41 | $9,203,015 |
   | 2020 | the four boroughs plus `center` | 56 | $17,750,473 |
   | 2024 | `barron`, `brooks-`, `center`, `jordan`, `kagan`, … (11) | 759 | $33,655,254 |

   Borough delegations are a documented legitimate convention; `placement`, `program`, `center`,
   `brooks-`, `ferreras-` are not — they are page-wrap and truncation artifacts, and this check finds
   them in one pass.

### The finding that actually reframes #51

**The two sources are keyed to different Councils.** Schedule C freezes the sponsor at adoption; the
workbook is re-published later with whoever holds the seat at snapshot time. FY2022 makes it
undeniable:

```
FY2022 Schedule C members absent from the FY2022 disclosure roster: 33
  ['ampry-samuel','cabrera','chin','cornegy','cumbo','d. diaz','diaz','dromm','eugene','gibson',
   'gjonaj','grodenchik','johnson','kallos','koo','koslowitz','lander','levin','levine','maisel',
   'matteo','menchaca','miller','perkins','reynoso','rodriguez','rose','rosenthal','the','treyger',
   'ulrich','vallone','van bramer']
FY2022 disclosure roster members absent from Schedule C: 38
  ['abreu','ariola','aviles','bottcher','brewer','caban','carr','de la rosa','farias','gutierrez',
   'hanif','hanks','hudson','jordan','joseph','kagan','krishnan','lee','marte','mealy','menin',
   'narcisse','nurse','osse','paladino','restler','sanchez','schulman','stevens','ung','velazquez',
   'vernikov','williams','won', …]
```

That is the 2018–2021 Council on one side and the 2022–2025 Council on the other, for the same
fiscal year. The FY2022 workbook's own sheet name is `FY22 (07-11-2023)` — a July 2023 snapshot of a
budget adopted in June 2021. `comparison-2021.md` found five such seat-succession pairs; FY2022 is a
wholesale replacement. (`'the'` in the Schedule C list is a parse artifact, not a member.)

**Consequence:** this is why `(EIN, amount)` matches FY2022 at 97.3% while `(EIN, amount, member)`
collapses to 40.5%. The member columns disagree because they are answering different questions, not
because either is wrong.

**Recommendation for #51.** Rescope it. It is currently framed as "`member` is not a person
identifier." It should be framed as **"`member` is a bare surname whose referent depends on which
document and which year you read it in."** The fix needs an external district-to-member roster per
Council session, which neither source provides. Two things are cheap and worth doing now:
(i) adopt the disclosure roster as a per-year validator for Schedule C member values; (ii) document
that Schedule C `member` = sponsor at adoption and disclosure `Council Member` = seat holder at
snapshot, and **never join the two on member.**

---

## 6. Issue #5 — does FY2013/FY2014 coverage reframe the backfill?

**Yes, decisively for FY2014. Not at all for FY2009–FY2012, and FY2013 is blocked.**

`DATA-ANOMALIES.md` §2 records that FY2009–FY2014 have no organization/EIN detail, and #5 frames the
backfill as reconstruction from Transparency Resolutions. Verified state on disk:

```
$ find data/fy14 -type f
data/fy14/schedule_c/fy14_schedule_c_initiatives.csv      (123 rows, $304,793,605)
data/fy14/schedule_c/fy14_schedule_c_reconciliation.txt
data/fy14/transparency-resolutions/…                      (166 rows, $1,392,772 designated)
                                                          <- no award-level file at all
```

The FY2014 workbook parses cleanly today: **6,611 award-level rows, $393,733,477**, with EIN, status,
agency, address, purpose, and fiscal conduit. Against 166 transparency rows carrying $1.39M — and
those rows are visibly damaged (`head -3 data/fy14/transparency-resolutions/fy14_transparency_all.csv`
shows an `organization` field reading `"Fiscal Member Organization EINNumber Agency Amount Agy# U/A
FiscalConduit… Gentile Inc.)"`).

**So for FY2014 the reconstruction approach is obviated, not assisted.** One deterministic
spreadsheet read produces 40x the rows and 280x the dollars of the resolution-mining route, with a
better schema.

**FY2013 is blocked, not available.** `funded_disclosure_FY2013.xls` is legacy OLE2/BIFF —
`open(...).read(8).hex()` gives `d0cf11e0a1b11ae1`, 2,351,104 bytes. Python's standard library has no
BIFF reader, so the stdlib-only constraint that made the FY2014–FY2027 parser cheap does not reach
it. Options: add `xlrd` (a dependency, for one file), convert once by hand outside the repo and
commit the result as a documented derived artifact, or defer. **Recommendation: defer and say so.**
One year is not worth a dependency, and a hand-conversion is a provenance liability in a repo whose
core promise is "no LLM reads a number."

**FY2009–FY2012 are untouched by this.** The disclosure series begins at FY2013. Transparency
Resolutions remain the only route, and #5 should keep that framing for those four years.

**Net reframe for #5:** split it. FY2014 -> one spreadsheet read, immediate, high confidence.
FY2013 -> blocked on a BIFF reader, decide explicitly. FY2009–FY2012 -> unchanged, still resolution
reconstruction, still hard.

---

## 7. What would falsify this conclusion

I ran the three tests that could have overturned the verdict. One of them produced a real caveat.

### Test 1 — Is `(EIN, amount)` matching meaningful at all? **Partly. This is the caveat.**

Discretionary awards cluster on round amounts ($5,000, $10,000) to a stable set of organizations, so
a high match rate could be coincidence rather than identity. The test: match each year's Schedule C
against **every** year's disclosure. If off-diagonal is close to diagonal, the metric proves nothing.

```
schedC     2015   2016   2017   2018   2019   2020   2021   2022   2023   2024   2025   2026   2027
FY2016    40.9%  86.0%  55.5%  41.2%  25.4%  22.7%  10.7%  12.2%  11.0%  11.0%  11.9%  11.9%  11.0%
FY2020    19.3%  28.5%  45.4%  56.7%  80.1%  93.7%  49.5%  61.9%  53.9%  52.1%  51.0%  50.0%  46.0%
FY2022    27.2%  34.5%  41.3%  47.4%  58.0%  68.3%  73.0%  97.3%  57.5%  48.8%  46.2%  44.1%  39.4%
FY2024    17.2%  22.0%  28.2%  31.5%  37.7%  43.2%  39.8%  53.1%  75.2%  97.3%  78.5%  71.7%  61.8%
FY2027    15.3%  19.2%  24.8%  27.0%  32.0%  36.8%  33.4%  42.9%  54.8%  61.8%  69.1%  79.8% 100.0%
```

**The diagonal wins every time — but the background is high.** FY2027's Schedule C matches the
**FY2026** disclosure at 79.8%; FY2024's matches FY2025 at 78.5%. So a raw "97.3% match" is not 97
points of signal. It is roughly **13–25 points above an adjacent-year baseline**, because the same
organizations receive the same round amounts year after year.

This does not overturn the verdict — the margin is consistent, and FY2016's 86.0% against a 55.5%
background is a 30-point margin in the *worst* year. But **any future write-up citing a match rate
must cite the adjacent-year baseline next to it**, or it overstates its case. This report is the
first thing in the project to measure that baseline.

### Test 2 — Would the Cleared/Pending choice overturn it? **No, and it settles open question #2.**

From the §3d table: filtering to Cleared moves FY2015–FY2026 capture by **under one point** in every
year — and **breaks FY2027 completely**, where 5,003 of 10,040 rows are Pending, producing a
nonsensical 198% capture. `comparison-2024.md` found the same from the other direction: filtering to
Cleared destroys all three of FY2024's exact stream agreements.

**Answer to the plan's open question #2: carry the flag, do not default to Cleared.** The plan's
tentative recommendation ("default to Cleared") is wrong and would corrupt the newest fiscal year.

### Test 3 — Are the two sources actually independent? **No, and that limits how much agreement proves.**

Both documents are produced by the New York City Council from the same internal designation
database: Schedule C is its adopted-budget rendering, the workbook its disclosure rendering. **This
is one record set rendered twice, not two independent observers.** Agreement therefore proves the
extraction is faithful to a shared source; it does **not** independently validate the Council's own
figures.

Evidence they are nonetheless *separately produced*, so agreement is still informative: the workbook
carries fields the PDF never prints (`Fiscal Conduit`, `FC EIN`, grantee address, `MOCS ID#`); its
sheet names record independent revision dates (`FY19 (4-14-21)`, `FY22 (07-11-2023)`); and the two
**disagree on specific published figures** — FY2020 Public Health Funding Backfill ($6,000,000 in the
PDF vs $4,667,933 in the workbook) and FY2027 `Support Our Older Adults` (a $1 difference between
the Council's own two documents). Neither is strictly authoritative over the other.

### What I did *not* manage to falsify, and would still like to

- No test I ran distinguishes "extraction lost the row" from "the row was designated post-adoption"
  in FY2022/FY2023/FY2026. That needs a page-by-page PDF read, which I did not do.
- FY2015 was never in the plan's table and has **no per-year report**. Its 9.8% capture and 81.7%
  match rate are the weakest numbers in the corpus and are the least examined.

---

## 8. Phase 2 recommendation: **proceed, with a changed shape and a changed order**

Phase 1's gate is satisfied — the sources are comparable, which is what Phase 2 was waiting on. But
three of Phase 2's premises should change.

**Proceed as written on:**

- Emitting `data/{year}/expense_disclosure/{year}_expense_awards.csv`, one row per award. The parser
  exists (`code/parse_expense_disclosure.py`, committed as `7cd320b`), is stdlib-only, and handles
  all seven header layouts plus the embedded-summary trap (9 rows stripped across FY2024/FY2026).
- **Keeping it separate from the Schedule C extraction.** The different-Council finding in §5 is a
  decisive argument for this. The two sources disagree on sponsor by design; merging them would
  destroy the provenance that makes the disagreement legible.

**Change:**

1. **Extend the scope to FY2014–FY2027, not FY2016–FY2020.** All thirteen parseable years benefit,
   FY2014 most of all (§6). FY2013 is deferred with a documented reason.
2. **Do not default `Status` to Cleared.** Carry the flag. FY2027 is ~50% Pending (§7 Test 2).
3. **Reorder: the FY2015–FY2020 appendix recovery is now the highest-value item on the whole plan,
   ahead of Phase 2's general ingestion.** 26,935 rows and $294,629,825, in a program whose per-year
   totals are known to within 1% before any code runs (§3a). Nothing else on the plan has that
   combination of size and testability. It sits in Phase 4 by the plan's numbering; it should be
   done next.
4. **Add a new item: FY2022 and FY2023 body extraction.** They are currently presented as clean
   years and they are the two worst in the corpus by internal residual. At minimum they need the
   Phase 0 coverage caveat that FY2016–FY2020 is getting. This is not in the plan at all.

**One thing to change immediately (Phase 0):** the plan's Phase 0 adds a coverage warning for
FY2016–FY2020. Ship it — but scoped to the measured years, not to a five-year window that implies
the rest is complete. On the evidence here the warning belongs on **every year except FY2027**.

---

## 9. Gaps, blockers, and things I could not verify

**Blockers**

1. **FY2013 is unreadable with the stdlib.** OLE2/BIFF. Needs `xlrd`, an out-of-band conversion, or
   a deferral decision. Not resolvable tonight under the no-install rule.
2. **No network.** Every claim about the Council's publication dates, `Last-Modified` headers, or
   the live RnD site is inherited from the parent plan and `source/expense-funding-disclosure/README.md`.
   I did not re-verify any of it.

**Not verified — stated as inference, flagged here so it is not later read as fact**

3. **The FY2022/FY2023/FY2026 residual is not partitioned.** I show it exists and is 6–7x the
   FY2027 floor. I did **not** read those PDFs to establish how much is extraction loss versus
   legitimate post-adoption or agency-direct money. This is the largest open question in the report.
4. **The per-year "unexplained" orphan EINs are inherited, not re-checked.** Each per-year
   report read its own orphans individually; I re-derived the counts but did not re-read the
   individual rows.
5. **The FY2027 post-adoption explanation is quoted from `comparison-2027.md`**, which verified it
   against the PDF. I did not independently re-open the PDF.
6. **The asterisk mechanism** — that FY2016/FY2017's dropped rows are the asterisked ones — is
   verified in `comparison-2016.md` and `comparison-2017.md` for those two years only. **Whether it
   explains FY2018–FY2020 is untested.** The parent plan flagged this as its most reputationally
   significant unconfirmed claim; it is now confirmed for two years and open for three.

**Coverage gaps in this Phase 1 run**

7. **FY2015 has no per-year report.** It sits below every other year on both capture (9.8%) and match
   rate (81.7%) and was never in the plan's table. It deserves the same treatment FY2016–FY2021 got.
8. **FY2022, FY2023, FY2025, FY2026 are covered by this document only** — the corpus-wide tables and
   the FY2022 roster dig. There is no per-year deep read for any of the four, and FY2022/FY2023 turned
   out to be the years that most need one.
9. **Cross-year contamination in the appendix streams was not tested.** The disclosure stream totals
   are ~$49.8M every year; I did not test whether a given year's *appendix rows* could have been
   parsed from an adjacent year's pages.

**Known inconsistencies among the per-year reports, left standing rather than silently reconciled**

10. Two reports claim FY2026 (or FY2027) is the only year that disambiguates a surname. **Both are
    wrong** — FY2020 and FY2021 carry `D. Diaz`. Corrected in §5; the source reports were not edited.
11. `comparison-2016.md` and `comparison-2018.md` describe the disclosure as "not a superset" and
    "a superset" respectively. Both are locally correct. The corpus view (§3c) shows the residue is
    real but no more than 3.07% of dollars in any year — which is why §1 states the verdict as (a)
    with (b) failing narrowly, rather than picking one of the per-year framings.

**Repo state noted in passing, not acted on**

12. `README.md:95` still says the appendix files "are subsets of the main body re-sorted by funding
    stream — **do not add them to the Schedule C total**." Track B's evidence (97.5% of appendix rows
    unmatched against their own year's awards CSV) and §3a here both contradict it for the awards
    table. `data/` and the root README were read-only tonight. **This needs a decision before 1.4.0
    ships**, because the repo and the tools now tell different stories.
13. Seven ad-hoc `compare_*.py` / `diagnose_*.py` scripts now sit in this folder from eight parallel
    sessions. `compare_year.py` is the generic form and is what this report and `findings_corpus.py`
    both build on. Collapsing the rest is housekeeping worth doing.
