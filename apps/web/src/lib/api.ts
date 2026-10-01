/** Typed fetch wrapper for the API behind /api (same origin). Cookies carry the session; mutating calls add the CSRF header. */
import type { components } from "./api-types";

export type ApiError = { error_code: string; message: string; status: number; errors?: unknown };

export class ApiFailure extends Error {
  constructor(public readonly error: ApiError) {
    super(error.message);
  }
}

function csrf(): string | null {
  if (typeof document === "undefined") return null;
  const m = document.cookie.match(/(?:^|; )vs_csrf=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

export async function api<T = unknown>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const headers = new Headers(init.headers || {});
  if (init.json !== undefined) headers.set("Content-Type", "application/json");
  const method = (init.method || "GET").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const t = csrf();
    if (t) headers.set("X-CSRF-Token", t);
  }
  const res = await fetch(`/api${path}`, { ...init, method, headers, credentials: "include", body: init.json !== undefined ? JSON.stringify(init.json) : init.body });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { error_code: "bad_response", message: text.slice(0, 200) };
  }
  if (!res.ok) {
    const d = (data || {}) as Partial<ApiError>;
    throw new ApiFailure({ error_code: d.error_code || "http_error", message: d.message || res.statusText, status: res.status, errors: d.errors });
  }
  return data as T;
}

// Types from the generated OpenAPI document (npm run gen:api).
type S = components["schemas"];
export type Me = S["MeOut"];
export type Catalog = S["CatalogOut"];
export type Template = S["TemplateOut"];
export type Project = S["ProjectDetailOut"];
export type ProjectSummary = S["ProjectOut"];
export type Asset = S["AssetOut"];
export type Plan = S["PlanOut"];
export type Presign = S["PresignOut"];
export type AuthOut = S["AuthOut"];
