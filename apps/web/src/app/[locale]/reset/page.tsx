"use client";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { api } from "@/lib/api";
import { Link } from "@/i18n/navigation";
import { ErrorText, Field } from "@/components/ui";

function ResetForm() {
  const t = useTranslations("auth");
  const token = useSearchParams().get("token") || "";
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<unknown>(null);
  return (
    <form className="card mt-4" onSubmit={async (e) => { e.preventDefault(); setError(null); try { await api("/auth/reset", { method: "POST", json: { token, password } }); setDone(true); } catch (err) { setError(err); } }}>
      <Field label={t("newPassword")} htmlFor="password" hint={t("passwordHint")}><input id="password" className="input" type="password" minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
      <ErrorText error={error} />
      {done ? <p className="text-sm font-semibold text-green-300">{t("resetDone")} <Link href="/login" className="underline">{t("login")}</Link></p> : <button className="btn-primary w-full" type="submit">{t("resetTitle")}</button>}
    </form>
  );
}

export default function Reset() {
  const t = useTranslations("auth");
  return (
    <div className="mx-auto max-w-md py-8">
      <h1 className="text-2xl font-bold">{t("resetTitle")}</h1>
      <Suspense><ResetForm /></Suspense>
    </div>
  );
}
