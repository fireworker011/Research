#!/usr/bin/env python3
"""字幕とシーン表から、動画QCの通し視聴表を下書きする。

画面そのものは見ていない。一致列は人が通しで見て書き換える。
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path


GAP_MS_DEFAULT = 1500

HEADER_MAP = {
    "id": "id",
    "scene": "id",
    "シーン": "id",
    "start": "start",
    "in": "start",
    "開始": "start",
    "開始時刻": "start",
    "end": "end",
    "out": "end",
    "終了": "end",
    "終了時刻": "end",
    "visual": "visual",
    "画面": "visual",
    "画面に映っているもの": "visual",
    "映像": "visual",
    "line": "line",
    "dialogue": "line",
    "セリフ": "line",
    "台詞": "line",
    "original_audio": "original_audio",
    "has_audio": "original_audio",
    "元音声": "original_audio",
    "元音声あり": "original_audio",
}

AUDIO_YES = {"yes", "true", "1", "y", "あり", "有", "yes"}


@dataclass
class Cue:
    start_ms: int
    end_ms: int
    text: str


@dataclass
class Scene:
    start_ms: int | None
    end_ms: int | None
    visual: str
    line: str
    original_audio: bool | None
    scene_id: str


def norm(text: str) -> str:
    text = text.replace("\u3000", " ")
    return re.sub(r"\s+", "", text)


def cell(text: str) -> str:
    cleaned = text.replace("|", "｜").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def fmt_ms(value: int | None) -> str:
    if value is None:
        return ""
    if value < 0:
        value = 0
    hours = value // 3600000
    rest = value % 3600000
    minutes = rest // 60000
    rest = rest % 60000
    seconds = rest // 1000
    millis = rest % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def parse_clock(token: str) -> int:
    token = token.strip().replace(",", ".")
    parts = token.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = "0"
        minutes, seconds = parts
    elif len(parts) == 1:
        hours = "0"
        minutes = "0"
        seconds = parts[0]
    else:
        raise ValueError(f"時刻を読めない: {token}")
    if "." in seconds:
        sec_text, frac = seconds.split(".", 1)
        millis = int((frac + "000")[:3])
    else:
        sec_text = seconds
        millis = 0
    return ((int(hours) * 60 + int(minutes)) * 60 + int(sec_text)) * 1000 + millis


def parse_srt(text: str) -> list[Cue]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    cues: list[Cue] = []
    time_re = re.compile(
        r"(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})"
    )
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.split("\n")
        for index, line in enumerate(lines):
            matched = time_re.search(line)
            if not matched:
                continue
            body = "\n".join(lines[index + 1 :]).strip()
            cues.append(
                Cue(parse_clock(matched.group(1)), parse_clock(matched.group(2)), body)
            )
            break
    return cues


def parse_vtt(text: str) -> list[Cue]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    cues: list[Cue] = []
    time_re = re.compile(
        r"((?:\d{1,2}:)?\d{1,2}:\d{2}[,.]\d{1,3})\s*-->\s*((?:\d{1,2}:)?\d{1,2}:\d{2}[,.]\d{1,3})"
    )
    for block in re.split(r"\n\s*\n", text.strip()):
        if block.startswith("WEBVTT") or block.startswith("NOTE") or block.startswith("STYLE"):
            continue
        lines = block.split("\n")
        for index, line in enumerate(lines):
            matched = time_re.search(line)
            if not matched:
                continue
            body_lines = []
            for body in lines[index + 1 :]:
                body_lines.append(re.sub(r"<[^>]+>", "", body))
            cues.append(
                Cue(
                    parse_clock(matched.group(1)),
                    parse_clock(matched.group(2)),
                    "\n".join(body_lines).strip(),
                )
            )
            break
    return cues


def load_subs(path: Path) -> list[Cue]:
    text = path.read_text(encoding="utf-8-sig")
    suffix = path.suffix.lower()
    if suffix == ".vtt":
        return parse_vtt(text)
    if suffix == ".srt":
        return parse_srt(text)
    cues = parse_srt(text)
    if cues:
        return cues
    return parse_vtt(text)


def split_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [part.strip() for part in stripped.split("|")]


def map_header(name: str) -> str | None:
    key = name.strip().lower()
    if key in HEADER_MAP:
        return HEADER_MAP[key]
    if name.strip() in HEADER_MAP:
        return HEADER_MAP[name.strip()]
    return None


def parse_audio(value: str) -> bool | None:
    text = value.strip().lower()
    if not text:
        return None
    if text in AUDIO_YES or value.strip() in AUDIO_YES:
        return True
    if text in {"no", "false", "0", "n", "なし", "無"}:
        return False
    return None


def parse_optional_clock(value: str) -> int | None:
    text = value.strip()
    if not text:
        return None
    try:
        return parse_clock(text)
    except ValueError:
        return None


def rows_to_scenes(headers: list[str], rows: list[list[str]]) -> list[Scene]:
    mapped = [map_header(header) for header in headers]
    if not any(name in {"visual", "line", "original_audio", "start"} for name in mapped):
        raise ValueError("シーン表の列が分からない（画面 / セリフ / 開始 / 元音声）")
    scenes: list[Scene] = []
    for row in rows:
        if not any(cell_text.strip() for cell_text in row):
            continue
        values = {
            "id": "",
            "start": "",
            "end": "",
            "visual": "",
            "line": "",
            "original_audio": "",
        }
        for index, name in enumerate(mapped):
            if name is None or index >= len(row):
                continue
            values[name] = row[index]
        scenes.append(
            Scene(
                start_ms=parse_optional_clock(values["start"]),
                end_ms=parse_optional_clock(values["end"]),
                visual=values["visual"].strip(),
                line=values["line"].strip(),
                original_audio=parse_audio(values["original_audio"]),
                scene_id=values["id"].strip(),
            )
        )
    return scenes


def parse_markdown_table(text: str) -> list[Scene]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    index = 0
    while index < len(lines) - 1:
        if "|" not in lines[index] or not re.search(r"\|\s*-+", lines[index + 1]):
            index += 1
            continue
        headers = split_row(lines[index])
        if not any(map_header(header) for header in headers):
            index += 1
            continue
        rows: list[list[str]] = []
        cursor = index + 2
        while cursor < len(lines) and "|" in lines[cursor]:
            if not re.match(r"^\s*\|?\s*-+", lines[cursor]):
                rows.append(split_row(lines[cursor]))
            cursor += 1
        return rows_to_scenes(headers, rows)
    raise ValueError("シーン表の表が見つからない")


def parse_csv_table(path: Path) -> list[Scene]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            headers = next(reader)
        except StopIteration as exc:
            raise ValueError("シーン表が空") from exc
        rows = [row for row in reader]
    return rows_to_scenes(headers, rows)


def load_scenes(path: Path) -> list[Scene]:
    if path.suffix.lower() == ".csv":
        return parse_csv_table(path)
    return parse_markdown_table(path.read_text(encoding="utf-8-sig"))


def overlaps(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and start_b < end_a


def dialogue_gaps(cues: list[Cue], gap_ms: int) -> list[str]:
    found: list[str] = []
    ordered = sorted(cues, key=lambda cue: (cue.start_ms, cue.end_ms))
    for prev, nxt in zip(ordered, ordered[1:]):
        gap = nxt.start_ms - prev.end_ms
        if gap > gap_ms:
            found.append(
                f"- {fmt_ms(prev.end_ms)} → {fmt_ms(nxt.start_ms)} の空き {gap / 1000:.3f}秒"
            )
    return found


def scene_for_cue(cue: Cue, scenes: list[Scene]) -> list[Scene]:
    timed = [scene for scene in scenes if scene.start_ms is not None and scene.end_ms is not None]
    if not timed:
        return []
    return [
        scene
        for scene in timed
        if overlaps(cue.start_ms, cue.end_ms, scene.start_ms or 0, scene.end_ms or 0)
    ]


def match_text(spoken: str, scene_line: str) -> str:
    if not spoken and not scene_line:
        return "セリフなし。画面は要目視"
    if not spoken:
        return "要目視（字幕が無い）"
    if not scene_line:
        return "要目視（シーン表にセリフが無い）。画面との一致は目視"
    if norm(spoken) == norm(scene_line):
        return "字幕とシーン表のセリフは一致。画面は要目視"
    return f"セリフ不一致。字幕「{cell(spoken)}」／シーン表「{cell(scene_line)}」"


@dataclass
class SheetRow:
    start_ms: int | None
    end_ms: int | None
    spoken: str
    visual: str
    verdict: str


def build_rows(cues: list[Cue], scenes: list[Scene]) -> list[SheetRow]:
    rows: list[SheetRow] = []
    used: set[int] = set()
    timed = all(scene.start_ms is not None and scene.end_ms is not None for scene in scenes) and bool(scenes)
    if cues and timed:
        for cue in cues:
            matched = scene_for_cue(cue, scenes)
            for scene in matched:
                used.add(id(scene))
            visual = " / ".join(scene.visual for scene in matched if scene.visual)
            scene_line = " / ".join(scene.line for scene in matched if scene.line)
            if not visual:
                visual = "（この時刻のシーン表に画面の記載なし）"
            rows.append(
                SheetRow(cue.start_ms, cue.end_ms, cue.text, visual, match_text(cue.text, scene_line))
            )
        for scene in scenes:
            if id(scene) in used:
                continue
            rows.append(
                SheetRow(
                    scene.start_ms,
                    scene.end_ms,
                    scene.line,
                    scene.visual or "（シーン表に画面の記載なし）",
                    match_text(scene.line, scene.line if scene.line else ""),
                )
            )
        return rows
    if cues and scenes and len(cues) == len(scenes) and not timed:
        for cue, scene in zip(cues, scenes):
            visual = scene.visual or "（シーン表に画面の記載なし）"
            rows.append(SheetRow(cue.start_ms, cue.end_ms, cue.text, visual, match_text(cue.text, scene.line)))
        return rows
    if cues:
        for cue in cues:
            rows.append(
                SheetRow(
                    cue.start_ms,
                    cue.end_ms,
                    cue.text,
                    "（シーン表にこの字幕へ対応する時刻が無い）",
                    match_text(cue.text, ""),
                )
            )
        return rows
    for scene in scenes:
        visual = scene.visual or "（シーン表に画面の記載なし）"
        rows.append(SheetRow(scene.start_ms, scene.end_ms, scene.line, visual, match_text("", scene.line)))
    return rows


def qc1_text(scenes: list[Scene], cues: list[Cue]) -> str:
    known = [scene.original_audio for scene in scenes if scene.original_audio is not None]
    if not scenes or not known:
        return "未確認: シーン表に元音声の列が無い。素材に元の音があるなら、ナレーションを重ねない。"
    has_voice = any(cue.text.strip() for cue in cues) or any(scene.line.strip() for scene in scenes)
    if any(flag is True for flag in known) and has_voice:
        return "NG候補: 元音声ありの場面にセリフがある。ナレーションを重ねない。人が音を聞いて確定する。"
    if any(flag is True for flag in known):
        return "要目視: 元音声ありの場面がある。セリフ列は空。ナレーションが乗っていないか音で確認する。"
    return "下書き: シーン表は元音声なし。素材の音を聞いて、ナレーションを重ねていないか確認する。"


def qc4_text(gaps: list[str], cues: list[Cue]) -> str:
    if len(cues) < 2:
        return "該当なし: セリフ間隔を見る組が2つ未満。通しで無音の長さを確認する。"
    if gaps:
        return f"NG候補: 1.5秒を超える空きが{len(gaps)}箇所。下の一覧。"
    return "下書きOK: 字幕のセリフ間は1.5秒以内。通し視聴で無音が伸びていないか確認する。"


def build_sheet(
    cues: list[Cue],
    scenes: list[Scene],
    subs_name: str,
    scenes_name: str,
    gap_ms: int = GAP_MS_DEFAULT,
) -> str:
    gaps = dialogue_gaps(cues, gap_ms)
    rows = build_rows(cues, scenes)
    mismatch = any(row.verdict.startswith("セリフ不一致") for row in rows)
    qc2 = "要目視: セリフと字幕が画面と合うか、下の表を見ながら最初から最後まで確認する。"
    if mismatch:
        qc2 += " 字幕とシーン表のセリフが一致しない行がある。"
    lines = [
        "# 通し視聴表（下書き）",
        "",
        f"- 字幕: {subs_name}",
        f"- シーン表: {scenes_name}",
        "- この表は機械の下書き。画面は見ていない。人が最初から最後まで見て、一致列を ○ か × に書き換える。",
        "",
        "## QC5",
        "",
        "| # | 項目 | 下書き |",
        "|---|---|---|",
        f"| 1 | 元音声がある素材にナレーションを重ねない | {cell(qc1_text(scenes, cues))} |",
        f"| 2 | セリフと字幕が画面と合う | {cell(qc2)} |",
        "| 3 | 体の欠けや崩れたシーンがない | 要目視: 体の欠けや崩れた絵は機械では判断しない。通しで見て該当シーンを一致列に書く。 |",
        f"| 4 | セリフ間は1.5秒以内 | {cell(qc4_text(gaps, cues))} |",
        "| 5 | 最初から最後まで通して見る | 未実施: この表を見ながら最初から最後まで見る。見ていない動画をOKにしない。 |",
        "",
        "## 通し表",
        "",
        "| 開始 | 終了 | セリフ | 画面に映っているもの | 一致 |",
        "|---|---|---|---|---|",
    ]
    if not rows:
        lines.append("|  |  |  | （行が無い） | 要目視 |")
    for row in rows:
        lines.append(
            "| {start} | {end} | {spoken} | {visual} | {verdict} |".format(
                start=fmt_ms(row.start_ms),
                end=fmt_ms(row.end_ms),
                spoken=cell(row.spoken),
                visual=cell(row.visual),
                verdict=cell(row.verdict),
            )
        )
    lines.extend(["", "## セリフ間が1.5秒を超えた箇所", ""])
    if gaps:
        lines.extend(gaps)
    else:
        lines.append("- なし")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="字幕とシーン表から動画QCの通し視聴表を下書きする")
    parser.add_argument("--subs", required=True, help="字幕ファイル (.srt / .vtt)")
    parser.add_argument("--scenes", required=True, help="シーン表 (.md / .csv)")
    parser.add_argument("--out", required=True, help="書き出す通し視聴表 .md")
    parser.add_argument(
        "--gap-sec",
        type=float,
        default=GAP_MS_DEFAULT / 1000,
        help="セリフ間の上限秒（既定 1.5）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    subs_path = Path(args.subs)
    scenes_path = Path(args.scenes)
    out_path = Path(args.out)
    if not subs_path.is_file():
        print(f"字幕が無い: {subs_path}", file=sys.stderr)
        return 2
    if not scenes_path.is_file():
        print(f"シーン表が無い: {scenes_path}", file=sys.stderr)
        return 2
    try:
        cues = load_subs(subs_path)
        scenes = load_scenes(scenes_path)
        sheet = build_sheet(
            cues,
            scenes,
            subs_path.name,
            scenes_path.name,
            gap_ms=int(round(args.gap_sec * 1000)),
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(sheet, encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
