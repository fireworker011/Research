"""
動画㉑「友達の家に泊まった夜、通知が鳴った」scene1〜7 の画像を gpt-image-1 で自動生成

出力先: C:\\Users\\ys734\\Desktop\\pet21_images\\

使い方:
  python generate_images_pet21.py
  python generate_images_pet21.py 1 3 5  # 指定シーンのみ再生成
"""

import base64
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\pet21_images")

WOMAN = (
    "Japanese woman in her early 30s, black shoulder-length straight hair "
    "slightly tucked behind one ear, oval face, natural makeup, "
    "wearing a light beige turtleneck sweater and dark navy trousers"
)

PROMPTS = [
    # scene1: フック（友人宅のリビングでスマホが光る）
    "Close-up shot of a smartphone lighting up with a notification on a "
    "living room table, cozy friend's apartment at night, warm indoor "
    "lighting, blurred figures relaxing in the background. Vertical 9:16 portrait.",

    # scene2: 友人と楽しそうに話している和やかなシーン
    f"{WOMAN}, sitting on a sofa at a friend's home, laughing and chatting "
    "happily during a casual girls' night gathering, warm cozy lighting. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene3: 会話の途中でスマホにちらっと目をやる
    f"{WOMAN}, medium close-up shot focused on her face, glancing "
    "briefly toward her smartphone on the table while still smiling "
    "at the conversation, subtle curiosity. Warm indoor lighting. "
    "Vertical 9:16 portrait.",

    # scene4: 席を外し廊下でスマホを開く緊張の表情
    f"{WOMAN}, standing alone in a quiet hallway, opening her smartphone "
    "with a slightly tense curious expression, dim hallway lighting. "
    "Full upper body in frame. Vertical 9:16 portrait.",

    # scene5: ペットカメラ映像・猫が普段いない場所に座っている
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat sitting in an unusual spot it doesn't normally occupy, "
    "such as on top of a bookshelf, calm curious posture, quiet Japanese "
    "apartment at night. Vertical 9:16 portrait.",

    # scene6: 猫がくつろいだ様子で毛づくろいをしている
    "Pet camera footage style, slightly grainy security camera look. "
    "Tabby cat grooming itself contentedly, relaxed posture, peaceful "
    "atmosphere, dim nighttime room lighting. Vertical 9:16 portrait.",

    # scene7: CTA（安堵の笑顔でスマホをしまい友人の元へ戻る）
    f"{WOMAN}, standing in a hallway with a relieved warm smile, "
    "putting her smartphone away, softly touched expression before "
    "returning to the gathering. No text. Full upper body in frame. "
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
    print("gpt-image-1 画像生成 — 動画㉑「友達の家に泊まった夜、通知が鳴った」")
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
