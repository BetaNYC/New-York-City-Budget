# NYC Open Data `4d7f-74pe` vs the Council's disclosure workbooks

**Report generated:** 2026-10-14 (office) · **Data current as of:** Open Data pulled 2026-10-14
06:53–06:55 ET (publisher last updated it 2021-04-20); our dataset is the 2026-10-12 re-pull of
rnd.council.nyc.gov; FY2009–FY2012 Council workbooks from the Internet Archive (captures of
2025-02-12, content-identical to 2014–2016 captures). · Issue: #85 (epic #89); FY2009–FY2012 half
of #86.

Code: `code/fetch_open_data_4d7f74pe.py`, `code/diff_open_data_disclosure.py` (tests:
`code/test_diff_open_data_disclosure.py`). Outputs in
[`2026-10-14-open-data-diff/`](2026-10-14-open-data-diff/): `summary.csv`, `unmatched-rows.csv`
(every row left unmatched, both sides), `field-differences.csv`, `open-data-profile.csv`.
Follow-up questions: [`2026-10-14-follow-up-questions-85-86.md`](2026-10-14-follow-up-questions-85-86.md).
A sample of 20 nominations for a person to check by eye (#89 B12):
[`2026-10-14-open-data-diff/REVIEW-SHEET.md`](2026-10-14-open-data-diff/REVIEW-SHEET.md).

**Terminology.** The portal calls these rows "applications for discretionary funding". They are
designations, the same rows as the Council's disclosure workbooks. The Council's real
application files are a different data class (`2026-10-14-wayback-council-files.md`).

Reproduce:

```
python3 code/diff_open_data_disclosure.py --open-data <cache>/4d7f-74pe.csv \
  --workbook 2009=source/wayback-council/files/20250212200136/funded_disclosure_FY2009.xls \
  --workbook 2010=source/wayback-council/files/20250212200137/funded_disclosure_FY2010.xls \
  --workbook 2011=source/wayback-council/files/20250212200134/funded_disclosure_FY2011.xls \
  --workbook 2012=source/wayback-council/files/20250212200132/funded_disclosure_FY2012.xls \
  --out-dir research/2026-10-14-open-data-diff
```

## The short version

1. **Open Data is the Council's own disclosure data, frozen at a later clearance state.** In
   FY2014–FY2016 and FY2019–FY2020, **every** row matches one-for-one once Open Data's amount
   rounding is allowed for. In FY2016 every row matches exactly.
2. **Open Data rounds amounts.** The dictionary types Amount as `integer`. FY2012 onward are
   rounded half-up to whole dollars (5,437.50 → 5,438; 6,333.33 → 6,333); FY2009–FY2011 to cents.
   That alone accounts for 958 rows that an exact match would leave unmatched. Our dataset keeps the published cents.
3. **Open Data lost leading zeros on 1,600 EINs** (FY2009–FY2018 only; EIN is typed `integer`).
   Padded back to 9 digits for matching; the raw value is kept.
4. **FY2013 (+1,294) is two things:** the Council's FY2013 workbook carries 18 citywide
   initiatives as **one lump row each**, which Open Data itemizes into **1,168** grantee rows
   (+1,150). The other **+144** are designations added after the Council's workbook was frozen.
   That workbook is an early snapshot: 53% of its rows (and $380.7M of $398.9M) are still
   Pending. Open Data's FY2013 is 92% Cleared.
5. **FY2021 (−41):** our file (sheet dated 2023-06-23) is two years later than Open Data
   (2021-04-20). 194 rows on our side and 153 on Open Data's do not match. Of those pairs,
   47 are re-designations (same member, source, agency and amount, different grantee) and 9
   are amount changes. The rest look like adds and drops. Our unmatched side includes **18 Food
   Pantries rows worth $16.0M** (when they were added is not recorded anywhere). Year total: Open Data $376.3M vs ours $393.3M.
6. **FY2017 and FY2018 (−1 each)** are re-allocations, not a missing row. FY2018 comes down to a
   **$221** DFTA row only we have, and one $5,000 St. Andrew Avellino designation that moved from
   Aging/DFTA to Youth/DYCD. In FY2017, 9 rows remain after 8 nominated re-allocations, with no
   single culprit.
7. **MOCS ID matching is not possible for FY2009–FY2021.** Open Data has a MOCS ID on every row
   (`FY09 5052`; unique except two `FY09 Not an Award` rows and one repeated `FY09 2039`). The
   Council workbooks have no MOCS ID column before FY2024. Open Data's IDs are therefore the
   **only** MOCS IDs that exist for those years.
8. **FY2009–FY2012 (candidate new years):** FY2009 and FY2011 agree with the Council's own
   workbooks after rounding (4/4 and 8/9 rows left). FY2012 agrees except for 155 $0 "CBO
   Defunded" rows that Open Data dropped. **FY2010 does not:** the Council workbook has 2,592
   rows ($111.6M) where Open Data has 5,981 ($357.8M). Both archived copies of that workbook
   (2016 and 2025) are identical, so Open Data is the only complete FY2010 source found.

## Method

- **Pull:** 20 SODA pages of 5,000 rows, `$order=:id`, 2.5 s apart, count checked against
  `count(*)` (97,002) and `:id` uniqueness. Manifest: `source/open-data-4d7f-74pe/MANIFEST.csv`.
- **Normalization, both sides:** text via the parser's `_clean` (invisible characters, soft
  hyphen, whitespace); EIN via `clean_ein` (hyphen removed); Open Data 8-digit EINs padded
  (counted as `ein_padded_open_data`); `status_norm` cleared / pending / other with the raw
  value kept; amounts as `Decimal` of the shortest round-trip repr.
- **Matching tiers (per fiscal year):**
  1. `(EIN, amount)` as a **multiset**: a pair printed twice is two rows. Never EIN alone, never
     member.
  2. **After rounding:** what is left, with our amount rounded half-up to cents, then to whole
     dollars, against Open Data's amount. Reported separately, never folded into tier 1.
  3. **Nominations, not matches:** same EIN and name, different amount (`amount_differs`); same
     name and amount, different EIN (`ein_differs`); same slot (amount, source, agency,
     member) and a different organization (`grantee_differs`, i.e. likely re-designated).
     Nominated rows stay in the unmatched counts.
- **Field differences** only on unambiguous pairs, where `(EIN, amount)` occurs once on each
  side.

## Per year

| FY | Open Data rows | Council rows | Δ | exact | after rounding | nominated (amt / EIN / grantee) | left unmatched OD / Council | total OD | total Council |
|---|---:|---:|---:|---:|---:|---|---|---:|---:|
| 2009 ‡ | 5,745 | 5,745 | 0 | 5,258 | 483 | 0 / 3 / 0 | 4 / 4 | 414,226,178 | 414,226,177 |
| 2010 ‡ | 5,981 | 2,592 | +3,389 | 2,107 | 82 | 98 / 7 / 35 | 3,792 / 403 | 357,820,611 | 111,558,053 |
| 2011 ‡ | 5,419 | 5,420 | −1 | 5,382 | 29 | 1 / 4 / 2 | 8 / 9 | 395,907,487 | 395,907,487 |
| 2012 ‡ | 5,671 | 5,823 | −152 | 5,546 | 85 | 0 / 19 / 6 | 40 / 192 | 386,823,783 | 386,832,782 |
| 2013 | 6,281 | 4,987 | +1,294 | 4,682 | 54 | 89 / 28 / 49 | 1,545 / 251 | 412,148,910 | 398,882,402 |
| 2014 | 6,611 | 6,611 | 0 | 6,538 | 72 | 0 / 0 / 1 | 1 / 1 | 393,733,475 | 393,733,477 |
| 2015 | 6,650 | 6,650 | 0 | 6,503 | 146 | 0 / 1 / 0 | 1 / 1 | 286,731,849 | 286,731,856 |
| 2016 | 7,797 | 7,797 | 0 | 7,797 | 0 | 0 / 0 / 0 | 0 / 0 | 381,376,626 | 381,376,626 |
| 2017 | 8,670 | 8,671 | −1 | 8,653 | 5 | 2 / 1 / 5 | 12 / 13 | 353,501,925 | 353,501,886 |
| 2018 | 8,893 | 8,894 | −1 | 8,878 | 0 | 0 / 3 / 11 | 15 / 16 | 381,899,779 | 381,900,000 |
| 2019 | 9,655 | 9,655 | 0 | 9,653 | 2 | 0 / 0 / 0 | 0 / 0 | 392,945,001 | 392,945,000 |
| 2020 | 10,616 | 10,616 | 0 | 10,608 | 0 | 0 / 0 / 4 | 8 / 8 | 457,216,702 | 457,216,702 |
| 2021 | 9,013 | 9,054 | −41 | 8,860 | 0 | 9 / 0 / 47 | 153 / 194 | 376,280,506 | 393,250,506 |

‡ Council side = the Council's own workbook from the Internet Archive (#86), not our dataset.
Totals in whole dollars here; exact values in `summary.csv`.

The single rows left in FY2014 and FY2015 are a grantee change (FY2014: Speaker's $25,000 to
"WNET" in Open Data, "Thirteen" with another EIN in ours) and an EIN blank in Open Data that our
file fills (FY2015, St. Catherine of Genoa food pantry, $7,218.75).

## Totals by status

Open Data's statuses are a **later** state than the Council workbooks for FY2009–FY2013, and an
**earlier** one than our re-pull for FY2017–FY2021.

| FY | Open Data | Council side |
|---|---|---|
| 2009 | Cleared 5,721 · Pending 24 | Cleared 4,356 · Pending 1,389 |
| 2010 | Cleared 5,839 · Pending 142 | Cleared 1,048 · Pending 1,544 |
| 2011 | Cleared 5,091 · Pending 328 | Cleared 4,894 · Pending 387 · Government 136 ($2.6M) · Pending FC Clearance 3 |
| 2012 | Cleared 5,566 · Pending 105 | Cleared 5,482 · Pending 137 · **Government 49 ($235.2M)** · **CBO Defunded 155 ($0)** |
| 2013 | Cleared 5,771 · **Government 311 ($123.2M)** · Pending 190 · Revoked 7 · Pending-Council 2 | Cleared 2,343 ($18.2M) · Pending 2,644 ($380.7M) |
| 2014–2016 | Cleared / Pending only | Cleared / Pending only, identical counts every year |
| 2017 | Pending 84 ($1.11M) | Pending 50 ($0.71M) |
| 2018 | Pending 80 ($1.05M) | Pending 51 ($0.51M); UPPERCASE in the workbook |
| 2020 | Pending 99 ($1.89M) | Pending 67 ($0.64M) |
| 2021 | Pending 170 ($4.94M) · **Designated 1** ($20,000, DCLA, CASA) | Pending 120 ($1.48M) |

Where the extra statuses would go: every one lands in `status_norm = other` and keeps its raw
value. "Government" marks a City agency as the recipient (309 of 311 FY2013 rows carry the City
EIN 136400434). In FY2012 the Council's workbook used it for $235.2M that Open Data reports as
"Cleared". "Revoked" (7 rows, $48,214) and "Pending-Council" (2 rows) exist only in FY2013;
"Designated" only once, in FY2021. Nothing defines any of them (the data dictionary is silent).

## Field differences on matched rows

Counts over unambiguous pairs (`field-differences.csv` has every year and field). Most
differences are spelling conventions, not changed facts:

- **council_member:** the Council workbooks use short forms, while Open Data spells them out:
  `CC` → `Speaker` (225 rows in FY2009), `Brooklyn`/`QN`/`MN` → `… Delegation`, `Viverito` →
  `Mark-Viverito`, `Vallone` → `Vallone, Jr`. Separately, **Open Data keeps the member of the
  time where our re-export shows the current roster**: FY2021 `Richards` → `Brooks-Powers`
  (60 rows), `Menchaca` → `Aviles` (48), `Torres` → `Feliz` (31).
- **source:** the Council abbreviates and Open Data expands: `IOI` → `Immigrant Opportunity
  Initiative (IOI)`, `CASA` → `Cultural After School Adventure (CASA)` (FY2009–FY2014).
- **status:** the clearance timing above, plus case (FY2018 `CLEARED` vs `Cleared`: 5,121 of
  5,144 pairs differ only in case).
- **legal_name:** small edits (`Project Hospitality` / `Project Hospitality, Inc.`). FY2017 has 85
  and FY2018 has 68.
- **address fields:** almost identical. The exception is FY2010: on 180 pairs the Council
  workbook's address is **blank** where Open Data has one (e.g. `2 Lyon Place, White Plains, NY
  10601`). Open Data filled addresses the Council's file never carried.
- **purpose:** edited text in FY2017 (288) and FY2018 (330).

## Open Data completeness and geocoding

From `open-data-profile.csv`. Geocoding covers 75,385 of 97,002 rows (77.7%), from 63.3% (FY2013)
to 91.5% (FY2011). BIN/BBL cover 74,820 rows, and 15 BBLs are literally `0` (FY2019 14,
FY2010 1). Since 2026-10-14 the normalizer reads a BBL of `0` as blank (`od_geo`, #89 B13), so
`open-data-profile.csv` counts them in `filled_bbl_zero_blanked`, not in `filled_bbl`. `council_district`
holds 51 distinct districts. The geocode is of the **grantee's mailing address** (the dictionary:
"the building's location"). It is not where services are delivered and not the sponsoring
member's district, so a `council_district` here says where the organization's office is. The
method (Geosupport version, match type) is not documented.

Mapping if adopted: `borough`, `latitude`, `longitude`, `community_board`, `council_district`,
`census_tract`, `bin`, `bbl`, `nta` would be new columns. We have no geocodes; our addresses carry
only a ZIP check (`zip`, `zip_status`). These columns would be Open Data's assertion, labeled as
such, and would exist only for FY2009–FY2021.

## FY2009–FY2012 as candidate new years

| FY | Open Data rows / $ | Council workbook rows / $ | Verdict |
|---|---|---|---|
| 2009 | 5,745 / 414.2M | 5,745 / 414.2M | Same rows; Open Data has later statuses and cents-rounded amounts |
| 2010 | 5,981 / 357.8M | 2,592 / 111.6M | **Council workbook incomplete.** Open Data is the only full source found |
| 2011 | 5,419 / 395.9M | 5,420 / 395.9M | Same rows bar re-allocations |
| 2012 | 5,671 / 386.8M | 5,823 / 386.8M | Same, except the Council keeps 155 $0 "CBO Defunded" rows |

Field shape: both sources carry the same 16 fields as our FY2013 file. There is no MOCS ID in the
workbooks and no Fiscal Year column, and the member is a short form. Open Data adds MOCS IDs and
geocodes.

## What this does not establish

- That Open Data's later statuses are correct. Neither source dates its statuses.
- What happened to an unmatched row. Nominations are leads for a person to check in the
  workbooks, not conclusions.
- Anything about FY2022 onward. Open Data stops at FY2021.
