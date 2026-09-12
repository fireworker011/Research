"""
動画㉝「新しいごはんを、なかなか食べてくれなかった」scene1〜7 の画像を gpt-image-1 で自動生成

改善ルール適用: scene1は「女性がスマホを見る」構図を禁止し、
新しいフードのパッケージのクローズアップから始める新構図。

出力先: C:\\Users\\ys734\\Desktop\\pet33_images\\

使い方:
  python generate_images_pet33.py
  python generate_images_pet33.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet33_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（新しいフードパッケージのクローズアップ・新構図）
    "Close-up shot of a new bag of premium cat food on a kitchen "
    "counter, soft afternoon light, quiet tidy Japanese kitchen. "
    "Vertical 9:16 portrait.",

    # scene2: フードを準備しながら少し不安げな表情
    f"{WOMAN}, standing in the kitchen pouring new cat food into a "
    "bowl, slightly worried thoughtful expression, soft afternoon "
    "light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: ごはん皿を見つめて考え込む様子
    f"{WOMAN}, kneeling in the kitchen looking down at a food bowl "
    "with a concerned reflective expression, soft afternoon light. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene4: ソファでスマホを操作し画面に見入る
    f"{WOMAN}, sitting on sofa at home, looking intently at smartphone "
    "screen with a worried curious expression, soft evening light. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫が新しいフードの匂いを嗅ぐだけで離れる
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sniffing cautiously at a food bowl then stepping back "
    "without eating, hesitant wary posture, quiet Japanese kitchen. "
    "Vertical 9:16 portrait.",

    # scene6: ペットカメラ映像・猫が恐る恐る新しいフードを食べ始める
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat cautiously taking its first small bite from a food "
    "bowl, tentative careful motion, soft afternoon light. "
    "Vertical 9:16 portrait.",

    # scene7: CTA（見守る中、新しいごはんを食べる温かいラストシーン）
    f"{WOMAN}, kneeling beside a tabby cat that is eating from its "
    "bowl, warm relieved smile watching over it, cozy Japanese "
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
    print("gpt-image-1 画像生成 — 動画㉝「新しいごはんを、なかなか食べてくれなかった」")
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
