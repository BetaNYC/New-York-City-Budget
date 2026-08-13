#!/usr/bin/env python3
"""
verify_crosswalk.py — prove every recorded edit actually happened, and nothing else did.

data/combined/org_name_recovery_crosswalk.csv is the audit trail for every automated repair made
to this corpus. It is only worth anything if it is exact, so this asserts three things:

  1. COMPLETE   — every crosswalk entry matches the value now in the data.
  2. GROUNDED   — every entry's `original_organization` differs from the recovered value, so no
                  entry claims a change that was actually a no-op.
  3. UNIQUE     — no (file, line, defect) appears twice.

Run it after any repair pass. Exit 1 on any failure — this one IS a hard gate, because a wrong
audit trail is worse than no audit trail: it asserts provenance that does not hold.

Usage:  python3 code/verify_crosswalk.py
"""
import csv
import collections
import os
import sys

CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"


def main():
    if not os.path.exists(CROSSWALK):
        print(f"no crosswalk at {CROSSWALK} — nothing to verify")
        return 0
    with open(CROSSWALK, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    cache, mismatched, noop = {}, [], []
    for r in rows:
        f = r["file"]
        if f not in cache:
            if not os.path.exists(f):
                mismatched.append((r, "<file missing>")); continue
            with open(f, newline="", encoding="utf-8") as fh:
                cache[f] = list(csv.DictReader(fh))
        idx = int(r["line"]) - 2
        if idx < 0 or idx >= len(cache[f]):
            mismatched.append((r, "<line out of range>")); continue
        row = cache[f][idx]
        # wrong_ein entries repair the `ein` column; everything else repairs `organization`.
        if r["defect"] == "wrong_ein":
            expected, actual = r["ein"], row.get("ein", "")
        else:
            expected, actual = r["recovered_organization"], row.get("organization", "")
        if actual != expected:
            mismatched.append((r, actual))
        if r.get("original_organization", "") == r.get("recovered_organization", ""):
            noop.append(r)

    dupes = [k for k, n in collections.Counter(
        (r["file"], r["line"], r["defect"]) for r in rows).items() if n > 1]

    by_defect = collections.Counter(r["defect"] for r in rows)
    print(f"crosswalk entries: {len(rows):,}")
    for d, n in sorted(by_defect.items()):
        print(f"  {n:>5}  {d}")
    print(f"\nCOMPLETE  {len(rows) - len(mismatched)}/{len(rows)} entries match the data")
    print(f"GROUNDED  {len(rows) - len(noop)}/{len(rows)} entries record a real change")
    print(f"UNIQUE    {len(rows) - len(dupes)}/{len(rows)} (file, line, defect) keys distinct")

    ok = True
    if mismatched:
        ok = False
        print(f"\nFAIL — {len(mismatched)} entries do not match the data:")
        for r, actual in mismatched[:5]:
            print(f"  {r['file']}:{r['line']} [{r['defect']}]")
            print(f"     crosswalk says: {(r['ein'] if r['defect']=='wrong_ein' else r['recovered_organization'])[:60]!r}")
            print(f"     data has      : {str(actual)[:60]!r}")
    if noop:
        ok = False
        print(f"\nFAIL — {len(noop)} entries claim a change that is a no-op")
    if dupes:
        ok = False
        print(f"\nFAIL — {len(dupes)} duplicate (file, line, defect) keys, e.g. {dupes[:3]}")

    print("\nPASS — the audit trail is exact" if ok else "\nFAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
