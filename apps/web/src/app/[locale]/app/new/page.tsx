"use client";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { RequestTemplateDialog } from "@/components/request-template";
import { ErrorText, Field, Spinner } from "@/components/ui";
import { useRouter } from "@/i18n/navigation";
import { api, type Catalog, type Template } from "@/lib/api";
import { fmtDuration } from "@/lib/format";
import { mediaDuration, presignAsset, presignInput, uploadToS3 } from "@/lib/upload";

type PendingAsset = { file: File; description: string; progress: number; done?: boolean; error?: string };
const STEPS = ["source", "format", "template", "assets", "brief"] as const;
const MAX_INPUT_MB = 200;
const MAX_SECONDS = 600;

export default function NewProject() {
  const t = useTranslations("wizard");
  const tt = useTranslations("templates");
  const locale = useLocale();
  const router = useRouter();
  const { me } = useAuth();
  const [step, setStep] = useState(0);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState<unknown>(null);
  // source
  const [mode, setMode] = useState<"upload" | "script">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [uploadPct, setUploadPct] = useState<number | null>(null);
  const [inputKey, setInputKey] = useState<string | null>(null);
  const [script, setScript] = useState("");
  // format
  const [lang, setLang] = useState("");
  const [size, setSize] = useState("9:16");
  const [customSize, setCustomSize] = useState("1080x1920");
  const [platform, setPlatform] = useState("tiktok");
  // template
  const [template, setTemplate] = useState<string | null>(null);
  const [requestOpen, setRequestOpen] = useState(false);
  // assets + brief
  const [assets, setAssets] = useState<PendingAsset[]>([]);
  const [title, setTitle] = useState("");
  const [keyPoints, setKeyPoints] = useState("");
  const [accent, setAccent] = useState("");
  const [bg, setBg] = useState("");
  const [creating, setCreating] = useState<string | null>(null);

  useEffect(() => {
    api<Catalog>("/templates").then(setCatalog).catch(setError);
  }, []);
  const ttsEnabled = !!me?.features.tts;
  const sizes = useMemo(() => catalog?.sizes ?? [], [catalog]);

  const pickFile = async (f: File | null) => {
    setFileError(null);
    setInputKey(null);
    setUploadPct(null);
    if (!f) return setFile(null);
    if (!(f.type.startsWith("audio/") || f.type.startsWith("video/"))) return setFileError(t("badType"));
    if (f.size > MAX_INPUT_MB * 1024 * 1024) return setFileError(t("tooLarge"));
    const dur = await mediaDuration(f);
    if (dur && dur > MAX_SECONDS) return setFileError(t("tooLong", { duration: fmtDuration(dur, locale) }));
    setFile(f);
    try {
      const post = await presignInput(f);
      setUploadPct(0);
      await uploadToS3(post, f, (p) => setUploadPct(Math.round(p * 100)));
      setUploadPct(100);
      setInputKey(post.key);
    } catch (e) {
      setFileError(e instanceof Error ? e.message : String(e));
    }
  };

  const canNext = () => {
    if (step === 0) return mode === "upload" ? !!inputKey : script.trim().length > 20;
    if (step === 2) return !!template;
    return true;
  };

  const create = async () => {
    setCreating(t("creating"));
    setError(null);
    try {
      const brief: Record<string, unknown> = {};
      if (title.trim()) brief.title = title.trim();
      if (keyPoints.trim()) brief.key_points = keyPoints.split("\n").map((s) => s.trim()).filter(Boolean);
      if (accent || bg) brief.brand_colors = { ...(accent ? { accent } : {}), ...(bg ? { bg } : {}) };
      const body = { title: title.trim() || file?.name || "Untitled", template, size: size === "custom" ? customSize : size, platform, lang: lang || null, brief,
        ...(mode === "upload" ? { input_key: inputKey } : { script }) };
      const r = await api<{ project: { id: string } }>("/projects", { method: "POST", json: body });
      const pid = r.project.id;
      // assets upload right after creation (the worker downloads them when the job starts)
      for (const a of assets) {
        try {
          const post = await presignAsset(pid, a.file);
          await uploadToS3(post, a.file, (p) => setAssets((prev) => prev.map((x) => (x === a ? { ...x, progress: p } : x))));
          await api(`/projects/${pid}/assets`, { method: "POST", json: { asset_id: post.asset_id, description: a.description || null } });
        } catch (e) {
          setAssets((prev) => prev.map((x) => (x === a ? { ...x, error: String(e) } : x)));
        }
      }
      router.push(`/app/projects/${pid}`);
    } catch (e) {
      setError(e);
      setCreating(null);
    }
  };

  if (!catalog) return <div className="py-10"><Spinner /></div>;
  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <ol className="mt-3 flex flex-wrap gap-2 text-xs" aria-label={t("title")}>
        {STEPS.map((s, i) => (
          <li key={s} className={`chip ${i === step ? "bg-brand text-white" : i < step ? "bg-brand/10 text-brand" : "bg-ink/10 text-ink/60"}`} aria-current={i === step ? "step" : undefined}>{i + 1}. {t(`steps.${s}`)}</li>
        ))}
      </ol>
      <div className="card mt-4">
        {step === 0 && (
          <div>
            <h2 className="font-semibold">{t("sourceTitle")}</h2>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <button type="button" className={`rounded-lg border p-4 text-start ${mode === "upload" ? "border-brand bg-brand/5" : "border-ink/15"}`} onClick={() => setMode("upload")} aria-pressed={mode === "upload"}>
                <span className="font-semibold">{t("sourceUpload")}</span><span className="hint">{t("sourceUploadHint")}</span>
              </button>
              <button type="button" className={`rounded-lg border p-4 text-start ${mode === "script" ? "border-brand bg-brand/5" : "border-ink/15"}`} onClick={() => setMode("script")} disabled={!ttsEnabled} aria-pressed={mode === "script"}>
                <span className="font-semibold">{t("sourceScript")}</span><span className="hint">{t("sourceScriptHint")}</span>
              </button>
            </div>
            {mode === "upload" ? (
              <div className="mt-4">
                <label htmlFor="input-file" className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-ink/20 p-8 text-sm text-ink/70 hover:border-brand"
                  onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); pickFile(e.dataTransfer.files[0] ?? null); }}>
                  {file ? t("chosen", { name: file.name, size: `${(file.size / 1e6).toFixed(1)} MB` }) : t("dropHere")}
                  <input id="input-file" data-testid="input-file" type="file" accept="audio/*,video/*" className="sr-only" onChange={(e) => pickFile(e.target.files?.[0] ?? null)} />
                </label>
                {uploadPct !== null && <p className="mt-2 text-sm" aria-live="polite">{inputKey ? t("uploaded") : t("uploading", { pct: uploadPct })}</p>}
                {fileError && <p role="alert" className="mt-2 text-sm text-red-700">{fileError}</p>}
              </div>
            ) : (
              <Field label={t("scriptLabel")} htmlFor="script" hint={t("scriptHint")}><textarea id="script" className="input min-h-40" value={script} onChange={(e) => setScript(e.target.value)} /></Field>
            )}
          </div>
        )}
        {step === 1 && (
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={t("language")} htmlFor="lang">
              <select id="lang" className="input" value={lang} onChange={(e) => setLang(e.target.value)}>
                <option value="">{t("languageAuto")}</option>
                {catalog.languages.map((l) => (<option key={l.code} value={l.code}>{l.name}</option>))}
              </select>
            </Field>
            <Field label={t("size")} htmlFor="size">
              <select id="size" className="input" value={size} onChange={(e) => setSize(e.target.value)}>
                {sizes.map((s) => (<option key={s.id} value={s.id}>{s.label}</option>))}
              </select>
              {size === "custom" && <input className="input mt-2" aria-label={t("customSize")} value={customSize} onChange={(e) => setCustomSize(e.target.value)} placeholder="1080x1920" />}
            </Field>
            <Field label={t("platform")} htmlFor="platform">
              <select id="platform" className="input" value={platform} onChange={(e) => setPlatform(e.target.value)}>
                {catalog.platforms.map((p) => (<option key={p} value={p}>{p === "none" ? t("platformNone") : p}</option>))}
              </select>
            </Field>
          </div>
        )}
        {step === 2 && (
          <div>
            <div className="flex items-center justify-between"><h2 className="font-semibold">{t("templateTitle")}</h2><button type="button" className="btn-secondary" onClick={() => setRequestOpen(true)}>{tt("requestTitle")}</button></div>
            <ul className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3" role="radiogroup" aria-label={t("templateTitle")}>
              {catalog.templates.map((tpl: Template) => (
                <li key={tpl.name}>
                  <button type="button" role="radio" aria-checked={template === tpl.name} disabled={!tpl.available} data-testid={`template-${tpl.name}`}
                    className={`w-full rounded-lg border p-2 text-start ${template === tpl.name ? "border-brand ring-2 ring-brand" : "border-ink/15"} disabled:opacity-50`} onClick={() => setTemplate(tpl.name)}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={`/previews/${tpl.name}.jpg`} alt="" className="aspect-[9/16] w-full rounded object-cover" />
                    <span className="mt-1 block text-sm font-semibold">{tpl.title}</span>
                    <span className="block text-xs text-ink/60">{tpl.available ? tpl.summary : tt("needsPlan", { plan: tpl.tier_required })}</span>
                  </button>
                </li>
              ))}
            </ul>
            <RequestTemplateDialog open={requestOpen} onClose={() => setRequestOpen(false)} />
          </div>
        )}
        {step === 3 && (
          <div>
            <h2 className="font-semibold">{t("assetsTitle")}</h2>
            <p className="hint">{t("assetsHint")}</p>
            <label className="btn-secondary mt-3 cursor-pointer">
              {t("addAssets")}
              <input data-testid="asset-files" type="file" multiple accept="image/jpeg,image/png,image/webp,image/heic,video/mp4,video/quicktime" className="sr-only"
                onChange={(e) => setAssets([...assets, ...Array.from(e.target.files ?? []).slice(0, 20 - assets.length).map((f) => ({ file: f, description: "", progress: 0 }))])} />
            </label>
            <p className="hint">{t("assetsAfterCreate")}</p>
            <ul className="mt-3 space-y-2">
              {assets.map((a, i) => (
                <li key={i} className="flex flex-wrap items-center gap-3 rounded-lg border border-ink/10 p-2">
                  <span className="min-w-40 truncate text-sm">{a.file.name}</span>
                  <input className="input flex-1" placeholder={t("assetDescription")} value={a.description} aria-label={t("assetDescription")} onChange={(e) => setAssets(assets.map((x, j) => (j === i ? { ...x, description: e.target.value } : x)))} />
                  <button type="button" className="btn-secondary" onClick={() => setAssets(assets.filter((_, j) => j !== i))}>{t("assetRemove")}</button>
                </li>
              ))}
            </ul>
          </div>
        )}
        {step === 4 && (
          <div>
            <h2 className="font-semibold">{t("briefTitle")}</h2>
            <Field label={t("videoTitle")} htmlFor="title"><input id="title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} /></Field>
            <Field label={t("keyPoints")} htmlFor="kp" hint={t("keyPointsHint")}><textarea id="kp" className="input min-h-24" value={keyPoints} onChange={(e) => setKeyPoints(e.target.value)} /></Field>
            <fieldset className="grid gap-3 sm:grid-cols-2"><legend className="label">{t("brandColors")}</legend>
              <label className="text-sm">{t("accent")}<input type="text" className="input" placeholder="#FFD43B" value={accent} onChange={(e) => setAccent(e.target.value)} /></label>
              <label className="text-sm">{t("background")}<input type="text" className="input" placeholder="#101820" value={bg} onChange={(e) => setBg(e.target.value)} /></label>
            </fieldset>
            <div className="mt-4 rounded-lg bg-ink/5 p-3 text-sm">
              <strong>{t("summary")}:</strong> {mode === "upload" ? file?.name : t("sourceScript")} · {lang || t("languageAuto")} · {size === "custom" ? customSize : size} · {platform} · {template} · {assets.length} {t("steps.assets").toLowerCase()}
            </div>
          </div>
        )}
        <ErrorText error={error} />
        <div className="mt-6 flex justify-between">
          <button type="button" className="btn-secondary" disabled={step === 0} onClick={() => setStep(step - 1)}>{t("back")}</button>
          {step < STEPS.length - 1 ? (
            <button type="button" className="btn-primary" data-testid="wizard-next" disabled={!canNext()} onClick={() => setStep(step + 1)}>{t("next")}</button>
          ) : (
            <button type="button" className="btn-primary" data-testid="wizard-create" disabled={!!creating || !template} onClick={create}>{creating ?? t("create")}</button>
          )}
        </div>
        {step === 0 && !canNext() && <p className="hint">{t("requiredSource")}</p>}
      </div>
    </div>
  );
}
