# Plan: serve the checked PDF tables in the MCP and the explorer

**Report generated:** 2026-10-22. Prepared by BetaNYC with AI assistance.
**Data current as of:** `main` @ `3af3c7c` (FY2018–FY2027 checked tables merged in #203); the live
explorer as deployed from that commit.
**Last revised:** 2026-10-22, after the grill with Noel Hidalgo: every open question is decided
(see "Decisions").
**Status:** epic plan for #190. Nothing here changes code, data or the published package yet.

## The goal, in one line

The MCP answers questions from the clean tables we extract from the Council's budget PDFs, and the
public explorer lets anyone search the same tables, with every row one click from the page it was
read from.

## Why now

Version 2.0 (decided 2026-10-14, released 2026-10-17) stopped serving anything read from a PDF
(DATA-ANOMALIES §27), because the old parser lost and merged rows without saying so (§20, §21, #52,
#59). The tables built since are different. Each is read from the PDF's own text and ruled lines,
checked against a second reading of the page image, tied to every printed total and checked for
missed ink (`PDF-RECIPE.md`). Every flagged row goes to a review queue that a person decides.

## The rules both front ends share

- **Checked data only.** The MCP and the public explorer serve every family-year that went through
  the new process: `reviewed` and `closed` in `data/pdf_years.csv`. Every row says which:
  "checked, review in progress" or "checked and reviewed". The old parser's output (FY2008–FY2017
  until redone) is never served; the MCP says those years aren't available yet.
- **Values as printed.** No value is corrected. A row the PDF gets wrong carries its review decision
  (`source_error`) and note. Where the page and the PDF's text layer disagree, a person checks the
  page in review; if confirmed, the value a reader sees on the page is used and flagged "read from
  the page image". The reader never swaps values on its own.
- **Hidden text is served, and labeled.** Text in the PDF that a reader can't see on the page
  (clipped names, staff notes past a table's edge) is returned in its own field, always labeled
  "hidden text, not visible on the printed page".
- **Every row links to its page.** Three links, built by one shared function so the MCP and the
  explorer never disagree:
  1. **The explorer's source view, at the row.** It already exists. Example, the FY2027 Medicare
     Rights Center award the old parser dropped:
     `https://betanyc.github.io/New-York-City-Budget/explorer/#view=source&spdf=source%2FFY27%2FFiscal-2027-Schedule-C-Final-3.pdf&spage=279&sbox=18.42%2C402.92%2C958.68%2C460.06&slabel=Medicare+Rights+Center%2C+%24135%2C000`
     opens page 279 with the row highlighted (checked on the live site 2026-10-22). It opens at the
     top of the page; it should scroll to the box.
  2. **The PDF on GitHub at the build's commit,** so the link never points at a changed file.
  3. **The publisher's copy,** where known (for example `source/gpp/MANIFEST.csv`).

## What "closed" means

A family-year is `closed` when:

1. Every **critical** item is decided one by one.
2. Every **warning** is decided, individually or in groups by check type with one note per group
   (for example "all 37 hyphen-break warnings: `accepted_as_printed`").
3. Every **`needs_info`** item is answered, or has waited 30 days since its question was sent. After
   30 days the row is published as printed with a visible label ("Question sent to Council Finance
   on <date>, no answer yet"); the question stays open as a GitHub issue.

`code/validate_review_decisions.py --complete` must enforce this (#194).

## Families and where each stands

| Family | Checked years (on `main`) | MCP today | Explorer today |
|---|---|---|---|
| Schedule C | FY2018–FY2027 | none (retired in 2.0) | Only as a second source beside each disclosure award (`ScheduleC.jsx`); no search of all rows |
| Transparency resolutions | FY2018–FY2026 | none | Only inside Compare years; no view of its own |
| Capital §254 supporting detail | FY2018–FY2027 except FY2021 (OMB's copy is in `source/gpp/`, #186) | none | Beside the workbook rows in Capital; Part III in Orgs |
| Terms and Conditions | FY2018, FY2021–FY2027 | none | Terms view |

## Workstreams (each becomes a child issue)

| # | Workstream | What "done" means |
|---|---|---|
| W1 | **Shared row-link builder** | One function, used by the MCP and the explorer, turns a row's `source_pdf`, `pdf_page`, `bbox_pt` into the three links; tests prove both produce identical links |
| W2 | **Explorer source view scrolls to the row** | Opening a link lands on the highlighted box |
| W3 | **MCP tools** | Four tools: `search_schedule_c_awards` (with each row's `disclosure_status`), `search_transparency_changes`, `search_capital_book`, `search_terms_conditions`. Each row returns values as printed, review status label, flags, decision, hidden text (labeled) and the three links. `search_disclosure_awards` stays separate. `list_available_fiscal_years` reports each family-year's status; the `REMOVED_TOOLS` notes point at the new tools |
| W4 | **Explorer: a searchable page for every family** | Schedule C search across all rows; a new Transparency view (by organization, member, resolution and date); a capital-book search; Terms with book-order numbers labeled. Reviewed and closed years, each row labeled with its status and linking to its page. Includes #205 and #206 |
| W5 | **Tests that guard the rules** | Replace, on purpose, the two tests that forbid PDF data today (`mcp/test/no-pdf-data.test.js`, `mcp/test/pdf-families.test.js`). New: no old-parser row is ever served; every served row carries its status label; MCP answers equal the explorer's; every link resolves |
| W6 | **Optional PDF data download** | The npm package keeps only the spreadsheet data (about 51 MB) on the user's drive. The PDF tables (about 115 MB more) and, optionally, the PDF files themselves download on request, through both `npx @betanyc/nyc-budget-mcp download --pdf-tables [--pdfs]` and a config setting (e.g. `NYC_BUDGET_PDF_DATA=on`). Files come from this repo's GitHub Releases and are checked against published sha256s. Until downloaded, the four PDF tools say how to add them |
| W7 | **Automatic data releases** | A workflow builds, checks and publishes a dated data release to GitHub Releases whenever a merge to `main` changes the PDF tables. npm releases still need Noel's tag |
| W8 | **Schema changes from the grill** | A `fiscal_conduit` field in Schedule C and transparency for every year; a field for the `*` mark (named from the PDF's own footnote); a `program_or_subheading` field so `purpose` holds only the printed purpose; a sub-awards table for the Jobs to Build On partner list (FY2019, FY2018), linked to the CWE award; "no dollar amount" rows (Beating Hearts) kept and marked; the page-image rule above, applied first to FY2023 Laundromat Project and FY2019 Himalayan Elders |
| W9 | **Data housekeeping** | Retired PDF-parser CSVs move to `data/retired/` with a pointer, year by year as each is redone; `wb_pick_by_amount` turned on for FY2026 and its 3 decided items re-checked; FY2018 capital fills the gap in `data/capital/`, labeled "from the PDF", once FY2018 capital is closed (#202); FY2024 capital signed off, with the PDF's "no copying" setting noted in DATA-ANOMALIES |
| W10 | **Docs** | The repo README rewritten for how things work now; MCP README; DATA-ANOMALIES (a section that narrows §27); the explorer's About page; `PDF-RECIPE.md` (what reviewed and closed mean) |
| W11 | **Release** | MCP minor version (new tools, nothing removed), e.g. 2.1.0; tag pushed by Noel only; the explorer redeploys on merge |

## Working with the data owners

- **Council Finance questions** (every `needs_info` item: MA-series capital rows, FY2025 Apollo
  Theater, FY2022 Borough President rows, the older ones): one shared document or spreadsheet the
  Council answers in, plus a monthly email from Noel pointing to it. Each question also gets a
  GitHub issue recording the date sent, which starts its 30 days. Drafts are prepared for Noel; he
  sends them.
- **NYC Open Data `t474-a92g`** (City Council Capital Budget, published by the Council, starts at
  FY2019): ask the Council to add FY2018 and earlier, offering our checked FY2018 table, in two
  ways: an email from Noel to the Council team BetaNYC already works with, and the portal's
  "contact dataset owner" form, so the request is also on the City's record. Both drafted for Noel;
  he sends the email and submits the form, or approves submitting it.

## How the work is run

- **Builders.** One session per workstream group, each in its own worktree from `main`, opening PRs
  and never merging. The MCP and the explorer are built at the same time:
  1. W1 first (both use it).
  2. Then in parallel: MCP (W3, W5, W6), explorer (W2, W4), schema (W8, before W3/W4 finish
     their filters), housekeeping (W9).
  3. Then W7, W10, W11.
- **QA, independent of the builders.** For each builder PR, separate sessions that did not write the
  code check it:
  1. **Code review:** correctness, the status labels, no old-parser row served, error handling.
  2. **Data parity:** the same question asked of the MCP, the explorer and the CSVs gives the same
     rows and totals.
  3. **Links:** every link from a sample of rows opens the right page, with the box on the row.
  4. **Plain-language check** of every user-facing string.
  Findings go back to the builder; the orchestrator merges only after QA passes and Noel says so.

## Estimate

Agent build time, from the overnight pace (two PDF families per session in 1–2.5 hours):

| Work | Time |
|---|---|
| W1 + W2 | about 1 hour |
| W3 + W5 | 2–3 hours |
| W4 | 2–4 hours |
| W6 + W7 | 2–3 hours |
| W8 | 2–3 hours (re-promotes every year) |
| W9, W10 | 1–2 hours |
| QA rounds and fixes | 3–5 hours across sessions |

About a day or two of sessions in parallel. Closing years (people deciding review items) and PR
review set the real pace.

## Decisions (grill, 2026-10-22)

| # | Question | Decision |
|---|---|---|
| 1 | What closes a family? | Critical items one by one; warnings in groups by type; `needs_info` blocks |
| 2 | An unanswered Council Finance question? | Publish after 30 days, labeled with the date sent; the issue stays open |
| 3 | MCP or explorer first? | Both at once |
| 4 | Four MCP tools or one? | Four |
| 5 | Show years still in review? | Yes, in the explorer and the MCP, labeled |
| 6 | Package size | Spreadsheet data stays in the package; PDF tables and PDFs are an optional download |
| 7 | How to get the download | Both a command and a config setting, from this repo's GitHub Releases |
| 8 | Schedule C and the disclosure | Separate tools, linked by `disclosure_status` |
| 9 | Who publishes? | Data releases automatically on merge; npm on Noel's tag |
| 10 | Old parser output | Never shown |
| 11 | Telling the story | A project page plus a post on beta.nyc; part of a later effort to give each GitHub repo its own project page |
| 12 | FY2024 capital "no copying" setting | Signed off; noted in DATA-ANOMALIES |
| 13 | Jobs to Build On partner list | A separate sub-awards table, linked to the CWE award |
| 14 | Beating Hearts rows | Kept, marked "no dollar amount"; totals skip them |
| 15 | Hidden text | Served in both, labeled |
| 16 | Fiscal conduits | One field, both tables, every year |
| 17 | The `*` mark | Its own field |
| 18 | Program column and sub-headings | Their own field |
| 19 | Page vs. text layer | The page wins after a person confirms it in review; flagged |
| 20 | MA-series capital items | `needs_info` in every year; one question to Council Finance |
| 21 | Reaching Council Finance | Shared doc or spreadsheet, plus a monthly email from Noel; GitHub issues record the date |
| 22 | FY2018 Reso 01 (dated 2017-06-21) | Stays in FY2018; each chart's own fiscal year on its rows |
| 23 | Old CSVs | Move to `data/retired/` |
| 24 | FY2026 `wb_pick_by_amount` | On; re-check its 3 decided items |
| 25 | FY2018 capital in `data/capital/` | Yes, labeled "from the PDF", once closed |
| 26 | Asking the Council to fill `t474-a92g` | Both: an email to the Council team we know, and NYC Open Data's "contact dataset owner" form |

## Related

Epic #101 (getting the years checked); epic #190; decisions issue #209; `PDF-RECIPE.md`;
DATA-ANOMALIES §20, §21, §27; the explorer's source view (`viz/explorer/src/views/Source.jsx`,
`src/state/hash.js`); the portal PDFs (#186); known bugs #192–#208.
