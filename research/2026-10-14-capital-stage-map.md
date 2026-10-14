---
title: "Capital stage map: Council designation to payment (#87), and the RnD file list (#88)"
created: 2026-10-14
type: research-note
status: draft
tags: [nyc-budget, capital, open-data, checkbook, council, research]
issue: "BetaNYC/New-York-City-Budget#87, #88 (epic #89)"
---

# Capital stage map: Council designation to payment (#87), and the RnD file list (#88)

**Report generated:** 2026-10-14
**Data current as of:** 2026-10-14 (Open Data queried this morning; RnD site read at 10:58 UTC;
Council workbook as pulled 2026-10-12, July copy from commit `98f1086`)
**Author:** research-intelligence, for epic #89
**Companion notes:** [Open Data inventory (#84)](2026-10-14-structured-data-inventory.md),
[follow-up questions](2026-10-14-follow-up-questions-84-87-88.md)
**Evidence:** [`2026-10-14-capital-stage-map/`](2026-10-14-capital-stage-map/) holds the
reconciliation script, the OMB extract it reads (161 rows), and its output.

## Summary

- **Stages 1 to 3 link cleanly, by budget line.** The Council's own budget lines (the `D` and
  `DN` series) carry only Council designations. For FY2027, **146 of 153 Council budget lines
  match OMB's adopted Capital Budget to the dollar** in both FY2027 and FY2028 ($669.8M of the
  Council's $853.7M). The commitment plan carries the same lines, in thousands, release by
  release.
- **Below the budget line there is no shared key.** The Council's project IDs (`CN0003`,
  `NC0415`, `CC0001`) appear in no OMB, DCP or OPS dataset. The FMS project ID (`850AGMBDXVAN`)
  is assigned later by the agency. The link from a Council row to an FMS project is a **text
  match** inside one budget line. It works well on single-grantee `DN` lines and poorly on
  shared lines such as `E D001` (708 school projects in FY2027).
- **Stages 4 and 5 are visible only in aggregate, through DCP's CPDB.** It reports committed and
  spent dollars per FMS project, plus a "spent according to Checkbook" sum. No Open Data capital
  dataset carries a contract ID.
- **Checkbook was not tested.** The first and only call returned an error (`Empty response`). Per
  the access rules, I stopped all Checkbook calls.
- **#88: the RnD site serves 16 data files and nothing else**: the 15 expense workbooks
  FY2013–FY2027 and `Capital-Database.xlsx`. No archive of earlier capital years.

## 1. The Council file itself (stage 1)

Read with openpyxl, `python -I`:

| | July 2026 pull (commit `98f1086`) | October 2026 pull (current file) |
|---|---|---|
| Sheet | `FY26` | `FY27 CAPITAL` |
| Rows | 1,252 data rows + header | 1,213 data rows + header |
| Columns | `PROJECT, BORO, BUDLINE, CD, SPONSOR, TITLE, DESC, FY26, FY27, FY28, FY29` | `PROJECT ID, BORO, BUDGET LINE, CD, SPONSOR, TITLE, PROJECT DESCRIPTION, FY27, FY28` |
| First-year total | FY26 $779,320,000 | FY27 $853,688,000 |
| Out-year totals | FY27 $22.3M, FY28 $3M, FY29 $3M | FY28 $44M (6 rows) |
| Project ID form | Agency prefix + `CN`/`NC` + 4 digits (`E CN0001`, `AG NC0415`) | `CC` + 4 digits, no agency prefix (`CC0001`) |
| Budget lines | 160 distinct | 153 distinct |
| Oddities | One duplicate ID (`HN CN1451`, two sponsors, two amounts); 14 descriptions cite another project ID (e.g. "(E CN0967)") | One row with `BORO = A`, `CD = 99`, sponsor "Technical Adjustments"; 5 rows at CD 99; 1 row at CD 80, sponsor "Admin" |

Things to know before building on it:

- **Project IDs are unique within a year only, and the format changes every year or two.**
  `t474-a92g` uses three digits with a doubled space for FY2019–FY2025 (`E  CN459`), the July
  workbook uses four digits (`E CN0001`), and the October workbook drops the agency prefix
  (`CC0001`). The repo's PDF parse of FY2027 shows the printed form keeps the prefix
  (`AG CC1053`), so the workbook strips it.
- **`CD` is a list**, e.g. `00,24,94`. `00` is the Speaker. The RnD site's own filter list is
  `00` to `51` plus `91, 92, 93, 94, 95, 97, 99` (from its JS bundle). It does not include `80`.
- **`CN` and `NC` (FY2026):** all but one `DN`-line row is `NC`, and `NC` also appears on 99
  shared-line rows. My reading is that `NC` marks a non-city (non-profit) grantee, matching the
  PDF's Part II. That is an inference, not confirmed.

## 2. The stages and their keys

| Stage | Structured source | Grain | Years on hand | Key in | Key out to the next stage | Link status |
|---|---|---|---|---|---|---|
| 1. Council designation | RnD `Capital-Database.xlsx` (current year only); Open Data `t474-a92g` (FY2019–FY2026) | One Council award; out-years as columns (RnD) or rows (Open Data) | FY2019–FY2027 (FY2019–FY2026 on Open Data, FY2027 RnD only) | Council project ID (year-unique) | **Budget line** (`PV DN132`) | Tested |
| 2. Adopted capital budget | OMB `46m8-77gv` | Release × budget line × funding source, dollars | FY2019–FY2027 adopted (releases 2018–2026) | Budget line, with a space; pick the July `pub_date` | Budget line | **Works.** 146/153 lines exact for FY2027 |
| 3a. Commitment plan, line level | OMB `2cmn-uidm` | Release × budget line × City/Non-City, **thousands** | Releases April 2016 → 2026-09-28 | Budget line, no space (`PVDN132`) | Budget line | **Works** for single-grantee lines, to rounding |
| 3b. Commitment plan, project level | DCP CPDB `djxg-kcfi` (commitments) | Planned commitment of one FMS project | One snapshot, `fisa_2026` | Budget line, hyphen (`PV-DN132`) | **FMS project ID** (`maprojid`) | **Text match only.** No Council ID on the OMB/DCP side |
| 4. Contract | No Open Data source with a contract ID. CPDB `fi59-268w` gives `commit_total` per FMS project. OPS dashboard `fb86-vt7u` gives phase and schedule per FMS ID | FMS project | `fisa_2026`; dashboard 2023-05 → 2026-05 | FMS project ID | Contract ID: **not available** in these sources | **Partial.** A dollar amount committed, not which contract |
| 5. Payment | CPDB `fi59-268w` `spent_total` and `spent_total_checkbooknyc`; Checkbook NYC itself (untested) | FMS project, lifetime | `fisa_2026` | FMS project ID | n/a | **Partial.** Totals per project, no checks, no dates |

Normalizing the budget line is the whole join: collapse whitespace and hyphens
(`P  D018` = `P D018` = `P-D018` = `PD018`). The dashboard's list form (`P -D018 , P -I001`)
needs splitting first.

## 3. Tests with real projects

Each row below was checked against live Open Data on 2026-10-14. Amounts are dollars unless
marked $K.

| Council row | Stage 2: adopted (`46m8-77gv`) | Stage 3a: commitment plan (`2cmn-uidm`) | Stage 3b–5: CPDB / dashboard | Verdict |
|---|---|---|---|---|
| **FY26 `AG NC0415`**, MBD Community Housing Corp. vans, `AG DN04L`, $121,000 (Salamanca) | July 2025 release: `AG DN04L` FY2026 $121,000 | Sept 2025: FY2026 121 $K. Feb and May 2026: moved to FY2027. Sept 2026: FY2027 121 $K | `850AGMBDXVAN`, "MBD COMMUNITY HOUSING CORPORATION VANS FOR SENIOR ACTIVITIES" (the Council's title, word for word), adopted $121,000, planned June 2027, committed $0, spent $0 | **Full chain to stage 3b.** Shows a one-year slip. Not yet contracted or paid |
| **FY27 `CC0701`**, RiseBoro farmers' market truck, `ED DN05T`, $92,000 (Nurse) | July 2026 release: `ED DN05T` FY2027 $92,000 (title "RISEBORO COMMUNITY PARTNERSHIP …") | Sept 2026: FY2027 92 $K | Not in CPDB yet. CPDB shows two older RiseBoro projects on the same line (vehicles $295,000, $273,098 committed; youth center $1,159,000) | **Stages 1–3a work.** Stage 3b waits for a new CPDB version |
| **FY27 `CC0166` + `CC1251`**, Ryan Health outfitting, `HL DN164`, $838,000 (Abreu) + $371,000 ("Admin", CD 80) | `HL DN164` FY2027 $1,209,000 = the two rows | Sept 2026: FY2027 1,209 $K | Not in CPDB yet (an older $3.42M acquisition project is) | **Stages 1–3a work**, and show an "Admin" row is real money on a Council line |
| **FY27 `CC0010` + `CC0908`**, DCTV ground floor, `PV DN132`, $250,000 (Marte) + $800,000 (Speaker, Marte) | `PV DN132` FY2027 $1,050,000 = the two rows | Sept 2026: FY2027 0, FY2030 1,568 $K. May 2026 showed FY2030 518 $K, and 518 + 1,050 = 1,568 | Not in CPDB yet. Older DCTV projects on this line: renovation `850PV132DCTV`, spent $1,645,593, Checkbook-derived $1,604,593 | **Stages 1–3a work.** The commitment plan pushed the new money to FY2030. That reading comes from the arithmetic, not from a stated reason |
| **FY26 `P CN0003`**, Duane Park upgrades, `P D018` (shared Manhattan parks line), $300,000 (Marte) | Line total only ($28.2M in FY2026); cannot isolate one project | Line total only | OPS dashboard, May 2026: `fms_id P-301DUAN`, "Duane Park Upgrades - Upgrades At Duane Park" (the Council's TITLE and DESC joined), total budget $300,000, Pre-Design, budget lines `P -D018 , P -I001` | **Works by text match** on a shared line, through the dashboard rather than CPDB |
| **FY27 `CC0001`**, Gouverneur Hospital dishwasher, `HO D003`, $350,000 | `HO D003` FY2027 $50,878,000 and FY2028 $15,000,000 = the sum of the Council's 27 rows on that line, both years | Not queried | Not queried | Line reconciles. No project-level test |

**Whole-file test (stage 1 to stage 2, FY2027).** One query pulled every OMB budget line matching
`% D%` in the July 2026 adopted release (161 lines, all City non-exempt funding). The script in
`2026-10-14-capital-stage-map/` compares them with the October Council workbook:

- **146 of 153 Council lines match exactly** in FY2027 and FY2028.
- **7 lines differ** (Council vs OMB, FY2027): `F D175` $22,306,000 vs $22,556,000; `HD D022`
  $8,605,000 vs $21,105,000; `P D017` $28,156,000 vs $27,577,000; `P D019` $53,749,000 vs
  $56,634,000; `P D020` $26,394,000 vs $26,973,000; `P D021` $39,695,000 vs $39,861,000;
  `PV DN004` $5,000,000 vs $6,351,000. The repo's PDF-derived FY2027 data agrees with the Council
  workbook on all seven, so the gap is between the Council's list and OMB's appropriation, not a
  workbook error. `P D017` is $579,000 lower at OMB and `P D020` is $579,000 higher, which looks
  like one project booked in a different borough (interpretation).
- **8 OMB lines in the `D` series have no Council row**: `ED DN05U` $3,315,000, `ED DN07N`
  $2,525,000, `ED DN647` $1,000,000, `HR DN153` $500,000, `HR DN567` $489,000, `L D002` $75,000,
  `PW D005` $628,000, `S D129` $105,000.
- **Totals:** Council $853,688,000 / $44,000,000; OMB $879,477,000 / $44,000,000. The $25,789,000
  gap is $17,152,000 on the seven lines plus $8,637,000 on the eight.

## 4. What the MCP can honestly answer about capital

**Can answer, from structured data, with exact figures:**

- What the Council designated, to which project title, sponsor, district and budget line, by
  year: FY2019–FY2026 from `t474-a92g`, FY2027 from the RnD workbook.
- Whether the Council's money appears in the adopted capital budget, at budget-line grain, and
  where it does not (the 7 + 8 lines above become a reported discrepancy, not a hidden one).
- Where each Council budget line sits in each commitment plan release since 2016, including
  money that slipped to a later year.

**Can answer, with a stated match method and confidence:**

- Which FMS project(s) a Council designation became, for single-grantee `DN` lines and for
  titles that match the agency's project name. Report it as "matched by budget line and title,"
  never as a confirmed link.
- For a matched project: adopted, committed and spent to date, and DCP's sum of Checkbook
  checks, as of the one CPDB snapshot.
- For a matched project on the OPS dashboard: phase and forecast completion.

**Cannot answer from structured public data today:**

- Which contract a Council capital designation became, or which vendor holds it.
- Check-level payments for a designation (dates, payees), unless Checkbook capital spending can
  be filtered by FMS project, which was not tested.
- Project-level status for most of the 708 school projects on `E D001` and the other shared
  lines, without a text match that has not been tested at scale.
- Any capital history before FY2019 from Open Data. (The FY2017 Council workbook found on the
  Internet Archive under #86 is the next lead.)

## 5. Checkbook NYC spot check

- **One call**, `nyc-checkbook-mcp` `search_spending`: `payee_name = "DOWNTOWN COMMUNITY
  TELEVISION"`, `spending_category = c`, `issue_date_from = 2019-07-01`, `page_size = 50`.
- **Result: `Error: Empty response`.** No status code was surfaced. Per the rules, I stopped all
  Checkbook calls and made no others. A response with no data alongside an error means unknown,
  not "no payments."
- The plan had been to check CPDB's `spent_total_checkbooknyc` ($1,604,593 for `850PV132DCTV`)
  against Checkbook's own capital checks to DCTV.
- Also relevant: the MCP's `search_spending` has no capital-project or budget-code filter, only
  agency, payee, contract, dates, amount and category. A project-level payment test needs the
  Checkbook API documentation checked first (follow-up question 87-8).

## 6. #88: what the Council RnD site serves (read 2026-10-14, 10:58 UTC)

Two HTTP requests, both cached in `../nycb-cache/rnd-2026-10-14/` with headers and SHA-256 sums:

1. `GET https://rnd.council.nyc.gov/expense_funding/`, 200, 1,825 bytes, nginx 1.28.3. A
   single-page app shell that loads `/expense_funding/assets/index-DYh0fcxj.js`.
2. `GET https://rnd.council.nyc.gov/expense_funding/assets/index-DYh0fcxj.js`, 200, 562,034 bytes.

The page alone names no data files, so reading the bundle was the only way to see them. That is
why this "one read" took two requests. No redirects were followed. User-Agent:
`BetaNYC-research/1.0 (New-York-City-Budget issue #88; noel@beta.nyc)`.

**What the bundle loads.** One base URL, `https://rnd.council.nyc.gov/src/assets/`, and two
URL builders:

- Expense: `excelFund/funded_disclosure_FY{year}.{xls|xlsx}` for years `2027` back to `2013`
  (`xls` for 2013 and earlier, `xlsx` after). 15 files.
- Capital: `Capital-Database.xlsx`. One file, the current year only. The capital page reads the
  first sheet only.

**Nothing else.** No other workbook, CSV, JSON or PDF is referenced. Other strings in the
bundle are a logo, a Council icon on `council.nyc.gov`, and the client-side download name
`FY {year} Capital Discretionary Funding.xlsx` (generated in the browser, not a file on the
server). Routes: `/`, `/capital_funding`, `/expense_funding`.

**Small things the bundle tells us:**

- Council district filter values: `00`–`51`, `91`, `92`, `93`, `94`, `95`, `97`, `99`. Sponsor
  names extra to members: "Black, Latino and Asian Caucus", "Brooklyn Delegation". Borough map
  `Q, M, X, K, R` only (no `A`).
- The expense page records each workbook's `Last-Modified` header as its "as of" date. The
  server sent `Last-Modified` equal to the request time and `no-cache` for the page and bundle,
  so that header may not mean "last changed" for the workbooks either (follow-up question 88-1).
- This matches the 16 files the disclosure repo already mirrors
  (`NYCB-disclosure/source/expense-funding-disclosure/MANIFEST.csv`). Nothing is missing.

## Sources

- Council RnD site: <https://rnd.council.nyc.gov/expense_funding/>, <https://rnd.council.nyc.gov/capital_funding/>
- `t474-a92g`, `46m8-77gv`, `2cmn-uidm`, `djxg-kcfi`, `fi59-268w`, `fb86-vt7u` on
  <https://data.cityofnewyork.us/>
- Council workbook: `NYCB-disclosure/source/expense-funding-disclosure/Capital-Database.xlsx`
  (2026-10-12) and commit `98f1086` (July 2026)
- Repo PDF-derived capital: `data/fy27/capital/fy27_capital_projects.csv` (context only)

## Limits

- Six designations tested by hand, plus one whole-file test at budget-line grain. The text-match
  step has not been tested at scale.
- CPDB on Open Data is a single snapshot. I could not see how a project moved over time at
  project grain.
- OMB commitment plan amounts are rounded to thousands. A one-row line matches only to $1,000.
