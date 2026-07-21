/**
 * MCP server: tool definitions + call routing for the NYC budget data.
 * Structurally modeled on @betanyc/nyc-charter-laws-rules (local/offline corpus,
 * no live upstream API) — Server + StdioServerTransport + zod-validated args.
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { readFileSync } from "fs";
import { z } from "zod";
import {
  searchAwards,
  getAwardsByEin,
  searchTransparency,
  searchCapital,
  getTerms,
  getLegistarLink,
  listFiscalYears,
  buildMeetingUrl,
  type AwardRow,
} from "./db.js";

const PACKAGE_VERSION = (
  JSON.parse(
    readFileSync(new URL("../package.json", import.meta.url), "utf-8")
  ) as { version: string }
).version;

const SCOPE_NOTE =
  "Coverage: Schedule C awards FY2015–FY2027; Terms & Conditions FY2015–FY2018 + FY2021–FY2027; §254 capital FY2020 + FY2022–FY2027; Transparency Resolutions FY2010–FY2024 + FY2026 (org/program TEXT is low-confidence for FY2010–FY2013 — financial columns reliable; join on EIN). FY2009–FY2014 Schedule C is initiatives-only (no EIN) and is EXCLUDED from the award tools. FY2008 and the FY2009 transparency resolutions are unparsed (source blocked). The Legistar crosswalk covers FY2008–FY2027. Run list_available_fiscal_years for exact per-dataset coverage.";

const FOOTER = `
---
NYC budget data structured by BetaNYC (https://beta.nyc) from the NYC Council's adopted-budget documents (Schedule C, Terms & Conditions, §254 capital, Transparency Resolutions). Dollar figures were extracted deterministically and reconciled against printed totals in the source repo. Served by @betanyc/nyc-budget-mcp v${PACKAGE_VERSION} (https://github.com/BetaNYC/New-York-City-Budget). ${SCOPE_NOTE}`.trim();

function withFooter(text: string): string {
  return `${text}\n\n${FOOTER}`;
}

const money = (n: number | null): string =>
  n == null
    ? "—"
    : n < 0
      ? `-$${Math.abs(n).toLocaleString("en-US")}`
      : `$${n.toLocaleString("en-US")}`;

function summarizeAwardsByYear(rows: AwardRow[]): string {
  const byYear = new Map<number, { count: number; total: number }>();
  for (const r of rows) {
    const e = byYear.get(r.fiscal_year) ?? { count: 0, total: 0 };
    e.count += 1;
    e.total += r.amount ?? 0;
    byYear.set(r.fiscal_year, e);
  }
  return [...byYear.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([y, e]) => `  FY${y}: ${e.count} award(s), ${money(e.total)}`)
    .join("\n");
}

export const server = new Server(
  { name: "nyc-budget-mcp", version: PACKAGE_VERSION },
  { capabilities: { tools: {} } }
);

export const TOOLS = [
  {
    name: "search_awards",
    description: `Search NYC Council discretionary (Schedule C) awards across FY2015–FY2027 (the EIN-level years). Filter by any combination of EIN, organization name, program name, council member (surname), fiscal year, category, and initiative. NOTE: a single EIN can be a fiscal sponsor covering many programs — e.g. EIN 13-2612524 ("Fund for the City of New York, Inc.") is a passthrough for dozens of programs, so to isolate one grantee (e.g. BetaNYC) filter by \`program\` as well as \`ein\`. FY2009–FY2014 have no award/EIN data (initiatives-only) and are not searchable here. ${SCOPE_NOTE}`,
    inputSchema: {
      type: "object",
      properties: {
        ein: { type: "string", description: "Tax ID; hyphens optional (13-2612524 or 132612524)" },
        organization: { type: "string", description: "Organization name (substring, case-insensitive)" },
        program: { type: "string", description: "Program name (substring) — the field that distinguishes grantees under a shared fiscal-sponsor EIN" },
        council_member: { type: "string", description: "Sponsoring council member surname (substring)" },
        fiscal_year: { type: "number", description: "Any year FY2015–FY2027" },
        category: { type: "string", description: "Schedule C category (substring)" },
        initiative: { type: "string", description: "Council initiative name (substring)" },
        limit: { type: "number", description: "Max rows (default 50, max 500)" },
      },
      additionalProperties: false,
    },
  },
  {
    name: "get_awards_by_ein",
    description: `Return every Schedule C award tied to an EIN across FY2015–FY2027, with a per-fiscal-year count and total. This is the primary cross-system join key. Reminder: for a fiscal-sponsor EIN the result mixes many programs — narrow with search_awards(ein, program) to isolate one grantee. ${SCOPE_NOTE}`,
    inputSchema: {
      type: "object",
      properties: {
        ein: { type: "string", description: "Tax ID; hyphens optional" },
        fiscal_year: { type: "number", description: "Optional: restrict to a year FY2015–FY2027" },
      },
      required: ["ein"],
      additionalProperties: false,
    },
  },
  {
    name: "search_transparency_resolutions",
    description: `Search the NYC Council Transparency Resolutions FY2010–FY2024 + FY2026 — post-adoption discretionary designations, rescissions, and purpose changes. Rescissions carry negative amounts; a transfer is a rescind + designate pair on the same EIN/agency. Filter by EIN, council member, fiscal year, action (designate / rescind / purpose_change), or organization. IMPORTANT: \`fiscal_year\` filters the resolution *document's* fiscal year (the year whose budget it amends); each result also shows the row-level designation year, which can differ or be blank. CAVEAT: for FY2010–FY2013 the organization/council-member/program TEXT is low-confidence (glued/garbled PDF text layer) — the financial columns (EIN, amount, agency, date, action) are reliable, so join on EIN, not name; affected rows are flagged in the output. ${SCOPE_NOTE}`,
    inputSchema: {
      type: "object",
      properties: {
        ein: { type: "string", description: "Tax ID; hyphens optional" },
        council_member: { type: "string", description: "Council member surname (substring); unreliable for FY2010–FY2013" },
        fiscal_year: { type: "number", description: "Resolution document fiscal year, FY2010–FY2024 or 2026" },
        action: { type: "string", enum: ["designate", "rescind", "purpose_change"], description: "Type of action" },
        organization: { type: "string", description: "Organization name (substring); unreliable for FY2010–FY2013" },
        limit: { type: "number", description: "Max rows (default 50, max 500)" },
      },
      additionalProperties: false,
    },
  },
  {
    name: "get_legistar_link",
    description: `Look up the NYC Council Legistar legislative record (matter number, adoption date, adopting-session link) for a budget source document via the FY2008–FY2027 crosswalk. Filter by fiscal_year and/or document_type (schedule_c, terms_conditions, capital_a, capital_b, transparency_reso, transparency_reso_NN) or by local_file. For confirmed rows, returns a WORKING link to the City Council meeting where the matter was adopted (Legistar MeetingDetail); the older bill-detail URL is not surfaced because NYC's two Legistar backends use different ids and it resolves to "Invalid parameters!". Always surfaces the crosswalk \`status\`: 'confirmed' (matter verified), 'candidate' (anchor/exhibit not upgraded to confirmed), or 'not_located' (no matter found). Do not treat a candidate/not_located row as an authoritative citation.`,
    inputSchema: {
      type: "object",
      properties: {
        fiscal_year: { type: "number", description: "Any year FY2008–FY2027" },
        document_type: { type: "string", description: "schedule_c, terms_conditions, capital_a, capital_b, transparency_reso, or transparency_reso_NN (substring)" },
        local_file: { type: "string", description: "Repo-relative source PDF path (substring)" },
      },
      additionalProperties: false,
    },
  },
  {
    name: "search_capital_projects",
    description: `Search §254 capital changes across FY2020 + FY2022–FY2027 (no FY2021 detail book exists). Filter by agency, fiscal year, sponsor (council member surname; co-sponsored rows list multiple), or project title. \`fy1\` is the adoption-year allocation. All parsed years — FY2020, FY2022, FY2023, FY2024, FY2025, FY2026 — come from the "Supporting Detail Book" (Council-additions Capital Project Detail), share the full schema (borough, sub-id, sponsor), and reconcile against the printed agency subtotals and both \`TOTALS FOR ALL\` grand totals (FY2027 partially). FY2025 was reparsed from the FY2025 Supporting Detail Book (PR #21) and is now directly comparable to the other years. ${SCOPE_NOTE}`,
    inputSchema: {
      type: "object",
      properties: {
        agency: { type: "string", description: "Agency name (substring)" },
        fiscal_year: { type: "number", description: "FY2020, or any of FY2022–FY2027" },
        sponsor: { type: "string", description: "Sponsoring council member surname (substring)" },
        title: { type: "string", description: "Project title (substring)" },
        limit: { type: "number", description: "Max rows (default 50, max 500)" },
      },
      additionalProperties: false,
    },
  },
  {
    name: "get_terms_conditions",
    description: `Retrieve Terms & Conditions (reporting mandates attached to appropriations) across FY2015–FY2018 + FY2021–FY2027 (no standalone T&C document exists for FY2019/FY2020). Filter by fiscal year and/or agency name. ${SCOPE_NOTE}`,
    inputSchema: {
      type: "object",
      properties: {
        fiscal_year: { type: "number", description: "FY2015–FY2018 or FY2021–FY2027" },
        agency: { type: "string", description: "Agency name (substring)" },
        limit: { type: "number", description: "Max rows (default 50, max 500)" },
      },
      additionalProperties: false,
    },
  },
  {
    name: "list_available_fiscal_years",
    description: `Report exactly which fiscal years each dataset actually covers, so callers are never misled about what exists. Returns the parsed years for awards/terms/capital/transparency and the full crosswalk range, plus the honesty caveats (FY2009–FY2014 initiatives-only/no-EIN and excluded from award tools; FY2010–FY2013 transparency text low-confidence).`,
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

/**
 * Unknown-parameter guesses we have actually seen, mapped to the real parameter
 * they should have been (issue #37). Kept PER-TOOL by filtering targets against
 * that tool's own schema: `council_member` is real on search_awards but not on
 * search_capital_projects, and `sponsor` is the reverse — a global alias table
 * would point callers at parameters the tool does not have.
 */
const ALIAS_HINTS: Record<string, { targets: string[]; why: string }> = {
  council_district: {
    targets: ["council_member", "sponsor"],
    why: "no district filter exists, because Schedule C awards and §254 capital both key on the sponsoring member's surname",
  },
  district: {
    targets: ["council_member", "sponsor"],
    why: "no district filter exists, because Schedule C awards and §254 capital both key on the sponsoring member's surname",
  },
  query: { targets: ["organization", "program"], why: "there is no free-text search parameter" },
};

/**
 * Parse tool arguments against a `.strict()` schema, converting zod's
 * unrecognized-key error into a message that names the accepted parameters for
 * THIS tool. Silently dropping an unknown filter returns real, correctly
 * sourced data answering a different question — a hard error is far safer.
 */
function parseArgs<S extends z.ZodObject<z.ZodRawShape, "strict">>(
  tool: string,
  schema: S,
  args: unknown
): z.infer<S> {
  const parsed = schema.safeParse(args ?? {});
  if (parsed.success) return parsed.data as z.infer<S>;
  const accepted = Object.keys(schema.shape);
  const unknown = parsed.error.issues.flatMap((i) =>
    i.code === "unrecognized_keys" ? i.keys : []
  );
  if (unknown.length === 0) throw parsed.error;
  const hints = unknown.flatMap((key) => {
    const hint = ALIAS_HINTS[key];
    const targets = hint?.targets.filter((t) => accepted.includes(t)) ?? [];
    return targets.length
      ? [`Use \`${targets.join("` or `")}\` instead of \`${key}\` — ${hint.why}.`]
      : [];
  });
  throw new Error(
    [
      `${tool} does not accept ${unknown.map((k) => `\`${k}\``).join(", ")}.`,
      accepted.length
        ? `Accepted parameters: ${accepted.join(", ")}.`
        : `${tool} takes no parameters.`,
      ...hints,
    ].join(" ")
  );
}

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    switch (name) {
      case "search_awards": {
        const a = parseArgs("search_awards", z.object({
            ein: z.string().optional(),
            organization: z.string().optional(),
            program: z.string().optional(),
            council_member: z.string().optional(),
            fiscal_year: z.number().int().optional(),
            category: z.string().optional(),
            initiative: z.string().optional(),
            limit: z.number().int().optional(),
          }).strict(), args);
        const rows = searchAwards(a);
        if (rows.length === 0)
          return { content: [{ type: "text", text: withFooter("No matching Schedule C awards.") }] };
        const total = rows.reduce((s, r) => s + (r.amount ?? 0), 0);
        const body = rows
          .map(
            (r) =>
              `FY${r.fiscal_year} · ${money(r.amount)} · ${r.member || "(collective)"} → ${r.organization}` +
              (r.program ? ` [${r.program}]` : "") +
              (r.initiative ? `\n    initiative: ${r.initiative}` : "") +
              (r.agency ? ` · agency: ${r.agency}` : "")
          )
          .join("\n");
        return {
          content: [
            {
              type: "text",
              text: withFooter(
                `${rows.length} award(s), total ${money(total)}:\n\n${body}\n\nBy fiscal year:\n${summarizeAwardsByYear(rows)}`
              ),
            },
          ],
        };
      }

      case "get_awards_by_ein": {
        const a = parseArgs("get_awards_by_ein", z.object({ ein: z.string(), fiscal_year: z.number().int().optional() }).strict(), args);
        const rows = getAwardsByEin(a.ein, a.fiscal_year);
        if (rows.length === 0)
          return { content: [{ type: "text", text: withFooter(`No Schedule C awards for EIN ${a.ein}.`) }] };
        const orgs = [...new Set(rows.map((r) => r.organization).filter(Boolean))];
        const total = rows.reduce((s, r) => s + (r.amount ?? 0), 0);
        const body = rows
          .map(
            (r) =>
              `FY${r.fiscal_year} · ${money(r.amount)} · ${r.member || "(collective)"}` +
              (r.program ? ` · ${r.program}` : "") +
              (r.initiative ? ` · ${r.initiative}` : "")
          )
          .join("\n");
        return {
          content: [
            {
              type: "text",
              text: withFooter(
                `EIN ${a.ein}: ${rows.length} award(s) across FY2015–FY2027, total ${money(total)}.\n` +
                  `Organization name(s) on file: ${orgs.join("; ") || "(none)"}\n\n` +
                  `Per fiscal year:\n${summarizeAwardsByYear(rows)}\n\nRows:\n${body}`
              ),
            },
          ],
        };
      }

      case "search_transparency_resolutions": {
        const a = parseArgs("search_transparency_resolutions", z.object({
            ein: z.string().optional(),
            council_member: z.string().optional(),
            fiscal_year: z.number().int().optional(),
            action: z.enum(["designate", "rescind", "purpose_change"]).optional(),
            organization: z.string().optional(),
            limit: z.number().int().optional(),
          }).strict(), args);
        const rows = searchTransparency(a);
        if (rows.length === 0)
          return { content: [{ type: "text", text: withFooter("No matching transparency-resolution rows.") }] };
        const body = rows
          .map(
            (r) =>
              `FY${r.source_fy} Reso ${r.resolution} (${r.date}) · ${r.action} · ${money(r.amount)} · ${r.council_member || "(none)"} → ${r.organization}` +
              (r.agency ? ` · ${r.agency}` : "") +
              (r.low_text_confidence ? ` · ⚠ LOW-confidence text (join on EIN ${r.ein || "?"})` : "") +
              `\n    chart: ${r.chart}` +
              (r.purpose ? `\n    purpose: ${r.purpose}` : "")
          )
          .join("\n");
        const lowConf = rows.some((r) => r.low_text_confidence);
        const caveat = lowConf
          ? "\n\n⚠ Some rows are FY2010–FY2013, where the organization/member/program TEXT is low-confidence (garbled PDF text layer). The financial columns (EIN, amount, agency, date, action) are reliable — join on EIN, not name."
          : "";
        return { content: [{ type: "text", text: withFooter(`${rows.length} row(s):\n\n${body}${caveat}`) }] };
      }

      case "get_legistar_link": {
        const a = parseArgs("get_legistar_link", z.object({
            fiscal_year: z.number().int().optional(),
            document_type: z.string().optional(),
            local_file: z.string().optional(),
          }).strict(), args);
        if (a.fiscal_year == null && !a.document_type && !a.local_file)
          return {
            content: [{ type: "text", text: withFooter("Provide at least one of: fiscal_year, document_type, local_file.") }],
            isError: true,
          };
        const rows = getLegistarLink(a);
        if (rows.length === 0)
          return { content: [{ type: "text", text: withFooter("No crosswalk rows matched.") }] };
        const body = rows
          .map((r) => {
            // The adopting City Council session carries a WORKING Legistar link
            // (MeetingDetail.aspx accepts the OData EventId). The row's stored
            // legistar_url is a LegislationDetail.aspx link keyed on OData ids the
            // public site does not recognize ("Invalid parameters!"), so it is NOT
            // surfaced as an authoritative citation — see issue #31.
            const meetingUrl = buildMeetingUrl(r.adopting_event_id);
            return (
              `FY${r.fiscal_year} · ${r.document_type} · [${r.status}] ${r.legistar_matter_number || "(no matter)"}` +
              (r.adoption_date ? ` · adopted ${r.adoption_date}` : "") +
              (meetingUrl
                ? `\n    adopting session: ${r.adopting_body}` +
                  (r.adopting_action ? ` — ${r.adopting_action}` : "") +
                  (r.adopting_datetime ? ` — ${r.adopting_datetime}` : "") +
                  `\n    ${meetingUrl}`
                : `\n    (no verified Legistar link — matter number + adoption date are the citation)`) +
              (r.notes ? `\n    notes: ${r.notes}` : "")
            );
          })
          .join("\n\n");
        return { content: [{ type: "text", text: withFooter(`${rows.length} crosswalk row(s):\n\n${body}`) }] };
      }

      case "search_capital_projects": {
        const a = parseArgs("search_capital_projects", z.object({
            agency: z.string().optional(),
            fiscal_year: z.number().int().optional(),
            sponsor: z.string().optional(),
            title: z.string().optional(),
            limit: z.number().int().optional(),
          }).strict(), args);
        const rows = searchCapital(a);
        if (rows.length === 0)
          return { content: [{ type: "text", text: withFooter("No matching capital projects.") }] };
        const total = rows.reduce((s, r) => s + (r.fy1 ?? 0), 0);
        const body = rows
          .map(
            (r) =>
              `FY${r.fiscal_year} · ${money(r.fy1)} · ${r.title} · ${r.agency}` +
              (r.sponsor ? ` · sponsor: ${r.sponsor}` : "") +
              (r.boro ? ` · boro: ${r.boro}` : "") +
              (r.action ? ` · ${r.action}` : "")
          )
          .join("\n");
        return {
          content: [
            {
              type: "text",
              text: withFooter(`${rows.length} project(s), FY1 total ${money(total)}:\n\n${body}`),
            },
          ],
        };
      }

      case "get_terms_conditions": {
        const a = parseArgs("get_terms_conditions", z.object({
            fiscal_year: z.number().int().optional(),
            agency: z.string().optional(),
            limit: z.number().int().optional(),
          }).strict(), args);
        const rows = getTerms(a);
        if (rows.length === 0)
          return { content: [{ type: "text", text: withFooter("No matching terms & conditions.") }] };
        const body = rows
          .map(
            (r) =>
              `FY${r.fiscal_year} · #${r.item_number} · ${r.agency_name} (${r.agency_code})` +
              (r.coverage_period ? ` · ${r.coverage_period}` : "") +
              (r.report_deadlines ? ` · deadlines: ${r.report_deadlines}` : "") +
              (r.condition_text ? `\n    ${r.condition_text.slice(0, 300)}${r.condition_text.length > 300 ? "…" : ""}` : "")
          )
          .join("\n");
        return { content: [{ type: "text", text: withFooter(`${rows.length} term(s):\n\n${body}`) }] };
      }

      case "list_available_fiscal_years": {
        parseArgs("list_available_fiscal_years", z.object({}).strict(), args);
        const r = listFiscalYears();
        const fmt = (ys: number[]) => (ys.length ? ys.map((y) => `FY${y}`).join(", ") : "(none)");
        const text =
          `NYC Budget MCP — dataset coverage (exact per-dataset parsed years):\n\n` +
          `Schedule C awards:        ${fmt(r.awards)} (EIN-level)\n` +
          `Terms & Conditions:       ${fmt(r.terms)}\n` +
          `Capital (§254):           ${fmt(r.capital)} (all from the "Supporting Detail Book"; full schema; reconcile against printed subtotals — FY2027 partially)\n` +
          `Transparency Resolutions: ${fmt(r.transparency)} (by resolution document year; FY2010–FY2013 org/program text is LOW-confidence — join on EIN)\n` +
          `Legistar crosswalk:       FY${r.crosswalk.min}–FY${r.crosswalk.max} (provenance index; covers years not parsed to CSV)\n\n` +
          `HONESTY GUARD:\n` +
          `• Award tools (search_awards / get_awards_by_ein) serve FY2015–FY2027 only.\n` +
          `• FY2009–FY2014 Schedule C is INITIATIVES-ONLY (no per-organization rows, no EINs) and is deliberately NOT in the award tools. Its category/initiative totals live in the source repo, not here.\n` +
          `• FY2008 Schedule C and the FY2009 Transparency Resolutions are unparsed (blocked source documents).\n` +
          `• The crosswalk still links every FY2008–FY2027 document to Legistar even where no CSV is parsed.`;
        return { content: [{ type: "text", text: withFooter(text) }] };
      }

      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { content: [{ type: "text", text: `Error: ${message}` }], isError: true };
  }
});

export async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}
