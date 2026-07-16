"""
動画㉕「今日も、一人でお留守番」ナレーション音声生成（Voicevox / 波音リツ）

新フォーマット: 猫目線モノローグ

事前準備: Voicevox を起動（http://localhost:50021）

使い方:
  python make_audio_pet25.py

出力先: C:\\Users\\ys734\\Desktop\\audio_pet25\\
"""

import json
import subprocess
import time
import urllib.request
import urllib.parse
from pathlib import Path

OUTPUT_DIR = Path(r"C:\Users\ys734\Desktop\audio_pet25")
VOICEVOX   = "http://localhost:50021"
SPEAKER_ID = 9
SPEED      = 0.90
PITCH      = -0.02
INTONATION = 1.3

NARRATION = [
    "今日も、一人でお留守番",
    "ドアが閉まる音、いつも同じ",
    "窓の外を眺めるだけの時間",
    "静かな部屋に、小さな光が灯った",
    "あの人の声が、聞こえた気がした",
    "しっぽが、勝手に動いた",
    "一人でも、ちゃんと繋がっていられるカメラ",
]


def check_voicevox():
    try:
        urllib.request.urlopen(f"{VOICEVOX}/version", timeout=3)
        return True
    except Exception:
        return False


def generate_scene(text: str, out_path: Path):
    url = f"{VOICEVOX}/audio_query?text={urllib.parse.quote(text)}&speaker={SPEAKER_ID}"
    with urllib.request.urlopen(urllib.request.Request(url, method="POST")) as res:
        query = json.loads(res.read())

    query["speedScale"]        = SPEED
    query["pitchScale"]        = PITCH
    query["intonationScale"]   = INTONATION
    query["prePhonemeLength"]  = 0.1
    query["postPhonemeLength"] = 0.15

    url2 = f"{VOICEVOX}/synthesis?speaker={SPEAKER_ID}"
    body = json.dumps(query).encode("utf-8")
    req2 = urllib.request.Request(url2, data=body, method="POST",
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req2) as res:
        out_path.write_bytes(res.read())


def concat_to_mp3(files: list[Path], dst: Path):
    list_file = dst.parent / "_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in files), encoding="utf-8"
    )
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:a", "libmp3lame", "-q:a", "2", str(dst),
    ], check=True, capture_output=True)
    list_file.unlink()


def main():
    print("=" * 50)
    print("動画㉕ ナレーション生成（波音リツ / 猫目線）")
    print("=" * 50)

    if not check_voicevox():
        print("❌ Voicevox が起動していません。起動してから再実行してください。")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene_files = []

    for i, text in enumerate(NARRATION, 1):
        out = OUTPUT_DIR / f"scene{i:02d}.wav"
        print(f"  scene{i}: {text}")
        generate_scene(text, out)
        scene_files.append(out)
        print(f"          → {out.name} ✅")
        time.sleep(0.3)

    print("\n結合・MP3変換中...")
    full = OUTPUT_DIR / "full_narration.mp3"
    concat_to_mp3(scene_files, full)
    print(f"  → {full.name} ✅")

    print(f"\n✅ 完成: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
