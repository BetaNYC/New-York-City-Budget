#!/usr/bin/env python3
"""build_open_data_crosswalk.py -- for every record the repo serves, say whether it is on NYC
Open Data, which row, as of which snapshot (research/2026-10-21-open-data-tracking/PLAN.md §5,
approved 2026-10-21).

    python3 code/build_open_data_crosswalk.py --write | --check

Reads only committed files: the repo's records (data/) and the Open Data snapshots
(source/open-data-<id>/). No network.

Writes data/open_data/:
  crosswalk_<family>.csv          the latest snapshot's crosswalk, one row per (record, dataset)
                                  where the dataset covers the record's year
  crosswalk_history_<family>.csv.gz   every snapshot's rows, append-only (gzip mtime 0)
  coverage.csv                    per (family, dataset, fiscal year): our records by status, the
                                  portal's rows, and portal-only rows (PLAN Q5: counted, not listed)

Families and rules (PLAN §5; the first rule that gives exactly one portal row wins; two or more is
`ambiguous` with the candidates listed, never a guess):

  expense       data/fyNN/expense_disclosure/ awards.
    4d7f-74pe   FY2009-FY2021. Bucket = (fiscal year, EIN, amount rounded half-up to dollars),
                the rule code/parse_expense_disclosure.py od_matches uses. One row on each side:
                `same` when the amounts agree exactly or after the portal's rounding (to cents,
                FY2009-FY2011; to dollars, FY2012+), else `differs` (amount). Several on either
                side: `ambiguous`. None on the portal: `absent`. The committed portal extract is
                keys only (#85), so other fields are not compared here; they are in
                research/2026-10-14-open-data-diff/field-differences.csv.
    ujre-m2tj   FY2019-FY2021. Through the MOCS award number the record got from 4d7f-74pe;
                else (fiscal year, vendor name normalized, amount, agency), one row each side.
                The latest posting of each award is used; its clearance status and date go in
                portal_status / portal_as_of, beside the Council workbook's own status (PLAN Q6).
  capital_award data/capital/council_capital_awards.csv (and, where present, Part I of
                data/fyNN/pdf/capital_sd/).
    t474-a92g   report years FY2019-FY2026. A row that came from t474 is that portal row. A
                workbook or PDF row matches on (report year, project ID without agency prefix,
                budget line, amount FY, amount); then borough, district, sponsor and title are
                compared as printed (whitespace collapsed).
  capital_line  distinct (report year, budget line) of the Council awards. Status `context`
                (the line is on the portal, not the award) or `absent`.
    46m8-77gv   data/capital/council_vs_omb_by_budget_line.csv: the adopted release; a verdict
                other than `match` is listed in differing_fields.
    2cmn-uidm   the latest commitment-plan release whose first year is the report year.
    djxg-kcfi   the line has a planned commitment in the CPDB version held (fisa_2026, one version):
                FY2026 on only; an earlier year is not covered, since a line missing now proves nothing then.
  terms_unit    (fiscal year, agency, unit of appropriation) named by T&C: data/fyNN/pdf/terms/
                where present, else the retired data/fyNN/terms/ (a multi-agency condition there
                does not say which unit is whose, so its units match under any listed agency).
    mwzb-yiwb   the adopted-release extract. A pair outside the extract's filter, an `All` unit,
                or a year before FY2017 is `not_covered`, never `absent`.

Statuses: same, differs, ambiguous, absent, context, not_covered. Crosswalk files carry no
`not_covered` rows (coverage.csv counts them), which keeps them small; a record with no row and a
year outside a dataset's coverage reads "No NYC Open Data dataset covers this".
"""
import argparse
import csv
import glob
import gzip
import io
import os
import re
import sys
from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_capital_council as BC          # noqa: E402
import parse_expense_disclosure as P        # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join("data", "open_data")
FIELDS = ["family", "record_key", "fiscal_year", "dataset_id", "snapshot_date", "portal_row_id",
          "match_status", "match_rule", "differing_fields", "portal_value", "portal_status",
          "portal_as_of"]
COVERAGE_FIELDS = ["family", "dataset_id", "fiscal_year", "snapshot_date", "covered", "records",
                   "same", "differs", "ambiguous", "ambiguous_present", "absent", "context", "not_covered",
                   "portal_rows", "portal_only", "note"]
STATUSES = ["same", "differs", "ambiguous", "absent", "context", "not_covered"]
MAX_CANDIDATES = 20
COVERS = {"4d7f-74pe": range(2009, 2022), "ujre-m2tj": range(2019, 2022),
          "t474-a92g": range(2019, 2027), "46m8-77gv": range(2019, 2028),
          # CPDB is one current version (fisa_2026): a line missing from it says nothing about an
          # earlier year, so it covers FY2026 on only (PLAN §5, absent vs not covered).
          "2cmn-uidm": range(2016, 2028), "djxg-kcfi": range(2026, 2100),
          "mwzb-yiwb": range(2017, 2028)}
FAMILY_DATASETS = {"expense": ["4d7f-74pe", "ujre-m2tj"], "capital_award": ["t474-a92g"],
                   "capital_line": ["46m8-77gv", "2cmn-uidm", "djxg-kcfi"],
                   "terms_unit": ["mwzb-yiwb"]}


def p(rel):
    return os.path.join(ROOT, rel)


def read_csv(rel):
    with open(p(rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_gz(rel):
    with gzip.open(p(rel), "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def snapshot_date(ds):
    """Retrieval date of the held snapshot's assembled file (its MANIFEST row)."""
    for r in read_csv(f"source/open-data-{ds}/MANIFEST.csv"):
        if r["file"] in (f"{ds}.csv.gz", f"{ds}-keys.csv.gz"):
            return r["retrieved_at"][:10]
    raise ValueError(f"{ds}: no assembled file in MANIFEST.csv")


def norm_text(s):
    return " ".join(P._clean(s or "").split())


def dollars(d):
    return d.quantize(Decimal(1), rounding=ROUND_HALF_UP)


def row(family, key, fy, ds, snap, status, rule, **kw):
    assert status in STATUSES, status
    return {"family": family, "record_key": key, "fiscal_year": fy, "dataset_id": ds,
            "snapshot_date": snap, "match_status": status, "match_rule": rule, **kw}


# ------------------------------------------------------------------------------------------
# expense
# ------------------------------------------------------------------------------------------

def expense_records(root=ROOT):
    out = []
    for path in sorted(glob.glob(os.path.join(root, "data", "fy*", "expense_disclosure", "*_awards.csv"))):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                out.append(r)
    return out


CERTAIN = "presence certain"


def ambiguous_rule(prefix, n_ours, n_portal):
    """An ambiguous bucket. With no more of ours than portal rows, every one of ours has a portal
    row with the same key values: present, row not identifiable. With more of ours, at least one is
    not on the portal, and which is unknown: only possibly present."""
    return (f"{prefix}: bucket holds {n_ours} of ours and {n_portal} on the portal; "
            + (f"{CERTAIN}: every one of ours has a portal row with the same key values, row not identifiable"
               if n_ours <= n_portal else
               "presence uncertain: more of ours than on the portal, so at least one is not there"))


def match_buckets(ours, theirs, key_ours, key_theirs):
    """Pair rows in (key) buckets. -> ({id(our row): (status, rule, [their rows])}, portal_only
    per year). `ours`/`theirs` rows carry 'fiscal_year'."""
    a, b = defaultdict(list), defaultdict(list)
    for r in ours:
        a[key_ours(r)].append(r)
    for t in theirs:
        b[key_theirs(t)].append(t)
    res, only = {}, Counter()
    for k, ts in b.items():
        n = len(a.get(k, []))
        if n < len(ts):
            only[k[0]] += len(ts) - n
    for k, rs in a.items():
        ts = b.get(k, [])
        if not ts:
            for r in rs:
                res[id(r)] = ("absent", "no portal row in the bucket", [])
            continue
        if len(rs) == 1 and len(ts) == 1:
            res[id(rs[0])] = (None, None, ts)       # caller decides same / differs
            continue
        for r in rs:
            res[id(r)] = ("ambiguous", (len(rs), len(ts)), ts)
    return res, only


def amount_tier(ours, portal):
    if ours == portal:
        return "exact"
    if ours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == portal:
        return "rounded_cents"
    if dollars(ours) == portal:
        return "rounded_dollars"
    return None


def expense_4d7f(records, snap):
    ds = "4d7f-74pe"
    keys = read_gz("source/open-data-4d7f-74pe/4d7f-74pe-keys.csv.gz")
    years = COVERS[ds]
    for k in keys:
        k["_ein"] = P._od_ein(k["ein"])
        k["_amt"] = P.parse_amount_text(k["amount"])
    recs = [r for r in records if int(r["fiscal_year"]) in years]
    for r in recs:
        r["_amt"] = P.parse_amount_text(r["amount"])
    res, only = match_buckets(
        recs, keys,
        lambda r: (int(r["fiscal_year"]), r["ein"], dollars(r["_amt"])),
        lambda k: (int(k["fiscal_year"]), k["_ein"], dollars(k["_amt"])))
    out, mocs = [], {}
    for r in recs:
        key = f"{r['fiscal_year']}|{r['source_row']}"
        status, rule, ts = res[id(r)]
        kw = {}
        if status is None:
            t = ts[0]
            tier = amount_tier(r["_amt"], t["_amt"])
            if tier:
                status, rule = "same", f"fy_ein_amount ({tier})"
            else:
                status, rule = "differs", "fy_ein_amount_bucket"
                kw["differing_fields"] = f"amount: ours {r['amount']}, portal {t['amount']}"
            kw["portal_row_id"] = t[":id"]
            kw["portal_value"] = t["amount"]
            mocs[id(r)] = t["mocs_id"]
        elif status == "ambiguous":
            kw["portal_row_id"] = ";".join(t[":id"] for t in ts[:MAX_CANDIDATES]) + \
                (";…" if len(ts) > MAX_CANDIDATES else "")
            rule = ambiguous_rule("fy_ein_amount", *rule)
        else:
            rule = "fy_ein_amount: " + rule
        out.append(row("expense", key, r["fiscal_year"], ds, snap, status, rule, **kw))
    portal_rows = Counter(int(k["fiscal_year"]) for k in keys)
    return out, only, portal_rows, mocs


def expense_ujre(records, snap, mocs):
    ds = "ujre-m2tj"
    raw = read_gz("source/open-data-ujre-m2tj/ujre-m2tj.csv.gz")
    latest = {}
    for t in raw:                      # latest posting of each award
        n = t["mocs_award_number"]
        if n not in latest or t["post_date"] > latest[n]["post_date"]:
            latest[n] = t
    portal = list(latest.values())
    for t in portal:
        t["fiscal_year"] = 2000 + int(t["mocs_award_number"][2:4])
        t["_amt"] = P.parse_amount_text(t["amount"])
    years = COVERS[ds]
    recs = [r for r in records if int(r["fiscal_year"]) in years]
    by_num = {t["mocs_award_number"]: t for t in portal}
    fb = defaultdict(list)
    for t in portal:
        fb[(t["fiscal_year"], norm_text(t["vendor_name"]).upper(), dollars(t["_amt"]),
            t["agency"].strip().upper())].append(t)
    ours_fb = defaultdict(list)
    for r in recs:
        ours_fb[(int(r["fiscal_year"]), norm_text(r["legal_name"]).upper(),
                 dollars(P.parse_amount_text(r["amount"])), r["agency"].strip().upper())].append(r)
    used, out = set(), []
    for r in recs:
        key = f"{r['fiscal_year']}|{r['source_row']}"
        num = r.get("od_mocs_id") or mocs.get(id(r), "")
        t, rule = None, None
        if num and num in by_num:
            t, rule = by_num[num], "mocs_award_number (via 4d7f-74pe)"
        else:
            k = (int(r["fiscal_year"]), norm_text(r["legal_name"]).upper(),
                 dollars(P.parse_amount_text(r["amount"])), r["agency"].strip().upper())
            ts = fb.get(k, [])
            if len(ts) == 1 and len(ours_fb[k]) == 1:
                t, rule = ts[0], "fy_vendor_amount_agency"
            elif ts:
                out.append(row("expense", key, r["fiscal_year"], ds, snap, "ambiguous",
                               ambiguous_rule("fy_vendor_amount_agency", len(ours_fb[k]), len(ts)),
                               portal_row_id=";".join(x[":id"] for x in ts[:MAX_CANDIDATES])))
                continue
        if t is None:
            out.append(row("expense", key, r["fiscal_year"], ds, snap, "absent",
                           "no MOCS award number match, no unique (fy, vendor, amount, agency) match"))
            continue
        used.add(t["mocs_award_number"])
        ours_amt = P.parse_amount_text(r["amount"])
        tier = amount_tier(ours_amt, t["_amt"])
        kw = {"portal_row_id": t[":id"], "portal_value": t["amount"],
              "portal_status": t["statussummary"].strip(), "portal_as_of": t["post_date"][:10]}
        if tier:
            out.append(row("expense", key, r["fiscal_year"], ds, snap, "same", f"{rule} ({tier})", **kw))
        else:
            out.append(row("expense", key, r["fiscal_year"], ds, snap, "differs", rule,
                           differing_fields=f"amount: ours {r['amount']}, portal {t['amount']}", **kw))
    only = Counter(t["fiscal_year"] for t in portal if t["mocs_award_number"] not in used)
    return out, only, Counter(t["fiscal_year"] for t in portal)


# ------------------------------------------------------------------------------------------
# capital awards
# ------------------------------------------------------------------------------------------

def pid(s):
    return " ".join((s or "").split()).split(" ")[-1]


def capital_records(root=ROOT):
    recs = []
    for r in read_csv("data/capital/council_capital_awards.csv"):
        recs.append({"key": f"{r['report_year']}|{r['source_row']}|{r['amount_fy']}", "fy": int(r["report_year"]),
                     "amount_fy": r["amount_fy"], "project_id": r["project_id"],
                     "budget_line": r["budget_line"], "amount": r["amount"],
                     "borough": r["borough"], "council_district": r["council_district"],
                     "sponsor": r["sponsor"], "title": r["title"], "source_kind": r["source_kind"],
                     "source_row": r["source_row"]})
    # Part I of the reviewed capital supporting detail, where promoted (record per non-zero FY).
    for path in sorted(glob.glob(os.path.join(root, "data", "fy*", "pdf", "capital_sd",
                                              "*_capital_sd_projects.csv"))):
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        fys = [c for c in rows[0] if re.fullmatch(r"fy20\d\d", c)] if rows else []
        # FY2025 prints some IDs on two Part I rows (C3.id_reused): those keys also carry the
        # row's page and place, so they stay unique. Every other key is unchanged.
        twice = {k for k, n in Counter(r["sub_id"] for r in rows if r["part"] == "I").items() if n > 1}
        for r in rows:
            if r["part"] != "I":
                continue
            at = f"|p{r['pdf_page']}r{r['row_in_page']}" if r["sub_id"] in twice else ""
            for c in fys:
                if r[c] not in ("", "0"):
                    recs.append({"key": f"pdf|{r['fiscal_year']}|{r['sub_id']}{at}|{c[2:]}",
                                 "fy": int(r["fiscal_year"]), "amount_fy": c[2:],
                                 "project_id": r["sub_id"], "budget_line": r["budget_line"],
                                 "amount": r[c], "borough": r["boro"], "council_district": "",
                                 "sponsor": r["sponsor"], "title": r["title"],
                                 "source_kind": "pdf_capital_sd", "source_row": r["sub_id"]})
    keys = Counter(r["key"] for r in recs)
    dup = [k for k, n in keys.items() if n > 1]
    if dup:
        raise ValueError(f"capital record keys repeat: {dup[:5]}")
    return recs


def capital_t474(recs, snap):
    ds = "t474-a92g"
    t474 = read_gz("source/open-data-t474-a92g/t474-a92g.csv.gz")
    good, heads, tails = BC.t474_split(t474)
    years = COVERS[ds]
    portal = [t for t in good if int(t["reported"]) in years]
    by_id = {t[":id"]: t for t in t474}
    idx = defaultdict(list)
    for t in portal:
        idx[(int(t["reported"]), pid(t["id"]), norm_text(t["budget_line"]),
             str(2000 + int(t["fiscal_year"][2:])), Decimal(t["award"]))].append(t)
    head_ids = {(int(h["reported"]), pid(h["id"])) for h in heads}
    ours_n = Counter((r["fy"], pid(r["project_id"]), norm_text(r["budget_line"]), str(r["amount_fy"]),
                      Decimal(P.parse_amount_text(r["amount"])) if r["amount"] else None)
                     for r in recs if r["source_kind"] != "open_data_t474")
    used, out = set(), []
    for r in recs:
        if r["fy"] not in years:
            continue
        if r["source_kind"] == "open_data_t474":
            t = by_id[r["source_row"]]
            used.add(t[":id"])
            status = "same" if r["amount"] else "differs"
            out.append(row("capital_award", r["key"], r["fy"], ds, snap, status,
                           "is_portal_row (data/capital loads t474 for this year)",
                           portal_row_id=t[":id"], portal_value=t["award"],
                           differing_fields="" if r["amount"] else
                           "record broken across portal rows; amount unknown (RECONCILIATION §2)"))
            continue
        k = (r["fy"], pid(r["project_id"]), norm_text(r["budget_line"]), str(r["amount_fy"]),
             Decimal(P.parse_amount_text(r["amount"])))
        ts = idx.get(k, [])
        if len(ts) == 1:
            t = ts[0]
            used.add(t[":id"])
            diffs = []
            for ours, theirs, name in ((r["borough"], t["borough"], "borough"),
                                       (r["council_district"], t["council_district"], "council_district"),
                                       (r["sponsor"], t["sponsor"], "sponsor"),
                                       (r["title"], t["title"], "title")):
                if r["source_kind"] == "pdf_capital_sd" and name in ("council_district", "sponsor", "title"):
                    continue        # the PDF prints its own forms (upper case, member lists)
                a, b = norm_text(ours), norm_text(theirs)
                ca, cb = a, b
                if name == "council_district":       # "08" and "8" name one district
                    ca, cb = (",".join(sorted(str(int(x)) for x in re.findall(r"\d+", v))) for v in (a, b))
                if ca != cb:
                    diffs.append(f"{name}: ours {a!r}, portal {b!r}")
            out.append(row("capital_award", r["key"], r["fy"], ds, snap,
                           "differs" if diffs else "same",
                           "report_year_id_line_fy_amount", portal_row_id=t[":id"],
                           portal_value=t["award"], differing_fields="; ".join(diffs)))
        elif ts:
            out.append(row("capital_award", r["key"], r["fy"], ds, snap, "ambiguous",
                           ambiguous_rule("report_year_id_line_fy_amount", ours_n[k], len(ts)),
                           portal_row_id=";".join(t[":id"] for t in ts)))
        elif (r["fy"], pid(r["project_id"])) in head_ids:
            h = next(h for h in heads if (int(h["reported"]), pid(h["id"])) == (r["fy"], pid(r["project_id"])))
            out.append(row("capital_award", r["key"], r["fy"], ds, snap, "differs",
                           "report_year_id (portal record broken across rows)", portal_row_id=h[":id"],
                           differing_fields="portal record broken across rows; its amount and FY are "
                                            "unreadable (data/capital/RECONCILIATION.md §2)"))
        else:
            out.append(row("capital_award", r["key"], r["fy"], ds, snap, "absent",
                           "report_year_id_line_fy_amount: no portal row"))
    # Portal-only counts only against the Council's own records (the PDF rows repeat them).
    council_years = {r["fy"] for r in recs if r["source_kind"] != "pdf_capital_sd"}
    only = Counter(int(t["reported"]) for t in portal if t[":id"] not in used and int(t["reported"]) in council_years)
    return out, only, Counter(int(t["reported"]) for t in portal)


# ------------------------------------------------------------------------------------------
# capital lines
# ------------------------------------------------------------------------------------------

def line_records(recs):
    return sorted({(r["fy"], BC.norm_line(r["budget_line"])) for r in recs
                   if r["source_kind"] != "pdf_capital_sd" and BC.norm_line(r["budget_line"])})


def capital_lines(recs, snaps):
    lines = line_records(recs)
    out, portal_rows, only = [], {}, {}
    # 46m8-77gv through data/capital's own reconciliation (the adopted release per report year).
    ds = "46m8-77gv"
    recon = {(int(v["report_year"]), v["budget_line_norm"]): v
             for v in read_csv("data/capital/council_vs_omb_by_budget_line.csv")}
    omb = defaultdict(list)
    for o in read_csv("data/capital/omb_capital_budget_council_lines.csv"):
        omb[(o["pub_date"], o["budget_line_norm"])].append(o["source_row"])
    for fy, ln in lines:
        if fy not in COVERS[ds]:
            continue
        v = recon.get((fy, ln))
        key = f"{fy}|{ln}"
        if v is None or v["verdict"] == "council_only":
            out.append(row("capital_line", key, fy, ds, snaps[ds], "absent",
                           "adopted release: line not in it"))
            continue
        diff = "" if v["verdict"] == "match" else \
            f"{v['verdict']}: council y1 {v['council_y1']}, omb y1 {v['omb_y1']}; council y2 {v['council_y2']}, omb y2 {v['omb_y2']}"
        out.append(row("capital_line", key, fy, ds, snaps[ds], "context",
                       f"adopted release {v['omb_pub_date']} (council_vs_omb_by_budget_line.csv)",
                       portal_row_id=";".join(omb.get((v["omb_pub_date"], ln), [])),
                       portal_value=v["omb_y1"], differing_fields=diff,
                       portal_as_of=v["omb_pub_date"]))
    portal_rows[ds] = Counter(int(v["report_year"]) for v in recon.values() if v["omb_y1"] not in ("", "0"))
    only[ds] = Counter(int(v["report_year"]) for v in recon.values() if v["verdict"] == "omb_only")
    # 2cmn-uidm: the latest release whose first year is the report year.
    ds = "2cmn-uidm"
    plan = defaultdict(list)
    for o in read_csv("data/capital/omb_commitment_plan_council_lines.csv"):
        plan[(int(o["yr1_fy"]), o["budget_line_norm"])].append(o)
    seen = set()
    for fy, ln in lines:
        if fy not in COVERS[ds]:
            continue
        rs = plan.get((fy, ln), [])
        key = f"{fy}|{ln}"
        if not rs:
            out.append(row("capital_line", key, fy, ds, snaps[ds], "absent",
                           "no commitment-plan release with this first year lists the line"))
            continue
        last = max(o["pub_date"] for o in rs)
        sel = [o for o in rs if o["pub_date"] == last]
        seen.add((fy, ln))
        tot = sum(Decimal(o["year1_amt_k"] or 0) for o in sel)
        out.append(row("capital_line", key, fy, ds, snaps[ds], "context",
                       f"latest release with first year {fy}: {last}",
                       portal_row_id=";".join(o["source_row"] for o in sel),
                       portal_value=f"{tot}K", portal_as_of=last))
    portal_rows[ds] = Counter(fy for (fy, ln) in plan if fy in COVERS[ds])
    only[ds] = Counter(fy for (fy, ln) in plan if (fy, ln) not in seen and
                       fy in {f for f, _ in lines})
    # djxg-kcfi: planned commitments in the one CPDB version held.
    ds = "djxg-kcfi"
    cp = defaultdict(list)
    for o in read_gz("source/open-data-djxg-kcfi/djxg-kcfi.csv.gz"):
        n = BC.norm_line(o["budgetline"].replace("-", " ", 1))
        if n:
            cp[n].append(o)
    version = sorted({o["ccpversion"] for v in cp.values() for o in v})
    if version != ["fisa_2026"]:
        raise ValueError(f"djxg-kcfi versions {version}: update COVERS['djxg-kcfi']")
    for fy, ln in lines:
        if fy not in COVERS[ds]:
            continue
        key = f"{fy}|{ln}"
        rs = cp.get(ln, [])
        if not rs:
            out.append(row("capital_line", key, fy, ds, snaps[ds], "absent",
                           f"no planned commitment on the line in CPDB {'/'.join(version)}"))
            continue
        tot = sum(Decimal(o["totalplannedcommit"] or 0) for o in rs)
        out.append(row("capital_line", key, fy, ds, snaps[ds], "context",
                       f"planned commitments in CPDB {'/'.join(version)}",
                       portal_row_id=";".join(o[":id"] for o in rs[:MAX_CANDIDATES]) +
                       (";…" if len(rs) > MAX_CANDIDATES else ""),
                       portal_value=str(tot), portal_status=f"{len(rs)} commitments",
                       portal_as_of="/".join(version)))
    council = {ln for _, ln in lines}
    council = {ln for fy, ln in lines if fy in COVERS[ds]}
    portal_rows[ds] = Counter({0: len([n for n in cp if BC.is_council_line(n)])})
    only[ds] = Counter({0: len([n for n in cp if BC.is_council_line(n) and n not in council])})
    return out, portal_rows, only, lines


# ------------------------------------------------------------------------------------------
# terms units
# ------------------------------------------------------------------------------------------

def terms_records(root=ROOT):
    """[(fy, item, agency_or_blank, [listed agencies], unit, source)]"""
    pdf_years = {}
    for path in sorted(glob.glob(os.path.join(root, "data", "fy*", "pdf", "terms", "*_terms_units.csv"))):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("unit_of_appropriation"):
                    pdf_years.setdefault(int(r["fiscal_year"]), []).append(
                        (int(r["fiscal_year"]), r["item_number"], r["agency_code"], [r["agency_code"]],
                         r["unit_of_appropriation"], os.path.relpath(path, root)))
    out = [x for v in pdf_years.values() for x in v]
    for path in sorted(glob.glob(os.path.join(root, "data", "fy*", "terms", "*.csv"))):
        fy = 2000 + int(re.search(r"fy(\d\d)", os.path.basename(path)).group(1))
        if fy in pdf_years:
            continue
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                codes = re.findall(r"\d{3}", r["agency_code"])
                for u in [u.strip() for u in r["units_of_appropriation"].split(";") if u.strip()]:
                    out.append((fy, r["item_number"], codes[0] if len(codes) == 1 else "", codes, u,
                                os.path.relpath(path, root)))
    return out


def extract_filter(manifest_rows):
    """(release per fiscal year, {(agency, unit)}) from the extract's recorded $where."""
    note = next(r["note"] for r in manifest_rows if r["file"] == "mwzb-yiwb.csv.gz")
    where = note.split("$where: ", 1)[1]
    rel = {int(fy): pub for pub, fy in re.findall(r"publication_date='(\d{8})' AND fiscal_year=(\d{4})", where)}
    pairs = set()
    for ag, us in re.findall(r"agency_number in \(([^)]*)\) AND unit_appropriation_number in \(([^)]*)\)", where):
        for a in re.findall(r"'(\w+)'", ag):
            pairs |= {(a.zfill(3), u.zfill(3)) for u in re.findall(r"'(\w+)'", us)}
    return rel, pairs


def terms_units(snap):
    ds = "mwzb-yiwb"
    rel, pairs = extract_filter(read_csv("source/open-data-mwzb-yiwb/MANIFEST.csv"))
    agg = defaultdict(lambda: [0, Decimal(0), ""])
    for o in read_gz("source/open-data-mwzb-yiwb/mwzb-yiwb.csv.gz"):
        # Releases before 2023 drop leading zeros ('40', '1'); compare padded.
        a = agg[(int(o["fiscal_year"]), o["agency_number"].zfill(3), o["unit_appropriation_number"].zfill(3))]
        a[0] += 1
        a[1] += Decimal(o["adopted_budget_amount"] or 0)
        a[2] = o["unit_appropriation_name"]
    out, nc = [], Counter()
    seen_keys = Counter()
    for fy, item, ag, agencies, unit, src in terms_records():
        base = f"{fy}|{item}|{ag or '+'.join(agencies)}|{unit}"
        seen_keys[base] += 1
        key = base if seen_keys[base] == 1 else f"{base}#{seen_keys[base]}"
        why = None
        if fy not in rel:
            why = "fiscal year before FY2017 or not in the extract"
        elif not re.fullmatch(r"\d{3}", unit):
            why = f"unit {unit!r} is not a single unit of appropriation"
        elif not any((a, unit) in pairs for a in agencies):
            why = "pair outside the extract filter"
        if why:
            nc[fy] += 1
            continue
        hits = [(a, agg[(fy, a, unit)]) for a in agencies if (fy, a, unit) in agg]
        if not hits:
            out.append(row("terms_unit", key, fy, ds, snap, "absent",
                           f"adopted release {rel[fy]}: no row for the unit"))
            continue
        a, (n, amt, name) = hits[0]
        rule = f"adopted release {rel[fy]}: agency {a}, unit {unit}" + \
            ("" if ag else " (retired CSV: unit matched under a listed agency)")
        out.append(row("terms_unit", key, fy, ds, snap, "context", rule,
                       portal_value=str(amt), portal_status=f"{n} rows; {name}", portal_as_of=rel[fy]))
    portal_rows = Counter(fy for fy, _, _ in agg)
    return out, nc, portal_rows, rel


# ------------------------------------------------------------------------------------------
# assemble
# ------------------------------------------------------------------------------------------

def csv_text(rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fields})
    return buf.getvalue()


def gz_bytes(text):
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0, compresslevel=9) as g:
        g.write(text.encode("utf-8"))
    return out.getvalue()


def coverage_rows(family, ds, snap, xw, records_by_year, portal_rows, only, not_covered=None, note=""):
    st = defaultdict(Counter)
    for r in xw:
        if r["dataset_id"] == ds:
            st[int(r["fiscal_year"])][r["match_status"]] += 1
            if r["match_status"] == "ambiguous" and CERTAIN in r["match_rule"]:
                st[int(r["fiscal_year"])]["ambiguous_present"] += 1
    out = []
    for fy in sorted(records_by_year):
        cov = fy in COVERS[ds]
        c = st[fy]
        nc = (not_covered or {}).get(fy, 0) if cov else records_by_year[fy]
        out.append({"family": family, "dataset_id": ds, "fiscal_year": fy, "snapshot_date": snap,
                    "covered": "yes" if cov else "no", "records": records_by_year[fy],
                    **{s: c[s] for s in STATUSES if s != "not_covered"},
                    "ambiguous_present": c["ambiguous_present"], "not_covered": nc,
                    "portal_rows": portal_rows.get(fy, 0) if cov else "",
                    "portal_only": only.get(fy, 0) if cov else "", "note": note})
    return out


def build():
    snaps = {ds: snapshot_date(ds) for dss in FAMILY_DATASETS.values() for ds in dss}
    xw, cov = defaultdict(list), []
    # expense
    recs = expense_records()
    by_year = Counter(int(r["fiscal_year"]) for r in recs)
    a, only_a, prow_a, mocs = expense_4d7f(recs, snaps["4d7f-74pe"])
    b, only_b, prow_b = expense_ujre(recs, snaps["ujre-m2tj"], mocs)
    xw["expense"] = a + b
    cov += coverage_rows("expense", "4d7f-74pe", snaps["4d7f-74pe"], a, by_year, prow_a, only_a,
                         note="keys-only extract: EIN and amount compared")
    cov += coverage_rows("expense", "ujre-m2tj", snaps["ujre-m2tj"], b, by_year, prow_b, only_b,
                         note="latest posting per award (2021-06-09)")
    # capital awards
    crec = capital_records()
    by_year = Counter(r["fy"] for r in crec if r["source_kind"] != "pdf_capital_sd")
    c, only_c, prow_c = capital_t474(crec, snaps["t474-a92g"])
    xw["capital_award"] = c
    cov += coverage_rows("capital_award", "t474-a92g", snaps["t474-a92g"],
                         [x for x in c if not x["record_key"].startswith("pdf|")], by_year, prow_c, only_c,
                         note="Council records (workbook, t474); PDF rows are in the crosswalk only")
    # capital lines
    d, prow_d, only_d, lines = capital_lines(crec, snaps)
    xw["capital_line"] = d
    by_year = Counter(fy for fy, _ in lines)
    for ds in FAMILY_DATASETS["capital_line"]:
        note = {"46m8-77gv": "adopted release per report year",
                "2cmn-uidm": "latest release with that first year",
                "djxg-kcfi": "one current CPDB version (fisa_2026): covers FY2026 on only; portal "
                             "counts are Council lines in it, those years together"}[ds]
        pr, on = prow_d[ds], only_d[ds]
        if ds == "djxg-kcfi":
            pr = {fy: pr[0] for fy in by_year if fy in COVERS[ds]}
            on = {max(by_year): on[0]}
        cov += coverage_rows("capital_line", ds, snaps[ds], d, by_year, pr, on, note=note)
    # terms units
    e, nc_e, prow_e, rel = terms_units(snaps["mwzb-yiwb"])
    xw["terms_unit"] = e
    by_year = Counter(fy for fy, *_ in terms_records())
    cov += coverage_rows("terms_unit", "mwzb-yiwb", snaps["mwzb-yiwb"], e, by_year, prow_e, {},
                         not_covered=nc_e, note="adopted-release extract; portal_rows = (agency, unit) "
                                                "pairs in it; portal-only not counted (extract)")
    files = {}
    for fam, rows in xw.items():
        rows.sort(key=lambda r: (r["dataset_id"], str(r["fiscal_year"]), r["record_key"]))
        files[f"{OUT}/crosswalk_{fam}.csv"] = csv_text(rows, FIELDS)
        files[f"{OUT}/crosswalk_history_{fam}.csv.gz"] = history(fam, rows)
    files[f"{OUT}/coverage.csv"] = csv_text(cov, COVERAGE_FIELDS)
    return files


def history(fam, rows):
    """Earlier snapshots' rows kept, this build's (dataset, snapshot) replaced, gzip mtime 0."""
    path = p(f"{OUT}/crosswalk_history_{fam}.csv.gz")
    keep = []
    current = {(r["dataset_id"], r["snapshot_date"]) for r in rows}
    if os.path.exists(path):
        keep = [r for r in read_gz(f"{OUT}/crosswalk_history_{fam}.csv.gz")
                if (r["dataset_id"], r["snapshot_date"]) not in current]
    allr = keep + rows
    allr.sort(key=lambda r: (r["dataset_id"], r["snapshot_date"], str(r["fiscal_year"]), r["record_key"]))
    return gz_bytes(csv_text(allr, FIELDS))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    files = build()
    bad = 0
    for rel, content in sorted(files.items()):
        data = content if isinstance(content, bytes) else content.encode("utf-8")
        full = p(rel)
        if a.write:
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "wb") as f:
                f.write(data)
            print(f"wrote {rel} ({len(data):,} bytes)")
        else:
            cur = open(full, "rb").read() if os.path.exists(full) else None
            if cur != data:
                bad += 1
                print(f"DRIFT {rel}")
            else:
                print(f"ok    {rel}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
