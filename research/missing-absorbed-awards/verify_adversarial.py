"""Adversarial re-verification of the four absorbed-award investigations.

Re-derives every load-bearing number independently: extraction, disclosure AND
transparency-resolution corroboration, initiative-level reconciliation, the permutation
null, and the double-count check. Read-only. Stdlib only (no pandas, no openpyxl).

    python3 research/missing-absorbed-awards/verify_adversarial.py
    python3 research/missing-absorbed-awards/verify_adversarial.py --selfcheck
"""
import csv, glob, os, re, sys, zipfile, collections, random
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# ---------------------------------------------------------------- xlsx (cell-reference aware)
def _col(ref):
    m = re.match(r"([A-Z]+)", ref)
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _shared(z):
    out, buf, depth = [], [], 0
    try:
        f = z.open("xl/sharedStrings.xml")
    except KeyError:
        return out
    for ev, el in ET.iterparse(f, events=("start", "end")):
        if ev == "start" and el.tag == NS + "si":
            buf, depth = [], 1
        elif ev == "end" and el.tag == NS + "t" and depth:
            buf.append(el.text or "")
        elif ev == "end" and el.tag == NS + "si":
            out.append("".join(buf)); depth = 0; el.clear()
    return out


def xlsx_table(path):
    """Rows as dicts. Keyed on each cell's `r` reference, so Excel's omitted empty cells
    cannot shift later columns left -- the defect in code/recover_org_names.py."""
    z = zipfile.ZipFile(path)
    ss = _shared(z)
    sheets = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))
    hdr, out, row = None, [], {}
    for ev, el in ET.iterparse(z.open(sheets[0]), events=("end",)):
        if el.tag == NS + "c":
            t, v, ise = el.get("t"), el.find(NS + "v"), el.find(NS + "is")
            if t == "inlineStr" and ise is not None:
                val = "".join(x.text or "" for x in ise.iter(NS + "t"))
            elif v is None:
                val = ""
            elif t == "s":
                val = ss[int(v.text)] if v.text and int(v.text) < len(ss) else ""
            else:
                val = v.text or ""
            row[_col(el.get("r") or "A1")] = val
            el.clear()
        elif el.tag == NS + "row":
            vals = [row.get(i, "") for i in range(max(row) + 1)] if row else []
            if hdr is None:
                if sum(1 for v in vals if v.strip()) >= 4:
                    hdr = [v.strip() for v in vals]
            elif any(v.strip() for v in vals):
                out.append({(hdr[i] if i < len(hdr) else f"_{i}"): (vals[i] if i < len(vals) else "")
                            for i in range(max(len(hdr), len(vals)))})
            row = {}; el.clear()
    return hdr, out


# ---------------------------------------------------------------- extraction
# The advisory's own test (validate_data.py:353). Note it only sees HYPHENATED EINs.
FLAG_EIN = re.compile(r"\d{2}-\d{7}")
# What actually appears in the merged text: hyphenated OR bare 9-digit.
EIN_ANY = re.compile(r"(?<![\d-])(\d{2}-\d{7}|\d{9})(?![\d-])")
AMT = re.compile(r"\$\s?([\d,]+(?:\.\d{1,2})?)")


def extract(org):
    """(name, ein9, amount) per absorbed award. Walks EINs in order; each amount search is
    bounded by the NEXT EIN, so an EIN can never claim a later award's amount."""
    out, ms, prev = [], list(EIN_ANY.finditer(org)), 0
    for k, m in enumerate(ms):
        nxt = ms[k + 1].start() if k + 1 < len(ms) else len(org)
        am = AMT.search(org[m.end():nxt])
        name = org[prev:m.start()].strip(" *,-")
        ein = m.group(1).replace("-", "")
        if am:
            out.append((name, ein, int(round(float(am.group(1).replace(",", ""))))))
            prev = m.end() + am.end()
        else:
            out.append((name, ein, None)); prev = m.end()
    return out


def selfcheck():
    T = [
        ("Bridge Street Development Corporation 11-3250772 * $29,729 Brighton Neighborhood Association, Inc.",
         [("Bridge Street Development Corporation", "113250772", 29729)]),
        ("Housing Conservation Coordinators, Inc. 51-0141489 * $29,730 Housing Court Answers, Inc. 13-3317188 * $29,730 Hudson Guild",
         [("Housing Conservation Coordinators, Inc.", "510141489", 29730),
          ("Housing Court Answers, Inc.", "133317188", 29730)]),
        # BARE 9-digit EIN: real absorbed awards the hyphen-only advisory never sees
        ("Centro Altagracia de Fe y Justicia 161765323 * $52,692 Community Health Center of Richmond 510567466 * $52,692 X",
         [("Centro Altagracia de Fe y Justicia", "161765323", 52692),
          ("Community Health Center of Richmond", "510567466", 52692)]),
        ("Asian Community United Society Inc. 264164117 * $10,000.00 To cover",
         [("Asian Community United Society Inc.", "264164117", 10000)]),
        # window bound: an EIN with no amount must NOT steal the next award's
        ("Alpha 11-1111111 Beta 22-2222222 * $500 Gamma",
         [("Alpha", "111111111", None), ("Beta", "222222222", 500)]),
        ("The funds requested will subsidize the delivery of farm shares to $12 per share", []),
        ("Org 1234567890123 $5,000 X", []),
        ("East Flatbush Village, Inc. 80-0612019 Meyer Levin High School $18,000 Next Org",
         [("East Flatbush Village, Inc.", "800612019", 18000)]),
        # malformed 10-digit EIN is unrecoverable, must yield nothing
        ("Urban Health Plan, Inc. 15-24042810 $88,855 West Brighton", []),
    ]
    for s, want in T:
        got = extract(s)
        assert got == want, f"\n IN {s!r}\n GOT {got}\n WANT {want}"
    print(f"selfcheck: {len(T)}/{len(T)} pass")


def population():
    """The 303 rows the org_merged advisory flags, with their absorbed triples."""
    tri = []
    for f in sorted(glob.glob("data/fy*/schedule_c/*.csv")):
        b = os.path.basename(f)
        if "initiatives" in b:
            continue
        fy = 2000 + int(b[2:4])
        with open(f, newline="", encoding="utf-8") as fh:
            rd = csv.DictReader(fh)
            if "organization" not in (rd.fieldnames or []):
                continue
            for i, r in enumerate(rd, start=2):
                org = r.get("organization") or ""
                if not (FLAG_EIN.search(org) or "$" in org):
                    continue
                for nm, e, a in extract(org):
                    tri.append(dict(fy=fy, file=b, line=i, name=nm, ein=e, amount=a,
                                    init=r.get("initiative", "")))
    return tri


def ni(s):
    s = (s or "").lower().replace("’", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s)).strip()


# ---------------------------------------------------------------- report
def main():
    tri = population()
    good = [t for t in tri if t["amount"] is not None]
    rows = len({(t["file"], t["line"]) for t in tri})
    print(f"\n[1] EXTRACTION   flagged rows={rows}  triples={len(tri)}  "
          f"with amount={len(good)}  ${sum(t['amount'] for t in good):,}")
    keys = collections.Counter((t["fy"], t["ein"], t["amount"]) for t in good)
    print(f"    dedup by (fy,ein,amount) would DROP {len(good)-len(keys)} REAL awards "
          f"(e.g. fy17:27, 3 members x $20,000 to PowerMyLearning)")

    # ---- corroboration: disclosure AND transparency resolutions
    disc = {}
    for fy in (2016, 2017, 2018, 2019):
        _, rs = xlsx_table(f"source/expense-funding-disclosure/funded_disclosure_FY{fy}.xlsx")
        s = set()
        for r in rs:
            e = re.sub(r"\D", "", r.get("EIN", "") or "")
            a = (r.get("Amount", "") or "").strip().replace(",", "")
            if len(e) == 9 and a:
                try: s.add((e, int(round(float(a)))))
                except ValueError: pass
        disc[fy] = s
    trans = collections.defaultdict(set)
    for f in glob.glob("data/fy*/transparency-resolutions/fy*_transparency_all.csv"):
        fy = 2000 + int(re.search(r"fy(\d\d)", os.path.basename(f)).group(1))
        for r in csv.DictReader(open(f, newline="", encoding="utf-8")):
            e = re.sub(r"\D", "", r.get("ein") or "")
            try: a = int(r.get("amount") or 0)
            except ValueError: continue
            if len(e) == 9 and a > 0:
                trans[fy].add((e, a))
    st = collections.Counter()
    for t in good:
        k = (t["ein"], t["amount"])
        d, r = k in disc.get(t["fy"], set()), k in trans.get(t["fy"], set())
        st["corroborated" if (d or r) else "NEITHER"] += 1
        st["disclosure"] += d; st["transparency"] += r
    print(f"\n[2] CORROBORATION (same fiscal year, independent sources)")
    print(f"    Council disclosure workbook : {st['disclosure']:>4}/{len(good)} ({100*st['disclosure']/len(good):.1f}%)")
    print(f"    transparency resolutions    : {st['transparency']:>4}/{len(good)} ({100*st['transparency']/len(good):.1f}%)")
    print(f"    >=1 SOURCE                  : {st['corroborated']:>4}/{len(good)} ({100*st['corroborated']/len(good):.1f}%)")

    # ---- initiative-level reconciliation
    printed, awards = collections.defaultdict(dict), collections.defaultdict(collections.Counter)
    for fy in range(2015, 2028):
        t = str(fy)[2:]
        p = f"data/fy{t}/schedule_c/fy{t}_schedule_c_initiatives.csv"
        if os.path.exists(p):
            for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
                k = ni(r["initiative"])
                if k: printed[fy][k] = printed[fy].get(k, 0) + int(r["amount"])
        a = f"data/fy{t}/schedule_c/fy{t}_schedule_c_awards.csv"
        if os.path.exists(a):
            for r in csv.DictReader(open(a, newline="", encoding="utf-8")):
                k = ni(r.get("initiative"))
                if k and (r.get("amount") or "").strip():
                    awards[fy][k] += int(r["amount"])
    absorbed = collections.defaultdict(collections.Counter)
    for t in good:
        if "appendix" in t["file"]:
            continue
        k = ni(t["init"])
        if k: absorbed[t["fy"]][k] += t["amount"]

    cells, vals, closures, overs = [], [], 0, []
    for fy in printed:
        for k, v in absorbed[fy].items():
            if k in printed[fy] and k in awards[fy]:
                cells.append((fy, k)); vals.append(v)
                d = printed[fy][k] - awards[fy][k]
                if d - v == 0 and d != 0: closures += 1
                if d >= 0 > d - v: overs.append((fy, k, v - d))
    print(f"\n[3] RECONCILIATION (award rows vs printed INITIATIVE amount)")
    print(f"    joined initiatives carrying >=1 absorbed award: {len(cells)}")
    print(f"    gaps closed to EXACTLY $0 by the recovery     : {closures}")
    print(f"    apparent OVERSHOOTS                           : {len(overs)}")
    for fy, k, x in overs:
        print(f"        FY{fy} {k[:44]:<44} over by ${x:,}")

    random.seed(7)
    ge = tot = 0
    for _ in range(20000):
        sh = vals[:]; random.shuffle(sh)
        c = sum(1 for (fy, k), v in zip(cells, sh)
                if printed[fy][k] - awards[fy][k] - v == 0 and printed[fy][k] != awards[fy][k])
        tot += c; ge += c >= closures
    print(f"    permutation null (20k shuffles, seed 7): mean={tot/20000:.2f}  "
          f"P(null>=observed)={ge/20000:.5f}")

    # ---- double-count: does an absorbed award already have a row in the SAME stream + year?
    idx = collections.defaultdict(list)
    for f in glob.glob("data/fy*/schedule_c/*.csv"):
        b = os.path.basename(f)
        if "initiatives" in b: continue
        fy = 2000 + int(b[2:4])
        with open(f, newline="", encoding="utf-8") as fh:
            rd = csv.DictReader(fh)
            if "ein" not in (rd.fieldnames or []): continue
            for i, r in enumerate(rd, start=2):
                e = re.sub(r"\D", "", r.get("ein") or "")
                a = (r.get("amount") or "").strip()
                if len(e) == 9 and a:
                    try: idx[(fy, e, int(a))].append((b, i))
                    except ValueError: pass
    col = [(t, h) for t in good
           for h in [[x for x in idx.get((t["fy"], t["ein"], t["amount"]), [])
                      if x != (t["file"], t["line"])]] if h]
    print(f"\n[4] DOUBLE-COUNT   exact (fy,ein,amount) collisions within Schedule C: {len(col)}")
    for t, h in col:
        print(f"        FY{t['fy']} ein={t['ein']} ${t['amount']:,}  {t['file']}:{t['line']} -> {h}")


if __name__ == "__main__":
    selfcheck()
    if "--selfcheck" not in sys.argv:
        main()
