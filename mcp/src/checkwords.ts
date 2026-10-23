/**
 * The check codes of the PDF review (`H8.lattice`, `W.fiscal_conduit`, `T7.overfull`, ...) in
 * plain words, ONE table for both front ends: the MCP imports this module, and the explorer
 * imports the compiled mcp/dist/checkwords.js (as it does rowlinks.js), so an answer and the
 * explorer never word the same check two ways.
 *
 * The codes are written by the readers and review scripts (code/schedc/checks.py,
 * code/transreso/checks.py, code/parse_*_v2.py, code/review_capital_sd.py, code/review_terms.py)
 * into the promoted review files' `check_id` and the rows' `flags` (data/fy* /pdf/). The codes stay
 * in the data and in review builds; public views and MCP answers show the sentence instead.
 *
 * Each sentence says what is odd about the PDF or about our reading of it, never about the
 * organization on the row. mcp/test/checkwords.test.js fails when a code in data/fy* /pdf/ has no
 * sentence here.
 */

/** Check code -> one short plain sentence. */
export const CHECK_WORDS: Record<string, string> = {
  // ---- Capital book (§254 supporting detail): code/review_capital_sd.py
  "C2.rescindments": "The book prints its cuts to earlier projects as one total, with no list, so only the subtraction could be checked.",
  "C3.id_reused": "The same project ID is printed on more than one project.",
  "C3.id_series": "This project ID is in a series whose meaning we have not confirmed.",
  "C3.ma_series": "These rows are printed only in Part II, in a project ID series (\"MA\" or \"MM\") that is not in the Part I total.",
  "C3.part2_only": "This row is printed only in Part II, the list of money to non-city groups, with no matching Part I row.",
  "C3.part2_vs_part1": "Part II prints this row a little differently from its Part I row.",
  "C5.geom_vs_stream": "Two ways of reading the page placed a value on different rows; we kept the one that matches the page's layout.",
  "C5.title_blank_line": "The title cell starts with an empty line; the title below it was joined to it.",
  "C6.amount_cells": "A year's amount cell holds no value or more than one; it was left blank.",
  "C6.boro": "The borough code is printed in an unusual way.",
  "C6.cell_overflow": "Some text runs slightly past the edge of its cell.",
  "C6.key_overrun": "Two words in the book's key are printed with no space between them.",
  "C6.sponsor_digit": "The sponsor cell includes a number, such as a district number.",
  "C6.sponsor_seat": "The sponsor is printed as a district seat, not a Council Member's name.",
  "C7.hairlines": "Very thin lines between rows do not show in the page image; they separate rows and hold no data.",
  "C7.rules": "A line drawn in the PDF does not show in the page image.",
  "C9.workbook": "This project is in the PDF or the Council's capital spreadsheet, but not both.",
  "C9.workbook_boro": "The borough differs from the Council's capital spreadsheet.",
  "C9.workbook_cd": "The Council district differs from the Council's capital spreadsheet.",
  "C9.workbook_description": "The description differs from the Council's capital spreadsheet.",
  "C9.workbook_no_amount": "The Council's capital spreadsheet has no amount for this project, so the amounts could not be compared.",
  "C9.workbook_sponsor": "The sponsor is worded differently in the Council's capital spreadsheet.",
  "C9.workbook_text": "Some accented letters are garbled in the Council's capital spreadsheet; they were fixed before comparing.",
  "C9.workbook_title": "The project title is worded differently in the Council's capital spreadsheet.",

  // ---- Schedule C: code/schedc/checks.py, code/parse_schedule_c_v2.py
  "H5.anchors": "A value on this row does not look like what its column should hold, such as an EIN in an unusual form.",
  "H6.furniture": "Some text on this row looks like page furniture (a header or footer) and was checked by a person.",
  "H8.image_only_row": "The page image shows a row that the PDF's text layer does not.",
  "H8.lattice": "Two readings of the page (the PDF's text and its image) split this row differently.",
  "H9.ink": "There is printed ink on the page that no row we read covers.",
  "H10.category_total": "The PDF's printed category total does not equal the sum of its lines.",
  "H10.no_summary": "This category prints no summary table or total.",
  "H11.box_alias": "An initiative's name is printed slightly differently in the summary and in its box.",
  "H11.box_amount_read": "A box amount is misprinted in the PDF; it was read from the printed summary.",
  "H12.designated_sum": "An initiative's rows do not add up to its printed amount.",
  "H12.initiative_pages": "These rows are printed on pages out of order and were matched to their initiative by a person.",
  "H12.statement_adds_up": "An initiative's written statement gives amounts that do not add up to its printed amount.",
  "H12.table_total": "A table's printed total does not equal the sum of its rows.",
  "H13.rollup": "The book's category totals do not exactly equal the sum of its rows; we traced the gap to specific pages.",
  "K.box_amount": "A box prints a different amount from its summary line.",
  "K.ein_other_org": "The EIN printed on this row belongs to a different organization.",
  "K.ein_repeated": "The PDF prints the EIN of the row above on this row too.",
  "K.ein_shift": "Some EINs on this page appear to be printed one row off.",
  "K.ein_two_values": "The PDF prints two different EINs for this organization.",
  "K.side_list": "This is a list printed under one award, showing who the money passes to; it is not counted twice.",
  "K.statement_typo": "The printed statement has a typo in an amount.",
  "K.text_layer": "The PDF's text layer and the printed page differ slightly; the text layer is kept.",

  // ---- Transparency resolutions: code/transreso/checks.py, code/parse_transparency_v2.py
  "K.adopted_before_fy": "This resolution is dated before its fiscal year began.",
  "K.no_fiscal_year": "This chart prints no fiscal year.",
  "K.no_resolution_number": "The PDF prints no resolution number.",
  "K.repeated_chart": "The same rows are printed more than once in this resolution.",
  "T3.chart_number": "A chart's caption prints a different number from the one it is read as.",
  "T3.continued_missing": "A chart continues on the next page without the word \"continued\".",
  "T3.continued_number": "A \"continued\" caption prints a different chart number.",
  "T3.continued_start": "A chart's first page is marked \"continued\".",
  "T3.label_page": "A page holds only a footnote and a page label.",
  "T3.page_label": "A chart page prints no page label.",
  "T4.blank_header": "A chart's header row is blank, so the previous page's header was used.",
  "T4.no_amount": "This chart prints no dollar amounts.",
  "T5.anchors": "This row prints no EIN, or an EIN in an unusual form.",
  "T5.text_below_table": "A few characters are printed just below the table and were read into its last row.",
  "T6.footnote": "A footnote in the PDF explains this chart.",
  "T7.overfull": "Text in a cell is longer than the cell, so part of it is hidden on the printed page.",
  "T7.overlaid": "Text is drawn on top of this row's cell and is hidden on the printed page.",
  "T11.markers": "A footnote mark on this row does not match the footnotes printed.",
  "T12.fiscal_year": "A chart prints no fiscal year, or one that differs from the resolution's text.",
  "T13.printed_date": "The date printed on the resolution differs from the adoption date in the Council's legislative record.",

  // ---- Terms and Conditions: code/review_terms.py
  "T2.heading_not_bold": "An item's heading is printed in regular type, not bold.",
  "T2.no_agency_code": "An agency is printed with no agency code.",
  "T3.body_vs_heading": "An item's heading names budget units or lines that its text does not.",
  "T7.old_csv": "This item was missing from an older copy of the data.",
  "T7.old_csv_agency": "The agency differs from an older copy of the data.",
  "T7.old_csv_text": "The text differs from an older copy of the data.",
  "T7.old_csv_units": "The budget units differ from an older copy of the data.",

  // ---- Warnings shared by the readers (routine notes on how a page was printed)
  "W.amount_bare": "The amount is printed without a dollar sign.",
  "W.amount_cents": "The amount is printed with cents.",
  "W.amount_format": "The amount is printed in an unusual format.",
  "W.amount_no_dollar": "The amount is printed without a dollar sign.",
  "W.amount_odd_format": "The amount is printed with cents or a trailing period.",
  "W.amount_split_digits": "The amount's digits are split across two cells and were joined.",
  "W.amount_zero": "The amount is printed as $0.",
  "W.asterisk": "The PDF prints a * on this row; its footnote says a City review step was not finished when the budget was adopted.",
  "W.band_header": "Part of the table's header is printed outside its cells.",
  "W.banner_variant": "A category banner is printed in an unusual layout.",
  "W.box_amount_cells": "A box amount is printed across several cells.",
  "W.box_amount_loose": "A box amount is printed outside the box.",
  "W.box_amount_no_dollar": "A box amount is printed without a dollar sign.",
  "W.box_title_above": "A box's title is printed above the box.",
  "W.caption_format": "A chart caption is printed in an unusual format.",
  "W.cid_glyph": "The PDF has a character that does not display (shown as an empty box).",
  "W.clipped_text": "Some text is hidden under the next cell on the printed page.",
  "W.conduit_ein": "The fiscal conduit's EIN is not readable on the page.",
  "W.continuation_row": "This row continues onto a second line or page.",
  "W.edited_after_export": "Some text on this row is in a different font, which suggests it was added after the PDF was exported.",
  "W.ein_no_hyphen": "The EIN is printed without its hyphen.",
  "W.ein_overflow_hyphen": "The EIN's hyphen runs into the next cell.",
  "W.fiscal_conduit": "The PDF prints something in the fiscal-conduit column for this row, usually a group that receives the money for the one listed.",
  "W.fy2030_wrapped_below": "A year's amount is printed just below the row's line.",
  "W.geom_near": "Some text sits just outside its row's lines and was joined to the nearest row.",
  "W.header_span_cell": "A header cell spans more than one column.",
  "W.headerless_table": "This table has no header row on its page; the header from the page before was used.",
  "W.hrule_table": "This table is drawn with horizontal lines only.",
  "W.loose_header": "The table's header is printed above the table, outside its lines.",
  "W.made_cell": "No cell is drawn under a column on this row; it was read from the header's column.",
  "W.made_cell_empty": "No cell is drawn under a column on this row, and the space is empty.",
  "W.midword_wrap": "A word is split across two lines in the PDF.",
  "W.prequal_star_in_org": "A * is printed at the end of the organization's name, not in the * column.",
  "W.shared_column": "Two values are printed in one cell and were split.",
  "W.sliver_char": "A letter printed in a narrow gap was joined to the text beside it.",
  "W.spanning_cell": "A cell on this row spans more than one column.",
  "W.sponsor_wrapped_below": "The sponsor's name wraps below the row's line.",
  "W.star_in_cell": "A * is printed at the end of a cell, not in a * column.",
  "W.subheading": "This row sits under a sub-heading, which is kept with it.",
  "W.summary_amount_doubled": "A summary amount's text is in the PDF twice; the page shows it once.",
  "W.summary_amount_no_dollar": "A summary amount is printed without a dollar sign.",
  "W.unpaired_purpose": "This change of purpose has no matching opposite entry in its chart.",
  "W.wrap_hyphen": "A line ends in a hyphen and was joined to the next line.",
  "W5.wrap_hyphen": "A line ends in a hyphen; we kept it joined to the next line.",
};

/** The sentence for a check we have no entry for (the test keeps this from showing). */
export const UNKNOWN_CHECK = "A check on how this row was read from the PDF.";

/** One check code in plain words. */
export function checkWords(code: unknown): string {
  return CHECK_WORDS[String(code ?? "").trim()] ?? UNKNOWN_CHECK;
}

/** The plain sentences for a row's `;`-joined flags, each once, in the row's order. */
export function flagWords(flags: unknown): string[] {
  const out: string[] = [];
  for (const f of String(flags ?? "").split(";").map((s) => s.trim()).filter(Boolean)) {
    const w = checkWords(f);
    if (!out.includes(w)) out.push(w);
  }
  return out;
}

/** A review row's `field` (one or more columns, `;`-joined) in plain words. */
export const FIELD_WORDS: Record<string, string> = {
  org: "organization name",
  ein: "EIN",
  amount: "amount",
  member: "Council Member",
  sponsor: "sponsor",
  agency: "agency",
  purpose: "purpose",
  title: "project title",
  boro: "borough",
  description: "description",
  conduit: "fiscal conduit",
  program_or_subheading: "program or sub-heading",
  resolution_date: "resolution date",
  resolution_number: "resolution number",
  budget_fiscal_year: "fiscal year",
  report_content: "report",
  fy2027: "FY2027 amount",
  fy2028: "FY2028 amount",
  fy2029: "FY2029 amount",
  fy2030: "FY2030 amount",
  "*": "* column",
  "New Purpose of Funds": "new purpose of funds",
};

/**
 * A review row's note in plain words, derived by rule: the check's sentence, then the parts of the
 * row it is about ("Part of the row: organization name, EIN."), where `field` names known columns. The reviewer's own note (what_to_check)
 * is shorthand for reviewers, so it is not shown in public; it stays in the data and in review
 * builds. Unknown field values (an initiative's name, a terms item number) are left out.
 */
export function plainReviewNote(r: { check_id?: unknown; field?: unknown }): string {
  const words = checkWords(r.check_id);
  const fields = [...new Set(String(r.field ?? "").split(";").map((s) => FIELD_WORDS[s.trim()]).filter(Boolean))];
  return fields.length ? `${words} Part of the row: ${fields.join(", ")}.` : words;
}

/**
 * A row's flags in plain words, less those its review entries already say: a plain note starts
 * with its check's sentence (plainReviewNote), so a sentence is left out when a note starts with
 * it. The public explorer carries no check id, so both front ends match on the sentence.
 */
export function otherFlagWords(flags: unknown, plainNotes: readonly unknown[]): string[] {
  const said = plainNotes.map((n) => String(n ?? ""));
  return flagWords(flags).filter((w) => !said.some((p) => p.startsWith(w)));
}
