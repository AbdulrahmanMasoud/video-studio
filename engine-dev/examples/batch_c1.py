import sys; sys.path.insert(0, '..')
from mkplan import Plan
p = Plan("mirror", "Stop saying sorry in your emails. Seriously. Sorry for the late reply makes you sound small. Instead, say thank you for your patience. Same message, but now you sound confident. Try it on your next email and watch how people respond.")
p.save({"music": {"mood": "lofi"}, "scenes": [
  {"type": "title", "start": 0, "text": "Stop saying sorry", "sub": "Email tip #1", "at": 0.1, "end": p.w("seriously")},
  {"type": "talk", "start": p.w("seriously", off=-0.05), "zooms": [{"at": p.w("seriously"), "end": p.we("seriously", off=0.2), "scale": 1.35, "snap": True}],
   "stickers": [{"text": "Sorry for the late reply", "icon": "x", "at": p.w("sorry", 2), "end": p.we("small"), "color": "alt"},
                {"text": "Thank you for your patience", "icon": "check", "at": p.w("thank"), "end": p.we("confident")}]},
  {"type": "lower", "start": p.w("try", off=-0.05), "name": "Sara Adel", "role": "Communication coach", "at": p.w("try"), "end": p.we("respond")}
]})
p = Plan("storytime", "Three years ago I quit my job with no plan. Everyone told me I was crazy. The first six months were the hardest of my life. I sold my car. I moved back in with my parents. But then one small client turned into ten. And today I run a team of twelve. So if you're scared, that's normal. Start anyway.")
p.save({"music": {"mood": "piano", "drop": p.w("but")}, "scenes": [
  {"type": "chapter", "start": 0, "n": 1, "title": "The day I quit", "at": 0.1, "hold": p.w("everyone")},
  {"type": "talk", "start": p.w("everyone", off=-0.05), "note": "“You're crazy.”", "noteAt": p.w("crazy")},
  {"type": "photo", "start": p.w("i", 3, off=-0.05), "caption": "Bye, car", "at": p.w("sold"), "end": p.w("but")},
  {"type": "chapter", "start": p.w("but", off=-0.05), "n": 2, "title": "One client became ten", "at": p.w("but"), "hold": p.w("and")},
  {"type": "talk", "start": p.w("and", off=-0.05), "note": "Team of 12", "noteAt": p.w("twelve")},
  {"type": "end", "start": p.w("so", off=-0.05), "text": "Start anyway.", "sub": "Scared is normal", "at": p.w("start")}
]})
p = Plan("podcast", "So what's the biggest mistake new founders make? Honestly, building for months before talking to a single customer. You fall in love with the idea. Right, and by the time you launch nobody wants it. Exactly. Talk to ten customers before you write one line of code.")
p.save({"music": {"mood": "none"}, "data": {"show": "The Build Show", "speakers": [{"name": "Omar", "role": "Host"}, {"name": "Lina", "role": "Founder, Nodebox"}]}, "scenes": [
  {"type": "split", "start": 0, "turns": [
     {"who": 0, "start": 0, "end": p.we("make", off=0.15)},
     {"who": 1, "start": p.w("honestly", off=-0.1), "end": p.we("idea", off=0.15)},
     {"who": 0, "start": p.w("right", off=-0.1), "end": p.we("it", 1, off=0.15)},
     {"who": 1, "start": p.w("exactly", off=-0.1), "end": 999}]},
  {"type": "quote", "start": p.w("talk", off=-0.1), "text": "Talk to ten customers before you write one line of code.", "who": "Lina, Founder of Nodebox", "at": p.w("talk")}
]})
