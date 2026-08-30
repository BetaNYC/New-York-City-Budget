#!/usr/bin/env python3
"""Trace the crosswalk across the branch's commits.

The crosswalk ACCUMULATES by design -- each script appends and never re-validates prior rows.
Commit 0627897 changed how the disclosure workbooks are read ("match disclosure headers by
substring -- FY2016 was silently unreadable"), which changed the evidence base under every
decision made before it. This shows which rows were written under the superseded evidence and
never revisited.
"""
import csv
import io
import subprocess
import sys

COMMITS = ["902568f", "7d971e4", "2c8168f", "eb0133e", "eb7c48c", "18d84cb",
           "0627897", "f3f9fa2", "4c0df1f", "553d5d2", "afa391c", "393aa8b",
           "f320901", "9c1a99d"]
PATH = "data/combined/org_name_recovery_crosswalk.csv"


def at(ref):
    r = subprocess.run(["git", "show", f"{ref}:{PATH}"], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return list(csv.DictReader(io.StringIO(r.stdout)))


def key(r):
    return (r["file"], r["line"])


def main():
    prev = None
    prev_ref = None
    snapshots = {}
    for c in COMMITS:
        rows = at(c)
        subj = subprocess.run(["git", "log", "-1", "--format=%s", c],
                              capture_output=True, text=True).stdout.strip()
        if rows is None:
            print(f"{c}  (no crosswalk)            {subj[:60]}")
            prev = None
            continue
        snapshots[c] = rows
        added = removed = changed = 0
        if prev is not None:
            pk = {key(r): r for r in prev}
            nk = {key(r): r for r in rows}
            added = len(set(nk) - set(pk))
            removed = len(set(pk) - set(nk))
            changed = sum(1 for k in set(pk) & set(nk)
                          if pk[k]["recovered_organization"] != nk[k]["recovered_organization"])
        print(f"{c}  rows={len(rows):5d}  +{added:<5d} -{removed:<5d} ~{changed:<4d}  {subj[:60]}")
        prev, prev_ref = rows, c

    # Which of today's rows were first written BEFORE the reader fix at 0627897?
    fix = "0627897"
    pre = snapshots.get("18d84cb")     # last snapshot before the reader fix
    now = snapshots[COMMITS[-1]]
    if pre:
        prek = {key(r) for r in pre}
        survivors = [r for r in now if key(r) in prek]
        print()
        print(f"rows in the FINAL crosswalk that were first written before the reader fix "
              f"({fix}) and never re-derived: {len(survivors):,} of {len(now):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
