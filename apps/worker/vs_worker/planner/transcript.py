"""Transcript helpers shared by the planners: sentences, sections on pauses, short titles."""
from __future__ import annotations

import re

END_PUNCT = ".!?؟。！？"
STRIP = " \t\n.,;:!?؟،。！？\"'“”‘’()[]{}"
STOPWORDS = {"for", "and", "or", "the", "a", "an", "to", "of", "in", "on", "at", "with", "every", "one", "your", "my", "but", "so", "is",
             "are", "that", "this", "it", "you", "we", "و", "في", "على", "من", "إلى", "عن", "بس", "اللي", "ده", "دي", "كل", "أي", "مع", "عشان"}


def clean(word: str) -> str:
    return word.strip(STRIP)


def sentences(words: list[dict]) -> list[tuple[int, int]]:
    """(first_index, last_index) per sentence, split on end punctuation."""
    out, start = [], 0
    for i, w in enumerate(words):
        if w["w"][-1:] in END_PUNCT or i == len(words) - 1:
            out.append((start, i)); start = i + 1
    return out


def sections(words: list[dict], gap: float = 0.28, max_s: float = 9.0, min_words: int = 3) -> list[tuple[int, int]]:
    """Split the edited transcript into beats.

    Sentences (end punctuation) are the primary unit; when the transcript has no punctuation, pauses >= gap are used.
    Pieces shorter than min_words merge into their neighbour, sentences longer than max_s are split at their longest
    inner pause. Always returns at least one section covering all words.
    """
    if not words:
        return []
    cuts = [i for i in range(1, len(words)) if words[i - 1]["w"][-1:] in END_PUNCT]
    if not cuts:
        cuts = [i for i in range(1, len(words)) if words[i]["s"] - words[i - 1]["e"] >= gap]
    starts = [0] + cuts
    pieces = [[starts[k], (starts[k + 1] - 1) if k + 1 < len(starts) else len(words) - 1] for k in range(len(starts))]
    merged: list[list[int]] = []
    for a, b in pieces:
        if merged and (b - a + 1) < min_words:
            merged[-1][1] = b                      # tiny sentence ("Why?") joins the previous beat
        elif merged and (merged[-1][1] - merged[-1][0] + 1) < min_words:
            merged[-1][1] = b                      # previous beat was tiny: absorb this one
        else:
            merged.append([a, b])
    out: list[tuple[int, int]] = []
    for a, b in merged:
        out.extend(_split_long(words, a, b, max_s))
    return out


def _split_long(words, a, b, max_s):
    if words[b]["e"] - words[a]["s"] <= max_s or b - a < 6:
        return [(a, b)]
    mid = max(range(a + 3, b - 2), key=lambda i: words[i]["s"] - words[i - 1]["e"])
    return _split_long(words, a, mid - 1, max_s) + _split_long(words, mid, b, max_s)


def title(words: list[dict], a: int, b: int, min_words: int = 4, max_words: int = 6, max_chars: int = 40) -> str:
    """First 4–6 words of a section, cut at a natural point (comma/period), without trailing punctuation."""
    toks = [w["w"].strip(" \t\n\"'“”‘’()[]{}") for w in words[a:b + 1]]
    toks = [t for t in toks if t]
    out: list[str] = []
    for t in toks[:max_words]:
        if out and len(" ".join(out + [t])) > max_chars and len(out) >= min(min_words, len(toks)):
            break
        out.append(t)
        if len(out) >= min_words and t[-1:] in ",;:،" + END_PUNCT:
            break
    while len(out) > 3 and out[-1].strip(STRIP).lower() in STOPWORDS:
        out.pop()                                   # do not end a title on "for", "and", "the"…
    text = " ".join(out) or (toks[0] if toks else "")
    return text.rstrip(" .,;:!?؟،。！？")


def first_word(words, a) -> str:
    return clean(words[a]["w"]) or "•"


def is_rtl(lang: str | None) -> bool:
    return (lang or "en").split("-")[0].lower() in {"ar", "fa", "ur", "he", "iw", "yi", "ps", "sd", "ug", "dv", "ckb"}


NUMBER_WORDS = {
    "en": {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10},
    "ar": {"اثنين": 2, "اتنين": 2, "ثلاث": 3, "ثلاثة": 3, "تلات": 3, "تلاتة": 3, "أربع": 4, "أربعة": 4, "اربع": 4, "خمس": 5, "خمسة": 5,
           "ست": 6, "ستة": 6, "سبع": 7, "سبعة": 7, "ثماني": 8, "ثمانية": 8, "تسع": 9, "تسعة": 9, "عشر": 10, "عشرة": 10},
}


def announced_count(words, a, b, lang) -> tuple[int, int] | None:
    """If the sentence a..b announces a count ("three tips", "أربع حاجات"), return (index, n)."""
    table = NUMBER_WORDS.get((lang or "en").split("-")[0].lower(), NUMBER_WORDS["en"])
    for i in range(a, b + 1):
        t = clean(words[i]["w"])
        if t.isdigit() and 2 <= int(t) <= 10:
            return i, int(t)
        if t.lower() in table:
            return i, table[t.lower()]
        if re.sub(r"^(ال|و|ب|ل)", "", t) in table:
            return i, table[re.sub(r"^(ال|و|ب|ل)", "", t)]
    return None
