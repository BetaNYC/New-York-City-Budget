#!/usr/bin/env python3
"""Sum the advisory counts data/QA-REPORT.md itself reports per file, so the branch's own
residue claim ("140 org_prose and 64 org_merged") can be checked against the branch's own
validator rather than against a differently-tuned detector."""
import collections
import re

TOT = collections.Counter()
ROWS = 0
with open("data/QA-REPORT.md", encoding="utf-8") as fh:
    for ln in fh:
        if not ln.startswith("| `"):
            continue
        name = re.match(r"\|\s*`([^`]+)`", ln).group(1)
        if name.startswith("combined/"):
            continue                       # roll-up of the per-year files; would double count
        if "/schedule_c/" not in name or "initiativ" in name or "reconcil" in name:
            continue
        m = re.search(r"\|\s*(\d+)\s*\|", ln)
        if m:
            ROWS += int(m.group(1))
        for kind in ("org_prose", "org_merged", "column_bleed", "duplicate"):
            mm = re.search(kind + r": (\d+)", ln)
            if mm:
                TOT[kind] += int(mm.group(1))

print("QA-REPORT.md, per-file advisories summed over data/fy*/schedule_c/ (combined excluded):")
for k, v in TOT.most_common():
    print(f"  {k:<14} {v}")
print(f"  rows accounted    {ROWS:,}")
