"""
動画㊵「休日は、いつもより長く一緒にいられる」scene1〜6 の画像を gpt-image-1 で自動生成

■ 女性キャラクター復帰・第1弾（2026/07/28 構造改善ルールを継承）
  これまでの「違和感→カメラ確認→発見→感動」型は使わず、
  素朴な「一緒に過ごす」スライスオブライフ構成に変更。
  服装・部屋も従来と変える（オフィス服→休日カジュアル、ソファ→畳の部屋）。
  CTAなし（復帰1本目は非商業で様子見）。

出力先: C:\\Users\\ys734\\Desktop\\pet40_images\\

使い方:
  python generate_images_pet40.py
  python generate_images_pet40.py 1 3     # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet40_images")

# 顔・髪型は継続性のため維持。服装は休日カジュアルに変更（従来のオフィス系タートルネックではない）
WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a soft cream knit cardigan over a white t-shirt and "
    "relaxed loungewear pants, casual weekend look"
)

PROMPTS = [
    # scene1: 休日カジュアル姿の女性と猫が朝の光の中でくつろぐ
    f"{WOMAN}, sitting on a sunlit tatami floor in the morning, tabby "
    "cat curled up beside her, relaxed peaceful weekend morning "
    "atmosphere, warm soft light through the window. Full upper body "
    "in frame. Vertical 9:16 portrait.",

    # scene2: 女性と猫がのんびり朝食をとる様子
    f"{WOMAN}, sitting at a low table having a simple breakfast, tabby "
    "cat sitting calmly nearby watching, cozy unhurried morning mood, "
    "warm natural light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 二人が畳の日向でくつろぐ
    f"{WOMAN}, lying casually on a sunlit tatami floor with a tabby cat "
    "curled up against her side, both basking in warm sunlight, "
    "relaxed lazy weekend mood. Full upper body in frame. Vertical 9:16 portrait.",

    # scene4: 女性と猫が並んで眠ってしまっている
    f"{WOMAN}, dozing off peacefully on the tatami floor in the warm "
    "sunlight, tabby cat asleep curled up right beside her, both "
    "completely at ease, soft afternoon light. Full upper body in "
    "frame. Vertical 9:16 portrait.",

    # scene5: 女性が目を覚まし隣の猫を見つける優しい瞬間
    f"{WOMAN}, slowly opening her eyes and waking up, noticing the "
    "tabby cat still sleeping peacefully beside her, tender soft "
    "smile forming, warm afternoon light. Full upper body in frame. "
    "Vertical 9:16 portrait.",

    # scene6: 二人が笑顔（猫は伸び）で過ごす温かいラストカット
    f"{WOMAN}, sitting up and smiling warmly, tabby cat stretching "
    "beside her waking up too, cozy contented weekend atmosphere, "
    "warm soft light. No text. Full upper body in frame. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㊵「休日は、いつもより長く一緒にいられる」")
    print(f"※女性キャラクター復帰・第1弾（{total}シーン・CTAなし・従来の発見型構成ではない）")
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
