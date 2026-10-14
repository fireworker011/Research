"""効果音とごく小さいBGMをその場で合成する。クレジット不要のオリジナル。"""

from __future__ import annotations

import numpy as np

from irasutoya_short.constants import SAMPLE_RATE

SR = SAMPLE_RATE


def _env(n: int, attack: float, release: float) -> np.ndarray:
    t = np.arange(n, dtype=np.float32) / SR
    dur = n / SR
    att = np.clip(t / max(attack, 1e-3), 0, 1)
    rel = np.clip((dur - t) / max(release, 1e-3), 0, 1)
    return att * rel


def paper() -> np.ndarray:
    n = int(0.28 * SR)
    noise = np.random.default_rng(1).uniform(-1, 1, n).astype(np.float32)
    return noise * _env(n, 0.01, 0.18) * 0.55


def whoosh() -> np.ndarray:
    n = int(0.35 * SR)
    noise = np.random.default_rng(2).uniform(-1, 1, n).astype(np.float32)
    kernel = np.ones(180, dtype=np.float32) / 180
    noise = np.convolve(noise, kernel, mode="same")
    return noise * _env(n, 0.08, 0.2) * 1.4


def shock() -> np.ndarray:
    n = int(0.45 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    freq = 520 * np.exp(-t * 7) + 80
    phase = 2 * np.pi * np.cumsum(freq) / SR
    tone = np.sin(phase).astype(np.float32)
    return tone * _env(n, 0.005, 0.28) * 0.7


def notify() -> np.ndarray:
    n = int(0.32 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    tone = np.sin(2 * np.pi * 880 * t) * (t < 0.09) + np.sin(2 * np.pi * 1175 * t) * (t >= 0.1)
    return tone.astype(np.float32) * _env(n, 0.005, 0.12) * 0.45


def coin() -> np.ndarray:
    n = int(0.4 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    tone = np.sin(2 * np.pi * 1318 * t) * np.exp(-t * 6) + 0.6 * np.sin(2 * np.pi * 1760 * t) * np.exp(-t * 5)
    return tone.astype(np.float32) * 0.4


def tick() -> np.ndarray:
    """あるあるの1項目。短いクリック。"""
    n = int(0.08 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    tone = np.sin(2 * np.pi * 1400 * t)
    return tone.astype(np.float32) * _env(n, 0.002, 0.05) * 0.35


def rise() -> np.ndarray:
    """順位や転換の立ち上がり。"""
    n = int(0.28 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    freq = 420 + 900 * t
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return np.sin(phase).astype(np.float32) * _env(n, 0.01, 0.12) * 0.4


def make_sfx(name: str) -> np.ndarray | None:
    table = {
        "none": None,
        "paper": paper,
        "whoosh": whoosh,
        "shock": shock,
        "notify": notify,
        "coin": coin,
        "tick": tick,
        "rise": rise,
    }
    if name not in table:
        raise ValueError(f"未知の効果音: {name}")
    fn = table[name]
    return None if fn is None else fn()


def bgm_loop(seconds: float, kind: str = "B4") -> np.ndarray:
    """オリジナルのベッド。B4 は従来の木琴。声より小さく使う。"""
    if kind == "B1":
        return np.zeros(int(seconds * SR), dtype=np.float32)
    table = {
        "B2": _piano,
        "B3": _lofi,
        "B4": _xylophone,
        "B5": _guitar,
        "B6": _ambience,
    }
    if kind not in table:
        raise ValueError(f"未知のBGM: {kind}")
    bed = table[kind](seconds)
    peak = float(np.max(np.abs(bed))) if bed.size else 0.0
    if peak > 1e-6:
        bed = bed / peak * np.float32(0.18)
    return bed.astype(np.float32)


def _xylophone(seconds: float) -> np.ndarray:
    """ごく小さいペンタトニック。公開済みの木琴に相当。"""
    n = int(seconds * SR)
    t = np.arange(n, dtype=np.float32) / SR
    notes = np.array([523.25, 587.33, 659.25, 783.99, 880.0], dtype=np.float32)
    beat = 0.5
    out = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(7)
    i = 0
    while i * beat < seconds:
        freq = float(notes[int(rng.integers(0, len(notes)))])
        a = int(i * beat * SR)
        b = min(n, a + int(0.28 * SR))
        if b <= a:
            break
        lt = np.arange(b - a, dtype=np.float32) / SR
        out[a:b] += np.sin(2 * np.pi * freq * lt) * np.exp(-lt * 6) * 0.15
        i += 1
    return out


def _tone(freq: float, n: int, decay: float, harmonic: float) -> np.ndarray:
    t = np.arange(n, dtype=np.float32) / SR
    wave = np.sin(2 * np.pi * freq * t) + harmonic * np.sin(2 * np.pi * freq * 2 * t)
    return wave.astype(np.float32) * np.exp(-t * decay)


def _piano(seconds: float) -> np.ndarray:
    n = int(seconds * SR)
    out = np.zeros(n, dtype=np.float32)
    chords = ((262.0, 330.0, 392.0), (220.0, 262.0, 330.0), (196.0, 247.0, 294.0), (174.0, 220.0, 262.0))
    step = int(1.6 * SR)
    span = int(1.45 * SR)
    for index in range(0, n, step):
        chord = chords[(index // step) % len(chords)]
        end = min(n, index + span)
        for freq in chord:
            out[index:end] += _tone(freq, end - index, 1.15, 0.18) * 0.22
    return out


def _lofi(seconds: float) -> np.ndarray:
    n = int(seconds * SR)
    out = _piano(seconds) * 0.55
    rng = np.random.default_rng(3)
    noise = rng.normal(0, 1, n).astype(np.float32)
    kernel = np.ones(400, dtype=np.float32) / 400
    noise = np.convolve(noise, kernel, mode="same").astype(np.float32)
    t = np.arange(n, dtype=np.float32) / SR
    wobble = 0.85 + 0.15 * np.sin(2 * np.pi * 0.18 * t)
    out += noise * wobble * 0.04
    return out


def _guitar(seconds: float) -> np.ndarray:
    n = int(seconds * SR)
    out = np.zeros(n, dtype=np.float32)
    notes = (196.0, 247.0, 294.0, 330.0, 247.0, 220.0)
    beat = 0.62
    span = int(0.48 * SR)
    for index, freq in enumerate(notes * (int(seconds / beat) + 1)):
        start = int(index * beat * SR)
        if start >= n:
            break
        end = min(n, start + span)
        out[start:end] += _tone(freq, end - start, 7.5, 0.35) * 0.4
    return out


def _ambience(seconds: float) -> np.ndarray:
    n = int(seconds * SR)
    rng = np.random.default_rng(6)
    white = rng.normal(0, 1, n).astype(np.float32)
    brown = np.cumsum(white)
    peak = float(np.max(np.abs(brown))) or 1.0
    t = np.arange(n, dtype=np.float32) / SR
    amp = 0.08 * (0.65 + 0.35 * np.sin(2 * np.pi * 0.07 * t))
    return (brown / peak).astype(np.float32) * amp
