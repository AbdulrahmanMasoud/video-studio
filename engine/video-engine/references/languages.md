# Languages

Every template works in any language. Set `--lang` on `init` (and `"lang"` in the plan).

## What changes automatically
- **Direction**: `ar`, `fa`, `ur`, `he`, `yi`, `ps`, `sd`, `ug`, `dv`, `ckb` render right-to-left. Layouts,
  progress bars, swipes and reading order mirror; platform safe zones do not (platform UI doesn't mirror).
- **Fonts**: Google Fonts are chosen per script and role (display/body/serif/mono/hand/rounded/condensed)
  and cached in `~/.cache/video-studio/fonts`. Supported scripts: Latin, Cyrillic, Greek, Vietnamese,
  Arabic, Persian, Urdu, Hebrew, Devanagari, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati,
  Gurmukhi, Thai, Japanese, Korean, Simplified and Traditional Chinese (Noto fallbacks for the rest).
  Override with `--fonts '{"display":"Cairo","body":"Tajawal"}'`. Without internet the system fonts are used.
- **Word joining**: Chinese, Japanese, Thai, Lao, Khmer, Burmese and Tibetan are laid out without spaces.
- **Numbers**: formatted with the locale (`1,000` / `١٬٠٠٠`). `--numerals latin|native` forces a digit set.
- **Uppercase** styling is skipped for scripts without case.

## Transcription
faster-whisper supports ~100 languages. For Arabic dialects (Egyptian, Gulf, Levantine…), Hindi, Urdu and
other non-English speech use `--model medium` (default) or `large-v3` for the best accuracy. Pass
`--prompt` with names and technical terms. Always proofread `transcript_edit.txt`; fix words in
`words_edit.json` (the `w` field) before rendering; timing stays the same.

## Labels
Templates print a few UI words (for example "Question", "MYTH/FACT", "LIVE", "Ingredients"). Each
template's SKILL.md lists the label keys. Translate them in the plan:

```json
"labels": {"question": "سؤال", "myth": "خرافة", "fact": "حقيقة"}
```

## AI voice (TTS)
`vt.py tts` uses edge-tts with a natural default voice per language, e.g. `ar` → `ar-EG-SalmaNeural`,
`en` → `en-US-AriaNeural`, `es` → `es-ES-ElviraNeural`, `hi` → `hi-IN-SwaraNeural`,
`ja` → `ja-JP-NanamiNeural`. Pick any other voice with `--voice` (list: `edge-tts --list-voices`),
speed with `--rate +10%`. Requires internet.
