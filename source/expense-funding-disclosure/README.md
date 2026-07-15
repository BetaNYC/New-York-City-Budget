# Council Expense Funding Disclosure spreadsheets

Machine-readable, **award-level** discretionary **expense** funding disclosure spreadsheets
published by the New York City Council's Research & Data (RnD) division, for **Fiscal Years
2013–2027**, plus the RnD site's capital workbook.

These are the Council's own structured disclosure files — the same data the Council presents at
<https://rnd.council.nyc.gov/expense_funding/>. Unlike the adopted-budget **Schedule C PDFs** in the
per-fiscal-year `source/FY**/` folders (which are parsed by this repo's PDF pipeline), these files
are already tabular, so they need no text extraction. They are included here as source records and
as the basis for an award-level expense dataset that is richer than what the PDFs yield.

## Provenance

- **Source:** NYC Council Research & Data division, <https://rnd.council.nyc.gov/expense_funding/>.
  The site is a client-side app that loads these static files directly; there is no server API.
- **Expense file URLs:** `https://rnd.council.nyc.gov/src/assets/excelFund/funded_disclosure_FY{YYYY}.{ext}`
  (`ext` = `xls` for FY2013, `xlsx` for FY2014+).
- **Capital file URL:** `https://rnd.council.nyc.gov/src/assets/Capital-Database.xlsx`.
- **Retrieved:** 2026-07-15.
- **Rights:** © The City of New York. These are official NYC Council disclosure publications,
  reproduced here as public records for transparency and analysis. All rights to the documents
  remain with the City of New York. (Same terms as the PDFs under `source/`.)

## Files & manifest (as retrieved 2026-07-15)

| File | Sheet | Rows (incl. header) | Cols |
|---|---|---|---|
| `funded_disclosure_FY2013.xls` | (legacy `.xls`) | — | — |
| `funded_disclosure_FY2014.xlsx` | FY14 | 6,612 | 16 |
| `funded_disclosure_FY2015.xlsx` | FY15 | 6,651 | 17 |
| `funded_disclosure_FY2016.xlsx` | FY16 | 7,798 | 16 |
| `funded_disclosure_FY2017.xlsx` | FY17 | 8,675 | 17 |
| `funded_disclosure_FY2018.xlsx` | FY18 | 8,895 | 17 |
| `funded_disclosure_FY2019.xlsx` | FY19 (4-14-21) | 9,656 | 17 |
| `funded_disclosure_FY2020.xlsx` | FY20 (06-16-2022) | 10,617 | 17 |
| `funded_disclosure_FY2021.xlsx` | FY21 (06-23-2023) | 9,055 | 17 |
| `funded_disclosure_FY2022.xlsx` | FY22 (07-11-2023) | 11,337 | 17 |
| `funded_disclosure_FY2023.xlsx` | FY23 (07-11-2023) | 11,028 | 17 |
| `funded_disclosure_FY2024.xlsx` | FY24 (06-08-26) | 10,829 | 18 |
| `funded_disclosure_FY2025.xlsx` | FY25 (06-08-26) | 11,281 | 18 |
| `funded_disclosure_FY2026.xlsx` | FY26 (06-08-26) | 11,766 | 18 |
| `funded_disclosure_FY2027.xlsx` | FY27 (07-01-26) | 10,041 | 18 |
| `Capital-Database.xlsx` | FY26 | 1,253 | 11 |

Sheet names embed the Council's own "last updated" date (e.g. `FY25 (06-08-26)`), a useful
refresh-cadence signal.

## Schema

**Expense, FY2024+ (18 columns):**
`MOCS ID#, Fiscal Year, Source, Council Member, Legal Name, Tax ID, Status, Amount, Agency,
Program Name, Grantee Street Address, Grantee Street Address (2), City, State, Zip, …`

- **`MOCS ID#`** (e.g. `FY25 00001`) — Mayor's Office of Contract Services identifier; a stable
  per-award key and the join to registered contracts / Checkbook spending. **Present FY2024+ only.**
- **`Tax ID`** — grantee EIN; the reliable join to IRS 990 / nonprofit data.
- **`Status`** — `Cleared` or `Pending` (clearance state of the designation).
- **`Source`** — funding stream: `Local`, `Youth`, `Aging`, `Speaker's Initiative`, or one of
  ~180 named citywide initiatives.
- **Grantee mailing address** — enables geocoding to council district / neighborhood.

**Expense, FY2015–FY2023 (17 columns):** as above minus `MOCS ID#`; earlier files use
`Council Members` / `Legal Name of Organization` / `EIN` header wording.

**Expense, FY2014 (16 columns)** and **FY2013 (`.xls`)** are the earliest; verify columns
empirically before relying on them.

**Capital (11 columns):** `PROJECT, BORO, BUDLINE, CD, SPONSOR, TITLE, DESC, FY26, FY27, FY28, FY29`.
The RnD capital workbook held only an FY26 sheet when retrieved (despite an on-site download button
labeled "FY 2025 Capital Discretionary Funding"); it is **not** the clean per-year series that the
expense files provide.

## Data-quality notes

1. **FY2026 carries embedded summary/footer rows** mixed into the data — rows whose `Status`
   column reads `Schedule C Total:`, `Updated Total:`, `Difference:`, or `Master List Total:`.
   These must be stripped before summing (a naive total is inflated). Check every year.
2. **`Status` (Cleared vs Pending) must be handled deliberately.** The upcoming budget year is
   heavily Pending at publication (FY2027 was ~50% Pending as retrieved).
3. **Organization names have minor inconsistencies** (leading spaces, quoting). `Tax ID` (EIN) and
   `MOCS ID#` are the reliable keys.

## Relationship to this repo's Schedule C data

The parsed Schedule C data under `data/{year}/schedule_c/` is extracted from the adopted-budget
**PDFs** and is reconciled to the documents' printed category `TOTAL` lines. These disclosure files
are a **separate, award-level** source that reaches back two years further (FY2013–FY2014) and adds
fields the PDFs do not expose cleanly (MOCS ID, grantee address, clearance status). An evaluation of
which source is authoritative for which use case is tracked in the BetaNYC workspace.
