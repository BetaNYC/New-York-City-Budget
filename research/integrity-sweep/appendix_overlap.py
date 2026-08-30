#!/usr/bin/env python3
"""Do the per-year appendix files duplicate awards already in the main-body award files?

This bears on whether the published 62,213 / $3,741,615,569 headline double counts. It is a
PRE-EXISTING question -- the appendix files were loaded before this branch -- but the branch
republishes the headline, so it is in scope.
"""
import collections
import csv
import glob
import re
import sys


def norm(v):
    return re.sub(r"\D", "", v or "")


def fy_of(p):
    m = re.search(r"[/\\]fy(\d{2})[/\\]", p)
    return 2000 + int(m.group(1)) if m else None


def load(kind):
    rows = []
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        if (kind == "appendix") != ("appendix" in f):
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                try:
                    a = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    continue
                rows.append((fy_of(f), norm(r.get("ein")), a,
                             (r.get("organization") or "").strip(),
                             (r.get("member") or "").strip()))
    return rows


def main():
    app, awd = load("appendix"), load("awards")
    print(f"appendix rows {len(app):,}  ${sum(x[2] for x in app):,}")
    print(f"awards   rows {len(awd):,}  ${sum(x[2] for x in awd):,}")
    print(f"TOTAL         {len(app) + len(awd):,}  ${sum(x[2] for x in app + awd):,}")

    ai = collections.Counter((x[0], x[1], x[2]) for x in awd)
    hits = [x for x in app if ai.get((x[0], x[1], x[2]))]
    print(f"\nappendix rows whose (fy, ein, amount) also appears in an awards file: "
          f"{len(hits):,}  ${sum(x[2] for x in hits):,}")

    ai4 = collections.Counter((x[0], x[1], x[2], x[3], x[4]) for x in awd)
    hits4 = [x for x in app if ai4.get((x[0], x[1], x[2], x[3], x[4]))]
    print(f"...and also matching organization AND member: {len(hits4):,}  "
          f"${sum(x[2] for x in hits4):,}")
    by_fy = collections.Counter(x[0] for x in hits4)
    print("  by fiscal year:", dict(sorted(by_fy.items())))
    for x in hits4[:8]:
        print(f"    FY{x[0]} ein={x[1]} ${x[2]:,} {x[3][:40]!r} member={x[4]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
