# Music moods

Music is composed on the fly for the exact video length (royalty-free, deterministic). Set it in the
plan or on the command line:

```json
"music": {"mood": "lofi", "drop": "w:21", "end": "we:90", "stops": ["w:40~w:42"], "bpm": 90, "seed": 3, "transpose": 0}
```

- `drop`: where the full beat kicks in (before it: a light intro). Put it on the first big reveal.
- `end`: where the track resolves with a final hit (default: end of video).
- `stops`: short silences for dramatic moments (`"from~to"`).
- `file`: use the user's own track instead (looped/trimmed and faded automatically).
- `"mood": "none"` or `vt.py build --no-music` for no music.

| mood | bpm | feel | good for |
|---|---|---|---|
| `lofi` | 84 | warm e-piano, soft drums, vinyl crackle | tips, tutorials, chill talking heads |
| `upbeat` | 118 | bright pop | lists, product, before/after |
| `corporate` | 108 | clean piano + pluck | data, SaaS demos, LinkedIn |
| `cinematic` | 70 | strings, big drums | trailers, stories, timelines |
| `tension` | 92 | pulsing strings | myths, reveals, mysteries |
| `edm` | 126 | four-on-the-floor, sidechain pump | hot takes, sales, hype |
| `acoustic` | 96 | plucked guitar, shaker | travel, lifestyle, whiteboard |
| `news` | 100 | urgent stabs | breaking news, updates |
| `workout` | 128 | driving four-on-the-floor | fitness |
| `ambient` | 60 | pads, sparse piano | tech, calm explainers |
| `jazzy` | 104 | e-piano, walking bass, brushes | cooking, cafés |
| `game` | 140 | chiptune | quizzes, games |
| `piano` | 72 | solo piano | personal stories, emotional moments |
