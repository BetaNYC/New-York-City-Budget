"""
Stage 4 -- docTR recognition, and the mapping of recognized words onto grid cells.

Two predictors are held: the full detect+recognize pipeline for whole pages, and the bare
recognition model for re-reading a single cropped cell. The second one is what makes the
targeted re-OCR pass cheap -- when a numeric cell fails its validator we crop it, upscale
it, and re-read just that crop, rather than re-running detection over the page.

docTR (and therefore torch) is imported lazily inside Engine so this module can be
imported -- and the cell-assignment logic tested -- in the plain `.venv`.
"""
import os
import re

DET_ARCH = "db_resnet50"
RECO_ARCH = "crnn_vgg16_bn"

# Cells whose value must survive a checksum-style validator. A failure here triggers the
# targeted re-OCR pass; a failure after that is flagged and queued for human review.
NUMERIC_COLUMNS = ("ein", "amount", "agy_num", "ua", "conduit_ein")

RE_OCR_SCALE = 3          # upscale factor for the targeted re-read of a failing cell
CROP_PAD_PX = 4           # padding inside the cell rectangle, to clear the printed rules

# A word must hold at least this fraction of its own area inside EACH of two-or-more cells
# before we call it a genuine cross-cell straddle (see find_cell_span_conflicts). A descender
# dipping under a rule, or slant/antialiasing bleed at a cell edge, lands well under this and
# must not trigger the fallback -- only an unambiguous split should.
SPAN_MIN_FRAC = 0.30


class Engine:
    """Lazily-constructed docTR predictors. Build one and reuse it for the whole batch --
    model construction dominates runtime otherwise."""

    def __init__(self, det_arch=DET_ARCH, reco_arch=RECO_ARCH):
        self.det_arch = det_arch
        self.reco_arch = reco_arch
        self._ocr = None
        self._reco = None

    @property
    def ocr(self):
        if self._ocr is None:
            from doctr.models import ocr_predictor
            # assume_straight_pages=True: stage 1 has already made the page upright and
            # deskewed it, and we need word geometry in the SAME frame as the detected
            # grid. Letting docTR rotate internally would silently break cell assignment.
            self._ocr = ocr_predictor(self.det_arch, self.reco_arch, pretrained=True,
                                      assume_straight_pages=True)
        return self._ocr

    @property
    def reco(self):
        if self._reco is None:
            from doctr.models import recognition_predictor
            self._reco = recognition_predictor(self.reco_arch, pretrained=True)
        return self._reco

    @staticmethod
    def _rgb(gray):
        import numpy as np
        if gray.ndim == 3:
            return gray
        return np.stack([gray] * 3, axis=-1)

    def words(self, gray):
        """Recognize a page. Returns [{'text', 'conf', 'bbox': (x0,y0,x1,y1)}] in pixels."""
        result = self.ocr([self._rgb(gray)])
        page = result.pages[0]
        h, w = page.dimensions
        out = []
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    (rx0, ry0), (rx1, ry1) = word.geometry
                    out.append({
                        "text": word.value,
                        "conf": float(word.confidence),
                        "bbox": (int(rx0 * w), int(ry0 * h), int(rx1 * w), int(ry1 * h)),
                    })
        return out

    def mean_confidence(self, gray):
        """(mean word confidence, word count) -- the orientation tiebreak signal. Text read
        at the wrong 90deg multiple recognizes as a few low-confidence fragments; read
        upright it recognizes as many high-confidence words, so the product separates
        cleanly."""
        words = self.words(gray)
        if not words:
            return 0.0, 0
        return sum(w["conf"] for w in words) / len(words), len(words)

    def read_crop(self, crop):
        """Recognize a single pre-cropped cell image. Returns (text, confidence)."""
        out = self.reco([self._rgb(crop)])
        if not out:
            return "", 0.0
        text, conf = out[0]
        return text, float(conf)


def _centroid(bbox):
    x0, y0, x1, y1 = bbox
    return (x0 + x1) / 2.0, (y0 + y1) / 2.0


def _iou(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    area_a = max(1, (ax1 - ax0) * (ay1 - ay0))
    return inter / float(area_a)


def assign_words(words, grid):
    """Bin page words into grid cells.

    Primary rule is centroid containment -- unambiguous, order-independent, and immune to
    a word's box overhanging a rule. A word whose centroid lands outside the lattice (in a
    margin, or straddling a rule after a slight deskew residue) falls back to the cell it
    overlaps most, and only if that overlap covers at least half the word.

    Returns {(row, col): [word, ...]} plus the list of words that could not be placed.
    """
    cells = {}
    orphans = []
    for w in words:
        cx, cy = _centroid(w["bbox"])
        rc = grid.locate(cx, cy)
        if rc is None:
            best, best_iou = None, 0.0
            for r in range(grid.nrows):
                for c in range(grid.ncols):
                    ov = _iou(w["bbox"], grid.cell(r, c))
                    if ov > best_iou:
                        best, best_iou = (r, c), ov
            if best is None or best_iou < 0.5:
                orphans.append(w)
                continue
            rc = best
        cells.setdefault(rc, []).append(w)
    return cells, orphans


def find_cell_span_conflicts(words, grid, min_frac=SPAN_MIN_FRAC):
    """Words whose box unambiguously straddles two or more grid cells.

    `assign_words` above places a word wholesale into whichever single cell its centroid
    lands in -- correct almost always, but silently wrong when a word's detection box
    actually covers real ink in a second cell too (a value that visually crosses a column or
    row rule). This looks for that case directly: for each word, check its centroid-cell's
    3x3 neighbourhood (a word cannot geometrically overlap a cell it isn't adjacent to) and
    reuse `_iou`, which is already "fraction of the word's own area inside this cell." If
    `min_frac` or more of the word's area lands in each of two-or-more cells, that's a
    genuine split, not edge bleed -- report every cell implicated.

    Returns {(row, col): [word, ...]}, one entry per implicated cell, so the caller can
    re-read each of those cells independently rather than trust this word's assignment.
    """
    conflicts = {}
    for w in words:
        cx, cy = _centroid(w["bbox"])
        primary = grid.locate(cx, cy)
        if primary is None:
            continue  # outside the lattice -- assign_words' own orphan path handles this
        pr, pc = primary
        hits = [(r, c)
                for r in range(max(0, pr - 1), min(grid.nrows, pr + 2))
                for c in range(max(0, pc - 1), min(grid.ncols, pc + 2))
                if _iou(w["bbox"], grid.cell(r, c)) >= min_frac]
        if len(hits) >= 2:
            for rc in hits:
                conflicts.setdefault(rc, []).append(w)
    return conflicts


def cell_text(words, line_tol=None):
    """Join a cell's words into reading order: rows of text top-to-bottom, words left to
    right within a row. `line_tol` defaults to half the median word height, which groups a
    wrapped organization name correctly without merging two table rows."""
    if not words:
        return "", 1.0
    heights = sorted(w["bbox"][3] - w["bbox"][1] for w in words)
    tol = line_tol if line_tol is not None else max(4, heights[len(heights) // 2] // 2)

    lines = []
    for w in sorted(words, key=lambda w: (w["bbox"][1], w["bbox"][0])):
        cy = (w["bbox"][1] + w["bbox"][3]) / 2.0
        for line in lines:
            if abs(cy - line["cy"]) <= tol:
                line["words"].append(w)
                break
        else:
            lines.append({"cy": cy, "words": [w]})

    parts = []
    for line in lines:
        parts.append(" ".join(w["text"] for w in sorted(line["words"],
                                                        key=lambda w: w["bbox"][0])))
    # Confidence of a cell is its WEAKEST word: a value is only as trustworthy as the
    # least-certain character group in it.
    return " ".join(p for p in parts if p).strip(), min(w["conf"] for w in words)


def header_row_texts(words, grid):
    """Reconstruct the column-header cells from the words printed just ABOVE the grid.

    The FY09 chart headers sit above the ruled data area with NO top border, so they are not
    row 0 of the detected grid -- row 0 is the first data row. This bins the words between
    the 'CHART n: Title' caption line and the grid's top edge into the grid's columns by
    their x-centroid, so the header maps against the exact column boundaries the data uses.
    Returns a list of length grid.ncols.
    """
    import numpy as np
    ys0 = grid.ys[0]
    above = [w for w in words if (w["bbox"][1] + w["bbox"][3]) / 2.0 < ys0]

    # The caption line ("CHART n: Title") sits above the header; drop it and anything higher.
    caption_bottom = 0
    for w in above:
        if re.match(r"(?i)^chart\b", w["text"]):
            caption_bottom = max(caption_bottom, w["bbox"][3])
    # ...and cap the band so stray marks at the top of the page can never reach the header.
    rowh = float(np.median(np.diff(grid.ys))) if len(grid.ys) > 1 else 40.0
    band_top = ys0 - max(60.0, 2.5 * rowh)
    floor = max(float(caption_bottom), band_top)
    header = [w for w in above if (w["bbox"][1] + w["bbox"][3]) / 2.0 > floor]

    texts = []
    for c in range(grid.ncols):
        x0, x1 = grid.xs[c], grid.xs[c + 1]
        col = [w for w in header if x0 <= (w["bbox"][0] + w["bbox"][2]) / 2.0 < x1]
        texts.append(cell_text(col)[0] if col else "")
    return texts


def crop_cell(gray, rect, pad=CROP_PAD_PX):
    """Crop a cell's interior, inset by `pad` so the printed rules are not fed to the
    recognizer as glyph strokes."""
    x0, y0, x1, y1 = rect
    h, w = gray.shape[:2]
    x0, y0 = max(0, x0 + pad), max(0, y0 + pad)
    x1, y1 = min(w, x1 - pad), min(h, y1 - pad)
    if x1 <= x0 or y1 <= y0:
        return None
    return gray[y0:y1, x0:x1]


def reread_cell(engine, gray, rect, scale=RE_OCR_SCALE):
    """Targeted re-OCR of one cell: crop, upscale, recognize with the recognition model
    alone. Returns (text, conf) or None if the cell is empty/degenerate."""
    import cv2
    crop = crop_cell(gray, rect)
    if crop is None or crop.size == 0:
        return None
    big = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return engine.read_crop(big)


def draw_ocr_overlay(gray, grid, cell_texts, cell_confs, low_conf=0.80):
    """Debug artifact for stage 4: the recognized text written back into each cell, tinted
    red where confidence fell below `low_conf`.

    This is the counterpart to grid.py's overlay -- it makes an OCR miss (a dropped digit,
    a column the text landed in the wrong cell of) visible at a glance, next to the pixels
    it came from, without opening a JSON dump.
    """
    import cv2
    img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for x in grid.xs:
        cv2.line(img, (x, grid.ys[0]), (x, grid.ys[-1]), (210, 210, 210), 1)
    for y in grid.ys:
        cv2.line(img, (grid.xs[0], y), (grid.xs[-1], y), (210, 210, 210), 1)
    for (r, c), text in cell_texts.items():
        if not text.strip():
            continue
        x0, y0, x1, y1 = grid.cell(r, c)
        conf = cell_confs.get((r, c), 1.0)
        colour = (0, 0, 220) if conf < low_conf else (0, 140, 0)
        shown = text if len(text) <= 22 else text[:21] + "…"
        cv2.putText(img, shown, (x0 + 2, y0 + 16), cv2.FONT_HERSHEY_PLAIN, 0.8,
                    colour, 1, cv2.LINE_AA)
    return img


def draw_detection_overlay(gray, words, grid=None, low_conf=0.80):
    """Debug artifact for stage 4: docTR's raw word DETECTION boxes on the page, tinted by
    recognition confidence (red below `low_conf`).

    Complements draw_ocr_overlay, which shows text AFTER it is routed into cells. This shows
    the boxes BEFORE cell assignment, so problems the cell view hides are visible directly:
    a word straddling a rule, a missed/merged word, or a word orphaned outside the lattice
    (a box that lands in no cell). When `grid` is given its lines are drawn faintly for
    reference, so which boxes fall in which column is obvious.
    """
    import cv2
    img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    if grid is not None:
        for x in grid.xs:
            cv2.line(img, (x, grid.ys[0]), (x, grid.ys[-1]), (210, 210, 210), 1)
        for y in grid.ys:
            cv2.line(img, (grid.xs[0], y), (grid.xs[-1], y), (210, 210, 210), 1)
    for w in words:
        x0, y0, x1, y1 = w["bbox"]
        colour = (0, 0, 220) if w["conf"] < low_conf else (0, 140, 0)
        cv2.rectangle(img, (x0, y0), (x1, y1), colour, 1)
    return img


def save_crop(gray, rect, path):
    """Write a cell crop for the human-review queue, so a flagged value can be checked
    against the actual pixels without hunting through a 68-page PDF."""
    import cv2
    crop = crop_cell(gray, rect, pad=0)
    if crop is None or crop.size == 0:
        return ""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, crop)
    return path
