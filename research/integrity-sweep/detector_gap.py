#!/usr/bin/env python3
"""The repair pipeline and the validator use DIFFERENT definitions of the org_prose defect.

recover_org_names.PROSE was deliberately broadened mid-branch ("Broadened after a dry run found
rows the first pattern missed"). validate_data.ORG_PROSE was not. data/QA-REPORT.md -- the
artifact a reader consults -- counts with the narrow one.

This lists rows the repair script considers prose and the validator does not, so the gap can be
judged rather than asserted.
"""
import csv
import glob
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import recover_org_names as ROG  # noqa: E402
import validate_data as VD       # noqa: E402


def main():
    only_repair, only_val, both = [], [], 0
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                org = (r.get("organization") or "").strip()
                if not org or VD.EIN_IN_TEXT.search(org) or "$" in org:
                    continue
                a = bool(ROG.PROSE.search(org))
                b = bool(VD.ORG_PROSE.search(org))
                if a and b:
                    both += 1
                elif a:
                    only_repair.append((f, ln, org, int(float(r.get("amount") or 0))))
                elif b:
                    only_val.append((f, ln, org, int(float(r.get("amount") or 0))))

    print(f"both detectors agree           : {both}")
    print(f"repair-script pattern ONLY     : {len(only_repair)}   "
          f"${sum(x[3] for x in only_repair):,}")
    print(f"validator pattern ONLY         : {len(only_val)}")
    print("\n20 random rows the repair script calls prose and QA-REPORT.md does not:")
    for f, ln, org, amt in random.Random(20260813).sample(only_repair, min(20, len(only_repair))):
        print(f"  {f.split('/')[1]}:{ln} ${amt:>10,}  {org[:88]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
