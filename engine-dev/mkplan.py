"""Dev helper for writing examples/plan.example.json files.

    from mkplan import Plan
    p = Plan("quiz", "Which planet is the hottest? ...")
    p.w("hottest")        -> "w:3"   (start of the first word of the phrase)
    p.we("hottest")       -> "we:3"  (end of the last word of the phrase)
    p.w("the", 2)         -> 2nd occurrence
    p.save({...plan...})  -> writes engine/<tpl>/examples/plan.example.json
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / "engine"


def norm(s):
    return re.sub(r"[^\w]+", "", s.lower())


class Plan:
    def __init__(self, template, script, lang="en"):
        self.t, self.script, self.lang = template, script, lang
        self.toks = script.split()
        self.n = [norm(x) for x in self.toks]

    def find(self, phrase, occ=1):
        ph = [norm(x) for x in phrase.split()]
        hits = [i for i in range(len(self.n)) if self.n[i:i + len(ph)] == ph]
        if len(hits) < occ:
            raise SystemExit(f"[{self.t}] phrase not found: {phrase!r} (occurrence {occ})")
        return hits[occ - 1], hits[occ - 1] + len(ph) - 1

    def w(self, phrase, occ=1, off=None):
        i = self.find(phrase, occ)[0]
        return f"w:{i}" + (f"{off:+g}" if off else "")

    def we(self, phrase, occ=1, off=None):
        i = self.find(phrase, occ)[1]
        return f"we:{i}" + (f"{off:+g}" if off else "")

    def save(self, plan):
        plan = dict(plan)
        plan.setdefault("lang", self.lang)
        plan["demoScript"] = self.script
        d = SK / self.t / "examples"
        d.mkdir(parents=True, exist_ok=True)
        (d / "plan.example.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("wrote", d / "plan.example.json")
