#!/usr/bin/env python3
"""The 272 surname-leading rows fix_member_bleed.py deliberately left alone.

Its gate needs the disclosure to hold exactly ONE name for the row's (EIN, amount) and for that
name to equal the peeled remainder. This asks a weaker but still evidence-based question: is the
peeled remainder a legal name the Council published ANYWHERE, while the full string as printed
is not? That is the signature of a real bleed the strict gate could not clear.
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
import fix_member_bleed as FMB   # noqa: E402
import recover_org_names as ROG  # noqa: E402

canon = ROG.canon


def main():
    per_year, pooled = build_lookups.load()
    published = set()
    for names in pooled["strict"].values():
        published |= {canon(n) for n in names}

    surnames = FMB.build_surnames(FMB.surname_sources())
    tally = collections.Counter()
    money = collections.Counter()
    ex = []
    for f in FMB.award_files():
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                org = (r.get("organization") or "").strip()
                if not org:
                    continue
                sur, rest = FMB.peel(org, surnames)
                if not sur:
                    continue
                try:
                    a = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    a = 0
                whole_ok = canon(org) in published
                rest_ok = canon(rest) in published
                if whole_ok:
                    k = "left alone, correct as printed"
                elif rest_ok:
                    k = "LIKELY A REAL BLEED, not peeled"
                    if len(ex) < 20:
                        ex.append((f.split("/")[1], ln, sur, org, rest, a))
                else:
                    k = "neither form is a published name"
                tally[k] += 1
                money[k] += a
    for k, v in tally.most_common():
        print(f"  {k:<38} {v:>6} rows  ${money[k]:>13,}")
    print("\nexamples of the unrepaired bleeds:")
    for fy, ln, sur, org, rest, a in ex:
        print(f"  {fy}:{ln} ${a:>9,}  -{sur!r} {org[:52]!r}")
        print(f"{'':>24}-> {rest[:60]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
