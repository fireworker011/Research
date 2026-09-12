"""
ペット動画②「通知を見て言葉を失った」 アセンブラ

scene1.mp4〜scene6.mp4 を結合し、Voicevoxナレーション＋テロップを合成して完成動画を出力。
scene7（商品テキストカード）はFFmpegで自動生成。

事前準備: Voicevox を起動しておく（http://localhost:50021）

使い方:
  python assemble_pet2.py
"""

import json
import subprocess
import tempfile
import shutil
import time
import urllib.request
import urllib.parse
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────────────────────────
SCENES_DIR  = Path(r"C:\Users\ys734\Desktop\新しいフォルダー")
OUTPUT      = Path(r"C:\Users\ys734\Desktop\pet_short_02.mp4")
VOICEVOX    = "http://localhost:50021"
SPEAKER_ID  = 9      # 波音リツ (ノーマル)
SPEED       = 0.88
PITCH       = -0.03
INTONATION  = 1.4

# テロップ＝ナレーション（7シーン分）
SUBTITLES = [
    "通知を見て、言葉を失った",
    "昼休み、会社で確認した",
    "何かをくわえて……うろうろしてる",
    "私の、靴下だった",
    "においを嗅いで、安心してた",
    "仕事中に、泣きそうになった",
    "留守番中の子に、声が届くカメラ",
]
# ─────────────────────────────────────────────────────────────────────────────

ASS_TEXTS = SUBTITLES[:6] + [
    "留守番中の子に、声が届くカメラ。\\Nリンクはプロフィールへ【PR】"
]


def run(cmd, label="", cwd=None):
    print(f"  [{label}] 実行中..." if label else "  実行中...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpegエラー ({label}):\n{result.stderr[-1500:]}")


def voicevox_generate(text: str, out_path: Path):
    """Voicevox API で音声生成"""
    url = f"{VOICEVOX}/audio_query?text={urllib.parse.quote(text)}&speaker={SPEAKER_ID}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as res:
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


def generate_narration(texts: list[str], out_dir: Path) -> list[Path]:
    """Voicevox で各シーンのナレーションを生成"""
    paths = []
    for i, text in enumerate(texts, 1):
        out = out_dir / f"tts_{i:02d}.wav"
        print(f"  [TTS] scene{i}: {text}")
        voicevox_generate(text, out)
        paths.append(out)
        time.sleep(0.3)
    return paths


def pad_audio_to_5s(src: Path, dst: Path):
    """音声を5秒に合わせる（短ければ無音でパディング、長ければカット）"""
    run([
        "ffmpeg", "-y", "-i", str(src),
        "-t", "5",
        "-af", "apad=pad_dur=5,atrim=duration=5",
        "-c:a", "aac", "-ar", "44100", "-ac", "2",
        str(dst),
    ], f"pad {src.name}")


def concat_audio(paths: list[Path], dst: Path, tmp: Path):
    list_file = tmp / "audio_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in paths), encoding="utf-8"
    )
    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:a", "aac",
        str(dst),
    ], "音声concat")


def trim_resize(src: Path, dst: Path):
    """5秒にトリム・縦型1080×1920にリサイズ（映像のみ）"""
    run([
        "ffmpeg", "-y", "-i", str(src),
        "-t", "5",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
        "-r", "30",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        str(dst),
    ], f"trim {src.name}")


def make_text_card(dst: Path):
    """scene7: 黒背景のみ生成（テキストはASS字幕で描画）"""
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=#0a0a1a:size=1080x1920:duration=5:rate=30",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        str(dst),
    ], "scene7テキストカード")


def concat_video(paths: list[Path], dst: Path, tmp: Path):
    list_file = tmp / "video_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in paths), encoding="utf-8"
    )
    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(dst),
    ], "映像concat")


def merge_av(video: Path, audio: Path, dst: Path):
    """映像と音声を合成"""
    run([
        "ffmpeg", "-y",
        "-i", str(video),
        "-i", str(audio),
        "-c:v", "copy", "-c:a", "aac",
        "-shortest",
        str(dst),
    ], "映像+音声合成")


def create_ass(dst: Path):
    """白文字・黒縁のASS字幕ファイルを生成"""
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Meiryo,55,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
        "-1,0,0,0,100,100,0,0,1,4,0,2,40,40,80,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events = []
    for i, text in enumerate(ASS_TEXTS):
        s = i * 5
        e = (i + 1) * 5
        events.append(
            f"Dialogue: 0,0:{s//60:02d}:{s%60:02d}.00,"
            f"0:{e//60:02d}:{e%60:02d}.00,Default,,0,0,0,,{text}"
        )
    dst.write_text(header + "\n".join(events), encoding="utf-8-sig")


def burn_subtitles(src: Path, ass: Path, dst: Path):
    # ASSフィルタはパス内のコロンをオプション区切りと誤認するため、
    # ass の親ディレクトリを cwd にしてファイル名のみで参照する（コロン排除）。
    run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", f"ass={ass.name}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "copy",
        str(dst),
    ], "テロップ焼き込み", cwd=str(ass.parent))


def main():
    print("=" * 50)
    print("ペット動画② アセンブラ 開始")
    print("=" * 50)

    # scene1〜6 確認
    scene_files = []
    for i in range(1, 7):
        p = SCENES_DIR / f"scene{i}.mp4"
        if not p.exists():
            raise FileNotFoundError(f"見つかりません: {p}")
        scene_files.append(p)
    print(f"✅ 素材確認: {len(scene_files)}ファイル")

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # Step1: TTS ナレーション生成
        print("\n[Step1] ナレーション生成 (Voicevox / 波音リツ)")
        tts_dir = tmp / "tts"
        tts_dir.mkdir()
        raw_tts = generate_narration(SUBTITLES, tts_dir)

        # Step2: 各ナレーションを5秒にパディング
        print("\n[Step2] 音声を5秒に調整")
        padded_audio = []
        for p in raw_tts:
            out = tmp / f"pad_{p.name.replace('.mp3', '.aac')}"
            pad_audio_to_5s(p, out)
            padded_audio.append(out)

        # Step3: 音声を結合
        print("\n[Step3] 音声結合")
        full_audio = tmp / "full_audio.aac"
        concat_audio(padded_audio, full_audio, tmp)

        # Step4: 映像トリム・リサイズ
        print("\n[Step4] 映像トリム・リサイズ")
        trimmed_video = []
        for sf in scene_files:
            out = tmp / f"t_{sf.name}"
            trim_resize(sf, out)
            trimmed_video.append(out)

        # Step5: scene7 テキストカード生成
        print("\n[Step5] scene7 テキストカード生成")
        scene7 = tmp / "t_scene7.mp4"
        make_text_card(scene7)
        trimmed_video.append(scene7)

        # Step6: 映像結合
        print("\n[Step6] 映像結合")
        concat_v = tmp / "concat_video.mp4"
        concat_video(trimmed_video, concat_v, tmp)

        # Step7: 映像＋音声合成
        print("\n[Step7] 映像＋音声合成")
        av_merged = tmp / "av_merged.mp4"
        merge_av(concat_v, full_audio, av_merged)

        # Step8: ASS字幕生成
        print("\n[Step8] テロップ生成")
        ass_path = tmp / "subtitles.ass"
        create_ass(ass_path)

        # Step9: テロップ焼き込み
        print("\n[Step9] テロップ焼き込み")
        final_tmp = tmp / "final.mp4"
        burn_subtitles(av_merged, ass_path, final_tmp)

        # 出力
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final_tmp, OUTPUT)

    print(f"\n{'='*50}")
    print(f"✅ 完成!")
    print(f"   出力先: {OUTPUT}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
