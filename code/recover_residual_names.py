#!/usr/bin/env python3
"""
recover_residual_names.py — the residue pass after recover_org_names.py.

recover_org_names.py recovers a grantee name when the Council's expense disclosure resolves the
row's (EIN, amount) to EXACTLY ONE legal name. That leaves a residue it cannot touch, currently
252 rows: 156 `org_prose`, 92 `org_merged`, 4 with an entirely empty `organization` (counts under
validate_data.py's definitions, which are narrower than recover_org_names.py's internal PROSE).
Two things put a row in the residue:

  * the disclosure offers SEVERAL names for that (EIN, amount) — usually punctuation and suffix
    variants of one organization ("Safe Horizon" / "Safe Horizon, Inc."), sometimes genuinely
    different grantees sharing a fiscal sponsor's EIN and a common round amount; or
  * the disclosure offers NONE — the year is missing, or the amount was later amended.

This pass adds three more sources and applies a name only where at least TWO of the four agree and
NONE dissents. It never breaks a tie and never picks a "best" candidate; disagreement and internal
ambiguity are both hard stops.

  S1 council_disclosure     source/expense-funding-disclosure/funded_disclosure_FY*.xlsx
  S2 transparency_reso      data/fy*/transparency-resolutions/*_transparency_all.csv
                            The Council's designation resolutions — published separately from the
                            disclosure workbook, on a different cadence, from different copy.
  S3 corpus_other_year      our own clean award rows for the same (EIN, amount) in a DIFFERENT
                            fiscal year. Never the row's own year: a same-year sibling is the same
                            source document, not corroboration.
  S4 absorbed_text          org_merged only — the name printed after the last dollar figure in the
                            row's own polluted text. Free, but wrong often enough (see below) that
                            it is only ever a corroborating vote, never a lone witness.

KEY, and the safety of this script rests on it exactly as it does in recover_org_names.py:
(EIN, amount), never EIN alone. Fiscal sponsors pass funds through for many grantees — EIN
13-2612524 (Fund for the City of New York) carries 229 distinct names in this corpus — so an
EIN-only recovery stamps the SPONSOR's name onto an award that went somewhere else. `member` is
NOT a component: the disclosure workbooks are republished with the roster current at snapshot
time rather than the one that adopted the budget, which drops the unique-match rate from 96% to
24% (Phase 1 FINDINGS.md).

THE UNANIMITY RULE, stated exactly, because "two sources agree" has a weak reading that is wrong:

  1. Each source that has anything to say must collapse to ONE canonical name (canon() below).
     A source offering several distinct organizations does not abstain — it VETOES. Its key was
     not unique, so the key does not identify this award, so no source keyed the same way can be
     trusted on this row either. This is what keeps fiscal-sponsor rows out: their (EIN, amount)
     is non-unique everywhere at once.
  2. At least TWO sources must have spoken.
  3. Every source that spoke must agree on that one canonical name.

Any violation leaves the row alone, still flagged. A row left flagged is a correct outcome.

Worked example of why S4 is never trusted alone — data/fy16/schedule_c line 197 carries EIN
13-6202692 for $10,000 and the text "Bowery Residents' Committee Senior Center 13-2736659 *
$261,000 Charles Walburg Multi-Service Center". The trailing name is a neighbouring award's, not
this row's; the disclosure names Chinese-American Planning Council for that (EIN, amount). Two
sources, flat disagreement, so the row is left alone. That is the rule working, not failing.

Usage:
  python3 code/recover_residual_names.py --dry-run   # report only; writes NOTHING, anywhere
  python3 code/recover_residual_names.py             # apply, and append to the crosswalk
"""
import argparse
import collections
import csv
import glob
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"
CROSSWALK_FIELDS = ["file", "line", "ein", "amount", "defect", "source", "match_key",
                    "original_organization", "recovered_organization"]

# validate_data.py's advisory patterns, verbatim. The residue this script targets is defined as
# "what the validator still flags", so the detection must be the validator's, not a broader one:
# recover_org_names.py's internal PROSE is deliberately wider and also fires on real grantee names
# ("Fund for the City of New York" trips `funds? for`), which are not defects and not in scope.
ORG_PROSE = re.compile(
    r"\b(will |funds? (requested|will)|to support|to provide|funding (for|to|will)"
    r"|in order to|program that|services to)\b", re.I)
EIN_IN_TEXT = re.compile(r"\d{2}-\d{7}")
# Anything with a dollar figure or a formatted EIN inside it is polluted text, wherever it is read
# from. Used to keep the SOURCES clean as well as to detect the defect: a source row that is itself
# broken must never become the recovery for another row.
DOLLAR = re.compile(r"\$\s*[\d,]+(?:\.\d+)?")


# Boroughs and agencies that appear in the noisy `member` column but are not council surnames.
# Copied from validate_data.py so the two agree on what a surname is.
NOT_SURNAMES = {"brooklyn", "bronx", "queens", "manhattan", "staten", "island", "speaker",
                "citywide", "delegation", "various"}
_SURNAMES = set()


def build_surnames():
    """Council-member surnames, taken from the transparency files' `council_member` column, which
    is the cleanest place they appear. Same construction as validate_data.build_surname_set:
    single alpha tokens of 4+ characters, boroughs and agencies removed."""
    out = set()
    for p in sorted(glob.glob("data/fy*/transparency-resolutions/*_transparency_all.csv")):
        with open(p, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                v = (r.get("council_member") or "").strip()
                if not v:
                    continue
                tok = v.split()[-1]            # "De La Rosa" -> "Rosa"
                if tok.isalpha() and len(tok) >= 4 and tok.lower() not in NOT_SURNAMES:
                    out.add(tok.lower())
    return out


def classify(org):
    """The defect on this row, or None. Mirrors validate_data.py's order: org_merged wins over
    org_prose, because an absorbed neighbour is the more severe finding."""
    if not org:
        return "empty"
    if EIN_IN_TEXT.search(org) or "$" in org:
        return "org_merged"
    if ORG_PROSE.search(org):
        return "org_prose"
    return None


def has_member_bleed(org):
    """A council surname sitting in front of the organization name — validate_data.py's
    `column_bleed` advisory, 3,893 rows corpus-wide. "Gjonaj HANAC, Inc." is not a variant spelling
    of HANAC; it is a corrupt record, and a corrupt record must not become the recovery for a
    broken one."""
    toks = (org or "").split()
    return len(toks) > 1 and toks[0].strip(".,").lower() in _SURNAMES


def is_clean_name(org):
    """Usable as EVIDENCE: present, not polluted, not prose, no member-name bleed.

    This filter only ever REMOVES candidates. Removing a good candidate can leave a row flagged
    that might have been recoverable; it can never turn a correct answer into a wrong one. That
    asymmetry is why the filter is deliberately blunt — a handful of genuine names do begin with a
    word that is also a council surname, and losing them as evidence costs nothing that matters.
    """
    return bool(org) and classify(org) is None and not has_member_bleed(org)


def norm_ein(v):
    return re.sub(r"\D", "", v or "")


def to_amount(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def canon(name):
    """Normalise for COMPARISON only — never for output. Collapses the benign variants that make
    two sources look like they disagree when they do not: 'Carnegie Hall Corporation' vs
    'Carnegie Hall Corporation, The'. Copied from recover_org_names.py so the two passes agree on
    what "the same organization" means."""
    n = (name or "").lower().strip()
    n = re.sub(r"^the\s+", "", n)
    n = re.sub(r"[,.]?\s*(the|inc|incorporated|llc|ltd|corp|corporation|co)\b\.?", " ", n)
    return re.sub(r"[^a-z0-9]+", "", n)


def pick(row, needles, exclude=()):
    """First value whose HEADER contains one of `needles`, case-insensitively, skipping any header
    containing one of `exclude`.

    Headers drift across the FY2013-FY2027 series — FY2016 heads the name column "Legal Name of
    Organization Requesting Funding", FY2014 heads the amount column "Amount ($" — so exact lookups
    silently return nothing and a whole year goes missing. Substring, never equality.

    `exclude` exists because every workbook carries a SECOND EIN column for the fiscal conduit
    ("FC EIN" through FY2017, "Fiscal Conduit EIN" from FY2018), and a bare "ein" substring will
    happily match it. The grantee's own column happens to come first in all fourteen workbooks, so
    first-match order alone gets the right answer today — but that is column-order luck, not a
    rule, and reading a conduit's EIN as the grantee's would silently misattribute the award.
    """
    for k, v in row.items():
        kl = (k or "").strip().lower()
        if any(x in kl for x in exclude):
            continue
        if any(n in kl for n in needles) and v not in (None, ""):
            return v
    return ""


def absorbed_tail(org):
    """S4: the organization name printed after the LAST dollar figure in a polluted cell.

    FY2016-FY2017 rows lose their boundary as "<neighbour> <ein> * $<amount> <this row's name>",
    so the tail is the row's own grantee. Returns "" unless the tail is a clean name — in the
    FY2018 shape the text continues into purpose prose ("... $10,500.00 Funds will be used to ..."),
    and a prose tail is not a name. Short tails are dropped as acronym debris.
    """
    if not org or not DOLLAR.search(org):
        return ""
    tail = DOLLAR.split(org)[-1].strip(" *,;.")
    return tail if len(tail) >= 4 and is_clean_name(tail) else ""


def read_workbook(path):
    """S1 for one workbook: (EIN, amount) -> {legal name}. Stdlib only; xlsx is a zip of XML.

    sharedStrings is streamed with iterparse — loading it whole stalls on these files. FY2013 ships
    as legacy .xls (an OLE compound file, not a zip) and is therefore not read here at all; the
    glob only takes .xlsx.
    """
    z = zipfile.ZipFile(path)
    shared = []
    with z.open("xl/sharedStrings.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "si":
                shared.append("".join(t.text or "" for t in el.iter(NS + "t")))
                el.clear()

    def cv(c):
        v = c.find(NS + "v")
        if v is None or v.text is None:
            return ""
        return shared[int(v.text)] if c.get("t") == "s" else v.text

    def placed(el):
        """{column index: value} using each cell's DECLARED reference, not its position.

        xlsx omits empty cells entirely, so a row with a blank third column ships four <c> elements
        for six columns. Zipping the header against positions therefore slides every later value
        one field left: the amount lands under the EIN header and the row is silently mis-keyed.
        1,782 rows across FY2014, FY2016, FY2017, FY2024 and FY2026 have at least one omitted cell,
        FY2014 alone 1,494 of 6,611. Reading r="D7" instead of counting is the fix.
        """
        out = {}
        for c in el.findall(NS + "c"):
            m = re.match(r"([A-Z]+)", c.get("r") or "A")
            n = 0
            for ch in m.group(1):
                n = n * 26 + (ord(ch) - 64)
            out[n - 1] = cv(c)
        return out

    hdr, out = None, {}
    with z.open("xl/worksheets/sheet1.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "row":
                cells = placed(el)
                if hdr is None:
                    hdr = cells
                else:
                    d = {h: cells.get(i, "") for i, h in hdr.items()}
                    ein = norm_ein(pick(d, ("tax id", "ein"), exclude=("fc ein", "conduit")))
                    name = (pick(d, ("legal name",)) or "").strip()
                    amt = to_amount(pick(d, ("amount",)) or 0)
                    if ein and amt is not None and is_clean_name(name):
                        out.setdefault((ein, amt), set()).add(name)
                el.clear()
    return out


def council_names():
    """S1: (EIN, amount) -> {legal name}, across every disclosure workbook."""
    lookup = {}
    for p in sorted(glob.glob("source/expense-funding-disclosure/funded_disclosure_FY*.xlsx")):
        for k, names in read_workbook(p).items():
            lookup.setdefault(k, set()).update(names)
    return lookup


def transparency_names():
    """S2: (EIN, amount) -> {organization}, from the transparency designation resolutions.

    Only `designate` rows count. A resolution also carries `rescind` rows with negative amounts —
    the reversal of an earlier designation — and a rescission tells you what an award USED to be,
    not what it is. Keying on the positive designated amount keeps the two apart.
    """
    lookup = {}
    for p in sorted(glob.glob("data/fy*/transparency-resolutions/*_transparency_all.csv")):
        with open(p, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                org = (r.get("organization") or "").strip()
                ein = norm_ein(r.get("ein"))
                amt = to_amount(r.get("amount"))
                if not ein or amt is None or amt <= 0 or not is_clean_name(org):
                    continue
                lookup.setdefault((ein, amt), set()).add(org)
    return lookup


def load_sources():
    """S1, S2, S3 — in this order, because the surname set has to exist before anything reads a
    name through is_clean_name()."""
    global _SURNAMES
    _SURNAMES = build_surnames()
    return council_names(), transparency_names(), corpus_names()


def award_files():
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiatives" not in f and "reconcil" not in f:
            yield f


def fy_of(path):
    """'data/fy18/schedule_c/x.csv' -> 'fy18'."""
    return path.split(os.sep)[1] if os.sep in path else path.split("/")[1]


def corpus_names():
    """S3: (EIN, amount) -> {(fiscal year, organization)} from our own rows that parsed cleanly.

    The fiscal year is carried so callers can drop the row's own year. A clean sibling in the same
    file is the same source document read twice, not a second witness.
    """
    lookup = {}
    for f in award_files():
        fy = fy_of(f)
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                org = (r.get("organization") or "").strip()
                ein = norm_ein(r.get("ein"))
                amt = to_amount(r.get("amount"))
                if ein and amt is not None and is_clean_name(org):
                    lookup.setdefault((ein, amt), set()).add((fy, org))
    return lookup


def surface(names, tally):
    """One surface form for a set of names known to share a canon.

    Most-corroborated first (how many of the agreeing sources spell it that way), then longest,
    then lexicographic. All three are deterministic. The corroboration term matters: the FY2017
    disclosure carries three spellings of New Heritage Theatre Group and length alone would pick
    the inverted "New Heritage Theatre Group, Inc., The" over the form every other source uses."""
    return sorted(names, key=lambda n: (-tally.get(n, 0), -len(n), n))[0]


# Order in which an agreed name is rendered. The Council's own disclosure is the authoritative
# legal name, so it wins the spelling whenever it is one of the agreeing sources.
SOURCE_PRIORITY = ["council_disclosure", "transparency_reso", "corpus_other_year", "absorbed_text"]


def resolve(votes, original):
    """Apply the unanimity rule to {source: {names}}.

    Returns (recovered_name, [agreeing sources]) or None. See the module docstring: an internally
    ambiguous source vetoes rather than abstaining, two sources must speak, and all must agree.
    """
    speaking = {s: ns for s, ns in votes.items() if ns}
    if len(speaking) < 2:
        return None
    canons = set()
    for names in speaking.values():
        c = {canon(n) for n in names}
        if len(c) != 1:
            return None                       # non-unique source: veto, not abstention
        canons |= c
    if len(canons) != 1:
        return None                           # sources disagree
    agreed = canons.pop()
    if not agreed or canon(original).startswith(agreed):
        # Nothing was LOST here. Either the field already holds exactly this name, or it holds this
        # name followed by extra text (FY21's appendices append a program label: "Entertainers for
        # Education Alliance, Inc. -I Will Graduate Program", which the validator flags only because
        # "Will Graduate" trips its `will ` pattern). Overwriting would delete that trailing text —
        # a normalisation, not a recovery, and this script's guarantee is that it destroys nothing.
        return None
    # How many PUBLISHED sources spell it each way. absorbed_text is excluded from the count: it
    # votes on which organization this is, but its spelling comes out of a run-together cell and
    # is routinely clipped ("Leake and Watts Services, Inc" with the period lost), so letting it
    # into the tally elects the damaged form.
    tally = collections.Counter(n for s, names in speaking.items() if s != "absorbed_text"
                                for n in names)
    for s in SOURCE_PRIORITY:
        if s in speaking:
            return surface(speaking[s], tally), sorted(speaking)
    return None


def collect(council, transparency, corpus):
    """Walk every award row, and return (applied, skipped) for the residue rows only."""
    applied, skipped = [], []
    for f in award_files():
        fy = fy_of(f)
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                org = (r.get("organization") or "").strip()
                defect = classify(org)
                if defect is None:
                    continue
                ein = norm_ein(r.get("ein"))
                amt = to_amount(r.get("amount"))
                if not ein or amt is None:
                    skipped.append((f, ln, defect, "no usable (ein, amount) on the row"))
                    continue
                key = (ein, amt)
                votes = {
                    "council_disclosure": set(council.get(key, ())),
                    "transparency_reso": set(transparency.get(key, ())),
                    "corpus_other_year": {o for (y, o) in corpus.get(key, ()) if y != fy},
                    "absorbed_text": {absorbed_tail(org)} - {""},
                }
                got = resolve(votes, org)
                if got is None:
                    spoke = [s for s, v in votes.items() if v]
                    skipped.append((f, ln, defect,
                                    "no two-source agreement (" + (",".join(spoke) or "no source")
                                    + ")"))
                    continue
                name, sources = got
                applied.append(dict(file=f, line=ln, ein=ein, amount=amt, defect=defect,
                                    source="+".join(sources), match_key="ein+amount",
                                    original_organization=org, recovered_organization=name))
    return applied, skipped


def append_crosswalk(rows):
    """Append to the audit trail. It ACCUMULATES and is never overwritten: it is the only record
    that the original text existed, and dropping an earlier pass's entries would leave those edits
    undocumented and irreversible."""
    os.makedirs(os.path.dirname(CROSSWALK), exist_ok=True)
    prior = []
    if os.path.exists(CROSSWALK):
        with open(CROSSWALK, newline="", encoding="utf-8") as fh:
            prior = list(csv.DictReader(fh))
    with open(CROSSWALK, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CROSSWALK_FIELDS)
        w.writeheader()
        for row in sorted(prior + rows, key=lambda r: (r["file"], int(r["line"]))):
            w.writerow({k: row.get(k, "") for k in CROSSWALK_FIELDS})
    return len(prior) + len(rows)


def apply_edits(rows):
    for f in sorted({r["file"] for r in rows}):
        edits = {r["line"]: r["recovered_organization"] for r in rows if r["file"] == f}
        with open(f, newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            fields, data = rdr.fieldnames, list(rdr)
        for ln, name in edits.items():
            data[ln - 2]["organization"] = name
        with open(f, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
        print(f"  applied {len(edits):>3} to {f}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dry-run", action="store_true",
                    help="report only; writes nothing, including the crosswalk")
    args = ap.parse_args(argv)

    council, transparency, corpus = load_sources()
    print(f"council surnames held out of every source: {len(_SURNAMES):,}")
    print(f"S1 council_disclosure  (ein, amount) keys: {len(council):,}")
    print(f"S2 transparency_reso   (ein, amount) keys: {len(transparency):,}")
    print(f"S3 corpus_other_year   (ein, amount) keys: {len(corpus):,}")

    applied, skipped = collect(council, transparency, corpus)
    residue = len(applied) + len(skipped)
    print(f"\nresidue rows in scope                    : {residue:,}")
    for d in ("org_prose", "org_merged", "empty"):
        a = sum(1 for r in applied if r["defect"] == d)
        s = sum(1 for r in skipped if r[2] == d)
        print(f"  {d:<11} resolved {a:>3}   left flagged {s:>3}")
    print(f"\nresolved by two or more agreeing sources : {len(applied):,}")
    print(f"left alone, unresolved                   : {len(skipped):,}")
    for r in applied[:8]:
        print(f"  {fy_of(r['file'])}:{r['line']:<5} {r['source']}")
        print(f"      {r['original_organization'][:64]!r}")
        print(f"   -> {r['recovered_organization'][:64]!r}")

    if args.dry_run:
        # Exit BEFORE any write. A dry run that touched the crosswalk once recorded 16
        # substitutions the data never received, which destroys the one guarantee the file
        # exists to provide: that every line in it happened.
        print("\n--dry-run: nothing written — no CSV touched, crosswalk untouched")
        return 0

    if not applied:
        print("\nnothing to apply; crosswalk untouched")
        return 0
    apply_edits(applied)
    total = append_crosswalk(applied)
    print(f"crosswalk -> {CROSSWALK} ({total:,} total entries, {len(applied):,} from this run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
