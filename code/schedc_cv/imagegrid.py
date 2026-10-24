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


def _roles(texts, roles=ROLE, squeeze=False):
    """{column: role} from header cell texts. `squeeze` matches with the spaces taken out
    (the pixel columns: FY2020 p.39 prints "Councilmember")."""
    out = {}
    for j, c in enumerate(texts):
        h = " ".join(c.split()).lower()
        if not h or len(h) > 60:
            continue
        for k, r in roles:
            if (k.replace(" ", "") in h.replace(" ", "") if squeeze else k in h) and \
                    r not in out.values():
                out[j] = r
                break
    return out


def image_rows(page_chars, lats, x_tolerance, carry=None, roles=ROLE):
    """Award rows read through the image lattices alone: [{y0, y1, fields{role: raw}}].

    `carry` (optional dict, kept by the caller from page to page) lets a table that runs over
    a page break without repeating its header (FY2026 pp.157, 195) be read with the last
    header the IMAGE side found: carry["header"] = {role: x_centre_pt}. The carried header
    applies only to lattices above the page's first own header, and only when the carried
    org, EIN and amount columns each land in a different column of the lattice and its first
    row holds an EIN in the EIN column. Off when carry is None (FY2027).

    `roles` is the header role table; a year's config may add words after the shared ones
    (FY2025 p.156: a name column headed "Institute")."""
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
            rl = _roles(raw, roles)
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


def hrule_ys(gray, dpi, x0_pt, x1_pt, kernel_px, cover=0.8):
    """y positions (pt) of horizontal rules drawn across a table's width, read from pixels
    alone: pixel rows of `grid.rule_masks`' horizontal mask covered over at least `cover` of
    [x0_pt, x1_pt], merged where adjacent. The image-side check for tables ruled with
    horizontal lines only (FY2024), where `grid.detect_grid` finds no lattice: it confirms
    each row band's top and bottom rule and that no rule runs through the band."""
    import numpy as np
    from ocr import grid as G
    s = dpi / 72.0
    horiz, _ = G.rule_masks(G.binarize(gray), kernel_px=kernel_px)
    a, b = max(0, int(x0_pt * s)), min(gray.shape[1], int(x1_pt * s))
    if b <= a:
        return []
    frac = (horiz[:, a:b] > 0).mean(axis=1)
    rows = np.nonzero(frac >= cover)[0]
    out, run = [], []
    for y in rows:
        if run and y > run[-1] + 1:
            out.append((run[0] + run[-1]) / 2 / s)
            run = []
        run.append(int(y))
    if run:
        out.append((run[0] + run[-1]) / 2 / s)
    return out


def check_bands(awards, ys, tol_pt):
    """Per award row of an h-rule table: 'bands_agree' when a pixel rule lies within tol_pt of
    its top and of its bottom and none lies inside it (2 pt in from each edge), else
    'bands_differ' with what is missing. Returns {award_id: (status, diffs)}."""
    out = {}
    for a in awards:
        top, bot = a["bbox_pt"][1], a["bbox_pt"][3]
        diffs = []
        if not any(abs(y - top) <= tol_pt for y in ys):
            diffs.append("no_rule_at_top")
        if not any(abs(y - bot) <= tol_pt for y in ys):
            diffs.append("no_rule_at_bottom")
        if any(top + 2 < y < bot - 2 for y in ys):
            diffs.append("rule_inside_row")
        out[a["award_id"]] = ("bands_agree" if not diffs else "bands_differ", diffs)
    return out


# --- pixel columns: a second reading of rows the image lattice cannot see (#193) -------------
#
# A table ruled across only (FY2024 p.65), or whose vertical "rules" are the edges of white
# boxes (p.178), or whose header is printed outside its grid (FY2021 p.63), gives the image
# lattice no cells, and its rows were read once. Here the image side finds their columns
# itself: the header's labels are runs of ink in the header band, and between each two labels
# the column edge is the widest run of pixel columns that holds no ink from the header down to
# the table's last rule. Each row is the band between its two pixel rules (`check_bands`);
# its characters are clipped to those cells by centre, as in `image_rows`. The vector side's
# only inputs are which table to look in (its box) and which band a row is in (its edges,
# matched to pixel rules); every edge used is a pixel one.

LABEL_GAP_PT = 4.5        # ink runs closer than this are one header label (a word space ~2.5 pt)
LOOSE_HEADER_PT = 14.0    # a header printed above the table's top rule (FY2021 p.63, FY2024 p.149)
HEADER_BAND_MAX_PT = 40.0
HEADER_RULE_TOL_PT = 3.0  # the rule under a header may sit off the first row's edge (FY2023 p.35)
RULE_FRINGE_PX = 2        # rules are taken out with their antialiased edges
# Header words read only here: a sub-award list prints "Amount" and "Service Type" as two
# labels over what the vector side reads as one cell (FY2018 p.106; `subaward_proxies`).
COLUMN_ROLES = [("service type", "service_type")]


def text_ink(gray, kernel_px):
    """The page's ink with its drawn rules taken out: a bool mask, True where there is type."""
    import cv2
    import numpy as np
    from ocr import grid as G
    ink = G.binarize(gray)
    horiz, vert = G.rule_masks(ink, kernel_px=kernel_px)
    k = 2 * RULE_FRINGE_PX + 1
    rules = cv2.dilate(np.maximum(horiz, vert), np.ones((k, k), np.uint8))
    return (ink > 0) & (rules == 0)


def _runs(flags):
    """[(start, end)) of the runs of True in a 1-d bool array."""
    out, start = [], None
    for i, v in enumerate(flags):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(flags)))
    return out


def header_labels(tink, dpi, x0_pt, x1_pt, y0_pt, y1_pt, gap_pt=LABEL_GAP_PT):
    """x extents (pt) of the labels printed in a header band: runs of inked pixel columns,
    joined across gaps narrower than gap_pt."""
    s = dpi / 72.0
    a, b = max(0, int(x0_pt * s)), min(tink.shape[1], int(x1_pt * s))
    t, u = max(0, int(y0_pt * s)), min(tink.shape[0], int(y1_pt * s))
    if b <= a or u <= t:
        return []
    out = []
    for r0, r1 in _runs(tink[t:u, a:b].any(axis=0)):
        if out and r0 - out[-1][1] < gap_pt * s:
            out[-1] = (out[-1][0], r1)
        else:
            out.append((r0, r1))
    return [((a + r0) / s, (a + r1) / s) for r0, r1 in out]


def column_edges(tink, dpi, labels, y0_pt, y1_pt):
    """Between each two consecutive labels [(x0, x1)], the centre (pt) of the widest run of
    pixel columns with no ink from y0 to y1; None when a pair has no such run."""
    s = dpi / 72.0
    t, u = max(0, int(y0_pt * s)), min(tink.shape[0], int(y1_pt * s))
    out = []
    for (_, l1), (r0, _) in zip(labels, labels[1:]):
        a, b = int(l1 * s) + 1, int(r0 * s)
        free = _runs(~tink[t:u, a:b].any(axis=0)) if b > a else []
        if not free:
            return None
        w0, w1 = max(free, key=lambda r: (r[1] - r[0], -r[0]))
        out.append(round((a + (w0 + w1) / 2) / s, 2))
    return out


def _text_in(chars, x0, x1, y0, y1, x_tolerance):
    return chars_to_text([c for c in chars if x0 <= (c["x0"] + c["x1"]) / 2 < x1 and
                          y0 <= (c["top"] + c["bottom"]) / 2 < y1], x_tolerance)


def pixel_header(tink, dpi, chars, x0_pt, x1_pt, y0_pt, y1_pt, x_tolerance, roles=ROLE):
    """The header printed in a band, read as labels: [(x0, x1, role or None)], or None unless
    it names an org, an EIN and an amount column."""
    labels = header_labels(tink, dpi, x0_pt, x1_pt, y0_pt, y1_pt)
    texts = [_text_in(chars, l0 - 0.5, l1 + 0.5, y0_pt, y1_pt, x_tolerance) for l0, l1 in labels]
    rl = _roles(texts, list(roles) + COLUMN_ROLES, squeeze=True)
    if not {"org", "ein", "amount"} <= set(rl.values()):
        return None
    return [(l0, l1, rl.get(j)) for j, (l0, l1) in enumerate(labels)]


def _rule_near(ys, y, tol):
    near = [v for v in ys if abs(v - y) <= tol]
    return min(near, key=lambda v: abs(v - y)) if near else None


def pixel_columns(tink, dpi, chars, ys, table_bbox, first_tops, x_tolerance, tol_pt, carry=None,
                  roles=ROLE):
    """The columns of one table the image lattice cannot see: {xs, roles, header} or None.

    The header is looked for in the band above the table's first row (between its top pixel
    rule and the rule above, when that band is under HEADER_BAND_MAX_PT), then in the
    LOOSE_HEADER_PT over that rule. `first_tops` are the tops of the table's first award row
    and of its first row whose band the pixel rules confirm; the first with a pixel rule near
    it is used (a first row drawn without its top rule, FY2024 p.152). Failing both bands,
    `carry` (the last pixel header, kept by the caller) is used when its EIN column holds an
    EIN in that first row. `ys` are the page's pixel rules across the table (`hrule_ys`)."""
    x0, _, x1, bot = table_bbox
    r_top = next((r for r in (_rule_near(ys, y, max(tol_pt, HEADER_RULE_TOL_PT))
                              for y in first_tops) if r is not None), None)
    r_bot = _rule_near(ys, bot, tol_pt) or bot
    if r_top is None:
        return None
    above = [v for v in ys if v < r_top - 1]
    bands = []
    if above and r_top - max(above) <= HEADER_BAND_MAX_PT:
        bands.append((max(above), r_top))
    bands.append((r_top - LOOSE_HEADER_PT, r_top))
    for b0, b1 in bands:
        hdr = pixel_header(tink, dpi, chars, x0, x1, b0 + 0.5, b1 - 0.5, x_tolerance, roles)
        if hdr is None:
            continue
        edges = column_edges(tink, dpi, [(l0, l1) for l0, l1, _ in hdr], b0, r_bot)
        if edges is None:
            return None
        if carry is not None:
            carry["labels"] = hdr
        return dict(xs=[x0] + edges + [x1], roles=[r for _, _, r in hdr], header="own")
    if carry is None or not carry.get("labels"):
        return None
    hdr = carry["labels"]
    edges = column_edges(tink, dpi, [(l0, l1) for l0, l1, _ in hdr], r_top, r_bot)
    if edges is None:
        return None
    xs = [x0] + edges + [x1]
    ci = [r for _, _, r in hdr].index("ein")
    r_next = min((v for v in ys if v > r_top + 1), default=None)
    if r_next is None or not re.fullmatch(r"\d{2}-\d{7}|\d{9}", _text_in(
            chars, xs[ci], xs[ci + 1], r_top, r_next, x_tolerance).strip()):
        return None
    return dict(xs=xs, roles=[r for _, _, r in hdr], header="carried")


def _drop_star(text):
    """The text without one "*" printed as a word of its own."""
    return re.sub(r"(^|\s)\*(?=\s|$)", "", text, count=1).strip()


def check_columns(award, cols, ys, chars, x_tolerance, tol_pt):
    """Read one award row through pixel columns: (status, diffs, image fields). The row's band
    is between the pixel rules at its top and bottom edge (it passed `check_bands`).

    The row is compared as the vector side read it into its fields (`_columns_raw` where a
    row gives one, else `_raw`). A "*" the vector side read from a cell of its own under a
    header with no "*" column (row flag `star_in_cell`, FY2018 p.127; a review item already)
    has no pixel column either and lands in a neighbour's; it is not counted as a difference."""
    y0 = _rule_near(ys, award["bbox_pt"][1], tol_pt)
    y1 = _rule_near(ys, award["bbox_pt"][3], tol_pt)
    xs = cols["xs"]
    fields = {r: _text_in(chars, xs[i], xs[i + 1], y0, y1, x_tolerance)
              for i, r in enumerate(cols["roles"]) if r}
    vec = award.get("_columns_raw") or award["_raw"]
    star = "star_in_cell" in award.get("row_flags", [])
    diffs = []
    for f in FIELDS + (("service_type",) if "service_type" in vec else ()):
        if f in vec or f in fields:
            v, i = vec.get(f), fields.get(f)
            if v != i and not (star and i is not None and v == _drop_star(i)):
                diffs.append(f)
    return ("columns_agree" if not diffs else "columns_differ"), diffs, fields
