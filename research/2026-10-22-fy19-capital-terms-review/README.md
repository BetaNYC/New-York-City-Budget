# FY2019 PDF review: capital §254 supporting detail (no Terms & Conditions in `source/`)

**Report generated:** 2026-10-22 01:30 EDT. Prepared by BetaNYC with AI assistance (Claude Code).
**Data current as of:** the PDF in `source/FY19/` (sha256 below), `data/capital/council_capital_awards.csv`
and `data/capital/omb_capital_budget_council_lines.csv` at `5d89af1` (FY2019 rows from NYC Open Data
`t474-a92g`, published by the Council; no Council workbook was found for FY2019, `data/capital/README.md`).
**Status:** review build for GitHub #110 (epic #101). Nothing in `data/` was changed by this folder; the
stacked promotion PR writes `data/fy19/pdf/capital_sd/`.

The FY2019 twin of the capital half of
[`../2026-10-21-fy20-capital-terms-review/`](../2026-10-21-fy20-capital-terms-review/README.md), made with
the **same script** and a new per-year config. Every number here was printed by the script, or by the ad hoc
OMB comparison named below, on 2026-10-22. Schedule C and the transparency resolutions are separate
reviews.

**Only one of the two families exists for FY2019.** There is no FY2019 Terms & Conditions in
`source/FY19/`, so this folder has no `fy19_terms_*` files and `data/pdf_years.csv` gets no FY2019 `terms`
row.

## What is here

| File | What it is |
|---|---|
| [`REVIEW.md`](REVIEW.md) | **For Noel.** The flagged rows, critical first, then by dollars, with page numbers and what to decide |
| [`ISSUE-LOG-DRAFT.md`](ISSUE-LOG-DRAFT.md) | Draft #110 issue-log comments, one per problem. Not posted |
| `data/fy19_capital_sd_projects.csv` | 1,625 rows, raw and clean side by side, page and bbox. Three columns only this year has: `council_district` (the CD codes as printed), `description`, `description_raw` (the DESC column) |
| `data/fy19_capital_sd_totals.csv` | The one printed total row (p.54), with the computed sums and `OK` |
| `data/fy19_capital_sd_part3.csv`, `…_part3_orgs.csv` | Header only: this book has no Part III (kept so every year has the same files) |
| `data/fy19_capital_sd_pages.csv` | Triage, every page |
| `data/fy19_capital_sd_checks.txt`, `…_review.csv`, `…_ink.json` | Check output and the machine review queue (32 entries: 3 `critical`, 29 `warn`) |
| `data/fy19_capital_sd_review_decisions.csv` | Empty decisions file (header only) |

Review CSV columns are the FY2020 ones.

## The code

| File | Change |
|---|---|
| [`code/review_capital_sd.py`](../../code/review_capital_sd.py) | **A second reader, for an Excel print (config `layout = "grid"`).** Every other year is a Word table printed without rules; FY2019 draws every cell border. `parse_grid_page()` reads rows from the drawn grid: a row is the band between two horizontal rules, a field is the column between two vertical rules, named by the header word inside it (config `[grid] header`). The second read is the content stream (Excel writes row by row), as for the Word books. It also reads the one unlabelled total row under the grid, and the **Key to CD** (pp.54–55), which turns the CD codes into names (`apply_cd_key()`). C7 also compares the column borders with the pixels in this mode. Smaller, off unless asked: C1 accepts a total with no printed count (amounts only); C2 says "no summary page" when the page map has none; C9 also compares the CD codes and the description (grid only). Everything else is config (`extra_sub_ids`, `wb_full_id`, `workbook_mojibake = "utf-8"`) |
| `config/capital_sd/fy2019.toml` | New |
| [`code/test_review_fy19_capital_terms.py`](../../code/test_review_fy19_capital_terms.py) | 4 FY2019 tests, golden rows read off the rendered pages |

**FY2020–FY2027 output is byte-identical.** All capital research files of FY2020 and FY2022–FY2027 were
rebuilt with this code and `git status` shows no change to any of them (FY2021 has no capital book). A
second FY2019 run gives the same files.

## Results

### Capital supporting detail (55 pp., sha256 `afc334a4…418c`)

`Capital-Final-Upload.pdf`, "Supporting Detail to the Fiscal 2019 Changes to the Executive Capital Budget
(Council Projects Only)". Microsoft Excel 2016; **not encrypted; no /Rotate**; all 55 pages 792 × 612.
Fonts: Calibri, Calibri-Bold (the grid); ArialMT, Arial-BoldMT (the Key to CD only).

**A different kind of book from every other year.** It is the Council's database printed from Excel:
`PROJECT, POLBORO, NEWPROJECT, CD, TITLE, DESC, FY19, FY20, FY21, FY22`, the same columns as
`t474-a92g`. **No cover, contents, dividers, agency headings, `TOTALS FOR` lines, Part II, Part III or
summary page.** pp.1–54 are one table sorted by ID; one bold row under the grid on p.54 prints the four
column totals with **no label and no project count**; the **Key to CD** (p.54 from y = 167, and p.55)
names the 64 codes. The sponsor is printed as **council-district codes**, not names.

| Check | Result |
|---|---|
| Rows | **1,625** (one per ruled row with an ID). 221 rows list more than one CD code |
| C1 the total row | **1 / 1 ties on all four FYs**: FY2019 **$614,910,000**, FY2020 **$15,900,000**, FY2021 and FY2022 `-` (zero). The FY2019 total is written as two touching pieces, `6` and `14,910,000`; read as one. **It prints no project count, so only the amounts are checked** (the count is `-` in the totals file) |
| C2 summary | **None printed.** No additions / rescindments / net to check |
| C3 | No Part II. Part I has 161 rows on `DN` (non-city) lines, $98,592,000. **Six ID numbers printed twice:** `LB CN001`–`LB CN006`, each once on `LB D104` (Brooklyn Public Library) and once on `LN D008` (New York Public Library), pp.40–41. t474 has all twelve the same way |
| C4 | No Part III |
| C5 two reads of each word | **36,308 agree, 0 disagree**, 0 written out of row order |
| C6 every word in one cell | 0 orphans, 0 words left over. **3 rows print the borough in lower case, `k`** (Brooklyn), all CD 41 (Ampry-Samuel): `E CN161` p.6, `E CN227` p.8, `E CN403` p.12. Critical, kept as printed. 4 dashes that close a title run 0.5–0.7 pt over the title cell's right border (warn) |
| Key to CD | 64 codes, 00–51 (the Speaker and 51 members) and 88–99 (caucuses, delegations, `Citywide`, `Technical Adjustments`). Every code a row prints is in the key; 90 (LGBT Caucus), 96 (Citywide) and 99 (Technical Adjustments) are used by no row. **p.55 prints `Caucus Black, Latino and Asian97`**: the name runs into the district with no gap; split at the digits |
| C7 rules | Horizontal: 1,801 / 1,802 matched. Excel draws the header's bottom border twice on 53 pages (counted once); on p.55 the key's top border lies on the header's (1 warn). **Column borders: 599 / 599** |
| C8 ink coverage | **0 uncovered regions** on 55 pages. Self-test: hiding `AG CN002` (p.1) gives 74 regions |
| C9 Open Data `t474-a92g`, FY2019 | **1,628 / 1,628** t474 amounts match a PDF amount on (full ID, budget line, FY, amount), none left over either side (1,622 FY2019, 6 FY2020). Title 1,625 / 1,625. **CD codes 1,624 / 1,625** (t474 writes them run together: `00, 37` → 37). Sponsor 1,617 / 1,625: 7 are how a group is named (below), 1 is real: **`HW CN030`** (p.40, $500,000, "DOT REPAVING IN DISTRICT 31") prints CD **49, 00** (Rose, Speaker); t474 has 3100 (Richards, Speaker). Description 1,621 / 1,625: 4 rows print an empty DESC where t474 has `NA`. Borough 1,622 / 1,625 (the three `k`) |
| PDF vs OMB adopted capital budget (report only) | By budget line against OMB `46m8-77gv`, adopted release 2018-07-13, FY2019 and FY2020: **165 / 176 lines match.** OMB is higher on 10 (`HW D101` +$4,000,000, `P D019` +$3,000,000, `P D017` +$2,600,000, `PV D467` +$2,500,000, `HD D021` +$1,500,000, `E D001` +$500,000, `P D018` +$400,000, `PW D007` +$350,000, `T D005` +$250,000, `PO D185` +$60,000) and has 1 line with no PDF row (`LB D107` $300,000): $15,460,000 in all. The same numbers as `data/capital/RECONCILIATION.md` §3 for t474, as they must be (C9). This is OMB vs the Council, not a reading error |
| vs a retired `data/fy19/capital` CSV | **There is none** (`data/fy19/` has no capital folder) |

**How the sponsor is filled.** The PDF prints codes; `sponsor_raw` keeps them as printed (`00, 37`). `sponsor`
is the book's own Key to CD applied to them, in the printed order: a member by the key's LASTNAME cell
(`Espinal`, `Diaz Sr.`, `Van Bramer`), as t474 writes them; a group by its LASTNAME and FIRSTNAME cells as
printed (`Caucus Progressive`, `Caucus Black, Latino and Asian`, `Bronx Delegation`). t474 writes
`Progressive Caucus` and `Black, Latino and Asian Caucus`, which is where 7 of the 8 sponsor warnings come
from. Note that `Caucus Black, Latino and Asian` holds a comma, so a sponsor list cannot be split on
commas alone; use `council_district` to count sponsors. (REVIEW D1.)

## What FY2019 does that no other year does

- **An Excel print with every cell ruled.** Read from its vector grid, checked against the image grid.
- **CD codes instead of sponsor names**, and a key to them on the last two pages, in another font.
- **A DESC column**: every description opens with `--` (dropped in `description`, kept in
  `description_raw`); 4 are empty.
- **One total row with no label and no count**, no agency totals, no summary page.
- **Excel's zero is `-`.** Read as 0; `fyNNNN_printed` keeps `-`.
- Lower-case `k` boroughs (3), a two-digit ID (`HL NC57`, p.36), six IDs reused across the two library
  systems, and typos as printed (`SUPPMENTAL`, `CONFGURATION`, `EASIDE`, `SURVEILLIANCE`).

## How to redo it

```
.venv/bin/python code/review_capital_sd.py --fy 2019          # --no-ink skips C7/C8
.venv/bin/python code/review_capital_sd.py --fy 2019 --selftest-ink --out /tmp/x   # C8 must fire on p.1
.venv/bin/python -m pytest code/test_review_fy19_capital_terms.py
```

Same environment as FY2020 (pdfplumber 0.11.10, pypdfium2 5.14.0, opencv-python-headless 4.14.0.94,
numpy 2.5.4, Python 3.14.8). The comparison with OMB by budget line was run ad hoc (`budget_line_norm`,
release `20180713`, year 1 and year 2); its numbers are above.

## What the checks cannot prove

- **The total row has no count.** If a row were dropped and another row's amount doubled, C1 would not see
  it. C5 (two reads), C6 (every word in one cell), C8 (no ink left over) and C9 (every t474 amount, both
  ways) close that gap.
- **The sponsor names are derived** from the book's own key, not printed on the row.
- **t474 was published by the Council, likely from the same database.** C9 agreeing shows the PDF was read
  right; it does not show the database was right (`HW CN030` is the one place they disagree).

## Not done

- **Terms & Conditions:** none in `source/FY19/`.
- **OCR audit (PLAN stage 10).** Not run: the PDF is born-digital with 0 uncovered ink.
- **DATA-ANOMALIES** and **`data/capital/`** are not edited. The proposed entry is below.
- Suggested decisions (`code/build_review_suggestions.py`) and `mcp/scripts/pdf-families.mjs` do not list
  FY2019 yet (recipe Step 6, the integrator's).

## Proposed DATA-ANOMALIES entry

Not applied (parallel sessions edit that file; the integrator numbers it):

> **§NN. FY2019 capital supporting detail, re-read from the PDF (GitHub #110).**
> `research/2026-10-22-fy19-capital-terms-review/`. The book is the Council's database printed from Excel
> (every cell ruled; no agency totals, no Part II or III, no summary page), read from its vector grid
> and checked against the image grid. 1,625 rows; its one total row (no label, no count) ties on all four
> years: $614,910,000 FY2019, $15,900,000 FY2020. It equals NYC Open Data `t474-a92g` on all 1,628
> amounts and all 1,625 titles. Sponsors are printed as council-district codes with a key on pp.54–55;
> one row disagrees with t474 (`HW CN030`, p.40: CD 49 Rose in the PDF, 31 Richards in t474, title "DOT
> REPAVING IN DISTRICT 31"). The PDF prints three lower-case `k` boroughs, a two-digit ID (`HL NC57`) and
> six IDs used twice (`LB CN001`–`LB CN006`). Against OMB's adopted release, 165 / 176 lines match and
> OMB carries $15,460,000 more on 11 lines. FY2019 has no Terms & Conditions in `source/`.
