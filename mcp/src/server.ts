/**
 * MCP server: tool definitions + call routing for the NYC budget data.
 *
 * 2.0.0 serves structured sources only: the NYC Council's expense funding disclosure workbooks
 * and its capital designations (Council workbooks and NYC Open Data t474-a92g), with OMB's
 * adopted capital budget as a by-line comparison. Every PDF-derived dataset and the five tools
 * built on it were removed; calling one of them returns its migration note (REMOVED_TOOLS).
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { readFileSync } from "fs";
import { z } from "zod";
import {
  searchDisclosure,
  listDisclosureYears,
  searchCapital,
  listCapitalSources,
  compareCapitalToOmb,
  listOmbComparisonYears,
  normEin,
  normBudgetLine,
  normProjectId,
  DISCLOSURE_STATUSES,
  ZIP_STATUSES,
  OMB_VERDICTS,
  type CapitalResult,
  type CapitalRow,
  type CapitalSource,
  type DisclosureResult,
  type DisclosureRow,
  type DisclosureYear,
  type OmbComparisonResult,
} from "./db.js";

const PACKAGE_VERSION = (
  JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf-8")) as { version: string }
).version;

const REPO_URL = "https://github.com/BetaNYC/New-York-City-Budget";

const n = (x: number) => x.toLocaleString("en-US");

/** Dollars, rounded to cents for display (disclosure amounts and their sums can be fractional). */
const usd = (v: number): string => {
  const c = Math.round(v * 100) / 100;
  const s = Math.abs(c).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
  return c < 0 ? `-$${s}` : `$${s}`;
};

const errorResult = (text: string) => ({ content: [{ type: "text", text: `Error: ${text}` }], isError: true });
const textResult = (text: string) => ({ content: [{ type: "text", text }] });

/** "2009, 2011–2027" from a sorted year list. */
function yearSpan(years: number[]): string {
  const parts: string[] = [];
  for (let i = 0; i < years.length; ) {
    let j = i;
    while (j + 1 < years.length && years[j + 1] === years[j] + 1) j++;
    parts.push(i === j ? `FY${years[i]}` : `FY${years[i]}–FY${years[j]}`);
    i = j + 1;
  }
  return parts.join(", ") || "(none)";
}

// ===========================================================================
// search_disclosure_awards
// ===========================================================================

const DISCLOSURE_FOOTER = `
---
Source: the NYC Council's expense funding disclosure workbooks — from the Council Research & Data site (https://rnd.council.nyc.gov/expense_funding/) or, for FY2009, FY2011 and FY2012, the Council's own archived workbooks retrieved through the Internet Archive — as downloaded on the date shown per year; parsed by BetaNYC (code/parse_expense_disclosure.py in ${REPO_URL}). Amounts are the workbook's own. Served by @betanyc/nyc-budget-mcp v${PACKAGE_VERSION}.`.trim();

/** One line, always present: the ways this source is commonly misread. */
const DISCLOSURE_CAVEAT =
  "Caveat: council_member is the Council's roster when the workbook was exported, not necessarily the member who sponsored the designation; the disclosure includes designations made after adoption, so it is not the adopted budget's Schedule C; status is a moment — Pending rows clear over time, so the Cleared figure is the headline, except in an early-snapshot year; the address is the grantee's mailing address as printed, not where services were delivered.";

/** #70: what each zip_status says about the derived zip, shown after it on every row. */
const ZIP_STATUS_NOTE: Record<string, string> = {
  valid: "a 2020 Census ZCTA",
  padded: "leading zero restored; in-state 2020 ZCTA",
  trimmed: "first five digits of a ragged ZIP+4; in-state 2020 ZCTA",
  repaired_extra_digit: "six digits printed; the only one-digit deletion that is an in-state 2020 ZCTA",
  ambiguous_extra_digit: "six digits printed; more than one one-digit deletion is an in-state 2020 ZCTA, none picked",
  not_a_zcta: "not a 2020 ZCTA: not verified, not fake (PO-box ZIPs have none)",
  state_mismatch: "a 2020 ZCTA in another state than the row's",
  invalid: "no ZIP could be read from the cell",
  blank: "no ZIP printed",
};

const ROW_FLAG_NOTE: Record<string, string> = {
  not_an_award: "not_an_award: printed as a designation but not a grant to an organization (a lump allocation on the City's own EIN with no address); kept and counted in totals, as published",
};

/** The grantee mailing address as printed, then the derived zip and its status. */
function addressLine(r: DisclosureRow): string {
  const street = [r.address1, r.address2, r.city].filter((x) => x && x.trim() !== "").join(", ");
  const tail = [r.state, r.postal_code].filter((x) => x && x.trim() !== "").join(" ");
  const printed = [street, tail].filter((x) => x !== "").join(", ") || "(none printed)";
  return (
    `\n    grantee mailing address: ${printed}` +
    ` · zip ${r.zip || "—"} (${r.zip_status}: ${ZIP_STATUS_NOTE[r.zip_status] ?? "unknown status"})` +
    (r.zip_candidates ? ` · candidates ${r.zip_candidates.split(";").join(", ")}` : "")
  );
}

/** #72: how the printed council_member resolved, in brackets after the name. */
function memberTag(r: DisclosureRow): string {
  switch (r.council_member_type) {
    case "member":
      return ` [Legistar person ${r.council_member_id}]`;
    case "member_outside_fy":
      return ` [Legistar person ${r.council_member_id}; no recorded vote in FY${r.fiscal_year}: the export-time roster]`;
    case "ambiguous":
      return " [ambiguous: more than one member of that name served this year; not resolved]";
    case "unresolved":
      return " [not a Legistar member name; not resolved]";
    case "district_label":
      return " [a district label, not a person]";
    default:
      return ""; // speaker, delegation, citywide, blank: the printed value says what it is
  }
}

function disclosureRowLine(r: DisclosureRow): string {
  return (
    `FY${r.fiscal_year}` +
    (r.mocs_id ? ` · ${r.mocs_id}` : "") +
    ` · ${usd(r.amount)} · ${r.status || r.status_norm}` +
    ` · ${r.council_member || "(no member)"}${memberTag(r)} → ${r.legal_name} (EIN ${r.ein || "—"})` +
    (r.source ? ` · source: ${r.source}` : "") +
    (r.agency ? ` · agency: ${r.agency}` : "") +
    (r.program_name ? `\n    program: ${r.program_name}` : "") +
    addressLine(r) +
    (r.fiscal_conduit
      ? `\n    fiscal conduit: ${r.fiscal_conduit}${r.fiscal_conduit_ein ? ` (EIN ${r.fiscal_conduit_ein})` : ""}`
      : "") +
    (r.od_mocs_id ? `\n    NYC Open Data 4d7f-74pe MOCS ID ${r.od_mocs_id} (cross-reference; amounts agree: ${r.od_match})` : "") +
    (r.row_flag ? `\n    row_flag ${ROW_FLAG_NOTE[r.row_flag] ?? r.row_flag}` : "") +
    `\n    workbook row ${r.source_row}` +
    (r.duplicate_group != null
      ? r.duplicate_group === r.source_row
        ? " · exact-copy group: first of the rows printed identically (duplicate_group " + r.duplicate_group + ")"
        : ` · exact copy of workbook row ${r.duplicate_group} (duplicate_group ${r.duplicate_group})`
      : "")
  );
}

/** A disclosure_years note without its own leading label ("not loaded: ", "early snapshot: "). */
const noteText = (note: string) => note.replace(/^(not loaded|early snapshot):\s*/i, "");

/** One year's provenance: file, sheet, where it came from, when we downloaded it. */
function snapshotLine(s: DisclosureYear): string {
  const where =
    s.source_kind === "internet_archive"
      ? `Internet Archive capture ${s.wayback_timestamp} of ${s.url}`
      : `Council RnD site, ${s.url}`;
  return (
    `  FY${s.fiscal_year}: ${s.file}, sheet "${s.sheet}", retrieved ${s.retrieved} (sha256 ${s.sha256.slice(0, 12)}), from the ${where}` +
    (s.early_snapshot ? `\n    EARLY SNAPSHOT: ${noteText(s.note)}` : "")
  );
}

/** The coverage statement every disclosure answer carries (FY2010's exclusion, the early snapshots). */
function disclosureCoverage(years: DisclosureYear[]): string {
  const loaded = years.filter((y) => y.loaded).map((y) => y.fiscal_year);
  const excluded = years.filter((y) => !y.loaded);
  const early = years.filter((y) => y.loaded && y.early_snapshot).map((y) => `FY${y.fiscal_year}`);
  return (
    `Coverage: ${yearSpan(loaded)}.` +
    excluded.map((y) => ` FY${y.fiscal_year} is NOT included (the Council's workbook for it exists but is not loaded; see list_available_fiscal_years).`).join("") +
    (early.length ? ` Early snapshots, whose Cleared totals are not headline figures: ${early.join(", ")}.` : "")
  );
}

function disclosureText(res: DisclosureResult, coverage: string): string {
  const t = res.totals;
  const all = t.cleared.rows + t.pending.rows + t.other.rows;
  const allAmt = t.cleared.amount + t.pending.amount + t.other.amount;
  const shown = res.rows.length;
  const early = res.snapshots.filter((s) => s.early_snapshot && res.by_year.some((y) => y.fiscal_year === s.fiscal_year));
  const allEarly = early.length > 0 && early.length === res.by_year.length;
  const L: string[] = [
    `${n(res.matched)} matching designation(s) in the Council's expense funding disclosure. ` +
      (shown < res.matched
        ? `Showing ${shown} of ${n(res.matched)}, highest amount first — the totals below cover all ${n(res.matched)}. Narrow the filters or raise limit (max 500) to see more rows.`
        : `Showing all ${shown}, highest amount first.`),
    "",
    `Totals over all ${n(res.matched)} match(es):`,
    `  Cleared${allEarly ? " (early snapshot, not a headline)" : " (headline)"}: ${n(t.cleared.rows)} row(s), ${usd(t.cleared.amount)}`,
    `  Pending:            ${n(t.pending.rows)} row(s), ${usd(t.pending.amount)}`,
  ];
  if (t.other.rows) L.push(`  Other status:       ${n(t.other.rows)} row(s), ${usd(t.other.amount)}`);
  L.push(`  All statuses (not a headline figure): ${n(all)} row(s), ${usd(allAmt)}`);
  if (early.length && !allEarly)
    L.push(
      `  Includes early-snapshot year(s) ${early.map((s) => `FY${s.fiscal_year}`).join(", ")}: the Cleared figure above mixes them in; read the per-year split.`
    );
  if (res.by_year.length > 1) {
    L.push("", "By fiscal year (cleared / pending):");
    for (const y of res.by_year) {
      const isEarly = early.some((s) => s.fiscal_year === y.fiscal_year);
      L.push(
        `  FY${y.fiscal_year}${isEarly ? " (early snapshot)" : ""}: cleared ${n(y.totals.cleared.rows)} row(s) ${usd(y.totals.cleared.amount)} · ` +
          `pending ${n(y.totals.pending.rows)} row(s) ${usd(y.totals.pending.amount)}` +
          (y.totals.other.rows ? ` · other ${n(y.totals.other.rows)} row(s) ${usd(y.totals.other.amount)}` : "")
      );
    }
  }
  for (const col of ["council_member", "source", "agency"] as const) {
    const vals = res.matched_values[col];
    if (!vals || vals.length < 2) continue;
    const list = vals
      .slice(0, 15)
      .map(
        (v) =>
          `${v.value || "(blank)"}${v.council_member_id ? ` [Legistar person ${v.council_member_id}]` : ""} (${n(v.rows)} row(s), ${usd(v.amount)})`
      );
    L.push(
      "",
      `Note: the ${col} filter is a substring match and matched ${n(vals.length)} different ${col === "council_member" ? "name/person pairs" : "values"}; the totals above combine them: ` +
        list.join("; ") + (vals.length > 15 ? `; and ${n(vals.length - 15)} more` : "") +
        (col === "council_member" ? ". For one person exactly, use council_member_id." : col === "source" ? ". For one stream exactly, use source_exact." : ".")
    );
  }
  if (res.ein_legal_names != null && res.ein_legal_names > 1)
    L.push(
      "",
      `Note: ${n(res.ein_legal_names)} different legal names carry this EIN in the match. One EIN can pool many bodies: a fiscal sponsor's projects, or, for 136400434 (the City of New York), hundreds of City agencies, schools and programs. Read the names, not just the EIN.`
    );
  if (res.duplicates.rows > 0)
    L.push(
      "",
      `Note: ${n(res.duplicates.rows)} of the matched rows are exact copies (${n(res.duplicates.groups)} group(s) of rows identical in every published field but their workbook row; marked "exact copy" below). ` +
        `The workbooks print every copy and the totals above include them all. ${n(res.duplicates.extra_rows)} row(s), ${usd(res.duplicates.extra_amount)}, are copies beyond the first of their group; ` +
        `whether each is a real second designation or a filing error cannot be told from the workbook.`
    );
  for (const fl of res.flagged)
    L.push(
      "",
      `Note: ${n(fl.rows)} matched row(s), ${usd(fl.amount)}, carry row_flag ${fl.row_flag} (${ROW_FLAG_NOTE[fl.row_flag] ?? "see DATA-DICTIONARY.md"}). Subtract them yourself when you mean money to organizations.`
    );
  if (res.no_ein.rows > 0)
    L.push(
      "",
      `Note: ${n(res.no_ein.rows)} matched row(s), ${usd(res.no_ein.amount)}, print no grantee EIN (blank, or text with no digits such as "NA"; shown as "EIN —"). They are counted in the totals above. Some name an initiative or program rather than an organization (FY2009's largest is "School Budget Restoration", $120,000,000); read their legal_name before counting them as money to an organization.`
    );
  L.push("", "Snapshot (which download each year comes from):", ...res.snapshots.map(snapshotLine));
  L.push("", coverage);
  L.push("", "Rows:", ...res.rows.map(disclosureRowLine), "", DISCLOSURE_CAVEAT);
  return L.join("\n");
}

// ===========================================================================
// search_council_capital
// ===========================================================================

const CAPITAL_FOOTER = `
---
Source: the NYC Council's capital designations — the Council's own capital workbooks (FY2015–FY2017 and FY2026 from Internet Archive captures, FY2027 downloaded from the Council RnD site) and, for FY2019–FY2025, NYC Open Data t474-a92g, published by the Council — built by BetaNYC (code/build_capital_council.py, data/capital/ in ${REPO_URL}). Amounts are as published. Served by @betanyc/nyc-budget-mcp v${PACKAGE_VERSION}.`.trim();

const CAPITAL_CAVEAT =
  "Caveat: FY2018 is missing (no Council workbook found, and t474-a92g starts at FY2019). A Council project ID is internal to budget negotiations, unique within one year only, and not an FMS/Checkbook project ID; the only key shared with OMB is the budget line, so any link from a row to a city project or contract would be a match by budget line and title, which this tool does not make, and there is no contract-level data here. sponsor is the surname or body as printed, with no Legistar ID attached (one surname can be different members in different years). The codes borough A, council district 80, ID prefix CC and ID type PN are not in the Council's data dictionary and their meaning is unconfirmed. Sums are this repo's arithmetic, not a Council figure (FY2015 and FY2016 print totals, and the rows equal them).";

const SOURCE_KIND_LABEL: Record<string, string> = {
  council_workbook: "Council capital workbook",
  open_data_t474: "NYC Open Data t474-a92g (published by the Council)",
};

function capitalSourceLine(s: CapitalSource): string {
  const where = s.wayback_timestamp
    ? `Internet Archive capture ${s.wayback_timestamp} of ${s.url}`
    : s.source_kind === "open_data_t474"
      ? "SODA API, https://data.cityofnewyork.us/resource/t474-a92g.json"
      : s.url || "(no URL recorded)";
  const updated = /rowsUpdatedAt (\d+)/.exec(s.note);
  return (
    `  FY${s.report_year}: ${SOURCE_KIND_LABEL[s.source_kind] ?? s.source_kind}, ${s.source_file} (${where}), ` +
    `retrieved ${s.retrieved}, sha256 ${s.sha256.slice(0, 12)}` +
    (updated ? `; Open Data says its rows were last updated ${new Date(Number(updated[1]) * 1000).toISOString().slice(0, 10)}` : "")
  );
}

function capitalRowLine(r: CapitalRow): string {
  const amt =
    r.amount == null
      ? "amount unknown (split_record_amount_unknown: a t474 record broken across rows; not in any total)"
      : `${usd(r.amount)} for FY${r.amount_fy}${r.amount_fy !== r.report_year ? " (out-year)" : ""}`;
  return (
    `FY${r.report_year} list · ${amt}` +
    ` · budget line ${r.budget_line_norm || (r.budget_line ? `${r.budget_line} (as printed; no budget-line shape)` : "(none printed)")}` +
    (r.project_id ? ` · project ${r.project_id}` : "") +
    ` · sponsor ${r.sponsor || "(none printed)"}` +
    (r.council_district ? ` · council district ${r.council_district}` : "") +
    (r.borough ? ` · borough ${r.borough}` : "") +
    `\n    title: ${r.title || "(none)"}` +
    (r.description ? `\n    description: ${r.description}` : "") +
    `\n    ${r.source_kind === "open_data_t474" ? `t474-a92g row ${r.source_row}` : `workbook row ${r.source_row}`}`
  );
}

function capitalText(res: CapitalResult, districtGiven: boolean): string {
  const shown = res.rows.length;
  const L: string[] = [
    `${n(res.matched)} matching row(s) in the Council's capital designations. ` +
      (shown < res.matched
        ? `Showing ${shown} of ${n(res.matched)}, highest amount first — the totals below cover all ${n(res.matched)}. Narrow the filters or raise limit (max 500) to see more rows.`
        : `Showing all ${shown}, highest amount first.`),
    "",
    `Totals over all ${n(res.matched)} match(es):`,
    `  For the list's own year (amount_fy = report year): ${n(res.report_year_amounts.rows)} row(s), ${usd(res.report_year_amounts.amount)}`,
  ];
  if (res.out_years.length)
    L.push(
      `  Out-year amounts (planned for later years, listed separately, not added above): ` +
        res.out_years.map((o) => `FY${o.amount_fy} ${n(o.rows)} row(s) ${usd(o.amount)}`).join("; ")
    );
  if (res.amount_unknown)
    L.push(`  Amount unknown (split records; in no total): ${n(res.amount_unknown)} row(s)`);
  if (res.by_report_year.length > 1) {
    L.push("", "By report year (list's own year / out-years):");
    for (const y of res.by_report_year)
      L.push(
        `  FY${y.report_year}: ${n(y.report_year_amounts.rows)} row(s) ${usd(y.report_year_amounts.amount)}` +
          (y.out_year_amounts.rows ? ` · out-years ${n(y.out_year_amounts.rows)} row(s) ${usd(y.out_year_amounts.amount)}` : "") +
          (y.amount_unknown ? ` · amount unknown ${n(y.amount_unknown)} row(s)` : "")
      );
  }
  if (res.matched_sponsors && res.matched_sponsors.length > 1) {
    const list = res.matched_sponsors
      .slice(0, 15)
      .map((v) => `${v.value || "(blank)"} (${n(v.rows)} row(s), ${usd(v.amount)})`);
    L.push(
      "",
      `Note: the sponsor filter is a substring match and matched ${n(res.matched_sponsors.length)} different values; the totals above combine them: ` +
        list.join("; ") + (res.matched_sponsors.length > 15 ? `; and ${n(res.matched_sponsors.length - 15)} more` : "") +
        ". For one value exactly, use sponsor_exact."
    );
  }
  if (districtGiven)
    L.push(
      "",
      `Note: council_district matches only rows from the Council's own workbooks. Rows from ${yearSpan(res.district_unusable_years)} (NYC Open Data t474-a92g) never match it: Open Data stored the district as a number, which collapsed every comma list ("22, 25, 29") into one integer, so no value there can be trusted to be one district. Use sponsor for those years.`
    );
  L.push("", "Sources (which file each report year comes from):", ...res.sources.map(capitalSourceLine));
  L.push("", "Rows:", ...res.rows.map(capitalRowLine), "", CAPITAL_CAVEAT);
  return L.join("\n");
}

// ===========================================================================
// compare_capital_to_omb
// ===========================================================================

const OMB_FOOTER = `
---
Source: this repo's comparison (data/capital/council_vs_omb_by_budget_line.csv, data/capital/RECONCILIATION.md §3 in ${REPO_URL}) of the Council capital table with OMB's Capital Budget on NYC Open Data (46m8-77gv), the adopted release for each first fiscal year. Served by @betanyc/nyc-budget-mcp v${PACKAGE_VERSION}.`.trim();

const OMB_CAVEAT =
  "Caveat: this is BetaNYC's arithmetic, not a Council or OMB reconciliation. For each report year it sums the Council table's rows by budget line (the list's own year and the next year) and OMB's adopted release for that first fiscal year (the last release of the year, published in July), summed over funding sources, Council-series lines only (D, DN). 'match' means both years are equal to the dollar for the LINE; it does not show that the projects under the line are the same. 'differ', 'council_only' and 'omb_only' are not errors by either party: OMB's adopted figure can include changes the Council's list does not. FY2015–FY2017 are not compared (OMB's dataset starts at FY2019; FY2016 prints no budget lines), and FY2018 has no Council list.";

const VERDICT_LABEL: Record<string, string> = {
  match: "match (both years equal)",
  differ: "differ",
  council_only: "Council only (no OMB line)",
  omb_only: "OMB only (no Council row)",
};

function ombText(res: OmbComparisonResult): string {
  const money = (v: number | null) => (v == null ? "—" : usd(v));
  const shown = res.rows.length;
  const L: string[] = [
    `${n(res.matched)} budget line(s) compared. ` +
      (shown < res.matched
        ? `Showing ${shown} of ${n(res.matched)}: lines that disagree first, then the largest first-year difference. Counts below cover all ${n(res.matched)}.`
        : `Showing all ${shown}: lines that disagree first.`),
    "",
    "Verdicts over all matches: " + OMB_VERDICTS.map((v) => `${VERDICT_LABEL[v]} ${n(res.verdicts[v])}`).join(" · "),
  ];
  if (res.by_year.length > 1) {
    L.push("", "By report year (OMB adopted release used):");
    for (const y of res.by_year)
      L.push(`  FY${y.report_year} (OMB release ${y.omb_pub_date}): ` + OMB_VERDICTS.map((v) => `${v} ${y.verdicts[v]}`).join(", "));
  }
  L.push(
    "",
    "Rows (Council / OMB, the list's year then the next year):",
    ...res.rows.map(
      (r) =>
        `FY${r.report_year} · ${r.budget_line_norm} · ${VERDICT_LABEL[r.verdict]} · OMB release ${r.omb_pub_date}` +
          `\n    FY${r.report_year}: Council ${money(r.council_y1)} / OMB ${money(r.omb_y1)} · FY${r.report_year + 1}: Council ${money(r.council_y2)} / OMB ${money(r.omb_y2)} · Council rows ${r.council_rows}`
    ),
    "",
    OMB_CAVEAT
  );
  return L.join("\n");
}

// ===========================================================================
// Tool definitions
// ===========================================================================

export const server = new Server(
  { name: "nyc-budget-mcp", version: PACKAGE_VERSION },
  { capabilities: { tools: {} } }
);

const LIMIT_DESC = "Max rows shown, 1–500 (default 50; above 500 is capped at 500, below 1 is an error). Totals always cover every match.";

export const TOOLS = [
  {
    name: "search_disclosure_awards",
    description: `Search the NYC Council's expense funding disclosure — the Council's own award-level list of discretionary expense designations, FY2009 and FY2011–FY2027 (FY2010 is NOT included: the Council's archived workbook for it is incomplete against NYC Open Data, so it is left out). One row per published row (exact copies are kept and flagged), with clearance status, funding stream, agency and the grantee's mailing address; MOCS ID from FY2024, and for FY2009–FY2021 the MOCS ID NYC Open Data gives the same designation (od_mocs_id) where the pairing is unambiguous. FY2009 and FY2013 are EARLY SNAPSHOTS: frozen while much was Pending and never revised, so their Cleared totals are not headline figures; the answer says so. This is a later snapshot than the adopted budget: it includes designations made after adoption, and council_member is the roster when the workbook was exported. Every row is returned whatever its status unless you filter on status; the response gives the TRUE number of matching rows and totals over all of them (Cleared and Pending separately), even when the rows shown are limited, plus the file, sheet, source and retrieval date of each year. Filter by any combination of fiscal_year, ein, legal_name, council_member (substring) or council_member_id (exact Legistar person ID — 'Levin' and 'Levine' are different people), source (substring) or source_exact, agency, program_name, zip (exact 5-digit), zip_status, city (exact), status, mocs_id, od_mocs_id, min_amount, max_amount. Rows come highest amount first. Purpose text is not served; each row gives its workbook row number in the source repo.`,
    inputSchema: {
      type: "object",
      properties: {
        fiscal_year: { type: "number", description: "FY2009 or FY2011–FY2027. FY2010 is not in the dataset; asking for it returns the reason." },
        ein: { type: "string", description: "Grantee tax ID: exactly 9 digits, hyphens optional (anything else is an error, never padded). Matches the grantee EIN only, not the fiscal conduit's. One EIN can cover many bodies (136400434 is the City of New York); the answer says how many legal names it matched." },
        legal_name: { type: "string", description: "Grantee legal name (substring, case-insensitive; % and _ are literal)" },
        council_member: {
          type: "string",
          description: "Council member as the workbook names them (case-insensitive substring; 'Levin' also matches 'Levine', and the answer lists every value matched with its Legistar person ID) — the roster at export time, e.g. 'Speaker' for Speaker's designations. For one person, use council_member_id.",
        },
        council_member_id: {
          type: "string",
          description: "Exact Legistar person ID of the council member (e.g. '7567' Stephen T. Levin, '7634' Mark Levine), as resolved per fiscal year by the repo's member crosswalk from the Council MCP's Legistar index. Rows whose printed name is ambiguous, unresolved, a delegation, 'Speaker' or blank carry no ID and never match. Digits only.",
        },
        source: {
          type: "string",
          description: "Funding stream as the workbook names it (case-insensitive substring; 'Youth' also matches initiatives such as 'Summer Youth Employment Program', and the answer lists every value matched): Local, Youth, Aging, Speaker's Initiative, or a citywide initiative name. For one stream exactly, use source_exact.",
        },
        source_exact: {
          type: "string",
          description: "Funding stream, exact: equal to the workbook's value ignoring case and surrounding whitespace ('Youth' matches the Youth stream only).",
        },
        agency: { type: "string", description: "City agency (substring), e.g. DYCD" },
        program_name: { type: "string", description: "Program name (substring)" },
        zip: {
          type: "string",
          description: "Grantee mailing ZIP, exactly 5 digits (anything else is an error). Matches the 5-digit zip derived from the published postal_code (ZIP+4 read to its first five; a 4-digit ZIP padded, a ragged ZIP+4 trimmed, or a 6-digit ZIP repaired, only into a 2020 ZCTA of the row's own state). Rows whose zip_status is ambiguous_extra_digit, invalid or blank have no zip and never match. A mailing address, not where services were delivered.",
        },
        zip_status: {
          type: "string",
          enum: [...ZIP_STATUSES],
          description: "How the zip was read, checked against the Census 2020 ZCTAs: valid, padded (leading zero restored), trimmed (ragged ZIP+4 such as '11203-', '11231=1020' or '11413 ZipCode2: 3929'), repaired_extra_digit (6 digits printed; exactly one one-digit deletion is an in-state ZCTA, e.g. '111691' -> 11691), ambiguous_extra_digit (6 digits; two or more deletions are, e.g. '114345' -> 11434 or 11435; no zip, candidates shown on the row), not_a_zcta (not verified, not fake: PO-box ZIPs have no ZCTA), state_mismatch, invalid (no ZIP readable), blank (none printed).",
        },
        city: {
          type: "string",
          description: "Grantee mailing city, exact match ignoring case and surrounding whitespace, as printed: 'brooklyn' matches 'Brooklyn' and 'BROOKLYN', but not the cells printed 'Brooklyn,' or 'Brooklyn NY', and 'Bronx' does not match 'The Bronx'; 'New York' is how most Manhattan rows print. Not a borough or district filter.",
        },
        status: {
          type: "string",
          enum: [...DISCLOSURE_STATUSES],
          description: "Restrict to one clearance status. Omit for all (the default; totals are still reported per status).",
        },
        mocs_id: { type: "string", description: "The workbook's own MOCS ID, exact (case and surrounding whitespace ignored), e.g. 'FY26 01234'. Printed from FY2024 only." },
        od_mocs_id: { type: "string", description: "NYC Open Data 4d7f-74pe's MOCS ID for the same designation, exact (case and surrounding whitespace ignored), e.g. 'FY09 2838'. FY2009–FY2021 only, and only where the pairing is unambiguous. A cross-reference, not a source." },
        min_amount: { type: "number", description: "Minimum designation amount, dollars (inclusive)" },
        max_amount: { type: "number", description: "Maximum designation amount, dollars (inclusive)" },
        limit: { type: "number", description: LIMIT_DESC },
      },
      additionalProperties: false,
    },
  },
  {
    name: "search_council_capital",
    description: `Search the NYC Council's capital designations (Council-funded capital projects), FY2015–FY2017 and FY2019–FY2027 (FY2018 is missing from every source found). FY2015–FY2017, FY2026 and FY2027 come from the Council's own capital workbooks, FY2019–FY2025 from NYC Open Data t474-a92g, which the Council publishes; each answer names the file, retrieval date and sha256 of every year it draws on. One row per (record, fiscal-year amount): a list's own-year amount and any out-year amounts are separate rows, totaled separately. Filter by any combination of fiscal_year (the list's year), amount_fy, budget_line (exact, e.g. 'P D018'), project_id (exact), sponsor (substring) or sponsor_exact, borough (exact code), council_district (workbook years only), title and description (substrings), min_amount, max_amount. Answers give the TRUE match count and totals over every match, highest amount first. Exact by budget line only: the Council's project IDs are internal and do not link to OMB, FMS or Checkbook projects, and there is no contract-level data. sponsor carries no Legistar ID.`,
    inputSchema: {
      type: "object",
      properties: {
        fiscal_year: { type: "number", description: "The Council capital list's fiscal year (report year): FY2015–FY2017 or FY2019–FY2027. FY2018 returns why it is missing." },
        amount_fy: { type: "number", description: "The fiscal year an amount is for: the list's own year or an out-year (e.g. fiscal_year 2027 with amount_fy 2028 gives FY2027's out-year amounts)." },
        budget_line: { type: "string", description: "Budget line, exact, as agency code then line, separated by a space or '-' ('P D018', 'PW-DN846', 'hl dn164'). A value without the separator ('PD018') is refused, because where the agency code ends cannot be told. The only key shared with OMB's capital datasets. FY2016 prints no budget lines." },
        project_id: { type: "string", description: "The Council's project ID, exact, ignoring case and runs of spaces ('E  CN459' = 'e cn459'). Unique within one year only; not an FMS or Checkbook ID. FY2015 prints none." },
        sponsor: { type: "string", description: "Sponsor as printed (case-insensitive substring; % and _ literal): a member's surname, 'Speaker', a delegation or caucus, 'Technical Adjustments'. The answer lists every value matched. No Legistar ID is attached." },
        sponsor_exact: { type: "string", description: "Sponsor, exact, ignoring case and surrounding whitespace ('Rivera' matches 'Rivera' only, not 'De La Rosa-Rivera')." },
        borough: { type: "string", description: "Borough code exactly as printed (case-sensitive): K Brooklyn, M Manhattan, Q Queens, R Staten Island, X Bronx, C citywide. 'A' (meaning unconfirmed) and FY2016's lower-case 'k' and 'x' are kept as printed and are matched only by those exact values." },
        council_district: { type: "number", description: "One council district or code, 0–99 (0 Speaker, 88–98 caucuses and delegations, 99 Technical Adjustments): matches a row whose printed district list contains it. Council-workbook years only (FY2015–FY2017, FY2026, FY2027): t474 years never match, because Open Data collapsed their district lists into single numbers." },
        title: { type: "string", description: "Project title (substring, case-insensitive; % and _ literal). In many FY2019 rows the title names the organization." },
        description: { type: "string", description: "Project description (substring, case-insensitive; % and _ literal)." },
        min_amount: { type: "number", description: "Minimum amount, dollars (inclusive)" },
        max_amount: { type: "number", description: "Maximum amount, dollars (inclusive)" },
        limit: { type: "number", description: LIMIT_DESC },
      },
      additionalProperties: false,
    },
  },
  {
    name: "compare_capital_to_omb",
    description: `Compare the Council capital list with OMB's adopted Capital Budget (NYC Open Data 46m8-77gv), by budget line, FY2019–FY2027: for each report year and Council-series budget line, the Council's total and OMB's adopted total for that year and the next, and a verdict (match, differ, council_only, omb_only). This is BetaNYC's arithmetic, not a Council or OMB reconciliation; 'match' is about the line's totals, not its projects. Filter by report_year, budget_line (exact) and verdict. Lines that disagree come first.`,
    inputSchema: {
      type: "object",
      properties: {
        report_year: { type: "number", description: "FY2019–FY2027" },
        budget_line: { type: "string", description: "Budget line, exact, as agency code then line ('P D018')" },
        verdict: { type: "string", enum: [...OMB_VERDICTS], description: "match (both years equal to the dollar), differ, council_only (no OMB line), omb_only (no Council row)" },
        limit: { type: "number", description: "Max lines shown, 1–500 (default 50). Counts always cover every match." },
      },
      additionalProperties: false,
    },
  },
  {
    name: "list_available_fiscal_years",
    description: `Report, for every fiscal year, which structured datasets this server holds and where each came from: the expense funding disclosure (loaded or not, Council RnD download or Internet Archive capture, retrieval date, early-snapshot flag), the Council capital list (Council workbook or NYC Open Data t474-a92g), and whether the year is in the Council-vs-OMB comparison. States the gaps plainly: FY2010 disclosure not loaded, FY2018 capital missing, nothing before FY2009.`,
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

/**
 * Tools removed in 2.0.0 and where their questions go now. Calling one returns this note as an
 * error rather than a bare "Unknown tool", so a client configured for 1.x learns why.
 */
export const REMOVED_TOOLS: Record<string, string> = {
  search_awards: "Use search_disclosure_awards (filters legal_name, program_name, council_member or council_member_id, fiscal_year, ein). The adopted-budget Schedule C it served was extracted from PDFs and is retired.",
  get_awards_by_ein: "Use search_disclosure_awards with ein (and fiscal_year if you need one year); its totals and per-year split cover every match.",
  search_transparency_resolutions: "Retired with no replacement yet: the transparency resolutions were extracted from PDFs. Post-adoption designations appear in search_disclosure_awards as rows of the disclosure, without the resolution number.",
  search_capital_projects: "Use search_council_capital (the Council's capital designations from its own workbooks and NYC Open Data t474-a92g). The §254 capital tables it served were extracted from PDFs and are retired.",
  get_terms_conditions: "Retired with no replacement yet: Terms & Conditions were extracted from PDFs.",
  get_legistar_link: "Retired: its crosswalk indexed the adopted-budget PDF documents (Schedule C, §254 capital, Terms & Conditions, transparency resolutions) that 2.0 no longer serves, and several rows were researchers' candidates rather than verified links. For a resolution's Legistar record, use the NYC Council MCP (@betanyc/nyc-council-mcp).",
};

const DISTRICT_WHY_DISCLOSURE =
  "no district filter exists: the disclosure names a council member (as of the workbook's export), not a district";

/**
 * Unknown-parameter guesses mapped to the real parameter they should have been (issue #37). Kept
 * PER TOOL by filtering targets against that tool's own schema, so a hint never points a caller
 * at a parameter the tool lacks.
 */
const ALIAS_HINTS: Record<string, { targets: string[]; why: string; whyByTool?: Record<string, string> }> = {
  council_district: {
    targets: ["council_member", "council_member_id"],
    why: DISTRICT_WHY_DISCLOSURE,
  },
  district: {
    targets: ["council_member", "council_member_id", "council_district"],
    why: DISTRICT_WHY_DISCLOSURE,
    whyByTool: { search_council_capital: "the district filter is named council_district" },
  },
  query: {
    targets: ["legal_name", "program_name", "title", "description"],
    why: "there is no free-text search parameter",
  },
  organization: {
    targets: ["legal_name", "title"],
    why: "the disclosure names the grantee field legal_name",
    whyByTool: { search_council_capital: "capital rows name no grantee field; in many FY2019 rows the title names the organization" },
  },
  program: { targets: ["program_name"], why: "the disclosure names the program field program_name" },
  status_norm: { targets: ["status"], why: "status takes the normalized value (cleared / pending / other)" },
  postal_code: { targets: ["zip"], why: "zip is the 5-digit ZIP derived from the published postal_code" },
  zip_code: { targets: ["zip"], why: "the ZIP filter is named zip" },
  council_member: { targets: ["sponsor", "sponsor_exact"], why: "capital rows name the sponsor as printed" },
  member: { targets: ["council_member", "council_member_id", "sponsor"], why: "the member filter has its own name on each tool" },
  boro: { targets: ["borough"], why: "the borough filter is named borough" },
  year: { targets: ["fiscal_year", "report_year"], why: "the year filter has its own name on each tool" },
  fy: { targets: ["fiscal_year", "report_year"], why: "the year filter has its own name on each tool" },
  report_year: { targets: ["fiscal_year"], why: "fiscal_year is the capital list's report year" },
  agency: { targets: ["budget_line"], why: "capital rows carry no agency column; the budget line starts with the agency code" },
  project_title: { targets: ["title"], why: "the title filter is named title" },
};

/**
 * Parse tool arguments against a `.strict()` schema, converting zod's unrecognized-key error into
 * a message that names the accepted parameters for THIS tool. Silently dropping an unknown filter
 * returns real data answering a different question — a hard error is far safer.
 */
function parseArgs<S extends z.ZodObject<z.ZodRawShape, "strict">>(tool: string, schema: S, args: unknown): z.infer<S> {
  const parsed = schema.safeParse(args ?? {});
  if (parsed.success) return parsed.data as z.infer<S>;
  const accepted = Object.keys(schema.shape);
  const unknown = parsed.error.issues.flatMap((i) => (i.code === "unrecognized_keys" ? i.keys : []));
  if (unknown.length === 0) throw parsed.error;
  const hints = unknown.flatMap((key) => {
    const hint = ALIAS_HINTS[key];
    const targets = hint?.targets.filter((t) => accepted.includes(t)) ?? [];
    return targets.length
      ? [`Use \`${targets.join("` or `")}\` instead of \`${key}\` — ${hint.whyByTool?.[tool] ?? hint.why}.`]
      : [];
  });
  throw new Error(
    [
      `${tool} does not accept ${unknown.map((k) => `\`${k}\``).join(", ")}.`,
      accepted.length ? `Accepted parameters: ${accepted.join(", ")}.` : `${tool} takes no parameters.`,
      ...hints,
    ].join(" ")
  );
}

/** Guards shared by the searches; each returns an error message or null. */
function limitError(limit?: number): string | null {
  return limit != null && limit < 1
    ? `limit must be at least 1 (got ${limit}); totals always cover every match, so a small limit is enough to see them.`
    : null;
}
function rangeError(min?: number, max?: number): string | null {
  return min != null && max != null && min > max
    ? `min_amount (${min}) is greater than max_amount (${max}); nothing can match.`
    : null;
}
function emptyError(name: string, v?: string): string | null {
  return v != null && v.trim() === "" ? `${name} is empty; omit it, or give a value.` : null;
}

function budgetLineArg(v: string | undefined): { value?: string; error?: string } {
  if (v == null) return {};
  const norm = normBudgetLine(v);
  return norm
    ? { value: norm }
    : {
        error: `budget_line must be an agency code of one or two letters, then a space or '-', then the line (e.g. 'P D018', 'PW-DN846'); got ${JSON.stringify(v)}. A value without the separator is refused, because where the agency code ends cannot be told.`,
      };
}

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    switch (name) {
      case "search_disclosure_awards": {
        const a = parseArgs("search_disclosure_awards", z.object({
            fiscal_year: z.number().int().optional(),
            ein: z.string().optional(),
            legal_name: z.string().optional(),
            council_member: z.string().optional(),
            council_member_id: z.union([z.string(), z.number().int()]).optional(),
            source: z.string().optional(),
            source_exact: z.string().optional(),
            agency: z.string().optional(),
            program_name: z.string().optional(),
            zip: z.string().optional(),
            zip_status: z.enum(ZIP_STATUSES).optional(),
            city: z.string().optional(),
            status: z.enum(DISCLOSURE_STATUSES).optional(),
            mocs_id: z.string().optional(),
            od_mocs_id: z.string().optional(),
            min_amount: z.number().optional(),
            max_amount: z.number().optional(),
            limit: z.number().int().optional(),
          }).strict(), args);
        // #70: a ZIP is 5 digits. A ZIP+4 or a 4-digit value is refused, never trimmed or padded.
        if (a.zip != null && !/^\d{5}$/.test(a.zip.trim()))
          return errorResult(
            `zip must be exactly 5 digits; got ${JSON.stringify(a.zip)}.` +
              (/^\d{5}\D/.test(a.zip.trim()) ? ` For a ZIP+4, give its first five digits ("${a.zip.trim().slice(0, 5)}").` : "")
          );
        // An EIN is 9 digits; "N/A" or an 8-digit value is refused, never guessed at.
        if (a.ein != null) {
          const digits = normEin(a.ein);
          if (digits.length !== 9)
            return errorResult(
              `ein must be 9 digits (hyphens optional); got ${JSON.stringify(a.ein)}, which has ${digits.length}.` +
                (digits.length === 8 ? ` If a spreadsheet dropped a leading zero, try "0${digits}".` : "")
            );
        }
        if (a.council_member_id != null && !/^\d+$/.test(String(a.council_member_id).trim()))
          return errorResult(
            `council_member_id must be a Legistar person ID (digits only); got ${JSON.stringify(a.council_member_id)}. To search by name, use council_member.`
          );
        const guard =
          emptyError("city", a.city) ?? emptyError("source_exact", a.source_exact) ?? emptyError("mocs_id", a.mocs_id) ??
          emptyError("od_mocs_id", a.od_mocs_id) ?? limitError(a.limit) ?? rangeError(a.min_amount, a.max_amount);
        if (guard) return errorResult(guard);

        const years = listDisclosureYears();
        const coverage = disclosureCoverage(years);
        const asked = a.fiscal_year != null ? years.find((y) => y.fiscal_year === a.fiscal_year) : undefined;
        if (asked && !asked.loaded)
          return textResult(
            `FY${asked.fiscal_year} is not in the disclosure dataset: ${noteText(asked.note)}\n\n` +
              `The workbook is kept in the source repo (${asked.source_path}, Internet Archive capture ${asked.wayback_timestamp}, sha256 ${asked.sha256.slice(0, 12)}) but its rows are not served.\n\n${coverage}\n\n${DISCLOSURE_FOOTER}`
          );
        const res = searchDisclosure({
          ...a,
          council_member_id: a.council_member_id == null ? undefined : String(a.council_member_id).trim(),
        });
        if (res.matched === 0) {
          const loaded = years.filter((y) => y.loaded).map((y) => y.fiscal_year);
          const snap = res.snapshots
            .filter((s) => s.loaded)
            .map((s) => ` FY${s.fiscal_year} is from ${s.file}, sheet "${s.sheet}", retrieved ${s.retrieved}.`)
            .join("");
          return textResult(
            `No matching designations in the Council's expense funding disclosure (covers ${yearSpan(loaded)}).${snap}\n\n${coverage}\n\n${DISCLOSURE_CAVEAT}\n\n${DISCLOSURE_FOOTER}`
          );
        }
        return textResult(`${disclosureText(res, coverage)}\n\n${DISCLOSURE_FOOTER}`);
      }

      case "search_council_capital": {
        const a = parseArgs("search_council_capital", z.object({
            fiscal_year: z.number().int().optional(),
            amount_fy: z.number().int().optional(),
            budget_line: z.string().optional(),
            project_id: z.string().optional(),
            sponsor: z.string().optional(),
            sponsor_exact: z.string().optional(),
            borough: z.string().optional(),
            council_district: z.number().int().optional(),
            title: z.string().optional(),
            description: z.string().optional(),
            min_amount: z.number().optional(),
            max_amount: z.number().optional(),
            limit: z.number().int().optional(),
          }).strict(), args);
        const line = budgetLineArg(a.budget_line);
        if (line.error) return errorResult(line.error);
        if (a.council_district != null && (a.council_district < 0 || a.council_district > 99))
          return errorResult(`council_district must be 0–99 (a district, 0 Speaker, 88–99 caucus/delegation codes); got ${a.council_district}.`);
        if (a.borough != null && !/^[A-Za-z]$/.test(a.borough.trim()))
          return errorResult(`borough must be one printed code letter (K, M, Q, R, X, C, or the unconfirmed A, k, x); got ${JSON.stringify(a.borough)}.`);
        const guard =
          emptyError("project_id", a.project_id) ?? emptyError("sponsor_exact", a.sponsor_exact) ??
          limitError(a.limit) ?? rangeError(a.min_amount, a.max_amount);
        if (guard) return errorResult(guard);

        const sources = listCapitalSources();
        const years = sources.map((s) => s.report_year);
        if (a.fiscal_year != null && !years.includes(a.fiscal_year)) {
          const why =
            a.fiscal_year === 2018
              ? "FY2018 is in no source found: no Council capital workbook for it was located, and NYC Open Data t474-a92g starts at FY2019."
              : `FY${a.fiscal_year} is outside the dataset.`;
          return textResult(`${why} The Council capital list covers ${yearSpan(years)}.\n\n${CAPITAL_CAVEAT}\n\n${CAPITAL_FOOTER}`);
        }
        const res = searchCapital({
          ...a,
          budget_line: line.value,
          project_id: a.project_id == null ? undefined : normProjectId(a.project_id),
          borough: a.borough?.trim(),
        });
        if (res.matched === 0) {
          const src = res.sources.map((s) => `\n${capitalSourceLine(s)}`).join("");
          return textResult(
            `No matching rows in the Council's capital designations (covers ${yearSpan(years)}; FY2018 missing).` +
              (src ? `\nSearched:${src}` : "") +
              (a.council_district != null
                ? `\nNote: council_district never matches FY2019–FY2025 (t474) rows; their district lists were collapsed by Open Data.`
                : "") +
              `\n\n${CAPITAL_CAVEAT}\n\n${CAPITAL_FOOTER}`
          );
        }
        return textResult(`${capitalText(res, a.council_district != null)}\n\n${CAPITAL_FOOTER}`);
      }

      case "compare_capital_to_omb": {
        const a = parseArgs("compare_capital_to_omb", z.object({
            report_year: z.number().int().optional(),
            budget_line: z.string().optional(),
            verdict: z.enum(OMB_VERDICTS).optional(),
            limit: z.number().int().optional(),
          }).strict(), args);
        const line = budgetLineArg(a.budget_line);
        if (line.error) return errorResult(line.error);
        const guard = limitError(a.limit);
        if (guard) return errorResult(guard);
        const years = listOmbComparisonYears();
        if (a.report_year != null && !years.includes(a.report_year))
          return textResult(
            `FY${a.report_year} is not in the comparison, which covers ${yearSpan(years)}.\n\n${OMB_CAVEAT}\n\n${OMB_FOOTER}`
          );
        const res = compareCapitalToOmb({ ...a, budget_line: line.value });
        if (res.matched === 0)
          return textResult(`No budget lines matched (the comparison covers ${yearSpan(years)}).\n\n${OMB_CAVEAT}\n\n${OMB_FOOTER}`);
        return textResult(`${ombText(res)}\n\n${OMB_FOOTER}`);
      }

      case "list_available_fiscal_years": {
        parseArgs("list_available_fiscal_years", z.object({}).strict(), args);
        const disc = new Map(listDisclosureYears().map((y) => [y.fiscal_year, y]));
        const cap = new Map(listCapitalSources().map((s) => [s.report_year, s]));
        const omb = new Set(listOmbComparisonYears());
        const all = [...new Set([...disc.keys(), ...cap.keys()])].sort((x, y) => x - y);
        const lines = all.map((fy) => {
          const d = disc.get(fy);
          const c = cap.get(fy);
          const dTxt = !d
            ? "disclosure: none"
            : !d.loaded
              ? "disclosure: NOT LOADED (see below)"
              : `disclosure: ${n(d.award_rows)} rows, ${d.source_kind === "internet_archive" ? `Internet Archive capture ${d.wayback_timestamp}` : "Council RnD"}, retrieved ${d.retrieved}${d.early_snapshot ? ", EARLY SNAPSHOT" : ""}`;
          const cTxt = c
            ? `capital: ${n(c.rows)} rows, ${c.source_kind === "open_data_t474" ? "NYC Open Data t474-a92g" : "Council workbook"}, retrieved ${c.retrieved}`
            : fy === 2018
              ? "capital: MISSING (no source found)"
              : "capital: none";
          return `  FY${fy} · ${dTxt} · ${cTxt}${omb.has(fy) ? " · in the OMB comparison" : ""}`;
        });
        const excluded = [...disc.values()].filter((y) => !y.loaded);
        const early = [...disc.values()].filter((y) => y.loaded && y.early_snapshot);
        const text = [
          `NYC Budget MCP v${PACKAGE_VERSION} — what each fiscal year holds (structured sources only):`,
          "",
          ...lines,
          "",
          "Gaps and flags:",
          ...excluded.map((y) => `• FY${y.fiscal_year} disclosure is not loaded: ${noteText(y.note)}`),
          ...early.map((y) => `• FY${y.fiscal_year} disclosure is an early snapshot: ${noteText(y.note)}`),
          "• FY2018 capital: no Council workbook was found and NYC Open Data t474-a92g starts at FY2019.",
          "• Nothing before FY2009 (disclosure) or FY2015 (capital). The OMB comparison covers " + yearSpan([...omb].sort((x, y) => x - y)) + ".",
          "• Retired in 2.0.0 and not served: everything extracted from the adopted-budget PDFs — Schedule C and its appendices, Terms & Conditions, §254 capital, transparency resolutions, and the Legistar crosswalk of those documents. They remain in the source repo for history.",
          "",
          `Source repo: ${REPO_URL}. Served by @betanyc/nyc-budget-mcp v${PACKAGE_VERSION}.`,
        ].join("\n");
        return textResult(text);
      }

      default: {
        const moved = REMOVED_TOOLS[name];
        if (moved) return errorResult(`${name} was removed in @betanyc/nyc-budget-mcp 2.0.0. ${moved}`);
        return errorResult(`Unknown tool: ${name}`);
      }
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return errorResult(message);
  }
});

export async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}
