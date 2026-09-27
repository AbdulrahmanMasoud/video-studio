"""Typed pipeline errors. `code` is stable and mapped to translated messages in the web app."""
from __future__ import annotations

# error codes raised by the engine CLI (vt.py die(..., error_code=...)) that are the user's fault: no retry
USER_ERROR_CODES = {"input_missing", "input_invalid", "input_too_long", "intake_missing", "asset_invalid", "tts_disabled", "tts_not_configured"}
# transient: retried once by the queue
TRANSIENT_CODES = {"timeout", "interrupted", "worker_crash"}


class PipelineError(Exception):
    def __init__(self, code: str, message: str, *, step: str | None = None, transient: bool | None = None, detail: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.step = step
        self.transient = (code in TRANSIENT_CODES) if transient is None else transient
        self.user_error = code in USER_ERROR_CODES
        self.detail = detail or {}

    def to_dict(self) -> dict:
        return {"error_code": self.code, "message": self.message, "step": self.step, "transient": self.transient,
                "user_error": self.user_error, **({"detail": self.detail} if self.detail else {})}

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}" + (f" (step {self.step})" if self.step else "")
