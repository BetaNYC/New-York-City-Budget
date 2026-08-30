#!/usr/bin/env python3
"""Score EVERY applied repair, not a sample, against three sources that are independent of the
repair scripts, and report an error rate with its basis.

Sources
  D_same   the Council's expense disclosure workbook for the row's own fiscal year
  D_other  the same workbook series, any OTHER fiscal year (a separate publication event)
  T        the Transparency Resolutions (separate document, separate parser)
  C_other  this corpus's own rows for the same EIN in other fiscal years

A repair is scored:
  CONFIRMED_2+   at least two of {D, T, C} agree with the applied name
  CONFIRMED_1    exactly one agrees, none contradicts
  CONTRADICTED   a source that speaks for this exact (EIN, amount) gives a DIFFERENT single name
  AMBIGUOUS      the disclosure holds >1 distinct name for the key, so the unique-match gate the
                 scripts claim to enforce did not actually hold
  UNSUPPORTED    nothing speaks
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
CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"


def norm(v):
    return re.sub(r"\D", "", v or "")


def fy_of(p):
    m = re.search(r"[/\\]fy(\d{2})[/\\]", p)
    return 2000 + int(m.group(1)) if m else None


def transparency():
    out = collections.defaultdict(set)
    for f in glob.glob("data/fy*/transparency-resolutions/fy*_transparency_all.csv"):
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                try:
                    a = abs(int(float(r.get("amount") or 0)))
                except (TypeError, ValueError):
                    continue
                e, nm = norm(r.get("ein")), (r.get("organization") or "").strip()
                if e and nm:
                    out[(e, a)].add(nm)
    return out


def corpus_by_ein():
    out = collections.defaultdict(set)
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiativ" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                e, nm = norm(r.get("ein")), (r.get("organization") or "").strip()
                if e and nm:
                    out[e].add((fy_of(f), nm))
    return out


def main():
    per_year, pooled = build_lookups.load()
    sy = per_year["strict"]
    tr, cb = transparency(), corpus_by_ein()

    rows = list(csv.DictReader(open(CROSSWALK, newline="", encoding="utf-8")))
    score = collections.Counter()
    by_defect = collections.defaultdict(collections.Counter)
    flagged = collections.defaultdict(list)

    for r in rows:
        fy, key = fy_of(r["file"]), (r["ein"], int(r["amount"]))
        applied = r["recovered_organization"]
        if r["defect"] == "wrong_ein":                 # name unchanged; audited separately
            applied = re.sub(r"^\[ein \d+\]\s*", "", applied)
        ca = canon(applied)

        d_same = sy.get(fy, {}).get(key, set())
        d_other = {n for y, tbl in sy.items() if y != fy for n in tbl.get(key, set())}
        t = tr.get(key, set())
        c = {n for y, n in cb.get(r["ein"], set()) if y != fy}

        agree = set()
        if ca in {canon(x) for x in d_same}:
            agree.add("D")
        if ca in {canon(x) for x in d_other}:
            agree.add("D")
        if any(ca and ca in canon(x) for x in t):
            agree.add("T")
        if ca in {canon(x) for x in c}:
            agree.add("C")

        d_all = d_same or d_other
        d_canon = {canon(x) for x in d_all}
        if d_canon and len(d_canon) > 1 and r["defect"] != "member_bleed":
            v = "AMBIGUOUS"
        elif d_canon and len(d_canon) == 1 and ca not in d_canon:
            v = "CONTRADICTED"
        elif len(agree) >= 2:
            v = "CONFIRMED_2+"
        elif len(agree) == 1:
            v = "CONFIRMED_1"
        else:
            v = "UNSUPPORTED"
        score[v] += 1
        by_defect[r["defect"]][v] += 1
        if v in ("CONTRADICTED", "UNSUPPORTED", "AMBIGUOUS"):
            flagged[v].append((r, sorted(d_all)[:3], sorted(t)[:2], sorted(c)[:2]))

    n = len(rows)
    print(f"applied repairs scored: {n:,}\n")
    print(f"{'verdict':<16}{'n':>7}{'share':>9}")
    for v, k in score.most_common():
        print(f"{v:<16}{k:>7}{k / n:>8.2%}")
    print()
    print(f"{'defect':<14}" + "".join(f"{v:>15}" for v in
          ("CONFIRMED_2+", "CONFIRMED_1", "AMBIGUOUS", "CONTRADICTED", "UNSUPPORTED")))
    for d in sorted(by_defect):
        print(f"{d:<14}" + "".join(f"{by_defect[d][v]:>15}" for v in
              ("CONFIRMED_2+", "CONFIRMED_1", "AMBIGUOUS", "CONTRADICTED", "UNSUPPORTED")))

    for v in ("CONTRADICTED", "UNSUPPORTED"):
        print(f"\n===== {v} ({len(flagged[v])}) =====")
        for r, d, t, c in flagged[v][:30]:
            print(f"  {r['file'].split('/')[1]}:{r['line']} {r['defect']} ein={r['ein']} "
                  f"${int(r['amount']):,}")
            print(f"     applied      : {r['recovered_organization'][:70]!r}")
            print(f"     disclosure   : {[x[:50] for x in d]}")
            print(f"     transparency : {[x[:50] for x in t]}")
            print(f"     corpus other : {[x[:50] for x in c]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
