"""
Promote reviewed PDF tables to data/fyNN/pdf/<family>/ and write data/pdf_years.csv.

The integration contract (viz/explorer/INTEGRATION.md §1-2, branch feature/budget-explorer):
every PDF-derived row carries `fiscal_year, source_pdf, pdf_sha256, pdf_page, bbox_pt,
review_id, flags`, with values as printed. `bbox_pt` is `x0,top,x1,bottom` in PDF points on the
**unrotated** page (top-left origin), so a viewer that renders the page with its /Rotate can map it.

This script re-runs the parsers (code/review_capital_sd.py, code/review_terms.py,
code/parse_schedule_c_v2.py, code/parse_transparency_v2.py) into a scratch folder, so the
promoted files are regenerated from the PDFs, never copied from research/.
Families promoted here: FY2027 `capital_sd`, `schedule_c` and `terms` (GitHub #102); FY2026
`capital_sd`, `terms` (from config/capital_sd/ and config/terms/), `schedule_c` and `transparency`
(via code/parse_transparency_v2.py), all GitHub #103. For FY2025 back to FY2018 (FY2025 #104,
FY2024 #105, FY2023 #106, FY2022 #107, FY2021 #108, FY2020 #109, FY2019 #110, FY2018 #111):
`schedule_c` and `transparency` every year; `capital_sd` and `terms` FY2025-FY2022 and FY2018;
FY2021 `terms` only (no FY2021 capital supporting detail in source/); FY2020 `capital_sd` only
(Part I only, so its orgs table is header only; no FY2020 T&C); FY2019 `capital_sd` only (an
Excel print: no Part II/III and no summary page; no FY2019 T&C). The FY2018 capital book prints
no summary page.

`status` in data/pdf_years.csv: `reviewed` = every check ran and its flags are listed, but Noel has
not signed off; `closed` = the year's issue is closed. Promotion writes `reviewed`; only a person
changes it to `closed` (the MCP serves `closed` rows only).

Run:   .venv/bin/python code/build_pdf_promoted.py --write
Check: .venv/bin/python code/build_pdf_promoted.py --check   (regenerates and compares; exit 1 on drift)
"""
import argparse
import ast
import csv
import io
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import review_capital_sd as cap  # noqa: E402
import review_terms as terms     # noqa: E402

YEARS_CSV = os.path.join(REPO, "data", "pdf_years.csv")
YEARS_COLS = ["fiscal_year", "family", "source_pdf", "pdf_sha256", "issue", "status", "rows",
              "flagged", "printed_totals_tied", "note"]
CONTRACT = ["fiscal_year", "source_pdf", "pdf_sha256", "pdf_page", "bbox_pt", "review_id", "flags"]
REVIEW_COLS = ["fiscal_year", "family", "source_pdf", "pdf_sha256"] + cap.Review.COLS


def rel(path):
    return os.path.relpath(path, REPO)


def unrotate(bbox, rotate, disp_w, disp_h):
    """pdfplumber display box -> unrotated page box, both `x0,top,x1,bottom`, top-left origin.

    For /Rotate 90 the page is turned a quarter clockwise for display, so an unrotated point
    (u, v) shows at (disp_w - v, u). Checked on p.40 against pdfium's unrotated char boxes."""
    if not bbox:
        return ""
    x0, top, x1, bottom = (float(v) for v in bbox.split(","))
    if rotate == 0:
        u0, v0, u1, v1 = x0, top, x1, bottom
    elif rotate == 90:
        u0, v0, u1, v1 = top, disp_w - x1, bottom, disp_w - x0
    else:
        raise ValueError(f"rotation {rotate} not handled")
    return f"{u0:.2f},{v0:.2f},{u1:.2f},{v1:.2f}"


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def attach(rows, review, key_row, key_rev):
    """Set review_id and flags on each row from the review entries that point at it."""
    by = {}
    for rv in review:
        k = key_rev(rv)
        if k is not None:
            by.setdefault(k, []).append(rv)
    used = set()
    for r in rows:
        hits = by.get(key_row(r), [])
        used.add(key_row(r))
        r["review_id"] = ";".join(dict.fromkeys(h["review_id"] for h in hits))
        r["flags"] = ";".join(sorted({h["check_id"] for h in hits}))
    return used


# ------------------------------------------------------------------------------------------
# Capital supporting detail (FY2027, FY2026)
# ------------------------------------------------------------------------------------------

def build_capital_sd(scratch, fy=2027):
    """Columns follow the year's printed FY headers: FY2027 has fy2027..fy2030, FY2026
    fy2026..fy2029. A loader that unions the years keeps every printed column."""
    cap.run(scratch, do_ink=True, fy=fy)
    d = os.path.join(scratch, "data")
    px = cap.PREFIX
    fys = cap.FYS
    # FY2019 prints no summary page: no summary lines are added to its totals table.
    summary_pno = (cap.pages_of("summary") or [None])[0]
    pages = {int(p["pdf_page"]): p for p in read(os.path.join(d, f"{px}_capital_sd_pages.csv"))}
    base = {"fiscal_year": cap.FY, "source_pdf": rel(cap.PDF), "pdf_sha256": cap.PDF_SHA256}

    def unrot(page, bbox):
        p = pages[int(page)]
        return unrotate(bbox, int(p["rotate"]), float(p["width"]), float(p["height"]))

    review = [dict(base, family="capital_sd", **r) for r in read(os.path.join(d, f"{px}_capital_sd_review.csv"))]

    projects = read(os.path.join(d, f"{px}_capital_sd_projects.csv"))
    for r in projects:
        r.update(base)
        r["bbox_pt"] = unrot(r["pdf_page"], r["bbox_pt"])
    attach(projects, review, lambda r: (r["part"], r["sub_id"]),
           lambda rv: (rv["part"], rv["sub_id"]) if rv["sub_id"] and rv["part"] in ("I", "II") else None)
    proj_cols = CONTRACT + ["part", "agency", "row_in_page", "sub_id", "budget_line", "boro", "title",
                            "building_code", "school_code", *fys,
                            "sponsor", "title_raw", "sponsor_raw",
                            # FY2019 (Excel print) only: its CD codes and DESC column.
                            *(c for c in ("council_district", "description", "description_raw")
                              if projects and c in projects[0]),
                            *(f"{fy}_printed" for fy in fys)]

    # Part III: one row per printed budget-line row, carrying its organization's printed line.
    orgs = read(os.path.join(d, f"{px}_capital_sd_part3_orgs.csv"))
    lines = read(os.path.join(d, f"{px}_capital_sd_part3.csv"))
    org_rows = []
    i = 0
    for o in orgs:
        for k in range(int(o["n_lines"])):
            l = lines[i]
            i += 1
            assert l["organization"] == o["organization"], (l, o)
            org_rows.append(dict(base, pdf_page=l["pdf_page"], bbox_pt=unrot(l["pdf_page"], l["bbox_pt"]),
                                 organization=o["organization"], org_pdf_page=o["pdf_page"],
                                 org_bbox_pt=unrot(o["pdf_page"], o["bbox_pt"]),
                                 org_line_in_org=k + 1, org_lines=o["n_lines"],
                                 budget_line=l["budget_line"],
                                 **{fy: l[fy] for fy in fys},
                                 **{f"org_printed_{fy}": o[f"org_{fy}"] for fy in fys},
                                 org_status=o["status"]))
    assert i == len(lines)
    attach(org_rows, review, lambda r: ("III", r["organization"]),
           lambda rv: ("III", rv["note"].split(":")[0]) if rv["part"] == "III" else None)
    org_cols = CONTRACT + ["organization", "budget_line", *fys,
                           *(f"org_printed_{fy}" for fy in fys), "org_lines", "org_line_in_org",
                           "org_status", "org_pdf_page", "org_bbox_pt"]

    # Printed totals (every TOTALS FOR line) and the summary page (FY2027 p.61, FY2026 p.65).
    totals = []
    for t in read(os.path.join(d, f"{px}_capital_sd_totals.csv")):
        totals.append(dict(base, bbox_pt="", kind="totals_for", **t))
    summary_lines = ()
    if summary_pno:
        with cap.pdfplumber.open(cap.PDF) as pdf:
            summ = cap.summary_page(pdf, None)
        p1 = next(t for t in totals if t["part"] == "I" and t["name"] == "ALL")
        summary_lines = (("City Council Additions", summ["additions"], p1["sum_" + fys[0]]),
                         ("Less Rescindments from Prior Capital Budgets", summ["rescindments"], ""),
                         ("Net Change", summ["net"], summ["additions"] - summ["rescindments"]))
    for name, val, sumv in summary_lines:
        status = "" if sumv == "" else ("OK" if int(sumv) == val else "FAIL")
        totals.append(dict(base, pdf_page=summary_pno, bbox_pt="", kind="summary", part="", name=name,
                           **{"printed_" + fys[0]: val, "sum_" + fys[0]: sumv}, status=status))
    attach(totals, review, lambda r: (str(r["pdf_page"]), r["name"]),
           lambda rv: (str(rv["pdf_page"]), "Less Rescindments from Prior Capital Budgets")
           if rv["check_id"] == "C2.rescindments" else None)
    tot_cols = CONTRACT + ["kind", "part", "name", "printed_count", "rows",
                           *(f"printed_{fy}" for fy in fys), *(f"sum_{fy}" for fy in fys),
                           "status", "printed_text"]

    tied = sum(1 for t in totals if t["kind"] == "totals_for" and t["status"] == "OK")
    n_tot = sum(1 for t in totals if t["kind"] == "totals_for")
    files = {
        f"{px}_capital_sd_projects.csv": to_csv(projects, proj_cols),
        f"{px}_capital_sd_orgs.csv": to_csv(org_rows, org_cols),
        f"{px}_capital_sd_totals.csv": to_csv(totals, tot_cols),
        f"{px}_capital_sd_review.csv": to_csv(review, REVIEW_COLS),
    }
    summ_ok = all(t["status"] == "OK" for t in totals if t["kind"] == "summary" and t["status"])
    year = dict(base, family="capital_sd", issue=cap.CFG["issue"], status="reviewed", rows=len(projects),
                flagged=sum(1 for r in projects if r["flags"]),
                printed_totals_tied=f"{tied}/{n_tot}",
                note=((f"Parts I+II {len(projects)} rows (projects table); Part III {len(org_rows)} "
                       f"budget-line rows of {len(orgs)} organizations (orgs table); "
                       if cap.pages_of("part3") else
                       # FY2020 prints Part I only: no Part II or III to promote.
                       f"Part I only (the book prints no Part II or III): {len(projects)} rows "
                       "(projects table); ") +
                      (f"p.{summary_pno} summary {'ties' if summ_ok else 'DOES NOT tie'}. " if summary_pno else
                       "no summary page printed. ") +
                      f"Review: {cap.CFG['review_dir']}/REVIEW.md"))
    return files, year


# ------------------------------------------------------------------------------------------
# Terms and Conditions (FY2027, FY2026)
# ------------------------------------------------------------------------------------------

def build_terms(scratch, fy=2027):
    terms.run(scratch, do_ink=True, fy=fy)
    d = os.path.join(scratch, "data")
    px = terms.PREFIX
    fsr_item = str(terms.CFG["fsr_table"]["item_number"])
    base = {"fiscal_year": terms.FY, "source_pdf": rel(terms.PDF), "pdf_sha256": terms.PDF_SHA256}
    review = [dict(base, family="terms", **r) for r in read(os.path.join(d, f"{px}_terms_review.csv"))]
    conds = read(os.path.join(d, f"{px}_terms_conditions.csv"))
    for c in conds:
        c.update(base)
        # The row's page and box: its first page. Later pages' boxes stay in page_boxes.
        first = c["page_boxes"].split("|")[0]
        c["pdf_page"], c["bbox_pt"] = first.split(":")
    owner_of_table = {p: c["item_number"] for c in conds for p in
                      (int(x.split(":")[0]) for x in c["page_boxes"].split("|"))
                      if c["item_number"] == fsr_item}
    attach(conds, review, lambda c: c["item_number"],
           lambda rv: rv["field"] if rv["field"].isdigit() else
           (owner_of_table.get(int(rv["pdf_page"])) if rv["check_id"] == "W.midword_wrap" else None))
    cond_cols = CONTRACT + ["item_number", "page_start", "page_end", "page_boxes", "kind", "agency_name",
                            "agency_code", "units_of_appropriation", "num_units", "budget_lines",
                            "dates_mentioned", "report_deadlines", "heading_raw", "condition_text",
                            "condition_text_raw"]
    units = read(os.path.join(d, f"{px}_terms_units.csv"))
    for u in units:
        u.update(base)
    attach(units, review, lambda u: None, lambda rv: None)
    unit_cols = CONTRACT + ["item_number", "agency_name", "agency_code", "unit_of_appropriation",
                            "budget_line"]
    fsr = read(os.path.join(d, f"{px}_terms_fsr_table.csv"))
    for r in fsr:
        r.update(base, bbox_pt="", item_number=int(fsr_item))
    attach(fsr, review, lambda r: (r["pdf_page"], r["report_content_raw"]),
           lambda rv: (str(rv["pdf_page"]), ast.literal_eval(rv["note"].split("cell: ", 1)[1]
                                                             .rsplit(" (kept", 1)[0]))
           if rv["check_id"] == "W.midword_wrap" else None)
    fsr_cols = CONTRACT + ["item_number", "financial_status_report", "report_content", "issue_date",
                           "anticipated_meeting_date", "report_content_raw"]
    files = {
        f"{px}_terms_conditions.csv": to_csv(conds, cond_cols),
        f"{px}_terms_units.csv": to_csv(units, unit_cols),
        f"{px}_terms_fsr_table.csv": to_csv(fsr, fsr_cols),
        f"{px}_terms_review.csv": to_csv(review, REVIEW_COLS),
    }
    nums = sorted(int(c["item_number"]) for c in conds)
    assert nums == list(range(1, nums[-1] + 1)), "condition numbering has a gap or repeat"
    year = dict(base, family="terms", issue=terms.CFG["issue"], status="reviewed", rows=len(conds),
                flagged=sum(1 for c in conds if c["flags"]),
                printed_totals_tied="n/a",
                note=(f"No printed totals; numbering 1..{nums[-1]} complete; {len(units)} unit and "
                      "budget-line heading lines placed (units table). "
                      f"Review: {terms.CFG['review_dir']}/REVIEW.md"))
    return files, year


# ------------------------------------------------------------------------------------------
# FY2027 Schedule C
# ------------------------------------------------------------------------------------------

# What each year's pdf_years.csv note says after the row count and total.
SC_NOTE = {
    2027: ("25 category TOTALs tie; one $1 PDF self-error (p.214, initiative statement vs its "
           "rows) flagged. Review: research/2026-10-20-fy27-schedule-c-review/REVIEW.md"),
    2026: ("24/25 category TOTALs tie; two PDF self-errors flagged (p.173 TOTAL $800 under its "
           "lines; p.98 rows $15,000 under the statement); 2 eight-digit EINs. "
           "Review: research/2026-10-21-fy26-schedule-c-review/REVIEW.md"),
    2025: ("24/25 category TOTALs tie (Parks prints no summary table, p.202); PDF self-errors "
           "flagged (p.115 TOTAL $50,000 under its lines; p.64 statement $594,000 short of its "
           "box; p.167 rows $27,000 under the statement; p.222 '$3.2 million' for a $501,000 "
           "box); 1 malformed EIN (p.181). "
           "Review: research/2026-10-21-fy25-schedule-c-review/REVIEW.md"),
    2024: ("24/25 category TOTALs tie (Parks prints no summary table, p.201); PDF self-errors "
           "flagged (p.63 TOTAL $52,935 under its lines; six statements whose reserve and rows "
           "do not make the box); pp.130-137 (191 rows, $12,028,500) attached to NYC Cleanup, "
           "flagged; 1,438 rows in tables with no vertical rules checked by pixel rules only; "
           "bbox_pt from the MediaBox corner (216 pages start at -18,18). "
           "Review: research/2026-10-21-fy24-schedule-c-review/REVIEW.md"),
    2023: ("26/26 category TOTALs tie; appendices equal their fixed pots, including the two "
           "$5,000 Local rows the old parse lost (pp.213, 235); PDF self-errors flagged (boxes "
           "vs summary: p.83 Low Wage Worker Support $120,000 vs $2,000,000, p.86 Autism "
           "Awareness; six boxes whose rows or reserve do not make the box; four rounded "
           "statements; roll-up +$646,350); Asiyah Women's Center printed with another org's "
           "EIN (pp.13, 175); 1,028 rows in tables with no vertical rules checked by pixel rules "
           "only. Review: research/2026-10-21-fy23-schedule-c-review/REVIEW.md"),
    2022: ("25/25 category TOTALs tie; appendices equal their fixed pots; PDF self-errors flagged "
           "(p.57 Public Health Funding Backfill box $4,467,933 vs summary $4,667,933; six "
           "statements holding a reserve while their rows make the whole box; three more and one "
           "rounding; roll-up +$6,545,340); 5 EINs of the wrong length; Art as a Catalyst for "
           "Change (40 rows, pp.84-85) read with its Program column in "
           "program_or_subheading (36 rows print one). "
           "Review: research/2026-10-21-fy22-schedule-c-review/REVIEW.md"),
    2021: ("26/26 category TOTALs tie; appendices equal their fixed pots; PDF self-errors flagged "
           "(p.122 box printed '$477,00', read as $477,000; three statements holding a reserve "
           "while their rows make the whole box; one $1 over and one rounding; roll-up "
           "+$129,070); 6 EINs of the wrong length; award headers printed outside the table "
           "rules; 431 rows checked by pixel rules only. "
           "Review: research/2026-10-22-fy21-schedule-c-review/REVIEW.md"),
    2020: ("27/27 category TOTALs tie; appendices (amounts printed with no '$') equal their fixed "
           "pots; PDF self-errors flagged (p.46 three EINs printed one row off; p.46 rows "
           "$200,000 short of the box; p.45 $2,000 over; five rounded statements; roll-up "
           "-$219,300); 3 EINs of the wrong length; DATA-ANOMALIES §20's FY2020 row read as two "
           "awards; 1,532 rows checked by pixel rules only. "
           "Review: research/2026-10-22-fy20-schedule-c-review/REVIEW.md"),
    2019: ("27/27 category TOTALs tie; appendices (amounts printed with no '$') equal their fixed "
           "pots; a '*' column (review not complete) read into review_not_completed, 304 rows; "
           "PDF self-errors flagged (six post-adoption reserves printed again as City-agency "
           "rows; p.62 Ending the Epidemic rows $150,000 over; roll-up +$914,919); a partner "
           "list under one award (pp.105-106) read as its 28 sub-awards ($4,463,500), not "
           "counted; all 39 of DATA-ANOMALIES §20's FY2019 merged rows read as 82 awards; 902 "
           "rows checked by pixel rules only. "
           "Review: research/2026-10-22-fy19-schedule-c-review/REVIEW.md"),
    2018: ("25/26 category TOTALs tie (Community Development's prints $100,000 over its lines, "
           "a named PDF self-error); appendices equal their fixed pots (Appendix A's amounts "
           "printed with cents, the rest with no '$'); a '*' column read into "
           "review_not_completed, 1,504 rows; fiscal conduits (50 rows) in fiscal_conduit; PDF "
           "self-errors flagged (two reserves printed again as City-agency rows; six boxes whose "
           "rows do not make them; roll-up +$2,754,028); p.55 Good Shepherd printed with another "
           "org's EIN; a partner list (p.106) read as its 28 sub-awards ($4,463,500), not "
           "counted; all 94 of DATA-ANOMALIES §20's FY2018 merged rows read as 224 awards; 646 "
           "rows checked by pixel rules only. "
           "Review: research/2026-10-22-fy18-schedule-c-review/REVIEW.md"),
}
SC_ISSUE = {2027: 102, 2026: 103, 2025: 104, 2024: 105, 2023: 106, 2022: 107, 2021: 108, 2020: 109, 2019: 110, 2018: 111}


def build_schedule_c(scratch, fy=2027):
    """Re-run code/parse_schedule_c_v2.py (all checks, image lattice and ink included) into the
    scratch folder and promote its award, initiative, category and review tables. Its rows
    already carry the row contract; no Schedule C PDF has /Rotate pages (FY2026's and FY2025's
    landscape pages are 792x612 media boxes), so bbox_pt needs no unrotate. Its coordinates
    are from the MediaBox's top-left corner (FY2024 has MediaBoxes starting at (-18, 18))."""
    import contextlib
    import parse_schedule_c_v2 as sc
    from schedc import config as sc_config
    cfg = sc_config.load(fy)
    yy = f"fy{fy % 100:02d}"
    # The parser reads decisions from its output folder, so seed the scratch run with the
    # reviewer's decisions; otherwise the promoted review file never carries them.
    decisions = os.path.join(REPO, cfg["review_dir"], "data", f"{yy}_sc_review_decisions.csv")
    if os.path.exists(decisions):
        os.makedirs(scratch, exist_ok=True)
        shutil.copy(decisions, os.path.join(scratch, f"{yy}_sc_review_decisions.csv"))
    with contextlib.redirect_stdout(io.StringIO()):
        if sc.main(["--fy", str(fy), "--out", scratch]) != 0:
            raise RuntimeError("parse_schedule_c_v2 failed")
    checks_txt = open(os.path.join(scratch, f"{yy}_sc_checks.txt"), encoding="utf-8").read()
    if "FAIL" in checks_txt.replace("(FAIL)", ""):
        raise RuntimeError("a Schedule C check failed; not promoting")
    base = {"fiscal_year": fy, "source_pdf": cfg["pdf"], "pdf_sha256": cfg["sha256"]}
    awards = read(os.path.join(scratch, f"{yy}_sc_awards.csv"))
    inits = read(os.path.join(scratch, f"{yy}_sc_initiatives.csv"))
    cats = read(os.path.join(scratch, f"{yy}_sc_categories.csv"))
    # Sub-awards (the Jobs to Build On partner lists, FY2019 and FY2018): header only in the
    # other years, so every year has the file.
    subs = read(os.path.join(scratch, f"{yy}_sc_subawards.csv"))
    review = [dict(base, family="schedule_c", **r)
              for r in read(os.path.join(scratch, f"{yy}_sc_review.csv"))]
    for rs in (awards, inits, cats, subs):
        for r in rs:
            assert r["source_pdf"] == base["source_pdf"] and r["pdf_sha256"] == base["pdf_sha256"]
    order = lambda cols: CONTRACT + [c for c in cols if c not in CONTRACT]
    files = {
        f"{yy}_sc_awards.csv": to_csv(awards, order(list(awards[0]))),
        f"{yy}_sc_initiatives.csv": to_csv(inits, order(list(inits[0]))),
        f"{yy}_sc_categories.csv": to_csv(cats, order(list(cats[0]))),
        f"{yy}_sc_subawards.csv": to_csv(subs, order(sc.SUBAWARD_COLUMNS)),
        f"{yy}_sc_review.csv": to_csv(review, ["fiscal_year", "family", "source_pdf", "pdf_sha256"]
                                      + [c for c in review[0] if c not in base and c != "family"]),
    }
    tot = {r["category"]: int(r["amount"]) for r in cats if r["line"] == "TOTAL"}
    lines = {}
    for r in cats:
        if r["line"] != "TOTAL":
            lines[r["category"]] = lines.get(r["category"], 0) + int(r["amount"])
    tied = sum(1 for c in tot if lines.get(c) == tot[c])
    year = dict(base, family="schedule_c", issue=SC_ISSUE[fy], status="reviewed",
                rows=len(awards), flagged=sum(1 for r in awards if r["flags"]),
                printed_totals_tied=f"{tied}/{len(tot)}",
                note=(f"{len(awards)} award rows, ${sum(int(r['amount']) for r in awards):,} "
                      f"(body + appendices A/B/C); {SC_NOTE[fy]}"))
    return files, year


# ------------------------------------------------------------------------------------------
# Transparency resolutions (FY2026 .. FY2018)
# ------------------------------------------------------------------------------------------

TR_ISSUE = {2026: 103, 2025: 104, 2024: 105, 2023: 106, 2022: 107, 2021: 108, 2020: 109, 2019: 110, 2018: 111}


def tr_note(fy, cfg, rows_, charts):
    """The data/pdf_years.csv note for a transparency year."""
    reviewed = sum(1 for r in rows_ if r["review_id"])
    if fy == 2026:
        return (f"10 resolutions (Res 1013-2025 .. Res 0529-2026, 2025-08-14 .. 2026-06-30), "
                f"{len(rows_)} rows, {len(charts)} charts; each row has resolution_number and "
                "resolution_date. The charts print no money totals: printed_totals_tied is "
                "'Charts 1 through N' vs charts found (Reso 03-10 print it). Of the flagged "
                f"rows, {reviewed} are in the review file; the "
                "rest carry routine flags only (no-border cells, hyphenless EINs, compound "
                "words at a line end). pdf_sha256 = "
                "sha256 of the sorted '<sha256>  <path>' lines of the 10 PDFs. "
                "Review: research/2026-10-21-fy26-transparency-review/REVIEW.md")
    res = cfg["resolutions"]
    numbered = [r for r in res if r["number"]]
    unnumbered = [r for r in res if not r["number"]]
    printing = [r["seq"] for r in res if r["charts_printed"]]
    tied_how = (f"printed_totals_tied is 'Charts 1 through N' vs charts found (Reso "
                f"{printing[0]:02d}-{printing[-1]:02d} print it)" if printing else
                "printed_totals_tied is n/a (no resolution prints a chart count either)")
    n_unnum = sum(1 for r in rows_ if not r["resolution_number"])
    return (f"{len(res)} resolutions ({numbered[0]['number']} .. {numbered[-1]['number']}, "
            f"{res[0]['date']} .. {res[-1]['date']}), {len(rows_)} rows, {len(charts)} charts; "
            "each row has resolution_date and resolution_number"
            + (f", except the {n_unnum} rows of Reso "
               + ", ".join(f"{r['seq']:02d} ({r['date']})" for r in unnumbered)
               + ", whose number is not on record (review item)" if unnumbered else "")
            + f". The charts print no money totals: {tied_how}. Of the flagged "
            f"rows, {reviewed} are in the review file; the rest carry routine flags only. "
            f"pdf_sha256 = sha256 of the sorted '<sha256>  <path>' lines of the {len(res)} PDFs. "
            f"Review: {cfg['review_dir']}/REVIEW.md")


def build_transparency(scratch, fy=2026):
    """Re-run code/parse_transparency_v2.py (all checks, image lattice and ink included) into the
    scratch folder and promote its row, chart, resolution and review tables (GitHub #103 FY2026,
    #104 FY2025, #105 FY2024, #106 FY2023, #107 FY2022, #108 FY2021, #109 FY2020, #110 FY2019, #111 FY2018). FY2022 Reso 02's media box starts at
    (-8.39, -8.39); the parser already writes its bbox_pt on the rendered page.

    One family row in data/pdf_years.csv covers a year's resolution PDFs: `source_pdf` is their
    folder and `pdf_sha256` the sha256 of the sorted "<sha256>  <path>" lines, so any change to
    any of them changes it. Every data row carries its own PDF and that PDF's hash. FY2024 Reso 01
    pp.3-61 carry /Rotate 90: the parser's bbox_pt is in display coordinates, so it is unrotated
    here (no FY2025 or FY2026 page has a /Rotate)."""
    import contextlib
    import hashlib
    import parse_transparency_v2 as tr
    cfg = tr.load_config(fy)
    yy = f"fy{fy % 100:02d}"
    decisions = os.path.join(REPO, cfg["review_dir"], "data", f"{yy}_tr_review_decisions.csv")
    os.makedirs(scratch, exist_ok=True)
    if os.path.exists(decisions):
        shutil.copy(decisions, os.path.join(scratch, f"{yy}_tr_review_decisions.csv"))
    with contextlib.redirect_stdout(io.StringIO()):
        if tr.main(["--fy", str(fy), "--out", scratch]) != 0:
            raise RuntimeError("parse_transparency_v2 failed")
    checks_txt = open(os.path.join(scratch, f"{yy}_tr_checks.txt"), encoding="utf-8").read()
    if "FAIL" in checks_txt.replace("(FAIL)", ""):
        raise RuntimeError("a transparency check failed; not promoting")
    pdfs = {r["seq"]: r for r in cfg["resolutions"]}
    shas = {r["seq"]: r["sha256"] for r in cfg["resolutions"]}
    order = lambda cols: CONTRACT + [c for c in cols if c not in CONTRACT]
    rows_ = read(os.path.join(scratch, f"{yy}_tr_rows.csv"))
    charts = read(os.path.join(scratch, f"{yy}_tr_charts.csv"))
    resos = read(os.path.join(scratch, f"{yy}_tr_resolutions.csv"))
    for r in rows_ + charts:
        seq = int(r["resolution_seq"])
        assert r["source_pdf"] == pdfs[seq]["pdf"] and r["pdf_sha256"] == shas[seq], r["source_pdf"]
    pages = {(p["resolution_seq"], p["pdf_page"]): p for p in read(os.path.join(scratch, f"{yy}_tr_pages.csv"))}
    for r in rows_:
        p = pages[(r["resolution_seq"], r["pdf_page"])]
        if int(p["rotation"]):
            r["bbox_pt"] = unrotate(r["bbox_pt"], int(p["rotation"]), float(p["width"]), float(p["height"]))
    for r in resos:
        r.update(fiscal_year=fy, pdf_page=1, bbox_pt="", review_id="", flags="")
    review = []
    for r in read(os.path.join(scratch, f"{yy}_tr_review.csv")):
        seq = int(r["resolution_seq"]) if r["resolution_seq"] else None
        review.append(dict(fiscal_year=fy, family="transparency",
                           source_pdf=pdfs[seq]["pdf"] if seq else "",
                           pdf_sha256=shas[seq] if seq else "", **r))
    files = {
        f"{yy}_tr_rows.csv": to_csv(rows_, order(list(rows_[0]))),
        f"{yy}_tr_charts.csv": to_csv(charts, order(list(charts[0]))),
        f"{yy}_tr_resolutions.csv": to_csv(resos, order(list(resos[0]))),
        f"{yy}_tr_review.csv": to_csv(review, list(review[0])),
    }
    folder = os.path.dirname(pdfs[1]["pdf"]) + "/"
    manifest = "".join(f"{shas[k]}  {pdfs[k]['pdf']}\n" for k in sorted(pdfs))
    n_printed = sum(1 for r in cfg["resolutions"] if r["charts_printed"])
    tied = sum(1 for r in resos if r["charts_printed"] and int(r["charts_printed"]) == int(r["charts"]))
    year = dict(fiscal_year=fy, family="transparency", source_pdf=folder,
                pdf_sha256=hashlib.sha256(manifest.encode()).hexdigest(), issue=TR_ISSUE[fy],
                status="reviewed", rows=len(rows_), flagged=sum(1 for r in rows_ if r["flags"]),
                printed_totals_tied=f"{tied}/{n_printed}" if n_printed else "n/a",
                note=tr_note(fy, cfg, rows_, charts))
    return files, year


FAMILIES = [("fy27", "capital_sd", lambda d: build_capital_sd(d, 2027)),
            ("fy27", "schedule_c", build_schedule_c),
            ("fy27", "terms", lambda d: build_terms(d, 2027)),
            ("fy26", "capital_sd", lambda d: build_capital_sd(d, 2026)),
            ("fy26", "terms", lambda d: build_terms(d, 2026)),
            ("fy26", "transparency", build_transparency),
            ("fy26", "schedule_c", lambda d: build_schedule_c(d, fy=2026)),
            ("fy25", "schedule_c", lambda d: build_schedule_c(d, fy=2025)),
            ("fy24", "schedule_c", lambda d: build_schedule_c(d, fy=2024)),
            ("fy23", "schedule_c", lambda d: build_schedule_c(d, fy=2023)),
            ("fy22", "schedule_c", lambda d: build_schedule_c(d, fy=2022)),
            ("fy21", "schedule_c", lambda d: build_schedule_c(d, fy=2021)),
            ("fy20", "schedule_c", lambda d: build_schedule_c(d, fy=2020)),
            ("fy19", "schedule_c", lambda d: build_schedule_c(d, fy=2019)),
            ("fy18", "schedule_c", lambda d: build_schedule_c(d, fy=2018)),
            ("fy25", "transparency", lambda d: build_transparency(d, 2025)),
            ("fy24", "transparency", lambda d: build_transparency(d, 2024)),
            ("fy23", "transparency", lambda d: build_transparency(d, 2023)),
            ("fy22", "transparency", lambda d: build_transparency(d, 2022)),
            ("fy21", "transparency", lambda d: build_transparency(d, 2021)),
            ("fy20", "transparency", lambda d: build_transparency(d, 2020)),
            ("fy19", "transparency", lambda d: build_transparency(d, 2019)),
            ("fy18", "transparency", lambda d: build_transparency(d, 2018)),
            ("fy25", "capital_sd", lambda d: build_capital_sd(d, 2025)),
            ("fy25", "terms", lambda d: build_terms(d, 2025)),
            ("fy24", "capital_sd", lambda d: build_capital_sd(d, 2024)),
            ("fy24", "terms", lambda d: build_terms(d, 2024)),
            ("fy23", "capital_sd", lambda d: build_capital_sd(d, 2023)),
            ("fy23", "terms", lambda d: build_terms(d, 2023)),
            ("fy22", "capital_sd", lambda d: build_capital_sd(d, 2022)),
            ("fy22", "terms", lambda d: build_terms(d, 2022)),
            ("fy21", "terms", lambda d: build_terms(d, 2021)),
            ("fy20", "capital_sd", lambda d: build_capital_sd(d, 2020)),
            ("fy19", "capital_sd", lambda d: build_capital_sd(d, 2019)),
            ("fy18", "capital_sd", lambda d: build_capital_sd(d, 2018)),
            ("fy18", "terms", lambda d: build_terms(d, 2018))]


def build_all():
    out, years = {}, []
    with tempfile.TemporaryDirectory() as tmp:
        for fy, fam, fn in FAMILIES:
            files, year = fn(os.path.join(tmp, f"{fy}_{fam}"))
            for name, text in files.items():
                out[os.path.join("data", fy, "pdf", fam, name)] = text
            years.append(year)
    out["data/pdf_years.csv"] = to_csv(sorted(years, key=lambda y: (-y["fiscal_year"], y["family"])),
                                       YEARS_COLS)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    out = build_all()
    bad = 0
    for path, text in sorted(out.items()):
        full = os.path.join(REPO, path)
        if a.write:
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            print(f"wrote {path} ({len(list(csv.reader(io.StringIO(text)))) - 1} rows)")
        else:
            cur = open(full, encoding="utf-8").read() if os.path.exists(full) else None
            if cur != text:
                bad += 1
                print(f"DRIFT {path}")
            else:
                print(f"ok    {path}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
