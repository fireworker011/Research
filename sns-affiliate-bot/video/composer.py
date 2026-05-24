import os
import subprocess
import tempfile
from pathlib import Path
from typing import List

from .voicevox import VoiceVox
from .pexels import PexelsClient


WIDTH = 1080
HEIGHT = 1920
FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"
FONT_FALLBACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.otf"


def _get_font() -> str:
    for f in [FONT_PATH, FONT_FALLBACK]:
        if os.path.exists(f):
            return f
    return "NotoSansCJK-Bold"


class VideoComposer:
    """
    シーンリストから YouTube Shorts 用 MP4 を生成する。
    各シーンは: 背景画像 + VOICEVOX音声 + 動的テロップ（FFmpeg drawtext）
    最終的に全シーンを concat して1本の動画に結合する。
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voicevox = VoiceVox()
        self.pexels = PexelsClient()

    def compose(self, script: dict, output_filename: str) -> str:
        """
        script: generate_youtube_script() の戻り値
        戻り値: 生成した MP4 ファイルのパス
        """
        scenes = script["scenes"]
        image_keywords = script.get("image_keywords", ["business"])

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            scene_files = []

            for i, scene in enumerate(scenes):
                scene_path = self._compose_scene(scene, i, image_keywords, tmp)
                scene_files.append(scene_path)

            output_path = str(self.output_dir / output_filename)
            self._concat_scenes(scene_files, output_path)

        return output_path

    def _compose_scene(self, scene: dict, idx: int, image_keywords: list, tmp: Path) -> str:
        text = scene.get("text", "")
        duration = scene.get("duration_sec", 5)

        image_path = str(tmp / f"img_{idx}.jpg")
        self.pexels.fetch_and_save(image_keywords, image_path)

        audio_path = str(tmp / f"audio_{idx}.wav")
        self.voicevox.synthesize(text.replace("\n", "。"), audio_path)

        scene_path = str(tmp / f"scene_{idx}.mp4")
        self._ffmpeg_scene(image_path, audio_path, text, duration, scene_path)

        return scene_path

    def _ffmpeg_scene(self, image: str, audio: str, text: str, duration: int, output: str):
        font = _get_font()
        safe_text = self._escape_ffmpeg_text(text)

        drawtext_lines = self._build_drawtext(safe_text, font)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image,
            "-i", audio,
            "-vf",
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            + drawtext_lines,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            "-t", str(duration + 1),
            "-pix_fmt", "yuv420p",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg エラー:\n{result.stderr}")

    def _build_drawtext(self, text: str, font: str) -> str:
        lines = text.split("\\n") if "\\n" in text else text.split("\n")
        filters = []
        y_start = HEIGHT // 2 - (len(lines) * 70) // 2

        for i, line in enumerate(lines):
            y = y_start + i * 80
            filters.append(
                f"drawtext=fontfile='{font}':"
                f"text='{line}':"
                f"fontcolor=white:"
                f"fontsize=52:"
                f"box=1:boxcolor=black@0.6:boxborderw=12:"
                f"x=(w-text_w)/2:y={y}:"
                f"enable='between(t,0.3,999)'"
            )
        return ",".join(filters)

    def _concat_scenes(self, scene_files: List[str], output: str):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for sf in scene_files:
                f.write(f"file '{sf}'\n")
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
            raise RuntimeError(f"FFmpeg concat エラー:\n{result.stderr}")

    @staticmethod
    def _escape_ffmpeg_text(text: str) -> str:
        return (text
                .replace("'", "\\'")
                .replace(":", "\\:")
                .replace("[", "\\[")
                .replace("]", "\\]"))
