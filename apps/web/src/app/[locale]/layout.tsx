import type { Metadata } from "next";
import { IBM_Plex_Sans_Arabic, Inter } from "next/font/google";
import { notFound } from "next/navigation";
import { NextIntlClientProvider, hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { isRtl, routing } from "@/i18n/routing";
import { AuthProvider } from "@/components/auth-provider";
import { SiteHeader } from "@/components/site-header";
import "../globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const plexArabic = IBM_Plex_Sans_Arabic({ subsets: ["arabic"], weight: ["400", "500", "600", "700"], variable: "--font-arabic", display: "swap" });

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "app" });
  return { title: { default: t("name"), template: `%s · ${t("name")}` }, description: t("tagline") };
}

export default async function LocaleLayout({ children, params }: { children: React.ReactNode; params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();
  setRequestLocale(locale);
  const t = await getTranslations({ locale, namespace: "app" });
  return (
    <html lang={locale} dir={isRtl(locale) ? "rtl" : "ltr"} className={`${inter.variable} ${plexArabic.variable}`}>
      <body className="min-h-screen antialiased">
        <a href="#main" className="sr-only sr-only-focusable">{t("skip")}</a>
        <NextIntlClientProvider>
          <AuthProvider>
            <SiteHeader />
            <main id="main" className="mx-auto w-full max-w-6xl px-4 pb-16 pt-6 sm:px-6">{children}</main>
          </AuthProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
