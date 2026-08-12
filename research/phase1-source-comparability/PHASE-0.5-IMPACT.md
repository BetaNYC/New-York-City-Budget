---
title: "Phase 0.5 — Schedule C appendix ingest: before/after impact and design writeup"
created: 2026-08-12
type: research
status: complete
tags: [nyc-budget, mcp, schedule-c, data-integrity]
---

# Phase 0.5 — loading the Schedule C appendix into the MCP index

**Report generated:** 2026-08-12
**Data current as of:** 2026-08-12 (committed `data/` tree at `de251b5`; no re-parse, no network)
**Package:** `@betanyc/nyc-budget-mcp` 1.3.1 → **1.4.0**
**Branch:** `research/phase1-source-comparability` (not merged, not tagged, not published)

---

## What changed in one sentence

28,575 Schedule C appendix rows that were parsed, QA'd, committed, and reaching **no consumer**
are now in the MCP index and returned by the award tools, discriminated by a new `source_table`
column, and every already-published main-body figure is still reproducible exactly.

## BEFORE / AFTER — per fiscal year

Row counts and `SUM(amount)` from `mcp/data/budget.db`, built by `npm run build-index`.
"BEFORE" is the v1.3.1 index; "AFTER" is v1.4.0. **No main-body row changed** — the BEFORE
column is exactly what `source_table = 'schedule_c'` returns today.

| FY | rows BEFORE | $ BEFORE | + appendix rows | + appendix $ | rows AFTER | $ AFTER | row Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 652 | $73,199,837 | — | — | 652 | $73,199,837 | — |
| 2016 | 335 | $89,917,012 | — | — | 335 | $89,917,012 | — |
| 2017 | 364 | $89,901,487 | — | — | 364 | $89,901,487 | — |
| 2018 | 480 | $102,716,956 | +422 | +$4,419,275 | 902 | $107,136,231 | +87.9% |
| 2019 | 846 | $181,026,931 | — | — | 846 | $181,026,931 | — |
| 2020 | 2,841 | $258,762,385 | — | — | 2,841 | $258,762,385 | — |
| 2021 | 1,810 | $202,070,188 | +4,310 | +$49,799,000 | 6,120 | $251,869,188 | +238.1% |
| 2022 | 1,492 | $222,556,943 | +4,182 | +$49,799,000 | 5,674 | $272,355,943 | +280.3% |
| 2023 | 1,848 | $262,419,214 | +4,056 | +$49,789,000 | 5,904 | $312,208,214 | +219.5% |
| 2024 | 5,368 | $400,663,574 | +3,911 | +$49,799,000 | 9,279 | $450,462,574 | +72.9% |
| 2025 | 5,646 | $412,985,110 | +3,920 | +$49,799,000 | 9,566 | $462,784,110 | +69.4% |
| 2026 | 5,838 | $487,287,245 | +3,914 | +$49,794,000 | 9,752 | $537,081,245 | +67.0% |
| 2027 | 6,118 | $605,111,412 | +3,860 | +$49,799,000 | 9,978 | $654,910,412 | +63.1% |
| **TOTAL** | **33,638** | **$3,388,618,294** | **+28,575** | **+$352,997,275** | **62,213** | **$3,741,615,569** | **+84.9%** |

By appendix stream: aging 3,822 rows / $43,689,275 · local 18,826 rows / $255,758,000 ·
youth 5,927 rows / $53,550,000.

Data-quality properties hold across the expanded corpus: **0 NULL amounts, 0 non-9-digit EINs**
in all 62,213 rows.

### Read this before quoting a number from the table

- **These are not restated figures.** Nothing was recomputed, re-parsed, or corrected. The AFTER
  column is the BEFORE column plus rows that already existed on disk.
- **FY2015–FY2017, FY2019, FY2020 are unchanged** because their appendix CSVs are header-only
  upstream. FY2018 changes by aging rows only — its local and youth CSVs are also header-only.
  That is a gap in `data/`, not something this release touched.
- **The per-year appendix totals match `DATA-ANOMALIES.md` #19 exactly** (the ~$49.8M fixed
  aging/local/youth pots, independently confirmed there on 2026-07-15). Two records derived
  separately agreeing to the dollar is a real check, and it passed.
- **Do not add the AFTER dollar column to a printed Schedule C grand total.** FY2027 happens to
  land within $854,587 of its printed $655,764,999 grand total, and **that is a coincidence, not a
  reconciliation** — FY2023's $312,208,214 sits nowhere near its $486,446,095. Anyone tempted by
  the FY2027 near-miss should look at FY2023 first.

## The canonical case: Bard College, EIN 14-1713034

**Before:** `get_awards_by_ein("14-1713034", fiscal_year: 2023)` → *No Schedule C awards for
EIN 14-1713034.* Not an incomplete answer — a confident, formatted, footnoted zero.

**On disk the whole time**, `data/fy23/schedule_c/fy23_appendix_b_local.csv` lines 200–202:

```
Abreu,Bard College,Bard Prison Initiative - Reentry & Alumni Affairs,141713034,5000,MOCJ,…
Brooks-Powers,Bard College,Council District 31,141713034,10000,MOCJ,…
Powers,Bard College,Prison Initiative,141713034,5000,MOCJ,…
```

**After:** three rows, $20,000, three sponsoring members, each tagged `[appendix: local]`.

FY2023 was the clean test case because its total was *zero*. FY2024–FY2027 were the quieter
version of the same bug: main-body rows present, appendix designations missing, so the answer
looked plausible and was simply short. `grep -n "141713034" data/fy*/schedule_c/*appendix*.csv`
returns 18 rows across FY2021–FY2027.

## Were these rows real? (VERIFIED against a source outside this repo)

This is the question that had to be settled before a single row was written, because the repo's
own `README.md` says of these files: *"These are subsets of the main body re-sorted by funding
stream — do not add them to the Schedule C total."* If that were true of the awards table,
loading them would double-count.

**It is not true of the awards table.** Three independent checks:

1. **Against the year's own awards CSV.** Matching all 28,575 appendix rows on
   `(member, EIN, amount)` against the same fiscal year's `*_schedule_c_awards.csv` leaves
   **27,874 of 28,575 unmatched (97.5%)**. The appendix is overwhelmingly *not* a re-sort of what
   the awards CSV already holds.

2. **Against the Council's own published disclosure spreadsheet** —
   `source/expense-funding-disclosure/funded_disclosure_FY2023.xlsx`, which is not derived from
   this repo. All three Bard designations appear there with `Source` = "Local", matching member,
   amount, and purpose text verbatim. These are real designations the MCP was failing to report.

3. **Aggregate agreement, FY2027.** The disclosure's `Source` column counts are **Aging 467,
   Local 2558, Youth 835**. The FY2027 appendix files hold **467, 2,558, 835** rows. Three-way
   exact agreement, file for file, with a source published by a different organization. This is
   what upgrades the A→aging / B→local / C→youth mapping from a plausible reading of the filenames
   to a verified fact. (FY2023 is close but not exact — 490/2805/850 vs 489/2726/841 — small
   upstream parser gaps.)

**Residual duplication is marginal and measured, not assumed.** Using the disclosure as arbiter
(does `awards` + `appendix` on a key exceed the disclosure's own multiplicity for that key?):
**12 rows in FY2023 and 2 rows in FY2027**, out of 8,000-odd. Inspecting the FY2027 collisions by
hand shows most are coincidental round-amount matches on distinct designations — e.g. a $20,000
aging designation to Alpha Phi Alpha Senior Citizens Center colliding with an unrelated $20,000
Digital Inclusion award to the same org and member. **Some genuine duplicates are certainly in
there.** They are a rounding error against 28,575 rows that were invisible, and they are worth
naming rather than hiding.

**What this does NOT settle:** whether the README sentence is wrong, or right about something
else. It is defensible about the printed *category* totals — the pots plausibly sit inside the
category lines that `*_schedule_c_initiatives.csv` reconciles against. Reconciling that sentence
with this finding is Phase 1 work. It was left alone tonight (the corpus was read-only), and the
contradiction is recorded in `mcp/CHANGELOG.md` rather than silently resolved.

## Design decision: discriminator column, not a separate table

Two options were on the table. **Option 1 was implemented.**

| | Option 1 — `source_table` on `awards` (chosen) | Option 2 — separate `appendix_awards` table + new tool |
|---|---|---|
| Bard FY2023 resolves | automatically, via existing tools | only if the caller knows to call the new tool |
| Existing query results | **change** (counts and totals rise) | unchanged |
| Published v1.3.x figures | reproducible via `source_table:"schedule_c"` | reproducible by default |
| Cost of being wrong | one filter argument, or one `WHERE` clause in `searchAwards` | 28,575 rows stay invisible to anyone who doesn't know to ask |

**Why option 1.** The failure being fixed is that a caller asks a reasonable question and gets a
confident wrong answer. Option 2 preserves that failure by default: `get_awards_by_ein` would
still return "no awards" for Bard FY2023, and only a caller who already suspected the gap would
find the rows. A discretionary-funding index whose completeness depends on the user's prior
knowledge of its gaps is the same defect wearing a new table name.

**The honest cost.** Every already-published total from this MCP is now the *main-body slice* of
what these tools return. FY2023 award counts move 1,848 → 5,904. Anyone reconciling against an
older figure will see a discrepancy that is real, expected, and not an error.

Four things make that cost survivable, and they are the actual deliverable of this decision:

1. **`source_table: "schedule_c"` reproduces the pre-1.4.0 result set exactly.** Pinned by test,
   not by assertion in prose.
2. **Every appendix row is tagged in output** (`· [appendix: local]`), so no row is silently
   reclassified as main-body Schedule C.
3. **Any mixed result set prints a `By source:` split**, naming both subtotals, saying the rows
   were absent before v1.4.0, and naming the escape hatch. A number that grows without saying why
   is how a reconciliation becomes a phantom discrepancy.
4. **`list_available_fiscal_years` states the change** and reports appendix coverage as an explicit
   subset of the award years.

**Reversing it is cheap** — that was a design requirement, not an afterthought. Default the filter
to `'schedule_c'` in `searchAwards`/`getAwardsByEin` (`mcp/src/db.ts`) and every existing query
returns to v1.3.x behavior with the data still loaded and reachable. No re-index, no data loss,
no schema change.

## Column reconciliation — explicit, no silent coercion

The appendix CSVs are a **strict subset** of `AwardRow`. No renames, no type conflicts, no orphan
columns. The mismatch is entirely absent fields.

| `AwardRow` field | awards CSV | Appendix B (local) | Appendix A/C (aging/youth) | How it was handled |
|---|:---:|:---:|:---:|---|
| `fiscal_year` | injected from folder | absent | absent | injected from folder name — **identical** to the existing path, not a coercion |
| `category` | present | **absent** | **absent** | stored `""` |
| `initiative` | present | **absent** | **absent** | stored `""` |
| `award_type` | present | **absent** | **absent** | stored `""` |
| `member` | present | present | present | loaded verbatim |
| `organization` | present | present | present | loaded verbatim |
| `program` | present | present | present | loaded verbatim |
| `ein` | present | present | present | `normEin()` — digits-only, same helper as the existing path. 0 rows altered |
| `amount` | present | present | present | `parseAmount()`, same helper. 0 rows altered, 0 NULLs produced |
| `agency` | present | present | **absent** | B loaded verbatim; **A/C stored `""`** |
| `purpose` | present | present | present | loaded verbatim |
| `source_table` | — | — | — | **new**: `'schedule_c'` / `'appendix'` |
| `appendix_stream` | — | — | — | **new**: read off the filename |

**The four empty fields are a deliberate refusal to infer, and this is the part most likely to be
"helpfully" fixed later by someone who shouldn't.**

- **`category` / `initiative` / `award_type`** — reading A/B/C as the missing `initiative` is
  tempting and was not done. It was not tested against the FY-matched
  `*_schedule_c_initiatives.csv`, so it stays an inference.
- **`agency` on aging/youth** — DFTA-for-aging and DYCD-for-youth is the obvious guess and is
  **demonstrably not safe**: appendix B records `MOCJ` on Bard's FY2023 local rows, so agency is
  not constant per stream. An empty string is a fact; a plausible guess is not.
- **Consequence for callers, stated in the tool schema:** filtering `search_awards` on `category`
  or `initiative` **excludes appendix rows entirely**, because they have no such value to match.
  A test pins this.

`appendix_stream` is the one added field, and it is mechanically derived from the filename with
zero inference — it is the only thing distinguishing the three appendix files once they are merged
into one table, so dropping it would have destroyed information that exists on disk. Its
correctness is what check 3 above verifies.

## Anomalies observed in passing (VERIFIED, not fixed — corpus was read-only)

1. **`agency` disagrees between the appendix and the Council's disclosure.** Bard's FY2023 rows
   read `MOCJ` in `fy23_appendix_b_local.csv` and `DYCD` in `funded_disclosure_FY2023.xlsx`, with
   identical member, amount, and purpose text. One of the two is wrong. Not diagnosed here.
2. **PDF page-header bleed contaminates `purpose`** in at least FY2022 and FY2027 appendix B —
   e.g. a row ending `… Page 37 Appendix B: Local Initiatives Council Member Sponsor Legal Name of
   Organization - Program Name Tax ID Amount Agency Purpose of Funds`. A pre-existing parser
   artifact in `data/`, now visible to consumers because these rows finally reach one.
3. **`awards` has no primary key and no unique constraint** (`PRAGMA table_info(awards)`: every
   column `notnull=0 pk=0`). Nothing in the schema would reject a duplicate. The rebuild is
   idempotent because `build-index.mjs` drops and recreates the DB, so this is not a live hazard —
   but any future incremental loader must not assume the database will catch it.

## Verification

```
$ npm ci --offline --no-audit --no-fund
added 133 packages in 3s

$ npm test
ℹ tests 62
ℹ suites 0
ℹ pass 62
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
```

New/changed tests:

- `mcp/test/appendix-ingest.test.js` (new, 8 tests) — the Bard FY2023 case in **both** directions
  (rows now returned, **and** `source_table:"schedule_c"` still returns nothing for FY2023, which
  is what proves they are new rows rather than a main-body figure that shifted); corpus totals;
  exact pre-1.4.0 reproduction; the mixed-result disclosure; the no-invented-fields guard.
- `mcp/test/coverage.test.js` — per-year main-body counts and totals **unchanged**, now scoped to
  `source_table = 'schedule_c'` so the published-figure regression guard survives the ingest; adds
  a parallel per-year appendix table and a guard that header-only years contribute nothing.

## Files changed

```
mcp/scripts/build-index.mjs     appendix loader + 2 new columns + index
mcp/src/db.ts                   AwardRow fields, source_table filter, appendix year coverage
mcp/src/server.ts               source_table param on 2 tools, row tagging, By-source split
mcp/test/appendix-ingest.test.js  (new)
mcp/test/coverage.test.js       scoped main-body guard + appendix expectations
mcp/package.json                1.3.1 → 1.4.0
mcp/package-lock.json           lockfile sync (the step missed on both 1.3.0 and 1.3.1)
mcp/CHANGELOG.md                1.4.0 entry
mcp/README.md                   data-scope row, tool table, totals-changed warning
```

Untouched, as required: `data/`, `source/`, `viz/`, root `README.md`, `DATA-ANOMALIES.md`,
`code/`. No tag, no publish, no merge.
