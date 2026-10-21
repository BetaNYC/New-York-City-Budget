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

AMOUNT_RE = re.compile(r"^\$\s?(\d{1,3}(?:,\d{3})*)$")
EIN_RE = re.compile(r"^(\d{2}-\d{7}|\d{9})$")
MONEY_ANY = re.compile(r"\$\s?([\d,]+)")


def clean_text(raw):
    """Clean value from raw cell text. The only rules (PLAN §5.2):
    1. a line break after a hyphen that has no space before it joins with no space, and keeps
       the hyphen (`Home-⏎Delivered` -> `Home-Delivered`; flagged `wrap_hyphen`, because it
       could also be a split word);
    2. any other line break joins with one space;
    3. runs of whitespace collapse to one space; ends are trimmed.
    Returns (clean, rules_applied)."""
    rules = []
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


def table_kind(t, cfg):
    first = " | ".join(" ".join(c["text_raw"].split()) for c in t["rows"][0]["cells"]
                       if c["text_raw"].strip())
    if re.search(cfg["structure"]["award_header_re"], first):
        return "award"
    if first.startswith(cfg["structure"]["summary_title"]):
        return "summary"
    if re.search(r"\$[\d,]+$", first) and len(t["rows"]) >= 1 and \
            any(" ".join(c["text_raw"].split()) for c in t["rows"][0]["cells"][:3]):
        return "box"
    return "other"


def statement_kind(text, cfg):
    """Designation statement -> (kind, reserve, designated). Kinds come from config regexes."""
    t = " ".join(text.split())
    for st in cfg["statements"]:
        m = re.search(st["re"], t)
        if m:
            g = m.groupdict()
            num = lambda k: int(g[k].replace(",", "")) if g.get(k) else None
            return st["kind"], num("reserve"), num("designated")
    return "unknown", None, None


def build(pages, cfg):
    """Vector pages -> dict(categories, summary_lines, initiatives, awards, flags, events)."""
    s = cfg["structure"]
    labels = [(p, f) for p, f in s["header_labels"]]
    categories = set(cfg["categories"])
    sections = cfg["sections"]  # list of {name, title_re}
    flags = []

    def flag(check, severity, page, msg, **kw):
        flags.append(dict(check_id=check, severity=severity, pdf_page=page, message=msg, **kw))

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
    stmt_buf = None  # collecting a designation statement
    last_cols = None

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
            if text.startswith(s["statement_prefix"]):
                close_statement()
                stmt_buf = dict(page=pn, bottom=obj["bottom"],
                                lines=[text[len(s["statement_prefix"]):].strip()])
                continue
            # A statement continues only on the next text line directly below it on the same
            # page (12 pt leading; 6 pt slack). That keeps a page's running sub-heading (a
            # category name under the header, e.g. p.116) out of the statement before it.
            if stmt_buf is not None and pn == stmt_buf["page"] and \
                    -3 <= obj["top"] - stmt_buf["bottom"] <= 6 and \
                    not re.fullmatch(s["page_furniture_re"], text):
                stmt_buf["lines"].append(text)
                stmt_buf["bottom"] = obj["bottom"]
            continue

        t = obj
        if kind != "line":
            close_statement()
        if kind == "other":
            only = [c["text_raw"] for c in t["rows"][0]["cells"] if c["text_raw"].strip()]
            if len(t["rows"]) == 1 and len(only) == 1 and only[0] in categories:
                category, current = only[0], None
            continue
        if kind == "summary":
            for r in t["rows"][1:]:
                cells = [" ".join(c["text_raw"].split()) for c in r["cells"]]
                texts = [x for x in cells if x]
                if not texts or texts == ["Agency", "Initiative", "Amount"]:
                    continue
                amt = parse_amount(texts[-1])
                rec = dict(category=category, pdf_page=pn, table_index=t["table_index"],
                           row_index=r["row_index"], bbox_pt=[r["cells"][0]["bbox"][0], r["top"],
                                                              r["cells"][-1]["bbox"][2], r["bottom"]],
                           cells=texts, amount=amt, amount_printed=texts[-1])
                if amt is None:
                    flag("H10.summary_row", "critical", pn, f"summary row amount unreadable: {texts}")
                rec["is_total"] = texts[0].upper() == "TOTAL"
                if not rec["is_total"]:
                    rec["agency"] = texts[0] if len(texts) == 3 else ""
                    rec["initiative"] = texts[-2]
                summary.append(rec)
            continue
        if kind == "box":
            cells = [c for c in t["rows"][0]["cells"] if c["text_raw"].strip()]
            title_raw = cells[0]["text_raw"]
            amt_printed = " ".join(cells[-1]["text_raw"].split())
            # A long title wraps into the next row band of the black bar (p.44): any cell
            # aligned with the title cell that starts above the bottom of the amount cell
            # (which spans the whole bar) is part of the title.
            bar_bottom = cells[-1]["bbox"][3]
            for r in t["rows"][1:]:
                for c in r["cells"]:
                    if c["bbox"][0] == cells[0]["bbox"][0] and c["bbox"][1] < bar_bottom \
                            and c["text_raw"].strip():
                        title_raw += "\n" + c["text_raw"]
            title, _ = clean_text(title_raw)
            current = dict(initiative_id=len(initiatives) + 1, initiative=title,
                           initiative_raw=title_raw, category=category,
                           section=section, pdf_page=pn, table_index=t["table_index"],
                           amount=parse_amount(amt_printed), amount_printed=amt_printed,
                           bbox_pt=t["bbox"], statement="", statement_kind="none",
                           reserve=None, designated=None, n_rows=0, rows_sum=0)
            if current["amount"] is None:
                flag("H11.box", "critical", pn, f"box amount unreadable: {amt_printed!r}",
                     initiative=title)
            if category is None:
                flag("H3.category", "critical", pn, f"box before any category: {title}")
            initiatives.append(current)
            continue

        # award table
        hdr = t["rows"][0]
        cols, unknown = header_map(hdr, labels)
        if unknown:
            flag("H4.header", "critical", pn, f"unknown header label(s): {unknown}",
                 table_index=t["table_index"])
        fields = [f for f, _ in cols]
        if "ein" not in fields or "amount" not in fields or "org" not in fields:
            flag("H4.header", "critical", pn, f"award header lacks org/ein/amount: {fields}",
                 table_index=t["table_index"])
            continue
        last_cols = cols
        rows = t["rows"]
        for ri in range(1, len(rows)):
            r = rows[ri]
            rec = dict(pdf_page=pn, table_index=t["table_index"], row_index=r["row_index"],
                       section=section, category=category if section == "body" else "",
                       initiative=current["initiative"] if (current and section == "body") else "",
                       initiative_id=current["initiative_id"] if (current and section == "body") else "",
                       initiative_page=current["pdf_page"] if (current and section == "body") else "",
                       header=" | ".join(fields), row_flags=[])
            x0 = min(c["bbox"][0] for c in r["cells"])
            x1 = max(c["bbox"][2] for c in r["cells"])
            rec["bbox_pt"] = [x0, r["top"], x1, r["bottom"]]
            used = set()
            char_boxes = []
            for f, x in cols:
                cell, spanned = _cell_at(rows, ri, x)
                raw = cell["text_raw"] if cell else ""
                if cell is not None:
                    used.add(tuple(cell["bbox"]))
                    if spanned is None:
                        char_boxes += cell["char_boxes"]
                if spanned is not None and raw:
                    rec["row_flags"].append(f"spanning_cell:{f}")
                rec[f + "_raw"] = raw
            for c in r["cells"]:
                if tuple(c["bbox"]) not in used and c["text_raw"].strip():
                    rec["row_flags"].append("unmapped_cell")
                    flag("H7.unmapped", "critical", pn, f"text in a cell no header column claims: "
                         f"{c['text_raw'][:80]!r}", table_index=t["table_index"],
                         row_index=r["row_index"])
            rec["_char_boxes"] = char_boxes
            rec["_raw"] = {f: rec[f + "_raw"] for f in fields}
            if not any(rec[f + "_raw"].strip() for f in fields):
                rec["row_flags"].append("empty_row")
            awards.append(rec)
            if current and section == "body":
                current["n_rows"] += 1
    close_statement()

    # 2. Field cleaning and per-row validation.
    fy = cfg["fiscal_year"] % 100
    for rec in awards:
        rec["award_id"] = (f"fy{fy:02d}-p{rec['pdf_page']:03d}-t{rec['table_index']:02d}"
                           f"-r{rec['row_index']:03d}")
        applied = set()
        for f in ("member", "sponsor", "delegation", "org", "agency", "purpose"):
            if f + "_raw" in rec:
                rec[f], rules = clean_text(rec[f + "_raw"])
                applied.update(rules)
                if "wrap_hyphen" in rules:
                    rec["row_flags"].append(f"wrap_hyphen:{f}")
            else:
                rec[f], rec[f + "_raw"] = "", ""
        rec["clean_rules_applied"] = ";".join(sorted(applied))
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
        if rec["amount"] is None:
            rec["row_flags"].append("amount_unreadable")

    for ini in initiatives:
        ini["rows_sum"] = sum(a["amount"] or 0 for a in awards
                              if a["initiative_id"] == ini["initiative_id"])
    return dict(initiatives=initiatives, summary=summary, awards=awards, flags=flags,
                last_cols=last_cols)
