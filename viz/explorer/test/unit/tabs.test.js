import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, test } from "vitest";

import { HashLink } from "../../src/components/ui.jsx";

describe("view tabs (DESIGN-NOTES.md §1)", () => {
  test("the current tab carries aria-current=page; the others do not", () => {
    const on = renderToStaticMarkup(createElement(HashLink, { href: "#view=capital", onGo: () => {}, className: "active", current: true }, "Capital"));
    const off = renderToStaticMarkup(createElement(HashLink, { href: "#view=years", onGo: () => {} }, "Years"));
    expect(on).toContain('aria-current="page"');
    expect(on).toContain('href="#view=capital"');
    expect(off).not.toContain("aria-current");
  });
});
