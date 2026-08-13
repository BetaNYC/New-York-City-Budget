#!/usr/bin/env python3
"""
fix_member_bleed.py — peel a bled council-member surname off the front of an organization name.

Schedule C award rows sometimes carry the sponsoring member's surname glued to the head of the
grantee's name, bled in from the neighbouring column when the PDF's row boundaries collapsed:

    member ''          organization 'Eugene 71st Precinct Community Council, Inc.'
    member 'Brooks-'   organization 'Powers 2020 Vision for Schools, Inc.'

DATA-ANOMALIES.md §14 and §16 record this class as RESOLVED — but only for the two parsers those
sections cover (Schedule C's "Delegation" sponsor token, and the Transparency Resolution parser's
"<Borough> Delegation"). Neither touches a bled *personal* surname in the schedule_c award stream,
where it is still present corpus-wide.

WHY THIS CANNOT BE A STRING RULE. The leading token is frequently a legitimate part of the name:
"Brooklyn Book Bodega", "Queens Borough Public Library", "Staten Island Children's Museum",
"Louis Armstrong House Museum", "Rose Center for Earth and Space" — every one of those leads with
a value that also appears in the `member` column. Stripping on the surname alone would vandalise
3,425 correct names to repair 1,083 broken ones. So the surname set only *nominates* a row; nothing
is stripped without independent confirmation, and there is exactly one confirming source: the
Council's own disclosure workbook must hold exactly one legal name for this row's (EIN, amount),
and it must equal the stripped remainder. (EIN alone is not a usable key: fiscal sponsors pass
funds through for many grantees — 13-2612524 carries 229 distinct names here. `member` is
deliberately NOT part of the key; the workbooks are republished with the roster current at snapshot
time, which drops match rates from 96% to 24%.)

The FULL organization string is checked against the same evidence first: if the disclosure confirms
the name as printed, the leading token is real and the row is left alone. Anything that resolves to
zero or to more than one candidate is left flagged — a flagged row is a correct outcome, a
plausibly-filled one is not.

ONE SOURCE ONLY, AND WHY. A second rule was written and then deleted: where the disclosure has no
row, fall back to a name this corpus already carries cleanly for the same EIN. It earned 4 fixes
out of 1,087 and two of them were WRONG. EIN 13-5562989 is "Hudson Guild", and this corpus holds
ten rows on which the parser made the OPPOSITE mistake — `member` = "Hudson", `organization` =
"Guild". Those became the EIN's only "clean" name, so the fallback confidently truncated a real
organization to "Guild". Our own output is not independent evidence about our own defects. The
Council's workbook is; nothing else here is.

The removed surname is recorded in the crosswalk's `match_key`, and `original_organization` holds
the verbatim original, so every edit is reversible from the audit trail alone.

WHERE THE SURNAME GOES. Deleting it outright would destroy the row's only trace of who sponsored
the award — on 166 rows the `member` column is empty and the bled token is the sole attribution.
So, exactly as `peel_delegation()` does for the Transparency Resolutions (DATA-ANOMALIES.md §16),
the surname is recovered INTO `member` when and only when no member was already resolved. An
existing value is never overwritten, including the "Speaker" that most of these rows carry: the
Speaker's co-sponsorship is real, and choosing between the two is a judgement this script has no
grounds to make. Rows that gained a member say so in `match_key` (`|member<-Eugene`).

Usage:
  python3 code/fix_member_bleed.py --dry-run   # report only; writes NOTHING, not even the crosswalk
  python3 code/fix_member_bleed.py             # apply, and append to the crosswalk
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

# Values that appear in the `member` column but name nobody: parser residue ("The", "Center",
# "Placement", "Program") or a role rather than a person ("Speaker"). Peeling these would be
# indefensible whatever the evidence said, so they never enter the set.
NOT_SURNAMES = {"speaker", "the", "center", "placement", "program", "delegation",
                "various", "citywide", "staten", "island"}

# Geography, not a roster — the five boroughs do not change with an election, which is why a
# literal is honest here and a member list would not be. They sponsor Boroughwide designations and
# print in `member` as "Brooklyn" or "Bronx Delegation", so they bleed exactly like a surname.
# They also open a great many REAL names ("Brooklyn Book Bodega", "Queens Borough Public Library"),
# which is exactly what the confirmation step is for: 3,088 borough-led names are confirmed as
# printed and left alone, 115 are confirmed as bleeds and peeled.
BOROUGHS = {"Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"}

# A member value we are willing to treat as a name: letters plus the punctuation real surnames
# carry (De La Rosa, Brooks-Powers, P. Sanchez, O'Neill).
NAMEISH = re.compile(r"^[A-Za-z][A-Za-z .'\-]*$")


def award_files(root="data"):
    """Every award-bearing schedule_c CSV. Initiatives and reconciliation files carry no
    organization column and are skipped."""
    return sorted(f for f in glob.glob(os.path.join(root, "fy*", "schedule_c", "*.csv"))
                  if "initiativ" not in f and "reconcil" not in f)


def pick(row, needles):
    """First value whose HEADER contains one of `needles`, case-insensitively. The disclosure
    headers drift across FY2013-FY2027 — FY2016 heads the name column 'Legal Name of Organization
    Requesting Funding', FY2014 heads the amount column 'Amount ($' — so an exact lookup silently
    returns nothing for whole fiscal years."""
    for k, v in row.items():
        if any(n in (k or "").strip().lower() for n in needles) and v not in (None, ""):
            return v
    return ""


def norm_ein(v):
    return re.sub(r"\D", "", v or "")


def canon(name):
    """Normalise for COMPARISON only, never for output. Collapses the benign variants that make
    two sources look like they disagree when they do not ('Carnegie Hall Corporation' vs
    'Carnegie Hall Corporation, The')."""
    n = (name or "").lower().strip()
    n = re.sub(r"^the\s+", "", n)
    n = re.sub(r"[,.]?\s*(the|inc|incorporated|llc|ltd|corp|corporation|co)\b\.?", " ", n)
    return re.sub(r"[^a-z0-9]+", "", n)


def read_workbook(path):
    """Stdlib xlsx reader -> {(ein, amount): {legal name, ...}}.

    xlsx is a zip of XML. sharedStrings is streamed with iterparse because loading it whole stalls
    on these files. `tax id`/`ein` must not match the 'FC EIN' (fiscal conduit) column, which names
    the pass-through sponsor rather than the grantee — hence the explicit exclusion below."""
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

    hdr, out = None, {}
    with z.open("xl/worksheets/sheet1.xml") as f:
        for _, el in ET.iterparse(f, events=("end",)):
            if el.tag == NS + "row":
                vals = [cv(c) for c in el.findall(NS + "c")]
                if hdr is None:
                    # Blank the conduit column before any substring match can reach it.
                    hdr = ["" if "fc ein" in (h or "").lower() else h for h in vals]
                else:
                    d = dict(zip(hdr, vals))
                    ein = norm_ein(pick(d, ("tax id", "ein")))
                    name = (pick(d, ("legal name",)) or "").strip()
                    try:
                        amt = int(float(pick(d, ("amount",)) or 0))
                    except (TypeError, ValueError):
                        el.clear()
                        continue
                    if ein and name:
                        out.setdefault((ein, amt), set()).add(name)
                el.clear()
    return out


def council_names(root="source/expense-funding-disclosure"):
    """Return (per_year, pooled) lookups of (EIN, amount) -> {legal name}.

    Kept per year as well as pooled because (EIN, amount) is unique within a year but NOT across
    the 15-year series: the same grantee draws the same round number in two different years, and an
    organization that renamed itself (MFY Legal Services -> Mobilization for Justice) then presents
    as two conflicting candidates for one key. Consulting the row's own fiscal year first removes
    that false conflict; the pooled lookup is only a fallback for keys its own year does not carry.
    """
    per_year, pooled = {}, {}
    for p in sorted(glob.glob(os.path.join(root, "funded_disclosure_FY*.xlsx"))):
        m = re.search(r"FY(\d{4})", p)
        if not m:
            continue
        year = int(m.group(1))
        per_year[year] = tbl = read_workbook(p)
        for k, names in tbl.items():
            pooled.setdefault(k, set()).update(names)
    return per_year, pooled


def file_year(path):
    """data/fy16/schedule_c/... -> 2016. None if the path carries no fyNN segment."""
    m = re.search(r"[/\\]fy(\d{2})[/\\]", path)
    return 2000 + int(m.group(1)) if m else None


def build_surnames(files):
    """Council-member surnames DERIVED FROM THE DATA — never a hardcoded roster, which goes stale
    every election. Sources are the `member` column of the award files themselves and the
    `council_member` column of the transparency files, which is cleaner.

    Full values are kept ('De La Rosa', 'Brooks-Powers') so a multi-token surname is peeled whole.
    Their PARTS are kept too, because the bleed routinely splits a compound name across the two
    columns — 'Brooks-' stays in `member` while 'Powers ...' leads the organization. A part must be
    >= 4 letters, which keeps particles ('De', 'La', 'Van') and initials out of the set."""
    out = set(BOROUGHS)
    for path in files:
        with open(path, newline="", encoding="utf-8") as fh:
            rd = csv.DictReader(fh)
            col = "member" if "member" in (rd.fieldnames or []) else "council_member"
            if col not in (rd.fieldnames or []):
                continue
            for r in rd:
                v = (r.get(col) or "").strip().strip(".,")
                if not v or not NAMEISH.match(v) or v.lower() in NOT_SURNAMES:
                    continue
                if len(v) >= 3:
                    out.add(v)
                for part in re.split(r"[\s\-]+", v):
                    part = part.strip(".'")
                    if len(part) >= 4 and part.isalpha() and part.lower() not in NOT_SURNAMES:
                        out.add(part)
    return out


def surname_sources(root="data"):
    """Award files plus the transparency files, whose member column is the cleaner of the two."""
    return award_files(root) + sorted(glob.glob(os.path.join(root, "fy*", "transparency", "*.csv")))


def _lead(org, surnames):
    """Longest surname immediately followed by ' ' or ','. Longest-first matters: 'De La Rosa
    Community League' must peel 'De La Rosa', not stop at a shorter member value prefixing it."""
    best = None
    for s in surnames:
        if org.startswith(s + " ") or org.startswith(s + ","):
            if best is None or len(s) > len(best):
                best = s
    return best


def peel(org, surnames):
    """Return (removed, remainder) for the run of council surnames leading `org`, else (None, None).

    A single bled sponsor is the common case ('Eugene 71st Precinct…'), but co-sponsored awards
    print the whole list and bleed all of it — 'Brannan, Lander, Maisel Brooklyn Alliance, Inc.'
    So the run is consumed while each comma-separated element is itself a known surname, and stops
    dead at the first element that is not. 'Ampry-Samuel, BLAC, Cornegy Bedford Stuyvesant…' peels
    only 'Ampry-Samuel,' and then halts on 'BLAC' — leaving a remainder no source will confirm,
    which is the intended outcome: a partial peel resolves to nothing and the row stays flagged."""
    n, rest = 0, org
    while True:
        s = _lead(rest, surnames)
        if s is None:
            break
        tail = rest[len(s):]
        stripped = tail.lstrip(",").strip().lstrip("-–—").strip()
        n, rest = len(org) - len(stripped), stripped
        if not tail.startswith(","):      # a space, not a comma: the sponsor list ends here
            break
    if not n or len(rest) < 3:
        return None, None
    # Verbatim prefix, so `original` is always `removed` + whitespace + `recovered` — the peel is
    # reversible by string arithmetic alone, with no re-derivation of the surname set.
    return org[:n].strip(), rest


def _fix(f, ln, row, ein, amt, sur, org, rest, source, key):
    """One planned substitution. `member` is filled from the peeled surname only when the row has
    no member at all — see the module docstring; an existing value, "Speaker" included, stands.
    A co-sponsor LIST is never written to `member`: that column holds one surname everywhere else,
    and picking one of three would be the guess this script exists to avoid."""
    one = sur.rstrip(",")                       # a trailing comma is punctuation, not a co-sponsor
    take_member = not (row.get("member") or "").strip() and "," not in one
    return dict(file=f, line=ln, ein=ein, amount=amt, defect="member_bleed", source=source,
                match_key=f"{key}|removed={sur}" + (f"|member<-{one}" if take_member else ""),
                original_organization=org, recovered_organization=rest,
                _member=one if take_member else None)


def plan(root="data", disclosure_root="source/expense-funding-disclosure"):
    """Decide every row's fate without touching anything. Returns (fixes, stats, samples)."""
    files = award_files(root)
    surnames = build_surnames(surname_sources(root))
    per_year, pooled = council_names(disclosure_root)

    fixes = []
    stats = collections.Counter()
    samples = collections.defaultdict(list)

    for f in files:
        own = per_year.get(file_year(f), {})
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                org = (r.get("organization") or "").strip()
                if not org:
                    continue
                sur, rest = peel(org, surnames)
                if not sur:
                    continue
                stats["candidates"] += 1
                ein = norm_ein(r.get("ein"))
                try:
                    amt = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    amt = None
                key = (ein, amt) if (ein and amt is not None) else None
                cand = own.get(key) or pooled.get(key) or set()
                scope = "FY%d" % file_year(f) if key in own else "any-year"

                if not cand:
                    stats["unresolved"] += 1
                    samples["unresolved"].append((f, ln, sur, org, ""))
                    continue

                # The disclosure knows this exact award. It is the arbiter, both ways. Collapse to
                # canonical form first: "Asian Americans for Equality" and "Asian Americans For
                # Equality, Inc." are two spellings of one answer, not two candidates, and treating
                # them as a conflict would forfeit real fixes.
                cset = {canon(c) for c in cand}
                if canon(org) in cset:
                    stats["confirmed_as_printed"] += 1
                    samples["confirmed_as_printed"].append((f, ln, sur, org, ""))
                elif len(cset) == 1 and canon(rest) in cset:
                    fixes.append(_fix(f, ln, r, ein, amt, sur, org, rest,
                                      "council_disclosure", f"ein+amount@{scope}"))
                    stats["fix_disclosure"] += 1
                    samples["fix_disclosure"].append((f, ln, sur, org, rest))
                else:
                    stats["disclosure_disagrees"] += 1
                    samples["disclosure_disagrees"].append(
                        (f, ln, sur, org, " | ".join(sorted(cand))[:70]))

    stats["surnames"] = len(surnames)
    stats["council_keys"] = len(pooled)
    return fixes, stats, samples


def apply_fixes(fixes):
    """Rewrite the `organization` cell of the planned rows — and `member`, where the plan says the
    row had none. No other column is touched, in any row."""
    by_file = collections.defaultdict(dict)
    for x in fixes:
        by_file[x["file"]][x["line"]] = x
    for f, edits in sorted(by_file.items()):
        with open(f, newline="", encoding="utf-8") as fh:
            rd = csv.DictReader(fh)
            fields, data = rd.fieldnames, list(rd)
        for ln, x in edits.items():
            data[ln - 2]["organization"] = x["recovered_organization"]
            if x.get("_member") and "member" in fields:
                data[ln - 2]["member"] = x["_member"]
        with open(f, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
        print(f"  applied {len(edits):>4} to {f}")


CROSSWALK_FIELDS = ["file", "line", "ein", "amount", "defect", "source", "match_key",
                    "original_organization", "recovered_organization"]


def append_crosswalk(fixes, path=CROSSWALK):
    """Append this run's substitutions. The crosswalk is the audit trail for every edit ever made
    to this corpus, so it must ACCUMULATE — an overwrite would leave earlier edits undocumented,
    which is the one guarantee the file exists to provide."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    prior = []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as fh:
            prior = list(csv.DictReader(fh))
    rows = prior + fixes
    rows.sort(key=lambda r: (r["file"], int(r["line"])))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CROSSWALK_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CROSSWALK_FIELDS})
    return len(prior), len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dry-run", action="store_true",
                    help="report only; writes nothing, not even the crosswalk")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--samples", type=int, default=6, help="example rows to print per bucket")
    a = ap.parse_args(argv)

    fixes, stats, samples = plan(a.data_dir)

    print(f"surnames derived from data      : {stats['surnames']}")
    print(f"council (ein, amount) keys      : {stats['council_keys']:,}")
    print(f"rows leading with a surname     : {stats['candidates']:,}")
    print("-" * 62)
    print(f"FIX   disclosure confirms the peel : {stats['fix_disclosure']:,}")
    print(f"KEEP  disclosure confirms as printed: {stats['confirmed_as_printed']:,}")
    print(f"LEAVE disclosure names something else: {stats['disclosure_disagrees']:,}")
    print(f"LEAVE no disclosure row for the award: {stats['unresolved']:,}")
    print("-" * 62)
    print(f"TOTAL to change                 : {len(fixes):,}")
    print(f"  of those, also gaining `member`: "
          f"{sum(1 for x in fixes if x.get('_member')):,}")

    for bucket in ("fix_disclosure", "disclosure_disagrees", "unresolved"):
        rows = samples.get(bucket, [])[:a.samples]
        if not rows:
            continue
        print(f"\n{bucket} (first {len(rows)}):")
        for f, ln, sur, org, other in rows:
            print(f"  {f.split('/')[1]}:{ln:<6} -{sur!r:<16} {org[:52]!r}")
            if other:
                print(f"{'':>26}-> {other[:52]!r}")

    if a.dry_run:
        # Exit BEFORE any write. A dry run that touched the crosswalk once recorded 16
        # substitutions the data never received — phantom entries in the file whose whole job is
        # to prove nothing was destroyed.
        print("\n--dry-run: nothing written — no CSV, no crosswalk")
        return 0

    if not fixes:
        print("\nnothing to apply")
        return 0

    apply_fixes(fixes)
    before, after = append_crosswalk(fixes)
    print(f"crosswalk -> {CROSSWALK} ({before:,} -> {after:,} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
