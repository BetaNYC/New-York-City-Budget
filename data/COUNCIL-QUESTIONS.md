# Questions to Council Finance

`council_questions.csv` lists the questions the PDF review left for the NYC Council's Finance
Division (decisions #209, epic #190). The MCP and the explorer read it and show each question's
status on the rows it covers. Nothing has been sent yet: every question is a `draft`.

| Column | What it holds |
|---|---|
| `question_id` | A short name, lowercase words joined by `-`. |
| `review_ids` | The review rows the question covers (`;`-joined `review_id`s from `data/fy*/pdf/*/*_review.csv`). Blank when the question is about rows with no review entry. |
| `issue` | The GitHub issue that tracks the question, where there is one. |
| `sent_on` | The date it was sent (`YYYY-MM-DD`), blank for a draft. |
| `answered_on`, `answer` | The date and the answer, once answered. |
| `status` | `draft` (not sent), `sent` or `answered`. |

**How each status reads** (`mcp/src/questions.ts`, the same words in the MCP and the explorer):

- `draft`: "Open question (not yet sent)"
- `sent`, under 30 days: "Question sent to Council Finance on <date>"
- `sent`, 30 days or more: "Question sent to Council Finance on <date>, no answer yet". The rows
  are published as printed, with that date.
- `answered`: "Council Finance answered on <date>: <answer>"
- A `needs_info` review row that no question covers (a check we are still doing ourselves, such
  as a Legistar lookup): "Still being checked"

**When a question is sent:** set `status` to `sent` and `sent_on` to the date. When it is
answered: set `status` to `answered`, and fill `answered_on` and `answer`.
`code/test_council_questions.py` checks the file.

## The questions (drafts, 2026-10-23)

Wording for Noel to adapt. Each comes from the review's suggestion for the rows. "The capital
book" is the Supporting Detail for each year's Changes to the Executive Capital Budget (Section
254) that OMB publishes; page numbers are the PDF's pages in `source/FYNN/`.

**Opening line:** We are building a public, checked copy of the Council's budget documents
(BetaNYC, github.com/BetaNYC/New-York-City-Budget). While reading the capital books we found a
few rows we could not explain from the documents alone. Could you help us with the questions
below?

- **`capital-ma-series`** (FY2018 and FY2022–FY2027; FY2019 and FY2020 print no Part II).
  In each book, Part II lists rows that are not in Part I or its total. They have project IDs in
  the "MA" series (FY2026: "MM"), sit on "0N" budget lines, and print no sponsor: FY2018 pp.72–74
  (52 rows), FY2022 pp.77–78 (25), FY2023 pp.76–77 (39), FY2024 pp.65–67 (29), FY2025 pp.72–74 (39),
  FY2026 pp.71–72 (39 MM rows), FY2027 pp.66–67 (30). From FY2022 on they are also not in
  `t474-a92g`. What are the MA and MM series and the 0N lines?
- **`capital-borough-codes-a-c`** (#227). What do borough codes A and C mean in the capital books?
- **`fy2025-capital-pv-ct001-apollo-theater`**. FY2025 p.74, Part II: PV CT001 on PV DN027,
  "126 PV207APLO APOLLO THEATER", $2,500,000. It is not in Part I and not in the MA series. What
  kind of item is it?
- **`fy2022-capital-borough-president-part-ii`**. FY2022, Part II only, no sponsor printed:
  HL KBP01 on HL KN04A (p.75, Brooklyn Plaza Medical Center, $1,000,000); PW KBP01 on PW KN497
  (p.82, Saint Francis College, $1,551,000); PW KBP02 on PW KN03G (p.82, Campaign Against Hunger,
  $1,000,000); PW MBP01 on PW MN03W (p.82, Earth Matter NY, −$72,000). What are the KBP/MBP IDs
  and the KN/MN lines?
- **`fy2024-capital-hl-ta001`**. FY2024 p.65, Part II only: HL TA001 on HL RN404, "SEC249
  ADJUSTMENT FOR THE SIUH NORTHWELL HEALTH CARDIAC IMAGING PROJ", −$40,000. What kind of item is
  it?
- **`fy2018-capital-ta-part-ii`**. FY2018, Part II only, no sponsor printed: AG TA001 on AG DN865
  (p.72, Conselya Block Association, $500,000); HH TA001 on HH DN106 (p.80, Coalition for the
  Homeless, $693,000); HH TA003 on HH MN336 (p.80, Project Renewal, −$100,000). What kind of items
  are these?
- **`fy2023-capital-rr-series`**. FY2023, Part I (pp.46–69): 15 rows with RR project IDs and no
  sponsor printed, $22,633,000, four of them on borough A. What does the RR series mean? On HD D020,
  HD RR001 "CYPRESS HILLS CHILD CARE ASSOC." $4,280,000 (p.51) and HD NC040 "CYPRESS HILLS CHILD
  CARE CORPORATION" $4,279,000 (p.50): are these one project or two?
- **`fy2022-capital-e-cn884`**. FY2022 p.43: E CN884 is printed on two $500,000 rows on E D001
  ("811K TECHNOLOGY" and "NYC PUBLIC SCHOOL 97 BRONX - SCHOOLYARD"); `t474-a92g` has one. Are these
  two separate projects sharing one ID?
- **`fy2020-capital-tf-cn90`**. FY2020 p.79: TF CN90 is printed on two $200,000 rows on TF D005
  (real-time passenger information, one in Manhattan for Council District 11, one in Queens).
  Are these two separate projects sharing one ID?
- **`fy2019-capital-hw-cn030`**. FY2019 p.40: HW CN030, "DOT REPAVING IN DISTRICT 31", $500,000,
  prints sponsor Rose and "CD 49, 00"; `t474-a92g` has district 31 (Richards). Which district and
  sponsor is it?
- **`fy2027-capital-workbook-titles`**. Two FY2027 rows whose titles differ from `t474-a92g`:
  E CC0598 (p.23; the book: Queens United Middle School gym / supplemental cooling; the dataset:
  a science lab upgrade) and E CC1245 (p.36; the book: P.S. 370 auditorium; the dataset: P.S. 199
  auditorium). Which project is each?
