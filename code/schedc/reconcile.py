"""
Stage 8 -- reconcile to what the PDF prints (PLAN §3, §6 H10-H13).

  H10  each category's summary lines sum to its printed TOTAL
  H11  the initiative boxes in a category equal its summary lines, as a multiset of
       (initiative, amount)
  H12  each initiative's rows sum to what its designation statement says it designated:
         full          rows = box amount
         partial       rows = designated, and reserve + designated = box amount
         reserve_only  no rows, reserve = box amount
         none          rows = box amount (member-item initiatives print no statement)
         reserve_all   no rows; the whole box is held post-adoption (FY2026)
         designated    rows = designated = box amount (FY2026)
         direct        designated straight to an agency: stated amounts add to the box; rows,
                       if any, add to the box; else the box is a direct pot (FY2026)
  H13  roll-up: body rows + post-adoption reserves (+ direct pots) = sum of the category TOTALs

A failure is a flag. It passes only as a named exception in the year's config, matched on
(check, page, expected, observed), so a second error in the same place still fails. The PDF
is never corrected.
"""
import re
from collections import Counter

MONEY = re.compile(r"\$([\d,]+)")


def _exception(cfg, check, page, expected, observed):
    for e in cfg.get("exceptions", []):
        if e["check"] == check and (e.get("page"), e.get("expected"), e.get("observed")) == \
                (page, expected, observed):
            return e
    return None


def run(S, cfg):
    """Returns (results, flags). results is a list of dicts, one per check instance."""
    results, flags = [], []

    def record(check, page, label, expected, observed, **kw):
        ok = expected == observed
        exc = None if ok else _exception(cfg, check, page, expected, observed)
        status = "ok" if ok else ("named_exception" if exc else "FAIL")
        results.append(dict(check_id=check, pdf_page=page, label=label, expected=expected,
                            observed=observed, diff=(observed or 0) - (expected or 0),
                            status=status, note=exc["note"] if exc else "", **kw))
        if not ok:
            flags.append(dict(check_id=check, severity="warn" if exc else "critical",
                              pdf_page=page, message=f"{label}: expected {expected:,}, "
                              f"observed {observed:,}" + (f" (named exception: {exc['note']})"
                                                          if exc else ""),
                              expected=expected, observed=observed, **kw))

    cats = list(dict.fromkeys(r["category"] for r in S["summary"]))
    totals = {}
    for cat in cats:
        lines = [r for r in S["summary"] if r["category"] == cat and not r["is_total"]]
        tots = [r for r in S["summary"] if r["category"] == cat and r["is_total"]]
        if len(tots) != 1:
            flags.append(dict(check_id="H10.total", severity="critical",
                              pdf_page=lines[0]["pdf_page"] if lines else 0,
                              message=f"{cat}: {len(tots)} TOTAL lines"))
            continue
        tot = tots[0]
        totals[cat] = tot["amount"]
        record("H10.category_total", tot["pdf_page"], cat, tot["amount"],
               sum(r["amount"] or 0 for r in lines), category=cat)
        boxes = Counter((i["initiative"], i["amount"]) for i in S["initiatives"]
                        if i["category"] == cat)
        summ = Counter((r["initiative"], r["amount"]) for r in lines)
        # Named aliases (config `box_aliases`): a summary line printed under another name than
        # its box, or one summary line for several boxes (FY2026 p.112 SAVE). Each must match
        # exactly; each use is a warn flag, so a person sees it.
        for al in cfg.get("box_aliases", []):
            if al["category"] != cat:
                continue
            want = Counter(tuple(b) for b in al["boxes"])
            key = tuple(al["summary"])
            if not (want - boxes) and summ[key]:
                boxes = boxes - want + Counter({key: 1})
                flags.append(dict(check_id="H11.box_alias", severity="warn",
                                  pdf_page=al["page"], category=cat, dollar_impact=0,
                                  message=f"{cat}: summary line {key[0]!r} ${key[1]:,} is printed "
                                  "as box(es) " + "; ".join(f"{b[0]!r} ${b[1]:,}" for b in al["boxes"])
                                  + f" ({al['note']})"))
        if boxes != summ:
            for k in sorted((boxes - summ).keys() | (summ - boxes).keys(), key=str):
                flags.append(dict(check_id="H11.box_vs_summary", severity="critical",
                                  pdf_page=tot["pdf_page"], category=cat,
                                  message=f"{cat}: {k[0]!r} ${k[1]:,} boxes={boxes[k]} "
                                  f"summary={summ[k]}"))
        results.append(dict(check_id="H11.box_vs_summary", pdf_page=tot["pdf_page"], label=cat,
                            expected=sum(summ.values()), observed=sum((boxes & summ).values()),
                            diff=0, status="ok" if boxes == summ else "FAIL", note="",
                            category=cat))
    for c in cfg["categories"]:
        if c not in totals:
            flags.append(dict(check_id="H10.total", severity="critical", pdf_page=0,
                              message=f"category {c!r} has no summary table"))

    reserves = direct = 0
    for ini in S["initiatives"]:
        k, amt, rows = ini["statement_kind"], ini["amount"], ini["rows_sum"]
        kw = dict(initiative=ini["initiative"], initiative_id=ini["initiative_id"],
                  category=ini["category"])
        label = f"{ini['initiative']} ({k})"
        if k == "partial":
            record("H12.designated_sum", ini["pdf_page"], label, ini["designated"], rows, **kw)
            record("H12.statement_adds_up", ini["pdf_page"], label, amt,
                   ini["reserve"] + ini["designated"], **kw)
            reserves += ini["reserve"]
        elif k == "reserve_only":
            record("H12.reserve_only_rows", ini["pdf_page"], label, 0, ini["n_rows"], **kw)
            record("H12.statement_adds_up", ini["pdf_page"], label, amt, ini["reserve"], **kw)
            reserves += ini["reserve"]
        elif k == "reserve_all":
            # "will designate awards post-adoption": no amount printed, so the whole box is
            # the reserve; the only check is that no rows are printed under it.
            record("H12.reserve_only_rows", ini["pdf_page"], label, 0, ini["n_rows"], **kw)
            reserves += amt or 0
        elif k == "designated":
            record("H12.designated_sum", ini["pdf_page"], label, ini["designated"], rows, **kw)
            record("H12.statement_adds_up", ini["pdf_page"], label, amt, ini["designated"], **kw)
        elif k == "direct":
            # Designated straight to an agency (CUNY, DOE). Rows, when printed, add to the box;
            # amounts, when stated, add to the box; otherwise the box is a direct pot.
            stated = [int(v.replace(",", "")) for v in MONEY.findall(ini["statement"])]
            if stated:
                record("H12.statement_adds_up", ini["pdf_page"], label, amt, sum(stated), **kw)
            if ini["n_rows"]:
                record("H12.designated_sum", ini["pdf_page"], label, amt, rows, **kw)
            else:
                direct += amt or 0
        else:
            record("H12.designated_sum", ini["pdf_page"], label, amt, rows, **kw)

    body = sum(a["amount"] or 0 for a in S["awards"] if a["section"] == "body")
    record("H13.rollup", 0, "body rows + post-adoption reserves vs sum of category TOTALs"
           + (" (+ direct agency designations)" if direct else ""),
           sum(totals.values()), body + reserves + direct)
    return results, flags, dict(category_totals=sum(totals.values()), body_rows=body,
                                reserves=reserves, direct=direct)
