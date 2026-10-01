"use client";
import { useTranslations } from "next-intl";
import { STATUS_ORDER } from "@/lib/status";

export function Timeline({ status, progress }: { status: string; progress: number }) {
  const t = useTranslations("status");
  const idx = STATUS_ORDER.indexOf(status as (typeof STATUS_ORDER)[number]);
  const shown = STATUS_ORDER.filter((s) => s !== "created");
  return (
    <ol className="mt-2 space-y-1 text-sm">
      {shown.map((s) => {
        const i = STATUS_ORDER.indexOf(s);
        const state = status === "failed" ? (i < idx ? "done" : "todo") : i < idx ? "done" : i === idx ? "current" : "todo";
        return (
          <li key={s} className="flex items-center gap-2">
            <span aria-hidden className={`inline-block h-2.5 w-2.5 rounded-full ${state === "done" ? "bg-green-500" : state === "current" ? "bg-brand animate-pulse" : "bg-ink/15"}`} />
            <span className={state === "todo" ? "text-ink/50" : ""}>{t(s)}</span>
          </li>
        );
      })}
      <li className="mt-2 h-2 w-full overflow-hidden rounded bg-ink/10" aria-hidden><div className="h-full bg-brand transition-all" style={{ width: `${progress}%` }} /></li>
    </ol>
  );
}
