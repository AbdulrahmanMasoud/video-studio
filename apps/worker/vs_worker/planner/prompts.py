"""Prompt builder for the storyboard planner (system prompt + user message)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from ..engine import ENGINE_DIR
from .assets import RESERVED_MEDIA, media_fields

ROLE = ("You are a senior short-form video editor and motion designer. You write the storyboard (plan.json) that an "
        "animation engine renders frame-accurately on top of the speaker's voice.")

HARD_RULES = """HARD RULES (violations make the video unusable):
1. ALL on-screen text must be in the video language ({lang_name}, code "{lang}"). Translate template UI words with "labels".
2. Anchor every reveal to the word that says it: use "w:<index>" / "we:<index>" from the indexed transcript below. Never invent indices; the
   transcript has {n_words} words (indices 0..{last}). Start a scene ~0.1 s before its first word ("w:12-0.1").
3. On-screen text summarises, it does not transcribe: at most 6 words per card/title (captions carry the speech).
4. Never invent facts, numbers, statistics, names or quotes that the speaker did not say.
5. Scenes are ordered by time and each scene ends where the next starts; keep the last scene ≥ 1.2 s after the last word.
6. Use only scene types of this template: {scene_types}. Every scene needs "type" and "start".
7. Output JSON only, matching the plan schema: keys "lang", "scenes", optional "labels", "music", "captions", "palette", "data", "sfx".
{asset_rules}"""

ASSET_RULES = """8. ASSETS: the user provided these media assets (name, kind, description). Use an asset ONLY where the voice talks about it, in these
   media slots of this template: {media_fields}. Never reuse the same asset in two slots unless the brief asks. Prefer transparent PNGs
   (has_alpha) for product slots. Put leftover but relevant assets in full-frame "media" scenes (type "media", field "media", ≥ 1.5 s,
   anchored to a matching phrase). Never invent asset names: only {asset_names} exist. Leave a slot empty rather than guessing."""

LANG_NAMES = {"en": "English", "ar": "Arabic", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", "pt": "Portuguese", "tr": "Turkish",
              "hi": "Hindi", "ur": "Urdu", "fa": "Persian", "he": "Hebrew", "ja": "Japanese", "ko": "Korean", "zh": "Chinese", "id": "Indonesian",
              "ru": "Russian", "nl": "Dutch", "pl": "Polish", "sv": "Swedish", "vi": "Vietnamese", "th": "Thai", "bn": "Bengali", "ta": "Tamil"}


def lang_name(code: str) -> str:
    return LANG_NAMES.get((code or "en").split("-")[0].lower(), code)


def skill_doc(template: str, engine_dir: Path | None = None) -> str:
    """The template's SKILL.md without the bash 'Produce' section (the model does not run commands)."""
    p = Path(engine_dir or ENGINE_DIR) / template / "SKILL.md"
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)                      # frontmatter
    text = re.sub(r"## 2\. Produce.*?(?=## 3\.)", "", text, flags=re.S)                    # bash block
    text = re.sub(r"## 1\. Intake.*?(?=## 3\.)", "", text, flags=re.S)                     # intake questions
    return text.strip()


def plan_schema_doc(engine_dir: Path | None = None) -> str:
    p = Path(engine_dir or ENGINE_DIR) / "video-engine/references/plan-schema.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def example_plan(template: str, lang: str, engine_dir: Path | None = None, max_scenes: int = 6) -> dict | None:
    d = Path(engine_dir or ENGINE_DIR) / template / "examples"
    f = d / "plan.ar.json" if (lang or "").startswith("ar") and (d / "plan.ar.json").exists() else d / "plan.example.json"
    if not f.exists():
        return None
    plan = json.loads(f.read_text(encoding="utf-8"))
    script = plan.pop("demoScript", None)
    plan.pop("demoMedia", None)
    plan["scenes"] = plan.get("scenes", [])[:max_scenes]
    return {"script_excerpt": " ".join((script or "").split()[:60]), "plan": plan}


def build_system_prompt(template: str, lang: str, n_words: int, scene_types: list[str], assets: list[dict], engine_dir: Path | None = None) -> str:
    names = [a["name"] for a in assets]
    asset_rules = ASSET_RULES.format(media_fields=", ".join(media_fields(template, engine_dir)), asset_names=", ".join(names)) if names else \
        "8. There are no user assets: do not use media slots or \"media\" scenes (the engine would draw a placeholder)."
    rules = HARD_RULES.format(lang_name=lang_name(lang), lang=lang, n_words=n_words, last=max(0, n_words - 1), scene_types=", ".join(scene_types),
                              asset_rules=asset_rules)
    return "\n\n".join([ROLE, f"# TEMPLATE: {template}\n" + skill_doc(template, engine_dir), "# PLAN SCHEMA\n" + plan_schema_doc(engine_dir), rules])


def build_user_message(*, transcript_edit: str, brief: dict, lang: str, size: tuple[int, int], platform: str, template: str, assets: list[dict],
                       brand: dict | None = None, engine_dir: Path | None = None) -> str:
    parts = [f"VIDEO: language={lang} ({lang_name(lang)}), size={size[0]}x{size[1]}, platform={platform}, template={template}."]
    if brief:
        b = {k: v for k, v in brief.items() if v}
        if b:
            parts.append("BRIEF from the user (follow it, but never invent facts):\n" + json.dumps(b, ensure_ascii=False))
    if brand and (brand.get("palette") or brand.get("fonts")):
        parts.append("BRAND KIT (already applied by the engine; do not override palette unless asked): " + json.dumps(brand, ensure_ascii=False))
    if assets:
        rows = [{k: a.get(k) for k in ("name", "kind", "description", "width", "height", "duration", "has_alpha") if a.get(k) is not None} for a in assets
                if a.get("name") not in RESERVED_MEDIA]
        parts.append("ASSETS:\n" + json.dumps(rows, ensure_ascii=False))
    ex = example_plan(template, lang, engine_dir)
    if ex:
        parts.append("EXAMPLE (a different script; shows the style and how anchors are used):\nscript: " + ex["script_excerpt"] +
                     "\nplan (shortened):\n" + json.dumps(ex["plan"], ensure_ascii=False))
    parts.append("INDEXED TRANSCRIPT (edited; [index] word@seconds):\n" + transcript_edit.strip())
    parts.append("Write the complete plan.json for this transcript now. JSON only.")
    return "\n\n".join(parts)


def repair_message(errors: list[str]) -> str:
    return ("The engine rejected the plan with these errors:\n- " + "\n- ".join(errors[:12]) +
            "\n\nFix ONLY what is needed and return the complete corrected plan.json (JSON only).")
