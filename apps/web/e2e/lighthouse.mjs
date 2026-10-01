// Lighthouse accessibility ≥ 90 on the landing page and the (authenticated) dashboard. Run inside the e2e image.
import lighthouse from "lighthouse";
import { launch } from "chrome-launcher";
import { existsSync, readdirSync } from "node:fs";

/** Playwright's bundled Chromium (inside the e2e image) or whatever chrome-launcher finds. */
function chromePath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const root = "/ms-playwright";
  if (!existsSync(root)) return undefined;
  for (const d of readdirSync(root).filter((n) => n.startsWith("chromium-"))) {
    for (const sub of readdirSync(`${root}/${d}`)) {
      const cand = `${root}/${d}/${sub}/chrome`;
      if (sub.startsWith("chrome-linux") && existsSync(cand)) return cand;
    }
  }
  return undefined;
}

const BASE = process.env.BASE_URL || "http://localhost:3000";
const API = process.env.API_URL || "http://localhost:8000";
const MIN = Number(process.env.LH_MIN_A11Y || 90);

async function register() {
  const email = `lh-${Date.now()}@example.com`;
  const r = await fetch(`${API}/auth/register`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password: "lighthouse-pass-123" }) });
  if (!r.ok) throw new Error(`register failed: ${r.status}`);
  const cookie = r.headers.getSetCookie().map((c) => c.split(";")[0]).join("; ");
  return cookie;
}

const chrome = await launch({ chromePath: chromePath(), chromeFlags: ["--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"] });
try {
  const cookie = await register();
  const targets = [{ name: "landing", url: `${BASE}/en`, headers: {} }, { name: "dashboard", url: `${BASE}/en/app`, headers: { Cookie: cookie } }];
  let failed = false;
  for (const t of targets) {
    const result = await lighthouse(t.url, { port: chrome.port, onlyCategories: ["accessibility"], extraHeaders: t.headers, output: "json", logLevel: "error" });
    const score = Math.round((result.lhr.categories.accessibility.score || 0) * 100);
    const audits = Object.values(result.lhr.audits).filter((a) => a.score !== null && a.score < 1 && a.scoreDisplayMode !== "informative").map((a) => a.id);
    console.log(`${t.name}: accessibility ${score} (${audits.length ? "failing: " + audits.join(", ") : "no failing audits"})`);
    if (score < MIN) failed = true;
  }
  if (failed) { console.error(`accessibility below ${MIN}`); process.exit(1); }
} finally {
  await chrome.kill();
}
