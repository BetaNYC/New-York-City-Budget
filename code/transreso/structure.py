"""
Structure: chart captions, header roles and designation rows, by page position.

A chart page is: a caption above the table (`CHART #n: <title> - Fiscal YYYY`, with
"(continued)" on later pages), the table (header row, then one designation change per row),
then footnotes and a `Page n` label below it. Fiscal year and initiative are chart-level, so
every row carries its chart's. Values are kept as printed (`*_raw`); the clean value only joins
lines (schedc.structure.clean_text) and, for the organization, takes the trailing `**` / `***`
marker into its own column.

Nothing on a row says "transfer": a rescission prints in parentheses (and red), a designation
without. A row with a blank member cell is the agency side of a transfer (DESIGN: family
assessment §1.2 E4); it is never filled from the row above.
"""
import re

from schedc.structure import clean_text

# Printed header label -> role. A label not listed here is a T4 flag.
LABELS = {
    "Member": "member", "Borough": "member", "Borough/Member": "member", "Source": "source",
    "Member/Borough": "member",                                    # FY2025 Reso 08 p.12
    "Organization - Program": "org", "Organization": "org", "EIN Number": "ein",
    "Organization - School": "org",                                # FY2020 Reso 03 p.58
    "Agency": "agency", "Amount": "amount", "Agy #": "agy", "U/A": "ua", "*": "prequal",
    "Purpose of Funds": "purpose", "New Purpose of Funds": "purpose",
}
REQUIRED = {"org", "ein", "agency", "amount"}
# "- Fiscal YYYY" closes the caption; Reso 07 p.12 prints "Assistance- Fiscal 2026" (no space).
# FY2025 Reso 11 p.6 prints "CHART #4 Anti-Poverty" with no colon (flagged W.caption_format).
# FY2023 prints "CHART 41:" (no "#", Reso 01 p.81), "- FY 2023" for "- Fiscal 2023" (Reso 01
# p.66, Reso 09 pp.21-25) and "(cpntinued)" (Reso 03 p.20); each is read and flagged
# W.caption_format.
CAPTION = re.compile(r"^CHART #?(\d*):?\s*(.*?)(?:\s*-\s+(?:Fiscal|FY) (\d{4}))?"
                     r"(\s*\(c[a-z]ntinued\))?$")
PAGE_LABEL = re.compile(r"^Page\s(\d+)$")   # FY2024 Reso 01: "Page\xa01" (no-break space)
# FY2022 Reso 03 chart #48 prints cents, always ".00" ("$20,290.00"); read as whole dollars.
AMOUNT = re.compile(r"^(\()?\$(\d{1,3}(?:,\d{3})*)(\.00)?(\))?$")
EIN_HYPHEN = re.compile(r"^\d{2}-\d{7}$")
EIN_PLAIN = re.compile(r"^\d{9}$")
MARKER = re.compile(r"\s*(\*{1,3})$")
FOOTNOTES = {
    "*": ("* Indicates pending completion of pre-qualification review.",
          "*Indicates pending completion of pre-qualification review."),           # FY2022
    "**": ("** Requires a budget modification for the changes to take effect",),
    "***": ("*** Correction to designation listed in Schedule C and/or subsequent T",
            "*** Correction and/or Reversal of a change made in a previous Transparency",   # FY2023
            "*** Technical adjustment to designation made in a previous Transparency"),     # FY2021
}


def footnote_of(line):
    """The marker whose footnote this printed line is, or None."""
    return next((k for k, vs in FOOTNOTES.items() if any(line.startswith(v) for v in vs)), None)
# FY2020 caption variants, rewritten before CAPTION is matched (each flagged W.caption_format):
# "Chart #35:" (Reso 01 pp.70-80), "Chart # 44:" (Reso 03 pp.73-87) and "SU-CASA (continued) -
# Fiscal 2020" (Reso 05 pp.32-33, Reso 06 pp.17-18). "CHART #:" with no number (Reso 06
# pp.25-26) matches CAPTION with an empty number.
CAPTION_FIXES = [
    (re.compile(r"^Chart\b"), "CHART", "'Chart' for 'CHART'"),
    (re.compile(r"^CHART # (?=\d)"), "CHART #", "a space after '#'"),
    (re.compile(r"\s*(\(c[a-z]ntinued\))(\s*-\s+(?:Fiscal|FY) \d{4})$"), r"\2 \1",
     "'(continued)' before the fiscal year"),
]


def normalise_caption(cap):
    """(caption as CAPTION expects it, [what was rewritten])."""
    fixes = []
    for rx, to, what in CAPTION_FIXES:
        new = rx.sub(to, cap, count=1)
        if new != cap:
            cap = new
            fixes.append(what)
    return cap, fixes


CITY_EIN = "136400434"


def parse_amount(s):
    """'$5,000' -> 5000, '($5,000)' -> -5000; anything else -> None."""
    m = AMOUNT.match(s.strip())
    if not m or bool(m.group(1)) != bool(m.group(4)):
        return None
    v = int(m.group(2).replace(",", ""))
    return -v if m.group(1) else v


def parse_ein(s):
    """Printed EIN -> (9 digits or '', format). Formats: hyphen, no_hyphen, blank, odd."""
    t = s.strip()
    if not t:
        return "", "blank"
    if EIN_HYPHEN.match(t):
        return t.replace("-", ""), "hyphen"
    if EIN_PLAIN.match(t):
        return t, "no_hyphen"
    return "", "odd"


def caption_of(page, table):
    """Caption lines above the table, joined; and footer lines below it."""
    top = table["bbox"][1]
    above = [ln for ln in page["lines"] if ln["bottom"] <= top]
    below = [ln for ln in page["lines"] if ln["top"] >= table["bbox"][3]]
    return " ".join(ln["text"] for ln in above).strip(), below


def build(res, pages, x_tolerance, doc_fy=2026, renumber=None):
    """One resolution's pages -> dict(rows, charts, flags, page_info). `doc_fy` is the document year
    (the row id prefix). `renumber` = {pdf_page: (printed, read_as)}: captions that print the
    wrong chart number (T3.chart_number, named exceptions in the config; FY2019 Reso 01 p.108)."""
    renumber = renumber or {}
    rows, charts, flags, info, empty, chart_notes = [], {}, [], [], [], []
    seq = res["seq"]

    def flag(check, page, msg, severity="critical", **kw):
        flags.append(dict(check_id=check, severity=severity, resolution_seq=seq, pdf_page=page,
                          message=msg, **kw))

    prev_chart = None
    for p in pages:
        pi = dict(resolution_seq=seq, pdf_page=p["page"], tables=len(p["tables"]), caption="",
                  chart_number="", continued="", page_label="", footnotes="", rows=0,
                  width=p["width"], height=p["height"], rotation=p["rotation"])
        info.append(pi)
        if not p["tables"]:
            continue
        if len(p["tables"]) != 1:
            flag("T3.charts", p["page"], f"{len(p['tables'])} tables on one chart page")
        t = p["tables"][0]
        cap, below = caption_of(p, t)
        norm, fixes = normalise_caption(cap)
        m = CAPTION.match(norm)
        pi["caption"] = cap
        if not m:
            flag("T3.charts", p["page"], f"no chart caption above the table: {cap[:80]!r}")
            continue
        num, title, fy, cont = (int(m.group(1)) if m.group(1) else None), m.group(2), m.group(3), \
            bool(m.group(4))
        pi.update(chart_number=num if num is not None else "", continued=int(cont))
        if fixes:
            flag("W.caption_format", p["page"], f"caption prints {' and '.join(fixes)}: "
                 f"{cap[:80]!r}; read as chart #{num}{' (continued)' if cont else ''}",
                 severity="warn", chart_number=num)
        elif num is None:
            pass                                    # T3.continued_number below, or T3.charts
        elif res.get("caption_no_hash") and cap.startswith(f"CHART {m.group(1)}:"):
            pass                                    # FY2019: "CHART 1:" is the resolution's style
        elif not cap.startswith(f"CHART #{m.group(1)}:"):
            what = ("no '#' before" if not cap.startswith("CHART #") else "no ':' after")
            flag("W.caption_format", p["page"], f"caption prints {what} the chart number: "
                 f"{cap[:80]!r}; read as chart #{num}", severity="warn", chart_number=num)
        elif fy and not re.search(r"-\s+Fiscal \d{4}", cap) or cont and "(continued)" not in cap:
            flag("W.caption_format", p["page"], f"caption prints "
                 f"{'FY YYYY for Fiscal YYYY' if fy and 'Fiscal' not in cap else 'a misspelt (continued)'}: "
                 f"{cap[:80]!r}; read as chart #{num}, Fiscal {fy}"
                 f"{' (continued)' if cont else ''}", severity="warn", chart_number=num)
        if p["page"] in renumber and num == renumber[p["page"]][0]:
            # FY2019 Reso 01 p.108: the first page of chart #56 (Purpose of Funds Changes - Fiscal
            # 2018) prints "CHART 55:"; its later pages print 56. Named exception only.
            flag("T3.chart_number", p["page"], f"caption prints chart #{num}, read as chart "
                 f"#{renumber[p['page']][1]} (named exception in the config): {cap[:80]!r}",
                 severity="warn", chart_number=renumber[p["page"]][1])
            num = renumber[p["page"]][1]
        labels = [ln["text"] for ln in below]
        pl = [int(PAGE_LABEL.match(x).group(1)) for x in labels if PAGE_LABEL.match(x)]
        pi["page_label"] = pl[0] if len(pl) == 1 else ""
        notes = sorted({footnote_of(x) for x in labels} - {None})
        pi["footnotes"] = " ".join(notes)
        other = [x for x in labels if not PAGE_LABEL.match(x) and not footnote_of(x)]
        # Footnote 3 wraps onto a second line ("…Transparency Resolution(s)"); anything else
        # below a table is unexpected text and goes to review.
        other = [x for x in other if not ("***" in notes and x.startswith("Resolution"))]

        if cont and num is not None and num not in charts and \
                (prev_chart or {}).get("chart_number") == num - 1:
            # FY2023 Reso 08 p.32: the first page of chart #25 prints "(continued)". Read as the
            # start of the chart; allowed only as a named exception (T3.continued_start).
            flag("T3.continued_start", p["page"], f"first page of chart #{num} prints "
                 f"'(continued)': {cap[:80]!r}; read as the start of the chart", severity="warn",
                 chart_number=num)
            cont = False
        same = prev_chart and prev_chart["title"] == title and prev_chart["fy_printed"] == (fy or "")
        if cont and same and prev_chart["chart_number"] != num:
            # FY2022 Reso 07 p.34: "CHART #21: Purpose of Funds Changes (continued)" under chart #22
            # of the same title and year. Read as continuing it; named exception only.
            # FY2020 Reso 06 pp.25-26 print "CHART #:" with no number; the same rule applies.
            flag("T3.continued_number", p["page"], f"'(continued)' caption prints chart "
                 f"{'#' + str(num) if num is not None else 'with no number'}, "
                 f"but continues chart #{prev_chart['chart_number']} (same title and year): "
                 f"{cap[:80]!r}; read as chart #{prev_chart['chart_number']}", severity="warn",
                 chart_number=prev_chart["chart_number"])
            num = prev_chart["chart_number"]
        elif not cont and same and prev_chart["chart_number"] == num:
            # FY2022 Reso 01 pp.51-54, Reso 02 p.35: the caption repeats without "(continued)".
            # Read as continuing the chart; named exception only.
            flag("T3.continued_missing", p["page"], f"caption repeats chart #{num} without "
                 f"'(continued)': {cap[:80]!r}; read as its continuation", severity="warn",
                 chart_number=num)
            cont = True
        if num is None:
            flag("T3.charts", p["page"], f"caption prints no chart number: {cap[:80]!r}")
            continue
        if cont:
            if not prev_chart or prev_chart["chart_number"] != num or prev_chart["title"] != title \
                    or prev_chart["fy_printed"] != (fy or ""):
                flag("T3.charts", p["page"], f"'(continued)' caption does not continue the "
                     f"previous page's chart: {cap[:80]!r}")
            ch = charts.get(num)
        else:
            if num in charts:
                flag("T3.charts", p["page"], f"chart #{num} starts twice")
            ch = charts[num] = dict(resolution_seq=seq, chart_number=num, title=title,
                                    fy_printed=fy or "", first_page=p["page"], last_page=p["page"],
                                    pages=0, header="", kind="")
            if not fy:
                flag("T12.fiscal_year", p["page"], f"chart #{num} {title!r} prints no fiscal year",
                     severity="warn", chart_number=num)
        if ch is None:
            continue
        ch["last_page"] = p["page"]
        ch["pages"] += 1
        prev_chart = ch

        header = [h["label"] for h in t["header"]]
        roles = {j: LABELS.get(lb) for j, lb in enumerate(header)}
        # Some pages leave the last header cell blank where others print "*" (Reso 01 p.48,
        # Reso 04 p.3); the column is the same narrow pre-qualification column.
        if header and header[-1] == "" and roles.get(len(header) - 2) == "ua":
            roles[len(header) - 1] = "prequal"
        unknown = [header[j] for j, r in roles.items() if r is None]
        kind = "purpose_of_funds" if "purpose" in roles.values() else "designation"
        if not unknown and {"org", "ein"} <= set(roles.values()) and \
                not {"agency", "amount", "purpose"} & set(roles.values()):
            # FY2022 "Beating Hearts": a list of organizations with no agency and no amount, and
            # a note under the table saying what they get. Rows kept, amount blank; named
            # exception only (T4.no_amount). The note is not furniture.
            kind = "no_amount"
            chart_notes.append(dict(resolution_seq=seq, pdf_page=p["page"], lines=other))
            flag("T4.no_amount", p["page"], f"chart #{num} {title!r} prints no Agency or Amount "
                 f"column ({header}); rows kept with a blank amount. Its note: "
                 f"{' '.join(other)[:300]!r}", severity="warn", chart_number=num)
            other = []
        elif unknown or not REQUIRED <= set(roles.values()):
            flag("T4.headers", p["page"], f"header not recognised: {header}")
        for x in other:
            flag("T6.furniture", p["page"], f"unexpected text below the table: {x[:100]!r}")
        hdr_s = " | ".join(header)
        if ch["header"] and ch["header"] != hdr_s:
            ch.setdefault("header_variants", set()).add(hdr_s)
        ch["header"] = ch["header"] or hdr_s
        ch["kind"] = kind

        for r in t["rows"]:
            if not any(c["text_raw"] or c["hidden"] for c in r["cols"].values()):
                # A drawn row with nothing printed in it (FY2023 Reso 01 p.67, Reso 03 p.83,
                # Reso 06 p.53): not a change. Counted, not kept.
                empty.append(dict(resolution_seq=seq, pdf_page=p["page"], row_index=r["row_index"]))
                continue
            raw = {roles[int(j)]: c["text_raw"] for j, c in r["cols"].items() if roles.get(int(j))}
            red = {roles[int(j)]: c["red"] for j, c in r["cols"].items() if roles.get(int(j))}
            nchars = {roles[int(j)]: c["nchars"] for j, c in r["cols"].items() if roles.get(int(j))}
            how = {roles[int(j)]: c["how"] for j, c in r["cols"].items() if roles.get(int(j))}
            hidden = {roles[int(j)]: c["hidden"] for j, c in r["cols"].items()
                      if roles.get(int(j)) and c["hidden"]}
            row_flags = list(r["flags"])
            rec = dict(row_id=f"fy{doc_fy % 100:02d}-tr{seq:02d}-p{p['page']:03d}-r{r['row_index']:03d}",
                       resolution_seq=seq, pdf_page=p["page"], table_index=t["table_index"],
                       row_index=r["row_index"], bbox_pt=r["bbox"], chart_number=num,
                       chart_title=title, budget_fiscal_year=int(fy) if fy else "",
                       chart_kind=kind, member_header=next(
                           (header[j] for j, ro in roles.items() if ro == "member"), ""),
                       purpose_header=next(
                           (header[j] for j, ro in roles.items() if ro == "purpose"), ""),
                       _raw=raw, _char_boxes=[b for c in r["cols"].values() for b in c["char_boxes"]],
                       _how=how, _hidden=hidden)
            rec["hidden_text"] = "; ".join(f"{k}: {v}" for k, v in sorted(hidden.items()))
            if hidden:
                row_flags.append("clipped_text:" + "+".join(sorted(hidden)))
            rules = []
            for f in ("source", "member", "org", "agency", "purpose"):
                v, ru = clean_text(raw.get(f, ""))
                rec[f + "_raw"] = raw.get(f, "")
                rec[f] = v
                rules += [f"{x}:{f}" for x in ru]
            mk = MARKER.search(rec["org"])
            rec["org_marker"] = mk.group(1) if mk else ""
            if mk:
                rec["org"] = rec["org"][:mk.start()].rstrip()
            rec["budget_modification"] = int(rec["org_marker"] == "**")
            rec["correction"] = int(rec["org_marker"] == "***")
            # The "*" may sit in its own column or at the end of the organization text (Reso 03
            # p.2 row 18); either way the footnote says it marks pending pre-qualification.
            rec["prequal_pending"] = int(raw.get("prequal", "").strip() == "*" or
                                         rec["org_marker"] == "*")
            rec["prequal_printed"] = raw.get("prequal", "")
            rec["ein_printed"] = raw.get("ein", "")
            rec["ein"], rec["ein_format"] = parse_ein(rec["ein_printed"])
            rec["amount_printed"] = raw.get("amount", "")
            rec["amount"] = parse_amount(rec["amount_printed"])
            rec["agy_num"] = raw.get("agy", "").strip()
            rec["ua"] = raw.get("ua", "").strip()
            a = rec["amount"]
            if kind == "no_amount":
                rec["action"] = "listed"
            elif kind == "purpose_of_funds":
                rec["action"] = "purpose_from" if (a or 0) < 0 else "purpose_to"
            else:
                rec["action"] = "rescind" if (a or 0) < 0 else "designate"
            # The City's own EIN with no member: the agency side of a transfer (money parked in,
            # or taken from, an agency pool), not an award to an organization.
            rec["agency_side"] = int(rec["ein"] == CITY_EIN and not rec["member"])
            rec["clean_rules_applied"] = ";".join(sorted(set(rules)))
            for ru in rules:
                if ru.startswith("wrap_hyphen"):
                    row_flags.append(ru)
            # Row-level checks recorded as flags.
            if not any(raw.values()):
                row_flags.append("empty_row")
            if rec["ein_format"] == "no_hyphen":
                row_flags.append("ein_no_hyphen")
            elif rec["ein_format"] in ("blank", "odd"):
                row_flags.append("ein_" + rec["ein_format"])
            if a is None and kind != "no_amount":
                row_flags.append("amount_unreadable")
            elif a == 0:
                row_flags.append("amount_zero")
            # Sign vs colour: a rescission prints red, a designation black (T10).
            n_amt, n_red = nchars.get("amount", 0), red.get("amount", 0)
            if a is not None and ((a < 0) != (n_red == n_amt and n_amt > 0) or 0 < n_red < n_amt):
                row_flags.append("sign_colour")
            if rec["prequal_printed"].strip() not in ("", "*"):
                row_flags.append("prequal_odd")
            if rec["org_marker"] == "*":
                row_flags.append("prequal_star_in_org")
            if rec["org_marker"] and rec["org_marker"] not in notes:
                row_flags.append("marker_without_footnote")
            rec["row_flags"] = row_flags
            rows.append(rec)
            pi["rows"] += 1

    return dict(rows=rows, charts=list(charts.values()), flags=flags, page_info=info,
                empty_rows=empty, chart_notes=chart_notes)
