"""
Stage 4 for transparency charts -- rows rebuilt from the image lattice alone (H8).

The lattice comes from the rendered pixels through Christian Moscardi's `grid.py`, one table
region at a time (code/schedc_cv/imagegrid.py `lattices`). Nothing from the vector side is
used: not its cells, not its header columns, not its clipping decisions.

What is particular to these charts:
- `grid.py` keeps only separators that run most of the table's height, so a rule drawn in
  the header row alone (Source | Member on purpose-of-funds charts; the `*` column on some
  pages) is not in the lattice. When a header cell's text is not one known label, this module
  looks for the missing rule *in the header row's own pixels*: a pixel column dark over at
  least 90% of the header band, inside that cell. The cell is split there.
- Text is read by runs, with the image lattice deciding which cell a run starts in and which
  of its characters are hidden (clipped), the same reading rule as the vector side but on
  the other lattice.
"""
from functools import partial

import numpy as np

from schedc.vector import ZERO_WIDTH, chars_to_text
from schedc_cv import imagegrid
from transreso import reader, structure

HEADER_RULE_FRAC = 0.9


def _roles(labels):
    roles = {j: structure.LABELS.get(lb) for j, lb in enumerate(labels)}
    if labels and labels[-1] == "" and roles.get(len(labels) - 2) == "ua":
        roles[len(labels) - 1] = "prequal"
    return roles


def _header_rules(gray, dpi, x0, x1, y0, y1):
    """x positions (pt) of vertical rules drawn inside one header cell, from pixels."""
    s = dpi / 72.0
    X0, X1, Y0, Y1 = int(x0 * s) + 4, int(x1 * s) - 4, int(y0 * s) + 3, int(y1 * s) - 3
    if X1 <= X0 or Y1 <= Y0:
        return []
    band = gray[Y0:Y1, X0:X1] < 128
    frac = band.mean(axis=0)
    xs, run = [], []
    for i, v in enumerate(frac):
        if v >= HEADER_RULE_FRAC:
            run.append(i)
        elif run:
            xs.append((X0 + (run[0] + run[-1]) / 2) / s)
            run = []
    if run:
        xs.append((X0 + (run[0] + run[-1]) / 2) / s)
    return [round(x, 2) for x in xs]


def _rule_drawn(gray, dpi, x, y0, y1, frac=HEADER_RULE_FRAC):
    """True if a vertical rule at x (pt) is drawn down the band y0..y1 (pt), from pixels: some
    pixel column within 2 px of x is dark over `frac` of the band (ends trimmed 3 px)."""
    s = dpi / 72.0
    X, Y0, Y1 = int(round(x * s)), int(y0 * s) + 3, int(y1 * s) - 3
    if Y1 <= Y0:
        return True
    band = gray[Y0:Y1, max(0, X - 2):X + 3] < 128
    return bool(band.size) and float(band.mean(axis=0).max()) >= frac


def image_rows(page_chars, gray, dpi, kernel_px, pad, x_tolerance, run_gap, overlay=False,
               overfull=False, blank_labels=None, restart=False):
    """[{y0, y1, fields{role: raw}, hidden{role: text}}] for every data row the image lattice
    finds under a recognised header, plus the lattices and notes. On `overfull` pages (T7.overfull)
    a text block of two or more lines goes to the image row holding its middle, as in the
    reader (transreso.reader.block_ys); the rows are the image lattice's own. `blank_labels`: on a
    page whose header prints no labels (T4.blank_header), the labels the reader borrowed from
    the page before, used when the lattice has the same number of columns."""
    lats = imagegrid.lattices(gray, dpi, kernel_px, pad)
    chars = [c for c in page_chars if c["text"] not in ZERO_WIDTH]
    notes = []
    rows = []
    for k, L in enumerate(lats):
        if not L["xs_pt"]:
            continue
        xs, ys = list(L["xs_pt"]), L["ys_pt"]
        # Header row = the first lattice row; split cells whose text is not one label.
        def cell_of(c, xs=xs, ys=ys):
            cx, cy = (c["x0"] + c["x1"]) / 2, (c["top"] + c["bottom"]) / 2
            ri, ci = imagegrid._band(ys, cy), imagegrid._band(xs, cx)
            return None if ri is None or ci is None else (ri, ci)
        hdr_chars = {}
        for c in chars:
            rc = cell_of(c)
            if rc and rc[0] == 0:
                hdr_chars.setdefault(rc[1], []).append(c)
        extra = []
        for ci in range(len(xs) - 1):
            lab = " ".join(chars_to_text(hdr_chars.get(ci, []), x_tolerance).split())
            if lab not in structure.LABELS and lab != "":
                for x in _header_rules(gray, dpi, xs[ci], xs[ci + 1], ys[0], ys[1]):
                    extra.append(x)
                    notes.append(f"region {k}: header rule at {x} pt found in header pixels")
        # The same, right of the lattice's last rule: a last column whose right rule is drawn
        # in the header and a few rows only (the `*` column on FY2025 Reso 07 p.30, which
        # holds "01/") is not in the lattice at all. Looked for only where a data row has a
        # letter on the page right of the lattice; an empty column there has nothing to read
        # (24 FY2026 pages leave the empty `*` column outside the lattice).
        page_w = gray.shape[1] * 72.0 / dpi
        if any(xs[-1] < (c["x0"] + c["x1"]) / 2 < page_w and ys[1] <= (c["top"] + c["bottom"]) / 2 < ys[-1]
               and c["text"].strip() for c in chars):
            for x in _header_rules(gray, dpi, xs[-1] + 1, page_w, ys[0], ys[1]):
                extra.append(x)
                notes.append(f"region {k}: header rule at {x} pt found in header pixels")
        xs = sorted(xs + extra)

        def cell_of2(c, xs=xs, ys=ys):
            cx, cy = (c["x0"] + c["x1"]) / 2, (c["top"] + c["bottom"]) / 2
            ri, ci = imagegrid._band(ys, cy), imagegrid._band(xs, cx)
            return None if ri is None or ci is None else (ri, ci)
        # Data cells: the lattice's columns (plus rules found in the header's pixels), but a
        # column rule counts in a row only where the row's own pixels show it (`grid.py` keeps
        # a separator drawn in most rows though some rows leave it out, Reso 02 p.125, and
        # drops one drawn in only a few, Reso 02 p.110). Cells either side of a missing rule are one cell;
        # the header's labels then split its runs, each going where it starts.
        lat_xs = xs      # the lattice's rules plus any found in the header's pixels
        drawn = {(ri, si): _rule_drawn(gray, dpi, lat_xs[si], ys[ri], ys[ri + 1])
                 for ri in range(len(ys) - 1) for si in range(1, len(lat_xs) - 1)}

        def data_cell(c, xs=lat_xs, ys=ys, drawn=drawn, bys={}):
            cx, cy = (c["x0"] + c["x1"]) / 2, bys.get(id(c), (c["top"] + c["bottom"]) / 2)
            ri, ci = imagegrid._band(ys, cy), imagegrid._band(xs, cx)
            if ri is None or ci is None:
                return None
            while ci > 0 and not drawn[(ri, ci)]:
                ci -= 1
            return (ri, ci)

        if overfull:
            def box_of(c, xs=lat_xs, ys=ys):
                rc = data_cell(c)
                return None if rc is None else (xs[rc[1]], ys[rc[0]], xs[rc[1] + 1], ys[rc[0] + 1])
            data_cell = partial(data_cell, bys=reader.block_ys(chars, box_of, run_gap))

        cells, hidden = {}, {}
        all_runs = reader.runs(chars, run_gap, cell=lambda c: data_cell(c), restart=restart)
        over = reader.overlaid(all_runs, data_cell) if overlay else set()
        for k_run, run in enumerate(all_runs):
            own = data_cell(run[0])
            if own is None:
                continue
            ri = own[0]
            if ri == 0:
                col = cell_of2(run[0])[1]
            else:
                col = imagegrid._band(xs, (run[0]["x0"] + run[0]["x1"]) / 2)
            for c in run:
                if k_run not in over and data_cell(c) == own:
                    cells.setdefault((ri, col), []).append(c)
                else:
                    hidden.setdefault((ri, col), []).append(c)
        nc = len(xs) - 1
        labels = [" ".join(chars_to_text(cells.get((0, ci), []), x_tolerance).split())
                  for ci in range(nc)]
        if blank_labels and not any(labels) and len(blank_labels) == len(labels):
            labels = list(blank_labels)
        roles = _roles(labels)
        rs_ = set(roles.values())
        listing = {"org", "ein"} <= rs_ and not {"agency", "amount", "purpose"} & rs_   # FY2022
        if not structure.REQUIRED <= rs_ and not listing:
            notes.append(f"region {k}: no recognised header {labels}")
            continue
        for ri in range(1, len(ys) - 1):
            f = {roles[ci]: chars_to_text(cells.get((ri, ci), []), x_tolerance)
                 for ci in range(nc) if roles.get(ci)}
            h = {roles[ci]: "".join(c["text"] for c in hidden[(ri, ci)]).strip()
                 for ci in range(nc) if roles.get(ci) and
                 "".join(c["text"] for c in hidden.get((ri, ci), [])).strip()}
            rows.append(dict(region=k, row=ri, y0=ys[ri], y1=ys[ri + 1], fields=f, hidden=h))
    return rows, lats, notes


FIELDS = ("source", "member", "org", "ein", "agency", "amount", "agy", "ua", "prequal", "purpose",
          "conduit", "conduit_ein")


def compare_page(recs, img_rows, row_tol_pt):
    """Per vector row: agree / differs / no_image_row / multi_image_row, with the fields that
    differ; and the image rows no vector row claimed."""
    out, used = [], set()
    for a in recs:
        y0, y1 = a["bbox_pt"][1], a["bbox_pt"][3]
        yc = (y0 + y1) / 2
        cands = [i for i, r in enumerate(img_rows) if r["y0"] <= yc < r["y1"]]
        rec = dict(row_id=a["row_id"], diffs=[], image={})
        if len(cands) != 1:
            rec["status"] = "no_image_row" if not cands else "multi_image_row"
            out.append(rec)
            continue
        r = img_rows[cands[0]]
        used.add(cands[0])
        dy = max(abs(r["y0"] - y0), abs(r["y1"] - y1))
        if dy > row_tol_pt:
            rec["diffs"].append(f"row_band:{dy:.2f}pt")
        for f in FIELDS:
            if f in a["_raw"] or f in r["fields"]:
                if a["_raw"].get(f, "") != r["fields"].get(f, ""):
                    rec["diffs"].append(f)
        if a.get("_hidden", {}) != r["hidden"]:
            rec["diffs"].append("hidden_text")
        rec["image"] = r["fields"]
        rec["status"] = "agree" if not rec["diffs"] else "differs"
        out.append(rec)
    extra = [r for i, r in enumerate(img_rows) if i not in used]
    return out, extra
