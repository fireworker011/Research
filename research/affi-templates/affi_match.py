"""Measure one baked clip against the source range it was made from.

Sound offset and similarity come from the loudness envelopes of both files.
Cuts are matched within two frames. Speech is compared character by character
when faster-whisper can read the clip. Lip movement itself is not measured:
that needs a face model, and none runs here. Nothing is written as a match
rate unless it was computed from the two files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

import affi_media
import affi_speech

RATE = 16000
HOP_S = 0.01
MAX_LAG_S = 0.5
CUT_TOLERANCE_S = 2 / 24
LIP_NOTE = "口の動きそのものは測っていない。顔のモデルが要る。"
_NOT_A_CHAR = re.compile(r"[\s.,?!、。？！…・\-]+")


def envelope(samples: np.ndarray, rate: int = RATE, hop_s: float = HOP_S) -> np.ndarray:
    hop = max(1, int(rate * hop_s))
    count = len(samples) // hop
    if count == 0:
        return np.zeros(0, dtype=np.float64)
    frames = samples[: count * hop].astype(np.float64).reshape(count, hop)
    return np.sqrt((frames**2).mean(axis=1))


def audio_offset(
    source: np.ndarray,
    generated: np.ndarray,
    *,
    rate: int = RATE,
    max_lag_s: float = MAX_LAG_S,
) -> tuple[float | None, float | None]:
    """(lag in ms, correlation). A positive lag means the generated sound comes later."""
    a = envelope(source, rate)
    b = envelope(generated, rate)
    size = min(len(a), len(b))
    if size < 10:
        return None, None
    a = a[:size] - a[:size].mean()
    b = b[:size] - b[:size].mean()
    if not a.any() or not b.any():
        return None, None
    reach = int(max_lag_s / HOP_S)
    best_lag, best = 0, -2.0
    for lag in range(-reach, reach + 1):
        if lag >= 0:
            x, y = a[: size - lag], b[lag:]
        else:
            x, y = a[-lag:], b[: size + lag]
        if len(x) < 10:
            continue
        denom = float(np.linalg.norm(x) * np.linalg.norm(y))
        if denom <= 0:
            continue
        value = float(np.dot(x, y) / denom)
        if value > best:
            best, best_lag = value, lag
    if best <= -2.0:
        return None, None
    return round(best_lag * HOP_S * 1000, 1), round(best, 3)


def match_cuts(
    source: Sequence[float],
    generated: Sequence[float],
    *,
    tolerance_s: float = CUT_TOLERANCE_S,
) -> dict[str, Any]:
    left = sorted(float(value) for value in source)
    right = sorted(float(value) for value in generated)
    used: set[int] = set()
    offsets: list[float] = []
    for value in left:
        pick = None
        for index, other in enumerate(right):
            if index in used or abs(other - value) > tolerance_s:
                continue
            if pick is None or abs(other - value) < abs(right[pick] - value):
                pick = index
        if pick is not None:
            used.add(pick)
            offsets.append(right[pick] - value)
    return {
        "source": len(left),
        "generated": len(right),
        "matched": len(offsets),
        "mean_offset_ms": round(float(np.mean(np.abs(offsets))) * 1000, 1) if offsets else None,
    }


def _chars(text: str) -> str:
    return _NOT_A_CHAR.sub("", str(text or "").replace(affi_speech.UNCLEAR, "")).casefold()


def char_error_rate(reference: str, heard: str) -> float | None:
    ref = _chars(reference)
    hyp = _chars(heard)
    if not ref:
        return None
    previous = list(range(len(hyp) + 1))
    for i, ref_char in enumerate(ref, start=1):
        current = [i] + [0] * len(hyp)
        for j, hyp_char in enumerate(hyp, start=1):
            current[j] = min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (ref_char != hyp_char),
            )
        previous = current
    return round(previous[-1] / len(ref), 3)


def _cuts_in(cuts: Sequence[float] | None, start_s: float, end_s: float) -> list[float] | None:
    if cuts is None:
        return None
    edge = 1 / 24
    return [round(cut - start_s, 3) for cut in cuts if start_s + edge < cut < end_s - edge]


def measure_clip(
    source: Path,
    start_s: float,
    end_s: float,
    generated: Path,
    *,
    source_cuts: Sequence[float] | None = None,
    source_lines: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Numbers measured from both files. A part that cannot be measured is None with a reason."""
    span = float(end_s) - float(start_s)
    report: dict[str, Any] = {"start_s": float(start_s), "end_s": float(end_s), "lip": LIP_NOTE}
    try:
        src = affi_media._decode_mono(Path(source), RATE, start_s, end_s)
        gen = affi_media._decode_mono(Path(generated), RATE, 0.0, span)
        lag_ms, corr = audio_offset(src, gen)
        report["sound"] = {"lag_ms": lag_ms, "correlation": corr}
    except Exception as exc:
        report["sound"] = {"lag_ms": None, "correlation": None, "why": type(exc).__name__}
    wanted = _cuts_in(source_cuts, float(start_s), float(end_s))
    found = affi_media.detect_cuts(Path(generated))
    if wanted is None or found is None:
        report["cuts"] = None
    else:
        report["cuts"] = match_cuts(wanted, [cut for cut in found if cut < span - 1 / 24])
    expected = " ".join(piece["text"] for piece in affi_speech.lines_in_span(source_lines, start_s, end_s) if piece["text"])
    if not expected:
        report["speech"] = None
    else:
        try:
            heard_lines = affi_speech.transcribe_file(Path(generated))
        except Exception as exc:
            report["speech"] = {"cer": None, "why": type(exc).__name__}
        else:
            heard = " ".join(piece["text"] for piece in affi_speech.lines_in_span(heard_lines, 0.0, span) if piece["text"])
            report["speech"] = {"cer": char_error_rate(expected, heard), "expected": expected, "heard": heard}
    return report


def summary_text(clip_id: str, report: Mapping[str, Any]) -> str:
    parts = [f"{clip_id}:"]
    sound = report.get("sound") or {}
    if sound.get("lag_ms") is None:
        parts.append("音のずれは測れない")
    else:
        parts.append(f"音のずれ {sound['lag_ms']:g}ms 相関 {sound['correlation']:g}")
    cuts = report.get("cuts")
    if cuts is None:
        parts.append("カットは比べていない")
    else:
        parts.append(f"カット 元 {cuts['source']} 本のうち {cuts['matched']} 本が2コマ以内")
    speech = report.get("speech")
    if speech is None:
        parts.append("せりふは比べていない")
    elif speech.get("cer") is None:
        parts.append("せりふは読めない")
    else:
        parts.append(f"せりふの文字の違い {speech['cer']:g}")
    parts.append(LIP_NOTE)
    return " ".join(parts)


def write_report(path: Path, report: Mapping[str, Any]) -> Path:
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
