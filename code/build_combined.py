#!/usr/bin/env python3
"""
Build the cross-year roll-ups in data/combined/ by stacking every committed per-year Schedule C
file with a leading `year` column (FYnn). Idempotent: rerun any time new years are parsed.

  data/combined/all_years_initiatives.csv  <- every data/fyNN/schedule_c/*_schedule_c_initiatives.csv
  data/combined/all_years_awards.csv       <- every data/fyNN/schedule_c/*_schedule_c_awards.csv

Years with only an initiatives summary (FY2009-FY2014, early era) contribute to the initiatives
roll-up but not the awards roll-up (those documents carry no award-level rows). legistar_crosswalk.csv
is maintained separately and is not touched here.
"""
import csv, glob, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data")

INIT_COLS = ["category", "agencies", "initiative", "amount"]
AWARD_COLS = ["category", "initiative", "award_type", "member", "organization",
              "program", "ein", "amount", "agency"]

def year_of(path):
    m = re.search(r'/fy(\d\d)/', path)
    return f"FY{m.group(1)}" if m else "FY??"

def build(kind, cols):
    pattern = os.path.join(DATA, "fy*", "schedule_c", f"*_schedule_c_{kind}.csv")
    rows = []
    for p in sorted(glob.glob(pattern)):
        yr = year_of(p)
        with open(p, newline="") as f:
            for r in csv.DictReader(f):
                rows.append([yr] + [r.get(c, "") for c in cols])
    out = os.path.join(DATA, "combined", f"all_years_{kind}.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["year"] + cols)
        w.writerows(rows)
    years = sorted({r[0] for r in rows})
    print(f"{os.path.relpath(out, REPO)}: {len(rows)} rows across {len(years)} years "
          f"({years[0]}..{years[-1]})")

def main():
    os.makedirs(os.path.join(DATA, "combined"), exist_ok=True)
    build("initiatives", INIT_COLS)
    build("awards", AWARD_COLS)

if __name__ == "__main__":
    main()
