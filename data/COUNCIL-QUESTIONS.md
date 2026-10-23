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
- `sent`, under 30 days: "Question sent on <date>"
- `sent`, 30 days or more: "Question sent to Council Finance on <date>, no answer yet". The rows
  are published as printed, with that date.
- `answered`: "Council Finance answered on <date>: <answer>"

**When a question is sent:** set `status` to `sent` and `sent_on` to the date. When it is
answered: set `status` to `answered`, and fill `answered_on` and `answer`.
`code/test_council_questions.py` checks the file.

## The questions (drafts, 2026-10-23)

Wording for Noel to adapt. Each comes from the review's suggestion for the rows.

- **`capital-ma-series`** (every capital year, FY2018–FY2027). In the §254 supporting detail,
  Part II prints rows with "MA" project IDs on "0N" budget lines, with no sponsor (FY2026 also
  "MM"). They are not in Part I or its total, nor in the Council's capital dataset (`t474-a92g`).
  What are the MA and MM series and the 0N lines?
- **`capital-borough-codes-a-c`** (#227). What do borough codes A and C mean in the capital books?
- **`fy2025-capital-pv-ct001-apollo-theater`**. PV CT001 (Apollo Theater) is printed only in
  Part II, with a CT ID on a DN line. What is it?
- **`fy2022-capital-borough-president-part-ii`**. Four Part II-only rows with KBP/MBP IDs on KN/MN
  lines and no sponsor. What are KBP/MBP and KN/MN?
- **`fy2024-capital-hl-ta001`**. HL TA001, −$40,000, printed only in Part II, a TA ID on an RN
  line. What is it?
- **`fy2018-capital-ta-part-ii`**. Three Part II-only TA rows with no sponsor (HH TA003 is
  negative). What are they?
- **`fy2023-capital-rr-series`**. Fifteen Part I rows with RR IDs and no sponsor, four on borough A.
  What do RR and borough A mean, and is the Cypress Hills pair one project?
- **`fy2022-capital-e-cn884`**. E CN884 is printed on two $500,000 rows on E D001. Should it have
  been two IDs?
- **`fy2020-capital-tf-cn90`**. TF CN90 is printed twice on TF D005 at $200,000. Should it have
  been two IDs?
- **`fy2019-capital-hw-cn030`**. HW CN030 prints CD 49, 00 (Rose); the Council's dataset has
  district 31 (Richards). Which is right?
- **`fy2027-capital-workbook-titles`**. Two FY2027 rows whose titles differ from the Council's
  dataset: E CC0598 (the book: Queens United Middle School gym / supplemental cooling; the
  dataset: a science lab upgrade) and E CC1245 (the book: P.S. 370 auditorium; the dataset:
  P.S. 199 auditorium). Which project is each?
