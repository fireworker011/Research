"""
Instagram 読むリール（テキストスライド型縦型動画）生成器。
Pillow でスライド画像を作成し、FFmpeg で MP4 に変換・結合する。
顔出しなし・音声なし。Instagram アップロード時に音楽を追加する前提。
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
HEIGHT = 1920
FPS = 25
SLIDE_BG = (13, 13, 13)       # デフォルト背景色 (dark)

_FONT_CANDIDATES = [
    str(Path(__file__).parent.parent / "assets/fonts/NotoSansJP-Bold.otf"),
    str(Path(__file__).parent.parent / "assets/fonts/NotoSansJP-Bold.ttf"),
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.otf",
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\meiryo.ttc",
]

THEMES = {
    "dark":  {"bg": (13, 13, 13),    "text": (255, 255, 255)},
    "pink":  {"bg": (26,  8, 20),    "text": (255, 255, 255)},
    "navy":  {"bg": ( 8, 16, 26),    "text": (255, 255, 255)},
    "beige": {"bg": (245, 240, 232), "text": ( 26,  26,  26)},
}


def _find_font() -> str:
    for f in _FONT_CANDIDATES:
        if os.path.exists(f):
            return f
    return ""


def _ffmpeg_bin() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def _wrap_lines(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """テキストを max_width px に収まるよう折り返す。"""
    lines = []
    for raw in text.split("\n"):
        raw = raw.strip()
        if not raw:
            lines.append("")
            continue
        current = ""
        for ch in raw:
            test = current + ch
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
    return lines


def _make_slide_image(
    text: str,
    bg_color: tuple,
    text_color: tuple,
    font_path: str,
    size: tuple = (WIDTH, HEIGHT),
) -> Image.Image:
    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)

    margin_x = int(size[0] * 0.08)
    max_text_w = size[0] - margin_x * 2

    # フォントサイズを行数に応じて自動調整
    lines_count = len(text.split("\n"))
    base_size = 88 if lines_count <= 3 else (72 if lines_count <= 5 else 60)

    for fontsize in range(base_size, 30, -4):
        try:
            font = ImageFont.truetype(font_path, fontsize)
        except Exception:
            font = ImageFont.load_default()

        lines = _wrap_lines(text, font, max_text_w)
        line_h = int(fontsize * 1.75)
        total_h = len(lines) * line_h

        if total_h <= size[1] * 0.80:
            break

    y = (size[1] - total_h) // 2
    for line in lines:
        if line:
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            x = (size[0] - w) // 2
            draw.text((x, y), line, font=font, fill=text_color)
        y += line_h

    return img


class InstagramReelGenerator:
    """テキストスライド型 Instagram リールを生成する。"""

    def __init__(self, output_dir: str = "output/reels"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.font_path = _find_font()
        self.ffmpeg = _ffmpeg_bin()

        if not self.font_path:
            raise RuntimeError(
                "日本語フォントが見つかりません。\n"
                "assets/fonts/NotoSansJP-Bold.otf を配置してください。"
            )

    def generate(
        self,
        slides: List[dict],
        output_filename: str,
        theme: str = "dark",
        bgm_path: Optional[str] = None,
    ) -> str:
        """
        slides: [{"text": "...", "duration": 3}, ...]
        戻り値: 生成した MP4 のパス
        """
        t = THEMES.get(theme, THEMES["dark"])

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            scene_files = []

            for i, slide in enumerate(slides):
                img = _make_slide_image(
                    text=slide["text"],
                    bg_color=t["bg"],
                    text_color=t["text"],
                    font_path=self.font_path,
                )
                img_path = str(tmp / f"slide_{i:02d}.png")
                img.save(img_path)

                scene_path = str(tmp / f"scene_{i:02d}.mp4")
                self._img_to_clip(img_path, slide.get("duration", 3), scene_path)
                scene_files.append(scene_path)

            output_path = str(self.output_dir / output_filename)
            self._concat(scene_files, output_path, bgm_path)

        print(f"✅ リール生成完了: {output_path}")
        return output_path

    def _img_to_clip(self, img_path: str, duration: int, output: str):
        """静止画を指定秒数の MP4 クリップに変換する。"""
        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1",
            "-i", img_path,
            "-t", str(duration),
            "-vf", f"scale={WIDTH}:{HEIGHT}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-an",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg clip エラー:\n{result.stderr[-1000:]}")

    def _concat(
        self,
        scene_files: List[str],
        output: str,
        bgm_path: Optional[str] = None,
    ):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            for sf in scene_files:
                f.write(f"file '{sf.replace(chr(92), '/')}'\n")
            list_file = f.name

        try:
            if bgm_path and os.path.exists(bgm_path):
                cmd = [
                    self.ffmpeg, "-y",
                    "-f", "concat", "-safe", "0", "-i", list_file,
                    "-stream_loop", "-1", "-i", bgm_path,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                    "-c:a", "aac", "-b:a", "128k",
                    "-filter:a", "volume=0.25",
                    "-shortest", "-pix_fmt", "yuv420p",
                    output,
                ]
            else:
                cmd = [
                    self.ffmpeg, "-y",
                    "-f", "concat", "-safe", "0", "-i", list_file,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                    "-pix_fmt", "yuv420p",
                    "-an",
                    output,
                ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg concat エラー:\n{result.stderr[-1000:]}")
        finally:
            os.unlink(list_file)
