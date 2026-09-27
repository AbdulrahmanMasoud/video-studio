import sys; sys.path.insert(0, '..')
from mkplan import Plan
p = Plan("screen", "Here's how to set up your first project in thirty seconds. Click new project in the top right. Give it a name and pick a template. Then hit create, and that's it, your workspace is ready.")
p.save({"music": {"mood": "corporate"}, "demoMedia": {"screen": "video"}, "scenes": [
  {"type": "step", "start": 0, "n": 1, "text": "Your first project in 30 seconds", "at": 0.1},
  {"type": "demo", "start": p.w("click", off=-0.4), "device": "browser", "url": "app.example.com/projects", "clicks": [
     {"x": 0.85, "y": 0.06, "at": p.w("click"), "label": "New project", "end": p.we("right")},
     {"x": 0.4, "y": 0.45, "at": p.w("name"), "label": "Name it", "end": p.we("template"), "zoom": 1.4},
     {"x": 0.78, "y": 0.9, "at": p.w("create"), "label": "Create", "end": p.we("ready")}]}
]})
p = Plan("showcase", "Meet Aura, the water bottle that reminds you to drink. It glows when it's time for a sip, keeps drinks cold for twenty four hours, and tracks every ounce in the app. All for just thirty nine dollars. Get yours today.")
p.save({"music": {"mood": "upbeat", "drop": p.w("meet")}, "scenes": [
  {"type": "product", "start": 0, "name": "Aura Bottle", "tagline": "The bottle that reminds you to drink", "badge": "NEW", "at": p.w("meet"),
   "features": [{"text": "Glows to remind you", "at": p.w("glows"), "icon": "bolt"}, {"text": "Cold for 24h", "at": p.w("keeps"), "icon": "clock"}, {"text": "Tracks in the app", "at": p.w("tracks"), "icon": "check"}],
   "price": 39, "oldPrice": 59, "currency": "$", "priceAt": p.w("thirty")},
  {"type": "cta", "start": p.w("get", off=-0.1), "text": "Get yours today", "button": "Shop now", "sub": "Free shipping this week", "at": p.w("get")}
]})
p = Plan("before-after", "This is my desk before. Cables everywhere, no light, and I could never focus. One weekend and eighty dollars later, here's the after. Clean, bright, and I actually want to work here now. Here's what changed. Cable tray, one lamp, and a monitor arm.")
p.save({"music": {"mood": "upbeat"}, "demoMedia": {"before_img": "image", "after_img": "video"}, "scenes": [
  {"type": "compare", "start": 0, "at": 0.1, "wipeAt": p.w("heres"), "before": {"label": "BEFORE", "media": "before_img"}, "after": {"label": "AFTER", "media": "after_img"}},
  {"type": "split", "start": p.w("heres", 2, off=-0.1), "at": p.w("heres", 2), "afterAt": p.w("cable"),
   "before": {"label": "BEFORE", "items": ["Cables everywhere", "No light", "Can't focus"]},
   "after": {"label": "AFTER", "items": ["Cable tray", "One lamp", "Monitor arm"]}}
]})
