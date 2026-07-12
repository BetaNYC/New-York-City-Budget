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
CROSSWALK = os.path.join(DATA, "combined", "initiative_name_crosswalk.csv")

INIT_COLS = ["category", "agencies", "initiative", "amount"]
# `purpose` MUST be included: it is a distinguishing field in the per-year award files.
# Dropping it collapses source-distinct rows (same org/amount, different stated purpose) into
# apparent duplicates in the roll-up — manufacturing dups that do not exist in the source. See
# DATA-ANOMALIES.md #8. Every data/fyNN/schedule_c/*_awards.csv carries this 10th column.
AWARD_COLS = ["category", "initiative", "award_type", "member", "organization",
              "program", "ein", "amount", "agency", "purpose"]

def house_style(s):
    """Deterministic canonical spelling for an initiative label: strip a leading '*'
    footnote marker, straight-quote curly apostrophes, spell '&' as 'and', collapse
    internal whitespace. Source casing is preserved so acronyms (CASA, CUNY, HIV/AIDS)
    stay intact. Used as the fallback for any raw label not in the crosswalk."""
    s = s.strip()
    s = re.sub(r"^\*+\s*", "", s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"\s*&\s*", " and ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def load_crosswalk(path=CROSSWALK):
    """raw_initiative -> initiative_canonical, from the committed crosswalk. Missing file
    is not fatal: every label then falls back to house_style()."""
    m = {}
    if os.path.exists(path):
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                m[r["raw_initiative"]] = r["initiative_canonical"]
    return m

def canonical_for(raw, xwalk):
    """The stable cross-year key. Explicit crosswalk mapping wins (handles judgment calls
    house_style can't make — dropped words, hyphenation); otherwise mechanical normalization."""
    return xwalk.get(raw) or house_style(raw)

def year_of(path):
    m = re.search(r'/fy(\d\d)/', path)
    return f"FY{m.group(1)}" if m else "FY??"

def collect(kind, cols, data_dir=DATA):
    """Stack every per-year data/fyNN/schedule_c/*_schedule_c_<kind>.csv into rows prefixed
    with the FYnn year. Pure (no writes) so it is unit-testable against a fixture tree."""
    pattern = os.path.join(data_dir, "fy*", "schedule_c", f"*_schedule_c_{kind}.csv")
    rows = []
    for p in sorted(glob.glob(pattern)):
        yr = year_of(p)
        with open(p, newline="") as f:
            for r in csv.DictReader(f):
                rows.append([yr] + [r.get(c, "") for c in cols])
    return rows

def build(kind, cols, data_dir=DATA, xwalk=None):
    if xwalk is None:
        xwalk = load_crosswalk()
    rows = collect(kind, cols, data_dir)
    out = os.path.join(data_dir, "combined", f"all_years_{kind}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # Insert a derived `initiative_canonical` immediately after the raw `initiative` column.
    # Non-destructive: `initiative` stays verbatim from source. See DATA-ANOMALIES #17.
    out_cols = list(cols)
    ipos = None
    if "initiative" in cols:
        ci = cols.index("initiative")
        out_cols = cols[:ci + 1] + ["initiative_canonical"] + cols[ci + 1:]
        ipos = 1 + ci  # +1 for the leading `year` column prepended in collect()
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["year"] + out_cols)
        for r in rows:
            if ipos is not None:
                r = r[:ipos + 1] + [canonical_for(r[ipos], xwalk)] + r[ipos + 1:]
            w.writerow(r)
    years = sorted({r[0] for r in rows})
    print(f"{os.path.relpath(out, REPO)}: {len(rows)} rows across {len(years)} years "
          f"({years[0]}..{years[-1]})")

def main():
    os.makedirs(os.path.join(DATA, "combined"), exist_ok=True)
    xwalk = load_crosswalk()
    build("initiatives", INIT_COLS, xwalk=xwalk)
    build("awards", AWARD_COLS, xwalk=xwalk)

if __name__ == "__main__":
    main()
