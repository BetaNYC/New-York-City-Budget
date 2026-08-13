---
title: Amount Audit — award amounts against the Council's expense disclosure
created: 2026-08-12
type: data-audit
status: active
tags: [nyc-budget, data-quality, audit, schedule-c]
---

# Amount Audit

**Report generated:** 2026-08-12  
**Data current as of:** 2026-08-12 (corpus at `data/fy*/schedule_c/`, disclosure at `source/expense-funding-disclosure/`)  
**Produced by:** `code/audit_amounts.py` — read-only, changes nothing

## Verdict, up front

**Report, do not touch. None of this is safely auto-correctable, and the script has no `--apply` path.** The reasoning is in [Is any of this auto-correctable?](#is-any-of-this-auto-correctable) below. Nothing was written to `data/combined/org_name_recovery_crosswalk.csv`: that file records substitutions *applied to the data*, and this pass applied none.

Of **62,213 award rows** carrying **$3,741,615,569**, **60,665 (97.51%)** have their amount corroborated by the Council's own same-year disclosure, covering **$3,551,858,231 (94.93% of dollars)**.

## What was compared

Each award row in `data/fy*/schedule_c/*.csv` (Schedule C awards plus the three appendices; initiative totals and reconciliation notes excluded) against `source/expense-funding-disclosure/funded_disclosure_FY####.xlsx` for the **same fiscal year**, joined on **(EIN, canonical organization name)**.

Three deliberate choices, each of which has burned this repo before:

- **EIN alone is not the key.** Fiscal sponsors pass funds through for many grantees — EIN 13-2612524 (Fund for the City of New York) carries 229 distinct names in this corpus. Keying on EIN alone would corroborate an award against a different organization's money.
- **Council member is not part of the key.** The disclosure workbooks are republished with the roster current at snapshot time, not the one that adopted the budget.
- **Headers are matched by case-insensitive substring**, because they drift across the series (`Amount ($` in FY2014; `Legal Name of Organization Requesting Funding` in FY2016; `Tax ID` from FY2021). The fiscal-conduit columns `FC EIN` / `Fiscal Conduit EIN` are explicitly excluded — they hold the pass-through sponsor's EIN, not the grantee's.

### One repair to the source, in memory only

Some disclosure rows are shifted one column left of their headers: citywide initiative awards with no council member, where the empty cell collapsed and dragged the rest of the row with it. Read naively they yield `ein="Cleared"`, `amount="DFTA"` and are dropped — which would make every one of our matching rows report a **phantom** shortfall.

Rows repaired in memory: **FY2016: 272**. The signature is a bare 9-digit number in the name slot **and** a non-empty non-numeric token in the EIN slot; in FY2016 it partitions 7,797 rows into 272 / 7,525 with nothing ambiguous in between. `source/` is never written.

## Results

| Verdict | Rows | % | Dollars | Meaning |
|---|---:|---:|---:|---|
| `exact` | 57,243 | 92.01% | $3,217,129,556 | our amount is one of the amounts the disclosure records for this (EIN, organization) that year |
| `name_variant` | 3,422 | 5.50% | $334,728,675 | amount corroborated under the same EIN that year; only the organization *text* differs from the disclosure's legal name. **Not an amount defect** |
| `rounding` | 18 | 0.03% | $5,685,403 | nearest disclosure amount is within $5 but not equal |
| `neighbour_bleed` | 3 | 0.00% | $1,322,333 | our amount is uniquely held, in the disclosure, by a *different* organization printed within 3 lines of ours |
| `ein_absent` | 419 | 0.67% | $18,308,251 | this EIN does not appear anywhere in that year's disclosure, so the amount can be neither confirmed nor contradicted |
| `unconfirmed` | 1,102 | 1.77% | $164,316,851 | the EIN is present that year, but not carrying this amount |
| `no_key` | 6 | 0.01% | $124,500 | our row has no EIN or no organization name — nothing to join on |
| **total** | **62,213** | | **$3,741,615,569** | |

### By fiscal year

| FY | rows | corroborated | % | rounding | bleed | unconfirmed + ein_absent |
|---|---:|---:|---:|---:|---:|---:|
| FY2015 | 652 | 535 | 82.1% | 1 | 1 | 115 |
| FY2016 | 335 | 290 | 86.6% | 9 | 0 | 36 |
| FY2017 | 364 | 330 | 90.7% | 2 | 0 | 32 |
| FY2018 | 902 | 828 | 91.8% | 0 | 0 | 71 |
| FY2019 | 846 | 760 | 89.8% | 0 | 0 | 86 |
| FY2020 | 2,841 | 2,682 | 94.4% | 0 | 0 | 159 |
| FY2021 | 6,120 | 5,860 | 95.8% | 3 | 0 | 257 |
| FY2022 | 5,674 | 5,533 | 97.5% | 1 | 0 | 138 |
| FY2023 | 5,904 | 5,742 | 97.3% | 0 | 1 | 161 |
| FY2024 | 9,279 | 9,087 | 97.9% | 0 | 0 | 192 |
| FY2025 | 9,566 | 9,444 | 98.7% | 0 | 1 | 121 |
| FY2026 | 9,752 | 9,598 | 98.4% | 0 | 0 | 153 |
| FY2027 | 9,978 | 9,976 | 100.0% | 2 | 0 | 0 |

## Off by cents / rounding

**18 rows**, total absolute drift **$18** — 13 where ours is higher, 5 where ours is lower.

The $5 threshold is not a guess. Measuring the distance from our amount to the nearest figure the Council records under the same EIN, across every row that is not an exact hit, the distribution has a clean gap right where the threshold sits:

| distance | rows |
|---|---:|
| exactly $1 | 18 |
| $2–$5 | 0 |
| $6–$99 | 3 |
| $100–$999 | 108 |
| $1,000+ | 994 |

Every one of these is an initiative allocation split N ways and rounded independently on each side. FY2015 New York Urban League is the clearest: the disclosure carries both $166,666 and $833,334 for the same organization — a fifth and the whole — and we carry $833,333.

| file | line | organization | ours | disclosure | Δ | §20 merged row |
|---|---:|---|---:|---:|---:|---|
| `fy15_schedule_c_awards.csv` | 648 | New York Urban League | $833,333 | $833,334 | -1 | — |
| `fy16_schedule_c_awards.csv` | 69 | Belmont Arthur Avenue Local Developmen | $29,730 | $29,729 | +1 | — |
| `fy16_schedule_c_awards.csv` | 70 | Bridge Street Development Corporation | $29,730 | $29,729 | +1 | — |
| `fy16_schedule_c_awards.csv` | 71 | Brighton Neighborhood Association, Inc | $29,730 | $29,729 | +1 | — |
| `fy16_schedule_c_awards.csv` | 73 | Central Astoria Local Development Coal | $29,730 | $29,729 | +1 | — |
| `fy16_schedule_c_awards.csv` | 74 | Clinton Housing Development Company, I | $29,730 | $29,729 | +1 | **yes** |
| `fy16_schedule_c_awards.csv` | 75 | El Barrio Operation Fight Back, Inc. 1 | $29,730 | $29,729 | +1 | **yes** |
| `fy16_schedule_c_awards.csv` | 76 | Good Old Lower East Side, Inc. | $29,730 | $29,729 | +1 | — |
| `fy16_schedule_c_awards.csv` | 83 | Neighborhood Housing Services of East  | $29,731 | $29,730 | +1 | — |
| `fy16_schedule_c_awards.csv` | 94 | Strycker's Bay Neighborhood Council, I | $29,731 | $29,730 | +1 | **yes** |
| `fy17_schedule_c_awards.csv` | 163 | Good Old Lower East Side, Inc. 13-3311 | $29,730 | $29,729 | +1 | **yes** |
| `fy17_schedule_c_awards.csv` | 209 | Bronx Defenders 13-3931074 * $2,076,66 | $2,076,666 | $2,076,667 | -1 | **yes** |
| `fy21_schedule_c_awards.csv` | 536 | Center for Employment Opportunities | $689,361 | $689,360 | +1 | — |
| `fy21_schedule_c_awards.csv` | 1763 | Girls for Gender Equity, Inc. | $98,438 | $98,437 | +1 | — |
| `fy21_schedule_c_awards.csv` | 1770 | Latinas on the Verge of Excellence | $26,437 | $26,438 | -1 | — |
| `fy22_schedule_c_awards.csv` | 512 | Osborne Association, Inc., The | $1,603,868 | $1,603,867 | +1 | — |
| `fy27_schedule_c_awards.csv` | 4682 | Osborne Association, Inc., The | $14,999 | $15,000 | -1 | — |
| `fy27_schedule_c_awards.csv` | 4724 | Selfhelp Community Services, Inc. | $44,999 | $45,000 | -1 | — |

### Why even these $5 gaps must not be closed automatically

**5 of these 18 rows are `org_merged` rows** — their `organization` field still carries a second organization's EIN or dollar figure, the boundary loss of DATA-ANOMALIES.md §20. On those rows the $1 gap is not rounding at all. It is a coincidence of an even two-way split, and the amount on the row belongs to the *other* organization.

`fy17_schedule_c_awards.csv:209` is §20's own worked example, and this audit reached it from the opposite direction. The row reads:

```
organization: Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders Services
ein:          113305406   (Brooklyn Defenders)
amount:       2076666     (Bronx Defenders' share)
```

The disclosure records $2,076,667 for EIN 113305406. A tolerant fixer would see a $1 gap, call it rounding, write $2,076,667, and produce a row that passes every check while the award it swallowed is still missing and the evidence of the swallow is gone. **A defect that is visible is worth more than a figure that is plausible.** This one class of finding is on its own sufficient to settle the question below.

## Amount belonging to a different organization

**3 rows.** Our amount is held, in the Council's record, by exactly one organization — and that organization is printed within 3 lines of ours in the same file. Uniqueness is what makes the claim worth making: $5,000 is held by hundreds of grantees a year, so proximity alone proves nothing.

| file | line | our organization | our amount | belongs to |
|---|---:|---|---:|---|
| `fy15_schedule_c_awards.csv` | 646 | Coalition for Asian American Child | $833,333 | EIN 133573852 |
| `fy23_schedule_c_awards.csv` | 585 | Mayor's Office of Criminal Justice | $325,000 | EIN 132612524 |
| `fy25_schedule_c_awards.csv` | 3465 | Community Service Society of New Y | $164,000 | EIN 133824852 |

These are the same boundary loss as §20 — the Schedule C parser absorbing one award into the next when an asterisk or a program name sits between the EIN and the dollar figure — reached here from the opposite direction, by noticing that the Council attributes the figure to a neighbour. The count is small because the test is strict on purpose: the amount must be *uniquely* held. Rows where the swallowed award happened to be an even split of the same pot land in the rounding table above instead, which is where the more dangerous cases turn out to be.

## Is any of this auto-correctable?

**No. Audit only.** Four reasons, in descending order of how much they should worry you.

**1. The two sources are different vintages of the truth, not two attempts at one figure.** Our amounts come from the adopted Schedule C, published in June of the budget year. The disclosure workbooks are administrative snapshots republished later — their sheet tabs say so: `FY19 (4-14-21)`, `FY20 (06-16-2022)`, `FY24 (06-08-26)`. When they disagree, the Council revising an award after adoption is at least as likely as this repo mis-parsing one. Copying their figure over ours would make the dataset agree with a spreadsheet and stop agreeing with the PDF it cites as its source — and would erase the only evidence that the number ever moved. That is a loss of information dressed up as a correction.

**2. The rounding cases have no correct answer, and 5 of 18 are not rounding at all.** $833,333 against $833,334; $29,730 against $29,729. Both sides are dividing an initiative pot and rounding, and ours is not systematically wrong — 13 high, 5 low. No rule picks a winner, so any rule applied here would be invented. Worse, on the 5 `org_merged` rows the $1 gap is a coincidence hiding a swallowed award, and closing it would destroy the evidence — see above.

**3. On the bleed rows, there is nothing to write.** §20's defect is a *missing* row: an award got absorbed into its neighbour. The surviving row has organization A's name against organization B's money, and the fix is to recover the lost row, not to overwrite a number. Substituting an amount would make the row look sound while the award it swallowed stayed missing — converting a visible defect into an invisible one. That is the single worst outcome available here.

**4. `unconfirmed` and `ein_absent` (1,521 rows) are mostly not defects at all.** The repo's own source-comparability study found row capture against the disclosure is materially below 100% in every fiscal year. Absence from the disclosure is absence of evidence. Treating it as evidence of a wrong amount, and 'fixing' it, would fabricate figures for awards the disclosure simply does not list.

The bar this repo already set for a fix — a substitution resolvable to exactly ONE candidate from the Council's own record — is met by none of these classes. Not one.

## Corroboration of earlier passes

Cross-referencing `data/combined/org_name_recovery_crosswalk.csv` against these verdicts, as an independent check on repairs already applied:

| earlier fix | rows | amount corroborated afterwards | remainder |
|---|---:|---:|---|
| `member_bleed` | 1,083 | 1,070 | 4 ein_absent, 9 unconfirmed |
| `org_merged` | 239 | 228 | 1 ein_absent, 10 unconfirmed |
| `org_prose` | 1,076 | 1,062 | 4 ein_absent, 10 unconfirmed |
| `wrong_ein` | 20 | 20 | — |

The `wrong_ein` result is the meaningful one: those 20 rows were re-keyed on (name, amount), and 20 of 20 now agree with the disclosure on a key that *includes the EIN the pass wrote*. That is confirmation arriving from a direction the fix itself did not use.

## Limits of this audit

- **FY2013 has no machine-readable disclosure.** It ships as `.xls` — a genuine OLE2 compound document (magic `d0cf11e0`), not a renamed zip — and no standard-library module reads BIFF. It costs nothing here: this corpus holds no FY2013 award rows, only initiative totals.
- **Set membership, not multiset.** A row is corroborated if its amount appears among that organization's disclosure amounts for the year. Where we hold three $5,000 rows and the disclosure holds one, all three read `exact`. That is a duplication question, not an amount question, and it is out of scope here.
- **`name_variant` is a floor, not a ceiling.** It corroborates the amount under the EIN without asserting the two names are the same organization. For a fiscally-sponsored award they may not be.
- **Nothing here establishes completeness.** This audit asks whether the amounts we hold are right, never whether we hold all the awards. Those are different questions and the second one has a worse answer.

Row-level detail for every non-corroborated award: `data/AMOUNT-AUDIT-findings.csv` (1,548 rows).

