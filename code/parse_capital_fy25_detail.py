#!/usr/bin/env python3
"""
Layout-aware parser for the FY2025 Council-additions 'Supporting Detail For Fiscal Year 2025 —
Changes to the Executive Capital Budget Adopted by the City Council Pursuant to Section 254'
book (the "Capital Project Detail" genre — the FY2025 counterpart to the FY2026/FY2027 supporting-
detail books, NOT the broad §254 appropriation-changes book parsed by parse_capital_fy25.py).

Reuses the coordinate approach of parse_capital_fy26.py (pdfplumber word coordinates, y-clustered
rows, per-page x-bands read from that page's header) because the text layer is column-scrambled
under extract_text() and hardcoded bands corrupt shifted parts. Two FY25-specific header quirks
this variant handles:

  1. The left code column header is 'PROJECT ID' (x0~37), not FY26's 'SUB ID'. Keying on the
     literal 'SUB' (as parse_capital_fy26.py does) finds no header and skips every page.
  2. The header row therefore carries TWO 'PROJECT' tokens — 'PROJECT ID' (x0~37, the left code
     column) and 'PROJECT TITLE' (x0~189, the title column). The left one is disambiguated by x0.

The document has THREE parts (the FY26 book had two):
  * I.   Capital Project Detail            (city; BORO header + agency 'TOTALS FOR ...' subtotals)
  * II.  Non-City Capital Project Detail   (same layout as I; a non-city SUBSET re-listed)
  * III. Capital Project Detail by Non-City Entity  (a DIFFERENT schema: organization-grouped, no
         boro/sponsor/agency subtotals; each entity carries a printed $ total, and the part carries
         a 'TOTAL NON-CITY PROJECT ALLOCATIONS' grand total == Part II's grand total). Part III is
         a cross-tab of Part II, so it is emitted to a SEPARATE sidecar CSV rather than mixed into
         the comparable Part I+II rows (which match the FY26/FY27 canonical CSVs exactly).

Parts I+II -> {prefix}_capital_projects.csv  (FY26/FY27 schema, reconciled to printed subtotals)
Part III   -> {prefix}_capital_noncity_by_entity.csv  (organization, budget_line, fy1..fy4)
Reconciliation report -> {prefix}_capital_reconciliation.txt (per-agency subtotals, both grand
totals for Parts I/II, and Part III per-entity + grand-total + Part-II cross-check).

fy1 = adoption year (FY2025); fy2..fy4 = out-years (FY2026..FY2028). All numbers/IDs/boro come
straight from coordinates (deterministic); sponsor is split off the sponsor column using the
accent-normalized council roster.
"""
import re, csv, os, argparse, unicodedata
from collections import defaultdict
import pdfplumber

BORO_SET = set("MXKQRA")            # M/X/K/Q/R + A (citywide)
BS = re.compile(r'\bB[:;]\s*(\S+)|\bS[:;]\s*(\S+)')
NUM = re.compile(r'^-?[\d,]+$')     # a printed amount, incl. negative adjustments
DOLLAR = re.compile(r'^\$-?[\d,]+$')  # Part III entity/grand totals are '$'-prefixed


def money(s): return int(str(s).replace(",", "").replace("$", "").strip() or 0)
def deaccent(s): return "".join(c for c in unicodedata.normalize("NFD", s)
                                if unicodedata.category(c) != "Mn")


def load_roster(awards_csvs):
    r = set()
    for p in awards_csvs:
        if os.path.exists(p):
            for row in csv.DictReader(open(p)):
                m = row.get("member", "").strip()
                if m: r.add(deaccent(m).upper())
    r |= {"SPEAKER", "BRONX DELEGATION", "BROOKLYN DELEGATION", "QUEENS DELEGATION",
          "MANHATTAN DELEGATION", "STATEN ISLAND DELEGATION",
          "BRONX", "BROOKLYN", "QUEENS", "MANHATTAN", "STATEN ISLAND",
          "TECHNICAL ADJUSTMENTS"}
    return r


def split_sponsor(blob, roster):
    """Peel roster names off the front of the sponsor-column text (may include a stray title
    fragment if a wide title word bled into the band)."""
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
                nxt = seg[len(nm):len(nm) + 1]
                if nxt == "" or not nxt.isalpha() or nxt.isupper():
                    hit = nm; break
        if not hit: break
        names.append(raw[pos:pos + len(hit)]); pos += len(hit)
        after = up[pos:]
        m = re.match(r'\s*,\s*', after)
        if m: pos += m.end()
        else: break
    return ", ".join(n.strip() for n in names) if names else raw


def page_part(page):
    for w in page.extract_words():
        if w['top'] < 45:
            m = re.match(r'^(I{1,3})\.$', w['text'])
            if m: return m.group(1)
    return None


def cluster_rows(words, ytol=3):
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


def which_amt(x0, x1, amt_bounds):
    """Amount column for a right-aligned number, keyed on its right edge x1."""
    for i, (lo, hi) in enumerate(amt_bounds):
        if lo <= x1 < hi:
            return i
    return None


# ---------- Parts I & II: standard 'Capital Project Detail' layout ----------

def page_columns(page):
    """Read this page's header row and return column x-bands. FY25 header layout:
    'PROJECT ID' (left code, x0~37) | 'BUDGET LINE' (right code, x0~93) | 'BORO' | 'PROJECT TITLE'
    (x0~189) | 'FY 2025..2028' (right-aligned amounts) | 'SPONSOR'. Returns dict or None if the
    page has no such header (cover / TOC / Part III)."""
    words = page.extract_words()
    boro_hdr = next((w for w in words if w['text'] == "BORO" and w['top'] < 110), None)
    if boro_hdr is None: return None
    y = boro_hdr['top']
    band = [w for w in words if abs(w['top'] - y) <= 4]
    hdr = {}
    for w in band:
        t = w['text']
        if t == "PROJECT" and w['x0'] < 90 and 'projid' not in hdr: hdr['projid'] = w['x0']
        elif t == "BUDGET": hdr['budget'] = w['x0']
        elif t == "BORO": hdr['boro'] = w['x0']
        elif t == "PROJECT" and w['x0'] > 150 and 'title' not in hdr: hdr['title'] = w['x0']
        elif t == "SPONSOR": hdr['sponsor'] = w['x0']
        elif t == "FY" and w['x0'] > 380: hdr.setdefault('fy_x', []).append(w['x0'])
    need = {'projid', 'budget', 'boro', 'title', 'sponsor'}
    if not need <= set(hdr): return None
    fy_x = sorted(hdr.get('fy_x', []))[:4]
    if len(fy_x) < 4: return None
    # amount columns are right-aligned; a value's right edge (x1) lands in [this_fy_x, next_fy_x).
    amt_bounds = []
    for i, x in enumerate(fy_x):
        lo = x
        hi = fy_x[i + 1] if i + 1 < len(fy_x) else hdr['sponsor'] - 4
        amt_bounds.append((lo, hi))
    # left code header 'PROJECT ID' sits over the CN/NC number -> schema budget_line; right code
    # header 'BUDGET LINE' sits over the D/DN number -> schema sub_id (matches FY26/FY27).
    return dict(
        bl_lo=hdr['projid'] - 4, bl_hi=hdr['budget'] - 4,
        sub_lo=hdr['budget'] - 4, sub_hi=hdr['boro'] - 6,
        boro_lo=hdr['boro'] - 6, boro_hi=hdr['title'] - 6,
        title_lo=hdr['title'] - 6, title_hi=fy_x[0] - 4,
        spon_lo=hdr['sponsor'] - 8,
        amt_bounds=amt_bounds,
    )


def parse_detail(pdf, roster):
    """Parse Parts I & II. Returns (projects, subtotals, grand_totals)."""
    projects = []; subtotals = []
    grand = {}  # part -> dict(fy1, projects)
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
        p['sponsor'] = split_sponsor(p.pop('sponsor_raw'), roster)
        projects.append(p)

    for page in pdf.pages:
        pp = page_part(page)
        if pp: part = pp
        cols = page_columns(page)
        if cols is None:
            continue
        page_ctr = page.width / 2
        words = [w for w in page.extract_words(use_text_flow=False)
                 if 78 < w['top'] < 560]
        for r in cluster_rows(words):
            ws = r['ws']
            texts = [w['text'] for w in ws]
            joined = " ".join(texts)
            if "BORO" in texts and ("SPONSOR" in texts or "TITLE" in texts):
                continue  # column-header row
            sm = re.match(r'^TOTALS FOR\s+(.+?)\s+\((\d+)\s+PROJECTS?\)', joined, re.I)
            if sm:
                close(pending); pending = None
                ag = sm.group(1).strip()
                amts = {}
                for w in ws:
                    if NUM.match(w['text']):
                        c = which_amt(w['x0'], w['x1'], cols['amt_bounds'])
                        if c is not None: amts[c] = money(w['text'])
                if ag.upper() == "ALL":
                    grand[part] = dict(fy1=amts.get(0, 0), projects=int(sm.group(2)))
                else:
                    subtotals.append(dict(part=part, agency=ag,
                                          fy1=amts.get(0, 0), projects=int(sm.group(2))))
                continue
            boro_w = [w for w in ws if w['text'] in BORO_SET
                      and cols['boro_lo'] <= w['x0'] < cols['boro_hi']]
            left = [w for w in ws if w['x0'] < cols['boro_lo']]
            if boro_w and len(left) >= 2:  # a data row
                close(pending)
                boro = boro_w[0]['text']
                bl = " ".join(w['text'] for w in ws if cols['bl_lo'] <= w['x0'] < cols['bl_hi'])
                sub = " ".join(w['text'] for w in ws if cols['sub_lo'] <= w['x0'] < cols['sub_hi'])
                amts = {0: 0, 1: 0, 2: 0, 3: 0}; amt_ids = set()
                for w in ws:
                    if NUM.match(w['text']):
                        c = which_amt(w['x0'], w['x1'], cols['amt_bounds'])
                        if c is not None:
                            amts[c] = money(w['text']); amt_ids.add(id(w))
                title_ws = [w for w in ws if cols['title_lo'] <= w['x0'] < cols['spon_lo']
                            and id(w) not in amt_ids]
                spon_ws = [w for w in ws if w['x0'] >= cols['spon_lo']]
                pending = dict(part=part, agency=agency, budget_line=bl, sub_id=sub,
                               boro=boro, fy1=amts[0], fy2=amts[1], fy3=amts[2], fy4=amts[3],
                               title=" ".join(w['text'] for w in title_ws),
                               sponsor_raw=" ".join(w['text'] for w in spon_ws))
                continue
            # agency header: centered all-caps row, no amount, no left-band code
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
        close(pending); pending = None
    close(pending)
    return projects, subtotals, grand


# ---------- Part III: 'Capital Project Detail by Non-City Entity' ----------

def page_columns_p3(page):
    words = page.extract_words()
    org = next((w for w in words if w['text'] == "ORGANIZATION" and w['top'] < 130), None)
    if org is None: return None
    y = org['top']
    band = [w for w in words if abs(w['top'] - y) <= 4]
    hdr = {}
    for w in band:
        if w['text'] == "BUDGET": hdr['line'] = w['x0']          # 'BUDGET LINE' col, x0~374
        elif w['text'] == "FY" and w['x0'] > 440:
            hdr.setdefault('fy_x', []).append(w['x0'])
    fy_x = sorted(hdr.get('fy_x', []))[:4]
    if 'line' not in hdr or len(fy_x) < 4: return None
    amt_bounds = []
    for i, x in enumerate(fy_x):
        lo = x
        hi = fy_x[i + 1] if i + 1 < len(fy_x) else fy_x[-1] + 80
        amt_bounds.append((lo, hi))
    return dict(org_hi=hdr['line'] - 6, line_lo=hdr['line'] - 6,
                line_hi=fy_x[0] - 6, amt_bounds=amt_bounds)


def parse_part3(pdf):
    """Parse Part III. Returns (rows, entities, grand). rows = budget-line grain;
    entities = [(organization, total_fy1)]; grand = dict(fy1..)."""
    rows = []; entities = []; grand = {}
    cur = None; namebuf = ""
    for page in pdf.pages:
        if page_part(page) != "III":
            continue
        cols = page_columns_p3(page)
        if cols is None:
            continue
        words = [w for w in page.extract_words(use_text_flow=False) if 108 < w['top'] < 575]
        for r in cluster_rows(words):
            ws = r['ws']; texts = [w['text'] for w in ws]; joined = " ".join(texts)
            if "TOTAL NON-CITY PROJECT ALLOCATIONS" in joined:
                amts = {}
                for w in ws:
                    if DOLLAR.match(w['text']):
                        c = which_amt(w['x0'], w['x1'], cols['amt_bounds'])
                        if c is not None: amts[c] = money(w['text'])
                grand = dict(fy1=amts.get(0, 0), fy2=amts.get(1, 0),
                             fy3=amts.get(2, 0), fy4=amts.get(3, 0))
                continue
            if "ORGANIZATION" in texts or ("BUDGET" in texts and "LINE" in texts):
                continue  # repeated header
            dollar = any(DOLLAR.match(w['text']) for w in ws)
            org_ws = [w for w in ws if w['x0'] < cols['org_hi']]
            code_ws = [w for w in ws if cols['line_lo'] <= w['x0'] < cols['line_hi']]
            if dollar and org_ws:  # entity header (org name + $-totals)
                org = (namebuf + " " + " ".join(w['text'] for w in org_ws)).strip()
                namebuf = ""
                amts = {}
                for w in ws:
                    if DOLLAR.match(w['text']):
                        c = which_amt(w['x0'], w['x1'], cols['amt_bounds'])
                        if c is not None: amts[c] = money(w['text'])
                cur = dict(organization=org, total_fy1=amts.get(0, 0), got=0)
                entities.append(cur)
                continue
            if code_ws:  # budget-line row under current entity
                bl = " ".join(w['text'] for w in code_ws)
                amts = {0: 0, 1: 0, 2: 0, 3: 0}
                for w in ws:
                    if NUM.match(w['text']):
                        c = which_amt(w['x0'], w['x1'], cols['amt_bounds'])
                        if c is not None: amts[c] = money(w['text'])
                rows.append(dict(organization=cur['organization'] if cur else "",
                                 budget_line=bl, fy1=amts[0], fy2=amts[1],
                                 fy3=amts[2], fy4=amts[3]))
                if cur is not None: cur['got'] += amts[0]
                continue
            if org_ws and not dollar:  # org-name wrap line (no $, no code) -> buffer
                namebuf = (namebuf + " " + " ".join(w['text'] for w in org_ws)).strip()
    return rows, entities, grand


# ---------- output ----------

def write_out(projects, subtotals, grand, p3_rows, p3_entities, p3_grand,
              pdf_path, outdir, prefix, npages):
    os.makedirs(outdir, exist_ok=True)
    P = lambda n: os.path.join(outdir, f"{prefix}_{n}")
    cols = ["part", "agency", "budget_line", "sub_id", "boro", "fy1", "fy2", "fy3", "fy4",
            "sponsor", "title", "building_code", "school_code"]
    with open(P("capital_projects.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for p in projects: w.writerow([p.get(c, "") for c in cols])

    with open(P("capital_noncity_by_entity.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["organization", "budget_line", "fy1", "fy2", "fy3", "fy4"])
        for r in p3_rows:
            w.writerow([r["organization"], r["budget_line"], r["fy1"], r["fy2"], r["fy3"], r["fy4"]])

    got = defaultdict(int); cntp = defaultdict(int)
    for p in projects:
        got[(p['part'], p['agency'])] += p['fy1']; cntp[(p['part'], p['agency'])] += 1
    L = [f"CAPITAL (§254) RECONCILIATION ({prefix}) — Council-additions supporting-detail book",
         f"source: {os.path.basename(pdf_path)} ({npages} pages)",
         f"projects parsed (Parts I+II): {len(projects)} | agency subtotals: {len(subtotals)}",
         f"total FY1 (all projects): ${sum(p['fy1'] for p in projects):,}\n",
         f"{'PART/AGENCY':52} {'proj$':>14} {'printed$':>14} {'n':>4} {'pn':>4}  status"]
    ok = 0
    for st in subtotals:
        key = (st['part'], st['agency']); g = got.get(key, 0); c = cntp.get(key, 0)
        good = (g == st['fy1'] and c == st['projects'])
        if good: ok += 1
        L.append(f"{(st['part']+' '+st['agency'])[:52]:52} {g:>14,} {st['fy1']:>14,} "
                 f"{c:>4} {st['projects']:>4}  {'OK' if good else 'DIFF'}")
    L.append(f"\n{ok}/{len(subtotals)} agency subtotals reconcile (amount + project count)")

    # grand-total checks per part
    L.append("\nGRAND TOTALS (printed 'TOTALS FOR ALL' vs summed projects):")
    gok = 0
    for part in sorted(grand):
        rs = [p for p in projects if p['part'] == part]
        gsum = sum(p['fy1'] for p in rs); gcnt = len(rs)
        pr = grand[part]
        good = (gsum == pr['fy1'] and gcnt == pr['projects'])
        if good: gok += 1
        L.append(f"  Part {part}: parsed ${gsum:,} / {gcnt} proj  vs printed "
                 f"${pr['fy1']:,} / {pr['projects']} proj  {'OK' if good else 'DIFF'}")

    # Part III reconciliation
    L.append("\nPART III — Capital Project Detail by Non-City Entity (sidecar cross-tab of Part II):")
    ent_ok = sum(1 for e in p3_entities if e['got'] == e['total_fy1'])
    p3_sum = sum(r['fy1'] for r in p3_rows)
    L.append(f"  entities: {len(p3_entities)} ({ent_ok} reconcile to their printed $ total) | "
             f"budget-line rows: {len(p3_rows)}")
    L.append(f"  summed budget-line FY2025: ${p3_sum:,}  vs printed grand total "
             f"${p3_grand.get('fy1', 0):,}  {'OK' if p3_sum == p3_grand.get('fy1') else 'DIFF'}")
    # cross-check Part III grand total == Part II grand total
    p2 = grand.get('II', {})
    if p2:
        xok = (p3_grand.get('fy1') == p2.get('fy1'))
        L.append(f"  cross-check: Part III grand ${p3_grand.get('fy1', 0):,} "
                 f"{'==' if xok else '!='} Part II grand ${p2.get('fy1', 0):,}  "
                 f"{'OK' if xok else 'DIFF'}")

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
    with pdfplumber.open(a.pdf) as pdf:
        projects, subtotals, grand = parse_detail(pdf, roster)
        p3_rows, p3_entities, p3_grand = parse_part3(pdf)
        npages = len(pdf.pages)
    rep, ok, n = write_out(projects, subtotals, grand, p3_rows, p3_entities, p3_grand,
                           a.pdf, a.outdir, a.prefix, npages)
    print(rep)


if __name__ == "__main__":
    main()
