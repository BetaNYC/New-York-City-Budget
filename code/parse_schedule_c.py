#!/usr/bin/env python3
"""
Parse an NYC Council 'Adopted Expense Budget Adjustment Summary' (Schedule C) PDF
into reconciled structured data. Year-robust: categories are derived from each
document's own Table of Contents, and every category is reconciled against the
document's printed TOTAL line.

Emits (to --outdir, prefixed with --prefix):
  *_schedule_c_initiatives.csv   category, agencies, initiative, amount   (reconciles to printed TOTALs)
  *_schedule_c_awards.csv        category, initiative, award_type, member, organization, program, ein, amount, agency, purpose
  *_appendix_a_aging.csv         member, organization, program, ein, amount, purpose
  *_appendix_b_local.csv         member, organization, program, ein, amount, agency, purpose
  *_appendix_c_youth.csv         member, organization, program, ein, amount, purpose
  *_schedule_c_reconciliation.txt

Money columns are extracted deterministically via EIN+$amount anchors (never model-transcribed);
council-member names are derived from the document itself so the parser isn't pinned to one roster.
"""
import re, csv, os, argparse

RUNHDR  = re.compile(r'(?i)^fiscal year \d{4} adopted expense budget adjustment summary')
ANCHOR  = re.compile(r'(\d{2}-?\d{7})\s+\$([\d,]+)((?:\s+[A-Z]{2,6}(?:/[A-Z]{2,6})?)?)')
AMT_END = re.compile(r'\$([\d,]+)\s*$')
NAME_LINE = re.compile(r"^[A-Z][A-Za-z.'\-]+(?: [A-Z][A-Za-z.'\-]+){0,2}$")
TOC_LINE  = re.compile(r'^(.+?)\s*\.{3,}\s*\d+\s*$')

BOUNDARY = ("Agency:","U/A:","Scope of Service","Designation Method","Target Population",
    "First Year Funded","Area(s) Served","Members Providing","This initiative",
    "Council Initiatives","Agency Initiative Amount","TOTAL")
NOISE_WORDS = {"Fiscal","Total","Agency","Initiative","Amount","Appendix","Schedule","Council",
    "Purpose","Legal","Name","Tax","Sponsor","Community","Development","Designation","Method"}

def money(s): return int(str(s).replace(",","").replace("$","").strip())
def norm(s):  return re.sub(r'\s+',' ',s).strip().upper()
def eind(e):  return e.replace("-","")   # digits-only EIN for stable aggregation

def load_pages(pdf):
    import pypdf
    return {i+1:(p.extract_text() or "") for i,p in enumerate(pypdf.PdfReader(pdf).pages)}

def derive_categories(pages):
    """Read the Table of Contents; return ordered canonical category names (ToC casing)."""
    toc_pg=None
    for pn in sorted(pages):
        if pn>8: break
        # FY25-FY27 head the contents page 'Table of Contents'; some earlier years (e.g. FY2018)
        # head it just 'Contents'. Match either as a standalone heading line.
        if re.search(r'(?im)^\s*(?:table of )?contents\s*$', pages[pn]): toc_pg=pn; break
    cats=[]
    if toc_pg:
        for pn in range(toc_pg, toc_pg+3):
            for ln in pages.get(pn,"").split("\n"):
                m=TOC_LINE.match(ln.strip())
                if not m: continue
                name=m.group(1).strip()
                u=name.upper()
                if any(k in u for k in ("SCHEDULE C INTRO","TABLE OF CONTENT","APPENDIX")): continue
                if len(name)<4: continue
                cats.append(name)
    # dedupe preserving order
    seen=set(); out=[]
    for c in cats:
        if norm(c) not in seen: seen.add(norm(c)); out.append(c)
    return out

def first_heading_page(pages, marker, after=5):
    for pn in sorted(pages):
        if pn<=after: continue
        for ln in pages[pn].split("\n"):
            if ln.strip().lower().startswith(marker.lower()): return pn
    return None

def build_roster(pages, lo, hi):
    from collections import Counter
    cnt=Counter()
    for pn in range(lo,hi):
        for ln in pages.get(pn,"").split("\n"):
            s=ln.strip()
            if NAME_LINE.match(s) and not any(w in s.split() for w in NOISE_WORDS) and len(s)<=28:
                cnt[s]+=1
    return {n for n,c in cnt.items() if c>=5 and not n.endswith(".") and n!="Delegation"}

def split_org_program(text):
    text=re.sub(r'\s+',' ',text).strip()
    for sep in (" – "," - "):
        if sep in text:
            org,prog=text.split(sep,1); return org.strip(),prog.strip()
    return text,""

# ---------- initiatives (summary blocks, mapped to ToC category order) ----------
def parse_initiatives(pages, lo, hi, cats):
    """Segment each summary block ('Agency Initiative Amount' -> 'TOTAL $x') and map the Nth
    block to the Nth ToC category. Works whether the category heading prints before the block
    (FY27) or after it (FY26)."""
    canon={norm(c):c for c in cats}
    lines=[]
    for pn in range(lo,hi):
        for ln in pages[pn].split("\n"):
            s=ln.strip()
            if s: lines.append(s)
    head_idx=[(i,canon[norm(s)]) for i,s in enumerate(lines) if norm(s) in canon]
    # collect summary blocks with their line span
    blocks=[]; in_block=False; start=None; buf=[]; rows=[]
    for i,s in enumerate(lines):
        if re.search(r'(?i)agency\s+initiative\s+amount', s):
            in_block=True; start=i; buf=[]; rows=[]; continue
        if not in_block: continue
        mt=re.match(r'(?i)^total\b.*?\$([\d,]+)', s)
        if mt:
            blocks.append((start,i,rows,money(mt.group(1)))); in_block=False; buf=[]; rows=[]; continue
        if RUNHDR.match(s) or re.match(r'^\d{1,3}$',s) or norm(s) in canon \
           or re.search(r'(?i)council initiatives',s):
            buf=[]; continue
        m=AMT_END.search(s)
        if m:
            pre=s[:m.start()].strip()
            if pre: buf.append(pre)
            rows.append((re.sub(r'\s+',' '," ".join(buf)).strip(), money(m.group(1)))); buf=[]
        else:
            buf.append(s)
    # Primary labeling = ToC order (block[i] -> cats[i]); validated below against each block's
    # adjacent heading. Detect whether headings sit just BEFORE the AIA or just AFTER the TOTAL.
    hd={i:c for i,c in head_idx}; K=8
    before_hits=sum(any((a-d) in hd for d in range(1,K+1)) for (a,t,_,_) in blocks)
    after_hits =sum(any((t+d) in hd for d in range(1,K+1)) for (a,t,_,_) in blocks)
    before_mode=before_hits>=after_hits
    def adj_heading(a,t):
        for i in (range(a-1,a-K-1,-1) if before_mode else range(t+1,t+K+1)):
            if i in hd: return hd[i]
        return None
    # Primary labeling: ToC order (block[i] -> cats[i]). The document is organized in ToC order and
    # every category that has a Council-Initiatives summary contributes exactly one block, in order.
    # (A trailing category with no summary block -- e.g. FY25 Youth Services, funded only via the
    # Youth Discretionary appendix -- correctly maps to no block.) Adjacency is used only to warn.
    out=[]; recon={}; mism=[]
    for bi,(a,t,rows,total) in enumerate(blocks):
        cat=cats[bi] if bi<len(cats) else f"UNMAPPED_BLOCK_{bi}"
        adj=adj_heading(a,t)
        if adj and norm(adj)!=norm(cat): mism.append((bi,cat,adj))
        recon[cat]=total
        for raw,amt in rows:
            m=re.match(r'^([A-Z][A-Za-z]{1,5}(?:[/,]\s?[A-Z][A-Za-z]{1,5})*)\s+(.*)$', raw)
            ag,name=(m.group(1),m.group(2)) if (m and raw.split()[0].isupper()) else ("",raw)
            out.append((cat,ag.strip(),name.strip(),amt))
    if len(blocks)!=len(cats):
        print(f"[warn] {len(blocks)} summary blocks vs {len(cats)} ToC categories "
              f"(trailing category with no main-body summary maps to no block)")
    return out, recon, len(blocks)

# ---------- main-body awards (header-driven state machine) ----------
def parse_awards(pages, lo, hi, cats, roster):
    canon={norm(c):c for c in cats}
    out=[]; cur_cat=None; cur_init=None; mode=None; ip_purpose=False
    buf=[]; member_hold=""; pending=None

    def emit(rec):
        head=re.sub(r'\s+',' '," ".join(rec["org"])).strip()
        member=rec["member"]
        if not member:
            toks=head.split()
            for k in (3,2,1):
                if " ".join(toks[:k]) in roster: member=" ".join(toks[:k]); head=" ".join(toks[k:]); break
        org,prog=split_org_program(head)
        out.append(dict(category=rec["cat"], initiative=rec["init"] or "",
            award_type="member_item" if member else "initiative_provider",
            member=member, organization=org, program=prog, ein=eind(rec["ein"]),
            amount=rec["amt"], agency=rec["agency"],
            purpose=re.sub(r'\s+',' '," ".join(rec["purpose"])).strip()))
    def flush():
        nonlocal pending
        if pending: emit(pending); pending=None

    lines=[]
    for pn in range(lo,hi):
        for ln in pages[pn].split("\n"):
            s=ln.strip()
            if s and not RUNHDR.match(s) and not re.match(r'^\d{1,3}$',s): lines.append(s)

    def looks_purpose(s):
        return bool(re.match(r"(?i)^(funds?|finds?|funding|to support|to provide|to defray|to assist|"
                             r"to enhance|to fund|to ensure|to cover|to |support|provide|provides)\b", s)) \
               or (s[:1].islower())

    for s in lines:
        if norm(s) in canon:
            flush(); cur_cat=canon[norm(s)]; cur_init=None; mode=None; buf=[]; member_hold=""; continue
        low=s.lower()
        if "council member" in low and "legal name" in low:
            flush(); mode="MI"; buf=[]; member_hold=""; continue
        if low.startswith("legal name of organization"):
            flush(); mode="IP"; ip_purpose=("purpose" in low); buf=[]; member_hold=""; continue
        if any(s.startswith(b) for b in BOUNDARY):
            flush(); buf=[]; member_hold=""; continue
        m=ANCHOR.search(s)
        if m:
            pre=s[:m.start()].strip(); ein=m.group(1); amount=money(m.group(2)); agency=m.group(3).strip()
            ptail=s[m.end():].strip()
            if mode=="IP":
                # org = trailing non-purpose buf lines + pre (drops any bled-in prior purpose)
                org=[x for x in buf if not looks_purpose(x)] + ([pre] if pre else [])
                flush()
                pending=dict(cat=cur_cat, init=cur_init, member="", org=org, ein=ein, amt=amount,
                             agency=agency, purpose=([ptail] if ptail else []))
                buf=[]
            else:  # MI
                org=buf+([pre] if pre else [])
                flush()
                pending=dict(cat=cur_cat, init=cur_init, member=member_hold, org=org, ein=ein, amt=amount,
                             agency=agency, purpose=([ptail] if ptail else []))
                buf=[]; member_hold=""
        else:
            mm=AMT_END.search(s)
            if mm and not re.search(r'\d{2}-?\d{7}', s):     # initiative header 'Name $amount'
                flush(); cur_init=s[:mm.start()].strip(); buf=[]; member_hold=""; continue
            toks=s.split(); mk=""
            for k in (3,2,1):
                if " ".join(toks[:k]) in roster: mk=" ".join(toks[:k]); break
            if mk and mode!="IP":                            # new member-item record starts
                flush(); member_hold=mk
                rest=" ".join(toks[len(mk.split()):]).strip(); buf=[rest] if rest else []
            else:
                if pending is not None and (mode=="MI" or (mode=="IP" and ip_purpose and looks_purpose(s))):
                    pending["purpose"].append(s)
                else:
                    buf.append(s)
    flush()
    return out

# ---------- appendices (member | org-program | taxid | amount | [agency] | purpose) ----------
def parse_appendix(pages, lo, hi, roster, has_agency, has_purpose):
    text="\n".join(l for pn in range(lo,hi) for l in pages[pn].split("\n")
                   if not RUNHDR.match(l.strip()) and not re.match(r'^\d{1,3}$', l.strip()))
    ms=list(ANCHOR.finditer(text)); out=[]
    def find_member(hlines):
        for j in range(len(hlines)):
            toks=hlines[j].split()
            for k in (3,2,1):
                if " ".join(toks[:k]) in roster:
                    rest=" ".join(toks[k:])
                    return " ".join(toks[:k]), ([rest] if rest else [])+hlines[j+1:]
        return "", hlines
    for i,m in enumerate(ms):
        head=text[(ms[i-1].end() if i>0 else 0):m.start()]
        tail=text[m.end():(ms[i+1].start() if i+1<len(ms) else len(text))]
        hlines=[x.strip() for x in head.split("\n") if x.strip()]
        member,org_lines=find_member(hlines)
        org,prog=split_org_program(" ".join(org_lines))
        purpose=""
        if has_purpose:
            pl=[]
            for x in (l.strip() for l in tail.split("\n") if l.strip()):
                t=x.split()
                if any(" ".join(t[:k]) in roster for k in (3,2,1)): break
                pl.append(x)
            purpose=re.sub(r'\s+',' '," ".join(pl)).strip()
        out.append(dict(member=member, organization=org, program=prog, ein=eind(m.group(1)),
                        amount=money(m.group(2)), agency=(m.group(3).strip() if has_agency else ""),
                        purpose=purpose))
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("pdf")
    ap.add_argument("--outdir",required=True); ap.add_argument("--prefix",required=True)
    a=ap.parse_args(); os.makedirs(a.outdir,exist_ok=True)
    pages=load_pages(a.pdf); maxp=max(pages)
    cats=derive_categories(pages)
    apxA=first_heading_page(pages,"Appendix A")
    apxB=first_heading_page(pages,"Appendix B")
    apxC=first_heading_page(pages,"Appendix C")
    body_hi=apxA or maxp+1
    # body starts at the first real summary table ('Agency Initiative Amount'), skipping the
    # narrative intro (which repeats category words like 'Public Safety' as prose subheadings).
    body_lo=6
    for pn in sorted(pages):
        if pn>2 and re.search(r'(?i)agency\s+initiative\s+amount', pages[pn]): body_lo=max(6,pn-1); break
    roster=build_roster(pages,body_lo,maxp+1)

    inits,recon,nblocks=parse_initiatives(pages,body_lo,body_hi,cats)
    awards=parse_awards(pages,body_lo,body_hi,cats,roster)
    # cleanup: drop header-row artifacts; backfill purpose-polluted org names by EIN
    from collections import Counter, defaultdict as _dd
    HJ=("legal name","program name","council member","sponsor legal")
    awards=[r for r in awards if not any(h in r["organization"].lower() for h in HJ)]
    def _poll(o): return (not o) or bool(re.match(r'(?i)^(funds?|finds?|funding|to |support|provide|purpose)',o))
    nm=_dd(Counter)
    for r in awards:
        if not _poll(r["organization"]): nm[r["ein"]][r["organization"]]+=1
    for r in awards:
        if _poll(r["organization"]) and nm.get(r["ein"]):
            r["organization"]=nm[r["ein"]].most_common(1)[0][0]; r["_backfilled"]="1"
    aging=parse_appendix(pages,apxA,apxB,roster,False,True) if apxA else []
    local=parse_appendix(pages,apxB,apxC,roster,True, True) if apxB else []
    youth=parse_appendix(pages,apxC,maxp+1,roster,False,True) if apxC else []

    P=lambda n: os.path.join(a.outdir,f"{a.prefix}_{n}")
    with open(P("schedule_c_initiatives.csv"),"w",newline="") as f:
        w=csv.writer(f); w.writerow(["category","agencies","initiative","amount"])
        for c,ag,nm,amt in inits: w.writerow([c,ag,nm,amt])
    def wr(path,rows,cols):
        with open(path,"w",newline="") as f:
            w=csv.writer(f); w.writerow(cols)
            for r in rows: w.writerow([r.get(c,"") for c in cols])
    wr(P("schedule_c_awards.csv"),awards,["category","initiative","award_type","member","organization","program","ein","amount","agency","purpose"])
    wr(P("appendix_a_aging.csv"),aging,["member","organization","program","ein","amount","purpose"])
    wr(P("appendix_b_local.csv"),local,["member","organization","program","ein","amount","agency","purpose"])
    wr(P("appendix_c_youth.csv"),youth,["member","organization","program","ein","amount","purpose"])

    from collections import defaultdict
    isum=defaultdict(int)
    for c,ag,nm,amt in inits: isum[c]+=amt
    L=[]; ok=0; gi=0; gp=0
    L.append(f"SCHEDULE C RECONCILIATION  ({a.prefix})")
    L.append(f"source: {os.path.basename(a.pdf)}  ({maxp} pages)")
    L.append(f"sections: body 6..{body_hi-1} | A {apxA} | B {apxB} | C {apxC}")
    L.append(f"categories from ToC: {len(cats)} | summary blocks found: {nblocks}"
             f"{'  <-- MISMATCH' if nblocks!=len(cats) else ''} | roster: {len(roster)} members\n")
    L.append(f"{'CATEGORY':52} {'initiatives':>14} {'printed':>14}  status")
    for c in cats:
        i=isum.get(c,0); p=recon.get(c) or 0; gi+=i; gp+=p
        if i==p and p: ok+=1
        L.append(f"{c[:52]:52} {i:>14,} {p:>14,}  {'OK' if (i==p and p) else f'DIFF {i-p:+,}'}")
    L.append(f"{'GRAND TOTAL':52} {gi:>14,} {gp:>14,}  {ok}/{len(cats)} categories exact")
    mi=[r for r in awards if r['award_type']=='member_item']; ip=[r for r in awards if r['award_type']=='initiative_provider']
    L.append("")
    L.append(f"awards: {len(awards)} rows  ${sum(r['amount'] for r in awards):,}")
    L.append(f"  member items:         {len(mi):5d}  ${sum(r['amount'] for r in mi):,}")
    L.append(f"  initiative providers: {len(ip):5d}  ${sum(r['amount'] for r in ip):,}")
    L.append(f"appendix A (aging): {len(aging):5d} rows  ${sum(r['amount'] for r in aging):,}")
    L.append(f"appendix B (local): {len(local):5d} rows  ${sum(r['amount'] for r in local):,}")
    L.append(f"appendix C (youth): {len(youth):5d} rows  ${sum(r['amount'] for r in youth):,}")
    rep="\n".join(L); open(P("schedule_c_reconciliation.txt"),"w").write(rep+"\n")
    print(rep); print("\nWROTE ->",a.outdir)

if __name__=="__main__": main()
