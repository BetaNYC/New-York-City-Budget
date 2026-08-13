#!/usr/bin/env python3
"""FY2021-specific diagnostics that compare_year.py does not do.

    python3 research/phase1-source-comparability/diagnose_2021.py

compare_year.py answers "how much do the two sources disagree". This answers "why".
Three questions, in order of how much they move the verdict:

  1. Every Schedule C EIN with no FY2021 disclosure row -- does that EIN appear in ANY
     OTHER disclosure year? An EIN the Council discloses in FY2020 and FY2022 but not
     FY2021 is a real FY2021 disclosure gap. An EIN it never discloses in any year is
     more likely a Schedule C transcription error. That split is the whole verdict.
  2. Council-member relabeling. Restricted to (EIN, amount) keys that are UNIQUE on both
     sides -- $5,000 designations collide across dozens of members and a naive join
     manufactures hundreds of spurious "member changed" pairs.
  3. The named mismatches quoted in comparison-2021.md, printed in full so the prose can
     be checked against the rows.

Stdlib only. Reads nothing outside the repo. Writes nothing.
"""

import csv
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "code"))
from parse_expense_disclosure import parse_year, SRC_DIR  # noqa: E402

SC_DIR = os.path.join(ROOT, "data", "fy21", "schedule_c")


def norm_ein(e):
    """9 digits, leading zeros preserved. Both sides publish bare digits, but the awards
    CSV carries a few EINs the PDF split with a dash, so strip non-digits first."""
    d = re.sub(r"\D", "", e or "")
    return d.zfill(9) if d else ""


def load_schedule_c():
    rows = []
    with open(os.path.join(SC_DIR, "fy21_schedule_c_awards.csv")) as f:
        for r in csv.DictReader(f):
            rows.append(dict(file="awards", member=r["member"], org=r["organization"],
                             ein=norm_ein(r["ein"]), amount=float(r["amount"] or 0),
                             agency=r.get("agency", ""),
                             init=r["initiative"] or r["category"]))
    for fn, src in (("fy21_appendix_a_aging.csv", "Aging"),
                    ("fy21_appendix_b_local.csv", "Local"),
                    ("fy21_appendix_c_youth.csv", "Youth")):
        with open(os.path.join(SC_DIR, fn)) as f:
            for r in csv.DictReader(f):
                rows.append(dict(file=fn, member=r["member"], org=r["organization"],
                                 ein=norm_ein(r["ein"]), amount=float(r["amount"] or 0),
                                 agency=r.get("agency", ""), init=src))
    return rows


def load_disclosure(fy=2021):
    aw, rep = parse_year(os.path.join(SRC_DIR, f"funded_disclosure_FY{fy}.xlsx"))
    return [dict(bucket=a.source, member=a.council_member, org=a.legal_name,
                 ein=norm_ein(a.ein), amount=a.amount, status=a.status_norm,
                 row=a.source_row, agency=a.agency) for a in aw], rep


def hdr(t):
    print("\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)


def q1_cross_year(sc, dis):
    hdr("1. SCHEDULE-C-ONLY EINs -- present in any OTHER disclosure year?")
    have21 = {d["ein"] for d in dis}
    only = sorted({s["ein"] for s in sc if s["ein"] and s["ein"] not in have21})
    # First occurrence of each EIN on the Schedule C side, for labeling.
    label = {}
    for s in sc:
        label.setdefault(s["ein"], s)

    years = {}
    for y in range(2014, 2028):
        p = os.path.join(SRC_DIR, f"funded_disclosure_FY{y}.xlsx")
        if os.path.exists(p):
            aw, _ = parse_year(p)
            years[y] = {norm_ein(a.ein) for a in aw}

    elsewhere, never = [], []
    for e in only:
        ys = sorted(y for y, s in years.items() if e in s)
        (elsewhere if ys else never).append((e, ys))

    print(f"Schedule C EINs with no FY2021 disclosure row : {len(only)}")
    print(f"  disclosed in at least one OTHER year        : {len(elsewhere)}"
          f"   <-- real FY2021 disclosure gaps")
    print(f"  disclosed in NO year at all                 : {len(never)}"
          f"   <-- candidate Schedule C EIN errors")

    print("\n-- disclosed in other years, absent from FY2021 --")
    for e, ys in elsewhere:
        s = label[e]
        print(f"  {e}  FY{min(ys)}-FY{max(ys)} ({len(ys)} yrs)  "
              f"{s['member']!r:16s} ${s['amount']:>10,.0f}  {s['org'][:56]!r}")
    print("\n-- in no disclosure year at all --")
    for e, _ in never:
        s = label[e]
        print(f"  {e}  {s['member']!r:16s} ${s['amount']:>10,.0f}  {s['org'][:56]!r}")
    return only


def q2_member_crosswalk(sc, dis):
    hdr("2. COUNCIL-MEMBER CROSSWALK -- (EIN, amount) keys UNIQUE on both sides")
    dk = Counter((d["ein"], round(d["amount"], 2)) for d in dis)
    sk = Counter((s["ein"], round(s["amount"], 2)) for s in sc)
    # ponytail: uniqueness on both sides is the whole trick. Without it a $5,000 key joins
    # every member who gave $5,000 to that org, and the output is noise.
    uniq = {k for k in dk if dk[k] == 1 and sk.get(k) == 1}
    dmap = {(d["ein"], round(d["amount"], 2)): d for d in dis}

    same, pairs = 0, Counter()
    for s in sc:
        k = (s["ein"], round(s["amount"], 2))
        if k in uniq and s["member"]:
            d = dmap[k]
            if s["member"] == d["member"]:
                same += 1
            else:
                pairs[(s["member"], d["member"])] += 1
    n = same + sum(pairs.values())
    print(f"unique-key matches: {n}   member identical: {same} ({same / n * 100:.1f}%)"
          f"   member differs: {sum(pairs.values())}")
    print("\npairs occurring 3+ times:")
    for (a, b), c in pairs.most_common():
        if c >= 3:
            print(f"  {c:5d}  schedule C {a!r:20s} -> disclosure {b!r}")
    tail = sum(c for c in pairs.values() if c < 3)
    print(f"\n({tail} further pairs occur once or twice -- long tail, not a pattern)")

    print("\n-- per-member: where do a departed member's rows land in disclosure? --")
    for m in ("King", "Lancman", "Menchaca", "Richards", "Torres"):
        rows = [s for s in sc if s["member"] == m]
        t, miss = Counter(), 0
        for s in rows:
            c = [d["member"] for d in dis
                 if d["ein"] == s["ein"] and round(d["amount"], 2) == round(s["amount"], 2)]
            if c:
                t[max(set(c), key=c.count)] += 1
            else:
                miss += 1
        print(f"  schedule C {m:11s} n={len(rows):4d}  unmatched={miss:3d}  {t.most_common(3)}")
    print("\n-- and the reverse, for members disclosure has that Schedule C does not --")
    for m in ("Aviles", "Brooks-Powers", "D. Diaz", "Feliz", "Gennaro", "Riley"):
        rows = [d for d in dis if d["member"] == m]
        t, miss = Counter(), 0
        for d in rows:
            c = [s["member"] for s in sc
                 if s["ein"] == d["ein"] and round(s["amount"], 2) == round(d["amount"], 2)]
            if c:
                t[max(set(c), key=c.count)] += 1
            else:
                miss += 1
        print(f"  disclosure {m:13s} n={len(rows):4d}  unmatched={miss:3d}  {t.most_common(3)}")


CASES = [
    ("M1  ANHD -- same org, different EIN", ("132775999",), ("265551998",)),
    ("M2  Asiyah Women's Center -- same org, different EIN", ("832104070",), ("822712941",)),
    ("M3  BAFA -- disclosure splits into 3 rows, Schedule C has 1", ("454788710",), ("454788710",)),
    ("M4  Sustainable South Bronx -- absent from FY2021 disclosure entirely "
     "(disclosure side prints nothing; that IS the finding)", ("020535999",), ("020535999",)),
    ("M5  Schedule C 'organization' is a purpose string + PDF page header",
     ("113462888",), ("113462888",)),
    ("M6  Bard College -- the canonical test case, FY2021", ("141713034",), ("141713034",)),
    ("M7  Chin $7,700 -- Earth Matter vs Triangle Fire",
     ("270625845",), ("270625845", "455137219")),
    ("M8  Bay Ridge Community Council -- in Schedule C, not in FY2021 disclosure",
     ("112602994",), ("112602994",)),
    ("M9  White Plains Road DMA -- EIN in no disclosure year", ("133776486",), ("133776486",)),
    ("M10 AIMHigh -- King -> Riley", ("813143733",), ("813143733",)),
    ("M11 Arab American Association -- Menchaca -> Aviles", ("113604756",), ("113604756",)),
    ("M12 Belmont DMA -- Torres -> Feliz", ("270834463",), ("270834463",)),
]


def q3_quoted(sc, dis):
    hdr("3. THE MISMATCHES QUOTED IN comparison-2021.md")
    for label, deins, seins in CASES:
        print(f"\n--- {label} ---")
        for d in dis:
            if d["ein"] in deins:
                print(f"  DISCLOSURE row {d['row']}: source={d['bucket']!r} "
                      f"member={d['member']!r} legal_name={d['org']!r} ein={d['ein']} "
                      f"amount={d['amount']:,.0f} status={d['status']!r} agency={d['agency']!r}")
        for s in sc:
            if s["ein"] in seins:
                print(f"  SCHEDULE C [{s['file']}]: initiative={s['init']!r} "
                      f"member={s['member']!r} organization={s['org']!r} ein={s['ein']} "
                      f"amount={s['amount']:,.0f} agency={s['agency']!r}")


def demo(sc, dis, rep):
    """One runnable check. Asserts the load is intact and the headline claims in
    comparison-2021.md still hold, so a re-parse that silently changes either source
    fails here rather than quietly contradicting the report."""
    assert len(dis) == 9054, len(dis)
    assert round(sum(d["amount"] for d in dis)) == 393_250_506
    assert len(sc) == 6120, len(sc)
    assert round(sum(s["amount"] for s in sc)) == 251_869_188
    # The report's central structural claim: the three appendix files reproduce the three
    # disclosure Source buckets to the dollar, while carrying fewer rows.
    for src, fn in (("Aging", "fy21_appendix_a_aging.csv"),
                    ("Local", "fy21_appendix_b_local.csv"),
                    ("Youth", "fy21_appendix_c_youth.csv")):
        d = sum(x["amount"] for x in dis if x["bucket"] == src)
        c = sum(x["amount"] for x in sc if x["file"] == fn)
        assert d == c, (src, d, c)
        assert len([x for x in dis if x["bucket"] == src]) >= \
               len([x for x in sc if x["file"] == fn]), src
    # And the claim that falsifies "disclosure is a superset".
    only = {s["ein"] for s in sc if s["ein"]} - {d["ein"] for d in dis}
    assert len(only) == 74, len(only)
    # The sheet name carries the snapshot date the succession finding rests on.
    assert rep.sheet_name == "FY21 (06-23-2023)", rep.sheet_name
    print("demo: ok -- 6 assertions on the FY2021 corpus hold")


if __name__ == "__main__":
    sc = load_schedule_c()
    dis, rep = load_disclosure()
    demo(sc, dis, rep)
    print(f"\ndisclosure sheet name: {rep.sheet_name!r}  "
          f"(the workbook's own as-of date, three FYs after FY2021)")
    q1_cross_year(sc, dis)
    q2_member_crosswalk(sc, dis)
    q3_quoted(sc, dis)
