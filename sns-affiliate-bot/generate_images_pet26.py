"""
動画㉖「休日、寝坊した朝に鳴った」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet26_images\\

使い方:
  python generate_images_pet26.py
  python generate_images_pet26.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet26_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（布団の中、スマホが震えて光る）
    "Close-up shot of a smartphone vibrating and glowing on a bedside "
    "table next to a futon, soft morning light filtering through "
    "curtains, quiet bedroom atmosphere. Vertical 9:16 portrait.",

    # scene2: 布団の中でまだぼんやりしている
    f"{WOMAN}, lying in bed under a soft blanket on a lazy weekend "
    "morning, eyes half open, sleepy relaxed expression, soft morning "
    "light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 眠そうに目をこすりながら寝返りを打つ
    f"{WOMAN}, lying in bed, rubbing her eyes drowsily while turning "
    "over, still mostly asleep, soft morning light. Full upper body "
    "in frame. Vertical 9:16 portrait.",

    # scene4: 枕元でスマホが震え続けるのに気づく
    f"{WOMAN}, lying in bed, glancing toward her smartphone vibrating "
    "repeatedly on the nightstand, faint awareness growing on her "
    "face, soft morning light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: 体を起こしスマホを手に取る、眠そうな表情
    f"{WOMAN}, sitting up slowly in bed, reaching for her smartphone "
    "with a still-sleepy but curious expression, soft morning light. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene6: ペットカメラ映像・猫がドアの前で鳴いている
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting in front of a door, mouth open as if meowing, "
    "slightly urgent posture, quiet Japanese apartment morning light. "
    "Vertical 9:16 portrait.",

    # scene7: CTA（安堵しながら布団から出て向かう温かいラストシーン）
    f"{WOMAN}, getting out of bed with a relieved warm smile, softly "
    "touched expression, morning light. No text. Full upper body in "
    "frame. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㉖「休日、寝坊した朝に鳴った」")
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
