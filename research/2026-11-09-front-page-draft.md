# Front page draft: two doors (#264, for #267)

**Status:** proposed, needs Noel. Drafted 2026-11-09 for epic
[#272](https://github.com/BetaNYC/New-York-City-Budget/issues/272). This is the wording only.
[#267](https://github.com/BetaNYC/New-York-City-Budget/issues/267) builds it into `viz/index.html`
with the shared header and footer, once the agency explorer is in `viz/agencies/` (#265), so the
front page never links to a page that is not there yet.

Every figure below is already on the current front page or in the [README](../README.md), and
was checked against its source on 2026-11-09. Links are relative (`./`, never `/`), because the
site lives under `/New-York-City-Budget/`.

---

## Page title

NYC budget data, checked — BetaNYC

## Meta description

Two halves of New York City's budget, from BetaNYC: every City agency's adopted and modified
budget, FY2017–FY2027, from NYC Open Data; and the Council's discretionary funding, who got
what, from the Council's spreadsheets and budget PDFs.

## H1

NYC budget data, checked

## Lead

BetaNYC publishes New York City's budget as data you can search and check. There are two
halves, and they answer different questions. Every number comes from the City's own data, and
we never change one by hand.

## Door 1: City agency budgets → `agencies/`

**City agency budgets**

How much each City agency was given in the adopted budget, and how it changed during the year,
FY2017–FY2027. Every agency and community board, by unit of appropriation.

- *Answers:* How much does my community board get? How did an agency's budget change?
- *Source:* NYC Open Data, Expense Budget (`mwzb-yiwb`), published for the Mayor's Office of
  Management and Budget. FY2026 adopted: $115.9 billion net; $117,791,473,676 as counted in Open
  Data, which includes $1,884,163,949 of intra-city money.
- *Checked:* the build stops unless it matches OMB's printed FY2026 Adopted Budget to the dollar.

Button: **Look up agency budgets**

## Door 2: Council discretionary funding → `explorer/`

**Council discretionary funding**

Which organizations the City Council funds, for how much, through which agency, and at whose
request. Expense awards FY2009 and FY2011–FY2027, capital designations, and the tables from the
Council's budget PDFs.

- *Answers:* Which groups did my Council member fund? Did this nonprofit get Council money?
- *Source:* the Council's spreadsheets and budget PDFs, and NYC Open Data.
- *Checked:* every row of the FY2018–FY2027 budget PDFs read twice and tied to the printed
  totals; review in progress.

Button: **Search Council funding**

## Below the doors

**Not sure which you need?** [Which tool answers my question?](which-tool page) It also explains
the words: fiscal year, adopted and modified, unit of appropriation, intra-city.

**The fiscal year.** NYC's fiscal year runs July 1 to June 30 and is named for the year it ends:
FY2026 is July 1, 2025 to June 30, 2026. Both halves use it.

**Correction, 2026-11-09.** Before this date the agency budget explorer showed every year one
year late: "Adopted 2026" was really FY2025. It is fixed. If you copied agency figures before
2026-11-09, please download them again.

## How the Council's PDF tables are checked

Keep the current front page's section as is (figures as of the `pdf-tables-2026-10-24-260d16e`
release):

- 141,456 rows in 36 tables: Schedule C, the transparency resolutions, the capital book and
  Terms and Conditions.
- Schedule C: 76,216 of 76,272 rows read the same both ways. The other 56 went to a person.
- 515 of 519 printed totals tie exactly. The other 4 are totals the PDF itself gets wrong, and
  they are flagged, not fixed.
- The review is still going. No year is finished yet.

Also keep, word for word: the coverage gaps ("FY2010 is not included", "FY2018 is missing"), the
"Use it" links (explorer, MCP, downloads, changelog), and the frozen-explorer notice with its
`legacy.html` link and deep-link script. `viz/test_pages_site.py` checks all of these.

## Footer, on every page (#267)

Built and maintained by BetaNYC. Agency budgets: NYC Open Data `mwzb-yiwb`, data as of the June
2026 release. Council funding: data as of the `pdf-tables-2026-10-24-260d16e` release. Last
revised: *date*. Questions, or something that looks wrong? Open an issue on GitHub.

The agency explorer is adapted from DataMade's Look at Cook (MIT).
