# FY2019 transparency resolutions: what a person needs to check

**Report generated:** 2026-10-22 01:40 EDT. Source: `data/fy19_tr_review.csv` (52 rows), sorted
the same way: the 7 critical items first, then by how much money each could touch. Write each
decision into `data/fy19_tr_review_decisions.csv` by `review_id` (columns `review_id, decision,
note, decided_by, decided_at`; decisions `source_error`, `parser_bug`, `accepted_as_printed` or
`needs_info`), or use the explorer's review screen and `code/validate_review_decisions.py --add`.
The pipeline never writes that file. Nothing here changes a dollar amount. Each item has a crop
in `data/overlays/` (named `r<reso>-p<page>-<review_id>.png`).

## Critical (7)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 1–2 | `9d5b5c4d7120` `fffe2d2c53d4` | 01, p.111 | 4,090,000 | **"All Allocations", EIN "Various"**: chart #56 Purpose of Funds Changes - Fiscal 2018, Source "Food Pantries", DYCD, ($4,090,000) and $4,090,000, a new purpose for the whole initiative ("… refrigeration and other operational needs … food and hygiene pantries in DOE schools"). | Kept as printed: `ein` blank, `ein_printed` "Various". The old CSV missed both rows. | `accepted_as_printed` |
| 3 | `68a35940ec45` | 03, p.46 | 12,000 | **EIN with a hidden glyph**: Dromm, Himalayan Elders Project, Inc., DFTA $12,000. The page shows "472383238" (no hyphen); the text layer adds a tab glyph, "472383238(cid:9)", so the EIN is not read. | `ein` blank, `ein_printed` as in the text layer. The old CSV missed this row. | `parser_bug`, note "EIN 472383238 (47-2383238) as shown on the page" |
| 4–7 | `fd173be58370` `8540b98b201f` `8cf11d14f11d` `73f1326f3977` | 04, p.19 | 5,000–10,000 | **`**` on a page whose only footnote is `*`**: chart #4 Anti-Poverty Initiative, Torres: Urban Justice Center ($10,000) MOCJ → Catholic Charities Community Services $10,000 DYCD; Cumbo: Brooklyn Defender Services ($5,000) DSS/HRA → Fund for the City of New York - Crown Heights Mediation Center $5,000 DYCD. | Kept as printed: `budget_modification` = 1. Named exceptions. | `source_error` |

## Warn (45)

| # | review_id | Reso, page | $ | What | What we did | Suggest |
|---:|---|---|---:|---|---|---|
| 8–40 | 33 items (`T7.overfull`) | 03 pp.43, 46, 83; 04 pp.23, 26, 40, 49, 51, 52, 56, 64, 65; 07 pp.25–31, 37, 38 | 3,500–52,500 | **Overfull cell**: the organization (or purpose) wraps to more lines than the row is tall, and is drawn across the row's rules. On the page part of it is cut off or printed on top of the next row. Largest: Reso 03 p.43 row 12, Association of Community Employment Programs for the Homeless, $52,500; Reso 04 p.65 row 1, LSNY Bronx Corporation, ($50,000), purpose "… survivors of domestic / violence." | Read whole from the text layer as one block per cell (README item 1). 43 rows on these pages read differently from before; each was compared by hand, before and after. For example Reso 07 p.27 row 17 was "IGnrce.enwich House, Inc. …" and is now "Greenwich House, Inc. …"; Reso 04 p.49 row 6 gains "67K", Reso 04 p.51 row 2 "43B". | `accepted_as_printed` |
| 41 | `0ab53f659594` | 07, p.30 | 15,000 | **A separator printed without spaces at a line end**: Ulrich, "Jamaica Center for Arts and Learning, Inc. - CCNS Howard Beach Neighborhood SC-" / "Catholic Charities Neighborhood Services, Inc.", DCLA $15,000. The rows around it print " - " between program and sponsor. | Kept as printed: "…Neighborhood SC-Catholic Charities…". Named in `wrap_hyphen_review`. | `accepted_as_printed` |
| 42 | `6705769f1596` | 01, p.1 | — | **Printed date one day before Legistar's**: p.1 "This Resolution, dated July 17, 2018"; Res 0457-2018 adopted 2018-07-18 (Legistar, 2026-07-07 notes; the filename uses it). | `resolution_date` = 2018-07-18; `resolution_date_source` names only the Legistar notes. Named exception (`T13.printed_date`). | `source_error` |
| 43 | `e06f8aeea1ba` | 01, p.108 | — | **Wrong chart number**: "CHART 55: Purpose of Funds Changes - Fiscal 2018". #55 is the Fiscal 2019 chart (pp.104–107); pp.109–111 print "CHART 56: … Fiscal 2018 (continued)". | Read as the first page of chart #56. Named exception (`T3.chart_number`). | `source_error` |
| 44 | `4af715944a83` | 03, p.55 | — | **"Page 41" printed on top of the `***` footnote** (the text layer reads "…Transparency ResolutPioange 41"). | No label read; the labels around it (40, 42) count the page. Named exception (`T3.page_label`). | `accepted_as_printed` |
| 45–47 | `e29a9e69a342` `37c6fc0433f1` `e9cf6d6b0a30` | 02 p.32; 09 p.23; 10 p.15 | — | **Odd captions**: "CHART 7 Cultural Immigrant Initiative" (no colon); "CHART # 7:" (space after "#"); "CHART 7:" in a resolution that otherwise prints "CHART #n:". | Read as the printed number. | `accepted_as_printed` |
| 48–52 | `7d33ee4c31ac` `db52eb3d0481` `d2a214951861` `c970c5dc2b21` `8ffa2797d4cc` | 02 p.103; 03 p.83; 04 p.68; 05 p.138; 07 p.41 | — | **"Beating Hearts Initiative": no Agency or Amount column** (112 rows: 41, 53, 5, 12, 1), and no note under the table. Reso 03 p.83 also has one overfull row (item in 8–40, `2d36ea91ec80`). | Rows kept, amount blank, `action` = `listed`. Named exceptions (`T4.no_amount`). | `accepted_as_printed` |

## Not in the review file, on purpose

- **One chart $1 off inside itself** (no printed total, so no check fails): Reso 02 chart #8
  DoVE (pp.33–37, +$4,546,229 against −$4,546,228). Both grids read the same digits. See
  Decisions.
- **Reso 02 takes back $144,999 more than it gives**: chart #5 A Greener NYC −$70,000 and chart
  #12 Parks Equity Initiative −$75,000 have no matching designation in the resolution (plus the
  $1 above). Reported, not a check.
- **2 EINs printed without a hyphen**, read as printed (`W.ein_no_hyphen`): Reso 02 p.74 DOHMH
  (City EIN, −$182,000) and Reso 07 p.25 Conscientious Musical Revues ($15,000); both rows the
  old CSV missed. Three more are on "Beating Hearts" rows.
- **25 line-end hyphens on 24 rows**, all read by hand (`config/transparency/fy2019.toml`); only
  item 41 is not a compound word.
- **144 rows with a cell spanning two columns** (`W.spanning_cell`): initiative names printed
  across Source and Member on purpose-of-funds charts, member blank, as FY2026.
- **2 `*` cells with no border of their own** (`W.made_cell_empty`, Reso 07 p.22), both empty.
- **1 drawn row that prints nothing** (Reso 05 p.29 row 31). Counted, not a row.
- **Disclosure gaps** (report only): 544 FY2019 designations not found on (EIN, amount): 484
  taken back later, 43 at another amount, 10 key already used, 5 EIN not in the disclosure, 2
  City-EIN name mismatch. FY2018 and FY2017 charts: 143 of 158 and 138 of 143 found.
  `data/fy19_tr_disclosure_match.csv`.
- **Rescission origins** (report only): of 1,393, 713 take back an earlier resolution's row, 49
  match a Schedule C award (retired CSV), 298 part of a larger amount, 333 not found.

## Decisions for Noel

1. **The $1 slip** (DoVE, Reso 02 chart #8). Kept as printed, not a review row, as FY2020's two.
   Decide all three together.
2. **Item 3, Himalayan Elders Project**: the page clearly shows EIN 472383238; only a hidden tab
   glyph in the text layer stops it being read. I suggest `parser_bug` with the EIN in the note,
   rather than a code rule for one row.
3. **Overfull cells (items 8–40)**: the text layer is the record; the page shows these names
   overlapped or cut off. If you would rather keep only what the page shows, say so; the reader
   would need a clipping rule instead.
4. **"Beating Hearts Initiative" rows** (112) with no amount and no note. Kept as `listed`, as
   FY2020–FY2022.
5. **Reso 01's date**: kept Legistar's 2018-07-18 (it matches the filename and the crosswalk).
