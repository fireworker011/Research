"""
動画⑳「会議中、通知が3回鳴った」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet20_images\\

使い方:
  python generate_images_pet20.py
  python generate_images_pet20.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet20_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（会議室、テーブルの上でスマホが震える。人物は背景でぼかす）
    "Close-up shot of a smartphone vibrating on a conference table, "
    "screen lighting up with a notification, blurred silhouettes of "
    "meeting attendees in the background, office meeting room lighting. "
    "Vertical 9:16 portrait.",

    # scene2: 女性が横目でスマホをちらっと見る、平静を装う（顔中心のミディアムショット）
    f"{WOMAN}, medium close-up shot focused on her face, glancing "
    "sideways toward her smartphone on the table, trying to maintain "
    "a composed expression, subtle tension, office meeting room "
    "lighting. Vertical 9:16 portrait.",

    # scene3: 表情が徐々に不安げに変わる（バストアップ、正面から）
    f"{WOMAN}, front-facing bust shot, expression shifting to quiet "
    "worry, brows slightly furrowed, sitting upright at a conference "
    "table, office meeting room lighting. Vertical 9:16 portrait.",

    # scene4: 会議室を出てすぐスマホを開く緊張の表情
    f"{WOMAN}, walking out of a meeting room hallway, quickly opening "
    "her smartphone with a tense urgent expression, office corridor "
    "lighting. Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫が何度もレンズの前を横切る
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat walking back and forth repeatedly in front of the camera "
    "lens, restless pacing motion, quiet Japanese apartment. Vertical 9:16 portrait.",

    # scene6: 猫がレンズに顔を近づけて見つめる
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat approaching close to the camera lens, face filling the "
    "frame, curious attentive eyes looking directly into the lens. "
    "Vertical 9:16 portrait.",

    # scene7: CTA（安堵と愛おしさの混じった笑顔）
    f"{WOMAN}, standing in the office corridor, looking at smartphone "
    "screen with a relieved warm smile, softly touched expression. "
    "No text. Full upper body in frame. Vertical 9:16 portrait.",
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
    print("gpt-image-1 画像生成 — 動画⑳「会議中、通知が3回鳴った」")
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
