"""
動画㉕「今日も、一人でお留守番」scene1〜7 の画像を gpt-image-1 で自動生成

新フォーマット: 猫目線モノローグ（全編ほぼペットカメラ視点、最後のみ女性視点）

出力先: C:\\Users\\ys734\\Desktop\\pet25_images\\

使い方:
  python generate_images_pet25.py
  python generate_images_pet25.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet25_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（玄関のドアが閉まる瞬間、猫が見つめる）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting near the entrance, watching the front door as it "
    "closes, morning light filtering in briefly before the door shuts, "
    "quiet contemplative mood. Vertical 9:16 portrait.",

    # scene2: 静かな部屋に一人残される
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting alone in a now-quiet Japanese living room, "
    "stillness settling in, soft empty morning light. Vertical 9:16 portrait.",

    # scene3: 窓辺でぼんやり外を見ている
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting on a windowsill, gazing quietly out the window, "
    "soft afternoon light, calm solitary atmosphere. Vertical 9:16 portrait.",

    # scene4: カメラのランプに気づき顔を上げる
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat looking up attentively toward a small blinking light "
    "from a pet camera device, curious alert expression, dim indoor "
    "lighting. Vertical 9:16 portrait.",

    # scene5: 耳がぴくっと動き反応するクローズアップ
    "Pet camera footage style, slightly grainy security camera look. "
    "Close-up of a tabby cat's face, ears suddenly perking up and "
    "rotating forward attentively, eyes widening slightly, alert "
    "reaction to a sound. Vertical 9:16 portrait.",

    # scene6: しっぽがゆっくり揺れる
    "Pet camera footage style, slightly grainy security camera look. "
    "Close-up of a tabby cat's tail swaying slowly and gently, calm "
    "responsive motion, quiet Japanese apartment. Vertical 9:16 portrait.",

    # scene7: CTA（女性がスマホで猫に話しかけて微笑む）
    f"{WOMAN}, sitting at office desk, smiling warmly while speaking "
    "into her smartphone using a pet camera app, tender affectionate "
    "expression. No text. Full upper body in frame. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㉕「今日も、一人でお留守番」（猫目線）")
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
