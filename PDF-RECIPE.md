# Recipe: turn one fiscal year of PDFs into checked tables

This is the step-by-step for one fiscal year of Council budget PDFs: from the files in `source/`
to tables a person has reviewed and the public explorer serves. FY2027 (#102), FY2026 (#103) and
FY2025 back to FY2018 (#104–#111) were done this way. The plan behind it is
[`research/2026-10-19-schedule-c-pdf-toolkit/PLAN.md`](research/2026-10-19-schedule-c-pdf-toolkit/PLAN.md),
and the epic that tracks every year is [#101](https://github.com/BetaNYC/New-York-City-Budget/issues/101).

**Last revised:** 2026-10-22.

## The idea in four lines

1. Read the table borders the PDF draws, not the order its text happens to come out in.
2. Check every row against what the PDF prints: its totals, a second reading from the page
   image, and an ink check for anything missed.
3. Never fix the PDF. Where it is wrong or unclear, flag the row and let a person decide.
4. Nothing is public until a person has decided every flag and marked the year `closed`.

## Words used here

| Word | Meaning |
|---|---|
| EIN | An organization's federal tax ID. Schedule C prints one on every award row. |
| Anchor | The thing that marks the start of a row, usually its EIN. Counting anchors tells you how many rows a page should have. |
| Vector grid | The table borders the PDF draws as lines. Reading cells from them is the main reading. |
| Image grid | The same borders found in a picture of the page. It is the second, independent reading. |
| Ink coverage | A check that every printed mark on the page landed inside a parsed cell. |
| Tier | How readable a PDF is: A = ruled tables, B = few lines, A+B = some of each, D = a scan. |
| §254 | Section 254 of the City Charter, under which the Council adopts changes to the capital budget. |
| Stacked PR | A pull request opened against another pull request's branch, so the two are reviewed in order. |

## The four kinds of PDF

Each kind (a "family") has one script and one config file per year. Everything specific to a year
lives in its config; the code is shared.

| Family | What it is | Script | Config | Tests |
|---|---|---|---|---|
| `schedule_c` | Schedule C: who got each discretionary award | `code/parse_schedule_c_v2.py` | `config/schedule_c/fy20NN.toml` | `code/test_schedc.py` |
| `transparency` | Transparency resolutions: changes made after adoption, each with a date | `code/parse_transparency_v2.py` | `config/transparency/fy20NN.toml` | `code/test_transreso.py` |
| `capital_sd` | Capital §254 supporting detail | `code/review_capital_sd.py` | `config/capital_sd/fy20NN.toml` | `code/test_review_capital_sd.py`, `code/test_review_fyNN_capital_terms.py` |
| `terms` | Terms and Conditions | `code/review_terms.py` | `config/terms/fy20NN.toml` | `code/test_review_fyNN_capital_terms.py` |

Shared code: `code/schedc/` (vector grid, structure, printed totals, disclosure alignment, review
file), `code/schedc_cv/` (image grid, ink coverage), `code/transreso/` (transparency on top of
both), and `code/ocr/grid.py` (Christian Moscardi's image grid, from #43).

Capital Resolution A ("Capital Changes") books are not a family yet. The epic rates them low
priority.

## Before you start

- [ ] Read the year's issue (#102 is FY2027 … #121 is FY2008) and its row in the epic's year table.
- [ ] Look up every PDF for the year in `data/pdf_condition.csv`: pages, tier (A: ruled tables,
      B: few rules, D: a scan), rotated pages, encryption.
- [ ] Read the family's assessment in `research/2026-10-19-schedule-c-pdf-toolkit/families/`.
- [ ] Read the most recent finished year of the same family as your model, especially its
      `README.md`, `REVIEW.md` and `ISSUE-LOG-DRAFT.md`. For FY2026:
      `research/2026-10-21-fy26-schedule-c-review/`, `research/2026-10-21-fy26-transparency-review/`,
      `research/2026-10-21-fy26-capital-terms-review/`.
- [ ] Set up Python once:

```bash
python3 -m venv .venv
.venv/bin/pip install -r code/requirements.txt -r code/requirements-cv.txt pytest
```

## Step 1: write the year's config

Copy the latest config of the family, for example `config/schedule_c/fy2026.toml` to
`fy2025.toml`, and change what is true of the new year: the PDF path and its `sha256`, page
count, `review_dir`, the categories or units as printed, and any page-specific quirks. Every
value should cite the page it was read from.

`review_dir` is where the run writes: `research/<date>-fyNN-<family>-review/`, with the date the
work starts (run `date`). Capital and Terms and Conditions share one folder,
`research/<date>-fyNN-capital-terms-review/`. Their configs also set `prefix` and `issue`
(the year's issue number), which promotion reads.

To try a few pages without writing anything, Schedule C takes `--pages`:

```bash
.venv/bin/python code/parse_schedule_c_v2.py --fy 2025 --pages 160-170
```

## Step 2: run it

```bash
.venv/bin/python code/parse_schedule_c_v2.py --fy 2025       # Schedule C, about 1 minute
.venv/bin/python code/parse_transparency_v2.py --fy 2025     # transparency resolutions
.venv/bin/python code/review_capital_sd.py --fy 2025         # capital supporting detail
.venv/bin/python code/review_terms.py --fy 2025              # Terms and Conditions
```

Then prove two things:

- [ ] **Re-running gives the same files, byte for byte.**
- [ ] **Every year already done is unchanged.** Re-run each finished year of the family and
      confirm `git status` shows no change to its files. If the shared code had to change, this
      is how you show it did not change anything else.

Run the family's tests (table above). Add a test for anything new you handled.

## Step 3: read the checks

Each run writes a `*_checks.txt` into `<review_dir>/data/`. The checks, in plain words:

| Check | What it asks | If it fails |
|---|---|---|
| Vector grid vs image grid | Do two independent readings (the PDF's drawn lines, and the page image) find the same cells and values? | A person looks; the text layer is the record, unless the person confirms the page shows something else (`read_from_page_image`, Step 7) |
| Printed totals | Do the rows add up to every total the PDF prints (category, initiative, chart, `TOTALS FOR`)? | A parser bug until proven otherwise; if the PDF is wrong, it becomes a named exception in the config |
| Anchor census | Does every EIN (or other row anchor) on the page become exactly one row? | Rows were dropped or merged |
| Ink coverage | Is any printed mark on the page outside every parsed cell? | Something was dropped |
| Disclosure alignment | How do the rows compare with the Council's disclosure workbook for that year? | Report only. The disclosure never fills or changes a PDF value |

When the PDF disagrees with itself (for example, FY2027 p.214: a statement says $7,229,999 and its
rows add to $7,229,998), do not fix it. Add a named exception to the config that matches the page
and both amounts, so the run still passes and the row goes to review.

## Step 4: write the review record

In `<review_dir>/`:

- [ ] `README.md`: what was parsed, the results, how to redo it, and what the checks cannot prove.
- [ ] `REVIEW.md`: every flagged item, critical first, then by dollars. For each one, say what to
      check and suggest a decision.
- [ ] `ISSUE-LOG-DRAFT.md`: one block per problem, in the order found:
      **Problem / Where / Found by / Tried / Fix / Status**.
- [ ] `data/*_review.csv`: the review queue. Keep the same columns as the model year's file, so
      the explorer's review screen and `code/validate_review_decisions.py` work unchanged.

Open **PR A** (code, config, tests, review record) against `main`.

## Step 5: promote

Promotion regenerates the tables from the PDF into `data/fyNN/pdf/<family>/`. Nothing is copied
from `research/`.

- [ ] Add the year to `code/build_pdf_promoted.py`: an entry in `FAMILIES`. Schedule C also
      needs the year in `SC_ISSUE` and `SC_NOTE`, and transparency in `TR_ISSUE`, or the run
      stops with an error. Capital and terms take the issue from their config.
- [ ] Run it. It writes the tables and the year's rows in `data/pdf_years.csv`, with
      `status = reviewed` and the year's issue number.
- [ ] Run `--check` yourself before opening the PR. CI runs it too, with `pytest code` and
      `build_review_suggestions.py --check` (`.github/workflows/python-checks.yml`, #200), but
      it takes about 20 minutes, so don't wait for CI to find a drift.

```bash
.venv/bin/python code/build_pdf_promoted.py --write
.venv/bin/python code/build_pdf_promoted.py --check     # exit 1 if anything drifted
```

Open **PR B** (promotion), stacked on PR A. Doing two years? Stack them: year 1 review, year 1
promote, year 2 review, year 2 promote.

## Step 6: load it into the explorer for review

- [ ] In `mcp/scripts/pdf-families.mjs`, add the year's decisions file path under each family's
      `decisions`. Commit a decisions file holding only the header line:
      `review_id,decision,note,decided_by,decided_at`.
- [ ] Add the year to `code/build_review_suggestions.py`: its review files in `REVIEW_FILES`,
      and rules in `suggest()` that cite the year's own `REVIEW.md` items. Items that say "ask
      Council Finance" become `needs_info`. A family-year in `data/pdf_years.csv` with no
      `REVIEW_FILES` entry, or no rules of its own, stops the run, and
      `code/test_review_decisions.py` fails if any review row has no suggestion. Then run
      `--write`, and `--check` before you open the PR.
- [ ] Build the explorer with the reviewed data and run its tests (Node 22 or later):

```bash
(cd mcp && npm ci)
cd viz/explorer
npm ci
npm run data -- --include-reviewed     # never touches mcp/data/budget.db
npm test && npm run build && npx vite preview
```

Every row from a reviewed family is labeled "checked, review in progress".

## Step 7: a person reviews

Open the explorer's **Review** tab. Each item shows the PDF page with the row highlighted, the
parsed values, and the suggested decision. The decisions are:

| Decision | Meaning |
|---|---|
| `accepted_as_printed` | The row is right as the PDF prints it |
| `source_error` | The PDF itself is wrong; keep it as printed and flag it |
| `parser_bug` | We read it wrong; the right value goes in the note |
| `needs_info` | Can't tell yet (for example, waiting on Council Finance) |
| `read_from_page_image` | The page and the PDF's text layer disagree, and you checked the page: use what the page shows. The note must say it: `page shows ein: "87-0753479"` (fields: `ein`, `org`, `member`, `agency`, `purpose`). The reader then uses that value, keeps the text layer's in `ein_printed` / `*_raw`, and lists the field in the row's `read_from_page_image` (#209; `code/page_image.py`) |

Decisions stay in the browser until you export them. Export per family, then check the export
and merge it into the committed file:

```bash
.venv/bin/python code/validate_review_decisions.py \
    --review data/fy25/pdf/schedule_c/fy25_sc_review.csv \
    --decisions <review_dir>/data/fy25_sc_review_decisions.csv \
    --add ~/Downloads/<exported file> --write
```

The decisions file is the record of a decision. The review files' `decision` and `note` columns
are copies of it (the readers fill them on every run), so `--write` also copies the merged
decisions into the review file beside the decisions file and into `--review`, changing only those
cells. After editing a decisions file by hand, run the same command with `--sync` instead of
`--add`. `code/test_review_decisions.py` fails while a committed review file says something its
decisions file does not (#195). A `read_from_page_image` decision also changes its data row: re-run
the reader (Step 2) and `code/build_pdf_promoted.py --write`.

Each `parser_bug` means fixing the code, re-running Steps 2 and 5, and checking the item again.

## Step 8: record it on GitHub

- [ ] Post `ISSUE-LOG-DRAFT.md` on the year's issue, one comment per family, plus a status
      comment: rows, totals tied, flags, and what is still open.
- [ ] Add a `DATA-ANOMALIES.md` entry for each family, covering what the year taught us.
- [ ] Before posting, check every number against the files. Write `#5` only for issue 5: condition
      and chart numbers written as `#5` link to unrelated issues, so write them as `No. 5`.

## Step 9: close the year

A family is done when every item has a final decision:

```bash
.venv/bin/python code/validate_review_decisions.py --review <review csv> --decisions <decisions csv> --complete
# exit 0: every item has a final decision; 1: the decisions file is invalid;
# 2: something is still open, or decided needs_info
```

`--complete` counts `needs_info` as open: it lists each one with its check and page and exits 2.
Settle each by hand: change its `decision` in the decisions file to the final one, put the
answer in the note, and run `--sync` (`--add` never overwrites a committed decision). To close a
family with a `needs_info` left on purpose (for example, a question to Council Finance that has
waited 30 days), add `--allow-needs-info` and say why in the PR.

- [ ] A person changes the family's `status` from `reviewed` to `closed` in `data/pdf_years.csv`.
      Only a person does this.
- [ ] When every family of the year is closed, write the reflection on the year's issue: what
      worked, what didn't, what is odd about that year's PDFs, how to redo it, and time spent vs.
      the estimate. Then close the issue and tick the year in epic #101.

Once that is merged to `main`, the public explorer
(https://betanyc.github.io/New-York-City-Budget/explorer/) shows the family on its next deploy.

## Running a year with AI sessions

FY2027 to FY2018 were run as one background session per family, each in its own git worktree,
with a person integrating and reviewing. FY2027 and FY2026 started from `main`; FY2025 back to
FY2018 were one stack of PRs per family, each year on the one before, merged together by an
integrator. Epic #101 shows which years are in progress. The brief each session got had the
same parts:

- **Where:** the repo (public), the branch, what `main` already holds.
- **Goal:** the PDFs, with page counts, tier and known problems from `data/pdf_condition.csv` and
  the epic's year table.
- **Read first:** the epic, the year's issue, the posted logs of the last finished year, and that
  year's research folder as the model.
- **Do:** Steps 1 to 5 of this recipe, ending in a plain-language summary with PR links and the
  critical items, each with a suggested decision.
- **Rules:** commit, test, push and open PRs; never merge, force-push, commit to `main`, post on
  issues, or call Legistar or the Council site. Don't stop to ask: decide conservatively, flag it,
  and list "Decisions for the maintainer" in the PR. Stay inside your family; shared files
  (`data/pdf_years.csv`, `code/build_pdf_promoted.py`) get merged by the integrator.

The person integrating then does Step 6, runs the whole build and tests, and opens the review.
