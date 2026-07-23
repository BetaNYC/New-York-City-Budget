#!/usr/bin/env python3
"""
Parse the FY2009 Transparency Resolutions -- which are SCANS -- into the repo's standard
Transparency-Resolution CSVs.

Every other year (FY10-FY27) is read deterministically from the PDF's own text layer by
`parse_transparency_reso.py`. The eight FY2009 documents have no text layer at all: they
are 300-dpi bitonal Xerox scans, and their data pages are landscape tables rotated onto
portrait sheets -- in BOTH directions, varying page to page within a single file. They
were the last structural gap in this repo's Transparency-Resolution coverage.

This script runs the OCR pipeline in `code/ocr/`:

    render -> orient (90deg + deskew) -> classify -> grid -> OCR -> assemble -> report

The tables are fully ruled, so cell boundaries are read off the printed rules and column
identity comes from geometry rather than from regex-guessing at a reflowed line. That is
what makes this output *cleaner* than the FY10-FY13 text-layer years, whose glued words
and header bleed are documented in PARSING.md.

HONESTY: the figures here are MODEL-READ. They are validated by shape checks, an agency-code
dictionary built from the already-parsed years, and -- uniquely for FY09 -- an exact check
against the totals some charts print. Anything that fails is flagged in the `flags` column
and listed in `*_needs_review.csv` with a crop of the original pixels. Nothing uncertain is
shipped as if it were exact.

Requires the separate OCR environment (torch is not a dependency of the other parsers):

    python3 -m venv .venv-ocr
    .venv-ocr/bin/pip install -r code/requirements.txt -r code/requirements-ocr.txt

Emits (to --outdir, prefixed with --prefix):
  resoNN_transparency_designations.csv   the standard 16-column schema
  *_transparency_all.csv                 all resolutions combined
  *_transparency_fiscal_conduits.csv     FY09-only Fiscal Conduit / Status columns
  *_transparency_needs_review.csv        the human-review queue, with cell crops
  *_transparency_reconciliation.txt      printed-total checks + OCR quality band
  (cache) build/ocr/<stem>/              page images, orientation, grids, debug overlays
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import parse_transparency_reso as tr                      # noqa: E402
from ocr import assemble, classify, grid as gridmod, headers, orient, recognize, render, report  # noqa: E402

STAGES = ["render", "orient", "classify", "grid", "ocr", "assemble", "report"]
DEFAULT_CACHE = "build/ocr"


def _upto(stage):
    return STAGES[:STAGES.index(stage) + 1]


def _imread(path):
    import cv2
    return cv2.imread(path, cv2.IMREAD_GRAYSCALE)


def _imwrite(path, img):
    import cv2
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, img)


def _cells_from_words(word_cells, grid):
    """{(r,c): Cell} for every cell in the lattice, empty ones included."""
    from ocr.recognize import cell_text
    out = {}
    for r in range(grid.nrows):
        for c in range(grid.ncols):
            words = word_cells.get((r, c), [])
            text, conf = cell_text(words)
            out[(r, c)] = assemble.Cell(text, conf, grid.cell(r, c))
    return out


def _reread_failing_numerics(engine, gray, cells, mapping, grid):
    """Targeted second look at numeric cells that failed their validator.

    Detection over a whole 300-dpi page can clip a thin digit or merge a comma into a
    neighbour. Re-reading just the failing cell, cropped inside its rules and upscaled, is
    cheap because it skips detection entirely -- and it only ever fires on a value we have
    already decided we do not trust.
    """
    from ocr import recognize
    checks = {"ein": lambda t: assemble.parse_ein(t)[1],
              "conduit_ein": lambda t: assemble.parse_ein(t)[1],
              "amount": lambda t: assemble.parse_amount(t)[1],
              "agy_num": lambda t: bool(assemble.CODE_RE.match(assemble.normalize_numeric(t))),
              "ua": lambda t: bool(assemble.CODE_RE.match(assemble.normalize_numeric(t)))}
    fixed = 0
    for field, ok in checks.items():
        col = mapping.get(field)
        if col is None:
            continue
        for r in range(1, grid.nrows):
            cell = cells.get((r, col))
            if cell is None or not cell.text.strip() or ok(cell.text):
                continue
            got = recognize.reread_cell(engine, gray, cell.rect)
            if got and ok(got[0]):
                cells[(r, col)] = assemble.Cell(got[0], got[1], cell.rect)
                fixed += 1
    return fixed


def process_pdf(pdf, cache_dir, outdir, prefix, roster, agency_vocab, engine,
                stages, pages=None, debug=False, force=False, min_conf=None,
                do_dewarp=True):
    """Run the pipeline over one resolution PDF. Returns (resolution, date, assembler,
    page_kinds, confidences)."""
    stem = os.path.splitext(os.path.basename(pdf))[0]
    m = tr.FNAME.search(stem)
    if not m:
        raise SystemExit(f"cannot derive resolution number/date from filename: {stem}")
    resolution, date = int(m.group(1)), m.group(2)

    crop_dir = os.path.join(outdir, "review-crops")
    upright_cache = {}

    asm = assemble.Assembler(resolution, date, roster, agency_vocab,
                             min_conf=min_conf or assemble.DEFAULT_MIN_CONF,
                             crop_dir=crop_dir,
                             gray_provider=lambda p: upright_cache.get(p))

    rendered = render.render_pdf(pdf, cache_dir, pages=pages, force=force)
    if "orient" not in stages:
        return resolution, date, asm, {}, []

    orient_path = os.path.join(cache_dir, stem, "orient.json")
    records = orient.load_records(orient_path)
    page_kinds, confidences = {}, []
    captions = {}                       # page_no -> (chart_no, chart_title)
    chart_title, chart_mappings = "", {}

    for page_no, raw_path in rendered:
        upright_path = render.page_png(cache_dir, stem, page_no, "upright")
        if os.path.exists(upright_path) and not force and page_no in records:
            up = _imread(upright_path)
        else:
            gray = _imread(raw_path)
            up, rec = orient.orient_page(gray, engine, override=records.get(page_no),
                                         do_dewarp=do_dewarp)
            records[page_no] = rec
            _imwrite(upright_path, up)
        upright_cache[page_no] = up

        # Stage 2 -- what KIND of page is this? Rule counts only, no cell lattice, so this
        # decision stands on its own and does not pull stage 3 forward.
        if "classify" not in stages:
            continue
        kind = classify.classify_page(up)
        page_kinds[(resolution, page_no)] = kind
        if kind != classify.KIND_CHART or "grid" not in stages:
            continue

        # Stage 3 -- extract the exact cell lattice, only on the chart pages stage 2 flagged.
        g = gridmod.detect_grid(up)
        if g is None:
            # Classified chart, but no lattice recovered: a real disagreement worth seeing,
            # not something to hide by reclassifying the page.
            print(f"  ! reso {resolution:02d} p{page_no}: classified chart but no cell "
                  f"lattice recovered -- 0 rows from this page")
            continue
        g.save(_ensure(os.path.join(cache_dir, stem, "grid", f"page-{page_no:03d}.json")))
        if debug:
            _imwrite(os.path.join(cache_dir, stem, "debug", f"page-{page_no:03d}-grid.png"),
                     gridmod.draw_overlay(up, g))

        chart_no, title = classify.read_caption(engine, up, g)
        # Continuation pages of a long chart repeat the table but not always the caption;
        # carry the last one forward so their rows land under the right chart.
        chart_title = title or chart_title
        captions[page_no] = (chart_no, chart_title)
        if "ocr" not in stages:
            continue

        page_words = engine.words(up)
        word_cells, orphans = recognize.assign_words(page_words, g)
        cells = _cells_from_words(word_cells, g)
        confidences.extend(c.conf for c in cells.values() if c.text.strip())

        # The header is printed ABOVE the ruled area (no top border), so it is not grid row 0
        # -- row 0 is the first data row. Reconstruct the header from the band above the grid.
        header_texts = recognize.header_row_texts(page_words, g)
        widths = [g.xs[c + 1] - g.xs[c] for c in range(g.ncols)]
        mapping = headers.map_header(header_texts, widths, up.shape[1])
        if not mapping.ok:
            cached = chart_mappings.get(chart_title)
            if cached is not None and cached.ok:
                mapping = cached
            else:
                asm.reviews.append({
                    "resolution": resolution, "page": page_no, "row": 0,
                    "column": "header", "raw_text": " | ".join(header_texts),
                    "confidence": "", "flag": "ocr:header",
                    "crop": "",
                })
                _dump_cells(cache_dir, stem, page_no, chart_title, None, cells, g, orphans)
                print(f"  ! reso {resolution:02d} p{page_no}: header unmapped "
                      f"(missing {mapping.missing}) -- page skipped, queued for review")
                continue
        chart_mappings.setdefault(chart_title, mapping)

        _reread_failing_numerics(engine, up, cells, mapping, g)
        # Persist the recognized cells so stage 4 can be inspected without re-running OCR.
        _dump_cells(cache_dir, stem, page_no, chart_title, mapping, cells, g, orphans)
        if debug:
            texts = {rc: c.text for rc, c in cells.items()}
            confs = {rc: c.conf for rc, c in cells.items()}
            _imwrite(os.path.join(cache_dir, stem, "debug", f"page-{page_no:03d}-ocr.png"),
                     recognize.draw_ocr_overlay(up, g, texts, confs, low_conf=min_conf or 0.80))
            _imwrite(os.path.join(cache_dir, stem, "debug", f"page-{page_no:03d}-det.png"),
                     recognize.draw_detection_overlay(up, page_words, g,
                                                      low_conf=min_conf or 0.80))
        if "assemble" in stages:
            asm.add_page(page_no, chart_title, cells, mapping, g)

    orient.save_records(orient_path, records)
    _dump_pages_csv(cache_dir, stem, page_kinds, captions, records)
    return resolution, date, asm, page_kinds, confidences


def _dump_cells(cache_dir, stem, page_no, chart_title, mapping, cells, grid, orphans):
    """Persist stage 4 output for one page: every cell's recognized text, confidence and
    box, plus the resolved column mapping and any words that fell outside the lattice. This
    is the inspectable artifact for the OCR stage -- `--stage ocr` writes it without touching
    the CSVs, so the recognition can be checked cell by cell."""
    import json
    payload = {
        "chart": chart_title,
        "nrows": grid.nrows,
        "ncols": grid.ncols,
        "columns": (mapping.columns if mapping is not None else {}),
        "header_missing": (mapping.missing if mapping is not None else ["<unmapped>"]),
        "cells": [
            {"row": r, "col": c, "text": cells[(r, c)].text,
             "conf": round(float(cells[(r, c)].conf), 4)}
            for r in range(grid.nrows) for c in range(grid.ncols)
            if cells[(r, c)].text.strip()
        ],
        "orphans": [{"text": w["text"], "conf": round(float(w["conf"]), 4),
                     "bbox": list(w["bbox"])} for w in orphans],
    }
    path = _ensure(os.path.join(cache_dir, stem, "cells", f"page-{page_no:03d}.json"))
    with open(path, "w") as f:
        json.dump(payload, f, indent=1)


def _dump_pages_csv(cache_dir, stem, page_kinds, captions, records):
    """The per-PDF page ledger: kind, detected 90deg turn + skew, and the chart caption.
    Small enough to eyeball, and the first place to look when a chart page went missing."""
    path = os.path.join(cache_dir, stem, "pages.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["resolution", "page", "kind", "rotate90", "skew_deg",
                    "chart_no", "chart_title"])
        for (res, page), kind in sorted(page_kinds.items()):
            rec = records.get(page, {})
            chart_no, title = captions.get(page, ("", ""))
            w.writerow([res, page, kind, rec.get("rotate90", ""),
                        rec.get("skew_deg", ""), chart_no, title])


def _ensure(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", nargs="?", help="single resolution PDF (omit with --batch)")
    ap.add_argument("--batch", metavar="SRCDIR", help="directory of Transparency-Reso-*.pdf")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--prefix", default="fy09")
    ap.add_argument("--roster-csv", nargs="*", default=[tr.default_roster()],
                    help="Schedule C awards CSV(s) supplying the council-member roster")
    ap.add_argument("--data-root", default="data",
                    help="root of the parsed data tree, for the agency-code vocabulary")
    ap.add_argument("--cache-dir", default=DEFAULT_CACHE)
    ap.add_argument("--stage", choices=STAGES, default="report",
                    help="run stages up to and including this one (default: the whole pipeline)")
    ap.add_argument("--pages", help="restrict to page numbers, e.g. 9-12,20")
    ap.add_argument("--only", help="substring filter on the PDF filename")
    ap.add_argument("--min-conf", type=float, default=assemble.DEFAULT_MIN_CONF)
    ap.add_argument("--debug", action="store_true", help="write grid-overlay PNGs")
    ap.add_argument("--force", action="store_true", help="ignore cached page images")
    ap.add_argument("--no-engine", action="store_true",
                    help="skip docTR entirely (stages 0-3 only; orientation is axis-only)")
    ap.add_argument("--no-dewarp", action="store_true",
                    help="skip the dewarp step in orient (for A/B against warped output)")
    args = ap.parse_args()

    if not args.batch and not args.pdf:
        ap.error("give a PDF or --batch SRCDIR")

    stages = _upto(args.stage)
    os.makedirs(args.outdir, exist_ok=True)

    pdfs = ([args.pdf] if args.pdf else
            [os.path.join(args.batch, f) for f in sorted(os.listdir(args.batch))
             if f.lower().endswith(".pdf") and "-dup" not in f.lower()])
    if args.only:
        pdfs = [p for p in pdfs if args.only in os.path.basename(p)]
    if not pdfs:
        raise SystemExit("no PDFs to process")

    # The engine is needed from stage 1 onward (orientation's 180deg tiebreak), not just
    # for stage 4, so build it unless the caller explicitly opted out.
    engine = None
    if not args.no_engine:
        from ocr.recognize import Engine
        engine = Engine()

    roster = tr.load_schedule_c_roster(args.roster_csv)
    agency_vocab = assemble.load_agency_vocab(assemble.discover_agency_sources(args.data_root))
    print(f"roster: {len(roster)} names   agency vocabulary: {len(agency_vocab)} codes")

    per_reso, all_rows, all_reviews, all_conduits = [], [], [], []
    page_kinds, confidences = {}, []
    hits = misses = 0

    for pdf in pdfs:
        print(f"[{os.path.basename(pdf)}]")
        resolution, date, asm, kinds, confs = process_pdf(
            pdf, args.cache_dir, args.outdir, args.prefix, roster, agency_vocab, engine,
            stages, pages=render.parse_page_spec(args.pages), debug=args.debug,
            force=args.force, min_conf=args.min_conf, do_dewarp=not args.no_dewarp)
        page_kinds.update(kinds)
        confidences.extend(confs)
        hits += asm.member_hits
        misses += asm.member_misses
        per_reso.append((resolution, date, asm.rows, asm.totals))
        all_rows.extend(asm.rows)
        all_reviews.extend(asm.reviews)
        all_conduits.extend(asm.conduits)
        if "assemble" in stages:
            out = os.path.join(args.outdir, f"reso{resolution:02d}_transparency_designations.csv")
            tr.write_csv(out, asm.rows)
            print(f"  -> {out}  ({len(asm.rows)} rows)")

    if "assemble" not in stages:
        print(f"stopped after stage '{args.stage}'")
        return

    tr.write_csv(os.path.join(args.outdir, f"{args.prefix}_transparency_all.csv"), all_rows)
    assemble.write_sidecar(
        os.path.join(args.outdir, f"{args.prefix}_transparency_fiscal_conduits.csv"),
        assemble.CONDUIT_COLS, all_conduits)
    assemble.write_sidecar(
        os.path.join(args.outdir, f"{args.prefix}_transparency_needs_review.csv"),
        assemble.REVIEW_COLS, all_reviews)

    if "report" in stages:
        text = report.build_report(args.prefix, per_reso, all_rows, all_reviews,
                                   page_kinds, confidences, args.min_conf, hits, misses)
        path = os.path.join(args.outdir, f"{args.prefix}_transparency_reconciliation.txt")
        with open(path, "w") as f:
            f.write(text)
        print(text)


if __name__ == "__main__":
    main()
