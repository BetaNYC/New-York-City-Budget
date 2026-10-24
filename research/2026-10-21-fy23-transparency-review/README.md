# FY2023 transparency resolutions, checked from the PDFs (#106)

**Report generated:** 2026-10-21 22:20 EDT. Prepared by BetaNYC with AI assistance.
**Data current as of:** the 14 PDFs in `source/FY23/transparency-resolutions/` (697 pages; hashes
in `config/transparency/fy2023.toml`); expense disclosure as committed in
`data/fyNN/expense_disclosure/` (FY2023 workbook sheet "FY23 (07-11-2023)", FY2022 "FY22 (07-11-2023)",
FY2021 "FY21 (06-23-2023)", FY2020 "FY20 (06-16-2022)"); resolution numbers and adoption dates from
`research/2026-07-07-legistar-links-fy21-27.md` and `data/combined/legistar_crosswalk.csv` (read
from Legistar on 2026-07-07, not re-queried); code at this branch's commit.
**Status:** checked, review not started. Every check passes or is a named, listed exception.
Noel has not signed off the review file.

Part of #106 (epic #101). This folder is the review record. The tables are promoted to
`data/fy23/pdf/transparency/` by a separate PR. FY2023 Schedule C and capital/terms are other
sessions' work. The method is FY2026's (`research/2026-10-21-fy26-transparency-review/`) with the
FY2025 and FY2024 additions; this README says what differs.

## What these PDFs are

Same layout as FY2024–FY2026: one resolution per PDF, the Committee on Finance report first (it
prints the date, "This Resolution, dated July 14, 2022"), then Excel charts, one landscape table
per page. Reso 01–03 have long reports (6–7 pages: they describe each of 49–56 charts); the rest
have 1–2. No page carries /Rotate, and none prints "Charts 1 through N". The year is the biggest
so far: 14 resolutions, 656 chart pages, 502 charts.

## Results

| What | Result |
|---|---|
| Rows | **8,424** (6,348 designations, 1,634 rescissions, 442 purpose-of-funds rows) from 502 charts on 656 chart pages. Budget years: 2023 7,857 · 2022 378 · 2021 183 · 2020 6 |
| Printed totals | **None to tie.** 0 money amounts outside the tables (T15), and no resolution prints a chart count. The "Page n" labels count every chart page (1..n on all 14; 4 pages print none, below) |
| Image grid (independent) | **8,424 / 8,424** rows agree on every field |
| Ink coverage | **0 regions** (202 loose px of 282 million). Self-test on Reso 01 p.7 passes: hiding one row, or one letter, makes the check fire |
| Anchor census | 8,424 EIN-shaped words = 8,424 rows with an EIN, page by page; every row has an EIN and a readable amount. 4 drawn rows print nothing and are counted, not kept (below) |
| Sign vs colour | 1,855 amounts in parentheses, all red |
| Characters | 989,989 non-space; 0 in a table but in no cell; 13 hidden (4 runs, each in the review file) |
| Dates | All 14 print their date and it matches Legistar and the filename |
| Numbers | All 14 from Legistar (Res 0255-2022 .. Res 0705-2023) |
| Disclosure (report only) | FY2023: 5,525 of 6,050 organization designations ($200.9M) are in the disclosure on (EIN, amount); 403 of the rest were taken back later |
| Old CSV (`data/fy23/transparency-resolutions/`) | Every one of its 8,354 rows is here. It missed 70: 61 EINs printed without a hyphen and 9 ordinary rows (list in `data/fy23_tr_retired_csv_compare.csv`) |
| Review file | **45 rows** (18 critical, 27 warn), largest $100,000 (`REVIEW.md`) |

### Per resolution

"Orgs +" / "Orgs −" are rows to and from organizations; "agency side" is the City-EIN row with no
member that parks money in, or takes it from, an agency pool.

| # | Res. | Adopted | Rows | Charts | Orgs + (n, $) | Orgs − (n, $) | Agency side net | Purpose rows | "Speaker" rows |
|---:|---|---|---:|---:|---|---|---:|---:|---:|
| 1 | 0255-2022 | 2022-07-14 | 1,782 | 56 | 1,487, $66,795,010 | 174, −$2,572,721 | −$64,040,389 | 62 | 26 |
| 2 | 0288-2022 | 2022-08-11 | 1,752 | 49 | 1,545, $58,159,201 | 122, −$3,092,700 | −$55,066,501 | 24 | 13 |
| 3 | 0327-2022 | 2022-09-29 | 1,569 | 55 | 1,320, $30,274,080 | 155, −$4,484,871 | −$25,373,209 | 26 | 31 |
| 4 | 0363-2022 | 2022-10-27 | 815 | 47 | 622, $20,908,624 | 133, −$3,665,755 | −$17,242,869 | 10 | 9 |
| 5 | 0388-2022 | 2022-11-22 | 428 | 38 | 284, $6,797,559 | 88, −$1,595,128 | −$5,202,431 | 24 | 10 |
| 6 | 0440-2022 | 2022-12-21 | 435 | 41 | 276, $6,993,835 | 77, −$1,861,536 | −$5,132,299 | 46 | 15 |
| 7 | 0457-2023 | 2023-01-19 | 202 | 30 | 123, $4,709,750 | 42, −$948,231 | +$1,238,481 | 10 | 2 |
| 8 | 0472-2023 | 2023-02-02 | 561 | 41 | 216, $16,789,930 | 194, −$16,514,930 | −$275,000 | 140 | 32 |
| 9 | 0502-2023 | 2023-02-16 | 144 | 31 | 72, $2,383,270 | 50, −$1,129,398 | −$1,253,872 | 10 | 0 |
| 10 | 0508-2023 | 2023-03-02 | 256 | 29 | 138, $11,011,985 | 105, −$9,771,985 | −$1,240,000 | 10 | 16 |
| 11 | 0530-2023 | 2023-03-16 | 137 | 17 | 56, $1,153,000 | 40, −$683,000 | −$470,000 | 30 | 11 |
| 12 | 0575-2023 | 2023-04-27 | 208 | 37 | 87, $2,435,627 | 82, −$2,425,327 | −$10,300 | 36 | 14 |
| 13 | 0607-2023 | 2023-05-11 | 25 | 8 | 12, $179,834 | 10, −$144,834 | −$35,000 | 2 | 0 |
| 14 | 0705-2023 | 2023-06-30 | 110 | 23 | 45, $1,208,088 | 48, −$1,531,088 | +$323,000 | 12 | 6 |

Every resolution's designation rows net to $0 except three. Reso 01 (+$181,900) is all chart #6,
Speaker's Initiative to Address Citywide Needs (p.17). In Reso 03 (+$416,000) money moves between
initiative charts (Community Development Initiatives −$6,190,000, p.56, and three housing charts −$350,000,
against 18 charts that gain), and the charts together come to +$416,000. Reso 07 (+$5,000,000)
is two one-sided charts: Language Services Worker Co-operatives (+$2,800,000, p.22) and Community
Interpreter Bank (+$2,200,000, p.23). New money, not moves. The PDF prints no total, so this is
reported, not flagged.

## What is new in FY2023 (and how the code handles it)

1. **Caption variants.** Reso 01 p.81 prints "CHART 41:" (no "#"). Reso 01 p.66 and Reso 09
   pp.21, 22, 25 print "- FY 2023" where every other chart prints "- Fiscal 2023". Reso 03 p.20
   prints "(cpntinued)". The caption reader takes each and flags it `W.caption_format` (warn, in
   the review file). Before this, chart #41's 4 rows were dropped and the 4 "FY 2023" charts
   (11 rows) had no budget year.
2. **A chart's first page prints "(continued)".** Reso 08 p.32: chart #25 (Prisoners' Rights
   Project) starts here; p.31 is chart #24. Its two rows ($1,000,000 MOCJ to DYCD, Legal Aid
   Society) were dropped. Now read as the chart's start; allowed only as a named exception
   (`T3.continued_start`), and in the review file.
3. **Drawn rows with nothing in them.** Reso 01 p.67, Reso 03 p.83, Reso 06 p.53 (×2): the grid
   draws an empty row under the last one. Counted in T5 and not kept as rows.
4. **A second wording of the `***` footnote:** "Correction and/or Reversal of a change made in a
   previous Transparency Resolution" (Reso 02 p.8). Both wordings are accepted.
5. **18 rows marked `***` on pages that print only the `*` and `**` footnotes** (9 pages, Reso
   03–08). Named exceptions, as FY2024's two; kept as printed.
6. **4 chart pages with no "Page n" label** (Reso 08 p.44, Reso 09 pp.29–31), all Fiscal 2022
   charts; the next label counts them. Named exceptions.

FY2024, FY2025 and FY2026 outputs are byte-identical with these changes (every tracked file in
their review folders, crops included; re-run on 2026-10-21), with one exception that is not
from this change: re-running FY2026 writes Noel's two committed decisions (commit 428ec86) into
`fy26_tr_review.csv`, which was not regenerated when they were recorded. The base commit
(d2770cb) gives the identical file. Left uncommitted here.

## Files

As in FY2024 (`fy23_` prefix): `REVIEW.md`, `ISSUE-LOG-DRAFT.md` (for #106, **not posted**),
`data/fy23_tr_rows.csv` (8,424), `fy23_tr_charts.csv` (502), `fy23_tr_resolutions.csv` (14),
`fy23_tr_review.csv` (45, same columns as `fy24_tr_review.csv`), `fy23_tr_checks.txt`,
`fy23_tr_flags.csv`, `fy23_tr_pages.csv`, `fy23_tr_disclosure_match.csv`,
`fy23_tr_retired_csv_compare.csv` (the 70 rows above), `fy23_tr_manifest.json`, `data/overlays/`
(45 review crops).

## How to redo it

```
.venv/bin/python code/parse_transparency_v2.py --fy 2023      # ~1.5 min on a laptop CPU
.venv/bin/python -m pytest code/test_transreso.py
```

Byte-identical on re-run (checked). Every year-specific fact is in
`config/transparency/fy2023.toml`.

## What these checks cannot prove

- That a change exists which no PDF printed (no totals, and no chart counts this year).
- Text where both grids read the same wrong text layer (no OCR sample).
- Why the old parser dropped the 9 ordinary rows; not investigated (the retired files stay as they are).

## Since this review

- Rescission origins (report only) now use the checked FY2023 Schedule C,
  `data/fy23/pdf/schedule_c/fy23_sc_awards.csv` (#204, re-run 2026-10-23): 343 → 348 match a
  Schedule C award, 104 → 102 part of a larger amount, 202 → 199 not found. The retired old-parser
  CSVs had missed or misread those awards' (EIN, amount).

## Not done here

- OCR audit.
- Nothing added to the MCP or the public site; the retired `data/fy23/transparency-resolutions/`
  files are unchanged.

## Proposed DATA-ANOMALIES entry

Not added to `DATA-ANOMALIES.md` (parallel sessions number their sections; the integrator places
it). Proposed text:

> ## NN. FY2023 transparency resolutions rebuilt from the PDFs, checked (#106) — REVIEW NOT STARTED
>
> > **Scope.** A new, checked parse of the 14 PDFs in `source/FY23/transparency-resolutions/`
> > (`code/parse_transparency_v2.py --fy 2023`, `config/transparency/fy2023.toml`). Its review
> > record is [`research/2026-10-21-fy23-transparency-review/`](research/2026-10-21-fy23-transparency-review/README.md).
> > The old `data/fy23/transparency-resolutions/*.csv` files are unchanged and stay the historical
> > record (§27). Not served by the MCP.
>
> **Result.** 8,424 rows from 502 charts (the old parse had 8,354, all of which are here), each
> with its resolution's number and adoption date. An independent image grid agrees on every row;
> the ink check finds nothing outside a parsed cell. No totals and no chart counts are printed.
>
> **What the old parse missed.** 61 EINs printed without a hyphen and 9 ordinary rows.
>
> **Things a re-parse must know.** Captions vary: "CHART 41:" (no "#", Reso 01 p.81), "- FY 2023"
> (Reso 01 p.66, Reso 09 pp.21–25), "(cpntinued)" (Reso 03 p.20), and a chart's first page marked
> "(continued)" (Reso 08 p.32). Empty drawn rows sit under some tables (Reso 01 p.67, Reso 03 p.83,
> Reso 06 p.53). The `***` footnote has a second wording. 4 chart pages print no "Page n" label
> (Reso 08 p.44, Reso 09 pp.29–31).
>
> **What the PDF itself gets wrong (flagged, never fixed).** 18 `***` rows with no `***` footnote on
> the page (Reso 03–08). The City's EIN 13-6400434 printed for Fort Greene Council, Inc. (Reso 11
> p.19). Two $0 rows (Reso 07 p.27).
