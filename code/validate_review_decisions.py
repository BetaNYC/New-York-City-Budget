"""
Validate a review-decisions CSV against its review CSV, and report what is still open.

A decisions file is a person's answers to a PDF family's review queue (PLAN.md §5.3). It is never
written by a pipeline; the explorer's review screen exports one for a person to commit. Shape,
exactly as research/2026-10-20-fy27-schedule-c-review/data/fy27_sc_review_decisions.csv:

    review_id,decision,note,decided_by,decided_at

Checks (each failure is listed; any failure exits 1):
  - the header is exactly those five columns, in that order
  - every review_id is in the review CSV (a decision on an id that no longer exists is stale)
  - no review_id appears twice
  - decision is one of source_error, parser_bug, accepted_as_printed, needs_info,
    read_from_page_image
  - a read_from_page_image decision (code/page_image.py: the page and the text layer disagree and
    a person confirmed what the page shows) names one data row (its review row has an award_id or
    row_id; not a sub-award), and its note says what the page shows: page shows <field>:
    "<value>", e.g. page shows ein: "87-0753479"; <field> is one of page_image.FIELDS and, when the
    review row names a field, that one
  - decided_by is not blank; decided_at is an ISO date or date-time (2026-10-21, 2026-10-21T09:30:00Z)
Report: decided / open counts, and every open review_id with its check and page. `needs_info`
is a valid decision but not a final one (it still needs an answer), so it is listed separately.

    .venv/bin/python code/validate_review_decisions.py \\
        --review data/fy27/pdf/schedule_c/fy27_sc_review.csv \\
        --decisions research/2026-10-20-fy27-schedule-c-review/data/fy27_sc_review_decisions.csv

--complete also exits 2 when anything is open or decided `needs_info` (#194): a family is not done
while a question is outstanding. --allow-needs-info lets those through on purpose (for example, a
question sent to Council Finance that has waited its 30 days). Exit 0: valid.

Merging an export from the explorer's review screen into the committed file:

    ... --decisions <committed file> --add ~/Downloads/<exported file> [--write]

adds the exported rows whose review_id the committed file does not decide yet; a row that would
change a committed decision is a problem (nothing is overwritten). The merged result is validated;
--write saves it over the committed file only if it is valid.

One record of a decision (#195): the decisions CSV is the record. A review file's `decision` and
`note` columns are a copy of it, made by the readers (code/schedc/review.py,
code/parse_transparency_v2.py) on every run. --write (and --sync, on its own) also copies the
record into the review files that carry those columns: the one beside the decisions file (the
review folder's) and --review (the promoted one), changing only those two cells, so a re-run of a
decided year gives the same bytes. A read_from_page_image decision also changes its data row: for
that, re-run the reader and code/build_pdf_promoted.py --write. code/test_review_decisions.py
fails while any committed copy differs from its record.
"""
import argparse
import csv
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import page_image  # noqa: E402

HEADER = ["review_id", "decision", "note", "decided_by", "decided_at"]
DECISIONS = ("source_error", "parser_bug", "accepted_as_printed", "needs_info", page_image.DECISION)
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$")


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        header = next(r, [])
        rows = [dict(zip(header, row)) for row in r if any(c.strip() for c in row)]
    return header, rows


def validate(review_rows, header, decisions):
    """Returns dict(errors, decided, open, needs_info) for review rows and decision rows."""
    errors = []
    if header != HEADER:
        errors.append(f"header is {','.join(header)}; expected {','.join(HEADER)}")
    known = {r["review_id"]: r for r in review_rows if r.get("review_id") and r["review_id"] != "ok"}
    seen = {}
    for i, d in enumerate(decisions, start=2):
        rid = (d.get("review_id") or "").strip()
        at = f"line {i} ({rid or 'no review_id'})"
        if rid in seen:
            errors.append(f"{at}: review_id also on line {seen[rid]}")
            continue
        seen[rid] = i
        if rid not in known:
            errors.append(f"{at}: review_id not in the review CSV (stale or mistyped)")
        if d.get("decision") not in DECISIONS:
            errors.append(f"{at}: decision {d.get('decision')!r}; allowed: {', '.join(DECISIONS)}")
        elif d["decision"] == page_image.DECISION:
            row = known.get(rid, {})
            if rid in known and not (row.get("award_id") or row.get("row_id")):
                errors.append(f"{at}: {page_image.DECISION} needs a review row naming one data row "
                              "(award_id or row_id); this one names none")
            elif page_image.is_subaward(row.get("award_id")):
                errors.append(f"{at}: {page_image.DECISION} is not supported on a sub-award row "
                              f"({row['award_id']}) yet")
            try:
                page_image.parse(d.get("note"), row.get("field") or "")
            except ValueError as e:
                errors.append(f"{at}: {e}")
        if not (d.get("decided_by") or "").strip():
            errors.append(f"{at}: decided_by is blank")
        if not ISO.match((d.get("decided_at") or "").strip()):
            errors.append(f"{at}: decided_at {d.get('decided_at')!r} is not an ISO date")
    decided = [rid for rid in seen if rid in known]
    open_ = [known[rid] for rid in known if rid not in seen]
    needs = [rid for rid in decided if next(d for d in decisions if d.get("review_id", "").strip() == rid).get("decision") == "needs_info"]
    return dict(errors=errors, decided=decided, open=open_, needs_info=needs, total=len(known))


def merge(committed, added):
    """Committed rows, plus added rows for review_ids not yet decided. Returns (rows, problems)."""
    have = {d.get("review_id", "").strip(): d for d in committed}
    out, problems = list(committed), []
    for d in added:
        rid = d.get("review_id", "").strip()
        if rid in have:
            if have[rid].get("decision") != d.get("decision"):
                problems.append(f"{rid}: already decided as {have[rid].get('decision')!r} in the committed file; "
                                f"the export says {d.get('decision')!r}; not changed")
            continue
        have[rid] = d
        out.append(d)
    return out, problems


def to_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def review_csv(header, rows):
    """A review file's text, written as the readers write it."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=header, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def copies(decisions_path, review_path):
    """The review files that may carry a copy of the decisions: the one beside the decisions file
    (fyNN_sc_review_decisions.csv -> fyNN_sc_review.csv) and the --review file."""
    beside = None
    if decisions_path.endswith("_review_decisions.csv"):
        beside = decisions_path[:-len("_decisions.csv")] + ".csv"
    return list(dict.fromkeys(os.path.abspath(p) for p in (beside, review_path) if p and os.path.exists(p)))


def sync(path, decisions):
    """Copy decision and note from the record into one review file, if it has those columns.
    Returns the review_ids whose cells changed (the file is rewritten only if there are any)."""
    header, rows = read(path)
    if "decision" not in header or "note" not in header:
        return []
    record = {(d.get("review_id") or "").strip(): d for d in decisions}
    changed = []
    for r in rows:
        if r.get("review_id") in ("", "ok"):
            continue
        d = record.get(r["review_id"], {})
        new = (d.get("decision", ""), d.get("note", ""))
        if (r.get("decision", ""), r.get("note", "")) != new:
            r["decision"], r["note"] = new
            changed.append(r["review_id"])
    if changed:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write(review_csv(header, rows))
    return changed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--review", required=True, help="the family's review CSV")
    ap.add_argument("--decisions", required=True, help="the decisions CSV to check")
    ap.add_argument("--complete", action="store_true",
                    help="exit 2 if any review row is still open or decided needs_info")
    ap.add_argument("--allow-needs-info", action="store_true",
                    help="with --complete: do not count needs_info decisions as open")
    ap.add_argument("--add", help="an exported decisions CSV to merge into --decisions")
    ap.add_argument("--write", action="store_true", help="with --add: save the merged file over --decisions if valid, "
                    "and copy the decisions into the review files")
    ap.add_argument("--sync", action="store_true", help="copy the decisions into the review files that carry "
                    "decision and note columns (the one beside --decisions, and --review), if valid")
    a = ap.parse_args(argv)
    _, review_rows = read(a.review)
    header, decisions = read(a.decisions)
    merge_problems = []
    if a.add:
        add_header, added = read(a.add)
        if add_header != HEADER:
            merge_problems.append(f"{a.add}: header is {','.join(add_header)}; expected {','.join(HEADER)}")
        decisions, more = merge(decisions, added)
        merge_problems += more
        print(f"{a.add}: {len(added)} rows; merged into {a.decisions}")
    res = validate(review_rows, header, decisions)
    res["errors"] = merge_problems + res["errors"]
    print(f"{a.decisions}: {len(res['decided'])}/{res['total']} decided, {len(res['open'])} open, "
          f"{len(res['needs_info'])} needs_info, {len(res['errors'])} problems")
    for e in res["errors"]:
        print(f"  PROBLEM {e}")
    for r in res["open"]:
        print(f"  open    {r['review_id']}  {r.get('check_id', '')}  p.{r.get('pdf_page', '')}")
    by_id = {r["review_id"]: r for r in review_rows if r.get("review_id")}
    for rid in res["needs_info"]:
        r = by_id.get(rid, {})
        print(f"  needs_info {rid}  {r.get('check_id', '')}  p.{r.get('pdf_page', '')}")
    if res["errors"]:
        if (a.add and a.write) or a.sync:
            print("  not written: fix the problems above")
        return 1
    if a.add and a.write:
        with open(a.decisions, "w", newline="", encoding="utf-8") as f:
            f.write(to_csv(decisions))
        print(f"  wrote {a.decisions}")
    if (a.add and a.write) or a.sync:
        kinds = {(d.get("review_id") or "").strip(): d.get("decision") for d in decisions}
        for path in copies(a.decisions, a.review):
            changed = sync(path, decisions)
            if changed:
                print(f"  copied {len(changed)} decisions into {path}")
            if any(kinds.get(rid) == page_image.DECISION for rid in changed):
                print("  a read_from_page_image decision changes its data row too: re-run the reader "
                      "and code/build_pdf_promoted.py --write")
    if a.complete and (res["open"] or (res["needs_info"] and not a.allow_needs_info)):
        if res["needs_info"] and not a.allow_needs_info:
            print(f"  not complete: {len(res['needs_info'])} needs_info still to answer "
                  "(--allow-needs-info to accept them on purpose)")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
