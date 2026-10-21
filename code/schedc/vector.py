"""
Stages 3 and 5 -- the vector lattice and cell text (PLAN §3).

The lattice is the PDF's own drawn borders, found by pdfplumber `find_tables()` with its
default lines strategy. Cell text is NOT pdfplumber's `extract()`: each PDF character goes to
the one cell that holds its centre. That is Christian Moscardi's `assign_words` rule
(code/ocr/recognize.py), applied to PDF characters instead of OCR words. It is what keeps a
stray hyphen or a glyph that pokes over a rule from landing in the neighbouring cell.

Characters outside every table are returned as `loose` text lines, which the structure stage
reads for headings and designation statements. Nothing is dropped silently: every
non-whitespace character on a page ends up in a cell, in a loose line, or in `orphans`
(inside a table's bbox but in no cell), and `orphans` is a check (H7).

Coordinates are pdfplumber's: points, origin top-left, rounded to 0.01 pt on output.
"""
import re

import numpy as np

# Two characters are on one text line when their tops are this close (pt). Body text is 8-11 pt
# with >= 2.4 pt leading gaps between lines in FY2027 cells, so 2.0 pt joins a line's glyphs
# (superscript-free text; tops vary < 0.6 pt within a line) without merging adjacent lines.
LINE_TOL = 2.0
# A gap wider than this between two glyphs on a line is a word break even with no space glyph.
# pdfplumber's own default (x_tolerance=3). Per-year config may override (PLAN §2.2).
X_TOLERANCE = 3.0
# An EIN-shaped word, for the anchor census (H5): pdfplumber's own word extraction is a read
# independent of our cell assignment. A leading/trailing '*' is a footnote mark, not the EIN.
EIN_TOKEN = re.compile(r"^\*?(\d{2}-\d{7}|\d{9})\*?$")
ZERO_WIDTH = {"​", "‌", "‍", "﻿", "­"}


def r2(v):
    return round(float(v) + 0.0, 2)


def bbox2(b):
    return [r2(v) for v in b]


def chars_to_text(chars, x_tolerance=X_TOLERANCE):
    """Characters -> raw text. Lines top to bottom, joined with '\\n'; glyphs left to right,
    with a space where the PDF has a space glyph or the gap exceeds x_tolerance. Nothing else
    is changed: no dehyphenation, no case or punctuation repair."""
    if not chars:
        return ""
    lines = []
    for c in sorted(chars, key=lambda c: (c["top"], c["x0"])):
        if lines and abs(c["top"] - lines[-1][0]) <= LINE_TOL:
            lines[-1][1].append(c)
        else:
            lines.append([c["top"], [c]])
    out = []
    for _, cs in lines:
        cs.sort(key=lambda c: c["x0"])
        s, prev = [], None
        for c in cs:
            if prev is not None and c["x0"] - prev["x1"] > x_tolerance and s and s[-1] != " " \
                    and c["text"] != " ":
                s.append(" ")
            s.append(c["text"])
            prev = c
        out.append("".join(s).strip(" "))
    return "\n".join(ln for ln in out if ln != "")


def text_lines(chars, x_tolerance=X_TOLERANCE):
    """Loose characters -> [{top, bottom, x0, x1, text, size, bold}], top to bottom. A line is
    split where the horizontal gap is wide (> 40 pt), so side-by-side labels stay apart."""
    rows = []
    for c in sorted(chars, key=lambda c: (c["top"], c["x0"])):
        if rows and abs(c["top"] - rows[-1][0]) <= LINE_TOL:
            rows[-1][1].append(c)
        else:
            rows.append([c["top"], [c]])
    out = []
    for _, cs in rows:
        cs.sort(key=lambda c: c["x0"])
        groups = [[cs[0]]]
        for c in cs[1:]:
            if c["x0"] - groups[-1][-1]["x1"] > 40:
                groups.append([c])
            else:
                groups[-1].append(c)
        for g in groups:
            text = chars_to_text(g, x_tolerance)
            if not text.strip():
                continue
            ink = [c for c in g if c["text"].strip()]
            out.append(dict(
                top=r2(min(c["top"] for c in g)), bottom=r2(max(c["bottom"] for c in g)),
                x0=r2(g[0]["x0"]), x1=r2(g[-1]["x1"]), text=text,
                size=r2(max(c["size"] for c in ink)) if ink else 0.0,
                bold=any("bold" in c["fontname"].lower() for c in ink)))
    return out


def _assign(chars, boxes):
    """Index of the box holding each char's centre, or -1. Boxes are (x0, top, x1, bottom).
    Boxes from one lattice do not overlap, so 'the' box is unique; ties (a centre exactly on a
    shared edge) go to the first box in reading order, matching half-open [lo, hi) bands."""
    if not chars or not boxes:
        return np.full(len(chars), -1, dtype=int)
    cx = np.array([(c["x0"] + c["x1"]) / 2 for c in chars])
    cy = np.array([(c["top"] + c["bottom"]) / 2 for c in chars])
    b = np.array(boxes, dtype=float)
    inside = ((cx[:, None] >= b[None, :, 0]) & (cx[:, None] < b[None, :, 2]) &
              (cy[:, None] >= b[None, :, 1]) & (cy[:, None] < b[None, :, 3]))
    hit = inside.any(axis=1)
    return np.where(hit, inside.argmax(axis=1), -1)


def read_page(page, page_no, x_tolerance=X_TOLERANCE, table_settings=None):
    """One page -> dict with tables (rows of cells with raw text), loose lines and orphans.
    `table_settings` overrides pdfplumber's lines-strategy defaults for this page only (a
    year's config names the page and says why; FY2025 p.167)."""
    tables = sorted(page.find_tables(table_settings or {}),
                    key=lambda t: (r2(t.bbox[1]), r2(t.bbox[0])))
    chars = [c for c in page.chars]
    zero_width = sum(1 for c in chars if c["text"] in ZERO_WIDTH)
    chars = [c for c in chars if c["text"] not in ZERO_WIDTH]

    tboxes = [t.bbox for t in tables]
    t_of = _assign(chars, tboxes)
    out_tables = []
    orphans = []
    orphan_chars = []
    for ti, t in enumerate(tables):
        tchars = [c for c, k in zip(chars, t_of) if k == ti]
        cells = sorted({tuple(r2(v) for v in c) for c in t.cells}, key=lambda b: (b[1], b[0]))
        c_of = _assign(tchars, cells)
        by_cell = {}
        for c, k in zip(tchars, c_of):
            if k < 0:
                orphan_chars.append(c)
                if c["text"].strip():
                    orphans.append(dict(table=ti, text=c["text"], bbox=bbox2(
                        (c["x0"], c["top"], c["x1"], c["bottom"]))))
                continue
            by_cell.setdefault(int(k), []).append(c)
        # Row bands: distinct cell tops, as pdfplumber's Table.rows groups them.
        tops = sorted({b[1] for b in cells})
        rows = []
        for ri, top in enumerate(tops):
            rc = []
            for ci, b in enumerate(cells):
                if b[1] != top:
                    continue
                cs = by_cell.get(ci, [])
                rc.append(dict(bbox=list(b), text_raw=chars_to_text(cs, x_tolerance),
                               nchars=sum(1 for c in cs if c["text"].strip()),
                               char_boxes=[bbox2((c["x0"], c["top"], c["x1"], c["bottom"]))
                                           for c in cs if c["text"].strip()]))
            rc.sort(key=lambda d: d["bbox"][0])
            bottom = min(c["bbox"][3] for c in rc)
            rows.append(dict(row_index=ri, top=top, bottom=bottom, cells=rc))
        out_tables.append(dict(table_index=ti, bbox=bbox2(t.bbox), rows=rows))

    # Orphans (in a table's bbox, in no cell: e.g. the values beside an initiative box's
    # labels, which FY2027 draws without a right-hand border) are also read as loose text, so
    # the structure stage sees them. They stay listed in `orphans` for the H7 check.
    loose = [c for c, k in zip(chars, t_of) if k < 0] + orphan_chars
    return dict(page=page_no, width=r2(page.width), height=r2(page.height),
                tables=out_tables, lines=text_lines(loose, x_tolerance),
                loose_char_boxes=[bbox2((c["x0"], c["top"], c["x1"], c["bottom"]))
                                  for c in loose if c["text"].strip()],
                orphans=orphans, zero_width_chars=zero_width,
                ein_tokens=sum(1 for w in page.extract_words() if EIN_TOKEN.match(w["text"])),
                nonws_chars=sum(1 for c in chars if c["text"].strip()))


def read_pdf(pdf_path, pages=None, x_tolerance=X_TOLERANCE, page_settings=None):
    """`page_settings`: {page number: pdfplumber table settings} for the few pages a year's
    config overrides; every other page uses pdfplumber's defaults."""
    import pdfplumber
    out = []
    page_settings = page_settings or {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if pages and (i + 1) not in pages:
                continue
            out.append(read_page(page, i + 1, x_tolerance, page_settings.get(i + 1)))
            page.flush_cache()
    return out
