"""Real-provider smoke tests: one tiny JSON completion per provider whose credential is present. Skipped otherwise."""
from __future__ import annotations

import os

import pytest

from vs_worker.llm.client import LLMClient
from vs_worker.llm.settings import PROVIDER_ENV, LLMSettings

REAL_MODELS = {
    "anthropic": "anthropic/claude-haiku-4-5-20251001",
    "openai": "openai/gpt-4o-mini",
    "gemini": "gemini/gemini-2.5-flash",
    "openrouter": "openrouter/openai/gpt-4o-mini",
    "groq": "groq/llama-3.3-70b-versatile",
    "ollama": os.environ.get("OLLAMA_MODEL", "ollama/qwen2.5:14b"),
}


@pytest.mark.network
@pytest.mark.parametrize("provider", sorted(REAL_MODELS))
def test_provider_smoke(provider):
    if not os.environ.get(PROVIDER_ENV[provider]):
        pytest.skip(f"{PROVIDER_ENV[provider]} not set")
    if os.environ.get("VT_OFFLINE") == "1":
        pytest.skip("VT_OFFLINE=1")
    c = LLMClient(LLMSettings.from_env())
    msgs = [{"role": "user", "content": 'Return {"answer": 42, "lang": "en"}'}]
    r = c.complete_json("You answer with JSON.", msgs, model=REAL_MODELS[provider], max_tokens=200, timeout=60, task="smoke")
    assert r.data.get("answer") == 42 and r.tokens_out > 0
