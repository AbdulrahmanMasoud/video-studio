import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({ baseDirectory: dirname(fileURLToPath(import.meta.url)) });
const config = [...compat.extends("next/core-web-vitals", "next/typescript"), { ignores: [".next/**", "node_modules/**", "playwright-report/**", "test-results/**", "public/**", "next-env.d.ts", "src/lib/api-types.d.ts"] }];
export default config;
