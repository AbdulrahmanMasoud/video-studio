"use client";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { PlansGrid } from "@/components/plans-grid";
import { ErrorText } from "@/components/ui";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";

type Sub = { plan: string; credits: number; provider: string; status: string | null; subscription_plan: string | null; current_period_end: string | null; cancel_at_period_end: boolean };

export default function Billing() {
  const t = useTranslations("billing");
  const locale = useLocale();
  const { me, refresh } = useAuth();
  const [sub, setSub] = useState<Sub | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [success, setSuccess] = useState(false);
  useEffect(() => {
    api<Sub>("/billing/subscription").then(setSub).catch(setError);
    if (new URLSearchParams(window.location.search).get("checkout") === "success") {
      setSuccess(true);
      refresh();
    }
  }, [refresh, me?.user.plan]);
  const names = { free: t("free"), starter: t("starter"), pro: t("pro"), agency: t("agency") } as Record<string, string>;
  return (
    <div>
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      {success && <p role="status" className="mt-3 rounded-lg border border-green-300 bg-green-500/10 px-4 py-2 text-sm text-green-300">{t("checkoutSuccess")}</p>}
      <ErrorText error={error} />
      {me && (
        <div className="card mt-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-ink-2">{t("current")}</p>
            <p className="text-xl font-bold" data-testid="plan-name">{names[me.user.plan] ?? me.user.plan}</p>
            {sub?.current_period_end && (
              <p className="text-xs text-ink-2">{sub.cancel_at_period_end ? t("endsOn", { date: fmtDate(sub.current_period_end, locale) }) : t("renewsOn", { date: fmtDate(sub.current_period_end, locale) })}</p>
            )}
          </div>
          <div>
            <p className="text-sm text-ink-2">{t("credits")}</p>
            <p className="text-xl font-bold tabular-nums" data-testid="credits">{me.user.credits}</p>
          </div>
          {sub?.status && sub.status !== "expired" && (
            <button type="button" className="btn-secondary" onClick={async () => { try { const r = await api<{ url: string }>("/billing/portal"); window.location.href = r.url; } catch (e) { setError(e); } }}>{t("portal")}</button>
          )}
          <p className="w-full text-xs text-ink-2">{t("renews")}</p>
        </div>
      )}
      <PlansGrid mode="billing" />
    </div>
  );
}
