import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { registerViaUi } from "./helpers";

/** Arabic locale renders RTL without layout breakage: html dir, no horizontal overflow, screenshots of 3 pages; axe has no serious violations. */
const pages = [
  { name: "landing", path: "/ar", auth: false },
  { name: "register", path: "/ar/register", auth: false },
  { name: "dashboard", path: "/ar/app", auth: true },
];

for (const p of pages) {
  test(`arabic ${p.name} is RTL and does not overflow`, async ({ page }, testInfo) => {
    if (p.auth) await registerViaUi(page, "ar");
    await page.goto(p.path);
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
    for (const width of [390, 1280]) {
      await page.setViewportSize({ width, height: 900 });
      await page.waitForTimeout(300);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow, `horizontal overflow at ${width}px`).toBeLessThanOrEqual(1);
      await page.screenshot({ path: testInfo.outputPath(`${p.name}-${width}.png`), fullPage: true });
    }
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious, JSON.stringify(serious.map((v) => ({ id: v.id, nodes: v.nodes.length })))).toEqual([]);
  });
}

test("english landing has no serious accessibility violations", async ({ page }) => {
  await page.goto("/en");
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(results.violations.filter((v) => v.impact === "serious" || v.impact === "critical")).toEqual([]);
});
