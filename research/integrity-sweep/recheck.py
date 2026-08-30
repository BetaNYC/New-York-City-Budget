#!/usr/bin/env python3
"""Re-decide every applied repair against an independently-read disclosure workbook.

For each crosswalk entry, rebuild the candidate set the repair script would have seen if its
xlsx reader had positioned cells by their `r` reference instead of by ordinal position, and
classify the applied substitution:

  CONFIRMED    strict evidence is a single name and it matches what was written
  CONTRADICTED strict evidence is a single name and it is a DIFFERENT name
  AMBIGUOUS    strict evidence holds >1 distinct name, so the unique-match gate should not have
               fired at all; the applied name may be right by luck but is not established
  NO_EVIDENCE  strict evidence holds no row for this (EIN, amount)
"""
import collections
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import build_lookups            # noqa: E402
import recover_org_names as ROG  # noqa: E402

CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"
canon = ROG.canon


def file_year(path):
    m = re.search(r"[/\\]fy(\d{2})[/\\]", path)
    return 2000 + int(m.group(1)) if m else None


def main():
    per_year, pooled = build_lookups.load()
    strict_year, strict_pool = per_year["strict"], pooled["strict"]
    rog_pool = pooled["rog"]

    rows = list(csv.DictReader(open(CROSSWALK, newline="", encoding="utf-8")))
    verdict = collections.Counter()
    detail = collections.defaultdict(list)

    for r in rows:
        defect = r["defect"]
        ein, amt = r["ein"], int(r["amount"])
        applied = r["recovered_organization"]
        key = (ein, amt)

        if defect == "member_bleed":
            y = file_year(r["file"])
            cand = strict_year.get(y, {}).get(key) or strict_pool.get(key) or set()
        elif defect == "wrong_ein":
            cand = strict_pool.get(key) or set()   # keyed on name+amount originally; see below
        else:
            cand = strict_pool.get(key) or set()

        cset = {canon(c) for c in cand}
        if not cand:
            v = "NO_EVIDENCE"
        elif len(cset) == 1:
            v = "CONFIRMED" if canon(applied) in cset else "CONTRADICTED"
        else:
            v = "AMBIGUOUS_ok" if canon(applied) in cset else "AMBIGUOUS_bad"

        verdict[(defect, v)] += 1
        detail[(defect, v)].append((r, sorted(cand)))

    print(f"{'defect':<14}{'verdict':<16}{'n':>7}")
    for (d, v), n in sorted(verdict.items()):
        print(f"{d:<14}{v:<16}{n:>7}")
    print()

    # What would the ORIGINAL reader have decided vs the strict one, on the same gate?
    flipped = 0
    for r in rows:
        key = (r["ein"], int(r["amount"]))
        o, s = rog_pool.get(key, set()), strict_pool.get(key, set())
        if len(o) == 1 and len(s) > 1:
            flipped += 1
    print(f"crosswalk rows where the ORIGINAL reader saw a unique candidate but the")
    print(f"strict reader sees more than one (gate fired on ambiguous evidence): {flipped}")
    print()

    for k in sorted(detail):
        if k[1] in ("CONTRADICTED", "AMBIGUOUS_bad"):
            print(f"--- {k} ({len(detail[k])}) ---")
            for r, cand in detail[k][:25]:
                print(f"  {r['file'].split('/')[1]}:{r['line']} ein={r['ein']} ${int(r['amount']):,}")
                print(f"     was     : {r['original_organization'][:80]!r}")
                print(f"     applied : {r['recovered_organization'][:80]!r}")
                print(f"     strict  : {[c[:60] for c in cand[:4]]}")
    return detail


if __name__ == "__main__":
    main()
