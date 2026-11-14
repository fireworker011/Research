"""自作のBGMとSEを numpy で生成する。他人の音源は使わない。

既存ファイルは上書きしない。全部作り直すときは --force。
"""

from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np

SR = 24000
ROOT = Path(__file__).resolve().parents[1]
RNG = np.random.default_rng(20261109)


def _write(path: Path, data: np.ndarray, peak: float = 0.9) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    samples = np.asarray(data, dtype=np.float32)
    level = float(np.max(np.abs(samples))) or 1.0
    samples = samples / level * peak
    pcm = np.clip(samples * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())


def _noise(n: int) -> np.ndarray:
    return RNG.standard_normal(n).astype(np.float32)


def _thump(freq: float = 70.0, dur: float = 0.18, noise_mix: float = 0.35) -> np.ndarray:
    n = int(SR * dur)
    t = np.arange(n, dtype=np.float32) / SR
    body = np.sin(2.0 * np.pi * freq * t) * np.exp(-t * 14.0)
    click = _noise(n) * np.exp(-t * 46.0) * noise_mix
    return (body + click).astype(np.float32)


def _place(buf: np.ndarray, sig: np.ndarray, at: float, amp: float = 1.0) -> None:
    i0 = int(round(at * SR))
    if i0 >= len(buf) or i0 < 0:
        return
    i1 = min(len(buf), i0 + len(sig))
    buf[i0:i1] += sig[: i1 - i0] * amp


def drone() -> np.ndarray:
    seconds = 16.0
    n = int(SR * seconds)
    t = np.arange(n, dtype=np.float32) / SR
    # 周期がループ長で閉じる正弦だけを重ね、継ぎ目でジャンプしない。
    sig = (
        0.55 * np.sin(2.0 * np.pi * 45.0 * t)
        + 0.28 * np.sin(2.0 * np.pi * 60.0 * t)
        + 0.16 * np.sin(2.0 * np.pi * 90.0 * t)
        + 0.08 * np.sin(2.0 * np.pi * 30.0 * t)
    )
    lfo = 0.72 + 0.28 * np.sin(2.0 * np.pi * 0.125 * t)
    air = _noise(n)
    kernel = np.ones(80, dtype=np.float32) / 80.0
    air = np.convolve(air, kernel, mode="same") * 0.08
    return (sig * lfo + air).astype(np.float32)


def footsteps(interval: float, count: int, amp0: float = 1.0, slow: float = 0.0) -> np.ndarray:
    span = interval * count + 0.4
    buf = np.zeros(int(SR * span), dtype=np.float32)
    at = 0.05
    for i in range(count):
        amp = amp0 * (0.72 ** i if slow else 1.0)
        _place(buf, _thump(68.0 + (i % 2) * 8.0, 0.16), at, amp)
        at += interval + slow * i * 0.08
    return buf


def footsteps_fade() -> np.ndarray:
    buf = np.zeros(int(SR * 2.4), dtype=np.float32)
    at = 0.04
    for i, amp in enumerate((1.0, 0.72, 0.48, 0.28, 0.14)):
        _place(buf, _thump(64.0, 0.16), at, amp)
        at += 0.34 + i * 0.08
    return buf


def key_rattle() -> np.ndarray:
    buf = np.zeros(int(SR * 0.85), dtype=np.float32)
    at = 0.02
    for _ in range(9):
        n = int(SR * 0.035)
        t = np.arange(n, dtype=np.float32) / SR
        burst = _noise(n) * np.exp(-t * 80.0)
        tone = np.sin(2.0 * np.pi * 1600.0 * t) * np.exp(-t * 60.0) * 0.4
        _place(buf, burst + tone, at, 0.8)
        at += float(RNG.uniform(0.05, 0.09))
    return buf


def tap_glow() -> np.ndarray:
    n = int(SR * 0.24)
    t = np.arange(n, dtype=np.float32) / SR
    freq = np.linspace(380.0, 920.0, n)
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    tone = np.sin(phase) * np.exp(-t * 7.0)
    click = _noise(n) * np.exp(-t * 70.0) * 0.5
    return (tone + click).astype(np.float32)


def rule_hit() -> np.ndarray:
    n = int(SR * 0.48)
    t = np.arange(n, dtype=np.float32) / SR
    body = np.sin(2.0 * np.pi * 82.0 * t) * np.exp(-t * 6.0)
    smack = _noise(n) * np.exp(-t * 18.0) * 0.55
    return (body + smack).astype(np.float32)


def msg_vibrate() -> np.ndarray:
    n = int(SR * 0.55)
    t = np.arange(n, dtype=np.float32) / SR
    carrier = _noise(n)
    kernel = np.ones(6, dtype=np.float32) / 6.0
    carrier = np.convolve(carrier, kernel, mode="same")
    mod = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2.0 * np.pi * 28.0 * t))
    env = np.exp(-t * 3.2)
    return (carrier * mod * env).astype(np.float32)


def low_boom() -> np.ndarray:
    n = int(SR * 0.9)
    t = np.arange(n, dtype=np.float32) / SR
    body = np.sin(2.0 * np.pi * 46.0 * t) * np.exp(-t * 3.4)
    sub = np.sin(2.0 * np.pi * 28.0 * t) * np.exp(-t * 2.6) * 0.6
    air = _noise(n) * np.exp(-t * 8.0) * 0.25
    return (body + sub + air).astype(np.float32)


def low_pulse() -> np.ndarray:
    buf = np.zeros(int(SR * 0.9), dtype=np.float32)
    _place(buf, low_boom()[: int(SR * 0.4)], 0.0, 0.7)
    _place(buf, low_boom()[: int(SR * 0.35)], 0.42, 0.45)
    return buf


def light_off_tick() -> np.ndarray:
    n = int(SR * 0.09)
    t = np.arange(n, dtype=np.float32) / SR
    return (_noise(n) * np.exp(-t * 90.0) + np.sin(2.0 * np.pi * 1800.0 * t) * np.exp(-t * 70.0) * 0.4).astype(np.float32)


def screen_lock() -> np.ndarray:
    buf = np.zeros(int(SR * 0.28), dtype=np.float32)
    _place(buf, light_off_tick(), 0.0, 0.8)
    _place(buf, light_off_tick(), 0.12, 0.55)
    return buf


def eerie_whisper() -> np.ndarray:
    n = int(SR * 1.3)
    t = np.arange(n, dtype=np.float32) / SR
    raw = _noise(n)
    slow = np.convolve(raw, np.ones(50) / 50.0, mode="same")
    band = raw - slow
    band = np.convolve(band, np.ones(4) / 4.0, mode="same")
    lfo = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2.0 * np.pi * 3.5 * t))
    env = np.sin(np.clip(t / 1.3, 0, 1) * np.pi)
    return (band * lfo * env).astype(np.float32)


GENERATORS = {
    "key_rattle": key_rattle,
    "footsteps_slow": lambda: footsteps(0.48, 4),
    "footsteps_fast": lambda: footsteps(0.22, 5),
    "footsteps_fade": footsteps_fade,
    "tap_glow": tap_glow,
    "rule_hit": rule_hit,
    "msg_vibrate": msg_vibrate,
    "low_boom": low_boom,
    "low_pulse": low_pulse,
    "light_off_tick": light_off_tick,
    "screen_lock": screen_lock,
    "eerie_whisper": eerie_whisper,
}


def generate(force: bool = False) -> None:
    bgm = ROOT / "assets" / "bgm" / "dark_ambient_drone.wav"
    if force or not bgm.exists():
        _write(bgm, drone(), peak=0.9)
        print(f"wrote {bgm}")
    se_dir = ROOT / "assets" / "se"
    for name, fn in GENERATORS.items():
        path = se_dir / f"{name}.wav"
        if force or not path.exists():
            _write(path, fn(), peak=0.9)
            print(f"wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="BGMとSEを numpy で生成する")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    generate(force=args.force)


if __name__ == "__main__":
    main()
