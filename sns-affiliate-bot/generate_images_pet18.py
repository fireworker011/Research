"""
動画⑱「留守番が得意な猫なんて、いない」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet18_images\\

使い方:
  python generate_images_pet18.py
  python generate_images_pet18.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet18_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（出かける準備をしながら猫に話しかける）
    f"{WOMAN}, kneeling at the entrance putting on her shoes, talking "
    "gently to a tabby cat sitting nearby, warm reassuring expression, "
    "morning light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene2: 自信ありげに猫を撫でて玄関を出る
    f"{WOMAN}, petting a tabby cat's head confidently at the entrance "
    "before leaving, calm assured smile, morning light. Full upper "
    "body in frame. Vertical 9:16 portrait.",

    # scene3: オフィスで落ち着いて仕事をしている
    f"{WOMAN}, working calmly and confidently at office desk, focused "
    "and relaxed expression, soft office lighting. Full upper body "
    "in frame. Vertical 9:16 portrait.",

    # scene4: ふと思い立ってスマホを取り出す
    f"{WOMAN}, pausing at office desk and casually picking up her "
    "smartphone, curious relaxed expression, soft office lighting. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫が玄関前でじっと座ったまま
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting motionless in front of an apartment entrance "
    "door, unchanged position, quiet and still, subdued atmosphere. "
    "Vertical 9:16 portrait.",

    # scene6: 驚きと申し訳なさの混じった表情
    f"{WOMAN}, sitting at office desk, looking at smartphone screen "
    "with a surprised and guilty expression, hand near her mouth, "
    "soft office lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene7: CTA（帰宅し猫を優しく抱きしめる）
    f"{WOMAN}, kneeling at the entrance of her home, gently embracing "
    "a tabby cat with tenderness, warm heartfelt expression, soft "
    "evening light. No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑱「留守番が得意な猫なんて、いない」")
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
