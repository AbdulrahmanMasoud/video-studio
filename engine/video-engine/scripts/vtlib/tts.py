"""Optional AI voiceover when the user has no recording.

`TTSProvider` implementations write an MP3 for a text in a language. No provider returns word timings:
the pipeline runs `vt.py transcribe` on the generated audio afterwards, exactly like a real recording.

Providers (env `TTS_PROVIDER`):
  openai   OpenAI text-to-speech over HTTPS (needs OPENAI_API_KEY; model TTS_OPENAI_MODEL, voice TTS_OPENAI_VOICE)
  espeak   offline espeak-ng voice (robotic; tests and fixtures only)
  none     disabled (default): `vt.py tts` exits with a clear error
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from .common import OFFLINE, OfflineError, die, log, run, which

# language code -> a reasonable default voice for each provider
OPENAI_VOICES = {"default": "alloy"}
ESPEAK_VOICES = {"ar": "ar", "en": "en-us", "es": "es", "fr": "fr", "de": "de", "it": "it", "pt": "pt-br", "ru": "ru", "tr": "tr", "hi": "hi",
                 "ja": "ja", "ko": "ko", "zh": "cmn", "id": "id", "ur": "ur", "fa": "fa", "he": "he", "nl": "nl", "pl": "pl", "sv": "sv", "vi": "vi"}


class TTSProvider:
    name = "base"

    def synthesize(self, text: str, lang: str, out_mp3: Path, voice: str | None = None, rate: str = "+0%") -> Path:
        raise NotImplementedError


class OpenAITTS(TTSProvider):
    """https://platform.openai.com/docs/guides/text-to-speech (POST /v1/audio/speech)."""
    name = "openai"

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None, timeout: float = 120.0):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("TTS_OPENAI_MODEL", "gpt-4o-mini-tts")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.timeout = timeout

    def synthesize(self, text, lang, out_mp3, voice=None, rate="+0%"):
        if not self.api_key:
            die("TTS_PROVIDER=openai but OPENAI_API_KEY is not set", error_code="tts_not_configured")
        if OFFLINE:
            raise OfflineError("VT_OFFLINE=1: TTS needs network")
        voice = voice or os.environ.get("TTS_OPENAI_VOICE") or OPENAI_VOICES["default"]
        speed = _rate_to_speed(rate)
        body = {"model": self.model, "input": text[:4096], "voice": voice, "response_format": "mp3", "speed": speed}
        req = urllib.request.Request(f"{self.base_url}/audio/speech", data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                Path(out_mp3).write_bytes(r.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            raise RuntimeError(f"OpenAI TTS failed ({e.code}): {detail}")
        return Path(out_mp3)


class EspeakTTS(TTSProvider):
    """Offline synthetic voice via espeak-ng + ffmpeg. Not for production; deterministic fixtures for tests."""
    name = "espeak"

    def synthesize(self, text, lang, out_mp3, voice=None, rate="+0%"):
        if not which("espeak-ng"):
            die("espeak-ng is not installed (needed for TTS_PROVIDER=espeak)", error_code="tts_not_configured")
        voice = voice or ESPEAK_VOICES.get(lang, "en-us")
        wpm = int(round(160 * _rate_to_speed(rate)))
        wav = Path(out_mp3).with_suffix(".wav")
        run(["espeak-ng", "-v", voice, "-s", str(wpm), "-w", str(wav), text])
        run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-ar", "44100", "-b:a", "128k", str(out_mp3)])
        wav.unlink(missing_ok=True)
        return Path(out_mp3)


PROVIDERS = {"openai": OpenAITTS, "espeak": EspeakTTS}


def _rate_to_speed(rate: str) -> float:
    """'+10%' -> 1.1 ; '-20%' -> 0.8 ; '1.2' -> 1.2"""
    try:
        r = str(rate).strip()
        if r.endswith("%"):
            return max(0.25, min(4.0, 1 + float(r[:-1]) / 100))
        return max(0.25, min(4.0, float(r)))
    except ValueError:
        return 1.0


def get_provider(name: str | None = None) -> TTSProvider:
    name = (name or os.environ.get("TTS_PROVIDER") or "none").lower()
    if name in ("none", "off", ""):
        die("AI voice is disabled (TTS_PROVIDER=none). Set TTS_PROVIDER=openai (with OPENAI_API_KEY) or record a voice note.",
            error_code="tts_disabled")
    if name not in PROVIDERS:
        die(f"unknown TTS_PROVIDER '{name}'. Choose one of: {', '.join(PROVIDERS)}", error_code="tts_not_configured")
    return PROVIDERS[name]()


def synthesize(job, text: str, voice: str | None = None, rate: str = "+0%", provider: str | None = None):
    """Write JOB/tts.mp3 and make it the job input. Word timings come from `vt.py transcribe` afterwards."""
    lang = (job.data.get("lang") or "en").split("-")[0]
    prov = get_provider(provider)
    mp3 = job.p("tts.mp3")
    prov.synthesize(text.strip(), lang, mp3, voice, rate)
    job.data["input"] = str(mp3); job.data["input_kind"] = "audio"; job.data["tts"] = {"provider": prov.name, "voice": voice}
    job.save()
    log(f"TTS ({prov.name}) -> tts.mp3 ({mp3.stat().st_size // 1024} KB). Next: vt.py transcribe JOB (word timings), then analyze + edit.")
    return mp3
