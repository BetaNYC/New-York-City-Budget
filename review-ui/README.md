# review-ui — Schedule C extraction review

A local tool for answering one question about any row in this repo: **is it right, and how do we
know?** It puts the source PDF page beside the rows extracted from it, shows every QA flag, and
traces a single row back through each stage of the pipeline that produced it.

Vite + vanilla JS + PDF.js. No network, no build server, no data leaves the machine.

## Run it

```bash
cd review-ui
npm install
python3 build_index.py       # ~40s per fiscal year; writes public/data/
npm run dev                  # http://localhost:5180
```

`build_index.py` takes `--year 2016` to do one year. Start there — the full corpus is ~27 MB of
JSON and takes several minutes.

From the workspace repo the dev server is also registered in `.claude/launch.json` as
`schedule-c-review-ui`. That entry uses a path relative to the main checkout; **from inside a git
worktree** the prefix needs four levels (`../../../../New-York-City-Budget/review-ui`).

## What each tab is for

**Page review** — the source page rendered on the left, the rows attributed to it on the right.
Click any row for the stage-by-stage trace. Two filters narrow the page list to pages that produced
rows, or to pages that produced *defective* rows. Arrow keys page through.

The collapsed **"Text layer the parser read"** panel under the PDF is the honest one: it shows the
pypdf output the parser actually consumed. When a page clearly prints award rows and produced none,
the answer is usually visible there.

**QA metrics** — defects and observations separately (see below), page-attribution rates, rows per
stream, and the parser's own reconciliation notes verbatim.

**Pipeline** — the six stages from PDF to QA verdict, each with the number it produced for this
year, and why that stage can fail.

**Unplaced rows** — rows whose `(EIN, amount)` pair is printed on no page of the PDF. Each is either
a row whose amount changed after extraction, or evidence the page attribution is wrong.

## Two things it is careful about

**Defects and observations are not the same thing.** A defect is a field that is wrong
(`org_merged`, `org_prose`, `org_blank`). An observation is a field that is empty for a reason the
schema allows — a citywide initiative row has no sponsoring member, so `member_blank` is correct
there. Only defects count against "clean". Conflating them scored FY2016 at 0% clean when its
organization fields were 97.6% sound.

**Page attribution is evidence, not certainty.** The CSVs carry no page number, so `build_index.py`
reconstructs it: it re-runs the parser's own `ANCHOR` over each page in isolation and matches the
`(EIN, amount)` pairs it finds against the committed rows. Where a pair is printed on more than one
page, **every** candidate is recorded and the row is marked ambiguous in the UI rather than silently
assigned to the first. FY2027 places all 9,978 rows; FY2016 places 333 of 335.

## It reuses the repo's own code, deliberately

`build_index.py` imports `ANCHOR`, `money()` and `eind()` from `code/parse_schedule_c.py`, and the
flag detectors from `code/validate_data.py`. It does not re-implement either. A review tool that
disagrees with the thing it reviews is worse than no review tool — so when the parser changes, this
view changes with it, including in the ways that are wrong.

## What it will show you today

FY2016's QA tab reports `appendix_a_aging 0`, `appendix_b_local 0`, `appendix_c_youth 0` against 213
appendix pages in the source document. That is
[#59](https://github.com/BetaNYC/New-York-City-Budget/issues/59) — the anchor required a `$` those
years do not print — rendered as a bar chart.

`public/data/` is gitignored: it is derived from `source/` and `data/`, and regenerates in minutes.
