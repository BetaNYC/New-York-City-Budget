/** Shared by the Agency budgets specs (a spec file must not import another spec file). */

/** The three screens: all agencies, one agency (NYPD), one unit (NYPD 001 Operations), FY2025. */
export const PAGES = {
  list: "explorer/#view=agencies&abfy=2025",
  agency: "explorer/#view=agencies&abfy=2025&abag=056",
  unit: "explorer/#view=agencies&abfy=2025&abag=056&abunit=001",
};

/** Open a screen and wait until its numbers are on screen (the view sets data-ready="true"). */
export async function openView(page, path) {
  await page.goto(path);
  await page.locator('[data-view="agencies"][data-ready="true"]').waitFor({ timeout: 150_000 });
}
