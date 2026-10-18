"""Finish a short with narration and no source audio.

Grok Imagine clips already contain a voice. Keeping that stream and laying
narration on top produces two voices. When narration is added, the source
audio is discarded with `-an` and is never mixed, ducked, or lowered.
"""

from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 48000
# Amplitude ratio 0.15 is about -16.5 dB, the "15% under the voice" level.
BGM_AMPLITUDE = 0.15
KANE_SPEED = 1.12
LINE_GAP_SEC = 0.16


class FinishError(RuntimeError):
    pass


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "")[-2000:]
        raise FinishError(f"command failed: {' '.join(cmd[:8])}\n{tail}")


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def duration_of(path: Path) -> float:
    return float(probe(path)["format"]["duration"])


def audio_stream_count(path: Path) -> int:
    streams = probe(path).get("streams") or []
    return sum(1 for stream in streams if stream.get("codec_type") == "audio")


def extract_muted_picture(
    src: Path,
    dst: Path,
    *,
    start: float | None = None,
    end: float | None = None,
    vf: str | None = None,
    fps: int | None = None,
) -> None:
    """Write picture only. The source audio stream is not mapped."""
    cmd = ["ffmpeg", "-y", "-i", str(src)]
    filters: list[str] = []
    if start is not None or end is not None:
        start_s = 0.0 if start is None else start
        end_s = f":end={end:.6f}" if end is not None else ""
        filters.append(f"trim=start={start_s:.6f}{end_s},setpts=PTS-STARTPTS")
    if vf:
        filters.append(vf)
    if fps is not None:
        filters.append(f"fps={fps}")
    filters.append("format=yuv420p")
    cmd += ["-vf", ",".join(filters), "-an"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p"]
    if fps is not None:
        cmd += ["-r", str(fps)]
    cmd.append(str(dst))
    run(cmd)
    if audio_stream_count(dst) != 0:
        raise FinishError(f"muted picture still has audio: {dst}")


def concat_pictures(paths: list[Path], dst: Path, fps: int) -> None:
    if len(paths) == 1:
        extract_muted_picture(paths[0], dst, fps=fps)
        return
    cmd = ["ffmpeg", "-y"]
    for path in paths:
        cmd += ["-i", str(path)]
    parts = []
    labels = []
    for index in range(len(paths)):
        parts.append(
            f"[{index}:v]setpts=PTS-STARTPTS,fps={fps},scale=1080:1920,setsar=1,format=yuv420p[v{index}]"
        )
        labels.append(f"[v{index}]")
    graph = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(paths)}:v=1:a=0[v]"
    cmd += [
        "-filter_complex",
        graph,
        "-map",
        "[v]",
        "-an",
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        str(dst),
    ]
    run(cmd)
    if audio_stream_count(dst) != 0:
        raise FinishError(f"concat picture still has audio: {dst}")


def write_wav(path: Path, samples: np.ndarray, sr: int = SR) -> None:
    audio = np.clip(samples, -1.0, 1.0)
    pcm = (audio * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        handle.writeframes(pcm.tobytes())


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as handle:
        sr = handle.getframerate()
        channels = handle.getnchannels()
        frames = handle.readframes(handle.getnframes())
    pcm = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        pcm = pcm.reshape(-1, channels).mean(axis=1)
    return pcm, sr


def resample(samples: np.ndarray, src_sr: int, dst_sr: int = SR) -> np.ndarray:
    if src_sr == dst_sr or len(samples) == 0:
        return samples.astype(np.float32)
    dst_n = max(1, int(round(len(samples) * dst_sr / src_sr)))
    src_x = np.linspace(0.0, 1.0, len(samples), endpoint=False)
    dst_x = np.linspace(0.0, 1.0, dst_n, endpoint=False)
    return np.interp(dst_x, src_x, samples).astype(np.float32)


def squeeze_internal_silence(samples: np.ndarray, sr: int, max_gap: float = 0.18, thresh: float = 0.02) -> np.ndarray:
    """Shorten pauses inside one spoken line. Leading and trailing silence stay put."""
    if len(samples) == 0:
        return samples
    loud = np.abs(samples) >= thresh
    max_n = int(max_gap * sr)
    pieces: list[np.ndarray] = []
    index = 0
    total = len(samples)
    while index < total:
        if loud[index]:
            end = index + 1
            while end < total and loud[end]:
                end += 1
            pieces.append(samples[index:end])
            index = end
            continue
        end = index + 1
        while end < total and not loud[end]:
            end += 1
        quiet = samples[index:end]
        if index > 0 and end < total and len(quiet) > max_n:
            quiet = quiet[:max_n]
        pieces.append(quiet)
        index = end
    if not pieces:
        return samples
    return np.concatenate(pieces)


def trim_silence(samples: np.ndarray, sr: int, thresh: float = 0.012, pad: float = 0.02) -> np.ndarray:
    if len(samples) == 0:
        return samples
    loud = np.where(np.abs(samples) >= thresh)[0]
    if len(loud) == 0:
        return samples[: int(0.05 * sr)]
    pad_n = int(pad * sr)
    start = max(0, int(loud[0]) - pad_n)
    end = min(len(samples), int(loud[-1]) + pad_n)
    return samples[start:end]


def atempo(samples: np.ndarray, sr: int, factor: float, work: Path) -> np.ndarray:
    """Pitch-preserving speed. factor > 1 shortens the line."""
    if factor <= 1.02:
        return samples
    work.mkdir(parents=True, exist_ok=True)
    src = work / "atempo-in.wav"
    dst = work / "atempo-out.wav"
    write_wav(src, samples, sr)
    filters: list[str] = []
    remaining = factor
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    filters.append(f"atempo={max(0.5, remaining):.5f}")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-af",
            ",".join(filters),
            "-ar",
            str(sr),
            "-ac",
            "1",
            str(dst),
        ]
    )
    sped, _ = read_wav(dst)
    return sped


def place_lines(lines: list[tuple[float, np.ndarray]], total: float, sr: int = SR) -> np.ndarray:
    out = np.zeros(max(1, int(round(total * sr))), dtype=np.float32)
    for start, samples in lines:
        index = int(round(start * sr))
        if index >= len(out):
            continue
        end = min(len(out), index + len(samples))
        out[index:end] += samples[: end - index]
    return out


def write_bed(path: Path, duration: float, kind: str, sr: int = SR) -> None:
    """Original synthesized bed. Each kind is a different pattern."""
    n = max(1, int(round(duration * sr)))
    t = np.arange(n, dtype=np.float64) / sr
    if kind == "piano_night":
        # Slow A-minor fifths, not a marimba.
        chord = np.zeros(n)
        for freq, amp in ((220.0, 0.34), (261.63, 0.22), (329.63, 0.16)):
            chord += amp * np.sin(2 * np.pi * freq * t) * np.exp(-0.35 * (t % 4.2))
        audio = chord
    elif kind == "piano_reply":
        chord = np.zeros(n)
        for freq, amp in ((311.13, 0.28), (369.99, 0.2), (466.16, 0.14)):
            chord += amp * np.sin(2 * np.pi * freq * t) * np.exp(-0.55 * (t % 3.1))
        audio = chord
    elif kind == "marimba_evening":
        bpm = 96.0
        step = 60.0 / bpm
        notes = [523.25, 587.33, 659.25, 783.99, 659.25, 587.33]
        audio = np.zeros(n)
        for index, freq in enumerate(notes * 8):
            start = index * step
            mask = (t >= start) & (t < start + step * 0.85)
            local = t - start
            audio[mask] += 0.45 * np.sin(2 * np.pi * freq * local[mask]) * np.exp(-6.5 * local[mask])
    elif kind == "box_hall":
        bpm = 72.0
        step = 60.0 / bpm
        notes = [392.0, 349.23, 329.63, 293.66]
        audio = np.zeros(n)
        for index, freq in enumerate(notes * 10):
            start = index * step
            mask = (t >= start) & (t < start + 0.35)
            local = t - start
            audio[mask] += 0.4 * np.sin(2 * np.pi * freq * 2 * local[mask]) * np.exp(-8.0 * local[mask])
    elif kind == "night_pad":
        audio = (
            0.22 * np.sin(2 * np.pi * 146.83 * t)
            + 0.14 * np.sin(2 * np.pi * 220.0 * t)
            + 0.08 * np.sin(2 * np.pi * 293.66 * t + 0.4)
        ) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.18 * t))
    elif kind == "marimba_c":
        bpm = 104.0
        step = 60.0 / bpm
        notes = [261.63, 329.63, 392.0, 523.25, 392.0, 329.63]
        audio = np.zeros(n)
        for index, freq in enumerate(notes * 12):
            start = index * step
            mask = (t >= start) & (t < start + step * 0.7)
            local = t - start
            audio[mask] += 0.5 * np.sin(2 * np.pi * freq * local[mask]) * np.exp(-7.0 * local[mask])
    elif kind == "piano_eb":
        audio = np.zeros(n)
        for freq, amp in ((155.56, 0.3), (196.0, 0.22), (233.08, 0.16), (311.13, 0.1)):
            audio += amp * np.sin(2 * np.pi * freq * t) * (0.7 + 0.3 * np.sin(2 * np.pi * (66 / 60) * t))
    elif kind == "guitar_g":
        bpm = 88.0
        step = 60.0 / bpm / 2
        notes = [196.0, 246.94, 293.66, 392.0, 293.66, 246.94]
        audio = np.zeros(n)
        for index, freq in enumerate(notes * 16):
            start = index * step
            mask = (t >= start) & (t < start + step * 1.4)
            local = t - start
            audio[mask] += (
                0.28 * np.sin(2 * np.pi * freq * local[mask])
                + 0.12 * np.sin(2 * np.pi * freq * 2 * local[mask])
            ) * np.exp(-5.5 * local[mask])
    else:
        raise FinishError(f"unknown bed: {kind}")
    peak = float(np.max(np.abs(audio))) or 1.0
    audio = (audio / peak * 0.7).astype(np.float32)
    write_wav(path, audio, sr)


def _fit_duration(samples: np.ndarray, sr: int, duration: float) -> np.ndarray:
    audio = resample(samples, sr)
    n = max(1, int(round(duration * SR)))
    if len(audio) < n:
        audio = np.pad(audio, (0, n - len(audio)))
    return audio[:n].astype(np.float32)


def _peak_norm(samples: np.ndarray, peak: float = 0.9) -> np.ndarray:
    level = float(np.max(np.abs(samples))) or 1.0
    return samples / level * peak


def mix_voice_and_bgm(voice: Path, bgm: Path, dst: Path, duration: float) -> None:
    """Voice plus a bed at 15% amplitude. There is no source-audio input.

    Both are peak-matched first, then the bed is multiplied by 0.15.
    A quiet floor keeps the mix from dropping below the silence gate.
    """
    voice_samples, voice_sr = read_wav(voice)
    bed_samples, bed_sr = read_wav(bgm)
    voice_audio = _peak_norm(_fit_duration(voice_samples, voice_sr, duration))
    bed_audio = _peak_norm(_fit_duration(bed_samples, bed_sr, duration)) * BGM_AMPLITUDE
    n = len(voice_audio)
    fade_in = min(n, int(0.25 * SR))
    fade_out = min(n, int(0.35 * SR))
    envelope = np.ones(n, dtype=np.float32)
    if fade_in:
        envelope[:fade_in] = np.linspace(0.35, 1.0, fade_in, dtype=np.float32)
    if fade_out:
        envelope[-fade_out:] *= np.linspace(1.0, 0.45, fade_out, dtype=np.float32)
    mixed = voice_audio + bed_audio * envelope
    floor = (0.02 * np.sin(2 * np.pi * 90.0 * np.arange(n) / SR)).astype(np.float32)
    mixed = mixed + floor
    peak = float(np.max(np.abs(mixed))) or 1.0
    if peak > 0.89:
        mixed *= 0.89 / peak
    write_wav(dst, mixed.astype(np.float32))


def mux(picture: Path, mix: Path, dst: Path) -> None:
    """Map the muted picture and the narration mix. Source audio is not an input."""
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(picture),
            "-i",
            str(mix),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-shortest",
            str(dst),
        ]
    )
    if audio_stream_count(dst) != 1:
        raise FinishError(f"expected exactly one audio stream: {dst}")


def detect_count(path: Path, audio_filter: str | None = None, video_filter: str | None = None) -> int:
    cmd = ["ffmpeg", "-i", str(path)]
    if audio_filter:
        cmd += ["-af", audio_filter]
    if video_filter:
        cmd += ["-vf", video_filter]
    cmd += ["-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    text = result.stderr
    if audio_filter and "silence_start" in audio_filter:
        return text.count("silence_start")
    if video_filter and "freezedetect" in video_filter:
        return text.count("freeze_start")
    return text.count("silence_start") + text.count("freeze_start")


def dominant_freq(path: Path) -> float:
    if path.suffix.lower() != ".wav":
        decoded = path.with_suffix(".freq.wav")
        run(["ffmpeg", "-y", "-i", str(path), "-ac", "1", "-ar", str(SR), str(decoded)])
        path = decoded
    samples, sr = read_wav(path)
    if len(samples) < sr // 10:
        return 0.0
    window = samples[: sr]
    spectrum = np.abs(np.fft.rfft(window * np.hanning(len(window))))
    freqs = np.fft.rfftfreq(len(window), 1.0 / sr)
    spectrum[0] = 0
    return float(freqs[int(np.argmax(spectrum))])
