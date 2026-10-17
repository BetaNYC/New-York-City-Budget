#!/usr/bin/env python3
"""Derive a ZCTA -> state(s) table from the Census Bureau's 2020 ZCTA-to-County relationship
file, for checking the ZIP codes in the expense disclosure (GitHub #70).

Source (downloaded once, 2026-10-12, on the maintainer's approval; NOT committed, 6.8 MB):
  https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt
Its URL, retrieval date, byte count and sha256 are in source/census-zcta/MANIFEST.csv; this
script refuses a file whose sha256 differs, so the derived table can only come from those bytes.

Layout, from the Census Bureau's documentation, not inferred from the file:
  * Record layout, "2020 ZCTA to County Relationship File" (tab20_zcta520_county20_natl.txt),
    https://www.census.gov/programs-surveys/geography/technical-documentation/records-layout/2020-zcta-record-layout.html
    18 columns, of which this script reads two: GEOID_ZCTA5_20 ("GEOID of the 2020 ZCTA5") and
    GEOID_COUNTY_20 ("GEOID of the 2020 county").
  * "Explanation of the 2020 ZIP Code Tabulation Area (ZCTA) to County Relationship File",
    https://www2.census.gov/geo/pdfs/maps-data/data/rel2020/zcta520/explanation_tab20_zcta520_county20_natl.pdf
    One record per ZCTA x county intersection; a ZCTA in two counties has two records (its
    example: ZCTA 06331 in counties 09011 and 09015); "In situations where there is a COUNTY, but
    no ZCTA exists, the ZCTA values are not populated" -- those records are skipped here.
  The delimiter (|) and the UTF-8 byte-order mark are not stated in either document; they are
  what the downloaded file holds, and the header is checked against the documented column
  names before anything is read, so a changed layout is a stop, not a misread.
A county GEOID is the 2-digit state FIPS code followed by the 3-digit county code (documented
example: county 09011, New London County, Connecticut = state 09). State FIPS -> USPS code is
the Census Bureau's table, https://www.census.gov/library/reference/code-lists/ansi/ansi-codes-for-states.html
(STATE_FIPS below, copied from it).

Output: data/reference/zcta2020_states.csv  (zcta, states) -- states is every USPS state code
the ZCTA's counties lie in, sorted, joined with ';' (a ZCTA can cross a state line).

Run:
  python3 code/zcta_states.py --derive PATH/TO/tab20_zcta520_county20_natl.txt
  python3 code/zcta_states.py --check    exit 1 if the committed table is malformed or its
                                          row count/sha256 disagree with MANIFEST.csv
"""

import argparse
import csv
import hashlib
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "source", "census-zcta")
MANIFEST = os.path.join(SRC_DIR, "MANIFEST.csv")
TABLE = os.path.join(ROOT, "data", "reference", "zcta2020_states.csv")
RAW_NAME = "tab20_zcta520_county20_natl.txt"

# The documented record layout, in order. The header must equal this exactly.
LAYOUT = ["OID_ZCTA5_20", "GEOID_ZCTA5_20", "NAMELSAD_ZCTA5_20", "AREALAND_ZCTA5_20",
          "AREAWATER_ZCTA5_20", "MTFCC_ZCTA5_20", "CLASSFP_ZCTA5_20", "FUNCSTAT_ZCTA5_20",
          "OID_COUNTY_20", "GEOID_COUNTY_20", "NAMELSAD_COUNTY_20", "AREALAND_COUNTY_20",
          "AREAWATER_COUNTY_20", "MTFCC_COUNTY_20", "CLASSFP_COUNTY_20", "FUNCSTAT_COUNTY_20",
          "AREALAND_PART", "AREAWATER_PART"]

# State FIPS -> (USPS code, name). Copied from the Census Bureau's "ANSI Codes for States" table
# (URL in the module docstring): the 50 states, DC, and the outlying areas that carry a USPS code.
STATE_FIPS = {
    "01": ("AL", "Alabama"), "02": ("AK", "Alaska"), "04": ("AZ", "Arizona"),
    "05": ("AR", "Arkansas"), "06": ("CA", "California"), "08": ("CO", "Colorado"),
    "09": ("CT", "Connecticut"), "10": ("DE", "Delaware"), "11": ("DC", "District of Columbia"),
    "12": ("FL", "Florida"), "13": ("GA", "Georgia"), "15": ("HI", "Hawaii"),
    "16": ("ID", "Idaho"), "17": ("IL", "Illinois"), "18": ("IN", "Indiana"),
    "19": ("IA", "Iowa"), "20": ("KS", "Kansas"), "21": ("KY", "Kentucky"),
    "22": ("LA", "Louisiana"), "23": ("ME", "Maine"), "24": ("MD", "Maryland"),
    "25": ("MA", "Massachusetts"), "26": ("MI", "Michigan"), "27": ("MN", "Minnesota"),
    "28": ("MS", "Mississippi"), "29": ("MO", "Missouri"), "30": ("MT", "Montana"),
    "31": ("NE", "Nebraska"), "32": ("NV", "Nevada"), "33": ("NH", "New Hampshire"),
    "34": ("NJ", "New Jersey"), "35": ("NM", "New Mexico"), "36": ("NY", "New York"),
    "37": ("NC", "North Carolina"), "38": ("ND", "North Dakota"), "39": ("OH", "Ohio"),
    "40": ("OK", "Oklahoma"), "41": ("OR", "Oregon"), "42": ("PA", "Pennsylvania"),
    "44": ("RI", "Rhode Island"), "45": ("SC", "South Carolina"), "46": ("SD", "South Dakota"),
    "47": ("TN", "Tennessee"), "48": ("TX", "Texas"), "49": ("UT", "Utah"),
    "50": ("VT", "Vermont"), "51": ("VA", "Virginia"), "53": ("WA", "Washington"),
    "54": ("WV", "West Virginia"), "55": ("WI", "Wisconsin"), "56": ("WY", "Wyoming"),
    "60": ("AS", "American Samoa"), "64": ("FM", "Federated States of Micronesia"),
    "66": ("GU", "Guam"), "68": ("MH", "Marshall Islands"),
    "69": ("MP", "Commonwealth of the Northern Mariana Islands"), "70": ("PW", "Palau"),
    "72": ("PR", "Puerto Rico"), "74": ("UM", "U.S. Minor Outlying Islands"),
    "78": ("VI", "U.S. Virgin Islands"),
}
USPS = {code for code, _ in STATE_FIPS.values()}
_NAME_TO_USPS = {name.lower(): code for code, name in STATE_FIPS.values()}

TABLE_FIELDS = ["zcta", "states"]
MANIFEST_FIELDS = ["file", "url", "retrieved", "bytes", "sha256", "last_modified", "records",
                   "zcta_records", "derived", "derived_rows"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def derive(lines):
    """Iterable of text lines of the relationship file -> ({zcta: set(usps)}, records, zcta
    records). Stops on a header that is not the documented layout, a ZCTA that is not 5 digits,
    or a county GEOID whose state FIPS is not in STATE_FIPS."""
    rd = csv.reader(lines, delimiter="|")
    header = next(rd)
    if header and header[0].startswith("\ufeff"):
        header[0] = header[0][1:]
    if header != LAYOUT:
        raise ValueError(f"header is not the documented 18-column layout: {header}")
    iz, ic = LAYOUT.index("GEOID_ZCTA5_20"), LAYOUT.index("GEOID_COUNTY_20")
    out, n, nz = {}, 0, 0
    for row in rd:
        if not row:
            continue
        n += 1
        if len(row) != len(LAYOUT):
            raise ValueError(f"record {n}: {len(row)} fields, expected {len(LAYOUT)}")
        z, county = row[iz], row[ic]
        if z == "":
            continue  # a county with no ZCTA (documented, Example 3)
        if not re.fullmatch(r"\d{5}", z):
            raise ValueError(f"record {n}: GEOID_ZCTA5_20 {z!r} is not 5 digits")
        if not re.fullmatch(r"\d{5}", county) or county[:2] not in STATE_FIPS:
            raise ValueError(f"record {n}: GEOID_COUNTY_20 {county!r} has no known state FIPS")
        nz += 1
        out.setdefault(z, set()).add(STATE_FIPS[county[:2]][0])
    return out, n, nz


def table_text(zctas):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(TABLE_FIELDS)
    for z in sorted(zctas):
        w.writerow([z, ";".join(sorted(zctas[z]))])
    return buf.getvalue()


def load_table(path=TABLE):
    """{zcta: frozenset(usps)} from the committed derived table."""
    with open(path, newline="", encoding="utf-8") as f:
        return {r["zcta"]: frozenset(r["states"].split(";")) for r in csv.DictReader(f)}


def read_manifest(path=MANIFEST):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- ZIP status (GitHub #70)

ZIP_STATUSES = ("valid", "padded", "trimmed", "not_a_zcta", "state_mismatch", "invalid", "blank")
_ZIP5 = re.compile(r"(\d{5})")
_ZIP9 = re.compile(r"(\d{5})(?:\s*-\s*\d{4}|\d{4})")
# A ragged ZIP+4: five digits, a hyphen, then digits that are not exactly four ('11203-',
# '10027-000', '11217-11217', '11102-20'). Only the hyphenated form counts; '11231=1020',
# '11413 ZipCode2: 3929' and six-digit typos ('111691') are not read as one.
_RAGGED = re.compile(r"(\d{5})\s*-\s*(?!\d{4}$)\d*")


def row_state(state):
    """The USPS code a disclosure `state` cell names, or '' if it names none unambiguously.
    Read: a USPS code in any case ('NY', 'ny'); a state name in any case ('New York'); the
    workbook's name-and-code run-together form when the two agree ('New YorkNY', FY2015-FY2017).
    Not read: boroughs ('Brooklyn'), a ZIP, 'N/A', anything else -- those rows' ZIPs are checked
    for existence only (see classify_zip)."""
    s = " ".join((state or "").split())
    if s.upper() in USPS:
        return s.upper()
    if s.lower() in _NAME_TO_USPS:
        return _NAME_TO_USPS[s.lower()]
    m = re.fullmatch(r"(.+?)([A-Za-z]{2})", s)
    if m and _NAME_TO_USPS.get(m.group(1).strip().lower()) == m.group(2).upper():
        return m.group(2).upper()
    return ""


def classify_zip(postal_code, state, zctas):
    """(zip, zip_status) for one row. `postal_code` is kept as published, elsewhere; this only
    derives. Rules (DATA-DICTIONARY):
      blank           the cell is empty
      valid           5 digits, or ZIP+4 ('10001-1234', '10001 - 1234', '100011234'), whose
                      first five are a 2020 ZCTA, in the row's state when the state cell names
                      one (row_state); zip = the five digits
      state_mismatch  as valid, but the ZCTA lies wholly in other states; zip = the five digits
      not_a_zcta      a well-formed 5-digit ZIP that is not a 2020 ZCTA (PO-box-only and
                      single-building ZIPs such as 10008 are not ZCTAs): NOT VERIFIED, not fake;
                      zip = the five digits
      padded          4 digits, and '0' + those digits is a 2020 ZCTA in the row's state (an
                      Excel number that lost its leading zero); zip = the padded value
      trimmed         a ragged ZIP+4 (_RAGGED: '11203-', '11217-11217', '10027-000') whose first
                      five digits are a 2020 ZCTA in the row's state; zip = those five digits.
                      Not trimmed when the row names no state or the ZCTA is elsewhere.
      invalid         anything else: 4 digits that do not pad to an in-state ZCTA (or whose row
                      names no state), a ragged ZIP+4 that does not trim to one, '0', '#N/A', a
                      name, a URL; zip = ''"""
    raw = (postal_code or "").strip()
    if raw == "":
        return "", "blank"
    st = row_state(state)
    m = _ZIP5.fullmatch(raw) or _ZIP9.fullmatch(raw)
    if m:
        z = m.group(1)
        if z not in zctas:
            return z, "not_a_zcta"
        if st and st not in zctas[z]:
            return z, "state_mismatch"
        return z, "valid"
    if re.fullmatch(r"\d{4}", raw):
        z = "0" + raw
        if st and z in zctas and st in zctas[z]:
            return z, "padded"
    m = _RAGGED.fullmatch(raw)
    if m:
        z = m.group(1)
        if st and z in zctas and st in zctas[z]:
            return z, "trimmed"
    return "", "invalid"


# ---------------------------------------------------------------- CLI

def manifest_text(row):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerow(row)
    return buf.getvalue()


def check(table=TABLE, manifest=MANIFEST):
    """Problems with the committed table, [] if none: rows must be 5-digit ZCTAs, sorted, unique,
    each with known USPS codes, and as many as MANIFEST.csv's derived_rows."""
    bad = []
    rows = []
    with open(table, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames != TABLE_FIELDS:
            return [f"header {rd.fieldnames} != {TABLE_FIELDS}"]
        rows = list(rd)
    zs = [r["zcta"] for r in rows]
    if zs != sorted(set(zs)):
        bad.append("zctas are not sorted and unique")
    bad += [f"bad row {r}" for r in rows if not re.fullmatch(r"\d{5}", r["zcta"])
            or not r["states"] or any(x not in USPS for x in r["states"].split(";"))][:5]
    m = [r for r in read_manifest(manifest) if r["file"] == RAW_NAME]
    if len(m) != 1:
        bad.append(f"MANIFEST.csv has {len(m)} rows for {RAW_NAME}")
    elif int(m[0]["derived_rows"]) != len(rows):
        bad.append(f"table has {len(rows)} rows, MANIFEST.csv says {m[0]['derived_rows']}")
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--derive", metavar="PATH", help="the downloaded relationship file")
    g.add_argument("--check", action="store_true", help="validate the committed table")
    ap.add_argument("--retrieved", help="YYYY-MM-DD the file was downloaded (first derivation)")
    ap.add_argument("--last-modified", help="the server's Last-Modified header, as recorded")
    a = ap.parse_args(argv)
    if a.check:
        bad = check()
        for b in bad:
            print(f"BAD: {b}")
        print(f"{os.path.relpath(TABLE, ROOT)}: {'OK' if not bad else 'FAILED'}")
        return 1 if bad else 0
    digest = sha256_file(a.derive)
    prev = read_manifest() if os.path.exists(MANIFEST) else []
    prev = [r for r in prev if r["file"] == RAW_NAME]
    if prev and prev[0]["sha256"] != digest:
        sys.exit(f"{a.derive}: sha256 {digest} is not the {prev[0]['sha256']} recorded in "
                 f"MANIFEST.csv; a different file needs its own approval and a new manifest row")
    if not prev and not (a.retrieved and a.last_modified):
        sys.exit("first derivation: pass --retrieved YYYY-MM-DD and --last-modified (never inferred)")
    with open(a.derive, encoding="utf-8", newline="") as f:
        zctas, n, nz = derive(f)
    row = prev[0] if prev else {
        "file": RAW_NAME,
        "url": "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/" + RAW_NAME,
        "retrieved": a.retrieved, "last_modified": a.last_modified}
    row.update(bytes=os.path.getsize(a.derive), sha256=digest, records=n, zcta_records=nz,
               derived=os.path.relpath(TABLE, ROOT), derived_rows=len(zctas))
    os.makedirs(os.path.dirname(TABLE), exist_ok=True)
    os.makedirs(SRC_DIR, exist_ok=True)
    for path, text in ((TABLE, table_text(zctas)), (MANIFEST, manifest_text(row))):
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(path, ROOT)}")
    print(f"{n} records, {nz} with a ZCTA, {len(zctas)} distinct ZCTAs, "
          f"{sum(len(v) > 1 for v in zctas.values())} in more than one state")
    return 0


if __name__ == "__main__":
    sys.exit(main())
