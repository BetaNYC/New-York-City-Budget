#!/usr/bin/env python3
"""Draw a reproducible random sample of applied repairs and lay out every piece of independent
evidence for each, so a human verdict can be reached per row.

Evidence axes, in decreasing independence from the repair itself:
  1. the Council's expense disclosure workbook, read by reference position (all 14 years)
  2. the Transparency Resolutions -- a separate publication, parsed by a separate parser
  3. this corpus's own rows for the same EIN in OTHER fiscal years

Usage: python3 sample_verify.py [n_per_class] [seed]
"""
import collections
import csv
import glob
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "code"))
import build_lookups             # noqa: E402
import recover_org_names as ROG  # noqa: E402

canon = ROG.canon
CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 20260813


def norm(v):
    return re.sub(r"\D", "", v or "")


def fy_of(p):
    m = re.search(r"[/\\]fy(\d{2})[/\\]", p)
    return 2000 + int(m.group(1)) if m else None


def transparency():
    """(ein, amount) -> {(fy, name)} from the Transparency Resolutions."""
    out = collections.defaultdict(set)
    for f in glob.glob("data/fy*/transparency-resolutions/fy*_transparency_all.csv"):
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                try:
                    a = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    continue
                e = norm(r.get("ein"))
                nm = (r.get("organization") or "").strip()
                if e and nm:
                    out[(e, abs(a))].add((r.get("fiscal_year", ""), nm))
    return out


def corpus_by_ein():
    out = collections.defaultdict(set)
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                e = norm(r.get("ein"))
                nm = (r.get("organization") or "").strip()
                if e and nm:
                    out[e].add((fy_of(f), nm))
    return out


def main():
    per_year, pooled = build_lookups.load()
    sy = per_year["strict"]
    tr = transparency()
    cb = corpus_by_ein()

    rows = list(csv.DictReader(open(CROSSWALK, newline="", encoding="utf-8")))
    # residual-recovered rows are labelled by their multi-source `source` value, not `defect`
    def cls(r):
        if r["defect"] == "member_bleed":
            return "member_bleed"
        if r["defect"] == "wrong_ein":
            return "wrong_ein"
        if "+" in r["source"]:
            return "residual(" + r["defect"] + ")"
        return r["defect"]

    buckets = collections.defaultdict(list)
    for r in rows:
        buckets[cls(r)].append(r)

    rnd = random.Random(SEED)
    print(f"# hand-verification sample  seed={SEED}  n={N} per class")
    print(f"# classes: {{k: len(v) for k, v in buckets.items()}}".replace("{k: len(v) for k, v in buckets.items()}",
          str({k: len(v) for k, v in sorted(buckets.items())})))
    total = 0
    for k in sorted(buckets):
        pick = rnd.sample(buckets[k], min(N, len(buckets[k])))
        for r in pick:
            total += 1
            fy = fy_of(r["file"])
            key = (r["ein"], int(r["amount"]))
            print()
            print(f"[{total}] {k}  {r['file'].split('/')[1]}:{r['line']}  "
                  f"ein={r['ein']} ${int(r['amount']):,}  FY{fy}")
            print(f"     WAS      : {r['original_organization'][:100]!r}")
            print(f"     APPLIED  : {r['recovered_organization'][:100]!r}")
            own = sorted(sy.get(fy, {}).get(key, set()))
            print(f"     disclosure FY{fy}   : {own if own else '-- none --'}")
            other = sorted({(y, n) for y, tbl in sy.items() if y != fy
                            for n in tbl.get(key, set())})
            print(f"     disclosure other yrs: {other[:4] if other else '-- none --'}")
            t = sorted(tr.get(key, set()))
            print(f"     transparency reso   : {t[:3] if t else '-- none --'}")
            c = sorted({(y, n) for y, n in cb.get(r['ein'], set()) if y != fy})
            print(f"     corpus other yrs    : {c[:4] if c else '-- none --'}")
            ev = []
            if own and canon(r['recovered_organization']) in {canon(x) for x in own}:
                ev.append("disclosure-same-year")
            if other and canon(r['recovered_organization']) in {canon(n) for _, n in other}:
                ev.append("disclosure-other-year")
            if t and canon(r['recovered_organization']) in {canon(n) for _, n in t}:
                ev.append("transparency")
            if c and canon(r['recovered_organization']) in {canon(n) for _, n in c}:
                ev.append("corpus-other-year")
            print(f"     >>> corroborated by: {ev if ev else 'NOTHING'}"
                  f"   (independent sources: {len(set(x.split('-')[0] for x in ev))})")
    print(f"\nsampled {total} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
