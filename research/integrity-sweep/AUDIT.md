# Adversarial audit — `fix/recover-lost-grantee-names`

**Report generated** 2026-08-13
**Data current as of** branch head `9c1a99d`, merge base `902568f`
**Scope** every repair applied on this branch: 2,418 crosswalk substitutions, two sidecars, four repair scripts, two gates.
**Mode** audit only. Nothing under `data/` was modified. Every script written for this audit lives in `research/integrity-sweep/` and is read-only.

---

## Verdict

**SAFE TO MERGE WITH CAVEATS — after two one-line fixes and three documentation corrections.**

The repairs are sound. I attacked them from an independently written xlsx reader, three corroborating sources, and the git history, and the corpus came back materially better than it went in. Two things are wrong and should be fixed before merge; neither is systemic.

| | |
|---|---|
| **Verified-wrong name substitutions** | **1 of 2,398** — 0.042% |
| Substitutions that were not an improvement (1 wrong + 2 information-losing) | 3 of 2,398 — 0.13% |
| EIN corrections wrong | **0 of 20** |
| Member-surname peels wrong | **0 of 1,083** |
| Awards double-published in a sidecar | **1 of 22,677** — $29,729 of $306,875,821 |
| Dollars moved | **$0**, verified at cell level, not just per year |
| Repairs applied when the scripts' own uniqueness rule did not actually hold | 57 of 2,398 — 2.4% (all predate commit `0627897`) |

**Basis for the error rate.** Not a sample. Every one of the 2,418 crosswalk entries was re-decided against (a) the Council's disclosure workbooks re-read with cells positioned by their `r` reference, (b) the Transparency Resolutions, and (c) this corpus's own rows for the same EIN in other fiscal years. 2,368 (97.93%) are corroborated by **two or more** of those three independent sources; 49 by exactly one; 1 is contradicted.

```
$ python3 research/integrity-sweep/corroborate_all.py
applied repairs scored: 2,418

verdict               n    share
CONFIRMED_2+       2368  97.93%
CONFIRMED_1          49   2.03%
CONTRADICTED          1   0.04%
```

A 60-row stratified hand sample (`sample_verify.py`, seed 20260813, 10 per defect class) was read row by row against the same three sources plus the raw workbook rows; it found nothing the population scan missed.

---

## Method, and why it is independent

The repairs and their gates all read the disclosure workbooks through the same helper, so re-using it would have audited nothing. I wrote `research/integrity-sweep/xlsxlib.py` from the OOXML layout instead, with one deliberate difference: **every cell is positioned by its `r` reference (`A1` notation), not by its ordinal position among the `<c>` elements present in the XML.** xlsx omits empty cells, so `zip(header, cells_present)` shifts every value after an interior gap.

That reader is itself checked (`test_xlsxlib.py`) against a workbook built with a known interior gap, plus a live read of FY2023.

```
$ python3 research/integrity-sweep/test_xlsxlib.py
live read ok: source/expense-funding-disclosure/funded_disclosure_FY2023.xlsx header row 1, 11,027 data rows
all xlsxlib checks passed
```

---

## Findings, ranked

### 1. VERIFIED CORRUPTION — one row where correct data was replaced with wrong data

`data/fy16/schedule_c/fy16_schedule_c_awards.csv:141`, EIN 13-2612524, **$258,800**.

```
WAS     : 'Fund for the City of New York'
APPLIED : 'Center for Court Innovation (Brownsville Community Justice Center)'
```

Both FY2016-vintage published sources name the original, not the replacement:

```
$ python3 research/integrity-sweep/fcny.py
=== every FY2016 disclosure row with EIN 132612524 and amount 258800 ===
  xlsx row 4819: name='Fund for the City of New York, Inc.' amount=258800 fc_ein=''
  xlsx row 5621: name='Fund for the City of New York, Inc.' amount=258800 fc_ein=''
=== transparency-resolution rows, EIN 132612524 amount 258800 ===
  fy15 reso=3 fy=2015 org='Center for Court Innovation (Brownsville Community Justice Center)'
  fy16 reso=1 fy=2016 org='Fund for the City of New York, Inc.'
```

The applied name is the **FY2015** spelling, pulled in because `recover_org_names.council_names()` pools all fourteen workbooks into one `(EIN, amount)` lookup.

**Mechanism, fully traced.** Three things had to line up:

1. `recover_org_names.PROSE` matches `funds? for`, so the string `Fund for the City of New York` is classified `org_prose`. It is a false positive — a real legal name.
2. The script has a guard for exactly this (`if len(cand) == 1 and canon(org) == canon(candidate): continue`).
3. The guard could not fire, because at commit `2c8168f` — when this substitution was applied — the reader matched headers **exactly**, and FY2016 heads its name column `Legal Name of Organization Requesting Funding`. The whole FY2016 workbook was invisible. The pooled candidate set held only the FY2015 name, so `len(cand) == 1` was true and the gate opened.

Commit `0627897` fixed the header matching four commits later. **Nothing re-derived the rows already applied.**

```
$ python3 research/integrity-sweep/fcny_year.py
   crosswalk row present at 2c8168f: True   0627897: True   9c1a99d: True
```

**Fix:** revert that one cell to `Fund for the City of New York, Inc.` (or, better, re-run `recover_org_names.py` from scratch — see finding 2). Cost: one line.

### 2. STRUCTURAL — the crosswalk accumulates across a changed evidence base, and nothing re-validates

The crosswalk is append-only by design, which is right for an audit trail. But the repair scripts also use it as the record of what has already been decided, and the evidence base under those decisions changed mid-branch.

```
$ python3 research/integrity-sweep/crosswalk_history.py
2c8168f  rows= 1060  ...  fix: recover 1,060 lost grantee names
eb0133e  rows= 1271  +211 ...
18d84cb  rows= 1291  +20  ...
0627897  rows= 1287  +8  -20   fix: match disclosure headers by substring — FY2016 was silently unreadable
...
9c1a99d  rows= 2418

rows in the FINAL crosswalk that were first written before the reader fix (0627897)
and never re-derived: 1,291 of 2,418
```

**Consequence, measured.** 57 applied repairs sit on a `(EIN, amount)` key that, read correctly, carries more than one distinct legal name — so the rule the scripts state ("nothing applied unless exactly ONE candidate") did not hold for them.

```
$ python3 research/integrity-sweep/attribute_ambiguity.py
  already ambiguous to the current reader too    applied_before_0627897=True  n=53
  positional-shift (defect 2, STILL LIVE)        applied_before_0627897=True  n=4
  TOTAL 57
```

**All 57 predate `0627897`.** 53 of them were applied when the exact-header reader made FY2014 and FY2016 invisible; 4 are attributable to the still-live positional-shift defect (finding 3).

Substantively most of the 57 are benign — JASA/HANAC/YMCA/CUNY spelling variants of the same body, which a year-scoped read resolves. Only finding 1 is materially wrong. But the *guarantee* is broken, and the guarantee is what the repo asks readers to trust.

**Fix:** re-run all four repair scripts from a clean crosswalk on the current reader, and diff the result against the shipped crosswalk. Anything that no longer resolves uniquely should be reverted to its original text and left flagged.

### 3. LIVE BUG — all four repair scripts still map xlsx cells by position, not by reference

`recover_org_names.read_workbook`, `fix_member_bleed.read_workbook`, `fix_wrong_eins.load_year` and `build_appendix_from_disclosure.read_disclosure` all do `dict(zip(hdr, [cv(c) for c in el.findall(NS+"c")]))`. xlsx omits empty cells.

```
$ python3 research/integrity-sweep/reader_diff.py
funded_disclosure_FY2014.xlsx  orig_keys=4170  strict_keys=5206  strict_only=1036  name_set_differs=9
funded_disclosure_FY2016.xlsx  orig_keys=5619  strict_keys=5867  strict_only= 248  name_set_differs=6
...
TOTAL orig keys   : 32,665
TOTAL strict keys : 33,364
keys only in strict: 699
```

The scripts see **699 fewer `(EIN, amount)` keys than the workbooks contain**, and 15 keys where the set of names is wrong. FY2014 alone has 1,494 rows with an interior gap, FY2016 has 274.

Direction of harm is mostly benign — a thinner lookup means fewer recoveries, not wrong ones (`orig_only = 0`, so the shift never invented a key). But a **thinner** set is exactly what makes `len(cand) == 1` fire on incomplete evidence, which is the mechanism behind findings 1 and 2.

**Fix:** four identical one-line changes — read `c.get("r")` and place the value at that column index. `research/integrity-sweep/xlsxlib.py:rows()` is a working reference implementation, 30 lines.

### 4. DOUBLE COUNT — one award published twice, $29,729

`data/recovered/schedule_c_absorbed_awards.csv` re-emits an award the corpus already carries.

```
$ python3 research/integrity-sweep/absorbed.py
--- 1. collisions with a live award row on (fy, ein, amount) ---
  sidecar: 'Central Astoria Local Development Coalition, Inc.' $29,729 FY2017
           absorbed_from fy17:161  confidence=high disclosure_confirmed=yes
  live   : fy17:160 'Central Astoria Local Development Coalition, Inc.' ein=112652331 $29,729
```

The Council published exactly one Central Astoria designation at that amount:

```
$ python3 research/integrity-sweep/central_astoria.py
  xlsx row 1455: Source=Community Housing Preservation Strategies | Amount=29729 | Status=Cleared
```

The gate that should have caught it exists — `already_in_corpus` in `code/absorbed_award_candidates.csv` — and is simply set wrong for this one row:

```
$ python3 research/integrity-sweep/candidates_audit.py
  flagged=0  recomputed=0  n=442
  flagged=0  recomputed=1  n=1     <-- Central Astoria
  flagged=1  recomputed=1  n=2
```

This is a **1-in-445 flag error**, not a design failure. Note it became an *exact* duplicate only after this branch's `wrong_ein` repair corrected fy17:160's EIN from `112412584` to `112652331`; before that it was a name+amount duplicate only.

**Fix:** drop that row from the sidecar. Cost: one line. $29,729 of $66,502,721.

### 5. PROVENANCE — the absorbed sidecar has no generating script in the repo

`code/build_recovered_awards.py` reads `code/absorbed_award_candidates.csv`, a checked-in 445-row intermediate carrying the verdicts, the disclosure joins, and the `already_in_corpus` flag. Nothing in the tree produces that file.

```
$ grep -rl "already_in_corpus" .
code/absorbed_award_candidates.csv
code/build_recovered_awards.py
```

443 awards and $66.5M are therefore **not reproducible from source**. They can only be re-checked, which is what finding 4 did. Every other artifact on this branch regenerates: I rebuilt the 22,234-row appendix sidecar from the workbooks with my own reader and got it back byte-identical (finding 9).

**Fix:** commit the generator, or state plainly in `data/recovered/README` (there is none) that this sidecar is a one-off derivation.

### 6. GATE — `verify_crosswalk.py` misses six of eight corruptions I constructed

Its docstring claims it proves "every recorded edit actually happened, **and nothing else did**." It does the first half only: it iterates crosswalk rows and compares `recovered_organization` to the live cell. It never reads the data looking for unrecorded edits, never checks `original_organization` against anything, and never re-tests the evidence.

```
$ python3 research/integrity-sweep/break_the_gate.py
baseline: (0, 'PASS — the audit trail is exact')

  [     GATE BLIND] 500 entries claim a prior value that never existed
  [     GATE BLIND] 500 entries carry a fabricated (EIN, amount) join key
  [     GATE BLIND] every entry relabelled to an invented source
  [     GATE BLIND] 200 organization cells rewritten with no crosswalk entry
  [gate catches it] 200 EINs rewritten with no crosswalk entry
  [     GATE BLIND] 200 amounts rewritten with no crosswalk entry
  [     GATE BLIND] one row given two contradictory audit-trail entries
  [gate catches it] CONTROL — one entry disagrees with the data
```

The EIN scenario is caught only by luck — the mutated range happens to contain a `wrong_ein` entry. The `UNIQUE` assertion keys on `(file, line, defect)`, so two entries for one row telling different stories about its history both pass.

The stated reversibility guarantee — *"`original_organization` holds the verbatim original, so every edit is reversible from the audit trail alone"* — is **unverified by anything in the repo.**

**Fix, two lines each:** diff the data against the base ref and assert every changed cell has a crosswalk entry; key `UNIQUE` on `(file, line)`.

Separately: `verify_no_dollars_moved.py`'s docstring says it compares "a git ref and the working tree," but `totals_at("HEAD")` reads the **committed** tree. Uncommitted damage passes.

### 7. DOCUMENTATION — `member` was filled from an uncorroborated inference on 166 rows

The peel writes the removed token into `member` where the row had none. The *name* half of that edit is confirmed against the disclosure; the *member* half is not, and cannot be — `member` was deliberately excluded from the join key because of roster-vintage drift.

```
$ python3 research/integrity-sweep/member_fills.py
rows that gained a `member` from the peel: 166
  agrees with disclosure       144
  DISAGREES with disclosure     22
```

87 of the 166 are borough names (Manhattan 34, Bronx 16, Staten Island 14, Queens 12, Brooklyn 11), consistent with existing corpus convention for boroughwide designations. Of the 22 disagreements, ~14 are the string mismatch `Staten Island` vs the disclosure's `SI Delegation`. A handful are genuinely questionable (`fy15:38` wrote `Reynoso`; the FY2015 workbook says `Reyna`).

`DATA-ANOMALIES.md` §21 does not mention that `member` was written at all. It should, and it should mark it INFERRED.

### 8. GAP — FY2018's Local and Youth appendices are still empty, $44.45M

`build_appendix_from_disclosure.py` hardcodes `(2015, 2016, 2017, 2019, 2020)`, and its emptiness guard is per **year**, not per **file**:

```python
if not files or any(sum(1 for _ in open(f)) > 1 for f in files):
    print(f"  FY{fy}: appendix files are populated — skipping")
```

FY2018 has a populated `appendix_a_aging.csv` (422 rows), so the whole year is excluded even though its Local and Youth files hold a header and nothing else.

```
$ python3 research/integrity-sweep/gaps.py
  appendix_a_aging       124 rows  $   1,235,225
  appendix_b_local      3019 rows  $  35,796,000
  appendix_c_youth       874 rows  $   7,419,000
  TOTAL                 4017 rows  $  44,450,225
```

This corroborates the parallel sweep's finding 4 independently (they estimated ~$45.4M).

### 9. LATENT — 358 correct organization names sit one guard away from finding 1

The repair pipeline and the validator disagree about what `org_prose` is. `recover_org_names.PROSE` was deliberately broadened mid-branch; `validate_data.ORG_PROSE` was not.

```
$ python3 research/integrity-sweep/detector_gap.py
both detectors agree           : 140
repair-script pattern ONLY     : 369   $29,682,734
validator pattern ONLY         : 0

$ python3 research/integrity-sweep/latent_risk.py
  the string IS a published legal name (false positive): 358   $28,949,394
  not a published legal name (probably real prose)     : 11
    x343   'Fund for the City of New York, Inc.'
    x9     'South Asian Fund for Education, Scholarship and Training, Inc.'
```

343 rows reading `Fund for the City of New York, Inc.` are classified as a defect by the repair script every time it runs. Only the `canon(org) == canon(candidate)` guard keeps them intact — the guard that failed once already, at fy16:141.

**Fix:** exclude a string that canon-matches a published legal name before the prose pattern is even consulted.

### 10. UNREPAIRED — 53 real member bleeds remain, $3.05M

The peel is idempotent (a re-run now plans zero changes, which is the right behavior). But its strict gate leaves behind rows where the evidence is weaker yet still clear:

```
$ python3 research/integrity-sweep/false_negatives.py
  left alone, correct as printed           3581 rows  $  110,938,378
  neither form is a published name          139 rows  $    9,835,858
  LIKELY A REAL BLEED, not peeled            53 rows  $    3,049,806

  fy15:37  -'Eugene'     'Eugene Brooklyn Housing and Family Services, Inc.'
  fy21:583 -'Dromm'      'Dromm City University of New York'
  fy17:26  -'Crowley'    'Crowley Coalition for Queens, Inc.'
```

Not an error — leaving them flagged is defensible — but `DATA-ANOMALIES.md` §21 says the real class is "~1,354" and 1,083 were fixed. The 53 with independent support for the peel should be named.

### 11. DOCUMENTATION — sidecar quality issues shipped without labels

`schedule_c_absorbed_awards.csv` contains one row whose `organization` is purpose prose and one carrying an unpeeled surname:

```
$ python3 research/integrity-sweep/candidates_audit.py
  organization holds purpose prose        : 1
      'Funding will support senior programming and meals Cornegy Sumner House'  $6,750
  organization leads with a member surname: 27   (26 are legitimate names; 1 is a bleed)
      'Lander Npower, Inc.'  name_source=absorbed_text
```

Both are `name_source=absorbed_text`, i.e. already the low-confidence tier. Worth fixing, not worth blocking on.

Also: the sidecar's `absorbed_from_line` column no longer resolves against the shipped data, because the name repairs **deleted the absorbed text those line numbers point at**. Verified as a repair artifact, not a provenance error:

```
$ python3 research/integrity-sweep/anchor_at_base.py 902568f
anchor rows at 902568f: absorbed text visible 445, not visible 0, unresolved 0
```

At `HEAD` only 96 of 445 still show it. A reader must consult the crosswalk. Say so.

---

## What I verified clean

**No money moved — checked at cell level, not just per year.** Their own `verify_no_dollars_moved.py` sums per fiscal year, which a pair of offsetting errors would survive. I diffed every tracked CSV cell by cell between `902568f` and `HEAD`:

```
$ python3 research/integrity-sweep/diff_cells.py 902568f HEAD
=== columns changed, all files ===
  organization                  3287
  member                         332
  ein                             38
amount cells changed: 0
```

No row-count change and no header change in any file. And the counts **reconcile exactly** with the crosswalk: 3,287 − 889 (the derived `all_years_awards.csv` rollup) = 2,398 organization edits in per-year files = 2,418 crosswalk entries − 20 `wrong_ein` entries (which touch `ein`, not `organization`). 38 − 18 = 20 EIN edits. 332 − 166 = 166 member fills, matching the script's own stated 166. **The crosswalk is complete with respect to what actually changed on disk.**

**All 20 `wrong_ein` repairs are independently correct.** Re-derived from the workbooks with a corrected reader and a conduit-column matcher that actually matches the FY2018+ header:

```
$ python3 research/integrity-sweep/check_wrong_ein.py
tally: {'CONFIRMED': 20}
```

*(Latent, no impact: `fix_wrong_eins.py` looks for a header containing `fc ein`. FY2018+ heads it `Fiscal Conduit EIN`, which does not contain that substring, so the fiscal-conduit skip is dead from FY2018 on — 8 conduit EINs in FY2018, 1 in FY2023, seen by a correct read and by that script as 0. None of the 20 repairs was affected.)*

**All 1,083 member-surname peels are confirmed by the disclosure**, under a reference-positioned, year-scoped read, and none produces a name unknown to the disclosure for that EIN:

```
$ python3 research/integrity-sweep/recheck.py
member_bleed  CONFIRMED          1083

$ python3 research/integrity-sweep/decap.py
=== TEST C ===
peeled names not found under their own EIN anywhere in the disclosure: 0
```

**The peel created zero decapitations.** This is the finding the parallel sweep ranked first, and it is **entirely pre-existing** — the count is bit-identical at the merge base and at HEAD:

```
$ python3 research/integrity-sweep/decap_at_ref.py 902568f 2c8168f 553d5d2 HEAD
   902568f  pairs=97  rows=690  dollars=$136,938,046
   2c8168f  pairs=97  rows=690  dollars=$136,938,046
   553d5d2  pairs=97  rows=690  dollars=$136,938,046
      HEAD  pairs=97  rows=690  dollars=$136,938,046
```

`member='Brooklyn' org='Defender Services'`, `member='Hudson' org='Guild'`, `member='Queens' org='Community House, Inc.'` — all of it was there before this branch, and none of it was created by the peel:

```
=== TEST B: of those, how many were created by this branch's peel? ===
peel-created decapitations: 0
```

The script's own docstring explains why: it deleted a corpus-fallback rule precisely because it truncated Hudson Guild to "Guild." That judgment was correct and held.

**The 22,234-row appendix sidecar reproduces exactly.** I rebuilt it from the workbooks with my own reader and the same filters:

```
$ python3 research/integrity-sweep/rebuild_appendix.py
published sidecar : 22,234 rows  $240,373,100
strict rebuild    : 22,234 rows  $240,373,100
rows in the PUBLISHED sidecar that a correct read does not produce: 0  $0
rows a correct read produces that the sidecar is MISSING          : 0  $0
```

**Neither sidecar duplicates the corpus** (beyond finding 4), on any of four progressively looser keys — exact `(fy, ein, amount)`, `(fy, canon-name, amount)`, amount rounded to $100, and name-only:

```
$ python3 research/integrity-sweep/sidecars.py
per-year corpus: 62,213 rows  appendix=28,575  awards=33,638
per-year corpus dollars: $3,741,615,569

===== schedule_c_appendix_recovered.csv =====   (vs the ENTIRE per-year corpus)
  collides on strict         0 rows  ($0)
  collides on loose          0 rows  ($0)
  collides on rounded        0 rows  ($0)
```

The 6,723 name-only collisions are the same grantee receiving both an initiative award and an appendix designation in one year — expected, not duplication (zero of them collide against the per-year appendix files).

The appendix sidecar covers exactly 2015, 2016, 2017, 2019, 2020 — precisely the years whose per-year appendix files hold a header and nothing else. Verified file by file.

**The five internal duplicate tuples in the absorbed sidecar are legitimate.** Each is two or three different council members designating the same amount to the same grantee, and the disclosure publishes at least as many:

```
$ python3 research/integrity-sweep/internal_dups.py
FY2017 ein=112634818 $51,000 catholicmigrationservices
   sidecar copies : 2   published designations: 2 [('Ferreras-Copeland', ...), ('Van Bramer', ...)]
   -> OK
   ... all five OK
```

**The headline numbers are right.** 62,213 rows, $3,741,615,569, independently recomputed. `data/QA-REPORT.md`'s own per-file advisories sum to exactly the residue §21 claims (140 `org_prose`, 64 `org_merged`), and to 62,213 rows.

**The MCP index does not load `data/recovered/`.** No downstream double count from either sidecar.

**The repairs are idempotent.** `fix_member_bleed.py --dry-run` now plans zero changes on 3,773 surname-leading rows.

---

## Corrections to the parallel sweep

Its finding **1** ("A sponsor token is peeled off a real organization name — 740 rows, $133,017,064… New class, and the worst") attributes the defect to this branch's peeler. **That attribution is wrong.** Measured at four commits including the merge base, the count is identical: 690 rows, $136,938,046 by my definition, unchanged by every repair on this branch. The defect is real, it is serious, and it is **pre-existing** — it belongs to the Schedule C parser, not to `fix_member_bleed.py`. Zero of those rows were created by the peel.

Its finding **4** (FY2018 appendices) I confirm independently: 4,017 rows, $44,450,225.

Its finding **2** (appendix rows inside the headline total) I confirm as an open question and place it out of this branch's scope — the appendix files were loaded at `902568f`, and the branch changes no amount. My own overlap measurement: 693 appendix rows totalling $8,117,500 match an awards row on all of `(fy, ein, amount, organization, member)`.

---

## Could not verify

State these as gaps, not as clean bills.

- **Whether the 693 appendix/awards overlaps are duplicates.** Needs the source PDFs. Not resolvable from the CSVs, and not made better or worse by this branch.
- **Whether `Fund for the City of New York, Inc.` or `Center for Court Innovation (Brownsville Community Justice Center)` is the *editorially* right value for a fiscal-conduit award.** I established only that the FY2016 sources say the former and the row said the former before the repair, so the repair changed a correct value to a differently-sourced one. Which convention the repo wants is a maintainer decision.
- **Whether the 22 `member` fills that disagree with the disclosure are wrong.** No Council roster by year exists in this repo, and the workbooks are republished with the roster current at snapshot time. `fy15:38` (`Reynoso` written, disclosure says `Reyna`) cannot be settled here.
- **FY2013.** `funded_disclosure_FY2013.xls` is the old binary format; every script globs `*.xlsx` and skips it. Out of corpus range (fy15–fy27), so no impact, but it is silently absent from the evidence base rather than deliberately excluded.
- **The 139 surname-leading rows where neither the printed string nor the peeled remainder is a published name** ($9,835,858). Undecidable from the sources in this repo.

---

## Must-fix before merge

1. **Revert `data/fy16/schedule_c/fy16_schedule_c_awards.csv:141`** to `Fund for the City of New York, Inc.`, and remove or annul its crosswalk entry. *(finding 1)*
2. **Drop the FY2017 Central Astoria row from `data/recovered/schedule_c_absorbed_awards.csv`.** *(finding 4)*
3. **Correct `DATA-ANOMALIES.md` §21:** record that `member` was written on 166 rows and mark it INFERRED; state that 53 evidenced bleeds remain unrepaired; note that the absorbed sidecar's `absorbed_from_line` no longer resolves against the shipped data. *(findings 7, 10, 11)*

## Should-fix soon

4. Position xlsx cells by `r` reference in all four scripts. *(finding 3)*
5. Exclude published legal names from the prose pattern before it is consulted. *(finding 9)*
6. Give `verify_crosswalk.py` the second half of its own docstring — assert that no cell changed without a crosswalk entry — and key `UNIQUE` on `(file, line)`. *(finding 6)*
7. Re-derive the whole crosswalk from a clean slate on the fixed reader and diff. *(finding 2)*
8. Commit the generator for `code/absorbed_award_candidates.csv`, or label the sidecar as a non-reproducible one-off. *(finding 5)*
9. Make `build_appendix_from_disclosure.py`'s emptiness guard per-file and add FY2018. *(finding 8)*

---

## Reproducing this audit

All scripts are stdlib-only, read-only, and take no arguments unless noted. Run from the repo root.

| script | what it establishes |
|---|---|
| `test_xlsxlib.py` | the audit's own reader is correct |
| `diff_cells.py [base] [head]` | cell-level diff; proves $0 moved and the crosswalk is complete |
| `reader_diff.py` | the positional-shift defect, quantified per workbook |
| `corroborate_all.py` | every repair scored against three independent sources |
| `sample_verify.py [n] [seed]` | stratified hand sample with all evidence laid out |
| `recheck.py` | every repair re-decided under a correct read |
| `overwrote_good.py` | repairs that replaced an already-correct name |
| `fcny.py`, `fcny_year.py` | finding 1, end to end |
| `crosswalk_history.py`, `attribute_ambiguity.py` | finding 2 |
| `check_wrong_ein.py` | all 20 EIN repairs, independently re-derived |
| `decap.py`, `decap_at_ref.py` | the decapitation class, and its attribution |
| `member_fills.py` | the 166 inferred `member` values |
| `false_negatives.py` | unrepaired bleeds |
| `sidecars.py`, `absorbed.py`, `absorbed_dups.py`, `internal_dups.py`, `central_astoria.py`, `candidates_audit.py`, `anchor_at_base.py` | both sidecars |
| `rebuild_appendix.py` | the appendix sidecar, rebuilt from source |
| `break_the_gate.py` | corruptions `verify_crosswalk.py` accepts |
| `gaps.py`, `residue_split.py`, `qa_tally.py`, `detector_gap.py`, `latent_risk.py` | residue, gaps, detector disagreement |
| `appendix_overlap.py` | the pre-existing appendix/awards overlap |

`build_lookups.py` writes a 16 MB `lookups.json` cache the others read. It builds itself on first use (~30s) and is a build artifact, not a deliverable — delete it freely.
