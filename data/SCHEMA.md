# `nyc_budget.csv` — schema and methodology

Stable documentation of the cleaned CSV emitted by `nyc_budget_cleanup.py`. This file is the
contract a downstream consumer (the front-end today, an MCP or API tomorrow) can build against
without re-reading the pipeline code.

## Source

- **Dataset:** NYC Open Data "Expense Budget", id `mwzb-yiwb`.
- **API:** Socrata SODA 2.1. Resource `https://data.cityofnewyork.us/resource/mwzb-yiwb.json`,
  metadata `https://data.cityofnewyork.us/api/views/mwzb-yiwb.json`.
- **Auth:** none. Public, read-only. No app token required.
- **Coverage:** Fiscal Years 2017–2027 (inclusive).
- **SODA query reference:** https://dev.socrata.com/docs/queries/

Source field names (confirmed from the metadata endpoint, not guessed):
`publication_date` (text, `YYYYMMDD`), `fiscal_year` (number), `agency_number` (text),
`agency_name` (text), `unit_appropriation_number` (text), `unit_appropriation_name` (text),
`adopted_budget_amount` (number), `current_modified_budget_amount` (number).

## Adopted-snapshot methodology (the anti-triple-count rule)

Each fiscal year is published up to three times — Preliminary (January), Executive (April/May),
and Adopted (June) — and **each publication restates the entire budget**. Summing across
publications counts the same money up to three times.

The pipeline keeps exactly **one `publication_date` per fiscal year: the maximum (Adopted, June)
snapshot**. Because `publication_date` is zero-padded `YYYYMMDD` text, its lexical maximum equals
its chronological maximum. The snapshot dates are discovered dynamically from the data, so the
method survives future publications rather than hard-coding dates.

**Validation gate:** after filtering, the FY2026 Adopted total must fall within
`[110B, 118B]`. The published FY2026 adopted expense budget is **$114,384,991,832** (~$114.385B);
a triple-count regression would read ~$343B and abort the run before any CSV is written.

## Grain

One row per `(agency_number, unit_appropriation_number)` pair — an agency's unit of
appropriation. As of the last regeneration: **1,313 rows across 146 agencies**. Amounts within a
`(agency, unit, fiscal_year)` group are summed. Display names resolve to the latest fiscal year
present, so agency/unit renames show their most recent label.

## Columns

Header names are **case-sensitive** and must not change without a matching change in
`js/app.js` (see the coupling note below).

### Static columns

| Column | Meaning | v1 source |
|---|---|---|
| `Fund` | Top-level grouping | `agency_name` |
| `Department` | Sub-grouping under Fund | `unit_appropriation_name` |
| `Control Officer` | Second top-level axis | `agency_name` (**v1 placeholder** — duplicates `Fund` so the front-end's second view renders; a real second axis, e.g. object class, replaces this later) |
| `Department ID` | Stable id for the unit | `unit_appropriation_number` (zero-padded string; keep as text) |
| `Short Title` | — | empty in v1 |
| `Link to Website` | — | empty in v1 |
| `Department Description` | — | empty in v1 |

### Per-fiscal-year columns

For each fiscal year `YYYY` in 2017–2027, two columns:

| Column | Meaning | Source |
|---|---|---|
| `Adopted YYYY` | Adopted budget for that agency-unit in `YYYY` | `sum(adopted_budget_amount)` over the group |
| `Modified YYYY` | Current modified budget at the Adopted snapshot | `sum(current_modified_budget_amount)` over the group |

Values are written plain — no `$`, no thousands separators. Whole-dollar amounts render as
integers; cents are preserved only when actually present. Consumers should parse them as floats.

### Column/label coupling (do not drift)

`js/app.js` reads each year's value with the key `<label> + ' ' + year`, where `label` is the
config's `apropTitle` (`'Adopted'`) or `expendTitle` (`'Modified'`). The CSV column **prefixes**
here must equal those labels exactly. The pipeline centralizes them in `APROP_LABEL` /
`EXPEND_LABEL`; rename one side and you must rename the other, or the chart reads `NaN`.

## Regenerating

```bash
python3 data/nyc_budget_cleanup.py            # writes data/nyc_budget.csv (full) + sample
python3 data/nyc_budget_cleanup.py --sample-only   # sample only (fast)
python3 data/nyc_budget_cleanup.py --out DIR       # write into DIR
```

Stdlib only (`urllib`, `csv`, `json`) — no third-party dependencies. Idempotent: re-running
overwrites the output deterministically. Read-only against the API; writes only local CSVs.

## Notes for a future MCP / API

- The `(agency, unit)` grain and the Adopted-snapshot rule are the stable primitives — an MCP
  should expose totals filtered to the adopted snapshot, never the raw multi-publication rows.
- Keep `agency_number` / `unit_appropriation_number` as **strings**; they are zero-padded and
  casting to int drops leading zeros (`040` → `40`).
- The `Control Officer` placeholder is the one field that is not yet a real second dimension;
  design any second-axis query around a real field (e.g. object class) rather than this column.
