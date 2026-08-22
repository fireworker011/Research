"""
動画⑲「猫が一人でいる時間、平均12時間」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet19_images\\

使い方:
  python generate_images_pet19.py
  python generate_images_pet19.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet19_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（統計を見て驚く表情アップ）
    f"{WOMAN}, looking at smartphone screen with a surprised expression, "
    "eyebrows raised, close-up on her face reacting to something "
    "unexpected, soft indoor lighting. Full upper body in frame. "
    "Vertical 9:16 portrait.",

    # scene2: スマホで何かを調べている真剣な表情
    f"{WOMAN}, sitting on sofa at home, scrolling smartphone with a "
    "focused serious expression, researching something intently, "
    "soft evening light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 部屋を見渡し罪悪感のある表情
    f"{WOMAN}, sitting on sofa at home, looking around the empty room "
    "with a guilty reflective expression, soft evening light. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene4: ペットカメラ映像・猫が静かな部屋に一人でいる
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting alone in a quiet empty Japanese living room, "
    "still and solitary, soft afternoon light through window. "
    "Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・ソファの上でじっと座る猫
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting motionless on a sofa, unchanged position, "
    "calm but isolated atmosphere, dim indoor lighting. Vertical 9:16 portrait.",

    # scene6: 切ない表情でスマホを見つめる
    f"{WOMAN}, sitting on sofa at home, looking at smartphone screen "
    "with a tender melancholic expression, softly moved, warm evening "
    "light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene7: CTA（帰宅し猫と触れ合う温かいラストシーン）
    f"{WOMAN}, sitting on the floor at home, tabby cat approaching and "
    "rubbing against her affectionately, warm joyful smile, cozy "
    "Japanese living room, soft evening light. No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑲「猫が一人でいる時間、平均12時間」")
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
