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
   A run that starts in an undrawn cell and runs past the table's edge is cut there the same
   way (FY2025 Reso 07 pp.29-30: staff notes past the `*` column, only "01/" shows).
2. **Spanning cells.** On purpose-of-funds charts the data rows draw no rule between Source
   and Member, so one drawn cell spans two header columns (FY2026 Reso 01 p.91). Its runs are
   split by the header's column edges, each run going where its first character sits.
3. **Missing cells.** Where a row has no drawn cell under a header column (the `*` column on
   some pages, the last purpose cell on Reso 03 p.81), the cell is the header column's
   x-range across the row's band. Characters in it are read, and the row is flagged.

4. **Overfull cells** (FY2019, FY2018). Where a cell's text wraps to more lines than its row
   is tall, Excel centres the text block on the row and draws it across the rules above and
   below (FY2019 Reso 07 p.27: "Alvin Ailey Dance Foundation, Inc. - … Social Services," /
   "Inc." in a one-line row, its "Inc." on top of the next row's first line). On pages the
   config names (check T7.overfull), a cell's lines are one *block* (runs drawn one after
   another, each next line starting at the block's left edge one line lower), and the whole
   block belongs to the cell that holds the block's vertical middle. Elsewhere nothing changes.

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
# crossing starts a new run. So does a letter that starts more than this before the last one
# ends (FY2024 Reso 02 p.11: the clipped "n" of "Staten Island Delegation" ends 0.95 pt after
# "South Shore ..." begins, and both centres fall in the next cell).
CLIP_GAP_MAX = 0.5
# A header column is under a data cell when they overlap by more than this (pt). Drawn rules
# line up to 0.01 pt in these files; 2 pt ignores a rule's own width.
OVERLAP_MIN = 2.0
# On pages named in the config (check T7.overlaid), a run whose first letter lies more than this
# share of its width on top of a letter drawn earlier on the same line is overlaid text that the
# page does not show (FY2022 Reso 09 p.38:
# "Funding to go support …" is drawn over the EIN "13-4170389" and clipped away when rendered).
# Only letters an earlier run shows in its own cell count (see `overlaid`).
OVERLAY_SHARE = 0.5
# A letter drawn more than this (pt) above or below the cell it is read into is overfull text
# (T7.overfull). Letters in cells that fit stay inside their cell's box; FY2020-FY2026 have none.
OVERFULL_PT = 1.5
# Block lines (see `block_ys`): a next line starts within this (pt) of the block's left edge and
# at most this many letter heights below the line before.
BLOCK_X_TOL = 1.0
BLOCK_PITCH = 1.6


def overlaid(run_list, cell):
    """Indexes of runs whose first ink letter starts on top of a letter that an earlier run
    shows in its own cell. Letters an earlier run carries past its cell are clipped, so text
    drawn over them is the visible text (FY2025 Reso 01 pp.59-61, FY2026 Reso 02 p.110)."""
    seen, out = [], set()
    for k, run in enumerate(run_list):
        ink = [c for c in run if c["text"].strip() and not c["text"].startswith("(cid:")]
        if ink:
            f = ink[0]
            w = max(f["x1"] - f["x0"], 0.01)
            if any(abs(f["top"] - c["top"]) <= LINE_TOL and
                   min(f["x1"], c["x1"]) - max(f["x0"], c["x0"]) > OVERLAY_SHARE * w for c in seen):
                out.add(k)
                continue
            own = cell(run[0])
            seen += [c for c in ink if cell(c) == own]
    return out


def runs(chars, gap=RUN_GAP, cell=None, restart=False):
    """Content-stream runs (see module docstring). `chars` in stream order. A run also ends
    where the fill colour changes (a red amount, then black text), and, when `cell(c)` gives
    each char's drawn cell, where it crosses a cell edge with a gap over CLIP_GAP_MAX or where
    a letter overlaps the last by more than CLIP_GAP_MAX."""
    out, cur = [], []
    for c in chars:
        if cur:
            p = cur[-1]
            g = c["x0"] - p["x1"]
            # `restart` (pages the config names, T7.clip_restart): text already carried past its
            # own cell continues only with no gap; a gap over CLIP_GAP_MAX there is the next
            # cell's own text starting after its padding (FY2018 Reso 04 p.52: "…Velocity Track
            # Club New York" runs into the EIN cell, and the EIN "46-3197831" follows 0.99 pt
            # after the "k"). Not everywhere: hidden text can itself have such gaps (FY2018 Reso
            # 03 p.72, "Inc.(COMET)" drawn with no space glyph).
            if abs(c["top"] - p["top"]) <= LINE_TOL and c["x0"] >= p["x0"] - 0.01 and \
                    g <= gap and c.get("non_stroking_color") == p.get("non_stroking_color") and \
                    (cell is None or (g >= -CLIP_GAP_MAX and (g <= CLIP_GAP_MAX or (
                        cell(c) == cell(p) and not (restart and cell(p) != cell(cur[0])))))):
                cur.append(c)
                continue
            out.append(cur)
        cur = [c]
    if cur:
        out.append(cur)
    return out


def block_ys(chars, box_of, run_gap=RUN_GAP):
    """{id(char): the vertical middle of its text block} for chars in blocks of two or more
    lines (overfull cells, module docstring item 4). `chars` in stream order; `box_of(c)` is the
    box (x0, top, x1, bottom) holding the char's centre, or None. A next line joins the block
    only if it is in the same box as the line before, or it and a line already in the block are
    both drawn across their boxes' rules: some rows are drawn column by column, and a line that
    fits its own row is never part of the next row's block (FY2019 Reso 07 p.27, Borough
    "Eugene" in rows 2 and 3; Reso 04 p.40, rows 1 and 2)."""
    def over(line):
        # A letter in no box at all is past the table's edge (FY2019 Reso 04 p.49, "67K" under
        # the last row): drawn across the rule too.
        return any(c["text"].strip() and (box_of(c) is None or overshoot(c, box_of(c)) > OVERFULL_PT)
                   for c in line)
    blocks = []
    for run in runs(chars, run_gap):
        f = run[0]
        if blocks:
            b = blocks[-1]
            last = b["lines"][-1]
            if abs(f["top"] - last[0]["top"]) <= LINE_TOL and f["x0"] >= last[-1]["x1"] - 0.5:
                last.extend(run)
                continue
            h = max(f["bottom"] - f["top"], 0.01)
            if 0 < f["top"] - last[0]["top"] <= BLOCK_PITCH * h and abs(f["x0"] - b["x0"]) <= BLOCK_X_TOL \
                    and (box_of(f) == box_of(last[0]) or (b["over"] and over(run))):
                b["lines"].append(list(run))
                b["over"] = b["over"] or over(run)
                continue
        blocks.append(dict(x0=f["x0"], lines=[list(run)], over=over(run)))
    out = {}
    for b in blocks:
        if len(b["lines"]) < 2:
            continue
        cs = [c for ln in b["lines"] for c in ln]
        mid = (min(c["top"] for c in cs) + max(c["bottom"] for c in cs)) / 2
        out.update((id(c), mid) for c in cs)
    return out


def _assign_y(chars, boxes, ys):
    """_assign, with a char's vertical centre taken from `ys` (id -> y) where it is listed."""
    if not ys:
        return _assign(chars, boxes)
    return _assign([dict(x0=c["x0"], x1=c["x1"], top=ys[id(c)], bottom=ys[id(c)]) if id(c) in ys
                    else c for c in chars], boxes)


def overshoot(c, b):
    """How far (pt) letter `c` is drawn above or below box `b`."""
    return max(b[1] - c["top"], c["bottom"] - b[3])


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


def read_page(page, page_no, x_tolerance=3.0, run_gap=RUN_GAP, overlay=False, overfull=False,
              restart=False):
    tables = sorted(page.find_tables(), key=lambda t: (r2(t.bbox[1]), r2(t.bbox[0])))
    allchars = list(page.chars)
    zero_width = sum(1 for c in allchars if c["text"] in ZERO_WIDTH)
    chars = [c for c in allchars if c["text"] not in ZERO_WIDTH]

    # Every drawn cell on the page, for run ownership.
    cells = []                       # (table_index, bbox)
    for ti, t in enumerate(tables):
        for b in sorted({tuple(r2(v) for v in c) for c in t.cells}, key=lambda b: (b[1], b[0])):
            cells.append((ti, b))
    bys = {}
    if overfull:
        k0 = _assign(chars, [b for _, b in cells])
        box0 = {id(c): cells[k][1] for c, k in zip(chars, k0) if k >= 0}
        bys = block_ys(chars, lambda c: box0.get(id(c)), run_gap)
    cell_of = _assign_y(chars, [b for _, b in cells], bys)
    idx = {id(c): k for k, c in enumerate(chars)}

    clipped_ids, clipped, hidden_of, hidden_at, overlay_cells = set(), [], {}, {}, set()
    all_runs = runs(chars, run_gap, cell=lambda c: cell_of[idx[id(c)]], restart=restart)
    # Only on pages the year's config names (T7.overlaid: FY2022 Reso 09 p.38, FY2026 Reso 02
    # p.114). FY2024 Reso 06 p.26 has text drawn over text too, and its committed output
    # predates the rule.
    over = overlaid(all_runs, lambda c: cell_of[idx[id(c)]]) if overlay else set()
    for ri, run in enumerate(all_runs):
        k0 = cell_of[idx[id(run[0])]]
        if ri in over and k0 >= 0:
            # Overlaid text: every letter hidden, recorded on the cell it starts in.
            ink = [c for c in run if c["text"].strip()]
            clipped_ids.update(id(c) for c in run)
            hidden_of[k0] = (hidden_of.get(k0, "") + "".join(c["text"] for c in run)).strip()
            overlay_cells.add(k0)
            ti, b = cells[k0]
            clipped.append(dict(table=ti, owner_bbox=list(b), run_text="".join(c["text"] for c in run),
                                hidden_text="".join(c["text"] for c in run), overlaid=True,
                                bbox=bbox2((min(c["x0"] for c in ink), min(c["top"] for c in ink),
                                            max(c["x1"] for c in ink), max(c["bottom"] for c in ink)))))
            continue
        if k0 < 0:
            # A run that starts outside every drawn cell (an undrawn `*` cell) and runs past the
            # table's edge (FY2025 Reso 07 pp.29-30: staff notes in a column past the `*`
            # column; the page shows "01/", cut at the table's right rule, and the rest runs
            # off the page). Its letters outside the table are hidden; they stay with the run's
            # first letter so the made cell that reads it records them.
            tb = next((t.bbox for t in tables if _inside(run[0], t.bbox)), None)
            off = [c for c in run if tb and not _inside(c, tb)]
            if off and len(off) < len(run):
                clipped_ids.update(id(c) for c in off)
                hidden_at[id(run[0])] = "".join(c["text"] for c in off).strip()
                ink = [c for c in off if c["text"].strip()]
                clipped.append(dict(table=-1, owner_bbox=[], run_text="".join(c["text"] for c in run),
                                    hidden_text="".join(c["text"] for c in off),
                                    bbox=bbox2((min(c["x0"] for c in ink), min(c["top"] for c in ink),
                                                max(c["x1"] for c in ink),
                                                max(c["bottom"] for c in ink)))))
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
    t_of = _assign_y(visible, tboxes, bys)
    out_tables, orphans, loose = [], [], []
    for ti, t in enumerate(tables):
        tchars = [c for c, k in zip(visible, t_of) if k == ti]
        tcells = [b for tj, b in cells if tj == ti]
        gidx = [k for k, (tj, _) in enumerate(cells) if tj == ti]   # table cell -> page cell
        c_of = _assign_y(tchars, tcells, bys)
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
                if gidx[k] in overlay_cells:
                    flags.append("overlaid_text:" + "+".join(header[j]["label"] for j in under))
                if overfull and any(c["text"].strip() and overshoot(c, b) > OVERFULL_PT for c in cs):
                    flags.append("overfull_cell:" + "+".join(header[j]["label"] for j in under))
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
                cols[j] = _cell_rec(got, sb, "made", x_tolerance,
                                    " ".join(hidden_at[id(c)] for c in got if id(c) in hidden_at))
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
                rotation=int(page.rotation or 0), origin=[r2(page.bbox[0]), r2(page.bbox[1])],
                tables=out_tables,
                lines=text_lines(outside + loose, x_tolerance),
                loose_char_boxes=[bbox2((c["x0"], c["top"], c["x1"], c["bottom"]))
                                  for c in outside if c["text"].strip()],
                orphans=orphans, clipped=clipped, zero_width_chars=zero_width,
                ein_tokens=sum(1 for w in words_vis if EIN_TOKEN.match(w["text"])),
                ein_tokens_all_chars=sum(1 for w in words_all if EIN_TOKEN.match(w["text"])),
                nonws_chars=sum(1 for c in chars if c["text"].strip()),
                clipped_chars=sum(1 for c in chars if id(c) in clipped_ids and c["text"].strip()),
                overfull_chars=sum(1 for c, k in zip(chars, cell_of) if k >= 0 and c["text"].strip()
                                   and overshoot(c, cells[k][1]) > OVERFULL_PT))


def read_pdf(pdf_path, x_tolerance=3.0, run_gap=RUN_GAP, pages=None, overlay_pages=(),
             overfull_pages=(), restart_pages=()):
    import pdfplumber
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if pages and (i + 1) not in pages:
                continue
            out.append(read_page(page, i + 1, x_tolerance, run_gap, (i + 1) in overlay_pages,
                                 (i + 1) in overfull_pages, (i + 1) in restart_pages))
            page.flush_cache()
    return out


MONEY = re.compile(r"\(?\$[\d,]+(?:\.\d\d)?\)?")
