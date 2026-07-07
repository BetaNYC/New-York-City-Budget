# Scoping: FY2022–FY2024 Schedule C gap

**Report generated:** 2026-07-07
**Data current as of:** 2026-07-07
**Status:** Discovery pass complete. 11 of 12 possible core documents (Schedule C, Terms
& Conditions, Capital ×2 document types where published) + all 37 transparency
resolutions downloaded and format-tested against the existing FY25–27 parsers. Ready to
hand to `software-engineer` for the parsing phase.

## Why this gap exists

This repo's PDF-extraction pipeline covers FY2025–FY2027. NYC Open Data's
["City Council Discretionary Funding"](https://data.cityofnewyork.us/dataset/4d7f-74pe)
dataset covers FY2009–FY2021 but stopped being updated in April 2021. That leaves
**FY2022, FY2023, and FY2024 with no source anywhere** in either this repo or the
Open Data catalog.

## Goal

Determine whether Schedule C, Terms & Conditions, Section 254 capital changes, and
post-adoption Transparency Resolutions can be sourced for FY2022–FY2024, matching
the document set this repo already has for FY2025–FY2027 as closely as possible.

**Interpretation of scope:** "match as much as you can from the existing work" is read
here as full parity with the current FY25–27 document set — Schedule C, Terms &
Conditions, Capital (Section 254), and Transparency Resolutions — not Schedule C alone.
Flag if that's too broad.

## What this task is and isn't

- **Is:** discovery, acquisition of source PDFs, and documentation of per-year format
  deviations against the existing parsers.
- **Isn't:** writing or adapting parser code. Once source documents are in hand and
  deviations are documented, parsing/extraction work routes to the `software-engineer`
  agent as a follow-on task — this memo is written to be handed to that agent directly,
  without it needing to re-derive context.

## Sources to consult

1. **council.nyc.gov budget archive** — primary. Check whether FY22/23/24 Adopted
   Budget documents (Schedule C, Terms & Conditions, Section 254) are published there
   the same way FY25–27 are.
2. **`nyc-council-mcp` (Legistar-backed)** — for two purposes: (a) locating budget-adoption
   legislative records and any attached documents if the Council site copy is missing
   or reorganized, and (b) searching for "Transparency Resolution"–pattern items in the
   months following each of the three budget adoptions (June 2021 → FY22 cycle, June
   2022 → FY23, June 2023 → FY24). First confirms whether the Transparency Resolution
   practice even existed before FY26 — it may not, and "doesn't exist for this year" is
   a legitimate finding.
3. **Wayback Machine** — fallback if the Council site has reorganized or removed older
   budget documents.
4. **`nyc-checkbook-mcp`** — light-touch plausibility cross-check only, not primary
   sourcing or full reconciliation.
5. **This repo's own `code/` parsers** (`parse_schedule_c.py`, `parse_terms.py`,
   `parse_capital.py` + the `_fy25`/`_fy26` variants) — reference for what format
   deviations would mean for a future parser.

## Methodology

1. Locate and download Schedule C, Terms & Conditions, and Capital (Section 254) PDFs
   for FY22/FY23/FY24 from council.nyc.gov; save into `source/FY22/`, `source/FY23/`,
   `source/FY24/` following this repo's existing layout. This is data acquisition, not
   parsing — in scope for this task.
2. For any document not found on the Council site: try Wayback Machine, then a
   `nyc-council-mcp` Legistar search for the budget-adoption record and any attachments.
3. Query `nyc-council-mcp` for Transparency-Resolution-pattern items in each post-adoption
   window; confirm whether the practice predates FY26.
4. Spot-check a handful of found amounts against `nyc-checkbook-mcp` for plausibility.
5. Diff each found document's structure against the existing parser assumptions and
   write up deviations per year — explicit enough that `software-engineer` can act on
   them without re-reading the source PDFs from scratch.

## Output

- `research/2026-07-07-fy22-fy24-gap-scoping.md` (this file) — updated in place with
  findings once the discovery pass runs.
- `source/FY22/`, `source/FY23/`, `source/FY24/` — located PDFs, if found.
- A per-year "processing notes" section below (added once discovery runs), one per
  fiscal year, covering: source status, resolution inventory, format deviations from
  the FY25–27 parsers, and a feasibility verdict — this is the brief handed to
  `software-engineer` for the parsing phase.

## Effort estimate

A few hours of research — web reconnaissance plus two live MCP sources and light
cross-checking. No parsing or coding in this phase.

## Open questions

1. Confirm the scope interpretation above — full FY25–27 document parity (Schedule C +
   Terms & Conditions + Capital + Transparency Resolutions), not Schedule C + T&C only?
2. OK to use `nyc-council-mcp` and `nyc-checkbook-mcp` live, and to fetch/browse
   council.nyc.gov budget-archive pages, for this discovery pass?
3. If a fiscal year's Transparency Resolution practice turns out not to have existed
   before FY26, is "N/A for this year, documented and moved on" sufficient, or should I
   dig for an earlier equivalent under a different name?
4. This repo now has a `research/` folder and a `research/fy22-24-schedule-c-gap`
   branch that don't exist on `main` yet — OK to hold off on pushing / opening a PR
   until you've reviewed the scoping findings, rather than pushing now?

## Processing notes (per fiscal year)

**Methodology actually used:** `council.nyc.gov/budget/fy20NN/` turned out to have a
complete, stable archive page for all three years — every document type was found there
directly (Wayback Machine and Legistar attachment-fishing were not needed). Legistar
(`nyc-council-mcp`) was used only for the secondary check below (confirming the
transparency-resolution practice is real Council legislation). All PDFs downloaded with
`curl`, validated with `file`, and test-parsed with the **unmodified** FY25–27 parsers in
a throwaway venv (`/tmp/nycb_venv`, `pypdf` 6.14.2 + `pdfplumber`) — no changes were made
to `code/`. Test outputs are not committed (they lived in `/tmp/nycb_test`); anyone
repeating this should get near-identical reconciliation numbers by re-running the same
commands against the files now in `source/`.

**Global finding — the Transparency Resolution practice predates FY26 and goes back at
least to FY2022.** Noel's framing is confirmed as fact, not assumption: council.nyc.gov
publishes a "Transparency Resolutions" section on every fiscal year's budget archive page
back through FY2022, each a Committee-on-Finance report attached to a Council resolution
titled "RESOLUTION APPROVING THE NEW DESIGNATION AND CHANGES IN THE DESIGNATION OF
CERTAIN ORGANIZATIONS TO RECEIVE FUNDING IN THE EXPENSE BUDGET" (confirmed by reading the
opening page of FY22 Reso #1). The council.nyc.gov copies are primary-source Council
Finance Division publications, not secondary reporting. I was **not** able to attach
Legistar matter IDs to individual resolutions in the time budgeted — `nyc-council-mcp`'s
local full-text index (`search_bills`/`search_events`) appears to index Introductions
(Local Laws) far more completely than Resolutions; single-token searches for
"Transparency," "designation," and "budget" returned only unrelated Int-numbered local
laws, never the Finance Committee resolutions themselves. This is consistent with a
known tool quirk logged in the 2026-06-05 research-intelligence journal entry (resolutions
need a `Res `-prefixed exact file number, which we don't have). **Not a blocker** — the
document itself is the primary source and states its own legislative status — but a
`software-engineer`/future pass wanting formal Legistar matter IDs per resolution would
need to browse `legistar.council.nyc.gov` directly rather than rely on the MCP's search.

**Checkbook plausibility check (light-touch, as scoped):** spot-checked two FY2022
Schedule C awards against `nyc-checkbook-mcp` — viBe Theater Experience, Inc. (DCLA, $5,000
Schedule C designation) shows real FY2022 DCLA contract payments (multiple checks,
$2,460–$68,000, issued Jul 2021–Mar 2022); African Services Committee, Inc. (DHMH, $5,000
designation) shows real FY2022 payments from DHMH/DSS/DYCD (51 checks, consistent with the
repo's own documented caveat that discretionary designations often get folded into larger
delegate-agency contracts rather than paid as isolated line items). Both pass the sniff
test — real recipients, real money, right agencies, right fiscal year.

---

### FY2022

**Source status — all four document types found and downloaded**, all directly from
`council.nyc.gov/budget/fy2022/`:

| Document | Local path | Status |
|---|---|---|
| Schedule C | `source/FY22/Fiscal-2022-Schedule-C-Merge-6.30.21.pdf` | Found, downloaded (326 pages) |
| Terms & Conditions | `source/FY22/FY22-Terms-and-Conditions_FINAL.pdf` | Found, downloaded (18 pages) |
| Capital (Section 254), Capital Project Detail type | `source/FY22/FY22-Sec254-Capital-Supporting-Detail-Book.pdf` | Found, downloaded (92 pages) |
| Capital (Section 254), Resolution-A/Appropriation-Changes type | — | **Not found on council.nyc.gov.** The FY2022 archive page has only one capital link (the Supporting Detail Book above); no "Reso A Book" or "Changes To..." link is present, unlike FY2023/FY2024 (see below). Not chased via Wayback/Legistar within the time budget — flagged as an open gap, not confirmed unpublished. |
| Transparency Resolutions | `source/FY22/transparency-resolutions/` | All 14 found and downloaded (`Transparency-Reso-01-2021-07-29.pdf` … `Transparency-Reso-14-2022-06-13.pdf`, covering July 29, 2021 – June 13, 2022) |

**Transparency-resolution-equivalent legislation inventory:** 14 resolutions, titled
"Transparency Resolution #1–#14" on the council.nyc.gov page itself — same name FY26
uses. Confirms the practice and the naming both predate FY26 by at least 4 years.

**Format deviations from the FY25–27 parsers:**

- **Schedule C — no deviation.** `parse_schedule_c.py` run unmodified reconciles
  **24/26 categories exact**, GRAND TOTAL $465,014,395 vs printed $465,728,895 (two
  categories — Veterans Services, Youth Services — differ, same class of in-source
  arithmetic inconsistency already documented for FY25/FY26, not a parser fault).
  1,479 award rows, $221.76M. ANCHOR/TOC/RUNHDR regexes all match cleanly.
- **Terms & Conditions — real deviation, parser variant needed.** Current output: **0
  rows** (silent failure, not an error). Root cause: `HEADER` regex requires a leading
  item number (`^\d{1,3}\.\s+...`), but FY22's document has **no item numbering at
  all** — each condition just opens with `Agency Name (Code)` (e.g. "Administration
  for Children's Services (068)"), confirmed by direct text inspection. A second,
  separate item-header shape exists for capital-line conditions: a bare `Capital
  Budget` line (no agency name, no 3-digit code) followed by one or more `Budget Line
  XX-NNNN – Title` lines — this is unlike FY25's phrasing of the same concept
  (`N. Capital Budget for Agency Name (Code)`, which *does* match the numbered-header
  regex). FY22 has 58 agency-code headers + 4 bare "Capital Budget" headers (5 budget-line
  sub-entries across them) = roughly 62 condition items total, in an 18-page document.
  **A new parser variant needs:** (1) a HEADER regex without the leading-number
  requirement, with a synthetic sequential `item_number` assigned during parsing since
  the source doesn't number items; (2) a second header pattern for the bare `Capital
  Budget` / `Budget Line` case with no agency code.
- **Capital (Supporting Detail Book / Capital Project Detail type) — real deviation,
  parser variant needed, but reconciliation is achievable.** `parse_capital.py` run
  unmodified against the FY22 Supporting Detail Book produces **0 projects** — not
  because the document type differs (the Table of Contents literally reads "I. FY 2022
  CHANGES TO THE EXECUTIVE CAPITAL BUDGET PURSUANT TO SECTION 254 CAPITAL PROJECT
  DETAIL," the same document type FY26/FY27 use), but because **pypdf's
  `extract_text()` returns the rows in scrambled column order** for this PDF — e.g. a
  project row reads `E  CN002 M P.S. 2 MEYER LONDON SCHOOL TECH UPGRADE` then a
  separate line `B:M002 S:M002` then `0E  D001 CHIN0 090,000`, interleaving the
  title/sponsor/amount columns instead of one clean row per project. The `ROW` regex
  (built for FY26/27's clean linear text) never matches. This is the **same class of
  problem** `parse_capital_fy25.py` and `parse_transparency_reso.py` already solved for
  their harder documents via pdfplumber word-coordinate clustering
  (`cluster_rows()`/`load_lines()`) — the fix is to apply that same technique here
  rather than pypdf's naive line splitting. Reconciliation targets exist and are
  intact: **34 `TOTALS FOR <agency> (N PROJECTS)` subtotal lines** are present in the
  raw text (confirmed via regex scan), so a coordinate-aware rewrite should be able to
  reconcile the same way FY26/FY27 do.

**Feasibility verdict:** Schedule C — parseable today, zero code changes. Terms &
Conditions — needs a small `_legacy` HEADER-regex variant (no line-order/layout fix
needed, moderate effort, maybe an hour of work). Capital — needs a pdfplumber
coordinate-clustering rewrite following the pattern already established in
`parse_capital_fy25.py`/`parse_transparency_reso.py` (higher effort than T&C, lower than
building from scratch since the technique is proven in-repo). Transparency Resolutions —
parseable today with the single-PDF invocation of `parse_transparency_reso.py`; only
`batch()` needs its hardcoded `!= 10` PDF-count assertion (`code/parse_transparency_reso.py:259`)
parameterized to accept 14. The missing Reso-A/Appropriation-Changes capital document is
the one open item requiring a follow-up decision (accept the gap, or spend more time on
Wayback/Legistar).

---

### FY2023

**Source status — all four document types found and downloaded**, all from
`council.nyc.gov/budget/fy2023/`. FY2023 is the richest of the three years: **two**
distinct capital documents were published (unlike FY22's one), matching the FY2024/FY2025
pattern rather than FY2022's.

| Document | Local path | Status |
|---|---|---|
| Schedule C | `source/FY23/Fiscal-2023-Schedule-C-Merge-6.13.22-Final-1.pdf` | Found, downloaded (334 pages) |
| Terms & Conditions | `source/FY23/FY23-Terms-and-Conditions_FINAL_OMB-and-Council-Review-6.11.22.pdf` | Found, downloaded (19 pages) |
| Capital, Capital Project Detail type ("Supporting Detail Book") | `source/FY23/FY23-Sec254-Capital-Supporting-Detail-Book.pdf` | Found, downloaded (89 pages) |
| Capital, Resolution-A/Appropriation-Changes type ("Reso A Book") | `source/FY23/FY23-Sec254-Capital-ResoA-Book.pdf` | Found, downloaded (101 pages) — opens with the literal "RESOLUTION A / Resolved, by the Council, pursuant to section 254..." text, textually the same document type as FY25's `Fiscal-2025-Capital-Changes.pdf` |
| Transparency Resolutions | `source/FY23/transparency-resolutions/` | All 14 found and downloaded (`Transparency-Reso-01-2022-07-14.pdf` … `Transparency-Reso-14-2023-06-30.pdf`, covering July 14, 2022 – June 30, 2023) |

**Transparency-resolution-equivalent legislation inventory:** 14 resolutions, same
"Transparency Resolution #N" naming and Finance Committee report structure as FY2022 and
FY2026.

**Format deviations from the FY25–27 parsers:**

- **Schedule C — no deviation.** `parse_schedule_c.py` run unmodified reconciles
  **26/26 categories exact**, GRAND TOTAL $486,446,095 (matches printed exactly — the
  best reconciliation of any of the three years, on par with FY2027's clean run).
  1,824 award rows, $260.06M.
- **Terms & Conditions — same deviation as FY2022.** 0 rows from the unmodified
  parser, same root cause: no leading item numbers (62 agency-code headers found via a
  test regex without the number requirement), plus 4 bare `Capital Budget` headers (5
  `Budget Line` sub-entries) in a 19-page document. The FY22 parser-variant spec above
  applies unchanged to FY2023.
- **Capital, Capital Project Detail type — same deviation as FY2022.** Column-order
  scrambling in pypdf's `extract_text()` on the same "CAPITAL PROJECT DETAIL" document
  type; 32 `TOTALS FOR <agency> (N PROJECTS)` subtotal lines confirmed present and
  available for reconciliation once a pdfplumber rewrite exists.
- **Capital, Resolution-A/Appropriation-Changes type — no deviation.**
  `parse_capital_fy25.py` run unmodified against `FY23-Sec254-Capital-ResoA-Book.pdf`
  parses cleanly: 130 change blocks, $893.6M total FY2023 (CN) change amount, correctly
  labeled `NOT RECONCILABLE` (matches FY25's own documented status — this document type
  has no printed subtotals to check against, same as FY25).

**Feasibility verdict:** Schedule C and the Reso-A/Appropriation-Changes capital
document — parseable today, zero code changes (best-case year of the three). Terms &
Conditions and the Capital-Project-Detail capital document need the same two parser
variants scoped under FY2022, applied identically here (no FY23-specific new work, this
is shared engineering effort across FY22–24).

---

### FY2024

**Source status — all four document types found and downloaded**, all from
`council.nyc.gov/budget/fy2024/`. Same two-capital-document pattern as FY2023.

| Document | Local path | Status |
|---|---|---|
| Schedule C | `source/FY24/Fiscal-2024-Schedule-C-Merge-Final.pdf` | Found, downloaded (453 pages — notably larger than FY22/23) |
| Terms & Conditions | `source/FY24/FY24-Terms-and-Conditions.pdf` | Found, downloaded (24 pages) |
| Capital, Capital Project Detail type ("Section 254 Supporting Detail Book") | `source/FY24/FY2024-Sec254-Supporting-Detail-Book_7.10.2023pwp-2.pdf` | Found, downloaded (78 pages) |
| Capital, Resolution-A/Appropriation-Changes type ("Changes To The Executive Capital Budget Adopted by the City Council") | `source/FY24/Fiscal-Year-2024-Changes-To-The-Executive-Capital-Budget-Adopted-by-the-City-Council.pdf` | Found, downloaded (86 pages) — same "RESOLUTION A" opening text as FY23's Reso A Book and FY25's Capital-Changes.pdf; this is the year where the council.nyc.gov *filename itself* echoes FY25's document title almost verbatim, which is what first suggested (and then confirmed) the two are the same document type |
| Transparency Resolutions | `source/FY24/transparency-resolutions/` | All 9 found and downloaded (`Transparency-Reso-01-2023-08-03.pdf` … `Transparency-Reso-09-2024-06-30.pdf`, covering August 3, 2023 – June 30, 2024) |

**Transparency-resolution-equivalent legislation inventory:** 9 resolutions (fewer than
FY22/FY23's 14 — cadence appears to have slowed from roughly monthly to roughly
bimonthly/quarterly starting this year), same naming and structure.

**Format deviations from the FY25–27 parsers:**

- **Schedule C — no deviation, but note the near-miss.** `parse_schedule_c.py` run
  unmodified reconciles **24/26 categories exact**, GRAND TOTAL $471,928,500 vs printed
  $471,875,565 (two categories differ by a net $52,935 — same in-source arithmetic-
  inconsistency class as FY22, FY25, FY26, not a parser fault). 5,299 award rows,
  $398.0M — a much higher row count than FY22/23, consistent with the much larger page
  count (453 pp).
- **Terms & Conditions — same deviation as FY2022/FY2023.** 0 rows from the unmodified
  parser; 68 agency-code headers (no leading numbers) + 4 bare `Capital Budget` headers
  (5 `Budget Line` sub-entries) in a 24-page document. Same parser-variant spec applies.
- **Capital, Capital Project Detail type — same deviation as FY2022/FY2023.** Same
  pypdf column-scrambling; 32 `TOTALS FOR <agency> (N PROJECTS)` subtotal lines
  confirmed present.
- **Capital, Resolution-A/Appropriation-Changes type — no deviation.**
  `parse_capital_fy25.py` run unmodified against the "Changes To..." PDF parses cleanly:
  138 change blocks, $1.145B total FY2024 (CN) change amount, `NOT RECONCILABLE` (as
  expected, same as FY23 and FY25).

**Feasibility verdict:** Schedule C and the Reso-A/Appropriation-Changes capital
document — parseable today, zero code changes. Terms & Conditions and the
Capital-Project-Detail document need the same shared parser variants as FY22/FY23 — no
FY24-specific new work.

---

### Cross-year summary for `software-engineer`

| Document type | FY22 | FY23 | FY24 | Parser work needed |
|---|---|---|---|---|
| Schedule C | Found, reconciles 24/26 | Found, reconciles 26/26 | Found, reconciles 24/26 | **None** — `parse_schedule_c.py` works as-is on all three |
| Terms & Conditions | Found, 0 rows (unnumbered headers + bare Capital Budget items) | Same deviation | Same deviation | **One shared variant** — HEADER regex without leading-number requirement + synthetic item_number + a second bare-"Capital Budget" header pattern. Same fix serves all three years. |
| Capital — Capital Project Detail ("Supporting Detail Book") | Found, 0 projects (pypdf column-scrambling) | Same deviation | Same deviation | **One shared pdfplumber rewrite** — apply the coordinate-clustering technique already proven in `parse_capital_fy25.py`/`parse_transparency_reso.py`. Subtotals exist for reconciliation in all three years (34/32/32 `TOTALS FOR` lines). |
| Capital — Resolution A / Appropriation Changes | **Not found** on council.nyc.gov (open gap) | Found, parses cleanly with `parse_capital_fy25.py` unmodified | Found, parses cleanly with `parse_capital_fy25.py` unmodified | **None** for FY23/FY24. FY22 needs a decision: accept the gap, or spend more time chasing Wayback/Legistar. |
| Transparency Resolutions | Found, 14 resos, parses cleanly per-PDF | Found, 14 resos, parses cleanly per-PDF | Found, 9 resos, parses cleanly per-PDF | **None** for single-PDF parsing. `batch()`'s hardcoded `!= 10` count assertion (line 259) needs to accept 14/14/9 instead of always-10. |

**Total new source material added:** 11 core PDFs (3 FY22 + 4 FY23 + 4 FY24 — FY22 is one
short because its Resolution-A/Appropriation-Changes capital document wasn't found) + 37
transparency-resolution PDFs (14 + 14 + 9) = 48 files across `source/FY22/`,
`source/FY23/`, `source/FY24/` (including `transparency-resolutions/` subfolders),
roughly 50MB combined.
