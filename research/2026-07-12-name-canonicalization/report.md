---
title: "NYC Council Discretionary — Initiative-Name Collisions (longitudinal join breakage)"
created: 2026-07-11
type: review
status: draft
tags: [data-quality, civic-tech, open-data, review]
area: civic-tech
source: marvin
---

# NYC Council Discretionary Funding — Initiative-Name Collisions

**Report generated:** 2026-07-11
**Data current as of:** 2026-07-10 (repo HEAD e169b07)
**Source:** `BetaNYC/New-York-City-Budget` — `data/combined/all_years_initiatives.csv` (2,598 rows, 846 distinct raw initiative labels, FY09–FY27)
**Analysis script:** `scripts/analyze_initiative_names.py` (reproducible; emits `initiative_name_collisions.json`)

## The problem, in one sentence

The combined dataset has **no canonical initiative-name layer**, so the same initiative appears under two or more spellings across fiscal years. Any longitudinal join keyed on the raw `initiative` string fragments that initiative into multiple short-lived series — it looks funded one year and *gone* the next, when in reality the money continued under a differently-spelled label.

## What the scan found

| Tier | What it catches | Groups | Labels involved | $ spanned |
|---|---|---|---|---|
| **Mechanical** (high confidence) | Same label differing only by case, whitespace, `&`/`AND`, curly vs. straight apostrophe, a leading `*` marker, or trailing punctuation. Content words identical. | **28** | 56 | $275,841,575 |
| **Aggressive** (needs a human eye) | Additionally ignores hyphen/slash spacing and small dropped words — catches hyphenation, Oxford-comma, slash-vs-parens, and dropped-word variants. May over-merge. | **21** | 45 | $329,124,790 |

The `&`/`AND` split you flagged is real but small — **4 of the 28 mechanical groups**. The larger mechanical fragmenters are:

| Root cause | Mechanical groups |
|---|---|
| leading * | 14 |
| casing | 6 |
| curly apostrophe | 5 |
| &/AND | 4 |

**Headline:** the single biggest fragmenter by dollars is **not** `&`/`AND` — it's the **curly vs. straight apostrophe** (`'` vs `’`), which silently splits *City's First Readers* ($55,181,235), *Teacher's Choice*, *Prisoners' Rights Project*, and *Young Women's Leadership Development*; and the **leading `*` marker**, a source-formatting artifact that split ~13 FY10–FY11 health initiatives. In the aggressive tier, a single hyphen (*After School* vs *After-School*) splits the **$188M Cultural After-School Adventure (CASA)** program — the largest collision in the dataset.

---

## Tier 1 — Mechanical merges (high confidence: 28 groups)

Each block is **one** initiative. Fix = collapse to a single canonical spelling.


### 1. Teacher's Choice
*Causes:* `curly apostrophe` · *Combined:* $59,355,000 · *Span:* FY09–FY16

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Teacher's Choice` | FY09, FY10, FY11, FY15, FY16 | 5 | $51,020,000 |
| `Teacher’s Choice` | FY13, FY14 | 2 | $8,335,000 |

### 2. City’s First Readers
*Causes:* `curly apostrophe` · *Combined:* $55,181,235 · *Span:* FY16–FY27

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `City's First Readers` | FY27 | 1 | $5,449,667 |
| `City’s First Readers` | FY16–FY26 (11 yrs) | 11 | $49,731,568 |

### 3. Developmental, Psychological & Behavioral Health Services
*Causes:* `&/AND` · *Combined:* $24,279,893 · *Span:* FY17–FY27

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Developmental, Psychological & Behavioral Health Services` | FY17–FY26 (10 yrs) | 10 | $22,024,400 |
| `Developmental, Psychological and Behavioral Health Services` | FY27 | 1 | $2,255,493 |

### 4. Young Women's Leadership Development
*Causes:* `curly apostrophe` · *Combined:* $16,490,450 · *Span:* FY17–FY27

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Young Women's Leadership Development` | FY17–FY27 (8 yrs) | 8 | $11,268,950 |
| `Young Women’s Leadership Development` | FY24, FY25, FY26 | 3 | $5,221,500 |

### 5. *Child Health Clinics
*Causes:* `leading *` · *Combined:* $15,000,000 · *Span:* FY09–FY11

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*Child Health Clinics` | FY10, FY11 | 2 | $10,000,000 |
| `Child Health Clinics` | FY09 | 1 | $5,000,000 |

### 6. Prisoners’ Rights Project
*Causes:* `curly apostrophe` · *Combined:* $11,100,000 · *Span:* FY16–FY27

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Prisoners' Rights Project` | FY27 | 1 | $1,000,000 |
| `Prisoners’ Rights Project` | FY16–FY26 (11 yrs) | 11 | $10,100,000 |

### 7. Dropout Prevention & Intervention
*Causes:* `&/AND` · *Combined:* $10,985,000 · *Span:* FY09–FY19

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Dropout Prevention & Intervention` | FY09, FY10, FY11, FY12, FY13, FY14 | 6 | $8,500,000 |
| `Dropout Prevention and Intervention` | FY19 | 1 | $2,485,000 |

### 8. *Infant Mortality
*Causes:* `leading *` · *Combined:* $10,092,000 · *Span:* FY09–FY11

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*Infant Mortality` | FY10, FY11 | 2 | $6,546,000 |
| `Infant Mortality` | FY09 | 1 | $3,546,000 |

### 9. Diversity, Inclusion and Equity in Tech Initiative
*Causes:* `&/AND` · *Combined:* $6,895,000 · *Span:* FY18–FY27

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Diversity, Inclusion & Equity in Tech Initiative` | FY27 | 1 | $700,000 |
| `Diversity, Inclusion and Equity in Tech Initiative` | FY18–FY26 (9 yrs) | 9 | $6,195,000 |

### 10. *Obesity Intervention Programs
*Causes:* `leading *` · *Combined:* $6,765,000 · *Span:* FY09–FY11

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*Obesity Intervention Programs` | FY10, FY11 | 2 | $3,765,000 |
| `Obesity Intervention Programs` | FY09 | 1 | $3,000,000 |

### 11. Older Adults Mental Health (formerly Geriatric Older Adults)
*Causes:* `casing` · *Combined:* $6,755,060 · *Span:* FY25–FY26

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Older Adults Mental Health (Formerly Geriatric Older Adults)` | FY26 | 1 | $3,349,520 |
| `Older Adults Mental Health (formerly Geriatric Older Adults)` | FY25 | 1 | $3,405,540 |

### 12. *Rapid HIV Testing
*Causes:* `leading *` · *Combined:* $6,000,000 · *Span:* FY09–FY11

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*Rapid HIV Testing` | FY10, FY11 | 2 | $4,000,000 |
| `Rapid HIV Testing` | FY09 | 1 | $2,000,000 |

### 13. *HIV/AIDS-Faith Based Initiative
*Causes:* `leading *` · *Combined:* $5,500,000 · *Span:* FY09–FY11

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*HIV/AIDS-Faith Based Initiative` | FY10, FY11 | 2 | $3,500,000 |
| `HIV/AIDS-Faith Based Initiative` | FY09 | 1 | $2,000,000 |

### 14. Reproductive & Sexual Health Services
*Causes:* `&/AND` · *Combined:* $5,339,337 · *Span:* FY17–FY27

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Reproductive & Sexual Health Services` | FY18–FY26 (7 yrs) | 7 | $3,452,056 |
| `Reproductive and Sexual Health Services` | FY17, FY20, FY21, FY27 | 4 | $1,887,281 |

### 15. Dominican Studies Institute
*Causes:* `casing` · *Combined:* $4,100,000 · *Span:* FY09–FY16

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Dominican Studies Institute` | FY09–FY15 (7 yrs) | 7 | $3,130,000 |
| `Dominican Studies institute` | FY16 | 1 | $970,000 |

### 16. *NYC Managed Care Consumer Assistance Program
*Causes:* `leading *` · *Combined:* $4,000,000 · *Span:* FY09–FY10

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*NYC Managed Care Consumer Assistance Program` | FY10 | 1 | $2,000,000 |
| `NYC Managed Care Consumer Assistance Program` | FY09 | 1 | $2,000,000 |

### 17. CityMeals on Wheels
*Causes:* `casing` · *Combined:* $4,000,000 · *Span:* FY09–FY14

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `CityMeals on Wheels` | FY10, FY13, FY14 | 3 | $3,000,000 |
| `Citymeals on Wheels` | FY09 | 1 | $1,000,000 |

### 18. *Cancer Initiatives
*Causes:* `leading *` · *Combined:* $3,865,000 · *Span:* FY09–FY11

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*Cancer Initiatives` | FY10, FY11 | 2 | $2,365,000 |
| `Cancer Initiatives` | FY09 | 1 | $1,500,000 |

### 19. *Injection Drug Users Health Alliance (IDUHA)
*Causes:* `leading *` · *Combined:* $3,700,000 · *Span:* FY10–FY16

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*Injection Drug Users Health Alliance (IDUHA)` | FY10, FY11 | 2 | $2,700,000 |
| `Injection Drug Users Health Alliance (IDUHA)` | FY16 | 1 | $1,000,000 |

### 20. *Primary Care Initiative PEG Restoration
*Causes:* `leading *` · *Combined:* $3,419,600 · *Span:* FY10–FY11

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*Primary Care Initiative PEG Restoration` | FY10 | 1 | $2,750,000 |
| `Primary Care Initiative PEG Restoration` | FY11 | 1 | $669,600 |

### 21. CONNECT, Inc. Community Empowerment Program
*Causes:* `leading *` · *Combined:* $2,910,000 · *Span:* FY10–FY16

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*CONNECT, Inc. Community Empowerment Program` | FY11, FY12 | 2 | $540,000 |
| `CONNECT, Inc. Community Empowerment Program` | FY10, FY13, FY14, FY15, FY16 | 5 | $2,370,000 |

### 22. *Asthma Control Program
*Causes:* `leading *` · *Combined:* $2,090,000 · *Span:* FY09–FY16

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*Asthma Control Program` | FY10, FY11 | 2 | $1,045,000 |
| `Asthma Control Program` | FY09, FY16 | 2 | $1,045,000 |

### 23. Pride at Work
*Causes:* `casing` · *Combined:* $2,004,000 · *Span:* FY24–FY27

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Pride At Work` | FY27 | 1 | $501,000 |
| `Pride at Work` | FY24, FY25, FY26 | 3 | $1,503,000 |

### 24. *HIV Prevention and Health Literacy for Seniors
*Causes:* `leading *` · *Combined:* $1,780,000 · *Span:* FY09–FY11

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*HIV Prevention and Health Literacy for Seniors` | FY10, FY11 | 2 | $1,140,000 |
| `HIV Prevention and Health Literacy for Seniors` | FY09 | 1 | $640,000 |

### 25. Care Workers for Our Future
*Causes:* `casing` · *Combined:* $1,600,000 · *Span:* FY24–FY27

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Care Workers For Our Future` | FY27 | 1 | $400,000 |
| `Care Workers for Our Future` | FY24, FY25, FY26 | 3 | $1,200,000 |

### 26. Family Planning
*Causes:* `leading *` · *Combined:* $1,411,000 · *Span:* FY09–FY16

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*Family Planning` | FY10, FY11 | 2 | $693,000 |
| `Family Planning` | FY09, FY16 | 2 | $718,000 |

### 27. *NYU Dental Van
*Causes:* `leading *` · *Combined:* $804,000 · *Span:* FY09–FY11

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `*NYU Dental Van` | FY10, FY11 | 2 | $536,000 |
| `NYU Dental Van` | FY09 | 1 | $268,000 |

### 28. Women's Housing and Economic Development Corporation (WHEDCO)
*Causes:* `casing`, `curly apostrophe` · *Combined:* $420,000 · *Span:* FY14–FY16

| Spelling (raw) | Years | # yrs | Amount |
|---|---|--:|--:|
| `Women's Housing and Economic Development Corporation (WHEDCO)` | FY14 | 1 | $210,000 |
| `Women’s Housing and Economic Development Corporation (WHEDco)` | FY16 | 1 | $210,000 |

---

## Tier 2 — Needs review (21 groups)

These collapse only under aggressive normalization (hyphen/slash/dropped-word). Most are genuine duplicates, but confirm before merging — a few could be legitimately distinct programs.

| Suggested canonical | Variants (raw) | Causes | Combined |
|---|---|---|--:|
| *HIV AIDS -Communities of Color (Prevention & Education) | `*HIV AIDS -Communities of Color (Prevention & Education)` (FY10–FY10, $1,664,000)<br>`*HIV/AIDS-Communities of Color (Prevention & Education)` (FY11–FY11, $1,500,000)<br>`HIV AIDS-Communities of Color (Prevention & Education)` (FY09–FY09, $1,664,000) | leading * | $4,828,000 |
| Small Business and Job Development / Financial Literacy | `Small Business and Job Development / Financial Literacy` (FY11–FY14, $2,500,000)<br>`Small Business/Job Development / Financial Literacy` (FY15–FY15, $600,000)<br>`Small Business/Job Development/Financial Literacy` (FY16–FY16, $600,000) | wording | $3,700,000 |
| Chess in the Schools | `Chess in the Schools` (FY13–FY16, $800,000)<br>`Chess in the Schools, Inc.` (FY15–FY15, $400,000)<br>`Chess-in-the-Schools, Inc.` (FY10–FY10, $300,000) | hyphenation | $1,500,000 |
| Cultural After-School Adventure (CASA) | `Cultural After School Adventure (CASA)` (FY09–FY09, $2,850,000)<br>`Cultural After-School Adventure (CASA)` (FY11–FY27, $185,600,000) | hyphenation | $188,450,000 |
| Coalition Theaters of Color | `Coalition Theaters of Color` (FY15–FY27, $46,780,000)<br>`Coalition of Theaters of Color` (FY09–FY14, $4,400,000) | wording | $51,180,000 |
| PEG Restoration –Cultural Institution Group | `PEG Restoration – Cultural Institution Group` (FY13–FY13, $6,000,000)<br>`PEG Restoration –Cultural Institution Group` (FY12–FY12, $20,548,790) | wording | $26,548,790 |
| Big Brothers Big Sisters of New York City | `Big Brothers Big Sisters of New York City` (FY14–FY26, $12,270,000)<br>`Big Brothers and Big Sisters of New York City` (FY19–FY27, $2,400,000) | wording | $14,670,000 |
| Anti-Eviction & SRO Legal Services | `Anti Eviction and SRO Legal Services` (FY09–FY09, $2,250,000)<br>`Anti-Eviction & SRO Legal Services` (FY11–FY14, $8,000,000) | &/AND | $10,250,000 |
| Transportation - Operating Costs | `Transportation - Operating Costs` (FY09–FY10, $5,550,000)<br>`Transportation Operating Costs` (FY13–FY14, $4,000,000) | wording | $9,550,000 |
| Teen Relationship Abuse Prevention Program (RAPP) – PEG Restoration | `Teen Relationship Abuse Prevention Program (RAPP) – PEG Restoration` (FY13–FY14, $4,000,000)<br>`Teen Relationship Abuse Prevention Program (RAPP) –PEG Restoration` (FY12–FY12, $2,000,000) | wording | $6,000,000 |
| Anti-Gun Violence - Community Based Programs | `Anti-Gun Violence - Community Based Programs` (FY15–FY15, $2,528,000)<br>`Anti-Gun Violence - Community-Based Programs` (FY16–FY16, $1,590,000) | hyphenation | $4,118,000 |
| Anti-Gun Violence - Violence Prevention, Conflict Mediation, and Youth Development | `Anti-Gun Violence - Violence Prevention, Conflict Mediation and Youth Development` (FY15–FY15, $250,000)<br>`Anti-Gun Violence - Violence Prevention, Conflict Mediation, and Youth Development` (FY13–FY14, $1,500,000) | wording | $1,750,000 |
| YMCA After School Program | `YMCA After School Program` (FY12–FY14, $1,050,000)<br>`YMCA After-School Program` (FY15–FY15, $350,000) | hyphenation | $1,400,000 |
| Immigrant Opportunities Initiative (IOI – CUNY Citizenship NOW! Expansion) | `Immigrant Opportunities Initiative (IOI – CUNY Citizenship NOW! Expansion` (FY13–FY13, $600,000)<br>`Immigrant Opportunities Initiative (IOI – CUNY Citizenship NOW! Expansion)` (FY14–FY14, $800,000) | wording | $1,400,000 |
| EBTs at Food Markets (GrowNYC) | `EBTs at Food Markets (GrowNYC)` (FY12–FY14, $875,000)<br>`EBTs at Food Markets/GrowNYC` (FY11–FY11, $420,000) | wording | $1,295,000 |
| Young Adult Institute and Workshop, Inc. | `Young Adult Institute & Workshop` (FY16–FY16, $50,000)<br>`Young Adult Institute and Workshop, Inc.` (FY10–FY11, $800,000) | &/AND | $850,000 |
| Peter Vallone Scholarship –FIT | `Peter Vallone Scholarship – FIT` (FY09–FY09, $250,000)<br>`Peter Vallone Scholarship –FIT` (FY10–FY11, $500,000) | wording | $750,000 |
| Food Retail and Workforce Training and Placement Program | `Food Retail Workforce Training and Placement Program` (FY11–FY11, $50,000)<br>`Food Retail and Workforce Training and Placement Program` (FY12–FY16, $285,000) | wording | $335,000 |
| Workforce Development - Queens Tech Education | `Workforce Development - Queens Tech Education` (FY13–FY15, $195,000)<br>`Workforce Development-Queens Tech Education` (FY16–FY16, $65,000) | wording | $260,000 |
| Diversity in Media Program | `Diversity in Media Program` (FY12–FY12, $100,000)<br>`Diversity in the Media Program` (FY13–FY13, $100,000) | wording | $200,000 |
| Household Composting Program (GrowNYC) | `Household Composting Program (GrowNYC)` (FY12–FY12, $45,000)<br>`Household Composting Program/GrowNYC` (FY11–FY11, $45,000) | wording | $90,000 |


---

## Where the fix belongs

Two options, not mutually exclusive:

1. **Normalize at build time (parser / `build_combined.py`).** Add a canonicalization pass that strips the leading `*`, unifies curly→straight apostrophes, `&`→`and` (or the reverse — pick one house style), collapses whitespace, and title-cases consistently. This fixes Tier 1 automatically and deterministically. **Recommended for the mechanical tier.**
2. **A committed crosswalk file (`data/combined/initiative_name_crosswalk.csv`).** `raw_spelling,canonical_name,confidence`. Required for the Tier-2 judgment calls (hyphenation, dropped words) that shouldn't be auto-merged, and gives downstream users (the viz, the MCP) a single join key. Seed it from this report.

Suggested house style, for consistency with the source PDFs and press-safe output: keep the ampersand as the word **"and"**, straight apostrophe, no leading `*`, Title Case.

## Caveats

- Dollar figures are summed across the raw `amount` column as-is; they confirm materiality, not audited totals.
- The mechanical tier is safe to auto-merge. The aggressive tier is a *candidate* list — human confirmation required.
- Scan is on `initiative` only. `category` and `agencies` showed **no** `&`/`AND` collisions, but a full canonical-name effort should re-run the same tiering on those columns.

*Generated by `gen_report.py` from `initiative_name_collisions.json`. Re-runnable against any refresh of the combined CSV.*
