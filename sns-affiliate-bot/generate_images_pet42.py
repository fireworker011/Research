"""
動画㊷「新しいおもちゃ、3秒で飽きられました」scene1〜5 の画像を gpt-image-1 で自動生成

■ 猫のみ路線・確定方針適用（2026/08〜）
  ㊴「箱、届きました」（4,000達成）と同じ路線: 猫のみ主演・CTAなし。
  女性キャラクターは当面完全に封印。

出力先: C:\\Users\\ys734\\Desktop\\pet42_images\\

使い方:
  python generate_images_pet42.py
  python generate_images_pet42.py 1 3     # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet42_images")

# 人物は登場させない（確定方針: 女性キャラクター封印）

PROMPTS = [
    # scene1: 新しいおもちゃを前に猫が興味深そうに近づく
    "Tabby cat cautiously approaching a brand new colorful cat toy "
    "placed on a Japanese living room floor, curious sniffing "
    "posture, warm afternoon light. Vertical 9:16 portrait.",

    # scene2: 猫がおもちゃで楽しそうに遊んでいる
    "Tabby cat playfully batting and pouncing on a new cat toy, "
    "engaged excited motion, warm indoor light in a cozy Japanese "
    "living room. Vertical 9:16 portrait.",

    # scene3: 猫がふとおもちゃから目をそらす瞬間
    "Tabby cat pausing mid-play, head turning away from the toy with "
    "sudden distracted disinterest, comic timing, warm afternoon "
    "light. Vertical 9:16 portrait.",

    # scene4: 猫がおもちゃの入っていた箱や包み紙で遊び始める
    "Tabby cat completely absorbed in playing with a crumpled piece "
    "of wrapping paper and a small cardboard box, the abandoned new "
    "toy visible nearby untouched, warm cozy light. Vertical 9:16 portrait.",

    # scene5: おもちゃそっちのけで箱に夢中な猫、満足げな様子
    "Tabby cat contentedly sitting inside a small cardboard box, "
    "satisfied relaxed expression, the new toy still lying forgotten "
    "in the background, warm afternoon light. No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㊷「新しいおもちゃ、3秒で飽きられました」")
    print(f"※猫のみ路線（確定方針）（{total}シーン・人物なし・CTAなし）")
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
