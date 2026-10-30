"""Original bed for the pension-rate trial.

Synthesizes a quiet pad and a short original pluck pattern with NumPy and
SciPy. No sample library and no published melody. The wav is scaled so its
RMS over the spoken portion is 15% of the narration's speech RMS.
"""

from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np
from scipy import signal

ROOT = Path(__file__).resolve().parents[1]
NARRATION = ROOT / "public" / "narration.wav"
OUTPUT = ROOT / "public" / "bgm.wav"
LEVEL = ROOT / "public" / "bgm-level.json"
SPEECH_END_SEC = 12.0
TARGET_RATIO = 0.15


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


def synthesize(sample_rate: int, seconds: float) -> np.ndarray:
    count = int(sample_rate * seconds)
    time = np.arange(count) / sample_rate

    def tone(freq: float, amp: float) -> np.ndarray:
        phase = 2 * np.pi * freq * time
        return np.sin(phase) * amp + np.sin(phase * 2) * amp * 0.12

    pad = tone(146.83, 0.34) + tone(220.00, 0.22) + tone(369.99, 0.08)
    pad *= 0.62 + 0.38 * np.sin(2 * np.pi * 0.07 * time + 0.4)

    pattern = [293.66, 440.00, 349.23, 523.25, 392.00, 293.66, 349.23, 466.16]
    pluck = np.zeros(count)
    note_len = int(0.62 * sample_rate)
    step = int(0.90 * sample_rate)
    pos = int(0.25 * sample_rate)
    for index in range(40):
        if pos + note_len >= count:
            break
        freq = pattern[index % len(pattern)]
        env_t = np.arange(note_len) / sample_rate
        env = np.exp(-env_t * 5.2)
        phase = 2 * np.pi * freq * env_t
        note = (np.sin(phase) + 0.18 * np.sin(phase * 2)) * env
        pluck[pos : pos + note_len] += note * 0.28
        pos += step

    rng = np.random.default_rng(20261022)
    noise = rng.normal(0, 1, count)
    coeffs_b, coeffs_a = signal.butter(2, 280 / (sample_rate / 2), btype="low")
    air = signal.lfilter(coeffs_b, coeffs_a, noise)
    air *= 0.035 / (np.max(np.abs(air)) + 1e-9)

    mix = pad * 0.55 + pluck + air
    fade_in = int(0.4 * sample_rate)
    fade_out = int(1.2 * sample_rate)
    mix[:fade_in] *= np.linspace(0, 1, fade_in)
    mix[-fade_out:] *= np.linspace(1, 0, fade_out)
    return mix


def main() -> None:
    voice, voice_sr = read_wav(NARRATION)
    seconds = len(voice) / voice_sr
    speech = voice[: int(SPEECH_END_SEC * voice_sr)]
    speech_rms = float(np.sqrt(np.mean(speech[np.abs(speech) > 0.02] ** 2)))

    sample_rate = 44100
    mix = synthesize(sample_rate, seconds)
    bed = mix[int(0.4 * sample_rate) : int(SPEECH_END_SEC * sample_rate)]
    bed_rms = float(np.sqrt(np.mean(bed**2)))
    mix *= TARGET_RATIO * speech_rms / bed_rms
    measured = mix[int(0.4 * sample_rate) : int(SPEECH_END_SEC * sample_rate)]
    bgm_rms = float(np.sqrt(np.mean(measured**2)))
    write_wav(OUTPUT, mix, sample_rate)
    LEVEL.write_text(
        json.dumps(
            {
                "voice_speech_rms": speech_rms,
                "bgm_rms": bgm_rms,
                "rms_ratio": bgm_rms / speech_rms,
                "bgm_peak": float(np.max(np.abs(mix))),
                "seconds": seconds,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(LEVEL.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
