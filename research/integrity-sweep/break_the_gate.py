#!/usr/bin/env python3
"""Construct corruptions that code/verify_crosswalk.py accepts.

Runs entirely inside a throwaway copy of the tree; data/ in the real worktree is never touched.
Each scenario mutates the copy, re-runs the gate there, and reports the gate's exit code.
A corruption that exits 0 is one the gate cannot see.
"""
import csv
import os
import shutil
import subprocess
import sys
import tempfile

GATE = "code/verify_crosswalk.py"
CW = "data/combined/org_name_recovery_crosswalk.csv"
ROOT = os.getcwd()


def stage():
    d = tempfile.mkdtemp(prefix="gate-")
    os.makedirs(os.path.join(d, "code"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, GATE), os.path.join(d, GATE))
    shutil.copytree(os.path.join(ROOT, "data"), os.path.join(d, "data"),
                    ignore=shutil.ignore_patterns("*.DS_Store"))
    return d


def run(d):
    r = subprocess.run([sys.executable, GATE], cwd=d, capture_output=True, text=True)
    tail = [ln for ln in r.stdout.splitlines() if ln.startswith(("PASS", "FAILED", "FAIL"))]
    return r.returncode, (tail[-1] if tail else r.stdout.strip().splitlines()[-1])


def rewrite(path, mutate):
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        fields, rows = rd.fieldnames, list(rd)
    mutate(rows, fields)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def scenario(name, mutate_cw=None, mutate_data=None, datafile=None):
    d = stage()
    try:
        if mutate_cw:
            rewrite(os.path.join(d, CW), mutate_cw)
        if mutate_data:
            rewrite(os.path.join(d, datafile), mutate_data)
        code, msg = run(d)
        verdict = "GATE BLIND" if code == 0 else "gate catches it"
        print(f"  [{verdict:>15}] {name}")
        print(f"                    exit={code}  {msg}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    print("baseline:")
    d = stage()
    print("   ", run(d))
    shutil.rmtree(d, ignore_errors=True)

    print("\nscenarios:")

    # 1. Falsify the audit trail's record of what was there before.
    def fake_original(rows, fields):
        n = 0
        for r in rows:
            if r["defect"] == "org_prose" and n < 500:
                r["original_organization"] = "TOTALLY FABRICATED PRIOR VALUE"
                n += 1
    scenario("500 entries claim a prior value that never existed", mutate_cw=fake_original)

    # 2. Falsify the key the repair says it joined on.
    def fake_key(rows, fields):
        n = 0
        for r in rows:
            if r["defect"] in ("org_prose", "org_merged") and n < 500:
                r["ein"] = "000000000"
                r["amount"] = "1"
                n += 1
    scenario("500 entries carry a fabricated (EIN, amount) join key", mutate_cw=fake_key)

    # 3. Falsify the provenance label.
    def fake_source(rows, fields):
        for r in rows:
            r["source"] = "hand_typed_by_someone"
            r["match_key"] = "vibes"
    scenario("every entry relabelled to an invented source", mutate_cw=fake_source)

    # 4. An edit to the data with NO crosswalk entry at all.
    target = "data/fy23/schedule_c/fy23_schedule_c_awards.csv"

    def silent_edit(rows, fields):
        for r in rows[:200]:
            if (r.get("organization") or "").strip():
                r["organization"] = "SILENTLY REPLACED"
    scenario("200 organization cells rewritten with no crosswalk entry",
             mutate_data=silent_edit, datafile=target)

    # 5. A silent EIN change with no crosswalk entry.
    def silent_ein(rows, fields):
        for r in rows[:200]:
            if (r.get("ein") or "").strip():
                r["ein"] = "999999999"
    scenario("200 EINs rewritten with no crosswalk entry",
             mutate_data=silent_ein, datafile=target)

    # 6. A silent AMOUNT change with no crosswalk entry.
    def silent_amount(rows, fields):
        for r in rows[:200]:
            r["amount"] = "1"
    scenario("200 amounts rewritten with no crosswalk entry",
             mutate_data=silent_amount, datafile=target)

    # 7. Two entries for one row under different defect labels, agreeing on the outcome.
    def dup_row(rows, fields):
        add = []
        for r in rows[:300]:
            if r["defect"] == "org_prose":
                c = dict(r)
                c["defect"] = "org_merged"
                c["original_organization"] = "A SECOND, CONTRADICTORY STORY"
                add.append(c)
        rows.extend(add)
        rows.sort(key=lambda r: (r["file"], int(r["line"])))
    scenario("one row given two contradictory audit-trail entries", mutate_cw=dup_row)

    # 8. Control: the gate's actual job.
    def real_break(rows, fields):
        rows[0]["recovered_organization"] = "NOT WHAT THE DATA SAYS"
    scenario("CONTROL — one entry disagrees with the data", mutate_cw=real_break)
    return 0


if __name__ == "__main__":
    sys.exit(main())
