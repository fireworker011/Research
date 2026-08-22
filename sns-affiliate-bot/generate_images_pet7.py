"""
動画⑦「カメラに映ってたの、見せていいですか」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet7_images\\

使い方:
  python generate_images_pet7.py
  python generate_images_pet7.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet7_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: スマホを見せようとしている（フック）
    f"{WOMAN} with dark navy blazer, sitting at office desk, "
    "slightly amused and puzzled expression, holding up smartphone "
    "as if about to show something to the viewer. Soft office lighting. "
    "Upper body in frame. Vertical 9:16 portrait.",

    # scene2: 何気なくカメラを開く
    f"{WOMAN} with dark navy blazer, at office desk during lunch break, "
    "casually opening pet camera app on smartphone, relaxed and "
    "unsuspecting expression. Soft office light. Upper body in frame. "
    "Vertical 9:16 portrait.",

    # scene3: 猫が壁をじっと見ている（奇行①）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting completely still, staring intensely at a blank "
    "white wall with wide focused eyes. Nothing on the wall. "
    "Eerie and slightly comic atmosphere. Vertical 9:16 portrait.",

    # scene4: 猫が壁を見続けている（奇行②・首傾げ）
    "Pet camera footage style, slightly grainy. Tabby cat sitting in front "
    "of a plain white wall, head slightly tilted to one side, completely "
    "transfixed, tail neatly wrapped around its feet. Mysterious and "
    "comic expression. Vertical 9:16 portrait.",

    # scene5: 女性が笑いをこらえている
    f"{WOMAN} with dark navy blazer, at office desk, hand covering mouth "
    "trying not to laugh out loud, eyes wide and amused, shoulders "
    "slightly shaking with suppressed laughter. Soft office light. "
    "Upper body in frame. Vertical 9:16 portrait.",

    # scene6: 猫がカメラに気づく
    "Pet camera footage style, slightly grainy. Tabby cat suddenly turning "
    "its head directly toward the camera with wide curious eyes and ears "
    "perked up, as if noticing it's being watched. Slightly comic "
    "surprised expression. Vertical 9:16 portrait.",

    # scene7: CTA（女性と猫・笑顔・温かい）
    f"{WOMAN} sitting at home laughing warmly at her smartphone, "
    "tabby cat sitting right beside her looking up curiously, "
    "warm cozy Japanese living room, cheerful and heartwarming atmosphere. "
    "No text. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑦「カメラに映ってたの、見せていいですか」")
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
