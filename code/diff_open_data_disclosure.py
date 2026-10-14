#!/usr/bin/env python3
"""diff_open_data_disclosure.py -- compare NYC Open Data "City Council Discretionary Funding"
(4d7f-74pe) with the Council's own expense funding disclosure workbooks, per fiscal year
(GitHub #85, and the FY2009-FY2012 half of #86).

    python3 code/diff_open_data_disclosure.py --open-data CACHE/4d7f-74pe.csv \
        [--workbook FY=PATH ...] [--out-dir DIR] [--date YYYY-MM-DD]

Two "Council" sides are possible per year:
  * FY2013-FY2021: our published dataset, data/fyNN/expense_disclosure/fyNN_expense_awards.csv
    (the 2026-10-12 re-pull of rnd.council.nyc.gov).
  * any year given with --workbook FY=PATH (FY2009-FY2012 from the Internet Archive): the
    workbook is parsed with code/parse_expense_disclosure.py exactly as --write would.

Matching rules (issue #85):
  * rows pair on the MULTISET of (ein, amount) -- a pair printed twice is two rows. Never on EIN
    alone and never on council member (the member is the roster at export time).
  * MOCS ID matching is reported only where BOTH sides carry one. Before FY2024 the Council
    workbooks have no MOCS ID column, so for FY2009-FY2021 this is always "not possible", and the
    report says so instead of inventing a key.
  * field differences are counted only on rows whose (ein, amount) occurs exactly once on each
    side (an unambiguous pair). Rows inside a repeated key are counted, not paired.

Normalization, applied to BOTH sides where it applies, raw values kept:
  * text: parse_expense_disclosure._clean (invisible characters, soft hyphen, whitespace).
  * EIN: clean_ein (NN-NNNNNNN loses its hyphen). Open Data's EIN column is text, but 1,600 of
    its values are 8 digits: a leading zero lost before publication. The Open Data side pads an
    8-digit all-digit EIN to 9 and counts it (ein_padded); the raw value stays in ein_raw. The
    workbook side keeps its own rule (pad only a NUMERIC cell).
  * status: status_norm cleared / pending / other; the raw value is kept and reported, because
    Open Data's extra values (Government, Revoked, Pending-Council, Designated) and the
    workbooks' (CBO Defunded, Pending FC Clearance) all fall in "other".
  * amount: Decimal of the shortest round-trip repr (parse_amount_text) on both sides.

Stdlib only (plus xlrd for an .xls workbook). No network.
"""
import argparse
import csv
import io
import os
import sys
from collections import Counter, defaultdict
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse_expense_disclosure as P

ROOT = os.path.dirname(HERE)
OVERLAP = range(2013, 2022)
STATUSES = ("cleared", "pending", "other")
# (field in the common shape, Open Data column, our column)
FIELD_PAIRS = [
    ("legal_name", "legal_name_of_organization", "legal_name"),
    ("council_member", "council_member", "council_member"),
    ("source", "source", "source"),
    ("agency", "agency", "agency"),
    ("program_name", "program_name", "program_name"),
    ("status", "status", "status"),
    ("address1", "address", "address1"),
    ("address2", "address_2_optional", "address2"),
    ("city", "city", "city"),
    ("state", "state", "state"),
    ("postal_code", "postcode", "postal_code"),
    ("purpose", "purpose_of_funds", "purpose"),
    ("fiscal_conduit", "fiscal_conduit_name", "fiscal_conduit"),
    ("fiscal_conduit_ein", "fc_ein", "fiscal_conduit_ein"),
]
GEO = ["borough", "latitude", "longitude", "community_board", "council_district",
       "census_tract", "bin", "bbl", "nta"]


def od_ein(raw):
    """Open Data EIN -> (ein, padded). 8 digits = a lost leading zero, padded and flagged."""
    e, _ = P.clean_ein(raw, False)
    if e.isdigit() and len(e) == 8:
        return e.zfill(9), True
    return e, False


def amount(s):
    d = P.parse_amount_text(s)
    if d is None:
        raise ValueError(f"not an amount: {s!r}")
    return d


def norm_od(r):
    """One Open Data row (as served) -> the common shape. Raw columns kept under od_*."""
    ein, padded = od_ein(r.get("ein", ""))
    out = {f: P._clean(r.get(od, "")) for f, od, _ in FIELD_PAIRS}
    out.update({
        "fiscal_year": int(float(r["fiscal_year"])), "mocs_id": P._clean(r.get("mocs_id", "")),
        "ein": ein, "ein_raw": r.get("ein", ""), "ein_padded": padded,
        "amount": amount(r["amount"]), "status_norm": P.norm_status(r.get("status", "")),
        "fiscal_conduit_ein": od_ein(r.get("fc_ein", ""))[0],
        "ref": r.get(":id", ""),
    })
    for g in GEO:
        out[g] = r.get(g, "")
    return out


def norm_ours(r):
    """One row of fyNN_expense_awards.csv (already normalized by the parser)."""
    out = {f: r.get(ours, "") for f, _, ours in FIELD_PAIRS}
    out.update({"fiscal_year": int(r["fiscal_year"]), "mocs_id": r.get("mocs_id", ""),
                "ein": r["ein"], "amount": amount(r["amount"]), "status_norm": r["status_norm"],
                "ref": f"{r['source_file']}:{r['source_row']}"})
    return out


def norm_award(a):
    """A parse_expense_disclosure.Award -> the common shape."""
    d = a._asdict()
    out = {f: d.get(ours, "") for f, _, ours in FIELD_PAIRS}
    out.update({"fiscal_year": a.fiscal_year, "mocs_id": a.mocs_id, "ein": a.ein,
                "amount": Decimal(a.amount_text), "status_norm": a.status_norm,
                "ref": f"{a.source_file}:{a.source_row}"})
    return out


def load_open_data(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [norm_od(r) for r in csv.DictReader(f)]


DATA_DIR = os.path.join(ROOT, "data")


def load_ours(fy, data_dir=DATA_DIR):
    p = os.path.join(data_dir, f"fy{fy % 100:02d}", "expense_disclosure",
                     f"fy{fy % 100:02d}_expense_awards.csv")
    with open(p, newline="", encoding="utf-8") as f:
        return [norm_ours(r) for r in csv.DictReader(f)]


def load_workbook(path):
    awards, rep = P.parse_year(path)
    if rep.skipped:
        raise SystemExit(f"{path}: {rep.skipped}")
    return [norm_award(a) for a in awards], rep


def totals(rows):
    t = {s: Decimal(0) for s in STATUSES}
    n = Counter()
    for r in rows:
        t[r["status_norm"]] += r["amount"]
        n[r["status_norm"]] += 1
    return n, t


def q(d, places):
    """Round half-up to `places` decimals (Open Data's rounding: 5437.5 -> 5438, 6333.33 ->
    6333 from FY2012; 7481.296758 -> 7481.30 in FY2009-FY2011)."""
    from decimal import ROUND_HALF_UP
    return d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def _multiset_pair(left, right, lkey, rkey):
    """Pair rows of `left` and `right` whose keys are equal, as a multiset, in input order.
    Returns (pairs, left_rest, right_rest)."""
    pool = defaultdict(list)
    for r in right:
        pool[rkey(r)].append(r)
    pairs, rest = [], []
    for r in left:
        bucket = pool.get(lkey(r))
        if bucket:
            pairs.append((r, bucket.pop(0)))
        else:
            rest.append(r)
    right_rest = [r for b in pool.values() for r in b]
    return pairs, rest, right_rest


def _slot(r, amt):
    return (amt, r["source"].casefold(), r["agency"].casefold(), r["council_member"].casefold())


def _nominate(od_rest, ours_rest):
    """After matching: nominations for a person to check, never matches. In order:
      amount_differs   same EIN and legal name, different amount
      ein_differs      same legal name and amount, different EIN (a corrected or filled EIN)
      grantee_differs  same slot -- amount, source, agency, council member -- and a different
                       organization: the money was most likely re-designated to another
                       grantee between the two publications."""
    out = []
    for kind, lk, rk in (
        ("amount_differs", lambda r: (r["ein"], r["legal_name"].casefold()),
         lambda r: (r["ein"], r["legal_name"].casefold())),
        ("ein_differs", lambda r: (r["amount"], r["legal_name"].casefold()),
         lambda r: (q(r["amount"], 0), r["legal_name"].casefold())),
        ("grantee_differs", lambda r: _slot(r, r["amount"]),
         lambda r: _slot(r, q(r["amount"], 0) if r["amount"] != q(r["amount"], 0)
                         and r["fiscal_year"] >= 2012 else r["amount"]))):
        pairs, od_rest, ours_rest = _multiset_pair(od_rest, ours_rest, lk, rk)
        out += [(kind, a, b) for a, b in pairs]
    return out


def compare(od, ours):
    """Compare one year's rows. Returns a dict of counts plus the unmatched rows.

    Tier 1 (match): multiset of (ein, amount), exact.
    Tier 2 (match after rounding): what is left, on (ein, council amount rounded half-up to
           cents) and then (ein, rounded to whole dollars) against (ein, Open Data amount).
    Then nominations (not matches): same legal name and EIN, different amount; same legal
           name and amount, different EIN."""
    ko = Counter((r["ein"], r["amount"]) for r in od)
    ku = Counter((r["ein"], r["amount"]) for r in ours)
    by_od, by_ours = defaultdict(list), defaultdict(list)
    for r in od:
        by_od[(r["ein"], r["amount"])].append(r)
    for r in ours:
        by_ours[(r["ein"], r["amount"])].append(r)

    exact, od_rest, ours_rest = _multiset_pair(
        od, ours, lambda r: (r["ein"], r["amount"]), lambda r: (r["ein"], r["amount"]))
    rc, od_rest, ours_rest = _multiset_pair(
        od_rest, ours_rest, lambda r: (r["ein"], r["amount"]),
        lambda r: (r["ein"], q(r["amount"], 2)))
    rd, od_rest, ours_rest = _multiset_pair(
        od_rest, ours_rest, lambda r: (r["ein"], r["amount"]),
        lambda r: (r["ein"], q(r["amount"], 0)))
    nominations = _nominate(od_rest, ours_rest)

    unique = [k for k in ko if ko[k] == 1 and ku.get(k) == 1]
    field_diff = Counter()
    field_diff_ci = Counter()        # still different after casefold
    examples = defaultdict(list)
    for k in unique:
        a, b = by_od[k][0], by_ours[k][0]
        for f, _, _ in FIELD_PAIRS:
            if a[f] != b[f]:
                field_diff[f] += 1
                if a[f].casefold() != b[f].casefold():
                    field_diff_ci[f] += 1
                if len(examples[f]) < 5:
                    examples[f].append((k[0], str(k[1]), a[f], b[f], a["ref"], b["ref"]))
    n_od, t_od = totals(od)
    n_us, t_us = totals(ours)
    return {
        "rows_od": len(od), "rows_ours": len(ours), "matched": len(exact),
        "matched_rounded_cents": len(rc), "matched_rounded_dollars": len(rd),
        "od_only": od_rest, "ours_only": ours_rest, "nominations": nominations,
        "unique_pairs": len(unique),
        "field_diff": field_diff, "field_diff_ci": field_diff_ci, "examples": examples,
        "mocs_possible": any(r["mocs_id"] for r in ours) and any(r["mocs_id"] for r in od),
        "n_od": n_od, "t_od": t_od, "n_ours": n_us, "t_ours": t_us,
        "status_raw_od": Counter(r["status"] for r in od),
        "status_raw_ours": Counter(r["status"] for r in ours),
        "status_moves": Counter((by_od[k][0]["status"], by_ours[k][0]["status"]) for k in unique
                                if by_od[k][0]["status_norm"] != by_ours[k][0]["status_norm"]),
        "ein_padded_od": sum(1 for r in od if r.get("ein_padded")),
    }


def money(d):
    return f"{d:,.2f}".rstrip("0").rstrip(".") if d != d.to_integral_value() else f"{int(d):,}"


UNMATCHED_FIELDS = ["fiscal_year", "side", "ein", "amount", "status", "legal_name", "source",
                    "agency", "council_member", "program_name", "mocs_id", "ref"]


def unmatched_csv(results):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=UNMATCHED_FIELDS, lineterminator="\n",
                       extrasaction="ignore")
    w.writeheader()
    for fy, label, res in results:
        for side, rows in (("open_data_only", res["od_only"]), (f"{label}_only", res["ours_only"])):
            for r in sorted(rows, key=lambda r: (r["ein"], r["amount"], r["ref"])):
                w.writerow({**r, "fiscal_year": fy, "side": side, "amount": P.format_amount(r["amount"])})
    return out.getvalue()


SUMMARY_FIELDS = ["fiscal_year", "council_side", "rows_open_data", "rows_council", "row_delta",
                  "matched_ein_amount", "matched_rounded_cents", "matched_rounded_dollars",
                  "nominated_amount_differs", "nominated_ein_differs",
                  "nominated_grantee_differs", "open_data_only", "council_only", "unique_pairs",
                  "cleared_open_data", "cleared_council", "pending_open_data", "pending_council",
                  "other_open_data", "other_council", "total_open_data", "total_council",
                  "ein_padded_open_data"]


def summary_csv(results):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=SUMMARY_FIELDS, lineterminator="\n")
    w.writeheader()
    for fy, label, r in results:
        w.writerow({
            "fiscal_year": fy, "council_side": label, "rows_open_data": r["rows_od"],
            "rows_council": r["rows_ours"], "row_delta": r["rows_od"] - r["rows_ours"],
            "matched_ein_amount": r["matched"],
            "matched_rounded_cents": r["matched_rounded_cents"],
            "matched_rounded_dollars": r["matched_rounded_dollars"],
            "nominated_amount_differs": sum(1 for k, _, _ in r["nominations"]
                                            if k == "amount_differs"),
            "nominated_ein_differs": sum(1 for k, _, _ in r["nominations"] if k == "ein_differs"),
            "nominated_grantee_differs": sum(1 for k, _, _ in r["nominations"]
                                             if k == "grantee_differs"),
            "open_data_only": len(r["od_only"]),
            "council_only": len(r["ours_only"]), "unique_pairs": r["unique_pairs"],
            **{f"{s}_open_data": P.format_amount(r["t_od"][s]) for s in STATUSES},
            **{f"{s}_council": P.format_amount(r["t_ours"][s]) for s in STATUSES},
            "total_open_data": P.format_amount(sum(r["t_od"].values())),
            "total_council": P.format_amount(sum(r["t_ours"].values())),
            "ein_padded_open_data": r["ein_padded_od"],
        })
    return out.getvalue()


def field_diff_csv(results):
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["fiscal_year", "field", "unique_pairs", "differ_exact", "differ_casefold"])
    for fy, _, r in results:
        for f, _, _ in FIELD_PAIRS:
            w.writerow([fy, f, r["unique_pairs"], r["field_diff"][f], r["field_diff_ci"][f]])
    return out.getvalue()


def profile(rows):
    """Profile a set of Open Data rows (one year): statuses, totals, field completeness."""
    n = len(rows)
    filled = {f: sum(1 for r in rows if r.get(f)) for f, _, _ in FIELD_PAIRS}
    filled.update({g: sum(1 for r in rows if r.get(g)) for g in GEO})
    filled["mocs_id"] = sum(1 for r in rows if r["mocs_id"])
    return {"rows": n, "status": Counter(r["status"] for r in rows),
            "amount_by_status": {s: sum((r["amount"] for r in rows if r["status"] == s),
                                        Decimal(0)) for s in {r["status"] for r in rows}},
            "filled": filled}


PROFILE_FIELDS = ["fiscal_year", "rows", "statuses", "amount_by_status"] + \
    [f"filled_{f}" for f, _, _ in FIELD_PAIRS] + ["filled_mocs_id"] + [f"filled_{g}" for g in GEO]


def profile_csv(by_fy):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=PROFILE_FIELDS, lineterminator="\n")
    w.writeheader()
    for fy in sorted(by_fy):
        p = profile(by_fy[fy])
        w.writerow({
            "fiscal_year": fy, "rows": p["rows"],
            "statuses": "; ".join(f"{k}={v}" for k, v in sorted(p["status"].items())),
            "amount_by_status": "; ".join(f"{k}={P.format_amount(v)}"
                                          for k, v in sorted(p["amount_by_status"].items())),
            **{f"filled_{k}": v for k, v in p["filled"].items()}})
    return out.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--open-data", required=True)
    ap.add_argument("--workbook", action="append", default=[],
                    help="FY=PATH, a Council workbook to compare for that year")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "research", "open-data-diff"))
    a = ap.parse_args(argv)
    od = load_open_data(a.open_data)
    by_fy = defaultdict(list)
    for r in od:
        by_fy[r["fiscal_year"]].append(r)
    results = []
    for fy in OVERLAP:
        results.append((fy, "disclosure_2026_10_12", compare(by_fy[fy], load_ours(fy))))
    for spec in a.workbook:
        fy, path = spec.split("=", 1)
        rows, _ = load_workbook(path)
        results.append((int(fy), "wayback_workbook", compare(by_fy[int(fy)], rows)))
    os.makedirs(a.out_dir, exist_ok=True)
    for name, text in (("summary.csv", summary_csv(results)),
                       ("unmatched-rows.csv", unmatched_csv(results)),
                       ("field-differences.csv", field_diff_csv(results)),
                       ("open-data-profile.csv", profile_csv(by_fy))):
        with open(os.path.join(a.out_dir, name), "w", encoding="utf-8", newline="") as f:
            f.write(text)
    print(summary_csv(results))


if __name__ == "__main__":
    main()
