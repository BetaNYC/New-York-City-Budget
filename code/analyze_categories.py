#!/usr/bin/env python3
"""Category-column collision scan for Schedule C (analogous to the initiative scan).

Tiers:
  MECHANICAL  — same category differing only by CASE, apostrophe style, '&'/'and',
                whitespace, a trailing '.', or the known 'ORGANZIATIONS' typo. Safe merges.
  EDITORIAL   — additionally ignores a trailing Services/Initiative(s) suffix, a
                '(formerly ...)' annotation, possessive "'s", and simple plural 's'.
                These are alignment SUGGESTIONS — some are genuine policy renames
                (e.g. Senior Services -> Older Adult Services) and need a human call.
"""
import csv, re, json, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(REPO, "data", "combined", "all_years_initiatives.csv")
OUT = os.path.join(REPO, "data", "combined", "category_collisions.json")
FY = [f"FY{n:02d}" for n in range(9, 28)]

def yrs(s): return [y for y in FY if y in s]

def mech_norm(c):
    t = c.strip().replace("’", "'").replace("‘", "'")
    t = re.sub(r"\s*&\s*", " and ", t)
    t = t.rstrip(".")
    t = re.sub(r"\s+", " ", t).strip().lower()
    t = t.replace("organziations", "organizations")   # known misspelling FY11-13
    return t

_SUFFIX = re.compile(r"\b(services|initiatives|initiative)\b\s*$")
def edit_norm(c):
    t = mech_norm(c)
    t = re.sub(r"\s*\(formerly[^)]*\)", "", t)          # "(formerly senior services)"
    t = re.sub(r",?\s*formerly .*$", "", t)             # ", formerly ..."
    t = t.replace("'s", "")                              # possessive: children's -> children
    for _ in range(2):                                   # peel up to two trailing suffix words
        t = _SUFFIX.sub("", t).strip()
    t = re.sub(r"\b(\w{4,})s\b", r"\1", t)               # crude singular: organizations->organization
    t = re.sub(r"\s+", " ", t).strip()
    return t

rows = list(csv.DictReader(open(SRC)))
years = defaultdict(set); amt = defaultdict(float)
for r in rows:
    c = r["category"]; years[c].add(r["year"])
    try: amt[c] += float(r["amount"] or 0)
    except ValueError: pass

def stat(c): return {"spelling": c, "years": yrs(years[c]), "n_years": len(yrs(years[c])), "amount": round(amt[c], 2)}

def pick_canonical(variants):
    """Prefer a not-ALL-CAPS variant (the modern Title-Case era); tie-break by dollars."""
    non_caps = [v for v in variants if v != v.upper()]
    pool = non_caps or variants
    dom = max(pool, key=lambda v: amt[v])
    return dom.replace("’", "'"), (not non_caps)  # (canonical, casing_needs_review)

mech_of = {c: mech_norm(c) for c in years}
edit_of = {c: edit_norm(c) for c in years}

# Editorial super-groups that merge across ≥2 DISTINCT mechanical clusters are the ones
# worth surfacing (a suffix / plural / possessive drift that mechanical alone kept apart).
edit_members = defaultdict(list)
for c in years: edit_members[edit_of[c]].append(c)
tier2 = {k: v for k, v in edit_members.items() if len({mech_of[c] for c in v}) > 1}
tier2_mechkeys = {mech_of[c] for v in tier2.values() for c in v}

# Mechanical Tier-1 = case/typo/apostrophe-only merges NOT absorbed into an editorial group.
mech_members = defaultdict(list)
for c in years: mech_members[mech_of[c]].append(c)
mech = {k: v for k, v in mech_members.items() if len(v) > 1 and k not in tier2_mechkeys}
edit_only = tier2

# "(formerly X)" annotations — explicit rename evidence a maintainer should decide on.
renames = []
for c in years:
    m = re.search(r"formerly ([^)]+)", c, re.I)
    if m: renames.append({"annotated": c, "former_name": m.group(1).strip().rstrip(")")})

def pack(gmap, tier):
    out = []
    for key, variants in gmap.items():
        canonical, casing_todo = pick_canonical(variants)
        vs = sorted((stat(v) for v in variants), key=lambda d: (-d["amount"]))
        out.append({
            "tier": tier, "normalized": key, "canonical": canonical,
            "casing_needs_review": casing_todo,
            "combined_amount": round(sum(v["amount"] for v in vs), 2),
            "n_variants": len(vs),
            "combined_years": yrs(set().union(*[set(v["years"]) for v in vs])),
            "variants": vs,
        })
    out.sort(key=lambda d: -d["combined_amount"])
    return out

result = {"fy": FY, "distinct_categories": len(years),
          "mechanical_groups": pack(mech, "mechanical"),
          "editorial_groups": pack(edit_only, "editorial"),
          "renames": renames}
json.dump(result, open(OUT, "w"), indent=2)

def money(a): return f"${a:,.0f}"
print(f"distinct categories: {len(years)}")
print(f"MECHANICAL groups: {len(result['mechanical_groups'])} | EDITORIAL-only groups: {len(result['editorial_groups'])}\n")
for tier, key in (("MECHANICAL", "mechanical_groups"), ("EDITORIAL (review)", "editorial_groups")):
    print(f"===== {tier} =====")
    for g in result[key]:
        flag = "  ⚠ casing?" if g["casing_needs_review"] else ""
        print(f"  → {g['canonical']!r}  ({money(g['combined_amount'])}){flag}")
        for v in g["variants"]:
            print(f"       {v['spelling']!r:58} {v['years'][0]}–{v['years'][-1]} ({v['n_years']}y) {money(v['amount'])}")
    print()
