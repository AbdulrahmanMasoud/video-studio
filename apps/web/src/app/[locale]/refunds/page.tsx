import { getTranslations, setRequestLocale } from "next-intl/server";

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("legal");
  return (
    <article className="prose max-w-3xl py-6">
      <h1 className="text-3xl font-extrabold">{t("refunds")}</h1>
      <p className="mt-4 text-ink/70">{t("placeholder")}</p>
    </article>
  );
}
