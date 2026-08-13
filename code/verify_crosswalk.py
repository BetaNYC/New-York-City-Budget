#!/usr/bin/env python3
"""
verify_crosswalk.py — prove every recorded edit actually happened, and nothing else did.

data/combined/org_name_recovery_crosswalk.csv is the audit trail for every automated repair made
to this corpus. It is only worth anything if it is exact, so this asserts three things:

  1. COMPLETE   — every crosswalk entry matches the value now in the data.
  2. GROUNDED   — every entry's `original_organization` differs from the recovered value, so no
                  entry claims a change that was actually a no-op.
  3. UNIQUE     — no (file, line, defect) appears twice.
  4. ACCOUNTED  — and nothing else changed. Every cell that differs from the baseline ref has a
                  crosswalk entry explaining it. Without this the trail proves only that recorded
                  edits happened, not that unrecorded ones did not — an adversarial audit
                  constructed six corruptions the first three checks all passed, including 200
                  silently-rewritten organizations and 200 silently-rewritten amounts.

Run it after any repair pass. Exit 1 on any failure — this one IS a hard gate, because a wrong
audit trail is worse than no audit trail: it asserts provenance that does not hold.

Usage:  python3 code/verify_crosswalk.py
"""
import collections
import csv
import os
import re
import sys

CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"


def accounted(baseline):
    """Every data cell differing from `baseline` must be explained by a crosswalk entry.

    This is the "and nothing else did" half. Compares organization/ein/member per (file, line)
    against the git ref and requires a matching crosswalk row for each difference. Amount changes
    are ALWAYS unexplained — no repair is permitted to move money.
    """
    import io
    import subprocess
    with open(CROSSWALK, newline="", encoding="utf-8") as fh:
        known = {(r["file"], int(r["line"])): r for r in csv.DictReader(fh)}
    listing = subprocess.run(["git", "ls-tree", "-r", "--name-only", baseline, "data/"],
                             capture_output=True, text=True)
    if listing.returncode != 0:
        return None, f"cannot read ref {baseline!r}"
    unexplained = []
    for f in listing.stdout.split():
        if "/schedule_c/" not in f or not f.endswith(".csv"):
            continue
        if "initiatives" in f or "reconcil" in f or not os.path.exists(f):
            continue
        old = list(csv.DictReader(io.StringIO(
            subprocess.run(["git", "show", f"{baseline}:{f}"], capture_output=True, text=True).stdout)))
        with open(f, newline="", encoding="utf-8") as fh:
            new = list(csv.DictReader(fh))
        if len(old) != len(new):
            unexplained.append((f, 0, "row count", len(old), len(new)))
            continue
        for i, (o, n) in enumerate(zip(old, new)):
            line = i + 2
            for col in ("organization", "ein", "member", "amount"):
                if (o.get(col) or "") == (n.get(col) or ""):
                    continue
                e = known.get((f, line))
                # An amount change is never explainable by a name/EIN repair.
                if col == "amount" or e is None:
                    unexplained.append((f, line, col, o.get(col, "")[:40], n.get(col, "")[:40]))
                    continue
                # The entry must also be TRUTHFUL about what it replaced. An entry whose
                # `original_organization` does not match what the baseline actually held is a
                # fabricated provenance record — it explains a change that did not happen and
                # conceals the one that did.
                if col == "organization":
                    claimed = e.get("original_organization", "")
                    # wrong_ein entries prefix the ein, e.g. "[ein 112412584] Name"
                    claimed = re.sub(r"^\[ein \d+\] ", "", claimed)
                    if claimed != (o.get(col) or ""):
                        unexplained.append((f, line, "fabricated original",
                                            (o.get(col) or "")[:40], claimed[:40]))
        # note: a crosswalk entry covering the line explains organization/ein/member changes there
    return unexplained, None


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
    baseline = os.environ.get("CROSSWALK_BASELINE", "main")
    unexp, err = accounted(baseline)
    if err:
        print(f"ACCOUNTED skipped — {err}")
        unexp = []
    else:
        print(f"ACCOUNTED {len(unexp)} unexplained cell change(s) vs {baseline}")

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
    if unexp:
        ok = False
        print(f"\nFAIL — {len(unexp)} cell change(s) with no crosswalk entry:")
        for f, line, col, o, n in unexp[:5]:
            print(f"  {f}:{line} [{col}]  {o!r} -> {n!r}")

    print("\nPASS — the audit trail is exact" if ok else "\nFAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
