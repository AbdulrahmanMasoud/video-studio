# Production standards

The target is "a professional short-form editor made this". Check each item before delivering.

## Structure and pacing
- **Hook in 0–2 s.** First visual change within 0.3 s. The opening title states the payoff.
- **Change every ~1.5 s.** A reveal, a camera move, a new card, a caption change. No static hold > 3 s.
- **One idea per scene.** When the voice moves to a new point, cut to a new scene.
- **End with a payoff or CTA** held ≥ 1.2 s after the last word so it can be read.
- Remove stumbles, false starts, long breaths and dead air (`vt.py edit`). Keep natural rhythm:
  `tight` for social, `natural` for stories.

## On-screen text
- Summarize, do not transcribe: 2–6 words per card where possible. Captions carry the full speech.
- Always in the video's language, including template labels (`labels` in the plan).
- Highlight the one key word per card (accent color / marker highlight).
- Never place important text under the caption zone or the platform UI (the engine's safe zones
  handle this when `--platform` is set; check stills anyway).
- Numbers: use `numerals` to match the audience (Arabic-Indic vs Latin digits).

## Motion
- Reveals land **on the word** (anchor `at` to the word that says it, 0–0.1 s early).
- Ease out on entry, ease in on exit; springy scale for small UI pops; nothing linear.
- Keep motion purposeful: one main moving element at a time; background motion subtle.

## Captions
- Short chunks (≤ 3 words for vertical, ≤ 6 for landscape), active word highlighted.
- Break on punctuation and pauses. Correct transcription mistakes in `words_edit.json` before rendering
  (misspelled names are the most common complaint).

## Sound
- Voice is king: integrated −14 LUFS master (platform standard), true peak ≤ −1 dBTP.
- Music ducks under the voice (sidechain); `music_db` −13 with voice, −8 without.
- Every reveal has a subtle sound; transitions have whooshes; the payoff has an impact/success.
  Sound effects sit under the voice (−14 to −24 dB cue gains); never stack more than 2 at once.
- Music `drop` on the first key reveal; `end` shortly after the last word for a clean button ending.

## QA checklist
- [ ] `qa/report.json`: resolution/fps correct, LUFS ≈ target, true peak ≤ −1, no black segments
- [ ] `qa/final_sheet.jpg`: every frame readable, no overflow, correct direction (RTL/LTR)
- [ ] Captions in sync and spelled correctly
- [ ] All text in the requested language
- [ ] Nothing important hidden by platform UI
