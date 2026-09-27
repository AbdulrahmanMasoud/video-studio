import sys; sys.path.insert(0, '..')
from mkplan import Plan
p = Plan("flash-sale", "Flash sale! Everything is fifty percent off, but only for the next twenty four hours. Sneakers, hoodies, backpacks, all of it. Use code FLASH fifty at checkout. Go now.")
p.save({"music": {"mood": "edm", "drop": p.w("fifty")}, "data": {"tape": "FLASH SALE • 50% OFF • 24H ONLY • "}, "scenes": [
  {"type": "sale", "start": 0, "kicker": "FLASH SALE", "value": 50, "suffix": "%", "at": p.w("fifty"), "timer": {"seconds": 86400}, "fine": "Ends in 24 hours. While stocks last."},
  {"type": "items", "start": p.w("sneakers", off=-0.1), "currency": "$", "items": [
     {"name": "Sneakers", "price": 45, "old": 90, "at": p.w("sneakers")}, {"name": "Hoodie", "price": 30, "old": 60, "at": p.w("hoodies")},
     {"name": "Backpack", "price": 25, "old": 50, "at": p.w("backpacks")}, {"name": "Cap", "price": 10, "old": 20, "at": p.w("all")}]},
  {"type": "cta", "start": p.w("use", off=-0.1), "text": "Use code", "code": "FLASH50", "sub": "At checkout", "at": p.w("use")}
]})
p = Plan("cinema", "Every city has a heartbeat. In the early morning, before the noise, you can almost hear it. This is the story of the people who wake it up. The bakers. The drivers. The dreamers. The first light.")
p.save({"music": {"mood": "cinematic"}, "demoMedia": {"shot1": "video"}, "scenes": [
  {"type": "title", "start": 0, "kicker": "A SHORT FILM", "text": "The First Light", "at": 0.4},
  {"type": "shot", "start": p.w("in", off=-0.2), "media": "shot1", "kenburns": {"from": 1.02, "to": 1.15, "x": 0.4, "y": 0.4}},
  {"type": "chapter", "start": p.w("this", off=-0.2), "n": 1, "title": "The people who wake it up", "at": p.w("this")},
  {"type": "end", "start": p.w("the", 8, off=-0.2), "text": "The First Light", "sub": "Coming soon", "at": p.w("first")}
]})
p = Plan("journey", "In twenty fifteen I wrote my first line of code. Two years later I got my first job. In twenty twenty I started freelancing. Then in twenty twenty three I launched my own company. And this year we crossed one million users.")
p.save({"music": {"mood": "cinematic"}, "scenes": [
  {"type": "timeline", "start": 0, "title": "My journey", "events": [
     {"year": 2015, "label": "First line of code", "at": p.w("twenty")},
     {"year": 2017, "label": "First job", "at": p.w("two")},
     {"year": 2020, "label": "Started freelancing", "at": p.w("twenty", 3)},
     {"year": 2023, "label": "Launched my company", "at": p.w("twenty", 5)}]},
  {"type": "milestone", "start": p.w("and", off=-0.1), "from": 2015, "year": 2026, "title": "1,000,000 users", "text": "And we're just getting started", "at": p.w("and")}
]})
p = Plan("breaking", "Breaking news. A new AI model can now edit full videos from a single voice note. Here's what you need to know. First, it works in any language. Second, it exports in any size. And third, it's free to try today.")
p.save({"music": {"mood": "news"}, "data": {"channel": "TECH DAILY", "ticker": ["AI edits full videos from a voice note", "Works in any language", "Any aspect ratio", "Free to try today"]}, "scenes": [
  {"type": "headline", "start": 0, "label": "BREAKING NEWS", "title": "AI now edits full videos from a single voice note", "sub": "Here's what you need to know", "at": 0.2},
  {"type": "point", "start": p.w("first", off=-0.1), "text": "Works in any language", "kicker": "KEY POINT", "at": p.w("first")},
  {"type": "point", "start": p.w("second", off=-0.1), "text": "Exports in any size", "at": p.w("second")},
  {"type": "point", "start": p.w("and", off=-0.1), "text": "Free to try today", "at": p.w("third")}
]})
p = Plan("city-map", "One perfect day in Lisbon. Start with coffee in Alfama. Walk down to the river for lunch at Time Out Market. Then catch the sunset at the Miradouro. Five stars, would do it again.")
p.save({"music": {"mood": "acoustic"}, "scenes": [
  {"type": "map", "start": 0, "title": "One day in Lisbon", "seed": 11, "pins": [
     {"label": "Alfama café", "x": 0.75, "y": 0.25, "at": p.w("coffee")},
     {"label": "Time Out Market", "x": 0.3, "y": 0.6, "at": p.w("lunch")},
     {"label": "Miradouro", "x": 0.55, "y": 0.85, "at": p.w("sunset")}],
   "routeAt": p.w("sunset", off=0.8), "routeDur": 1.6},
  {"type": "place", "start": p.w("five", off=-0.1), "name": "Miradouro da Senhora do Monte", "tag": "SUNSET", "rating": 4.8, "text": "The best view in the city. Get there 30 minutes early.", "at": p.w("five")}
]})
p = Plan("recipe", "Garlic butter pasta in fifteen minutes. You need pasta, butter, garlic, parmesan, and parsley. Boil the pasta for ten minutes. Melt the butter and fry the garlic. Toss everything together with the cheese. That's it, dinner is ready.")
p.save({"music": {"mood": "jazzy"}, "scenes": [
  {"type": "title", "start": 0, "text": "Garlic butter pasta", "time": "15 min", "servings": "2", "at": 0.2},
  {"type": "ingredients", "start": p.w("you", off=-0.1), "items": [
     {"text": "Pasta", "qty": "200 g", "at": p.w("pasta", 2)}, {"text": "Butter", "qty": "3 tbsp", "at": p.w("butter", 2)},
     {"text": "Garlic", "qty": "4 cloves", "at": p.w("garlic", 2)}, {"text": "Parmesan", "qty": "50 g", "at": p.w("parmesan")}, {"text": "Parsley", "qty": "a handful", "at": p.w("parsley")}]},
  {"type": "step", "start": p.w("boil", off=-0.1), "text": "Boil the pasta", "timer": 600, "at": p.w("boil")},
  {"type": "step", "start": p.w("melt", off=-0.1), "text": "Melt butter, fry the garlic", "at": p.w("melt")},
  {"type": "step", "start": p.w("toss", off=-0.1), "text": "Toss with the cheese", "at": p.w("toss")},
  {"type": "final", "start": p.w("thats", off=-0.1), "text": "Dinner is ready!", "at": p.w("dinner")}
]})
p = Plan("workout", "Ten squats. Go. One, two, three, four, five, six, seven, eight, nine, ten. Great. Rest for fifteen seconds. Next up, a plank. Hold it for twenty seconds. You're done. Amazing work.")
reps = [p.w(x) for x in ["one","two","three","four","five","six","seven","eight","nine","ten"]]
reps[-1] = p.w("ten", 2)
p.save({"music": {"mood": "workout"}, "scenes": [
  {"type": "exercise", "start": 0, "name": "Squats", "set": "SET 1 / 3", "reps": 10, "repTimes": reps, "at": p.w("go")},
  {"type": "rest", "start": p.w("great", off=-0.1), "seconds": 15, "next": "Plank", "at": p.w("rest")},
  {"type": "exercise", "start": p.w("hold", off=-0.1), "name": "Plank", "seconds": 5, "at": p.w("hold")},
  {"type": "done", "start": p.w("youre", off=-0.1), "text": "Workout complete!", "sub": "Amazing work", "at": p.w("done")}
]})
p = Plan("review", "I used these headphones for a month. Here's my score: four point two out of five. The good: amazing battery life and great noise cancelling. The bad: they're heavy and the app is buggy. So should you buy them? Yes, if you travel a lot.")
p.save({"music": {"mood": "upbeat"}, "scenes": [
  {"type": "score", "start": 0, "product": "Wave X Headphones", "rating": 4.2, "max": 5, "at": p.w("four"), "sub": "After 30 days of daily use"},
  {"type": "pros", "start": p.w("the", 1, off=-0.1), "items": [{"text": "Amazing battery life", "at": p.w("amazing")}, {"text": "Great noise cancelling", "at": p.w("great")}]},
  {"type": "cons", "start": p.w("the", 2, off=-0.1), "items": [{"text": "Heavy", "at": p.w("heavy")}, {"text": "Buggy app", "at": p.w("buggy")}]},
  {"type": "verdict", "start": p.w("so", off=-0.1), "text": "BUY IT", "positive": True, "sub": "If you travel a lot", "at": p.w("yes")}
]})
