"use client";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { api } from "@/lib/api";
import { Link, useRouter } from "@/i18n/navigation";
import { useAuth } from "@/components/auth-provider";
import { ErrorText, Field } from "@/components/ui";

export default function Register() {
  const t = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const { refresh } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  return (
    <div className="mx-auto max-w-md py-8">
      <h1 className="text-2xl font-bold">{t("register")}</h1>
      <form className="card mt-4" onSubmit={async (e) => { e.preventDefault(); setBusy(true); setError(null); try { await api("/auth/register", { method: "POST", json: { email, password, locale } }); await refresh(); router.push("/app"); } catch (err) { setError(err); } finally { setBusy(false); } }}>
        <Field label={t("email")} htmlFor="email"><input id="email" className="input" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
        <Field label={t("password")} htmlFor="password" hint={t("passwordHint")}><input id="password" className="input" type="password" autoComplete="new-password" minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
        <ErrorText error={error} />
        <button className="btn-primary mt-2 w-full" disabled={busy} type="submit">{t("register")}</button>
        <p className="mt-4 text-center text-sm text-ink-2">{t("haveAccount")} <Link href="/login" className="font-semibold text-brand underline">{t("login")}</Link></p>
      </form>
    </div>
  );
}
