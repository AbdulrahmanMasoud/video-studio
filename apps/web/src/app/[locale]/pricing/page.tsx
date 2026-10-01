import { getTranslations, setRequestLocale } from "next-intl/server";
import { PlansGrid } from "@/components/plans-grid";

export default async function Pricing({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("pricing");
  return (
    <div className="py-6">
      <h1 className="text-3xl font-extrabold">{t("title")}</h1>
      <p className="mt-2 text-ink/70">{t("text")}</p>
      <PlansGrid mode="public" />
    </div>
  );
}
