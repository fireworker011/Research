"""
動画⑬「10年飼って、初めて知った」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet13_images\\

使い方:
  python generate_images_pet13.py
  python generate_images_pet13.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet13_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（ペットカメラ映像・猫が玄関前で待っている）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting perfectly still in front of an apartment entrance door, "
    "facing the door, waiting patiently alone. Quiet and slightly melancholic "
    "atmosphere. Vertical 9:16 portrait.",

    # scene2: 女性と猫が一緒にくつろぐ日常
    f"{WOMAN}, sitting on sofa at home with a tabby cat curled up beside her, "
    "relaxed and comfortable everyday scene, warm Japanese living room, "
    "soft evening light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 女性がオフィスで仕事中（猫のことは頭にない）
    f"{WOMAN}, focused on work at office desk, typing on keyboard, "
    "confident and concentrated expression, no particular worry, "
    "soft office lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene4: ペットカメラ映像・玄関前でうずくまる猫のアップ
    "Pet camera footage style, slightly grainy security camera look. "
    "Close-up of a tabby cat huddled at the base of an apartment entrance door, "
    "nose almost touching the door, ears slightly drooped, "
    "quietly waiting. Emotional and tender atmosphere. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・ずっと同じ場所にいる
    "Pet camera footage style, slightly grainy security camera look. "
    "Wide shot of Japanese apartment entrance, tabby cat sitting in the same "
    "spot by the door for a long time, unchanged position, loyal and patient. "
    "Dim indoor lighting. Vertical 9:16 portrait.",

    # scene6: 女性が目を潤ませてスマホを見つめる
    f"{WOMAN}, sitting at office desk, staring at smartphone screen with "
    "glistening tearful eyes, deeply moved and surprised expression, "
    "hand covering mouth slightly. Soft office lighting. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene7: CTA（帰宅・玄関で猫と目が合う感動シーン）
    f"{WOMAN}, opening the front door of a Japanese apartment, "
    "tabby cat sitting right there looking up at her, eyes meeting, "
    "deeply emotional homecoming moment, warm entrance lighting. "
    "No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑬「10年飼って、初めて知った」")
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
