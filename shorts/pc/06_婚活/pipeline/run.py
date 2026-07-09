"""
婚活Shorts 自動パイプライン(無料版) — オーケストレーター

Grokアプリで手動生成したシーン動画(scene_01.mp4〜)を受け取り、
TTS音声との尺合わせ・結合・YouTube投稿だけを自動化する。
画像/動画生成のAPI課金は一切発生しない。

使い方:
  # 1) 台本からGrokに貼るプロンプト一覧を書き出す(このステップは課金なし)
  python make_prompts.py scripts_json/003_ng5sen.json
  → prompts/003_ng5sen_grok_prompts.md ができるのでGrokアプリに1つずつ貼る

  # 2) Grokで作った動画を input/<project_id>/scene_01.mp4 ... に置く
  #    (Google Driveアプリ等でスマホから直接このフォルダに置ければOK。
  #     置けない場合はClaudeとのチャットに動画を送ってもらえればアップロードします)

  # 3) 合成のみ(投稿前に人間が1回確認する運用を推奨)
  python run.py scripts_json/003_ng5sen.json

  # 4) 確認OKなら投稿(非公開)
  python run.py scripts_json/003_ng5sen.json --upload-only

  # 5) 確認もスキップして即公開したい場合
  python run.py scripts_json/003_ng5sen.json --upload-only --public
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from assemble import assemble
from tts import generate_scene_narrations

BASE = Path(__file__).parent
OUT = BASE / "output"
IN = BASE / "input"


def build(script_path: Path, do_upload: bool = False, upload_only: bool = False,
          privacy: str = "private") -> Path:
    script = json.loads(script_path.read_text(encoding="utf-8"))
    pid = script["project_id"]
    scenes = script["scenes"]
    workdir = OUT / pid
    final = workdir / f"{pid}_final.mp4"

    if not upload_only:
        # ① シーン動画は Grokアプリで手動生成済みのものを読み込む(課金なし)
        #    scene に "video" があればそのファイルを使う(同じクリップの使い回し可
        #    → 6本の素材から12カットの高テンポ動画が作れる)
        print("── ① 手動生成済みシーン動画を確認 ──")
        scene_dir = IN / pid
        videos = []
        for i, sc in enumerate(scenes, 1):
            name = sc.get("video", f"scene_{i:02d}.mp4")
            p = scene_dir / name
            if not p.exists():
                raise FileNotFoundError(
                    f"シーン動画が見つかりません: {p}\n"
                    f"Grokアプリで生成した動画をこのパスに置いてから再実行してください。\n"
                    f"プロンプト一覧: python make_prompts.py {script_path}"
                )
            videos.append(p)
        print(f"  ✅ {len(videos)}シーン確認OK")

        # ② ナレーション音声(無料: Edge TTS)
        print("── ② TTS 音声生成 ──")
        narrations = generate_scene_narrations(scenes, workdir / "audio")

        # ③ FFmpeg 合成(無料) — テロップは既定でON(ミュート視聴対応)
        print("── ③ FFmpeg 合成 ──")
        bgm = BASE / "assets" / script.get("bgm", "")
        telops = None
        if script.get("telop", True):
            telops = [sc.get("telop_text", sc["narration"]) for sc in scenes]
        assemble(videos, narrations, final, bgm if script.get("bgm") else None,
                 telops=telops)

    # ④ YouTube 投稿
    if do_upload or upload_only:
        print("── ④ YouTube 投稿 ──")
        from upload import upload_short
        upload_short(
            final,
            title=script["title"],
            description=script["description"],
            tags=script.get("tags", []),
            privacy=privacy,
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
    privacy = "public" if "--public" in args else "private"
    build(
        Path(args[0]),
        do_upload="--upload" in args,
        upload_only="--upload-only" in args,
        privacy=privacy,
    )
