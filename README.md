# New York City Budget

Machine-readable, reconciled structured data extracted from the **New York City Council's adopted budget documents** — discretionary funding (Schedule C), reporting mandates (Terms & Conditions), and capital changes (Section 254) — for **Fiscal Years 2025, 2026, and 2027**.

Every dollar figure here was extracted **deterministically** from the Council's own PDFs and checked line by line against the documents' printed totals. The FY2027 discretionary schedule reconciles to the exact dollar: **$655,764,999**.

---

## Built by BetaNYC

[**BetaNYC**](https://beta.nyc) is New York's civic organization dedicated to improving lives through public interest technology, open data, and civic design. We build tools, train the public, and advocate for a more transparent, accountable, and participatory city government.

City budgets are among the most consequential public documents there are, and among the least usable — hundreds of pages of PDF tables that resist analysis. This project turns three years of them into clean, joinable data so journalists, researchers, community boards, and New Yorkers can actually ask questions of their city's spending.

**Support open civic data:** [beta.nyc](https://beta.nyc) · [donate](https://beta.nyc/donate) · [newsletter](https://beta.nyc)

---

## Licensing

This repository has two kinds of content under two different terms:

- **Source documents** (`source/`) are **© The City of New York**. They are official NYC Council adopted-budget publications, reproduced here as public records for transparency and analysis. All rights to those documents remain with the City of New York.
- **Software and derived data** — the parser code in `code/`, the extracted CSVs in `data/`, and the [analysis document](Insights-NYC-Council-Discretionary-FY25-FY27.md) — are released under the **MIT License** (see [`LICENSE`](LICENSE)). This code was **built with [Claude](https://claude.ai)**.

If you use the derived data, please attribute BetaNYC and link back to this repository, and cite the City of New York as the source of the underlying documents.

---

## How this was made

Three Python parsers (in `code/`) read the PDF text layer and emit structured rows using regular expressions, with **no hand transcription and no language-model reading of the numbers**. Each Schedule C category total is reconciled against the document's own printed `TOTAL` line, so the data can be trusted or challenged against the source. The Schedule C parser derives its category list and council-member roster from each document, so it adapts to a new fiscal year automatically.

## Repository layout

```
New-York-City-Budget/
├── README.md                                       ← you are here
├── Insights-NYC-Council-Discretionary-FY25-FY27.md ← narrative analysis
├── LICENSE                                         ← MIT, for the code + derived data
├── source/              ← official NYC Council PDFs, © City of New York
│   ├── FY25/  FY26/  FY27/
├── data/                ← extracted, reconciled CSVs
│   ├── fy25/  fy26/  fy27/
│   │   ├── schedule_c/  discretionary expense funding
│   │   ├── terms/       Terms & Conditions (reporting mandates)
│   │   └── capital/     Section 254 capital changes (FY27 only)
│   └── combined/        all-years roll-ups
└── code/                ← the three parser scripts + requirements.txt
```

## The data files

### `data/{year}/schedule_c/{year}_schedule_c_initiatives.csv` — authoritative totals
One row per Council initiative; sums exactly to each category's printed `TOTAL`.
`category, agencies, initiative, amount`

### `data/{year}/schedule_c/{year}_schedule_c_awards.csv` — who got what
One row per designation to a named organization.
`category, initiative, award_type, member, organization, program, ein, amount, agency, purpose`
- `award_type` = `member_item` (an individual Council Member's local designation) or `initiative_provider` (a provider named collectively under a citywide initiative).
- `ein` is the tax ID (digits only) — the reliable join key to IRS 990 / nonprofit data. Organization *names* are best-effort; a minority are imperfect, but the EIN and amount are exact.

### `data/{year}/schedule_c/{year}_appendix_*.csv`
Detail breakouts with a `purpose` field: `_a_aging` (Aging Discretionary), `_b_local` (Local Initiatives, includes an `agency` column), `_c_youth` (Youth Discretionary). These are subsets of the main body re-sorted by funding stream — **do not add them to the Schedule C total.**

### `data/{year}/terms/{year}_terms_and_conditions.csv`
`item_number, agency_name, agency_code, units_of_appropriation, num_units, report_deadlines, coverage_period, condition_text`

### `data/fy27/capital/fy27_capital_projects.csv` (FY2027 only)
`part, agency, budget_line, sub_id, boro, fy1, fy2, fy3, fy4, sponsor, title, building_code, school_code`
`fy1` is the adoption year; `fy2..fy4` are out-years. `boro`: M/X/K/Q/R.

### `data/combined/`
`all_years_initiatives.csv` and `all_years_awards.csv` — the per-year files stacked with a leading `year` column for cross-year analysis.

## Reconciliation status

| Year | Schedule C categories reconciled | Note |
|---|---|---|
| **FY2027** | **25 / 25 exact** | grand total $655,764,999 |
| **FY2026** | 24 / 25 exact | Immigrant Services: the source PDF's own line items exceed its printed total by **$800** |
| **FY2025** | 24 / 26 exact | Education: the source PDF's own line items exceed its printed total by **$50,000** |

The two "misses" are arithmetic inconsistencies **inside the official PDFs**, not extraction errors — the parser faithfully captured both the line items and the printed total, and they disagree in the source. FY2027 capital reconciles 23 of 26 agency subtotals. See each `*_reconciliation.txt` for the line-by-line check.

## Known limitations

- Some `initiative_provider` award rows have imperfect organization *names* (EIN + amount are correct).
- Borough delegations ("Brooklyn", "Queens", …) appear in the `member` column as collective sponsors.
- **FY2025 and FY2026 capital are not included** — the FY2025 file is encrypted and the FY2026 file has a scrambled text layer, both needing layout-aware extraction. Only FY2027 capital is parsed.
- Category names differ across years (FY2025 has a standalone "Libraries" that later folds into "Cultural Organizations"). Normalize before comparing.

## Reproduce or extend to a new year

Requires Python 3 with the packages in `code/requirements.txt` (`pypdf`, `cryptography`):

```bash
python code/parse_schedule_c.py <ScheduleC.pdf> --outdir data/fy28/schedule_c --prefix fy28
python code/parse_terms.py       <Terms.pdf>     --outdir data/fy28/terms      --prefix fy28
python code/parse_capital.py     <Capital.pdf>   --outdir data/fy28/capital     --prefix fy28 \
       --roster data/*/schedule_c/*_schedule_c_awards.csv
```

Always read the generated `*_reconciliation.txt` to confirm a parse before trusting a new year.

---

*Source: NYC Council Finance Division, adopted budget Schedule C, Terms & Conditions, and Section 254 capital changes, FY2025–FY2027, [council.nyc.gov](https://council.nyc.gov/budget/). Structured and analyzed by [BetaNYC](https://beta.nyc).*
