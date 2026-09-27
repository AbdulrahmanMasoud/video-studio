# plan.json schema (shared by every template)

```jsonc
{
  "lang": "en",                  // BCP-47 code; sets direction, fonts and number formatting
  "dir": "rtl",                  // optional override
  "numerals": "auto",            // auto | latin | native
  "duration": 30,                // only for videos without a voice (otherwise derived from the words)
  "scenes": [ { "type": "hook", "start": 0, "...": "template fields" } ],
  "labels": { "question": "سؤال" },          // translations for built-in UI words (see template SKILL.md)
  "captions": { "style": "pill", "maxWords": 3, "position": "bottom" },
  "palette": { "accent": "#FFE04A" },        // override template colors by key
  "music": { "mood": "lofi", "drop": "w:21", "end": "we:90", "stops": ["w:40~w:42"], "file": null, "bpm": null },
  "sfx": [ { "t": "w:30", "sfx": "ding", "gain": -14 } ],   // extra manual sound cues
  "mix": { "music_db": -13, "sfx_db": 2 },
  "data": { },                   // template-level data (e.g. breaking.ticker, podcast.speakers)
  "cuts": [ ]                    // optional: override jump-cut times (default: from the edit)
}
```

## Time values

Anywhere a time is expected (`start`, `end`, `at`, `…At`), use:

| Form | Meaning |
|---|---|
| `3.25` | seconds on the edited timeline |
| `"w:12"` | start of word 12 (index from `transcript_edit.txt`) |
| `"we:12"` | end of word 12 |
| `"w:12+0.3"`, `"w:12-0.1"` | offset in seconds |

A missing word index is an error that names the index; re-read `transcript_edit.txt`.

## Scenes

- Each scene needs `type` and `start`. `end` defaults to the next scene's start (last scene: end of
  video). Order by time.
- Optional on any scene: `"transition": "slide" | "fade" | "zoom" | "push" | "cut"` (the default
  comes from the template) and `"labels": {...}`.
- Scenes shorter than 0.6 s produce a warning; merge them.

### Common scenes (available in every template)

| type | fields | use |
|---|---|---|
| `text` | `text`, `sub`, `at`, `size` (in U, default 11), `sfx` | a big statement card |
| `media` | `media` (registered name), `text`, `kenburns` (false to disable), `mediaOffset` | full-frame b-roll image or clip |

## Captions

`style`: `pill` (active word in a pill), `karaoke` (words fill with color), `pop` (one big word at a
time), `line` (subtitle line), `boxed` (line in a box, active word colored), `none`.
Other keys: `maxWords`, `maxChars`, `gap` (seconds of silence that force a new chunk), `position`
(`bottom`/`middle`/`top`), `size` (U), `upper`, `color`, `hl`, `hlText`, `box`, `font`,
`chunks` (explicit: list of word counts or lists of word indices).

## Units

Templates size everything in **U** = 1 % of the frame's short side, so a layout scales to any size.
