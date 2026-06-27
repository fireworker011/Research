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

HEADER_TEMPLATE = """\
以下のキャラクター設定を守りながら、7枚の画像を順番に生成してください。
1枚生成するたびに次に進んでください。

【画像サイズ】
縦型 9:16（ポートレート）で生成してください。

【キャラクター固定設定（女性が登場するシーンに必ず適用）】
{woman}
{style}

"""

SCENE_TEMPLATE = "【scene{n}】\n{prompt}\n\n"


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

    # ヘッダー
    body = HEADER_TEMPLATE.format(woman=woman, style=STYLE)

    # 各シーン
    for i, prompt in enumerate(prompts, 1):
        # WOMANプロンプトはヘッダーに書いたので個別プロンプトから除去
        clean = prompt.replace(f"{woman}, ", "").replace(woman, "上記の女性")
        body += SCENE_TEMPLATE.format(n=i, prompt=clean.strip())

    # 出力
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / f"pet{num}_chatgpt_prompts.txt"
    out.write_text(body, encoding="utf-8")
    print(f"  ✅ 保存: {out}  ({len(prompts)}シーン)")


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
    print("ChatGPTに貼り付けるだけで7枚連続生成できます。")


if __name__ == "__main__":
    main()
