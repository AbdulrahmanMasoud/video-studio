"""Deterministic fallback planner: used when no LLM is reachable so the product never fully stops.

Rules (from the brief): split the transcript into sections on pauses, one scene per section, titles = the
first 4–6 words. Dedicated storyboards exist for `steps` and `mirror`; every other template gets the common
`text` scene per section (available in all templates), so a plan always validates.
"""
from __future__ import annotations

from .transcript import announced_count, first_word, sections, title

NAME = "fallback"

LABELS = {  # template UI words in the languages we ship UI for; the LLM planner handles the rest
    "en": {"remember": "Remember", "save": "Save this", "prompt": "Prompt", "unclear": "unclear"},
    "ar": {"remember": "الخلاصة", "save": "احفظ الفيديو", "prompt": "برومبت", "unclear": "غير واضح"},
}


def _labels(lang):
    return LABELS.get((lang or "en").split("-")[0].lower(), LABELS["en"])


def plan(template: str, words: list[dict], lang: str | None, *, brief: dict | None = None, media: dict | None = None, duration: float | None = None) -> dict:
    """Return a plan.json dict for the template anchored to word indices of `words` (words_edit.json)."""
    lang = lang or "en"
    brief = brief or {}
    if not words:
        return {"lang": lang, "duration": duration or 8, "scenes": [{"type": "text", "start": 0, "text": brief.get("title") or "…"}]}
    secs = sections(words)
    fn = {"steps": _steps, "mirror": _mirror}.get(template, _generic)
    p = fn(words, secs, lang, brief, media or {})
    p["lang"] = lang
    return p


def _steps(words, secs, lang, brief, media):
    L = _labels(lang)
    scenes: list[dict] = []
    a0, b0 = secs[0]
    hook = {"type": "hook", "start": 0, "title": brief.get("title") or title(words, a0, b0), "icon": "bulb", "at": f"w:{a0}"}
    scenes.append(hook)
    body = secs[1:-1] if len(secs) >= 3 else secs[1:]
    cnt = announced_count(words, a0, b0, lang)
    if cnt and len(body) >= 2 and cnt[1] >= 2:
        i, n = cnt
        # split the hook sentence: count scene starts on the number word
        scenes.append({"type": "count", "start": f"w:{i}-0.1", "n": min(n, len(body)), "at": f"w:{i}",
                       "text": title(words, i + 1, b0) if i < b0 else "", "textAt": f"w:{min(i + 1, b0)}"})
    for a, b in body:
        t = title(words, a, b)
        scenes.append({"type": "step", "start": f"w:{a}-0.1", "short": first_word(words, a), "title": t,
                       "card": {"kind": "text", "text": title(words, a, b, 5, 8, 60), "at": f"w:{min(a + 1, b)}"}})
    if len(secs) >= 3:
        a, b = secs[-1]
        scenes.append({"type": "outro", "start": f"w:{a}-0.1", "label": L["remember"], "text": title(words, a, b), "textAt": f"w:{a}",
                       "cta": L["save"]})
    drop = f"w:{secs[min(1, len(secs) - 1)][0]}"
    return {"scenes": scenes, "labels": {"prompt": L["prompt"], "unclear": L["unclear"]}, "music": {"mood": "lofi", "drop": drop}}


def _mirror(words, secs, lang, brief, media):
    scenes: list[dict] = []
    a0, b0 = secs[0]
    scenes.append({"type": "title", "start": 0, "text": brief.get("title") or title(words, a0, b0), "at": 0.1, "end": f"we:{b0}"})
    for k, (a, b) in enumerate(secs[1:] if len(secs) > 1 else secs):
        sc = {"type": "talk", "start": f"w:{a}-0.05",
              "zooms": [{"at": f"w:{a}", "end": f"we:{min(a + 2, b)}+0.2", "scale": 1.3 if k % 2 == 0 else 1.15, "snap": True}],
              "stickers": [{"text": title(words, a, b, 2, 5, 28), "at": f"w:{a}", "end": f"we:{b}", "pos": "top" if k % 2 == 0 else "middle"}]}
        scenes.append(sc)
    data = {}
    if "cam" not in media:
        data["punch"] = False
    return {"scenes": scenes, "music": {"mood": "lofi"}, **({"data": data} if data else {})}


def _generic(words, secs, lang, brief, media):
    scenes: list[dict] = []
    for k, (a, b) in enumerate(secs):
        text = brief.get("title") if k == 0 and brief.get("title") else title(words, a, b)
        scenes.append({"type": "text", "start": 0 if k == 0 else f"w:{a}-0.1", "text": text, "at": f"w:{a}"})
    return {"scenes": scenes}
