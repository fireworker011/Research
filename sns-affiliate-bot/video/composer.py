import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from .voicevox import VoiceVox
from .pexels import PexelsClient


WIDTH = 1080
HEIGHT = 1920
FPS = 25

_FONTS_WINDOWS = [
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
]
_FONTS_LINUX = [
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.otf",
]


def _find_font() -> str:
    candidates = _FONTS_WINDOWS if platform.system() == "Windows" else _FONTS_LINUX
    for f in candidates:
        if os.path.exists(f):
            return f
    return ""


def _copy_font_to_tmp(font_path: str, tmp: Path) -> str:
    """フォントを tmpdir にコピーしてパスを返す（Windows の C:\\... コロン問題回避）。"""
    if not font_path:
        return ""
    dest = str(tmp / "font.ttc")
    shutil.copy2(font_path, dest)
    return dest


def _ffmpeg_font_path(path: str) -> str:
    """FFmpeg drawtext の fontfile 値用にパスをエスケープする。"""
    path = path.replace("\\", "/")
    # ドライブレターのコロンをエスケープ (C:/ -> C\:/)
    if len(path) >= 2 and path[1] == ":":
        path = path[0] + "\\:" + path[2:]
    return path


class VideoComposer:
    """
    シーンリストから縦型ショート動画 (1080x1920) を生成する。
    各シーンは: 背景画像(Ken Burns) + VOICEVOX音声 + テロップ（FFmpeg drawtext）
    全シーンを concat して1本の MP4 に結合する。
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voicevox = VoiceVox()
        self.pexels = PexelsClient()

    def compose(self, script: dict, output_filename: str) -> str:
        """
        script: generate_youtube_script() / generate_threads_video_script() の戻り値
        戻り値: 生成した MP4 ファイルのパス
        """
        scenes = script["scenes"]
        image_keywords = script.get("image_keywords", ["business"])

        raw_font = _find_font()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            font = _copy_font_to_tmp(raw_font, tmp) if raw_font else ""
            scene_files = []

            for i, scene in enumerate(scenes):
                scene_path = self._compose_scene(scene, i, image_keywords, tmp, font)
                scene_files.append(scene_path)

            output_path = str(self.output_dir / output_filename)
            self._concat_scenes(scene_files, output_path)

        return output_path

    def _compose_scene(
        self, scene: dict, idx: int, image_keywords: list, tmp: Path, font: str
    ) -> str:
        text = scene.get("text", "")
        duration = scene.get("duration_sec", 5)

        image_path = str(tmp / f"img_{idx}.jpg")
        self.pexels.fetch_and_save(image_keywords, image_path)

        audio_path = str(tmp / f"audio_{idx}.wav")
        self.voicevox.synthesize(text.replace("\n", "。"), audio_path)

        scene_path = str(tmp / f"scene_{idx}.mp4")
        self._ffmpeg_scene(image_path, audio_path, text, duration, scene_path, font)

        return scene_path

    def _ffmpeg_scene(
        self, image: str, audio: str, text: str, duration: int, output: str, font: str
    ):
        safe_text = self._escape_ffmpeg_text(text)
        frames = max(1, (duration + 2) * FPS)

        # Ken Burns: 徐々にズームイン (1.0 → 1.2)
        ken_burns = (
            f"zoompan=z='min(zoom+0.0010,1.2)':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={WIDTH}x{HEIGHT},fps={FPS}"
        )

        vf_parts = [ken_burns]
        if font and safe_text:
            vf_parts.append(self._build_drawtext(safe_text, font))

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image,
            "-i", audio,
            "-vf", ",".join(vf_parts),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            "-t", str(duration + 2),
            "-pix_fmt", "yuv420p",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg エラー:\n{result.stderr[-2000:]}")

    def _build_drawtext(self, text: str, font: str) -> str:
        lines = text.split("\\n") if "\\n" in text else text.split("\n")
        font_escaped = _ffmpeg_font_path(font)
        filters = []
        y_start = HEIGHT // 2 + 200 - (len(lines) * 70) // 2

        for i, line in enumerate(lines):
            y = y_start + i * 80
            filters.append(
                f"drawtext=fontfile='{font_escaped}':"
                f"text='{line}':"
                f"fontcolor=white:"
                f"fontsize=52:"
                f"box=1:boxcolor=black@0.65:boxborderw=14:"
                f"x=(w-text_w)/2:y={y}:"
                f"enable='between(t,0.2,999)'"
            )
        return ",".join(filters)

    def _concat_scenes(self, scene_files: List[str], output: str):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            for sf in scene_files:
                sf_escaped = sf.replace("\\", "/")
                f.write(f"file '{sf_escaped}'\n")
            list_file = f.name

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        os.unlink(list_file)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg concat エラー:\n{result.stderr[-2000:]}")

    @staticmethod
    def _escape_ffmpeg_text(text: str) -> str:
        return (text
                .replace("'", "\\'")
                .replace(":", "\\:")
                .replace("[", "\\[")
                .replace("]", "\\]"))
