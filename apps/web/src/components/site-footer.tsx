import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

export function SiteFooter() {
  const t = useTranslations("footer");
  const tl = useTranslations("legal");
  const tn = useTranslations("nav");
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-4 px-4 py-8 text-sm text-ink-2 sm:flex-row sm:items-center sm:px-6">
        <p>{t("rights", { year: new Date().getFullYear() })}</p>
        <nav aria-label="Footer" className="flex flex-wrap gap-4">
          <Link href="/pricing" className="hover:text-ink">{tn("pricing")}</Link>
          <Link href="/terms" className="hover:text-ink">{tl("terms")}</Link>
          <Link href="/privacy" className="hover:text-ink">{tl("privacy")}</Link>
          <Link href="/refunds" className="hover:text-ink">{tl("refunds")}</Link>
        </nav>
      </div>
    </footer>
  );
}
