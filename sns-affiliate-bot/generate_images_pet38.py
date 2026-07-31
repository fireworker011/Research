"""
動画㊳「うちの子、実は掃除機が苦手です」scene1〜5 の画像を gpt-image-1 で自動生成

■ テンプレート脱却の実験動画・第5弾（ストック用・8/2以降に投稿予定）
  弱点・苦手あるある集・共感型。猫のみ主演・CTAなし・商品訴求なし。

出力先: C:\\Users\\ys734\\Desktop\\pet38_images\\

使い方:
  python generate_images_pet38.py
  python generate_images_pet38.py 1 3     # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet38_images")

# この動画も人物を登場させない（㉞〜㊲に続き映像世界を固定しない）

PROMPTS = [
    # scene1: 掃除機を警戒するように身構える
    "Tabby cat crouching low with ears back and eyes wide, wary "
    "defensive posture, facing a vacuum cleaner sitting a few feet "
    "away on a Japanese living room floor, tense alert atmosphere, "
    "warm indoor light. Vertical 9:16 portrait.",

    # scene2: 体重計の上で動かなくなっている
    "Tabby cat standing completely frozen and stiff on a bathroom "
    "scale, wide-eyed motionless expression, comic tension, soft "
    "bathroom lighting. Vertical 9:16 portrait.",

    # scene3: 耳を伏せて隠れようとする様子
    "Tabby cat with ears flattened back, partially hiding behind a "
    "sofa cushion, wary cautious expression, warm living room "
    "lighting. Vertical 9:16 portrait.",

    # scene4: ドライヤーの音に驚いて逃げる仕草
    "Tabby cat mid-flight, startled and fleeing with an alarmed "
    "expression, ears back, away from a hair dryer on a bathroom "
    "counter, comic motion, warm indoor light. Vertical 9:16 portrait.",

    # scene5: リラックスして丸くなっている温かいラストカット
    "Tabby cat curled up peacefully and contentedly on a soft cushion, "
    "completely relaxed and at ease, warm cozy Japanese living room "
    "light. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㊳「うちの子、実は掃除機が苦手です」")
    print(f"※テンプレート脱却の実験動画・第5弾（{total}シーン・人物なし・CTAなし）")
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
