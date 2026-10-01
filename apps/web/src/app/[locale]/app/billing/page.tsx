"use client";
import { useTranslations } from "next-intl";
import { useAuth } from "@/components/auth-provider";
import { PlansGrid } from "@/components/plans-grid";
import { api } from "@/lib/api";

export default function Billing() {
  const t = useTranslations("billing");
  const { me } = useAuth();
  return (
    <div>
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      {me && (
        <div className="card mt-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-ink/60">{t("current")}</p>
            <p className="text-xl font-bold capitalize">{me.plan.name}</p>
          </div>
          <div>
            <p className="text-sm text-ink/60">{t("credits")}</p>
            <p className="text-xl font-bold" data-testid="credits">{me.user.credits}</p>
          </div>
          <button type="button" className="btn-secondary" onClick={async () => { const r = await api<{ url: string }>("/billing/portal"); window.location.href = r.url; }}>{t("portal")}</button>
          <p className="w-full text-xs text-ink/60">{t("renews")}</p>
        </div>
      )}
      <PlansGrid mode="billing" />
    </div>
  );
}
