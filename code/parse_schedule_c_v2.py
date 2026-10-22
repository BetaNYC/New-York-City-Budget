#!/usr/bin/env python3
"""
Schedule C from the PDF, checked (PLAN: research/2026-10-19-schedule-c-pdf-toolkit/PLAN.md).

  python3 code/parse_schedule_c_v2.py --fy 2027              full run, writes <review_dir>/data/
  python3 code/parse_schedule_c_v2.py --fy 2027 --no-cv      skip the image lattice and ink checks
  python3 code/parse_schedule_c_v2.py --fy 2027 --pages 279  iterate on some pages (writes nothing)

Stages (PLAN §3): vector lattice + cell text (schedc.vector) -> structure (schedc.structure)
-> structural checks H1-H7, H14, H16 (schedc.checks) -> image lattice H8 and ink coverage H9
(schedc_cv, needs opencv + numpy) -> reconcile to printed totals H10-H13 (schedc.reconcile)
-> disclosure alignment, report-only, H17 (schedc.disclosure) -> review file (schedc.review).

The vector pass is cached in build/schedc/fyNNNN/ (gitignored), keyed by the PDF sha256,
the x_tolerance and the source of schedc/vector.py. No network. Outputs are deterministic:
sorted, rounded to 0.01 pt, no timestamps.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from schedc import checks, config, disclosure, reconcile, review, structure, vector  # noqa: E402

ROOT = config.ROOT
# The explorer's row contract (NYCB-explorer viz/explorer/INTEGRATION.md §1): fiscal_year,
# source_pdf, pdf_sha256, pdf_page, bbox_pt, review_id, flags, on every output row.
CONTRACT = ["fiscal_year", "source_pdf", "pdf_sha256", "pdf_page", "bbox_pt", "review_id", "flags"]
# row_flags (detail) -> check id (the `flags` column)
ROW_FLAG_CHECK = {"wrap_hyphen": "W5.wrap_hyphen", "ein_overflow_hyphen": "W.ein_overflow_hyphen",
                  "spanning_cell": "W.spanning_cell", "unmapped_cell": "H7.unmapped",
                  "empty_row": "H5.anchors", "ein_unreadable": "H5.anchors",
                  "amount_unreadable": "H5.anchors", "continuation_row": "W.continuation_row", "sliver_band": "W.continuation_row",
                  "headerless_table": "W.headerless_table",
                  "amount_no_dollar": "W.amount_no_dollar", "amount_bare": "W.amount_bare",
                  "cid_glyph": "W.cid_glyph",
                  "amount_split_digits": "W.amount_split_digits",
                  "amount_odd_format": "W.amount_odd_format",
                  "header_span_cell": "W.header_span_cell", "hrule_table": "W.hrule_table",
                  "loose_header": "W.loose_header", "band_header": "W.band_header", "subheading": "W.subheading",
                  "reattributed": "H12.initiative_pages",
                  "sliver_char": "W.sliver_char"}
AWARD_COLUMNS = [
    "award_id", "fiscal_year", "source_pdf", "section", "category", "initiative", "initiative_id",
    "member", "sponsor", "delegation", "org", "ein", "amount", "agency", "purpose",
    "ein_printed", "amount_printed", "member_raw", "sponsor_raw", "delegation_raw", "org_raw",
    "agency_raw", "purpose_raw", "clean_rules_applied", "row_flags", "image_check",
    "disclosure_status", "disclosure_reason", "pdf_sha256", "pdf_page", "table_index",
    "row_index", "bbox_pt", "lattice", "review_id", "flags"]


def bbox_s(b):
    return ",".join(f"{v:.2f}" for v in b)


def cached_vector(cfg, pdf_sha, cache_dir, pages=None):
    src = open(os.path.join(HERE, "schedc", "vector.py"), "rb").read()
    # Per-page table settings (config `vector_pages`, e.g. FY2025 p.167), part of the key.
    ps = {v["page"]: {k: x for k, x in v.items() if k not in ("page", "note")}
          for v in cfg.get("vector_pages", [])}
    hrule = bool(cfg["structure"].get("hrule_tables"))
    open_top = bool(cfg["structure"].get("open_top_rows"))
    opts = tuple(o for o in vector.VECTOR_OPTS if cfg["structure"].get(o))
    key = hashlib.sha256(pdf_sha.encode() + str(cfg["x_tolerance"]).encode() + src
                         + (json.dumps(ps, sort_keys=True).encode() if ps else b"")
                         + (b"hrule" if hrule else b"")
                         + (b"open_top" if open_top else b"")
                         + "".join(opts).encode()).hexdigest()[:16]
    path = os.path.join(cache_dir, f"vector-{key}.json")
    if pages is None and os.path.exists(path):
        return json.load(open(path))
    pg = vector.read_pdf(cfg["_pdf_abs"], pages=pages, x_tolerance=cfg["x_tolerance"],
                         page_settings=ps, hrule=hrule, open_top=open_top, opts=opts)
    if pages is None:
        os.makedirs(cache_dir, exist_ok=True)
        json.dump(pg, open(path, "w"))
    return pg


def run_cv(cfg, S, vpages, out_overlays, only_pages=None):
    """Image lattice compare + ink coverage, one page render at a time. Returns
    (row_results{award_id: rec}, page_results{page: dict}, flags, ink_acceptance)."""
    import pdfplumber
    import pypdfium2 as pdfium
    from schedc_cv import imagegrid, ink

    im = cfg["image"]
    dpi = im["dpi"]
    by_page = {}
    for a in S["awards"]:
        by_page.setdefault(a["pdf_page"], []).append(a)
    vmap = {p["page"]: p for p in vpages}
    row_res, page_res, flags = {}, {}, []
    carry = {} if im.get("carry_header") else None
    hrule_cache = {}
    roles = imagegrid.ROLE + [tuple(r) for r in im.get("extra_roles", [])]
    pdf = pdfplumber.open(cfg["_pdf_abs"])
    doc = pdfium.PdfDocument(cfg["_pdf_abs"])
    try:
        for pn in sorted(by_page):
            if only_pages and pn not in only_pages:
                continue
            aw = by_page[pn]
            gray = doc[pn - 1].render(scale=dpi / 72.0, grayscale=True).to_numpy()
            if gray.ndim == 3:
                gray = gray[:, :, 0]
            page = pdf.pages[pn - 1]
            ox, oy = vector.origin(page)     # pixels start at the MediaBox corner (FY2024)
            lats = imagegrid.lattices(gray, dpi, im["kernel_px"], im["region_pad_px"])
            irows = imagegrid.image_rows(vector.shift(page.chars, ox, oy), lats,
                                         cfg["x_tolerance"], carry, roles)
            res, extra = imagegrid.compare_page(aw, irows, im["row_tol_pt"])
            # Rows of tables ruled with horizontal lines only (vector.hrule_tables): the image
            # lattice cannot see them; their row bands are checked against pixel rules. With
            # `image.band_check` (FY2024) the same goes for any row the image lattice did not
            # see: tables whose only vertical "rules" are the edges of white-filled boxes
            # (e.g. p.178) look ruled to pdfplumber and unruled to the pixels.
            vt = {t["table_index"]: t for t in vmap[pn]["tables"]}
            for r in res:
                a = next(x for x in aw if x["award_id"] == r["award_id"])
                t = vt.get(a["table_index"], {})
                if (t.get("hrule") or im.get("band_check")) and r["status"] == "no_image_row":
                    ys = hrule_cache.get((pn, a["table_index"]))
                    if ys is None:
                        ys = hrule_cache[(pn, a["table_index"])] = imagegrid.hrule_ys(
                            gray, dpi, t["bbox"][0], t["bbox"][2], im["kernel_px"])
                    st, d = imagegrid.check_bands([a], ys, im["row_tol_pt"])[a["award_id"]]
                    r.update(status=st, diffs=d)
            for r in res:
                row_res[r["award_id"]] = r
            marks = []
            for r in res:
                if r["status"] not in ("agree", "bands_agree"):
                    a = next(x for x in aw if x["award_id"] == r["award_id"])
                    marks.append(a["bbox_pt"])
                    flags.append(dict(check_id="H8.lattice", severity="critical", pdf_page=pn,
                                      award_id=a["award_id"], table_index=a["table_index"],
                                      row_index=a["row_index"],
                                      field=";".join(r["diffs"]) or r["status"],
                                      message=f"image lattice {r['status']}: {r['diffs']}",
                                      value_image=json.dumps(r["image"], ensure_ascii=False),
                                      dollar_impact=a["amount"] or 0))
            for x in extra:
                if not any(v.strip() for v in x["fields"].values()):
                    continue
                marks.append([0, x["y0"], page.width, x["y1"]])
                flags.append(dict(check_id="H8.image_only_row", severity="critical",
                                  pdf_page=pn, message="image lattice row with no vector row",
                                  value_image=json.dumps(x["fields"], ensure_ascii=False),
                                  dollar_impact=structure.parse_amount(
                                      x["fields"].get("amount", "").strip()) or 0))
            # ink coverage over this page's award tables
            vp = vmap[pn]
            tids = {a["table_index"] for a in aw}
            tboxes = [t["bbox"] for t in vp["tables"] if t["table_index"] in tids]
            cboxes = [b for a in aw for b in a["_char_boxes"]]
            # Text read into a table but into no award row: loose header words and award-table
            # sub-headings (structure `header_band_words`, `award_subheadings`; FY2021).
            cboxes += [b for ti in tids for b in S.get("covered", {}).get((pn, ti), [])]
            hrows = S.get("header_rows", {})
            for t in vp["tables"]:
                if t["table_index"] in tids:
                    for r in t["rows"][:hrows.get((pn, t["table_index"]), 1)]:
                        for c in r["cells"]:
                            cboxes += c["char_boxes"]
            rules = _shift_rules(ink.rule_shapes(page), ox, oy)
            ik = ink.coverage(gray, dpi, tboxes, cboxes, rules, im["char_pad_px"],
                              im["rule_pad_px"], im["ink_cell_px"], im["ink_min_region_px"])
            for reg in ik["regions"]:
                marks.append(reg["bbox_pt"])
                flags.append(dict(check_id="H9.ink", severity="critical", pdf_page=pn,
                                  message=f"uncovered ink, {reg['ink_px']} px",
                                  bbox_pt=reg["bbox_pt"], dollar_impact=0))
            n_lat = sum(1 for L in lats if L["xs_pt"])
            page_res[pn] = dict(image_regions=len(lats), image_lattices=n_lat,
                                image_rows=len(irows),
                                rows_agree=sum(1 for r in res if r["status"] in
                                               ("agree", "bands_agree")),
                                ink_px=ik["ink_px"], uncovered_px=ik["uncovered_px"],
                                ink_regions=len(ik["regions"]))
            if marks and out_overlays:
                os.makedirs(out_overlays, exist_ok=True)
                _overlay_crops(gray, dpi, marks, os.path.join(out_overlays, f"p{pn:03d}"))
            page.flush_cache()

        # Ink acceptance (PLAN §3 stage 6): the check must fire when a known row or a single
        # character is withheld. Run on the configured page; recorded in checks.txt.
        acc = {}
        pn = cfg["image"]["ink_acceptance_page"]
        if pn in by_page and (not only_pages or pn in only_pages):
            aw = by_page[pn]
            gray = doc[pn - 1].render(scale=dpi / 72.0, grayscale=True).to_numpy()
            if gray.ndim == 3:
                gray = gray[:, :, 0]
            page = pdf.pages[pn - 1]
            ox, oy = vector.origin(page)
            vp = vmap[pn]
            tids = {a["table_index"] for a in aw}
            tboxes = [t["bbox"] for t in vp["tables"] if t["table_index"] in tids]
            hrows = S.get("header_rows", {})
            hdr = [b for t in vp["tables"] if t["table_index"] in tids
                   for r in t["rows"][:hrows.get((pn, t["table_index"]), 1)]
                   for c in r["cells"] for b in c["char_boxes"]]
            hdr += [b for ti in tids for b in S.get("covered", {}).get((pn, ti), [])]
            rules = _shift_rules(ink.rule_shapes(page), ox, oy)
            target = cfg["image"]["ink_acceptance_award_id"]

            def fire(boxes):
                return ink.coverage(gray, dpi, tboxes, boxes + hdr, rules, im["char_pad_px"],
                                    im["rule_pad_px"], im["ink_cell_px"],
                                    im["ink_min_region_px"])["regions"]
            allb = [b for a in aw for b in a["_char_boxes"]]
            row = [b for a in aw if a["award_id"] != target for b in a["_char_boxes"]]
            t_boxes = next(a["_char_boxes"] for a in aw if a["award_id"] == target)
            small = min(range(len(t_boxes)), key=lambda i: (t_boxes[i][2] - t_boxes[i][0]) *
                        (t_boxes[i][3] - t_boxes[i][1]))
            one = [b for b in allb if b is not t_boxes[small]]
            acc = dict(page=pn, award_id=target, clean=len(fire(allb)),
                       row_withheld=len(fire(row)), char_withheld=len(fire(one)),
                       char=t_boxes[small])
            if im.get("ink_acceptance_char") == "alnum":
                # The smallest box overall may be a comma or period, whose ink is below the
                # region floor (FY2026 p.176: a comma, 0 regions). Then test the smallest
                # letter or digit, and report the punctuation result next to it.
                txt = {tuple(vector.bbox2((c["x0"], c["top"], c["x1"], c["bottom"]))): c["text"]
                       for c in vector.shift(page.chars, ox, oy)}
                acc["char_text"] = txt.get(tuple(t_boxes[small]), "?")
                alnum = [i for i in range(len(t_boxes)) if txt.get(tuple(t_boxes[i]), "").isalnum()]
                k = min(alnum, key=lambda i: (t_boxes[i][2] - t_boxes[i][0]) *
                        (t_boxes[i][3] - t_boxes[i][1]))
                acc.update(any_char_withheld=acc["char_withheld"], any_char_text=acc["char_text"],
                           char=t_boxes[k], char_text=txt[tuple(t_boxes[k])],
                           char_withheld=len(fire([b for b in allb if b is not t_boxes[k]])))
    finally:
        pdf.close()
        doc.close()
    return row_res, page_res, flags, acc


def _shift_rules(rules, ox, oy):
    """ink.rule_shapes boxes moved to MediaBox-corner coordinates (vector.origin)."""
    if not ox and not oy:
        return rules
    return [(a - ox, b - oy, c - ox, d - oy) for a, b, c, d in rules]


def _overlay_crops(gray, dpi, marks, stem):
    """Small PNG crops (150 dpi) around each marked box, the box drawn in red."""
    import cv2
    s = dpi / 72.0
    H, W = gray.shape
    for k, b in enumerate(sorted(marks)):
        x0, y0 = max(0, int((b[0] - 30) * s)), max(0, int((b[1] - 30) * s))
        x1, y1 = min(W, int((b[2] + 30) * s)), min(H, int((b[3] + 30) * s))
        img = cv2.cvtColor(gray[y0:y1, x0:x1], cv2.COLOR_GRAY2BGR)
        cv2.rectangle(img, (int(b[0] * s) - x0 - 4, int(b[1] * s) - y0 - 4),
                      (int(b[2] * s) - x0 + 4, int(b[3] * s) - y0 + 4), (0, 0, 255), 3)
        img = cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        cv2.imwrite(f"{stem}-{k}.png", img)


def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--fy", type=int, required=True)
    ap.add_argument("--pages", help="e.g. 270-280 (iterate; writes nothing)")
    ap.add_argument("--no-cv", action="store_true", help="skip image lattice and ink checks")
    ap.add_argument("--cache-dir", default=os.path.join(ROOT, "build", "schedc"))
    ap.add_argument("--out", help="output folder (default: the year's review folder, "
                    "config `review_dir`)")
    a = ap.parse_args(argv)

    cfg = config.load(a.fy)
    yy = f"fy{a.fy % 100:02d}"
    pdf_sha = config.sha256_file(cfg["_pdf_abs"])
    only = None
    if a.pages:
        from ocr.render import parse_page_spec
        only = parse_page_spec(a.pages)
    cache = os.path.join(a.cache_dir, f"fy{a.fy}")
    vpages = structure.split_merged_tables(cached_vector(cfg, pdf_sha, cache), cfg)
    S = structure.build(vpages, cfg)
    for r in S["awards"]:
        r["fiscal_year"] = a.fy
        r["pdf_sha256"] = pdf_sha

    chk_res, chk_flags = checks.run(cfg, pdf_sha, vpages, S)
    rec_res, rec_flags, roll = reconcile.run(S, cfg)
    outdir = a.out or os.path.join(ROOT, cfg["review_dir"], "data")
    cv_rows, cv_pages, cv_flags, acc = {}, {}, [], {}
    if not a.no_cv:
        cv_rows, cv_pages, cv_flags, acc = run_cv(
            cfg, S, vpages, None if only else os.path.join(outdir, "overlays"), only)
    D = disclosure.align(S["awards"], a.fy)
    dsum = disclosure.summary(D, S["awards"])

    awards = S["awards"]
    if only:
        awards = [r for r in awards if r["pdf_page"] in only]
    for r in awards:
        i = D["matches"].get(r["award_id"])
        r["disclosure_status"] = D["disc"][i]["status"] if i is not None else "unmatched"
    reasons = {u["award"]["award_id"]: u for u in D["unmatched_sc"]}
    for r in awards:
        u = reasons.get(r["award_id"])
        r["disclosure_reason"] = u["reason"] if u else ""
        cr = cv_rows.get(r["award_id"])
        r["image_check"] = (cr["status"] + (":" + ";".join(cr["diffs"]) if cr["diffs"] else "")
                            ) if cr else ("not_run" if a.no_cv else "no_result")
        r["lattice"] = "both" if cr and cr["status"] == "agree" else \
            "vector+bands" if cr and cr["status"] == "bands_agree" else "vector"
        r["row_flags_s"] = ";".join(r["row_flags"])

    # Flags that need a person, as review items.
    items = []
    all_flags = S["flags"] + chk_flags + rec_flags + cv_flags
    aw_by_id = {r["award_id"]: r for r in S["awards"]}
    for f in all_flags:
        it = dict(f)
        it["what_to_check"] = f["message"]
        a_ = aw_by_id.get(f.get("award_id", ""))
        if a_:
            it.setdefault("table_index", a_["table_index"])
            it.setdefault("row_index", a_["row_index"])
            it["value_vector"] = json.dumps(a_["_raw"], ensure_ascii=False)
            it.setdefault("dollar_impact", a_["amount"] or 0)
        if f["check_id"].startswith(("H10", "H12", "H13")) and "expected" in f:
            it["dollar_impact"] = abs((f["observed"] or 0) - (f["expected"] or 0))
        items.append(it)
    for r in S["awards"]:
        h8 = {f.get("award_id") for f in cv_flags}
        if "ein_overflow_hyphen" in r["row_flags"] and r["award_id"] not in h8:
            items.append(dict(check_id="W.ein_overflow_hyphen", severity="warn",
                              pdf_page=r["pdf_page"], table_index=r["table_index"],
                              row_index=r["row_index"], award_id=r["award_id"], field="ein",
                              dollar_impact=r["amount"],
                              what_to_check="EIN cell also holds a lone '-' (the org text's "
                              "trailing hyphen running over the rule); EIN read as "
                              f"{r['ein']}. Confirm on the page.",
                              value_vector=json.dumps(r["_raw"], ensure_ascii=False)))
        if "amount_split_digits" in r["row_flags"]:
            items.append(dict(check_id="W.amount_split_digits", severity="warn",
                              pdf_page=r["pdf_page"], table_index=r["table_index"],
                              row_index=r["row_index"], award_id=r["award_id"], field="amount",
                              dollar_impact=r["amount"],
                              what_to_check="amount's last digit(s) sit in the narrow cell to "
                              f"its right; joined and read as {r['amount_printed']!r}. Confirm "
                              "on the page.",
                              value_vector=json.dumps(r["_raw"], ensure_ascii=False)))
        if "sliver_char" in r["row_flags"]:
            items.append(dict(check_id="W.sliver_char", severity="warn",
                              pdf_page=r["pdf_page"], table_index=r["table_index"],
                              row_index=r["row_index"], award_id=r["award_id"], field="org",
                              dollar_impact=r["amount"],
                              what_to_check="a letter centred in the narrow cell left of the text "
                              "(a phantom column) was read into the cell its glyph runs into; "
                              f"read as {r['org']!r}. Confirm on the page.",
                              value_vector=json.dumps(r["_raw"], ensure_ascii=False)))
        if "amount_odd_format" in r["row_flags"]:
            items.append(dict(check_id="W.amount_odd_format", severity="warn",
                              pdf_page=r["pdf_page"], table_index=r["table_index"],
                              row_index=r["row_index"], award_id=r["award_id"], field="amount",
                              dollar_impact=r["amount"],
                              what_to_check=f"amount printed as {r['amount_printed']!r} (cents "
                              f"or a trailing period); read as {r['amount']:,}. Confirm on the "
                              "page.",
                              value_vector=json.dumps(r["_raw"], ensure_ascii=False)))
        if "amount_no_dollar" in r["row_flags"]:
            items.append(dict(check_id="W.amount_no_dollar", severity="warn",
                              pdf_page=r["pdf_page"], table_index=r["table_index"],
                              row_index=r["row_index"], award_id=r["award_id"], field="amount",
                              dollar_impact=r["amount"],
                              what_to_check=f"amount printed without '$': "
                              f"{r['amount_printed']!r}; read as {r['amount']:,}. Confirm on "
                              "the page.",
                              value_vector=json.dumps(r["_raw"], ensure_ascii=False)))
        for fl in r["row_flags"]:
            if fl == "wrap_hyphen:org" and "-\nCouncil District" in r["org_raw"]:
                items.append(dict(check_id="W5.wrap_hyphen", severity="warn",
                                  pdf_page=r["pdf_page"], table_index=r["table_index"],
                                  row_index=r["row_index"], award_id=r["award_id"],
                                  field="org", dollar_impact=r["amount"],
                                  what_to_check="org line ends in '-' before 'Council District'; "
                                  f"clean value keeps it joined: {r['org']!r}. Is it ' - '?",
                                  value_vector=json.dumps(r["_raw"], ensure_ascii=False)))
    for k in cfg.get("known_issues", []):
        items.append(dict(k, severity=k.get("severity", "warn")))
    # Two initiatives on one page failing the same check (FY2023 p.43: two H12.designated_sum
    # exceptions) would share a review_id; there the initiative is the `field`, as two box
    # aliases on one page are (reconcile.py). No other year has such a pair.
    keys = Counter((i["check_id"], i.get("pdf_page", ""), i.get("table_index", ""),
                    i.get("row_index", ""), i.get("field", "")) for i in items)
    for i in items:
        if i.get("initiative") and not i.get("field") and keys[(
                i["check_id"], i.get("pdf_page", ""), i.get("table_index", ""),
                i.get("row_index", ""), "")] > 1:
            i["field"] = i["initiative"]

    if only:
        print(f"pages {a.pages}: {len(awards)} rows, ${sum(r['amount'] or 0 for r in awards):,}")
        for it in items:
            if not only or it.get("pdf_page") in only:
                print(" ", it["severity"], it["check_id"], it.get("pdf_page"), it["what_to_check"][:120])
        return 0

    os.makedirs(outdir, exist_ok=True)
    checks_ran = [c["check_id"] for c in chk_res] + ["H8.lattice", "H9.ink", "H10-H13", "H17"]
    rv_rows, stale = review.write(os.path.join(outdir, f"{yy}_sc_review.csv"), items, a.fy,
                                  os.path.join(outdir, f"{yy}_sc_review_decisions.csv"),
                                  checks_ran)
    # Per-row review_id (the row's first entry in the review file, by its sort order) and flags.
    rid, rflags = {}, {}
    for rv, it in ((rv, next(i for i in items if review.review_id(
            a.fy, i["check_id"], i.get("pdf_page", ""), i.get("table_index", ""),
            i.get("row_index", ""), i.get("field", "")) == rv["review_id"])) for rv in rv_rows):
        for key in ([("award", it["award_id"])] if it.get("award_id") else []) + \
                ([("initiative", it["initiative_id"])] if it.get("initiative_id") else []):
            rid.setdefault(key, rv["review_id"])
    for f in all_flags + items:
        if f.get("award_id"):
            rflags.setdefault(("award", f["award_id"]), set()).add(f["check_id"])
        if f.get("initiative_id"):
            rflags.setdefault(("initiative", f["initiative_id"]), set()).add(f["check_id"])
    for r in S["awards"]:
        fs = rflags.setdefault(("award", r["award_id"]), set())
        fs.update(ROW_FLAG_CHECK[fl.split(":")[0]] for fl in r["row_flags"])
        r["review_id"] = rid.get(("award", r["award_id"]), "")
        r["flags"] = ";".join(sorted(fs))
        r["source_pdf"] = cfg["pdf"]
    for r in S["awards"]:
        r["bbox_pt_s"] = bbox_s(r["bbox_pt"])
    rows_out = []
    for r in S["awards"]:
        o = {c: r.get(c, "") for c in AWARD_COLUMNS}
        o["row_flags"] = r["row_flags_s"]
        o["bbox_pt"] = r["bbox_pt_s"]
        o["amount"] = "" if r["amount"] is None else r["amount"]
        rows_out.append(o)
    write_csv(os.path.join(outdir, f"{yy}_sc_awards.csv"), rows_out, AWARD_COLUMNS)

    for i in S["initiatives"]:
        i.update(fiscal_year=a.fy, source_pdf=cfg["pdf"], pdf_sha256=pdf_sha,
                 review_id=rid.get(("initiative", i["initiative_id"]), ""),
                 flags=";".join(sorted(rflags.get(("initiative", i["initiative_id"]), ()))))
    ini_cols = CONTRACT[:4] + ["initiative_id", "category", "initiative", "amount", "amount_printed",
                "statement_kind", "reserve", "designated", "n_rows", "rows_sum", "statement",
                "table_index", "bbox_pt", "review_id", "flags"]
    for i in S["initiatives"]:
        i["bbox_pt"] = bbox_s(i["bbox_pt"]) if isinstance(i["bbox_pt"], list) else i["bbox_pt"]
    write_csv(os.path.join(outdir, f"{yy}_sc_initiatives.csv"), S["initiatives"], ini_cols)
    cat_rows = []
    for s in S["summary"]:
        cat_rows.append(dict(category=s["category"], line="TOTAL" if s["is_total"] else "initiative",
                             agency=s.get("agency", ""), initiative=s.get("initiative", ""),
                             amount=s["amount"], amount_printed=s["amount_printed"],
                             pdf_page=s["pdf_page"], table_index=s["table_index"],
                             row_index=s["row_index"], bbox_pt=bbox_s(s["bbox_pt"]),
                             fiscal_year=a.fy, source_pdf=cfg["pdf"], pdf_sha256=pdf_sha,
                             review_id="", flags=""))
    write_csv(os.path.join(outdir, f"{yy}_sc_categories.csv"), cat_rows,
              CONTRACT[:4] + ["category", "line", "agency", "initiative", "amount",
                              "amount_printed", "table_index", "row_index", "bbox_pt",
                              "review_id", "flags"])

    rows_by_page = Counter(r["pdf_page"] for r in S["awards"])
    page_rows = []
    for p in vpages:
        pr = dict(pdf_page=p["page"], section=checks.section_of_page(cfg, p["page"]),
                  width_pt=p["width"], height_pt=p["height"], tables=len(p["tables"]),
                  award_rows=rows_by_page.get(p["page"], 0), ein_tokens=p["ein_tokens"],
                  nonws_chars=p["nonws_chars"], zero_width_chars=p["zero_width_chars"])
        pr.update(cv_pages.get(p["page"], {}))
        page_rows.append(pr)
    write_csv(os.path.join(outdir, f"{yy}_sc_pages.csv"), page_rows,
              ["pdf_page", "section", "width_pt", "height_pt", "tables", "award_rows",
               "ein_tokens", "nonws_chars", "zero_width_chars", "image_regions",
               "image_lattices", "image_rows", "rows_agree", "ink_px", "uncovered_px",
               "ink_regions"])

    flag_cols = ["severity", "check_id", "pdf_page", "award_id", "table_index", "row_index",
                 "field", "message"]
    flag_rows = sorted(all_flags, key=lambda f: (f["severity"], f["check_id"], f["pdf_page"],
                                                  str(f.get("award_id", ""))))
    warn_rows = []
    for r in S["awards"]:
        for fl in r["row_flags"]:
            warn_rows.append(dict(severity="warn", check_id="row_flag", pdf_page=r["pdf_page"],
                                  award_id=r["award_id"], table_index=r["table_index"],
                                  row_index=r["row_index"], field=fl, message=fl))
    write_csv(os.path.join(outdir, f"{yy}_sc_flags.csv"), flag_rows + warn_rows, flag_cols)

    # Disclosure match file
    dm = []
    for r in S["awards"]:
        i = D["matches"].get(r["award_id"])
        d = D["disc"][i] if i is not None else None
        dm.append(dict(side="pdf", award_id=r["award_id"], pdf_page=r["pdf_page"],
                       section=r["section"], ein=r["ein"], amount=r["amount"], org=r["org"],
                       disclosure_row=d["row"] if d else "", disclosure_name=d["name"] if d else "",
                       disclosure_source=d["source"] if d else "",
                       disclosure_status=d["status"] if d else "",
                       ambiguous=bool(d and i in D["ambiguous"]),
                       reason="matched" if d else r["disclosure_reason"]))
    for u in D["unmatched_disc"]:
        d = u["disc"]
        dm.append(dict(side="disclosure_only", award_id="", pdf_page="", section="",
                       ein=d["ein"], amount=d["amount"], org="", disclosure_row=d["row"],
                       disclosure_name=d["name"], disclosure_source=d["source"],
                       disclosure_status=d["status"], ambiguous="", reason=u["reason"]))
    write_csv(os.path.join(outdir, f"{yy}_sc_disclosure_match.csv"), dm,
              ["side", "award_id", "pdf_page", "section", "ein", "amount", "org",
               "disclosure_row", "disclosure_name", "disclosure_source", "disclosure_status",
               "ambiguous", "reason"])


    # checks.txt
    L = []
    w = L.append
    tot = sum(r["amount"] or 0 for r in S["awards"])
    w(f"SCHEDULE C FY{a.fy} -- checks (code/parse_schedule_c_v2.py; config {cfg['_path']})")
    w(f"pdf {cfg['pdf']}  sha256 {pdf_sha}")
    w("")
    w(f"award rows: {len(S['awards']):,}  total ${tot:,}")
    for sec in ("body", "appendix_a", "appendix_b", "appendix_c"):
        rs = [r for r in S["awards"] if r["section"] == sec]
        w(f"  {sec:<11} {len(rs):>6,} rows  ${sum(r['amount'] or 0 for r in rs):>14,}")
    w(f"initiatives: {len(S['initiatives'])}  categories: {len(set(s['category'] for s in S['summary']))}")
    w("")
    w("STRUCTURAL CHECKS")
    for c in chk_res:
        w(f"  {c['status']:<5} {c['check_id']:<16} {c['detail']}")
    w("")
    w("PRINTED TOTALS (H10-H13)")
    st = Counter((r["check_id"], r["status"]) for r in rec_res)
    for k in sorted(st):
        w(f"  {k[0]:<26} {k[1]:<16} {st[k]}")
    for r in rec_res:
        if r["status"] != "ok":
            w(f"  -> {r['status']}: p.{r['pdf_page']} {r['label']}: expected {reconcile._n(r['expected'])}, "
              f"observed {reconcile._n(r['observed'])} (diff {r['diff']:+,}) {r['note']}")
    if roll.get("direct"):
        gap = roll["category_totals"] - roll["body_rows"] - roll["reserves"] - roll["direct"]
        w(f"  roll-up: category TOTALs ${roll['category_totals']:,} = body rows "
          f"${roll['body_rows']:,} + post-adoption reserves ${roll['reserves']:,} + designated "
          f"directly to an agency, no rows printed ${roll['direct']:,}"
          + (f" + ${gap:,}" if gap else ""))
    else:
        w(f"  roll-up: category TOTALs ${roll['category_totals']:,} = body rows ${roll['body_rows']:,}"
          f" + post-adoption reserves ${roll['reserves']:,} "
          f"{'+ $' + format(roll['category_totals'] - roll['body_rows'] - roll['reserves'], ',') if roll['category_totals'] != roll['body_rows'] + roll['reserves'] else ''}")
    w("  appendices print no total; their pots (DATA-ANOMALIES §19): "
      + ", ".join(f"{s} ${sum(r['amount'] or 0 for r in S['awards'] if r['section'] == s):,}"
                  for s in ("appendix_a", "appendix_b", "appendix_c")))
    w("")
    if a.no_cv:
        w("IMAGE LATTICE / INK: not run (--no-cv)")
    else:
        sc = Counter(r["status"] for r in cv_rows.values())
        w("IMAGE LATTICE (H8): rows read independently through code/ocr/grid.py lattices")
        w(f"  agree on every field: {sc.get('agree', 0):,} of {len(S['awards']):,}")
        if "bands_agree" in sc or "bands_differ" in sc:
            w(f"  rows in tables with no drawn vertical rules, which the image lattice cannot "
              f"see: {sc.get('bands_agree', 0) + sc.get('bands_differ', 0):,}; the pixels' "
              f"horizontal rules confirm the row band of {sc.get('bands_agree', 0):,}")
        for k in sorted(sc):
            if k not in ("agree", "bands_agree"):
                w(f"  {k}: {sc[k]}")
        w(f"  image rows with no vector row: {sum(1 for f in cv_flags if f['check_id'] == 'H8.image_only_row')}")
        w("INK COVERAGE (H9): uncovered-ink regions inside award tables")
        w(f"  regions: {sum(1 for f in cv_flags if f['check_id'] == 'H9.ink')}  "
          f"uncovered px total: {sum(p['uncovered_px'] for p in cv_pages.values()):,} of "
          f"{sum(p['ink_px'] for p in cv_pages.values()):,} ink px")
        if acc:
            im = cfg["image"]
            w(f"  acceptance on p.{acc['page']} ({acc['award_id']}): clean run {acc['clean']} regions; "
              f"row withheld -> {acc['row_withheld']}; one char withheld -> {acc['char_withheld']} "
              f"({'PASS' if acc['clean'] == 0 and acc['row_withheld'] and acc['char_withheld'] else 'FAIL'})"
              + (f"; the char is {acc['char_text']!r}" if "char_text" in acc else ""))
            if "any_char_withheld" in acc and not acc["any_char_withheld"]:
                w(f"  blind spot: withholding the row's smallest box, {acc['any_char_text']!r}, -> "
                  f"{acc['any_char_withheld']} regions (its ink is under the "
                  f"{im['ink_min_region_px']} px region floor). A lone dropped comma or period "
                  "is not visible to ink; H7 (every character lands in a cell) covers it")
    w("")
    w(f"DISCLOSURE (report-only; data/{yy}/expense_disclosure, "
      f"{cfg.get('disclosure_note', 'retrieved 2026-10-12')})")
    w(f"  pdf rows {dsum['pdf_rows']:,}; disclosure rows {dsum['disclosure_rows']:,}; "
      f"matched (EIN, amount, City-EIN name rule) {dsum['matched']:,}")
    nn = disclosure.align_without_name_rule(S["awards"], a.fy)
    if cfg.get("h17_floor", 9859):
        w(f"  matched without the City-EIN name rule (the 2026-10-19 prototype's H17 floor, "
          f"{cfg.get('h17_floor', 9859):,}): {nn:,}")
    else:   # no prototype for this year (FY2024): no floor to compare with
        w(f"  matched without the City-EIN name rule (no prototype floor for this year): {nn:,}")
    for sec in ("body", "appendix_a", "appendix_b", "appendix_c"):
        parts = []
        for stt in ("cleared", "pending", "other", "unmatched"):
            n = dsum["by"].get((sec, stt, "rows"), 0)
            if n:
                parts.append(f"{stt} {n:,} (${dsum['by'].get((sec, stt, 'dollars'), 0):,})")
        w(f"  {sec:<11} " + "; ".join(parts))
    w("  pdf rows without a disclosure row, by reason: " +
      ", ".join(f"{k} {v}" for k, v in sorted(dsum["sc_reasons"].items())))
    w("  disclosure rows without a pdf row, by reason: " +
      ", ".join(f"{k} {v} (${dsum['disc_reason_dollars'][k]:,})"
                for k, v in sorted(dsum["disc_reasons"].items())))
    w(f"  disclosure rows on keys where the allocation was a choice (ambiguous): {dsum['ambiguous_rows']:,}")
    w("")
    rw = Counter(fl.split(":")[0] for r in S["awards"] for fl in r["row_flags"])
    w("WARN COUNTS (not in the review file; listed in flags.csv)")
    w("  " + ", ".join(f"{k} {v}" for k, v in sorted(rw.items())))
    w(f"  zero-width chars dropped: {sum(p['zero_width_chars'] for p in vpages)}")
    w("")
    sev = Counter(r["severity"] for r in rv_rows)
    w(f"REVIEW FILE: {len(rv_rows)} rows ({sev.get('critical', 0)} critical, {sev.get('warn', 0)} warn); "
      f"stale decisions: {len(stale)}")
    open(os.path.join(outdir, f"{yy}_sc_checks.txt"), "w").write("\n".join(L) + "\n")

    import pdfplumber
    import pypdfium2
    man = dict(fiscal_year=a.fy, pdf=cfg["pdf"], pdf_sha256=pdf_sha, config=cfg["_path"],
               config_sha256=cfg["_sha256"], python=sys.version.split()[0],
               pdfplumber=pdfplumber.__version__, pypdfium2=str(pypdfium2.version.PYPDFIUM_INFO),
               pdfium=str(pypdfium2.version.PDFIUM_INFO))
    try:
        import cv2
        import numpy
        man.update(opencv=cv2.__version__, numpy=numpy.__version__)
    except ImportError:
        pass
    json.dump(man, open(os.path.join(outdir, f"{yy}_sc_manifest.json"), "w"), indent=2,
              sort_keys=True)
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
