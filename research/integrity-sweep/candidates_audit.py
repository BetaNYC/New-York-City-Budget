#!/usr/bin/env python3
"""Audit code/absorbed_award_candidates.csv -- the checked-in intermediate the 443-row absorbed
sidecar is generated from. No script in the repo produces this file, so its columns cannot be
re-derived; they can only be re-checked.

Checks:
  * `already_in_corpus` recomputed from the live per-year CSVs
  * `absorbing_line` -- does the named row actually contain absorbed text?
  * quality of the names shipped in the sidecar (prose, bled surnames, embedded EINs)
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
import recover_org_names as ROG  # noqa: E402
import fix_member_bleed as FMB   # noqa: E402

canon = ROG.canon
CAND = "code/absorbed_award_candidates.csv"
SIDE = "data/recovered/schedule_c_absorbed_awards.csv"
EIN_IN_TEXT = re.compile(r"\d{2}-\d{7}")


def norm(v):
    return re.sub(r"\D", "", v or "")


def fy_of(p):
    m = re.search(r"[/\\]fy(\d{2})[/\\]", p)
    return 2000 + int(m.group(1)) if m else None


def main():
    live = collections.Counter()
    live_rows = {}
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                try:
                    a = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    continue
                live[(fy_of(f), norm(r.get("ein")), a)] += 1
                live_rows.setdefault((f, ln), r)

    cands = list(csv.DictReader(open(CAND, newline="", encoding="utf-8")))
    print(f"candidates: {len(cands)}")

    print("\n--- already_in_corpus, as flagged vs recomputed ---")
    tab = collections.Counter()
    wrong = []
    for c in cands:
        fy = 2000 + int(c["fy"][2:])
        k = (fy, norm(c["ein"]), int(float(c["amount"])))
        recomputed = "1" if live.get(k) else "0"
        tab[(c.get("already_in_corpus"), recomputed)] += 1
        if c.get("already_in_corpus") == "0" and recomputed == "1":
            wrong.append((c, k))
    for k, v in sorted(tab.items()):
        print(f"  flagged={k[0]}  recomputed={k[1]}  n={v}")
    print(f"\n  candidates emitted into the sidecar that ARE already in the corpus: {len(wrong)}")
    for c, k in wrong:
        print(f"    FY{k[0]} ein={k[1]} ${k[2]:,}  {c['first_candidate_name'][:50]!r}"
              f"  verdict={c['verdict']}")

    print("\n--- does absorbing_line actually hold absorbed text? ---")
    bad_anchor = 0
    for c in cands:
        r = live_rows.get((c["absorbing_file"], int(c["absorbing_line"])))
        if r is None:
            continue
        org = (r.get("organization") or "")
        if not (EIN_IN_TEXT.search(org) or "$" in org or "*" in org):
            bad_anchor += 1
            if bad_anchor <= 12:
                print(f"    {c['absorbing_file'].split('/')[1]}:{c['absorbing_line']} "
                      f"org={org[:52]!r}  -> child {c['first_candidate_name'][:36]!r}")
    print(f"  absorbing rows with NO visible absorbed text: {bad_anchor} of {len(cands)}")

    print("\n--- quality of names shipped in the sidecar ---")
    side = list(csv.DictReader(open(SIDE, newline="", encoding="utf-8")))
    surnames = FMB.build_surnames(FMB.surname_sources())
    prose = [r for r in side if ROG.is_prose(r["organization"])]
    bled = [r for r in side if FMB.peel(r["organization"].strip(), surnames)[0]]
    einy = [r for r in side if EIN_IN_TEXT.search(r["organization"] or "")]
    print(f"  organization holds purpose prose        : {len(prose)}")
    for r in prose[:6]:
        print(f"      {r['organization'][:70]!r}  ${int(r['amount']):,}")
    print(f"  organization leads with a member surname: {len(bled)}")
    for r in bled[:8]:
        print(f"      {r['organization'][:60]!r}  name_source={r['name_source']}")
    print(f"  organization contains an EIN            : {len(einy)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
