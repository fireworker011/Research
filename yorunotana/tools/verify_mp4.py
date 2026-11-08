"""build-yorunotana.ps1 と同じ ffprobe 検査を Python で行う。

合格は 1080x1920、60fps、75.0〜95.0秒、音声ストリームあり。
LAST_RESULT.txt は `PASS | <job_id>.mp4 | 86.8s | PR:True` の1行。
"""

from __future__ import annotations

import argparse
import json
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
        if not (75.0 <= duration <= 95.0):
            reasons.append(f"尺が {duration:.3f}秒")
        if not has_audio:
            reasons.append("音声ストリームがない")
    status = "PASS" if not reasons else "FAIL"
    line = f"{status} | {job_id}.mp4 | {duration:.1f}s | PR:{pr_text}"
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
            f"- 尺: {duration:.3f}秒 （基準 75.0〜95.0） {mark(75.0 <= duration <= 95.0)}",
            f"- 音声ストリーム: {'あり' if has_audio else 'なし'} {mark(has_audio)}",
            f"- PRバッジ（ジョブ指定）: {pr_text}",
            f"- 総合: {status}",
            "",
            "## 各カット",
            *cuts(Path(args.timing) if args.timing else None),
            "",
            "## A8提出前チェック",
            "- 画面は 1080x1920 の縦動画",
            "- 尺は 75.0秒以上 95.0秒以下",
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
