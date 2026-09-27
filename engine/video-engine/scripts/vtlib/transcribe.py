"""Word-level transcription with faster-whisper. Works for ~100 languages."""
from __future__ import annotations

from pathlib import Path

from .common import log, run, save_json


def to_wav16(src, dst):
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(dst)])
    return dst


def transcribe(audio: Path, lang: str | None, model: str = "medium", prompt: str | None = None, out_words: Path = None, out_txt: Path = None,
               device: str = "auto"):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("faster-whisper is not installed. Run: python vt.py setup")
    wav = Path(out_words).with_name("_asr16.wav")
    to_wav16(audio, wav)
    compute = "int8"
    try:
        m = WhisperModel(model, device=device if device != "auto" else "auto", compute_type=compute)
    except Exception:
        m = WhisperModel(model, device="cpu", compute_type="int8")
    log(f"transcribing with whisper-{model} (lang={lang or 'auto'}) ...")
    segs, info = m.transcribe(str(wav), language=(lang.split("-")[0] if lang else None), word_timestamps=True, beam_size=5,
                              vad_filter=False, condition_on_previous_text=False, initial_prompt=prompt)
    words = []
    for s in segs:
        for w in s.words or []:
            t = w.word.strip()
            if not t:
                continue
            words.append({"w": t, "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)})
    # Whisper word ends often swallow the following pause; clamp to next start.
    for i in range(len(words) - 1):
        words[i]["e"] = min(words[i]["e"], words[i + 1]["s"])
    save_json(out_words, words)
    write_indexed(words, out_txt, info.language if info else lang)
    wav.unlink(missing_ok=True)
    log(f"{len(words)} words, detected language: {getattr(info, 'language', '?')} -> {out_words.name}, {out_txt.name}")
    return words


def write_indexed(words, out_txt: Path, lang=None, per_line: int = 8):
    """Human/Claude-readable transcript: every word with its index and time, low-confidence words flagged with '?'."""
    lines = [f"# language: {lang}", "# format: [index] word@start  (use 'w:<index>' in plan.json to anchor timings; '?' = low confidence)"]
    row = []
    for i, w in enumerate(words):
        flag = "?" if w.get("p", 1) < 0.45 else ""
        row.append(f"[{i}] {w['w']}{flag}@{w['s']:.2f}")
        gap_after = (words[i + 1]["s"] - w["e"]) if i + 1 < len(words) else 0
        if len(row) >= per_line or gap_after > 0.6 or w["w"][-1:] in ".!?؟。！？":
            lines.append("  ".join(row)); row = []
    if row:
        lines.append("  ".join(row))
    Path(out_txt).write_text("\n".join(lines) + "\n", encoding="utf-8")
