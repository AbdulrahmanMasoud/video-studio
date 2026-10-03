"use client";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ErrorText } from "./ui";

type Field = { path: string; label: string; value: string; maxLen: number };

export function TextsForm({ projectId, fields, disabled, onApplied }: { projectId: string; fields: Field[]; disabled: boolean; onApplied: () => Promise<unknown> }) {
  const t = useTranslations("project");
  const [values, setValues] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [applied, setApplied] = useState(false);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    setValues(Object.fromEntries(fields.map((f) => [f.path, f.value])));
  }, [fields]);
  const changed = fields.filter((f) => values[f.path] !== undefined && values[f.path] !== f.value);
  return (
    <section className="card mt-4">
      <h2 className="font-semibold">{t("texts")}</h2>
      <p className="hint">{t("textsHint")}</p>
      <form className="mt-3 grid gap-3 sm:grid-cols-2" onSubmit={async (e) => { e.preventDefault(); setBusy(true); setError(null); setApplied(false); try { await api(`/projects/${projectId}/texts`, { method: "POST", json: { fields: changed.map((f) => ({ path: f.path, value: values[f.path] })) } }); setApplied(true); await onApplied(); } catch (err) { setError(err); } finally { setBusy(false); } }}>
        {fields.map((f) => (
          <label key={f.path} className="text-sm">
            <span className="mb-1 block text-xs text-ink-2">{f.label}</span>
            <input className="input" data-testid={`field-${f.path}`} maxLength={f.maxLen} value={values[f.path] ?? ""} disabled={disabled || busy} onChange={(e) => setValues({ ...values, [f.path]: e.target.value })} />
          </label>
        ))}
        <div className="sm:col-span-2">
          <ErrorText error={error} />
          <button type="submit" className="btn-primary" data-testid="apply-texts" disabled={disabled || busy || changed.length === 0}>{busy ? t("saving") : t("saveTexts")}</button>
          {applied && <span className="ms-3 text-sm text-green-300">{t("textsApplied")}</span>}
        </div>
      </form>
    </section>
  );
}
