# IBO Data Center ↔ New-York-City-Budget: inventory, findings, and crosswalk

**Report generated:** 2026-07-08
**Data current as of:** 2026-07-08 (IBO Data Center and NYC Open Data catalog observed live this date)
**Author:** research-intelligence (for the `New-York-City-Budget` repo)
**Status:** Draft for orchestrator review. Uncommitted. Read-only research; no other repo file was edited.

---

## Summary (read this first)

- **Noel's observation #1 (IBO is not on the Open Data Portal) is incorrect.** IBO publishes **20 datasets** on NYC Open Data (`data.cityofnewyork.us`) under the agency name **"NYC Independent Budget Office (IBO)."** They mirror the Data Center's fiscal-history series (revenue/spending summary, agency expenditures, capital expenditures, debt, headcount, tax effort) plus COVID spending trackers. The correct statement is narrower: IBO's *analytical publications* (fiscal briefs, budget-option reports, testimony) are not on the portal, and the Open Data copies of some series lag the Data Center (several cap at FY2018/FY2020).
- **Noel's observation #2 (no Schedule C on the Data Center) is correct, and stronger than stated.** The Data Center has **no reference to "Schedule C," "discretionary," or "member items"** anywhere. Verified across all eight Data Center panels plus the page body. IBO's entire budget-data offering is **aggregate** — citywide and agency-level totals, revenue, debt, headcount, education, tax — with **no designation-level, member-item, organization-level, or EIN-level data of any kind.**
- **The single most important finding:** the intersection between IBO's data and this repo is **essentially empty**, and that is the point. IBO owns the top-down, decades-long *fiscal-context* picture (what the City spends by agency, raises by tax, owes in debt). This repo owns the bottom-up *who-got-what* picture (which organization, which Council member, how much, which EIN) that IBO does not publish at all. They are complementary, not competing. This repo fills a real gap in the NYC budget-data ecosystem.

---

## 1. IBO Data Center inventory

**Source:** <https://www.ibo.nyc.gov/content/data-center> (the page is JavaScript-rendered; WebFetch returned only the shell, so this was inventoried live in a browser). The Data Center is an eight-panel accordion under three headings. Format is overwhelmingly **downloadable Excel files** plus some interactive charts/tables.

### A. NYC Fiscal History — "fiscal history and staffing levels citywide and by agency"

| Product | What it is | Coverage |
|---|---|---|
| Fiscal History Data for **Current City Agencies** | Citywide Summary + per-agency expenditure/revenue/positions history. Agency list includes "City Council," "Borough Presidents," etc. — this is each body's **operating budget as an agency**, not Council designations. | Long historical series |
| Fiscal History Data for **Former Agencies** | Same series for dissolved bodies (Board of Estimate, etc.) | Historical |
| **NYC Fiscal History Data Tables** (Excel) | All Revenue; Agency Expenditures; Actual Full-Time Positions; Tax Revenues; Other Non-Tax Revenues; Grants & Aid; **Capital Expenditures Since 1985** | FY1980-era → recent (Open Data mirrors cap ~FY2018–FY2020) |

### B. More Budget and Financial Data

| Product | What it is | Coverage |
|---|---|---|
| **Education Spending Since 1990** (Excel) | "Chart Book Data Tables" | Since 1990 |
| **Debt Service Since 2000** (Excel) | Debt Service; Debt Outstanding | Since FY2000 |
| **New York City Tax Effort** (Excel) | Background/methodological notes + historical tables | Historical (tax effort series since 1929 on the Open Data copy) |
| **NYC Residents' Income and Tax Liability** (Excel) | One file per tax year | Tax years 2006–2023 |

### C. Historical Dashboards (explicitly "no longer being updated")

- Federal Covid Relief Spending Dashboard
- NYC Covid-19 Spending Tracker

### Beyond the Data Center

IBO's principal output is **Publications**, not datasets: analyses of the Preliminary / Executive / Adopted budgets, fiscal briefs, "Budget Options," revenue/economic forecasts, and testimony, organized by topic (education, infrastructure, housing, city-budget-overview, workforce, environment). These are **analytical PDFs**, discoverable via IBO's site and the City's Government Publications Portal (`a860-gpp.nyc.gov`) — not structured, machine-readable data.

**Update cadence / licensing:** the Data Center states no explicit update cadence or license on-page; the historical dashboards are flagged as frozen. The Open Data mirrors carry standard NYC Open Data terms of use and per-dataset "last update" metadata (which is how the FY2018/FY2020 lag is visible).

---

## 2. The Schedule C question — CONFIRMED (no reference)

**Finding:** after checking **all eight Data Center panels** (Current Agencies, Former Agencies, Fiscal History Data Tables, Education, Debt, Tax Effort, Resident Income/Tax, Historical Dashboards) and the page body, there is **no reference to "Schedule C," "discretionary," "member item," or "member items"** on the IBO Data Center. A `site:ibo.nyc.gov` search for those terms returns only analytical report PDFs (units of appropriation, CCRB staffing, Fair Fares, pensions, etc.) — none is a discretionary/designation **data product**.

**Precise statement:** IBO does not publish discretionary / Schedule C / member-item designation data — not in aggregate as a data file, and not at the organization or EIN level — anywhere on the Data Center. The most IBO does with member-item money is occasional **narrative analysis inside individual reports**; it has never been a structured dataset. So this repo's designation-level Schedule C data has **no IBO counterpart**.

---

## 3. The Open Data Portal question — Noel's premise CORRECTED

**Finding:** IBO **is** on `data.cityofnewyork.us`. A catalog browse filtered to agency **"NYC Independent Budget Office (IBO)"** returns **20 datasets**, including:

- NYC IBO Revenue And Spending Summary FY1980–FY2020 (`7zhs-43jt`)
- NYC IBO Agency Expenditures FY1980–2018
- NYC IBO Capital Expenditures Since 1985
- NYC IBO Debt Service Since FY2000 (`6ggx-itps`) and Debt Outstanding Since FY2000 (`5i9t-mvdt`)
- NYC IBO Full Time Positions in city government, by fiscal year
- NYC IBO State And Federal Categorical Aid FY1980–2020 (`fu34-wamz`); Non-Tax Revenues FY1980–FY2020
- Annual Tax Effort in NYC since 1929; Income By Type Of Income And AGI Range
- IBO Federal Stimulus / COVID-19 spending trackers (ARPA/CRRSAA; by agency; by expense type; by date)

So the Data Center's fiscal-history series **is** substantially mirrored on Open Data as IBO-published datasets. **None of the 20 is discretionary/Schedule C/member-item data** — consistent with §2.

**On the "separate charter office → not subject to the Open Data Law" theory:** IBO is created by **NYC Charter §259 (Chapter 11)** as an independent office, not a mayoral agency. But the Open Data Law's definition of "agency" (Admin. Code **§23-501**) is broad — "an office, administration, department, division, bureau, board, commission, advisory committee or other governmental entity performing a governmental function of the city of New York" — which plausibly reaches IBO, and **empirically IBO does publish to the portal.** So the theory is weakened: the reason IBO's *full* output (especially its reports, and the most current cuts of some series) is not all on the portal is more likely practical/editorial than a clean legal exemption. **Flag for counsel** before asserting IBO's Open Data Law status either way; this note does not resolve it.

---

## 4. Crosswalk: this repo vs. IBO (and adjacent sources)

The grain is the whole story. This repo is **designation-level** (one row per award/organization). IBO is **aggregate** (citywide/agency totals and long time series).

| Budget dimension | This repo (`New-York-City-Budget`) | IBO Data Center / IBO Open Data | Relationship |
|---|---|---|---|
| **Discretionary designations (Schedule C):** org, sponsoring Council member, amount, agency, **EIN**, program | ✔ Core product. Award/EIN level FY2015–FY2027; initiatives-only FY2009–FY2014 | ✘ Nothing at any grain | **WE ARE UNIQUE** |
| **Post-adoption designations (Transparency Resolutions):** designate/rescind/purpose-change | ✔ FY2010–FY2024 + FY2026 | ✘ | **WE ARE UNIQUE** |
| **Terms & Conditions** (reporting mandates on appropriations) | ✔ FY2015–FY2024, FY2025–FY2027 | ✘ | **WE ARE UNIQUE** |
| **Legislative provenance** (Legistar matter #, adoption date, URL) | ✔ Crosswalk, FY2008–FY2027 | ✘ | **WE ARE UNIQUE** |
| **§254 Council capital *changes*** (project, borough, sponsor) | ✔ FY2020, FY2022–FY2027 (project-level, Council amendments) | ✘ project-level; IBO has only **Capital Expenditures Since 1985** (citywide/agency aggregate) | **COMPLEMENT** (different grain: Council's line-item changes vs. citywide capital spend over time) |
| **Agency expense budget / actual expenditures** | ✘ | ✔ Agency Expenditures FY1980+ (aggregate) | **IBO UNIQUE** |
| **Revenue** (tax, non-tax, state/federal aid) | ✘ | ✔ FY1980+ | **IBO UNIQUE** |
| **Debt service / debt outstanding** | ✘ | ✔ Since FY2000 | **IBO UNIQUE** |
| **Headcount / full-time positions** | ✘ | ✔ By fiscal year | **IBO UNIQUE** |
| **Education spending, tax effort, resident income/tax** | ✘ | ✔ Long series | **IBO UNIQUE** |
| **Fiscal analysis, forecasts, budget options, testimony** | ✘ | ✔ Publications (PDF, not data) | **IBO UNIQUE** |
| **The Council as a spending body** | Council **designations** (money it directs to outside orgs) | Council **operating budget** (its own agency expenditures, in fiscal history) | **COMPLEMENT** (two different objects that share the word "Council") |

**Adjacent, non-IBO sources worth naming in the same ecosystem map:**
- **NYC Open Data — "City Council Discretionary Funding" (`4d7f-74pe`, FY2009–FY2021, ~97k rows, Council-published, stopped updating April 2021).** This is the *only* other structured, award-level discretionary source. It **overlaps** our Schedule C for FY2015–FY2021, and our repo is the unique source for **FY2022–FY2027** (after it went stale) and adds source-reconciliation rigor, Terms, Capital, Transparency, and Legistar provenance. (Scoping already lodged in `research/2026-07-07-fy09-fy21-legacy-import-scoping.md`.)
- **NYC Checkbook (Comptroller)** — actual spending/contracts; the "did the designation become a paid contract?" join (already in the repo's Future Work).

**The gap that matters:** neither IBO nor (post-FY2021) NYC Open Data publishes machine-readable, EIN-level Council discretionary designations from the adopted budget. This repo is the source that closes it, and IBO is the source that supplies the fiscal context this repo intentionally omits.

---

## 5. Recommended placement for the contextualization

**Recommendation: one durable home, one light touch — do not scatter.**

1. **Primary (do this): add a "How this relates to other NYC budget data sources" section to the repo `README.md`,** placed just after "Cross-reference it with the rest of the city's record" / before "Future work." It gives readers an honest ecosystem map — what this repo is, what it is *not*, and where to go for the rest. Draft below, ready to paste.
2. **Secondary (recommend to Noel, do not edit): one sentence + IBO link in the blog draft's "Cross-reference it with the rest of the city's record" list,** positioning IBO as the *fiscal-context* complement. The blog already thanks the Open Data team; adding IBO as a named neighbor strengthens the "we fill a gap" narrative without diluting the ask. Suggested line: *"the NYC Independent Budget Office ([Data Center](https://www.ibo.nyc.gov/content/data-center)) for the citywide and agency-level fiscal picture our who-got-what data sits inside."* (The blog draft is explicitly off-limits for editing; this is a recommendation for Noel.)
3. **Skip:** a DATA-DICTIONARY.md note. The dictionary is a column reference; an ecosystem map there would be off-purpose. The README section covers it.

### Ready-to-paste README section

```markdown
## How this relates to other NYC budget data sources

This repository is one piece of a larger NYC budget-data ecosystem. It is
deliberately narrow: **designation-level, who-got-what data from the Council's
adopted budget** — the organization, the sponsoring Council member, the amount,
the implementing agency, and the recipient's EIN. It is not a source of citywide
fiscal totals, revenue, or long-run spending trends. Here is where the neighbors fit.

| Source | What it's best for | Overlap with this repo |
|---|---|---|
| **This repo** | Council discretionary (Schedule C) awards, Terms & Conditions, §254 capital changes, Transparency Resolutions, and a Legistar crosswalk — at the organization/EIN level | — |
| **[NYC Independent Budget Office — Data Center](https://www.ibo.nyc.gov/content/data-center)** | The aggregate fiscal picture: citywide and agency-level expenditures and revenue (FY1980+), capital expenditures (since 1985), debt, headcount, education spending, and tax data. Also IBO's fiscal analyses and budget-option reports. | **None at the award level.** IBO has no discretionary/Schedule C/member-item data. It is the fiscal *context* this repo's who-got-what data sits inside. Most of the Data Center is also published on NYC Open Data under agency "NYC Independent Budget Office (IBO)." |
| **[NYC Open Data — City Council Discretionary Funding](https://data.cityofnewyork.us/dataset/4d7f-74pe) (`4d7f-74pe`)** | Award-level Council discretionary funding, FY2009–FY2021, Council-published | **Directly overlaps FY2015–FY2021.** It stopped updating in April 2021, so this repo is the machine-readable source for **FY2022–FY2027** and adds source-reconciled totals plus Terms, Capital, Transparency, and Legistar provenance. |
| **[NYC Checkbook](https://www.checkbooknyc.com) (Comptroller)** | Actual spending and registered contracts | Complements this repo: join on EIN to ask whether a designation became a paid contract. |
| **[NYC Council Finance Division](https://council.nyc.gov/budget/) / OMB** | The primary source documents (adopted budget PDFs) this repo parses | This repo is the structured, reconciled extraction of those documents. |

In short: **IBO tells you what the City spends, raises, and owes in aggregate over
decades; this repo tells you which organizations the Council funded, and how much,
in the adopted budget.** Neither IBO nor NYC Open Data (after FY2021) publishes the
second thing as machine-readable data. That is the gap this repository fills.
```

---

## Sources checked

- IBO Data Center — <https://www.ibo.nyc.gov/content/data-center> (all 8 panels rendered live)
- IBO site search for "Schedule C / discretionary / member items" — returned analytical PDFs only, no data product
- NYC Open Data catalog, agency = "NYC Independent Budget Office (IBO)" — <https://data.cityofnewyork.us/browse?Dataset-Information_Agency=NYC+Independent+Budget+Office+(IBO)> (20 datasets)
- Individual IBO datasets: `7zhs-43jt`, `fu34-wamz`, `5i9t-mvdt`, `6ggx-itps`
- NYC Open Data "City Council Discretionary Funding" `4d7f-74pe` (per repo's own FY09–FY21 scoping doc)
- NYC Charter §259 / Chapter 11 (IBO establishing authority); Admin. Code §23-501 ("agency" definition) — legal status flagged, not resolved
- Repo docs: `README.md`, `DATA-DICTIONARY.md`, `DATA-ANOMALIES.md`, `research/2026-07-07-fy09-fy21-legacy-import-scoping.md`

## Honest limits

- Data Center content was read via browser text extraction; I did not open each Excel file, so per-file column detail and exact latest-year coverage are as-labeled, not as-opened.
- "20 datasets" is the count under the exact agency facet "NYC Independent Budget Office (IBO)"; IBO data cross-published under another agency label would not appear in that count.
- The IBO/Open Data Law legal question is flagged for counsel, not decided here.
- I did not query any live API (no NYC Open Data / Socrata API calls); portal facts come from the public catalog web UI.

---

## IBO fiscal-history tables ↔ Schedule C / §254 capital — authoritative intersection (2026-07-08)

**Added:** 2026-07-08. This section supersedes §153's "did not open each Excel file" limit — all seven `data-fiscal-history` Excel files were downloaded and opened with openpyxl, and the NYC Open Data catalog was queried live via the Socrata MCP (operator-authorized for this IBO task). Everything below is from the files and the portal as observed, not as-labeled.

### A. Per-file inventory (opened, not inferred)

All seven files share one shape: a **wide "matrix" layout** — category/agency rows down the first column(s), **fiscal years across the columns (2024 → 1980, newest first)**, a 2–3 row title block above a single header row, and blank spacer rows between blocks. Fiscal years are labeled by **ending calendar year** (`2024` = FY2024). All dollar figures are **nominal** (no inflation adjustment anywhere); several workbooks ship the same data twice — once in whole dollars, once in `$000s`. Source for all seven is the Comptroller's **Comprehensive/Annual Financial Report (CAFR/ACFR)** — i.e. **audited actuals**, except positions (OMB, as of June 30).

| File | Sheets | Grain | FY coverage (Excel) | Units | Portal equivalent + ID | Portal coverage / frozen |
|---|---|---|---|---|---|---|
| `agency-expenditures.xlsx` | `DETAIL`, `In $000's` | **agency × expense line × FY** (line items: Personal Services / OTPS / less: intra-city / prior-year adj / **TOTAL DEPT.**); 104 agency blocks | **FY1980–FY2024** | nominal $ and $000s | Agency Expenditures FY1980–2018 — `cwjy-rrh3` | **to FY2018**, frozen 2019-07-12 |
| `capital-expenditures.xlsx` | `Sheet1`, `Totals in $thousands` | **functional area → agency → purpose × FY** (two label columns A/B) | **FY1985–FY2024** | nominal $ and $000s | Capital Expenditures Since 1985 — `hukm-snmq` | **to FY2020**, frozen 2021-07-12 |
| `actual-full-time-positions.xlsx` | `ALL FUNDS` | **agency × FY** (headcount) | **FY1980–FY2024** | full-time positions (count, as of 6/30; OMB) | Full Time Positions… — `uaj7-9szf` | to ~FY2020, frozen 2021-06-18 |
| `all-revenue.xlsx` | `$ in Thousands`, `Calculations`, `All Revenue` | **revenue category × FY**, citywide | **FY1980–FY2024** | nominal $ and $000s | Revenue And Spending Summary FY1980–FY2020 — `7zhs-43jt` | **to FY2020**, frozen 2021-06-25 |
| `tax-revenue.xlsx` | `Taxes` | **tax type × FY**, citywide | **FY1980–FY2024** | nominal $ | Tax Revenue FY1980–FY2020 — `hdnu-nbrh` | **to FY2020**, frozen 2021-06-28 |
| `other-nontax-revenues.xlsx` | `City Non-Tax` | **non-tax revenue type × FY**, citywide | **FY1980–FY2024** | nominal $ | Non-Tax Revenues FY1980–FY2020 — `ypbd-r4kg` | **to FY2020**, frozen 2021-06-25 |
| `grants-aid.xlsx` | `Non City` | **aid category × FY**, citywide (State/Federal/Other **categorical aid the City receives**) | **FY1980–FY2024** | nominal $ | State And Federal Categorical Aid FY1980–2020 — `fu34-wamz` | **to FY2020**, frozen 2021-06-24 |

**Portal-vs-Excel verdict (Task 1):** for these seven series the **Excel files are the authoritative, most-current copy.** Every portal mirror was frozen in 2019–2021 and caps at **FY2018 (agency-expenditures) or FY2020 (the other six)**; the Excel files run through **FY2024** — four to six additional audited years. Same underlying series, same CAFR source; the portal copy simply stopped being refreshed. If you need the current numbers, use the Excel. (The portal copies remain useful only for their stable dataset IDs and API access to the FY≤2020 slice.)

### B. Join-key analysis (Task 2) — per table

The only structural key any of our repo data shares with any of these tables is **agency × fiscal year**, and only two of the seven tables carry an agency dimension in a form our data can reach.

**1. `agency-expenditures` — the one defensible join.**
- **Key:** `(agency, fiscal_year)`. Aggregate our Schedule C **awards** up from org-level to `agency × FY` (`SUM(amount) GROUP BY agency, year`), take IBO's **`TOTAL DEPT.`** row per agency-year.
- **Taxonomy:** matches, **but only through a hand-built crosswalk.** Our `agency` field is abbreviations (DYCD, DCLA, DFTA, DSS/HRA, DHMH, DPR, SBS, HPD, DSNY, CUNY, DOE, NYPD, DHS, FDNY, ACS, QBPL, HHC, DOT, MOCJ, …); IBO uses full names ("Dept. of Youth and Community Development", "Department for the Aging", "Department of Cultural Affairs", …). Every populated abbreviation in our awards has a counterpart line in IBO's 104-agency list, so a ~30-row abbrev→IBO-name map closes it. Borough/DA/community-board codes (SIBP, DAQN, BKCB, …) map to IBO's "Borough President – X" / "District Attorney – X" / "Community Boards" lines.
- **Year overlap:** our awards are FY2015–FY2027; IBO actuals run to FY2024 → **joinable window FY2015–FY2024** (FY2025–FY2027 have no IBO actual yet).
- **Coverage caveat:** the single largest `agency` bucket in `all_years_awards.csv` is **blank (~14.6k rows)** — awards with no implementing agency tagged. The join only reaches rows where `agency` is populated, so a large share of designations fall outside it.

**2. `capital-expenditures` — technically joinable, not authoritative.**
- **Key:** same `(agency, FY)` idea — aggregate our §254 capital rows to agency×FY, join IBO's per-agency capital total.
- **Three problems make it illustrative at best:** (a) our capital `agency` labels are an older, functional taxonomy (EDUCATION, PARKS, HIGHWAYS, PUBLIC BUILDINGS, HOUSING AUTHORITY, …) that maps only loosely and lossily onto IBO's functional-group→agency structure (Environmental Protection & Sanitation, Transportation Services, …); (b) a **parser artifact pollutes the field** — 52 rows carry a leaked data string as the agency value (`"PV MA1002 … NOEL POINTER FOUNDATION"`), which must be cleaned before any grouping; (c) the measure gap is wider than for expense (see below). Overlap window is thin: our capital is FY2020, FY2022–FY2027; IBO actuals to FY2024 → FY2020, FY2022–FY2024.

**3–6. `all-revenue`, `tax-revenue`, `other-nontax-revenues`, `grants-aid` — no join.**
- All four are **citywide, by revenue/tax/aid *category*, with no agency, organization, or EIN dimension.** Our repo has no revenue data and nothing at citywide-category grain. There is **no key** and **no shared universe** — do not attempt a join.
- **False-friend flag:** `grants-aid` is **intergovernmental categorical aid the City *receives* from State/Federal**, not grants the Council *gives out*. The name invites a wrong linkage to discretionary "grants." It is unrelated to Schedule C in both direction and universe.

**7. `actual-full-time-positions` — no meaningful join.**
- It shares the `agency × FY` key with #1, so a join is *mechanically* possible, but pairing "discretionary dollars designated" against "agency headcount" has no analytic meaning. Treat as **no join**.

### C. The adopted-vs-actual caveat (stated once, load-bearing)

Our repo measures **intent**; IBO measures **outcome**. Schedule C = *adopted discretionary designations* (a slice of the **expense budget**, as adopted). §254 = *adopted changes to the capital budget*. IBO agency-expenditures and capital-expenditures = **actual, audited expenditures from the CAFR**. So even where the `(agency, FY)` key lines up perfectly, the two sides are **different measures of the same agency-year** — a small designated-intent slice against a full audited-actual total. A join tells you *"Council discretionary designations to Agency X in FY Y sat inside Agency X's total actual spending of $Z"* — a **share-of / sits-inside** relationship. It is **never an identity**; the numbers should not, and will not, equal each other. For capital the gap is larger still: an *adopted delta* to a multi-year capital plan vs. *actual cash capital outlays*.

### D. Bottom line — where a defensible intersection exists

| IBO table | Can our data intersect it? | How |
|---|---|---|
| **agency-expenditures** | **Yes — the one authoritative join.** | Schedule C awards → aggregate to `agency × FY`, crosswalk abbreviations → IBO names, FY2015–FY2024. Framed strictly as discretionary designations **as a share of** the agency's actual expense total (intent-slice ⊂ actual-total). |
| **capital-expenditures** | **Weak / illustrative only.** | §254 → `agency × FY`, but lossy taxonomy crosswalk + a parser artifact to clean + adopted-delta-vs-actual gap. Not authoritative. |
| all-revenue / tax-revenue / other-nontax-revenues / grants-aid | **No.** | Citywide revenue/aid categories; no agency/EIN; different universe. `grants-aid` is aid *received*, not grants *given*. |
| actual-full-time-positions | **No meaningful join.** | Shares the key but headcount × discretionary-$ has no analytic meaning. |

**One-sentence verdict:** exactly **one** of the seven IBO tables supports a defensible intersection with this repo — **agency-expenditures**, on `agency × fiscal year` (FY2015–FY2024, via an abbreviation crosswalk), and only as a "discretionary designations sit inside the agency's actual expenditure total" framing; **capital-expenditures** is a distant, illustrative-only second; the remaining five have no meaningful join.

### E. Honest limits (this section)

- Agency-name matching was verified by extracting IBO's full 104-agency expenditure list and our repo's distinct `agency` values and reconciling them by eye; I did **not** build or test the actual crosswalk CSV — that is an implementation step, and a handful of edge codes (e.g. `MOCJ`→"Office of Criminal Justice") should be confirmed against a Council roster/agency table before production use.
- Portal coverage end-years are read from dataset titles and `data_updated_at`; I did not row-count each portal copy to confirm the last populated FY.
- The capital parser artifact (52 rows) is noted here as a join blocker, not fixed; it belongs in `DATA-ANOMALIES.md` for the software-engineer/data owner to address.
