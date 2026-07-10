# `viz/` — NYC Council Discretionary (Schedule C) Funding visualization

An interactive, static visualization of NYC Council discretionary (Schedule C) funding,
**FY2015–FY2027**, built directly on the reconciled CSVs in this repo's `data/` tree — no
live API, no re-parsing of PDFs. FY2027 reconciles to **$655,764,999**.

**Prototype.** See [`PLAN.md`](PLAN.md) for the full design, the two-axis mapping, the
reconciliation gate, and an honest account of where the data does and does not fit the
model.

## Run it locally

```bash
# 1. (Re)generate the cleaned CSV the site consumes
python3 viz/schedulec_cleanup.py          # writes viz/data/schedule_c.csv
python3 viz/schedulec_cleanup.py --check   # reconcile only, don't write

# 2. Serve from inside viz/ (paths are relative; see PLAN.md §6)
cd viz && python3 -m http.server 8802
# open http://localhost:8802/
```

## Tests

```bash
python3 viz/test_schedulec_cleanup.py     # standalone, no deps
# or: pytest viz/test_schedulec_cleanup.py
```

Guards: the FY2027 = $655,764,999 reconciliation gate, both-axes-sum-to-the-same-total,
per-category totals matching the source, the CSV column contract the JS depends on, no
blank numeric cells, and the Itemized ≤ Adopted invariant.

## Files

| Path | What |
|---|---|
| `schedulec_cleanup.py` | Transforms `data/{year}/schedule_c/*.csv` → `data/schedule_c.csv` (the look-at-cook cleaned-CSV format). Stdlib only. |
| `test_schedulec_cleanup.py` | Regression tests (dual-mode: standalone or pytest). |
| `data/schedule_c.csv` | Generated wide CSV the site loads (1,278 leaf rows). |
| `index.html`, `js/`, `css/`, `lib/`, `fonts/`, `images/` | The look-at-cook static site (config + labels adapted for Schedule C). |
| `PLAN.md` | Design, mapping, risks, semantic mismatches. |
| `LICENSE.md` | DataMade's MIT license for the look-at-cook toolkit (retained verbatim). |

## Attribution

This visualization is built on **[look-at-cook](https://github.com/datamade/look-at-cook)**
by **[DataMade](https://datamade.us)** (Derek Eder, Nick Rougeux) and **Open City**,
released under the MIT License (see `LICENSE.md`, retained verbatim). Adapted for NYC
Council Schedule C funding by **[BetaNYC](https://beta.nyc)**.

The visualized data is the reconciled derived data in this repository (MIT, repo `LICENSE`);
the underlying source documents are © the City of New York.
