#!/usr/bin/env python3
"""
Layout-aware parser for the FY2025 'Changes to the Executive Capital Budget Pursuant to
Section 254' PDF (Fiscal-2025-Capital-Changes.pdf).

IMPORTANT — FY25 is a DIFFERENT document type than FY26/FY27. It is the Section-254
"Appropriation Changes / Changes to Part I" resolution schedule, not the "Capital Project
Detail" schedule. Consequences for the FY27 schema:
  * There are NO 'TOTALS FOR <agency> (N PROJECTS)' subtotal lines anywhere in the document,
    so this parse CANNOT be reconciled the way FY26/FY27 are. The only printed total is a
    single citywide grand total ($15.28B TOTAL FUNDS) which is the whole adopted budget, not
    the sum of these changes. This is a property of the source, not a parser limitation.
  * The document has NO borough, NO sub-id, and NO council-sponsor columns. Those FY27 fields
    are emitted EMPTY. What FY25 does carry that FY27 doesn't: an ACTION per change
    (ELIMINATE / SUBSTITUTE / NEW PROJECT), emitted in an extra 'action' column.

Each budget line (e.g. 'CS-DN05H') is a block: a code at x~36, one or more action words at
x~552, a right-aligned '(CN)' amount row carrying the FY2025..FY2028 change amounts, and a
multi-line boilerplate title whose meaningful tail is the org/project name.

Amounts come straight from coordinates (deterministic). The '(CN)' amount row is the change;
a sibling bare-number row (0 0 0 0) is the prior baseline and is ignored for fy1..fy4.

Emits the FY27 columns plus 'action' (extra, FY25-only):
  part, agency, budget_line, sub_id, boro, fy1, fy2, fy3, fy4, sponsor, title,
  building_code, school_code, action
"""
import re, csv, os, argparse
from collections import defaultdict
import pdfplumber

MONEY = re.compile(r'^([\d,]+)\(CN\)$')          # a change amount like 680,000(CN)
BARE  = re.compile(r'^[\d,]+$')
CODE  = re.compile(r'^[A-Z]{1,3}-D[A-Z0-9]+$')   # budget-line code, e.g. AG-DN06Y, CS-DN05H
ACTIONS = ("ELIMINATE", "SUBSTITUTE")
BS = re.compile(r'\bB[:;]\s*(\S+)|\bS[:;]\s*(\S+)')

def money(s): return int(s.replace(",", "") or 0)

# (CN) amounts are right-aligned; measured right edges (x1) cluster tightly at these columns:
#   FY2025 ~445, FY2026 ~550, FY2027 ~655, FY2028 ~760.
AMT_X1 = [445, 550, 655, 760]
def amt_col(x1):
    best = min(range(4), key=lambda i: abs(AMT_X1[i] - x1))
    return best if abs(AMT_X1[best] - x1) < 25 else None

def cluster_rows(words, ytol=3):
    rows = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        for r in rows:
            if abs(r['y'] - w['top']) <= ytol:
                r['ws'].append(w); break
        else:
            rows.append({'y': w['top'], 'ws': [w]})
    for r in rows: r['ws'].sort(key=lambda w: w['x0'])
    return sorted(rows, key=lambda r: r['y'])

def parse(pdf_path):
    projects = []
    with pdfplumber.open(pdf_path) as pdf:
        agency = ""; pending = None
        def close(p):
            if not p: return
            title = re.sub(r'\s+', ' ', p['title']).strip()
            bc = sc = ""
            for b, s in BS.findall(title):
                if b: bc = b
                if s: sc = s
            title = BS.sub("", title).strip(" ,")
            p['title'] = title; p['building_code'] = bc; p['school_code'] = sc
            p['action'] = ", ".join(dict.fromkeys(p.pop('actions')))  # dedup, keep order
            projects.append(p)

        for page in pdf.pages:
            t = page.extract_text() or ""
            if "CHANGES TO PART" not in t:
                continue  # cover / resolution / grand-total pages
            words = [w for w in page.extract_words(use_text_flow=False)
                     if w['top'] > 100 and w['top'] < 545]
            for r in cluster_rows(words):
                ws = r['ws']
                texts = [w['text'] for w in ws]
                # skip the repeated column-header row
                if "LINE" in texts and "TITLE" in texts:
                    continue
                # agency header: a centered all-caps row (left edge >= 280), no code, no amounts,
                # no action word. Checked FIRST (before the code test) and works whether or not a
                # block is pending — a header follows the last change block of the prior agency.
                # Title/boilerplate continuations start at x~96, so their left edge rules them out.
                lo = min(w['x0'] for w in ws)
                if lo >= 280 \
                   and all(re.match(r"^[A-Z0-9&'./,\-()]+$", x) for x in texts) \
                   and not any(MONEY.match(x) or BARE.match(x) for x in texts) \
                   and not any(x in ACTIONS or x in ("(NEW", "PROJECT)") for x in texts):
                    close(pending); pending = None
                    agency = " ".join(w['text'] for w in ws)
                    continue
                # budget-line code at far left -> start a new change block
                code_w = next((w for w in ws if w['x0'] < 90 and CODE.match(w['text'])), None)
                if code_w:
                    close(pending)
                    pending = dict(part="I", agency=agency, budget_line=code_w['text'],
                                   sub_id="", boro="", fy1=0, fy2=0, fy3=0, fy4=0,
                                   sponsor="", title="", actions=[])
                    # a code row may also carry title words / an action on the same line
                    for w in ws:
                        if w is code_w: continue
                        if 90 <= w['x0'] < 520 and not MONEY.match(w['text']) and not BARE.match(w['text']):
                            pending['title'] += " " + w['text']
                        elif w['x0'] >= 520 and w['text'] in ACTIONS:
                            pending['actions'].append(w['text'])
                    continue
                if pending is None:
                    continue
                # within a pending block:
                #  - (CN) amount row -> the change amounts
                cn = [w for w in ws if MONEY.match(w['text'])]
                if cn:
                    for w in cn:
                        c = amt_col(w['x1'])
                        if c is not None:
                            pending[f"fy{c+1}"] = money(MONEY.match(w['text']).group(1))
                    continue
                #  - action words at right (ELIMINATE/SUBSTITUTE/(NEW PROJECT))
                acts = [w['text'] for w in ws if w['x0'] >= 520 and w['text'] in ACTIONS]
                if acts:
                    pending['actions'].extend(acts)
                # '(NEW' 'PROJECT)' action or title marker at right
                if any(w['x0'] >= 520 and w['text'] == "(NEW" for w in ws):
                    pending['actions'].append("NEW PROJECT")
                #  - title / boilerplate continuation (x0 ~ 96..510), skip bare baseline numbers
                for w in ws:
                    if 90 <= w['x0'] < 520 and not BARE.match(w['text']) \
                       and not MONEY.match(w['text']) and w['text'] not in ("(NEW", "PROJECT)"):
                        pending['title'] += " " + w['text']
            # end page
        close(pending)
    return projects

def write_out(projects, pdf_path, outdir, prefix, npages):
    os.makedirs(outdir, exist_ok=True)
    P = lambda n: os.path.join(outdir, f"{prefix}_{n}")
    cols = ["part", "agency", "budget_line", "sub_id", "boro", "fy1", "fy2", "fy3", "fy4",
            "sponsor", "title", "building_code", "school_code", "action"]
    with open(P("capital_projects.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for p in projects: w.writerow([p.get(c, "") for c in cols])

    by_ag = defaultdict(lambda: [0, 0])
    for p in projects:
        by_ag[p['agency']][0] += p['fy1']; by_ag[p['agency']][1] += 1
    L = [f"CAPITAL (§254) EXTRACTION — NOT RECONCILABLE ({prefix})",
         f"source: {os.path.basename(pdf_path)} ({npages} pages)",
         "",
         "FY2025 is the Section-254 APPROPRIATION-CHANGES schedule ('Changes to Part I'), a",
         "different document type than FY2026/FY2027 'Capital Project Detail'. It contains NO",
         "'TOTALS FOR <agency> (N PROJECTS)' subtotal lines, so there is NOTHING to reconcile",
         "the FY27 way. It also has no borough / sub-id / council-sponsor columns (emitted empty).",
         "The single printed total is a citywide grand total ($15.28B), the whole adopted budget,",
         "not the sum of these changes. Numbers below are the sum of the printed (CN) change",
         "amounts per agency, provided for sanity only — there is no printed subtotal to check them",
         "against.",
         "",
         f"change blocks parsed: {len(projects)}",
         f"total FY2025 (CN) change amount: ${sum(p['fy1'] for p in projects):,}",
         "",
         f"{'AGENCY':48} {'sum FY2025 (CN)':>18} {'blocks':>8}"]
    for ag in sorted(by_ag):
        s, n = by_ag[ag]
        L.append(f"{ag[:48]:48} {s:>18,} {n:>8}")
    rep = "\n".join(L)
    open(P("capital_reconciliation.txt"), "w").write(rep + "\n")
    return rep

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--prefix", required=True)
    a = ap.parse_args()
    projects = parse(a.pdf)
    with pdfplumber.open(a.pdf) as pdf:
        npages = len(pdf.pages)
    print(write_out(projects, a.pdf, a.outdir, a.prefix, npages))

if __name__ == "__main__":
    main()
