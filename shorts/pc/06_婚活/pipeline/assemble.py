"""
FFmpeg 合成 — CapCut の手作業を置き換える

シーンごとの動画 + シーンごとのナレーション音声を
「音声の長さに動画を合わせて」結合し、1本の縦型mp4にする。

2026-07改修(伸びない原因の診断結果を反映):
 - テロップ焼き込みを追加(ミュート視聴対応: 白字+黒縁の大テロップ)
   ナレーションを句読点で短いチャンクに割り、2〜3秒ごとに切り替える
 - 語尾の余韻を 0.4s → 0.2s に短縮(テンポ改善)
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

W, H, FPS = 720, 1280, 24

FONT = Path(__file__).parent / "assets" / "fonts" / "NotoSansJP-Bold.otf"
FONT_SIZE = 52          # 720px幅に対して大きめ(スマホで読める)
TELOP_Y = "h*0.70"      # 画面下寄り中央
BORDER_W = 5
CHUNK_MAX = 15          # テロップ1枚の最大文字数(2〜3秒で読める量)


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


def _split_telop(text: str) -> list[str]:
    """ナレーションを読みやすい短チャンクに分割(句読点優先、上限CHUNK_MAX字)"""
    parts = [p for p in re.split(r"[、。!?！？\n]", text) if p.strip()]
    chunks: list[str] = []
    for p in parts:
        p = p.strip()
        while len(p) > CHUNK_MAX:
            chunks.append(p[:CHUNK_MAX])
            p = p[CHUNK_MAX:]
        if p:
            chunks.append(p)
    return chunks or [text[:CHUNK_MAX]]


def _telop_filters(text: str, total: float, tmp: Path, tag: str) -> str:
    """チャンクを時間比例で配分した drawtext フィルタ列を返す"""
    chunks = _split_telop(text)
    total_chars = sum(len(c) for c in chunks) or 1
    filters = []
    t0 = 0.0
    for j, c in enumerate(chunks):
        dur = total * len(c) / total_chars
        tf = tmp / f"telop_{tag}_{j:02d}.txt"
        tf.write_text(c, encoding="utf-8")
        filters.append(
            f"drawtext=fontfile='{FONT}':textfile='{tf}':"
            f"fontsize={FONT_SIZE}:fontcolor=white:borderw={BORDER_W}:bordercolor=black:"
            f"x=(w-text_w)/2:y={TELOP_Y}:"
            f"enable='between(t,{t0:.2f},{t0 + dur:.2f})'"
        )
        t0 += dur
    return ",".join(filters)


def _fit_scene(video: Path, audio: Path, out: Path, telop_text: str | None,
               tmp: Path, tag: str) -> None:
    """シーン動画をナレーション音声の長さに合わせ、テロップを焼き込む"""
    vd, ad = _duration(video), _duration(audio)
    pad = ad + 0.2  # 語尾の余韻(テンポ重視で短め)

    vf = f"scale={W}:{H},fps={FPS}"
    if telop_text:
        vf += "," + _telop_filters(telop_text, pad, tmp, tag)

    if vd >= pad:
        _run([
            "ffmpeg", "-y", "-i", str(video), "-i", str(audio),
            "-t", f"{pad:.2f}",
            "-vf", vf,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-shortest", str(out),
        ])
    else:
        factor = pad / vd
        _run([
            "ffmpeg", "-y", "-i", str(video), "-i", str(audio),
            "-filter_complex",
            f"[0:v]setpts={factor:.4f}*PTS,{vf}[v]",
            "-map", "[v]", "-map", "1:a",
            "-t", f"{pad:.2f}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", str(out),
        ])


def assemble(scene_videos: list[Path], narrations: list[Path],
             out_path: Path, bgm_path: Path | None = None,
             telops: list[str] | None = None) -> Path:
    """シーン結合 + ナレーション + テロップ + BGM(任意) → 完成mp4"""
    tmp = out_path.parent / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    fitted = []
    for i, (v, a) in enumerate(zip(scene_videos, narrations), 1):
        f = tmp / f"fit_{i:02d}.mp4"
        text = telops[i - 1] if telops else None
        _fit_scene(v, a, f, text, tmp, f"{i:02d}")
        fitted.append(f)
        print(f"  ✅ シーン{i} 尺合わせ+テロップ完了")

    lst = tmp / "list.txt"
    lst.write_text("\n".join(f"file '{p.resolve()}'" for p in fitted))
    joined = tmp / "joined.mp4"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
          "-c", "copy", str(joined)])

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
