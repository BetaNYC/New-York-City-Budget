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
| `data/schedule_c.csv` | Generated wide CSV the site loads (1,273 leaf rows). |
| `index.html`, `js/`, `css/`, `lib/`, `fonts/`, `images/` | The look-at-cook static site (config + labels adapted for Schedule C). |
| `PLAN.md` | Design, mapping, risks, semantic mismatches. |
| `LICENSE.md` | DataMade's MIT license for the look-at-cook toolkit (retained verbatim). |

## About BetaNYC

This project is built and maintained by [BetaNYC](https://beta.nyc), New York's
civic technology and open-data community. We work to improve lives in New York
through civic design, technology, data, and public-interest technology.

**Come do civic tech with us.** We run public events, meetups, and hands-on
data classes throughout the year — including [NYC School of Data](https://www.schoolofdata.nyc/)
and [CityCamp NYC](https://citycamp.nyc), and we host frequent civic-tech gatherings. See what's coming up on our
[events calendar](https://www.beta.nyc/events/).

**Sustain this work.** This project is free and open source. To help keep this work going and find BetaNYC's tools, please consider [donating and becoming a Beta Builder](https://beta.nyc/donate).

## Building on this? Tell us!

If you build something with this project, we'd love to hear about it. We can help other New Yorkers find it. BetaNYC publishes a weekly newsletter, *This Week in NYC's Civic Technology and Open Data*.

- **[Subscribe to the newsletter](https://beta.nyc/newsletter)** to keep up with NYC civic tech, open data, and public-interest technology.
- **Built something, or found a story worth sharing?** [Submit a link for the newsletter](https://www.beta.nyc/newsletter-inbox/) and we'll consider it for an upcoming issue.

## Related BetaNYC projects

See the full suite of BetaNYC's civic-data tools at **[beta.nyc/ai-tools](https://beta.nyc/ai-tools)**.

This Schedule C visualization shares its toolkit (DataMade's [Look at Cook](https://github.com/datamade/look-at-cook)) with BetaNYC's citywide budget explorer, **[nyc-budget-viz](https://github.com/BetaNYC/nyc-budget-viz)** — a multi-year visualization of NYC's full **expense budget** (~$114B, every agency, adopted vs. modified), FY2017–FY2027, from NYC Open Data. This repo's `viz/` covers **Council discretionary** funding (~$656M); that one covers the citywide total.

## Attribution

This visualization is built on **[look-at-cook](https://github.com/datamade/look-at-cook)**
by **[DataMade](https://datamade.us)** (Derek Eder, Nick Rougeux) and **Open City**,
released under the MIT License (see `LICENSE.md`, retained verbatim). Adapted for NYC
Council Schedule C funding by **[BetaNYC](https://beta.nyc)**.

The visualized data is the reconciled derived data in this repository (MIT, repo `LICENSE`);
the underlying source documents are © the City of New York.
