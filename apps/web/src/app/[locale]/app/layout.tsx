"use client";
import { useTranslations } from "next-intl";
import { useEffect } from "react";
import { useAuth } from "@/components/auth-provider";
import { Spinner } from "@/components/ui";
import { useRouter } from "@/i18n/navigation";
import { api } from "@/lib/api";
import { useState } from "react";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { me, loading } = useAuth();
  const router = useRouter();
  const t = useTranslations("auth");
  const [resent, setResent] = useState(false);
  useEffect(() => {
    if (!loading && !me) router.replace("/login");
  }, [loading, me, router]);
  if (loading || !me) return <div className="py-16 text-center"><Spinner /></div>;
  return (
    <div>
      {!me.user.email_verified && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-sm" role="status">
          <span>{t("verifyBanner", { email: me.user.email })}</span>
          <button type="button" className="btn-secondary" disabled={resent} onClick={async () => { await api("/auth/resend-verification", { method: "POST" }); setResent(true); }}>{resent ? t("resent") : t("resend")}</button>
        </div>
      )}
      {children}
    </div>
  );
}
