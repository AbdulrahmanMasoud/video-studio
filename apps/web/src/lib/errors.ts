/** error_code → translation key (messages.errors.*). Unknown codes fall back to the server message. */
export const KNOWN_ERRORS = [
  "bad_credentials", "email_taken", "csrf", "unauthenticated", "email_unverified", "token_invalid", "rate_limited", "too_many_jobs",
  "insufficient_credits", "plan_required", "template_disabled", "unknown_template", "input_required", "tts_disabled", "input_missing",
  "file_too_large", "unsupported_type", "too_many_assets", "upload_missing", "asset_in_use", "not_preview_ready", "not_done", "not_failed",
  "input_too_long", "input_invalid", "asset_invalid", "plan_failed", "plan_invalid", "llm_unavailable", "timeout", "worker_crash", "engine_error",
  "cancelled", "validation_error", "not_found", "project_busy", "nothing_to_do", "invalid_slot", "unknown_asset", "invalid_word", "intake_missing",
] as const;
export type KnownError = (typeof KNOWN_ERRORS)[number];
export const isKnownError = (code: string): code is KnownError => (KNOWN_ERRORS as readonly string[]).includes(code);
