"""
Terms and Conditions: parse, check and review (epic #101; FY2027 #102, FY2026 #103,
FY2025 #104, FY2024 #105).

One parser, one config per year (config/terms/fyNNNN.toml: PDF, sha256, page furniture, the
retired CSV to compare with). FY2027 (the default): source/FY27/FY27-FINAL-Terms-and-Conditions-
6.30.26.pdf (32 pages, tier B, Word export). FY2026: source/FY26/FY26-Terms-and-Conditions-1.pdf
(29 pages). FY2025: source/FY25/FY25-Terms-and-Conditions-1.pdf (25 pages). FY2024:
source/FY24/FY24-Terms-and-Conditions.pdf (24 pages, no printed condition numbers: config numbered = false). Writes to the config's research/ folder (never to data/; DATA-ANOMALIES §27).

The document is prose (families/transparency-and-terms.md §4). Its structure is:

  heading   bold, centred: "N. Agency (code)", then "Unit of Appropriation [nnn]" and/or
            "Budget Line XX-nnnn" lines; one condition may name several agencies, each with
            its own bold "Agency (code)" line and units (#64, p.24)
  body      regular text up to the next numbered heading; lettered and numbered lists inside
            the body are not headings (they are not bold)
  table     one ruled table, DOE's Financial Status Report schedule (#15, pp.7-8)

Checks (numbers in checks.txt, failures in review.csv):
  T1 numbered headings run 1..N with no gap or repeat
  T2 every "Unit of Appropriation [..]" / "Budget Line .." line on the page (an independent
     regex over the page text) lands in exactly one condition's heading
  T3 the units and budget lines the body's first sentence names = the heading's (report only:
     a difference is the PDF disagreeing with itself)
  T4 character conservation: every character outside page furniture is in one condition
  T5 FSR table: vector lattice (pdfplumber) vs image lattice (code/ocr/grid.py detect_grid,
     kernel_px=60) separators within 2 pt, and cell strings identical under both
  T6 ink coverage, as in review_capital_sd.py
  T7 against the retired data/fyNN/terms CSV (config old_csv): rows, numbers, agencies, units, and text
     (whitespace removed), plus the mid-word split count in each

Run:  .venv/bin/python code/review_terms.py [--fy 2027|2026|2025|2024] [--out DIR] [--no-ink]
"""
import argparse
import collections
import csv
import os
import re
import sys
import tomllib

import pdfplumber

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from review_capital_sd import Review, render_gray, ink_regions, sha256, SCALE  # noqa: E402

CONFIG_DIR = os.path.join(REPO, "config", "terms")


def configure(fy):
    """Load config/terms/fy<fy>.toml and set the module's per-year globals."""
    global CFG, FY, TAG, PREFIX, PDF, PDF_SHA256, OLD_CSV, OUT, FURNITURE_RE
    with open(os.path.join(CONFIG_DIR, f"fy{fy}.toml"), "rb") as f:
        CFG = tomllib.load(f)
    FY = CFG["fiscal_year"]
    TAG = f"fy{FY}"
    PREFIX = CFG["prefix"]
    PDF = os.path.join(REPO, CFG["pdf"])
    PDF_SHA256 = CFG["sha256"]
    OLD_CSV = os.path.join(REPO, CFG["old_csv"])
    OUT = os.path.join(REPO, CFG["review_dir"])
    FURNITURE_RE = re.compile(CFG["furniture"]["pattern"])


configure(2027)

HEAD_RE = re.compile(r"^(\d+)\.\s+(.+?)\s*\((\d{3})\)$")
AGENCY_RE = re.compile(r"^(.+?)\s*\(\s?(\d{3})\)$")            # FY2024: "( 128)"
# FY2026 #5, #7: "Units of"; FY2024 "[ 003]", "[ 020 ]", "Unit of appropriation [101]".
UOA_RE = re.compile(r"^Units? of [Aa]ppropriation \[\s?([^\]]+?)\s?\]$")
BL_RE = re.compile(r"^Budget Line (.+)$")
DATE_RE = re.compile(r"(?:January|February|March|April|May|June|July|August|September|October|"
                     r"November|December) \d{1,2}, \d{4}")


def is_bold(ln):
    cs = [c for c in ln["chars"] if c["text"].strip()]
    return bool(cs) and all("Bold" in c["fontname"] for c in cs)


def page_lines(page, table_bboxes):
    """Text lines outside the tables, with their characters; furniture marked."""
    out = []
    for ln in page.extract_text_lines(return_chars=True):
        cx = (ln["x0"] + ln["x1"]) / 2
        cy = (ln["top"] + ln["bottom"]) / 2
        if any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in table_bboxes):
            continue
        ln["bold"] = is_bold(ln)
        fu = CFG["furniture"]
        ln["furniture"] = fu["top_min"] < ln["top"] < fu["top_max"] and \
            FURNITURE_RE.fullmatch(ln["text"].strip()) is not None
        out.append(ln)
    return out


def join_lines(texts, flags):
    """PLAN §5.2 join rule: a line ending in a hyphen not preceded by a space joins with no
    space (and is flagged wrap_hyphen); otherwise lines join with a space."""
    out = ""
    for t in texts:
        t = t.strip()
        if not out:
            out = t
        elif re.search(r"\S-$", out):
            flags.add("wrap_hyphen")
            out += t
        else:
            out += " " + t
    return out


def fsr_table(pdf, review, report):
    """T5 on the one ruled table. Returns rows and the table bboxes per page."""
    import numpy as np
    from ocr import grid
    rows, bboxes = [], collections.defaultdict(list)
    agree = disagree = 0
    for pno, page in enumerate(pdf.pages, 1):
        # FY2024 draws white boxes behind some headings (pp.11, 16, 18, 21) that pdfplumber reads
        # as tables; config table_pages names the pages that hold the real one.
        if "table_pages" in CFG and pno not in CFG["table_pages"]:
            continue
        for t in page.find_tables():
            bboxes[pno].append(t.bbox)
            # Vector lattice: distinct cell edges.
            vx = sorted({round(c[0], 1) for c in t.cells} | {round(c[2], 1) for c in t.cells})
            vy = sorted({round(c[1], 1) for c in t.cells} | {round(c[3], 1) for c in t.cells})
            # Image lattice on a crop of the table region, padded 8 px (PLAN §3 stage 4).
            gray = render_gray(PDF, pno)
            x0, y0, x1, y1 = (int(t.bbox[0] * SCALE) - 8, int(t.bbox[1] * SCALE) - 8,
                              int(t.bbox[2] * SCALE) + 8, int(t.bbox[3] * SCALE) + 8)
            crop = np.ascontiguousarray(gray[y0:y1, x0:x1])
            g = grid.detect_grid(crop, kernel_px=60)
            if g is None:
                review.add("T5.image_grid", "critical", pno, "no image lattice on the FSR table")
                continue
            ix = [(x + x0) / SCALE for x in g.xs]
            iy = [(y + y0) / SCALE for y in g.ys]
            miss_x = [x for x in vx if min(abs(x - i) for i in ix) > 2]
            miss_y = [y for y in vy if min(abs(y - i) for i in iy) > 2]
            extra_x = [i for i in ix if min(abs(x - i) for x in vx) > 2]
            extra_y = [i for i in iy if min(abs(y - i) for y in vy) > 2]
            report.append(f"T5 p.{pno}: vector {len(vx)} x / {len(vy)} y separators; image "
                          f"{len(ix)} x / {len(iy)} y; unmatched vector x{miss_x} y{miss_y}, "
                          f"image x{[round(v, 1) for v in extra_x]} y{[round(v, 1) for v in extra_y]}")
            for v in miss_x + miss_y + extra_x + extra_y:
                review.add("T5.lattice", "critical", pno, f"separator at {round(v, 1)} in one lattice only")
            # Cell strings under each lattice, characters assigned by centre (stage 5).
            def cells_by(xs, ys):
                cells = collections.defaultdict(list)
                for ch in page.chars:
                    cx, cy = (ch["x0"] + ch["x1"]) / 2, (ch["top"] + ch["bottom"]) / 2
                    if not (t.bbox[0] <= cx <= t.bbox[2] and t.bbox[1] <= cy <= t.bbox[3]):
                        continue
                    r = next((k for k in range(len(ys) - 1) if ys[k] <= cy < ys[k + 1]), None)
                    c = next((k for k in range(len(xs) - 1) if xs[k] <= cx < xs[k + 1]), None)
                    cells[(r, c)].append(ch)
                txt = {}
                for k, chs in cells.items():
                    # A character joins a line when it overlaps the line's height by half its
                    # own: FY2026's superscript ordinals ("October 2nd", p.8) sit ~3 pt high
                    # and would otherwise read as a line of their own ("nd October 2").
                    lines = []
                    for ch in sorted(chs, key=lambda c: (c["top"], c["x0"])):
                        h = ch["bottom"] - ch["top"]
                        ln = next((l for l in lines if min(l["bottom"], ch["bottom"]) -
                                   max(l["top"], ch["top"]) > h / 2), None)
                        if ln is None:
                            lines.append({"top": ch["top"], "bottom": ch["bottom"], "chars": [ch]})
                        else:
                            ln["chars"].append(ch)
                    txt[k] = "\n".join("".join(c["text"] for c in sorted(l["chars"], key=lambda c: c["x0"])).strip()
                                       for l in sorted(lines, key=lambda l: l["top"]))
                return txt
            tv, ti = cells_by(vx, vy), cells_by(ix, iy)
            for k in sorted(set(tv) | set(ti), key=lambda k: (k[0] or 0, k[1] or 0)):
                if tv.get(k) == ti.get(k):
                    agree += 1
                else:
                    disagree += 1
                    review.add("T5.cell_text", "critical", pno, f"cell {k}: vector {tv.get(k)!r} "
                               f"image {ti.get(k)!r}")
            for r in range(len(vy) - 1):
                cells = [tv.get((r, c), "") for c in range(len(vx) - 1)]
                if any(cells):
                    rows.append({"pdf_page": pno, "row": r, "cells_raw": cells})
    report.append(f"T5 FSR table cells: {agree} identical under both lattices, {disagree} differ")
    # Assemble: header on p.7, rows on pp.7-8. Cells keep their line breaks raw.
    out = []
    for r in rows:
        c = r["cells_raw"]
        if c[0].replace("\n", " ").startswith("FINANCIAL"):
            continue
        flags = set()
        clean = [join_lines(x.split("\n"), flags) for x in c]
        if any(re.search(r"\b(Su mmary|FY 2 0\d\d)\b", x) for x in clean):
            flags.add("midword_wrap_in_source")
        out.append({"pdf_page": r["pdf_page"], "financial_status_report": clean[0],
                    "report_content": clean[1], "issue_date": clean[2],
                    "anticipated_meeting_date": clean[3],
                    "report_content_raw": c[1], "flags": ";".join(sorted(flags))})
        if "midword_wrap_in_source" in flags:
            review.add("W.midword_wrap", "warn", r["pdf_page"],
                       f"the PDF wraps a word inside the cell: {c[1]!r} (kept as printed)",
                       field="report_content")
    return out, bboxes


def box_add(cond, pno, ln):
    """Grow the condition's box on page `pno` (one box per page it touches)."""
    b = cond.setdefault("boxes", {}).get(pno)
    nb = (ln["x0"], ln["top"], ln["x1"], ln["bottom"])
    cond["boxes"][pno] = nb if b is None else (min(b[0], nb[0]), min(b[1], nb[1]),
                                               max(b[2], nb[2]), max(b[3], nb[3]))


def parse(pdf, bboxes, review):
    conds, cur, mode = [], None, None
    emitted_lines = collections.defaultdict(list)
    for pno, page in enumerate(pdf.pages, 1):
        lines = page_lines(page, bboxes.get(pno, []))
        if pno == 1:
            for ln in lines:
                emitted_lines[pno].append(ln)        # cover: FISCAL NNNN / TERMS AND CONDITIONS
            continue
        for ln in lines:
            if ln["furniture"]:
                emitted_lines[pno].append(ln)
                continue
            text = ln["text"].strip()
            m = HEAD_RE.match(text) if ln["bold"] else None
            head = (int(m.group(1)), m.group(2), m.group(3)) if m else None
            # FY2024 prints no condition numbers: a bold agency line (or "Capital Budget") after
            # body text starts the next condition, numbered in page order (config numbered = false).
            # Some agency lines print no code ("Department of Transportation", "Mayoralty", p.16, 20).
            # One is printed in regular type but for its code (p.21 "Office of Criminal Justice
            # ( 128)"): a centred line that is exactly "Name (code)" counts too, and is flagged.
            unnumbered = not CFG.get("numbered", True)
            plain_head = unnumbered and not ln["bold"] and ln["x0"] > 100 and \
                AGENCY_RE.match(text) is not None
            if head is None and unnumbered and (ln["bold"] or plain_head) and mode != "head" and \
                    not (UOA_RE.match(text) or BL_RE.match(text)):
                a = AGENCY_RE.match(text)
                head = (len(conds) + 1, a.group(1) if a else text, a.group(2) if a else "")
            if head:
                cur = {"item_number": head[0], "page_start": pno, "page_end": pno,
                       "groups": [{"agency": head[1], "code": head[2], "uoas": [],
                                   "budget_lines": []}],
                       "heading_lines": [text], "body_lines": [], "flags": set()}
                if unnumbered and not ln["bold"]:
                    cur["flags"].add("heading_not_bold")
                    review.add("T2.heading_not_bold", "warn", pno, f"#{head[0]}: heading printed in "
                               f"regular type: {text}", field=str(head[0]))
                conds.append(cur)
                box_add(cur, pno, ln)
                mode = "head"
                emitted_lines[pno].append(ln)
                continue
            if cur is None:
                review.add("T4.before_first", "critical", pno, f"text before condition 1: {text}")
                continue
            cur["page_end"] = pno
            emitted_lines[pno].append(ln)
            box_add(cur, pno, ln)
            if ln["bold"] and mode == "head":
                cur["heading_lines"].append(text)
                u, b, a = UOA_RE.match(text), BL_RE.match(text), AGENCY_RE.match(text)
                lb = (pno, f"{ln['x0']:.2f},{ln['top']:.2f},{ln['x1']:.2f},{ln['bottom']:.2f}")
                if u:
                    cur["groups"][-1]["uoas"].append(u.group(1))
                    cur["groups"][-1].setdefault("uoa_boxes", []).append(lb)
                elif b:
                    cur["groups"][-1]["budget_lines"].append(b.group(1))
                    cur["groups"][-1].setdefault("bl_boxes", []).append(lb)
                elif a and unnumbered and not cur["groups"][-1]["code"] and \
                        not cur["groups"][-1]["uoas"] and not cur["groups"][-1]["budget_lines"]:
                    # An agency name wrapped onto a second line (FY2024 p.23: "Office of
                    # Technological Innovation/Department of Information Telecommunication" /
                    # "Services (858)").
                    g = cur["groups"][-1]
                    g["agency"], g["code"] = f"{g['agency']} {a.group(1)}", a.group(2)
                    cur["flags"].add("agency_name_wrapped")
                elif a:
                    cur["groups"].append({"agency": a.group(1), "code": a.group(2), "uoas": [],
                                          "budget_lines": []})
                elif unnumbered and not re.search(r"[\[\]()]", text):
                    # A later agency printed with no code (p.16: DCAS, Parks), or "Capital Budget"
                    # after an agency's units (p.14).
                    cur["groups"].append({"agency": text, "code": "", "uoas": [], "budget_lines": []})
                else:
                    review.add("T2.heading_line", "critical", pno, f"unknown heading line: {text}",
                               field=str(cur["item_number"]))
                continue
            if ln["bold"] and mode == "body":
                cur["flags"].add("bold_in_body")
                review.add("T4.bold_in_body", "warn", pno, f"#{cur['item_number']}: bold line "
                           f"inside the body: {text}")
            mode = "body"
            cur["body_lines"].append({"text": ln["text"], "x0": ln["x0"], "pdf_page": pno,
                                      "top": ln["top"]})
    # A table belongs to the condition open at its top edge: the last condition with a line
    # above it on its page, else the last condition started on an earlier page (#15, pp.7-8).
    for pno, tbs in bboxes.items():
        for tb in tbs:
            above = [c for c in conds for ln in c["body_lines"] + c.get("head_tops", [])
                     if ln["pdf_page"] == pno and ln["top"] < tb[1]]
            owner = above[-1] if above else ([c for c in conds if c["page_start"] < pno] or [None])[-1]
            if owner is None:
                review.add("T4.table_owner", "critical", pno, "table before any condition")
                continue
            owner.setdefault("tables", []).append(pno)
            bx = owner.setdefault("boxes", {}).get(pno)
            owner["boxes"][pno] = tb if bx is None else (min(bx[0], tb[0]), min(bx[1], tb[1]),
                                                         max(bx[2], tb[2]), max(bx[3], tb[3]))
            owner["page_end"] = max(owner["page_end"], pno)
    return conds, emitted_lines


def body_sentence_check(c, review):
    """T3: units and budget lines named in the opening clause vs the heading."""
    # FY2026 prints budget lines with U+2010 (`HD‐0009`); compared as ASCII, kept as printed.
    body = " ".join(l["text"] for l in c["body_lines"]).replace("\u2010", "-")
    head_u = sorted({u for g in c["groups"] for u in g["uoas"] if u != "All"})
    head_b = sorted({b.split(" ")[0].replace("–", "").replace("\u2010", "-").strip()
                     for g in c["groups"] for b in g["budget_lines"]})
    # Every "unit(s) of appropriation number(s) ..." list and "budget line(s) ..." list in the
    # body (a multi-agency condition has one "As a condition ..." sentence per agency, #73).
    named_u, named_b = set(), set()
    # "numbers" is optional: FY2026 writes "units of appropriation 401, 402, ..." (#16).
    for lst in re.findall(r"units? of appropriation (?:numbers? )?((?:\d{3}(?:,? and |, | )?)+)", body):
        named_u.update(re.findall(r"\d{3}", lst))
    for lst in re.findall(r"budget lines? ((?:[A-Z]{1,3}-\d{3,4}[A-Z]?(?:,? and |, | )?)+)", body):
        named_b.update(re.findall(r"[A-Z]{1,3}-\d{3,4}[A-Z]?", lst))
    # "100, 101, and 200 for DHS; 001 and 014 for HPD; ..." (#64, #75): every 3-digit number
    # between a unit list's start and the next " shall ".
    for span in re.findall(r"units? of appropriation (?:numbers? )?(.+?) shall ", body):
        named_u.update(re.findall(r"(?<![-\d])\b(\d{3})\b(?!-)", span))
    m = re.search(r"As a condition of", body)
    clause = body
    named_u, named_b = sorted(named_u), sorted(named_b)
    all_units = any(u == "All" for g in c["groups"] for u in g["uoas"])
    ok_u = named_u == head_u or (all_units and not named_u and "all" in clause.lower())
    ok_b = named_b == head_b or not head_b and not named_b
    if not m:
        c["flags"].add("no_opening_clause")
    if not (ok_u and ok_b):
        review.add("T3.body_vs_heading", "warn", c["page_start"],
                   f"#{c['item_number']}: heading units {head_u} lines {head_b}; body "
                   f"names units {named_u} lines {named_b}", field=str(c["item_number"]),
                   expected=";".join(head_u + head_b), observed=";".join(named_u + named_b))
    return ok_u and ok_b


def split_words(texts, vocab):
    """Adjacent tokens whose join is a word in `vocab` and whose halves are not."""
    n = 0
    for t in texts:
        toks = re.findall(r"[A-Za-z]+", t)
        for a, b in zip(toks, toks[1:]):
            if (a + b).lower() in vocab and a.lower() not in vocab and b.lower() not in vocab:
                n += 1
    return n


def run(out_dir=None, do_ink=True, fy=None):
    if fy is not None:
        configure(fy)
    out_dir = out_dir or OUT
    assert sha256(PDF) == PDF_SHA256, "H1: not the PDF this config was written for"
    os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)
    review = Review(tag=TAG)
    report = [f"FY{FY} Terms and Conditions: checks", f"pdf: {os.path.relpath(PDF, REPO)}",
              f"sha256: {PDF_SHA256}", ""]
    with pdfplumber.open(PDF) as pdf:
        pages = []
        for n, p in enumerate(pdf.pages, 1):
            pages.append({"pdf_page": n, "rotate": p.rotation, "width": round(float(p.width)),
                          "height": round(float(p.height)), "chars": len(p.chars),
                          "rects": len(p.rects), "lines": len(p.lines), "images": len(p.images),
                          "tables": len(p.find_tables()),
                          "kind": "cover" if n == 1 else "conditions"})
        fsr, bboxes = fsr_table(pdf, review, report)
        conds, emitted = parse(pdf, bboxes, review)

        # Agency lines printed with no code (FY2024 p.16 DOT, DCAS, Parks; p.18 DYCD; p.20
        # Mayoralty): kept as printed, code blank, flagged.
        for c in conds:
            for g in c["groups"]:
                if not g["code"] and not g["agency"].startswith("Capital Budget"):
                    c["flags"].add("agency_code_not_printed")
                    review.add("T2.no_agency_code", "warn", c["page_start"],
                               f"#{c['item_number']}: '{g['agency']}' is printed with no agency code",
                               field=str(c["item_number"]))

        # T1 numbering.
        nums = [c["item_number"] for c in conds]
        gaps = sorted(set(range(1, max(nums) + 1)) - set(nums))
        dups = [k for k, v in collections.Counter(nums).items() if v > 1]
        report.append(f"T1 numbered conditions: {len(conds)}; run 1..{max(nums)}; gaps {gaps}; "
                      f"repeats {dups}; in order: {nums == sorted(nums)}")
        if not CFG.get("numbered", True):
            # No printed numbers to check: count the paragraphs that open a condition instead.
            opens = sum(1 for p in pdf.pages[1:] for l in p.extract_text_lines()
                        if l["x0"] < 80 and l["text"].startswith("As a condition"))
            report.append(f"   the PDF prints no numbers (item_number = order in the book); "
                          f"paragraphs opening 'As a condition' at the left margin: {opens}")
            if opens != len(conds):
                review.add("T1.numbering", "critical", "", f"{len(conds)} headings but {opens} "
                           "'As a condition' paragraphs")
        for g in gaps:
            review.add("T1.numbering", "critical", "", f"condition {g} missing")
        for d in dups:
            review.add("T1.numbering", "critical", "", f"condition {d} printed twice")

        # T2 independent census of unit / budget-line lines over the raw page text.
        census = collections.Counter()
        for n, p in enumerate(pdf.pages, 1):
            for line in (p.extract_text() or "").splitlines():
                line = line.strip()
                if UOA_RE.match(line) or BL_RE.match(line):
                    census[line] += 1
        got = collections.Counter(l for c in conds for l in c["heading_lines"]
                                  if UOA_RE.match(l) or BL_RE.match(l))
        report.append(f"T2 unit/budget-line heading lines: page text {sum(census.values())}, in "
                      f"conditions {sum(got.values())}, difference {dict((census - got) + (got - census))}")
        n_uoa = sum(v for k, v in census.items() if UOA_RE.match(k))
        report.append(f"   of which 'Unit of Appropriation' lines: {n_uoa}")

        # T3 opening clause vs heading.
        ok = sum(body_sentence_check(c, review) for c in conds)
        report.append(f"T3 body names exactly the heading's units and lines: {ok}/{len(conds)}")

        # T4 character conservation.
        lost = 0
        for n, p in enumerate(pdf.pages, 1):
            seen = {id(ch) for ln in emitted[n] for ch in ln["chars"]}
            inside_tables = {id(ch) for ch in p.chars for b in bboxes.get(n, [])
                             if b[0] <= (ch["x0"] + ch["x1"]) / 2 <= b[2]
                             and b[1] <= (ch["top"] + ch["bottom"]) / 2 <= b[3]}
            # extract_text_lines builds new char dicts; compare by position and text instead.
            keyset = {(round(ch["x0"], 2), round(ch["top"], 2), ch["text"])
                      for ln in emitted[n] for ch in ln["chars"]}
            for ch in p.chars:
                if not ch["text"].strip() or id(ch) in inside_tables:
                    continue
                if (round(ch["x0"], 2), round(ch["top"], 2), ch["text"]) not in keyset:
                    lost += 1
                    review.add("T4.char_lost", "critical", n, f"character not emitted: {ch['text']!r} "
                               f"at {round(ch['x0'])},{round(ch['top'])}")
        report.append(f"T4 characters outside furniture and tables not in any condition: {lost}")

        # T6 ink.
        if do_ink:
            regions = 0
            for n, p in enumerate(pdf.pages, 1):
                words = []
                for i, ln in enumerate(emitted[n]):
                    words.append({"wid": i, "chars": ln["chars"]})
                k = len(words)
                for b in bboxes.get(n, []):
                    words.append({"wid": k, "chars": [ch for ch in p.chars
                                  if b[0] <= (ch["x0"] + ch["x1"]) / 2 <= b[2]
                                  and b[1] <= (ch["top"] + ch["bottom"]) / 2 <= b[3]]})
                    k += 1
                regs, _ = ink_regions(render_gray(PDF, n), words, {w["wid"] for w in words}, p)
                regions += len(regs)
                for rg in regs:
                    review.add("T6.ink", "critical", n, f"uncovered ink {rg['ink_px']} px at {rg['bbox_pt']}")
            report.append(f"T6 ink coverage: {len(pdf.pages)} pages, {regions} uncovered regions")
        else:
            report.append("T6: not run (--no-ink)")

    # Rows.
    rows = []
    for c in conds:
        flags = set(c["flags"])
        text = join_lines([l["text"] for l in c["body_lines"]], flags)
        kinds = {"capital" if g["agency"].startswith("Capital Budget") or g["budget_lines"] else "expense"
                 for g in c["groups"]}
        rows.append({
            "item_number": c["item_number"], "page_start": c["page_start"], "page_end": c["page_end"],
            "kind": "+".join(sorted(kinds)),
            "agency_name": "; ".join(g["agency"] for g in c["groups"]),
            "agency_code": "; ".join(g["code"] for g in c["groups"]),
            "units_of_appropriation": "; ".join(f"{g['code']}:{u}" for g in c["groups"] for u in g["uoas"]),
            "num_units": sum(len(g["uoas"]) for g in c["groups"]),
            "budget_lines": "; ".join(b for g in c["groups"] for b in g["budget_lines"]),
            "dates_mentioned": "; ".join(dict.fromkeys(DATE_RE.findall(text))),
            "report_deadlines": "; ".join(dict.fromkeys(
                re.findall(r"no later than (" + DATE_RE.pattern + ")", text))),
            "page_boxes": "|".join(f"{p}:{b[0]:.2f},{b[1]:.2f},{b[2]:.2f},{b[3]:.2f}"
                                   for p, b in sorted(c.get("boxes", {}).items())),
            "heading_raw": "\n".join(c["heading_lines"]),
            "condition_text": text,
            "condition_text_raw": "\n".join(l["text"] for l in c["body_lines"]),
            "flags": ";".join(sorted(flags)),
            "pdf_sha256": PDF_SHA256})
    vocab = {w.lower() for r in rows for w in re.findall(r"[A-Za-z]+", r["condition_text"])}

    # T7 against the retired CSV.
    with open(OLD_CSV, newline="", encoding="utf-8") as f:
        old = list(csv.DictReader(f))
    oby = {int(o["item_number"]): o for o in old}
    squash = lambda s: re.sub(r"\s+", "", s)
    same_text = same_agency = 0
    for r in rows:
        o = oby.get(r["item_number"])
        if not o:
            review.add("T7.old_csv", "warn", r["page_start"], f"#{r['item_number']} not in the old CSV")
            continue
        if squash(o["condition_text"]) == squash(r["condition_text"]):
            same_text += 1
        else:
            a, b = squash(o["condition_text"]), squash(r["condition_text"])
            k = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
            review.add("T7.old_csv_text", "warn", r["page_start"],
                       f"#{r['item_number']}: text differs from the old CSV at char {k}: "
                       f"old ...{a[max(0, k - 30):k + 40]!r} new ...{b[max(0, k - 30):k + 40]!r}",
                       field=str(r["item_number"]))
        if o["agency_name"].split(";")[0].strip() == r["agency_name"].split(";")[0].strip() and \
                o["agency_code"].split(";")[0].strip() == r["agency_code"].split(";")[0].strip():
            same_agency += 1
        else:
            review.add("T7.old_csv_agency", "warn", r["page_start"],
                       f"#{r['item_number']}: agency old '{o['agency_name']}' ({o['agency_code']}) "
                       f"new '{r['agency_name']}' ({r['agency_code']})", field=str(r["item_number"]))
        old_u = sorted(u.strip() for u in o["units_of_appropriation"].split(";") if u.strip())
        new_u = sorted(u.split(":")[1] for u in r["units_of_appropriation"].split("; ") if u)
        if old_u != new_u:
            review.add("T7.old_csv_units", "warn", r["page_start"],
                       f"#{r['item_number']}: units old {old_u} new {new_u}", field=str(r["item_number"]))
    report.append(f"T7 old CSV: {len(old)} rows, new {len(rows)}; first agency equal {same_agency}; "
                  f"text equal ignoring whitespace {same_text}")
    report.append(f"   mid-word splits (join is a word in the new text, halves are not): old "
                  f"{split_words([o['condition_text'] for o in old], vocab)}, new "
                  f"{split_words([r['condition_text'] for r in rows], vocab)}")
    nh = sum(1 for r in rows if "wrap_hyphen" in r["flags"])
    report.append(f"W wrap_hyphen joins (line ended in a hyphen; joined with none): {nh} conditions")
    for r in rows:
        if "wrap_hyphen" in r["flags"]:
            review.add("W.wrap_hyphen", "warn", r["page_start"],
                       f"#{r['item_number']}: a line ends in a hyphen; joined without a space",
                       field=str(r["item_number"]))
    multi = [r for r in rows if ";" in r["agency_code"]]
    report.append(f"Conditions naming more than one agency: {[r['item_number'] for r in multi]}")
    report.append(f"Kinds: {dict(collections.Counter(r['kind'] for r in rows))}")

    d = os.path.join(out_dir, "data")
    with open(os.path.join(d, f"{PREFIX}_terms_conditions.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(d, f"{PREFIX}_terms_units.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_number", "agency_name", "agency_code", "unit_of_appropriation", "budget_line",
                    "pdf_page", "bbox_pt"])
        for c in conds:
            for g in c["groups"]:
                for u, (p, bx) in zip(g["uoas"], g.get("uoa_boxes", [])):
                    w.writerow([c["item_number"], g["agency"], g["code"], u, "", p, bx])
                for b, (p, bx) in zip(g["budget_lines"], g.get("bl_boxes", [])):
                    w.writerow([c["item_number"], g["agency"], g["code"], "", b, p, bx])
    with open(os.path.join(d, f"{PREFIX}_terms_fsr_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fsr[0]))
        w.writeheader()
        w.writerows(fsr)
    with open(os.path.join(d, f"{PREFIX}_terms_pages.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pages[0]))
        w.writeheader()
        w.writerows(pages)
    with open(os.path.join(d, f"{PREFIX}_terms_review.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=Review.COLS)
        w.writeheader()
        w.writerows(sorted(review.rows, key=lambda r: (r["severity"] != "critical", str(r["pdf_page"]))))
        if not review.rows:
            w.writerow({"check_id": "ok", "note": "all checks ran; nothing to review"})
    cnt = collections.Counter((r["check_id"], r["severity"]) for r in review.rows)
    report += ["", "review.csv by check:"] + [f"  {c:<22} {s:<8} {n}" for (c, s), n in sorted(cnt.items())]
    with open(os.path.join(d, f"{PREFIX}_terms_checks.txt"), "w") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))
    return rows, review


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--fy", type=int, default=2027, help="fiscal year (config/terms/fy<FY>.toml)")
    ap.add_argument("--out", default=None, help="output folder (default: the config's review_dir)")
    ap.add_argument("--no-ink", action="store_true")
    a = ap.parse_args()
    run(a.out, do_ink=not a.no_ink, fy=a.fy)
