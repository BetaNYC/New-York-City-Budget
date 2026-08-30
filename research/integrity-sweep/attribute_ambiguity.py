#!/usr/bin/env python3
"""Split the 57 pooled-ambiguous repairs by which reader defect explains them.

Two distinct reader defects exist on this branch:
  (1) exact-header matching -- FY2014 and FY2016 entirely unreadable. FIXED at 0627897, but the
      crosswalk accumulates and nothing re-derived the rows applied before it.
  (2) positional cell mapping -- xlsx omits empty cells, so any row with an interior gap shifts.
      STILL PRESENT in all four repair scripts at HEAD.
"""
import collections
import csv
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import build_lookups             # noqa: E402
import recover_org_names as ROG  # noqa: E402

canon = ROG.canon
CW = "data/combined/org_name_recovery_crosswalk.csv"


def main():
    per_year, pooled = build_lookups.load()
    sp, rp = pooled["strict"], pooled["rog"]

    pre = subprocess.run(["git", "show", f"18d84cb:{CW}"],
                         capture_output=True, text=True).stdout
    pre_keys = {(r["file"], r["line"]) for r in csv.DictReader(pre.splitlines())}

    tally = collections.Counter()
    for r in csv.DictReader(open(CW, newline="", encoding="utf-8")):
        if r["defect"] not in ("org_prose", "org_merged"):
            continue
        k = (r["ein"], int(r["amount"]))
        s = len({canon(x) for x in sp.get(k, set())})
        o = len({canon(x) for x in rp.get(k, set())})
        if s <= 1:
            continue
        applied_pre_fix = (r["file"], r["line"]) in pre_keys
        if o == 1:
            tally[("positional-shift (defect 2, STILL LIVE)", applied_pre_fix)] += 1
        else:
            tally[("already ambiguous to the current reader too", applied_pre_fix)] += 1

    print("pooled-ambiguous applied repairs, by cause and by whether they predate the header fix:")
    for (cause, pre_fix), n in sorted(tally.items()):
        print(f"  {cause:<46} applied_before_0627897={pre_fix}  n={n}")
    print(f"  TOTAL {sum(tally.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
