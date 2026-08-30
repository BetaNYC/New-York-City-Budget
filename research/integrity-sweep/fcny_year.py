#!/usr/bin/env python3
"""Which fiscal year's workbook supplies each candidate name for (13-2612524, $258,800), and
what the crosswalk recorded -- to establish whether the applied name entered under the
superseded exact-header reader.
"""
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_lookups  # noqa: E402

KEY = ("132612524", 258800)


def main():
    per_year, pooled = build_lookups.load()
    for kind in ("strict", "rog"):
        print(f"-- {kind} reader --")
        for y in sorted(per_year[kind]):
            names = per_year[kind][y].get(KEY)
            if names:
                print(f"   FY{y}: {sorted(names)}")
        print(f"   pooled: {sorted(pooled[kind].get(KEY, set()))}")

    print("\n-- crosswalk row, and the commit it first appeared in --")
    for r in csv.DictReader(open("data/combined/org_name_recovery_crosswalk.csv",
                                 newline="", encoding="utf-8")):
        if r["file"].endswith("fy16_schedule_c_awards.csv") and r["line"] == "141":
            for k, v in r.items():
                print(f"   {k:<26} {v[:110]}")
    for c in ("2c8168f", "0627897", "9c1a99d"):
        out = subprocess.run(["git", "show",
                              f"{c}:data/combined/org_name_recovery_crosswalk.csv"],
                             capture_output=True, text=True).stdout
        hit = [ln for ln in out.splitlines()
               if "fy16/schedule_c/fy16_schedule_c_awards.csv,141," in ln]
        print(f"   present at {c}: {bool(hit)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
