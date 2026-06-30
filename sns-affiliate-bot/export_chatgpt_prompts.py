"""
ChatGPT Web用プロンプトファイル自動生成

API不要で ChatGPT Web（GPT-4o）に貼り付けるだけで
7枚の画像を連続生成できるプロンプトを出力する。

使い方:
  python export_chatgpt_prompts.py 8      → pet8用を生成
  python export_chatgpt_prompts.py 7 8 9  → 複数まとめて生成
  python export_chatgpt_prompts.py        → 全動画分を生成

出力先: chatgpt_prompts/ フォルダ
"""

import importlib.util
import sys
from pathlib import Path

OUTPUT_DIR = Path("chatgpt_prompts")

STYLE = "Photorealistic, cinematic, Japanese setting, no text or watermarks. Vertical 9:16 portrait."

CHAR_TEMPLATE = """\
【キャラクター設定】（以降の画像生成にすべて適用してください）
{woman}
{style}
縦型 9:16（ポートレート）の単独画像で生成してください。
"""

SCENE_TEMPLATE = """\
{prompt} {style}
縦型 9:16（ポートレート）。テキスト・ウォーターマークなし。
"""


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("mod", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def export(num: int):
    src = Path(f"generate_images_pet{num}.py")
    if not src.exists():
        print(f"  ❌ {src} が見つかりません")
        return

    mod = load_module(src)
    prompts = mod.PROMPTS
    woman   = getattr(mod, "WOMAN", "Japanese woman in her early 30s")

    out_dir = OUTPUT_DIR / f"pet{num}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # メッセージ0: キャラクター設定（最初に1回送る）
    char_msg = CHAR_TEMPLATE.format(woman=woman, style=STYLE)
    (out_dir / "00_キャラクター設定.txt").write_text(char_msg, encoding="utf-8")

    # メッセージ1〜7: シーンごとに個別ファイル
    for i, prompt in enumerate(prompts, 1):
        clean = prompt.replace(f"{woman}, ", "").replace(woman, "上記の女性")
        msg = SCENE_TEMPLATE.format(prompt=clean.strip(), style=STYLE)
        (out_dir / f"scene{i:02d}.txt").write_text(msg, encoding="utf-8")

    print(f"  ✅ 保存: {out_dir}/  ({len(prompts)}シーン)")
    print(f"     送り方: 00_キャラクター設定.txt → scene01.txt → scene02.txt ... の順に1つずつ送信")


def main():
    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None

    if nums is None:
        # 全動画を自動検出
        nums = sorted(
            int(p.stem.replace("generate_images_pet", ""))
            for p in Path(".").glob("generate_images_pet*.py")
        )

    print("=" * 45)
    print("ChatGPT Webプロンプト エクスポート")
    print("=" * 45)

    for n in nums:
        print(f"\n[動画{n}] 処理中...")
        export(n)

    print(f"\n✅ 完了: {OUTPUT_DIR}/")
    print("送り方: 00_キャラクター設定.txt を最初に送信 → scene01〜07を1つずつ別メッセージで送信")


if __name__ == "__main__":
    main()
