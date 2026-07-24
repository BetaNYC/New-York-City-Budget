# FY2009 Transparency Resolutions — install & step-by-step run

A stage-by-stage walkthrough of the OCR pipeline
(`code/parse_transparency_reso_fy09.py` + `code/ocr/`), stopping after each stage to look
at what it produced before moving on. Every stage leaves an inspectable artifact under a
gitignored cache dir (`build/ocr/`), so you can validate the pipeline one step at a time.

Run everything from the repo root. On macOS `open <file>` opens an image in Preview; swap
for your viewer on Linux (`xdg-open`).

---

## 0. One-time setup

The OCR stack pulls in torch (~1–2 GB) and is deliberately kept out of the deterministic
parsers' `requirements.txt`, so it lives in its own virtualenv.

```bash
cd /Users/christianmoscardi/New-York-City-Budget

python3 -m venv .venv-ocr
.venv-ocr/bin/pip install --upgrade pip
.venv-ocr/bin/pip install -r code/requirements.txt -r code/requirements-ocr.txt
```

No system packages are needed: `pypdfium2` bundles its own PDF renderer and
`opencv-python-headless` needs no display libraries.

Confirm the environment and run the pure-logic tests (grid detection, header mapping,
validators — no model download, a few seconds):

```bash
.venv-ocr/bin/python -c "import doctr, cv2, pypdfium2, numpy; print('ocr env OK')"
.venv-ocr/bin/python -m pytest code/test_parse_transparency_reso_fy09.py -q
```

The first pipeline run downloads the docTR model weights (~100 MB) and caches them; later
runs are offline.

Set the shell variables used throughout:

```bash
SRC=source/FY09/transparency-resolutions
OUT=data/fy09/transparency-resolutions
STEM=Transparency-Reso-01-2008-08-14        # the resolution we'll walk through
```

For the council-member roster, **pass the glob directly** to `--roster-csv` (shown in the
commands below) rather than stashing it in a variable:

```bash
--roster-csv data/fy*/schedule_c/*_schedule_c_awards.csv
```

> **zsh gotcha (this repo's default shell):** do *not* do `ROSTER=$(ls …)` then
> `--roster-csv $ROSTER`. In **zsh**, an unquoted `$ROSTER` does **not** word-split, so all
> the newline-separated paths arrive as a *single* argument that matches no file — the
> parser then loads an empty roster and prints `roster: 1 names`. A glob passed straight to
> the flag expands to separate words in both zsh and bash, so it always works. (If you
> really want a variable, use a zsh array: `roster=(data/fy*/schedule_c/*_schedule_c_awards.csv)`
> then `--roster-csv $roster`.)

We validate on **one resolution** (`--only Transparency-Reso-01`) and a **page window**
(`--pages 1-14`) so each step is quick. That window covers the narrative pages, an EXHIBIT
divider, the dense `CHART 1: Local Initiatives` (≈ p.9), and the small
`Chart 4: Veterans Resource Center` that prints a `$500,000.00` total (≈ p.12) — and the
two charts happen to be rotated in *opposite* directions, which is exactly what stage 1
has to get right.

> Every command uses `--stage <name>`, which runs the pipeline **up to and including** that
> stage and then stops. Because each stage caches its output, re-running a later stage does
> not redo the earlier ones. Add `--force` to any command to recompute from scratch.

---

## Stage 0 — `render`: PDF pages → images

```bash
.venv-ocr/bin/python code/parse_transparency_reso_fy09.py \
    --only Transparency-Reso-01 --pages 1-14 \
    --batch $SRC --outdir $OUT --stage render
```

**Look at:** the raw page images, rendered 1:1 with the 300-dpi scan.

```bash
ls build/ocr/$STEM/raw/
open build/ocr/$STEM/raw/page-009.png build/ocr/$STEM/raw/page-012.png
```

You should see the scanned pages exactly as stored — the chart pages will be **sideways**
here (landscape tables on portrait sheets). That's expected; stage 1 fixes it.

---

## Stage 1 — `orient`: rotate upright + deskew + dewarp

Three corrections, cheapest first: a 90° turn, then a global deskew (single rotation
angle), then a **dewarp** that flattens residual page *bow* — the FY09 scans curve their
printed rules by several pixels across the page, which no rotation can straighten and which
is enough to defeat grid detection downstream (the ink of one rule smears across several
scanlines). Dewarp models the curvature from the rules themselves and remaps the page so
they become straight; it is a no-op on pages without enough rules (narrative/divider) and
on pages already flat.

```bash
.venv-ocr/bin/python code/parse_transparency_reso_fy09.py \
    --only Transparency-Reso-01 --pages 1-14 \
    --batch $SRC --outdir $OUT --stage orient
```

**Look at:** the corrected images, and the per-page decision log.

```bash
open build/ocr/$STEM/upright/page-009.png build/ocr/$STEM/upright/page-012.png
python3 -m json.tool build/ocr/$STEM/orient.json
```

Success criterion: **no page is sideways or upside-down.** `orient.json` records, per page,
`rotate90` (number of 90° counter-clockwise turns applied), `skew_deg`, the method used, and
`warp_max_dev_px` / `warp_applied` (how many pixels of bow the dewarp removed). Confirm that
the two chart pages got *different* `rotate90` values — proof the per-page detection is
doing its job, not applying a per-file constant — and that chart pages show a non-zero
`warp_max_dev_px`. To compare against un-dewarped output, re-run with `--no-dewarp --force`.

> **If a page came out wrong:** edit its `rotate90` (0/1/2/3) or `skew_deg` in
> `build/ocr/$STEM/orient.json`, then re-run this stage with `--force`. The hand value wins
> over detection (`method` becomes `override`), and all later stages pick it up.

> Orientation's upside-down tiebreak uses the docTR engine. If you pass `--no-engine` the
> rotation is axis-only (may be 180° off) — fine for eyeballing stages 0/3, not for a real run.

---

## Stage 2 — `classify`: what is each page?

```bash
.venv-ocr/bin/python code/parse_transparency_reso_fy09.py \
    --only Transparency-Reso-01 --pages 1-14 \
    --batch $SRC --outdir $OUT --stage classify
```

**Look at:** the page ledger.

```bash
column -s, -t build/ocr/$STEM/pages.csv
```

One row per page: `kind` (`narrative` / `divider` / `chart` / `blank`), the `rotate90` and
`skew_deg` from stage 1, and — for chart pages — the `chart_no` and `chart_title` read from
the caption above the table. Check that the CHART pages are labelled `chart` and their
titles read correctly (e.g. `Local Initiatives`, `Veterans Resource Center`); narrative and
EXHIBIT pages carry no chart data and are correctly *not* classified as charts.

---

## Stage 3 — `grid`: find the ruled cells

```bash
.venv-ocr/bin/python code/parse_transparency_reso_fy09.py \
    --only Transparency-Reso-01 --pages 1-14 \
    --batch $SRC --outdir $OUT --stage grid --debug
```

**Look at:** the grid overlays — this is the pipeline's most important visual check.

```bash
open build/ocr/$STEM/debug/page-009-grid.png    # dense ~40-row Chart 1
open build/ocr/$STEM/debug/page-012-grid.png    # small Chart 4
python3 -m json.tool build/ocr/$STEM/grid/page-009.json | head -20
```

Blue lines are detected column separators, red lines row separators, and each cell is
labelled `row,col`. Success: every printed rule has a matching line, no column is split or
merged, and the header is row 0. `grid.json` holds the raw separator coordinates.

A rule is detected as a connected COMPONENT whose bounding box spans ≥`MIN_SPAN_FRAC` of the
table (not by summing ink per scanline). That matters for the FY09 charts, whose interior
column rules are faint and wander a few pixels — their densest single column carries well
under half the height, so a per-scanline test drops them, but each is still one full-height
component. (This is what was collapsing the long-form charts to 2 columns.)

> If the grid is wrong (a faint rule missed, or speckle picked up as a line), the knobs are
> `--stage grid --debug --force` after adjusting the defaults in `code/ocr/grid.py`
> (`MIN_SPAN_FRAC`, `MERGE_TOL_PX`, `KERNEL_DIVISOR`). The overlay makes the effect obvious.

---

## Stage 4 — `ocr`: read the cells

```bash
.venv-ocr/bin/python code/parse_transparency_reso_fy09.py \
    --only Transparency-Reso-01 --pages 1-14 \
    --batch $SRC --outdir $OUT --stage ocr --debug
```

**Look at:** two overlays and the machine-readable dump.

```bash
open build/ocr/$STEM/debug/page-012-ocr.png                     # recognized text, per cell
open build/ocr/$STEM/debug/page-012-det.png                     # raw word detection boxes
python3 -m json.tool build/ocr/$STEM/cells/page-012.json | less
```

Two complementary views, both tinted green/**red** by confidence (`--min-conf`, default 0.80):

- **`-ocr.png`** writes the recognized text back into each cell — this is the *after*
  view, showing what text landed in which column.
- **`-det.png`** draws docTR's raw word boxes with the grid lines faint underneath — the
  *before* view. Use it to see detection directly: a box straddling a rule, a missed or
  merged word, or a word orphaned **outside** the lattice (a box in no cell — e.g. the
  header row, which is meant to sit above the grid).

`cells/page-NNN.json` lists every non-empty cell (`row, col, text, conf`), the resolved
`columns` mapping (which grid column became `ein`, `amount`, …), and any `orphans` (words
that landed outside the lattice). This stage does **not** write the CSVs — it's purely for
validating recognition. Spot-check that the EINs and dollar amounts in `page-012.json`
match the pixels in `page-012-ocr.png`.

---

## Stage 5/6 — `assemble`: cells → schema rows + review queue

(Header mapping, stage 5, runs inside assembly; there is no separate `--stage headers`.)

```bash
.venv-ocr/bin/python code/parse_transparency_reso_fy09.py \
    --only Transparency-Reso-01 --pages 1-14 \
    --batch $SRC --outdir $OUT --stage assemble
```

**Look at:** the emitted rows, the FY09-only sidecar, and the human-review queue.

```bash
column -s, -t $OUT/reso01_transparency_designations.csv | less -S
column -s, -t $OUT/fy09_transparency_fiscal_conduits.csv | less -S
column -s, -t $OUT/fy09_transparency_needs_review.csv | less -S
open $OUT/review-crops/            # cropped pixels for each flagged cell
```

Check: rows are in the standard 16-column schema; the `flags` column carries `ocr:*` codes
only where a value failed validation; rescissions have negative `amount` and
`action=rescind`; the `Fiscal Conduit` / `Status` columns landed in the sidecar (not the
main file). Every flagged cell has a matching crop under `review-crops/` so you can confirm
the value against the original pixels.

---

## Stage 7 — `report`: reconciliation + OCR quality

```bash
.venv-ocr/bin/python code/parse_transparency_reso_fy09.py \
    --only Transparency-Reso-01 --pages 1-14 \
    --batch $SRC --outdir $OUT --stage report
```

**Look at:**

```bash
cat $OUT/fy09_transparency_reconciliation.txt
```

Key lines: the **printed-total checks** (Chart 4 should reconcile to `$500,000.00`
*exactly* — the strongest evidence the OCR read the numbers right), the page accounting,
and the **OCR quality band** (HIGH / MODERATE / LOW) with per-flag counts and the size of
the review queue.

---

## Full run (all 8 resolutions, every page)

Once the single-resolution walkthrough looks right, drop `--only` and `--pages` and let the
default `--stage report` run the whole pipeline end to end:

```bash
.venv-ocr/bin/python code/parse_transparency_reso_fy09.py \
    --batch $SRC --outdir $OUT --prefix fy09 \
    --roster-csv data/fy*/schedule_c/*_schedule_c_awards.csv
```

Then run the repo-wide validator (from the plain `.venv`, or `.venv-ocr` — it has no OCR
deps) and read the FY09 result:

```bash
.venv-ocr/bin/python code/validate_data.py
```

Expected: FY09's new files produce **0 hard schema failures** (exactly 16 columns, valid
EINs, correct transparency sign rules), and `fy09_transparency_reconciliation.txt` shows
the printed-total charts reconciling exactly. Fill the row counts, reconciliation result,
and confidence band into `code/PARSING.md` (the "OCR pipeline" section still says *not yet
run*).

---

## Cheat sheet

| stage | command `--stage` | inspect |
|---|---|---|
| 0 render | `render` | `build/ocr/<stem>/raw/*.png` |
| 1 orient | `orient` | `build/ocr/<stem>/upright/*.png`, `orient.json` |
| 2 classify | `classify` | `build/ocr/<stem>/pages.csv` |
| 3 grid | `grid --debug` | `build/ocr/<stem>/debug/*-grid.png`, `grid/*.json` |
| 4 ocr | `ocr --debug` | `build/ocr/<stem>/debug/*-ocr.png`, `cells/*.json` |
| 6 assemble | `assemble` | `data/fy09/.../reso*.csv`, `*_needs_review.csv`, `review-crops/` |
| 7 report | `report` (default) | `data/fy09/.../fy09_transparency_reconciliation.txt` |

Useful flags: `--only <substr>` (one PDF), `--pages 9-12,20` (page window), `--force`
(ignore cache), `--min-conf 0.85` (stricter flagging), `--no-engine` (skip docTR for
stages 0–3), `--no-dewarp` (skip the orient dewarp, for A/B), `--cache-dir <dir>` (default
`build/ocr`).
