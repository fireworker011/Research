"""Timed speech from a source video.

H3 forms the mouth from the words inside ``<d>``. Those words are the ones
read from the file. A missing read does not invent a line.
``faster_whisper`` is optional, so the import stays next to the call.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

SPEECH_MODEL = "small"
_CJK = re.compile(r"[ぁ-んァ-ン一-龥]")
_HANGUL = re.compile(r"[가-힣]")
_WHISPER = None


def speech_sidecar(path: Path) -> Path:
    return Path(str(path) + ".speech.json")


def finish_sentence(text: str) -> str:
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    raw = raw.replace("〜", "").replace("~", "")
    raw = raw.replace("。", ".").replace("？", "?").replace("！", "!")
    raw = raw.strip()
    if not raw:
        return ""
    if raw[-1] not in ".?!":
        raw += "."
    return raw


def language_tag(text: str) -> str:
    if _CJK.search(text):
        return "Japanese"
    if _HANGUL.search(text):
        return "Korean"
    return "English"


def dialogue_tag(text: str) -> str:
    spoken = finish_sentence(text)
    if not spoken:
        return ""
    return f"<d>[{language_tag(spoken)}] {spoken}</d>"


def stamp(seconds: float) -> str:
    ms = max(0, int(round(float(seconds) * 1000)))
    minutes, rem = divmod(ms, 60_000)
    sec, milli = divmod(rem, 1000)
    return f"{minutes:02d}:{sec:02d}.{milli:03d}"


def lines_in_span(lines: list[dict], start_s: float, end_s: float) -> list[dict]:
    """Lines that overlap ``[start_s, end_s)``, with times relative to ``start_s``."""
    picked = []
    for line in lines:
        line_start = float(line["start_s"])
        line_end = float(line["end_s"])
        if line_end <= start_s or line_start >= end_s:
            continue
        text = finish_sentence(str(line.get("text") or ""))
        if not text:
            continue
        picked.append(
            {
                "start_s": max(0.0, line_start - start_s),
                "end_s": min(end_s - start_s, line_end - start_s),
                "text": text,
            }
        )
    picked.sort(key=lambda item: (item["start_s"], item["end_s"]))
    return picked


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


def read_sidecar(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("speech.json は配列")
    lines = []
    for row in data:
        if not isinstance(row, dict):
            raise ValueError("speech.json の行がオブジェクトではない")
        lines.append(
            {
                "start_s": float(row["start_s"]),
                "end_s": float(row["end_s"]),
                "text": str(row.get("text") or ""),
            }
        )
    return lines


def read_source_speech(path: Path) -> tuple[list[dict], str, bool]:
    """Absolute-time lines, a note, and whether the words were actually read.

    An empty list with success means the audio was measured and nobody spoke.
    Failure leaves the mouth on the soundtrack and does not add a line.
    """
    side = speech_sidecar(path)
    if side.is_file():
        try:
            return read_sidecar(side), "せりふは隣の speech.json。口はその文だけを作る。", True
        except (OSError, ValueError, json.JSONDecodeError):
            return [], "せりふの文字は読めない。口は参照の音声に合わせる。文は足さない。", False
    if not has_audio_stream(path):
        return [], "せりふの文字は読めない。口は参照の音声に合わせる。文は足さない。", False
    try:
        lines = transcribe_file(path)
    except Exception as exc:
        return [], f"せりふの文字は読めない。口は参照の音声に合わせる。文は足さない。{exc}", False
    if not lines:
        return [], "発話は無い。口は言葉を作らない。", True
    return lines, "せりふは音声から読んだ。口はその文だけを作る。", True


def transcribe_file(path: Path) -> list[dict]:
    """Read speech with faster-whisper. The package is optional and stays local to this call."""
    model = _model()
    segments, _info = model.transcribe(str(path), vad_filter=True, word_timestamps=False)
    lines = []
    for segment in segments:
        text = finish_sentence(segment.text)
        if not text:
            continue
        lines.append(
            {
                "start_s": float(segment.start),
                "end_s": float(segment.end),
                "text": text,
            }
        )
    return lines


def _model():
    global _WHISPER
    if _WHISPER is not None:
        return _WHISPER
    from faster_whisper import WhisperModel

    device = "cpu"
    compute = "int8"
    try:
        import torch
    except ImportError:
        torch = None
    if torch is not None and torch.cuda.is_available():
        device = "cuda"
        compute = "float16"
    _WHISPER = WhisperModel(SPEECH_MODEL, device=device, compute_type=compute)
    return _WHISPER
