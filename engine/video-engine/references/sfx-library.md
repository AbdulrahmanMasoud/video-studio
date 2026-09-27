# Sound effects

All effects are synthesized locally (royalty-free, no downloads). Templates place them automatically;
add extra ones in `plan.json`:

```json
"sfx": [{"t": "w:30", "sfx": "ding", "gain": -14, "pan": 0.2}]
```

`t` is seconds or `w:N`; `gain` in dB (typical −12 to −24); `pan` −1…1; `dur` for sweeps/risers.

| name | character / typical use |
|---|---|
| `whoosh` | airy sweep up (transitions; `dur`) |
| `whoosh-down` | sweep down (things dropping in; `dur`) |
| `swoosh` | short fast sweep |
| `pop` | UI pop (cards, list items) |
| `pop-high` | small bright pop (stickers, chips) |
| `pop-low` | deeper pop (titles, big cards) |
| `click` | mouse / toggle click |
| `ding` | bell, a confirmation |
| `success` | rising arpeggio (correct answer, payoff) |
| `error` | soft negative blip |
| `buzzer` | wrong-answer buzzer |
| `impact` | cinematic hit (big numbers, slams) |
| `boom` | sub-heavy boom (trailer titles) |
| `sparkle` | shimmer (magic, reveal) |
| `scratch` | pen/marker scratch (highlights, strikes) |
| `marker` | marker drawing (`dur`) |
| `zip` | zip (routes, fast moves) |
| `riser` | tension riser before a reveal (`dur`) |
| `tick` | clock tick |
| `tock` | clock tock |
| `beep` | short beep (timers, news) |
| `beep-long` | long beep |
| `whistle` | coach whistle |
| `cash` | cash register (prices) |
| `shutter` | camera shutter (photos) |
| `page` | page turn |
| `bubble` | chat bubble |
| `send` | message sent |
| `notify` | notification chime |
| `sting` | dramatic sting (hooks, titles) |
| `drumroll` | drumroll (`dur`, before #1 / verdicts) |
| `heartbeat` | heartbeat |
| `coin` | coin (promo codes, rewards) |
| `glitch` | digital glitch |
| `key` | single key press |
| `typing` | keyboard typing burst (`dur`; templates add it for typed text) |
