import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..", "..");

export default defineConfig({
  // Relative base: the built app works wherever it is served — /explorer/ under the GitHub Pages
  // project site (https://betanyc.github.io/New-York-City-Budget/explorer/), or a local server's
  // root. The app is one page with hash state, so nothing resolves against a deeper path.
  // src/paths.js turns asset paths into absolute URLs for DuckDB's worker.
  base: "./",
  plugins: [react()],
  server: {
    port: 5276,
    // src/query/sql.js imports the MCP's fold rule from mcp/dist/fold.js, outside this app.
    fs: { allow: [REPO] },
  },
  optimizeDeps: {
    // duckdb-wasm ships pre-bundled ESM that references its .wasm and worker by relative path;
    // esbuild's dependency pre-bundling would rewrite those references (as in nyc-eo-explorer).
    exclude: ["@duckdb/duckdb-wasm"],
    esbuildOptions: { target: "esnext" },
  },
  build: {
    target: "esnext",
    outDir: "dist",
    // The DuckDB engine is a ~33 MB .wasm; the chunk-size warning is not actionable.
    chunkSizeWarningLimit: 40_000,
  },
});
