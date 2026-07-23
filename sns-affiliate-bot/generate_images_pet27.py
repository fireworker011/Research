"""
動画㉗「ごはんが、減ってなかった」scene1〜7 の画像を gpt-image-1 で自動生成

改善ルール適用: scene1は「女性がスマホを見る」構図を禁止し、
手つかずのごはん皿のクローズアップから始める新構図。

出力先: C:\\Users\\ys734\\Desktop\\pet27_images\\

使い方:
  python generate_images_pet27.py
  python generate_images_pet27.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet27_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（手つかずのごはん皿のクローズアップ・新構図）
    "Close-up shot of a cat food bowl on a kitchen floor, food untouched "
    "and full, soft afternoon light through a nearby window, quiet "
    "empty Japanese kitchen, subtle sense of unease. Vertical 9:16 portrait.",

    # scene2: 帰宅して玄関からキッチンの方を見て立ち止まる
    f"{WOMAN}, standing at the entrance of her apartment just after "
    "coming home, pausing and looking toward the kitchen with a "
    "curious concerned expression, soft evening light. Full upper "
    "body in frame. Vertical 9:16 portrait.",

    # scene3: 朝、猫が普段通りにしている様子
    "Tabby cat looking healthy and lively in the morning light, "
    "stretching casually near a window, normal everyday cat behavior, "
    "warm Japanese apartment morning. Vertical 9:16 portrait.",

    # scene4: ソファで真剣な表情でスマホを操作
    f"{WOMAN}, sitting on sofa at home, looking at smartphone screen "
    "with a serious concerned expression, checking something intently, "
    "soft evening light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・皿の前でじっと座り続ける猫（強い画）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting motionless directly in front of a food bowl, "
    "not eating, staring at the bowl with a subdued posture, quiet "
    "Japanese kitchen. Vertical 9:16 portrait.",

    # scene6: ペットカメラ映像・声をかけたら食べ始める瞬間
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat beginning to eat from its food bowl, head lowering "
    "toward the food, relaxed posture returning, quiet Japanese "
    "kitchen. Vertical 9:16 portrait.",

    # scene7: CTA（そばで見守る中、猫が美味しそうに食べる温かいシーン）
    f"{WOMAN}, kneeling beside a tabby cat that is happily eating from "
    "its bowl, warm gentle smile watching over it, cozy Japanese "
    "kitchen, soft evening light. No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㉗「ごはんが、減ってなかった」")
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
