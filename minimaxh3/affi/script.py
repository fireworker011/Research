"""Load the 2026-10-03 run scripts. This module does not write new lines."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

# Inbox canvas is the grokbot 9:16 high size. The 9s FL2VA token budget in the
# runs was 640x1152, which h3-i2v-job rejects for mode i2v.
INBOX_W = 768
INBOX_H = 1344

PATTERNS: dict[str, dict[str, Any]] = {
    "introduce": {
        "fixture": "run01.md",
        "genre": "pet_food",
        "product": "kanetora",
        "parts": (
            {"key": "6s", "duration_s": 6.0, "mode": "i2v", "ref": "dog", "template_canvas": "768x1344"},
            {"key": "9s", "duration_s": 9.0, "mode": "i2v", "ref": "dog", "template_canvas": "640x1152"},
        ),
    },
    "buy_before": {
        "fixture": "run02.md",
        "genre": "beauty_skincare",
        "product": "orbis",
        "parts": (
            {"key": "6s", "duration_s": 6.0, "mode": "i2v", "ref": "sakura", "template_canvas": "768x1344"},
            {"key": "9s", "duration_s": 9.0, "mode": "i2v", "ref": "sakura", "template_canvas": "640x1152"},
        ),
    },
    "missing_on_camera": {
        "fixture": "run03.md",
        "genre": "pet_camera",
        "product": "furbo",
        "parts": (
            {"key": "6s", "duration_s": 6.0, "mode": "i2v", "ref": "dog", "template_canvas": "768x1344"},
            {"key": "9s", "duration_s": 9.0, "mode": "i2v", "ref": "dog", "template_canvas": "640x1152"},
        ),
    },
}

_ROW = re.compile(
    r"^\|\s*([0-9.]+)-([0-9.]+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*[^|]+\|\s*[^|]+\|\s*([^|]+?)\s*\|"
)
_PUNCT = set("、。！？…「」『』（）()・,.!?")


def char_count(text: str) -> int:
    return sum(1 for ch in text if not ch.isspace() and ch not in _PUNCT)


def load_pattern(pattern_id: str) -> dict[str, Any]:
    spec = PATTERNS[pattern_id]
    text = (FIXTURE_DIR / spec["fixture"]).read_text(encoding="utf-8")
    script = parse_run(text)
    parts = []
    for meta, prompt in zip(spec["parts"], script["prompts"], strict=True):
        parts.append({**meta, "prompt": prompt, "width": INBOX_W, "height": INBOX_H})
    return {
        "pattern_id": pattern_id,
        "genre": spec["genre"],
        "product": spec["product"],
        "hook": script["hook"],
        "beats": script["beats"],
        "title": script["title"],
        "description": script["description"],
        "parts": parts,
    }


def parse_run(text: str) -> dict[str, Any]:
    hook_m = re.search(r"## フック1行\n+\*\*(.+?)\*\*", text)
    title_m = re.search(r"## タイトル\n+`([^`]+)`", text)
    desc_m = re.search(r"## 概要欄\n+```text\n(.*?)```", text, re.S)
    if not hook_m or not title_m or not desc_m:
        raise ValueError("台本のフック・タイトル・概要欄が読めない")
    beats = []
    for line in text.splitlines():
        row = _ROW.match(line)
        if not row:
            continue
        start, end, role, spoken, caption = row.groups()
        beats.append(
            {
                "start": float(start),
                "end": float(end),
                "role": role.strip(),
                "spoken": spoken.strip(),
                "caption": caption.strip(),
            }
        )
    prompts = []
    for chunk in re.split(r"\n#### ", text):
        found = re.search(r"```text\n(For the target video,.*?)```", chunk, re.S)
        if found:
            prompts.append(found.group(1).strip() + "\n")
    if len(beats) != 5 or len(prompts) != 2:
        raise ValueError(f"台本の行数={len(beats)} プロンプト数={len(prompts)}")
    return {
        "hook": hook_m.group(1).strip(),
        "title": title_m.group(1).strip(),
        "description": desc_m.group(1).strip() + "\n",
        "beats": beats,
        "prompts": prompts,
    }
