# Absorbed awards: exactly what is missing

**Report generated:** 2026-08-12
**Data current as of:** 2026-08-12 (working tree `research/missing-absorbed-awards`, commit `2c8168f`)
**Scope:** Question 1 — parse the 303 `org_merged` rows, extract every absorbed (EIN, amount, name)
triple, and determine which have no row anywhere in `data/`.

Reproduce every number here with:

```
python3 research/missing-absorbed-awards/inventory_absorbed.py --self-check
python3 research/missing-absorbed-awards/inventory_absorbed.py
```

Per-triple output: `research/missing-absorbed-awards/absorbed_triples_inventory.csv` (647 rows).

---

## Headline

**445 absorbed awards were extracted from the 303 flagged rows. 443 of them have no row in their
own fiscal year — 437 distinct awards worth $66,376,721.**

The literal test the question proposes — *does a row with that `(ein, amount)` exist anywhere in
`data/`* — returns a much smaller number, **153 absent / $24.3M**. That test is wrong, and
demonstrating why is the main finding of this inventory. Both numbers are given below.

| Reading of "already exists" | Absent triples | Distinct awards | Dollars |
|---|---:|---:|---:|
| `(ein, amount)` anywhere in `data/` — the literal question | 153 | 151 | $24,298,733 |
| `(fiscal year, ein, amount)` — the award-correct test | **443** | **437** | **$66,376,721** |

"Already exist elsewhere, so duplicated in text rather than lost": **292** under the literal test,
**2** under the correct one.

---

## 1. The shape, verified against real strings

The brief's sketch was `"<org A text> <EIN of B> * $<amount of B> <org B name> ..."`. The real
strings say something slightly but importantly different: **a grantee's name is printed immediately
BEFORE its own EIN**, not after it. The anchor case:

```
data/fy17/schedule_c/fy17_schedule_c_awards.csv:209
  ein 113305406   amount 2076666
  organization "Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services"
```

Bronx Defenders' EIN is 13-3931074 and Brooklyn Defender Services' is 11-3305406. So the row's own
columns belong to the **trailing** name, and `(13-3931074, $2,076,667)` is a separate award. Second
confirmation, where the two EIN prefixes are unambiguous (Manhattan `13-` vs Queens `11-`):

```
fy17_schedule_c_awards.csv:175   ein 112435565  amount 29730
  "West Side Federation for Senior Supportive Housing, Inc. 13-2926433 * $29,730 Woodside on the Move, Inc."
```

This matters mechanically: the name for a triple is the text since the *previous* award's amount,
not the text after the EIN.

Three printed variants have to be read by one pass:

| Variant | Example |
|---|---|
| asterisk (common) | `Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services` |
| no asterisk, bare 9-digit EIN | `Make the Road New York 113344389 * $52,692 New York Immigration Coalition` |
| **program name between EIN and amount** | `East Flatbush Village, Inc. 80-0612019 Meyer Levin High School $18,000 Afro-Latin Jazz Alliance of New York, Inc. 45-3665976 Brownsville Academy $18,000 Central` |

Appendix rows also carry cents and interleaved member surnames and purpose prose:

```
fy18_appendix_a_aging.csv:402   ein 371469320  amount 3000
  ".00 Funding will support the operating costs of Vocal Ease's program, ... Rodriguez
   Vocal Ease, Inc. 371469320 * $3,500.00 Funding will be used for operating expenses ... Johnson Vocal Ease, Inc."
```

Up to six awards are absorbed into a single row:

| Triples in one host row | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|
| host rows | 208 | 52 | 25 | 8 | 4 | 1 |

### How the pairing is made safe

A single regex spanning EIN→amount either misses the third variant or, made permissive, lets an EIN
claim an amount belonging to a *later* award. The extractor instead walks EIN occurrences in order
and **bounds each amount search at the next EIN**. An EIN can only ever claim an amount printed
before the next EIN appears; one with none is reported as an orphan, never guessed at. The
self-check asserts this directly (`Alpha 11-1111111 Beta 22-2222222 * $500 Gamma` must yield one
triple, not two).

---

## 2. Extraction results

**445 triples from 298 of the 303 rows.** The five rows yielding nothing are worth naming, because
three of them are not this defect at all:

| Row | Why no triple |
|---|---|
| `fy24:4850`, `fy25:5074`, `fy26:5204` | **Advisory false positives.** Purpose prose containing `"...farm shares to $12 per share..."`. No EIN, no absorbed award. The `org_merged` test fires on any `$`. |
| `fy18_schedule_c_awards.csv:442` | **Malformed EIN**, unrecoverable by key: `"Urban Health Plan, Inc. 15-24042810 $88,855 West Brighton Community Local Development Corporation"` — eight digits after the hyphen. |
| `fy20_schedule_c_awards.csv:2665` | Same malformed EIN, same $88,855 award. |

So the true `org_merged` population is **300 rows**, not 303, and two known-lost awards
($88,855 each, FY2018 and FY2020) cannot be keyed at all.

Two orphan EINs (an EIN with no amount before the next EIN) are reported and left unpaired:
`112665181` at `fy18_appendix_a_aging.csv:333` and `11-6000202` (Brooklyn Music School) at
`fy19_schedule_c_awards.csv:632`.

---

## 3. Why `(EIN, amount)` alone is the wrong presence key

`code/recover_org_names.py` established `(EIN, amount)` as the award key because EIN alone is
unsafe — fiscal sponsors pass funds through for many grantees, and 13-2612524 carries 229 distinct
names in this corpus. **That reasoning is correct and is kept here.** But for a *presence* test it
is not sufficient, and the gap is large.

Council initiatives fund the same organization at the same standard amount year after year. So an
absorbed FY2016 award tests as "already present" against an FY2019 row that is a **different
award**. Worked example — Hudson Guild, EIN 13-5562989, $29,730, absorbed from an FY2016 row:

```
$ grep -rn "135562989" data/fy*/schedule_c/ | grep "29730"
data/fy17/.../fy17_schedule_c_awards.csv:165   ... 135562989,29730
data/fy18/.../fy18_schedule_c_awards.csv:181   Hudson Guild,,135562989,29730
data/fy19/.../fy19_schedule_c_awards.csv:391   Hudson Guild,,135562989,29730
data/fy20/.../fy20_schedule_c_awards.csv:1758  Hudson Guild,,135562989,29730

$ grep -rn "135562989" data/fy16/schedule_c/
data/fy16/.../fy16_schedule_c_awards.csv:302   Hudson Guild,,135562989,84000     # $84,000, not $29,730
```

The FY2016 $29,730 award to Hudson Guild exists in no FY2016 file. The year-agnostic test called it
present anyway. **290 of the 292 "already present" triples are this collision class** — matched only
in a different fiscal year.

### Three independent checks that the year-scoped answer is the right one

1. **427 of the 443** year-scoped-absent triples are for an organization with **no row at all** in
   that fiscal year. Not a different award — no award.
2. **Zero** of the remaining 16 have an existing same-year amount within 1% of the extracted one, so
   there is no evidence any of these are amount mis-reads of a row that does exist.
3. **The Council's own disclosure workbooks confirm 91.5% of them**, at exact same-year EIN+amount
   (400 of 437 distinct FY2016–FY2019 awards). The baseline for comparison is what the *cleanly
   parsed* rows achieve against the same workbooks:

   | Fiscal year | Clean parsed rows confirmed | Absorbed triples confirmed |
   |---|---:|---:|
   | FY2016 | 85.9% | — |
   | FY2017 | 89.6% | — |
   | FY2018 | 92.0% | — |
   | FY2019 | 90.0% | — |
   | FY2016–19 combined | 86–92% | **91.5%** |

   The awards this parser threw away are, as a population, exactly as real as the ones it kept.

---

## 4. Total dollars genuinely missing, per fiscal year

**Q1 scope — organization column of the flagged rows, year-scoped test (the answer):**

| Fiscal year | Distinct awards missing | Dollars missing | Confirmed by Council disclosure |
|---|---:|---:|---:|
| FY2016 | 26 | $11,059,565 | 21 / $9,736,375 |
| FY2017 | 203 | $27,769,502 | 190 / $26,626,967 |
| FY2018 | 165 | $23,289,954 | 149 / $20,212,017 |
| FY2019 | 43 | $4,257,700 | 40 / $3,993,100 |
| **Total** | **437** | **$66,376,721** | **400 / $60,568,459** |

For comparison, the literal `(ein, amount)`-anywhere test:

| Fiscal year | Distinct awards | Dollars |
|---|---:|---:|
| FY2016 | 15 | $8,424,370 |
| FY2017 | 65 | $10,635,211 |
| FY2018 | 49 | $2,756,173 |
| FY2019 | 22 | $2,482,979 |
| **Total** | **151** | **$24,298,733** |

Largest individual losses (all VERIFIED absent from their fiscal year):

| FY | EIN | Amount | Grantee | Absorbed into |
|---|---|---:|---|---|
| FY2016 | 13-3564313 | $5,354,200 | Consortium for Worker Education (CWE) | `fy16_schedule_c_awards.csv:243` |
| FY2017 | 13-3931074 | $2,076,667 | Bronx Defenders | `fy17_schedule_c_awards.csv:209` |
| FY2017 | 47-2375867 | $2,000,000 | A&G Early Child Care Community Network Inc. | `fy17_schedule_c_awards.csv:2` |
| FY2016 | 13-1788491 | $1,000,000 | American Cancer Society, Inc., The | `fy16_schedule_c_awards.csv:43` |
| FY2016 | 26-1269358 | $750,000 | Heath Corps, Inc. | `fy16_schedule_c_awards.csv:57` |

Confirming the largest by hand:

```
$ grep -rn "133564313" data/ | grep -c "5354200"
0                    # CWE appears in FY15/22/23/24 at other amounts; $5,354,200 exists nowhere
```

---

## 5. The advisory's blind spot (outside Q1 scope, but it changes the total)

The `org_merged` advisory only inspects the `organization` column. Absorbed text also lands in
`program` and `purpose`, and there the advisory is silent:

- **40 more triples** inside the same 303 flagged rows, spilled into `program`/`purpose`
  (e.g. `fy17:267` carries `RAICES 11-2730462 * $83,000 St. Barnabas Hospital` in `program`).
- **78 rows with a completely clean `organization`** whose `program` or `purpose` carries absorbed
  awards. These fire **no advisory at all**. `fy18_schedule_c_awards.csv:409` is typical: the
  `organization` reads plainly `Consortium for Worker Education`, while `program` holds
  `"WSC 13-3564313 * $2,200,000 Consortium for Worker Education – Jobs to Build On** 13-3564313 * $5,154,200 HOPE Program, Inc., The"`.
  162 triples come out of these 78 rows.

Corpus-wide totals including both, year-scoped:

| Fiscal year | Distinct awards missing | Dollars missing |
|---|---:|---:|
| FY2016 | 31 | $11,529,565 |
| FY2017 | 226 | $36,657,702 |
| FY2018 | 227 | $31,301,254 |
| FY2019 | 57 | $4,535,700 |
| FY2022 | 2 | $25,000 |
| **Total** | **543** | **$84,049,221** |

Of which 495 awards / $75,681,759 are confirmed present in the Council's disclosure for the same
fiscal year (FY2016–19 subset).

**The `org_merged` count of 303 is therefore not the size of this defect.** It is 300 real rows plus
78 the advisory never sees, and it undercounts the dollars by roughly $17.7M.

---

## 6. Limits and unknowns — stated plainly

- **Dedup may undercount.** Distinct awards are counted by `(fiscal year, EIN, amount)`. Among real
  award rows, 7,045 of 43,664 such keys (16.13%) legitimately appear more than once — two members
  can fund the same org at the same amount in the same year. Collapsing 443 triples to 437 awards
  removed 6; some of those 6 may be genuinely distinct. The effect is small and in the direction of
  *understating* the loss.
- **VERIFIED vs INFERRED.** Every count, dollar total, and absence claim above is VERIFIED — each
  comes from a command run against the working tree, and the absences were re-checked by grep for
  the largest cases. The *interpretation* that a cross-year `(EIN, amount)` match is a different
  award rather than the same one is INFERRED, but it is supported by all three checks in §3.
- **The 8.5% not confirmed by disclosure is not evidence of a bad extraction.** Cleanly parsed rows
  miss disclosure at a similar rate (8–14%), consistent with the Phase 1 finding that disclosure is
  not a strict superset of Schedule C.
- **FY2020–FY2027 are essentially unaffected.** One triple in FY2022 ($15,000) and nothing else. The
  defect is concentrated in FY2016–FY2019, with the two malformed-EIN rows in FY2018 and FY2020.
- **Unknown: the two $88,855 Urban Health Plan awards.** Their EIN is printed malformed
  (`15-24042810`), so they cannot be keyed against `data/` or against disclosure by EIN. They are
  known-lost and unquantifiable by this method. Recovering them needs the source PDF, not this data.
- **Not attempted here:** whether these awards can be *recovered* into `data/` (Question 2), and
  whether the transparency-resolution files contain any of them. Transparency resolutions record
  mid-year designations and rescissions, a different universe from adopted-budget Schedule C awards,
  so they were deliberately excluded from the presence index.
