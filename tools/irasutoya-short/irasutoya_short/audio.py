"""WAVの読み書きと、声・効果音・BGMの重ね。"""

from __future__ import annotations

import io
import wave
from pathlib import Path

import numpy as np

from irasutoya_short.constants import SAMPLE_RATE


def wav_bytes_to_float(data: bytes) -> np.ndarray:
    with wave.open(io.BytesIO(data), "rb") as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        pcm = np.frombuffer(wf.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
        ch = wf.getnchannels()
    if ch > 1:
        pcm = pcm.reshape(-1, ch).mean(axis=1)
    if sr != SAMPLE_RATE and len(pcm):
        duration = len(pcm) / sr
        target = int(duration * SAMPLE_RATE)
        x_old = np.linspace(0, 1, len(pcm), endpoint=False)
        x_new = np.linspace(0, 1, target, endpoint=False)
        pcm = np.interp(x_new, x_old, pcm).astype(np.float32)
    return pcm


def read_wav(path: str | Path) -> np.ndarray:
    return wav_bytes_to_float(Path(path).read_bytes())


def write_wav(path: str | Path, samples: np.ndarray, sr: int = SAMPLE_RATE) -> None:
    pcm = np.clip(samples, -1.0, 1.0)
    ints = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(ints.tobytes())


def fit_length(samples: np.ndarray, n: int) -> np.ndarray:
    out = np.zeros(n, dtype=np.float32)
    m = min(n, len(samples))
    out[:m] = samples[:m]
    return out


def mix_tracks(voice: np.ndarray, sfx: np.ndarray | None, sfx_gain: float, bgm: np.ndarray | None, bgm_gain: float) -> np.ndarray:
    n = len(voice)
    out = voice.astype(np.float32).copy()
    peak = float(np.max(np.abs(out))) if n else 0.0
    if peak > 0.05:
        out *= min(1.0, 0.8 / peak)
    if sfx is not None and n:
        chunk = sfx[:n] * sfx_gain
        out[: len(chunk)] += chunk
    if bgm is not None and n and bgm_gain > 0:
        bed = fit_length(bgm, n) * bgm_gain
        hop = 1200
        for i in range(0, n, hop):
            seg = out[i : i + hop]
            loud = float(np.sqrt(np.mean(seg * seg) + 1e-12))
            duck = 0.35 if loud > 0.02 else 1.0
            out[i : i + hop] += bed[i : i + hop] * duck
    peak = float(np.max(np.abs(out))) if n else 0.0
    if peak > 0.98:
        out *= 0.98 / peak
    return out
