"use client";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { ErrorText, Field } from "@/components/ui";
import { usePathname, useRouter } from "@/i18n/navigation";
import { api } from "@/lib/api";

const PALETTE_KEYS = ["accent", "bg", "text"] as const;

export default function Settings() {
  const t = useTranslations("settings");
  const ta = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const { me, refresh, logout } = useAuth();
  const [palette, setPalette] = useState<Record<string, string>>({});
  const [font, setFont] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [password, setPassword] = useState("");
  useEffect(() => {
    if (me?.brand_kit) {
      setPalette(me.brand_kit.palette as Record<string, string>);
      setFont((me.brand_kit.fonts as Record<string, string>).display || "");
    }
  }, [me]);
  const canBrand = !!me?.plan.brand_kit;
  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <section className="card mt-4">
        <h2 className="font-semibold">{t("locale")}</h2>
        <select className="input mt-2 max-w-xs" value={locale} aria-label={ta("locale")} onChange={async (e) => { await api("/me", { method: "PATCH", json: { locale: e.target.value } }); router.replace(pathname, { locale: e.target.value as "en" | "ar" }); }}>
          <option value="en">English</option>
          <option value="ar">العربية</option>
        </select>
      </section>
      <section className="card mt-4">
        <h2 className="font-semibold">{t("brandKit")}</h2>
        <p className="hint">{t("brandKitHint")}</p>
        <form className="mt-3" onSubmit={async (e) => { e.preventDefault(); setError(null); setSaved(false); try { await api("/me/brand-kit", { method: "PUT", json: { palette: Object.fromEntries(Object.entries(palette).filter(([, v]) => v)), fonts: font ? { display: font } : {} } }); await refresh(); setSaved(true); } catch (err) { setError(err); } }}>
          <fieldset disabled={!canBrand} className="grid gap-3 sm:grid-cols-3">
            <legend className="label">{t("palette")}</legend>
            {PALETTE_KEYS.map((k) => (
              <label key={k} className="text-sm">
                <span className="mb-1 block capitalize">{k}</span>
                <input type="color" className="h-10 w-full rounded border border-line" value={palette[k] || "#2f3cf0"} onChange={(e) => setPalette({ ...palette, [k]: e.target.value })} aria-label={k} />
              </label>
            ))}
          </fieldset>
          <Field label={t("displayFont")} htmlFor="font"><input id="font" className="input" disabled={!canBrand} value={font} onChange={(e) => setFont(e.target.value)} placeholder="Cairo" /></Field>
          <ErrorText error={error} />
          <button type="submit" className="btn-primary" disabled={!canBrand}>{t("save")}</button>
          {saved && <span className="ms-3 text-sm text-green-300">{t("saved")}</span>}
        </form>
      </section>
      <section className="card mt-4 border-red-500/30">
        <h2 className="font-semibold text-red-300">{t("danger")}</h2>
        <p className="hint">{t("deleteText")}</p>
        <form className="mt-3 flex flex-wrap items-end gap-3" onSubmit={async (e) => { e.preventDefault(); setError(null); try { await api("/me", { method: "DELETE", json: { password } }); await logout(); router.push("/"); } catch (err) { setError(err); } }}>
          <div className="flex-1"><label className="label" htmlFor="pw">{ta("password")}</label><input id="pw" type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
          <button type="submit" className="btn-danger">{t("deleteAccount")}</button>
        </form>
      </section>
    </div>
  );
}
