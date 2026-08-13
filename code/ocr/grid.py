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
MERGE_TOL_PX = 12        # fragments this close in position are ONE rule: a thick or doubled
                         # rule, OR a slightly slanted border whose pieces drift a few px in x
                         # down the page (p27 drifts 6px, p44 8px). Safely below the ~50px gap
                         # between the closest real columns, so distinct columns never merge.
MAX_BRIDGE_GAP_FRAC = 0.06   # join co-linear fragments of one rule across a gap up to ~one cell
                             # (6% of the table span) BEFORE the span test, so a border broken
                             # by a single missing-cell dropout is still recovered whole. One
                             # cell is ~5% of the height here; two cells (~10%) will not bridge.
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


def _rule_components(mask, axis):
    """Raw connected components of a rule mask, as dicts sorted by position along the separator
    axis. `pos` is the component centroid on that axis (x for a vertical rule, y for horizontal);
    [lo, hi) is its extent ALONG the rule direction (its height, for a vertical rule).

    Bounding-box extent is used, not per-scanline ink, on purpose: a faint, dotty-but-connected
    rule is still ONE component spanning the full table -- the page-11 condition the span test
    must not miss. What that alone does NOT handle is a rule broken into SEPARATE components
    (a curve/dropout); _rule_groups() below rejoins those.
    """
    cv2 = _cv2()
    length_stat = cv2.CC_STAT_HEIGHT if axis == 1 else cv2.CC_STAT_WIDTH
    lo_stat = cv2.CC_STAT_TOP if axis == 1 else cv2.CC_STAT_LEFT
    coord = 0 if axis == 1 else 1        # centroid x for a vertical rule, y for horizontal
    n, _, stats, cent = cv2.connectedComponentsWithStats((mask > 0).astype("uint8"),
                                                         connectivity=8)
    comps = []
    for i in range(1, n):
        lo = int(stats[i, lo_stat])
        length = int(stats[i, length_stat])
        comps.append({"pos": float(cent[i][coord]), "lo": lo, "hi": lo + length,
                      "length": length, "area": int(stats[i, cv2.CC_STAT_AREA])})
    comps.sort(key=lambda c: c["pos"])
    return comps


def _bridged_runs(intervals, max_gap):
    """Join [lo, hi) intervals into runs, bridging any gap <= max_gap. Returns the merged
    (lo, hi) runs. A slanted border the straight opening kernel eroded through, or a border
    with a one-cell dropout, arrives as two intervals with a small gap; bridging rejoins them
    so the rule is measured as one span rather than two half-length fragments."""
    intervals = sorted(intervals)
    runs = [list(intervals[0])]
    for lo, hi in intervals[1:]:
        if lo - runs[-1][1] <= max_gap:
            runs[-1][1] = max(runs[-1][1], hi)
        else:
            runs.append([lo, hi])
    return [(lo, hi) for lo, hi in runs]


def _rule_groups(mask, axis, span, min_span_frac=MIN_SPAN_FRAC, merge_tol=MERGE_TOL_PX,
                 max_gap_frac=MAX_BRIDGE_GAP_FRAC):
    """Cluster rule COMPONENTS into candidate separators, then decide each by its BRIDGED span.

    Two things defeat a plain per-component span test on these scans, both seen at a left/right
    border:
      * a rule read as several STACKED pieces -- a slanted border the straight (1, vk) opening
        kernel eroded through, or a border with a rules-crossing dropout the height of a cell; and
      * pieces that drift a few px in x across the page height.
    So components at essentially the same position (centroid within merge_tol) are grouped as one
    rule, their extents are joined across gaps up to max_gap_frac of the span (~one cell), and the
    span test is applied to THAT bridged extent -- not to each fragment. A left border arriving as
    a 0.55 and a 0.45 fragment, neither passing alone, is thereby recovered as one full separator.

    The old order (filter each component by span, THEN merge survivors) is exactly what missed
    this: both fragments were dropped before anything could rejoin them. Here grouping and
    bridging happen FIRST, and the threshold sees the whole rule.

    Returns one dict per candidate separator (position-sorted): its area-weighted `pos`, the
    `bridged_frac` its longest bridged run reaches, whether it `passes`, and its `members`.
    """
    comps = _rule_components(mask, axis)
    if not comps:
        return []
    need = max(1, int(min_span_frac * span))
    max_gap = max(1, int(max_gap_frac * span))
    groups, cur = [], [comps[0]]
    for c in comps[1:]:
        if c["pos"] - cur[-1]["pos"] <= merge_tol:
            cur.append(c)
        else:
            groups.append(cur)
            cur = [c]
    groups.append(cur)
    out = []
    for g in groups:
        runs = _bridged_runs([(c["lo"], c["hi"]) for c in g], max_gap)
        extent = max(hi - lo for lo, hi in runs)
        weight = sum(c["area"] for c in g) or 1
        pos = sum(c["pos"] * c["area"] for c in g) / weight    # slant -> the rule's average x
        out.append({
            "pos": int(round(pos)),
            "bridged_extent": extent,
            "bridged_frac": round(extent / span, 4) if span else 0.0,
            "passes": bool(extent >= need),
            "fragments": len(g),
            "runs": [[int(a), int(b)] for a, b in runs],
            "members": [{"pos": int(round(c["pos"])), "lo": c["lo"], "hi": c["hi"],
                         "frac": round(c["length"] / span, 4) if span else 0.0} for c in g],
        })
    return out


def separators(mask, axis, span, min_span_frac=MIN_SPAN_FRAC, merge_tol=MERGE_TOL_PX,
               max_gap_frac=MAX_BRIDGE_GAP_FRAC):
    """Collapse a rule mask into separator coordinates.

    axis=0 -> horizontal rules, returns y coordinates; axis=1 -> vertical, returns x.
    `span` is the table extent along the OTHER axis; a rule must cover min_span_frac of it,
    which is what drops underlines, strikethroughs and scanner speckle.

    Rules are recovered from connected COMPONENTS by bounding-box extent (not per-scanline ink),
    and co-linear fragments of one physical rule are grouped and gap-bridged BEFORE the span test
    (see _rule_groups). So a faint dotty rule, a doubled rule, and a border broken by a curve or a
    one-cell dropout all resolve to a single separator at the rule's position.
    """
    return sorted(g["pos"] for g in _rule_groups(mask, axis, span, min_span_frac, merge_tol,
                                                 max_gap_frac) if g["passes"])


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


def span_diagnostics(gray, min_span_frac=MIN_SPAN_FRAC, merge_tol=MERGE_TOL_PX,
                     max_gap_frac=MAX_BRIDGE_GAP_FRAC, kernel_divisor=KERNEL_DIVISOR):
    """Per-rule diagnostics for the rule masks, emitted under --debug.

    Lists every candidate separator exactly as _rule_groups builds it: the individual `members`
    (co-linear fragments) with their own span fractions, the `bridged_frac` the group reaches
    once their extents are joined across small gaps, and whether that clears the cut. When a
    printed rule fails to become a separator, this is where to see WHY -- e.g. a left border
    arriving as two sub-threshold fragments (0.55 + 0.45) that bridging rejoins into one
    full-height separator, or a genuine >1-cell break that stays split and correctly fails.
    """
    import numpy as np
    ink = binarize(gray)
    horiz, vert = rule_masks(ink, kernel_divisor)
    rules = np.maximum(horiz, vert)
    ys_nz, xs_nz = np.nonzero(rules)
    if ys_nz.size == 0:
        return {"bbox": None, "vertical": [], "horizontal": []}
    bbox = (int(xs_nz.min()), int(ys_nz.min()), int(xs_nz.max()), int(ys_nz.max()))
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1])
    kw = dict(min_span_frac=min_span_frac, merge_tol=merge_tol, max_gap_frac=max_gap_frac)
    return {
        "bbox": list(bbox),
        "table_width": tw,
        "table_height": th,
        "min_span_frac": min_span_frac,
        "max_gap_frac": max_gap_frac,
        "need_vertical_px": max(1, int(min_span_frac * th)),
        "need_horizontal_px": max(1, int(min_span_frac * tw)),
        "max_gap_vertical_px": max(1, int(max_gap_frac * th)),
        "max_gap_horizontal_px": max(1, int(max_gap_frac * tw)),
        "vertical": _rule_groups(vert, axis=1, span=th, **kw),
        "horizontal": _rule_groups(horiz, axis=0, span=tw, **kw),
    }


def _draw_seg(cv2, img, axis, pos, lo, hi, color, thickness):
    """One separator segment: vertical (axis=1) at x=pos from y=lo..hi, else horizontal."""
    if axis == 1:
        cv2.line(img, (pos, lo), (pos, hi), color, thickness)
    else:
        cv2.line(img, (lo, pos), (hi, pos), color, thickness)


def draw_span_overlay(gray, diag=None, axis=1, kernel_divisor=KERNEL_DIVISOR):
    """Visual companion to span_diagnostics(): the rule mask over a faded page. Each candidate
    separator is drawn from its member fragments (thin grey) and its bridged run (bold), green
    if the bridged span clears the threshold (now a separator) or red if it still falls short,
    labelled with the bridged fraction. Defaults to the VERTICAL axis, where a missing left/right
    border is diagnosed. Surviving rule ink is tinted cyan so an eroded/curved line shows its
    true shape -- letting you see two half-height fragments become one green full-height rule.
    """
    cv2 = _cv2()
    if diag is None:
        diag = span_diagnostics(gray, kernel_divisor=kernel_divisor)
    ink = binarize(gray)
    horiz, vert = rule_masks(ink, kernel_divisor)
    mask = vert if axis == 1 else horiz
    img = cv2.cvtColor(((gray.astype("uint16") // 2) + 128).astype("uint8"),
                       cv2.COLOR_GRAY2BGR)          # faded page, so the overlay reads clearly
    img[mask > 0] = (200, 200, 0)                    # cyan: rule ink that survived the opening
    for grp in (diag["vertical"] if axis == 1 else diag["horizontal"]):
        color = (0, 180, 0) if grp["passes"] else (0, 0, 255)
        for m in grp["members"]:                     # each raw fragment, thin grey
            _draw_seg(cv2, img, axis, grp["pos"], m["lo"], m["hi"], (150, 150, 150), 1)
        for lo, hi in grp["runs"]:                   # the bridged run, bold, in the verdict colour
            _draw_seg(cv2, img, axis, grp["pos"], lo, hi, color, 3)
        anchor = grp["runs"][0][0]
        org = ((grp["pos"] + 4, max(16, anchor - 5)) if axis == 1
               else (anchor + 4, max(16, grp["pos"] - 5)))
        cv2.putText(img, f"{grp['bridged_frac']:.2f}", org,
                    cv2.FONT_HERSHEY_PLAIN, 1.3, color, 2, cv2.LINE_AA)
    return img
