"""Optional AI voiceover when the user has no recording.

Uses the `edge-tts` package (online Microsoft neural voices, no API key). It returns word timings,
so no transcription step is needed. Prefer a real human recording whenever the user can provide one.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from .common import log, run, save_json
from .transcribe import write_indexed

DEFAULT_VOICES = {
    "ar": "ar-EG-SalmaNeural", "en": "en-US-AriaNeural", "es": "es-ES-ElviraNeural", "fr": "fr-FR-DeniseNeural", "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural", "pt": "pt-BR-FranciscaNeural", "ru": "ru-RU-SvetlanaNeural", "tr": "tr-TR-EmelNeural", "hi": "hi-IN-SwaraNeural",
    "ja": "ja-JP-NanamiNeural", "ko": "ko-KR-SunHiNeural", "zh": "zh-CN-XiaoxiaoNeural", "id": "id-ID-GadisNeural", "ur": "ur-PK-UzmaNeural",
    "fa": "fa-IR-DilaraNeural", "he": "he-IL-HilaNeural", "nl": "nl-NL-ColetteNeural", "pl": "pl-PL-ZofiaNeural", "sv": "sv-SE-SofieNeural",
    "vi": "vi-VN-HoaiMyNeural", "th": "th-TH-PremwadeeNeural", "bn": "bn-IN-TanishaaNeural", "ta": "ta-IN-PallaviNeural", "uk": "uk-UA-PolinaNeural",
}


async def _speak(text, voice, mp3, rate):
    import edge_tts
    try:
        com = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    except TypeError:
        com = edge_tts.Communicate(text, voice, rate=rate)
    words = []
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s = ch["offset"] / 1e7; d = ch["duration"] / 1e7
                words.append({"w": ch["text"], "s": round(s, 3), "e": round(s + d, 3), "p": 1.0})
    return words


def synthesize(job, text: str, voice: str | None = None, rate: str = "+0%"):
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        raise SystemExit("edge-tts is not installed. Run: pip install edge-tts   (needs internet)")
    lang = (job.data.get("lang") or "en").split("-")[0]
    voice = voice or DEFAULT_VOICES.get(lang) or DEFAULT_VOICES["en"]
    mp3 = job.p("tts.mp3")
    words = asyncio.run(_speak(text, voice, mp3, rate))
    job.data["input"] = str(mp3); job.data["input_kind"] = "audio"; job.data["tts_voice"] = voice; job.save()
    save_json(job.p("words.json"), words)
    write_indexed(words, job.p("transcript.txt"), lang)
    log(f"TTS voice {voice}: {len(words)} words -> tts.mp3 (now run: analyze + edit as usual)")
    return words
