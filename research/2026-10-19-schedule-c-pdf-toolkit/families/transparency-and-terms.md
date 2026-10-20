---
title: "PDF family assessment: transparency resolutions and Terms & Conditions"
created: 2026-10-19
type: research
status: draft
tags: [schedule-c, pdf, qa, transparency-resolutions, terms-and-conditions]
---

# PDF family assessment: transparency resolutions and Terms & Conditions

**Report generated:** 2026-10-19 23:46 EDT. Prepared by BetaNYC with AI assistance.
**Last revised:** 2026-10-20 00:18 EDT — factual QA pass (11 fixes)
**Data current as of:** source PDFs and committed CSVs at this branch's base (`main` @ `f5740c3`
plus the condition survey, `30fc9f3`); Council disclosure CSVs as committed under
`data/fyNN/expense_disclosure/`; Christian Moscardi's PR #43 at local `pr43` head `2191833`;
issue #44 and PR #43 comments read from GitHub on 2026-10-19.
**Status:** draft. Nothing was built or committed. No repo file other than this one was touched.

Every number below comes from a command run on 2026-10-19, against the files named. The vector-grid
numbers come from an **unreviewed prototype** (pdfplumber `lines` strategy, about 80 lines,
scratch only). They show what a grid parse finds, not a clean dataset. Where I looked at a
rendered page, the page is named.

---

## Bottom line

1. **Transparency resolutions: 187 PDFs, 8,122 pages, three eras.** FY2013–FY2026 are
   born-digital Excel charts with full cell grids (149 PDFs, 6,827 pp). FY2010–FY2012 are
   born-digital as well (23 PDFs, 729 pp), but their text layer glues words together and their
   charts print totals. 15 PDFs (566 pp) are scans: all 8 for FY2009, 3 for FY2010, 3 for FY2011
   and 1 for FY2012.
2. **The committed transparency CSVs undercount.** The prototype grid parse finds rows the
   committed parse never emitted in every year. The clearest case is FY2026: 173 rows print
   the EIN without a hyphen (`131641068`), and the committed parser's regex requires the
   hyphen. All 157 positive designations among them match the FY2026 Council disclosure on
   (EIN, amount), so they are real awards. Corpus-wide the prototype finds 475 hyphenless EINs.
3. **FY2010–FY2012 are reconcilable, contrary to `code/PARSING.md`.** Their charts print a
   total under the grid. 178 such lines (140 `$0.00` transfer charts, 38 non-zero). The
   prototype, unreviewed, sums to the printed total exactly on 170 of 178. The committed CSVs
   also truncate cents: 337 prototype rows in those years carry non-zero cents (`$18,606.94`
   is committed as `18606`).
4. **Nine FY2010–FY2013 PDFs produce no designations, and seven of them are scans.** FY2010
   Reso 01 is a 6-page FY2009 resolution with its exhibits missing. FY2013 Reso 09 is not a
   transparency resolution at all: it is a Finance Division report on the SoHo BID. The three
   FY2013 `.doc` "BLOCKED" files also hold no charts (0 EINs), so converting them recovers
   nothing.
5. **Christian's OCR pipeline extends to FY2010–FY2012 without new code.** On two chart pages
   each of FY2011 Reso 08 and FY2012 Reso 02 (Xerox JBIG2 scans), it produced 83 and 60 rows.
   On the 18 FY2012 rows I checked against the page, every EIN, amount and member matched.
   What does not carry over cleanly is chart captions and the org/program split. #44 is a
   review-time problem, not an engineering one.
6. **Terms & Conditions are prose, and the committed extract is roughly the right shape.** But
   its text carries 393 mid-word splits (`appropriatio n`, `inci dents`) from the pypdf text
   layer. The fix is to re-extract the text and add a check, not to restructure the data.

---

## 1. Inventory and condition

### 1.1 Transparency resolutions by fiscal year × era × tier

Tier is from `data/pdf_condition.csv` (`qa_tier`). "Scan pp" are inked image-only pages, and
"blank" are pages with no ink. "Divider pp" are the vector-drawn EXHIBIT pages (0 characters,
no image) in the FY2010–FY2011 ScanSoft files. Counts come from a script over
`data/pdf_condition_pages.csv`.

| FY | PDFs | Pages | Doc tiers | Era / producer | Scan pp | Divider pp | Blank |
|---|---:|---:|---|---|---:|---:|---:|
| 2009 | 8 | 332 | D×8 | Scan: 301-dpi bitonal JBIG2 in PDFlib+PDI wrappers | 331 | 0 | 1 |
| 2010 | 12 | 430 | A×8 (mixed), B×1, D×3 | ScanSoft PDF Create! (8); Distiller (R01); scans R02 (Xerox 5655), R03–R04 (PDFlib) | 110 | 96 | 24 |
| 2011 | 10 | 307 | A×5 (4 mixed), A+B×2, D×3 | ScanSoft / Distiller; scans R08–R10 (Xerox 5675) | 57 | 54 | 1 |
| 2012 | 8 | 226 | A×6, A+B×1, D×1 | ScanSoft / Distiller; scan R02 (Xerox 5675); R07 has a `-dup` twin | 46 | 0 | 1 |
| 2013 | 9 | 238 | A×8, A+B×1 | Word 2010 (+ 3 `.doc` files, not PDFs) | 0 | 0 | 0 |
| 2014 | 3 | 48 | A×3 | ScanSoft / Adobe PDF Library | 0 | 0 | 0 |
| 2015 | 12 | 378 | A×12 | Acrobat Pro 11 / ScanSoft | 0 | 0 | 0 |
| 2016 | 13 | 557 | A×13 | Acrobat Pro 11 / ScanSoft / Nuance | 0 | 0 | 0 |
| 2017 | 13 | 630 | A×13 | Acrobat Pro 11 / Nuance | 0 | 0 | 0 |
| 2018 | 12 | 598 | A×12 | Acrobat Pro 11 / DC / Nuance | 0 | 0 | 2 |
| 2019 | 11 | 733 | A×11 | Acrobat Pro / Nuance / PDF Library | 0 | 0 | 0 |
| 2020 | 8 | 508 | A×8 | Acrobat Pro DC | 0 | 0 | 0 |
| 2021 | 8 | 404 | A×8 | Acrobat Pro DC | 0 | 0 | 0 |
| 2022 | 14 | 709 | A×14 | Acrobat Pro DC / macOS Quartz / Word | 0 | 0 | 4 |
| 2023 | 14 | 697 | A×14 | Acrobat Pro (32-bit) | 0 | 0 | 0 |
| 2024 | 9 | 388 | A×9 | Acrobat Pro (32-bit) | 0 | 0 | 0 |
| 2025 | 13 | 395 | A×13 | Acrobat Pro (64-bit) | 0 | 0 | 0 |
| 2026 | 10 | 544 | A×10 | Acrobat Pro (64-bit); R02 straight from Excel | 0 | 0 | 0 |
| **Total** | **187** | **8,122** | | | **544** | **150** | **33** |

**Tier D, exactly.** The 15 scanned PDFs hold 566 pages: 544 inked and 22 blank. 21 of the
blank pages are duplex backs in FY2010 Reso 02, and 1 is FY2009 Reso 07 p.11. The FY2010–FY2012
scans are 7 documents and 234 pages (FY2010: 42 + 18 + 71; FY2011: 29 + 15 + 13; FY2012: 46),
of which 213 are inked.

### 1.2 Eras, as seen on the page

I rendered pages with pypdfium2 and looked at them.

- **E1, FY2009 scans** (FY2009 Reso 01, pp.16 and 24, and a contact sheet of all 30 pages).
  - **Layout.** Each file opens with a Committee on Finance report and the resolution text,
    then the charts. The charts are landscape tables on portrait sheets and render sideways.
  - **Cells and totals.** The tables are fully ruled, amounts print with cents
    (`$119,591.65`), and several charts print a total under the grid: Chart 8, "Legal
    Services for the Working Poor", prints `$1,050,000.00` = 4 × `$262,500.00`.
  - **More than one resolution per file.** FY2009 Reso 01 contains three "THE COUNCIL /
    REPORT OF THE COMMITTEE ON FINANCE" title pages (pp.1, 15 and 24 on the contact sheet), so
    one file can hold several resolutions or report versions.
  - **Handwriting.** The resolution text carries handwritten margin notes. At thumbnail size
    they appear to read "Chart 12 does not exist" (p.2) and "… does not exist" (p.7). These
    need a human read.
- **E2, FY2010–FY2012 born-digital** (FY2010 Reso 05 p.11; FY2011 Reso 06 p.13).
  - **Columns.** Excel charts with a full cell grid. The header row sits *above* the top rule,
    outside the grid. Columns: `Member | Organization | EIN Number | Agency | Amount | Agy # |
    U/A | Fiscal Conduit/Sponsoring Organization | Fiscal Conduit EIN | *`.
  - **Amounts and totals.** Amounts print with cents. Rescissions print red in parentheses.
    A total line sits under each chart (`$0.00` on transfer charts).
  - **Glued text, and why it is solvable.** The text layer has no space glyphs: inter-word
    gaps measure about 2.4 pt and intra-word gaps about 0.06 pt (FY2010 Reso 05 p.11, measured
    with pdfplumber). That is a clean empty valley. `x_tolerance=1.5` turns
    `ChristChurchofNewBrighton` into `Christ Church of New Brighton`. This is the
    "glued-text problem" the build plan raises for #44 and FY2010–FY2014 Schedule C, and on
    born-digital pages it yields to geometry.
- **E3, FY2013–FY2018** (FY2013 Reso 01 p.17; FY2016 Reso 01 p.10).
  - **Layout.** The same grid. FY2013's header is still above the top rule, and from FY2016
    the header is inside the grid. Charts carry "- Fiscal YYYY" in the caption from FY2013.
  - **Column variants.** A "Source" column on purpose-of-funds charts (`Source | Member |
    Organization | EIN | Agency | Amount | New Purpose of Funds`). Fiscal-conduit columns on
    the Local Initiatives charts through FY2018. "Organization - Program" headers start in
    FY2016.
- **E4, FY2019–FY2026** (FY2019 Reso 05 p.28; FY2023 Reso 04 p.4; FY2026 Reso 02 p.3).
  - **Layout.** A full grid with a gray header row. Whole-dollar amounts. "Page n" footers.
    `CHART #n:` captions repeat on every page ("(continued)").
  - **Blank member cells.** From FY2023, rows whose member cell is blank are the agency side
    of a transfer, as in FY2026 Reso 02 p.3: `| Housing Preservation and Development |
    13-6400434 | HPD | $100,000`. A parser must not fill these from the row above.

### 1.3 What a row is

One row is one designation change. The columns are:

- **Who and to whom:** the sponsoring member (or Borough delegation, "Speaker", or none for
  citywide initiatives), the organization (from FY2016, "Organization - Program") and its EIN.
- **The money:** the agency code, the amount and the budget coordinates `Agy #` / `U/A`.
- **Conduit columns:** before FY2019, many rows also carry the fiscal conduit and the
  conduit's EIN.
- **The `*` column:** marks a row pending pre-qualification. `**` and `***` after the
  organization mark "requires a budget modification" and "correction to a previous
  resolution".

**Fiscal year and initiative are chart-level, not row-level.** The fiscal year comes from the
chart caption ("Local Initiatives - Fiscal 2026") and the initiative is the chart's name.

**The sign carries change vs. new.** A rescission prints in parentheses (red). A transfer is a
rescind/designate pair, and a new designation is a lone positive row. Nothing on the row says
"transfer"; it is inferred from the chart's net, which is why the printed `$0.00` totals in
FY2009–FY2012 matter.

### 1.4 Contents problems in the transparency folders

| File | What it actually is | Evidence |
|---|---|---|
| `FY10/.../Transparency-Reso-01-2009-03-11.pdf` | A **Fiscal 2009** resolution ("This Resolution, dated March 11, 2009 … Fiscal 2009 Expense Budget"). It is 6 pages of report and resolution text, and the Charts 1–10 / Exhibits A–J it cites are **not in the file**. | Text p.1, p.6; 0 chart pages |
| `FY10/.../Transparency-Reso-02-2009-06-19.pdf` | A Finance Division packet dated June 18, 2009. Inside: a memo (p.1: "The last FY'09 Transparency Resolution"), a disclosure form, a "NON-CITY CAPITAL FUNDING FROM RESOLUTION A" list, then "FISCAL 2009 TRANSPARENCY RESOLUTION June 19, 2009" and its charts. | Rendered p.1; contact sheet |
| `FY10/.../Transparency-Reso-03-2009-06-30.pdf` | A FY2010 resolution covering Fiscal 2008, 2009 and 2010 designations. It is correctly filed, but it carries prior-year charts. | Rendered p.1 |
| `FY13/.../Transparency-Reso-09-2013-02-27.pdf` | **Not a transparency resolution.** It is a Finance Division report on a resolution "concerning the establishment of the SoHo Business Improvement District". | Text pp.1–2; the only born-digital file in the folder without "DESIGNATION" on pp.1–2 |
| `FY13/.../Transparency-Reso-{07,10,11}-*.doc` | The report and resolution text only. `textutil` finds 0 EIN-shaped strings in each, although they cite 7, 10 and 14 charts. Their exhibits are absent. | `textutil -convert txt` |
| `FY12/.../Transparency-Reso-07-2012-02-01-dup.pdf` | The same content as `…-01.pdf`. All 29 pages have identical text and render to identical pixels (at 0.5×). The files differ only in `ModDate` (18:54:15 vs 18:54:37, 2012-03-15) and the byte offsets that follow from it. Either copy can be canonical. | pypdfium2 text and render hashes; metadata |
| `FY18/.../Transparency-Reso-01-2017-06-21.pdf` | Dated before FY2018 starts, but the report covers designations after the June 6, 2017 FY2018 adoption. Correctly filed. | Text p.1 |

**Numbering gaps cannot be tested from these files.** The `NN` in the filenames runs 1..N
with no gaps in every folder. It looks repo-assigned: the documents print "Preconsidered Res.
No." with the number blank. Calendar gaps between consecutive resolution dates are the only
signal. The longest are:

| Gap | From | To |
|---|---|---|
| 307 days | FY2013 Reso 12 (2013-06-26) | FY2014 Reso 01 (2014-04-29) |
| 175 days | FY2012 Reso 07 (2012-02-01) | FY2013 Reso 01 (2012-07-25) |
| 124 days | FY2020 Reso 07 | FY2020 Reso 08 |
| 114 days | FY2015 Reso 12 | FY2016 Reso 01 |

Whether resolutions were adopted in those windows (especially July 2013–March 2014 and
February–June 2012) is open. Answering it needs the Council's own record, which this
assessment did not query.

---

## 2. What the committed parse gets wrong (measured)

### 2.1 Zero-row resolutions reported as "EXTRACTED"

The `*_reconciliation.txt` files list these resolutions at 0 rows, yet `code/PARSING.md`
counts them as parsed:

- **FY2010:** Reso 01 (no charts), Reso 02, 03 and 04 (scans).
- **FY2011:** Reso 08, 09 and 10 (scans).
- **FY2012:** Reso 02 (scan).
- **FY2013:** Reso 09 (SoHo BID).

The table there reads "FY10 | 12 | LOW", "FY11 | 10" and "FY13 | 9 (of 12 …)". The FY2010–FY2012
scans appear nowhere in DATA-ANOMALIES §1's blocked list.

### 2.2 Vector-grid prototype vs. committed CSVs

**Method.** The scratch `vgrid.py` runs pdfplumber `find_tables` (lines/lines, snap 3) on
every page with a `CHART n` caption. When the header is not a grid row, it takes the header
from the words in the 22 pt band above the grid. Columns are mapped by header name, and words
are joined with `x_tolerance=1.5`. The comparison is the (EIN digits, amount in cents)
multiset against `fyNN_transparency_all.csv`, excluding the `-dup` file. Runtime for all
172 born-digital PDFs was a few minutes on one core. The prototype is **unreviewed**:
"only_vgrid" mixes real recoveries with prototype errors (for example, the rows it reads with
no amount).

| FY | Prototype rows | Committed | Matched | Only prototype | Only committed | Hyphen-less/odd EIN | No EIN |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2010 | 1,965 | 1,788 | 1,665 | 300 | 123 | 9 | 157 |
| 2011 | 1,602 | 1,545 | 1,416 | 186 | 129 | 6 | 20 |
| 2012 | 980 | 932 | 865 | 114 | 67 | 5 | 1 |
| 2013 | 1,950 | 1,857 | 1,827 | 123 | 30 | 7 | 2 |
| 2014 | 174 | 166 | 158 | 16 | 8 | 0 | 7 |
| 2015 | 3,323 | 3,047 | 2,884 | 439 | 163 | 22 | 19 |
| 2016 | 4,394 | 4,156 | 4,150 | 63 | 6 | 38 | 1 |
| 2017 | 5,124 | 4,656 | 4,641 | 300 | 15 | 98 | 13 |
| 2018 | 5,546 | 5,366 | 5,352 | 58 | 14 | 58 | 2 |
| 2019 | 7,207 | 7,090 | 7,090 | 5 | 0 | 8 | 0 |
| 2020 | 5,382 | 5,319 | 5,305 | 4 | 14 | 4 | 0 |
| 2021 | 4,500 | 4,463 | 4,463 | 9 | 0 | 8 | 1 |
| 2022 | 7,918 | 7,768 | 7,768 | 59 | 0 | 56 | 1 |
| 2023 | 8,424 | 8,354 | 8,354 | 70 | 0 | 72 | 0 |
| 2024 | 3,303 | 3,294 | 3,294 | 9 | 0 | 8 | 0 |
| 2025 | 3,555 | — (never parsed) | — | 3,555 | — | 10 | 2 |
| 2026 | 4,952 | 4,755 | 4,755 | 197 | 0 | 175 | 1 |

**What the disagreements are, where I checked:**

1. **Hyphen-less EINs.** Across the corpus the prototype reads 475 nine-digit EIN cells with
   no hyphen (seen on FY2026 Reso 02 p.27: `131641068`, Goodwill Industries, $20,000). The
   committed `ANCHOR` regex requires `\d{2}-\d{7}`, so every such row is dropped. For FY2026,
   157 of 173 are positive designations, and **157 of 157** match the FY2026 disclosure on
   (EIN, amount).
2. **No EIN printed.** Example: FY2013 Reso 01 p.17, Quinn / Friends of Vesuvio Playground /
   DPR / ($3,500.00), with the EIN cell empty on the page. The committed parse is EIN-anchored
   and drops these.
3. **Rows merged into their neighbor in FY2013.** FY2013 Reso 01 has 80 prototype rows that
   are not committed as rows, over 26 pages. The committed parse kept only each one's EIN,
   appended to the previous row's `organization`, and dropped its name and amount. Examples:
   p.20 "Working Today Inc. 13-3858323 DOHMH $100,000.00" survives only as `13-3858323` inside
   the Paraprofessional Healthcare Institute row, and p.26 "Woodside on the Move, Inc.
   11-2435565 HPD $13,438.00" only as `11-2435565` inside the West Side Federation row. 77 of
   Reso 01's 587 committed rows carry a second EIN in `organization`. This is the row-merging
   class of Schedule C FY2023 and DATA-ANOMALIES §20.
4. **Cents truncated.** `ANCHOR` captures `\$[\d,]+` and stops at the decimal point. The
   prototype finds 337 FY2010–FY2012 rows with non-zero cents. Example: FY2011 Reso 06 p.20,
   Christ the Rock, `$18,606.94` is committed as `18606`. These rows land in both "only"
   columns, which accounts for part of FY2010–FY2012's "only committed".
5. **Clipped overflow text.** In 98 EIN cells the prototype reads letters, such as FY2013
   Reso 01 p.19 `nc.41-2068330`. The organization text runs under the EIN cell, and the page
   clips it out of view (crop viewed). A vector parse has to honor clipping, or flag every
   cell whose characters fall outside the visible cell.
6. **In-source EIN oddities, to flag and never fix.**
   - Two EINs for the same organization on consecutive rows: FY2010 Reso 05 p.11, Christ
     Church of New Brighton, `13-5598851` and `13-5596851` (viewed).
   - Malformed EINs: an 8-digit `20569320` (3 rows), a 10-digit `20-11664531`, a 7-digit tail
     `13-559836`, and an EIN with a leading zero-width space.
   - A placeholder EIN: FY2012 Reso 02 p.20, Kupferberg Center Performances `13-0000004`
     (viewed on the scan).

### 2.3 FY2010–FY2012 printed totals

Check: sum the prototype rows since the last total and compare with the lone money line on the
page (`totcheck.py`, scratch).

| FY | Totals checked | Exact | Mismatch |
|---|---:|---:|---:|
| 2010 | 86 | 82 | 4 |
| 2011 | 74 | 71 | 3 |
| 2012 | 18 | 17 | 1 |

**Mismatches of one or two cents (3), likely in-source rounding, to confirm on the page:**

- FY2010 Reso 06 p.28: printed $1,664,000.00, rows $1,663,999.98.
- FY2011 Reso 03 p.46: printed $1,365,000.00, rows +$0.01.
- FY2012 Reso 03 p.16: printed ($0.00), rows −$0.01.

**Larger mismatches (5), not yet diagnosed:**

- FY2010 Reso 09 p.15: printed $0.00, rows $273,500.
- FY2010 Reso 10 p.19: printed $0.00, rows −$50,000.
- FY2010 Reso 12 p.12: printed $0.00, rows $13,500.
- FY2011 Reso 02 p.24: printed $1,200,000.00, rows $5,700,000.
- FY2011 Reso 05 p.22: printed $0.00, rows $160,000.

These could be page-boundary errors in the check, missed rows, or real arithmetic errors in
the source.

FY2013 onward prints no lone money line (0 in every year), so the "NOT RECONCILABLE" label
holds there.

### 2.4 Independent check: the Council disclosure workbooks

**How it should tie.** A disclosure workbook (`data/fyNN/expense_disclosure/
fyNN_expense_awards.csv`, which has `ein`, `amount`, `council_member`, `fiscal_conduit`,
`fiscal_conduit_ein`) lists each fiscal year's designations after adoption. A positive
transparency row for fiscal year Y should appear in FY Y's disclosure as (EIN, amount),
unless a later resolution changed it. Rescissions and the City-EIN agency halves of transfers
should not. Use the plan's join rule: the (EIN, amount) multiset, never EIN alone, and a name
check for `13-6400434`.

**Tested on two resolutions:**

- **FY2026 Reso 02.** 1,296 of 1,321 positive prototype rows (98.1%) match the FY2026
  disclosure on (EIN, amount), and 1,224 of 1,244 non-City rows do. This works as a coverage
  check for modern years.
- **FY2013 Reso 01.** Only 123 of 506 positive rows match the FY2013 disclosure. Of the 70
  positive rows the committed parse missed, 10 match. The early-year disclosure is evidently a
  different snapshot or scope, and I did not diagnose it. Treat disclosure alignment as
  report-only, and expect it to be useful from about FY2015 on.

FY2010 has no disclosure CSV in `data/`.

---

## 3. Christian Moscardi's pipeline (#43) and the extension (#44)

### 3.1 What #43 already does for FY2009

His `code/ocr/` pipeline (render → orient → classify → grid → docTR recognize → assemble →
report) produced `data/fy09/transparency-resolutions/` on branch `pr43`.

| Measure | Value |
|---|---|
| Rows | 2,620 over 8 resolutions |
| Page classes | 124 chart, 121 narrative, 86 divider, 1 blank |
| Cells recognized | 19,532 |
| Mean cell confidence | 0.927 |
| Rows with at least one flag | 2,194 (83.74%) |
| `ocr:amt` (amount failed its shape check) | 897 rows (34.24%) |
| `ocr:ein` | 55 |
| Rows with the `amount` field empty | 897 |
| Cells queued for review | 3,858 |
| Printed totals that reconcile exactly | 0 of 1 found |

What I checked in his output:

- **Chart 8 of Reso 01 is right.** The four rows (EINs 11-2480339, 51-0141489, 13-2972415,
  13-3442022, each $262,500) match the page I viewed.
- **His report never checks that chart's printed total.** Chart 8 prints `$1,050,000.00` under
  the grid, but the report found only one printed total in all of FY2009 (reso 07). Total
  detection is under-counting, so the strongest check FY2009 has is mostly unused.
- **Chart captions are garbled.** Reso 01's chart field reads "Legal for the Poor Services
  Working EIN Agency # Organization …", with the words out of order and header words mixed
  in. Captions need their own read.
- **The `flags` column carries `*`, `**`, `.`, `:` and `-` values** (the star column leaking
  into it).

### 3.2 Trial on FY2010–FY2012 scans (two pages each)

Run unmodified from `git archive pr43`, Python 3.12 venv (docTR 0.12.0, torch 2.14.1, OpenCV
4.14.0, pypdfium2 4.30.0), `--pages 20-21 --debug`:

| File | Rows | `ocr:ein` | `ocr:amt` | `ocr:lowconf` rows | Cells / queued | Wall time |
|---|---:|---:|---:|---:|---:|---:|
| FY2011 Reso 08 (Xerox 5675) | 83 | 0 | 2 | 57 | 592 / 80 | 50.8 s |
| FY2012 Reso 02 (Xerox 5675) | 60 | 0 | 0 | 30 | 420 / 42 | 40.0 s |

I compared the first 18 FY2012 rows (p.20, upright render from his cache) with the page.
**Every member, EIN and amount was correct**, including the in-source placeholder
`13-0000004`. Three problems showed up:

- **Chart captions.** The p.20 caption ("CHART 4: Cultural After-School Adventure (CASA) -
  Continued") came out blank, and p.21's is header soup.
- **Organization and program split.** It is inconsistent: sometimes "PS 73" lands in
  `program`, and sometimes "Creative Arts Team PS 117 Q" stays in `organization`.
- **Stray characters.** One `*` was read into the organization ("Brooklyn Arts Council, Inc.
  \* Public School 104").

**Verdict on #44.** The extension is straightforward for the numeric columns: the same
scanner family (301-dpi bitonal JBIG2, confirmed by reading the image XObjects), the same
fully ruled charts, and per-page orientation handles the sideways pages. Captions, the
org/program split, and the FY2010–FY2012 total lines (which his report should check, as
in §2.3) are the work. FY2010 Reso 03–04 are PDFlib-wrapped like FY2009. I did not run them.

### 3.3 Scope corrections for #44

- **Scope.** #44 is FY2010–FY2012 scans only: 7 documents and 234 pages. **FY2013 has no
  scans.**
- **Fiscal year.** FY2010 Reso 02 is a *Fiscal 2009* transparency resolution (its own memo
  says so). FY2010 Reso 01 is Fiscal 2009 too, with no charts to OCR. Whoever owns the FY2009
  year should decide where their rows belong.
- **Exhibit dividers.** The 150 vector-drawn EXHIBIT dividers in the born-digital ScanSoft
  files need no OCR. They are 0-character, 0-image pages.

---

## 4. Terms & Conditions (12 PDFs: 11 T&C documents + the misfiled DOHMH insert)

**What they are.** The 11 documents (274 pp; 275 with the insert) are Word-produced prose,
16–34 pages each, with no scans (`terms_conditions` tiers: B×10, A+B×1, A×1, the A being the
DOHMH insert).

**What each condition holds:**

- an agency heading with its code, e.g. "City University of New York (042)", numbered
  `N.` from FY2025;
- one or more "Unit of Appropriation [NNN]" lines, or for capital items, "Budget Line
  HA-0001";
- a paragraph: "As a condition of the funds in unit of appropriation …, the agency shall
  submit to the Council … a report on …";
- report deadlines and coverage periods.

**Tables appear once a year, at most.** Ruled pages (FY2022 p.8, FY2027 p.7, both viewed) are
the DOE "Financial Status Report" schedule (FSR month, content, issue date, meeting date).
That is a small table, not data.

**Is "structured data" the right goal?** Yes, at the level of one row per condition. The prose
is the data, so the structure is the index around it. The committed `data/fyNN/terms/*.csv`
schema (`item_number, agency_name, agency_code, units_of_appropriation, num_units,
report_deadlines, coverage_period, condition_text`) is already that index.

**Minimal useful extract.** Keep that schema. Add `page_start` and `page_end`, a `kind`
column (expense U/A vs. capital budget line), and a printed-vs-synthesized `item_number`
flag. Carry verbatim `condition_text` from a text layer with geometric word spacing. Emit the
FSR table as a small side table, or leave it in the text.

**QA path:**

1. **Counts.**
   - FY2025–FY2027 print numbered headings 1..65, 1..68 and 1..75, with no gaps or
     duplicates. These equal the committed row counts (65, 68, 75).
   - FY2015–FY2024 print none, so count the agency-code headings instead and compare.
2. **Text fidelity.** The committed text has mid-word splits from pypdf. Counted as adjacent
   tokens whose concatenation is a word in the pdfium text layer and whose halves are not:

   | FY | Splits | FY | Splits |
   |---|---:|---|---:|
   | 2015 | 4 | 2022 | 29 |
   | 2016 | 37 | 2023 | 26 |
   | 2017 | 18 | 2024 | 33 |
   | 2018 | 13 | 2025 | 36 |
   | 2021 | 27 | 2026 | 1 |
   | | | 2027 | 169 |
   | **Total** | | | **393** |

   Re-extract the text, and keep this check as a regression test.
3. **Units of appropriation.** Every "Unit of Appropriation [x]" line in the PDF (228, 237
   and 262 lines in FY2025–FY2027) must land in exactly one condition.
4. **Human spot-read of the segment boundaries,** 2 or 3 conditions per year.

**Other T&C findings:**

- **The FY2015 file is mixed.** `fy2015-tc.pdf` is expense *and* capital: the committed CSV
  has 2 "Capital Budget" conditions and 15 expense conditions (Correction, DOE, DOHMH, DHS,
  SBS, DYCD, Miscellaneous). It is not "capital budget T&C" as the condition survey says
  (recorded in `../CONDITION.md` errata, 2026-10-19).
- **A trailing-hyphen artifact.** The FY2015 committed data writes "Department of Homeless
  Services-".
- **The FY2022 FSR table has an in-source date oddity:** the month column's years are out of
  sequence (SEPTEMBER–DECEMBER 2022, then FEBRUARY 2022, then MARCH 2021). Flag it; do not fix
  it.
- **`FY17/2016-DOHMH-Terms-and-Conditions-Oral-Health.pdf`** (1 page, viewed) is a DOHMH
  oral-health program update.
  - **It looks like a fragment.** The page opens mid-list with "Updated oral health
    provider list", and it reads like a reply to a condition, not a condition.
  - **Its one table adds up internally.** It has 4 programs plus a Total: 268,000 + 12,450 +
    13,120 + 7,500 = 301,070, and children seen 1,675 + 417 + 1,110 = 3,202.
  - **What to do with it.** It is not T&C, and there is nothing to parse into the T&C schema.
    Reclassify it as a supporting document.

---

## 5. Summary

### 5.1 Year × type × tier

| FY | Transparency: PDFs (tiers) | Scan pp | T&C | DOHMH insert |
|---|---|---:|---|---|
| 2009 | 8 (D×8) | 331 (+1 blank) | — | — |
| 2010 | 12 (A×8, B×1, D×3) | 110 (+21 blank) | — | — |
| 2011 | 10 (A×5, A+B×2, D×3) | 57 | — | — |
| 2012 | 8 (A×6, A+B×1, D×1), incl. `-dup` | 46 | — | — |
| 2013 | 9 (A×8, A+B×1), + 3 `.doc` | 0 | — | — |
| 2014 | 3 (A×3) | 0 | — | — |
| 2015 | 12 (A×12) | 0 | B (17 pp) | — |
| 2016 | 13 (A×13) | 0 | B (30 pp) | — |
| 2017 | 13 (A×13) | 0 | B (30 pp) | A (1 pp) |
| 2018 | 12 (A×12) | 0 | B (34 pp) | — |
| 2019 | 11 (A×11) | 0 | — | — |
| 2020 | 8 (A×8) | 0 | — | — |
| 2021 | 8 (A×8) | 0 | B (16 pp) | — |
| 2022 | 14 (A×14) | 0 | A+B (18 pp) | — |
| 2023 | 14 (A×14) | 0 | B (19 pp) | — |
| 2024 | 9 (A×9) | 0 | B (24 pp) | — |
| 2025 | 13 (A×13), never parsed | 0 | B (25 pp) | — |
| 2026 | 10 (A×10) | 0 | B (29 pp) | — |
| 2027 | — | — | B (32 pp) | — |

### 5.2 QA path and effort per group

The effort figures are my estimates, not measurements.

| Group | Files / pages | Path | Effort |
|---|---|---|---|
| G1 Born-digital, E3–E4 (FY2013–FY2026) | 149 / 6,827 | **Parse:** vector grid with char-center cell assignment, clip-aware, and the header taken from inside or above the grid.<br>**Checks:** Christian's image grid as the independent check (as on FY2027 Schedule C); disclosure alignment as report-only coverage.<br>**Review:** the ~1,500 prototype disagreements in this table. | 3–4 days of build, then 1–2 days of review |
| G2 Born-digital, E2 (FY2010–FY2012) | 23 / 729 | **Parse:** G1 plus geometric word spacing (`x_tolerance` in the measured valley), exact cents, the conduit columns, and an EXHIBIT-divider skip.<br>**Check:** the printed-total gate (178 totals; 8 to diagnose). | +2 days |
| G3 Scans FY2010–FY2012 (#44) | 7 / 234 (213 inked) | **Run:** Christian's pipeline as is. Measured at about 20–25 s per page wall, so roughly 1.5 h.<br>**Add:** a printed-total check that finds totals under the grid, and a caption read.<br>**Review:** the queue. Extrapolating 42–80 queued cells per 2 chart pages, and assuming FY2009's chart-page share (124 of 332) holds, so that about 80 of the 213 inked pages are charts (not counted), gives about 1,700–3,200 cells. | 1 day of engineering, 2–3 days of review |
| G4 FY2009 scans (#43) | 8 / 332 | **Done by Christian.** Remaining: widen total detection (Chart 8 example), clean the captions, and work the 3,858-cell review queue. Then decide where FY2010 Reso 01–02 (Fiscal 2009) belong. | 2–3 days of review |
| G5 Not transparency / empty | FY2013 Reso 09; FY2010 Reso 01; 3 FY2013 `.doc` | Reclassify and document. Find the missing exhibits from another source, if one exists. | Hours, plus a records question |
| T&C | 11 / 274, + 1-page insert | Keep the schema and re-extract the text. Checks: counts, U/A coverage, a split-word regression test, spot reads. | About 1 day |

---

## 6. Corrections the published record needs

These are flags for the repo owner. Nothing was changed.

1. **`code/PARSING.md` transparency table.**
   - It counts zero-row resolutions as parsed: FY2010 Reso 01–04, FY2011 Reso 08–10, FY2012
     Reso 02 and FY2013 Reso 09.
   - It says "NOT RECONCILABLE in every year — these documents print no per-chart or grand
     totals". That is false for FY2009–FY2012.
   - Its org-text confidence bands disagree with the year files. FY2014 is listed MODERATE;
     the file says LOW (6.02%). FY2015 is listed HIGH; the file says MODERATE. FY2016 is
     listed MODERATE; the file says LOW (5.08%).
2. **DATA-ANOMALIES §1.** It omits the seven FY2010–FY2012 scans from the blocked list. Its
   FY2013 `.doc` entry implies OCR or conversion would recover data, but the files hold no
   charts.
3. **DATA-ANOMALIES §3 / `PARSING.md`, "financial columns … are deterministic and reliable in
   every year".** They are not complete:
   - hyphen-less EINs are dropped (157 confirmed FY2026 awards);
   - rows with no printed EIN are dropped;
   - some FY2013 rows are merged into their neighbors (77 in Reso 01);
   - cents are truncated in FY2010–FY2012.
4. **DATA-ANOMALIES §8 (`-dup`).** Confirmed: same content, `ModDate` 22 s apart. The entry
   can say so.
5. **FY2013 Reso 09 is the SoHo BID report.** It should leave the transparency folder or be
   labeled as such.
6. **FY2010 Reso 01 and Reso 02 are Fiscal 2009 documents.** Reso 01 lacks its exhibits.
   Reso 02 also bundles a Resolution A non-City capital list.
7. **Noel Hidalgo's PR #43 comment (#60 item E).** It reads "FY2010–FY2013 … image-only — 234 pages
   across 8 documents". The correct statement is FY2010–FY2012, 7 documents, 234 pages (213
   inked).
8. **`CONDITION.md` (this folder).** Both items are recorded in `../CONDITION.md` errata,
   2026-10-19:
   - "The 15 tier D files (694 pages)": they hold 566 pages. 694 is the family's page-tier D
     count, which includes the 150 vector dividers.
   - "`FY15/fy2015-tc.pdf` is the *capital* budget T&C": it is mixed (§4).
9. **PR #43's DATA-ANOMALIES §22.** "FY2009 is the *only* Transparency-Resolution year whose
   charts print totals" is not right: FY2010–FY2012 do too.
10. **Committed T&C text.** It carries 393 mid-word splits (§4).

## 7. For the PR #43 author (Christian Moscardi)

These notes are public, so sending them waits for a maintainer decision.

**Already done, credit as is:** the FY2009 pipeline, its trust model, the review queue, and
the conduit sidecar.

**To tell him:**

- Chart 8 of FY2009 Reso 01 prints `$1,050,000.00`, but `report.py` found only 1 printed total
  in FY2009, so total detection misses totals printed under the grid. FY2010–FY2012 have 178
  such lines.
- Unmodified, his pipeline read FY2011 Reso 08 and FY2012 Reso 02 cleanly on the numeric
  columns.
- Chart captions and the org/program split are the weak fields.
- On born-digital FY2010–FY2012, `x_tolerance=1.5` fixes the glued text (gaps of about 0.06
  pt vs. 2.4 pt), so the hybrid he suggests in #44 (OCR plus the text layer for validation)
  is available. For the 23 born-digital files the text layer can be primary.

**To ask him:**

1. Would he widen the printed-total detection to lines under the grid, and add a caption
   stage?
2. For #44, should FY2010 Reso 02 (Fiscal 2009) be emitted under FY2009?
3. Is the 34% `ocr:amt` rate in FY2009 mostly the `$#,###.##` shape check rejecting good
   reads, or real misreads? His PR description says the results "look pretty good" and are
   "probably in the 90%+ range already".
4. Would he review a clip-aware vector-grid parser for the born-digital years, with his image
   grid as the check?

## 8. Open questions

1. Do the missing exhibits (FY2010 Reso 01; FY2013 Reso 07, 10, 11) exist anywhere, and were
   resolutions adopted in the July 2013–March 2014 and February–June 2012 gaps?
2. Where do Fiscal 2009 documents filed under FY10 belong in the output: by folder or by the
   resolution's own fiscal year?
3. What are the 5 non-cent FY2010–FY2011 total mismatches (§2.3): checker, parser, or source?
4. Why does the FY2013 disclosure match only 24% of FY2013 Reso 01's positive rows?
5. Should FY2025 (13 PDFs, 3,555 prototype rows, never parsed) be parsed now, given 2.0
   retired PDF-derived data from the MCP?
6. The handwritten FY2009 annotations ("Chart 12 does not exist"): are any charts missing
   from the scans themselves?

---

*Method note.* Scratch scripts (not committed) were the condition-CSV aggregation, `render.py`,
`sheet.py`, `pagetext.py`, `headers.py`, `vgrid.py`, `compare.py`, `yearcmp.py`, `totcheck.py`
and the disclosure and T&C checks. Christian's pipeline ran from `git archive pr43`, unmodified.
Rendered pages were viewed for FY2009 Reso 01 (pp.16 and 24, plus a contact sheet), FY2010
Reso 02 (p.1, sheet), FY2010 Reso 03 (p.1, sheet), FY2010 Reso 05 p.11, FY2011 Reso 06 p.13,
FY2011 Reso 08 (sheet), FY2012 Reso 02 (sheet; p.20 upright), FY2013 Reso 01 p.17 and the crops
at p.19 and p.44, FY2016 Reso 01 p.10, FY2019 Reso 05 p.28, FY2023 Reso 04 p.4, FY2026 Reso 02
p.3 and the crop at p.27, T&C FY2022 p.8 and FY2027 p.7, and the DOHMH insert.
