"""build-yorunotana.ps1 と同じ ffprobe 検査を Python で行う。

合格は 1080x1920、60fps、60.0〜70.0秒、音声あり、
2.0秒以上のフリーズなし、2.0秒以上の無音なし。
尺が足りないときは測った長さのまま FAIL する。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def probe(path: Path) -> dict:
    raw = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", str(path),
        ]
    )
    return json.loads(raw)


def fps_of(stream: dict) -> float:
    rate = str(stream.get("r_frame_rate") or "0/1")
    num, den = rate.split("/")
    den_f = float(den)
    if den_f == 0:
        return 0.0
    return float(num) / den_f


def _spans(log: str, kind: str, total: float) -> list[float]:
    number = r"([0-9]+(?:\.[0-9]+)?)"
    starts = [float(value) for value in re.findall(rf"{kind}_start:\s*{number}", log)]
    ends = [float(value) for value in re.findall(rf"{kind}_end:\s*{number}", log)]
    durations = [float(value) for value in re.findall(rf"{kind}_duration:\s*{number}", log)]
    if durations and len(durations) >= len(starts):
        return durations
    spans: list[float] = []
    for index, start in enumerate(starts):
        if index < len(ends):
            spans.append(ends[index] - start)
        elif index < len(durations):
            spans.append(durations[index])
        else:
            spans.append(max(0.0, total - start))
    return spans or durations


def detect_freeze_and_silence(video: Path) -> tuple[list[float], list[float], str]:
    """freezedetect n=-60dB d=2 と silencedetect n=-50dB d=2。秒のリストを返す。"""
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats",
            "-i", str(video),
            "-vf", "freezedetect=n=-60dB:d=2",
            "-af", "silencedetect=n=-50dB:d=2",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
    )
    log = (result.stderr or "") + "\n" + (result.stdout or "")
    if result.returncode != 0 and "freeze_start" not in log and "silence_start" not in log:
        raise SystemExit(f"ffmpeg のフリーズ/無音検出が失敗しました:\n{log[-1500:]}")
    total = 0.0
    info = probe(video)
    total = float((info.get("format") or {}).get("duration") or 0.0)
    freezes = _spans(log, "freeze", total)
    silences = _spans(log, "silence", total)
    return freezes, silences, log


def cuts(timing_path: Path | None) -> list[str]:
    if timing_path is None or not timing_path.exists():
        return ["- （audio_timing.json なし）"]
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    lines = []
    for item in timing.get("items") or []:
        length = float(item["end_sec"]) - float(item["start_sec"])
        label = str(item.get("kind"))
        if item.get("segment_id") is not None:
            label += f" #{item['segment_id']} {item.get('scene') or ''}"
        lines.append(
            f"- {label}: {length:.2f}s ({float(item['start_sec']):.2f}-{float(item['end_sec']):.2f})"
        )
    return lines or ["- （カットなし）"]


def main() -> int:
    parser = argparse.ArgumentParser(description="MP4の尺・解像度・音声を検査する")
    parser.add_argument("--video", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--timing")
    parser.add_argument("--write", action="store_true", help="REPORT.md と LAST_RESULT.txt を書く")
    parser.add_argument("--report-dir", default=".")
    args = parser.parse_args()
    video = Path(args.video)
    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    job_id = str(job.get("job_id") or "unknown")
    pr_text = "True" if job.get("pr_badge") else "False"
    reasons: list[str] = []
    width = height = 0
    duration = 0.0
    fps = 0.0
    has_audio = False
    freezes: list[float] = []
    silences: list[float] = []
    freeze_max = 0.0
    silence_max = 0.0
    if not video.exists():
        reasons.append("MP4が存在しない")
    else:
        info = probe(video)
        visual = next((stream for stream in info.get("streams") or [] if stream.get("codec_type") == "video"), None)
        audio = next((stream for stream in info.get("streams") or [] if stream.get("codec_type") == "audio"), None)
        if visual is None:
            reasons.append("映像ストリームがない")
        else:
            width = int(visual.get("width") or 0)
            height = int(visual.get("height") or 0)
            fps = fps_of(visual)
        duration = float((info.get("format") or {}).get("duration") or 0.0)
        has_audio = audio is not None
        if not (width == 1080 and height == 1920):
            reasons.append(f"解像度が {width}x{height}")
        if abs(fps - 60.0) >= 0.05:
            reasons.append(f"フレームレートが {fps:.3f}")
        if not (60.0 <= duration <= 70.0):
            reasons.append(f"尺が {duration:.3f}秒")
        if not has_audio:
            reasons.append("音声ストリームがない")
        freezes, silences, _log = detect_freeze_and_silence(video)
        freeze_max = max(freezes) if freezes else 0.0
        silence_max = max(silences) if silences else 0.0
        if freeze_max >= 2.0:
            reasons.append(f"フリーズが {freeze_max:.2f}秒")
        if silence_max >= 2.0:
            reasons.append(f"無音が {silence_max:.2f}秒")
    status = "PASS" if not reasons else "FAIL"
    line = (
        f"{status} | {job_id}.mp4 | {duration:.1f}s | PR:{pr_text}"
        f" | freeze={freeze_max:.2f}s | silence={silence_max:.2f}s"
    )
    mark = lambda ok: "OK" if ok else "NG"
    report = "\n".join(
        [
            "# yorunotana 検証レポート",
            "",
            f"- ジョブファイル: {args.job}",
            f"- job_id: {job_id}",
            f"- 出力: {video}",
            f"- 解像度: {width}x{height} （基準 1080x1920） {mark(width == 1080 and height == 1920)}",
            f"- フレームレート: {fps:.3f} （基準 60） {mark(abs(fps - 60.0) < 0.05)}",
            f"- 尺: {duration:.3f}秒 （基準 60.0〜70.0。2026-11-09 21:25 の決定） {mark(60.0 <= duration <= 70.0)}",
            f"- 音声ストリーム: {'あり' if has_audio else 'なし'} {mark(has_audio)}",
            f"- 最長フリーズ: {freeze_max:.2f}秒 （基準 2.0秒未満、noise=-60dB d=2） {mark(freeze_max < 2.0)}",
            f"- 検出したフリーズ: {', '.join(f'{value:.2f}s' for value in freezes) if freezes else 'なし'}",
            f"- 最長無音: {silence_max:.2f}秒 （基準 2.0秒未満、noise=-50dB d=2） {mark(silence_max < 2.0)}",
            f"- 検出した無音: {', '.join(f'{value:.2f}s' for value in silences) if silences else 'なし'}",
            f"- PRバッジ（ジョブ指定）: {pr_text}",
            f"- 総合: {status}",
            "",
            "## 各カット",
            *cuts(Path(args.timing) if args.timing else None),
            "",
            "## A8提出前チェック",
            "- 画面は 1080x1920 の縦動画",
            "- 尺は 60.0秒以上 70.0秒以下",
            "- 音声トラックがある",
            "- pr_badge が true のジョブは、右上に PR を全編出す（描画側の責務）",
            "- アフィリエイトのURLは、リポジトリにも完成動画の中にも置かない",
            "",
            "## メモ",
            *([f"- {reason}" for reason in reasons] if reasons else ["- なし"]),
            "",
        ]
    )
    print(line)
    if args.write:
        dest = Path(args.report_dir)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "LAST_RESULT.txt").write_text(line + "\n", encoding="utf-8")
        (dest / "REPORT.md").write_text(report, encoding="utf-8")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
