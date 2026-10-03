"use client";
import { useTranslations } from "next-intl";
import { useState } from "react";

export type GalleryItem = { name: string; title: string; category: string; summary: string; preview: string };

export function TemplateGallery({ templates, enabled }: { templates: GalleryItem[]; enabled: string[] }) {
  const t = useTranslations("templates");
  const categories = Array.from(new Set(templates.map((x) => x.category)));
  const [cat, setCat] = useState<string | null>(null);
  const shown = templates.filter((x) => !cat || x.category === cat);
  return (
    <div className="mt-6">
      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by category">
        <button type="button" className={`chip ${cat === null ? "bg-brand text-on-brand" : "chip-muted"}`} aria-pressed={cat === null} onClick={() => setCat(null)}>All</button>
        {categories.map((c) => (
          <button key={c} type="button" className={`chip ${cat === c ? "bg-brand text-on-brand" : "chip-muted"}`} aria-pressed={cat === c} onClick={() => setCat(c)}>{c}</button>
        ))}
      </div>
      <ul className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {shown.map((tpl) => (
          <li key={tpl.name} className="group overflow-hidden rounded-xl border border-line bg-surface">
            <div className="relative overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={tpl.preview} alt={`${tpl.title} template preview`} className="aspect-[9/16] w-full object-cover transition-transform duration-200 ease-out group-hover:scale-[1.03]" loading="lazy" decoding="async" />
              <span className={`chip absolute start-2 top-2 ${enabled.includes(tpl.name) ? "bg-brand text-on-brand" : "bg-bg/80 text-ink-2"}`}>{enabled.includes(tpl.name) ? t("enabled") : t("comingSoon")}</span>
            </div>
            <div className="p-3">
              <h3 className="font-semibold text-balance">{tpl.title}</h3>
              <p className="text-xs text-ink-3">{tpl.category}</p>
              <p className="mt-1 line-clamp-2 text-xs text-ink-2 text-pretty">{tpl.summary}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
