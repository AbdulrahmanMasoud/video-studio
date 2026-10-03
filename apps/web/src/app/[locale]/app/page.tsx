"use client";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { ErrorText, Spinner, StatusChip } from "@/components/ui";
import { Link } from "@/i18n/navigation";
import { api, type ProjectSummary } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { isActive } from "@/lib/status";

export default function Dashboard() {
  const t = useTranslations("dashboard");
  const tn = useTranslations("nav");
  const locale = useLocale();
  const { me } = useAuth();
  const [items, setItems] = useState<ProjectSummary[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const load = () => api<{ items: ProjectSummary[]; total: number }>("/projects").then((r) => setItems(r.items)).catch(setError);
  useEffect(() => {
    load();
  }, []);
  useEffect(() => {
    if (!items?.some((p) => isActive(p.status))) return;
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, [items]);
  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{t("title")}</h1>
          {me && <p className="text-sm text-ink-2">{t("plan", { plan: me.plan.name })} · {t("credits", { n: me.user.credits })}</p>}
        </div>
        <Link href="/app/new" className="btn-primary" data-testid="new-video">{tn("new")}</Link>
      </div>
      <ErrorText error={error} />
      {!items ? (
        <div className="py-10"><Spinner /></div>
      ) : items.length === 0 ? (
        <div className="card mt-6 text-center">
          <p className="text-ink-2">{t("empty")}</p>
          <Link href="/app/new" className="btn-primary mt-4">{t("emptyCta")}</Link>
        </div>
      ) : (
        <div className="card mt-6 overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 text-start text-xs uppercase text-ink-2">
              <tr><th className="px-4 py-2 text-start">{t("columns.title")}</th><th className="px-4 py-2 text-start">{t("columns.template")}</th><th className="px-4 py-2 text-start">{t("columns.status")}</th><th className="px-4 py-2 text-start">{t("columns.updated")}</th></tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id} className="border-t border-line hover:bg-surface-2">
                  <td className="px-4 py-3"><Link href={`/app/projects/${p.id}`} className="font-semibold text-brand hover:underline">{p.title}</Link></td>
                  <td className="px-4 py-3">{p.template}</td>
                  <td className="px-4 py-3"><StatusChip status={p.status} />{isActive(p.status) && <span className="ms-2 text-xs text-ink-2">{p.progress}%</span>}</td>
                  <td className="px-4 py-3 text-ink-2">{fmtDate(p.updated_at, locale)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
