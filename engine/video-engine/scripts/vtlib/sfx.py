"""Royalty-free sound effects synthesized from scratch, placed from cues.json (written by the renderer).

Every effect is generated with numpy, so there is nothing to license and nothing to download.
Cue format: {"t": seconds, "sfx": name, "gain": dB, "pan": -1..1, "dur": seconds (typing/riser), "pitch": ratio}
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
_rng = np.random.default_rng(11)


def _t(d): return np.arange(int(max(d, 0.001) * SR)) / SR
def _bp(x, lo, hi, o=2): return sosfilt(butter(o, [max(20, lo), min(SR / 2 - 100, hi)], "bandpass", fs=SR, output="sos"), x)
def _lp(x, f, o=2): return sosfilt(butter(o, min(f, SR / 2 - 100), "lowpass", fs=SR, output="sos"), x)
def _hp(x, f, o=2): return sosfilt(butter(o, f, "highpass", fs=SR, output="sos"), x)
def _norm(x, pk=0.9):
    m = np.abs(x).max() if len(x) else 0
    return x / m * pk if m > 0 else x
def _fade(x, a=0.003, b=0.02):
    x = x.copy(); na, nb = min(len(x) // 2, int(a * SR)), min(len(x) // 2, int(b * SR))
    if na: x[:na] *= np.linspace(0, 1, na)
    if nb: x[-nb:] *= np.linspace(1, 0, nb)
    return x
def _sweep_noise(d, lo, hi, up=True):
    n = int(d * SR); x = _rng.standard_normal(n); out = np.zeros(n); ch = 480
    for i in range(0, n, ch):
        p = i / n; f = lo * (hi / lo) ** (p if up else 1 - p)
        seg = x[max(0, i - 2000): i + ch]
        y = _bp(seg, f * 0.6, f * 1.6); out[i:i + ch] = y[-len(x[i:i + ch]):]
    return out
def _tone(f, d, decay=6.0, harm=(1, 0.35, 0.15)):
    t = _t(d); s = sum(a * np.sin(2 * np.pi * f * (k + 1) * t) for k, a in enumerate(harm))
    return s * np.exp(-t * decay)


def whoosh(d=0.5, up=True): return _norm(_sweep_noise(d, 250, 6000, up) * np.sin(np.pi * np.linspace(0, 1, int(d * SR))) ** 1.6)
def swoosh(): return whoosh(0.32, True)
def pop(f0=520, d=0.12):
    t = _t(d); f = f0 * (1 + 1.2 * np.exp(-t * 60))
    return _fade(_norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)), 0.001, 0.01)
def click(d=0.025, f=3500): return _norm(_bp(_rng.standard_normal(int(d * SR)), f * 0.6, f * 1.5) * np.exp(-_t(d) * 180), 0.8)
def key():
    a = click(0.03, _rng.uniform(2500, 4200)) * 0.8; b = pop(_rng.uniform(180, 240), 0.04) * 0.35
    o = np.zeros(max(len(a), len(b))); o[:len(a)] += a; o[:len(b)] += b; return o
def ding(freqs=(1318.5, 1975.5), d=1.1, gap=0.07):
    o = np.zeros(int((d + gap * len(freqs)) * SR))
    for i, f in enumerate(freqs):
        s = _tone(f, d, 5.5); st = int(i * gap * SR); o[st:st + len(s)] += s
    return _fade(_norm(o, 0.8), 0.002, 0.05)
def success(): return ding((1046.5, 1318.5, 1568, 2093), 1.2, 0.06)
def error():
    t1, t2 = _t(0.13), _t(0.19)
    s = np.concatenate([(np.sign(np.sin(2 * np.pi * 190 * t1)) * 0.4 + np.sin(2 * np.pi * 150 * t1)) * np.exp(-t1 * 10), np.sin(2 * np.pi * 120 * t2) * np.exp(-t2 * 14)])
    return _fade(_norm(_lp(s, 1800), 0.8), 0.002, 0.03)
def buzzer():
    t = _t(0.55); s = np.sign(np.sin(2 * np.pi * 110 * t)) * 0.5 + np.sign(np.sin(2 * np.pi * 116 * t)) * 0.5
    return _fade(_norm(_lp(s, 2200) * (1 - t / 0.6), 0.7), 0.005, 0.05)
def impact(d=1.2):
    t = _t(d); f = 40 + 90 * np.exp(-t * 18)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    nz = _lp(_rng.standard_normal(len(t)), 900) * np.exp(-t * 14) * 0.6
    crack = _hp(_rng.standard_normal(len(t)), 2500) * np.exp(-t * 45) * 0.35
    return _fade(_norm(np.tanh((body + nz + crack) * 1.6), 0.95), 0.0005, 0.1)
def boom(): return _norm(_lp(impact(1.8), 300), 0.95)
def sparkle(d=0.9, n=7, base=1760):
    o = np.zeros(int(d * SR)); sc = [1, 9 / 8, 5 / 4, 3 / 2, 5 / 3, 2, 9 / 4, 5 / 2]
    for i in range(n):
        s = _tone(base * sc[i % 8], 0.45, 9, (1,)) * (1 - i / (n * 1.4)); st = int(i * 0.055 * SR); o[st:st + len(s)] += s[:len(o) - st]
    return _fade(_norm(o, 0.7), 0.002, 0.05)
def scratch(d=0.28): return _norm(_bp(_rng.standard_normal(int(d * SR)), 900, 5000) * np.sin(np.pi * _t(d) / d) ** 0.7, 0.7)
def marker(d=0.45):
    t = _t(d); n = _bp(_rng.standard_normal(len(t)), 1800, 7000) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t) ** 2)
    return _fade(_norm(n * np.minimum(1, t / 0.03), 0.5), 0.01, 0.05)
def zipdown(d=0.4):
    t = _t(d); f = 1800 * (0.12 ** (t / d))
    return _fade(_norm(_lp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5, 3000) * np.sin(np.pi * t / d), 0.6), 0.002, 0.03)
def riser(d=1.2):
    t = _t(d); f = 200 * (8 ** (t / d))
    return _norm((np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + _hp(_rng.standard_normal(len(t)), 3000) * 0.4) * (t / d) ** 2.2, 0.6)
def tick(): return _norm(_bp(_rng.standard_normal(int(0.02 * SR)), 3000, 9000) * np.exp(-_t(0.02) * 250), 0.7)
def tock(): return pop(900, 0.06)
def beep(f=1000, d=0.12): t = _t(d); return _fade(_norm(np.sin(2 * np.pi * f * t), 0.6), 0.003, 0.02)
def beep_long(): return beep(1000, 0.6)
def whistle():
    t = _t(0.7); f = 2800 + 250 * np.sin(2 * np.pi * 28 * t)
    return _fade(_norm(np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.2 * _bp(_rng.standard_normal(len(t)), 2000, 4000), 0.6), 0.02, 0.08)
def cash():
    a = ding((2637, 3136), 0.6, 0.03); b = _norm(_bp(_rng.standard_normal(int(0.15 * SR)), 2000, 8000) * np.exp(-_t(0.15) * 30), 0.5)
    o = np.zeros(len(a) + 2000); o[:len(b)] += b; o[1500:1500 + len(a)] += a; return _norm(o, 0.8)
def shutter():
    a = click(0.02, 2500); b = click(0.03, 1800); o = np.zeros(int(0.12 * SR)); o[:len(a)] += a; o[int(0.07 * SR):int(0.07 * SR) + len(b)] += b; return o
def page():
    t = _t(0.35); return _fade(_norm(_bp(_rng.standard_normal(len(t)), 800, 6000) * np.sin(np.pi * t / 0.35) ** 2, 0.6), 0.01, 0.05)
def bubble(): return pop(900, 0.09)
def send(): return _norm(np.concatenate([whoosh(0.22, True), np.zeros(10)]), 0.7)
def notify(): return ding((1567.98, 2093), 0.5, 0.09)
def sting():
    t = _t(1.4); chord = sum(np.sin(2 * np.pi * f * t) for f in (146.8, 220, 293.7, 440)) * np.exp(-t * 2.2)
    return _fade(_norm(np.tanh(chord * 0.8) + 0.4 * impact(1.4)[:len(t)], 0.9), 0.002, 0.1)
def drumroll(d=1.2):
    o = np.zeros(int(d * SR)); step = 0.045
    for k in range(int(d / step)):
        s = _norm(_bp(_rng.standard_normal(int(0.05 * SR)), 150, 3000) * np.exp(-_t(0.05) * 60), 0.3 + 0.6 * k / (d / step)); st = int(k * step * SR); o[st:st + len(s)] += s[:len(o) - st]
    return _norm(o, 0.8)
def heartbeat():
    def thump(): t = _t(0.18); return np.sin(2 * np.pi * 55 * t) * np.exp(-t * 22)
    o = np.zeros(int(0.9 * SR)); a = thump(); o[:len(a)] += a; o[int(0.22 * SR):int(0.22 * SR) + len(a)] += a * 0.7; return _norm(o, 0.9)
def coin(): return ding((987.8, 1318.5), 0.5, 0.08)
def glitch():
    t = _t(0.35); s = np.sign(np.sin(2 * np.pi * 80 * t)) * (_rng.random(len(t)) > 0.6)
    return _fade(_norm(_bp(s + _rng.standard_normal(len(t)) * 0.3, 300, 6000), 0.6), 0.002, 0.03)

LIB = {
    "whoosh": lambda c: whoosh(c.get("dur", 0.5), True), "whoosh-down": lambda c: whoosh(c.get("dur", 0.5), False), "swoosh": lambda c: swoosh(),
    "pop": lambda c: pop(520), "pop-high": lambda c: pop(880, 0.1), "pop-low": lambda c: pop(300, 0.16), "click": lambda c: click(0.03, 2600),
    "ding": lambda c: ding(), "success": lambda c: success(), "error": lambda c: error(), "buzzer": lambda c: buzzer(),
    "impact": lambda c: impact(), "boom": lambda c: boom(), "sparkle": lambda c: sparkle(), "scratch": lambda c: scratch(),
    "marker": lambda c: marker(c.get("dur", 0.45)), "zip": lambda c: zipdown(), "riser": lambda c: riser(c.get("dur", 1.0)),
    "tick": lambda c: tick(), "tock": lambda c: tock(), "beep": lambda c: beep(), "beep-long": lambda c: beep_long(), "whistle": lambda c: whistle(),
    "cash": lambda c: cash(), "shutter": lambda c: shutter(), "page": lambda c: page(), "bubble": lambda c: bubble(), "send": lambda c: send(),
    "notify": lambda c: notify(), "sting": lambda c: sting(), "drumroll": lambda c: drumroll(c.get("dur", 1.2)), "heartbeat": lambda c: heartbeat(),
    "coin": lambda c: coin(), "glitch": lambda c: glitch(), "key": lambda c: key(),
}
NAMES = sorted(list(LIB) + ["typing"])


def _reverb(x, d=0.9, k=5.5, mix=0.16):
    ir = _rng.standard_normal(int(d * SR)) * np.exp(-_t(d) * k); ir = _lp(ir, 6000); ir /= np.sqrt((ir ** 2).sum())
    return x + mix * fftconvolve(x, ir)[: len(x)]


def build_track(cues, duration, out, master_db=0.0):
    import soundfile as sf
    n = int((duration + 1.0) * SR)
    L, R = np.zeros(n), np.zeros(n)
    unknown = set()

    def place(sig, t, gain_db, pan):
        g = 10 ** (gain_db / 20); st = int(t * SR)
        if st < 0: sig = sig[-st:]; st = 0
        e = min(n, st + len(sig)); s = sig[: e - st] * g
        L[st:e] += s * np.sqrt((1 - pan) / 2) * 1.414; R[st:e] += s * np.sqrt((1 + pan) / 2) * 1.414

    for c in cues:
        name, t = c.get("sfx"), float(c.get("t", 0))
        gain, pan = float(c.get("gain", -14)), float(c.get("pan", 0))
        if name == "typing":
            end = t + float(c.get("dur", 0.6)); x = t
            while x < end:
                place(key(), x, gain + _rng.uniform(-3, 1), _rng.uniform(-0.3, 0.3)); x += _rng.uniform(0.055, 0.1)
            continue
        fn = LIB.get(name)
        if not fn:
            unknown.add(name); continue
        sig = fn(c)
        if c.get("pitch") and c["pitch"] != 1:
            idx = np.arange(0, len(sig), c["pitch"]); sig = np.interp(idx, np.arange(len(sig)), sig)
        place(sig, t, gain, pan)
    mixd = np.stack([_reverb(L), _reverb(R)], 1)[: int(duration * SR)] * 10 ** (master_db / 20)
    peak = np.abs(mixd).max()
    if peak > 0.98:
        mixd *= 0.98 / peak
    sf.write(str(out), mixd.astype(np.float32), SR)
    return sorted(unknown)
