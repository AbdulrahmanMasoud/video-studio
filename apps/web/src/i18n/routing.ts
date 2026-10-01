import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({ locales: ["en", "ar"], defaultLocale: "en", localePrefix: "always" });
export type Locale = (typeof routing.locales)[number];
export const isRtl = (locale: string) => locale === "ar";
