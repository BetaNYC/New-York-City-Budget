import { readFileSync } from "fs";

/** This package's version, from its package.json (one place, for the server and the download's User-Agent). */
export const PACKAGE_VERSION = (
  JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf-8")) as { version: string }
).version;
