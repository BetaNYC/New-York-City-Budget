---
title: "PARKED — the adversarial audit of PR #56, and the sweep that fed it"
created: 2026-08-29
type: research-index
status: parked
tags: [nyc-budget, schedule-c, audit, adversarial, parked]
---

# PARKED — adversarial audit toolkit

**Parked 2026-08-29.** Held, not abandoned. Read this before the rest.

These 36 files were **untracked working files in two throwaway worktrees**
(`~/Code/NYCB-adversarial`, `~/Code/NYCB-sweep`) and existed on no remote. A
`git worktree remove --force` would have destroyed all of them. They are pushed here so that
cannot happen.

Entry point for the wider effort: **[#60](https://github.com/BetaNYC/New-York-City-Budget/issues/60)**.

---

## What this is

`AUDIT.md` (29 KB) is the **adversarial audit of [PR #56](https://github.com/BetaNYC/New-York-City-Budget/pull/56)** — the 5,450-cell repair now on `main`. Its own scope line:

> every repair applied on this branch: 2,418 crosswalk substitutions, two sidecars, four repair
> scripts, two gates. **Mode:** audit only. Nothing under `data/` was modified.

Verdict: **safe to merge with caveats**, after two one-line fixes and three documentation
corrections. That verdict is why #56 landed. **The evidence behind it has been on one laptop ever
since.**

The 34 scripts are what produced it, plus `sweep.py` (26 KB) — the systematic corpus sweep from the
sibling worktree, whose findings are [#57](https://github.com/BetaNYC/New-York-City-Budget/issues/57) FOLLOW-UP 4.

---

## Why it is worth keeping

**It does not trust the thing it audits.** `xlsxlib.py` is an independent stdlib xlsx reader written
*for* the audit, with `test_xlsxlib.py` as its self-check and `reader_diff.py` comparing it against
the repair scripts' reader. A second opinion about the source, not a re-run of the first.

**It attacks the guards.** `break_the_gate.py` — *"construct corruptions that
`code/verify_crosswalk.py` accepts."* `detector_gap.py` found the repair pipeline and the validator
use **different definitions of `org_prose`**. `verify_crosswalk.py` is on `main` today with no
adversarial tests of its own.

**It scores the whole population, not a sample.** `corroborate_all.py` — *"score EVERY applied
repair against three sources independent of the repair."*

**It asks whether the repairs made anything worse.** `overwrote_good.py` — *"find repairs that
replaced a name that was ALREADY CORRECT."* Plus `latent_risk.py`, `false_negatives.py`,
`member_fills.py`.

**Three scripts answer open tickets directly:**

| script | ticket |
|---|---|
| `appendix_overlap.py` | *"do the per-year appendix files duplicate awards already in the main body?"* — **#57 blocker 2** |
| `candidates_audit.py` | audits `code/absorbed_award_candidates.csv` — **#57 FOLLOW-UP 3** |
| `sweep.py` | produced **#57 FOLLOW-UP 4**'s four defect classes |

#57 blocker 2 was re-derived from scratch on 2026-08-29, badly, and retracted — while a script
written to answer it sat untracked in a worktree.

---

## How to use it

Everything here is **read-only by design** and was written against branch `fix/recover-lost-grantee-names` @ `9c1a99d`, merge base `902568f`. The corpus has moved since — #56 merged, and
`fix/parser-anchor-fy15-fy20` changes it again. **Expect paths and counts to need updating; expect
the method to still hold.**

Nothing here is a candidate for `main` as-is. It is investigative tooling, kept because rebuilding
it would cost more than reading it.

---

## Provenance

Recovered from the untracked working trees of two worktrees on `janus`, 2026-08-29, during a branch
cleanup that removed 22 other local-only branches. This branch is based on `9c1a99d`, the audited
head — **not** on current `main`, so its `data/` tree is a pre-#56 snapshot. **Do not merge it.**
Take the files.
