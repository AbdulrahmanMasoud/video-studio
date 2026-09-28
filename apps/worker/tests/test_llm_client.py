"""LLMClient through a fake transport: every provider goes through the same code path (json mode detection, api_base for Ollama,
fence stripping, repair pass, fallback chain, cost accounting) without network."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from vs_worker.llm.client import LLMClient, LLMError
from vs_worker.llm.cost import table_cost
from vs_worker.llm.json_utils import JSONExtractError, extract_json
from vs_worker.llm.settings import PROVIDER_ENV, LLMSettings, provider_status

PROVIDER_MODELS = ["anthropic/claude-sonnet-5", "openai/gpt-4o", "gemini/gemini-2.5-pro", "openrouter/meta-llama/llama-3.3-70b-instruct",
                   "groq/llama-3.3-70b-versatile", "ollama/qwen2.5:14b"]


def fake_response(content: str, tin=120, tout=40):
    usage = SimpleNamespace(prompt_tokens=tin, completion_tokens=tout)
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))], usage=usage)


class Transport:
    """Records calls and returns queued contents (or raises queued exceptions)."""

    def __init__(self, *items):
        self.items = list(items); self.calls = []

    def __call__(self, **kw):
        self.calls.append(kw)
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return fake_response(item)


def settings(**kw):
    base = dict(planner_model="anthropic/claude-sonnet-5", fast_model="anthropic/claude-haiku-4-5-20251001", vision_model="anthropic/claude-sonnet-5",
                free_tier_model="anthropic/claude-haiku-4-5-20251001", paid_tier_model="anthropic/claude-sonnet-5", fallback_chain=[], ollama_base_url="http://ollama:11434")
    base.update(kw)
    return LLMSettings(**base)


@pytest.mark.parametrize("model", PROVIDER_MODELS)
def test_every_provider_same_code_path(model):
    t = Transport('```json\n{"scenes": [{"type": "hook", "start": 0}], "lang": "en"}\n```')
    c = LLMClient(settings(), completion=t)
    r = c.complete_json("sys", [{"role": "user", "content": "plan"}], model=model, task="plan")
    assert r.data["scenes"][0]["type"] == "hook" and r.model == model and r.attempts == 1
    kw = t.calls[0]
    assert kw["model"] == model and kw["messages"][0]["role"] == "system" and "JSON" in kw["messages"][0]["content"]
    assert kw["timeout"] == 120.0 and kw["max_tokens"] == 8000
    if model.startswith("ollama/"):
        assert kw["api_base"] == "http://ollama:11434"
    assert r.tokens_in == 120 and r.tokens_out == 40 and r.cost_usd >= 0 and r.cost_source in ("table", "litellm")


def test_repair_pass_on_invalid_json():
    t = Transport("Sure! Here is the plan: {scenes: [broken", '{"scenes": [{"type": "text", "start": 0}]}')
    c = LLMClient(settings(), completion=t)
    r = c.complete_json("sys", [{"role": "user", "content": "x"}], model="openai/gpt-4o")
    assert r.attempts == 2 and r.data["scenes"][0]["type"] == "text"
    assert "not valid JSON" in t.calls[1]["messages"][-1]["content"]
    assert r.tokens_in == 240  # both calls counted


def test_invalid_json_twice_raises():
    t = Transport("nope", "still nope")
    with pytest.raises(LLMError) as ei:
        LLMClient(settings(), completion=t).complete_json("s", [{"role": "user", "content": "x"}], model="openai/gpt-4o")
    assert "invalid JSON twice" in str(ei.value)


def test_fallback_chain_on_provider_error():
    t = Transport(TimeoutError("read timed out"), '{"ok": true}')
    c = LLMClient(settings(fallback_chain=["openai/gpt-4o"]), completion=t)
    r = c.complete_json("s", [{"role": "user", "content": "x"}], model="anthropic/claude-sonnet-5")
    assert r.data == {"ok": True} and r.model == "openai/gpt-4o" and r.models_tried == ["anthropic/claude-sonnet-5", "openai/gpt-4o"]


def test_chain_exhausted_raises_transient():
    t = Transport(ConnectionError("down"), ConnectionError("down too"))
    c = LLMClient(settings(fallback_chain=["groq/llama-3.3-70b-versatile"]), completion=t)
    with pytest.raises(LLMError) as ei:
        c.complete_json("s", [{"role": "user", "content": "x"}], model="anthropic/claude-sonnet-5")
    assert ei.value.transient and "all models failed" in str(ei.value)


def test_auth_error_is_not_retried_on_chain():
    class AuthenticationError(Exception):
        pass
    t = Transport(AuthenticationError("401 bad key"), '{"ok": 1}')
    c = LLMClient(settings(fallback_chain=["openai/gpt-4o"]), completion=t)
    with pytest.raises(LLMError):
        c.complete_json("s", [{"role": "user", "content": "x"}], model="anthropic/claude-sonnet-5")
    assert len(t.calls) == 1


def test_images_are_attached_as_data_urls(tmp_path):
    from PIL import Image
    img = tmp_path / "sheet.jpg"; Image.new("RGB", (8, 8), (1, 2, 3)).save(img)
    t = Transport('{"fixes": []}')
    LLMClient(settings(), completion=t).complete_json("s", [{"role": "user", "content": "review"}], model="openai/gpt-4o", images=[img])
    content = t.calls[0]["messages"][-1]["content"]
    assert isinstance(content, list) and content[0]["type"] == "text" and content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_extract_json_variants():
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('text before {"a": [1, 2,]} after') == {"a": [1, 2]}
    assert extract_json('```json\n{"a": "x}"}\n```') == {"a": "x}"}
    assert extract_json('[1, 2]') == [1, 2]
    with pytest.raises(JSONExtractError):
        extract_json("no json here")


def test_cost_table_fallback():
    assert table_cost("anthropic/claude-sonnet-5", 1_000_000, 0) == 3.0
    assert table_cost("ollama/anything", 5000, 5000) == 0.0
    assert table_cost("unknown/model", 1_000_000, 1_000_000) == 18.0


def test_settings_defaults_follow_available_keys():
    s = LLMSettings.from_env(env={"ANTHROPIC_API_KEY": "k"})
    assert s.planner_model.startswith("anthropic/") and s.fast_model.startswith("anthropic/")
    s = LLMSettings.from_env(env={"OPENAI_API_KEY": "k"})
    assert s.planner_model == "openai/gpt-4o"
    s = LLMSettings.from_env(env={"OLLAMA_BASE_URL": "http://x"})
    assert s.planner_model.startswith("ollama/") and s.ollama_base_url == "http://x"
    env = {"OPENAI_API_KEY": "k", "LLM_MODEL_PLANNER": "groq/llama-3.3-70b-versatile", "LLM_FALLBACK_CHAIN": "openai/gpt-4o, gemini/gemini-2.5-pro"}
    s = LLMSettings.from_env(env=env, overrides={"llm.fast_model": "openai/gpt-4o-mini"})
    assert s.planner_model == "groq/llama-3.3-70b-versatile" and s.fast_model == "openai/gpt-4o-mini"
    assert s.chain_for(s.planner_model) == ["groq/llama-3.3-70b-versatile", "openai/gpt-4o", "gemini/gemini-2.5-pro"]
    assert s.planner_for_tier("free") == "openai/gpt-4o-mini" and s.planner_for_tier("paid") == "groq/llama-3.3-70b-versatile"
    st = provider_status({"GROQ_API_KEY": "x"})
    assert st["groq"]["available"] and not st["anthropic"]["available"] and set(st) == set(PROVIDER_ENV)


def test_json_mode_detection_uses_litellm_when_present():
    # openai supports response_format; the flag must be present in the request for such providers
    t = Transport('{"a":1}')
    LLMClient(settings(), completion=t).complete_json("s", [{"role": "user", "content": "x"}], model="openai/gpt-4o")
    assert t.calls[0].get("response_format") == {"type": "json_object"}
