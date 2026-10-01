import { expect, type APIRequestContext, type Page } from "@playwright/test";
import { createHash } from "node:crypto";
import { deflateSync } from "node:zlib";

export const API_URL = process.env.API_URL || "http://localhost:8000";

export function uniqueEmail(prefix = "e2e") {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

/** A tiny solid-colour PNG generated in-process (no fixtures needed). */
export function pngBuffer(width: number, height: number, rgb: [number, number, number]): Buffer {
  const crc32 = (buf: Buffer) => {
    let c = ~0;
    for (const b of buf) {
      c ^= b;
      for (let k = 0; k < 8; k++) c = (c >>> 1) ^ (0xedb88320 & -(c & 1));
    }
    return (~c) >>> 0;
  };
  const chunk = (type: string, data: Buffer) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const td = Buffer.concat([Buffer.from(type), data]);
    const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(td));
    return Buffer.concat([len, td, crc]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4); ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  const row = Buffer.concat([Buffer.from([0]), Buffer.alloc(width * 3)]);
  for (let x = 0; x < width; x++) { row[1 + x * 3] = rgb[0]; row[2 + x * 3] = rgb[1]; row[3 + x * 3] = rgb[2]; }
  const raw = Buffer.concat(Array.from({ length: height }, () => row));
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk("IHDR", ihdr), chunk("IDAT", deflateSync(raw)), chunk("IEND", Buffer.alloc(0))]);
}

export async function registerViaUi(page: Page, locale = "en") {
  const email = uniqueEmail();
  const password = "e2e-password-123";
  await page.goto(`/${locale}/register`);
  await page.getByLabel(locale === "ar" ? "البريد الإلكتروني" : "Email").fill(email);
  await page.getByLabel(locale === "ar" ? "كلمة المرور" : "Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: locale === "ar" ? "إنشاء حساب" : "Create account" }).click();
  await expect(page).toHaveURL(new RegExp(`/${locale}/app$`));
  return { email, password };
}

export async function grantCredits(request: APIRequestContext, email: string, credits: number) {
  const r = await request.post(`${API_URL}/admin/grant-credits`, { headers: { "X-Admin-Key": process.env.ADMIN_API_KEY || "change-me-admin-key" }, data: { email, credits } });
  expect(r.ok()).toBeTruthy();
}

export const md5 = (b: Buffer) => createHash("md5").update(b).digest("hex");
