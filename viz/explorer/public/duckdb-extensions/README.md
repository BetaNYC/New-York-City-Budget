# DuckDB extensions, served from this site (#301)

DuckDB-WASM loads the `parquet` extension (every Council view that reads Parquet) and the `json`
extension (Organizations) at run time. By default it fetches them from DuckDB's server,
`https://extensions.duckdb.org`, so every visitor's browser contacted a third party, and the
explorer broke if that server was down. These are the same two files, served from this site
instead: `src/duckdb/store.js` sets `custom_extension_repository` to this folder ([DuckDB-WASM:
Load Extensions](https://duckdb.org/docs/stable/clients/wasm/extensions)).

| File | Downloaded from | Bytes | sha256 |
|---|---|---:|---|
| `v1.4.3/wasm_eh/parquet.duckdb_extension.wasm` | https://extensions.duckdb.org/v1.4.3/wasm_eh/parquet.duckdb_extension.wasm | 3,045,039 | `22765c8f7dc741cda2b571a66ac7bb355295d7d69a6c37e5315b265672984f55` |
| `v1.4.3/wasm_eh/json.duckdb_extension.wasm` | https://extensions.duckdb.org/v1.4.3/wasm_eh/json.duckdb_extension.wasm | 820,646 | `b997276c8e15cc3ebdeda340d73d15dc1c4f4755ad281280451cb0a2f79302e9` |

Downloaded 2026-11-14 (the server's `last-modified`: 2025-12-08). The files are unchanged, so
DuckDB's signature check still passes; nothing turns it off. `v1.4.3` is the DuckDB version inside
`@duckdb/duckdb-wasm` 1.32.0 (`viz/explorer/package.json`), and `wasm_eh` is the bundle the explorer
uses. **When that package is upgraded, download the new version's files into a new folder** and
update this table and `test/duckdb-extensions.test.mjs`; that test fails until you do.

DuckDB is MIT-licensed (https://github.com/duckdb/duckdb/blob/main/LICENSE).
