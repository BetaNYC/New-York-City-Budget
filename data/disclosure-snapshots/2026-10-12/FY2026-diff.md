# Disclosure snapshot diff — FY2026

- old: `funded_disclosure_FY2026.xlsx (sha256 4691c42bd3e7)`
- new: `funded_disclosure_FY2026.xlsx (sha256 81651e599ad6)`
- paired rows: 11,702 (11,571 by MOCS ID, the rest by the composite key); added 62; removed 55
- rows that could not use a MOCS ID (blank or repeated within a snapshot): old 0, new 0
- ambiguous composite groups: 0 (0 rows) — the pairing inside these is a choice; their transitions are counts, not row-to-row facts

This compares two files. It is not a statement by the Council about what changed.

## Totals by status

| status | old rows | old $ | new rows | new $ | Δ rows | Δ $ |
|---|---:|---:|---:|---:|---:|---:|
| cleared | 11,612 | 707,372,205 | 11,658 | 708,776,879 | +46 | +1,404,674 |
| pending | 145 | 8,840,950 | 106 | 7,436,276 | -39 | -1,404,674 |
| other | 0 | 0 | 0 | 0 | +0 | +0 |
| **all** | 11,757 | 716,213,155 | 11,764 | 716,213,155 | +7 | +0 |

## Status transitions

| from | to | rows |
|---|---|---:|
| pending | cleared | 19 |

## Amount changes (MOCS-ID pairs) — 29

| MOCS ID | EIN | legal name | old $ | new $ | Δ $ |
|---|---|---|---:|---:|---:|
| FY26 00589 | 112557794 | Broad Channel Volunteers, Inc. | 370,000 | 191,150 | -178,850 |
| FY26 07907 | 136400434 | Department of Parks and Recreation | 31,250 | 30,000 | -1,250 |
| FY26 10878 | 133179546 | Food Bank For New York City | 12,500 | 11,618 | -882 |
| FY26 11027 | 133179546 | Food Bank For New York City | 5,000 | 2,620 | -2,380 |
| FY26 11045 | 133179546 | Food Bank For New York City | 20,000 | 14,769 | -5,231 |
| FY26 11148 | 133179546 | Food Bank For New York City | 12,000 | 8,377 | -3,623 |
| FY26 11151 | 133179546 | Food Bank For New York City | 8,138 | 6,643 | -1,495 |
| FY26 11658 | 133740434 | 125th Street District Management Association, Inc. | 64,000 | 53,245 | -10,755 |
| FY26 11663 | 133846431 | Association of Community Employment Programs for the Homeless, Inc. | 1,000,000 | 153,277 | -846,723 |
| FY26 11667 | 270834463 | Belmont District Management Association, Inc. | 30,000 | 28,204 | -1,796 |
| FY26 11671 | 800356502 | Central Fulton Street District Management Association, Inc. | 25,000 | 18,691 | -6,309 |
| FY26 11674 | 200214837 | DUMBO District Management Association, Inc. | 100,000 | 70,895 | -29,105 |
| FY26 11678 | 112908148 | Flatbush Avenue District Management Association | 29,620 | 29,619 | -1 |
| FY26 11684 | 133455415 | HUB-Third Ave Merchants District Management Association, Inc. | 20,000 | 13,413 | -6,587 |
| FY26 11687 | 112977052 | Kings Highway District Management Association, Inc. | 38,000 | 31,650 | -6,350 |
| FY26 11689 | 133922300 | Lincoln Square District Management Association, Inc. | 22,161 | 22,110 | -51 |
| FY26 11691 | 810788036 | Meatpacking District Management Association | 150,000 | 137,346 | -12,654 |
| FY26 11695 | 202659913 | Myrtle Avenue Brooklyn DMA, Inc. | 40,000 | 39,000 | -1,000 |
| FY26 11696 | 112912570 | Myrtle Avenue District Management Association | 37,999 | 34,892 | -3,107 |
| FY26 11698 | 112764038 | North Flatbush Avenue District Management Association, Inc. | 35,000 | 30,450 | -4,550 |
| FY26 11702 | 113067330 | Steinway Street District Management Association, Inc. | 65,000 | 25,000 | -40,000 |
| FY26 11705 | 300253124 | Sutphin Boulevard District Management Association, Inc. | 36,000 | 25,533 | -10,467 |
| FY26 11708 | 133004730 | Union Square Partnership, Inc. | 85,000 | 81,345 | -3,655 |
| FY26 11710 | 383873130 | Westchester Square District Management Association, Inc. | 40,000 | 23,444 | -16,556 |
| FY26 11711 | 113149139 | Woodhaven District Management Association, Inc. | 25,000 | 24,079 | -921 |
| FY26 11783 | 133919295 | NOHO NY District Management Association, Inc. | 20,000 | 12,200 | -7,800 |
| FY26 11785 | 471044631 | SoHo Broadway District Management Association, Inc. | 150,000 | 119,906 | -30,094 |
| FY26 12133 | 136400434 | Department for the Aging | 100,000 | 70,000 | -30,000 |
| FY26 12179 | 136400434 | Department of Youth and Community Development | 5,000 | 4,000 | -1,000 |

Other fields changed on MOCS-ID pairs: `agency` 3, `council_member` 159, `program_name` 4, `purpose` 5, `source` 2

## Re-numbered (paired by the composite key; MOCS ID differs) — 131

The same designation under a different MOCS ID: every composite-key field (EIN, amount, agency, program, source) agrees. Paired, not counted as a removal plus an addition. The council member is not part of the key; a member change on such a pair is counted below the table.

| old prefix | new prefix | rows |
|---|---|---:|
| `FY26` | `FY26GP` | 131 |

| old MOCS ID | new MOCS ID | EIN | legal name | status (old → new) | amount |
|---|---|---|---|---|---:|
| FY26 00038 | FY26GP 00038 | 131835632 | A Chance In Life | cleared → cleared | 10,000 |
| FY26 00082 | FY26GP 00082 | 833055037 | Aid for Life International, Inc. | cleared → cleared | 5,000 |
| FY26 00116 | FY26GP 00116 | 934601552 | Allerton Allies Community Fridge, Inc. | cleared → cleared | 10,000 |
| FY26 00134 | FY26GP 00134 | 823132682 | Alopecian Beauty Co | cleared → cleared | 5,000 |
| FY26 00144 | FY26GP 00144 | 911792864 | Alzheimer's Foundation of America | cleared → cleared | 5,000 |
| FY26 00162 | FY26GP 00162 | 136272129 | American Legion Post 398 Colonel Charles Young, Inc. | cleared → cleared | 7,000 |
| FY26 00205 | FY26GP 00205 | 882634587 | Angellyh Yambo Foundation, Inc. | cleared → cleared | 5,000 |
| FY26 00367 | FY26GP 00367 | 464377279 | Barbershop Books, Inc. | cleared → cleared | 5,000 |
| FY26 00417 | FY26GP 00417 | 237413087 | Belle Harbor Property Owners Association, Inc. | cleared → cleared | 5,000 |
| FY26 00431 | FY26GP 00431 | 924025778 | Besi Association, Inc. | cleared → cleared | 20,000 |
| FY26 00440 | FY26GP 00440 | 923630891 | Beyond Educational Enrichment, Inc. | cleared → cleared | 10,000 |
| FY26 00624 | FY26GP 00624 | 454010209 | Bronx Giants Youth Football and Cheer, Inc. | cleared → cleared | 10,000 |
| FY26 00774 | FY26GP 00774 | 111532426 | Brooklyn Queens Conservatory of Music | cleared → cleared | 10,000 |
| FY26 00782 | FY26GP 00782 | 112739496 | Brooklyn Tech Alumni Foundation, Inc. | cleared → cleared | 5,000 |
| FY26 00804 | FY26GP 00804 | 942952782 | Buddhist Tzu Chi Foundation | cleared → cleared | 5,000 |
| FY26 00805 | FY26GP 00805 | 991778940 | Building 26 Association, Inc. | cleared → cleared | 5,000 |
| FY26 00811 | FY26GP 00811 | 264546315 | Bushwick Starr, Inc. | cleared → cleared | 10,000 |
| FY26 00819 | FY26GP 00819 | 112503313 | CABS Home Attendants Service, Inc. | cleared → cleared | 5,000 |
| FY26 00820 | FY26GP 00820 | 112503313 | CABS Home Attendants Service, Inc. | cleared → cleared | 10,000 |
| FY26 00821 | FY26GP 00821 | 112503313 | CABS Home Attendants Service, Inc. | cleared → cleared | 10,000 |
| FY26 00840 | FY26GP 00840 | 842906456 | Camino Al Arte | cleared → cleared | 20,500 |
| FY26 00844 | FY26GP 00844 | 112358083 | Canaan Senior Service Center, Inc. | cleared → cleared | 5,000 |
| FY26 00845 | FY26GP 00845 | 921209875 | Cannabis Justice & Equity Initiative Corporation | cleared → cleared | 10,000 |
| FY26 00853 | FY26GP 00853 | 841712162 | Caregivers Outreach Ministry Empowerment, Inc. | cleared → cleared | 10,000 |
| FY26 00860 | FY26GP 00860 | 112778372 | Caribbean American Sports and Cultural Youth Movement (CASYM), Inc. | cleared → cleared | 15,000 |
| FY26 00941 | FY26GP 00941 | 208180809 | Catholic Managed Long Term Care, Inc. | cleared → cleared | 5,000 |
| FY26 00942 | FY26GP 00942 | 208180809 | Catholic Managed Long Term Care, Inc. | cleared → cleared | 5,000 |
| FY26 01136 | FY26GP 01136 | 832630080 | Chinese Peoples Federation for World Peace USA, Inc. | cleared → cleared | 5,000 |
| FY26 01184 | FY26GP 01184 | 472244424 | City Mission, Inc. | cleared → cleared | 5,000 |
| FY26 01299 | FY26GP 01299 | 922196829 | Common Ground Community Services, Inc. | cleared → cleared | 5,750 |
| FY26 01813 | FY26GP 01813 | 261523871 | East Harlem Preservation, Inc. | cleared → cleared | 5,000 |
| FY26 01922 | FY26GP 01922 | 920603325 | ENVSN Foundation | cleared → cleared | 10,000 |
| FY26 01924 | FY26GP 01924 | 861340437 | Epic Village Community Development Corporation | cleared → cleared | 5,000 |
| FY26 01990 | FY26GP 01990 | 116019293 | First Baptist Church of Sheepshead Bay | cleared → cleared | 5,000 |
| FY26 02041 | FY26GP 02041 | 010907562 | Forest Playground Neighborhood Association, Inc. | cleared → cleared | 25,000 |
| FY26 02104 | FY26GP 02104 | 813355590 | Friends of Pack and Troop 253, Inc. | cleared → cleared | 5,000 |
| FY26 02177 | FY26GP 02177 | 271848709 | Girl Be Heard Institute | cleared → cleared | 5,000 |
| FY26 02208 | FY26GP 02208 | 333137407 | Goals For Life NYC, Inc. | cleared → cleared | 10,000 |
| FY26 02209 | FY26GP 02209 | 333137407 | Goals For Life NYC, Inc. | cleared → cleared | 10,000 |
| FY26 02365 | FY26GP 02365 | 136271908 | Harlem Commonwealth Council, Inc. | cleared → cleared | 10,000 |
| FY26 02366 | FY26GP 02366 | 821630347 | Harlem Dance Club, Inc. | cleared → cleared | 7,500 |
| FY26 02373 | FY26GP 02373 | 260847222 | Harlem Mothers Stop Another Violent End, Inc. | cleared → cleared | 10,000 |
| FY26 02374 | FY26GP 02374 | 922096596 | Harlem Network News Foundation, Inc. | cleared → cleared | 10,000 |
| FY26 02379 | FY26GP 02379 | 811352107 | Harlem SGL LGBTQ Center, Inc. | cleared → cleared | 10,000 |
| FY26 02440 | FY26GP 02440 | 842929615 | Helping Our People Evolve Incorporated | cleared → cleared | 5,000 |
| FY26 02488 | FY26GP 02488 | 871567482 | Holocaust Music Lost & Found, Inc. | cleared → cleared | 5,000 |
| FY26 02489 | FY26GP 02489 | 871567482 | Holocaust Music Lost & Found, Inc. | cleared → cleared | 5,000 |
| FY26 02578 | FY26GP 02578 | 831897911 | Imogen Roche Foundation, Inc. | cleared → cleared | 5,000 |
| FY26 02606 | FY26GP 02606 | 471831397 | Internal Creations, Inc. | cleared → cleared | 5,000 |
| FY26 02620 | FY26GP 02620 | 825122449 | Isaiah Whitehead Foundation, Inc. | cleared → cleared | 10,000 |
| FY26 02627 | FY26GP 02627 | 854284614 | Itty Bitty City Kitties, Inc. | cleared → cleared | 5,000 |
| FY26 02649 | FY26GP 02649 | 411801834 | Jeremiah Program | cleared → cleared | 10,000 |
| FY26 02753 | FY26GP 02753 | 851603288 | Joseph Prison to Palace Program, Inc. | cleared → cleared | 5,000 |
| FY26 02850 | FY26GP 02850 | 884305412 | Kiwanis Club for Community Care Foundation, Inc. | cleared → cleared | 5,000 |
| FY26 02874 | FY26GP 02874 | 994174091 | Korean American Youth Choir of New York | cleared → cleared | 5,000 |
| FY26 02895 | FY26GP 02895 | 832249413 | Ladies of Hope Ministries, Inc. | cleared → cleared | 7,500 |
| FY26 02994 | FY26GP 02994 | 113193909 | Living Traditions, Inc. | cleared → cleared | 5,000 |
| FY26 03008 | FY26GP 03008 | 823676844 | Lou's Helping Hand Foundation | cleared → cleared | 5,000 |
| FY26 03022 | FY26GP 03022 | 135596792 | Madison Square Boys & Girls Club, Inc. | cleared → cleared | 8,000 |
| FY26 03023 | FY26GP 03023 | 135596792 | Madison Square Boys & Girls Club, Inc. | cleared → cleared | 8,000 |
| FY26 03173 | FY26GP 03173 | 133601854 | Metrotech District Management Association, Inc. | cleared → cleared | 5,000 |
| FY26 03200 | FY26GP 03200 | 800117847 | Miss Black American Princess, Inc. | cleared → cleared | 5,000 |
| FY26 03204 | FY26GP 03204 | 113501430 | Mo Better Jaguars Football, Inc. | cleared → cleared | 5,000 |
| FY26 03210 | FY26GP 03210 | 862578460 | Modify Wellness, Inc. | cleared → cleared | 5,000 |
| FY26 03244 | FY26GP 03244 | 825510172 | Motivational Monster’s, Inc. | cleared → cleared | 15,000 |
| FY26 03245 | FY26GP 03245 | 825510172 | Motivational Monster’s, Inc. | cleared → cleared | 5,000 |
| FY26 03327 | FY26GP 03327 | 131924971 | Naumburg Orchestral Concerts, Inc. | cleared → cleared | 5,000 |
| FY26 03388 | FY26GP 03388 | 880926217 | New Harlem Renaissance | cleared → cleared | 7,500 |
| FY26 03403 | FY26GP 03403 | 131809283 | New York Board of Rabbis, Inc. | cleared → cleared | 5,000 |
| FY26 03404 | FY26GP 03404 | 131809283 | New York Board of Rabbis, Inc. | cleared → cleared | 5,000 |
| FY26 03699 | FY26GP 03699 | 993367298 | New York Interfaith Commission for Housing Equality, Inc. | cleared → cleared | 5,000 |
| FY26 03700 | FY26GP 03700 | 993367298 | New York Interfaith Commission for Housing Equality, Inc. | cleared → cleared | 5,000 |
| FY26 03783 | FY26GP 03783 | 823387804 | New York Videogame Critics Circle, Inc. | cleared → cleared | 5,000 |
| FY26 03801 | FY26GP 03801 | 825510616 | Nido de Esperanza Charitable Society | cleared → cleared | 5,000 |
| FY26 03832 | FY26GP 03832 | 994498650 | Nourishing Wells, Inc. | cleared → cleared | 10,000 |
| FY26 03854 | FY26GP 03854 | 841622031 | Ocean Bay Community Development Corporation | cleared → cleared | 5,000 |
| FY26 03928 | FY26GP 03928 | 020588068 | Beyond Bedtime, Inc. | cleared → cleared | 5,000 |
| FY26 03952 | FY26GP 03952 | 112229635 | Parodneck Foundation For Self Help Housing and Community Development, The | cleared → cleared | 10,000 |
| FY26 04006 | FY26GP 04006 | 136019220 | Poetry Society of America | cleared → cleared | 5,000 |
| FY26 04055 | FY26GP 04055 | 460776852 | Powerhouse Arts, Inc. | cleared → cleared | 5,000 |
| FY26 04059 | FY26GP 04059 | 921552648 | Practical Knowledge, Inc. | cleared → cleared | 5,000 |
| FY26 04091 | FY26GP 04091 | 853511986 | Project Media Zone, Inc. | cleared → cleared | 5,000 |
| FY26 04092 | FY26GP 04092 | 853511986 | Project Media Zone, Inc. | cleared → cleared | 5,000 |
| FY26 04219 | FY26GP 04219 | 132605604 | Queens Legal Services Corporation | cleared → cleared | 5,000 |
| FY26 04264 | FY26GP 04264 | 810714759 | Red Hook New York Rising Community Reconstruction Planning Committee, Ltd. | cleared → cleared | 5,000 |
| FY26 04292 | FY26GP 04292 | 811592925 | Renew Queens | cleared → cleared | 25,000 |
| FY26 04345 | FY26GP 04345 | 454460685 | Riverdale Children's Theatre, Inc. | cleared → cleared | 5,000 |
| FY26 04356 | FY26GP 04356 | 133204621 | Riverkeeper, Inc. | cleared → cleared | 5,000 |
| FY26 04377 | FY26GP 04377 | 832462823 | Rockaway Film Festival, Inc. | cleared → cleared | 5,000 |
| FY26 04428 | FY26GP 04428 | 883969802 | Saffiyahfrica, Inc. | cleared → cleared | 5,000 |
| FY26 04509 | FY26GP 04509 | 112301220 | Sephardic Multi Service Senior Citizens Center, Inc. | cleared → cleared | 5,000 |
| FY26 04653 | FY26GP 04653 | 237061382 | Special Olympics New York, Inc. | cleared → cleared | 5,000 |
| FY26 04654 | FY26GP 04654 | 237061382 | Special Olympics New York, Inc. | cleared → cleared | 5,000 |
| FY26 04655 | FY26GP 04655 | 237061382 | Special Olympics New York, Inc. | cleared → cleared | 10,000 |
| FY26 04660 | FY26GP 04660 | 743158439 | Spring Creek Senior Partners, Inc. | cleared → cleared | 10,000 |
| FY26 04762 | FY26GP 04762 | 260149521 | Street Corner Resources, Inc. | cleared → cleared | 5,000 |
| FY26 04806 | FY26GP 04806 | 223920483 | Sybarite Productions, Inc. | cleared → cleared | 5,000 |
| FY26 04807 | FY26GP 04807 | 223920483 | Sybarite Productions, Inc. | cleared → cleared | 10,000 |
| FY26 04816 | FY26GP 04816 | 331854711 | Tail Waggers Task Force, Inc. | cleared → cleared | 5,000 |
| FY26 04823 | FY26GP 04823 | 863679997 | Tea Arts and Cultures, Inc. | cleared → cleared | 5,000 |
| FY26 04834 | FY26GP 04834 | 133007801 | Terence Cardinal Cooke Health Care Center | cleared → cleared | 5,000 |
| FY26 04881 | FY26GP 04881 | 934592071 | Tribeca North Neighborhood Association, Inc. | cleared → cleared | 10,000 |
| FY26 04933 | FY26GP 04933 | 932643668 | United Hands Organization, Inc. | cleared → cleared | 5,000 |
| FY26 04934 | FY26GP 04934 | 932643668 | United Hands Organization, Inc. | cleared → cleared | 5,000 |
| FY26 04945 | FY26GP 04945 | 921790740 | United Palace for Arts and Culture, Inc. | cleared → cleared | 5,000 |
| FY26 04974 | FY26GP 04974 | 203049366 | Upper Midtown Chabad Lubavitch, Inc. | cleared → cleared | 5,000 |
| FY26 04975 | FY26GP 04975 | 203049366 | Upper Midtown Chabad Lubavitch, Inc. | cleared → cleared | 2,500 |
| FY26 04976 | FY26GP 04976 | 203049366 | Upper Midtown Chabad Lubavitch, Inc. | cleared → cleared | 2,500 |
| FY26 04977 | FY26GP 04977 | 993632277 | Upper West Side Cinema Center, Inc. | cleared → cleared | 10,000 |
| FY26 05016 | FY26GP 05016 | 823077340 | Values 4 Life Foundation, Inc. | cleared → cleared | 10,000 |
| FY26 05057 | FY26GP 05057 | 912036204 | Vietnam Veterans of America, Chapter 126 | cleared → cleared | 5,000 |
| FY26 05141 | FY26GP 05141 | 921139195 | West 95th Street Block Association | cleared → cleared | 5,000 |
| FY26 05154 | FY26GP 05154 | 872925731 | West Harlem Arts Alliance, Inc. | cleared → cleared | 10,000 |
| FY26 05175 | FY26GP 05175 | 133585152 | White Bird Productions, Inc. | cleared → cleared | 10,000 |
| FY26 05222 | FY26GP 05222 | 131484145 | Women's City Club of New York, Inc. | cleared → cleared | 5,000 |
| FY26 06277 | FY26GP 06277 | 872065261 | Living Arts Collaborative, Inc. | cleared → cleared | 20,000 |
| FY26 06472 | FY26GP 06472 | 131972960 | Paper Bag Players, Inc., The | cleared → cleared | 20,000 |
| FY26 07034 | FY26GP 07034 | 133718885 | Throggs Neck Benevolent Association, Inc. | cleared → cleared | 15,000 |
| FY26 07607 | FY26GP 07607 | 861557595 | Blacklining Foundation, Inc. | cleared → cleared | 10,000 |
| FY26 07804 | FY26GP 07804 | 132899445 | Stuyvesant Park Neighborhood Association | cleared → cleared | 10,000 |
| FY26 07989 | FY26GP 07989 | 133455415 | HUB-Third Ave Merchants District Management Association, Inc. | cleared → cleared | 20,000 |
| FY26 08955 | FY26GP 08955 | 112358083 | Canaan Senior Service Center, Inc. | cleared → cleared | 20,000 |
| FY26 08998 | FY26GP 08998 | 135562324 | Correctional Association of New York | cleared → cleared | 10,000 |
| FY26 09170 | FY26GP 09170 | 112229635 | Parodneck Foundation For Self Help Housing and Community Development, The | cleared → cleared | 10,000 |
| FY26 09311 | FY26GP 09311 | 475395985 | Canarsie Community Development, Inc. | cleared → cleared | 25,000 |
| FY26 09454 | FY26GP 09454 | 851603288 | Joseph Prison to Palace Program, Inc. | cleared → cleared | 10,000 |
| FY26 09640 | FY26GP 09640 | 133058019 | Harlem Week, Inc. | cleared → cleared | 10,000 |
| FY26 09942 | FY26GP 09942 | 131809283 | New York Board of Rabbis, Inc. | cleared → cleared | 5,000 |
| FY26 10617 | FY26GP 10617 | 264546315 | Bushwick Starr, Inc. | cleared → cleared | 5,413 |
| FY26 10627 | FY26GP 10627 | 116019293 | First Baptist Church of Sheepshead Bay | cleared → cleared | 5,000 |
| FY26 11239 | FY26GP 11239 | 823676844 | Lou's Helping Hand Foundation | cleared → cleared | 5,945 |

Fields outside the key changed on composite-key pairs: `council_member` 2

## Candidate amount changes (composite-keyed rows) — 0

One removed and one added row that agree on every key field except amount. A nomination to check in the workbooks; **not** counted as an amount change.


## Likely re-issued (removed and added rows sharing EIN, amount and legal name) — 2

A removed row and an added row with the same EIN, amount and legal name, matched one to one: probably the same grant re-filed under a new MOCS ID with a different agency, stream or member. A nomination only; both rows are still counted in Added and Removed.

| old row | old MOCS ID | new row | new MOCS ID | EIN | legal name | amount | fields that differ |
|---|---|---|---|---|---|---:|---|
| 3746 | FY26 01703 | 11588 | FY26 12219 | 136400434 | Department of Transportation | 6,000 | mocs_id, program_name, council_member, status_norm |
| 11164 | FY26 10572 | 11634 | FY26 12266 | 472167056 | Victory Music and Dance Company, Inc. | 30,000 | mocs_id, source, council_member |

## Added — 62

| row | MOCS ID | EIN | legal name | source | status | amount |
|---|---|---|---|---|---|---:|
| row 11573 | FY26 12203 | 136400434 | Department of Transportation | Local | Cleared | 1,000 |
| row 11574 | FY26 12204 | 993632277 | Upper West Side Cinema Center, Inc. | Speaker's Initiative | Cleared | 40,000 |
| row 11575 | FY26 12205 | 136400434 | Department of Transportation | Anti-Poverty | Cleared | 1,000 |
| row 11576 | FY26 12206 | 136400434 | Department of Parks and Recreation | Parks Equity Initiative | Cleared | 4,305 |
| row 11577 | FY26 12207 | 136400434 | Department of Parks and Recreation | Parks Equity Initiative | Cleared | 8,199 |
| row 11578 | FY26 12208 | 136400434 | Department of Parks and Recreation | Parks Equity Initiative | Cleared | 4,670 |
| row 11579 | FY26 12209 | 133846431 | Association of Community Employment Programs for the Homeless, Inc. | NYC Cleanup | Cleared | 20,000 |
| row 11580 | FY26 12210 | 133846431 | Association of Community Employment Programs for the Homeless, Inc. | NYC Cleanup | Cleared | 10,000 |
| row 11581 | FY26 12211 | 270295829 | Bedford Stuyvesant Gateway District Management Association, Inc. | NYC Cleanup | Cleared | 20,000 |
| row 11582 | FY26 12212 | 136400434 | Department of Sanitation | NYC Cleanup | Cleared | 40,000 |
| row 11583 | FY26 12213 | 352323897 | Rooftop Films, Inc. | Boroughwide Needs Initiative | Cleared | 5,000 |
| row 11584 | FY26 12214 | 651209020 | Brooklyn Ballers Sports, Youth and Educational Corporation | Boroughwide Needs Initiative | Cleared | 10,250 |
| row 11585 | FY26 12216 | 852420028 | Rethink Food USA, Inc. | Local | Cleared | 5,000 |
| row 11586 | FY26 12217 | 870753479 | Laundromat Project, Inc., The | Anti-Poverty | Cleared | 9,750 |
| row 11587 | FY26 12218 | 113463183 | 77th Precinct Community Council, Inc. | Local | Cleared | 25,000 |
| row 11588 | FY26 12219 | 136400434 | Department of Transportation | Local | Cleared | 6,000 |
| row 11589 | FY26 12220 | 111735956 | Shaare Zion Congregation | Local | Cleared | 5,000 |
| row 11590 | FY26 12222 | 133622107 | Mosholu-Montefiore Community Center, Inc. | Local | Cleared | 5,000 |
| row 11591 | FY26 12223 | 136400434 | Fire Department of New York | Speaker's Initiative | Cleared | 178,850 |
| row 11592 | FY26 12224 | 133976066 | Partnership for After School Education, Inc. | Speaker's Initiative | Cleared | 50,000 |
| row 11593 | FY26 12225 | 132617681 | United Way of New York City | Speaker's Initiative | Cleared | 1,000,000 |
| row 11594 | FY26 12226 | 112024569 | Council of School Supervisors and Administrators of the City of NY | Speaker's Initiative | Cleared | 255,000 |
| row 11595 | FY26 12227 | 139226721 | United Federation of Teachers Educational Foundation, Inc. | Speaker's Initiative | Cleared | 250,000 |
| row 11596 | FY26 12228 | 113174514 | St. John's Bread and Life Program, Inc. | Speaker's Initiative | Cleared | 150,000 |
| row 11597 | FY26 12229 | 262214534 | Brooklyn Community Pride Center, Inc. | Speaker's Initiative | Cleared | 150,000 |
| row 11598 | FY26 12230 | 830440009 | Children of Promise, NYC | Speaker's Initiative | Cleared | 50,000 |
| row 11599 | FY26 12231 | 112412205 | Bedford Stuyvesant Family Health Center, Inc. | Speaker's Initiative | Cleared | 150,000 |
| row 11600 | FY26 12232 | 237348989 | Korean Community Services of Metropolitan New York, Inc. | Speaker's Initiative | Cleared | 50,000 |
| row 11601 | FY26 12233 | 135562374 | University Settlement Society of New York | Speaker's Initiative | Cleared | 200,000 |
| row 11602 | FY26 12234 | 133187792 | Asian Americans For Equality, Inc. | Speaker's Initiative | Cleared | 50,000 |
| row 11603 | FY26 12235 | 133609811 | Korean American Family Service Center, The | Speaker's Initiative | Cleared | 50,000 |
| row 11604 | FY26 12236 | 841899350 | Communities Resist, Inc. | Speaker's Initiative | Cleared | 50,000 |
| row 11605 | FY26 12237 | 133306195 | Institute for Community Living, Inc. | Speaker's Initiative | Cleared | 100,000 |
| row 11606 | FY26 12238 | 136400434 | City University of New York | Speaker's Initiative | Cleared | 51,000 |
| row 11607 | FY26 12239 | 133846431 | Association of Community Employment Programs for the Homeless, Inc. | Speaker's Initiative | Cleared | 50,000 |
| row 11608 | FY26 12240 | 133843322 | Center for Employment Opportunities | Speaker's Initiative | Cleared | 50,000 |
| row 11609 | FY26 12241 | 136400434 | Department of Sanitation | Speaker's Initiative | Cleared | 84,000 |
| row 11610 | FY26 12242 | 474803090 | UA3, Inc. | Speaker's Initiative | Cleared | 50,000 |
| row 11611 | FY26 12243 | 320000557 | Greater Bethel Community Development Corporation | Speaker's Initiative | Cleared | 50,000 |
| row 11612 | FY26 12244 | 135596746 | NYSARC, Inc., New York City Chapter | Neighborhood Development Grant Initiative | Cleared | 20,000 |
| row 11613 | FY26 12245 | 133706442 | Staten Island Economic Development Corporation | Local | Cleared | 10,000 |
| row 11614 | FY26 12246 | 135562308 | New York University | Speaker's Initiative | Cleared | 150,000 |
| row 11615 | FY26 12247 | 134012789 | Dr. Theodore A. Atlas Foundation, Inc. | Local | Cleared | 10,000 |
| row 11616 | FY26 12248 | 133179546 | Food Bank For New York City | Food Pantries | Cleared | 5,231 |
| row 11617 | FY26 12249 | 133179546 | Food Bank For New York City | Food Pantries | Cleared | 2,380 |
| row 11618 | FY26 12250 | 133179546 | Food Bank For New York City | Food Pantries | Cleared | 3,623 |
| row 11619 | FY26 12251 | 133179546 | Food Bank For New York City | Food Pantries | Cleared | 1,495 |
| row 11620 | FY26 12252 | 133179546 | Food Bank For New York City | Food Pantries | Cleared | 882 |
| row 11621 | FY26 12253 | 133805585 | Teatro Circulo, Ltd. | SU-CASA | Cleared | 15,000 |
| row 11622 | FY26 12254 | 133805585 | Teatro Circulo, Ltd. | SU-CASA | Cleared | 15,000 |
| row 11623 | FY26 12255 | 133805585 | Teatro Circulo, Ltd. | SU-CASA | Cleared | 15,000 |
| row 11624 | FY26 12256 | 136400434 | Department of Sanitation | BID Containerization | Cleared | 2,262,619 |
| row 11625 | FY26 12257 | 471267077 | Neighborhood Housing Services of Queens CDC, Inc. | Foreclosure Prevention Programs | Cleared | 55,000 |
| row 11626 | FY26 12258 | 133576756 | Youth Justice Network, Inc. | Peer Specialists Support | Cleared | 50,000 |
| row 11627 | FY26 12259 | 135596746 | NYSARC, Inc., New York City Chapter | Peer Specialists Support | Cleared | 50,000 |
| row 11628 | FY26 12260 | 136400434 | Department of Health and Mental Hygiene | Local | Cleared | 5,000 |
| row 11629 | FY26 12261 | 112608645 | Jewish Community Council of Canarsie, Inc. | Local | Cleared | 5,000 |
| row 11630 | FY26 12262 | 844338493 | Muna Social Services, Inc. | Local | Cleared | 12,500 |
| row 11631 | FY26 12263 | 844338493 | Muna Social Services, Inc. | Youth | Cleared | 7,500 |
| row 11632 | FY26 12264 | 112608645 | Jewish Community Council of Canarsie, Inc. | Anti-Poverty | Cleared | 5,000 |
| row 11633 | FY26 12265 | 136400434 | Department of Cultural Affairs | Support Our Older Adults | Cleared | 30,000 |
| row 11634 | FY26 12266 | 472167056 | Victory Music and Dance Company, Inc. | Older Adult Center Improvements | Cleared | 30,000 |

## Removed — 55

| row | MOCS ID | EIN | legal name | source | status | amount |
|---|---|---|---|---|---|---:|
| row 63 | FY26 11662 | 113619986 | 86th Street Bay Ridge District Management Association, Inc. | BID Containerization | Cleared | 19,953 |
| row 977 | FY26 00403 | 116083182 | Bedford Stuyvesant Restoration Corporation | Speaker's Initiative | Cleared | 100,000 |
| row 978 | FY26 00404 | 116083182 | Bedford Stuyvesant Restoration Corporation | Speaker's Initiative | Cleared | 2,500,000 |
| row 1003 | FY26 00421 | 112568013 | Bensonhurst Council of Jewish Organizations | Local | Pending | 5,000 |
| row 1827 | FY26 11668 | 133009946 | Bryant Park Corporation | BID Containerization | Cleared | 36,100 |
| row 1940 | FY26 11669 | 270699754 | Capitol District Management Association, Inc. | BID Containerization | Cleared | 15,000 |
| row 2031 | FY26 11670 | 920829346 | Castle Hill District Management Association, Inc. | BID Containerization | Cleared | 40,000 |
| row 2178 | FY26 12174 | 133843322 | Center for Employment Opportunities | BID Containerization | Cleared | 29,247 |
| row 2451 | FY26 11672 | 455491393 | Chinatown District Management Association, Inc. | BID Containerization | Cleared | 80,000 |
| row 2834 | FY26 11782 | 061561857 | Columbus Avenue District Management Association, Inc. | BID Containerization | Cleared | 82,250 |
| row 3355 | FY26 12095 | 136400434 | Department for the Aging | Speaker's Initiative | Pending | 10,000 |
| row 3356 | FY26 07067 | 136400434 | Department of Cultural Affairs | SU-CASA | Pending | 45,000 |
| row 3513 | FY26 01495 | 136400434 | Department of Education | Speaker's Initiative | Cleared | 284,000 |
| row 3520 | FY26 12198 | 136400434 | Department of Education | Speaker's Initiative | Pending | 150,000 |
| row 3536 | FY26 12186 | 136400434 | Department of Health and Mental Hygiene | Peer Specialists Support | Pending | 100,000 |
| row 3547 | FY26 01656 | 136400434 | Department of Parks and Recreation | Anti-Poverty | Pending | 9,750 |
| row 3548 | FY26 01655 | 136400434 | Department of Parks and Recreation | Boroughwide Needs Initiative | Pending | 10,250 |
| row 3554 | FY26 12160 | 136400434 | Department of Parks and Recreation | Local | Cleared | 5,000 |
| row 3580 | FY26 07908 | 136400434 | Department of Parks and Recreation | NYC Cleanup | Pending | 88,750 |
| row 3728 | FY26 12180 | 136400434 | Department of Social Services | Anti-Poverty | Pending | 1,000 |
| row 3737 | FY26 12096 | 136400434 | Department of Social Services | Speaker's Initiative | Pending | 10,000 |
| row 3746 | FY26 01703 | 136400434 | Department of Transportation | Local | Pending | 6,000 |
| row 3766 | FY26 12196 | 136400434 | Department of Youth and Community Development | Boroughwide Needs Initiative | Pending | 5,000 |
| row 3768 | FY26 12191 | 136400434 | Department of Youth and Community Development | Local | Pending | 10,000 |
| row 3769 | FY26 12182 | 136400434 | Department of Youth and Community Development | Parks Equity Initiative | Pending | 17,174 |
| row 3770 | FY26 01730 | 136400434 | Department of Youth and Community Development | Speaker's Initiative | Pending | 26,000 |
| row 3919 | FY26 01796 | 884269147 | Dreyfus Health Policy & Research Center, Inc. | Local | Cleared | 5,000 |
| row 4378 | FY26 11784 | 870793638 | Flatbush Nostrand Junction District Management Association, Inc. | BID Containerization | Pending | 100,000 |
| row 4675 | FY26 11681 | 141933279 | Forest Avenue District Management Association, Inc. | BID Containerization | Cleared | 35,000 |
| row 5162 | FY26 11779 | 822193145 | Greater JFK District Management Association, Inc. | BID Containerization | Cleared | 57,224 |
| row 5726 | FY26 12193 | 136400434 | Housing Preservation and Development | Local | Pending | 10,000 |
| row 5754 | FY26 11686 | 471247857 | Hudson Yards Hell's Kitchen Business Improvement District, Inc. | BID Containerization | Cleared | 148,516 |
| row 6301 | FY26 02801 | 463766464 | Kan Cobra Tiger Alliance, Inc. | Local | Cleared | 5,000 |
| row 6593 | FY26 11688 | 133466792 | Lenape Bloemendael District Management Association | BID Containerization | Cleared | 55,493 |
| row 6667 | FY26 02960 | 853008532 | Lights Out Performance, Inc. | Local | Pending | 5,000 |
| row 6678 | FY26 02967 | 043672661 | Lincoln Terrace Tennis Association, Inc. | Local | Cleared | 15,000 |
| row 7361 | FY26 11694 | 133877808 | Mosholu-Jerome East Gun Hill Road District Management Association | BID Containerization | Cleared | 57,672 |
| row 7609 | FY26 08396 | 237398279 | Neighborhood Housing Services of Jamaica, Inc. | Foreclosure Prevention Programs | Cleared | 55,000 |
| row 7656 | FY26 03366 | 263564521 | Network of Angels, Inc. | Local | Cleared | 7,500 |
| row 7691 | FY26 11697 | 823226337 | New Dorp District Management Association, Inc. | BID Containerization | Cleared | 18,213 |
| row 7724 | FY26 03394 | 112996487 | New Life Evangelistic Church | Anti-Poverty | Cleared | 5,000 |
| row 8610 | FY26 09669 | 133779611 | NYSARC, Inc., New York City Chapter, AHRC New York City | Neighborhood Development Grant Initiative | Cleared | 20,000 |
| row 8801 | FY26 11699 | 263926626 | Park Slope Fifth Avenue District Management Association, Inc. | BID Containerization | Cleared | 85,000 |
| row 8882 | FY26 11781 | 112709046 | Pitkin Avenue District Management Association, Inc. | BID Containerization | Cleared | 54,000 |
| row 9351 | FY26 04239 | 992548532 | R I N G Inc. | Local | Cleared | 5,000 |
| row 10039 | FY26 04533 | 934351686 | Sew So Fresh, Inc. | Youth | Cleared | 7,500 |
| row 10138 | FY26 12188 | 136400434 | Small Business Services | Local | Pending | 5,000 |
| row 10243 | FY26 11700 | 810728516 | South Shore District Management Association, Inc. | BID Containerization | Cleared | 25,000 |
| row 10246 | FY26 11701 | 263497932 | Southern Boulevard District Management Association, Inc. | BID Containerization | Cleared | 30,000 |
| row 10336 | FY26 04671 | 800079644 | St. James Holiness Church | Local | Cleared | 5,000 |
| row 10586 | FY26 11704 | 113251860 | Sunset Park District Management Association, Inc. | BID Containerization | Cleared | 56,000 |
| row 10709 | FY26 11707 | 842946779 | Throggs Neck District Management Association, Inc. | BID Containerization | Cleared | 54,470 |
| row 11164 | FY26 10572 | 472167056 | Victory Music and Dance Company, Inc. | Support Our Older Adults | Cleared | 30,000 |
| row 11293 | FY26 11706 | 133348873 | Washington Heights Business Improvement District Mgmt Association, Inc. | BID Containerization | Cleared | 20,000 |
| row 11414 | FY26 11713 | 883290964 | West Village District Management Association | BID Containerization | Pending | 125,000 |
