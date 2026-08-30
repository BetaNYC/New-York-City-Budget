#!/usr/bin/env python3
"""Re-run the absorbing-row anchor check against the pre-repair data, to separate a real
provenance error from an artefact of the repairs themselves.

The name repairs rewrote `organization` in place, deleting the very absorbed text that the
sidecar's `absorbed_from_line` column points at. So the anchor must be tested at the merge base.
"""
import csv
import io
import re
import subprocess
import sys

CAND = "code/absorbed_award_candidates.csv"
EIN_IN_TEXT = re.compile(r"\d{2}-\d{7}")
REF = sys.argv[1] if len(sys.argv) > 1 else "902568f"


def blob(ref, path):
    r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def main():
    cands = list(csv.DictReader(open(CAND, newline="", encoding="utf-8")))
    cache = {}
    ok = bad = missing = 0
    examples = []
    for c in cands:
        f = c["absorbing_file"]
        if f not in cache:
            b = blob(REF, f)
            cache[f] = list(csv.DictReader(io.StringIO(b))) if b else None
        data = cache[f]
        if data is None:
            missing += 1
            continue
        i = int(c["absorbing_line"]) - 2
        if not (0 <= i < len(data)):
            missing += 1
            continue
        org = data[i].get("organization") or ""
        if EIN_IN_TEXT.search(org) or "$" in org or "*" in org:
            ok += 1
        else:
            bad += 1
            if len(examples) < 12:
                examples.append((f.split("/")[1], c["absorbing_line"], org[:60],
                                 c["first_candidate_name"][:40]))
    print(f"anchor rows at {REF}: absorbed text visible {ok}, not visible {bad}, unresolved {missing}")
    for e in examples:
        print(f"  {e[0]}:{e[1]} org={e[2]!r} -> child {e[3]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
