#!/usr/bin/env python3
"""build_capital_council.py -- the Council capital dataset from structured sources only, plus
OMB's adopted capital budget and commitment plan as reference tables, and a reconciliation by
budget line (GitHub #89 A6, A7, B8-B10).

    python3 code/build_capital_council.py            summary
    python3 code/build_capital_council.py --write    write data/capital/*
    python3 code/build_capital_council.py --check    exit 1 if anything committed is stale

Sources (every one committed, every one pinned by sha256 in its folder's manifest):
  The Council's own capital workbooks ("Capital-Database"), preferred wherever they exist:
    FY2015, FY2016, FY2017   Internet Archive captures, source/wayback-council/files/
    FY2026                   Internet Archive capture of rnd.council.nyc.gov (2025-12-03),
                             content-identical to the 2026-07-15 RnD download (git 98f1086)
    FY2027                   rnd.council.nyc.gov, source/expense-funding-disclosure/ (2026-10-12)
  NYC Open Data t474-a92g "City Council Capital Budget" (the Council's own publication), for
    the report years with no workbook: FY2019-FY2025. Its FY2026 rows are diffed against the
    FY2026 workbook, never mixed in. FY2018 exists in neither: a gap, stated.
  NYC Open Data 46m8-77gv "Capital Budget" (OMB, whole dollars) and 2cmn-uidm "Capital
    Commitment Plan" (OMB, THOUSANDS of dollars): reference tables, Council-series lines only.

Workbooks are read with the disclosure parser's stdlib OOXML reader (zipfile + ElementTree);
openpyxl is kept for the independent audit (code/audit_capital.py).

Outputs, data/capital/:
  council_capital_awards.csv           one row per (Council record, fiscal-year column) with a
                                       non-zero amount (a record whose amounts are all zero
                                       keeps one row at 0, so no record is lost)
  omb_capital_budget_council_lines.csv 46m8-77gv rows on Council-series budget lines (D / DN)
  omb_commitment_plan_council_lines.csv 2cmn-uidm rows on Council-series lines ($ thousands)
  council_vs_omb_by_budget_line.csv    per report year and budget line: the Council table's sum
                                       vs OMB's adopted release, first year and second year
  RECONCILIATION.md                    the same, summarized; the t474 / FY2026 workbook diff;
                                       every stripped, malformed or repaired row
Every sum is this repo's arithmetic, never a Council or OMB figure.

Budget line normal form (`budget_line_norm`): agency code, one space, the line ("P D018"),
from any of "P  D018", "P-D018", "P D018", "PD018" (2cmn-uidm drops the space; its own
`projtype` column splits it). A Council-series line is one whose line part starts with D.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import io
import os
import re
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse_expense_disclosure as P

ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "data", "capital")
WAYBACK = os.path.join(ROOT, "source", "wayback-council")
RND = os.path.join(ROOT, "source", "expense-funding-disclosure")

# report year -> (path relative to ROOT, manifest path, manifest key)
WORKBOOKS = {
    2015: "source/wayback-council/files/20141025112732/Capital-Database-FY15.xlsx",
    2016: "source/wayback-council/files/20150910155210/Capital-Database-FY16.xlsx",
    2017: "source/wayback-council/files/20170704093017/Capital-Database-FY17.xlsx",
    2026: "source/wayback-council/files/20251203222510/Capital-Database.xlsx",
    2027: "source/expense-funding-disclosure/Capital-Database.xlsx",
}
T474 = "source/open-data-t474-a92g/t474-a92g.csv.gz"
OMB_BUDGET = "source/open-data-46m8-77gv/46m8-77gv.csv.gz"
OMB_PLAN = "source/open-data-2cmn-uidm/2cmn-uidm.csv.gz"
T474_YEARS = range(2019, 2026)      # report years taken from t474 (no workbook)
DIFF_YEARS = (2026,)                # report years with both: diffed, workbook wins
MISSING_YEARS = (2018,)

# Header text -> field. Mapped by text, never by position; an unknown header is a stop.
HEADERS = {
    "project": "project_id", "project id": "project_id",
    "borough": "borough", "boro": "borough", "polboro": "borough",
    "district(s)": "council_district", "districts": "council_district", "cd": "council_district",
    "sponsors": "sponsor", "sponsor": "sponsor",
    "fiscal year funded": "fiscal_year_funded",
    "title": "title",
    "description": "description", "desc": "description", "project description": "description",
    "budget line": "budget_line", "budline": "budget_line",
}
# FY2015's "Project" column holds BUDGET LINES ("AG D001", "PW-DN846"), not project IDs: every
# value has the budget-line shape (checked on every build, a stop otherwise), and FY2015 has no
# other budget-line column. FY2016 has project IDs and no budget line at all.
HEADER_OVERRIDES = {2015: {"project": "budget_line"}}

FIELDS = ["report_year", "amount_fy", "project_id", "borough", "budget_line",
          "budget_line_norm", "council_district", "sponsor", "title", "description", "amount",
          "source_kind", "source_file", "source_row", "row_flag"]
ROW_FLAGS = ("split_record_amount_unknown",)
OMB_BUDGET_FIELDS = ["pub_date", "release", "proj_type", "budget_line", "budget_line_norm",
                     "budget_line_title", "funding", "yr1_fy", "year1_amt", "year2_amt",
                     "year3_amt", "year4_amt", "source_row"]
OMB_PLAN_FIELDS = ["pub_date", "projtype", "budget_line", "budget_line_norm",
                   "budget_line_desc", "funding", "num_yrs_prsnt", "yr1_fy", "year1_amt_k",
                   "year2_amt_k", "year3_amt_k", "year4_amt_k", "year5_amt_k", "source_row"]
RECON_FIELDS = ["report_year", "budget_line_norm", "omb_pub_date", "council_rows",
                "council_y1", "omb_y1", "council_y2", "omb_y2", "verdict"]

_LINE = re.compile(r"([A-Z]{1,2})[\s-]+([A-Z0-9]+)")


# ---------------------------------------------------------------- small helpers

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_sha(rel):
    """The sha256 a committed source file must have, from its folder's manifest."""
    if rel.startswith("source/wayback-council/"):
        key = rel.removeprefix("source/wayback-council/")
        man = os.path.join(WAYBACK, "MANIFEST.csv")
    elif rel.startswith("source/expense-funding-disclosure/"):
        key, man = os.path.basename(rel), os.path.join(RND, "MANIFEST.csv")
    else:
        key, man = os.path.basename(rel), os.path.join(ROOT, os.path.dirname(rel), "MANIFEST.csv")
    with open(man, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["file"] == key:
                return r["sha256"]
    raise ValueError(f"{rel}: no row in {os.path.relpath(man, ROOT)}")


def checked(rel):
    p = os.path.join(ROOT, rel)
    if sha256(p) != manifest_sha(rel):
        raise ValueError(f"{rel}: sha256 differs from its manifest")
    return p


def norm_line(raw, projtype=None):
    """Budget line -> 'AG DN04L' normal form, or '' if it has no recognizable shape. With
    `projtype` (OMB's own column) the agency code is split off by it, so 'PVDN132' works."""
    s = P._clean(raw).upper()
    if not s:
        return ""
    if projtype:
        pt = P._clean(projtype).upper()
        if s.startswith(pt):
            rest = re.sub(r"[\s-]+", "", s[len(pt):])
            return f"{pt} {rest}" if rest else ""
    m = _LINE.fullmatch(s)
    return f"{m.group(1)} {m.group(2)}" if m else ""


def is_council_line(norm):
    return bool(norm) and norm.split(" ", 1)[1].startswith("D")


def amount(text):
    d = P.parse_amount_text(text)
    if d is None:
        raise ValueError(f"not an amount: {text!r}")
    return d


def fmt(d):
    return P.format_amount(d)


# ---------------------------------------------------------------- Council workbooks

def read_workbook(fy, rel=None):
    """-> (records, stripped, header_note). records: [{field..., 'amounts': {fy: Decimal},
    'source_row': n}]. A row with every text field blank whose amounts equal the column sums of
    the rows above it is a TOTALS row (FY2015, FY2016) and is stripped and listed; any other
    row without a project/budget line and title is a stop."""
    rel = rel or WORKBOOKS[fy]
    import zipfile
    z = zipfile.ZipFile(checked(rel))
    sheet_path, sheet = P._sheet_and_name(z)
    rows = P._rows(z, sheet_path, P._shared_strings(z))
    _hrn, hdr = next(rows)
    over = HEADER_OVERRIDES.get(fy, {})
    col_field, fy_cols = {}, {}
    for col, raw in hdr.items():
        h = " ".join(P._clean(raw).lower().split())
        if not h:
            continue
        m = re.fullmatch(r"fy(\d\d)", h)
        if m:
            fy_cols[col] = 2000 + int(m.group(1))
        elif h in over:
            col_field[col] = over[h]
        elif h in HEADERS:
            col_field[col] = HEADERS[h]
        else:
            raise ValueError(f"{rel}: unmapped header {raw!r} in column {col}")
    records, stripped = [], []
    for rn, cells in rows:
        if not any(P._clean(v) for v in cells.values()):
            continue
        rec = {f: P._clean(cells.get(c)) for c, f in col_field.items()}
        extra = [c for c in cells if P._clean(cells.get(c)) and c not in col_field
                 and c not in fy_cols]
        if extra:
            raise ValueError(f"{rel} row {rn}: values in unheaded columns {extra}")
        rec["amounts"] = {y: amount(cells.get(c) or "0") for c, y in fy_cols.items()}
        rec["source_row"] = rn
        if not any(rec.get(f) for f in col_field.values()):
            stripped.append(rec)
            continue
        records.append(rec)
    for s in stripped:
        sums = {y: sum((r["amounts"][y] for r in records), Decimal(0)) for y in fy_cols.values()}
        if s["amounts"] != sums:
            raise ValueError(f"{rel} row {s['source_row']}: a row with no text that is not the "
                             f"column totals {s['amounts']} vs {sums}")
    if fy in HEADER_OVERRIDES:
        bad = [r["budget_line"] for r in records if not norm_line(r["budget_line"])]
        if bad:
            raise ValueError(f"{rel}: 'Project' values that are not budget lines: {bad[:5]}")
    note = f"sheet {sheet!r}; fiscal-year columns {sorted(fy_cols.values())}"
    return records, stripped, note


def workbook_rows(fy):
    """council_capital_awards rows for one workbook year, plus the report's notes."""
    records, stripped, note = read_workbook(fy)
    rel = WORKBOOKS[fy]
    out = []
    for r in records:
        amts = {y: a for y, a in sorted(r["amounts"].items()) if a != 0} or {fy: Decimal(0)}
        for y, a in amts.items():
            out.append({
                "report_year": fy, "amount_fy": y, "project_id": r.get("project_id", ""),
                "borough": r.get("borough", ""), "budget_line": r.get("budget_line", ""),
                "budget_line_norm": norm_line(r.get("budget_line", "")),
                "council_district": r.get("council_district", ""),
                "sponsor": r.get("sponsor", ""), "title": r.get("title", ""),
                "description": r.get("description", ""), "amount": fmt(a),
                "source_kind": "council_workbook", "source_file": rel,
                "source_row": r["source_row"], "row_flag": ""})
    return out, records, stripped, note


# ---------------------------------------------------------------- Open Data t474-a92g

def read_gz(rel):
    with gzip.open(checked(rel), "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def t474_split(rows):
    """Separate t474's well-formed rows from the fragments of records that were broken across
    rows (a quote or line break inside a description). -> (good, heads, tails).
    head: report year, ID and budget line present, no award and no fiscal year (the record's
          first half). tail: `reported` is not a year (the rest of a description spilled in)."""
    good, heads, tails = [], [], []
    for r in rows:
        year_ok = bool(re.fullmatch(r"20\d\d", r["reported"]))
        if not year_ok:
            tails.append(r)
        elif not r["award"] and not r["fiscal_year"]:
            heads.append(r)
        elif r["award"] and re.fullmatch(r"FY\d\d", r["fiscal_year"]):
            good.append(r)
        else:
            raise ValueError(f"t474 {r[':id']}: unrecognized row shape {r}")
    return good, heads, tails


def t474_rows(rows, years=T474_YEARS):
    good, heads, tails = t474_split(rows)
    out = []
    for r in good + heads:
        ry = int(r["reported"])
        if ry not in years:
            continue
        head = r in heads
        out.append({
            "report_year": ry, "amount_fy": "" if head else 2000 + int(r["fiscal_year"][2:]),
            "project_id": P._clean(r["id"]), "borough": P._clean(r["borough"]),
            "budget_line": P._clean(r["budget_line"]),
            "budget_line_norm": norm_line(r["budget_line"]),
            "council_district": r["council_district"], "sponsor": P._clean(r["sponsor"]),
            "title": P._clean(r["title"]), "description": P._clean(r["description"]),
            "amount": "" if head else fmt(amount(r["award"])),
            "source_kind": "open_data_t474", "source_file": T474, "source_row": r[":id"],
            "row_flag": "split_record_amount_unknown" if head else ""})
    return out, heads, tails


def fy26_diff(wb_rows, t474_all):
    """The FY2026 workbook vs t474's report-2026 rows, keyed on (project ID with whitespace
    collapsed, fiscal year): rows only in one, and amount differences."""
    good, heads, _ = t474_split(t474_all)

    def key(pid, y):
        return (" ".join(pid.split()), y)
    wb = collections.defaultdict(list)
    for r in wb_rows:
        if r["report_year"] == 2026:
            wb[key(r["project_id"], r["amount_fy"])].append(Decimal(r["amount"]))
    od = collections.defaultdict(list)
    for r in good:
        if r["reported"] == "2026":
            od[key(r["id"], 2000 + int(r["fiscal_year"][2:]))].append(amount(r["award"]))
    only_wb = sorted(k for k in wb if k not in od)
    only_od = sorted(k for k in od if k not in wb)
    differ = sorted((k, wb[k], od[k]) for k in wb if k in od and sorted(wb[k]) != sorted(od[k]))
    head26 = [h for h in heads if h["reported"] == "2026"]
    proven = []
    for h in head26:
        k = key(h["id"], 2026)
        if k in wb and len(wb[k]) == 1:
            proven.append((h[":id"], h["id"], wb[k][0]))

    def tot(d):
        return sum((sum(v) for v in d.values()), Decimal(0))
    return {"wb_rows": sum(len(v) for v in wb.values()), "od_rows": sum(len(v) for v in od.values()),
            "od_heads": len(head26), "wb_total": tot(wb), "od_total": tot(od),
            "only_wb": [(k, wb[k]) for k in only_wb], "only_od": [(k, od[k]) for k in only_od],
            "differ": differ, "proven": proven}


# ---------------------------------------------------------------- OMB reference tables

def omb_budget_rows(rows):
    """46m8-77gv rows on Council-series lines. `release` is 'adopted' for the last release of
    each first fiscal year (its pub_date is in July in every year 2018-2026), else ''."""
    last = {}
    for r in rows:
        y = r["yr1_fy"]
        last[y] = max(last.get(y, ""), r["pub_date"])
    out = []
    for r in rows:
        n = norm_line(r["budline"], r["proj_type"])
        if not is_council_line(n):
            continue
        out.append({"pub_date": r["pub_date"],
                    "release": "adopted" if r["pub_date"] == last[r["yr1_fy"]] else "",
                    "proj_type": r["proj_type"], "budget_line": r["budline"],
                    "budget_line_norm": n, "budget_line_title": P._clean(r["budline_title"]),
                    "funding": r["funding"], "yr1_fy": r["yr1_fy"],
                    **{f"year{i}_amt": r[f"year{i}_amt"] for i in range(1, 5)},
                    "source_row": r[":id"]})
    out.sort(key=lambda r: (r["pub_date"], r["budget_line_norm"], r["funding"], r["source_row"]))
    return out


def omb_plan_rows(rows):
    """2cmn-uidm rows on Council-series lines (amounts in THOUSANDS, as published). The one row
    with no release, line or year (its amounts look like grand totals) is stripped and listed."""
    out, stripped = [], []
    for r in rows:
        if not r["pub_date"] and not r["budline"]:
            stripped.append(r)
            continue
        n = norm_line(r["budline"], r["projtype"])
        if not is_council_line(n):
            continue
        out.append({"pub_date": r["pub_date"], "projtype": r["projtype"],
                    "budget_line": r["budline"], "budget_line_norm": n,
                    "budget_line_desc": P._clean(r["budline_desc"]), "funding": r["funding"],
                    "num_yrs_prsnt": r["num_yrs_prsnt"], "yr1_fy": r["yr1_fy"],
                    **{f"year{i}_amt_k": r[f"year{i}_amt"] for i in range(1, 6)},
                    "source_row": r[":id"]})
    out.sort(key=lambda r: (r["pub_date"], r["budget_line_norm"], r["funding"], r["source_row"]))
    return out, stripped


# ---------------------------------------------------------------- reconciliation

def reconcile(council, omb):
    """Per report year Y with an OMB adopted release whose first year is Y: for every
    Council-series budget line in either, the Council table's sum for fiscal years Y and Y+1
    against OMB's year1_amt and year2_amt summed over funding sources. verdict: match /
    differ / council_only / omb_only. Rows with no amount (split records) are counted apart."""
    adopted = collections.defaultdict(lambda: [Decimal(0), Decimal(0)])
    pub = {}
    for r in omb:
        if r["release"] != "adopted":
            continue
        y = int(r["yr1_fy"])
        pub[y] = r["pub_date"]
        adopted[(y, r["budget_line_norm"])][0] += Decimal(r["year1_amt"])
        adopted[(y, r["budget_line_norm"])][1] += Decimal(r["year2_amt"])
    mine = collections.defaultdict(lambda: [Decimal(0), Decimal(0), 0])
    for r in council:
        y = r["report_year"]
        if y not in pub or not is_council_line(r["budget_line_norm"]) or r["amount"] == "":
            continue
        k = (y, r["budget_line_norm"])
        mine[k][2] += 1
        if r["amount_fy"] == y:
            mine[k][0] += Decimal(r["amount"])
        elif r["amount_fy"] == y + 1:
            mine[k][1] += Decimal(r["amount"])
    out = []
    for y in sorted(pub):
        lines = sorted({k[1] for k in mine if k[0] == y} | {k[1] for k in adopted if k[0] == y})
        for ln in lines:
            c, o = mine.get((y, ln)), adopted.get((y, ln))
            if c is None:
                v = "omb_only"
            elif o is None:
                v = "council_only"
            else:
                v = "match" if c[:2] == o else "differ"
            out.append({"report_year": y, "budget_line_norm": ln, "omb_pub_date": pub[y],
                        "council_rows": c[2] if c else 0,
                        "council_y1": fmt(c[0]) if c else "", "omb_y1": fmt(o[0]) if o else "",
                        "council_y2": fmt(c[1]) if c else "", "omb_y2": fmt(o[1]) if o else "",
                        "verdict": v})
    return out


def recon_summary(recon):
    s = collections.defaultdict(collections.Counter)
    for r in recon:
        s[r["report_year"]][r["verdict"]] += 1
    return s


# ---------------------------------------------------------------- build

def build():
    council, notes, stripped_all, wb_records = [], {}, {}, {}
    wb_rows26 = []
    for fy in sorted(WORKBOOKS):
        rows, records, stripped, note = workbook_rows(fy)
        council += rows
        notes[fy] = (note, len(records))
        stripped_all[fy] = stripped
        wb_records[fy] = records
        if fy == 2026:
            wb_rows26 = rows
    t474_all = read_gz(T474)
    trows, heads, tails = t474_rows(t474_all)
    council += trows
    council.sort(key=lambda r: (r["report_year"], r["source_kind"], str(r["source_row"]).zfill(8),
                                str(r["amount_fy"])))
    omb_b = omb_budget_rows(read_gz(OMB_BUDGET))
    omb_p, plan_stripped = omb_plan_rows(read_gz(OMB_PLAN))
    recon = reconcile(council, omb_b)
    diff = fy26_diff(wb_rows26, t474_all)
    return {"council": council, "notes": notes, "stripped": stripped_all, "heads": heads,
            "tails": tails, "omb_budget": omb_b, "omb_plan": omb_p,
            "plan_stripped": plan_stripped, "recon": recon, "diff26": diff,
            "wb_records": wb_records}


def csv_text(fields, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def _usd(d):
    return P._usd(d)


def report_text(b):
    c = b["council"]
    by = collections.defaultdict(lambda: [0, Decimal(0), set()])
    for r in c:
        k = (r["report_year"], r["source_kind"])
        by[k][0] += 1
        by[k][2].add(r["source_row"])
        if r["amount"] != "" and r["amount_fy"] == r["report_year"]:
            by[k][1] += Decimal(r["amount"])
    L = ["# Council capital: dataset report and reconciliation by budget line", "",
         ("Generated by `code/build_capital_council.py` from committed sources only (no network). "
         "Every sum below is this repo's arithmetic, not a Council or OMB figure. Re-running it "
         "reproduces this file byte for byte; `--check` fails if it is stale."), "",
         "## 1. What the table holds", "",
         "| report year | source | records | rows | first-year amount ($) |",
         "|---|---|---:|---:|---:|"]
    for (y, kind), (n, tot, recs) in sorted(by.items()):
        L.append(f"| FY{y} | {kind} | {len(recs):,} | {n:,} | {_usd(tot)} |")
    L += ["", (f"FY{MISSING_YEARS[0]} is in no source found (no Council workbook, and t474-a92g "
          "starts at FY2019). The first-year amount is the sum of rows whose `amount_fy` is "
          "the report year; out-year rows are in the table under their own `amount_fy`."), ""]
    L += ["## 2. Rows stripped or flagged", "",
          ("**Workbook totals rows** (FY2015 and FY2016 end in one row whose amounts equal the "
          "column sums above it; stripped, never counted):"), ""]
    for fy, st in sorted(b["stripped"].items()):
        for s in st:
            L.append(f"- FY{fy} row {s['source_row']}: "
                     + ", ".join(f"FY{y} {_usd(a)}" for y, a in sorted(s["amounts"].items())))
    L += ["", ("**t474-a92g records broken across rows** (a quote or line break inside a "
          "description split each record). A record's first row keeps its ID and budget line "
          "but has no award and no fiscal year; the spilled text fragments carry what looks "
          "like an award. Which fragment belongs to which record cannot be shown from the "
          "Council's own files for these years, so first rows are kept with a blank amount and "
          "`row_flag = split_record_amount_unknown`, and fragments are listed here, not used:"), ""]
    for h in b["heads"]:
        L.append(f"- first row `{h[':id']}`: report {h['reported']}, ID `{h['id']}`, "
                 f"line `{h['budget_line']}`, {h['title']!r}"
                 + (" (FY2026: not in the table; the FY2026 workbook is used, §4)"
                    if h["reported"] == "2026" else ""))
    for t in b["tails"]:
        L.append(f"- fragment `{t[':id']}`: " + ", ".join(
            f"{k}={v!r}" for k, v in t.items() if v and not k.startswith(":")))
    L += ["", "## 3. Council vs OMB adopted capital budget, by budget line", "",
          ("OMB `46m8-77gv`, the adopted release for each first fiscal year (the last release of "
          "that year, published in July), summed over funding sources, `year1_amt` and "
          "`year2_amt`, against the Council table's rows for the same report year with "
          "`amount_fy` = that year and the next. Council-series lines only (`D`, `DN`). "
          "`match` = both years equal to the dollar."), "",
          "| report year | OMB release | lines | match | differ | Council only | OMB only |",
          "|---|---|---:|---:|---:|---:|---:|"]
    pub = {r["report_year"]: r["omb_pub_date"] for r in b["recon"]}
    for y, cnt in sorted(recon_summary(b["recon"]).items()):
        n = sum(cnt.values())
        L.append(f"| FY{y} | {pub[y]} | {n} | {cnt['match']} | {cnt['differ']} | "
                 f"{cnt['council_only']} | {cnt['omb_only']} |")
    L += ["", ("Per line: `council_vs_omb_by_budget_line.csv`. The Council side for FY2019–FY2025 "
          "is t474-a92g; for FY2026 and FY2027 the Council's workbook."), ""]
    y27 = [r for r in b["recon"] if r["report_year"] == 2027]
    if y27:
        cl = [r for r in y27 if r["verdict"] in ("match", "differ", "council_only")]
        L += [(f"**FY2027:** {sum(r['verdict'] == 'match' for r in y27)} of {len(cl)} Council "
              f"budget lines match OMB's July 2026 adopted release in both FY2027 and FY2028. "
              f"Lines that differ:"), ""]
        for r in y27:
            if r["verdict"] == "differ":
                L.append(f"- `{r['budget_line_norm']}` Council {_usd(Decimal(r['council_y1']))} / "
                         f"{_usd(Decimal(r['council_y2']))}, OMB {_usd(Decimal(r['omb_y1']))} / "
                         f"{_usd(Decimal(r['omb_y2']))}")
        L += ["", "OMB lines in the Council series with no Council row:", ""]
        for r in y27:
            if r["verdict"] == "omb_only":
                L.append(f"- `{r['budget_line_norm']}` OMB {_usd(Decimal(r['omb_y1']))} / "
                         f"{_usd(Decimal(r['omb_y2']))}")
        ct = sum(Decimal(r["council_y1"] or 0) for r in y27)
        ot = sum(Decimal(r["omb_y1"] or 0) for r in y27)
        L += ["", (f"Totals FY2027: Council {_usd(ct)}, OMB {_usd(ot)}, difference "
              f"{_usd(ot - ct)}."), ""]
    d = b["diff26"]
    L += ["## 4. FY2026: the Council's workbook vs t474-a92g", "",
          (f"Keyed on (project ID, whitespace collapsed; fiscal year). Workbook {d['wb_rows']:,} "
          f"rows, {_usd(d['wb_total'])}; t474 {d['od_rows']:,} well-formed rows, "
          f"{_usd(d['od_total'])}, plus {d['od_heads']} record(s) broken across rows (§2). "
          f"The table uses the workbook."), ""]
    for k, v in d["only_wb"]:
        L.append(f"- only in the workbook: `{k[0]}` FY{k[1]} {', '.join(_usd(x) for x in v)}")
    for k, v in d["only_od"]:
        L.append(f"- only in t474: `{k[0]}` FY{k[1]} {', '.join(_usd(x) for x in v)}")
    for k, a, o in d["differ"]:
        L.append(f"- amount differs: `{k[0]}` FY{k[1]} workbook {a} vs t474 {o}")
    for rid, pid, a in d["proven"]:
        L.append(f"- broken t474 record `{rid}` (`{pid}`): the workbook proves its FY2026 amount, "
                 f"{_usd(a)}")
    L += ["", "## 5. Reference tables", "",
          (f"- `omb_capital_budget_council_lines.csv`: {len(b['omb_budget']):,} rows of "
          f"`46m8-77gv` on Council-series lines, every release, whole dollars; `release` = "
          f"`adopted` marks the July release."),
          (f"- `omb_commitment_plan_council_lines.csv`: {len(b['omb_plan']):,} rows of "
          f"`2cmn-uidm` on Council-series lines, every release, **thousands of dollars** as "
          f"published."), ""]
    for s in b["plan_stripped"]:
        L.append(f"- stripped from `2cmn-uidm`: `{s[':id']}`, no release, line or year; "
                 f"amounts {s['year1_amt']} / {s['year2_amt']} / {s['year3_amt']} / "
                 f"{s['year4_amt']} ($K), the size of grand totals.")
    return "\n".join(L) + "\n"


def outputs(b):
    return {
        os.path.join(OUT_DIR, "council_capital_awards.csv"): csv_text(FIELDS, b["council"]),
        os.path.join(OUT_DIR, "omb_capital_budget_council_lines.csv"):
            csv_text(OMB_BUDGET_FIELDS, b["omb_budget"]),
        os.path.join(OUT_DIR, "omb_commitment_plan_council_lines.csv"):
            csv_text(OMB_PLAN_FIELDS, b["omb_plan"]),
        os.path.join(OUT_DIR, "council_vs_omb_by_budget_line.csv"):
            csv_text(RECON_FIELDS, b["recon"]),
        os.path.join(OUT_DIR, "RECONCILIATION.md"): report_text(b),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    b = build()
    files = outputs(b)
    if a.check:
        bad = P.stale(files)
        for path, why in bad:
            print(f"STALE ({why}): {os.path.relpath(path, ROOT)}")
        print(f"check: {len(files)} files, {len(bad)} stale")
        return 1 if bad else 0
    if a.write:
        P.write_files(files)
        for p in sorted(files):
            print(f"wrote {os.path.relpath(p, ROOT)}")
    for y, cnt in sorted(recon_summary(b["recon"]).items()):
        print(f"FY{y}: {dict(cnt)}")
    print(f"council rows {len(b['council'])}; heads {len(b['heads'])}; tails {len(b['tails'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
