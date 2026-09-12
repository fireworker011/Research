"""
動画㉔「留守番中、猫の行動の7割は飼い主が知らない」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet24_images\\

使い方:
  python generate_images_pet24.py
  python generate_images_pet24.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet24_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（統計を見て驚く表情アップ）
    f"{WOMAN}, medium close-up shot focused on her face, looking at "
    "smartphone screen with a surprised expression, eyebrows raised, "
    "reacting to something unexpected, soft indoor lighting. "
    "Vertical 9:16 portrait.",

    # scene2: スマホで記事を読みながら考え込む
    f"{WOMAN}, sitting on sofa at home, reading an article on her "
    "smartphone with a thoughtful concerned expression, soft evening "
    "light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 自信なさげに猫との写真を眺める
    f"{WOMAN}, sitting on sofa at home, looking at a photo of herself "
    "with her cat on her smartphone, uncertain reflective expression, "
    "soft evening light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene4: オフィスでふとスマホを取り出す
    f"{WOMAN}, sitting at office desk, casually picking up her "
    "smartphone with a curious expression, soft office lighting. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫が意外な行動をしている
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat doing an unexpected quirky behavior alone at home, such "
    "as balancing on the edge of a shelf, surprising and unfamiliar "
    "action. Vertical 9:16 portrait.",

    # scene6: 驚きと愛おしさの混じった表情でスマホを見つめる
    f"{WOMAN}, sitting at office desk, looking at smartphone screen "
    "with an expression of surprised delight and warm affection, "
    "soft office lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene7: CTA（女性と猫が一緒にくつろぐ温かいラストシーン）
    f"{WOMAN}, sitting on sofa at home, tabby cat curled up affectionately "
    "beside her, warm contented smile, cozy Japanese living room, soft "
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
    print("gpt-image-1 画像生成 — 動画㉔「留守番中、猫の行動の7割は飼い主が知らない」")
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
