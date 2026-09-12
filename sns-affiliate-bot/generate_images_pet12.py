"""
動画⑫「声だけで、しっぽが動いた」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet12_images\\

使い方:
  python generate_images_pet12.py
  python generate_images_pet12.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet12_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（ペットカメラ映像・猫がくつろいでいる）
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat relaxing comfortably on a sofa in a Japanese apartment, "
    "calm and peaceful, soft warm lighting. Cozy domestic atmosphere. "
    "Vertical 9:16 portrait.",

    # scene2: 女性がオフィスでペットカメラアプリを操作
    f"{WOMAN}, sitting at office desk, holding smartphone and opening "
    "a pet camera app, curious and slightly hopeful expression, "
    "soft office lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 半信半疑でマイクボタンを押す
    f"{WOMAN}, at office desk, finger hovering over smartphone screen "
    "with a doubtful yet hopeful expression, hesitating before pressing "
    "a button, soft office lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene4: ペットカメラ映像・猫の耳がぴくっと動く
    "Pet camera footage style, slightly grainy security camera look. "
    "Close-up of a tabby cat's face, ears suddenly perking up and rotating "
    "forward attentively, eyes widening slightly, alert reaction. "
    "Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・しっぽがゆれカメラを向く
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat slowly turning its head toward the camera direction, "
    "tail beginning to sway gently, curious and responsive expression. "
    "Vertical 9:16 portrait.",

    # scene6: 女性が目を潤ませて笑顔でスマホを見る
    f"{WOMAN}, at office desk, eyes glistening with happy tears, "
    "warm smile spreading across her face while looking at smartphone "
    "screen, deeply moved expression. Soft office lighting. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene7: CTA（帰宅・猫が駆け寄る温かいシーン）
    f"{WOMAN}, standing in the entrance of a Japanese apartment, "
    "smiling warmly as a tabby cat trots toward her happily, "
    "homecoming scene, warm evening lighting, heartwarming atmosphere. "
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
    print("gpt-image-1 画像生成 — 動画⑫「声だけで、しっぽが動いた」")
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
