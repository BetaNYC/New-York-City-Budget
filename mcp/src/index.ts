#!/usr/bin/env node
import { main } from "./server.js";

main().catch((err) => {
  console.error(`Fatal: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
});
