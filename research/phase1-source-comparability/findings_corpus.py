#!/usr/bin/env python3
"""Corpus-wide reproducer for FINDINGS.md. Every table in that document comes from here.

    python3 research/phase1-source-comparability/findings_corpus.py

The per-year reports (comparison-20NN.md) each dig into one fiscal year. This does the one
thing none of them can: put all thirteen years on the same axes, so the shape of the gap is
visible instead of the depth of any single year's hole.

Reads only. Writes nothing. Standard library only. Asserts its own headline claims in demo().
"""

import csv
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_expense_disclosure import parse_year          # noqa: E402
from compare_year import load_schedule_c, norm_ein, cents  # noqa: E402

YEARS = list(range(2015, 2028))

# The three per-member formula streams. In the disclosure these are `Source` values; in the
# Schedule C extraction they are the three appendix files. Same money, different container --
# which is exactly why the gap has to be decomposed along this line and not measured in bulk.
STREAMS = {"local", "youth", "aging"}


def stream_of(source):
    s = (source or "").strip().lower()
    return s if s in STREAMS else ""


def year_row(fy):
    disc, rep = parse_year(os.path.join(
        ROOT, "source", "expense-funding-disclosure", f"funded_disclosure_FY{fy}.xlsx"))
    awards, appendix = load_schedule_c(fy)
    sched = awards + appendix

    d_stream = [a for a in disc if stream_of(a.source)]
    d_body = [a for a in disc if not stream_of(a.source)]

    d_pair = Counter((norm_ein(a.ein), cents(a.amount)) for a in disc)
    s_pair = Counter((norm_ein(r["ein"]), cents(r["amount"])) for r in sched)
    matched = sum((d_pair & s_pair).values())

    # Which DISCLOSURE rows are unreachable from Schedule C, and which stream do they sit in?
    # Row-count subtraction (disc_body - awards) would answer this only if the two sides
    # partitioned identically, and they do not -- so consume the multiset instead.
    budget = +(d_pair - s_pair)          # unmatched disclosure rows, per (EIN, amount) key
    miss_stream = miss_body = 0
    miss_stream_amt = miss_body_amt = miss_pending = 0
    for a in disc:
        k = (norm_ein(a.ein), cents(a.amount))
        if budget.get(k, 0) <= 0:
            continue
        budget[k] -= 1
        if stream_of(a.source):
            miss_stream += 1
            miss_stream_amt += cents(a.amount)
        else:
            miss_body += 1
            miss_body_amt += cents(a.amount)
        if a.status_norm == "pending":
            miss_pending += 1

    d_ein, s_ein = {norm_ein(a.ein) for a in disc}, {norm_ein(r["ein"]) for r in sched}
    orphan_ein = s_ein - d_ein
    orphan_rows = [r for r in sched if norm_ein(r["ein"]) in orphan_ein]

    def blank(rows, get):
        return sum(1 for r in rows if not (get(r) or "").strip())

    return dict(
        fy=fy, sheet=rep.sheet_name,
        d_rows=len(disc), d_amt=sum(cents(a.amount) for a in disc),
        d_stream_rows=len(d_stream), d_stream_amt=sum(cents(a.amount) for a in d_stream),
        d_body_rows=len(d_body), d_body_amt=sum(cents(a.amount) for a in d_body),
        a_rows=len(awards), a_amt=sum(cents(r["amount"]) for r in awards),
        x_rows=len(appendix), x_amt=sum(cents(r["amount"]) for r in appendix),
        matched=matched, s_rows=len(sched),
        miss_stream=miss_stream, miss_stream_amt=miss_stream_amt,
        miss_body=miss_body, miss_body_amt=miss_body_amt, miss_pending=miss_pending,
        orphan_ein=len(orphan_ein), orphan_rows=len(orphan_rows),
        orphan_amt=sum(cents(r["amount"]) for r in orphan_rows),
        d_member_blank=blank(disc, lambda a: a.council_member),
        s_member_blank=blank(sched, lambda r: r.get("member", "")),
        d_members=len({(a.council_member or "").strip().lower() for a in disc}),
        s_members=len({(r.get("member", "") or "").strip().lower() for r in sched}),
    )


def initiatives_total(fy):
    """The Schedule C PDF's own printed initiative totals, as extracted. This stream is the
    one the repo reconciles against printed figures, and it names NO per-member stream (no
    Local / Youth / Aging line), so it is directly comparable to the awards CSV alone."""
    yy = f"{fy % 100:02d}"
    p = os.path.join(ROOT, "data", f"fy{yy}", "schedule_c",
                     f"fy{yy}_schedule_c_initiatives.csv")
    rows = list(csv.DictReader(open(p, newline="")))
    assert not any(re.fullmatch(r"(local|youth|aging)\s*(initiatives|discretionary)?",
                                (r["initiative"] or "").strip(), re.I) for r in rows), fy
    return len(rows), sum(cents(r["amount"]) for r in rows)


def m(c):
    return f"${c / 100:,.0f}"


def main():
    rows = [year_row(fy) for fy in YEARS]

    print("\n== CAPTURE, ROWS AND DOLLARS "
          "(pre-1.4.0 = awards CSV only; post = awards + appendix) ==")
    print(f"{'FY':<5}{'disc rows':>10}{'awards':>9}{'+apx':>9}{'pre %':>8}{'post %':>8}"
          f"{'disc $':>16}{'sched $':>16}{'post $%':>9}")
    for r in rows:
        print(f"{r['fy']:<5}{r['d_rows']:>10}{r['a_rows']:>9}{r['a_rows'] + r['x_rows']:>9}"
              f"{r['a_rows'] / r['d_rows']:>8.1%}"
              f"{(r['a_rows'] + r['x_rows']) / r['d_rows']:>8.1%}"
              f"{m(r['d_amt']):>16}{m(r['a_amt'] + r['x_amt']):>16}"
              f"{(r['a_amt'] + r['x_amt']) / r['d_amt']:>9.1%}")

    print("\n== WHERE THE MISSING ROWS LIVE: per-member streams vs everything else ==")
    print(f"{'FY':<5}{'disc Local/Youth/Aging':>24}{'disc stream $':>16}{'sched appendix':>16}"
          f"{'stream gap':>12}{'disc body':>11}{'sched awards':>13}{'body gap':>10}")
    gap_rows = gap_amt = 0
    for r in rows:
        print(f"{r['fy']:<5}{r['d_stream_rows']:>24}{m(r['d_stream_amt']):>16}{r['x_rows']:>16}"
              f"{r['d_stream_rows'] - r['x_rows']:>12}"
              f"{r['d_body_rows']:>11}{r['a_rows']:>13}"
              f"{r['d_body_rows'] - r['a_rows']:>10}")
        if r["fy"] <= 2020:
            gap_rows += r["d_stream_rows"] - r["x_rows"]
            gap_amt += r["d_stream_amt"] - r["x_amt"]
    print(f"  FY2015-FY2020 per-member stream shortfall: {gap_rows} rows  {m(gap_amt)}")

    print("\n== THE ACTUAL HOLE: disclosure rows with no (EIN, amount) partner in Schedule C ==")
    print(f"{'FY':<5}{'unmatched':>11}{'in streams':>12}{'$ streams':>15}"
          f"{'in body':>10}{'$ body':>16}{'of which pending':>18}")
    for r in rows:
        print(f"{r['fy']:<5}{r['miss_stream'] + r['miss_body']:>11}{r['miss_stream']:>12}"
              f"{m(r['miss_stream_amt']):>15}{r['miss_body']:>10}{m(r['miss_body_amt']):>16}"
              f"{r['miss_pending']:>18}")

    print("\n== SAME-UNIVERSE TEST: do the rows Schedule C DID capture exist in disclosure? ==")
    print(f"{'FY':<5}{'sched rows':>12}{'(EIN,amt) matched':>20}{'rate':>8}"
          f"{'orphan EIN':>12}{'orphan rows':>13}{'orphan $':>14}{'orphan $ %':>12}")
    for r in rows:
        print(f"{r['fy']:<5}{r['s_rows']:>12}{r['matched']:>20}"
              f"{r['matched'] / r['s_rows']:>8.1%}"
              f"{r['orphan_ein']:>12}{r['orphan_rows']:>13}{m(r['orphan_amt']):>14}"
              f"{r['orphan_amt'] / max(1, r['a_amt'] + r['x_amt']):>12.2%}")

    print("\n== INTERNAL CHECK, NO DISCLOSURE INVOLVED: the repo's own two Schedule C streams ==")
    print(f"{'FY':<5}{'initiatives $':>18}{'awards $':>18}{'residual':>18}{'residual %':>12}")
    for r in rows:
        _, iv = initiatives_total(r["fy"])
        print(f"{r['fy']:<5}{m(iv):>18}{m(r['a_amt']):>18}{m(iv - r['a_amt']):>18}"
              f"{(iv - r['a_amt']) / iv:>12.1%}")

    print("\n== ISSUE #51: council member attribution, both sides ==")
    print(f"{'FY':<5}{'disc blank':>12}{'disc labels':>13}{'sched blank':>13}"
          f"{'sched rows':>12}{'sched labels':>14}{'sheet':>20}")
    for r in rows:
        print(f"{r['fy']:<5}{r['d_member_blank']:>12}{r['d_members']:>13}"
              f"{r['s_member_blank']:>13}{r['s_rows']:>12}{r['s_members']:>14}"
              f"{r['sheet']:>20}")
    return rows


def demo():
    """The four claims FINDINGS.md leads with. If any breaks, the document is wrong."""
    r16, r20, r22, r27 = (year_row(y) for y in (2016, 2020, 2022, 2027))

    # 1. The rows Schedule C captured are overwhelmingly present in the disclosure. That is
    #    what makes this one universe rather than two, and it holds in the WORST year.
    assert r16["matched"] / r16["s_rows"] > 0.85, r16
    assert r27["matched"] / r27["s_rows"] > 0.99, r27

    # 2. The disclosure is NOT a strict superset -- small but non-zero in most years.
    assert r20["orphan_rows"] > 0 and r20["orphan_amt"] / r20["a_amt"] < 0.01, r20
    assert r27["orphan_rows"] == 0, r27

    # 3. FY2016-FY2020's hole is dominated by the per-member streams the appendix never got.
    assert r16["x_rows"] == 0 and r16["d_stream_rows"] > 4000, r16

    # 4. The parent plan's "FY2016-FY2020 is the broken range" scoping fails: FY2022 captures
    #    barely half its disclosure rows even AFTER the appendix load.
    assert 0.45 < (r22["a_rows"] + r22["x_rows"]) / r22["d_rows"] < 0.55, r22
    print("demo: OK")


if __name__ == "__main__":
    demo()
    main()
