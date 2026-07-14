"""
動画㉓「電車の中で、通知が鳴った」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet23_images\\

使い方:
  python generate_images_pet23.py
  python generate_images_pet23.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet23_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（満員電車の中、スマホが震える）
    "Close-up shot of a smartphone vibrating in a woman's hand inside a "
    "crowded train, screen lighting up with a notification, blurred "
    "commuters in the background, evening train interior lighting. "
    "Vertical 9:16 portrait.",

    # scene2: 帰宅ラッシュの中、疲れた表情
    f"{WOMAN}, standing in a crowded commuter train holding a strap, "
    "tired expression during evening rush hour, dim train interior "
    "lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: ふと不安げにスマホを気にする
    f"{WOMAN}, medium close-up shot focused on her face, standing in a "
    "train, glancing worriedly at her smartphone in her hand, subtle "
    "tension. Dim train interior lighting. Vertical 9:16 portrait.",

    # scene4: 駅のホームで立ち止まりスマホを開く緊張の表情
    f"{WOMAN}, standing still on a train station platform, quickly "
    "opening her smartphone with a tense urgent expression, evening "
    "station lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫が窓の外を見つめている
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting on a windowsill, gazing intently out the window, "
    "calm focused posture, soft evening light through the window. "
    "Vertical 9:16 portrait.",

    # scene6: 猫が玄関の方向を振り返る
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat turning its head toward the direction of the entrance "
    "door, alert and attentive expression, quiet Japanese apartment. "
    "Vertical 9:16 portrait.",

    # scene7: CTA（安堵の笑顔でスマホをしまい帰路を急ぐ）
    f"{WOMAN}, standing on a train station platform with a relieved "
    "warm smile, putting her smartphone away, softly touched expression, "
    "evening station lighting. No text. Full upper body in frame. "
    "Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画㉓「電車の中で、通知が鳴った」")
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
