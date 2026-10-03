"use client";
import { useLocale, useTranslations } from "next-intl";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { AssetPanel } from "@/components/asset-panel";
import { useAuth } from "@/components/auth-provider";
import { TextsForm } from "@/components/texts-form";
import { Timeline } from "@/components/timeline";
import { ErrorText, Spinner, StatusChip } from "@/components/ui";
import { Link, useRouter } from "@/i18n/navigation";
import { ApiFailure, api, type Project } from "@/lib/api";
import { isKnownError } from "@/lib/errors";
import { fmtDuration } from "@/lib/format";
import { isActive, watchProject } from "@/lib/status";

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const t = useTranslations("project");
  const te = useTranslations("errors");
  const locale = useLocale();
  const router = useRouter();
  const { me, refresh } = useAuth();
  const [p, setP] = useState<Project | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [live, setLive] = useState<{ status: string; progress?: number | null } | null>(null);

  const load = useCallback(() => api<Project>(`/projects/${id}`).then(setP).catch(setError), [id]);
  useEffect(() => {
    load();
  }, [load]);
  // live updates while a job runs; reload the full project on every state change
  useEffect(() => {
    if (!p || !isActive(p.status)) return;
    let last = p.status;
    const stop = watchProject(id, (d) => {
      setLive(d);
      if (d.status && d.status !== last) {
        last = d.status;
        load();
      }
    }, () => { load(); refresh(); });
    return stop;
  }, [p?.status, id, load, refresh, p]);

  const act = async (name: string, fn: () => Promise<unknown>) => {
    setBusy(name);
    setError(null);
    try {
      await fn();
      await load();
      await refresh();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(null);
    }
  };

  if (error && !p) return <div className="py-10"><ErrorText error={error} /></div>;
  if (!p) return <div className="py-10"><Spinner /></div>;
  const status = live?.status && isActive(p.status) ? live.status : p.status;
  const progress = live?.progress ?? p.progress;
  const errorMessage = p.error_code ? (isKnownError(p.error_code) ? te(p.error_code) : p.error_message) : null;
  const stageKey = (["preview", "render", "edit"] as const).find((s) => s === p.failed_stage) ?? "preview";
  const qaIssues = Array.isArray((p.qa as { issues?: unknown } | null)?.issues) ? ((p.qa as { issues: unknown[] }).issues.map(String)) : [];
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div>
        <Link href="/app" className="text-sm text-brand hover:underline">← {t("backToList")}</Link>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold" data-testid="project-title">{p.title}</h1>
          <StatusChip status={status} />
          {isActive(status) && <span className="text-sm text-ink-2" aria-live="polite" data-testid="progress">{progress}% · {t("eventsLive")}</span>}
        </div>
        <ErrorText error={error} />
        {status === "failed" && (
          <div className="card mt-4 border-red-500/30 bg-red-500/10" role="alert">
            <h2 className="font-bold text-red-300">{t("failedTitle")}</h2>
            <p className="text-sm text-red-300">{t("failedStage", { stage: t(`stage.${stageKey}`) })}: {errorMessage}</p>
            <button type="button" className="btn-primary mt-3" disabled={!!busy} onClick={() => act("retry", () => api(`/projects/${id}/retry`, { method: "POST" }))}>{t("retry")}</button>
          </div>
        )}
        {status === "done" && (
          <div className="card mt-4 border-green-500/30 bg-green-500/10" data-testid="done-card">
            <h2 className="font-bold text-green-300">{t("doneTitle")}</h2>
            {me?.plan.watermark && <p className="hint">{t("watermarkNote")}</p>}
            <button type="button" className="btn-primary mt-3" data-testid="download" disabled={!!busy}
              onClick={() => act("download", async () => { const r = await api<{ url: string }>(`/projects/${id}/download`); window.open(r.url, "_blank", "noopener"); })}>
              {t("download")}
            </button>
            {p.sheet_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={p.sheet_url} alt="Final frames" className="mt-4 w-full rounded-lg border border-line" />
            )}
          </div>
        )}
        <section className="card mt-4">
          <h2 className="font-semibold">{t("preview")}</h2>
          <p className="hint">{t("previewHint")}</p>
          {p.preview_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={p.preview_url} alt="Storyboard preview, one frame per scene" className="mt-3 w-full rounded-lg border border-line" data-testid="contact-sheet" />
          ) : (
            <p className="mt-3 text-sm text-ink-2">{t("noPreviewYet")}</p>
          )}
          {p.status === "preview_ready" && (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button type="button" className="btn-primary" data-testid="render" disabled={!!busy} onClick={() => act("render", () => api(`/projects/${id}/render`, { method: "POST" }))}>
                {busy === "render" ? t("rendering") : t("render")}
              </button>
              {p.credits_needed != null && <span className="text-sm text-ink-2">{t("renderCost", { n: p.credits_needed })}</span>}
            </div>
          )}
        </section>
        {p.editable_fields && p.editable_fields.length > 0 && (
          <TextsForm projectId={id} fields={p.editable_fields as { path: string; label: string; value: string; maxLen: number }[]} disabled={p.status !== "preview_ready"} onApplied={load} />
        )}
        {p.assets.length > 0 && <AssetPanel project={p} disabled={p.status !== "preview_ready"} onApplied={load} />}
      </div>
      <aside className="space-y-4">
        <section className="card">
          <h2 className="font-semibold">{t("timeline")}</h2>
          <Timeline status={status} progress={progress} />
        </section>
        <section className="card text-sm">
          <h2 className="font-semibold">{t("details")}</h2>
          <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
            <dt className="text-ink-2">{t("template")}</dt><dd>{p.template}</dd>
            <dt className="text-ink-2">{t("language")}</dt><dd>{p.detected_lang || p.lang || "—"}</dd>
            <dt className="text-ink-2">{t("size")}</dt><dd>{p.size_w}×{p.size_h}</dd>
            <dt className="text-ink-2">{t("duration")}</dt><dd>{fmtDuration(p.duration_s, locale)}</dd>
            <dt className="text-ink-2">{t("planner")}</dt><dd>{p.planner === "fallback" ? t("plannerFallback") : p.planner ? t("plannerLlm") : "—"}</dd>
            {p.llm_cost_usd > 0 && <><dt className="text-ink-2">{t("cost")}</dt><dd>${p.llm_cost_usd.toFixed(4)}</dd></>}
          </dl>
          {qaIssues.length > 0 && <p className="hint">{t("qaIssues")}: {qaIssues.join("; ")}</p>}
          <button type="button" className="btn-danger mt-4 w-full" disabled={!!busy}
            onClick={() => { if (confirm(t("deleteConfirm"))) act("delete", async () => { await api(`/projects/${id}`, { method: "DELETE" }); router.push("/app"); }); }}>
            {t("delete")}
          </button>
        </section>
        {p.words && p.words.length > 0 && (
          <details className="card text-sm">
            <summary className="cursor-pointer font-semibold">{t("transcript")}</summary>
            <p className="mt-2 leading-relaxed text-ink-2">{(p.words as { w: string }[]).map((w) => w.w).join(" ")}</p>
          </details>
        )}
      </aside>
      {error instanceof ApiFailure && null}
    </div>
  );
}
