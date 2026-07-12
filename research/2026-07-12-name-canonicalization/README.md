# Name canonicalization — decision provenance

How the editorial `initiative_canonical` and `category_canonical` merges (see [`DATA-ANOMALIES.md`](../../DATA-ANOMALIES.md) #17–#18) were decided. Open the HTML files in a browser.

- `collision-matrix.html` — every name collision, toggle initiatives ⇄ categories.
- `org-continuity.html` — the "same funded organizations?" test (shared EINs) behind each category merge.
- `exhaustive-map.html` — all 96 category labels routed backward into the FY2027 anchor set.
- `leaf-duplicate-review.html` — the leaf-duplicate review (Formerly / suffix / acronym / ATI classes).
- `report.md` — narrative summary of the initiative-name collisions.

Regenerate the underlying scans with [`code/analyze_initiative_names.py`](../../code/analyze_initiative_names.py) and [`code/analyze_categories.py`](../../code/analyze_categories.py). The decisions themselves live in the committed `data/combined/*_name_crosswalk.csv`.
