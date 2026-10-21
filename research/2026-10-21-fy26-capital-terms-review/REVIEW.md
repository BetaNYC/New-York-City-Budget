# FY2026 capital and T&C: rows for Noel to review

**Generated:** 2026-10-21 00:32 EDT, from `data/fy26_capital_sd_review.csv` and
`data/fy26_terms_review.csv`. Prepared by BetaNYC with AI assistance.

Sorted by dollars. Page = PDF page (1-based), not the printed "Page N of 61". Nothing here was
"fixed": every value is kept as printed, and the flag says why to look.

**Short version.** Every printed total ties (33 / 33, plus the p.65 summary and Part III). No dollar
amount in the PDF is in doubt. The Council workbook matches 1,253 of 1,261 amounts; the 8 others are
explained. What's left is three odd Part II rows, words (sponsor, title) and two policy questions.

## A. Capital: decide or confirm (by dollars)

| # | $ (FY2026) | Page | Row | What | Suggested decision |
|---|---:|---|---|---|---|
| 1 | 62,073,000 | 71–72 | 39 `PV MM…` rows on `PV 0N…` lines | In Part II and Part III only. Not in Part I, not in the p.65 "City Council Additions", not in the Council workbook. No sponsor. The Part II total ($203,243,000) includes them. FY2027's `MA` / `0N` rows are the same kind | Accept as printed. Ask Council Finance what `MM` / `MA` / `0N` mean (Mayoral?) |
| 2 | 26,920,000 | 65 | p.65 "Less Rescindments" | One printed number. No list of rescindments in this book, so only the subtraction ties | Accept; note "unverifiable here" |
| 3 | 2,500,000 | 71 | `PV MA0022` THE CENTER FOR NEW JEWISH CULTURE AT 17 EASTERN PARKWAY, line `PV 0N06Z` | Part II only, like #1, but an `MA` ID (not `MM`). In Part III (p.85) | Accept as printed; include in the Council Finance question |
| 4 | 2,500,000 / 2,000,000 / 1,000,000 | 59 / 61, 74 / 56 | `PV NC1130`, `PV NC1031`, `P CN1114` | `, WON`, `, SALAAM`, `, POWERS` typed into the PDF after export (font `KGLUJE+ArialMT`). The workbook has `Speaker`, `Speaker`, `Speaker,Lee`. Unlike FY2027, the `PV NC1031` edit is in Part I **and** Part II | Accept as printed (the later edit) |
| 5 | 250,000 + 125,000 | 50 | `HN CN1451`, `HN CN0092` (Hunter campus school gym) | **The workbook files two projects under one ID.** PDF: `HN CN1451` $250,000 SPEAKER and `HN CN0092` $125,000 POWERS. Workbook: `HN CN1451` twice (rows 61 and 875), no `CN0092`; its row 61 text even cites `HN CN0145`. Same amounts and line | Keep the PDF. Note the workbook error in `data/capital/RECONCILIATION.md` (not edited here) |
| 6 | (FY2027) 2,950,000 | 4, 51, 64 | 7 rows with sponsor `ADMIN` (`AG NC1561`, `AG NC1563`–`NC1566`, `HR NC1560`, `PW NC1562`) | $0 in FY2026, money in FY2027 only. Not in the workbook (it holds the FY2026 report). In Part I, Part II and the totals | Accept as printed |
| 7 | 500,000 | 70 | `PV MA0007` GUGGENHEIM MUSEUM (126 PV467GUG8), line `PV DN176` | Part II only, on a `DN` line (the lines Part I rows use), not in Part I. In Part III (p.80) | Accept as printed; include in the Council Finance question |
| 8 | **−183,000** | 70, 81 | `PV MA0005` MANHATTAN COMMUNITY ACCESS CORPORATION EVENT STUDIO UPGRADE, line `PV MN07D` | **A negative row**, Part II only. Printed `-183,000` (p.70) and `$(183,000)` (p.81). Every total includes it | Accept as printed (a reduction). Viewers must not assume amounts ≥ 0 |
| 9 | 1,500,000 … 200,000 | 67, 69, 73, 75 | `ED NC1175`, `ED NC0689`, `HL NC1187`, `PV NC0691`, `PW NC1092` | Part II prints `GUTIERREZ` / `FARIAS` where Part I prints `GUTIÉRREZ` / `FARÍAS`. Only the accent differs | Accept both as printed |
| 10 | 200,000 | 19 | `E CN1572` NEW HEIGHTS MIDDLE SCHOOL LAB | The PDF prints `K391 S:K722` (no `B:`); the workbook has `B:K391`. Ink check: nothing hidden | Accept as printed; `building_code` empty |
| 11 | 78,000 | 36 | `E CN0093` | Title: PDF starts `P94M THE SPECTRUM SCHOOL …`; workbook has no `P94M` | Accept PDF |
| 12 | 50,000 | 57 | `P CN0393` TREE GUARDS | Workbook adds ` CD 16` | Accept PDF |
| 13 | — | 17–41 | 8 `E CN…` titles | The **workbook** has stray characters in the codes (`B:X091nS:X091`, `P.S. 93n9`, `B:M1910S:M452`, `S:Q9M93`). The PDF is clean | None here; a note for `data/capital/` |
| 14 | — | 4–53 | 41 titles | A code that is not `B:`/`S:` + letter + 3 digits stays in the title as printed (`B:07X277`, `S:437`, `B;Q405`, `B: S:`). FY2027 has 18 such rows and they were accepted | Accept as printed |
| 15 | — | 35–41 | 4 titles (`E CN1588`, `CN1564`, `CN1566`, `CN0450`) | A tab glyph with no Unicode mapping between the codes; `title_raw` keeps `(cid:9)`, `title` reads it as a space | Accept |

## B. Capital: checked, no action needed (FYI)

- **8 two-read disagreements** (pp.56, 59, 61, 74). Someone edited these pages after export, so the
  text stream is out of order. Every one kept the page-position read: 4 are a `0` both rows print,
  4 are sponsors the Council workbook confirms (e.g. p.56 `LEE` belongs to `P CN1542`).
- **3 rows** needed the "nearest row" rule (`PV NC0991` pp.61 and 74, `HL NC1333` p.69). Values
  and sponsors match the other Part and the workbook.
- **`TECHNICAL ADJUSTMENTS`** is a printed sponsor on 18 Part I rows ($25,919,000). All 18 are in the
  workbook. Kept as printed.
- **The retired `data/fy26/capital/` CSV** agrees with this parse on every row, amount and sponsor.
  It differs only in how it split odd codes out of titles (41 titles, 81 code cells), and it names the
  ID column `budget_line` and the budget line `sub_id`. Not edited.
- **`P CN1606`** ($2,000,000, p.56), which `data/capital/RECONCILIATION.md` §4 found only in the
  workbook, is printed in the PDF: a third source agrees.

## C. Terms & Conditions

Nothing has dollars. All checks pass except one wording quirk (C3).

| # | Page | What | Suggested decision |
|---|---|---|---|
| 1 | 2–29 | **The retired CSV is wrong for 18 conditions.** It put headings into the text (#5, #25, #29, #39, #53–#55, #59–#68), put the FSR table into #15's text, and lost units in 12 conditions (#5 and #25 entirely, because they print `Units of Appropriation`; the second and later agencies in #59–#68) | Use the new file. Note it in DATA-ANOMALIES |
| 2 | all | The PDF uses U+2010 (`‐`) for hyphens: 91 in condition text, plus budget lines (`HB‐0278`). The old CSV turned them into `-` (29 conditions differ only by that). New keeps them as printed | Keep as printed. Search in the explorer should fold `‐` to `-` |
| 3 | 27 | #67 says "units of appropriations 311 and 312"; T3 does not read the plural, so it flags the body as naming only NYPD's 001. The heading (311, 312, 001) is right | Accept; the typo is the PDF's |
| 4 | 8 | FSR table dates print superscript ordinals and a no-break space (`October 2nd`). The parser now keeps the ordinal in place (it had read `nd October 2`); the no-break space is kept | Accept as printed |

## D. Policy questions (not decided here)

1. Where clean PDF data lives (epic #101, open decision 1). This folder is `research/` only; the
   stacked promotion PR writes `data/fy26/pdf/`, as FY2027's did.
2. Should the retired `data/fy26/capital/` and `data/fy26/terms/` CSVs be replaced by these, or left
   as history with a pointer? (Same question as FY2027 D2.)
