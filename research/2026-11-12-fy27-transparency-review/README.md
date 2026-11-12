# FY2027 transparency resolutions, checked from the PDFs (#246, #102)

**Report generated:** 2026-11-12. Prepared by BetaNYC with AI assistance.
**Data current as of:** the 4 PDFs and their 4 resolution-text files in
`source/FY27/transparency-resolutions/` (227 pages; hashes in `config/transparency/fy2027.toml`
and `source/FY27/README.md`, downloaded and checked 2026-11-12); expense disclosure as committed
in `data/fyNN/expense_disclosure/`; rescission origins from the checked
`data/fy27/pdf/schedule_c/fy27_sc_awards.csv`; code at this branch's commit.
**Status:** checked, review in progress. Every check passes or is a named, listed exception.
No person has reviewed the flags yet.

Part of #246 and #102 (epic #101). Done the same way as FY2026
(`research/2026-10-21-fy26-transparency-review/`), with the same code, plus two small additions
(below).

## What these PDFs are

After the FY2027 budget was adopted (June 30, 2026), the Council changed who gets the money, a
batch at a time, by resolution. Each of the 4 PDFs is one resolution's charts. Each chart row is
one change: money taken from an organization (red, in parentheses), money given to one (black),
or the purpose of an award reworded. Unlike FY2026, these PDFs print **no resolution text**: it is
a separate "Res. No." Word file on the same Legistar page, kept beside each PDF.

## Results

| What | Result |
|---|---|
| Rows | **2,808** (2,020 designations, 650 rescissions, 138 purpose-of-funds rows) from 155 charts on 227 pages |
| Per resolution | 719 · 425 · 1,297 · 367 (table below) |
| Budget year changed | Fiscal 2027: 2,742 rows · Fiscal 2026: 49 · Fiscal 2025: 10 · none printed: 7 (3 charts) |
| Printed totals | **None to tie.** The charts print no money totals (T15). What is printed and ties: "Charts 1 through N" in each resolution's text, 4 / 4 (38, 40, 49, 28) |
| Image grid (independent) | **2,808 / 2,808** rows agree on every field |
| Ink coverage | 0 uncovered regions. Self-test passes: hiding one row, or one letter, makes the check fire (Reso 01 p.1) |
| Anchor census | 2,809 EIN-shaped words = 2,808 rows with an EIN + 1 EIN printed inside an organization's name (Reso 04 p.13, named exception, critical review item) |
| Sign vs colour | 719 amounts in parentheses, all red; 0 disagree |
| Characters | 325,852 non-space characters; 0 in a table but in no cell; 0 hidden |
| Fiscal years | Every chart's year is one its resolution's text names (2025-2027); 3 charts print none |
| Dates | No PDF prints a date. Dates are the Legistar dates, equal to the filename dates |
| Spot check by eye | 8 rows (2 per resolution, money and purpose rows, picked at random, seed 246) cropped from the page at 200 dpi: all fields match |
| Disclosure (report only) | Fiscal 2027: 952 of 1,962 organization designations ($36.2M) are in the disclosure on (EIN, amount). The FY2027 disclosure is the Council's adoption-time snapshot (#58), so most later designations are not in it yet |
| Review file | **10 rows** (1 critical, 9 warn), largest $20,000 (`REVIEW.md`) |

### Per resolution

| # | Res. | Adopted | Pages | Rows | Charts | Orgs + (n, $) | Orgs − (n, $) | Agency side net | Purpose rows | "Speaker" rows |
|---:|---|---|---:|---:|---:|---|---|---:|---:|---:|
| 1 | 0551-2026 | 2026-07-16 | 54 | 719 | 38 | 448, $13,417,188 | 202, −$7,052,800 | −$6,364,388 | 22 | 108 |
| 2 | 0595-2026 | 2026-08-13 | 48 | 425 | 40 | 240, $22,821,060 | 106, −$7,974,500 | −$14,706,560 | 30 | 40 |
| 3 | 0652-2026 | 2026-09-24 | 89 | 1,297 | 49 | 1,091, $33,872,762 | 113, −$5,970,074 | −$27,302,688 | 56 | 51 |
| 4 | 0695-2026 | 2026-10-22 | 36 | 367 | 28 | 208, $5,971,781 | 99, −$2,271,973 | −$3,194,808 | 30 | 41 |

Designations and rescissions net to $0 in Reso 01; Reso 02-04 net +$140,000, +$600,000 and
+$505,000. As in FY2026, the PDF prints no total that could show this as an error; it fits money
held back at adoption being designated later. Reported, not flagged.

## What is new for FY2027

1. **Resolution text from a separate file.** `code/parse_transparency_v2.py` reads a
   resolution's text from the Word file named by `text` in the config (sha256 checked), when the
   PDF has none. The fiscal-year check (T12) and "Charts 1 through N" use it. Other years are
   unchanged: none of their configs sets `text`.
2. **An EIN printed inside an organization's name** (`T5.ein_in_text`, `code/transreso/checks.py`).
   A named exception gives the page and the word; it passes only if a row on that page prints the
   word in its organization. Reso 04 p.13.

## Files

As FY2026: `REVIEW.md`, `ISSUE-LOG-DRAFT.md` (not posted), and in `data/`: rows, charts,
resolutions, review, review decisions (header only: no decisions yet), checks, flags, pages,
disclosure match, retired-CSV compare (none: there was no old FY2027 CSV), manifest, and a page
crop per review item in `overlays/`.

## How to redo it

```
python3 -m venv .venv
.venv/bin/pip install -r code/requirements.txt -r code/requirements-cv.txt pytest
.venv/bin/python code/parse_transparency_v2.py --fy 2027      # ~30 s on a laptop CPU
.venv/bin/python -m pytest code/test_transreso.py
```

The run is byte-identical on re-run (checked).

## What these checks cannot prove

- That a change exists which no PDF printed (no totals to catch it).
- Which organization the Reso 04 p.13 row means (the PDF prints an EIN for its name).
- The year of the 3 charts that print none.
- Text where both grids read the same wrong text layer. No OCR sample was run (ink is clean and
  the PDFs are born-digital).
