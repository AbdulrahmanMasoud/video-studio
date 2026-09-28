"""Plan validation (Pydantic + template whitelist + anchors + asset names), editable fields, asset slots, and edits by JSON path."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..engine import ENGINE_DIR
from .assets import RESERVED_MEDIA, media_fields

ANCHOR_RE = re.compile(r"^\s*(w|we):(\d+)\s*([+-]\s*\d*\.?\d+)?\s*$")
TIME_KEYS_RE = re.compile(r"^(start|end|at|.*At|t|drop|stops|wipeAt|flipAt|strikeAt|countdownAt|revealAt|underlineAt|priceAt|textAt)$")
NON_TEXT_KEYS = {"type", "transition", "media", "icon", "kind", "pos", "color", "font", "sfx", "layout", "device", "url", "align", "style", "mood",
                 "file", "name_key", "who", "id", "answer", "n", "currency", "src", "dir", "lang", "numerals", "highlight"}
MAX_LEN = {"title": 60, "kicker": 40, "label": 40, "short": 16, "sub": 80, "subtitle": 80, "text": 120, "cta": 60, "q": 120, "name": 60,
           "tagline": 80, "caption": 80, "a": 30, "b": 30, "code": 60, "role": 60, "tag": 40, "headline": 80, "default": 100}


class Scene(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str = Field(min_length=1)
    start: float | int | str


class Plan(BaseModel):
    model_config = ConfigDict(extra="allow")
    lang: str | None = None
    scenes: list[Scene] = Field(min_length=1)
    labels: dict[str, str] | None = None
    music: dict | None = None
    captions: dict | None = None
    palette: dict[str, str] | None = None
    data: dict | None = None
    sfx: list[dict] | None = None
    mix: dict | None = None
    duration: float | None = None


def template_scene_types(template: str, engine_dir: Path | None = None) -> list[str]:
    p = Path(engine_dir or ENGINE_DIR) / template / "template.json"
    types = json.loads(p.read_text(encoding="utf-8")).get("scenes", []) if p.exists() else []
    return sorted(set(types) | {"text", "media"})


def validate_plan(plan: Any, template: str, n_words: int, known_media: set[str] | None = None, engine_dir: Path | None = None) -> list[str]:
    """Return a list of human-readable errors (empty = valid). Mirrors the engine's own checks and adds asset-name validation."""
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["plan must be a JSON object"]
    try:
        Plan.model_validate(plan)
    except ValidationError as e:
        for err in e.errors()[:8]:
            errors.append("schema: " + ".".join(str(x) for x in err["loc"]) + ": " + err["msg"])
        return errors
    allowed = set(template_scene_types(template, engine_dir))
    for i, sc in enumerate(plan["scenes"]):
        if sc.get("type") not in allowed:
            errors.append(f'Scene {i}: type "{sc.get("type")}" is not defined by template {template}. Available: {", ".join(sorted(allowed))}')

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(o, list):
            for j, v in enumerate(o):
                walk(v, f"{path}[{j}]")
        elif isinstance(o, str):
            m = ANCHOR_RE.match(o)
            if m and int(m.group(2)) >= n_words:
                errors.append(f"{path}: Plan references missing word index {o.strip()} (have {n_words} words)")

    walk({"scenes": plan["scenes"], "music": plan.get("music") or {}, "sfx": plan.get("sfx") or [], "data": plan.get("data") or {}}, "")
    if known_media is not None:
        for path, name in asset_slots(plan, template, engine_dir, include_empty=False):
            if name not in known_media and name not in RESERVED_MEDIA:
                errors.append(f'{path}: unknown asset "{name}" (available: {", ".join(sorted(known_media)) or "none"})')
    return errors


# ------------------------------------------------------------------ editable fields
def _label(path: str, scene_type: str | None) -> str:
    parts = re.findall(r"([A-Za-z_]+)|\[(\d+)\]", path)
    words = []
    for name, idx in parts:
        if name == "scenes":
            continue
        if idx:
            words.append(f"#{int(idx) + 1}")
        else:
            words.append(name)
    head = f"{scene_type} " if scene_type else ""
    return (head + " · ".join(words)).strip()


def editable_fields(plan: dict) -> list[dict]:
    """Flat list of {path, label, value, maxLen} for every user-facing string in the plan (scenes + labels)."""
    out: list[dict] = []

    def walk(o, path, scene_type):
        if isinstance(o, dict):
            for k, v in o.items():
                p = f"{path}.{k}" if path else k
                if isinstance(v, str):
                    if k in NON_TEXT_KEYS or TIME_KEYS_RE.match(k) or ANCHOR_RE.match(v) or not v.strip():
                        continue
                    out.append({"path": p, "label": _label(p, scene_type), "value": v, "maxLen": MAX_LEN.get(k, MAX_LEN["default"])})
                else:
                    walk(v, p, scene_type)
        elif isinstance(o, list):
            for j, v in enumerate(o):
                walk(v, f"{path}[{j}]", scene_type)

    for i, sc in enumerate(plan.get("scenes", [])):
        walk(sc, f"scenes[{i}]", sc.get("type"))
    for k, v in (plan.get("labels") or {}).items():
        if isinstance(v, str):
            out.append({"path": f"labels.{k}", "label": f"label · {k}", "value": v, "maxLen": 40})
    return out


# ------------------------------------------------------------------ JSON paths
def _tokens(path: str) -> list[str | int]:
    toks: list[str | int] = []
    for name, idx in re.findall(r"([A-Za-z_][\w-]*)|\[(\d+)\]", path):
        toks.append(int(idx) if idx else name)
    return toks


def get_path(obj: Any, path: str, default=None):
    cur = obj
    for t in _tokens(path):
        try:
            cur = cur[t]
        except (KeyError, IndexError, TypeError):
            return default
    return cur


def set_path(obj: Any, path: str, value: Any, *, delete_if_none: bool = False) -> None:
    toks = _tokens(path)
    cur = obj
    for t in toks[:-1]:
        if isinstance(t, int):
            cur = cur[t]
        else:
            if t not in cur or cur[t] is None:
                cur[t] = {}
            cur = cur[t]
    last = toks[-1]
    if value is None and delete_if_none:
        if isinstance(cur, dict):
            cur.pop(last, None)
    else:
        cur[last] = value


def apply_text_edits(plan: dict, fields: list[dict]) -> dict:
    """fields: [{path, value}] from the editable-fields form. Only string values are accepted; anchors/times cannot be edited here."""
    out = copy.deepcopy(plan)
    allowed = {f["path"]: f for f in editable_fields(out)}
    for f in fields:
        path, value = str(f.get("path") or ""), f.get("value")
        if path not in allowed or not isinstance(value, str):
            raise ValueError(f"field {path!r} is not editable")
        set_path(out, path, value.strip()[: allowed[path]["maxLen"]])
    return out


# ------------------------------------------------------------------ asset slots
def _slot_paths(scene: dict, idx: int, rest: list[str]) -> list[str]:
    """Expand 'items[].media' inside scene idx into concrete JSON paths."""
    base = f"scenes[{idx}]"

    def rec(obj, prefix, parts):
        head, tail = parts[0], parts[1:]
        is_list = head.endswith("[]")
        key = head[:-2] if is_list else head
        if not tail:
            return [f"{prefix}.{key}"]
        child = obj.get(key) if isinstance(obj, dict) else None
        if is_list:
            return [p for j, it in enumerate(child or []) if isinstance(it, dict) for p in rec(it, f"{prefix}.{key}[{j}]", tail)]
        return rec(child if isinstance(child, dict) else {}, f"{prefix}.{key}", tail)

    return rec(scene, base, rest)


def asset_slots(plan: dict, template: str, engine_dir: Path | None = None, include_empty: bool = True) -> list[tuple[str, str | None]]:
    """[(json_path, asset_name|None)] for every media slot of the template present in the plan."""
    out: list[tuple[str, str | None]] = []
    fields = media_fields(template, engine_dir)
    for i, sc in enumerate(plan.get("scenes", [])):
        for mp in fields:
            typ, _, rest = mp.partition(".")
            if sc.get("type") != typ:
                continue
            for path in _slot_paths(sc, i, rest.split(".")):
                val = get_path(plan, path)
                if isinstance(val, str) and val:
                    out.append((path, val))
                elif include_empty and (val is None or val == ""):
                    out.append((path, None))
    return out


def apply_asset_changes(plan: dict, template: str, words: list[dict], changes: list[dict] | None = None, inserts: list[dict] | None = None,
                        known_assets: set[str] | None = None, engine_dir: Path | None = None) -> dict:
    """changes: [{path, asset|null}] swap/remove; inserts: [{asset, at_word, dur}] add a full-frame media scene at a word."""
    out = copy.deepcopy(plan)
    valid = {p for p, _ in asset_slots(out, template, engine_dir, include_empty=True)}
    for ch in changes or []:
        path, asset = ch.get("path"), ch.get("asset")
        if path not in valid:
            raise ValueError(f"{path!r} is not a media slot of template {template}")
        if asset is not None and known_assets is not None and asset not in known_assets:
            raise ValueError(f"unknown asset {asset!r}")
        set_path(out, str(path), asset, delete_if_none=True)
    for ins in inserts or []:
        asset, at_word, dur = str(ins.get("asset") or ""), int(ins.get("at_word", 0)), float(ins.get("dur") or 2.0)
        if not asset or (known_assets is not None and asset not in known_assets):
            raise ValueError(f"unknown asset {asset!r}")
        if not 0 <= at_word < len(words):
            raise ValueError(f"at_word {at_word} out of range (0..{len(words) - 1})")
        dur = max(1.5, min(dur, 15.0))
        out["scenes"] = _insert_media_scene(out["scenes"], words, asset, at_word, dur)
    return out


def _start_seconds(sc: dict, words: list[dict]) -> float:
    v = sc.get("start", 0)
    if isinstance(v, (int, float)):
        return float(v)
    m = ANCHOR_RE.match(str(v))
    if not m:
        return 0.0
    i = min(int(m.group(2)), len(words) - 1)
    base = words[i]["s"] if m.group(1) == "w" else words[i]["e"]
    return base + (float(m.group(3).replace(" ", "")) if m.group(3) else 0.0)


def _insert_media_scene(scenes: list[dict], words: list[dict], asset: str, at_word: int, dur: float) -> list[dict]:
    """Insert a `media` scene at word `at_word` for `dur` seconds; the interrupted scene resumes afterwards (a copy) so nothing goes dark."""
    t = words[at_word]["s"] - 0.1
    ordered = sorted(scenes, key=lambda s: _start_seconds(s, words))
    new = {"type": "media", "start": f"w:{at_word}-0.1", "end": f"w:{at_word}+{round(dur - 0.1, 2)}", "media": asset, "kenburns": True}
    out: list[dict] = []
    inserted = False
    for k, sc in enumerate(ordered):
        s0 = _start_seconds(sc, words)
        s1 = _start_seconds(ordered[k + 1], words) if k + 1 < len(ordered) else float("inf")
        out.append(sc)
        if not inserted and s0 <= t < s1:
            out.append(new)
            inserted = True
            if t + dur < s1 - 0.4:  # resume the interrupted scene after the insert
                resume = copy.deepcopy(sc)
                resume["start"] = f"w:{at_word}+{round(dur - 0.1, 2)}"
                out.append(resume)
    if not inserted:
        out.append(new)
    return out
