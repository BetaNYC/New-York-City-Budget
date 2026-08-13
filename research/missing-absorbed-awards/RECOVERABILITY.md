---
title: "Question 2 — Can the absorbed awards be recovered, and how confidently?"
created: 2026-08-12
type: research-findings
status: draft
tags: [nyc-budget, schedule-c, data-quality, award-recovery]
---

# Question 2 — Can the absorbed awards be recovered, and how confidently?

**Report generated** 2026-08-12
**Data current as of** 2026-08-12 (working tree `research/missing-absorbed-awards`, branch
`research/missing-absorbed-awards`, base commit `2c8168f`), and
`source/expense-funding-disclosure/funded_disclosure_FY2014..FY2027.xlsx` as committed.
**Scope** the 303 rows the `org_merged` advisory flags in `code/validate_data.py`. Nothing else.

Reproduce every number here with:

```
python3 code/prototype_recover_absorbed.py --demo          # parser self-check
python3 code/prototype_recover_absorbed.py                 # full pass, writes the candidate CSV
python3 code/prototype_recover_absorbed.py --naive-reader  # prices the xlsx reader bug (§7.1)
```

Row-level output: `research/missing-absorbed-awards/absorbed_award_candidates.csv` (445 rows).

**Relationship to Question 1.** This pass extracted the absorbed awards independently of
`inventory_absorbed.py` — different code, different author — and lands on the same population:
**445 triples, 443 with no row in their own fiscal year, 437 distinct awards, $66,376,721.**
Two independent extractions agreeing to the dollar is the strongest evidence available that the
extraction itself is sound. Tier counts below are given over all 445 triples; §6.1 restates them
over the 437 distinct awards so the two reports reconcile.

---

## 1. Answer in one paragraph

**Yes, and mostly at full confidence.** Of the 445 absorbed (EIN, amount) pairs, **384 (86.3%,
$60,242,459) resolve to exactly one row in the Council's disclosure workbook for the same fiscal
year** — an unambiguous identification that supplies organization, agency, purpose, and the
disclosure's own `Source` label verbatim. A further 24 (5.4%) resolve to one *organization* but
several *rows*, so the name is safe and the per-award fields are not. 18 (4.0%) resolve only by
pooling across fiscal years or resolve to more than one organization. **19 (4.3%, $2,839,146) have
no disclosure row at that EIN and amount in any year and cannot be completed from this source at
all.** Two of our ten schema fields — **`category` and `initiative`** — do not exist in disclosure
in any form; §5 shows that inheriting them from the absorbing row is *usually* right and *unsafely*
so, and recommends inheriting only `category`, flagged as inferred.

---

## 2. What was extracted, and why the pairs can be trusted

The parser loses an award when the PDF prints an asterisk, a program name, or a CASA school between
the EIN and the amount. That award's text lands in the `organization` field of the next row that
*does* match:

```
data/fy17/schedule_c/fy17_schedule_c_awards.csv:159
  ein 112435523  amount 29729
  organization "Bridge Street Development Corporation 11-3250772 * $29,729 Brighton Neighborhood Association, Inc."
```

`absorbed()` walks each such string, pairs every EIN with the first dollar amount within
`MAX_EIN_AMT_GAP` characters, and treats the preceding text as a name *hint only*.

**The distance budget is measured, not guessed.** Across all 303 rows, 442 of 445 EIN→amount gaps
are 0–9 characters (`" * "`) and 3 are 20–29 (a CASA school name between the two). Nothing sits
further out. An EIN with no amount after it — a fiscal-conduit EIN, e.g.
`JCC of Greater Coney Island 112665181` in `fy18_appendix_a_aging.csv:333` — is correctly **not**
asserted as an award.

**Independent confirmation that the pairing is right.** For the 423 triples matching a single
disclosure identity, the name scraped out of the PDF text agrees with the legal name disclosure
attaches to that (EIN, amount):

| extracted name vs disclosure legal name | n | share |
|---|---:|---:|
| exact after canonicalization | 339 | 80.1% |
| one is a substring of the other | 62 | 14.7% |
| differ | 21 | 5.0% |
| extracted name empty | 1 | 0.2% |

Two sources that never see each other agree on **94.8%** of the pairs.

**And it proves the name hint is not itself usable.** Some of the 21 are off-by-one, not spelling
drift. `fy17_schedule_c_awards.csv:161` reads
`Clinton Housing Development Company, Inc. 11-2652331 * $29,729 …`, but FY2017 disclosure says
`11-2652331` is *Central Astoria Local Development Coalition, Inc.* — Clinton Housing is
`13-2851988`. In that stretch of the PDF the name column is offset one row from the EIN column.
**This is why `recover_org_names.py` keyed on (EIN, amount) rather than on EIN or on name, and the
same choice is load-bearing here:** the amount is what makes the key survive a misaligned name.

---

## 3. Match rates

```
absorbed triples extracted: 445
  unique         | same_fy    384   86.3%
  unique_by_name | same_fy     24    5.4%
  unique         | any_fy      10    2.2%
  unique_by_name | any_fy       5    1.1%
  ambiguous      | any_fy       3    0.7%
  absent         | none        19    4.3%
  already have a row of their own    2
  genuinely missing                443
```

- **Uniquely matched: 423 of 445 (95.1%).**
- **Ambiguous (>1 distinct legal name at that EIN and amount): 3 (0.7%).**
- **Absent (no disclosure row anywhere): 19 (4.3%).**

By fiscal year. The defect is concentrated in FY17–FY18 and does not exist outside FY16–FY19:

| FY | triples | unique | unique_by_name | ambiguous | absent |
|---|---:|---:|---:|---:|---:|
| FY16 | 26 | 21 | 0 | 0 | 5 |
| FY17 | 207 | 189 | 12 | 1 | 5 |
| FY18 | 169 | 146 | 15 | 1 | 7 |
| FY19 | 43 | 38 | 2 | 1 | 2 |

**All three ambiguous cases are the same organization under two spellings**, not two grantees:

```
FY17 134145441  $20,000  ->  ['NPower Inc.', 'Npower, Inc.']
FY18 237085239  $80,000  ->  ['New York Center for Interpersonal Development, Inc.',
                              'YPIS of Staten Island Inc. (New York Center for Interpersonal Development)']
FY19 201407519  $14,600  ->  ['Rising Circle Theater Collective', 'Rising Circle Theater Collective, Inc.']
```

A canonicalizer would collapse all three. They are held at tier C anyway, because deciding that two
strings name one legal entity is a judgment, not a string operation — and the corpus already
contains at least one pair where it is genuinely hard (`Her Justice` / `InMotion`, one organization
that renamed, §7.3).

---

## 4. Per-field fill rate — what disclosure can actually supply

Our schema is `category, initiative, award_type, member, organization, program, ein, amount,
agency, purpose`. Rates count rows where disclosure supplies a value **every** candidate row agrees
on (tier A has one candidate, so it is the raw fill):

| our field | disclosure column | tier A | tier B | tier C |
|---|---|---:|---:|---:|
| `category` | — none — | — | — | — |
| `initiative` | — none — | — | — | — |
| `award_type` | — none — | — | — | — |
| `member` | Council Member(s) | 20.3% | 25.0% | 22.2% |
| `organization` | Legal Name | **100.0%** | **100.0%** | 83.3% |
| `program` | Program Name | 2.6% | 0.0% | 5.6% |
| `ein` | EIN / Tax ID | **100.0%** | **100.0%** | **100.0%** |
| `amount` | Amount | **100.0%** | **100.0%** | **100.0%** |
| `agency` | Agency | **100.0%** | 66.7% | 88.9% |
| `purpose` | Purpose of Funds | **100.0%** | 33.3% | 66.7% |
| *(no field)* | Source | **100.0%** | 54.2% | 72.2% |

### `member` at 20.3% and `program` at 2.6% are structural, not a matching failure

Disclosure fills `Council Member` 79–92% of the time overall. The absorbed awards are not a random
sample: **404 of 445 sit on rows whose `award_type` is `initiative_provider`** (40 blank, 1
`member_item`) — citywide initiative awards with no sponsoring member. Restricting the disclosure
baseline to exactly the `Source` values our tier-A awards belong to gives a weighted member fill of
**48.5% (n = 7,044)**, and the largest individual initiatives are 0%:

```
 19.2%  n=  214  Community Housing Preservation Strategies
  0.0%  n=  176  Coalition Theaters of Color
100.0%  n= 2168  Aging
  0.0%  n=  170  Autism Awareness
  0.0%  n=   52  Discretionary Child Care
  0.0%  n=   25  COMPASS
```

`member` is empty in these records because **there is no member**, not because the row was not
found. The same holds for `program` (13.1% in FY16 rising to 45.8% in FY19 overall, concentrated in
member-driven awards).

**Do not backfill either field.** A blank meaning "citywide, no sponsor" is correct data; a member
name carried over from the absorbing row would be a fabricated attribution to a named public
official.

---

## 5. `category` and `initiative` — the fields disclosure cannot supply

Neither exists in the workbooks. `award_type` does not either, but it is trivially derivable from
`Source` (`Local`/`Youth`/`Aging`/`Boro` → `member_item`, otherwise `initiative_provider`) and is
not at issue.

The tempting inference: **the absorbed award sat immediately before the absorbing row in the same
PDF stream, therefore under the same section heading, therefore it can inherit the absorbing row's
`category` and `initiative`.**

### The inference is usually right

Testing it against disclosure's own `Source` — does the absorbed award share a `Source` with the
row that swallowed it? Over the 423 uniquely-matched triples:

```
same_source                       384   90.8%
absorbing_row_not_in_disclosure    23    5.4%
DIFFERENT_source                   16    3.8%
```

### And not good enough for `initiative`

The 3.8% failures are precisely the awards that sat at a **section boundary** — last award of one
initiative, absorbed into the first row of the next:

```
FY17 161765323  $52,692  absorbing=[Access Health Initiative]        absorbed=[Access Health NYC]
FY17 202015286  $32,000  absorbing=[Infant Mortality Reduction]      absorbed=[Maternal and Child Health Services]
FY17 471169779  $29,730  absorbing=[Community Consultants Contracts] absorbed=[Community Housing Preservation Strategies]
FY17 133468427  $75,000  absorbing=[Joseph S. Murphy Institute …]    absorbed=[Immigrant Health Initiative]
```

Two things make this worse than 3.8% suggests:

1. **The absorbing row's own `initiative` is unreliable to begin with.** Checking every clean
   FY16–FY19 award row against its same-year disclosure `Source`: 56.5% match, 6.9% partial,
   **18.0% differ**, 6.8% our value blank, 11.8% no disclosure row. Inheriting from an 18%-wrong
   field compounds error rather than bounding it. In the `471169779` case above the absorbing row's
   `initiative` is *blank*, so the inheritance would have produced nothing anyway.
2. **A wrong `initiative` is invisible downstream.** A blank reads as "unknown". An inherited wrong
   one reads as fact — and the entire point of this recovery is to add rows people can trust.

### Recommendation

- **`initiative`: leave blank.** Populate it instead from the disclosure `Source`, which is present
  for 100% of tier A, is the Council's own label, and is *measured* rather than inherited. That
  needs a `Source` → `initiative` crosswalk, because the vocabularies drift (`Access Health
  Initiative` vs `Access Health NYC`). Building that crosswalk is separate work and is **not**
  attempted here.
- **`category`: inherit from the absorbing row, and mark it inherited.** Every
  `DIFFERENT_source` example stays inside one category (`HEALTH SERVICES`, `HOUSING`, `IMMIGRANT
  SERVICES`) — category is a coarser heading than initiative and survives a section-boundary
  crossing. This is **inferred, not verified**: nothing in either source confirms it award by
  award, so recovered rows must carry a provenance column saying so (see `PROVENANCE.md`).
- **`award_type`: derive from `Source`.** Deterministic, and consistent with existing corpus usage.

---

## 6. Confidence tiers

| tier | n | share | dollars | what it means | what may be written |
|---|---:|---:|---:|---|---|
| **A** | **384** | 86.3% | $60,242,459 | one same-year disclosure row at (EIN, amount) | `ein`, `amount`, `organization`, `agency`, `purpose` verbatim; `member`/`program` verbatim where non-blank; `category` inherited-and-flagged; `initiative` blank pending a `Source` crosswalk |
| **B** | 24 | 5.4% | $495,500 | several same-year rows, all one legal name | `ein`, `amount`, `organization` only. The candidate sets **disagree** on `member` 16/24, `purpose` 16/24, `program` 9/24, `agency` 8/24 — those must stay blank |
| **C** | 18 | 4.0% | $2,969,116 | matched only by pooling fiscal years, or >1 distinct legal name | nothing without human review: a cross-year match may be a different award of the same size |
| **D** | 19 | 4.3% | $2,839,146 | no disclosure row at that EIN and amount in any year | not completable from this source |
| | **445** | | **$66,546,221** | | |

**Full confidence: 384 awards, $60.2M. Partial: 42 awards (B + C), $3.46M. Not at all: 19 awards,
$2.84M.**

### 6.1 Restated over the 437 distinct awards, to reconcile with Question 1

Of the 445 triples, 2 collide with a `(fy, ein, amount)` that already has a row, and 5 keys appear
twice within the absorbed set (6 surplus triples). Removing both gives the Q1 figure exactly:

| tier | distinct awards | share | dollars |
|---|---:|---:|---:|
| A | 383 | 87.6% | $60,202,459 |
| B | 17 | 3.9% | $366,000 |
| C | 18 | 4.1% | $2,969,116 |
| D | 19 | 4.3% | $2,839,146 |
| **total** | **437** | | **$66,376,721** |

### 6.2 The 19 in tier D

Mostly large, plausible awards whose EIN appears in disclosure in *other* years at *other* amounts —
the grantee is real; the amount is what fails to match.

```
FY16 131788491  $1,000,000  American Cancer Society, Inc., The
FY16 135654450    $234,000  Selfhelp Community Services - Northridge NORC
FY17 131924236    $200,000  Memorial Sloan-Kettering Cancer Center
FY17 510204121    $204,103  Jamaica Service Program for Older Adults (JSPOA)
FY17 043263046    $175,000  Jumpstart for Children
FY18 132969182    $160,000  Urban Youth Alliance International, Inc.
FY18 261385792    $109,000  Bronx Freedom Fund, Inc.
FY18 135623279    $107,103  Staten Island Mental Health Society, Inc.
FY19 133385032    $125,000  Mary Mitchell Family and Youth Center, Inc.
FY19 132806160    $125,000  Northwest Bronx Community and Clergy Coalition, Inc.
```

(Full list in the CSV, `tier == "D"`.)

This is consistent with Phase 1: disclosure is not a strict superset of Schedule C (0.07%–3.07% of
extracted dollars per year have no disclosure counterpart). **These are awards Schedule C is the
only record of — and the corpus currently has no row for them at all.** They remain recoverable *as
awards* from the Schedule C text itself: name, EIN and amount are all legible in the absorbed
string. What is not recoverable is anything disclosure would have supplied. A tier-D row could be
written with `organization` from the extracted name, accepting the 5% name-alignment risk of §2,
and `agency`/`purpose`/`member` blank.

### 6.3 Two absorbed awards already have a row

`fy18_appendix_a_aging.csv:402` (Vocal Ease, Inc., $3,500) and `fy18_schedule_c_awards.csv:364`
(Street Corner Resources, Inc., $40,000). A human must decide whether the existing corpus row *is*
this award or a genuine second award of the same size. Every other absorbed award is absent from
the corpus entirely.

---

## 7. Three findings outside the question that bear on the answer

### 7.1 `recover_org_names.py` reads xlsx in a way that silently drops rows

`read_workbook()` in `code/recover_org_names.py` builds each row as
`dict(zip(header, [cv(c) for c in row.findall('c')]))`. **Excel omits empty cells**, so any row with
a blank in the middle shifts every later column one position left. Where `Council Member` is blank —
every citywide initiative award — `EIN` reads the literal string `Cleared`, and the row drops out of
the lookup entirely.

Measured by running the same match with both readers:

| workbook | (EIN, amount) keys, naive `zip` | positional (`r` attribute) | lost |
|---|---:|---:|---:|
| FY2014 | 2,035 | 2,245 | **210** |
| FY2016 | 5,619 | 5,867 | **248** |
| all others | identical | identical | 0 |
| **total** | **86,903** | **87,361** | **458** |

`prototype_recover_absorbed.py` maps cells by their `r` attribute instead. The gain on this task is
9 triples moved up into tier A (`--naive-reader` gives 375 tier A, 13 `unique|any_fy`, 6 ambiguous;
the positional reader gives 384, 10, 3).

**The consequence for the 1,060 already-applied name recoveries has not been assessed and should
be.** The same reader produced them, and FY2016 — where it is worst — is in scope for that pass.

### 7.2 I could not reproduce the handed-down "248 of 303 confirmed, 55 absent, all FY2016"

The retained rows' own (EIN, amount) confirm at these rates:

| reader | scope | confirmed | absent | absent by FY |
|---|---|---:|---:|---|
| naive | same FY | 257 | 46 | FY16 12, FY17 14, FY18 14, FY19 6 |
| naive | any FY | 282 | 21 | FY16 4, FY17 9, FY18 5, FY19 3 |
| positional | same FY | **265** | 38 | FY16 4, FY17 14, FY18 14, FY19 6 |
| positional | any FY | 282 | 21 | FY16 4, FY17 9, FY18 5, FY19 3 |

Filtering to `Status = Cleared` changes nothing. **No combination yields 248/55, and none puts every
absent row in FY2016.** Either the figure used a method not reconstructed here, or it is wrong.
Flagged, not resolved — it does not affect the answer above, which is measured on the absorbed
triples independently. **Treat 248/55 as unverified.**

### 7.3 The 303 is not the full extent of the defect

- **The `program` column has the same absorption and nothing counts it.** `org_merged` inspects only
  `organization`. **40 rows carry EIN-and-amount text in `program`, holding 93 further extractable
  pairs** — 23 in `fy18_appendix_a_aging.csv`, 8 in FY17, 6 in FY16, 2 in FY19, 1 in FY18.
  `fy19_schedule_c_awards.csv:632` alone has an entire CASA table in its `program` field.
- **3 of the 303 are not absorption at all.** `fy24:4850`, `fy25:5074`, `fy26:5204` carry the same
  purpose sentence — *"The funds requested will subsidize the delivery of farm shares to $12 per
  share…"* — which trips the `"$" in org` test. They are `org_prose`; the `elif` ordering at
  `validate_data.py:353-361` misroutes them into the more severe advisory.
- **2 of the 303 have a corrupted EIN in the absorbed text.** `fy18:442` and `fy20:2665` both read
  `Urban Health Plan, Inc. 15-24042810 $88,855`. There is no EIN `15-2404281`. The award is
  **Urban Health Plan, Inc., EIN 23-7360305, $88,855, MWBE Leadership Associations, SBS**, present
  in the FY2018 and FY2020 workbooks and unique there on (name, amount). Recoverable, but only via a
  fallback key this prototype does not implement.
- **Rows the advisory does not flag can still carry the wrong name.** Checking every unflagged award
  row against its unique same-FY disclosure row: 89.6% agree, 6.8% ambiguous, 2.4% no unique row,
  **0.7% (409 rows) disagree**. Sampling shows most are spelling variants (`Brooklyn Defender` vs
  `Brooklyn Defenders Services`), some are renames (`Her Justice` / `InMotion`), and some are real
  misalignment — `fy15_schedule_c_awards.csv:37` reads `Eugene Brooklyn Housing and Family
  Services,` where disclosure has `Housing and Family Services of Greater New York, Inc.` and
  `Eugene` is a council member's surname. **409 is an upper bound on a mostly-benign population, not
  a defect count.** Note that `recover_org_names.py` has already rewritten 1,060 names on this
  branch using the same key, so agreement is partly by construction and this figure understates the
  pre-existing drift.

---

## 8. What this does not establish

- **Nothing has been written back to `data/`.** The prototype is read-only apart from its own CSV
  under `research/`.
- **The `Source` → `initiative` crosswalk does not exist.** Until it does, `initiative` on recovered
  rows should be blank, and tier A's "100% Source fill" is potential, not realized.
- **Whether recovered rows change any published total is out of scope here** — see
  `RECONCILIATION.md` (Question 3), which measures exactly that.
- **The 19 tier-D awards are unresolved, not disproven.** They may exist in the FY2013 `.xls`
  workbook (not readable by `zipfile`, excluded here), in a later republication of a workbook, or
  nowhere. **Unknown.**
- **`--naive-reader` mode was used to price §7.1 only.** Its output goes to
  `absorbed_award_candidates_NAIVEREADER.csv` so it cannot be mistaken for the real result.
