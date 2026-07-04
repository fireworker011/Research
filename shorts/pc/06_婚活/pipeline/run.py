"""
婚活Shorts 完全自動パイプライン — オーケストレーター

台本JSON → Grok画像 → Grok動画 → TTS音声 → FFmpeg合成 → YouTube投稿

使い方:
  # 生成のみ(投稿前に人間が1回確認する運用を推奨)
  python run.py scripts_json/003_ng5sen.json

  # 生成 + 確認スキップで自動投稿
  python run.py scripts_json/003_ng5sen.json --upload

  # 生成済み動画を投稿だけ
  python run.py scripts_json/003_ng5sen.json --upload-only
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from assemble import assemble
from grok_client import GrokClient
from tts import generate_scene_narrations

BASE = Path(__file__).parent
OUT = BASE / "output"


def build(script_path: Path, do_upload: bool = False, upload_only: bool = False) -> Path:
    script = json.loads(script_path.read_text(encoding="utf-8"))
    pid = script["project_id"]
    scenes = script["scenes"]
    workdir = OUT / pid
    final = workdir / f"{pid}_final.mp4"

    if not upload_only:
        grok = GrokClient()

        # ① 画像生成(キャラ一貫性: 全プロンプトに共通キャラ設定を前置)
        char = script.get("character", "")
        print("── ① Grok 画像生成 ──")
        images = []
        for i, sc in enumerate(scenes, 1):
            p = workdir / "images" / f"scene_{i:02d}.png"
            if not p.exists():
                grok.generate_image(f"{char} {sc['image_prompt']} テキストなし。", p)
            images.append(p)

        # ② 画像 → 動画
        print("── ② Grok 動画生成 ──")
        videos = []
        for i, (sc, img) in enumerate(zip(scenes, images), 1):
            p = workdir / "videos" / f"scene_{i:02d}.mp4"
            if not p.exists():
                grok.image_to_video(img, sc["motion_prompt"], sc.get("duration", 8), p)
            videos.append(p)

        # ③ ナレーション音声
        print("── ③ TTS 音声生成 ──")
        narrations = generate_scene_narrations(scenes, workdir / "audio")

        # ④ FFmpeg 合成
        print("── ④ FFmpeg 合成 ──")
        bgm = BASE / "assets" / script.get("bgm", "")
        assemble(videos, narrations, final, bgm if script.get("bgm") else None)

    # ⑤ YouTube 投稿
    if do_upload or upload_only:
        print("── ⑤ YouTube 投稿 ──")
        from upload import upload_short
        upload_short(
            final,
            title=script["title"],
            description=script["description"],
            tags=script.get("tags", []),
        )
    else:
        print(f"\n動画を確認してください: {final}")
        print(f"問題なければ: python run.py {script_path} --upload-only")

    return final


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    build(
        Path(args[0]),
        do_upload="--upload" in args,
        upload_only="--upload-only" in args,
    )
