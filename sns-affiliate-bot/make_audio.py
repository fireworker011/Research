"""
Voicevox で台本ナレーションを生成する

事前準備:
  1. Voicevox を起動（http://localhost:50021 が必要）
  2. python make_audio.py

出力先: C:\\Users\\ys734\\Desktop\\audio\\
  - scene01.wav 〜 scene07.wav  （各シーン個別）
  - full_narration.mp3            （全シーン結合）
"""

import json
import subprocess
import time
from pathlib import Path
import urllib.request
import urllib.error

# ── 設定 ──────────────────────────────────────────────────────────────────────
OUTPUT_DIR  = Path(r"C:\Users\ys734\Desktop\audio")
VOICEVOX    = "http://localhost:50021"
SPEAKER_ID  = 9    # 波音リツ (ノーマル)

# 感情パラメータ（1.0 が標準）
SPEED        = 0.88    # ゆっくり目
PITCH        = -0.03   # 少し低め
INTONATION   = 1.4     # 抑揚を強く

# 台本ナレーション（7シーン）
NARRATION = [
    "通知を見て、言葉を失った",
    "昼休み、会社で確認した",
    "何かをくわえて……うろうろしてる",
    "私の、靴下だった",
    "においを嗅いで、安心してた",
    "仕事中に、泣きそうになった",
    "留守番中の子に、声が届くカメラ",
]
# ─────────────────────────────────────────────────────────────────────────────


def check_voicevox():
    """Voicevox が起動しているか確認"""
    try:
        urllib.request.urlopen(f"{VOICEVOX}/version", timeout=3)
        return True
    except Exception:
        return False


def audio_query(text: str) -> dict:
    url = f"{VOICEVOX}/audio_query?text={urllib.parse.quote(text)}&speaker={SPEAKER_ID}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())


def synthesis(query: dict) -> bytes:
    url = f"{VOICEVOX}/synthesis?speaker={SPEAKER_ID}"
    body = json.dumps(query).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as res:
        return res.read()


def generate_scene(text: str, out_path: Path):
    """1シーンの音声を生成・保存"""
    query = audio_query(text)

    # 感情パラメータ適用
    query["speedScale"]      = SPEED
    query["pitchScale"]      = PITCH
    query["intonationScale"] = INTONATION
    query["volumeScale"]     = 1.0
    # 読点・句点で間を取る
    query["prePhonemeLength"]  = 0.1
    query["postPhonemeLength"] = 0.15

    wav = synthesis(query)
    out_path.write_bytes(wav)


def concat_to_mp3(files: list[Path], dst: Path):
    """WAVファイルを結合してMP3に変換"""
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


def main():
    import urllib.parse

    print("=" * 50)
    print("Voicevox ナレーション生成")
    print("=" * 50)

    # Voicevox 起動確認
    if not check_voicevox():
        print("❌ Voicevox が起動していません。")
        print("   Voicevox を起動してから再実行してください。")
        return

    print(f"✅ Voicevox 接続OK (波音リツ, speaker={SPEAKER_ID})\n")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scene_files = []
    for i, text in enumerate(NARRATION, 1):
        out = OUTPUT_DIR / f"scene{i:02d}.wav"
        print(f"  scene{i:02d}: {text}")
        generate_scene(text, out)
        scene_files.append(out)
        print(f"           → {out.name} ✅")
        time.sleep(0.3)  # API 負荷軽減

    print("\n全シーン結合・MP3変換中...")
    full = OUTPUT_DIR / "full_narration.mp3"
    concat_to_mp3(scene_files, full)
    print(f"  → {full.name} ✅")

    print(f"\n{'='*50}")
    print(f"✅ 完成!")
    print(f"   出力先: {OUTPUT_DIR}")
    print(f"{'='*50}")
    print("\n聴いて確認後、問題なければ assemble_pet2.py で動画に合成します。")


if __name__ == "__main__":
    main()
