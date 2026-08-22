"""
動画⑯「短冊に願い事を書いたら、うちの子が見ていた」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet16_images\\

使い方:
  python generate_images_pet16.py
  python generate_images_pet16.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet16_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（短冊に願い事を書く女性と見つめる猫）
    f"{WOMAN}, writing a wish on a colorful Tanabata paper strip "
    "(tanzaku) at a low table, a tabby cat sitting beside her watching "
    "intently, small bamboo branch with decorations nearby, warm "
    "evening light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene2: 筆を持ちながら考え込む
    f"{WOMAN}, holding a writing brush over a blank tanzaku paper strip, "
    "thoughtful pausing expression, deciding what to write, soft warm "
    "indoor lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 短冊に文字を書く手元
    f"{WOMAN}'s hand writing Japanese characters on a tanzaku paper "
    "strip with a brush pen, close-up of the writing motion, warm soft "
    "lighting, cozy home atmosphere. Vertical 9:16 portrait.",

    # scene4: ふと不安げな表情
    f"{WOMAN}, pausing while looking at the tanzaku she just wrote, "
    "a subtly worried and thoughtful expression crossing her face, "
    "soft evening light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・短冊の下でくつろぐ猫
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat relaxing peacefully beneath a small bamboo branch "
    "decorated with colorful Tanabata paper strips, cozy Japanese "
    "living room at night. Vertical 9:16 portrait.",

    # scene6: 短冊を見上げるように眠る愛らしい姿
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sleeping curled up directly under hanging Tanabata "
    "paper strips, peaceful and adorable, dim warm night lighting. "
    "Vertical 9:16 portrait.",

    # scene7: CTA（七夕飾りの前で一緒にくつろぐ）
    f"{WOMAN}, sitting on the floor beside a small Tanabata bamboo "
    "decoration with colorful paper strips, tabby cat curled up "
    "affectionately beside her, warm contented smile, cozy Japanese "
    "living room, soft evening light. No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑯「短冊に願い事を書いたら、うちの子が見ていた」")
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
