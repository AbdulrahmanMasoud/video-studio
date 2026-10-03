import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { PreviewMarquee } from "@/components/marquee";
import { PlansGrid } from "@/components/plans-grid";
import { TemplateGallery } from "@/components/template-gallery";
import catalog from "../../../../../packages/shared/templates.json";

const ENABLED = ["steps", "mirror", "quiz", "chat", "top-five", "hot-take"];
const HERO = ["steps", "quiz", "top-five", "mirror", "chat", "hot-take", "showcase", "counter", "cinema", "breaking", "recipe", "journey"];

export default async function Landing({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("landing");
  const steps = [1, 2, 3] as const;
  const feats = [1, 2, 3, 4, 5, 6] as const;
  const faqs = [1, 2, 3, 4] as const;
  return (
    <div>
      {/* hero */}
      <section className="section pb-10 sm:pb-12">
        <div className="mx-auto max-w-3xl text-center">
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1 className="mt-3 text-5xl font-bold leading-[1.05] text-balance sm:text-6xl lg:text-7xl">{t("heroTitle")}</h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-ink-2 text-pretty">{t("heroText")}</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/register" className="btn-primary px-6 py-3 text-base">{t("ctaPrimary")}</Link>
            <Link href="/#templates" className="btn-secondary px-6 py-3 text-base">{t("ctaSecondary")}</Link>
          </div>
          <p className="mt-4 text-sm text-ink-3">{t("freeNote")}</p>
        </div>
      </section>
      <section aria-label="Template previews" className="-mx-4 sm:-mx-6">
        <PreviewMarquee names={HERO} />
      </section>

      {/* trust strip */}
      <section className="section pb-0">
        <p className="eyebrow">{t("trustTitle")}</p>
        <ul className="mt-3 grid gap-3 sm:grid-cols-3">
          {[t("trust1"), t("trust2"), t("trust3")].map((x) => (
            <li key={x} className="rounded-lg border border-line bg-surface px-4 py-3 text-sm text-ink-2 text-pretty">{x}</li>
          ))}
        </ul>
      </section>

      {/* how it works */}
      <section className="section">
        <h2 className="text-3xl font-bold text-balance sm:text-4xl">{t("howTitle")}</h2>
        <ol className="mt-8 grid gap-4 sm:grid-cols-3">
          {steps.map((i) => (
            <li key={i} className="card">
              <span className="display text-4xl font-bold text-brand tabular-nums">0{i}</span>
              <h3 className="mt-3 text-lg font-semibold">{t(`step${i}Title`)}</h3>
              <p className="mt-1 text-sm text-ink-2 text-pretty">{t(`step${i}Text`)}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* features */}
      <section className="section pt-0">
        <h2 className="text-3xl font-bold text-balance sm:text-4xl">{t("featuresTitle")}</h2>
        <ul className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {feats.map((i) => (
            <li key={i} className="card">
              <h3 className="font-semibold">{t(`feat${i}Title`)}</h3>
              <p className="mt-1 text-sm text-ink-2 text-pretty">{t(`feat${i}Text`)}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* gallery */}
      <section id="templates" className="section pt-0 scroll-mt-24">
        <h2 className="text-3xl font-bold text-balance sm:text-4xl">{t("galleryTitle")}</h2>
        <p className="mt-2 text-ink-2 text-pretty">{t("galleryText")}</p>
        <TemplateGallery templates={catalog.map((c) => ({ name: c.name, title: c.title, category: c.category, summary: c.summary, preview: c.preview }))} enabled={ENABLED} />
      </section>

      {/* pricing */}
      <section id="pricing" className="section pt-0 scroll-mt-24">
        <h2 className="text-3xl font-bold text-balance sm:text-4xl">{t("pricingTitle")}</h2>
        <p className="mt-2 text-ink-2">{t("pricingText")}</p>
        <PlansGrid mode="public" />
      </section>

      {/* faq */}
      <section className="section pt-0">
        <h2 className="text-3xl font-bold text-balance sm:text-4xl">{t("faqTitle")}</h2>
        <div className="mt-6 divide-y divide-line rounded-xl border border-line bg-surface">
          {faqs.map((i) => (
            <details key={i} className="group px-5 py-4">
              <summary className="cursor-pointer list-none font-semibold marker:content-none">
                <span className="me-2 text-brand" aria-hidden>+</span>{t(`faq${i}q`)}
              </summary>
              <p className="mt-2 text-sm text-ink-2 text-pretty">{t(`faq${i}a`)}</p>
            </details>
          ))}
        </div>
      </section>

      {/* final cta */}
      <section className="section pt-0">
        <div className="rounded-2xl border border-line bg-surface px-6 py-12 text-center">
          <h2 className="text-3xl font-bold text-balance sm:text-4xl">{t("finalTitle")}</h2>
          <p className="mt-2 text-ink-2">{t("finalText")}</p>
          <Link href="/register" className="btn-primary mt-6 px-6 py-3 text-base">{t("ctaPrimary")}</Link>
        </div>
      </section>
    </div>
  );
}
