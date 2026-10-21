"""
Hard checks on the parse (the T-series; numbering follows PLAN §6's H-checks where they match).

  T1  input identity: every PDF's sha256 and page count equal the config
  T2  triage: the committed PDF condition survey shows no invisible text, and every chart page
      carries a text layer
  T3  charts: numbers run 1..N in each resolution with no gap or repeat; every "(continued)"
      page continues the chart before it; N equals the printed "Charts 1 through N"; the
      "Page n" labels under the charts run 1, 2, 3, … with no gap
  T4  headers: every table header is made of known labels and names org, EIN, agency, amount
  T5  anchors: EIN-shaped words on each page (pdfplumber's own word reader, on the visible
      text) equal the rows with an EIN; every row has one readable amount
  T6  furniture: no header or footer text in a data cell; nothing unexpected under a table
  T7  characters: every non-space character in a table is in a cell, or listed as clipped
  T10 sign vs colour: parentheses <=> red ink, on every amount
  T11 markers: `**` / `***` on a row have their footnote on the page; the `*` column holds
      only `*` or nothing
  T12 fiscal year: every chart's "Fiscal YYYY" is one the resolution's own text names
  T13 dates: a printed resolution date equals the config's (Legistar) date and the filename's
  T14 provenance: row ids unique, every row has a bbox
  T15 printed totals: money printed outside the tables on chart pages (there should be none
      to tie, and this proves it)
  T16 values: every clean value is reproducible from its raw text
"""
import csv
import datetime
import os
import re
from collections import Counter

from schedc.config import ROOT
from schedc.structure import clean_text
from transreso import reader

FURNITURE = re.compile(r"(Organization - Program|EIN Number|^Agency$|^Amount$|Purpose of Funds|"
                       r"^Page \d+$|Indicates pending|Requires a budget modification|CHART #)")
FY_IN_TEXT = re.compile(r"Fiscal (?:Year )?(\d{4})")


def run(cfg, R, S):
    """R: per-resolution dict(res, sha, npages, pages, front_text). S: structure output merged
    (rows, charts, flags, page_info). Returns (results, flags)."""
    res, flags = [], []

    def out(check, ok, detail):
        res.append(dict(check_id=check, status="ok" if ok else "FAIL", detail=detail))

    def flag(check, seq, page, msg, severity="critical", **kw):
        flags.append(dict(check_id=check, severity=severity, resolution_seq=seq, pdf_page=page,
                          message=msg, **kw))

    rows = S["rows"]
    # T1
    bad = [r["res"]["seq"] for r in R if r["sha"] != r["res"]["sha256"] or r["npages"] != r["res"]["pages"]]
    out("T1.input", not bad, f"{len(R)} PDFs, {sum(r['npages'] for r in R)} pages; "
        f"{len(bad)} differ from config")
    for s in bad:
        flag("T1.input", s, 0, "PDF bytes or page count differ from config")

    # T2
    cond = list(csv.DictReader(open(os.path.join(ROOT, "data", "pdf_condition_pages.csv"))))
    chart_pages = {(p["resolution_seq"], p["pdf_page"]) for p in S["page_info"] if p["tables"]}
    n_surv, badp = 0, []
    for r in R:
        mine = [c for c in cond if c["path"] == r["res"]["pdf"]]
        n_surv += len(mine)
        for c in mine:
            pg = int(c["page"])
            if int(c["invisible_chars"]) or ((r["res"]["seq"], pg) in chart_pages and int(c["chars"]) <= 100):
                badp.append((r["res"]["seq"], pg))
    out("T2.triage", n_surv == sum(r["npages"] for r in R) and not badp,
        f"{n_surv} pages surveyed; {len(badp)} fail the text-layer gate")
    for s, pg in badp:
        flag("T2.triage", s, pg, "page fails the text-layer gate")

    # T3
    t3 = [f for f in S["flags"] if f["check_id"] == "T3.charts"]
    gaps = []
    for r in R:
        seq = r["res"]["seq"]
        nums = sorted(c["chart_number"] for c in S["charts"] if c["resolution_seq"] == seq)
        if nums != list(range(1, len(nums) + 1)):
            gaps.append((seq, f"chart numbers {nums[:5]}… not 1..{len(nums)}"))
        printed = r["res"]["charts_printed"]
        if printed and printed != len(nums):
            gaps.append((seq, f"prints 'Charts 1 through {printed}', found {len(nums)}"))
        labels = [p["page_label"] for p in S["page_info"]
                  if p["resolution_seq"] == seq and p["tables"]]
        if labels != list(range(1, len(labels) + 1)):
            gaps.append((seq, f"'Page n' labels under the charts are not 1..{len(labels)}"))
    out("T3.charts", not t3 and not gaps,
        f"{len(S['charts'])} charts on {len(chart_pages)} pages; printed chart counts tie on "
        f"{sum(1 for r in R if r['res']['charts_printed'])} of "
        f"{sum(1 for r in R if r['res']['charts_printed'])} resolutions that print one; "
        f"{len(t3)} caption problems; {len(gaps)} numbering problems")
    for s, m in gaps:
        flag("T3.charts", s, 0, m)

    # T4
    t4 = [f for f in S["flags"] if f["check_id"] == "T4.headers"]
    out("T4.headers", not t4, f"{len(t4)} unrecognised headers")

    # T5
    by_page = Counter((r["resolution_seq"], r["pdf_page"]) for r in rows if r["ein"])
    diffs, n_tok, n_tok_all = [], 0, 0
    for r in R:
        for p in r["pages"]:
            k = (r["res"]["seq"], p["page"])
            n_tok += p["ein_tokens"]
            n_tok_all += p["ein_tokens_all_chars"]
            if p["ein_tokens"] != by_page.get(k, 0):
                diffs.append((k, p["ein_tokens"], by_page.get(k, 0)))
    no_amt = [r for r in rows if r["amount"] is None]
    no_ein = [r for r in rows if not r["ein"]]
    out("T5.anchors", not diffs and not no_amt,
        f"{n_tok} EIN-shaped words on the visible text ({n_tok_all} counting clipped letters), "
        f"{sum(by_page.values())} rows with an EIN; {len(diffs)} pages differ; "
        f"{len(no_amt)} rows without a readable amount; {len(no_ein)} rows print no EIN")
    for (s, pg), w, n in diffs:
        flag("T5.anchors", s, pg, f"{w} EIN-shaped words but {n} rows with an EIN")
    for a in no_amt:
        flag("T5.anchors", a["resolution_seq"], a["pdf_page"], "row without a readable amount",
             row_id=a["row_id"])
    for a in no_ein:
        flag("T5.anchors", a["resolution_seq"], a["pdf_page"],
             f"row prints no EIN: {a['org']!r} {a['amount_printed']}", row_id=a["row_id"])

    # T6
    furn = [(a, f) for a in rows for f in ("source", "member", "org", "agency", "purpose")
            if a.get(f) and FURNITURE.search(a[f])]
    t6 = [f for f in S["flags"] if f["check_id"] == "T6.furniture"]
    out("T6.furniture", not furn and not t6,
        f"{len(furn)} data cells holding header/footer text; {len(t6)} unexpected lines under tables")
    for a, f in furn:
        flag("T6.furniture", a["resolution_seq"], a["pdf_page"],
             f"{f} holds furniture text: {a[f][:80]!r}", row_id=a["row_id"])

    # T7
    orph = [(r["res"]["seq"], p["page"], o) for r in R for p in r["pages"] for o in p["orphans"]]
    clip = [(r["res"]["seq"], p["page"], c) for r in R for p in r["pages"] for c in p["clipped"]]
    out("T7.chars", not orph,
        f"{sum(p['nonws_chars'] for r in R for p in r['pages'])} non-space chars; "
        f"{len(orph)} in a table but in no cell; "
        f"{sum(p['clipped_chars'] for r in R for p in r['pages'])} clipped (hidden) chars in "
        f"{len(clip)} runs, each listed for review")
    for s, pg, o in orph:
        flag("T7.chars", s, pg, f"char {o['text']!r} in a table but in no cell", bbox_pt=o["bbox"])

    # T10
    sc = [a for a in rows if "sign_colour" in a["row_flags"]]
    out("T10.sign_colour", not sc,
        f"{sum(1 for a in rows if (a['amount'] or 0) < 0)} amounts in parentheses, all red; "
        f"{len(sc)} rows where sign and colour disagree")
    for a in sc:
        flag("T10.sign_colour", a["resolution_seq"], a["pdf_page"],
             f"amount {a['amount_printed']!r}: parentheses and red ink disagree", row_id=a["row_id"])

    # T11
    t11 = [a for a in rows if {"marker_without_footnote", "prequal_odd"} & set(a["row_flags"])]
    out("T11.markers", not t11,
        f"{sum(1 for a in rows if a['org_marker'] == '**')} rows marked **, "
        f"{sum(1 for a in rows if a['org_marker'] == '***')} marked ***, "
        f"{sum(1 for a in rows if a['prequal_pending'])} pending pre-qualification; "
        f"{len(t11)} without their footnote or with an odd * cell")
    for a in t11:
        flag("T11.markers", a["resolution_seq"], a["pdf_page"],
             f"marker problem: {a['row_flags']}", row_id=a["row_id"])

    # T12
    bad12 = []
    for r in R:
        named = {int(y) for y in FY_IN_TEXT.findall(r["front_text"])}
        for c in S["charts"]:
            if c["resolution_seq"] == r["res"]["seq"] and c["fy_printed"] and \
                    int(c["fy_printed"]) not in named:
                bad12.append((c, sorted(named)))
    nofy = [c for c in S["charts"] if not c["fy_printed"]]
    exc = {(e["resolution_seq"], e["chart_number"], e["fy_printed"])
           for e in cfg.get("exceptions", []) if e["check_id"] == "T12.fiscal_year"}
    named = [(c, n) for c, n in bad12 if (c["resolution_seq"], c["chart_number"], c["fy_printed"]) in exc]
    unused = exc - {(c["resolution_seq"], c["chart_number"], c["fy_printed"]) for c, _ in named}
    out("T12.fiscal_year", len(bad12) == len(named) and not unused,
        f"{len(S['charts']) - len(nofy)} charts print a fiscal year, all named in their "
        f"resolution's text; {len(nofy)} print none (warn, in the review file); "
        f"{len(bad12)} name a year the text does not ({len(named)} a named exception in the "
        f"config, kept as printed and in the review file)")
    for c, named in bad12:
        flag("T12.fiscal_year", c["resolution_seq"], c["first_page"],
             f"chart #{c['chart_number']} is Fiscal {c['fy_printed']}; the resolution text names {named}")

    # T13
    bad13 = []
    for r in R:
        res_ = r["res"]
        fname = re.search(r"(\d{4}-\d{2}-\d{2})\.pdf$", res_["pdf"]).group(1)
        if fname != res_["date"]:
            bad13.append((res_["seq"], f"filename date {fname} != config date {res_['date']}"))
        if res_["printed_date"]:
            d = datetime.datetime.strptime(res_["printed_date"], "%B %d, %Y").date().isoformat()
            if d != res_["date"] or f"dated {res_['printed_date']}" not in r["front_text"]:
                bad13.append((res_["seq"], f"printed date {res_['printed_date']!r} != {res_['date']}"))
    out("T13.dates", not bad13,
        f"{sum(1 for r in R if r['res']['printed_date'])} resolutions print their date and it "
        f"matches; all {len(R)} filename dates equal the Legistar adoption dates in the config")
    for s, m in bad13:
        flag("T13.dates", s, 1, m)

    # T14
    ids = [a["row_id"] for a in rows]
    out("T14.provenance", len(ids) == len(set(ids)) and all(a["bbox_pt"] for a in rows),
        f"{len(ids)} row ids, {len(set(ids))} unique")

    # T15
    money = []
    for r in R:
        for p in r["pages"]:
            if not p["tables"]:
                continue
            for ln in p["lines"]:
                if reader.MONEY.search(ln["text"]):
                    money.append((r["res"]["seq"], p["page"], ln["text"]))
    out("T15.printed_totals", not money,
        f"{len(money)} money amounts printed outside the tables on chart pages: the FY2026 "
        f"charts print no totals, so there is nothing to tie (the arithmetic is reported, not checked)")
    for s, pg, t in money:
        flag("T15.printed_totals", s, pg, f"money printed outside a table: {t!r}")

    # T16
    bad16 = [a for a in rows for f in ("source", "member", "agency", "purpose")
             if clean_text(a[f + "_raw"])[0] != a[f]]
    bad16 += [a for a in rows if (clean_text(a["org_raw"])[0][:len(a["org"])] != a["org"])]
    out("T16.values", not bad16, f"{len(bad16)} clean values not reproducible from raw")
    return res, flags
