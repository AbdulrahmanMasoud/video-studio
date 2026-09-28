"""Template media slots (from each SKILL.md scene table) and asset description with a vision model."""
from __future__ import annotations

import functools
import re
from pathlib import Path

from ..engine import ENGINE_DIR

# Curated fallback (what the SKILL.md tables say today). The parser below derives the same from the tables; this
# map is used when a table cannot be parsed. Dotted paths: "<scene>.<field>", "[]" marks a list.
CURATED_MEDIA_FIELDS = {
    "before-after": ["compare.before.media", "compare.after.media"],
    "breaking": ["headline.media"], "cinema": ["shot.media"], "city-map": ["place.media"], "flash-sale": ["items.items[].media"],
    "podcast": ["solo.media"], "review": ["score.media"], "screen": ["demo.media"], "storytime": ["photo.media"],
    "showcase": ["product.media"], "recipe": ["title.media", "step.media", "final.media"], "top-five": ["rank.media"],
    "workout": ["exercise.media"],
}
COMMON_MEDIA_FIELDS = ["media.media"]
# media names the engine/pipeline registers itself (never user assets)
RESERVED_MEDIA = {"cam", "screen", "photo", "broll"}


def _fields_in(spec: str, prefix: str) -> list[str]:
    """Find `media` fields inside a scene's field spec like "`before` {`label`, `media`}, `items` [{`name`, `media`}], `media`"."""
    out: list[str] = []
    # nested objects: `name` {...}  or `name` [{...}]; `other` {…} means "same fields as the previous object"
    prev_has_media = False
    for m in re.finditer(r"`(\w+)`\s*(\[?\{)(.*?)\}\]?", spec):
        name, opener, inner = m.group(1), m.group(2), m.group(3)
        sub = "[]" if opener.startswith("[") else ""
        has_media = bool(re.search(r"`media`", inner)) or (inner.strip() in ("…", "...") and prev_has_media)
        if has_media:
            out.append(f"{prefix}.{name}{sub}.media")
        prev_has_media = has_media
    # top-level `media` (not inside braces)
    flat = re.sub(r"\[?\{.*?\}\]?", "", spec)
    if re.search(r"`media`", flat):
        out.append(f"{prefix}.media")
    return out


@functools.lru_cache(maxsize=64)
def media_fields(template: str, engine_dir: Path | None = None) -> list[str]:
    """Dotted media slot paths for a template, e.g. ['rank.media', 'media.media'] (parsed from SKILL.md, curated fallback)."""
    skill = Path(engine_dir or ENGINE_DIR) / template / "SKILL.md"
    found: list[str] = []
    if skill.exists():
        for line in skill.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\|\s*`(\w[\w-]*)`\s*\|\s*(.*?)\s*\|\s*$", line)
            if not m or m.group(1) in ("type", "media", "text"):
                continue
            found += _fields_in(m.group(2), m.group(1))
    if not found:
        found = list(CURATED_MEDIA_FIELDS.get(template, []))
    seen: list[str] = []
    for f in found + COMMON_MEDIA_FIELDS:
        if f not in seen:
            seen.append(f)
    return seen


def preview_image(entry: dict, job_dir: Path) -> Path | None:
    """A JPEG/PNG path representing a registered media entry (image file, or the middle frame of a clip)."""
    if entry.get("type") == "image":
        p = Path(entry["src"].replace("file://", ""))
        return p if p.exists() else None
    d = Path(entry.get("dir", "").replace("file://", ""))
    frames = sorted(d.glob("*.jpg")) if d.exists() else []
    return frames[len(frames) // 2] if frames else None


class AssetDescriber:
    """Fills missing asset descriptions with one short line each, in the video language (fast vision model)."""

    def __init__(self, llm, model: str, lang_names: dict | None = None):
        self.llm, self.model = llm, model

    def describe(self, index: list[dict], media: dict, job_dir: Path, lang: str) -> tuple[list[dict], list[dict]]:
        todo = [r for r in index if not r.get("error") and not (r.get("description") or "").strip()]
        usage: list[dict] = []
        if not todo:
            return index, usage
        images, names = [], []
        for r in todo:
            p = preview_image(media.get(r["name"], {}), job_dir)
            if p:
                images.append(p); names.append(r["name"])
        if not names:
            return index, usage
        system = ("You describe images for a video editor. For each image, write ONE short line (max 12 words) in the language with "
                  f"code '{lang}' saying what it shows (object, person, place, screenshot...). Never invent brands or text you cannot read.")
        user = ("The images are attached in this order: " + ", ".join(names) +
                '. Return {"descriptions": {"<name>": "<one line>", ...}} with exactly these names.')
        resp = self.llm.complete_json(system, [{"role": "user", "content": user}], model=self.model, task="describe_assets", images=images,
                                      context={"assets": [{"name": n, "kind": next((r.get("kind") for r in todo if r["name"] == n), "image")} for n in names],
                                               "lang": lang})
        usage.append(resp.usage())
        desc = (resp.data or {}).get("descriptions") or {}
        for r in index:
            if r["name"] in desc and isinstance(desc[r["name"]], str) and desc[r["name"]].strip():
                r["description"] = desc[r["name"]].strip()[:120]
                r["description_source"] = "ai"
        return index, usage
