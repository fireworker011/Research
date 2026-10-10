"""音声波形から、1コマごとの口の開きを計算する。"""

from __future__ import annotations

import numpy as np

from irasutoya_short.constants import FPS, SAMPLE_RATE


def mouth_envelope(samples: np.ndarray, nframes: int, sr: int = SAMPLE_RATE, fps: int = FPS) -> np.ndarray:
    """0〜1。開きは速く、閉じは少し遅くする。"""
    if nframes <= 0:
        return np.zeros(0, dtype=np.float32)
    audio = np.asarray(samples, dtype=np.float32).reshape(-1)
    env = np.zeros(nframes, dtype=np.float32)
    hop = sr / float(fps)
    for i in range(nframes):
        a = int(i * hop)
        b = min(len(audio), int((i + 1) * hop))
        if b <= a:
            continue
        seg = audio[a:b]
        env[i] = float(np.sqrt(np.mean(seg * seg) + 1e-12))
    peak = float(np.percentile(env, 95)) if env.size else 0.0
    if peak < 1e-5:
        return env
    env = np.clip(env / peak, 0.0, 1.0)
    env[env < 0.08] = 0.0
    smooth = np.zeros_like(env)
    level = 0.0
    for i, value in enumerate(env):
        if value >= level:
            level = value
        else:
            level = level * 0.62 + value * 0.38
        smooth[i] = level
    return smooth
