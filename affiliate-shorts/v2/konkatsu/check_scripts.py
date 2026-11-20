#!/usr/bin/env python3
"""完了条件の確認。収録はしない。投稿もしない。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IDS = ["01", "02", "03", "04", "05"]
FILES = ["script.md", "narration.txt", "subs.srt", "pr_last2s.txt", "description.txt"]
LAST = "プロフィールを見直そう"
PR = "#PR\n広告を含みます\n"
BANNED = [
    "詳しくは",
    "リンク",
    "資料請求",
    "無料",
    "概要欄",
    "フォロー",
    "チャンネル",
    "http",
    "https",
    "申込",
    "タップ",
    "登録",
    "こちら",
    "px.a8.net",
    "AFFILIATE",
]
NAMES = ["紫藤", "来島", "四国めたん", "白上", "玄野", "剣崎", "青山龍星", "Pappy", "ペアーズ"]
FIELDS = ["場面", "構図", "色", "出だし", "テンポ"]


def parse_srt(text: str) -> list[tuple[int, int, str]]:
    blocks = re.split(r"\n\s*\n", text.strip())
    cues = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            raise SystemExit(f"srt block is short: {block!r}")
        times = lines[1]
        match = re.fullmatch(
            r"(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)",
            times,
        )
        if not match:
            raise SystemExit(f"bad time line: {times}")
        nums = [int(n) for n in match.groups()]

        def to_ms(h: int, m: int, s: int, ms: int) -> int:
            return ((h * 60 + m) * 60 + s) * 1000 + ms

        start = to_ms(*nums[:4])
        end = to_ms(*nums[4:])
        cues.append((start, end, "\n".join(lines[2:])))
    return cues


def main() -> int:
    errors: list[str] = []
    totals: list[tuple[str, int]] = []
    field_values: dict[str, list[str]] = {name: [] for name in FIELDS}
    for vid in IDS:
        folder = ROOT / vid
        for name in FILES:
            if not (folder / name).is_file():
                errors.append(f"{vid}/{name} が無い")
        narration = (folder / "narration.txt").read_text(encoding="utf-8")
        srt_text = (folder / "subs.srt").read_text(encoding="utf-8")
        pr = (folder / "pr_last2s.txt").read_text(encoding="utf-8")
        description = (folder / "description.txt").read_text(encoding="utf-8")
        script = (folder / "script.md").read_text(encoding="utf-8")
        if pr != PR:
            errors.append(f"{vid}/pr_last2s.txt が指定の2行ではない")
        narration_lines = [line for line in narration.splitlines() if line]
        if not narration_lines or narration_lines[-1] != LAST:
            errors.append(f"{vid}/narration.txt の最後が {LAST} ではない")
        if description.splitlines()[-1] != LAST:
            errors.append(f"{vid}/description.txt の最後が {LAST} ではない")
        if "#PR" not in description.splitlines():
            errors.append(f"{vid}/description.txt に #PR が無い")
        if "フィクションです" not in description:
            errors.append(f"{vid}/description.txt に創作である旨が無い")
        for word in BANNED:
            if word in narration or word in description or word in script:
                errors.append(f"{vid} に禁止語 {word}")
        for name in NAMES:
            blob = narration + description + script + srt_text
            if name in blob:
                errors.append(f"{vid} に実在名または既存素材の固有名 {name}")
        cues = parse_srt(srt_text)
        if not cues:
            errors.append(f"{vid} の字幕が空")
            continue
        prev = None
        for index, (start, end, text) in enumerate(cues, start=1):
            if end <= start:
                errors.append(f"{vid} cue {index} の長さが0以下")
            if prev is not None and start != prev:
                errors.append(f"{vid} cue {index} が前の字幕と連続していない")
            prev = end
            for line in text.splitlines():
                if len(line) > 16:
                    errors.append(f"{vid} cue {index} が16文字超 ({len(line)}): {line}")
        body = cues[:-1]
        last = cues[-1]
        if last[1] - last[0] != 2000:
            errors.append(f"{vid} の末尾が2.000秒ではない: {last[1] - last[0]}ms")
        if last[2] != "#PR\n広告を含みます":
            errors.append(f"{vid} の末尾字幕がPRではない")
        for _start, _end, text in body:
            if "#PR" in text or "広告" in text or "http" in text:
                errors.append(f"{vid} の本編字幕にPRまたはURL")
            for word in BANNED:
                if word in text:
                    errors.append(f"{vid} の本編字幕に禁止語 {word}")
        spoken = "".join(narration_lines)
        caption = "".join(text for _s, _e, text in body)
        if spoken != caption:
            errors.append(f"{vid} のナレーションと本編字幕が一致しない")
        if body[-1][2] != LAST:
            errors.append(f"{vid} の本編最後の字幕が {LAST} ではない")
        totals.append((vid, cues[-1][1]))
        for name in FIELDS:
            match = re.search(rf"^- {name}: (.+)$", script, re.M)
            if not match:
                errors.append(f"{vid}/script.md に {name} が無い")
            else:
                field_values[name].append(match.group(1))
    for name, values in field_values.items():
        if len(values) == len(IDS) and len(set(values)) != len(IDS):
            errors.append(f"{name} が5本で揃っていない")
    totals.sort(key=lambda item: item[1])
    for (left_id, left_ms), (right_id, right_ms) in zip(totals, totals[1:]):
        gap = right_ms - left_ms
        if gap < 5000:
            errors.append(f"長さが近い: {left_id} と {right_id} の差が {gap}ms")
    if errors:
        print("\n".join(errors))
        return 1
    print("ok")
    for vid, total in sorted(totals):
        print(f"{vid}\t{total / 1000:.3f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
