#!/usr/bin/env python3
"""
Parse an NYC Council 'Changes to the Executive Capital Budget Pursuant to Section 254'
supporting-detail PDF into structured project rows, reconciled against the printed
'TOTALS FOR <agency> (N PROJECTS)' subtotals.

Emits:
  {prefix}_capital_projects.csv   part, agency, budget_line, sub_id, boro, fy1..fy4, sponsor, title, building_code, school_code
  {prefix}_capital_reconciliation.txt

fy1 is the adoption year (e.g. FY2027), fy2..fy4 the three out-years.
Numeric/ID/borough fields are extracted deterministically; sponsor is split from the title
using an accent-normalized council-member roster (the two are glued together in the PDF text).
"""
import re, csv, os, argparse, unicodedata

# A data row: <AGCODE CODE> <AGCODE CODE> <BORO> <fy1> [<fy2..fy4>] <blob>.
# Two code-column layouts share this document:
#   * CITY items      -> budget line 'XX CC####',  sub id 'XX D####'/'XX DN###'; the blob after
#                        the amounts is SPONSOR glued to TITLE (e.g. 'BREWERAILEY ...').
#   * NON-CITY items  -> budget line 'XX MA####',  sub id 'XX 0N###'; the blob is the grantee
#                        ORGANIZATION NAME only — there is no council sponsor on these rows.
# Both code pairs must be accepted or the MA/0N rows fail to match, fall through to the
# agency-header branch, and (a) get dropped as projects while (b) the last one leaks a whole
# row's worth of text into the `agency` field of the CITY rows that follow it. (FY2027 bug.)
ROW = re.compile(r'^(\S+\s+(?:CC|MA)\w+)\s+(\S+\s+(?:D|0N)\w+)\s+([A-Z])\s+([\d,]+)((?:\s+\d[\d,]*)*)\s*(.*)$')
SUBTOTAL = re.compile(r'^([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*TOTALS FOR\s+(.+?)\s+\((\d+)\s+PROJECTS?\)', re.I)
PART = re.compile(r'^(I{1,3})\.$')
BS = re.compile(r'\bB:\s*(\S+)|\bS:\s*(\S+)')

def money(s): return int(str(s).replace(",","").strip() or 0)
def deaccent(s): return "".join(c for c in unicodedata.normalize("NFD",s) if unicodedata.category(c)!="Mn")

def load_pages(pdf):
    import pypdf
    return {i+1:(p.extract_text() or "") for i,p in enumerate(pypdf.PdfReader(pdf).pages)}

def load_roster(awards_csvs):
    """Union of council-member surnames across years, upper+deaccented, for sponsor splitting."""
    r=set()
    for p in awards_csvs:
        if os.path.exists(p):
            for row in csv.DictReader(open(p)):
                m=row.get("member","").strip()
                if m: r.add(deaccent(m).upper())
    r |= {"SPEAKER","BRONX DELEGATION","BROOKLYN DELEGATION","QUEENS DELEGATION",
          "MANHATTAN DELEGATION","STATEN ISLAND DELEGATION","BRONX","BROOKLYN","QUEENS","MANHATTAN"}
    return r

def split_sponsor(blob, roster):
    """blob = 'SPONSOR[, SPONSOR...]TITLE' with sponsor glued to title. Peel roster names off the front."""
    raw=blob.strip()
    up=deaccent(raw).upper()
    names=[]; pos=0
    # sort roster by length desc so 'BROOKLYN DELEGATION' matches before 'BROOKLYN'
    R=sorted(roster,key=len,reverse=True)
    while True:
        seg=up[pos:].lstrip()
        skip=len(up[pos:])-len(seg); pos+=skip
        hit=None
        for nm in R:
            if seg.startswith(nm):
                # ensure the char after the name isn't a lowercase letter continuation of a longer word
                nxt=seg[len(nm):len(nm)+1]
                if nxt=="" or not nxt.isalpha() or nxt.isupper():
                    hit=nm; break
        if not hit: break
        names.append(raw[pos:pos+len(hit)]); pos+=len(hit)
        after=up[pos:]
        m=re.match(r'\s*,\s*', after)   # comma-separated co-sponsors
        if m: pos+=m.end()
        else: break
    sponsor=", ".join(n.strip() for n in names) if names else ""
    title=raw[pos:].strip(" ,")
    return sponsor, title

def parse(pages):
    lines=[]
    for pn in sorted(pages):
        for ln in pages[pn].split("\n"):
            s=ln.strip()
            s=re.sub(r'(?<=\d),\s+(?=\d)', ',', s)   # fix amounts split as '4, 500,000'
            if s and not re.match(r'^Page \d+ of', s) and "PURSUANT TO SECTION 254" not in s \
               and not s.startswith("FY 2027PROJECT") and not s.startswith("FY 2026PROJECT") \
               and not s.startswith("FY 2025PROJECT") and s not in ("CAPITAL PROJECT DETAIL",):
                lines.append(s)
    projects=[]; subtotals=[]; part=""; agency=""; pending=None
    KNOWN_HEADERS={"NON-CITY CAPITAL PROJECT DETAIL","CAPITAL PROJECT DETAIL BY NON-CITY ENTITY",
                   "TABLE OF CONTENTS"}
    def close(p):
        if not p: return
        title=re.sub(r'\s+',' ',p["title"]).strip()
        bc=sc=""
        for b,s in BS.findall(title):
            if b: bc=b
            if s: sc=s
        title=BS.sub("",title).strip()
        p["title"]=title; p["building_code"]=bc; p["school_code"]=sc
        projects.append(p)
    for s in lines:
        pm=PART.match(s)
        if pm: part=pm.group(1); continue
        sm=SUBTOTAL.match(s)
        if sm:
            close(pending); pending=None
            subtotals.append(dict(part=part,agency=sm.group(5).strip(),
                fy1=money(sm.group(1)),projects=int(sm.group(6))))
            continue
        rm=ROW.match(s)
        if rm:
            close(pending)
            bl,sub,boro,f1,outs,blob=rm.groups()
            ov=[money(x) for x in outs.split()] if outs.strip() else []
            ov+= [0,0,0]
            # Non-city rows (sub id '0N###') have no council sponsor: the whole blob is the
            # grantee org name. Flag them so the sponsor-splitter leaves the title intact
            # rather than peeling a leading roster word (e.g. 'BROOKLYN' off 'BROOKLYN BALLET').
            noncity=sub.split()[-1].startswith("0N")
            pending=dict(part=part,agency=agency,budget_line=re.sub(r'\s+',' ',bl),
                sub_id=re.sub(r'\s+',' ',sub),boro=boro,fy1=money(f1),fy2=ov[0],
                fy3=ov[1],fy4=ov[2],sponsor="",title=blob,_noncity=noncity)
            continue
        # agency header: all-caps line, not a row/subtotal, not a known section header
        if pending is None or True:
            if s.isupper() and len(s)>3 and s not in KNOWN_HEADERS and not s.startswith("TOTALS FOR"):
                # could be an agency header OR a title continuation. Treat as agency only if no pending row.
                if pending is None:
                    agency=s; continue
        # otherwise: title continuation of the pending row
        if pending is not None:
            pending["title"]+=" "+s
    close(pending)
    return projects, subtotals

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("pdf")
    ap.add_argument("--outdir",required=True); ap.add_argument("--prefix",required=True)
    ap.add_argument("--roster",nargs="*",default=[])
    a=ap.parse_args(); os.makedirs(a.outdir,exist_ok=True)
    pages=load_pages(a.pdf)
    roster=load_roster(a.roster)
    projects,subtotals=parse(pages)
    for p in projects:
        if p.pop("_noncity", False):
            continue                       # non-city grantee row: title already whole, no sponsor
        p["sponsor"],p["title"]=split_sponsor(p["title"],roster)

    P=lambda n: os.path.join(a.outdir,f"{a.prefix}_{n}")
    cols=["part","agency","budget_line","sub_id","boro","fy1","fy2","fy3","fy4","sponsor","title","building_code","school_code"]
    with open(P("capital_projects.csv"),"w",newline="") as f:
        w=csv.writer(f); w.writerow(cols)
        for p in projects: w.writerow([p.get(c,"") for c in cols])

    # reconcile fy1 per agency (Part I only; parts II/III repeat structure) vs subtotals
    from collections import defaultdict
    got=defaultdict(int); cntp=defaultdict(int)
    for p in projects:
        got[(p["part"],p["agency"])]+=p["fy1"]; cntp[(p["part"],p["agency"])]+=1
    L=[f"CAPITAL (§254) RECONCILIATION ({a.prefix})",
       f"source: {os.path.basename(a.pdf)} ({max(pages)} pages)",
       f"projects parsed: {len(projects)} | agency subtotals: {len(subtotals)}",
       f"total FY1 (all projects): ${sum(p['fy1'] for p in projects):,}\n",
       f"{'PART/AGENCY':52} {'proj$':>14} {'printed$':>14} {'n':>4} {'pn':>4}  status"]
    ok=0
    for st in subtotals:
        key=(st["part"],st["agency"]); g=got.get(key,0); c=cntp.get(key,0)
        good = (g==st["fy1"] and c==st["projects"])
        if good: ok+=1
        L.append(f"{(st['part']+' '+st['agency'])[:52]:52} {g:>14,} {st['fy1']:>14,} {c:>4} {st['projects']:>4}  {'OK' if good else 'DIFF'}")
    L.append(f"\n{ok}/{len(subtotals)} agency subtotals reconcile (amount + project count)")
    rep="\n".join(L); open(P("capital_reconciliation.txt"),"w").write(rep+"\n")
    print(rep[:2000]); print("..."); print(f"\n{ok}/{len(subtotals)} subtotals OK | {len(projects)} projects -> {a.outdir}")

if __name__=="__main__": main()
