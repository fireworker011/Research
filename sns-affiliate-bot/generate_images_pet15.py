"""
動画⑮「最後に顔を見たのは、何日前だっけ」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet15_images\\

使い方:
  python generate_images_pet15.py
  python generate_images_pet15.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet15_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（疲れた様子でふと考え込む）
    f"{WOMAN}, sitting on sofa at home looking exhausted, pausing with a "
    "distant thoughtful expression, dim evening lighting, quiet "
    "contemplative mood. Full upper body in frame. Vertical 9:16 portrait.",

    # scene2: 深夜に帰宅、疲れきった様子
    f"{WOMAN}, arriving home late at night, taking off her coat by the "
    "entrance, visibly exhausted expression, dim entrance lighting. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 慌ただしく身支度して玄関を出る
    f"{WOMAN}, hurriedly putting on her coat and shoes at the entrance "
    "in the morning, rushed movements, checking her watch, morning "
    "light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene4: 立ち止まり、罪悪感のある表情
    f"{WOMAN}, standing still at the entrance, pausing with a guilty "
    "and reflective expression, hand resting on the door, soft "
    "morning light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫がこちらを見つめている
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting still, looking directly toward the camera with "
    "calm attentive eyes, quiet Japanese apartment. Vertical 9:16 portrait.",

    # scene6: 目を潤ませながらスマホを見つめる
    f"{WOMAN}, sitting at office desk, looking at smartphone screen with "
    "glistening tearful eyes, soft emotional smile, deeply touched "
    "expression. Soft office lighting. Full upper body in frame. "
    "Vertical 9:16 portrait.",

    # scene7: CTA（帰宅、猫を抱きしめる温かいラストシーン）
    f"{WOMAN}, kneeling at home embracing a tabby cat warmly, tender "
    "and heartfelt expression, cozy Japanese living room, warm evening "
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
    print("gpt-image-1 画像生成 — 動画⑮「最後に顔を見たのは、何日前だっけ」")
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
