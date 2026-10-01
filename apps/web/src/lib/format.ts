export function fmtDuration(seconds: number | null | undefined, locale: string): string {
  if (!seconds && seconds !== 0) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return new Intl.NumberFormat(locale).format(m) + ":" + String(s).padStart(2, "0");
}

export function fmtDate(iso: string, locale: string): string {
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
}

export function fmtMoney(usd: number, locale: string): string {
  return new Intl.NumberFormat(locale, { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(usd);
}
