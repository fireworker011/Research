"""60-second instrumental score for the drama trailer.

A minor piano motif, a low pad, and a heartbeat that cuts out
on the title hit. No vocals. Deterministic.
"""

from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np

SR = 48000
DURATION = 60.0
N = int(SR * DURATION)
RNG = np.random.default_rng(7)


def midi_to_hz(note: float) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def env_adsr(n: int, attack: float, decay: float, sustain: float, release: float, sr: int = SR) -> np.ndarray:
    a = max(1, int(attack * sr))
    d = max(1, int(decay * sr))
    r = max(1, int(release * sr))
    if a + d + r >= n:
        r = max(1, n // 5)
        d = max(1, n // 5)
        a = max(1, min(a, n - d - r))
    s = n - a - d - r
    attack_e = np.linspace(0.0, 1.0, a, endpoint=False) ** 1.4
    decay_e = np.linspace(1.0, sustain, d, endpoint=False)
    sustain_e = np.full(max(0, s), sustain)
    release_e = np.linspace(sustain, 0.0, r)
    return np.concatenate([attack_e, decay_e, sustain_e, release_e])[:n]


def add_mono(dst: np.ndarray, start: float, clip: np.ndarray) -> None:
    i0 = int(start * SR)
    if i0 >= len(dst) or i0 < -len(clip):
        return
    if i0 < 0:
        clip = clip[-i0:]
        i0 = 0
    i1 = min(len(dst), i0 + len(clip))
    dst[i0:i1] += clip[: i1 - i0]


def piano(freq: float, dur: float, amp: float, vibrato: bool = False) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq
    if vibrato and dur > 1.2:
        f = freq * (1.0 + 0.0022 * np.sin(2 * math.pi * 4.6 * t))
    partials = (
        (1.0, 1.0, 0.42),
        (2.003, 0.42, 0.95),
        (3.008, 0.22, 1.55),
        (4.015, 0.12, 2.3),
        (5.03, 0.06, 3.1),
        (6.05, 0.03, 4.0),
        (8.09, 0.015, 4.8),
    )
    y = np.zeros(n)
    for ratio, gain, damp in partials:
        tone = f * ratio if np.ndim(f) else freq * ratio
        if np.ndim(f):
            phase = 2 * math.pi * np.cumsum(f * ratio) / SR
            wave_p = np.sin(phase)
        else:
            wave_p = np.sin(2 * math.pi * tone * t)
        y += gain * wave_p * np.exp(-t * damp)
    hammer_n = min(n, int(0.018 * SR))
    noise = RNG.normal(0.0, 1.0, hammer_n)
    kernel = np.ones(32) / 32.0
    noise = np.convolve(noise, kernel, mode="same")
    burst = np.zeros(n)
    burst[:hammer_n] = noise * np.linspace(1.0, 0.0, hammer_n) ** 2
    y += burst * 0.08
    y *= env_adsr(n, 0.008, 0.45, 0.62, min(1.3, dur * 0.55))
    fade = min(n, int(0.006 * SR))
    y[:fade] *= np.linspace(0.0, 1.0, fade)
    return y * amp


def pad_chord(notes: tuple[int, ...], dur: float, amp: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for note in notes:
        base = midi_to_hz(note)
        for detune, gain in ((-0.08, 0.33), (0.0, 0.4), (0.07, 0.33)):
            freq = base * (2.0 ** (detune / 12.0))
            y += gain * np.sin(2 * math.pi * freq * t)
            y += 0.18 * gain * np.sin(2 * math.pi * freq * 2.002 * t) * np.exp(-t * 0.4)
    y *= env_adsr(n, 1.1, 0.4, 0.85, 1.6)
    return y * amp


def heartbeat(length: int, amp_env: np.ndarray) -> np.ndarray:
    y = np.zeros(length)
    interval = int(0.88 * SR)
    dub = int(0.16 * SR)
    for i0 in range(0, length - int(0.4 * SR), interval):
        for offset, gain, f0 in ((0, 1.0, 78.0), (dub, 0.62, 64.0)):
            n = int(0.11 * SR)
            t = np.arange(n) / SR
            freq = f0 * np.exp(-t * 8.0) + 36.0
            phase = 2 * math.pi * np.cumsum(freq) / SR
            thump = np.sin(phase) * np.exp(-t * 18.0)
            j = i0 + offset
            if j + n < length:
                y[j : j + n] += thump * gain
    y *= amp_env
    return y


def whoosh(dur: float, amp: float) -> np.ndarray:
    n = int(dur * SR)
    noise = RNG.normal(0.0, 1.0, n)
    win = int(0.02 * SR)
    noise = np.convolve(noise, np.ones(win) / win, mode="same")
    t = np.linspace(0.0, 1.0, n)
    rise = t ** 2
    return noise * rise * amp


def impact(amp: float) -> np.ndarray:
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * math.pi * 52.0 * t) * np.exp(-t * 2.4)
    sub = np.sin(2 * math.pi * 34.0 * t) * np.exp(-t * 1.6)
    noise = RNG.normal(0.0, 1.0, n)
    noise = np.convolve(noise, np.ones(80) / 80.0, mode="same")
    crack = noise * np.exp(-t * 22.0)
    return (body * 0.7 + sub * 0.55 + crack * 0.22) * amp


def delay_taps(x: np.ndarray) -> np.ndarray:
    y = np.zeros_like(x)
    taps = (
        (0.073, 0.28),
        (0.119, 0.22),
        (0.181, 0.16),
        (0.257, 0.11),
        (0.353, 0.07),
        (0.491, 0.045),
    )
    for seconds, gain in taps:
        d = int(seconds * SR)
        y[d:] += x[:-d] * gain
    return y


def write_wav(path: Path, stereo: np.ndarray) -> None:
    peak = float(np.max(np.abs(stereo)))
    if peak > 0:
        stereo = stereo / peak * 0.89
    stereo = np.tanh(stereo * 1.15)
    peak = float(np.max(np.abs(stereo)))
    stereo = stereo / max(peak, 1e-9) * 0.89
    pcm = np.clip(stereo, -1.0, 1.0)
    interleaved = pcm.T.reshape(-1)
    samples = (interleaved * 32767.0).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(samples.tobytes())


def rms_per_second(stereo: np.ndarray) -> list[float]:
    mono = stereo.mean(axis=0)
    out = []
    for sec in range(int(DURATION)):
        chunk = mono[sec * SR : (sec + 1) * SR]
        out.append(float(np.sqrt(np.mean(chunk ** 2))))
    return out


def compose() -> np.ndarray:
    left = np.zeros(N)
    right = np.zeros(N)

    # Melody. Times are locked to the picture cuts.
    melody = (
        (0.45, 69, 2.1, 0.34),
        (2.40, 72, 1.9, 0.32),
        (4.20, 76, 2.0, 0.30),
        (6.05, 74, 1.5, 0.26),
        (7.40, 72, 1.9, 0.28),
        (9.25, 69, 2.2, 0.30),
        (11.45, 64, 1.8, 0.24),
        (13.35, 57, 2.0, 0.28),
        (15.25, 60, 1.6, 0.22),
        (16.50, 65, 1.5, 0.24),
        (17.70, 69, 1.8, 0.28),
        (19.50, 62, 1.6, 0.24),
        (21.05, 65, 1.5, 0.26),
        (22.55, 69, 1.8, 0.30),
        (24.25, 72, 1.8, 0.32),
        (26.05, 76, 1.6, 0.30),
        (27.45, 72, 1.4, 0.26),
        (28.85, 69, 1.9, 0.28),
        (30.65, 65, 1.7, 0.24),
        (32.25, 69, 1.5, 0.26),
        (33.65, 67, 1.8, 0.28),
        (35.45, 64, 1.7, 0.26),
        (37.85, 64, 0.95, 0.30),
        (38.75, 68, 1.05, 0.34),
        (39.75, 71, 1.4, 0.36),
        (41.25, 76, 1.8, 0.38),
        (43.25, 83, 0.28, 0.42),
        (44.25, 80, 0.28, 0.40),
        (45.25, 76, 0.42, 0.36),
        (46.55, 69, 2.0, 0.30),
        (48.45, 72, 1.7, 0.28),
        (50.05, 76, 1.05, 0.24),
        (52.75, 69, 1.9, 0.22),
        (54.45, 72, 1.8, 0.20),
        (56.25, 64, 2.4, 0.18),
        (58.35, 57, 1.6, 0.12),
    )
    for start, note, dur, amp in melody:
        tone = piano(midi_to_hz(note), dur, amp, vibrato=dur > 1.4)
        overtone = piano(midi_to_hz(note + 12), min(dur, 1.2), amp * 0.12, vibrato=False)
        add_mono(left, start, tone * 1.0)
        add_mono(right, start + 0.012, tone * 0.92)
        add_mono(left, start, overtone * 0.8)
        add_mono(right, start + 0.014, overtone * 0.7)

    chords = (
        (6.0, 12.0, (57, 60, 64, 69), 0.07),
        (16.0, 8.0, (53, 57, 60, 65), 0.08),
        (22.0, 7.0, (57, 60, 64, 69), 0.085),
        (28.5, 5.5, (53, 57, 60, 65), 0.08),
        (33.5, 4.5, (52, 55, 59, 64), 0.085),
        (37.7, 8.5, (52, 56, 59, 64), 0.10),
        (46.2, 5.0, (57, 60, 64, 69), 0.09),
        (52.2, 7.4, (57, 60, 64, 69), 0.075),
    )
    for start, dur, notes, amp in chords:
        body = pad_chord(notes, dur, amp)
        add_mono(left, start, body)
        add_mono(right, start + 0.02, body * 0.96)

    # Root bed from the phone shot onward, gone on the hit, back under the title.
    roots = (
        (13.2, 4.0, 45, 0.07),
        (17.2, 5.0, 50, 0.07),
        (22.2, 6.0, 45, 0.075),
        (28.2, 5.0, 41, 0.07),
        (33.2, 4.4, 43, 0.075),
        (37.6, 8.6, 40, 0.08),
        (46.2, 4.9, 45, 0.07),
        (52.3, 6.8, 45, 0.055),
    )
    for start, dur, note, amp in roots:
        n = int(dur * SR)
        t = np.arange(n) / SR
        tone = np.sin(2 * math.pi * midi_to_hz(note) * t)
        tone *= env_adsr(n, 0.4, 0.2, 0.8, 0.8)
        add_mono(left, start, tone * amp)
        add_mono(right, start, tone * amp)

    drone_n = int((51.15 - 8.0) * SR)
    drone_t = np.arange(drone_n) / SR
    drone = (
        np.sin(2 * math.pi * midi_to_hz(45) * drone_t) * 0.045
        + np.sin(2 * math.pi * midi_to_hz(52) * drone_t) * 0.03
    )
    drone *= env_adsr(drone_n, 2.0, 0.4, 0.9, 1.2)
    add_mono(left, 8.0, drone)
    add_mono(right, 8.0, drone)
    title_n = int(7.2 * SR)
    title_t = np.arange(title_n) / SR
    title_drone = np.sin(2 * math.pi * midi_to_hz(45) * title_t) * 0.04
    title_drone *= env_adsr(title_n, 0.8, 0.3, 0.85, 1.4)
    add_mono(left, 52.2, title_drone)
    add_mono(right, 52.2, title_drone)

    pulse_from = int(17.2 * SR)
    pulse_to = int(51.15 * SR)
    pulse_env = np.zeros(N)
    ramp = np.linspace(0.0, 1.0, pulse_to - pulse_from)
    curve = np.clip(ramp ** 1.35, 0.0, 1.0)
    # Ease off a little on the window shot, then push into the hit.
    window = int(46.2 * SR)
    curve[window - pulse_from :] *= 0.82
    curve[-int(0.4 * SR) :] *= np.linspace(1.0, 0.0, int(0.4 * SR))
    pulse_env[pulse_from:pulse_to] = curve
    pulse = heartbeat(N, pulse_env) * 0.34
    add_mono(left, 0.0, pulse)
    add_mono(right, 0.0, pulse)

    add_mono(left, 50.45, whoosh(0.75, 0.05))
    add_mono(right, 50.45, whoosh(0.75, 0.05))
    hit = impact(0.55)
    add_mono(left, 51.18, hit)
    add_mono(right, 51.18, hit)

    # Quiet air so the open is not digital silence.
    air = RNG.normal(0.0, 1.0, N)
    air = np.convolve(air, np.ones(400) / 400.0, mode="same")
    air *= 0.004
    add_mono(left, 0.0, air)
    add_mono(right, 0.0, air * 0.9)

    wet_l = delay_taps(left)
    wet_r = delay_taps(right)
    left = left + wet_l * 0.85
    right = right + wet_r * 0.85

    fade_out = int(1.1 * SR)
    ramp_out = np.linspace(1.0, 0.0, fade_out)
    left[-fade_out:] *= ramp_out
    right[-fade_out:] *= ramp_out
    fade_in = int(0.03 * SR)
    left[:fade_in] *= np.linspace(0.0, 1.0, fade_in)
    right[:fade_in] *= np.linspace(0.0, 1.0, fade_in)
    return np.stack([left, right], axis=0)


def main() -> None:
    root = Path(__file__).resolve().parent
    stereo = compose()
    levels = rms_per_second(stereo)
    out = root / "build" / "score.wav"
    write_wav(out, stereo)
    report = root / "build" / "score-rms.txt"
    lines = [f"{sec:02d}s  {level:.4f}" for sec, level in enumerate(levels)]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
