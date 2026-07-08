#!/usr/bin/env python3
"""
Parse the EARLY-ERA (FY2009-FY2014) NYC Council Schedule C documents, which parse_schedule_c.py
cannot read (0 summary blocks).

How the early era differs
-------------------------
FY2015+ Schedule C lists discretionary awards as EIN-anchored tables (member / organization /
EIN / $amount), which parse_schedule_c.py reconciles category-by-category. The FY2009-FY2014
documents have NO award-level EIN tables at all: the discretionary designations were made
*post-adoption*, so the organization-level detail for these years lives in the Transparency
Resolutions (see data/fyNN/transparency-resolutions/), not here.

What these documents DO contain, per category, is a reconcilable **initiatives summary**:

    CHILDREN'S SERVICES                         <- category header (all caps)
    Summary of Fiscal 2013 Council Initiatives: <- (FY11-14; absent FY09/FY10)
    Children's Services
    Agency Initiative Funding                   <- table header ('Funding', not 'Amount')
    ACS  Early Learn Child Care Restoration  $39,304,000
    ...
    TOTAL $61,368,000                           <- printed category total

followed by prose per-initiative detail blocks (Initiative / Agency / Amount / Description...).

This parser extracts the initiatives summary and reconciles each category's row sum against its
printed TOTAL — the same authoritative reconciliation parse_schedule_c.py does. It emits:
  {prefix}_schedule_c_initiatives.csv   category, agencies, initiative, amount
  {prefix}_schedule_c_reconciliation.txt
It does NOT emit awards/appendix files (no such data in these documents; join the Transparency
Resolutions for the org-level designations).
"""
import re, csv, os, argparse
from collections import defaultdict

TABLE_HDR = re.compile(r'(?i)^Agency\s+Initiative\s+Funding\b')
ROW = re.compile(r'^(.*?\S)\s*\$([\d,]+)\s*$')   # amount may be glued to text: '...(Harvest Home)$60,000'
AMT_ONLY = re.compile(r'^\$([\d,]+)\s*$')      # a right-aligned amount alone on its own line
TOTAL = re.compile(r'(?i)^TOTAL\s+\$([\d,]+)\s*$')
RUNHDR = re.compile(r'(?i)adopted expense budget adjustment|new york city council finance division'
                    r'|^fiscal year \d{4}|page \|')
SUMMARY_OF = re.compile(r'(?i)^Summary of Fiscal')

def money(s): return int(s.replace(",", "").strip() or 0)
def norm(s): return re.sub(r'\s+', ' ', s).strip().upper()

def load_pages(pdf):
    import pypdf
    return {i + 1: (p.extract_text() or "") for i, p in enumerate(pypdf.PdfReader(pdf).pages)}

def is_caps_header(s):
    """A category header: an all-caps line of words (allow &'.,-/ and digits), 4-48 chars, not a
    running header / table row / boilerplate."""
    if not (4 <= len(s) <= 48): return False
    if RUNHDR.search(s): return False
    if '$' in s: return False
    letters = [c for c in s if c.isalpha()]
    if not letters or any(c.islower() for c in letters): return False
    return bool(re.match(r"^[A-Z0-9 &'.,\-/()]+$", s))

def parse(pages):
    lines = []
    for pn in sorted(pages):
        for ln in pages[pn].split("\n"):
            s = ln.replace("\xa0", " ").strip()
            s = re.sub(r'(?<=\d),\s+(?=\d)', ',', s)   # fix amounts split as '$1,499, 254'
            if s:
                lines.append(s)
    initiatives = []          # (category, agency, initiative, amount)
    recon = {}                # category -> printed TOTAL
    order = []                # category order as encountered
    last_header = None
    in_table = False
    cur_cat = None
    cur_rows = []
    buf = []                  # wrapped initiative-text lines awaiting their amount

    def add_row(body, amt):
        body = re.sub(r'\s+', ' ', body).strip()
        toks = body.split(" ", 1)
        cur_rows.append((toks[0] if toks else "", toks[1] if len(toks) > 1 else "", amt))

    for s in lines:
        if TABLE_HDR.match(s):
            in_table = True; cur_rows = []; buf = []
            cur_cat = last_header or f"CATEGORY_{len(order) + 1}"
            continue
        if not in_table:
            if is_caps_header(s):
                last_header = s
            continue
        # inside a summary table
        mt = TOTAL.match(s)
        if mt:
            total = money(mt.group(1))
            cat = cur_cat
            if norm(cat) not in {norm(c) for c in order}:
                order.append(cat)
            recon[cat] = recon.get(cat, 0) + total
            for ag, init, amt in cur_rows:
                initiatives.append((cat, ag, init, amt))
            in_table = False; cur_rows = []; cur_cat = None; buf = []
            continue
        ao = AMT_ONLY.match(s)
        if ao:                                  # amount alone -> close out the buffered wrap text
            if buf:
                add_row(" ".join(buf), money(ao.group(1))); buf = []
            continue
        m = ROW.match(s)
        if m:                                   # 'text $amount' -> a complete row (prepend any wrap)
            add_row(" ".join(buf) + " " + m.group(1), money(m.group(2))); buf = []
            continue
        # a plain text line: a wrapped initiative-name continuation
        buf.append(s)
    return initiatives, recon, order

def write_out(initiatives, recon, order, pdf_path, outdir, prefix, npages):
    os.makedirs(outdir, exist_ok=True)
    P = lambda n: os.path.join(outdir, f"{prefix}_{n}")
    with open(P("schedule_c_initiatives.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["category", "agencies", "initiative", "amount"])
        for c, ag, nm, amt in initiatives:
            w.writerow([c, ag, nm, amt])
    isum = defaultdict(int)
    for c, ag, nm, amt in initiatives:
        isum[c] += amt
    L = [f"SCHEDULE C RECONCILIATION  ({prefix})  [parser: parse_schedule_c_legacy.py, early-era]",
         f"source: {os.path.basename(pdf_path)}  ({npages} pages)",
         "",
         "Early-era Schedule C: initiatives-summary reconciliation only. These documents carry NO",
         "award-level EIN tables (post-adoption designations live in the Transparency Resolutions),",
         "so no awards/appendix files are emitted.",
         "",
         f"{'CATEGORY':52} {'initiatives':>14} {'printed':>14}  status"]
    ok = 0; gi = 0; gp = 0
    for c in order:
        i = isum.get(c, 0); p = recon.get(c) or 0; gi += i; gp += p
        if i == p and p: ok += 1
        L.append(f"{c[:52]:52} {i:>14,} {p:>14,}  {'OK' if (i == p and p) else f'DIFF {i - p:+,}'}")
    L.append(f"{'GRAND TOTAL':52} {gi:>14,} {gp:>14,}  {ok}/{len(order)} categories exact")
    L.append(f"\ninitiatives rows: {len(initiatives)}")
    rep = "\n".join(L)
    open(P("schedule_c_reconciliation.txt"), "w").write(rep + "\n")
    return rep, ok, len(order)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("--outdir", required=True); ap.add_argument("--prefix", required=True)
    a = ap.parse_args()
    pages = load_pages(a.pdf)
    initiatives, recon, order = parse(pages)
    rep, ok, n = write_out(initiatives, recon, order, a.pdf, a.outdir, a.prefix, max(pages))
    print(rep)

if __name__ == "__main__":
    main()
