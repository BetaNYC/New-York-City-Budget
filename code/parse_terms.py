#!/usr/bin/env python3
"""
Parse an NYC Council 'Terms and Conditions' PDF (reporting conditions attached to
appropriations) into structured rows. Format is stable FY25-FY27.

Emits:
  {prefix}_terms_and_conditions.csv  item_number, agency_name, agency_code, units_of_appropriation,
                                      num_units, report_deadlines, coverage_period, condition_text
"""
import re, csv, os, argparse

HEADER = re.compile(r'^(\d{1,3})\.\s+(.+?\S)\s+\((\d{3})\)\s*$')
UA = re.compile(r'^Unit of Appropriation\s+\[?(\w+)\]?')
DATE = re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b')
PERIOD = re.compile(r'(?i)period\s+beginning\s+(.+?)\s+and\s+ending\s+(.+?)[.,;]')

def load_pages(pdf):
    import pypdf
    return {i+1:(p.extract_text() or "") for i,p in enumerate(pypdf.PdfReader(pdf).pages)}

def parse(pages):
    lines=[]
    for pn in sorted(pages):
        for ln in pages[pn].split("\n"):
            s=ln.replace("\xa0"," ").replace("‐","-").strip()   # FY26 uses non-breaking spaces
            if not s: continue
            if re.match(r'^Page \d+ of \d+$', s) or re.match(r'^\d{1,3}$', s): continue
            if re.match(r'(?i)^fiscal (year )?20\d\d', s) and "condition" not in s.lower(): continue
            if re.match(r'(?i)^terms and conditions$', s): continue
            lines.append(s)
    items=[]; cur=None
    for s in lines:
        h=HEADER.match(s)
        if h:
            if cur: items.append(cur)
            cur=dict(item_number=int(h.group(1)), agency_name=h.group(2).strip(),
                     agency_code=h.group(3), units=[], text=[])
            continue
        if cur is None: continue
        u=UA.match(s)
        if u and not cur["text"]:            # UA lines come before the condition text
            cur["units"].append(u.group(1)); continue
        cur["text"].append(s)
    if cur: items.append(cur)
    # normalize (fix soft-hyphen/space artifacts like 'appropriatio n')
    out=[]
    for it in items:
        txt=re.sub(r'\s+',' '," ".join(it["text"])).strip()
        txt=re.sub(r'(\w)\s-\s(\w)', r'\1\2', txt)   # 'semi- annual' -> 'semiannual' is too aggressive? keep mild
        dates=sorted(set(m.group(0) for m in DATE.finditer(txt)))
        pm=PERIOD.search(txt)
        period=f"{pm.group(1)} to {pm.group(2)}" if pm else ""
        out.append(dict(item_number=it["item_number"], agency_name=it["agency_name"],
            agency_code=it["agency_code"], units_of_appropriation="; ".join(it["units"]),
            num_units=len(it["units"]), report_deadlines="; ".join(dates),
            coverage_period=period, condition_text=txt))
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("pdf")
    ap.add_argument("--outdir",required=True); ap.add_argument("--prefix",required=True)
    a=ap.parse_args(); os.makedirs(a.outdir,exist_ok=True)
    pages=load_pages(a.pdf); items=parse(pages)
    cols=["item_number","agency_name","agency_code","units_of_appropriation","num_units",
          "report_deadlines","coverage_period","condition_text"]
    p=os.path.join(a.outdir,f"{a.prefix}_terms_and_conditions.csv")
    with open(p,"w",newline="") as f:
        w=csv.writer(f); w.writerow(cols)
        for it in items: w.writerow([it[c] for c in cols])
    from collections import Counter
    ag=Counter(it["agency_name"] for it in items)
    print(f"{a.prefix}: {len(items)} conditions across {len(ag)} agencies | "
          f"{sum(it['num_units'] for it in items)} UA references | "
          f"{sum(1 for it in items if it['report_deadlines'])} with explicit deadlines")
    print("  top agencies:", ", ".join(f"{n}({c})" for n,c in ag.most_common(4)))
    print("  ->", p)

if __name__=="__main__": main()
