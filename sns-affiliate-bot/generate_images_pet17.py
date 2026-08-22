"""
動画⑰「深夜2時、通知が鳴った」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet17_images\\

使い方:
  python generate_images_pet17.py
  python generate_images_pet17.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet17_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（暗いホテルの部屋でスマホが光る）
    "Dark hotel room at night, smartphone screen glowing on a nightstand "
    "beside a bed, notification light illuminating the dim room, "
    "tense quiet atmosphere. Vertical 9:16 portrait.",

    # scene2: 出張中のホテルで疲れて横になる
    f"{WOMAN}, lying in a hotel bed at night wearing casual home clothes, "
    "tired expression, dim room lighting, business trip atmosphere. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 不安げにスマホへ手を伸ばす
    f"{WOMAN}, sitting up in bed at night, reaching for her smartphone "
    "with a slightly anxious expression, dim hotel room lighting. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene4: 画面を見つめて息をのむ
    f"{WOMAN}, holding smartphone close to her face at night, eyes "
    "widening with tense anticipation, holding her breath, dim "
    "lighting from the screen. Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫がレンズの真正面にお座り
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting perfectly upright directly in front of the "
    "camera lens, facing forward, calm and composed posture. "
    "Vertical 9:16 portrait.",

    # scene6: 猫がレンズをじっと見つめるアップ
    "Pet camera footage style, slightly grainy security camera look. "
    "Close-up of a tabby cat's face staring directly into the camera "
    "lens with calm curious eyes, quiet nighttime room. Vertical 9:16 portrait.",

    # scene7: CTA（スマホ越しに目を潤ませて微笑む）
    f"{WOMAN}, looking at smartphone screen in the dim hotel room at "
    "night, eyes glistening with a warm emotional smile, softly moved "
    "expression. No text. Full upper body in frame. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑰「深夜2時、通知が鳴った」")
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
    print("次のステップ: 各画像をGrokで動画化してください")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
