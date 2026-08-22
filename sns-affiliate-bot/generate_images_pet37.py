"""
動画㊲「うちの子クイズ、正解できますか」scene1〜6 の画像を gpt-image-1 で自動生成

■ テンプレート脱却の実験動画・第4弾（ストック用・8/2以降に投稿予定）
  視聴者参加型クイズ形式。一時停止を挟む構成でコメント・視聴維持率向上を狙う。
  猫のみ主演・CTAなし。

出力先: C:\\Users\\ys734\\Desktop\\pet37_images\\

使い方:
  python generate_images_pet37.py
  python generate_images_pet37.py 1 3     # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet37_images")

# この動画も人物を登場させない（㉞㉟㊱に続き映像世界を固定しない）

PROMPTS = [
    # scene1: 問題提示（猫がこちらを見ている構図）
    "Tabby cat sitting between a cardboard box and a soft folded "
    "blanket on the floor, looking directly at the camera with an "
    "inquisitive expression, as if posing a question, warm indoor "
    "light in a Japanese living room. Vertical 9:16 portrait.",

    # scene2: 一時停止ポイント（迷っているような仕草）
    "Tabby cat glancing back and forth between a cardboard box and a "
    "soft folded blanket, head tilting curiously as if deciding, "
    "warm afternoon light. Vertical 9:16 portrait.",

    # scene3: 正解（毛布を選ぶ意外な行動）
    "Tabby cat settling comfortably into a soft folded blanket "
    "instead of the nearby cardboard box, content relaxed expression, "
    "warm cozy Japanese living room light. Vertical 9:16 portrait.",

    # scene4: 次の問題（別のシチュエーション、おもちゃ2択）
    "Tabby cat sitting between two different cat toys, a feather "
    "wand and a small ball, looking directly at the camera with a "
    "curious expression, warm indoor light. Vertical 9:16 portrait.",

    # scene5: 正解（予想と違う選択）
    "Tabby cat ignoring both toys and instead playing with a "
    "crumpled piece of paper nearby, amused surprising behavior, "
    "warm afternoon light. Vertical 9:16 portrait.",

    # scene6: ラストカット（満足げにこちらを見る）
    "Tabby cat sitting proudly and contentedly, looking directly at "
    "the camera with a satisfied expression, warm cozy Japanese "
    "living room light. Vertical 9:16 portrait.",
]

STYLE = "Photorealistic, cinematic, Japanese home setting, no text or watermarks."


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
    print("gpt-image-1 画像生成 — 動画㊲「うちの子クイズ、正解できますか」")
    print(f"※テンプレート脱却の実験動画・第4弾（{total}シーン・人物なし・CTAなし）")
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
