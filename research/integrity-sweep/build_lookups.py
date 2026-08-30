#!/usr/bin/env python3
"""Build and cache both readers' (EIN, amount) -> {legal name} lookups, per year and pooled."""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))

import xlsxlib                    # noqa: E402
import reader_diff               # noqa: E402
import recover_org_names as ROG  # noqa: E402
import fix_member_bleed as FMB   # noqa: E402

OUT = os.path.join(HERE, "lookups.json")
SRC = "source/expense-funding-disclosure"


def build():
    per_year = {"strict": {}, "rog": {}, "fmb": {}}
    for p in sorted(glob.glob(os.path.join(SRC, "funded_disclosure_FY*.xlsx"))):
        y = re.search(r"FY(\d{4})", p).group(1)
        per_year["strict"][y] = reader_diff.strict_lookup(p)
        per_year["rog"][y] = ROG.read_workbook(p)
        per_year["fmb"][y] = FMB.read_workbook(p)
        print("built", y, {k: len(per_year[k][y]) for k in per_year}, file=sys.stderr)

    ser = {}
    for kind, years in per_year.items():
        ser[kind] = {y: {f"{e}|{a}": sorted(n) for (e, a), n in tbl.items()}
                     for y, tbl in years.items()}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ser, f)
    print("wrote", OUT, file=sys.stderr)


def load():
    if not os.path.exists(OUT):
        build()                       # ~30s; the cache is a build artifact, not a deliverable
    with open(OUT, encoding="utf-8") as f:
        ser = json.load(f)
    per_year = {}
    pooled = {}
    for kind, years in ser.items():
        per_year[kind] = {}
        pooled[kind] = {}
        for y, tbl in years.items():
            d = {}
            for k, names in tbl.items():
                e, a = k.rsplit("|", 1)
                d[(e, int(a))] = set(names)
            per_year[kind][int(y)] = d
            for kk, nn in d.items():
                pooled[kind].setdefault(kk, set()).update(nn)
    return per_year, pooled


if __name__ == "__main__":
    build()
