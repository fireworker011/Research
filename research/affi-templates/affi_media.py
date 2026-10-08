"""Measure a source video before it is split for Ref2VA.

Cuts come from ffmpeg ``scdet``. Silences come from ``silencedetect``.
Speaker turns come from pyannote in its own package folder, so the torch that
H3 uses is not replaced. Instrument names come from an AudioSet tagger.
Every threshold below is a gate, not a measured accuracy. A probe that cannot
run returns ``None``, and the caller does not invent the missing part.
``torch`` and ``transformers`` are optional on this path, so the tagger
imports them next to its call.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

FPS = 24
MIN_FRAMES = 120
# ffmpeg scdet default threshold.
SCENE_THRESHOLD = 10.0
SILENCE_DB = -35.0
SILENCE_MIN_S = 0.2
SPEAKER_SITE = Path("/content/affi-speaker")
SPEAKER_MODEL = "pyannote/speaker-diarization-3.1"
SPEAKER_SEGMENTATION = "pyannote/segmentation-3.0"
# PyTorch wrapper of WeSpeaker VoxCeleb ResNet34_LM. The official .onnx file is a different model.
SPEAKER_EMBEDDING = "pyannote/wespeaker-voxceleb-resnet34-LM"
# The model card still calls use_auth_token. huggingface_hub 1.0 dropped it.
SPEAKER_HUB = "0.36.0"
SPEAKER_AUDIO = "3.3.2"
TAGGER_MODEL = "MIT/ast-finetuned-audioset-10-10-0.4593"
TAGGER_MIN_SCORE = 0.3
TAGGER_RATE = 16000
TAGGER_WINDOW_S = 10.0
INSTRUMENTS = {
    "Piano": "piano",
    "Electric piano": "electric piano",
    "Organ": "organ",
    "Synthesizer": "synthesizer",
    "Acoustic guitar": "acoustic guitar",
    "Electric guitar": "electric guitar",
    "Bass guitar": "bass guitar",
    "Guitar": "guitar",
    "Ukulele": "ukulele",
    "Drum kit": "drum kit",
    "Drum machine": "drum machine",
    "Snare drum": "snare drum",
    "Hi-hat": "hi-hat",
    "Violin, fiddle": "violin",
    "Cello": "cello",
    "String section": "string section",
    "Harp": "harp",
    "Trumpet": "trumpet",
    "Saxophone": "saxophone",
    "Flute": "flute",
    "Clarinet": "clarinet",
    "Accordion": "accordion",
    "Harmonica": "harmonica",
    "Marimba, xylophone": "marimba",
    "Glockenspiel": "glockenspiel",
    "Choir": "choir",
}

_CUT = re.compile(r"lavfi\.scd\.time:\s*([0-9.]+)")
_SILENCE_START = re.compile(r"silence_start:\s*(-?[0-9.]+)")
_SILENCE_END = re.compile(r"silence_end:\s*(-?[0-9.]+)")
_TAGGER = None

# Penalty for a range boundary. A cut costs nothing, silence little, inside speech a lot.
_AT_CUT = 0.0
_NEAR_CUT = 0.5
_IN_SILENCE = 1.0
_ELSEWHERE = 2.0
_PER_RANGE = 5.0
_PER_PAD_FRAME = 0.02
_HARD_WEIGHT = 100.0


def has_audio_stream(path: Path) -> bool:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return False
    try:
        text = subprocess.check_output(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "csv=p=0",
                str(path),
            ],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return "audio" in text


def _ffmpeg_log(args: Sequence[str]) -> str | None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    try:
        done = subprocess.run(
            [ffmpeg, "-hide_banner", "-nostats", *args],
            capture_output=True,
            text=True,
            timeout=600,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    return done.stderr


def parse_cuts(log: str) -> list[float]:
    found = sorted({round(float(value), 3) for value in _CUT.findall(log)})
    return [value for value in found if value > 0]


def detect_cuts(path: Path) -> list[float] | None:
    """Scene changes in source seconds. None when ffmpeg cannot read the file."""
    log = _ffmpeg_log(["-i", str(path), "-an", "-vf", f"scdet=threshold={SCENE_THRESHOLD:g}", "-f", "null", "-"])
    if log is None:
        return None
    return parse_cuts(log)


def parse_silences(log: str, duration_s: float) -> list[tuple[float, float]]:
    starts = [float(value) for value in _SILENCE_START.findall(log)]
    ends = [float(value) for value in _SILENCE_END.findall(log)]
    spans: list[tuple[float, float]] = []
    for index, start in enumerate(starts):
        end = ends[index] if index < len(ends) else duration_s
        start = max(0.0, start)
        end = min(float(duration_s), end)
        if end > start:
            spans.append((round(start, 3), round(end, 3)))
    return spans


def detect_silences(path: Path, duration_s: float) -> list[tuple[float, float]] | None:
    """Silent stretches in source seconds. None without an audio stream."""
    if not has_audio_stream(path):
        return None
    log = _ffmpeg_log(
        [
            "-i",
            str(path),
            "-vn",
            "-af",
            f"silencedetect=noise={SILENCE_DB:g}dB:d={SILENCE_MIN_S:g}",
            "-f",
            "null",
            "-",
        ]
    )
    if log is None:
        return None
    return parse_silences(log, duration_s)


def align_frames(frames: int) -> int:
    value = int(frames)
    while value % 17 != 5:
        value += 1
    return value


def _speech_marks(total: int, lines: Sequence[Mapping[str, Any]]) -> list[int]:
    """2 inside a word or a line read without words, 1 between words of one line."""
    marks = [0] * (total + 1)
    for line in lines:
        words = line.get("words") or []
        start = int(float(line["start_s"]) * FPS) + 1
        end = int(float(line["end_s"]) * FPS + 0.999999)
        if not words:
            for k in range(max(0, start), min(total, end - 1) + 1):
                marks[k] = 2
            continue
        for k in range(max(0, start), min(total, end - 1) + 1):
            marks[k] = max(marks[k], 1)
        for word in words:
            w_start = int(float(word["start_s"]) * FPS) + 1
            w_end = int(float(word["end_s"]) * FPS + 0.999999)
            for k in range(max(0, w_start), min(total, w_end - 1) + 1):
                marks[k] = 2
    return marks


def _base_costs(
    total: int,
    cuts: Sequence[float] | None,
    silences: Sequence[tuple[float, float]] | None,
) -> tuple[list[float], list[int]]:
    """Boundary cost and a sound mark. The sound mark stands in for speech when the words were not read."""
    cost = [_ELSEWHERE] * (total + 1)
    sound = [0] * (total + 1)
    if silences is not None:
        sound = [1] * (total + 1)
        for start, end in silences:
            for k in range(max(0, int(start * FPS + 0.999999)), min(total, int(end * FPS)) + 1):
                cost[k] = _IN_SILENCE
                sound[k] = 0
    for cut in cuts or []:
        center = int(round(float(cut) * FPS))
        for k in (center - 1, center + 1):
            if 0 <= k <= total:
                cost[k] = min(cost[k], _NEAR_CUT)
        if 0 <= center <= total:
            cost[center] = _AT_CUT
    return cost, sound


def _solve(
    end_frames: float,
    max_frames: int,
    cost: list[float],
    hard: list[int],
) -> tuple[list[int], float, int] | None:
    """Range boundaries on the 24 fps grid. Returns (boundaries, cost, hard sum)."""
    grid = int(end_frames + 1e-6)
    inf = float("inf")
    best = [inf] * (grid + 1)
    back = [-1] * (grid + 1)
    hard_sum = [0] * (grid + 1)
    best[0] = 0.0
    pad = [0.0] * (max_frames + 1)
    for length in range(MIN_FRAMES, max_frames + 1):
        pad[length] = _PER_RANGE + _PER_PAD_FRAME * (align_frames(length) - length)
    for k in range(MIN_FRAMES, grid + 1):
        here = cost[k] + _HARD_WEIGHT * hard[k]
        low = max(0, k - max_frames)
        high = k - MIN_FRAMES
        top = inf
        pick = -1
        for prev in range(low, high + 1):
            value = best[prev]
            if value == inf:
                continue
            value += pad[k - prev]
            if value < top:
                top = value
                pick = prev
        if pick >= 0:
            best[k] = top + here
            back[k] = pick
            hard_sum[k] = hard_sum[pick] + hard[k]
    finish = inf
    last = -1
    for k in range(0, grid + 1):
        if best[k] == inf:
            continue
        tail = end_frames - k
        frames = int(round(tail))
        if tail < MIN_FRAMES - 1e-6 or frames > max_frames:
            continue
        value = best[k] + _PER_RANGE + _PER_PAD_FRAME * (align_frames(max(frames, MIN_FRAMES)) - tail)
        if value < finish:
            finish = value
            last = k
    if last < 0:
        return None
    marks: list[int] = []
    k = last
    while k > 0:
        marks.append(k)
        k = back[k]
    marks.reverse()
    return marks, finish, hard_sum[last]


def plan_spans(
    duration_s: float,
    *,
    steps: Sequence[tuple[int, int]],
    cuts: Sequence[float] | None = None,
    silences: Sequence[tuple[float, float]] | None = None,
    lines: Sequence[Mapping[str, Any]] = (),
) -> tuple[list[tuple[float, float]], int]:
    """Ranges that cover the file. Returns the ranges and the short edge of the step used.

    ``steps`` is ``(largest aligned frames, short edge)`` in the order to try.
    The first step whose boundaries all avoid speech wins. Without a reading,
    sound stands in for speech when silences were measured.
    """
    duration = float(duration_s)
    if duration <= 0:
        raise ValueError("元動画の秒数が 0")
    end_frames = duration * FPS
    if end_frames < MIN_FRAMES:
        edge = min(steps)[1] if steps else 0
        return [(0.0, round(duration, 3))], edge
    total = int(end_frames + 1e-6)
    cost, sound = _base_costs(total, cuts, silences)
    marks = _speech_marks(total, lines) if lines else [0] * (total + 1)
    hard = [max(marks[k], sound[k] if not lines else 0) for k in range(total + 1)]
    found: list[tuple[int, int, list[int], int]] = []
    for order, (max_frames, edge) in enumerate(steps):
        solved = _solve(end_frames, int(max_frames), cost, hard)
        if solved is None:
            continue
        bounds, _score, hard_total = solved
        found.append((hard_total, order, bounds, edge))
        if hard_total == 0:
            break
    if not found:
        raise ValueError(f"H3 の 5〜15 秒に分けられない: {duration:g}秒")
    _hard_total, _order, bounds, edge = min(found, key=lambda item: (item[0], item[1]))
    points = [0.0] + [round(k / FPS, 3) for k in bounds] + [round(duration, 3)]
    return [(points[i], points[i + 1]) for i in range(len(points) - 1)], edge


def _decode_mono(path: Path, rate: int, start_s: float | None = None, end_s: float | None = None) -> np.ndarray:
    """Mono float32 samples through ffmpeg."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg が無い")
    args = [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(path)]
    if start_s is not None and end_s is not None:
        args.extend(["-ss", f"{float(start_s):.3f}", "-to", f"{float(end_s):.3f}"])
    args.extend(["-vn", "-ac", "1", "-ar", str(int(rate)), "-f", "f32le", "-"])
    raw = subprocess.run(args, capture_output=True, check=True, timeout=600).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def _tagger():
    """AudioSet tagger. transformers and torch are optional on this path."""
    global _TAGGER
    if _TAGGER is not None:
        return _TAGGER
    import torch
    from transformers import ASTFeatureExtractor, ASTForAudioClassification

    extractor = ASTFeatureExtractor.from_pretrained(TAGGER_MODEL)
    model = ASTForAudioClassification.from_pretrained(TAGGER_MODEL).eval()
    _TAGGER = (torch, extractor, model)
    return _TAGGER


def labels_from_scores(scores: Mapping[str, float]) -> list[str]:
    picked = [
        (score, INSTRUMENTS[label])
        for label, score in scores.items()
        if label in INSTRUMENTS and float(score) >= TAGGER_MIN_SCORE
    ]
    picked.sort(key=lambda item: -item[0])
    names: list[str] = []
    for _score, name in picked:
        if name not in names:
            names.append(name)
    return names


def music_tags(path: Path, spans: Sequence[tuple[float, float]]) -> tuple[list[list[str]] | None, str]:
    """Instrument names per range. None when the tagger cannot run."""
    try:
        samples = _decode_mono(path, TAGGER_RATE)
        torch, extractor, model = _tagger()
    except Exception as exc:
        return None, f"楽器は調べていない。{type(exc).__name__}"
    id2label = model.config.id2label
    window = int(TAGGER_WINDOW_S * TAGGER_RATE)
    found: list[list[str]] = []
    for start_s, end_s in spans:
        part = samples[int(start_s * TAGGER_RATE) : int(end_s * TAGGER_RATE)]
        best: dict[str, float] = {}
        for offset in range(0, max(1, len(part)), window):
            piece = part[offset : offset + window]
            if len(piece) < TAGGER_RATE:
                continue
            inputs = extractor(piece, sampling_rate=TAGGER_RATE, return_tensors="pt")
            with torch.no_grad():
                scores = torch.sigmoid(model(**inputs).logits)[0].tolist()
            for index, score in enumerate(scores):
                label = id2label[index]
                best[label] = max(best.get(label, 0.0), float(score))
        found.append(labels_from_scores(best))
    return found, "楽器は AudioSet の判定器で調べた。"


def speaker_gate_lines() -> list[str]:
    """What the token account must accept before this pipeline can download."""
    return [
        f"話者は {SPEAKER_MODEL}。このページは config.yaml だけで、重みは別のモデルにある。",
        f"埋め込みは WeSpeaker の VoxCeleb ResNet34_LM。読むのは {SPEAKER_EMBEDDING}。公式の .onnx は使わない。",
        "利用条件は、次の2つにこのトークンのアカウントで同意する。",
        f"https://huggingface.co/{SPEAKER_MODEL}",
        f"https://huggingface.co/{SPEAKER_SEGMENTATION}",
    ]


def speaker_site_ready(site: Path = SPEAKER_SITE) -> bool:
    """True when this folder has the pyannote and hub pins that can load the pipeline."""
    return (
        (site / "pyannote" / "audio").is_dir()
        and (site / f"pyannote_audio-{SPEAKER_AUDIO}.dist-info").is_dir()
        and (site / f"huggingface_hub-{SPEAKER_HUB}.dist-info").is_dir()
    )


def speaker_install_argv(site: Path = SPEAKER_SITE) -> list[str]:
    """pyannote and a CPU torch in their own folder. The H3 torch is not touched.

    huggingface_hub stays on 0.36 because the 3.1 pipeline still passes ``use_auth_token``.
    """
    return [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-q",
        "--upgrade",
        "--target",
        str(site),
        "--extra-index-url",
        "https://download.pytorch.org/whl/cpu",
        "torch==2.5.1+cpu",
        "torchaudio==2.5.1+cpu",
        f"pyannote.audio=={SPEAKER_AUDIO}",
        f"huggingface_hub=={SPEAKER_HUB}",
        "numpy<2",
    ]


def parse_turns(data: Any) -> list[tuple[float, float, str]]:
    turns = []
    for row in data or []:
        start = float(row["start_s"])
        end = float(row["end_s"])
        if end > start:
            turns.append((start, end, str(row["speaker"])))
    turns.sort()
    return turns


def diarize(path: Path, *, site: Path = SPEAKER_SITE) -> tuple[list[tuple[float, float, str]] | None, str]:
    """Speaker turns from pyannote in its own folder. None when it is not installed or fails."""
    if not speaker_site_ready(site):
        return None, "話者は分けていない。pyannote が入っていない。"
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or ""
    if not token:
        return None, "話者は分けていない。HF_TOKEN が無い。"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None, "話者は分けていない。ffmpeg が無い。"
    script = Path(__file__).resolve().parent / "affi_speaker.py"
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "speech.wav"
        out = Path(tmp) / "turns.json"
        try:
            subprocess.run(
                [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", str(wav)],
                check=True,
                timeout=600,
            )
            env = {**os.environ, "PYTHONPATH": str(site), "HF_TOKEN": token}
            done = subprocess.run(
                [sys.executable, str(script), str(wav), str(out), SPEAKER_MODEL],
                env=env,
                capture_output=True,
                text=True,
                timeout=1800,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return None, f"話者は分けていない。{type(exc).__name__}"
        if done.returncode != 0 or not out.is_file():
            tail = (done.stderr or "").strip().splitlines()[-1:] or [""]
            return None, f"話者は分けていない。pyannote が止まった。{tail[0][:200]}"
        turns = parse_turns(json.loads(out.read_text(encoding="utf-8")))
    labels = {label for _start, _end, label in turns}
    return turns, f"話者は pyannote で {len(labels)} 人に分けた。"
