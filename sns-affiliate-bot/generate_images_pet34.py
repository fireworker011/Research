"""
動画㉞「今日の寝相、こうだった」scene1〜5 の画像を gpt-image-1 で自動生成

■ テンプレート脱却の実験動画（2026/07/26 構造改善ルール適用）
  従来の型を意図的にすべて外している:
    - 7シーン固定 → 5シーン
    - 女性が主役 → 猫のみ・人物なし
    - ペットカメラ映像風 → 普通の温かい室内撮影
    - 違和感→発見→感動 → ただ可愛い・クスッと笑える
    - 商品CTA＋#PR → CTAなし・完全非商業

出力先: C:\\Users\\ys734\\Desktop\\pet34_images\\

使い方:
  python generate_images_pet34.py
  python generate_images_pet34.py 1 3     # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet34_images")

# この動画は人物を登場させない（映像世界の固定を崩すため WOMAN は未使用）

PROMPTS = [
    # scene1: 仰向けで大の字に寝ている猫
    "Tabby cat sleeping on its back with all four legs sprawled out in "
    "a completely relaxed spread-eagle pose on a soft rug, belly up, "
    "utterly carefree, warm afternoon light in a cozy Japanese living "
    "room. Vertical 9:16 portrait.",

    # scene2: 小さな箱に無理やり詰まって寝ている猫
    "Tabby cat squeezed into a cardboard box that is clearly too small "
    "for it, body overflowing the edges, sleeping soundly despite the "
    "tight fit, comically content, warm indoor light. Vertical 9:16 portrait.",

    # scene3: 椅子から半分ずり落ちた体勢で寝ている猫
    "Tabby cat asleep on a wooden chair with its upper body sliding off "
    "the edge, head hanging down, still fast asleep and unbothered, "
    "soft natural light in a Japanese home. Vertical 9:16 portrait.",

    # scene4: ありえない角度で爆睡している猫
    "Tabby cat sleeping in an absurd twisted position, body curled at "
    "an impossible angle with one paw over its face, deeply asleep, "
    "humorous and endearing, warm cozy room lighting. Vertical 9:16 portrait.",

    # scene5: 気持ちよさそうに伸びをする猫
    "Tabby cat waking up and stretching luxuriously with front paws "
    "extended forward and back arched, blissful expression, warm golden "
    "afternoon light streaming through a window. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㉞「今日の寝相、こうだった」")
    print(f"※テンプレート脱却の実験動画（{total}シーン・人物なし・CTAなし）")
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
