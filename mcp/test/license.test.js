/**
 * One license story (2026-10-16): everything BetaNYC made in the repository (code, derived data,
 * documentation) is MIT. Before this, the READMEs pointed data and docs at a CC BY-SA 4.0 file
 * (LICENSE-DATA) while LICENSE said MIT, so the published README contradicted the repo.
 * This fails if a second license comes back into the license statements, or if the statement
 * that the City's source documents are not covered goes missing.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const MCP = join(HERE, "..");
const REPO = join(MCP, "..");

const read = (p) => readFileSync(p, "utf8");
const FILES = {
  "LICENSE": join(REPO, "LICENSE"),
  "README.md": join(REPO, "README.md"),
  "mcp/README.md": join(MCP, "README.md"),
};
const SECOND_LICENSE = /LICENSE-DATA|CC[ -]BY|Creative Commons|ShareAlike|Share-Alike/i;

test("no license statement points at a second (CC BY-SA) license", () => {
  for (const [name, path] of Object.entries(FILES)) {
    const m = read(path).match(SECOND_LICENSE);
    assert.equal(m, null, `${name} still mentions "${m && m[0]}"`);
  }
});

test("the npm package ships the repository's LICENSE, word for word", () => {
  // mcp/LICENSE exists so `npm pack` includes it (npm cannot ship ../LICENSE). FAILS if it drifts.
  assert.equal(read(join(MCP, "LICENSE")), read(FILES.LICENSE));
});

test("package.json and LICENSE say MIT", () => {
  const pkg = JSON.parse(read(join(MCP, "package.json")));
  assert.equal(pkg.license, "MIT");
  assert.match(read(FILES.LICENSE), /^MIT License/);
});

test("LICENSE covers code, data and docs, and excludes the City's source documents", () => {
  const lic = read(FILES.LICENSE);
  for (const dir of ["`code/`", "`mcp/`", "`viz/`", "`data/`", "documentation"]) {
    assert.ok(lic.includes(dir), `LICENSE should name ${dir}`);
  }
  assert.match(lic, /source documents in `source\/` are NOT covered/);
});

test("both READMEs say the source documents are not covered by BetaNYC's license", () => {
  assert.match(read(FILES["README.md"]), /BetaNYC's license does not apply to them/);
  assert.match(read(FILES["mcp/README.md"]), /not covered by BetaNYC's license/);
});
