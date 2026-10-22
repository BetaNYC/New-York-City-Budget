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
            # Its words with their x extents (a loose header line such as "EIN  Amount"
            # spans two columns; FY2024 p.155).
            words, prev = [], None
            for c in g:
                if not c["text"].strip():
                    prev = None
                    continue
                if prev is not None and c["x0"] - prev["x1"] <= x_tolerance and words:
                    words[-1] = [words[-1][0], r2(c["x1"]), words[-1][2] + c["text"]]
                else:
                    words.append([r2(c["x0"]), r2(c["x1"]), c["text"]])
                prev = c
            out.append(dict(
                top=r2(min(c["top"] for c in g)), bottom=r2(max(c["bottom"] for c in g)),
                x0=r2(g[0]["x0"]), x1=r2(g[-1]["x1"]), text=text,
                size=r2(max(c["size"] for c in ink)) if ink else 0.0,
                bold=any("bold" in c["fontname"].lower() for c in ink), words=words))
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


def origin(page):
    """The MediaBox's top-left corner in pdfplumber's frame. pdfplumber reports coordinates
    relative to the PDF's own origin; a page whose MediaBox does not start at (0, 0) (FY2024:
    216 pages with MediaBox [-18.03 17.97 773.97 629.97]) is rendered from its MediaBox corner,
    so every coordinate is shifted by this before it is compared with pixels or written out
    (families/schedule-c-fy2008-fy2024.md, "One coordinate trap"). (0, 0) on most pages."""
    return page.bbox[0], page.bbox[1]


def shift(objs, ox, oy):
    """pdfplumber chars/rects/lines moved to MediaBox-corner coordinates. The same objects,
    untouched, when the page starts at (0, 0)."""
    if not ox and not oy:
        return objs
    return [dict(o, x0=o["x0"] - ox, x1=o["x1"] - ox, top=o["top"] - oy,
                 bottom=o["bottom"] - oy) for o in objs]


def read_page(page, page_no, x_tolerance=X_TOLERANCE, table_settings=None, hrule=False,
              open_top=False):
    """One page -> dict with tables (rows of cells with raw text), loose lines and orphans.
    `table_settings` overrides pdfplumber's lines-strategy defaults for this page only (a
    year's config names the page and says why; FY2025 p.167). Coordinates are from the
    MediaBox's top-left corner (`origin`)."""
    ox, oy = origin(page)
    tables = sorted(page.find_tables(table_settings or {}),
                    key=lambda t: (r2(t.bbox[1]), r2(t.bbox[0])))
    if ox or oy:
        tables = [_ShiftedTable(t, ox, oy) for t in tables]
    hnotes = []
    if open_top:
        ws = shift(page.extract_words(), ox, oy)
        tables = [open_top_row(page, ox, oy, t, ws) for t in tables]
    if hrule:
        tables, hnotes = hrule_tables(page, ox, oy, tables, shift(page.extract_words(), ox, oy))
    if hrule or open_top:
        tables = sorted(tables, key=lambda t: (r2(t.bbox[1]), r2(t.bbox[0])))
    chars = shift(page.chars, ox, oy)
    chars = [c for c in chars]
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
        tab = dict(table_index=ti, bbox=bbox2(t.bbox), rows=rows)
        if isinstance(t, _HruleTable):
            tab.update(hrule=True, splits=[r2(v) for v in t.splits])
            # A character whose box crosses a column split: the split may cut a word.
            tab["split_straddles"] = sum(
                1 for c in tchars if c["text"].strip() and
                any(c["x0"] + 0.3 < v < c["x1"] - 0.3 for v in t.splits))
        out_tables.append(tab)

    # Orphans (in a table's bbox, in no cell: e.g. the values beside an initiative box's
    # labels, which FY2027 draws without a right-hand border) are also read as loose text, so
    # the structure stage sees them. They stay listed in `orphans` for the H7 check.
    loose = [c for c, k in zip(chars, t_of) if k < 0] + orphan_chars
    return dict(page=page_no, width=r2(page.width), height=r2(page.height),
                tables=out_tables, lines=text_lines(loose, x_tolerance),
                loose_char_boxes=[bbox2((c["x0"], c["top"], c["x1"], c["bottom"]))
                                  for c in loose if c["text"].strip()],
                orphans=orphans, zero_width_chars=zero_width,
                **(dict(hrule_notes=hnotes) if hnotes else {}),
                ein_tokens=sum(1 for w in page.extract_words() if EIN_TOKEN.match(w["text"])),
                nonws_chars=sum(1 for c in chars if c["text"].strip()))


# --- Tables ruled with horizontal lines only (FY2024) -------------------------------------
# FY2024 prints many initiative award tables (pp.35-48, 63-69, 123-128, 148-171, 176-190,
# 209-213, ...) with a rule under each row and no vertical rules, so the lines strategy finds
# no table (or a sliver of one, from white-filled boxes). PLAN §3 and
# families/schedule-c-fy2008-fy2024.md ("h-rule-only tables"): rows from the drawn rules,
# columns from the EIN and amount words. Used only where a year's config sets
# `structure.hrule_tables`, and only for stacks of rules whose EIN or amount words the lines
# strategy left outside its cells.
HRULE_MIN_W = 150.0     # pt: a table rule, not an underline
HRULE_MERGE = 2.0       # pt: a rule drawn as a thin filled box has two edges this close
HRULE_ROW_MAX = 45.0    # pt: a row band is at most three lines of 11 pt type
HRULE_ALIGN = 3.0       # pt: the rules of one table start and end within this of each other
AMOUNT_WORD = re.compile(r"^\$[\d,]+$")


def _dark(color):
    """pdfplumber colour -> True if it renders darker than mid-grey (as schedc_cv.ink)."""
    if color is None:
        return True
    if isinstance(color, (int, float)):
        return color < 0.5
    c = list(color)
    if len(c) == 1:
        return c[0] < 0.5
    if len(c) == 3:
        return sum(c) / 3 < 0.5
    if len(c) == 4:
        return (1 - min(1, c[0] + c[3])) * 0.3 + (1 - min(1, c[1] + c[3])) * 0.59 + \
            (1 - min(1, c[2] + c[3])) * 0.11 < 0.5
    return True


def _hrules(page, ox, oy):
    """Dark horizontal rules at least HRULE_MIN_W long: [(y, x0, x1)]. A rule is often drawn
    as several abutting thin boxes (FY2024 p.36: x 54-441, 441-505, 505-558), and a thin box
    has two edges; marks within HRULE_MERGE of the same y whose x ranges touch are one rule."""
    raw = []
    for r in page.rects:
        if r["bottom"] - r["top"] <= 3.0 and \
                ((r.get("fill") and _dark(r.get("non_stroking_color"))) or
                 (r.get("stroke") and _dark(r.get("stroking_color")))):
            raw.append(((r["top"] + r["bottom"]) / 2 - oy, r["x0"] - ox, r["x1"] - ox))
    for ln in page.lines:
        if abs(ln["top"] - ln["bottom"]) <= 1.0 and _dark(ln.get("stroking_color")):
            raw.append(((ln["top"] + ln["bottom"]) / 2 - oy, ln["x0"] - ox, ln["x1"] - ox))
    groups = []
    for y, a, b in sorted(raw):
        if groups and y - groups[-1][-1][0] <= HRULE_MERGE:
            groups[-1].append((y, a, b))
        else:
            groups.append([(y, a, b)])
    out = []
    for g in groups:
        y = sum(v[0] for v in g) / len(g)
        spans = []
        for _, a, b in sorted(g, key=lambda v: v[1]):
            if spans and a <= spans[-1][1] + 1.0:
                spans[-1][1] = max(spans[-1][1], b)
            else:
                spans.append([a, b])
        out += [(y, a, b) for a, b in spans if b - a >= HRULE_MIN_W]
    return sorted(out)


def hrule_tables(page, ox, oy, tables, words):
    """Tables built from stacks of horizontal rules. `tables` are the lines-strategy tables
    (bbox and cells, already shifted); `words` are the page's words, shifted. Returns
    (tables, notes): the page's tables with h-rule tables added.

    A lines-strategy table is *suspect* when no word is in any of its cells (p.161: a column of
    white-filled boxes), when it holds an EIN word that is in none of its cells, or a row with
    an EIN word in its cells but no amount word (FY2024 p.69: white-filled boxes
    make a table of names and EINs, the amounts outside it; p.160: the box table runs on into
    the award rows, whose words fall in no cell). Rules inside the other tables are ignored.

    A stack of rules (same left and right ends, rows at most HRULE_ROW_MAX apart) becomes a
    table from the band above its first EIN word (or the header band above that, if it names
    an EIN or Tax ID column) to its last band with an EIN or amount word, when some EIN or
    amount word in it is in no cell of a kept table. Suspect tables lose their cells inside
    that region; a suspect table left with no cells is dropped. Columns: org | EIN | amount,
    split at the leftmost EIN word and halfway between the EIN and amount words."""
    def cell_of(w, t):
        cx, cy = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
        return next((c for c in t.cells if c[0] <= cx < c[2] and c[1] <= cy < c[3]), None)

    def in_box(w, b):
        cx, cy = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
        return b[0] <= cx < b[2] and b[1] <= cy < b[3]

    ein_w = [w for w in words if EIN_TOKEN.match(w["text"])]
    amt_w = [w for w in words if AMOUNT_WORD.match(w["text"])]
    suspect = set()
    for k, t in enumerate(tables):
        if not any(cell_of(w, t) for w in words):
            suspect.add(k)          # no word in any cell: white-filled boxes only (p.161)
            continue
        tops_amt = {cell_of(w, t)[1] for w in amt_w if cell_of(w, t)}
        for w in ein_w:
            if not in_box(w, t.bbox):
                continue
            c = cell_of(w, t)
            if c is None or c[1] not in tops_amt:
                suspect.add(k)
                break
    keep = [t for k, t in enumerate(tables) if k not in suspect]
    all_rules = _hrules(page, ox, oy)
    rules = [(y, a, b) for y, a, b in all_rules
             if not any(t.bbox[1] + 0.5 < y < t.bbox[3] - 0.5 and a < t.bbox[2] and
                        b > t.bbox[0] for t in keep)]
    stacks = []
    for y, a, b in rules:
        st = stacks[-1] if stacks else None
        if st and abs(a - st["x0"]) <= HRULE_ALIGN and abs(b - st["x1"]) <= HRULE_ALIGN and \
                y - st["ys"][-1] <= HRULE_ROW_MAX:
            st["ys"].append(y)
        else:
            stacks.append(dict(x0=a, x1=b, ys=[y]))
    kept_cells = [c for t in keep for c in t.cells]

    def loose(w):
        cx, cy = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
        return not any(c[0] <= cx < c[2] and c[1] <= cy < c[3] for c in kept_cells)

    trimmed = {k: list(tables[k].cells) for k in suspect}
    new, notes = [], []
    for st in stacks:
        x0, x1, ys = st["x0"], st["x1"], st["ys"]
        # A first row with no rule above it (p.152): the band over the first rule, back to the
        # nearest rule, when it holds an EIN word and an amount word.
        floor = max([y for y, _, _ in all_rules if y < ys[0] - 1.0], default=0.0)
        over = [w for w in words if x0 <= (w["x0"] + w["x1"]) / 2 < x1 and w["top"] > floor
                and ys[0] - HRULE_ROW_MAX < (w["top"] + w["bottom"]) / 2 < ys[0]]
        if any(EIN_TOKEN.match(w["text"]) for w in over) and \
                any(AMOUNT_WORD.match(w["text"]) for w in over) and \
                not any(t.bbox[1] < ys[0] - 1.0 and t.bbox[3] > min(w["top"] for w in over)
                        and t.bbox[0] < x1 and t.bbox[2] > x0 for t in keep):
            ys = [max(floor, min(w["top"] for w in over) - 2.0)] + ys
        bands = list(zip(ys, ys[1:]))
        bw = [[w for w in words if in_box(w, (x0, ya, x1, yb))] for ya, yb in bands]
        has = [any(EIN_TOKEN.match(w["text"]) or AMOUNT_WORD.match(w["text"]) for w in ws)
               for ws in bw]
        data = [i for i, ws in enumerate(bw) if any(EIN_TOKEN.match(w["text"]) for w in ws)]
        if not data:
            continue
        first, last = data[0], data[-1]
        if first > 0 and not has[first - 1] and \
                any(w["text"] in ("EIN", "ID") for w in bw[first - 1]):
            first -= 1
        ys = ys[first:last + 2]
        top, bottom = ys[0], ys[-1]
        inside = [w for w in words if in_box(w, (x0, top, x1, bottom))]
        eins = [w for w in inside if EIN_TOKEN.match(w["text"])]
        amts = [w for w in inside if AMOUNT_WORD.match(w["text"])]
        if not [w for w in eins + amts if loose(w)]:
            continue
        if not amts or max(w["x1"] for w in eins) >= min(w["x0"] for w in amts):
            notes.append(f"h-rule stack at y {top:.1f}-{bottom:.1f}: EIN and amount words do "
                         "not form two columns; not read")
            continue
        b1 = min(w["x0"] for w in eins) - 0.5
        b2 = (max(w["x1"] for w in eins) + min(w["x0"] for w in amts)) / 2
        for k in trimmed:
            trimmed[k] = [c for c in trimmed[k] if not (
                (c[1] + c[3]) / 2 > top and (c[1] + c[3]) / 2 < bottom and
                c[0] < x1 and c[2] > x0)]
        tcells = []
        for ya, yb in zip(ys, ys[1:]):
            tcells += [(x0, ya, b1, yb), (b1, ya, b2, yb), (b2, ya, x1, yb)]
        new.append(_HruleTable((x0, top, x1, bottom), tcells, (b1, b2)))
    if not new:
        return tables, notes
    out = [t for k, t in enumerate(tables) if k not in suspect]
    for k in sorted(suspect):
        cs = trimmed[k]
        if cs == list(tables[k].cells):
            out.append(tables[k])
        elif cs:
            out.append(_Cells((min(c[0] for c in cs), min(c[1] for c in cs),
                               max(c[2] for c in cs), max(c[3] for c in cs)), cs))
    return out + new, notes


def open_top_row(page, ox, oy, t, words=None):
    """A lines-strategy table whose column rules run up past its top rule into a band with no
    rule above it (FY2024 pp.41-46: the first row of a page's table has no top rule; its
    vertical rules start 13 pt higher). Returns the table with that band added as a row, cut
    at the first row's column rules, or the table unchanged. Every column rule must reach the
    same height (within 1 pt) and the band must be at most HRULE_ROW_MAX tall."""
    top = min(c[1] for c in t.cells)
    first = [c for c in t.cells if c[1] == top]
    xs = sorted({c[0] for c in first} | {c[2] for c in first})
    v = [(e["x0"] - ox, e["top"] - oy) for e in page.edges if e["orientation"] == "v" and
         abs(e["bottom"] - oy - top) <= 1.0 and e["top"] - oy < top - 5]
    ups = []
    for x in xs:
        hit = [y for ex, y in v if abs(ex - x) <= 1.0]
        if not hit:
            ups = None
            break
        ups.append(min(hit))
    if ups is None:
        # No column rules above either (p.152: "Planned Parenthood ... 13-2621497 $374,219"
        # sits over the first rule with nothing drawn above it but the page-header rule). The
        # band is taken only when it holds an EIN word and an amount word, from just above
        # its highest word, and never above the nearest rule.
        if words is None:
            return t
        band = [w for w in words if xs[0] <= (w["x0"] + w["x1"]) / 2 < xs[-1] and
                top - HRULE_ROW_MAX < (w["top"] + w["bottom"]) / 2 < top]
        ruled = [y for y, a, b in _hrules(page, ox, oy) if y < top - 1.0]
        floor = max(ruled) if ruled else 0.0
        band = [w for w in band if w["top"] > floor]
        if not (any(EIN_TOKEN.match(w["text"]) for w in band) and
                any(AMOUNT_WORD.match(w["text"]) for w in band)):
            return t
        ups = [max(floor, min(w["top"] for w in band) - 2.0)]
    y0 = max(ups)
    if max(ups) - min(ups) > 1.0 or top - y0 > HRULE_ROW_MAX:
        return t
    cells = [(a, y0, b, top) for a, b in zip(xs, xs[1:])] + list(t.cells)
    return _Cells((t.bbox[0], y0, t.bbox[2], t.bbox[3]), cells)


class _Cells:
    """A lines-strategy table with cells changed: cut down to the cells above an h-rule table,
    or with an open top row added."""

    def __init__(self, bbox, cells):
        self.bbox, self.cells = bbox, cells


class _HruleTable:
    """A table built by `hrule_tables`: bbox, cells and its two column splits."""

    def __init__(self, bbox, cells, splits):
        self.bbox, self.cells, self.splits = bbox, cells, splits


class _ShiftedTable:
    """A pdfplumber table's bbox and cells, moved by (-ox, -oy)."""

    def __init__(self, t, ox, oy):
        b = t.bbox
        self.bbox = (b[0] - ox, b[1] - oy, b[2] - ox, b[3] - oy)
        self.cells = [(c[0] - ox, c[1] - oy, c[2] - ox, c[3] - oy) for c in t.cells]


def read_pdf(pdf_path, pages=None, x_tolerance=X_TOLERANCE, page_settings=None, hrule=False,
             open_top=False):
    """`page_settings`: {page number: pdfplumber table settings} for the few pages a year's
    config overrides; every other page uses pdfplumber's defaults."""
    import pdfplumber
    out = []
    page_settings = page_settings or {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if pages and (i + 1) not in pages:
                continue
            out.append(read_page(page, i + 1, x_tolerance, page_settings.get(i + 1), hrule,
                                 open_top))
            page.flush_cache()
    return out
