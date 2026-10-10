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


def make_sfx(name: str) -> np.ndarray | None:
    table = {
        "none": None,
        "paper": paper,
        "whoosh": whoosh,
        "shock": shock,
        "notify": notify,
        "coin": coin,
    }
    if name not in table:
        raise ValueError(f"未知の効果音: {name}")
    fn = table[name]
    return None if fn is None else fn()


def bgm_loop(seconds: float) -> np.ndarray:
    """ごく小さいペンタトニック。任意BGM。"""
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
