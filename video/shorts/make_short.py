#!/usr/bin/env python3
"""台本.md と jobs.json から縦の短い動画を作る。

声は VOICEVOX の CPU エンジン（起動しているとき）。無いときは edge-tts。
等倍のまま置く。10.5秒に入らないときは言葉を削る。早回しはしない。
書き出しの直後に検品を実行する。投稿はしない。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import struct
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from video.common.flat_mix import BGM_RATIO, filter_path, font_path

RATE = 48000
VOICEVOX_URL = "http://127.0.0.1:50021"
ADULT_MARKERS = ("ヌード", "全裸", "性交", "アダルトビデオ", "エロ動画")
DASH = r"[\-\u2013\u2014〜~]"
PREFIXES = ("だから、", "だから", "でも、", "でも", "それで、", "それで")
SOFT_WORDS = ("感じの", "もう、", "もう")
EDGE_VOICE = {
    "yorunotana": "ja-JP-KeitaNeural",
}
# 金メモとペットは冥鳴ひまり。yorunotana は話者13。婚活は四国めたん（女性・標準）。
VOICEVOX_SPEAKER = {
    "pet": 14,
    "kane": 14,
    "yorunotana": 13,
    "konkatsu": 2,
    "beauty": 2,
    "yua": 8,
    "h3": 2,
}


@dataclass(frozen=True)
class Profile:
    width: int
    height: int
    fps: int
    duration: float
    duration_min: float
    duration_max: float
    pr: str
    captions: str
    checker: str
    credit: bool
    silence_limit: float | None


PROFILES: dict[str, Profile] = {
    "konkatsu": Profile(1080, 1920, 30, 10.5, 8.0, 10.5, "window", "all", "box", False, None),
    "beauty": Profile(1080, 1920, 30, 10.5, 8.0, 10.5, "open-tail", "all", "box", False, None),
    "pet": Profile(1080, 1920, 24, 10.5, 8.0, 10.5, "tail", "hook", "template", False, None),
    "kane": Profile(1080, 1920, 24, 10.5, 8.0, 10.5, "none", "all", "template", True, None),
    "yua": Profile(2160, 3840, 60, 10.5, 8.0, 10.5, "none", "all", "box", False, None),
    "h3": Profile(1344, 768, 24, 70.0, 60.0, 80.0, "tail", "all", "box", False, None),
    "yorunotana": Profile(1080, 1920, 30, 65.0, 60.0, 70.0, "tail", "all", "internal", False, 2.0),
}


@dataclass(frozen=True)
class Scene:
    start: float
    end: float
    visual: str
    pr_only: bool


@dataclass(frozen=True)
class Speech:
    start: float
    end: float
    text: str
    scene: int


@dataclass(frozen=True)
class RawCap:
    start: float
    end: float
    text: str
    position: str


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str
    position: str
    hook: bool = False
    pr: bool = False


@dataclass(frozen=True)
class ScriptDoc:
    scenes: list[Scene]
    speeches: list[Speech]
    captions: list[RawCap]
    text: str


def adult_marker(text: str) -> str | None:
    for marker in ADULT_MARKERS:
        if marker in text:
            return marker
    return None


def pr_begin_of(profile: Profile) -> float | None:
    if profile.pr == "none":
        return None
    if profile.pr == "window":
        return 8.5
    return profile.duration - 2.0


def speech_limit_of(profile: Profile) -> float:
    begin = pr_begin_of(profile)
    latest = profile.duration - 1.5
    if begin is not None:
        return min(latest, begin)
    return latest


def _section(md: str, token: str) -> str:
    parts = re.split(r"(?m)^#{1,6}\s+", md)
    for part in parts[1:]:
        lines = part.split("\n", 1)
        title = lines[0].strip()
        if token in title:
            return lines[1] if len(lines) > 1 else ""
    return ""


def parse_script(md: str) -> ScriptDoc:
    scenes: list[Scene] = []
    speeches: list[Speech] = []
    row_re = re.compile(
        rf"^\|\s*([0-9]+(?:\.[0-9]+)?)\s*{DASH}\s*([0-9]+(?:\.[0-9]+)?)\s*\|([^|]*)\|([^|]*)\|\s*$"
    )
    speech_re = re.compile(
        rf"\[([0-9]+(?:\.[0-9]+)?)\s*{DASH}\s*([0-9]+(?:\.[0-9]+)?)\]\s*([^／\[\]|]+)"
    )
    for line in md.splitlines():
        matched = row_re.match(line.strip())
        if matched is None:
            continue
        start = float(matched.group(1))
        end = float(matched.group(2))
        visual = matched.group(3).strip()
        spoken = matched.group(4).strip()
        if visual in {"映っているもの", "---"} or "---" in visual:
            continue
        found = speech_re.findall(spoken)
        pr_only = not found and ("声なし" in spoken or "広告" in visual)
        scene_index = len(scenes)
        scenes.append(Scene(start, end, visual, pr_only))
        for raw_start, raw_end, text in found:
            speeches.append(
                Speech(float(raw_start), float(raw_end), text.strip(), scene_index)
            )
    captions = _parse_captions(_section(md, "字幕"))
    return ScriptDoc(scenes, speeches, captions, md)


def _position(bullet: str) -> str:
    if "右上" in bullet or "an9" in bullet:
        return "corner"
    if "上部" in bullet or "an8" in bullet:
        return "top"
    if "下部" in bullet or "an2" in bullet:
        return "bottom"
    return "center"


def _parse_captions(body: str) -> list[RawCap]:
    token_re = re.compile(rf"([0-9]+(?:\.[0-9]+)?)\s*{DASH}\s*([0-9]+(?:\.[0-9]+)?)|「([^」]+)」")
    captions: list[RawCap] = []
    for bullet in body.splitlines():
        if "「" not in bullet:
            continue
        position = _position(bullet)
        start: float | None = None
        end: float | None = None
        for matched in token_re.finditer(bullet):
            if matched.group(1) is not None:
                start = float(matched.group(1))
                end = float(matched.group(2))
                continue
            if start is None or end is None:
                continue
            captions.append(RawCap(start, end, matched.group(3).strip(), position))
    return captions


def is_pr_text(text: str) -> bool:
    visible = re.sub(r"\{[^}]*\}", "", text).strip()
    if "#PR" in text:
        return True
    return visible == "PR" or visible.startswith("PR｜") or visible.startswith("PR|")


def variants_of(text: str) -> list[str]:
    found: list[str] = []

    def add(item: str) -> None:
        cleaned = re.sub(r"\s+", "", item).strip("、")
        if not cleaned:
            return
        if cleaned[-1] not in "。？！":
            cleaned += "。"
        if cleaned not in found:
            found.append(cleaned)

    add(text)
    for prefix in PREFIXES:
        if text.startswith(prefix):
            add(text[len(prefix) :])
    for soft in SOFT_WORDS:
        if soft in text:
            add(text.replace(soft, "", 1))
    parts = [part.strip() for part in text.rstrip("。？！").split("、") if part.strip()]
    if len(parts) >= 2:
        add(parts[0])
        add(parts[-1])
        add("".join(parts))
        second = parts[-1]
        for soft in SOFT_WORDS:
            second = second.replace(soft, "")
        add(parts[0] + second.replace("写真", ""))
    return found


def choose_takes(
    options: list[list[tuple[str, float]]],
    limit: float,
) -> tuple[list[tuple[str, float]], float, float] | None:
    """各行は原文を先に置く。入らないときだけ、より短い候補へ替える。"""
    chosen = [line[0] for line in options]
    guard = 0
    while guard < 40:
        guard += 1
        placed = _fit_gap(chosen, limit)
        if placed is not None:
            return placed
        longest = max(range(len(chosen)), key=lambda index: chosen[index][1])
        text, duration = chosen[longest]
        original = options[longest][0][0]
        head = original.rstrip("。？！")
        for prefix in PREFIXES:
            if head.startswith(prefix):
                head = head[len(prefix) :]
                break
        head = head.split("、")[0]
        shorter = [
            item
            for item in options[longest]
            if item[0] != text and item[1] <= duration - 0.05
        ]
        if not shorter:
            return None
        shorter.sort(key=lambda item: (head in item[0], item[1]), reverse=True)
        chosen[longest] = shorter[0]
    return None


def _fit_gap(
    chosen: list[tuple[str, float]],
    limit: float,
) -> tuple[list[tuple[str, float]], float, float] | None:
    speech = sum(item[1] for item in chosen)
    gaps = max(0, len(chosen) - 1)
    for gap, start in ((0.40, 0.25), (0.30, 0.20), (0.20, 0.15), (0.15, 0.12)):
        end = start + speech + gap * gaps
        if end <= limit + 1e-6:
            return chosen, start, gap
    return None


def place_takes(
    chosen: list[tuple[str, float]],
    start: float,
    gap: float,
) -> list[tuple[str, float, float]]:
    clock = start
    placed: list[tuple[str, float, float]] = []
    for text, duration in chosen:
        placed.append((text, clock, clock + duration))
        clock += duration + gap
    return placed


def map_time(second: float, source: list[float], dest: list[float]) -> float:
    if second <= source[0]:
        return dest[0]
    for index in range(len(source) - 1):
        left, right = source[index], source[index + 1]
        if second <= right or index == len(source) - 2:
            span = right - left
            ratio = 0.0 if span <= 0 else (second - left) / span
            ratio = min(1.0, max(0.0, ratio))
            return dest[index] + ratio * (dest[index + 1] - dest[index])
    return dest[-1]


def build_cues(
    doc: ScriptDoc,
    placed: list[tuple[str, float, float]],
    profile: Profile,
) -> list[Cue]:
    content = [scene for scene in doc.scenes if not scene.pr_only]
    if not content:
        content = doc.scenes
    source = [scene.start for scene in content]
    content_end = content[-1].end
    if doc.scenes and doc.scenes[-1].pr_only:
        content_end = doc.scenes[-1].start
    source.append(content_end)
    dest = [0.0]
    for scene_index in range(1, len(content)):
        starts = [
            span[1]
            for speech, span in zip(doc.speeches, placed)
            if speech.scene == scene_index
        ]
        dest.append(starts[0] if starts else dest[-1])
    begin = pr_begin_of(profile)
    dest.append(profile.duration if begin is None else begin)
    cues: list[Cue] = []
    for raw in doc.captions:
        if is_pr_text(raw.text) or raw.position == "corner":
            continue
        if raw.start >= content_end:
            continue
        start = map_time(raw.start, source, dest)
        end = map_time(min(raw.end, content_end), source, dest)
        if begin is not None:
            if start >= begin:
                continue
            end = min(end, begin)
        if end - start < 0.05:
            continue
        cues.append(Cue(start, end, raw.text, raw.position))
    cues = _mark_hook(cues)
    return _add_pr(cues, profile)


def _mark_hook(cues: list[Cue]) -> list[Cue]:
    tops = [cue for cue in cues if cue.position == "top"]
    if not tops:
        return cues
    first = min(tops, key=lambda cue: (cue.start, cue.end))
    if first.start > 0.05:
        return cues
    hook_end = min(first.end, 1.0)
    replacement = [
        Cue(0.0, hook_end, "{\\an8}" + first.text, "top", hook=True),
    ]
    if first.end > hook_end + 0.05:
        replacement.append(Cue(hook_end, first.end, first.text, "top"))
    index = cues.index(first)
    return cues[:index] + replacement + cues[index + 1 :]


def _add_pr(cues: list[Cue], profile: Profile) -> list[Cue]:
    kept = [cue for cue in cues if not cue.pr and not is_pr_text(cue.text)]
    if profile.pr == "none":
        return kept
    if profile.pr == "window":
        kept.append(Cue(8.5, 10.5, "広告 #PR", "center", pr=True))
        return kept
    if profile.pr == "tail":
        begin = profile.duration - 2.0
        kept.append(Cue(begin, profile.duration, "広告 #PR", "center", pr=True))
        return kept
    if profile.pr == "open-tail":
        kept.append(Cue(0.0, profile.duration, "{\\an9}PR", "corner", pr=True))
        begin = profile.duration - 2.0
        kept.append(Cue(begin, profile.duration, "広告 #PR", "center", pr=True))
        return kept
    raise AssertionError(profile.pr)


def cues_for_burn(cues: list[Cue], profile: Profile) -> list[Cue]:
    if profile.captions == "hook":
        return [cue for cue in cues if cue.hook or cue.pr]
    return cues


def render_srt(cues: list[Cue]) -> str:
    blocks: list[str] = []
    ordered = sorted(cues, key=lambda cue: (cue.start, cue.end, cue.text))
    for index, cue in enumerate(ordered, start=1):
        blocks.append(
            f"{index}\n{_srt_time(cue.start)} --> {_srt_time(cue.end)}\n{cue.text}\n"
        )
    return "\n".join(blocks) + ("\n" if blocks else "")


def _srt_time(seconds: float) -> str:
    total = int(round(seconds * 1000))
    hours, total = divmod(total, 3_600_000)
    minutes, total = divmod(total, 60_000)
    secs, millis = divmod(total, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def pr_problem(cues: list[Cue], profile: Profile) -> str | None:
    marked = [cue for cue in cues if cue.pr or is_pr_text(cue.text)]
    if profile.pr == "none":
        return "PRがある" if marked else None
    if profile.pr == "window":
        if len(marked) != 1:
            return f"PRが{len(marked)}本"
        cue = marked[0]
        if abs(cue.start - 8.5) > 0.001 or abs(cue.end - 10.5) > 0.001:
            return "PRの秒が8.5〜10.5ではない"
        if "#PR" not in cue.text:
            return "#PRが無い"
        early = [item for item in marked if item.start < 8.5]
        if early:
            return "8.5秒より前にPRがある"
    return None


def default_out(script: Path, line: str) -> Path:
    matched = re.match(r"(\d{4}-\d{2}-\d{2})-([^-]+)-", script.stem)
    if matched:
        folder = f"{matched.group(1)}_{matched.group(2)}"
    else:
        folder = f"undated_{line}"
    return ROOT / "output" / "00_確認待ち" / folder / f"{script.stem}.mp4"


def default_srt(script: Path) -> Path:
    if script.parent.name == "scripts":
        return script.parent.parent / "subs" / f"{script.stem}.srt"
    return script.with_suffix(".srt")


def find_srt(script: Path, explicit: Path | None) -> Path | None:
    """添付や台本と同じフォルダの srt だけを既存とみなす。subs/ は自分で書く場所。"""
    if explicit is not None and explicit.is_file():
        return explicit
    sibling = script.with_suffix(".srt")
    if sibling.is_file():
        return sibling
    return None


class Canvas:
    def __init__(self, width: int, height: int, color: tuple[int, int, int]) -> None:
        self.width = width
        self.height = height
        self.buf = bytearray(bytes(color) * (width * height))

    def rect(self, x: int, y: int, width: int, height: int, color: tuple[int, int, int]) -> None:
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + width)
        y1 = min(self.height, y + height)
        if x1 <= x0 or y1 <= y0:
            return
        pixel = bytes(color)
        span = pixel * (x1 - x0)
        for row in range(y0, y1):
            start = (row * self.width + x0) * 3
            self.buf[start : start + len(span)] = span

    def save(self, path: Path) -> None:
        header = f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
        path.write_bytes(header + bytes(self.buf))


def _park(canvas: Canvas) -> None:
    width, height = canvas.width, canvas.height
    canvas.rect(0, 0, width, int(height * 0.46), (118, 188, 226))
    canvas.rect(0, int(height * 0.46), width, height, (78, 164, 74))
    canvas.rect(int(width * 0.12), int(height * 0.22), int(width * 0.16), int(height * 0.28), (42, 130, 58))
    canvas.rect(int(width * 0.18), int(height * 0.34), int(width * 0.04), int(height * 0.16), (122, 78, 46))
    canvas.rect(int(width * 0.62), int(height * 0.18), int(width * 0.18), int(height * 0.26), (36, 124, 64))
    canvas.rect(int(width * 0.68), int(height * 0.30), int(width * 0.045), int(height * 0.18), (110, 72, 42))
    seat_y = int(height * 0.62)
    canvas.rect(int(width * 0.18), seat_y, int(width * 0.64), int(height * 0.025), (148, 96, 52))
    canvas.rect(int(width * 0.22), seat_y, int(width * 0.03), int(height * 0.08), (128, 82, 44))
    canvas.rect(int(width * 0.74), seat_y, int(width * 0.03), int(height * 0.08), (128, 82, 44))


def paint_scene(kind: str, path: Path, width: int, height: int) -> None:
    canvas = Canvas(width, height, (118, 188, 226))
    _park(canvas)
    if kind == "park-tripod":
        _paint_tripod(canvas)
    elif kind == "photographer":
        _paint_photographer(canvas)
    elif kind == "monitor":
        _paint_monitor(canvas)
    else:
        raise AssertionError(kind)
    canvas.save(path)


def _paint_tripod(canvas: Canvas) -> None:
    width, height = canvas.width, canvas.height
    cx = int(width * 0.50)
    top = int(height * 0.50)
    foot = int(height * 0.62)
    for shift in (-70, 0, 70):
        canvas.rect(cx + shift // 3, top, 18, foot - top, (28, 28, 32))
    canvas.rect(cx - 46, top - 10, 110, 18, (28, 28, 32))
    canvas.rect(cx - 36, top - 150, 72, 140, (22, 22, 26))
    canvas.rect(cx - 26, top - 136, 52, 96, (86, 168, 78))


def _paint_photographer(canvas: Canvas) -> None:
    width, height = canvas.width, canvas.height
    canvas.rect(int(width * 0.18), int(height * 0.58), int(width * 0.64), int(height * 0.22), (24, 24, 28))
    canvas.rect(int(width * 0.22), int(height * 0.52), int(width * 0.22), int(height * 0.10), (214, 170, 142))
    canvas.rect(int(width * 0.56), int(height * 0.52), int(width * 0.22), int(height * 0.10), (214, 170, 142))
    person_x = int(width * 0.62)
    person_y = int(height * 0.34)
    canvas.rect(person_x, person_y, int(width * 0.08), int(height * 0.045), (92, 62, 40))
    canvas.rect(person_x - 8, person_y + int(height * 0.04), int(width * 0.10), int(height * 0.09), (236, 224, 196))
    canvas.rect(person_x - 10, person_y + int(height * 0.12), int(width * 0.11), int(height * 0.10), (196, 176, 148))


def _paint_monitor(canvas: Canvas) -> None:
    width, height = canvas.width, canvas.height
    canvas.rect(0, 0, width, height, (64, 120, 70))
    canvas.rect(int(width * 0.12), int(height * 0.28), int(width * 0.76), int(height * 0.48), (18, 18, 20))
    screen_x = int(width * 0.20)
    screen_y = int(height * 0.34)
    screen_w = int(width * 0.60)
    screen_h = int(height * 0.34)
    canvas.rect(screen_x, screen_y, screen_w, screen_h, (232, 236, 214))
    canvas.rect(screen_x, screen_y, screen_w, int(screen_h * 0.55), (120, 176, 96))
    canvas.rect(
        screen_x + int(screen_w * 0.42),
        screen_y + int(screen_h * 0.28),
        int(screen_w * 0.16),
        int(screen_h * 0.42),
        (236, 224, 196),
    )


def infer_paint(visual: str, index: int) -> str:
    if any(word in visual for word in ("モニター", "背面")):
        return "monitor"
    if any(word in visual for word in ("カメラマン", "両手", "ミラーレス")):
        return "photographer"
    if any(word in visual for word in ("三脚", "ベンチ", "芝生", "公園")):
        return "park-tripod"
    return ("park-tripod", "photographer", "monitor")[index % 3]


def voicevox_up(base: str) -> bool:
    try:
        with urllib.request.urlopen(base + "/version", timeout=0.6) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def voicevox_speaker_ids(base: str) -> set[int]:
    with urllib.request.urlopen(base + "/speakers", timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    found: set[int] = set()
    for person in payload:
        for style in person.get("styles", []):
            found.add(int(style["id"]))
    return found


def synthesize_voicevox(text: str, speaker: int, dest: Path, base: str) -> None:
    query_url = base + "/audio_query?" + urllib.parse.urlencode({"text": text, "speaker": speaker})
    request = urllib.request.Request(query_url, data=b"", method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        query = response.read()
    synth_url = base + "/synthesis?" + urllib.parse.urlencode({"speaker": speaker})
    synth = urllib.request.Request(
        synth_url,
        data=query,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(synth, timeout=120) as response:
        dest.write_bytes(response.read())


async def _edge_save(text: str, voice: str, dest: Path) -> None:
    await edge_tts.Communicate(text, voice).save(str(dest))


def synthesize_edge(text: str, voice: str, dest: Path) -> None:
    asyncio.run(_edge_save(text, voice, dest))


def decode_mono(path: Path) -> list[int]:
    raw = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(RATE),
            "-f",
            "s16le",
            "-",
        ]
    )
    count = len(raw) // 2
    return list(struct.unpack("<" + "h" * count, raw[: count * 2]))


def trim_ends(samples: list[int], threshold: int = 900) -> list[int]:
    if not samples:
        return samples
    first = 0
    last = len(samples) - 1
    while first < last and abs(samples[first]) < threshold:
        first += 1
    while last > first and abs(samples[last]) < threshold:
        last -= 1
    pad = int(0.03 * RATE)
    start = max(0, first - pad)
    end = min(len(samples), last + 1 + pad)
    return samples[start:end]


def fade_edges(samples: list[int]) -> None:
    span = min(len(samples) // 4, int(0.015 * RATE))
    for index in range(span):
        gain = index / span
        samples[index] = int(samples[index] * gain)
        samples[-1 - index] = int(samples[-1 - index] * gain)


def write_wav(path: Path, samples: list[int]) -> None:
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        frames = bytearray()
        for sample in samples:
            frames += struct.pack("<h", max(-32767, min(32767, sample)))
        handle.writeframes(frames)


def mix_bed(
    spans: list[tuple[list[int], float]],
    seconds: float,
    ratio: float,
) -> list[int]:
    count = int(round(seconds * RATE))
    voice = [0] * count
    voiced: list[int] = []
    for samples, start in spans:
        offset = int(round(start * RATE))
        for index, sample in enumerate(samples):
            at = offset + index
            if 0 <= at < count:
                voice[at] = sample
                voiced.append(sample)
    if not voiced:
        raise RuntimeError("声が空")
    voice_rms = math.sqrt(sum(sample * sample for sample in voiced) / len(voiced))
    bed_amp = voice_rms * ratio / math.sqrt(1.0 + 0.6 * 0.6)
    mixed: list[int] = []
    for index in range(count):
        second = index / RATE
        bed = math.sin(2 * math.pi * 110 * second) * bed_amp
        bed += math.sin(2 * math.pi * 164.81 * second) * bed_amp * 0.6
        if second > seconds - 0.25:
            bed *= max(0.0, (seconds - second) / 0.25)
        mixed.append(int(voice[index] + bed))
    return mixed


def loudnorm_two_pass(src: Path, dest: Path, integrated: float, true_peak: float) -> None:
    probe = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(src),
            "-af",
            f"loudnorm=I={integrated}:TP={true_peak}:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    blob = probe.stderr
    measured = json.loads(blob[blob.rfind("{") : blob.rfind("}") + 1])
    audio_filter = (
        f"loudnorm=I={integrated}:TP={true_peak}:LRA=11:"
        f"measured_I={measured['input_i']}:"
        f"measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:"
        f"measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:linear=true"
    )
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-af",
            audio_filter,
            "-ar",
            str(RATE),
            "-ac",
            "1",
            str(dest),
        ]
    )


def measure_loudness(path: Path) -> tuple[float | None, float | None]:
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    text = probe.stderr
    integrated_vals = re.findall(r"I:\s*(-?[0-9.]+)\s*LUFS", text)
    true_peak = None
    if "True peak:" in text:
        tail = text.split("True peak:")[-1]
        matched = re.search(r"Peak:\s*(-?[0-9.]+)\s*dBFS", tail)
        if matched:
            true_peak = float(matched.group(1))
    integrated = float(integrated_vals[-1]) if integrated_vals else None
    return integrated, true_peak


def loudness_ok(integrated: float | None, true_peak: float | None) -> bool:
    if integrated is None or true_peak is None:
        return False
    return abs(integrated - (-14.0)) <= 0.6 and -6.0 <= true_peak <= -1.5


def gain_db(integrated: float | None, true_peak: float | None) -> float:
    gain = 0.0
    if integrated is not None and integrated > -13.4:
        gain = -14.0 - integrated
    if true_peak is not None and true_peak > -1.5:
        gain = min(gain, -1.5 - true_peak - 0.4)
    if integrated is not None and integrated < -14.6 and true_peak is not None and true_peak < -2.3:
        headroom = -1.9 - true_peak
        gain = min(-14.0 - integrated, max(0.0, headroom))
    return gain


def apply_gain(src: Path, dest: Path, gain: float) -> None:
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-af",
            f"volume={gain:.3f}dB",
            "-ar",
            str(RATE),
            "-ac",
            "1",
            str(dest),
        ]
    )


def cut_bounds(doc: ScriptDoc, placed: list[tuple[str, float, float]], profile: Profile) -> list[float]:
    content = [scene for scene in doc.scenes if not scene.pr_only] or doc.scenes
    bounds = [0.0]
    for scene_index in range(1, len(content)):
        starts = [
            span[1]
            for speech, span in zip(doc.speeches, placed)
            if speech.scene == scene_index
        ]
        bounds.append(starts[0] if starts else bounds[-1])
    bounds.append(profile.duration)
    return bounds


def video_filter(
    cuts: list[tuple[Path, float]],
    cues: list[Cue],
    profile: Profile,
    font: str,
    text_dir: Path,
    pr_begin: float | None,
) -> str:
    chains: list[str] = []
    for index, (_image, duration) in enumerate(cuts):
        phase = round(0.6 * index, 3)
        chains.append(
            f"[{index}:v]scale=iw*1.08:ih*1.08,"
            f"crop={profile.width}:{profile.height}:"
            f"x='(in_w-{profile.width})/2+12*sin(t+{phase})':"
            f"y='(in_h-{profile.height})/2+8*sin(t*0.8+{phase})',"
            f"trim=duration={duration:.3f},setpts=PTS-STARTPTS,"
            f"fps={profile.fps},setsar=1,format=yuv420p[v{index}]"
        )
    head = "".join(f"[v{index}]" for index in range(len(cuts)))
    graph = ";".join(chains)
    graph += f";{head}concat=n={len(cuts)}:v=1:a=0,format=rgba[cat]"
    current = "[cat]"
    if pr_begin is not None:
        graph += (
            f";{current}drawbox=x=0:y=0:w=iw:h=ih:color=black@0.28:t=fill:"
            f"enable='gte(t\\,{pr_begin:.3f})'[dim]"
        )
        current = "[dim]"
    draws: list[str] = []
    top_lines: list[str] = []
    for cue in cues:
        if cue.position != "top":
            continue
        visible_top = re.sub(r"\{[^}]*\}", "", cue.text).strip()
        if visible_top not in top_lines:
            top_lines.append(visible_top)
    for cue in cues:
        visible = re.sub(r"\{[^}]*\}", "", cue.text).strip()
        if not visible:
            continue
        slot = text_dir / f"cue{len(draws)}.txt"
        slot.write_text(visible + "\n", encoding="utf-8")
        if cue.pr and cue.position == "center":
            size, x_expr, y_expr = 72, "(w-text_w)/2", "(h-text_h)/2"
        elif cue.position == "top":
            size = 54
            x_expr = "(w-text_w)/2"
            y_expr = str(140 + 96 * top_lines.index(visible))
        elif cue.position == "bottom":
            size, x_expr, y_expr = 52, "(w-text_w)/2", "h*0.80"
        elif cue.position == "corner":
            size, x_expr, y_expr = 42, "w-text_w-48", "72"
        else:
            size, x_expr, y_expr = 60, "(w-text_w)/2", "h*0.46"
        draws.append(
            "drawtext="
            f"fontfile={font}:textfile={filter_path(str(slot))}:expansion=none:"
            f"fontsize={size}:fontcolor=white:borderw=6:bordercolor=black:"
            f"x={x_expr}:y={y_expr}:enable='between(t\\,{cue.start:.3f}\\,{cue.end:.3f})'"
        )
    if profile.credit:
        credit = text_dir / "credit.txt"
        credit.write_text("BGM: 自作\n", encoding="utf-8")
        draws.append(
            "drawtext="
            f"fontfile={font}:textfile={filter_path(str(credit))}:expansion=none:"
            "fontsize=42:fontcolor=white:borderw=5:bordercolor=black:"
            "x=(w-text_w)/2:y=h*0.90"
        )
    if draws:
        graph += f";{current}" + ",".join(draws) + ",format=yuv420p[v]"
    else:
        graph += f";{current}format=yuv420p[v]"
    return graph


def render_picture(
    cuts: list[tuple[Path, float]],
    cues: list[Cue],
    profile: Profile,
    dest: Path,
    work: Path,
) -> None:
    font = filter_path(font_path())
    graph = video_filter(cuts, cues, profile, font, work, pr_begin_of(profile))
    if "atempo" in graph:
        raise RuntimeError("早回しは入れない")
    frames = int(round(profile.duration * profile.fps))
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for image, duration in cuts:
        command += ["-loop", "1", "-t", f"{duration:.3f}", "-i", str(image)]
    command += [
        "-filter_complex",
        graph,
        "-map",
        "[v]",
        "-an",
        "-r",
        str(profile.fps),
        "-fps_mode",
        "cfr",
        "-frames:v",
        str(frames),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    subprocess.check_call(command)


def mux_audio(picture: Path, audio: Path, dest: Path, profile: Profile) -> None:
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(picture),
            "-i",
            str(audio),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-t",
            f"{profile.duration:.3f}",
            "-movflags",
            "+faststart",
            str(dest),
        ]
    )


def run_checker(line: str, profile: Profile, mp4: Path) -> tuple[int, str]:
    if profile.checker == "template":
        command = ["bash", str(ROOT / "tools" / "check_video.sh"), str(mp4), line, "--final"]
    elif profile.checker == "box":
        command = ["bash", str(ROOT / "video" / "shorts" / "check_video.sh"), str(mp4), line]
    else:
        return _internal_check(mp4, profile)
    proc = subprocess.run(command, capture_output=True, text=True)
    text = proc.stdout
    if proc.stderr.strip():
        text += "\n" + proc.stderr
    return proc.returncode, text.rstrip() + "\n"


def _internal_check(mp4: Path, profile: Profile) -> tuple[int, str]:
    duration = float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(mp4),
            ],
            text=True,
        ).strip()
    )
    lines = [f"DUR {'PASS' if profile.duration_min <= duration <= profile.duration_max else 'FAIL'} 長さ={duration:.3f}秒"]
    code = 0 if lines[0].startswith("DUR PASS") else 1
    if profile.silence_limit is not None:
        log = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-i",
                str(mp4),
                "-af",
                f"silencedetect=noise=-45dB:d={profile.silence_limit}",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
        ).stderr
        silent = "silence_start" in log
        lines.append(
            "SIL "
            + ("FAIL 2秒以上の無音" if silent else "PASS 2秒以上の無音なし")
        )
        if silent:
            code = 1
    return code, "\n".join(lines) + "\n"


def prepare_media(
    doc: ScriptDoc,
    jobs: list[dict[str, str]],
    profile: Profile,
    bounds: list[float],
    work: Path,
) -> list[tuple[Path, float]]:
    content = [scene for scene in doc.scenes if not scene.pr_only] or doc.scenes
    cuts: list[tuple[Path, float]] = []
    for index, scene in enumerate(content):
        duration = bounds[index + 1] - bounds[index]
        if duration <= 0.05:
            raise RuntimeError(f"カット{index + 1}の長さが無い")
        clip = jobs[index] if index < len(jobs) else {}
        given = clip.get("path", "").strip()
        dest = work / f"cut{index}.ppm"
        if given:
            source = Path(given)
            if not source.is_file():
                raise RuntimeError(f"素材が無い: {source}")
            dest = source
        else:
            kind = str(clip.get("paint") or infer_paint(scene.visual, index))
            paint_scene(kind, dest, profile.width, profile.height)
        cuts.append((dest, duration))
    return cuts


def synth_take(text: str, line: str, dest: Path, engine: str, speaker: int | None, voice: str) -> None:
    if engine == "voicevox":
        if speaker is None:
            raise RuntimeError("VOICEVOX の話者番号が無い")
        synthesize_voicevox(text, speaker, dest, VOICEVOX_URL)
        return
    synthesize_edge(text, voice, dest)


def build(script_path: Path, line: str, jobs_path: Path | None, srt_path: Path | None, out: Path, handoff: Path) -> int:
    notes: list[str] = []
    profile = PROFILES.get(line)
    if profile is None:
        handoff.write_text(f"ライン名が無い: {line}\n", encoding="utf-8")
        return 2
    md = script_path.read_text(encoding="utf-8")
    marker = adult_marker(md)
    if jobs_path is not None and jobs_path.is_file():
        jobs_text = jobs_path.read_text(encoding="utf-8")
        marker = marker or adult_marker(jobs_text)
    else:
        jobs_text = ""
    if marker is not None:
        handoff.parent.mkdir(parents=True, exist_ok=True)
        handoff.write_text(
            f"止めた。成人向けの語「{marker}」がある。素材は置いていない。投稿していない。\n",
            encoding="utf-8",
        )
        return 2
    doc = parse_script(md)
    if not doc.speeches:
        handoff.write_text("セリフが無いので止めた。投稿していない。\n", encoding="utf-8")
        return 1
    found_srt = find_srt(script_path, srt_path)
    jobs: list[dict[str, str]] = []
    if jobs_text:
        payload = json.loads(jobs_text)
        jobs = list(payload.get("clips", []))
    if not any(str(clip.get("path", "")).strip() for clip in jobs):
        notes.append(
            "Krea と Drive の画像は添付に無かった。jobs.json の path が空なので、"
            "顔の無い平面の絵を枠いっぱいに使った。切り抜き合成はしていない。有料プランには上げていない。"
        )
    engine, speaker, voice, engine_note = _pick_engine(line)
    notes.append(engine_note)
    work = out.parent / f".work-{script_path.stem}"
    if work.exists():
        for child in work.iterdir():
            if child.is_file():
                child.unlink()
    work.mkdir(parents=True, exist_ok=True)
    options: list[list[tuple[str, float]]] = []
    cache: dict[str, list[int]] = {}
    for speech in doc.speeches:
        line_options: list[tuple[str, float]] = []
        for text in variants_of(speech.text):
            if text not in cache:
                media = work / f"voice-{len(cache)}.wav"
                synth_take(text, line, media, engine, speaker, voice)
                samples = trim_ends(decode_mono(media))
                fade_edges(samples)
                cache[text] = samples
            line_options.append((text, len(cache[text]) / RATE))
        options.append(line_options)
    limit = speech_limit_of(profile)
    picked = choose_takes(options, limit)
    if picked is None:
        _write_handoff(handoff, notes + ["等倍のまま言葉を削っても、声が尺に入らなかった。投稿していない。"], "", None, None, 1)
        return 1
    chosen, start, gap = picked
    placed = place_takes(chosen, start, gap)
    spoken_note = "、".join(f"「{text}」{span_end - span_start:.2f}秒" for text, span_start, span_end in [
        (item[0], item[1], item[2]) for item in placed
    ])
    originals = [speech.text for speech in doc.speeches]
    if [item[0] for item in chosen] != originals:
        notes.append(
            f"原文のままだと等倍で {limit:.1f} 秒までに終わらない。早回しはせず、言葉を削った。"
            f"採用した読み: {spoken_note}。間は {gap:.2f} 秒。"
        )
    else:
        notes.append(f"読みは原文のまま。間は {gap:.2f} 秒。{spoken_note}")
    cues = build_cues(doc, placed, profile)
    problem = pr_problem(cues, profile)
    if problem:
        _write_handoff(handoff, notes + [f"字幕のPRが規格外: {problem}"], "", None, None, 1)
        return 1
    burn = cues_for_burn(cues, profile)
    srt_dest = default_srt(script_path)
    srt_dest.parent.mkdir(parents=True, exist_ok=True)
    srt_dest.write_text(render_srt(burn), encoding="utf-8")
    if found_srt is None:
        notes.append(
            "台本が指す subs/*.srt は添付に無かった。字幕の節から作り、"
            f"映像に焼いたものと同じ内容を {srt_dest.relative_to(ROOT)} に書いた。"
            "PR は 8.5〜10.5 秒だけ。"
        )
    else:
        notes.append(f"隣の SRT は残した: {found_srt.relative_to(ROOT)}。映像用は尺に合わせて書き直した。")
    spans = [(cache[text], span_start) for text, span_start, _span_end in placed]
    mixed = mix_bed(spans, profile.duration, BGM_RATIO)
    voice_wav = work / "mix.wav"
    norm_wav = work / "norm.wav"
    write_wav(voice_wav, mixed)
    loudnorm_two_pass(voice_wav, norm_wav, -14.0, -2.6)
    bounds = cut_bounds(doc, placed, profile)
    cuts = prepare_media(doc, jobs, profile, bounds, work)
    picture = work / "picture.mp4"
    render_picture(cuts, burn, profile, picture, work)
    out.parent.mkdir(parents=True, exist_ok=True)
    mux_audio(picture, norm_wav, out, profile)
    integrated, true_peak = measure_loudness(out)
    audio_now = norm_wav
    fixes = 0
    code, checker_text = run_checker(line, profile, out)
    while fixes < 3 and (code != 0 or not loudness_ok(integrated, true_peak)):
        if loudness_ok(integrated, true_peak) or integrated is None:
            break
        gain = gain_db(integrated, true_peak)
        if abs(gain) < 0.05:
            break
        fixes += 1
        nxt = work / f"norm-{fixes}.wav"
        apply_gain(audio_now, nxt, gain)
        audio_now = nxt
        mux_audio(picture, audio_now, out, profile)
        integrated, true_peak = measure_loudness(out)
        code, checker_text = run_checker(line, profile, out)
    notes.append(f"音量のやり直し: {fixes} 回（上限 3）。BGM は自作の正弦波で、声の実効値の約15%。")
    notes.append("投稿・公開はしていない。A8 の URL は置いていない。")
    _write_handoff(handoff, notes, checker_text, integrated, true_peak, code)
    return code


def _pick_engine(line: str) -> tuple[str, int | None, str, str]:
    speaker = VOICEVOX_SPEAKER.get(line, 2)
    voice = EDGE_VOICE.get(line, "ja-JP-NanamiNeural")
    if voicevox_up(VOICEVOX_URL):
        try:
            ids = voicevox_speaker_ids(VOICEVOX_URL)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            ids = set()
        if speaker in ids:
            return "voicevox", speaker, voice, f"声は VOICEVOX 話者{speaker}。等倍。edge-tts は使っていない。"
        return (
            "edge-tts",
            None,
            voice,
            f"VOICEVOX は起動していたが話者{speaker}が無い。予備の edge-tts（{voice}、等倍）にした。",
        )
    return (
        "edge-tts",
        None,
        voice,
        f"VOICEVOX の CPU エンジンは 127.0.0.1:50021 に無い。予備の edge-tts（{voice}、等倍）にした。有料の声は使っていない。",
    )


def _write_handoff(
    path: Path,
    notes: list[str],
    checker_text: str,
    integrated: float | None,
    true_peak: float | None,
    code: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    loud = "測れていない"
    if integrated is not None and true_peak is not None:
        loud = f"I={integrated:.2f} LUFS / TP={true_peak:.2f} dBFS"
    body = [
        "# 短尺の1本目",
        "",
        "投稿していない。テンプレの `video/HANDOFF.md` と `tools/check_video.sh` は書き換えていない。",
        "",
        "## メモ",
        "",
    ]
    body.extend(f"- {note}" for note in notes)
    body.extend(
        [
            "",
            "## 音量",
            "",
            loud,
            "",
            "## check_video.sh",
            "",
            "```",
            checker_text.rstrip(),
            "```",
            "",
            f"exit={code}",
            "",
        ]
    )
    path.write_text("\n".join(body), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="台本から短い縦動画を作る。投稿はしない。")
    parser.add_argument("script", type=Path)
    parser.add_argument("line", choices=sorted(PROFILES))
    parser.add_argument("--jobs", type=Path)
    parser.add_argument("--srt", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--handoff", type=Path, default=ROOT / "video" / "shorts" / "HANDOFF.md")
    parser.add_argument("--final", action="store_true", help="完成の尺（既定でこの規格）")
    args = parser.parse_args(argv)
    script = args.script if args.script.is_absolute() else ROOT / args.script
    if not script.is_file():
        print(f"台本が無い: {args.script}", file=sys.stderr)
        return 2
    jobs = None
    if args.jobs is not None:
        jobs = args.jobs if args.jobs.is_absolute() else ROOT / args.jobs
    out = args.out or default_out(script, args.line)
    if not out.is_absolute():
        out = ROOT / out
    try:
        return build(script, args.line, jobs, args.srt, out, args.handoff)
    except (subprocess.CalledProcessError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        args.handoff.parent.mkdir(parents=True, exist_ok=True)
        args.handoff.write_text(
            "組み立てに失敗した。投稿していない。\n\n" + str(exc) + "\n",
            encoding="utf-8",
        )
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
