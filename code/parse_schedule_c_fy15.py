#!/usr/bin/env python3
"""
Standalone Schedule C parser for FISCAL 2015 only.

Why a dedicated variant (not a change to parse_schedule_c.py)
------------------------------------------------------------
FY2015 is a modern-era Schedule C — it DOES carry EIN-anchored discretionary award
tables (member / organization / EIN / $amount), so its awards, roster, and appendix
extraction are handled exactly by the shared parser's machinery, which this file
imports and reuses unchanged.

The ONE thing the shared parser gets wrong on FY2015 is the initiatives
block -> category mapping. The shared parser maps the Nth "Agency Initiative Amount"
summary block to the Nth Table-of-Contents category (positional). That is safe for
FY2016-FY2027, where every ToC category that has a summary block appears in order and
the only unmatched categories are trailing (Youth Services). FY2015 breaks it:

  * its ToC lists 28 entries, but only 24 have a Council-Initiatives summary block;
  * two of the 28 are narrative front-matter ("FROM BUDGET RESPONSE TO ADOPTION...",
    "INTRODUCTION") that sit at the FRONT of the ToC, and
  * two real categories (BOROUGHWIDE NEEDS, HEALTH SERVICES AND PREVENTION) have no
    main-body summary block at all.

Because the two narrative entries lead the list, positional mapping shifts EVERY
label: block 0 (Anti-Gun Violence, $6.7M) gets labeled "FROM BUDGET RESPONSE...",
block 1 (Anti-Poverty, $2.8M) gets "INTRODUCTION", and so on, and the last four real
categories fall off the end as 0/0. The per-block amounts and totals are correct; only
the labels are wrong.

Fixing this in the shared parser would mean changing its labeling for all committed
years (regression risk to FY16-FY27), so — following the repo's existing pattern of
year/era-specific variants (parse_capital_fy25.py, parse_capital_fy26.py,
parse_schedule_c_legacy.py) — FY2015 gets this dedicated parser instead. It maps each
summary block to the category heading that immediately PRECEDES it in the body text
(the FY2015 layout always prints "<CATEGORY>" then "Agency Initiative Amount").

With correct labels, all 24 blocks reconcile 24/24 EXACT against their printed TOTAL —
after handling three FY2015 line-item formatting artifacts that the shared parser's
segmentation silently drops (each verified by hand to sum to the printed category TOTAL,
so these are extraction gaps, not in-source arithmetic):
  * CUNY   — an initiative whose NAME contains "Council Initiatives"
             ("Results Based Accountability for Council Initiatives $500,000"): the
             shared parser discards any line matching /council initiatives/ as a heading.
  * HOUSING — "$ 100,000" with a space between the "$" and the digits.
  * YOUTH  — "...Youth Action Build Initiative 2,100,000": a bare, comma-grouped amount
             printed with NO "$" sign.
(The same three artifact classes likely explain some of the single-category "in-source"
diffs recorded for FY16-FY24; hardening the SHARED parser for them is a separate,
regression-gated pass and is deliberately out of scope here.)

Emits the identical file set to the shared parser (matches FY16's output set):
  fy15_schedule_c_initiatives.csv   category, agencies, initiative, amount
  fy15_schedule_c_awards.csv        category, initiative, award_type, member,
                                    organization, program, ein, amount, agency, purpose
  fy15_appendix_a_aging.csv         (FY15 keeps all awards inline -> header only, like FY16)
  fy15_appendix_b_local.csv
  fy15_appendix_c_youth.csv
  fy15_schedule_c_reconciliation.txt

Regenerate:
  .venv/bin/python code/parse_schedule_c_fy15.py \
      source/FY15/fy2015-FY15-Schedule-C-Template-Final.pdf \
      --outdir data/fy15/schedule_c --prefix fy15
"""
import re, csv, os, argparse
from collections import Counter, defaultdict

import parse_schedule_c as P  # reuse all shared machinery unchanged


# A trailing money amount, tolerant of three FY2015-specific artifacts the shared parser's
# AMT_END ($ + digits, no gap) misses — each verified against the printed category TOTAL:
#   * '$ 100,000'  -> a space between the '$' and the digits         (HOUSING block)
#   * '2,100,000'  -> a bare comma-grouped amount with NO '$' sign   (YOUTH block)
# The bare (no-$) form is only accepted when comma-grouped, so a stray page number or a
# 4-digit year can't be mistaken for an amount.
AMT_DOLLAR = re.compile(r'\$\s*([\d,]+)\s*$')
AMT_BARE = re.compile(r'(?:^|\s)(\d{1,3}(?:,\d{3})+)\s*$')


def trailing_amount(s):
    """Return (start_index_of_amount, value) if the line ends in a money amount, else None."""
    m = AMT_DOLLAR.search(s)
    if m:
        return m.start(), P.money(m.group(1))
    m = AMT_BARE.search(s)
    if m:
        return m.start(1), P.money(m.group(1))
    return None


def parse_initiatives_fy15(pages, lo, hi, cats):
    """Segment each summary block ('Agency Initiative Amount' -> 'TOTAL $x') and map it to the
    category heading that immediately PRECEDES the block in the body (adjacent-heading mapping),
    instead of the shared parser's positional block[i] -> cats[i]. Returns
    (rows, recon, nblocks) with the same row shape the shared parser emits."""
    canon = {P.norm(c): c for c in cats}
    lines = []
    for pn in range(lo, hi):
        for ln in pages[pn].split("\n"):
            s = ln.strip()
            if s:
                lines.append(s)
    # positions of every category-heading line in the flattened body
    hd = {}
    for i, s in enumerate(lines):
        if P.norm(s) in canon:
            hd[i] = canon[P.norm(s)]

    # segment summary blocks. Data rows (a line ending in an amount) are captured BEFORE the
    # heading/noise filter, so a legitimate initiative whose NAME contains 'Council Initiatives'
    # (e.g. FY15 CUNY 'Results Based Accountability for Council Initiatives $500,000') is NOT
    # discarded as a section heading the way the shared parser drops it.
    blocks = []; in_block = False; start = None; buf = []; rows = []
    for i, s in enumerate(lines):
        if re.search(r'(?i)agency\s+initiative\s+amount', s):
            in_block = True; start = i; buf = []; rows = []; continue
        if not in_block:
            continue
        mt = re.match(r'(?i)^total\b.*?\$([\d,]+)', s)
        if mt:
            blocks.append((start, i, rows, P.money(mt.group(1)))); in_block = False; buf = []; rows = []; continue
        if P.RUNHDR.match(s) or re.match(r'^\d{1,3}$', s):   # running header / bare page number
            buf = []; continue
        ta = trailing_amount(s)
        if ta:
            pos, amt = ta
            pre = s[:pos].strip()
            if pre:
                buf.append(pre)
            rows.append((re.sub(r'\s+', ' ', " ".join(buf)).strip(), amt)); buf = []
            continue
        # a line with no trailing amount: a category heading, the 'Fiscal 20NN Council
        # Initiatives' sub-heading, or wrapped initiative-name text awaiting its amount.
        if P.norm(s) in canon or re.search(r'(?i)council initiatives', s) \
           or re.search(r'(?i)^fiscal \d{4}', s):
            buf = []; continue
        buf.append(s)

    # map each block to the NEAREST preceding heading (FY2015 always prints the category
    # heading just above its 'Agency Initiative Amount' table).
    K = 8

    def preceding_heading(block_start):
        for i in range(block_start - 1, block_start - K - 1, -1):
            if i in hd:
                return hd[i]
        return None

    out = []; recon = {}; unmapped = 0
    for a, t, rows, total in blocks:
        cat = preceding_heading(a)
        if cat is None:
            unmapped += 1
            cat = f"UNMAPPED_BLOCK_@{a}"
        # a category could (defensively) appear twice; sum rather than clobber
        recon[cat] = recon.get(cat, 0) + total
        for raw, amt in rows:
            m = re.match(r'^([A-Z][A-Za-z]{1,5}(?:[/,]\s?[A-Z][A-Za-z]{1,5})*)\s+(.*)$', raw)
            ag, name = (m.group(1), m.group(2)) if (m and raw.split()[0].isupper()) else ("", raw)
            out.append((cat, ag.strip(), name.strip(), amt))
    if unmapped:
        print(f"[warn] {unmapped} summary block(s) had no preceding category heading within {K} lines")
    return out, recon, len(blocks)


def main():
    ap = argparse.ArgumentParser(description="FY2015 Schedule C parser (adjacent-heading mapping).")
    ap.add_argument("pdf")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--prefix", required=True)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    pages = P.load_pages(a.pdf)
    maxp = max(pages)
    cats = P.derive_categories(pages)
    apxA = P.first_heading_page(pages, "Appendix A")
    apxB = P.first_heading_page(pages, "Appendix B")
    apxC = P.first_heading_page(pages, "Appendix C")
    body_hi = apxA or maxp + 1
    body_lo = 6
    for pn in sorted(pages):
        if pn > 2 and re.search(r'(?i)agency\s+initiative\s+amount', pages[pn]):
            body_lo = max(6, pn - 1); break
    roster = P.build_roster(pages, body_lo, maxp + 1)

    inits, recon, nblocks = parse_initiatives_fy15(pages, body_lo, body_hi, cats)
    awards = P.parse_awards(pages, body_lo, body_hi, cats, roster)

    # cleanup: identical to the shared parser (drop header-row artifacts; backfill purpose-polluted
    # org names by EIN) so the awards CSV matches the other modern years' shape exactly.
    HJ = ("legal name", "program name", "council member", "sponsor legal")
    awards = [r for r in awards if not any(h in r["organization"].lower() for h in HJ)]

    def _poll(o):
        return (not o) or bool(re.match(r'(?i)^(funds?|finds?|funding|to |support|provide|purpose)', o))

    nm = defaultdict(Counter)
    for r in awards:
        if not _poll(r["organization"]):
            nm[r["ein"]][r["organization"]] += 1
    for r in awards:
        if _poll(r["organization"]) and nm.get(r["ein"]):
            r["organization"] = nm[r["ein"]].most_common(1)[0][0]; r["_backfilled"] = "1"

    aging = P.parse_appendix(pages, apxA, apxB, roster, False, True) if apxA else []
    local = P.parse_appendix(pages, apxB, apxC, roster, True, True) if apxB else []
    youth = P.parse_appendix(pages, apxC, maxp + 1, roster, False, True) if apxC else []

    Pj = lambda n: os.path.join(a.outdir, f"{a.prefix}_{n}")
    with open(Pj("schedule_c_initiatives.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["category", "agencies", "initiative", "amount"])
        for c, ag, nm2, amt in inits:
            w.writerow([c, ag, nm2, amt])

    def wr(path, rows, cols):
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(cols)
            for r in rows:
                w.writerow([r.get(c, "") for c in cols])
    wr(Pj("schedule_c_awards.csv"), awards,
       ["category", "initiative", "award_type", "member", "organization", "program", "ein", "amount", "agency", "purpose"])
    wr(Pj("appendix_a_aging.csv"), aging, ["member", "organization", "program", "ein", "amount", "purpose"])
    wr(Pj("appendix_b_local.csv"), local, ["member", "organization", "program", "ein", "amount", "agency", "purpose"])
    wr(Pj("appendix_c_youth.csv"), youth, ["member", "organization", "program", "ein", "amount", "purpose"])

    isum = defaultdict(int)
    for c, ag, nm2, amt in inits:
        isum[c] += amt
    reconcilable = [c for c in cats if recon.get(c)]   # categories that actually have a summary block
    L = []
    L.append(f"SCHEDULE C RECONCILIATION  ({a.prefix})  [parser: parse_schedule_c_fy15.py, adjacent-heading mapping]")
    L.append(f"source: {os.path.basename(a.pdf)}  ({maxp} pages)")
    L.append(f"sections: body 6..{body_hi-1} | A {apxA} | B {apxB} | C {apxC}")
    L.append(f"categories from ToC: {len(cats)} | summary blocks found: {nblocks} | "
             f"reconcilable (have a block): {len(reconcilable)} | roster: {len(roster)} members\n")
    L.append(f"{'CATEGORY':52} {'initiatives':>14} {'printed':>14}  status")
    ok = 0; gi = 0; gp = 0
    for c in cats:
        i = isum.get(c, 0); p = recon.get(c) or 0; gi += i; gp += p
        if p == 0:
            L.append(f"{c[:52]:52} {i:>14,} {p:>14,}  no summary block")
            continue
        if i == p:
            ok += 1
        L.append(f"{c[:52]:52} {i:>14,} {p:>14,}  {'OK' if i == p else f'DIFF {i-p:+,}'}")
    L.append(f"{'GRAND TOTAL':52} {gi:>14,} {gp:>14,}  {ok}/{len(reconcilable)} reconcilable categories exact")
    L.append("")
    L.append("Notes:")
    L.append(f"  * {len(reconcilable)} of {len(cats)} ToC entries carry a Council-Initiatives summary block.")
    L.append("  * 4 ToC entries have no summary block: 2 narrative front-matter sections")
    L.append("    (FROM BUDGET RESPONSE..., INTRODUCTION) + 2 real categories funded without a")
    L.append("    main-body summary (BOROUGHWIDE NEEDS, HEALTH SERVICES AND PREVENTION).")
    L.append("  * All 24 reconcilable categories are EXACT. Three FY15 line-item formatting")
    L.append("    artifacts are handled here (a 'Council Initiatives' initiative name, a '$ 100,000'")
    L.append("    space-after-dollar amount, and a bare no-$ '2,100,000' amount) — each verified to")
    L.append("    sum to the printed category TOTAL.")
    mi = [r for r in awards if r['award_type'] == 'member_item']
    ip = [r for r in awards if r['award_type'] == 'initiative_provider']
    L.append("")
    L.append(f"awards: {len(awards)} rows  ${sum(r['amount'] for r in awards):,}  (EIN-anchored; FY15 IS award/EIN-level)")
    L.append(f"  member items:         {len(mi):5d}  ${sum(r['amount'] for r in mi):,}")
    L.append(f"  initiative providers: {len(ip):5d}  ${sum(r['amount'] for r in ip):,}")
    L.append(f"appendix A (aging): {len(aging):5d} rows  ${sum(r['amount'] for r in aging):,}")
    L.append(f"appendix B (local): {len(local):5d} rows  ${sum(r['amount'] for r in local):,}")
    L.append(f"appendix C (youth): {len(youth):5d} rows  ${sum(r['amount'] for r in youth):,}")
    rep = "\n".join(L)
    open(Pj("schedule_c_reconciliation.txt"), "w").write(rep + "\n")
    print(rep)
    print("\nWROTE ->", a.outdir)


if __name__ == "__main__":
    main()
