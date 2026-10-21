"""
Stage 4 -- the image lattice, an independent check on the vector lattice (PLAN §3, H8).

The cell grid is re-derived from the rendered pixels with Christian Moscardi's `grid.py`
(code/ocr/grid.py, PR #43; the absolute `kernel_px` option from PR #99), called once per table
REGION, not once per page: portrait pages stack several tables, and whole-page mode found no
lattice on 91 of 107 FY2027 multi-table pages. Regions are connected components of the page's
rule mask. The region finder, the role table and the row comparison are salvaged from the
2026-10-19 FY2027 prototype (`image_grid.py`, `image_rows.py`; BetaNYC working notes), which
found 9,952 of 9,979 rows agreeing on every field.

Independence: the image side uses no vector geometry. It finds its own regions, its own row
and column separators and its own header row (by role words), and builds its own award rows.
It shares only the PDF's text layer with the vector side (characters are clipped to image
cells by centre), so it cannot catch a text-layer error (p.486); ink coverage and a person do.

Comparison per vector award row: find the image row whose band holds the row's centre; the
row agrees when the band edges are within `row_tol_pt` and every field's text is identical.
"""
import bisect
import re

from schedc.vector import chars_to_text, ZERO_WIDTH

SEG_KERNEL_PX = 60      # ~14 pt at 300 dpi: longer than any glyph stroke in FY2027
SEG_DILATE_PX = 5       # closes the 1-2 px antialias gaps where rules meet
MIN_REGION_W, MIN_REGION_H = 150, 30

# Header role words (prototype `image_rows.ROLE`), first match wins, one column per role.
ROLE = [("council member", "member"), ("borough", "delegation"), ("sponsor", "sponsor"),
        ("delegation", "delegation"), ("legal name", "org"), ("organization", "org"),
        ("tax id", "ein"), ("ein", "ein"), ("amount", "amount"), ("agency", "agency"),
        ("purpose", "purpose")]


def regions(gray, kernel_px=SEG_KERNEL_PX):
    """Table regions on a page: bounding boxes (px) of connected components of the rule mask."""
    import cv2
    import numpy as np
    from ocr import grid as G
    ink = G.binarize(gray)
    horiz, vert = G.rule_masks(ink, kernel_px=kernel_px)
    m = cv2.dilate(np.maximum(horiz, vert), np.ones((SEG_DILATE_PX, SEG_DILATE_PX), np.uint8))
    n, _, st, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8), connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h = (int(v) for v in st[i, :4])
        if w >= MIN_REGION_W and h >= MIN_REGION_H:
            out.append((x, y, x + w, y + h))
    return sorted(out, key=lambda b: (b[1], b[0]))


def lattices(gray, dpi, kernel_px, pad):
    """[{bbox_pt, xs_pt, ys_pt, notes}] for every region with a lattice; regions without one
    are returned with xs_pt=None."""
    from ocr import grid as G
    H, W = gray.shape
    s = 72.0 / dpi
    out = []
    for x0, y0, x1, y1 in regions(gray, kernel_px):
        cx0, cy0, cx1, cy1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
        g = G.detect_grid(gray[cy0:cy1, cx0:cx1], kernel_px=kernel_px)
        out.append(dict(bbox_pt=[round(v * s, 2) for v in (x0, y0, x1, y1)],
                        xs_pt=[round((cx0 + v) * s, 2) for v in g.xs] if g else None,
                        ys_pt=[round((cy0 + v) * s, 2) for v in g.ys] if g else None,
                        notes=g.notes if g else ["no lattice"]))
    return out


def _band(seps, v):
    i = bisect.bisect_right(seps, v) - 1
    return i if 0 <= i < len(seps) - 1 else None


def _roles(texts):
    out = {}
    for j, c in enumerate(texts):
        h = " ".join(c.split()).lower()
        if not h or len(h) > 60:
            continue
        for k, r in ROLE:
            if k in h and r not in out.values():
                out[j] = r
                break
    return out


def image_rows(page_chars, lats, x_tolerance, carry=None):
    """Award rows read through the image lattices alone: [{y0, y1, fields{role: raw}}].

    `carry` (optional dict, kept by the caller from page to page) lets a table that runs over
    a page break without repeating its header (FY2026 pp.157, 195) be read with the last
    header the IMAGE side found: carry["header"] = {role: x_centre_pt}. The carried header
    applies only to lattices above the page's first own header, and only when the carried
    org, EIN and amount columns each land in a different column of the lattice and its first
    row holds an EIN in the EIN column. Off when carry is None (FY2027)."""
    chars = [c for c in page_chars if c["text"] not in ZERO_WIDTH]
    cells = {}
    for ch in chars:
        cx, cy = (ch["x0"] + ch["x1"]) / 2, (ch["top"] + ch["bottom"]) / 2
        for k, L in enumerate(lats):
            if not L["xs_pt"]:
                continue
            ri, ci = _band(L["ys_pt"], cy), _band(L["xs_pt"], cx)
            if ri is not None and ci is not None:
                cells.setdefault((k, ri, ci), []).append(ch)
                break
    rows = []
    seen_header = False
    for k, L in enumerate(lats):
        if not L["xs_pt"]:
            continue
        nr, nc = len(L["ys_pt"]) - 1, len(L["xs_pt"]) - 1
        hdr = None
        if carry is not None and carry.get("header") and not seen_header:
            hdr = {}
            for role, x in carry["header"].items():
                ci = _band(L["xs_pt"], x)
                if ci is not None and ci not in hdr:
                    hdr[ci] = role
            if not {"org", "ein", "amount"} <= set(hdr.values()):
                hdr = None
            else:
                # ... and only when the lattice's first row holds an EIN in that column.
                ein_ci = next(ci for ci, role in hdr.items() if role == "ein")
                first = chars_to_text(cells.get((k, 0, ein_ci), []), x_tolerance).strip()
                if not re.fullmatch(r"\d{2}-\d{7}|\d{9}", first):
                    hdr = None
        for ri in range(nr):
            raw = [chars_to_text(cells.get((k, ri, ci), []), x_tolerance) for ci in range(nc)]
            rl = _roles(raw)
            if {"org", "ein", "amount"} <= set(rl.values()):
                hdr = rl
                seen_header = True
                if carry is not None:
                    carry["header"] = {role: (L["xs_pt"][ci] + L["xs_pt"][ci + 1]) / 2
                                       for ci, role in rl.items()}
                continue
            if hdr is None:
                continue
            rows.append(dict(region=k, row=ri, y0=L["ys_pt"][ri], y1=L["ys_pt"][ri + 1],
                             fields={role: raw[ci] for ci, role in hdr.items()}))
    return rows


FIELDS = ("member", "sponsor", "delegation", "org", "ein", "amount", "agency", "purpose")


def compare_page(awards, img_rows, row_tol_pt):
    """Compare the page's vector award rows with its image rows. Returns one result per vector
    row: {award_id, status, diffs, image{field: raw}}; status is agree / differs / no_image_row
    / multi_image_row. Also returns image rows no vector row claimed (rows the vector side may
    have dropped)."""
    out, used = [], set()
    for a in awards:
        y0, y1 = a["bbox_pt"][1], a["bbox_pt"][3]
        yc = (y0 + y1) / 2
        cands = [i for i, r in enumerate(img_rows) if r["y0"] <= yc < r["y1"]]
        rec = dict(award_id=a["award_id"], diffs=[], image={})
        if len(cands) != 1:
            rec["status"] = "no_image_row" if not cands else "multi_image_row"
            out.append(rec)
            continue
        r = img_rows[cands[0]]
        used.add(cands[0])
        dy = max(abs(r["y0"] - y0), abs(r["y1"] - y1))
        if dy > row_tol_pt:
            rec["diffs"].append(f"row_band:{dy:.2f}pt")
        vec = a["_raw"]
        for f in FIELDS:
            if f in vec or f in r["fields"]:
                if vec.get(f) != r["fields"].get(f):
                    rec["diffs"].append(f)
        rec["image"] = r["fields"]
        rec["status"] = "agree" if not rec["diffs"] else "differs"
        out.append(rec)
    extra = [r for i, r in enumerate(img_rows) if i not in used]
    return out, extra


def overlay(gray, dpi, lats, vector_tables, marks, path):
    """Debug overlay: vector table lattice in blue, image lattice in green, marks in red."""
    import cv2
    img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    s = dpi / 72.0
    P = lambda v: int(round(v * s))
    for t in vector_tables:
        for r in t["rows"]:
            for c in r["cells"]:
                b = c["bbox"]
                cv2.rectangle(img, (P(b[0]), P(b[1])), (P(b[2]), P(b[3])), (255, 0, 0), 1)
    for L in lats:
        if not L["xs_pt"]:
            continue
        for x in L["xs_pt"]:
            cv2.line(img, (P(x), P(L["ys_pt"][0])), (P(x), P(L["ys_pt"][-1])), (0, 160, 0), 2)
        for y in L["ys_pt"]:
            cv2.line(img, (P(L["xs_pt"][0]), P(y)), (P(L["xs_pt"][-1]), P(y)), (0, 160, 0), 2)
    for b in marks:
        cv2.rectangle(img, (P(b[0]) - 6, P(b[1]) - 6), (P(b[2]) + 6, P(b[3]) + 6), (0, 0, 255), 4)
    cv2.imwrite(path, img)
