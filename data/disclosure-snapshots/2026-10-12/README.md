# Disclosure snapshot diff — 2026-07-15 → 2026-10-12

What moved in the Council's expense funding disclosure workbooks between the snapshot first
committed (retrieved 2026-07-15) and the re-pull of 2026-10-12. All 16 files were downloaded
again on 2026-10-12; FY2013–FY2024 came back byte-identical, so only these three years have a
report. (`Capital-Database.xlsx` also changed; no code reads it, see
`source/expense-funding-disclosure/README.md`.)

| Report | old sha256 (2026-07-15) | new sha256 (2026-10-12) | sheet, old → new |
|---|---|---|---|
| [FY2025-diff.md](FY2025-diff.md) | `b3c646dd4e2c` | `c6e543e77e40` | `FY25 (06-08-26)` → `FY25 (09-14-26)` |
| [FY2026-diff.md](FY2026-diff.md) | `4691c42bd3e7` | `81651e599ad6` | `FY26 (06-08-26)` → `FY26 (09-14-26)` |
| [FY2027-diff.md](FY2027-diff.md) | `d15f058a38ea` | `654a97d06f9d` | `FY27 (07-01-26)` → `FY27 (09-14-26)` |

Full hashes: `source/expense-funding-disclosure/MANIFEST.csv` (new) and `MANIFEST-HISTORY.csv`
(old). The old workbooks are in this repo's git history.

Produced by `code/diff_disclosure_snapshots.py OLD NEW --out …`, OLD being the workbook as
committed before the re-pull. These compare two files; they are not a statement by the Council
about what changed or why.

Headlines:

- **FY2025:** 11,280 → 11,276 rows (+8 / −12), one amount change (MOCS ID `FY25 11126`,
  $250,000 → $150,000), no status transitions; total unchanged at $595,181,182. 149 rows changed
  `council_member` from `Holden` to `Wong`.
- **FY2026:** 11,757 → 11,764 rows (+62 / −55), 19 Pending → Cleared, 29 amount changes; total
  unchanged at $716,213,155. 131 rows were re-numbered from `FY26 NNNNN` to `FY26GP NNNNN`;
  161 rows changed `council_member` from `Bottcher` to `Wilson` (2 of them also re-numbered).
  An earlier version of these reports keyed composite pairs on `council_member` too and showed
  those 2 as one removal plus one addition each (+64 / −57, 129); the member is never a key now. The workbook no longer carries
  its footer rows (`Master List Total` etc.).
- **FY2027:** 10,040 → 10,407 rows (+495 / −128), 3,608 Pending → Cleared and 84 Cleared →
  Pending, 72 amount changes; total $705,564,000 → $705,704,000. Cleared went from $143,034,722
  to $590,253,954.
