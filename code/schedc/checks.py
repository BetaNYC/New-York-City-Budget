"""
Structural hard checks on the parse itself (PLAN §6): H1-H7, H14, H16. The arithmetic checks
(H10-H13) are in reconcile.py, lattice agreement (H8) and ink (H9) in code/schedc_cv/, the
disclosure floor (H17) in disclosure.py.

Each check returns a list of result dicts {check_id, status, detail} and appends flags.
"""
import csv
import os
import re

from schedc.config import ROOT
from schedc.vector import EIN_TOKEN

FURNITURE = re.compile(r"(Legal Name of Organization|Tax ID|^EIN$|Purpose of Funds|"
                       r"Council Member$|^Page \d+$|Appendix [ABC]:|Adopted Expense Budget)")


def section_of_page(cfg, pn):
    for r in cfg["page_ranges"]:
        if r["first"] <= pn <= r["last"]:
            return r["name"]
    return None


def run(cfg, pdf_sha, pages, S):
    res, flags = [], []

    def out(check, ok, detail):
        res.append(dict(check_id=check, status="ok" if ok else "FAIL", detail=detail))

    def flag(check, page, msg, **kw):
        flags.append(dict(check_id=check, severity="critical", pdf_page=page, message=msg, **kw))

    # H1 input identity
    ok = pdf_sha == cfg["sha256"] and len(pages) == cfg["pages"]
    out("H1.input", ok, f"sha256 {pdf_sha[:12]}… pages {len(pages)}")
    if not ok:
        flag("H1.input", 0, "PDF bytes or page count differ from config")

    # H2 triage, from the committed PDF condition survey (code/pdf_condition.py)
    rows = [r for r in csv.DictReader(open(os.path.join(ROOT, "data", "pdf_condition_pages.csv")))
            if r["path"] == cfg["pdf"]]
    award_pages = {a["pdf_page"] for a in S["awards"]}
    bad = [int(r["page"]) for r in rows if int(r["invisible_chars"]) != 0 or
           (int(r["page"]) in award_pages and int(r["chars"]) <= 100)]
    out("H2.triage", len(rows) == cfg["pages"] and not bad,
        f"{len(rows)} pages surveyed; {len(bad)} with invisible text or <=100 chars on an award page")
    for p in bad:
        flag("H2.triage", p, "page fails the text-layer gate")

    # H3 page map: every award row's section equals its page's configured range
    wrong = [a for a in S["awards"] if section_of_page(cfg, a["pdf_page"]) != a["section"]]
    out("H3.pagemap", not wrong, f"{len(wrong)} award rows outside their configured section range")
    for a in wrong:
        flag("H3.pagemap", a["pdf_page"], f"row in section {a['section']} on a page configured "
             f"as {section_of_page(cfg, a['pdf_page'])}", award_id=a["award_id"])

    # H4 headers: recorded by structure.build as flags; summarised here
    h4 = [f for f in S["flags"] if f["check_id"].startswith("H4")]
    out("H4.headers", not h4, f"{len(h4)} unknown or incomplete award-table headers")

    # H5 anchor census: EIN-shaped words per page == award rows on that page with an EIN
    by_page = {}
    for a in S["awards"]:
        if a["ein"]:
            by_page[a["pdf_page"]] = by_page.get(a["pdf_page"], 0) + 1
    diffs = [(p["page"], p["ein_tokens"], by_page.get(p["page"], 0)) for p in pages
             if p["ein_tokens"] != by_page.get(p["page"], 0)]
    one = [a for a in S["awards"] if not a["ein"] or a["amount"] is None]
    out("H5.anchors", not diffs and not one,
        f"{sum(p['ein_tokens'] for p in pages)} EIN-shaped words, "
        f"{sum(by_page.values())} rows with an EIN; {len(diffs)} pages differ; "
        f"{len(one)} rows without exactly one EIN and one amount")
    for pn, words, rws in diffs:
        flag("H5.anchors", pn, f"{words} EIN-shaped words but {rws} award rows with an EIN")
    for a in one:
        flag("H5.anchors", a["pdf_page"], "row without a readable EIN or amount",
             award_id=a["award_id"])

    # H6 furniture in data cells
    furn = [(a, f) for a in S["awards"] for f in ("member", "sponsor", "delegation", "org",
                                                   "agency", "purpose")
            if a.get(f) and FURNITURE.search(a[f])]
    out("H6.furniture", not furn, f"{len(furn)} data cells holding header/footer text")
    for a, f in furn:
        flag("H6.furniture", a["pdf_page"], f"{f} holds furniture text: {a[f][:80]!r}",
             award_id=a["award_id"])

    # H7 character conservation inside award tables
    award_tables = {(a["pdf_page"], a["table_index"]) for a in S["awards"]}
    orph = [(p["page"], o) for p in pages for o in p["orphans"]
            if (p["page"], o["table"]) in award_tables]
    unm = [f for f in S["flags"] if f["check_id"] == "H7.unmapped"]
    out("H7.chars", not orph and not unm,
        f"{sum(p['nonws_chars'] for p in pages)} non-space chars; {len(orph)} orphan chars in "
        f"award tables; {len(unm)} unmapped cells")
    for pn, o in orph:
        flag("H7.chars", pn, f"char {o['text']!r} in an award table but in no cell",
             bbox_pt=o["bbox"])

    # H14 provenance and unique ids
    ids = [a["award_id"] for a in S["awards"]]
    out("H14.provenance", len(ids) == len(set(ids)) and all(a.get("bbox_pt") for a in S["awards"]),
        f"{len(ids)} award_ids, {len(set(ids))} unique")

    # H16 no value altered: printed fields equal the cell text; clean differs only by listed rules
    from schedc.structure import clean_text
    bad16 = [a for a in S["awards"]
             for f in ("member", "sponsor", "delegation", "org", "agency", "purpose")
             if a.get(f + "_raw") and clean_text(a[f + "_raw"])[0] != a[f]]
    out("H16.values", not bad16, f"{len(bad16)} clean values not reproducible from raw")
    return res, flags
