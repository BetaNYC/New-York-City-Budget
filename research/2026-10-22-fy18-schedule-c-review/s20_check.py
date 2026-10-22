"""DATA-ANOMALIES §20: each old merged row -> the awards in the new parse."""
import csv, re, sys
old, new, out = sys.argv[1], sys.argv[2], sys.argv[3]
rows = [r for r in csv.DictReader(open(old)) if re.search(r"\d{2}-\d{7}", r["organization"]) or "$" in r["organization"]]
aw = list(csv.DictReader(open(new)))
def find(ein, amt):
    # The printed EIN too, for one printed with the wrong length (clean EIN left blank).
    e = ein.replace("-", "")
    return [a for a in aw if e in (a["ein"], a["ein_printed"].replace("-", "")) and
            a["amount"] == str(amt)]
res = []
for i, r in enumerate(rows, 1):
    o = r["organization"]
    parts = [(m[0], m[1], m[3]) for m in re.findall(r"(.*?)\s+(\d{2}-\d{7,8})\s*(.*?)\s*\*?\s*\$([\d,]+)\s*", o)]
    rest = re.sub(r".*\$[\d,]+\s*", "", o)
    awards = [(p[0].strip(), p[1], int(p[2].replace(",", ""))) for p in parts] + [(rest.strip(), r["ein"], int(r["amount"] or 0))]
    for name, ein, amt in awards:
        hit = find(ein, amt)
        res.append(dict(s20_row=i, old_category=r.get("category", ""), old_initiative=r.get("initiative", ""), old_organization=o,
                        name=name, ein=ein.replace("-", ""), amount=amt, found=len(hit),
                        award_ids=";".join(a["award_id"] for a in hit),
                        new_org=" / ".join(sorted({a["org"] for a in hit}))))
w = csv.DictWriter(open(out, "w"), fieldnames=list(res[0]), lineterminator="\n")
w.writeheader(); w.writerows(res)
print(len(rows), "merged rows ->", len(res), "awards;", sum(1 for x in res if x["found"] >= 1), "found;", [ (x["s20_row"], x["name"], x["ein"], x["amount"]) for x in res if not x["found"]])
