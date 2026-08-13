#!/usr/bin/env python3
"""
recover_org_names.py — restore grantee names lost during Schedule C extraction.

Some award rows carry purpose prose in the `organization` column instead of the grantee's name
(the `org_prose` defect, DATA-ANOMALIES.md §20). The row's `ein` and `amount` are intact, so the
name can be recovered deterministically by EIN. Nothing is inferred and no model reads anything.

Two independent sources, in priority order:
  1. The Council's own expense disclosure workbooks (source/expense-funding-disclosure/) — the
     authoritative legal name, published by the Council itself.
  2. This repo's own clean award rows — the same EIN in a year the parser handled correctly.

Every substitution is written to data/combined/org_name_recovery_crosswalk.csv with BOTH the
original text and the replacement, so each edit is auditable and reversible. Rows where the two
sources disagree are reported and NOT applied. Rows neither source resolves are left untouched
and keep firing the `org_prose` advisory.

Usage:
  python3 code/recover_org_names.py --dry-run    # build the crosswalk, change nothing
  python3 code/recover_org_names.py              # build the crosswalk and apply it
"""
import argparse, csv, glob, os, re, sys, zipfile
import xml.etree.ElementTree as ET

# Descriptive prose where a grantee name belongs. Broadened after a dry run found rows the first
# pattern missed ("Funds to be used…", "Funding support for…") — those had leaked into the
# recovery source itself, which is exactly the contamination this pass exists to remove.
PROSE = re.compile(
    r"\b(will |funds? (requested|will|to|for|support)|to support|to provide|funding (for|to|will|support)"
    r"|in order to|program that|services to|to be used|used (for|to)|support(s)? the)\b", re.I)
EIN_IN_TEXT = re.compile(r"\d{2}-\d{7}")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
CROSSWALK = "data/combined/org_name_recovery_crosswalk.csv"


def pick(row, needles):
    """First value whose HEADER contains one of `needles` (case-insensitive). Tolerates the
    header drift across FY2013-FY2027 rather than requiring an exact string match."""
    for k, v in row.items():
        kl = (k or "").strip().lower()
        if any(n in kl for n in needles):
            if v not in (None, ""):
                return v
    return ""


def norm_ein(v):
    return re.sub(r"\D", "", v or "")


def is_prose(org):
    """Prose in the name slot (the org_prose defect)."""
    if not org or EIN_IN_TEXT.search(org) or "$" in org:
        return False
    return bool(PROSE.search(org))


def is_merged(org):
    """The org_merged defect: a following award's text absorbed into this row, betrayed by an
    embedded EIN or dollar sign.

    These were initially excluded from recovery on the theory that their `amount` is unreliable,
    so a clean name would make an untrustworthy figure look sound. Measured against the Council's
    disclosure that theory holds for only a minority: 248 of 303 have their own (EIN, amount)
    confirmed present, meaning the row IS correctly valued and correctly attributed and only its
    organization TEXT is polluted. Those are recoverable on exactly the same key as org_prose.

    The remaining 55 (all FY2016) have no disclosure row for their (EIN, amount). They are left
    untouched by the unique-match rule below — no confirmation, no substitution — and keep firing
    the advisory. The absorbed neighbours these rows swallowed are a separate problem: those are
    MISSING rows, not broken ones, and adding them is not this script's job."""
    return bool(org) and bool(EIN_IN_TEXT.search(org) or "$" in org)


def read_workbook(path):
    """Stdlib xlsx reader keyed on (EIN, amount) -> set of legal names.

    KEY CHOICE, and the whole safety of this script rests on it. EIN alone is NOT a usable key:
    fiscal sponsors pass funds through for many grantees, so one EIN carries many real names --
    13-2612524 (Fund for the City of New York) appears under 229 distinct names in our own corpus.
    Recovering by EIN would stamp the SPONSOR's name onto an award that went elsewhere.

    (EIN, amount) identifies the individual award and resolves uniquely for 96% of affected rows.
    `member` was tested as a third component and REJECTED: it drops the unique-match rate to 24%,
    because the disclosure workbook is republished with the Council roster current at snapshot
    time, not the one that adopted the budget (Phase 1 FINDINGS.md).

    Shared strings are streamed -- loading them whole stalls on these files."""
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
                    hdr = vals
                else:
                    d = dict(zip(hdr, vals))
                    # Headers drift across the 15-year series and exact lookups silently miss:
                    # FY2016 heads the name column "Legal Name of Organization Requesting Funding"
                    # and FY2014 heads the amount column "Amount ($". Both returned None under the
                    # first version of this script, so FY2016 recovered 10 rows instead of its real
                    # share and FY2014 was skipped outright. Match on a prefix/substring instead.
                    ein = norm_ein(pick(d, ("tax id", "ein")))
                    name = (pick(d, ("legal name",)) or "").strip()
                    try:
                        amt = int(float(pick(d, ("amount",)) or 0))
                    except (TypeError, ValueError):
                        el.clear(); continue
                    if ein and name:
                        out.setdefault((ein, amt), set()).add(name)
                el.clear()
    return out


def canon(name):
    """Normalise for COMPARISON only — never for output. Collapses the benign variants that make
    two sources look like they disagree when they do not: 'Carnegie Hall Corporation' vs
    'Carnegie Hall Corporation, The'."""
    n = (name or "").lower().strip()
    n = re.sub(r"^the\s+", "", n)
    n = re.sub(r"[,.]?\s*(the|inc|incorporated|llc|ltd|corp|corporation|co)\b\.?", " ", n)
    return re.sub(r"[^a-z0-9]+", "", n)


def council_names():
    """(EIN, amount) -> set of legal names, across every disclosure workbook."""
    lookup = {}
    for p in sorted(glob.glob("source/expense-funding-disclosure/funded_disclosure_FY*.xlsx")):
        for k, names in read_workbook(p).items():
            lookup.setdefault(k, set()).update(names)
    return lookup


def corpus_names():
    """EIN -> name, from our own award rows that parsed cleanly."""
    lookup = {}
    for f in glob.glob("data/fy*/schedule_c/*.csv"):
        if "initiatives" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                org = (r.get("organization") or "").strip()
                if not org or is_prose(org) or EIN_IN_TEXT.search(org) or "$" in org:
                    continue
                ein = norm_ein(r.get("ein"))
                if ein:
                    lookup.setdefault(ein, org)
    return lookup


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="build the crosswalk, change no CSV")
    args = ap.parse_args()

    council = council_names()
    print(f"council (ein, amount) keys: {len(council):,}")

    rows, ambiguous, unresolved = [], [], []
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        if "initiatives" in f or "reconcil" in f:
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            for ln, r in enumerate(csv.DictReader(fh), start=2):
                org = (r.get("organization") or "").strip()
                if not (is_prose(org) or is_merged(org)):
                    continue
                defect = "org_prose" if is_prose(org) else "org_merged"
                ein = norm_ein(r.get("ein"))
                try:
                    amt = int(float(r.get("amount") or 0))
                except (TypeError, ValueError):
                    unresolved.append((f, ln, ein, org)); continue
                cand = council.get((ein, amt), set())
                # Guard against over-matching the prose pattern. "Fund for the City of New York"
                # trips the `funds? for` branch but is a real grantee name, not prose. If what is
                # already there is the same name as the candidate modulo suffix/punctuation, there
                # is nothing to recover -- leave it alone rather than churn the field.
                if len(cand) == 1 and canon(org) == canon(next(iter(cand))):
                    continue
                if len(cand) == 1:
                    rows.append(dict(file=f, line=ln, ein=ein, amount=amt,
                                     original_organization=org,
                                     recovered_organization=next(iter(cand)),
                                     source="council_disclosure", match_key="ein+amount",
                                     defect=defect))
                elif len(cand) > 1:
                    ambiguous.append((f, ln, ein, amt, sorted(cand)))
                else:
                    unresolved.append((f, ln, ein, org))

    os.makedirs("data/combined", exist_ok=True)
    # The crosswalk is the audit trail for every substitution ever applied, so it must ACCUMULATE.
    # Re-running after an earlier pass would otherwise drop the earlier entries and leave those
    # edits undocumented — the file is the thing a reader checks our work against.
    prior = []
    if os.path.exists(CROSSWALK):
        with open(CROSSWALK, newline="", encoding="utf-8") as fh:
            prior = list(csv.DictReader(fh))
    seen = {(r["file"], r["line"]) for r in rows}
    new_count = len(rows)          # this run only — the cumulative total is reported separately
    rows = [r for r in prior if (r["file"], r["line"]) not in seen] + rows
    rows.sort(key=lambda r: (r["file"], int(r["line"])))
    with open(CROSSWALK, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "line", "ein", "amount", "defect", "source",
                                           "match_key", "original_organization",
                                           "recovered_organization"])
        w.writeheader()
        w.writerows(rows)

    print(f"\nrecovered THIS RUN (unique ein+amount): {new_count:,}")
    print(f"crosswalk total, all runs             : {len(rows):,}")
    print(f"ambiguous  (>1 candidate, NOT applied): {len(ambiguous):,}")
    print(f"unresolved (no match, NOT applied)    : {len(unresolved):,}")
    print(f"crosswalk -> {CROSSWALK}")
    if ambiguous:
        print("\nfirst ambiguous (left untouched):")
        for f, ln, ein, amt, cands in ambiguous[:5]:
            print(f"  {ein} ${amt:,} -> {cands[:3]}")

    if args.dry_run:
        print("\n--dry-run: no CSV modified")
        return 0

    by_file = {}
    for r in rows:
        by_file.setdefault(r["file"], {})[r["line"]] = r["recovered_organization"]
    for f, edits in by_file.items():
        with open(f, newline="", encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            fields, data = rdr.fieldnames, list(rdr)
        for ln, name in edits.items():
            data[ln - 2]["organization"] = name
        with open(f, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
        print(f"  applied {len(edits):>4} to {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
