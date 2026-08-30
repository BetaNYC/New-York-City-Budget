#!/usr/bin/env python3
"""Cell-level diff of every tracked data CSV between a base ref and HEAD.

Stronger than code/verify_no_dollars_moved.py, which sums per fiscal year: a year total is
unchanged if two rows move in opposite directions, and it never looks at row counts, row order,
or any column but `amount`.

This one reports, per file: rows added/removed, and for every surviving row (matched by
position, since the repair scripts rewrite in place by line number) which columns changed.
"""
import collections
import csv
import io
import subprocess
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "902568f"
HEAD = sys.argv[2] if len(sys.argv) > 2 else "HEAD"


def tracked(ref, prefix="data/"):
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, prefix],
                       capture_output=True, text=True, check=True)
    return [f for f in r.stdout.split() if f.endswith(".csv")]


def load(ref, path):
    blob = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True).stdout
    rd = csv.DictReader(io.StringIO(blob))
    return rd.fieldnames or [], list(rd)


def main():
    base_files, head_files = set(tracked(BASE)), set(tracked(HEAD))
    print(f"files only in {BASE}: {sorted(base_files - head_files)}")
    print(f"files only in {HEAD}: {sorted(head_files - base_files)}")
    print()

    col_changes = collections.Counter()
    per_file = {}
    amount_moves = []
    for path in sorted(base_files & head_files):
        bf, br = load(BASE, path)
        hf, hr = load(HEAD, path)
        note = []
        if bf != hf:
            note.append(f"HEADER {bf} -> {hf}")
        if len(br) != len(hr):
            note.append(f"ROWCOUNT {len(br)} -> {len(hr)}")
        changed = collections.Counter()
        n = min(len(br), len(hr))
        for i in range(n):
            for k in bf:
                if k not in hf:
                    continue
                a, b = br[i].get(k), hr[i].get(k)
                if a != b:
                    changed[k] += 1
                    if k == "amount":
                        amount_moves.append((path, i + 2, a, b))
        if changed or note:
            per_file[path] = (dict(changed), note)
        col_changes.update(changed)

    for path, (changed, note) in per_file.items():
        print(f"{path}")
        for x in note:
            print(f"    !! {x}")
        for k, v in sorted(changed.items(), key=lambda kv: -kv[1]):
            print(f"    {k:<26} {v:>6}")
    print()
    print("=== columns changed, all files ===")
    for k, v in col_changes.most_common():
        print(f"  {k:<26} {v:>7}")
    print()
    print(f"amount cells changed: {len(amount_moves)}")
    for x in amount_moves[:20]:
        print("   ", x)


if __name__ == "__main__":
    main()
