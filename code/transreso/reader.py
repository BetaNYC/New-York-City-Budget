"""
Stages 3 and 5 for transparency charts -- vector lattice and cell text, read by runs.

The lattice is the PDF's own drawn borders (pdfplumber `find_tables()`, lines strategy), as in
code/schedc/vector.py. Three things differ, all measured on the FY2026 resolutions:

1. **Runs, and clipped text.** The charts are Excel exports. Excel draws each cell's text as
   one run and clips it at the next drawn rule, but the clipped letters stay in the text layer
   (FY2026 Reso 08 p.19: "…Modern History of Polan" shows; "d, Inc. - Stories of Greenpoint"
   is hidden under the EIN cell). A *run* is a stretch of characters drawn one after another
   in the content stream, on one line, each starting no more than `run_gap` pt after the last
   ends. A run belongs to the cell that holds its first character's centre. Its characters
   whose centre falls in another drawn cell are clipped: not emitted, and listed in `clipped`
   so a person sees every one. If one of them was in fact visible, the ink check finds it.
2. **Spanning cells.** On purpose-of-funds charts the data rows draw no rule between Source
   and Member, so one drawn cell spans two header columns (FY2026 Reso 01 p.91). Its runs are
   split by the header's column edges, each run going where its first character sits.
3. **Missing cells.** Where a row has no drawn cell under a header column (the `*` column on
   some pages, the last purpose cell on Reso 03 p.81), the cell is the header column's
   x-range across the row's band. Characters in it are read, and the row is flagged.

Nothing is dropped silently: every non-space character inside a table ends in a cell, in
`clipped`, or in `orphans`, and the checks count all three.
"""
import re

from schedc.vector import (LINE_TOL, ZERO_WIDTH, EIN_TOKEN, _assign, bbox2, chars_to_text, r2,
                           text_lines)

RUN_GAP = 3.0
# Where a run crosses a drawn cell edge, clipped text continues the word with no gap (measured
# -0.07..+0.07 pt on every clipped run in FY2026). A new cell's own text starts after the cell
# padding (0.98 pt and 2.85 pt measured on Reso 01 p.85 and Reso 04 p.34). Over this gap, a
# crossing starts a new run.
CLIP_GAP_MAX = 0.5
# A header column is under a data cell when they overlap by more than this (pt). Drawn rules
# line up to 0.01 pt in these files; 2 pt ignores a rule's own width.
OVERLAP_MIN = 2.0


def runs(chars, gap=RUN_GAP, cell=None):
    """Content-stream runs (see module docstring). `chars` in stream order. A run also ends
    where the fill colour changes (a red amount, then black text), and, when `cell(c)` gives
    each char's drawn cell, where it crosses a cell edge with a gap over CLIP_GAP_MAX."""
    out, cur = [], []
    for c in chars:
        if cur:
            p = cur[-1]
            g = c["x0"] - p["x1"]
            if abs(c["top"] - p["top"]) <= LINE_TOL and c["x0"] >= p["x0"] - 0.01 and \
                    g <= gap and c.get("non_stroking_color") == p.get("non_stroking_color") and \
                    (cell is None or g <= CLIP_GAP_MAX or cell(c) == cell(p)):
                cur.append(c)
                continue
            out.append(cur)
        cur = [c]
    if cur:
        out.append(cur)
    return out


def _centre(c):
    return (c["x0"] + c["x1"]) / 2, (c["top"] + c["bottom"]) / 2


def _inside(c, b):
    cx, cy = _centre(c)
    return b[0] <= cx < b[2] and b[1] <= cy < b[3]


def is_red(color):
    """pdfplumber non-stroking colour -> True for the red the charts print rescissions in."""
    if isinstance(color, (list, tuple)) and len(color) == 3:
        r, g, b = color
        return r > 0.6 and g < 0.35 and b < 0.35
    return False


def _cell_rec(chars, bbox, how, x_tolerance, hidden=""):
    ink = [c for c in chars if c["text"].strip()]
    return dict(bbox=bbox2(bbox), how=how, text_raw=chars_to_text(chars, x_tolerance),
                hidden=hidden,
                nchars=len(ink), red=sum(1 for c in ink if is_red(c.get("non_stroking_color"))),
                char_boxes=[bbox2((c["x0"], c["top"], c["x1"], c["bottom"])) for c in ink])


def read_page(page, page_no, x_tolerance=3.0, run_gap=RUN_GAP):
    tables = sorted(page.find_tables(), key=lambda t: (r2(t.bbox[1]), r2(t.bbox[0])))
    allchars = list(page.chars)
    zero_width = sum(1 for c in allchars if c["text"] in ZERO_WIDTH)
    chars = [c for c in allchars if c["text"] not in ZERO_WIDTH]

    # Every drawn cell on the page, for run ownership.
    cells = []                       # (table_index, bbox)
    for ti, t in enumerate(tables):
        for b in sorted({tuple(r2(v) for v in c) for c in t.cells}, key=lambda b: (b[1], b[0])):
            cells.append((ti, b))
    cell_of = _assign(chars, [b for _, b in cells])
    idx = {id(c): k for k, c in enumerate(chars)}

    clipped_ids, clipped, hidden_of = set(), [], {}
    for run in runs(chars, run_gap, cell=lambda c: cell_of[idx[id(c)]]):
        k0 = cell_of[idx[id(run[0])]]
        if k0 < 0:
            continue
        hidden = [c for c in run if cell_of[idx[id(c)]] != k0 and c["text"].strip()]
        if hidden:
            clipped_ids.update(id(c) for c in run if cell_of[idx[id(c)]] != k0)
            hidden_of[k0] = (hidden_of.get(k0, "") + "".join(
                c["text"] for c in run if cell_of[idx[id(c)]] != k0)).strip()
            ti, b = cells[k0]
            clipped.append(dict(table=ti, owner_bbox=list(b),
                                run_text="".join(c["text"] for c in run),
                                hidden_text="".join(c["text"] for c in run
                                                    if cell_of[idx[id(c)]] != k0),
                                bbox=bbox2((min(c["x0"] for c in hidden),
                                            min(c["top"] for c in hidden),
                                            max(c["x1"] for c in hidden),
                                            max(c["bottom"] for c in hidden)))))
    visible = [c for c in chars if id(c) not in clipped_ids]

    tboxes = [t.bbox for t in tables]
    t_of = _assign(visible, tboxes)
    out_tables, orphans, loose = [], [], []
    for ti, t in enumerate(tables):
        tchars = [c for c, k in zip(visible, t_of) if k == ti]
        tcells = [b for tj, b in cells if tj == ti]
        gidx = [k for k, (tj, _) in enumerate(cells) if tj == ti]   # table cell -> page cell
        c_of = _assign(tchars, tcells)
        by_cell = {}
        free = []
        for c, k in zip(tchars, c_of):
            if k < 0:
                free.append(c)
            else:
                by_cell.setdefault(int(k), []).append(c)
        tops = sorted({b[1] for b in tcells})
        bands = []
        for top in tops:
            ks = [k for k, b in enumerate(tcells) if b[1] == top]
            bands.append((top, min(tcells[k][3] for k in ks), sorted(ks, key=lambda k: tcells[k][0])))
        # Header = the first band; its cells are the columns.
        h_top, h_bot, h_ks = bands[0]
        header = []
        for k in h_ks:
            b = tcells[k]
            rec = _cell_rec(by_cell.get(k, []), b, "cell", x_tolerance)
            rec["label"] = " ".join(rec["text_raw"].split())
            header.append(rec)
        rows = []
        for ri, (top, bot, ks) in enumerate(bands[1:], start=1):
            cols, flags = {}, []
            for k in ks:
                b = tcells[k]
                under = [j for j, h in enumerate(header)
                         if min(b[2], h["bbox"][2]) - max(b[0], h["bbox"][0]) > OVERLAP_MIN]
                cs = by_cell.get(k, [])
                hid = hidden_of.get(gidx[k], "")
                if len(under) == 1:
                    cols[under[0]] = _cell_rec(cs, b, "cell", x_tolerance, hid)
                elif len(under) > 1:
                    flags.append("spanning_cell:" + "+".join(header[j]["label"] for j in under))
                    parts = {j: [] for j in under}
                    for run in runs(cs, run_gap):
                        cx = _centre(run[0])[0]
                        j = next((j for j in under if header[j]["bbox"][0] <= cx < header[j]["bbox"][2]),
                                 under[0] if cx < header[under[0]]["bbox"][0] else under[-1])
                        parts[j] += run
                    for j in under:
                        hb = header[j]["bbox"]
                        cols[j] = _cell_rec(parts[j], (max(b[0], hb[0]), b[1], min(b[2], hb[2]), b[3]),
                                            "split", x_tolerance, hid if j == under[0] else "")
                elif cs:
                    flags.append("cell_outside_header")
            for j, h in enumerate(header):
                if j in cols:
                    continue
                hb = h["bbox"]
                sb = (hb[0], top, hb[2], bot)
                got = [c for c in free if _inside(c, sb)]
                free = [c for c in free if not _inside(c, sb)]
                cols[j] = _cell_rec(got, sb, "made", x_tolerance)
                # An empty made cell (the `*` column with no rule) changes nothing; one that
                # holds text does, and goes to review.
                flags.append(("made_cell:" if got else "made_cell_empty:") + h["label"])
            rb = bbox2((min(c["bbox"][0] for c in cols.values()), top,
                        max(c["bbox"][2] for c in cols.values()), bot))
            rows.append(dict(row_index=ri, top=r2(top), bottom=r2(bot), bbox=rb, cols=cols,
                             flags=flags))
        for c in free:
            if c["text"].strip():
                orphans.append(dict(table=ti, text=c["text"],
                                    bbox=bbox2((c["x0"], c["top"], c["x1"], c["bottom"]))))
        loose += free
        out_tables.append(dict(table_index=ti, bbox=bbox2(t.bbox), header=header, rows=rows))

    outside = [c for c, k in zip(visible, t_of) if k < 0]
    words_all = page.extract_words()
    vis_page = page.filter(lambda o: o.get("object_type") != "char" or id(o) not in clipped_ids)
    words_vis = vis_page.extract_words()
    return dict(page=page_no, width=r2(page.width), height=r2(page.height),
                rotation=int(page.rotation or 0), tables=out_tables,
                lines=text_lines(outside + loose, x_tolerance),
                loose_char_boxes=[bbox2((c["x0"], c["top"], c["x1"], c["bottom"]))
                                  for c in outside if c["text"].strip()],
                orphans=orphans, clipped=clipped, zero_width_chars=zero_width,
                ein_tokens=sum(1 for w in words_vis if EIN_TOKEN.match(w["text"])),
                ein_tokens_all_chars=sum(1 for w in words_all if EIN_TOKEN.match(w["text"])),
                nonws_chars=sum(1 for c in chars if c["text"].strip()),
                clipped_chars=sum(1 for c in chars if id(c) in clipped_ids and c["text"].strip()))


def read_pdf(pdf_path, x_tolerance=3.0, run_gap=RUN_GAP, pages=None):
    import pdfplumber
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if pages and (i + 1) not in pages:
                continue
            out.append(read_page(page, i + 1, x_tolerance, run_gap))
            page.flush_cache()
    return out


MONEY = re.compile(r"\(?\$[\d,]+(?:\.\d\d)?\)?")
