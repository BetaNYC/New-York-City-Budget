#!/usr/bin/env node
/**
 * nyc-budget-mcp            start the MCP server (stdio)
 * nyc-budget-mcp download --pdf-tables [--pdfs] [--from <manifest URL or path>]
 *                           download the optional PDF tables (and the PDFs) into the per-user
 *                           data folder, checking every file's sha256 (src/pdfdata.ts, #215)
 */
import { main } from "./server.js";
import { dataDir, downloadPdfData } from "./pdfdata.js";

const USAGE = `usage:
  nyc-budget-mcp                                   start the MCP server (stdio)
  nyc-budget-mcp download --pdf-tables [--pdfs]    download the checked PDF tables (about 17 MB; 115 MB on disk) and,
                                                   with --pdfs, the PDF files, from this repo's GitHub Releases
    --from <url or path>   a manifest (pdf-tables.manifest.json) to use instead of the newest release
  Files go to ${dataDir()} (set NYC_BUDGET_DATA_DIR to choose another folder).`;

async function download(args: string[]): Promise<void> {
  const known = new Set(["--pdf-tables", "--pdfs", "--from"]);
  const at = args.indexOf("--from");
  const from = at >= 0 ? args[at + 1] : undefined;
  const bad = args.filter((a, i) => !known.has(a) && !(at >= 0 && i === at + 1));
  if (bad.length || (at >= 0 && !from) || (!args.includes("--pdf-tables") && !args.includes("--pdfs"))) {
    console.error(USAGE);
    process.exit(2);
  }
  await downloadPdfData({ from, pdfs: args.includes("--pdfs") });
}

const [cmd, ...rest] = process.argv.slice(2);
const run = cmd === "download" ? download(rest) : cmd === "--help" || cmd === "help" ? Promise.resolve(console.error(USAGE)) : main();
run.catch((err) => {
  console.error(`Fatal: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
});
