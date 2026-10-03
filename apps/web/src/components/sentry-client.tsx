"use client";
import { useEffect } from "react";

/** Browser error reporting, only when NEXT_PUBLIC_SENTRY_DSN is set at build time. The SDK is loaded lazily so it never affects the bundle otherwise. */
export function SentryClient() {
  useEffect(() => {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (!dsn) return;
    import("@sentry/browser").then((Sentry) => Sentry.init({ dsn, environment: process.env.NODE_ENV, sendDefaultPii: false, tracesSampleRate: 0 })).catch(() => {});
  }, []);
  return null;
}
