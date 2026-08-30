---
title: "PARKED — the absorbed-award investigation, and the generator #57 says is missing"
created: 2026-08-29
type: research-index
status: parked
tags: [nyc-budget, schedule-c, absorbed-awards, parked]
---

# PARKED — absorbed Schedule C awards

**Parked 2026-08-29.** This branch is held, not abandoned, and not intended to merge as-is.
Read this file first.

Held because **it contains work that exists nowhere else** — six files that are on this branch and
not on `main`. Everything else here duplicates `main` or is *behind* it.

Entry point for the wider effort: **[#60](https://github.com/BetaNYC/New-York-City-Budget/issues/60)**.

---

## The reason this branch was not deleted

[#57](https://github.com/BetaNYC/New-York-City-Budget/issues/57) FOLLOW-UP 3 states:

> `data/recovered/schedule_c_absorbed_awards.csv` is built by `code/build_recovered_awards.py` from
> `code/absorbed_award_candidates.csv` — **and that candidates file has no generator in the repo.**
> It was produced during investigation and committed as data. Every other artifact here regenerates
> from `source/`. This one cannot, which breaks the repo's own contract that the pipeline is
> reproducible.

**The generator is on this branch.** `code/prototype_recover_absorbed.py`, line 49:

```python
OUT = "research/missing-absorbed-awards/absorbed_award_candidates.csv"
```

Verified 2026-08-29: this branch's `absorbed_award_candidates.csv` is **byte-identical** to the
`code/absorbed_award_candidates.csv` that `main` ships. 445 rows, 25 columns.

**What is NOT verified:** the script has not been re-run and its fresh output diffed against the
committed CSV. Identical bytes prove the file came from here; they do not prove the script still
reproduces it against today's `data/` tree — which has moved considerably since 2026-08-12.
**That re-run is the work that would actually close FOLLOW-UP 3**, and it is maybe ten minutes.

Note the path in the script points at `research/`, while `main` ships the file under `code/`. Whoever
closes this should decide which location is canonical and make the script write there.

---

## What is here

Four investigation questions, each with its report, plus three scripts and two datasets.

| file | what it is |
|---|---|
| `INVENTORY.md` | **Q1** — parse the 303 `org_merged` rows and extract every absorbed (EIN, amount, name) triple |
| `RECOVERABILITY.md` | **Q2** — can the absorbed awards be recovered, and how confidently? |
| `RECONCILIATION.md` | **Q3** — what recovering them does to reconciliation |
| `PROVENANCE.md` | **Q4** — how to mark provenance if they are published as rows |
| `RECOMMENDATION.md` | the synthesis: publish the 445 absorbed awards as a sidecar, after a label fix |
| `inventory_absorbed.py` | writes `absorbed_triples_inventory.csv` (648 rows) |
| `prototype_recover_absorbed.py` | **the generator** — writes `absorbed_award_candidates.csv` (445 rows) |
| `measure_reconciliation.py` | Q3's measurement |
| `verify_adversarial.py` | adversarial re-verification of the four investigations |
| `absorbed_award_candidates.csv` | 445 rows — identical to what `main` ships |
| `absorbed_triples_inventory.csv` | 648 rows — the raw triples |

---

## Do not merge this branch as-is

Its `data/` tree is a **2026-08-12 snapshot that predates [#56](https://github.com/BetaNYC/New-York-City-Budget/pull/56)**. Merging would delete 26,335 lines from
`data/recovered/schedule_c_appendix_recovered.csv` and revert thousands of repaired cells. The diff
against `main` reads `-46,393` lines for exactly this reason.

**Take the six files, not the branch.** Cherry-pick or copy `research/missing-absorbed-awards/` and
`code/prototype_recover_absorbed.py` onto a fresh branch off current `main`.

---

## The four sibling branches that were NOT kept

`audit/amounts-5ca2`, `fix/member-bleed`, `fix/initiative-reconciliation` and
`fix/residual-org-names` were local-only snapshots from the same 2026-08-12 era. Checked
2026-08-29: **each had zero files that do not also exist on `main`**, and each was *behind* main
rather than ahead — their work landed through #56. They were deleted rather than pushed.

This branch was kept because it is the one that failed that test.
