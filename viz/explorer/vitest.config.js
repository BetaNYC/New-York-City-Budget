import { defineConfig } from "vitest/config";

// Unit tests (pure functions: query building, URL state, the year model, links; and static
// markup of small components, rendered with react-dom/server). Node environment: no DOM, no
// DuckDB. The parity test, which needs the built Parquet and the MCP's index, runs separately
// under node --test (npm run test:parity).
export default defineConfig({
  // The automatic JSX runtime, as the app build uses (@vitejs/plugin-react), so .jsx modules
  // imported by a test need no `React` in scope.
  esbuild: { jsx: "automatic" },
  test: {
    environment: "node",
    include: ["test/unit/**/*.test.js"],
  },
});
