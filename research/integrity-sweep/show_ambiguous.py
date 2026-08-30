#!/usr/bin/env python3
"""List every applied name repair whose (EIN, amount) carries more than one distinct legal
name once the workbook is read with cells positioned by reference.

These are rows where the scripts' own stated safety rule -- "nothing is applied unless exactly
ONE candidate" -- did not actually hold. The applied name is one of the candidates, so it may
still be right; it is simply not established by the evidence the script claimed to rely on.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import build_lookups             # noqa: E402
import recover_org_names as ROG  # noqa: E402

canon = ROG.canon
CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"


def main():
    per_year, pooled = build_lookups.load()
    sp, rp = pooled["strict"], pooled["rog"]
    rows = list(csv.DictReader(open(CROSSWALK, newline="", encoding="utf-8")))
    n = 0
    for r in rows:
        if r["defect"] not in ("org_prose", "org_merged"):
            continue
        k = (r["ein"], int(r["amount"]))
        s, o = sp.get(k, set()), rp.get(k, set())
        if len({canon(c) for c in s}) > 1:
            n += 1
            print(f"[{n}] {r['file'].split('/')[1]}:{r['line']} ein={r['ein']} "
                  f"${int(r['amount']):,}  src={r['source']}")
            print(f"    applied : {r['recovered_organization'][:75]!r}")
            print(f"    orig-rdr: {sorted(o)[:3]}")
            print(f"    strict  : {sorted(s)[:5]}")
    print("TOTAL ambiguous under a reference-positioned read:", n)


if __name__ == "__main__":
    main()
