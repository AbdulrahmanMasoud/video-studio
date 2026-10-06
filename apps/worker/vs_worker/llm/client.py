"""LLMClient: one class wrapping LiteLLM for every provider (Anthropic, OpenAI, Gemini, OpenRouter, Groq, Ollama).

    client = LLMClient(settings)
    resp = client.complete_json(system, messages, schema=None, model="anthropic/claude-sonnet-5", task="plan")
    resp.data  -> parsed JSON;  resp.tokens_in/out, resp.cost_usd, resp.model, resp.attempts

- JSON mode (`response_format`) is requested where the provider supports it; otherwise the prompt asks for JSON only.
- Output goes through fence stripping / balanced-object extraction; on failure one repair pass asks the model to
  return valid JSON. Vision input is a list of image paths turned into data URLs.
- Models in `settings.chain_for(model)` are tried in order when a call fails or times out.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .cost import estimate_cost
from .json_utils import JSONExtractError, extract_json
from .settings import LLMSettings, provider_of

JSON_ONLY = "Respond with a single JSON object and nothing else: no prose, no markdown fences."


class LLMError(Exception):
    def __init__(self, message: str, *, model: str | None = None, transient: bool = True, cause: Exception | None = None):
        super().__init__(message)
        self.model = model
        self.transient = transient
        self.cause = cause


@dataclass
class LLMResponse:
    data: Any
    raw: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    cost_source: str = "table"
    attempts: int = 1
    seconds: float = 0.0
    task: str = ""
    models_tried: list[str] = field(default_factory=list)

    def usage(self) -> dict:
        return {"task": self.task, "model": self.model, "tokens_in": self.tokens_in, "tokens_out": self.tokens_out, "cost_usd": self.cost_usd,
                "cost_source": self.cost_source, "attempts": self.attempts, "seconds": round(self.seconds, 2)}


def image_part(path: Path | str, detail: str = "low") -> dict:
    p = Path(path)
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": detail}}


class LLMClient:
    name = "litellm"

    def __init__(self, settings: LLMSettings | None = None, *, completion=None):
        self.settings = settings or LLMSettings.from_env()
        self._completion = completion  # injectable for tests; defaults to litellm.completion
        self.calls: list[dict] = []

    # ------------------------------------------------------------------ public
    def complete_json(self, system: str, messages: list[dict], *, schema: dict | None = None, model: str | None = None, max_tokens: int | None = None,
                      timeout: float | None = None, task: str = "", images: list[Path | str] | None = None, temperature: float = 0.2,
                      context: dict | None = None) -> LLMResponse:
        """`context` is accepted for interface parity with MockLLM (which uses it to shape canned answers) and ignored here."""
        del context
        model = model or self.settings.planner_model
        max_tokens = max_tokens or self.settings.max_tokens
        timeout = timeout or self.settings.timeout_s
        msgs: list[dict[str, Any]] = [{"role": "system", "content": system + "\n\n" + JSON_ONLY}] + [dict(m) for m in messages]
        if images:
            last = msgs[-1]
            content = last["content"] if isinstance(last["content"], list) else [{"type": "text", "text": str(last["content"])}]
            last["content"] = content + [image_part(p) for p in images]
        if schema:
            msgs[0]["content"] += "\nThe JSON must match this schema:\n" + json.dumps(schema, ensure_ascii=False)
        errors: list[str] = []
        tried: list[str] = []
        t0 = time.time()
        for m in self.settings.chain_for(model):
            tried.append(m)
            try:
                resp = self._call_with_repair(m, msgs, max_tokens, timeout, temperature, task)
                resp.seconds = time.time() - t0
                resp.models_tried = tried
                return resp
            except LLMError as e:
                errors.append(f"{m}: {e}")
                if not e.transient:
                    break
        raise LLMError("all models failed: " + " | ".join(errors), model=model, transient=True)

    # ------------------------------------------------------------------ internals
    def _call_with_repair(self, model: str, msgs: list[dict], max_tokens: int, timeout: float, temperature: float, task: str) -> LLMResponse:
        raw, usage, response = self._raw(model, msgs, max_tokens, timeout, temperature)
        attempts = 1
        try:
            data = extract_json(raw)
        except JSONExtractError as e:
            repair = msgs + [{"role": "assistant", "content": raw[:6000]},
                             {"role": "user", "content": f"That was not valid JSON ({e}). Return the same content as one valid JSON object only."}]
            raw2, usage2, response2 = self._raw(model, repair, max_tokens, timeout, 0.0)
            attempts = 2
            try:
                data = extract_json(raw2)
            except JSONExtractError as e2:
                raise LLMError(f"model returned invalid JSON twice: {e2}", model=model, transient=True) from e2
            raw, response = raw2, response2
            usage = {"in": usage["in"] + usage2["in"], "out": usage["out"] + usage2["out"]}
        cost, source = estimate_cost(model, usage["in"], usage["out"], response)
        r = LLMResponse(data=data, raw=raw, model=model, tokens_in=usage["in"], tokens_out=usage["out"], cost_usd=cost, cost_source=source,
                        attempts=attempts, task=task)
        self.calls.append(r.usage())
        return r

    def _raw(self, model: str, msgs: list[dict], max_tokens: int, timeout: float, temperature: float):
        completion = self._completion
        if completion is None:
            import litellm
            litellm.suppress_debug_info = True
            completion = litellm.completion
        kwargs: dict[str, Any] = {"model": model, "messages": msgs, "max_tokens": max_tokens, "timeout": timeout, "temperature": temperature, "num_retries": 1}
        if provider_of(model) == "ollama" and self.settings.ollama_base_url:
            kwargs["api_base"] = self.settings.ollama_base_url
        if self._supports_json_mode(model):
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = completion(**kwargs)
        except Exception as e:  # provider/network error: let the chain continue
            transient = not _is_auth_error(e)
            raise LLMError(f"{type(e).__name__}: {str(e)[:300]}", model=model, transient=transient, cause=e) from e
        try:
            raw = response.choices[0].message.content or ""
        except Exception as e:
            raise LLMError(f"unexpected response shape: {e}", model=model) from e
        u = getattr(response, "usage", None)
        usage = {"in": int(getattr(u, "prompt_tokens", 0) or 0), "out": int(getattr(u, "completion_tokens", 0) or 0)}
        return raw, usage, response

    @staticmethod
    def _supports_json_mode(model: str) -> bool:
        try:
            import litellm
            params = litellm.get_supported_openai_params(model=model) or []
            return "response_format" in params
        except Exception:
            return provider_of(model) in ("openai", "gemini", "groq", "openrouter", "ollama")


def _is_auth_error(e: Exception) -> bool:
    name = type(e).__name__.lower()
    return "auth" in name or "permission" in name or "401" in str(e) or "403" in str(e)
