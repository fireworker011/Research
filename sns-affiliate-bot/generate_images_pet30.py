"""
動画㉚「クッションの上に、抜け毛だけが残ってた」scene1〜7 の画像を gpt-image-1 で自動生成

改善ルール適用: scene1は「女性がスマホを見る」構図を禁止し、
クッションの上の抜け毛のクローズアップから始める新構図。

出力先: C:\\Users\\ys734\\Desktop\\pet30_images\\

使い方:
  python generate_images_pet30.py
  python generate_images_pet30.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet30_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（クッションの上の抜け毛のクローズアップ・新構図）
    "Close-up shot of a soft beige cushion on a sofa, with fine cat fur "
    "left behind in a curled nest-like shape, soft afternoon light, "
    "quiet Japanese living room, subtle wistful atmosphere. Vertical 9:16 portrait.",

    # scene2: クッションを見つめて立ち止まる
    f"{WOMAN}, standing in her living room, looking down at a cushion "
    "on the sofa with a quiet reflective expression, soft evening "
    "light. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 部屋を見渡し猫を探す様子
    f"{WOMAN}, looking around her living room with a searching curious "
    "expression, soft evening light. Full upper body in frame. "
    "Vertical 9:16 portrait.",

    # scene4: ソファでスマホを操作し画面に見入る
    f"{WOMAN}, sitting on sofa at home, looking intently at smartphone "
    "screen with a concerned curious expression, soft evening light. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫がクッションで長時間丸まっている
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat curled up peacefully on a cushion for a long time, "
    "unchanged relaxed position, soft afternoon light through window. "
    "Vertical 9:16 portrait.",

    # scene6: ペットカメラ映像・猫がクッションの匂いを嗅ぐ仕草
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sniffing gently at a cushion, tender curious gesture, "
    "soft quiet Japanese living room. Vertical 9:16 portrait.",

    # scene7: CTA（クッションのそばで猫と一緒にくつろぐ温かいラストシーン）
    f"{WOMAN}, sitting on the sofa beside the cushion, tabby cat curled "
    "up affectionately against her, warm contented smile, cozy "
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
    print("gpt-image-1 画像生成 — 動画㉚「クッションの上に、抜け毛だけが残ってた」")
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
