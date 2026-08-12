#!/usr/bin/env python3
"""Compare the FY2016 Council expense disclosure workbook against parsed Schedule C.

Read-only against data/ and source/. Emits the analysis that backs comparison-2016.md.

Run:  python3 research/phase1-source-comparability/compare_2016.py
      python3 research/phase1-source-comparability/compare_2016.py --section ein

Sections: totals ein source member exact mismatch  (default: all)
"""

import csv
import os
import sys
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "code"))
from parse_expense_disclosure import parse_year  # noqa: E402

XLSX = os.path.join(ROOT, "source", "expense-funding-disclosure",
                    "funded_disclosure_FY2016.xlsx")
SKED = os.path.join(ROOT, "data", "fy16", "schedule_c")


def money(x):
    return f"${x:,.0f}"


def load_disclosure():
    awards, report = parse_year(XLSX)
    return awards, report


def load_schedule_c():
    """awards CSV + the three appendix CSVs. Appendices are header-only for FY2016."""
    rows = []
    with open(os.path.join(SKED, "fy16_schedule_c_awards.csv")) as f:
        for r in csv.DictReader(f):
            r["_file"] = "fy16_schedule_c_awards.csv"
            rows.append(r)
    appendix = {}
    for name in ("fy16_appendix_a_aging.csv", "fy16_appendix_b_local.csv",
                 "fy16_appendix_c_youth.csv"):
        with open(os.path.join(SKED, name)) as f:
            got = list(csv.DictReader(f))
        appendix[name] = got
        for r in got:
            r["_file"] = name
            rows.append(r)
    return rows, appendix


def norm_ein(v):
    """Digits only. Both sides publish 9-digit EINs; disclosure preserves leading zeros."""
    return "".join(ch for ch in (v or "") if ch.isdigit())


def amt(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def section_totals(disc, rep, sked, appendix):
    print("=" * 78)
    print("1. TOTALS")
    print("=" * 78)
    print(f"disclosure   rows_present={rep.n_rows_present} awards={rep.n_awards} "
          f"blank={rep.n_blank} stripped={rep.n_stripped}")
    print(f"disclosure   total {money(rep.total_amount)}   by_status {rep.by_status}")
    cl = [a for a in disc if a.status_norm == "cleared"]
    pd = [a for a in disc if a.status_norm == "pending"]
    print(f"  cleared  n={len(cl):>5}  {money(sum(a.amount for a in cl))}")
    print(f"  pending  n={len(pd):>5}  {money(sum(a.amount for a in pd))}")
    print()
    sked_total = sum(amt(r["amount"]) or 0 for r in sked)
    print(f"schedule C   rows={len(sked)}   total {money(sked_total)}")
    for name, got in appendix.items():
        print(f"  {name:<34} rows={len(got)}")
    print(f"  award_type  {dict(collections.Counter(r.get('award_type', '') for r in sked))}")
    print(f"  member non-blank: {sum(1 for r in sked if (r.get('member') or '').strip())}")
    print(f"  agency non-blank: {sum(1 for r in sked if (r.get('agency') or '').strip())}")
    print(f"  purpose non-blank: {sum(1 for r in sked if (r.get('purpose') or '').strip())}")
    print()
    print(f"DELTA rows   {rep.n_awards - len(sked):>10,}  "
          f"(disclosure {rep.n_awards} - schedule C {len(sked)})")
    print(f"DELTA $      {money(rep.total_amount - sked_total)}  "
          f"({money(rep.total_amount)} - {money(sked_total)})")
    print(f"schedule C captures {100 * sked_total / rep.total_amount:.1f}% of disclosure $, "
          f"{100 * len(sked) / rep.n_awards:.1f}% of rows")


def section_ein(disc, sked):
    print()
    print("=" * 78)
    print("2. EIN, BOTH DIRECTIONS")
    print("=" * 78)
    d_ein = collections.defaultdict(list)
    for a in disc:
        if norm_ein(a.ein):
            d_ein[norm_ein(a.ein)].append(a)
    s_ein = collections.defaultdict(list)
    for r in sked:
        if norm_ein(r.get("ein")):
            s_ein[norm_ein(r["ein"])].append(r)

    print(f"disclosure distinct EINs : {len(d_ein):>6}   "
          f"(rows with no EIN: {sum(1 for a in disc if not norm_ein(a.ein))})")
    print(f"schedule C distinct EINs : {len(s_ein):>6}   "
          f"(rows with no EIN: {sum(1 for r in sked if not norm_ein(r.get('ein')))})")

    both = set(d_ein) & set(s_ein)
    only_d = set(d_ein) - set(s_ein)
    only_s = set(s_ein) - set(d_ein)
    print(f"in BOTH                  : {len(both):>6}")
    print(f"disclosure ONLY          : {len(only_d):>6}")
    print(f"schedule C ONLY          : {len(only_s):>6}   <-- falsifies 'disclosure is a superset'")

    # cleared/pending split of the disclosure-only EINs
    od_cl = sum(1 for e in only_d if any(a.status_norm == "cleared" for a in d_ein[e]))
    od_pd = sum(1 for e in only_d if all(a.status_norm == "pending" for a in d_ein[e]))
    print(f"  disclosure-only EINs with >=1 Cleared row : {od_cl}")
    print(f"  disclosure-only EINs that are all Pending : {od_pd}")

    if only_s:
        print()
        print("--- EVERY schedule-C-only EIN, in full ---")
        for e in sorted(only_s):
            for r in s_ein[e]:
                print(f"  EIN {e}  {money(amt(r['amount']) or 0):>14}  "
                      f"[{r.get('category', '')}] {r.get('initiative', '')}")
                print(f"      org: {r.get('organization', '')!r}")
                print(f"      program: {r.get('program', '')!r}  file: {r['_file']}")
    return d_ein, s_ein, both, only_d, only_s


def section_source(disc, sked):
    print()
    print("=" * 78)
    print("3. SOURCE (disclosure) vs INITIATIVE (schedule C)")
    print("=" * 78)
    d_src = collections.Counter(a.source for a in disc)
    s_init = collections.Counter(r.get("initiative", "") for r in sked)
    print(f"disclosure distinct Source values    : {len(d_src)}")
    print(f"schedule C distinct initiative values: {len(s_init)}")

    d_names = {s.strip().lower(): s for s in d_src}
    s_names = {s.strip().lower(): s for s in s_init}
    shared = set(d_names) & set(s_names)
    print(f"exact-string overlap (casefolded)    : {len(shared)}")
    print()
    print(f"--- schedule C initiatives NOT in disclosure Source ({len(set(s_names) - set(d_names))}) ---")
    for k in sorted(set(s_names) - set(d_names)):
        print(f"  {s_names[k]!r}  ({s_init[s_names[k]]} rows)")
    print()
    print(f"--- disclosure Source NOT in schedule C initiative, top 30 of "
          f"{len(set(d_names) - set(s_names))} ---")
    for k, _ in sorted(((k, d_src[d_names[k]]) for k in set(d_names) - set(s_names)),
                       key=lambda kv: -kv[1])[:30]:
        print(f"  {d_names[k]!r}  ({d_src[d_names[k]]} rows)")
    print()
    print("--- per-initiative $ where the NAME matches exactly ---")
    print(f"{'initiative':<52} {'disclosure $':>14} {'schedC $':>14} {'delta':>14}")
    for k in sorted(shared):
        dv = sum(a.amount for a in disc if a.source.strip().lower() == k)
        sv = sum(amt(r["amount"]) or 0 for r in sked
                 if (r.get("initiative") or "").strip().lower() == k)
        print(f"{d_names[k][:50]:<52} {money(dv):>14} {money(sv):>14} {money(dv - sv):>14}")


def section_member(disc, sked):
    print()
    print("=" * 78)
    print("4. COUNCIL MEMBER  (evidence for issue #51)")
    print("=" * 78)
    s_mem = [(r.get("member") or "").strip() for r in sked]
    print(f"schedule C rows with a non-empty member: {sum(1 for m in s_mem if m)} / {len(s_mem)}")
    d_mem = collections.Counter(a.council_member for a in disc)
    print(f"disclosure distinct Council Member values: {len(d_mem)}")
    print()
    print("--- disclosure surname collisions (the #51 set) ---")
    for surname in ("Williams", "Sanchez", "Rivera", "Barron", "Vallone"):
        hits = sorted(v for v in d_mem if surname.lower() in v.lower())
        print(f"  {surname:<10} {len(hits)} distinct value(s): {hits}")
    print()
    print("--- full disclosure Council Member roster ---")
    for name, n in sorted(d_mem.items()):
        tot = sum(a.amount for a in disc if a.council_member == name)
        print(f"  {name:<34} {n:>5} rows  {money(tot):>14}")


def section_exact(disc, sked):
    print()
    print("=" * 78)
    print("5. EXACT AWARD MATCH")
    print("=" * 78)
    d_pairs = collections.Counter((norm_ein(a.ein), a.amount) for a in disc if norm_ein(a.ein))
    s_pairs = collections.Counter((norm_ein(r["ein"]), amt(r["amount"]))
                                  for r in sked if norm_ein(r.get("ein")))
    inter = set(d_pairs) & set(s_pairs)
    print("(EIN, amount)")
    print(f"  disclosure distinct pairs : {len(d_pairs)}")
    print(f"  schedule C distinct pairs : {len(s_pairs)}")
    print(f"  matched pairs             : {len(inter)}")
    print(f"  schedule C pairs UNMATCHED: {len(set(s_pairs) - set(d_pairs))}")
    print(f"  disclosure pairs unmatched: {len(set(d_pairs) - set(s_pairs))}")
    matched_rows = sum(s_pairs[p] for p in inter)
    print(f"  schedule C ROWS covered by a matched pair: {matched_rows} / {len(sked)}")

    print()
    print("(EIN, amount, member) -- not computable: schedule C member is 100% empty for FY2016")

    print()
    print("--- schedule C (EIN, amount) pairs with NO disclosure counterpart, all of them ---")
    unmatched = sorted(set(s_pairs) - set(d_pairs), key=lambda p: -(p[1] or 0))
    for ein, a in unmatched:
        rows = [r for r in sked if norm_ein(r.get("ein")) == ein and amt(r["amount"]) == a]
        for r in rows:
            print(f"  EIN {ein} {money(a or 0):>14}  {r.get('organization', '')[:46]!r}")
            print(f"      initiative: {r.get('initiative', '')!r}")
            d_same = [x for x in disc if norm_ein(x.ein) == ein]
            if d_same:
                print(f"      same EIN in disclosure: {len(d_same)} row(s), "
                      f"{money(sum(x.amount for x in d_same))} total")
                for x in sorted(d_same, key=lambda x: -x.amount)[:4]:
                    print(f"        - {money(x.amount):>12} {x.status:<8} "
                          f"{x.council_member:<16} {x.source[:36]!r}")
            else:
                print("      same EIN in disclosure: NONE")
    return d_pairs, s_pairs, inter


def section_mismatch(disc, sked, d_ein, s_ein, both):
    print()
    print("=" * 78)
    print("6. MISMATCHES READ INDIVIDUALLY -- EINs in both, amounts disagree")
    print("=" * 78)
    cases = []
    for e in sorted(both):
        dv = sum(a.amount for a in d_ein[e])
        sv = sum(amt(r["amount"]) or 0 for r in s_ein[e])
        if abs(dv - sv) > 0.5:
            cases.append((abs(dv - sv), e, dv, sv))
    cases.sort(reverse=True)
    print(f"EINs present in both sources whose totals differ: {len(cases)} of {len(both)}")
    print()
    for i, (_, e, dv, sv) in enumerate(cases[:14], 1):
        srows = s_ein[e]
        drows = sorted(d_ein[e], key=lambda a: -a.amount)
        print(f"--- CASE {i}  EIN {e} ---")
        print(f"  schedule C total {money(sv)}   disclosure total {money(dv)}   "
              f"delta {money(dv - sv)}")
        print(f"  schedule C rows ({len(srows)}):")
        for r in srows:
            print(f"    {money(amt(r['amount']) or 0):>14}  [{r.get('category', '')}] "
                  f"{r.get('initiative', '')}")
            print(f"        org {r.get('organization', '')!r}")
        print(f"  disclosure rows ({len(drows)}), showing up to 8:")
        for a in drows[:8]:
            print(f"    {money(a.amount):>14}  {a.status:<8} {a.council_member:<16} "
                  f"{a.source[:40]!r}")
            print(f"        org {a.legal_name!r}  row {a.source_row}")
        if len(drows) > 8:
            rest = sum(a.amount for a in drows[8:])
            print(f"    ... {len(drows) - 8} more rows, {money(rest)}")
        print()


def main():
    want = sys.argv[sys.argv.index("--section") + 1] if "--section" in sys.argv else "all"
    disc, rep = load_disclosure()
    sked, appendix = load_schedule_c()

    if want in ("all", "totals"):
        section_totals(disc, rep, sked, appendix)
    d_ein, s_ein, both, only_d, only_s = section_ein(disc, sked) if want in ("all", "ein", "mismatch") \
        else (None, None, None, None, None)
    if want in ("all", "source"):
        section_source(disc, sked)
    if want in ("all", "member"):
        section_member(disc, sked)
    if want in ("all", "exact"):
        section_exact(disc, sked)
    if want in ("all", "mismatch"):
        section_mismatch(disc, sked, d_ein, s_ein, both)


def demo():
    """One runnable check: the two sides load, and the headline gap is real."""
    disc, rep = load_disclosure()
    sked, appendix = load_schedule_c()
    assert rep.n_awards == 7797, rep.n_awards
    assert abs(rep.total_amount - 381376626.0) < 1, rep.total_amount
    assert len(sked) == 335, len(sked)
    assert all(len(v) == 0 for v in appendix.values()), "FY2016 appendices are header-only"
    assert sum(1 for r in sked if (r.get("member") or "").strip()) == 0, \
        "FY2016 schedule C member column is empty"
    # EIN normalization must not collapse distinct orgs
    assert norm_ein("14-1713034") == "141713034"
    assert norm_ein("​452732865") == "452732865"
    print("demo: ok")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        main()
