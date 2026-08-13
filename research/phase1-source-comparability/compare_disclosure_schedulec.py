#!/usr/bin/env python3
"""Compare a Council expense-disclosure workbook against the parsed Schedule C corpus.

    python3 research/phase1-source-comparability/compare_disclosure_schedulec.py 2020

Left side  : source/expense-funding-disclosure/funded_disclosure_FY{YYYY}.xlsx
             via code/parse_expense_disclosure.parse_year (stdlib xlsx reader).
Right side : data/fy{yy}/schedule_c/fy{yy}_schedule_c_awards.csv  +  the three
             appendix CSVs for that year.  READ-ONLY -- this script never writes there.

Everything is printed. Nothing is written. No network.
"""

import csv
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "code"))
from parse_expense_disclosure import parse_year  # noqa: E402

FY = int(sys.argv[1]) if len(sys.argv) > 1 else 2020
YY = f"{FY % 100:02d}"
SC_DIR = os.path.join(ROOT, "data", f"fy{YY}", "schedule_c")


def money(x):
    return f"${x:,.0f}"


def load_schedule_c():
    """Body awards + appendix rows, tagged by which file they came from."""
    rows = []
    body = os.path.join(SC_DIR, f"fy{YY}_schedule_c_awards.csv")
    with open(body, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["_file"] = os.path.basename(body)
            r["_kind"] = r.get("award_type", "")
            rows.append(r)
    for tag in ("a_aging", "b_local", "c_youth"):
        p = os.path.join(SC_DIR, f"fy{YY}_appendix_{tag}.csv")
        if not os.path.exists(p):
            continue
        with open(p, newline="", encoding="utf-8") as f:
            n = 0
            for r in csv.DictReader(f):
                r["_file"] = os.path.basename(p)
                r["_kind"] = "appendix_" + tag.split("_")[1]
                r.setdefault("category", "")
                r.setdefault("initiative", "")
                rows.append(r)
                n += 1
            print(f"    {os.path.basename(p)}: {n} data rows")
    return rows


def sc_amount(r):
    s = (r.get("amount") or "").strip()
    return float(s) if s else 0.0


def sc_ein(r):
    return (r.get("ein") or "").strip()


def h(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def main():
    print(f"FISCAL YEAR {FY}")
    print(f"disclosure : source/expense-funding-disclosure/funded_disclosure_FY{FY}.xlsx")
    print(f"schedule c : data/fy{YY}/schedule_c/")
    print("  appendix files:")
    sc = load_schedule_c()
    disc, rep = parse_year(
        os.path.join(ROOT, "source", "expense-funding-disclosure",
                     f"funded_disclosure_FY{FY}.xlsx"))

    cleared = [a for a in disc if a.status_norm == "cleared"]
    pending = [a for a in disc if a.status_norm == "pending"]

    # ---------------------------------------------------------------- totals
    h("1. ROW AND DOLLAR TOTALS")
    print(f"disclosure rows            {len(disc):>8}   {money(rep.total_amount):>16}")
    print(f"  cleared                  {len(cleared):>8}   "
          f"{money(sum(a.amount for a in cleared)):>16}")
    print(f"  pending                  {len(pending):>8}   "
          f"{money(sum(a.amount for a in pending)):>16}")
    print(f"  stripped summary rows    {rep.n_stripped:>8}")
    body = [r for r in sc if r["_file"].endswith("awards.csv")]
    apx = [r for r in sc if not r["_file"].endswith("awards.csv")]
    print(f"schedule C body rows       {len(body):>8}   "
          f"{money(sum(sc_amount(r) for r in body)):>16}")
    for k in ("member_item", "initiative_provider"):
        sub = [r for r in body if r["_kind"] == k]
        print(f"  {k:<24} {len(sub):>8}   {money(sum(sc_amount(r) for r in sub)):>16}")
    print(f"schedule C appendix rows   {len(apx):>8}   "
          f"{money(sum(sc_amount(r) for r in apx)):>16}")
    print(f"schedule C TOTAL           {len(sc):>8}   "
          f"{money(sum(sc_amount(r) for r in sc)):>16}")
    print()
    print(f"row delta   disclosure - scheduleC = {len(disc) - len(sc):+}")
    print(f"$   delta   disclosure - scheduleC = "
          f"{money(rep.total_amount - sum(sc_amount(r) for r in sc))}")

    # ------------------------------------------------------------------- EIN
    h("2. BY EIN, BOTH DIRECTIONS")
    d_ein = defaultdict(list)
    for a in disc:
        if a.ein:
            d_ein[a.ein].append(a)
    s_ein = defaultdict(list)
    for r in sc:
        if sc_ein(r):
            s_ein[sc_ein(r)].append(r)
    print(f"distinct EIN in disclosure : {len(d_ein)}   "
          f"(blank EIN rows: {sum(1 for a in disc if not a.ein)})")
    print(f"distinct EIN in schedule C : {len(s_ein)}   "
          f"(blank EIN rows: {sum(1 for r in sc if not sc_ein(r))})")
    both = set(d_ein) & set(s_ein)
    only_d = set(d_ein) - set(s_ein)
    only_s = set(s_ein) - set(d_ein)
    print(f"in BOTH                    : {len(both)}")
    print(f"disclosure ONLY            : {len(only_d)}   "
          f"{money(sum(a.amount for e in only_d for a in d_ein[e]))} across "
          f"{sum(len(d_ein[e]) for e in only_d)} rows")
    print(f"schedule C ONLY            : {len(only_s)}   "
          f"{money(sum(sc_amount(r) for e in only_s for r in s_ein[e]))} across "
          f"{sum(len(s_ein[e]) for e in only_s)} rows")
    print()
    print("*** schedule C EINs absent from disclosure -- the falsifying direction ***")
    if not only_s:
        print("    none.")
    for e in sorted(only_s,
                    key=lambda e: -sum(sc_amount(r) for r in s_ein[e]))[:40]:
        rs = s_ein[e]
        print(f"    {e}  {len(rs):>3} rows  {money(sum(sc_amount(r) for r in rs)):>12}  "
              f"{rs[0].get('organization','')[:52]!r}")
    print()
    print("    cleared/pending split of the disclosure-only EINs:")
    c = Counter(a.status_norm for e in only_d for a in d_ein[e])
    print(f"      {dict(c)}")

    # --------------------------------------------------- Source vs initiative
    h("3. SOURCE / INITIATIVE VOCABULARY")
    d_src = Counter(a.source for a in disc)
    s_init = Counter(r.get("initiative", "") for r in sc)
    s_cat = Counter(r.get("category", "") for r in sc)
    print(f"disclosure Source values      : {len(d_src)}")
    print(f"schedule C initiative values  : {len(s_init)}  "
          f"(blank on {s_init.get('', 0)} rows)")
    print(f"schedule C category values    : {len(s_cat)}")

    def norm(s):
        s = s.lower().replace("’", "'").replace("&", "and")
        s = "".join(ch for ch in s if ch.isalnum() or ch == " ")
        return " ".join(s.split())

    dn = {norm(k): k for k in d_src if k}
    sn = {norm(k): k for k in s_init if k}
    inter = set(dn) & set(sn)
    print(f"exact-after-normalization overlap: {len(inter)}")
    print()
    print(f"--- disclosure Source with NO schedule C initiative match "
          f"({len(set(dn) - set(sn))}) ---")
    for k in sorted(set(dn) - set(sn), key=lambda k: -d_src[dn[k]]):
        rows = [a for a in disc if a.source == dn[k]]
        print(f"    {d_src[dn[k]]:>5} rows {money(sum(a.amount for a in rows)):>14}  {dn[k]!r}")
    print()
    print(f"--- schedule C initiative with NO disclosure Source match "
          f"({len(set(sn) - set(dn))}) ---")
    for k in sorted(set(sn) - set(dn), key=lambda k: -s_init[sn[k]]):
        rows = [r for r in sc if r.get("initiative") == sn[k]]
        print(f"    {s_init[sn[k]]:>5} rows {money(sum(sc_amount(r) for r in rows)):>14}  "
              f"{sn[k]!r}")

    # ------------------------------------------------------- council members
    h("4. COUNCIL MEMBER")
    d_mem = Counter(a.council_member for a in disc)
    s_mem = Counter(r.get("member", "") for r in sc)
    print(f"disclosure distinct : {len(d_mem)}  (blank on {d_mem.get('', 0)} rows)")
    print(f"schedule C distinct : {len(s_mem)}  (blank on {s_mem.get('', 0)} rows)")
    dm = {m for m in d_mem if m}
    sm = {m for m in s_mem if m}
    print()
    print(f"--- in disclosure, NOT in schedule C ({len(dm - sm)}) ---")
    for m in sorted(dm - sm):
        rows = [a for a in disc if a.council_member == m]
        print(f"    {d_mem[m]:>5} rows {money(sum(a.amount for a in rows)):>14}  {m!r}")
    print()
    print(f"--- in schedule C, NOT in disclosure ({len(sm - dm)}) ---")
    for m in sorted(sm - dm):
        rows = [r for r in sc if r.get("member") == m]
        print(f"    {s_mem[m]:>5} rows {money(sum(sc_amount(r) for r in rows)):>14}  {m!r}")
    print()
    print("--- surnames that collide within this year's disclosure roster ---")
    print("    (a bare surname vs an initial-prefixed one means the Council itself"
          " disambiguated)")
    bysur = defaultdict(list)
    for m in sorted(dm):
        bysur[m.split()[-1]].append(m)
    for sur, ms in sorted(bysur.items()):
        if len(ms) > 1:
            print(f"    {sur}: {ms}")
    print("    schedule C side:")
    bysur2 = defaultdict(list)
    for m in sorted(sm):
        bysur2[m.split()[-1]].append(m)
    for sur, ms in sorted(bysur2.items()):
        if len(ms) > 1:
            print(f"    {sur}: {ms}")

    # ---------------------------------------------------------- exact awards
    h("5. EXACT AWARD MATCH")
    for label, keyfn_d, keyfn_s in (
        ("(EIN, amount)",
         lambda a: (a.ein, round(a.amount, 2)),
         lambda r: (sc_ein(r), round(sc_amount(r), 2))),
        ("(EIN, amount, member)",
         lambda a: (a.ein, round(a.amount, 2), a.council_member),
         lambda r: (sc_ein(r), round(sc_amount(r), 2), (r.get("member") or "").strip())),
    ):
        dc, scc = Counter(), Counter()
        for a in disc:
            if a.ein:
                dc[keyfn_d(a)] += 1
        for r in sc:
            if sc_ein(r):
                scc[keyfn_s(r)] += 1
        matched = sum(min(dc[k], scc[k]) for k in set(dc) & set(scc))
        print(f"  {label}")
        print(f"    distinct keys  disclosure {len(dc):>6}   schedule C {len(scc):>6}"
              f"   shared {len(set(dc) & set(scc)):>6}")
        print(f"    rows matched (multiplicity-aware)      {matched:>6}")
        print(f"    disclosure rows unmatched              "
              f"{sum(dc.values()) - matched:>6}")
        print(f"    schedule C rows unmatched              "
              f"{sum(scc.values()) - matched:>6}")
        if label.endswith("member)"):
            continue
        # cleared/pending on the matched side, for the 2-tuple key only
        mk = set(dc) & set(scc)
        cs = Counter(a.status_norm for a in disc if a.ein and keyfn_d(a) in mk)
        cu = Counter(a.status_norm for a in disc if a.ein and keyfn_d(a) not in mk)
        print(f"    disclosure status on matched keys      {dict(cs)}")
        print(f"    disclosure status on unmatched keys    {dict(cu)}")

    # -------------------------------------------------- individual mismatches
    h("6. SCHEDULE C ROWS WITH NO (EIN, amount) TWIN IN DISCLOSURE -- read one by one")
    dc = Counter((a.ein, round(a.amount, 2)) for a in disc if a.ein)
    left = Counter()
    misses = []
    for r in sc:
        k = (sc_ein(r), round(sc_amount(r), 2))
        if not k[0]:
            continue
        left[k] += 1
        if left[k] > dc.get(k, 0):
            misses.append(r)
    print(f"total such rows: {len(misses)}   {money(sum(sc_amount(r) for r in misses))}")
    print()
    misses.sort(key=lambda r: -sc_amount(r))
    for r in misses[:20]:
        e = sc_ein(r)
        print(f"  schedule C row: {r}")
        peers = d_ein.get(e, [])
        if peers:
            print(f"    disclosure has {len(peers)} row(s) for EIN {e}:")
            for a in peers[:8]:
                print(f"      row {a.source_row:>6} {a.status:<8} {money(a.amount):>12} "
                      f"src={a.source!r} member={a.council_member!r} "
                      f"name={a.legal_name!r}")
            print(f"      disclosure sum for this EIN = "
                  f"{money(sum(a.amount for a in peers))}")
        else:
            print(f"    EIN {e} ABSENT from disclosure entirely")
        print()

    # ---------------------------------------- per-EIN dollar agreement
    h("7. PER-EIN DOLLAR AGREEMENT (EINs present in both)")
    agree = dis = 0
    diffs = []
    for e in both:
        dsum = sum(a.amount for a in d_ein[e])
        ssum = sum(sc_amount(r) for r in s_ein[e])
        if abs(dsum - ssum) < 0.01:
            agree += 1
        else:
            dis += 1
            diffs.append((dsum - ssum, e, dsum, ssum))
    print(f"EINs where the two sources agree to the dollar : {agree}")
    print(f"EINs where they do not                         : {dis}")
    diffs.sort(key=lambda t: -abs(t[0]))
    print()
    print("  largest 15 per-EIN dollar gaps (disclosure - scheduleC):")
    for d, e, ds, ss in diffs[:15]:
        nm = d_ein[e][0].legal_name[:44]
        print(f"    {e}  {money(d):>14}   disc {money(ds):>13} ({len(d_ein[e])} rows)"
              f"   sc {money(ss):>13} ({len(s_ein[e])} rows)  {nm!r}")


if __name__ == "__main__":
    main()
