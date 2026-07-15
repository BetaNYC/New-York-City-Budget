---
title: "NYC Council Discretionary & Budget Analysis, FY2025–FY2027"
created: 2026-07-06
updated: 2026-07-15
type: analysis
status: draft
area: civic-tech
source: marvin
tags: [nyc-budget, schedule-c, discretionary-funding, open-data, city-council]
---

# NYC Council Budget: What the Numbers Say, FY2025–FY2027

**Report generated:** 2026-07-06
**Data current as of:** 2026-07-06 (source PDFs downloaded from council.nyc.gov and supplied locally)
**Last revised:** 2026-07-15 (FY2025 and FY2026 Section 254 capital now parsed and reconciled; capital section and extraction-limitation notes updated accordingly)
**Scope:** Three adopted-budget document types across three fiscal years — Schedule C (discretionary expense funding), Terms & Conditions (reporting mandates), and the Section 254 Capital changes (FY2025–FY2027). All figures are extracted directly from the Council's own PDFs and reconciled against the documents' printed totals.

> **How to trust these numbers.** Every dollar figure below comes from a deterministic parse of the source PDF, not a hand transcription or a language-model reading. The Schedule C category totals were checked line by line against each document's own printed `TOTAL` and match to the dollar in all but two cases, both of which are arithmetic errors inside the official PDFs (documented at the end). Where a figure is best-effort, it is labeled.

---

## The headline

NYC Council discretionary (Schedule C) funding, by adopted total:

| Fiscal year | Discretionary total | Change |
|---|--:|--:|
| **FY2025** | $534,963,682 | — |
| **FY2026** | $665,080,821 | +$130.1M (+24.3%) |
| **FY2027** | $655,764,999 | −$9.3M (−1.4%) |

The story of these three years is a single large step up between FY2025 and FY2026, then a slight pullback into FY2027. The composition of that money changed far more than the top line did.

---

## Where the growth went: category shifts

The FY2025→FY2026 jump was not spread evenly. A few categories moved hundreds of times more than others. Category totals (reconciled to the printed `TOTAL` lines):

| Category | FY2025 | FY2026 | FY2027 | FY25→FY27 |
|---|--:|--:|--:|--:|
| Immigrant Services | $35,237,141 | $86,092,141 | $86,417,141 | **+$51.2M** |
| Speaker's Initiative (Citywide Needs) | $3,370,000 | $96,080,500 | $86,522,049 | **+$83.2M** |
| Mental Health | $29,142,110 | $40,642,110 | $40,767,110 | +$11.6M |
| Food | $11,893,750 | $27,018,750 | $27,018,750 | +$15.1M |
| Higher Education | $24,511,869 | $29,411,869 | $29,561,869 | +$5.1M |
| Public Safety | $27,961,475 | $5,715,600 | $5,785,600 | **−$22.2M** |
| Small Business & Workforce Dev. | $64,277,500 | $33,961,475 | $33,252,902 | **−$31.0M** |
| Criminal Justice | $37,811,645 | $33,407,284 | $33,470,153 | −$4.3M |

Four movements stand out:

1. **Immigrant Services more than doubled** and then held. The increase is concentrated in two initiatives: the New York Immigrant Family Unity Project ($24.9M in FY2027) and Unaccompanied Minors and Families ($16.98M). This is the Council's discretionary footprint on the migrant response.
2. **The Speaker's Initiative to Address Citywide Needs went from a rounding error to the single largest category.** It was $3.37M in FY2025 and roughly $86–96M in the two later years. This is the biggest structural change in the dataset, and it means a growing share of discretionary money is being directed centrally rather than through the older category structure.
3. **Public Safety and Small Business/Workforce both fell sharply.** Public Safety dropped from $27.96M to under $6M; Small Business & Workforce Development fell from $64.3M to about $33M. Some of this is reclassification rather than pure cuts, but the net direction is clear.
4. **Food funding more than doubled** ($11.9M → $27.0M), led by Feeding Our Communities ($13M) and Food Pantries ($10.5M).

### A structural change worth flagging

FY2025 had **26 discretionary categories**, including a standalone **Libraries** category ($15.7M) and a singular "Cultural Organization." FY2026 and FY2027 have **25 categories**: Libraries was folded into Cultural Organizations, which is why Cultural Organizations appears flat at $34.35M while Libraries disappears. Anyone comparing category lists across years needs to account for this merge.

Also note: in FY2025 there is **no main-body Youth Services initiative summary** — Youth discretionary money that year lived entirely in the Youth Discretionary appendix.

---

## How discretionary money actually flows

Schedule C money moves through two channels, and they are very different in size:

| Channel | FY2025 | FY2026 | FY2027 |
|---|--:|--:|--:|
| **Citywide initiatives** (Council directs, providers named collectively) | $317.2M | $373.7M | $495.1M |
| **Member items** (individual Council Members' local designations) | $93.0M | $109.9M | $105.8M |

The takeaway: **the large majority of discretionary dollars flow through citywide initiatives, not individual member items.** Member items are numerous (roughly 3,600–3,900 designations a year) but small on average; the citywide initiatives are where the real money is. The gap between these award totals and the full category totals (about $50M in FY2027) is money the Council designates after adoption ("post-adoption").

---

## The biggest initiatives (FY2027)

| Amount | Category | Initiative |
|--:|---|---|
| $86,522,049 | Speaker's Initiative | Speaker's Initiative to Address Citywide Needs |
| $24,900,000 | Immigrant Services | New York Immigrant Family Unity Project |
| $19,962,000 | Criminal Justice | Alternatives to Incarceration and Reentry |
| $17,340,000 | Cultural Organizations | Cultural After-School Adventure (CASA) |
| $16,981,800 | Immigrant Services | Unaccompanied Minors and Families |
| $16,411,869 | Higher Education | Peter F. Vallone Academic Scholarship |
| $14,500,000 | Community Development | NYC RISE with Adult Literacy Forward |
| $14,280,000 | Environmental | NYC Cleanup |
| $13,000,000 | Food | Feeding Our Communities |
| $12,010,000 | Domestic Violence | Domestic Violence and Empowerment (DoVE) |

---

## Who receives the money

Aggregating award designations by tax ID (EIN) across all three years. **The EIN and dollar figures are exact; the organization names are best-effort** and a few are imperfect fragments of the source text (noted where known). Use the EIN as the reliable key.

| Recipient (EIN) | 3-yr total | FY25 | FY26 | FY27 |
|---|--:|--:|--:|--:|
| New York Public Library (13-6400434) *(labeled "City Clerk" in raw extract)* | $108.4M | $27.0M | $30.3M | $51.1M |
| Legal Aid Society (13-5562265) | $42.2M | $11.6M | $10.7M | $19.8M |
| City University of New York (13-3893536) | $35.1M | $3.7M | $4.9M | $26.5M |
| UFT Educational Foundation (13-9226721) | $25.2M | $9.5M | $7.5M | $8.3M |
| Defender Services (11-3305406) | $23.1M | $6.6M | $6.8M | $9.7M |
| Assoc. of Community Employment Programs (13-3846431) | $18.9M | $5.5M | $6.5M | $6.9M |
| Consortium for Worker Education (13-3564313) | $15.8M | $0.01M | $8.0M | $7.9M |
| Fortune Society (13-2645436) | $12.6M | $3.1M | $4.7M | $4.9M |
| Bronx Defenders (13-3931074) | $11.6M | $0.7M | $1.4M | $9.6M |

**Pattern:** legal-services and criminal-justice organizations (Legal Aid, Bronx Defenders, Defender Services, Fortune Society) are among the largest recipients, consistent with the size of the Legal Services and Criminal Justice categories. The New York Public Library's designations grew notably into FY2027.

---

## By administering agency (FY2027 member items)

The city agency that actually administers the contract:

| Agency | Member-item $ |
|---|--:|
| DYCD (Youth & Community Development) | $63.1M |
| DCLA (Cultural Affairs) | $35.1M |
| DSS/HRA (Social Services) | $14.3M |
| DFTA (Aging) | $12.1M |
| DHMH (Health & Mental Hygiene) | $7.0M |
| DPR (Parks) | $6.2M |

DYCD administers the plurality of member-directed discretionary spending, followed by Cultural Affairs.

---

## By Council Member (FY2027 member items)

Member items are small and numerous. Among individual members, the FY2027 leaders by designated dollars were Riley ($2.18M, 60 items), Hanks ($2.09M), Williams ($2.07M), Zhuang ($1.97M), and Mealy ($1.95M). Most members land in a fairly tight band of roughly $1.5M–$2.2M across 60–100 designations.

Two large entries — "Brooklyn" ($16.1M) and "Queens" ($3.1M) — are **borough delegations** acting as collective sponsors, not individual members, and should be read separately.

---

## The stable base: appendix programs

Three appendix programs are strikingly consistent year to year, suggesting formula-driven allocations:

| Program | FY25 | FY26 | FY27 |
|---|--:|--:|--:|
| Aging Discretionary | $5,610,000 | $5,610,000 | $5,610,000 |
| Local Initiatives | $36,539,000 | $36,534,000 | $36,539,000 |
| Youth Discretionary | $7,650,000 | $7,650,000 | $7,650,000 |

The Aging and Youth appendix totals are identical to the dollar all three years; Local Initiatives varies by only a few thousand.

---

## Oversight is growing: Terms & Conditions

The Council attaches reporting mandates ("Terms and Conditions") to appropriations. These grew each year:

| Year | Conditions | Units of Appropriation referenced |
|---|--:|--:|
| FY2025 | 65 | 156 |
| FY2026 | 68 | 178 |
| FY2027 | 75 | 206 |

The **Department of Education is the most-conditioned agency every year** (16–17 conditions), reflecting both its size and the Council's focus on school-level transparency. About 60 of each year's conditions carry an explicit reporting deadline.

---

## Capital (Section 254)

All three years of Section 254 capital changes are now parsed and reconciled, so cross-year capital comparison is available. The FY2027 detail is broken out below; FY2025 and FY2026 per-year figures are in the README's capital summary and each `*_reconciliation.txt`.

The **FY2027** Section 254 capital changes contain **1,358 project lines** totaling roughly **$992.5M** across the three detail parts (city, non-city, and by non-city entity). Distribution of the adoption-year amounts:

- **By borough:** Queens $262.3M, Manhattan $251.2M, Brooklyn $229.7M, Bronx $172.7M, Staten Island $76.3M.
- **By agency:** Education $225.5M, Parks $182.1M, Cultural Institutions $110.4M, Public Buildings $62.7M, Housing & Development $53.5M.

*Reconciliation status:* **FY2025** reconciles **30/30** agency subtotals plus both grand totals exactly — Part I (Council capital additions, directly comparable to FY2026/FY2027) **$775,000,000 / 1,327 projects**, Part II (non-city) **$158,992,000 / 181 projects**, Part III (non-city-by-entity cross-tab) 106/106 entities. **FY2026** reconciles **31/31**. **FY2027** reconciles **24 of 26** agency subtotals exactly; two agencies (Housing & Development and Human Resources) carry minor in-source formatting differences (see `data/fy27/capital/fy27_capital_reconciliation.txt`). The FY2025 canonical detail is parsed from the Council-version supporting-detail book; the broader FY2025 appropriation-changes book (~$5.2B of all executive-capital changes) is a different document type, retained for provenance only and labeled `NOT RECONCILABLE`.

---

## Data-quality findings (surfaced by the parse)

Deterministic parsing catches things a manual read would miss. Two are arithmetic errors **inside the official PDFs**:

1. **FY2026 Immigrant Services:** the listed initiatives sum to $86,092,141 but the document's printed `TOTAL` says $86,091,341 — an **$800 discrepancy in the source document**.
2. **FY2025 Education:** the listed initiatives sum to $39,974,300 but the printed `TOTAL` says $39,924,300 — a **$50,000 discrepancy in the source document**.

In both cases the extraction faithfully captured both the line items and the printed total; they simply disagree in the source. Every other category in all three years reconciles to the dollar.

Known extraction limitations (do not affect reconciled totals): a minority of citywide-initiative award rows have imperfect organization *names* (the EIN and amount are correct); borough delegations appear alongside individual members in the member list.

---

## What you can do with the structured data

The parse produced analysis-ready CSVs (see `Outputs/`). Because every award carries an EIN, the data joins directly to:
- **IRS 990 / nonprofit data** (via EIN) — recipient financial health, other funding.
- **Council district and member rosters** — geographic and political analysis.
- **City agency contract data** — follow the money from designation to contract.

The reconciled initiative-level file is the authoritative view of how much each Council initiative received; the award-level file is the granular who-got-what.

---

*Prepared by Marvin (BetaNYC workspace). Source documents: NYC Council Finance Division, adopted budget Schedule C, Terms & Conditions, and Section 254 capital changes, FY2025–FY2027, council.nyc.gov.*
