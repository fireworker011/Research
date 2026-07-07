"""
台本JSON → Grokアプリに貼るプロンプト一覧(Markdown)を書き出す

課金は一切発生しない(APIを呼ばず、テキストを組み立てるだけ)。
スマホでこのMarkdownを開き、シーンごとにGrokアプリへコピペする。

使い方:
  python make_prompts.py scripts_json/003_ng5sen.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).parent


def make_prompts(script_path: Path) -> Path:
    script = json.loads(script_path.read_text(encoding="utf-8"))
    pid = script["project_id"]
    char = script.get("character", "")
    scenes = script["scenes"]

    lines = [
        f"# {pid} — Grokアプリ用プロンプト一覧",
        "",
        "各シーンごとに、①画像プロンプトをGrokに貼って画像生成 →",
        "②できた画像を選んで動画化ボタン →③動きの指示(動画プロンプト)を貼る。",
        f"完成したらファイル名を `scene_01.mp4`〜`scene_{len(scenes):02d}.mp4` にして",
        f"`pipeline/input/{pid}/` フォルダに置く(またはこのチャットに送る)。",
        "",
        "---",
        "",
    ]

    for i, sc in enumerate(scenes, 1):
        lines += [
            f"## シーン{i} (目安{sc.get('duration', 8)}秒)",
            "",
            "**① 画像プロンプト(コピペ用)**",
            "```",
            f"{char} {sc['image_prompt']} テキストなし。",
            "```",
            "",
            "**② 動画化の動きの指示(コピペ用)**",
            "```",
            sc["motion_prompt"],
            "```",
            "",
            f"保存ファイル名: `scene_{i:02d}.mp4`",
            "",
            "---",
            "",
        ]

    out_dir = BASE / "prompts"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{pid}_grok_prompts.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 作成しました: {out_path}")
    print(f"   このファイルをスマホで開いてGrokアプリにコピペしてください。")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python make_prompts.py scripts_json/<台本>.json")
        sys.exit(1)
    make_prompts(Path(sys.argv[1]))
