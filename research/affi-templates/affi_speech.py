"""Timed speech from a source video.

H3 forms the mouth from the words inside ``<d>``. Those words are the ones
read from the file. A missing read does not invent a line. A word read below
``MIN_WORD_PROB`` is written ``[unclear]``, as the H3 prompt guide asks. A line
with no clear word is left to the soundtrack. A line that crosses a range or a
cut is split by word time. ``faster_whisper`` is optional, so the import stays
next to the call.
"""

from __future__ import annotations

import gc
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from affi_media import has_audio_stream

SPEECH_MODEL = "small"
# Gate, not a measured accuracy.
MIN_WORD_PROB = 0.5
UNCLEAR = "[unclear]"
UNREAD_NOTE = "せりふの文字は読めない。口は参照の音声に合わせる。文は足さない。"
_CJK = re.compile(r"[ぁ-んァ-ン一-龥]")
_HANGUL = re.compile(r"[가-힣]")
_UNCLEAR_RUN = re.compile(r"(\s*)\[unclear\](?:\s*\[unclear\])*")
_NOT_A_WORD = re.compile(r"[\s.,?!、。？！…・\-]+")
_WHISPER = None


def speech_sidecar(path: Path) -> Path:
    return Path(str(path) + ".speech.json")


def finish_sentence(text: str, *, complete: bool = True) -> str:
    raw = re.sub(r"\s+", " ", str(text or "")).strip()
    raw = raw.replace("〜", "").replace("~", "")
    raw = raw.replace("。", ".").replace("？", "?").replace("！", "!")
    raw = raw.strip()
    if not raw:
        return ""
    if complete and raw[-1] not in ".?!":
        raw += "."
    return raw


def language_tag(text: str) -> str:
    if _CJK.search(text):
        return "Japanese"
    if _HANGUL.search(text):
        return "Korean"
    return "English"


def dialogue_tag(text: str, *, complete: bool = True, lead: str = "", tail: str = "") -> str:
    spoken = finish_sentence(text, complete=complete)
    if not spoken:
        return ""
    return f"<d>[{language_tag(spoken)}] {lead}{spoken}{tail}</d>"


def stamp(seconds: float) -> str:
    ms = max(0, int(round(float(seconds) * 1000)))
    minutes, rem = divmod(ms, 60_000)
    sec, milli = divmod(rem, 1000)
    return f"{minutes:02d}:{sec:02d}.{milli:03d}"


def clean_words(words: Any) -> list[dict]:
    kept = []
    for word in words or []:
        if not isinstance(word, Mapping):
            continue
        try:
            start = float(word["start_s"])
            end = float(word["end_s"])
        except (KeyError, TypeError, ValueError):
            continue
        text = str(word.get("text") or "")
        if not text.strip() or end < start:
            continue
        kept.append({"start_s": start, "end_s": end, "text": text, "prob": float(word.get("prob", 1.0))})
    kept.sort(key=lambda item: item["start_s"])
    return kept


def words_text(words: Sequence[Mapping[str, Any]]) -> str:
    pieces = []
    for word in words:
        text = str(word["text"])
        if float(word.get("prob", 1.0)) < MIN_WORD_PROB:
            text = (" " if text[:1].isspace() else "") + UNCLEAR
        pieces.append(text)
    joined = _UNCLEAR_RUN.sub(lambda match: match.group(1) + UNCLEAR, "".join(pieces))
    return joined.strip()


def has_clear_word(text: str) -> bool:
    return bool(_NOT_A_WORD.sub("", str(text or "").replace(UNCLEAR, "")))


def _mid(word: Mapping[str, Any]) -> float:
    return (float(word["start_s"]) + float(word["end_s"])) / 2


def piece_of(
    line: Mapping[str, Any],
    start_s: float,
    end_s: float,
    *,
    origin: float,
) -> dict | None:
    """The part of one line heard in ``[start_s, end_s)``. Times are from ``origin``.

    With words, a word belongs where its middle falls. Without words, the whole
    line belongs where its middle falls, and the other side keeps only the
    window, with no text, so the mouth there follows the soundtrack.
    """
    line_start = float(line["start_s"])
    line_end = float(line["end_s"])
    if line_end <= start_s or line_start >= end_s:
        return None
    words = line.get("words") or []
    if words:
        inside = [word for word in words if start_s <= _mid(word) < end_s]
        if not inside:
            return None
        head = any(_mid(word) < start_s for word in words)
        tail = any(_mid(word) >= end_s for word in words)
        text = words_text(inside)
        piece_start = max(start_s, float(inside[0]["start_s"]))
        piece_end = min(end_s, float(inside[-1]["end_s"]))
    else:
        owner = start_s <= (line_start + line_end) / 2 < end_s
        head = tail = False
        text = str(line.get("text") or "") if owner else ""
        piece_start = max(start_s, line_start)
        piece_end = min(end_s, line_end)
    clear = has_clear_word(text)
    return {
        "start_s": round(piece_start - origin, 3),
        "end_s": round(max(piece_start, piece_end) - origin, 3),
        "text": finish_sentence(text, complete=not tail) if clear else "",
        "speaker": str(line.get("speaker") or "S1"),
        "head_cut": head,
        "tail_cut": tail,
        "unread": not clear,
        "unclear": UNCLEAR in text,
    }


def lines_in_span(
    lines: Sequence[Mapping[str, Any]],
    start_s: float,
    end_s: float,
    *,
    origin: float | None = None,
) -> list[dict]:
    """Pieces heard in ``[start_s, end_s)``, with times from ``origin`` (default ``start_s``)."""
    base = float(start_s) if origin is None else float(origin)
    picked = [piece for line in lines if (piece := piece_of(line, float(start_s), float(end_s), origin=base))]
    picked.sort(key=lambda item: (item["start_s"], item["end_s"]))
    return picked


def assign_speakers(
    lines: list[dict],
    turns: Sequence[tuple[float, float, str]] | None,
) -> int:
    """Number speakers S1, S2, ... in the order heard. Returns the count.

    With turns, each line takes the speaker it overlaps most, else the nearest
    turn. Without turns, a ``speaker`` already on the line is kept. Lines with
    neither are one speaker.
    """
    raw: list[str] = []
    for line in lines:
        label = ""
        if turns:
            start = float(line["start_s"])
            end = float(line["end_s"])
            overlap: dict[str, float] = {}
            for t_start, t_end, t_label in turns:
                shared = min(end, t_end) - max(start, t_start)
                if shared > 0:
                    overlap[t_label] = overlap.get(t_label, 0.0) + shared
            if overlap:
                label = max(overlap.items(), key=lambda item: item[1])[0]
            else:
                mid = (start + end) / 2
                label = min(turns, key=lambda turn: min(abs(mid - turn[0]), abs(mid - turn[1])))[2]
        else:
            label = str(line.get("speaker") or "")
        raw.append(label)
    order: dict[str, str] = {}
    for label in raw:
        key = label or "_"
        if key not in order:
            order[key] = f"S{len(order) + 1}"
    for line, label in zip(lines, raw):
        line["speaker"] = order[label or "_"]
    return len(order)


def read_sidecar(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("speech.json は配列")
    lines = []
    for row in data:
        if not isinstance(row, dict):
            raise ValueError("speech.json の行がオブジェクトではない")
        line = {
            "start_s": float(row["start_s"]),
            "end_s": float(row["end_s"]),
            "text": str(row.get("text") or ""),
            "words": clean_words(row.get("words")),
        }
        if row.get("speaker"):
            line["speaker"] = str(row["speaker"])
        lines.append(line)
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
        except (OSError, ValueError, KeyError, TypeError):
            return [], UNREAD_NOTE, False
    if not has_audio_stream(path):
        return [], UNREAD_NOTE, False
    try:
        lines = transcribe_file(path)
    except Exception as exc:
        return [], f"{UNREAD_NOTE}{type(exc).__name__}", False
    if not lines:
        return [], "発話は無い。口は言葉を作らない。", True
    return lines, "せりふは音声から語の時刻まで読んだ。口はその文だけを作る。", True


def transcribe_file(path: Path) -> list[dict]:
    """Read speech with faster-whisper, with word times and word probabilities.

    The model is released afterwards, so it does not hold GPU memory while H3 runs.
    """
    try:
        return _transcribe(_model(), path)
    finally:
        release_model()


def release_model() -> None:
    global _WHISPER
    _WHISPER = None
    gc.collect()


def _transcribe(model: Any, path: Path) -> list[dict]:
    segments, _info = model.transcribe(str(path), vad_filter=True, word_timestamps=True)
    lines = []
    for segment in segments:
        words = clean_words(
            {
                "start_s": word.start,
                "end_s": word.end,
                "text": word.word,
                "prob": word.probability,
            }
            for word in (segment.words or [])
        )
        text = words_text(words) if words else str(segment.text or "")
        if not text.strip():
            continue
        lines.append(
            {
                "start_s": float(segment.start),
                "end_s": float(segment.end),
                "text": text,
                "words": words,
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
