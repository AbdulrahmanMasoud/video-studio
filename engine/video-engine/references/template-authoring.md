# Writing a new template

A template is a folder next to `video-engine/`:

```
skills/my-template/
  SKILL.md                      # frontmatter + intake + storyboard rules + scene schema
  template.json                 # manifest
  template.js                   # visuals (runs in headless Chromium)
  examples/plan.example.json    # example plan with a "demoScript" (used by engine-dev/smoke.py)
```

## template.json

```json
{
  "name": "my-template", "title": "My Template", "category": "Education",
  "summary": "One line shown by `vt.py templates`",
  "fonts": ["display", "body"],                 // roles to load: display body serif mono hand rounded condensed
  "captions": {"style": "pill", "maxWords": 3},
  "music": {"mood": "lofi"},
  "needsMedia": ["cam"],                        // optional: media names the template expects
  "scenes": ["intro", "point", "text", "media"]
}
```

## template.js

```js
(function () {
  const { C, P, eo, ei, sp, L } = VT;       // clamp, progress, ease-out, ease-in, spring, lerp
  VT.template({
    theme: {
      palette: { bg: '#111', deep: '#000', ink: '#111', paper: '#fff', accent: '#FFE04A', text: '#fff', muted: 'rgba(255,255,255,.7)' },
      captions: { style: 'pill', hl: '#FFE04A', hlText: '#111' },
      transition: 'slide',                    // slide | fade | zoom | push | cut
      sfx: { transition: 'whoosh', transitionGain: -16 },
      zones: { head: 0.18 },                  // header height (fraction of H, portrait)
    },
    background(layer) { /* build once */ return (t) => { /* per frame */ }; },
    scenes: {
      intro: {
        build(s, layer, ctx) {                // s = resolved scene (times in seconds), ctx.scenes = all scenes
          const U = VT.U, z = VT.Z.full;
          const title = VT.text(layer, s.title, { w: z.w * 0.9, h: z.h * 0.3, size: 10, color: VT.col('text') });
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'pop-low', { gain: -12 }); // sound effect synced to the reveal
          return (t, lt) => {                   // t = video time, lt = time since scene start
            const p = P(t, at, 0.5);
            VT.place(title, VT.W / 2, z.y + z.h / 2, { s: L(0.8, 1, sp(p)), o: C(p * 3) });
          };
        },
      },
    },
    overlays: [ (layer) => (t) => { /* persistent UI such as a progress tracker */ } ],
  });
})();
```

Rules that keep templates correct at every size and language:

- **Deterministic**: no `Date`, `Math.random`, timers or CSS animations. Everything is a function
  of `t`. Use `VT.hash(n)` for pseudo-randomness.
- **Units**: size with `VT.U` (1 % of the short side). Lay out inside `VT.Z` zones:
  `safe`, `area`, `head`, `body`, `cap` (captions), `full` (area minus captions), `column`.
  `VT.orient` is `portrait | square | landscape`; design for all three.
- **Text**: `VT.text(layer, str, {w, h, size, weight, font, color, align, box, valign})` auto-shrinks to
  fit. `VT.fit(el, w, h, minU)` shrinks any composite element (all inline font sizes scale together).
  Always `VT.esc()` user text inserted as HTML.
- **RTL**: use `VT.dir`, `VT.sign` (multiply horizontal motion), logical CSS (`inset-inline-start`),
  and set `direction:${VT.dir}` on flex rows. Test with an Arabic plan.
- **Numbers**: `VT.num(n, decimals)` formats per locale.
- **Labels**: `VT.label(s, 'key', 'English default')` so users can translate UI words.
- **Media**: `VT.media(layer, name, css)` returns an `<img>`; call `img.update(t)` every frame for
  video. `VT.hasMedia(name)`. Draw a tasteful placeholder when media is missing.
- **Helpers**: `VT.card`, `VT.badge`, `VT.stamp`, `VT.icon(name, color)` (`VT.iconNames`), `VT.svg`,
  `VT.rough.*` + `VT.drawPath` (hand-drawn strokes), `VT.type` (typewriter), `VT.caret`,
  `VT.win`, `VT.pop`, `VT.rise`, `VT.level(t)` (voice loudness 0..1), `VT.cuts` (edit points),
  `VT.words` (timed words), `VT.plan.data`, `VT.rows/cols/inset/clampW/sub/center`.
- **Sound**: add `VT.cue(time, name, {gain, pan, dur})` for every reveal; `VT.typingCue(a, b)` for typing.

## Testing

```bash
python3 engine-dev/smoke.py my-template --sizes 9:16,1:1,16:9          # renders stills from the example plan
python3 engine-dev/smoke.py my-template --plan plan.ar.json            # RTL check
```

Look at every contact sheet in `engine-dev/_smoke/`. Fix overflow, collisions with captions, and
anything that looks unfinished before opening a pull request.
