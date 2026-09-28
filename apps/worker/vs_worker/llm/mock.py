"""MockLLM: the same `complete_json` interface without any provider.

Default behaviour per `task`:
  plan            the template's example plan (Arabic one when the video is Arabic and it exists) re-anchored to the
                  real transcript, with media slots filled from the asset list in `context`
  repair          same as plan (the scripted queue is what tests use to return "bad then good")
  edit_decision   {"drop": []}
  describe_assets {"descriptions": {name: "<kind> <n>"}}
  vision_review   {"fixes": []}
A scripted queue (`MockLLM(script=[...])`) returns canned dicts (or callables of the request) first, in order.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .client import LLMResponse

Scripted = dict | Callable[[dict], dict]


class MockLLM:
    name = "mock"

    def __init__(self, engine_dir: Path | None = None, script: list[Scripted] | None = None):
        from ..engine import ENGINE_DIR
        self.engine_dir = Path(engine_dir or ENGINE_DIR)
        self.script: list[Scripted] = list(script or [])
        self.calls: list[dict] = []
        self.requests: list[dict] = []

    def complete_json(self, system: str, messages: list[dict], *, schema=None, model: str | None = None, max_tokens=None, timeout=None,
                      task: str = "", images=None, temperature: float = 0.2, context: dict | None = None) -> LLMResponse:
        req = {"system": system, "messages": messages, "task": task, "model": model or "mock/mock", "images": list(images or []), "context": context or {}}
        self.requests.append(req)
        if self.script:
            item = self.script.pop(0)
            data = item(req) if callable(item) else item
        else:
            data = self._default(task, req)
        tokens_in = len(system) // 4 + sum(len(str(m.get("content"))) for m in messages) // 4
        r = LLMResponse(data=data, raw=json.dumps(data, ensure_ascii=False), model=str(req["model"]), tokens_in=tokens_in,
                        tokens_out=len(json.dumps(data)) // 4, cost_usd=0.0, cost_source="mock", task=task)
        self.calls.append(r.usage())
        return r

    # ------------------------------------------------------------------ defaults
    def _default(self, task: str, req: dict) -> dict:
        ctx = req["context"]
        if task in ("plan", "repair"):
            return self.example_plan(ctx.get("template", "steps"), ctx.get("lang", "en"), ctx.get("n_words", 0), ctx.get("assets", []),
                                     ctx.get("media_paths", []))
        if task == "edit_decision":
            return {"drop": []}
        if task == "describe_assets":
            return {"descriptions": {a["name"]: f"{a.get('kind', 'image')} {i + 1}" for i, a in enumerate(ctx.get("assets", []))}}
        if task == "vision_review":
            return {"fixes": []}
        return {}

    def example_plan(self, template: str, lang: str, n_words: int, assets: list[dict], media_paths: list[str]) -> dict:
        """Template example re-anchored to the real transcript: anchors are scaled from the demoScript's word count to n_words."""
        d = self.engine_dir / template / "examples"
        f = d / "plan.ar.json" if (lang or "en").startswith("ar") and (d / "plan.ar.json").exists() else d / "plan.example.json"
        plan = json.loads(f.read_text(encoding="utf-8"))
        n_demo = len((plan.pop("demoScript", "") or "").split())
        plan.pop("demoMedia", None)
        plan["lang"] = lang or plan.get("lang", "en")
        if n_words and n_demo:
            plan = rescale_anchors(plan, n_demo, n_words)
        names = [a["name"] for a in assets]
        if names:
            fill_media_slots(plan, media_paths, names)
        return plan


def rescale_anchors(obj: Any, n_from: int, n_to: int) -> Any:
    k = (n_to - 1) / max(1, n_from - 1)

    def conv(v):
        m = re.match(r"^(w|we):(\d+)(.*)$", v)
        if not m:
            return v
        i = min(n_to - 1, max(0, int(round(int(m.group(2)) * k))))
        return f"{m.group(1)}:{i}{m.group(3)}"

    if isinstance(obj, dict):
        return {a: rescale_anchors(b, n_from, n_to) for a, b in obj.items()}
    if isinstance(obj, list):
        return [rescale_anchors(x, n_from, n_to) for x in obj]
    if isinstance(obj, str):
        return conv(obj)
    return obj


def fill_media_slots(plan: dict, media_paths: list[str], names: list[str]) -> None:
    """Put asset names into the template's media fields, one asset per slot in order (dotted paths like 'rank.media')."""
    k = 0
    for sc in plan.get("scenes", []):
        for mp in media_paths:
            typ, _, rest = mp.partition(".")
            if sc.get("type") != typ or not rest:
                continue
            targets = _resolve_targets(sc, rest.split("."))
            for parent, key in targets:
                if k < len(names):
                    parent[key] = names[k]; k += 1


def _resolve_targets(obj: Any, parts: list[str]) -> list[tuple[Any, str]]:
    """Walk 'items[].media' / 'before.media' into (container, key) pairs, creating dicts on the way."""
    head, rest = parts[0], parts[1:]
    is_list = head.endswith("[]")
    key = head[:-2] if is_list else head
    if not rest:
        return [(obj, key)] if isinstance(obj, dict) else []
    child = obj.get(key) if isinstance(obj, dict) else None
    out: list[tuple[Any, str]] = []
    if is_list:
        for item in child or []:
            if isinstance(item, dict):
                out += _resolve_targets(item, rest)
    else:
        if child is None:
            child = obj[key] = {}
        if isinstance(child, dict):
            out += _resolve_targets(child, rest)
    return out
