# Hand-labelled ground truth — FY2009 OCR pipeline

One CSV per labelled page. `test_parse_transparency_reso_fy09.py` renders that page, runs
the pipeline over it, and asserts that **every EIN and every amount here is recovered
exactly**. Text fields (organization, member) are reported but not asserted — OCR text
accuracy is a quality metric, dollar accuracy is a correctness requirement.

Columns:

```
source_pdf,page,row,member,organization,ein,amount
```

- `source_pdf` — repo-relative path, e.g. `source/FY09/transparency-resolutions/Transparency-Reso-01-2008-08-14.pdf`
- `page` — 1-based PDF page number
- `ein` — 9 digits, no hyphen (matching the emitted schema)
- `amount` — signed whole dollars; negative for a rescission

Three pages are worth labelling, chosen to cover the layout variety:

| page | why |
|---|---|
| `Transparency-Reso-01-2008-08-14.pdf` p.9 | dense ~40-row `CHART 1: Local Initiatives`, long column shape, rotated one way, prints a `$0.00` net-zero total |
| `Transparency-Reso-01-2008-08-14.pdf` p.12 | small `Chart 4: Veterans Resource Center`, short column shape, prints a `$500,000.00` total, rotated the *other* way |
| `Transparency-Reso-07-2009-04-22.pdf` p.20 | `CHART 3: Youth Discretionary` with populated Fiscal Conduit / Status columns |

Label them by hand from the page images (`build/ocr/<stem>/upright/page-NNN.png` after
`--stage orient`), not from the pipeline's own output — truth derived from the thing under
test proves nothing.
