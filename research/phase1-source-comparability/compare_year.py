#!/usr/bin/env python3
"""Compare the Council's expense disclosure workbook against parsed Schedule C, one FY.

    python3 research/phase1-source-comparability/compare_year.py 2018

Disclosure side : source/expense-funding-disclosure/funded_disclosure_FY{YYYY}.xlsx
                  read through code/parse_expense_disclosure.py (stdlib only).
Schedule C side : data/fy{YY}/schedule_c/fy{YY}_schedule_c_awards.csv
                  + fy{YY}_appendix_{a_aging,b_local,c_youth}.csv

Everything is a set / multiset comparison in BOTH directions. The direction that matters
most is Schedule C -> disclosure: a Schedule C EIN with no disclosure counterpart falsifies
"the disclosure is a superset of Schedule C".

Prints a report to stdout. Writes nothing. Reads nothing outside the repo.
"""

import csv
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "code"))
from parse_expense_disclosure import parse_year  # noqa: E402

APPENDIX = {"a_aging": "Aging", "b_local": "Local", "c_youth": "Youth"}


def norm_ein(v):
    """Digits only, left-padded to 9. Both sides publish 9-digit EINs, but a hyphenated
    or short one would otherwise silently fail to join."""
    d = re.sub(r"\D", "", v or "")
    return d.zfill(9) if d else ""


def cents(v):
    return int(round(float(v) * 100))


def money(c):
    return f"${c / 100:,.2f}"


def load_schedule_c(fy):
    """Return (awards_rows, appendix_rows). Each row is a dict with a `_src` tag."""
    yy = f"{fy % 100:02d}"
    d = os.path.join(ROOT, "data", f"fy{yy}", "schedule_c")
    awards = []
    p = os.path.join(d, f"fy{yy}_schedule_c_awards.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, newline="")):
            r["_src"] = "awards"
            awards.append(r)
    appendix = []
    for suffix, label in APPENDIX.items():
        p = os.path.join(d, f"fy{yy}_appendix_{suffix}.csv")
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p, newline="")):
            r["_src"] = f"appendix_{suffix}"
            r["_appendix_source"] = label
            appendix.append(r)
    return awards, appendix


def h(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main(fy):
    xlsx = os.path.join(ROOT, "source", "expense-funding-disclosure",
                        f"funded_disclosure_FY{fy}.xlsx")
    disc, rep = parse_year(xlsx)
    if rep.skipped:
        print(f"disclosure FY{fy} SKIPPED: {rep.skipped}")
        return 1
    awards, appendix = load_schedule_c(fy)
    sched = awards + appendix

    h(f"FY{fy} ROW AND DOLLAR TOTALS")
    print(f"disclosure   rows {len(disc):>6}   {money(sum(cents(a.amount) for a in disc))}"
          f"   file={rep.source_file} sheet={rep.sheet_name!r}")
    for k, v in sorted(rep.by_status.items()):
        tot = sum(cents(a.amount) for a in disc if a.status_norm == k)
        print(f"    status {k:<10} rows {v:>6}   {money(tot)}")
    print(f"schedule C   rows {len(sched):>6}   {money(sum(cents(r['amount']) for r in sched))}")
    for src in sorted({r["_src"] for r in sched}):
        rows = [r for r in sched if r["_src"] == src]
        print(f"    {src:<20} rows {len(rows):>6}   "
              f"{money(sum(cents(r['amount']) for r in rows))}")
    if awards:
        for t in sorted({r.get("award_type", "") for r in awards}):
            rows = [r for r in awards if r.get("award_type", "") == t]
            print(f"      award_type {t:<20} rows {len(rows):>5}   "
                  f"{money(sum(cents(r['amount']) for r in rows))}")

    # ---- by EIN, both directions -------------------------------------------------
    d_ein = defaultdict(list)
    for a in disc:
        d_ein[norm_ein(a.ein)].append(a)
    s_ein = defaultdict(list)
    for r in sched:
        s_ein[norm_ein(r["ein"])].append(r)

    only_s = sorted(set(s_ein) - set(d_ein))
    only_d = sorted(set(d_ein) - set(s_ein))
    both = sorted(set(s_ein) & set(d_ein))

    h("BY EIN, BOTH DIRECTIONS")
    print(f"distinct EIN  disclosure {len(d_ein):>6}   schedule C {len(s_ein):>6}"
          f"   in both {len(both):>6}")
    print(f"Schedule C EIN NOT in disclosure : {len(only_s)}   "
          f"({money(sum(cents(r['amount']) for e in only_s for r in s_ein[e]))}, "
          f"{sum(len(s_ein[e]) for e in only_s)} rows)   <-- falsifies superset if > 0")
    print(f"disclosure EIN NOT in Schedule C : {len(only_d)}   "
          f"({money(sum(cents(a.amount) for e in only_d for a in d_ein[e]))}, "
          f"{sum(len(d_ein[e]) for e in only_d)} rows)")
    cl = sum(1 for e in only_d for a in d_ein[e] if a.status_norm == "cleared")
    pd_ = sum(1 for e in only_d for a in d_ein[e] if a.status_norm == "pending")
    print(f"    of those disclosure-only rows: cleared {cl}, pending {pd_}")
    print("\nSchedule C EINs absent from disclosure (all, with rows):")
    for e in only_s:
        for r in s_ein[e]:
            print(f"  {e}  {money(cents(r['amount'])):>16}  [{r['_src']}] "
                  f"{r.get('organization', '')[:90]!r}")

    # ---- by exact award ----------------------------------------------------------
    h("BY EXACT AWARD")
    d_pair = Counter((norm_ein(a.ein), cents(a.amount)) for a in disc)
    s_pair = Counter((norm_ein(r["ein"]), cents(r["amount"])) for r in sched)
    inter = d_pair & s_pair
    print(f"(EIN, amount)          disclosure {sum(d_pair.values()):>6} rows / "
          f"{len(d_pair)} keys   schedule C {sum(s_pair.values()):>6} rows / {len(s_pair)} keys")
    print(f"                       matched multiset {sum(inter.values())} rows "
          f"({sum(inter.values()) / max(1, sum(s_pair.values())):.1%} of Schedule C)")
    s_un = s_pair - d_pair
    d_un = d_pair - s_pair
    print(f"  Schedule C rows unmatched : {sum(s_un.values()):>6}   "
          f"{money(sum(k[1] * n for k, n in s_un.items()))}")
    print(f"  disclosure rows unmatched : {sum(d_un.values()):>6}   "
          f"{money(sum(k[1] * n for k, n in d_un.items()))}")

    def memb(x):
        return re.sub(r"\s+", " ", (x or "")).strip().lower()

    d_tri = Counter((norm_ein(a.ein), cents(a.amount), memb(a.council_member)) for a in disc)
    s_tri = Counter((norm_ein(r["ein"]), cents(r["amount"]), memb(r.get("member", "")))
                    for r in sched)
    inter3 = d_tri & s_tri
    print(f"\n(EIN, amount, member)  matched multiset {sum(inter3.values())} rows "
          f"({sum(inter3.values()) / max(1, sum(s_tri.values())):.1%} of Schedule C)")
    print(f"  Schedule C rows unmatched : {sum((s_tri - d_tri).values()):>6}")
    print(f"  disclosure rows unmatched : {sum((d_tri - s_tri).values()):>6}")

    # ---- by council member -------------------------------------------------------
    h("BY COUNCIL MEMBER")
    dm = Counter(memb(a.council_member) for a in disc)
    sm = Counter(memb(r.get("member", "")) for r in sched)
    print(f"distinct values  disclosure {len(dm)}   schedule C {len(sm)}")
    print(f"disclosure blank {dm.get('', 0)}   schedule C blank {sm.get('', 0)}")
    print("\ndisclosure member values (count, $):")
    for k in sorted(dm):
        tot = sum(cents(a.amount) for a in disc if memb(a.council_member) == k)
        print(f"  {k!r:<28} {dm[k]:>5}  {money(tot):>16}")
    print("\nschedule C member values (count, $):")
    for k in sorted(sm):
        tot = sum(cents(r["amount"]) for r in sched if memb(r.get("member", "")) == k)
        print(f"  {k!r:<28} {sm[k]:>5}  {money(tot):>16}")
    print("\nsurname collision probe (Williams / Sanchez / Rivera / Barron / Vallone):")
    for side, c in (("disclosure", dm), ("schedule C", sm)):
        hit = {k: v for k, v in c.items()
               if any(s in k for s in
                      ("williams", "sanchez", "rivera", "barron", "vallone"))}
        print(f"  {side}: {hit}")

    # ---- initiative vocabulary ---------------------------------------------------
    h("SOURCE / INITIATIVE VOCABULARY")
    dsrc = Counter(a.source for a in disc)
    sinit = Counter(r.get("initiative", "") for r in awards)
    scat = Counter(r.get("category", "") for r in awards)
    sapp = Counter(r.get("_appendix_source", "") for r in appendix)
    print(f"disclosure Source values : {len(dsrc)}")
    print(f"schedule C initiative    : {len(sinit)}    category: {len(scat)}")
    print(f"schedule C appendix files: {dict(sapp)}")

    def key(s):
        return re.sub(r"[^a-z0-9]", "", (s or "").lower())

    dkeys = {key(k): k for k in dsrc}
    skeys = {key(k): k for k in list(sinit) + list(scat) + list(sapp)}
    shared = sorted(set(dkeys) & set(skeys))
    print(f"\nexact-after-normalization overlap: {len(shared)} names")
    for k in shared:
        print(f"  {dkeys[k]!r:<58} disc {dsrc[dkeys[k]]:>4}  "
              f"schedC {sinit.get(skeys[k], 0) + scat.get(skeys[k], 0) + sapp.get(skeys[k], 0):>4}")
    print(f"\ndisclosure Source with NO Schedule C counterpart: "
          f"{len(set(dkeys) - set(skeys))}")
    for k in sorted(set(dkeys) - set(skeys), key=lambda x: -dsrc[dkeys[x]]):
        print(f"  {dkeys[k]!r:<62} {dsrc[dkeys[k]]:>5} rows  "
              f"{money(sum(cents(a.amount) for a in disc if a.source == dkeys[k]))}")
    print(f"\nSchedule C initiative/category with NO disclosure counterpart: "
          f"{len(set(skeys) - set(dkeys))}")
    for k in sorted(set(skeys) - set(dkeys)):
        n = sinit.get(skeys[k], 0) + scat.get(skeys[k], 0) + sapp.get(skeys[k], 0)
        print(f"  {skeys[k]!r:<62} {n:>5} rows")

    # ---- dollars per initiative --------------------------------------------------
    h("DOLLARS PER SHARED INITIATIVE NAME (disclosure Source vs Schedule C initiative)")
    print(f"{'name':<52}{'disc $':>16}{'schedC $':>16}{'delta':>16}")
    for k in shared:
        dv = sum(cents(a.amount) for a in disc if a.source == dkeys[k])
        sv = sum(cents(r["amount"]) for r in awards
                 if key(r.get("initiative", "")) == k or key(r.get("category", "")) == k)
        sv += sum(cents(r["amount"]) for r in appendix
                  if key(r.get("_appendix_source", "")) == k)
        print(f"{dkeys[k][:50]:<52}{money(dv):>16}{money(sv):>16}{money(sv - dv):>16}")

    return 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2018))
