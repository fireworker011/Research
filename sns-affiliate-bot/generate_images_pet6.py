"""
動画⑥「心配で、泣いてしまった」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet6_images\\

使い方:
  python generate_images_pet6.py
  python generate_images_pet6.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet6_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup"
)

PROMPTS = [
    # scene1: 泣きながらスマホを見る（フック）
    f"{WOMAN}, crying softly while looking at smartphone screen, "
    "dark room at night, soft blue screen glow on her tear-stained face, "
    "emotional and cinematic. Full upper body in frame. Vertical 9:16 portrait.",

    # scene2: 誰もいない部屋（孤独感）
    "Empty Japanese apartment living room, warm dim indoor light, "
    "cat toys scattered on the floor, a small cat bed in the corner, "
    "quiet and lonely atmosphere. No people, no cat. Cinematic. Vertical 9:16 portrait.",

    # scene3: 仕事中に気になってスマホを見る
    f"{WOMAN} wearing dark navy blazer, sitting at office desk, "
    "distracted expression staring at smartphone instead of working, "
    "soft office lighting, worried look. Upper body in frame. Vertical 9:16 portrait.",

    # scene4: カメラ映像（猫が小さく丸まって動かない）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat curled up very small in the corner of an empty room, "
    "completely still and alone, dim indoor light, sad and lonely feeling. "
    "Vertical 9:16 portrait.",

    # scene5: 女性の目に涙が溢れる（クローズアップ）
    f"Extreme close-up of {WOMAN}'s eyes filling with tears, "
    "soft blue smartphone screen glow reflected in her glistening eyes, "
    "emotional, cinematic, dark background. Vertical 9:16 portrait.",

    # scene6: 猫が顔を上げてカメラを見る（転換）
    "Pet camera footage style, slightly grainy. Tabby cat lifting its head "
    "and looking directly at the camera with alert perked-up ears, "
    "as if hearing a familiar voice. Warm indoor light. Vertical 9:16 portrait.",

    # scene7: 女性が涙ながらに微笑む（CTA）
    f"{WOMAN}, smiling through tears while looking at smartphone, "
    "warm golden glow on her face, emotional and deeply relieved expression, "
    "dark background, cinematic. No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑥「心配で、泣いてしまった」")
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
