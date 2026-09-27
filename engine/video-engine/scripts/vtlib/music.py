"""Royalty-free background music, composed procedurally per video.

Moods set tempo, harmony and instruments. The arrangement follows the edit:
  --drop   time where drums/bass enter (usually the first big reveal)
  --stops  short breaks (e.g. right before the punchline)
  --end    time where the band stops and the last chord rings out
Everything is generated with numpy, so the output is original and free to use.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
rng = np.random.default_rng(3)

def _t(d): return np.arange(int(max(d, 0.001) * SR)) / SR
def _lp(x, f): return sosfilt(butter(2, min(f, SR / 2 - 200), "lowpass", fs=SR, output="sos"), x)
def _hp(x, f): return sosfilt(butter(2, f, "highpass", fs=SR, output="sos"), x)
def _bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "bandpass", fs=SR, output="sos"), x)
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def _env(d, a=0.01, r=0.1):
    t = _t(d); return np.minimum(1, t / max(a, 1e-3)) * np.minimum(1, np.maximum(0, (d - t) / max(r, 1e-3)))

# ---------------------------------------------------------------- instruments
def pad(f, d, bright=1.0):
    t = _t(d); s = sum(np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6)) for k in (0.997, 1.0, 1.004))
    s += 0.3 * bright * sum(np.sin(2 * np.pi * 2 * f * k * t) for k in (0.998, 1.003))
    return s * _env(d, 0.35, 0.5) * 0.12
def strings(f, d):
    t = _t(d); saw = sum(((f * k * t) % 1.0) * 2 - 1 for k in (0.996, 1.0, 1.005))
    return _lp(saw, 2200) * _env(d, 0.5, 0.6) * 0.06
def epiano(f, d):
    t = _t(d); s = np.sin(2 * np.pi * f * t + 0.8 * np.sin(2 * np.pi * f * t) * np.exp(-t * 3)) * np.exp(-t * 2.2)
    return s * _env(d, 0.005, 0.2) * 0.22
def piano(f, d):
    t = _t(d); s = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.6 + k * 0.9)) for k, a in ((1, 1), (2, 0.45), (3, 0.2), (4, 0.1)))
    return s * _env(d, 0.003, 0.15) * 0.25
def pluck(f, d=0.5):
    t = _t(d); s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) * np.exp(-t * 12)
    return s * np.exp(-t * 7) * _env(d, 0.002, 0.05)
_GCACHE = {}
def guitar(f, d=0.9):  # Karplus-Strong (cached per pitch)
    k = (round(f, 2), d)
    if k in _GCACHE:
        return _GCACHE[k]
    n = int(d * SR); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    _GCACHE[k] = _lp(out, 5000) * 0.5
    return _GCACHE[k]
def saw_stab(f, d):
    t = _t(d); s = sum(((f * k * t) % 1.0) * 2 - 1 for k in (0.99, 1.0, 1.01))
    return _lp(s, 3500) * np.exp(-t * 5) * _env(d, 0.003, 0.05) * 0.18
def square(f, d):
    t = _t(d); return np.sign(np.sin(2 * np.pi * f * t)) * np.exp(-t * 4) * _env(d, 0.002, 0.03) * 0.08
def bass(f, d, kind="sine"):
    t = _t(d)
    s = np.sin(2 * np.pi * f * t) if kind == "sine" else _lp(((f * t) % 1.0) * 2 - 1, 600)
    return s * _env(d, 0.01, 0.06) * 0.5
def kick():
    t = _t(0.35); f = 45 + 110 * np.exp(-t * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
def snare():
    t = _t(0.2); return (_bp(rng.standard_normal(len(t)), 1200, 6000) * np.exp(-t * 22) + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.4) * 0.5
def clap():
    t = _t(0.18); return _bp(rng.standard_normal(len(t)), 1000, 5000) * np.exp(-t * 28) * 0.45
def hat(open_=False):
    d = 0.14 if open_ else 0.04; t = _t(d); return _hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * (25 if open_ else 90)) * 0.3
def shaker():
    t = _t(0.08); return _bp(rng.standard_normal(len(t)), 4000, 10000) * np.sin(np.pi * t / 0.08) * 0.18
def tom(f=90):
    t = _t(0.5); return np.sin(2 * np.pi * f * t * (1 + 0.3 * np.exp(-t * 20))) * np.exp(-t * 7) * 0.7

# ----------------------------------------------------------------------- moods
# chords as MIDI note lists; roots for bass
MOODS = {
    "lofi":      dict(bpm=84, chords=[[57, 60, 64, 67, 71], [50, 57, 60, 65], [55, 59, 62, 65, 69], [48, 55, 59, 64]], roots=[45, 38, 43, 36], keys="epiano", arp="pluck", drums="lofi", bass="sine", crackle=True),
    "upbeat":    dict(bpm=118, chords=[[60, 64, 67], [55, 59, 62, 67], [57, 60, 64], [53, 57, 60, 65]], roots=[48, 43, 45, 41], keys="pad", arp="pluck", drums="pop", bass="saw"),
    "corporate": dict(bpm=108, chords=[[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 67]], roots=[48, 45, 41, 43], keys="piano", arp="pluck", drums="soft", bass="sine"),
    "cinematic": dict(bpm=70, chords=[[57, 60, 64], [53, 57, 60], [48, 55, 60, 64], [55, 59, 62]], roots=[33, 29, 36, 31], keys="strings", arp="piano", drums="cinematic", bass="sine"),
    "tension":   dict(bpm=92, chords=[[57, 60, 64], [57, 60, 65], [56, 59, 64], [57, 60, 64]], roots=[33, 33, 32, 33], keys="strings", arp=None, drums="pulse", bass="saw"),
    "edm":       dict(bpm=126, chords=[[57, 60, 64], [53, 57, 60], [48, 52, 55, 60], [55, 59, 62]], roots=[45, 41, 36, 43], keys="stab", arp="pluck", drums="four", bass="saw", pump=True),
    "acoustic":  dict(bpm=96, chords=[[55, 59, 62, 67], [52, 55, 59, 64], [48, 52, 55, 60], [50, 54, 57, 62]], roots=[43, 40, 36, 38], keys=None, arp="guitar", drums="shaker", bass="sine"),
    "news":      dict(bpm=100, chords=[[50, 53, 57], [50, 53, 58], [48, 52, 55], [49, 53, 57]], roots=[38, 38, 36, 37], keys="stab", arp=None, drums="news", bass="saw"),
    "workout":   dict(bpm=128, chords=[[57, 60, 64], [57, 60, 64], [53, 57, 60], [55, 59, 62]], roots=[33, 33, 29, 31], keys="stab", arp=None, drums="four", bass="saw", pump=True),
    "ambient":   dict(bpm=60, chords=[[48, 55, 62, 64], [45, 52, 59, 64], [41, 48, 55, 60], [43, 50, 57, 62]], roots=[36, 33, 29, 31], keys="pad", arp="piano_sparse", drums=None, bass=None),
    "jazzy":     dict(bpm=104, chords=[[50, 53, 57, 60, 64], [55, 59, 62, 65], [48, 52, 55, 59], [45, 49, 52, 55]], roots=[38, 43, 36, 33], keys="epiano", arp=None, drums="brush", bass="walk"),
    "game":      dict(bpm=140, chords=[[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]], roots=[48, 45, 41, 43], keys=None, arp="square", drums="chip", bass="square"),
    "piano":     dict(bpm=72, chords=[[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]], roots=[45, 41, 36, 43], keys=None, arp="piano", drums=None, bass=None),
}


def _reverb(x, d=1.6, k=3.2, mix=0.25):
    ir = rng.standard_normal(int(d * SR)) * np.exp(-_t(d) * k); ir = _lp(ir, 6000); ir /= np.sqrt((ir ** 2).sum())
    return x + mix * fftconvolve(x, ir)[: len(x)]


def compose(duration, mood="lofi", bpm=None, drop=None, stops=None, end=None, seed=3, transpose=0, out=None):
    import soundfile as sf
    global rng
    rng = np.random.default_rng(seed)
    M = MOODS.get(mood, MOODS["lofi"])
    bpm = bpm or M["bpm"]; beat = 60 / bpm; bar = beat * 4
    N = int((duration + 2) * SR)
    L, R = np.zeros(N), np.zeros(N)
    drop = duration * 0.12 if drop is None else drop
    end = duration - 1.2 if end is None else end
    stops = stops or []
    off = drop % beat

    def put(sig, at, g=1.0, pan=0.0):
        st = int(at * SR)
        if st >= N or st + len(sig) <= 0: return
        if st < 0: sig = sig[-st:]; st = 0
        e = min(N, st + len(sig)); s = sig[: e - st] * g
        L[st:e] += s * np.sqrt((1 - pan) / 2) * 1.414; R[st:e] += s * np.sqrt((1 + pan) / 2) * 1.414

    def stopped(t): return any(a <= t < b for a, b in stops)
    tr = transpose
    start = off - bar * 2; bi = 0; tb = start
    drums = M.get("drums")
    while tb < duration:
        ci = bi % 4; ch = [n + tr for n in M["chords"][ci]]; root = M["roots"][ci] + tr
        if tb + bar > 0 and tb < end:
            kind = M.get("keys")
            for n in ch:
                if kind == "pad": put(pad(midi(n), bar + 0.4), tb, 0.9)
                elif kind == "strings": put(strings(midi(n), bar + 0.5), tb, 1.0)
                elif kind == "epiano":
                    put(epiano(midi(n), beat * 1.8), tb, 0.8); put(epiano(midi(n), beat * 1.6), tb + beat * 2.5, 0.5)
                elif kind == "piano": put(piano(midi(n), bar), tb, 0.5)
                elif kind == "stab":
                    for k in (0, 1.5, 3):
                        if tb + k * beat >= drop: put(saw_stab(midi(n), beat * 0.8), tb + k * beat, 0.8)
                    put(pad(midi(n), bar + 0.3, 0.5), tb, 0.35)
            arp = M.get("arp")
            if arp:
                pat = [0, 2, 1, 3, 2, 1, 3, 2]
                steps = 8 if arp != "piano_sparse" else 4
                for k in range(steps):
                    at = tb + k * bar / steps
                    if at >= end or stopped(at): continue
                    n = ch[pat[k] % len(ch)] + (12 if arp in ("pluck", "square") else 0)
                    if arp == "pluck": put(pluck(midi(n)), at, 0.16 * (0.8 if k % 2 else 1), [-0.35, 0.35][k % 2])
                    elif arp == "guitar": put(guitar(midi(n - 12 if n > 64 else n), 0.9), at, 0.35, [-0.25, 0.25][k % 2])
                    elif arp == "square": put(square(midi(n), beat * 0.45), at, 0.8, [-0.2, 0.2][k % 2])
                    elif arp in ("piano", "piano_sparse"): put(piano(midi(n + 12), beat * 2), at, 0.35, [-0.2, 0.2][k % 2])
            for k in range(4):
                at = tb + k * beat
                if at < drop - 0.01 or at >= end or stopped(at): continue
                bk = M.get("bass")
                if bk == "walk": put(bass(midi(root + [0, 4, 7, 9][k]), beat * 0.9), at, 0.45)
                elif bk == "square": put(square(midi(root), beat * 0.5) * 3, at, 0.5)
                elif bk:
                    if k in (0, 2) or mood in ("tension", "news", "workout", "edm"):
                        put(bass(midi(root), beat * 0.9, "saw" if bk == "saw" else "sine"), at, 0.5 if k in (0, 2) else 0.32)
                if drums in ("pop", "soft", "lofi"):
                    if k in (0, 2): put(kick(), at + (0.02 if drums == "lofi" and k == 2 else 0), 0.85 if drums != "soft" else 0.6)
                    if k in (1, 3): put(snare() if drums == "lofi" else clap(), at, 0.5 if drums != "soft" else 0.3, 0.1)
                    put(hat(), at + beat / 2 + (0.04 if drums == "lofi" else 0), 0.22, 0.25)
                elif drums in ("four", "chip"):
                    put(kick(), at, 0.95); put(hat(True), at + beat / 2, 0.25, 0.25)
                    if k in (1, 3): put(clap(), at, 0.55, 0.1)
                elif drums == "shaker":
                    put(shaker(), at, 0.6, 0.3); put(shaker(), at + beat / 2, 0.4, 0.3)
                    if k == 0: put(kick(), at, 0.5)
                elif drums == "cinematic":
                    if k == 0 and bi % 2 == 0: put(tom(70), at, 0.9)
                    if k == 2: put(tom(95), at, 0.5)
                elif drums == "pulse":
                    for q in range(4): put(bass(midi(root + 12), beat / 4 * 0.8, "saw"), at + q * beat / 4, 0.18)
                    if k == 0: put(kick(), at, 0.7)
                elif drums == "news":
                    if k in (0, 2): put(tom(80), at, 0.8)
                    put(hat(), at + beat / 2, 0.2)
                elif drums == "brush":
                    put(_bp(rng.standard_normal(int(0.12 * SR)), 2000, 8000) * np.exp(-_t(0.12) * 18) * 0.15, at, 1, 0.2)
                    if k in (0, 2): put(kick(), at, 0.4)
        tb += bar; bi += 1
    # ending: sustained final chord
    fin = [n + tr for n in M["chords"][0]]
    ring = max(0.5, duration + 0.8 - end)
    for n in fin:
        put(pad(midi(n), ring + 0.6), end, 0.9)
    put(piano(midi(fin[-1] + 12), 1.5), end, 0.4)
    if M.get("crackle"):
        cr = (rng.random(N) > 0.9993) * rng.uniform(-0.4, 0.4, N); c = _hp(cr, 1500) * 0.5
        L += c; R += c
    mix = np.stack([L, R], 1)
    cut = int(max(0, drop) * SR)
    if cut > 0:
        mix[:cut] = np.stack([_lp(L[:cut], 1400), _lp(R[:cut], 1400)], 1)
    if M.get("pump"):
        env = np.ones(N)
        t0 = drop
        while t0 < end:
            a = int(t0 * SR); b = min(N, a + int(beat * SR)); x = np.linspace(0, 1, b - a)
            env[a:b] = 0.45 + 0.55 * np.minimum(1, x * 3); t0 += beat
        mix *= env[:, None]
    mix = np.stack([_reverb(mix[:, 0]), _reverb(mix[:, 1])], 1)[: int(duration * SR)]
    fo = int(min(1.4, duration * 0.2) * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    fi = int(0.2 * SR); mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.9
    if out:
        sf.write(str(out), mix.astype(np.float32), SR)
    return mix
