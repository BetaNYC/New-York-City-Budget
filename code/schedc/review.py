"""
Stage 11 -- the review file (PLAN §5.3): one row per thing a person must look at.

Kept short on purpose: it lists critical flags and the few warn flags that could change a
value (never the routine ones; those are counted in checks.txt and listed in flags.csv).
Sorted by severity, then dollar impact, largest first. `review_id` is a sha1 of
(fy, check, page, table, row, field), so a person's decision in fyNN_sc_review_decisions.csv
survives a re-run. The pipeline never writes the decisions file.
"""
import csv
import hashlib
import os

COLUMNS = ["review_id", "severity", "dollar_impact", "check_id", "pdf_page", "table_index",
           "row_index", "award_id", "field", "what_to_check", "value_vector", "value_image",
           "value_other", "expected", "observed", "overlay", "decision", "note"]


def review_id(fy, check, page, table="", row="", field=""):
    key = "|".join(str(v) for v in (fy, check, page, table, row, field))
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def write(path, items, fy, decisions_path, checks_ran):
    decided = {}
    if os.path.exists(decisions_path):
        with open(decisions_path, newline="", encoding="utf-8") as f:
            decided = {r["review_id"]: r for r in csv.DictReader(f)}
    rows = []
    for it in items:
        r = {c: it.get(c, "") for c in COLUMNS}
        r["review_id"] = review_id(fy, it["check_id"], it.get("pdf_page", ""),
                                   it.get("table_index", ""), it.get("row_index", ""),
                                   it.get("field", ""))
        d = decided.get(r["review_id"])
        if d:
            r["decision"], r["note"] = d.get("decision", ""), d.get("note", "")
        rows.append(r)
    sev = {"critical": 0, "warn": 1}
    rows.sort(key=lambda r: (sev.get(r["severity"], 2), -int(r["dollar_impact"] or 0),
                             int(r["pdf_page"] or 0), r["review_id"]))
    stale = sorted(set(decided) - {r["review_id"] for r in rows})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
        if not rows:
            w.writerow({"review_id": "ok", "what_to_check": "nothing to review; checks run: "
                        + ", ".join(checks_ran)})
    return rows, stale
