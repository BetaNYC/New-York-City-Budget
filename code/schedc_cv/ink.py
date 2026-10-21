"""
Stage 6 -- ink coverage, the dropped-content check (PLAN §3, H9).

Schedule C prints no award total, so nothing in the arithmetic can see a row that was never
emitted. Ink can. The question: is every inked pixel inside an award table accounted for by
a character we emitted (or a header label we classified) or by a drawn rule?

  ink      = rendered page < 128 (Christian's fixed threshold, `grid.binarize`)
  measured = the vector bbox of every award table on the page
  covered  = the box of every emitted or header character, padded by `char_pad_px`
             + every dark filled rect and stroked line from the PDF's own vector graphics,
               drawn at its true size, padded by `rule_pad_px` (born-digital pages give exact
               rule geometry, so Christian's `rule_pixels` heuristic for scans is not needed)
  leftover = ink - covered, grouped into reportable regions

`find_uncovered_regions` and `_tight_bbox` are ported from Christian Moscardi's
`nyc_executive_orders/vlm_ocr.py` (BetaNYC/nyc-executive-orders @ 84df8193, MIT; his commit
851045c6, 2026-09-08), unchanged except that the two module constants they read are passed in.
His docstring: ink coverage is "the only QA signal here that can see *dropped* content."
"""
import math

import numpy as np

# Christian's values at 200 dpi were cell_px 24, min_region_ink 400. At 300 dpi the same
# physical size is 36 px and 900 px (area scales with dpi squared). Re-measured on FY2027 in
# the acceptance run (see the module's test and checks.txt).
CELL_PX = 36
MIN_REGION_INK = 900
UNCOVERED_CELL_MIN_INK_FRACTION = 0.025   # his constant
MAX_UNCOVERED_REGIONS = 12                # his constant


def find_uncovered_regions(uncovered, cell_px, min_region_ink, offset,
                           min_ink_fraction=UNCOVERED_CELL_MIN_INK_FRACTION,
                           max_regions=MAX_UNCOVERED_REGIONS):
    """Group leftover ink pixels into a handful of reportable rectangles (ported; see module
    docstring). Grouping works on a coarse grid: a cell counts as inked once it holds enough
    ink to be type rather than speckle, adjacent inked cells are merged, and a merged group has
    to carry min_region_ink pixels before it is reported. The reported box is shrunk back onto
    the group's own ink. Returned bboxes are in full-page pixels; offset is the ROI's corner."""
    h, w = uncovered.shape
    if h == 0 or w == 0:
        return []
    grid_h, grid_w = math.ceil(h / cell_px), math.ceil(w / cell_px)
    padded = np.zeros((grid_h * cell_px, grid_w * cell_px), dtype=np.int32)
    padded[:h, :w] = uncovered
    cells = padded.reshape(grid_h, cell_px, grid_w, cell_px).sum(axis=(1, 3))
    hot = cells >= max(1, int(cell_px * cell_px * min_ink_fraction))
    seen = np.zeros_like(hot, dtype=bool)
    regions = []
    for row in range(grid_h):
        for col in range(grid_w):
            if not hot[row, col] or seen[row, col]:
                continue
            stack, group = [(row, col)], []
            seen[row, col] = True
            while stack:
                r, c = stack.pop()
                group.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < grid_h and 0 <= nc < grid_w and hot[nr, nc] and not seen[nr, nc]:
                        seen[nr, nc] = True
                        stack.append((nr, nc))
            rows = np.array([p[0] for p in group])
            cols = np.array([p[1] for p in group])
            ink_px = int(cells[rows, cols].sum())
            if ink_px < min_region_ink:
                continue
            bbox = _tight_bbox(uncovered, rows, cols, cell_px, offset)
            if bbox is None:
                continue
            regions.append({"bbox": bbox, "ink_px": ink_px})
    regions.sort(key=lambda r: r["ink_px"], reverse=True)
    return regions[:max_regions]


def _tight_bbox(uncovered, rows, cols, cell_px, offset):
    """The smallest full-page box holding this group's ink, and nothing else (ported)."""
    off_x, off_y = offset
    r0, r1 = int(rows.min()), int(rows.max()) + 1
    c0, c1 = int(cols.min()), int(cols.max()) + 1
    owned = np.zeros((r1 - r0, c1 - c0), dtype=bool)
    owned[rows - r0, cols - c0] = True
    owned = np.kron(owned, np.ones((cell_px, cell_px), dtype=bool))
    y0, x0 = r0 * cell_px, c0 * cell_px
    patch = uncovered[y0:y0 + owned.shape[0], x0:x0 + owned.shape[1]]
    ys, xs = np.nonzero(patch & owned[:patch.shape[0], :patch.shape[1]])
    if ys.size == 0:
        return None
    return [int(off_x + x0 + xs.min()), int(off_y + y0 + ys.min()),
            int(off_x + x0 + xs.max() + 1), int(off_y + y0 + ys.max() + 1)]


def _dark(color):
    """pdfplumber colour -> True if it renders darker than mid-grey."""
    if color is None:
        return True
    if isinstance(color, (int, float)):
        return color < 0.5
    c = list(color)
    if len(c) == 1:
        return c[0] < 0.5
    if len(c) == 3:
        return sum(c) / 3 < 0.5
    if len(c) == 4:  # CMYK
        return (1 - min(1, c[0] + c[3])) * 0.3 + (1 - min(1, c[1] + c[3])) * 0.59 + \
            (1 - min(1, c[2] + c[3])) * 0.11 < 0.5
    return True


def rule_shapes(page):
    """Every dark vector mark on a pdfplumber page, as (x0, top, x1, bottom) in pt."""
    out = []
    for r in page.rects:
        if r.get("fill") and _dark(r.get("non_stroking_color")):
            out.append((r["x0"], r["top"], r["x1"], r["bottom"]))
        if r.get("stroke") and _dark(r.get("stroking_color")):
            lw = (r.get("linewidth") or 1) / 2
            x0, t, x1, b = r["x0"], r["top"], r["x1"], r["bottom"]
            out += [(x0 - lw, t - lw, x1 + lw, t + lw), (x0 - lw, b - lw, x1 + lw, b + lw),
                    (x0 - lw, t - lw, x0 + lw, b + lw), (x1 - lw, t - lw, x1 + lw, b + lw)]
    for ln in page.lines:
        if _dark(ln.get("stroking_color")):
            lw = (ln.get("linewidth") or 1) / 2
            out.append((ln["x0"] - lw, ln["top"] - lw, ln["x1"] + lw, ln["bottom"] + lw))
    return out


def coverage(gray, dpi, table_boxes, char_boxes, rules, char_pad_px, rule_pad_px,
             cell_px=CELL_PX, min_region_ink=MIN_REGION_INK):
    """Uncovered-ink regions inside the award tables of one page.
    Returns dict(ink_px, uncovered_px, regions=[{bbox_pt, ink_px}])."""
    s = dpi / 72.0
    H, W = gray.shape
    ink = gray < 128
    roi = np.zeros_like(ink)
    covered = np.zeros_like(ink)

    def px(b, pad):
        return (max(0, int(math.floor(b[0] * s)) - pad), max(0, int(math.floor(b[1] * s)) - pad),
                min(W, int(math.ceil(b[2] * s)) + pad), min(H, int(math.ceil(b[3] * s)) + pad))

    for b in table_boxes:
        x0, y0, x1, y1 = px(b, 0)
        roi[y0:y1, x0:x1] = True
    for b in char_boxes:
        x0, y0, x1, y1 = px(b, char_pad_px)
        covered[y0:y1, x0:x1] = True
    for b in rules:
        x0, y0, x1, y1 = px(b, rule_pad_px)
        covered[y0:y1, x0:x1] = True
    measured = ink & roi
    left = measured & ~covered
    regions = []
    if left.any():
        ys, xs = np.nonzero(roi)
        oy, ox = int(ys.min()), int(xs.min())
        sub = left[oy:int(ys.max()) + 1, ox:int(xs.max()) + 1]
        for r in find_uncovered_regions(sub, cell_px, min_region_ink, (ox, oy)):
            regions.append(dict(bbox_pt=[round(v / s, 2) for v in r["bbox"]], ink_px=r["ink_px"]))
    return dict(ink_px=int(measured.sum()), uncovered_px=int(left.sum()), regions=regions)
