"""Robust JSON extraction from model output: fences, prose around the object, trailing commas."""
from __future__ import annotations

import json
import re


class JSONExtractError(ValueError):
    pass


def extract_json(text: str):
    """Return the first JSON object/array found in `text`. Raises JSONExtractError."""
    if text is None:
        raise JSONExtractError("empty response")
    s = text.strip()
    # 1) fenced block
    m = re.search(r"```(?:json)?\s*(.*?)```", s, re.S | re.I)
    if m:
        s = m.group(1).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # 2) first balanced {...} or [...]
    for opener, closer in (("{", "}"), ("[", "]")):
        i = s.find(opener)
        while i != -1:
            depth, j, in_str, esc = 0, i, False, False
            while j < len(s):
                c = s[j]
                if in_str:
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == '"':
                        in_str = False
                elif c == '"':
                    in_str = True
                elif c == opener:
                    depth += 1
                elif c == closer:
                    depth -= 1
                    if depth == 0:
                        cand = s[i:j + 1]
                        try:
                            return json.loads(cand)
                        except json.JSONDecodeError:
                            try:
                                return json.loads(_repair(cand))
                            except json.JSONDecodeError:
                                break
                j += 1
            i = s.find(opener, i + 1)
    raise JSONExtractError("no JSON object found in the response")


def _repair(s: str) -> str:
    s = re.sub(r",\s*([}\]])", r"\1", s)            # trailing commas
    s = re.sub(r"(?<!\\)'", '"', s) if s.count('"') < 2 else s  # single-quoted JSON
    s = re.sub(r"//[^\n]*", "", s)                  # line comments
    return s
