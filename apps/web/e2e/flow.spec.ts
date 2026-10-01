import { expect, test } from "@playwright/test";
import { pngBuffer, registerViaUi } from "./helpers";
import path from "node:path";

/** Phase 4 DoD: register → new project with 2 image assets → preview → edit text → swap an asset → render → download. */
test("register → create → preview → edit → swap → render → download", async ({ page, request }) => {
  test.setTimeout(15 * 60 * 1000);
  await registerViaUi(page);
  await page.getByTestId("new-video").click();
  await expect(page).toHaveURL(/\/en\/app\/new$/);
  // 1) source: upload the fixture (direct to S3, progress shown)
  await page.getByTestId("input-file").setInputFiles(path.join(__dirname, "fixtures", "voice.mp3"));
  await expect(page.getByText("Uploaded")).toBeVisible({ timeout: 60_000 });
  await page.getByTestId("wizard-next").click();
  // 2) format
  await page.getByLabel("Language of the video").selectOption("en");
  await page.getByLabel("Size").selectOption("9:16");
  await page.getByTestId("wizard-next").click();
  // 3) template
  await page.getByTestId("template-top-five").click();
  await page.getByTestId("wizard-next").click();
  // 4) two image assets
  await page.getByTestId("asset-files").setInputFiles([
    { name: "red.png", mimeType: "image/png", buffer: pngBuffer(320, 320, [230, 60, 60]) },
    { name: "blue.png", mimeType: "image/png", buffer: pngBuffer(320, 320, [60, 160, 230]) },
  ]);
  await page.getByLabel("What is this?").first().fill("a red card");
  await page.getByTestId("wizard-next").click();
  // 5) brief → create
  await page.getByLabel("Title").fill("E2E top five");
  await page.getByTestId("wizard-create").click();
  await expect(page).toHaveURL(/\/en\/app\/projects\/[0-9a-f-]+$/, { timeout: 60_000 });
  await expect(page.getByTestId("project-title")).toHaveText("E2E top five");
  // preview ready: contact sheet + editable texts + asset panel
  await expect(page.getByTestId("contact-sheet")).toBeVisible({ timeout: 10 * 60 * 1000 });
  await expect(page.getByTestId("render")).toBeVisible();
  const panel = page.getByTestId("asset-panel");
  await expect(panel).toBeVisible();
  // edit a text
  const firstField = page.locator("[data-testid^='field-']").first();
  const fieldId = await firstField.getAttribute("data-testid");
  await firstField.fill("Edited by Playwright");
  await page.getByTestId("apply-texts").click();
  await expect(page.getByText("Texts updated.")).toBeVisible({ timeout: 5 * 60 * 1000 });
  await expect(page.getByTestId("render")).toBeVisible({ timeout: 5 * 60 * 1000 });
  await expect(page.getByTestId(fieldId!)).toHaveValue("Edited by Playwright");
  // swap an asset: first slot gets the other image
  const firstSlot = panel.locator("[data-testid^='slot-']").first();
  const slotPath = (await firstSlot.getAttribute("data-testid"))!.replace("slot-", "");
  await page.getByTestId(`swap-${slotPath}`).click();
  const picker = page.getByTestId(`picker-${slotPath}`);
  const options = await picker.locator("option").allTextContents();
  const target = options.find((o) => o.includes("blue.png")) ?? options[1];
  await picker.selectOption({ label: target });
  await expect(page.getByTestId("render")).toBeVisible({ timeout: 5 * 60 * 1000 });
  await expect(page.getByTestId(`slot-${slotPath}`)).toContainText("blue.png", { timeout: 60_000 });
  // render → done → download
  await page.getByTestId("render").click();
  await expect(page.getByTestId("done-card")).toBeVisible({ timeout: 15 * 60 * 1000 });
  const [dl] = await Promise.all([page.waitForResponse((r) => r.url().includes("/download") && r.request().method() === "GET"), page.getByTestId("download").click()]);
  expect(dl.ok()).toBeTruthy();
  const { url, filename } = (await dl.json()) as { url: string; filename: string };
  expect(filename).toBe("E2E top five.mp4");
  expect(url).toContain("final.mp4");
  const res = await request.get(url);
  expect(res.ok()).toBeTruthy();
  const body = await res.body();
  expect(body.length).toBeGreaterThan(50_000);
  expect(body.subarray(4, 8).toString()).toBe("ftyp");
});
