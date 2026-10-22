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
from schedc.structure import TEXT_FIELDS
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
        if a.get("fiscal_conduit_ein"):
            # A fiscal conduit's EIN printed on the row (FY2018 "FC EIN" column).
            by_page[a["pdf_page"]] = by_page.get(a["pdf_page"], 0) + 1
    for sa in S.get("subawards", []):
        if sa["ein"]:
            # A sub-award row of a side list (FY2019 pp.105-106, FY2018 p.106).
            by_page[sa["pdf_page"]] = by_page.get(sa["pdf_page"], 0) + 1
    diffs = [(p["page"], p["ein_tokens"], by_page.get(p["page"], 0)) for p in pages
             if p["ein_tokens"] != by_page.get(p["page"], 0)]
    # A page whose word count is off for a reason read off the page (FY2020 p.306: the text
    # layer glues one EIN to the name before it, "Students131693134", so the page has one
    # EIN-shaped word fewer than rows) passes only as a named exception matched on (page,
    # words, rows); a warn flag.
    pw = {(e["page"], e["words"], e["rows"]): e for e in cfg.get("exceptions", [])
          if e["check"] == "H5.page_words"}
    for d in [d for d in diffs if d in pw]:
        diffs.remove(d)
        flags.append(dict(check_id="H5.anchors", severity="warn", pdf_page=d[0],
                          dollar_impact=0, message=f"{d[1]} EIN-shaped words but {d[2]} award "
                          f"rows with an EIN (named exception: {pw[d]['note']})"))
    # A row whose printed EIN is not EIN-shaped (FY2026: two 8-digit EINs) passes only as a
    # named exception in the year's config, matched on (award_id, ein_printed).
    named = {(e["award_id"], e["ein_printed"]): e for e in cfg.get("exceptions", [])
             if e["check"] == "H5.anchors"}
    one = [a for a in S["awards"] if (not a["ein"] or a["amount"] is None)
           and (a["award_id"], a["ein_printed"]) not in named]
    exc = [a for a in S["awards"] if (a["award_id"], a["ein_printed"]) in named]
    out("H5.anchors", not diffs and not one,
        f"{sum(p['ein_tokens'] for p in pages)} EIN-shaped words, "
        f"{sum(by_page.values())} rows with an EIN; {len(diffs)} pages differ; "
        f"{len(one)} rows without exactly one EIN and one amount"
        + (f"; {len(exc)} named exceptions" if exc else ""))
    for pn, words, rws in diffs:
        flag("H5.anchors", pn, f"{words} EIN-shaped words but {rws} award rows with an EIN")
    for a in one:
        flag("H5.anchors", a["pdf_page"], "row without a readable EIN or amount",
             award_id=a["award_id"])
    for a in exc:
        e = named[(a["award_id"], a["ein_printed"])]
        flags.append(dict(check_id="H5.anchors", severity="warn", pdf_page=a["pdf_page"],
                          award_id=a["award_id"], field="ein",
                          message=f"EIN printed as {a['ein_printed']!r}, not an EIN; clean "
                          f"EIN left blank (named exception: {e['note']})"))

    # H6 furniture in data cells
    furn = [(a, f) for a in S["awards"] for f in TEXT_FIELDS
            if a.get(f) and FURNITURE.search(a[f])]
    # A cell whose own printed text matches a furniture pattern (FY2023 p.176: a purpose that
    # ends "in conjunction with Council Member") passes only as a named exception in the
    # year's config, matched on (award_id, field); it stays a warn in the review file.
    h6 = {(e["award_id"], e["field"]): e for e in cfg.get("exceptions", [])
          if e["check"] == "H6.furniture"}
    real = [(a, f) for a, f in furn if (a["award_id"], f) not in h6]
    out("H6.furniture", not real, f"{len(real)} data cells holding header/footer text"
        + (f"; {len(furn) - len(real)} named exceptions" if len(furn) > len(real) else ""))
    for a, f in furn:
        e = h6.get((a["award_id"], f))
        if e:
            flags.append(dict(check_id="H6.furniture", severity="warn", pdf_page=a["pdf_page"],
                              award_id=a["award_id"], field=f,
                              message=f"{f} matches a furniture pattern: {a[f][-80:]!r} "
                              f"(named exception: {e['note']})"))
            continue
        flag("H6.furniture", a["pdf_page"], f"{f} holds furniture text: {a[f][:80]!r}",
             award_id=a["award_id"])

    # H7 character conservation inside award tables
    award_tables = {(a["pdf_page"], a["table_index"]) for a in S["awards"]}
    bw = S.get("band_words", {})

    def _read_header_word(pn, o):
        # A loose header word read into its table's header (structure `header_band_words`).
        cx, cy = (o["bbox"][0] + o["bbox"][2]) / 2, (o["bbox"][1] + o["bbox"][3]) / 2
        return any(b[0] - 0.5 <= cx <= b[2] + 0.5 and b[1] <= cy < b[3]
                   for b in bw.get((pn, o["table"]), []))
    orph = [(p["page"], o) for p in pages for o in p["orphans"]
            if (p["page"], o["table"]) in award_tables and not _read_header_word(p["page"], o)]
    unm = [f for f in S["flags"] if f["check_id"] == "H7.unmapped"]
    out("H7.chars", not orph and not unm,
        f"{sum(p['nonws_chars'] for p in pages)} non-space chars; {len(orph)} orphan chars in "
        f"award tables; {len(unm)} unmapped cells")
    for pn, o in orph:
        flag("H7.chars", pn, f"char {o['text']!r} in an award table but in no cell",
             bbox_pt=o["bbox"])

    # H7 for tables built from horizontal rules (vector.hrule_tables, FY2024 only): their
    # column splits are inferred from the EIN and amount words, so no character may cross one.
    hts = [(p["page"], t) for p in pages for t in p["tables"] if t.get("hrule")]
    notes = [(p["page"], n) for p in pages for n in p.get("hrule_notes", [])]
    if hts or notes:
        cross = sum(t["split_straddles"] for _, t in hts)
        out("H7.hrule_splits", not cross and not notes,
            f"{len(hts)} tables from horizontal rules; {cross} characters cross a column "
            f"split; {len(notes)} stacks of rules not read")
        for pn, t in hts:
            if t["split_straddles"]:
                flag("H7.hrule_splits", pn, f"{t['split_straddles']} characters cross a column "
                     f"split at {t['splits']}", table_index=t["table_index"])
        for pn, n in notes:
            flag("H7.hrule_splits", pn, n)

    # H14 provenance and unique ids
    ids = [a["award_id"] for a in S["awards"]]
    out("H14.provenance", len(ids) == len(set(ids)) and all(a.get("bbox_pt") for a in S["awards"]),
        f"{len(ids)} award_ids, {len(set(ids))} unique")

    # H16 no value altered: printed fields equal the cell text; clean differs only by listed rules
    from schedc.structure import clean_text
    bad16 = [a for a in S["awards"]
             for f in TEXT_FIELDS
             if a.get(f + "_raw") and clean_text(a[f + "_raw"])[0] != a[f]]
    out("H16.values", not bad16, f"{len(bad16)} clean values not reproducible from raw")
    return res, flags
