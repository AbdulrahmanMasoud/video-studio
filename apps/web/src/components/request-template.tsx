"use client";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { api } from "@/lib/api";
import { ErrorText, Field } from "./ui";

export function RequestTemplateDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const t = useTranslations("templates");
  const tc = useTranslations("common");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<unknown>(null);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg/70 p-4" role="dialog" aria-modal="true" aria-labelledby="req-title">
      <div className="card w-full max-w-lg">
        <h2 id="req-title" className="text-lg font-bold">{t("requestTitle")}</h2>
        <p className="hint">{t("requestText")}</p>
        {done ? (
          <p className="mt-3 text-sm font-semibold text-green-300">{t("requestThanks")}</p>
        ) : (
          <form className="mt-3" onSubmit={async (e) => { e.preventDefault(); setError(null); try { await api("/template-requests", { method: "POST", json: { description, example_url: url || null } }); setDone(true); } catch (err) { setError(err); } }}>
            <Field label={t("requestDescription")} htmlFor="req-desc"><textarea id="req-desc" className="input min-h-28" minLength={10} required value={description} onChange={(e) => setDescription(e.target.value)} /></Field>
            <Field label={t("requestUrl")} htmlFor="req-url"><input id="req-url" className="input" type="url" value={url} onChange={(e) => setUrl(e.target.value)} /></Field>
            <ErrorText error={error} />
            <div className="flex justify-end gap-2"><button type="button" className="btn-secondary" onClick={onClose}>{tc("close")}</button><button type="submit" className="btn-primary">{t("requestSend")}</button></div>
          </form>
        )}
        {done && <div className="mt-3 flex justify-end"><button type="button" className="btn-secondary" onClick={onClose}>{tc("close")}</button></div>}
      </div>
    </div>
  );
}
