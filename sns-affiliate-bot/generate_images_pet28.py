"""
動画㉘「窓辺の毛布が、いつもより丸まってた」scene1〜7 の画像を gpt-image-1 で自動生成

改善ルール適用: scene1は「女性がスマホを見る」構図を禁止し、
窓辺の毛布のクローズアップから始める新構図。

出力先: C:\\Users\\ys734\\Desktop\\pet28_images\\

使い方:
  python generate_images_pet28.py
  python generate_images_pet28.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet28_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（窓辺の毛布のクローズアップ・新構図）
    "Close-up shot of a soft beige blanket by a window, curled up more "
    "tightly and neatly than usual, soft afternoon light through sheer "
    "curtains, quiet Japanese apartment, subtle sense of curiosity. "
    "Vertical 9:16 portrait.",

    # scene2: 帰宅して部屋に入り窓辺の方を見て立ち止まる
    f"{WOMAN}, standing in her living room just after coming home, "
    "looking toward the window with a curious pausing expression, "
    "soft evening light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 毛布に近づき不思議そうな表情
    f"{WOMAN}, kneeling near a window, looking at a curled up blanket "
    "with a puzzled curious expression, soft evening light. Full "
    "upper body in frame. Vertical 9:16 portrait.",

    # scene4: ソファでスマホを操作し画面を見つめる
    f"{WOMAN}, sitting on sofa at home, looking at smartphone screen "
    "with a curious focused expression, soft evening light. Full "
    "upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫が毛布を前足で丸める行動
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat using its front paws to knead and shape a soft blanket "
    "by a window, focused determined behavior, soft afternoon light. "
    "Vertical 9:16 portrait.",

    # scene6: ペットカメラ映像・丸めた毛布の中で気持ちよさそうに丸まる
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat curled up contentedly inside a neatly shaped blanket "
    "nest by the window, peaceful relaxed posture, soft afternoon "
    "light. Vertical 9:16 portrait.",

    # scene7: CTA（毛布の中の猫を優しく撫でる温かいラストシーン）
    f"{WOMAN}, kneeling beside the window, gently petting a tabby cat "
    "curled up in its blanket nest, warm affectionate smile, cozy "
    "Japanese living room, soft evening light. No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㉘「窓辺の毛布が、いつもより丸まってた」")
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
