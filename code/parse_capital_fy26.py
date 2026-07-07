#!/usr/bin/env python3
"""
Layout-aware parser for the FY2026 'Changes to the Executive Capital Budget Pursuant to
Section 254 — Capital Project Detail' supporting-detail PDF.

The FY26 PDF's text layer is column-scrambled under pypdf.extract_text(); this parser
instead uses pdfplumber word coordinates, clusters words into visual rows by y, and maps
each word to a column by its x-position against band boundaries read from THAT PAGE's header
row. Part I and Part II are shifted horizontally, so per-page boundaries handle both.
Amounts are right-aligned and classified by their right edge (x1), so wide/negative values
(e.g. -183,000) land in the right column instead of bleeding into the title.

Emits the FY27 schema exactly:
  part, agency, budget_line, sub_id, boro, fy1, fy2, fy3, fy4, sponsor, title, building_code, school_code

fy1 = adoption year (FY2026); fy2..fy4 = the three out-years.
Numbers/IDs/boro come straight from coordinates (deterministic). Sponsor is split from the
sponsor column text using the accent-normalized council roster (schedule-C awards).

Reconciles per-agency FY1 sum and project count against the printed
'TOTALS FOR <agency> (N PROJECTS)' lines.
"""
import re, csv, os, argparse, unicodedata
from collections import defaultdict
import pdfplumber

# Column x0 bands (points). Derived from the header + data rows of the FY26 schedule.
# budget_line ~37, sub_id ~93, boro ~159, title 189..~390, fy amounts right-aligned,
# sponsor ~569+. Amount columns identified by x0 of the LEFT edge of each right-aligned number.
BORO_SET = set("MXKQRA")  # M/X/K/Q/R + A (citywide/all boroughs)
BS = re.compile(r'\bB[:;]\s*(\S+)|\bS[:;]\s*(\S+)')

NUM = re.compile(r'^-?[\d,]+$')  # a printed amount, incl. negative adjustments like -183,000
def money(s): return int(str(s).replace(",", "").replace("$", "").strip() or 0)
def deaccent(s): return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def load_roster(awards_csvs):
    r = set()
    for p in awards_csvs:
        if os.path.exists(p):
            for row in csv.DictReader(open(p)):
                m = row.get("member", "").strip()
                if m: r.add(deaccent(m).upper())
    r |= {"SPEAKER", "BRONX DELEGATION", "BROOKLYN DELEGATION", "QUEENS DELEGATION",
          "MANHATTAN DELEGATION", "STATEN ISLAND DELEGATION",
          "BRONX", "BROOKLYN", "QUEENS", "MANHATTAN", "STATEN ISLAND"}
    return r

def split_sponsor(blob, roster):
    """blob = 'SPONSOR[, SPONSOR...]' text from the sponsor column (may include trailing title
    fragments if a title word bled into the band). Peel roster names off the front."""
    raw = blob.strip()
    up = deaccent(raw).upper()
    names = []; pos = 0
    R = sorted(roster, key=len, reverse=True)
    while True:
        seg = up[pos:].lstrip()
        skip = len(up[pos:]) - len(seg); pos += skip
        hit = None
        for nm in R:
            if seg.startswith(nm):
                nxt = seg[len(nm):len(nm)+1]
                if nxt == "" or not nxt.isalpha() or nxt.isupper():
                    hit = nm; break
        if not hit: break
        names.append(raw[pos:pos+len(hit)]); pos += len(hit)
        after = up[pos:]
        m = re.match(r'\s*,\s*', after)
        if m: pos += m.end()
        else: break
    sponsor = ", ".join(n.strip() for n in names) if names else raw
    return sponsor

def page_part(page):
    for w in page.extract_words():
        if w['top'] < 45:
            m = re.match(r'^(I{1,3})\.$', w['text'])
            if m: return m.group(1)
    return None

def page_columns(page):
    """Read the header row ('SUB ID / BUDGET LINE / BORO / PROJECT TITLE / FY xxxx.../ SPONSOR')
    and return x-boundaries for this page. Part I and Part II are shifted horizontally, so
    boundaries are derived per page rather than hardcoded. Returns dict or None if no header."""
    words = page.extract_words()
    # anchor on the column-header row: the row containing the 'BORO' label. Read only words
    # within a few points of its y (avoids the 'CAPITAL PROJECT DETAIL' subtitle grabbing PROJECT).
    boro_hdr = next((w for w in words if w['text'] == "BORO" and w['top'] < 110), None)
    if boro_hdr is None: return None
    y = boro_hdr['top']
    band = [w for w in words if abs(w['top'] - y) <= 4]
    hdr = {}
    for w in band:
        t = w['text']
        if t == "SUB" and 'sub' not in hdr: hdr['sub'] = w['x0']
        elif t == "BUDGET": hdr['budget'] = w['x0']
        elif t == "BORO": hdr['boro'] = w['x0']
        elif t == "PROJECT" and 'title' not in hdr: hdr['title'] = w['x0']
        elif t == "SPONSOR": hdr['sponsor'] = w['x0']
        elif t == "FY" and w['x0'] > 380:
            hdr.setdefault('fy_x', []).append(w['x0'])
    need = {'sub', 'budget', 'boro', 'title', 'sponsor'}
    if not need <= set(hdr): return None
    fy_x = sorted(hdr.get('fy_x', []))[:4]
    # column bands:
    #  budget_line: [sub_x, budget_x)          (leftmost code cluster, header label 'SUB ID')
    #  sub_id:      [budget_x, boro_x - 4)      (header label 'BUDGET LINE')
    #  boro:        [boro_x - 4, title_x - 4)
    #  title:       [title_x - 4, ~sponsor - amount gap)  we cap title by amount x below
    #  sponsor:     [sponsor_x - 6, inf)
    # NOTE: the two leftmost header labels ('SUB ID' at ~sub_x, 'BUDGET LINE' at ~budget_x)
    # sit above the two code columns; the FY27 schema names the left code 'budget_line' and the
    # right code 'sub_id', matching the printed data (left = CN/NC number, right = D/DN number).
    # amount columns are RIGHT-aligned, so a value's right edge (x1) is the stable anchor; wide
    # numbers (e.g. 14,480,000) extend far left and would fall in the title band if keyed on x0.
    # Each column's numbers right-align to just left of the NEXT column's FY-header x. Bound each
    # column's x1 by [this_fy_x, next_fy_x) — the printed number's right edge lands in that window.
    amt_bounds = []
    for i, x in enumerate(fy_x):
        lo = x
        hi = (fy_x[i + 1]) if i + 1 < len(fy_x) else hdr['sponsor'] - 4
        amt_bounds.append((lo, hi))
    return dict(
        bl_lo=hdr['sub'] - 4, bl_hi=hdr['budget'] - 4,
        sub_lo=hdr['budget'] - 4, sub_hi=hdr['boro'] - 6,
        boro_lo=hdr['boro'] - 6, boro_hi=hdr['title'] - 6,
        title_lo=hdr['title'] - 6, title_hi=fy_x[0] - 4 if fy_x else 380,
        spon_lo=hdr['sponsor'] - 8,
        amt_bounds=amt_bounds,
    )

def which_amt(x0, x1, amt_bounds):
    """Return amount-column index for a right-aligned number, keyed on its right edge x1."""
    for i, (lo, hi) in enumerate(amt_bounds):
        if lo <= x1 < hi:
            return i
    return None

def cluster_rows(words, ytol=3):
    """Group words into visual rows by 'top'. Returns list of (y, [words]) sorted top->bottom."""
    rows = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        placed = False
        for r in rows:
            if abs(r['y'] - w['top']) <= ytol:
                r['ws'].append(w); placed = True; break
        if not placed:
            rows.append({'y': w['top'], 'ws': [w]})
    for r in rows:
        r['ws'].sort(key=lambda w: w['x0'])
    return sorted(rows, key=lambda r: r['y'])

def parse(pdf_path, roster):
    projects = []; subtotals = []
    with pdfplumber.open(pdf_path) as pdf:
        part = ""; agency = ""
        pending = None
        def close(p):
            if not p: return
            title = re.sub(r'\s+', ' ', p['title']).strip()
            bc = sc = ""
            for b, s in BS.findall(title):
                if b: bc = b
                if s: sc = s
            title = BS.sub("", title).strip(" ,")
            p['title'] = title; p['building_code'] = bc; p['school_code'] = sc
            p['sponsor'] = split_sponsor(p.pop('sponsor_raw'), roster)
            projects.append(p)

        page_ctr = None  # page horizontal center, for agency-header centering test
        for page in pdf.pages:
            pp = page_part(page)
            if pp: part = pp
            cols = page_columns(page)
            if cols is None:
                continue  # non-schedule page (TOC, part-III non-city table, cover)
            page_ctr = page.width / 2
            words = [w for w in page.extract_words(use_text_flow=False)
                     if w['top'] > 78 and w['top'] < 560]  # strip page title band + footer
            rows = cluster_rows(words)
            for r in rows:
                ws = r['ws']
                texts = [w['text'] for w in ws]
                joined = " ".join(texts)
                # skip the column-header row (SUB ID / BUDGET LINE / BORO / PROJECT TITLE / SPONSOR)
                if "BORO" in texts and ("SPONSOR" in texts or "TITLE" in texts):
                    continue
                # subtotal line
                sm = re.match(r'^TOTALS FOR\s+(.+?)\s+\((\d+)\s+PROJECTS?\)', joined, re.I)
                if sm:
                    close(pending); pending = None
                    ag = sm.group(1).strip()
                    if ag.upper() == "ALL":   # grand total, not an agency subtotal
                        continue
                    amts = {}
                    for w in ws:
                        if NUM.match(w['text']):
                            c = which_amt(w['x0'], w['x1'], cols['amt_bounds'])
                            if c is not None: amts[c] = money(w['text'])
                    subtotals.append(dict(part=part, agency=ag,
                                          fy1=amts.get(0, 0), projects=int(sm.group(2))))
                    continue
                # a data row: a single boro letter in the boro band, plus >=1 code left of it.
                boro_w = [w for w in ws if w['text'] in BORO_SET
                          and cols['boro_lo'] <= w['x0'] < cols['boro_hi']]
                left = [w for w in ws if w['x0'] < cols['boro_lo']]
                is_row = bool(boro_w) and len(left) >= 2
                if is_row:
                    close(pending)
                    boro = boro_w[0]['text']
                    bl = " ".join(w['text'] for w in ws if cols['bl_lo'] <= w['x0'] < cols['bl_hi'])
                    sub = " ".join(w['text'] for w in ws if cols['sub_lo'] <= w['x0'] < cols['sub_hi'])
                    amts = {0: 0, 1: 0, 2: 0, 3: 0}
                    amt_ids = set()
                    for w in ws:
                        if NUM.match(w['text']):
                            c = which_amt(w['x0'], w['x1'], cols['amt_bounds'])
                            if c is not None:
                                amts[c] = money(w['text']); amt_ids.add(id(w))
                    # title = title-band words that are NOT amount tokens (wide amounts start left)
                    title_ws = [w for w in ws if cols['title_lo'] <= w['x0'] < cols['spon_lo']
                                and id(w) not in amt_ids]
                    spon_ws = [w for w in ws if w['x0'] >= cols['spon_lo']]
                    title = " ".join(w['text'] for w in title_ws)
                    spon = " ".join(w['text'] for w in spon_ws)
                    pending = dict(part=part, agency=agency, budget_line=bl, sub_id=sub,
                                   boro=boro, fy1=amts[0], fy2=amts[1], fy3=amts[2], fy4=amts[3],
                                   title=title, sponsor_raw=spon)
                    continue
                # agency header: all-caps row, no boro, no amounts, no left-band code, horizontally
                # centered on the page. Title continuations are left-aligned at title_lo, so their
                # left edge (< center - margin) rules them out.
                has_amt = any(NUM.match(w['text'])
                              and which_amt(w['x0'], w['x1'], cols['amt_bounds']) is not None
                              for w in ws)
                has_left = any(w['x0'] < cols['boro_lo'] for w in ws)
                lo = min(w['x0'] for w in ws); hi = max(w['x1'] for w in ws)
                mid = (lo + hi) / 2
                is_header = (not has_amt and not has_left
                             and lo >= cols['title_lo'] + 60
                             and abs(mid - page_ctr) <= 55
                             and all(re.match(r"^[A-Z0-9&'./,\-()]+$", w['text']) for w in ws))
                if is_header:
                    close(pending); pending = None
                    agency = " ".join(w['text'] for w in sorted(ws, key=lambda w: w['x0']))
                elif pending is not None:
                    cont = [w['text'] for w in ws if cols['title_lo'] <= w['x0'] < cols['title_hi']]
                    spon_cont = [w['text'] for w in ws if w['x0'] >= cols['spon_lo']]
                    if cont: pending['title'] += " " + " ".join(cont)
                    if spon_cont: pending['sponsor_raw'] += " " + " ".join(spon_cont)
        close(pending)
    return projects, subtotals

def write_out(projects, subtotals, pdf_path, outdir, prefix, npages):
    os.makedirs(outdir, exist_ok=True)
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
         f"source: {os.path.basename(pdf_path)} ({npages} pages)",
         f"projects parsed: {len(projects)} | agency subtotals: {len(subtotals)}",
         f"total FY1 (all projects): ${sum(p['fy1'] for p in projects):,}\n",
         f"{'PART/AGENCY':52} {'proj$':>14} {'printed$':>14} {'n':>4} {'pn':>4}  status"]
    ok = 0
    for st in subtotals:
        key = (st['part'], st['agency']); g = got.get(key, 0); c = cntp.get(key, 0)
        good = (g == st['fy1'] and c == st['projects'])
        if good: ok += 1
        L.append(f"{(st['part']+' '+st['agency'])[:52]:52} {g:>14,} {st['fy1']:>14,} {c:>4} {st['projects']:>4}  {'OK' if good else 'DIFF'}")
    L.append(f"\n{ok}/{len(subtotals)} agency subtotals reconcile (amount + project count)")
    rep = "\n".join(L)
    open(P("capital_reconciliation.txt"), "w").write(rep + "\n")
    return rep, ok, len(subtotals)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--roster", nargs="*", default=[])
    a = ap.parse_args()
    roster = load_roster(a.roster)
    projects, subtotals = parse(a.pdf, roster)
    with pdfplumber.open(a.pdf) as pdf:
        npages = len(pdf.pages)
    rep, ok, n = write_out(projects, subtotals, a.pdf, a.outdir, a.prefix, npages)
    print(rep)

if __name__ == "__main__":
    main()
