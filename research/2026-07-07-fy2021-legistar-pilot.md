# Pilot: FY2021 historical sourcing (Legistar + council.nyc.gov)

**Report generated:** 2026-07-07
**Data current as of:** 2026-07-07
**Status:** Pilot complete. 11 of 11 attempted documents found and downloaded (Schedule C,
Terms & Conditions, Capital §254 Resolution A, 8 Transparency Resolutions). One
document sub-type (Capital Project Detail / Supporting Detail Book) not confirmed
found or absent — genuinely unresolved, not exhaustively searched.

## Context

This is one of two parallel one-year pilots (this doc = FY2021; a sibling agent
independently ran FY2008) commissioned to produce real per-year cost/feasibility
signal before committing to a full FY2008–FY2021 historical sourcing pass across
`New-York-City-Budget`. Per instructions, this pass did not read or coordinate with
the FY2008 agent's output file. Branch: `research/fy22-24-schedule-c-gap` (no
commits made, per instructions).

## Headline finding that changes the cost model

**The scoping assumption that "council.nyc.gov's own budget-archive pages do NOT go
back before ~FY2022" is wrong for FY2021.** `council.nyc.gov/budget/fy2021/` is a
live, complete archive page with the same structure as the FY2022–2027 pages
already in this repo: a "Discretionary Funding" section with Schedule C, a "Terms
and Conditions" section, and a "Transparency Resolutions" section with all 8 of that
cycle's resolutions individually linked and dated. This single page supplied 3 of
this pilot's 4 document types (Schedule C, Terms & Conditions, all 8 Transparency
Resolutions) in about 4 tool calls total (`WebFetch` + a confirming `Chrome`
page-text pull) — dramatically cheaper than the Legistar full-text-search technique
the FY22–24 pass had to use for everything.

**Practical implication for the remaining years:** before assuming Legistar is
required, check `council.nyc.gov/budget/fy{YYYY}/` directly first. It is unknown how
far back this pattern holds (FY2021 confirmed; FY2020, FY2019, etc. not checked —
out of scope for this pilot). Establishing that floor is a cheap, high-value next
step for whoever scopes the remaining years.

## Source status table

| Document | Found? | Local path | Source | Pages |
|---|---|---|---|---|
| Schedule C | Yes | `source/FY21/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf` | council.nyc.gov | 343 |
| Terms & Conditions | Yes | `source/FY21/Fiscal-2021-Terms-and-Conditions.pdf` | council.nyc.gov | 16 |
| Capital §254, Resolution A (schedule of changes) | Yes | `source/FY21/FY21-Sec254-Capital-ResoA-M231-Res1362-Res1363.pdf` | Legistar attachment | 73 |
| Capital §254, Capital Project Detail / Supporting Detail Book | Not found this pass | — | — | — |
| Transparency Resolutions (8) | Yes, all 8 | `source/FY21/transparency-resolutions/` | council.nyc.gov | 126, 65, 47, 23, 40, 40, 38, 25 |

Total: 11 files, ~11 MB, `source/FY21/`.

## How each was found

### Schedule C — found in ~2 tool calls (WebFetch)

`council.nyc.gov/budget/fy2021/` → "Discretionary Funding" section → single link
"Schedule C (PDF)" →
`https://council.nyc.gov/budget/wp-content/uploads/sites/54/2020/06/Fiscal-2021-Schedule-C-Cover-REPORT-Final.pdf`.
Downloaded via `curl`, validated with `file` (valid PDF, 343 pages via `pypdf`).

**Format check:** ran `code/parse_schedule_c.py` unmodified in a throwaway venv
(`pypdf` 6.14.2 + `pdfplumber`, mirroring the FY22–24 pass's method). **Reconciles
25/26 categories exact**, GRAND TOTAL $304,268,931 (one category, Youth Services,
diffs by $0 net — same class of in-source arithmetic quirk already documented for
FY22/24/25/26, not a parser fault). 1,800 award rows, $201.5M; appendix A (aging)
514 rows, appendix B (local) 2,902 rows, appendix C (youth) 894 rows. **No code
changes needed** — this is one of the cleanest reconciliations across all years
checked to date, on par with FY2023.

### Terms & Conditions — found in ~2 tool calls (WebFetch)

Same `council.nyc.gov/budget/fy2021/` page → "Terms and Conditions" section →
`Fiscal-2021-Terms-and-Conditions-PDF.pdf`. Downloaded, validated (16 pages).

**Format check:** `code/parse_terms.py` run unmodified produces **0 conditions**
— the same deviation already documented and scoped for FY2022–2024. Confirmed by
direct text inspection: no leading item numbers, each condition opens with `Agency
Name (Code)` (e.g. "Administration for Children's Services (068)"). Counted 47
agency-code headers + 3 bare "Capital Budget" headers (4 "Budget Line" sub-entries)
across the 16 pages — roughly 50 condition items total. The parser-variant fix
already scoped in the FY22–24 doc (HEADER regex without the leading-number
requirement + synthetic sequential item_number + a second bare-`Capital Budget`
header pattern) applies unchanged to FY2021; no FY2021-specific new work.

**Answering the task's investigation question:** for FY2021, Terms & Conditions
**does** exist as a standalone, separately-published document — not an exhibit
folded into the budget-adoption resolution, and not absent. It was simply on
council.nyc.gov rather than Legistar.

### Capital §254 — found in ~10 tool calls (mixed MCP + Chrome), moderate effort

council.nyc.gov's FY2021 page has **no** Section 254 / capital-changes document
(confirmed by inspecting the full page text; the only capital-adjacent link is a
different document, "Capital Budget Fact Sheet," part of the Financial Plan
Overview, not the Resolution A/B changes package). This matches FY2022's pattern
(council.nyc.gov also lacked it there) more than FY2023/24's (which had it).

Used the FY2022 technique exactly as scoped: `nyc-council-mcp`'s
`search_legislation_live` for the phrase "CAPITAL PROGRAM FOR THE ENSUING THREE
YEARS" via the Legistar web UI (not the live-API tool, which is last-modified-sorted
and would have missed a 2020 record) returned one Resolution A/B pair per fiscal
year back to 1998. FY2021's pair:

- **`Res 1362-2020`** — Resolution A (schedule of changes), title: "...BE AND THE
  SAME ARE HEREBY APPROVED IN ACCORDANCE WITH THE FOLLOWING SCHEDULE OF CHANGES
  (RESOLUTION A)." Adopted 6/30/2020, sponsor Daniel Dromm, Committee on Finance.
- **`Res 1363-2020`** — Resolution B (total-amounts adoption), same adoption date.
  Not the document sought (per the FY22 precedent, Resolution A carries the actual
  changes package as an attachment; Resolution B does not).

Confirmed via `nyc-council-mcp get_bill` (fast, reliable) rather than browser
search — both matters share `MatterEXText4: "M 0231-2020"`, the Mayor's Message
cross-reference, confirming the pairing independent of file-number adjacency.

**Getting the PDF:** browsed `Res 1362-2020`'s own Legistar detail page (via
Claude in Chrome). Attachment #5, "M 231 & Res 1362 & Res 1363 - Fiscal 2021
Capital Budget & Accompanying Resolutions," is the document — same naming pattern
as FY2022's attachment. Downloaded from Legistar's `View.ashx` endpoint. Opens: "The
City of New York / Fiscal Year 2021 Changes To the Executive Capital Budget Adopted
by the City Council / Pursuant to Section 254 of the City Charter" — same title
convention as FY22/23/24.

**Format check:** ran `code/parse_capital_fy25.py` unmodified. **Parses cleanly**:
161 change blocks across 25 agencies, $3,449,337,177 total FY(CN) change amount
(label reads "FY2025" in the parser's own output string — a cosmetic artifact of
the script, not a bug; the year is inferred from the `--prefix` arg the caller
supplies, not parsed from content). No `$0`-amount tokenization bug like FY2022's;
behaves like FY2023/24 (works out of the box, `NOT RECONCILABLE` is the expected
status for this document type — it has no printed subtotals to check against, same
as FY25).

**Capital Project Detail / Supporting Detail Book type — not found this pass.**
Not on council.nyc.gov's FY2021 page. Checked Resolution A's (`Res 1362-2020`)
attachment list directly — only one capital-changes PDF is attached there, not a
second Supporting Detail Book. Did **not** exhaustively check Resolution B's
(`Res 1363-2020`) attachment list — repeated browser-automation flakiness (see
Tooling notes below) made each additional Legistar detail-page visit costly, and
the pilot's effort budget was prioritized toward closing out the other three
document types. This is a genuine "not resolved" gap, not a confirmed absence —
distinct from Terms & Conditions, which *was* confirmively resolved as "exists,
found."

### Transparency Resolutions — found in ~2 tool calls (WebFetch), all 8

Same council.nyc.gov page, "Transparency Resolutions" section, 8 individually
dated and linked PDFs spanning August 27, 2020 – June 30, 2021:

`Transparency-Reso-01-2020-08-27.pdf` … `Transparency-Reso-08-2021-06-30.pdf`.

All downloaded and validated (page counts: 126, 65, 47, 23, 40, 40, 38, 25).
8 resolutions is fewer than FY2022/23's 14 each — closer to FY2024's 9, suggesting
the higher-frequency (roughly monthly, sometimes twice-monthly) cadence seen in
FY2022/23 may not extend as far back as FY2021, or FY2021's pandemic-disrupted
Council calendar reduced the count. Not confirmed either way; noted as an
observation only.

**Cross-check via Legistar (redundant, but confirms the practice and its
FY-tagging mechanics):** the Legistar resolution series carrying the generic title
"Resolution approving the new designation and changes in the designation of certain
organizations to receive funding in the Expense Budget" (title stopped naming the
fiscal year explicitly sometime after ~2017) is confirmed to **be** this
Transparency Resolution mechanism, not a separate "Schedule C" filing. A full-text
phrase search for `"Fiscal 2021 Expense Budget"` on the Legistar web UI (36 hits,
spanning FY2021 through incidental later references) identified **`Res 1394-2020`**
(adopted 2020-08-27) as the oldest/first resolution referencing Fiscal 2021 — this
matches Transparency Resolution #1's date on council.nyc.gov exactly, confirming
the two sources describe the same underlying legislative record. A separate,
earlier resolution in the same series, `Res 1352-2020` (also adopted 6/30/2020,
same day as the FY2021 budget), was initially mistaken for an FY2021 record but its
full text shows it is a **Fiscal 2020 closeout** ("Whereas...the City Council
adopted the expense budget for fiscal year 2020...") — a useful negative finding:
**do not assume the resolution filed on budget-adoption day is that year's first
designation resolution; check the Whereas-clause fiscal year, not just the
adoption date.**

## Format notes summary (for `software-engineer`, once source-gathering across
years is complete)

| Document | FY2021 result | Deviation class |
|---|---|---|
| Schedule C | 25/26 categories exact, unmodified parser | None — same as FY23/25/26 |
| Terms & Conditions | 0 rows, unmodified parser | Same shared deviation as FY22–24 (no leading item numbers); same fix applies |
| Capital §254 Resolution A | 161 blocks, $3.449B, unmodified parser | None — same as FY23/24 |
| Capital §254 Capital Project Detail | Not found | N/A — could not test |
| Transparency Resolutions | Not test-parsed this pass (out of scope; format already proven for FY22–24 same-title documents) | Presumed none, not verified |

## Tooling notes (cost signal for remaining years)

- **A second, uncoordinated agent was operating in the same shared "Office Machine
  Chrome" browser instance during this session** (visible via shared tab state and
  overlapping Legistar searches for FY2008-era records). Opening a dedicated new
  tab (`tabs_create_mcp`) and, once discovered, explicitly selecting the correct
  browser via `select_browser` (three Chrome instances were connected; the task
  brief named "Office Machine Chrome" specifically) resolved cross-contamination.
  **This is a real, non-trivial cost for parallelized pilots**: an unknown number
  of early tool calls in this session were wasted on stale/contaminated page state
  before the isolation was diagnosed and fixed. A future parallel run should
  either request separate browser connections up front or serialize the
  browser-dependent steps.
- **Independent of the above, `legistar.council.nyc.gov`'s search form has a
  persistent race condition** under automated (non-human-speed) interaction: a
  `click → type` sequence issued in rapid succession frequently loses the typed
  text (the field renders empty, or an async postback clears it, or a phantom
  autocomplete-style value from browser history/a previous search silently
  replaces it). The reliable pattern found through trial: **click, then type, then
  screenshot to confirm the value stuck, then click the search button as a fully
  separate step** — batching click+type+click in one `browser_batch` call failed
  more often than not. Individual link clicks on the results grid also frequently
  needed to be issued twice. This roughly doubled the number of tool calls needed
  for every Legistar web-UI interaction in this pass.
- Given the above, **`nyc-council-mcp`'s `get_bill` tool (by exact `Res
  NNNN-YYYY` file number) was far more reliable and faster than the web UI** for
  anything beyond full-text discovery — used it to confirm dates, titles, and the
  Resolution A/B pairing (via the shared `M 0231-2020` cross-reference field)
  without touching the browser at all.

## Effort estimate (rough tool-call counts, this pilot)

- Schedule C: ~2 calls (WebFetch discovery + curl download)
- Terms & Conditions: ~1 call (same WebFetch pull as Schedule C, separate curl)
- Transparency Resolutions (all 8): ~3 calls total (one WebFetch page-text pull
  supplied all 8 URLs; one batch curl download)
- Capital §254 Resolution A: roughly 15–20 tool calls — Legistar phrase search,
  `get_bill` calls to confirm the A/B pair, several retries of the Legistar web UI
  race condition to reach the attachment list, `read_page` to extract the
  attachment href, curl download
- Capital §254 Capital Project Detail: ~5 calls spent, inconclusive, abandoned
  short of a confirmed finding
- Browser-isolation diagnosis (one-time, session-specific): ~10 calls, would not
  recur in a non-parallel run

**Total this session: roughly 45–55 tool calls**, but a large fraction (the
browser-isolation diagnosis, and much of the Legistar race-condition retrying) is
either non-recurring (isolation) or would shrink significantly with the
`get_bill`-first, browser-only-for-attachments discipline this pass converged on
late. A repeat of this exact FY (or a similar year where council.nyc.gov's archive
page exists) using the now-known-good method — check council.nyc.gov first,
`get_bill` for Legistar confirmation, browser only for the final attachment
click-through — would likely run **20–25 tool calls**, well under half this
session's actual count.

## Feasibility verdict

**FY2021 is fully feasible and comparatively cheap** — more so than the FY22–24
gap-fill pass, because 3 of 4 document types came from council.nyc.gov (a source
the scoping doc wrongly assumed didn't exist for this year) rather than requiring
the heavier Legistar attachment-hunting technique. Schedule C and Capital §254
Resolution A both parse cleanly with zero code changes. Terms & Conditions needs
the already-scoped parser variant (no new work). The one open gap — Capital
Project Detail / Supporting Detail Book — is a genuine "not resolved," not a
confirmed absence; a future pass should check Resolution B's attachment list and/or
try a targeted Legistar text search for "Supporting Detail Book" or "Capital
Project Detail" phrasing before concluding it doesn't exist for this year.

**Recommendation for the remaining FY2008–FY2020 span:** check
`council.nyc.gov/budget/fy{YYYY}/` for each candidate year before assuming Legistar
attachment-hunting is required — this alone could substantially cut the cost
estimate for whichever years the pattern extends to.
