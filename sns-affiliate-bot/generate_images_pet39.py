"""
動画㊴「箱、届きました」scene1〜5 の画像を gpt-image-1 で自動生成

■ テンプレート脱却の実験動画・第6弾（ストック用・8/2以降に投稿予定）
  新しい段ボール箱への反応を定点観測（開封〜占領まで）。
  猫のみ主演・CTAなし・商品訴求なし。

出力先: C:\\Users\\ys734\\Desktop\\pet39_images\\

使い方:
  python generate_images_pet39.py
  python generate_images_pet39.py 1 3     # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet39_images")

# この動画も人物を登場させない（㉞〜㊳に続き映像世界を固定しない）

PROMPTS = [
    # scene1: リビングの床に置かれたばかりの段ボール箱
    "A plain cardboard delivery box freshly placed on the floor of a "
    "Japanese living room, no cat visible yet, soft afternoon light, "
    "quiet anticipatory atmosphere. Vertical 9:16 portrait.",

    # scene2: 猫が少し離れた場所から箱を警戒気味に観察
    "Tabby cat sitting a few feet away from a cardboard box, watching "
    "it intently with cautious curious eyes, low crouched alert "
    "posture, warm indoor light. Vertical 9:16 portrait.",

    # scene3: 猫が低い姿勢でゆっくり箱に近づく
    "Tabby cat slowly creeping toward a cardboard box in a low "
    "stalking posture, focused determined expression, warm afternoon "
    "light in a Japanese living room. Vertical 9:16 portrait.",

    # scene4: 猫が箱の匂いを嗅ぎ、中に足を踏み入れる
    "Tabby cat sniffing the edge of an open cardboard box, one paw "
    "stepping cautiously over the rim, curious careful motion, warm "
    "indoor light. Vertical 9:16 portrait.",

    # scene5: 猫が箱の中にすっぽり収まり満足げにくつろぐ
    "Tabby cat completely settled and curled up inside a cardboard "
    "box, content satisfied expression, perfectly fitting the space, "
    "warm cozy Japanese living room light. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㊴「箱、届きました」")
    print(f"※テンプレート脱却の実験動画・第6弾（{total}シーン・人物なし・CTAなし）")
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
