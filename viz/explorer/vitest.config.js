import { defineConfig } from "vitest/config";

// Unit tests only (pure functions: query building, URL state, the year model, links). Node
// environment: nothing here touches the DOM, React or DuckDB. The parity test, which needs the
// built Parquet and the MCP's index, runs separately under node --test (npm run test:parity).
export default defineConfig({
  test: {
    environment: "node",
    include: ["test/unit/**/*.test.js"],
  },
});
