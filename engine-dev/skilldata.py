# Source data for generating each template's SKILL.md (dev/gen_skills.py). Edit here, then regenerate.
T = {}

T["steps"] = dict(
 title="Steps", tag="numbered tips with a progress tracker",
 desc="Turn a voice note, video or script into a polished numbered-tips video (\"3 ways to…\", \"4 steps to…\", how-to, tutorial, prompt tips) with a step tracker, typed prompt cards with bad→good rewrites, lists and A/B toggles.",
 look="Bold cobalt background, a pill tracker that fills as each step is covered, a big number count-in, and one visual card per step: a typed prompt (with an \"unclear\" stamp on the bad version and highlights on the good one), a list, A/B toggles or a statement card.",
 when="Any content with a clear sequence of tips, steps or rules.",
 extra_intake="How many steps/tips the video covers (usually obvious from the script).",
 pace="tight",
 rules=["Open with `hook` (the promise/title, ≤ 6 words) for the first sentence.",
        "Use `count` when the speaker announces the number of tips; anchor `at` on the number word.",
        "One `step` per tip. `short` is 1 word for the tracker. Pick the card kind that shows the tip: `prompt` for before/after wording, `list` for questions/ingredients, `toggles` for choices, `text` for a one-liner.",
        "Close with `outro` (the takeaway; `strikeAt` crosses out a misconception like \"magic\")."],
 scenes=[("hook","`title`, `icon` (robot, bulb, question, star, none), `at`, `beats` [{`at`, `kind`: sparkle|confused}]"),
         ("count","`n`, `at` (number slam), `text`, `textAt`"),
         ("step","`n` (auto), `short` (tracker label), `title`, `card`: `{kind:'prompt', label, bad:{text,at,end,stamp}, good:{text,at,end}, highlights:[{text,at}]}` · `{kind:'list', items:[{text,at,icon}]}` · `{kind:'toggles', items:[{a,b,at,flipAt}]}` · `{kind:'text', text, at}`"),
         ("outro","`kicker`, `strikeAt`, `label`, `text`, `highlight`, `textAt`, `cta`")],
 labels=["prompt", "unclear"], arabic=True)

T["whiteboard"] = dict(
 title="Whiteboard", tag="an explainer that draws itself",
 desc="Make a whiteboard / sketch explainer video from a recording or script: hand-drawn titles, boxes and arrows that draw themselves, checklists, comparisons and circled key notes, synced to the voice. Use for concepts, processes, frameworks, \"how X works\".",
 look="Off-white grid paper, marker strokes in ink and red, handwritten type, karaoke captions. Diagrams draw box by box as they are mentioned.",
 when="Explaining a concept, process, loop or framework; teaching.",
 extra_intake="", pace="natural",
 rules=["Start with `title` (the question the video answers).",
        "Use `diagram` for processes (2–5 nodes; `layout` vertical/horizontal/cycle; `circle` highlights the key node).",
        "Use `list` for checklists, `compare` for two options, `note` for the final takeaway (it gets circled)."],
 scenes=[("title","`text`, `at`, `underlineAt`"),
         ("diagram","`title`, `nodes` [{`text`, `at`, `color`: accent}], `layout` vertical|horizontal|cycle, `arrows` (false to hide), `circle` {`index`, `at`}"),
         ("list","`title`, `items` [{`text`, `at`, `checkAt`, `check`: false}]"),
         ("compare","`title`, `left` {`title`, `items`, `at`}, `right` {…}"),
         ("note","`text`, `at`, `circleAt`")],
 labels=[])

T["quiz"] = dict(
 title="Quiz", tag="question, options, countdown and reveal",
 desc="Create an interactive quiz / trivia / \"guess the answer\" video: question card, A-D options that pop in on the voice, a countdown ring with ticks, and a green reveal of the correct answer, plus an explanation card and a score screen.",
 look="Violet gradient with drifting question marks, white cards, a yellow countdown ring that turns red, and a satisfying correct/incorrect reveal.",
 when="Trivia, test-your-knowledge, \"can you guess\", educational checks.",
 extra_intake="The correct answer for each question (confirm if the script doesn't say it).", pace="tight",
 rules=["One `question` per question; anchor each option's `at` to the word that says it.",
        "`countdownAt` on the \"3, 2, 1\" (or leave a 2–3 s pause); `revealAt` on the word that gives the answer.",
        "Follow with `explain` (why) and optionally end with `score`."],
 scenes=[("question","`q`, `options` [{`text`, `at`}] or strings, `answer` (0-based index), `at`, `optionsAt`, `countdownAt`, `seconds` (3), `revealAt`, `countdown` (false to hide), `label`"),
         ("explain","`title`, `text`, `icon`, `at`"),
         ("score","`total`, `score`, `text`, `at`")],
 labels=["question", "letters (option letters, e.g. \"أبجد\")", "why", "score"], arabic=True)

T["before-after"] = dict(
 title="Before / After", tag="transformations with a wipe reveal",
 desc="Make a before/after transformation video (makeover, redesign, room/desk setup, fitness progress, code refactor, photo edit): a wipe slider reveals the after image or clip, or two cards compare bullet points side by side.",
 look="Dark frame, red BEFORE / green AFTER chips, a white divider with a handle that teases, then sweeps across.",
 when="Anything with a clear before state and after state.",
 extra_intake="The before and after images/clips (or the list of differences if there are no images).", pace="tight",
 rules=["Register the images/clips first: `vt.py media JOB --name before_img --image before.jpg` and `--name after_img …`.",
        "`compare` with `wipeAt` on the word that introduces the result (\"here's the after\").",
        "Follow with `split` to list what changed (anchor `afterAt` to the first change)."],
 scenes=[("compare","`before` {`label`, `media`, `items`, `text`}, `after` {…}, `at`, `wipeAt`, `wipeDur`, `full` (edge-to-edge)"),
         ("split","`before` {`label`, `items`}, `after` {…}, `at`, `afterAt`")],
 labels=["before", "after"], media=["before/after images or clips (any names)"])

T["mirror"] = dict(
 title="Mirror", tag="talking-head edit",
 desc="Edit a talking-head / face-to-camera video like a pro creator: removes pauses and stumbles, punch-in zooms on every jump cut, one-word pop captions, emphasis zooms, sticker callouts, headline cards and lower-third name tags.",
 look="The user's footage full-frame with alternating 1.0×/1.12× punch-ins on each cut, big yellow pop captions, bold stickers and a clean white headline.",
 when="The user recorded themselves talking to camera.",
 extra_intake="The camera video (required). Whether they want their name/title shown.", pace="tight",
 rules=["`init --input video.mp4`, then `transcribe`, `analyze`, `edit` (cuts both audio and footage), then `vt.py media JOB --name cam`.",
        "Split the video into `talk` scenes by idea. Add `zooms` (snap: true) on punchlines, `stickers` for key phrases (≤ 5 words).",
        "Open with `title` over the first sentence; add `lower` once, early, if the speaker should be introduced."],
 scenes=[("talk","`zooms` [{`at`, `end`, `scale` (1.3), `x`, `y` (0–1 focus), `snap`}], `stickers` [{`text`, `at`, `end`, `icon`, `pos` top|middle, `color`}]"),
         ("title","`text`, `sub`, `at`, `end`"),
         ("lower","`name`, `role`, `at`, `end`")],
 labels=[], media=["`cam` (the edited camera video: `vt.py media JOB --name cam`)"], data="`data.punch: false` disables automatic punch-ins; `data.cam` renames the camera media.")

T["podcast"] = dict(
 title="Podcast", tag="podcast / interview clips",
 desc="Turn a podcast, interview or conversation into a vertical or landscape clip: split speaker panels (video or avatars) that light up on whoever is talking, live audio meters, an ON AIR badge with the show name, pull-quote cards and solo views.",
 look="Dark studio, rounded speaker panels with a red active-speaker ring, boxed captions, show badge on top.",
 when="Two or three people talking; interview or podcast highlights.",
 extra_intake="Speaker names (and roles), who speaks when (or let transcription + listening decide), show name, per-speaker footage if any.", pace="natural",
 rules=["Put speakers in `data.speakers` [{`name`, `role`, `media`}] and the show name in `data.show`.",
        "Use `split` with `turns` [{`who`, `start`, `end`}] covering who talks when (anchor to words).",
        "Cut to `quote` for the most shareable sentence; `solo` for a long answer by one speaker."],
 scenes=[("split","`speakers` (else `data.speakers`), `turns` [{`who`, `start`, `end`}], `speaker` (default active)"),
         ("solo","`who`, `media`"),
         ("quote","`text`, `who`, `at`")],
 labels=["onair"], media=["one video per speaker (optional), e.g. `--name host`, `--name guest`"], data="`data.speakers`, `data.show`, `data.badge`.")

T["storytime"] = dict(
 title="Storytime", tag="personal stories",
 desc="Edit a personal story / storytime / life-lesson video: warm color-graded footage (or voice-only), chapter title cards, polaroid photos that drop in, handwritten notes and a closing card.",
 look="Warm film grade and light leaks, serif chapter cards, polaroids with tape, karaoke captions in amber.",
 when="Narrative content: \"the day I…\", journeys, lessons, confessions.",
 extra_intake="Camera video or voice; any photos to include.", pace="natural",
 rules=["Break the story into 2–4 `chapter`s; `hold` controls how long the card covers the footage.",
        "Between chapters use `talk` (optionally with a short handwritten `note`).",
        "Drop a `photo` when the story mentions a person/place/object (register with `media --image`).",
        "End with `end` (the lesson in ≤ 5 words)."],
 scenes=[("chapter","`n`, `kicker`, `title`, `at`, `hold`"),
         ("talk","`note`, `noteAt`, `noteEnd`"),
         ("photo","`media`, `caption`, `at`, `end`, `rotate`"),
         ("end","`text`, `sub`, `at`")],
 labels=["chapter", "end"], media=["`cam` (optional), photos by name"])

T["verdict"] = dict(
 title="Verdict", tag="myth vs fact",
 desc="Make a myth-busting / \"true or false\" / fact-check video: the claim appears and gets stamped MYTH with a buzzer, the real fact slides in with a check, reasons stack up, and a BUSTED or TRUE stamp lands at the end.",
 look="Dark charcoal with red and green glows; cream cards, MYTH/FACT tags, strike-through on the myth.",
 when="Correcting a misconception, fact-checking, \"stop believing…\".",
 extra_intake="The myth and the correct fact (verify facts; do not invent statistics).", pace="tight",
 rules=["`claim`: `mythAt` when the myth is stated, `stampAt` when the speaker says it's false, `factAt` when the truth is given.",
        "`reason` lists the evidence (≤ 3 points).", "Finish with `stamp` (BUSTED / TRUE / PARTLY TRUE)."],
 scenes=[("claim","`myth`, `fact`, `mythAt`, `stampAt`, `factAt`"),
         ("reason","`title`, `points` [{`text`, `at`, `kind`: fact|myth, `icon`}]"),
         ("stamp","`text`, `kind` myth|fact, `sub`, `at`")],
 labels=["myth", "fact", "busted"])

T["hot-take"] = dict(
 title="Hot Take", tag="bold opinions",
 desc="Make a hot take / unpopular opinion / controversial statement video built for comments: fiery kicker, words that slam in one by one, a live poll with animated bars, and a comment call-to-action.",
 look="Near-black with rising embers and diagonal stripes, huge uppercase statement with highlighted words, one-word pop captions.",
 when="Opinions, debates, \"unpopular opinion\", engagement bait done tastefully.",
 extra_intake="", pace="tight",
 rules=["`take` for the statement (≤ 8 words, `highlight` 1–2 words). A second `take` can give the reason.",
        "`poll` with plausible percentages the user provides (label them as illustrative if invented).",
        "End with `cta` inviting comments."],
 scenes=[("take","`kicker`, `text`, `highlight` [words], `at`, `stagger`, `upper`"),
         ("poll","`question`, `options` [{`label`, `pct`, `at`}], `at`, `fillAt`"),
         ("cta","`text`, `sub`, `at`")],
 labels=["kicker", "cta", "ctaSub"])

T["chat"] = dict(
 title="AI Chat", tag="AI conversations",
 desc="Show an AI chat conversation as a video: a chat window where the user's messages send, the AI shows typing dots then streams its reply, with reactions and auto-scroll, plus a result card. Great for prompt demos, \"I asked ChatGPT/Claude…\" and AI tips.",
 look="Dark gradient with soft color blobs, a light chat window, indigo user bubbles, white AI bubbles, typing status in the header.",
 when="Demonstrating prompts, AI answers, chatbot flows, DMs.",
 extra_intake="The exact messages to show (user and AI).", pace="tight",
 rules=["One `chat` scene holds the whole exchange; anchor each message's `at`/`end` to when the voice says it.",
        "Keep AI replies short (≤ 5 lines); use `\\n•` for bullet lines.", "End with `result` summarizing the takeaway."],
 scenes=[("chat","`title`, `messages` [{`from`: user|ai, `text`, `at`, `end`, `think` (typing-dots seconds), `react`: heart|star|fire|check}]"),
         ("result","`title`, `text`, `icon`, `at`")],
 labels=["assistant", "typing", "online"])

T["terminal"] = dict(
 title="Terminal", tag="developer / CLI demos",
 desc="Create a coding / command-line / developer tutorial video: a terminal window where commands type themselves, output prints in color (success, errors, warnings, highlights), the camera zooms into key lines, and callout cards explain the fix.",
 look="Deep navy with a subtle moving grid, macOS-style terminal, green prompt, monospace font, boxed captions.",
 when="CLI tools, install guides, git, npm, Python, DevOps, error fixes.",
 extra_intake="The exact commands and outputs to show.", pace="tight",
 rules=["One `terminal` scene per session; `cmd` lines type between `at` and `end`; outputs appear at `at`.",
        "Use `zoomAt`/`zoomEnd` on the line the voice explains.", "Use `callout` for the key takeaway or fix."],
 scenes=[("terminal","`title`, `prompt` (\"$ \"), `fontSize` (U), `lines` [{`text`, `kind`: cmd|out|ok|err|warn|hl|comment, `at`, `end`}], `zoomAt`, `zoomEnd`, `zoom`"),
         ("callout","`title`, `text`, `sub`, `kind` ok|err|warn|info, `icon`, `at`")],
 labels=[])

T["screen"] = dict(
 title="Screen Demo", tag="app & website walkthroughs",
 desc="Turn a screen recording into a polished app / website / SaaS walkthrough: the recording inside a browser or phone frame, an animated cursor that glides to each click, click ripples, callout labels and camera zooms, plus numbered step cards.",
 look="Light lavender background, realistic browser chrome or phone bezel, dark callout labels, indigo accents.",
 when="Product demos, feature tours, onboarding, how-to-use-this-app.",
 extra_intake="The screen recording (or screenshots) and where the important clicks are.", pace="natural",
 rules=["Register the recording: `vt.py media JOB --name screen --video rec.mp4` (`mediaOffset` to skip).",
        "Clicks use `x`/`y` as fractions of the screen (0–1). Anchor `at` to the word describing the action.",
        "Insert `step` cards between parts of a longer demo."],
 scenes=[("demo","`device` browser|phone|none, `media` (screen), `url`, `title`, `ratio`, `clicks` [{`x`, `y`, `at`, `end`, `label`, `zoom` (1.3)}], `mediaOffset`"),
         ("step","`n`, `text`, `at`")],
 labels=[], media=["`screen` (the recording or a screenshot)"])

T["showcase"] = dict(
 title="Showcase", tag="product ads",
 desc="Make a product ad / launch / promo video: the product floats on a lit pedestal, feature chips pop in, the price slams in with the old price struck out, and a tap-the-button CTA closes it. Works with a product photo (PNG cutout ideal) or a placeholder.",
 look="Warm studio white, soft glow, black price tag, orange accent, bright pop music.",
 when="E-commerce, launches, merch, apps, services.",
 extra_intake="Product name, price and currency, 2–4 features, product image, the CTA wording.", pace="tight",
 rules=["Register the product image: `vt.py media JOB --name product --image product.png`.",
        "`product` with `features` anchored to the words; `priceAt` on the price.", "End with `cta` (button text in the video language)."],
 scenes=[("product","`name`, `tagline`, `media`, `badge`, `features` [{`text`, `at`, `icon`}], `price`, `oldPrice`, `currency`, `priceAt`, `at`"),
         ("cta","`text`, `button`, `sub`, `at`")],
 labels=["shop"], media=["`product` image (optional)"])

T["counter"] = dict(
 title="Counter", tag="numbers & data stories",
 desc="Create a data / statistics video where numbers count up on the voice: giant animated figures with rings or bar charts, labels and sources, and animated comparison bars. For facts, research findings, growth, reports.",
 look="Deep navy with a cyan grid glow, tabular numbers, cyan-to-lime bars.",
 when="Any script built around numbers.",
 extra_intake="The real figures and their sources (never invent statistics; mark examples as illustrative).", pace="tight",
 rules=["One `stat` per headline number, `at` on the number word; `chart` ring for percentages, bars for growth.",
        "`compare` for 2–5 values side by side.", "Add `source` whenever the number comes from a study."],
 scenes=[("stat","`value`, `prefix`, `suffix`, `decimals`, `label`, `sub`, `source`, `chart` none|ring|bars, `max` (ring), `bars` [values], `at`, `dur`"),
         ("compare","`title`, `items` [{`label`, `value`, `prefix`, `suffix`, `decimals`, `highlight`, `at`}], `at`")],
 labels=[])

T["top-five"] = dict(
 title="Top Five", tag="countdown rankings",
 desc="Make a top-5 / top-10 / ranking / countdown list video: huge rank numbers, item titles with optional images, a rank tracker, and a drumroll plus confetti for number one.",
 look="Purple with rotating gold rays, outlined rank numbers, solid gold #1.",
 when="Rankings, best-of lists, favorites, countdowns.",
 extra_intake="The ranked items (and images if any).", pace="tight",
 rules=["Open with `intro`. One `rank` per item from the highest number down to 1.",
        "Anchor `at` on the number word; #1 automatically gets a drumroll (keep ~1 s before it)."],
 scenes=[("intro","`n`, `kicker`, `title`, `sub`, `at`"),
         ("rank","`n`, `title`, `subtitle`, `media`, `at`, `drumroll`")],
 labels=["top"], media=["one image per item (optional)"])

T["flash-sale"] = dict(
 title="Flash Sale", tag="loud promos",
 desc="Make a flash sale / discount / limited-time offer promo video: a shaking giant percentage, a live countdown clock, product tiles with slashed prices and a dashed promo-code box. Works with or without a voiceover.",
 look="Hot red with a spinning sunburst and scrolling yellow SALE tapes, EDM beat.",
 when="Discounts, Black Friday, launches with deadlines.",
 extra_intake="Discount, deadline, products and prices, promo code. Voiceover or music-only?", pace="tight",
 rules=["Music-only version: no `--input`, set `\"duration\"` (8–15 s) and use seconds for times.",
        "`sale` first; `items` if there are products; `cta` with the code last."],
 scenes=[("sale","`kicker`, `value`, `prefix`, `suffix` (%), `word` (OFF), `timer` {`seconds`}, `fine`, `at`"),
         ("items","`items` [{`name`, `price`, `old`, `media`, `icon`, `at`}], `currency`, `at`"),
         ("cta","`text`, `code`, `sub`, `at`")],
 labels=["flash", "off", "cta"], data="`data.tape` sets the scrolling tape text.")

T["echo"] = dict(
 title="Echo", tag="kinetic typography",
 desc="Make a kinetic typography video where the spoken words themselves are the visuals: every word animates in exactly as it is said, lines resize to fill the frame, emphasized words explode in color. Ideal for motivational speeches, quotes, poetry and punchy statements.",
 look="Black with slow color glows, massive uppercase type, lime accent words, pink live-word highlight. No separate captions (the type is the caption).",
 when="Motivation, quotes, manifesto-style statements, voice-only content.",
 extra_intake="", pace="natural",
 rules=["`flow` does it automatically from the transcript: list 3–6 `emphasis` words.",
        "Use `words` for a hand-crafted climax (styles: normal, accent, huge, small, outline, strike).",
        "End with `quote` if there is a closing line or attribution."],
 scenes=[("flow","`emphasis` [words], `maxChars`, `lines`, `upper`"),
         ("words","`items` [{`text`, `at`, `style`, `strikeAt`, `clear`}], `upper`"),
         ("quote","`text`, `author`, `at`")],
 labels=[], arabic=True)

T["cinema"] = dict(
 title="Cinema", tag="trailer & documentary look",
 desc="Make a cinematic trailer / documentary / brand film video: letterbox bars, film grain and vignette, elegant serif titles that breathe open, Ken Burns motion on photos and clips, roman-numeral chapter cards and a closing title.",
 look="Black and warm gold, serif typography, subtitle-style captions, cinematic music with a boom on titles.",
 when="Storytelling with footage/photos, brand films, trailers, travel films.",
 extra_intake="The footage/photos to use (b-roll), title of the film.", pace="relaxed",
 rules=["Register every clip/photo (`media --name shot1 --video …`).",
        "Alternate `shot` scenes (3–6 s each) with sparse `title`/`chapter` cards; end with `end`."],
 scenes=[("title","`kicker`, `text`, `sub`, `at`, `upper`"),
         ("shot","`media`, `text`, `at`, `kenburns` {`from`, `to`, `x`, `y`}, `mediaOffset`"),
         ("chapter","`n`, `numeral` (arabic for 1,2,3), `title`, `at`"),
         ("end","`text`, `sub`, `at`")],
 labels=[], media=["b-roll clips/photos by name"])

T["journey"] = dict(
 title="Journey", tag="timelines",
 desc="Make a timeline / history / \"my journey\" / company story video: a track that draws itself while the camera travels from event to event, years and labels popping in on the voice, and milestone cards with a rolling year counter.",
 look="Deep teal with drifting dots, amber track and years, cream event cards.",
 when="Histories, career stories, product evolution, roadmaps.",
 extra_intake="Dates and events.", pace="natural",
 rules=["One `timeline` with 3–6 `events`, each `at` on the year/date word (vertical track in portrait, horizontal otherwise).",
        "Use `milestone` for the big moment or present day."],
 scenes=[("timeline","`title`, `events` [{`year`, `label`, `at`}], `orientation` auto|vertical|horizontal"),
         ("milestone","`from`, `year`, `title`, `text`, `at`")],
 labels=[], arabic=True)

T["breaking"] = dict(
 title="Breaking", tag="news bulletins",
 desc="Make a breaking-news / news-update / announcement video in TV style: flashing BREAKING banner, headline bar, media window, numbered key points, LIVE badge, channel name and a scrolling ticker.",
 look="Navy newsroom with red and white bars, news music and beeps, boxed captions.",
 when="News, updates, announcements, launches, recaps.",
 extra_intake="Headline, key points, channel name, an image or clip for the headline (optional).", pace="tight",
 rules=["`headline` first (title ≤ 10 words).", "One `point` per key fact.", "Ticker items in `data.ticker` (short)."],
 scenes=[("headline","`label`, `title`, `sub`, `media`, `icon`, `at`"),
         ("point","`n`, `text`, `kicker`, `at`")],
 labels=["breaking", "live", "latest"], data="`data.channel`, `data.ticker` [strings], `data.tickerLabel`, `data.live`.")

T["city-map"] = dict(
 title="City Map", tag="travel & places",
 desc="Make a travel / city guide / itinerary / \"best places in X\" video: a stylized animated city map with pins dropping in as each place is named, a route that draws itself between them, and place cards with photos and star ratings.",
 look="Clean light map (roads, parks, a river) generated per video, red pins, blue dashed route, white cards.",
 when="Travel guides, food tours, day plans, store locations.",
 extra_intake="The places in order, ratings, photos (optional).", pace="natural",
 rules=["`map` with 2–5 `pins`; `x`/`y` (0–1) roughly reflect real relative positions.",
        "`routeAt` after the last pin to reveal the route.", "One `place` card per highlight."],
 scenes=[("map","`title`, `pins` [{`label`, `x`, `y`, `at`}], `routeAt`, `routeDur`, `seed`, `zoom`"),
         ("place","`name`, `tag`, `rating`, `text`, `media`, `icon`, `at`")],
 labels=[])

T["recipe"] = dict(
 title="Recipe", tag="cooking videos",
 desc="Make a recipe / cooking / food video: a plated title card with time and servings, an ingredient checklist that ticks off, numbered step cards with a kitchen timer, and a final dish reveal with sparkles.",
 look="Cream kitchen check pattern, tomato-red accents, handwritten finish, jazzy music.",
 when="Recipes, drinks, meal prep, baking.",
 extra_intake="Ingredients with quantities, steps, cooking times, photos of steps/dish (optional).", pace="natural",
 rules=["`title` first, `ingredients` next (quantities in `qty`).", "One `step` per action; `timer` in seconds for waits.", "End with `final`."],
 scenes=[("title","`text`, `time`, `servings`, `media`, `at`"),
         ("ingredients","`title`, `items` [{`text`, `qty`, `at`}]"),
         ("step","`n`, `text`, `timer` (seconds), `media`, `at`"),
         ("final","`text`, `media`, `at`")],
 labels=["ingredients", "final"])

T["workout"] = dict(
 title="Workout", tag="fitness routines",
 desc="Make a workout / exercise / fitness routine video: exercise cards with a live rep counter synced to the counting voice or an interval countdown ring, rest timers with \"next up\", and a trophy finish with confetti.",
 look="Black with neon-lime streaks, huge rep numbers, pink rest ring, workout music.",
 when="Home workouts, gym routines, stretching, challenges.",
 extra_intake="Exercises, reps or seconds, sets, rest times, demo footage (optional).", pace="tight",
 rules=["For reps, set `repTimes` to the counted words (\"one, two…\") so the counter follows the voice.",
        "Use `seconds` for timed holds; `rest` between exercises; `done` at the end."],
 scenes=[("exercise","`name`, `set`, `reps`, `repTimes` [times], `repEvery`, `seconds`, `media`, `at`"),
         ("rest","`seconds`, `next`, `label`, `at`"),
         ("done","`text`, `sub`, `at`")],
 labels=["reps", "sec", "rest", "next", "done"])

T["review"] = dict(
 title="Review", tag="honest reviews",
 desc="Make a product / app / book / restaurant review video: a star score that fills up with a counting rating, pros and cons lists, and a BUY IT / SKIP IT verdict stamp with a drumroll.",
 look="Dark slate with gold stars, green pros, red cons, stamped verdict.",
 when="Reviews, comparisons, \"is it worth it\".",
 extra_intake="The item, the score, pros, cons, the verdict.", pace="tight",
 rules=["`score` first (anchor `at` on the number).", "`pros` then `cons` (≤ 3 each).", "`verdict` last (`positive` false for SKIP)."],
 scenes=[("score","`product`, `rating`, `max` (5), `media`, `sub`, `at`"),
         ("pros","`title`, `items` [{`text`, `at`}]"),
         ("cons","`title`, `items` [{`text`, `at`}]"),
         ("verdict","`text`, `positive`, `kicker`, `sub`, `at`")],
 labels=["pros", "cons", "verdict", "buy", "skip"])

T["whiteboard"]["scenes"][3] = ("compare", "`title`, `at`, `left` {`title`, `items` [{`text`, `at`} or strings]}, `right` {…}")
