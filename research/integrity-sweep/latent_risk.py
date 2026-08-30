#!/usr/bin/env python3
"""How many correct organization names are currently protected from the repair script only by its
last-resort guard.

recover_org_names.is_prose() fires on 369 rows the validator does not flag. Sampling shows they
are real legal names containing the word 'Fund for' / 'Funds support'. Nothing was overwritten
because of one guard: if the single disclosure candidate canon-equals what is already there,
skip. That guard cannot fire when the disclosure is unreadable, or when the candidate set is
thinned to one wrong name -- which is exactly how fy16:141 was corrupted.
"""
import collections
import csv
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import build_lookups             # noqa: E402
import recover_org_names as ROG  # noqa: E402
import validate_data as VD       # noqa: E402

canon = ROG.canon


def fy_of(p):
    m = re.search(r"[/\\]fy(\d{2})[/\\]", p)
    return 2000 + int(m.group(1)) if m else None


def main():
    per_year, pooled = build_lookups.load()
    published = set()
    for names in pooled["strict"].values():
        published |= {canon(n) for n in names}

    real, unknown = collections.Counter(), collections.Counter()
    money = 0
    names = collections.Counter()
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                org = (r.get("organization") or "").strip()
                if not org or VD.EIN_IN_TEXT.search(org) or "$" in org:
                    continue
                if not ROG.PROSE.search(org) or VD.ORG_PROSE.search(org):
                    continue
                try:
                    a = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    a = 0
                if canon(org) in published:
                    real[fy_of(f)] += 1
                    money += a
                    names[org] += 1
                else:
                    unknown[fy_of(f)] += 1
    print("rows the repair script's prose pattern fires on but the validator does not:")
    print(f"  the string IS a published legal name (false positive): {sum(real.values())}"
          f"   ${money:,}")
    print(f"  not a published legal name (probably real prose)     : {sum(unknown.values())}")
    print("\n  most common false-positive names:")
    for n, c in names.most_common(8):
        print(f"    x{c:<5} {n[:70]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
