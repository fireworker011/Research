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
DATES = ("2026-10-12", "2026-10-13")

_SHOT_HEAD = re.compile(
    r"^## ショット(\d+)\u3000(\d+)\u2013(\d+)秒（(\d+)秒）\s*$",
    re.M,
)
_ACTION = re.compile(r"^動作: (.+)$", re.M)
_FENCE = re.compile(r"```text\n(.*?)\n```", re.S)
_VOICE_ROW = re.compile(r"^\| (\d+)\u2013(\d+) \| (.+) \|$", re.M)
_READ_LINE = re.compile(r"^読む文: (.+)$", re.M)


def shot_filename(index: int) -> str:
    return f"imagine/shot-{index:02d}.mp4"


def parse_imagine(text: str, source: str) -> list[dict]:
    shots: list[dict] = []
    for part in re.split(r"(?=^## )", text, flags=re.M):
        head = _SHOT_HEAD.match(part)
        if head is None:
            continue
        index = int(head.group(1))
        start = int(head.group(2))
        end = int(head.group(3))
        length = int(head.group(4))
        if end - start != length:
            raise SystemExit(
                f"{source}: ショット{index} の区間 {start}–{end} と長さ {length} が一致しない"
            )
        action = _ACTION.search(part)
        fence = _FENCE.search(part)
        if action is None or fence is None:
            raise SystemExit(f"{source}: ショット{index} に動作かプロンプトが無い")
        prompt = fence.group(1)
        duration = re.match(r"Duration: (\d+) seconds\.", prompt)
        if duration is None or int(duration.group(1)) != length:
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
        if len(spoken) != 1:
            raise SystemExit(f"{source}: 読む行が1行ではない")
        line = spoken[0][2].strip()
        read_line = _READ_LINE.search(text)
        if read_line is not None and read_line.group(1).strip() != line:
            raise SystemExit(f"{source}: 表の文と「読む文」が違う")
        return {
            "narration": True,
            "text": line,
            "window_start_sec": int(spoken[0][0]),
            "window_end_sec": int(spoken[0][1]),
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


def iter_packs() -> list[dict]:
    packs: list[dict] = []
    order = 0
    for line_id, line_label in LINES:
        for date in DATES:
            root = STOCK / date / line_id
            if not root.is_dir():
                raise SystemExit(f"無い: {root}")
            slugs = sorted(path.name for path in root.iterdir() if (path / "IMAGINE.md").is_file())
            if len(slugs) != 10:
                raise SystemExit(f"{date}/{line_id}: パックが {len(slugs)} 本（10本であるべき）")
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
    if len(packs) != 60:
        raise SystemExit(f"パック数が {len(packs)}（60であるべき）")
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
