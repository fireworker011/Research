"""
動画㊱「窓の外の観察日記」scene1〜5 の画像を gpt-image-1 で自動生成

■ テンプレート脱却の実験動画・第3弾（ストック用・8/2以降に投稿予定）
  猫のみ主演・CTAなし・時間帯ごとの定点観察スタイル（ドキュメンタリー風）

出力先: C:\\Users\\ys734\\Desktop\\pet36_images\\

使い方:
  python generate_images_pet36.py
  python generate_images_pet36.py 1 3     # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet36_images")

# この動画も人物を登場させない（㉞㉟に続き映像世界を固定しない）

PROMPTS = [
    # scene1: 朝、雨上がりの匂いを確認する
    "Tabby cat sitting on a windowsill in the early morning, nose "
    "twitching as it sniffs the air near a slightly open window, "
    "raindrops still visible on the glass outside, soft misty morning "
    "light. Vertical 9:16 portrait.",

    # scene2: 昼、通り過ぎる人を目で追う
    "Tabby cat sitting on a windowsill at midday, eyes tracking "
    "something moving outside the window, focused alert gaze, bright "
    "daylight streaming in, quiet Japanese apartment. Vertical 9:16 portrait.",

    # scene3: 夕方、夕焼けをぼんやり眺める
    "Tabby cat sitting on a windowsill in the evening, gazing "
    "quietly outside as warm orange sunset light bathes its fur, "
    "peaceful contemplative mood. Vertical 9:16 portrait.",

    # scene4: 夜、窓に映る自分と見つめ合う
    "Tabby cat sitting close to a dark window at night, its own "
    "faint reflection visible in the glass, curious still gaze, "
    "dim warm interior lighting. Vertical 9:16 portrait.",

    # scene5: 今日の観察、終了です
    "Tabby cat curled up comfortably on a windowsill cushion, eyes "
    "slowly closing, peaceful and settled, soft dim evening light. "
    "Vertical 9:16 portrait.",
]

STYLE = "Photorealistic, cinematic, Japanese home setting, no text or watermarks."


def main():
    total = len(PROMPTS)
    targets = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(1, total + 1))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY が .env に設定されていません")
        return

    client = OpenAI(api_key=api_key)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("gpt-image-1 画像生成 — 動画㊱「窓の外の観察日記」")
    print(f"※テンプレート脱却の実験動画・第3弾（{total}シーン・人物なし・CTAなし）")
    print(f"対象シーン: {targets}")
    print("=" * 50)

    for i, prompt in enumerate(PROMPTS, 1):
        if i not in targets:
            continue
        out = OUTPUT_DIR / f"scene{i}.png"
        print(f"\n[scene{i}/{total}] 生成中...")
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

        if i < total:
            time.sleep(3)

    print(f"\n{'='*50}")
    print(f"✅ 完成! {OUTPUT_DIR}")
    print("次のステップ: 各画像をGrokで動画化してください")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
