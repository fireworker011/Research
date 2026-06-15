"""
台本に沿ってナレーション音声を生成する

出力先: C:\\Users\\ys734\\Desktop\\audio\\
  - scene01.mp3 〜 scene07.mp3  （各シーン個別）
  - full_narration.mp3            （全シーン結合）

使い方:
  python make_audio.py
"""

import asyncio
import subprocess
import shutil
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\audio")
VOICE      = "ja-JP-NanamiNeural"   # 落ち着いた女性の声

# 台本ナレーション（7シーン）
NARRATION = [
    "通知を見て、言葉を失った",
    "昼休み、会社で確認した",
    "何かをくわえて…うろうろしてる",
    "私の靴下だった",
    "においを嗅いで、安心してた",
    "仕事中に、泣きそうになった",
    "留守番中の子に、声が届くカメラ",
]
# ─────────────────────────────────────────────────────────────────────────────


async def generate(text: str, out_path: Path, voice: str = VOICE):
    import edge_tts
    tts = edge_tts.Communicate(text, voice)
    await tts.save(str(out_path))


def concat_audio(files: list[Path], dst: Path):
    list_file = dst.parent / "_concat_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in files), encoding="utf-8"
    )
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:a", "libmp3lame", "-q:a", "2",
        str(dst),
    ], check=True, capture_output=True)
    list_file.unlink()


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"出力先: {OUTPUT_DIR}\n")

    scene_files = []
    for i, text in enumerate(NARRATION, 1):
        out = OUTPUT_DIR / f"scene{i:02d}.mp3"
        print(f"  scene{i:02d}: {text}")
        await generate(text, out)
        scene_files.append(out)
        print(f"           → {out.name} ✅")

    print("\n全シーン結合中...")
    full = OUTPUT_DIR / "full_narration.mp3"
    concat_audio(scene_files, full)
    print(f"  → {full.name} ✅")

    print(f"\n完成! {OUTPUT_DIR} を確認してください。")
    print("問題なければ assemble_pet2.py で動画に合成します。")


if __name__ == "__main__":
    asyncio.run(main())
