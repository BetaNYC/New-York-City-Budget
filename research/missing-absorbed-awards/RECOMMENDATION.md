---
title: "Absorbed Schedule C awards — recommendation"
created: 2026-08-12
type: research-finding
status: complete
tags: [nyc-budget, schedule-c, data-quality, recommendation]
---

# Absorbed Schedule C awards — recommendation

**Report generated** 2026-08-12
**Data current as of** 2026-08-12 (worktree `~/Code/NYCB-missing`, branch `research/missing-absorbed-awards`, HEAD `27d693c`)
**For** Noel Hidalgo
**Inputs** `INVENTORY.md` (Q1), `RECOVERABILITY.md` (Q2), `RECONCILIATION.md` (Q3), `PROVENANCE.md` (Q4), and an adversarial re-verification of all four
**Verified for this document by re-running** `research/missing-absorbed-awards/verify_adversarial.py` (self-check 9/9) plus one independent measurement of the advisory blind spot

---

## The decision, in five lines

**Yes — publish them.** The evidence is strong enough, and stronger than the evidence behind
things already shipped in this repo.

**But publish them as a separate file** (`data/recovered/schedule_c_absorbed_awards.csv`), not as
new rows inside the per-year CSVs, and **not in the same release as an MCP index change**. Nothing
already published moves. A journalist who cited last month's numbers can still reproduce them.

**And fix one thing first.** A *different* parser defect files whole provider tables under the
wrong initiative. Until it is fixed, the recovery's own quality check reports false failures on
exactly the initiatives the recovery repaired — and a false failure reads like "the recovery
double-counted," which would wrongly kill a sound plan.

**The bigger finding is not the recovery.** Two things it turned up matter more, and one of them is
an error in data you are shipping *right now*. See §7.

---

## 1. How many awards are missing, and worth how much

**445 awards. $66,546,221.** Both VERIFIED — reproduced just now by `verify_adversarial.py`, and
independently reached by three separately-written extractors that agree exactly.

The uncertainty is one-directional: **this is a floor, not an estimate.**

| | Awards | Dollars | Confidence |
|---|---:|---:|---|
| Independently corroborated (Council disclosure and/or transparency resolutions, same fiscal year) | 411 | ~$60.9M | VERIFIED — 92.4%, re-run today |
| Extracted but uncorroborated | 34 | ~$5.7M | real per reconciliation, unconfirmed per any second source |
| **In-scope total (the 303 flagged rows)** | **445** | **$66,546,221** | **VERIFIED** |
| Known misses inside those rows (3 hidden by a program name, 2 with a mangled 10-digit EIN) | +5 | +$231,710 | VERIFIED, not recoverable by the current pattern |
| Same defect in rows that fire **no advisory at all** — absorbed text landed in `program`/`purpose` instead of `organization` | +~160 | +~$18.1M | MEASURED TWICE (77 rows/$18,073,625 in my run; 78 rows/$18.1M in the adversarial pass) |
| **Full extent of the defect, corpus-wide** | **~610** | **~$84.9M** | INFERRED from two independent measurements |

Read it as: **at least $66.5M is provably missing; the true figure is nearer $85M.** The dollar
corroboration split ($60.9M / $5.7M) is carried from the adversarial report; I re-ran the counts
(411/445), not the dollar partition.

Scale check: the affected years are FY2016–FY2019. FY2017 alone is missing **$27.9M** against
$89.9M of award rows the parser did keep — roughly a quarter of that year's itemized awards are
absent from the dataset.

---

## 2. Should they be added at all?

**Yes.** Three reasons, in descending strength.

**(a) The dollars pass a test that a wrong answer cannot pass.** Where the PDF itemizes an
initiative, the itemization is exhaustive — the provider list sums to the printed initiative
amount. Adding the absorbed awards closes **32 initiative gaps to exactly $0**. Shuffle the same
absorbed totals across the same 87 initiatives 20,000 times and you get a mean of 0.77 closures and
never more than 6. `P < 0.00005`. The closing sums are things like $6,206,332 and $9,355,069 — not
round numbers you can hit by luck.

**(b) An independent document confirms 92.4% of them,** at exact same-year EIN + amount. For
comparison, rows the parser *did* parse cleanly confirm against the same workbooks at 86–92%. The
absorbed awards are as well-attested as the ones already published.

**(c) These two lines of evidence fail independently.** Reconciliation uses only the PDF. Disclosure
uses only the workbooks. If either were systematically wrong, the other would still stand. That is
why I am comfortable at "publish" rather than "investigate further."

### The strongest argument against

*You are extracting from a text layer whose failure mode you have just proven scrambles field
associations — and publishing the result into a dataset journalists cite.*

This is a real argument and it is not fully answerable. The same column shift that caused the
absorption also decouples a **name** from its EIN: ~5% of extracted names disagree with the
disclosure record for the same EIN and amount. And 34 awards ($5.7M) have no second source at all.
Publishing a row asserts that an award existed. A wrong assertion is worse than a documented
absence — your framing, and I agree with it.

What defuses it, and why I still say publish:

- **The failure is in the name, not the money.** If amounts had shifted along with names,
  same-year corroboration would be near-random instead of 91.7%. The amount travels with its EIN.
- **So do not take names from the extraction.** Take the grantee name from the disclosure workbook
  via the (fiscal year, EIN, amount) join — 95.1% resolve to exactly one candidate, 0.7% are
  ambiguous (all one organization under two spellings). Where there is no disclosure row, **leave
  the name blank** rather than use the extracted one.
- **The 34 uncorroborated awards get a status column, not a deletion.** They stay in the file,
  marked, so the file never overstates what it knows.
- **Nothing published changes.** A separate file cannot corrupt an existing citation.

---

## 3. Does the reconciliation evidence support the plan?

**Yes, and this is the load-bearing result.** I re-derived it today rather than take it on report.

```
joined initiatives carrying >=1 absorbed award: 87
gaps closed to EXACTLY $0 by the recovery     : 32
permutation null (20k shuffles, seed 7): mean=0.77  P(null>=observed)=0.00000
```

Three things make this more than a statistic.

**It is also the double-count test.** If the absorbed text were a duplicate rendering of an award
already in the data, adding it would push initiatives *past* their printed totals. It does not. All
32 movements come from the short side and land on or before zero, and the recovery breaks **none**
of the initiatives that already balanced.

**All three apparent overshoots were opened, and none is a double count.**

| Case | Residual | What it actually is |
|---|---:|---|
| FY2016 Community Consultant Contracts | −$12 | 30 existing + 7 recovered = **37 awards**, and $1,100,000 ÷ 37 = $29,729.73. The recovery produces exactly the count an even 37-way split requires. The $12 is rounding in the Council's own printing. This *confirms* the recovery. |
| FY2018 Viral Hepatitis Prevention | −$396,978 | A separate label defect. Four rows are the Q–W tail of the Maternal Health list mis-filed under the next header. Reattached, both initiatives are **short**. |
| FY2019 HIV/AIDS Faith-Based | −$36,019 | Same defect, worse. All 13 rows are Maternal grantees; the initiative has **zero** genuine rows. Corrected, it is $525,799 short. |

**Direct double-count check: 2 of 445 (0.45%, $43,500).** Both FY2018, both listed by file and line.
They need a human call — the same organization at the same amount can legitimately be two council
members' awards — so they get held out, not applied blind. Sixteen same-EIN/different-amount cases
are not a risk: a different amount is a different award, which is precisely why the key is
(EIN, amount) and not EIN alone.

**The premise that had to be corrected:** the printed *category* total is not a reconciliation
target and cannot be made into one. Award rows cover 27%–64% of printed category dollars in the
affected years **by design** — most initiatives are lump appropriations the PDF never itemizes
(FY2017 `SPEAKER'S INITIATIVE`, $30,075,000, zero award rows because the document prints none).
Coverage climbs monotonically to 92% by FY2027 as the Council itemizes more. That gap is real,
structural, and tells you nothing about this defect.

---

## 4. If yes: exactly how

### Provenance — a separate file, per-field marking

`data/recovered/schedule_c_absorbed_awards.csv`. Not merged.

The reason is a measured fact, not a preference: **a recovered row is mixed-provenance at the field
level.** The EIN and amount come first-hand from the same PDF text as every other row (400 of 404
embedded EINs already sit beside their amount in text the parser read). The organization name comes
second-hand from the disclosure workbook. Category and initiative are inherited from the position of
the row that swallowed it.

A row-level `source = recovered` flag would say the *dollars* are second-hand. They are not — and
that is the direction that damages the repo's determinism claim. So: **one provenance value per
field, from a closed vocabulary** (`schedule_c_pdf` / `council_disclosure` / `host_row_context`),
empty where unknown.

Field-by-field, what can and cannot be supplied:

| Field | Source | Fill |
|---|---|---|
| `ein`, `amount` | Schedule C PDF text | 100% |
| `fiscal_year` | Schedule C PDF text | 100% |
| `organization` | Council disclosure, joined on (FY, EIN, amount) | 100% of tier A/B; blank for the 19 with no disclosure row |
| `agency`, `purpose` | Council disclosure | 100% / 100% for tier A |
| `category` | Inherited from the host row — mark **inferred** | 100%, inferred |
| `initiative` | **Leave blank.** The host row's own `initiative` is itself 18% wrong. A wrong value is invisible downstream; a blank reads as "unknown." | 0% |
| `member` | Disclosure, where present | 20% — **structural**, not a failure: 404 of 445 are citywide initiatives with no sponsoring member. **Never backfill a member name.** |
| `status` | This recovery | 100% — `corroborated` / `uncorroborated` / `held_for_review` |

### What breaks downstream

**With the separate file (recommended): nothing.** No existing CSV changes shape. `build_combined.py`
does not see it. The MCP index does not see it. The viz does not see it. The CI version guard is not
tripped.

The two things you must not skip, because a sidecar's whole risk is being ignored:

1. **Register it in `code/validate_data.py`** — one `detect_type` branch, one `TYPES` entry.
   `validate_tree` silently skips files it does not recognize. An unregistered data file is
   ungraded, which is the exact shape of the defect we are fixing.
2. **Add the README row in the same commit.** Precedent: `data/combined/org_name_recovery_crosswalk.csv`
   has 1,060 rows, ships today, and appears nowhere in the README. A file nobody can find is a file
   nobody can audit.

**For contrast, merging into the per-year CSVs (option a) breaks four things:** `validate_data.py`
hard-fails on an extra column (verified by running it against a scratch copy); `build_combined.py`
drops the column unless its explicit 10-name list is edited; the MCP's CSV reader ignores unknown
columns entirely, so the mark reaches no consumer until the table, the INSERT, and `AwardRow` are
all extended — and `searchAwards` is `SELECT *`, so that changes the output shape of every award
tool; and FY2017's published row count stops matching prior figures with no visible seam.

**MCP indexing is a later, separate decision.** If you make it, the cheapest correct mechanism
already exists: `source_table = 'recovered'`, the discriminator added in 1.4.0 for the appendix
rows. No schema change, no output-shape change, and every previously published total stays
interpretable as a named slice.

### Sequence and effort

Estimates, not measurements. Each step is independently shippable.

| # | Step | Why here | Effort |
|---|---|---|---|
| 0 | **Ship the initiative-level reconciliation as a permanent check** | It is a pass/fail signal the award stream has never had. It would have caught this defect (FY2017 balances at 24% against a 44–77% norm). It found two more defects in an afternoon. One join against data already in the repo. | ~half day |
| 1 | **Fix the initiative-label misassignment** — provider tables filed under the wrong initiative | **BLOCKING.** Do this before step 3 or the recovery's own check reports false overshoots on the initiatives it just repaired. | ~1 day |
| 2 | **Fix the category-label shift** (positional map vs. text match, FY2016–FY2021) | Independent, small, and any consumer keying on `category` is reading the wrong label today. | ~2 hours |
| 3 | **Write the recovered-awards file** | The join exists in prototype form. Add the missed `program-name-between-EIN-and-amount` shape; hold out the 2 collisions; mark the 34 uncorroborated. | ~1 day |
| 4 | **Extend to the ~160 unflagged awards** (~$18.1M) | Same defect, `program`/`purpose` fields, no advisory fires. Widen the advisory regex too — it only matches hyphenated EINs and misses 45 bare 9-digit ones. | ~half day |
| 5 | *(separate decision)* MCP index + CHANGELOG + version bump | Not in the same release as step 3. | — |

---

## 5. The honest alternative, if you decide against

**Publishing the inventory as a documented gap is legitimate**, and I would not argue hard against
it. `DATA-ANOMALIES.md` §20 already says "Not fixed."

But be clear about what it saves: **almost nothing.** The inventory has to be built either way — the
same extraction, the same join, the same guards. Once it exists, emitting a CSV instead of a
markdown table is a print statement. The gap-only option is the recommended option with the
machine-readable half deleted, and the deletion is the only difference.

Its real cost is that ~445 awards stay discoverable only by reading prose, and the MCP and viz stay
wrong in the years where the defect is most concentrated (FY2017–FY2018 = 239 of the 303 rows).

**If you go this way, still do steps 0–2.** They are not conditional on the recovery, and step 0 is
the highest-value item on the whole list regardless of what you decide here.

---

## 6. What would need to be true for me to be wrong — and how to check

Ordered by how much damage each would do.

**1. The absorbed text is a duplicate rendering, not a separate award.** Then adding it
double-counts $66.5M.
*Why I don't believe it:* only 2 of 445 exist as rows anywhere in the same year, and if they were
duplicates the 32 exact closures would be 32 overshoots instead.
*How to check, ~15 minutes:* open the FY2017 Adopted Budget Schedule C PDF at **Discretionary Child
Care**, printed $9,355,069. Count the provider rows. There should be **11**. Our data has **5**.
The six absorbed ones make up the difference exactly. If the PDF shows 5, I am wrong and you should
stop everything.

**2. The printed initiative amount is not exhaustive** — it includes money the provider list never
itemizes. Then the closures are coincidence.
*Why I don't believe it:* 24%–77% of joined initiatives already balance **to the dollar** with no
repair at all, in every year including ones with no absorbed awards. That test passes independently
of the recovery.
*How to check:* `python3 research/missing-absorbed-awards/measure_reconciliation.py` — the
already-balance column is right there, per year.

**3. The disclosure workbooks are not an independent source.** If Schedule C and the disclosure
files are both generated from one internal Council database, "92.4% corroborated" is weaker than it
sounds.
*This one I genuinely cannot rule out* — I have no provenance statement from the Council. But the
reconciliation evidence does not use disclosure at all, so the conclusion survives even if this is
true. Worth asking Finance Division directly.

**4. Amounts shifted along with names.** Then the (EIN, amount) key is fiction.
*Why I don't believe it:* corroboration would collapse toward random. It is 91.7%.
*How to check:* `python3 research/missing-absorbed-awards/verify_adversarial.py --selfcheck`, then
pick five rows from the output CSV and find them by hand in the Council's workbook.

**5. Cross-year (EIN, amount) matches are the same award, not different ones.** This is the single
inference the whole inventory rests on. If wrong, the count drops from 443 missing to 153.
*Why I don't believe it:* 427 of the 443 are organizations with **no row at all** in that fiscal
year — not a different award, no award. And the same-year disclosure confirmation is 91.7%.

**Full reproduction, ~10 minutes:**

```bash
cd ~/Code/NYCB-missing                  # branch research/missing-absorbed-awards
python3 research/missing-absorbed-awards/verify_adversarial.py --selfcheck
python3 research/missing-absorbed-awards/verify_adversarial.py
python3 research/missing-absorbed-awards/measure_reconciliation.py
python3 research/missing-absorbed-awards/inventory_absorbed.py --self-check
```

---

## 7. Two things that matter more than the recovery

**A. Wrong grantee names are shipping in already-published rows, right now.**

The same column shift that causes absorption also decouples a name from its EIN *without producing
any advisory*. `fy17_schedule_c_awards.csv:160` reads organization "Central Astoria Local
Development Coalition, Inc." against EIN `112412584`, which is Housing & Family Services of Greater
New York. Clean row. No flag. Wrong grantee, published, citable.

Corpus-wide, **409 unflagged rows (0.7%)** carry an organization name that disagrees with their
unique same-year disclosure row. Most are benign spelling variants and renames. Some are not.

**This is worse than the missing awards.** An absence is honest. A wrong name is an assertion — and
this dataset is on npm and cited by journalists. It deserves its own audit, ahead of the recovery.

**B. The award stream has never had a pass/fail check, and now it can.**

The initiative-level reconciliation is one join against data already in the repo. It would have
caught this defect in FY2017. It caught two more defects while being built. Ship it as a permanent
advisory even if you ship nothing else on this list.

---

## Appendix — where the numbers disagree, and which I used

Four investigations plus an adversarial pass produced slightly different counts. Stated plainly so
nobody thinks a discrepancy was hidden:

| Quantity | Range across passes | Used here | Why |
|---|---|---|---|
| Absorbed awards | 437 / 442 / 445 | **445** | 437 dedupes on (FY, EIN, amount), which collapses genuinely distinct awards — FY2017 line 27 is three council members each giving $20,000 to the same organization. 442 misses three awards hidden behind a program name. |
| Dollars | $66,376,721 / $66,492,221 / $66,546,221 | **$66,546,221** | Same reason. |
| Disclosure confirmation | 86.3% / 91.5% / 91.7% | **91.7%** | Re-run today. The 86.3% figure is the strictest tier (exactly one same-year row) and excludes valid multi-row matches. |
| Any independent source | not measured / 92.4% | **92.4%** | The transparency resolutions add 73 confirmations nobody else counted. |
| Advisory blind spot | $17.7M / $18.1M | **~$18.1M** | My own run: 77 rows, 160 pairs, $18,073,625. |
| Double-count risk | 2 | **2** ($43,500) | Unanimous, and re-verified today. |
| Initiative gaps closed | 32 | **32** | Unanimous, re-verified today, `P < 0.00005`. |

Two claims from the earlier passes are **not** carried into this recommendation because they did not
survive re-checking, and neither affects the decision:

- The handed-down "248 of 303 confirmed, 55 absent, all FY2016" does not reproduce under any
  combination of reader, scope, and status filter. Treat it as unverified.
- One pass attributed a `recover_org_names.py` xlsx bug to sparse cells costing FY2016 248 keys. The
  adversarial pass found the real cause is a column *header* mismatch (FY2016's name column is
  headed differently and is never looked up; FY2014's amount column is headed `Amount ($`). Blast
  radius on the 1,060 already-applied names is small — 1,046 are confirmed by the same year's
  workbook — but that script's year-agnostic lookup is a latent version of the cross-year collision
  problem and should be revisited on its own.
