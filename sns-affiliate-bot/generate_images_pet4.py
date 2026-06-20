"""
動画④「泣いてたら、気づかれた」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet4_images\\
  - scene1.png 〜 scene7.png

使い方:
  python generate_images_pet4.py
  python generate_images_pet4.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet4_images")

PROMPTS = [
    # scene1: 深夜、一人で泣いている女性（フック）
    "Japanese woman in her 30s sitting alone at home late at night, "
    "crying quietly, face slightly wet with tears, soft dim lamp light, "
    "dark background, emotional and cinematic. Vertical 9:16 portrait.",

    # scene2: 上半身全体・ティッシュ（理由は言えない）
    "Japanese woman in her 30s sitting alone on the floor in a dark room, "
    "upper body fully visible from head to waist, head slightly bowed down, "
    "used tissues beside her, soft warm lamp light from the side, "
    "dark and quiet atmosphere, emotional. Full upper body in frame, "
    "no cropping. Cinematic. Vertical 9:16 portrait.",

    # scene3: スマホを開く（涙の顔にスクリーンの光）
    "Japanese woman holding smartphone in dark room at night, "
    "soft blue screen glow illuminating her tear-stained face, "
    "tired and emotional expression, looking at phone. Cinematic. Vertical 9:16 portrait.",

    # scene4: ペットカメラ映像（猫がカメラ前に座っている）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting directly in front of the camera, staring straight "
    "into the lens, alert and completely still. Dim warm indoor lighting. "
    "Vertical 9:16 portrait.",

    # scene5: 猫のアップ（じっと見ている）
    "Extreme close-up of a tabby cat face staring directly at camera "
    "with calm, attentive, almost knowing expression. Pet camera footage look, "
    "warm indoor light, slightly grainy. Vertical 9:16 portrait.",

    # scene6: スマホ画面（猫＋マイクボタン）
    "Close-up of smartphone screen from the front, screen facing camera. "
    "On screen: a pet camera app showing a tabby cat looking toward camera. "
    "A woman's finger about to press the microphone button at bottom of screen. "
    "Soft blue screen glow, phone screen fully visible. Vertical 9:16 portrait.",

    # scene7: CTA（女性が微笑む・涙が乾いていく）
    "Japanese woman sitting in dark room, softly smiling at her phone, "
    "warm glow on her face, tears drying, hopeful and comforted expression. "
    "Emotional and cinematic, no text. Vertical 9:16 portrait.",
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
    print(f"gpt-image-1 画像生成 — 動画④「泣いてたら、気づかれた」")
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
