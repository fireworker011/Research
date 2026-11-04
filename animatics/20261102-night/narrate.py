#!/usr/bin/env python3
"""字幕の台詞を女性の話し言葉で読み、その秒に合わせて m4a を作る。

フック（{\\an8}）と広告（#PR）は読まない。
声は ja-JP-NanamiNeural。読みの速さは +15%まで。早回しはしない。
行末の無音だけを切る。枠より長いときは失敗させる。
"""

from __future__ import annotations

import asyncio
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import edge_tts

VOICE = "ja-JP-NanamiNeural"
RATE = "+15%"
SAMPLE_RATE = 48000


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        text=True,
    )
    return float(out.strip())


def parse_spoken(srt: str) -> list[tuple[float, float, str]]:
    blocks = re.split(r"\n(?:[ \t]*\n)+", srt.replace("\r\n", "\n").strip())
    cues: list[tuple[float, float, str]] = []
    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        body = "\n".join(lines[2:])
        if any(mark in body for mark in ("{\\an8}", "{\\an9}", "#PR", "広告")):
            continue
        visible = re.sub(r"\{[^}]*\}", "", body).strip()
        if not visible:
            continue
        start_s, end_s = lines[1].split(" --> ")
        cues.append((to_seconds(start_s), to_seconds(end_s), visible))
    return cues


def to_seconds(stamp: str) -> float:
    hh, mm, rest = stamp.split(":")
    ss, ms = rest.split(",")
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000


async def synthesize(text: str, dest: Path) -> None:
    await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(dest))


def fit_clip(src: Path, dest: Path, slot: float) -> float:
    trimmed = dest.with_suffix(".trim.wav")
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-af",
            "silenceremove=start_periods=1:start_threshold=-35dB:start_silence=0.02,"
            "areverse,silenceremove=start_periods=1:start_threshold=-35dB:start_silence=0.02,areverse",
            "-c:a",
            "pcm_s16le",
            str(trimmed),
        ]
    )
    spoken = probe_duration(trimmed)
    if spoken > slot + 0.02:
        raise SystemExit(f"枠 {slot:.3f} 秒に対して読みが {spoken:.3f} 秒: 早回しはしない")
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(trimmed),
            "-filter:a",
            f"apad=whole_dur={slot:.3f},aresample={SAMPLE_RATE},aformat=channel_layouts=mono",
            "-t",
            f"{slot:.3f}",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )
    return spoken


def silence(dest: Path, seconds: float) -> None:
    if seconds <= 0.001:
        return
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r={SAMPLE_RATE}:cl=mono",
            "-t",
            f"{seconds:.3f}",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )


async def build(srt_path: Path, m4a_path: Path, duration: float) -> None:
    cues = parse_spoken(srt_path.read_text(encoding="utf-8"))
    if not cues:
        raise SystemExit(f"読む行が無い: {srt_path}")
    with tempfile.TemporaryDirectory(prefix="narrate-") as tmp:
        work = Path(tmp)
        pieces: list[Path] = []
        cursor = 0.0
        for index, (start, end, text) in enumerate(cues):
            slot = end - start
            if slot <= 0:
                raise SystemExit(f"枠が無い: {text}")
            if start < cursor - 0.001:
                raise SystemExit(f"字幕が重なる: {text}")
            if start > cursor + 0.001:
                gap = work / f"gap{index}.wav"
                silence(gap, start - cursor)
                pieces.append(gap)
            raw = work / f"raw{index}.mp3"
            fitted = work / f"fit{index}.wav"
            await synthesize(text, raw)
            spoken = fit_clip(raw, fitted, slot)
            print(f"  {start:.3f}-{end:.3f} +15% {spoken:.2f}秒 {text}")
            pieces.append(fitted)
            cursor = end
        if duration > cursor + 0.001:
            tail = work / "tail.wav"
            silence(tail, duration - cursor)
            pieces.append(tail)
        listing = work / "list.txt"
        listing.write_text(
            "".join(f"file '{piece}'\n" for piece in pieces), encoding="utf-8"
        )
        wav = work / "all.wav"
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(listing),
                "-c:a",
                "pcm_s16le",
                str(wav),
            ]
        )
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(wav),
                "-t",
                f"{duration:.3f}",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-ar",
                str(SAMPLE_RATE),
                str(m4a_path),
            ]
        )
    got = probe_duration(m4a_path)
    if abs(got - duration) > 0.08:
        raise SystemExit(f"音声の長さが {got:.3f} 秒（指定 {duration:.3f}）")


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: narrate.py SRT M4A DURATION")
    srt_path, m4a_path, duration_s = sys.argv[1:]
    asyncio.run(build(Path(srt_path), Path(m4a_path), float(duration_s)))


if __name__ == "__main__":
    main()
