"""
Stage 7 -- structure (PLAN §3): categories, summary tables, initiative boxes, designation
statements, award rows and appendices, from the vector pages.

Everything is ordered by (page, y) geometry, never by content-stream order (FY2027 p.205
draws a box after rows that sit below it). An award row belongs to the last initiative box
above it; a landscape page inherits from the page before it. Year-specific facts (header
labels, statement wording, section titles) come from the year's config; an unknown header or
statement is a flag, never a guess.

Fields keep the printed text (`*_raw`, `amount_printed`) next to the clean value. The clean
value differs from raw only by the rules in `clean_text`.
"""
import re
from decimal import Decimal

AMOUNT_RE = re.compile(r"^\$\s?(\d{1,3}(?:,\d{3})*)$")
EIN_RE = re.compile(r"^(\d{2}-\d{7}|\d{9})$")
MONEY_ANY = re.compile(r"\$\s?([\d,]+)")
CID = re.compile(r"\(cid:\d+\)")
# An amount cut inside its last thousands group ("$200,00"): the rest is in the next cell.
SPLIT_TAIL = re.compile(r"^\$\s?\d{1,3}(?:,\d{3})*,\d{1,2}$")
EIN_IN_TEXT = re.compile(r"(^|[\s|])(\d{2}-\d{7}|\d{9})($|[\s|])")
# An EIN as printed, also with too few or too many digits (FY2021 p.90 "47-984801"): enough to
# know a row is an award row (structure `header_band_words`); the EIN itself is read by EIN_RE.
EIN_LIKE = re.compile(r"^\d{2}-\d{6,8}$")
# An award header's column words, as printed (structure `header_band_words`).
HEADER_WORD = re.compile(r"\b(EIN|Tax ID|Amount)\b")
# An award row's text fields, each kept raw (`<field>_raw`) and clean. `program_or_subheading`
# holds a "Program" or "School" column (header label `program_or_subheading`; FY2018-FY2022 Art
# as a Catalyst for Change) or a sub-heading printed inside the table (`award_subheadings`), so
# that `purpose` holds only a printed purpose (decided in #209). `fiscal_conduit` is FY2018's
# "Fiscal Conduit" column.
TEXT_FIELDS = ("member", "sponsor", "delegation", "org", "agency", "purpose",
               "program_or_subheading", "fiscal_conduit")


def clean_text(raw):
    """Clean value from raw cell text. The only rules (PLAN §5.2):
    1. a line break after a hyphen that has no space before it joins with no space, and keeps
       the hyphen (`Home-⏎Delivered` -> `Home-Delivered`; flagged `wrap_hyphen`, because it
       could also be a split word);
    2. any other line break joins with one space;
    3. runs of whitespace collapse to one space; ends are trimmed;
    4. an unmapped glyph, which pdfplumber writes as "(cid:N)", is dropped (FY2026 p.344:
       "District 36.(cid:9)", drawn on the page as an empty box; flagged `cid_glyph`).
    Returns (clean, rules_applied)."""
    rules = []
    if CID.search(raw):
        raw = CID.sub("", raw)
        rules.append("cid_glyph")
    lines = raw.split("\n")
    out = lines[0] if lines else ""
    for ln in lines[1:]:
        if re.search(r"[^\s]-$", out):
            out += ln
            rules.append("wrap_hyphen")
        else:
            out += " " + ln
            rules.append("line_join")
    collapsed = re.sub(r"\s+", " ", out).strip()
    if collapsed != out:
        rules.append("ws_collapse")
    return collapsed, sorted(set(rules))


def strip_star(text):
    """A row's "*" mark printed at the end of a cell, dropped (clean rule `star_mark`)."""
    return re.sub(r"(^|\s)\*$", "", text).strip()


def parse_amount(s):
    m = AMOUNT_RE.match(s.strip())
    return int(m.group(1).replace(",", "")) if m else None


def money_in(text):
    m = MONEY_ANY.search(text)
    return int(m.group(1).replace(",", "")) if m else None


def _cell_at(rows, ri, x):
    """The cell covering x in row ri, or a taller cell from an earlier row that spans down into
    it (a vertically merged cell). Returns (cell, spanned_from_row_index_or_None)."""
    row = rows[ri]
    for c in row["cells"]:
        if c["bbox"][0] <= x < c["bbox"][2]:
            return c, None
    mid = (row["top"] + row["bottom"]) / 2
    for rj in range(ri - 1, -1, -1):
        for c in rows[rj]["cells"]:
            b = c["bbox"]
            if b[0] <= x < b[2] and b[1] <= mid < b[3]:
                return c, rows[rj]["row_index"]
    return None, None


def header_map(row, labels):
    """Header row -> [(field, x_centre)] from cells whose text matches a configured label.
    Returns (columns, unknown_labels)."""
    cols, unknown = [], []
    for c in row["cells"]:
        t = " ".join(c["text_raw"].split())
        if not t:
            continue
        field = None
        for pat, f in labels:
            if re.fullmatch(pat, t):
                field = f
                break
        if field is None:
            unknown.append(t)
        else:
            cols.append((field, (c["bbox"][0] + c["bbox"][2]) / 2))
    return cols, unknown


def _join_header_bands(r0, r1):
    """Two header row bands -> one synthetic header row, each band-1 text appended (after a
    space) to the band-0 cell over its centre. None when band 1 holds an EIN or an amount, or
    text under no band-0 cell."""
    t1 = _row_text(r1)
    if not t1 or EIN_IN_TEXT.search(t1) or MONEY_ANY.search(t1):
        return None
    cells = [dict(c) for c in r0["cells"]]
    for c in r1["cells"]:
        if not c["text_raw"].strip():
            continue
        cx = (c["bbox"][0] + c["bbox"][2]) / 2
        hit = [h for h in cells if h["bbox"][0] <= cx < h["bbox"][2]]
        if not hit:
            return None
        hit[0]["text_raw"] = (hit[0]["text_raw"] + " " + c["text_raw"]).strip()
    return dict(cells=cells)


def table_kind(t, cfg):
    first = " | ".join(" ".join(c["text_raw"].split()) for c in t["rows"][0]["cells"]
                       if c["text_raw"].strip())
    if re.search(cfg["structure"]["award_header_re"], first):
        return "award"
    titles = cfg["structure"].get("summary_titles", [cfg["structure"]["summary_title"]])
    if any(first.startswith(x) for x in titles):
        return "summary"
    if re.search(r"\$[\d,]+$", first) and len(t["rows"]) >= 1 and \
            any(" ".join(c["text_raw"].split()) for c in t["rows"][0]["cells"][:3]) and \
            not (cfg["structure"].get("short_ein_rows") and
                 re.search(r"(^|[\s|])\d{2}-(\d{6}|\d{8})($|[\s|])", first)):
        # `short_ein_rows` (FY2018 p.107): a row printing an EIN of the wrong length
        # ("Urban Health Plan, Inc. | 15-24042810 | $88,855") is an award row, not a box.
        return "box"
    if cfg["structure"].get("box_amount_dollar_space") and re.search(r"\$ [\d,]+$", first) and \
            not EIN_IN_TEXT.search(first):
        # The box amount printed with a space after "$" (FY2023 p.34 "AAPI | $ 5,000,000").
        return "box"
    if cfg["structure"].get("box_amount_without_dollar") and \
            re.search(r"\| \d{1,3}(?:,\d{3})+$", first) and not EIN_IN_TEXT.search(first) and \
            first.count(" | ") == 1:
        # The box amount printed without its "$" (FY2023 p.92 "Trauma Recovery Centers |
        # 2,400,000", in the black bar): a title cell and a bare amount, nothing EIN-like.
        return "box"
    if cfg["structure"].get("box_amount_cells") and not EIN_IN_TEXT.search(first):
        # The box amount cut into cells (FY2025 p.157 "... | $ | 5 | 00,000").
        texts = [c["text_raw"].strip() for c in t["rows"][0]["cells"] if c["text_raw"].strip()]
        for k in range(2, min(4, len(texts) - 1) + 1):
            if parse_amount("".join(texts[-k:])) is not None:
                return "box"
    if cfg["structure"].get("box_amount_on_second_row") and len(t["rows"]) >= 2 and \
            first and "$" not in first and not EIN_IN_TEXT.search(first):
        # A box whose title wraps to a second line, the amount printed on that line (FY2026
        # p.157 "Healthy Beginnings (Formerly ... Maternal and" / "Child Health Services) |
        # $4,393,244"). The title cell of both rows starts at the same x.
        r0, r1 = t["rows"][0]["cells"], t["rows"][1]["cells"]
        second = " | ".join(" ".join(c["text_raw"].split()) for c in r1 if c["text_raw"].strip())
        if re.search(r"\$[\d,]+$", second) and not EIN_IN_TEXT.search(second) and \
                r0[0]["bbox"][0] == r1[0]["bbox"][0] and len(r0) == len(r1):
            return "box2"
    return "other"


def statement_amount(v):
    """A dollar figure as a statement prints it: "1,120,000", or in millions, "4.1 million"
    (FY2025 p.36: "has designated $4.1 million"; the rows under it add to $4,100,000). A
    rounded figure is taken at its face value, so a statement that rounds fails H12 and is a
    review row, never a silent tolerance."""
    if not v:
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?) million", v)
    if m:
        return int(Decimal(m.group(1)) * 1000000)
    return int(v.replace(",", ""))


def statement_kind(text, cfg):
    """Designation statement -> (kind, reserve, designated). Kinds come from config regexes;
    several groups named `designated...` add up (FY2024 p.147 names two amounts designated), and
    so do groups named `reserve...` (FY2022 p.65: two amounts allocated straight to agencies,
    the rest to the providers listed)."""
    t = " ".join(text.split())
    for st in cfg["statements"]:
        m = re.search(st["re"], t)
        if m:
            g = m.groupdict()
            parts = [statement_amount(v) for k_, v in sorted(g.items())
                     if k_.startswith("designated") and v]
            held = [statement_amount(v) for k_, v in sorted(g.items())
                    if k_.startswith("reserve") and v]
            return st["kind"], (sum(held) if held else None), \
                (sum(parts) if parts else None)
    return "unknown", None, None


def _row_text(r):
    return " | ".join(" ".join(c["text_raw"].split()) for c in r["cells"] if c["text_raw"].strip())


SLIVER_PT = 8.0


def _band_header(row, lines, x0, x1, prefix):
    """A header row with the loose words printed in its own row band added, each to the cell
    under its centre (FY2021 p.45: "EIN" in the cell, "Legal Name of Organization" and
    "Amount" in the same band but outside every cell). Loose lines that are statements, or
    lie outside the table's width, are left out. None when no word was added."""
    cells = [dict(c) for c in row["cells"]]
    added = False
    used = []
    for ln in lines:
        if ln.get("from_table") or ln["text"].startswith(prefix) or \
                not row["top"] <= (ln["top"] + ln["bottom"]) / 2 < row["bottom"]:
            continue
        words = [w for w in ln.get("words", []) if x0 <= (w[0] + w[1]) / 2 < x1]
        hits = [[c for c in cells if c["bbox"][0] <= (w[0] + w[1]) / 2 < c["bbox"][2]]
                for w in words]
        if words and not any(hits):
            # A loose line right of the row's last cell (p.35 "Amount", the row's cells
            # ending at x 467 inside a table 538 wide): its own cell, the line's width.
            cells.append(dict(bbox=[words[0][0], row["top"], words[-1][1], row["bottom"]],
                              text_raw=" ".join(w[2] for w in words), nchars=0,
                              char_boxes=[]))
            added = True
            used += [[w[0], row["top"], w[1], row["bottom"]] for w in words]
            continue
        for w, hit in zip(words, hits):
            if hit:
                hit[0]["text_raw"] = (hit[0]["text_raw"] + " " + w[2]).strip()
                added = True
                used.append([w[0], row["top"], w[1], row["bottom"]])
    cells.sort(key=lambda c: c["bbox"][0])
    return dict(row, cells=cells, band_words=used) if added else None


def _cell_words(c):
    """A cell's words with their x extents, from its text and its (non-space) char boxes."""
    out, cur = [], []
    boxes = iter(c["char_boxes"])
    for ch in c["text_raw"] + " ":
        if ch.isspace():
            if cur:
                out.append((min(b[0] for _, b in cur), max(b[2] for _, b in cur),
                            "".join(x for x, _ in cur)))
                cur = []
            continue
        b = next(boxes, None)
        if b is None:
            return []
        cur.append((ch, b))
    return out


def _row_texts_with_slivers(t):
    """Row texts of a table, with letters that fell into a narrow sliver cell put back in
    front of their row. FY2026 p.162 draws a 5 pt cell down the left edge of a box that
    spans six row bands; each label's first letter lands in it ("D" | "esignation Method:").
    A sliver's letters are matched to row bands by their own vertical centre. Used only to
    read box and statement rows; award cells are never rebuilt this way."""
    texts = [_row_text(r) for r in t["rows"]]
    for r0 in t["rows"]:
        for c in r0["cells"]:
            if c["bbox"][2] - c["bbox"][0] >= SLIVER_PT or not c["text_raw"].strip():
                continue
            letters = [ch for ch in c["text_raw"] if not ch.isspace()]
            boxes = sorted(c["char_boxes"], key=lambda b: (b[1], b[0]))
            if len(letters) != len(boxes):
                continue
            for ch, b in zip(letters, boxes):
                cy = (b[1] + b[3]) / 2
                for i, r in enumerate(t["rows"]):
                    if r["top"] <= cy < r["bottom"]:
                        rest = [x for x in r["cells"] if x is not c and x["text_raw"].strip()]
                        if rest and abs(rest[0]["bbox"][0] - c["bbox"][2]) < 0.5:
                            texts[i] = ch + _row_text(dict(cells=rest))
                        break
    return texts


def split_merged_tables(pages, cfg):
    """FY2026 portrait pages draw an initiative box, its description, its designation
    statement and its award table as ONE ruled table (p.36: 32 row bands, one pdfplumber
    table). Split such a table where FY2027 draws separate ones, so the rest of the pipeline
    sees the same shapes in both years:

      - a row that is an award header (config `award_header_re`) below row 0 starts a new
        table;
      - a row whose text starts with the statement prefix, and the rows under it up to the
        award header (none holding an EIN), become loose text lines (the statement), as
        FY2027 prints them.

    Row indices are kept as printed (so award ids still say where the row is); tables on the
    page are renumbered top to bottom and orphans are re-pointed by position. Off unless the
    year's config sets `structure.split_merged_tables`. Returns new page dicts; the input
    (the vector cache) is not modified."""
    if not cfg["structure"].get("split_merged_tables"):
        return pages
    hdr_re = re.compile(cfg["structure"]["award_header_re"])
    prefix = cfg["structure"]["statement_prefix"]
    split_boxes = cfg["structure"].get("split_boxes")
    in_cell = cfg["structure"].get("statement_in_cell")
    split_after = cfg["structure"].get("split_boxes_after_rows")
    stmt_loose = cfg["structure"].get("statement_loose_text")
    # A box row inside a table that starts with an award header and has no statement row
    # (FY2023 p.53: "... Community Schools rows | (empty band) | Educational Programs for
    # Students | $7,143,133 | Agency: ...", the box's statement on in the next table). The
    # table is split there as `split_boxes_after_rows` splits one with a statement.
    in_award = split_after and cfg["structure"].get("split_boxes_award_tables")
    # An award header printed partly outside the table's rules, in the same row band (FY2021
    # p.35: "Legal Name of Organization | EIN" in cells, "Amount" loose beside them): read
    # with its loose words, so the statement above it ends there and the table splits there.
    band_words = cfg["structure"].get("header_band_words")

    sub_heads = set(cfg["structure"].get("award_subheadings", []))

    def seg_award(x0):
        # The segment is an award table: it starts at the award header or, in a year with
        # award-table sub-headings (FY2021 p.72), at a sub-heading or an award row carried
        # over from the page before.
        return bool(hdr_re.search(x0) or (sub_heads and (x0 in sub_heads or
                                                          EIN_IN_TEXT.search(x0))))

    def box_row(i, x):
        # A second initiative box drawn inside the same ruled table, directly under the first
        # box's statement (FY2025 p.35: "Adult Literacy Pilot Project | $2,500,000" in row 11).
        # Off unless the year's config sets `structure.split_boxes`.
        return bool(split_boxes and i > 0 and re.search(r"\$[\d,]+$", x) and
                    not EIN_IN_TEXT.search(x) and not x.startswith(prefix))

    out = []
    for p in pages:
        tables, lines = [], list(p["lines"])
        for t in p["tables"]:
            texts = _row_texts_with_slivers(t)
            if band_words:
                for i, r in enumerate(t["rows"]):
                    bh = _band_header(r, p["lines"], t["bbox"][0], t["bbox"][2], prefix)
                    if bh is not None and hdr_re.search(_row_text(bh)):
                        texts[i] = _row_text(bh)
            if not any((hdr_re.search(x) and i > 0) or x.startswith(prefix)
                       or (in_cell and (" " + prefix) in x)
                       or (in_award and hdr_re.search(texts[0]) and box_row(i, x) and
                           x.count(" | ") == 1 and not re.search(r"\d{2}-\d", x))
                       for i, x in enumerate(texts)):
                tables.append(dict(t, _orig=t["table_index"]))
                continue
            segs, cur, in_stmt = [], [], False
            for i, (r, x) in enumerate(zip(t["rows"], texts)):
                k = x.find(" " + prefix) if in_cell else -1
                if k > 0 and not hdr_re.search(x) and not EIN_IN_TEXT.search(x):
                    # The statement starts on a later line of a description cell (FY2025
                    # p.168: "Scope of Service: ... for Fiscal 2025 only." / "Designation
                    # Method: The Council will designate awards post-adoption."). The row
                    # stays as it is; its statement part is also read as a text line.
                    if cur:
                        segs.append(cur)
                    cur, in_stmt = [], True
                    xs = [c["bbox"] for c in r["cells"] if c["text_raw"].strip()]
                    lines.append(dict(top=r["top"], bottom=r["bottom"],
                                      x0=min(b[0] for b in xs), x1=max(b[2] for b in xs),
                                      text=" ".join(x[k:].replace(" | ", " ").split()),
                                      size=0.0, bold=False, from_table=True))
                    continue
                if (in_stmt and box_row(i, x)) or (split_after and cur and not in_stmt and
                                                   seg_award(texts[t["rows"].index(cur[0])])
                                                   and box_row(i, x) and x.count(" | ") == 1
                                                   and not re.search(r"\d{2}-\d", x)):
                    # ... or right under the award rows of the box before it (FY2024 p.122:
                    # "Supportive Alternatives to Violent Encounters (SAVE) | $1,850,000" after
                    # the first SAVE box's one award row): two text cells, title and amount,
                    # with nothing EIN-like ("13-294-6970" is a malformed EIN, not a box).
                    if cur:
                        segs.append(cur)
                    cur, in_stmt = [r], False
                    continue
                # The statement runs on until the award header (p.209 wraps it into a row of
                # two cells: "to the following providers for Fiscal 2026 | .").
                if x.startswith(prefix) or (in_stmt and not hdr_re.search(x)
                                            and not EIN_IN_TEXT.search(x)):
                    if cur:
                        segs.append(cur)
                    cur, in_stmt = [], True
                    xs = [c["bbox"] for c in r["cells"] if c["text_raw"].strip()]
                    if not xs:
                        continue    # an empty band under the statement (FY2025 p.35 r10)
                    text = " ".join(x.replace(" | ", " ").split())
                    if stmt_loose and text == prefix:
                        # The statement's words sit in the band but in no cell (FY2024 p.217:
                        # "Designation Method:" alone in a cell, "The City Council has
                        # designated ..." beside it, outside the cells). Loose lines centred in
                        # the band
                        # and inside the table's width are read into it, and taken out of
                        # the page's loose lines.
                        side = [ln for ln in lines if not ln.get("from_table") and
                                r["top"] <= (ln["top"] + ln["bottom"]) / 2 < r["bottom"] and
                                t["bbox"][0] <= ln["x0"] and ln["x1"] <= t["bbox"][2]]
                        for ln in sorted(side, key=lambda ln: ln["x0"]):
                            text = " ".join((text + " " + ln["text"]).split())
                            lines.remove(ln)
                    lines.append(dict(top=r["top"], bottom=r["bottom"],
                                      x0=min(b[0] for b in xs), x1=max(b[2] for b in xs),
                                      text=text, size=0.0, bold=False, from_table=True))
                    continue
                in_stmt = False
                if hdr_re.search(x) and cur:
                    segs.append(cur)
                    cur = []
                cur.append(r)
            if cur:
                segs.append(cur)
            for rows in segs:
                tables.append(dict(table_index=None, _orig=t["table_index"], rows=rows, bbox=[
                    t["bbox"][0], rows[0]["top"], t["bbox"][2],
                    max(c["bbox"][3] for r in rows for c in r["cells"])]))
        tables.sort(key=lambda t: (t["bbox"][1], t["bbox"][0]))
        for i, t in enumerate(tables):
            t["table_index"] = i
        orphans = []
        for o in p["orphans"]:
            cy = (o["bbox"][1] + o["bbox"][3]) / 2
            same = [t for t in tables if t["_orig"] == o["table"]]
            hit = [t for t in same if t["bbox"][1] <= cy < t["bbox"][3]] or (
                # `orphans_in_gaps` (FY2020 p.113): an orphan in a band that went to no
                # segment (a statement's words beside its label, read as the statement) is in
                # no table, not in the table's first segment.
                [] if cfg["structure"].get("orphans_in_gaps") else same)
            orphans.append(dict(o, table=hit[0]["table_index"] if hit else -1))
        lines.sort(key=lambda ln: (ln["top"], ln["x0"]))
        out.append(dict(p, tables=tables, lines=lines, orphans=orphans))
    return out


# A side list's header labels as printed (FY2019 pp.105-106; FY2018 p.106 prints "Amount" and
# "Service Type" in one header cell, read as `amount_service`).
SIDE_LABELS = {"Organization": "org", "EIN": "ein", "Amount": "amount",
               "Service Type": "service_type", "Amount Service Type": "amount_service"}
MONEY_TOKEN = re.compile(r"\$[\d,]+")


def _side_rows(part, hdr, pn, flag):
    """The rows of a side list (structure `side_lists`; FY2019 pp.105-106, FY2018 p.106) as
    sub-award records. Each cell goes to the header cell over its centre (some rows are cut
    into narrow phantom cells, p.105 r11); a row band with no EIN is the wrapped text of the row
    above ("Placement", p.105 r13), joined to it with its line break, flagged. The list's later
    tables print no header of their own (FY2018 p.106): the first table's header holds."""
    hcells = [c for c in hdr["cells"] if c["text_raw"].strip()]
    cols = []
    for c in hcells:
        t_ = " ".join(c["text_raw"].split())
        if t_ not in SIDE_LABELS:
            flag("H4.header", "critical", pn, f"side list header label not known: {t_!r}")
            return []
        cols.append((SIDE_LABELS[t_], c["bbox"][0], c["bbox"][2]))

    def field_of(c):
        cx = (c["bbox"][0] + c["bbox"][2]) / 2
        hit = [f for f, a, b in cols if a <= cx < b]
        return hit[0] if hit else min(cols, key=lambda k: abs((k[1] + k[2]) / 2 - cx))[0]

    out = []
    for k_, u in enumerate(part):
        for r in u["rows"][(1 if k_ == 0 else 0):]:
            raw = {}
            boxes = []
            for c in sorted(r["cells"], key=lambda c: c["bbox"][0]):
                if not c["text_raw"].strip():
                    continue
                f = field_of(c)
                raw[f] = (raw[f] + "\n" + c["text_raw"]) if f in raw else c["text_raw"]
                boxes += c["char_boxes"]
            if not raw:
                continue
            x0 = min(c["bbox"][0] for c in r["cells"])
            x1 = max(c["bbox"][2] for c in r["cells"])
            band = [x0, r["top"], x1, r["bottom"]]
            if not EIN_IN_TEXT.search(_row_text(r)) and out and out[-1]["table_index"] == \
                    u["table_index"]:
                prev = out[-1]
                for f, v in raw.items():
                    prev["_raw"][f] = (prev["_raw"][f] + "\n" + v) if prev["_raw"].get(f) else v
                prev["bbox_pt"][3] = r["bottom"]
                prev["_char_boxes"] += boxes
                if "continuation_row" not in prev["row_flags"]:
                    prev["row_flags"].append("continuation_row")
                continue
            out.append(dict(pdf_page=pn, table_index=u["table_index"], row_index=r["row_index"],
                            bbox_pt=list(band), _raw=raw, _char_boxes=boxes, row_flags=[]))
    for sa in out:
        raw = dict(sa["_raw"])    # sa["_raw"] stays as the cells read (the image check's view)
        if "amount_service" in raw:
            # One cell for both (FY2018 p.106): the "$" figure is the amount; the rest of the
            # cell, its lines kept, is the service type. Flagged (routine).
            lines = raw.pop("amount_service").split("\n")
            amt = next((m.group(0) for ln in lines for m in [MONEY_TOKEN.search(ln)] if m), "")
            rest = [MONEY_TOKEN.sub("", ln, count=1).strip() if amt and amt in ln else ln
                    for ln in lines]
            raw["amount"] = amt
            raw["service_type"] = "\n".join(ln for ln in rest if ln.strip())
            sa["row_flags"].append("shared_column")
        sa["org_raw"] = raw.get("org", "")
        sa["org"], _ = clean_text(sa["org_raw"])
        sa["service_type_raw"] = raw.get("service_type", "")
        sa["service_type"], _ = clean_text(sa["service_type_raw"])
        sa["ein_printed"] = raw.get("ein", "").strip()
        sa["ein"] = sa["ein_printed"].replace("-", "") if EIN_RE.match(sa["ein_printed"]) else ""
        sa["amount_printed"] = " ".join(raw.get("amount", "").split())
        sa["amount"] = parse_amount(sa["amount_printed"])
        sa["subaward_id"] = f"p{pn:03d}-t{sa['table_index']:02d}-r{sa['row_index']:03d}"
        for f, bad in (("ein", "ein_unreadable"), ("amount", "amount_unreadable")):
            if not sa[f]:
                sa["row_flags"].append(bad)
                flag("H5.anchors", "critical", pn, f"side list row {f} unreadable: "
                     f"{raw.get(f, '')!r}", table_index=sa["table_index"],
                     row_index=sa["row_index"], field=f)
    return out


def _link_subawards(subawards, awards, cfg, flag):
    """Each sub-award's parent: the one award its list names (`parent` in the year's
    `side_lists` entry: page, EIN, amount as printed). The FY2018 list's page prints what is
    left of the parent (`remainder`, p.105: "The remaining $690,700 will be used by CWE"):
    parent amount - sub-awards = remainder, or a critical flag."""
    fy = cfg["fiscal_year"] % 100
    by_parent = {}
    for sa in subawards:
        side = sa.pop("side_list")
        if "parent" not in side:
            raise ValueError(f"{cfg.get('_path', 'the year config')}: [[side_lists]] page "
                             f"{side['page']} has no `parent` (page, ein, amount of the award "
                             "the list breaks down)")
        pa = side["parent"]
        hit = [a for a in awards if a["pdf_page"] == pa["page"] and a["ein"] == pa["ein"]
               and a["amount"] == pa["amount"]]
        if len(hit) != 1:
            flag("K.side_list_parent", "critical", sa["pdf_page"], f"side list parent "
                 f"{pa} found {len(hit)} times", table_index=sa["table_index"])
            sa["parent_award_id"] = ""
        else:
            sa["parent_award_id"] = hit[0]["award_id"]
            by_parent.setdefault(hit[0]["award_id"], (hit[0], pa, []))[2].append(sa)
        sa["subaward_id"] = f"fy{fy:02d}-sub-{sa['subaward_id']}"
    for aid, (a, pa, subs) in by_parent.items():
        tot = sum(sa["amount"] or 0 for sa in subs)
        if "remainder" in pa and a["amount"] - tot != pa["remainder"]:
            flag("K.side_list_sum", "critical", pa["page"], f"{a['org']} ${a['amount']:,} less "
                 f"its {len(subs)} sub-awards ${tot:,} is ${a['amount'] - tot:,}; the page prints "
                 f"a remainder of ${pa['remainder']:,}", award_id=aid,
                 expected=pa["remainder"], observed=a["amount"] - tot,
                 dollar_impact=abs(a["amount"] - tot - pa["remainder"]))
        elif tot > a["amount"]:
            flag("K.side_list_sum", "critical", pa["page"], f"{a['org']} ${a['amount']:,}: its "
                 f"{len(subs)} sub-awards add to more, ${tot:,}", award_id=aid,
                 dollar_impact=tot - a["amount"])


def build(pages, cfg):
    """Vector pages -> dict(categories, summary_lines, initiatives, awards, flags, events)."""
    s = cfg["structure"]
    labels = [(p, f) for p, f in s["header_labels"]]
    categories = set(cfg["categories"])
    sections = cfg["sections"]  # list of {name, title_re}
    flags = []

    def flag(check, severity, page, msg, **kw):
        flags.append(dict(check_id=check, severity=severity, pdf_page=page, message=msg, **kw))

    # Letters printed just left of a table's left rule, in its first row band (FY2025 p.36):
    # loose lines of one or two characters that straddle the rule.
    edge_letters, edge_digits = {}, {}
    if s.get("amount_sliver_join"):
        # Digits printed just right of a table's right rule, in its first row band (FY2025
        # p.260: the last "0" of a box amount).
        for p in pages:
            for t in p["tables"]:
                r0 = t["rows"][0]
                for ln in p["lines"]:
                    if re.fullmatch(r"\d{1,2}", ln["text"]) and \
                            t["bbox"][2] - 3 <= ln["x0"] <= t["bbox"][2] + 3 and \
                            r0["top"] <= (ln["top"] + ln["bottom"]) / 2 < r0["bottom"]:
                        edge_digits[(p["page"], t["table_index"])] = ln["text"]
    if s.get("box_title_letters"):
        for p in pages:
            for t in p["tables"]:
                r0 = t["rows"][0]
                for ln in p["lines"]:
                    if len(ln["text"]) <= 2 and ln["x0"] < t["bbox"][0] <= ln["x1"] and \
                            r0["top"] <= (ln["top"] + ln["bottom"]) / 2 < r0["bottom"]:
                        edge_letters[(p["page"], t["table_index"])] = ln["text"]

    page_lines = {p["page"]: p["lines"] for p in pages}

    # 1. One event list in (page, top) order.
    events = []
    for p in pages:
        pn = p["page"]
        for t in p["tables"]:
            kind = table_kind(t, cfg)
            events.append((pn, t["bbox"][1], 1, kind, t))
        for ln in p["lines"]:
            events.append((pn, ln["top"], 0, "line", ln))
    events.sort(key=lambda e: (e[0], e[1], e[2]))

    category, section = None, "body"
    current, initiatives, summary, awards = None, [], [], []
    header_rows = {}  # (page, table_index) -> header row bands, where not 1
    band_words = {}   # (page, table_index) -> boxes of loose header words read (header_band_words)
    beside = set()    # ids of loose lines read into a statement beside its label
    # Sub-headings printed as a row of an award table (FY2021 p.70 "Technical Assistance",
    # "Community Consultant Contracts"; config `structure.award_subheadings`, the texts as
    # printed): not award rows; the rows under one carry it in `program_or_subheading`
    # (flagged), so `purpose` holds only a printed purpose (decided in #209).
    subheads = set(s.get("award_subheadings", []))
    sub_of = {}       # initiative_id -> the sub-heading the rows under it are printed beneath
    covered = {}      # (page, table_index) -> char boxes read that are in no award row
    side_tables = {}  # page -> bboxes of tables named in `side_lists` (not award rows)
    subawards = []    # rows of the tables named in `side_lists` (_side_rows)
    table_totals = []  # TOTAL rows closing an award table (`award_table_totals`)

    def _subhead(r):
        texts = {" ".join(c["text_raw"].split()) for c in r["cells"] if c["text_raw"].strip()}
        return next(iter(texts)) if len(texts) == 1 and texts <= subheads else None
    stmt_buf = None  # collecting a designation statement
    last_cols = last_owner = None

    def close_statement():
        nonlocal stmt_buf
        if stmt_buf is None:
            return
        text = " ".join(stmt_buf["lines"])
        kind, reserve, designated = statement_kind(text, cfg)
        if current is None:
            flag("H12.statement", "critical", stmt_buf["page"], "statement with no initiative box")
        else:
            current.update(statement=text, statement_kind=kind, reserve=reserve,
                           designated=designated, statement_page=stmt_buf["page"])
            if kind == "unknown":
                flag("H12.statement", "critical", stmt_buf["page"],
                     f"unknown designation statement: {text[:160]}",
                     initiative=current["initiative"])
        stmt_buf = None

    for pn, top, _, kind, obj in events:
        if kind == "line":
            text = obj["text"]
            sec = next((x["name"] for x in sections if re.fullmatch(x["title_re"], text.strip())),
                       None)
            if sec:
                close_statement()
                section, current = sec, None
                continue
            if obj["size"] >= s["banner_min_size"] and obj["bold"] and text in categories:
                close_statement()
                category, current = text, None
                continue
            if subheads and text in subheads and current is not None:
                # A sub-heading printed above the award table's header (p.70 "Technical
                # Assistance"), not in a row of it.
                close_statement()
                sub_of[current["initiative_id"]] = text
                continue
            if text.startswith(s["statement_prefix"]):
                close_statement()
                stmt_buf = dict(page=pn, bottom=obj["bottom"],
                                lines=[text[len(s["statement_prefix"]):].strip()])
                if s.get("statement_beside_label") and text.strip() == s["statement_prefix"]:
                    # The label alone, the statement's first line beside it as its own loose
                    # line, set off by a tab (FY2020 p.161: "Designation Method:" in bold at
                    # x 80-179, "The City Council has designated ..." from x 224 in the same
                    # band). Read into the statement, in reading order.
                    cy = (obj["top"] + obj["bottom"]) / 2
                    span = s.get("statement_beside_label_span")
                    # `statement_beside_label_span` (FY2019 pp.43, 105: the label centred
                    # between the statement's two lines, "The City Council has designated ...
                    # for Fiscal" above its centre and "2019:" below): every loose line beside
                    # the label whose height overlaps the label's, in reading order.
                    side = sorted((ln for ln in page_lines.get(pn, []) if ln is not obj and
                                   not ln.get("from_table") and ln["x0"] > obj["x1"] and
                                   ((ln["top"] < obj["bottom"] and obj["top"] < ln["bottom"])
                                    if span else ln["top"] <= cy < ln["bottom"])),
                                  key=lambda ln: (ln["top"], ln["x0"]) if span else ln["x0"])
                    if side:
                        stmt_buf["lines"] = [" ".join(ln["text"] for ln in side)]
                        stmt_buf["bottom"] = max(obj["bottom"], *(ln["bottom"] for ln in side))
                        beside.update(id(ln) for ln in side)
                continue
            if id(obj) in beside:
                continue
            # A statement continues only on the next text line directly below it on the same
            # page (12 pt leading; 6 pt slack). That keeps a page's running sub-heading (a
            # category name under the header, e.g. p.116) out of the statement before it.
            if stmt_buf is not None and pn == stmt_buf["page"] and \
                    -3 <= obj["top"] - stmt_buf["bottom"] <= 6 and \
                    not re.fullmatch(s["page_furniture_re"], text):
                if s.get("header_band_words") and not obj.get("from_table") and \
                        HEADER_WORD.search(" ".join(
                            ln["text"] for ln in page_lines.get(pn, [])
                            if not ln.get("from_table") and abs(
                                ln["top"] + ln["bottom"] - obj["top"] - obj["bottom"]) <= 6)):
                    # The award header printed as loose text right under the statement
                    # (FY2021 p.40 "Legal Name", "EIN", "Amount"): it ends the statement.
                    close_statement()
                    continue
                stmt_buf["lines"].append(text)
                stmt_buf["bottom"] = obj["bottom"]
            continue

        t = obj
        if s.get("skip_empty_first_row") and len(t["rows"]) > 1 and \
                not any(c["text_raw"].strip() for c in t["rows"][0]["cells"]):
            # An empty row band drawn above a box's title bar (FY2021 p.84, Queens Borough
            # Public Library's subsidy): the table is read from its first row with text.
            t = dict(t, rows=t["rows"][1:])
            kind = table_kind(t, cfg)
        if kind != "line":
            close_statement()
        headerless = False
        loose_hdr = None
        if kind in ("other", "box") and s.get("loose_header"):
            # The award header printed as loose text just above the table, outside its rules
            # (FY2024 p.149: "Legal Name of Organization", "EIN", "Amount" in bold, 10 pt above
            # the first rule). Each loose line goes to the first-row cell under its centre; the
            # table is an award table when that gives a known org, EIN and amount column and
            # its first row holds an EIN and an amount there.
            above = [ln for ln in page_lines.get(pn, []) if -2 <= t["bbox"][1] - ln["bottom"] <= 14
                     and not ln.get("from_table") and not (
                         s.get("header_band_words") and ln["text"].startswith(s["statement_prefix"]))]
            if s.get("header_band_words") and above:
                # Only the line band nearest the table (FY2021 p.85: the statement's second
                # line, "designate $30,000 post adoption:", is 12 pt above the header).
                low = max(ln["bottom"] for ln in above)
                above = [ln for ln in above if low - ln["bottom"] <= 3]
            hc = [dict(c, text_raw="") for c in t["rows"][0]["cells"]]
            for ln in above:
                for wx0, wx1, wt in ln.get("words", []):
                    cx = (wx0 + wx1) / 2
                    hit = [c for c in hc if c["bbox"][0] <= cx < c["bbox"][2]]
                    if hit:
                        hit[0]["text_raw"] = (hit[0]["text_raw"] + " " + wt).strip()
            c2, u2 = header_map(dict(cells=hc), labels)
            f2 = dict(c2)
            if "org" not in f2 and {"ein", "amount"} <= set(f2):
                # The name column's label printed inside the table above (p.265: "Legal Name
                # of Organization" in the box table's last band, "EIN Amount" loose below it):
                # the first-row cell left of the EIN column, when it holds text, is the name.
                left = [c for c in t["rows"][0]["cells"] if c["bbox"][2] <= f2["ein"] and
                        c["text_raw"].strip()]
                if len(left) == 1:
                    c2 = c2 + [("org", (left[0]["bbox"][0] + left[0]["bbox"][2]) / 2)]
                    f2 = dict(c2)
            if above and not u2 and {"org", "ein", "amount"} <= set(f2):
                c_ein = _cell_at(t["rows"], 0, f2["ein"])[0]
                c_amt = _cell_at(t["rows"], 0, f2["amount"])[0]
                ein_ok = EIN_LIKE if s.get("header_band_words") else EIN_RE
                if c_ein and c_amt and ein_ok.match(c_ein["text_raw"].strip()) and \
                        parse_amount(c_amt["text_raw"]) is not None:
                    kind, loose_hdr = "award", c2
        band_hdr = None
        if s.get("header_band_words") and loose_hdr is None and len(t["rows"]) > 1 and (
                kind != "award" or not {"org", "ein", "amount"} <= set(dict(header_map(
                    t["rows"][0], labels)[0]))):
            # The award header printed partly outside the table's rules, in its first row band
            # (FY2021 p.45: "EIN" in a cell, "Legal Name of Organization" and "Amount" loose
            # beside it; p.35 after the table split). Read with the loose words when that gives
            # a known org, EIN and amount column and the row under it holds an EIN and an
            # amount there. Flagged on every row.
            bh = _band_header(t["rows"][0], page_lines.get(pn, []), t["bbox"][0], t["bbox"][2],
                              s["statement_prefix"])
            if bh is not None:
                c2, u2 = header_map(bh, labels)
                f2 = dict(c2)
                if not u2 and {"org", "ein", "amount"} <= set(f2):
                    c_ein = _cell_at(t["rows"], 1, f2["ein"])[0]
                    c_amt = _cell_at(t["rows"], 1, f2["amount"])[0]
                    if c_ein and c_amt and EIN_RE.match(c_ein["text_raw"].strip()) and \
                            parse_amount(c_amt["text_raw"]) is not None:
                        kind, band_hdr = "award", c2
                        # Its loose words are header text, read: H7 does not count them as
                        # characters in no cell.
                        band_words[(pn, t["table_index"])] = bh["band_words"]
                        covered.setdefault((pn, t["table_index"]), []).extend(bh["band_words"])
        if s.get("header_one_cell") and band_hdr is None and loose_hdr is None and \
                len(t["rows"]) > 1:
            # The award header drawn as one cell over the whole width, the rows under it in
            # four (FY2020 pp.162-164, Neighborhood Development Grant Initiative: "Council
            # Member Legal Name of Organization EIN Amount"). Its words go to the row-1 cell
            # under each word's centre; read when that names org, EIN and amount and row 1
            # holds an EIN and an amount there. Flagged on every row.
            h0 = [c for c in t["rows"][0]["cells"] if c["text_raw"].strip()]
            if len(h0) == 1 and re.search(s["award_header_re"], " ".join(h0[0]["text_raw"].split())):
                hc = [dict(c, text_raw="") for c in t["rows"][1]["cells"]]
                for wx0, wx1, wt in _cell_words(h0[0]):
                    hit = [c for c in hc if c["bbox"][0] <= (wx0 + wx1) / 2 < c["bbox"][2]]
                    if hit:
                        hit[0]["text_raw"] = (hit[0]["text_raw"] + " " + wt).strip()
                c2, u2 = header_map(dict(cells=hc), labels)
                f2 = dict(c2)
                if not u2 and {"org", "ein", "amount"} <= set(f2):
                    c_ein = _cell_at(t["rows"], 1, f2["ein"])[0]
                    c_amt = _cell_at(t["rows"], 1, f2["amount"])[0]
                    if c_ein and c_amt and EIN_LIKE.match(c_ein["text_raw"].strip()) and \
                            parse_amount(c_amt["text_raw"]) is not None:
                        kind, band_hdr = "award", c2
        if kind in ("other", "box") and s.get("headerless_continuation") and last_cols and \
                last_owner is current:
            # An award table carried over a page break with no header row (FY2026 p.157,
            # where a one-row carry-over otherwise reads as an initiative box "...| $98,469";
            # p.195): it continues the last award table when nothing (box, summary, banner,
            # section) came between, and the previous header's EIN and amount columns land on
            # an EIN and an amount in its first row. Flagged on every row.
            k0 = 1 if subheads and len(t["rows"]) > 1 and _subhead(t["rows"][0]) else 0
            c_ein = _cell_at(t["rows"], k0, dict(last_cols)["ein"])[0]
            c_amt = _cell_at(t["rows"], k0, dict(last_cols)["amount"])[0]
            ein_ok = (EIN_RE.match(c_ein["text_raw"].strip()) or (
                s.get("short_ein_rows") and EIN_LIKE.match(c_ein["text_raw"].strip()))) \
                if c_ein else None
            if c_ein and c_amt and ein_ok and \
                    parse_amount(c_amt["text_raw"]) is not None:
                kind, headerless = "award", True
        if kind == "other" and s.get("box_title_above"):
            # A box whose title bar is printed above the table's top rule, outside its cells,
            # the table starting at "Agency:" (FY2018 p.94: "Crisis Management System – Cure
            # Violence" and "$4,775,000" in the band over the table). Read as the box's first
            # row; flagged, so a person confirms it.
            r0 = t["rows"][0]
            t0 = " ".join(_row_text(r0).split())
            band = [ln for ln in page_lines.get(pn, []) if not ln.get("from_table") and
                    -1.0 <= t["bbox"][1] - ln["bottom"] <= 3.0 and
                    t["bbox"][0] - 2 <= ln["x0"]]   # p.95: the table only as wide as "Agency:"
            money = [ln for ln in band if re.fullmatch(r"\$[\d,]+", ln["text"])]
            title = [ln for ln in band if ln not in money]
            if t0.startswith("Agency:") and len(money) == 1 and title and \
                    max(ln["x1"] for ln in title) < money[0]["x0"] and \
                    not any(EIN_IN_TEXT.search(ln["text"]) for ln in title):
                top = min(ln["top"] for ln in band)
                x1 = max(t["bbox"][2], money[0]["x1"])
                cells = [dict(bbox=[t["bbox"][0], top, money[0]["x0"], t["bbox"][1]],
                              text_raw=" ".join(ln["text"] for ln in
                                                sorted(title, key=lambda ln: ln["x0"])),
                              nchars=0, char_boxes=[]),
                         dict(bbox=[money[0]["x0"], top, x1, t["bbox"][1]],
                              text_raw=money[0]["text"], nchars=0, char_boxes=[])]
                t = dict(t, rows=[dict(r0, row_index=-1, top=top, bottom=t["bbox"][1],
                                       cells=cells)] + t["rows"])
                kind = "box"
                flag("W.box_title_above", "warn", pn, f"box title {cells[0]['text_raw']!r} "
                     f"and amount {money[0]['text']!r} printed above the box's table, outside "
                     "its rules; read as its title bar; confirm on the page",
                     table_index=t["table_index"], field=cells[0]["text_raw"],
                     dollar_impact=parse_amount(money[0]["text"]))
        if kind == "other" and s.get("box_amount_loose"):
            # A box drawn narrower than its title bar, its amount printed beside it outside
            # the rules (FY2021 p.98: "Naturally Occurring Retirement Communities (NORCs)" in
            # a table 79-388 wide, "$5,400,325" loose at x 478-531 in the same band). Read as
            # the box's amount cell; flagged.
            r0 = t["rows"][0]
            texts0 = [c for c in r0["cells"] if c["text_raw"].strip()]
            side = [ln for ln in page_lines.get(pn, []) if not ln.get("from_table") and
                    re.fullmatch(r"\$[\d,]+", ln["text"]) and ln["x0"] >= t["bbox"][2] - 2 and
                    r0["top"] <= (ln["top"] + ln["bottom"]) / 2 < r0["bottom"]]
            if len(texts0) == 1 and len(side) == 1 and not EIN_IN_TEXT.search(texts0[0]["text_raw"]):
                ln = side[0]
                cell = dict(bbox=[ln["x0"], r0["top"], ln["x1"], r0["bottom"]],
                            text_raw=ln["text"], nchars=len(ln["text"]), char_boxes=[])
                t = dict(t, rows=[dict(r0, cells=r0["cells"] + [cell])] + t["rows"][1:])
                kind = "box"
                flag("W.box_amount_loose", "warn", pn, f"box amount {ln['text']!r} printed "
                     f"outside the box's rules, beside {texts0[0]['text_raw'][:60]!r}; read as "
                     "its amount; confirm on the page", table_index=t["table_index"],
                     field="amount", dollar_impact=parse_amount(ln["text"]))
        if kind == "other":
            only = [c["text_raw"] for c in t["rows"][0]["cells"] if c["text_raw"].strip()]
            if len(t["rows"]) == 1 and len(only) == 1 and only[0] in categories:
                category, current = only[0], None
            elif s.get("banner_variants"):
                # A category banner drawn as a table with empty bands above and below it (FY2020
                # p.111 "Housing"), or printed twice over itself, the text layer holding it on
                # two lines (p.97 "Health Services\nHealth Services"). Flagged.
                texts = [c["text_raw"] for r in t["rows"] for c in r["cells"]
                         if c["text_raw"].strip()]
                names = {ln.strip() for x in texts for ln in x.split("\n") if ln.strip()}
                if len(names) == 1 and next(iter(names)) in categories:
                    category, current = next(iter(names)), None
                    flag("W.banner_variant", "warn", pn, f"category banner {category!r} read "
                         f"from a table of {len(t['rows'])} row band(s) holding {texts!r}",
                         table_index=t["table_index"], dollar_impact=0)
            continue
        if kind == "summary":
            for r in t["rows"][1:]:
                cells = [" ".join(c["text_raw"].split()) for c in r["cells"]]
                texts = [x for x in cells if x]
                if not texts or texts == ["Agency", "Initiative", "Amount"]:
                    continue
                amt = parse_amount(texts[-1])
                half = len(texts[-1]) // 2
                if amt is None and s.get("summary_amount_doubled") and \
                        texts[-1][:half] == texts[-1][half:] and parse_amount(texts[-1][:half]):
                    # The text layer holds the amount twice, side by side, where the page shows
                    # it once (FY2020 p.145 "$3,383,670$3,383,670"). Read once; flagged.
                    amt = parse_amount(texts[-1][:half])
                    flag("W.summary_amount_doubled", "warn", pn, f"summary amount's text is "
                         f"printed twice, {texts[-1]!r}; the page shows it once; read as "
                         f"{amt:,}; confirm on the page", table_index=t["table_index"],
                         row_index=r["row_index"], field="amount", dollar_impact=amt)
                if amt is None and s.get("summary_amount_without_dollar") and \
                        re.fullmatch(r"\d{1,3}(?:,\d{3})+", texts[-1]):
                    # Printed without its "$" (FY2021 p.49, Education "TOTAL | 21,679,075").
                    # Read as the number printed; flagged.
                    amt = int(texts[-1].replace(",", ""))
                    flag("W.summary_amount_no_dollar", "warn", pn, f"summary amount printed "
                         f"without '$': {texts[-1]!r}; read as {amt:,}; confirm on the page",
                         table_index=t["table_index"], row_index=r["row_index"],
                         field="amount", dollar_impact=amt)
                rec = dict(category=category, pdf_page=pn, table_index=t["table_index"],
                           row_index=r["row_index"], bbox_pt=[r["cells"][0]["bbox"][0], r["top"],
                                                              r["cells"][-1]["bbox"][2], r["bottom"]],
                           cells=texts, amount=amt, amount_printed=texts[-1])
                if amt is None:
                    flag("H10.summary_row", "critical", pn, f"summary row amount unreadable: {texts}")
                rec["is_total"] = texts[0].upper() == "TOTAL" or (
                    s.get("total_colon") and texts[0].upper() == "TOTAL:")   # FY2022 p.32
                if not rec["is_total"]:
                    rec["agency"] = texts[0] if len(texts) == 3 else ""
                    rec["initiative"] = texts[-2]
                summary.append(rec)
            continue
        if kind == "box2":
            r0 = [c for c in t["rows"][0]["cells"] if c["text_raw"].strip()]
            cells = [c for c in t["rows"][1]["cells"] if c["text_raw"].strip()]
            title_raw = r0[0]["text_raw"] + "\n" + cells[0]["text_raw"]
            amt_printed = " ".join(cells[-1]["text_raw"].split())
            current = dict(initiative_id=len(initiatives) + 1, initiative=clean_text(title_raw)[0],
                           initiative_raw=title_raw, category=category,
                           section=section, pdf_page=pn, table_index=t["table_index"],
                           amount=parse_amount(amt_printed), amount_printed=amt_printed,
                           bbox_pt=t["bbox"], statement="", statement_kind="none",
                           reserve=None, designated=None, n_rows=0, rows_sum=0)
            if current["amount"] is None:
                flag("H11.box", "critical", pn, f"box amount unreadable: {amt_printed!r}",
                     initiative=current["initiative"])
            initiatives.append(current)
            continue
        if kind == "box":
            cells = [c for c in t["rows"][0]["cells"] if c["text_raw"].strip()]
            title_raw = cells[0]["text_raw"]
            if s.get("box_title_letters"):
                # The title's first letter drawn apart from the rest (FY2025): in its own
                # narrow cell, abutting the next (p.149 "E" | "nding the Epidemic", p.258 "V" |
                # "eteran Resource Centers"), or left of the table's left rule, outside every
                # cell (p.36 "D" + "igital Inclusion ..."). Put back; H11 (box vs summary
                # line) checks the result. Off unless the year's config sets it.
                if len(cells) > 2 and len(cells[0]["text_raw"].strip()) <= 2 and \
                        abs(cells[1]["bbox"][0] - cells[0]["bbox"][2]) < 0.5:
                    title_raw = cells[0]["text_raw"].strip() + cells[1]["text_raw"]
                    cells = [dict(cells[1], text_raw=title_raw)] + cells[2:]
                lead = edge_letters.get((pn, t["table_index"]))
                if lead and cells[0]["bbox"][0] == t["bbox"][0]:
                    title_raw = lead + title_raw
            if s.get("box_title_tail") and len(cells) > 2 and \
                    len(cells[1]["text_raw"].strip()) <= 2 and \
                    abs(cells[1]["bbox"][0] - cells[0]["bbox"][2]) < 0.5:
                # The title's last letter drawn apart, in its own cell abutting the rest
                # (FY2019 p.74 "Foreclosure Buyback Initiativ" | "e"). Put back; H11 checks it.
                title_raw = title_raw + cells[1]["text_raw"].strip()
                cells = [dict(cells[0], text_raw=title_raw)] + cells[2:]
            amt_printed = " ".join(cells[-1]["text_raw"].split())
            bare = None
            if s.get("box_amount_without_dollar") and parse_amount(amt_printed) is None and \
                    re.fullmatch(r"\d{1,3}(?:,\d{3})+", amt_printed):
                # Printed without its "$" (FY2023 p.92). Read as the number printed; flagged.
                flag("W.box_amount_no_dollar", "warn", pn, f"box amount printed without '$': "
                     f"{amt_printed!r}; read as {int(amt_printed.replace(',', '')):,}; confirm on "
                     "the page", table_index=t["table_index"], field="amount",
                     dollar_impact=int(amt_printed.replace(",", "")))
                bare = int(amt_printed.replace(",", ""))
            if s.get("box_amount_cells") and parse_amount(amt_printed) is None:
                # The box amount cut into several cells by phantom column rules (FY2025 p.157
                # "$" | "5" | "00,000"): the last cells, joined with no space, read as one
                # amount. Flagged, so a person confirms it.
                for k in range(2, min(4, len(cells) - 1) + 1):
                    joined = "".join(c["text_raw"].strip() for c in cells[-k:])
                    if parse_amount(joined) is not None:
                        amt_printed = joined
                        cells = cells[:-k] + [dict(cells[-1], text_raw=joined)]
                        flag("W.box_amount_cells", "warn", pn, f"box amount printed across {k} "
                             f"cells; read as {joined!r}; confirm on the page",
                             table_index=t["table_index"], field="amount",
                             dollar_impact=parse_amount(joined))
                        break
            if len(cells) == 1:
                # Title and amount in one cell, no rule between them (FY2026 pp.218, 220): the
                # amount is the trailing "$N" of the printed text.
                m = re.search(r"\s(\$[\d,]+)$", title_raw)
                if m:
                    title_raw, amt_printed = title_raw[:m.start()], m.group(1)
            # A long title wraps into the next row band of the black bar (p.44): any cell
            # aligned with the title cell that starts above the bottom of the amount cell
            # (which spans the whole bar) is part of the title.
            bar_bottom = cells[-1]["bbox"][3]
            for r in t["rows"][1:]:
                for c in r["cells"]:
                    if c["bbox"][0] == cells[0]["bbox"][0] and c["bbox"][1] < bar_bottom \
                            and c["text_raw"].strip():
                        title_raw += "\n" + c["text_raw"]
            if s.get("amount_sliver_join") and SPLIT_TAIL.match(amt_printed):
                # The last digit(s) of the box amount fall right of the table's right rule
                # (FY2025 p.260 "$250,00" + "0"). Put back from the loose line beside it.
                tail = edge_digits.get((pn, t["table_index"]))
                if tail and parse_amount(amt_printed + tail) is not None:
                    amt_printed += tail
                    flag("W.amount_split_digits", "warn", pn, f"box amount printed across the "
                         f"table's right rule: read as {amt_printed!r}; confirm on the page",
                         table_index=t["table_index"], field="amount",
                         dollar_impact=parse_amount(amt_printed))
            title, _ = clean_text(title_raw)
            current = dict(initiative_id=len(initiatives) + 1, initiative=title,
                           initiative_raw=title_raw, category=category,
                           section=section, pdf_page=pn, table_index=t["table_index"],
                           amount=parse_amount(amt_printed) if bare is None else bare,
                           amount_printed=amt_printed,
                           bbox_pt=t["bbox"], statement="", statement_kind="none",
                           reserve=None, designated=None, n_rows=0, rows_sum=0)
            for rd in s.get("box_amount_read", []):
                # A box amount printed malformed (FY2021 p.122 "$477,00", the summary line
                # "$477,000"): read as the config names it, the printed text kept. Each entry
                # must match page, title and printed text exactly; a critical review item.
                if current["amount"] is None and (rd["page"], rd["initiative"], rd["printed"]) \
                        == (pn, title, amt_printed):
                    current["amount"] = rd["amount"]
                    flag("H11.box_amount_read", "critical", pn, f"box amount printed "
                         f"{amt_printed!r}, read as ${rd['amount']:,}: {rd['note']}",
                         initiative=title, initiative_id=current["initiative_id"],
                         field="amount", dollar_impact=rd["amount"])
            if current["amount"] is None:
                flag("H11.box", "critical", pn, f"box amount unreadable: {amt_printed!r}",
                     initiative=title)
            if category is None:
                flag("H3.category", "critical", pn, f"box before any category: {title}")
            initiatives.append(current)
            continue

        # award table
        hdr = t["rows"][0]
        cols, unknown = (last_cols, []) if headerless else \
            (loose_hdr, []) if loose_hdr else (band_hdr, []) if band_hdr else header_map(hdr, labels)
        first = 0 if (headerless or loose_hdr) else 1
        if unknown and not headerless and not loose_hdr and s.get("header_two_bands") and \
                len(t["rows"]) > 1:
            # A header printed over two row bands (FY2025 pp.131-144: "Council" over "Member",
            # a rule between them). Read as one header only when every text cell of the
            # second band sits under a header cell, it holds no EIN and no amount, and the
            # joined labels are all known; otherwise the unknown label stays a flag.
            joined = _join_header_bands(t["rows"][0], t["rows"][1])
            if joined is not None:
                c2, u2 = header_map(joined, labels)
                if not u2:
                    cols, unknown, first = c2, [], 2
                    header_rows[(pn, t["table_index"])] = 2
        side = next((sl for sl in cfg.get("side_lists", []) if sl["page"] == pn and
                     _row_text(hdr) == sl["header"]), None) if not headerless else None
        if side is not None:
            # A table under an award that lists who the award passes through to (FY2019
            # pp.105-106: "**Below is a list of the Jobs to Build On service providers
            # partners", under CWE's $5,154,200 row). Named in the year's config with its page
            # and header as printed: its rows are not awards and are not counted; the list,
            # its rows and their sum are one review item. Its characters count as read.
            # The list runs on into the ruled tables under it with no header of their own
            # (FY2018 p.106: three tables), up to the next table of another kind.
            part = [t]
            for u in sorted((u for p_ in pages if p_["page"] == pn for u in p_["tables"]
                             if u["bbox"][1] > t["bbox"][1]), key=lambda u: u["bbox"][1]):
                if table_kind(u, cfg) != "other":
                    break
                part.append(u)
            # Its rows are sub-awards (decided in #209): each row with an EIN is one, linked to
            # the award it breaks down (`parent`, below), and not counted in any award total.
            subs = _side_rows(part, hdr, pn, flag)
            for sa in subs:
                sa.update(side_list=side)
            subawards.extend(subs)
            tot = sum(sa["amount"] or 0 for sa in subs)
            flag("K.side_list", "critical", pn, f"{side['note']}: {len(subs)} rows with an EIN, "
                 f"${tot:,} as printed; read as sub-awards of one award (the subawards table), "
                 "not counted as awards", table_index=t["table_index"], dollar_impact=tot)
            for u in part:
                side_tables.setdefault(pn, []).append(u["bbox"])
                covered.setdefault((pn, u["table_index"]), []).extend(
                    b for r in u["rows"] for c in r["cells"] for b in c["char_boxes"])
            continue
        if unknown:
            flag("H4.header", "critical", pn, f"unknown header label(s): {unknown}",
                 table_index=t["table_index"])
        fields = [f for f, _ in cols]
        if "ein" not in fields or "amount" not in fields or "org" not in fields:
            flag("H4.header", "critical", pn, f"award header lacks org/ein/amount: {fields}",
                 table_index=t["table_index"])
            continue
        last_cols, last_owner = cols, current
        rows = t["rows"]
        for ri in range(first, len(rows)):
            r = rows[ri]
            if subheads and _subhead(r):
                sub_of[current["initiative_id"] if current else None] = _subhead(r)
                covered.setdefault((pn, t["table_index"]), []).extend(
                    b for c in r["cells"] for b in c["char_boxes"])
                continue
            rec = dict(pdf_page=pn, table_index=t["table_index"], row_index=r["row_index"],
                       section=section, category=category if section == "body" else "",
                       initiative=current["initiative"] if (current and section == "body") else "",
                       initiative_id=current["initiative_id"] if (current and section == "body") else "",
                       initiative_page=current["pdf_page"] if (current and section == "body") else "",
                       header=" | ".join(fields),
                       row_flags=(["headerless_table"] if headerless else []) +
                       (["loose_header"] if loose_hdr else []) +
                       (["band_header"] if band_hdr else []) +
                       (["hrule_table"] if t.get("hrule") else []))
            x0 = min(c["bbox"][0] for c in r["cells"])
            x1 = max(c["bbox"][2] for c in r["cells"])
            rec["bbox_pt"] = [x0, r["top"], x1, r["bottom"]]
            used = set()
            spans = set()
            char_boxes = []
            for f, x in cols:
                cell, spanned = _cell_at(rows, ri, x)
                if f == "star" and cell is not None and any(
                        _cell_at(rows, ri, x2)[0] is cell for f2, x2 in cols if f2 != "star"):
                    # A row whose cells do not split where the header's "*" column does
                    # (FY2019 p.45: the amount cell runs under the "*"): the cell is the other
                    # column's, not the star's.
                    rec[f + "_raw"] = ""
                    continue
                raw = cell["text_raw"] if cell else ""
                if cell is not None:
                    used.add(tuple(cell["bbox"]))
                    if spanned is None:
                        char_boxes += cell["char_boxes"]
                if spanned is not None and raw:
                    rec["row_flags"].append(f"spanning_cell:{f}")
                    spans.add(f)
                rec[f + "_raw"] = raw
            if s.get("amount_sliver_join") and "amount" in fields:
                # An amount's last digit(s) in the narrow cell right of the amount cell (FY2025
                # p.222 "$200,00" | "0": a white-filled phantom column inside the drawn border).
                # Joined when the amount cell ends in an incomplete thousands group and the two
                # read as one amount; flagged, so a person confirms it.
                ac = _cell_at(rows, ri, dict(cols)["amount"])[0]
                for c in r["cells"]:
                    if ac is not None and tuple(c["bbox"]) not in used and \
                            re.fullmatch(r"\d{1,2}", c["text_raw"].strip()) and \
                            c["bbox"][2] - c["bbox"][0] <= 10 and \
                            abs(c["bbox"][0] - ac["bbox"][2]) < 0.5 and \
                            SPLIT_TAIL.match(rec["amount_raw"].strip()) and \
                            parse_amount(rec["amount_raw"].strip() + c["text_raw"].strip()) is not None:
                        rec["amount_raw"] = rec["amount_raw"].strip() + c["text_raw"].strip()
                        used.add(tuple(c["bbox"]))
                        char_boxes += c["char_boxes"]
                        rec["row_flags"].append("amount_split_digits")
            if s.get("header_span_cells") and not headerless:
                # A data row cut into more cells than its header (FY2025 p.183: the name
                # column's header spans x 72-409, the row's name sits in a cell 77-230 and the
                # cell at the header's centre, 230-409, is empty). A text cell no column
                # claimed goes to the header cell over its centre, if that column read empty.
                spans_x = [(f, hc["bbox"][0], hc["bbox"][2]) for hc in hdr["cells"]
                           for f, x in cols if hc["bbox"][0] <= x < hc["bbox"][2]]
                for c in r["cells"]:
                    if tuple(c["bbox"]) in used or not c["text_raw"].strip():
                        continue
                    cx = (c["bbox"][0] + c["bbox"][2]) / 2
                    hit = [f for f, a, b in spans_x if a <= cx < b]
                    if len(hit) == 1 and not rec[hit[0] + "_raw"].strip():
                        rec[hit[0] + "_raw"] = c["text_raw"]
                        used.add(tuple(c["bbox"]))
                        char_boxes += c["char_boxes"]
                        rec["row_flags"].append(f"header_span_cell:{hit[0]}")
            if s.get("header_overlap_cells") and not headerless and not loose_hdr and \
                    not band_hdr:
                # A data row whose cell borders do not line up with its header's (FY2021 p.73:
                # the header's EIN cell spans x 336-392, its centre falls in an empty 5 pt cell
                # of the data row, whose EIN sits in a cell 375-433). A text cell no column
                # claimed goes to the one header column whose cell it overlaps, if that column
                # read empty; flagged.
                spans_x = [(f, hc["bbox"][0], hc["bbox"][2]) for hc in hdr["cells"]
                           for f, x in cols if hc["bbox"][0] <= x < hc["bbox"][2]]
                for c in r["cells"]:
                    if tuple(c["bbox"]) in used or not c["text_raw"].strip():
                        continue
                    hit = [f for f, a, b in spans_x if a < c["bbox"][2] and c["bbox"][0] < b]
                    if len(hit) == 1 and not rec[hit[0] + "_raw"].strip():
                        rec[hit[0] + "_raw"] = c["text_raw"]
                        used.add(tuple(c["bbox"]))
                        char_boxes += c["char_boxes"]
                        rec["row_flags"].append(f"header_span_cell:{hit[0]}")
            if any(c.get("sliver_chars") for c in r["cells"] if tuple(c["bbox"]) in used):
                rec["row_flags"].append("sliver_char")     # vector.read_page `sliver_chars`
            for c in r["cells"]:
                if tuple(c["bbox"]) not in used and c["text_raw"].strip() == "*" and \
                        "star" not in fields and any(f_ == "star" for _, f_ in labels):
                    # A "*" in its own cell under a header with no "*" column (FY2018 p.127,
                    # Dedicated Contraceptive Fund: "Legal Name of Organization | EIN | Amount"):
                    # the row's asterisk, flagged and a review item.
                    rec["row_flags"] += ["asterisk", "star_in_cell"]
                    char_boxes += c["char_boxes"]
                    flag("W.star_in_cell", "warn", pn, "'*' printed in a cell of its own under a "
                         "header with no '*' column; read as the row's asterisk",
                         table_index=t["table_index"], row_index=r["row_index"], field="star",
                         dollar_impact=0)
                    continue
                if tuple(c["bbox"]) not in used and c["text_raw"].strip():
                    rec["row_flags"].append("unmapped_cell")
                    flag("H7.unmapped", "critical", pn, f"text in a cell no header column claims: "
                         f"{c['text_raw'][:80]!r}", table_index=t["table_index"],
                         row_index=r["row_index"])
            rec["_char_boxes"] = char_boxes
            sub = sub_of.get(current["initiative_id"] if current else None) if subheads else None
            if sub and "program_or_subheading" not in fields:
                rec["program_or_subheading_raw"] = sub
                rec["row_flags"].append("subheading")
            rec["_raw"] = {f: rec[f + "_raw"] for f in fields}
            # A row band whose own cells hold text but no EIN and no amount, directly under an
            # award row of the same table, is the rest of that row's wrapped text: FY2026
            # draws a rule between the two lines of a long name (p.130 "...Washington
            # Heights" / "and Inwood"). Joined to the row above, line break kept; flagged.
            # Text a band only sees through a taller cell above it (spanning) is that row's,
            # not the band's; a band with no text of its own is a sliver of the row above
            # (p.48 r22, under a two-line amount) and is not a row. Off unless the year's
            # config sets `structure.continuation_rows`.
            prev = awards[-1] if awards else None
            own = {f for f in fields if f not in spans and rec[f + "_raw"].strip()}
            if s.get("continuation_rows") and prev is not None and ri > first and \
                    (prev["pdf_page"], prev["table_index"]) == (pn, t["table_index"]) and \
                    "ein" not in own and "amount" not in own:
                for f in sorted(own):
                    prev[f + "_raw"] = (prev[f + "_raw"] + "\n" + rec[f + "_raw"]
                                        if prev[f + "_raw"] else rec[f + "_raw"])
                prev["_raw"] = {f: prev[f + "_raw"] for f in fields}
                prev["_char_boxes"] += char_boxes
                prev["bbox_pt"] = [min(prev["bbox_pt"][0], x0), prev["bbox_pt"][1],
                                   max(prev["bbox_pt"][2], x1), r["bottom"]]
                prev["row_flags"].append(f"continuation_row:r{r['row_index']}" if own
                                         else f"sliver_band:r{r['row_index']}")
                prev["row_flags"] += [f for f in rec["row_flags"] if f not in prev["row_flags"]
                                      and not f.startswith("spanning_cell")]
                continue
            if s.get("award_table_totals") and "org" in fields and \
                    " ".join(rec["org_raw"].split()).upper() == "TOTAL" and \
                    not rec["ein_raw"].strip() and current is not None:
                # A TOTAL row closing an award table (FY2018 p.64: "TOTAL | $1,187,000" under
                # Access Health NYC's rows). Not an award: checked against the rows of its
                # initiative read so far; a mismatch is a critical H12.table_total.
                tot = parse_amount(" ".join(rec["amount_raw"].split()))
                got = sum(parse_amount(" ".join(a["amount_raw"].split())) or 0 for a in awards
                          if a.get("initiative_id") == current["initiative_id"] and
                          a["section"] == section)
                table_totals.append(dict(pdf_page=pn, initiative=current["initiative"],
                                         printed=tot, rows=got))
                if tot != got:
                    # A PDF that disagrees with itself passes only as a named exception matched
                    # on (page, printed, rows), as reconcile's; a warn flag then.
                    exc = next((e for e in cfg.get("exceptions", []) if e["check"] ==
                                "H12.table_total" and (e["page"], e["expected"], e["observed"])
                                == (pn, tot, got)), None)
                    flag("H12.table_total", "warn" if exc else "critical", pn,
                         f"{current['initiative']}: TOTAL row prints "
                         f"{rec['amount_raw'].strip()!r}; its rows add to {got:,}" +
                         (f" (named exception: {exc['note']})" if exc else ""),
                         initiative=current["initiative"], table_index=t["table_index"],
                         row_index=r["row_index"], dollar_impact=abs((tot or 0) - got))
                covered.setdefault((pn, t["table_index"]), []).extend(char_boxes)
                continue
            if not any(rec[f + "_raw"].strip() for f in fields):
                rec["row_flags"].append("empty_row")
            awards.append(rec)
            if current and section == "body":
                current["n_rows"] += 1
    close_statement()

    # Pages whose rows belong to another initiative than the box above them in page order
    # (FY2024 pp.130-137: eight landscape pages with no printed page number, merged in after
    # A Greener NYC's statement (printed p.89); their rows are NYC Cleanup's, whose box is on
    # p.145, and add to exactly the $12,028,500 its statement designates). Named in the year's
    # config, each with its reason; every moved row is flagged and the move is a review item.
    for ip in cfg.get("initiative_pages", []):
        tgt = [i for i in initiatives if i["initiative"] == ip["initiative"] and
               i["category"] == ip["category"]]
        moved = [a for a in awards if ip["first"] <= a["pdf_page"] <= ip["last"] and
                 a["section"] == "body"]
        if len(tgt) != 1 or not moved:
            flag("H12.initiative_pages", "critical", ip["first"], f"initiative_pages: "
                 f"{ip['initiative']!r} found {len(tgt)} times, {len(moved)} rows on the pages")
            continue
        for a in moved:
            old_id = a["initiative_id"]
            for i in initiatives:
                if i["initiative_id"] == old_id:
                    i["n_rows"] -= 1
            a.update(initiative=tgt[0]["initiative"], initiative_id=tgt[0]["initiative_id"],
                     initiative_page=tgt[0]["pdf_page"], category=tgt[0]["category"])
            a["row_flags"].append("reattributed")
            tgt[0]["n_rows"] += 1
        flag("H12.initiative_pages", "critical", ip["first"],
             f"{len(moved)} rows on pp.{ip['first']}-{ip['last']} attached to "
             f"{ip['initiative']!r} (box p.{tgt[0]['pdf_page']}), not to the box above them in "
             f"page order: {ip['note']}", initiative_id=tgt[0]["initiative_id"],
             initiative=ip["initiative"],
             dollar_impact=sum(parse_amount(" ".join(a["amount_raw"].split())) or 0
                               for a in moved))

    # 2. Field cleaning and per-row validation.
    fy = cfg["fiscal_year"] % 100
    for rec in awards:
        rec["award_id"] = (f"fy{fy:02d}-p{rec['pdf_page']:03d}-t{rec['table_index']:02d}"
                           f"-r{rec['row_index']:03d}")
        has_conduit = "conduit_raw" in rec or "conduit_ein_raw" in rec
        if has_conduit:
            # "Fiscal Conduit" and "FC EIN" columns (FY2018, header labels `conduit`,
            # `conduit_ein`; p.10: an organization may receive its funds through a fiscal
            # conduit): kept in `fiscal_conduit` and `fiscal_conduit_ein`, the same fields as
            # the transparency rows (decided in #209).
            rec["fiscal_conduit_raw"] = rec.pop("conduit_raw", "")
            rec["fiscal_conduit_ein_printed"] = rec.pop("conduit_ein_raw", "").strip()
        applied = set()
        for f in TEXT_FIELDS:
            if f + "_raw" in rec:
                rec[f], rules = clean_text(rec[f + "_raw"])
                applied.update(rules)
                if "wrap_hyphen" in rules:
                    rec["row_flags"].append(f"wrap_hyphen:{f}")
                if "cid_glyph" in rules:
                    rec["row_flags"].append(f"cid_glyph:{f}")
            else:
                rec[f], rec[f + "_raw"] = "", ""
        rec["clean_rules_applied"] = ";".join(sorted(applied))
        star_col = "star_raw" in rec
        if star_col or ("hrule_table" in rec["row_flags"] and
                        any(f == "star" for _, f in labels)):
            # A "*" column (FY2019, FY2018, header label `star`). The PDF's footnote (FY2019
            # p.11, FY2018 p.10): "For those organizations identified in Schedule C with an
            # asterisk, either MOCS or the Council's review process has not yet been completed;
            # ... All such reviews and requirements must be completed prior to contract
            # award." Kept in `review_not_completed` (below); any other text there is a review
            # item.
            st = " ".join(rec.pop("star_raw", "").split())
            cut = next((f for f in ("program_or_subheading", "purpose", "org")
                        if re.search(r"(^|\s)\*$", rec[f])),
                       None) if not st and "hrule_table" in rec["row_flags"] else None
            if st == "*":
                rec["row_flags"].append("asterisk")
            elif cut:
                # A table ruled with horizontal lines only has no "*" column of its own (p.94:
                # "Public School / Middle School 183  *" in the Program column): the row is
                # flagged and is a review item. In org or purpose the "*" stays in the cell as
                # printed; in program_or_subheading (row context, not printed text a reader
                # quotes) the clean value drops it, since review_not_completed records it; the
                # raw value keeps it (clean rule `star_mark`).
                printed = rec[cut]
                rec["row_flags"] += ["asterisk", "star_in_cell"]
                if cut == "program_or_subheading":
                    rec[cut] = strip_star(printed)
                    rec["clean_rules_applied"] = ";".join(sorted(
                        set(filter(None, rec["clean_rules_applied"].split(";"))) | {"star_mark"}))
                    how = ("the '*' is the row's mark (review_not_completed), dropped from "
                           "program_or_subheading; program_or_subheading_raw keeps it")
                else:
                    how = "kept in the cell as printed"
                flag("W.star_in_cell", "warn", rec["pdf_page"], f"'*' printed at the end of "
                     f"the {cut} cell {printed[-60:]!r} (no '*' column in this table); {how}",
                     award_id=rec["award_id"],
                     table_index=rec["table_index"], row_index=rec["row_index"], field=cut,
                     dollar_impact=0)
            elif st:
                rec["row_flags"].append("star_text")
                flag("H7.star", "critical", rec["pdf_page"], f"'*' column holds {st!r}",
                     award_id=rec["award_id"], table_index=rec["table_index"],
                     row_index=rec["row_index"], field="star")
        if any(f == "star" for _, f in labels):
            # `review_not_completed`: "1" where the row prints the "*" (in its column or, flagged,
            # in a cell of its own or at the end of a cell); "0" where the row's table has a "*"
            # column and the row prints none; blank where the table has no "*" column, and in
            # every year whose PDF prints no "*" footnote (FY2020 on).
            rec["review_not_completed"] = "1" if "asterisk" in rec["row_flags"] else \
                "0" if star_col and "star_text" not in rec["row_flags"] else ""
        if has_conduit:
            # A row that prints a fiscal conduit is flagged and is a warn review item; the FC EIN
            # counts in the anchor census.
            fe = rec["fiscal_conduit_ein_printed"]
            rec["fiscal_conduit_ein"] = fe.replace("-", "") if EIN_RE.match(fe) else ""
            note = next((n for n in s.get("conduit_notes", []) if n["page"] == rec["pdf_page"]
                         and n["printed"] == rec["fiscal_conduit"]), None)
            if note is not None:
                # Text in the conduit column that is not a conduit (FY2018 p.271: "Please
                # indicate the actuals schools.", a drafting note; config `conduit_notes`):
                # fiscal_conduit blank, the printed text kept in fiscal_conduit_raw, flagged.
                printed = rec["fiscal_conduit"]
                rec["fiscal_conduit"] = ""
                rec["row_flags"].append("conduit_note")
                flag("W.fiscal_conduit", "warn", rec["pdf_page"], f"the conduit column prints "
                     f"{printed!r}: {note['note']}; fiscal_conduit left blank, the text kept in "
                     "fiscal_conduit_raw", award_id=rec["award_id"],
                     table_index=rec["table_index"], row_index=rec["row_index"], field="conduit",
                     dollar_impact=0)
            elif rec["fiscal_conduit"] or fe:
                rec["row_flags"].append("fiscal_conduit")
                if not (rec["fiscal_conduit"] and rec["fiscal_conduit_ein"]):
                    # A conduit with a well-formed EIN is stored and is no review item (it was one
                    # while the review file was its only home, before #222); one with no EIN, or
                    # an FC EIN that is not an EIN (p.242 "13-281380"), still is.
                    kept = ("kept in fiscal_conduit; fiscal_conduit_ein blank (no EIN printed)"
                            if not fe else f"kept in fiscal_conduit; the FC EIN as printed is not "
                            "an EIN, so fiscal_conduit_ein is blank (fiscal_conduit_ein_printed "
                            "keeps it)")
                    flag("W.fiscal_conduit", "warn", rec["pdf_page"], f"fiscal conduit printed: "
                         f"{rec['fiscal_conduit']!r}, FC EIN {' '.join(fe.split())!r}; {kept}",
                         award_id=rec["award_id"], table_index=rec["table_index"],
                         row_index=rec["row_index"], field="conduit", dollar_impact=0)
        rec["ein_printed"] = rec.pop("ein_raw").strip()
        rec["amount_printed"] = " ".join(rec.pop("amount_raw").split())
        if "empty_row" in rec["row_flags"]:
            rec["ein"], rec["amount"] = "", None
            continue
        e = rec["ein_printed"]
        rec["ein"] = e.replace("-", "") if EIN_RE.match(e) else ""
        if not rec["ein"]:
            # One narrow, stated rule: an EIN cell whose only other line is a lone "-" (the
            # trailing hyphen of the organisation text overflowing the column rule; FY2027
            # p.463) reads as the EIN line. Flagged, so a person confirms it.
            lines = [ln.strip() for ln in e.split("\n") if ln.strip()]
            digits = [ln for ln in lines if EIN_RE.match(ln)]
            if len(digits) == 1 and all(ln == "-" for ln in lines if ln != digits[0]):
                rec["ein"] = digits[0].replace("-", "")
                rec["row_flags"].append("ein_overflow_hyphen")
        if not rec["ein"]:
            rec["row_flags"].append("ein_unreadable")
        rec["amount"] = parse_amount(rec["amount_printed"])
        if rec["amount"] is None and cfg["structure"].get("amount_without_dollar") and \
                re.fullmatch(r"\d{1,3}(?:,\d{3})*", rec["amount_printed"]):
            # Printed without its "$" (FY2026 p.111, Ghetto Film School "75,000"). Read as the
            # number printed; flagged, so a person confirms it.
            rec["amount"] = int(rec["amount_printed"].replace(",", ""))
            # `bare_amounts` (FY2020): tables with a Council Member, Borough or Sponsor column
            # (the member tables and the appendices) print every amount with no "$" (p.13
            # "5,500"); a routine flag there, a review item anywhere else.
            bare = cfg["structure"].get("bare_amounts") and \
                {"member", "delegation", "sponsor"} & set(rec["header"].split(" | "))
            rec["row_flags"].append("amount_bare" if bare else "amount_no_dollar")
        if rec["amount"] is None and cfg["structure"].get("amount_cents") and \
                re.fullmatch(r"\$\d{1,3}(?:,\d{3})*\.00", rec["amount_printed"]) and \
                {"member", "delegation", "sponsor"} & set(rec["header"].split(" | ")):
            # `amount_cents` (FY2018): Appendix A prints every amount with zero cents
            # ("$30,000.00", p.131). Read as the whole dollars printed; a routine flag there.
            rec["amount"] = int(rec["amount_printed"][1:].split(".")[0].replace(",", ""))
            rec["row_flags"].append("amount_cents")
        if rec["amount"] is None and cfg["structure"].get("amount_odd_format") and \
                re.fullmatch(r"\$\d{1,3}(?:,\d{3})*(?:\.00|\.)", rec["amount_printed"]):
            # Printed with zero cents or a trailing period (FY2025 p.168 "$77,000.00", p.170
            # "$50,000."). Read as the whole dollars printed; flagged, so a person confirms it.
            rec["amount"] = int(rec["amount_printed"][1:].split(".")[0].replace(",", ""))
            rec["row_flags"].append("amount_odd_format")
        if rec["amount"] is None:
            rec["row_flags"].append("amount_unreadable")

    for ini in initiatives:
        ini["rows_sum"] = sum(a["amount"] or 0 for a in awards
                              if a["initiative_id"] == ini["initiative_id"])
    _link_subawards(subawards, awards, cfg, flag)
    return dict(initiatives=initiatives, summary=summary, awards=awards, flags=flags,
                subawards=subawards,
                side_tables=side_tables, table_totals=table_totals,
                last_cols=last_cols, header_rows=header_rows,
                band_words=band_words, covered=covered)
