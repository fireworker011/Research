"""
ペット動画②「通知を見て言葉を失った」 アセンブラ

scene1.mp4〜scene6.mp4 を結合し、テロップを焼き込んで完成動画を出力する。
scene7（商品テキストカード）はFFmpegで自動生成。

使い方:
  python assemble_pet2.py
"""

import subprocess
import tempfile
import shutil
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────────────────────────
SCENES_DIR = Path(r"C:\Users\ys734\Desktop\新しいフォルダー")
OUTPUT     = Path(r"C:\Users\ys734\Desktop\pet_short_02.mp4")
FONT       = r"C:/Windows/Fonts/meiryo.ttc"

# テロップ（7シーン分）
SUBTITLES = [
    "通知を見て、言葉を失った",
    "昼休み、会社で確認した",
    "何かをくわえて…うろうろしてる",
    "私の靴下だった",
    "においを嗅いで、安心してた",
    "仕事中に、泣きそうになった",
    "留守番中の子に、声が届くカメラ。\\Nリンクはプロフィールへ【PR】",
]
# ─────────────────────────────────────────────────────────────────────────────


def run(cmd, label=""):
    print(f"  [{label}] 実行中..." if label else "  実行中...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"FFmpegエラー ({label}):\n{result.stderr[-1500:]}")


def trim_resize(src: Path, dst: Path):
    """5秒にトリム・縦型1080×1920にリサイズ（音声なし）"""
    run([
        "ffmpeg", "-y", "-i", str(src),
        "-t", "5",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
               "setsar=1",
        "-r", "30",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        str(dst),
    ], f"trim {src.name}")


def make_text_card(dst: Path):
    """scene7: 黒背景に商品テキストを描画（5秒）"""
    line1 = "留守番中の子に、声が届くカメラ。"
    line2 = "リンクはプロフィールへ 【PR】"
    vf = (
        f"drawtext=fontfile='{FONT}':text='{line1}':"
        f"fontcolor=white:fontsize=52:x=(w-text_w)/2:y=(h/2)-60,"
        f"drawtext=fontfile='{FONT}':text='{line2}':"
        f"fontcolor=#cccccc:fontsize=40:x=(w-text_w)/2:y=(h/2)+20"
    )
    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=#0a0a1a:size=1080x1920:duration=5:rate=30",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        str(dst),
    ], "scene7テキストカード")


def concat(paths: list[Path], dst: Path, tmp: Path):
    list_file = tmp / "concat_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in paths), encoding="utf-8"
    )
    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(dst),
    ], "concat")


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
    for i, text in enumerate(SUBTITLES):
        s = i * 5
        e = (i + 1) * 5
        sh = s // 3600
        sm = (s % 3600) // 60
        ss = s % 60
        eh = e // 3600
        em = (e % 3600) // 60
        es = e % 60
        events.append(
            f"Dialogue: 0,{sh}:{sm:02d}:{ss:02d}.00,"
            f"{eh}:{em:02d}:{es:02d}.00,Default,,0,0,0,,{text}"
        )
    dst.write_text(header + "\n".join(events), encoding="utf-8-sig")


def burn_subtitles(src: Path, ass: Path, dst: Path):
    ass_posix = ass.as_posix().replace("C:/", "C\\\\:/")
    run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", f"ass='{ass_posix}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "copy",
        str(dst),
    ], "テロップ焼き込み")


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

        # Step1: 各シーンをトリム・リサイズ
        print("\n[Step1] トリム・リサイズ")
        trimmed = []
        for sf in scene_files:
            out = tmp / f"t_{sf.name}"
            trim_resize(sf, out)
            trimmed.append(out)

        # Step2: scene7 テキストカード生成
        print("\n[Step2] scene7 テキストカード生成")
        scene7 = tmp / "t_scene7.mp4"
        make_text_card(scene7)
        trimmed.append(scene7)

        # Step3: concat
        print("\n[Step3] 結合")
        concat_out = tmp / "concat.mp4"
        concat(trimmed, concat_out, tmp)

        # Step4: ASS字幕生成
        print("\n[Step4] テロップ生成")
        ass_path = tmp / "subtitles.ass"
        create_ass(ass_path)

        # Step5: テロップ焼き込み
        print("\n[Step5] テロップ焼き込み")
        final_tmp = tmp / "final.mp4"
        burn_subtitles(concat_out, ass_path, final_tmp)

        # 出力
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final_tmp, OUTPUT)

    print(f"\n{'='*50}")
    print(f"✅ 完成!")
    print(f"   出力先: {OUTPUT}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
