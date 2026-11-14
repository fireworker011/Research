#!/usr/bin/env python3
"""生成カットを参考タイムラインの尺に合わせて 1080x1920 でつなぐ。

使い方:
    python3 finish.py timeline.json gen_dir out.mp4 --audio voice.wav
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ksutil

SLACK_FRAMES = 2


def gen_path(gen_dir: Path, index: int) -> Path:
    path = gen_dir / f"gen{index:02d}.mp4"
    if not path.is_file():
        ksutil.die(f"生成カットがありません: {path}")
    return path


def build_vf(
    start: float,
    trim_dur: float,
    speed: float,
    out_fps: int,
    shake: bool,
    grain: bool,
    vignette: bool,
) -> str:
    filters = [
        f"trim=start={start:.6f}:duration={trim_dur:.6f}",
        f"setpts=(PTS-STARTPTS)/{speed:.8f}",
        f"fps={out_fps}",
    ]
    if shake:
        zoom_w = round(ksutil.OUT_W * 1.05)
        zoom_h = round(ksutil.OUT_H * 1.05)
        filters.append(f"scale={zoom_w}:{zoom_h}:force_original_aspect_ratio=increase")
        filters.append(f"crop={zoom_w}:{zoom_h}")
        filters.append(
            "crop="
            f"{ksutil.OUT_W}:{ksutil.OUT_H}:"
            "x='(in_w-out_w)/2+3*sin(n/8)':"
            "y='(in_h-out_h)/2+2*cos(n/11)'"
        )
    else:
        filters.append(
            f"scale={ksutil.OUT_W}:{ksutil.OUT_H}:force_original_aspect_ratio=increase"
        )
        filters.append(f"crop={ksutil.OUT_W}:{ksutil.OUT_H}")
    if vignette:
        filters.append("vignette=angle=PI/5")
    if grain:
        filters.append("noise=alls=8:allf=t")
    filters.append("setsar=1")
    filters.append("format=yuv420p")
    return ",".join(filters)


def plan_window(
    cut: dict,
    gen: Path,
    speed: float,
    out_fps: int,
    source_fps: float,
    peak_align: bool,
) -> tuple[float, float]:
    out_n = ksutil.out_frames_for(cut, out_fps, source_fps)
    src_dur = out_n / out_fps * speed
    slack = SLACK_FRAMES / out_fps * speed
    info = ksutil.ffprobe(gen)
    gen_dur = info["duration_sec"]
    need = ksutil.HEAD_SEC + src_dur
    if gen_dur < need - 1e-3:
        ksutil.die(
            f"{gen.name} が短いです。先頭 {ksutil.HEAD_SEC:.2f}s を外したあと "
            f"{src_dur:.2f}s 必要ですが、動画は {gen_dur:.2f}s です"
        )
    earliest = ksutil.HEAD_SEC
    latest = max(earliest, gen_dur - src_dur)
    if peak_align:
        scanned = ksutil.scan_motion(gen, info["fps"], ignore_before_sec=ksutil.HEAD_SEC)
        ideal = scanned["peak_frame"] / info["fps"] - float(cut["peak_sec"]) * speed
        if ideal < earliest - 1e-3 or ideal > latest + 1e-3:
            print(
                f"注意: cut {int(cut['index']):02d} の peak は、尺が収まる範囲にずらして合わせます",
                file=sys.stderr,
            )
    else:
        ideal = earliest
    start = min(max(ideal, earliest), latest)
    room = gen_dur - start
    trim_dur = src_dur + slack if room >= src_dur + slack - 1e-3 else src_dur
    return start, trim_dur


def render_segment(
    cut: dict,
    gen: Path,
    dest: Path,
    speed: float,
    out_fps: int,
    source_fps: float,
    peak_align: bool,
    shake: bool,
    grain: bool,
    vignette: bool,
) -> None:
    out_n = ksutil.out_frames_for(cut, out_fps, source_fps)
    start, trim_dur = plan_window(cut, gen, speed, out_fps, source_fps, peak_align)
    vf = build_vf(start, trim_dur, speed, out_fps, shake, grain, vignette)
    ksutil.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(gen),
            "-vf",
            vf,
            "-frames:v",
            str(out_n),
            *ksutil.encode_args(out_fps),
            "-an",
            str(dest),
        ]
    )
    info = ksutil.ffprobe(dest)
    if info["frame_count"] != out_n:
        ksutil.die(
            f"{gen.name} から {out_n} フレームを切り出せませんでした"
            f"（得られたのは {info['frame_count']}）。生成動画の長さが足りない可能性があります"
        )
    if info["width"] != ksutil.OUT_W or info["height"] != ksutil.OUT_H or info["pix_fmt"] != "yuv420p":
        ksutil.die(f"{dest.name} が 1080x1920 yuv420p ではありません")


def concat_reencode(segments: list[Path], dest: Path, fps: int) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for segment in segments:
        cmd.extend(["-i", str(segment)])
    count = len(segments)
    graph = "".join(f"[{i}:v]" for i in range(count))
    graph += f"concat=n={count}:v=1:a=0,setsar=1,format=yuv420p[v]"
    cmd.extend(
        [
            "-filter_complex",
            graph,
            "-map",
            "[v]",
            *ksutil.encode_args(fps),
            "-an",
            str(dest),
        ]
    )
    ksutil.run(cmd)


def concat_segments(segments: list[Path], dest: Path, fps: int) -> None:
    expected = sum(ksutil.ffprobe(segment)["frame_count"] for segment in segments)
    if len(segments) == 1:
        shutil.copyfile(segments[0], dest)
    else:
        listing = dest.with_suffix(".txt")
        lines = []
        for segment in segments:
            quoted = str(segment.resolve()).replace("'", "'\\''")
            lines.append(f"file '{quoted}'")
        listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
        proc = subprocess.run(
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
                "-c",
                "copy",
                str(dest),
            ],
            capture_output=True,
            text=True,
        )
        listing.unlink(missing_ok=True)
        got = ksutil.ffprobe(dest)["frame_count"] if proc.returncode == 0 and dest.is_file() else -1
        if proc.returncode != 0 or got != expected:
            concat_reencode(segments, dest, fps)
    got = ksutil.ffprobe(dest)["frame_count"]
    if got != expected:
        ksutil.die(f"結合後のフレーム数が合いません: {got} != {expected}")


def xfade_segments(segments: list[Path], dest: Path, fps: int, xfade: float) -> None:
    durations = [ksutil.ffprobe(segment)["frame_count"] / fps for segment in segments]
    for index, duration in enumerate(durations, start=1):
        if duration <= xfade:
            ksutil.die(f"カット {index} の尺 {duration:.3f}s が --xfade {xfade:.3f}s 以下です")
    parts: list[str] = []
    previous = "[0:v]"
    consumed = 0.0
    for index in range(1, len(segments)):
        consumed += durations[index - 1]
        offset = consumed - xfade * index
        if offset <= 0:
            ksutil.die("クロスフェードの開始位置が 0 以下です。--xfade を短くしてください")
        label = "[vout]" if index == len(segments) - 1 else f"[vx{index}]"
        parts.append(
            f"{previous}[{index}:v]xfade=transition=fade:duration={xfade:.6f}:offset={offset:.6f}{label}"
        )
        previous = label
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for segment in segments:
        cmd.extend(["-i", str(segment)])
    cmd.extend(
        [
            "-filter_complex",
            ";".join(parts),
            "-map",
            "[vout]",
            *ksutil.encode_args(fps),
            "-an",
            str(dest),
        ]
    )
    ksutil.run(cmd)


def mux_audio(video: Path, wav: Path, dest: Path) -> None:
    ksutil.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-i",
            str(wav),
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
            "-movflags",
            "+faststart",
            str(dest),
        ]
    )


def apply_gain(wav: Path, dest: Path, gain_db: float) -> None:
    ksutil.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(wav),
            "-af",
            f"volume={gain_db:.4f}dB",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(dest),
        ]
    )


def write_with_audio(video: Path, audio: Path, dest: Path, duration: float, work: Path) -> None:
    wav = work / "norm.wav"
    ksutil.render_normalized_wav(audio, wav, duration)
    mux_audio(video, wav, dest)
    measured = ksutil.measure_loudness(dest)
    if measured is not None and (measured < -14.5 or measured > -13.5):
        gained = work / "norm-gain.wav"
        apply_gain(wav, gained, ksutil.TARGET_LUFS - measured)
        mux_audio(video, gained, dest)
        measured = ksutil.measure_loudness(dest)
    if measured is None:
        print("注意: 出力のラウドネスを測れませんでした", file=sys.stderr)
    else:
        print(f"loudness {measured:.2f} LUFS")


def finish(
    timeline_path: Path,
    gen_dir: Path,
    out_path: Path,
    fps: int | None,
    speed: float,
    xfade: float,
    peak_align: bool,
    grain: bool,
    vignette: bool,
    shake: bool,
    audio: Path | None,
) -> None:
    if not math.isfinite(speed) or speed <= 0:
        ksutil.die("--speed は 0 より大きい数です")
    if not math.isfinite(xfade) or xfade < 0:
        ksutil.die("--xfade は 0 以上の秒です")
    if audio is not None and not audio.is_file():
        ksutil.die(f"音声がありません: {audio}")
    if not gen_dir.is_dir():
        ksutil.die(f"生成カットのフォルダがありません: {gen_dir}")

    timeline = ksutil.load_timeline(timeline_path)
    out_fps = ksutil.resolve_out_fps(timeline, fps)
    source_fps = ksutil.timeline_fps(timeline)
    cuts = timeline["cuts"]
    if xfade > 0:
        for cut in cuts:
            if float(cut["duration_sec"]) <= xfade:
                ksutil.die(
                    f"cut {int(cut['index']):02d} の尺が --xfade {xfade:.3f}s 以下です"
                )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ks-finish-") as tmp:
        work = Path(tmp)
        segments: list[Path] = []
        for cut in cuts:
            gen = gen_path(gen_dir, int(cut["index"]))
            dest = work / f"seg{int(cut['index']):02d}.mp4"
            render_segment(
                cut,
                gen,
                dest,
                speed,
                out_fps,
                source_fps,
                peak_align,
                shake,
                grain,
                vignette,
            )
            segments.append(dest)
            print(f"seg {int(cut['index']):02d}  {ksutil.ffprobe(dest)['frame_count']}f")

        joined = work / "joined.mp4"
        if xfade > 0 and len(segments) > 1:
            xfade_segments(segments, joined, out_fps, xfade)
        else:
            concat_segments(segments, joined, out_fps)

        info = ksutil.ffprobe(joined)
        if audio is None:
            fast = work / "fast.mp4"
            ksutil.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(joined),
                    "-c",
                    "copy",
                    "-movflags",
                    "+faststart",
                    str(fast),
                ]
            )
            shutil.move(fast, out_path)
        else:
            write_with_audio(joined, audio, out_path, info["duration_sec"], work)

    final = ksutil.ffprobe(out_path)
    if final["width"] != ksutil.OUT_W or final["height"] != ksutil.OUT_H:
        ksutil.die(f"出力サイズが {final['width']}x{final['height']} です")
    if final["codec"] != "h264" or final["pix_fmt"] != "yuv420p":
        ksutil.die(f"出力が H.264 yuv420p ではありません: {final['codec']} {final['pix_fmt']}")
    print(
        f"wrote {out_path}  {final['width']}x{final['height']}  "
        f"{final['fps_rational']}  {final['frame_count']}f  {final['duration_sec']:.3f}s"
    )


def main(argv: list[str] | None = None) -> int:
    ksutil.require_tools()
    parser = argparse.ArgumentParser(
        description="生成カット（genNN.mp4）を参考タイムラインの尺に合わせてつなぐ。"
    )
    parser.add_argument("timeline", type=Path, help="split_ref.py の timeline.json")
    parser.add_argument("gen_dir", type=Path, help="gen01.mp4 があるフォルダ")
    parser.add_argument("out", type=Path, help="出力 mp4")
    parser.add_argument("--fps", type=int, default=None, help="24 か 30。省略時は timeline に合わせる")
    parser.add_argument("--speed", type=float, default=1.0, help="生成側の再生速度。出力尺は元のまま")
    parser.add_argument("--xfade", type=float, default=0.0, help="クロスフェード秒。0 ならカット")
    parser.add_argument("--peak-align", action="store_true", help="生成側の動きの山を元の Peak に合わせる")
    parser.add_argument("--grain", action="store_true", help="細いグレインを足す")
    parser.add_argument("--vignette", action="store_true", help="ビネットを足す")
    parser.add_argument("--shake", action="store_true", help="ごく小さい手ブレと 105%% 拡大")
    parser.add_argument("--audio", type=Path, default=None, help="この音声を -14 LUFS にして載せる")
    args = parser.parse_args(argv)
    finish(
        args.timeline,
        args.gen_dir,
        args.out,
        args.fps,
        args.speed,
        args.xfade,
        args.peak_align,
        args.grain,
        args.vignette,
        args.shake,
        args.audio,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
