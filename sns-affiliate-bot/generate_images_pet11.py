"""
動画⑪「もし倒れていたら、気づけない」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet11_images\\

使い方:
  python generate_images_pet11.py
  python generate_images_pet11.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet11_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（ペットカメラ映像・猫が一人で静かにしている）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting alone and very still in a quiet, dimly lit Japanese "
    "apartment, calm but slightly unsettling atmosphere, vulnerable solitary "
    "mood. Vertical 9:16 portrait.",

    # scene2: 女性がオフィスで物思いにふける
    f"{WOMAN}, sitting at office desk, lost in thought, gazing into the "
    "distance with a subtly anxious expression, pen resting in hand, "
    "soft office lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 猫が普段通りに見える（隠してしまう、という示唆）
    "Tabby cat sitting calmly on a windowsill at home, looking outwardly "
    "healthy and composed, soft natural daylight, serene domestic "
    "atmosphere. Vertical 9:16 portrait.",

    # scene4: 女性がスマホを取り出す・不安そうに
    f"{WOMAN}, sitting at office desk, reaching for her smartphone with "
    "a worried expression, slightly tense posture, soft office lighting. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫が元気に歩いている
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat walking energetically across a Japanese apartment living "
    "room, alert and healthy, normal everyday movement. Vertical 9:16 portrait.",

    # scene6: 女性が安堵の表情でスマホを見る
    f"{WOMAN}, sitting at office desk, looking at smartphone screen with "
    "a relieved soft smile, shoulders relaxing, gentle expression of "
    "relief. Soft office lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene7: CTA（女性と猫が一緒にくつろぐ温かいシーン）
    f"{WOMAN}, sitting on sofa at home, cat curled up peacefully beside "
    "her, warm gentle smile, cozy Japanese living room, soft evening "
    "light. No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑪「もし倒れていたら、気づけない」")
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
