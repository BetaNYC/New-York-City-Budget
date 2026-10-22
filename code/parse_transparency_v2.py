#!/usr/bin/env python3
"""
Transparency resolutions from the PDFs, checked (GitHub #103 FY2026, #104 FY2025, #105 FY2024,
#106 FY2023, #107 FY2022, #108 FY2021, #109 FY2020; toolkit plan:
research/2026-10-19-schedule-c-pdf-toolkit/PLAN.md).

  python3 code/parse_transparency_v2.py --fy 2026            full run, writes <review_dir>/data/
                                                             (config/transparency/fy<FY>.toml)
  python3 code/parse_transparency_v2.py --fy 2026 --no-cv    skip the image lattice and ink checks
  python3 code/parse_transparency_v2.py --fy 2026 --out DIR  write somewhere else

Stages: vector lattice + cell text by runs (transreso.reader) -> captions, headers, rows
(transreso.structure) -> hard checks T1-T16 (transreso.checks) -> image lattice compare (H8)
and ink coverage (H9) (transreso.image, schedc_cv) -> disclosure alignment and rescission
origins, report-only (transreso.disclosure) -> review file.

Every row carries the explorer's row contract (fiscal_year, source_pdf, pdf_sha256, pdf_page,
bbox_pt, review_id, flags) plus resolution_seq, resolution_number and resolution_date.
`fiscal_year` is the document year (the folder and data/pdf_years.csv row); the year whose
budget a row changes is `budget_fiscal_year`, from the chart caption.

The vector pass is cached in build/transreso/ (gitignored), keyed by PDF sha256, settings and
the reader's source. No network. Outputs are deterministic.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import tomllib
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from schedc.config import ROOT, sha256_file  # noqa: E402
from transreso import checks, disclosure, reader, structure  # noqa: E402

CONTRACT = ["fiscal_year", "source_pdf", "pdf_sha256", "pdf_page", "bbox_pt", "review_id", "flags"]
ROW_COLUMNS = CONTRACT + [
    "row_id", "resolution_seq", "resolution_number", "resolution_date", "resolution_date_source",
    "chart_number", "chart_title", "budget_fiscal_year", "chart_kind", "action", "agency_side",
    "source", "member", "member_header", "org", "org_marker", "budget_modification", "correction",
    "prequal_pending", "ein", "ein_format", "agency", "amount", "agy_num", "ua", "purpose",
    "purpose_header", "source_raw", "member_raw", "org_raw", "ein_printed", "agency_raw",
    "amount_printed", "prequal_printed", "purpose_raw", "hidden_text", "clean_rules_applied",
    "row_flags", "image_check", "lattice", "disclosure_status", "disclosure_reason",
    "disclosure_row", "table_index", "row_index"]
REVIEW_COLUMNS = ["review_id", "severity", "dollar_impact", "check_id", "resolution_seq",
                  "pdf_page", "row_index", "row_id", "field", "what_to_check", "value_vector",
                  "value_image", "expected", "observed", "overlay", "decision", "note"]
# Row flags that need a person (everything else is routine and only counted).
REVIEW_ROW_FLAGS = {"clipped_text": "W.clipped_text", "made_cell": "W.made_cell",
                    "prequal_star_in_org": "W.prequal_star_in_org", "ein_blank": "T5.anchors",
                    "ein_odd": "T5.anchors", "amount_zero": "W.amount_zero",
                    "cell_outside_header": "T7.chars", "empty_row": "T5.anchors"}
ROW_FLAG_CHECK = dict(REVIEW_ROW_FLAGS, wrap_hyphen="W5.wrap_hyphen", ein_no_hyphen="W.ein_no_hyphen",
                      spanning_cell="W.spanning_cell", made_cell_empty="W.made_cell_empty", sign_colour="T10.sign_colour",
                      marker_without_footnote="T11.markers", prequal_odd="T11.markers",
                      amount_unreadable="T5.anchors", unpaired_purpose="W.unpaired_purpose",
                      overlaid_text="T7.overlaid")


def load_config(fy):
    path = os.path.join(ROOT, "config", "transparency", f"fy{fy}.toml")
    raw = open(path, "rb").read()
    cfg = tomllib.loads(raw.decode("utf-8"))
    cfg["_path"] = os.path.relpath(path, ROOT)
    cfg["_sha256"] = hashlib.sha256(raw).hexdigest()
    return cfg


def review_id(fy, check, seq, page, row="", field=""):
    key = "|".join(str(v) for v in (fy, check, seq, page, row, field))
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def bbox_s(b):
    return ",".join(f"{v:.2f}" for v in b)


def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def overlay_pages(cfg, seq):
    """Pages of resolution `seq` where text drawn over a cell's own text is hidden (T7.overlaid,
    a named exception in the config; FY2022 Reso 09 p.38)."""
    return sorted(e["pdf_page"] for e in cfg.get("exceptions", [])
                  if e["check_id"] == "T7.overlaid" and e["resolution_seq"] == seq)


def cached_pages(cfg, res, sha, cache_dir):
    src = b"".join(open(os.path.join(HERE, "transreso", m), "rb").read()
                   for m in ("reader.py",)) + open(os.path.join(HERE, "schedc", "vector.py"), "rb").read()
    overlay = overlay_pages(cfg, res["seq"])
    key = hashlib.sha256(sha.encode() + str((cfg["x_tolerance"], cfg["run_gap_pt"])).encode()
                         + (str(overlay).encode() if overlay else b"") + src).hexdigest()[:16]
    path = os.path.join(cache_dir, f"r{res['seq']:02d}-{key}.json")
    if os.path.exists(path):
        return json.load(open(path))
    pg = reader.read_pdf(os.path.join(ROOT, res["pdf"]), cfg["x_tolerance"], cfg["run_gap_pt"],
                         overlay_pages=overlay)
    os.makedirs(cache_dir, exist_ok=True)
    json.dump(pg, open(path, "w"))
    return json.load(open(path))     # same shape as a cache hit (JSON keys are strings)


def front_text(res):
    import pdfplumber
    out = []
    with pdfplumber.open(os.path.join(ROOT, res["pdf"])) as pdf:
        for p in pdf.pages:
            if p.find_tables():
                break
            out.append(p.extract_text() or "")
    return " ".join(" ".join(out).split())


def _gray(doc, pn, dpi):
    g = doc[pn - 1].render(scale=dpi / 72.0, grayscale=True).to_numpy()
    return g[:, :, 0] if g.ndim == 3 else g


def _to_text_coords(gray, origin, dpi):
    """The rendered page shifted so pixel = pdfplumber point x dpi/72. pdfplumber counts from the
    media box's own origin, the renderer from the page's corner; they differ where the box does
    not start at (0, 0) (FY2022 Reso 02: -8.39, -8.39)."""
    import numpy as np
    s = dpi / 72.0
    for axis, o in ((1, origin[0]), (0, origin[1])):
        d = int(round(-o * s))
        if d > 0:
            gray = gray[d:, :] if axis == 0 else gray[:, d:]
        elif d < 0:
            pad = [(0, 0), (0, 0)]
            pad[axis] = (-d, 0)
            gray = np.pad(gray, pad, constant_values=255)
    return gray


def shift_box(b, origin):
    """A pdfplumber box -> the same box on the page as rendered (top-left corner = 0, 0)."""
    return [b[0] - origin[0], b[1] - origin[1], b[2] - origin[0], b[3] - origin[1]]


def run_cv(cfg, R, rows, out_overlays):
    """Image lattice compare (H8) and ink coverage (H9) on every chart page."""
    import pdfplumber
    import pypdfium2 as pdfium
    from schedc_cv import ink
    from transreso import image
    im = cfg["image"]
    dpi = im["dpi"]
    row_res, page_res, flags, acc = {}, {}, [], {}
    by_page = defaultdict(list)
    for r in rows:
        by_page[(r["resolution_seq"], r["pdf_page"])].append(r)
    marks_by_page = defaultdict(list)
    for x in R:
        res = x["res"]
        seq = res["seq"]
        path = os.path.join(ROOT, res["pdf"])
        pdf = pdfplumber.open(path)
        doc = pdfium.PdfDocument(path)
        try:
            for vp in x["pages"]:
                pn = vp["page"]
                if not vp["tables"]:
                    continue
                recs = by_page.get((seq, pn), [])
                gray = _gray(doc, pn, dpi)
                if any(vp.get("origin", (0, 0))):
                    gray = _to_text_coords(gray, vp["origin"], dpi)
                page = pdf.pages[pn - 1]
                irows, lats, notes = image.image_rows(page.chars, gray, dpi, im["kernel_px"],
                                                      im["region_pad_px"], cfg["x_tolerance"],
                                                      cfg["run_gap_pt"],
                                                      pn in overlay_pages(cfg, seq))
                res_, extra = image.compare_page(recs, irows, im["row_tol_pt"])
                for rr in res_:
                    row_res[rr["row_id"]] = rr
                    if rr["status"] != "agree":
                        a = next(r for r in recs if r["row_id"] == rr["row_id"])
                        marks_by_page[(seq, pn)].append(a["bbox_pt"])
                        flags.append(dict(check_id="H8.lattice", severity="critical",
                                          resolution_seq=seq, pdf_page=pn, row_id=a["row_id"],
                                          field=";".join(rr["diffs"]) or rr["status"],
                                          message=f"image lattice {rr['status']}: {rr['diffs']}",
                                          value_image=json.dumps(rr["image"], ensure_ascii=False),
                                          dollar_impact=abs(a["amount"] or 0)))
                for e in extra:
                    if not any(v.strip() for v in e["fields"].values()):
                        continue
                    marks_by_page[(seq, pn)].append([0, e["y0"], page.width, e["y1"]])
                    flags.append(dict(check_id="H8.image_only_row", severity="critical",
                                      resolution_seq=seq, pdf_page=pn,
                                      message="image lattice row with no vector row",
                                      value_image=json.dumps(e["fields"], ensure_ascii=False),
                                      dollar_impact=abs(structure.parse_amount(
                                          e["fields"].get("amount", "")) or 0)))
                t = vp["tables"][0]
                hdr = [b for h in t["header"] for b in h["char_boxes"]]
                if im.get("header_char_top_pt"):
                    # FY2022 Reso 02: bold capitals in the header ("EIN") rise above the box the
                    # text layer gives them; the config names how far (0 elsewhere).
                    hdr = [[b[0], b[1] - im["header_char_top_pt"], b[2], b[3]] for b in hdr]
                cboxes = [b for a in recs for b in a["_char_boxes"]] + hdr
                rules = ink.rule_shapes(page)
                ik = ink.coverage(gray, dpi, [t["bbox"]], cboxes, rules, im["char_pad_px"],
                                  im["rule_pad_px"], im["ink_cell_px"], im["ink_min_region_px"])
                for reg in ik["regions"]:
                    marks_by_page[(seq, pn)].append(reg["bbox_pt"])
                    flags.append(dict(check_id="H9.ink", severity="critical", resolution_seq=seq,
                                      pdf_page=pn, message=f"uncovered ink, {reg['ink_px']} px",
                                      bbox_pt=reg["bbox_pt"], dollar_impact=0))
                page_res[(seq, pn)] = dict(
                    image_regions=len(lats), image_lattices=sum(1 for L in lats if L["xs_pt"]),
                    image_rows=len(irows), rows_agree=sum(1 for r in res_ if r["status"] == "agree"),
                    image_notes="; ".join(notes), ink_px=ik["ink_px"],
                    uncovered_px=ik["uncovered_px"], ink_regions=len(ik["regions"]))
                if seq == im["ink_acceptance_seq"] and pn == im["ink_acceptance_page"]:
                    target = im["ink_acceptance_row_id"]

                    def fire(boxes):
                        return ink.coverage(gray, dpi, [t["bbox"]], boxes + hdr, rules,
                                            im["char_pad_px"], im["rule_pad_px"],
                                            im["ink_cell_px"], im["ink_min_region_px"])["regions"]
                    allb = [b for a in recs for b in a["_char_boxes"]]
                    t_boxes = next(a["_char_boxes"] for a in recs if a["row_id"] == target)
                    small = min(range(len(t_boxes)), key=lambda i: (t_boxes[i][2] - t_boxes[i][0]) *
                                (t_boxes[i][3] - t_boxes[i][1]))
                    acc = dict(seq=seq, page=pn, row_id=target, clean=len(fire(allb)),
                               row_withheld=len(fire([b for a in recs if a["row_id"] != target
                                                      for b in a["_char_boxes"]])),
                               char_withheld=len(fire([b for b in allb if b is not t_boxes[small]])),
                               char=t_boxes[small])
                if marks_by_page.get((seq, pn)) and out_overlays:
                    os.makedirs(out_overlays, exist_ok=True)
                    _overlay_crops(gray, dpi, marks_by_page[(seq, pn)],
                                   os.path.join(out_overlays, f"r{seq:02d}-p{pn:03d}"))
                page.flush_cache()
        finally:
            pdf.close()
            doc.close()
    return row_res, page_res, flags, acc


def _overlay_crops(gray, dpi, marks, stem):
    import cv2
    s = dpi / 72.0
    H, W = gray.shape
    seen = []
    for b in sorted(marks):
        if b in seen:
            continue
        seen.append(b)
        k = len(seen) - 1
        x0, y0 = max(0, int((b[0] - 30) * s)), max(0, int((b[1] - 30) * s))
        x1, y1 = min(W, int((b[2] + 30) * s)), min(H, int((b[3] + 30) * s))
        img = cv2.cvtColor(gray[y0:y1, x0:x1], cv2.COLOR_GRAY2BGR)
        cv2.rectangle(img, (int(b[0] * s) - x0 - 4, int(b[1] * s) - y0 - 4),
                      (int(b[2] * s) - x0 + 4, int(b[3] * s) - y0 + 4), (0, 0, 255), 3)
        img = cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        cv2.imwrite(f"{stem}-{k}.png", img)


def review_crops(cfg, R, rv, by_id, outdir):
    """One crop per review item that points at a row (the row boxed in red), or at a page
    (the page's top third, where the caption is). Sets each item's `overlay`."""
    import cv2
    import pypdfium2 as pdfium
    dpi = cfg["image"]["dpi"]
    os.makedirs(outdir, exist_ok=True)
    for x in R:
        seq = x["res"]["seq"]
        mine = [o for o in rv if str(o["resolution_seq"]) == str(seq) and o["pdf_page"] != ""]
        if not mine:
            continue
        doc = pdfium.PdfDocument(os.path.join(ROOT, x["res"]["pdf"]))
        try:
            for pn in sorted({int(o["pdf_page"]) for o in mine}):
                gray = _gray(doc, pn, dpi)
                s = dpi / 72.0
                H, W = gray.shape
                for o in (o for o in mine if int(o["pdf_page"]) == pn):
                    r = by_id.get(o["row_id"])
                    b = r["bbox_pt"] if r else [0, 0, W / s, H / s / 3]
                    x0, y0 = max(0, int((b[0] - 20) * s)), max(0, int((b[1] - 40) * s))
                    x1, y1 = min(W, int((b[2] + 20) * s)), min(H, int((b[3] + 40) * s))
                    img = cv2.cvtColor(gray[y0:y1, x0:x1], cv2.COLOR_GRAY2BGR)
                    if r:
                        cv2.rectangle(img, (int(b[0] * s) - x0 - 4, int(b[1] * s) - y0 - 4),
                                      (int(b[2] * s) - x0 + 4, int(b[3] * s) - y0 + 4), (0, 0, 255), 3)
                    img = cv2.resize(img, None, fx=0.4, fy=0.4, interpolation=cv2.INTER_AREA)
                    name = f"r{seq:02d}-p{pn:03d}-{o['review_id']}.png"
                    cv2.imwrite(os.path.join(outdir, name), img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                    o["overlay"] = f"overlays/{name}"
        finally:
            doc.close()


def purpose_pairs(rows):
    """On purpose-of-funds charts each change prints as a pair: the old purpose with the amount
    in parentheses, the new one without. Rows with no partner (same chart, EIN and |amount|)."""
    pool = defaultdict(list)
    for r in rows:
        if r["chart_kind"] == "purpose_of_funds" and r["amount"] is not None:
            pool[(r["resolution_seq"], r["chart_number"], r["ein"], abs(r["amount"]))].append(r)
    lone = []
    for k, rs in pool.items():
        neg = [r for r in rs if r["amount"] < 0]
        pos = [r for r in rs if r["amount"] > 0]
        if len(neg) != len(pos):
            more = neg if len(neg) > len(pos) else pos
            lone += more[len(min(neg, pos, key=len)):]
    return lone


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--fy", type=int, required=True)
    ap.add_argument("--no-cv", action="store_true")
    ap.add_argument("--cache-dir", default=os.path.join(ROOT, "build", "transreso"))
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    cfg = load_config(a.fy)
    yy = f"fy{a.fy % 100:02d}"
    outdir = a.out or os.path.join(ROOT, cfg["review_dir"], "data")
    cache = os.path.join(a.cache_dir, f"fy{a.fy}")

    R, rows, charts, sflags, page_info, empty, notes = [], [], [], [], [], [], []
    for res in cfg["resolutions"]:
        sha = sha256_file(os.path.join(ROOT, res["pdf"]))
        pages = cached_pages(cfg, res, sha, cache)
        S = structure.build(res, pages, cfg["x_tolerance"], a.fy)
        date_source = (f"printed p.1 and {cfg['numbers_source']}" if res["printed_date"]
                       else cfg["numbers_source"])
        for r in S["rows"]:
            r.update(fiscal_year=a.fy, source_pdf=res["pdf"], pdf_sha256=sha,
                     resolution_number=res["number"], resolution_date=res["date"],
                     resolution_date_source=date_source)
        for c in S["charts"]:
            c.update(resolution_number=res["number"], resolution_date=res["date"])
        R.append(dict(res=res, sha=sha, npages=len(pages), pages=pages, front_text=front_text(res)))
        rows += S["rows"]
        charts += S["charts"]
        sflags += S["flags"]
        page_info += S["page_info"]
        empty += S["empty_rows"]
        notes += S["chart_notes"]
    S = dict(rows=rows, charts=charts, flags=sflags, page_info=page_info, empty_rows=empty,
             chart_notes=notes)
    for r in purpose_pairs(rows):
        r["row_flags"].append("unpaired_purpose")

    chk_res, chk_flags = checks.run(cfg, R, S)
    cv_rows, cv_pages, cv_flags, acc = {}, {}, [], {}
    if not a.no_cv:
        cv_rows, cv_pages, cv_flags, acc = run_cv(cfg, R, rows, os.path.join(outdir, "overlays"))
    # Row boxes on the page as rendered (only differs where the page origin is not 0, 0).
    for x in R:
        for vp in x["pages"]:
            if any(vp.get("origin", (0, 0))):
                for r in rows:
                    if r["resolution_seq"] == x["res"]["seq"] and r["pdf_page"] == vp["page"]:
                        r["bbox_pt"] = shift_box(r["bbox_pt"], vp["origin"])
    D = disclosure.align(rows, a.fy)
    old = disclosure.compare_retired(rows, a.fy)

    for r in rows:
        st = D["per_row"].get(r["row_id"])
        r["disclosure_status"], r["disclosure_reason"], r["disclosure_row"] = st if st else ("n/a", "", "")
        cr = cv_rows.get(r["row_id"])
        r["image_check"] = (cr["status"] + (":" + ";".join(cr["diffs"]) if cr["diffs"] else "")
                            ) if cr else ("not_run" if a.no_cv else "no_result")
        r["lattice"] = "both" if cr and cr["status"] == "agree" else "vector"

    # Review items.
    items = []
    by_id = {r["row_id"]: r for r in rows}
    seen_check_row = set()
    for f in sflags + chk_flags + cv_flags:
        if f["check_id"] in ("T4.headers",) and not f.get("row_id"):
            pass
        it = dict(f, what_to_check=f["message"])
        r = by_id.get(f.get("row_id", ""))
        if r:
            it.setdefault("row_index", r["row_index"])
            it["value_vector"] = json.dumps(r["_raw"], ensure_ascii=False)
            it.setdefault("dollar_impact", abs(r["amount"] or 0))
            seen_check_row.add((f["check_id"], r["row_id"]))
        items.append(it)
    h8 = {f.get("row_id") for f in cv_flags}
    for r in rows:
        for fl in r["row_flags"]:
            base = fl.split(":")[0]
            cid = REVIEW_ROW_FLAGS.get(base)
            if not cid or (cid, r["row_id"]) in seen_check_row:
                continue
            if base == "clipped_text":
                what = (f"text hidden under the next cell ({r['hidden_text']}); the value keeps "
                        f"only what shows. Confirm on the page." +
                        (" The image lattice reads the cell differently (see H8)." if r["row_id"] in h8 else ""))
            elif base == "made_cell":
                what = f"no drawn cell under '{fl.split(':', 1)[1]}' in this row; read from the header's column. Confirm."
            elif base == "prequal_star_in_org":
                what = f"'*' printed at the end of the organization, not in the * column: {r['org_raw']!r}. Read as pending pre-qualification."
            elif base == "amount_zero":
                what = "amount prints as $0"
            else:
                what = f"row flag {fl}"
            seen_check_row.add((cid, r["row_id"]))
            items.append(dict(check_id=cid, severity="warn", resolution_seq=r["resolution_seq"],
                              pdf_page=r["pdf_page"], row_index=r["row_index"], row_id=r["row_id"],
                              field=fl.split(":", 1)[1] if ":" in fl else "",
                              dollar_impact=abs(r["amount"] or 0), what_to_check=what,
                              value_vector=json.dumps(r["_raw"], ensure_ascii=False)))
    for r in rows:
        if "unpaired_purpose" in r["row_flags"]:
            items.append(dict(check_id="W.unpaired_purpose", severity="warn",
                              resolution_seq=r["resolution_seq"], pdf_page=r["pdf_page"],
                              row_index=r["row_index"], row_id=r["row_id"], field="amount",
                              dollar_impact=abs(r["amount"] or 0),
                              what_to_check=f"purpose-of-funds row with no partner of the opposite "
                              f"sign (same chart, EIN, amount): {r['org']!r} {r['amount_printed']}",
                              value_vector=json.dumps(r["_raw"], ensure_ascii=False)))
    for r in rows:
        for pat in cfg.get("wrap_hyphen_review", []):
            for f in ("org", "purpose", "member", "source"):
                if pat in r[f + "_raw"]:
                    items.append(dict(check_id="W5.wrap_hyphen", severity="warn",
                                      resolution_seq=r["resolution_seq"], pdf_page=r["pdf_page"],
                                      row_index=r["row_index"], row_id=r["row_id"], field=f,
                                      dollar_impact=abs(r["amount"] or 0),
                                      what_to_check=f"{f} line ends in '-' before a capitalised "
                                      f"word; clean value keeps it joined: {r[f]!r}. Is it ' - '?",
                                      value_vector=json.dumps(r["_raw"], ensure_ascii=False)))
    known = {(k["resolution_seq"], k["pdf_page"]) for k in cfg.get("known_issues", [])}
    items = [it for it in items if not (it["check_id"] == "T12.fiscal_year" and
                                        it["severity"] == "warn" and
                                        (it.get("resolution_seq"), it.get("pdf_page")) in known)]
    for k in cfg.get("known_issues", []):
        items.append(dict(k, severity=k.get("severity", "warn")))
    decisions_path = os.path.join(outdir, f"{yy}_tr_review_decisions.csv")
    decided = {}
    if os.path.exists(decisions_path):
        decided = {d["review_id"]: d for d in csv.DictReader(open(decisions_path, encoding="utf-8"))}
    rv = []
    for it in items:
        o = {c: it.get(c, "") for c in REVIEW_COLUMNS}
        o["review_id"] = review_id(a.fy, it["check_id"], it.get("resolution_seq", ""),
                                   it.get("pdf_page", ""), it.get("row_index", ""), it.get("field", ""))
        d = decided.get(o["review_id"])
        if d:
            o["decision"], o["note"] = d.get("decision", ""), d.get("note", "")
        rv.append(o)
    # one entry per id (a row can raise the same check twice through two paths)
    rv = list({o["review_id"]: o for o in rv}.values())
    if not a.no_cv:
        review_crops(cfg, R, rv, by_id, os.path.join(outdir, "overlays"))
    sev = {"critical": 0, "warn": 1}
    rv.sort(key=lambda o: (sev.get(o["severity"], 2), -int(o["dollar_impact"] or 0),
                           int(o["resolution_seq"] or 0), int(o["pdf_page"] or 0), o["review_id"]))
    stale = sorted(set(decided) - {o["review_id"] for o in rv})

    # Row contract: review_id = the row's first review entry; flags = every check id on it.
    rid, rfl = {}, defaultdict(set)
    for o in rv:
        if o["row_id"]:
            rid.setdefault(o["row_id"], o["review_id"])
            rfl[o["row_id"]].add(o["check_id"])
    for f in sflags + chk_flags + cv_flags:
        if f.get("row_id"):
            rfl[f["row_id"]].add(f["check_id"])
    for r in rows:
        rfl[r["row_id"]].update(ROW_FLAG_CHECK[fl.split(":")[0]] for fl in r["row_flags"])
        r["review_id"] = rid.get(r["row_id"], "")
        r["flags"] = ";".join(sorted(rfl[r["row_id"]]))

    os.makedirs(outdir, exist_ok=True)
    out_rows = []
    for r in rows:
        o = {c: r.get(c, "") for c in ROW_COLUMNS}
        o["bbox_pt"] = bbox_s(r["bbox_pt"])
        o["row_flags"] = ";".join(r["row_flags"])
        o["amount"] = "" if r["amount"] is None else r["amount"]
        out_rows.append(o)
    write_csv(os.path.join(outdir, f"{yy}_tr_rows.csv"), out_rows, ROW_COLUMNS)
    write_csv(os.path.join(outdir, f"{yy}_tr_review.csv"), rv, REVIEW_COLUMNS)

    # Charts and resolutions.
    ch_rows = []
    for c in charts:
        rs = [r for r in rows if r["resolution_seq"] == c["resolution_seq"] and
              r["chart_number"] == c["chart_number"]]
        pos = [r["amount"] for r in rs if (r["amount"] or 0) > 0]
        neg = [r["amount"] for r in rs if (r["amount"] or 0) < 0]
        res = next(x["res"] for x in R if x["res"]["seq"] == c["resolution_seq"])
        ch_rows.append(dict(fiscal_year=a.fy, source_pdf=res["pdf"],
                            pdf_sha256=next(x["sha"] for x in R if x["res"]["seq"] == c["resolution_seq"]),
                            pdf_page=c["first_page"], bbox_pt="", review_id="",
                            flags=";".join(sorted({f for r in rs for f in r["flags"].split(";") if f})),
                            resolution_seq=c["resolution_seq"], resolution_number=c["resolution_number"],
                            resolution_date=c["resolution_date"], chart_number=c["chart_number"],
                            chart_title=c["title"], budget_fiscal_year=c["fy_printed"],
                            chart_kind=c["kind"], header=c["header"],
                            header_variants=" || ".join(sorted(c.get("header_variants", ()))),
                            first_page=c["first_page"], last_page=c["last_page"], pages=c["pages"],
                            rows=len(rs), positive_rows=len(pos), positive_sum=sum(pos),
                            negative_rows=len(neg), negative_sum=sum(neg), net=sum(pos) + sum(neg)))
    ch_cols = CONTRACT + ["resolution_seq", "resolution_number", "resolution_date", "chart_number",
                          "chart_title", "budget_fiscal_year", "chart_kind", "header",
                          "header_variants", "first_page", "last_page", "pages", "rows",
                          "positive_rows", "positive_sum", "negative_rows", "negative_sum", "net"]
    write_csv(os.path.join(outdir, f"{yy}_tr_charts.csv"), ch_rows, ch_cols)

    re_rows = []
    for x in R:
        res, seq = x["res"], x["res"]["seq"]
        rs = [r for r in rows if r["resolution_seq"] == seq]
        des = [r for r in rs if r["chart_kind"] == "designation"]
        org = [r for r in des if not r["agency_side"]]
        re_rows.append(dict(
            resolution_seq=seq, resolution_number=res["number"], resolution_date=res["date"],
            printed_date=res["printed_date"], legistar_id=res.get("legistar_id", ""), source_pdf=res["pdf"],
            pdf_sha256=x["sha"], pages=x["npages"],
            chart_pages=sum(1 for p in page_info if p["resolution_seq"] == seq and p["tables"]),
            charts=sum(1 for c in charts if c["resolution_seq"] == seq),
            charts_printed=res["charts_printed"] or "",
            budget_years=" ".join(f"{y}:{sum(1 for r in rs if r['budget_fiscal_year'] == y)}"
                                  for y in sorted({r["budget_fiscal_year"] for r in rs if r["budget_fiscal_year"]})),
            rows=len(rs), designation_rows=len(des),
            org_designations=sum(1 for r in org if r["amount"] > 0),
            org_designations_sum=sum(r["amount"] for r in org if r["amount"] > 0),
            org_rescissions=sum(1 for r in org if r["amount"] < 0),
            org_rescissions_sum=sum(r["amount"] for r in org if r["amount"] < 0),
            agency_side_rows=sum(1 for r in des if r["agency_side"]),
            agency_side_net=sum(r["amount"] for r in des if r["agency_side"]),
            net_all_rows=sum(r["amount"] for r in des),
            purpose_rows=sum(1 for r in rs if r["chart_kind"] == "purpose_of_funds"),
            speaker_rows=sum(1 for r in rs if r["member"] == "Speaker"),
            flagged_rows=sum(1 for r in rs if r["flags"]),
            review_items=sum(1 for o in rv if str(o["resolution_seq"]) == str(seq))))
    write_csv(os.path.join(outdir, f"{yy}_tr_resolutions.csv"), re_rows, list(re_rows[0]))

    pg_rows = []
    for p in page_info:
        pr = dict(p)
        pr.update(cv_pages.get((p["resolution_seq"], p["pdf_page"]), {}))
        vp = next(x for x in R if x["res"]["seq"] == p["resolution_seq"])["pages"][p["pdf_page"] - 1]
        pr.update(ein_tokens=vp["ein_tokens"], ein_tokens_all_chars=vp["ein_tokens_all_chars"],
                  nonws_chars=vp["nonws_chars"], clipped_chars=vp["clipped_chars"],
                  zero_width_chars=vp["zero_width_chars"])
        pg_rows.append(pr)
    write_csv(os.path.join(outdir, f"{yy}_tr_pages.csv"), pg_rows,
              ["resolution_seq", "pdf_page", "width", "height", "rotation", "tables", "chart_number",
               "continued", "page_label", "footnotes", "rows", "ein_tokens", "ein_tokens_all_chars",
               "nonws_chars", "clipped_chars", "zero_width_chars", "image_regions",
               "image_lattices", "image_rows", "rows_agree", "image_notes", "ink_px",
               "uncovered_px", "ink_regions", "caption"])

    flag_rows = sorted(sflags + chk_flags + cv_flags,
                       key=lambda f: (f["severity"], f["check_id"], f["resolution_seq"], f["pdf_page"]))
    for r in rows:
        for fl in r["row_flags"]:
            flag_rows.append(dict(severity="warn", check_id="row_flag", resolution_seq=r["resolution_seq"],
                                  pdf_page=r["pdf_page"], row_id=r["row_id"], field=fl, message=fl))
    write_csv(os.path.join(outdir, f"{yy}_tr_flags.csv"), flag_rows,
              ["severity", "check_id", "resolution_seq", "pdf_page", "row_id", "field", "message"])

    dm = [dict(row_id=r["row_id"], resolution_seq=r["resolution_seq"], pdf_page=r["pdf_page"],
               budget_fiscal_year=r["budget_fiscal_year"], action=r["action"], ein=r["ein"],
               amount=r["amount"], org=r["org"], status=r["disclosure_status"],
               reason=r["disclosure_reason"], disclosure_row=r["disclosure_row"])
          for r in rows if r["disclosure_status"] != "n/a"]
    write_csv(os.path.join(outdir, f"{yy}_tr_disclosure_match.csv"), dm, list(dm[0]))
    old = old or dict(only_new=[], only_old=[])
    old_rows = [dict(side="new_only", resolution_seq=r["resolution_seq"], row_id=r["row_id"],
                     ein=r["ein"], ein_printed=r["ein_printed"], amount=r["amount"], org=r["org"])
                for r in old["only_new"]] + \
               [dict(side="retired_only", resolution_seq=r["resolution"], row_id="", ein=r["ein"],
                     ein_printed="", amount=r["amount"], org=r["organization"]) for r in old["only_old"]]
    write_csv(os.path.join(outdir, f"{yy}_tr_retired_csv_compare.csv"), old_rows,
              ["side", "resolution_seq", "row_id", "ein", "ein_printed", "amount", "org"])

    # checks.txt
    L = []
    w = L.append
    w(f"TRANSPARENCY RESOLUTIONS FY{a.fy} -- checks (code/parse_transparency_v2.py; config {cfg['_path']})")
    w(f"{len(R)} PDFs, {sum(x['npages'] for x in R)} pages, "
      f"{sum(1 for p in page_info if p['tables'])} chart pages, {len(charts)} charts")
    w("")
    w(f"rows: {len(rows):,}")
    for kind in ("designate", "rescind", "purpose_from", "purpose_to"):
        rs = [r for r in rows if r["action"] == kind]
        w(f"  {kind:<13} {len(rs):>6,} rows  ${sum(r['amount'] or 0 for r in rs):>16,}")
    if any(r["action"] == "listed" for r in rows):      # FY2022 "Beating Hearts": no amount
        w(f"  {'listed':<13} {sum(1 for r in rows if r['action'] == 'listed'):>6,} rows  (no amount printed)")
    for y in sorted({r["budget_fiscal_year"] for r in rows if r["budget_fiscal_year"]}):
        rs = [r for r in rows if r["budget_fiscal_year"] == y]
        w(f"  budget year {y}: {len(rs):,} rows")
    w(f"  no budget year printed: {sum(1 for r in rows if not r['budget_fiscal_year'])} rows")
    w("")
    w("PER RESOLUTION (rows; organizations: designations / rescissions; agency side net; purpose rows)")
    for x in re_rows:
        w(f"  {x['resolution_seq']:>2} {x['resolution_number']} {x['resolution_date']}: "
          f"{x['rows']:>5,} rows, {x['charts']} charts"
          f"{' (prints ' + str(x['charts_printed']) + ')' if x['charts_printed'] else ''}; "
          f"+{x['org_designations']:,} ${x['org_designations_sum']:,} / "
          f"{x['org_rescissions']:,} ${x['org_rescissions_sum']:,}; agency side "
          f"${x['agency_side_net']:,}; purpose {x['purpose_rows']}")
    w("")
    w("HARD CHECKS")
    for c in chk_res:
        w(f"  {c['status']:<5} {c['check_id']:<20} {c['detail']}")
    w("")
    if a.no_cv:
        w("IMAGE LATTICE / INK: not run (--no-cv)")
    else:
        sc = Counter(r["status"] for r in cv_rows.values())
        w("IMAGE LATTICE (H8): rows rebuilt from code/ocr/grid.py lattices, compared field by field")
        w(f"  agree on every field: {sc.get('agree', 0):,} of {len(rows):,}")
        for k in sorted(sc):
            if k != "agree":
                w(f"  {k}: {sc[k]}")
        w(f"  image rows with no vector row: {sum(1 for f in cv_flags if f['check_id'] == 'H8.image_only_row')}")
        w(f"  header rules found in header pixels (not in the lattice): "
          f"{sum(1 for p in cv_pages.values() if p['image_notes'])} pages")
        w("INK COVERAGE (H9): uncovered-ink regions inside the chart tables")
        w(f"  regions: {sum(1 for f in cv_flags if f['check_id'] == 'H9.ink')}  "
          f"uncovered px total: {sum(p['uncovered_px'] for p in cv_pages.values()):,} of "
          f"{sum(p['ink_px'] for p in cv_pages.values()):,} ink px")
        if acc:
            w(f"  acceptance on Reso {acc['seq']:02d} p.{acc['page']} ({acc['row_id']}): clean run "
              f"{acc['clean']} regions; row withheld -> {acc['row_withheld']}; one char withheld -> "
              f"{acc['char_withheld']} ({'PASS' if acc['clean'] == 0 and acc['row_withheld'] and acc['char_withheld'] else 'FAIL'})")
    w("")
    w("DISCLOSURE (report-only; data/fyNN/expense_disclosure)")
    for y, s in sorted(D["summary"].items()):
        if not s.get("disclosure_rows"):
            w(f"  budget year {y}: no disclosure file in data/")
            continue
        rs = [r for r in rows if r["budget_fiscal_year"] == y and r["disclosure_status"] in ("matched", "unmatched")]
        reasons = Counter(r["disclosure_reason"] for r in rs if r["disclosure_status"] == "unmatched")
        w(f"  budget year {y}: {s['positive_rows']:,} organization designations; "
          f"{s['matched']:,} found in the disclosure on (EIN, amount) "
          f"(${sum(r['amount'] for r in rs if r['disclosure_status'] == 'matched'):,}); not found: "
          + ", ".join(f"{k} {v}" for k, v in sorted(reasons.items())))
    resc = [r for r in rows if r["disclosure_status"] == "rescission"]
    w(f"  rescissions of organizations: {len(resc):,}; where the money was designated before: " +
      ", ".join(f"{k} {v}" for k, v in sorted(Counter(r["disclosure_reason"] for r in resc).items())))
    w("")
    if "old_rows" not in old:
        w(f"RETIRED CSV: none ({disclosure.retired_path(a.fy)} does not exist)")
    else:
        w(f"RETIRED CSV ({disclosure.retired_path(a.fy)}, old parser)")
        w(f"  retired rows {old['old_rows']:,}; these rows {old['new_rows']:,}; same (resolution, EIN, "
          f"amount) {old['matched']:,}; only here {len(old['only_new'])} "
          "(EIN printed: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(
              r['ein_format'] for r in old['only_new']).items())) +
          f"); only in the retired file {len(old['only_old'])}")
    w("")
    rw = Counter(fl.split(":")[0] for r in rows for fl in r["row_flags"])
    w("ROW FLAG COUNTS (all listed in flags.csv; review file holds only those that could change a value)")
    w("  " + ", ".join(f"{k} {v}" for k, v in sorted(rw.items())))
    w(f"  zero-width chars dropped: {sum(p['zero_width_chars'] for x in R for p in x['pages'])}")
    w("")
    sv = Counter(o["severity"] for o in rv)
    w(f"REVIEW FILE: {len(rv)} rows ({sv.get('critical', 0)} critical, {sv.get('warn', 0)} warn); "
      f"stale decisions: {len(stale)}")
    open(os.path.join(outdir, f"{yy}_tr_checks.txt"), "w").write("\n".join(L) + "\n")

    import pdfplumber
    import pypdfium2
    man = dict(fiscal_year=a.fy, config=cfg["_path"], config_sha256=cfg["_sha256"],
               pdfs={x["res"]["pdf"]: x["sha"] for x in R}, python=sys.version.split()[0],
               pdfplumber=pdfplumber.__version__, pypdfium2=str(pypdfium2.version.PYPDFIUM_INFO),
               pdfium=str(pypdfium2.version.PDFIUM_INFO))
    try:
        import cv2
        import numpy
        man.update(opencv=cv2.__version__, numpy=numpy.__version__)
    except ImportError:
        pass
    json.dump(man, open(os.path.join(outdir, f"{yy}_tr_manifest.json"), "w"), indent=2, sort_keys=True)
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
