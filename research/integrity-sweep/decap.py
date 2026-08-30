#!/usr/bin/env python3
"""Hunt for decapitated organization names: rows where a leading token that is BOTH a council
surname/borough AND part of the grantee's real legal name has been stripped.

Two independent tests:

  A. Corpus-internal. For every (member, organization) pair in the live data, ask whether
     `member + ' ' + organization` appears anywhere in the corpus, or in the Council's
     disclosure, as a whole legal name. If it does, the split is suspect.

  B. Disclosure-anchored. For every row the peel actually changed (the crosswalk's
     member_bleed entries), check the recovered name against the disclosure's own set of legal
     names for that EIN across all years -- not just the (EIN, amount) key the repair used.
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

canon = ROG.canon
CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"


def award_files():
    return sorted(f for f in glob.glob("data/fy*/schedule_c/*.csv")
                  if "initiativ" not in f and "reconcil" not in f)


def main():
    per_year, pooled = build_lookups.load()
    strict = pooled["strict"]

    # every legal name the Council itself published, and every name by EIN
    all_names = set()
    ein_names = collections.defaultdict(set)
    for (e, a), names in strict.items():
        all_names |= {canon(n) for n in names}
        ein_names[e] |= set(names)

    # --- Test A: joins that reconstruct a published legal name ------------------------------
    suspect = collections.Counter()
    suspect_money = collections.Counter()
    rows_seen = 0
    for f in award_files():
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                m = (r.get("member") or "").strip().rstrip(",")
                o = (r.get("organization") or "").strip()
                if not m or not o:
                    continue
                rows_seen += 1
                joined = canon(f"{m} {o}")
                if joined and joined in all_names and canon(o) not in all_names:
                    try:
                        amt = int(float(r.get("amount") or 0))
                    except (TypeError, ValueError):
                        amt = 0
                    suspect[(m, o)] += 1
                    suspect_money[(m, o)] += amt

    print("=== TEST A: member+organization reconstructs a PUBLISHED legal name, while")
    print("            organization alone matches no published name ===")
    print(f"rows scanned with both member and organization: {rows_seen:,}")
    print(f"distinct (member, organization) pairs implicated: {len(suspect):,}")
    print(f"row instances: {sum(suspect.values()):,}   dollars: ${sum(suspect_money.values()):,}")
    print()
    for (m, o), n in suspect.most_common(30):
        print(f"  n={n:<5} ${suspect_money[(m, o)]:>13,}  member={m!r:<20} org={o!r}")

    # --- Test B: did the PEEL create any of them? -------------------------------------------
    print()
    print("=== TEST B: of those, how many were created by this branch's peel? ===")
    peeled = {}
    for r in csv.DictReader(open(CROSSWALK, newline="", encoding="utf-8")):
        if r["defect"] == "member_bleed":
            peeled[(r["file"], int(r["line"]))] = r
    hit = 0
    for f in award_files():
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                if (f, ln) not in peeled:
                    continue
                m = (r.get("member") or "").strip().rstrip(",")
                o = (r.get("organization") or "").strip()
                if not m or not o:
                    continue
                if canon(f"{m} {o}") in all_names and canon(o) not in all_names:
                    hit += 1
                    if hit <= 20:
                        print(f"  {f.split('/')[1]}:{ln} member={m!r} org={o!r}")
                        print(f"      was {peeled[(f, ln)]['original_organization']!r}")
    print(f"peel-created decapitations: {hit}")

    # --- Test C: is every peeled name known to the disclosure for that EIN? ------------------
    print()
    print("=== TEST C: peeled name vs every legal name the disclosure gives that EIN ===")
    bad = 0
    for (f, ln), r in sorted(peeled.items()):
        names = ein_names.get(r["ein"], set())
        if names and canon(r["recovered_organization"]) not in {canon(n) for n in names}:
            bad += 1
            if bad <= 15:
                print(f"  {f.split('/')[1]}:{ln} ein={r['ein']} applied="
                      f"{r['recovered_organization'][:50]!r}")
                print(f"      disclosure for this EIN: {sorted(names)[:3]}")
    print(f"peeled names not found under their own EIN anywhere in the disclosure: {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
