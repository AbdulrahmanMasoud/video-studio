import { useTranslations } from "next-intl";

export type GalleryItem = { name: string; title: string; category: string; summary: string; preview: string };

export function TemplateGallery({ templates, enabled }: { templates: GalleryItem[]; enabled: string[] }) {
  const t = useTranslations("templates");
  return (
    <ul className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {templates.map((tpl) => (
        <li key={tpl.name} className="card p-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={tpl.preview} alt={`${tpl.title} preview`} className="aspect-[9/16] w-full rounded-md object-cover" loading="lazy" />
          <div className="mt-2 flex items-start justify-between gap-2">
            <div>
              <h3 className="font-semibold">{tpl.title}</h3>
              <p className="text-xs text-ink/60">{tpl.category}</p>
            </div>
            <span className={`chip ${enabled.includes(tpl.name) ? "bg-green-100 text-green-800" : "bg-ink/10 text-ink/70"}`}>{enabled.includes(tpl.name) ? t("enabled") : t("comingSoon")}</span>
          </div>
          <p className="mt-1 line-clamp-2 text-xs text-ink/70">{tpl.summary}</p>
        </li>
      ))}
    </ul>
  );
}
