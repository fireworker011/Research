"""
動画③「帰れない夜だった」scene1〜6 の画像を DALL-E 3 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet3_images\\
  - scene1.png 〜 scene6.png

使い方:
  python generate_images_pet3.py
"""

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── 設定 ──────────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet3_images")

PROMPTS = [
    # scene1: 夜の会社・残業（顔をランプで照らす）
    "Japanese office at night, late overtime. Japanese woman in her 30s "
    "sitting at a desk, face clearly lit by warm desk lamp light, "
    "exhausted and blank expression. Dark background, dramatic low-key lighting "
    "with lamp illuminating her face. Cinematic. Vertical 9:16 portrait.",

    # scene2: スマホの時刻「23:14」
    "Close-up of a smartphone screen showing 23:14 at night, "
    "held by a woman's hands. Blurred dark office background. "
    "Cinematic, emotional, soft screen glow. Vertical 9:16 portrait.",

    # scene3: カメラアプリを開く（スマホ背面・女性の表情重視）
    "Japanese woman at office desk at night, opening a pet camera app "
    "on her phone with a worried expression, soft screen glow "
    "illuminating her face. The phone is held facing away from camera, "
    "showing the back of the phone. Only the woman's worried face is visible, "
    "not the phone screen content. Night, dark background. Vertical 9:16.",

    # scene4: 猫がドアの前で待っている
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat curled up sleeping directly in front of an apartment "
    "entrance door, waiting alone. Warm dim indoor light. Vertical 9:16 portrait.",

    # scene5: マイクボタンを押す（猫・スマホ正面）
    "Close-up of smartphone screen from the front, screen facing camera. "
    "On screen: a pet camera app showing a tabby cat, NOT a dog. "
    "A woman's finger pressing a microphone button at the bottom of the screen. "
    "Soft blue screen glow, phone screen fully visible. Vertical 9:16 portrait.",

    # scene6: 猫がカメラに近づいてくる
    "Tabby cat perking up its ears and slowly walking toward "
    "the camera, curious and alert. Warm indoor lighting, "
    "cozy Japanese apartment. Eye-level shot. Vertical 9:16 portrait.",

    # scene7: CTAカード（帰宅・再会・温かい締め）
    "Japanese woman arriving home late at night, kneeling down as "
    "a tabby cat runs toward her, warm hallway light. "
    "Emotional reunion, soft warm golden lighting, cinematic. "
    "No text. Vertical 9:16 portrait.",
]
# ─────────────────────────────────────────────────────────────────────────────

STYLE = "Photorealistic, cinematic, Japanese setting, no text or watermarks."


def main():
    import sys
    # python generate_images_pet3.py 1 3 5  → 指定シーンのみ再生成
    targets = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, 8))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY が .env に設定されていません")
        return

    client = OpenAI(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print(f"gpt-image-1 画像生成 — scene{targets}")
    print("=" * 50)

    for i, prompt in enumerate(PROMPTS, 1):
        if i not in targets:
            continue
        out = OUTPUT_DIR / f"scene{i}.png"
        print(f"\n[scene{i}/6] 生成中...")
        print(f"  {prompt[:60]}...")

        try:
            resp = client.images.generate(
                model="gpt-image-1",
                prompt=f"{prompt} {STYLE}",
                size="1024x1536",   # 縦型（2:3）
                quality="high",
                n=1,
            )
            import base64
            img_data = base64.b64decode(resp.data[0].b64_json)
            out.write_bytes(img_data)
            print(f"  ✅ 保存: {out.name}")

        except Exception as e:
            print(f"  ❌ エラー: {e}")

        if i < len(PROMPTS):
            time.sleep(3)   # レート制限対策

    print(f"\n{'='*50}")
    print(f"✅ 完成! {OUTPUT_DIR}")
    print("次のステップ: 各画像をGrokで5秒動画化してください")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
