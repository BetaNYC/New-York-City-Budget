"""
Stage 1 -- make a scanned page upright and level.

Two independent problems, solved separately:

  * COARSE (90deg multiples). The chart pages are landscape tables printed onto portrait
    sheets, and the rotation direction VARIES page to page inside a single file -- e.g. in
    Transparency-Reso-01 the Chart 1 page reads top-down on the left edge while
    Transparency-Reso-07's Chart 3 page reads bottom-up. A per-file constant is wrong; this
    has to be decided per page.
  * FINE (a degree or two of scanner skew). Left uncorrected, a long table's rules drift
    across several cell-heights from one edge of the page to the other, and grid.py's
    span test stops finding them.

We rotate the image ourselves rather than delegating to docTR, because stage 4 needs word
geometry in the same coordinate frame as the grid detected in stage 3.

The orientation decision for every page is persisted to orient.json with the method that
produced it, so a page the detector gets wrong can be corrected by editing one number and
re-running the downstream stages -- no code change, no re-render.
"""
import json
import os

MAX_SKEW_DEG = 5.0        # beyond this it is not skew, it is a mis-detected 90deg turn
AXIS_MARGIN = 1.15        # projection variance ratio needed to call the text axis outright


def _cv2():
    import cv2
    return cv2


def text_axis(gray):
    """'horizontal' or 'vertical' -- which way the lines of type run, plus the confidence
    ratio behind the call.

    Lines of text alternate ink rows with blank leading, so the ink profile ACROSS the text
    direction has far more variance than the profile ALONG it. Blur the glyphs together
    first so the measurement is about lines, not letters. This settles the axis (0/180 vs
    90/270) cheaply and very reliably; it says nothing about which way is up.
    """
    import numpy as np
    cv2 = _cv2()
    small = cv2.resize(gray, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    ink = (small < 128).astype(np.float32)
    blur = cv2.blur(ink, (9, 9))
    row_var = float(np.var(blur.sum(axis=1)))
    col_var = float(np.var(blur.sum(axis=0)))
    denom = max(1e-6, min(row_var, col_var))
    ratio = max(row_var, col_var) / denom
    return ("horizontal" if row_var >= col_var else "vertical"), ratio


def _rot90(gray, k):
    import numpy as np
    return np.ascontiguousarray(np.rot90(gray, k))


def detect_rotate90(gray, engine=None):
    """Number of 90deg COUNTER-CLOCKWISE turns needed to make the page upright.

    The projection heuristic fixes the axis, leaving two candidates (k and k+2). docTR
    settles the remaining 180deg ambiguity: upside-down type recognizes as a handful of
    low-confidence fragments, upright type as many high-confidence words, so
    mean_confidence * word_count separates the two decisively.

    Without an engine, returns the axis-correcting turn and reports 'axis-only' -- enough
    to inspect stage-0/1 output, not enough to trust downstream.
    """
    axis, ratio = text_axis(gray)
    # A page whose type runs vertically is a landscape table turned onto a portrait sheet.
    # Turning it one quarter turn counter-clockwise puts the type back on the horizontal;
    # the other possibility is three turns, and that is the 180deg question below.
    candidates = (0, 2) if axis == "horizontal" else (1, 3)
    if engine is None:
        return candidates[0], "axis-only", ratio

    best_k, best_score, scores = candidates[0], -1.0, {}
    for k in candidates:
        conf, n = engine.mean_confidence(_downscale_center(_rot90(gray, k)))
        score = conf * n
        scores[k] = score
        if score > best_score:
            best_k, best_score = k, score
    runner_up = max((s for k, s in scores.items() if k != best_k), default=0.0)
    margin = best_score / max(1e-6, runner_up)
    return best_k, "projection+ocr", margin


def _downscale_center(gray, max_side=1400):
    """A centre band of the page, downscaled -- enough type for the confidence tiebreak at
    a fraction of the cost of recognizing the full 300-dpi page."""
    cv2 = _cv2()
    h, w = gray.shape[:2]
    y0, y1 = int(h * 0.15), int(h * 0.85)
    band = gray[y0:y1, :]
    scale = min(1.0, max_side / float(max(band.shape[:2])))
    if scale < 1.0:
        band = cv2.resize(band, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return band


def estimate_skew(gray, max_skew=MAX_SKEW_DEG):
    """Residual skew in degrees (positive = page rotated counter-clockwise).

    On a chart page the printed rules are the best possible protractor, so measure them:
    take the long horizontal rules and use the median of their angles. Pages with no rules
    fall back to the minimum-area rectangle of the ink, which is coarser but adequate for
    narrative text we do not extract values from.
    """
    import numpy as np
    cv2 = _cv2()
    from . import grid as grid_mod

    ink = grid_mod.binarize(gray)
    horiz, _ = grid_mod.rule_masks(ink)
    h, w = gray.shape[:2]
    lines = cv2.HoughLinesP(horiz, 1, np.pi / 720, threshold=200,
                            minLineLength=int(w * 0.4), maxLineGap=20)
    angles = []
    if lines is not None:
        for x0, y0, x1, y1 in lines[:, 0]:
            if x1 == x0:
                continue
            a = np.degrees(np.arctan2(y0 - y1, x1 - x0))
            if abs(a) <= max_skew:
                angles.append(float(a))
    if angles:
        return float(np.median(angles)), "rules"

    pts = cv2.findNonZero(ink)
    if pts is None:
        return 0.0, "blank"
    angle = cv2.minAreaRect(pts)[-1]
    if angle > 45:
        angle -= 90
    return (float(angle) if abs(angle) <= max_skew else 0.0), "ink-bbox"


def deskew(gray, angle):
    """Rotate by -angle about the page centre onto an expanded white canvas, so no ink is
    cropped and no black wedge is introduced for grid.py to mistake for a rule."""
    import numpy as np
    cv2 = _cv2()
    if abs(angle) < 0.05:
        return gray
    h, w = gray.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), -angle, 1.0)
    cos, sin = abs(m[0, 0]), abs(m[0, 1])
    nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
    m[0, 2] += (nw / 2.0) - w / 2.0
    m[1, 2] += (nh / 2.0) - h / 2.0
    return cv2.warpAffine(gray, m, (nw, nh), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=255)


# --- dewarp ---------------------------------------------------------------------------
# Deskew removes a single global rotation, but the FY09 scans also BOW: a printed rule
# that should be a straight horizontal line curves by a handful of pixels across the page
# (measured ~6-7px on Transparency-Reso-01 chart pages). No rotation can flatten a curve,
# and the bow is enough to break grid.py -- the rule's ink spreads over several scanlines,
# so no single scanline spans the width and the separator's span test fails. Dewarp models
# the curvature from the rules themselves and remaps the page so they become straight.
DEWARP_MIN_RULES = 3          # need a few rules to model the warp; fewer -> leave the page alone
DEWARP_MIN_DEV_PX = 2.0       # below this the page is flat enough; skip the resample
DEWARP_XBINS = 48             # x-resolution of the traced curvature
DEWARP_RULE_WIDTH_FRAC = 0.40  # a "rule" spans at least this fraction of the page width


def _long_horizontal_rules(gray, width_frac=DEWARP_RULE_WIDTH_FRAC):
    """[(xs, ys), ...] pixel coordinates of each long horizontal rule component."""
    import numpy as np
    cv2 = _cv2()
    from . import grid as grid_mod
    ink = grid_mod.binarize(gray)
    horiz, _ = grid_mod.rule_masks(ink)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(horiz, connectivity=8)
    w = gray.shape[1]
    rules = []
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_WIDTH] >= width_frac * w:
            ys, xs = np.nonzero(lab == i)
            rules.append((xs, ys))
    return rules


def estimate_warp(gray, xbins=DEWARP_XBINS, min_rules=DEWARP_MIN_RULES):
    """Trace the page's long horizontal rules into a curvature table, or None if there are
    too few rules to model the warp (narrative / divider pages).

    Returns (targets[R], dev[R, xbins]): each rule's straight (median) y, and how far the
    rule actually sits from that straight line at each x-bin -- i.e. the bow deskew leaves
    behind. Rules are sorted top to bottom.
    """
    import numpy as np
    rules = _long_horizontal_rules(gray)
    if len(rules) < min_rules:
        return None
    w = gray.shape[1]
    edges = np.linspace(0, w, xbins + 1)
    targets, devs = [], []
    for xs, ys in rules:
        yb = np.full(xbins, np.nan)
        idx = np.clip(np.searchsorted(edges, xs, side="right") - 1, 0, xbins - 1)
        for b in range(xbins):
            m = idx == b
            if m.any():
                yb[b] = ys[m].mean()
        valid = np.isfinite(yb)
        if valid.sum() < xbins * 0.5:          # rule too broken to trust as a reference
            continue
        yb = np.interp(np.arange(xbins), np.flatnonzero(valid), yb[valid])
        t = float(np.median(yb))
        targets.append(t)
        devs.append(yb - t)
    if len(targets) < min_rules:
        return None
    order = np.argsort(targets)
    return np.array(targets)[order], np.array(devs)[order]


def dewarp(gray, warp):
    """Flatten the page's horizontal rules using estimate_warp()'s curvature table. Returns
    (image, max_dev_px). Near-identity, and skipped, where the rules are already straight."""
    import numpy as np
    cv2 = _cv2()
    if warp is None:
        return gray, 0.0
    targets, dev = warp
    max_dev = float(np.abs(dev).max())
    if max_dev < DEWARP_MIN_DEV_PX:
        return gray, max_dev
    h, w = gray.shape[:2]
    xbins = dev.shape[1]
    rows = np.arange(h)
    # Vertical shift on a coarse (h x xbins) grid: at each x-bin, interpolate the bow across
    # rows using the rules as anchors (flat beyond the top/bottom rule).
    shift_coarse = np.empty((h, xbins), np.float32)
    for b in range(xbins):
        shift_coarse[:, b] = np.interp(rows, targets, dev[:, b])
    shift_full = cv2.resize(shift_coarse, (w, h), interpolation=cv2.INTER_LINEAR)
    map_x = np.tile(np.arange(w, dtype=np.float32), (h, 1))
    map_y = rows[:, None].astype(np.float32) + shift_full
    out = cv2.remap(gray, map_x, map_y, interpolation=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_CONSTANT, borderValue=255)
    return out, max_dev


def orient_page(gray, engine=None, override=None, do_dewarp=True):
    """Return (upright_image, record). `override` is a dict loaded from a hand-edited
    orient.json entry and wins over detection -- that is the manual escape hatch.

    Pipeline: 90deg turn -> deskew (global rotation) -> dewarp (residual bow). Dewarp is a
    no-op on pages without enough rules (narrative/divider) and on pages already flat.
    """
    if override and "rotate90" in override:
        k, method, conf = int(override["rotate90"]), "override", 1.0
    else:
        k, method, conf = detect_rotate90(gray, engine)
    turned = _rot90(gray, k)

    if override and "skew_deg" in override:
        skew, skew_src = float(override["skew_deg"]), "override"
    else:
        skew, skew_src = estimate_skew(turned)
    out = deskew(turned, skew)

    warp_dev, warp_applied = 0.0, False
    if do_dewarp and not (override and override.get("no_dewarp")):
        out, warp_dev = dewarp(out, estimate_warp(out))
        warp_applied = warp_dev >= DEWARP_MIN_DEV_PX

    return out, {"rotate90": k, "method": method, "confidence": round(float(conf), 4),
                 "skew_deg": round(skew, 3), "skew_method": skew_src,
                 "warp_max_dev_px": round(float(warp_dev), 2), "warp_applied": warp_applied}


def load_records(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return {int(k): v for k, v in json.load(f).items()}


def save_records(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({str(k): v for k, v in sorted(records.items())}, f, indent=1)
