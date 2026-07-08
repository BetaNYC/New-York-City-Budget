#!/usr/bin/env python3
"""
Parse the NYC Council 'Terms and Conditions' PDFs in the EARLIER format used FY2015-FY2024,
which parse_terms.py cannot read (it returns 0 rows).

Format difference from the FY25-FY27 documents parse_terms.py handles
--------------------------------------------------------------------
FY25-FY27 number each condition with a leading 'N. Agency Name (Code)' header. The FY15-FY24
documents do NOT: a condition simply opens with a header line of one of these shapes, with no
item number:

  * 'Agency Name (068)'                         -- agency + 3-digit budget code
  * 'Capital Budget'                            -- a bare capital header (no agency, no code)
    followed by 'All Project Lines - All Projects' or 'Budget Line HA-0001 - <title>'

(FY15/FY16 additionally print a bare sequence number on its OWN line before each header; those
are indistinguishable from page numbers by pattern, so this parser ignores them and assigns its
own sequential item_number in document order -- a 1:1 stand-in, since the source order is
preserved.)

A single condition can span MULTIPLE agency headers (e.g. ACS (068) then DOC (072), each with
its own Unit-of-Appropriation lines, sharing one condition paragraph). Those are kept as one
item: the first header is the primary agency_name/agency_code, every header's UA lines are
collected, and the condition text names all agencies.

Emits the same schema as parse_terms.py:
  {prefix}_terms_and_conditions.csv  item_number, agency_name, agency_code,
      units_of_appropriation, num_units, report_deadlines, coverage_period, condition_text

There are no printed totals in a Terms & Conditions document, so there is nothing to reconcile;
correctness is checked by item/agency/UA counts and by regression tests on the committed CSVs.
"""
import re, csv, os, argparse
from parse_terms import load_pages, DATE, PERIOD

# Agency header WITHOUT a leading item number: 'Administration for Children's Services (068)'.
HEADER = re.compile(r'^(.+?\S)\s+\((\d{3})\)\s*$')
CAPITAL = 'Capital Budget'
# Unit-of-Appropriation, and the capital sub-headers that play the same "unit" role.
UA = re.compile(r'^Units? of Appropriation\s+\[?(\w+)\]?')
CAP_UNIT = re.compile(r'^(?:Budget Line|All Project Lines)\b')

def clean_lines(pages):
    """Document text as physical lines, minus page furniture / running headers. Bare numbers are
    dropped (FY15/FY16 item numbers look identical to page numbers; item_number is synthesized)."""
    out = []
    for pn in sorted(pages):
        for ln in pages[pn].split("\n"):
            s = ln.replace("\xa0", " ").replace("‐", "-").strip()
            if not s:
                continue
            if re.match(r'^Page \d+ of \d+$', s) or re.match(r'^\d{1,3}$', s):
                continue
            if re.match(r'(?i)^fiscal (year )?20\d\d', s) and "condition" not in s.lower():
                continue
            if re.match(r'(?i)^(terms )?and conditions$', s) or re.match(r'(?i)^terms$', s):
                continue
            out.append(s)
    return out

def parse(pages):
    lines = clean_lines(pages)
    items = []; cur = None; synth = 0
    for s in lines:
        h = HEADER.match(s)
        cap = (s == CAPITAL)
        if h or cap:
            # a header that follows condition text starts a NEW item; a header with no text yet
            # is an additional agency for the SAME item (keep the first as primary).
            if cur is None or cur["text"]:
                if cur:
                    items.append(cur)
                synth += 1
                cur = dict(item_number=synth,
                           agency_name=(h.group(1).strip() if h else CAPITAL),
                           agency_code=(h.group(2) if h else ""),
                           units=[], text=[])
            continue
        if cur is None:
            continue
        if not cur["text"]:
            u = UA.match(s)
            if u:
                cur["units"].append(u.group(1)); continue
            if CAP_UNIT.match(s):
                cur["units"].append(re.sub(r'\s+', ' ', s).strip()); continue
        cur["text"].append(s)
    if cur:
        items.append(cur)

    out = []
    for it in items:
        txt = re.sub(r'\s+', ' ', " ".join(it["text"])).strip()
        txt = re.sub(r'(\w)\s-\s(\w)', r'\1\2', txt)
        dates = sorted(set(m.group(0) for m in DATE.finditer(txt)))
        pm = PERIOD.search(txt)
        period = f"{pm.group(1)} to {pm.group(2)}" if pm else ""
        out.append(dict(item_number=it["item_number"], agency_name=it["agency_name"],
                        agency_code=it["agency_code"], units_of_appropriation="; ".join(it["units"]),
                        num_units=len(it["units"]), report_deadlines="; ".join(dates),
                        coverage_period=period, condition_text=txt))
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("--outdir", required=True); ap.add_argument("--prefix", required=True)
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    pages = load_pages(a.pdf); items = parse(pages)
    cols = ["item_number", "agency_name", "agency_code", "units_of_appropriation", "num_units",
            "report_deadlines", "coverage_period", "condition_text"]
    p = os.path.join(a.outdir, f"{a.prefix}_terms_and_conditions.csv")
    with open(p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for it in items:
            w.writerow([it[c] for c in cols])
    from collections import Counter
    ag = Counter(it["agency_name"] for it in items)
    print(f"{a.prefix}: {len(items)} conditions across {len(ag)} agencies | "
          f"{sum(it['num_units'] for it in items)} UA/budget-line references | "
          f"{sum(1 for it in items if it['report_deadlines'])} with explicit deadlines")
    print("  top agencies:", ", ".join(f"{n}({c})" for n, c in ag.most_common(4)))
    print("  ->", p)

if __name__ == "__main__":
    main()
