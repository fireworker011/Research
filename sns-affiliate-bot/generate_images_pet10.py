"""
動画⑩「帰ってから謝っても、もう遅い」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet10_images\\

使い方:
  python generate_images_pet10.py
  python generate_images_pet10.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet10_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（ペットカメラ映像・猫が元気なくうずくまる）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat lying curled up alone on the floor of a dim Japanese apartment, "
    "looking lethargic and unwell, low energy, very still. "
    "Quiet and uneasy atmosphere. Vertical 9:16 portrait.",

    # scene2: 残業する女性
    f"{WOMAN}, sitting at office desk late at night, exhausted expression, "
    "staring blankly at a computer screen, papers piled around her, "
    "harsh fluorescent office lighting. Subtle worry on her face. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: スマホを見たくても見られない
    f"{WOMAN}, at office desk, glancing anxiously at her smartphone lying "
    "face-down on the desk, hesitating to check it, furrowed brow, "
    "suppressed worry. Soft office lighting. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene4: ペットカメラ映像・猫がいつもと違う場所に
    "Pet camera footage style, slightly grainy security camera look. "
    "Wide shot of a Japanese apartment hallway, tabby cat lying hunched "
    "near the entrance in an unusual spot, not moving, slightly curled inward. "
    "Eerie quiet and dim lighting. Vertical 9:16 portrait.",

    # scene5: 猫を抱き上げる女性
    f"{WOMAN}, kneeling on the floor at home, gently cradling a tabby cat "
    "in both arms, deeply worried expression, checking the cat carefully, "
    "cozy Japanese living room. Emotional and tense atmosphere. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene6: 後悔・涙をこらえながらアプリを見る
    f"{WOMAN}, sitting on the floor at home, holding smartphone showing "
    "a pet camera app screen, tearful eyes glistening with regret, "
    "expression of guilt and realization, tabby cat resting beside her. "
    "Quiet emotional atmosphere, warm interior light. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene7: CTA（元気になった猫と笑顔の女性）
    f"{WOMAN}, sitting on sofa at home, smiling with relief, "
    "healthy tabby cat curled comfortably on her lap, "
    "holding smartphone showing a pet camera app, "
    "warm and cheerful Japanese living room. No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑩「帰ってから謝っても、もう遅い」")
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
    print("次のステップ: 各画像をGrokで5秒動画化してください")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
