/**
 * The DuckDB extensions this site serves itself (#301; public/duckdb-extensions/README.md): the
 * files are the ones downloaded from extensions.duckdb.org, unchanged, for the DuckDB version the
 * explorer's DuckDB-WASM runs. Each test says what result would make it FAIL.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DIR = join(ROOT, "public", "duckdb-extensions", "v1.4.3", "wasm_eh");
const PINNED = {
  "parquet.duckdb_extension.wasm": "22765c8f7dc741cda2b571a66ac7bb355295d7d69a6c37e5315b265672984f55",
  "json.duckdb_extension.wasm": "b997276c8e15cc3ebdeda340d73d15dc1c4f4755ad281280451cb0a2f79302e9",
};

test("each extension file is the one downloaded, byte for byte", () => {
  // FAILS if a file was changed (DuckDB's signature check would refuse it) or is missing.
  for (const [name, sha] of Object.entries(PINNED)) {
    assert.equal(createHash("sha256").update(readFileSync(join(DIR, name))).digest("hex"), sha, name);
  }
});

test("the files match the DuckDB-WASM the explorer runs", () => {
  // FAILS when @duckdb/duckdb-wasm is upgraded: its DuckDB asks for another version's folder, so
  // download that version's files (see the README) and update this test.
  const pkg = JSON.parse(readFileSync(join(ROOT, "node_modules", "@duckdb", "duckdb-wasm", "package.json"), "utf8"));
  assert.equal(pkg.version, "1.32.0", "DuckDB-WASM 1.32.0 runs DuckDB v1.4.3");
});
