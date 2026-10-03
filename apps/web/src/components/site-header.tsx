"use client";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Link, usePathname, useRouter } from "@/i18n/navigation";
import { useAuth } from "./auth-provider";

export function SiteHeader() {
  const t = useTranslations("nav");
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const { me, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const other = locale === "ar" ? "en" : "ar";
  const links = me
    ? [{ href: "/app", label: t("dashboard") }, { href: "/app/new", label: t("new") }, { href: "/app/billing", label: t("billing") }, { href: "/app/settings", label: t("settings") }]
    : [{ href: "/#templates", label: t("templates") }, { href: "/pricing", label: t("pricing") }];
  const active = (href: string) => href !== "/" && pathname.startsWith(href.replace(/#.*/, ""));
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="display flex items-center gap-2 text-lg font-bold text-ink">
          <span aria-hidden className="inline-flex size-7 items-center justify-center rounded-md bg-brand text-on-brand">▶</span>
          VideoStudio
        </Link>
        <nav aria-label="Main" className="hidden items-center gap-1 sm:flex">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors hover:bg-surface ${active(l.href) ? "text-brand" : "text-ink-2 hover:text-ink"}`}>{l.label}</Link>
          ))}
          <button type="button" className="btn-ghost" onClick={() => router.replace(pathname, { locale: other })} aria-label={t("language")}>
            {other === "ar" ? "العربية" : "English"}
          </button>
          {me ? (
            <button type="button" className="btn-secondary" onClick={async () => { await logout(); router.push("/"); }}>{t("logout")}</button>
          ) : (
            <>
              <Link href="/login" className="btn-secondary">{t("login")}</Link>
              <Link href="/register" className="btn-primary">{t("register")}</Link>
            </>
          )}
        </nav>
        <button type="button" className="btn-secondary sm:hidden" aria-expanded={open} aria-controls="mobile-nav" onClick={() => setOpen(!open)}>{t("menu")}</button>
      </div>
      {open && (
        <nav id="mobile-nav" aria-label="Mobile" className="flex flex-col gap-1 border-t border-line px-4 py-2 sm:hidden">
          {links.map((l) => (<Link key={l.href} href={l.href} className="rounded-md px-3 py-2 text-sm font-medium hover:bg-surface" onClick={() => setOpen(false)}>{l.label}</Link>))}
          <button type="button" className="rounded-md px-3 py-2 text-start text-sm font-medium" onClick={() => router.replace(pathname, { locale: other })}>{other === "ar" ? "العربية" : "English"}</button>
          {me ? (
            <button type="button" className="rounded-md px-3 py-2 text-start text-sm font-medium" onClick={async () => { await logout(); router.push("/"); }}>{t("logout")}</button>
          ) : (
            <>
              <Link href="/login" className="rounded-md px-3 py-2 text-sm font-medium">{t("login")}</Link>
              <Link href="/register" className="rounded-md px-3 py-2 text-sm font-medium">{t("register")}</Link>
            </>
          )}
        </nav>
      )}
    </header>
  );
}
