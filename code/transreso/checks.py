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
from transreso import reader, structure

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
    # A chart's first page printing "(continued)" is read as its start, allowed only as a named
    # exception (FY2023 Reso 08 p.32).
    cs_exc = {(e["resolution_seq"], e["pdf_page"]) for e in cfg.get("exceptions", [])
              if e["check_id"] == "T3.continued_start"}
    cs = {(f["resolution_seq"], f["pdf_page"]) for f in S["flags"] if f["check_id"] == "T3.continued_start"}
    t3 += [dict(resolution_seq=k[0], pdf_page=k[1]) for k in sorted(cs ^ cs_exc)]
    # FY2022: a caption that repeats without "(continued)", or a "(continued)" caption with the
    # wrong chart number, is read as continuing the chart before it; named exceptions only.
    cont_named = {}
    for cid in ("T3.continued_missing", "T3.continued_number"):
        ex = {(e["resolution_seq"], e["pdf_page"]) for e in cfg.get("exceptions", []) if e["check_id"] == cid}
        got = {(f["resolution_seq"], f["pdf_page"]) for f in S["flags"] if f["check_id"] == cid}
        t3 += [dict(resolution_seq=k[0], pdf_page=k[1]) for k in sorted(got ^ ex)]
        cont_named[cid] = len(got & ex)
    # FY2022 Reso 02 p.106: a page with no table that prints only a footnote and "Page 84" (the
    # chart before it spilled over). Named exception: its label joins the count in page order.
    spill = {(e["resolution_seq"], e["pdf_page"]) for e in cfg.get("exceptions", [])
             if e["check_id"] == "T3.label_page"}
    gaps = []
    # A chart page that prints no "Page n" label is allowed only as a named exception; the
    # labels that are printed must still count every chart page (FY2025 Reso 02 pp.74-75).
    unlab = {(e["resolution_seq"], e["pdf_page"]) for e in cfg.get("exceptions", [])
             if e["check_id"] == "T3.page_label"}
    unlab_seen = set()
    for r in R:
        seq = r["res"]["seq"]
        nums = sorted(c["chart_number"] for c in S["charts"] if c["resolution_seq"] == seq)
        if nums != list(range(1, len(nums) + 1)):
            gaps.append((seq, f"chart numbers {nums[:5]}… not 1..{len(nums)}"))
        printed = r["res"]["charts_printed"]
        if printed and printed != len(nums):
            gaps.append((seq, f"prints 'Charts 1 through {printed}', found {len(nums)}"))
        def spill_label(p):
            pl = [int(m.group(1)) for ln in r["pages"][p["pdf_page"] - 1]["lines"]
                  for m in [structure.PAGE_LABEL.match(ln["text"])] if m]
            return dict(p, page_label=pl[0] if len(pl) == 1 else "")
        cps = [p if p["tables"] else spill_label(p) for p in S["page_info"]
               if p["resolution_seq"] == seq and (p["tables"] or (seq, p["pdf_page"]) in spill)]
        for p in cps:
            if p["page_label"] == "" and (seq, p["pdf_page"]) in unlab:
                unlab_seen.add((seq, p["pdf_page"]))
        labels = [p["page_label"] if not (p["page_label"] == "" and (seq, p["pdf_page"]) in unlab)
                  else i for i, p in enumerate(cps, start=1)]
        if labels != list(range(1, len(labels) + 1)):
            gaps.append((seq, f"'Page n' labels under the charts are not 1..{len(labels)}"))
    tabled = {(p["resolution_seq"], p["pdf_page"]) for p in S["page_info"] if p["tables"]}
    for k in sorted(spill & tabled):
        gaps.append((k[0], f"named label-only page p.{k[1]} has a table"))
    for k in sorted(unlab - unlab_seen):
        gaps.append((k[0], f"named unlabelled page p.{k[1]} prints a label or is not a chart page"))
    out("T3.charts", not t3 and not gaps,
        f"{len(S['charts'])} charts on {len(chart_pages)} pages; printed chart counts tie on "
        f"{sum(1 for r in R if r['res']['charts_printed'])} of "
        f"{sum(1 for r in R if r['res']['charts_printed'])} resolutions that print one; "
        f"{len(t3)} caption problems; {len(gaps)} numbering problems"
        + (f"; {len(unlab_seen)} chart pages print no 'Page n' label (named exceptions, counted "
           f"by the labels around them)" if unlab else "")
        + (f"; {len(cs & cs_exc)} chart's first page prints '(continued)' (named exception, read "
           f"as the chart's start)" if cs_exc else "")
        + (f"; {cont_named['T3.continued_missing']} pages repeat a caption without '(continued)' "
           f"and {cont_named['T3.continued_number']} print the wrong chart number on a "
           f"'(continued)' caption (named exceptions, read as continuations)"
           if any(cont_named.values()) else "")
        + (f"; {len(spill)} page(s) with no table print only a footnote and a 'Page n' label "
           f"(named exception, counted)" if spill else ""))
    for s_, pg in sorted(spill - tabled):
        flag("T3.label_page", s_, pg, "page with no table prints only a footnote and a 'Page n' "
             "label (the chart before it spilled over); counted (named exception in the config)",
             severity="warn")
    for s_, pg in sorted(unlab_seen):
        flag("T3.page_label", s_, pg, "chart page prints no 'Page n' label; the next label "
             "counts it (named exception in the config)", severity="warn")
    for s, m in gaps:
        flag("T3.charts", s, 0, m)

    # T4
    t4 = [f for f in S["flags"] if f["check_id"] == "T4.headers"]
    # FY2022 "Beating Hearts": a header with no Agency or Amount, allowed only as a named
    # exception (T4.no_amount).
    na_ex = {(e["resolution_seq"], e["pdf_page"]) for e in cfg.get("exceptions", [])
             if e["check_id"] == "T4.no_amount"}
    na = {(f["resolution_seq"], f["pdf_page"]) for f in S["flags"] if f["check_id"] == "T4.no_amount"}
    t4 += [dict(resolution_seq=k[0], pdf_page=k[1]) for k in sorted(na ^ na_ex)]
    out("T4.headers", not t4, f"{len(t4)} unrecognised headers"
        + (f"; {len(na & na_ex)} chart pages print no Agency or Amount column (named exceptions; "
           f"{sum(1 for a in rows if a['chart_kind'] == 'no_amount')} rows kept with a blank "
           f"amount)" if na_ex else ""))

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
    no_amt = [r for r in rows if r["amount"] is None and r["chart_kind"] != "no_amount"]
    no_ein = [r for r in rows if not r["ein"]]
    empty = S.get("empty_rows", [])
    out("T5.anchors", not diffs and not no_amt,
        f"{n_tok} EIN-shaped words on the visible text ({n_tok_all} counting clipped letters), "
        f"{sum(by_page.values())} rows with an EIN; {len(diffs)} pages differ; "
        f"{len(no_amt)} rows without a readable amount; {len(no_ein)} rows print no EIN"
        + (f"; {len(empty)} drawn rows print nothing and are not rows (" +
           ", ".join(f"Reso {e['resolution_seq']:02d} p.{e['pdf_page']} row {e['row_index']}"
                     for e in empty) + ")" if empty else ""))
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
    over = [a for a in rows if any(f.startswith("overlaid_text") for f in a["row_flags"])]
    ov_ex = {(e["resolution_seq"], e["pdf_page"]) for e in cfg.get("exceptions", [])
             if e["check_id"] == "T7.overlaid"}
    ov_bad = ov_ex - {(a["resolution_seq"], a["pdf_page"]) for a in over}
    out("T7.chars", not orph and not ov_bad,
        f"{sum(p['nonws_chars'] for r in R for p in r['pages'])} non-space chars; "
        f"{len(orph)} in a table but in no cell; "
        f"{sum(p['clipped_chars'] for r in R for p in r['pages'])} clipped (hidden) chars in "
        f"{len(clip)} runs, each listed for review"
        + (f"; {sum(1 for c in clip if c[2].get('overlaid'))} runs drawn on top of other text "
           f"and not shown on the page ({len(over)} rows, critical review items)" if over else ""))
    for a in over:
        flag("T7.overlaid", a["resolution_seq"], a["pdf_page"],
             f"text drawn on top of this row's cell is hidden on the page ({a['hidden_text']}); "
             f"kept out of the value. Confirm on the page.", row_id=a["row_id"])
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
    exc11 = {(e["resolution_seq"], e["pdf_page"], e["row_index"])
             for e in cfg.get("exceptions", []) if e["check_id"] == "T11.markers"}
    named11 = {(a["resolution_seq"], a["pdf_page"], a["row_index"]) for a in t11} & exc11
    out("T11.markers", len(named11) == len(t11) and named11 == exc11,
        f"{sum(1 for a in rows if a['org_marker'] == '**')} rows marked **, "
        f"{sum(1 for a in rows if a['org_marker'] == '***')} marked ***, "
        f"{sum(1 for a in rows if a['prequal_pending'])} pending pre-qualification; "
        f"{len(t11)} without their footnote or with an odd * cell"
        + (f" ({len(named11)} a named exception in the config, kept as printed and in the "
           f"review file)" if exc11 else ""))
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
    money, in_notes = [], 0
    notes = {(n["resolution_seq"], n["pdf_page"]): n["lines"] for n in S.get("chart_notes", [])}
    for r in R:
        for p in r["pages"]:
            if not p["tables"]:
                continue
            for ln in p["lines"]:
                if ln["text"] in notes.get((r["res"]["seq"], p["page"]), ()):
                    in_notes += bool(reader.MONEY.search(ln["text"]))
                    continue
                if reader.MONEY.search(ln["text"]):
                    money.append((r["res"]["seq"], p["page"], ln["text"]))
    out("T15.printed_totals", not money,
        f"{len(money)} money amounts printed outside the tables on chart pages: the FY{cfg['fiscal_year']} "
        f"charts print no totals, so there is nothing to tie (the arithmetic is reported, not checked)"
        + (f"; {in_notes} in notes under no-amount charts (in the review file with the chart)"
           if notes else ""))
    for s, pg, t in money:
        flag("T15.printed_totals", s, pg, f"money printed outside a table: {t!r}")

    # T16
    bad16 = [a for a in rows for f in ("source", "member", "agency", "purpose")
             if clean_text(a[f + "_raw"])[0] != a[f]]
    bad16 += [a for a in rows if (clean_text(a["org_raw"])[0][:len(a["org"])] != a["org"])]
    out("T16.values", not bad16, f"{len(bad16)} clean values not reproducible from raw")
    return res, flags
