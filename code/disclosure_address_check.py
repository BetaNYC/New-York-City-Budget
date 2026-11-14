#!/usr/bin/env python3
"""Check the disclosure's grantee mailing addresses against the City's address file, PAD
(GitHub #247), for the rows whose ZIP the Census check (#70, code/zcta_states.py) could not
settle: `ambiguous_extra_digit` (six digits printed, several one-digit deletions are real ZIPs)
and `state_mismatch` (a real ZIP, but in another state than the row's state cell).

Offline, with no geocoding service: DCP Planning Labs' normalized PAD file, the file NYC's
GeoSearch is built from (https://planninglabs.nyc3.digitaloceanspaces.com/geosearch-data/
latest/labs-geosearch-pad-normalized.csv; about 700 MB, public). It is never committed: build
mode reads a local copy (CSV or the Parquet made from it) and writes only the small result,
data/disclosure_address_check.csv, with the PAD version and the file's sha256 on every row.

The method is BetaNYC's NYC address matching reference (betanyc-ai-workspace
team/reference/nyc-address-matching.md, §3 and §5): an exact match on (house number,
normalized street, borough), the street normalized the same way on both sides, after cleanup
rules on the printed address. A row is settled only when the address matches exactly ONE PAD
address (one ZIP and one tax lot) AND that ZIP agrees with what the row printed:

  ambiguous_extra_digit -> repaired_by_address   when PAD's ZIP is one of zip_candidates; zip =
                                                 that ZIP, the candidates are kept
  state_mismatch        -> nyc_address_confirmed when PAD's ZIP is the row's own zip; zip is
                                                 unchanged: the printed state cell is wrong

Every other row keeps its status and says why here (no borough, no match, several matches, or
PAD's ZIP differs from what was printed). The borough comes from the printed city when it names
one, else from the ZIP (or every candidate ZIP) when all point to one borough. Never a guess:
nothing printed is rewritten, and nothing changes without a match. These are mailing addresses,
not where services were delivered.

Run:
  python3 code/disclosure_address_check.py --pad ~/.cache/betanyc-pad/pad-26c.parquet --write
  python3 code/disclosure_address_check.py --check     (no PAD needed; CI)
"""

import argparse
import csv
import glob
import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "disclosure_address_check.csv")
PAD_URL = ("https://planninglabs.nyc3.digitaloceanspaces.com/geosearch-data/latest/"
           "labs-geosearch-pad-normalized.csv")

FIELDS = ["fiscal_year", "source_row", "zcta_status", "postal_code", "zip_candidates",
          "borough", "borough_from", "house_number", "street_key", "rules", "pad_matches",
          "pad_zip", "pad_bbl", "result", "reason", "pad_version", "pad_sha256"]
CHECKED = ("ambiguous_extra_digit", "state_mismatch")
SETTLED = {"ambiguous_extra_digit": "repaired_by_address", "state_mismatch": "nyc_address_confirmed"}

# ---------------------------------------------------------------- normalization (§3)

BORO_OF_CITY = {"NEW YORK": "1", "MANHATTAN": "1", "NEW YORK CITY": "1", "BRONX": "2",
                "THE BRONX": "2", "BROOKLYN": "3", "STATEN ISLAND": "5"}
# ZIP prefixes wholly in one borough (Queens' mailing cities are neighborhoods, so its ZIPs decide).
ZIP3_BORO = {"100": "1", "101": "1", "102": "1", "104": "2", "112": "3", "103": "5",
             "110": "4", "111": "4", "113": "4", "114": "4", "116": "4"}
BORO_NAME = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}
SUFFIX = {"STREET": "ST", "STR": "ST", "STREAT": "ST", "AVENUE": "AVE", "AV": "AVE", "AVENU": "AVE",
          "BOULEVARD": "BLVD", "ROAD": "RD", "PLACE": "PL", "PARKWAY": "PKWY", "PKY": "PKWY",
          "DRIVE": "DR", "LANE": "LN", "COURT": "CT", "TERRACE": "TER", "SQUARE": "SQ",
          "HIGHWAY": "HWY", "EXPRESSWAY": "EXPY", "EXPWY": "EXPY", "TURNPIKE": "TPKE",
          "PLAZA": "PLZ", "CONCOURSE": "CONC"}
TYPES = set(SUFFIX.values()) | {"ST", "AVE", "BLVD", "RD", "PL", "PKWY", "DR", "LN", "CT", "TER",
                                "SQ", "HWY", "EXPY", "TPKE", "PLZ", "CONC"}
DIRS = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
WORD_ORD = {"FIRST": "1", "SECOND": "2", "THIRD": "3", "FOURTH": "4", "FIFTH": "5", "SIXTH": "6",
            "SEVENTH": "7", "EIGHTH": "8", "NINTH": "9", "TENTH": "10", "ELEVENTH": "11",
            "TWELFTH": "12"}
_ORD = re.compile(r"\b(\d+)(ST|ND|RD|TH)\b")
_UNIT = re.compile(r"(\s*#.*$|\b(FL|FLR|FLOOR|STE|SUITE|RM|ROOM|APT|UNIT|BSMT|BASEMENT)\b.*$)")
_NUM = r"\d+[A-Z]?(?:-\d+[A-Z]?)?"


def norm_street(s):
    """Upper case, punctuation out, '45TH' -> '45', 'THIRD' -> '3', 'STREET' -> 'ST',
    'WEST' -> 'W'; words after the street type dropped ('8 AVE 5' -> '8 AVE'), unless the type
    is the first word ('AVE P'). Applied the same way to PAD's streets and to ours."""
    s = re.sub(r"[.,']", " ", (s or "").upper())
    s = _ORD.sub(r"\1", " ".join(s.split()))
    out = []
    for w in s.split(" "):
        if w:
            w = WORD_ORD.get(w, w)
            w = DIRS.get(w, w)
            out.append(SUFFIX.get(w, w))
    for i, w in enumerate(out):
        if i > 0 and w in TYPES:
            return " ".join(out[: i + 1])
    return " ".join(out)


def split_address(a):
    """(house number, street key, rules) for a printed address line, or (None, None, rules).
    Cleanup (§5): text after the first comma, unit text ('FL', 'SUITE', '#455'), and a name
    printed before the house number ('SOBRO 555 BERGEN AVENUE')."""
    rules = []
    a = " ".join((a or "").upper().split())
    if "," in a:
        a, rules = a.split(",")[0], rules + ["after_comma_dropped"]
    b = _UNIT.sub("", a).strip()
    if b != a:
        rules.append("unit_dropped")
    m = re.fullmatch(rf"({_NUM})\s+(.+)", b)
    if not m:
        m = re.fullmatch(rf"[A-Z][A-Z&' ]*?\s({_NUM})\s+(.+)", b)
        if m:
            rules.append("name_before_number")
    if not m:
        return None, None, rules
    street = norm_street(m.group(2))
    if not street or street in TYPES:      # a street that is only a type is no street (§5)
        return None, None, rules
    return m.group(1), street, rules


def borough_of(row):
    """(borough digit, how) from the printed city, else from the ZIP or every candidate ZIP."""
    c = " ".join((row["city"] or "").upper().split())
    if c in BORO_OF_CITY:
        return BORO_OF_CITY[c], "city"
    zs = [row["zip"]] if row["zip"] else [z for z in row["zip_candidates"].split(";") if z]
    bs = {ZIP3_BORO.get(z[:3]) for z in zs}
    if zs and len(bs) == 1 and None not in bs:
        return bs.pop(), "zip"
    return "", ""


# ---------------------------------------------------------------- the decision

def decide(row, hits):
    """row: a disclosure CSV row (status from the Census check); hits: the distinct
    (pad_zip, pad_bbl) of PAD addresses matching the row's key, or None when the row has no key.
    -> (result, reason, pad_zip, pad_bbl). result is the settled status or 'left'."""
    st = row["zip_status"]
    if hits is None:
        return "left", "no house number and street could be read, or no NYC borough", "", ""
    if not hits:
        return "left", "no PAD address matches", "", ""
    if len(hits) > 1:
        return "left", f"{len(hits)} PAD addresses match; none picked", "", ""
    z, bbl = hits[0]
    if st == "ambiguous_extra_digit":
        if z in row["zip_candidates"].split(";"):
            return SETTLED[st], "one PAD address; its ZIP is one of the candidates", z, bbl
        return "left", "one PAD address, but its ZIP is not one of the candidates", z, bbl
    if st == "state_mismatch":
        if z == row["zip"]:
            return SETTLED[st], "one NYC address with this ZIP; the printed state names another state", z, bbl
        return "left", "one PAD address, but its ZIP differs from the printed ZIP", z, bbl
    raise ValueError(f"not a checked status: {st}")


def apply(zip_, status, cands, check):
    """The row's (zip, zip_status, zip_candidates) after its committed check row, if settled.
    Refuses a check row that does not fit the row (a stale file)."""
    if check is None or check["result"] == "left":
        return zip_, status, cands
    if status != check["zcta_status"] or SETTLED.get(status) != check["result"]:
        raise ValueError(f"address check {check['fiscal_year']}/{check['source_row']} is stale: "
                         f"row is {status}, check says {check['zcta_status']} -> {check['result']}")
    if status == "ambiguous_extra_digit":
        if check["pad_zip"] not in cands.split(";"):
            raise ValueError(f"address check {check['fiscal_year']}/{check['source_row']}: "
                             f"{check['pad_zip']} is not a candidate")
        return check["pad_zip"], "repaired_by_address", cands
    if check["pad_zip"] != zip_:
        raise ValueError(f"address check {check['fiscal_year']}/{check['source_row']}: ZIP differs")
    return zip_, "nyc_address_confirmed", cands


# ---------------------------------------------------------------- files

def disclosure_rows(root=ROOT):
    """The rows to check, from the committed per-year CSVs, with the status the Census check
    alone gives (a settled row is read back to its Census status, so the build is stable)."""
    back = {v: k for k, v in SETTLED.items()}
    out = []
    for f in sorted(glob.glob(os.path.join(root, "data", "fy*", "expense_disclosure", "*_expense_awards.csv"))):
        with open(f, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                st = back.get(r["zip_status"], r["zip_status"])
                if st in CHECKED:
                    r = dict(r, zip_status=st, zip=(r["zip"] if st == "state_mismatch" else ""))
                    out.append(r)
    return sorted(out, key=lambda r: (int(r["fiscal_year"]), int(r["source_row"])))


def load(path=OUT):
    """{(fiscal_year, source_row): check row} from the committed file ({} if absent)."""
    if not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["fiscal_year"], r["source_row"]): r for r in csv.DictReader(f)}


def text(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(pad_path, rows, pad_sha256):
    """Match `rows` against the PAD file at `pad_path` (CSV or Parquet). Needs duckdb."""
    import duckdb  # only in build mode; CI and the tests never load PAD
    con = duckdb.connect()
    src = (f"read_parquet('{pad_path}')" if pad_path.endswith(".parquet") else
           f"(SELECT number, street, zipcode, json_extract_string(addendum_json_pad, '$.bbl') AS bbl, "
           f"json_extract_string(addendum_json_pad, '$.version') AS version "
           f"FROM read_csv('{pad_path}', all_varchar=true, header=true))")
    con.execute(f"CREATE TABLE pad AS SELECT upper(number) AS num, street, zipcode, bbl, version, "
                f"substr(bbl, 1, 1) AS boro FROM {src} WHERE number IS NOT NULL AND number <> ''")
    versions = [v for (v,) in con.execute("SELECT DISTINCT version FROM pad").fetchall()]
    if len(versions) != 1:
        raise SystemExit(f"PAD file carries {len(versions)} versions: {versions}")
    streets = [s for (s,) in con.execute("SELECT DISTINCT street FROM pad").fetchall()]
    con.execute("CREATE TABLE sn (street VARCHAR, nstreet VARCHAR)")
    con.executemany("INSERT INTO sn VALUES (?, ?)", [(s, norm_street(s)) for s in streets])
    con.execute("CREATE TABLE padn AS SELECT p.num, s.nstreet, p.boro, p.zipcode, p.bbl FROM pad p JOIN sn s USING (street)")
    out = []
    for r in rows:
        num, street, rules = split_address(r["address1"])
        boro, how = borough_of(r)
        hits = None
        if num and boro:
            hits = con.execute("SELECT DISTINCT zipcode, bbl FROM padn WHERE num = ? AND nstreet = ? AND boro = ? "
                               "ORDER BY 1, 2", [num, street, boro]).fetchall()
        result, reason, pz, pb = decide(r, hits)
        out.append({"fiscal_year": r["fiscal_year"], "source_row": r["source_row"],
                    "zcta_status": r["zip_status"], "postal_code": r["postal_code"],
                    "zip_candidates": r["zip_candidates"], "borough": BORO_NAME.get(boro, ""),
                    "borough_from": how, "house_number": num or "", "street_key": street or "",
                    "rules": ";".join(rules), "pad_matches": "" if hits is None else len(hits),
                    "pad_zip": pz, "pad_bbl": pb, "result": result, "reason": reason,
                    "pad_version": versions[0], "pad_sha256": pad_sha256})
    return out


def check(path=OUT, root=ROOT):
    """Problems with the committed file, [] if none: it must cover exactly the rows the Census
    check leaves ambiguous_extra_digit or state_mismatch, each row's printed values must match,
    and every settled row must fit decide()'s rule."""
    bad = []
    have = load(path)
    rows = disclosure_rows(root)
    want = {(r["fiscal_year"], r["source_row"]): r for r in rows}
    if set(have) != set(want):
        bad.append(f"covers {len(have)} rows; the data has {len(want)} to check "
                   f"(missing {sorted(set(want) - set(have))[:5]}, extra {sorted(set(have) - set(want))[:5]})")
    for k, c in have.items():
        r = want.get(k)
        if r is None:
            continue
        if (c["zcta_status"], c["postal_code"], c["zip_candidates"]) != (r["zip_status"], r["postal_code"], r["zip_candidates"]):
            bad.append(f"{k}: printed values changed since the check")
            continue
        if c["result"] != "left":
            hits = [(c["pad_zip"], c["pad_bbl"])] if c["pad_matches"] == "1" else []
            if decide(r, hits)[0] != c["result"]:
                bad.append(f"{k}: result {c['result']} does not follow from its PAD match")
        if not c["pad_version"] or not re.fullmatch(r"[0-9a-f]{64}", c["pad_sha256"]):
            bad.append(f"{k}: no PAD version or sha256")
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pad", help="local PAD normalized file (CSV, or Parquet made from it)")
    ap.add_argument("--pad-sha256", help="sha256 of the downloaded CSV (default: of --pad)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        bad = check()
        for b in bad:
            print("PROBLEM:", b)
        print(f"{os.path.relpath(OUT, ROOT)}: {'OK' if not bad else f'{len(bad)} problem(s)'}")
        return 1 if bad else 0
    if not a.pad:
        ap.error("--write needs --pad")
    rows = build(os.path.expanduser(a.pad), disclosure_rows(), a.pad_sha256 or sha256_of(os.path.expanduser(a.pad)))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write(text(rows))
    from collections import Counter
    for (st, res), n in sorted(Counter((r["zcta_status"], r["result"]) for r in rows).items()):
        print(f"{st:<22} -> {res:<22} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
