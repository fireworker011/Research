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
    genre = script.get("genre", "婚活")  # 台本JSONのgenreフィールドで他ジャンルにも流用可
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
        f"あなたは{genre}ジャンルのショート動画クリエイターです。",
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

    # ── ③ フルAgent Mode 完結版(Grok側で完成動画まで作る・最推奨) ──
    full_path = out_dir / f"{pid}_full_agent_prompt.md"
    full_path.write_text(_build_full_agent(script, sources), encoding="utf-8")

    print(f"✅ 作成しました: {step_path.name}(ステップ実行版)")
    print(f"✅ 作成しました: {agent_path.name}(素材のみAgent版)")
    print(f"✅ 作成しました: {full_path.name}(フル完結版・最推奨)")
    print("   フル完結版をGrokのフルAgent Modeに貼ると完成動画1本まで自動生成されます。")
    return step_path, agent_path


def _build_full_agent(script: dict, sources: list[dict]) -> str:
    """Grok フルAgent Mode用: 画像→動画→音声→同期編集→キャプションまで
    一括で完成動画を作らせるプロンプトを台本JSONから組み立てる"""
    pid = script["project_id"]
    char = script.get("character", "")
    genre = script.get("genre", "婚活")
    scenes = script["scenes"]
    final_name = script.get("final_filename", f"{pid}_完成ショート.mp4")

    # ナレーション: 同じ素材(video)を使うシーンを1段落にまとめ、段落間に（間）
    paragraphs: list[str] = []
    cur_video, cur_texts = None, []
    for sc in scenes:
        v = sc.get("video")
        if v != cur_video and cur_texts:
            paragraphs.append("".join(cur_texts))
            cur_texts = []
        cur_video = v
        cur_texts.append(sc["narration"])
    if cur_texts:
        paragraphs.append("".join(cur_texts))
    narration = "\n\n（間）\n\n".join(paragraphs)

    scene_lines = []
    for i, sc in enumerate(sources, 1):
        name = sc.get("video", f"scene_{i:02d}.mp4")
        stem = name.rsplit(".", 1)[0]
        scene_lines.append(
            f"シーン{i}（{stem}）：{sc['image_prompt']}"
            f"動画化：{sc['motion_prompt']}"
        )

    return f"""あなたはGrokのフルAgent Modeで、{genre}ジャンルのYouTube Shortsをプロクオリティで1本完結まで自動生成する専門クリエイターです。
以下の全指示を厳密に守り、**画像生成 → 動画生成 → ナレーション音声作成 → 音声長に完全同期した動画編集（ミュート＋長さ調整） → スマホ最適自然キャプション焼き込み**まで、**一切ユーザーの追加指示なしで最後まで実行**してください。

【必須仕様】
・縦型9:16（スマホ画面想定）
・YouTube Shorts最適化：上部10%（通知バー）と下部15%（再生バー・タイトルエリア）を完全に避けた安全ゾーンにキャプション配置
・キャプションは文の途中で不自然に改行せず、自然な文単位でタイミングよく表示（途切れ感ゼロ、読みやすく）
・最終出力は**1本の完成動画ファイル**（またはダウンロード可能な形式）として提供。ファイル名は「{final_name}」

【キャラクター統一ルール（全シーン厳守）】
{char}
自然なメイク。リアル写真風・高詳細・自然な肌質。全シーンで同一人物として完全に一致させる。

【重要ルール】
・全シーンで**口は一切動かさない**（リップシンク禁止）。表情変化・まばたき・うなずき・視線移動のみで演技。
・音声・BGM・テロップは動画生成時には一切入れない（最終合成で追加）。

【{len(sources)}シーン生成（各約10秒）】
{chr(10).join(scene_lines)}

【ナレーション音声】
以下の全文を「落ち着いた、少し感情がこもった告白するようなトーン」で、テンポよく自然な女性声（コンパニオン風）で読み上げてください。（間）では短く一呼吸置く。

「{narration}」

【最終合成】
・各シーンの無音動画をナレーション音声の対応部分の長さに完全に同期（必要に応じて速度微調整・トリム）。
・動画はミュート状態で音声を重ねる。
・自然キャプションを焼き込み（文単位で自然に区切り、スマホUI被りゼロ、読みやすいフォント・位置、白字+黒縁）。
・全体を高テンポで魅力的な{genre}ショート動画に仕上げる。

完成したら、**「完成動画はこちらです！」**と明記してダウンロード可能な形式で提示してください。
途中経過（各シーン画像・動画・音声単体）も必要に応じて提供可。

今すぐ全パイプラインを自動実行して、最高品質の完成動画を1本作ってください！
"""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python make_prompts.py scripts_json/<台本>.json")
        sys.exit(1)
    make_prompts(Path(sys.argv[1]))
