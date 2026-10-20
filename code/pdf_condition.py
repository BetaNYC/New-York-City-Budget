#!/usr/bin/env python3
"""
PDF condition survey: what state is every PDF under source/ in, and what QA would it need to
become clean structured data? Stage 0 (triage) of the PDF-to-structured-data plan.

Writes two deterministic CSVs (sorted, rounded, no timestamps, so a re-run on the same bytes
produces byte-identical files):

  data/pdf_condition.csv        one row per PDF
  data/pdf_condition_pages.csv  one row per page

Text-layer classification is a port of Christian Moscardi's text-layer probe,
``nyc_executive_orders/textlayer.py`` in BetaNYC/nyc-executive-orders (MIT). Credit for the
method is his: two probes, because one is not enough --

1. character density: mean extracted characters per page; at or below 100 there is no usable
   text layer (``scanned``);
2. text render mode: the share of glyphs drawn in PDF render mode 3 (invisible). Above 0.5 the
   text layer is somebody's OCR stamped invisibly over a page image (``scanned-ocr-layer``),
   not the document. The share is bimodal at 0 and 1, so the threshold sits in an empty valley;

and per-page counts are kept, because a mean hides an image-only page inside a good document.

His original runs on PyMuPDF (AGPL). This port runs on pypdfium2 (Apache-2.0/BSD-3) so the
shipped code carries no AGPL dependency. The port was validated against the original on every
PDF in source/ (see research/2026-10-19-schedule-c-pdf-toolkit/CONDITION.md for the result and
the harness). Character counts differ slightly (pdfium's text page inserts generated spaces and
line breaks differently from PyMuPDF's get_text), which is why the validation compares
classifications and low-text page lists, not raw counts.

Everything beyond the text-layer class is new here and is a heuristic, stated as such:

* ``image_only_pages``: low-text pages (<= 100 chars) that carry ink (measured by rendering the
  page at 36 dpi) not explained by their own text: an image covers >= 30% of the page, or there is
  ink and no text at all. Christian's ``image_only_pages`` is every low-text page; that list is
  kept here as ``low_text_pages`` (the validation target). The rest of it is split into
  ``short_text_pages`` (inked, with a short real text layer: covers, dividers) and
  ``blank_pages`` (no ink). In a ``scanned`` document every inked page is image-only.
* rules / rects: visible path objects, walked segment by segment in page coordinates. A line
  segment (or a closed four-point subpath that is thin) is a horizontal or vertical rule; a closed
  four-point subpath that is not thin is a rect. Paths inside Form XObjects are measured in the
  form's own coordinate space (pdfium does not compose the form matrix), which can mis-orient a
  rotated form; counts of rules are unaffected.
* ``garbled_share``: share of non-whitespace extracted characters that are U+FFFD, private-use, or
  C0 controls, i.e. glyphs with no usable Unicode mapping.
* family: rule-based on the filename and, independently, the first page's text. If the two
  disagree, or neither matches, the family is ``unknown``. Never guessed.

No network, no OCR. Pure local inspection of committed bytes.

Run:  python code/pdf_condition.py            (from the repo root)
Test: pytest code/test_pdf_condition.py
Deps: pypdfium2>=5,<6 (pdfium 156.0.8076.0 was used for the committed CSVs) and pypdf>=6,<7,
      both in code/requirements.txt.
"""
from __future__ import annotations

import argparse
import csv
import ctypes
import hashlib
import logging
import os
import re
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path

try:
    import pypdfium2 as pdfium
    import pypdfium2.raw as pdfium_c
    from pypdf import PdfReader
except ImportError as exc:  # fail loud, never mysteriously
    sys.exit(f"pdf_condition.py: missing dependency ({exc}). "
             f"Install with: pip install -r code/requirements.txt")

log = logging.getLogger("pdf_condition")

# --- Christian's thresholds, unchanged -------------------------------------------------------
TEXT_LAYER_CHARS_PER_PAGE_THRESHOLD = 100
INVISIBLE_CHAR_SHARE_THRESHOLD = 0.5
CLASS_TEXT = "text"
CLASS_OCR_LAYER = "scanned-ocr-layer"
CLASS_SCANNED = "scanned"
CLASS_ERROR = "error"
CLASS_MIXED = "mixed"  # this survey only: text + image-only pages in one document (see doc_row)

# --- this survey's heuristics ----------------------------------------------------------------
INK_DPI = 36                 # render resolution for the ink check on low-text pages
INK_DARK_LEVEL = 200         # 8-bit gray below this counts as ink
INK_SHARE_THRESHOLD = 0.002  # >= 0.2% dark pixels = the page has content
RULE_MAX_THICKNESS = 2.5     # pt: a rule is at most this thick ...
RULE_MIN_LENGTH = 4.0        # pt: ... and at least this long
RULED_PAGE_MIN_H = 2         # a page "has a ruled table" with >= 2 horizontal rules ...
RULED_PAGE_MIN_V = 3         # ... and >= 3 vertical rules,
RULED_PAGE_MIN_RECTS = 15    # ... or >= 15 non-thin rects (cell boxes)
RULED_DOC_MIN_SHARE = 0.10   # doc has_ruled_tables if >= 10% of its pages are ruled
DOC_TIER_A_MIN_RULED_SHARE = 0.5  # doc tier A if >= half its pages are ruled
GARBLED_DOC_THRESHOLD = 0.01
IMAGE_ONLY_MIN_IMAGE_SHARE = 0.3  # a low-text page this covered by images is a picture page

FAMILY_FILENAME_RULES = [  # first match wins; order matters (supporting detail before changes)
    ("transparency_resolution", re.compile(r"transparency-reso", re.IGNORECASE)),
    ("capital_supporting_detail", re.compile(r"supporting-detail|capresowork", re.IGNORECASE)),
    ("terms_conditions", re.compile(r"terms-and-conditions|tandc|[-_]tc\.pdf$", re.IGNORECASE)),
    ("schedule_c", re.compile(r"sched(ule)?[-_ ]?c|skedc|(^|[-_])c20\d\d\.pdf$", re.IGNORECASE)),
    ("capital_changes", re.compile(
        r"capreso|reso-?a|changes[-_]?(to[-_]?)?(the[-_])?exec|changestobudget|capital-changes|"
        r"section-254-changes", re.IGNORECASE)),
]
FAMILY_TITLE_RULES = [  # applied to whitespace-normalized first-page text
    ("transparency_resolution", re.compile(
        r"\btransparency\b|resolution approving the new designation and changes in the designation",
        re.IGNORECASE)),
    ("capital_supporting_detail", re.compile(r"supporting detail", re.IGNORECASE)),
    ("terms_conditions", re.compile(r"terms and conditions", re.IGNORECASE)),
    ("schedule_c", re.compile(
        r"schedule c\b|adjustments? summary|djustment ummary|budget adjustment summary", re.IGNORECASE)),
    ("capital_changes", re.compile(
        r"changes to the executive capital budget|changes pursuant to section 254", re.IGNORECASE)),
]
FAMILY_UNKNOWN = "unknown"

_FY_DIR = re.compile(r"^FY(\d{2})$")


# --- results ---------------------------------------------------------------------------------
@dataclass
class PageResult:
    page: int
    chars: int = 0
    traced_chars: int = 0
    invisible_chars: int = 0
    garbled_chars: int = 0
    nonspace_chars: int = 0
    image_area_share: float = 0.0
    h_rules: int = 0
    v_rules: int = 0
    rects: int = 0
    curves: int = 0
    rotation: int = 0
    width: float = 0.0
    height: float = 0.0
    ink_share: float | None = None  # only measured on low-text pages
    error: str = ""

    @property
    def low_text(self) -> bool:
        return self.chars <= TEXT_LAYER_CHARS_PER_PAGE_THRESHOLD

    @property
    def has_ink(self) -> bool:
        return self.ink_share is not None and self.ink_share >= INK_SHARE_THRESHOLD

    @property
    def image_only(self) -> bool:
        """A low-text page whose ink is not explained by its own (short) text layer: either a
        large image covers it, or it has ink and no text at all (vector art / outlined text)."""
        return self.low_text and self.has_ink and (
            self.image_area_share >= IMAGE_ONLY_MIN_IMAGE_SHARE or self.nonspace_chars == 0)

    @property
    def ruled(self) -> bool:
        return ((self.h_rules >= RULED_PAGE_MIN_H and self.v_rules >= RULED_PAGE_MIN_V)
                or self.rects >= RULED_PAGE_MIN_RECTS)

    @property
    def garbled_share(self) -> float:
        return self.garbled_chars / self.nonspace_chars if self.nonspace_chars else 0.0


@dataclass
class DocResult:
    path: str
    pages: list[PageResult] = field(default_factory=list)
    sha256: str = ""
    nbytes: int = 0
    pdf_version: str = ""
    producer: str = ""
    creator: str = ""
    encrypted: bool = False
    fonts_total: int = 0
    fonts_without_tounicode: int = 0
    fonts_type0_without_tounicode: int = 0
    fonts_type3: int = 0
    first_page_text: str = ""
    error: str = ""


# --- pure classification helpers (unit-tested) ------------------------------------------------
def textlayer_class(page_chars: list[int], invisible: int, traced: int) -> str:
    """Christian's classification, verbatim logic."""
    if not page_chars:
        return CLASS_ERROR
    if sum(page_chars) / len(page_chars) <= TEXT_LAYER_CHARS_PER_PAGE_THRESHOLD:
        return CLASS_SCANNED
    share = invisible / traced if traced else 0.0
    return CLASS_OCR_LAYER if share > INVISIBLE_CHAR_SHARE_THRESHOLD else CLASS_TEXT


def low_text_pages(page_chars: list[int]) -> list[int]:
    """Christian's image_only_pages: only reported inside a document that passed the gate."""
    if not page_chars:
        return []
    if sum(page_chars) / len(page_chars) <= TEXT_LAYER_CHARS_PER_PAGE_THRESHOLD:
        return []
    return [i for i, n in enumerate(page_chars, 1) if n <= TEXT_LAYER_CHARS_PER_PAGE_THRESHOLD]


def is_garbled_char(ch: str) -> bool:
    cp = ord(ch)
    if ch in "\t\n\r":
        return False
    return (cp == 0xFFFD or cp < 0x20 or 0xE000 <= cp <= 0xF8FF
            or 0xF0000 <= cp <= 0x10FFFF)


def classify_segment(x0: float, y0: float, x1: float, y1: float) -> str | None:
    """'h' / 'v' for a straight rule, else None."""
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    if dy <= RULE_MAX_THICKNESS and dx >= RULE_MIN_LENGTH:
        return "h"
    if dx <= RULE_MAX_THICKNESS and dy >= RULE_MIN_LENGTH:
        return "v"
    return None


def classify_box(w: float, h: float) -> str | None:
    """A closed four-point subpath: thin -> rule, else rect, tiny -> None."""
    if h <= RULE_MAX_THICKNESS and w >= RULE_MIN_LENGTH:
        return "h"
    if w <= RULE_MAX_THICKNESS and h >= RULE_MIN_LENGTH:
        return "v"
    if w > RULE_MAX_THICKNESS and h > RULE_MAX_THICKNESS:
        return "rect"
    return None


def family_from_filename(name: str) -> str | None:
    for fam, rx in FAMILY_FILENAME_RULES:
        if rx.search(name):
            return fam
    return None


def family_from_title(text: str) -> str | None:
    norm = re.sub(r"\s+", " ", text or "")
    for fam, rx in FAMILY_TITLE_RULES:
        if rx.search(norm):
            return fam
    return None


def resolve_family(by_name: str | None, by_title: str | None) -> tuple[str, str]:
    """(family, basis). Agreement or a single signal decides; conflict or silence is unknown."""
    if by_name and by_title:
        return (by_name, "filename+title") if by_name == by_title else (FAMILY_UNKNOWN, "conflict")
    if by_name:
        return by_name, "filename"
    if by_title:
        return by_title, "title"
    return FAMILY_UNKNOWN, "none"


def fiscal_year_from_path(rel: str) -> str:
    for part in Path(rel).parts:
        m = _FY_DIR.match(part)
        if m:
            return str(2000 + int(m.group(1)))
    return ""


def compact_pages(pages: list[int]) -> str:
    """[1,2,3,7,9,10] -> '1-3,7,9-10'."""
    out, start, prev = [], None, None
    for p in sorted(pages):
        if start is None:
            start = prev = p
        elif p == prev + 1:
            prev = p
        else:
            out.append(f"{start}-{prev}" if prev != start else str(start))
            start = prev = p
    if start is not None:
        out.append(f"{start}-{prev}" if prev != start else str(start))
    return ",".join(out)


def page_tier(doc_class: str, p: PageResult) -> str:
    if doc_class == CLASS_ERROR or p.error:
        return "error"
    if doc_class == CLASS_SCANNED and p.low_text:
        return "D" if p.has_ink else "blank"
    if doc_class == CLASS_OCR_LAYER:
        return "C"
    if p.low_text:
        if p.image_only:
            return "D"
        return "short-text" if p.has_ink else "blank"
    return "A" if p.ruled else "B"


def doc_tier(textlayer: str, ruled_share: float) -> str:
    """Document tier from the textlayer class (not the survey's 'mixed', which is a flag)."""
    text_class = textlayer
    if text_class == CLASS_ERROR:
        return "error"
    if text_class == CLASS_SCANNED:
        return "D"
    if text_class == CLASS_OCR_LAYER:
        return "C"
    # Ruled-page share is not bimodal across the corpus (composite documents mix narrative,
    # ruled charts and unruled listings), so the middle band is reported as composite rather
    # than forced. The per-page tier in pdf_condition_pages.csv is the finer truth; a mixed
    # document's image-only pages are tier D there.
    if ruled_share >= DOC_TIER_A_MIN_RULED_SHARE:
        return "A"
    if ruled_share < RULED_DOC_MIN_SHARE:
        return "B"
    return "A+B"


# --- measurement (pdfium) ---------------------------------------------------------------------
_NULL_U16 = ctypes.cast(None, ctypes.POINTER(ctypes.c_ushort))


def _textobj_len(obj_raw, tp_raw) -> int:
    nbytes = pdfium_c.FPDFTextObj_GetText(obj_raw, tp_raw, _NULL_U16, 0)
    return max(0, nbytes // 2 - 1)  # UTF-16LE incl. NUL terminator


def _path_visible(obj_raw) -> bool:
    fill, stroke = ctypes.c_int(), ctypes.c_int()
    if not pdfium_c.FPDFPath_GetDrawMode(obj_raw, ctypes.byref(fill), ctypes.byref(stroke)):
        return True
    return bool(fill.value) or bool(stroke.value)


def _measure_path(obj_raw, res: PageResult) -> None:
    n = pdfium_c.FPDFPath_CountSegments(obj_raw)
    if n <= 0:
        return
    m = pdfium_c.FS_MATRIX()
    if not pdfium_c.FPDFPageObj_GetMatrix(obj_raw, ctypes.byref(m)):
        m.a, m.b, m.c, m.d, m.e, m.f = 1, 0, 0, 1, 0, 0
    fx, fy = ctypes.c_float(), ctypes.c_float()
    sub: list[tuple[float, float]] = []
    sub_closed = False
    sub_lines_only = True

    def flush():
        if len(sub) == 5 or (len(sub) == 4 and sub_closed):
            pts = sub[:4]
            if sub_lines_only and len(sub) in (4, 5):
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                kind = classify_box(max(xs) - min(xs), max(ys) - min(ys))
                if kind == "h":
                    res.h_rules += 1
                elif kind == "v":
                    res.v_rules += 1
                elif kind == "rect":
                    res.rects += 1
                return
        for (x0, y0), (x1, y1) in pairwise(sub):
            kind = classify_segment(x0, y0, x1, y1)
            if kind == "h":
                res.h_rules += 1
            elif kind == "v":
                res.v_rules += 1

    for i in range(n):
        seg = pdfium_c.FPDFPath_GetPathSegment(obj_raw, i)
        typ = pdfium_c.FPDFPathSegment_GetType(seg)
        pdfium_c.FPDFPathSegment_GetPoint(seg, ctypes.byref(fx), ctypes.byref(fy))
        x = m.a * fx.value + m.c * fy.value + m.e
        y = m.b * fx.value + m.d * fy.value + m.f
        if typ == pdfium_c.FPDF_SEGMENT_MOVETO:
            if sub:
                flush()
            sub, sub_closed, sub_lines_only = [(x, y)], False, True
            continue
        if typ == pdfium_c.FPDF_SEGMENT_BEZIERTO:
            res.curves += 1
            sub_lines_only = False
        sub.append((x, y))
        if pdfium_c.FPDFPathSegment_GetClose(seg):
            sub_closed = True
    if sub:
        flush()


_DARK_BYTES = bytes(range(INK_DARK_LEVEL))


def _ink_share(page) -> float:
    bmp = page.render(scale=INK_DPI / 72, grayscale=True)
    try:
        w, h, stride = bmp.width, bmp.height, bmp.stride
        buf = bytes(bmp.buffer)
    finally:
        bmp.close()
    if not w or not h:
        return 0.0
    dark = 0
    for row in range(h):
        line = buf[row * stride: row * stride + w]
        dark += len(line) - len(line.translate(None, _DARK_BYTES))
    return dark / (w * h)


def _measure_page(pdf, idx: int) -> PageResult:
    res = PageResult(page=idx + 1)
    page = pdf[idx]
    try:
        res.rotation = page.get_rotation()
        res.width, res.height = page.get_size()
        cl, cb, cr, ct = page.get_cropbox()
        page_area = max(1e-6, (cr - cl) * (ct - cb))
        tp = page.get_textpage()
        try:
            res.chars = tp.count_chars()
            text = tp.get_text_range() if res.chars else ""
            for ch in text:
                if not ch.isspace():
                    res.nonspace_chars += 1
                    if is_garbled_char(ch):
                        res.garbled_chars += 1
            img_area = 0.0
            for obj in page.get_objects(max_depth=15):
                t = obj.type
                if t == pdfium_c.FPDF_PAGEOBJ_TEXT:
                    n = _textobj_len(obj.raw, tp.raw)
                    res.traced_chars += n
                    if (pdfium_c.FPDFTextObj_GetTextRenderMode(obj.raw)
                            == pdfium_c.FPDF_TEXTRENDERMODE_INVISIBLE):
                        res.invisible_chars += n
                elif t == pdfium_c.FPDF_PAGEOBJ_PATH:
                    if _path_visible(obj.raw):
                        _measure_path(obj.raw, res)
                elif t == pdfium_c.FPDF_PAGEOBJ_IMAGE:
                    l, b, r, tt = obj.get_bounds()
                    w = max(0.0, min(r, cr) - max(l, cl))
                    h = max(0.0, min(tt, ct) - max(b, cb))
                    img_area += w * h
            res.image_area_share = min(1.0, img_area / page_area)
        finally:
            tp.close()
        if res.low_text:
            res.ink_share = _ink_share(page)
    except Exception as exc:  # noqa: BLE001 - one bad file/page must not sink the batch; recorded in the row
        res.error = f"{type(exc).__name__}: {exc}"
    finally:
        page.close()
    return res


def _font_census(path: Path, doc: DocResult) -> None:
    try:
        reader = PdfReader(str(path))
        doc.encrypted = bool(reader.is_encrypted)
        if reader.is_encrypted:
            reader.decrypt("")
        seen: set = set()

        def walk(resources, depth=0):
            if resources is None or depth > 6:
                return
            resources = resources.get_object()
            fonts = resources.get("/Font")
            if fonts is not None:
                for ref in fonts.get_object().values():
                    key = (ref.idnum, ref.generation) if hasattr(ref, "idnum") else id(ref)
                    if key in seen:
                        continue
                    seen.add(key)
                    f = ref.get_object()
                    doc.fonts_total += 1
                    sub = f.get("/Subtype")
                    if sub == "/Type3":
                        doc.fonts_type3 += 1
                    if "/ToUnicode" not in f:
                        doc.fonts_without_tounicode += 1
                        if sub == "/Type0":
                            doc.fonts_type0_without_tounicode += 1
            xobjs = resources.get("/XObject")
            if xobjs is not None:
                for ref in xobjs.get_object().values():
                    key = ("x", ref.idnum, ref.generation) if hasattr(ref, "idnum") else id(ref)
                    if key in seen:
                        continue
                    seen.add(key)
                    xo = ref.get_object()
                    if xo.get("/Subtype") == "/Form":
                        walk(xo.get("/Resources"), depth + 1)

        for pg in reader.pages:
            walk(pg.get("/Resources"))
    except Exception as exc:  # noqa: BLE001 - one bad file/page must not sink the batch; recorded in the row
        doc.error = (doc.error + "; " if doc.error else "") + f"font census: {exc}"


def survey_pdf(path: str | Path, rel: str | None = None) -> DocResult:
    path = Path(path)
    doc = DocResult(path=rel or str(path))
    data = path.read_bytes()
    doc.sha256 = hashlib.sha256(data).hexdigest()
    doc.nbytes = len(data)
    try:
        pdf = pdfium.PdfDocument(str(path))
    except Exception as exc:  # noqa: BLE001 - one bad file/page must not sink the batch; recorded in the row
        doc.error = f"open: {exc}"
        return doc
    try:
        v = pdf.get_version()
        doc.pdf_version = f"{v // 10}.{v % 10}" if v else ""
        meta = pdf.get_metadata_dict(skip_empty=True)
        doc.producer = meta.get("Producer", "")
        doc.creator = meta.get("Creator", "")
        doc.encrypted = pdfium_c.FPDF_GetSecurityHandlerRevision(pdf.raw) != -1
        for i in range(len(pdf)):
            doc.pages.append(_measure_page(pdf, i))
        if len(pdf):
            p0 = pdf[0]
            tp = p0.get_textpage()
            doc.first_page_text = re.sub(r"\s+", " ", tp.get_text_range())[:400]
            tp.close()
            p0.close()
    except Exception as exc:  # noqa: BLE001 - one bad file/page must not sink the batch; recorded in the row
        doc.error = f"read: {exc}"
    finally:
        pdf.close()
    pdfium_encrypted = doc.encrypted
    _font_census(path, doc)
    doc.encrypted = doc.encrypted or pdfium_encrypted
    return doc


# --- rows ------------------------------------------------------------------------------------
DOC_FIELDS = [
    "path", "fiscal_year", "family", "family_basis", "family_by_filename", "family_by_title",
    "sha256", "bytes", "pages", "producer", "creator", "pdf_version", "encrypted",
    "page_sizes", "orientations", "rotated_pages",
    "text_class", "textlayer_class", "qa_tier", "special_flags",
    "chars_per_page_mean", "chars_per_page_median", "chars_per_page_min",
    "invisible_char_share", "low_text_pages", "image_only_pages", "short_text_pages",
    "blank_pages",
    "pages_with_images", "vector_rule_density", "ruled_table_pages", "has_ruled_tables",
    "garbled_share", "fonts_total", "fonts_without_tounicode", "fonts_type0_without_tounicode",
    "fonts_type3", "page_errors", "error",
]
PAGE_FIELDS = [
    "path", "page", "chars", "invisible_chars", "traced_chars", "image_area_share", "ink_share",
    "h_rules", "v_rules", "rules", "rects", "curves", "ruled", "rotation", "width", "height",
    "garbled_share", "page_tier", "error",
]


def _counts(items) -> str:
    c: dict[str, int] = {}
    for it in items:
        c[it] = c.get(it, 0) + 1
    return ";".join(f"{k}:{v}" for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def doc_row(doc: DocResult) -> dict:
    pages = doc.pages
    pc = [p.chars for p in pages]
    traced = sum(p.traced_chars for p in pages)
    invisible = sum(p.invisible_chars for p in pages)
    tl = textlayer_class(pc, invisible, traced) if not doc.error.startswith("open") else CLASS_ERROR
    low = low_text_pages(pc)
    short_text: list[int] = []
    if tl == CLASS_SCANNED:
        inked = [p.page for p in pages if p.has_ink]
        blank = [p.page for p in pages if p.ink_share is not None and not p.has_ink]
    else:
        lows = set(low)
        inked = [p.page for p in pages if p.page in lows and p.image_only]
        short_text = [p.page for p in pages if p.page in lows and p.has_ink and not p.image_only]
        blank = [p.page for p in pages if p.page in lows and not p.has_ink]
    # mixed: a text document holding image-only pages, or a scanned document (mean <= 100
    # chars/page) that nevertheless holds real text pages. The textlayer class is kept as-is.
    text_pages = [p.page for p in pages if not p.low_text]
    text_class = CLASS_MIXED if ((tl == CLASS_TEXT and inked)
                                 or (tl == CLASS_SCANNED and text_pages)) else tl
    ruled_pages = [p.page for p in pages if p.ruled]
    has_ruled = bool(pages) and len(ruled_pages) >= max(1, RULED_DOC_MIN_SHARE * len(pages))
    nonspace = sum(p.nonspace_chars for p in pages)
    garbled = (sum(p.garbled_chars for p in pages) / nonspace) if nonspace else 0.0
    by_name = family_from_filename(Path(doc.path).name)
    by_title = family_from_title(doc.first_page_text)
    family, basis = resolve_family(by_name, by_title)

    def orient(p):
        w, h = (p.height, p.width) if p.rotation in (90, 270) else (p.width, p.height)
        return "landscape" if w > h else "portrait"

    flags = []
    if doc.encrypted:
        flags.append("encrypted")
    if garbled > GARBLED_DOC_THRESHOLD:
        flags.append("garbled-text")
    if text_class == CLASS_MIXED:
        flags.append("mixed")
    if any(p.rotation for p in pages):
        flags.append("rotated-pages")
    if doc.error or any(p.error for p in pages):
        flags.append("parse-error")
    if family == FAMILY_UNKNOWN:
        flags.append("family-unknown")
    return {
        "path": doc.path,
        "fiscal_year": fiscal_year_from_path(doc.path),
        "family": family,
        "family_basis": basis,
        "family_by_filename": by_name or "",
        "family_by_title": by_title or "",
        "sha256": doc.sha256,
        "bytes": doc.nbytes,
        "pages": len(pages),
        "producer": doc.producer,
        "creator": doc.creator,
        "pdf_version": doc.pdf_version,
        "encrypted": doc.encrypted,
        "page_sizes": _counts(f"{round(p.width)}x{round(p.height)}" for p in pages),
        "orientations": _counts(orient(p) for p in pages),
        "rotated_pages": compact_pages([p.page for p in pages if p.rotation]),
        "text_class": text_class,
        "textlayer_class": tl,
        "qa_tier": doc_tier(tl, len(ruled_pages) / len(pages) if pages else 0.0),
        "special_flags": ";".join(flags),
        "chars_per_page_mean": round(sum(pc) / len(pc), 2) if pc else 0,
        "chars_per_page_median": statistics.median(pc) if pc else 0,
        "chars_per_page_min": min(pc) if pc else 0,
        "invisible_char_share": round(invisible / traced, 4) if traced else 0.0,
        "low_text_pages": compact_pages(low),
        "image_only_pages": compact_pages(inked),
        "short_text_pages": compact_pages(short_text),
        "blank_pages": compact_pages(blank),
        "pages_with_images": sum(1 for p in pages if p.image_area_share > 0),
        "vector_rule_density": statistics.median(
            [p.h_rules + p.v_rules + p.rects for p in pages]) if pages else 0,
        "ruled_table_pages": len(ruled_pages),
        "has_ruled_tables": has_ruled,
        "garbled_share": round(garbled, 4),
        "fonts_total": doc.fonts_total,
        "fonts_without_tounicode": doc.fonts_without_tounicode,
        "fonts_type0_without_tounicode": doc.fonts_type0_without_tounicode,
        "fonts_type3": doc.fonts_type3,
        "page_errors": compact_pages([p.page for p in pages if p.error]),
        "error": doc.error,
    }


def page_rows(doc: DocResult, text_class_tl: str) -> list[dict]:
    rows = []
    for p in doc.pages:
        rows.append({
            "path": doc.path, "page": p.page, "chars": p.chars,
            "invisible_chars": p.invisible_chars, "traced_chars": p.traced_chars,
            "image_area_share": round(p.image_area_share, 4),
            "ink_share": "" if p.ink_share is None else round(p.ink_share, 4),
            "h_rules": p.h_rules, "v_rules": p.v_rules, "rules": p.h_rules + p.v_rules,
            "rects": p.rects, "curves": p.curves, "ruled": p.ruled, "rotation": p.rotation,
            "width": round(p.width, 1), "height": round(p.height, 1),
            "garbled_share": round(p.garbled_share, 4),
            "page_tier": page_tier(text_class_tl, p), "error": p.error,
        })
    return rows


def _survey_one(args: tuple[str, str]) -> tuple[dict, list[dict]]:
    abspath, rel = args
    doc = survey_pdf(abspath, rel)
    row = doc_row(doc)
    return row, page_rows(doc, row["textlayer_class"])


def run(source: Path, out_dir: Path, repo_root: Path, workers: int) -> tuple[int, int]:
    pdfs = sorted(p for p in source.rglob("*") if p.suffix.lower() == ".pdf" and p.is_file())
    if not pdfs:
        raise SystemExit(f"pdf_condition.py: no PDFs found under {source}")
    for p in pdfs:  # git-LFS pointers would silently survey as garbage
        with open(p, "rb") as fh:
            if fh.read(5) != b"%PDF-":
                raise SystemExit(f"pdf_condition.py: {p} is not a PDF (git-LFS pointer?)")
    jobs = [(str(p), p.relative_to(repo_root).as_posix()) for p in pdfs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(_survey_one, jobs, chunksize=1))
    results.sort(key=lambda r: r[0]["path"])
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "pdf_condition.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=DOC_FIELDS, lineterminator="\n")
        w.writeheader()
        for row, _ in results:
            w.writerow(row)
    n_pages = 0
    with open(out_dir / "pdf_condition_pages.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=PAGE_FIELDS, lineterminator="\n")
        w.writeheader()
        for _, prows in results:
            for pr in prows:
                w.writerow(pr)
                n_pages += 1
    return len(results), n_pages


def main(argv=None) -> int:
    here = Path(__file__).resolve().parent
    repo = here.parent
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--source", type=Path, default=repo / "source")
    ap.add_argument("--out-dir", type=Path, default=repo / "data")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s pdf_condition %(levelname)s %(message)s")
    t0 = time.monotonic()
    log.info("event=start source=%s workers=%d", a.source, a.workers)
    n_docs, n_pages = run(a.source.resolve(), a.out_dir.resolve(), repo, a.workers)
    log.info("event=done pdfs=%d pages=%d seconds=%.1f", n_docs, n_pages, time.monotonic() - t0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
