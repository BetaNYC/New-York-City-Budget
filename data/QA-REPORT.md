# NYC Budget — Data QA Report

**Report generated:** 2026-08-12  
**Data current as of:** 2026-08-12 (files under `data/`)  
**Tool:** `code/validate_data.py`

**Verdict:** PASS — 273 files, 0 hard failure(s), 439 soft advisory(ies).

Severity: HARD (exit 1) = schema drift, malformed row, non-numeric amount, or malformed EIN. SOFT (exit 0) = zeros, sign anomalies, outliers, duplicates, column-bleed residuals, coverage notes. See the module docstring for the full check list and rationale.

## EIN coverage (feeds the MCP award-tool decision)

Valid 9-digit EINs / total rows, per year and EIN-bearing doctype. Initiatives, terms, and capital carry no EIN by design and are omitted. Transparency uses the `*_transparency_all.csv` file (per-reso components excluded to avoid double count).

| FY | doctype | valid EIN / rows | coverage |
|---|---|---|---|
| FY2010 | transparency | 1788/1788 | 100.0% |
| FY2011 | transparency | 1545/1545 | 100.0% |
| FY2012 | transparency | 932/932 | 100.0% |
| FY2013 | transparency | 1857/1857 | 100.0% |
| FY2014 | transparency | 166/166 | 100.0% |
| FY2015 | appendix | 0/0 | 0.0% |
| FY2015 | awards | 652/652 | 100.0% |
| FY2015 | transparency | 3047/3047 | 100.0% |
| FY2016 | appendix | 0/0 | 0.0% |
| FY2016 | awards | 335/335 | 100.0% |
| FY2016 | transparency | 4156/4156 | 100.0% |
| FY2017 | appendix | 0/0 | 0.0% |
| FY2017 | awards | 364/364 | 100.0% |
| FY2017 | transparency | 4656/4656 | 100.0% |
| FY2018 | appendix | 422/422 | 100.0% |
| FY2018 | awards | 480/480 | 100.0% |
| FY2018 | transparency | 5366/5366 | 100.0% |
| FY2019 | appendix | 0/0 | 0.0% |
| FY2019 | awards | 846/846 | 100.0% |
| FY2019 | transparency | 7090/7090 | 100.0% |
| FY2020 | appendix | 0/0 | 0.0% |
| FY2020 | awards | 2841/2841 | 100.0% |
| FY2020 | transparency | 5319/5319 | 100.0% |
| FY2021 | appendix | 4310/4310 | 100.0% |
| FY2021 | awards | 1810/1810 | 100.0% |
| FY2021 | transparency | 4463/4463 | 100.0% |
| FY2022 | appendix | 4182/4182 | 100.0% |
| FY2022 | awards | 1492/1492 | 100.0% |
| FY2022 | transparency | 7768/7768 | 100.0% |
| FY2023 | appendix | 4056/4056 | 100.0% |
| FY2023 | awards | 1848/1848 | 100.0% |
| FY2023 | transparency | 8354/8354 | 100.0% |
| FY2024 | appendix | 3911/3911 | 100.0% |
| FY2024 | awards | 5368/5368 | 100.0% |
| FY2024 | transparency | 3294/3294 | 100.0% |
| FY2025 | appendix | 3920/3920 | 100.0% |
| FY2025 | awards | 5646/5646 | 100.0% |
| FY2026 | appendix | 3914/3914 | 100.0% |
| FY2026 | awards | 5838/5838 | 100.0% |
| FY2026 | transparency | 4755/4755 | 100.0% |
| FY2027 | appendix | 3860/3860 | 100.0% |
| FY2027 | awards | 6118/6118 | 100.0% |
| FYNone | recovered_awards | 443/443 | 100.0% |

## Reconciliation roll-up

Parsed from every `*_reconciliation.txt`. Transparency prints no totals → N/A by nature. PARTIAL = documented in-source arithmetic diffs, not extraction errors.

| FY | doctype | ratio | status |
|---|---|---|---|
| FY2009 | schedule_c | 21/22 | PARTIAL (1 in-source diff) |
| FY2010 | schedule_c | 21/21 | PASS |
| FY2010 | transparency | — | N/A (no printed totals) |
| FY2011 | schedule_c | 18/19 | PARTIAL (1 in-source diff) |
| FY2011 | transparency | — | N/A (no printed totals) |
| FY2012 | schedule_c | 16/16 | PASS |
| FY2012 | transparency | — | N/A (no printed totals) |
| FY2013 | schedule_c | 17/17 | PASS |
| FY2013 | transparency | — | N/A (no printed totals) |
| FY2014 | schedule_c | 17/17 | PASS |
| FY2014 | transparency | — | N/A (no printed totals) |
| FY2015 | schedule_c | 24/24 | PASS |
| FY2015 | transparency | — | N/A (no printed totals) |
| FY2016 | schedule_c | 24/26 | PARTIAL (2 in-source diff) |
| FY2016 | transparency | — | N/A (no printed totals) |
| FY2017 | schedule_c | 24/27 | PARTIAL (3 in-source diff) |
| FY2017 | transparency | — | N/A (no printed totals) |
| FY2018 | schedule_c | 24/27 | PARTIAL (3 in-source diff) |
| FY2018 | transparency | — | N/A (no printed totals) |
| FY2019 | schedule_c | 27/28 | PARTIAL (1 in-source diff) |
| FY2019 | transparency | — | N/A (no printed totals) |
| FY2020 | capital | 23/23 | PASS |
| FY2020 | schedule_c | 27/28 | PARTIAL (1 in-source diff) |
| FY2020 | transparency | — | N/A (no printed totals) |
| FY2021 | schedule_c | 25/26 | PARTIAL (1 in-source diff) |
| FY2021 | transparency | — | N/A (no printed totals) |
| FY2022 | capital | 32/32 | PASS |
| FY2022 | schedule_c | 24/26 | PARTIAL (2 in-source diff) |
| FY2022 | transparency | — | N/A (no printed totals) |
| FY2023 | capital | 30/30 | PASS |
| FY2023 | schedule_c | 26/26 | PASS |
| FY2023 | transparency | — | N/A (no printed totals) |
| FY2024 | capital | 30/30 | PASS |
| FY2024 | schedule_c | 24/26 | PARTIAL (2 in-source diff) |
| FY2024 | transparency | — | N/A (no printed totals) |
| FY2025 | capital | — | N/A (no printed totals) |
| FY2025 | capital | 30/30 | PASS |
| FY2025 | schedule_c | 24/26 | PARTIAL (2 in-source diff) |
| FY2026 | capital | 31/31 | PASS |
| FY2026 | schedule_c | 24/25 | PARTIAL (1 in-source diff) |
| FY2026 | transparency | — | N/A (no printed totals) |
| FY2027 | capital | 24/26 | PARTIAL (2 in-source diff) |
| FY2027 | schedule_c | 25/25 | PASS |

## Initiative-level award reconciliation (SOFT advisory)

Award rows summed per initiative vs that initiative's own **printed** amount in `*_schedule_c_initiatives.csv`, joined exactly on a punctuation-folded initiative name within one fiscal year. `residual = printed - award rows`: positive is **short**, negative is **over**. This is the award stream's first pass/fail target — the per-year `*_reconciliation.txt` reconciles only the category summary and reports award rows as a bare tally with no target at all.

Advisory, never a gate. Three known structural causes live in this residual: award rows carrying no initiative label at all, initiative labels the parser mis-assigns to a neighbouring block, and provider tables the source PDF's text layer never yielded. `unjoined $` is award dollars under a label with no printed counterpart plus dollars on rows with no label — counted here so the joined columns are not mistaken for full coverage.

`recovered` is the optional sidecar `recovered/schedule_c_absorbed_awards.csv` (awards the parser absorbed into a neighbouring row and lost), included so the gap is legible with and without it. It is present.

| FY | joined | balanced | short | over | printed | award rows | residual | recovered | residual after | balanced after | unjoined $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FY2015 | 54 | 47 | 7 | 0 | 72,846,000 | 48,788,999 | 24,057,001 | 0 | 24,057,001 | 47 | 24,410,838 |
| FY2016 | 65 | 50 | 15 | 0 | 86,474,645 | 73,550,272 | 12,924,373 | 9,503,585 | 3,420,788 | 55 | 16,366,740 |
| FY2017 | 62 | 15 | 46 | 1 | 137,820,597 | 84,169,476 | 53,651,121 | 22,996,522 | 30,654,599 | 28 | 5,732,011 |
| FY2018 | 52 | 23 | 29 | 0 | 109,707,645 | 76,182,556 | 33,525,089 | 16,268,804 | 17,256,285 | 31 | 26,534,400 |
| FY2019 | 78 | 33 | 39 | 6 | 179,903,641 | 158,781,023 | 21,122,618 | 3,573,279 | 17,549,339 | 39 | 22,245,908 |
| FY2020 | 82 | 41 | 39 | 2 | 214,474,020 | 174,711,180 | 39,762,840 | 0 | 39,762,840 | 41 | 84,051,205 |
| FY2021 | 74 | 43 | 30 | 1 | 154,055,180 | 120,286,489 | 33,768,691 | 0 | 33,768,691 | 43 | 81,783,699 |
| FY2022 | 74 | 33 | 38 | 3 | 188,358,720 | 142,087,611 | 46,271,109 | 0 | 46,271,109 | 33 | 80,469,332 |
| FY2023 | 86 | 43 | 42 | 1 | 234,402,951 | 179,962,789 | 54,440,162 | 0 | 54,440,162 | 43 | 82,456,425 |
| FY2024 | 102 | 61 | 39 | 2 | 288,174,916 | 232,265,374 | 55,909,542 | 0 | 55,909,542 | 61 | 168,398,200 |
| FY2025 | 104 | 69 | 33 | 2 | 305,027,167 | 244,365,464 | 60,661,703 | 0 | 60,661,703 | 69 | 168,619,646 |
| FY2026 | 98 | 57 | 37 | 4 | 330,237,279 | 255,775,861 | 74,461,418 | 0 | 74,461,418 | 57 | 231,511,384 |
| FY2027 | 152 | 113 | 34 | 5 | 507,368,128 | 493,824,363 | 13,543,765 | 0 | 13,543,765 | 113 | 111,287,049 |

Unjoined detail — dollars this check cannot test, per year:

| FY | award labels with no printed counterpart | $ | award rows with no initiative label | $ | recovered $ not joinable |
|---|---:|---:|---:|---:|---:|
| FY2015 | 22 | 23,610,838 | 2 | 800,000 | 0 |
| FY2016 | 15 | 16,366,740 | 0 | 0 | 1,555,980 |
| FY2017 | 8 | 5,174,171 | 24 | 557,840 | 4,883,980 |
| FY2018 | 20 | 22,400,501 | 49 | 4,133,899 | 7,036,150 |
| FY2019 | 15 | 16,525,806 | 70 | 5,720,102 | 684,421 |
| FY2020 | 18 | 42,846,440 | 562 | 41,204,765 | 0 |
| FY2021 | 30 | 59,425,430 | 442 | 22,358,269 | 0 |
| FY2022 | 20 | 72,699,191 | 63 | 7,770,141 | 0 |
| FY2023 | 3 | 3,519,423 | 1098 | 78,937,002 | 0 |
| FY2024 | 16 | 38,239,051 | 2479 | 130,159,149 | 0 |
| FY2025 | 10 | 36,869,548 | 2501 | 131,750,098 | 0 |
| FY2026 | 16 | 59,289,174 | 2410 | 172,222,210 | 0 |
| FY2027 | 6 | 111,287,049 | 0 | 0 | 0 |

### Initiatives that do not balance (455)

Balanced initiatives are omitted — their residual is $0 by definition. Sorted by fiscal year, then by the size of the residual.

| FY | initiative | status | printed | award rows | rows | residual | recovered | residual after |
|---|---|---|---:|---:|---:|---:|---:|---:|
| FY2015 | Summer Out of School Time (OST) | short | 17,500,000 | 3,000,000 | 1 | 14,500,000 | 0 | 14,500,000 |
| FY2015 | Domestic Violence and Empowerment (DoVE) Initiative | short | 4,000,000 | 600,000 | 1 | 3,400,000 | 0 | 3,400,000 |
| FY2015 | Senior Centers, Programs, and Services Enhancement | short | 3,005,000 | 641,000 | 5 | 2,364,000 | 0 | 2,364,000 |
| FY2015 | Citywide Civil Legal Services | short | 3,750,000 | 1,500,000 | 2 | 2,250,000 | 0 | 2,250,000 |
| FY2015 | Elder Abuse Enhancement | short | 1,000,000 | 107,000 | 2 | 893,000 | 0 | 893,000 |
| FY2015 | A Greener NYC | short | 750,000 | 100,000 | 2 | 650,000 | 0 | 650,000 |
| FY2015 | Communities of Color Non-Profit Stabilization Fund | short | 2,500,000 | 2,499,999 | 3 | 1 | 0 | 1 |
| FY2016 | Jobs to Build On | short | 5,636,000 | 281,800 | 1 | 5,354,200 | 5,354,200 | 0 |
| FY2016 | Alternatives to Incarceration (ATI) Programs | short | 4,432,000 | 1,703,525 | 4 | 2,728,475 | 1,871,275 | 857,200 |
| FY2016 | Worker Cooperative Business Development Initiative | short | 2,100,000 | 1,095,000 | 10 | 1,005,000 | 1,005,000 | 0 |
| FY2016 | Unaccompanied Minors and Families | short | 1,500,000 | 590,000 | 3 | 910,000 | 0 | 910,000 |
| FY2016 | Anti-Gun Violence - Community-Based Programs | short | 1,590,000 | 750,000 | 3 | 840,000 | 0 | 840,000 |
| FY2016 | Obesity Prevention | short | 1,300,000 | 550,000 | 2 | 750,000 | 750,000 | 0 |
| FY2016 | Initiative to Address Sexual Assault | short | 600,000 | 300,000 | 2 | 300,000 | 150,000 | 150,000 |
| FY2016 | Legal Services for Domestic Violence Victims | short | 350,000 | 125,000 | 1 | 225,000 | 100,000 | 125,000 |
| FY2016 | Community Consultant Contracts (CCC) | short | 1,100,000 | 891,902 | 30 | 208,098 | 208,110 | -12 |
| FY2016 | Legal Services for the Working Poor | short | 1,725,000 | 1,525,000 | 5 | 200,000 | 0 | 200,000 |
| FY2016 | Anti-Gun Violence - Mental Health/Therapeutic Services | short | 520,000 | 385,000 | 6 | 135,000 | 0 | 135,000 |
| FY2016 | COMPASS Slot Restoration | short | 9,886,800 | 9,783,200 | 50 | 103,600 | 0 | 103,600 |
| FY2016 | LGBT Students’ Liaison | short | 200,000 | 100,000 | 1 | 100,000 | 0 | 100,000 |
| FY2016 | Elder Abuse Enhancement | short | 335,000 | 285,000 | 4 | 50,000 | 50,000 | 0 |
| FY2016 | Day Laborer Workforce Initiative | short | 500,000 | 485,000 | 4 | 15,000 | 15,000 | 0 |
| FY2017 | Job Training and Placement Initiative | short | 8,106,000 | 551,800 | 3 | 7,554,200 | 0 | 7,554,200 |
| FY2017 | Discretionary Child Care | short | 9,355,069 | 3,148,737 | 5 | 6,206,332 | 6,206,332 | 0 |
| FY2017 | Alternatives to Incarceration (ATIs) | short | 5,632,000 | 1,456,100 | 6 | 4,175,900 | 0 | 4,175,900 |
| FY2017 | Naturally Occurring Retirement Communities (NORCs) | short | 3,850,000 | 1,285,000 | 8 | 2,565,000 | 0 | 2,565,000 |
| FY2017 | Autism Awareness | short | 3,315,386 | 861,383 | 15 | 2,454,003 | 424,003 | 2,030,000 |
| FY2017 | New York Immigrant Family Unity Project | short | 6,230,000 | 4,153,332 | 2 | 2,076,668 | 2,076,667 | 1 |
| FY2017 | Community Housing Preservation Strategies | short | 3,651,000 | 1,640,295 | 33 | 2,010,705 | 866,835 | 1,143,870 |
| FY2017 | City’s First Readers | short | 2,792,000 | 894,000 | 8 | 1,898,000 | 898,000 | 1,000,000 |
| FY2017 | Digital Inclusion and Literacy Initiative | short | 2,040,000 | 180,000 | 9 | 1,860,000 | 0 | 1,860,000 |
| FY2017 | Stabilizing NYC | short | 2,000,000 | 575,000 | 6 | 1,425,000 | 325,000 | 1,100,000 |
| FY2017 | Afterschool Enrichment Initiative | short | 5,425,000 | 4,075,000 | 2 | 1,350,000 | 0 | 1,350,000 |
| FY2017 | Supportive Alternatives to Violent Encounters (SAVE) | short | 1,950,000 | 600,000 | 1 | 1,350,000 | 0 | 1,350,000 |
| FY2017 | Immigrant Opportunities Initiative | short | 2,600,000 | 1,382,000 | 18 | 1,218,000 | 1,038,000 | 180,000 |
| FY2017 | Court-Involved Youth Mental Health Initiative | short | 1,900,000 | 692,000 | 7 | 1,208,000 | 908,000 | 300,000 |
| FY2017 | LGBTQ Senior Services in Every Borough | short | 1,500,000 | 300,000 | 1 | 1,200,000 | 1,200,000 | 0 |
| FY2017 | Legal Services for Low-Income New Yorkers | short | 5,000,000 | 4,000,000 | 2 | 1,000,000 | 250,000 | 750,000 |
| FY2017 | Legal Services for the Working Poor | short | 2,405,000 | 1,420,000 | 6 | 985,000 | 305,000 | 680,000 |
| FY2017 | Viral Hepatitis Prevention | short | 1,186,476 | 214,290 | 3 | 972,186 | 0 | 972,186 |
| FY2017 | Anti-Eviction and Housing Court Resources | short | 5,650,000 | 4,744,500 | 12 | 905,500 | 650,000 | 255,500 |
| FY2017 | COMPASS | short | 8,000,000 | 7,116,400 | 4 | 883,600 | 883,600 | 0 |
| FY2017 | Physical Education and Fitness | short | 1,925,000 | 1,125,000 | 1 | 800,000 | 0 | 800,000 |
| FY2017 | Access to Food and Nutritional Education | short | 930,000 | 250,000 | 2 | 680,000 | 680,000 | 0 |
| FY2017 | Educational Programs for Students | short | 2,975,000 | 2,300,000 | 2 | 675,000 | 675,000 | 0 |
| FY2017 | Children Under Five | short | 1,002,000 | 346,154 | 2 | 655,846 | 0 | 655,846 |
| FY2017 | Immigrant Health Initiative | short | 1,500,000 | 850,000 | 7 | 650,000 | 600,000 | 50,000 |
| FY2017 | Small Business Outreach and Assistance Program | short | 1,288,855 | 666,250 | 5 | 622,605 | 522,605 | 100,000 |
| FY2017 | Initiative to Combat Sexual Assault | short | 1,348,000 | 748,000 | 1 | 600,000 | 450,000 | 150,000 |
| FY2017 | Geriatric Mental Health | short | 1,827,000 | 1,229,000 | 14 | 598,000 | 434,000 | 164,000 |
| FY2017 | Dropout Prevention and Intervention Initiative | short | 1,595,000 | 1,015,000 | 8 | 580,000 | 300,000 | 280,000 |
| FY2017 | Support for Educators | short | 12,744,500 | 12,294,500 | 1 | 450,000 | 450,000 | 0 |
| FY2017 | Mental Health Services for Vulnerable Populations | short | 1,093,000 | 663,295 | 6 | 429,705 | 280,000 | 149,705 |
| FY2017 | Support for Victims of Human Trafficking | short | 750,000 | 325,000 | 3 | 425,000 | 375,000 | 50,000 |
| FY2017 | Access Health | short | 1,070,000 | 701,156 | 10 | 368,844 | 210,768 | 158,076 |
| FY2017 | YouthBuild Project Initiative | short | 2,100,000 | 1,742,200 | 4 | 357,800 | 357,800 | 0 |
| FY2017 | Child Health and Wellness | short | 646,000 | 300,000 | 1 | 346,000 | 346,000 | 0 |
| FY2017 | MWBE Leadership Associations | short | 600,000 | 283,905 | 4 | 316,095 | 119,780 | 196,315 |
| FY2017 | Medicaid Redesign Transition | short | 500,000 | 200,000 | 3 | 300,000 | 150,000 | 150,000 |
| FY2017 | Social Adult Day Care Enhancement | short | 950,000 | 665,000 | 7 | 285,000 | 190,000 | 95,000 |
| FY2017 | Cancer Services | short | 790,500 | 540,500 | 6 | 250,000 | 250,000 | 0 |
| FY2017 | Restorative Justice Program | short | 1,300,000 | 1,050,000 | 2 | 250,000 | 0 | 250,000 |
| FY2017 | Day Laborer Workforce Initiative | short | 570,000 | 350,000 | 4 | 220,000 | 220,000 | 0 |
| FY2017 | Legal Services for Veterans | short | 350,000 | 150,000 | 1 | 200,000 | 200,000 | 0 |
| FY2017 | Homeless Prevention Fund | short | 820,000 | 656,000 | 2 | 164,000 | 0 | 164,000 |
| FY2017 | Elder Abuse Enhancement | short | 335,000 | 235,000 | 3 | 100,000 | 50,000 | 50,000 |
| FY2017 | Information and Referral Services | short | 407,811 | 351,679 | 2 | 56,132 | 56,132 | 0 |
| FY2017 | Homeless Prevention Services for Veterans | over | 300,000 | 350,000 | 2 | -50,000 | 25,000 | -75,000 |
| FY2017 | Children and Families in NYC Homeless System | short | 1,000,000 | 977,000 | 5 | 23,000 | 23,000 | 0 |
| FY2018 | Domestic Violence and Empowerment (DoVE) Initiative | short | 7,805,000 | 562,500 | 1 | 7,242,500 | 0 | 7,242,500 |
| FY2018 | Discretionary Child Care | short | 9,855,190 | 3,537,041 | 5 | 6,318,149 | 6,318,149 | 0 |
| FY2018 | Afterschool Enrichment Initiative | short | 5,725,000 | 1,675,000 | 3 | 4,050,000 | 4,000,000 | 50,000 |
| FY2018 | Autism Awareness | short | 3,236,846 | 264,903 | 4 | 2,971,943 | 0 | 2,971,943 |
| FY2018 | Job Training and Placement Initiative | short | 7,906,000 | 5,015,300 | 31 | 2,890,700 | 0 | 2,890,700 |
| FY2018 | Alternatives to Incarceration (ATI’s) | short | 6,407,000 | 4,678,660 | 14 | 1,728,340 | 1,328,340 | 400,000 |
| FY2018 | Bail Fund | short | 1,400,000 | 150,000 | 1 | 1,250,000 | 109,000 | 1,141,000 |
| FY2018 | COMPASS | short | 1,813,600 | 963,200 | 4 | 850,400 | 704,400 | 146,000 |
| FY2018 | Post-Arrest Diversion Program | short | 1,025,000 | 330,000 | 1 | 695,000 | 0 | 695,000 |
| FY2018 | Immigrant Opportunities Initiative | short | 2,600,000 | 1,928,000 | 20 | 672,000 | 455,000 | 217,000 |
| FY2018 | Support for Victims of Human Trafficking | short | 1,000,000 | 375,000 | 4 | 625,000 | 375,000 | 250,000 |
| FY2018 | Restorative Justice Program | short | 1,300,000 | 800,000 | 2 | 500,000 | 0 | 500,000 |
| FY2018 | Support for Educators | short | 20,804,500 | 20,354,000 | 1 | 450,500 | 450,000 | 500 |
| FY2018 | Initiative to Combat Sexual Assault | short | 1,348,000 | 898,000 | 2 | 450,000 | 300,000 | 150,000 |
| FY2018 | Children Under Five | short | 1,002,000 | 576,923 | 3 | 425,077 | 425,077 | 0 |
| FY2018 | Court-Involved Youth Mental Health | short | 2,050,000 | 1,672,000 | 14 | 378,000 | 145,000 | 233,000 |
| FY2018 | MWBE Leadership Associations | short | 600,000 | 245,975 | 4 | 354,025 | 265,170 | 88,855 |
| FY2018 | Information and Referral Services | short | 407,811 | 56,132 | 1 | 351,679 | 103,914 | 247,765 |
| FY2018 | Mental Health Services for Vulnerable Populations | short | 1,218,000 | 883,000 | 10 | 335,000 | 250,000 | 85,000 |
| FY2018 | Geriatric Mental Health | short | 1,905,540 | 1,618,540 | 19 | 287,000 | 63,000 | 224,000 |
| FY2018 | Cancer Services | short | 790,500 | 640,500 | 8 | 150,000 | 150,000 | 0 |
| FY2018 | Veterans Community Development | short | 515,000 | 395,000 | 6 | 120,000 | 120,000 | 0 |
| FY2018 | Food Access and Benefits | short | 725,000 | 625,000 | 1 | 100,000 | 0 | 100,000 |
| FY2018 | Supportive Alternatives to Violent Encounters (SAVE) | short | 1,950,000 | 1,850,000 | 4 | 100,000 | 100,000 | 0 |
| FY2018 | Access to Healthy Food and Nutritional Education | short | 930,000 | 835,000 | 5 | 95,000 | 95,000 | 0 |
| FY2018 | Dedicated Contraceptive Fund | short | 400,000 | 337,000 | 3 | 63,000 | 63,000 | 0 |
| FY2018 | Naturally Occurring Retirement Communities (NORCs) | short | 3,850,000 | 3,805,000 | 12 | 45,000 | 45,000 | 0 |
| FY2018 | Initiative for Immigrant Survivors of Domestic Violence | short | 250,000 | 230,000 | 6 | 20,000 | 0 | 20,000 |
| FY2018 | Viral Hepatitis Prevention | short | 1,423,658 | 1,416,882 | 26 | 6,776 | 403,754 | -396,978 |
| FY2019 | Domestic Violence and Empowerment (DoVE) Initiative | short | 9,305,000 | 1,582,500 | 18 | 7,722,500 | 45,000 | 7,677,500 |
| FY2019 | Child Health and Wellness | over | 646,000 | 6,175,370 | 67 | -5,529,370 | 308,630 | -5,838,000 |
| FY2019 | Job Training and Placement Initiative | over | 8,106,000 | 12,287,700 | 33 | -4,181,700 | 0 | -4,181,700 |
| FY2019 | Parks Equity Initiative | short | 4,603,500 | 600,000 | 1 | 4,003,500 | 0 | 4,003,500 |
| FY2019 | Communities of Color Nonprofit Stabilization Fund | over | 3,700,000 | 7,380,000 | 47 | -3,680,000 | 70,000 | -3,750,000 |
| FY2019 | Food Pantries | short | 4,600,000 | 1,000,000 | 1 | 3,600,000 | 0 | 3,600,000 |
| FY2019 | Crisis Management System | short | 2,590,000 | 810,000 | 3 | 1,780,000 | 0 | 1,780,000 |
| FY2019 | Alternatives to Incarceration (ATI’s) | short | 8,107,000 | 6,357,000 | 17 | 1,750,000 | 0 | 1,750,000 |
| FY2019 | Court-Involved Youth Mental Health | short | 2,850,000 | 1,193,000 | 9 | 1,657,000 | 0 | 1,657,000 |
| FY2019 | Borough Presidents’ Discretionary Funding Restoration | over | 1,129,774 | 2,732,000 | 22 | -1,602,226 | 25,000 | -1,627,226 |
| FY2019 | Access Health | short | 2,500,000 | 1,187,000 | 17 | 1,313,000 | 0 | 1,313,000 |
| FY2019 | Dropout Prevention and Intervention | short | 2,485,000 | 1,180,000 | 4 | 1,305,000 | 0 | 1,305,000 |
| FY2019 | Initiative to Combat Sexual Assault | short | 2,810,000 | 1,548,000 | 5 | 1,262,000 | 200,000 | 1,062,000 |
| FY2019 | Opioid Prevention and Treatment | short | 2,000,000 | 750,000 | 3 | 1,250,000 | 250,000 | 1,000,000 |
| FY2019 | Worker Cooperative Business Development Initiative | short | 3,499,000 | 2,380,600 | 11 | 1,118,400 | 562,400 | 556,000 |
| FY2019 | Discretionary Child Care | short | 5,355,190 | 4,242,000 | 15 | 1,113,190 | 0 | 1,113,190 |
| FY2019 | YouthBuild Project Initiative | short | 2,100,000 | 989,700 | 4 | 1,110,300 | 370,100 | 740,200 |
| FY2019 | Senior Centers for Immigrant Populations | short | 2,000,000 | 900,000 | 9 | 1,100,000 | 100,000 | 1,000,000 |
| FY2019 | Mental Health Services for Vulnerable Populations | short | 1,718,000 | 979,000 | 7 | 739,000 | 0 | 739,000 |
| FY2019 | Viral Hepatitis Prevention | short | 1,923,658 | 1,198,121 | 22 | 725,537 | 27,000 | 698,537 |
| FY2019 | Cancer Services | over | 599,500 | 1,245,500 | 11 | -646,000 | 0 | -646,000 |
| FY2019 | Wrap-Around Support for Transitional-Aged Foster Youth | short | 1,100,000 | 550,000 | 7 | 550,000 | 0 | 550,000 |
| FY2019 | Day Laborer Workforce Initiative | short | 1,970,000 | 1,470,000 | 6 | 500,000 | 0 | 500,000 |
| FY2019 | COMPASS | short | 1,813,600 | 1,319,200 | 5 | 494,400 | 494,400 | 0 |
| FY2019 | Chamber on the Go and Small Business Assistance | short | 1,888,855 | 1,404,855 | 12 | 484,000 | 88,500 | 395,500 |
| FY2019 | Veterans Community Development | short | 970,000 | 515,000 | 7 | 455,000 | 0 | 455,000 |
| FY2019 | Support for Educators | short | 20,804,500 | 20,354,500 | 1 | 450,000 | 450,000 | 0 |
| FY2019 | Young Women's Leadership Development | short | 1,096,000 | 718,500 | 11 | 377,500 | 0 | 377,500 |
| FY2019 | Trans Equity Programs | short | 1,775,000 | 1,525,000 | 7 | 250,000 | 0 | 250,000 |
| FY2019 | Children Under Five | short | 1,002,000 | 757,000 | 6 | 245,000 | 0 | 245,000 |
| FY2019 | Mental Health Services for Veterans | short | 420,000 | 225,000 | 2 | 195,000 | 0 | 195,000 |
| FY2019 | Immigrant Health Initiative | short | 2,000,000 | 1,835,000 | 19 | 165,000 | 165,000 | 0 |
| FY2019 | Autism Awareness | short | 3,236,846 | 3,076,298 | 35 | 160,548 | 60,548 | 100,000 |
| FY2019 | Homeless Prevention Services for Veterans | short | 300,000 | 150,000 | 1 | 150,000 | 0 | 150,000 |
| FY2019 | Legal Services for Veterans | short | 450,000 | 300,000 | 2 | 150,000 | 0 | 150,000 |
| FY2019 | Initiative for Immigrant Survivors of Domestic Violence | over | 350,000 | 485,000 | 9 | -135,000 | 0 | -135,000 |
| FY2019 | Construction Site Safety Training | short | 1,100,000 | 975,000 | 8 | 125,000 | 125,000 | 0 |
| FY2019 | MWBE Leadership Associations | short | 600,000 | 478,550 | 7 | 121,450 | 0 | 121,450 |
| FY2019 | LGBTQ Inclusive Curriculum | short | 600,000 | 500,000 | 7 | 100,000 | 100,000 | 0 |
| FY2019 | Made in NYC | short | 850,000 | 750,000 | 1 | 100,000 | 0 | 100,000 |
| FY2019 | Immigrant Opportunities Initiative | short | 2,600,000 | 2,530,000 | 32 | 70,000 | 10,000 | 60,000 |
| FY2019 | Afterschool Enrichment Initiative | short | 6,303,907 | 6,235,000 | 8 | 68,907 | 0 | 68,907 |
| FY2019 | Support for Victims of Human Trafficking | short | 1,200,000 | 1,140,000 | 9 | 60,000 | 60,000 | 0 |
| FY2019 | Job Placement for Veterans | short | 200,000 | 150,000 | 1 | 50,000 | 0 | 50,000 |
| FY2019 | HIV/AIDS Faith Based | short | 1,131,000 | 1,105,318 | 13 | 25,682 | 61,701 | -36,019 |
| FY2020 | Domestic Violence and Empowerment (DoVE) Initiative | short | 9,805,000 | 620,000 | 13 | 9,185,000 | 0 | 9,185,000 |
| FY2020 | Community Schools | over | 3,750,000 | 11,153,800 | 12 | -7,403,800 | 0 | -7,403,800 |
| FY2020 | New York Immigrant Family Unity Project | short | 16,600,000 | 11,066,667 | 2 | 5,533,333 | 0 | 5,533,333 |
| FY2020 | Cultural After-School Adventure (CASA) | short | 17,340,000 | 12,540,000 | 627 | 4,800,000 | 0 | 4,800,000 |
| FY2020 | NYC Cleanup | short | 13,260,000 | 8,478,200 | 117 | 4,781,800 | 0 | 4,781,800 |
| FY2020 | Food Pantries | short | 5,659,000 | 1,000,000 | 1 | 4,659,000 | 0 | 4,659,000 |
| FY2020 | Coalition Theaters of Color | short | 3,740,000 | 350,400 | 6 | 3,389,600 | 0 | 3,389,600 |
| FY2020 | Cultural Immigrant Initiative | short | 7,395,000 | 5,074,000 | 259 | 2,321,000 | 0 | 2,321,000 |
| FY2020 | Support Our Seniors | short | 5,100,000 | 3,208,000 | 181 | 1,892,000 | 0 | 1,892,000 |
| FY2020 | Diversion Programs | short | 2,525,000 | 930,000 | 1 | 1,595,000 | 0 | 1,595,000 |
| FY2020 | Wrap-Around Support for Transitional-Aged Foster Youth | over | 1,230,000 | 2,696,125 | 32 | -1,466,125 | 0 | -1,466,125 |
| FY2020 | Borough Presidents’ Discretionary Funding Restoration | short | 1,129,774 | 100,000 | 2 | 1,029,774 | 0 | 1,029,774 |
| FY2020 | Unaccompanied Minors and Families | short | 3,981,800 | 3,016,800 | 5 | 965,000 | 0 | 965,000 |
| FY2020 | Digital Inclusion and Literacy Initiative | short | 3,060,000 | 2,340,000 | 103 | 720,000 | 0 | 720,000 |
| FY2020 | Discretionary Child Care | short | 5,405,190 | 4,731,108 | 6 | 674,082 | 0 | 674,082 |
| FY2020 | Neighborhood Development Grant Initiative | short | 2,040,000 | 1,368,000 | 65 | 672,000 | 0 | 672,000 |
| FY2020 | Naturally Occurring Retirement Communities (NORCs) | short | 5,325,325 | 4,741,294 | 37 | 584,031 | 0 | 584,031 |
| FY2020 | Ending the Epidemic | short | 7,735,000 | 7,161,200 | 67 | 573,800 | 0 | 573,800 |
| FY2020 | Maternal and Child Health Services | short | 2,192,818 | 1,631,117 | 13 | 561,701 | 0 | 561,701 |
| FY2020 | Worker Cooperative Business Development Initiative | short | 3,609,000 | 3,096,711 | 12 | 512,289 | 0 | 512,289 |
| FY2020 | Access Health | short | 3,000,000 | 2,500,000 | 36 | 500,000 | 0 | 500,000 |
| FY2020 | Legal Services for Low-Income New Yorkers | short | 5,800,000 | 5,300,000 | 5 | 500,000 | 0 | 500,000 |
| FY2020 | Healthy Aging Initiative | short | 2,040,000 | 1,589,000 | 108 | 451,000 | 0 | 451,000 |
| FY2020 | Legal Services for the Working Poor | short | 3,205,000 | 2,897,500 | 10 | 307,500 | 0 | 307,500 |
| FY2020 | Veterans Community Development | short | 1,270,000 | 970,000 | 9 | 300,000 | 0 | 300,000 |
| FY2020 | Discharge Planning | short | 800,000 | 550,000 | 2 | 250,000 | 0 | 250,000 |
| FY2020 | Reproductive and Sexual Health Services | short | 594,788 | 344,788 | 2 | 250,000 | 0 | 250,000 |
| FY2020 | College and Career Readiness | short | 1,778,000 | 1,578,000 | 8 | 200,000 | 0 | 200,000 |
| FY2020 | Prevent Sexual Assault (PSA) Initiative for Young Adults | short | 350,000 | 150,000 | 2 | 200,000 | 0 | 200,000 |
| FY2020 | Support for Victims of Human Trafficking | short | 1,200,000 | 1,025,000 | 9 | 175,000 | 0 | 175,000 |
| FY2020 | Citywide Homeless Prevention Fund | short | 820,000 | 656,000 | 2 | 164,000 | 0 | 164,000 |
| FY2020 | HIV/AIDS Faith Based | short | 1,131,000 | 999,000 | 24 | 132,000 | 0 | 132,000 |
| FY2020 | Initiative for Immigrant Survivors of Domestic Violence | short | 530,000 | 420,000 | 9 | 110,000 | 0 | 110,000 |
| FY2020 | Elder Abuse Prevention Programs | short | 335,000 | 235,000 | 3 | 100,000 | 0 | 100,000 |
| FY2020 | Mental Health Services for Vulnerable Populations | short | 2,318,000 | 2,219,000 | 20 | 99,000 | 0 | 99,000 |
| FY2020 | Initiative to Combat Sexual Assault | short | 3,210,000 | 3,112,000 | 13 | 98,000 | 0 | 98,000 |
| FY2020 | MWBE Leadership Associations | short | 600,000 | 511,145 | 8 | 88,855 | 0 | 88,855 |
| FY2020 | Mental Health Services for Veterans | short | 500,000 | 420,000 | 4 | 80,000 | 0 | 80,000 |
| FY2020 | Immigrant Opportunities Initiative | short | 2,600,000 | 2,535,000 | 32 | 65,000 | 0 | 65,000 |
| FY2020 | Dedicated Contraceptive Fund | short | 781,000 | 718,000 | 3 | 63,000 | 0 | 63,000 |
| FY2020 | Legal Services for Veterans | short | 600,000 | 550,000 | 5 | 50,000 | 0 | 50,000 |
| FY2021 | Domestic Violence and Empowerment (DoVE) Initiative | short | 9,805,000 | 1,672,500 | 20 | 8,132,500 | 0 | 8,132,500 |
| FY2021 | New York Immigrant Family Unity Project | short | 16,600,000 | 11,066,667 | 2 | 5,533,333 | 0 | 5,533,333 |
| FY2021 | Food Pantries | short | 5,659,000 | 1,000,000 | 1 | 4,659,000 | 0 | 4,659,000 |
| FY2021 | Coalition Theaters of Color | short | 3,740,000 | 1,389,000 | 21 | 2,351,000 | 0 | 2,351,000 |
| FY2021 | Adult Literacy Initiative | short | 3,400,000 | 1,196,124 | 15 | 2,203,876 | 0 | 2,203,876 |
| FY2021 | Autism Awareness | short | 3,246,846 | 1,361,483 | 15 | 1,885,363 | 0 | 1,885,363 |
| FY2021 | Access Health | short | 2,550,000 | 685,169 | 10 | 1,864,831 | 0 | 1,864,831 |
| FY2021 | Public Health Funding Backfill | short | 3,967,743 | 2,294,255 | 73 | 1,673,488 | 0 | 1,673,488 |
| FY2021 | Court-Involved Youth Mental Health | short | 2,890,000 | 1,241,850 | 10 | 1,648,150 | 0 | 1,648,150 |
| FY2021 | Parks Equity Initiative | short | 1,798,500 | 778,500 | 1 | 1,020,000 | 0 | 1,020,000 |
| FY2021 | Diversion Programs | over | 2,162,000 | 3,150,000 | 13 | -988,000 | 0 | -988,000 |
| FY2021 | Unaccompanied Minors and Families | short | 3,981,800 | 3,391,800 | 7 | 590,000 | 0 | 590,000 |
| FY2021 | Initiative for Immigrant Survivors of Domestic Violence | short | 477,000 | 112,500 | 3 | 364,500 | 0 | 364,500 |
| FY2021 | Innovative Criminal Justice Programs | short | 1,833,000 | 1,508,000 | 6 | 325,000 | 0 | 325,000 |
| FY2021 | Chamber on the Go and Small Business Assistance | short | 1,605,527 | 1,314,827 | 13 | 290,700 | 0 | 290,700 |
| FY2021 | LGBT Community Services | short | 3,166,250 | 2,902,750 | 14 | 263,500 | 0 | 263,500 |
| FY2021 | Veterans Community Development | short | 1,206,500 | 965,000 | 8 | 241,500 | 0 | 241,500 |
| FY2021 | Support for Victims of Human Trafficking | short | 1,200,000 | 975,000 | 8 | 225,000 | 0 | 225,000 |
| FY2021 | Legal Services for the Working Poor | short | 2,724,250 | 2,505,300 | 11 | 218,950 | 0 | 218,950 |
| FY2021 | Geriatric Mental Health | short | 1,619,709 | 1,408,909 | 20 | 210,800 | 0 | 210,800 |
| FY2021 | Prevent Sexual Assault (PSA) Initiative for Young Adults | short | 315,000 | 135,000 | 2 | 180,000 | 0 | 180,000 |
| FY2021 | Maternal and Child Health Services | short | 1,863,895 | 1,702,395 | 15 | 161,500 | 0 | 161,500 |
| FY2021 | Senior Centers, Programs, and Enhancements | short | 3,376,670 | 3,246,670 | 55 | 130,000 | 0 | 130,000 |
| FY2021 | City’s First Readers | short | 3,904,900 | 3,777,400 | 16 | 127,500 | 0 | 127,500 |
| FY2021 | CUNY Citizenship NOW! Program | short | 3,250,000 | 3,150,000 | 2 | 100,000 | 0 | 100,000 |
| FY2021 | Legal Services for Low-Income New Yorkers | short | 4,930,000 | 4,845,000 | 5 | 85,000 | 0 | 85,000 |
| FY2021 | Immigrant Opportunities Initiative | short | 2,600,000 | 2,520,000 | 32 | 80,000 | 0 | 80,000 |
| FY2021 | Mental Health Services for Veterans | short | 475,000 | 395,000 | 3 | 80,000 | 0 | 80,000 |
| FY2021 | Young Women's Leadership Development | short | 1,444,950 | 1,386,450 | 26 | 58,500 | 0 | 58,500 |
| FY2021 | Civic Education in New York City Schools | short | 467,500 | 425,000 | 1 | 42,500 | 0 | 42,500 |
| FY2021 | HIV/AIDS Faith Based | short | 961,350 | 951,150 | 24 | 10,200 | 0 | 10,200 |
| FY2022 | Food Pantries | short | 19,159,000 | 1,000,000 | 1 | 18,159,000 | 0 | 18,159,000 |
| FY2022 | New York Immigrant Family Unity Project | short | 16,600,000 | 11,066,667 | 2 | 5,533,333 | 0 | 5,533,333 |
| FY2022 | Parks Equity Initiative | short | 5,113,500 | 778,500 | 1 | 4,335,000 | 0 | 4,335,000 |
| FY2022 | City’s First Readers | over | 5,564,000 | 9,314,000 | 19 | -3,750,000 | 0 | -3,750,000 |
| FY2022 | Access Health | short | 4,000,000 | 680,888 | 8 | 3,319,112 | 0 | 3,319,112 |
| FY2022 | CUNY Research Institutes | short | 4,500,000 | 2,250,000 | 3 | 2,250,000 | 0 | 2,250,000 |
| FY2022 | LGBTQ Inclusive Curriculum | short | 2,800,000 | 700,000 | 7 | 2,100,000 | 0 | 2,100,000 |
| FY2022 | Geriatric Mental Health | short | 3,405,540 | 1,495,540 | 18 | 1,910,000 | 0 | 1,910,000 |
| FY2022 | Autism Awareness | short | 3,246,846 | 1,767,466 | 21 | 1,479,380 | 0 | 1,479,380 |
| FY2022 | Children Under Five | short | 2,502,000 | 1,114,350 | 10 | 1,387,650 | 0 | 1,387,650 |
| FY2022 | LGBTQ Senior Services in Every Borough | short | 1,500,000 | 280,000 | 1 | 1,220,000 | 0 | 1,220,000 |
| FY2022 | Communities of Color Nonprofit Stabilization Fund | short | 3,700,000 | 2,500,000 | 15 | 1,200,000 | 0 | 1,200,000 |
| FY2022 | Physical Education and Fitness | short | 2,175,000 | 1,050,000 | 2 | 1,125,000 | 0 | 1,125,000 |
| FY2022 | Innovative Criminal Justice Programs | short | 2,637,948 | 1,683,000 | 6 | 954,948 | 0 | 954,948 |
| FY2022 | Legal Services for the Working Poor | short | 3,205,000 | 2,327,500 | 8 | 877,500 | 0 | 877,500 |
| FY2022 | Young Women's Leadership Development | short | 1,805,500 | 1,165,125 | 21 | 640,375 | 0 | 640,375 |
| FY2022 | Unaccompanied Minors and Families | short | 3,981,800 | 3,391,800 | 7 | 590,000 | 0 | 590,000 |
| FY2022 | Mental Health Services for Vulnerable Populations | short | 2,338,000 | 1,800,300 | 20 | 537,700 | 0 | 537,700 |
| FY2022 | College and Career Readiness | short | 1,578,000 | 1,198,000 | 8 | 380,000 | 0 | 380,000 |
| FY2022 | Ending the Epidemic | over | 7,735,000 | 8,087,600 | 65 | -352,600 | 0 | -352,600 |
| FY2022 | Veterans Community Development | short | 1,270,000 | 970,000 | 8 | 300,000 | 0 | 300,000 |
| FY2022 | Support for Victims of Human Trafficking | short | 1,200,000 | 925,000 | 8 | 275,000 | 0 | 275,000 |
| FY2022 | HIV/AIDS Faith Based | short | 2,131,000 | 1,880,000 | 15 | 251,000 | 0 | 251,000 |
| FY2022 | Support for Educators | short | 4,400,000 | 4,150,000 | 2 | 250,000 | 0 | 250,000 |
| FY2022 | Step In and Stop It Initiative to Address Bystander Intervention | over | 174,000 | 398,375 | 5 | -224,375 | 0 | -224,375 |
| FY2022 | Viral Hepatitis Prevention | short | 1,923,658 | 1,717,447 | 30 | 206,211 | 0 | 206,211 |
| FY2022 | Prevent Sexual Assault (PSA) Initiative for Young Adults | short | 350,000 | 150,000 | 2 | 200,000 | 0 | 200,000 |
| FY2022 | Social and Emotional Supports for Students | short | 1,906,500 | 1,721,500 | 4 | 185,000 | 0 | 185,000 |
| FY2022 | Immigrant Health Initiative | short | 2,000,000 | 1,845,000 | 19 | 155,000 | 0 | 155,000 |
| FY2022 | Construction Site Safety Training | short | 1,100,000 | 975,000 | 8 | 125,000 | 0 | 125,000 |
| FY2022 | Job Training and Placement Initiative | short | 8,000,000 | 7,899,200 | 6 | 100,800 | 0 | 100,800 |
| FY2022 | CUNY Citizenship NOW! Program | short | 3,250,000 | 3,150,000 | 2 | 100,000 | 0 | 100,000 |
| FY2022 | Job Placement for Veterans | short | 200,000 | 100,000 | 1 | 100,000 | 0 | 100,000 |
| FY2022 | Initiative for Immigrant Survivors of Domestic Violence | short | 530,000 | 440,000 | 9 | 90,000 | 0 | 90,000 |
| FY2022 | MWBE Leadership Associations | short | 600,000 | 549,075 | 7 | 50,925 | 0 | 50,925 |
| FY2022 | Cancer Services | short | 599,500 | 549,500 | 6 | 50,000 | 0 | 50,000 |
| FY2022 | Civic Education in New York City Schools | short | 550,000 | 500,000 | 1 | 50,000 | 0 | 50,000 |
| FY2022 | Immigrant Opportunities Initiative | short | 2,600,000 | 2,553,000 | 31 | 47,000 | 0 | 47,000 |
| FY2022 | Legal Services for Veterans | short | 600,000 | 570,000 | 6 | 30,000 | 0 | 30,000 |
| FY2022 | Mental Health Services for Veterans | short | 500,000 | 470,000 | 4 | 30,000 | 0 | 30,000 |
| FY2022 | Dedicated Contraceptive Fund | short | 781,000 | 777,850 | 4 | 3,150 | 0 | 3,150 |
| FY2023 | Food Pantries | short | 7,630,203 | 1,000,000 | 1 | 6,630,203 | 0 | 6,630,203 |
| FY2023 | New York Immigrant Family Unity Project | short | 16,600,000 | 11,066,667 | 2 | 5,533,333 | 0 | 5,533,333 |
| FY2023 | Naturally Occurring Retirement Communities (NORCs) | short | 6,091,026 | 1,810,026 | 1 | 4,281,000 | 0 | 4,281,000 |
| FY2023 | Coalition Theaters of Color | short | 5,770,000 | 1,595,000 | 23 | 4,175,000 | 0 | 4,175,000 |
| FY2023 | Senior Centers, Programs, and Enhancements | short | 4,376,670 | 500,000 | 1 | 3,876,670 | 0 | 3,876,670 |
| FY2023 | Initiative to Combat Sexual Assault | short | 4,210,000 | 549,750 | 3 | 3,660,250 | 0 | 3,660,250 |
| FY2023 | City’s First Readers | short | 5,449,667 | 1,828,018 | 7 | 3,621,649 | 0 | 3,621,649 |
| FY2023 | Adult Literacy Initiative | short | 4,000,000 | 667,000 | 3 | 3,333,000 | 0 | 3,333,000 |
| FY2023 | Community Housing Preservation Strategies | short | 3,651,000 | 672,296 | 12 | 2,978,704 | 0 | 2,978,704 |
| FY2023 | Immigrant Health Initiative | short | 2,430,341 | 79,255 | 1 | 2,351,086 | 0 | 2,351,086 |
| FY2023 | Access Health | short | 3,699,179 | 1,491,583 | 15 | 2,207,596 | 0 | 2,207,596 |
| FY2023 | Autism Awareness | short | 3,316,846 | 1,301,483 | 15 | 2,015,363 | 0 | 2,015,363 |
| FY2023 | Low Wage Worker Support | short | 2,000,000 | 120,000 | 2 | 1,880,000 | 0 | 1,880,000 |
| FY2023 | Diversion Programs | short | 2,525,000 | 930,000 | 1 | 1,595,000 | 0 | 1,595,000 |
| FY2023 | Wrap-Around Support for Transitional-Aged Foster Youth | over | 1,230,000 | 2,619,500 | 33 | -1,389,500 | 0 | -1,389,500 |
| FY2023 | Supportive Alternatives to Violent Encounters (SAVE) | short | 2,450,000 | 1,600,000 | 2 | 850,000 | 0 | 850,000 |
| FY2023 | Physical Education and Fitness | short | 1,175,000 | 375,000 | 2 | 800,000 | 0 | 800,000 |
| FY2023 | Hate Crimes Prevention | short | 1,000,000 | 250,000 | 5 | 750,000 | 0 | 750,000 |
| FY2023 | Unaccompanied Minors and Families | short | 3,981,800 | 3,361,800 | 6 | 620,000 | 0 | 620,000 |
| FY2023 | Worker Cooperative Business Development Initiative | short | 3,768,208 | 3,255,919 | 12 | 512,289 | 0 | 512,289 |
| FY2023 | Chamber on the Go and Small Business Assistance | short | 2,388,855 | 1,904,274 | 12 | 484,581 | 0 | 484,581 |
| FY2023 | Ending the Epidemic | short | 9,553,030 | 9,098,092 | 46 | 454,938 | 0 | 454,938 |
| FY2023 | Opioid Prevention and Treatment | short | 3,500,000 | 3,100,000 | 17 | 400,000 | 0 | 400,000 |
| FY2023 | Food Access and Benefits | short | 1,500,000 | 1,116,000 | 6 | 384,000 | 0 | 384,000 |
| FY2023 | Community Land Trust | short | 1,500,000 | 1,228,500 | 14 | 271,500 | 0 | 271,500 |
| FY2023 | Children Under Five | short | 1,787,000 | 1,517,000 | 9 | 270,000 | 0 | 270,000 |
| FY2023 | Veterans Community Development | short | 1,270,000 | 1,016,000 | 9 | 254,000 | 0 | 254,000 |
| FY2023 | Job Training and Placement Initiative | short | 8,250,000 | 8,040,000 | 7 | 210,000 | 0 | 210,000 |
| FY2023 | Home Loan Program | short | 2,000,000 | 1,800,000 | 5 | 200,000 | 0 | 200,000 |
| FY2023 | Prevent Sexual Assault (PSA) Initiative for Young Adults | short | 350,000 | 150,000 | 2 | 200,000 | 0 | 200,000 |
| FY2023 | Senior Centers for Immigrant Populations | short | 1,500,000 | 1,350,000 | 9 | 150,000 | 0 | 150,000 |
| FY2023 | Immigrant Opportunities Initiative | short | 2,600,000 | 2,496,000 | 31 | 104,000 | 0 | 104,000 |
| FY2023 | CUNY Citizenship NOW! Program | short | 3,250,000 | 3,150,000 | 2 | 100,000 | 0 | 100,000 |
| FY2023 | Foreclosure Prevention Programs | short | 4,250,000 | 4,150,000 | 19 | 100,000 | 0 | 100,000 |
| FY2023 | Geriatric Mental Health | short | 3,405,540 | 3,305,540 | 34 | 100,000 | 0 | 100,000 |
| FY2023 | Innovative Criminal Justice Programs | short | 2,637,948 | 2,537,948 | 9 | 100,000 | 0 | 100,000 |
| FY2023 | Mental Health Services for Veterans | short | 500,000 | 400,000 | 4 | 100,000 | 0 | 100,000 |
| FY2023 | Trans Equity Programs | short | 3,275,000 | 3,200,000 | 14 | 75,000 | 0 | 75,000 |
| FY2023 | Homeless Prevention Services for Veterans | short | 300,000 | 240,000 | 1 | 60,000 | 0 | 60,000 |
| FY2023 | Educational Programs for Students | short | 7,143,133 | 7,093,133 | 10 | 50,000 | 0 | 50,000 |
| FY2023 | LGBT Community Services | short | 5,225,000 | 5,175,000 | 23 | 50,000 | 0 | 50,000 |
| FY2023 | Job Placement for Veterans | short | 200,000 | 160,000 | 1 | 40,000 | 0 | 40,000 |
| FY2023 | Social and Emotional Supports for Students | short | 1,916,500 | 1,916,000 | 5 | 500 | 0 | 500 |
| FY2024 | Domestic Violence and Empowerment (DoVE) Initiative | short | 12,010,000 | 816,923 | 14 | 11,193,077 | 0 | 11,193,077 |
| FY2024 | Afterschool Enrichment Initiative | short | 8,235,000 | 715,300 | 16 | 7,519,700 | 0 | 7,519,700 |
| FY2024 | Food Pantries | short | 7,260,000 | 1,059,000 | 3 | 6,201,000 | 0 | 6,201,000 |
| FY2024 | Coalition Theaters of Color | short | 5,715,000 | 1,510,000 | 21 | 4,205,000 | 0 | 4,205,000 |
| FY2024 | AAPI Community Support | short | 5,060,000 | 1,550,000 | 14 | 3,510,000 | 0 | 3,510,000 |
| FY2024 | Community Housing Preservation Strategies | short | 3,651,000 | 643,310 | 11 | 3,007,690 | 0 | 3,007,690 |
| FY2024 | Cultural After-School Adventure (CASA) | short | 17,340,000 | 14,860,000 | 742 | 2,480,000 | 0 | 2,480,000 |
| FY2024 | Autism Awareness | short | 3,261,846 | 812,054 | 11 | 2,449,792 | 0 | 2,449,792 |
| FY2024 | City’s First Readers | short | 5,449,667 | 3,300,650 | 10 | 2,149,017 | 0 | 2,149,017 |
| FY2024 | Mental Health Services for Vulnerable Populations | short | 3,663,000 | 1,899,000 | 27 | 1,764,000 | 0 | 1,764,000 |
| FY2024 | Support Our Older Adults (formerly Support Our Seniors) | short | 7,650,000 | 6,325,000 | 329 | 1,325,000 | 0 | 1,325,000 |
| FY2024 | Worker Cooperative Business Development Initiative | short | 3,768,208 | 2,612,598 | 9 | 1,155,610 | 0 | 1,155,610 |
| FY2024 | Crisis Management System | short | 3,770,600 | 2,725,600 | 39 | 1,045,000 | 0 | 1,045,000 |
| FY2024 | Cultural Immigrant Initiative | short | 7,395,000 | 6,525,000 | 348 | 870,000 | 0 | 870,000 |
| FY2024 | Naturally Occurring Retirement Communities (NORCs) | short | 5,181,768 | 4,385,654 | 30 | 796,114 | 0 | 796,114 |
| FY2024 | Chamber on the Go and Small Business Assistance | short | 2,252,267 | 1,484,897 | 11 | 767,370 | 0 | 767,370 |
| FY2024 | Trauma Recovery Centers | short | 2,400,000 | 1,783,415 | 4 | 616,585 | 0 | 616,585 |
| FY2024 | Digital Inclusion and Literacy Initiative | short | 4,590,000 | 3,990,000 | 180 | 600,000 | 0 | 600,000 |
| FY2024 | Viral Hepatitis Prevention | short | 2,247,454 | 1,688,726 | 24 | 558,728 | 0 | 558,728 |
| FY2024 | Education Equity Action Plan | short | 5,000,000 | 4,500,000 | 4 | 500,000 | 0 | 500,000 |
| FY2024 | Art a Catalyst for Change | short | 720,000 | 301,000 | 15 | 419,000 | 0 | 419,000 |
| FY2024 | Child Health and Wellness | short | 664,719 | 364,719 | 2 | 300,000 | 0 | 300,000 |
| FY2024 | Unaccompanied Minors and Families | short | 3,981,800 | 3,691,800 | 6 | 290,000 | 0 | 290,000 |
| FY2024 | YouthBuild Project Initiative | short | 1,750,000 | 1,472,000 | 10 | 278,000 | 0 | 278,000 |
| FY2024 | Young Women’s Leadership Development | short | 1,740,500 | 1,465,805 | 23 | 274,695 | 0 | 274,695 |
| FY2024 | Court-Involved Youth Mental Health | short | 3,425,000 | 3,175,000 | 20 | 250,000 | 0 | 250,000 |
| FY2024 | Geriatric Mental Health | short | 3,405,540 | 3,205,540 | 32 | 200,000 | 0 | 200,000 |
| FY2024 | Welcome NYC | short | 1,175,000 | 995,000 | 23 | 180,000 | 0 | 180,000 |
| FY2024 | Support for Victims of Human Trafficking | short | 1,075,000 | 900,000 | 8 | 175,000 | 0 | 175,000 |
| FY2024 | Elie Wiesel Holocaust Survivors | short | 4,200,000 | 4,031,000 | 25 | 169,000 | 0 | 169,000 |
| FY2024 | HIV/AIDS Faith Based | short | 1,966,311 | 1,827,147 | 29 | 139,164 | 0 | 139,164 |
| FY2024 | Immigrant Opportunities Initiative | short | 2,600,000 | 2,463,000 | 31 | 137,000 | 0 | 137,000 |
| FY2024 | Neighborhood Development Grant Initiative | over | 2,550,000 | 2,661,000 | 118 | -111,000 | 0 | -111,000 |
| FY2024 | Construction Site Safety Training | short | 1,100,000 | 1,000,000 | 8 | 100,000 | 0 | 100,000 |
| FY2024 | Innovative Criminal Justice Programs | short | 2,637,948 | 2,537,948 | 10 | 100,000 | 0 | 100,000 |
| FY2024 | Opioid Prevention and Treatment | short | 3,075,000 | 2,975,000 | 16 | 100,000 | 0 | 100,000 |
| FY2024 | Job Training and Placement Initiative | short | 8,450,000 | 8,375,000 | 8 | 75,000 | 0 | 75,000 |
| FY2024 | Trans Equity Programs | short | 3,225,000 | 3,150,000 | 13 | 75,000 | 0 | 75,000 |
| FY2024 | Initiative to Combat Sexual Assault | short | 4,160,000 | 4,091,000 | 16 | 69,000 | 0 | 69,000 |
| FY2024 | Pride at Work | over | 501,000 | 560,000 | 11 | -59,000 | 0 | -59,000 |
| FY2024 | Children Under Five | short | 1,556,231 | 1,521,231 | 11 | 35,000 | 0 | 35,000 |
| FY2025 | Domestic Violence and Empowerment (DoVE) Initiative | short | 12,010,000 | 297,693 | 6 | 11,712,307 | 0 | 11,712,307 |
| FY2025 | Discharge Planning | short | 9,450,000 | 350,000 | 1 | 9,100,000 | 0 | 9,100,000 |
| FY2025 | Food Pantries | short | 8,260,000 | 1,059,000 | 3 | 7,201,000 | 0 | 7,201,000 |
| FY2025 | New York Immigrant Family Unity Project | short | 16,600,000 | 11,066,667 | 2 | 5,533,333 | 0 | 5,533,333 |
| FY2025 | Information and Referral Services | over | 407,811 | 5,589,579 | 39 | -5,181,768 | 0 | -5,181,768 |
| FY2025 | Coalition Theaters of Color | short | 5,715,000 | 1,925,576 | 25 | 3,789,424 | 0 | 3,789,424 |
| FY2025 | Afterschool Enrichment Initiative | short | 8,235,000 | 4,880,000 | 21 | 3,355,000 | 0 | 3,355,000 |
| FY2025 | Access Health Initiative | short | 3,620,210 | 407,032 | 3 | 3,213,178 | 0 | 3,213,178 |
| FY2025 | AAPI Community Support | short | 5,060,000 | 2,140,000 | 20 | 2,920,000 | 0 | 2,920,000 |
| FY2025 | Community Housing Preservation Strategies | short | 3,651,000 | 801,352 | 15 | 2,849,648 | 0 | 2,849,648 |
| FY2025 | Cultural After-School Adventure (CASA) | short | 17,340,000 | 14,680,000 | 734 | 2,660,000 | 0 | 2,660,000 |
| FY2025 | Trauma Recovery Centers | short | 4,800,000 | 2,290,473 | 3 | 2,509,527 | 0 | 2,509,527 |
| FY2025 | Autism Awareness | short | 3,261,846 | 1,511,483 | 19 | 1,750,363 | 0 | 1,750,363 |
| FY2025 | Maternal and Child Health Services | over | 3,728,525 | 5,370,662 | 45 | -1,642,137 | 0 | -1,642,137 |
| FY2025 | NYC Cleanup | short | 14,280,000 | 12,700,000 | 196 | 1,580,000 | 0 | 1,580,000 |
| FY2025 | Community Composting | short | 6,245,000 | 4,745,000 | 13 | 1,500,000 | 0 | 1,500,000 |
| FY2025 | Crisis Management System | short | 3,770,600 | 2,685,000 | 29 | 1,085,600 | 0 | 1,085,600 |
| FY2025 | Mental Health Services for Vulnerable Populations | short | 3,613,000 | 2,744,000 | 35 | 869,000 | 0 | 869,000 |
| FY2025 | Cultural Immigrant Initiative | short | 7,395,000 | 6,640,000 | 380 | 755,000 | 0 | 755,000 |
| FY2025 | Support Our Older Adults | short | 7,650,000 | 6,900,000 | 376 | 750,000 | 0 | 750,000 |
| FY2025 | City’s First Readers | short | 5,449,667 | 4,699,992 | 14 | 749,675 | 0 | 749,675 |
| FY2025 | Unaccompanied Minors and Families | short | 3,981,800 | 3,361,800 | 6 | 620,000 | 0 | 620,000 |
| FY2025 | Worker Cooperative Business Development Initiative | short | 3,768,208 | 3,255,919 | 13 | 512,289 | 0 | 512,289 |
| FY2025 | LGBTQIA+ Inclusive Curriculum | short | 2,800,000 | 2,295,000 | 16 | 505,000 | 0 | 505,000 |
| FY2025 | Digital Inclusion and Literacy Initiative | short | 4,590,000 | 4,100,000 | 192 | 490,000 | 0 | 490,000 |
| FY2025 | Art a Catalyst for Change | short | 720,000 | 408,000 | 21 | 312,000 | 0 | 312,000 |
| FY2025 | Children and Families in NYC Homeless System | short | 1,350,000 | 1,095,000 | 5 | 255,000 | 0 | 255,000 |
| FY2025 | Neighborhood Development Grant Initiative | short | 2,550,000 | 2,300,000 | 124 | 250,000 | 0 | 250,000 |
| FY2025 | Immigrant Opportunities Initiative | short | 2,600,000 | 2,430,000 | 29 | 170,000 | 0 | 170,000 |
| FY2025 | Welcome NYC | short | 1,175,000 | 1,070,000 | 23 | 105,000 | 0 | 105,000 |
| FY2025 | CUNY Citizenship NOW! Program | short | 3,350,000 | 3,250,000 | 2 | 100,000 | 0 | 100,000 |
| FY2025 | Viral Hepatitis Prevention | short | 2,247,454 | 2,158,190 | 28 | 89,264 | 0 | 89,264 |
| FY2025 | Support for Victims of Human Trafficking | short | 1,075,000 | 1,000,000 | 8 | 75,000 | 0 | 75,000 |
| FY2025 | Initiative to Combat Sexual Assault | short | 4,160,000 | 4,091,000 | 16 | 69,000 | 0 | 69,000 |
| FY2025 | Pride at Work | short | 501,000 | 451,000 | 5 | 50,000 | 0 | 50,000 |
| FY2026 | New York Immigrant Family Unity Project | short | 24,900,000 | 11,066,667 | 2 | 13,833,333 | 0 | 13,833,333 |
| FY2026 | Unaccompanied Minors and Families | short | 16,481,800 | 3,361,800 | 6 | 13,120,000 | 0 | 13,120,000 |
| FY2026 | Domestic Violence and Empowerment (DoVE) Initiative | short | 12,010,000 | 549,693 | 10 | 11,460,307 | 0 | 11,460,307 |
| FY2026 | Food Pantries | short | 8,467,000 | 1,266,000 | 5 | 7,201,000 | 0 | 7,201,000 |
| FY2026 | Adult Literacy Forward (Formerly Adult Literacy Pilot Project) | over | 8,245,148 | 13,824,412 | 71 | -5,579,264 | 0 | -5,579,264 |
| FY2026 | NYC Cleanup | over | 14,280,000 | 19,575,000 | 211 | -5,295,000 | 0 | -5,295,000 |
| FY2026 | A Greener NYC | short | 5,100,000 | 108,085 | 4 | 4,991,915 | 0 | 4,991,915 |
| FY2026 | Substance Abuse Prevention and Intervention Specialists | over | 2,000,000 | 6,650,000 | 4 | -4,650,000 | 0 | -4,650,000 |
| FY2026 | Parks Equity Initiative | short | 5,368,500 | 1,067,300 | 12 | 4,301,200 | 0 | 4,301,200 |
| FY2026 | Coalition Theaters of Color | short | 5,715,000 | 1,874,530 | 25 | 3,840,470 | 0 | 3,840,470 |
| FY2026 | Afterschool Enrichment Initiative | short | 8,235,000 | 4,772,650 | 18 | 3,462,350 | 0 | 3,462,350 |
| FY2026 | Trans Equity Programs | short | 6,450,000 | 3,225,000 | 15 | 3,225,000 | 0 | 3,225,000 |
| FY2026 | Access Health Initiative | short | 3,620,210 | 515,866 | 4 | 3,104,344 | 0 | 3,104,344 |
| FY2026 | AAPI Community Support | short | 5,060,000 | 2,040,000 | 19 | 3,020,000 | 0 | 3,020,000 |
| FY2026 | Community Housing Preservation Strategies | short | 3,651,000 | 864,118 | 16 | 2,786,882 | 0 | 2,786,882 |
| FY2026 | Education Equity Action Plan | short | 7,500,000 | 4,750,000 | 5 | 2,750,000 | 0 | 2,750,000 |
| FY2026 | Autism Awareness | short | 3,261,846 | 1,142,746 | 14 | 2,119,100 | 0 | 2,119,100 |
| FY2026 | Chamber on the Go and Small Business Assistance | short | 2,252,267 | 258,506 | 2 | 1,993,761 | 0 | 1,993,761 |
| FY2026 | City’s First Readers | short | 5,449,667 | 4,114,932 | 13 | 1,334,735 | 0 | 1,334,735 |
| FY2026 | Cultural After-School Adventure (CASA) | short | 17,340,000 | 16,060,000 | 803 | 1,280,000 | 0 | 1,280,000 |
| FY2026 | Children Under Five | short | 1,556,231 | 450,769 | 3 | 1,105,462 | 0 | 1,105,462 |
| FY2026 | Estate Planning and Resolution Initiative (EPAR) | short | 2,000,000 | 965,000 | 16 | 1,035,000 | 0 | 1,035,000 |
| FY2026 | MCCAP Initiative | short | 2,014,114 | 1,014,114 | 13 | 1,000,000 | 0 | 1,000,000 |
| FY2026 | MWBE Leadership Associations | over | 600,000 | 1,450,000 | 8 | -850,000 | 0 | -850,000 |
| FY2026 | Cultural Immigrant Initiative | short | 7,395,000 | 6,783,000 | 383 | 612,000 | 0 | 612,000 |
| FY2026 | Worker Cooperative Business Development Initiative | short | 3,768,208 | 3,255,919 | 13 | 512,289 | 0 | 512,289 |
| FY2026 | LGBTQIA+ Inclusive Curriculum | short | 2,800,000 | 2,295,000 | 16 | 505,000 | 0 | 505,000 |
| FY2026 | Support Our Older Adults | short | 7,650,000 | 7,175,000 | 391 | 475,000 | 0 | 475,000 |
| FY2026 | Digital Inclusion and Literacy Initiative | short | 4,590,000 | 4,120,000 | 188 | 470,000 | 0 | 470,000 |
| FY2026 | Court-Involved Youth Mental Health | short | 3,425,000 | 3,225,000 | 20 | 200,000 | 0 | 200,000 |
| FY2026 | Neighborhood Development Grant Initiative | short | 2,550,000 | 2,360,000 | 125 | 190,000 | 0 | 190,000 |
| FY2026 | Social Adult Day Care | short | 1,505,556 | 1,338,272 | 8 | 167,284 | 0 | 167,284 |
| FY2026 | Stabilizing NYC | short | 3,700,000 | 3,540,000 | 19 | 160,000 | 0 | 160,000 |
| FY2026 | Pride at Work | short | 501,000 | 390,000 | 4 | 111,000 | 0 | 111,000 |
| FY2026 | CUNY Citizenship NOW! Program | short | 3,350,000 | 3,250,000 | 2 | 100,000 | 0 | 100,000 |
| FY2026 | Community Land Trust | short | 1,500,000 | 1,401,750 | 17 | 98,250 | 0 | 98,250 |
| FY2026 | Older Adult Clubs for Immigrant Populations | short | 1,500,000 | 1,425,000 | 10 | 75,000 | 0 | 75,000 |
| FY2026 | Welcome NYC (Formerly Key to the City and Welcome NYC) | short | 1,875,000 | 1,800,000 | 26 | 75,000 | 0 | 75,000 |
| FY2026 | Immigrant Opportunities Initiative | short | 2,600,000 | 2,535,000 | 31 | 65,000 | 0 | 65,000 |
| FY2026 | Mental Health Services for Vulnerable Populations | short | 3,669,020 | 3,639,020 | 41 | 30,000 | 0 | 30,000 |
| FY2026 | LGBTQIA+ Community Services | short | 5,200,000 | 5,175,000 | 23 | 25,000 | 0 | 25,000 |
| FY2027 | Food Pantries | short | 10,467,000 | 1,266,000 | 5 | 9,201,000 | 0 | 9,201,000 |
| FY2027 | Creative Arts Team | over | 400,000 | 5,650,000 | 7 | -5,250,000 | 0 | -5,250,000 |
| FY2027 | Peer Specialists Support | short | 4,500,000 | 200,000 | 2 | 4,300,000 | 0 | 4,300,000 |
| FY2027 | Older Adults Mental Health | over | 3,474,520 | 6,549,520 | 52 | -3,075,000 | 0 | -3,075,000 |
| FY2027 | Cultural After-School Adventure (CASA) | short | 17,340,000 | 15,620,000 | 781 | 1,720,000 | 0 | 1,720,000 |
| FY2027 | Developmental, Psychological and Behavioral Health Services | over | 2,255,493 | 3,255,493 | 20 | -1,000,000 | 0 | -1,000,000 |
| FY2027 | Educational Programs for Students | short | 8,943,133 | 7,943,133 | 20 | 1,000,000 | 0 | 1,000,000 |
| FY2027 | Opioid Prevention and Treatment | over | 3,075,000 | 4,025,000 | 29 | -950,000 | 0 | -950,000 |
| FY2027 | NYC Cleanup | short | 14,280,000 | 13,401,000 | 197 | 879,000 | 0 | 879,000 |
| FY2027 | Domestic Violence and Empowerment (DoVE) Initiative | short | 12,010,000 | 11,160,000 | 413 | 850,000 | 0 | 850,000 |
| FY2027 | Gender-Affirming Care for TGNCNBI Youth | short | 3,500,000 | 2,833,333 | 5 | 666,667 | 0 | 666,667 |
| FY2027 | A Greener NYC | short | 5,100,000 | 4,545,000 | 245 | 555,000 | 0 | 555,000 |
| FY2027 | Healthy Beginnings | short | 4,593,244 | 4,118,003 | 22 | 475,241 | 0 | 475,241 |
| FY2027 | HIV/AIDS Pathways to Care | short | 11,339,653 | 10,911,934 | 56 | 427,719 | 0 | 427,719 |
| FY2027 | Support Our Older Adults | short | 7,649,999 | 7,229,998 | 394 | 420,001 | 0 | 420,001 |
| FY2027 | Confronting Religious and Ethnic Discrimination at CUNY | over | 500,000 | 900,000 | 2 | -400,000 | 0 | -400,000 |
| FY2027 | Digital Inclusion and Literacy Initiative | short | 4,590,000 | 4,195,000 | 200 | 395,000 | 0 | 395,000 |
| FY2027 | Cultural Immigrant Initiative | short | 7,395,000 | 7,010,000 | 397 | 385,000 | 0 | 385,000 |
| FY2027 | Chamber on the Go and Small Business Assistance | short | 2,140,972 | 1,850,721 | 11 | 290,251 | 0 | 290,251 |
| FY2027 | BID Containerization | short | 1,987,721 | 1,702,768 | 19 | 284,953 | 0 | 284,953 |
| FY2027 | Parks Equity Initiative | short | 5,368,500 | 5,108,500 | 228 | 260,000 | 0 | 260,000 |
| FY2027 | Wrap-Around Support for Transitional-Aged Foster Youth | short | 1,096,788 | 871,708 | 7 | 225,080 | 0 | 225,080 |
| FY2027 | Neighborhood Development Grant Initiative | short | 2,550,000 | 2,335,000 | 131 | 215,000 | 0 | 215,000 |
| FY2027 | Court-Involved Youth Mental Health Initiative | short | 3,425,000 | 3,250,000 | 19 | 175,000 | 0 | 175,000 |
| FY2027 | Coalition Theaters of Color | short | 5,715,000 | 5,551,000 | 64 | 164,000 | 0 | 164,000 |
| FY2027 | City's First Readers | short | 5,449,667 | 5,296,553 | 17 | 153,114 | 0 | 153,114 |
| FY2027 | Naturally Occurring Retirement Communities (NORCs) | short | 5,181,768 | 5,033,124 | 35 | 148,644 | 0 | 148,644 |
| FY2027 | MWBE Leadership Associations | short | 700,000 | 553,155 | 6 | 146,845 | 0 | 146,845 |
| FY2027 | Violence Prevention and Intervention for Youth and Young Adults | short | 4,560,600 | 4,422,600 | 83 | 138,000 | 0 | 138,000 |
| FY2027 | Alternatives to Incarceration and Reentry Programs | short | 19,962,000 | 19,834,000 | 30 | 128,000 | 0 | 128,000 |
| FY2027 | Culturally Specific Gender Based Violence Initiative | short | 3,000,000 | 2,900,000 | 22 | 100,000 | 0 | 100,000 |
| FY2027 | LGBTQIA+ Youth Support and Services | short | 5,000,000 | 4,900,000 | 21 | 100,000 | 0 | 100,000 |
| FY2027 | Community Land Trust | short | 1,500,000 | 1,401,750 | 15 | 98,250 | 0 | 98,250 |
| FY2027 | Veterans Community Development | short | 1,270,000 | 1,178,000 | 10 | 92,000 | 0 | 92,000 |
| FY2027 | Immigrant Opportunities Initiative | short | 6,489,132 | 6,429,132 | 51 | 60,000 | 0 | 60,000 |
| FY2027 | Elder Abuse Prevention Programs | short | 335,000 | 285,000 | 6 | 50,000 | 0 | 50,000 |
| FY2027 | Mental Health Services for Vulnerable Populations | short | 3,669,020 | 3,619,020 | 43 | 50,000 | 0 | 50,000 |
| FY2027 | Mental Health Services for Veterans | short | 420,000 | 385,000 | 3 | 35,000 | 0 | 35,000 |
| FY2027 | Older Adult Centers, Programs, and Services | short | 3,733,226 | 3,703,226 | 34 | 30,000 | 0 | 30,000 |

## Per-file findings

| file | rows | EIN cov | hard | soft findings |
|---|---|---|---|---|
| `combined/all_years_awards.csv` | 33638 | 100% | 0 | duplicate: 148 duplicate row instance(s); e.g. x2: ['FY17', 'HOUSING', 'Housing', 'Community Housing Preservation Strategies']...; column_bleed: 74 suspected surname-in-organization residual(s); e.g. line 489: 'Hudson Guild'; org_prose: 22 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 7148: 'Funding to support a theater production for children of peop'; org_merged: 59 award row(s) with an EIN or `$` inside `organization` — row boundary lost, so `amount` may belong to a different org than `organization` names; e.g. line 697: 'Charles B. Wang Community Health Center, Inc. 13-2739694 * $' |
| `combined/all_years_initiatives.csv` | 2598 | — | 0 | — |
| `fy09/schedule_c/fy09_schedule_c_initiatives.csv` | 123 | — | 0 | — |
| `fy10/schedule_c/fy10_schedule_c_initiatives.csv` | 124 | — | 0 | — |
| `fy10/transparency-resolutions/fy10_transparency_all.csv` | 1788 | 100% | 0 | fiscal_year: 58 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1730 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['10', '2010-04-29', 'LocalInitiatives', '']... |
| `fy10/transparency-resolutions/reso01_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy10/transparency-resolutions/reso02_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy10/transparency-resolutions/reso03_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy10/transparency-resolutions/reso04_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy10/transparency-resolutions/reso05_transparency_designations.csv` | 86 | 100% | 0 | fiscal_year: 86 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso06_transparency_designations.csv` | 214 | 100% | 0 | fiscal_year: 214 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso07_transparency_designations.csv` | 195 | 100% | 0 | fiscal_year: 195 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso08_transparency_designations.csv` | 501 | 100% | 0 | fiscal_year: 501 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso09_transparency_designations.csv` | 317 | 100% | 0 | fiscal_year: 317 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso10_transparency_designations.csv` | 309 | 100% | 0 | fiscal_year: 58 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 251 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['10', '2010-04-29', 'LocalInitiatives', '']... |
| `fy10/transparency-resolutions/reso11_transparency_designations.csv` | 95 | 100% | 0 | fiscal_year: 95 row(s) with empty fiscal_year |
| `fy10/transparency-resolutions/reso12_transparency_designations.csv` | 71 | 100% | 0 | fiscal_year: 71 row(s) with empty fiscal_year |
| `fy11/schedule_c/fy11_schedule_c_initiatives.csv` | 110 | — | 0 | — |
| `fy11/transparency-resolutions/fy11_transparency_all.csv` | 1545 | 100% | 0 | fiscal_year: 26 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1519 row(s) with empty fiscal_year; duplicate: 2 duplicate row instance(s); e.g. x2: ['3', '2010-09-29', 'Food Pantries', '']... |
| `fy11/transparency-resolutions/reso01_transparency_designations.csv` | 262 | 100% | 0 | fiscal_year: 262 row(s) with empty fiscal_year |
| `fy11/transparency-resolutions/reso02_transparency_designations.csv` | 226 | 100% | 0 | fiscal_year: 226 row(s) with empty fiscal_year |
| `fy11/transparency-resolutions/reso03_transparency_designations.csv` | 435 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 427 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['3', '2010-09-29', 'Food Pantries', '']... |
| `fy11/transparency-resolutions/reso04_transparency_designations.csv` | 96 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 88 row(s) with empty fiscal_year |
| `fy11/transparency-resolutions/reso05_transparency_designations.csv` | 211 | 100% | 0 | fiscal_year: 211 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['5', '2010-11-17', 'HIV/AIDS-FaithBasedInitiative', '']... |
| `fy11/transparency-resolutions/reso06_transparency_designations.csv` | 190 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 184 row(s) with empty fiscal_year |
| `fy11/transparency-resolutions/reso07_transparency_designations.csv` | 125 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 121 row(s) with empty fiscal_year |
| `fy11/transparency-resolutions/reso08_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy11/transparency-resolutions/reso09_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy11/transparency-resolutions/reso10_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy12/schedule_c/fy12_schedule_c_initiatives.csv` | 97 | — | 0 | — |
| `fy12/transparency-resolutions/fy12_transparency_all.csv` | 932 | 100% | 0 | fiscal_year: 40 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 549 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2011-11-03', 'HIV/AIDS Faith Based Initiative (cont.)', '']...; column_bleed: 4 suspected surname-in-organization residual(s); e.g. line 118: 'Hudson Guild' |
| `fy12/transparency-resolutions/reso01_transparency_designations.csv` | 134 | 100% | 0 | fiscal_year: 134 row(s) with empty fiscal_year; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 118: 'Hudson Guild' |
| `fy12/transparency-resolutions/reso02_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy12/transparency-resolutions/reso03_transparency_designations.csv` | 168 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 162 row(s) with empty fiscal_year |
| `fy12/transparency-resolutions/reso04_transparency_designations.csv` | 258 | 100% | 0 | fiscal_year: 7 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 251 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2011-11-03', 'HIV/AIDS Faith Based Initiative (cont.)', '']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 49: 'Brewer WellnessintheSchools,Inc.' |
| `fy12/transparency-resolutions/reso05_transparency_designations.csv` | 42 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 2 row(s) with empty fiscal_year |
| `fy12/transparency-resolutions/reso06_transparency_designations.csv` | 200 | 100% | 0 | column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 156: 'Gennaro 11-2267876 Young Israel of Queens Valley' |
| `fy12/transparency-resolutions/reso07_transparency_designations.csv` | 130 | 100% | 0 | fiscal_year: 9 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy13/schedule_c/fy13_schedule_c_initiatives.csv` | 121 | — | 0 | — |
| `fy13/transparency-resolutions/fy13_transparency_all.csv` | 1857 | 100% | 0 | fiscal_year: 70 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 426 row(s) with empty fiscal_year; duplicate: 10 duplicate row instance(s); e.g. x2: ['2', '2012-08-22', 'YouthDiscretionary-Fiscal2013', '2013']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 547: 'Gennaro CatholicCharitiesNeighborhoodServices -Colin-NewellE' |
| `fy13/transparency-resolutions/reso01_transparency_designations.csv` | 587 | 100% | 0 | fiscal_year: 3 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 244 row(s) with empty fiscal_year; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 547: 'Gennaro CatholicCharitiesNeighborhoodServices -Colin-NewellE' |
| `fy13/transparency-resolutions/reso02_transparency_designations.csv` | 227 | 100% | 0 | fiscal_year: 3 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 128 row(s) with empty fiscal_year; duplicate: 2 duplicate row instance(s); e.g. x2: ['2', '2012-08-22', 'YouthDiscretionary-Fiscal2013', '2013']... |
| `fy13/transparency-resolutions/reso03_transparency_designations.csv` | 374 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 49 row(s) with empty fiscal_year; duplicate: 3 duplicate row instance(s); e.g. x2: ['3', '2012-09-24', 'Anti-GunViolenceInitiative-ConflictPreventionRemediation-FY2013', '']... |
| `fy13/transparency-resolutions/reso04_transparency_designations.csv` | 130 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['4', '2012-10-11', 'LocalInitiatives-Fiscal2013', '2013']... |
| `fy13/transparency-resolutions/reso05_transparency_designations.csv` | 215 | 100% | 0 | duplicate: 2 duplicate row instance(s); e.g. x2: ['5', '2012-11-13', 'HIV/AIDSFaithBasedInitiative-Fiscal2013', '2013']... |
| `fy13/transparency-resolutions/reso06_transparency_designations.csv` | 103 | 100% | 0 | — |
| `fy13/transparency-resolutions/reso08_transparency_designations.csv` | 55 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['8', '2013-01-23', 'LocalInitiatives-Fiscal2013', '2013']... |
| `fy13/transparency-resolutions/reso09_transparency_designations.csv` | 0 | 0% | 0 | — |
| `fy13/transparency-resolutions/reso12_transparency_designations.csv` | 166 | 100% | 0 | fiscal_year: 48 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 5 row(s) with empty fiscal_year |
| `fy14/schedule_c/fy14_schedule_c_initiatives.csv` | 123 | — | 0 | — |
| `fy14/transparency-resolutions/fy14_transparency_all.csv` | 166 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['1', '2014-04-29', 'CulturalAfterSchoolAdventure-Fiscal2014', '2014']... |
| `fy14/transparency-resolutions/reso01_transparency_designations.csv` | 36 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['1', '2014-04-29', 'CulturalAfterSchoolAdventure-Fiscal2014', '2014']... |
| `fy14/transparency-resolutions/reso02_transparency_designations.csv` | 80 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy14/transparency-resolutions/reso03_transparency_designations.csv` | 50 | 100% | 0 | — |
| `fy15/schedule_c/fy15_appendix_a_aging.csv` | 0 | 0% | 0 | — |
| `fy15/schedule_c/fy15_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy15/schedule_c/fy15_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy15/schedule_c/fy15_schedule_c_awards.csv` | 652 | 100% | 0 | column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 489: 'Hudson Guild' |
| `fy15/schedule_c/fy15_schedule_c_initiatives.csv` | 140 | — | 0 | — |
| `fy15/terms/fy15_terms_and_conditions.csv` | 17 | — | 0 | — |
| `fy15/transparency-resolutions/fy15_transparency_all.csv` | 3047 | 100% | 0 | fiscal_year: 160 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 23 duplicate row instance(s); e.g. x2: ['1', '2014-07-24', 'Local Initiatives - Fiscal 2015', '2015']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 1523: 'Hudson Guild' |
| `fy15/transparency-resolutions/reso01_transparency_designations.csv` | 291 | 100% | 0 | fiscal_year: 5 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['1', '2014-07-24', 'Local Initiatives - Fiscal 2015', '2015']... |
| `fy15/transparency-resolutions/reso02_transparency_designations.csv` | 548 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy15/transparency-resolutions/reso03_transparency_designations.csv` | 875 | 100% | 0 | fiscal_year: 42 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 5 duplicate row instance(s); e.g. x2: ['3', '2014-09-23', 'Local Initiatives - Fiscal 2015', '2015']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 684: 'Hudson Guild' |
| `fy15/transparency-resolutions/reso04_transparency_designations.csv` | 275 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2014-10-07', 'Local Initiatives - Fiscal 2015', '2015']... |
| `fy15/transparency-resolutions/reso05_transparency_designations.csv` | 121 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['5', '2014-10-22', 'Local Initiatives - Fiscal 2015', '2015']... |
| `fy15/transparency-resolutions/reso06_transparency_designations.csv` | 170 | 100% | 0 | fiscal_year: 11 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['6', '2014-11-25', 'FoodPantriesInitiative-Fiscal2015', '2015']... |
| `fy15/transparency-resolutions/reso07_transparency_designations.csv` | 284 | 100% | 0 | duplicate: 6 duplicate row instance(s); e.g. x2: ['7', '2014-12-17', 'Local Initiatives - Fiscal 2015', '2015']... |
| `fy15/transparency-resolutions/reso08_transparency_designations.csv` | 40 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy15/transparency-resolutions/reso09_transparency_designations.csv` | 117 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy15/transparency-resolutions/reso10_transparency_designations.csv` | 68 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy15/transparency-resolutions/reso11_transparency_designations.csv` | 178 | 100% | 0 | fiscal_year: 26 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['11', '2015-02-26', 'LocalInitiatives-Fiscal2014', '2014']... |
| `fy15/transparency-resolutions/reso12_transparency_designations.csv` | 80 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['12', '2015-03-31', 'Local Initiatives - Fiscal 2015', '2015']... |
| `fy16/schedule_c/fy16_appendix_a_aging.csv` | 0 | 0% | 0 | — |
| `fy16/schedule_c/fy16_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy16/schedule_c/fy16_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy16/schedule_c/fy16_schedule_c_awards.csv` | 335 | 100% | 0 | column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 302: 'Hudson Guild'; org_merged: 8 award row(s) with an EIN or `$` inside `organization` — row boundary lost, so `amount` may belong to a different org than `organization` names; e.g. line 45: 'Charles B. Wang Community Health Center, Inc. 13-2739694 * $' |
| `fy16/schedule_c/fy16_schedule_c_initiatives.csv` | 193 | — | 0 | — |
| `fy16/terms/fy16_terms_and_conditions.csv` | 30 | — | 0 | — |
| `fy16/transparency-resolutions/fy16_transparency_all.csv` | 4156 | 100% | 0 | fiscal_year: 92 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 9 row(s) with empty fiscal_year; duplicate: 28 duplicate row instance(s); e.g. x2: ['2', '2015-08-13', 'Local Initiatives - Fiscal 2016', '2016']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 729: 'Hudson Guild' |
| `fy16/transparency-resolutions/reso01_transparency_designations.csv` | 432 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy16/transparency-resolutions/reso02_transparency_designations.csv` | 431 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['2', '2015-08-13', 'Local Initiatives - Fiscal 2016', '2016']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 297: 'Hudson Guild' |
| `fy16/transparency-resolutions/reso03_transparency_designations.csv` | 883 | 100% | 0 | fiscal_year: 22 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 7 row(s) with empty fiscal_year; duplicate: 7 duplicate row instance(s); e.g. x2: ['3', '2015-09-17', 'Local Initiatives - Fiscal 2016', '2016']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 760: 'Joseph P. Addabbo Family Health Center, Inc.' |
| `fy16/transparency-resolutions/reso04_transparency_designations.csv` | 516 | 100% | 0 | — |
| `fy16/transparency-resolutions/reso05_transparency_designations.csv` | 315 | 100% | 0 | fiscal_year: 2 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 11 duplicate row instance(s); e.g. x3: ['5', '2015-10-15', 'Cultural After School Adventure (CASA) - Fiscal 2016', '2016']... |
| `fy16/transparency-resolutions/reso06_transparency_designations.csv` | 161 | 100% | 0 | column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 17: 'Williams Top Development Corporation** 11-3409359 Top Develo' |
| `fy16/transparency-resolutions/reso07_transparency_designations.csv` | 471 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['7', '2015-11-24', 'YouthDiscretionary-Fiscal2016', '2016']... |
| `fy16/transparency-resolutions/reso08_transparency_designations.csv` | 208 | 100% | 0 | fiscal_year: 14 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['8', '2015-12-16', 'Healthy Aging Initiative - Fiscal 2016', '2016']... |
| `fy16/transparency-resolutions/reso09_transparency_designations.csv` | 190 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy16/transparency-resolutions/reso10_transparency_designations.csv` | 186 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 2 row(s) with empty fiscal_year; duplicate: 1 duplicate row instance(s); e.g. x2: ['10', '2016-02-24', 'Anti-Gun Violence - Art a Catalyst for Change Initiative - Fiscal 2016', '2016']... |
| `fy16/transparency-resolutions/reso11_transparency_designations.csv` | 88 | 100% | 0 | duplicate: 2 duplicate row instance(s); e.g. x2: ['11', '2016-03-22', 'NYC Digital Inclusion and Literacy Initiative - Fiscal 2016', '2016']... |
| `fy16/transparency-resolutions/reso12_transparency_designations.csv` | 115 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy16/transparency-resolutions/reso13_transparency_designations.csv` | 160 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy17/schedule_c/fy17_appendix_a_aging.csv` | 0 | 0% | 0 | — |
| `fy17/schedule_c/fy17_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy17/schedule_c/fy17_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy17/schedule_c/fy17_schedule_c_awards.csv` | 364 | 100% | 0 | duplicate: 4 duplicate row instance(s); e.g. x2: ['HOUSING', 'Community Housing Preservation Strategies', 'initiative_provider', '']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 30: 'Hudson Guild'; org_merged: 20 award row(s) with an EIN or `$` inside `organization` — row boundary lost, so `amount` may belong to a different org than `organization` names; e.g. line 10: 'Jumpstart for Children 04-3263046 * $175,000 Literacy Inc. (' |
| `fy17/schedule_c/fy17_schedule_c_initiatives.csv` | 133 | — | 0 | — |
| `fy17/terms/fy17_terms_and_conditions.csv` | 30 | — | 0 | — |
| `fy17/transparency-resolutions/fy17_transparency_all.csv` | 4656 | 100% | 0 | fiscal_year: 213 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 2 row(s) with empty fiscal_year; duplicate: 50 duplicate row instance(s); e.g. x2: ['1', '2016-07-14', 'Cultural After-School Adventure (CASA) - Fiscal 2017', '2017']...; column_bleed: 4 suspected surname-in-organization residual(s); e.g. line 876: 'Mealy Reel Works Teen Film Making, Inc.' |
| `fy17/transparency-resolutions/reso01_transparency_designations.csv` | 684 | 100% | 0 | fiscal_year: 26 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 8 duplicate row instance(s); e.g. x2: ['1', '2016-07-14', 'Cultural After-School Adventure (CASA) - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso02_transparency_designations.csv` | 1019 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 9 duplicate row instance(s); e.g. x2: ['2', '2016-08-16', 'Local Initiatives - Fiscal 2017', '2017']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 192: 'Mealy Reel Works Teen Film Making, Inc.' |
| `fy17/transparency-resolutions/reso03_transparency_designations.csv` | 421 | 100% | 0 | fiscal_year: 41 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['3', '2016-09-14', 'NYC Cleanup - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso04_transparency_designations.csv` | 550 | 100% | 0 | fiscal_year: 2 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2016-09-28', 'Parks Equity Initiative - Fiscal 2017', '2017']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 472: 'Hudson Guild' |
| `fy17/transparency-resolutions/reso05_transparency_designations.csv` | 458 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 9 duplicate row instance(s); e.g. x2: ['5', '2016-10-27', 'Cultural After-School Adventure (CASA) - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso06_transparency_designations.csv` | 166 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy17/transparency-resolutions/reso07_transparency_designations.csv` | 332 | 100% | 0 | fiscal_year: 7 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 7 duplicate row instance(s); e.g. x2: ['7', '2016-12-15', 'Anti-Poverty Initiative - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso08_transparency_designations.csv` | 303 | 100% | 0 | fiscal_year: 7 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 2 row(s) with empty fiscal_year; duplicate: 2 duplicate row instance(s); e.g. x2: ['8', '2017-01-18', 'Parks Equity Initiative - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso09_transparency_designations.csv` | 161 | 100% | 0 | fiscal_year: 9 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy17/transparency-resolutions/reso10_transparency_designations.csv` | 122 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy17/transparency-resolutions/reso11_transparency_designations.csv` | 129 | 100% | 0 | fiscal_year: 2 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['11', '2017-03-16', 'Parks Equity Initiative - Fiscal 2017', '2017']... |
| `fy17/transparency-resolutions/reso12_transparency_designations.csv` | 130 | 100% | 0 | fiscal_year: 41 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy17/transparency-resolutions/reso13_transparency_designations.csv` | 181 | 100% | 0 | fiscal_year: 34 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['13', '2017-06-06', 'Youth Discretionary - Fiscal 2017', '2017']... |
| `fy18/schedule_c/fy18_appendix_a_aging.csv` | 422 | 100% | 0 | org_prose: 40 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 10: '.00 Funding will support the purchase of equipment and suppl'; org_merged: 5 award row(s) with an EIN or `$` inside `organization` — row boundary lost, so `amount` may belong to a different org than `organization` names; e.g. line 31: '.00 To provide funding for the Senior Healthy Eating and Wel' |
| `fy18/schedule_c/fy18_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy18/schedule_c/fy18_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy18/schedule_c/fy18_schedule_c_awards.csv` | 480 | 100% | 0 | duplicate: 7 duplicate row instance(s); e.g. x2: ['Housing', 'Community Housing Preservation Strategies', 'initiative_provider', '']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 181: 'Hudson Guild'; org_merged: 21 award row(s) with an EIN or `$` inside `organization` — row boundary lost, so `amount` may belong to a different org than `organization` names; e.g. line 2: 'A&G Early Child Care Community Network Inc. 47-2375867 * $2,' |
| `fy18/schedule_c/fy18_schedule_c_initiatives.csv` | 128 | — | 0 | — |
| `fy18/terms/fy18_terms_and_conditions.csv` | 33 | — | 0 | — |
| `fy18/transparency-resolutions/fy18_transparency_all.csv` | 5366 | 100% | 0 | fiscal_year: 345 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1 row(s) with empty fiscal_year; duplicate: 51 duplicate row instance(s); e.g. x2: ['1', '2017-06-21', 'Local Initiatives - Fiscal 2018', '2018']...; column_bleed: 4 suspected surname-in-organization residual(s); e.g. line 3262: 'Hudson Guild' |
| `fy18/transparency-resolutions/reso01_transparency_designations.csv` | 885 | 100% | 0 | fiscal_year: 25 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 9 duplicate row instance(s); e.g. x2: ['1', '2017-06-21', 'Local Initiatives - Fiscal 2018', '2018']... |
| `fy18/transparency-resolutions/reso02_transparency_designations.csv` | 808 | 100% | 0 | fiscal_year: 31 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['2', '2017-07-20', 'Parks Equity Initiative - Fiscal 2018', '2018']... |
| `fy18/transparency-resolutions/reso03_transparency_designations.csv` | 1176 | 100% | 0 | fiscal_year: 34 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 19 duplicate row instance(s); e.g. x2: ['3', '2017-08-24', 'Cultural After-School Adventure (CASA) - Fiscal 2018', '2018']... |
| `fy18/transparency-resolutions/reso04_transparency_designations.csv` | 462 | 100% | 0 | fiscal_year: 34 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 7 duplicate row instance(s); e.g. x2: ['4', '2017-09-27', 'Local Initiatives - Fiscal 2018', '2018']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 393: 'Hudson Guild' |
| `fy18/transparency-resolutions/reso05_transparency_designations.csv` | 503 | 100% | 0 | fiscal_year: 60 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['5', '2017-10-31', 'Local Initiatives - Fiscal 2018', '2018']... |
| `fy18/transparency-resolutions/reso06_transparency_designations.csv` | 299 | 100% | 0 | fiscal_year: 47 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['6', '2017-11-30', 'Purpose of Funds Changes - Fiscal 2018', '2018']... |
| `fy18/transparency-resolutions/reso07_transparency_designations.csv` | 231 | 100% | 0 | fiscal_year: 30 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 78: 'Louis Armstrong House Museum' |
| `fy18/transparency-resolutions/reso08_transparency_designations.csv` | 402 | 100% | 0 | fiscal_year: 48 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['8', '2018-02-15', 'Aging Discretionary - Fiscal 2018', '2018']...; column_bleed: 2 suspected surname-in-program residual(s); e.g. line 105: 'Hudson High School Of Learning Technologies (M437)' |
| `fy18/transparency-resolutions/reso09_transparency_designations.csv` | 181 | 100% | 0 | fiscal_year: 2 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1 row(s) with empty fiscal_year |
| `fy18/transparency-resolutions/reso10_transparency_designations.csv` | 88 | 100% | 0 | — |
| `fy18/transparency-resolutions/reso11_transparency_designations.csv` | 83 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy18/transparency-resolutions/reso12_transparency_designations.csv` | 248 | 100% | 0 | fiscal_year: 16 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['12', '2018-06-14', 'Local Initiatives - Fiscal 2018', '2018']... |
| `fy19/schedule_c/fy19_appendix_a_aging.csv` | 0 | 0% | 0 | — |
| `fy19/schedule_c/fy19_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy19/schedule_c/fy19_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy19/schedule_c/fy19_schedule_c_awards.csv` | 846 | 100% | 0 | duplicate: 2 duplicate row instance(s); e.g. x2: ['HOUSING', 'Community Housing Preservation Strategies', 'initiative_provider', '']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 318: 'Joseph P. Addabbo Family Health Center, Inc., The'; org_merged: 10 award row(s) with an EIN or `$` inside `organization` — row boundary lost, so `amount` may belong to a different org than `organization` names; e.g. line 110: "LifeWay Network, Inc. 20-8645579 * $60,000 Mayor's Office of" |
| `fy19/schedule_c/fy19_schedule_c_initiatives.csv` | 133 | — | 0 | — |
| `fy19/transparency-resolutions/fy19_transparency_all.csv` | 7090 | 100% | 0 | fiscal_year: 713 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 74 duplicate row instance(s); e.g. x3: ['1', '2018-07-18', 'Local Initiatives - Fiscal 2019', '2019']...; column_bleed: 18 suspected surname-in-organization residual(s); e.g. line 1419: 'Hudson Guild' |
| `fy19/transparency-resolutions/reso01_transparency_designations.csv` | 1702 | 100% | 0 | fiscal_year: 78 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 21 duplicate row instance(s); e.g. x3: ['1', '2018-07-18', 'Local Initiatives - Fiscal 2019', '2019']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 1419: 'Hudson Guild' |
| `fy19/transparency-resolutions/reso02_transparency_designations.csv` | 1562 | 100% | 0 | fiscal_year: 26 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 13 duplicate row instance(s); e.g. x2: ['2', '2018-08-08', 'Local Initiatives - Fiscal 2019', '2019']...; column_bleed: 7 suspected surname-in-organization residual(s); e.g. line 204: 'Ayala Young Audiences New York, Inc.' |
| `fy19/transparency-resolutions/reso03_transparency_designations.csv` | 1064 | 100% | 0 | fiscal_year: 35 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 9 duplicate row instance(s); e.g. x2: ['3', '2018-09-26', 'Cultural Immigrant Initiative - Fiscal 2019', '2019']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 746: 'Ayala New York City Housing Authority' |
| `fy19/transparency-resolutions/reso04_transparency_designations.csv` | 591 | 100% | 0 | fiscal_year: 94 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 11 duplicate row instance(s); e.g. x2: ['4', '2018-10-31', 'Aging Discretionary - Fiscal 2019', '2019']...; column_bleed: 3 suspected surname-in-program residual(s); e.g. line 212: 'Hudson High School Of Learning Technologies' |
| `fy19/transparency-resolutions/reso05_transparency_designations.csv` | 913 | 100% | 0 | fiscal_year: 346 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 11 duplicate row instance(s); e.g. x2: ['5', '2018-12-11', 'Anti-Poverty Initiative - Fiscal 2019', '2019']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 203: 'Rivera Educational Alliance, Inc.' |
| `fy19/transparency-resolutions/reso06_transparency_designations.csv` | 89 | 100% | 0 | fiscal_year: 22 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['6', '2018-12-20', 'Local Initiatives - Fiscal 2017', '2017']... |
| `fy19/transparency-resolutions/reso07_transparency_designations.csv` | 337 | 100% | 0 | fiscal_year: 20 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 80: 'Powers Midtown Management Group, Inc.' |
| `fy19/transparency-resolutions/reso08_transparency_designations.csv` | 349 | 100% | 0 | fiscal_year: 68 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 3 duplicate row instance(s); e.g. x2: ['8', '2019-02-28', 'Boroughwide Needs Initiative - Fiscal 2018', '2018']... |
| `fy19/transparency-resolutions/reso09_transparency_designations.csv` | 285 | 100% | 0 | duplicate: 3 duplicate row instance(s); e.g. x2: ['9', '2019-03-28', 'Local Initiatives - Fiscal 2019', '2019']...; column_bleed: 3 suspected surname-in-program residual(s); e.g. line 18: 'Louis Armstrong World Festival' |
| `fy19/transparency-resolutions/reso10_transparency_designations.csv` | 131 | 100% | 0 | fiscal_year: 20 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['10', '2019-04-18', 'Local Initiatives - Fiscal 2019', '2019']... |
| `fy19/transparency-resolutions/reso11_transparency_designations.csv` | 67 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy20/capital/fy20_capital_projects.csv` | 1663 | — | 0 | — |
| `fy20/schedule_c/fy20_appendix_a_aging.csv` | 0 | 0% | 0 | — |
| `fy20/schedule_c/fy20_appendix_b_local.csv` | 0 | 0% | 0 | — |
| `fy20/schedule_c/fy20_appendix_c_youth.csv` | 0 | 0% | 0 | — |
| `fy20/schedule_c/fy20_schedule_c_awards.csv` | 2841 | 100% | 0 | duplicate: 29 duplicate row instance(s); e.g. x2: ['Community Development', 'Digital Inclusion and Literacy Initiative', 'member_item', 'Ayala']...; column_bleed: 12 suspected surname-in-organization residual(s); e.g. line 107: 'Hudson Guild' |
| `fy20/schedule_c/fy20_schedule_c_initiatives.csv` | 137 | — | 0 | — |
| `fy20/transparency-resolutions/fy20_transparency_all.csv` | 5319 | 100% | 0 | fiscal_year: 207 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 41 duplicate row instance(s); e.g. x2: ['1', '2019-07-23', 'Local Initiatives - Fiscal 2020', '2020']...; column_bleed: 11 suspected surname-in-program residual(s); e.g. line 57: 'Louis Armstrong Tenant Association' |
| `fy20/transparency-resolutions/reso01_transparency_designations.csv` | 1361 | 100% | 0 | fiscal_year: 28 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 8 duplicate row instance(s); e.g. x2: ['1', '2019-07-23', 'Local Initiatives - Fiscal 2020', '2020']...; column_bleed: 1 suspected surname-in-program residual(s); e.g. line 57: 'Louis Armstrong Tenant Association' |
| `fy20/transparency-resolutions/reso02_transparency_designations.csv` | 1268 | 100% | 0 | fiscal_year: 13 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 13 duplicate row instance(s); e.g. x2: ['2', '2019-08-14', 'Cultural After-School Adventure (CASA) - Fiscal 2020', '2020']...; column_bleed: 4 suspected surname-in-program residual(s); e.g. line 34: 'Hudson River Park Estuary Lab Levine (Environmental Educatio' |
| `fy20/transparency-resolutions/reso03_transparency_designations.csv` | 1062 | 100% | 0 | fiscal_year: 28 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 7 duplicate row instance(s); e.g. x2: ['3', '2019-09-25', 'Local Initiatives - Fiscal 2020', '2020']... |
| `fy20/transparency-resolutions/reso04_transparency_designations.csv` | 539 | 100% | 0 | fiscal_year: 76 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['4', '2019-11-14', 'Anti-Poverty Initiative - Fiscal 2020', '2020']...; column_bleed: 2 suspected surname-in-program residual(s); e.g. line 78: 'Louis Armstrong Tenant Association' |
| `fy20/transparency-resolutions/reso05_transparency_designations.csv` | 557 | 100% | 0 | fiscal_year: 46 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 5 duplicate row instance(s); e.g. x2: ['5', '2019-12-19', 'Cultural After-School Adventure (CASA) - Fiscal 2020', '2020']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 115: 'Louis Armstrong House Museum' |
| `fy20/transparency-resolutions/reso06_transparency_designations.csv` | 176 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-program residual(s); e.g. line 10: 'Williams Plaza Tenant Association' |
| `fy20/transparency-resolutions/reso07_transparency_designations.csv` | 233 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['7', '2020-02-27', 'Digital Inclusion and Literacy Initiative - Fiscal 2020', '2020']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 16: 'Hudson River Park Trust' |
| `fy20/transparency-resolutions/reso08_transparency_designations.csv` | 123 | 100% | 0 | — |
| `fy21/schedule_c/fy21_appendix_a_aging.csv` | 514 | 100% | 0 | org_prose: 2 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 382: 'To support programming for seniors at the RiseBoro Breevort ' |
| `fy21/schedule_c/fy21_appendix_b_local.csv` | 2902 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Richards', 'Queens Borough Public Library', 'Arverne Library', '136400434']...; column_bleed: 9 suspected surname-in-organization residual(s); e.g. line 24: 'Adams Street Foundation, Inc.'; org_prose: 4 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 716: 'Funds will be used to promote Cypriot folk arts radio progra' |
| `fy21/schedule_c/fy21_appendix_c_youth.csv` | 894 | 100% | 0 | column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 416: 'Hudson Guild'; org_prose: 5 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 101: 'To provide funding to support the teen interns participating' |
| `fy21/schedule_c/fy21_schedule_c_awards.csv` | 1810 | 100% | 0 | duplicate: 4 duplicate row instance(s); e.g. x2: ['Boroughwide Needs', '', 'member_item', 'Brooklyn']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 1031: 'Hudson Guild'; org_prose: 3 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 1630: 'Funding to support a theater production for children of peop' |
| `fy21/schedule_c/fy21_schedule_c_initiatives.csv` | 124 | — | 0 | — |
| `fy21/terms/fy21_terms_and_conditions.csv` | 46 | — | 0 | — |
| `fy21/transparency-resolutions/fy21_transparency_all.csv` | 4463 | 100% | 0 | fiscal_year: 126 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 18 duplicate row instance(s); e.g. x2: ['1', '2020-08-27', 'Local Initiatives - Fiscal 2021', '2021']...; column_bleed: 9 suspected surname-in-organization residual(s); e.g. line 628: 'Louis Armstrong House Museum' |
| `fy21/transparency-resolutions/reso01_transparency_designations.csv` | 2414 | 100% | 0 | fiscal_year: 58 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['1', '2020-08-27', 'Local Initiatives - Fiscal 2021', '2021']...; column_bleed: 5 suspected surname-in-organization residual(s); e.g. line 628: 'Louis Armstrong House Museum' |
| `fy21/transparency-resolutions/reso02_transparency_designations.csv` | 705 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['2', '2020-09-23', 'Cultural After-School Adventure (CASA) - Fiscal 2021', '2021']... |
| `fy21/transparency-resolutions/reso03_transparency_designations.csv` | 249 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['3', '2020-10-29', 'Cultural After-School Adventure (CASA) - Fiscal 2021', '2021']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 76: 'Louis Midtown Management Group, Inc.' |
| `fy21/transparency-resolutions/reso04_transparency_designations.csv` | 184 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy21/transparency-resolutions/reso05_transparency_designations.csv` | 226 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x3: ['5', '2020-12-17', 'Local Initiatives - Fiscal 2021', '2021']... |
| `fy21/transparency-resolutions/reso06_transparency_designations.csv` | 218 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['6', '2021-02-25', 'Youth Discretionary - Fiscal 2021', '2021']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 113: 'Holden Colonial Farmhouse Restoration Society of Bellerose, ' |
| `fy21/transparency-resolutions/reso07_transparency_designations.csv` | 312 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['7', '2021-04-22', 'Aging Discretionary - Fiscal 2021', '2021']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 114: 'Gennaro Department of Parks and Recreation' |
| `fy21/transparency-resolutions/reso08_transparency_designations.csv` | 155 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['8', '2021-06-30', 'Local Initiatives - Fiscal 2021', '2021']... |
| `fy22/capital/fy22_capital_projects.csv` | 1641 | — | 0 | amount: line 1635: fy1 negative -72,000 (capital expected >= 0) |
| `fy22/schedule_c/fy22_appendix_a_aging.csv` | 510 | 100% | 0 | org_prose: 4 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 75: 'Funds will be used to support educational and health promoti' |
| `fy22/schedule_c/fy22_appendix_b_local.csv` | 2790 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Eugene', 'Prospect Lefferts Gardens Neighborhood Association, Inc.', '', '237064386']...; column_bleed: 8 suspected surname-in-organization residual(s); e.g. line 1211: 'Gennaro, Jewish Hatzoloh Incorporated'; org_prose: 20 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 67: 'To provide for the enrollment of individuals in Council Dist' |
| `fy22/schedule_c/fy22_appendix_c_youth.csv` | 882 | 100% | 0 | column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 411: 'Hudson Guild'; org_prose: 12 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 38: 'funding will support a basketball program and ELA Test Prepa' |
| `fy22/schedule_c/fy22_schedule_c_awards.csv` | 1492 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Speaker’s Initiative to Address Citywide Needs', 'Speaker’s Initiative to Address Citywide Needs', 'initiative_provider', '']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 817: 'Hudson Guild'; org_prose: 6 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 1201: 'Support new permanent installations in four family shelters ' |
| `fy22/schedule_c/fy22_schedule_c_initiatives.csv` | 138 | — | 0 | — |
| `fy22/terms/fy22_terms_and_conditions.csv` | 50 | — | 0 | — |
| `fy22/transparency-resolutions/fy22_transparency_all.csv` | 7768 | 100% | 0 | fiscal_year: 134 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 40 duplicate row instance(s); e.g. x3: ['1', '2021-07-29', 'Local Initiatives - Fiscal 2022', '2022']...; column_bleed: 18 suspected surname-in-organization residual(s); e.g. line 168: 'Holden Outstanding Renewal Enterprises, Inc.' |
| `fy22/transparency-resolutions/reso01_transparency_designations.csv` | 1432 | 100% | 0 | fiscal_year: 33 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 9 duplicate row instance(s); e.g. x3: ['1', '2021-07-29', 'Local Initiatives - Fiscal 2022', '2022']...; column_bleed: 8 suspected surname-in-organization residual(s); e.g. line 168: 'Holden Outstanding Renewal Enterprises, Inc.' |
| `fy22/transparency-resolutions/reso02_transparency_designations.csv` | 2147 | 100% | 0 | fiscal_year: 24 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 14 duplicate row instance(s); e.g. x2: ['2', '2021-08-26', 'Local Initiatives - Fiscal 2022', '2022']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 746: 'Louis Armstrong House Museum' |
| `fy22/transparency-resolutions/reso03_transparency_designations.csv` | 1464 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['3', '2021-09-23', 'Viral Hepatitis Prevention- Fiscal 2022', '2022']...; column_bleed: 4 suspected surname-in-organization residual(s); e.g. line 649: 'Hudson River Community Sailing, Inc.' |
| `fy22/transparency-resolutions/reso04_transparency_designations.csv` | 512 | 100% | 0 | fiscal_year: 5 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2021-10-07', 'Cultural After-School Adventure (CASA) - Fiscal 2022', '2022']... |
| `fy22/transparency-resolutions/reso05_transparency_designations.csv` | 335 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['5', '2021-10-21', 'Local Initiatives - Fiscal 2022', '2022']... |
| `fy22/transparency-resolutions/reso06_transparency_designations.csv` | 280 | 100% | 0 | — |
| `fy22/transparency-resolutions/reso07_transparency_designations.csv` | 264 | 100% | 0 | fiscal_year: 8 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy22/transparency-resolutions/reso08_transparency_designations.csv` | 268 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['8', '2021-12-09', 'Aging Discretionary - Fiscal 2022', '2022']... |
| `fy22/transparency-resolutions/reso09_transparency_designations.csv` | 301 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['9', '2021-12-15', 'Art a Catalyst for Change - Fiscal 2022', '2022']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 144: 'Joseph P. Addabbo Family Health Center, Inc.' |
| `fy22/transparency-resolutions/reso10_transparency_designations.csv` | 383 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 7 duplicate row instance(s); e.g. x2: ['10', '2022-03-10', 'A Greener NYC - Fiscal 2022', '2022']... |
| `fy22/transparency-resolutions/reso11_transparency_designations.csv` | 156 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 71: 'Louis Armstrong House Museum' |
| `fy22/transparency-resolutions/reso12_transparency_designations.csv` | 126 | 100% | 0 | fiscal_year: 14 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy22/transparency-resolutions/reso13_transparency_designations.csv` | 66 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy22/transparency-resolutions/reso14_transparency_designations.csv` | 34 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['14', '2022-06-13', 'SU-CASA - Fiscal 2022', '2022']... |
| `fy23/capital/fy23_capital_projects.csv` | 1547 | — | 0 | — |
| `fy23/schedule_c/fy23_appendix_a_aging.csv` | 489 | 100% | 0 | org_prose: 2 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 377: 'Funds will be used to enhance educational and health promoti' |
| `fy23/schedule_c/fy23_appendix_b_local.csv` | 2726 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Brooks-Powers', 'Queens Borough Public Library', 'Laurelton Library', '136400434']...; column_bleed: 13 suspected surname-in-organization residual(s); e.g. line 158: "Brannan, Brooklyn, Hanif Asiyah Women's Center"; org_prose: 22 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 124: 'Funds will be used to create Programs for Holocaust Survivor' |
| `fy23/schedule_c/fy23_appendix_c_youth.csv` | 841 | 100% | 0 | column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 410: 'Hudson Guild'; org_prose: 6 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 353: 'Funds will support High School Based Programs at the Monroe ' |
| `fy23/schedule_c/fy23_schedule_c_awards.csv` | 1848 | 100% | 0 | duplicate: 6 duplicate row instance(s); e.g. x3: ['BOROUGHWIDE NEEDS', '', 'member_item', 'Manhattan']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 1425: "Hudson, Narcisse, Women's Campaign Against Hunger, Inc., The"; org_prose: 2 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 1502: 'To provide funding to support virtual community that provide' |
| `fy23/schedule_c/fy23_schedule_c_initiatives.csv` | 143 | — | 0 | — |
| `fy23/terms/fy23_terms_and_conditions.csv` | 60 | — | 0 | — |
| `fy23/transparency-resolutions/fy23_transparency_all.csv` | 8354 | 100% | 0 | amount: line 6896: designate amount 0 (expected > 0); amount: line 6897: designate amount 0 (expected > 0); fiscal_year: 544 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 11 row(s) with empty fiscal_year; duplicate: 43 duplicate row instance(s); e.g. x2: ['1', '2022-07-14', 'Youth Discretionary - Fiscal 2023', '2023']...; column_bleed: 12 suspected surname-in-program residual(s); e.g. line 407: 'Hudson River Park Project' |
| `fy23/transparency-resolutions/reso01_transparency_designations.csv` | 1759 | 100% | 0 | fiscal_year: 130 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 2 row(s) with empty fiscal_year; duplicate: 7 duplicate row instance(s); e.g. x2: ['1', '2022-07-14', 'Youth Discretionary - Fiscal 2023', '2023']...; column_bleed: 2 suspected surname-in-program residual(s); e.g. line 407: 'Hudson River Park Project' |
| `fy23/transparency-resolutions/reso02_transparency_designations.csv` | 1736 | 100% | 0 | fiscal_year: 35 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['2', '2022-08-11', 'Youth Discretionary - Fiscal 2023', '2023']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 963: 'Hudson Guild' |
| `fy23/transparency-resolutions/reso03_transparency_designations.csv` | 1562 | 100% | 0 | fiscal_year: 51 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 15 duplicate row instance(s); e.g. x2: ['3', '2022-09-29', 'Local Initiatives - Fiscal 2023', '2023']...; column_bleed: 4 suspected surname-in-organization residual(s); e.g. line 177: 'Hudson River Community Sailing, Inc.' |
| `fy23/transparency-resolutions/reso04_transparency_designations.csv` | 807 | 100% | 0 | fiscal_year: 83 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['4', '2022-10-27', 'Anti-Poverty Initiative - Fiscal 2023', '2023']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 182: 'Louis Armstrong House Museum' |
| `fy23/transparency-resolutions/reso05_transparency_designations.csv` | 423 | 100% | 0 | fiscal_year: 78 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 4 duplicate row instance(s); e.g. x2: ['5', '2022-11-22', 'Art a Catalyst for Change - Fiscal 2023', '2023']... |
| `fy23/transparency-resolutions/reso06_transparency_designations.csv` | 432 | 100% | 0 | fiscal_year: 56 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['6', '2022-12-21', 'Community Safety and Victim Services Initiative - Fiscal 2023', '2023']... |
| `fy23/transparency-resolutions/reso07_transparency_designations.csv` | 201 | 100% | 0 | amount: line 177: designate amount 0 (expected > 0); amount: line 178: designate amount 0 (expected > 0); fiscal_year: 24 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy23/transparency-resolutions/reso08_transparency_designations.csv` | 556 | 100% | 0 | fiscal_year: 20 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['8', '2023-02-02', 'Local Initiatives - Fiscal 2023', '2023']... |
| `fy23/transparency-resolutions/reso09_transparency_designations.csv` | 144 | 100% | 0 | fiscal_year: 16 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 9 row(s) with empty fiscal_year |
| `fy23/transparency-resolutions/reso10_transparency_designations.csv` | 254 | 100% | 0 | fiscal_year: 16 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['10', '2023-03-02', 'Local Initiatives - Fiscal 2023', '2023']... |
| `fy23/transparency-resolutions/reso11_transparency_designations.csv` | 137 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy23/transparency-resolutions/reso12_transparency_designations.csv` | 208 | 100% | 0 | fiscal_year: 21 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 54: 'Hudson Guild' |
| `fy23/transparency-resolutions/reso13_transparency_designations.csv` | 25 | 100% | 0 | fiscal_year: 4 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy23/transparency-resolutions/reso14_transparency_designations.csv` | 110 | 100% | 0 | fiscal_year: 6 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy24/capital/fy24_capital_projects.csv` | 1364 | — | 0 | amount: line 1287: fy1 negative -40,000 (capital expected >= 0) |
| `fy24/schedule_c/fy24_appendix_a_aging.csv` | 477 | 100% | 0 | — |
| `fy24/schedule_c/fy24_appendix_b_local.csv` | 2616 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Restler', 'Department of Education', 'Urban Assembly Institute of Math and Science for Young Women (K527)', '136400434']...; column_bleed: 9 suspected surname-in-organization residual(s); e.g. line 381: "Sanchez, Women's Brooklyn Legal Services Corporation A"; org_prose: 1 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 568: 'at CCNY. It will support public events focuses on LGBTQ+ the' |
| `fy24/schedule_c/fy24_appendix_c_youth.csv` | 818 | 100% | 0 | column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 408: 'Hudson Guild' |
| `fy24/schedule_c/fy24_schedule_c_awards.csv` | 5368 | 100% | 0 | duplicate: 28 duplicate row instance(s); e.g. x2: ['CULTURAL ORGANIZATIONS', 'Cultural After-School Adventure (CASA)', 'member_item', 'Williams']...; column_bleed: 12 suspected surname-in-organization residual(s); e.g. line 394: 'Hudson Guild'; org_prose: 4 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 4845: 'Funds will be used for referrals from the family courts, sch' |
| `fy24/schedule_c/fy24_schedule_c_initiatives.csv` | 146 | — | 0 | — |
| `fy24/terms/fy24_terms_and_conditions.csv` | 59 | — | 0 | — |
| `fy24/transparency-resolutions/fy24_transparency_all.csv` | 3294 | 100% | 0 | fiscal_year: 215 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 28 duplicate row instance(s); e.g. x2: ['1', '2023-08-03', 'Community Safety and Victim Services Initiative - Fiscal 2024', '2024']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 212: 'Rivera Outstanding Renewal Enterprises, Inc.' |
| `fy24/transparency-resolutions/reso01_transparency_designations.csv` | 790 | 100% | 0 | fiscal_year: 16 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 5 duplicate row instance(s); e.g. x2: ['1', '2023-08-03', 'Community Safety and Victim Services Initiative - Fiscal 2024', '2024']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 212: 'Rivera Outstanding Renewal Enterprises, Inc.' |
| `fy24/transparency-resolutions/reso02_transparency_designations.csv` | 953 | 100% | 0 | fiscal_year: 53 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 6 duplicate row instance(s); e.g. x2: ['2', '2023-09-14', 'Food Pantries - Fiscal 2024', '2024']... |
| `fy24/transparency-resolutions/reso03_transparency_designations.csv` | 327 | 100% | 0 | fiscal_year: 30 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy24/transparency-resolutions/reso04_transparency_designations.csv` | 280 | 100% | 0 | fiscal_year: 13 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 11 duplicate row instance(s); e.g. x2: ['4', '2023-11-02', 'Cultural After-School Adventure (CASA) - Fiscal 2024', '2024']... |
| `fy24/transparency-resolutions/reso05_transparency_designations.csv` | 212 | 100% | 0 | fiscal_year: 20 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 97: 'Hanks Waterfront Alliance, Inc.' |
| `fy24/transparency-resolutions/reso06_transparency_designations.csv` | 126 | 100% | 0 | fiscal_year: 15 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['6', '2024-02-08', 'Local Initiatives - Fiscal 2024', '2024']... |
| `fy24/transparency-resolutions/reso07_transparency_designations.csv` | 369 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['7', '2024-04-11', 'Local Initiatives - Fiscal 2024', '2024']... |
| `fy24/transparency-resolutions/reso08_transparency_designations.csv` | 161 | 100% | 0 | fiscal_year: 42 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['8', '2024-05-23', 'Domestic Violence and Empowerment (DoVE) Initiative - Fiscal 2023', '2023']... |
| `fy24/transparency-resolutions/reso09_transparency_designations.csv` | 76 | 100% | 0 | fiscal_year: 14 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy25/capital/fy25_capital_projects.csv` | 1508 | — | 0 | — |
| `fy25/schedule_c/fy25_appendix_a_aging.csv` | 470 | 100% | 0 | — |
| `fy25/schedule_c/fy25_appendix_b_local.csv` | 2616 | 100% | 0 | column_bleed: 6 suspected surname-in-organization residual(s); e.g. line 650: 'Abreu, BLAC Community League of the Heights, Inc.' |
| `fy25/schedule_c/fy25_appendix_c_youth.csv` | 834 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Salaam', 'Figure Skating in Harlem, Inc.', '', '133945168']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 407: 'Hudson Guild' |
| `fy25/schedule_c/fy25_schedule_c_awards.csv` | 5646 | 100% | 0 | duplicate: 18 duplicate row instance(s); e.g. x3: ['CULTURAL ORGANIZATION', 'Cultural After-School Adventure (CASA)', 'member_item', 'Williams']...; column_bleed: 10 suspected surname-in-program residual(s); e.g. line 212: 'Louis Pink Houses TA Programming'; org_prose: 3 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 5134: 'Funding will be used to support operation of The Bronx Night' |
| `fy25/schedule_c/fy25_schedule_c_initiatives.csv` | 158 | — | 0 | — |
| `fy25/terms/fy25_terms_and_conditions.csv` | 65 | — | 0 | — |
| `fy26/capital/fy26_capital_projects.csv` | 1456 | — | 0 | amount: line 1336: fy1 negative -183,000 (capital expected >= 0) |
| `fy26/schedule_c/fy26_appendix_a_aging.csv` | 473 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Salaam', 'Catholic Managed Long Term Care, Inc.', '', '208180809']... |
| `fy26/schedule_c/fy26_appendix_b_local.csv` | 2618 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Salaam', 'New York Interfaith Commission for Housing Equality, Inc.', '', '993367298']...; column_bleed: 14 suspected surname-in-organization residual(s); e.g. line 52: 'Carr, Hanks Albanian-American Association of Ulqin, Inc.' |
| `fy26/schedule_c/fy26_appendix_c_youth.csv` | 823 | 100% | 0 | column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 415: 'Hudson Guild' |
| `fy26/schedule_c/fy26_schedule_c_awards.csv` | 5838 | 100% | 0 | duplicate: 15 duplicate row instance(s); e.g. x2: ['CULTURAL ORGANIZATIONS', 'Cultural After-School Adventure (CASA)', 'member_item', 'Williams']...; column_bleed: 11 suspected surname-in-program residual(s); e.g. line 200: 'Louis Armstrong Houses TA Association'; org_prose: 3 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 5076: "Funding to support Bridge Street Development's Tenant and Ho" |
| `fy26/schedule_c/fy26_schedule_c_initiatives.csv` | 157 | — | 0 | — |
| `fy26/terms/fy26_terms_and_conditions.csv` | 68 | — | 0 | — |
| `fy26/transparency-resolutions/fy26_transparency_all.csv` | 4755 | 100% | 0 | fiscal_year: 326 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1 row(s) with empty fiscal_year; duplicate: 36 duplicate row instance(s); e.g. x2: ['1', '2025-08-14', 'Local Initiatives - Fiscal 2026', '2026']...; column_bleed: 9 suspected surname-in-organization residual(s); e.g. line 533: 'Brannan Edith and Carl Marks Jewish Community House of Benso' |
| `fy26/transparency-resolutions/reso01_transparency_designations.csv` | 985 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error); fiscal_year: 1 row(s) with empty fiscal_year; duplicate: 10 duplicate row instance(s); e.g. x2: ['1', '2025-08-14', 'Local Initiatives - Fiscal 2026', '2026']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 533: 'Brannan Edith and Carl Marks Jewish Community House of Benso' |
| `fy26/transparency-resolutions/reso02_transparency_designations.csv` | 1638 | 100% | 0 | fiscal_year: 31 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 18 duplicate row instance(s); e.g. x2: ['2', '2025-09-25', 'Local Initiatives - Fiscal 2026', '2026']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 453: 'Mealy Department of Parks and Recreation' |
| `fy26/transparency-resolutions/reso03_transparency_designations.csv` | 832 | 100% | 0 | fiscal_year: 168 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 1 duplicate row instance(s); e.g. x2: ['3', '2025-10-29', 'Local Initiatives - Fiscal 2025', '2025']...; column_bleed: 2 suspected surname-in-organization residual(s); e.g. line 461: 'Hudson Square District Management Association, Inc.' |
| `fy26/transparency-resolutions/reso04_transparency_designations.csv` | 487 | 100% | 0 | fiscal_year: 10 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 3 duplicate row instance(s); e.g. x2: ['4', '2025-11-25', 'Support Our Older Adults - Fiscal 2026', '2026']... |
| `fy26/transparency-resolutions/reso05_transparency_designations.csv` | 162 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error); column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 133: 'Hudson Square District Management Association, Inc.' |
| `fy26/transparency-resolutions/reso06_transparency_designations.csv` | 190 | 100% | 0 | fiscal_year: 14 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['6', '2026-02-12', 'Local Initiatives - Fiscal 2026', '2026']... |
| `fy26/transparency-resolutions/reso07_transparency_designations.csv` | 78 | 100% | 0 | fiscal_year: 18 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy26/transparency-resolutions/reso08_transparency_designations.csv` | 91 | 100% | 0 | fiscal_year: 16 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy26/transparency-resolutions/reso09_transparency_designations.csv` | 141 | 100% | 0 | fiscal_year: 12 prior-year row(s) embedded (EXPECTED for transparency; not an error) |
| `fy26/transparency-resolutions/reso10_transparency_designations.csv` | 151 | 100% | 0 | fiscal_year: 27 prior-year row(s) embedded (EXPECTED for transparency; not an error); duplicate: 2 duplicate row instance(s); e.g. x2: ['10', '2026-06-30', 'Local Initiatives - Fiscal 2023', '2023']...; column_bleed: 1 suspected surname-in-organization residual(s); e.g. line 87: "Hudson Yards Hell's Kitchen Business Improvement District, I" |
| `fy27/capital/fy27_capital_projects.csv` | 1388 | — | 0 | — |
| `fy27/schedule_c/fy27_appendix_a_aging.csv` | 467 | 100% | 0 | — |
| `fy27/schedule_c/fy27_appendix_b_local.csv` | 2558 | 100% | 0 | duplicate: 2 duplicate row instance(s); e.g. x2: ['Hanks', 'Grace Foundation of New York', 'Council District 49', '134131863']...; column_bleed: 11 suspected surname-in-organization residual(s); e.g. line 70: 'Brewer, Caban, LGBTQIA+ American Museum of Lesbian Gay Bisex' |
| `fy27/schedule_c/fy27_appendix_c_youth.csv` | 835 | 100% | 0 | duplicate: 1 duplicate row instance(s); e.g. x2: ['Paladino', 'New York Sun Works, Inc.', 'Hydroponic Classrooms - Public School 094Q David D. Porter (26Q094)', '200670312']...; column_bleed: 3 suspected surname-in-program residual(s); e.g. line 361: 'Joseph Miccio Community Center Cornerstone Programs - Counci' |
| `fy27/schedule_c/fy27_schedule_c_awards.csv` | 6118 | 100% | 0 | duplicate: 34 duplicate row instance(s); e.g. x2: ['Cultural Organizations', 'Cultural After-School Adventure (CASA)', 'member_item', 'Abreu']...; column_bleed: 12 suspected surname-in-program residual(s); e.g. line 203: 'Louis Armstrong Houses TA Association'; org_prose: 1 award row(s) whose `organization` holds purpose prose instead of a grantee name — `ein` and `amount` are intact, the display name is lost; e.g. line 5925: 'Funding to assist low-income individuals and families in Cou' |
| `fy27/schedule_c/fy27_schedule_c_initiatives.csv` | 170 | — | 0 | — |
| `fy27/terms/fy27_terms_and_conditions.csv` | 75 | — | 0 | — |
| `recovered/schedule_c_absorbed_awards.csv` | 443 | 100% | 0 | duplicate: 6 duplicate row instance(s); e.g. x2: ['2017', 'HOUSING', 'Community Housing Preservation Strategies', 'initiative_provider']...; column_bleed: 3 suspected surname-in-organization residual(s); e.g. line 18: 'Hudson Guild' |

### Notes on the soft heuristics

- **Column-bleed** is a *suspected*-residual heuristic: it flags an organization/program field whose leading token is one of 47 surnames drawn from the transparency `council_member` column (boroughs/agencies excluded). Because that source column itself carries some bleed, the set is imperfect and the check has known FALSE POSITIVES — organizations whose real name simply begins with such a token (e.g. `Hudson Guild`, `Joseph P. Addabbo Family Health Center`). Genuine residuals look like `Brewer ParentsofPublicSchool9,Inc.` (a member surname prepended to a glued-word org). Treat this column as a review queue, not a defect list; the repo has no authoritative council-member roster to validate against.
- **Capital negative amounts**: the §254 books are *Changes to the Capital Budget*, so a negative FY amount (a de-appropriation/reduction) can be legitimate. Flagged for review, not treated as an error.
- **Transparency prior-year rows**: a resolution routinely amends *earlier* years' designations, so `fiscal_year` values below the folder year are expected and counted, not flagged.

