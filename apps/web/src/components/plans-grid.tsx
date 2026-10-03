"use client";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { api, type Plan } from "@/lib/api";
import { fmtMoney } from "@/lib/format";
import { Link, useRouter } from "@/i18n/navigation";
import { useAuth } from "./auth-provider";
import { ErrorText, Spinner } from "./ui";

export function PlansGrid({ mode }: { mode: "public" | "billing" }) {
  const t = useTranslations("billing");
  const locale = useLocale();
  const router = useRouter();
  const { me, refresh } = useAuth();
  const [plans, setPlans] = useState<Plan[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState<string | null>(null);
  useEffect(() => {
    api<Plan[]>("/billing/plans").then(setPlans).catch(setError);
  }, []);
  const choose = async (plan: string) => {
    setBusy(plan);
    setError(null);
    try {
      const r = await api<{ url: string }>("/billing/checkout", { method: "POST", json: { plan } });
      if (r.url.includes("mock_checkout=")) {
        router.push(`/app/billing?mock_checkout=${plan}`);
      } else {
        window.location.href = r.url;
      }
    } catch (e) {
      setError(e);
    } finally {
      setBusy(null);
    }
  };
  if (!plans) return <div className="py-8"><Spinner /></div>;
  const names = { free: t("free"), starter: t("starter"), pro: t("pro"), agency: t("agency") } as Record<string, string>;
  return (
    <div className="mt-6">
      <ErrorText error={error} />
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {plans.map((p) => {
          const current = me?.user.plan === p.name;
          return (
            <li key={p.name} className={`card flex flex-col ${current ? "border-brand" : ""} ${p.name === "pro" && !current ? "border-ink-3" : ""}`}>
              <h3 className="text-lg font-bold">{names[p.name] ?? p.name}</h3>
              <p className="display mt-1 text-3xl font-bold tabular-nums">{fmtMoney(p.price_usd, locale)}<span className="text-sm font-normal text-ink-2">{t("perMonth")}</span></p>
              <ul className="mt-3 flex-1 space-y-1 text-sm text-ink-2">
                <li>{t("features.credits", { n: p.credits })}</li>
                <li>{t("features.res", { res: p.max_res })}</li>
                <li>{p.watermark ? t("features.watermark") : t("features.noWatermark")}</li>
                <li>{p.templates === "all" ? t("features.all") : t("features.basic")}</li>
                {p.brand_kit && <li>{t("features.brandKit")}</li>}
                {p.priority_queue && <li>{t("features.priority")}</li>}
              </ul>
              <div className="mt-4">
                {current ? (
                  <span className="chip chip-warn">{t("currentPlan")}</span>
                ) : p.name === "free" ? (
                  !me && <Link href="/register" className="btn-secondary w-full">{t("choose", { plan: names[p.name] })}</Link>
                ) : me ? (
                  <button type="button" className="btn-primary w-full" disabled={busy === p.name} onClick={() => choose(p.name)}>{t("choose", { plan: names[p.name] })}</button>
                ) : (
                  <Link href="/register" className="btn-primary w-full">{t("choose", { plan: names[p.name] })}</Link>
                )}
              </div>
            </li>
          );
        })}
      </ul>
      {mode === "billing" && <MockCheckout onDone={refresh} />}
      <p className="mt-4 text-xs text-ink-2">{t("creditRule")}</p>
    </div>
  );
}

function MockCheckout({ onDone }: { onDone: () => Promise<unknown> }) {
  const t = useTranslations("billing");
  const router = useRouter();
  const [plan, setPlan] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    const p = new URLSearchParams(window.location.search).get("mock_checkout");
    setPlan(p);
  }, []);
  if (!plan) return null;
  const names = { free: t("free"), starter: t("starter"), pro: t("pro"), agency: t("agency") } as Record<string, string>;
  return (
    <div role="dialog" aria-labelledby="mock-title" className="card mt-6 border-brand/40">
      <h3 id="mock-title" className="font-bold">{t("mockTitle")}</h3>
      <p className="mt-1 text-sm">{t("mockText", { plan: names[plan] ?? plan })}</p>
      <ErrorText error={error} />
      {done ? (
        <p className="mt-2 text-sm font-semibold text-green-300">{t("mockDone")}</p>
      ) : (
        <button type="button" className="btn-primary mt-3" onClick={async () => { try { await api("/billing/mock/subscribe", { method: "POST", json: { plan } }); await onDone(); setDone(true); router.replace("/app/billing"); } catch (e) { setError(e); } }}>
          {t("mockConfirm")}
        </button>
      )}
    </div>
  );
}
