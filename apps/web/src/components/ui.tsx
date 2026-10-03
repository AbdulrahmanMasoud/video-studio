"use client";
import { useTranslations } from "next-intl";
import { ApiFailure } from "@/lib/api";
import { isKnownError } from "@/lib/errors";

export function ErrorText({ error }: { error: unknown }) {
  const t = useTranslations("errors");
  const tc = useTranslations("common");
  if (!error) return null;
  let msg = tc("error");
  if (error instanceof ApiFailure) msg = isKnownError(error.error.error_code) ? t(error.error.error_code) : error.error.message;
  else if (error instanceof Error) msg = error.message;
  return <p role="alert" className="mt-2 rounded-md border border-red-500/30 bg-red-500/100/10 px-3 py-2 text-sm text-red-300">{msg}</p>;
}

export function Spinner({ label }: { label?: string }) {
  const tc = useTranslations("common");
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-ink-2">
      <span aria-hidden className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-brand border-t-transparent" />
      {label ?? tc("loading")}
    </span>
  );
}

export function StatusChip({ status }: { status: string }) {
  const t = useTranslations("status");
  const cls = status === "done" ? "chip-ok" : status === "failed" ? "chip-err" : status === "preview_ready" ? "chip-warn" : "chip-info";
  const key = (["created", "uploading", "queued_transcribe", "transcribing", "editing", "planning", "preview_ready", "queued_render", "rendering", "done", "failed"] as const).find((k) => k === status);
  return <span className={`chip ${cls}`}>{key ? t(key) : status}</span>;
}

export function Field({ label, hint, children, htmlFor }: { label: string; hint?: string; children: React.ReactNode; htmlFor?: string }) {
  return (
    <div className="mb-4">
      <label className="label" htmlFor={htmlFor}>{label}</label>
      {children}
      {hint && <p className="hint">{hint}</p>}
    </div>
  );
}
