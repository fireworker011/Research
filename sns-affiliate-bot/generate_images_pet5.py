"""
動画⑤「行かないで、って顔をしてた」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet5_images\\
  - scene1.png 〜 scene7.png

使い方:
  python generate_images_pet5.py
  python generate_images_pet5.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet5_images")

# 女性キャラクター固定設定（全シーン共通）
WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: 猫の上目遣い（フック・女性なし）
    "Close-up of tabby cat face looking up with big pleading round eyes, "
    "soft morning light, Japanese apartment entrance, heartwarming and emotional. "
    "Vertical 9:16 portrait.",

    # scene2: 朝の準備中の女性
    f"{WOMAN}, putting on a dark navy blazer over her turtleneck near the entrance, "
    "bright morning sunlight through window, cozy Japanese apartment interior. "
    "Full upper body clearly in frame, face and hair visible. Vertical 9:16 portrait.",

    # scene3: 玄関で靴を履く・猫が横に
    f"Japanese apartment entrance, {WOMAN} bending slightly to put on shoes, "
    "tabby cat sitting right beside her feet looking up with pleading eyes, "
    "warm morning indoor light. Both woman upper body and cat fully visible. "
    "Vertical 9:16 portrait.",

    # scene4: 猫がドア前でじっと見ている（女性なし）
    "Tabby cat sitting directly in front of apartment entrance door, "
    "staring up with big round eyes, gentle pleading expression, "
    "soft morning light. Full cat body in frame. Vertical 9:16 portrait.",

    # scene5: 会社の昼休みにスマホを開く
    f"{WOMAN} with dark navy blazer, sitting at office desk during lunch break, "
    "looking at smartphone with warm and slightly worried expression, "
    "soft office lighting. Face and hair clearly visible. Upper body in frame. "
    "Vertical 9:16 portrait.",

    # scene6: カメラに映る猫（待っている・女性なし）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat curled up sleeping directly in front of apartment entrance door, "
    "waiting alone. Warm dim indoor light. Vertical 9:16 portrait.",

    # scene7: CTA（帰宅・再会）
    f"{WOMAN} with dark navy blazer, arriving home in the evening, "
    "kneeling at apartment entrance, tabby cat running toward her with tail up, "
    "warm golden indoor light, emotional and heartwarming reunion. "
    "Face and hair clearly visible. Cinematic. No text. Vertical 9:16 portrait.",
]

STYLE = "Photorealistic, cinematic, Japanese setting, no text or watermarks."


def main():
    targets = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, 8))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY が .env に設定されていません")
        return

    client = OpenAI(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("gpt-image-1 画像生成 — 動画⑤「行かないで、って顔をしてた」")
    print(f"対象シーン: {targets}")
    print("=" * 50)

    for i, prompt in enumerate(PROMPTS, 1):
        if i not in targets:
            continue
        out = OUTPUT_DIR / f"scene{i}.png"
        print(f"\n[scene{i}/7] 生成中...")
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

        if i < len(PROMPTS):
            time.sleep(3)

    print(f"\n{'='*50}")
    print(f"✅ 完成! {OUTPUT_DIR}")
    print("次のステップ: 各画像をGrokで5秒動画化してください")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
