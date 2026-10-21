"""
FY2027 Section 254 capital supporting detail: parse, tie out and review (GitHub #102, epic #101).

Source: source/FY27/Supporting-Detail-for-FY2027-Changes-To-the-Executive-Capital-Budget-
Pursuant-to-Section-254.V4.pdf (80 pages, tier B, 71 pages rotated /Rotate 90).

This is a review build, not a served dataset (DATA-ANOMALIES §27: PDF data is not served in
2.0). It writes to research/2026-10-20-fy27-capital-terms-review/ and never touches data/.

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
  C2 `TOTALS FOR ALL` per Part; p.61 additions = Part I FY2027; additions - rescindments = net
  C3 Part II rows are Part I rows (every field)
  C4 Part III: each organization's $ line = its budget-line rows; the grand total; Part III by
     budget line = Part II by budget line
  C5 geometry read == stream read, word by word
  C6 every non-furniture word on a detail page lands in exactly one field (no orphans)
  C7 image rules (code/ocr/grid.py rule_masks at 300 dpi) == vector rules, every page
  C8 ink coverage: rendered ink not under an emitted character or a vector rule
  C9 alignment with data/capital/council_capital_awards.csv (report only, never fills a value)

Run:  .venv/bin/python code/review_capital_sd.py [--out DIR] [--no-ink] [--selftest-ink]
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import re
import sys
import unicodedata

import pdfplumber

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

PDF = os.path.join(REPO, "source/FY27/Supporting-Detail-for-FY2027-Changes-To-the-Executive-"
                         "Capital-Budget-Pursuant-to-Section-254.V4.pdf")
PDF_SHA256 = "4c48252ec0d0a7b6795456feaa53f303193e6a8dcf608b2984758000139d5b90"
AWARDS = os.path.join(REPO, "data/capital/council_capital_awards.csv")
OUT = os.path.join(REPO, "research/2026-10-20-fy27-capital-terms-review")

# Page map, checked against the page furniture in triage() (a page that disagrees fails).
PAGE_MAP = {1: "cover", 2: "contents", 3: "divider", 61: "summary", 62: "divider",
            72: "divider"}
PAGE_MAP.update({p: "part1" for p in range(4, 61)})
PAGE_MAP.update({p: "part2" for p in range(63, 72)})
PAGE_MAP.update({p: "part3" for p in range(73, 81)})
FYS = ("fy2027", "fy2028", "fy2029", "fy2030")

X_TOL = 1.5               # pdfplumber x_tolerance; the prototype's value (families/capital.md §3.1)
LINE_TOL = 1.5            # words whose tops differ by less than this are one printed line
BLOCK_GAP = 12.0          # pt between line tops: below = same cell (leading ~9.6), above = new
                          # cell (>= 14.4 measured). Re-measured in checks.txt every run.
AMOUNT_X1_TOL = 3.0       # an amount is right-aligned to its FY header's right edge
NEAR_TOL = 6.0            # a word outside every row band may join the nearest band within this
AMOUNT_RE = re.compile(r"^-?\$?[\d,]+$")
SUB_CODE_RE = re.compile(r"^[A-Z]{1,3}$")
SUB_ID_RE = re.compile(r"^[A-Z]{2}\d{3,5}$")
CODE_RE = re.compile(r"\b([BS]):(?:[BS]:)?\s?([A-Z]\d{3}[A-Z]?)\b")   # "B:B:Q156" printed too
# The Word export's two font subsets on detail pages. Text in any other subset was typed in
# later (Acrobat edits after export: pp.40, 45, 46, 47, 55, 56, 58).
EXPORT_FONTS = ("FPJADB+", "FPJABP+")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def money(s):
    """Printed amount -> int. `$` and thousands commas only; a leading minus is kept."""
    return int(s.replace("$", "").replace(",", ""))


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
        w["bold"] = "Bold" in w["fontname"]
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


def line_text(ws):
    return " ".join(w["text"] for w in sorted(ws, key=lambda w: w["x0"]))


def rid(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:12]


class Review:
    """review.csv rows (PLAN.md §5.3 shape, trimmed to what this book has)."""

    COLS = ["review_id", "check_id", "severity", "pdf_page", "part", "sub_id", "budget_line",
            "field", "dollars", "expected", "observed", "note"]

    def __init__(self):
        self.rows = []

    def add(self, check_id, severity, page, note, part="", sub_id="", budget_line="",
            field="", dollars=0, expected="", observed=""):
        self.rows.append({"review_id": rid("fy2027", check_id, page, sub_id, field, note),
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
            ok = pg["first_line"] == expect_first[k] and pg["rotate"] == 90 and \
                pg["printed_label"] != ""
        elif k == "part3":
            ok = pg["rotate"] == 0 and pg["printed_label"] != ""
        if not ok:
            bad += 1
            review.add("H3.page_map", "critical", pg["pdf_page"],
                       f"page furniture does not match the page map ({k})")
    return bad


# --------------------------------------------------------------------------------------------
# Parts I and II: the detail table
# --------------------------------------------------------------------------------------------

def header_columns(lines):
    """Column geometry from this page's header line (SUB ID ... SPONSOR)."""
    for ln in lines:
        texts = [w["text"] for w in ln]
        if "SUB" in texts and "SPONSOR" in texts:
            by = {w["text"]: w for w in ln}
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
    row["title"] = re.sub(r"\s+", " ", CODE_RE.sub("", row["title_raw"].replace("\n", " "))).strip()
    # Clean rules (listed, counted): line breaks -> space; whitespace collapsed; a space before
    # a comma removed (the post-export edits print "BANKS , LOUIS").
    sp = re.sub(r"\s+", " ", row["sponsor_raw"].replace("\n", " ")).strip()
    row["sponsor"] = re.sub(r" ,", ",", sp)
    rules = []
    if "\n" in row["title_raw"] or "\n" in row["sponsor_raw"]:
        rules.append("line_join")
    if row["sponsor"] != sp:
        rules.append("space_before_comma")
    if codes:
        rules.append("bs_codes_split")
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

    def amounts(ln):
        got = {}
        for w in ln:
            if AMOUNT_RE.match(w["text"]):
                for k, x1 in enumerate(hdr["fy_x1"]):
                    if abs(w["x1"] - x1) <= AMOUNT_X1_TOL:
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
                state["org"] = {"pdf_page": pno, "organization": text,
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
            ys.append(((r["top"] + r["bottom"]) / 2, r["x0"], r["x1"]))
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


def ink_regions(gray, words, consumed, page, pad_px=4, min_ink_px=30):
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
                          f"{n:>5}/{t['printed_count']:<5} {got['fy2027']:>13,}/"
                          f"{t['printed_fy2027']:<13,} {status}")
            if status == "OK":
                ok += 1
            else:
                review.add("C1.total", "critical", t["pdf_page"],
                           f"TOTALS FOR {t['name']}: rows {n} vs {t['printed_count']}; "
                           + ", ".join(f"{fy} {got[fy]:,} vs {t[f'printed_{fy}']:,}" for fy in diffs),
                           part=part, dollars=max([abs(got[fy] - t[f"printed_{fy}"]) for fy in FYS]),
                           expected=t["printed_fy2027"], observed=got["fy2027"])
            if t["name"] != "ALL":
                since = []
    return ok


def summary_page(pdf, review):
    """p.61: City Council Additions / Less Rescindments / Net Change."""
    text = pdf.pages[60].extract_text()
    def grab(label):
        m = re.search(label + r"\s+\(?\$([\d,]+)\)?", text)
        return money(m.group(1)) if m else None
    return {"additions": grab("City Council Additions"),
            "rescindments": grab("Less Rescindments from Prior Capital Budgets"),
            "net": grab("Net Change")}


def awards_fy2027():
    with open(AWARDS, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["report_year"] == "2027"]


def align_workbook(rows, review, report):
    """C9. The workbook drops the agency prefix from the ID (`CC0001`); compare on
    (ID number, budget line, FY, amount) for every non-zero amount, then explain the rest."""
    aw = awards_fy2027()
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
    wb_keys = collections.Counter()
    wb_by = collections.defaultdict(list)
    for a in aw:
        k = (a["project_id"], a["budget_line"], a["amount_fy"], int(a["amount"]))
        wb_keys[k] += 1
        wb_by[k].append(a)
    matched = sum((pdf_keys & wb_keys).values())
    pdf_only = pdf_keys - wb_keys
    wb_only = wb_keys - pdf_keys
    report.append(f"  PDF Part I non-zero amounts: {sum(pdf_keys.values())}; workbook FY2027 rows: "
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
    for a in aw:
        wb_by_id[(a["project_id"], a["budget_line"])].append(a)
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
                       dollars=r["fy2027"] or 0)
    report.append(f"  borough differs from the workbook on {boro_diff} Part I rows")

    # Title and sponsor, as an independent check of which row each wrapped line went to.
    # The workbook title carries the B:/S: codes, as the PDF prints them.
    def norm(s):
        # Accents folded: the post-export edits print FARIAS where the workbook has Farías.
        return re.sub(r"[^A-Z0-9]", "", unicodedata.normalize("NFKD", s).upper())

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
        a = cands[0]
        if norm(r["title_raw"]) == norm(a["title"]):
            t_eq += 1
        else:
            review.add("C9.workbook_title", "warn", r["pdf_page"],
                       f"title PDF '{r['title_raw'].replace(chr(10), ' / ')}' vs workbook "
                       f"'{a['title']}'", part="I", sub_id=r["sub_id"],
                       budget_line=r["budget_line"], field="title", dollars=r["fy2027"] or 0)
        if people(r["sponsor"]) == people(a["sponsor"]):
            s_eq += 1
        else:
            review.add("C9.workbook_sponsor", "warn", r["pdf_page"],
                       f"sponsor PDF '{r['sponsor']}' vs workbook '{a['sponsor']}'",
                       part="I", sub_id=r["sub_id"], budget_line=r["budget_line"],
                       field="sponsor", dollars=r["fy2027"] or 0)
    report.append(f"  title equal (letters and digits only) on {t_eq}/{n}; sponsor list equal on "
                  f"{s_eq}/{n}")
    return matched, pdf_only, wb_only


# --------------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------------

ROW_COLS = ["part", "agency", "pdf_page", "row_in_page", "sub_id", "budget_line", "boro", "title",
            "building_code", "school_code", "fy2027", "fy2028", "fy2029", "fy2030", "sponsor",
            "title_raw", "sponsor_raw", "fy2027_printed", "fy2028_printed", "fy2029_printed",
            "fy2030_printed", "flags", "bbox_pt", "pdf_sha256"]


def run(out_dir, do_ink=True, ink_selftest=False):
    assert sha256(PDF) == PDF_SHA256, "H1: the PDF is not the one this config was written for"
    os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)
    review = Review()
    report = ["FY2027 capital supporting detail: checks", f"pdf: {os.path.relpath(PDF, REPO)}",
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
                if kind == "part2" and n == 63:
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
                c7["pages"] += 1
                c7["matched"] += m
                c7["vector_only"] += len(vonly)
                c7["image_only"] += len(ionly)
                for y in vonly:
                    review.add("C7.rules", "warn", n, f"vector rule at y={y} not seen in pixels")
                for y in ionly:
                    review.add("C7.rules", "critical", n, f"rule in pixels at y={y} not in vector")
                used = consumed_by_page[n]
                if ink_selftest and n == 40:
                    # Drop HD CC1047's words from the emitted set: the check must fire.
                    drop = {wid for r in rows if r["sub_id"] == "HD CC1047" for wid in r["words"]}
                    used = used - drop
                regs, total_ink = ink_regions(gray, words_by_page[n], used, page)
                c8["pages"] += 1
                c8["regions"] += len(regs)
                ink_detail[n] = regs
                for rg in regs:
                    review.add("C8.ink", "critical", n,
                               f"uncovered ink {rg['ink_px']} px at {rg['bbox_pt']}")
            report.append(f"C7 image rules vs vector rules: {c7['pages']} pages, "
                          f"{c7['matched']} matched, {c7['vector_only']} vector only, "
                          f"{c7['image_only']} image only")
            report.append(f"C8 ink coverage: {c8['pages']} pages, {c8['regions']} uncovered "
                          f"regions" + ("  [SELF-TEST: HD CC1047 removed on p.40]"
                                        if ink_selftest else ""))
        else:
            report.append("C7, C8: not run (--no-ink)")

    report.append("")
    report.append(f"Rows parsed: Part I {sum(r['part'] == 'I' for r in rows)}, "
                  f"Part II {sum(r['part'] == 'II' for r in rows)}")
    report.append("C1/C2 TOTALS FOR lines (rows/printed, FY2027 sum/printed):")
    ok = reconcile(rows, totals, review, report)
    report.append(f"  {ok}/{len(totals)} totals lines tie on count and all four FYs")

    # C2: the p.61 summary.
    p1_all = next((t for t in totals if t["part"] == "I" and t["name"] == "ALL"), None)
    report.append(f"C2 p.61: additions {summ['additions']:,}, rescindments "
                  f"{summ['rescindments']:,}, net {summ['net']:,}")
    if p1_all and summ["additions"] == p1_all["printed_fy2027"] == p1_all.get("sum_fy2027"):
        report.append("  additions = Part I TOTALS FOR ALL FY2027 = sum of Part I rows: OK")
    else:
        report.append("  additions vs Part I: FAIL")
        review.add("C2.summary", "critical", 61, "additions do not equal Part I FY2027",
                   dollars=abs((summ["additions"] or 0) - (p1_all or {}).get("sum_fy2027", 0)))
    if summ["additions"] - summ["rescindments"] == summ["net"]:
        report.append("  additions - rescindments = net: OK")
    else:
        review.add("C2.summary", "critical", 61, "additions - rescindments != net")
    review.add("C2.rescindments", "warn", 61,
               f"rescindments ({summ['rescindments']:,}) are printed as one number; no list of "
               "them is in this book, so only the subtraction can be checked",
               dollars=summ["rescindments"])

    # C3: Part II rows are Part I rows.
    key = lambda r: (r["sub_id"], r["budget_line"], r["boro"], r["title"], r["sponsor"],
                     *(r[fy] for fy in FYS))
    p1_by_id = {r["sub_id"]: r for r in rows if r["part"] == "I"}
    p2_rows = [r for r in rows if r["part"] == "II"]
    same = only2 = 0
    for r in p2_rows:
        a = p1_by_id.get(r["sub_id"])
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
                       dollars=r["fy2027"] or 0, expected=a[f], observed=r[f])
    ma = [r for r in p2_rows if r["sub_id"] not in p1_by_id]
    report.append(f"C3 Part II: {len(p2_rows)} rows; {same} equal a Part I row in every field; "
                  f"{len(p2_rows) - same - only2} differ in a field; {only2} are not in Part I")
    ma_ids = collections.Counter(r["sub_id"].split(" ")[1][:2] for r in ma)
    ma_lines = collections.Counter(r["budget_line"].split(" ")[1][:2] for r in ma)
    report.append(f"  not in Part I: ID series {dict(ma_ids)}, budget-line series {dict(ma_lines)}, "
                  f"FY2027 ${sum(r['fy2027'] or 0 for r in ma):,}, sponsor blank on "
                  f"{sum(1 for r in ma if not r['sponsor'])}")
    for r in ma:
        if not (r["sub_id"].split(" ")[1].startswith("MA") and r["budget_line"].split(" ")[1].startswith("0N")):
            review.add("C3.part2_only", "critical", r["pdf_page"],
                       "Part II row not in Part I and not in the MA / 0N series", part="II",
                       sub_id=r["sub_id"], budget_line=r["budget_line"], dollars=r["fy2027"] or 0)
    review.add("C3.ma_series", "warn", ma[0]["pdf_page"] if ma else "",
               f"{len(ma)} Part II rows (MA IDs on 0N budget lines, no sponsor, "
               f"${sum(r['fy2027'] or 0 for r in ma):,} FY2027) are not Council additions: they are "
               "not in Part I, not in the p.61 total, and not in the Council workbook. Meaning of "
               "MA / 0N unconfirmed", part="II", dollars=sum(r["fy2027"] or 0 for r in ma))
    p2ids = {r["sub_id"] for r in p2_rows}
    p1_dn = [r for r in rows if r["part"] == "I" and r["budget_line"].split(" ")[-1].startswith("DN")]
    missing_dn = [r for r in p1_dn if r["sub_id"] not in p2ids]
    report.append(f"  Part I rows on DN (non-city) lines: {len(p1_dn)}; missing from Part II: "
                  f"{len(missing_dn)}")
    for r in missing_dn:
        review.add("C3.dn_not_in_part2", "critical", r["pdf_page"],
                   "Part I row on a non-city (DN) budget line is not listed in Part II",
                   part="I", sub_id=r["sub_id"], budget_line=r["budget_line"],
                   dollars=r["fy2027"] or 0)
    p1_not_dn_in_2 = [r for r in p2_rows if r["sub_id"] in p1_by_id and
                      not r["budget_line"].split(" ")[-1].startswith("DN")]
    report.append(f"  Part II rows from Part I that are not on a DN line: {len(p1_not_dn_in_2)}")

    # Edited text (warn): post-export edits, so a person reads them.
    for r in rows:
        if r.get("edited_text"):
            review.add("W.edited_after_export", "warn", r["pdf_page"],
                       f"text typed in after export (other font): '{r['edited_text']}'; "
                       f"sponsor now reads '{r['sponsor']}'", part=r["part"], sub_id=r["sub_id"],
                       budget_line=r["budget_line"], dollars=r["fy2027"] or 0)
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
        report.append(f"  TOTAL NON-CITY PROJECT ALLOCATIONS {g['fy2027']:,}/{g['fy2028']:,}: "
                      f"rows {gsum['fy2027']:,}/{gsum['fy2028']:,} {st}")
        p2_all = next((t for t in totals if t["part"] == "II" and t["name"] == "ALL"), None)
        if p2_all:
            st2 = "OK" if all(g[fy] == p2_all[f"printed_{fy}"] for fy in FYS) else "FAIL"
            report.append(f"  = Part II TOTALS FOR ALL: {st2}")
    else:
        review.add("C4.grand", "critical", 80, "Part III grand total not found", part="III")
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
    report.append("C9 Council workbook (data/capital/council_capital_awards.csv, report_year 2027):")
    align_workbook(rows, review, report)

    # C5 tie-break. A near disagreement keeps the geometry read; it is downgraded only when
    # an independent source settles it: the field equals the Council workbook, or the word is a
    # 0 and both candidate rows print 0 there (no dollar effect).
    wb = collections.defaultdict(list)
    for a in awards_fy2027():
        wb[(a["project_id"], a["budget_line"])].append(a)
    by_sub = {(r["part"], r["sub_id"]): r for r in rows}
    norm = lambda t: re.sub(r"[^A-Z0-9]", "", unicodedata.normalize("NFKD", t).upper())
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
    with open(os.path.join(d, "fy27_capital_sd_pages.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pages[0]))
        w.writeheader()
        w.writerows(pages)
    with open(os.path.join(d, "fy27_capital_sd_projects.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ROW_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "flags": ";".join(sorted(set(r["flags"]))), "pdf_sha256": PDF_SHA256})
    with open(os.path.join(d, "fy27_capital_sd_totals.csv"), "w", newline="") as f:
        cols = ["part", "pdf_page", "name", "printed_count", "rows"] + \
               [f"printed_{fy}" for fy in FYS] + [f"sum_{fy}" for fy in FYS] + ["status", "printed_text"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(totals)
    with open(os.path.join(d, "fy27_capital_sd_part3.csv"), "w", newline="") as f:
        cols = ["pdf_page", "organization", "budget_line"] + list(FYS)
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(p3_lines)
    with open(os.path.join(d, "fy27_capital_sd_part3_orgs.csv"), "w", newline="") as f:
        cols = ["pdf_page", "organization"] + [f"org_{fy}" for fy in FYS] + ["n_lines", "status"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for o in orgs:
            w.writerow({**o, "n_lines": len(o["lines"])})
    review_rows = sorted(review.rows, key=lambda r: (r["severity"] != "critical",
                                                     -(r["dollars"] or 0), str(r["pdf_page"])))
    with open(os.path.join(d, "fy27_capital_sd_review.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=Review.COLS)
        w.writeheader()
        w.writerows(review_rows)
        if not review_rows:
            w.writerow({"check_id": "ok", "note": "all checks ran; nothing to review"})
    if do_ink:
        with open(os.path.join(d, "fy27_capital_sd_ink.json"), "w") as f:
            json.dump({str(k): v for k, v in ink_detail.items() if v}, f, indent=1)
    cnt = collections.Counter((r["check_id"], r["severity"]) for r in review.rows)
    report.append("")
    report.append("review.csv by check:")
    for (c, s), n in sorted(cnt.items()):
        report.append(f"  {c:<28} {s:<8} {n}")
    with open(os.path.join(d, "fy27_capital_sd_checks.txt"), "w") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))
    return rows, totals, review


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--no-ink", action="store_true", help="skip C7/C8 (no rendering)")
    ap.add_argument("--selftest-ink", action="store_true",
                    help="drop HD CC1047 from p.40's emitted set; C8 must fire there")
    a = ap.parse_args()
    run(a.out, do_ink=not a.no_ink, ink_selftest=a.selftest_ink)
