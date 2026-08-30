#!/usr/bin/env python3
"""Audit data/recovered/schedule_c_absorbed_awards.csv.

Three questions:
  1. the one (fy, ein, amount) that collides with a live award row -- real duplicate or coincidence?
  2. internal duplicates within the sidecar itself
  3. how much of it the Council's own disclosure actually confirms, and whether the host row
     that absorbed the text already carries the absorbed award's dollars
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
SIDE = "data/recovered/schedule_c_absorbed_awards.csv"


def norm_ein(v):
    return re.sub(r"\D", "", v or "")


def amt(r):
    try:
        return int(float(r.get("amount") or 0))
    except (TypeError, ValueError):
        return None


def fy_of(p):
    m = re.search(r"[/\\]fy(\d{2})[/\\]", p)
    return 2000 + int(m.group(1)) if m else None


def main():
    live = collections.defaultdict(list)
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                live[(fy_of(f), norm_ein(r.get("ein")), amt(r))].append((f, ln, r))

    rows = list(csv.DictReader(open(SIDE, newline="", encoding="utf-8")))
    print(f"sidecar rows: {len(rows):,}  dollars: ${sum(amt(r) or 0 for r in rows):,}")

    print("\n--- 1. collisions with a live award row on (fy, ein, amount) ---")
    for r in rows:
        k = (int(r["fiscal_year"]), norm_ein(r["ein"]), amt(r))
        for f, ln, lr in live.get(k, []):
            print(f"  sidecar: {r['organization'][:55]!r} ${amt(r):,} FY{r['fiscal_year']}")
            print(f"           absorbed_from {r['absorbed_from_file'].split('/')[1]}:"
                  f"{r['absorbed_from_line']}  confidence={r['confidence']} "
                  f"disclosure_confirmed={r['disclosure_confirmed']}")
            print(f"  live   : {f.split('/')[1]}:{ln} {lr.get('organization','')[:55]!r} "
                  f"ein={lr.get('ein')} ${amt(lr):,}")

    print("\n--- 2. internal duplicates within the sidecar ---")
    seen = collections.Counter()
    for r in rows:
        seen[(r["fiscal_year"], norm_ein(r["ein"]), amt(r), canon(r["organization"]))] += 1
    dup = {k: v for k, v in seen.items() if v > 1}
    print(f"  duplicate (fy, ein, amount, canon-name) tuples: {len(dup)}")
    for k, v in list(dup.items())[:10]:
        print("   ", v, k)

    print("\n--- 3. corroboration ---")
    print("  confidence:", collections.Counter(r["confidence"] for r in rows))
    print("  disclosure_confirmed:",
          collections.Counter(r["disclosure_confirmed"] for r in rows))
    print("  name_source:", collections.Counter(r["name_source"] for r in rows))

    # Independent re-confirmation against a reference-positioned read of the workbooks
    per_year, pooled = build_lookups.load()
    strict = pooled["strict"]
    ok = bad = none = 0
    for r in rows:
        k = (norm_ein(r["ein"]), amt(r))
        cand = strict.get(k, set())
        if not cand:
            none += 1
        elif canon(r["organization"]) in {canon(c) for c in cand}:
            ok += 1
        else:
            bad += 1
    print(f"\n  independent (EIN, amount) check against the disclosure:")
    print(f"    name matches a published legal name : {ok}")
    print(f"    name contradicts the published name : {bad}")
    print(f"    no disclosure row for that key      : {none}")

    print("\n--- 4. does the HOST row already carry the absorbed dollars? ---")
    # For each host (file, line), sum the absorbed children and compare with the host's own amount.
    hosts = collections.defaultdict(list)
    for r in rows:
        hosts[(r["absorbed_from_file"], int(r["absorbed_from_line"]))].append(r)
    shown = 0
    equal = 0
    for (f, ln), kids in sorted(hosts.items()):
        with open(f, newline="", encoding="utf-8") as fh:
            data = list(csv.DictReader(fh))
        host = data[ln - 2]
        h = amt(host)
        s = sum(amt(k) or 0 for k in kids)
        if h is not None and h == s:
            equal += 1
        if shown < 8:
            print(f"  {f.split('/')[1]}:{ln} host=${h:,} absorbed_children={len(kids)} "
                  f"sum=${s:,}  host_org={host.get('organization','')[:40]!r}")
            shown += 1
    print(f"  host rows: {len(hosts)};  host amount == sum of its absorbed children: {equal}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
