import sys; sys.path.insert(0, '..')
from mkplan import Plan
p = Plan("quiz", "Quick quiz. Which planet is the hottest in our solar system? Is it Mercury, Venus, Mars, or Jupiter? You have three seconds. Three, two, one. It's Venus! Even though Mercury is closer to the sun, Venus has a thick atmosphere that traps heat like a blanket. How many did you get right? Comment below.")
p.save({"music": {"mood": "game"}, "scenes": [
  {"type": "question", "start": 0, "at": p.w("which"), "q": "Which planet is the hottest?",
   "options": [{"text": "Mercury", "at": p.w("mercury")}, {"text": "Venus", "at": p.w("venus")}, {"text": "Mars", "at": p.w("mars")}, {"text": "Jupiter", "at": p.w("jupiter")}],
   "answer": 1, "countdownAt": p.w("three", 2), "seconds": 3, "revealAt": p.w("its")},
  {"type": "explain", "start": p.w("even", off=-0.1), "title": "Thick atmosphere", "text": "Venus is farther from the Sun than Mercury, but its CO2 blanket traps the heat: about 465°C.", "at": p.w("even"), "icon": "fire"},
  {"type": "score", "start": p.w("how", off=-0.1), "total": 1, "text": "Did you get it right?", "at": p.w("how")}
]})
p = Plan("verdict", "You only use ten percent of your brain. You've heard this a million times. It's a myth. Brain scans show that almost every region is active during a normal day. Even simple tasks light up large areas. And damage to almost any part causes problems. So no hidden ninety percent. Busted.")
p.save({"music": {"mood": "tension"}, "scenes": [
  {"type": "claim", "start": 0, "myth": "You only use 10% of your brain", "mythAt": p.w("you"), "stampAt": p.w("myth"),
   "fact": "Almost every region of your brain is active every day", "factAt": p.w("brain", 2)},
  {"type": "reason", "start": p.w("even", off=-0.1), "title": "Why we know", "points": [
     {"text": "Scans show activity everywhere", "at": p.w("even")},
     {"text": "Simple tasks light up large areas", "at": p.w("light")},
     {"text": "Damage anywhere causes problems", "at": p.w("damage")}]},
  {"type": "stamp", "start": p.w("so", off=-0.1), "kind": "myth", "text": "BUSTED", "sub": "No hidden 90%", "at": p.w("busted")}
]})
p = Plan("hot-take", "Unpopular opinion. Morning routines are overrated. You don't need to wake up at five to be successful. What matters is what you do with your best hours, whenever they are. I asked a thousand people and most of them agreed. So what do you think? Tell me in the comments.")
p.save({"music": {"mood": "edm", "drop": p.w("morning")}, "scenes": [
  {"type": "take", "start": 0, "kicker": "Unpopular opinion", "text": "Morning routines are overrated", "highlight": ["overrated"], "at": p.w("morning")},
  {"type": "take", "start": p.w("what", off=-0.1), "kicker": "What matters", "text": "Your best hours, whenever they are", "highlight": ["best", "hours"], "at": p.w("what")},
  {"type": "poll", "start": p.w("i", off=-0.1), "question": "Are morning routines overrated?", "at": p.w("asked"),
   "options": [{"label": "Yes, overrated", "pct": 64}, {"label": "No, they work", "pct": 29}, {"label": "Depends", "pct": 7}], "fillAt": p.w("most")},
  {"type": "cta", "start": p.w("so", off=-0.1), "text": "What do you think?", "sub": "Tell me in the comments", "at": p.w("what", 3)}
]})
p = Plan("echo", "Nobody is coming to save you. Not your boss. Not the algorithm. Not luck. Every small step you take today is a vote for the person you want to become. So start before you are ready. Start now.")
p.save({"music": {"mood": "cinematic", "drop": p.w("every")}, "scenes": [
  {"type": "flow", "start": 0, "emphasis": ["nobody", "save", "luck"]},
  {"type": "words", "start": p.w("every", off=-0.1), "items": [
     {"text": "Every small step", "at": p.w("every")},
     {"text": "is a vote", "at": p.w("is", 2), "style": "accent"},
     {"text": "for who", "at": p.w("for"), "style": "small"},
     {"text": "you become", "at": p.w("want"), "style": "huge"},
     {"text": "Start before", "at": p.w("start"), "clear": True},
     {"text": "you are ready", "at": p.w("you", 4), "style": "strike", "strikeAt": p.w("start", 2)},
     {"text": "Start now.", "at": p.w("start", 2), "style": "huge"}]}
]})
