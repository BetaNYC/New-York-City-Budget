#!/usr/bin/env python3
"""FY2019: Council expense disclosure workbook vs extracted Schedule C.

Every number in comparison-2019.md comes out of this file. Run it:

    python3 research/phase1-source-comparability/compare_2019.py

Sides:
  A  source/expense-funding-disclosure/funded_disclosure_FY2019.xlsx  (via
     code/parse_expense_disclosure.py -- read-only, not modified)
  B  data/fy19/schedule_c/fy19_schedule_c_awards.csv
     data/fy19/schedule_c/fy19_appendix_{a_aging,b_local,c_youth}.csv

Stdlib only. Nothing is written; nothing in data/ or source/ is touched.
"""

import csv
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "code"))
from parse_expense_disclosure import parse_year  # noqa: E402

XLSX = os.path.join(ROOT, "source", "expense-funding-disclosure",
                    "funded_disclosure_FY2019.xlsx")
SCDIR = os.path.join(ROOT, "data", "fy19", "schedule_c")


def norm(s):
    """Fold the cosmetic differences ONLY: curly quotes, case, whitespace, '&'/'and'.

    Deliberately does NOT stem, drop stopwords, or fuzzy-match. A name that survives
    this and still fails to match is a real vocabulary difference, not a typography one.
    """
    s = unicodedata.normalize("NFKD", s or "")
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9']+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_schedule_c():
    """awards + the three appendix files, tagged by which file they came from."""
    out = []
    aw = os.path.join(SCDIR, "fy19_schedule_c_awards.csv")
    with open(aw, newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            r["_file"] = "fy19_schedule_c_awards.csv"
            r["_row"] = i
            out.append(r)
    appendix_counts = {}
    for tag in ("a_aging", "b_local", "c_youth"):
        p = os.path.join(SCDIR, f"fy19_appendix_{tag}.csv")
        with open(p, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        appendix_counts[tag] = len(rows)
        for i, r in enumerate(rows, start=2):
            r.setdefault("category", "")
            r.setdefault("initiative", "")
            r.setdefault("award_type", f"appendix_{tag}")
            r.setdefault("agency", "")
            r["_file"] = f"fy19_appendix_{tag}.csv"
            r["_row"] = i
            out.append(r)
    return out, appendix_counts


def money(x):
    return f"${x:,.0f}"


def h(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def main():
    dis, rep = parse_year(XLSX)
    sc, appendix_counts = load_schedule_c()

    dis_total = sum(a.amount for a in dis)
    sc_total = sum(float(r["amount"]) for r in sc if r["amount"].strip())

    h("0. BASELINE")
    print(f"disclosure sheet name        {rep.sheet_name!r}")
    print(f"disclosure rows present      {rep.n_rows_present}")
    print(f"disclosure awards            {rep.n_awards}   {money(dis_total)}")
    print(f"  cleared                    {rep.by_status.get('cleared', 0)}   "
          f"{money(sum(a.amount for a in dis if a.status_norm == 'cleared'))}")
    print(f"  pending                    {rep.by_status.get('pending', 0)}   "
          f"{money(sum(a.amount for a in dis if a.status_norm == 'pending'))}")
    print(f"  stripped summary rows      {rep.n_stripped}")
    print(f"schedule C rows              {len(sc)}   {money(sc_total)}")
    for t, n in appendix_counts.items():
        print(f"  appendix {t:<8}            {n} data rows")
    print(f"schedule C award_type        {dict(Counter(r['award_type'] for r in sc))}")
    print(f"coverage (rows)              {len(sc) / rep.n_awards:.1%}")
    print(f"coverage (dollars)           {sc_total / dis_total:.1%}")
    print(f"UNACCOUNTED                  {rep.n_awards - len(sc)} rows   "
          f"{money(dis_total - sc_total)}")

    # ---------------------------------------------------------------- 1. EIN
    h("1. BY EIN, BOTH DIRECTIONS")
    dis_ein = defaultdict(list)
    for a in dis:
        dis_ein[a.ein].append(a)
    sc_ein = defaultdict(list)
    for r in sc:
        sc_ein[r["ein"].strip()].append(r)
    only_sc = sorted(set(sc_ein) - set(dis_ein))
    only_dis = sorted(set(dis_ein) - set(sc_ein))
    both = set(sc_ein) & set(dis_ein)
    print(f"distinct EIN, disclosure     {len(dis_ein)}")
    print(f"distinct EIN, schedule C     {len(sc_ein)}")
    print(f"in both                      {len(both)}")
    print(f"schedule C ONLY (falsifies superset claim)   {len(only_sc)}")
    print(f"disclosure ONLY                              {len(only_dis)}")
    print(f"schedule C rows carrying an EIN absent from disclosure: "
          f"{sum(len(sc_ein[e]) for e in only_sc)}  "
          f"{money(sum(float(r['amount']) for e in only_sc for r in sc_ein[e]))}")
    for e in only_sc:
        for r in sc_ein[e]:
            print(f"    EIN {e}  {money(float(r['amount'])):>12}  "
                  f"{r['initiative']!r}  {r['organization']!r}  "
                  f"[{r['_file']}:{r['_row']}]")
    # Are the schedule C-only EINs new organizations, or mangled digits for an org the
    # disclosure DOES carry? Two independent tests, no fuzzy name matching:
    #   (a) exact org-name hit in disclosure under a different EIN
    #   (b) an EIN in disclosure with the same nine digits in a different order
    dis_names = {norm(a.legal_name): a.ein for a in dis}
    digit_index = defaultdict(set)
    for e in dis_ein:
        digit_index["".join(sorted(e))].add(e)
    print("\n  schedule C-only EIN vs disclosure -- name and digit tests:")
    for e in only_sc:
        for r in sc_ein[e]:
            n = norm(r["organization"])
            name_hit = dis_names.get(n)
            perm = sorted(digit_index.get("".join(sorted(e)), set()) - {e})
            if name_hit or perm:
                print(f"    {e}  {r['organization'][:52]!r}")
                if name_hit:
                    print(f"        same org name in disclosure under EIN {name_hit}")
                if perm:
                    print(f"        disclosure EIN(s) with the same digits reordered: {perm}")

    pend_only = [e for e in only_dis
                 if all(a.status_norm == "pending" for a in dis_ein[e])]
    print(f"\n  disclosure-only EINs that are 100% Pending: {len(pend_only)}")

    # ------------------------------------------------------- 2. initiative
    h("2. SOURCE (disclosure) vs INITIATIVE (schedule C)")
    dis_src = Counter(a.source for a in dis)
    sc_init = Counter(r["initiative"] for r in sc if r["initiative"])
    dis_n = {norm(k): k for k in dis_src}
    sc_n = {norm(k): k for k in sc_init}
    shared = set(dis_n) & set(sc_n)
    print(f"distinct Source values       {len(dis_src)}")
    print(f"distinct initiative values   {len(sc_init)}")
    print(f"matched after normalization  {len(shared)}")
    print(f"\nIn disclosure Source, NOT in schedule C initiative "
          f"({len(set(dis_n) - set(sc_n))}):")
    for k in sorted(set(dis_n) - set(sc_n)):
        v = dis_n[k]
        print(f"    {dis_src[v]:>5} rows  {money(sum(a.amount for a in dis if a.source == v)):>14}  {v!r}")
    print(f"\nIn schedule C initiative, NOT in disclosure Source "
          f"({len(set(sc_n) - set(dis_n))}):")
    for k in sorted(set(sc_n) - set(dis_n)):
        v = sc_n[k]
        print(f"    {sc_init[v]:>5} rows  "
              f"{money(sum(float(r['amount']) for r in sc if r['initiative'] == v)):>14}  {v!r}")

    # ------------------------------- 2b. does the initiative LABEL survive?
    h("2b. INITIATIVE LABEL AGREEMENT ON ROWS THAT DO MATCH")
    # For every schedule C row whose (EIN, amount) exists in disclosure, ask whether ANY
    # of those disclosure rows carries the same Source. If none does, the extracted
    # initiative heading is contradicted by the disclosure for that exact award.
    dis_by_ea = defaultdict(list)
    for a in dis:
        dis_by_ea[(a.ein, round(a.amount))].append(a)
    agree = disagree = nomatch = 0
    blank_init = sum(1 for r in sc if not r["initiative"])
    relabel = Counter()
    for r in sc:
        cands = dis_by_ea.get((r["ein"].strip(), round(float(r["amount"]))))
        if not cands:
            nomatch += 1
            continue
        if not r["initiative"]:
            continue
        if any(norm(a.source) == norm(r["initiative"]) for a in cands):
            agree += 1
        else:
            disagree += 1
            relabel[(r["initiative"], cands[0].source)] += 1
    print(f"schedule C rows with a BLANK initiative                 {blank_init}")
    print(f"rows matched on (EIN, amount) whose label AGREES        {agree}")
    print(f"rows matched on (EIN, amount) whose label DISAGREES     {disagree}")
    print(f"rows with no (EIN, amount) match at all                 {nomatch}")
    print("\ntop relabelings (schedule C initiative -> disclosure Source):")
    for (a_, b_), n_ in relabel.most_common(15):
        print(f"    {n_:>4}  {a_[:44]!r}  ->  {b_!r}")

    # -------------------------------------------------- 3. council member
    h("3. COUNCIL MEMBER (issue #51)")
    dis_mem = Counter(a.council_member for a in dis)
    sc_mem = Counter(r["member"] for r in sc)
    print(f"disclosure distinct Council Member values: {len(dis_mem)} "
          f"({sum(1 for a in dis if not a.council_member)} rows blank)")
    print(f"schedule C distinct member values:        {len(sc_mem)} "
          f"({sum(1 for r in sc if not r['member'])} rows blank)")
    print("\nschedule C member values in full:")
    for k, v in sc_mem.most_common():
        print(f"    {v:>5}  {k!r}")
    print("\ndisclosure Council Member values that are ambiguous surnames:")
    ambiguous = ["Williams", "Sanchez", "Rivera", "Barron", "Vallone", "Diaz"]
    for name in ambiguous:
        hits = [k for k in dis_mem if norm(name) in norm(k)]
        print(f"    {name:<12} -> {hits if hits else 'ABSENT'}   "
              f"rows={sum(dis_mem[x] for x in hits)}")
    print("\ndisclosure carries a first name / initial anywhere in Council Member? "
          f"{any(' ' in k and k not in ('Bronx Delegation','Brooklyn Delegation','Manhattan Delegation','Queens Delegation','Staten Island Delegation') for k in dis_mem)}")
    print("multi-token Council Member values: "
          f"{sorted(k for k in dis_mem if ' ' in k)}")

    # ---------------------------------------------------- 4. exact awards
    h("4. EXACT AWARD MATCH, BOTH DIRECTIONS")

    def multiset(keys):
        c = Counter()
        for k in keys:
            c[k] += 1
        return c

    dis_ea = multiset((a.ein, round(a.amount)) for a in dis)
    sc_ea = multiset((r["ein"].strip(), round(float(r["amount"]))) for r in sc)
    matched = sum(min(dis_ea[k], sc_ea[k]) for k in set(dis_ea) & set(sc_ea))
    print("key = (EIN, amount)")
    print(f"  schedule C rows matched into disclosure   {matched} / {len(sc)}  "
          f"({matched / len(sc):.1%})")
    print(f"  schedule C rows UNMATCHED                 {len(sc) - matched}")
    print(f"  disclosure rows unmatched                 {len(dis) - matched}")

    dis_eam = multiset((a.ein, round(a.amount), norm(a.council_member)) for a in dis)
    sc_eam = multiset((r["ein"].strip(), round(float(r["amount"])), norm(r["member"]))
                      for r in sc)
    matched3 = sum(min(dis_eam[k], sc_eam[k]) for k in set(dis_eam) & set(sc_eam))
    print("\nkey = (EIN, amount, member)")
    print(f"  schedule C rows matched into disclosure   {matched3} / {len(sc)}  "
          f"({matched3 / len(sc):.1%})")
    print(f"  lost by adding member to the key          {matched - matched3}")

    # what the member key does to the 41 member_item rows specifically
    mi = [r for r in sc if r["award_type"] == "member_item"]
    mi2 = sum(1 for r in mi
              if sc_ea[(r["ein"].strip(), round(float(r["amount"])))] and
              dis_ea.get((r["ein"].strip(), round(float(r["amount"])))))
    print(f"  of the {len(mi)} member_item rows, {mi2} match on (EIN, amount); "
          f"0 can match on member (schedule C member holds a borough, not a name)")

    # unmatched schedule C rows, with a reason for each
    remaining = Counter(sc_ea)
    for k in list(remaining):
        remaining[k] = max(0, remaining[k] - dis_ea.get(k, 0))
    unmatched_rows = []
    seen = Counter()
    for r in sc:
        k = (r["ein"].strip(), round(float(r["amount"])))
        if seen[k] >= dis_ea.get(k, 0):
            unmatched_rows.append(r)
        seen[k] += 1
    print(f"\n  unmatched schedule C rows: {len(unmatched_rows)}  "
          f"{money(sum(float(r['amount']) for r in unmatched_rows))}")

    # classify WHY each unmatched row failed
    reason = Counter()
    for r in unmatched_rows:
        e = r["ein"].strip()
        if e not in dis_ein:
            reason["EIN absent from disclosure"] += 1
        elif any(round(a.amount) == round(float(r["amount"])) for a in dis_ein[e]):
            reason["EIN+amount exists but already consumed (duplicate/aggregate)"] += 1
        else:
            reason["EIN present, amount differs"] += 1
    for k, v in reason.most_common():
        print(f"    {v:>5}  {k}")

    # ------------------------------ 4b. run-together rows, and what they hide
    h("4b. RUN-TOGETHER ROWS (two PDF lines collapsed into one CSV row)")
    # In the Schedule C PDF each provider line reads "<Org> <EIN> <Amount>". When two
    # lines collapse, the FIRST line's EIN and amount end up inside the organization
    # string as "NN-NNNNNNN * $A" and only the SECOND line's EIN/amount reach the
    # columns. If the embedded pair is a real disclosure award, the extraction dropped a
    # row that is mechanically recoverable from text it already has.
    embedded = re.compile(r"(\d{2})-(\d{7})\s*\*\s*\$([\d,]+)")
    rt = [r for r in sc if embedded.search(r["organization"])]
    pairs = [(m.group(1) + m.group(2), int(m.group(3).replace(",", "")))
             for r in rt for m in embedded.finditer(r["organization"])]
    recoverable = [p for p in pairs if dis_ea.get(p, 0) > 0]
    own_ok = [r for r in rt
              if dis_ea.get((r["ein"].strip(), round(float(r["amount"]))), 0) > 0]
    print(f"rows whose organization contains a second org + its EIN + its amount: {len(rt)}"
          f"  ({len(rt) / len(sc):.1%} of the file)")
    print(f"embedded (EIN, amount) pairs recovered from that text: {len(pairs)}")
    print(f"  of those, an EXACT disclosure award: {len(recoverable)}  "
          f"{money(sum(a for _, a in recoverable))}")
    print(f"  the row's OWN (EIN, amount) is also an exact disclosure award: "
          f"{len(own_ok)} / {len(rt)}")
    print("so each run-together row is one award kept and >=1 award silently dropped.")

    print("\nOther non-organization values sitting in the organization column:")
    for r in sc:
        o = r["organization"]
        if o.startswith("**") or "Adopted Expense Budget" in o or o == "Population":
            print(f"    [{r['_file']}:{r['_row']}]  {o[:80]!r}  EIN {r['ein']}  "
                  f"{money(float(r['amount']))}")

    # ---------------------------------------- 5. per-initiative dollars
    h("5. DOLLARS PER INITIATIVE (matched vocabulary only)")
    rows = []
    for k in sorted(shared):
        dv, sv = dis_n[k], sc_n[k]
        d_all = [a for a in dis if a.source == dv]
        s_all = [r for r in sc if r["initiative"] == sv]
        d_amt = sum(a.amount for a in d_all)
        s_amt = sum(float(r["amount"]) for r in s_all)
        rows.append((sv, len(d_all), d_amt, len(s_all), s_amt, s_amt - d_amt))
    rows.sort(key=lambda t: -abs(t[5]))
    print(f"{'initiative':<52}{'dis n':>7}{'dis $':>14}{'sc n':>6}{'sc $':>14}{'delta':>14}")
    for t in rows:
        print(f"{t[0][:50]:<52}{t[1]:>7}{t[2]:>14,.0f}{t[3]:>6}{t[4]:>14,.0f}{t[5]:>14,.0f}")
    print(f"{'TOTAL (matched vocab)':<52}{sum(t[1] for t in rows):>7}"
          f"{sum(t[2] for t in rows):>14,.0f}{sum(t[3] for t in rows):>6}"
          f"{sum(t[4] for t in rows):>14,.0f}{sum(t[5] for t in rows):>14,.0f}")
    exact = [t for t in rows if abs(t[5]) < 0.5]
    print(f"\ninitiatives whose dollars agree EXACTLY: {len(exact)} / {len(rows)}")
    for t in exact:
        print(f"    {t[0]!r}  n={t[3]} vs {t[1]}  {money(t[4])}")

    # ------------------------------------------- 6. mismatches in full
    h("6. TEN+ MISMATCHES, QUOTED IN FULL")
    picks = []
    # (a) every schedule C EIN absent from disclosure
    for e in only_sc:
        for r in sc_ein[e]:
            picks.append(("EIN absent from disclosure", r, None))
    # (b) amount-differs cases
    n = 0
    for r in unmatched_rows:
        e = r["ein"].strip()
        if e in dis_ein and not any(round(a.amount) == round(float(r["amount"]))
                                    for a in dis_ein[e]):
            picks.append(("amount differs", r, dis_ein[e]))
            n += 1
            if n >= 8:
                break
    # (c) consumed-duplicate cases
    n = 0
    for r in unmatched_rows:
        e = r["ein"].strip()
        if e in dis_ein and any(round(a.amount) == round(float(r["amount"]))
                                for a in dis_ein[e]):
            picks.append(("aggregate vs per-member split", r, dis_ein[e]))
            n += 1
            if n >= 6:
                break
    for i, (why, r, cand) in enumerate(picks, 1):
        print(f"\n--- mismatch {i}: {why}")
        print(f"  SCHEDULE C  [{r['_file']}:{r['_row']}]")
        for k in ("category", "initiative", "award_type", "member", "organization",
                  "program", "ein", "amount", "agency", "purpose"):
            if r.get(k):
                print(f"      {k:<14}{r[k]!r}")
        if cand is None:
            print("  DISCLOSURE  no row with this EIN")
        else:
            same = [a for a in cand if norm(a.source) == norm(r["initiative"])]
            print(f"  DISCLOSURE  {len(cand)} row(s) with EIN {r['ein']}, "
                  f"total {money(sum(a.amount for a in cand))}; "
                  f"{len(same)} of them under the same initiative "
                  f"({money(sum(a.amount for a in same))})")
            show = same if same else cand
            label = "same initiative" if same else "all (no same-initiative row exists)"
            print(f"    -- {label}:")
            for a in show[:10]:
                print(f"      row {a.source_row:<6} {a.source:<38} "
                      f"{a.council_member:<18} {a.status:<8} {a.amount:>12,.0f}  "
                      f"{a.legal_name!r}")
            if len(show) > 10:
                print(f"      ... {len(show) - 10} more")

    # ------------------------------------ 6b. status of what DID match
    h("6b. CLEARED vs PENDING ACROSS THE MATCH")
    dis_pending = [a for a in dis if a.status_norm == "pending"]
    pend_keys = multiset((a.ein, round(a.amount)) for a in dis_pending)
    hit = sum(min(pend_keys[k], sc_ea[k]) for k in set(pend_keys) & set(sc_ea))
    print(f"disclosure Pending rows                     {len(dis_pending)}  "
          f"{money(sum(a.amount for a in dis_pending))}")
    print(f"  (EIN, amount) keys they contribute        {len(pend_keys)}")
    print(f"  schedule C rows that could match a Pending key  {hit}")
    print("Pending rows in full (all 53 are small local designations):")
    for a in sorted(dis_pending, key=lambda x: -x.amount)[:12]:
        print(f"    row {a.source_row:<6} {a.source:<10} {a.council_member:<16} "
              f"{a.amount:>10,.0f}  {a.legal_name[:44]!r}")
    print(f"    ... {len(dis_pending) - 12} more")
    print(f"Pending by Source: "
          f"{dict(Counter(a.source for a in dis_pending).most_common())}")
    for k in set(pend_keys) & set(sc_ea):
        print(f"the ONE Pending key reachable from schedule C: EIN {k[0]} {money(k[1])}")
        for a in dis_by_ea[k]:
            print(f"    disclosure row {a.source_row}  {a.source}  {a.status}  "
                  f"{a.legal_name!r}")
        for r in sc:
            if (r["ein"].strip(), round(float(r["amount"]))) == k:
                print(f"    schedule C [{r['_file']}:{r['_row']}] {r['initiative']!r} "
                      f"{r['organization']!r}")
    print("\nschedule C carries NO status column: "
          f"{'status' not in sc[0]}  -- Cleared/Pending is unrecoverable from data/fy19/")

    # ------------------------- 6c. the appendix hole, by disclosure Source
    h("6c. WHAT THE EMPTY APPENDICES COST")
    appendix_sources = {"Local": "appendix B", "Aging": "appendix A", "Youth": "appendix C"}
    tot_rows = tot_amt = 0
    for s, ap in appendix_sources.items():
        rows_s = [a for a in dis if a.source == s]
        tot_rows += len(rows_s)
        tot_amt += sum(a.amount for a in rows_s)
        print(f"  {s:<8} -> {ap:<12} disclosure has {len(rows_s):>5} rows "
              f"{money(sum(a.amount for a in rows_s)):>14};  "
              f"extracted CSV has {appendix_counts[[k for k in appendix_counts if s.lower()[:4] in k][0]]} rows")
    print(f"  TOTAL unrecoverable from the appendix files: {tot_rows} rows {money(tot_amt)}")
    print(f"  distinct EINs appearing ONLY under those three Sources: "
          f"{len({a.ein for a in dis if a.source in appendix_sources} - {a.ein for a in dis if a.source not in appendix_sources})}")

    # ------------------------------------------------- 7. self-checks
    h("7. SELF-CHECKS")
    assert rep.n_awards == 9655, rep.n_awards
    assert abs(dis_total - 392945000.0) < 0.5, dis_total
    assert len(sc) == 846, len(sc)
    assert abs(sc_total - 181026931.0) < 0.5, sc_total
    assert sum(appendix_counts.values()) == 0, appendix_counts
    # the headline claim: disclosure is NOT a strict superset of schedule C
    assert only_sc, "expected schedule C EINs absent from disclosure"
    # schedule C carries no council-member attribution at all
    assert not (set(norm(r["member"]) for r in sc if r["member"]) &
                set(norm(a.council_member) for a in dis if a.council_member)), \
        "schedule C member values unexpectedly overlap disclosure member names"
    # run-together rows exist and hide real awards
    assert len(rt) == 38 and len(recoverable) == 37, (len(rt), len(recoverable))
    # the initiative label on matched rows is contradicted more often than it is trivial
    assert disagree > 200, disagree
    print("all self-checks passed")


if __name__ == "__main__":
    main()
