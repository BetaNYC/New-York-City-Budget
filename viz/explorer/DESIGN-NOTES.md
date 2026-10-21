---
title: Budget explorer — design notes from review
created: 2026-10-21
type: plan
status: draft
tags: [viz, explorer, open-data, council-speaker]
---

# Budget explorer — design notes from review

**Report generated:** 2026-10-21 00:10. Requirements Noel raised while reviewing the FY2027 demo
build. Items 2 and 3 are design constraints for later work, recorded here so no PR builds
against them by accident.

## 1. The view tabs must read as buttons

The views (Expense awards, Years, Capital, Capital vs OMB, Organizations, Terms & Conditions,
Review, About the data) render as white text on the dark header. Only the active tab has a
shape. A first-time visitor cannot tell they are things to click.

- Every tab gets a visible button shape at rest (border or filled background), a hover and
  focus state, and a distinct active state (`aria-current="page"` already marks it).
- Keyboard focus ring visible on the dark header; contrast meets WCAG AA for text and for the
  tab boundary.
- Same treatment in the public build and the reviewed build.

## 2. Track whether each record is on NYC Open Data

The Council's data reaches the public through several channels that come and go: its own
workbooks, PDFs, and NYC Open Data. Some years exist on the portal and not in a workbook, some
the reverse, and portal datasets stop updating (`4d7f-74pe`, City Council Discretionary
Funding, last updated by its publisher 2021-04-20, covers FY2009–FY2021; `t474-a92g`, Council
capital, covers FY2019–FY2025, per `source/` READMEs).

Design so that, per record, the explorer can say **"also on NYC Open Data: dataset X, row Y, as
of date D"**, or "not on Open Data as of D":

- **Snapshots, not live calls.** Pull each relevant dataset whole, dated, into
  `source/open-data-<id>/` (the existing pattern: `MANIFEST.csv`, hash, `README.md` with
  terms and row counts). The explorer never calls the portal at runtime.
- **A crosswalk table** per family: `record key → (dataset_id, portal row id, snapshot date,
  match status: same / differs / absent)`, built by the same loader as everything else, so
  the MCP and the explorer agree.
- **History.** Keep every snapshot's crosswalk, so we can show when a record appeared on or
  disappeared from the portal.
- **Which datasets** is a research step (catalog search), not an assumption. Known so far:
  `4d7f-74pe` (expense designations), `t474-a92g` (Council capital), `46m8-77gv` (OMB capital
  budget), `2cmn-uidm` (OMB capital commitment plan).
- **Permission.** Noel approved pulling from the NYC Open Data portal for this collection
  (2026-10-21). The data plan (datasets, cadence, storage, matching rules) is confirmed with
  Noel before the first bulk pull, per the workspace research-planning rule.

## 3. "Speaker" is a role, not a person

Rows list the sponsor as `Speaker`. The Speaker changes, and **can change mid-fiscal-year**: a
fiscal year runs July to June, and a new Council session elects its Speaker in January, so one
fiscal year can span two Speakers (e.g. FY2026 runs July 2025 to June 2026 and crosses the
January 2026 change to Speaker Julie Menin).

- **A Speakers reference table** (`data/reference/council_speakers.csv`): person, Council
  member id, term start, term end, source. Sourced from records, not memory.
- **Resolve per record by its action date**, not its fiscal year: Schedule C designations by the
  adoption date; later designations by their transparency resolution date. When a record has no
  date and its fiscal year spans a change, show the role with both possible names and a
  "Speaker at time of designation not recorded" note. Never guess.
- **Keep the role.** Show "Speaker (Julie Menin)", never replace `Speaker` with a name, so the
  source text stays as printed.
- **The role also appears among co-sponsors** (capital: `Speaker, Johnson` in FY2015, when
  Corey Johnson was a district member and not yet Speaker). A name next to `Speaker` is a
  co-sponsor, not the Speaker. The parser and the views must not conflate the two.
