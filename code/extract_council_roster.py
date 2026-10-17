#!/usr/bin/env python3
"""Extract the NYC Council member roster, with each person's recorded voting dates, from
BetaNYC's local copy of Legistar, into a small committed CSV (GitHub #72).

Why a committed extract: the member crosswalk (code/build_member_crosswalk.py) and its tests must
run in CI, where neither the Legistar database nor the network exists. This script is the only
thing that reads the database, and it is run by hand when the roster needs refreshing.

Source: the SQLite index that @betanyc/nyc-council-mcp reads (BetaNYC/nyc-council-mcp; built by
its own indexer from Legistar). Path: --db, else $LEGISTAR_DB_PATH. Read-only (opened with
mode=ro). Never the Legistar web API and never the Council website. Tables and columns used,
as that index's own schema declares them (`.schema` of the file, checked 2026-10-12):
  people(person_id, full_name, first_name, last_name, active_flag)
  votes(event_item_id, person_id, person_name, vote_value, matter_id)   -- one row per vote
  event_items(event_item_id, event_id, ...)
  events(event_id, date, body_name, ...)
  sponsors(matter_id, person_id, is_primary)
  index_state(key, value)   -- 'last_indexed_at', 'schema_version'

Service evidence per person: every NYC fiscal year (July 1 - June 30) in which Legistar records
at least one vote by that person, at any body (Stated Meetings and committees), plus the first and
last vote dates. A vote on a date proves the person was a member on that date. The years are kept
as a SET, not a first-to-last span, because members leave and return: Charles Barron voted
FY2004-FY2014 and FY2022-FY2024, and a span would have put him in office through the years his
wife Inez Barron held the seat. Limits, stated in the crosswalk's documentation: a fiscal year
counts only if a vote was recorded in it; a person with no recorded vote has no years. Sponsorship counts are kept as supporting evidence only (a bill's date is not a
date the sponsor served).

Outputs:
  data/reference/council_members_legistar.csv       one row per Legistar person
  data/reference/council_members_legistar_meta.csv  provenance (key, value)

Run:
  python3 code/extract_council_roster.py [--db PATH]
"""

import argparse
import csv
import io
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "reference", "council_members_legistar.csv")
META = os.path.join(ROOT, "data", "reference", "council_members_legistar_meta.csv")

FIELDS = ["person_id", "full_name", "first_name", "last_name", "active_flag", "first_vote",
          "last_vote", "vote_meetings", "vote_fiscal_years", "sponsorships"]

QUERY = """
WITH v AS (
  SELECT vt.person_id, MIN(e.date) AS first_vote, MAX(e.date) AS last_vote,
         COUNT(DISTINCT e.event_id) AS vote_meetings
  FROM votes vt
  JOIN event_items ei ON ei.event_item_id = vt.event_item_id
  JOIN events e ON e.event_id = ei.event_id
  GROUP BY vt.person_id
), fy AS (
  -- NYC fiscal year N = July 1 of N-1 .. June 30 of N
  SELECT person_id, GROUP_CONCAT(fy, ';') AS vote_fiscal_years FROM (
    SELECT DISTINCT vt.person_id,
           CAST(substr(e.date, 1, 4) AS INTEGER) + (CAST(substr(e.date, 6, 2) AS INTEGER) >= 7) AS fy
    FROM votes vt
    JOIN event_items ei ON ei.event_item_id = vt.event_item_id
    JOIN events e ON e.event_id = ei.event_id
    ORDER BY vt.person_id, fy)
  GROUP BY person_id
), s AS (
  SELECT person_id, COUNT(*) AS sponsorships FROM sponsors GROUP BY person_id
)
SELECT p.person_id, p.full_name, COALESCE(p.first_name, ''), COALESCE(p.last_name, ''),
       COALESCE(p.active_flag, ''), COALESCE(v.first_vote, ''), COALESCE(v.last_vote, ''),
       COALESCE(v.vote_meetings, 0), COALESCE(fy.vote_fiscal_years, ''), COALESCE(s.sponsorships, 0)
FROM people p LEFT JOIN v ON v.person_id = p.person_id LEFT JOIN fy ON fy.person_id = p.person_id
LEFT JOIN s ON s.person_id = p.person_id
ORDER BY p.person_id
"""


def extract(db_path):
    """(rows, meta) from the database. Dates are cut to YYYY-MM-DD."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = []
        for r in con.execute(QUERY):
            d = dict(zip(FIELDS, r))
            d["first_vote"] = str(d["first_vote"])[:10]
            d["last_vote"] = str(d["last_vote"])[:10]
            # GROUP_CONCAT order is not guaranteed by SQLite; sort here.
            d["vote_fiscal_years"] = ";".join(
                str(y) for y in sorted({int(x) for x in str(d["vote_fiscal_years"]).split(";") if x}))
            d["full_name"] = " ".join(str(d["full_name"]).split())
            d["first_name"] = " ".join(str(d["first_name"]).split())
            d["last_name"] = " ".join(str(d["last_name"]).split())
            rows.append(d)
        state = dict(con.execute("SELECT key, value FROM index_state").fetchall())
        span = con.execute("""SELECT MIN(e.date), MAX(e.date) FROM votes vt
                              JOIN event_items ei ON ei.event_item_id = vt.event_item_id
                              JOIN events e ON e.event_id = ei.event_id""").fetchone()
    finally:
        con.close()
    meta = [("source", "local Legistar index read by @betanyc/nyc-council-mcp"),
            ("db_last_indexed_at", state.get("last_indexed_at", "")),
            ("db_schema_version", state.get("schema_version", "")),
            ("people", str(len(rows))),
            ("vote_dates_min", str(span[0])[:10]),
            ("vote_dates_max", str(span[1])[:10])]
    return rows, meta


def rows_text(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def meta_text(meta):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["key", "value"])
    w.writerows(meta)
    return buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", default=os.environ.get("LEGISTAR_DB_PATH"),
                    help="path to the Legistar SQLite index (default: $LEGISTAR_DB_PATH)")
    a = ap.parse_args(argv)
    if not a.db:
        sys.exit("extract_council_roster: pass --db PATH or set LEGISTAR_DB_PATH")
    if not os.path.exists(a.db):
        sys.exit(f"extract_council_roster: no database at {a.db}")
    rows, meta = extract(a.db)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for path, text in ((OUT, rows_text(rows)), (META, meta_text(meta))):
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
