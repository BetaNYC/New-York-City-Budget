# Schedule C Visualization — Plan & Design Notes

**Status:** working prototype (local render verified). Not yet deployed.
**Built:** 2026-07-10 · **Branch:** `feat/schedule-c-viz`
**Toolkit:** DataMade [look-at-cook](https://github.com/datamade/look-at-cook) (MIT), repurposed for NYC Council discretionary (Schedule C) funding.

This document records how Schedule C is mapped onto the look-at-cook model, what the
prototype renders, the reconciliation gate, and — honestly — where the data does *not*
fit the model cleanly.

---

## 1. What look-at-cook expects

look-at-cook is a static site (`index.html` + `js/app.js` + `data/<cleaned>.csv`, loaded
via jquery-csv) that renders a **wide, one-row-per-leaf CSV** with **per-year measure
columns**, and drills through a **two-axis hierarchy** to a shared leaf:

```
hierarchy = { Fund: ['Fund','Department'], 'Control Officer': ['Control Officer','Department'] }
```

Two top-level views (`Fund`, `Control Officer`) each drill to the same leaf (`Department`).
The JS **hard-codes the column names** `Fund`, `Control Officer`, `Department` (plus
`Department ID`, `Short Title`, `Link to Website`, `Department Description`), and derives
each per-year column key as **`apropTitle + ' ' + year`** / **`expendTitle + ' ' + year`**.
Two chart lines are drawn per slice: `apropTitle` (line 1) and `expendTitle` (line 2).

## 2. The mapping chosen

We **keep** the three hard-coded column names and repurpose them semantically:

| look-at-cook slot | column name (kept) | Schedule C meaning |
|---|---|---|
| Axis 1 — "Where's it going?" | `Fund` | **Schedule C category** (Anti-Poverty, Older Adult Services, …) |
| Axis 2 — "Who administers it?" | `Control Officer` | **Administering agency**, bucketed (see §5) |
| Shared leaf | `Department` | **Initiative** |

- **Leaf identity** = the tuple `(category, initiative)`, which is unique within any year
  (verified). Each leaf row carries the **full** initiative dollars; grouping by *either*
  axis re-sums the same rows, so **both axes reconcile to the same grand total** — no
  dollars are split. (Enforced by `test_both_axes_sum_to_same_grand_total_each_year`.)
- **Year range:** **FY2015–FY2027** (`startYear=2015, endYear=2027, activeYear=2027`).
  FY2015 is the earliest year with the modern reconciled Schedule C schedule; FY2027 is
  the latest in the repo. (FY2009–FY2014 exist but are initiatives-only with a different,
  UPPERCASE category vocabulary — see §5.)

### Config wired in `js/app.js`

```
startYear = 2015; endYear = 2027; activeYear = 2027;
municipalityName = 'NYC Council Discretionary Funding';
apropTitle  = 'Adopted';    // line 1 — MUST equal the CSV column prefix
expendTitle = 'Itemized';   // line 2 — MUST equal the CSV column prefix
dataSource  = 'data/schedule_c.csv';   // RELATIVE (see §6)
```

## 3. The two chart lines

Schedule C is a **single-measure** dataset (one figure: dollars). Rather than collapse the
toolkit's second series, we use both slots as two **real, additive** measures:

- **`Adopted <year>`** — the initiative's adopted discretionary total, from
  `data/{year}/schedule_c/{year}_schedule_c_initiatives.csv`. This is the **authoritative,
  reconciled** figure. **FY2027 grand total = $655,764,999**, to the dollar.
- **`Itemized <year>`** — dollars from that initiative designated to a **named recipient
  organization**, from `{year}_schedule_c_awards.csv`, summed per `(category, initiative)`
  and **clamped to never exceed** the adopted amount (see §5, Risk B). This is a
  **lower bound**, materially complete only in recent years.

The visible **gap** between the two lines is discretionary money **not traceable to a
named recipient** at the initiative level — lump-sum / citywide initiatives (e.g. the
Speaker's Initiative), plus the residue of the imperfect name join.

## 4. What the prototype renders (verified locally)

Served from `viz/` (`python3 -m http.server`, port 8802) and loaded in a browser:

- **Main chart:** Adopted line climbs $233M (FY2015) → **$655,764,999 (FY2027)**; the
  Itemized lower-bound line sits below it, near-zero in early years and rising to ~$483M
  in FY2027.
- **Scorecard** shows FY2027 = **$655,764,999.00** (the gate, visible in the UI).
- **Axis 1 (by category):** Speaker's Initiative $86.5M (Itemized $0 — correct, it's a
  lump), Immigrant Services $86.4M, Community Development $45.2M, Education $43.3M, …
- **Axis 2 (by agency):** same grand total ($655,764,999) — Multiple agencies $276.2M,
  Unspecified agency $96.4M, DSS/HRA $84.9M, DHMH $52.5M, DYCD $40.1M, …
- **Drill-down** (`+`) into a category/agency to its initiatives works.

## 5. Fit, risks, and semantic mismatches (read this)

**The core mismatch:** the reconciled grand total ($655,764,999) lives in the
**initiatives** file, which has **no council-member and no organization** columns. The
rich "who sponsored / who received" dimensions live in the **awards** file, which sums to
only **$605.1M** (≈$50.6M less) and therefore **cannot** carry the headline total. So the
primary measure is initiatives-based by necessity, and the compelling award-level "who"
detail is relegated to the (imperfect) second line. This is inherent to the data, not a
toolkit limitation.

- **Risk A — the Itemized line is unreliable in older years.** The award→initiative match
  is by initiative-name string, which drifts across the independently-parsed years. Match
  rate by year (awards $ matched to an initiative row): FY2015 65%, **FY2016–FY2019
  ~0%**, FY2020 7%, FY2021 17%, FY2022 2%, FY2023 56%, FY2024 44%, FY2025 46%, FY2026 47%,
  **FY2027 82%**. The Itemized line therefore **understates** true itemization before
  ~FY2023 and should be read as a lower bound. The **Adopted** line is clean for all 13
  years and is the figure to trust. *(Disclosed on-page in the About section.)*
- **Risk B — the name join also *over*-attributes in ~13 leaf-years** (two source
  initiatives colliding on one name key), producing raw Itemized > Adopted. We **clamp**
  Itemized to Adopted per leaf-year so the chart is never nonsensical; this is why Itemized
  is defined as a lower bound. (Enforced by `test_itemized_never_exceeds_adopted_per_leaf_year`.)
- **Risk C — the Agency axis is coarse.** The initiatives file's `agencies` field is
  multi-valued for 46/170 FY2027 rows and blank for 4. We bucket: single→that agency,
  comma-list→`"Multiple agencies"`, blank→`"Unspecified agency"`. Result: the two largest
  FY2027 agency buckets are "Multiple agencies" ($276M) and "Unspecified agency" ($96M) —
  honest but low-resolution. A production version would want a member/borough axis instead
  (available only in the awards file — see Risk A) or a per-initiative primary-agency
  assignment owned by the domain agent.
- **Risk D — category vocabulary drifts across years.** FY2015 categories are UPPERCASE
  and some names differ (README: "Libraries" later folds into "Cultural Organizations").
  Because `Fund` = the raw category string, a renamed category appears as a *separate* axis
  value across years, fragmenting some cross-year lines. Normalizing categories is
  **domain/editorial judgment** (metrics-insights / archivist), not viz code, and is left
  out of this prototype.
- **Risk E — leaf count.** 1,278 leaf rows (13 years of initiatives). look-at-cook handles
  this (the reference NYC config carried ~1,300 rows); performance is fine.
- **Known cosmetic item:** the header title wraps and overlaps the subtitle at narrow
  (~800px) widths — the DataMade theme was sized for the short "Look at Cook" title. Purely
  visual; does not affect data, chart, or interaction. Left for a polish pass.

## 6. Deployment notes

- **Serve from inside `viz/`.** `dataSource` and the Backbone template dir were changed
  from absolute (`/data/...`, `/js/views`) to **relative** (`data/...`, `js/views`) on
  purpose: this viz lives in a `/viz` subfolder of a repo that *also* has a top-level
  `/data` tree, so an absolute `/data/` would collide with the repo's source CSVs.
- **Regenerate the data:** `python3 viz/schedulec_cleanup.py` (writes
  `viz/data/schedule_c.csv`). `--check` reconciles without writing; `--start/--end` change
  the year range. Stdlib-only, no third-party deps.
- **Tests:** `python3 viz/test_schedulec_cleanup.py` (dual-mode; also `pytest`-collectable).

## 7. Licensing / attribution

The toolkit is DataMade's look-at-cook (MIT). `viz/LICENSE.md` retains DataMade's copyright
verbatim; attribution to DataMade, Derek Eder, Nick Rougeux, and Open City is preserved in
the page footer and About section. The repo's derived data is MIT (repo `LICENSE`); the
underlying documents are © City of New York.

## 8. What's left (not done in this prototype)

- Deploy decision (the orchestrator will surface the push/PR step to Noel — **not pushed**).
- A member / borough-delegation axis (needs the awards file and its member column; blocked
  on the awards/initiatives reconciliation gap and name-join reliability — a domain task).
- Category-name normalization across years (domain/editorial).
- Header/theme polish (title overlap; BetaNYC brand colors, logo, favicon).
- Optional: a per-initiative "primary agency" assignment to shrink the "Multiple agencies"
  bucket, and wiring the `Link to Website` / richer descriptions.
