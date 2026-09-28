"""Edit-decision step: ask the fast model which word ranges to drop (stumbles, repeated takes). Validated strictly; on doubt drop nothing."""
from __future__ import annotations

import re

SYSTEM = ("You are a dialogue editor. Given an analysis of a voice recording and its indexed transcript, list the word ranges to REMOVE: false starts, "
          "repeated takes (keep the last, better take), stumbles and filler that break the flow. Be conservative: when unsure, keep the words. "
          'Return {"drop": [{"from": <first word index>, "to": <last word index>, "reason": "<short>"}]} with inclusive indices, or {"drop": []}.')

MAX_SPAN = 15          # words per dropped range
MAX_TOTAL_FRACTION = 0.25


def decide_drops(llm, model: str, analysis: str, transcript: str, n_words: int, lang: str) -> tuple[str | None, list[dict]]:
    """Return (drop spec for `vt.py edit --drop`, usage list). None means: drop nothing."""
    user = f"ANALYSIS:\n{analysis.strip()[:4000]}\n\nINDEXED TRANSCRIPT ({n_words} words, language {lang}):\n{transcript.strip()[:12000]}"
    resp = llm.complete_json(SYSTEM, [{"role": "user", "content": user}], model=model, task="edit_decision", max_tokens=1500,
                             context={"n_words": n_words, "lang": lang})
    return validate_drops(resp.data, n_words), [resp.usage()]


def validate_drops(data, n_words: int) -> str | None:
    if not isinstance(data, dict) or not isinstance(data.get("drop"), list):
        return None
    ranges: list[tuple[int, int]] = []
    for r in data["drop"]:
        try:
            a, b = int(r["from"]), int(r["to"])
        except (KeyError, TypeError, ValueError):
            return None
        if not (0 <= a <= b < n_words) or b - a + 1 > MAX_SPAN:
            return None
        ranges.append((a, b))
    if not ranges:
        return None
    ranges.sort()
    for (_a1, b1), (a2, _b2) in zip(ranges, ranges[1:], strict=False):
        if a2 <= b1:
            return None  # overlapping: doubt
    if sum(b - a + 1 for a, b in ranges) > MAX_TOTAL_FRACTION * n_words:
        return None
    return ",".join(f"w:{a}-w:{b}" for a, b in ranges)


def stumble_candidates_present(analysis: str) -> bool:
    return bool(re.search(r"Possible retakes|stumbles", analysis or ""))
