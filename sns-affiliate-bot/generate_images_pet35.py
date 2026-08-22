"""
動画㉟「今日のイタズラ、証拠を残していった」scene1〜5 の画像を gpt-image-1 で自動生成

■ テンプレート脱却の実験動画・第2弾（2026/07/26 構造改善ルール継続）
  ㉞に続き: 猫のみ主演・CTAなし・「やれやれ」で終わるオチ（発見して感動、ではない）

出力先: C:\\Users\\ys734\\Desktop\\pet35_images\\

使い方:
  python generate_images_pet35.py
  python generate_images_pet35.py 1 3     # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet35_images")

# この動画も人物を登場させない（㉞に続き映像世界を固定しない）

PROMPTS = [
    # scene1: トイレットペーパーが部屋中に散らばっている現場
    "A trail of unrolled toilet paper scattered messily across a "
    "Japanese living room floor, shredded bits everywhere, comic crime "
    "scene atmosphere, no cat visible yet, warm afternoon light. "
    "Vertical 9:16 portrait.",

    # scene2: 倒れた観葉植物、土がこぼれている
    "A knocked-over potted plant on the floor of a Japanese living "
    "room, soil scattered around it, leaves bent, comic mess, warm "
    "afternoon light, no cat visible yet. Vertical 9:16 portrait.",

    # scene3: 段ボールの角がボロボロに引っかかれている
    "Close-up of a cardboard box corner completely shredded and torn "
    "up by claw marks, fibers sticking out messily, warm indoor "
    "light, no cat visible yet. Vertical 9:16 portrait.",

    # scene4: 猫が何食わぬ顔でくつろいでいる
    "Tabby cat lounging calmly on a sofa with an innocent nonchalant "
    "expression, completely relaxed as if nothing happened, warm "
    "cozy Japanese living room light. Vertical 9:16 portrait.",

    # scene5: 散らかった部屋の真ん中で満足げな猫
    "Tabby cat sitting proudly in the middle of a slightly messy "
    "Japanese living room with scattered toilet paper and a tipped "
    "plant in the background, content satisfied expression, warm "
    "afternoon light. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㉟「今日のイタズラ、証拠を残していった」")
    print(f"※テンプレート脱却の実験動画・第2弾（{total}シーン・人物なし・CTAなし）")
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
