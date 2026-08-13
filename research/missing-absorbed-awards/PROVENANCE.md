---
title: "Question 4 — if absorbed awards are recovered as rows, how should their provenance be marked?"
created: 2026-08-12
type: research-finding
status: draft
tags: [type/research, domain/software-engineer, project/nyc-budget]
---

# Q4 — Provenance marking for recovered absorbed awards

**Report generated:** 2026-08-12 21:11 EDT
**Data current as of:** 2026-08-12 (worktree `~/Code/NYCB-missing`, branch `research/missing-absorbed-awards` @ `2c8168f`)
**Scope:** judgement question, grounded in this repo's existing conventions. No repo file outside
`research/missing-absorbed-awards/` was modified. All commands below were run in this worktree.

---

## Recommendation, up front

**Option (b): a separate recovered-awards CSV, never merged into `*_schedule_c_awards.csv`** — with
four specifics that matter more than the choice itself:

1. Put it at **`data/recovered/schedule_c_absorbed_awards.csv`**, *not* under `data/combined/`.
2. **Register it in `validate_data.py`.** Unregistered, it is silently skipped — the §20 defect
   class repeating.
3. Mark provenance **per field, not per row**, from a closed vocabulary. A single `source=recovered`
   flag would be false in the direction that hurts.
4. If it later reaches the MCP, reuse the existing `source_table` discriminator with a third value
   `'recovered'` — no schema change, no `SELECT *` shape change.

**But read § "The one thing that could flip this" first.** There is a real chance the right answer
is option (a) with *no* provenance column at all, and the evidence for it is in this repo already.

---

## 1. What provenance means in this repo today

Provenance here is **per file, carried by the path**, not per row carried by a column. No award CSV
has ever had a provenance column. `data/fy17/schedule_c/fy17_schedule_c_awards.csv` means "the award
table of the FY2017 Schedule C PDF, extracted deterministically" — and `code/PARSING.md` records
which parser and invocation produces it. README states the promise at that level:

> "Every dollar figure here was extracted **deterministically** from the Council's own PDFs and
> checked line by line against the documents' printed totals." (README.md:5)

Two precedents already exist for changing these files, and they split cleanly.

### Precedent A — DATA-ANOMALIES §13 added rows, and marked nothing

The page-break-header fix recovered whole dropped awards and **added them to the existing
per-year CSVs**: FY2021 1,800 → 1,810, FY2024 5,299 → 5,368, FY2027 6,085 → 6,118. No column, no
flag, no sidecar. The record is a DATA-ANOMALIES entry with a per-year before→after table and a
regression test (`test_parse_schedule_c.py::test_fy27_west_side_work_coalition_survives`).

That was correct, and the reason is the whole point of this question: **those rows came from the
same PDF, via the same deterministic parser.** The file-level provenance statement stayed true, so
there was nothing to mark.

### Precedent B — the name recovery changed 1,060 fields using a *different* document, and still added no column

`code/recover_org_names.py` (commit `2c8168f`) rewrote the `organization` cell on 1,060 rows using
the Council's expense-disclosure workbooks — a different document from the Schedule C PDF. It did
not add a column either. Instead it wrote a full per-substitution audit sidecar:

```
$ head -1 data/combined/org_name_recovery_crosswalk.csv
file,line,ein,amount,source,match_key,original_organization,recovered_organization
$ wc -l data/combined/org_name_recovery_crosswalk.csv
    1061 data/combined/org_name_recovery_crosswalk.csv
```

Every edit is reversible from that file. So the repo's existing answer to "how do we mark
provenance" is: **a sidecar that makes the change auditable and reversible, not a column.**

That works for a *field* edit, because the row is still a Schedule C row and only one cell came from
elsewhere. It does not carry over unchanged to a *whole row*, because a whole row sourced elsewhere
makes the file's name untrue.

### A caution the precedent also supplies

`data/combined/org_name_recovery_crosswalk.csv` is **not documented in README**. The `data/combined/`
section lists `all_years_*`, `legistar_crosswalk.csv`, `initiative_name_crosswalk.csv` and
`category_name_crosswalk.csv` — not this one.

```
$ grep -rn "org_name_recovery" . --exclude-dir=node_modules --exclude-dir=.git
code/recover_org_names.py:14: … data/combined/org_name_recovery_crosswalk.csv …
code/recover_org_names.py:34:CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"
```

**VERIFIED.** A sidecar is cheap to add and cheap to leave undiscoverable. Whatever option is
chosen, the README row is part of the work, not a follow-up.

---

## 2. The fact that reframes the question

The absorbed awards' **money did not come from a second source.** 400 of the 404 embedded EINs sit
directly beside a dollar amount *inside the organization string the parser already captured from the
Schedule C PDF*:

```
$ python3 - <<'EOF'   # (full script in § Commands)
org_merged rows: 303
embedded EINs: 404   embedded EIN+amount pairs: 400
rows with >=1 recoverable EIN+amount pair in-string: 269
EOF
```

**VERIFIED.** So a recovered row is **mixed-provenance at the field level**:

| Field | Where the value comes from | Status |
|---|---|---|
| `ein`, `amount` | The Schedule C PDF, via this repo's own extraction — the same document as every other row | VERIFIED for 400/404 embedded EINs |
| `category`, `initiative`, `member`, `award_type` | Inherited from the host row's table context (same page, same table). Defensible, but an inference *from position*, not a value printed on that row | INFERRED |
| `organization` (and possibly `agency`, `program`, `purpose`) | The disclosure workbook, joined on `(EIN, amount)` — exactly what `recover_org_names.py` already does | Second document |

A row-level `source = "recovered"` column tells a reader the dollars are second-hand. **They are
not.** It also fails to say which of the other nine fields are inherited. That is a mark that is
simultaneously wrong and insufficient, which is the worst combination for a dataset whose headline
claim is that its numbers are not inferred.

Per-field provenance in a flat CSV means either one `*_source` column per multi-source field or a
JSON blob in a cell. That is a real cost — and it is a cost the *existing* award CSVs should not be
made to pay. Which is most of the argument for (b).

Note also what the disclosure workbook can and cannot supply. Its FY2017 header is:

```
$ python3 …  # stdlib xlsx read of funded_disclosure_FY2017.xlsx, first row
['Fiscal Year', 'Source', 'Council Members', 'Legal Name of Organization', 'EIN', 'Status',
 'Amount', 'Agency', 'Program Name', 'Street Address 1', … 'Purpose of Funds', 'Fiscal Conduit', 'FC EIN']
```

There is no `category` and no `award_type`. And `Source` is not the Schedule C `initiative`
vocabulary — its top values are the appendix streams:

```
FY2017 disclosure rows: 8674
   3127  Local
    925  Youth
    561  Cultural After-School Adventure (CASA)
    558  Aging
```

**VERIFIED.** So the workbook cannot fill the Schedule C schema even if we wanted it to. Any
recovered row put into `*_schedule_c_awards.csv` carries at least two empty or inferred columns.
`build-index.mjs` already stated the governing rule for exactly this situation when it loaded the
appendix rows: *"An empty string is a fact; a plausible guess is not."* (build-index.mjs:212)

---

## 3. Option (a) — add rows to the existing CSVs with a provenance column

### What breaks

**`code/validate_data.py` — HARD FAILURE, verified by running it.** The schema check computes
`extra = hset - required - optional` and hard-fails on anything unexpected (validate_data.py:230–234).
I copied 50 FY2016 award rows to a scratch tree, added one `provenance` column, and ran the real
validator:

```
$ python3 code/validate_data.py --data-dir <scratch>
validate_data: 1 files checked | 1 HARD finding(s) | 1 soft advisory(ies)

HARD FAILURES:
  [schema] …/fy16_schedule_c_awards.csv: unexpected columns: ['provenance']
```

Fixing it means editing **five** `TYPES` entries — `schedule_c_awards`, `combined_awards`,
`appendix_aging`, `appendix_local`, `appendix_youth` — and neither available route is good:

- add to `cols` → the column becomes **mandatory**, so any file not yet regenerated fails
  `missing columns`;
- add to `optional` → the column becomes **invisible to the schema check**, so a file that silently
  loses it passes clean. The provenance mark itself would then be unguarded.

**`code/build_combined.py`.** `AWARD_COLS` is an explicit 10-name list (build_combined.py:26–27) and
`collect()` reads `r.get(c, "")` for exactly those names. A new column is **dropped from
`all_years_awards.csv`** unless added there too. A roll-up that silently loses the provenance mark
is worse than no mark, because it is the file most people actually download.

**`mcp/scripts/build-index.mjs` — no break, and no mark.** It parses with `csv-parse` `columns: true`
(line 89) and every INSERT reads named properties (`r.category ?? ""`, lines 180–194). An extra CSV
column is simply never read. *(VERIFIED BY READING — `mcp/node_modules` is absent in this worktree
and the checkout that has it is out of bounds, so this is a code-reading claim, not a run.)* To
actually surface the mark you must extend the `awards` table (build-index.mjs:114–119), the INSERT
(169–174), and `AwardRow` in `mcp/src/db.ts:63–84`.

**MCP tool output shape.** `searchAwards` and `getAwardsByEin` are `SELECT * FROM awards`
(db.ts:198, 217). Adding a table column changes **every award tool's output shape** → CHANGELOG
entry + version bump. `mcp/package.json` is at `1.4.0`.

**`viz/schedulec_cleanup.py` — the column is harmless, the rows are not.** It reads by name, so an
extra column is ignored. But awards are bucketed as
`awd_by_key[(canonical_category, canonical_initiative)] += amount` (lines 256–262). Rows without
those fields key to `("", "")`, which is never in `leaf_keys_this_year`, so they raise the
denominator `all_awards_total` without raising `matched_total` — **`awards_matched_pct` falls in
precisely the years being fixed.** Today's baseline, run just now:

```
$ python3 viz/schedulec_cleanup.py --check
  FY2016: $   333,186,574 | $       250,000 |   0.3%
  FY2017: $   279,908,500 | $             0 |   0.0%
  FY2018: $   301,986,000 | $             0 |   0.0%
  FY2019: $   338,301,000 | $             0 |   0.0%
Reconciliation gate: Adopted 2027 grand total = $655,764,999 (target $655,764,999) -> PASS
```

**VERIFIED.** The FY2027 gate is computed from the *initiatives* side (`reconcile()` sums the Adopted
column) and is unaffected by anything done to awards.

**The CI version guard has a hole that option (a) walks straight into.** `.github/workflows/ci.yml`
diffs `mcp/src mcp/scripts mcp/package.json data/combined`. Rows added under `data/fy17/…` do **not**
trip it — yet `npm run prepare` runs `build-index` against `../data`, so the shipped npm package's
contents change with **no version bump forced**. Option (b) placed outside `data/combined/` has the
same property, but option (b) does not change what the currently-indexed files contain.

### How a skeptical reader audits it

Poorly. Today a reader can take any row of `fy17_schedule_c_awards.csv` and find it printed on a page
of the FY2017 Schedule C PDF. A recovered row cannot be checked that way: it is a *reconstruction* of
text the PDF prints inside a different row. And FY2017's row count would stop matching every
previously published figure with no visible seam — the reader has to trust the column.

---

## 4. Option (b) — a separate recovered-awards CSV, never merged

### What breaks

**`validate_data.py` — nothing breaks, and that is the problem.** `validate_tree` globs
`data/**/*.csv` recursively (line 481), but `detect_type` returns `None` for any filename it does not
recognize, and `None` means skip:

```
$ python3 -c "import sys; sys.path.insert(0,'code'); import validate_data as v; …"
data/combined/org_name_recovery_crosswalk.csv -> None
data/combined/all_years_awards.csv -> combined_awards
data/combined/recovered_awards.csv -> None
```

**VERIFIED.** A new data file would be **silently ungraded** — an artifact that is never inspected.
That is DATA-ANOMALIES §20's third failure mode in miniature ("the artifact was inspected,
misdiagnosed, and passed"; here it would not even be inspected). **Registering the file is not
optional in this recommendation.** One `detect_type` branch and one `TYPES` entry
(`ein="ein"`, `amounts=["amount"]`, `rule="positive"`) — roughly eight lines — buys EIN-validity
coverage, amount sanity, duplicate detection and the `org_merged` / `org_prose` advisories on the
recovered set itself.

**`build_combined.py`** — untouched. `collect()` globs `*_schedule_c_{kind}.csv` only.

**`build-index.mjs` / the MCP** — untouched unless you choose to index it. If you do, **the
mechanism already exists**: the `awards` table has `source_table` with `idx_awards_source`
(build-index.mjs:118, 123), populated `'schedule_c'` / `'appendix'`, and `AwardRow.source_table`
is documented as *"Added in 1.4.0; before that the table held main-body rows only, so every published
total from an earlier version is the 'schedule_c' slice of what these tools now return"*
(db.ts:75–81). A third value `'recovered'` costs one string literal: **no schema change, no
`SELECT *` shape change, no new index**, and it inherits a documented meaning and a precedent for how
to word the CHANGELOG.

**`viz`** — untouched. `_awards_path()` builds an explicit per-year path (schedulec_cleanup.py:189–191).

**Version guard** — `data/combined/` trips the guard on every edit, even while the MCP ignores the
file. `data/recovered/` does not. Hence the location recommendation.

### How a skeptical reader audits it

Best of the three, and by a wide margin. The existing CSVs stay byte-comparable to what has already
been published and cited, so nothing anyone has already quoted moves. The new file is a claim that
can be attacked on its own terms, provided each row carries its own evidence:

| Column | Why |
|---|---|
| `host_file`, `host_line` | Points at the exact row this award was absorbed into — reproducible against the committed CSV |
| `host_organization_raw` | The full merged string, verbatim. The reader can see the cut with their own eyes |
| `ein`, `amount` | As printed inside that string |
| `ein_source`, `amount_source` | Closed vocabulary; here `schedule_c_pdf` |
| `organization`, `organization_source` | `council_disclosure` when joined, empty when unresolved |
| `category`, `initiative`, `member`, `*_source` | `host_row_context` — names the inference instead of hiding it |
| `match_key` | Mirrors `recover_org_names.py`'s own field — `ein+amount` |

Closed vocabulary, three values: `schedule_c_pdf`, `host_row_context`, `council_disclosure`.
Anything unresolved stays **empty, never guessed** — build-index.mjs:207–213's rule, applied again.

---

## 5. Option (c) — publish the inventory as a documented gap only

**What breaks:** nothing, anywhere. §20 already exists and already records "**Not fixed.** The
extraction itself."

**Audit:** honest, but it leaves ~400 awards discoverable only by reading a markdown table, and
leaves the MCP and the viz still missing them in the years where they are most concentrated
(FY2017–FY2018 = 239 of 303 rows).

The decisive point against (c): **it is not actually cheaper than (b).** The inventory has to be
built either way — the same join, the same guards, the same ambiguity handling. Once it exists,
emitting it as CSV instead of a markdown table costs nothing. Option (c) is option (b) with the
machine-readable half deleted, and the deletion is the only difference.

---

## 6. Recommendation

**Option (b), with these five specifics.**

1. **`data/recovered/schedule_c_absorbed_awards.csv`.** Outside `data/combined/`, so the MCP version
   guard is not tripped by a file the MCP may never index.
2. **Register it in `code/validate_data.py`** — `detect_type` branch + one `TYPES` entry. Non-optional.
   An ungraded data file is how §20 happened.
3. **Field-level provenance, closed vocabulary, empty for unknown.** Not a row-level `recovered` flag:
   the money is first-hand Schedule C data (400/404 verified) and a row-level flag would say otherwise.
4. **Reuse `source_table='recovered'`** if and when it reaches the MCP, with a CHANGELOG note in the
   same shape as the 1.4.0 appendix note, so every previously published total stays interpretable as
   a named slice.
5. **Documentation moves in the same commit:** a `data/recovered/` row in README's repository layout
   and data-files section, a §20 update replacing "Not fixed" with a per-year table in the §13 shape,
   and — separately — the README row for `org_name_recovery_crosswalk.csv` that is currently missing.

---

## 7. The one thing that could flip this

**Option (a), with no provenance column at all, becomes the right answer if the split can be done
entirely inside the Schedule C PDF.**

If a fixed `parse_schedule_c.py` emits the absorbed award as its own row — EIN and amount from the
same text it already reads, `category` / `initiative` / `member` from the same table it is already
parsing — and the disclosure workbook is used **only to verify, never to supply a value**, then this
is a §13-class parser fix. The file-level provenance statement stays true, no column is needed, and
the correct record is a DATA-ANOMALIES per-year before→after table plus a regression test. Strictly
less machinery than (b), and better data.

The evidence that this is plausible is the 400/404 figure above: the absorbed award's own EIN and
amount are already in the repo, captured from the PDF. What is unproven is whether the split is
*deterministic* — whether a rule can cut `"Bronx Defenders 13-3931074 * $2,076,667 Brooklyn Defenders
Services"` into two rows without a judgement call, across all 303 rows and their variants. **That is
what a prototype should answer before this recommendation is acted on.** If it answers yes, take
that road.

**Option (c) becomes right if the `(EIN, amount)` join proves ambiguous at a material rate.**
`recover_org_names.py` refuses any multi-candidate match precisely because EIN alone is unsafe
(13-2612524 carries 229 names). If a large share of the 404 resolve to more than one disclosure
candidate — or if the 55 FY2016 rows turn out to be a class that cannot be keyed at all — then a
published CSV would be asserting awards we cannot individually defend, and a documented gap is the
honest artifact. Publish the gap, not the guess.

**Nothing makes (a)-with-a-column right.** Either the row belongs to the Schedule C PDF (then it
needs no column) or it does not (then it does not belong in that file).

---

## 8. Unknowns and cautions

- **Ambiguity rate of the `(EIN, amount)` join on the 404 embedded pairs is not measured here.** It is
  the single input that decides between (b) and (c), and it belongs to the prototype, not to this
  document.
- **4 of the 404 embedded EINs have no adjacent amount**, and at least one is malformed —
  `'Urban Health Plan, Inc. 15-24042810 $88,855 …'` carries a 10-digit EIN-shaped token. Whatever the
  recovery does, these are a residue that must stay empty rather than be repaired by inference.
- **The 55 FY2016 rows** flagged in the task context as lacking a confirmed disclosure counterpart were
  not re-examined here. If they are a distinct class, they may need a different disposition from the
  other 248 — possibly (c) for those rows even if (b) is chosen for the rest. Mixed dispositions are
  fine as long as the file says which is which.
- **The `csv-parse` extra-column claim is VERIFIED BY READING, not by running.** `mcp/node_modules`
  does not exist in this worktree and the checkout that has it is out of bounds for this task.
- **This document changes nothing.** No file outside `research/missing-absorbed-awards/` was touched.

---

## Commands run (for reproduction)

```bash
cd ~/Code/NYCB-missing

# org_merged row count, embedded EINs, and embedded EIN+amount pairs
python3 - <<'EOF'
import csv, glob, re, collections
EIN  = re.compile(r"\d{2}-\d{7}")
PAIR = re.compile(r"(\d{2}-\d{7})[^0-9$]{0,30}\$\s?([\d,]+)")
rows=ein_hits=pair_hits=with_pair=0
per_year=collections.Counter()
for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
    if "initiatives" in f or "reconcil" in f: continue
    for r in csv.DictReader(open(f, newline="", encoding="utf-8")):
        org = r.get("organization") or ""
        if not (EIN.search(org) or "$" in org): continue
        rows += 1; per_year[f.split("/")[1]] += 1
        e=len(EIN.findall(org)); p=len(PAIR.findall(org))
        ein_hits += e; pair_hits += p
        if p: with_pair += 1
print(rows, ein_hits, pair_hits, with_pair, dict(per_year))
EOF
# -> 303 404 400 269
#    {'fy16':21,'fy17':118,'fy18':121,'fy19':39,'fy20':1,'fy24':1,'fy25':1,'fy26':1}

# detect_type on a hypothetical sidecar
python3 -c "import sys; sys.path.insert(0,'code'); import validate_data as v; \
print(v.detect_type('data/combined/recovered_awards.csv'))"        # -> None

# schema hard-failure demo (scratch copy; nothing in data/ was modified)
python3 code/validate_data.py --data-dir <scratch-with-extra-column>
# -> HARD: [schema] … unexpected columns: ['provenance']

# viz baseline (read-only; --check writes nothing)
python3 viz/schedulec_cleanup.py --check
```

## Files read

- `README.md` (determinism + licensing, lines 5, 28, 92, 108–118, 155–162, 213–228)
- `DATA-ANOMALIES.md` §13, §14, §16, §19, §20
- `code/recover_org_names.py` (the `(EIN, amount)` key choice, lines 49–95; crosswalk write, 173–178)
- `data/combined/org_name_recovery_crosswalk.csv` (header + 1,060 rows)
- `code/validate_data.py` (`ORG_INTEGRITY_TYPES` 62–65, `TYPES` 70–130, `detect_type` 140–167,
  schema check 225–239, `org_merged` detector 343–361, tree glob 481)
- `code/build_combined.py` (`AWARD_COLS` 26–27, `collect` 82–92)
- `mcp/scripts/build-index.mjs` (schema 113–164, awards insert 168–199, appendix load + empty-field
  rule 201–239)
- `mcp/src/db.ts` (`AwardRow` 63–84, `searchAwards` 196–208, `getAwardsByEin` 211–221)
- `viz/schedulec_cleanup.py` (awards bucketing 253–271, clamp 309–316, `reconcile` 328–334)
- `viz/README.md`, `.github/workflows/ci.yml` (version guard paths)
- `source/expense-funding-disclosure/funded_disclosure_FY2017.xlsx` (header + `Source` distribution)
