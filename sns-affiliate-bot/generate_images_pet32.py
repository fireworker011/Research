"""
動画㉜「ごはんより、待つ方が好きだった」scene1〜7 の画像を gpt-image-1 で自動生成

新フォーマット: 猫目線モノローグ×食テーマ（㉕の猫目線形式と㉗の食×不安型を融合）
全編ほぼペットカメラ視点で統一し、最後のみ女性視点に切り替える。

出力先: C:\\Users\\ys734\\Desktop\\pet32_images\\

使い方:
  python generate_images_pet32.py
  python generate_images_pet32.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet32_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（ごはん皿の前に座っているが食べずにいる猫）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting calmly in front of a full food bowl, not eating "
    "yet, patient composed posture, soft afternoon light in a quiet "
    "Japanese kitchen. Vertical 9:16 portrait.",

    # scene2: 玄関の方向へ耳を傾ける仕草
    "Pet camera footage style, slightly grainy security camera look. "
    "Close-up of a tabby cat's face, ears turning and tilting toward "
    "the direction of the entrance, attentive listening posture, quiet "
    "Japanese apartment. Vertical 9:16 portrait.",

    # scene3: お座りしたまま静かに待つ
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting upright and still near the food bowl, calm "
    "patient waiting posture, soft afternoon light. Vertical 9:16 portrait.",

    # scene4: お腹のあたりを気にする仕草
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat glancing down toward its own belly with a subtle curious "
    "gesture, still sitting near the food bowl, quiet Japanese kitchen. "
    "Vertical 9:16 portrait.",

    # scene5: 視線だけ玄関に向けたまま動かない
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat's body remaining still while its eyes gaze steadily "
    "toward the entrance direction, quiet determined focus, soft "
    "afternoon light. Vertical 9:16 portrait.",

    # scene6: 耳がぴくっと動き、表情が和らぐ
    "Pet camera footage style, slightly grainy security camera look. "
    "Close-up of a tabby cat's face, ears perking up suddenly, "
    "expression softening with recognition, quiet Japanese apartment. "
    "Vertical 9:16 portrait.",

    # scene7: CTA（女性がスマホで話しかけながら見守り、猫が食べ始める）
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
    print("gpt-image-1 画像生成 — 動画㉜「ごはんより、待つ方が好きだった」")
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
