"""
動画⑧「真顔で待ち伏せされてた」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet8_images\\

使い方:
  python generate_images_pet8.py
  python generate_images_pet8.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet8_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: 真顔で待ち伏せする猫（フック）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting perfectly upright behind a door corner, completely "
    "still with a deadpan serious expression, as if lying in wait. "
    "Comic and slightly absurd atmosphere. Vertical 9:16 portrait.",

    # scene2: 仕事の合間にスマホを見る
    f"{WOMAN} with dark navy blazer, glancing at smartphone at office desk "
    "during a short break, casual relaxed expression. Soft office lighting. "
    "Upper body in frame. Vertical 9:16 portrait.",

    # scene3: 廊下の角に潜む猫
    "Pet camera footage style, slightly grainy. Tabby cat crouched low "
    "at the corner of a hallway, peeking around the wall with intense "
    "focused eyes, hunting ambush posture. Comic tension. Vertical 9:16 portrait.",

    # scene4: 待ち伏せ・微動だにしない
    "Pet camera footage style, slightly grainy. Tabby cat frozen completely "
    "still in a crouched ambush position, staring down an empty hallway, "
    "ears flat with intense concentration. Absurd and funny. Vertical 9:16 portrait.",

    # scene5: 女性が笑いをこらえる
    f"{WOMAN} with dark navy blazer, at office desk, raising one eyebrow "
    "with an amused puzzled smile, looking at smartphone, holding back a laugh. "
    "Soft office light. Upper body in frame. Vertical 9:16 portrait.",

    # scene6: 何もない廊下（オチ）
    "Pet camera footage style, slightly grainy. Wide shot of an empty "
    "Japanese apartment hallway with a tabby cat crouched in ambush position "
    "at the far corner, nothing else around. Comic emptiness. Vertical 9:16 portrait.",

    # scene7: CTA（女性と猫・笑顔）
    f"{WOMAN} sitting at home laughing warmly at her smartphone, "
    "tabby cat casually walking toward her, cozy Japanese living room, "
    "cheerful and heartwarming atmosphere. No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑧「真顔で待ち伏せされてた」")
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
