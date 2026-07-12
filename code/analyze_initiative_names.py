#!/usr/bin/env python3
"""
Detect initiative-name fragmentation in all_years_initiatives.csv.

Two normalization tiers:
  MECHANICAL  - same underlying label differing only by case, whitespace,
                &/and, curly/straight quotes, a leading '*' marker, and
                surrounding punctuation. Content words are preserved.
                => high confidence these are the SAME initiative.
  AGGRESSIVE  - additionally drops punctuation and small stopwords and
                normalizes hyphen/slash spacing. Catches hyphenation,
                Oxford-comma, slash-vs-parens, and dropped-word variants.
                => candidates that need a human eye (may over-merge).

Emits JSON to stdout-adjacent file and prints a summary.
"""
import csv, re, json, sys, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "data", "combined", "all_years_initiatives.csv")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "data", "combined", "initiative_name_collisions.json")

FYORDER = [f"FY{n:02d}" for n in range(9, 28)]  # FY09..FY27

def norm_mechanical(s: str) -> str:
    t = s.strip()
    t = t.lstrip("*").strip()                 # leading footnote marker
    t = t.replace("’", "'").replace("‘", "'")   # curly -> straight apostrophe
    t = t.replace("“", '"').replace("”", '"')
    t = re.sub(r"\s*&\s*", " and ", t)        # & -> and
    t = t.lower()
    t = re.sub(r"\s+", " ", t).strip()
    t = t.strip(".,;:")                        # trailing punctuation
    return t

STOP = {"the","a","an","of","for","and","in","to","at","on","inc"}
def norm_aggressive(s: str) -> str:
    t = norm_mechanical(s)
    t = t.replace("/", " ").replace("-", " ")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = " ".join(w for w in t.split() if w not in STOP)
    t = re.sub(r"\s+", " ", t).strip()
    return t

rows = list(csv.DictReader(open(SRC)))

# raw spelling -> {years:set, amount:float, rows:int}
raw_stats = defaultdict(lambda: {"years": set(), "amount": 0.0, "rows": 0})
for r in rows:
    raw = r["initiative"]
    st = raw_stats[raw]
    st["years"].add(r["year"])
    st["rows"] += 1
    try:
        st["amount"] += float(r["amount"] or 0)
    except ValueError:
        pass

def build_groups(normfn):
    g = defaultdict(list)
    for raw in raw_stats:
        g[normfn(raw)].append(raw)
    return {k: v for k, v in g.items() if len(v) > 1}

mech = build_groups(norm_mechanical)
aggr = build_groups(norm_aggressive)

def yrs_sorted(s): return [y for y in FYORDER if y in s]

def pack(group_map, tier):
    out = []
    for key, spellings in group_map.items():
        variants = []
        for raw in sorted(spellings):
            st = raw_stats[raw]
            variants.append({
                "spelling": raw,
                "years": yrs_sorted(st["years"]),
                "n_years": len(st["years"]),
                "total_amount": round(st["amount"], 2),
                "rows": st["rows"],
            })
        # union of years across all spellings, and whether spellings ever overlap in a year
        allyears = set()
        overlap = False
        seen = defaultdict(int)
        for v in variants:
            for y in v["years"]:
                seen[y] += 1
        overlap = any(c > 1 for c in seen.values())
        allyears = yrs_sorted(seen.keys())
        out.append({
            "tier": tier,
            "normalized": key,
            "n_variants": len(variants),
            "combined_years": allyears,
            "spellings_overlap_in_a_year": overlap,
            "combined_amount": round(sum(v["total_amount"] for v in variants), 2),
            "variants": variants,
        })
    out.sort(key=lambda d: (-d["n_variants"], -d["combined_amount"]))
    return out

mech_out = pack(mech, "mechanical")
# aggressive-only = groups that appear under aggressive but NOT already caught mechanically
mech_keys_as_aggr = {norm_aggressive_key for norm_aggressive_key in
                     {norm_aggressive(s) for grp in mech.values() for s in grp}}
aggr_only_map = {k: v for k, v in aggr.items() if k not in mech_keys_as_aggr}
aggr_out = pack(aggr_only_map, "aggressive")

result = {
    "source": SRC,
    "total_rows": len(rows),
    "distinct_raw_initiatives": len(raw_stats),
    "fy_order": FYORDER,
    "mechanical_groups": mech_out,
    "aggressive_only_groups": aggr_out,
}
json.dump(result, open(OUT, "w"), indent=2)

print(f"source: {SRC}")
print(f"total rows: {len(rows)}  distinct raw initiative labels: {len(raw_stats)}")
print(f"MECHANICAL (high-confidence same-initiative) groups: {len(mech_out)}")
print(f"AGGRESSIVE-only (needs review) groups: {len(aggr_out)}")
print(f"initiative labels involved in a mechanical merge: {sum(g['n_variants'] for g in mech_out)}")
amp = [g for g in mech_out if any('&' in v['spelling'] for v in g['variants'])
       and any('&' not in v['spelling'] for v in g['variants'])]
print(f"  of which &-vs-AND: {len(amp)}")
print(f"wrote -> {OUT}")
