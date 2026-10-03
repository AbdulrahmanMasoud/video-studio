"use client";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { api } from "@/lib/api";
import { Link, useRouter } from "@/i18n/navigation";
import { useAuth } from "@/components/auth-provider";
import { ErrorText, Field } from "@/components/ui";

export default function Login() {
  const t = useTranslations("auth");
  const router = useRouter();
  const { refresh } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  return (
    <div className="mx-auto max-w-md py-8">
      <h1 className="text-2xl font-bold">{t("login")}</h1>
      <form className="card mt-4" onSubmit={async (e) => { e.preventDefault(); setBusy(true); setError(null); try { await api("/auth/login", { method: "POST", json: { email, password } }); await refresh(); router.push("/app"); } catch (err) { setError(err); } finally { setBusy(false); } }}>
        <Field label={t("email")} htmlFor="email"><input id="email" className="input" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
        <Field label={t("password")} htmlFor="password"><input id="password" className="input" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
        <ErrorText error={error} />
        <button className="btn-primary mt-2 w-full" disabled={busy} type="submit">{t("login")}</button>
        <p className="mt-4 text-center text-sm text-ink-2"><Link href="/forgot" className="underline">{t("forgot")}</Link></p>
        <p className="mt-2 text-center text-sm text-ink-2">{t("noAccount")} <Link href="/register" className="font-semibold text-brand underline">{t("register")}</Link></p>
      </form>
    </div>
  );
}
