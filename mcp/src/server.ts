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
  type AwardRow,
} from "./db.js";

const PACKAGE_VERSION = (
  JSON.parse(
    readFileSync(new URL("../package.json", import.meta.url), "utf-8")
  ) as { version: string }
).version;

const SCOPE_NOTE =
  "Structured award/terms/capital data covers FY2025–FY2027 only (FY2008–FY2024 are not yet parsed to CSV). The Legistar crosswalk covers FY2008–FY2027. Transparency Resolutions are FY2026 (that file also carries embedded FY2023–FY2025 rows).";

const FOOTER = `
---
NYC budget data structured by BetaNYC (https://beta.nyc) from the NYC Council's adopted-budget documents (Schedule C, Terms & Conditions, §254 capital, Transparency Resolutions). Dollar figures were extracted deterministically and reconciled against printed totals in the source repo. PROTOTYPE — local snapshot, not a published package. ${SCOPE_NOTE}`.trim();

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

const TOOLS = [
  {
    name: "search_awards",
    description: `Search NYC Council discretionary (Schedule C) awards across FY2025–FY2027. Filter by any combination of EIN, organization name, program name, council member (surname), fiscal year, category, and initiative. NOTE: a single EIN can be a fiscal sponsor covering many programs — e.g. EIN 13-2612524 ("Delegation Fund for the City of New York, Inc.") is a passthrough for dozens of programs, so to isolate one grantee (e.g. BetaNYC) filter by \`program\` as well as \`ein\`. ${SCOPE_NOTE}`,
    inputSchema: {
      type: "object",
      properties: {
        ein: { type: "string", description: "Tax ID; hyphens optional (13-2612524 or 132612524)" },
        organization: { type: "string", description: "Organization name (substring, case-insensitive)" },
        program: { type: "string", description: "Program name (substring) — the field that distinguishes grantees under a shared fiscal-sponsor EIN" },
        council_member: { type: "string", description: "Sponsoring council member surname (substring)" },
        fiscal_year: { type: "number", description: "2025, 2026, or 2027" },
        category: { type: "string", description: "Schedule C category (substring)" },
        initiative: { type: "string", description: "Council initiative name (substring)" },
        limit: { type: "number", description: "Max rows (default 50, max 500)" },
      },
    },
  },
  {
    name: "get_awards_by_ein",
    description: `Return every Schedule C award tied to an EIN across FY2025–FY2027, with a per-fiscal-year count and total. This is the primary cross-system join key. Reminder: for a fiscal-sponsor EIN the result mixes many programs — narrow with search_awards(ein, program) to isolate one grantee. ${SCOPE_NOTE}`,
    inputSchema: {
      type: "object",
      properties: {
        ein: { type: "string", description: "Tax ID; hyphens optional" },
        fiscal_year: { type: "number", description: "Optional: restrict to 2025, 2026, or 2027" },
      },
      required: ["ein"],
    },
  },
  {
    name: "search_transparency_resolutions",
    description: `Search the FY2026 NYC Council Transparency Resolutions — post-adoption discretionary designations, rescissions, and purpose changes. Rescissions carry negative amounts; a transfer is a rescind + designate pair on the same EIN/agency. Filter by EIN, council member, fiscal year, action (designate / rescind / purpose_change), or organization. This file also contains embedded FY2023–FY2025 rows, so pass fiscal_year to scope. ${SCOPE_NOTE}`,
    inputSchema: {
      type: "object",
      properties: {
        ein: { type: "string", description: "Tax ID; hyphens optional" },
        council_member: { type: "string", description: "Council member surname (substring)" },
        fiscal_year: { type: "number", description: "e.g. 2026" },
        action: { type: "string", enum: ["designate", "rescind", "purpose_change"], description: "Type of action" },
        organization: { type: "string", description: "Organization name (substring)" },
        limit: { type: "number", description: "Max rows (default 50, max 500)" },
      },
    },
  },
  {
    name: "get_legistar_link",
    description: `Look up the NYC Council Legistar legislative record (matter number, adoption date, detail-page URL) for a budget source document via the FY2008–FY2027 crosswalk. Filter by fiscal_year and/or document_type (schedule_c, terms_conditions, capital_a, capital_b, transparency_reso, transparency_reso_NN) or by local_file. Always surfaces the crosswalk \`status\`: 'confirmed' (matter verified), 'candidate' (anchor/exhibit not upgraded to confirmed), or 'not_located' (no matter found). Do not treat a candidate/not_located row as an authoritative citation.`,
    inputSchema: {
      type: "object",
      properties: {
        fiscal_year: { type: "number", description: "Any year FY2008–FY2027" },
        document_type: { type: "string", description: "schedule_c, terms_conditions, capital_a, capital_b, transparency_reso, or transparency_reso_NN (substring)" },
        local_file: { type: "string", description: "Repo-relative source PDF path (substring)" },
      },
    },
  },
  {
    name: "search_capital_projects",
    description: `Search §254 capital changes across FY2025–FY2027. Filter by agency, fiscal year, sponsor (council member surname; co-sponsored rows list multiple), or project title. \`fy1\` is the adoption-year allocation. NOTE: FY2025 is the "Appropriation Changes" document — different schema (no borough/sub-id/sponsor, adds an action column) and NOT reconcilable; FY2026/FY2027 share a schema and reconcile against printed subtotals. ${SCOPE_NOTE}`,
    inputSchema: {
      type: "object",
      properties: {
        agency: { type: "string", description: "Agency name (substring)" },
        fiscal_year: { type: "number", description: "2025, 2026, or 2027" },
        sponsor: { type: "string", description: "Sponsoring council member surname (substring)" },
        title: { type: "string", description: "Project title (substring)" },
        limit: { type: "number", description: "Max rows (default 50, max 500)" },
      },
    },
  },
  {
    name: "get_terms_conditions",
    description: `Retrieve Terms & Conditions (reporting mandates attached to appropriations) across FY2025–FY2027. Filter by fiscal year and/or agency name. ${SCOPE_NOTE}`,
    inputSchema: {
      type: "object",
      properties: {
        fiscal_year: { type: "number", description: "2025, 2026, or 2027" },
        agency: { type: "string", description: "Agency name (substring)" },
        limit: { type: "number", description: "Max rows (default 50, max 500)" },
      },
    },
  },
  {
    name: "list_available_fiscal_years",
    description: `Report which fiscal years each dataset actually covers, so callers are not surprised by the FY2008–FY2024 gap in parsed award data. Returns the parsed years for awards/terms/capital/transparency and the full crosswalk range.`,
    inputSchema: { type: "object", properties: {} },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    switch (name) {
      case "search_awards": {
        const a = z
          .object({
            ein: z.string().optional(),
            organization: z.string().optional(),
            program: z.string().optional(),
            council_member: z.string().optional(),
            fiscal_year: z.number().int().optional(),
            category: z.string().optional(),
            initiative: z.string().optional(),
            limit: z.number().int().optional(),
          })
          .parse(args ?? {});
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
        const a = z
          .object({ ein: z.string(), fiscal_year: z.number().int().optional() })
          .parse(args ?? {});
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
                `EIN ${a.ein}: ${rows.length} award(s) across FY2025–FY2027, total ${money(total)}.\n` +
                  `Organization name(s) on file: ${orgs.join("; ") || "(none)"}\n\n` +
                  `Per fiscal year:\n${summarizeAwardsByYear(rows)}\n\nRows:\n${body}`
              ),
            },
          ],
        };
      }

      case "search_transparency_resolutions": {
        const a = z
          .object({
            ein: z.string().optional(),
            council_member: z.string().optional(),
            fiscal_year: z.number().int().optional(),
            action: z.enum(["designate", "rescind", "purpose_change"]).optional(),
            organization: z.string().optional(),
            limit: z.number().int().optional(),
          })
          .parse(args ?? {});
        const rows = searchTransparency(a);
        if (rows.length === 0)
          return { content: [{ type: "text", text: withFooter("No matching transparency-resolution rows.") }] };
        const body = rows
          .map(
            (r) =>
              `Reso ${r.resolution} (${r.date}) · ${r.action} · ${money(r.amount)} · ${r.council_member || "(none)"} → ${r.organization}` +
              (r.agency ? ` · ${r.agency}` : "") +
              `\n    chart: ${r.chart}` +
              (r.purpose ? `\n    purpose: ${r.purpose}` : "")
          )
          .join("\n");
        return { content: [{ type: "text", text: withFooter(`${rows.length} row(s):\n\n${body}`) }] };
      }

      case "get_legistar_link": {
        const a = z
          .object({
            fiscal_year: z.number().int().optional(),
            document_type: z.string().optional(),
            local_file: z.string().optional(),
          })
          .parse(args ?? {});
        if (a.fiscal_year == null && !a.document_type && !a.local_file)
          return {
            content: [{ type: "text", text: withFooter("Provide at least one of: fiscal_year, document_type, local_file.") }],
            isError: true,
          };
        const rows = getLegistarLink(a);
        if (rows.length === 0)
          return { content: [{ type: "text", text: withFooter("No crosswalk rows matched.") }] };
        const body = rows
          .map(
            (r) =>
              `FY${r.fiscal_year} · ${r.document_type} · [${r.status}] ${r.legistar_matter_number || "(no matter)"}` +
              (r.adoption_date ? ` · adopted ${r.adoption_date}` : "") +
              (r.legistar_url ? `\n    ${r.legistar_url}` : "") +
              (r.notes ? `\n    notes: ${r.notes}` : "")
          )
          .join("\n\n");
        return { content: [{ type: "text", text: withFooter(`${rows.length} crosswalk row(s):\n\n${body}`) }] };
      }

      case "search_capital_projects": {
        const a = z
          .object({
            agency: z.string().optional(),
            fiscal_year: z.number().int().optional(),
            sponsor: z.string().optional(),
            title: z.string().optional(),
            limit: z.number().int().optional(),
          })
          .parse(args ?? {});
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
        const a = z
          .object({
            fiscal_year: z.number().int().optional(),
            agency: z.string().optional(),
            limit: z.number().int().optional(),
          })
          .parse(args ?? {});
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
        const r = listFiscalYears();
        const fmt = (ys: number[]) => (ys.length ? ys.map((y) => `FY${y}`).join(", ") : "(none)");
        const text =
          `NYC Budget MCP — dataset coverage:\n\n` +
          `Schedule C awards:        ${fmt(r.awards)} (parsed)\n` +
          `Terms & Conditions:       ${fmt(r.terms)} (parsed)\n` +
          `Capital (§254):           ${fmt(r.capital)} (parsed; FY2025 is a different, non-reconcilable document type)\n` +
          `Transparency Resolutions: ${fmt(r.transparency)} (from the FY2026 file, which embeds prior-year rows)\n` +
          `Legistar crosswalk:       FY${r.crosswalk.min}–FY${r.crosswalk.max} (provenance index; covers years not yet parsed to CSV)\n\n` +
          `FY2008–FY2024 award/terms/capital data is NOT parsed yet — only source PDFs exist for those years. The crosswalk still links them to Legistar.`;
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
