#!/usr/bin/env python3
"""Run the decapitation test (decap.py Test A) against an arbitrary git ref, so a defect can be
attributed to this branch or exonerated as pre-existing.

Usage: python3 decap_at_ref.py <ref> [<ref> ...]
"""
import collections
import csv
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import build_lookups             # noqa: E402
import recover_org_names as ROG  # noqa: E402

canon = ROG.canon


def files_at(ref):
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, "data/"],
                       capture_output=True, text=True, check=True)
    return [f for f in r.stdout.split()
            if "/schedule_c/" in f and f.endswith(".csv")
            and "initiativ" not in f and "reconcil" not in f]


def main():
    per_year, pooled = build_lookups.load()
    all_names = set()
    for names in pooled["strict"].values():
        all_names |= {canon(n) for n in names}

    for ref in sys.argv[1:] or ["902568f", "HEAD"]:
        suspect = collections.Counter()
        money = collections.Counter()
        for f in files_at(ref):
            blob = subprocess.run(["git", "show", f"{ref}:{f}"],
                                  capture_output=True, text=True).stdout
            for r in csv.DictReader(io.StringIO(blob)):
                m = (r.get("member") or "").strip().rstrip(",")
                o = (r.get("organization") or "").strip()
                if not m or not o:
                    continue
                if canon(f"{m} {o}") in all_names and canon(o) not in all_names:
                    try:
                        amt = int(float(r.get("amount") or 0))
                    except (TypeError, ValueError):
                        amt = 0
                    suspect[(m, o)] += 1
                    money[(m, o)] += amt
        print(f"{ref:>10}  pairs={len(suspect):4d}  rows={sum(suspect.values()):5d}  "
              f"dollars=${sum(money.values()):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
