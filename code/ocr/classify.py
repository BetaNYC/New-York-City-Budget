"""
Stage 2 -- decide what each page is, and read the chart caption off the chart pages.

An FY09 resolution is roughly: ~5 pages of narrative report and the resolution text, then
alternating `EXHIBIT A` .. `EXHIBIT V` divider sheets and the chart pages that carry the
actual designations. Only chart pages produce rows, but every page is classified and
recorded so page accounting is complete and a missed chart page is visible rather than
silent.

The classifier leans on the same ruled-line evidence grid.py uses, but only COUNTS the
rules — it does not build the cell lattice. A chart page is the only kind with a printed
ruled table, so "enough horizontal and vertical rules" is decisive. Stage 3
(grid.detect_grid) then extracts the exact cells from the pages this flags as charts. That
ordering is deliberate: deciding what a page IS (stage 2) must not depend on stage 3's
lattice, or the two stages collapse into one.
"""
import re

from . import grid as _grid

CHART_CAPTION = re.compile(r"(?i)\bCHART\s*#?\s*(\d+)\s*[:.\-]\s*(.+)$")
CONTINUED = re.compile(r"\s*\(?\s*continued\s*\)?\s*$", re.I)

# A chart carries a rule between every data row and every column, so it has many of both.
# Thresholds mirror the old lattice gate (≥4 rows → ≥5 horizontal separators; ≥3 columns →
# ≥4 vertical separators), just expressed as rule counts instead of cell counts.
MIN_TABLE_HRULES = 5
MIN_TABLE_VRULES = 4
DIVIDER_MAX_COMPONENTS = 30    # an EXHIBIT sheet is a handful of large glyphs, nothing else
DIVIDER_MIN_GLYPH_FRAC = 0.03  # ...set in very large display type

KIND_CHART = "chart"
KIND_DIVIDER = "divider"
KIND_NARRATIVE = "narrative"
KIND_BLANK = "blank"


def ink_fraction(gray):
    import numpy as np
    return float((gray < 128).mean()) if gray.size else 0.0


def _glyph_stats(gray):
    """(component count, tallest component's height fraction of page height).

    Component COUNT, not raw ink density, is what separates a divider page from a
    narrative one: a page of body text breaks into hundreds of small components (letters,
    words, punctuation) regardless of how bold the font is, while an `EXHIBIT I` sheet is a
    handful of large ones. Ink fraction alone is the wrong signal here -- it scales with
    stroke weight, so a heavier caption font can push a divider's ink density above any
    fixed ratio and get it misread as narrative.
    """
    import cv2
    import numpy as np
    ink = ((gray < 128).astype(np.uint8)) * 255
    n, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    if n <= 1:
        return 0, 0.0
    heights = stats[1:, cv2.CC_STAT_HEIGHT]
    return int(n - 1), float(heights.max()) / max(1, gray.shape[0])


def classify_page(gray):
    """Return one of KIND_*, from cheap page-level evidence only — no cell lattice.

    Chart pages are decided by rule COUNT (grid.count_rules), not by stage 3's extracted
    lattice, so this stage stands alone. A page classified `chart` here that then yields no
    recoverable lattice in stage 3 is a useful disagreement — a table we could not parse —
    rather than being silently reclassified.
    """
    n_h, n_v = _grid.count_rules(gray)
    if n_h >= MIN_TABLE_HRULES and n_v >= MIN_TABLE_VRULES:
        return KIND_CHART
    if ink_fraction(gray) < 0.0005:
        return KIND_BLANK
    n_components, tallest_frac = _glyph_stats(gray)
    if n_components <= DIVIDER_MAX_COMPONENTS and tallest_frac >= DIVIDER_MIN_GLYPH_FRAC:
        return KIND_DIVIDER
    return KIND_NARRATIVE


def caption_strip(gray, grid, margin=10):
    """The band above the table, where the `CHART n: Title` caption is printed."""
    top = max(0, grid.ys[0] - margin)
    return gray[0:top, :] if top > 20 else None


def read_caption(engine, gray, grid):
    """(chart_no, chart_title) from the caption above the table, or ('', '').

    The title is the `chart` column's value and must match the other years' spelling, so a
    trailing '(continued)' is stripped exactly as parse_transparency_reso.py does.
    """
    strip = caption_strip(gray, grid)
    if strip is None or strip.size == 0 or engine is None:
        return "", ""
    words = engine.words(strip)
    if not words:
        return "", ""
    line = " ".join(w["text"] for w in sorted(words, key=lambda w: (w["bbox"][1], w["bbox"][0])))
    m = CHART_CAPTION.search(line)
    if not m:
        return "", ""
    title = CONTINUED.sub("", m.group(2)).strip()
    return m.group(1), re.sub(r"\s+", " ", title)
