"""Cost estimate: LiteLLM's cost map when it knows the model, else the price table in packages/shared/plans.yaml."""
from __future__ import annotations

import functools
import os
from pathlib import Path

ROOT = Path(os.environ.get("VS_REPO_ROOT", Path(__file__).resolve().parents[4]))
PLANS_YAML = Path(os.environ.get("VS_PLANS_YAML", ROOT / "packages/shared/plans.yaml"))


@functools.lru_cache(maxsize=1)
def price_table() -> dict:
    try:
        import yaml
        data = yaml.safe_load(PLANS_YAML.read_text(encoding="utf-8")) or {}
        return data.get("llm_prices") or {}
    except Exception:
        return {}


def table_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    t = price_table()
    row = t.get(model)
    if row is None:
        prov = model.split("/", 1)[0] + "/*"
        row = t.get(prov) or t.get("default") or {"input": 0.0, "output": 0.0}
    return round((tokens_in * float(row.get("input", 0)) + tokens_out * float(row.get("output", 0))) / 1e6, 6)


def estimate_cost(model: str, tokens_in: int, tokens_out: int, response=None) -> tuple[float, str]:
    """Returns (usd, source) where source is 'litellm' or 'table'."""
    if response is not None:
        try:
            import litellm
            c = litellm.completion_cost(completion_response=response)
            if c and c > 0:
                return round(float(c), 6), "litellm"
        except Exception:
            pass
    return table_cost(model, tokens_in, tokens_out), "table"
