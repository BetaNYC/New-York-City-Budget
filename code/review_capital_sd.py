"""
Section 254 capital supporting detail: parse, tie out and review (epic #101; FY2027 #102,
FY2026 #103, FY2025 #104, FY2024 #105, FY2023 #106).

One parser, one config per year: config/capital_sd/fyNNNN.toml holds the PDF, its sha256, the
page map, the FY columns and the other year-specific facts. FY2027 (the default) is
source/FY27/Supporting-Detail-for-FY2027-...-Section-254.V4.pdf (80 pages, Parts I and II
rotated /Rotate 90); FY2026 is source/FY26/Fiscal-2026-Capital-Budget-Supporting-Details-1.pdf
(86 pages, Part III rotated instead); FY2025 is source/FY25/Supporting-Detail-for-FY2025-...-
Council-Version-24.07.17.pdf (87 pages, all Parts upright, Part III a third export); FY2024 is
source/FY24/FY2024-Sec254-Supporting-Detail-Book_7.10.2023pwp-2.pdf (78 pages, encrypted with an
empty user password); FY2023 is source/FY23/FY23-Sec254-Capital-Supporting-Detail-Book.pdf (89 pages,
the City seal on its cover). Rules a later
year needed and an earlier one must not get are config switches, off by default, so a reviewed
year's output stays byte-identical.

This is a review build, not a served dataset (DATA-ANOMALIES §27: PDF data is not served in
2.0). It writes to the config's research/ folder and never touches data/.

Why it is not the Schedule C pipeline: the book has no cell borders. Parts I and II are a Word
table printed without rules, so there is no vector lattice and no image lattice to read
(families/capital.md §6). Each row is instead read twice, independently:

  * geometry  -- a row starts at its SUB ID line. Lines in the title column are grouped into
                 blocks by their spacing, and the blocks are paired with the rows in page order.
                 Every other word belongs to the row band that holds its centre.
  * stream    -- Word writes a table row by row, so in the content stream every word follows
                 its own row's SUB ID. A word's stream row is the last SUB ID emitted before it.

The two reads must agree on every word. A title printed above its own SUB ID line (p.40:
`HD CC1047` FIRST ATLANTIC TERMINAL) is where a line-by-line reader goes wrong.

Checks (each prints its numbers to checks.txt; failures go to review.csv):
  C1 every `TOTALS FOR` line: project count and all four FY sums, rows since the last total
  C2 `TOTALS FOR ALL` per Part; summary-page additions = Part I first FY; additions -
     rescindments = net
  C3 Part II rows are Part I rows (every field)
  C4 Part III: each organization's $ line = its budget-line rows; the grand total; Part III by
     budget line = Part II by budget line
  C5 geometry read == stream read, word by word
  C6 every non-furniture word on a detail page lands in exactly one field (no orphans)
  C7 image rules (code/ocr/grid.py rule_masks at 300 dpi) == vector rules, every page
  C8 ink coverage: rendered ink not under an emitted character or a vector rule
  C9 alignment with data/capital/council_capital_awards.csv (report only, never fills a value)

Run:  .venv/bin/python code/review_capital_sd.py [--fy 2027|2026|2025|2024|2023] [--out DIR] [--no-ink] [--selftest-ink]
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import re
import sys
import tomllib
import unicodedata

import pdfplumber

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

AWARDS = os.path.join(REPO, "data/capital/council_capital_awards.csv")
CONFIG_DIR = os.path.join(REPO, "config", "capital_sd")

X_TOL = 1.5               # pdfplumber x_tolerance; the prototype's value (families/capital.md §3.1)
LINE_TOL = 1.5            # words whose tops differ by less than this are one printed line
BLOCK_GAP = 12.0          # pt between line tops: below = same cell (leading ~9.6), above = new
                          # cell (>= 14.4 measured). Re-measured in checks.txt every run.
AMOUNT_X1_TOL = 3.0       # an amount is right-aligned to its FY header's right edge
NEAR_TOL = 6.0            # a word outside every row band may join the nearest band within this
AMOUNT_RE = re.compile(r"^-?\$?[\d,]+$|^\$?\([\d,]+\)$")   # FY2026 Part III: "(183,000)"
SUB_CODE_RE = re.compile(r"^[A-Z]{1,3}$")
SUB_ID_RE = re.compile(r"^[A-Z]{2}\d{3,5}$")
CID_TAB = "(cid:9)"
CODE_RE = re.compile(r"\b([BS]):(?:[BS]:)?\s?([A-Z]\d{3}[A-Z]?)\b")   # "B:B:Q156" printed too


def configure(fy):
    """Load config/capital_sd/fy<fy>.toml and set the module's per-year globals.

    PAGE_MAP is checked against the page furniture in triage() (a page that disagrees fails).
    EXPORT_FONTS: the Word export's fonts on detail pages; text in any other font was typed in
    later. Every other year-specific value is read from CFG where it is used."""
    global CFG, FY, TAG, PREFIX, PDF, PDF_SHA256, OUT, PAGE_MAP, FYS, EXPORT_FONTS, BOLD_FONTS
    with open(os.path.join(CONFIG_DIR, f"fy{fy}.toml"), "rb") as f:
        CFG = tomllib.load(f)
    FY = CFG["fiscal_year"]
    TAG = f"fy{FY}"
    PREFIX = CFG["prefix"]
    PDF = os.path.join(REPO, CFG["pdf"])
    PDF_SHA256 = CFG["sha256"]
    OUT = os.path.join(REPO, CFG["review_dir"])
    PAGE_MAP = {p: kind for kind, ranges in CFG["pages"].items()
                for a, b in ranges for p in range(a, b + 1)}
    FYS = tuple(CFG["fys"])
    EXPORT_FONTS = tuple(CFG["export_fonts"])
    # Bold faces whose names do not say "Bold" (FY2025 Part III: CIDFont+F1). Default none.
    BOLD_FONTS = frozenset(CFG.get("bold_fonts", ()))


def pages_of(kind):
    return sorted(p for p, k in PAGE_MAP.items() if k == kind)


configure(2027)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def money(s):
    """Printed amount -> int. `$` and thousands commas only; a leading minus or accounting
    parentheses (`$(183,000)`) make it negative."""
    v = s.replace("$", "").replace(",", "")
    return -int(v[1:-1]) if v.startswith("(") else int(v)


def page_words(page):
    """Words with font, size and the stream index of their first character (`si`)."""
    chars = page.chars
    for i, c in enumerate(chars):
        c["_si"] = i
    words = pdfplumber.utils.extract_words(chars, return_chars=True, x_tolerance=X_TOL,
                                           extra_attrs=["fontname", "size"])
    for k, w in enumerate(words):
        w["si"] = min(c["_si"] for c in w["chars"])
        w["wid"] = k
        w["bold"] = "Bold" in w["fontname"] or w["fontname"] in BOLD_FONTS
        w["cy"] = (w["top"] + w["bottom"]) / 2
    return words


def group_lines(words):
    """Cluster words into printed lines by `top`. Returns lists sorted top to bottom."""
    lines = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if lines and abs(w["top"] - lines[-1][0]["top"]) < LINE_TOL:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [sorted(l, key=lambda w: w["x0"]) for l in lines]


def bbox_of(ws):
    """`x0,top,x1,bottom` of some words, in pdfplumber's (display) coordinates."""
    return (f"{min(w['x0'] for w in ws):.2f},{min(w['top'] for w in ws):.2f},"
            f"{max(w['x1'] for w in ws):.2f},{max(w['bottom'] for w in ws):.2f}")


def line_text(ws):
    """Words left to right, one space apart. With `join_touching_words`, words that touch
    (gap under 0.5 pt) were split only because the font changed mid-word, so they join with no
    space (FY2025 p.51: an edit typed `SCHULMAN` with its `C` in another font subset). Off by
    default: on, FY2026/FY2027 `sponsor_raw` would lose the space in `GENNARO ,` (4 rows)."""
    if not CFG.get("join_touching_words"):
        return " ".join(w["text"] for w in sorted(ws, key=lambda w: w["x0"]))
    out, prev = "", None
    for w in sorted(ws, key=lambda w: w["x0"]):
        if prev is not None:
            out += "" if w["x0"] - prev["x1"] < 0.5 and abs(w["top"] - prev["top"]) < LINE_TOL else " "
        out += w["text"]
        prev = w
    return out


def rid(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:12]


class Review:
    """review.csv rows (PLAN.md §5.3 shape, trimmed to what this book has)."""

    COLS = ["review_id", "check_id", "severity", "pdf_page", "part", "sub_id", "budget_line",
            "field", "dollars", "expected", "observed", "note"]

    def __init__(self, tag=None):
        self.rows = []
        self.tag = tag            # review_id salt; default: this module's configured year

    def add(self, check_id, severity, page, note, part="", sub_id="", budget_line="",
            field="", dollars=0, expected="", observed=""):
        self.rows.append({"review_id": rid(self.tag or TAG, check_id, page, sub_id, field, note),
                          "check_id": check_id, "severity": severity, "pdf_page": page,
                          "part": part, "sub_id": sub_id, "budget_line": budget_line,
                          "field": field, "dollars": dollars, "expected": expected,
                          "observed": observed, "note": note})


# --------------------------------------------------------------------------------------------
# Stage 0: triage
# --------------------------------------------------------------------------------------------

def triage(pdf):
    out = []
    for n, p in enumerate(pdf.pages, 1):
        text = p.extract_text() or ""
        label = re.search(r"Page (\d+) of (\d+)", text)
        first = text.strip().splitlines()[0] if text.strip() else ""
        out.append({"pdf_page": n, "kind": PAGE_MAP.get(n, "UNMAPPED"), "rotate": p.rotation,
                    "width": round(float(p.width)), "height": round(float(p.height)),
                    "chars": len(p.chars), "rects": len(p.rects), "lines": len(p.lines),
                    "curves": len(p.curves), "images": len(p.images),
                    "printed_label": label.group(0) if label else "", "first_line": first[:60]})
    return out


def check_page_map(pages, review):
    """H3: the furniture on each page must agree with PAGE_MAP."""
    expect_first = {"part1": "I.", "part2": "II.", "part3": None}
    bad = 0
    for pg in pages:
        k = pg["kind"]
        ok = True
        if k == "UNMAPPED":
            ok = False
        elif k in ("part1", "part2"):
            ok = pg["first_line"] == expect_first[k] and pg["rotate"] == CFG["rotate"][k] and \
                pg["printed_label"] != ""
        elif k == "part3":
            ok = pg["rotate"] == CFG["rotate"][k] and pg["printed_label"] != ""
        if not ok:
            bad += 1
            review.add("H3.page_map", "critical", pg["pdf_page"],
                       f"page furniture does not match the page map ({k})")
    return bad


# --------------------------------------------------------------------------------------------
# Parts I and II: the detail table
# --------------------------------------------------------------------------------------------

def header_columns(lines):
    """Column geometry from this page's header line (SUB ID ... SPONSOR; FY2025 prints
    PROJECT ID ... SPONSOR, so `PROJECT` names both the ID and the title column)."""
    for ln in lines:
        texts = [w["text"] for w in ln]
        if ("SUB" in texts or texts[:2] == ["PROJECT", "ID"]) and "SPONSOR" in texts:
            by = {w["text"]: w for w in ln}        # the last PROJECT is the title's
            if "SUB" not in by:
                by["SUB"] = ln[0]
            fy_x1 = []
            for i, w in enumerate(ln):
                if w["text"] == "FY" and i + 1 < len(ln) and re.fullmatch(r"20\d\d", ln[i + 1]["text"]):
                    fy_x1.append(ln[i + 1]["x1"])
            assert len(fy_x1) == 4, f"header FY columns: {fy_x1}"
            fy_x0 = min(w["x0"] for w in ln if w["text"] == "FY")
            return {"top": ln[0]["top"], "fy_x0": fy_x0, "bottom": max(w["bottom"] for w in ln),
                    "sub": by["SUB"]["x0"], "budget": by["BUDGET"]["x0"],
                    "boro": by["BORO"]["x0"], "title": by["PROJECT"]["x0"],
                    "fy_x1": fy_x1, "sponsor": by["SPONSOR"]["x0"]}
    return None


def column_of(w, cols):
    """Which field a word sits in, by geometry only."""
    if AMOUNT_RE.match(w["text"]):
        for k, x1 in enumerate(cols["fy_x1"]):
            if abs(w["x1"] - x1) <= AMOUNT_X1_TOL:
                return FYS[k]
    x0 = w["x0"]
    # Titles end left of the FY 2027 header (widest seen ~375 pt). A non-amount word right of
    # it is sponsor text, even when it starts inside an amount column (p.56 PV CC0989).
    if x0 >= cols["sponsor"] - 2 or x0 >= cols["fy_x0"]:
        return "sponsor"
    if x0 >= cols["title"] - 2:
        return "title"
    if x0 >= cols["boro"] - 2:
        return "boro"
    if x0 >= cols["budget"] - 2:
        return "budget_line"
    if x0 >= cols["sub"] - 2:
        return "sub_id"
    return "unknown"


def classify_line(ln, cols):
    texts = [w["text"] for w in ln]
    if texts[:2] == ["TOTALS", "FOR"]:
        return "total"
    if re.fullmatch(r"Page \d+ of \d+", " ".join(texts)):
        return "footer"
    first = [w for w in ln if column_of(w, cols) == "sub_id"]
    if len(first) >= 2 and SUB_CODE_RE.match(first[0]["text"]) and SUB_ID_RE.match(first[1]["text"]):
        return "anchor"
    if all(w["bold"] for w in ln) and not any(AMOUNT_RE.match(t) for t in texts):
        return "heading"
    return "content"


def parse_total(ln, cols, page, review, part):
    text = line_text([w for w in ln if column_of(w, cols) not in FYS])
    m = re.fullmatch(r"TOTALS FOR (.+?)\s*\(([\d,]+) PROJECTS?\)", text)
    amounts = {fy: None for fy in FYS}
    for w in ln:
        c = column_of(w, cols)
        if c in FYS:
            amounts[c] = money(w["text"])
    if not m or any(v is None for v in amounts.values()):
        review.add("C1.total_line", "critical", page, f"unreadable totals line: {line_text(ln)}",
                   part=part)
        return None
    return {"part": part, "pdf_page": page, "name": m.group(1).strip(),
            "printed_count": int(m.group(2).replace(",", "")),
            **{f"printed_{fy}": amounts[fy] for fy in FYS},
            "printed_text": line_text(ln), "top": ln[0]["top"]}


def blocks_of(lines, field, cols):
    """Group the lines that carry `field` words into cell blocks by line spacing."""
    tagged = []
    for ln in lines:
        ws = [w for w in ln if column_of(w, cols) == field]
        if ws:
            tagged.append(ws)
    blocks = []
    for ws in tagged:
        if blocks and ws[0]["top"] - blocks[-1][-1][0]["top"] < BLOCK_GAP:
            blocks[-1].append(ws)
        else:
            blocks.append([ws])
    return blocks


def parse_detail_page(page, pno, part, state, review, gaps):
    """One Part I/II page. `state` carries the open agency across pages."""
    words = page_words(page)
    lines = group_lines(words)
    cols = header_columns(lines)
    if cols is None:
        review.add("H4.header", "critical", pno, "no SUB ID / SPONSOR header on a detail page",
                   part=part)
        return [], [], set(), words
    consumed = set()
    body = []
    for ln in lines:
        if ln[0]["bottom"] <= cols["bottom"] + 0.5:      # page title + column header
            consumed.update(w["wid"] for w in ln)
            continue
        kind = classify_line(ln, cols)
        if kind == "footer":
            consumed.update(w["wid"] for w in ln)
            continue
        body.append((kind, ln))

    # Split the body into segments at headings and totals; rows never cross them.
    segments, cur = [], []
    totals = []
    for kind, ln in body:
        if kind in ("heading", "total"):
            if cur:
                segments.append((state["agency"], cur))
            cur = []
            consumed.update(w["wid"] for w in ln)
            if kind == "heading":
                state["agency"] = line_text(ln)
            else:
                t = parse_total(ln, cols, pno, review, part)
                if t:
                    totals.append(t)
        else:
            cur.append((kind, ln))
    if cur:
        segments.append((state["agency"], cur))

    rows = []
    for agency, seg in segments:
        seg_lines = [ln for _, ln in seg]
        anchors = [ln for kind, ln in seg if kind == "anchor"]
        tblocks = blocks_of(seg_lines, "title", cols)
        # Record line gaps inside the title column, to keep BLOCK_GAP honest.
        tl = [ws[0]["top"] for ws in sum(([*b] for b in tblocks), [])]
        allt = sorted(ws[0]["top"] for ws in
                      ([w for w in ln if column_of(w, cols) == "title"] for ln in seg_lines) if ws)
        gaps.extend(round(b - a, 2) for a, b in zip(allt, allt[1:]))

        seg_rows = []
        for ln in anchors:
            byc = collections.defaultdict(list)
            for w in ln:
                byc[column_of(w, cols)].append(w)
            sub = byc["sub_id"]
            row = {"part": part, "agency": agency, "pdf_page": pno,
                   "sub_id": " ".join(w["text"] for w in sub[:2]),
                   "anchor_top": ln[0]["top"], "anchor_bottom": max(w["bottom"] for w in ln),
                   "anchor_si": min(w["si"] for w in sub[:2]),
                   "words": {}, "flags": []}
            for w in sub[:2]:
                row["words"][w["wid"]] = "sub_id"
            for w in sub[2:]:
                row["words"][w["wid"]] = "sub_id"
                row["flags"].append("extra_sub_id_word")
            seg_rows.append(row)
        if not seg_rows:
            for ln in seg_lines:
                review.add("C6.orphan", "critical", pno,
                           f"content with no row in segment: {line_text(ln)}", part=part)
            continue

        # Geometry read. Title blocks pair with rows in order.
        paired = len(tblocks) == len(seg_rows)
        if not paired:
            review.add("C5.title_blocks", "critical", pno,
                       f"{len(tblocks)} title blocks for {len(seg_rows)} rows in {agency}",
                       part=part, sub_id=seg_rows[0]["sub_id"])
        bands = []
        for i, row in enumerate(seg_rows):
            top, bot = row["anchor_top"], row["anchor_bottom"]
            if paired:
                b = tblocks[i]
                btop = b[0][0]["top"]
                bbot = max(w["bottom"] for w in b[-1])
                if not (btop - BLOCK_GAP <= row["anchor_top"] <= bbot + BLOCK_GAP):
                    review.add("C5.title_far", "critical", pno,
                               "title block is not next to its SUB ID line", part=part,
                               sub_id=row["sub_id"])
                top, bot = min(top, btop), max(bot, bbot)
            bands.append((top, bot))

        geom = {}
        for ln in seg_lines:
            for w in ln:
                hits = [i for i, (t, b) in enumerate(bands) if t - 0.5 <= w["cy"] <= b + 0.5]
                if len(hits) == 1:
                    geom[w["wid"]] = hits[0]
                    continue
                dist = sorted((min(abs(w["cy"] - t), abs(w["cy"] - b)), i)
                              for i, (t, b) in enumerate(bands))
                if dist and dist[0][0] <= NEAR_TOL and (len(dist) == 1 or dist[1][0] > dist[0][0] + 1):
                    geom[w["wid"]] = dist[0][1]
                    seg_rows[dist[0][1]]["flags"].append("geom_near")
                else:
                    geom[w["wid"]] = None

        # A sponsor cell can wrap past its row's band (FY2025 p.50 `HN CN017`: three lines). A
        # sponsor-column line in no band joins the row of the sponsor line just above it when the
        # gap is a within-cell gap (< BLOCK_GAP), as wrapped title lines do.
        prev = None                       # (top, row) of the last sponsor line placed in a row
        for ln in seg_lines:
            sp = [w for w in ln if column_of(w, cols) == "sponsor"]
            if not sp:
                continue
            ks = {geom[w["wid"]] for w in sp}
            if ks == {None} and prev and sp[0]["top"] - prev[0] < BLOCK_GAP:
                for w in sp:
                    geom[w["wid"]] = prev[1]
                seg_rows[prev[1]]["flags"].append("sponsor_wrapped_below")
                ks = {prev[1]}
            known = ks - {None}
            prev = (sp[0]["top"], next(iter(known))) if len(known) == 1 else None

        # Stream read: the last SUB ID emitted before the word.
        order = sorted(range(len(seg_rows)), key=lambda i: seg_rows[i]["anchor_si"])
        def stream_row(w):
            best = None
            for i in order:
                if seg_rows[i]["anchor_si"] <= w["si"]:
                    best = i
            return best

        for ln in seg_lines:
            for w in ln:
                g, s = geom[w["wid"]], stream_row(w)
                c = column_of(w, cols)
                if g is None and s is None:
                    review.add("C6.orphan", "critical", pno, f"word in no row: {w['text']}",
                               part=part)
                    continue
                if g != s:
                    gr = seg_rows[g]["sub_id"] if g is not None else "-"
                    sr = seg_rows[s]["sub_id"] if s is not None else "-"
                    # A stream row far from the word means the stream left row order here
                    # (later edits are written at the end of the page). That is no second
                    # opinion on the word, so it is counted, not flagged. A stream row next to
                    # the word is a real disagreement between two plausible rows.
                    near = s is not None and \
                        bands[s][0] - 2 * BLOCK_GAP <= w["cy"] <= bands[s][1] + 2 * BLOCK_GAP
                    if near or g is None:
                        review.add("C5.geom_vs_stream", "critical", pno,
                                   f"'{w['text']}' ({c}): geometry says {gr}, stream says {sr}",
                                   part=part, sub_id=gr, field=c)
                    else:
                        state.setdefault("stream_out_of_order", collections.Counter())[pno] += 1
                else:
                    state.setdefault("stream_agree", collections.Counter())[pno] += 1
                k = g if g is not None else s
                seg_rows[k]["words"][w["wid"]] = c
        wmap = {w["wid"]: w for ln in seg_lines for w in ln}
        for row in seg_rows:
            finish_row(row, wmap, pno, part, review)
            consumed.update(row["words"])
        rows.extend(seg_rows)
    return rows, totals, consumed, words


def finish_row(row, wmap, pno, part, review):
    by = collections.defaultdict(list)
    for wid, c in row["words"].items():
        by[c].append(wmap[wid])

    def text_of(field, raw=False):
        ws = sorted(by[field], key=lambda w: (round(w["top"]), w["x0"]))
        lines = group_lines(ws)
        return ("\n" if raw else " ").join(line_text(l) for l in lines)

    row["budget_line"] = text_of("budget_line")
    row["boro"] = text_of("boro")
    row["title_raw"] = text_of("title", raw=True)
    row["sponsor_raw"] = text_of("sponsor", raw=True)
    codes = CODE_RE.findall(row["title_raw"])
    row["building_code"] = ";".join(v for k, v in codes if k == "B")
    row["school_code"] = ";".join(v for k, v in codes if k == "S")
    # FY2026 has a tab glyph with no Unicode mapping between the B: and S: codes (pp.35-41):
    # pdfplumber gives it as "(cid:9)". It is kept in title_raw and read as a space in title.
    row["title"] = re.sub(r"\s+", " ", CODE_RE.sub("", row["title_raw"].replace("\n", " ")
                                                   .replace(CID_TAB, " "))).strip()
    # Clean rules (listed, counted): line breaks -> space; whitespace collapsed; a space before
    # a comma removed (the post-export edits print "BANKS , LOUIS"); "(cid:9)" -> space.
    sp = re.sub(r"\s+", " ", row["sponsor_raw"].replace("\n", " ")).strip()
    row["sponsor"] = re.sub(r" ,", ",", sp)
    rules = []
    if "\n" in row["title_raw"] or "\n" in row["sponsor_raw"]:
        rules.append("line_join")
    if row["sponsor"] != sp:
        rules.append("space_before_comma")
    if codes:
        rules.append("bs_codes_split")
    if CID_TAB in row["title_raw"]:
        rules.append("cid_tab")
    row["clean_rules_applied"] = ";".join(rules)
    fonts = collections.Counter(wmap[w]["fontname"] for w in row["words"])
    row["fonts"] = ";".join(sorted(fonts))
    edited = [wmap[w] for w in row["words"] if not wmap[w]["fontname"].startswith(EXPORT_FONTS)]
    row["edited_text"] = " ".join(w["text"] for w in sorted(edited, key=lambda w: (w["top"], w["x0"])))
    if edited:
        row["flags"].append("edited_after_export")
    for fy in FYS:
        vals = by[fy]
        if len(vals) != 1:
            row[f"{fy}_printed"] = ";".join(w["text"] for w in vals)
            row[fy] = None
            review.add("C6.amount_cells", "critical", pno,
                       f"{len(vals)} values in {fy}", part=part, sub_id=row["sub_id"], field=fy)
        else:
            row[f"{fy}_printed"] = vals[0]["text"]
            row[fy] = money(vals[0]["text"])
            if vals[0]["top"] - row["anchor_top"] > LINE_TOL:
                row["flags"].append(f"{fy}_wrapped_below")
    if not re.fullmatch(r"[A-Z]{1,3} [A-Z0-9]{3,6}", row["budget_line"]):
        review.add("C6.budget_line", "warn", pno, f"budget line shape: '{row['budget_line']}'",
                   part=part, sub_id=row["sub_id"], field="budget_line")
    if not re.fullmatch(r"[A-Z]", row["boro"]):
        review.add("C6.boro", "critical", pno, f"borough shape: '{row['boro']}'", part=part,
                   sub_id=row["sub_id"], field="boro")
    if re.search(r"\d", row["sponsor"]):
        review.add("C6.sponsor_digit", "critical", pno,
                   f"sponsor cell holds a number: '{row['sponsor']}' (as printed)", part=part,
                   sub_id=row["sub_id"], field="sponsor")
    if not row["title"]:
        review.add("C6.title_empty", "critical", pno, "empty title", part=part,
                   sub_id=row["sub_id"], field="title")
    ys = [wmap[w]["top"] for w in row["words"]]
    xs0 = [wmap[w]["x0"] for w in row["words"]]
    xs1 = [wmap[w]["x1"] for w in row["words"]]
    ys1 = [wmap[w]["bottom"] for w in row["words"]]
    row["bbox_pt"] = f"{min(xs0):.2f},{min(ys):.2f},{max(xs1):.2f},{max(ys1):.2f}"


# --------------------------------------------------------------------------------------------
# Part III: by non-city entity
# --------------------------------------------------------------------------------------------

def parse_part3_page(page, pno, state, review):
    """Organization header lines (bold, $ amounts) followed by budget-line rows."""
    words = page_words(page)
    lines = group_lines(words)
    hdr = None
    for ln in lines:
        t = [w["text"] for w in ln]
        if "ORGANIZATION" in t and "BUDGET" in t:
            by = {w["text"]: w for w in ln}
            fy_x1 = [ln[i + 1]["x1"] for i, w in enumerate(ln)
                     if w["text"] == "FY" and i + 1 < len(ln)]
            hdr = {"bottom": max(w["bottom"] for w in ln), "budget": by["BUDGET"]["x0"],
                   "fy_x1": fy_x1}
    if hdr is None or len(hdr["fy_x1"]) != 4:
        review.add("H4.header", "critical", pno, "Part III header not found", part="III")
        return [], [], set(), words
    consumed = set()
    lines_out, grand = [], []

    # FY2025 Part III sets its amounts up to ~5 pt left of the header's right edge.
    tol = CFG.get("part3_amount_x1_tol", AMOUNT_X1_TOL)

    def amounts(ln):
        got = {}
        for w in ln:
            if AMOUNT_RE.match(w["text"]):
                for k, x1 in enumerate(hdr["fy_x1"]):
                    if abs(w["x1"] - x1) <= tol:
                        got[FYS[k]] = w
        return got

    for ln in lines:
        if ln[0]["bottom"] <= hdr["bottom"] + 0.5 or \
                re.fullmatch(r"Page \d+ of \d+", line_text(ln)):
            consumed.update(w["wid"] for w in ln)
            continue
        am = amounts(ln)
        rest = [w for w in ln if w not in am.values()]
        text = line_text(rest)
        if text.startswith("TOTAL NON-CITY PROJECT ALLOCATIONS"):
            grand.append({fy: money(am[fy]["text"]) for fy in FYS})
            consumed.update(w["wid"] for w in ln)
            continue
        if rest and all(w["bold"] for w in rest) and rest[0]["x0"] < hdr["budget"] - 20:
            # An organization line (may wrap: a bold line with no amounts continues the name).
            if am and len(am) == 4:
                if state.get("pending_name"):
                    text = state.pop("pending_name") + " " + text
                state["org"] = {"pdf_page": pno, "organization": text, "bbox_pt": bbox_of(ln),
                                **{f"org_{fy}": money(am[fy]["text"]) for fy in FYS},
                                "lines": []}
                state["orgs"].append(state["org"])
            elif not am:
                state["pending_name"] = (state.get("pending_name", "") + " " + text).strip()
            else:
                review.add("C4.org_line", "critical", pno, f"org line with {len(am)} amounts: {text}",
                           part="III")
            consumed.update(w["wid"] for w in ln)
            continue
        if len(am) == 4 and re.fullmatch(r"[A-Z]{1,3} [A-Z0-9]{3,6}", text) and \
                rest[0]["x0"] >= hdr["budget"] - 5:
            if state.get("org") is None:
                review.add("C4.orphan", "critical", pno, f"budget line before any org: {text}",
                           part="III")
                continue
            state["org"]["lines"].append({"pdf_page": pno, "budget_line": text,
                                          "bbox_pt": bbox_of(ln),
                                          **{fy: money(am[fy]["text"]) for fy in FYS},
                                          "top": ln[0]["top"]})
            consumed.update(w["wid"] for w in ln)
            continue
        review.add("C6.orphan", "critical", pno, f"Part III line not understood: {line_text(ln)}",
                   part="III")
    return lines_out, grand, consumed, words


# --------------------------------------------------------------------------------------------
# Image rules vs vector rules (C7) and ink coverage (C8)
# --------------------------------------------------------------------------------------------

DPI = 300
SCALE = DPI / 72.0


def render_gray(pdf_path, pno):
    import numpy as np
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf_path)
    try:
        arr = doc[pno - 1].render(scale=SCALE, grayscale=True).to_numpy()
    finally:
        doc.close()
    if arr.ndim == 3:
        arr = arr[:, :, 0]
    return np.ascontiguousarray(arr)


def vector_rules(page):
    """Horizontal rules drawn as thin filled rects or lines: their y centres in pt."""
    ys = []
    for r in list(page.rects) + list(page.lines):
        h = r["bottom"] - r["top"]
        w = r["x1"] - r["x0"]
        if h <= 2.5 and w >= 100:
            ys.append(((r["top"] + r["bottom"]) / 2, r["x0"], r["x1"], h))
    return sorted(ys)


def image_rules(gray):
    """Horizontal rules from pixels with Christian's grid.py (kernel_px=60, PLAN §3 stage 4)."""
    import numpy as np
    from ocr import grid
    ink = grid.binarize(gray)
    horiz, _ = grid.rule_masks(ink, kernel_px=60)
    comps = grid._rule_components(horiz, axis=0)
    # Rules of at least 100 pt; glyph runs are far shorter than that.
    return sorted(c["pos"] / SCALE for c in comps if c["length"] >= 100 * SCALE)


def compare_rules(vec, img, tol=1.5):
    """Pair vector and image rules by y; return (matched, vector_only, image_only)."""
    vy = [v[0] for v in vec]
    used = set()
    matched, vonly = 0, []
    for y in vy:
        best = min(((abs(y - iy), j) for j, iy in enumerate(img) if j not in used), default=None)
        if best and best[0] <= tol:
            used.add(best[1])
            matched += 1
        else:
            vonly.append(round(y, 2))
    ionly = [round(iy, 2) for j, iy in enumerate(img) if j not in used]
    return matched, vonly, ionly


def ink_regions(gray, words, consumed, page, pad_px=4, min_ink_px=30, images=False):
    """Ink not covered by an emitted character's box or a vector rule/fill.

    A re-targeted, simplified take on exec-orders `vlm_ocr.ink_coverage` (PLAN §3 stage 6):
    on a born-digital page every inked pixel should be explained by a character we emitted
    or by a drawn rule. Characters of words we did not emit are left uncovered on purpose,
    so a dropped word shows up as ink.
    """
    import numpy as np
    from ocr import grid
    import cv2
    ink = grid.binarize(gray) > 0
    cover = np.zeros_like(ink, dtype=bool)
    H, W = ink.shape

    def box(x0, top, x1, bottom, pad):
        a = max(0, int(x0 * SCALE) - pad)
        b = min(W, int(x1 * SCALE) + pad + 1)
        c = max(0, int(top * SCALE) - pad)
        d = min(H, int(bottom * SCALE) + pad + 1)
        cover[c:d, a:b] = True

    for w in words:
        if w["wid"] in consumed:
            for ch in w["chars"]:
                # Bold capitals overshoot the font box: 14 pt titles by ~1.3 pt (pp.2, 3).
                pad = max(pad_px, int(0.12 * ch["size"] * SCALE))
                box(ch["x0"], ch["top"], ch["x1"], ch["bottom"], pad)
    # images=True: a picture's box counts as covered (config `ink_cover_image_pages`: FY2023
    # p.1 prints the City seal as two images). Only on the pages the config names.
    for im in (page.images if images else ()):
        box(im["x0"], im["top"], im["x1"], im["bottom"], pad_px)
    for r in list(page.rects) + list(page.lines) + list(page.curves):
        # pdfplumber gives a stroked line's centre line; its ink is linewidth thick.
        lw = float(r.get("linewidth") or 0) if r.get("stroke") else 0.0
        box(r["x0"], r["top"], r["x1"], r["bottom"], 2 + int(lw / 2 * SCALE + 0.5))
    left = (ink & ~cover).astype("uint8")
    n, _, stats, _ = cv2.connectedComponentsWithStats(left, connectivity=8)
    regions = []
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_ink_px:
            x, y, w, h = (int(stats[i, k]) for k in (0, 1, 2, 3))
            regions.append({"bbox_pt": [round(x / SCALE, 1), round(y / SCALE, 1),
                                        round((x + w) / SCALE, 1), round((y + h) / SCALE, 1)],
                            "ink_px": int(stats[i, cv2.CC_STAT_AREA])})
    return regions, int(ink.sum())


# --------------------------------------------------------------------------------------------
# Reconcile and align
# --------------------------------------------------------------------------------------------

def reconcile(rows, totals, review, report):
    """C1/C2: every TOTALS FOR line against the rows since the previous total in its Part."""
    ok = 0
    for part in ("I", "II"):
        prow = [r for r in rows if r["part"] == part]
        ptot = [t for t in totals if t["part"] == part]
        idx = 0
        since = []
        seq = sorted([("r", r["pdf_page"], r["anchor_top"], r) for r in prow] +
                     [("t", t["pdf_page"], t["top"], t) for t in ptot], key=lambda x: (x[1], x[2]))
        for kind, _, _, obj in seq:
            if kind == "r":
                since.append(obj)
                continue
            t = obj
            pool = prow if t["name"] == "ALL" else since
            got = {fy: sum((r[fy] or 0) for r in pool) for fy in FYS}
            n = len(pool)
            diffs = [fy for fy in FYS if got[fy] != t[f"printed_{fy}"]]
            status = "OK" if (n == t["printed_count"] and not diffs) else "FAIL"
            t.update({"rows": n, **{f"sum_{fy}": got[fy] for fy in FYS}, "status": status})
            report.append(f"  {part:>2} p.{t['pdf_page']:<3} {t['name'][:40]:<40} "
                          f"{n:>5}/{t['printed_count']:<5} {got[FYS[0]]:>13,}/"
                          f"{t['printed_' + FYS[0]]:<13,} {status}")
            if status == "OK":
                ok += 1
            else:
                review.add("C1.total", "critical", t["pdf_page"],
                           f"TOTALS FOR {t['name']}: rows {n} vs {t['printed_count']}; "
                           + ", ".join(f"{fy} {got[fy]:,} vs {t[f'printed_{fy}']:,}" for fy in diffs),
                           part=part, dollars=max([abs(got[fy] - t[f"printed_{fy}"]) for fy in FYS]),
                           expected=t["printed_" + FYS[0]], observed=got[FYS[0]])
            if t["name"] != "ALL":
                since = []
    return ok


def summary_page(pdf, review):
    """The summary page (FY2027 p.61): City Council Additions / Less Rescindments / Net Change."""
    text = pdf.pages[pages_of("summary")[0] - 1].extract_text()
    def grab(label):
        # FY2025 prints a space after the dollar sign: "($ 75,000,000)".
        m = re.search(label + r"\s+\(?\$\s?([\d,]+)\)?", text)
        return money(m.group(1)) if m else None
    return {"additions": grab("City Council Additions"),
            # FY2024 prints "Less: Rescindments ...".
            "rescindments": grab("Less:? Rescindments from Prior Capital Budgets"),
            "net": grab("Net Change")}


def wb_id(a):
    """The workbook's project ID without its agency prefix: FY2027 prints `CC0001`, FY2026
    `E CN0001`. The PDF's SUB ID is compared the same way (`sub_id.split(" ")[-1]`)."""
    return a["project_id"].split(" ")[-1]


def wb_text(s):
    """Undo the comparison source's mojibake, for comparing only (never written out). The
    FY2025 and FY2024 rows come from NYC Open Data t474-a92g, whose accents were decoded as
    cp437: FY2025 `OssΘ` is cp1252 `Ossé`, FY2024 `Oss├⌐` is UTF-8 `Ossé`. Config
    `workbook_mojibake = "cp1252"` / `"utf-8"` names the real encoding; default: no change."""
    enc = CFG.get("workbook_mojibake")
    if not enc or s.isascii():
        return s
    try:
        return s.encode("cp437").decode(enc)
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def awards_for_year():
    with open(AWARDS, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["report_year"] == str(FY)]
    if CFG.get("workbook_mojibake"):
        for r in rows:
            fixed = {k: wb_text(r[k]) for k in ("title", "sponsor")}
            r["_mojibake"] = [(r[k], fixed[k]) for k in fixed if fixed[k] != r[k]]
            r.update(fixed)
    return rows


def align_workbook(rows, review, report):
    """C9. The workbook drops the agency prefix from the ID (`CC0001`); compare on
    (ID number, budget line, FY, amount) for every non-zero amount, then explain the rest."""
    aw = awards_for_year()
    pdf_keys = collections.Counter()
    pdf_by = collections.defaultdict(list)
    for r in rows:
        if r["part"] != "I":
            continue
        pid = r["sub_id"].split(" ")[-1]
        for fy in FYS:
            v = r[fy]
            if v:
                k = (pid, r["budget_line"], fy[2:], v)
                pdf_keys[k] += 1
                pdf_by[k].append(r)
    # t474 records broken across rows keep their first row with no amount (row_flag
    # split_record_amount_unknown; data/capital/README.md). They cannot join on amount: each is
    # listed with the PDF row that has its ID and budget line. FY2022 and FY2023 have one each.
    aw_all = aw
    blank = [a for a in aw if a["amount"] == ""]
    aw = [a for a in aw if a["amount"] != ""]
    for a in blank:
        hits = [r for r in rows if r["part"] == "I" and r["sub_id"].split(" ")[-1] == wb_id(a)
                and r["budget_line"] == a["budget_line"]]
        got = "; ".join(f"{r['sub_id']} p.{r['pdf_page']} "
                        f"{', '.join(f'FY{fy[2:]} {r[fy]:,}' for fy in FYS if r[fy])}"
                        for r in hits) or "no PDF row"
        report.append(f"  workbook row with no amount ({a['row_flag'] or 'blank'}): {a['project_id']} "
                      f"{a['budget_line']} '{a['title']}' -> PDF: {got}")
        r = hits[0] if hits else None
        review.add("C9.workbook_no_amount", "warn", r["pdf_page"] if r else "",
                   f"the workbook row for {a['project_id']} on {a['budget_line']} has no amount "
                   f"({a['row_flag'] or 'blank'}; {a['source_row']}); the PDF prints {got}. "
                   "Not compared on amount", part="I", sub_id=r["sub_id"] if r else a["project_id"],
                   budget_line=a["budget_line"], dollars=(r[FYS[0]] or 0) if r else 0)
    wb_keys = collections.Counter()
    wb_by = collections.defaultdict(list)
    for a in aw:
        k = (wb_id(a), a["budget_line"], a["amount_fy"], int(a["amount"]))
        wb_keys[k] += 1
        wb_by[k].append(a)
    matched = sum((pdf_keys & wb_keys).values())
    pdf_only = pdf_keys - wb_keys
    wb_only = wb_keys - pdf_keys
    report.append(f"  PDF Part I non-zero amounts: {sum(pdf_keys.values())}; workbook FY{FY} rows: "
                  f"{sum(wb_keys.values())}; matched on (ID, budget line, FY, amount): {matched}; "
                  f"PDF only: {sum(pdf_only.values())}; workbook only: {sum(wb_only.values())}")
    for k, n in sorted(pdf_only.items()):
        r = pdf_by[k][0]
        review.add("C9.workbook", "warn", r["pdf_page"],
                   f"in the PDF, not in the workbook: {r['sub_id']} FY{k[2]} {k[3]:,}",
                   part="I", sub_id=r["sub_id"], budget_line=r["budget_line"], dollars=k[3])
    for k, n in sorted(wb_only.items()):
        a = wb_by[k][0]
        review.add("C9.workbook", "warn", "", f"in the workbook, not in the PDF: {k}",
                   part="I", sub_id=k[0], budget_line=k[1], dollars=k[3])
    # Text fields, for the matched rows: sponsor and borough (titles differ by design: the
    # workbook has title + description).
    wb_by_id = collections.defaultdict(list)
    for a in aw_all:
        wb_by_id[(wb_id(a), a["budget_line"])].append(a)
    boro_diff = 0
    for r in rows:
        if r["part"] != "I":
            continue
        cands = wb_by_id.get((r["sub_id"].split(" ")[-1], r["budget_line"]), [])
        if cands and all(c["borough"] != r["boro"] for c in cands):
            boro_diff += 1
            review.add("C9.workbook_boro", "warn", r["pdf_page"],
                       f"borough PDF {r['boro']} vs workbook "
                       f"{'/'.join(sorted({c['borough'] for c in cands}))}",
                       part="I", sub_id=r["sub_id"], budget_line=r["budget_line"], field="boro",
                       dollars=r[FYS[0]] or 0)
    report.append(f"  borough differs from the workbook on {boro_diff} Part I rows")

    # Title and sponsor, as an independent check of which row each wrapped line went to.
    # The workbook title carries the B:/S: codes, as the PDF prints them.
    def norm(s):
        # Accents folded: the post-export edits print FARIAS where the workbook has Farías.
        return re.sub(r"[^A-Z0-9]", "", unicodedata.normalize("NFKD", s.replace(CID_TAB, " ")).upper())

    def people(s):
        return sorted(p for p in (norm(x) for x in s.split(",")) if p)

    t_eq = s_eq = n = 0
    for r in rows:
        if r["part"] != "I":
            continue
        cands = wb_by_id.get((r["sub_id"].split(" ")[-1], r["budget_line"]), [])
        if not cands:
            continue
        n += 1
        # The PDF reuses some IDs on one budget line (FY2025 `HN CN018`, `HO CN019`, `E CN810`):
        # with `wb_pick_by_amount`, compare with the workbook row that has this row's amount.
        # Off by default, so FY2026/FY2027 output stays as reviewed (on, FY2026 `HN CN1451`
        # would lose 2 warnings: it would be compared with its own workbook row).
        a = cands[0]
        if CFG.get("wb_pick_by_amount"):
            a = next((c for c in cands if c["amount"] and
                      int(c["amount"]) == (r.get("fy" + c["amount_fy"]) or 0)), a)
        if norm(r["title_raw"]) == norm(a["title"]):
            t_eq += 1
        else:
            review.add("C9.workbook_title", "warn", r["pdf_page"],
                       f"title PDF '{r['title_raw'].replace(chr(10), ' / ')}' vs workbook "
                       f"'{a['title']}'", part="I", sub_id=r["sub_id"],
                       budget_line=r["budget_line"], field="title", dollars=r[FYS[0]] or 0)
        if people(r["sponsor"]) == people(a["sponsor"]):
            s_eq += 1
        else:
            review.add("C9.workbook_sponsor", "warn", r["pdf_page"],
                       f"sponsor PDF '{r['sponsor']}' vs workbook '{a['sponsor']}'",
                       part="I", sub_id=r["sub_id"], budget_line=r["budget_line"],
                       field="sponsor", dollars=r[FYS[0]] or 0)
    report.append(f"  title equal (letters and digits only) on {t_eq}/{n}; sponsor list equal on "
                  f"{s_eq}/{n}")
    moj = [a for a in aw if a.get("_mojibake")]
    if moj:
        report.append(f"  {len(moj)} rows of the comparison source print accents as mojibake "
                      f"(decoded as {CFG['workbook_mojibake']} to compare; source rows "
                      f"{', '.join(sorted({a['source_kind'] for a in moj}))})")
        raw, dec = moj[0]["_mojibake"][0]
        review.add("C9.workbook_text", "warn", "",
                   f"{len(moj)} FY{FY} rows of data/capital/council_capital_awards.csv print "
                   f"accents as mojibake (e.g. '{raw}' for '{dec}'); compared after decoding. "
                   "A note for data/capital, not edited here", part="I")
    return matched, pdf_only, wb_only


# --------------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------------

def row_cols():
    return (["part", "agency", "pdf_page", "row_in_page", "sub_id", "budget_line", "boro", "title",
             "building_code", "school_code", *FYS, "sponsor", "title_raw", "sponsor_raw"]
            + [f"{fy}_printed" for fy in FYS] + ["flags", "bbox_pt", "pdf_sha256"])


def run(out_dir=None, do_ink=True, ink_selftest=False, fy=None):
    if fy is not None:
        configure(fy)
    out_dir = out_dir or OUT
    assert sha256(PDF) == PDF_SHA256, "H1: the PDF is not the one this config was written for"
    os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)
    review = Review()
    selftest = CFG["ink_selftest"]
    summary_pno = pages_of("summary")[0]
    report = [f"FY{FY} capital supporting detail: checks", f"pdf: {os.path.relpath(PDF, REPO)}",
              f"sha256: {PDF_SHA256}", ""]
    rows, totals = [], []
    part3_state = {"org": None, "orgs": []}
    part3_grand = []
    gaps = []
    consumed_by_page, words_by_page = {}, {}
    with pdfplumber.open(PDF) as pdf:
        pages = triage(pdf)
        bad = check_page_map(pages, review)
        report.append(f"H3 page map: {len(pages)} pages, {bad} disagree")
        state = {"agency": None}
        for pg in pages:
            n, kind = pg["pdf_page"], pg["kind"]
            page = pdf.pages[n - 1]
            if kind in ("part1", "part2"):
                part = "I" if kind == "part1" else "II"
                if kind == "part2" and n == pages_of("part2")[0]:
                    state["agency"] = None
                r, t, used, words = parse_detail_page(page, n, part, state, review, gaps)
                for i, row in enumerate(r):
                    row["row_in_page"] = i + 1
                rows.extend(r)
                totals.extend(t)
            elif kind == "part3":
                _, g, used, words = parse_part3_page(page, n, part3_state, review)
                part3_grand.extend(g)
            else:
                words = page_words(page)
                used = {w["wid"] for w in words}       # cover, contents, dividers, summary
            consumed_by_page[n] = used
            words_by_page[n] = words
            leftovers = [w for w in words if w["wid"] not in used]
            for w in leftovers:
                review.add("C6.unconsumed", "critical", n, f"word not emitted: {w['text']}")
        summ = summary_page(pdf, review)

        # Block-gap valley: the largest within-cell gap and the smallest between-cell gap.
        within = [g for g in gaps if g < BLOCK_GAP]
        between = [g for g in gaps if g >= BLOCK_GAP]
        report.append(f"BLOCK_GAP {BLOCK_GAP}: title-line gaps within a cell max "
                      f"{max(within) if within else '-'}, between cells min "
                      f"{min(between) if between else '-'} ({len(gaps)} gaps)")

        # C7 and C8 need pixels.
        c7 = {"pages": 0, "matched": 0, "vector_only": 0, "image_only": 0}
        c8 = {"pages": 0, "regions": 0}
        ink_detail = {}
        if do_ink:
            for pg in pages:
                n = pg["pdf_page"]
                page = pdf.pages[n - 1]
                gray = render_gray(PDF, n)
                vec = vector_rules(page)
                img = image_rules(gray)
                m, vonly, ionly = compare_rules(vec, img)
                # Hairlines thinner than the config's c7_hairline_pt are under a pixel at 300
                # dpi (FY2025 Part III: 0.12 pt, 50% grey): counted, not listed one by one.
                hair = CFG.get("c7_hairline_pt", 0)
                thin = {round(v[0], 2) for v in vec if v[3] < hair}
                c7.setdefault("hairline", collections.Counter())
                c7["hairline"][n] += sum(1 for y in vonly if y in thin)
                vonly = [y for y in vonly if y not in thin]
                c7["pages"] += 1
                c7["matched"] += m
                c7["vector_only"] += len(vonly)
                c7["image_only"] += len(ionly)
                for y in vonly:
                    review.add("C7.rules", "warn", n, f"vector rule at y={y} not seen in pixels")
                for y in ionly:
                    review.add("C7.rules", "critical", n, f"rule in pixels at y={y} not in vector")
                used = consumed_by_page[n]
                if ink_selftest and n == selftest["page"]:
                    # Drop one row's words from the emitted set: the check must fire.
                    drop = {wid for r in rows if r["sub_id"] == selftest["sub_id"] and
                            r["pdf_page"] == n for wid in r["words"]}
                    used = used - drop
                img_pages = CFG.get("ink_cover_image_pages", ())
                if n in img_pages:
                    c8.setdefault("images", []).append((n, len(page.images)))
                regs, total_ink = ink_regions(gray, words_by_page[n], used, page,
                                              images=n in img_pages)
                c8["pages"] += 1
                c8["regions"] += len(regs)
                ink_detail[n] = regs
                for rg in regs:
                    review.add("C8.ink", "critical", n,
                               f"uncovered ink {rg['ink_px']} px at {rg['bbox_pt']}")
            report.append(f"C7 image rules vs vector rules: {c7['pages']} pages, "
                          f"{c7['matched']} matched, {c7['vector_only']} vector only, "
                          f"{c7['image_only']} image only")
            hl = c7.get("hairline", collections.Counter())
            if sum(hl.values()):
                pp = sorted(k for k, v in hl.items() if v)
                report.append(f"  plus {sum(hl.values())} vector hairlines under "
                              f"{CFG['c7_hairline_pt']} pt, below pixel resolution at {DPI} dpi, "
                              f"on pp.{pp[0]}-{pp[-1]}")
                review.add("C7.hairlines", "warn", pp[0],
                           f"{sum(hl.values())} vector rules thinner than {CFG['c7_hairline_pt']} pt "
                           f"(pp.{pp[0]}-{pp[-1]}) are not seen in the {DPI} dpi render; they are "
                           "separators between rows, not content")
            report.append(f"C8 ink coverage: {c8['pages']} pages, {c8['regions']} uncovered "
                          f"regions" + (f"  [SELF-TEST: {selftest['sub_id']} removed on "
                                        f"p.{selftest['page']}]" if ink_selftest else ""))
            for n, k in c8.get("images", ()):
                report.append(f"  p.{n}: {k} images counted as covered (config "
                              "ink_cover_image_pages)")
        else:
            report.append("C7, C8: not run (--no-ink)")

    report.append("")
    report.append(f"Rows parsed: Part I {sum(r['part'] == 'I' for r in rows)}, "
                  f"Part II {sum(r['part'] == 'II' for r in rows)}")
    report.append(f"C1/C2 TOTALS FOR lines (rows/printed, FY{FY} sum/printed):")
    ok = reconcile(rows, totals, review, report)
    report.append(f"  {ok}/{len(totals)} totals lines tie on count and all four FYs")

    # C2: the summary page.
    p1_all = next((t for t in totals if t["part"] == "I" and t["name"] == "ALL"), None)
    report.append(f"C2 p.{summary_pno}: additions {summ['additions']:,}, rescindments "
                  f"{summ['rescindments']:,}, net {summ['net']:,}")
    if p1_all and summ["additions"] == p1_all["printed_" + FYS[0]] == p1_all.get("sum_" + FYS[0]):
        report.append(f"  additions = Part I TOTALS FOR ALL FY{FY} = sum of Part I rows: OK")
    else:
        report.append("  additions vs Part I: FAIL")
        review.add("C2.summary", "critical", summary_pno, f"additions do not equal Part I FY{FY}",
                   dollars=abs((summ["additions"] or 0) - (p1_all or {}).get("sum_" + FYS[0], 0)))
    if summ["additions"] - summ["rescindments"] == summ["net"]:
        report.append("  additions - rescindments = net: OK")
    else:
        review.add("C2.summary", "critical", summary_pno, "additions - rescindments != net")
    review.add("C2.rescindments", "warn", summary_pno,
               f"rescindments ({summ['rescindments']:,}) are printed as one number; no list of "
               "them is in this book, so only the subtraction can be checked",
               dollars=summ["rescindments"])

    # C3: Part II rows are Part I rows.
    key = lambda r: (r["sub_id"], r["budget_line"], r["boro"], r["title"], r["sponsor"],
                     *(r[fy] for fy in FYS))
    p1_by_id = {r["sub_id"]: r for r in rows if r["part"] == "I"}
    p1_all = collections.defaultdict(list)
    for r in rows:
        if r["part"] == "I":
            p1_all[r["sub_id"]].append(r)
    p2_rows = [r for r in rows if r["part"] == "II"]
    same = only2 = 0
    for r in p2_rows:
        # An ID printed twice in Part I (FY2025 `ED NC128`, pp.4 and 44): the one on this
        # row's budget line.
        a = next((c for c in p1_all.get(r["sub_id"], []) if c["budget_line"] == r["budget_line"]),
                 p1_by_id.get(r["sub_id"]))
        if a is None:
            only2 += 1
            continue
        diff = [f for f in ("budget_line", "boro", "title", "sponsor", *FYS) if a[f] != r[f]]
        if not diff:
            same += 1
            continue
        for f in diff:
            review.add("C3.part2_vs_part1", "warn", r["pdf_page"],
                       f"Part II {f} '{r[f]}' vs Part I (p.{a['pdf_page']}) '{a[f]}'"
                       + (f"; Part I text added after export: '{a['edited_text']}'"
                          if a.get("edited_text") else ""),
                       part="II", sub_id=r["sub_id"], budget_line=r["budget_line"], field=f,
                       dollars=r[FYS[0]] or 0, expected=a[f], observed=r[f])
    ma = [r for r in p2_rows if r["sub_id"] not in p1_by_id]
    report.append(f"C3 Part II: {len(p2_rows)} rows; {same} equal a Part I row in every field; "
                  f"{len(p2_rows) - same - only2} differ in a field; {only2} are not in Part I")
    reused = {k: v for k, v in p1_all.items() if len(v) > 1}
    if reused:
        report.append(f"  Part I IDs printed on more than one row: {len(reused)} "
                      f"({', '.join(sorted(reused))})")
    for k, v in sorted(reused.items()):
        review.add("C3.id_reused", "warn", v[0]["pdf_page"],
                   f"{k} is printed on {len(v)} Part I rows: " + "; ".join(
                       f"p.{x['pdf_page']} {x['budget_line']} '{x['title']}' {x[FYS[0]] or 0:,}"
                       for x in v), part="I", sub_id=k, dollars=sum(x[FYS[0]] or 0 for x in v))
    ma_ids = collections.Counter(r["sub_id"].split(" ")[1][:2] for r in ma)
    ma_lines = collections.Counter(r["budget_line"].split(" ")[1][:2] for r in ma)
    ma_usd = sum(r[FYS[0]] or 0 for r in ma)
    report.append(f"  not in Part I: ID series {dict(ma_ids)}, budget-line series {dict(ma_lines)}, "
                  f"FY{FY} ${ma_usd:,}, sponsor blank on "
                  f"{sum(1 for r in ma if not r['sponsor'])}")
    # The series Part II-only rows are expected in (FY2027: MA IDs on 0N lines). Any other
    # Part II-only row is critical. The workbook claim is checked, not assumed.
    sid, sln = CFG["part2_only"]["id_prefix"], CFG["part2_only"]["line_prefix"]
    series = []
    for r in ma:
        if r["sub_id"].split(" ")[1].startswith(sid) and r["budget_line"].split(" ")[1].startswith(sln):
            series.append(r)
        else:
            review.add("C3.part2_only", "critical", r["pdf_page"],
                       f"Part II row not in Part I and not in the {sid} / {sln} series", part="II",
                       sub_id=r["sub_id"], budget_line=r["budget_line"], dollars=r[FYS[0]] or 0)
    wb_ids = {wb_id(a) for a in awards_for_year()}
    in_wb = [r for r in series if r["sub_id"].split(" ")[1] in wb_ids]
    s_usd = sum(r[FYS[0]] or 0 for r in series)
    if series:
        review.add("C3.ma_series", "warn", series[0]["pdf_page"],
                   f"{len(series)} Part II rows ({sid} IDs on {sln} budget lines, "
                   f"{'no sponsor' if not any(r['sponsor'] for r in series) else 'sponsors as printed'}, "
                   f"${s_usd:,} FY{FY}) are not Council additions: they are "
                   f"not in Part I, not in the p.{summary_pno} total, and "
                   + ("not in the Council workbook" if not in_wb else
                      f"{len(in_wb)} of their IDs are in the Council workbook") +
                   f". Meaning of {sid} / {sln} unconfirmed", part="II", dollars=s_usd)
    # Config `flag_id_series`: Part I ID series to list for a person (FY2023 `RR`: no sponsor,
    # some on borough A; the Council's t474 dictionary says only "analogous to TA"). One warning
    # per series naming every row; the rows stay in the data as printed. Default none.
    for ser in CFG.get("flag_id_series", ()):
        sr = [r for r in rows if r["part"] == "I" and r["sub_id"].split(" ")[-1].startswith(ser)]
        if not sr:
            continue
        usd = sum(r[FYS[0]] or 0 for r in sr)
        report.append(f"  Part I {ser} series: {len(sr)} rows, FY{FY} ${usd:,}, sponsor blank on "
                      f"{sum(1 for r in sr if not r['sponsor'])}, boroughs "
                      f"{dict(sorted(collections.Counter(r['boro'] for r in sr).items()))}")
        review.add("C3.id_series", "warn", sr[0]["pdf_page"],
                   f"{len(sr)} Part I rows carry {ser} IDs (${usd:,} FY{FY}, in the Part I total): "
                   + "; ".join(f"p.{r['pdf_page']} {r['sub_id']} {r['budget_line']} {r['boro']} "
                               f"'{r['title']}' {r[FYS[0]] or 0:,}"
                               + ("" if r["sponsor"] else " (no sponsor)") for r in sr)
                   + f". Meaning of {ser} unconfirmed", part="I", dollars=usd)
    p2ids = {r["sub_id"] for r in p2_rows}
    p1_dn = [r for r in rows if r["part"] == "I" and r["budget_line"].split(" ")[-1].startswith("DN")]
    missing_dn = [r for r in p1_dn if r["sub_id"] not in p2ids]
    report.append(f"  Part I rows on DN (non-city) lines: {len(p1_dn)}; missing from Part II: "
                  f"{len(missing_dn)}")
    for r in missing_dn:
        review.add("C3.dn_not_in_part2", "critical", r["pdf_page"],
                   "Part I row on a non-city (DN) budget line is not listed in Part II",
                   part="I", sub_id=r["sub_id"], budget_line=r["budget_line"],
                   dollars=r[FYS[0]] or 0)
    p1_not_dn_in_2 = [r for r in p2_rows if r["sub_id"] in p1_by_id and
                      not r["budget_line"].split(" ")[-1].startswith("DN")]
    report.append(f"  Part II rows from Part I that are not on a DN line: {len(p1_not_dn_in_2)}")

    # Edited text (warn): post-export edits, so a person reads them.
    for r in rows:
        if r.get("edited_text"):
            review.add("W.edited_after_export", "warn", r["pdf_page"],
                       f"text typed in after export (other font): '{r['edited_text']}'; "
                       f"sponsor now reads '{r['sponsor']}'", part=r["part"], sub_id=r["sub_id"],
                       budget_line=r["budget_line"], dollars=r[FYS[0]] or 0)
    sa = state.get("stream_agree", collections.Counter())
    so = state.get("stream_out_of_order", collections.Counter())
    report.append(f"C5 geometry vs stream: {sum(sa.values())} words agree; {sum(so.values())} words "
                  f"the stream wrote out of row order (no second opinion), on pages "
                  f"{sorted(so)}")

    # C4: Part III.
    orgs = part3_state["orgs"]
    p3_lines = [dict(l, organization=o["organization"]) for o in orgs for l in o["lines"]]
    org_ok = 0
    for o in orgs:
        sums = {fy: sum(l[fy] for l in o["lines"]) for fy in FYS}
        if all(sums[fy] == o[f"org_{fy}"] for fy in FYS) and o["lines"]:
            org_ok += 1
            o["status"] = "OK"
        else:
            o["status"] = "FAIL"
            review.add("C4.org_sum", "critical", o["pdf_page"],
                       f"{o['organization']}: lines {sums} vs printed "
                       f"{ {fy: o[f'org_{fy}'] for fy in FYS} }", part="III",
                       dollars=max(abs(sums[fy] - o[f"org_{fy}"]) for fy in FYS))
    report.append(f"C4 Part III: {len(orgs)} organizations, {len(p3_lines)} budget-line rows; "
                  f"{org_ok}/{len(orgs)} organization lines equal their rows")
    gsum = {fy: sum(l[fy] for l in p3_lines) for fy in FYS}
    if part3_grand:
        g = part3_grand[-1]
        st = "OK" if all(g[fy] == gsum[fy] for fy in FYS) else "FAIL"
        report.append(f"  TOTAL NON-CITY PROJECT ALLOCATIONS {g[FYS[0]]:,}/{g[FYS[1]]:,}: "
                      f"rows {gsum[FYS[0]]:,}/{gsum[FYS[1]]:,} {st}")
        p2_all = next((t for t in totals if t["part"] == "II" and t["name"] == "ALL"), None)
        if p2_all:
            st2 = "OK" if all(g[fy] == p2_all[f"printed_{fy}"] for fy in FYS) else "FAIL"
            report.append(f"  = Part II TOTALS FOR ALL: {st2}")
    else:
        review.add("C4.grand", "critical", pages_of("part3")[-1], "Part III grand total not found",
                   part="III")
    # By budget line, Part III vs Part II.
    by3 = collections.defaultdict(lambda: [0, 0, 0, 0])
    for l in p3_lines:
        for k, fy in enumerate(FYS):
            by3[l["budget_line"]][k] += l[fy]
    by2 = collections.defaultdict(lambda: [0, 0, 0, 0])
    for r in rows:
        if r["part"] == "II":
            for k, fy in enumerate(FYS):
                by2[r["budget_line"]][k] += r[fy] or 0
    lines_eq = sum(1 for bl in set(by2) | set(by3) if by2.get(bl) == by3.get(bl))
    report.append(f"  Part III vs Part II by budget line: {lines_eq}/{len(set(by2) | set(by3))} equal")
    for bl in sorted(set(by2) | set(by3)):
        a, b = by2.get(bl, [0] * 4), by3.get(bl, [0] * 4)
        if a != b:
            pages3 = sorted({l["pdf_page"] for l in p3_lines if l["budget_line"] == bl})
            pages2 = sorted({r["pdf_page"] for r in rows if r["part"] == "II" and r["budget_line"] == bl})
            review.add("C4.by_budget_line", "critical", (pages3 or pages2 or [""])[0],
                       f"budget line {bl}: Part II {a} (pp.{pages2}) vs Part III {b} (pp.{pages3})",
                       part="III", budget_line=bl, dollars=max(abs(x - y) for x, y in zip(a, b)))

    # C9 workbook alignment.
    report.append(f"C9 Council workbook (data/capital/council_capital_awards.csv, report_year {FY}):")
    align_workbook(rows, review, report)

    # C5 tie-break. A near disagreement keeps the geometry read; it is downgraded only when
    # an independent source settles it: the field equals the Council workbook, or the word is a
    # 0 and both candidate rows print 0 there (no dollar effect).
    wb = collections.defaultdict(list)
    for a in awards_for_year():
        wb[(wb_id(a), a["budget_line"])].append(a)
    by_sub = {(r["part"], r["sub_id"]): r for r in rows}
    norm = lambda t: re.sub(r"[^A-Z0-9]", "", unicodedata.normalize("NFKD", t.replace(CID_TAB, " ")).upper())
    ppl = lambda t: sorted(x for x in (norm(y) for y in t.split(",")) if x)
    for rv in review.rows:
        if rv["check_id"] != "C5.geom_vs_stream":
            continue
        r = by_sub.get((rv["part"], rv["sub_id"]))
        m = re.search(r"stream says (\S+ \S+)", rv["note"])
        other = by_sub.get((rv["part"], m.group(1))) if m else None
        f = rv["field"]
        a = (wb.get((r["sub_id"].split(" ")[-1], r["budget_line"])) or [None])[0] if r else None
        why = None
        if f in FYS and rv["note"].startswith("'0'") and r and other and r[f] == 0 and other[f] == 0:
            why = "a 0 that both rows print; no dollar effect"
        elif f == "title" and a and norm(r["title_raw"]) == norm(a["title"]):
            why = "geometry's title equals the Council workbook"
        elif f == "sponsor" and a and ppl(r["sponsor"]) == ppl(a["sponsor"]):
            why = "geometry's sponsor equals the Council workbook"
        if why:
            rv["severity"] = "warn"
            rv["note"] += f" -> kept geometry: {why}"

    # Flags carried on rows (warn).
    for r in rows:
        for f in sorted(set(r["flags"])):
            if f.endswith("_wrapped_below") or f == "geom_near" or f == "extra_sub_id_word":
                review.add(f"W.{f}", "warn", r["pdf_page"], f"row flag {f}", part=r["part"],
                           sub_id=r["sub_id"], budget_line=r["budget_line"])

    # ---- write -----------------------------------------------------------------------------
    d = os.path.join(out_dir, "data")
    with open(os.path.join(d, f"{PREFIX}_capital_sd_pages.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pages[0]))
        w.writeheader()
        w.writerows(pages)
    with open(os.path.join(d, f"{PREFIX}_capital_sd_projects.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=row_cols(), extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "flags": ";".join(sorted(set(r["flags"]))), "pdf_sha256": PDF_SHA256})
    with open(os.path.join(d, f"{PREFIX}_capital_sd_totals.csv"), "w", newline="") as f:
        cols = ["part", "pdf_page", "name", "printed_count", "rows"] + \
               [f"printed_{fy}" for fy in FYS] + [f"sum_{fy}" for fy in FYS] + ["status", "printed_text"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(totals)
    with open(os.path.join(d, f"{PREFIX}_capital_sd_part3.csv"), "w", newline="") as f:
        cols = ["pdf_page", "organization", "budget_line"] + list(FYS) + ["bbox_pt"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(p3_lines)
    with open(os.path.join(d, f"{PREFIX}_capital_sd_part3_orgs.csv"), "w", newline="") as f:
        cols = ["pdf_page", "organization"] + [f"org_{fy}" for fy in FYS] + ["n_lines", "status", "bbox_pt"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for o in orgs:
            w.writerow({**o, "n_lines": len(o["lines"])})
    review_rows = sorted(review.rows, key=lambda r: (r["severity"] != "critical",
                                                     -(r["dollars"] or 0), str(r["pdf_page"])))
    with open(os.path.join(d, f"{PREFIX}_capital_sd_review.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=Review.COLS)
        w.writeheader()
        w.writerows(review_rows)
        if not review_rows:
            w.writerow({"check_id": "ok", "note": "all checks ran; nothing to review"})
    if do_ink:
        with open(os.path.join(d, f"{PREFIX}_capital_sd_ink.json"), "w") as f:
            json.dump({str(k): v for k, v in ink_detail.items() if v}, f, indent=1)
    cnt = collections.Counter((r["check_id"], r["severity"]) for r in review.rows)
    report.append("")
    report.append("review.csv by check:")
    for (c, s), n in sorted(cnt.items()):
        report.append(f"  {c:<28} {s:<8} {n}")
    with open(os.path.join(d, f"{PREFIX}_capital_sd_checks.txt"), "w") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))
    return rows, totals, review


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--fy", type=int, default=2027, help="fiscal year (config/capital_sd/fy<FY>.toml)")
    ap.add_argument("--out", default=None, help="output folder (default: the config's review_dir)")
    ap.add_argument("--no-ink", action="store_true", help="skip C7/C8 (no rendering)")
    ap.add_argument("--selftest-ink", action="store_true",
                    help="drop the config's ink_selftest row from its page; C8 must fire there")
    a = ap.parse_args()
    run(a.out, do_ink=not a.no_ink, ink_selftest=a.selftest_ink, fy=a.fy)
