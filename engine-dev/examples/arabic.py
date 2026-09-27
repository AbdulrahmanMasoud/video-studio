"""Arabic (RTL) example plans: saved as examples/plan.ar.json. Run smoke with --plan plan.ar.json"""
import sys, json; sys.path.insert(0, '..')
from mkplan import Plan, SK
def save(p, plan):
    plan = dict(plan); plan["lang"] = "ar"; plan["demoScript"] = p.script
    (SK / p.t / "examples" / "plan.ar.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); print("wrote", p.t)
p = Plan("quiz", "سؤال سريع. أنهي كوكب هو الأسخن في المجموعة الشمسية؟ عطارد، الزهرة، المريخ، ولا المشتري؟ معاك تلات ثواني. تلاتة، اتنين، واحد. الإجابة الزهرة!", "ar")
save(p, {"labels": {"question": "سؤال", "letters": "أبجدهو", "why": "ليه؟", "score": "جبتها صح؟"}, "scenes": [{"type": "question", "start": 0, "at": p.w("أنهي"), "q": "أنهي كوكب هو الأسخن؟", "options": [{"text": "عطارد", "at": p.w("عطارد")}, {"text": "الزهرة", "at": p.w("الزهرة")}, {"text": "المريخ", "at": p.w("المريخ")}, {"text": "المشتري", "at": p.w("المشتري")}], "answer": 1, "countdownAt": p.w("تلاتة"), "seconds": 3, "revealAt": p.w("الإجابة")}]})
p = Plan("steps", "الذكاء الاصطناعي ذكي جدًا، بس مش بيقرا أفكارك. عشان كده عندي أربع حاجات هتفرق معاك. أولًا: كون واضح. ثانيًا: اديله السياق. مين إنت؟ ولمين؟ وليه؟", "ar")
save(p, {"scenes": [
  {"type": "hook", "start": 0, "title": "إزاي تكتب برومبت كويس؟", "icon": "robot"},
  {"type": "count", "start": p.w("عشان", off=-0.1), "n": 4, "at": p.w("أربع"), "text": "حاجات هتفرق معاك", "textAt": p.w("حاجات")},
  {"type": "step", "start": p.w("أولًا", off=-0.1), "short": "وضوح", "title": "كون واضح", "card": {"kind": "prompt", "bad": {"text": "اكتب بوست", "at": p.w("كون"), "end": p.we("واضح")}, "good": {"text": "اكتب بوست إنستجرام لمخبزي", "at": p.we("واضح", off=0.3)}}},
  {"type": "step", "start": p.w("ثانيًا", off=-0.1), "short": "السياق", "title": "اديله السياق", "card": {"kind": "list", "items": [{"text": "مين إنت؟", "at": p.w("مين")}, {"text": "لمين؟", "at": p.w("ولمين")}, {"text": "ليه؟", "at": p.w("وليه")}]}}]})
p = Plan("echo", "محدش جاي ينقذك. مش مديرك. مش الخوارزمية. مش الحظ. كل خطوة صغيرة بتعملها النهارده هي صوت للشخص اللي عايز تبقاه.", "ar")
save(p, {"scenes": [{"type": "flow", "start": 0, "emphasis": ["محدش", "ينقذك", "الحظ"]}]})
p = Plan("journey", "في ألفين خمستاشر كتبت أول سطر كود. بعدها بسنتين اشتغلت أول شغلانة. وفي ألفين عشرين بدأت فريلانس.", "ar")
save(p, {"scenes": [{"type": "timeline", "start": 0, "title": "رحلتي", "events": [{"year": 2015, "label": "أول سطر كود", "at": p.w("ألفين")}, {"year": 2017, "label": "أول شغلانة", "at": p.w("بعدها")}, {"year": 2020, "label": "بدأت فريلانس", "at": p.w("ألفين", 2)}]}]})
