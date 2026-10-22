# Plan: serve the checked PDF tables in the MCP and the explorer

**Report generated:** 2026-10-22. Prepared by BetaNYC with AI assistance.
**Data current as of:** `main` @ `2aecf90`; the FY2018–FY2025 PDF PRs (#139–#189) and their
integration; the live explorer as deployed from `9248851`.
**Status:** epic plan, before the grill. Nothing here changes code, data or the published package.

## The goal, in one line

The MCP answers questions from the clean tables we extract from the Council's budget PDFs, and the
public explorer lets anyone search the same tables, with every row one click from the page it was
read from.

## Why now

Version 2.0 (2026-10-14) stopped serving anything read from a PDF (DATA-ANOMALIES §27), because
the old parser lost and merged rows without saying so (§20, §21, #52, #59). The tables built since
are different. Each is read from the PDF's drawn borders, checked against a second reading of the
page image, tied to every printed total and checked for missed ink (`PDF-RECIPE.md`, #151). Every
flagged row goes to a review queue that a person decides. A year is served only when a person marks
it `closed` in `data/pdf_years.csv`. So the reason for retiring PDF data no longer holds for a
closed year.

## The rule both front ends share

- **Closed only.** A family-year appears in the MCP and the public explorer only when
  `data/pdf_years.csv` says `closed`. `reviewed` rows stay in local builds made with
  `--include-reviewed`. The index already works this way (`mcp/scripts/pdf-families.mjs`).
- **Values as printed.** No value is corrected. A row the PDF gets wrong carries its review decision
  (`source_error`) and note.
- **Every row links to its page.** Three links, built by one shared function so the MCP and the
  explorer never disagree:
  1. **The explorer's source view, at the row.** It already exists. Example, the FY2027 Medicare
     Rights Center award the old parser dropped:
     `https://betanyc.github.io/New-York-City-Budget/explorer/#view=source&spdf=source%2FFY27%2FFiscal-2027-Schedule-C-Final-3.pdf&spage=279&sbox=18.42%2C402.92%2C958.68%2C460.06&slabel=Medicare+Rights+Center%2C+%24135%2C000`
     opens page 279 with the row highlighted (checked on the live site 2026-10-22). It opens at the
     top of the page; it should scroll to the box.
  2. **The PDF on GitHub at the build's commit,** so the link never points at a changed file.
  3. **The publisher's copy,** where known (for example `source/gpp/MANIFEST.csv`, #187).

## Families and where each stands

| Family | Checked years (in PRs or merged) | MCP today | Explorer today |
|---|---|---|---|
| Schedule C | FY2018–FY2027 | none (retired in 2.0) | Only as a second source beside each disclosure award (`ScheduleC.jsx`); no search of all rows |
| Transparency resolutions | FY2018–FY2026 | none | Only inside Compare years; no view of its own |
| Capital §254 supporting detail | FY2018–FY2027 except FY2021 | none | Beside the workbook rows in Capital; Part III in Orgs |
| Terms and Conditions | FY2018, FY2021–FY2027 | none | Terms view |

## Workstreams (each becomes a child issue)

| # | Workstream | What "done" means |
|---|---|---|
| W0 | **Close the first years** (prerequisite) | At least FY2027 Schedule C `closed`, so every later workstream has real served data to test. Its review queue is already empty |
| W1 | **Shared row-link builder** | One function, used by the MCP and the explorer, turns a row's `source_pdf`, `pdf_page`, `bbox_pt` into the three links; tests prove both produce identical links |
| W2 | **Explorer source view scrolls to the row** | Opening a link lands on the highlighted box |
| W3 | **MCP tools** | `search_schedule_c_awards`, `search_transparency_changes`, `search_capital_book`, `search_terms_conditions`, each closed-only, each row with values as printed, flags, decision and the three links; `list_available_fiscal_years` reports each family-year's status; the `REMOVED_TOOLS` notes point at the new tools |
| W4 | **Explorer: a searchable page for every family** | Schedule C search across all rows (not only matched pairs); a new Transparency view (by organization, member, resolution and date); a capital-book search; Terms unchanged. All closed-only on the public site, every row linking to its page |
| W5 | **Tests that guard the rule** | Replace, on purpose, the two tests that today guarantee the opposite (`mcp/test/no-pdf-data.test.js`, `mcp/test/pdf-families.test.js` "no tool reads a pdf_* table"). New: a `reviewed` row never reaches a tool answer or the public build; MCP answers equal the explorer's for the same query; every link resolves |
| W6 | **Docs** | MCP README, DATA-ANOMALIES (a section that narrows §27), the explorer's About page, `PDF-RECIPE.md` (what "closed" makes public) |
| W7 | **Release** | MCP minor version (new tools, nothing removed), e.g. 2.1.0; the explorer redeploys on merge. The npm tag (`mcp-v2.1.0`) is pushed by Noel only |

## How the work is run

- **Builders.** One session per workstream group, each in its own worktree from `main`, opening PRs
  and never merging: W1+W3+W5 (MCP), W2+W4 (explorer), W6 after both. W1 lands first because the
  other two use it.
- **QA, independent of the builders.** For each builder PR, separate sessions that did not write the
  code check it:
  1. **Code review:** correctness, the closed-only gate, no `reviewed` leak, error handling.
  2. **Data parity:** the same question asked of the MCP, the explorer and the CSVs gives the same
     rows and totals.
  3. **Links:** every link from a sample of rows opens the right page, with the box on the row.
  4. **Plain-language check** of every user-facing string.
  Findings go back to the builder; the orchestrator merges only after QA passes and Noel says so.
- **Gate on data.** W3 and W4 are tested against W0's closed year. Until then they run against a
  local `--include-reviewed` build and must show nothing on a public build.

## Estimate

Agent build time, from last night's pace (two PDF families per session in 1–2.5 hours):

| Work | Time |
|---|---|
| W1 + W2 | about 1 hour |
| W3 + W5 | one session, 2–3 hours |
| W4 | one session, 2–4 hours |
| W6 | about 1 hour |
| QA rounds and fixes | 2–4 hours across sessions |

About a day of sessions in parallel. The pace is set by closing years (people deciding review items)
and by review of the PRs.

## Open questions for the grill

1. Four MCP tools, or one `search_pdf_tables`? (Recommendation: four.)
2. Should `search_disclosure_awards` mention the matching Schedule C row, or stay separate?
   (Recommendation: separate; Schedule C rows carry `disclosure_status`.)
3. What closes a family: every item decided, or every critical item decided plus the warnings
   accepted in bulk? `--complete` counts `needs_info` as decided today.
4. Package size: `mcp/data/budget.db` is about 51 MB; every closed year adds to it. Ship it in the
   package, or as a separate download?
5. Which front end comes first, the MCP or the explorer pages?
6. Should the explorer show `reviewed` years publicly, labeled "in review"? Today it does not.

## Related

Epic #101 (getting the years checked); `PDF-RECIPE.md` (#151); DATA-ANOMALIES §20, §21, §27; the
explorer's source view (`viz/explorer/src/views/Source.jsx`, `src/state/hash.js`); the portal PDFs
(#186, #187).
