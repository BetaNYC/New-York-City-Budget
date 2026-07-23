"""
Stage 3 -- recover a table's cell rectangles from its printed rules.

The FY09 chart pages are FULLY RULED: every cell has a visible border. That makes a
classical morphological pass strictly better than any learned table model here -- the
separators are literally drawn on the page, so cell boundaries are read off the ink rather
than predicted. Column identity then comes from geometry, which is what keeps the
organization/member text from bleeding between columns the way it does in FY10-FY13.

Everything in this module is pure numpy/OpenCV -- no torch, no docTR -- so it is testable
against synthetic ruled images (see test_parse_transparency_reso_fy09.py).
"""
import json
from dataclasses import dataclass, field, asdict

# Defaults tuned for 300-dpi letter scans. Overridable from the CLI while iterating.
MIN_SPAN_FRAC = 0.60     # a rule must span >=60% of the table bbox to count as a separator
MERGE_TOL_PX = 6         # separators closer than this are the same (thick/doubled) rule
KERNEL_DIVISOR = 30      # rule-detection kernel length = table dimension / this
MIN_ROW_PX = 12          # discard row bands thinner than a line of type
MIN_COL_PX = 18          # discard column bands too thin to hold a value


def _cv2():
    import cv2
    return cv2


@dataclass
class Grid:
    """An ordered lattice of separator coordinates and the cells they bound."""
    xs: list           # column separators, left to right (pixels)
    ys: list           # row separators, top to bottom (pixels)
    bbox: tuple        # (x0, y0, x1, y1) of the detected table
    notes: list = field(default_factory=list)

    @property
    def nrows(self):
        return max(0, len(self.ys) - 1)

    @property
    def ncols(self):
        return max(0, len(self.xs) - 1)

    def cell(self, r, c):
        """Pixel rectangle (x0, y0, x1, y1) of the cell at row r, column c."""
        return (self.xs[c], self.ys[r], self.xs[c + 1], self.ys[r + 1])

    def locate(self, px, py):
        """Return (row, col) containing point (px, py), or None if outside the lattice."""
        r = _band(self.ys, py)
        c = _band(self.xs, px)
        return None if (r is None or c is None) else (r, c)

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Grid(xs=list(d["xs"]), ys=list(d["ys"]), bbox=tuple(d["bbox"]),
                    notes=list(d.get("notes", [])))

    def save(self, path):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=1)

    @staticmethod
    def load(path):
        with open(path) as f:
            return Grid.from_dict(json.load(f))


def _band(seps, v):
    """Index of the band [seps[i], seps[i+1]) containing v."""
    for i in range(len(seps) - 1):
        if seps[i] <= v < seps[i + 1]:
            return i
    return None


def binarize(gray):
    """Grayscale -> uint8 ink mask (ink = 255). The scans are already bitonal, so a fixed
    threshold is both sufficient and deterministic; Otsu would drift page to page."""
    import numpy as np
    return ((gray < 128).astype(np.uint8)) * 255


def rule_masks(ink, kernel_divisor=KERNEL_DIVISOR):
    """Separate horizontal and vertical rules from text by morphological opening with a
    long, thin kernel: only ink that survives an erosion by a line-shaped element as long
    as 1/30 of the page can be a printed rule -- glyphs and speckle cannot."""
    cv2 = _cv2()
    h, w = ink.shape[:2]
    hk = max(20, w // kernel_divisor)
    vk = max(20, h // kernel_divisor)
    horiz = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
                             cv2.getStructuringElement(cv2.MORPH_RECT, (hk, 1)))
    vert = cv2.morphologyEx(ink, cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (1, vk)))
    return horiz, vert


def separators(mask, axis, span, min_span_frac=MIN_SPAN_FRAC, merge_tol=MERGE_TOL_PX):
    """Collapse a rule mask into separator coordinates.

    axis=0 -> horizontal rules, returns y coordinates; axis=1 -> vertical, returns x.
    `span` is the table extent along the OTHER axis; a rule must cover min_span_frac of it,
    which is what drops underlines, strikethroughs and scanner speckle.

    A rule is detected as a connected COMPONENT whose bounding-box length along its own
    direction reaches min_span_frac of the span, and each rule is located at its centroid.
    Bounding-box length is used, not per-scanline ink, on purpose: the FY09 interior column
    rules are faint and broken -- their ink covers under half of the rows in any single
    column, so a per-column-sum span test misses them -- but each is still one component
    spanning the full table height. Components whose centroids fall within merge_tol (a
    thick or doubled rule split in two) collapse to one.
    """
    import numpy as np
    cv2 = _cv2()
    n, _, stats, cent = cv2.connectedComponentsWithStats((mask > 0).astype("uint8"),
                                                         connectivity=8)
    length_stat = cv2.CC_STAT_HEIGHT if axis == 1 else cv2.CC_STAT_WIDTH
    coord = 0 if axis == 1 else 1        # centroid x for a vertical rule, y for horizontal
    need = max(1, int(min_span_frac * span))
    coords = sorted(float(cent[i][coord]) for i in range(1, n)
                    if stats[i, length_stat] >= need)
    if not coords:
        return []
    groups, cur = [], [coords[0]]
    for v in coords[1:]:
        if v - cur[-1] <= merge_tol:
            cur.append(v)
        else:
            groups.append(cur)
            cur = [v]
    groups.append(cur)
    return [int(round(sum(g) / len(g))) for g in groups]


def _prune(seps, min_gap, notes, what):
    """Drop separators that would create a band too thin to hold a value (a doubled rule
    the merge tolerance missed). Keeps the first of each too-close pair."""
    if not seps:
        return seps
    out = [seps[0]]
    for s in seps[1:]:
        if s - out[-1] < min_gap:
            notes.append(f"dropped {what} separator at {s} ({s - out[-1]}px from previous)")
            continue
        out.append(s)
    return out


def count_rules(gray, min_span_frac=MIN_SPAN_FRAC, merge_tol=MERGE_TOL_PX,
                kernel_divisor=KERNEL_DIVISOR):
    """(n_horizontal_rules, n_vertical_rules) printed on the page, WITHOUT building the
    cell lattice.

    This is stage 2's cheap "is there a table here?" signal. It shares its rule evidence
    (binarize → rule_masks → separators) with detect_grid(), stage 3's full pruned
    Cartesian extraction — so the two stages agree on what a "rule" is, but classification
    does not need the exact cell rectangles to decide a page is a chart. That keeps
    "what kind of page is this?" (stage 2) genuinely separate from "where are its cells?"
    (stage 3).
    """
    import numpy as np
    ink = binarize(gray)
    horiz, vert = rule_masks(ink, kernel_divisor)
    ys_nz, xs_nz = np.nonzero(np.maximum(horiz, vert))
    if ys_nz.size == 0:
        return 0, 0
    tw = max(1, int(xs_nz.max()) - int(xs_nz.min()))
    th = max(1, int(ys_nz.max()) - int(ys_nz.min()))
    n_h = len(separators(horiz, 0, tw, min_span_frac, merge_tol))
    n_v = len(separators(vert, 1, th, min_span_frac, merge_tol))
    return n_h, n_v


def detect_grid(gray, min_span_frac=MIN_SPAN_FRAC, merge_tol=MERGE_TOL_PX,
                kernel_divisor=KERNEL_DIVISOR, min_row_px=MIN_ROW_PX,
                min_col_px=MIN_COL_PX):
    """Detect the ruled table on an upright, deskewed page. Returns a Grid, or None when
    the page carries no lattice (narrative and EXHIBIT divider pages)."""
    import numpy as np
    ink = binarize(gray)
    horiz, vert = rule_masks(ink, kernel_divisor)

    rules = np.maximum(horiz, vert)
    ys_nz, xs_nz = np.nonzero(rules)
    if ys_nz.size == 0:
        return None
    bbox = (int(xs_nz.min()), int(ys_nz.min()), int(xs_nz.max()), int(ys_nz.max()))
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1])

    notes = []
    ys = _prune(separators(horiz, 0, tw, min_span_frac, merge_tol), min_row_px, notes, "row")
    xs = _prune(separators(vert, 1, th, min_span_frac, merge_tol), min_col_px, notes, "column")
    if len(xs) < 2 or len(ys) < 2:
        return None
    return Grid(xs=xs, ys=ys, bbox=bbox, notes=notes)


def draw_overlay(gray, grid):
    """Debug artifact: the page with detected separators and numbered cells drawn on it.

    This is the pipeline's primary iteration surface -- a bad kernel or span threshold is
    obvious at a glance here, and cheap to fix, in a way that a CSV diff never is.
    """
    cv2 = _cv2()
    img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for x in grid.xs:
        cv2.line(img, (x, grid.ys[0]), (x, grid.ys[-1]), (255, 0, 0), 2)
    for y in grid.ys:
        cv2.line(img, (grid.xs[0], y), (grid.xs[-1], y), (0, 0, 255), 2)
    for r in range(grid.nrows):
        for c in range(grid.ncols):
            x0, y0, _, _ = grid.cell(r, c)
            cv2.putText(img, f"{r},{c}", (x0 + 3, y0 + 14),
                        cv2.FONT_HERSHEY_PLAIN, 0.8, (0, 160, 0), 1, cv2.LINE_AA)
    return img
