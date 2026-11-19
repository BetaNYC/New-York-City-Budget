/**
 * Each data answer's Sources block (#334 review): one line per source the tool answers from, in
 * about_data's own words on whether it is official (the shared module's officialWording), read
 * from DATA-SOURCES.json, the file about_data reads. So an answer and about_data agree, and the
 * list cannot drift from the file: a source is linked in an answer exactly when DATA-SOURCES.json
 * lists the tool for it (test/provenance-lists.test.js checks both directions).
 */
import { readFileSync } from "node:fs";
import { officialWording, parseDataSources, type DataSource } from "./betanyc-tools.js";

/** Beside dist/ in the package, as about_data's dataSourcesPath (the prebuild script copies it). */
const DATA_SOURCES = new URL("../DATA-SOURCES.json", import.meta.url);

let loaded: DataSource[] | null = null;

/** The valid sources in DATA-SOURCES.json, read once; none when the file is missing or unreadable. */
function allSources(): DataSource[] {
  if (loaded) return loaded;
  try {
    loaded = (parseDataSources(readFileSync(DATA_SOURCES, "utf8")).doc?.sources ?? []).filter((s) => s.valid);
  } catch {
    loaded = [];
  }
  return loaded;
}

/** The sources DATA-SOURCES.json lists `tool` for, in file order. */
export function toolSources(tool: string): DataSource[] {
  return allSources().filter((s) => s.tools.includes(tool));
}

/** What about_data says of one source: published as is, modified by BetaNYC or produced by BetaNYC, with the official record's name and link. */
export function sourceLabel(s: DataSource): string {
  return officialWording({
    official: s.official === true,
    changed: s.changes?.changed === true,
    steps: s.changes?.steps ?? [],
    publisher: s.publisher?.name ?? "",
    publisherUrl: s.publisher?.url ?? null,
    sourceName: s.source_name ?? "",
    sourceUrl: s.source_url ?? "",
  });
}

/** The block that ends every data answer of `tool`. */
export function sourcesBlock(tool: string): string {
  const list = toolSources(tool);
  if (!list.length) {
    return "Sources: this server could not read its DATA-SOURCES.json. BetaNYC modified or produced all of its data, so none of it is an official record; about_data has the details.";
  }
  return ["Sources (as about_data gives them):", ...list.map((s) => `  ${s.title}: ${sourceLabel(s)}`)].join("\n");
}
