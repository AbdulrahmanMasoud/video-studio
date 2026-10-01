"use client";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { api } from "@/lib/api";
import { ErrorText, Field } from "@/components/ui";

export default function Forgot() {
  const t = useTranslations("auth");
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<unknown>(null);
  return (
    <div className="mx-auto max-w-md py-8">
      <h1 className="text-2xl font-bold">{t("forgotTitle")}</h1>
      <p className="mt-1 text-sm text-ink/70">{t("forgotText")}</p>
      <form className="card mt-4" onSubmit={async (e) => { e.preventDefault(); setError(null); try { await api("/auth/forgot", { method: "POST", json: { email } }); setSent(true); } catch (err) { setError(err); } }}>
        <Field label={t("email")} htmlFor="email"><input id="email" className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
        <ErrorText error={error} />
        {sent ? <p className="text-sm font-semibold text-green-700">{t("forgotSent")}</p> : <button className="btn-primary w-full" type="submit">{t("forgotSend")}</button>}
      </form>
    </div>
  );
}
