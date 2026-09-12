"""
動画㊶「お昼休み、こっそり様子を見てしまう」scene1〜5 の画像を gpt-image-1 で自動生成

■ 女性キャラクター復帰・第2弾（平日編）
  ㊵（休日）に続く平日ルーティン。scene1はスマホではなくお弁当から開始し
  サムネイル多様化を継続。服装は㊵と別色のオフィス系。CTAは軽く1回のみ。

出力先: C:\\Users\\ys734\\Desktop\\pet41_images\\

使い方:
  python generate_images_pet41.py
  python generate_images_pet41.py 1 3     # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet41_images")

# 顔・髪型は継続性のため維持。服装はオフィス系だが㊵とは別色（従来のベージュでもテラコッタでもない）
WOMAN = (
    "Japanese woman in her early 30s, youthful and stylish appearance, "
    "black shoulder-length straight hair slightly tucked behind one ear, "
    "oval face, natural makeup, wearing a fitted dusty blue knit top "
    "under a soft gray blazer, smart casual office look"
)

PROMPTS = [
    # scene1: お弁当箱を開ける手元、猫の形のふりかけご飯（新しい小道具）
    f"Close-up of hands opening a Japanese bento box at an office desk, "
    "revealing rice decorated with a cute cat-shaped furikake design, "
    "warm office lunch break lighting. Vertical 9:16 portrait.",

    # scene2: 書類をめくる手を止め、少し遠い目をする
    f"{WOMAN}, sitting at office desk, pausing while flipping through "
    "documents, a soft distant thoughtful expression, soft office "
    "lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 控えめにスマホを取り出す（手元中心）
    f"{WOMAN}, sitting at office desk during lunch break, discreetly "
    "taking out her smartphone, hands and lower face in frame rather "
    "than a direct facial close-up, soft office lighting. Vertical 9:16 portrait.",

    # scene4: ペットカメラ映像・猫が伸びをする
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat stretching luxuriously with a content expression, "
    "warm afternoon light in a quiet Japanese apartment. Vertical 9:16 portrait.",

    # scene5: 微笑みながら席を立ち仕事に戻る
    f"{WOMAN}, standing up from her office desk with a warm gentle "
    "smile, returning to work with renewed energy, soft office "
    "lighting. No text. Full upper body in frame. Vertical 9:16 portrait.",
]

STYLE = "Photorealistic, cinematic, Japanese office setting, no text or watermarks."


def main():
    total = len(PROMPTS)
    targets = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, total + 1))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY が .env に設定されていません")
        return

    client = OpenAI(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("gpt-image-1 画像生成 — 動画㊶「お昼休み、こっそり様子を見てしまう」")
    print(f"※女性キャラクター復帰・第2弾（平日編、{total}シーン、CTA軽く1回のみ）")
    print(f"対象シーン: {targets}")
    print("=" * 50)

    for i, prompt in enumerate(PROMPTS, 1):
        if i not in targets:
            continue
        out = OUTPUT_DIR / f"scene{i}.png"
        print(f"\n[scene{i}/{total}] 生成中...")
        print(f"  {prompt[:60]}...")

        try:
            resp = client.images.generate(
                model="gpt-image-1",
                prompt=f"{prompt} {STYLE}",
                size="1024x1536",
                quality="high",
                n=1,
            )
            img_data = base64.b64decode(resp.data[0].b64_json)
            out.write_bytes(img_data)
            print(f"  ✅ 保存: {out.name}")

        except Exception as e:
            print(f"  ❌ エラー: {e}")

        if i < total:
            time.sleep(3)

    print(f"\n{'='*50}")
    print(f"✅ 完成! {OUTPUT_DIR}")
    print("次のステップ: 各画像をGrokで動画化してください")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
