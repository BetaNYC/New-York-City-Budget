# FY2020 PDF review: capital §254 supporting detail (no Terms & Conditions in `source/`)

**Report generated:** 2026-10-22 00:20 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** the PDF in `source/FY20/` (sha256 below), `data/capital/council_capital_awards.csv`
and `data/capital/omb_capital_budget_council_lines.csv` at `c9e57d4` (FY2020 rows from NYC Open Data
`t474-a92g`, published by the Council; no Council workbook was found for FY2020, `data/capital/README.md`).
**Status:** review build for GitHub #109 (epic #101). Nothing in `data/` was changed by this folder; the
stacked promotion PR writes `data/fy20/pdf/capital_sd/`.

The FY2020 twin of the capital half of
[`../2026-10-21-fy22-capital-terms-review/`](../2026-10-21-fy22-capital-terms-review/README.md), made with
the **same script** and a new per-year config. The folder is dated the day the FY2021/FY2020 work started
(2026-10-21). Every number here was printed by the script, or by the ad hoc comparisons named below, on
2026-10-21/22. Schedule C and the transparency resolutions are separate reviews.

**Only one of the two families exists for FY2020.** There is no FY2020 Terms & Conditions in
`source/FY20/`, so this folder has no `fy20_terms_*` files and `data/pdf_years.csv` gets no FY2020
`terms` row.

## What is here

| File | What it is |
|---|---|
| [`REVIEW.md`](REVIEW.md) | **For Noel.** The flagged rows, critical first, then by dollars, with page numbers and what to decide |
| [`ISSUE-LOG-DRAFT.md`](ISSUE-LOG-DRAFT.md) | Draft #109 issue-log comments, one per problem. Not posted |
| `data/fy20_capital_sd_projects.csv` | Part I: 1,663 rows, raw and clean side by side, page and bbox |
| `data/fy20_capital_sd_totals.csv` | All 24 printed `TOTALS FOR` lines, with the computed sums and `OK` / `FAIL` |
| `data/fy20_capital_sd_part3.csv`, `…_part3_orgs.csv` | Header only: this book has no Part III (kept so every year has the same files) |
| `data/fy20_capital_sd_pages.csv` | Triage, every page |
| `data/fy20_capital_sd_checks.txt`, `…_review.csv`, `…_ink.json` | Check output and the machine review queue (88 entries: 3 `critical`, 85 `warn`) |
| `data/fy20_capital_sd_review_decisions.csv` | Empty decisions file (header only) |

Review CSV columns are the FY2022 ones.

## The code

| File | Change |
|---|---|
| [`code/review_capital_sd.py`](../../code/review_capital_sd.py) | Three additions, each off unless the year's config or page map asks. **A book with Part I only:** when the page map has no Part II (or Part III) pages, C3 (or C4) says "this book prints no Part II (III); nothing to compare" instead of flagging all 179 DN rows as missing from Part II, or crashing on the missing Part III total. **Config `title_blank_line`:** names a row whose title cell holds an empty line (p.39 `E CN817`); its next title block is joined to it, with a warning. **Config `wb_full_id`:** C9 compares the full ID with its agency prefix, because FY2020's t474 rows keep the prefix and one ID number is used by several prefixes on one line at one amount (`MT CN001` / `TF CN001`, `HW CN905` / `P CN905`). Everything else is config, reusing existing switches (`extra_sub_ids`, `workbook_mojibake = "utf-8"`, `wb_pick_by_amount`, `[rotate] part1 = 90`) |
| `config/capital_sd/fy2020.toml` | New |
| [`code/test_review_fy20_capital_terms.py`](../../code/test_review_fy20_capital_terms.py) | 5 FY2020 tests, golden rows read off the rendered pages |

**FY2021–FY2027 output is byte-identical.** All research files of FY2022–FY2027 (both scripts) and
FY2021 (T&C) were rebuilt with this code and `git status` shows no change to any of them. A second FY2020
run gives the same files.

## Results

### Capital supporting detail (80 pp., sha256 `0820f439…93d4`)

`Supporting-Detail-for-the-FY-2020-Changes-to-the-Executive-Capital-Budget-Adopted-by-the-City-Council-Pursuant-to-Section-254-2.pdf`.
GPL Ghostscript 9.20 from PScript5 (a different export from FY2022–FY2027). **AES-128 encrypted (V4 R4,
/P −1324) with an empty user password:** it opens and its text extracts, as FY2024's did. **pp.2–79
carry /Rotate 90** (portrait boxes shown landscape); p.1 and p.80 are landscape boxes, upright.

**Page map** (all 80 pages agree). p.1 cover · **pp.2–79 Part I** ("Page 1 of 78" … "Page 78 of 78") ·
**p.80 summary**. **No contents page, no dividers, no Part II and no Part III**: this book is Part I
only, with the summary last. Header `PROJECT ID`. Fonts: Helvetica, Helvetica-Bold, Times-Bold (the
"I." mark); 4 spaces in MicrosoftSansSerif on p.39 (a later edit, below).

| Check | Result |
|---|---|
| Rows | Part I 1,663. No Part II or III |
| C1 every `TOTALS FOR` line | **24 / 24 tie** on count and all four FYs, including `TOTALS FOR ALL (1663 PROJECTS)`: $701,210,000 FY2020 and $5,000,000 FY2021 (one row, `P CN988` ORCHARD BEACH, FY2021 only) |
| C2 p.80 summary | Additions $701,210,000 = Part I. Additions − rescindments $46,210,000 = net $655,000,000. No list of the rescindments in this book |
| C3 | No Part II to compare. Part I has 179 rows on `DN` (non-city) lines, $111,014,000. **Two ID numbers printed twice:** `P CN967` (p.68 `P D019` Forest Park pathways $500,000; p.71 `PV DN01L` Universal Hip Hop Museum $2,000,000) and **`TF CN90`** (p.79, both `TF D005`, $200,000 each, two different projects) |
| C4 | No Part III |
| C5 two reads of each word | 27,501 agree; no page edited after export; 0 disagreements. One title block needed config: **p.39 `E CN817`** prints an empty line inside its title cell (below) |
| C6 every word in one field | 0 orphans. **3 rows print the borough in lower case, `r`** (Staten Island): `F CN003` p.48, `HW CN006` p.60, `PV NC037` p.73. Critical, kept as printed. `HD NC926` prints borough `C` (t474 too) |
| C7 rules | 71 / 71 matched |
| C8 ink coverage | **0 uncovered regions** on 80 pages. Self-test: hiding `AG CN001` (p.2) gives 91 regions |
| C9 Open Data `t474-a92g`, FY2020 | **1,660 / 1,660** t474 amounts match a Part I amount on (full ID, budget line, FY, amount), none left over. The PDF adds **`E CN817` $170,000** and **`E CN832` $300,000** (p.39), the two records t474 lost to broken rows. **t474's FY2020 total $700,740,000 + $170,000 + $300,000 = the PDF's $701,210,000**; FY2021 $5,000,000 on both sides. One PDF row is all zeros and is not in t474 (`PV NC013` BALLET HISPANICO, p.71). Borough 1,659 / 1,662 (the three `r`). Title 1,659 / 1,662. Sponsor 1,609 / 1,662; the 53 others are wording (REVIEW B3) |
| PDF vs OMB adopted capital budget (report only) | Part I by budget line against OMB `46m8-77gv`, adopted release 2019-07-09, FY2020: **184 / 191 PDF lines match.** 7 PDF lines are lower than OMB (`E D001` −$2,500,000, `HD D020` −$2,000,000, `HW D102` −$500,000, `P D020` −$450,000, `HW D104` −$250,000, `PV DN031` −$150,000, `PV D467` −$38,000), and OMB has 4 Council-series lines with no PDF row (`HL DN843` $1,000,000, `ED DN973` $300,000, `RE D024` $136,000, `PV DN176` $29,000): $7,353,000 in all. t474 has no amount the PDF lacks (C9: none left over), so this is OMB vs the Council, not a reading error |
| vs the retired `data/fy20/capital` CSV | Same 1,663 rows and (ID, budget line) keys; **every amount equal**; borough equal except the three `r` (it upper-cased them). It **dropped the printed comma after `SPEAKER` on 219 rows**, **moved a wrapped sponsor line into the title on 26 rows** and cut it from the sponsor (`PV NC943`: "BRONX DELEGATION, BLACK, LATINO AND ASIAN CAUCUS, WOMEN'S CAUCUS, VAN BRAMER" lost from the sponsor; `PW NC907` lost PERKINS), dropped a title's trailing comma on 6 rows, and put spaces where the page shows none in the two edited titles (`E CN817` "ATP ARK", `E CN832`; below). Same swapped column names as FY2022/FY2023 (`budget_line` holds the ID) |

## What FY2020 does that FY2022 does not

- **Part I only**, summary last, no contents or dividers; encrypted; rotated; a Ghostscript export.
- **ID numbers outside the usual shape:** `E CNA02`–`CNA09` (p.46), `HL NC02` (p.54), `TF CN90` (p.79,
  twice). Listed in config `extra_sub_ids`.
- **One edit after export, p.39:** four spaces typed in MicrosoftSansSerif. One sits on a line of its own
  inside `E CN817`'s title (an empty line), two sit on top of letters, so the page shows
  `ACCESSIBLEBATHROOMS ATPARK` (no visible gap; kept as printed), and one does the same to `E CN832`
  (`(K003)GYMNASIUM`). These are the same two records t474 lost to broken rows.
- **The ID's agency prefix matters:** `MT CN001` and `TF CN001` are both $200,000 on `TF D005`.
- Lower-case `r` boroughs (3), a `C` borough, an all-zero row, and typos as printed (`ACQUISTION`,
  `BROOKYN`, `EXPANSIO`).
- **The PDF spells `AMPREY-SAMUEL`** on 31 rows (t474 and the Council: Ampry-Samuel), as FY2022.

## How to redo it

```
.venv/bin/python code/review_capital_sd.py --fy 2020          # --no-ink skips C7/C8
.venv/bin/python code/review_capital_sd.py --fy 2020 --selftest-ink --out /tmp/x   # C8 must fire on p.2
.venv/bin/python -m pytest code/test_review_fy20_capital_terms.py
```

Same environment as FY2022 (pdfplumber 0.11.10, pypdfium2 5.14.0, opencv-python-headless 4.14.0.94,
numpy 2.5.4, Python 3.14.8). The comparisons with the retired capital CSV and with OMB by budget line
were run ad hoc; their numbers are above.

## Not done

- **Terms & Conditions:** none in `source/FY20/`.
- **OCR audit (PLAN stage 10).** Not run: the PDF is born-digital with 0 uncovered ink.
- **DATA-ANOMALIES** and **`data/capital/`** are not edited. The proposed entry is below.
- Suggested decisions (`code/build_review_suggestions.py`) and `mcp/scripts/pdf-families.mjs` do not
  list FY2020 yet (recipe Step 6, the integrator's).

## Proposed DATA-ANOMALIES entry

Not applied (parallel sessions edit that file; the integrator numbers it):

> **§NN. FY2020 capital supporting detail, re-read from the PDF (GitHub #109).**
> `research/2026-10-21-fy20-capital-terms-review/`. The book is Part I only (no Part II or III),
> encrypted with an empty password and rotated. 24 / 24 printed totals tie (1,663 projects,
> $701,210,000 FY2020, $5,000,000 FY2021). Part I equals NYC Open Data `t474-a92g` on all 1,660 of its
> amounts and adds the two t474 lost to broken records (`E CN817` $170,000, `E CN832` $300,000), so
> t474's $700,740,000 becomes the PDF's total. Against OMB's adopted release, 184 / 191 lines match
> and OMB carries $7,353,000 more on 11 lines. The PDF prints three lower-case `r` boroughs, IDs outside
> the usual shape (`CNA02`, `NC02`, `CN90`, the last twice), an all-zero row, and `AMPREY-SAMUEL` (31
> rows). The retired capital CSV drops the comma after `SPEAKER` (219 rows) and moves wrapped sponsors
> into titles (26). FY2020 has no Terms & Conditions in `source/`.
