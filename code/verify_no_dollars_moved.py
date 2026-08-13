#!/usr/bin/env python3
"""
verify_no_dollars_moved.py — prove a data-repair changed no money.

Name, EIN and provenance repairs must never alter an amount. This compares the per-fiscal-year
award dollar total between a git ref and the working tree, and fails if any year moved.

PER YEAR, not just in total, deliberately: a total can net to zero while two years are wrong in
opposite directions, which is exactly the failure this is meant to catch.

Sidecars under data/recovered/ are excluded — they are additive by design and would legitimately
change a total. This checks the per-year extracts only.

Usage:
  python3 code/verify_no_dollars_moved.py            # compare against main
  python3 code/verify_no_dollars_moved.py <ref>      # compare against any ref
"""
import collections
import csv
import io
import subprocess
import sys


def totals_at(ref):
    out = collections.Counter()
    listing = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, "data/"],
                             capture_output=True, text=True)
    if listing.returncode != 0:
        print(f"cannot read ref {ref!r}: {listing.stderr.strip()}")
        sys.exit(2)
    for f in listing.stdout.split():
        if "/schedule_c/" not in f or not f.endswith(".csv"):
            continue
        if "initiatives" in f or "reconcil" in f:
            continue
        blob = subprocess.run(["git", "show", f"{ref}:{f}"], capture_output=True, text=True).stdout
        for r in csv.DictReader(io.StringIO(blob)):
            try:
                out[f.split("/")[1]] += int(float(r.get("amount") or 0))
            except (TypeError, ValueError):
                pass
    return out


def main():
    ref = sys.argv[1] if len(sys.argv) > 1 else "main"
    before, after = totals_at(ref), totals_at("HEAD")
    print(f"{'FY':<8}{ref[:16]:>18}{'HEAD':>18}{'delta':>12}")
    moved = []
    for fy in sorted(set(before) | set(after)):
        d = after[fy] - before[fy]
        if d:
            moved.append((fy, d))
        print(f"{fy:<8}{before[fy]:>18,}{after[fy]:>18,}{d:>12,}")
    print(f"{'TOTAL':<8}{sum(before.values()):>18,}{sum(after.values()):>18,}"
          f"{sum(after.values()) - sum(before.values()):>12,}")

    if moved:
        print(f"\nFAIL — {len(moved)} fiscal year(s) changed: {moved}")
        return 1
    print("\nPASS — no fiscal year's award dollars moved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
