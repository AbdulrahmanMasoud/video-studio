import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { TemplateGallery } from "@/components/template-gallery";
import catalog from "../../../../../packages/shared/templates.json";

export default async function Landing({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("landing");
  const steps = [1, 2, 3] as const;
  return (
    <div>
      <section className="grid items-center gap-8 py-10 md:grid-cols-2">
        <div>
          <h1 className="text-4xl font-extrabold leading-tight text-ink sm:text-5xl">{t("heroTitle")}</h1>
          <p className="mt-4 text-lg text-ink/70">{t("heroText")}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/register" className="btn-primary">{t("ctaPrimary")}</Link>
            <Link href="/pricing" className="btn-secondary">{t("ctaSecondary")}</Link>
          </div>
          <p className="mt-3 text-sm text-ink/60">{t("freeNote")}</p>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {["steps", "quiz", "top-five", "mirror", "chat", "hot-take"].map((n) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={n} src={`/previews/${n}.jpg`} alt={`${n} template preview`} className="aspect-[9/16] w-full rounded-lg object-cover shadow" loading="lazy" />
          ))}
        </div>
      </section>
      <section className="py-10">
        <h2 className="text-2xl font-bold">{t("howTitle")}</h2>
        <ol className="mt-4 grid gap-4 sm:grid-cols-3">
          {steps.map((i) => (
            <li key={i} className="card">
              <span className="chip bg-brand/10 text-brand">{i}</span>
              <h3 className="mt-2 font-semibold">{t(`step${i}Title`)}</h3>
              <p className="mt-1 text-sm text-ink/70">{t(`step${i}Text`)}</p>
            </li>
          ))}
        </ol>
      </section>
      <section className="py-10">
        <h2 className="text-2xl font-bold">{t("galleryTitle")}</h2>
        <p className="mt-1 text-ink/70">{t("galleryText")}</p>
        <TemplateGallery templates={catalog.map((c) => ({ name: c.name, title: c.title, category: c.category, summary: c.summary, preview: c.preview }))} enabled={["steps", "mirror", "quiz", "chat", "top-five", "hot-take"]} />
      </section>
    </div>
  );
}
