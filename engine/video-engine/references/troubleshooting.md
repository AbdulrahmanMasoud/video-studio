# Troubleshooting

| Symptom | Fix |
|---|---|
| `missing --lang, --size` on `init` | Ask the user for language and dimensions; this is required by design. |
| `doctor` says ffmpeg MISSING | macOS `brew install ffmpeg` · Ubuntu/Debian `sudo apt install ffmpeg` · Windows `winget install ffmpeg` |
| `doctor` says headless chromium MISSING | `python3 -m playwright install chromium` (Linux may also need `python3 -m playwright install-deps chromium`) |
| `pip` refuses (externally managed environment) | `vt.py setup --break-system-packages`, or use a virtualenv |
| `Plan references missing word index w:N` | Indices come from `transcript_edit.txt` (after `edit`), not `transcript.txt`. |
| `Scene type "x" is not defined by this template` | Use a scene type from the template's SKILL.md (or the common `text` / `media`). |
| Text is tiny | The card is overfull; shorten the text. On-screen text should summarize. |
| Wrong glyphs / boxes instead of letters | Fonts could not be downloaded (offline). Connect once, run `vt.py fonts --precache`, or pass `--fonts` with installed fonts. With `VT_OFFLINE=1` uncached families fall back to system fonts and log a warning. |
| Captions out of sync | Re-run `edit` after changing drops; never edit timings by hand; check the right transcript file. |
| Transcription is poor | Use `--model medium` or `large-v3`, add `--prompt`, then correct words in `words_edit.json`. |
| Render is slow | `--draft` for checks, `--workers N` to use more CPU cores, render only a range with `--start/--end`. |
| Media shows a grey placeholder | Register it: `vt.py media JOB --name <name> --video file.mp4` (or `--image`). The name must match the plan. |
| Audio too quiet/loud | `init --lufs -14` is the target; adjust `mix --music-db` / `--sfx-db` for balance. |
| Music not wanted | `"music": {"mood": "none"}` or `build --no-music`. |
| `tts_disabled` / `tts_not_configured` | Set `TTS_PROVIDER=openai` and `OPENAI_API_KEY` (or `--provider espeak` for a test voice). edge-tts is no longer used. |
| `input_too_long` on `init` | The input exceeds `--duration-limit`; trim the recording or raise the limit. |
| `asset_invalid` on `media` / `assets` | Not a real image/video, over 40 MP, or HEIC without `pillow-heif`. The manifest index lists the reason per asset. |
| QA says resolution differs | Expected for `--draft` (half size) or `--max-height`; the report's `note` explains. Only a mismatch with the *expected* size is an issue. |
