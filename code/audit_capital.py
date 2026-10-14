#!/usr/bin/env python3
"""Adversarial audit of the Council capital dataset (data/capital/), GitHub #89 A6-A7.

Independence. code/build_capital_council.py reads the workbooks with the disclosure parser's
stdlib OOXML reader and normalizes budget lines with its own function. This script imports
neither: it re-reads every Council workbook with openpyxl, maps headers by its own keyword
rules, reads the Open Data files with gzip + csv, and re-spells budget lines by its own regex.
Each question can fail; code/test_audit_capital.py shows it does, on constructed defects.

Run:
  python3 code/audit_capital.py            print the findings
  python3 code/audit_capital.py --write    write data/capital/CAPITAL-AUDIT.md
  python3 code/audit_capital.py --check    exit 1 if that report is stale

Needs openpyxl (code/requirements.txt). No network.
"""
import argparse
import collections
import csv
import gzip
import os
import re
import sys
import warnings
from decimal import ROUND_HALF_UP, Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "capital")
REPORT = os.path.join(DATA, "CAPITAL-AUDIT.md")
T474 = os.path.join(ROOT, "source", "open-data-t474-a92g", "t474-a92g.csv.gz")
OMB_BUDGET = os.path.join(ROOT, "source", "open-data-46m8-77gv", "46m8-77gv.csv.gz")
MAX_EX = 6


def fold(v):
    """Cell -> text the way the dataset documents it: whitespace runs to one space, trimmed,
    integral numbers without '.0'."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return " ".join(str(v).split())


def line_norm(raw):
    m = re.fullmatch(r"([A-Z]{1,2})[\s-]+([A-Z0-9]+)", " ".join(str(raw or "").upper().split()))
    return f"{m.group(1)} {m.group(2)}" if m else ""


def field_of(header):
    """This script's own header rule (keywords, not the builder's table)."""
    h = " ".join(str(header or "").lower().split())
    if re.fullmatch(r"fy\d\d", h):
        return ("fy", 2000 + int(h[2:]))
    if "desc" in h:   # "PROJECT DESCRIPTION" (FY2027) is a description, not an ID
        return "description"
    if "boro" in h:   # "Borough", "BORO", FY2017's "POLBORO"
        return "borough"
    for key, f in (("budget line", "budget_line"), ("budline", "budget_line"),
                   ("project", "project_id"), ("boro", "borough"), ("district", "council_district"),
                   ("cd", "council_district"), ("sponsor", "sponsor"), ("title", "title"),
                   ("desc", "description"), ("fiscal year funded", "fiscal_year_funded")):
        if h == key or h.startswith(key):
            return f
    return None


def read_workbook(path, fy):
    """-> ({source_row: {field: text, 'amounts': {fy: Decimal}}}, [text-less rows' amounts])."""
    import openpyxl
    warnings.simplefilter("ignore")
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    fields = [field_of(h) for h in rows[0]]
    if fy == 2015:   # documented in the dataset: FY2015's "Project" column holds budget lines
        fields = ["budget_line" if f == "project_id" else f for f in fields]
    recs, textless = {}, []
    for i, r in enumerate(rows[1:], start=2):
        if not any(fold(v) for v in r):
            continue
        rec = {"amounts": {}}
        for f, v in zip(fields, r):
            if isinstance(f, tuple):
                rec["amounts"][f[1]] = Decimal(repr(float(v))) if v not in (None, "") else Decimal(0)
            elif f:
                rec[f] = fold(v)
        if any(rec.get(k) for k in rec if k != "amounts"):
            recs[i] = rec
        else:
            textless.append(rec["amounts"])
    return recs, textless


def load(data_dir=DATA):
    with open(os.path.join(data_dir, "council_capital_awards.csv"), newline="",
              encoding="utf-8") as f:
        table = list(csv.DictReader(f))
    with open(os.path.join(data_dir, "council_vs_omb_by_budget_line.csv"), newline="",
              encoding="utf-8") as f:
        recon = list(csv.DictReader(f))
    return {"table": table, "recon": recon}


def result(status, count=0, examples=(), note=""):
    return {"status": status, "count": count, "examples": list(examples)[:MAX_EX], "note": note}


QUESTIONS = []


def question(qid, text):
    def deco(fn):
        QUESTIONS.append({"id": qid, "question": text, "fn": fn,
                          "method": " ".join((fn.__doc__ or "").split())})
        return fn
    return deco


@question("K1", "Does every row taken from a Council workbook equal its workbook cells, read a "
          "second way, and is every workbook record in the table (none lost, none invented)?")
def q_workbook_cells(ctx):
    """openpyxl re-read of each workbook named in source_file; per record (source_row): every
    text field equal after whitespace folding, and the record's non-zero amounts equal the
    table's (amount_fy, amount) rows; a record with all-zero amounts has one row at 0."""
    by_file = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in ctx["table"]:
        if r["source_kind"] == "council_workbook":
            by_file[(r["source_file"], int(r["report_year"]))][int(r["source_row"])].append(r)
    bad, n = [], 0
    for (rel, fy), rows in sorted(by_file.items()):
        recs, _ = ctx.get("reader", read_workbook)(os.path.join(ROOT, rel), fy)
        for rn in sorted(set(recs) - set(rows)):
            bad.append(f"{rel}:{rn} not in the table")
        for rn, trs in sorted(rows.items()):
            rec = recs.get(rn)
            n += 1
            if rec is None:
                bad.append(f"{rel}:{rn} in the table, not a workbook record")
                continue
            for f in ("project_id", "borough", "budget_line", "council_district", "sponsor",
                      "title", "description"):
                if any(t[f] != rec.get(f, "") for t in trs):
                    bad.append(f"{rel}:{rn} {f}: table {trs[0][f]!r} vs workbook {rec.get(f, '')!r}")
            want = {y: a for y, a in rec["amounts"].items() if a != 0} or {fy: Decimal(0)}
            got = {int(t["amount_fy"]): Decimal(t["amount"]) for t in trs}
            if got != want:
                bad.append(f"{rel}:{rn} amounts: table {got} vs workbook {want}")
    return result("finding" if bad else "pass", len(bad), bad, f"{n:,} workbook records compared.")


@question("K2", "Do the FY2015 and FY2016 totals rows equal the sums of the rows the table "
          "kept, and does no other workbook carry a text-less row?")
def q_totals_rows(ctx):
    """Re-reads each workbook; a row with no text is a totals row; its amounts must equal the
    table's sums by amount_fy for that report year. Only FY2015 and FY2016 may have one."""
    sums = collections.defaultdict(Decimal)
    files = {}
    for r in ctx["table"]:
        if r["source_kind"] == "council_workbook":
            files[int(r["report_year"])] = r["source_file"]
            sums[(int(r["report_year"]), int(r["amount_fy"]))] += Decimal(r["amount"])
    bad, notes = [], []
    for fy, rel in sorted(files.items()):
        _, textless = ctx.get("reader", read_workbook)(os.path.join(ROOT, rel), fy)
        if textless and fy not in (2015, 2016):
            bad.append(f"FY{fy}: {len(textless)} text-less row(s)")
        for amts in textless:
            for y, a in amts.items():
                if a != sums.get((fy, y), Decimal(0)):
                    bad.append(f"FY{fy} totals row FY{y} {a} vs table {sums.get((fy, y), 0)}")
            notes.append(f"FY{fy} totals row = table sums")
    return result("finding" if bad else "pass", len(bad), bad, "; ".join(notes) or "none")


def _t474():
    with gzip.open(T474, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@question("K3", "For FY2019-FY2025, does the table hold exactly t474-a92g's rows (count and "
          "sum per report year and fiscal year), with a blank amount only on the rows that "
          "have a report year but no award?")
def q_t474(ctx):
    """Raw t474-a92g.csv.gz with gzip + csv: rows with a 4-digit `reported` in 2019-2025,
    grouped by (reported, fiscal_year); the table's open_data_t474 rows grouped the same way.
    Rows with a year and no award must be exactly the table's flagged rows (by :id)."""
    raw = ctx.get("t474") or _t474()
    want, got = collections.Counter(), collections.Counter()
    want_s, got_s = collections.defaultdict(Decimal), collections.defaultdict(Decimal)
    blank_raw = set()
    for r in raw:
        if not re.fullmatch(r"20(19|2[0-5])", r["reported"]):
            continue
        if not r["award"]:
            blank_raw.add(r[":id"])
            continue
        k = (int(r["reported"]), 2000 + int(r["fiscal_year"][2:]))
        want[k] += 1
        want_s[k] += Decimal(r["award"])
    blank_tab = set()
    for r in ctx["table"]:
        if r["source_kind"] != "open_data_t474":
            continue
        if r["amount"] == "":
            blank_tab.add(r["source_row"])
            continue
        k = (int(r["report_year"]), int(r["amount_fy"]))
        got[k] += 1
        got_s[k] += Decimal(r["amount"])
    bad = [f"{k}: raw {want[k]} rows {want_s[k]} vs table {got[k]} rows {got_s[k]}"
           for k in sorted(set(want) | set(got)) if (want[k], want_s[k]) != (got[k], got_s[k])]
    if blank_raw != blank_tab:
        bad.append(f"blank-amount rows: raw {sorted(blank_raw)} vs table {sorted(blank_tab)}")
    return result("finding" if bad else "pass", len(bad), bad,
                  f"{sum(want.values()):,} rows in {len(want)} (year, fiscal year) cells; "
                  f"{len(blank_raw)} split record(s) with no amount.")


def _omb():
    with gzip.open(OMB_BUDGET, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@question("K4", "Does every line of the Council-vs-OMB reconciliation re-derive from the raw "
          "OMB file and the table (adopted = the last release for the first year), and is "
          "FY2027 146 of 153 matching?")
def q_recon(ctx):
    """Own computation: OMB 46m8-77gv rows whose budget line minus the proj_type prefix starts
    with D; adopted release = max pub_date per yr1_fy; sums of year1_amt/year2_amt by line;
    Council sums by line for amount_fy = report year and the next; verdicts compared with
    council_vs_omb_by_budget_line.csv line by line."""
    raw = ctx.get("omb") or _omb()
    last = {}
    for r in raw:
        last[r["yr1_fy"]] = max(last.get(r["yr1_fy"], ""), r["pub_date"])
    omb = collections.defaultdict(lambda: [Decimal(0), Decimal(0)])
    for r in raw:
        if r["pub_date"] != last[r["yr1_fy"]]:
            continue
        pt = r["proj_type"].strip().upper()
        rest = re.sub(r"[\s-]", "", r["budline"].upper()[len(pt):])
        if not rest.startswith("D"):
            continue
        k = (int(r["yr1_fy"]), f"{pt} {rest}")
        omb[k][0] += Decimal(r["year1_amt"])
        omb[k][1] += Decimal(r["year2_amt"])
    years = {k[0] for k in omb}
    mine = collections.defaultdict(lambda: [Decimal(0), Decimal(0)])
    for r in ctx["table"]:
        y, ln = int(r["report_year"]), line_norm(r["budget_line"])
        if y not in years or not ln or not ln.split(" ")[1].startswith("D") or not r["amount"]:
            continue
        if r["amount_fy"] == str(y):
            mine[(y, ln)][0] += Decimal(r["amount"])
        elif r["amount_fy"] == str(y + 1):
            mine[(y, ln)][1] += Decimal(r["amount"])
        else:
            mine[(y, ln)]
    want = {}
    for k in set(omb) | set(mine):
        want[k] = ("omb_only" if k not in mine else "council_only" if k not in omb
                   else "match" if mine[k] == omb[k] else "differ")
    got = {(int(r["report_year"]), r["budget_line_norm"]): r["verdict"] for r in ctx["recon"]}
    bad = [f"FY{k[0]} {k[1]}: report {got.get(k)} vs audit {want.get(k)}"
           for k in sorted(set(want) | set(got)) if got.get(k) != want.get(k)]
    y27 = collections.Counter(v for k, v in want.items() if k[0] == 2027)
    council27 = y27["match"] + y27["differ"] + y27["council_only"]
    if (y27["match"], council27) != (146, 153):
        bad.append(f"FY2027: {y27['match']} of {council27} match, the research found 146 of 153")
    return result("finding" if bad else "pass", len(bad), bad,
                  f"{len(want)} (year, line) verdicts re-derived; FY2027 {dict(sorted(y27.items()))}.")


@question("K5", "Is every budget_line_norm the published budget_line re-spelled, and is no "
          "amount rounded (every amount a whole number of dollars, as the sources print)?")
def q_lines(ctx):
    """Own regex on every row's budget_line; amounts must be integers (all three sources print
    whole dollars)."""
    bad = [f"{r['source_file']}:{r['source_row']} {r['budget_line']!r} -> {r['budget_line_norm']!r}"
           for r in ctx["table"] if line_norm(r["budget_line"]) != r["budget_line_norm"]]
    bad += [f"{r['source_file']}:{r['source_row']} amount {r['amount']!r}" for r in ctx["table"]
            if r["amount"] and Decimal(r["amount"]) != Decimal(r["amount"]).quantize(
                Decimal(1), rounding=ROUND_HALF_UP)]
    return result("finding" if bad else "pass", len(bad), bad,
                  f"{len(ctx['table']):,} rows checked.")


def run(ctx):
    return [{**{k: v for k, v in q.items() if k != "fn"}, **q["fn"](ctx)} for q in QUESTIONS]


def report_text(results):
    L = ["# Council capital: adversarial audit", "",
         ("Generated by `code/audit_capital.py` from committed files only. It re-reads the "
         "Council workbooks with openpyxl and the Open Data files with gzip + csv, never with "
         "`build_capital_council.py`, and maps headers and budget lines by its own rules. "
         "`code/test_audit_capital.py` shows each question failing on a constructed defect."), "",
         "| id | question | result | count | method / notes / examples |", "|---|---|---|---:|---|"]
    for r in results:
        d = r["method"] + (" **Note:** " + r["note"] if r["note"] else "")
        if r["examples"]:
            d += " **Examples:** " + "; ".join(f"`{e}`" for e in r["examples"])
        L.append(f"| {r['id']} | {r['question']} | **{r['status']}** | {r['count']:,} | "
                 f"{d.replace('|', '/')} |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    results = run(load())
    text = report_text(results)
    if a.write:
        with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(REPORT, ROOT)}")
    elif a.check:
        cur = ""
        if os.path.exists(REPORT):
            with open(REPORT, encoding="utf-8") as f:
                cur = f.read()
        if cur != text:
            print("STALE: data/capital/CAPITAL-AUDIT.md -- run code/audit_capital.py --write")
            return 1
        print("data/capital/CAPITAL-AUDIT.md is current")
    for r in results:
        print(f"{r['id']:4} {r['status']:8} {r['count']:>6}  {r['note'][:100]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
