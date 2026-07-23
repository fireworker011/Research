"""
Grok完全自動アセンブラ（CapCut不要）

入力:
  - SCENES_DIR/scene1.mp4 〜 scene7.mp4   （Grokで動画化した各シーン・無音）
  - VOICE_VIDEO                            （Grok Companionの音声入り動画）
  - BGM（任意）                            （なければ無音）

処理:
  1. Grok Companion動画から音声を自動抽出
  2. 無音区間を検出してナレーションを7分割
  3. 各シーン動画を対応ナレーションの長さに自動調整
  4. キャプション（テロップ）を自動焼き込み
  5. BGMを自動ミックス（音量バランス）
  6. 縦型1080×1920でエクスポート

使い方:
  python assemble_grok.py
  python assemble_grok.py --no-split   # 分割せずフル音声を全体に乗せる
"""

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────────────────────────
SCENES_DIR  = Path(r"C:\Users\ys734\Desktop\pet8_scenes")      # scene1〜7.mp4
VOICE_VIDEO = Path(r"C:\Users\ys734\Desktop\grok_voice.mp4")   # Companion音声入り動画
BGM         = Path(r"C:\Users\ys734\Desktop\bgm.mp3")          # 任意（なければ無視）
OUTPUT      = Path(r"C:\Users\ys734\Desktop\pet_short_08.mp4")

# テロップ＝ナレーション（CTAだけリンク誘導を追記）
SUBTITLES = [
    "真顔で待ち伏せされてた",
    "仕事の合間に、見てみたら",
    "廊下の角に、いた",
    "微動だに、しない",
    "誰を待ってるの",
    "何もない廊下を、ずっと",
    "留守番中の子の、全部が見えるカメラ",
]
CTA_EXTRA = "\\Nプロフィールのリンクへ【PR】"

# 無音判定パラメータ
SILENCE_DB   = "-30dB"   # これより静かなら無音とみなす
SILENCE_MIN  = 0.35      # この秒数以上続く無音を区切りとする
BGM_VOLUME   = 0.18      # BGM音量（ナレーション1.0に対して）
# ─────────────────────────────────────────────────────────────────────────────


def run(cmd, label="", cwd=None, capture=True):
    print(f"  [{label}] 実行中..." if label else "  実行中...")
    result = subprocess.run(cmd, capture_output=capture, text=True,
                            encoding="utf-8", cwd=cwd)
    if result.returncode != 0:
        err = result.stderr[-1500:] if result.stderr else "(no stderr)"
        raise RuntimeError(f"FFmpegエラー ({label}):\n{err}")
    return result


def extract_audio(src_video: Path, dst_audio: Path):
    """Grok Companion動画から音声を抽出（CapCutの代替）"""
    run([
        "ffmpeg", "-y", "-i", str(src_video),
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(dst_audio),
    ], "音声抽出")


def get_duration(media: Path) -> float:
    res = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(media),
    ], "尺取得")
    return float(json.loads(res.stdout)["format"]["duration"])


def detect_silences(audio: Path) -> list[tuple[float, float]]:
    """無音区間を検出して [(start, end), ...] を返す"""
    res = subprocess.run([
        "ffmpeg", "-i", str(audio),
        "-af", f"silencedetect=noise={SILENCE_DB}:d={SILENCE_MIN}",
        "-f", "null", "-",
    ], capture_output=True, text=True, encoding="utf-8")
    log = res.stderr
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", log)]
    ends   = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(starts, ends))


def split_points_from_silences(silences, total_dur, n_segments) -> list[float]:
    """無音の中点を区切り候補とし、n_segments個になるよう選ぶ"""
    midpoints = [(s + e) / 2 for s, e in silences]
    needed = n_segments - 1
    if len(midpoints) == needed:
        cuts = midpoints
    elif len(midpoints) > needed:
        # 無音が長い順に needed 個選ぶ
        ranked = sorted(silences, key=lambda x: x[1] - x[0], reverse=True)[:needed]
        cuts = sorted((s + e) / 2 for s, e in ranked)
    else:
        # 足りなければ均等割りでフォールバック
        cuts = [total_dur * i / n_segments for i in range(1, n_segments)]
    return [0.0] + cuts + [total_dur]


def slice_audio(audio: Path, start: float, end: float, dst: Path):
    run([
        "ffmpeg", "-y", "-i", str(audio),
        "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
        "-c:a", "aac", "-ar", "44100", "-ac", "2",
        str(dst),
    ], "音声スライス")


def fit_video_to_duration(src: Path, dur: float, dst: Path):
    """シーン動画を指定秒数に合わせ、縦型1080×1920にリサイズ（無音）"""
    run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src),
        "-t", f"{dur:.3f}",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1",
        "-r", "30",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        str(dst),
    ], f"尺調整 {src.name}")


def concat_media(paths: list[Path], dst: Path, tmp: Path, mode: str):
    list_file = tmp / f"{mode}_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in paths), encoding="utf-8"
    )
    codec = ["-c", "copy"] if mode == "video" else ["-c:a", "aac"]
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), *codec, str(dst),
    ], f"{mode} concat")


def merge_av(video: Path, audio: Path, dst: Path):
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(audio),
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(dst),
    ], "映像+音声合成")


def mix_bgm(video_with_voice: Path, bgm: Path, dst: Path):
    """ナレーション入り動画にBGMを重ねる"""
    run([
        "ffmpeg", "-y", "-i", str(video_with_voice), "-stream_loop", "-1", "-i", str(bgm),
        "-filter_complex",
        f"[1:a]volume={BGM_VOLUME}[bgm];[0:a][bgm]amix=inputs=2:duration=first[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(dst),
    ], "BGMミックス")


def create_ass(dst: Path, durations: list[float]):
    """各シーンの実尺に合わせてキャプションを生成"""
    texts = SUBTITLES[:6] + [SUBTITLES[6] + CTA_EXTRA]
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

    def ts(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    events, t = [], 0.0
    for text, dur in zip(texts, durations):
        events.append(
            f"Dialogue: 0,{ts(t)},{ts(t + dur)},Default,,0,0,0,,{text}"
        )
        t += dur
    dst.write_text(header + "\n".join(events), encoding="utf-8-sig")


def burn_subtitles(src: Path, ass: Path, dst: Path):
    run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", f"ass={ass.name}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "copy",
        str(dst),
    ], "テロップ焼き込み", cwd=str(ass.parent))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-split", action="store_true",
                    help="音声を分割せずフル尺で乗せる")
    args = ap.parse_args()

    print("=" * 55)
    print("Grok完全自動アセンブラ（CapCut不要）")
    print("=" * 55)

    # シーン動画確認
    scene_files = []
    for i in range(1, 8):
        p = SCENES_DIR / f"scene{i}.mp4"
        if not p.exists():
            raise FileNotFoundError(f"見つかりません: {p}")
        scene_files.append(p)
    print(f"✅ シーン動画: {len(scene_files)}本")

    if not VOICE_VIDEO.exists():
        raise FileNotFoundError(f"音声入り動画が見つかりません: {VOICE_VIDEO}")

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)

        # Step1: 音声抽出
        print("\n[Step1] Grok Companion動画から音声抽出")
        full_audio = tmp / "voice.wav"
        extract_audio(VOICE_VIDEO, full_audio)
        total = get_duration(full_audio)
        print(f"  → 音声尺: {total:.1f}秒")

        # Step2: 区切り決定
        print("\n[Step2] ナレーションを7分割")
        if args.no_split:
            bounds = [total * i / 7 for i in range(8)]
        else:
            silences = detect_silences(full_audio)
            print(f"  無音区間: {len(silences)}個検出")
            bounds = split_points_from_silences(silences, total, 7)
        seg_durs = [bounds[i + 1] - bounds[i] for i in range(7)]
        for i, d in enumerate(seg_durs, 1):
            print(f"  scene{i}: {d:.1f}秒")

        # Step3: 各シーンの音声スライス
        print("\n[Step3] 音声スライス")
        audio_parts = []
        for i in range(7):
            a = tmp / f"a_{i+1}.aac"
            slice_audio(full_audio, bounds[i], bounds[i + 1], a)
            audio_parts.append(a)

        # Step4: 各シーン動画を音声尺に合わせる
        print("\n[Step4] シーン動画の尺調整")
        fitted_videos = []
        for i, (sf, dur) in enumerate(zip(scene_files, seg_durs), 1):
            v = tmp / f"v_{i}.mp4"
            fit_video_to_duration(sf, dur, v)
            fitted_videos.append(v)

        # Step5: 映像・音声をそれぞれ結合
        print("\n[Step5] 結合")
        concat_v = tmp / "concat_v.mp4"
        concat_a = tmp / "concat_a.aac"
        concat_media(fitted_videos, concat_v, tmp, "video")
        concat_media(audio_parts, concat_a, tmp, "audio")

        # Step6: 映像＋音声
        print("\n[Step6] 映像＋音声合成")
        av = tmp / "av.mp4"
        merge_av(concat_v, concat_a, av)

        # Step7: BGMミックス（あれば）
        if BGM.exists():
            print("\n[Step7] BGMミックス")
            av_bgm = tmp / "av_bgm.mp4"
            mix_bgm(av, BGM, av_bgm)
            av = av_bgm
        else:
            print("\n[Step7] BGMなし（スキップ）")

        # Step8: キャプション
        print("\n[Step8] キャプション生成・焼き込み")
        ass_path = tmp / "subtitles.ass"
        create_ass(ass_path, seg_durs)
        final_tmp = tmp / "final.mp4"
        burn_subtitles(av, ass_path, final_tmp)

        # 出力
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final_tmp, OUTPUT)

    print(f"\n{'='*55}")
    print(f"✅ 完成!  {OUTPUT}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
