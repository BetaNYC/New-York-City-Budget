#!/usr/bin/env python3
"""Find repairs that replaced a name that was ALREADY CORRECT.

The prose detector is a regular expression, so a legal name containing 'Fund for', 'Services to',
'Support the' or similar trips it. If such a row is then 'recovered' from a candidate set that
happens to hold one name, a correct value is overwritten by a different one.

Test: original_organization is itself a legal name the Council published -- ideally for this very
(EIN, amount) in this very fiscal year -- yet it was replaced.
"""
import collections
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import build_lookups             # noqa: E402
import recover_org_names as ROG  # noqa: E402

canon = ROG.canon
CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"


def fy_of(p):
    m = re.search(r"[/\\]fy(\d{2})[/\\]", p)
    return 2000 + int(m.group(1)) if m else None


def main():
    per_year, pooled = build_lookups.load()
    sy, sp = per_year["strict"], pooled["strict"]
    published = set()
    for names in sp.values():
        published |= {canon(n) for n in names}

    rows = list(csv.DictReader(open(CROSSWALK, newline="", encoding="utf-8")))
    tiers = collections.Counter()
    hits = []
    for r in rows:
        if r["defect"] == "wrong_ein":
            continue
        orig, new = r["original_organization"].strip(), r["recovered_organization"].strip()
        co, cn = canon(orig), canon(new)
        if not co or co == cn:
            continue
        fy, key = fy_of(r["file"]), (r["ein"], int(r["amount"]))
        same = {canon(x) for x in sy.get(fy, {}).get(key, set())}
        anyk = {canon(x) for x in sp.get(key, set())}
        if co in same:
            tiers["ORIGINAL was the published name for this exact key AND year"] += 1
            hits.append(("A", r, sorted(sy.get(fy, {}).get(key, set()))))
        elif co in anyk:
            tiers["ORIGINAL was a published name for this key in another year"] += 1
            hits.append(("B", r, sorted(sp.get(key, set()))))
        elif co in published:
            tiers["ORIGINAL is a published legal name somewhere in the series"] += 1
            hits.append(("C", r, []))
    print("repairs that replaced a string which was itself a published legal name:")
    for k, v in tiers.most_common():
        print(f"  {k}: {v}")
    print()
    for tier in ("A", "B", "C"):
        sel = [h for h in hits if h[0] == tier]
        if not sel:
            continue
        print(f"--- tier {tier} ({len(sel)}) ---")
        for _, r, cand in sel[:20]:
            print(f"  {r['file'].split('/')[1]}:{r['line']} {r['defect']} ein={r['ein']} "
                  f"${int(r['amount']):,}")
            print(f"     WAS     : {r['original_organization'][:70]!r}")
            print(f"     APPLIED : {r['recovered_organization'][:70]!r}")
            if cand:
                print(f"     same-yr : {[c[:50] for c in cand]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
