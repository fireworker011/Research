"""commonalities.yaml. Missing cells stay the string 不明. Counts are not invented."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from minimaxh3.affi.products import GENRES, PLATFORMS

SCHEMA = "affi-commonalities/v1"
UNKNOWN = "不明"
PATTERN_IDS = ("introduce", "buy_before", "missing_on_camera", "daily_same", UNKNOWN)
CELL_KEYS = (
    "genre",
    "platform",
    "growing_n",
    "struggling_n",
    "hook_type",
    "duration_s",
    "caption_placement",
    "lead",
    "product_show",
    "do_not",
    "pattern_id",
)


def load_commonalities(path: Path | str) -> dict[str, Any]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise ValueError(f"schema は {SCHEMA}")
    cells = raw.get("cells")
    if not isinstance(cells, list):
        raise ValueError("cells が無い")
    seen: set[tuple[str, str]] = set()
    for cell in cells:
        if not isinstance(cell, dict):
            raise ValueError("cell は mapping")
        missing = [key for key in CELL_KEYS if key not in cell]
        if missing:
            raise ValueError("cell に足りない: " + ",".join(missing))
        genre = str(cell["genre"])
        platform = str(cell["platform"])
        if genre not in GENRES or platform not in PLATFORMS:
            raise ValueError(f"未知のジャンルかプラットフォーム: {genre} {platform}")
        if (genre, platform) in seen:
            raise ValueError(f"セルが重複: {genre} {platform}")
        seen.add((genre, platform))
        if str(cell["pattern_id"]) not in PATTERN_IDS:
            raise ValueError("pattern_id は introduce / buy_before / missing_on_camera / daily_same / 不明")
        if not isinstance(cell["do_not"], list) or not cell["do_not"]:
            raise ValueError("do_not は1件以上")
    if seen != {(g, p) for g in GENRES for p in PLATFORMS}:
        raise ValueError("ジャンル×プラットフォームの9セルが要る")
    return raw


def find_cell(doc: dict[str, Any], genre: str, platform: str) -> dict[str, Any]:
    for cell in doc["cells"]:
        if cell["genre"] == genre and cell["platform"] == platform:
            return cell
    raise KeyError(f"{genre} {platform}")
