"""plans.yaml access and plan rules (credits, resolution, watermark, templates, limits)."""
from __future__ import annotations

import math
from functools import lru_cache

import yaml

from ..config import get_settings

CREDIT_SECONDS = 90


@lru_cache(maxsize=1)
def load() -> dict:
    return yaml.safe_load(get_settings().plans_yaml.read_text(encoding="utf-8")) or {}


def plans() -> dict:
    return load().get("plans", {})


def plan(name: str) -> dict:
    p = plans().get(name)
    if p is None:
        raise KeyError(f"unknown plan {name!r}")
    return {"name": name, **p}


def limits() -> dict:
    return load().get("limits", {})


def basic_templates() -> list[str]:
    return list((load().get("templates") or {}).get("basic", []))


def is_paid(plan_name: str) -> bool:
    return plan_name != "free"


def credits_for_duration(seconds: float) -> int:
    """1 credit per started 90 s (never 0)."""
    return max(1, math.ceil(max(0.0, float(seconds)) / CREDIT_SECONDS))


def render_rules(plan_name: str) -> dict:
    p = plan(plan_name)
    return {"max_res": int(p.get("max_res", 720)), "watermark": bool(p.get("watermark", True)), "templates": p.get("templates", "basic"),
            "brand_kit": bool(p.get("brand_kit", False)), "priority_queue": bool(p.get("priority_queue", False)),
            "output_retention_days": int(p.get("output_retention_days", 30))}


def concurrency_limit(plan_name: str) -> int:
    c = limits().get("concurrent_jobs", {})
    return int(c.get("paid" if is_paid(plan_name) else "free", 1))


def projects_per_hour(plan_name: str) -> int:
    c = limits().get("projects_per_hour", {})
    return int(c.get("paid" if is_paid(plan_name) else "free", 10))


def template_allowed(plan_name: str, template: str, flag_tier: str = "free") -> bool:
    rules = render_rules(plan_name)
    if rules["templates"] != "all" and template not in basic_templates():
        return False
    order = ["free", "starter", "pro", "agency"]
    return order.index(plan_name) >= order.index(flag_tier) if flag_tier in order and plan_name in order else True
