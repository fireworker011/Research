"""ffprobe、フレーム差分、ラウドネスなど、3本のスクリプトが共有する処理。"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np

HEAD_SEC = 0.25
OUT_W = 1080
OUT_H = 1920
SCENE_THRESHOLD = 27.0
TARGET_LUFS = -14.0
DURATION_TOL_SEC = 0.2
CUT_TOL_FRAMES = 2


def die(message: str) -> None:
    raise SystemExit(message)


def require_tools() -> None:
    for name in ("ffmpeg", "ffprobe"):
        if shutil.which(name) is None:
            die(f"{name} が見つかりません")


def run(cmd: list[str], *, quiet: bool = True) -> subprocess.CompletedProcess[str]:
    args = list(cmd)
    if quiet and "-hide_banner" not in args:
        args.insert(1, "-hide_banner")
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail = "\n".join(tail[-25:])
        die(f"コマンドが失敗しました: {' '.join(args[:8])}\n{detail}")
    return proc


def parse_json_tail(text: str) -> dict:
    start = text.rfind("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        die("ffmpeg の JSON 出力を読めませんでした")
    return json.loads(text[start : end + 1])


def ffprobe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,nb_read_frames,nb_frames,codec_name,pix_fmt",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        die(f"ffprobe に失敗しました: {path}\n{(proc.stderr or '').strip()}")
    payload = json.loads(proc.stdout)
    streams = payload.get("streams") or []
    if not streams:
        die(f"映像ストリームがありません: {path}")
    stream = streams[0]
    fps = Fraction(stream.get("r_frame_rate") or "0/1")
    if fps <= 0:
        die(f"fps を読めません: {path}")
    raw_frames = stream.get("nb_read_frames") or stream.get("nb_frames")
    if raw_frames is None:
        die(f"フレーム数を読めません: {path}")
    frames = int(raw_frames)
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "fps": float(fps),
        "fps_fraction": fps,
        "fps_rational": f"{fps.numerator}/{fps.denominator}",
        "frame_count": frames,
        "duration_sec": float(Fraction(frames, 1) / fps),
        "codec": stream.get("codec_name") or "",
        "pix_fmt": stream.get("pix_fmt") or "",
    }


def has_audio(path: Path) -> bool:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    return "audio" in (proc.stdout or "")


def load_timeline(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"timeline.json を読めません: {exc}")
    if not isinstance(data, dict) or not data.get("cuts"):
        die("timeline にカットがありません")
    for key in ("fps", "duration_sec"):
        if key not in data:
            die(f"timeline に {key} がありません")
    needed = ("index", "start_sec", "end_sec", "duration_sec", "frame_count", "peak_sec")
    for cut in data["cuts"]:
        for key in needed:
            if key not in cut:
                die(f"カットに {key} がありません")
    data["cuts"] = sorted(data["cuts"], key=lambda cut: int(cut["index"]))
    return data


def timeline_fps(timeline: dict) -> float:
    rational = timeline.get("fps_rational")
    if rational:
        return float(Fraction(str(rational)))
    return float(timeline["fps"])


def out_frames_for(cut: dict, out_fps: float, timeline_fps_value: float) -> int:
    if abs(out_fps - timeline_fps_value) < 0.02:
        return int(cut["frame_count"])
    return max(1, int(round(float(cut["duration_sec"]) * out_fps)))


def expected_boundaries(timeline: dict, out_fps: float) -> list[int]:
    source_fps = timeline_fps(timeline)
    acc = 0
    bounds: list[int] = []
    cuts = timeline["cuts"]
    for cut in cuts[:-1]:
        acc += out_frames_for(cut, out_fps, source_fps)
        bounds.append(acc)
    return bounds


def encode_args(fps: int) -> list[str]:
    return [
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-bf",
        "0",
        "-r",
        str(fps),
        "-fps_mode",
        "cfr",
        "-g",
        str(max(1, fps)),
    ]


def scan_motion(
    path: Path,
    fps: float,
    ignore_before_sec: float = 0.0,
    keep_images: bool = False,
) -> dict:
    """フレーム差分が最大のフレームを返す。同点なら早いフレームを採る。"""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        die(f"映像を開けません: {path}")
    ignore_frame = int(math.ceil(ignore_before_sec * fps - 1e-9))
    first = None
    last = None
    peak_img = None
    prev = None
    best_score = -1.0
    best_index = 0
    index = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            current = frame.copy()
            if first is None:
                first = current
            if prev is not None and index >= ignore_frame and (index - 1) >= ignore_frame:
                score = float(cv2.absdiff(current, prev).mean())
                if score > best_score:
                    best_score = score
                    best_index = index
                    if keep_images:
                        peak_img = current
            last = current
            prev = current
            index += 1
    finally:
        cap.release()
    if index == 0 or first is None or last is None:
        die(f"フレームがありません: {path}")
    if best_score < 0:
        best_index = min(ignore_frame, index - 1)
        peak_img = first
    elif peak_img is None and keep_images:
        peak_img = first
    return {
        "frame_count": index,
        "peak_frame": best_index,
        "peak_score": best_score,
        "start": first if keep_images else None,
        "peak": peak_img if keep_images else None,
        "end": last if keep_images else None,
    }


def write_png(path: Path, image: np.ndarray) -> None:
    if image is None or not cv2.imwrite(str(path), image):
        die(f"PNG を書けません: {path}")


def frame_diffs(path: Path) -> list[float]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        die(f"映像を開けません: {path}")
    prev = None
    diffs: list[float] = []
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            small = cv2.resize(frame, (180, 320), interpolation=cv2.INTER_AREA)
            if prev is None:
                diffs.append(0.0)
            else:
                diffs.append(float(cv2.absdiff(small, prev).mean()))
            prev = small
    finally:
        cap.release()
    return diffs


def cut_alignment(diffs: list[float], expected: list[int]) -> tuple[bool, int, str]:
    """各基準切れ目の近くで差分の山が ±2 フレーム以内にあるかを見る。"""
    if not expected:
        return True, 0, "切れ目の最大ずれ 0フレーム"
    max_delta = 0
    weak: list[int] = []
    far: list[int] = []
    for boundary in expected:
        lo = max(1, boundary - 4)
        hi = min(len(diffs) - 1, boundary + 4)
        if hi < lo:
            weak.append(boundary)
            continue
        window = range(lo, hi + 1)
        peak = max(window, key=lambda i: diffs[i])
        delta = abs(peak - boundary)
        max_delta = max(max_delta, delta)
        background_values = [diffs[i] for i in window if abs(i - peak) > 1]
        background = float(np.median(background_values)) if background_values else 0.0
        strong = diffs[peak] >= max(8.0, background * 2.5)
        if not strong:
            weak.append(boundary)
        elif delta > CUT_TOL_FRAMES:
            far.append(boundary)
    if weak:
        return False, max_delta, f"切れ目を確認できない（フレーム {weak[0]} 付近）"
    if far:
        return False, max_delta, f"切れ目の最大ずれ {max_delta}フレーム（許容 ±{CUT_TOL_FRAMES}）"
    return True, max_delta, f"切れ目の最大ずれ {max_delta}フレーム"


def read_frames_at(path: Path, indices: list[int]) -> dict[int, np.ndarray]:
    wanted = set(indices)
    found: dict[int, np.ndarray] = {}
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        die(f"映像を開けません: {path}")
    index = 0
    try:
        while wanted - set(found):
            ok, frame = cap.read()
            if not ok:
                break
            if index in wanted:
                found[index] = frame.copy()
            index += 1
    finally:
        cap.release()
    return found


def write_contact_sheet(path: Path, frames: list[np.ndarray]) -> None:
    if not frames:
        die("コンタクトシートにするフレームがありません")
    thumb_w, thumb_h = 270, 480
    thumbs = [
        cv2.resize(frame, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA) for frame in frames
    ]
    cols = min(4, len(thumbs))
    rows = int(math.ceil(len(thumbs) / cols))
    sheet = np.zeros((rows * thumb_h, cols * thumb_w, 3), dtype=np.uint8)
    for number, thumb in enumerate(thumbs):
        row, col = divmod(number, cols)
        y = row * thumb_h
        x = col * thumb_w
        sheet[y : y + thumb_h, x : x + thumb_w] = thumb
        cv2.putText(
            sheet,
            f"{number + 1:02d}",
            (x + 12, y + 36),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    write_png(path, sheet)


def measure_loudness(path: Path) -> float | None:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-af",
            "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    try:
        stats = parse_json_tail(proc.stderr or "")
        value = float(stats["input_i"])
    except (json.JSONDecodeError, KeyError, ValueError, SystemExit):
        return None
    if not math.isfinite(value):
        return None
    return value


def loudnorm_stats(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-af",
            "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        die(f"ラウドネスを測れません: {path}\n{(proc.stderr or '')[-800:]}")
    stats = parse_json_tail(proc.stderr or "")
    try:
        measured = float(stats["input_i"])
    except (KeyError, ValueError) as exc:
        die(f"ラウドネスの数値がありません: {exc}")
    if not math.isfinite(measured):
        die(f"音声が無音に近いため -14 LUFS にそろえられません: {path}")
    return stats


def render_normalized_wav(audio: Path, dest: Path, duration: float) -> None:
    """音声を映像の長さに切り（短ければループし）、-14 LUFS 付近の wav にする。"""
    fitted = dest.with_name(dest.stem + "-fitted.wav")
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-stream_loop",
            "-1",
            "-i",
            str(audio),
            "-t",
            f"{duration:.6f}",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(fitted),
        ]
    )
    stats = loudnorm_stats(fitted)
    loudnorm = (
        "loudnorm=I=-14:TP=-1.5:LRA=11:"
        f"measured_I={stats['input_i']}:measured_LRA={stats['input_lra']}:"
        f"measured_TP={stats['input_tp']}:measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:linear=true"
    )
    proc = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(fitted),
            "-af",
            loudnorm,
            "-ar",
            "48000",
            "-ac",
            "2",
            str(dest),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(fitted),
                "-af",
                loudnorm.replace(":linear=true", ""),
                "-ar",
                "48000",
                "-ac",
                "2",
                str(dest),
            ]
        )
    measured = measure_loudness(dest)
    if measured is None:
        die("そろえた音声のラウドネスを測れませんでした")
    if measured < -14.5 or measured > -13.5:
        gain = TARGET_LUFS - measured
        corrected = dest.with_name(dest.stem + "-gain.wav")
        run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(dest),
                "-af",
                f"volume={gain:.4f}dB",
                "-ar",
                "48000",
                "-ac",
                "2",
                str(corrected),
            ]
        )
        corrected.replace(dest)
    fitted.unlink(missing_ok=True)


def black_starts(path: Path) -> list[str]:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-vf",
            "blackdetect=d=0.001:pic_th=0.98:pix_th=0.10",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()
        die("blackdetect に失敗しました\n" + "\n".join(tail[-15:]))
    starts: list[str] = []
    for line in (proc.stderr or "").splitlines():
        if "black_start:" not in line:
            continue
        for token in line.split():
            if token.startswith("black_start:"):
                starts.append(token.split(":", 1)[1])
    return starts


def resolve_out_fps(timeline: dict, requested: int | None) -> int:
    if requested is not None:
        if requested not in (24, 30):
            die("--fps は 24 か 30 です")
        return requested
    fps = timeline_fps(timeline)
    if abs(fps - 24) < 0.02:
        return 24
    if abs(fps - 30) < 0.02:
        return 30
    die("timeline の fps が 24 でも 30 でもないので、--fps 24 か --fps 30 を指定してください")
