"""Template catalog: packages/shared/templates.json (generated from the engine) merged with template_flags rows."""
from __future__ import annotations

import json
from functools import lru_cache

from ..config import get_settings

SIZES: list[dict] = [{"id": "9:16", "label": "9:16 (TikTok / Reels / Shorts)", "w": 1080, "h": 1920}, {"id": "1:1", "label": "1:1 (square)", "w": 1080, "h": 1080},
         {"id": "4:5", "label": "4:5 (Instagram portrait)", "w": 1080, "h": 1350}, {"id": "16:9", "label": "16:9 (YouTube)", "w": 1920, "h": 1080},
         {"id": "custom", "label": "Custom WxH", "w": None, "h": None}]
PLATFORMS = ["tiktok", "reels", "shorts", "youtube", "linkedin", "x", "none"]
LANGUAGES = [{"code": "en", "name": "English"}, {"code": "ar", "name": "Arabic"}, {"code": "es", "name": "Spanish"}, {"code": "fr", "name": "French"},
             {"code": "de", "name": "German"}, {"code": "it", "name": "Italian"}, {"code": "pt", "name": "Portuguese"}, {"code": "tr", "name": "Turkish"},
             {"code": "hi", "name": "Hindi"}, {"code": "ur", "name": "Urdu"}, {"code": "fa", "name": "Persian"}, {"code": "he", "name": "Hebrew"},
             {"code": "ja", "name": "Japanese"}, {"code": "ko", "name": "Korean"}, {"code": "zh", "name": "Chinese"}, {"code": "id", "name": "Indonesian"},
             {"code": "ru", "name": "Russian"}, {"code": "nl", "name": "Dutch"}, {"code": "pl", "name": "Polish"}, {"code": "vi", "name": "Vietnamese"}]


@lru_cache(maxsize=1)
def templates() -> list[dict]:
    p = get_settings().catalog_json
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    # fallback: read the engine folders directly
    out = []
    for d in sorted(get_settings().engine_dir.iterdir()):
        tj = d / "template.json"
        if tj.exists():
            m = json.loads(tj.read_text(encoding="utf-8"))
            out.append({"name": d.name, "title": m.get("title", d.name), "category": m.get("category", ""), "summary": m.get("summary", ""),
                        "scenes": m.get("scenes", []), "needs_media": m.get("needsMedia", []), "has_ar_example": (d / "examples/plan.ar.json").exists(),
                        "preview": f"/previews/{d.name}.jpg"})
    return out


def by_name(name: str) -> dict | None:
    return next((t for t in templates() if t["name"] == name), None)
