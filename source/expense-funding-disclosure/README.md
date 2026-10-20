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
- **Retrieved:** first 2026-07-15. **Re-pulled 2026-10-12** (all 16 files, with Noel's OK):
  FY2013–FY2024 came back byte-identical; FY2025, FY2026, FY2027 and `Capital-Database.xlsx`
  had changed and were replaced. What moved is in
  [`data/disclosure-snapshots/2026-10-12/`](../../data/disclosure-snapshots/2026-10-12/).
- **Rights:** © The City of New York. These are official NYC Council disclosure publications,
  reproduced here as public records for transparency and analysis. All rights to the documents
  remain with the City of New York. (Same terms as the PDFs under `source/`.)

## Files & manifest (as retrieved 2026-10-12)

**[`MANIFEST.csv`](MANIFEST.csv)** is the machine-readable baseline: per file its SHA-256, byte
size, retrieval date, sheet name, sheet rows, and (for the expense files) award rows, stripped
footer rows and total. `retrieved` is the date of the most recent download that produced exactly
these bytes, including a re-pull that found the file unchanged. It is written by
`code/parse_expense_disclosure.py --manifest`, and `code/test_parse_expense_disclosure.py` fails
if any file here stops matching its hash. A later re-pull is compared against it.

**[`MANIFEST-HISTORY.csv`](MANIFEST-HISTORY.csv)** is append-only: every manifest row a later
`--manifest` run replaced, with a `superseded_on` column (the replacing row's `retrieved` date,
or `removed`). The 2026-07-15 hashes of all 16 files are there, including the four workbooks
overwritten on 2026-10-12, so an old hash stays traceable after its file is gone. The workbooks
themselves stay in git history.

| File | Sheet | Rows (incl. header) | Cols |
|---|---|---|---|
| `funded_disclosure_FY2013.xls` | MASTER (legacy `.xls`; Sheet2/Sheet3 are empty) | 4,988 | 16 |
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
| `funded_disclosure_FY2025.xlsx` | FY25 (09-14-26) | 11,277 | 18 |
| `funded_disclosure_FY2026.xlsx` | FY26 (09-14-26) | 11,765 | 18 |
| `funded_disclosure_FY2027.xlsx` | FY27 (09-14-26) | 10,408 | 18 |
| `Capital-Database.xlsx` | FY27 CAPITAL | 1,214 | 9 |

Sheet names embed the Council's own "last updated" date (e.g. `FY25 (06-08-26)`), a useful
refresh-cadence signal.

## Schema

**Expense, FY2024+ (18 columns):**
`MOCS ID#, Fiscal Year, Source, Council Member, Legal Name, Tax ID, Status, Amount, Agency,
Program Name, Grantee Street Address, Grantee Street Address (2), City, State, Zip, …`

- **`MOCS ID#`** (e.g. `FY25 00001`) — Mayor's Office of Contract Services identifier, one per
  row. **Present FY2024+ only.** Not stable across snapshots (131 FY2026 IDs re-prefixed
  `FY26GP`, FY2027 re-issues, an ID whose EIN changed; IDs ascend with sheet order), and its
  join to registered contracts / Checkbook is **unverified** (see `DATA-ANOMALIES.md` §22).
- **`Tax ID`** — grantee EIN; the reliable join to IRS 990 / nonprofit data.
- **`Status`** — `Cleared` or `Pending` (clearance state of the designation).
- **`Source`** — funding stream: `Local`, `Youth`, `Aging`, `Speaker's Initiative`, or one of
  ~180 named citywide initiatives.
- **Grantee mailing address** — enables geocoding to council district / neighborhood.

**Expense, FY2015–FY2023 (17 columns):** as above minus `MOCS ID#`; earlier files use
`Council Members` / `Legal Name of Organization` / `EIN` header wording.

**Expense, FY2014 (16 columns)** and **FY2013 (`.xls`, 16 columns)** are the earliest. FY2013,
verified 2026-10-12: `Source, Council Member, Legal Name of Organization, EIN, Status, Amount ($,
Agency, Program Name, Street Address 1, Address 2, City, State, Zip Code, Purpose of Funds, Fiscal
Conduit Name, FC EIN`. It stores EINs and ZIPs partly as numbers and partly as text, and prints
175 EINs with a hyphen.

**Capital (9 columns, 2026-10-12):** `PROJECT ID, BORO, BUDGET LINE, CD, SPONSOR, TITLE, PROJECT
DESCRIPTION, FY27, FY28`, one sheet, `FY27 CAPITAL`. The RnD site serves one capital workbook at one
URL and replaces it: the 2026-07-15 copy held only an FY26 sheet (11 columns: `PROJECT, BORO,
BUDLINE, CD, SPONSOR, TITLE, DESC, FY26, FY27, FY28, FY29`; 1,253 rows incl. header), despite an
on-site download button labeled "FY 2025 Capital Discretionary Funding". That FY26 copy is now only
in this repo's git history (and its hash in `MANIFEST-HISTORY.csv`). It is **not** the clean
per-year series that the expense files provide, and **no code in this repo reads it**; it is kept
as a source record only.

## Data-quality notes

1. **The 2026-07-15 FY2026 workbook carried embedded summary/footer rows** mixed into the data —
   rows whose `Status` column reads `Schedule C Total:`, `Updated Total:`, `Difference:`, or
   `Master List Total:`. These must be stripped before summing (a naive total is inflated). The
   2026-10-12 FY2026 workbook has none. **Checked every year (2026-10-12):** FY2024 has them too — four with a blank `Status` and their labels
   (`New Total`, `Adoption Total`, `Admin New Add`, `Difference`) in the address column, plus one
   unlabeled typed value, `454,755`, in the Amount column of row 10829, whose meaning the file
   does not state. Every stripped row is listed in
   `data/fy24/expense_disclosure/fy24_expense_reconciliation.txt` and its FY2026 counterpart.
2. **`Status` (Cleared vs Pending) must be handled deliberately.** The upcoming budget year is
   heavily Pending at publication. FY2027 on 2026-07-15: about 50% of rows and about 80% of
   dollars Pending ($143,034,722 Cleared of $705,564,000). On 2026-10-12: about 16% of dollars
   Pending ($590,253,954 Cleared of $705,704,000).
3. **Organization names have minor inconsistencies** (leading spaces, quoting). `Tax ID` (EIN) is
   the reliable key within a year (it pools fiscal-sponsor programs, and the City's own EIN
   `136400434` covers hundreds of City bodies). `MOCS ID#` identifies a row within one snapshot
   only; see above.

## Re-pulling a snapshot (and diffing it against the one committed here)

The Council republishes these workbooks: the sheet name carries its "last updated" date, and
Pending rows clear over time. A re-pull is how that movement becomes visible. **Every download
needs Noel's explicit OK, each time** — this repo makes no automated or scheduled calls to the
Council site, and neither should anyone working in it.

1. **Get the OK first.** Name the years and the URLs (above) you intend to fetch.
2. **Download into a new, empty folder outside the repo**, one per pull, named for the date
   (e.g. `~/Downloads/council-disclosure-YYYY-MM-DD/`). Treat the files as untrusted input until
   checked: run any Python that reads them with `python3 -I`, scripts from the repo, paths as
   arguments.
3. **Hash before anything else.** Compare `shasum -a 256 <file>` with the `sha256` column of
   [`MANIFEST.csv`](MANIFEST.csv). Identical hash: nothing changed, stop there for that file.
4. **Diff each changed year against the committed snapshot**:
   ```bash
   python3 -I code/diff_disclosure_snapshots.py \
       source/expense-funding-disclosure/funded_disclosure_FY2027.xlsx \
       ~/Downloads/council-disclosure-YYYY-MM-DD/funded_disclosure_FY2027.xlsx \
       --out ~/Downloads/council-disclosure-YYYY-MM-DD/FY2027-diff.md
   ```
   The report gives status transitions (pending → cleared and back), amount changes, added and
   removed rows, and totals by status, old vs new. FY2024+ rows pair by MOCS ID; earlier years
   pair on a composite key, where an amount change can only appear as a removal plus an addition
   (listed as a *candidate*, never counted). Ambiguous pairings are counted, not resolved.
   Read it before replacing anything: a removal or an amount change is a finding to report, not
   noise to overwrite.
5. **Then update the repo, on a branch:** copy the new file over the old one in this folder,
   record it with `python3 code/parse_expense_disclosure.py --write --manifest --retrieved
   YYYY-MM-DD --verified YYYY-MM-DD` (`--retrieved`: the download date of changed files, which
   the script refuses to guess; `--verified`: the same date, for the files that came back
   byte-identical — omit it if you did not re-download those). Superseded manifest rows go to
   `MANIFEST-HISTORY.csv` automatically. Rerun `python3 code/reconcile_disclosure_schedule_c.py`
   and the tests, commit the diff reports under `data/disclosure-snapshots/YYYY-MM-DD/`, and put
   their headline numbers in the PR description. Update the retrieval date and table above.
   **Do not re-run the Schedule C repair scripts** (`fix_*.py`, `recover_*.py`,
   `fill_blank_initiatives.py`, `build_appendix_from_disclosure.py`) against the new snapshot as
   part of a re-pull: they repaired the adopted-budget data against the 2026-07-15 snapshot, and
   re-running them would mix vintages (see `code/audit_amounts.py`). That is its own decision.

The git history of this folder plus `MANIFEST.csv` is the record of what each snapshot was.

## Relationship to this repo's Schedule C data

The parsed Schedule C data under `data/{year}/schedule_c/` is extracted from the adopted-budget
**PDFs** and is reconciled to the documents' printed category `TOTAL` lines. These disclosure files
are a **separate, award-level** source that reaches back two years further (FY2013–FY2014) and adds
fields the PDFs do not expose cleanly (MOCS ID, grantee address, clearance status). An evaluation of
which source is authoritative for which use case is tracked in the BetaNYC workspace.
