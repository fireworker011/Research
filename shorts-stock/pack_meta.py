"""Read a shorts pack. Timings and lines come from the pack files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STOCK = Path(__file__).resolve().parent
LINES = (
    ("pet", "ペット"),
    ("konkatsu", "婚活"),
    ("beauty", "美容"),
)
FULL_DATES = ("2026-10-12", "2026-10-13", "2026-10-14")
HELD_DATES = ("2026-10-14b",)
# 日付ごとにラインの本数が違う。0 のラインはフォルダが無くてよい。
PARTIAL_COUNTS = {"2026-10-15": {"konkatsu": 5, "beauty": 5}}
DATES = FULL_DATES + HELD_DATES + tuple(PARTIAL_COUNTS)
_HELD_COUNTS = {"2026-10-14b": 3}

_NUM = r"\d+(?:\.\d+)?"
_SHOT_HEAD = re.compile(
    rf"^## ショット(\d+)\u3000({_NUM})\u2013({_NUM})秒（({_NUM})秒）\s*$",
    re.M,
)
_ACTION = re.compile(r"^動作: (.+)$", re.M)
_FENCE = re.compile(r"```text\n(.*?)\n```", re.S)
_VOICE_ROW = re.compile(rf"^\| ({_NUM})\u2013({_NUM}) \| (.+) \|$", re.M)


def shot_filename(index: int) -> str:
    return f"imagine/shot-{index:02d}.mp4"


def as_number(text: str) -> int | float:
    value = float(text)
    if value.is_integer():
        return int(value)
    return value


def parse_imagine(text: str, source: str) -> list[dict]:
    shots: list[dict] = []
    for part in re.split(r"(?=^## )", text, flags=re.M):
        head = _SHOT_HEAD.match(part)
        if head is None:
            continue
        index = int(head.group(1))
        start = as_number(head.group(2))
        end = as_number(head.group(3))
        length = as_number(head.group(4))
        if abs(float(end) - float(start) - float(length)) > 0.001:
            raise SystemExit(
                f"{source}: ショット{index} の区間 {start}–{end} と長さ {length} が一致しない"
            )
        action = _ACTION.search(part)
        fence = _FENCE.search(part)
        if action is None or fence is None:
            raise SystemExit(f"{source}: ショット{index} に動作かプロンプトが無い")
        prompt = fence.group(1)
        duration = re.match(rf"Duration: ({_NUM}) seconds\.", prompt)
        if duration is None or abs(float(duration.group(1)) - float(length)) > 0.001:
            raise SystemExit(f"{source}: ショット{index} の Duration が長さ {length} と違う")
        shots.append(
            {
                "index": index,
                "start_sec": start,
                "end_sec": end,
                "length_sec": length,
                "action": action.group(1).strip(),
                "prompt": prompt,
                "file": shot_filename(index),
            }
        )
    if not shots:
        raise SystemExit(f"{source}: ショットが無い")
    expected = list(range(1, len(shots) + 1))
    found = [shot["index"] for shot in shots]
    if found != expected:
        raise SystemExit(f"{source}: ショット番号が連続していない: {found}")
    return shots


def parse_voice(text: str, source: str) -> dict:
    if "ナレーションは無し" in text:
        return {
            "narration": False,
            "text": None,
            "window_start_sec": None,
            "window_end_sec": None,
        }
    rows = _VOICE_ROW.findall(text)
    spoken = [row for row in rows if row[2].strip() != "読まない"]
    if spoken:
        lines = [
            {
                "text": row[2].strip(),
                "window_start_sec": as_number(row[0]),
                "window_end_sec": as_number(row[1]),
            }
            for row in spoken
        ]
        read_lines = [item.strip() for item in re.findall(r"^読む文: (.+)$", text, re.M)]
        if read_lines and read_lines != [item["text"] for item in lines]:
            raise SystemExit(f"{source}: 表の文と「読む文」が違う")
        if len(lines) == 1:
            return {
                "narration": True,
                "text": lines[0]["text"],
                "window_start_sec": lines[0]["window_start_sec"],
                "window_end_sec": lines[0]["window_end_sec"],
            }
        return {
            "narration": True,
            "text": None,
            "window_start_sec": None,
            "window_end_sec": None,
            "lines": lines,
        }
    fences = _FENCE.findall(text)
    if len(fences) != 1:
        raise SystemExit(f"{source}: 読む文のブロックが1つではない")
    line = fences[0].strip()
    if "\n" in line or not line:
        raise SystemExit(f"{source}: 読む文が1文ではない")
    return {
        "narration": True,
        "text": line,
        "window_start_sec": None,
        "window_end_sec": None,
    }


def expected_slugs(date: str, line_id: str) -> int:
    if date in FULL_DATES:
        return 10
    if date in _HELD_COUNTS:
        return _HELD_COUNTS[date]
    return PARTIAL_COUNTS[date].get(line_id, 0)


def iter_packs() -> list[dict]:
    packs: list[dict] = []
    order = 0
    for line_id, line_label in LINES:
        for date in DATES:
            root = STOCK / date / line_id
            wanted = expected_slugs(date, line_id)
            if wanted == 0:
                if root.is_dir() and any((path / "IMAGINE.md").is_file() for path in root.iterdir()):
                    raise SystemExit(f"{date}/{line_id}: この日付には置かない")
                continue
            if not root.is_dir():
                raise SystemExit(f"無い: {root}")
            slugs = sorted(path.name for path in root.iterdir() if (path / "IMAGINE.md").is_file())
            if len(slugs) != wanted:
                raise SystemExit(
                    f"{date}/{line_id}: パックが {len(slugs)} 本（{wanted}本であるべき）"
                )
            for slug in slugs:
                order += 1
                pack_dir = root / slug
                imagine = (pack_dir / "IMAGINE.md").read_text()
                voice = (pack_dir / "VOICE.md").read_text()
                shots = parse_imagine(imagine, f"{date}/{line_id}/{slug}/IMAGINE.md")
                spoken = parse_voice(voice, f"{date}/{line_id}/{slug}/VOICE.md")
                packs.append(
                    {
                        "order": order,
                        "date": date,
                        "line": line_id,
                        "line_label": line_label,
                        "slug": slug,
                        "rel": f"{date}/{line_id}/{slug}",
                        "dir": pack_dir,
                        "shots": shots,
                        "voice": spoken,
                        "picture_sec": sum(shot["length_sec"] for shot in shots),
                    }
                )
    partial_total = sum(sum(counts.values()) for counts in PARTIAL_COUNTS.values())
    expected = (
        len(FULL_DATES) * len(LINES) * 10
        + sum(_HELD_COUNTS.values()) * len(LINES)
        + partial_total
    )
    if len(packs) != expected:
        raise SystemExit(f"パック数が {len(packs)}（{expected}であるべき）")
    return packs


def pack_json(pack_dir: Path) -> dict:
    target = pack_dir.resolve()
    for pack in iter_packs():
        if pack["dir"].resolve() == target:
            data = {key: value for key, value in pack.items() if key != "dir"}
            return data
    raise SystemExit(f"パックではない: {pack_dir}")


def load_speech_json(pack_dir: Path) -> dict | None:
    path = pack_dir / "voice" / "speech-length.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def atempo_chain(rate: float) -> str:
    """Speed-up chain. rate <= 1 yields an empty string (do not slow the voice to fill)."""
    if rate <= 1.0000001:
        return ""
    parts: list[str] = []
    remaining = rate
    while remaining > 2.0:
        parts.append("atempo=2.0")
        remaining /= 2.0
    parts.append(f"atempo={remaining:.6f}")
    return ",".join(parts)


def main(argv: list[str]) -> None:
    if len(argv) == 3 and argv[1] == "dump":
        json.dump(pack_json(Path(argv[2])), sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return
    raise SystemExit("usage: pack_meta.py dump PACK_DIR")


def fit_voice(
    picture_sec: float,
    voice_sec: float,
    window_start: float | None,
    window_end: float | None,
) -> dict:
    """Place the voice inside the picture. The picture length is not a return value to change."""
    if picture_sec <= 0:
        raise SystemExit("絵の長さが0")
    if voice_sec <= 0:
        raise SystemExit("声の長さが0")
    if window_start is None or window_end is None:
        start = 0.0
        end = picture_sec
    else:
        start = max(0.0, float(window_start))
        end = min(float(picture_sec), float(window_end))
    available = end - start
    if available <= 0:
        raise SystemExit("声を置く区間が絵の外")
    rate = voice_sec / available if voice_sec > available else 1.0
    return {
        "start_sec": start,
        "available_sec": available,
        "atempo": rate,
        "atempo_filter": atempo_chain(rate),
    }


if __name__ == "__main__":
    main(sys.argv)
