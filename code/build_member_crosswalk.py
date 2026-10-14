#!/usr/bin/env python3
"""Resolve the expense disclosure's `council_member` values to Legistar person IDs, per fiscal
year, and publish the crosswalk (GitHub #72).

The disclosure prints a member as a bare surname ("Levin"), sometimes with an initial
("D. Diaz", "Sanchez, J"), and the value is the Council's roster when the workbook was exported,
not proof of who made the designation. A substring filter on it blends different people:
"Levin" matches "Levine", "Won" matches "Wong". This script maps each (fiscal_year, printed
value) to at most one Legistar person, and says how, from evidence that is committed with it.

Inputs (committed, so CI and tests need neither the Legistar database nor the network):
  data/reference/council_members_legistar.csv   the roster extract, with each person's first
                                                and last recorded vote (code/extract_council_roster.py)
  the disclosure workbooks, parsed by code/parse_expense_disclosure.py (for the printed values
  and their row counts per year)

Output:
  data/disclosure_council_member_crosswalk.csv  one row per (fiscal_year, council_member)

council_member_type, decided in this order:
  blank             the cell is empty
  speaker           "Speaker": the Speaker's designations, a role, not a named member
  delegation        a borough delegation ("Bronx Delegation", "Brooklyn", "SI Delegation",
                    "Brooklyn / Queens")
  citywide          "Citywide"
  district_label    a council district label ("CD28"), not a person; never resolved to one
  member            exactly one Legistar person carries the printed surname (and initial, if
                    printed) AND has a recorded vote inside the fiscal year
  member_outside_fy exactly one such person exists, but none of them voted inside the fiscal
                    year: the workbook's export-time roster names someone who was not yet (or
                    no longer) in office that year (e.g. FY2025 "Wong", rows re-attributed from
                    Holden). The ID is given; the type says it is not that year's member.
  ambiguous         more than one such person voted inside the fiscal year; no ID, the
                    candidates are listed. Never guessed -- except where a person has decided a
                    file convention for that one (fiscal year, value); see FILE_CONVENTIONS.
  unresolved        no Legistar person carries the name ("CC", "NA"); no ID.

Service evidence and its limits: the fiscal years in which the Legistar index records at least
one vote by the person (any body), as a set -- members leave and return (Charles Barron: FY2004-
FY2014 and FY2022-FY2024; Inez Barron held the seat between). A fiscal year counts only if a
vote was recorded in it, so a member sworn in or leaving within days of a year boundary, with no
vote on that side of it, is not counted there. A person with no recorded vote (pre-2001 members,
Public Advocates) has no years and is never a candidate. The index's vote records run from 2001
to its last indexing date (data/reference/council_members_legistar_meta.csv), which covers every
fiscal year here except the unfinished part of FY2027.

File conventions (FILE_CONVENTIONS below): a value the rules above leave ambiguous may be
resolved by a decision a person made and recorded here, never by this script on its own. One
exists: FY2021 bare "Diaz". Ruben Diaz, Sr. and Darma V. Diaz both voted in FY2021; the workbook
prints Darma Diaz as "D. Diaz" in the same year, so bare "Diaz" is read as the other one, Ruben
Diaz, Sr. (Noel Hidalgo, 2026-10-13). The row is typed `member` and its method begins
"file_convention". The evidence is computed from the parsed workbook on every build, never typed
in: the Local-stream rows of each value, by the grantee's city and ZIP prefix. Those are grantee
MAILING addresses, not where services were delivered, so they support the reading; they do not
prove it. The build stops if the generic rule stops calling the value ambiguous, if the sibling
value is gone or resolves to someone else, or if the addresses stop pointing the stated way. A
rule names one fiscal year and one printed value and applies nowhere else.

Run:
  python3 code/build_member_crosswalk.py           print a summary
  python3 code/build_member_crosswalk.py --write   write the crosswalk
  python3 code/build_member_crosswalk.py --check   exit 1 if the committed crosswalk is stale
"""

import argparse
import collections
import csv
import datetime
import io
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ROSTER = os.path.join(ROOT, "data", "reference", "council_members_legistar.csv")
OUT = os.path.join(ROOT, "data", "disclosure_council_member_crosswalk.csv")

FIELDS = ["fiscal_year", "council_member", "rows", "council_member_type", "council_member_id",
          "legistar_full_name", "method", "evidence"]
TYPES = ("member", "member_outside_fy", "ambiguous", "unresolved", "speaker", "delegation",
         "citywide", "district_label", "blank")
# Types that carry a person ID.
ID_TYPES = ("member", "member_outside_fy")

_DELEGATION = re.compile(r"(?:bronx|brooklyn|manhattan|queens|staten island|si)"
                         r"(?:\s*/\s*(?:bronx|brooklyn|manhattan|queens|staten island))?"
                         r"(?: delegation)?", re.IGNORECASE)


def fold(s):
    """Case-, accent- and spacing-insensitive form: 'Velázquez' == 'velazquez'."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.replace("\u2019", "'").lower().split())


def fy_window(fy):
    """NYC fiscal year N runs July 1 of N-1 through June 30 of N."""
    return datetime.date(fy - 1, 7, 1), datetime.date(fy, 6, 30)


_SUFFIX = re.compile(r"(.+?),?\s+(jr|sr)\.?")


def split_suffix(v):
    """'vallone, jr' / 'sanders jr.' -> ('vallone', 'jr'); anything else -> (v, '')."""
    m = _SUFFIX.fullmatch(v)
    return (m.group(1), m.group(2)) if m else (v, "")


class Person:
    __slots__ = ("core", "first", "first_vote", "full", "hint", "id", "last_vote", "suffix",
                 "years")

    def __init__(self, row):
        self.id = row["person_id"]
        self.full = row["full_name"]
        self.first = fold(row["first_name"])
        last = fold(row["last_name"])
        last, self.suffix = split_suffix(last)               # "salamanca, jr." -> "salamanca"
        m = re.fullmatch(r"([a-z])\.\s*(.+)", last)          # Legistar's own "d. diaz"
        self.hint = m.group(1) if m else ""
        self.core = m.group(2) if m else last
        self.first_vote = datetime.date.fromisoformat(row["first_vote"]) if row["first_vote"] else None
        self.last_vote = datetime.date.fromisoformat(row["last_vote"]) if row["last_vote"] else None
        self.years = frozenset(int(y) for y in row["vote_fiscal_years"].split(";") if y)

    def window(self):
        """'FY2004, FY2006-FY2014, FY2022-FY2024' -- the fiscal years with a recorded vote."""
        if not self.years:
            return "no recorded vote"
        runs, ys = [], sorted(self.years)
        start = prev = ys[0]
        for y in ys[1:] + [None]:
            if y is not None and y == prev + 1:
                prev = y
                continue
            runs.append(f"FY{start}" if start == prev else f"FY{start}-FY{prev}")
            if y is not None:
                start = prev = y
        return ", ".join(runs)

    def voted_in(self, fy):
        return fy in self.years

    def initials(self):
        return {x for x in (self.first[:1], self.hint) if x}


def load_roster(path=ROSTER):
    with open(path, newline="", encoding="utf-8") as f:
        return [Person(r) for r in csv.DictReader(f)]


def parse_printed(value):
    """'D. Diaz' / 'J. Sanchez' / 'Sanchez, J' -> (surname, initial); 'Levin' -> ('levin', '')."""
    v = fold(value)
    m = re.fullmatch(r"([a-z])\.\s*(.+)", v)
    if m:
        return m.group(2), m.group(1)
    m = re.fullmatch(r"(.+?),\s*([a-z])\.?", v)
    if m:
        return m.group(1), m.group(2)
    return v, ""


def name_candidates(value, roster):
    """People whose surname is the printed surname. An exact surname match wins; then the same
    surname with spaces ignored ('DeBlasio' -> Legistar's 'de Blasio'); only if neither exists
    does a component of a hyphenated or two-word surname count ('Viverito' -> Mark-Viverito,
    'Ferreras' -> Ferreras-Copeland). A printed initial must match the person's first-name
    initial or Legistar's own initial prefix ('D. Diaz'). A printed generational suffix
    ('Vallone, Jr', FY2009-FY2011) must be the suffix Legistar records for the person: 'Vallone,
    Jr' is Peter F. Vallone, Jr., never Peter F. Vallone or Paul A. Vallone, and a person whose
    Legistar name carries no suffix is not a candidate for a suffixed value."""
    base, suffix = split_suffix(fold(value))
    surname, initial = parse_printed(base)
    exact = [p for p in roster if p.core == surname]
    spaced = [] if exact else [p for p in roster
                               if p.core.replace(" ", "") == surname.replace(" ", "")]
    cands = exact or spaced or [p for p in roster if surname in re.split(r"[-\s]+", p.core)]
    if initial:
        cands = [p for p in cands if initial in p.initials()]
    if suffix:
        cands = [p for p in cands if p.suffix == suffix]
    how = "exact surname" if exact else ("exact surname, spaces ignored" if spaced
                                         else "surname component")
    return cands, how + (f" + initial {initial.upper()}" if initial else "") + \
        (f" + suffix {suffix.capitalize()}" if suffix else "")


def classify(value, fy, roster):
    """-> dict with council_member_type, council_member_id, legistar_full_name, method, evidence."""
    v = " ".join((value or "").split())
    out = {"council_member_type": "", "council_member_id": "", "legistar_full_name": "",
           "method": "", "evidence": ""}
    if not v:
        return dict(out, council_member_type="blank", method="empty cell")
    if fold(v) == "speaker":
        return dict(out, council_member_type="speaker", method="the role 'Speaker', not a named member")
    if _DELEGATION.fullmatch(v):
        return dict(out, council_member_type="delegation", method="borough delegation label")
    if fold(v) == "citywide":
        return dict(out, council_member_type="citywide", method="citywide label")
    if re.fullmatch(r"cd\s*\d+", fold(v)):
        return dict(out, council_member_type="district_label",
                    method="council district label, not a person; not resolved to one")
    cands, how = name_candidates(v, roster)
    voted = [p for p in cands if p.years]
    unvoted = [p for p in cands if not p.years]
    a, b = fy_window(fy)
    span = f"FY{fy} = {a}..{b}"
    excluded = "; ".join(f"excluded {p.full} ({p.id}): no recorded vote" for p in unvoted)
    if not voted:
        return dict(out, council_member_type="unresolved",
                    method=f"no Legistar person with a recorded vote matches ({how})",
                    evidence=excluded)
    in_fy = [p for p in voted if p.voted_in(fy)]
    desc = "; ".join(f"{p.full} ({p.id}) voted in {p.window()}" for p in voted)
    ev = f"{span}; {desc}" + (f"; {excluded}" if excluded else "")
    if len(in_fy) == 1:
        p = in_fy[0]
        return dict(out, council_member_type="member", council_member_id=p.id,
                    legistar_full_name=p.full,
                    method=f"{how}; the only match with a recorded vote in FY{fy}", evidence=ev)
    if len(in_fy) > 1:
        return dict(out, council_member_type="ambiguous",
                    method=f"{how}; {len(in_fy)} matches voted in FY{fy}; not guessed",
                    evidence=ev)
    if len(voted) == 1:
        p = voted[0]
        return dict(out, council_member_type="member_outside_fy", council_member_id=p.id,
                    legistar_full_name=p.full,
                    method=f"{how}; the only match, but no recorded vote in FY{fy} "
                           f"(the workbook's export-time roster)", evidence=ev)
    return dict(out, council_member_type="ambiguous",
                method=f"{how}; {len(voted)} matches, none voted in FY{fy}; not guessed",
                evidence=ev)


# ---------------------------------------------------------------- file conventions

# Decisions a person made for one (fiscal year, printed value) the rules leave ambiguous. Each
# names the sibling value the workbook prints for the other candidate in the same year, the
# person the bare value is read as, and each candidate's district (borough + the ZIP prefix of
# that borough, for the address evidence). build() re-derives the evidence and stops if any
# premise fails. Keyed by (fiscal_year, value): a rule never applies to another year.
FILE_CONVENTIONS = {
    (2021, "Diaz"): {
        "sibling": "D. Diaz",
        "person_id": "7744",
        "districts": {"7744": ("District 18", "Bronx", "104"),
                      "7793": ("District 37", "Brooklyn", "112")},
        "decided": "Noel Hidalgo, 2026-10-13",
    },
}
EVIDENCE_STREAM = "Local"   # a member's own Local designations; citywide initiatives say less


def address_evidence(rows, boroughs):
    """rows: [(source, city, zip)] for one (year, value) -> (n Local rows, {borough: (rows whose
    city is the borough, rows whose zip starts with its prefix)})."""
    local = [(fold(c), z) for s, c, z in rows if s == EVIDENCE_STREAM]
    return len(local), {b: (sum(c == fold(b) for c, _ in local),
                            sum(z.startswith(pre) for _, z in local)) for b, pre in boroughs}


def apply_convention(fy, value, rule, roster, addresses):
    """The crosswalk fields for a FILE_CONVENTIONS value, or ValueError naming the premise that
    no longer holds."""
    where = f"file convention FY{fy} {value!r}"
    generic = classify(value, fy, roster)
    if generic["council_member_type"] != "ambiguous":
        raise ValueError(f"{where}: the rules now type it {generic['council_member_type']!r}; "
                         f"the convention is no longer needed -- remove it")
    cands, _how = name_candidates(value, roster)
    in_fy = {p.id: p for p in cands if p.voted_in(fy)}
    if set(in_fy) != set(rule["districts"]) or rule["person_id"] not in in_fy:
        raise ValueError(f"{where}: in-office candidates are {sorted(in_fy)}, the rule names "
                         f"{sorted(rule['districts'])}")
    sib = classify(rule["sibling"], fy, roster)
    other = next(i for i in in_fy if i != rule["person_id"])
    if (fy, rule["sibling"]) not in addresses or sib["council_member_id"] != other \
            or sib["council_member_type"] != "member":
        raise ValueError(f"{where}: the sibling {rule['sibling']!r} is not printed in FY{fy} as "
                         f"member {other} (got {sib['council_member_type']!r} "
                         f"{sib['council_member_id']!r})")
    boroughs = [(rule["districts"][i][1], rule["districts"][i][2]) for i in (rule["person_id"], other)]
    (mine_b, _), (other_b, _) = boroughs
    ev = {}
    for v in (value, rule["sibling"]):
        n, by = address_evidence(addresses.get((fy, v), []), boroughs)
        ev[v] = (n, by)
    _, bare = ev[value]
    _, sibl = ev[rule["sibling"]]
    if not (bare[mine_b][1] > bare[other_b][1] and sibl[other_b][1] > sibl[mine_b][1]):
        raise ValueError(f"{where}: the Local-stream ZIP prefixes no longer point the stated way: "
                         f"{value!r} {bare}, {rule['sibling']!r} {sibl}")
    p, q = in_fy[rule["person_id"]], in_fy[other]

    def said(v):
        n, by = ev[v]
        return (f"{v!r} {n} {EVIDENCE_STREAM}-stream rows: city "
                + " / ".join(f"{b} {by[b][0]}" for b, _ in boroughs) + ", ZIP "
                + " / ".join(f"{pre}xx {by[b][1]}" for b, pre in boroughs))

    dist = "; ".join(f"{x.full} ({x.id}) = {rule['districts'][x.id][0]} ({rule['districts'][x.id][1]})"
                     for x in (p, q))
    return dict(generic, council_member_type="member", council_member_id=p.id,
                legistar_full_name=p.full,
                method=(f"file_convention: both {p.full} and {q.full} voted in FY{fy}; the workbook "
                        f"prints {q.full} as {rule['sibling']!r} in the same year, so {value!r} is "
                        f"read as {p.full} (decided by {rule['decided']})"),
                evidence=(f"{generic['evidence']}; {dist}; grantee mailing addresses, not where "
                          f"services were delivered: {said(value)}; {said(rule['sibling'])}"))


def build(pairs, roster, addresses=None, conventions=None):
    """pairs: {(fiscal_year, printed value): row count} -> crosswalk rows, sorted. addresses:
    {(fiscal_year, value): [(source, city, zip)]}, needed for any value in `conventions`
    (default FILE_CONVENTIONS) that `pairs` holds, and for its sibling."""
    conventions = FILE_CONVENTIONS if conventions is None else conventions
    rows = []
    for (fy, v), n in sorted(pairs.items(), key=lambda kv: (kv[0][0], kv[0][1].lower(), kv[0][1])):
        rule = conventions.get((fy, v))
        if rule is not None:
            if addresses is None or (fy, v) not in addresses:
                raise ValueError(f"file convention FY{fy} {v!r}: no address evidence passed")
            fields = apply_convention(fy, v, rule, roster, addresses)
        else:
            fields = classify(v, fy, roster)
        rows.append({"fiscal_year": fy, "council_member": v, "rows": n, **fields})
    return rows


def disclosure_inputs(conventions=None):
    """({(fiscal_year, council_member): rows}, {(fiscal_year, value): [(source, city, zip)]})
    from the workbooks, through the parser. Addresses are kept only for the file-convention
    values and their siblings; zip is the dataset's own derived zip (code/zcta_states.py)."""
    conventions = FILE_CONVENTIONS if conventions is None else conventions
    sys.path.insert(0, HERE)
    import parse_expense_disclosure as P  # sibling module, imported on use
    import zcta_states as Z
    zctas = Z.load_table()
    want = set(conventions) | {(fy, r["sibling"]) for (fy, _v), r in conventions.items()}
    pairs, addresses = collections.Counter(), collections.defaultdict(list)
    for awards, rep in P.parse_all():
        if rep.skipped:
            raise SystemExit(f"FY{rep.fiscal_year} skipped ({rep.skipped}); cannot build the crosswalk")
        for a in awards:
            key = (a.fiscal_year, a.council_member)
            pairs[key] += 1
            if key in want:
                addresses[key].append((a.source, a.city, Z.classify_zip(a.postal_code, a.state, zctas)[0]))
    return pairs, dict(addresses)


def disclosure_pairs():
    """{(fiscal_year, council_member): rows} from the workbooks, through the parser."""
    return disclosure_inputs()[0]


def text(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def load(path=OUT):
    """{(fiscal_year:int, council_member): (type, id)} from the committed crosswalk."""
    with open(path, newline="", encoding="utf-8") as f:
        return {(int(r["fiscal_year"]), r["council_member"]):
                (r["council_member_type"], r["council_member_id"]) for r in csv.DictReader(f)}


def summary(rows):
    by = collections.Counter(r["council_member_type"] for r in rows)
    by_rows = collections.Counter()
    for r in rows:
        by_rows[r["council_member_type"]] += int(r["rows"])
    return {t: (by[t], by_rows[t]) for t in TYPES}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true", help="write the crosswalk CSV")
    g.add_argument("--check", action="store_true", help="exit 1 if the committed crosswalk is stale")
    a = ap.parse_args(argv)
    pairs, addresses = disclosure_inputs()
    try:
        rows = build(pairs, load_roster(), addresses)
    except ValueError as e:
        print(f"STOP: {e}")
        return 1
    t = text(rows)
    if a.check:
        cur = ""
        if os.path.exists(OUT):
            with open(OUT, encoding="utf-8") as f:
                cur = f.read()
        if cur != t:
            print(f"STALE: {os.path.relpath(OUT, ROOT)} -- run code/build_member_crosswalk.py --write")
            return 1
        print(f"{os.path.relpath(OUT, ROOT)} is current")
    elif a.write:
        with open(OUT, "w", encoding="utf-8", newline="") as f:
            f.write(t)
        print(f"wrote {os.path.relpath(OUT, ROOT)}")
    for typ, (values, n) in summary(rows).items():
        print(f"{typ:<18} {values:>5} (year, value) pairs {n:>8,} rows")
    for r in rows:
        if r["method"].startswith("file_convention"):
            print(f"file_convention    FY{r['fiscal_year']} {r['council_member']!r} -> "
                  f"{r['council_member_id']} {r['legistar_full_name']} ({r['rows']} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
