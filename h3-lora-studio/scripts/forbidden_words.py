"""Editable forbidden terms for h3-lora-studio.

Minors and affiliate URL fragments cannot be turned off from the JSON file.
`extra` and the Colab form are what the user can add or remove.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "catalog" / "forbidden.json"

LOCKED_MINORS = (
    "shota",
    "syota",
    "loli",
    "lolita",
    "loliita",
    "child",
    "children",
    "kid",
    "kids",
    "toddler",
    "infant",
    "minor",
    "underage",
    "teen",
    "teenage",
    "teenager",
    "小学生",
    "中学生",
    "pedo",
)
LOCKED_COMMERCIAL = ("px.a8.net", "a8mat=")
DEFAULT_BOUNDARY = ("child", "children", "kid", "kids", "minor", "teen")
SAFETY_PREFIX = r"(?:no|not\s+a|not|without|avoid|exclude|never)"


def _clean_terms(rows: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    if not isinstance(rows, list):
        return out
    for row in rows:
        term = str(row or "").strip()
        if not term:
            continue
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(term)
    return out


def parse_extra_terms(text: str | None) -> list[str]:
    raw = str(text or "").replace("、", ",")
    return _clean_terms([p.strip() for p in raw.split(",")])


def load_forbidden(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path or DEFAULT_PATH)
    data: dict[str, Any] = {}
    if p.is_file():
        loaded = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data = loaded
    minors = _clean_terms(list(LOCKED_MINORS) + list(data.get("minors") or []))
    extra = _clean_terms(data.get("extra") or [])
    boundary = {
        str(x).strip().lower()
        for x in (data.get("word_boundary") or DEFAULT_BOUNDARY)
        if str(x).strip()
    } or set(DEFAULT_BOUNDARY)
    return {
        "path": str(p),
        "minors": minors,
        "extra": extra,
        "word_boundary": sorted(boundary),
    }


def extra_terms(path: Path | str | None = None) -> list[str]:
    return list(load_forbidden(path)["extra"])


def _pattern_for(term: str, boundary: set[str]) -> str:
    escaped = re.escape(term)
    if term.lower() in boundary and re.fullmatch(r"[A-Za-z]+", term):
        return rf"\b{escaped}\b"
    return escaped


def _subject_re(minors: list[str], boundary: set[str]) -> re.Pattern[str]:
    parts = [_pattern_for(t, boundary) for t in minors if t]
    if not parts:
        parts = [_pattern_for(t, boundary) for t in LOCKED_MINORS]
    return re.compile("(" + "|".join(parts) + ")", re.I)


def _safety_re(minors: list[str]) -> re.Pattern[str]:
    body = "|".join(re.escape(t) for t in minors if t) or "child"
    grouped = rf"(?:{body})"
    return re.compile(
        rf"(?i)\b{SAFETY_PREFIX}\s+(?:a\s+)?{grouped}"
        rf"(?:\s*,\s*(?:no\s+|not\s+a\s+|not\s+)?{grouped})*"
    )


def forbidden_hits(
    text: str,
    *,
    negative: str | None = None,
    extra: list[str] | None = None,
    path: Path | str | None = None,
) -> list[str]:
    """Flag requested minors and extra banned strings. 'no child' is not a request."""
    cfg = load_forbidden(path)
    minors = list(cfg["minors"])
    extra_terms_ = _clean_terms(list(cfg["extra"]) + list(extra or []))
    boundary = set(cfg["word_boundary"])
    cleaned = str(text or "")
    neg = str(negative or "").strip()
    if neg:
        cleaned = cleaned.replace(neg, " ")
    cleaned = _safety_re(minors).sub(" ", cleaned)
    hits: set[str] = set()
    for match in _subject_re(minors, boundary).finditer(cleaned):
        hits.add(match.group(0).lower())
    low = cleaned.lower()
    for term in list(LOCKED_COMMERCIAL) + extra_terms_:
        if term.lower() in low:
            hits.add(term.lower())
    return sorted(hits)
