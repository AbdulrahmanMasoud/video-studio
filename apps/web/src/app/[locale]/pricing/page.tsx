import { getTranslations, setRequestLocale } from "next-intl/server";
import { PlansGrid } from "@/components/plans-grid";

export default async function Pricing({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("pricing");
  return (
    <div className="section">
      <div className="mx-auto max-w-2xl text-center">
        <h1 className="text-4xl font-bold text-balance sm:text-5xl">{t("title")}</h1>
        <p className="mt-3 text-lg text-ink-2 text-pretty">{t("text")}</p>
      </div>
      <PlansGrid mode="public" />
    </div>
  );
}
