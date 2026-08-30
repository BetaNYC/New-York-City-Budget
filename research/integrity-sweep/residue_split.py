#!/usr/bin/env python3
"""Split the remaining flagged rows by file family, to reconcile against the branch's own
claimed residue ("140 org_prose, 64 org_merged, 4 empty organization")."""
import collections
import csv
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import recover_org_names as ROG  # noqa: E402

EIN_IN_TEXT = re.compile(r"\d{2}-\d{7}")


def main():
    res = collections.Counter()
    money = collections.Counter()
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        fam = "appendix" if "appendix" in f else "awards"
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                org = (r.get("organization") or "").strip()
                try:
                    a = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    a = 0
                if not org:
                    k = "empty"
                elif EIN_IN_TEXT.search(org) or "$" in org:
                    k = "org_merged"
                elif ROG.is_prose(org):
                    k = "org_prose"
                else:
                    continue
                res[(fam, k)] += 1
                money[(fam, k)] += a
    for k in sorted(res):
        print(f"  {k[0]:<10}{k[1]:<12}{res[k]:>6} rows  ${money[k]:>12,}")
    print(f"  {'TOTAL':<22}{sum(res.values()):>6} rows  ${sum(money.values()):>12,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
