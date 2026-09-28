"""LLM routing settings shared by the API (admin endpoint) and the worker. The worker re-exports this module as vs_worker.llm.settings."""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

# provider prefix (LiteLLM) -> env var holding its credential / endpoint
PROVIDER_ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY",
    "ollama": "OLLAMA_BASE_URL",
}
DEFAULTS_BY_AVAILABILITY = [  # first provider with a credential wins (brief §8)
    ("anthropic", "anthropic/claude-sonnet-5", "anthropic/claude-haiku-4-5-20251001"),
    ("openai", "openai/gpt-4o", "openai/gpt-4o-mini"),
    ("ollama", "ollama/qwen2.5:14b", "ollama/qwen2.5:14b"),
]
SETTING_KEYS = ("llm.planner_model", "llm.fast_model", "llm.vision_model", "llm.free_tier_model", "llm.fallback_chain")


def provider_of(model: str) -> str:
    return model.split("/", 1)[0] if "/" in model else "openai"


def provider_status(env: Mapping[str, str] | None = None) -> dict[str, dict]:
    env = dict(os.environ) if env is None else env
    return {prov: {"env": var, "available": bool(env.get(var))} for prov, var in PROVIDER_ENV.items()}


def _bool(v: str | None, default=False) -> bool:
    if v is None or v == "":
        return default
    return v.lower() in ("1", "true", "yes", "on")


@dataclass
class LLMSettings:
    planner_model: str
    fast_model: str
    vision_model: str
    free_tier_model: str
    paid_tier_model: str
    fallback_chain: list[str] = field(default_factory=list)
    vision_review: bool = False
    max_attempts: int = 3
    timeout_s: float = 120.0
    max_tokens: int = 8000
    ollama_base_url: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None, overrides: dict | None = None) -> LLMSettings:
        """env defaults, then `overrides` (app_settings rows keyed `llm.*`) on top."""
        env = dict(os.environ) if env is None else env
        ov = overrides or {}
        planner_default, fast_default = DEFAULTS_BY_AVAILABILITY[0][1], DEFAULTS_BY_AVAILABILITY[0][2]
        for prov, planner_m, fast_m in DEFAULTS_BY_AVAILABILITY:
            if env.get(PROVIDER_ENV[prov]):
                planner_default, fast_default = planner_m, fast_m
                break
        generic = env.get("LLM_MODEL")
        planner: str = str(ov.get("llm.planner_model") or env.get("LLM_MODEL_PLANNER") or generic or planner_default)
        fast: str = str(ov.get("llm.fast_model") or env.get("LLM_MODEL_FAST") or fast_default)
        vision: str = str(ov.get("llm.vision_model") or env.get("LLM_MODEL_VISION") or planner)
        free: str = str(ov.get("llm.free_tier_model") or env.get("PLANNER_MODEL_FREE") or fast)
        paid: str = str(env.get("PLANNER_MODEL_PAID") or planner)
        chain = ov.get("llm.fallback_chain")
        if isinstance(chain, str):
            chain = [c.strip() for c in chain.split(",") if c.strip()]
        if chain is None:
            chain = [c.strip() for c in (env.get("LLM_FALLBACK_CHAIN") or "").split(",") if c.strip()]
        return cls(planner_model=planner, fast_model=fast, vision_model=vision, free_tier_model=free, paid_tier_model=paid,
                   fallback_chain=list(chain), vision_review=_bool(env.get("PLANNER_VISION_REVIEW")),
                   max_attempts=int(env.get("PLANNER_MAX_ATTEMPTS", "3")), timeout_s=float(env.get("LLM_TIMEOUT_S", "120")),
                   max_tokens=int(env.get("LLM_MAX_TOKENS", "8000")), ollama_base_url=env.get("OLLAMA_BASE_URL") or None)

    def planner_for_tier(self, tier: str) -> str:
        return self.free_tier_model if tier == "free" else self.paid_tier_model

    def chain_for(self, model: str) -> list[str]:
        """Primary model followed by the fallback chain (without duplicates)."""
        out = [model]
        for m in self.fallback_chain:
            if m not in out:
                out.append(m)
        return out

    def to_dict(self) -> dict:
        return {"llm.planner_model": self.planner_model, "llm.fast_model": self.fast_model, "llm.vision_model": self.vision_model,
                "llm.free_tier_model": self.free_tier_model, "llm.fallback_chain": list(self.fallback_chain)}
