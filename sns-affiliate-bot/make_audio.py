"""
台本に沿ってナレーション音声を生成する（SSML感情付き）

出力先: C:\\Users\\ys734\\Desktop\\audio\\
  - scene01.mp3 〜 scene07.mp3  （各シーン個別）
  - full_narration.mp3            （全シーン結合）

使い方:
  python make_audio.py
"""

import asyncio
import subprocess
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\audio")
VOICE      = "ja-JP-NanamiNeural"

# SSML付きナレーション（間・テンポ・ピッチで感情を表現）
NARRATION_SSML = [
    # scene1: 衝撃・固まる
    "<speak><prosody rate='slow' pitch='-3st'>"
    "通知を見て、<break time='700ms'/>言葉を失った"
    "</prosody></speak>",

    # scene2: 不安・緊張
    "<speak><prosody rate='medium' pitch='-1st'>"
    "昼休み、<break time='400ms'/>会社で確認した"
    "</prosody></speak>",

    # scene3: 首をかしげる・不思議
    "<speak><prosody rate='slow' pitch='0st'>"
    "何かをくわえて…<break time='600ms'/>うろうろしてる"
    "</prosody></speak>",

    # scene4: 静かな驚き
    "<speak><prosody rate='slow' pitch='-2st'>"
    "<break time='300ms'/>私の…靴下だった"
    "</prosody></speak>",

    # scene5: じんわり感動
    "<speak><prosody rate='slow' pitch='-2st'>"
    "においを嗅いで、<break time='600ms'/>安心してた"
    "</prosody></speak>",

    # scene6: 涙をこらえる
    "<speak><prosody rate='slow' pitch='-3st'>"
    "仕事中に、<break time='500ms'/>泣きそうになった"
    "</prosody></speak>",

    # scene7: 温かく締める
    "<speak><prosody rate='medium' pitch='-1st'>"
    "留守番中の子に、<break time='400ms'/>声が届くカメラ"
    "</prosody></speak>",
]

SCENE_LABELS = [
    "通知を見て、言葉を失った",
    "昼休み、会社で確認した",
    "何かをくわえて…うろうろしてる",
    "私の靴下だった",
    "においを嗅いで、安心してた",
    "仕事中に、泣きそうになった",
    "留守番中の子に、声が届くカメラ",
]
# ─────────────────────────────────────────────────────────────────────────────


async def generate(ssml: str, out_path: Path, voice: str = VOICE):
    import edge_tts
    tts = edge_tts.Communicate(ssml, voice)
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
    for i, (ssml, label) in enumerate(zip(NARRATION_SSML, SCENE_LABELS), 1):
        out = OUTPUT_DIR / f"scene{i:02d}.mp3"
        print(f"  scene{i:02d}: {label}")
        await generate(ssml, out)
        scene_files.append(out)
        print(f"           → {out.name} ✅")

    print("\n全シーン結合中...")
    full = OUTPUT_DIR / "full_narration.mp3"
    concat_audio(scene_files, full)
    print(f"  → {full.name} ✅")

    print(f"\n完成! {OUTPUT_DIR} を確認してください。")


if __name__ == "__main__":
    asyncio.run(main())
