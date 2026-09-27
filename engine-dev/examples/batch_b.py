import sys; sys.path.insert(0, '..')
from mkplan import Plan
p = Plan("chat", "I asked AI to plan my week and it actually worked. I typed: plan my week, I have a job, the gym three times, and a side project. It asked me one question: when do you have the most energy? I said mornings. Then it gave me a full schedule with deep work in the morning and the gym after work. Try it yourself.")
p.save({"music": {"mood": "lofi"}, "scenes": [
  {"type": "chat", "start": 0, "title": "AI Assistant", "messages": [
     {"from": "user", "text": "Plan my week. I have a job, the gym 3x, and a side project.", "at": p.w("plan", 2), "end": p.we("project")},
     {"from": "ai", "text": "Happy to! One question first: when do you have the most energy?", "at": p.w("it", 2), "end": p.we("energy"), "think": 0.6},
     {"from": "user", "text": "Mornings", "at": p.w("i", 4), "end": p.we("mornings"), "react": "heart"},
     {"from": "ai", "text": "Here's your week:\n• 7–9am deep work on the side project\n• 9–5 job\n• Mon/Wed/Fri gym after work\n• Sunday: review & plan", "at": p.w("then"), "end": p.we("work", 2)}]},
  {"type": "result", "start": p.w("try", off=-0.1), "title": "Try it yourself", "text": "Tell it your constraints, let it ask questions, then ask for the schedule.", "at": p.w("try")}
]})
p = Plan("terminal", "Want to see your whole project in one command? Run npx create app, pick a name, and it installs everything. Three seconds later, it's done. Start the dev server and you're live on localhost. If you see an error about the port, just change it. That's it.")
p.save({"music": {"mood": "ambient"}, "scenes": [
  {"type": "terminal", "start": 0, "title": "~/projects — zsh", "lines": [
     {"text": "npx create-app my-site", "kind": "cmd", "at": p.w("run"), "end": p.we("app")},
     {"text": "? Project name › my-site", "kind": "out", "at": p.w("pick")},
     {"text": "Installing dependencies…", "kind": "out", "at": p.w("installs")},
     {"text": "added 312 packages in 3s", "kind": "ok", "at": p.w("three")},
     {"text": "npm run dev", "kind": "cmd", "at": p.w("start"), "end": p.we("server")},
     {"text": "ready - local: http://localhost:3000", "kind": "hl", "at": p.w("live")},
     {"text": "Error: port 3000 already in use", "kind": "err", "at": p.w("if")}],
   "zoomAt": p.w("live"), "zoomEnd": p.w("if")},
  {"type": "callout", "start": p.w("just", off=-0.1), "kind": "ok", "title": "Change the port", "text": "npm run dev -- --port 3001", "at": p.w("just")}
]})
p = Plan("counter", "Here's a number that shocked me. Ninety-one percent of people who start a new habit quit within the first month. But look at this. People who track their habit daily are three times more likely to stick with it. Tracking beats motivation.")
p.save({"music": {"mood": "corporate", "drop": p.w("ninetyone")}, "scenes": [
  {"type": "stat", "start": 0, "value": 91, "suffix": "%", "chart": "ring", "max": 100, "label": "quit a new habit", "sub": "within the first month", "at": p.w("ninetyone"), "dur": 1.6, "source": "Illustrative data"},
  {"type": "stat", "start": p.w("but", off=-0.1), "value": 3, "suffix": "×", "chart": "bars", "bars": [1, 1.2, 1.6, 2.1, 3], "label": "more likely to stick with it", "at": p.w("three"), "dur": 1.2},
  {"type": "compare", "start": p.w("tracking", off=-0.1), "title": "What keeps habits alive", "at": p.w("tracking"), "items": [
     {"label": "Daily tracking", "value": 78, "suffix": "%"}, {"label": "Motivation", "value": 26, "suffix": "%"}, {"label": "Willpower", "value": 19, "suffix": "%"}]}
]})
p = Plan("top-five", "Top five apps I can't live without. Number five: a notes app that syncs everywhere. Number four: a password manager. Number three: a calendar that plans itself. Number two: a focus timer. And number one: an AI assistant that does all of the above.")
p.save({"music": {"mood": "upbeat"}, "scenes": [
  {"type": "intro", "start": 0, "n": 5, "title": "Apps I can't live without", "at": p.w("top")},
  {"type": "rank", "start": p.w("number", 1, off=-0.15), "n": 5, "title": "Notes app", "subtitle": "Syncs everywhere", "at": p.w("five", 2)},
  {"type": "rank", "start": p.w("number", 2, off=-0.15), "n": 4, "title": "Password manager", "at": p.w("four")},
  {"type": "rank", "start": p.w("number", 3, off=-0.15), "n": 3, "title": "Smart calendar", "subtitle": "Plans itself", "at": p.w("three")},
  {"type": "rank", "start": p.w("number", 4, off=-0.15), "n": 2, "title": "Focus timer", "at": p.w("two")},
  {"type": "rank", "start": p.w("and", off=-0.6), "n": 1, "title": "AI assistant", "subtitle": "Does all of the above", "at": p.w("one")}
]})
