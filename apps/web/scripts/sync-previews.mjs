// Copy the template preview images (docs/previews) into public/previews for local dev and builds.
import { cpSync, existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const candidates = [resolve(here, "../../../docs/previews"), resolve(here, "../../docs/previews")];
const src = candidates.find((c) => existsSync(c));
const dst = resolve(here, "../public/previews");
if (src) {
  mkdirSync(dst, { recursive: true });
  cpSync(src, dst, { recursive: true });
  console.log(`previews synced from ${src}`);
} else if (!existsSync(dst)) {
  console.warn("no docs/previews found; template images will 404");
}
