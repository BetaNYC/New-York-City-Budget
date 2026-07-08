#!/usr/bin/env python3
"""
Parser for the NYC Council 'Changes to the Executive Capital Budget Pursuant to Section 254
-- CAPITAL PROJECT DETAIL' supporting-detail PDFs (the "Supporting Detail Book"), for the
fiscal years whose PDF text layer pdfplumber extracts in clean reading order:
FY2020, FY2022, FY2023, FY2024.

Why a separate module from parse_capital.py / parse_capital_fy26.py
-------------------------------------------------------------------
The same logical document is emitted with a different text layer across years:

  * parse_capital.py reads the text with pypdf, whose extract_text() SCRAMBLES column order
    on these PDFs (amount / budget-line / sponsor tokens interleave, e.g.
    '0AG D001 RIVERA0 0236,000'), so its ROW regex never matches -> 0 projects. Verified on
    FY20/FY22/FY23/FY24.
  * parse_capital_fy26.py is a pdfplumber COORDINATE-clustering parser whose per-page column
    detection is anchored on FY2026's specific header labels ('SUB ID') and geometry; the
    FY20-FY24 pages use a different header ('PROJECT ID') and geometry, so page_columns()
    returns None -> 0 projects.
  * pdfplumber's own extract_text() DOES return these pages in clean reading order (verified),
    so a line + token parser is the simplest deterministic reader. Amounts are taken straight
    from the text tokens -- never model-transcribed.

Row layout (clean text)
-----------------------
    <PROJECT ID> <BUDGET LINE> <BORO> <TITLE...> <fy1> <fy2> <fy3> <fy4> [<SPONSOR...>]
e.g.
    AG CN001 AG D001 M SIROVICH CENTER ROOF REHAB 236,000 0 0 0 RIVERA

The four amount columns are the only run of >=4 consecutive numeric tokens in a row (titles
may contain an isolated number like 'I.S. 240', sponsors are surnames -- never numeric), so
they cleanly delimit the (uppercase) TITLE from the (uppercase) SPONSOR. Titles wrap onto
following lines; building/school codes appear as 'B:xxxx S:xxxx' on a wrap line.

  PROJECT ID column (CN/NC/CC/TA... number) -> budget_line   (matches the FY27 schema, where
  BUDGET LINE column (D/DN number)          -> sub_id         the left code is 'budget_line')

Reconciles per-agency FY1 sum + project count against the printed
'TOTALS FOR <agency> (N PROJECTS) <fy1> <fy2> <fy3> <fy4>' subtotal lines.

Emits the FY27 schema exactly:
  part, agency, budget_line, sub_id, boro, fy1, fy2, fy3, fy4, sponsor, title,
  building_code, school_code
"""
import re, csv, os, argparse, unicodedata
from collections import defaultdict
import pdfplumber

BORO_SET = set("MXKQRA")                  # M/X/K/Q/R + A (citywide / all boroughs)
# An amount token is 0-999 or comma-grouped thousands (incl. negative adjustments). NOT a
# malformed comma token like '4,' or '8,' -- those are title punctuation (e.g. 'NO. 4, 6, 7, 8')
# and must never be mistaken for the amount columns.
NUM = re.compile(r'^-?\d{1,3}(?:,\d{3})*$')
CODETOK = re.compile(r'^[A-Z0-9]{1,6}$')  # a code-column token, e.g. AG, CN001, D001, MA001, 0N381
PART = re.compile(r'^(I{1,3})\.$')
BS = re.compile(r'\bB[:;]\s*(\S+)|\bS[:;]\s*(\S+)')
TOTALS = re.compile(r'^TOTALS FOR\s+(.+?)\s+\((\d+)\s+PROJECTS?\)\s*(.*)$', re.I)

# lines that are page furniture / document titles, never data
SKIP = re.compile(
    r'CHANGES TO THE EXECUTIVE CAPITAL BUDGET|CAPITAL PROJECT DETAIL'
    r'|^PROJECT ID\b|^Page \d+|PURSUANT TO SECTION 254', re.I)

def money(s): return int(str(s).replace(",", "").strip() or 0)
def deaccent(s): return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def load_roster(awards_csvs):
    """Union of council-member surnames across years (upper + deaccented), for sponsor splitting."""
    r = set()
    for p in awards_csvs:
        if os.path.exists(p):
            for row in csv.DictReader(open(p)):
                m = row.get("member", "").strip()
                if m: r.add(deaccent(m).upper())
    r |= {"SPEAKER", "BRONX DELEGATION", "BROOKLYN DELEGATION", "QUEENS DELEGATION",
          "MANHATTAN DELEGATION", "STATEN ISLAND DELEGATION",
          "BRONX", "BROOKLYN", "QUEENS", "MANHATTAN", "STATEN ISLAND",
          "TECHNICAL ADJUSTMENT", "TECHNICAL ADJUSTMENTS"}
    return r

def split_sponsor(blob, roster):
    """blob = 'SPONSOR[, SPONSOR...]' text (uppercase). Peel roster names off the front; keep
    the remainder as-is (so an unknown sponsor is preserved rather than dropped)."""
    raw = blob.strip()
    if not raw: return ""
    up = deaccent(raw).upper()
    names = []; pos = 0
    R = sorted(roster, key=len, reverse=True)
    while True:
        seg = up[pos:].lstrip()
        skip = len(up[pos:]) - len(seg); pos += skip
        hit = None
        for nm in R:
            if seg.startswith(nm):
                nxt = seg[len(nm):len(nm) + 1]
                if nxt == "" or not nxt.isalpha() or nxt.isupper():
                    hit = nm; break
        if not hit: break
        names.append(raw[pos:pos + len(hit)]); pos += len(hit)
        after = up[pos:]
        m = re.match(r'\s*,\s*', after)
        if m: pos += m.end()
        else: break
    tail = raw[pos:].strip(" ,")
    return ", ".join(n.strip() for n in names) + ((" " + tail) if (names and tail) else (tail if not names else "")).rstrip() \
        if names else raw

def split_amounts(tokens):
    """tokens = the row's tokens AFTER the boro letter, i.e. '<TITLE...> <fy1..fy4> <SPONSOR...>'.
    The four fiscal-year amounts are the only run of >=4 consecutive numeric tokens; sponsors are
    surnames (never numeric). A title may END in a number (e.g. a community-district '126' or
    'I.S. 240'), which makes the numeric run longer than 4 -- so the amounts are the LAST four of
    the first >=4 run, and any earlier tokens in that run stay with the title.
    Returns (title_tokens, [4 amounts], sponsor_tokens) or None (not a data row)."""
    isnum = [bool(NUM.match(t)) for t in tokens]
    i, n = 0, len(tokens)
    while i < n:
        if isnum[i]:
            j = i
            while j < n and isnum[j]:
                j += 1
            if j - i >= 4:                       # first run of >=4 consecutive numerics
                amt_start = j - 4                # amounts are its LAST four
                return tokens[:amt_start], [money(t) for t in tokens[amt_start:j]], tokens[j:]
            i = j
        else:
            i += 1
    return None

def is_data_row(tokens):
    """A data row begins with two code pairs then a boro letter:
    <PROJID_a> <PROJID_b> <BL_a> <BL_b> <BORO> ...
    Signature: token[4] is a single boro letter; tokens[0..3] are short code tokens; at least
    one of the two 'second' code tokens carries a digit (so a run of title words can't pose as a
    code block); and a >=4 numeric run (the amounts) follows. Part II 'NON-CITY' rows use code
    prefixes (MA001, 0N381) unlike Part I's CN/NC/D -- hence a generic code-token test, not a
    prefix whitelist."""
    if len(tokens) < 6: return False
    # boro is a single letter. Normally M/X/K/Q/R/A, but the source occasionally prints it
    # lowercase ('r') or as a typo ('C' for a Bronx project); the reliable row signature is the
    # two code pairs + the 4-amount run, so accept any single letter here and keep it verbatim.
    if not (len(tokens[4]) == 1 and tokens[4].isalpha()): return False
    if not all(CODETOK.match(t) for t in tokens[:4]): return False
    if not (re.search(r'\d', tokens[1]) or re.search(r'\d', tokens[3])): return False
    return split_amounts(tokens[5:]) is not None

def parse(pdf_path):
    projects = []; subtotals = []
    with pdfplumber.open(pdf_path) as pdf:
        part = ""; agency = ""; pending = None

        def close(p):
            if not p: return
            title = re.sub(r'\s+', ' ', p['title']).strip()
            bc = sc = ""
            for b, s in BS.findall(title):
                if b: bc = b
                if s: sc = s
            title = BS.sub("", title).strip(" ,")
            p['title'] = title; p['building_code'] = bc; p['school_code'] = sc
            projects.append(p)

        lines = []
        for page in pdf.pages:
            t = page.extract_text() or ""
            for ln in t.split("\n"):
                s = ln.strip()
                if s: lines.append(s)

        for s in lines:
            pm = PART.match(s)
            if pm:
                close(pending); pending = None; part = pm.group(1); continue
            if SKIP.search(s):
                continue
            tm = TOTALS.match(s)
            if tm:
                close(pending); pending = None
                ag = tm.group(1).strip()
                if ag.upper() == "ALL":            # grand total, not an agency subtotal
                    continue
                amts = re.findall(r'-?[\d,]+', tm.group(3))
                subtotals.append(dict(part=part, agency=ag,
                                      fy1=money(amts[0]) if amts else 0,
                                      projects=int(tm.group(2))))
                continue
            toks = s.split()
            if is_data_row(toks):
                close(pending)
                title_t, amts, spon_t = split_amounts(toks[5:])
                pending = dict(part=part, agency=agency,
                               budget_line=f"{toks[0]} {toks[1]}",
                               sub_id=f"{toks[2]} {toks[3]}",
                               boro=toks[4].upper(), fy1=amts[0], fy2=amts[1], fy3=amts[2], fy4=amts[3],
                               sponsor_raw=" ".join(spon_t), title=" ".join(title_t))
                continue
            # not a part / skip / totals / data row:
            #  * pending open  -> title (and possibly sponsor) continuation of the current project
            #  * pending closed -> an agency header (all-caps line right after a TOTALS line/start)
            if pending is not None:
                pending['title'] += " " + s
            else:
                if s.isupper() or re.match(r"^[A-Z0-9&'./,\-() ]+$", s):
                    agency = s
        close(pending)
    return projects, subtotals

def write_out(projects, subtotals, pdf_path, outdir, prefix, npages, roster):
    os.makedirs(outdir, exist_ok=True)
    for p in projects:
        p['sponsor'] = split_sponsor(p.pop('sponsor_raw'), roster)
    P = lambda n: os.path.join(outdir, f"{prefix}_{n}")
    cols = ["part", "agency", "budget_line", "sub_id", "boro", "fy1", "fy2", "fy3", "fy4",
            "sponsor", "title", "building_code", "school_code"]
    with open(P("capital_projects.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for p in projects: w.writerow([p.get(c, "") for c in cols])

    got = defaultdict(int); cntp = defaultdict(int)
    for p in projects:
        got[(p['part'], p['agency'])] += p['fy1']; cntp[(p['part'], p['agency'])] += 1
    L = [f"CAPITAL (§254) RECONCILIATION ({prefix})",
         f"source: {os.path.basename(pdf_path)} ({npages} pages)  [parser: parse_capital_detail.py]",
         f"projects parsed: {len(projects)} | agency subtotals: {len(subtotals)}",
         f"total FY1 (all projects): ${sum(p['fy1'] for p in projects):,}\n",
         f"{'PART/AGENCY':52} {'proj$':>14} {'printed$':>14} {'n':>4} {'pn':>4}  status"]
    ok = 0
    for st in subtotals:
        key = (st['part'], st['agency']); g = got.get(key, 0); c = cntp.get(key, 0)
        good = (g == st['fy1'] and c == st['projects'])
        if good: ok += 1
        L.append(f"{(st['part'] + ' ' + st['agency'])[:52]:52} {g:>14,} {st['fy1']:>14,} "
                 f"{c:>4} {st['projects']:>4}  {'OK' if good else 'DIFF'}")
    L.append(f"\n{ok}/{len(subtotals)} agency subtotals reconcile (amount + project count)")
    rep = "\n".join(L)
    open(P("capital_reconciliation.txt"), "w").write(rep + "\n")
    return rep, ok, len(subtotals)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--roster", nargs="*", default=[])
    a = ap.parse_args()
    roster = load_roster(a.roster)
    projects, subtotals = parse(a.pdf)
    with pdfplumber.open(a.pdf) as pdf:
        npages = len(pdf.pages)
    rep, ok, n = write_out(projects, subtotals, a.pdf, a.outdir, a.prefix, npages, roster)
    print(rep)

if __name__ == "__main__":
    main()
