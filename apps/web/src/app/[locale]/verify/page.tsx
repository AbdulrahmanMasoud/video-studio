"use client";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Link } from "@/i18n/navigation";
import { useAuth } from "@/components/auth-provider";

function VerifyInner() {
  const t = useTranslations("auth");
  const token = useSearchParams().get("token") || "";
  const { refresh } = useAuth();
  const [state, setState] = useState<"verifying" | "ok" | "failed">("verifying");
  useEffect(() => {
    if (!token) { setState("failed"); return; }
    api("/auth/verify", { method: "POST", json: { token } }).then(async () => { setState("ok"); await refresh(); }).catch(() => setState("failed"));
  }, [token, refresh]);
  return (
    <div className="card mt-4" role="status">
      {state === "verifying" && <p>{t("verifying")}</p>}
      {state === "ok" && <p className="font-semibold text-green-700">{t("verified")} <Link href="/app" className="underline">→</Link></p>}
      {state === "failed" && <p className="text-red-700">{t("verifyFailed")}</p>}
    </div>
  );
}

export default function Verify() {
  const t = useTranslations("auth");
  return (
    <div className="mx-auto max-w-md py-8">
      <h1 className="text-2xl font-bold">{t("verifyTitle")}</h1>
      <Suspense><VerifyInner /></Suspense>
    </div>
  );
}
