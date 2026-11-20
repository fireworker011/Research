"""Original light beds for the two kane-v2 trials.

Synthesizes an upbeat major-key pluck with NumPy only. No sample library and
no published melody. Each wav is scaled so its RMS over the spoken portion is
15% of that narration's speech RMS.
"""

from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
TARGET_RATIO = 0.15
SR = 44100


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as handle:
        channels = handle.getnchannels()
        sample_rate = handle.getframerate()
        frames = np.frombuffer(handle.readframes(handle.getnframes()), dtype=np.int16)
    audio = frames.astype(np.float64) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    return audio, sample_rate


def write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    pcm = np.clip(audio, -1.0, 1.0)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes((pcm * 32767.0).astype(np.int16).tobytes())


def fit(audio: np.ndarray, samples: int) -> np.ndarray:
    if len(audio) < samples:
        return np.pad(audio, (0, samples - len(audio)))
    return audio[:samples]


def one_pole(source: np.ndarray, alpha: float) -> np.ndarray:
    out = np.empty_like(source)
    acc = 0.0
    for index, sample in enumerate(source):
        acc += alpha * (sample - acc)
        out[index] = acc
    return out


def synthesize(sample_rate: int, seconds: float, notes: list[float], seed: int) -> np.ndarray:
    count = int(sample_rate * seconds)
    time = np.arange(count) / sample_rate
    pad = (
        np.sin(2 * np.pi * notes[0] * 0.5 * time) * 0.18
        + np.sin(2 * np.pi * notes[2] * 0.5 * time) * 0.12
        + np.sin(2 * np.pi * notes[4] * 0.5 * time) * 0.08
    )
    pad *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.12 * time)

    pluck = np.zeros(count)
    step = int(sample_rate * 60 / 112 / 2)
    note_len = int(sample_rate * 0.28)
    for index in range(int(seconds * 8)):
        start = index * step
        if start + note_len >= count:
            break
        freq = notes[index % len(notes)]
        env_t = np.arange(note_len) / sample_rate
        env = np.exp(-env_t * 7.5)
        phase = 2 * np.pi * freq * env_t
        pluck[start : start + note_len] += (np.sin(phase) + 0.15 * np.sin(phase * 2)) * env * 0.34

    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 1, count)
    air = one_pole(noise, 0.02)
    hat = np.zeros(count)
    for index in range(int(seconds * 8)):
        start = index * step
        burst = int(0.03 * sample_rate)
        if start + burst >= count:
            break
        hat[start : start + burst] += air[start : start + burst] * np.linspace(1, 0, burst)
    hat *= 0.04 / (np.max(np.abs(hat)) + 1e-9)

    mix = pad * 0.45 + pluck + hat
    fade_in = int(0.25 * sample_rate)
    fade_out = int(0.8 * sample_rate)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)
    mix[-fade_out:] *= np.linspace(1, 0, fade_out)
    return mix


def level_bed(narration: Path, output: Path, frames: int, notes: list[float], seed: int) -> dict[str, float]:
    voice, voice_sr = read_wav(narration)
    samples = int(frames / 30 * SR)
    voice = fit(voice, samples)
    if voice_sr != SR:
        raise SystemExit(f"expected {SR} Hz, got {voice_sr}")
    speech = voice[np.abs(voice) > 0.02]
    speech_rms = float(np.sqrt(np.mean(speech**2)))
    mix = synthesize(SR, frames / 30, notes, seed)
    mix = fit(mix, samples)
    audible = mix[int(0.3 * SR) : int((frames / 30 - 0.8) * SR)]
    bed_rms = float(np.sqrt(np.mean(audible**2)))
    mix *= TARGET_RATIO * speech_rms / bed_rms
    measured = mix[int(0.3 * SR) : int((frames / 30 - 0.8) * SR)]
    bgm_rms = float(np.sqrt(np.mean(measured**2)))
    write_wav(output, mix, SR)
    write_wav(narration, voice, SR)
    return {
        "voice_speech_rms": round(speech_rms, 6),
        "bgm_rms": round(bgm_rms, 6),
        "rms_ratio": round(bgm_rms / speech_rms, 4),
        "bgm_peak": round(float(np.max(np.abs(mix))), 4),
        "seconds": round(frames / 30, 3),
    }


def main() -> None:
    payslip_notes = [523.25, 659.25, 783.99, 659.25, 587.33, 523.25, 440.0, 392.0]
    pension_notes = [392.0, 493.88, 587.33, 493.88, 440.0, 392.0, 329.63, 293.66]
    report = {
        "payslip": level_bed(
            PUBLIC / "narration-payslip.wav",
            PUBLIC / "bgm-payslip.wav",
            549,
            payslip_notes,
            20261023,
        ),
        "pension": level_bed(
            PUBLIC / "narration-pension.wav",
            PUBLIC / "bgm-pension.wav",
            527,
            pension_notes,
            20261024,
        ),
        "target_ratio": TARGET_RATIO,
    }
    (PUBLIC / "bgm-level.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
