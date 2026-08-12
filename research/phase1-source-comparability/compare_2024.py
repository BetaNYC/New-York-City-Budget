#!/usr/bin/env python3
"""Compare the Council's FY2024 expense disclosure workbook against this repo's parsed
Schedule C for FY2024 (awards CSV + the three appendix CSVs).

Read-only. Touches nothing under data/ or source/. Prints; writes no files.
Run:  python3 research/phase1-source-comparability/compare_2024.py [section]
"""

import csv
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "code"))
from parse_expense_disclosure import parse_year  # noqa: E402

XLSX = os.path.join(ROOT, "source", "expense-funding-disclosure",
                    "funded_disclosure_FY2024.xlsx")
SC_DIR = os.path.join(ROOT, "data", "fy24", "schedule_c")

APPENDIX = {                       # file -> the disclosure Source it should correspond to
    "fy24_appendix_a_aging.csv": "Aging",
    "fy24_appendix_b_local.csv": "Local",
    "fy24_appendix_c_youth.csv": "Youth",
}


def load_schedule_c():
    """Every parsed FY24 Schedule C row, normalized to one shape.

    ponytail: a dict per row, not a class. Nothing here outlives the script.
    """
    rows = []
    p = os.path.join(SC_DIR, "fy24_schedule_c_awards.csv")
    for i, r in enumerate(csv.DictReader(open(p)), start=2):
        rows.append({
            "file": "awards", "line": i,
            "member": r["member"].strip(), "org": r["organization"].strip(),
            "ein": r["ein"].strip(), "amount": float(r["amount"]),
            "bucket": r["initiative"].strip() or r["category"].strip(),
            "category": r["category"].strip(), "initiative": r["initiative"].strip(),
            "award_type": r["award_type"].strip(), "program": r.get("program", "").strip(),
        })
    for fn, src in APPENDIX.items():
        for i, r in enumerate(csv.DictReader(open(os.path.join(SC_DIR, fn))), start=2):
            rows.append({
                "file": fn.replace("fy24_appendix_", "").replace(".csv", ""), "line": i,
                "member": r["member"].strip(), "org": r["organization"].strip(),
                "ein": r["ein"].strip(), "amount": float(r["amount"]),
                "bucket": src, "category": "", "initiative": "",
                "award_type": "appendix", "program": r.get("program", "").strip(),
            })
    return rows


def load_disclosure():
    aw, rep = parse_year(XLSX)
    return aw, rep


def multiset_diff(a_keys, b_keys):
    """Counter difference both ways. Multiset, because duplicate (ein, amount) pairs are
    real data, not noise -- collapsing to sets would hide split designations."""
    ca, cb = Counter(a_keys), Counter(b_keys)
    return ca - cb, cb - ca


def money(x):
    return f"${x:,.0f}"


# --------------------------------------------------------------------------- sections

def s_totals(dis, sc):
    print("== 1. HEADLINE COUNTS AND DOLLARS ==\n")
    dcl = [a for a in dis if a.status_norm == "cleared"]
    dpn = [a for a in dis if a.status_norm == "pending"]
    print(f"disclosure rows            {len(dis):>7}   {money(sum(a.amount for a in dis))}")
    print(f"  Cleared                  {len(dcl):>7}   {money(sum(a.amount for a in dcl))}")
    print(f"  Pending                  {len(dpn):>7}   {money(sum(a.amount for a in dpn))}")
    print()
    for f in ("awards", "a_aging", "b_local", "c_youth"):
        sub = [r for r in sc if r["file"] == f]
        print(f"schedule C {f:<15} {len(sub):>7}   {money(sum(r['amount'] for r in sub))}")
    print(f"schedule C TOTAL           {len(sc):>7}   {money(sum(r['amount'] for r in sc))}")
    print()
    print(f"row delta   disclosure - scheduleC = {len(dis) - len(sc):+}")
    print(f"$   delta   disclosure - scheduleC = "
          f"{sum(a.amount for a in dis) - sum(r['amount'] for r in sc):+,.0f}")


def s_appendix_alignment(dis, sc):
    print("\n== 2. APPENDIX <-> disclosure Source, the three named streams ==\n")
    print(f"{'stream':<10}{'disclosure n':>14}{'appendix n':>12}{'disc $':>16}{'appx $':>16}"
          f"{'$ delta':>12}")
    for fn, src in APPENDIX.items():
        d = [a for a in dis if a.source == src]
        s = [r for r in sc if r["file"] == fn.replace("fy24_appendix_", "").replace(".csv", "")]
        ds, ss = sum(a.amount for a in d), sum(r["amount"] for r in s)
        print(f"{src:<10}{len(d):>14}{len(s):>12}{ds:>16,.0f}{ss:>16,.0f}{ds - ss:>12,.0f}")
    print()
    for fn, src in APPENDIX.items():
        d = [a for a in dis if a.source == src]
        st = Counter(a.status_norm for a in d)
        print(f"  {src}: disclosure status {dict(st)}")


def s_ein_both_directions(dis, sc):
    print("\n== 3. EIN COVERAGE, BOTH DIRECTIONS ==\n")
    de = {a.ein for a in dis}
    se = {r["ein"] for r in sc}
    print(f"distinct EIN in disclosure  {len(de)}")
    print(f"distinct EIN in schedule C  {len(se)}")
    print(f"intersection                {len(de & se)}")
    print(f"disclosure-only             {len(de - se)}")
    print(f"SCHEDULE C-ONLY             {len(se - de)}   <-- falsifies 'disclosure is a superset'")
    print()

    sc_only = se - de
    by_ein = defaultdict(list)
    for r in sc:
        if r["ein"] in sc_only:
            by_ein[r["ein"]].append(r)
    tot = sum(r["amount"] for v in by_ein.values() for r in v)
    print(f"Schedule C-only EINs cover {sum(len(v) for v in by_ein.values())} rows, {money(tot)}")
    print(f"  by file: {dict(Counter(r['file'] for v in by_ein.values() for r in v))}")
    print("\n  every Schedule C-only EIN (ein | rows | $ | file:line | org | member):")
    for ein in sorted(by_ein, key=lambda e: -sum(r["amount"] for r in by_ein[e])):
        v = by_ein[ein]
        print(f"    {ein}  {len(v):>2} rows  {money(sum(r['amount'] for r in v)):>12}")
        for r in v:
            print(f"        {r['file']}:{r['line']:<5} {money(r['amount']):>10}  "
                  f"member={r['member']!r}  bucket={r['bucket']!r}")
            print(f"          org={r['org']!r}")

    print(f"\n  disclosure-only EINs: {len(de - se)}")
    d_by = defaultdict(list)
    for a in dis:
        if a.ein in (de - se):
            d_by[a.ein].append(a)
    print(f"    covering {sum(len(v) for v in d_by.values())} rows, "
          f"{money(sum(a.amount for v in d_by.values() for a in v))}")
    print(f"    status: {Counter(a.status_norm for v in d_by.values() for a in v)}")
    print(f"    top Sources: {Counter(a.source for v in d_by.values() for a in v).most_common(10)}")


def s_source_vocab(dis, sc):
    print("\n== 4. SOURCE VOCABULARY vs INITIATIVE VOCABULARY ==\n")
    dsrc = Counter(a.source for a in dis)
    sini = Counter(r["initiative"] for r in sc if r["initiative"])
    scat = Counter(r["category"] for r in sc if r["category"])
    print(f"disclosure distinct Source      {len(dsrc)}")
    print(f"schedule C distinct initiative  {len(sini)}  (+ {len(scat)} categories)")
    print()

    dset, iset = set(dsrc), set(sini)
    exact = dset & iset
    print(f"exact string matches Source <-> initiative: {len(exact)}")
    print(f"Source values with NO exact initiative match: {len(dset - iset)}")
    print(f"initiative values with NO exact Source match: {len(iset - dset)}")
    print("\n  initiative present in Schedule C, absent from disclosure Source:")
    for k in sorted(iset - dset):
        print(f"    {sini[k]:>5} rows  {k!r}")
    print("\n  Source present in disclosure, absent from Schedule C initiative "
          "(top 40 by row count):")
    for k, n in sorted(((k, dsrc[k]) for k in dset - iset), key=lambda t: -t[1])[:40]:
        d = [a for a in dis if a.source == k]
        print(f"    {n:>5} rows  {money(sum(a.amount for a in d)):>14}  {k!r}")
    print(f"    ... {max(0, len(dset - iset) - 40)} more")


def s_members(dis, sc):
    print("\n== 5. COUNCIL MEMBER COLUMNS ==\n")
    dm = Counter(a.council_member for a in dis)
    sm = Counter(r["member"] for r in sc)
    print(f"distinct disclosure Council Member  {len(dm)}")
    print(f"distinct schedule C member          {len(sm)}")
    print()
    print("  in SCHEDULE C but not in disclosure:")
    for k in sorted(set(sm) - set(dm)):
        print(f"    {sm[k]:>5} rows  {k!r}")
    print("\n  in DISCLOSURE but not in Schedule C:")
    for k in sorted(set(dm) - set(sm)):
        print(f"    {dm[k]:>5} rows  {k!r}")
    print("\n  surname-collision check -- does either side carry a first name/district?")
    for name in ("Williams", "Sanchez", "Rivera", "Barron", "Vallone"):
        d = [a for a in dis if name.lower() in a.council_member.lower()]
        s = [r for r in sc if name.lower() in r["member"].lower()]
        print(f"    {name:<10} disclosure values={sorted({a.council_member for a in d})} "
              f"n={len(d)} | scheduleC values={sorted({r['member'] for r in s})} n={len(s)}")


def s_exact_awards(dis, sc):
    print("\n== 6. EXACT AWARD MATCHING, BOTH DIRECTIONS ==\n")
    for label, dkey, skey in (
        ("(EIN, amount)",
         lambda a: (a.ein, a.amount),
         lambda r: (r["ein"], r["amount"])),
        ("(EIN, amount, member)",
         lambda a: (a.ein, a.amount, a.council_member.lower()),
         lambda r: (r["ein"], r["amount"], r["member"].lower())),
    ):
        d_only, s_only = multiset_diff([dkey(a) for a in dis], [skey(r) for r in sc])
        matched_d = len(dis) - sum(d_only.values())
        matched_s = len(sc) - sum(s_only.values())
        print(f"  key {label}")
        print(f"    disclosure rows matched   {matched_d:>6} / {len(dis)}  "
              f"({100 * matched_d / len(dis):.1f}%)")
        print(f"    schedule C rows matched   {matched_s:>6} / {len(sc)}  "
              f"({100 * matched_s / len(sc):.1f}%)")
        print(f"    unmatched disclosure      {sum(d_only.values()):>6}")
        print(f"    unmatched schedule C      {sum(s_only.values()):>6}")
        print()

    # same, restricted to the three appendix streams, where a 1:1 correspondence is claimed
    print("  restricted to the Local/Youth/Aging streams only:")
    d3 = [a for a in dis if a.source in set(APPENDIX.values())]
    s3 = [r for r in sc if r["award_type"] == "appendix"]
    for label, dkey, skey in (
        ("(EIN, amount)", lambda a: (a.ein, a.amount), lambda r: (r["ein"], r["amount"])),
        ("(EIN, amount, member)",
         lambda a: (a.ein, a.amount, a.council_member.lower()),
         lambda r: (r["ein"], r["amount"], r["member"].lower())),
        ("(stream, EIN, amount, member)",
         lambda a: (a.source, a.ein, a.amount, a.council_member.lower()),
         lambda r: (r["bucket"], r["ein"], r["amount"], r["member"].lower())),
    ):
        d_only, s_only = multiset_diff([dkey(a) for a in d3], [skey(r) for r in s3])
        print(f"    {label:<32} disc unmatched {sum(d_only.values()):>5}/{len(d3)}   "
              f"sc unmatched {sum(s_only.values()):>5}/{len(s3)}")


def s_mismatch_readout(dis, sc):
    """The individually-read mismatches. Local stream only: it is the one place both sides
    claim to describe the same universe with the same total, so a difference there is a
    real representational difference and not a scope difference."""
    print("\n== 7. INDIVIDUAL MISMATCHES, LOCAL STREAM, READ ONE BY ONE ==\n")
    d = [a for a in dis if a.source == "Local"]
    s = [r for r in sc if r["file"] == "b_local"]

    dk = Counter((a.ein, a.amount, a.council_member.lower()) for a in d)
    sk = Counter((r["ein"], r["amount"], r["member"].lower()) for r in s)
    d_only, s_only = dk - sk, sk - dk
    print(f"Local: disclosure {len(d)} rows / appendix B {len(s)} rows; "
          f"unmatched on (EIN, amount, member): disclosure {sum(d_only.values())}, "
          f"appendix {sum(s_only.values())}")

    # A designation the disclosure splits but the PDF prints once, or vice versa: same
    # (ein, member) on both sides but a different number of rows.
    d_pair = defaultdict(list)
    for a in d:
        d_pair[(a.ein, a.council_member.lower())].append(a)
    s_pair = defaultdict(list)
    for r in s:
        s_pair[(r["ein"], r["member"].lower())].append(r)

    split = [k for k in set(d_pair) & set(s_pair) if len(d_pair[k]) != len(s_pair[k])]
    print(f"\n(EIN, member) pairs present on BOTH sides with a DIFFERENT row count: {len(split)}")
    for k in sorted(split, key=lambda k: -abs(len(d_pair[k]) - len(s_pair[k])))[:14]:
        ein, mem = k
        ds, ss = d_pair[k], s_pair[k]
        print(f"\n  --- EIN {ein}  member {mem!r}   disclosure {len(ds)} row(s) "
              f"{money(sum(a.amount for a in ds))}  |  appendix B {len(ss)} row(s) "
              f"{money(sum(r['amount'] for r in ss))}")
        for a in ds:
            print(f"      DISC  xlsx-row {a.source_row:<6} {money(a.amount):>10}  "
                  f"{a.status:<8} {a.legal_name!r}")
            print(f"            program={a.program_name!r}")
        for r in ss:
            print(f"      SC    b_local:{r['line']:<5} {money(r['amount']):>10}  "
                  f"{r['org']!r}")
            print(f"            program={r['program']!r}")

    # Amount-only disagreements: same EIN + member on both sides, amounts that do not line up.
    print("\n\n(EIN, member) pairs on both sides whose TOTAL DOLLARS disagree:")
    diff = [(k, sum(a.amount for a in d_pair[k]), sum(r["amount"] for r in s_pair[k]))
            for k in set(d_pair) & set(s_pair)]
    diff = [t for t in diff if abs(t[1] - t[2]) > 0.005]
    print(f"  count: {len(diff)}")
    for (ein, mem), dv, sv in sorted(diff, key=lambda t: -abs(t[1] - t[2]))[:12]:
        print(f"\n  --- EIN {ein}  member {mem!r}   disclosure {money(dv)}  appendix B "
              f"{money(sv)}   delta {dv - sv:+,.0f}")
        for a in d_pair[(ein, mem)]:
            print(f"      DISC  xlsx-row {a.source_row:<6} {money(a.amount):>10}  "
                  f"{a.status:<8} {a.legal_name!r}  prog={a.program_name!r}")
        for r in s_pair[(ein, mem)]:
            print(f"      SC    b_local:{r['line']:<5} {money(r['amount']):>10}  "
                  f"{r['org']!r}  prog={r['program']!r}")


def s_bard(dis, sc):
    print("\n== 8. CANONICAL CASE: Bard College EIN 141713034 ==\n")
    for a in dis:
        if a.ein == "141713034":
            print(f"  DISC xlsx-row {a.source_row:<6} {money(a.amount):>10} {a.status:<8} "
                  f"src={a.source!r} member={a.council_member!r} name={a.legal_name!r}")
    for r in sc:
        if r["ein"] == "141713034":
            print(f"  SC   {r['file']}:{r['line']:<5} {money(r['amount']):>10} "
                  f"member={r['member']!r} bucket={r['bucket']!r} org={r['org']!r}")


def s_dollars_by_bucket(dis, sc):
    print("\n== 9. DOLLARS BY BUCKET, TOP DISAGREEMENTS ==\n")
    dsum = defaultdict(float)
    dn = Counter()
    for a in dis:
        dsum[a.source] += a.amount
        dn[a.source] += 1
    ssum = defaultdict(float)
    sn = Counter()
    for r in sc:
        ssum[r["bucket"]] += r["amount"]
        sn[r["bucket"]] += 1
    keys = set(dsum) & set(ssum)
    print(f"{'bucket (exact name match both sides)':<58}{'disc n':>8}{'sc n':>7}"
          f"{'disc $':>15}{'sc $':>15}{'delta':>14}")
    rows = sorted(keys, key=lambda k: -abs(dsum[k] - ssum[k]))
    for k in rows:
        print(f"{k[:56]:<58}{dn[k]:>8}{sn[k]:>7}{dsum[k]:>15,.0f}{ssum[k]:>15,.0f}"
              f"{dsum[k] - ssum[k]:>14,.0f}")
    agree = [k for k in keys if abs(dsum[k] - ssum[k]) < 0.005]
    print(f"\nbuckets whose dollars agree EXACTLY on both sides: {len(agree)} of {len(keys)}")
    print(f"  {sorted(agree)}")


SECTIONS = {
    "totals": s_totals, "appendix": s_appendix_alignment, "ein": s_ein_both_directions,
    "source": s_source_vocab, "members": s_members, "exact": s_exact_awards,
    "mismatch": s_mismatch_readout, "bard": s_bard, "bucket": s_dollars_by_bucket,
}


def main():
    dis, rep = load_disclosure()
    sc = load_schedule_c()
    want = sys.argv[1:] or list(SECTIONS)
    for name in want:
        SECTIONS[name](dis, sc)
        print()


if __name__ == "__main__":
    main()
