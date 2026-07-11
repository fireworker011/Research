"""
台本JSON → Grokに貼るプロンプトを書き出す(2種類・課金なし)

  ① ステップ実行版: シーンごとに画像→動画を手動で進める(旧来型)
  ② Agent Mode 一括版: Grok Imagine の Agent Mode に1回貼るだけで
     全シーンの画像生成→動画化を自動連続実行させる(推奨)

台本JSONに "source_scenes"(実際に生成する動画素材の定義。image_prompt/
motion_prompt/videoファイル名を持つ) があればそれを使う。
なければ従来通り "scenes" をそのまま素材定義として扱う(#003/#004互換)。

使い方:
  python make_prompts.py scripts_json/005_sakiokuri.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).parent


def _get_source_scenes(script: dict) -> list[dict]:
    if "source_scenes" in script:
        return script["source_scenes"]
    return script["scenes"]  # 旧フォーマット(#003/#004): scenes = 素材定義


def make_prompts(script_path: Path) -> tuple[Path, Path]:
    script = json.loads(script_path.read_text(encoding="utf-8"))
    pid = script["project_id"]
    char = script.get("character", "")
    sources = _get_source_scenes(script)
    n = len(sources)

    out_dir = BASE / "prompts"
    out_dir.mkdir(exist_ok=True)

    # ── ① ステップ実行版 ──────────────────────────────────────
    step_lines = [
        f"# {pid} — Grokアプリ用プロンプト一覧(ステップ実行版)",
        "",
        "各シーンごとに、①画像プロンプトをGrokに貼って画像生成 →",
        "②できた画像を選んで動画化ボタン →③動きの指示(動画プロンプト)を貼る。",
        f"完成したらファイル名を `scene_01.mp4`〜`scene_{n:02d}.mp4` にして",
        "このチャットに送る(またはinput/フォルダに配置)。",
        "",
        "**注意**: ナレーション音声は後からパイプライン側で合成します。",
        "動画生成時は「口を閉じたまま、話しているように見える動きはさせない」よう",
        "動画プロンプトに必ず含めてください(リップシンクのズレ防止)。",
        "",
        "---",
        "",
    ]
    for i, sc in enumerate(sources, 1):
        name = sc.get("video", f"scene_{i:02d}.mp4")
        step_lines += [
            f"## シーン{i} (目安{sc.get('duration', 10)}秒)",
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
            f"保存ファイル名: `{name}`",
            "",
            "---",
            "",
        ]
    step_path = out_dir / f"{pid}_grok_prompts.md"
    step_path.write_text("\n".join(step_lines), encoding="utf-8")

    # ── ② Agent Mode 一括版 ───────────────────────────────────
    agent_lines = [
        f"# Grok Imagine Agent Mode — 一括実行プロンプト({pid})",
        "",
        "> Grok Imagine の Agent Mode にこのブロックをそのまま貼ってください。",
        f"> 画像生成→動画化を{n}シーン分、Agentが自動で連続実行します。",
        "> テロップ・ナレーション音声・BGMは不要(パイプライン側で自動合成するため)。",
        "",
        "---",
        "",
        "あなたは婚活ジャンルのショート動画クリエイターです。",
        f"以下の{n}シーンについて、①画像生成 → ②その画像を動画化、を順番に自動で行ってください。",
        "音声・BGM・テキスト(テロップ)は一切不要です。各シーンの動画だけ作ってください。",
        "",
        "【重要】ナレーション音声は別撮りで後からパイプライン側が合成します。",
        "動画内の人物は口を閉じたまま、話しているように見える動きは一切させないでください",
        "(リップシンクさせると、後から乗せるナレーションと口の動きがズレて不自然になります)。",
        "表情の変化・まばたき・うなずき・視線の動きだけで演技してください。",
        "",
        "【全シーン共通のキャラクター設定・必ず統一すること】",
        char,
        "全シーンで同一人物として描くこと。",
        "",
        "---",
        "",
    ]
    for i, sc in enumerate(sources, 1):
        name = sc.get("video", f"scene_{i:02d}.mp4")
        agent_lines += [
            f"### シーン{i}(保存名: {name} / 尺目安{sc.get('duration', 10)}秒)",
            f"**画像**: {sc['image_prompt']} テキストなし。",
            f"**動画化**: {sc['motion_prompt']}",
            "",
        ]
    agent_lines += [
        "---",
        "",
        f"{n}本すべて完成したら、上記のファイル名でダウンロードし、",
        "このチャットに送ってください。私がテロップ入り高テンポ版に合成して投稿準備まで進めます。",
    ]
    agent_path = out_dir / f"{pid}_agent_prompt.md"
    agent_path.write_text("\n".join(agent_lines), encoding="utf-8")

    print(f"✅ 作成しました: {step_path.name}(ステップ実行版)")
    print(f"✅ 作成しました: {agent_path.name}(Agent Mode 一括版・推奨)")
    print("   Agent Mode版をGrok Imagineに貼ると画像→動画を自動連続生成できます。")
    return step_path, agent_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python make_prompts.py scripts_json/<台本>.json")
        sys.exit(1)
    make_prompts(Path(sys.argv[1]))
