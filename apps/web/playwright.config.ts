import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.BASE_URL || "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 15 * 60 * 1000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
    // containers ship a 64 MB /dev/shm; without this flag the page crashes under memory pressure (e.g. while the worker renders)
    launchOptions: { args: ["--disable-dev-shm-usage", "--no-sandbox"] },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
