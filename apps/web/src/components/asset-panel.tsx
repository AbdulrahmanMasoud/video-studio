"use client";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { api, type Project } from "@/lib/api";
import { ErrorText } from "./ui";

type Slot = { path: string; asset: string | null };

export function AssetPanel({ project, disabled, onApplied }: { project: Project; disabled: boolean; onApplied: () => Promise<unknown> }) {
  const t = useTranslations("project");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [picker, setPicker] = useState<string | null>(null);
  const [insertAsset, setInsertAsset] = useState<string | null>(null);
  const [insertWord, setInsertWord] = useState(0);
  const [insertDur, setInsertDur] = useState(2);
  const slots = (project.asset_slots ?? []) as Slot[];
  const byName = Object.fromEntries(project.assets.map((a) => [a.name, a]));
  const ready = project.assets.filter((a) => a.status === "ready");
  const words = (project.words ?? []) as { w: string }[];
  const sceneOf = (path: string) => Number(/scenes\[(\d+)\]/.exec(path)?.[1] ?? 0) + 1;

  const apply = async (body: { changes?: { path: string; asset: string | null }[]; insert?: { asset: string; at_word: number; dur: number }[] }) => {
    setBusy(true);
    setError(null);
    try {
      await api(`/projects/${project.id}/asset-slots`, { method: "POST", json: body });
      setPicker(null);
      setInsertAsset(null);
      await onApplied();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card mt-4" data-testid="asset-panel">
      <h2 className="font-semibold">{t("assets")}</h2>
      <p className="hint">{t("assetsHint")}</p>
      <ErrorText error={error} />
      {busy && <p className="mt-2 text-sm text-ink-2" aria-live="polite">{t("applyingAssets")}</p>}
      <ul className="mt-3 space-y-2">
        {slots.map((s) => {
          const a = s.asset ? byName[s.asset] : null;
          return (
            <li key={s.path} className="flex flex-wrap items-center gap-3 rounded-lg border border-line p-2" data-testid={`slot-${s.path}`}>
              <span className="w-24 text-xs text-ink-2">{t("slot", { n: sceneOf(s.path) })}</span>
              {a?.thumbnail_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={a.thumbnail_url} alt="" className="h-12 w-12 rounded object-cover" />
              ) : (
                <span className="flex h-12 w-12 items-center justify-center rounded bg-surface-2 text-xs text-ink-3">—</span>
              )}
              <span className="flex-1 text-sm">{a ? `${a.original_name}${a.description ? " · " + a.description : ""}` : "—"}</span>
              {picker === s.path ? (
                <span className="flex flex-wrap items-center gap-2">
                  <select className="input w-auto" aria-label={t("choose")} defaultValue="" onChange={(e) => e.target.value && apply({ changes: [{ path: s.path, asset: e.target.value }] })} disabled={busy} data-testid={`picker-${s.path}`}>
                    <option value="">{t("choose")}</option>
                    {ready.filter((r) => r.name !== s.asset).map((r) => (<option key={r.name} value={r.name}>{r.original_name}{r.description ? ` · ${r.description}` : ""}</option>))}
                  </select>
                  <button type="button" className="btn-secondary" onClick={() => setPicker(null)}>{t("cancel")}</button>
                </span>
              ) : (
                <span className="flex gap-2">
                  <button type="button" className="btn-secondary" disabled={disabled || busy} onClick={() => setPicker(s.path)} data-testid={`swap-${s.path}`}>{t("swap")}</button>
                  {s.asset && <button type="button" className="btn-secondary" disabled={disabled || busy} onClick={() => apply({ changes: [{ path: s.path, asset: null }] })}>{t("remove")}</button>}
                </span>
              )}
            </li>
          );
        })}
      </ul>
      {project.unused_assets.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-semibold">{t("unused")}</h3>
          <ul className="mt-2 space-y-2">
            {project.unused_assets.map((name) => {
              const a = byName[name];
              return (
                <li key={name} className="flex flex-wrap items-center gap-3 rounded-lg border border-dashed border-line p-2" data-testid={`unused-${name}`}>
                  {a?.thumbnail_url && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={a.thumbnail_url} alt="" className="h-12 w-12 rounded object-cover" />
                  )}
                  <span className="flex-1 text-sm">{a?.original_name}{a?.description ? ` · ${a.description}` : ""}{a?.description_source === "ai" && <span className="ms-1 text-xs text-ink-3">({t("describedByAi")})</span>}</span>
                  {insertAsset === name ? (
                    <form className="flex flex-wrap items-end gap-2" onSubmit={(e) => { e.preventDefault(); apply({ insert: [{ asset: name, at_word: insertWord, dur: insertDur }] }); }}>
                      <label className="text-xs">{t("insertAt")}<select className="input mt-1" value={insertWord} onChange={(e) => setInsertWord(Number(e.target.value))}>{words.map((w, i) => (<option key={i} value={i}>{i + 1}. {w.w}</option>))}</select></label>
                      <label className="text-xs">{t("insertDuration")}<input type="number" className="input mt-1 w-24" min={1.5} max={15} step={0.5} value={insertDur} onChange={(e) => setInsertDur(Number(e.target.value))} /></label>
                      <button type="submit" className="btn-primary" disabled={busy}>{t("insertGo")}</button>
                      <button type="button" className="btn-secondary" onClick={() => setInsertAsset(null)}>{t("cancel")}</button>
                    </form>
                  ) : (
                    <button type="button" className="btn-secondary" disabled={disabled || busy || words.length === 0} onClick={() => setInsertAsset(name)}>{t("insert")}</button>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
      {project.assets.some((a) => a.status === "invalid") && (
        <ul className="mt-3 text-xs text-red-300">{project.assets.filter((a) => a.status === "invalid").map((a) => (<li key={a.id}>{a.original_name}: {t("invalidAsset")}</li>))}</ul>
      )}
    </section>
  );
}
