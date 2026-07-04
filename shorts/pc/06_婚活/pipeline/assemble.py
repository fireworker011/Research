"""
FFmpeg 合成 — CapCut の手作業を置き換える

シーンごとの動画 + シーンごとのナレーション音声を
「音声の長さに動画を合わせて」結合し、1本の縦型mp4にする。

テロップ焼き込みはしない(チャンネル方針: キャプションなし)。
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

W, H, FPS = 720, 1280, 24


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg失敗:\n{r.stderr[-2000:]}")


def _duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True,
    )
    return float(json.loads(r.stdout)["format"]["duration"])


def _fit_scene(video: Path, audio: Path, out: Path) -> None:
    """シーン動画をナレーション音声の長さに合わせる(足りなければスローループ)"""
    vd, ad = _duration(video), _duration(audio)
    pad = ad + 0.4  # 語尾の余韻
    if vd >= pad:
        # 動画が長い → カット
        _run([
            "ffmpeg", "-y", "-i", str(video), "-i", str(audio),
            "-t", f"{pad:.2f}",
            "-vf", f"scale={W}:{H},fps={FPS}",
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-shortest", str(out),
        ])
    else:
        # 動画が短い → スロー再生で引き延ばし
        factor = pad / vd
        _run([
            "ffmpeg", "-y", "-i", str(video), "-i", str(audio),
            "-filter_complex",
            f"[0:v]setpts={factor:.4f}*PTS,scale={W}:{H},fps={FPS}[v]",
            "-map", "[v]", "-map", "1:a",
            "-t", f"{pad:.2f}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", str(out),
        ])


def assemble(scene_videos: list[Path], narrations: list[Path],
             out_path: Path, bgm_path: Path | None = None) -> Path:
    """シーン結合 + ナレーション + BGM(任意) → 完成mp4"""
    tmp = out_path.parent / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    # 各シーンを音声尺に合わせる
    fitted = []
    for i, (v, a) in enumerate(zip(scene_videos, narrations), 1):
        f = tmp / f"fit_{i:02d}.mp4"
        _fit_scene(v, a, f)
        fitted.append(f)
        print(f"  ✅ シーン{i} 尺合わせ完了")

    # concat
    lst = tmp / "list.txt"
    lst.write_text("\n".join(f"file '{p.resolve()}'" for p in fitted))
    joined = tmp / "joined.mp4"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
          "-c", "copy", str(joined)])

    # BGM(音量15%でダッキング)
    if bgm_path and bgm_path.exists():
        _run([
            "ffmpeg", "-y", "-i", str(joined), "-stream_loop", "-1", "-i", str(bgm_path),
            "-filter_complex",
            "[1:a]volume=0.15[bgm];[0:a][bgm]amix=inputs=2:duration=first[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", str(out_path),
        ])
    else:
        joined.rename(out_path)

    print(f"✅ 完成: {out_path}")
    return out_path
