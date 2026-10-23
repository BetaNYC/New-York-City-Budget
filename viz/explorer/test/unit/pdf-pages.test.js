/**
 * The searchable PDF family pages (#213): Schedule C (every row), Transparency resolutions, the
 * capital book, and Terms' book-order numbers (#206); the Open Data lookup keyed on a book row's
 * own place (#205); their URL state; the row labels every PDF row carries (#190).
 *
 * The queries' answers are checked against budget.db in test/parity.test.mjs; here, what they ask.
 */
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, test } from "vitest";

import * as P from "../../src/query/pdf.js";
import { DEFAULT_STATE, FILTER_KEYS, PAGE_KEY, VIEWS, readHash, writeHash } from "../../src/state/hash.js";
import { HiddenText, PublicNotes, ReviewedLabel, RowLinks } from "../../src/components/pdf.jsx";
import ScheduleCSearch, { YearStatus } from "../../src/views/ScheduleCSearch.jsx";
import Transparency from "../../src/views/Transparency.jsx";
import Book from "../../src/views/Book.jsx";
import Terms from "../../src/views/Terms.jsx";

const html = (el, props) => renderToStaticMarkup(createElement(el, props));
const noop = () => {};
const MANIFEST = { source_commit: "fc1c9e6761adf3c585085eca8bc309eb7f2bfc3c" };
const page = (view, pdfYears) => html(view, { state: { ...DEFAULT_STATE, view: "x" }, set: noop, go: noop, manifest: MANIFEST, pdfYears });
const year = (family, fiscal_year, status = "reviewed") => ({ family, fiscal_year, status });

describe("URL state for the new pages", () => {
  test("each page is a view, and its filters and page are state keys that round-trip", () => {
    for (const v of ["schedc", "transparency", "book"]) {
      expect(VIEWS).toContain(v);
      expect(FILTER_KEYS[v].length).toBeGreaterThan(0);
      for (const k of [...FILTER_KEYS[v], PAGE_KEY[v]]) expect(k in DEFAULT_STATE).toBe(true);
    }
    const s = {
      ...DEFAULT_STATE,
      view: "transparency",
      trfy: 2025,
      trbfy: 2024,
      trorg: "South Asian Youth",
      trein: "13-3943630",
      trmember: "Lee",
      trreso: "1013",
      trfrom: "2025-08-01",
      trto: "2025-08-31",
      traction: "purpose_to",
      trpage: 2,
    };
    const h = writeHash(s);
    expect(readHash(h)).toEqual(s);
    expect(writeHash(readHash(h))).toBe(h);
    const b = { ...DEFAULT_STATE, view: "book", bkfy: 2024, bkid: "HL TA001", bkmin: -50000, bkmax: 0, bkboro: "K", bkpart: "I", bkpage: 1 };
    expect(readHash(writeHash(b))).toEqual(b);
    const c = { ...DEFAULT_STATE, view: "schedc", scfy: 2019, scorg: "Jobs", scein: "13-2736022", scmin: 1000.5, scmax: 5e6, scdisc: "unmatched", scpage: 3 };
    expect(readHash(writeHash(c))).toEqual(c);
  });
  test("no new key collides with the source viewer's (spdf, spage, sbox, slabel)", () => {
    for (const v of ["schedc", "transparency", "book"]) for (const k of FILTER_KEYS[v]) expect(["spdf", "spage", "sbox", "slabel"]).not.toContain(k);
  });
});

describe("the status label every PDF row carries (#190)", () => {
  test("reviewed and closed, in words", () => {
    expect(P.statusLabel("reviewed")).toBe("checked, review in progress");
    expect(P.statusLabel("closed")).toBe("checked and reviewed");
    expect(P.statusLabel("")).toBe("");
    expect(html(ReviewedLabel, { status: "closed" })).toContain("checked and reviewed");
    expect(html(ReviewedLabel, { status: "reviewed" })).toContain("checked, review in progress");
    expect(html(ReviewedLabel, { status: "closed", block: true })).toContain("signed the year off");
  });
  test("hidden text is shown in its own labeled field, never bare", () => {
    expect(html(HiddenText, { text: "" })).toBe("");
    const out = html(HiddenText, { text: "purpose: st Center Program in Council District 23." });
    expect(out).toContain("hidden text, not visible on the printed page");
    expect(out).toContain("st Center Program");
  });
  test("a row's links: its page in the source view, the PDF at the build's commit", () => {
    const row = { source_pdf: "source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf", pdf_page: 279, bbox_pt: "18.42,402.92,958.68,460.06", pdf_sha256: "x" };
    const out = html(RowLinks, { state: DEFAULT_STATE, go: noop, manifest: MANIFEST, row, label: "Medicare Rights Center, $135,000" });
    expect(out).toContain("p.279");
    expect(out).toContain("spage=279");
    expect(out).toContain(`/blob/${MANIFEST.source_commit}/source/FY27/Fiscal-2027-Schedule-C-Final-3.pdf`);
    // The GitHub page opens the PDF at page 1, so its label names no page.
    expect(out).toContain('aria-label="The PDF on GitHub"');
    expect(html(RowLinks, { state: DEFAULT_STATE, go: noop, manifest: MANIFEST, row: { source_pdf: "x.txt", pdf_page: 1 } })).toBe("");
  });
});

describe("public review notes (#224 review)", () => {
  test("plain notes, no check id or severity; undecided says so", () => {
    const out = html(PublicNotes, {
      notes: [
        { review_id: "a", check_id: "K.side_list", severity: "critical", pdf_page: 106, note: "a list printed beside the table", decision: "" },
        { review_id: "b", check_id: "W.amount_bare", severity: "warn", pdf_page: 106, note: "amount printed without $", decision: "accepted_as_printed", decision_note: "" },
      ],
    });
    expect(out).not.toMatch(/critical|K\.side_list|W\.amount_bare/i);
    expect(out).toContain("Not yet decided.");
    expect(out).toContain("Decided: kept as printed");
    expect(out).toContain("not about the organization");
  });
  test("the public notes query asks for no check id or severity (a public pdf_review has neither)", () => {
    const pub = P.reviewNotesQuery("a;b", { full: false }).sql;
    expect(pub).not.toMatch(/check_id|severity/);
    expect(pub).toContain("note, decision, decision_note");
    expect(P.reviewNotesQuery("a").sql).toContain("check_id, severity");
  });
  test("an EIN with no digits is reported, not silently dropped", () => {
    expect(P.einUnusable("abc")).toBe(true);
    expect(P.einUnusable("13-2612524")).toBe(false);
    expect(P.einUnusable("")).toBe(false);
  });
});

describe("Schedule C, every row", () => {
  test("filters: year, organization, EIN (the row's or its fiscal conduit's), sponsor, category, initiative, agency, amounts, disclosure", () => {
    const q = P.scSearchQuery(
      { fiscal_year: "2019", org: "Jobs", ein: "13-2736022", sponsor: "Speaker", category: "Local", initiative: "senior", agency: "DYCD", min_amount: "100", max_amount: 5000, disclosure: "unmatched" },
      0
    );
    expect(q.params).toEqual([2019, "jobs", "132736022", "132736022", "speaker", "speaker", "speaker", "local", "senior", "dycd", 100, 5000, "unmatched"]);
    expect(q.sql).toContain("(a.ein = ? OR a.fiscal_conduit_ein = ?)");
    expect(q.sql).toContain("a.member");
    expect(q.sql).toContain("a.delegation");
    expect(q.sql).toMatch(/LIMIT 50 OFFSET 0$/);
  });
  test("every row, not only the rows paired with the disclosure; no filter, no WHERE", () => {
    const q = P.scSearchQuery({}, 2);
    expect(q.params).toEqual([]);
    expect(q.sql).toMatch(/FROM pdf_schedule_c a\s+ORDER BY/);
    expect(q.sql).toContain("OFFSET 100");
  });
  test("sub-awards are never in a total, and are asked for only under awards that have them", () => {
    expect(P.scSearchTotalsQuery({}).sql).not.toContain("subawards");
    expect(P.scSubawardsQuery([{ fiscal_year: 2019, award_id: "a", subawards: 0 }])).toBeNull();
    const q = P.scSubawardsQuery([{ fiscal_year: 2019, award_id: "fy19-p105-t00-r002", subawards: 28 }, { fiscal_year: 2019, award_id: "b", subawards: 0 }]);
    expect(q.params).toEqual([2019, "fy19-p105-t00-r002"]);
  });
  test("the page renders its labeled filters, or says there is no data", () => {
    expect(page(ScheduleCSearch, [])).toContain("No Schedule C data is in this build");
    const out = page(ScheduleCSearch, [year("schedule_c", 2019), year("schedule_c", 2027, "closed")]);
    for (const l of ["Fiscal year", "Organization", "EIN (tax ID)", "Sponsor", "Category", "Initiative", "Agency", "Min $", "Max $", "In the disclosure spreadsheet"]) {
      expect(out).toContain(`<span>${l}</span>`);
    }
    expect(out).toContain('aria-label="Search Schedule C"');
    expect(out).toContain("checked, review in progress");
    expect(out).toContain("checked and reviewed");
    expect(out).toContain("clearance status, Cleared or Pending");
    expect(page(ScheduleCSearch, [year("schedule_c", 2019)]).replace(/<[^>]+>/g, "")).not.toContain("not an EIN");
    const bad = html(ScheduleCSearch, { state: { ...DEFAULT_STATE, scein: "abc" }, set: noop, go: noop, manifest: MANIFEST, pdfYears: [year("schedule_c", 2019)] });
    expect(bad).toContain("is not an EIN");
  });
  test("the year line groups years by status", () => {
    const out = html(YearStatus, { years: [year("t", 2020), year("t", 2018), year("t", 2027, "closed")] });
    expect(out).toContain("FY2018, FY2020");
    expect(out).toContain("FY2027");
  });
});

describe("Transparency resolutions", () => {
  test("filters: organization, EIN, member, resolution number and dates, fiscal year, budget year, kind", () => {
    const q = P.trQuery(
      { fiscal_year: 2025, budget_fiscal_year: "2024", org: "Make: STEAM", ein: "47-2123500", member: "Gutiérrez", resolution: "1013", date_from: "2025-08-01", date_to: "2025-08-31", action: "purpose_to" },
      0
    );
    expect(q.params).toEqual([2025, 2024, "make: steam", "472123500", "472123500", "gutierrez", "1013", "2025-08-01", "2025-08-31", "purpose_to"]);
    expect(q.sql).toContain("resolution_date >= ?");
    expect(q.sql).toContain("hidden_text");
    expect(q.sql).toMatch(/ORDER BY resolution_date DESC/);
  });
  test("a date that is not YYYY-MM-DD is ignored rather than compared as text", () => {
    expect(P.trQuery({ date_from: "8/1/2025", date_to: "" }, 0).params).toEqual([]);
  });
  test("totals by kind of change; rows with no dollar amount count as rows, not dollars", () => {
    const r = P.rollupTr([
      { action: "designate", agency_side: 0, n: 3, amount: 3000, no_amount: 0 },
      { action: "listed", agency_side: 0, n: 2, amount: 0, no_amount: 2 },
    ]);
    expect(r.matched).toBe(5);
    expect(r.byAction.listed).toEqual({ n: 2, amount: 0, no_amount: 2 });
    expect(P.trTotalsQuery({}).sql).toContain("SUM(amount)");
  });
  test("a City agency's own lines (agency side) are totaled apart from money to or from organizations", () => {
    const r = P.rollupTr([
      { action: "rescind", agency_side: 0, n: 4, amount: -310, no_amount: 0 },
      { action: "rescind", agency_side: 1, n: 2, amount: -1073, no_amount: 0 },
      { action: "designate", agency_side: 1, n: 1, amount: 73, no_amount: 0 },
    ]);
    expect(r.byAction.rescind.amount).toBe(-310);
    expect(r.byAction.designate).toBeUndefined();
    expect(r.agencyByAction).toEqual({ rescind: { n: 2, amount: -1073, no_amount: 0 }, designate: { n: 1, amount: 73, no_amount: 0 } });
    expect(r.matched).toBe(7);
    expect(P.trTotalsQuery({}).sql).toContain("COALESCE(agency_side, 0) AS agency_side");
  });
  test("the page renders its labeled filters, or says there is no data", () => {
    expect(page(Transparency, [])).toContain("No transparency resolution data");
    const out = page(Transparency, [year("transparency", 2025)]);
    for (const l of ["Year of the resolutions", "Budget year changed", "Organization", "EIN (tax ID)", "Council member", "Resolution number", "Adopted on or after", "Adopted on or before", "Kind of change"]) {
      expect(out).toContain(`<span>${l}</span>`);
    }
    expect(out).toContain('type="date"');
    expect(out).toContain('aria-describedby="tr-reso-help"');
  });
});

describe("the capital book", () => {
  test("filters: project ID, sponsor, borough (any case), agency, title or FY2019 description, budget line, part, year, amounts", () => {
    const q = P.bookQuery({ fiscal_year: 2019, sub_id: "cn001", sponsor: "CD 22", boro: "k", agency: "library", title: "heating", budget_line: "lb-d104", part: "I", min_amount: "-50000", max_amount: 0 }, 0);
    expect(q.params).toEqual([2019, "cn001", "cd 22", "cd 22", "K", "library", "heating", "heating", "LB D104", "I", -50000, 0]);
    expect(q.sql).toContain("upper(boro) = ?");
    expect(q.sql).toContain("description");
    expect(q.sql).toContain("council_district");
    expect(q.sql).toMatch(/ORDER BY fiscal_year DESC, part, pdf_page, row_in_page/);
  });
  test("negative amounts and vacant-district sponsors are counted on their own (#206)", () => {
    const t = P.bookTotalsQuery({}).sql;
    expect(t).toContain("negative_rows");
    expect(t).toContain("vacant_rows");
    expect(P.isVacantDistrict("CD 22")).toBe(true);
    expect(P.isVacantDistrict(" cd48 ")).toBe(true);
    expect(P.isVacantDistrict("SPEAKER, AVILÉS")).toBe(false);
    expect(P.isVacantDistrict("")).toBe(false);
  });
  test("#205: a SUB ID printed twice gets only its own row's NYC Open Data match", () => {
    // FY2025 prints E CN810 on two Part I rows (#142); the crosswalk keys each on its place.
    const xs = [
      { fiscal_year: 2025, record_row: "E CN810", record_part: "p19r12", record_amount_fy: 2025, portal_row_id: "row-7h42-r8im.3gyn" },
      { fiscal_year: 2025, record_row: "E CN810", record_part: "p29r21", record_amount_fy: 2025, portal_row_id: "row-byw5.wrq2_k74t" },
      { fiscal_year: 2025, record_row: "E CN811", record_part: null, record_amount_fy: 2025, portal_row_id: "row-other" },
      { fiscal_year: 2024, record_row: "E CN810", record_part: null, record_amount_fy: 2024, portal_row_id: "row-fy24" },
    ];
    const first = P.odForBookRow(xs, { fiscal_year: 2025, sub_id: "E CN810", pdf_page: 19, row_in_page: 12, id_rows: 2 });
    const second = P.odForBookRow(xs, { fiscal_year: 2025, sub_id: "E CN810", pdf_page: 29, row_in_page: 21, id_rows: 2 });
    expect(first.map((x) => [x.portal_row_id, x.exact])).toEqual([["row-7h42-r8im.3gyn", true]]);
    expect(second.map((x) => [x.portal_row_id, x.exact])).toEqual([["row-byw5.wrq2_k74t", true]]);
    // An ID printed once has no place in its key, and keeps its match as its own.
    expect(P.odForBookRow(xs, { fiscal_year: 2025, sub_id: "E CN811", pdf_page: 3, row_in_page: 1, id_rows: 1 }).map((x) => [x.portal_row_id, x.exact])).toEqual([["row-other", true]]);
    expect(P.bookPlace({ pdf_page: "19", row_in_page: "12" })).toBe("p19r12");
  });
  test("an ID printed on two rows (Part I and Part II) with no place recorded: matched on the ID only, on both rows", () => {
    const xs = [{ fiscal_year: 2027, record_row: "AG CC1053", record_part: null, record_amount_fy: 2027, portal_row_id: "row-x" }];
    for (const row of [{ part: "I", pdf_page: 4, row_in_page: 2 }, { part: "II", pdf_page: 63, row_in_page: 1 }]) {
      const [m] = P.odForBookRow(xs, { fiscal_year: 2027, sub_id: "AG CC1053", id_rows: 2, ...row });
      expect(m.exact).toBe(false);
    }
    expect(P.OD_SUB_ID_ONLY).toBe("matched on project ID only, not to this exact row");
    expect(P.bookQuery({}, 0).sql).toContain("AS id_rows");
  });
  test("the book's total is Part I; Part II's rows are counted apart (Noel, PR #224)", () => {
    const t = P.bookTotalsQuery({ fiscal_year: 2027 }).sql;
    expect(t).toMatch(/SUM\(amount_y1\) FILTER \(WHERE part = 'I'\), 0\) AS y1/);
    for (const c of ["part1_n", "noncity_y1", "part2_y1", "part2_only_n", "part2_only_y1"]) expect(t).toContain(c);
    const o = P.bookPart2OnlyQuery({ fiscal_year: 2027 });
    expect(o.sql).toContain("part = 'II'");
    expect(o.sql).toContain("NOT EXISTS");
    expect(o.params).toEqual([2027]);
    expect(P.bookQuery({}, 0).sql).toContain("AS in_other_part");
  });
  test("the MA series gets the Council Finance label; other Part-II-only rows do not", () => {
    expect(P.isMaSeries("PV MA0005")).toBe(true);
    expect(P.isMaSeries("E MA0001")).toBe(true);
    expect(P.isMaSeries("PV MM0001")).toBe(false);
    expect(P.isMaSeries("HL TA001")).toBe(false);
    expect(P.MA_QUESTION_LABEL).toBe("question sent to Council Finance");
  });
  test("a printed dash is shown as a dash, not $0 (FY2019)", () => {
    expect(P.printedDash("-")).toBe(true);
    expect(P.printedDash(" – ")).toBe(true);
    expect(P.printedDash("0")).toBe(false);
    expect(P.printedDash("")).toBe(false);
    expect(P.bookQuery({}, 0).sql).toContain("amount_y4_printed");
  });
  test("the borough list has the five boroughs and A and C as printed", () => {
    expect(P.BOOK_BOROUGHS.map(([k]) => k)).toEqual(["K", "M", "Q", "R", "X", "A", "C"]);
    expect(Object.fromEntries(P.BOOK_BOROUGHS).A).toBe("A (as printed)");
  });
  test("the Open Data query asks once per (year, SUB ID)", () => {
    expect(P.odForBookRowsQuery([])).toBeNull();
    const q = P.odForBookRowsQuery([
      { fiscal_year: 2025, sub_id: "E CN810" },
      { fiscal_year: 2025, sub_id: "E CN810" },
      { fiscal_year: 2024, sub_id: "HL TA001" },
    ]);
    expect(q.params).toEqual([2025, "E CN810", 2024, "HL TA001"]);
    expect(q.sql).toContain("x.record_pdf = 1");
  });
  test("the page renders its labeled filters, or says there is no data", () => {
    expect(page(Book, [])).toContain("No capital book data");
    const out = page(Book, [year("capital_sd", 2019)]);
    for (const l of ["Fiscal year", "Project ID (SUB ID)", "Sponsor", "Borough", "Agency", "Title or description", "Budget line", "Part of the book"]) {
      expect(out).toContain(`<span>${l}</span>`);
    }
  });
});

describe("Terms and Conditions: book-order numbers (#206)", () => {
  test("FY2018 and FY2021–FY2024 say the number is the order in the book; other years show the printed number", () => {
    for (const fy of [2018, 2021, 2022, 2023, 2024]) expect(P.termsNumberLabel(fy, 16)).toBe("No. 16 (book order)");
    for (const fy of [2025, 2026, 2027]) expect(P.termsNumberLabel(fy, 3)).toBe("No. 3");
  });
  test("ordinals", () => {
    expect([1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 101, 111].map(P.ordinal)).toEqual(["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "23rd", "101st", "111th"]);
  });
  test("the page says which years are numbered in book order", () => {
    const out = page(Terms, [year("terms", 2018), year("terms", 2027)]);
    expect(out).toContain("print no item numbers");
    expect(page(Terms, [year("terms", 2027)])).not.toContain("print no item numbers");
  });
});
